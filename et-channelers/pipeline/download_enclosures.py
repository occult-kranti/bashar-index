#!/usr/bin/env python3
"""Download audio that its publisher offers as a file: podcast enclosures and creator-hosted files.

This is the lane that works from a cloud machine. A podcast enclosure or an MP3 on the maker's own
site is an ordinary download link: there is no bot check to meet and nothing here tries to get past
one. No cookies, no login, no proxy. Raw audio never goes into Git.

Two local steps per item, the same as download_audio.py:
  1. a plain HTTPS GET saves the file to a scratch folder (size-capped, with an overall time limit);
  2. ffmpeg re-encodes it to mono 16 kHz Opus (24 kbps by default) and the scratch file is deleted.

Reads the queue from select_episodes.py. For every item it writes
    <root>/audio/<channel_dir>/<item id>.opus
and appends one line to <root>/audio/audio_manifest.jsonl, the same manifest the YouTube lane uses,
so transcribe.py, verify.py and export_public.py work on both. Records carry lane ("pod" or "web"),
the source host, the SHA-256 of the file as published, and twin_of when the same recording is an
indexed YouTube video.

Safety rails (all on by default):
  * Without --limit or --all it only prints what it WOULD do and exits.
  * --root must be outside any Git checkout.
  * Each host has its own start-rate limit and concurrency cap. 403 / 429 answers are never retried;
    after --stop-after-blocks of them in a row from one host, that host is left alone for the rest of
    the run and the script exits with code 3 when the other hosts are done.
  * Only network-class errors are retried, with exponential backoff. Missing files (404 / 410) are
    recorded once and skipped on later runs (use --retry-failed to try again).

    python3 pipeline/download_enclosures.py --limit 5              # pilot
    python3 pipeline/download_enclosures.py --all --workers 4
Keep the output private: the recordings belong to their makers.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import hashlib
import http.client
import os
import platform
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ITEM_RE, HostGates, Progress, add_root_arg, append_jsonl, ensure_outside_git, host_of,  # noqa: E402
                    http_error_class, lane_of, latest_by_key, layout, parse_shard, probe_duration, read_csv,
                    read_jsonl, run_cmd, stable_shard, sha256_file, utc_now)
from download_audio import ffmpeg_cmd, first_line, tool_version  # noqa: E402
from feeds import FetchError, open_url  # noqa: E402

SKIP_LATER = {"unavailable", "not_audio", "too_large"}
HARD = {"rate_limited", "forbidden"}
TEXT_TYPES = ("text/html", "text/plain", "application/json", "application/xml", "text/xml")


class Problem(Exception):
    def __init__(self, klass, message, status=0):
        super().__init__(message)
        self.klass, self.status = klass, status


def save_stream(url, dest, args):
    """GET `url` into `dest`. Returns facts about the response; raises Problem on any failure."""
    deadline = time.monotonic() + args.timeout
    try:
        response = open_url(url, timeout=args.socket_timeout)
    except FetchError as err:
        raise Problem(http_error_class(err.status) if err.status else "network", str(err), err.status) from None
    digest, received = hashlib.sha256(), 0
    with response:
        ctype = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype in TEXT_TYPES:
            raise Problem("not_audio", f"server sent {ctype}, not a media file", response.status)
        declared = response.headers.get("Content-Length")
        declared = int(declared) if declared and declared.isdigit() else None
        if declared and declared > args.max_bytes:
            raise Problem("too_large", f"file is {declared} bytes, over the {args.max_bytes} byte cap", response.status)
        try:
            with open(dest, "wb") as handle:
                while True:
                    block = response.read(1 << 16)
                    if not block:
                        break
                    received += len(block)
                    if received > args.max_bytes:
                        raise Problem("too_large", f"more than {args.max_bytes} bytes received", response.status)
                    if time.monotonic() > deadline:
                        raise Problem("network", f"timed out after {args.timeout}s with {received} bytes", response.status)
                    digest.update(block)
                    handle.write(block)
        except (OSError, http.client.HTTPException) as err:
            raise Problem("network", f"{type(err).__name__}: {err}"[:300], response.status) from None
        if declared is not None and received != declared:
            raise Problem("network", f"connection closed early: {received} of {declared} bytes", response.status)
        if received < args.min_bytes:
            raise Problem("not_audio", f"only {received} bytes received", response.status)
        return {"http_status": response.status, "content_type": ctype, "final_host": host_of(response.geturl()),
                "source_bytes": received, "source_sha256": digest.hexdigest()}


def fetch_one(args, row, audio_root, gates, versions):
    """Download and encode one item. Returns the manifest record, or None if its host was already stopped."""
    ident, host = row["video_id"], host_of(row["url"])
    target = audio_root / row["channel_dir"]
    work = audio_root / ".work" / ident
    final = target / f"{ident}.opus"
    rec = {"video_id": ident, "channel_dir": row["channel_dir"], "lane": row.get("lane") or lane_of(ident),
           "started": utc_now(), "expected_duration_s": int(float(row["duration_s"])) if row.get("duration_s") else None,
           "source_host": host, "source_url": row["url"], "feed_key": row.get("feed_key", ""),
           "published": row.get("published", ""), "twin_of": row.get("twin_of", ""),
           "tool": versions["client"], "encoder": versions["ffmpeg"],
           "target": f"opus mono {args.sample_rate} Hz {args.bitrate} complexity {args.opus_complexity}"}
    try:
        for attempt in range(1, args.attempts + 1):
            if gates.blocked(host):
                return None  # not attempted, not recorded: the next run picks it up
            shutil.rmtree(work, ignore_errors=True)
            work.mkdir(parents=True, exist_ok=True)
            gates.wait(host)
            t0 = time.time()
            raw = work / "source.bin"
            try:
                try:
                    facts = save_stream(row["url"], raw, args)
                except Problem:
                    raise
                except Exception as err:  # noqa: BLE001 - never let one item end the run
                    raise Problem("other", f"{type(err).__name__}: {err}"[:300]) from None
            except Problem as err:
                rec.update(attempts=attempt, elapsed_s=round(time.time() - t0, 1), status="error",
                           http_status=err.status, error_class=err.klass, error_tail=str(err)[-300:])
                if err.klass in HARD:
                    gates.hard_block(host)
                    return rec  # never retry into a block
                if err.klass != "network" or attempt == args.attempts:
                    return rec
                time.sleep(min(60.0, args.backoff * 2 ** (attempt - 1)))
                continue
            gates.success(host)
            rec.update(attempts=attempt, **facts)
            target.mkdir(parents=True, exist_ok=True)
            part = target / f"{ident}.opus.part"
            code, _, err = run_cmd(ffmpeg_cmd(args, raw, part), args.timeout)
            rec["elapsed_s"] = round(time.time() - t0, 1)
            if code == 0 and part.exists() and part.stat().st_size > 0:
                os.replace(part, final)
                rec.update(status="ok", path=f"{row['channel_dir']}/{final.name}", bytes=final.stat().st_size,
                           sha256=sha256_file(final), duration_s=probe_duration(final, args.ffprobe),
                           error_class="", error_tail="")
                return rec
            part.unlink(missing_ok=True)
            rec.update(status="error", error_class="transcode", error_tail=first_line(err)[-300:])
            return rec  # a re-encode failure is not a network problem, so no retry
        return rec
    finally:
        shutil.rmtree(work, ignore_errors=True)
        if rec.get("status"):
            append_jsonl(audio_root / "audio_manifest.jsonl", rec)


def run_queue(todo, args, audio_root, gates, versions, progress):
    """Thread pool with a per-host cap applied when choosing the next task, so no worker waits on a busy
    host while another host has work. Returns the number of items attempted."""
    workers, cap = max(1, args.workers), max(1, args.per_host)
    pending = {}
    for idx, row in enumerate(todo):
        pending.setdefault(host_of(row["url"]), collections.deque()).append((idx, row))
    inflight, running, attempted = collections.Counter(), {}, 0
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        while True:
            while len(running) < workers:
                if shutil.disk_usage(audio_root).free < args.min_free_gb * 1e9:
                    args.disk_full = True      # finish what is in flight, start nothing new
                    break
                ready = [(q[0][0], host) for host, q in pending.items()
                         if q and inflight[host] < cap and not gates.blocked(host)]
                if not ready:
                    break
                _, host = min(ready)  # earliest queue position among hosts with a free slot
                _, row = pending[host].popleft()
                inflight[host] += 1
                running[pool.submit(fetch_one, args, row, audio_root, gates, versions)] = host
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--queue", type=Path, help="queue CSV (default <root>/jobs/queue_enclosures.csv)")
    ap.add_argument("--limit", type=int, default=0, help="process at most N items")
    ap.add_argument("--all", action="store_true", help="process the whole queue")
    ap.add_argument("--only", default="", help="comma-separated channel_dir values (person ids)")
    ap.add_argument("--shard", help="i/n: only items whose stable hash falls in shard i of n")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--per-host", type=int, default=2, help="max simultaneous downloads from one host")
    ap.add_argument("--min-interval", type=float, default=1.0, help="seconds between download starts on one host")
    ap.add_argument("--stop-after-blocks", type=int, default=3)
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--backoff", type=float, default=5.0)
    ap.add_argument("--timeout", type=int, default=1800, help="overall seconds allowed per item")
    ap.add_argument("--socket-timeout", type=int, default=60)
    ap.add_argument("--max-bytes", type=int, default=1_500_000_000, help="refuse source files larger than this")
    ap.add_argument("--min-bytes", type=int, default=2000, help="smaller responses are treated as an error page")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--min-free-gb", type=float, default=2.0,
                    help="stop starting new items when the data drive has less free space than this (exit code 4)")
    ap.add_argument("--ffmpeg", default="ffmpeg")
    ap.add_argument("--ffprobe", default="ffprobe")
    ap.add_argument("--sample-rate", type=int, default=16000)
    ap.add_argument("--bitrate", default="24k")
    ap.add_argument("--opus-complexity", type=int, default=5, choices=range(0, 11), metavar="0-10",
                    help="libopus encoder effort. Measured on a 10-minute file: 10 takes 13.1 CPU-seconds, "
                         "5 takes 4.3 and the file is 4.6%% larger (default 5)")
    args = ap.parse_args()

    root = ensure_outside_git(args.root)
    paths = layout(root)
    audio_root = paths.audio
    queue = [r for r in read_csv(args.queue or paths.jobs / "queue_enclosures.csv")
             if ITEM_RE.match(r.get("video_id") or "") and host_of(r.get("url") or "")]
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        queue = [r for r in queue if r["channel_dir"] in wanted]
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

    known = [int(float(r["duration_s"])) for r in todo if r.get("duration_s")]
    kbps = float("".join(c for c in args.bitrate if c.isdigit() or c == ".") or 24)
    hosts = collections.Counter(host_of(r["url"]) for r in todo)
    print(f"queue {len(queue)} | already done or skipped {len(queue) - len(todo)} | to do {len(todo)} from "
          f"{len(hosts)} host(s) | known length {sum(known) / 3600:.1f} h ({len(todo) - len(known)} unknown) | "
          f"disk about {sum(known) * kbps * 1000 / 8 / 1e9:.2f} GB at {args.bitrate}", file=sys.stderr)
    if not args.limit and not args.all:
        print("dry run: pass --limit N for a pilot or --all for everything", file=sys.stderr)
        return
    if args.limit:
        todo = todo[:args.limit]
    if not todo:
        return
    if not shutil.which(args.ffmpeg):
        sys.exit(f"{args.ffmpeg} not found. Install it first (see pipeline/README.md).")
    versions = {"client": f"python-urllib {platform.python_version()}", "ffmpeg": tool_version(args.ffmpeg, "-version")}

    gates = HostGates(args.min_interval, args.stop_after_blocks)
    args.disk_full = False
    audio_root.mkdir(parents=True, exist_ok=True)
    attempted = run_queue(todo, args, audio_root, gates, versions, Progress(len(todo), "enclosures"))
    print(f"attempted {attempted} of {len(todo)}; manifest {audio_root / 'audio_manifest.jsonl'}", file=sys.stderr)
    if args.disk_full:
        print(f"STOPPED: less than {args.min_free_gb} GB free on the data drive. Move finished audio off this "
              "machine (see sync_archive.py) or pass a lower --min-free-gb, then rerun: finished items are skipped.",
              file=sys.stderr)
        sys.exit(4)
    if gates.blocked_hosts():
        print("STOPPED for these hosts after repeated 403 / 429 answers: " + ", ".join(gates.blocked_hosts())
              + ". Wait, then rerun: finished items are skipped.", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
