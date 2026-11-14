#!/usr/bin/env python3
"""Podcast feed helpers: fetch a URL politely, parse an RSS feed, normalise its episodes.

Standard library only. A podcast feed is the publisher's own list of files offered for download
(the <enclosure> of each item), so this lane needs no login and meets no bot check. Nothing here
sends cookies, uses a proxy or pretends to be a browser session.

Used by fetch_feeds.py, select_episodes.py, download_enclosures.py and fetch_publisher_transcripts.py.
"""
from __future__ import annotations

import gzip
import functools
import hashlib
import http.client
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from email.utils import parsedate_to_datetime

from common import item_id

# A plain, honest client name. No project, account or contact details are sent to third parties.
USER_AGENT = "podcast-feed-reader/1.0 (python-urllib)"
NS = {
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "podcast": "https://podcastindex.org/namespace/1.0",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
}
YOUTUBE_ID_IN_TEXT = re.compile(   # youtube-nocookie.com is YouTube's privacy-mode embed host: same ids
    r"(?<![A-Za-z0-9-])(?:youtube(?:-nocookie)?\.com/(?:watch\?(?:[^\s\"'<>]*&(?:amp;)?)?v=|live/|embed/|shorts/|v/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])")
AUDIO_TYPES = ("audio/", "video/")  # some feeds carry the audio track inside an mp4/m4v container
MAX_FEED_BYTES = 80 * 1024 * 1024


# An opener with an empty proxy table: proxy settings in the environment are ignored on purpose.
_DIRECT = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class FetchError(Exception):
    """A request that did not return usable bytes. `status` is the HTTP status, or 0 for a network error."""

    def __init__(self, status, message, final_url=""):
        super().__init__(message)
        self.status, self.final_url = status, final_url


def safe_url(url: str) -> str:
    """Percent-encode what a URL may not carry raw (spaces, non-ASCII letters), leaving existing %XX
    escapes alone. Publishers' own pages often link files as '.../Parable of the Back Yard.mp3'."""
    parts = urllib.parse.urlsplit((url or "").strip())
    host = parts.hostname or ""
    try:
        host.encode("ascii")
    except UnicodeEncodeError:
        host = host.encode("idna").decode("ascii")
    netloc = host + (f":{parts.port}" if parts.port else "")
    if parts.username:
        raise FetchError(0, "URLs with embedded credentials are not fetched")
    path = urllib.parse.quote(parts.path, safe="/%:@!$&'()*+,;=~-._")
    query = urllib.parse.quote(parts.query, safe="=&%:@!$'()*+,;/?~-._")
    return urllib.parse.urlunsplit((parts.scheme.lower(), netloc, path, query, ""))


def open_url(url, timeout=60, headers=None):
    """urllib response for a GET. Raises FetchError with the HTTP status on any failure."""
    if not re.match(r"^https?://", url or "", re.I):
        raise FetchError(0, f"not an http(s) URL: {str(url)[:80]!r}")
    try:
        request = urllib.request.Request(safe_url(url), headers={"User-Agent": USER_AGENT, "Accept": "*/*",
                                                                 **(headers or {})})
        return _DIRECT.open(request, timeout=timeout)
    except urllib.error.HTTPError as err:
        raise FetchError(err.code, f"HTTP Error {err.code}: {err.reason}", err.geturl() or url) from None
    except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as err:
        raise FetchError(0, f"{type(err).__name__}: {err}"[:300], url) from None


def get_bytes(url, timeout=60, max_bytes=MAX_FEED_BYTES):
    """(final_url, content_type, body) for a small resource such as a feed or a transcript."""
    with open_url(url, timeout, {"Accept-Encoding": "gzip"}) as response:
        try:
            body = response.read(max_bytes + 1)
        except (OSError, http.client.HTTPException) as err:
            raise FetchError(0, f"{type(err).__name__}: {err}"[:300], url) from None
        if len(body) > max_bytes:
            raise FetchError(0, f"response larger than {max_bytes} bytes", response.geturl())
        if (response.headers.get("Content-Encoding") or "").lower() == "gzip" or body[:2] == b"\x1f\x8b":
            try:
                body = gzip.decompress(body)
            except (OSError, EOFError, zlib.error):
                pass  # mislabelled plain body
        return response.geturl(), response.headers.get("Content-Type", ""), body


