"""Find independent publisher leads in the descriptions already saved for a dated selection.

Reads local metadata only. A creator linking a site or an episode is a discovery lead.
Edition matching and download availability still require the publisher's evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import html
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, unquote, urlencode, urlsplit, urlunsplit

try:
    from . import collection_coverage, common
except ImportError:
    import collection_coverage
    import common


LINK = re.compile(r"https?://[^\s<>\"'|\]\[]+", re.I)
SOCIAL = {"tiktok.com", "instagram.com", "facebook.com", "x.com", "twitter.com", "t.me"}
YOUTUBE = {"youtube.com", "youtu.be", "youtube-nocookie.com", "googlevideo.com", "ytimg.com"}
SPONSORS = {"paypal.com", "paypal.me", "buymeacoffee.com", "ko-fi.com", "cash.app", "venmo.com"}
SENSITIVE = re.compile(r"token|secret|pass(?:word|code)|signat|credential|expires|authoriz|x-amz|x-goog", re.I)


def on_host(host, domains):
    return any(host == site or host.endswith("." + site) for site in domains)


def public_link(value):
    try:
        parts = urlsplit(html.unescape(value).rstrip(".,;:!?)}\u200b"))
        host = (parts.hostname or "").casefold()
        if (parts.scheme.lower() not in {"https", "http"} or not host or parts.username is not None
                or parts.password is not None or parts.port is not None or "." not in host
                or on_host(host, YOUTUBE | SPONSORS) or not re.fullmatch(r"[a-z0-9.-]+", host)):
            return None
        query = parse_qs(parts.query, max_num_fields=40)
    except ValueError:
        return None
    # A public CMS id can identify an episode. Never retain session, sharing or signed query strings.
    if any(SENSITIVE.search(k) for k in query):
        return None
    safe = {k: v[0] for k, v in query.items() if k in {"p", "page_id"} and len(v) == 1 and v[0].isdigit()}
    path = parts.path.rstrip("/") or "/"
    decoded_path = unquote(path)
    if (len(path) > 500 or "=" in decoded_path or "&" in decoded_path or SENSITIVE.search(decoded_path)
            or re.search(r"(?i)/(?:oauth|checkout|cart|login)(?:/|$)", decoded_path)):
        return None
    return urlunsplit((parts.scheme.lower(), host, path, urlencode(safe), ""))


def kind(url):
    parts = urlsplit(url)
    path, host = parts.path.casefold(), parts.hostname or ""
    if re.search(r"\.(?:mp3|m4a|ogg|opus|flac|wav|mp4|webm)$", path):
        return "media_file"
    if re.search(r"\.(?:vtt|srt)$", path):
        return "caption_file"
    if re.search(r"(?:/rss|/feed)(?:/|$)|\.(?:rss|xml)$", path):
        return "feed"
    if on_host(host, SOCIAL):
        if path.startswith("/groups/") and "/posts/" not in path:
            return "social_profile"
        return "social_post" if re.search(r"/(?:reel|reels|video|videos|p|status|posts)/|/\d{3,}$", path) else "social_profile"
    if re.match(r"^/(?:store|shop|product|user|channel|c)/", path):
        return "website"
    if path != "/" and (on_host(host, {"vimeo.com", "rumble.com", "bitchute.com", "soundcloud.com",
                                       "buzzsprout.com", "podbean.com", "libsyn.com", "spreaker.com"})
                         or re.search(r"/(?:episode|podcast|video|transcript|listen|audio|p)/", path)):
        return "publisher_page"
    return "website"


def collect(root, selection):
    groups = json.loads(Path(selection).read_bytes())["channels"]
    selected = {item["video_id"]: (group["channel_dir"], group["channel_id"])
                for group in groups for item in group["items"]}
    coverage, acquired = collection_coverage.coverage(root, selection=selection)
    saved = {row["video_id"] for row in acquired}
    links, seen = defaultdict(set), set()
    for path in Path(root).rglob("*.info.json"):
        names = (path.parent.name, path.name.split(".", 1)[0])
        video = next((name for name in names if name in selected), None)
        if not video or path.is_symlink() or path.stat().st_size > 8_000_000:
            continue
        try:
            record = json.loads(path.read_bytes())
        except (OSError, UnicodeError, ValueError):
            continue
        if not isinstance(record, dict) or record.get("sanitization", {}).get("policy") != "public-research-metadata-v1":
            continue
        metadata = record.get("metadata", {})
        owner, channel = selected[video]
        if metadata.get("id") != video or metadata.get("channel_id") != channel:
            continue
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip():
            continue
        seen.add(video)
        for value in LINK.findall(description):
            url = public_link(value)
            if url:
                links[owner, url].add(video)
    leads = []
    for (owner, url), videos in sorted(links.items()):
        missing = sorted(videos - saved)
        if missing:
            leads.append(dict(channel_dir=owner, url=url, link_kind=kind(url), observed_in_selected=len(videos),
                              missing_audio_ids=missing))
    return {"schema_version": 1, "selection_sha256": coverage["selection_sha256"],
            "generated_at": coverage["generated_at"], "selected_recordings": len(selected),
            "verified_audio_at_scan": len(saved), "descriptions_read": len(seen),
            "missing_audio_with_description": len(seen - saved),
            "missing_audio_with_link": len({v for row in leads for v in row["missing_audio_ids"]}),
            "distinct_creator_links_by_kind": dict(Counter(row["link_kind"] for row in leads)), "leads": leads}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root = common.ensure_outside_git(args.root)
    out = common.ensure_outside_git(args.out)
    if not out.is_relative_to(root):
        parser.error("Output must be in the private archive")
    report = collect(root, args.selection)
    common.atomic_write_text(out, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "leads"}))


if __name__ == "__main__":
    main()
