#!/usr/bin/env python3
"""Shared helpers for the ET-channelers batch pipeline. Standard library only.

Design rules that every script in this folder follows:
  * Raw media, captions and transcripts live OUTSIDE any Git checkout (see ensure_outside_git).
  * Every step appends one JSON line per item to a manifest, so a rerun skips finished work.
  * Items are split across workers by a stable hash, so shards never overlap.
  * A run stops early on 403/429/bot-check responses instead of retrying into them.
"""
from __future__ import annotations

import calendar
import collections
import csv
import datetime
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

ET_ROOT = Path(__file__).resolve().parents[1]  # the et-channelers/ folder
ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")  # a YouTube video id
# Items that do not come from YouTube get "<lane>-<16 hex>": pod = podcast enclosure, web = file hosted
# by the creator, ia = Internet Archive. The manifests keep the field name "video_id" for every lane.
LANES = ("pod", "web", "ia")
LANE_ID_RE = re.compile(r"^(?:%s)-[0-9a-f]{16}$" % "|".join(LANES))
ITEM_RE = re.compile(r"^(?:[A-Za-z0-9_-]{11}|(?:%s)-[0-9a-f]{16})$" % "|".join(LANES))
AUDIO_EXT = (".opus", ".m4a", ".mp3", ".wav", ".flac", ".webm", ".ogg")
HARD_BLOCKS = {"bot_check", "rate_limited", "forbidden"}


# ---------------------------------------------------------------- small utilities
def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def parse_duration(text):
    """'1:02:03' -> 3723, '15:38' -> 938, '45' -> 45, '' / junk -> None."""
    if text is None or text == "":
        return None
    try:
        parts = [int(p) for p in str(text).strip().split(":")]
    except ValueError:
        return None
    if not 1 <= len(parts) <= 3 or any(p < 0 for p in parts):
        return None
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds


def slug(text, default="x") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(text or "")).strip("-._")
    return cleaned[:60] or default


