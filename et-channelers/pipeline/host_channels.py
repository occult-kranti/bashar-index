#!/usr/bin/env python3
"""Find the channel behind each recording of the Bashar Index list.

The list (draft-package/csv/bashar_videos_in_repo_by_channel.csv) names the channel each recording was
found on, but not its address. Two public lookups fill that in, one of each per channel:

  1. YouTube's embed lookup (oEmbed) for one of the channel's videos gives the channel's name and address.
  2. The channel page gives its id, its subscriber count and the websites the channel itself declares
     (the same reading discover_sites.py does for the tracked people).

No media and no login. robots.txt is read first; three refusals in a row stop the run (exit code 3). A
channel whose first video is gone is tried with its next one.

Writes  sources/bashar_host_channels.csv   channel, kind, youtube_name, channel_url, channel_id,
                                           subscribers, websites, evidence, checked
        sources/bashar_recordings_status.csv (--recordings)   for each listed recording, whether YouTube
                                           still answers for it: 200 yes, 404 gone, 401 not embeddable, 403 private
targets.py reads that file for the table of Bashar channels, and find_host_feeds.py uses the declared
websites to tell an interview show's own podcast from a namesake.

    python3 pipeline/host_channels.py --limit 3
    python3 pipeline/host_channels.py --all
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ET_ROOT, ID_RE, Breaker, host_id, host_of, read_csv, utc_now, write_csv  # noqa: E402
from discover_sites import read_channel_page, website_domains  # noqa: E402
from feeds import FetchError, get_bytes  # noqa: E402
from fetch_publisher_text import Robots  # noqa: E402

BASHAR_CSV = ET_ROOT / "draft-package" / "csv" / "bashar_videos_in_repo_by_channel.csv"
OUT = ET_ROOT / "sources" / "bashar_host_channels.csv"
FIELDS = ["channel", "host_id", "kind", "youtube_name", "channel_url", "channel_id", "subscribers", "websites", "evidence",
          "checked"]
OEMBED = "https://www.youtube.com/oembed?format=json&url="
STATUS_OUT = ET_ROOT / "sources" / "bashar_recordings_status.csv"
STATUS_FIELDS = ["video_id", "channel", "embed_lookup", "still_on_youtube", "checked"]
MEANING = {"200": "yes", "404": "no: gone", "401": "yes: embedding switched off", "403": "no: private"}


def kind_of(rows) -> str:
    types = [(r.get("content_type") or "").lower() for r in rows]
    if any(r.get("official") == "True" for r in rows):
        return "official channel"
    if any(t.startswith("interview") for t in types):
        return "interview show"
    return "re-upload channel" if any("re-upload" in t for t in types) else "clip channel"


def groups(path=BASHAR_CSV):
    """{channel name: its rows in the list}, in the list's order."""
    out = {}
    for row in read_csv(path) if Path(path).exists() else []:
        out.setdefault(row["channel"], []).append(row)
    return out


