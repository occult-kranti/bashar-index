#!/usr/bin/env python3
"""Read every accepted podcast feed and write its episode list to the private folder.

Input   sources/podcast_feeds.csv in the repository (feed address, whose it is, how it was verified).
        Rows are read when their verification is in --accept (default: verified,name-match).
Output  <root>/feeds/<feed_key>.jsonl        one line per episode with an audio enclosure
        <root>/feeds/feeds_manifest.jsonl    one line per attempt: status, counts, hours, date range, hash
No audio is downloaded here. Each feed is one GET of a file its publisher offers to every podcast
app. Feeds are read one at a time per host with a pause, a Retry-After is obeyed, and a host that
answers 403 or 429 three times in a row is left alone for the rest of the run. Any 403 or 429 ends
the run with exit code 3, and that host is not asked again on later runs until its wait is over.

relation "own"   the tracked person's own podcast: every episode is theirs.
relation "host"  a show that interviews people: person_id is "host:<show>", and select_episodes.py
                 later keeps only the episodes that name a tracked person. Each episode also gets
                 notes_marks: the names of the marks in its show notes that say the session is
                 channeled live (interview_types.py reads them). The notes themselves are not kept.

    python3 pipeline/fetch_feeds.py                 # every accepted feed not read in the last day
    python3 pipeline/fetch_feeds.py --refresh       # read them all again
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, HostGates, add_root_arg, append_jsonl, atomic_write_text, ensure_outside_git,  # noqa: E402
                    host_of, http_error_class, latest_by_key, layout, read_csv, read_jsonl, resting_hosts, say_refused,
                    say_resting, utc_now)
from feeds import FetchError, feed_key, get_bytes, parse_feed  # noqa: E402
from interview_types import from_notes, notes_by_episode  # noqa: E402

REGISTRY = ET_ROOT / "sources" / "podcast_feeds.csv"


def read_registry(path, accept):
    rows = []
    for row in read_csv(path) if Path(path).exists() else []:
        if row.get("feed_url") and row.get("person_id") and row.get("verification") in accept \
                and row.get("relation") in ("own", "host"):
            rows.append({**row, "feed_key": feed_key(row["person_id"], row["feed_url"])})
    return rows


def fetch_one(row, feeds_dir, gates, timeout):
    host = host_of(row["feed_url"])
    rec = {"feed_key": row["feed_key"], "person_id": row["person_id"], "relation": row["relation"],
           "feed_url": row["feed_url"], "host": host, "started": utc_now()}
    if gates.blocked(host):
        return None  # not attempted: the next run picks it up
    gates.wait(host)
    if gates.blocked(host):
        return None  # it refused while this request waited for its turn
    t0 = time.time()
    try:
        final_url, _, body = get_bytes(row["feed_url"], timeout=timeout)
        parsed = parse_feed(body, row["feed_url"], row["person_id"])
    except FetchError as err:
        klass = err.klass or (http_error_class(err.status) if err.status else "network")
        if klass in ("rate_limited", "forbidden"):
            gates.hard_block(host, err.retry_after)
        elif err.retry_after:
            gates.unavailable(host, err.retry_after)          # a 503 that says how long to wait: obeyed
        rec.update(status="error", http_status=err.status, error_class=klass, error_tail=str(err)[-300:])
        if err.retry_after is not None:
            rec["retry_after_s"] = err.retry_after
        return rec
    except Exception as err:  # noqa: BLE001 - malformed XML and the like: record it and go on
        rec.update(status="error", http_status=200, error_class="parse", error_tail=f"{type(err).__name__}: {err}"[-300:])
        return rec
    gates.success(host)
    marks = {}
    if row["relation"] == "host":
        # Whether an interview's show notes say the session is channeled live in the episode, read here from
        # the feed this run fetched anyway (interview_types.py used to fetch every interview feed again). Only
        # the names of the marks found are kept, never the notes themselves.
        marks = {ident: from_notes(text) for ident, text in notes_by_episode(body, row["person_id"]).items()}
    lines = [json.dumps({**episode, "feed_key": row["feed_key"], "person_id": row["person_id"],
                         "relation": row["relation"],
                         **({"notes_marks": marks.get(episode["video_id"], [])} if row["relation"] == "host" else {})},
                        ensure_ascii=False, separators=(",", ":"))
             for episode in parsed["episodes"]]
    atomic_write_text(feeds_dir / f"{row['feed_key']}.jsonl", "\n".join(lines) + ("\n" if lines else ""))
    feed = parsed["feed"]
    rec.update(status="ok", http_status=200, final_host=host_of(final_url), elapsed_s=round(time.time() - t0, 1),
               title=feed["title"], author=feed["author"], owner_name=feed["owner_name"], link=feed["link"],
               language=feed["language"], items=feed["items"], episodes=feed["episodes"],
               with_duration=feed["with_duration"], known_hours=feed["known_hours"],
               with_transcript=feed["with_transcript"], earliest=feed["earliest"], latest=feed["latest"],
               bytes=feed["bytes"], sha256=feed["sha256"], error_class="", error_tail="")
    if row["relation"] == "host":
        rec["notes_marks_read"] = True
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--accept", default="verified,name-match", help="verification values to read")
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--refresh", action="store_true", help="read feeds again even if read within --max-age-hours")
    ap.add_argument("--max-age-hours", type=float, default=24.0)
    ap.add_argument("--ask-resting", action="store_true",
                    help="ask hosts that refused on an earlier run again, before their wait is over")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--min-interval", type=float, default=1.0, help="seconds between requests to one host")
    ap.add_argument("--timeout", type=int, default=90)
    args = ap.parse_args()

    paths = layout(ensure_outside_git(args.root))
    manifest = paths.feeds / "feeds_manifest.jsonl"
    rows = read_registry(args.registry, {x.strip() for x in args.accept.split(",") if x.strip()})
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        rows = [r for r in rows if r["person_id"] in wanted]
    seen = latest_by_key(read_jsonl(manifest), "feed_key")
    now = time.time()

    def fresh(row):
        prev = seen.get(row["feed_key"])
        if not prev or prev.get("status") != "ok" or not (paths.feeds / f"{row['feed_key']}.jsonl").exists():
            return False
        if row["relation"] == "host" and not prev.get("notes_marks_read"):
            return False      # read before the show notes' marks were kept: read once more
        try:
            age = now - time.mktime(time.strptime(prev["started"], "%Y-%m-%dT%H:%M:%SZ")) + time.timezone
        except (KeyError, ValueError):
            return False
        return age < args.max_age_hours * 3600

    todo = [r for r in rows if args.refresh or not fresh(r)]
    recent = len(rows) - len(todo)
    # a host that refused on an earlier run is not asked again before its wait is over
    resting = {} if args.ask_resting else resting_hosts(read_jsonl(manifest), lambda r: r.get("host") or "")
    waiting = collections.Counter(host_of(r["feed_url"]) for r in todo if host_of(r["feed_url"]) in resting)
    say_resting(resting, waiting, "feed(s)")
    todo = [r for r in todo if host_of(r["feed_url"]) not in resting]
    print(f"feeds accepted {len(rows)} | read recently {recent} | to read {len(todo)}"
          + (f" | waiting for a host that refused {sum(waiting.values())}" if waiting else ""), file=sys.stderr)
    gates = HostGates(args.min_interval)
    ok = failed = skipped = 0
    with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for rec in pool.map(lambda r: fetch_one(r, paths.feeds, gates, args.timeout), todo):
            if rec is None:
                skipped += 1
                continue
            append_jsonl(manifest, rec)
            ok += rec["status"] == "ok"
            failed += rec["status"] != "ok"
    latest = latest_by_key(read_jsonl(manifest), "feed_key")
    good = [latest[r["feed_key"]] for r in rows if latest.get(r["feed_key"], {}).get("status") == "ok"]
    print(f"read {ok} ok, {failed} failed, {skipped} not attempted | on disk: {len(good)} feeds, "
          f"{sum(g['episodes'] for g in good)} episodes, {sum(g['known_hours'] for g in good):.0f} h with known length, "
          f"{sum(g['with_transcript'] for g in good)} with a publisher transcript link")
    if say_refused(gates):                       # any refusal, not only a tripped breaker: the cycle report says so
        sys.exit(3)


if __name__ == "__main__":
    main()
