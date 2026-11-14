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
  * Each host has its own start-rate limit, and so does every host a redirect leads to (a podcast enclosure
    usually starts at a tracking redirector; archive.org sends each file from one of its storage nodes); the
    cap on simultaneous downloads (--per-host) counts the first host of each address. 403 / 429 answers are
    never retried, and a Retry-After is obeyed, with a 403 / 429 or a 503; after --stop-after-blocks refusals
    in a row from one host, that host is left alone for the rest of the run, and no redirect is followed to it.
    Any 403 / 429 makes the script exit with code 3 when the other hosts are done, and a host that keeps
    refusing is not asked again on later runs until its wait is over (a day at least; common.resting_hosts).
  * One run at a time: a second one waits for the first (a lock in <root>/jobs/), then reads what is left.
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
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ITEM_RE, HostGates, Progress, add_root_arg, append_jsonl, archived_ids, ensure_outside_git,  # noqa: E402
                    downloader_lock, host_of, http_error_class, lane_of, latest_by_key, layout, parse_shard, probe_duration,
                    read_csv, read_jsonl, resting_hosts, run_cmd, say_refused, say_resting, stable_shard, sha256_file,
                    utc_now)
from download_audio import ffmpeg_cmd, first_line, tool_version  # noqa: E402
from feeds import FetchError, open_url  # noqa: E402

SKIP_LATER = {"unavailable", "not_audio", "too_large"}
HARD = {"rate_limited", "forbidden"}
TEXT_TYPES = ("text/html", "text/plain", "application/json", "application/xml", "text/xml")
SAME_HOST_ITEMS = 3      # a group's last answers for this many different items all came from one host: its host


class Problem(Exception):
    def __init__(self, klass, message, status=0, final_host="", retry_after=None):
        super().__init__(message)
        self.klass, self.status, self.final_host, self.retry_after = klass, status, final_host, retry_after


class MediaHosts:
    """Which host answers for an item, learned from the answers: per item, and per feed. Behind a redirector a
    feed usually lives on one media host, but Podbean sends a show's episodes from dozens of nodes, so a feed is
    taken to live on one host only when its answers for the last SAME_HOST_ITEMS different items all came from
    it. Files without a feed have no group (pass ''): archive.org sends them from about a hundred storage nodes
    and keeps the files of one item together on one node, so a run of files from one node says nothing about
    the next item."""

    def __init__(self, items=SAME_HOST_ITEMS):
        self._items, self._group, self._item, self._lock = items, {}, {}, threading.Lock()

    def note(self, group, item, host):
        if not host:
            return
        with self._lock:
            if item:
                self._item[item] = host
            answers = self._group.setdefault(group, collections.OrderedDict())
            answers.pop(item, None)                      # an item counts once, with its latest answer
            answers[item] = host
            while len(answers) > self._items:
                answers.popitem(last=False)

    def likely(self, group, item):
        """The host expected to answer for this item: the one that answered for it last, or the one host its
        group lives on, or ''."""
        with self._lock:
            if self._item.get(item):
                return self._item[item]
            hosts = list(self._group.get(group, {}).values())
        return hosts[0] if group and len(hosts) == self._items and len(set(hosts)) == 1 else ""

    def stopped_by(self, group, item, stopped):
        """The host that holds this item back (`stopped` says it is being left alone), or ''."""
        host = self.likely(group, item)
        return host if host and stopped(host) else ""


class Hops:
    """Called before each redirect is followed (feeds.open_url's before_redirect): every host along the way
    gets its own turn and its own Retry-After, and a host that is being left alone (it refused, or stopped
    answering) is not asked at all, whichever first hop leads to it. `last` is the last host led to."""

    def __init__(self, first, gates, stopped):
        self.first, self.gates, self.stopped, self.last, self.passed = first, gates, stopped, "", []

    def __call__(self, url):
        host = host_of(url)
        if host and host != self.first:
            if self.stopped(host):
                raise FetchError(0, f"redirect not followed: {host} is being left alone (it refused or stopped "
                                    "answering)", url, klass="held")
            self.gates.wait(host)
            if self.stopped(host):
                raise FetchError(0, f"redirect not followed: {host} refused while this request waited for its turn",
                                 url, klass="held")
        self.last = host or self.last
        if host and host != self.first and host not in self.passed:
            self.passed.append(host)


