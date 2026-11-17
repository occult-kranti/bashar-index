#!/usr/bin/env python3
"""Bounded native YouTube audio -> Google Drive, without transcoding or ASR.

Use an exclusively owned private --root outside Git. Every byte written by the
streaming downloader is admitted under a shared 20 GB ceiling. A 64 MB reserve
covers journals; existing files, incomplete downloads and active reservations
count too. Other applications writing into the root are outside this guarantee.

The rclone remote should point at the existing archive's ``04 Audio`` folder.
New objects go under <channel_dir>/Videos, Shorts, Recorded streams, or
Unclassified according to the source tab. Existing receipt paths stay intact.
The private audio manifest records those native formats, not 24 kbps Opus.
Successful Drive uploads are checked by remote size AND MD5, journaled with
fsync, and only then removed locally. Upload or verification failures retain
the local file. Restarting reconciles completed downloads before fetching more.

Plan/status never use the network. Run requires --limit N or --all. A bounded
--download-only --limit N pilot is available while Drive OAuth is being set up.
There is no duration filter or default per-item cap: admission uses the exact
selected audio size and metadata headroom within the whole-root budget. Items
that cannot fit remain explicitly deferred in the queue. Creating
<root>/sync/STOP_DRIVE_INGEST requests a persistent graceful stop (exit 130).
Drive rate limits create a ten-minute local cooldown; active cooldown exits 75
before any new network request. Neither marker is silently removed.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import contextlib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (HARD_BLOCKS, ID_RE, RateLimiter, add_root_arg, classify_error,
                    direct_env, ensure_outside_git, read_csv, read_jsonl,
                    sha256_file, utc_now, youtube_gate)

MAX_LOCAL_BYTES = 20_000_000_000  # decimal GB, matching the user's ceiling
JOURNAL_RESERVE = 64 * 1024 * 1024
METADATA_HEADROOM = 4 * 1024 * 1024
CHUNK = 1024 * 1024
NATIVE_EXTENSIONS = {"webm", "m4a", "opus", "ogg"}
_JOURNAL_LOCK = threading.Lock()
_ROOT_BUDGETS = {}  # writes to registered run roots also admit journal bytes
_DRIVE_CALLS = threading.BoundedSemaphore(2)


def registered_budget(path):
    return next((value for root, value in _ROOT_BUDGETS.items()
                 if Path(path).resolve().is_relative_to(root)), None)


def remove_local(path, missing_ok=False):
    budget = registered_budget(path)
    if budget:
        budget.remove(path, missing_ok=missing_ok)
    else:
        path.unlink(missing_ok=missing_ok)


def control_file(path, encoded, atomic=False):
    """Admit bounded control writes and account for replacement/truncation."""
    budget = registered_budget(path)
    with budget.lock if budget else contextlib.nullcontext():
        target = path.with_suffix(path.suffix + ".tmp") if atomic else path
        if budget and budget.usage() + len(encoded) > budget.cap:
            raise IngestError("storage_limit", "No local space for a durable control record")
        path.parent.mkdir(parents=True, exist_ok=True)
        before = target.stat().st_size if target.exists() else 0
        try:
            with open(target, "wb") as out:
                out.write(encoded)
                out.flush()
                os.fsync(out.fileno())
        finally:
            if budget:
                budget.changed((target.stat().st_size if target.exists() else 0) - before)
        if atomic:
            previous = path.stat().st_size if path.exists() else 0
            os.replace(target, path)
            if budget:
                budget.changed(-previous)


class IngestError(RuntimeError):
    """Only safe, nonsensitive messages are carried into the journal/log."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


class StopControl:
    """A persistent operator marker plus the in-process failure stop signal."""
    def __init__(self, marker):
        self.marker, self.event = Path(marker), threading.Event()

    @property
    def requested(self):
        return self.marker.exists()

    def is_set(self):
        return self.event.is_set() or self.requested

    def set(self):
        self.event.set()

    def wait(self, seconds):
        until = time.monotonic() + seconds
        while not self.is_set():
            left = until - time.monotonic()
            if left <= 0:
                return False
            self.event.wait(min(0.25, left))
        return True


@dataclass
class IngestResult:
    """A durable local pair handed from a source worker to the upload stage."""
    row: dict
    record: dict
    status: str = "ready"
    trusted: dict = field(default_factory=dict)
    remote_proofs: dict = field(default_factory=dict)
    allow_missing: bool = False
    captions: dict | None = None
    caption_only: bool = False


def terminal_unavailable(record):
    """Explicit source removal/private/unavailable response, never an access block."""
    return (record.get("status") == "unavailable" and record.get("error_class") == "unavailable"
            and not record.get("sha256") and not record.get("metadata"))


