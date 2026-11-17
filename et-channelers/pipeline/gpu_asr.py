"""Explicit, leased CUDA transcription of already verified private audio.

Importing this module starts no jobs, imports no optional GPU packages, and
changes no environment. Source acquisition and release belong to gpu_asr_queue.
The collector must remain parked until a shared storage coordinator exists.
"""
from __future__ import annotations

import argparse
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
import threading
import time
import zipfile

SCHEMA = 1
WORKER_VERSION = "gpu-asr-v1"
MAX_MANAGED_BYTES = 16_000_000_000
MAX_RESULT_BYTES = 20_000_000
SAMPLE_RATE = 16000
WINDOW_SECONDS = 30
FILES = {"segments.json", "transcript.txt", "telemetry.json", "provenance.json", "artifact_manifest.json"}
HERE = Path(__file__).resolve().parent
PROVENANCE_PATH = HERE / "gpu_asr_provenance.json"
DEFAULT_LOCK = HERE / "requirements-gpu-asr-win-py312.lock"
CONFIG = {"language": "en", "task": "transcribe", "beam_size": 5, "best_of": 1,
          "temperature": 0, "condition_on_previous_text": False, "vad_filter": True,
          "vad_parameters": {"min_silence_duration_ms": 500}, "word_timestamps": True}


class AsrError(RuntimeError):
    """Only constant error codes are suitable for console output."""
    def __init__(self, kind):
        self.kind = kind
        super().__init__(kind)


def require(condition, kind):
    if not condition:
        raise AsrError(kind)


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n").encode()


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def hashes(path):
    md5, sha256, size = hashlib.md5(), hashlib.sha256(), 0
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            size += len(block)
            md5.update(block)
            sha256.update(block)
    return {"bytes": size, "md5": md5.hexdigest(), "sha256": sha256.hexdigest()}


def read_json(path):
    path = Path(path)
    require(path.stat().st_size <= MAX_RESULT_BYTES, "oversized_control_document")
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path, value):
    path = Path(path)
    raw = encoded(value)
    require(len(raw) <= MAX_RESULT_BYTES, "result_size")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    with temporary.open("xb") as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


def within(path, root):
    result = Path(path).resolve()
    require(result.is_relative_to(Path(root).resolve()), "path_outside_private_scope")
    return result


def unexpired(value):
    try:
        expires = datetime.fromisoformat(value)
        return expires.tzinfo is not None and expires > datetime.now(timezone.utc)
    except (TypeError, ValueError):
        return False


