#!/usr/bin/env python3
"""One command for a whole collection run: download in parallel, upload, check, delete, report.

Meant for your own computer, where YouTube answers normally. It starts the existing steps side by
side and a watcher that keeps moving finished items to your private store and freeing the disk:

    check   tools       yt-dlp, ffmpeg, ffprobe  run and print their versions (with --go, before anything starts)
    first   list        discover.py           what every tracked channel holds (with --set all, the default)
    lanes   youtube     download_audio.py     audio of the queued YouTube videos (yt-dlp)
            captions    fetch_captions.py     YouTube's own caption tracks for the same videos
            enclosures  download_enclosures.py  podcast episodes and creator-hosted files
            texts       fetch_publisher_text.py  transcripts the publishers wrote
    beside  transcribe  transcribe.py         speech-to-text for the audio that has arrived, every
                                              --transcribe-every seconds while the lanes run (optional)
    then    transcribe  transcribe.py         one last pass once the lanes have ended (optional)
    always  sync        sync_archive.py       upload, verify, delete the local copy
            catalog     catalog.py            the index and the per-person coverage table

Without --go it only prints the plan. The store is checked before anything is downloaded: a GitHub
store must be a private repository, or the run stops there. Then the tools are checked: a yt-dlp or
ffmpeg the lanes need that cannot be run stops the run before any request, and a yt-dlp released more
than 60 days ago is named with a warning (YouTube changes often, and an old yt-dlp fails in ways that
look like blocks). Once the YouTube queue is built (and in the plan, when the queue on disk was built for
the same selection) the run says how many videos and known hours it holds and the least time each YouTube
lane takes at its pace.

    python3 pipeline/run_all.py --store gh:you/private-archive@audio-v1                    # show the plan
    python3 pipeline/run_all.py --store gh:you/private-archive@audio-v1 --go              # run it
    python3 pipeline/run_all.py --store dir:/mnt/disk/et-archive --lanes youtube,captions --set bashar75 --go
    python3 pipeline/run_all.py --store gh:you/private-archive@audio-v1 --transcribe large-v3 --devices 0 --go
    python3 pipeline/run_all.py --store gh:you/private-archive@audio-v1 --lanes youtube,captions --newest 10 --go

With --newest the YouTube queue is in rank order (every channel's newest video, then every channel's
second newest, ...), so a run stopped halfway has the newest videos of every channel.

    python3 pipeline/run_all.py --store dir:/mnt/disk/et-archive --lanes youtube,captions --queue queue_blackouts.csv --go
    python3 pipeline/run_all.py --store dir:/mnt/disk/et-archive --lanes captions --queue queue_youtube_all.csv --go

With --queue (repeatable) the YouTube lanes work through queue files built elsewhere (select_jobs.py --out,
or a queue from the private store's release) instead of listing the channels and building a queue here: the
listing and queue steps are skipped. The files are merged, in the order given, into <root>/jobs/queue_run.csv
(a video that appears twice keeps its first row; the columns are the first file's) and both lanes read that
one file, so the merge happens before anything is sent and the estimate counts what the lanes will see. Rows
already finished or settled are skipped by the lanes' own rules, as always. A file that is missing or has no
video_id column stops the run before anything starts (exit code 2). --queue cannot be combined with --newest,
--per-channel or --set (the files already say which videos).

Exit code: 0 clean, 2 the options or a queue file are wrong, 3 a source refused requests (wait and rerun), 4 the disk floor was reached,
5 the store was refused, 6 the setup is not ready (a tool the lanes need cannot be run, or a lane stopped
on failures that point at the setup), 9 nothing was left to run once the YouTube lanes were skipped by rule.
Everything is resumable: run the same command again.

The YouTube lanes (the channel listing, youtube, captions) are off unless the owner sets
ET_YOUTUBE_ROBOTS_OVERRIDE=1: yt-dlp asks youtube.com's /youtubei/ for listings, the player and captions,
and youtube.com's robots.txt disallows that path. Without the variable they are left out of the plan with
one line saying so, and the other lanes run as usual.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (SKIPPED_BY_RULE, YOUTUBE_OVERRIDE, YOUTUBE_RULE, add_root_arg, archived_ids,  # noqa: E402
                    atomic_write_text, ensure_outside_git, latest_by_key, layout, read_csv, read_jsonl, run_cmd,
                    write_csv, youtube_override)
from sync_archive import StoreError, open_store  # noqa: E402

HERE = Path(__file__).resolve().parent
LANES = ("youtube", "captions", "enclosures", "texts")
CAPTIONS_MIN_INTERVAL = 5.0       # captions and audio hit the same site: never faster than this, nor than the audio lane
TOOLS = {"yt-dlp": ("ytdlp", "--version"), "ffmpeg": ("ffmpeg", "-version"), "ffprobe": ("ffprobe", "-version")}
YTDLP_MAX_AGE_DAYS = 60
GIVE_UP_AFTER = 3                 # failed transcription passes in a row before the loop beside the lanes stops


def tool_flags(args, *names):
    """--ytdlp / --ffmpeg / --ffprobe for a step, only where the owner named a path other than the default."""
    flags = []
    for name in names:
        dest = TOOLS[name][0]
        if getattr(args, dest) != name:
            flags += [f"--{dest}", getattr(args, dest)]
    return flags


def build_plan(args, root):
    py, base = [sys.executable, "-I"], ["--root", str(root)]
    prepare, parallel, after = [], [], []
    queue_flag = ["--queue", str(run_queue_path(root))] if args.queue else []
    if {"youtube", "captions"} & set(args.lanes) and args.queue:
        pass                                            # the queue files say which videos: no listing, no queue step
    elif {"youtube", "captions"} & set(args.lanes):
        if args.set == "all":
            # "all" is every video the channels list, so the channels are listed first: public metadata, no
            # media, and channels already listed are skipped. Without this the queue would hold only the few
            # hundred videos the 2026-10 index happened to record.
            listing = py + [str(HERE / "discover.py"), *base, "--workers", "1", "--min-interval", "5"]
            if args.newest:
                # only the head of each Videos tab is wanted: list that much, and list it again if it is a day old
                listing += ["--tabs", "videos", "--max-per-channel", str(args.newest), "--max-age-days", "1"]
                prepare.append((f"list: the newest {args.newest} videos of every tracked channel",
                                listing + tool_flags(args, "yt-dlp")))
            else:
                prepare.append(("list: every video on every tracked channel", listing + tool_flags(args, "yt-dlp")))
        cmd = py + [str(HERE / "select_jobs.py"), *base, "--set", args.set]
        if args.newest:
            cmd += ["--newest", str(args.newest)]      # select_jobs.py puts a --newest queue in rank order
        elif args.per_channel:
            cmd += ["--per-channel", str(args.per_channel)]
        prepare.append(("queue: YouTube videos", cmd))
    if "enclosures" in args.lanes:
        prepare.append(("queue: podcast episodes and creator files", py + [str(HERE / "fetch_feeds.py"), *base]))
        cmd = py + [str(HERE / "select_episodes.py"), *base]
        if args.per_channel:
            cmd += ["--per-channel", str(args.per_channel)]
        prepare.append(("queue: choose episodes", cmd))
    if "youtube" in args.lanes:
        parallel.append(("youtube", py + [str(HERE / "download_audio.py"), *base, *queue_flag, "--all",
                                          "--workers", str(args.workers), "--min-interval", str(args.min_interval),
                                          "--min-free-gb", str(args.min_free_gb)]
                         + tool_flags(args, "yt-dlp", "ffmpeg", "ffprobe")))
    if "captions" in args.lanes:
        # captions and audio hit the same site: one caption worker, never faster than the audio lane
        parallel.append(("captions", py + [str(HERE / "fetch_captions.py"), *base, *queue_flag, "--all", "--workers", "1",
                                           "--min-interval", str(captions_interval(args))] + tool_flags(args, "yt-dlp")))
    if "enclosures" in args.lanes:
        parallel.append(("enclosures", py + [str(HERE / "download_enclosures.py"), *base, "--all", "--workers", "3",
                                             "--min-free-gb", str(args.min_free_gb)] + tool_flags(args, "ffmpeg", "ffprobe")))
    if "texts" in args.lanes:
        parallel.append(("texts", py + [str(HERE / "fetch_publisher_text.py"), *base, "--all"]))
    if args.transcribe:
        cmd = py + [str(HERE / "transcribe.py"), *base, "--model", args.transcribe]
        cmd += ["--devices", args.devices] if args.devices else ["--device", "cpu", "--compute-type", "int8"]
        after.append(("transcribe", cmd + tool_flags(args, "ffmpeg")))
    sync = py + [str(HERE / "sync_archive.py"), "push", *base, "--store", args.store, "--delete", args.delete,
                 "--watch", str(args.watch), "--stop-file", str(root / "sync" / ".stop"), "--gh", args.gh]
    if args.transcribe:
        sync.append("--hold-untranscribed")
    final_sync = [a for a in sync if a not in ("--watch", str(args.watch), "--stop-file", str(root / "sync" / ".stop"))]
    return prepare, parallel, after, sync, final_sync, py + [str(HERE / "catalog.py"), *base]


def captions_interval(args):
    return max(CAPTIONS_MIN_INTERVAL, args.min_interval)


def alongside_cmd(args, parallel, after):
    """The transcription command to run beside the lanes, or None (not asked for, turned off, or no lanes)."""
    if not (args.transcribe and args.transcribe_every > 0 and parallel):
        return None
    return next(cmd for label, cmd in after if label == "transcribe")


def stream(label, proc):
    for line in proc.stdout:
        print(f"[{label}] {line.rstrip()}", flush=True)


# ---------------------------------------------------------------- the tools, checked before anything starts
def needed_tools(args):
    """{tool: True if the run cannot work without it} for the lanes of this run."""
    need = {}
    if {"youtube", "captions"} & set(args.lanes):
        need["yt-dlp"] = True                       # the listing, the audio and the captions
    if "youtube" in args.lanes or "enclosures" in args.lanes or args.transcribe:
        need["ffmpeg"] = True                       # the encode, and the decode for the model
    if "youtube" in args.lanes or "enclosures" in args.lanes:
        need["ffprobe"] = False                     # lengths only: without it they are recorded as unknown
    return need


def release_age_days(version, today):
    """Days since the release date in a yt-dlp version ('2026.10.26', '2026.10.26.232915'), or None."""
    match = re.search(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", version or "")
    if not match:
        return None
    try:
        return (today - dt.date(*map(int, match.groups()))).days
    except ValueError:
        return None


def preflight(args, needed, today=None, out=None):
    """Run every tool the lanes will run (the same paths) for its version and print one line each. Returns
    the tools the run needs that cannot be run. An old yt-dlp is a warning, not a stop."""
    today, out = today or dt.date.today(), out or sys.stdout
    hints = {"yt-dlp": "install or update it (python -m pip install -U yt-dlp, see pipeline/README.md), or pass --ytdlp PATH",
             "ffmpeg": "install ffmpeg and put it on PATH (see pipeline/README.md), or pass --ffmpeg PATH",
             "ffprobe": "it comes with ffmpeg: put it on PATH or pass --ffprobe PATH"}
    missing = []
    for name, required in needed.items():
        dest, flag = TOOLS[name]
        path = getattr(args, dest)
        found = shutil.which(path)
        if found:
            try:
                code, stdout, stderr = run_cmd([found, flag], 60)
            except OSError as err:      # there, but the system will not start it: another build, blocked, damaged
                code, stdout, stderr = 126, "", str(err)
            version = next((line.strip() for line in (stdout or "").splitlines() if line.strip()), "")
        if not found or code != 0 or not version:
            why = (f"not found: {path!r} is not on PATH and is not a program" if not found else
                   f"cannot be run: {found} ended with code {code}: {(stderr or stdout or '').strip()[-200:]}")
            print(f"  {name:8} {why}. {hints[name]}" + ("" if required else "; going on, lengths are recorded as unknown"),
                  file=out, flush=True)
            if required:
                missing.append(name)
            continue
        print(f"  {name:8} {version[:80]}  ({found})", file=out, flush=True)
        if name == "yt-dlp":
            age = release_age_days(version, today)
            if age is None:
                print(f"  WARNING: no release date in yt-dlp's version {version[:40]!r}: make sure it is recent. Going on.",
                      file=out, flush=True)
            elif age > YTDLP_MAX_AGE_DAYS:
                print(f"  WARNING: this yt-dlp was released {age} days ago (more than {YTDLP_MAX_AGE_DAYS}). YouTube changes "
                      "often, and an old yt-dlp fails in ways that look like blocks (no formats, 403, bot checks), which "
                      "stop the lanes. Update it first: yt-dlp -U, or python -m pip install -U yt-dlp. Going on.",
                      file=out, flush=True)
    return missing


# ---------------------------------------------------------------- queue files given with --queue
class QueueError(Exception):
    pass


def run_queue_path(root):
    return layout(root).jobs / "queue_run.csv"


def load_queues(files):
    """Read the --queue files in order and merge them: every row with a video_id, the first row of a video that
    appears more than once, the first file's columns. Returns (rows, fields, duplicates dropped). Raises
    QueueError, naming the file, when one is missing, cannot be read or has no video_id column."""
    rows, fields, seen, dropped = [], None, set(), 0
    for path in files:
        path = Path(path)
        if not path.is_file():
            raise QueueError(f"queue file not found: {path}")
        try:
            with open(path, newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                header, read = reader.fieldnames or [], list(reader)
        except (OSError, UnicodeDecodeError, csv.Error) as err:
            raise QueueError(f"queue file cannot be read: {path}: {err}") from None
        if "video_id" not in header:
            raise QueueError(f"queue file has no video_id column: {path} (columns: {', '.join(header) or 'none'}); "
                             "a queue is what select_jobs.py writes, or a queue_*.csv from the private store")
        fields = fields or list(header)
        for row in read:
            vid = (row.get("video_id") or "").strip()
            if not vid:
                continue
            if vid in seen:
                dropped += 1
                continue
            seen.add(vid)
            rows.append({k: v for k, v in row.items() if k is not None})
    return rows, fields, dropped


def write_run_queue(root, args):
    """<root>/jobs/queue_run.csv and its meta file from the merged --queue files (with --go only)."""
    out = run_queue_path(root)
    rows, fields, dropped = args.queue_rows, args.queue_fields, args.queue_dropped
    write_csv(out, rows, fields)
    meta = {"created": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "files": [str(Path(p).resolve()) for p in args.queue], "videos": len(rows), "duplicates_dropped": dropped,
            "channels": len({r.get("channel_dir") or "" for r in rows})}
    atomic_write_text(out.with_name(out.stem + ".meta.json"), json.dumps(meta, indent=2) + "\n")
    print(f"queue: {len(rows)} videos from {len(args.queue)} file(s) ({dropped} repeated rows dropped) -> {out}", flush=True)


# ---------------------------------------------------------------- what the YouTube queue holds and how long it takes
def tier_queue(root, args):
    """The rows of <root>/jobs/queue.csv if select_jobs.py built it for this run's selection, else None."""
    jobs = layout(root).jobs
    try:
        meta = json.loads((jobs / "queue.meta.json").read_text(encoding="utf-8"))
        same = (meta.get("set") == args.set and int(meta.get("newest") or 0) == args.newest
                and int(meta.get("per_channel") or 0) == (0 if args.newest else args.per_channel))
        return [r for r in read_csv(jobs / "queue.csv") if r.get("video_id")] if same else None
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def lanes_to_do(root, rows):
    """{lane: rows still to do}, by the rules the lanes themselves skip an item with."""
    from download_audio import SKIP_LATER as AUDIO_SETTLED
    from fetch_captions import SKIP_LATER as CAPTIONS_SETTLED
    paths = layout(root)
    audio = latest_by_key(read_jsonl(paths.audio / "audio_manifest.jsonl"))
    caps = latest_by_key(read_jsonl(paths.captions / "captions_manifest.jsonl"))
    stored = archived_ids(root, "audio")

    def audio_left(row):
        prev = audio.get(row["video_id"])
        if prev and prev.get("status") == "ok":
            here = paths.audio / (prev.get("path") or "-")
            return not (row["video_id"] in stored or (here.is_file() and here.stat().st_size == prev.get("bytes")))
        return not (prev and prev.get("error_class") in AUDIO_SETTLED)

    def captions_left(row):
        prev = caps.get(row["video_id"])
        return not (prev and (prev.get("status") == "ok" or prev.get("error_class") in CAPTIONS_SETTLED))
    return {"youtube": [r for r in rows if audio_left(r)], "captions": [r for r in rows if captions_left(r)]}