def read_drive_cooldown(path):
    if not path or not Path(path).exists():
        return None
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        until = float(value["until_epoch"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise IngestError("drive_cooldown", "Drive cooldown record is unreadable; no Drive requests sent") from exc
    return value if until > time.time() else None


def write_drive_cooldown(path, reason="drive_rate_limited"):
    if not path:
        return
    path = Path(path)
    record = {"reason": reason, "observed_at": utc_now(), "until_epoch": time.time() + 600,
              "retry_after_s": 600}
    encoded = (json.dumps(record) + "\n").encode("utf-8")
    with _JOURNAL_LOCK:
        control_file(path, encoded, atomic=True)


def journal(path, record):
    """Durable append; repair a torn tail without discarding forensic evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    with _JOURNAL_LOCK:
        budget = registered_budget(path)
        guard = budget.lock if budget else contextlib.nullcontext()
        with guard:
            if budget and budget.usage() + len(encoded) + 1 > budget.cap:
                raise IngestError("storage_limit", "Local storage ceiling leaves no room for a durable receipt")
            before = path.stat().st_size if path.exists() else 0
            try:
                _append_durable(path, encoded)
            finally:
                if budget:
                    budget.changed((path.stat().st_size if path.exists() else 0) - before)


def _append_durable(path, encoded):
    with open(path, "a+b") as out:
        out.seek(0, os.SEEK_END)
        if out.tell():
            out.seek(-1, os.SEEK_END)
            if out.read(1) != b"\n":
                out.write(b"\n")
        out.write(encoded)
        out.flush()
        os.fsync(out.fileno())


def is_link(path):
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def tree_bytes(root):
    """Count all regular files, including partials; reject linked subtrees."""
    if not root.exists():
        return 0
    total = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(base) / name
            if is_link(path):
                raise IngestError("unsafe_path", "The private root contains a link or junction")
        for name in files:
            try:
                total += (Path(base) / name).stat().st_size
            except FileNotFoundError:  # another worker just completed its verified cleanup
                pass
    return total


def local_path(root, relative):
    """A receipt or source row must never authorize access outside the root."""
    path = root / relative
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()) or resolved == root.resolve():
        raise IngestError("unsafe_path", "A file path escapes the private root")
    for item in (path, *path.parents):
        if item == root.parent:
            break
        if is_link(item):
            raise IngestError("unsafe_path", "A file path traverses a link or junction")
    return path


@contextlib.contextmanager
def exclusive_lock(root):
    """Kernel lock works on Windows and Unix and automatically releases on exit."""
    lock_path = root / "sync" / "drive_ingest.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise IngestError("locked", "Another Drive ingestion run owns this private root") from exc
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


class Budget:
    def __init__(self, root, cap, file_cap, min_free, reserve=JOURNAL_RESERVE, cached=False):
        if not 0 < cap <= MAX_LOCAL_BYTES or file_cap < 0 or reserve >= cap:
            raise ValueError("invalid storage budget")
        self.root, self.cap = root, cap
        self.explicit_file_cap = file_cap
        self.file_cap = file_cap or cap - reserve
        self.min_free, self.reserve = min_free, reserve
        self.lock = threading.RLock()
        self.active = {}
        self.cached = cached
        self._used = tree_bytes(root) if cached else 0
        self._reconciled_at = time.monotonic()

    def usage(self, reconcile=False):
        """Cached only for the exclusively owned run; all its writes share this lock."""
        with self.lock:
            if not self.cached:
                return tree_bytes(self.root)
            if reconcile or time.monotonic() - self._reconciled_at >= 12:
                self._used = tree_bytes(self.root)
                self._reconciled_at = time.monotonic()
            return self._used

    def changed(self, delta):
        if self.cached:
            self._used += delta

    def remove(self, path, missing_ok=False):
        with self.lock:
            self.usage()
            size = path.stat().st_size if path.exists() else 0
            path.unlink(missing_ok=missing_ok)
            self.changed(-size)

    def _outstanding(self, omit=None):
        return sum(max(0, item["bytes"] - (item["path"].stat().st_size if item["path"].exists() else 0))
                   for key, item in self.active.items() if key != omit)

    def reserve_item(self, key, part, expected_bytes=None, metadata_headroom=0):
        with self.lock:
            used = self.usage()
            audio_bytes = expected_bytes if expected_bytes is not None else self.explicit_file_cap or min(8 * CHUNK, self.file_cap)
            if audio_bytes <= 0 or audio_bytes > self.file_cap:
                raise IngestError("deferred_storage", f"Item needs {audio_bytes} audio bytes; retained in queue until a buffer can hold it")
            amount = audio_bytes + metadata_headroom
            outstanding = self._outstanding(omit=key)
            already = part.stat().st_size if part.exists() else 0
            additional = max(0, amount - already)
            if used + outstanding + additional > self.cap - self.reserve:
                raise IngestError("deferred_storage", f"Item needs a {amount}-byte reservation; local buffer is currently unavailable")
            if shutil.disk_usage(self.root).free - outstanding - additional < self.min_free:
                raise IngestError("deferred_storage", f"Item needs {amount} bytes while preserving the free-disk floor")
            self.active[key] = {"path": part, "bytes": amount, "metadata_headroom": metadata_headroom}

    def admit_size(self, path, total):
        """Expand an unknown/estimated reservation from the server's exact length before writing."""
        with self.lock:
            found = next(((key, item) for key, item in self.active.items() if item["path"] == path), None)
            if found:
                self.reserve_item(found[0], path, total, found[1]["metadata_headroom"])
            elif total > self.file_cap:
                raise IngestError("deferred_storage", f"Item needs {total} bytes; retained for a larger available buffer")

    def completed_path(self, key, path):
        with self.lock:
            if key in self.active:
                self.active[key]["path"] = path

    def release(self, key):
        with self.lock:
            self.active.pop(key, None)

    def pressure(self):
        with self.lock:
            return (self.usage() + self._outstanding()) / (self.cap - self.reserve)

    def write(self, out, data):
        # The check and write share one lock: two workers cannot spend the same bytes.
        with self.lock:
            if out.tell() + len(data) > self.file_cap:
                raise IngestError("deferred_storage", "Item exceeds the configured buffer capacity; retained in queue")
            if self.usage() + len(data) > self.cap - self.reserve:
                raise IngestError("storage_limit", "Local storage ceiling reached")
            if shutil.disk_usage(self.root).free - len(data) < self.min_free:
                raise IngestError("disk_floor", "Free disk space reached the safety floor")
            before = out.tell()
            try:
                out.write(data)
                out.flush()  # subsequent workers' file-size checks see these bytes
            finally:
                self.changed(max(0, out.tell() - before))


def select_queue(path, newest=20, entire_queue=False):
    if not entire_queue and not 1 <= newest <= 50:
        raise ValueError("newest must be between 1 and 50")
    rows, seen, ranks = [], set(), set()
    for row in read_csv(path):
        video_id, channel = row.get("video_id", ""), row.get("channel_dir", "")
        if not ID_RE.fullmatch(video_id):
            raise ValueError("Queue contains an invalid YouTube video ID")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", channel) or channel in {".", ".."}:
            raise ValueError("Queue contains an unsafe channel directory")
        tab = row.get("tab", "")
        if not entire_queue and tab != "videos":
            raise ValueError("Queue must contain only the Videos tab")
        if entire_queue and tab not in {"videos", "shorts", "streams", ""}:
            raise ValueError("Entire queue contains an unknown source tab")
        try:
            rank = None if entire_queue and not row.get("listing_rank") else int(row["listing_rank"])
        except (KeyError, ValueError) as exc:
            raise ValueError("Queue needs zero-based listing_rank from fresh channel listings") from exc
        if rank is not None and rank < 0:
            raise ValueError("Queue contains a negative listing rank")
        if (not entire_queue and rank >= newest) or video_id in seen:
            continue
        if not entire_queue and rank is not None and (channel, tab, rank) in ranks:
            raise ValueError("Queue contains duplicate listing ranks within a channel")
        row["url"] = f"https://www.youtube.com/watch?v={video_id}"
        row["listing_rank"] = rank
        seen.add(video_id)
        ranks.add((channel, tab, rank))
        rows.append(row)
    ordered = sorted(rows, key=lambda row: (row["listing_rank"] is None, row["listing_rank"] or 0,
                                            row["channel_dir"], row.get("tab", "")))
    if not entire_queue:
        return ordered
    channels = {}
    for row in ordered:
        channels.setdefault(row["channel_dir"], collections.deque()).append(row)
    fair = []
    while channels:
        for channel in list(channels):
            fair.append(channels[channel].popleft())
            if not channels[channel]:
                del channels[channel]
    return fair


def run_tool(command, timeout=300):
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=timeout, env=direct_env())
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IngestError("tool_unavailable", "A required tool could not complete; check installation/connectivity") from exc
    return result


def extract_audio(args, row, metadata_only=False):
    command = [args.ytdlp, "--ignore-config", "--proxy", "", "--no-playlist", "--no-progress",
                       "--skip-download", "--dump-single-json", "--retries", "0", "--extractor-retries", "0",
                       "--socket-timeout", "30", "--sleep-requests", "0.75"]
    command += ["--ignore-no-formats-error"] if metadata_only else ["-f", "bestaudio[protocol=https][vcodec=none]"]
    client = getattr(args, "youtube_client", "default")
    if client == "mweb":
        command += ["--extractor-args", "youtube:player_client=mweb"]
    if metadata_only or getattr(args, "collect_captions", False):
        # Declare caption intent so yt-dlp reports access-policy warnings, while
        # simulation returns before its subtitle transport or filesystem writes.
        command += ["--simulate", "--write-subs", "--write-auto-subs", "--sub-langs", "en.*",
                    "--sub-format", "json3/vtt"]
    result = run_tool(command + [row["url"]], args.timeout)
    if result.returncode:
        kind = classify_error(result.stderr)
        # yt-dlp can report a scheduled premiere before it returns JSON metadata.
        # Match only its explicit error for this item; access/cooldown errors win.
        upcoming = re.search(
            r"(?im)^\s*ERROR:\s+\[youtube\]\s+" + re.escape(row["video_id"]) +
            r":\s*(?:Premieres in\s+[^\r\n]+|This live event will begin\b[^\r\n]*)$",
            result.stderr or "")
        if kind == "other" and upcoming:
            raise IngestError("live", "Upcoming premiere/live event has not started; item remains pending")
        raise IngestError(kind, "YouTube metadata/audio selection failed; no alternate client or credentials tried")
    try:
        info = json.loads(result.stdout)
    except ValueError as exc:
        raise IngestError("metadata", "yt-dlp did not return valid metadata") from exc
    # Keep a constant access signal, never raw warning text, URLs or credentials.
    if any(re.search(r"(?i)\b(?:subtitles?|subs)\b", line) and
           re.search(r"(?i)\bPO[ -]?token\b", line) and
           re.search(r"(?i)\b(?:requires?|required|missing|not provided)\b", line)
           for line in (result.stderr or "").splitlines() if line.lstrip().startswith("WARNING:")):
        info["_caption_access_warning"] = "subtitle_access_requirement"
    if info.get("id") != row["video_id"]:
        raise IngestError("metadata", "Metadata is not for the requested source item")
    if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
        raise IngestError("live", "Live/upcoming source is not a completed recording")
    if metadata_only:
        return info
    if info.get("vcodec") != "none":
        raise IngestError("metadata", "Selected media is not the requested audio-only item")
    if info.get("protocol") != "https" or info.get("ext") not in NATIVE_EXTENSIONS:
        raise IngestError("unsupported_format", "No supported native HTTPS audio stream was selected")
    if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
        raise IngestError("live", "Live/upcoming streams are outside the Videos-only queue")
    checked_cdn_url(info.get("url", ""))
    return info


def checked_cdn_url(url):
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or parsed.username or not host.endswith(".googlevideo.com"):
        raise IngestError("unsafe_url", "Audio URL is not an HTTPS YouTube media endpoint")
    return url


class MediaRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        checked_cdn_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def stream_audio(info, part, budget, rate_bytes, stop, http_chunk_bytes=0):
    """Write admitted chunks; optional HTTP ranges require exact offsets/totals.

    Ranges use the same successful media URL. A 200 response to the very first
    range may fall back to a complete response; later ranges must return 206.
    There are no retries, alternate clients, cookies, or proxy connections.
    """
    headers = {key: value for key, value in (info.get("http_headers") or {}).items()
               if key.lower() in {"user-agent", "accept", "accept-language", "origin", "referer"}}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), MediaRedirect())
    started, downloaded = time.monotonic(), 0
    reported = started
    total = int(info["filesize"]) if info.get("filesize") else None
    if total is not None and (total <= 0 or total > budget.file_cap):
        raise IngestError("deferred_storage", "Selected audio length exceeds the available buffer; retained in queue")
    md5, sha256 = hashlib.md5(), hashlib.sha256()
    validator = None
    try:
        with open(part, "wb") as out:
            while total is None or downloaded < total:
                if stop.is_set():
                    raise IngestError("stopped", "Run stopped before the next audio range")
                request_headers = dict(headers)
                range_end = None
                if http_chunk_bytes:
                    range_end = downloaded + http_chunk_bytes - 1
                    if total is not None:
                        range_end = min(range_end, total - 1)
                    request_headers["Range"] = f"bytes={downloaded}-{range_end}"
                    if validator:
                        request_headers["If-Range"] = validator
                req = urllib.request.Request(checked_cdn_url(info["url"]), headers=request_headers)
                with opener.open(req, timeout=30) as response:
                    length = response.headers.get("Content-Length")
                    content_range = response.headers.get("Content-Range")
                    if response.status == 206 and http_chunk_bytes:
                        match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", content_range or "")
                        if not match:
                            raise IngestError("truncated", "Range response lacks an exact complete Content-Range")
                        begin, end, full = map(int, match.groups())
                        if (begin != downloaded or full <= 0 or end != min(range_end, full - 1)
                                or (total is not None and full != total) or end < begin):
                            raise IngestError("truncated", "Range response offsets or total differ from the requested audio")
                        expected = end - begin + 1
                        if length is None or int(length) != expected:
                            raise IngestError("truncated", "Range byte count differs from Content-Range")
                        total = full
                    elif response.status == 200 and downloaded == 0 and not content_range:
                        expected = int(length) if length is not None else total
                        if expected is None or expected <= 0:
                            raise IngestError("unknown_length", "Audio response has no verifiable complete byte length")
                        if total is not None and total != expected:
                            raise IngestError("truncated", "Server length differs from the selected audio's full byte length")
                        total = expected  # initial Range ignored: validate the full body instead
                    else:
                        raise IngestError("truncated", "Server did not return the requested complete audio range")
                    budget.admit_size(part, total)
                    current_validator = response.headers.get("ETag") or response.headers.get("Last-Modified")
                    if validator and current_validator and current_validator != validator:
                        raise IngestError("changed_source", "Audio resource changed between range responses")
                    validator = current_validator or validator
                    received = 0
                    read = getattr(response, "read1", response.read)
                    while True:
                        if stop.is_set():
                            raise IngestError("stopped", "Run stopped before this download completed")
                        data = read(64 * 1024)
                        if not data:
                            break
                        if received + len(data) > expected:
                            raise IngestError("truncated", "Audio response exceeds its declared byte count")
                        budget.write(out, data)
                        md5.update(data)
                        sha256.update(data)
                        downloaded += len(data)
                        received += len(data)
                        now = time.monotonic()
                        if now - reported >= 15:
                            print(json.dumps({"video_id": info.get("id", ""), "status": "downloading",
                                              "bytes": downloaded, "total_bytes": total,
                                              "elapsed_s": round(now - started, 1),
                                              "average_kib_s": round(downloaded / max(0.001, now - started) / 1024, 1)}), flush=True)
                            reported = now
                        pause = downloaded / rate_bytes - (now - started)
                        if pause > 0:
                            stop.wait(pause)
                    if received != expected:
                        raise IngestError("truncated", "Audio response ended before its declared byte count")
                # Every completed range is proven contiguous before the next request.
            out.flush()
            os.fsync(out.fileno())
        if downloaded == 0 or downloaded != total:
            raise IngestError("truncated", "Audio response was empty or incomplete")
    except urllib.error.HTTPError as exc:
        kind = {403: "forbidden", 429: "rate_limited"}.get(exc.code, "network")
        raise IngestError(kind, f"YouTube media request returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise IngestError("network", "Audio stream interrupted; partial file retained") from exc
    return {"bytes": downloaded, "md5": md5.hexdigest(), "sha256": sha256.hexdigest()}


def hash_file(path):
    md5, sha256 = hashlib.md5(), hashlib.sha256()
    with open(path, "rb") as src:
        for block in iter(lambda: src.read(CHUNK), b""):
            md5.update(block)
            sha256.update(block)
    return {"bytes": path.stat().st_size, "md5": md5.hexdigest(), "sha256": sha256.hexdigest()}


def fingerprint(path):
    stat = path.stat()
    return (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino, stat.st_dev)


def validate_local(path, expected, trusted=None):
    """Use current-run stream hashes when stat identity is unchanged; hash resumes once."""
    before = fingerprint(path)
    if trusted != before:
        actual = hash_file(path)
        if fingerprint(path) != before or any(actual[key] != expected.get(key) for key in ("bytes", "md5", "sha256")):
            raise IngestError("local_changed", "Local bytes changed since capture; all local artifacts retained")
    return before


SOURCE_FOLDERS = {"videos": "Videos", "shorts": "Shorts", "streams": "Recorded streams", "": "Unclassified"}


def remote_path(remote, row, extension, legacy=False):
    folder = "YouTube native" if legacy else SOURCE_FOLDERS.get(row.get("tab", ""), "Unclassified")
    return remote.rstrip("/") + ("" if remote.endswith(":") else "/") + \
        f"{row['channel_dir']}/{folder}/{row['video_id']}.{extension}"


def valid_recorded_remote(remote, row, extension, recorded):
    """Accept known archive layouts within this exact root/channel/item, never move legacy objects."""
    candidates = {remote_path(remote, dict(row, tab=tab), extension) for tab in SOURCE_FOLDERS}
    candidates.add(remote_path(remote, row, extension, legacy=True))
    return recorded in candidates


def item_remote_path(remote, row, extension, record=None):
    if record and record.get("remote"):
        audio_extension = Path(record.get("path", "")).suffix.lstrip(".")
        if not valid_recorded_remote(remote, row, audio_extension, record["remote"]):
            raise IngestError("drive_destination", "Receipt belongs to a different archive destination")
        return record["remote"].rpartition("/")[0] + f"/{row['video_id']}.{extension}"
    return remote_path(remote, row, extension)


def remote_relative(remote, target):
    prefix = remote.rstrip("/") + ("" if remote.endswith(":") else "/")
    if not target.startswith(prefix):
        raise IngestError("drive_destination", "An upload path is outside the configured archive")
    path = target[len(prefix):]
    if not path or any(part in {"", ".", ".."} for part in path.split("/")) or any(
            char in path for char in ("\\", "\n", "\r", "\0", ":")):
        raise IngestError("drive_destination", "An upload path is not a safe relative filename")
    return path


@contextlib.contextmanager
def batch_manifest(root, paths):
    """A bounded exact-file manifest, never a broad archive listing or sync."""
    paths = list(paths)
    if len(paths) != len(set(paths)) or not paths or len(paths) > 128:
        raise IngestError("drive_destination", "Invalid or duplicate batch filenames")
    for path in paths:
        remote_relative("batch:", "batch:" + path)
    manifest = local_path(root, "sync/drive_ingest_batch_files.txt")
    encoded = ("\n".join(paths) + "\n").encode("utf-8")
    control_file(manifest, encoded)
    try:
        yield manifest
    finally:
        remove_local(manifest, missing_ok=True)


class Rclone:
    UPLOAD_CHUNK = "32M"  # four upload transfers reserve at most 128 MiB of Drive chunk buffers
    RETRY_FLAGS = ["--retries", "2", "--low-level-retries", "2", "--retries-sleep", "5s",
                   "--contimeout", "15s", "--timeout", "60s", "--tpslimit", "2", "--tpslimit-burst", "1"]

    def __init__(self, executable, config=None, cooldown_path=None):
        self.command = [executable] + (["--config", str(config)] if config else [])
        self.cooldown_path = cooldown_path

    def execute(self, arguments, timeout, operation):
        with _DRIVE_CALLS:
            if read_drive_cooldown(self.cooldown_path):
                raise IngestError("drive_cooldown", "Drive rate-limit rest period is active; local artifacts retained")
            result = run_tool(self.command + arguments, timeout)
            if result.returncode:
                self.failure(result, operation)
            return result

    def stat(self, remote):
        result = self.execute(["lsjson", remote, "--stat", "--hash", *self.RETRY_FLAGS], 300, "metadata read")
        try:
            value = json.loads(result.stdout)
            if not isinstance(value, dict):
                raise ValueError
            return value
        except ValueError as exc:
            raise IngestError("drive_read", "Drive metadata was invalid; local audio retained") from exc

    def preflight(self, remote):
        # A root --stat may be synthetic on Drive. Force one shallow backend read.
        result = self.execute(["lsjson", remote, "--max-depth", "1", "--dirs-only", "--disable", "ListR",
                               "--no-modtime", "--no-mimetype", *self.RETRY_FLAGS], 300, "archive connection check")
        try:
            if not isinstance(json.loads(result.stdout), list):
                raise ValueError
        except ValueError as exc:
            raise IngestError("drive_destination", "Drive destination is not a readable folder") from exc

    def copy(self, path, remote):
        self.execute(["copyto", str(path), remote, "--checksum", "--immutable",
                          "--transfers", "1", "--checkers", "1", "--buffer-size", "1M",
                          "--drive-chunk-size", self.UPLOAD_CHUNK, *self.RETRY_FLAGS], 3600, "single-file upload")

    def copy_pair(self, audio, metadata, audio_remote, metadata_remote):
        """One batch, exactly two files, no staging copies or broad folder sync."""
        audio_parent, metadata_parent = audio.parent.resolve(), metadata.parent.resolve()
        remote_parent, _, audio_name = audio_remote.rpartition("/")
        meta_remote_parent, _, metadata_name = metadata_remote.rpartition("/")
        if audio_parent != metadata_parent or remote_parent != meta_remote_parent or not remote_parent:
            raise IngestError("drive_destination", "Audio and metadata must share one upload destination folder")
        if audio.name != audio_name or metadata.name != metadata_name:
            raise IngestError("drive_destination", "Batch destination names differ from the verified local names")
        self.execute(["copy", str(audio_parent), remote_parent, "--max-depth", "1",
                          "--include", f"/{audio.name}", "--include", f"/{metadata.name}",
                          "--checksum", "--immutable", "--transfers", "2", "--checkers", "2",
                          "--buffer-size", "1M", "--drive-chunk-size", self.UPLOAD_CHUNK, *self.RETRY_FLAGS], 3600,
                     "audio/metadata batch upload")

    def copy_batch(self, local_root, remote, manifest, transfers=2):
        if not isinstance(transfers, int) or not 1 <= transfers <= 4:
            raise ValueError("upload transfers must be an integer from 1 to 4")
        self.execute(["copy", str(local_root), remote, "--files-from-raw", str(manifest),
                      "--no-traverse", "--checksum", "--immutable", "--transfers", str(transfers),
                      "--checkers", "2", "--buffer-size", "1M", "--drive-chunk-size", self.UPLOAD_CHUNK,
                      *self.RETRY_FLAGS], 3600, "bounded audio/metadata upload")

    def stat_batch(self, remote, paths, manifest):
        """One process, direct lookups of named objects; never recurse over Drive."""
        result = self.execute(["lsjson", remote, "--recursive", "--files-only", "--hash-type", "MD5",
                               "--no-modtime", "--no-mimetype", "--files-from-raw", str(manifest),
                               "--no-traverse", "--checkers", "2", *self.RETRY_FLAGS], 600,
                              "bounded batch metadata read")
        try:
            entries = json.loads(result.stdout)
            if not isinstance(entries, list):
                raise ValueError
            found, ids = {}, set()
            for entry in entries:
                path, identity = entry.get("Path"), entry.get("ID")
                if path not in paths or path in found or (identity and identity in ids):
                    raise ValueError
                found[path] = entry
                if identity:
                    ids.add(identity)
            if set(found) != set(paths):
                raise ValueError
            return found
        except (ValueError, AttributeError, TypeError) as exc:
            raise IngestError("drive_verify", "Batch metadata is missing, ambiguous, or invalid; local pairs retained") from exc

    def failure(self, result, operation):
        """Report useful categories/exit codes without exposing raw URLs or auth errors."""
        error = (getattr(result, "stderr", "") or "").lower()
        classes = [("drive_rate_limited", ("ratelimit", "rate limit", "quota", "429")),
                   ("drive_auth", ("invalid_grant", "invalid credentials", "unauthorized", "401")),
                   ("drive_conflict", ("immutable", "already exists")),
                   ("drive_permission", ("permission", "forbidden", "403")),
                   ("drive_not_found", ("not found", "notfound", "404")),
                   ("drive_network", ("timeout", "timed out", "connection reset", "connection refused", "i/o timeout")),
                   ("drive_server", ("backenderror", "internal error", "503", "502", "500"))]
        kind = next((name for name, terms in classes if any(term in error for term in terms)), "drive_upload")
        known_reasons = ("userRateLimitExceeded", "rateLimitExceeded", "dailyLimitExceeded", "quotaExceeded",
                         "storageQuotaExceeded", "insufficientPermissions", "authError", "notFound")
        reason = next((value for value in known_reasons if value.lower() in error), "")
        if kind == "drive_rate_limited":
            write_drive_cooldown(self.cooldown_path, reason or kind)
        detail = f", Google reason {reason}" if reason else ""
        raise IngestError(kind, f"Drive {operation} failed (rclone exit {result.returncode}, {kind}{detail}); local artifacts retained")


def verify_remote(metadata, expected):
    hashes = {str(key).lower(): value for key, value in (metadata.get("Hashes") or {}).items()}
    if metadata.get("IsDir") or int(metadata.get("Size", -1)) != expected["bytes"]:
        raise IngestError("drive_verify", "Drive byte count differs; local audio retained")
    if not hashes.get("md5") or hashes["md5"].lower() != expected["md5"].lower():
        raise IngestError("drive_verify", "Drive MD5 is missing or differs; local audio retained")


def verify_and_delete(root, record, drive, state_path, require_metadata=False, allow_missing=False,
                      trusted=None, remote_proofs=None):
    """Verify every artifact before deleting any. CLI always requires the pair.

    allow_missing is only for previously verified remote audio / deletion-crash
    recovery; remote size/hash readback is still required for every artifact.
    """
    if require_metadata and not record.get("metadata"):
        raise IngestError("metadata_missing", "Research metadata is not ready; audio retained")
    artifacts = [("audio", record)]
    if record.get("metadata"):
        artifacts.append(("metadata", record["metadata"]))
    checked = []
    verified = dict(record, status="verified", verified_at=utc_now())
    for kind, expected in artifacts:
        path = local_path(root, expected["path"])
        if path.exists():
            known = validate_local(path, expected, (trusted or {}).get(kind))
            checked.append((path, expected, known))
        elif not allow_missing:
            raise IngestError("local_missing", "An artifact is missing before verified storage")
        remote = (remote_proofs or {}).get(kind) or drive.stat(expected["remote"])
        verify_remote(remote, expected)
        if require_metadata and not remote.get("ID"):
            raise IngestError("drive_verify", "Drive object identity is missing; local pairs retained")
        if kind == "audio":
            verified["drive_id"] = remote.get("ID", "")
        else:
            verified["metadata"] = dict(expected, drive_id=remote.get("ID", ""))
    journal(state_path, verified)  # proof is durable before deletion
    for path, expected, known in checked:
        validate_local(path, expected, known)
    for path, _, _ in checked:
        remove_local(path)
    done = dict(verified, status="deleted", deleted_at=utc_now())
    journal(state_path, done)
    return done


def receipt_complete(record, row, remote):
    """Public phase gate: both independently checked objects and the same destination."""
    metadata = record.get("metadata") or {}
    return bool(record.get("status") == "deleted" and record.get("drive_id") and
                record.get("md5") and record.get("sha256") and metadata.get("drive_id") and
                metadata.get("md5") and metadata.get("sha256") and
                valid_recorded_remote(remote, row, Path(record.get("path", "")).suffix.lstrip("."), record.get("remote")) and
                metadata.get("remote") == record.get("remote", "").rpartition("/")[0] + f"/{row['video_id']}.info.json")


def ensure_metadata(args, row, rec, budget, limiter, stop, drive, state_path, info=None, captured_at=None,
                    trusted=None, remote_proofs=None):
    """Create once, or reconcile the exact same metadata bytes on restart."""
    metadata = rec.get("metadata")
    if metadata:
        path = local_path(args.root, metadata["path"])
        part = path.with_suffix(path.suffix + ".part")
        if not path.exists() and part.exists():
            actual = hash_file(part)
            if any(actual[key] != metadata[key] for key in ("bytes", "md5", "sha256")):
                raise IngestError("local_changed", "Completed metadata partial differs from its receipt; retained")
            os.replace(part, path)
        if path.exists():
            known = validate_local(path, metadata)
            if trusted is not None:
                trusted["metadata"] = known
            return path
        if drive and metadata.get("remote"):
            proof = drive.stat(metadata["remote"])
            verify_remote(proof, metadata)
            if remote_proofs is not None:
                remote_proofs["metadata"] = proof
            return None  # previously uploaded sidecar, checked without re-extracting
        raise IngestError("metadata_missing", "Recorded metadata is missing locally and has no checked Drive copy")
    if info is None:
        if stop.is_set() or getattr(args, "youtube_blocked", False):
            raise IngestError("youtube_cooldown", "Metadata backfill waits for YouTube's rest period; audio retained")
        limiter.wait()
        if stop.is_set():
            raise IngestError("stopped", "Metadata backfill stopped before a request")
        info = extract_audio(args, row)
        captured_at = utc_now()
    from media_metadata import build_metadata
    data = build_metadata(info, row, captured_at or utc_now())
    audio_destination = item_remote_path(args.remote, row, Path(rec["path"]).suffix.lstrip("."), rec) if args.remote else None
    data["archive_audio"] = {key: rec.get(key) for key in ("video_id", "bytes", "md5", "sha256", "drive_id")}
    data["archive_audio"].update(file_name=Path(rec["path"]).name, remote=audio_destination,
                                 encoding="native audio; no re-encode")
    encoded = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    relative = str(Path(rec["path"]).with_name(f"{row['video_id']}.info.json")).replace("\\", "/")
    path = local_path(args.root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise IngestError("local_changed", "Metadata file exists without its receipt; retained")
    part = path.with_suffix(path.suffix + ".part")
    if part.exists():
        remove_local(part)
    with open(part, "wb") as out:
        for offset in range(0, len(encoded), CHUNK):
            budget.write(out, encoded[offset:offset + CHUNK])
        out.flush()
        os.fsync(out.fileno())
    rec["metadata"] = dict(bytes=len(encoded), md5=hashlib.md5(encoded).hexdigest(),
                           sha256=hashlib.sha256(encoded).hexdigest(), path=relative,
                           remote=item_remote_path(args.remote, row, "info.json", rec) if args.remote else "")
    rec["status"] = "metadata_complete"
    journal(state_path, rec)  # hashes survive a crash before the sidecar rename
    os.replace(part, path)
    if trusted is not None:
        trusted["metadata"] = fingerprint(path)
    rec["status"] = "metadata_ready"
    journal(state_path, rec)
    return path


def load_state(path):
    latest = {}
    for rec in read_jsonl(path):
        if rec.get("video_id"):
            latest[rec["video_id"]] = rec
    return latest


CAPTION_POLICY = "english-published-and-original-automatic-v1"


class CaptionControl:
    """Serialize timedtext requests and keep their rest window separate from audio."""
    def __init__(self, records=(), min_interval=15.0):
        self.request_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.min_interval, self.next_start = min_interval, 0.0
        self.until, self.reason, self.stop = 0.0, "", None
        for record in records:
            kind = record.get("source_error_class", record.get("error_class", ""))
            until = float(record.get("retry_not_before_epoch", 0))
            if kind in HARD_BLOCKS and until > self.until:
                self.until, self.reason = until, kind

    def active(self):
        with self.state_lock:
            return self.until > time.time()

    def block(self, kind):
        with self.state_lock:
            self.until, self.reason = max(self.until, time.time() + 86400), kind

    @contextlib.contextmanager
    def slot(self, stop):
        while not self.request_lock.acquire(timeout=0.25):
            if stop.is_set():
                raise IngestError("stopped", "Caption request stopped while waiting for its slot")
            if self.active():
                raise IngestError("caption_cooldown", "Caption endpoint is resting; audio may continue")
        try:
            if self.active():
                raise IngestError("caption_cooldown", "Caption endpoint is resting; audio may continue")
            if stop.is_set():
                raise IngestError("stopped", "Caption request stopped before starting")
            self.stop = stop
            try:
                yield
            except Exception as exc:
                if getattr(exc, "kind", "") in HARD_BLOCKS:
                    self.block(exc.kind)  # close the breaker before another worker gets its slot
                raise
        finally:
            self.stop = None
            self.request_lock.release()

    def wait(self):
        """Passed to fetch_track, including redirects: every request start is paced."""
        if self.active():
            raise IngestError("caption_cooldown", "Caption endpoint is resting; audio may continue")
        pause = self.next_start - time.monotonic()
        if pause > 0 and self.stop.wait(pause):
            raise IngestError("stopped", "Caption request stopped during its pacing interval")
        if self.stop.is_set():
            raise IngestError("stopped", "Caption request stopped before its network call")
        self.next_start = time.monotonic() + self.min_interval


def caption_needs_source(record):
    return not record.get("captured_at") or bool(record.get("unresolved")) or any(
        not track.get("bundle") for track in record.get("tracks", []))


def write_caption_backfill_summary(args, audio_state, caption_state, control):
    pending, source = 0, 0
    for video_id, record in audio_state.items():
        if not receipt_complete(record, record, args.remote or ""):
            continue
        captions = caption_state.get(video_id, {})
        if not caption_receipt_complete(captions, record, args.remote or ""):
            pending += 1
            source += int(caption_needs_source(captions))
    summary = {"schema_version": 1, "policy": CAPTION_POLICY, "remote": args.remote or "",
               "updated_at": utc_now(), "endpoint": "youtube_captions",
               "pending_verified_audio_videos": pending, "pending_source_videos": source,
               "retry_not_before_epoch": control.until if source and control.until > 0 else 0,
               "error_class": control.reason if source and control.until > 0 else ""}
    control_file(args.root / "sync" / "drive_caption_backfill_state.json",
                 (json.dumps(summary) + "\n").encode("utf-8"), atomic=True)
    return summary


def caption_track_verified(track, row, remote):
    bundle = track.get("bundle") or {}
    identity = track.get("track_id", "")
    if not isinstance(identity, str) or not isinstance(bundle, dict) or not isinstance(bundle.get("bytes"), int):
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}", identity) and
                track.get("status") in {"verified", "deleted"} and bundle.get("drive_id") and
                bundle.get("bytes", 0) > 0 and re.fullmatch(r"[a-f0-9]{32}", str(bundle.get("md5", ""))) and
                re.fullmatch(r"[a-f0-9]{64}", str(bundle.get("sha256", ""))) and
                valid_recorded_remote(remote, row, f"captions.{identity}.zip", bundle.get("remote")))


