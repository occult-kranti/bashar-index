"""English source captions: selection, bounded transport, and timed normalization.

Transport URLs exist only in ephemeral track specs. Callers own spool reservations,
durable receipts, archives, and remote verification. No network retry occurs here.
"""
from __future__ import annotations

import hashlib
import html
import http.client
import json
import math
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request


MAX_RAW_BYTES = 64 * 1024 * 1024
_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "video.google.com"}
_FORMATS = {"json3": 0, "vtt": 1}
_HEADERS = {"user-agent", "accept", "accept-language", "origin", "referer"}


class CaptionError(RuntimeError):
    """Safe classification; messages never contain provider URLs or response bodies."""

    def __init__(self, kind, message=None):
        self.kind = kind
        super().__init__(message or kind.replace("_", " "))


def _text(value, limit=160):
    value = str(value or "")
    value = re.sub(r"https?://\S+", "[URL omitted]", value)
    return " ".join(value.split())[:limit]


def _url_parts(url, video_id=""):
    try:
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname not in _HOSTS
                or parsed.username or parsed.password or parsed.port not in (None, 443)
                or parsed.fragment or parsed.path not in ("/api/timedtext", "/timedtext")):
            raise CaptionError("unsafe_url")
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        query = {key.lower(): value for key, value in query.items()}
        if "tlang" in query:
            raise CaptionError("translated_track")
        if video_id and "v" in query and query["v"] != [video_id]:
            raise CaptionError("unsafe_url")
        return query
    except (TypeError, ValueError):
        raise CaptionError("unsafe_url") from None


def _language(value):
    return str(value or "").replace("_", "-").lower().removesuffix("-orig")


def _english(language):
    return bool(re.fullmatch(r"en(?:-[a-z0-9]+)*", language))


def select_tracks(info):
    """Select every English published track and original English ASR track.

    Alias/format/client duplicates collapse; any ``tlang`` URL is excluded even
    when its displayed language is English. An empty inventory is a report from
    the extractor, never proof that the video has no captions.
    """
    tracks, translated, other_languages, noncaption, unresolved = {}, set(), set(), set(), set()
    video_id = str(info.get("id") or "")
    if info.get("_caption_access_warning"):
        unresolved.add(("", "inventory", "subtitle_access_requirement"))
    inventory_seen = False
    for field, kind in (("subtitles", "published"), ("automatic_captions", "automatic_original")):
        collection = info.get(field)
        if collection is None:
            unresolved.add(("", kind, "inventory_not_reported"))
            continue
        if not isinstance(collection, dict):
            unresolved.add(("", kind, "invalid_inventory"))
            continue
        inventory_seen = True
        for alias, formats in collection.items():
            alias = str(alias)
            if alias == "live_chat":
                noncaption.add((kind, alias))
                continue
            if not isinstance(formats, list):
                unresolved.add((_text(alias), kind, "invalid_track_inventory"))
                continue
            candidates, reasons = [], set()
            for item in formats:
                if not isinstance(item, dict):
                    reasons.add("invalid_track_inventory")
                    continue
                try:
                    query = _url_parts(item.get("url"), video_id)
                except CaptionError as exc:
                    if exc.kind == "translated_track":
                        translated.add((kind, alias))
                    else:
                        reasons.add(exc.kind)
                    continue
                language = _language(query.get("lang", [alias])[0])
                if not _english(language):
                    other_languages.add((kind, language))
                    continue
                if kind == "automatic_original" and query.get("kind") != ["asr"]:
                    reasons.add("original_origin_unproven")
                    continue
                ext = str(item.get("ext") or "").lower()
                if ext not in _FORMATS:
                    reasons.add("unsupported_caption_format")
                    continue
                if query.get("fmt", [ext]) != [ext]:
                    reasons.add("caption_format_mismatch")
                    continue
                name = _text(item.get("name") or alias)
                # Auto's en/en-orig aliases refer to the same source track.
                discriminator = query.get("name", [""])[0]
                if kind == "published" and not discriminator:
                    discriminator = alias
                identity = (kind, language, discriminator)
                digest = hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:16]
                headers = {}
                for source in (info.get("http_headers"), item.get("http_headers")):
                    if isinstance(source, dict):
                        headers.update({str(k): str(v) for k, v in source.items()
                                        if str(k).lower() in _HEADERS and "\n" not in str(v) and "\r" not in str(v)})
                spec = {"video_id": video_id, "track_id": f"{kind}.{language}.{digest}",
                        "language": language, "kind": kind, "name": name, "ext": ext,
                        "url": item["url"], "http_headers": headers}
                candidates.append((identity, spec))
            for identity, spec in candidates:
                old = tracks.get(identity)
                if old is None or _FORMATS[spec["ext"]] < _FORMATS[old["ext"]]:
                    tracks[identity] = spec
            if not candidates:
                for reason in reasons:
                    unresolved.add((_text(alias), kind, reason))
    selected = sorted(tracks.values(), key=lambda item: (item["kind"], item["language"], item["track_id"]))
    return {"tracks": selected, "excluded_translated": len(translated),
            "excluded_languages": len(other_languages), "excluded_noncaption": len(noncaption),
            "unresolved": [{"language": lang, "kind": kind, "reason": reason}
                           for lang, kind, reason in sorted(unresolved)],
            "inventory_status": "incomplete" if unresolved or not inventory_seen else (
                "tracks_reported" if selected else "no_english_tracks_reported")}


