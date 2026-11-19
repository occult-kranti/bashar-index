"""Join a host's public podcast catalogue, YouTube listings and reviewed guest identities.

A person, a channel and an appearance have separate identities. A co-credit is
evidence of collaboration. Only explicit reviewed sources establish the guest's
own channeling or mediumship. No network access is required.
"""
from __future__ import annotations

from collections import defaultdict
from email.utils import parsedate_to_datetime
from html import unescape
import re
import unicodedata
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

from feeds import parse_duration_text


ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
PODCAST = "{https://podcastindex.org/namespace/1.0}"
CHANNEL_ID = re.compile(r"UC[A-Za-z0-9_-]{22}")
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")


def normalize_title(title):
    words = re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", unescape(title)).casefold())
    return " ".join(words)


def public_url(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        parts = urlsplit(value)
        if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
                or parts.port not in (None, 443)):
            return None
        if any(re.search(r"signature|credential|token|expires|x-amz|policy|session|auth", k, re.I)
               for k in parse_qs(parts.query, keep_blank_values=True)):
            return None
    except ValueError:
        return None
    return value


def read_episodes(data, feed_url, *, directory=(), include_unsized_enclosures=False):
    """Read explicit episode GUIDs, advertised downloadable editions and timed text.

    The Apple lookup is optional. Match an item's own podcastEpisode GUID plus
    title before accepting the directory's human-readable episode permalink.
    A show number may be reused and cannot identify an episode. A caller
    that supplies its own on-write size reservation can opt into enclosures
    whose publisher omits the byte count or reports zero.
    """
    if not public_url(feed_url):
        raise ValueError("Invalid public feed address")
    channel = ET.fromstring(data).find("channel")
    if channel is None:
        raise ValueError("RSS channel missing")
    links = defaultdict(set)
    for row in directory:
        if row.get("kind") != "podcast-episode":
            continue
        link = public_url(row.get("trackViewUrl"))
        if link and urlsplit(link).hostname == "podcasts.apple.com":
            links[(row.get("episodeGuid"), normalize_title(row.get("trackName", "")))].add(link)
    result = {}
    for item in channel.findall("item"):
        guid = (item.findtext("guid") or "").strip()
        title = (item.findtext("title") or "").strip()
        if not guid or not title or guid in result:
            raise ValueError("Each episode must have a distinct declared GUID and title")
        date = item.findtext("pubDate")
        key = guid, normalize_title(title)
        alternatives = links[key]
        webpage = public_url(item.findtext("link"))
        if not webpage and len(alternatives) == 1:
            webpage = next(iter(alternatives))
        enclosures = []
        for node in item.findall("enclosure"):
            link = public_url(node.get("url"))
            length = node.get("length", "")
            if link and length.isascii() and length.isdecimal() and int(length) > 0:
                enclosures.append({"url": link, "bytes": int(length), "mime_type": node.get("type")})
            elif link and include_unsized_enclosures and length in {"", "0"}:
                enclosures.append({"url": link, "bytes": None, "mime_type": node.get("type")})
        transcripts = []
        for node in item.findall(PODCAST + "transcript"):
            link = public_url(node.get("url"))
            if link:
                transcripts.append({"url": link, "mime_type": node.get("type"),
                                    "language": node.get("language"), "rel": node.get("rel")})
        result[guid] = {
            "guid": guid, "title": title, "feed_url": feed_url, "episode_url": webpage,
            "show_title": channel.findtext("title"), "show_language": channel.findtext("language"),
            "episode_number": item.findtext(ITUNES + "episode"), "season": item.findtext(ITUNES + "season"),
            "published_at": parsedate_to_datetime(date).isoformat() if date else None,
            "duration_seconds": parse_duration_text(item.findtext(ITUNES + "duration")),
            "enclosures": enclosures, "transcripts": transcripts,
        }
    return result


def numbered_episode_title(title):
    """Return the displayed base title, season and episode for a hyphenated episode suffix."""
    if not isinstance(title, str):
        return None
    match = re.fullmatch(r"(.+?)\s*\|\s*ep(?:isode)?\.?\s*([0-9]{1,3})-([0-9]{1,5})\s*", title, re.I)
    if match:
        return normalize_title(match[1]), int(match[2]), int(match[3])
    return None