def span(seconds):
    return f"{seconds:.0f} s" if seconds < 90 else f"{seconds / 60:.0f} min" if seconds < 5400 else f"{seconds / 3600:.1f} h"


def known_hours(rows):
    known = []
    for r in rows:
        try:
            known.append(float(r.get("duration_s") or ""))
        except ValueError:
            pass
    return sum(known) / 3600, len(rows) - len(known)


def pacing_floor(n, interval):
    """The least wall time n items take at one start per `interval` seconds. The limit is shared by all of a
    lane's workers, so more workers do not shorten it; the downloads and encodes themselves come on top."""
    return max(0, n - 1) * interval


def estimate_lines(root, args):
    """What the YouTube queue holds and the least time each YouTube lane takes, or one line saying it is not built."""
    if not {"youtube", "captions"} & set(args.lanes):
        return []
    rows = args.queue_rows if args.queue else tier_queue(root, args)
    if rows is None:
        return ["  estimate   jobs/queue.csv was not built for this selection yet: its videos, known hours and the "
                "least time each lane takes are printed once the queue step has built it"]
    hours, unknown = known_hours(rows)
    what = (f"--queue {', '.join(Path(p).name for p in args.queue)}" if args.queue else
            f"the newest {args.newest} of every channel" if args.newest else f"--set {args.set}")
    lines = [f"  estimate   queue for {what}: {len(rows)} videos from {len({r.get('channel_dir') or '' for r in rows})} "
             f"channels, {hours:.1f} h with known length ({unknown} unknown)"]
    todo = lanes_to_do(root, rows)
    if "youtube" in args.lanes:
        left, (h, _) = todo["youtube"], known_hours(todo["youtube"])
        lines.append(f"             youtube   {len(left)} to do ({h:.1f} h known): at least "
                     f"{span(pacing_floor(len(left), args.min_interval))} at a start every {args.min_interval:g} s shared "
                     f"by {args.workers} worker(s); the downloads and encodes add to it")
    if "captions" in args.lanes:
        left = todo["captions"]
        lines.append(f"             captions  {len(left)} to do: at least {span(pacing_floor(len(left), captions_interval(args)))} "
                     f"at a start every {captions_interval(args):g} s, 1 worker; yt-dlp waits 5 s more before each track")
    if args.transcribe:
        h, unknown = known_hours(todo["youtube"])
        lines.append(f"             transcribe  {h:.1f} h of new audio with known length ({unknown} unknown), "
                     + (f"as it arrives (every {args.transcribe_every:g} s) and once more at the end"
                        if args.transcribe_every > 0 else "after the lanes"))
    return lines


