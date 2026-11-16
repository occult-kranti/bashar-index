"""Retain public research metadata while excluding download/session material.

This module is deliberately pure: it reads no files, sends no requests and never
imports yt-dlp. Its input is the metadata already obtained for the audio item.
"""
from __future__ import annotations

import math
import re
from urllib.parse import parse_qsl, urlsplit

_OMIT = object()
_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_URL = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_LOCAL_PATH = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|file:|/(?:home|Users|workspaces|tmp|var|mnt|etc)/)", re.IGNORECASE)
_BEARER = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE)
_LANGUAGE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")

_PRIVATE_KEYS = {
    "http_headers", "request_headers", "response_headers", "headers", "cookie", "cookies",
    "cookiefile", "cookiesfrombrowser", "cookie_jar", "cookiejar", "authorization", "authentication", "auth",
    "username", "password", "credential", "credentials", "token", "access_token", "refresh_token",
    "api_key", "apikey", "client_secret", "session", "session_id", "session_token", "po_token",
    "visitor_data", "visitor_id", "tracking_params", "tracking", "signature", "sig", "lsig",
    "filename", "filepath", "file_path", "path", "directory", "dir", "working_directory",
    "download_archive", "cache_dir", "cachedir", "outtmpl", "paths",
    "requested_downloads", "requested_formats", "requested_entries", "downloader_options",
    "extractor_args", "postprocessors", "postprocessor_args", "fragments", "fragment_base_url", "proxy", "proxies",
    "manifest_url", "hls_aes", "url_transparent", "player_url", "player_client",
}
_PRIVATE_QUERY = {
    "token", "access_token", "refresh_token", "auth", "authorization", "credential", "credentials",
    "api_key", "apikey", "key", "signature", "sig", "lsig", "expire", "expires", "policy",
}


def _private_key(key):
    normalized = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", str(key))
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized).lower().replace("-", "_")
    return normalized.startswith("_") or normalized in _PRIVATE_KEYS or normalized.endswith(
        ("_password", "_secret", "_token", "_cookie", "_cookies", "_headers", "_filepath", "_path", "_filename", "_directory"))


def _private_url(value):
    """Transport URLs are never useful as durable source identifiers."""
    try:
        parsed = urlsplit(value)
        hostname = (parsed.hostname or "").lower()
        if parsed.username or parsed.password:
            return True
        if hostname == "googlevideo.com" or hostname.endswith(".googlevideo.com"):
            return True
        path = parsed.path.lower()
        if any(part in path for part in ("/timedtext", "/videoplayback", "/manifest/", "/youtubei/")):
            return True
        return any(name.lower() in _PRIVATE_QUERY or name.lower().startswith(("x-goog-", "x-amz-"))
                   for name, _ in parse_qsl(parsed.query, keep_blank_values=True))
    except ValueError:
        return True


def _clean(value, depth=0):
    if depth > 32:
        return _OMIT
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        if _LOCAL_PATH.match(value):
            return _OMIT
        if value.lower().startswith(("http://", "https://")) and not any(c.isspace() for c in value):
            if _private_url(value):
                return _OMIT
        value = _URL.sub(lambda match: "[transport URL omitted]" if _private_url(match.group())
                         else match.group(), value)
        return _BEARER.sub("[credential omitted]", value)
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if not isinstance(key, str) or _private_key(key):
                continue
            cleaned = _clean(item, depth + 1)
            if cleaned is not _OMIT:
                result[key] = cleaned
        return result
    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            cleaned = _clean(item, depth + 1)
            if cleaned is not _OMIT:
                result.append(cleaned)
        return result
    return _OMIT  # never stringify arbitrary objects (paths, cookies, sessions)


def build_metadata(info, row, captured_at):
    """Return a JSON-ready public metadata snapshot for this exact queued item.

    Descriptions, tags, categories, chapters, public thumbnails, dates, creator
    IDs, counts, language data and format characteristics are retained. Caption
    language inventories are recorded; no caption or transcript text is fetched.
    Unknown public metadata fields survive recursive sanitization for research.
    """
    if not isinstance(info, dict) or not isinstance(row, dict):
        raise ValueError("Metadata and queue row must be dictionaries")
    video_id = info.get("id") or row.get("video_id", "")
    if not isinstance(video_id, str) or not _VIDEO_ID.fullmatch(video_id):
        raise ValueError("Metadata needs a valid YouTube video ID")
    if row.get("video_id") and row["video_id"] != video_id:
        raise ValueError("Metadata belongs to a different queued video")
    if not isinstance(captured_at, str) or not captured_at:
        raise ValueError("Metadata needs its acquisition timestamp")

    def language_inventory(field):
        collection = info.get(field) or {}
        if not isinstance(collection, dict):
            return []
        return sorted(key for key in collection if isinstance(key, str) and _LANGUAGE.fullmatch(key))

    audio_language = _clean(info.get("language"))
    if audio_language is _OMIT:
        audio_language = None
    return {
        "schema_version": 1,
        "captured_at": captured_at,
        "source": {"platform": "youtube", "video_id": video_id,
                   "url": f"https://www.youtube.com/watch?v={video_id}"},
        "metadata": _clean(info),
        "queue": _clean(row),
        "languages": {"audio": audio_language,
                      "manual_subtitles": language_inventory("subtitles"),
                      "automatic_captions": language_inventory("automatic_captions")},
        "sanitization": {
            "policy": "public-research-metadata-v1",
            "excluded": ["temporary_media_and_caption_urls", "headers_and_credentials",
                         "local_paths", "internal_extractor_and_download_state"],
            "caption_text_fetched": False,
        },
    }