def save_stream(url, dest, args, hops=None):
    """GET `url` into `dest`. Returns facts about the response; raises Problem on any failure."""
    deadline = time.monotonic() + args.timeout
    try:
        response = open_url(url, timeout=args.socket_timeout, before_redirect=hops)
    except FetchError as err:
        answered = host_of(err.final_url or "")
        if not err.status and err.klass is None and hops is not None and hops.last:
            answered = hops.last          # the connection failed after a redirect: at the host it led to
        raise Problem(err.klass or (http_error_class(err.status) if err.status else "network"), str(err), err.status,
                      answered, err.retry_after) from None
    digest, received = hashlib.sha256(), 0
    answered_by = host_of(response.geturl())
    with response:
        ctype = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype in TEXT_TYPES:
            raise Problem("not_audio", f"server sent {ctype}, not a media file", response.status, answered_by)
        declared = response.headers.get("Content-Length")
        declared = int(declared) if declared and declared.isdigit() else None
        if declared and declared > args.max_bytes:
            raise Problem("too_large", f"file is {declared} bytes, over the {args.max_bytes} byte cap", response.status, answered_by)
        try:
            with open(dest, "wb") as handle:
                while True:
                    block = response.read(1 << 16)
                    if not block:
                        break
                    received += len(block)
                    if received > args.max_bytes:
                        raise Problem("too_large", f"more than {args.max_bytes} bytes received", response.status, answered_by)
                    if time.monotonic() > deadline:
                        raise Problem("network", f"timed out after {args.timeout}s with {received} bytes", response.status, answered_by)
                    digest.update(block)
                    handle.write(block)
        except (OSError, http.client.HTTPException) as err:
            raise Problem("network", f"{type(err).__name__}: {err}"[:300], response.status, answered_by) from None
        if declared is not None and received != declared:
            raise Problem("network", f"connection closed early: {received} of {declared} bytes", response.status, answered_by)
        if received < args.min_bytes:
            raise Problem("not_audio", f"only {received} bytes received", response.status, answered_by)
        return {"http_status": response.status, "content_type": ctype, "final_host": host_of(response.geturl()),
                "source_bytes": received, "source_sha256": digest.hexdigest()}