# ---------------------------------------------------------------- the lanes, and speech-to-text beside them
class TranscribeAlongside:
    """transcribe.py on the audio that has arrived, while the download lanes run. A pass starts every `every`
    seconds (counted from the start of the last one, so a long pass is followed at once), and never while
    another is running. It runs in its own thread and touches nothing of the lanes: a failed pass is reported
    and the loop goes on, and after GIVE_UP_AFTER failures in a row it starts no more passes. Its exit codes
    do not count; the pass after the lanes counts, as before."""

    def __init__(self, cmd, every, give_up=GIVE_UP_AFTER, label="transcribe"):
        self.cmd, self.every, self.give_up, self.label = list(cmd), float(every), give_up, label
        self.stop = threading.Event()
        self.starts, self.codes = [], []          # time.monotonic() at each pass's start, and each pass's exit code
        self._thread = threading.Thread(target=self._loop, name="transcribe-alongside", daemon=True)

    def start(self):
        self._thread.start()
        return self

    def _loop(self):
        failed = 0
        while not self.stop.is_set():
            began = time.monotonic()
            code = self._one_pass()
            self.codes.append(code)
            failed = failed + 1 if code else 0
            if failed >= self.give_up:
                print(f"[{self.label}] {failed} passes in a row failed: no more passes beside the downloads; "
                      "the pass after them still runs", flush=True)
                return
            self.stop.wait(max(0.0, self.every - (time.monotonic() - began)))

    def _one_pass(self):
        self.starts.append(time.monotonic())
        try:
            proc = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        except OSError as err:
            print(f"[{self.label}] could not start: {err}", flush=True)
            return 127
        with proc:                                 # closes the pipe and waits
            for line in proc.stdout:
                print(f"[{self.label}] {line.rstrip()}", flush=True)
        code = proc.returncode
        if code:
            print(f"[{self.label}] the pass ended with exit code {code}; the downloads go on", flush=True)
        return code

    def finish(self):
        """Start no new pass and wait for the one in progress, so the pass after the lanes never runs beside it."""
        self.stop.set()
        self._thread.join()


