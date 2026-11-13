#!/usr/bin/env python3
"""List every video on each tracked channel. Public metadata only: no media, no cookies, no login.

Uses yt-dlp in flat-playlist mode on the channel's three public tabs: Videos, Live and Shorts (a
channel's own count of "N videos" covers all three). Each row says which tab it came from. A channel
that has no Live or Shorts tab simply contributes nothing for it. One file per channel is written
atomically, so an interrupted run never leaves half a channel, and videos_all.jsonl is rebuilt from
those files. A run stops early after a few 403 / 429 / bot-check responses instead of pushing through.

This is the one YouTube step that also answers from a cloud server: listing asks for no video stream.

    python3 pipeline/discover.py --workers 3 --min-interval 3
    python3 pipeline/discover.py --only tyler-ellison,darryl-anka --workers 1
Output (safe to commit after review):
    <root>/discover/channels/<person_id>.jsonl, videos_all.jsonl, discover_manifest.jsonl
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, HARD_BLOCKS, ID_RE, Breaker, Progress, RateLimiter, add_root_arg,  # noqa: E402
                    append_jsonl, atomic_write_text, classify_error, latest_by_key, layout, read_csv, read_jsonl,
                    run_cmd, utc_now)

INDEX = ET_ROOT / "youtube-index" / "youtube_index.json"
EXTRA_CHANNELS = ET_ROOT / "sources" / "extra_channels.csv"   # tracked channels the 2026-10-23 index does not have
TABS = ("videos", "streams", "shorts")
NO_SUCH_TAB = re.compile(r"does not have a \w+ tab", re.I)


def extra_entries(path=EXTRA_CHANNELS):
    """Rows of sources/extra_channels.csv shaped like index entries."""
    out = []
    for row in read_csv(path) if Path(path).exists() else []:
        if row.get("person_id") and (row.get("channel_url") or "").startswith("https://www.youtube.com/"):
            out.append({"person": row["person_id"], "person_name": row.get("person_name", ""), "video_count": None,
                        "channel": {"url": row["channel_url"], "channel_id": row.get("channel_id", ""),
                                    "handle": row.get("handle", "")}})
    return out


def channel_url(entry):
    """The address of the channel's Videos tab, or None when the entry has no channel."""
    url = ((entry.get("channel") or {}).get("url") or "").rstrip("/")
    if not url:
        return None
    return url if url.endswith("/videos") else url + "/videos"


def list_tab(args, url):
    """(entries, '') for one tab, or (None, error text). A channel that has no such tab is an empty list."""
    code, out, err = run_cmd([args.ytdlp, "--ignore-config", "--flat-playlist", "-J", "--no-warnings",
                              "--playlist-items", f"1:{args.max_per_channel}", "--socket-timeout", "30",
                              "--extractor-retries", "2", "--extractor-args", "youtubetab:approximate_date",
                              "--sleep-requests", str(args.page_pause), url], args.timeout)
    if code != 0:
        return ([], "") if NO_SUCH_TAB.search(err or "") else (None, err or f"exit code {code}")
    try:
        return ((json.loads(out) or {}).get("entries") or []), ""
    except ValueError as exc:
        return None, f"the listing could not be read: {exc}"


def discover_one(args, entry, limiter, breaker, paths):
    person = entry["person"]
    url = channel_url(entry)
    base = url.removesuffix("/videos")
    expected = entry.get("video_count") if isinstance(entry.get("video_count"), int) else None
    record = {"person_id": person, "channel_url": url, "expected_total": expected, "started": utc_now()}
    t0 = time.time()
    rows, seen, per_tab = [], set(), {}
    try:
        for tab in args.tab_list:
            if breaker.tripped.is_set():
                return None                      # nothing recorded: the channel is listed again on the next run
            limiter.wait()
            entries, problem = list_tab(args, f"{base}/{tab}")
            if entries is None:
                raise RuntimeError(problem)
            per_tab[tab] = 0
            for e in entries:
                vid = e.get("id")
                if vid and ID_RE.match(vid) and vid not in seen:
                    seen.add(vid)
                    per_tab[tab] += 1
                    row = {"video_id": vid, "title": e.get("title"), "duration_s": e.get("duration"),
                           "view_count": e.get("view_count"), "person_id": person, "tab": tab}
                    if e.get("upload_date"):
                        row["upload_date_approx"] = e["upload_date"]      # worked out from "3 years ago": a guide, not a date
                    rows.append(row)
        text = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)
        atomic_write_text(paths.discover / "channels" / f"{person}.jsonl", text)
        record.update(status="ok", n_videos=len(rows), tabs=per_tab,
                      coverage=round(len(rows) / expected, 3) if expected else None)
        breaker.success()
    except Exception as exc:  # noqa: BLE001 - every failure is recorded, none is fatal
        klass = classify_error(str(exc))
        record.update(status="error", error_class=klass, error_tail=str(exc)[-300:])
        if klass in HARD_BLOCKS:
            breaker.hard_block()
    record["elapsed_s"] = round(time.time() - t0, 1)
    append_jsonl(paths.discover / "discover_manifest.jsonl", record)
    return record