def provenance(spec):
    """Persistable track identity, with no transport material or invented origin."""
    return {"schema_version": 1, "provider": "youtube", "selection": "english_original_only",
            "video_id": _text(spec["video_id"], 32), "track_id": spec["track_id"],
            "language": spec["language"], "kind": spec["kind"], "name": _text(spec.get("name")),
            "raw_format": spec["ext"], "machine_translated": False}


def _check_stop(stop):
    if stop is not None and stop.is_set():
        raise CaptionError("stopped")


def _pace(limiter, stop):
    _check_stop(stop)
    if limiter is not None:
        limiter.wait()
    _check_stop(stop)


class _CaptionRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, video_id, limiter, stop):
        self.video_id, self.limiter, self.stop = video_id, limiter, stop

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _url_parts(newurl, self.video_id)
        _pace(self.limiter, self.stop)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_track(spec, output, *, budget, limiter, stop, timeout=30, max_bytes=MAX_RAW_BYTES):
    """Stream one raw track through shared Budget.write, without retry or deletion.

    ``output`` must be a fresh binary file. Header length expands its existing
    budget reservation before any body write. Unknown lengths remain byte-capped.
    """
    if not isinstance(max_bytes, int) or max_bytes <= 0 or output.tell() != 0:
        raise ValueError("caption fetch requires a positive limit and empty output")
    _url_parts(spec["url"], spec.get("video_id", ""))
    headers = {k: v for k, v in spec.get("http_headers", {}).items()
               if k.lower() in _HEADERS and "\r" not in v and "\n" not in v}
    headers["Accept-Encoding"] = "identity"
    request = urllib.request.Request(spec["url"], headers=headers)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                       _CaptionRedirect(spec.get("video_id", ""), limiter, stop))
    _pace(limiter, stop)
    count, md5, sha256 = 0, hashlib.md5(), hashlib.sha256()
    try:
        with opener.open(request, timeout=timeout) as response:
            _url_parts(response.geturl(), spec.get("video_id", ""))
            content_type = str(response.headers.get("Content-Type", "")).split(";")[0].lower().strip()
            if (response.status != 200 or response.headers.get("Content-Range")
                    or response.headers.get("Content-Encoding", "identity").lower() not in ("", "identity")
                    or content_type in ("text/html", "application/xhtml+xml")):
                raise CaptionError("caption_response")
            length_header = response.headers.get("Content-Length")
            expected = None
            if length_header is not None:
                if not re.fullmatch(r"\d+", str(length_header)):
                    raise CaptionError("caption_response")
                expected = int(length_header)
                if expected == 0:
                    raise CaptionError("caption_response")
                if expected > max_bytes:
                    raise CaptionError("deferred_caption_size")
                if hasattr(budget, "admit_size"):
                    budget.admit_size(Path(output.name), expected)
            while True:
                _check_stop(stop)
                chunk = response.read(min(65536, max_bytes - count + 1))
                if not chunk:
                    break
                if count + len(chunk) > max_bytes:
                    raise CaptionError("deferred_caption_size")
                if expected is not None and count + len(chunk) > expected:
                    raise CaptionError("caption_response")
                budget.write(output, chunk)
                count += len(chunk)
                md5.update(chunk)
                sha256.update(chunk)
            if (expected is not None and count != expected) or count == 0:
                raise CaptionError("caption_response")
    except urllib.error.HTTPError as exc:
        kind = {401: "login_required", 403: "forbidden", 429: "rate_limited",
                404: "caption_unavailable", 410: "caption_unavailable"}.get(exc.code, "network")
        raise CaptionError(kind) from None
    except http.client.HTTPException:
        raise CaptionError("caption_response") from None
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        raise CaptionError("network") from None
    return {"bytes": count, "md5": md5.hexdigest(), "sha256": sha256.hexdigest(), "content_type": content_type}


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CaptionError("caption_response")
    try:
        valid = math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise CaptionError("caption_response")
    return value / 1000