def run_lanes(parallel, after, alongside=None, every=0.0):
    """Start the lanes side by side and wait for all of them, with transcribe.py beside them when `alongside` is
    a command and `every` > 0; then the `after` steps, one by one. Returns the worst exit code of the lanes
    and the after steps (a pass beside the lanes never counts)."""
    procs, threads = [], []
    for label, cmd in parallel:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        procs.append(proc)
        threads.append(threading.Thread(target=stream, args=(label, proc), daemon=True))
    for t in threads:
        t.start()
    beside = TranscribeAlongside(alongside, every).start() if alongside and every > 0 and procs else None
    worst = 0
    try:
        for proc in procs:
            worst = max(worst, proc.wait())
    except BaseException:
        if beside is not None:
            beside.stop.set()                  # interrupted: no new pass (the one running got the same signal)
        raise
    for t, proc in zip(threads, procs):
        t.join(timeout=10)                     # the lanes' last lines before the next step's
        if not t.is_alive():
            proc.stdout.close()
    if beside is not None:
        beside.finish()
    for label, cmd in after:
        worst = max(worst, subprocess.run(cmd).returncode)
    return worst


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--store", required=True, help="gh:OWNER/REPO@TAG (private repository) or dir:/folder")
    ap.add_argument("--lanes", default=",".join(LANES), help="comma-separated: " + ", ".join(LANES))
    ap.add_argument("--set", default="all", choices=("bashar75", "indexed", "channeling", "all"), help="which YouTube videos")
    ap.add_argument("--per-channel", type=int, default=0, help="sample at most K items per person (0 = everything)")
    ap.add_argument("--newest", type=int, default=0,
                    help="YouTube: the newest N videos of each channel's Videos tab instead of a sample (0 = off), "
                         "every channel's newest first")
    ap.add_argument("--queue", action="append", default=[], metavar="PATH",
                    help="YouTube: run the lanes over this queue file instead of listing channels and building a queue "
                         "(repeatable, in order; the files are merged into <root>/jobs/queue_run.csv). Not with --newest, "
                         "--per-channel or --set")
    ap.add_argument("--workers", type=int, default=2, help="YouTube downloads at once (the enclosure lane uses 3)")
    ap.add_argument("--min-interval", type=float, default=10.0,
                    help="seconds between YouTube download starts (default 10, yt-dlp's own advice)")
    ap.add_argument("--min-free-gb", type=float, default=5.0)
    ap.add_argument("--delete", choices=("none", "audio", "all"), default="audio",
                    help="local copies to remove once the stored copy is checked (default audio)")
    ap.add_argument("--watch", type=float, default=60, help="seconds between upload passes")
    ap.add_argument("--transcribe", default="", help="model name: also run speech-to-text on the downloaded audio")
    ap.add_argument("--transcribe-every", type=float, default=300,
                    help="with --transcribe: seconds between speech-to-text passes while the downloads run, one at a "
                         "time (default 300; 0 = only after the downloads). One more pass follows the downloads")
    ap.add_argument("--devices", default="", help="GPU ids for --transcribe, e.g. 0 or 0,1 (default: CPU)")
    ap.add_argument("--ytdlp", default="yt-dlp", help="the yt-dlp the YouTube lanes run (default: yt-dlp on PATH)")
    ap.add_argument("--ffmpeg", default="ffmpeg", help="the ffmpeg the lanes run (default: ffmpeg on PATH)")
    ap.add_argument("--ffprobe", default="ffprobe", help="the ffprobe the lanes run (default: ffprobe on PATH)")
    ap.add_argument("--gh", default="gh")
    ap.add_argument("--go", action="store_true", help="run it (without this the plan is only printed)")
    args = ap.parse_args()
    args.lanes = [x.strip() for x in args.lanes.split(",") if x.strip() in LANES]
    if args.queue and (args.newest or args.per_channel or args.set != "all"):
        ap.error("--queue cannot be combined with --newest, --per-channel or --set: the queue files already say which videos")
    if args.queue and not {"youtube", "captions"} & set(args.lanes):
        ap.error("--queue is read by the youtube and captions lanes: name one of them in --lanes")
    held = [] if youtube_override() else [lane for lane in args.lanes if lane in ("youtube", "captions")]
    if held:
        # the YouTube lanes request paths that youtube.com's robots.txt disallows: not without the owner's decision
        args.lanes = [lane for lane in args.lanes if lane not in held]
        print(f"skipped: the {' and '.join(held)} lane(s): {YOUTUBE_RULE}. Nothing is sent to YouTube. The owner can "
              f"allow it with {YOUTUBE_OVERRIDE}=1.", file=sys.stderr, flush=True)
        if not args.lanes:
            sys.exit(SKIPPED_BY_RULE)

    root = ensure_outside_git(args.root)
    args.queue_rows = args.queue_fields = None
    if args.queue and {"youtube", "captions"} & set(args.lanes):
        try:        # read before anything else, so a wrong file stops the run before any tool runs
            args.queue_rows, args.queue_fields, args.queue_dropped = load_queues(args.queue)
        except QueueError as err:
            print(f"STOPPED: {err}. Nothing was started.", file=sys.stderr, flush=True)
            sys.exit(2)
    prepare, parallel, after, sync, final_sync, catalog = build_plan(args, root)
    beside = alongside_cmd(args, parallel, after)
    needed = needed_tools(args)
    print("PLAN")
    if needed:
        print(f"  check      tools: {', '.join(needed)} (each is run for its version before anything starts)")
    if args.queue_rows is not None:
        print(f"  first      queue: merge {', '.join(args.queue)} into {run_queue_path(root)} ({len(args.queue_rows)} videos, "
              f"{args.queue_dropped} repeated rows dropped); no channel listing, no queue step")
    for label, cmd in prepare:
        print(f"  first      {label}: {' '.join(cmd[2:])}")
    for label, cmd in parallel:
        print(f"  side by side  {label}: {' '.join(cmd[2:])}")
    if beside:
        print(f"  beside     transcribe: every {args.transcribe_every:g} s while the lanes run, one pass at a time, "
              "the same command as below")
    print(f"  meanwhile  sync: {' '.join(sync[2:])}")
    for label, cmd in after:
        print(f"  then       {label}: {' '.join(cmd[2:])}")
    print(f"  last       catalog: {' '.join(catalog[2:])}")
    for line in estimate_lines(root, args):
        print(line)
    if not args.go:
        print("dry run: add --go to run this plan")
        return
    try:
        print("store: " + open_store(args.store, args.gh, root).check_private())
    except StoreError as err:
        print(f"STOPPED: {err}", file=sys.stderr)
        sys.exit(5)
    if needed:
        print("TOOLS", flush=True)
        missing = preflight(args, needed)
        if missing:
            print(f"STOPPED: {' and '.join(missing)} cannot be run, and the lanes need it. Nothing was started.",
                  file=sys.stderr, flush=True)
            sys.exit(6)

    worst = 0
    if args.queue_rows is not None:
        write_run_queue(root, args)
    for label, cmd in prepare:
        done = subprocess.run(cmd)
        if done.returncode not in (0, 3):
            sys.exit(f"{label} failed with exit code {done.returncode}")
        worst = max(worst, done.returncode)
    if {"youtube", "captions"} & set(args.lanes):
        print("ESTIMATE", flush=True)
        for line in estimate_lines(root, args):
            print(line, flush=True)
    stop = layout(root).root / "sync" / ".stop"
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.unlink(missing_ok=True)
    watcher = subprocess.Popen(sync, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    threading.Thread(target=stream, args=("sync", watcher), daemon=True).start()
    try:
        worst = max(worst, run_lanes(parallel, after, beside, args.transcribe_every))
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
           5: "STOPPED: the store refused the upload",
           6: "STOPPED: a lane stopped on failures that point at the setup; see its lines above"}.get(
        worst, f"finished with exit code {worst}"))
    sys.exit(worst)


if __name__ == "__main__":
    main()
