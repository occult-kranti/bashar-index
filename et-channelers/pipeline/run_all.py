#!/usr/bin/env python3
"""One command for a whole collection run: download in parallel, upload, check, delete, report.

Meant for your own computer, where YouTube answers normally. It starts the existing steps side by
side and a watcher that keeps moving finished items to your private store and freeing the disk:

    lanes   youtube     download_audio.py     audio of the queued YouTube videos (yt-dlp)
            captions    fetch_captions.py     YouTube's own caption tracks for the same videos
            enclosures  download_enclosures.py  podcast episodes and creator-hosted files
            texts       fetch_publisher_text.py  transcripts the publishers wrote
    then    transcribe  transcribe.py         speech-to-text for audio that has no text (optional)
    always  sync        sync_archive.py       upload, verify, delete the local copy
            catalog     catalog.py            the index and the per-person coverage table

Without --go it only prints the plan. The store is checked before anything is downloaded: a GitHub
store must be a private repository, or the run stops there.

    python3 pipeline/run_all.py --store gh:you/private-archive@audio-v1                    # show the plan
    python3 pipeline/run_all.py --store gh:you/private-archive@audio-v1 --go              # run it
    python3 pipeline/run_all.py --store dir:/mnt/disk/et-archive --lanes youtube,captions --set bashar75 --go
    python3 pipeline/run_all.py --store gh:you/private-archive@audio-v1 --transcribe large-v3 --devices 0 --go

Exit code: 0 clean, 3 a source refused requests (wait and rerun), 4 the disk floor was reached,
5 the store was refused. Everything is resumable: run the same command again.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import add_root_arg, ensure_outside_git, layout  # noqa: E402
from sync_archive import StoreError, open_store  # noqa: E402

HERE = Path(__file__).resolve().parent
LANES = ("youtube", "captions", "enclosures", "texts")


def build_plan(args, root):
    py, base = [sys.executable, "-I"], ["--root", str(root)]
    prepare, parallel, after = [], [], []
    if {"youtube", "captions"} & set(args.lanes):
        cmd = py + [str(HERE / "select_jobs.py"), *base, "--set", args.set]
        if args.per_channel:
            cmd += ["--per-channel", str(args.per_channel)]
        prepare.append(("queue: YouTube videos", cmd))
    if "enclosures" in args.lanes:
        prepare.append(("queue: podcast episodes and creator files", py + [str(HERE / "fetch_feeds.py"), *base]))
        cmd = py + [str(HERE / "select_episodes.py"), *base]
        if args.per_channel:
            cmd += ["--per-channel", str(args.per_channel)]
        prepare.append(("queue: choose episodes", cmd))
    if "youtube" in args.lanes:
        parallel.append(("youtube", py + [str(HERE / "download_audio.py"), *base, "--all", "--workers", str(args.workers),
                                          "--min-interval", str(args.min_interval)]))
    if "captions" in args.lanes:
        parallel.append(("captions", py + [str(HERE / "fetch_captions.py"), *base, "--all", "--workers", "2",
                                           "--min-interval", str(max(2.0, args.min_interval))]))
    if "enclosures" in args.lanes:
        parallel.append(("enclosures", py + [str(HERE / "download_enclosures.py"), *base, "--all", "--workers",
                                             str(args.workers), "--min-free-gb", str(args.min_free_gb)]))
    if "texts" in args.lanes:
        parallel.append(("texts", py + [str(HERE / "fetch_publisher_text.py"), *base, "--all"]))
    if args.transcribe:
        cmd = py + [str(HERE / "transcribe.py"), *base, "--model", args.transcribe]
        cmd += ["--devices", args.devices] if args.devices else ["--device", "cpu", "--compute-type", "int8"]
        after.append(("transcribe", cmd))
    sync = py + [str(HERE / "sync_archive.py"), "push", *base, "--store", args.store, "--delete", args.delete,
                 "--watch", str(args.watch), "--stop-file", str(root / "sync" / ".stop"), "--gh", args.gh]
    if args.transcribe:
        sync.append("--hold-untranscribed")
    final_sync = [a for a in sync if a not in ("--watch", str(args.watch), "--stop-file", str(root / "sync" / ".stop"))]
    return prepare, parallel, after, sync, final_sync, py + [str(HERE / "catalog.py"), *base]


def stream(label, proc):
    for line in proc.stdout:
        print(f"[{label}] {line.rstrip()}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--store", required=True, help="gh:OWNER/REPO@TAG (private repository) or dir:/folder")
    ap.add_argument("--lanes", default=",".join(LANES), help="comma-separated: " + ", ".join(LANES))
    ap.add_argument("--set", default="all", choices=("bashar75", "indexed", "channeling", "all"), help="which YouTube videos")
    ap.add_argument("--per-channel", type=int, default=0, help="sample at most K items per person (0 = everything)")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--min-interval", type=float, default=3.0, help="seconds between YouTube download starts")
    ap.add_argument("--min-free-gb", type=float, default=5.0)
    ap.add_argument("--delete", choices=("none", "audio", "all"), default="audio",
                    help="local copies to remove once the stored copy is checked (default audio)")
    ap.add_argument("--watch", type=float, default=60, help="seconds between upload passes")
    ap.add_argument("--transcribe", default="", help="model name: also run speech-to-text after the downloads")
    ap.add_argument("--devices", default="", help="GPU ids for --transcribe, e.g. 0 or 0,1 (default: CPU)")
    ap.add_argument("--gh", default="gh")
    ap.add_argument("--go", action="store_true", help="run it (without this the plan is only printed)")
    args = ap.parse_args()
    args.lanes = [x.strip() for x in args.lanes.split(",") if x.strip() in LANES]

    root = ensure_outside_git(args.root)
    prepare, parallel, after, sync, final_sync, catalog = build_plan(args, root)
    print("PLAN")
    for label, cmd in prepare:
        print(f"  first      {label}: {' '.join(cmd[2:])}")
    for label, cmd in parallel:
        print(f"  side by side  {label}: {' '.join(cmd[2:])}")
    print(f"  meanwhile  sync: {' '.join(sync[2:])}")
    for label, cmd in after:
        print(f"  then       {label}: {' '.join(cmd[2:])}")
    print(f"  last       catalog: {' '.join(catalog[2:])}")
    if not args.go:
        print("dry run: add --go to run this plan")
        return
    try:
        print("store: " + open_store(args.store, args.gh).check_private())
    except StoreError as err:
        print(f"STOPPED: {err}", file=sys.stderr)
        sys.exit(5)

    worst = 0
    for label, cmd in prepare:
        done = subprocess.run(cmd)
        if done.returncode not in (0, 3):
            sys.exit(f"{label} failed with exit code {done.returncode}")
        worst = max(worst, done.returncode)
    stop = layout(root).root / "sync" / ".stop"
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.unlink(missing_ok=True)
    watcher = subprocess.Popen(sync, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    threads = [threading.Thread(target=stream, args=("sync", watcher), daemon=True)]
    procs = []
    for label, cmd in parallel:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        procs.append((label, proc))
        threads.append(threading.Thread(target=stream, args=(label, proc), daemon=True))
    for t in threads:
        t.start()
    try:
        for label, proc in procs:
            worst = max(worst, proc.wait())
        for label, cmd in after:
            worst = max(worst, subprocess.run(cmd).returncode)
    finally:
        stop.write_text("stop\n")
        try:
            watcher.wait(timeout=args.watch + 600)
        except subprocess.TimeoutExpired:
            watcher.terminate()
    worst = max(worst, subprocess.run(final_sync).returncode)   # one last pass picks up the stragglers
    subprocess.run(catalog)
    stop.unlink(missing_ok=True)
    print({0: "done", 3: "STOPPED: a source refused requests; wait and run the same command again",
           4: "STOPPED: disk floor reached; the store has what was finished, run again to continue",
           5: "STOPPED: the store refused the upload"}.get(worst, f"finished with exit code {worst}"))
    sys.exit(worst)


if __name__ == "__main__":
    main()