def rebuild_all(paths):
    lines = []
    for f in sorted((paths.discover / "channels").glob("*.jsonl")):
        lines += [ln for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    atomic_write_text(paths.discover / "videos_all.jsonl", "\n".join(lines) + ("\n" if lines else ""))
    return len(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--ytdlp", default="yt-dlp")
    ap.add_argument("--index", type=Path, default=INDEX, help="channel index JSON (default: the committed one)")
    ap.add_argument("--extra-channels", type=Path, default=EXTRA_CHANNELS,
                    help="CSV of tracked channels the index does not have (default sources/extra_channels.csv)")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--min-interval", type=float, default=3.0, help="seconds between request starts, all workers")
    ap.add_argument("--stop-after-blocks", type=int, default=3)
    ap.add_argument("--max-per-channel", type=int, default=20000)
    ap.add_argument("--tabs", default=",".join(TABS), help="which tabs to list: videos, streams (live), shorts")
    ap.add_argument("--page-pause", type=float, default=0.3,
                    help="seconds between the page requests inside one listing (a long channel is many pages)")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--only", help="comma-separated person ids")
    ap.add_argument("--limit-channels", type=int, default=0)
    ap.add_argument("--retry-failed", action="store_true")
    args = ap.parse_args()

    args.tab_list = [t for t in (x.strip() for x in args.tabs.split(",")) if t]
    if not args.tab_list or set(args.tab_list) - set(TABS):
        sys.exit("--tabs takes any of: " + ", ".join(TABS))
    paths = layout(args.root)
    entries = [e for e in json.loads(args.index.read_text(encoding="utf-8"))["channels"] if channel_url(e)]
    known = {e["person"] for e in entries}
    entries += [e for e in extra_entries(args.extra_channels) if e["person"] not in known]
    if args.only:
        wanted = set(args.only.split(","))
        entries = [e for e in entries if e["person"] in wanted]
    done = latest_by_key(read_jsonl(paths.discover / "discover_manifest.jsonl"), "person_id")
    def listed(person):
        """Finished for every tab asked for. A record from before tabs existed covered the Videos tab only."""
        rec = done.get(person, {})
        return rec.get("status") == "ok" and set(args.tab_list) <= set(rec.get("tabs") or {"videos": 0}) \
            and (paths.discover / "channels" / f"{person}.jsonl").exists()

    todo = [e for e in entries if not listed(e["person"])]
    if not args.retry_failed:
        todo = [e for e in todo if done.get(e["person"], {}).get("error_class") not in ("unavailable",)]
    if args.limit_channels:
        todo = todo[:args.limit_channels]
    print(f"{len(entries)} channels have a URL; {len(todo)} to do", file=sys.stderr)
    if todo and not shutil.which(args.ytdlp):
        sys.exit(f"{args.ytdlp} not found. Install it first: pip install -r pipeline/requirements.txt")
    limiter, breaker = RateLimiter(args.min_interval), Breaker(args.stop_after_blocks)
    progress = Progress(len(todo), "discover")
    with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for rec in pool.map(lambda e: discover_one(args, e, limiter, breaker, paths), todo):
            if rec is not None:
                progress.tick(rec["status"] == "ok")
    total = rebuild_all(paths)
    print(f"videos_all.jsonl: {total} videos", file=sys.stderr)
    by_tab = {}
    for rec in latest_by_key(read_jsonl(paths.discover / "discover_manifest.jsonl"), "person_id").values():
        if rec.get("status") == "ok":
            for tab, count in (rec.get("tabs") or {}).items():
                by_tab[tab] = by_tab.get(tab, 0) + count
    if by_tab:
        print("by tab: " + ", ".join(f"{by_tab[t]} {t}" for t in TABS if t in by_tab), file=sys.stderr)
    if breaker.tripped.is_set():
        print("STOPPED: repeated 403 / 429 / bot-check responses. Wait, lower --workers or raise --min-interval, "
              "then rerun; finished channels are skipped.", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