def edition_matches(episodes, selection, *, maximum_duration_difference=2):
    """Accept one-to-one, same-host regular recordings with matching title and duration.

    This identifies a publisher edition. It cannot establish byte identity or
    complete word-level alignment with the YouTube edition. Ambiguities remain open.
    """
    owner = selection["channel_id"]
    if not CHANNEL_ID.fullmatch(owner):
        raise ValueError("Missing canonical host channel")
    source_by_title = defaultdict(list)
    for row in episodes.values():
        source_by_title[normalize_title(row["title"])].append(row)
    matched = defaultdict(list)
    for row in selection["items"]:
        if (row.get("tab") != "videos" or row.get("observed_primary_channel_id") != owner
                or row.get("expected_channel_id") != owner or not VIDEO_ID.fullmatch(row.get("video_id", ""))):
            raise ValueError("Listing row lacks matching regular-tab owner evidence")
        seconds = row.get("duration_s")
        if not isinstance(seconds, (int, float)) or seconds <= 0:
            continue
        same_title = list(source_by_title[normalize_title(row["title"])])
        numbered = numbered_episode_title(row["title"])
        if numbered:
            base, season, number = numbered
            for ep in source_by_title[base]:
                values = ep.get("season"), ep.get("episode_number")
                if (all(isinstance(v, str) and re.fullmatch(r"[0-9]{1,5}", v) for v in values)
                        and (int(values[0]), int(values[1])) == (season, number)):
                    same_title.append(ep)
        candidates = [ep for ep in same_title
                      if ep["duration_seconds"] and abs(seconds - ep["duration_seconds"]) <= maximum_duration_difference]
        if len(candidates) == 1:
            ep = candidates[0]
            matched[ep["guid"]].append({
                "youtube_video_id": row["video_id"], "youtube_url": "https://www.youtube.com/watch?v=" + row["video_id"],
                "youtube_title": row["title"], "youtube_duration_s": seconds,
                "youtube_tab": "videos", "channel_id": owner, "channel_dir": row["channel_dir"],
                "youtube_rank": row["regular_listing_rank"], "youtube_publication_display": row.get("publication_display"),
                "selection_page_sha256": row.get("page_sha256"), "episode": ep,
                "duration_difference_s": seconds - ep["duration_seconds"],
            })
    return sorted((rows[0] for rows in matched.values() if len(rows) == 1), key=lambda x: x["youtube_rank"])


def reviewed_appearances(episodes, reviews, host_channel_id):
    """Validate reviewed person–episode relationships and keep uncertain roles explicit."""
    if not CHANNEL_ID.fullmatch(host_channel_id):
        raise ValueError("Invalid host channel")
    seen = set()
    result = []
    for review in reviews:
        name = review["guest"].strip()
        guid = review["guid"]
        if not name or (guid, name.casefold()) in seen:
            raise ValueError("Duplicate or unnamed person in episode")
        seen.add((guid, name.casefold()))
        episode = episodes[guid]
        status = review["status"]
        if status not in {"confirmed", "role_confirmed_channel_unresolved", "possible", "other_role", "host"}:
            raise ValueError("Unknown guest role status")
        owner = review.get("channel_id") or ""
        if owner and (not CHANNEL_ID.fullmatch(owner) or owner == host_channel_id and status != "host"):
            raise ValueError("Guest channel identity invalid or reused from host")
        source = public_url(review.get("role_url"))
        ownership = public_url(review.get("owner_url"))
        if status == "confirmed" and (not source or not ownership or not owner or not review.get("role_evidence")):
            raise ValueError("Confirmed guest needs channel, role and ownership evidence")
        if status == "role_confirmed_channel_unresolved" and (owner or not source or not review.get("role_evidence")):
            raise ValueError("A role-only verification must provide a source and leave channel identity open")
        vid = review.get("host_video_id") or ""
        if vid and not VIDEO_ID.fullmatch(vid):
            raise ValueError("Host video ID invalid")
        episode_url = "https://www.youtube.com/watch?v=" + vid if vid else episode["episode_url"]
        result.append({**review, "guest": name, "channel_id": owner,
                       "channel_url": "https://www.youtube.com/channel/" + owner if owner else "",
                       "role_url": source, "owner_url": ownership, "host_channel_id": host_channel_id,
                       "host_video_id": vid, "host_episode_url": episode_url or episode["feed_url"],
                       "rss_feed_url": episode["feed_url"], "podcast_episode_url": episode["episode_url"],
                       "episode_number": episode["episode_number"], "episode_title": episode["title"],
                       "episode_published_at": episode["published_at"]})
    return result
