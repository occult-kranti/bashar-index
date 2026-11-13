#!/usr/bin/env python3
"""Read each tracked YouTube channel's public page for the links the channel itself declares.

A channel page carries a small block of structured data (schema.org ProfilePage) with the channel's
canonical address, its name, its subscriber count and a "sameAs" list: the maker's own website and
social profiles. That list is the maker's statement of what is theirs, so it is the evidence the
feed lookup needs (find_feeds.py only verifies a podcast when the official site is known) and the
starting point for finding texts and audio the maker publishes outside YouTube.

One plain GET per channel, no login, no cookies, nothing that needs a video stream. robots.txt is
read first. If YouTube answers with a consent or sign-in page instead of the channel, that is counted
as a refusal, and three in a row stop the run (exit code 3).

Reads   the committed index and sources/extra_channels.csv
Writes  <root>/sources/channel_pages.jsonl      one line per channel: id, name, counts, declared links
and with --merge adds each declared website (not social profiles) to sources/official_sites.csv in the
repository, with the channel it was read from as the evidence. Existing rows are never changed.

    python3 pipeline/discover_sites.py --limit 5
    python3 pipeline/discover_sites.py --all --merge
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, Breaker, add_root_arg, append_jsonl, ensure_outside_git, host_of, latest_by_key,  # noqa: E402
                    layout, read_csv, read_jsonl, utc_now, write_csv)
from discover import INDEX, extra_entries  # noqa: E402
from feeds import FetchError, get_bytes  # noqa: E402
from fetch_publisher_text import Robots  # noqa: E402

OFFICIAL_SITES = ET_ROOT / "sources" / "official_sites.csv"
# Profiles on other platforms are not "the maker's own site": nothing there can vouch for a feed.
PLATFORMS = ("facebook.com", "fb.com", "fb.me", "instagram.com", "twitter.com", "x.com", "tiktok.com", "youtube.com",
             "youtu.be", "patreon.com", "linktr.ee", "linkin.bio", "beacons.ai", "bio.link", "lnk.bio", "spotify.com",
             "apple.com", "amazon.com", "amzn.to", "t.me", "telegram.me", "telegram.org", "discord.gg", "discord.com",
             "rumble.com", "bitchute.com", "odysee.com", "paypal.com", "paypal.me", "venmo.com", "buymeacoffee.com",
             "ko-fi.com", "etsy.com", "eventbrite.com", "calendly.com", "zoom.us", "wa.me", "whatsapp.com",
             "snapchat.com", "pinterest.com", "linkedin.com", "threads.net", "twitch.tv", "soundcloud.com",
             "bandcamp.com", "insighttimer.com", "gofundme.com", "cash.app", "bit.ly", "tinyurl.com", "goo.gl",
             "google.com", "wikipedia.org", "audible.com", "gaia.com", "vimeo.com", "clubhouse.com", "locals.com")
JSON_LD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)


def find_person(node):
    """The Person (or Organization) object of a ProfilePage, wherever it is nested."""
    if isinstance(node, list):
        for item in node:
            found = find_person(item)
            if found:
                return found
    elif isinstance(node, dict):
        if "sameAs" in node or node.get("@type") in ("Person", "Organization"):
            return node
        for key in ("mainEntity", "author", "@graph"):
            found = find_person(node.get(key))
            if found:
                return found
    return None


def read_channel_page(markup: str) -> dict:
    """{channel_id, name, handle, subscribers, same_as} from a channel page, or {} if it is not one."""
    for block in JSON_LD.findall(markup):
        try:
            person = find_person(json.loads(block))
        except ValueError:
            continue
        if not person:
            continue
        links = person.get("sameAs") or []
        links = [links] if isinstance(links, str) else [str(x) for x in links if x]
        found = re.search(r"/channel/(UC[\w-]{22})", str(person.get("url") or ""))
        stats = person.get("interactionStatistic") or []
        stats = [stats] if isinstance(stats, dict) else stats
        subscribers = None
        for stat in stats:
            kind = str((stat.get("interactionType") or "")) if isinstance(stat, dict) else ""
            if isinstance(stat, dict) and ("Subscribe" in kind or "Follow" in kind) and str(stat.get("userInteractionCount", "")).isdigit():
                subscribers = int(stat["userInteractionCount"])
        return {"channel_id": found.group(1) if found else "", "name": str(person.get("name") or "")[:200],
                "handle": str(person.get("alternateName") or "")[:100], "subscribers": subscribers,
                "same_as": [link[:300] for link in links][:30]}
    return {}


def website_domains(links):
    """Hosts among the declared links that are the maker's own site, not a profile on a platform."""
    out = []
    for link in links:
        host = host_of(link if re.match(r"^https?://", link, re.I) else "https://" + link.lstrip("/"))
        host = host.removeprefix("www.")
        if not host or "." not in host or any(host == p or host.endswith("." + p) for p in PLATFORMS):
            continue
        if host not in out:
            out.append(host)
    return out