def caption_receipt_complete(record, row, remote):
    if record.get("policy") != CAPTION_POLICY or record.get("unresolved"):
        return False
    tracks = record.get("tracks", [])
    if record.get("status") == "none":
        return not tracks and bool(record.get("captured_at"))
    return bool(record.get("status") == "deleted" and tracks and
                len({track.get("track_id") for track in tracks}) == len(tracks) and
                all(caption_track_verified(track, row, remote) for track in tracks))


class _BudgetZipWriter:
    """Unseekable ZIP output makes every header/data write append-only and admitted."""
    def __init__(self, output, budget):
        self.output, self.budget = output, budget

    def write(self, data):
        self.budget.write(self.output, data)
        return len(data)

    def tell(self):
        return self.output.tell()

    def flush(self):
        self.output.flush()


def caption_bundle(args, row, audio, spec, budget, limiter, stop, state, state_path):
    from youtube_captions import fetch_track, normalize_caption, provenance
    track = next(track for track in state["tracks"] if track["track_id"] == spec["track_id"])
    identity = spec["track_id"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}", identity) or spec["ext"] not in {"json3", "vtt"}:
        raise IngestError("caption_metadata", "Caption identity/format is unsafe")
    extension = f"captions.{identity}.zip"
    destination = item_remote_path(args.remote, row, extension, audio) if args.remote else ""
    relative = ("audio/" + remote_relative(args.remote, destination)) if destination else (
        f"audio/{row['channel_dir']}/{SOURCE_FOLDERS.get(row.get('tab', ''), 'Unclassified')}/{row['video_id']}.{extension}")
    path = local_path(args.root, relative)
    part, raw = path.with_suffix(".zip.part"), path.with_suffix(".raw.part")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise IngestError("local_changed", "Caption bundle exists without matching completion evidence")
    for old in (part, raw):
        if old.exists():
            remove_local(old)
    key = f"caption:{row['video_id']}:{identity}"
    budget.reserve_item(key, raw, CHUNK)
    try:
        with args.caption_control.slot(stop):
            with open(raw, "wb") as output:
                measured = fetch_track(spec, output, budget=budget, limiter=args.caption_control, stop=stop)
                output.flush()
                os.fsync(output.fileno())
        normalized = normalize_caption(raw.read_bytes(), spec["ext"])
        detail = dict(provenance(spec), captured_at=state["captured_at"], policy=CAPTION_POLICY,
                      raw={key: measured[key] for key in ("bytes", "md5", "sha256")},
                      normalization_version=normalized.get("normalization_version", 1))
        with open(part, "wb") as output:
            with zipfile.ZipFile(_BudgetZipWriter(output, budget), "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=1) as bundle:
                with bundle.open(f"raw.{spec['ext']}", "w") as member, open(raw, "rb") as source:
                    for block in iter(lambda: source.read(CHUNK), b""):
                        member.write(block)
                bundle.writestr("segments.json", json.dumps(normalized, ensure_ascii=False).encode("utf-8"))
                bundle.writestr("transcript.txt", normalized["text"].encode("utf-8"))
                bundle.writestr("provenance.json", json.dumps(detail, ensure_ascii=False, indent=2).encode("utf-8"))
            output.flush()
            os.fsync(output.fileno())
        track.update(status="ready", bundle=dict(hash_file(part), path=relative, remote=destination))
        journal(state_path, state)  # ZIP hashes precede promotion and later deletion
        os.replace(part, path)
        remove_local(raw)
        return track
    finally:
        budget.release(key)


def prepare_captions(args, row, audio, budget, limiter, stop, info=None):
    """Independent, resumable caption evidence; failures never invalidate audio receipts."""
    from youtube_captions import CaptionError, select_tracks, provenance
    state_path = args.root / "sync" / "drive_caption_manifest.jsonl"
    previous = getattr(args, "caption_state", {}).get(row["video_id"], {})
    state = json.loads(json.dumps(previous)) if previous else {
        "video_id": row["video_id"], "channel_dir": row["channel_dir"], "policy": CAPTION_POLICY,
        "tracks": [], "unresolved": [], "status": "pending"}
    if not hasattr(args, "caption_state"):
        args.caption_state = {}
    args.caption_state[row["video_id"]] = state
    if not hasattr(args, "caption_control"):
        args.caption_control = CaptionControl(args.caption_state.values())
    control = args.caption_control
    if caption_receipt_complete(state, row, args.remote or ""):
        return state
    try:
        for track in state["tracks"]:
            bundle = track.get("bundle")
            if not bundle:
                continue
            if args.remote and not valid_recorded_remote(args.remote, row,
                    f"captions.{track['track_id']}.zip", bundle.get("remote")):
                raise IngestError("drive_destination", "Caption receipt belongs to another destination")
            if track.get("status") == "deleted":
                if not caption_track_verified(track, row, args.remote or ""):
                    raise IngestError("drive_verify", "Caption deletion receipt lacks complete proof")
                continue
            path = local_path(args.root, bundle["path"])
            part = path.with_suffix(".zip.part")
            if not path.exists() and part.exists():
                validate_local(part, bundle)
                os.replace(part, path)
            if path.exists():
                validate_local(path, bundle)
            elif track.get("status") != "verified":
                raise IngestError("local_missing", "Caption bundle is missing without verified storage")
        if state.get("policy") == CAPTION_POLICY and state.get("captured_at") and not state.get("unresolved") and all(track.get("bundle") for track in state["tracks"]):
            state["status"] = "ready" if state["tracks"] else "none"
            journal(state_path, state)
            return state
        if info is None:
            if control.active():
                raise IngestError("caption_cooldown", "Caption backfill waits for its endpoint rest period")
            if stop.is_set() or getattr(args, "youtube_blocked", False):
                raise IngestError("youtube_cooldown", "Caption discovery waits for the source rest period")
            limiter.wait()
            if stop.is_set():
                raise IngestError("stopped", "Caption discovery stopped before a request")
            info = extract_audio(args, row, metadata_only=True)
        selected = select_tracks(info)
        old = {track["track_id"]: track for track in state["tracks"]}
        state.update(captured_at=utc_now(), status="discovered", policy=CAPTION_POLICY,
                     excluded_translated=selected.get("excluded_translated", 0),
                     excluded_languages=selected.get("excluded_languages", 0),
                     excluded_noncaption=selected.get("excluded_noncaption", 0),
                     inventory_status=selected.get("inventory_status", "incomplete"),
                     unresolved=selected.get("unresolved", []))
        for spec in selected["tracks"]:
            old.setdefault(spec["track_id"], dict(provenance(spec), status="pending"))
        state["tracks"] = list(old.values())
        journal(state_path, state)
        for spec in selected["tracks"]:
            if old[spec["track_id"]].get("bundle"):
                continue
            if control.active():
                raise IngestError("caption_cooldown", "Caption endpoint is resting; audio may continue")
            if stop.is_set() or getattr(args, "youtube_blocked", False):
                raise IngestError("stopped", "Caption fetch stopped before another request")
            caption_bundle(args, row, audio, spec, budget, limiter, stop, state, state_path)
        state["status"] = "pending" if state["unresolved"] or any(not t.get("bundle") for t in state["tracks"]) else (
            "ready" if state["tracks"] else "none")
        state.pop("error_class", None)
        state.pop("error", None)
    except (IngestError, CaptionError) as exc:
        state.update(status="pending", error_class=exc.kind, error=str(exc), updated_at=utc_now())
        if exc.kind in HARD_BLOCKS:
            if not control.active():
                control.block(exc.kind)
            state["source_error_class"] = exc.kind
            state["retry_not_before_epoch"] = control.until
        elif exc.kind == "caption_cooldown":
            state["source_error_class"] = control.reason
            state["retry_not_before_epoch"] = control.until
        print(f"{row['video_id']}: captions: {exc.kind}", file=sys.stderr, flush=True)
    journal(state_path, state)
    return state


def upload_captions(args, items, drive, stop):
    """Exact caption batches use the shared uploader, after completed audio is saved."""
    state_path = args.root / "sync" / "drive_caption_manifest.jsonl"
    owners, paths = [], []
    try:
        for item in items:
            for track in (item.captions or {}).get("tracks", []):
                bundle = track.get("bundle")
                if not bundle or caption_track_verified(track, item.row, args.remote) and track.get("status") == "deleted":
                    continue
                if not valid_recorded_remote(args.remote, item.row, f"captions.{track['track_id']}.zip", bundle["remote"]):
                    raise IngestError("drive_destination", "Caption destination differs from its inventory")
                path = local_path(args.root, bundle["path"])
                relative = remote_relative(args.remote, bundle["remote"])
                if path.relative_to(args.root / "audio").as_posix() != relative:
                    raise IngestError("drive_destination", "Caption local path does not match its exact archive path")
                known = validate_local(path, bundle) if path.exists() else None
                if known is None and track.get("status") != "verified":
                    raise IngestError("local_missing", "Unverified caption bundle is missing")
                owners.append((item, track, path, relative, known))
                paths.append(relative)
        if len(paths) != len(set(paths)):
            raise IngestError("drive_destination", "Caption batch has duplicate object paths")
        proofs = {}
        for offset in range(0, len(owners), 128):
            group = owners[offset:offset + 128]
            upload_paths = [relative for _, _, path, relative, _ in group if path.exists()]
            if upload_paths:
                with batch_manifest(args.root, upload_paths) as manifest:
                    drive.copy_batch(args.root / "audio", args.remote, manifest, getattr(args, "upload_transfers", 2))
            check_paths = [entry[3] for entry in group]
            with batch_manifest(args.root, check_paths) as manifest:
                proofs.update(drive.stat_batch(args.remote, check_paths, manifest))
        for item, track, _, relative, _ in owners:
            proof = proofs.get(relative, {})
            verify_remote(proof, track["bundle"])
            if not proof.get("ID"):
                raise IngestError("drive_verify", "Caption Drive identity is missing; local ZIP retained")
        for item, track, path, relative, known in owners:
            track["bundle"]["drive_id"] = proofs[relative]["ID"]
            track.update(status="verified", verified_at=utc_now())
            journal(state_path, item.captions)
            if path.exists():
                validate_local(path, track["bundle"], known)
                remove_local(path)
            track.update(status="deleted", deleted_at=utc_now())
            journal(state_path, item.captions)
        for item in items:
            if not item.captions:
                continue
            state = item.captions
            if state.get("error_class", "").startswith("drive_"):
                state.pop("error_class", None)
                state.pop("error", None)
            if state.get("tracks") and not state.get("unresolved") and all(
                    caption_track_verified(track, item.row, args.remote) for track in state["tracks"]):
                state["status"] = "deleted"
            journal(state_path, state)
        return True
    except IngestError as exc:
        stop.set()
        for item in items:
            if item.captions:
                item.captions.update(status="pending", error_class=exc.kind, error=str(exc), updated_at=utc_now())
                journal(state_path, item.captions)
        print(f"Caption upload: {exc.kind}; local bundles retained", file=sys.stderr, flush=True)
        return False


def ingest_one(args, row, budget, limiter, stop, drive, state_path, prior=None, *, stage_only=False):
    rec = dict(prior or {}, video_id=row["video_id"], channel_dir=row["channel_dir"],
               entity=row.get("entity", ""), channeling=row.get("channeling", ""), updated_at=utc_now())
    rec.update({key: row.get(key, "") for key in ("title", "url", "tab", "listing_rank", "sources")})
    rec.update({key: row.get(key, "") for key in ("source_channel_name", "primary_person_id", "primary_person_name",
                                                "primary_person_role", "primary_person_basis", "entity_label_basis",
                                                "queue_provenance")})
    reserved, info, captured_at = False, None, None
    trusted, remote_proofs = {}, {}
    collect_metadata = getattr(args, "collect_metadata", True)
    captions = None
    try:
        if (getattr(args, "collect_captions", False) and prior and prior.get("status") == "deleted"
                and prior.get("metadata", {}).get("drive_id")):
            captions = prepare_captions(args, row, rec, budget, limiter, stop)
            has_local = any(track.get("bundle") and track.get("status") != "deleted"
                            for track in captions.get("tracks", []))
            return IngestResult(row, rec, status="ready" if has_local and not args.download_only else "deleted",
                                captions=captions, caption_only=True)
        if prior and prior.get("status") in {"verified", "deleted"} and prior.get("metadata") and drive:
            if stage_only:
                return IngestResult(row, rec, allow_missing=True)
            verify_and_delete(args.root, rec, drive, state_path, require_metadata=True, allow_missing=True)
            return "deleted"
        if prior and prior.get("status") == "download_complete":
            final = local_path(args.root, prior["path"])
            complete_part = final.with_suffix(final.suffix + ".part")
            if not final.exists() and complete_part.exists():
                if any(hash_file(complete_part)[key] != prior.get(key) for key in ("bytes", "md5", "sha256")):
                    raise IngestError("local_changed", "Completed partial differs from its receipt; retained")
                os.replace(complete_part, final)
        remote_only_audio = bool(prior and prior.get("path") and not local_path(args.root, prior["path"]).exists()
                                 and (prior.get("status") in {"deleted", "verified"} or prior.get("audio_on_drive")))
        if remote_only_audio:
            if not drive:
                raise IngestError("drive_read", "Audio-only legacy receipt needs Drive metadata backfill")
            path = local_path(args.root, rec["path"])
            if not valid_recorded_remote(args.remote, row, path.suffix.lstrip("."), rec.get("remote")):
                raise IngestError("drive_destination", "Existing audio belongs to a different Drive destination")
            remote_proofs["audio"] = drive.stat(rec["remote"])
            verify_remote(remote_proofs["audio"], rec)
            rec.update(audio_on_drive=True, status="audio_remote_ready")
            journal(state_path, rec)
        elif prior and prior.get("path") and local_path(args.root, prior["path"]).exists():
            path = local_path(args.root, prior["path"])
            trusted["audio"] = validate_local(path, prior)
            # A complete file surviving a crash is reused only after local checks.
            if prior.get("status") == "download_complete":
                rec.update(status="downloaded")
                journal(state_path, rec)
                journal(args.root / "audio" / "audio_manifest.jsonl",
                        dict(rec, status="ok", path=str(path.relative_to(args.root / "audio")).replace("\\", "/")))
        else:
            if stop.is_set():
                return "stopped"
            limiter.wait()
            if stop.is_set():
                return "stopped"
            info = extract_audio(args, row)
            captured_at = utc_now()
            relative = f"audio/{row['channel_dir']}/{SOURCE_FOLDERS.get(row.get('tab', ''), 'Unclassified')}/{row['video_id']}.{info['ext']}"
            path = local_path(args.root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                raise IngestError("local_changed", "An existing final file has no matching receipt; retained")
            part = path.with_suffix(path.suffix + ".part")
            # An incomplete file has no verified copy and is left intact until
            # this exact item is intentionally retried; reclaim it before reserve.
            if part.exists():
                remove_local(part)
            expected_bytes = int(info["filesize"]) if info.get("filesize") else None
            rec["expected_audio_bytes"] = expected_bytes
            budget.reserve_item(row["video_id"], part, expected_bytes,
                                METADATA_HEADROOM if collect_metadata else 0)
            reserved = True
            published = str(info.get("release_date") or info.get("upload_date") or "")
            if re.fullmatch(r"\d{8}", published):
                published = f"{published[:4]}-{published[4:6]}-{published[6:]}"
            rec.update(status="prepared", path=relative, published=published,
                       duration_s=info.get("duration"), source_ext=info["ext"],
                       source_format_id=info.get("format_id"),
                       youtube_client=getattr(args, "youtube_client", "default"),
                       target="native audio; no re-encode", title=row.get("title", ""))
            journal(state_path, rec)
            measured = stream_audio(info, part, budget, args.rate_bytes, stop, getattr(args, "http_chunk_bytes", 0))
            rec.update(measured, status="download_complete", downloaded_at=utc_now())
            journal(state_path, rec)  # durable hashes before promoting the partial
            os.replace(part, path)
            budget.completed_path(row["video_id"], path)
            trusted["audio"] = fingerprint(path)
            rec.update(status="downloaded")
            journal(state_path, rec)
            journal(args.root / "audio" / "audio_manifest.jsonl",
                    dict(rec, status="ok", path=str(path.relative_to(args.root / "audio")).replace("\\", "/")))
        if args.remote:
            rec["remote"] = item_remote_path(args.remote, row, path.suffix.lstrip("."), rec)
        metadata_path = None
        if collect_metadata:
            metadata_path = ensure_metadata(args, row, rec, budget, limiter, stop, drive,
                                            state_path, info, captured_at, trusted, remote_proofs)
            if args.remote:
                rec["metadata"]["remote"] = item_remote_path(args.remote, row, "info.json", rec)
        if getattr(args, "collect_captions", False):
            captions = prepare_captions(args, row, rec, budget, limiter, stop, info)
        if args.download_only:
            return "downloaded"
        rec["remote"] = item_remote_path(args.remote, row, path.suffix.lstrip("."), rec)
        if stage_only:
            rec.update(status="queued_upload", queued_upload_at=utc_now())
            journal(state_path, rec)
            return IngestResult(row, rec, trusted=trusted, remote_proofs=remote_proofs,
                                allow_missing=remote_only_audio or (collect_metadata and metadata_path is None),
                                captions=captions)
        # copyto --immutable --checksum is idempotent after an interrupted upload.
        if path.exists() and metadata_path:
            drive.copy_pair(path, metadata_path, rec["remote"], rec["metadata"]["remote"])
        elif path.exists():
            drive.copy(path, rec["remote"])
        elif metadata_path:
            drive.copy(metadata_path, rec["metadata"]["remote"])
        verify_and_delete(args.root, rec, drive, state_path, require_metadata=collect_metadata,
                          allow_missing=remote_only_audio or (collect_metadata and metadata_path is None),
                          trusted=trusted, remote_proofs=remote_proofs)
        if captions:
            upload_captions(args, [IngestResult(row, rec, captions=captions)], drive, stop)
        return "deleted"
    except IngestError as exc:
        # Preserve completion evidence alongside an upload failure for restart.
        outcome = {"deferred_storage": "deferred_storage", "live": "deferred_live",
                   "no_formats": "deferred_format", "stopped": "paused"}.get(exc.kind, "error")
        if exc.kind == "unavailable" and not rec.get("sha256") and not rec.get("metadata"):
            outcome = "unavailable"
        rec.update(status=outcome, error_class=exc.kind, error=str(exc), updated_at=utc_now())
        if exc.kind in HARD_BLOCKS:
            rec["source_error_class"] = exc.kind
            rec["retry_not_before_epoch"] = time.time() + 86400
        journal(state_path, rec)
        if exc.kind not in {"unavailable", "login_required", "deferred_storage", "live", "unsupported_format", "no_formats"}:
            stop.set()  # One block or Drive fault stops new work immediately.
        print(f"{row['video_id']}: {exc.kind}: {exc}", file=sys.stderr, flush=True)
        return IngestResult(row, rec, status=outcome) if stage_only else outcome
    finally:
        if reserved:
            budget.release(row["video_id"])


def upload_batch(args, items, drive, state_path, stop):
    """Upload a bounded batch, read each remote object once, then retire safe pairs."""
    results = []
    try:
        uploads, paths = [], []
        artifacts = []
        for item in items:
            rec = item.record
            if item.caption_only:
                continue
            if getattr(args, "collect_metadata", True) and not rec.get("metadata"):
                raise IngestError("metadata_missing", "An upload pair has no research metadata")
            for kind, expected in [("audio", rec)] + ([("metadata", rec["metadata"])] if rec.get("metadata") else []):
                relative = remote_relative(args.remote, expected["remote"])
                if not valid_recorded_remote(args.remote, item.row,
                        Path(rec["path"]).suffix.lstrip("."), rec["remote"]) or (kind == "metadata" and
                        expected["remote"] != rec["remote"].rpartition("/")[0] + f"/{item.row['video_id']}.info.json"):
                    raise IngestError("drive_destination", "An upload receipt belongs to a different destination")
                path = local_path(args.root, expected["path"])
                if path.exists():
                    item.trusted[kind] = validate_local(path, expected, item.trusted.get(kind))
                    uploads.append((path, expected["remote"], relative))
                elif not item.allow_missing:
                    raise IngestError("local_missing", "An upload artifact is missing; pair retained")
                paths.append(relative)
                artifacts.append((item, kind, expected, relative))
        if len(paths) != len(set(paths)):
            raise IngestError("drive_destination", "An upload batch contains duplicate object paths")
        mapped, legacy = [], collections.defaultdict(list)
        for path, destination, relative in uploads:
            if path.relative_to(args.root / "audio").as_posix() == relative:
                mapped.append(relative)
            else:
                legacy[(path.parent, destination.rpartition("/")[0])].append((path, destination))
        if mapped:
            with batch_manifest(args.root, mapped) as manifest:
                drive.copy_batch(args.root / "audio", args.remote, manifest, getattr(args, "upload_transfers", 2))
        for group in legacy.values():
            if len(group) == 2:
                drive.copy_pair(group[0][0], group[1][0], group[0][1], group[1][1])
            else:
                for path, destination in group:
                    drive.copy(path, destination)
        proofs = {}
        if paths:
            with batch_manifest(args.root, paths) as manifest:
                proofs = drive.stat_batch(args.remote, paths, manifest)
        # Check all proof records before deleting even the first local pair.
        for _, _, expected, relative in artifacts:
            if relative not in proofs:
                raise IngestError("drive_verify", "Batch proof omitted an object; local pairs retained")
            verify_remote(proofs[relative], expected)
            if not proofs[relative].get("ID"):
                raise IngestError("drive_verify", "Drive object identity is missing; local pairs retained")
        for item in items:
            if item.caption_only:
                results.append(IngestResult(item.row, item.record, status="deleted", captions=item.captions,
                                            caption_only=True))
                continue
            item_proofs = {kind: proofs[relative] for current, kind, _, relative in artifacts if current is item}
            done = verify_and_delete(args.root, item.record, drive, state_path,
                                     require_metadata=getattr(args, "collect_metadata", True),
                                     allow_missing=item.allow_missing, trusted=item.trusted, remote_proofs=item_proofs)
            results.append(IngestResult(item.row, done, status="deleted", captions=item.captions))
        if any(item.captions for item in items):
            upload_captions(args, items, drive, stop)
        return results
    except IngestError as exc:
        stop.set()
        for item in items:
            # A batch can fail after an earlier pair was already durably retired.
            latest = item.record
            if any(result.row["video_id"] == item.row["video_id"] for result in results):
                continue
            if item.caption_only:
                if item.captions:
                    item.captions.update(status="pending", error_class=exc.kind, error=str(exc))
                    journal(args.root / "sync" / "drive_caption_manifest.jsonl", item.captions)
                results.append(IngestResult(item.row, latest, status="error", captions=item.captions, caption_only=True))
                continue
            latest = dict(latest, status="error", error_class=exc.kind, error=str(exc), updated_at=utc_now())
            journal(state_path, latest)
            results.append(IngestResult(item.row, latest, status="error"))
        print(f"Upload batch: {exc.kind}: {exc}", file=sys.stderr, flush=True)
        return results


def run(args, rows):
    root = args.root
    stop_file = getattr(args, "stop_file", None) or root / "sync" / "STOP_DRIVE_INGEST"
    stop = StopControl(stop_file)
    if stop.requested:
        print(json.dumps({"status": "stopped", "stop_file": str(stop_file),
                          "message": "Remove the stop marker explicitly before resuming"}))
        return 130
    cooldown_path = root / "sync" / "drive_ingest_cooldown.json"
    cooldown = read_drive_cooldown(cooldown_path) if not args.download_only else None
    if cooldown:
        print(json.dumps({"status": "deferred_drive", "until_epoch": cooldown["until_epoch"],
                          "reason": cooldown.get("reason", "drive_rate_limited")}))
        return 75
    root.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(root):
        if tree_bytes(root) > args.max_local_bytes - JOURNAL_RESERVE:
            raise IngestError("storage_limit", "Existing private files leave no storage budget")
        budget = Budget(root, args.max_local_bytes, args.max_item_bytes, args.min_free_bytes, cached=True)
        _ROOT_BUDGETS[root.resolve()] = budget
        state_path = root / "sync" / "drive_ingest_manifest.jsonl"
        state = load_state(state_path)
        args.caption_state = load_state(root / "sync" / "drive_caption_manifest.jsonl")
        args.caption_control = CaptionControl(args.caption_state.values())
        youtube_blocked = any(float(rec.get("retry_not_before_epoch", 0)) > time.time()
                              for rec in state.values())
        args.youtube_blocked = youtube_blocked
        drive = None if args.download_only else Rclone(args.rclone, args.rclone_config, cooldown_path=cooldown_path)
        if drive:
            drive.preflight(args.remote)  # prove connection before any media download
        todo, caption_waiting_rows = [], []
        for row in rows:
            rec = state.get(row["video_id"], {})
            if terminal_unavailable(rec):
                continue
            captions_done = not getattr(args, "collect_captions", False) or caption_receipt_complete(
                args.caption_state.get(row["video_id"], {}), row, args.remote or "")
            if args.download_only and rec.get("status") == "deleted" and rec.get("metadata", {}).get("drive_id") and captions_done:
                continue
            if rec.get("status") in {"deleted", "verified"} and not args.download_only and not valid_recorded_remote(
                    args.remote, row, Path(rec["path"]).suffix.lstrip("."), rec.get("remote")):
                raise IngestError("drive_destination", "Receipt belongs to a different remote; use the original destination")
            if receipt_complete(rec, row, args.remote or "") and captions_done:
                continue
            if receipt_complete(rec, row, args.remote or "") and args.caption_control.active():
                cap = args.caption_state.get(row["video_id"], {})
                has_ready = any(track.get("bundle") and track.get("status") != "deleted"
                                for track in cap.get("tracks", []))
                if not has_ready:
                    caption_waiting_rows.append(row)
                    continue  # do not extract metadata solely for captions during its rest window
            if not getattr(args, "collect_metadata", True) and rec.get("status") == "verified" and not local_path(root, rec["path"]).exists():
                if drive:
                    verify_remote(drive.stat(rec["remote"]), rec)
                journal(state_path, dict(rec, status="deleted", deleted_at=utc_now()))
                continue
            todo.append(row)
        # Drain complete local files first; a Drive outage must never grow a backlog.
        def complete_audio_local(row):
            rec = state.get(row["video_id"], {})
            if not rec.get("path"):
                return False
            path = local_path(root, rec["path"])
            return path.exists() or rec.get("audio_on_drive") or rec.get("status") in {"verified", "deleted"} or (
                rec.get("status") == "download_complete" and path.with_suffix(path.suffix + ".part").exists())

        def complete_local(row):
            rec = state.get(row["video_id"], {})
            return complete_audio_local(row) and (not getattr(args, "collect_metadata", True) or bool(rec.get("metadata")))

        todo.sort(key=lambda row: not complete_local(row))
        def captions_need_source(row):
            if not getattr(args, "collect_captions", False):
                return False
            cap = args.caption_state.get(row["video_id"], {})
            return caption_needs_source(cap)

        cooldown_waiting = youtube_blocked and any(not complete_local(row) or captions_need_source(row) for row in todo)
        if youtube_blocked:
            todo = [row for row in todo if complete_local(row)]
            if cooldown_waiting:
                print("YouTube is in its 24-hour rest period; saving completed local audio only", file=sys.stderr)
        if args.limit:
            todo = todo[:args.limit]
        limiter = RateLimiter(args.min_interval)
        counts, pending, ready = collections.Counter(), {}, collections.deque()
        source = collections.deque(todo)
        active_channels = set()
        deferred_rows, deferred_ids, retried_storage = [], set(), False
        deferred_source_rows, retried_source = [], False
        retried_captions = False
        batch_items = getattr(args, "upload_batch_items", 8)
        batch_seconds = getattr(args, "upload_batch_seconds", 10)
        ready_limit = getattr(args, "ready_items", 16)
        upload_future, uploading, drive_failed, pressure_paused = None, [], False, False
        audio_progress = False
        format_failure_streak = 0

        def observe(row, result):
            nonlocal audio_progress, format_failure_streak
            outcome = result.status if isinstance(result, IngestResult) else result
            if outcome in {"deleted", "downloaded"} and not (
                    isinstance(result, IngestResult) and result.caption_only):
                audio_progress = True
            if outcome in {"ready", "deleted", "downloaded"} and not (
                    isinstance(result, IngestResult) and result.caption_only):
                format_failure_streak = 0
            elif outcome == "deferred_format":
                format_failure_streak += 1
                if format_failure_streak >= 3:
                    stop.set()
                    print("Three format-selection failures without audio progress; pending items retained for tool review",
                          file=sys.stderr, flush=True)
            if isinstance(result, IngestResult):
                state[row["video_id"]] = result.record
                if result.captions:
                    args.caption_state[row["video_id"]] = result.captions
                    if result.captions.get("retry_not_before_epoch", 0) and caption_needs_source(result.captions):
                        caption_waiting_rows.append(row)
            if outcome == "ready":
                ready.append((time.monotonic(), result))
            else:
                counts[outcome] += 1
                if outcome.startswith("deferred_"):
                    deferred_ids.add(row["video_id"])
                    if outcome == "deferred_storage" and not retried_storage:
                        deferred_rows.append(row)
                    elif outcome in {"deferred_live", "deferred_format"} and not retried_source:
                        deferred_source_rows.append(row)
                elif outcome in {"deleted", "downloaded", "unavailable"}:
                    deferred_ids.discard(row["video_id"])
            print(json.dumps({"video_id": row["video_id"], "status": outcome,
                              "completed_this_run": sum(counts.values()), "ready_pairs": len(ready),
                              "uploading_pairs": len(uploading)}), flush=True)

        with cf.ThreadPoolExecutor(max_workers=args.workers) as pool, \
                cf.ThreadPoolExecutor(max_workers=1) as uploader:
            while True:
                pressure = budget.pressure()
                pressure_paused = pressure >= 0.8 if not pressure_paused else pressure > 0.6
                if ready and upload_future is None and not drive_failed and not stop.requested and (
                        len(ready) >= batch_items or time.monotonic() - ready[0][0] >= batch_seconds or
                        not pending or pressure_paused or stop.is_set()):
                    uploading = [ready.popleft()[1] for _ in range(min(batch_items, len(ready)))]
                    upload_future = uploader.submit(upload_batch, args, uploading, drive, state_path, stop)
                while not stop.is_set() and len(pending) < args.workers and (
                        args.download_only or len(pending) + len(ready) + len(uploading) < ready_limit):
                    index = next((i for i, row in enumerate(source) if row["channel_dir"] not in active_channels and
                                  (not pressure_paused or complete_audio_local(row))), None)
                    if index is None:
                        break
                    row = source[index]
                    del source[index]
                    active_channels.add(row["channel_dir"])
                    fut = pool.submit(ingest_one, args, row, budget, limiter, stop, drive,
                                      state_path, state.get(row["video_id"]), stage_only=not args.download_only)
                    pending[fut] = row
                waiting = list(pending) + ([upload_future] if upload_future else [])
                if not waiting:
                    if ready and not drive_failed and not stop.requested:
                        continue
                    if not stop.is_set() and deferred_rows and not retried_storage and (counts["deleted"] or counts["downloaded"]):
                        source.extend(deferred_rows)
                        deferred_rows.clear()
                        retried_storage = True
                        continue
                    if not stop.is_set() and not source and not ready and deferred_source_rows and not retried_source and (
                            audio_progress) and not counts["error"] and not counts["paused"]:
                        # One late revisit after useful stage work, never an immediate polling loop.
                        source.extend(deferred_source_rows)
                        deferred_source_rows.clear()
                        retried_source = True
                        continue
                    if (not stop.is_set() and not source and not ready and caption_waiting_rows and
                            not retried_captions and not args.caption_control.active() and
                            audio_progress and not counts["error"]):
                        # One revisit after useful audio work if the endpoint window elapsed;
                        # a still-active window is scheduled separately, never waited out here.
                        source.extend({row["video_id"]: row for row in caption_waiting_rows}.values())
                        caption_waiting_rows.clear()
                        retried_captions = True
                        continue
                    break
                done, _ = cf.wait(waiting, timeout=0.25, return_when=cf.FIRST_COMPLETED)
                for fut in done:
                    if fut is upload_future:
                        try:
                            results = fut.result()
                        except Exception:
                            stop.set()
                            results = [IngestResult(item.row, item.record, status="error") for item in uploading]
                            print("Upload batch: unexpected failure; local pairs retained", file=sys.stderr)
                        drive_failed = any(result.status == "error" or
                                           (result.captions or {}).get("error_class", "").startswith("drive_")
                                           for result in results)
                        uploading, upload_future = [], None
                        for result in results:
                            observe(result.row, result)
                        continue
                    row = pending.pop(fut)
                    active_channels.discard(row["channel_dir"])
                    try:
                        result = fut.result()
                    except Exception:
                        stop.set()
                        result = "error"
                        print(f"{row['video_id']}: unexpected failure; local files retained", file=sys.stderr)
                    observe(row, result)
        unfinished = len(source) + len(ready)
        source_cooldown = any(float(rec.get("retry_not_before_epoch", 0)) > time.time()
                              for rec in state.values())
        caption_counts = collections.Counter(args.caption_state.get(row["video_id"], {}).get("status", "unknown")
                                             for row in rows) if getattr(args, "collect_captions", False) else {}
        caption_summary = write_caption_backfill_summary(args, state, args.caption_state, args.caption_control) \
            if getattr(args, "collect_captions", False) else {}
        print(json.dumps({"outcomes": counts, "local_bytes": tree_bytes(root),
                          "stopped": stop.is_set(), "youtube_cooldown": source_cooldown,
                          "deferred_items": len(deferred_ids), "pending_items": unfinished,
                          "storage_backpressure": pressure_paused, "captions": caption_counts,
                          "caption_deferred": caption_summary.get("pending_verified_audio_videos", 0),
                          "consecutive_format_failures": format_failure_streak,
                          "caption_retry_not_before_epoch": caption_summary.get("retry_not_before_epoch", 0)}), flush=True)
        if stop.requested:
            return 130
        if not args.download_only and read_drive_cooldown(cooldown_path):
            return 75
        return 3 if counts["error"] or counts["paused"] or cooldown_waiting or deferred_ids or unfinished or drive_failed or source_cooldown else 0


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("plan", "run", "status"))
    add_root_arg(ap)
    ap.add_argument("--queue", type=Path)
    ap.add_argument("--remote", help="rclone remote pointing to existing 04 Audio folder, e.g. etdrive:")
    ap.add_argument("--newest", type=int, default=20)
    ap.add_argument("--entire-queue", action="store_true", help="explicit second phase: every queue row, including Shorts/past streams and legacy rows")
    ap.add_argument("--workers", type=int, choices=range(1, 9), default=4, help="bounded source download workers")
    ap.add_argument("--upload-transfers", type=int, choices=range(1, 5), default=2)
    ap.add_argument("--upload-batch-items", type=int, choices=range(1, 17), default=8)
    ap.add_argument("--upload-batch-seconds", type=float, default=10.0)
    ap.add_argument("--ready-items", type=int, choices=range(1, 65), default=16,
                    help="maximum combined downloading, ready, and uploading pairs")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--download-only", action="store_true", help="bounded local pilot; requires --limit")
    ap.add_argument("--captions", action=argparse.BooleanOptionalAction, dest="collect_captions", default=True,
                    help="collect English published and original automatic captions; excludes translations")
    ap.add_argument("--max-local-gb", type=float, default=17.0)
    ap.add_argument("--max-item-mb", type=float, default=0.0,
                    help="optional explicit item cap; default 0 uses only the overall local-buffer limit")
    ap.add_argument("--min-free-gb", type=float, default=3.0)
    ap.add_argument("--rate-mib", type=float, default=2.0, help="per-worker download rate; default 2 MiB/s")
    ap.add_argument("--http-chunk-mib", type=float, default=1.0,
                    help="bounded HTTP ranges; default 1 MiB, 0 uses one full response")
    ap.add_argument("--min-interval", type=float, default=5.0, help="seconds between metadata request starts")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--ytdlp", default="yt-dlp")
    ap.add_argument("--youtube-client", choices=("default", "mweb"), default="default",
                    help="explicit extraction profile; mweb requires a configured PO-token provider")
    ap.add_argument("--rclone", default="rclone")
    ap.add_argument("--rclone-config", type=Path)
    ap.add_argument("--stop-file", type=Path, help="persistent graceful stop marker (default <root>/sync/STOP_DRIVE_INGEST)")
    ap.set_defaults(collect_metadata=True)
    return ap


def main(argv=None):
    ap = parser()
    args = ap.parse_args(argv)
    args.root = ensure_outside_git(args.root)
    if not 0 < args.max_local_gb <= 20 or args.max_item_mb < 0 or args.min_free_gb < 0:
        ap.error("local cap must be positive and <= 20 GB; optional item cap/free floor cannot be negative")
    if args.rate_mib <= 0 or args.min_interval < 0 or args.limit < 0 or args.http_chunk_mib < 0:
        ap.error("rate must be positive; interval and limit cannot be negative")
    if not 0 <= args.upload_batch_seconds <= 300 or args.upload_batch_items > args.ready_items:
        ap.error("batch wait must be 0..300 seconds and batch items cannot exceed ready-items")
    args.max_local_bytes, args.max_item_bytes = int(args.max_local_gb * 1e9), int(args.max_item_mb * 1e6)
    args.min_free_bytes, args.rate_bytes = int(args.min_free_gb * 1e9), args.rate_mib * 1024 * 1024
    args.http_chunk_bytes = int(args.http_chunk_mib * 1024 * 1024)
    if args.http_chunk_mib and args.http_chunk_bytes < 64 * 1024:
        ap.error("HTTP ranges must be at least 64 KiB when enabled")
    if args.max_item_bytes + JOURNAL_RESERVE > args.max_local_bytes:
        ap.error("per-item reservation plus journal reserve exceeds the local ceiling")
    try:
        if args.command == "status":
            state = load_state(args.root / "sync" / "drive_ingest_manifest.jsonl")
            print(json.dumps({"states": collections.Counter(r.get("status") for r in state.values()),
                              "local_bytes": tree_bytes(args.root), "max_local_bytes": args.max_local_bytes}))
            return 0
        if not args.queue:
            ap.error("plan/run requires --queue")
        rows = select_queue(args.queue, args.newest, args.entire_queue)
        if args.command == "plan":
            print(json.dumps({"videos": len(rows), "channels": len({r["channel_dir"] for r in rows}),
                              "queue_sha256": sha256_file(args.queue), "local_bytes": tree_bytes(args.root),
                              "max_local_bytes": args.max_local_bytes, "native_audio": True,
                              "transcription": False, "remote": args.remote}, indent=2))
            return 0
        if not args.limit and not args.all:
            ap.error("run requires --limit N or --all")
        if args.download_only and (not args.limit or args.all):
            ap.error("download-only is a bounded pilot: use --limit N, without --all")
        if not args.download_only and (not args.remote or not re.match(r"^[A-Za-z0-9_-]+:", args.remote)):
            ap.error("run requires a configured rclone --remote NAME:path")
        youtube_gate("Drive ingestion")
        return run(args, rows)
    except (IngestError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 75 if isinstance(exc, IngestError) and exc.kind in {"drive_rate_limited", "drive_cooldown"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
