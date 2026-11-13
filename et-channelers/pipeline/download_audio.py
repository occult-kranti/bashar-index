#!/usr/bin/env python3
"""Parallel, resumable, polite audio download. Raw audio never goes into Git.

Two local steps per video:
  1. yt-dlp downloads a small audio stream into a scratch folder (no cookies, no login, no proxy);
  2. ffmpeg re-encodes it to mono 16 kHz Opus (24 kbps by default): speech-sized, and the sample
     rate Whisper works at. The scratch file is then deleted.
ffmpeg does the encode, not yt-dlp's -x option, because yt-dlp copies the stream unchanged when the
source is already Opus, which would silently ignore the bitrate and channel settings.

Reads the queue from select_jobs.py. For every video it writes
    <root>/audio/<channel_dir>/<video_id>.opus
and appends one line to <root>/audio/audio_manifest.jsonl (status, bytes, duration, sha256, error class).

Safety rails (all on by default):
  * Without --limit or --all it only prints what it WOULD do (items, hours, disk) and exits.
  * --root must be outside any Git checkout.
  * A global start-rate limit, a per-channel concurrency cap, no cookies, no proxies, no login.
  * 403 / 429 / "confirm you are not a bot" responses are never retried; after --stop-after-blocks
    of them in a row the run stops (exit code 3) so you can wait or slow down. Nothing here tries to
    get around a bot check.
  * Only network-class errors are retried, with exponential backoff. Removed, private and age or
    members-only videos are recorded once and skipped on later runs (use --retry-failed to try again).

    python3 pipeline/download_audio.py --limit 10                 # pilot
    python3 pipeline/download_audio.py --all --workers 4 --shard 0/2
Respect YouTube's terms of service and the rights holders' rights; keep the output private.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (HARD_BLOCKS, Breaker, Progress, RateLimiter, add_root_arg, append_jsonl,  # noqa: E402
                    classify_error, ensure_outside_git, latest_by_key, layout, parse_shard, probe_duration,
                    read_csv, read_jsonl, run_cmd, sha256_file, stable_shard, utc_now)

SKIP_LATER = {"unavailable", "login_required"}
SYSTEMIC = {"other", "no_formats", "transcode"}  # failures that say something is wrong with the setup
SCRATCH_SUFFIXES = (".part", ".ytdl", ".temp", ".tmp")


def ytdlp_cmd(args, row, work):
    cmd = [args.ytdlp, "--ignore-config", "--no-playlist", "--no-warnings", "--no-progress",
           "-f", args.format, "--retries", "2", "--fragment-retries", "2", "--socket-timeout", "30",
           "--sleep-requests", str(getattr(args, "sleep_requests", 0.75)),
           "-o", str(work / "%(id)s.%(ext)s")]
    if args.limit_rate:
        cmd += ["--limit-rate", args.limit_rate]
    return cmd + [row["url"]]


def ffmpeg_cmd(args, src, dst):
    cmd = [args.ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
           "-vn", "-map", "0:a:0", "-ac", "1", "-ar", str(args.sample_rate),
           "-c:a", "libopus", "-b:a", args.bitrate]
    effort = getattr(args, "opus_complexity", None)
    if effort is not None:  # libopus default is 10; 5 costs a third of the CPU for about 5% more bytes
        cmd += ["-compression_level", str(effort)]
    return cmd + ["-f", "opus", str(dst)]


def find_raw(work, video_id):
    found = [p for p in work.glob(f"{video_id}.*") if p.suffix.lower() not in SCRATCH_SUFFIXES]
    return max(found, key=lambda p: p.stat().st_size) if found else None


def first_line(text):
    return (text or "").strip().splitlines()[0] if (text or "").strip() else ""


def fetch_one(args, row, audio_root, limiter, breaker, versions):
    """Download and encode one video. Returns the manifest record, or None if the run was stopped first."""
    video_id = row["video_id"]
    target = audio_root / row["channel_dir"]
    work = audio_root / ".work" / video_id
    final = target / f"{video_id}.opus"
    rec = {"video_id": video_id, "channel_dir": row["channel_dir"], "started": utc_now(),
           "expected_duration_s": int(row["duration_s"]) if row.get("duration_s") else None,
           "tool": f"yt-dlp {versions['ytdlp']}", "encoder": versions["ffmpeg"],
           "target": f"opus mono {args.sample_rate} Hz {args.bitrate}"}
    try:
        for attempt in range(1, args.attempts + 1):
            if breaker.tripped.is_set():
                return None  # not attempted, not recorded: the next run picks it up
            shutil.rmtree(work, ignore_errors=True)
            work.mkdir(parents=True, exist_ok=True)
            limiter.wait()
            t0 = time.time()
            code, _, err = run_cmd(ytdlp_cmd(args, row, work), args.timeout)
            raw = find_raw(work, video_id) if code == 0 else None
            rec.update(attempts=attempt, elapsed_s=round(time.time() - t0, 1))
            if raw is not None:
                target.mkdir(parents=True, exist_ok=True)
                part = target / f"{video_id}.opus.part"
                code2, _, err2 = run_cmd(ffmpeg_cmd(args, raw, part), args.timeout)
                if code2 == 0 and part.exists() and part.stat().st_size > 0:
                    os.replace(part, final)
                    rec.update(status="ok", path=f"{row['channel_dir']}/{final.name}", bytes=final.stat().st_size,
                               sha256=sha256_file(final), duration_s=probe_duration(final, args.ffprobe),
                               source_ext=raw.suffix, source_bytes=raw.stat().st_size, error_class="", error_tail="")
                    breaker.success()
                    if getattr(args, "systemic", None) is not None:
                        args.systemic.success()
                    return rec
                part.unlink(missing_ok=True)
                rec.update(status="error", error_class="transcode", error_tail=first_line(err2)[-300:])
                return rec  # a re-encode failure is not a network problem, so no retry
            klass = classify_error(err if code else "download finished but no audio file was produced")
            rec.update(status="error", error_class=klass, error_tail=(err or "").strip()[-300:])
            if klass in HARD_BLOCKS:
                breaker.hard_block()
                return rec  # never retry into a block
            if klass in SYSTEMIC and getattr(args, "systemic", None) is not None:
                args.systemic.hard_block()  # a run of these means the tool is broken, not the videos
            if klass != "network" or attempt == args.attempts:
                return rec
            time.sleep(min(60.0, args.backoff * 2 ** (attempt - 1)))
        return rec
    finally:
        shutil.rmtree(work, ignore_errors=True)
        if rec.get("status"):
            append_jsonl(audio_root / "audio_manifest.jsonl", rec)


def stopped(args):
    systemic = getattr(args, "systemic", None)
    return systemic is not None and systemic.tripped.is_set()


def run_queue(todo, args, audio_root, limiter, breaker, versions, progress):
    """Run the queue on a thread pool. The channel cap is applied when choosing the next task, so a
    worker thread never sits idle waiting on a busy channel. Returns the number of videos attempted."""
    workers, cap = max(1, args.workers), max(1, args.per_channel)
    pending = {}
    for idx, row in enumerate(todo):
        pending.setdefault(row["channel_dir"], collections.deque()).append((idx, row))
    inflight, running, attempted = collections.Counter(), {}, 0
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        while True:
            while len(running) < workers and not breaker.tripped.is_set() and not stopped(args):
                ready = [(q[0][0], chan) for chan, q in pending.items() if q and inflight[chan] < cap]
                if not ready:
                    break
                _, chan = min(ready)  # earliest queue position among channels with a free slot
                _, row = pending[chan].popleft()
                inflight[chan] += 1
                running[pool.submit(fetch_one, args, row, audio_root, limiter, breaker, versions)] = chan
            if not running:
                break
            done, _ = cf.wait(list(running), return_when=cf.FIRST_COMPLETED)
            for fut in done:
                inflight[running.pop(fut)] -= 1
                rec = fut.result()
                if rec is not None:
                    attempted += 1
                    progress.tick(rec["status"] == "ok")
    return attempted


def tool_version(cmd, flag):
    code, out, _ = run_cmd([cmd, flag], 30)
    return first_line(out)[:80] if code == 0 else "unknown"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--queue", type=Path, help="queue CSV (default <root>/jobs/queue.csv)")
    ap.add_argument("--limit", type=int, default=0, help="process at most N videos")
    ap.add_argument("--all", action="store_true", help="process the whole queue")
    ap.add_argument("--shard", help="i/n: only videos whose stable hash falls in shard i of n")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--per-channel", type=int, default=2, help="max simultaneous downloads per channel")
    ap.add_argument("--min-interval", type=float, default=10.0,
                    help="seconds between download starts, all workers (default 10: yt-dlp's own advice is one "
                         "video every 10 to 20 seconds to stay under YouTube's session limit)")
    ap.add_argument("--sleep-requests", type=float, default=0.75,
                    help="seconds yt-dlp waits between its own requests for one video")
    ap.add_argument("--limit-rate", default="", help="yt-dlp bandwidth cap per download, e.g. 2M")
    ap.add_argument("--stop-after-blocks", type=int, default=3)
    ap.add_argument("--stop-after-failures", type=int, default=8,
                    help="stop (exit code 6) after this many setup-type failures in a row: no formats, "
                         "encoder errors, unrecognised errors. 0 = never")
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--backoff", type=float, default=5.0)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--ytdlp", default="yt-dlp")
    ap.add_argument("--ffmpeg", default="ffmpeg")
    ap.add_argument("--ffprobe", default="ffprobe")
    ap.add_argument("--format", default="bestaudio[abr<=96]/bestaudio/best")
    ap.add_argument("--sample-rate", type=int, default=16000)
    ap.add_argument("--bitrate", default="24k")
    args = ap.parse_args()

    root = ensure_outside_git(args.root)
    paths = layout(root)
    audio_root = paths.audio
    queue = [r for r in read_csv(args.queue or paths.jobs / "queue.csv") if r.get("video_id")]
    i, n = parse_shard(args.shard)
    queue = [r for r in queue if stable_shard(r["video_id"], n) == i]
    done = latest_by_key(read_jsonl(audio_root / "audio_manifest.jsonl"))
    todo = []
    for r in queue:
        prev = done.get(r["video_id"])
        if prev and prev["status"] == "ok":
            f = audio_root / prev["path"]
            if f.exists() and f.stat().st_size == prev["bytes"]:
                continue
        elif prev and prev.get("error_class") in SKIP_LATER and not args.retry_failed:
            continue
        todo.append(r)

    known = [int(r["duration_s"]) for r in todo if r.get("duration_s")]
    kbps = float("".join(c for c in args.bitrate if c.isdigit() or c == ".") or 24)
    print(f"queue {len(queue)} | already done or skipped {len(queue) - len(todo)} | to do {len(todo)} | "
          f"known length {sum(known) / 3600:.1f} h ({len(todo) - len(known)} unknown) | "
          f"disk about {sum(known) * kbps * 1000 / 8 / 1e9:.2f} GB at {args.bitrate}", file=sys.stderr)
    if not args.limit and not args.all:
        print("dry run: pass --limit N for a pilot or --all for everything", file=sys.stderr)
        return
    if args.limit:
        todo = todo[:args.limit]
    if not todo:
        return
    for tool in (args.ytdlp, args.ffmpeg):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found. Install it first (see pipeline/README.md).")
    versions = {"ytdlp": tool_version(args.ytdlp, "--version"), "ffmpeg": tool_version(args.ffmpeg, "-version")}

    limiter, breaker = RateLimiter(args.min_interval), Breaker(args.stop_after_blocks)
    args.systemic = Breaker(args.stop_after_failures) if args.stop_after_failures else None
    attempted = run_queue(todo, args, audio_root, limiter, breaker, versions, Progress(len(todo), "audio"))
    print(f"attempted {attempted} of {len(todo)}; manifest {audio_root / 'audio_manifest.jsonl'}", file=sys.stderr)
    if stopped(args) and not breaker.tripped.is_set():
        print(f"STOPPED: {args.stop_after_failures} failures in a row that point at the setup, not at the videos "
              "(no usable formats, encoder errors or unrecognised errors). Run pipeline/doctor.py, update yt-dlp, "
              "read the last lines of audio_manifest.jsonl, then rerun: these videos will be tried again.",
              file=sys.stderr)
        sys.exit(6)
    if breaker.tripped.is_set():
        print("STOPPED: repeated 403 / 429 / bot-check responses. Wait, use fewer --workers or a larger "
              "--min-interval, then rerun: finished items are skipped.", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
