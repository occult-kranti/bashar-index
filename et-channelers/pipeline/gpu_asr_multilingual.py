"""Explicit leased original-language ASR plus a separately typed English view.

No GPU, network, source acquisition, or deletion occurs at import. The English
worker and its five-member ZIP contract remain unchanged. Ambiguous speech is
held, never converted into a guessed English transcript.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
import zipfile

HERE = Path(__file__).resolve().parent
if __name__ == "__main__" and str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
try:
    from . import gpu_asr as base
except ImportError:
    import gpu_asr as base

Settings = base.Settings
AsrError = base.AsrError
require = base.require
PINNED = HERE / "gpu_asr_multilingual_provenance.json"
CONTRACT = "original-and-english-v1"
PROFILE = "multilingual_original_and_english_translation"
SCHEMA = 1
MIN_PROBABILITY = .90
MIN_MARGIN = .20
MIN_SPEECH_SECONDS = 2.0
CORE_MEMBERS = {"original/segments.json", "original/transcript.txt", "provenance.json", "telemetry.json", "artifact_manifest.json"}
TRANSLATION_MEMBERS = {"english/segments.json", "english/transcript.txt"}
METADATA_HOLD_FLAGS = {"claimed_light_language", "explicit_nonverbal_label", "instrumental_label", "toning_or_chant_label"}


def language_code(value):
    return str(value or "und").lower().split("-")[0]


def model_proof(settings):
    pinned, receipt = base.read_json(PINNED), base.read_json(settings.model_receipt)
    require(base.hashes(settings.environment_lock)["sha256"] == pinned["requirements_lock_sha256"], "environment_lock_hash")
    expected = pinned["model"]
    require(receipt.get("status") == "model_verified" and all(receipt.get("source", {}).get(k) == expected[k] for k in ["repository", "revision"]), "multilingual_model_revision")
    observed = {x["file"]: x for x in receipt.get("files", [])}
    for item in expected["files"]:
        require(all(observed.get(item["file"], {}).get(k) == item[k] for k in ["bytes", "sha256"]), "model_receipt_hash")
        proof = base.hashes(base.within(settings.model_dir / item["file"], settings.model_dir))
        require(all(proof[k] == item[k] for k in ["bytes", "sha256"]), "model_hash")
    return {"repository": expected["repository"], "revision": expected["revision"], "model_sha256": next(x["sha256"] for x in expected["files"] if x["file"] == "model.bin"), "manifest_sha256": base.fingerprint(expected)}


def frame_proof(settings, proposal_path, model):
    lease = base.gpu_lease(settings)
    path = base.within(proposal_path, settings.root / "asr/jobs")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(lease.get("input_frame_sha256") == digest, "gpu_frame_mismatch")
    require(all(lease.get("model", {}).get(k) == model[k] for k in ["repository", "revision", "model_sha256"]), "gpu_model_mismatch")
    proposal = json.loads(raw)
    require(proposal.get("schema_version") == 1 and proposal.get("frame_id") == "multilingual-v1", "proposal_schema")
    jobs = {}
    for job in proposal.get("jobs", []):
        video = job.get("video_id", "")
        require(re.fullmatch(r"[A-Za-z0-9_-]{11}", video) is not None and video not in jobs, "proposal_identity")
        require(re.fullmatch(r"[A-Za-z0-9_-]{1,160}", job.get("proposal_job_id", "")) is not None, "proposal_job_id")
        require(job.get("profile") == PROFILE and all(job.get("desired_model", {}).get(k) == model[k] for k in ["repository", "revision"]), "proposal_model")
        jobs[video] = job
    require(len(jobs) == 5, "proposal_size")
    return digest, jobs


def validate_admission(settings, path, frame_hash, jobs):
    path = base.within(path, settings.root / "asr/jobs")
    admission = base.read_json(path)
    require(admission.get("schema_version") == 1 and admission.get("state") == "input_verified_waiting_gpu_lease", "input_not_admitted")
    require(admission.get("proposal_sha256") == frame_hash, "admission_frame")
    expected = jobs.get(admission.get("video_id"))
    require(expected is not None, "outside_proposal")
    job = admission["job"]
    require(job.get("profile") == PROFILE and job.get("job_id") == admission.get("job_id") == expected["proposal_job_id"], "job_identity")
    require(job.get("video_id") == expected["video_id"], "video_identity")
    for kind in ["audio", "metadata"]:
        require(all(job.get(kind, {}).get(k) == expected[kind][k] for k in ["remote", "drive_id", "bytes", "md5", "sha256"]), "source_proposal_mismatch")
    require(math.isfinite(float(job.get("duration_seconds", 0))) and float(job["duration_seconds"]) == float(expected["duration_seconds"]) > 0, "duration_proof")
    require(job.get("metadata_content_flags") == expected["metadata_content_flags"], "metadata_flags_mismatch")
    require(all(job.get("desired_model", {}).get(k) == expected["desired_model"][k] for k in ["repository", "revision", "device"]), "job_model_mismatch")
    source = base.read_json(base.within(admission["source_lease"], settings.root / "asr/leases"))
    require(source.get("status") == "active" and source.get("phase") in {"input_verified_waiting_gpu_lease", "processing", "awaiting_result_upload", "held_language_review"}, "source_lease_inactive")
    require(source.get("frame_id") == "multilingual-v1" and source.get("lease_id") == admission.get("source_lease_id") and source.get("video_id") == expected["video_id"], "source_lease_identity")
    require(source["lease_id"] != expected.get("source_lease", {}).get("superseded_english_hold_lease_id"), "new_source_lease_required")
    require(base.unexpired(source.get("expires_at")), "source_lease_expired")
    require(source.get("sourceDriveID") == job["audio"]["drive_id"] and source.get("expected_bytes") == job["audio"]["bytes"], "source_lease_proof")
    require(all(source.get("expected_hashes", {}).get(k) == job["audio"][k] for k in ["md5", "sha256"]), "source_lease_hash")
    objects = {}
    for item in admission.get("verified_input_objects", []):
        kind = item.get("kind")
        require(kind in {"audio", "metadata"} and kind not in objects, "source_object_set")
        target = base.within(item["private_path"], settings.root / "asr/input" / expected["video_id"])
        require(target == Path(source["private_path" if kind == "audio" else "metadata_private_path"]).resolve(), "source_lease_path")
        require(all(item.get("source", {}).get(k) == job[kind][k] for k in ["remote", "drive_id", "bytes", "md5", "sha256"]), "source_manifest_mismatch")
        actual = base.hashes(target)
        require(all(actual[k] == job[kind][k] == item.get("local", {}).get(k) for k in ["bytes", "md5", "sha256"]), "source_hash")
        objects[kind] = target
    require(set(objects) == {"audio", "metadata"}, "source_object_set")
    metadata = base.read_json(objects["metadata"])
    declared = metadata.get("languages", {}).get("audio") or metadata.get("metadata", {}).get("language") or "und"
    require(metadata.get("source", {}).get("video_id") == expected["video_id"] and language_code(declared) == language_code(expected["declared_audio_language"]), "metadata_language_identity")
    return admission, objects, expected


class Runtime(base.CudaRuntime):
    """Same isolated CUDA dependencies; fresh telemetry and no CPU ASR path."""
    def sample(self):
        self.handle = self.nvml.nvmlDeviceGetHandleByIndex(0)
        return {**super().sample(), "backend": "pynvml"}

    def fallback_sample(self):
        executable = shutil.which("nvidia-smi")
        require(executable is not None, "telemetry_unavailable")
        result = subprocess.run([executable, "--id=0", "--query-gpu=utilization.gpu,memory.used,temperature.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5, check=False)
        require(result.returncode == 0 and len(result.stdout.strip().splitlines()) == 1, "telemetry_unavailable")
        values = [int(v.strip()) for v in result.stdout.strip().split(",")]
        require(len(values) == 3, "telemetry_invalid")
        return {"gpu_percent": values[0], "vram_bytes": values[1] * 1024 * 1024, "temperature_c": values[2], "backend": "nvidia-smi-nvml"}

    def speech(self, audio):
        from faster_whisper.vad import VadOptions, get_speech_timestamps
        spans = get_speech_timestamps(audio, VadOptions(min_silence_duration_ms=500))
        chunks = [audio[x["start"]:x["end"]] for x in spans]
        speech = self.np.concatenate(chunks) if chunks else self.np.empty(0, dtype=self.np.float32)
        return speech, len(speech) / base.SAMPLE_RATE

    def detect(self, audio):
        return self.model.detect_language(audio=audio, vad_filter=False, language_detection_segments=1, language_detection_threshold=MIN_PROBABILITY)


class Monitor:
    def __init__(self, runtime, lease_guard, target=70, max_vram=6_500_000_000, *, rolling_history=None, soft_temperature=None):
        self.runtime, self.lease_guard, self.target, self.max_vram = runtime, lease_guard, target, max_vram
        # At or above this many degrees the next step waits, well before the hard stop at 85.
        self.soft_temperature = soft_temperature
        self.rolling_history = rolling_history
        self.samples, self.window = deque(maxlen=3600), deque()
        self.lock, self.done, self.ready = threading.RLock(), threading.Event(), threading.Event()
        self.error, self.last_error, self.errors, self.fallbacks = None, None, 0, 0
        self.count, self.total, self.peak_gpu, self.peak_vram, self.peak_temp, self.peak_rolling, self.max_gap = 0, 0, 0, 0, 0, 0, 0

    def add(self, row):
        row = dict(row)
        require(all(math.isfinite(float(row[k])) for k in ["gpu_percent", "vram_bytes", "temperature_c"]), "telemetry_invalid")
        require(0 <= row["gpu_percent"] <= 100 and row["vram_bytes"] >= 0 and 0 < row["temperature_c"] < 120, "telemetry_invalid")
        current = time.monotonic()
        row["elapsed_s"] = current - self.start
        with self.lock:
            if self.samples:
                self.max_gap = max(self.max_gap, row["elapsed_s"] - self.samples[-1]["elapsed_s"])
            self.samples.append(row)
            self.window.append(row)
            while self.window and row["elapsed_s"] - self.window[0]["elapsed_s"] > 30:
                self.window.popleft()
            if self.rolling_history is not None:
                self.rolling_history.append((current, row["gpu_percent"]))
                while current - self.rolling_history[0][0] > 30:
                    self.rolling_history.popleft()
            self.count += 1
            self.total += row["gpu_percent"]
            self.peak_gpu = max(self.peak_gpu, row["gpu_percent"])
            self.peak_vram = max(self.peak_vram, row["vram_bytes"])
            self.peak_temp = max(self.peak_temp, row["temperature_c"])
            self.peak_rolling = max(self.peak_rolling, self.rolling_mean())
            self.error = None
        self.ready.set()

    def rolling_mean(self):
        if self.rolling_history is not None:
            return statistics.mean(percent for _, percent in self.rolling_history)
        return statistics.mean(x["gpu_percent"] for x in self.window)

    def loop(self):
        while not self.done.is_set():
            try:
                self.add(self.runtime.sample())
            except Exception as exc:
                with self.lock:
                    self.error = type(exc).__name__
                    self.last_error = {"type": self.error, "nvml_value": getattr(exc, "value", None)}
                    self.errors += 1
                self.ready.set()
            self.done.wait(1)

    def begin(self):
        self.start = time.monotonic()
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()
        self.ready.wait(3)
        self.guard()

    def guard(self):
        deadline = time.monotonic() + 10
        while True:
            self.lease_guard()
            with self.lock:
                last = self.samples[-1] if self.samples else None
                stale = last is None or time.monotonic() - self.start - last["elapsed_s"] > 3
                failed = self.error and (last is None or last.get("backend") != "nvidia-smi-nvml")
            if stale or failed:
                try:
                    self.add(self.runtime.fallback_sample())
                    self.fallbacks += 1
                except Exception:
                    require(time.monotonic() < deadline, "telemetry_unavailable")
                    time.sleep(1)
                    continue
            with self.lock:
                last = self.samples[-1]
                require(last["vram_bytes"] <= self.max_vram, "vram_limit")
                require(last["temperature_c"] < 85, "temperature_limit")
                average = self.rolling_mean()
                warm = self.soft_temperature is not None and last["temperature_c"] >= self.soft_temperature
            if average <= max(1, self.target - 10) and not warm:
                return
            time.sleep(1)

    def finish(self):
        self.done.set()
        self.thread.join(2)
        with self.lock:
            return {"sample_count": self.count, "interval_seconds": 1, "rolling_window_seconds": 30, "soft_target_percent": self.target, "hard_instantaneous_cap_claimed": False, "mean_gpu_percent": self.total / max(1, self.count), "peak_gpu_percent": self.peak_gpu, "peak_vram_bytes": self.peak_vram, "max_temperature_c": self.peak_temp, "max_observed_rolling_mean_percent": self.peak_rolling, "sampling_gap_max_seconds": self.max_gap, "telemetry_error_count": self.errors, "last_telemetry_error": self.last_error, "fallback_samples": self.fallbacks, "retained_sample_limit": 3600, "samples": list(self.samples)}


def decide_language(job, probes):
    if any(job.get("metadata_content_flags", {}).get(k) for k in METADATA_HOLD_FLAGS):
        return {"status": "held", "reason": "metadata_nonlexical_review", "metadata_flags_are_not_interval_classification": True}
    if sum(p["speech_seconds"] for p in probes) < MIN_SPEECH_SECONDS:
        return {"status": "held", "reason": "no_reliable_speech"}
    strong = [p for p in probes if p["speech_seconds"] >= MIN_SPEECH_SECONDS and p["probability"] >= MIN_PROBABILITY and p["margin"] >= MIN_MARGIN]
    declared = language_code(job["declared_audio_language"])
    languages = {p["language"] for p in strong}
    if len(languages) > 1:
        return {"status": "held", "reason": "mixed_or_conflicting_language"}
    if declared not in {"und", "mul", "zxx"}:
        if languages and languages != {declared}:
            return {"status": "held", "reason": "metadata_detection_conflict"}
        if not strong:
            return {"status": "held", "reason": "language_confidence_insufficient"}
        chosen = declared
    else:
        required = 1 if float(job["duration_seconds"]) <= 30 else 2
        if len(strong) < required:
            return {"status": "held", "reason": "language_confidence_insufficient"}
        chosen = strong[0]["language"]
    require(re.fullmatch(r"[a-z]{2,3}", chosen) is not None and chosen not in {"und", "mul", "zxx"}, "detected_language_invalid")
    return {"status": "accepted", "language": chosen, "basis": "metadata_and_model_agreement" if declared not in {"und", "mul", "zxx"} else "model_agreement_across_speech_probes", "minimum_probability": MIN_PROBABILITY, "minimum_margin": MIN_MARGIN, "strong_probe_count": len(strong), "english_view": "original_alias" if chosen == "en" else "machine_translation", "human_confirmed": False}


def detect_language(runtime, path, job, guard):
    duration = float(job["duration_seconds"])
    count = max(1, math.ceil(duration / base.WINDOW_SECONDS))
    selected = {0, count // 2, count - 1}
    probes = []
    for index, (start, audio) in enumerate(runtime.windows(path, duration)):
        guard()
        if index not in selected:
            continue
        speech, seconds = runtime.speech(audio)
        row = {"start": start, "duration_seconds": len(audio) / base.SAMPLE_RATE, "speech_seconds": seconds, "language": None, "probability": 0, "margin": 0}
        if seconds >= MIN_SPEECH_SECONDS:
            guard()
            language, probability, all_probs = runtime.detect(speech)
            others = [float(prob) for lang, prob in all_probs if lang != language]
            row.update(language=language, probability=float(probability), margin=float(probability) - max(others, default=0))
            require(all(math.isfinite(row[k]) for k in ["probability", "margin"]) and 0 <= row["probability"] <= 1, "language_probability_invalid")
        probes.append(row)
    return {**decide_language(job, probes), "probes": probes, "probes_do_not_prove_full_recording_language_or_meaning": True}


class TaskRuntime:
    def __init__(self, runtime, config):
        self.runtime, self.config = runtime, config

    def windows(self, path, duration):
        return self.runtime.windows(path, duration)

    def transcribe(self, audio):
        return self.runtime.model.transcribe(audio, **self.config)


def validate_text(segments, text, language, duration):
    require(isinstance(text, str) and text.strip() and any(c.isalnum() for c in text), "variant_empty_text")
    require(segments.get("language") == language and segments.get("timebase") == "source_audio_seconds", "variant_language_timebase")
    require(segments.get("character_offset_unit") == "unicode_code_points" and segments.get("human_reviewed") is False, "variant_schema")
    require(abs(float(segments["duration_seconds"]) - duration) <= 2 and segments.get("segments"), "variant_duration")
    previous = -1
    for segment in segments["segments"]:
        require(all(math.isfinite(float(segment[k])) for k in ["start", "end"]) and 0 <= segment["start"] <= segment["end"] <= duration + .5 and segment["start"] >= previous, "variant_timestamp")
        previous = segment["start"]
        start, end = segment.get("char_start"), segment.get("char_end")
        require(type(start) is int and type(end) is int and 0 <= start < end <= len(text) and text[start:end] == segment.get("text") and segment["text"].strip(), "variant_text_offsets")
        for word in segment.get("words", []):
            require(type(word.get("char_start")) is int and type(word.get("char_end")) is int and start <= word["char_start"] < word["char_end"] <= end and text[word["char_start"]:word["char_end"]] == word.get("word"), "variant_word_offsets")
            require(all(math.isfinite(float(word[k])) for k in ["start", "end", "probability"]) and 0 <= word["start"] <= word["end"] <= duration + .5 and 0 <= word["probability"] <= 1, "variant_word_timestamp")


def verify_pair(path, expected=None, *, max_bytes=None):
    limit=base.MAX_RESULT_BYTES if max_bytes is None else max_bytes
    require(type(limit) is int and 0 < limit <= 256_000_000, "paired_size_budget")
    proof = base.hashes(path)
    require(0 < proof["bytes"] <= limit, "bundle_size")
    if expected:
        require(all(proof[k] == expected.get(k) for k in ["bytes", "md5", "sha256"]), "bundle_hash")
    with zipfile.ZipFile(path) as archive:
        require(all(not item.is_dir() and ((item.external_attr >> 16) & 0o170000) != 0o120000 for item in archive.infolist()), "bundle_link_or_directory")
        require(sum(x.file_size for x in archive.infolist()) <= limit and archive.testzip() is None, "bundle_crc_or_expansion")
        provenance = json.loads(archive.read("provenance.json"))
        require(provenance.get("output_contract") == CONTRACT and provenance.get("quality_state") == "unreviewed_asr" and provenance.get("compute", {}).get("cpu_asr_fallback") is False, "paired_contract")
        variants = provenance.get("text_variants", {})
        require(set(variants) == {"original", "english"}, "paired_variants")
        original, english = variants["original"], variants["english"]
        language = original.get("language")
        require(re.fullmatch(r"[a-z]{2,3}", language or "") is not None and language not in {"und", "mul", "zxx"}, "original_language")
        require(original.get("text_kind") == "original_asr" and original.get("config", {}).get("task") == "transcribe" and original["config"].get("language") == language, "original_config")
        alias = english.get("same_as") == "original"
        if alias:
            require(language == "en" and english.get("language") == "en" and english.get("text_kind") == "original_english_alias" and english.get("translation_performed") is False, "invalid_english_alias")
        else:
            require(english.get("language") == "en" and english.get("text_kind") == "english_audio_translation" and english.get("config", {}).get("task") == "translate" and english["config"].get("language") == language, "translation_config")
        members = CORE_MEMBERS | (set() if alias else TRANSLATION_MEMBERS)
        require(len(archive.infolist()) == len(members) and set(archive.namelist()) == members, "paired_member_set")
        manifest_bytes = archive.read("artifact_manifest.json")
        manifest = json.loads(manifest_bytes)
        require(manifest.get("run_id") == provenance.get("run_id") and re.fullmatch(r"asr-[a-f0-9]{24}", str(provenance.get("run_id"))) is not None, "paired_run_identity")
        identity = provenance.get("identity", {})
        require("asr-" + base.fingerprint(identity)[:24] == provenance["run_id"], "paired_identity_hash")
        require(identity.get("output_contract") == CONTRACT and all(identity.get(k) == provenance.get(k) for k in ["model", "source_audio", "source_metadata", "proposal_sha256", "worker_sha256", "environment_lock_sha256"]), "paired_identity_provenance")
        required_configs = {"original": original["config"]}
        if not alias:
            required_configs["english"] = english["config"]
        require(identity.get("configs") == required_configs, "paired_identity_configs")
        require(len(manifest.get("files", [])) == len(members) - 1 and {x["file"] for x in manifest["files"]} == members - {"artifact_manifest.json"}, "paired_manifest_members")
        for item in manifest["files"]:
            data = archive.read(item["file"])
            require(len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"], "paired_member_hash")
        require(provenance.get("source_audio", {}).get("drive_id") and re.fullmatch(r"[a-f0-9]{64}", provenance["source_audio"].get("sha256", "")) is not None, "paired_source_proof")
        require(provenance.get("source_metadata", {}).get("drive_id") and re.fullmatch(r"[a-f0-9]{64}", provenance["source_metadata"].get("sha256", "")) is not None, "paired_metadata_proof")
        require(re.fullmatch(r"[a-f0-9]{64}", provenance.get("model", {}).get("model_sha256", "")) is not None, "paired_model_proof")
        duration = float(provenance["metrics"]["audio_seconds"])
        require(math.isfinite(duration) and duration > 0, "paired_duration")
        for key in ["original"] + ([] if alias else ["english"]):
            variant = variants[key]
            require(variant.get("text_sha256") == hashlib.sha256(archive.read(key + "/transcript.txt")).hexdigest() and variant.get("segments_sha256") == hashlib.sha256(archive.read(key + "/segments.json")).hexdigest(), "variant_hash")
            require(variant.get("config_sha256") == base.fingerprint(variant.get("config")), "variant_config_hash")
            validate_text(json.loads(archive.read(key + "/segments.json")), archive.read(key + "/transcript.txt").decode("utf-8"), variant["language"], duration)
        if alias:
            require(english.get("text_sha256") == original["text_sha256"] and english.get("segments_sha256") == original["segments_sha256"], "alias_hash")
        require(provenance.get("quality", {}).get("accuracy_claimed") is False and provenance["quality"].get("speech_coverage_validated") is False and provenance["quality"].get("human_reviewed") is False, "paired_quality")
        return {"bundle": proof, "provenance": provenance, "artifact_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest()}


def write_pair(settings, admission, run_id, variants, telemetry, provenance, *, max_bytes=None, capacity_check=None):
    limit=base.MAX_RESULT_BYTES//2 if max_bytes is None else max_bytes
    require(type(limit) is int and 0 < limit <= 256_000_000, "paired_size_budget")
    members, descriptors = {}, {}
    for key, (segments, text, config) in variants.items():
        language = segments["language"]
        validate_text(segments, text, language, float(provenance["metrics"]["audio_seconds"]))
        members[key + "/segments.json"] = base.encoded(segments)
        members[key + "/transcript.txt"] = text.encode("utf-8")
        descriptors[key] = {"text_kind": "original_asr" if key == "original" else "english_audio_translation", "language": language, "config": config, "config_sha256": base.fingerprint(config), "text_sha256": hashlib.sha256(members[key + "/transcript.txt"]).hexdigest(), "segments_sha256": hashlib.sha256(members[key + "/segments.json"]).hexdigest()}
    if "english" not in variants:
        require(descriptors["original"]["language"] == "en", "missing_translation")
        descriptors["english"] = {"text_kind": "original_english_alias", "language": "en", "same_as": "original", "translation_performed": False, "text_sha256": descriptors["original"]["text_sha256"], "segments_sha256": descriptors["original"]["segments_sha256"]}
    provenance = {**provenance, "output_contract": CONTRACT, "text_variants": descriptors, "quality_state": "unreviewed_asr"}
    members["provenance.json"], members["telemetry.json"] = base.encoded(provenance), base.encoded(telemetry)
    manifest = {"schema_version": SCHEMA, "run_id": run_id, "files": [{"file": k, "bytes": len(v), "sha256": hashlib.sha256(v).hexdigest()} for k, v in sorted(members.items())]}
    members["artifact_manifest.json"] = base.encoded(manifest)
    require(sum(map(len, members.values())) <= limit, "paired_result_size")
    if capacity_check is None:
        base.inventory(settings)
    else:
        capacity_check(sum(map(len,members.values())))
    directory = settings.output_root / admission["video_id"] / run_id
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / (run_id + ".zip")
    temporary = destination.with_suffix(".zip.part")
    require(not destination.exists() and not temporary.exists(), "existing_unverified_result")
    with zipfile.ZipFile(temporary, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in members.items():
            archive.writestr(name, raw)
    with temporary.open("r+b") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    verified = verify_pair(temporary,max_bytes=max_bytes)
    os.replace(temporary, destination)
    receipt = {"schema_version": SCHEMA, "status": "local_transcription_complete_unreviewed", "output_contract": CONTRACT, "private_root": str(settings.root), "run_id": run_id, "video_id": admission["video_id"], "job_id": admission["job_id"], "source_lease_id": admission["source_lease_id"], "source_audio": admission["job"]["audio"], "source_metadata": admission["job"]["metadata"], "model": provenance["model"], "bundle": {"path": str(destination), **verified["bundle"]}, "artifact_manifest_sha256": verified["artifact_manifest_sha256"], "drive_upload": "pending"}
    base.atomic_json(directory / "receipt.json", receipt)
    return receipt


def record_hold(settings, admission, decision, model, frame_hash):
    record = {"schema_version": 1, "status": "held", "video_id": admission["video_id"], "job_id": admission["job_id"], "source_lease_id": admission["source_lease_id"], "source_audio_sha256": admission["job"]["audio"]["sha256"], "source_audio_drive_id": admission["job"]["audio"]["drive_id"], "model": model, "proposal_sha256": frame_hash, "decision": decision, "created_at": base.now(), "semantic_text_generated": False, "source_delete_allowed": False}
    base.atomic_json(settings.root / "asr/jobs/frames/multilingual-v1/holds" / (admission["job_id"] + ".json"), record)
    with base.kernel_lock(settings.root / "sync/asr_language_manifest_append.lock"):
        with (settings.root / "sync/asr_language_manifest.jsonl").open("ab") as output:
            output.write(base.encoded(record))
            output.flush()
            os.fsync(output.fileno())
    from gpu_asr_queue import queue_lock, refresh_ready
    with queue_lock(settings.root):
        source_path = base.within(admission["source_lease"], settings.root / "asr/leases")
        source = base.read_json(source_path)
        require(source.get("status") == "active" and source.get("lease_id") == admission["source_lease_id"], "source_lease_lost")
        source.update(phase="held_language_review", consumer_owner=settings.gpu_owner, hold_reason=decision["reason"], held_at=base.now())
        base.atomic_json(source_path, source)
        refresh_ready(settings.root, frame_id="multilingual-v1")
    return record


def run_jobs(settings, admission_paths, proposal_path, runtime_factory=Runtime):
    require(0 < len(admission_paths) <= 3, "rolling_input_limit")
    runtime, results = None, []
    with base.kernel_lock(settings.root / "sync/asr_gpu_owner.lock"):
        base.inventory(settings)
        model = model_proof(settings)
        frame_hash, jobs = frame_proof(settings, proposal_path, model)
        lease = base.gpu_lease(settings)
        worker_hash = base.hashes(Path(__file__))["sha256"]
        env_names = ["HF_HUB_OFFLINE", "HF_HUB_DISABLE_IMPLICIT_TOKEN", "TRANSFORMERS_OFFLINE", "HF_HOME", "TEMP", "TMP", "OMP_NUM_THREADS"]
        old_env = {key: os.environ.get(key) for key in env_names}
        temporary = settings.root / "asr/tmp"
        temporary.mkdir(parents=True, exist_ok=True)
        os.environ.update(HF_HUB_OFFLINE="1", HF_HUB_DISABLE_IMPLICIT_TOKEN="1", TRANSFORMERS_OFFLINE="1", HF_HOME=str(settings.root / "asr/cache"), TEMP=str(temporary), TMP=str(temporary), OMP_NUM_THREADS="2")
        try:
            for path in admission_paths:
                frame_proof(settings, proposal_path, model)
                admission, objects, job = validate_admission(settings, path, frame_hash, jobs)
                if any(job.get("metadata_content_flags", {}).get(k) for k in METADATA_HOLD_FLAGS):
                    results.append(record_hold(settings, admission, decide_language(job, []), model, frame_hash))
                    continue
                from gpu_asr_queue import claim_input
                source_lease = base.read_json(admission["source_lease"])
                if source_lease["phase"] == "input_verified_waiting_gpu_lease":
                    claim_input(settings.root, admission, settings.gpu_owner)
                else:
                    require(source_lease.get("consumer_owner") == settings.gpu_owner, "source_consumer_owner")
                if runtime is None:
                    runtime = runtime_factory(settings, lease)
                require(runtime.model.model.device == "cuda" and runtime.model.model.compute_type == "int8_float16", "cpu_fallback_forbidden")
                def guard():
                    frame_proof(settings, proposal_path, model)
                    source = base.read_json(admission["source_lease"])
                    require(source.get("status") == "active" and source.get("lease_id") == admission["source_lease_id"] and base.unexpired(source.get("expires_at")), "source_lease_lost")
                monitor = Monitor(runtime, guard, lease["rolling_utilization_target"] * 100, lease["max_vram_bytes"])
                started, begin = base.now(), time.monotonic()
                try:
                    monitor.begin()
                    decision = detect_language(runtime, objects["audio"], job, monitor.guard)
                    if decision["status"] == "held":
                        results.append(record_hold(settings, admission, decision, model, frame_hash))
                        continue
                    language = decision["language"]
                    configs = {"original": {**base.CONFIG, "language": language, "task": "transcribe"}}
                    if language != "en":
                        configs["english"] = {**base.CONFIG, "language": language, "task": "translate"}
                    identity = {"schema": SCHEMA, "output_contract": CONTRACT, "worker_sha256": worker_hash, "english_helper_sha256": base.hashes(Path(base.__file__))["sha256"], "proposal_sha256": frame_hash, "source_audio": job["audio"], "source_metadata": job["metadata"], "model": model, "configs": configs, "decode": {"window_seconds": base.WINDOW_SECONDS, "overlap_seconds": 0}, "language_policy": {"minimum_probability": MIN_PROBABILITY, "minimum_margin": MIN_MARGIN}, "environment_lock_sha256": base.hashes(settings.environment_lock)["sha256"]}
                    run_id = "asr-" + base.fingerprint(identity)[:24]
                    receipt_path = settings.output_root / admission["video_id"] / run_id / "receipt.json"
                    if receipt_path.exists():
                        receipt = base.read_json(receipt_path)
                        verified = verify_pair(receipt["bundle"]["path"], receipt["bundle"])
                        require(verified["provenance"].get("identity") == identity, "existing_result_version")
                        results.append(receipt)
                        continue
                    variants, task_metrics = {}, {}
                    for key, config in configs.items():
                        monitor.guard()
                        task_start = time.monotonic()
                        segments, text, vad_seconds = base.collect_segments(TaskRuntime(runtime, config), objects["audio"], float(job["duration_seconds"]), monitor.guard)
                        segments.update(language=language if key == "original" else "en", character_offset_unit="unicode_code_points", text_kind="original_asr" if key == "original" else "english_audio_translation")
                        variants[key] = (segments, text, config)
                        task_metrics[key] = {"decode_inference_pacing_seconds": time.monotonic() - task_start, "duration_after_vad_seconds": vad_seconds, "segment_count": len(segments["segments"])}
                finally:
                    telemetry = monitor.finish()
                validate_admission(settings, path, frame_hash, jobs)
                provenance = {"schema_version": SCHEMA, "run_id": run_id, "job_id": admission["job_id"], "source_video_id": admission["video_id"], "channel_dir": job["source"]["channel_dir"], "source_lease_id": admission["source_lease_id"], "source_audio": job["audio"], "source_metadata": job["metadata"], "source_admission_sha256": base.hashes(path)["sha256"], "proposal_sha256": frame_hash, "model": model, "identity": identity, "language_decision": decision, "metadata_flags_are_not_interval_classification": True, "worker_sha256": worker_hash, "environment_lock_sha256": identity["environment_lock_sha256"], "dependencies": runtime.dependencies, "started_at": started, "finished_at": base.now(), "compute": {"device": "cuda:0", "compute_type": "int8_float16", "model_workers": 1, "batch_size": 1, "cpu_asr_fallback": False, "gpu_lease_id": settings.gpu_lease_id}, "metrics": {"audio_seconds": variants["original"][0]["duration_seconds"], "detection_decode_inference_pacing_seconds": time.monotonic() - begin, "tasks": task_metrics}, "quality": {"accuracy_claimed": False, "human_reviewed": False, "speech_coverage_validated": False, "translation_semantics_human_verified": False, "window_boundary_effects_unvalidated": True, "word_times_are_model_estimates": True, "host_guest_identity_assigned": False}}
                results.append(write_pair(settings, admission, run_id, variants, telemetry, provenance))
        finally:
            if runtime is not None:
                runtime.close()
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    return results


def publish_result(receipt_path, remote, drive):
    receipt_path = Path(receipt_path)
    receipt = base.read_json(receipt_path)
    root = Path(receipt["private_root"]).resolve()
    require(receipt_path.resolve().is_relative_to(root / "asr/results"), "result_receipt_location")
    bundle = Path(receipt["bundle"]["path"]).resolve()
    require(bundle == receipt_path.resolve().parent / (receipt["run_id"] + ".zip"), "result_bundle_location")
    verified = verify_pair(bundle, receipt["bundle"])
    provenance = verified["provenance"]
    for key in ["run_id", "job_id", "source_lease_id", "source_audio", "source_metadata", "model"]:
        require(receipt[key] == provenance[key], "paired_receipt_identity")
    require(receipt["video_id"] == provenance["source_video_id"] and receipt["artifact_manifest_sha256"] == verified["artifact_manifest_sha256"], "paired_receipt_identity")
    parent = receipt["source_audio"]["remote"].rpartition("/")[0]
    require(remote == f"{parent}/{receipt['video_id']}/ASR/{receipt['run_id']}/{receipt['run_id']}.zip", "result_remote_path")
    drive.copy(bundle, remote)
    observed = drive.stat(remote)
    hashes = {k.lower(): v for k, v in observed.get("Hashes", {}).items()} if isinstance(observed, dict) else {}
    require(isinstance(observed, dict) and observed.get("ID") and observed.get("Size") == verified["bundle"]["bytes"] and hashes.get("md5", "").lower() == verified["bundle"]["md5"], "result_drive_proof")
    verify_pair(bundle, verified["bundle"])
    record = {"schema_version": SCHEMA, "status": "verified", "artifact_kind": "asr_bundle", "output_contract": CONTRACT, "quality_state": "unreviewed_asr", "verified_at": base.now(), "video_id": receipt["video_id"], "channel_dir": provenance["channel_dir"], "job_id": receipt["job_id"], "run_id": receipt["run_id"], "source_lease_id": receipt["source_lease_id"], "remote": remote, "drive_id": observed["ID"], **verified["bundle"], "source_audio_drive_id": receipt["source_audio"]["drive_id"], "source_audio_sha256": receipt["source_audio"]["sha256"], "source_metadata": receipt["source_metadata"], "model": receipt["model"], "text_variants": provenance["text_variants"], "metrics": provenance["metrics"], "artifact_manifest_sha256": verified["artifact_manifest_sha256"]}
    with base.kernel_lock(root / "sync/asr_manifest_append.lock"):
        with (root / "sync/asr_manifest.jsonl").open("ab") as output:
            output.write(base.encoded(record))
            output.flush()
            os.fsync(output.fileno())
        receipt.update(drive_upload="verified", remote_proof=record)
        base.atomic_json(receipt_path, receipt)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("bundle", type=Path)
    run = sub.add_parser("run")
    for name in ["root", "model-dir", "model-receipt", "proposal"]:
        run.add_argument("--" + name, type=Path, required=True)
    run.add_argument("--gpu-lease-id", required=True)
    run.add_argument("--gpu-owner", required=True)
    run.add_argument("--managed-root", action="append", type=Path, required=True)
    run.add_argument("--environment-lock", type=Path, default=base.DEFAULT_LOCK)
    inputs = run.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--admission", action="append", type=Path)
    inputs.add_argument("--ready", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.mode == "verify":
            result = verify_pair(args.bundle)
            print(json.dumps({"status": "verified_local_paired_bundle", **result["bundle"]}))
            return 0
        settings = Settings(args.root, args.model_dir, args.model_receipt, args.gpu_lease_id, args.gpu_owner, args.managed_root, args.environment_lock)
        paths = args.admission or base.read_json(base.within(args.ready, settings.root / "asr/jobs"))["admissions"]
        results = run_jobs(settings, paths, args.proposal)
        print(json.dumps({"status": "bounded_multilingual_run_finished", "local_paired_results": sum(x.get("status") == "local_transcription_complete_unreviewed" for x in results), "held": sum(x.get("status") == "held" for x in results), "uploaded": False}))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "pending", "error_class": exc.kind if isinstance(exc, AsrError) else "worker_error"}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
