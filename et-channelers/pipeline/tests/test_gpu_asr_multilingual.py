"""Offline multilingual admission, uncertainty and paired artifact regressions."""
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from types import ModuleType
import unittest
from unittest.mock import Mock, patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gpu_asr as base
import gpu_asr_multilingual as multi
import test_gpu_asr as fixtures


class Runtime(fixtures.FakeRuntime):
    def __init__(self, *args):
        super().__init__(*args)
        self.calls = []
        self.detected = "ja"
        self.probability = .97
        self.speech_seconds = 30
        self.model.transcribe = self.task

    def windows(self, _path, duration):
        for index in range(math.ceil(duration / 30)):
            yield index * 30, fixtures.Audio(min(30, duration - index * 30))

    def speech(self, audio):
        return audio, min(self.speech_seconds, len(audio) / base.SAMPLE_RATE)

    def detect(self, _audio):
        return self.detected, self.probability, [(self.detected, self.probability), ("fr", .02)]

    def task(self, _audio, **config):
        self.calls.append(config)
        text = "Hello" if config["task"] == "translate" or config["language"] == "en" else "こんにちは"
        word = SimpleNamespace(start=0, end=.9, word=text, probability=.95)
        segment = SimpleNamespace(start=0, end=.9, text=text, words=[word], avg_logprob=-.1, no_speech_prob=.01, compression_ratio=1)
        return iter([segment]), SimpleNamespace(duration_after_vad=25)


