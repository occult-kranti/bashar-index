#!/usr/bin/env python3
"""Shared helpers for the ET-channelers batch pipeline. Standard library only.

Design rules that every script in this folder follows:
  * Raw media, captions and transcripts live OUTSIDE any Git checkout (see ensure_outside_git).
  * Every step appends one JSON line per item to a manifest, so a rerun skips finished work.
  * Items are split across workers by a stable hash, so shards never overlap.
  * A run stops early on 403/429/bot-check responses instead of retrying into them.
"""
from __future__ import annotations

import csv
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
ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
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
    )


def add_root_arg(parser):
    parser.add_argument("--root", type=Path, default=default_root(),
                        help="private data folder, must be outside any Git checkout "
                             "(default: $ET_PRIVATE_DIR or ~/et-channelers-private)")


def ensure_outside_git(path) -> Path:
    resolved = Path(path).expanduser().resolve()
    for parent in (resolved, *resolved.parents):
        if (parent / ".git").exists():
            raise SystemExit(
                f"refusing to use {resolved}: it is inside a Git checkout ({parent}). "
                "Raw audio, captions and transcripts must stay out of the repository; "
                "pass --root with a folder elsewhere.")
    return resolved


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


def append_jsonl(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    with _APPEND_LOCK, open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)


def read_jsonl(path):
    """All records in a JSONL file. A torn last line from an interrupted run is skipped."""
    path = Path(path)
    if not path.exists():
        return []
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    records = []
    for n, line in enumerate(lines, 1):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            if n == len(lines):
                continue
            raise
    return records


def latest_by_key(records, key="video_id"):
    out = {}
    for record in records:
        out[record[key]] = record
    return out


# ---------------------------------------------------------------- running tools
def run_cmd(cmd, timeout):
    """(returncode, stdout, stderr); 124 on timeout, 127 if the executable is missing."""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
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
    if "not a bot" in t or ("sign in to confirm" in t and "bot" in t):
        return "bot_check"
    if "http error 429" in t or "too many requests" in t:
        return "rate_limited"
    if "http error 403" in t or "403: forbidden" in t:
        return "forbidden"
    if "confirm your age" in t or "age-restricted" in t or "members-only" in t \
            or "join this channel" in t or "login required" in t:
        return "login_required"
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
    """At most one call start per `interval` seconds (plus jitter), shared by all threads."""

    def __init__(self, interval, jitter=0.25, clock=time.monotonic, sleep=time.sleep, seed=None):
        self.interval, self.jitter = max(0.0, float(interval)), max(0.0, float(jitter))
        self._clock, self._sleep, self._rng = clock, sleep, random.Random(seed)
        self._next, self._lock = 0.0, threading.Lock()

    def wait(self):
        with self._lock:
            now = self._clock()
            start = max(now, self._next)
            self._next = start + self.interval * (1 + self._rng.uniform(0, self.jitter))
        if start > now:
            self._sleep(start - now)


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