def fetch_one(args, row, audio_root, gates, versions):
    """Download and encode one item. Returns the manifest record, or None if it was not asked for: its host was
    already stopped, or the host it leads to is being left alone."""
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
        # An enclosure address usually starts at a tracking redirector and ends at the show's media host.
        # Refusals are charged to the host that refused, so one show's refusing host does not stop the other
        # shows behind the same first hop, and no redirect is followed to a host that is being left alone
        # (Hops). A feed that is known to live on one host that is being left alone is not even started
        # (MediaHosts), so its first hop is not asked for every episode either. Files without a feed have no
        # group: each is held back only by the host that last answered for it.
        group = row.get("feed_key") or ""
        stopped = lambda h: gates.blocked(h) or h in args.resting  # noqa: E731
        for attempt in range(1, args.attempts + 1):
            if gates.blocked(host) or args.media.stopped_by(group, ident, stopped):
                return None  # not attempted, not recorded: the next run picks it up
            shutil.rmtree(work, ignore_errors=True)
            work.mkdir(parents=True, exist_ok=True)
            gates.wait(host)
            if gates.blocked(host) or args.media.stopped_by(group, ident, stopped):
                return None  # it refused while this request waited for its turn: not sent, not recorded
            rec["started"] = utc_now()      # when the request goes out, after its turn came
            t0 = time.time()
            raw = work / "source.bin"
            try:
                try:
                    hops = Hops(host, gates, stopped)
                    facts = save_stream(row["url"], raw, args, hops)
                except Problem:
                    raise
                except Exception as err:  # noqa: BLE001 - never let one item end the run
                    raise Problem("other", f"{type(err).__name__}: {err}"[:300]) from None
            except Problem as err:
                args.media.note(group, ident, err.final_host)
                if err.klass == "held":
                    return None  # the host it leads to is being left alone: nothing was asked of it, nothing recorded
                refuser = err.final_host or host
                rec.update(attempts=attempt, elapsed_s=round(time.time() - t0, 1), status="error",
                           http_status=err.status, error_class=err.klass, error_tail=str(err)[-300:],
                           final_host=refuser)
                if err.retry_after is not None:
                    rec["retry_after_s"] = err.retry_after
                if err.klass in HARD:
                    gates.hard_block(refuser, err.retry_after)
                    return rec  # never retry into a block
                if err.klass == "network":
                    gates.failure(refuser)
                    gates.unavailable(refuser, err.retry_after)    # a 503 that says how long to wait: obeyed
                if err.klass != "network" or attempt == args.attempts or gates.blocked(refuser):
                    return rec
                time.sleep(max(min(60.0, args.backoff * 2 ** (attempt - 1)), float(err.retry_after or 0)))
                continue
            args.media.note(group, ident, facts["final_host"] or host)
            for passed in dict.fromkeys([facts["final_host"] or host, host, *hops.passed]):
                gates.success(passed)          # every host along the way answered as asked
            via = [h for h in hops.passed if h != facts["final_host"]]
            if via:
                rec["via_hosts"] = via
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
    ap.add_argument("--stop-after-failures", type=int, default=6,
                    help="leave a host alone for the rest of the run after this many errors or timeouts in a row "
                         "from it (0 = never)")
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--backoff", type=float, default=5.0)
    ap.add_argument("--timeout", type=int, default=1800, help="overall seconds allowed per item")
    ap.add_argument("--socket-timeout", type=int, default=60)
    ap.add_argument("--max-bytes", type=int, default=1_500_000_000, help="refuse source files larger than this")
    ap.add_argument("--min-bytes", type=int, default=2000, help="smaller responses are treated as an error page")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--ask-resting", action="store_true",
                    help="ask hosts that refused on an earlier run again, before their wait is over")
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
    # One downloader at a time, whoever starts it (the collection loop, a cycle, an archive.org run started by
    # hand): a second one waits here and reads what is left to do only when the first has finished. Two at
    # once fetched the same items side by side, shared their scratch folders and doubled the per-host cap.
    locks = downloader_lock(paths.jobs, __file__, args.shard) if args.limit or args.all else []  # noqa: F841
    queue = [r for r in read_csv(args.queue or paths.jobs / "queue_enclosures.csv")
             if ITEM_RE.match(r.get("video_id") or "") and host_of(r.get("url") or "")]
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        queue = [r for r in queue if r["channel_dir"] in wanted]
    i, n = parse_shard(args.shard)
    queue = [r for r in queue if stable_shard(r["video_id"], n) == i]
    records = read_jsonl(audio_root / "audio_manifest.jsonl")
    done = latest_by_key(records)
    stored = archived_ids(root, "audio")   # uploaded, checked and then deleted here: finished, not missing
    todo = []
    for r in queue:
        prev = done.get(r["video_id"])
        if prev and prev["status"] == "ok":
            f = audio_root / prev["path"]
            if r["video_id"] in stored or (f.exists() and f.stat().st_size == prev["bytes"]):
                continue
        elif prev and prev.get("error_class") in SKIP_LATER and not args.retry_failed:
            continue
        todo.append(r)
    # A host that refused on an earlier run is not asked again before its wait is over: not the first host of an
    # item's address, not the host known to answer for it (MediaHosts), and no redirect leads to it (Hops).
    # A success counts for the first hop as well as for the host that served the file: archive.org redirects
    # every download to one of its storage nodes, so its own host never serves a file itself, and one refusal
    # must not leave all of it alone as though it had served nothing.
    credited = []
    for rec in records:
        credited.append(rec)
        if rec.get("status") == "ok" and rec.get("final_host"):
            for passed in dict.fromkeys([rec.get("source_host"), *(rec.get("via_hosts") or [])]):
                if passed and passed != rec["final_host"]:
                    credited.append({**rec, "final_host": passed})
    resting = {} if args.ask_resting else resting_hosts(credited, lambda r: r.get("final_host") or r.get("source_host") or "")
    media = MediaHosts()
    for rec in records:
        media.note(rec.get("feed_key") or "", rec.get("video_id") or "", rec.get("final_host") or "")

    def resting_host(row):
        first = host_of(row["url"])
        return first if first in resting else media.stopped_by(row.get("feed_key") or "", row["video_id"], resting.__contains__)
    waiting = collections.Counter(resting_host(r) for r in todo)
    waiting.pop("", None)
    say_resting(resting, waiting, "file(s)")
    todo = [r for r in todo if not resting_host(r)]

    def tried_before(r):
        prev = done.get(r["video_id"])
        return bool(prev) and prev.get("status") == "error"
    todo.sort(key=tried_before)     # stable: new items keep their order and come first

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

    gates = HostGates(args.min_interval, args.stop_after_blocks, args.stop_after_failures)
    args.media, args.resting = media, resting
    args.disk_full = False
    audio_root.mkdir(parents=True, exist_ok=True)
    attempted = run_queue(todo, args, audio_root, gates, versions, Progress(len(todo), "enclosures"))
    print(f"attempted {attempted} of {len(todo)}; manifest {audio_root / 'audio_manifest.jsonl'}", file=sys.stderr)
    refused, down = say_refused(gates), gates.down_hosts()     # any 403 / 429, not only a tripped breaker
    if down:
        print("STOPPED for these hosts, which were not answering (errors or timeouts): " + ", ".join(down)
              + ". Try again later: finished items are skipped.", file=sys.stderr)
    if refused or down:
        sys.exit(3)
    if args.disk_full:
        print(f"STOPPED: less than {args.min_free_gb} GB free on the data drive. Move finished audio off this "
              "machine (see sync_archive.py) or pass a lower --min-free-gb, then rerun: finished items are skipped.",
              file=sys.stderr)
        sys.exit(4)

if __name__ == "__main__":
    main()