def parse_duration_text(text):
    """'1:26:06' -> 5166, '43:34' -> 2614, '1344' -> 1344, '894.5' -> 894, junk -> None."""
    text = (text or "").strip()
    if not text:
        return None
    try:
        if ":" in text:
            parts = [float(p) for p in text.split(":")]
            if not 2 <= len(parts) <= 3 or any(p < 0 for p in parts):
                return None
            seconds = 0.0
            for part in parts:
                seconds = seconds * 60 + part
        else:
            seconds = float(text)
    except ValueError:
        return None
    return int(seconds) if 0 < seconds < 100 * 3600 else None


def parse_date(text):
    """RFC 2822 or ISO date -> 'YYYY-MM-DD', or '' if it cannot be read."""
    text = (text or "").strip()
    if not text:
        return ""
    try:
        return parsedate_to_datetime(text).date().isoformat()
    except (TypeError, ValueError, IndexError):
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
        return match.group(0) if match else ""


def _text(node, path):
    found = node.find(path, NS)
    return (found.text or "").strip() if found is not None and found.text else ""


def _int(text):
    try:
        return int(str(text).strip())
    except (TypeError, ValueError):
        return None


MEDIA_SUFFIXES = (".mp3", ".m4a", ".m4b", ".mp4", ".m4v", ".aac", ".ogg", ".oga", ".opus", ".wav", ".flac", ".webm", ".mov")
NOT_MEDIA_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf", ".html", ".htm", ".txt", ".zip")


def is_media(declared_type, url: str) -> bool:
    """True if an enclosure is a recording. The declared type decides when there is one; without it,
    the file name does; with neither, it is taken as a recording unless the name says otherwise."""
    kind = (declared_type or "").strip().lower()
    path = urllib.parse.urlsplit(url).path.lower()
    if kind:
        return kind.startswith(AUDIO_TYPES) or (kind == "application/octet-stream" and path.endswith(MEDIA_SUFFIXES))
    return not path.endswith(NOT_MEDIA_SUFFIXES)


def episode_key(guid: str, enclosure_url: str) -> str:
    """What identifies an episode wherever its feed lives: the <guid> its publisher gave it, or, when
    there is none, the path of its media file without host and query (hosts and tracking prefixes change)."""
    guid = (guid or "").strip()
    if guid:
        return guid
    path = urllib.parse.urlsplit(enclosure_url).path
    return "path:" + re.sub(r"^.*?/(?=[^/]+/[^/]+$)", "", path)   # last folder and file name