def _clean_text(value):
    return " ".join(value.split())


def _timestamp(value):
    parts = value.split(":")
    if len(parts) not in (2, 3) or not re.fullmatch(r"\d{2}\.\d{3}", parts[-1]):
        raise CaptionError("caption_response")
    if any(not part.isdigit() for part in parts[:-1]):
        raise CaptionError("caption_response")
    seconds, minutes = float(parts[-1]), int(parts[-2])
    if seconds >= 60 or minutes >= 60:
        raise CaptionError("caption_response")
    return seconds + minutes * 60 + (int(parts[0]) * 3600 if len(parts) == 3 else 0)


def normalize_caption(rawbytes, ext):
    """Retain provider cue order and timing; raw bytes remain the primary source.

    Missing JSON3 duration stays null. Rolling ASR repetitions are preserved in
    timed segments; text is a cue rendering rather than an inferred transcript.
    """
    try:
        raw = rawbytes.decode("utf-8-sig")
    except (UnicodeDecodeError, AttributeError):
        raise CaptionError("caption_response") from None
    segments = []
    if ext == "json3":
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            raise CaptionError("caption_response") from None
        if not isinstance(data, dict) or not isinstance(data.get("events"), list):
            raise CaptionError("caption_response")
        for event in data["events"]:
            if not isinstance(event, dict):
                raise CaptionError("caption_response")
            parts = event.get("segs", [])
            if not isinstance(parts, list) or any(not isinstance(part, dict) for part in parts):
                raise CaptionError("caption_response")
            texts = [part.get("utf8", "") for part in parts]
            if any(not isinstance(part, str) for part in texts):
                raise CaptionError("caption_response")
            text = _clean_text("".join(texts))
            if not text:
                continue
            start = _number(event.get("tStartMs"))
            end = start + _number(event["dDurationMs"]) if "dDurationMs" in event else None
            segments.append({"start": start, "end": end, "text": text})
    elif ext == "vtt":
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        if not re.match(r"^WEBVTT(?:[ \t].*)?(?:\n|$)", raw):
            raise CaptionError("caption_response")
        for block in re.split(r"\n[ \t]*\n", raw)[1:]:
            lines = block.strip().splitlines()
            if not lines or re.match(r"^(NOTE(?:\s|$)|STYLE$|REGION$)", lines[0]):
                continue
            index = 0 if "-->" in lines[0] else 1
            if index >= len(lines) or "-->" not in lines[index]:
                raise CaptionError("caption_response")
            timing = re.fullmatch(r"(\S+)\s+-->\s+(\S+)(?:\s+.*)?", lines[index])
            if not timing:
                raise CaptionError("caption_response")
            start, end = map(_timestamp, timing.groups())
            if end < start:
                raise CaptionError("caption_response")
            text = _clean_text(html.unescape(re.sub(r"<[^>]*>", "", "\n".join(lines[index + 1:]))))
            if text:
                segments.append({"start": start, "end": end, "text": text})
    else:
        raise CaptionError("unsupported_caption_format")
    if not segments or not any(segment["text"].strip() for segment in segments):
        raise CaptionError("caption_empty")
    return {"segments": segments, "text": "\n".join(segment["text"] for segment in segments),
            "raw_format": ext, "normalization_version": 1}
