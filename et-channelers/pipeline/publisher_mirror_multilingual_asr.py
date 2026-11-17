"""Leased German publisher-edition ASR and separately typed English translation.

Reuse publisher_mirror_asr's exact archive/RSS proof gate and the existing large-v3
runtime, language decision, paired writer and verifier. Imports are inert. No
source acquisition, model download, native-journal writes or input deletion.
Prepare accepts one ordinary mirror cohort item; run requires a newly admitted
GPU/source lease whose publisher_mirror_multilingual field equals binding_for().
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

try:
    from . import gpu_asr as base, gpu_asr_multilingual as multi
    from . import publisher_mirror_asr as mirror, publisher_variant_asr as variant
except ImportError:
    import gpu_asr as base
    import gpu_asr_multilingual as multi
    import publisher_mirror_asr as mirror
    import publisher_variant_asr as variant

PROFILE = "publisher-mirror-german-and-english-asr-v1"
BINDING_KEY = "publisher_mirror_multilingual"
POLICY = {"profile": PROFILE, "max_sources": 1, "max_input_bytes": 128_000_000,
          "window_seconds": 30, "duration_tolerance_seconds": 2, "wall_seconds": 3600,
          "heartbeat_seconds": 1, "language": "de", "language_evidence_scope": "publisher_rss_channel_declaration",
          "detection_min_probability": multi.MIN_PROBABILITY, "detection_min_margin": multi.MIN_MARGIN,
          "original_config": {**variant.CONFIG, "language": "de", "task": "transcribe"},
          "english_config": {**variant.CONFIG, "language": "de", "task": "translate"},
          "native_youtube_bytes": False, "changes_native_audio_count": False, "changes_native_asr_count": False}
SOURCE_KEYS = ("variant_id", "source_kind", "associated_youtube_id", "channel_dir", "measured_duration_seconds",
               "publisher_declared_duration_seconds", "episode_guid", "association", "native_youtube_bytes", "language")


def require(value, code):
    base.require(value, "publisher_pair_" + code)


def prepare_job(item):
    job = mirror.prepare_mirror_job(item)
    accepted, observed = mirror.json_file(Path(job["language_evidence_path"]))
    require(observed["sha256"] == job["language_evidence_sha256"], "language_evidence_changed")
    code = accepted["feed"].get("language")
    code = code.lower() if isinstance(code, str) else None
    german = bool(code and (code == "de" or code.startswith("de-")))
    held = job["status"] == "held_language_review" or any(
        accepted.get("association_evidence", {}).get(flag) is True for flag in multi.METADATA_HOLD_FLAGS)
    caption = job["association"]["source_adapter"]["caption_availability"]
    job["status"] = ("held_language_review" if held else "pending_german_publisher_language_evidence" if not german
                     else "publisher_text_available_review_before_asr" if caption["usable_english_bundles"] else "eligible")
    job["language"] = {"code": code, "basis": "hash_bound_publisher_rss_channel",
        "scope": "publisher_rss_channel_declaration", "evidence_sha256": observed["sha256"],
        "feed_sha256": accepted["feed"]["sha256"], "episode_language_independently_verified": False,
        "native_youtube_language_asserted": False} if german else None
    job["association"]["paired_adapter"] = {"profile": PROFILE, "worker_sha256": variant.sha(__file__),
                                            "output_contract": multi.CONTRACT}
    return job


def helper_hashes():
    return {"worker_sha256": variant.sha(__file__), "core_sha256": variant.sha(base.__file__),
            "multilingual_sha256": variant.sha(multi.__file__), "mirror_bridge_sha256": variant.sha(mirror.__file__),
            "variant_helper_sha256": variant.sha(variant.__file__)}


def prepare(args):
    variant.load_helpers(args.pipeline, args.heartbeat_worker)  # verify the existing pinned heartbeat; no GPU imports
    cohort = variant.read(args.cohort)
    require(len(cohort.get("items", [])) == 1, "cohort_size")
    jobs = [prepare_job(cohort["items"][0])]
    require(sum(j["audio"]["bytes"] + j["provenance"]["bytes"] for j in jobs) <= POLICY["max_input_bytes"], "input_budget")
    model = variant.read(multi.PINNED)["model"]
    proposal = {"schema_version": 1, "profile": PROFILE, **helper_hashes(), "config": POLICY,
        "config_sha256": base.fingerprint(POLICY), "model": model, "model_manifest_sha256": base.fingerprint(model),
        "heartbeat_worker_path": str(Path(args.heartbeat_worker).resolve()), "heartbeat_sha256": variant.HEARTBEAT_SHA,
        "cohort_path": str(Path(args.cohort).resolve()), "cohort_sha256": variant.sha(args.cohort), "jobs": jobs,
        "changes_native_audio_count": False, "changes_native_asr_count": False}
    with Path(args.output).open("xb") as output:
        output.write(base.encoded(proposal))
    return {"proposal_sha256": base.fingerprint(proposal), "binding": binding_for(proposal, base.fingerprint(proposal)),
            "eligible": sum(j["status"] == "eligible" for j in jobs), "profile": PROFILE}


def binding_for(proposal, proposal_sha):
    keys = (*helper_hashes(), "config_sha256", "model_manifest_sha256", "heartbeat_sha256", "cohort_sha256")
    return {**{key: proposal[key] for key in keys}, "proposal_sha256": proposal_sha}


def verify_proposal(args):
    require(variant.sha(args.proposal) == args.proposal_sha256, "proposal_hash")
    proposal = variant.read(args.proposal)
    require(proposal.get("profile") == PROFILE and proposal.get("config") == POLICY and
            proposal.get("config_sha256") == base.fingerprint(POLICY), "proposal_policy")
    require(all(proposal.get(k) == v for k, v in helper_hashes().items()), "helper_changed")
    heartbeat, _, _ = variant.load_helpers(args.pipeline, proposal["heartbeat_worker_path"])
    require(proposal.get("heartbeat_sha256") == variant.HEARTBEAT_SHA and
            variant.sha(proposal["cohort_path"]) == proposal["cohort_sha256"], "cohort_hash")
    cohort = variant.read(proposal["cohort_path"])
    require(len(cohort.get("items", [])) == 1 and proposal["jobs"] == [prepare_job(cohort["items"][0])], "evidence_changed")
    require(proposal["model"] == variant.read(multi.PINNED)["model"] and
            proposal["model_manifest_sha256"] == base.fingerprint(proposal["model"]), "model_manifest")
    require(sum(j["audio"]["bytes"] + j["provenance"]["bytes"] for j in proposal["jobs"]) <= POLICY["max_input_bytes"], "input_budget")
    return proposal, heartbeat


def validate_source(settings, job, admission, binding, model, heartbeat):
    gpu = base.gpu_lease(settings)
    require(gpu.get(BINDING_KEY) == binding and all(gpu.get("model", {}).get(k) == model[k]
            for k in ("repository", "revision", "model_sha256")), "gpu_binding")
    source_path = base.within(admission["source_lease_path"], settings.root / "asr/leases")
    source = base.read_json(source_path)
    require(source.get("schema_version") == 1 and source.get("state") == "active" and source.get("profile") == PROFILE,
            "source_state")
    require(source.get("owner") == settings.gpu_owner and source.get("lease_id") == admission.get("source_lease_id") and
            source.get(BINDING_KEY) == binding, "source_binding")
    require(source.get("source_variant_id") == job["variant_id"] and source.get("source_audio") == job["audio"] and
            source.get("source_provenance") == job["provenance"], "source_proof")
    require(source.get("publisher_language_evidence_sha256") == job["language"]["evidence_sha256"] and
            source.get("native_youtube_bytes") is False, "source_language")
    paths = {key: base.within(job[key + "_path"], settings.root / "asr/input") for key in ("audio", "provenance")}
    require({str(Path(p).resolve()) for p in source.get("input_paths", [])} == {str(p) for p in paths.values()}, "source_paths")
    expiry = min(heartbeat.epoch(gpu["expires_at"]), heartbeat.epoch(source["expires_at"]))
    require(expiry > time.time(), "source_expired")
    return paths, expiry


def verify_inputs(job, paths):
    for key, path in paths.items():
        observed = base.hashes(path)
        require(all(observed[k] == job[key][k] for k in ("bytes", "md5", "sha256")), "input_hash")
    require(base.read_json(paths["provenance"]) == job["provenance_data"], "input_provenance")


class CheckedRuntime:
    """Reuses the runtime; prove each complete pass with exact sample accounting."""
    def __init__(self, runtime, guard, duration):
        self.runtime, self.guard, self.duration = runtime, guard, duration
        self.model = runtime.model
        self.passes = []

    def windows(self, path, expected):
        require(expected == self.duration, "decode_duration_binding")
        samples = 0
        iterator = iter(self.runtime.windows(path, expected))
        while True:
            self.guard()
            try:
                start, audio = next(iterator)
            except StopIteration:
                break
            require(round(start * base.SAMPLE_RATE) == samples and 0 < len(audio) <= 30 * base.SAMPLE_RATE, "decode_window_geometry")
            samples += len(audio)
            require(samples <= int((expected + 2) * base.SAMPLE_RATE), "decode_limit")
            yield start, audio
        require(samples > 0 and abs(samples / base.SAMPLE_RATE - expected) <= 2, "decoded_duration")
        self.passes.append(samples)

    def speech(self, audio):
        return self.runtime.speech(audio)

    def detect(self, audio):
        return self.runtime.detect(audio)


def append_record(root, name, record):
    with base.kernel_lock(root / "sync" / (name + "_append.lock")):
        with (root / "sync" / (name + ".jsonl")).open("ab") as output:
            output.write(base.encoded(record))
            output.flush()
            os.fsync(output.fileno())


def run(args, runtime_factory=multi.Runtime):
    proposal, hb = verify_proposal(args)
    settings = base.Settings(**variant.read(args.settings))
    binding = binding_for(proposal, args.proposal_sha256)
    jobs = [j for j in proposal["jobs"] if j["status"] == "eligible"]
    admissions = variant.read(args.admissions).get("items", [])
    require(len(jobs) == len(admissions) == 1 and admissions[0].get("variant_id") == jobs[0]["variant_id"], "admissions")
    job, admission = jobs[0], admissions[0]
    runtime, monitor = None, None
    with base.kernel_lock(settings.root / "sync/asr_gpu_owner.lock"):
        base.inventory(settings)
        model = multi.model_proof(settings)
        require(model["manifest_sha256"] == proposal["model_manifest_sha256"], "model_binding")
        paths, _ = validate_source(settings, job, admission, binding, model, hb)
        heartbeat = hb.Heartbeat(lambda: validate_source(settings, job, admission, binding, model, hb)[1], POLICY["wall_seconds"])
        heartbeat(force=True)
        verify_inputs(job, paths)
        try:
            runtime = runtime_factory(settings, base.gpu_lease(settings))
            require(runtime.model.model.device == "cuda" and runtime.model.model.compute_type == "int8_float16", "cpu_fallback_forbidden")
            gpu = base.gpu_lease(settings)
            monitor = multi.Monitor(runtime, heartbeat, gpu["rolling_utilization_target"] * 100, gpu["max_vram_bytes"])
            monitor.begin()
            checked = CheckedRuntime(runtime, monitor.guard, job["measured_duration_seconds"])
            started, begin = base.now(), time.monotonic()
            decision = multi.detect_language(checked, paths["audio"], {"duration_seconds": job["measured_duration_seconds"],
                "declared_audio_language": "de", "metadata_content_flags": {}}, monitor.guard)
            require(len(checked.passes) == 1, "detection_decode_proof")
            if decision["status"] != "accepted":
                record = {"schema_version": 1, "status": "held", "artifact_kind": "publisher_variant_language_review",
                    "profile": PROFILE, "variant_id": job["variant_id"], "source_audio": job["audio"], "source_provenance": job["provenance"],
                    "source_lease_id": admission["source_lease_id"], "proposal_sha256": args.proposal_sha256,
                    "language_evidence": job["language"], "decision": decision, "created_at": base.now(),
                    "semantic_text_generated": False, "source_delete_allowed": False, "native_youtube_bytes": False,
                    "changes_native_audio_count": False, "changes_native_asr_count": False}
                append_record(settings.root, "publisher_variant_language_manifest", record)
                return record
            require(decision.get("language") == "de", "detected_language_conflict")
            decision["basis"] = "publisher_feed_declaration_and_sampled_model_agreement"
            configs = {"original": POLICY["original_config"], "english": POLICY["english_config"]}
            source_variant = {key: job[key] for key in SOURCE_KEYS}
            identity = {"schema": 1, "profile": PROFILE, "output_contract": multi.CONTRACT, "worker_sha256": variant.sha(__file__),
                "proposal_sha256": args.proposal_sha256, "source_audio": job["audio"], "source_metadata": job["provenance"],
                "source_variant": source_variant, "model": model, "configs": configs, BINDING_KEY: binding,
                "environment_lock_sha256": base.hashes(settings.environment_lock)["sha256"]}
            run_id = "asr-" + base.fingerprint(identity)[:24]
            source_id, job_id = "publisher-" + job["variant_id"], "publisher-pair-" + job["variant_id"][:24]
            destination = settings.output_root / source_id / run_id
            require(not destination.exists(), "result_exists")
            variants, tasks = {}, {}
            for key, config in configs.items():
                monitor.guard()
                segments, text, vad = base.collect_segments(multi.TaskRuntime(checked, config), paths["audio"], job["measured_duration_seconds"], monitor.guard)
                segments.update(language="de" if key == "original" else "en", character_offset_unit="unicode_code_points",
                                text_kind="original_asr" if key == "original" else "english_audio_translation")
                variants[key] = (segments, text, config)
                tasks[key] = {"decoded_samples": checked.passes[-1], "duration_after_vad_seconds": vad, "segment_count": len(segments["segments"])}
            require(len(checked.passes) == 3 and len(set(checked.passes)) == 1, "paired_decode_extent")
            heartbeat(force=True)
            verify_inputs(job, paths)
            telemetry = monitor.finish()
            monitor = None
            telemetry["guard"] = heartbeat.counters
            provenance = {**identity, "run_id": run_id, "job_id": job_id, "source_video_id": source_id,
                "source_kind": "publisher_audio_variant", "variant_id": job["variant_id"], "channel_dir": job["channel_dir"],
                "associated_youtube_id": job["associated_youtube_id"], "source_variant": source_variant,
                "source_lease_id": admission["source_lease_id"], "identity": identity, "original_publisher_provenance": job["provenance_data"],
                "language_evidence": job["language"], "language_decision": decision, "dependencies": runtime.dependencies,
                "native_youtube_bytes": False, "changes_native_audio_count": False, "changes_native_asr_count": False,
                "started_at": started, "finished_at": base.now(), "compute": {"device": "cuda:0", "compute_type": "int8_float16",
                "model_workers": 1, "batch_size": 1, "cpu_asr_fallback": False, "gpu_lease_id": settings.gpu_lease_id},
                "metrics": {"audio_seconds": checked.passes[0] / base.SAMPLE_RATE, "measured_container_duration_seconds": job["measured_duration_seconds"],
                            "detection_decoded_samples": checked.passes[0], "tasks": tasks, "elapsed_seconds": time.monotonic() - begin},
                "quality": {"accuracy_claimed": False, "human_reviewed": False, "speech_coverage_validated": False,
                            "translation_semantics_human_verified": False, "native_youtube_alignment_validated": False,
                            "word_times_are_model_estimates": True, "window_boundary_effects_unvalidated": True}}
            writer_admission = {"video_id": source_id, "job_id": job_id, "source_lease_id": admission["source_lease_id"],
                                "job": {"audio": job["audio"], "metadata": job["provenance"]}}
            receipt = multi.write_pair(settings, writer_admission, run_id, variants, telemetry, provenance)
            receipt.update(artifact_kind="publisher_variant_asr", profile=PROFILE, variant_id=job["variant_id"],
                           source_kind="publisher_audio_variant", associated_youtube_id=job["associated_youtube_id"],
                           native_youtube_bytes=False, changes_native_asr_count=False, changes_native_audio_count=False)
            receipt_path = destination / "receipt.json"
            base.atomic_json(receipt_path, receipt)
            verify_result(receipt)
            return {"status": "local_publisher_pair_complete", "receipt_path": str(receipt_path), "receipt": receipt,
                    "uploaded": False, "source_delete_allowed": False}
        finally:
            original = sys.exc_info()[1]
            try:
                if monitor:
                    monitor.finish()
            except Exception:
                if original is None:
                    raise
            finally:
                if runtime:
                    runtime.close()


def verify_result(receipt):
    require(receipt.get("artifact_kind") == "publisher_variant_asr" and receipt.get("profile") == PROFILE and
            receipt.get("source_kind") == "publisher_audio_variant", "receipt_type")
    verified = multi.verify_pair(receipt["bundle"]["path"], receipt["bundle"])
    p = verified["provenance"]
    for value in (receipt, p):
        require(all(value.get(k) is False for k in ("native_youtube_bytes", "changes_native_audio_count", "changes_native_asr_count")), "native_promotion")
    require(p.get("profile") == PROFILE and p.get("source_kind") == "publisher_audio_variant" and
            p.get("variant_id") == p["source_audio"]["sha256"] == receipt.get("variant_id"), "variant_identity")
    for key in ("run_id", "job_id", "source_lease_id", "source_audio", "source_metadata", "model", "associated_youtube_id"):
        require(receipt.get(key) == p.get(key), "receipt_identity")
    require(receipt.get("video_id") == p.get("source_video_id") and
            receipt.get("artifact_manifest_sha256") == verified["artifact_manifest_sha256"], "receipt_manifest")
    require(p["identity"].get("source_variant") == p.get("source_variant") and
            p["identity"].get("profile") == PROFILE and
            p["identity"].get(BINDING_KEY) == p.get(BINDING_KEY) and
            p.get("language_evidence") == p["source_variant"].get("language"), "publisher_identity")
    require(all(p["source_variant"].get(key) == p.get(key) for key in
                ("variant_id", "associated_youtube_id", "channel_dir", "source_kind", "native_youtube_bytes")), "publisher_source_identity")
    require(all(p.get("original_publisher_provenance", {}).get("audio", {}).get(key) == p["source_audio"].get(key)
                for key in ("bytes", "md5", "sha256")), "original_publisher_proof")
    require(p["text_variants"]["original"]["language"] == "de" and p["text_variants"]["english"].get("same_as") is None,
            "german_distinct_translation")
    require(p.get("language_decision", {}).get("status") == "accepted" and p["language_decision"].get("language") == "de", "language_decision")
    return verified


def publish_result(receipt_path, drive):
    receipt_path = Path(receipt_path).resolve()
    receipt = variant.read(receipt_path)
    root = Path(receipt["private_root"]).resolve()
    require(receipt_path == base.within(receipt_path, root / "asr/results"), "receipt_location")
    bundle = base.within(receipt["bundle"]["path"], root / "asr/results")
    require(bundle == receipt_path.parent / (receipt["run_id"] + ".zip"), "bundle_location")
    verified = verify_result(receipt)
    p = verified["provenance"]
    remote = p["source_audio"]["remote"].rpartition("/")[0] + "/ASR/" + receipt["run_id"] + "/" + receipt["run_id"] + ".zip"
    drive.copy(bundle, remote)
    observed = drive.stat(remote)
    hashes = {k.lower(): v for k, v in observed.get("Hashes", {}).items()} if isinstance(observed, dict) else {}
    require(isinstance(observed, dict) and observed.get("ID") and observed["ID"] not in
            {p["source_audio"]["drive_id"], p["source_metadata"]["drive_id"]} and observed.get("Size") == verified["bundle"]["bytes"] and
            hashes.get("md5", "").lower() == verified["bundle"]["md5"], "drive_proof")
    verify_result(receipt)
    record = {"schema_version": 1, "status": "verified", "artifact_kind": "publisher_variant_asr", "profile": PROFILE,
        "output_contract": multi.CONTRACT, "quality_state": "unreviewed_asr", "verified_at": base.now(), "variant_id": p["variant_id"],
        "associated_youtube_id": p["associated_youtube_id"], "channel_dir": p["channel_dir"], "source_audio": p["source_audio"],
        "source_provenance": p["source_metadata"], "source_variant": p["source_variant"], "source_lease_id": p["source_lease_id"],
        "run_id": receipt["run_id"], "remote": remote, "drive_id": observed["ID"], **verified["bundle"],
        "model": p["model"], "language_evidence": p["language_evidence"], "text_variants": p["text_variants"], "metrics": p["metrics"],
        "artifact_manifest_sha256": verified["artifact_manifest_sha256"], "native_youtube_bytes": False,
        "changes_native_audio_count": False, "changes_native_asr_count": False}
    append_record(root, "publisher_variant_asr_manifest", record)
    receipt.update(drive_upload="verified", remote_proof=record)
    base.atomic_json(receipt_path, receipt)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run"))
    for key in ("pipeline", "heartbeat-worker", "cohort", "output", "proposal", "proposal-sha256", "settings", "admissions"):
        parser.add_argument("--" + key)
    args = parser.parse_args(argv)
    try:
        result = prepare(args) if args.mode == "prepare" else run(args)
        print(json.dumps(result))
        return 0
    except Exception as error:
        print(json.dumps({"status": "held", "error_class": str(error) if isinstance(error, (base.AsrError, variant.VariantError)) else type(error).__name__}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