def targets(index_path, extra_path):
    entries = []
    if Path(index_path).exists():
        for channel in json.loads(Path(index_path).read_text(encoding="utf-8"))["channels"]:
            url = ((channel.get("channel") or {}).get("url") or "").strip()
            if url.startswith("https://www.youtube.com/"):
                entries.append({"person_id": channel["person"], "channel_url": url.rstrip("/").removesuffix("/videos")})
    known = {e["person_id"] for e in entries}
    for extra in extra_entries(extra_path):
        if extra["person"] not in known:
            entries.append({"person_id": extra["person"], "channel_url": extra["channel"]["url"].rstrip("/")})
    return entries


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--index", type=Path, default=INDEX)
    ap.add_argument("--extra-channels", type=Path, default=ET_ROOT / "sources" / "extra_channels.csv")
    ap.add_argument("--official-sites", type=Path, default=OFFICIAL_SITES)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--min-interval", type=float, default=4.0, help="seconds between requests")
    ap.add_argument("--stop-after-blocks", type=int, default=3)
    ap.add_argument("--refresh", action="store_true", help="read channels again even if already read")
    ap.add_argument("--merge", action="store_true", help="add the declared websites to sources/official_sites.csv")
    ap.add_argument("--timeout", type=int, default=40)
    args = ap.parse_args()

    paths = layout(ensure_outside_git(args.root))
    out = paths.sources / "channel_pages.jsonl"
    entries = targets(args.index, args.extra_channels)
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        entries = [e for e in entries if e["person_id"] in wanted]
    done = {} if args.refresh else {k: v for k, v in latest_by_key(read_jsonl(out), "person_id").items() if v.get("status") == "ok"}
    todo = [e for e in entries if e["person_id"] not in done]
    print(f"channels {len(entries)} | already read {len(entries) - len(todo)} | to read {len(todo)}", file=sys.stderr)
    if not args.limit and not args.all:
        print("dry run: pass --limit N or --all", file=sys.stderr)
    else:
        if args.limit:
            todo = todo[:args.limit]
        robots, breaker, last = Robots(), Breaker(args.stop_after_blocks), 0.0
        for n, entry in enumerate(todo, 1):
            if breaker.tripped.is_set():
                break
            rec = {"person_id": entry["person_id"], "channel_url": entry["channel_url"], "started": utc_now()}
            verdict = robots.allowed(entry["channel_url"])
            if not verdict:
                rec.update(status="error", error_class="network" if verdict is None else "robots")
                append_jsonl(out, rec)
                continue
            wait = args.min_interval - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            try:
                final_url, _, body = get_bytes(entry["channel_url"], timeout=args.timeout, max_bytes=10_000_000)
            except FetchError as err:
                klass = {404: "unavailable", 410: "unavailable", 403: "forbidden", 429: "rate_limited"}.get(err.status, "network")
                rec.update(status="error", http_status=err.status, error_class=klass, error_tail=str(err)[-200:])
                if klass in ("forbidden", "rate_limited"):
                    breaker.hard_block()
                append_jsonl(out, rec)
                continue
            facts = read_channel_page(body.decode("utf-8", "replace"))
            if "consent." in host_of(final_url) or not facts:
                # a consent or sign-in page instead of the channel: YouTube is not serving this address
                rec.update(status="error", error_class="bot_check", error_tail="no channel data on the page that came back")
                breaker.hard_block()
            else:
                breaker.success()
                rec.update(status="ok", websites=website_domains(facts["same_as"]), **facts)
            append_jsonl(out, rec)
            if n % 10 == 0 or n == len(todo):
                print(f"[sites] {n}/{len(todo)} channels read", file=sys.stderr, flush=True)
        if breaker.tripped.is_set():
            print("STOPPED: YouTube answered three times in a row with a refusal or a page that is not the channel. "
                  "Wait, then rerun: channels already read are skipped.", file=sys.stderr)

    read = [r for r in latest_by_key(read_jsonl(out), "person_id").values() if r.get("status") == "ok"]
    with_site = [r for r in read if r.get("websites")]
    print(f"read {len(read)} channel pages | {len(with_site)} declare a website of their own | "
          f"{sum(1 for r in read if r.get('channel_id'))} with a channel id -> {out}")
    if args.merge:
        rows = read_csv(args.official_sites) if args.official_sites.exists() else []
        have = {(r["person_id"], r["domain"]) for r in rows}
        added = 0
        for rec in sorted(with_site, key=lambda r: r["person_id"]):
            for domain in rec["websites"]:
                if (rec["person_id"], domain) not in have:
                    rows.append({"person_id": rec["person_id"], "domain": domain,
                                 "evidence": f"declared on the person's own YouTube channel page ({rec.get('channel_id') or rec['channel_url']}), "
                                             f"read {rec['started'][:10]}"})
                    have.add((rec["person_id"], domain))
                    added += 1
        rows.sort(key=lambda r: (r["person_id"], r["domain"]))
        write_csv(args.official_sites, rows, ["person_id", "domain", "evidence"])
        print(f"official sites: {added} added, {len(rows)} total -> {args.official_sites}")
    if "breaker" in dir() and breaker.tripped.is_set():
        sys.exit(3)


if __name__ == "__main__":
    main()
