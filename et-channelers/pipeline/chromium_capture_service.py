"""Loopback spool for explicitly activated Chrome tab audio; no YouTube requests.

Browser recordings are a distinct, re-encoded artifact. A content-clock coverage
claim alone never completes a recording: its decoded duration and non-silence
must also pass, and Drive identity/hash proofs precede owned-spool deletion.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ID_RE, ensure_outside_git, utc_now
from drive_ingest import (Rclone, IngestError, hash_file, journal, receipt_complete,
                          select_queue, tree_bytes, verify_remote)
from gpu_asr import kernel_lock

EXTENSION_ID = "egndajoiodmfaakhopchlaikhpdjdcnb"
ORIGIN = "chrome-extension://" + EXTENSION_ID
MAX_BODY = 1_048_576
MAX_CONTROL = 262_144
MANAGED_CAP = 16_000_000_000
SPOOL_CAP = 5_000_000_000
OTHER_GROWTH_RESERVE = 3_000_000_000
DISK_FLOOR = 2_000_000_000
CONTROL_RESERVE = 2_000_000
TAB_NAMES = {"videos": "Videos", "shorts": "Shorts", "streams": "Recorded streams", "": "Unclassified"}
CAPTURE_RE = re.compile(r"capture-[a-f0-9]{32}\Z")
WORKER_RE = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")


class CaptureError(Exception):
    def __init__(self, code, status=409):
        self.code, self.status = code, status
        super().__init__(code)


def require(ok, code, status=409):
    if not ok:
        raise CaptureError(code, status)


def finite(value, low=0):
    return type(value) in (int, float) and math.isfinite(value) and value >= low


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def atomic(path, value):
    raw = encoded(value)
    require(len(raw) <= MAX_CONTROL, "control_document_too_large", 413)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix + ".part")
    with part.open("wb") as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    os.replace(part, path)


def records(path):
    result = []
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    result.append(row)
            except ValueError:
                pass
    return result


def browser_receipt_complete(record, row, remote):
    capture_id = record.get("capture_id", "")
    if not isinstance(capture_id, str) or not CAPTURE_RE.fullmatch(capture_id):
        return False
    parent = f"{remote}/{row.get('channel_dir')}/{TAB_NAMES.get(row.get('tab'))}/{row.get('video_id')}/Browser capture/{capture_id}"
    for key, name in (("audio", "audio.webm"), ("metadata", "capture.info.json")):
        proof = record.get(key)
        if not isinstance(proof, dict) or proof.get("remote") != parent + "/" + name or not proof.get("drive_id"):
            return False
        if type(proof.get("bytes")) is not int or proof["bytes"] <= 0 or not re.fullmatch(r"[a-f0-9]{32}", str(proof.get("md5", ""))) or not re.fullmatch(r"[a-f0-9]{64}", str(proof.get("sha256", ""))):
            return False
    if record["audio"]["drive_id"] == record["metadata"]["drive_id"]:
        return False
    return (record.get("status") == "verified" and record.get("artifact_kind") == "browser_recorded_audio" and
            record.get("video_id") == row.get("video_id") and record.get("channel_dir") == row.get("channel_dir") and
            record.get("reencoded") is True and record.get("coverage_state") == "complete_content_clock_and_decoded_duration")


def source_metadata(value):
    """Published text only: never accept arbitrary transport/cookie objects."""
    require(isinstance(value, dict), "invalid_source_metadata", 400)
    result = {}
    for key, limit in {"title": 2000, "description": 100000, "channel_id": 100,
                       "channel_name": 1000, "author": 1000, "upload_date": 80,
                       "publish_date": 80, "language": 80}.items():
        if isinstance(value.get(key), str):
            result[key] = value[key][:limit]
    for key in ("keywords", "categories"):
        if isinstance(value.get(key), list):
            result[key] = [item[:200] for item in value[key][:200] if isinstance(item, str)]
    if type(value.get("view_count")) is int and value["view_count"] >= 0:
        result["view_count"] = value["view_count"]
    return result


def validate_coverage(value, expected):
    require(value.get("source_ended") is True and value.get("ads_detected") is False and
            value.get("playback_rate") == 1, "incomplete_or_modified_playback")
    duration, current = value.get("source_duration"), value.get("source_time")
    require(finite(duration, .1) and finite(current) and abs(duration - expected) <= max(2, expected * .001) and
            abs(current - duration) <= 1.5, "content_clock_end_mismatch")
    intervals = value.get("coverage_intervals")
    require(isinstance(intervals, list) and 0 < len(intervals) <= 50000, "missing_clock_coverage")
    edge = 0.0
    for interval in intervals:
        require(isinstance(interval, list) and len(interval) == 2 and
                all(finite(x) for x in interval), "invalid_clock_interval")
        start, end = interval
        require(start <= end <= duration + 1 and start <= edge + .75 and start >= edge - 1,
                "clock_gap_or_overlap")
        edge = max(edge, end)
    require(intervals[0][0] <= .75 and edge >= duration - 1.5, "incomplete_clock_coverage")
    return duration


def coverage_claim(value):
    return {key: value[key] for key in ("capture_id", "video_id", "source_ended", "source_duration",
            "source_time", "ads_detected", "playback_rate", "coverage_intervals") if key in value}


def inspect_audio(path, duration, ffprobe, ffmpeg):
    try:
        result = subprocess.run([ffprobe, "-v", "error", "-show_entries",
            "format=duration:stream=codec_type,codec_name,duration", "-of", "json", str(path)],
            capture_output=True, timeout=60, check=True)
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        require(len(streams) == 1 and streams[0].get("codec_type") == "audio" and
                streams[0].get("codec_name") == "opus", "unexpected_recorded_stream")
        declared = data.get("format", {}).get("duration") or streams[0].get("duration")
        # Decode the whole recording, not just its first audio packet.
        decoded = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-v", "info", "-i", str(path),
            "-vn", "-af", "aresample=16000,aformat=channel_layouts=mono,volumedetect", "-f", "null", "-"], capture_output=True,
            timeout=max(120, int(duration / 3) + 60), check=True)
        match = re.search(rb"mean_volume:\s*(-?[0-9.]+) dB", decoded.stderr)
        samples = re.findall(rb"n_samples:\s*(\d+)", decoded.stderr)
        require(bool(samples), "decoded_sample_count_missing")
        measured = int(samples[-1]) / 16000
        require(finite(measured, .1) and abs(measured - duration) <= max(2, duration * .002),
                "decoded_duration_mismatch")
        if declared and declared != "N/A":
            require(abs(float(declared) - measured) <= max(2, duration * .002), "container_duration_mismatch")
        require(match is not None and float(match[1]) > -65, "silent_or_unmeasured_recording")
        return {"decoded_duration_seconds": measured, "mean_volume_db": float(match[1]),
                "codec": "opus", "container": "webm", "full_decode_passed": True}
    except (OSError, ValueError, subprocess.SubprocessError):
        raise CaptureError("audio_validation_failed") from None


class Store:
    def __init__(self, root, queue, managed_roots, *, requested=None, remote="etdrive:04 Audio",
                 ffprobe="ffprobe", ffmpeg="ffmpeg", drive=None, spool_cap=SPOOL_CAP):
        self.root = Path(root).resolve()
        ensure_outside_git(self.root)
        require(0 < spool_cap <= SPOOL_CAP, "invalid_spool_cap")
        self.spool = self.root / "browser_capture"
        self.spool.mkdir(parents=True, exist_ok=True)
        require(self.spool.resolve().is_relative_to(self.root) and not self.spool.is_symlink(), "unsafe_spool")
        self.remote, self.ffprobe, self.ffmpeg, self.drive = remote, ffprobe, ffmpeg, drive
        self.spool_cap = spool_cap
        self.resource_phase()
        roots = sorted({Path(p).resolve() for p in [self.root, *managed_roots]}, key=lambda p: len(p.parts))
        self.roots = [p for i, p in enumerate(roots) if not any(p.is_relative_to(q) for q in roots[:i])]
        for required in (Path(sys.prefix).resolve(), Path(__file__).resolve().parents[2]):
            require(any(required.is_relative_to(p) for p in self.roots), "managed_roots_incomplete")
        self.lock, self.token = threading.RLock(), secrets.token_urlsafe(32)
        rows = select_queue(queue, newest=20)
        if requested and Path(requested).exists():
            rows = select_queue(requested, entire_queue=True) + rows
        self.rows = {}
        for row in rows:
            self.rows.setdefault(row["video_id"], row)
        self.jobs = {}
        for file in self.spool.glob("capture-*/state.json"):
            require(file.resolve().is_relative_to(self.spool), "unsafe_job_path")
            state = json.loads(file.read_text(encoding="utf-8"))
            capture_id = state.get("capture_id", "")
            require(CAPTURE_RE.fullmatch(capture_id or "") and file.parent.name == capture_id, "invalid_job_state")
            if state.get("state") in {"leased", "recording", "validating"}:
                state.update(state="held", error="service_restarted_incomplete")
                atomic(file, state)
            elif state.get("state") == "uploading":
                state.update(state="ready_for_upload", error="upload_interrupted_reconcile_exact_bytes")
                atomic(file, state)
            self.jobs[capture_id] = state
        self.reconcile_verified()
        self.reconciled = 0
        self.outside_bytes = 0
        self.refresh_budget()
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="capture-upload")
        self.validators = ThreadPoolExecutor(max_workers=2, thread_name_prefix="capture-validate")
        self.uploading = set()

    def resource_phase(self):
        require(not (self.spool / "STOP_CAPTURE").exists(), "capture_stop_requested")
        require((self.root / "sync/STOP_DRIVE_INGEST").read_text(encoding="utf-8").strip() ==
                "Codex resource phase: isolated ASR provisioning and bounded SABR investigation",
                "collector_resource_phase_required")
        resource_plan = json.loads((self.root / "sync/analysis_resource_plan.json").read_text(encoding="utf-8"))
        require(resource_plan.get("collector_dispatch_allowed") is False and
                resource_plan.get("browser_capture_dispatch_allowed") is True and
                resource_plan.get("accounting_cap_bytes") == MANAGED_CAP and
                any(r.get("lease_id") == "browser-capture-v1" and r.get("state") == "active" and
                    r.get("max_bytes") == SPOOL_CAP for r in resource_plan.get("reservations", [])),
                "capture_resource_reservation_required")

    def path(self, capture_id, name="state.json"):
        require(isinstance(capture_id, str) and CAPTURE_RE.fullmatch(capture_id), "invalid_capture_id", 400)
        path = self.spool / capture_id / name
        require(path.resolve().is_relative_to(self.spool), "unsafe_job_path")
        return path

    def save(self, job):
        atomic(self.path(job["capture_id"]), job)

    def reconcile_verified(self):
        """Recover a crash between durable remote proof and either local unlink."""
        proven = {r.get("capture_id"): r for r in records(self.root / "sync/browser_capture_manifest.jsonl")}
        for capture_id, job in self.jobs.items():
            receipt = proven.get(capture_id, {})
            if not browser_receipt_complete(receipt, job["source"], self.remote):
                continue
            found = []
            for key, name in (("audio", "audio.webm"), ("metadata", "capture.info.json")):
                path = self.path(capture_id, name)
                if path.exists():
                    expected = {k: receipt[key][k] for k in ("bytes", "md5", "sha256")}
                    require(hash_file(path) == expected, "verified_cleanup_local_changed")
                    found.append(path)
            for path in found:
                path.unlink()
            job.update(state="verified", receipt=receipt, reserved_bytes=0, local_deleted_at=utc_now())
            self.save(job)

    def refresh_budget(self):
        self.outside_bytes = sum(tree_bytes(path) for path in self.roots) - tree_bytes(self.spool)
        self.reconciled = time.monotonic()

    def budget(self, extra=0, reserve=0):
        self.resource_phase()
        if time.monotonic() - self.reconciled >= 12:
            self.refresh_budget()
        used = tree_bytes(self.spool)
        outstanding = sum(max(0, j.get("reserved_bytes", 0) - j.get("bytes", 0)) for j in self.jobs.values()
                          if j.get("state") in {"leased", "recording"})
        require(used + outstanding + reserve + extra + CONTROL_RESERVE <= self.spool_cap, "spool_backpressure", 507)
        require(self.outside_bytes + used + outstanding + reserve + extra + OTHER_GROWTH_RESERVE <= MANAGED_CAP,
                "managed_storage_backpressure", 507)
        require(shutil.disk_usage(self.root).free - outstanding - reserve - extra >= DISK_FLOOR,
                "disk_buffer_backpressure", 507)

    def completed(self):
        done = set()
        for rec in records(self.root / "sync/drive_ingest_manifest.jsonl"):
            row = self.rows.get(rec.get("video_id"))
            if row and receipt_complete(rec, row, self.remote):
                done.add(row["video_id"])
        for rec in records(self.root / "sync/browser_capture_manifest.jsonl"):
            row = self.rows.get(rec.get("video_id"))
            if row and browser_receipt_complete(rec, row, self.remote):
                done.add(row["video_id"])
        return done

    def next(self, value):
        worker = value.get("worker_id", "")
        require(isinstance(worker, str) and WORKER_RE.fullmatch(worker), "invalid_worker_id", 400)
        active = [j for j in self.jobs.values() if j["state"] in {"leased", "recording", "validating", "ready_for_upload", "uploading"}]
        same = next((j for j in active if j["worker_id"] == worker and j["state"] in {"leased", "recording"}), None)
        if same:
            return {"job": self.public_job(same)}
        require(sum(j["state"] in {"leased", "recording", "validating"} for j in active) < 4, "four_workers_active")
        done = self.completed() | {j["video_id"] for j in active}
        preferred = value.get("video_id")
        if preferred is not None:
            require(isinstance(preferred, str) and ID_RE.fullmatch(preferred), "invalid_video_id", 400)
        row = self.rows.get(preferred) if preferred else next((r for v, r in self.rows.items() if v not in done), None)
        if row is None or row["video_id"] in done:
            return {"job": None}
        self.budget(reserve=2_000_000)
        capture_id = "capture-" + secrets.token_hex(16)
        job = {"schema_version": 1, "capture_id": capture_id, "video_id": row["video_id"],
               "worker_id": worker, "state": "leased", "source": row, "created_at": utc_now(),
               "sequence": 0, "bytes": 0, "reserved_bytes": 2_000_000}
        self.jobs[capture_id] = job
        self.save(job)
        return {"job": self.public_job(job)}

    @staticmethod
    def public_job(job):
        raw = job["source"].get("duration_s")
        try:
            duration = float(raw)
        except (TypeError, ValueError):
            duration = None
        return {"capture_id": job["capture_id"], "video_id": job["video_id"],
                "watch_url": f"https://www.youtube.com/watch?v={job['video_id']}",
                "duration_seconds": duration if finite(duration, .1) else None}

    def get_job(self, value, states):
        capture_id = value.get("capture_id")
        self.path(capture_id)
        job = self.jobs.get(capture_id)
        require(job is not None and job["state"] in states, "capture_state_conflict")
        return job

    def start(self, value):
        job = self.get_job(value, {"leased"})
        require(value.get("video_id") == job["video_id"] and value.get("ads_detected") is False and
                value.get("is_live") is False and value.get("playback_rate") == 1 and
                finite(value.get("source_time")) and value["source_time"] <= .75, "invalid_source_start")
        duration = value.get("duration_seconds")
        require(finite(duration, .1), "unknown_source_duration")
        # Estimate is a reservation, never a duration exclusion; larger recordings
        # wait for sufficient spool space and remain in the queue.
        reserved = math.ceil(duration * 15000) + 2_000_000
        metadata = source_metadata(value.get("source_metadata", {}))
        old = job["reserved_bytes"]
        job["reserved_bytes"] = 0
        try:
            self.budget(reserve=reserved)
            job.update(state="recording", reserved_bytes=reserved, duration_seconds=duration,
                       source_metadata=metadata, started_at=utc_now())
            self.path(job["capture_id"], "audio.webm.part").touch(exist_ok=False)
            self.save(job)
        except BaseException:
            job.update(state="leased", reserved_bytes=old)
            part = self.path(job["capture_id"], "audio.webm.part")
            if part.is_file() and part.stat().st_size == 0:
                part.unlink()
            raise
        return {"accepted": True}

    def chunk(self, capture_id, sequence, payload):
        job = self.get_job({"capture_id": capture_id}, {"recording"})
        require(type(sequence) is int and sequence == job["sequence"], "chunk_sequence_conflict")
        require(0 < len(payload) <= MAX_BODY, "invalid_chunk_size", 413)
        extra = max(0, job["bytes"] + len(payload) - job["reserved_bytes"])
        self.budget(extra=extra)
        with self.path(capture_id, "audio.webm.part").open("ab") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        job["bytes"] += len(payload)
        job["reserved_bytes"] = max(job["reserved_bytes"], job["bytes"])
        job["sequence"] += 1
        self.save(job)
        return {"accepted": True, "sequence": sequence}

    def prepare_finish(self, value):
        job = self.get_job(value, {"recording"})
        require(value.get("video_id") == job["video_id"] and job["bytes"] > 0, "source_finish_identity")
        validate_coverage(value, job["duration_seconds"])
        job.update(state="validating", finish_claim=coverage_claim(value), reserved_bytes=0)
        self.save(job)
        return job

    def finish(self, value):
        with self.lock:
            job = self.prepare_finish(value)
        self.validators.submit(self.validate, job)
        return {"accepted": True, "state": "validating"}

    def status(self, value):
        self.path(value.get("capture_id"))
        job = self.jobs.get(value["capture_id"])
        require(job is not None, "capture_not_found", 404)
        state = job["state"]
        return {"state": "ready_for_upload" if state in {"ready_for_upload", "uploading", "verified"} else
                "held" if state in {"held", "upload_held"} else state}

    def validate(self, job):
        try:
            audio = self.path(job["capture_id"], "audio.webm.part")
            evidence = inspect_audio(audio, job["duration_seconds"], self.ffprobe, self.ffmpeg)
            final = self.path(job["capture_id"], "audio.webm")
            os.replace(audio, final)
            metadata = {"schema_version": 1, "artifact_kind": "browser_recorded_audio", "reencoded": True,
                        "video_id": job["video_id"], "source": job["source"],
                        "source_metadata": job["source_metadata"], "capture_id": job["capture_id"],
                        "source_watch_url": f"https://www.youtube.com/watch?v={job['video_id']}",
                        "capture_method": "user_activated_chrome_tabCapture_mediaRecorder",
                        "capture_extension_id": EXTENSION_ID, "target_audio_bits_per_second": 96000,
                        "coverage_state": "complete_content_clock_and_decoded_duration", "accuracy_state": "unreviewed",
                        "content_clock_claim": job["finish_claim"], "audio_validation": evidence,
                        "native_waveform_preserved": False, "created_at": utc_now()}
            atomic(self.path(job["capture_id"], "capture.info.json"), metadata)
            with self.lock:
                job.update(state="ready_for_upload", audio=hash_file(final),
                           metadata=hash_file(self.path(job["capture_id"], "capture.info.json")),
                           audio_validation=evidence, finished_at=utc_now())
                self.save(job)
            self.schedule_upload()
        except Exception as error:
            with self.lock:
                job.update(state="held", error=error.code if isinstance(error, CaptureError) else "validation_failed")
                self.save(job)

    def abort(self, value):
        job = self.get_job(value, {"leased", "recording"})
        reason = value.get("reason")
        reason = reason if isinstance(reason, str) and re.fullmatch(r"[a-z0-9_]{1,80}", reason) else "unclassified_browser_stop"
        job.update(state="held", reserved_bytes=0, error="browser_aborted_incomplete", abort_reason=reason,
                   stopped_at=utc_now())
        self.save(job)
        return {"accepted": True}

    def schedule_upload(self):
        if self.drive is None:
            return
        with self.lock:
            for job in self.jobs.values():
                if job["state"] == "ready_for_upload" and job["capture_id"] not in self.uploading:
                    self.uploading.add(job["capture_id"])
                    self.executor.submit(self.upload, job)

    def upload(self, job):
        try:
            with self.lock:
                job["state"] = "uploading"
                self.save(job)
            row, capture_id = job["source"], job["capture_id"]
            parent = f"{self.remote}/{row['channel_dir']}/{TAB_NAMES[row['tab']]}/{row['video_id']}/Browser capture/{capture_id}"
            audio, metadata = self.path(capture_id, "audio.webm"), self.path(capture_id, "capture.info.json")
            require(hash_file(audio) == job["audio"] and hash_file(metadata) == job["metadata"], "local_artifact_changed")
            self.drive.copy_pair(audio, metadata, parent + "/audio.webm", parent + "/capture.info.json")
            proofs = {}
            for key, path in (("audio", audio), ("metadata", metadata)):
                remote = parent + "/" + path.name
                entry = self.drive.stat(remote)
                verify_remote(entry, job[key])
                require(bool(entry.get("ID")), "drive_identity_missing")
                proofs[key] = dict(job[key], remote=remote, drive_id=entry["ID"])
            receipt = {"schema_version": 1, "artifact_kind": "browser_recorded_audio", "reencoded": True,
                       "video_id": row["video_id"], "channel_dir": row["channel_dir"], "tab": row["tab"], "capture_id": capture_id,
                       "status": "verified", "coverage_state": "complete_content_clock_and_decoded_duration",
                       "verified_at": utc_now(), **proofs}
            require(browser_receipt_complete(receipt, row, self.remote), "receipt_contract_failed")
            with self.lock:
                journal(self.root / "sync/browser_capture_manifest.jsonl", receipt)
                require(hash_file(audio) == job["audio"] and hash_file(metadata) == job["metadata"], "local_artifact_changed")
                audio.unlink()
                metadata.unlink()
                job.update(state="verified", receipt=receipt, local_deleted_at=utc_now())
                self.save(job)
        except (CaptureError, IngestError, OSError) as error:
            with self.lock:
                job.update(state="upload_held", error=getattr(error, "code", getattr(error, "kind", "upload_io_error")))
                self.save(job)
        finally:
            with self.lock:
                self.uploading.discard(job["capture_id"])

    def health(self):
        with self.lock:
            return {"schema_version": 1, "service": "channeling-browser-capture", "version": 1,
                    "active_workers": sum(j["state"] in {"leased", "recording", "validating"} for j in self.jobs.values()),
                    "queued_items": len(self.rows), "upload_enabled": self.drive is not None,
                    "spool_cap_bytes": self.spool_cap, "managed_cap_bytes": MANAGED_CAP,
                    "artifact_kind": "browser_recorded_audio", "reencoded": True}


class Handler(BaseHTTPRequestHandler):
    server_version = "ChannelingCapture/1"

    def log_message(self, *_):
        pass  # no headers, tokens, video text, or transport errors on the console

    def authorized_origin(self):
        require(self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}", "invalid_host", 403)
        require(self.headers.get("Origin") == ORIGIN, "invalid_origin", 403)

    def respond(self, status, value):
        raw = encoded(value)
        self.send_response(status)
        if self.headers.get("Origin") == ORIGIN:
            self.send_header("Access-Control-Allow-Origin", ORIGIN)
        self.send_header("Vary", "Origin")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        try:
            self.authorized_origin()
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", ORIGIN)
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Capture-Id, X-Sequence")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.send_header("Vary", "Origin")
            self.send_header("Content-Length", "0")
            self.end_headers()
        except CaptureError as error:
            self.respond(error.status, {"error": error.code})

    def do_GET(self):
        if self.path == "/capture/v1/health" and self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}":
            self.respond(200, self.server.store.health())
        else:
            self.respond(404, {"error": "not_found"})

    def do_POST(self):
        try:
            self.authorized_origin()
            store = self.server.store
            if self.path != "/capture/v1/pair":
                require(secrets.compare_digest(self.headers.get("Authorization", ""), "Bearer " + store.token),
                        "unauthorized", 401)
            require(not self.headers.get("Transfer-Encoding"), "transfer_encoding_rejected", 400)
            length = int(self.headers.get("Content-Length", "-1"))
            is_chunk = self.path == "/capture/v1/chunk"
            require(0 <= length <= (MAX_BODY if is_chunk else MAX_CONTROL), "invalid_body_size", 413)
            self.connection.settimeout(15)
            raw = self.rfile.read(length)
            require(len(raw) == length, "incomplete_body", 400)
            if is_chunk:
                with store.lock:
                    result = store.chunk(self.headers.get("X-Capture-Id"), int(self.headers.get("X-Sequence", "-1")), raw)
            else:
                value = json.loads(raw or b"{}")
                require(isinstance(value, dict), "invalid_json_object", 400)
                if self.path == "/capture/v1/pair":
                    result = {"token": store.token}
                elif self.path == "/capture/v1/finish":
                    result = store.finish(value)
                else:
                    method = {"/capture/v1/next": store.next, "/capture/v1/start": store.start,
                              "/capture/v1/abort": store.abort, "/capture/v1/status": store.status}.get(self.path)
                    require(method is not None, "not_found", 404)
                    with store.lock:
                        result = method(value)
            self.respond(200, result)
        except CaptureError as error:
            self.respond(error.status, {"error": error.code})
        except (ValueError, TypeError, UnicodeError):
            self.respond(400, {"error": "invalid_request"})
        except (OSError, IngestError):
            self.respond(503, {"error": "local_service_io_error"})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--requested", type=Path)
    parser.add_argument("--managed-root", type=Path, action="append", required=True)
    parser.add_argument("--ffprobe", required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--rclone")
    parser.add_argument("--remote", default="etdrive:04 Audio")
    parser.add_argument("--port", type=int, default=8768)
    args = parser.parse_args(argv)
    require(1024 <= args.port <= 65535, "invalid_port")
    drive = Rclone(args.rclone, cooldown_path=args.root / "sync/drive_cooldown.json") if args.rclone else None
    with kernel_lock(args.root / "sync/browser_capture_service.lock"):
        store = Store(args.root, args.queue, args.managed_root, requested=args.requested,
                      remote=args.remote, ffprobe=args.ffprobe, ffmpeg=args.ffmpeg, drive=drive)
        store.schedule_upload()
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
        server.store = store
        print(json.dumps({"state": "listening", "url": f"http://127.0.0.1:{args.port}/capture/v1/health"}), flush=True)
        try:
            server.serve_forever()
        finally:
            server.server_close()
            store.validators.shutdown(wait=True)
            store.executor.shutdown(wait=True)


if __name__ == "__main__":
    try:
        main()
    except (CaptureError, IngestError) as error:
        print(json.dumps({"error": getattr(error, "code", getattr(error, "kind", "service_error"))}))
        raise SystemExit(2)
