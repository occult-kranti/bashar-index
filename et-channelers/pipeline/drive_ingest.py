#!/usr/bin/env python3
"""Bounded native YouTube audio -> Google Drive, without transcoding or ASR.

Use an exclusively owned private --root outside Git. Every byte written by the
streaming downloader is admitted under a shared 20 GB ceiling. A 64 MB reserve
covers journals; existing files, incomplete downloads and active reservations
count too. Other applications writing into the root are outside this guarantee.

The rclone remote should point at the existing archive's ``04 Audio`` folder.
Native .webm/.m4a files go under <channel_dir>/YouTube native/<video_id>.<ext>.
The private audio manifest records those native formats, not 24 kbps Opus.
Successful Drive uploads are checked by remote size AND MD5, journaled with
fsync, and only then removed locally. Upload or verification failures retain
the local file. Restarting reconciles completed downloads before fetching more.

Plan/status never use the network. Run requires --limit N or --all. A bounded
--download-only --limit N pilot is available while Drive OAuth is being set up.
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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (HARD_BLOCKS, ID_RE, RateLimiter, add_root_arg, classify_error,
                    direct_env, ensure_outside_git, read_csv, read_jsonl,
                    sha256_file, utc_now, youtube_gate)

MAX_LOCAL_BYTES = 20_000_000_000  # decimal GB, matching the user's ceiling
JOURNAL_RESERVE = 64 * 1024 * 1024
CHUNK = 1024 * 1024
NATIVE_EXTENSIONS = {"webm", "m4a", "opus", "ogg"}
_JOURNAL_LOCK = threading.Lock()
_ROOT_BUDGETS = {}  # writes to registered run roots also admit journal bytes


class IngestError(RuntimeError):
    """Only safe, nonsensitive messages are carried into the journal/log."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def journal(path, record):
    """Durable append; repair a torn tail without discarding forensic evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    with _JOURNAL_LOCK:
        budget = next((value for root, value in _ROOT_BUDGETS.items()
                       if path.resolve().is_relative_to(root)), None)
        guard = budget.lock if budget else contextlib.nullcontext()
        with guard:
            if budget and tree_bytes(budget.root) + len(encoded) + 1 > budget.cap:
                raise IngestError("storage_limit", "Local storage ceiling leaves no room for a durable receipt")
            _append_durable(path, encoded)


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
    def __init__(self, root, cap, file_cap, min_free, reserve=JOURNAL_RESERVE):
        if not 0 < cap <= MAX_LOCAL_BYTES or file_cap <= 0 or reserve >= cap:
            raise ValueError("invalid storage budget")
        self.root, self.cap, self.file_cap = root, cap, file_cap
        self.min_free, self.reserve = min_free, reserve
        self.lock = threading.RLock()
        self.active = {}

    def reserve_item(self, key, part):
        with self.lock:
            used = tree_bytes(self.root)
            outstanding = sum(max(0, self.file_cap - (p.stat().st_size if p.exists() else 0))
                              for p in self.active.values())
            if used + outstanding + self.file_cap > self.cap - self.reserve:
                raise IngestError("storage_limit", "Local storage budget cannot reserve another item")
            if shutil.disk_usage(self.root).free - outstanding - self.file_cap < self.min_free:
                raise IngestError("disk_floor", "Free disk space is below the reserved safety floor")
            self.active[key] = part

    def release(self, key):
        with self.lock:
            self.active.pop(key, None)

    def write(self, out, data):
        # The check and write share one lock: two workers cannot spend the same bytes.
        with self.lock:
            if out.tell() + len(data) > self.file_cap:
                raise IngestError("item_too_large", "Native audio exceeded the per-item byte limit")
            if tree_bytes(self.root) + len(data) > self.cap - self.reserve:
                raise IngestError("storage_limit", "Local storage ceiling reached")
            if shutil.disk_usage(self.root).free - len(data) < self.min_free:
                raise IngestError("disk_floor", "Free disk space reached the safety floor")
            out.write(data)
            out.flush()  # subsequent workers' file-size checks see these bytes


def select_queue(path, newest=20, entire_queue=False):
    if not entire_queue and not 1 <= newest <= 20:
        raise ValueError("newest must be between 1 and 20")
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


def extract_audio(args, row):
    result = run_tool([args.ytdlp, "--ignore-config", "--proxy", "", "--no-playlist", "--no-warnings", "--no-progress",
                       "--skip-download", "--dump-single-json", "--retries", "0", "--extractor-retries", "0",
                       "--socket-timeout", "30", "--sleep-requests", "0.75", "-f",
                       "bestaudio[protocol=https][vcodec=none]", row["url"]], args.timeout)
    if result.returncode:
        kind = classify_error(result.stderr)
        raise IngestError(kind, "YouTube metadata/audio selection failed; no alternate client or credentials tried")
    try:
        info = json.loads(result.stdout)
    except ValueError as exc:
        raise IngestError("metadata", "yt-dlp did not return valid metadata") from exc
    if info.get("id") != row["video_id"] or info.get("vcodec") != "none":
        raise IngestError("metadata", "Selected media is not the requested audio-only item")
    if info.get("protocol") != "https" or info.get("ext") not in NATIVE_EXTENSIONS:
        raise IngestError("unsupported_format", "No supported native HTTPS audio stream was selected")
    if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
        raise IngestError("live", "Live/upcoming streams are outside the Videos-only queue")
    if info.get("filesize") and int(info["filesize"]) > args.max_item_bytes:
        raise IngestError("item_too_large", "Native audio exceeds the configured per-item byte limit")
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
        raise IngestError("item_too_large", "Selected audio length is outside the per-item byte limit")
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
                    if total > budget.file_cap:
                        raise IngestError("item_too_large", "Server audio length exceeds the per-item byte limit")
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


def remote_path(remote, row, extension):
    return remote.rstrip("/") + ("" if remote.endswith(":") else "/") + \
        f"{row['channel_dir']}/YouTube native/{row['video_id']}.{extension}"


class Rclone:
    RETRY_FLAGS = ["--retries", "2", "--low-level-retries", "2", "--retries-sleep", "5s",
                   "--contimeout", "15s", "--timeout", "60s"]

    def __init__(self, executable, config=None):
        self.command = [executable] + (["--config", str(config)] if config else [])

    def stat(self, remote):
        result = run_tool(self.command + ["lsjson", remote, "--stat", "--hash", *self.RETRY_FLAGS], 300)
        if result.returncode:
            self.failure(result, "metadata read")
        try:
            value = json.loads(result.stdout)
            if not isinstance(value, dict):
                raise ValueError
            return value
        except ValueError as exc:
            raise IngestError("drive_read", "Drive metadata was invalid; local audio retained") from exc

    def preflight(self, remote):
        if not self.stat(remote).get("IsDir"):
            raise IngestError("drive_destination", "Drive destination is not a readable folder")

    def copy(self, path, remote):
        result = run_tool(self.command + ["copyto", str(path), remote, "--checksum", "--immutable",
                          "--transfers", "1", "--checkers", "1", "--buffer-size", "1M",
                          "--drive-chunk-size", "8M", *self.RETRY_FLAGS], 3600)
        if result.returncode:
            self.failure(result, "single-file upload")

    def copy_pair(self, audio, metadata, audio_remote, metadata_remote):
        """One batch, exactly two files, no staging copies or broad folder sync."""
        audio_parent, metadata_parent = audio.parent.resolve(), metadata.parent.resolve()
        remote_parent, _, audio_name = audio_remote.rpartition("/")
        meta_remote_parent, _, metadata_name = metadata_remote.rpartition("/")
        if audio_parent != metadata_parent or remote_parent != meta_remote_parent or not remote_parent:
            raise IngestError("drive_destination", "Audio and metadata must share one upload destination folder")
        if audio.name != audio_name or metadata.name != metadata_name:
            raise IngestError("drive_destination", "Batch destination names differ from the verified local names")
        result = run_tool(self.command + ["copy", str(audio_parent), remote_parent, "--max-depth", "1",
                          "--include", f"/{audio.name}", "--include", f"/{metadata.name}",
                          "--checksum", "--immutable", "--transfers", "2", "--checkers", "2",
                          "--buffer-size", "1M", "--drive-chunk-size", "8M", *self.RETRY_FLAGS], 3600)
        if result.returncode:
            self.failure(result, "audio/metadata batch upload")

    @staticmethod
    def failure(result, operation):
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
        raise IngestError(kind, f"Drive {operation} failed (rclone exit {result.returncode}, {kind}); local artifacts retained")


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
        if kind == "audio":
            verified["drive_id"] = remote.get("ID", "")
        else:
            verified["metadata"] = dict(expected, drive_id=remote.get("ID", ""))
    journal(state_path, verified)  # proof is durable before deletion
    for path, expected, known in checked:
        validate_local(path, expected, known)
    for path, _, _ in checked:
        path.unlink()
    done = dict(verified, status="deleted", deleted_at=utc_now())
    journal(state_path, done)
    return done


def receipt_complete(record, row, remote):
    """Public phase gate: both independently checked objects and the same destination."""
    metadata = record.get("metadata") or {}
    return bool(record.get("status") == "deleted" and record.get("drive_id") and
                record.get("md5") and record.get("sha256") and metadata.get("drive_id") and
                metadata.get("md5") and metadata.get("sha256") and
                record.get("remote") == remote_path(remote, row, Path(record.get("path", "")).suffix.lstrip(".")) and
                metadata.get("remote") == remote_path(remote, row, "info.json"))


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
    audio_destination = remote_path(args.remote, row, Path(rec["path"]).suffix.lstrip(".")) if args.remote else None
    data["archive_audio"] = {key: rec.get(key) for key in ("video_id", "bytes", "md5", "sha256", "drive_id")}
    data["archive_audio"].update(file_name=Path(rec["path"]).name, remote=audio_destination,
                                 encoding="native audio; no re-encode")
    encoded = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    relative = f"audio/{row['channel_dir']}/{row['video_id']}.info.json"
    path = local_path(args.root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise IngestError("local_changed", "Metadata file exists without its receipt; retained")
    part = path.with_suffix(path.suffix + ".part")
    with open(part, "wb") as out:
        for offset in range(0, len(encoded), CHUNK):
            budget.write(out, encoded[offset:offset + CHUNK])
        out.flush()
        os.fsync(out.fileno())
    rec["metadata"] = dict(bytes=len(encoded), md5=hashlib.md5(encoded).hexdigest(),
                           sha256=hashlib.sha256(encoded).hexdigest(), path=relative,
                           remote=remote_path(args.remote, row, "info.json") if args.remote else "")
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


def ingest_one(args, row, budget, limiter, stop, drive, state_path, prior=None):
    rec = dict(prior or {}, video_id=row["video_id"], channel_dir=row["channel_dir"],
               entity=row.get("entity", ""), channeling=row.get("channeling", ""), updated_at=utc_now())
    rec.update({key: row.get(key, "") for key in ("title", "url", "tab", "listing_rank", "sources")})
    rec.update({key: row.get(key, "") for key in ("source_channel_name", "primary_person_id", "primary_person_name",
                                                "primary_person_role", "primary_person_basis", "entity_label_basis",
                                                "queue_provenance")})
    reserved, info, captured_at = False, None, None
    trusted, remote_proofs = {}, {}
    collect_metadata = getattr(args, "collect_metadata", True)
    try:
        if prior and prior.get("status") in {"verified", "deleted"} and prior.get("metadata") and drive:
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
            if rec.get("remote") != remote_path(args.remote, row, path.suffix.lstrip(".")):
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
            relative = f"audio/{row['channel_dir']}/{row['video_id']}.{info['ext']}"
            path = local_path(args.root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                raise IngestError("local_changed", "An existing final file has no matching receipt; retained")
            part = path.with_suffix(path.suffix + ".part")
            # An incomplete file has no verified copy and is left intact until
            # this exact item is intentionally retried; reclaim it before reserve.
            if part.exists():
                part.unlink()
            budget.reserve_item(row["video_id"], part)
            reserved = True
            published = str(info.get("release_date") or info.get("upload_date") or "")
            if re.fullmatch(r"\d{8}", published):
                published = f"{published[:4]}-{published[4:6]}-{published[6:]}"
            rec.update(status="prepared", path=relative, published=published,
                       duration_s=info.get("duration"), source_ext=info["ext"],
                       target="native audio; no re-encode", title=row.get("title", ""))
            journal(state_path, rec)
            measured = stream_audio(info, part, budget, args.rate_bytes, stop, getattr(args, "http_chunk_bytes", 0))
            rec.update(measured, status="download_complete", downloaded_at=utc_now())
            journal(state_path, rec)  # durable hashes before promoting the partial
            os.replace(part, path)
            trusted["audio"] = fingerprint(path)
            rec.update(status="downloaded")
            journal(state_path, rec)
            journal(args.root / "audio" / "audio_manifest.jsonl",
                    dict(rec, status="ok", path=str(path.relative_to(args.root / "audio")).replace("\\", "/")))
        if args.remote:
            rec["remote"] = remote_path(args.remote, row, path.suffix.lstrip("."))
        metadata_path = None
        if collect_metadata:
            metadata_path = ensure_metadata(args, row, rec, budget, limiter, stop, drive,
                                            state_path, info, captured_at, trusted, remote_proofs)
            if args.remote:
                rec["metadata"]["remote"] = remote_path(args.remote, row, "info.json")
        if args.download_only:
            return "downloaded"
        rec["remote"] = remote_path(args.remote, row, path.suffix.lstrip("."))
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
        return "deleted"
    except IngestError as exc:
        # Preserve completion evidence alongside an upload failure for restart.
        rec.update(status="error", error_class=exc.kind, error=str(exc), updated_at=utc_now())
        if exc.kind in HARD_BLOCKS:
            rec["retry_not_before_epoch"] = time.time() + 86400
        journal(state_path, rec)
        if exc.kind not in {"unavailable", "login_required", "item_too_large", "live", "unsupported_format"}:
            stop.set()  # One block or Drive fault stops new work immediately.
        print(f"{row['video_id']}: {exc.kind}: {exc}", file=sys.stderr, flush=True)
        return "error"
    finally:
        if reserved:
            budget.release(row["video_id"])


def run(args, rows):
    root = args.root
    root.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(root):
        if tree_bytes(root) > args.max_local_bytes - JOURNAL_RESERVE:
            raise IngestError("storage_limit", "Existing private files leave no storage budget")
        budget = Budget(root, args.max_local_bytes, args.max_item_bytes, args.min_free_bytes)
        _ROOT_BUDGETS[root.resolve()] = budget
        state_path = root / "sync" / "drive_ingest_manifest.jsonl"
        state = load_state(state_path)
        youtube_blocked = any(float(rec.get("retry_not_before_epoch", 0)) > time.time() for rec in state.values())
        args.youtube_blocked = youtube_blocked
        drive = None if args.download_only else Rclone(args.rclone, args.rclone_config)
        if drive:
            drive.preflight(args.remote)  # prove connection before any media download
        todo = []
        for row in rows:
            rec = state.get(row["video_id"], {})
            if args.download_only and rec.get("status") == "deleted" and rec.get("metadata", {}).get("drive_id"):
                continue
            if rec.get("status") in {"deleted", "verified"} and not args.download_only and rec.get("remote") != remote_path(
                    args.remote, row, Path(rec["path"]).suffix.lstrip(".")):
                raise IngestError("drive_destination", "Receipt belongs to a different remote; use the original destination")
            if receipt_complete(rec, row, args.remote or ""):
                continue
            if not getattr(args, "collect_metadata", True) and rec.get("status") == "verified" and not local_path(root, rec["path"]).exists():
                if drive:
                    verify_remote(drive.stat(rec["remote"]), rec)
                journal(state_path, dict(rec, status="deleted", deleted_at=utc_now()))
                continue
            todo.append(row)
        # Drain complete local files first; a Drive outage must never grow a backlog.
        def complete_local(row):
            rec = state.get(row["video_id"], {})
            if not rec.get("path"):
                return False
            path = local_path(root, rec["path"])
            audio_ready = path.exists() or rec.get("audio_on_drive") or rec.get("status") in {"verified", "deleted"} or (
                rec.get("status") == "download_complete" and path.with_suffix(path.suffix + ".part").exists())
            return audio_ready and (not getattr(args, "collect_metadata", True) or bool(rec.get("metadata")))

        todo.sort(key=lambda row: not complete_local(row))
        cooldown_waiting = youtube_blocked and any(not complete_local(row) for row in todo)
        if youtube_blocked:
            todo = [row for row in todo if complete_local(row)]
            if cooldown_waiting:
                print("YouTube is in its 24-hour rest period; saving completed local audio only", file=sys.stderr)
        if args.limit:
            todo = todo[:args.limit]
        limiter, stop = RateLimiter(args.min_interval), threading.Event()
        counts, pending = collections.Counter(), {}
        source = collections.deque(todo)
        active_channels = set()
        with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
            while True:
                while not stop.is_set() and len(pending) < args.workers:
                    index = next((i for i, row in enumerate(source) if row["channel_dir"] not in active_channels), None)
                    if index is None:
                        break
                    row = source[index]
                    del source[index]
                    active_channels.add(row["channel_dir"])
                    fut = pool.submit(ingest_one, args, row, budget, limiter, stop, drive,
                                      state_path, state.get(row["video_id"]))
                    pending[fut] = row
                if not pending:
                    break
                done, _ = cf.wait(pending, return_when=cf.FIRST_COMPLETED)
                for fut in done:
                    row = pending.pop(fut)
                    active_channels.discard(row["channel_dir"])
                    try:
                        outcome = fut.result()
                    except Exception:
                        stop.set()
                        outcome = "error"
                        print(f"{row['video_id']}: unexpected failure; local files retained", file=sys.stderr)
                    counts[outcome] += 1
                    print(json.dumps({"video_id": row["video_id"], "status": outcome,
                                      "completed_this_run": sum(counts.values())}), flush=True)
        print(json.dumps({"outcomes": counts, "local_bytes": tree_bytes(root),
                          "stopped": stop.is_set(), "youtube_cooldown": cooldown_waiting}), flush=True)
        return 3 if counts["error"] or cooldown_waiting else 0


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("plan", "run", "status"))
    add_root_arg(ap)
    ap.add_argument("--queue", type=Path)
    ap.add_argument("--remote", help="rclone remote pointing to existing 04 Audio folder, e.g. etdrive:")
    ap.add_argument("--newest", type=int, default=20)
    ap.add_argument("--entire-queue", action="store_true", help="explicit second phase: every queue row, including Shorts/past streams and legacy rows")
    ap.add_argument("--workers", type=int, choices=(1, 2, 3, 4), default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--download-only", action="store_true", help="bounded local pilot; requires --limit")
    ap.add_argument("--max-local-gb", type=float, default=19.0)
    ap.add_argument("--max-item-mb", type=float, default=1024.0)
    ap.add_argument("--min-free-gb", type=float, default=3.0)
    ap.add_argument("--rate-mib", type=float, default=2.0, help="per-worker download rate; default 2 MiB/s")
    ap.add_argument("--http-chunk-mib", type=float, default=1.0,
                    help="bounded HTTP ranges; default 1 MiB, 0 uses one full response")
    ap.add_argument("--min-interval", type=float, default=5.0, help="seconds between metadata request starts")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--ytdlp", default="yt-dlp")
    ap.add_argument("--rclone", default="rclone")
    ap.add_argument("--rclone-config", type=Path)
    ap.set_defaults(collect_metadata=True)
    return ap


def main(argv=None):
    ap = parser()
    args = ap.parse_args(argv)
    args.root = ensure_outside_git(args.root)
    if not 0 < args.max_local_gb <= 20 or args.max_item_mb <= 0 or args.min_free_gb < 0:
        ap.error("storage limits must be positive, local cap <= 20 GB, free floor >= 0")
    if args.rate_mib <= 0 or args.min_interval < 0 or args.limit < 0 or args.http_chunk_mib < 0:
        ap.error("rate must be positive; interval and limit cannot be negative")
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
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
