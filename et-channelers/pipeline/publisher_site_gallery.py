"""Read creator-published video metadata from a cached YouTube gallery on their own site."""
from __future__ import annotations

from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from .media_metadata import build_metadata


def linked_video_id(value):
    try:
        link = urlsplit(value or "")
        if link.scheme != "https" or link.username or link.password:
            return None
        if link.hostname == "youtu.be":
            return link.path.lstrip("/") if link.path.count("/") == 1 else None
        if link.hostname not in {"youtube.com", "www.youtube.com", "youtube-nocookie.com", "www.youtube-nocookie.com"}:
            return None
        if link.path == "/watch":
            values = parse_qs(link.query).get("v", [])
            return values[0] if len(values) == 1 else None
        parts = link.path.strip("/").split("/")
        return parts[1] if len(parts) == 2 and parts[0] == "embed" else None
    except ValueError:
        return None


def count_value(attrs, name):
    value = attrs.get(name) or ""
    return int(value) if value.isascii() and value.isdecimal() else None


def gallery_metadata(page, page_url, channel_id, selected, observed_at):
    """Join exact video and channel IDs. The gallery can cache engagement counts."""
    source_digest = sha256(page).hexdigest()
    recordings = {}

    class Gallery(HTMLParser):
        def handle_starttag(self, tag, pairs):
            attrs = dict(pairs)
            video_id = attrs.get("data-video-id")
            if (tag != "a" or video_id not in selected or attrs.get("data-channel-id") != channel_id
                    or linked_video_id(attrs.get("href")) != video_id or not attrs.get("data-video-title")):
                return
            published = count_value(attrs, "data-published-date")
            info = {
                "id": video_id, "channel_id": channel_id, "channel": attrs.get("data-user"),
                "title": attrs["data-video-title"], "description": unescape(attrs.get("data-title") or ""),
                "timestamp": published, "view_count": count_value(attrs, "data-view-count"),
                "like_count": count_value(attrs, "data-like-count"),
                "comment_count": count_value(attrs, "data-comment-count-raw"),
                "thumbnail": attrs.get("data-full-res"),
            }
            row = build_metadata({k: v for k, v in info.items() if v is not None}, selected[video_id], observed_at)
            row["observation_source"] = {"kind": "creator_site_youtube_gallery", "url": page_url,
                                         "page_sha256": source_digest, "engagement_as_of": None}
            if video_id in recordings and recordings[video_id] != row:
                raise ValueError("Conflicting gallery observations for the same video")
            recordings[video_id] = row

    parser = Gallery()
    parser.feed(page.decode("utf-8-sig"))
    parser.close()
    return list(recordings.values())