@contextmanager
def kernel_lock(path):
    """One owner on Windows and POSIX; the persistent lock file is never removed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if os.fstat(handle.fileno()).st_size == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise AsrError("gpu_owner_busy") from None
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@dataclass
class Settings:
    root: Path
    model_dir: Path
    model_receipt: Path
    gpu_lease_id: str
    gpu_owner: str
    managed_roots: list[Path]
    environment_lock: Path = DEFAULT_LOCK
    max_managed_bytes: int = MAX_MANAGED_BYTES
    output_root: Path | None = None

    def __post_init__(self):
        self.root = Path(self.root).resolve()
        from common import ensure_outside_git
        try:
            ensure_outside_git(self.root)
        except SystemExit:
            raise AsrError("private_root_inside_repository") from None
        self.model_dir = Path(self.model_dir).resolve()
        self.model_receipt = within(self.model_receipt, self.root)
        self.environment_lock = Path(self.environment_lock).resolve()
        self.output_root = within(self.output_root or self.root / "asr/results", self.root / "asr/results")
        require(0 < self.max_managed_bytes <= MAX_MANAGED_BYTES, "managed_cap")


def gpu_lease(settings):
    lease = read_json(settings.root / "sync/gpu_lease.json")
    require(lease.get("schema_version") == 1 and lease.get("state") == "active", "gpu_lease_inactive")
    require(lease.get("lease_id") == settings.gpu_lease_id and lease.get("owner") == settings.gpu_owner, "gpu_lease_owner")
    require(lease.get("exclusive_owner") is True and lease.get("device_index") == 0, "gpu_lease_not_exclusive")
    require(lease.get("cpu_fallback_allowed") is False and lease.get("additional_models_allowed") is False, "gpu_lease_policy")
    require(unexpired(lease.get("expires_at")), "gpu_lease_expired")
    require(isinstance(lease.get("max_vram_bytes"), int) and 0 < lease["max_vram_bytes"] <= 6_500_000_000, "vram_policy")
    require(0 < lease.get("rolling_utilization_target", 0) <= 0.70, "gpu_target")
    require(not (settings.root / "asr/STOP_ASR").exists(), "stop_requested")
    return lease


def inventory(settings, extra=3 * MAX_RESULT_BYTES):
    roots = sorted({Path(p).resolve() for p in settings.managed_roots}, key=lambda p: len(p.parts))
    roots = [p for i, p in enumerate(roots) if not any(p.is_relative_to(q) for q in roots[:i])]
    for required in [settings.root, settings.model_dir, Path(sys.prefix).resolve(), HERE.parent.parent]:
        require(any(required.is_relative_to(p) for p in roots), "incomplete_storage_inventory")
    totals = []
    for root in roots:
        require(root.is_dir(), "managed_root_missing")
        total = 0
        for directory, folders, files in os.walk(root, followlinks=False):
            for name in folders + files:
                item = Path(directory) / name
                require(not item.is_symlink() and not bool(getattr(item, "is_junction", lambda: False)()), "unaccounted_storage_link")
            total += sum((Path(directory) / name).stat().st_size for name in files)
        totals.append(total)
    plan = read_json(settings.root / "sync/analysis_resource_plan.json")
    require(plan.get("collector_dispatch_allowed") is False and (settings.root / "sync/STOP_DRIVE_INGEST").is_file(), "collector_not_parked")
    require(0 < plan.get("accounting_cap_bytes", 0) <= MAX_MANAGED_BYTES, "resource_plan_cap")
    # Reserve the full active allocations as additional headroom. This is
    # deliberately conservative while other owners may stage rolling inputs.
    require(all(isinstance(r.get("max_bytes"), int) and r["max_bytes"] >= 0 for r in plan.get("reservations", [])), "resource_reservation")
    headroom = sum(r["max_bytes"] for r in plan.get("reservations", []) if r.get("state") == "active")
    require(sum(totals) + extra + headroom <= min(settings.max_managed_bytes, plan["accounting_cap_bytes"]), "managed_storage_admission")
    return {"managed_bytes": sum(totals), "active_reservation_headroom_bytes": headroom,
            "result_headroom_bytes": extra, "cap_bytes": settings.max_managed_bytes}


def model_proof(settings):
    pinned = read_json(PROVENANCE_PATH)
    require(hashes(settings.environment_lock)["sha256"] == pinned["requirements_lock_sha256"], "environment_lock_hash")
    receipt = read_json(settings.model_receipt)
    expected = pinned["model"]
    require(receipt.get("status") == "model_verified", "model_unverified")
    require(all(receipt.get("source", {}).get(k) == expected[k] for k in ["repository", "revision"]), "model_revision")
    observed = {item["file"]: item for item in receipt.get("files", [])}
    for item in expected["files"]:
        path = within(settings.model_dir / item["file"], settings.model_dir)
        require(item["file"] in observed and all(observed[item["file"]].get(k) == item[k] for k in ["bytes", "sha256"]), "model_receipt_hash")
        proof = hashes(path)
        require(all(proof[k] == item[k] for k in ["bytes", "sha256"]), "model_hash")
    return {"repository": expected["repository"], "revision": expected["revision"],
            "model_sha256": next(f["sha256"] for f in expected["files"] if f["file"] == "model.bin"),
            "manifest_sha256": fingerprint(expected)}


def validate_admission(settings, admission_path):
    path = within(admission_path, settings.root / "asr/jobs")
    admission = read_json(path)
    require(admission.get("schema_version") == 1 and admission.get("state") == "input_verified_waiting_gpu_lease", "input_not_admitted")
    require(re.fullmatch(r"[A-Za-z0-9_-]{11}", admission.get("video_id", "")) is not None, "video_id")
    require(re.fullmatch(r"en(?:-[A-Za-z0-9]+)*", admission.get("language", {}).get("code", "")) is not None and admission["language"].get("basis"), "english_not_proven")
    job = admission["job"]
    require(job.get("video_id") == admission["video_id"] and job.get("job_id") == admission.get("job_id"), "job_identity")
    requested = job.get("requested_output", {})
    require(requested.get("task") == "transcribe" and requested.get("translate") is False, "task_policy")
    require(math.isfinite(float(job.get("duration_seconds", 0))) and float(job["duration_seconds"]) > 0, "duration_unproven")
    lease_path = within(admission["source_lease"], settings.root / "asr/leases")
    lease = read_json(lease_path)
    require(lease.get("status") == "active" and lease.get("phase") in {"input_verified_waiting_gpu_lease", "processing", "awaiting_result_upload"}, "source_lease_inactive")
    require(lease.get("lease_id") == admission.get("source_lease_id") and lease.get("video_id") == admission["video_id"], "source_lease_identity")
    require(unexpired(lease.get("expires_at")), "source_lease_expired")
    objects = {}
    for item in admission.get("verified_input_objects", []):
        kind = item.get("kind")
        require(kind in {"audio", "metadata"} and kind not in objects, "source_object_set")
        file_path = within(item["private_path"], settings.root / "asr/input")
        expected = job[kind]
        require(expected.get("drive_id") and expected.get("remote"), "source_remote_proof")
        require(all(item.get("source", {}).get(k) == expected.get(k) for k in ["drive_id", "remote", "bytes", "md5", "sha256"]), "source_manifest_mismatch")
        local = hashes(file_path)
        require(all(local[k] == expected.get(k) == item.get("local", {}).get(k) for k in ["bytes", "md5", "sha256"]), "source_hash")
        lease_key = "private_path" if kind == "audio" else "metadata_private_path"
        require(Path(lease[lease_key]).resolve() == file_path, "source_lease_path")
        objects[kind] = file_path
    require(set(objects) == {"audio", "metadata"}, "source_object_set")
    require(lease.get("expected_bytes") == job["audio"]["bytes"] and lease.get("sourceDriveID") == job["audio"]["drive_id"], "source_lease_proof")
    require(all(lease.get("expected_hashes", {}).get(k) == job["audio"][k] for k in ["md5", "sha256"]), "source_lease_hash")
    metadata = read_json(objects["metadata"])
    require(metadata.get("source", {}).get("video_id") == admission["video_id"], "metadata_identity")
    language = metadata.get("languages", {}).get("audio") or metadata.get("metadata", {}).get("language")
    require(isinstance(language, str) and re.fullmatch(r"en(?:-[A-Za-z0-9]+)*", language) is not None, "metadata_english_not_proven")
    return admission, objects, hashes(path)["sha256"]


def run_identity(admission, model, environment_hash, worker_hash, config=None):
    identity = {"schema": SCHEMA, "worker_version": WORKER_VERSION, "worker_sha256": worker_hash,
                "model": model, "environment_lock_sha256": environment_hash, "config": config or CONFIG,
                "decode": {"sample_rate": SAMPLE_RATE, "window_seconds": WINDOW_SECONDS, "overlap_seconds": 0},
                "video_id": admission["video_id"], "audio": admission["job"]["audio"],
                "metadata": admission["job"]["metadata"]}
    return "asr-" + fingerprint(identity)[:24], identity


class Monitor:
    def __init__(self, sample, guard, target=70, max_vram=6_500_000_000):
        self.sample, self.lease_guard, self.target, self.max_vram = sample, guard, target, max_vram
        self.window, self.samples = deque(), deque(maxlen=3600)
        self.done, self.ready = threading.Event(), threading.Event()
        self.error = None
        self.count, self.total_gpu, self.peak_gpu, self.peak_vram, self.max_temperature, self.max_rolling = 0, 0, 0, 0, 0, 0

    def begin(self):
        self.start = time.monotonic()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        require(self.ready.wait(5), "telemetry_unavailable")
        self.guard()

    def _loop(self):
        while not self.done.is_set():
            try:
                row = dict(self.sample())
                row["elapsed_s"] = time.monotonic() - self.start
                require(all(math.isfinite(float(row[k])) for k in ["gpu_percent", "vram_bytes", "temperature_c"]), "telemetry_invalid")
                self.window.append(row)
                while self.window and row["elapsed_s"] - self.window[0]["elapsed_s"] > 30:
                    self.window.popleft()
                self.samples.append(row)
                self.count += 1
                self.total_gpu += row["gpu_percent"]
                self.peak_gpu = max(self.peak_gpu, row["gpu_percent"])
                self.peak_vram = max(self.peak_vram, row["vram_bytes"])
                self.max_temperature = max(self.max_temperature, row["temperature_c"])
                self.max_rolling = max(self.max_rolling, self.rolling())
            except Exception:
                self.error = "telemetry_unavailable"
            self.ready.set()
            self.done.wait(1)

    def rolling(self):
        values = list(self.window)
        return statistics.mean(x["gpu_percent"] for x in values) if values else 0

    def guard(self):
        while True:
            self.lease_guard()
            require(not self.error and self.samples, "telemetry_unavailable")
            last = self.samples[-1]
            require(time.monotonic() - self.start - last["elapsed_s"] <= 3, "telemetry_stale")
            require(last["vram_bytes"] <= self.max_vram, "vram_limit")
            require(last["temperature_c"] < 85, "temperature_limit")
            if self.rolling() <= max(1, self.target - 10):
                return
            time.sleep(1)

    def finish(self):
        self.done.set()
        self.thread.join(2)
        return {"sample_count": self.count, "interval_seconds": 1, "rolling_window_seconds": 30,
                "soft_target_percent": self.target, "hard_instantaneous_cap_claimed": False,
                "mean_gpu_percent": self.total_gpu / max(self.count, 1), "peak_gpu_percent": self.peak_gpu,
                "peak_vram_bytes": self.peak_vram, "max_temperature_c": self.max_temperature,
                "max_observed_rolling_mean_percent": self.max_rolling, "samples": list(self.samples),
                "retained_sample_limit": 3600}


class CudaRuntime:
    def __init__(self, settings, lease):
        pinned = read_json(PROVENANCE_PATH)
        self.dependencies = {}
        for package in pinned["packages"]:
            observed = importlib.metadata.version(package["name"])
            require(observed == package["version"], "dependency_version")
            self.dependencies[package["name"]] = observed
        self.dlls = []
        if os.name == "nt":
            for name in ["cublas", "cuda_runtime"]:
                path = Path(sys.prefix) / "Lib/site-packages/nvidia" / name / "bin"
                self.dlls.append(os.add_dll_directory(str(path)))
        import ctranslate2
        import numpy
        import av
        import pynvml
        from faster_whisper import WhisperModel
        require(ctranslate2.get_cuda_device_count() > 0, "cuda_unavailable")
        require("int8_float16" in ctranslate2.get_supported_compute_types("cuda", 0), "cuda_compute_type")
        self.np, self.av, self.nvml = numpy, av, pynvml
        pynvml.nvmlInit()
        self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        self.model = WhisperModel(str(settings.model_dir), device="cuda", device_index=0,
                                  compute_type="int8_float16", cpu_threads=2, num_workers=1, local_files_only=True)
        require(self.model.model.device == "cuda" and self.model.model.compute_type == "int8_float16", "cpu_fallback_forbidden")

    def sample(self):
        return {"gpu_percent": self.nvml.nvmlDeviceGetUtilizationRates(self.handle).gpu,
                "vram_bytes": self.nvml.nvmlDeviceGetMemoryInfo(self.handle).used,
                "temperature_c": self.nvml.nvmlDeviceGetTemperature(self.handle, 0)}

    def windows(self, path, expected_duration):
        """Stream decoded frames; never allocate a full recording PCM array."""
        maximum = int((expected_duration + 2) * SAMPLE_RATE)
        target = WINDOW_SECONDS * SAMPLE_RATE
        buffer = self.np.empty(0, dtype=self.np.float32)
        total = 0
        with self.av.open(str(path)) as container:
            require(len(container.streams.audio) == 1, "audio_stream_count")
            resampler = self.av.AudioResampler(format="fltp", layout="mono", rate=SAMPLE_RATE)
            def decoded():
                for frame in container.decode(audio=0):
                    require(frame.sample_rate > 0 and frame.samples / frame.sample_rate <= WINDOW_SECONDS, "oversized_decode_frame")
                    yield from resampler.resample(frame)
                yield from resampler.resample(None)
            for frame in decoded():
                values = frame.to_ndarray().reshape(-1)
                require(self.np.isfinite(values).all(), "nonfinite_audio")
                require(total + len(buffer) + len(values) <= maximum, "decoded_duration_limit")
                buffer = self.np.concatenate((buffer, values))
                while len(buffer) >= target:
                    yield total / SAMPLE_RATE, buffer[:target]
                    total += target
                    buffer = buffer[target:]
            if len(buffer):
                yield total / SAMPLE_RATE, buffer
                total += len(buffer)
        require(abs(total / SAMPLE_RATE - expected_duration) <= 2, "decoded_duration_mismatch")

    def transcribe(self, audio):
        return self.model.transcribe(audio, **CONFIG)

    def close(self):
        self.model = None
        self.nvml.nvmlShutdown()
        for handle in self.dlls:
            handle.close()


def collect_segments(runtime, path, duration, guard):
    segments, text_parts, offset, decoded_end, vad_seconds = [], [], 0, 0, 0
    for start, audio in runtime.windows(path, duration):
        guard()
        window_duration = len(audio) / SAMPLE_RATE
        require(0 < window_duration <= WINDOW_SECONDS and abs(start - decoded_end) < 0.001, "decode_window_gap")
        iterator, info = runtime.transcribe(audio)
        vad_seconds += info.duration_after_vad
        while True:
            guard()
            try:
                segment = next(iterator)
            except StopIteration:
                break
            require(math.isfinite(segment.start) and math.isfinite(segment.end) and 0 <= segment.start <= segment.end <= window_duration + 0.5, "segment_time")
            value = segment.text.strip()
            if not value:
                continue
            if text_parts:
                offset += 1
            words, word_cursor = [], 0
            for word in segment.words or []:
                require(all(math.isfinite(float(x)) for x in [word.start, word.end, word.probability]), "word_numeric")
                require(0 <= word.start <= word.end <= window_duration + 0.5 and 0 <= word.probability <= 1, "word_time")
                token = word.word.strip()
                at = value.find(token, word_cursor) if token else -1
                require(at >= 0, "word_text_alignment")
                words.append({"start": start + word.start, "end": start + word.end, "word": token,
                              "probability": word.probability, "char_start": offset + at, "char_end": offset + at + len(token)})
                word_cursor = at + len(token)
            item = {"id": len(segments), "start": start + segment.start, "end": start + segment.end,
                    "text": value, "char_start": offset, "char_end": offset + len(value), "words": words,
                    "avg_logprob": segment.avg_logprob, "no_speech_prob": segment.no_speech_prob,
                    "compression_ratio": segment.compression_ratio}
            require(not segments or item["start"] >= segments[-1]["start"], "segment_order")
            segments.append(item)
            text_parts.append(value)
            offset += len(value)
            require(offset <= MAX_RESULT_BYTES // 8, "transcript_size")
        decoded_end = start + window_duration
    require(abs(decoded_end - duration) <= 2 and segments, "no_complete_transcript")
    text = "\n".join(text_parts) + "\n"
    for segment in segments:
        require(text[segment["char_start"]:segment["char_end"]] == segment["text"], "segment_text_alignment")
        for word in segment["words"]:
            require(text[word["char_start"]:word["char_end"]] == word["word"], "word_text_alignment")
    return {"schema_version": SCHEMA, "language": "en", "timebase": "source_audio_seconds",
            "duration_seconds": decoded_end, "segments": segments, "speaker_identity": "unassigned",
            "human_reviewed": False}, text, vad_seconds


def verify_bundle(path, expected=None):
    proof = hashes(path)
    require(0 < proof["bytes"] <= MAX_RESULT_BYTES, "bundle_size")
    if expected:
        require(all(proof[k] == expected.get(k) for k in ["bytes", "md5", "sha256"]), "bundle_hash")
    with zipfile.ZipFile(path) as bundle:
        require(len(bundle.infolist()) == len(FILES) and set(bundle.namelist()) == FILES, "bundle_members")
        require(sum(x.file_size for x in bundle.infolist()) <= MAX_RESULT_BYTES, "bundle_expansion")
        require(bundle.testzip() is None, "bundle_crc")
        manifest = json.loads(bundle.read("artifact_manifest.json"))
        require({x["file"] for x in manifest["files"]} == FILES - {"artifact_manifest.json"} and len(manifest["files"]) == 4, "artifact_manifest_members")
        for item in manifest["files"]:
            data = bundle.read(item["file"])
            require(len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"], "artifact_manifest_hash")
        provenance = json.loads(bundle.read("provenance.json"))
        require(provenance["run_id"] == manifest["run_id"] and provenance["compute"]["cpu_asr_fallback"] is False, "bundle_provenance")
        return {"bundle": proof, "provenance": provenance,
                "artifact_manifest_sha256": hashlib.sha256(bundle.read("artifact_manifest.json")).hexdigest()}


def write_bundle(settings, admission, run_id, segment_data, text, telemetry, provenance):
    directory = settings.output_root / admission["video_id"] / run_id
    directory.mkdir(parents=True, exist_ok=True)
    members = {"segments.json": encoded(segment_data), "transcript.txt": text.encode(),
               "telemetry.json": encoded(telemetry), "provenance.json": encoded(provenance)}
    manifest = {"schema_version": SCHEMA, "run_id": run_id, "files": [
        {"file": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in sorted(members.items())]}
    members["artifact_manifest.json"] = encoded(manifest)
    require(sum(map(len, members.values())) < MAX_RESULT_BYTES // 2, "result_size")
    inventory(settings)
    destination = directory / (run_id + ".zip")
    temporary = destination.with_suffix(".zip.part")
    require(not destination.exists() and not temporary.exists(), "existing_unverified_result")
    with zipfile.ZipFile(temporary, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in members.items():
            bundle.writestr(name, data)
    with temporary.open("r+b") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    verified = verify_bundle(temporary)
    os.replace(temporary, destination)
    receipt = {"schema_version": SCHEMA, "status": "local_transcription_complete_unreviewed", "run_id": run_id,
               "private_root": str(settings.root), "output_root": str(settings.output_root),
               "job_id": admission["job_id"], "video_id": admission["video_id"], "source_lease_id": admission["source_lease_id"],
               "source_audio": admission["job"]["audio"], "source_metadata": admission["job"]["metadata"],
               "model": provenance["model"], "config_sha256": fingerprint(provenance["config"]),
               "bundle": {"path": str(destination), **verified["bundle"]},
               "artifact_manifest_sha256": verified["artifact_manifest_sha256"], "drive_upload": "pending"}
    atomic_json(directory / "receipt.json", receipt)
    return receipt


def publish_result(receipt_path, remote, drive):
    """Publish one verified ZIP. Source inputs are never released here."""
    receipt_path = Path(receipt_path)
    receipt = read_json(receipt_path)
    root = Path(receipt.get("private_root", receipt_path.resolve().parents[4])).resolve()
    require(receipt_path.resolve().is_relative_to(root / "asr/results"), "result_receipt_location")
    require(re.fullmatch(r"asr-[a-f0-9]{24}", receipt.get("run_id", "")) is not None, "result_run_id")
    bundle_path = Path(receipt["bundle"]["path"]).resolve()
    require(bundle_path == receipt_path.resolve().parent / (receipt["run_id"] + ".zip"), "result_bundle_location")
    proof = verify_bundle(receipt["bundle"]["path"], receipt["bundle"])
    provenance = proof["provenance"]
    for key in ["run_id", "source_lease_id", "source_audio", "source_metadata"]:
        require(receipt[key] == provenance[key], "result_source_provenance")
    require(receipt.get("video_id") == provenance.get("source_video_id") and
            receipt.get("job_id") == provenance.get("job_id") and receipt.get("model") == provenance.get("model") and
            receipt.get("config_sha256") == fingerprint(provenance.get("config")) and
            receipt.get("artifact_manifest_sha256") == proof["artifact_manifest_sha256"], "result_identity_provenance")
    parent = receipt["source_audio"]["remote"].rsplit("/", 1)[0]
    expected_remote = f"{parent}/{receipt['video_id']}/ASR/{receipt['run_id']}/{receipt['run_id']}.zip"
    require(remote == expected_remote, "result_remote_path")
    drive.copy(Path(receipt["bundle"]["path"]), remote)
    item = drive.stat(remote)
    remote_hashes = {k.lower(): v for k, v in item.get("Hashes", {}).items()} if isinstance(item, dict) else {}
    require(isinstance(item, dict) and isinstance(item.get("ID"), str) and item["ID"] and item.get("Size") == proof["bundle"]["bytes"] and
            remote_hashes.get("md5", "").lower() == proof["bundle"]["md5"], "result_drive_proof")
    record = {"schema_version": SCHEMA, "status": "verified", "artifact_kind": "asr_bundle", "verified_at": now(),
              "video_id": receipt["video_id"], "channel_dir": provenance["channel_dir"], "run_id": receipt["run_id"],
              "job_id": receipt["job_id"], "source_lease_id": receipt["source_lease_id"], "remote": remote,
              "drive_id": item["ID"], **proof["bundle"], "source_audio_drive_id": receipt["source_audio"]["drive_id"],
              "source_audio_sha256": receipt["source_audio"]["sha256"], "source_metadata": receipt["source_metadata"],
              "model": receipt["model"], "config_sha256": receipt["config_sha256"],
              "artifact_manifest_sha256": receipt["artifact_manifest_sha256"],
              "quality_state": "unreviewed_asr", "metrics": provenance["metrics"]}
    with kernel_lock(root / "sync/asr_manifest_append.lock"):
        journal = root / "sync/asr_manifest.jsonl"
        with journal.open("ab") as output:
            output.write(encoded(record))
            output.flush()
            os.fsync(output.fileno())
        receipt["drive_upload"] = "verified"
        receipt["remote_proof"] = record
        atomic_json(receipt_path, receipt)
    return record


def run_jobs(settings, admission_paths, runtime_factory=CudaRuntime):
    runtime = None
    results = []
    with kernel_lock(settings.root / "sync/asr_gpu_owner.lock"):
        lease = gpu_lease(settings)
        inventory(settings)
        model = model_proof(settings)
        worker_hash = hashes(Path(__file__))["sha256"]
        environment_hash = hashes(settings.environment_lock)["sha256"]
        old_env = {k: os.environ.get(k) for k in ["HF_HUB_OFFLINE", "HF_HUB_DISABLE_IMPLICIT_TOKEN", "TRANSFORMERS_OFFLINE", "HF_HOME", "TEMP", "TMP", "OMP_NUM_THREADS"]}
        temporary = settings.root / "asr/tmp"
        temporary.mkdir(parents=True, exist_ok=True)
        os.environ.update(HF_HUB_OFFLINE="1", HF_HUB_DISABLE_IMPLICIT_TOKEN="1", TRANSFORMERS_OFFLINE="1",
                          HF_HOME=str(settings.root / "asr/cache"), TEMP=str(temporary), TMP=str(temporary), OMP_NUM_THREADS="2")
        try:
            for path in admission_paths:
                gpu_lease(settings)
                admission, objects, admission_hash = validate_admission(settings, path)
                desired = admission["job"]["desired_model"]
                require(all(desired.get(k) == model[k] for k in ["repository", "revision"]) and desired.get("device") == "cuda", "job_model_mismatch")
                run_id, identity = run_identity(admission, model, environment_hash, worker_hash)
                receipt_path = settings.output_root / admission["video_id"] / run_id / "receipt.json"
                if receipt_path.exists():
                    receipt = read_json(receipt_path)
                    verified = verify_bundle(receipt["bundle"]["path"], receipt["bundle"])
                    require(verified["provenance"].get("identity") == identity, "existing_result_version")
                    results.append(receipt)
                    continue
                inventory(settings)
                from gpu_asr_queue import claim_input
                source_lease = read_json(admission["source_lease"])
                if source_lease.get("phase") == "input_verified_waiting_gpu_lease":
                    claim_input(settings.root, admission, settings.gpu_owner)
                else:
                    require(source_lease.get("consumer_owner") == settings.gpu_owner, "source_consumer_owner")
                if runtime is None:
                    runtime = runtime_factory(settings, lease)
                require(runtime.model.model.device == "cuda" and runtime.model.model.compute_type == "int8_float16", "cpu_fallback_forbidden")
                def guard():
                    gpu_lease(settings)
                    source = read_json(admission["source_lease"])
                    require(source.get("status") == "active" and source.get("lease_id") == admission["source_lease_id"] and unexpired(source.get("expires_at")), "source_lease_lost")
                monitor = Monitor(runtime.sample, guard, lease["rolling_utilization_target"] * 100, lease["max_vram_bytes"])
                monitor.begin()
                started, begin = now(), time.monotonic()
                try:
                    segments, text, vad_seconds = collect_segments(runtime, objects["audio"], float(admission["job"]["duration_seconds"]), monitor.guard)
                    monitor.guard()
                finally:
                    telemetry = monitor.finish()
                # Detect any changed source bytes before sealing the result.
                validate_admission(settings, path)
                provenance = {"schema_version": SCHEMA, "status": "local_transcription_complete_unreviewed", "run_id": run_id,
                              "job_id": admission["job_id"], "source_video_id": admission["video_id"],
                              "channel_dir": admission["job"]["source"]["channel_dir"], "source_lease_id": admission["source_lease_id"],
                              "source_audio": admission["job"]["audio"], "source_metadata": admission["job"]["metadata"],
                              "source_admission_sha256": admission_hash, "language_evidence": admission["language"],
                              "caption_alternative_state": admission["job"]["caption"]["state"], "model": model,
                              "identity": identity, "config": CONFIG, "started_at": started, "finished_at": now(),
                              "dependencies": runtime.dependencies, "environment_lock_sha256": environment_hash, "worker_sha256": worker_hash,
                              "compute": {"device": "cuda:0", "compute_type": "int8_float16", "model_workers": 1,
                                          "batch_size": 1, "cpu_asr_fallback": False, "gpu_lease_id": settings.gpu_lease_id,
                                          "host_preprocessing": "PyAV decode, feature preparation, bundled ONNX VAD"},
                              "metrics": {"audio_seconds": segments["duration_seconds"], "duration_after_vad_seconds": vad_seconds,
                                          "inference_decode_pacing_seconds": time.monotonic() - begin, "segment_count": len(segments["segments"])},
                              "quality": {"accuracy_claimed": False, "human_reviewed": False, "word_times_are_model_estimates": True,
                                          "speech_coverage_validated": False, "host_guest_identity_assigned": False,
                                          "window_boundary_effects_unvalidated": True}, "source_retention": "until_verified_result_and_provenance_on_drive"}
                results.append(write_bundle(settings, admission, run_id, segments, text, telemetry, provenance))
        finally:
            if runtime is not None:
                runtime.close()
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    return results


def parser():
    command = argparse.ArgumentParser(description=__doc__)
    modes = command.add_subparsers(dest="mode", required=True)
    run = modes.add_parser("run", help="explicitly execute admitted private CUDA jobs")
    run.add_argument("--root", type=Path, required=True)
    run.add_argument("--model-dir", type=Path, required=True)
    run.add_argument("--model-receipt", type=Path, required=True)
    run.add_argument("--gpu-lease-id", required=True)
    run.add_argument("--gpu-owner", required=True)
    run.add_argument("--managed-root", type=Path, action="append", required=True)
    run.add_argument("--environment-lock", type=Path, default=DEFAULT_LOCK)
    run.add_argument("--max-managed-gb", type=float, default=16)
    run.add_argument("--output-root", type=Path)
    inputs = run.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--admission", type=Path, action="append")
    inputs.add_argument("--ready", type=Path)
    verify = modes.add_parser("verify", help="verify a local result ZIP without GPU imports")
    verify.add_argument("bundle", type=Path)
    return command


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.mode == "verify":
            proof = verify_bundle(args.bundle)
            print(json.dumps({"status": "verified_local_bundle", **proof["bundle"]}))
            return 0
        settings = Settings(args.root, args.model_dir, args.model_receipt, args.gpu_lease_id, args.gpu_owner,
                            args.managed_root, args.environment_lock, int(args.max_managed_gb * 1_000_000_000), args.output_root)
        paths = args.admission or read_json(within(args.ready, settings.root / "asr/jobs"))["admissions"]
        require(0 < len(paths) <= 3, "rolling_input_limit")
        results = run_jobs(settings, paths)
        print(json.dumps({"status": "local_complete_unreviewed", "jobs": len(results), "run_ids": [r["run_id"] for r in results], "uploaded": False}))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "pending", "error_class": exc.kind if isinstance(exc, AsrError) else "worker_error"}))
        return 3


if __name__ == "__main__":
    # -I removes the script directory; only the explicit CLI enables sibling helpers.
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    raise SystemExit(main())
