#!/usr/bin/env python3
"""One collection cycle from a cloud server: everything that works without a home connection.

This is the routine an agent (or a person) runs again and again. Every step is one of the existing
scripts, each resumable, so a cycle that is stopped or refused is simply run again:

    list     discover.py              what each tracked channel holds now (a listing older than a week is redone)
    feeds    fetch_feeds.py           the registered podcast feeds, the makers' own and the interview shows'
    queue    select_episodes.py       what to fetch: own feeds, creator files, archive.org audio, and
                                      interviews of the kind asked for (live channeling unless told otherwise)
    fetch    download_enclosures.py   the audio, down to the free-space floor
    texts    fetch_publisher_text.py  transcripts and pages the publishers offer
    kinds    interview_types.py       what kind each interview episode is
    speech   transcribe.py            speech-to-text for audio without text (only with --transcribe MODEL)
    tables   catalog.py, targets.py,  the catalogue, the coverage table, the target list and the list of
             sources_table.py         sources with their links and methods (published to plan/)

Without --go it prints the plan and does nothing. It never touches YouTube audio or captions: that is
run_all.py's job, on a home connection. A step that ends with code 3 (a source refused requests) or 4
(the disk floor was reached) does not stop the cycle: the later steps still record where things stand.
Anything else does.

    python3 pipeline/run_cycle.py                       # show the plan
    python3 pipeline/run_cycle.py --go                  # run it
    python3 pipeline/run_cycle.py --go --skip list,speech --max-hours 50
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import add_root_arg, ensure_outside_git, utc_now  # noqa: E402

HERE = Path(__file__).resolve().parent
STEPS = ("list", "feeds", "queue", "fetch", "texts", "kinds", "speech", "tables")
SOFT = (0, 3, 4)        # done, a source refused, the disk floor: the cycle goes on


def build_plan(args, root):
    py, base = [sys.executable, "-I"], ["--root", str(root)]
    queue = root / "jobs" / "queue_cycle.csv"
    select = py + [str(HERE / "select_episodes.py"), *base, "--out", str(queue), "--interview-types", args.interview_types]
    if args.only:
        select += ["--only", args.only]
    if args.max_hours:
        select += ["--max-hours", str(args.max_hours)]
    plan = {
        "list": [py + [str(HERE / "discover.py"), *base, "--ytdlp", args.ytdlp, "--workers", "1", "--min-interval", "5",
                       "--max-age-days", str(args.relist_days)]],
        "feeds": [py + [str(HERE / "fetch_feeds.py"), *base]],
        "queue": [select],
        "fetch": [py + [str(HERE / "download_enclosures.py"), *base, "--queue", str(queue), "--all", "--workers", "2",
                        "--per-host", "2", "--min-free-gb", str(args.min_free_gb)]],
        "texts": [py + [str(HERE / "fetch_publisher_text.py"), *base, "--all"]],
        "kinds": [py + [str(HERE / "interview_types.py"), *base, "--notes"]],
        "speech": [py + [str(HERE / "transcribe.py"), *base, "--model", args.transcribe, "--device", "cpu", "--compute-type", "int8",
                         "--workers", "1", "--cpu-threads", "2", "--batch-size", "8", "--order", "round-robin"]] if args.transcribe else [],
        "tables": [py + [str(HERE / "catalog.py"), *base, "--publish"], py + [str(HERE / "targets.py"), *base],
                   py + [str(HERE / "sources_table.py"), *base]],
    }
    if args.only and plan["list"]:
        plan["list"][0] += ["--only", args.only]
    return [(step, cmd) for step in STEPS if step not in args.skip for cmd in plan[step]]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--skip", default="", help="steps to leave out, comma-separated: " + ", ".join(STEPS))
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--interview-types", default="live channeling", help="kinds of interview episode to fetch (see select_episodes.py)")
    ap.add_argument("--max-hours", type=float, default=0, help="queue at most this many hours of audio in this cycle")
    ap.add_argument("--min-free-gb", type=float, default=3.0, help="stop downloading when the disk has less than this free")
    ap.add_argument("--relist-days", type=float, default=7, help="list a channel again when its listing is older than this")
    ap.add_argument("--transcribe", default="", help="model name: also run speech-to-text (takes days on a small machine)")
    ap.add_argument("--ytdlp", default="yt-dlp")
    ap.add_argument("--go", action="store_true", help="run it (without this the plan is only printed)")
    args = ap.parse_args()
    args.skip = {x.strip() for x in args.skip.split(",") if x.strip()}
    if args.skip - set(STEPS):
        sys.exit("--skip takes any of: " + ", ".join(STEPS))
    root = ensure_outside_git(args.root)
    plan = build_plan(args, root)
    print("CYCLE PLAN")
    for step, cmd in plan:
        print(f"  {step:7s} {' '.join(cmd[2:])}")
    if not args.transcribe and "speech" not in args.skip:
        print("  speech  (left out: pass --transcribe MODEL to include it)")
    if not args.go:
        print("dry run: add --go to run this cycle")
        return
    worst, log = 0, []
    for step, cmd in plan:
        started = utc_now()
        code = subprocess.run(cmd).returncode
        log.append((step, Path(cmd[2]).name, code, started))
        if code not in SOFT:
            print(f"STOPPED: {Path(cmd[2]).name} ended with exit code {code}", file=sys.stderr)
            worst = code
            break
        worst = max(worst, code)
    print("CYCLE REPORT")
    for step, script, code, started in log:
        note = {0: "done", 3: "a source refused requests: wait and run the cycle again", 4: "disk floor reached"}.get(code, f"failed ({code})")
        print(f"  {step:7s} {script:26s} {started}  {note}")
    sys.exit(worst)


if __name__ == "__main__":
    main()