def parse_feed(data: bytes, feed_url: str, person_id: str = "") -> dict:
    """Parse RSS bytes into {"feed": {...}, "episodes": [...]}. Episodes without an enclosure are counted
    but not returned. Show notes are not kept: only ids, titles, dates, sizes and links.

    An episode's id is made from the person it belongs to and the episode's own guid, not from the feed's
    address, so a feed that moves (http to https, a new host) keeps its ids and nothing is downloaded or
    counted twice. `legacy_id` is the id the first version of this lane used (feed address + guid)."""
    if b"<!ENTITY" in data[:4096]:
        raise ValueError("feed declares XML entities; refusing to parse it")
    root = ET.fromstring(data)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("no <channel> element: not an RSS 2.0 feed")
    items = channel.findall("item")
    episodes, seen = [], set()
    for position, item in enumerate(items, 1):
        enclosure = item.find("enclosure")
        url = (enclosure.get("url") or "").strip() if enclosure is not None else ""
        if not re.match(r"^https?://", url, re.I) or not is_media(enclosure.get("type"), url):
            continue          # no enclosure, or one that is a picture or a document (blog feeds attach a cover image)
        own_guid = _text(item, "guid")
        guid = own_guid or url
        ident = item_id("pod", person_id or feed_url, episode_key(own_guid, url))
        if ident in seen:
            continue  # the same guid listed twice
        seen.add(ident)
        notes = " ".join(filter(None, (_text(item, "description"), _text(item, "content:encoded"),
                                       _text(item, "itunes:summary"), _text(item, "link"))))
        transcripts = [{"url": t.get("url", "").strip(), "type": (t.get("type") or "").strip().lower(),
                        "language": (t.get("language") or "").strip(), "rel": (t.get("rel") or "").strip()}
                       for t in item.findall("podcast:transcript", NS) if (t.get("url") or "").strip()]
        episodes.append({
            "video_id": ident,
            "legacy_id": item_id("pod", feed_url, guid),
            "guid": guid,
            "position": position,
            "title": re.sub(r"\s+", " ", _text(item, "title") or _text(item, "itunes:title")),
            "published": parse_date(_text(item, "pubDate")),
            "duration_s": parse_duration_text(_text(item, "itunes:duration")),
            "enclosure_url": url,
            "enclosure_type": (enclosure.get("type") or "").strip().lower(),
            "enclosure_bytes": _int(enclosure.get("length")),
            "link": _text(item, "link"),
            "episode_no": _int(_text(item, "itunes:episode")),
            "season_no": _int(_text(item, "itunes:season")),
            "episode_type": _text(item, "itunes:episodeType"),
            "transcripts": transcripts,
            "youtube_ids": sorted(set(YOUTUBE_ID_IN_TEXT.findall(notes))),
        })
    dates = sorted(e["published"] for e in episodes if e["published"])
    known = [e["duration_s"] for e in episodes if e["duration_s"]]
    feed = {
        "feed_url": feed_url,
        "title": _text(channel, "title"),
        "author": _text(channel, "itunes:author"),
        "owner_name": _text(channel, "itunes:owner/itunes:name"),
        "link": _text(channel, "link"),
        "language": _text(channel, "language"),
        "copyright": _text(channel, "copyright"),
        "items": len(items),
        "episodes": len(episodes),
        "with_duration": len(known),
        "known_hours": round(sum(known) / 3600, 1),
        "with_transcript": sum(1 for e in episodes if e["transcripts"]),
        "earliest": dates[0] if dates else "",
        "latest": dates[-1] if dates else "",
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }
    return {"feed": feed, "episodes": episodes}


def feed_key(person_id: str, feed_url: str) -> str:
    """Folder-safe key for one feed of one person, e.g. 'athina-krol--3f9a2c1d'."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", person_id or "unknown").strip("-._")[:48] or "unknown"
    return f"{cleaned}--{hashlib.sha1(feed_url.encode('utf-8')).hexdigest()[:8]}"


# ---------------------------------------------------------------- title matching
_STOP = frozenset("a an and the of to in on for with by at from is are was be your you my our it this that "
                  "as or part pt ep episode full new live official video audio podcast show clip".split())


def tokens(text: str):
    """Lower-case content words of a title, used to compare an episode with a video."""
    words = re.findall(r"[^\W_]+", (text or "").lower().replace("’", "'").replace("'", ""), re.UNICODE)
    return [w for w in words if w not in _STOP and (len(w) > 1 or w.isdigit() or not w.isascii())]


@functools.lru_cache(maxsize=500_000)
def _token_set(text: str) -> frozenset:
    return frozenset(tokens(text))


def title_similarity(a: str, b: str) -> float:
    """Dice overlap of the content words of two titles: 1.0 identical sets, 0.0 disjoint or empty.
    The word sets are remembered: matching a feed against a whole channel compares each title thousands of times."""
    ta, tb = _token_set(a or ""), _token_set(b or "")
    if not ta or not tb:
        return 0.0
    return 2 * len(ta & tb) / (len(ta) + len(tb))


def name_pattern(names):
    """One compiled, case-insensitive whole-word pattern for a list of names and aliases, or None."""
    parts = []
    for name in names:
        words = re.findall(r"[^\W_]+", name or "", re.UNICODE)
        if words and sum(len(w) for w in words) >= 4:
            parts.append(r"[\W_]*".join(re.escape(w) for w in words))
    if not parts:
        return None
    return re.compile(r"(?<![^\W_])(?:%s)(?![^\W_])" % "|".join(sorted(set(parts), key=len, reverse=True)),
                      re.IGNORECASE | re.UNICODE)