def check_recordings(args, listed):
    """One embed lookup per listed recording: is it still on YouTube? Nothing about the video is saved."""
    have = {r["video_id"]: r for r in (read_csv(args.status_out) if args.status_out.exists() else [])}
    wanted = [(row["video_id"], channel) for channel, rows in listed.items() for row in rows if ID_RE.match(row.get("video_id") or "")]
    todo = [(v, c) for v, c in wanted if args.refresh or have.get(v, {}).get("embed_lookup") not in MEANING]
    print(f"recordings {len(wanted)} | already checked {len(wanted) - len(todo)} | to check {len(todo)}", file=sys.stderr)
    if not args.limit and not args.all:
        print("dry run: pass --limit N or --all", file=sys.stderr)
        todo = []
    elif args.limit:
        todo = todo[:args.limit]
    robots, last, refused = Robots(), 0.0, 0
    for n, (vid, channel) in enumerate(todo, 1):
        url = OEMBED + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}", safe="")
        if not robots.allowed(url):
            break
        wait = args.min_interval - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        last = time.monotonic()
        try:
            get_bytes(url, timeout=args.timeout, max_bytes=200_000)
            answer = "200"
        except FetchError as err:
            answer = str(err.status or "no answer")
        refused = refused + 1 if answer == "429" else 0
        if refused >= args.stop_after_blocks:
            print("STOPPED: YouTube asked three times in a row to slow down. Rerun later; checked recordings are skipped.", file=sys.stderr)
            break
        have[vid] = {"video_id": vid, "channel": channel, "embed_lookup": answer,
                     "still_on_youtube": MEANING.get(answer, "unknown"), "checked": utc_now()[:10]}
        if n % 20 == 0 or n == len(todo):
            print(f"[recordings] {n}/{len(todo)} checked", file=sys.stderr, flush=True)
    rows = [have[v] for v, _ in wanted if v in have]
    write_csv(args.status_out, rows, STATUS_FIELDS)
    up = sum(1 for r in rows if r["still_on_youtube"].startswith("yes"))
    print(f"{len(rows)} of {len(wanted)} recordings checked: {up} still on YouTube, "
          f"{sum(1 for r in rows if r['still_on_youtube'].startswith('no'))} not -> {args.status_out}")
    if refused >= args.stop_after_blocks:
        sys.exit(3)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", type=Path, default=BASHAR_CSV, help="the list of recordings by channel")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--min-interval", type=float, default=4.0, help="seconds between requests")
    ap.add_argument("--stop-after-blocks", type=int, default=3)
    ap.add_argument("--refresh", action="store_true", help="look channels up again even if already found")
    ap.add_argument("--recordings", action="store_true",
                    help="instead of the channels, ask for every listed recording whether YouTube still has it")
    ap.add_argument("--status-out", type=Path, default=STATUS_OUT)
    ap.add_argument("--timeout", type=int, default=40)
    args = ap.parse_args()

    listed = groups(args.list)
    if args.recordings:
        return check_recordings(args, listed)
    have = {r["channel"]: r for r in (read_csv(args.out) if args.out.exists() else [])}
    todo = [c for c in listed if args.refresh or not (have.get(c) or {}).get("channel_url")]
    print(f"channels {len(listed)} | already found {len(listed) - len(todo)} | to look up {len(todo)}", file=sys.stderr)
    if not args.limit and not args.all:
        print("dry run: pass --limit N or --all", file=sys.stderr)
        todo = []
    elif args.limit:
        todo = todo[:args.limit]
    robots, breaker, last, answers = Robots(), Breaker(args.stop_after_blocks), [0.0], []

    def get(url):
        """Body of one polite GET, or None. Refusals count toward the breaker; `answers` keeps each status."""
        if not robots.allowed(url):
            answers.append("robots")
            return None
        wait = args.min_interval - (time.monotonic() - last[0])
        if wait > 0:
            time.sleep(wait)
        last[0] = time.monotonic()
        try:
            final, _, body = get_bytes(url, timeout=args.timeout, max_bytes=10_000_000)
        except FetchError as err:
            answers.append(str(err.status or "no answer"))
            if err.status in (403, 429):
                breaker.hard_block()
            return None
        if "consent." in host_of(final):
            answers.append("consent page")
            breaker.hard_block()
            return None
        answers.append("200")
        breaker.success()
        return body

    for n, channel in enumerate(todo, 1):
        if breaker.tripped.is_set():
            break
        rows = listed[channel]
        rec = {"channel": channel, "host_id": host_id(channel), "kind": kind_of(rows), "checked": utc_now()[:10]}
        del answers[:]
        for row in rows[:3]:                                   # a removed video gives no answer: try the next
            vid = row.get("video_id") or ""
            if not ID_RE.match(vid) or breaker.tripped.is_set():
                continue
            body = get(OEMBED + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}", safe=""))
            try:
                embed = json.loads(body) if body else {}
            except ValueError:
                embed = {}
            address = str(embed.get("author_url") or "")
            if address.startswith("https://www.youtube.com/"):
                rec.update(youtube_name=str(embed.get("author_name") or "")[:200], channel_url=address.rstrip("/"),
                           evidence=f"YouTube's embed lookup for one of this channel's listed recordings, {utc_now()[:10]}")
                break
        if not rec.get("channel_url"):
            # 404: the video is gone. 401: it exists but may not be embedded. 403: private.
            rec["evidence"] = (f"no channel found: YouTube's embed lookup answered {', '.join(answers) or 'nothing'} for "
                               f"{min(3, len(rows))} of this channel's listed recordings on {utc_now()[:10]}")
        if rec.get("channel_url") and not breaker.tripped.is_set():
            page = get(rec["channel_url"])
            facts = read_channel_page(page.decode("utf-8", "replace")) if page else {}
            if facts:
                rec.update(channel_id=facts["channel_id"], subscribers=facts["subscribers"] or "",
                           websites=" ".join(website_domains(facts["same_as"])))
        have[channel] = {**have.get(channel, {}), **rec}
        if n % 10 == 0 or n == len(todo):
            print(f"[hosts] {n}/{len(todo)} channels looked up", file=sys.stderr, flush=True)
    # every channel of the list has a row, found or not, so the table is complete
    for channel, rows in listed.items():
        have.setdefault(channel, {"channel": channel, "host_id": host_id(channel), "kind": kind_of(rows)})
    table = [have[c] for c in sorted(listed, key=lambda c: (-len(listed[c]), c.lower()))]
    write_csv(args.out, table, FIELDS)
    found = sum(1 for r in table if r.get("channel_url"))
    print(f"{found} of {len(table)} channels have an address, {sum(1 for r in table if r.get('channel_id'))} an id, "
          f"{sum(1 for r in table if r.get('websites'))} declare a website -> {args.out}")
    if breaker.tripped.is_set():
        print("STOPPED: three refusals in a row. Wait, then rerun: channels already found are skipped.", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