class MultilingualTests(unittest.TestCase):
    def setUp(self):
        fixtures.WorkerTests.setUp(self)
        patch.object(multi, "PINNED", self.pinned).start()
        self.job.update(profile=multi.PROFILE, metadata_content_flags={key: False for key in multi.METADATA_HOLD_FLAGS}, declared_audio_language="ja", duration_seconds=90)
        self.source_lease.update(frame_id="multilingual-v1")
        self.admission["job"] = self.job
        self.admission["language"]["code"] = "ja"
        self.proposal_path = self.root / "asr/jobs/frames/multilingual-v1/proposal-test.json"
        self.set_language("ja")

    def set_language(self, declared):
        self.job["declared_audio_language"] = declared
        fixtures.write(self.metadata, {"source": {"video_id": self.video}, "languages": {"audio": declared}})
        self.job["metadata"].update(base.hashes(self.metadata))
        for item in self.admission["verified_input_objects"]:
            if item["kind"] == "metadata":
                item["source"] = copy.deepcopy(self.job["metadata"])
                item["local"] = base.hashes(self.metadata)
        self.refresh_frame()

    def refresh_frame(self):
        jobs = []
        for index in range(5):
            value = copy.deepcopy(self.job)
            value.update(video_id=self.video if index == 0 else "abcdefghij" + str(index), proposal_job_id=value["job_id"] if index == 0 else "job-" + str(index), source_lease={"superseded_english_hold_lease_id": None})
            jobs.append(value)
        fixtures.write(self.proposal_path, {"schema_version": 1, "frame_id": "multilingual-v1", "jobs": jobs})
        frame_hash = base.hashes(self.proposal_path)["sha256"]
        self.admission["proposal_sha256"] = frame_hash
        self.gpu.update(input_frame_sha256=frame_hash, model={"repository": self.model["repository"], "revision": self.model["revision"], "model_sha256": self.model["files"][0]["sha256"]})
        fixtures.write(self.root / "sync/gpu_lease.json", self.gpu)
        fixtures.write(self.source_lease_path, self.source_lease)
        fixtures.write(self.admission_path, self.admission)

    def run_fake(self, runtime=None):
        runtime = runtime or Runtime()
        with patch.object(base, "inventory", return_value={"managed_bytes": 100}):
            result = multi.run_jobs(self.settings, [self.admission_path], self.proposal_path, runtime_factory=Mock(return_value=runtime))[0]
        return result, runtime

    def rewrite_zip(self, receipt, change):
        path = Path(receipt["bundle"]["path"])
        with zipfile.ZipFile(path) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        change(members)
        # Rehash the outer manifest so semantic checks cannot hide behind stale hashes.
        manifest = json.loads(members["artifact_manifest.json"])
        manifest["files"] = [{"file": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} for name, raw in sorted(members.items()) if name != "artifact_manifest.json"]
        members["artifact_manifest.json"] = base.encoded(manifest)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, raw in members.items():
                archive.writestr(name, raw)
        return path

    def test_import_and_isolated_cli_are_inert(self):
        program = "import os,sys; before=dict(os.environ);import gpu_asr_multilingual;assert dict(os.environ)==before;assert not {'numpy','av','pynvml','ctranslate2','faster_whisper'}&set(sys.modules)"
        result = subprocess.run([sys.executable, "-c", program], cwd=base.HERE, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, "-I", multi.__file__, "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_known_japanese_produces_distinct_typed_pair(self):
        result, runtime = self.run_fake()
        verified = multi.verify_pair(result["bundle"]["path"], result["bundle"])
        variants = verified["provenance"]["text_variants"]
        self.assertEqual(variants["original"]["language"], "ja")
        self.assertEqual(variants["english"]["language"], "en")
        self.assertEqual(variants["english"]["config"]["task"], "translate")
        self.assertEqual({x["task"] for x in runtime.calls}, {"transcribe", "translate"})
        self.assertTrue(runtime.closed)
        self.assertTrue(self.audio.exists())
        with zipfile.ZipFile(result["bundle"]["path"]) as archive:
            self.assertEqual(len(archive.namelist()), 7)
        with self.assertRaisesRegex(base.AsrError, "bundle_members"):
            base.verify_bundle(result["bundle"]["path"])

    def test_detected_english_alias_does_not_invent_translation(self):
        self.set_language("und")
        runtime = Runtime(); runtime.detected = "en"
        result, runtime = self.run_fake(runtime)
        proof = multi.verify_pair(result["bundle"]["path"])
        english = proof["provenance"]["text_variants"]["english"]
        self.assertEqual(english["same_as"], "original")
        self.assertFalse(english["translation_performed"])
        self.assertEqual({x["task"] for x in runtime.calls}, {"transcribe"})
        with zipfile.ZipFile(result["bundle"]["path"]) as archive:
            self.assertEqual(set(archive.namelist()), multi.CORE_MEMBERS)

    def test_light_language_metadata_holds_before_gpu_factory(self):
        self.job["metadata_content_flags"]["claimed_light_language"] = True
        self.refresh_frame()
        factory = Mock()
        with patch.object(base, "inventory", return_value={}):
            result = multi.run_jobs(self.settings, [self.admission_path], self.proposal_path, factory)[0]
        self.assertEqual(result["status"], "held")
        self.assertEqual(result["decision"]["reason"], "metadata_nonlexical_review")
        factory.assert_not_called()
        self.assertFalse((self.root / "sync/asr_manifest.jsonl").exists())
        self.assertTrue(self.audio.exists())
        self.assertEqual(base.read_json(self.source_lease_path)["phase"], "held_language_review")

    def test_silence_never_reaches_language_or_transcription_model(self):
        self.set_language("und")
        runtime = Runtime(); runtime.speech_seconds = 0
        runtime.detect = Mock(side_effect=AssertionError("must not classify silence"))
        result, runtime = self.run_fake(runtime)
        self.assertEqual(result["decision"]["reason"], "no_reliable_speech")
        self.assertFalse(runtime.calls)
        self.assertTrue(self.audio.exists())

    def test_low_probability_is_held_without_semantic_output(self):
        self.set_language("und")
        runtime = Runtime(); runtime.probability = .65
        result, runtime = self.run_fake(runtime)
        self.assertEqual(result["decision"]["reason"], "language_confidence_insufficient")
        self.assertFalse(runtime.calls)

    def test_unknown_requires_repeated_agreement_and_margin(self):
        job = {"declared_audio_language": "und", "duration_seconds": 90, "metadata_content_flags": {}}
        strong = {"speech_seconds": 10, "language": "en", "probability": .99, "margin": .98}
        self.assertEqual(multi.decide_language(job, [strong])["status"], "held")
        self.assertEqual(multi.decide_language(job, [strong, strong])["language"], "en")
        self.assertEqual(multi.decide_language(job, [dict(strong, margin=.05)] * 3)["status"], "held")
        self.assertEqual(multi.decide_language(job, [strong, dict(strong, language="ja")])["reason"], "mixed_or_conflicting_language")

    def test_metadata_detection_conflict_is_held(self):
        runtime = Runtime(); runtime.detected = "en"
        result, runtime = self.run_fake(runtime)
        self.assertEqual(result["decision"]["reason"], "metadata_detection_conflict")
        self.assertFalse(runtime.calls)

    def test_frame_hash_and_model_binding_precede_runtime(self):
        for change in [{"input_frame_sha256": "f" * 64}, {"model": {"repository": "other", "revision": "a" * 40, "model_sha256": "0" * 64}}]:
            fixtures.write(self.root / "sync/gpu_lease.json", {**self.gpu, **change})
            factory = Mock()
            with patch.object(base, "inventory", return_value={}):
                with self.assertRaises(base.AsrError):
                    multi.run_jobs(self.settings, [self.admission_path], self.proposal_path, factory)
            factory.assert_not_called()

    def test_changed_source_or_model_never_loads_gpu(self):
        self.audio.write_bytes(b"changed")
        factory = Mock()
        with patch.object(base, "inventory", return_value={}):
            with self.assertRaisesRegex(base.AsrError, "source_hash"):
                multi.run_jobs(self.settings, [self.admission_path], self.proposal_path, factory)
        factory.assert_not_called()

    def test_no_cpu_fallback(self):
        runtime = Runtime(); runtime.model.model.device = "cpu"
        with self.assertRaisesRegex(base.AsrError, "cpu_fallback_forbidden"):
            self.run_fake(runtime)
        self.assertTrue(runtime.closed)

    def test_missing_translation_member_rejected(self):
        result, _ = self.run_fake()
        path = self.rewrite_zip(result, lambda members: members.pop("english/transcript.txt"))
        with self.assertRaisesRegex(base.AsrError, "paired_member_set"):
            multi.verify_pair(path)

    def test_non_english_cannot_claim_english_alias(self):
        result, _ = self.run_fake()
        def change(members):
            provenance = json.loads(members["provenance.json"])
            provenance["text_variants"]["english"] = {"same_as": "original", "language": "en", "text_kind": "original_english_alias", "translation_performed": False}
            members["provenance.json"] = base.encoded(provenance)
        path = self.rewrite_zip(result, change)
        with self.assertRaisesRegex(base.AsrError, "invalid_english_alias"):
            multi.verify_pair(path)

    def test_rehashed_invalid_unicode_offsets_rejected(self):
        result, _ = self.run_fake()
        def change(members):
            segments = json.loads(members["original/segments.json"])
            segments["segments"][0]["char_end"] += 1
            members["original/segments.json"] = base.encoded(segments)
            provenance = json.loads(members["provenance.json"])
            provenance["text_variants"]["original"]["segments_sha256"] = hashlib.sha256(members["original/segments.json"]).hexdigest()
            members["provenance.json"] = base.encoded(provenance)
        path = self.rewrite_zip(result, change)
        with self.assertRaisesRegex(base.AsrError, "variant_text_offsets"):
            multi.verify_pair(path)

    def test_path_traversal_member_rejected(self):
        result, _ = self.run_fake()
        path = self.rewrite_zip(result, lambda members: members.update({"../escape.txt": b"no"}))
        with self.assertRaisesRegex(base.AsrError, "paired_member_set"):
            multi.verify_pair(path)

    def test_rehashed_provenance_cannot_change_source_identity(self):
        result, _ = self.run_fake()
        def change(members):
            provenance = json.loads(members["provenance.json"])
            provenance["source_audio"]["drive_id"] = "different-object"
            members["provenance.json"] = base.encoded(provenance)
        path = self.rewrite_zip(result, change)
        with self.assertRaisesRegex(base.AsrError, "paired_identity_provenance"):
            multi.verify_pair(path)

    def test_vad_receives_options_object_not_untyped_dict(self):
        package = ModuleType("faster_whisper"); package.__path__ = []
        vad = ModuleType("faster_whisper.vad")
        vad.VadOptions = lambda **kwargs: SimpleNamespace(**kwargs)
        vad.get_speech_timestamps = Mock(return_value=[])
        runtime = object.__new__(multi.Runtime)
        runtime.np = SimpleNamespace(empty=lambda *args, **kwargs: fixtures.Audio(0), float32=object())
        with patch.dict(sys.modules, {"faster_whisper": package, "faster_whisper.vad": vad}):
            _audio, seconds = runtime.speech(fixtures.Audio(1))
        self.assertEqual(seconds, 0)
        self.assertEqual(vad.get_speech_timestamps.call_args.args[1].min_silence_duration_ms, 500)

    def test_fresh_telemetry_fallback_is_observed_and_recorded(self):
        runtime = Mock()
        runtime.sample.side_effect = RuntimeError("unavailable")
        runtime.fallback_sample.return_value = {"gpu_percent": 37, "vram_bytes": 100, "temperature_c": 56, "backend": "nvidia-smi-nvml"}
        monitor = multi.Monitor(runtime, lambda: None, max_vram=1000)
        try:
            monitor.begin()
            monitor.guard()
        finally:
            telemetry = monitor.finish()
        self.assertGreaterEqual(telemetry["fallback_samples"], 1)
        self.assertEqual(telemetry["peak_gpu_percent"], 37)
        self.assertGreaterEqual(telemetry["telemetry_error_count"], 1)

    def test_unavailable_smi_values_are_never_treated_as_idle(self):
        runtime = object.__new__(multi.Runtime)
        with patch.object(multi.shutil, "which", return_value="nvidia-smi"), patch.object(multi.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="N/A, N/A, N/A\n")) as call:
            with self.assertRaises(ValueError):
                runtime.fallback_sample()
        self.assertEqual(call.call_args.kwargs["timeout"], 5)

    def test_both_telemetry_backends_missing_stops_without_zero_sample(self):
        runtime = Mock(); runtime.fallback_sample.side_effect = RuntimeError("unavailable")
        monitor = multi.Monitor(runtime, lambda: None)
        monitor.start = 0
        with patch.object(multi.time, "monotonic", side_effect=[0, 11]):
            with self.assertRaisesRegex(base.AsrError, "telemetry_unavailable"):
                monitor.guard()
        self.assertFalse(monitor.samples)

    def test_symlink_member_rejected_without_extracting(self):
        result, _ = self.run_fake()
        path = Path(result["bundle"]["path"])
        with zipfile.ZipFile(path) as archive:
            members = [(x, archive.read(x.filename)) for x in archive.infolist()]
        with zipfile.ZipFile(path, "w") as archive:
            for info, data in members:
                if info.filename == "original/transcript.txt":
                    info.create_system = 3
                    info.external_attr = 0o120777 << 16
                archive.writestr(info, data)
        with self.assertRaisesRegex(base.AsrError, "bundle_link_or_directory"):
            multi.verify_pair(path)

    def test_local_pair_resume_does_not_repeat_semantic_transcription(self):
        result, _ = self.run_fake()
        runtime = Runtime()
        again, runtime = self.run_fake(runtime)
        self.assertEqual(again["run_id"], result["run_id"])
        self.assertFalse(runtime.calls)

    def test_publisher_requires_remote_proof_and_never_deletes_sources(self):
        result, _ = self.run_fake()
        path = Path(result["bundle"]["path"]).parent / "receipt.json"
        parent = self.job["audio"]["remote"].rpartition("/")[0]
        remote = f"{parent}/{self.video}/ASR/{result['run_id']}/{result['run_id']}.zip"
        drive = Mock()
        drive.stat.return_value = {"ID": "result", "Size": result["bundle"]["bytes"], "Hashes": {"md5": "0" * 32}}
        with self.assertRaisesRegex(base.AsrError, "result_drive_proof"):
            multi.publish_result(path, remote, drive)
        self.assertFalse((self.root / "sync/asr_manifest.jsonl").exists())
        self.assertTrue(self.audio.exists())
        drive.stat.return_value["Hashes"]["md5"] = result["bundle"]["md5"]
        record = multi.publish_result(path, remote, drive)
        self.assertEqual(record["output_contract"], multi.CONTRACT)
        self.assertEqual(record["quality_state"], "unreviewed_asr")
        self.assertEqual(set(record["text_variants"]), {"original", "english"})
        self.assertEqual(record["metrics"]["audio_seconds"], 90)
        self.assertTrue(self.audio.exists())


if __name__ == "__main__":
    unittest.main()