def sha256_file(path, chunk=1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalise_text(text: str) -> str:
    """Lower-case, whitespace-collapsed text, used only for hashing and duplicate checks."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def stable_shard(key: str, n: int) -> int:
    return int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16) % max(1, n)


def item_id(lane: str, *key_parts) -> str:
    """Stable id for a non-YouTube item, e.g. item_id("pod", feed_url, guid) -> 'pod-0123456789abcdef'."""
    if lane not in LANES:
        raise ValueError(f"unknown lane {lane!r}")
    joined = "\n".join(str(part).strip() for part in key_parts)
    return f"{lane}-{hashlib.sha256(joined.encode('utf-8')).hexdigest()[:16]}"


def host_id(channel: str) -> str:
    """The id of an interview show or re-upload channel, from the name the lists use for it:
    'Next Level Soul Podcast' -> 'host:next-level-soul-podcast'. A note in brackets is not part of the name."""
    return "host:" + slug(str(channel or "").split("(")[0].strip(), "channel").lower()


def lane_of(item: str) -> str:
    """'youtube' for an 11-character id, otherwise the lane prefix ('pod', 'web', 'ia')."""
    return item.split("-", 1)[0] if LANE_ID_RE.match(item or "") else "youtube"


def parse_shard(text):
    """'2/8' -> (2, 8). None -> (0, 1). Shards are 0-based, so 8 shards are 0/8 .. 7/8."""
    if not text:
        return 0, 1
    try:
        i, n = (int(x) for x in str(text).split("/"))
    except ValueError:
        raise SystemExit(f"--shard must look like 2/8, got {text!r}")
    if n < 1 or not 0 <= i < n:
        raise SystemExit(f"--shard {text}: need 0 <= i < n")
    return i, n


def lpt_assign(items, n, weight):
    """Longest-processing-time-first: split items into n bins with balanced total weight."""
    bins, loads = [[] for _ in range(n)], [0.0] * n
    for item in sorted(items, key=weight, reverse=True):
        k = loads.index(min(loads))
        bins[k].append(item)
        loads[k] += weight(item)
    return bins


# ---------------------------------------------------------------- paths
def default_root() -> Path:
    return Path(os.environ.get("ET_PRIVATE_DIR") or (Path.home() / "et-channelers-private"))


def layout(root) -> SimpleNamespace:
    root = Path(root)
    return SimpleNamespace(
        root=root,
        jobs=root / "jobs",
        discover=root / "discover",
        audio=root / "audio",
        captions=root / "captions",
        transcripts=root / "transcripts",
        qa=root / "qa",
        public=root / "public_export",
        sources=root / "sources",          # feed lookups and review tables
        feeds=root / "feeds",              # parsed episode lists, one file per feed
        pubtext=root / "transcripts_publisher",  # transcripts the publisher wrote (not speech-to-text)
    )


def add_root_arg(parser):
    parser.add_argument("--root", type=Path, default=default_root(),
                        help="private data folder, must be outside any Git checkout "
                             "(default: $ET_PRIVATE_DIR or ~/et-channelers-private)")


def _inside_git(resolved: Path):
    for parent in (resolved, *resolved.parents):
        if (parent / ".git").exists():
            return parent
    return None


def ensure_outside_git(path) -> Path:
    """The resolved folder, or exit if it, or any linked sub-folder directly inside it, is in a Git
    checkout. The second check matters: <root>/audio linked into a repository would otherwise let every
    lane write recordings into that repository while --root itself looks fine."""
    resolved = Path(path).expanduser().resolve()
    where = _inside_git(resolved)
    if where is None and resolved.is_dir():
        for child in resolved.iterdir():
            if child.is_symlink():
                where = _inside_git(child.resolve())
                if where is not None:
                    resolved = child
                    break
    if where is not None:
        raise SystemExit(
            f"refusing to use {resolved}: it is inside a Git checkout ({where}). "
            "Raw audio, captions and transcripts must stay out of the repository; "
            "pass --root with a folder elsewhere.")
    return Path(path).expanduser().resolve()


# ---------------------------------------------------------------- files
def atomic_write_text(path, text: str):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    with open(tmp, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


_APPEND_LOCK = threading.Lock()
_WARNED = set()


def append_jsonl(path, obj):
    """Append one record as one line. If a crash left the file ending in half a line, the new record
    starts on a fresh line, so the fragment stays a fragment and the record after it is not swallowed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    with _APPEND_LOCK:
        torn = False
        try:
            with open(path, "rb") as check:
                check.seek(-1, os.SEEK_END)
                torn = check.read(1) != b"\n"
        except OSError:
            pass                       # no file yet, or an empty one
        with open(path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(("\n" if torn else "") + line)


def read_jsonl(path):
    """All records in a JSONL file. A line that is not a whole record is what an interrupted write
    leaves behind: it is skipped, wherever it sits, and reported once on stderr so it is not silent.
    (Every line holds one complete record or none, so a skipped fragment loses at most the one item
    whose write was interrupted, and that item is simply done again.)"""
    path = Path(path)
    if not path.exists():
        return []
    records, bad = [], []
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            bad.append(n)
            continue
        if isinstance(record, dict):
            records.append(record)
        else:
            bad.append(n)
    if bad and str(path) not in _WARNED:
        _WARNED.add(str(path))
        print(f"note: {path.name} has {len(bad)} unreadable line(s) (first at line {bad[0]}), left by an "
              "interrupted write; skipped", file=sys.stderr)
    return records


def listed_videos(root):
    """Every row of the channel listings discover.py wrote. One file per channel, each written whole, so
    this is safe to read while a listing run is still going (videos_all.jsonl is rebuilt only at its end)."""
    folder = layout(root).discover / "channels"
    rows = []
    for listing in sorted(folder.glob("*.jsonl")) if folder.exists() else []:
        rows += read_jsonl(listing)
    return rows


def archived_ids(root, kind) -> set:
    """Ids whose `kind` ("audio", "asr", "pubtext", "captions") has a checked copy in a store, according
    to the ledger sync_archive.py keeps. Such an item is finished even when its local file was deleted
    to free the disk, so no step fetches or makes it again."""
    stored = {}
    for rec in read_jsonl(Path(root) / "sync" / "sync_manifest.jsonl"):
        if rec.get("kind") != kind:
            continue
        key = (rec.get("video_id"), rec.get("store"))
        if rec.get("withdrawn"):
            stored.pop(key, None)
        elif rec.get("verified"):
            stored[key] = True
    return {video_id for video_id, _ in stored}


def latest_by_key(records, key="video_id"):
    out = {}
    for record in records:
        out[record[key]] = record
    return out


# ---------------------------------------------------------------- local files another process still needs
def holds_dir(root) -> Path:
    return Path(root) / "sync" / "holds"


def pid_alive(pid) -> bool:
    """True if a process with this id is running. On Windows it is not checked and taken as running."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if os.name == "nt":                 # os.kill(pid, 0) would send Ctrl-C there
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:             # somebody else's process: it is running
        return True
    except OSError:
        return False
    return True


def hold_items(root, who, ids) -> Path:
    """Ask sync_archive.py to keep the local audio of these items while this process runs. transcribe.py
    names every file it has queued, so the sync does not remove a stored copy under it. The note is a small
    file in <root>/sync/holds/ that lapses by itself when the process is gone; delete it when done."""
    path = holds_dir(root) / f"{who}-{os.getpid()}.json"
    atomic_write_text(path, json.dumps({"who": who, "pid": os.getpid(), "since": utc_now(),
                                        "video_ids": sorted(set(ids))}))
    return path


def held_items(root) -> set:
    """Ids whose local audio a running process asked to keep (hold_items). A note left by a process that
    has ended counts for nothing."""
    out, folder = set(), holds_dir(root)
    for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            note = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(note, dict) and pid_alive(note.get("pid")):
            out.update(str(v) for v in note.get("video_ids") or [])
    return out


def file_lock(path, what, shared=False):
    """Hold a lock on `path` until this process ends (keep the returned file open). A process that asks for
    a lock someone else holds waits until it is free (several shared holders are fine together; an
    exclusive one is alone); `what` names the job in the message it prints. Where there is no fcntl
    (Windows) this does nothing and returns None."""
    try:
        import fcntl
    except ImportError:
        return None
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a", encoding="utf-8")       # not inherited by the tools this process starts
    mode = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
    try:
        fcntl.flock(handle, mode | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"waiting: another {what} is running (lock {path}); this one goes on when it has finished",
              file=sys.stderr, flush=True)
        fcntl.flock(handle, mode)
        print(f"the other {what} has finished: going on", file=sys.stderr, flush=True)
    return handle


def downloader_lock(jobs_dir, script, shard=None):
    """One run of a downloader at a time, whoever starts it, so no item is fetched by two processes and no
    host gets twice its cap. Shards of one queue (--shard i/n) hold disjoint items and may run together;
    a run of the whole queue waits for every shard and they wait for it. Keep the result until the end."""
    name = Path(script).stem
    if not shard:
        return [file_lock(Path(jobs_dir) / f"{name}.lock", name)]
    i, n = parse_shard(shard)
    return [file_lock(Path(jobs_dir) / f"{name}.lock", name, shared=True),
            file_lock(Path(jobs_dir) / f"{name}.shard-{i}-of-{n}.lock", f"{name} --shard {i}/{n}")]


# ---------------------------------------------------------------- running tools
PROXY_VARS = ("http_proxy", "https_proxy", "ftp_proxy", "all_proxy", "socks_proxy")


def direct_env(env=None):
    """A copy of the environment without proxy settings, so every tool this pipeline starts connects
    directly. The rule 'no proxies' is enforced here, not just stated."""
    env = dict(os.environ if env is None else env)
    for name in list(env):
        if name.lower() in PROXY_VARS:
            del env[name]
    return env


def run_cmd(cmd, timeout):
    """(returncode, stdout, stderr); 124 on timeout, 127 if the executable is missing."""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout, env=direct_env())
        return done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"
    except FileNotFoundError:
        return 127, "", f"executable not found: {cmd[0]}"


def probe_duration(path, ffprobe="ffprobe"):
    """Duration in seconds via ffprobe, or None if ffprobe is missing or fails."""
    code, out, _ = run_cmd([ffprobe, "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", str(path)], 60)
    try:
        return round(float(out.strip()), 2) if code == 0 else None
    except ValueError:
        return None


def classify_error(text: str) -> str:
    """Map yt-dlp / network error text to a short class. HARD_BLOCKS stop the whole run."""
    t = (text or "").lower()
    if "not a bot" in t or ("sign in to confirm" in t and "bot" in t) \
            or "ip is likely being blocked" in t or "captcha" in t:
        return "bot_check"
    # YouTube's session limit arrives as "Video unavailable. This content isn't available, try again
    # later" plus yt-dlp's "rate-limited by YouTube for up to an hour". It must be tested before the
    # "unavailable" phrases below, or the video would be filed as removed and never tried again.
    if "http error 429" in t or "too many requests" in t or "rate-limited" in t or "rate limited" in t \
            or "try again later" in t:
        return "rate_limited"
    if "http error 403" in t or "403: forbidden" in t:
        return "forbidden"
    if "confirm your age" in t or "age-restricted" in t or "members-only" in t \
            or "join this channel" in t or "login required" in t:
        return "login_required"
    # "Requested format is not available" means yt-dlp found no usable formats at all: usually a missing
    # JavaScript runtime or a player change, not a property of this one video. Never skip it for good.
    if "requested format is not available" in t or "no video formats found" in t:
        return "no_formats"
    if any(k in t for k in ("video unavailable", "private video", "has been removed",
                            "not available", "no longer available", "has been terminated")):
        return "unavailable"
    if any(k in t for k in ("timed out", "timeout", "connection reset", "connection aborted",
                            "temporary failure", "network is unreachable", "remote end closed",
                            "unable to download", "ssl", "incompleteread")):
        return "network"
    return "other"


# ---------------------------------------------------------------- concurrency helpers
class RateLimiter:
    """At most one call start per `interval` seconds (plus jitter), shared by all threads. hold() keeps every start,
    those already waiting for their turn included, until a wait the other side asked for is over (a Retry-After)."""

    def __init__(self, interval, jitter=0.25, clock=time.monotonic, sleep=time.sleep, seed=None):
        self.interval, self.jitter = max(0.0, float(interval)), max(0.0, float(jitter))
        self._clock, self._sleep, self._rng = clock, sleep, random.Random(seed)
        self._next, self._held, self._lock = 0.0, 0.0, threading.Lock()

    def hold(self, seconds):
        with self._lock:
            self._held = max(self._held, self._clock() + float(seconds))
            self._next = max(self._next, self._held)

    def wait(self):
        while True:
            with self._lock:
                now = self._clock()
                start = max(now, self._next)
                self._next = start + self.interval * (1 + self._rng.uniform(0, self.jitter))
            if start > now:
                self._sleep(start - now)
            with self._lock:
                if self._held <= start:
                    return
            # a Retry-After came while this call waited for its turn: it takes a new turn after that wait


class Breaker:
    """Trips after `limit` hard blocks in a row (403 / 429 / bot check). A success resets it."""

    def __init__(self, limit=3):
        self.limit, self.count = max(1, int(limit)), 0
        self.tripped = threading.Event()
        self._lock = threading.Lock()

    def success(self):
        with self._lock:
            self.count = 0

    def hard_block(self):
        with self._lock:
            self.count += 1
            if self.count >= self.limit:
                self.tripped.set()


class HostGates:
    """Politeness for plain HTTP lanes: each host gets its own start-rate limit and its own breaker,
    so one publisher that answers 403 / 429 is left alone while the other hosts carry on. A Retry-After
    is obeyed: a short one delays the host's next request, a long one leaves the host alone for the run.
    Check blocked() again after wait(): a request that was waiting for its turn when the host refused
    for the last time must not go out."""

    def __init__(self, interval=1.0, stop_after=3, stop_after_failures=0, clock=time.monotonic, sleep=time.sleep):
        self.interval, self.stop_after, self.stop_after_failures = interval, stop_after, stop_after_failures
        self._clock, self._sleep = clock, sleep
        self._limiters, self._breakers, self._down, self._lock = {}, {}, {}, threading.Lock()
        self._refused = collections.Counter()

    def _get(self, host):
        with self._lock:
            if host not in self._limiters:
                self._limiters[host] = RateLimiter(self.interval, clock=self._clock, sleep=self._sleep)
                self._breakers[host] = Breaker(self.stop_after)
                self._down[host] = Breaker(self.stop_after_failures or 10 ** 9)
            return self._limiters[host], self._breakers[host], self._down[host]

    def wait(self, host):
        self._get(host)[0].wait()

    def set_interval(self, host, seconds):
        """Never go faster than `seconds` between starts on this host (a robots.txt Crawl-delay)."""
        limiter = self._get(host)[0]
        limiter.interval = max(limiter.interval, float(seconds))

    def blocked(self, host) -> bool:
        """True when the host refused (403 / 429) or failed (errors, timeouts) too many times in a row."""
        _, refused, down = self._get(host)
        return refused.tripped.is_set() or down.tripped.is_set()

    def success(self, host):
        _, refused, down = self._get(host)
        refused.success()
        down.success()

    @staticmethod
    def _hold(limiter, seconds):
        limiter.hold(seconds)

    def hard_block(self, host, retry_after=None):
        """A refusal (403 / 429). `retry_after` is the wait the host asked for, in seconds, if it said."""
        limiter, refused, _ = self._get(host)
        with self._lock:
            self._refused[host] += 1
        refused.hard_block()
        if retry_after:
            if retry_after > RETRY_AFTER_IN_RUN_S:
                refused.tripped.set()            # longer than a run should wait: not asked again on this run
            else:
                self._hold(limiter, retry_after)

    def unavailable(self, host, retry_after):
        """An answer that is not a refusal but says how long to wait: a 503 with a Retry-After. A short wait
        delays the host's next request; a longer one than a run should hold leaves the host alone for the rest
        of the run (it is then listed with the hosts that were not answering). Call failure() as well."""
        limiter, _, down = self._get(host)
        if not retry_after:
            return
        if retry_after > RETRY_AFTER_IN_RUN_S:
            down.tripped.set()
        else:
            self._hold(limiter, retry_after)

    def refused_hosts(self):
        """{host: refusals} for every host that refused at least once on this run."""
        with self._lock:
            return dict(self._refused)

    def failure(self, host):
        """A network-class failure (5xx, timeout, dropped connection). Enough in a row and the host is
        left alone for the rest of the run instead of being asked again for every queued item."""
        self._get(host)[2].hard_block()

    def blocked_hosts(self):
        with self._lock:
            return sorted(h for h, b in self._breakers.items() if b.tripped.is_set())

    def down_hosts(self):
        with self._lock:
            return sorted(h for h, b in self._down.items() if b.tripped.is_set())


# ---------------------------------------------------------------- youtube.com's robots.txt
# youtube.com's robots.txt (read 2026-11-14) disallows these paths for every user agent. yt-dlp's channel
# listing beyond the first page, its player and its caption requests all go through /youtubei/, and the
# channel RSS is /feeds/videos.xml. The project obeys robots.txt, so every step that would send such a
# request refuses unless the owner opts in with YOUTUBE_OVERRIDE=1 (a decision for the owner: HANDOFF 6).
# Paths it allows, such as a channel page or the oEmbed lookup, are read by steps that read robots.txt first.
YOUTUBE_OVERRIDE = "ET_YOUTUBE_ROBOTS_OVERRIDE"
YOUTUBE_HOSTS = ("youtube.com", "youtu.be", "youtube-nocookie.com")
YOUTUBE_DISALLOWED = ("/api/", "/channel_picker", "/comment", "/feeds/videos.xml", "/file_download", "/get_video",
                      "/get_video_info", "/get_midroll_info", "/live_chat", "/login", "/qr", "/results", "/signup",
                      "/t/terms", "/timedtext_video", "/verify_age", "/watch_ajax", "/watch_fragments_ajax",
                      "/watch_popup", "/watch_queue_ajax", "/youtubei/")
SKIPPED_BY_RULE = 9          # exit status of a step that sent nothing because a rule forbids its requests
YOUTUBE_RULE = ("youtube.com's robots.txt disallows /youtubei/ and /feeds/videos.xml, which this step requests; "
                "owner decision pending (HANDOFF 6)")
YOUTUBE_WAITS = "the YouTube lanes wait for the owner's decision on youtube.com's robots.txt (HANDOFF 6)"
# Next steps that coverage tables written before the YouTube lanes were held still carry, and their new words
OLD_YOUTUBE_STEPS = {
    "YouTube only: run the YouTube lane on a home connection": f"YouTube only: {YOUTUBE_WAITS}",
    "no downloadable source found yet: run the YouTube lane on a home connection, or find the maker's own feed or site":
        f"no downloadable source found yet: find the maker's own feed or site; {YOUTUBE_WAITS}",
}


def youtube_override() -> bool:
    """True only when the owner set ET_YOUTUBE_ROBOTS_OVERRIDE=1."""
    return os.environ.get(YOUTUBE_OVERRIDE, "").strip() == "1"


def is_youtube(url: str) -> bool:
    host = host_of(url)
    return any(host == h or host.endswith("." + h) for h in YOUTUBE_HOSTS)


def youtube_disallowed(url: str) -> bool:
    """True for an address on YouTube whose path its robots.txt disallows for every user agent."""
    if not is_youtube(url):
        return False
    from urllib.parse import urlsplit
    try:
        path = urlsplit(url).path or "/"
    except ValueError:
        return True
    return any(path.startswith(prefix) for prefix in YOUTUBE_DISALLOWED)


def youtube_gate(step: str):
    """In front of every step whose requests to YouTube go through paths its robots.txt disallows (everything
    yt-dlp does). Unless the owner opted in, it says so in one line and ends the step with SKIPPED_BY_RULE,
    before anything is read or sent."""
    if youtube_override():
        print(f"{step}: {YOUTUBE_OVERRIDE}=1: requests that youtube.com's robots.txt disallows are sent, by the "
              "owner's decision", file=sys.stderr, flush=True)
        return
    print(f"skipped: {step}: {YOUTUBE_RULE}. Nothing was sent. The owner can allow it with {YOUTUBE_OVERRIDE}=1.",
          file=sys.stderr, flush=True)
    sys.exit(SKIPPED_BY_RULE)


# ---------------------------------------------------------------- refusals remembered from one run to the next
REFUSED = ("rate_limited", "forbidden", "bot_check")   # what a host says when it does not want to be asked
REFUSAL_REST_S = 24 * 3600                              # the least a host that refused is left alone
REFUSAL_REST_MAX_S = 32 * 24 * 3600
RETRY_AFTER_IN_RUN_S = 600                              # a longer Retry-After ends the host's turn on this run
SPELL_GAP_S = 3600                                      # refusals further apart than this are separate spells


def epoch(stamp):
    """Seconds since 1970 for a 'YYYY-MM-DDTHH:MM:SSZ' stamp, or None."""
    try:
        return calendar.timegm(time.strptime(str(stamp), "%Y-%m-%dT%H:%M:%SZ"))
    except (TypeError, ValueError):
        return None


def stamp(seconds) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(seconds))


def retry_after_seconds(value, now=None):
    """The wait a Retry-After header asks for, in seconds (it is a number of seconds or an HTTP date), or None."""
    text = str(value or "").strip()
    if not text:
        return None
    if text.isdigit():
        return min(int(text), REFUSAL_REST_MAX_S)
    from email.utils import parsedate_to_datetime
    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    return min(REFUSAL_REST_MAX_S, max(0, int(when.timestamp() - (time.time() if now is None else now))))


def resting_hosts(records, host_of_record, now=None, in_a_row=3):
    """{host: {"until", "times", "answer", "since"}} for the hosts to leave alone on this run, read from the
    step's own manifest (records in the order they were written).

    A host rests when the answers since its last success are refusals (403, 429, a bot check) and one of
    them was a 429, or there were `in_a_row` of them, or the host served nothing in the day before the
    first: a 403 for one file among many successes says something about that file, not about the host.
    It rests until the longest of the Retry-After it sent, 24 hours, and a wait that doubles with each
    further spell of refusals (32 days at most). A refusal that does not make the host rest still holds it for
    the Retry-After it carried."""
    state = {}
    for rec in records:
        host = host_of_record(rec) or ""
        if not host:
            continue
        if rec.get("status") == "ok":
            served = epoch(rec.get("started")) or 0
            entry = state.setdefault(host, {"served": None, "trail": []})
            entry["served"] = max(entry["served"] or 0, served)
            entry["trail"] = [t for t in entry["trail"] if t[0] > served]   # asked after this one started: it stands
        elif rec.get("error_class") in REFUSED and epoch(rec.get("started")) is not None:
            entry = state.setdefault(host, {"served": None, "trail": []})
            entry["trail"].append((epoch(rec["started"]), rec.get("error_class"), rec.get("http_status") or rec.get("error_class"),
                                   min(REFUSAL_REST_MAX_S, float(rec.get("retry_after_s") or 0))))
    now = time.time() if now is None else now
    out = {}
    for host, entry in state.items():
        trail = entry["trail"]
        if not trail:
            continue
        served_lately = entry["served"] is not None and entry["served"] >= trail[0][0] - REFUSAL_REST_S
        rests = any(klass == "rate_limited" for _, klass, _, _ in trail) or len(trail) >= in_a_row or not served_lately
        spells, last, asked = 0, None, 0.0
        for at, _, _, wait in trail:
            if last is None or at - last > SPELL_GAP_S:
                spells, asked = spells + 1, 0.0          # a new spell: an earlier Retry-After is over
            asked, last = max(asked, wait), at
        # a refusal that says nothing about the host by itself still holds it for as long as it asked (Retry-After)
        until = last + (max(asked, min(REFUSAL_REST_MAX_S, REFUSAL_REST_S * 2 ** (spells - 1))) if rests else asked)
        if until > now:
            out[host] = {"until": until, "times": len(trail), "answer": trail[-1][2], "since": stamp(trail[0][0])}
    return out


def say_resting(resting, waiting, what="item(s)"):
    """One line on stderr per host left alone on this run because it refused on an earlier one.
    `waiting` is {host: how many items of this run it holds}."""
    for host, info in sorted(resting.items()):
        if waiting.get(host):
            answer = info["answer"]
            print(f"left alone on this run: {host} refused ({'HTTP ' + str(answer) if str(answer).isdigit() else answer}) "
                  f"{info['times']} time(s) since {info['since']}; it is asked again after {stamp(info['until'])}. "
                  f"{waiting[host]} {what} wait for it.", file=sys.stderr, flush=True)


def say_refused(gates, file=None):
    """The STOPPED line for the hosts that refused on this run, or nothing. True if there were any."""
    refused, tripped = gates.refused_hosts(), set(gates.blocked_hosts())
    if not refused:
        return False
    print("STOPPED for these hosts after 403 / 429 answers: "
          + ", ".join(f"{h} ({n}{', left alone for the rest of the run' if h in tripped else ''})" for h, n in sorted(refused.items()))
          + ". Later runs leave a host that keeps refusing alone until its wait is over (a day at least, longer if it "
          "asks or refuses again); finished items are skipped.", file=file or sys.stderr)
    return True


def host_of(url: str) -> str:
    """Lower-case host of a URL without the port, '' if there is none."""
    from urllib.parse import urlsplit
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def http_error_class(status: int) -> str:
    """Map an HTTP status to the error classes used in the manifests."""
    if status == 429:
        return "rate_limited"
    if status in (401, 403):
        return "forbidden"
    if status in (404, 410, 451):
        return "unavailable"
    if 500 <= status < 600 or status == 408:
        return "network"
    return "other"


class Progress:
    def __init__(self, total, label, every=10.0, stream=None):
        self.total, self.label, self.every = total, label, every
        self.stream = stream or sys.stderr
        self.done, self.failed = 0, 0
        self.t0, self.last = time.monotonic(), 0.0
        self._lock = threading.Lock()

    def tick(self, ok=True):
        with self._lock:
            self.done += 1
            self.failed += 0 if ok else 1
            now = time.monotonic()
            if now - self.last >= self.every or self.done == self.total:
                self.last = now
                rate = self.done / max(now - self.t0, 1e-9)
                eta = (self.total - self.done) / rate if rate else 0
                print(f"[{self.label}] {self.done}/{self.total} done, {self.failed} failed, "
                      f"{rate * 60:.1f}/min, eta {eta / 60:.1f} min", file=self.stream, flush=True)
