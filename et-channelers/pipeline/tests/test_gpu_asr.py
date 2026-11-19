"""No GPU/network imports: lease, integrity, versioning and bounded-output checks."""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gpu_asr as asr


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class PinnedRepositoryArtifactTests(unittest.TestCase):
    def test_dependency_lock_retains_the_exact_published_hash(self):
        pinned = json.loads(asr.PROVENANCE_PATH.read_text(encoding='utf-8'))
        self.assertEqual(asr.hashes(asr.DEFAULT_LOCK)['sha256'], pinned['requirements_lock_sha256'])

    def test_isolated_cli_adds_only_repository_helpers_without_gpu_imports(self):
        script = str(Path(asr.__file__).resolve())
        program = ("import runpy,sys; sys.argv=[sys.argv[1],'--help']; "
                   "script=sys.argv[0]\n"
                   "try: runpy.run_path(script,run_name='__main__')\n"
                   "except SystemExit as exc: assert exc.code==0\n"
                   "import importlib.util; assert importlib.util.find_spec('gpu_asr_queue') is not None\n"
                   "assert not {'faster_whisper','ctranslate2','pynvml'} & set(sys.modules)\n")
        result = subprocess.run([sys.executable, '-I', '-c', program, script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class Audio:
    def __init__(self, seconds=1):
        self.samples = int(seconds * asr.SAMPLE_RATE)
    def __len__(self):
        return self.samples


class FakeRuntime:
    def __init__(self, *_args):
        self.model = SimpleNamespace(model=SimpleNamespace(device="cuda", compute_type="int8_float16"))
        self.dependencies = {"test": "1"}
        self.closed = False
    def sample(self):
        return {"gpu_percent": 10, "vram_bytes": 100, "temperature_c": 40}
    def windows(self, _path, _duration):
        yield 0, Audio()
    def transcribe(self, _audio):
        words = [SimpleNamespace(start=0, end=.4, word=" hello", probability=.9),
                 SimpleNamespace(start=.4, end=.9, word=" world", probability=.8)]
        return iter([SimpleNamespace(start=0, end=.9, text=" hello world", words=words,
                                     avg_logprob=-.1, no_speech_prob=.01, compression_ratio=1)]), SimpleNamespace(duration_after_vad=.9)
    def close(self):
        self.closed = True


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.video = "abcdefghijk"
        self.future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        model_dir = self.root / "models/pinned"
        model_dir.mkdir(parents=True)
        (model_dir / "model.bin").write_bytes(b"pinned model")
        self.lock = self.root / "requirements.lock"
        self.lock.write_text("test-package==1\n")
        self.model = {"repository": "test/model", "revision": "a" * 40,
                      "files": [{"file": "model.bin", **{k:v for k,v in asr.hashes(model_dir / "model.bin").items() if k != "md5"}}]}
        self.pinned = self.root / "pinned.json"
        write(self.pinned, {"model": self.model, "requirements_lock_sha256": asr.hashes(self.lock)["sha256"], "packages": []})
        self.addCleanup(patch.stopall)
        patch.object(asr, "PROVENANCE_PATH", self.pinned).start()
        receipt = self.root / "model-receipt.json"
        write(receipt, {"status": "model_verified", "source": self.model, "files": self.model["files"]})
        self.settings = asr.Settings(self.root, model_dir, receipt, "gpu-test", "owner", [self.root], self.lock)
        self.gpu = {"schema_version": 1, "state": "active", "lease_id": "gpu-test", "owner": "owner",
                    "exclusive_owner": True, "device_index": 0, "cpu_fallback_allowed": False,
                    "additional_models_allowed": False, "expires_at": self.future, "max_vram_bytes": 1000,
                    "rolling_utilization_target": .7}
        write(self.root / "sync/gpu_lease.json", self.gpu)
        self.audio = self.root / "asr/input" / self.video / (self.video + ".webm")
        self.audio.parent.mkdir(parents=True)
        self.audio.write_bytes(b"native audio bytes")
        self.metadata = self.audio.with_suffix(".info.json")
        write(self.metadata, {"source": {"video_id": self.video}, "languages": {"audio": "en-US"}})
        audio_proof = {**asr.hashes(self.audio), "drive_id": "audio-id", "remote": f"test:Audio/person/Videos/{self.video}.webm"}
        meta_proof = {**asr.hashes(self.metadata), "drive_id": "meta-id", "remote": f"test:Audio/person/Videos/{self.video}.info.json"}
        self.source_lease_path = self.root / "asr/leases/source.json"
        self.source_lease = {"schema_version": 1, "status": "active", "phase": "input_verified_waiting_gpu_lease",
                             "lease_id": "source-test", "video_id": self.video, "expires_at": self.future,
                             "private_path": str(self.audio), "metadata_private_path": str(self.metadata),
                             "expected_bytes": audio_proof["bytes"], "expected_hashes": {k: audio_proof[k] for k in ["md5", "sha256"]},
                             "sourceDriveID": "audio-id"}
        write(self.source_lease_path, self.source_lease)
        self.job = {"job_id": "job-one", "video_id": self.video, "audio": audio_proof, "metadata": meta_proof,
                    "duration_seconds": 1, "source": {"channel_dir": "person"}, "caption": {"state": "pending_caption_source"},
                    "desired_model": {"repository": self.model["repository"], "revision": self.model["revision"], "device": "cuda"},
                    "requested_output": {"task": "transcribe", "translate": False}}
        self.admission = {"schema_version": 1, "state": "input_verified_waiting_gpu_lease", "job_id": "job-one",
                          "video_id": self.video, "language": {"code": "en-US", "basis": "verified_source_metadata.languages.audio"},
                          "source_lease": str(self.source_lease_path), "source_lease_id": "source-test", "job": self.job,
                          "verified_input_objects": [{"kind": kind, "private_path": str(path), "source": proof,
                                                      "local": {k: proof[k] for k in ["bytes", "md5", "sha256"]}}
                                                     for kind, path, proof in [("audio", self.audio, audio_proof), ("metadata", self.metadata, meta_proof)]]}
        self.admission_path = self.root / "asr/jobs/admission.json"
        write(self.admission_path, self.admission)

    def run_fake(self, runtime=FakeRuntime):
        with patch.object(asr, "inventory", return_value={"managed_bytes": 100}):
            return asr.run_jobs(self.settings, [self.admission_path], runtime_factory=runtime)[0]

    def test_import_does_not_import_optional_libraries_or_change_environment(self):
        code = "import os,sys; before=dict(os.environ); import gpu_asr; assert dict(os.environ)==before; assert not {'ctranslate2','faster_whisper','numpy','pynvml','av'}&set(sys.modules)"
        subprocess.run([sys.executable, "-c", code], cwd=asr.HERE, check=True, capture_output=True)

    def test_lease_owner_expiry_and_cpu_policy_fail_closed(self):
        for update, code in [({"owner": "other"}, "gpu_lease_owner"),
                             ({"expires_at": "2000-01-01T00:00:00+00:00"}, "gpu_lease_expired"),
                             ({"cpu_fallback_allowed": True}, "gpu_lease_policy")]:
            write(self.root / "sync/gpu_lease.json", {**self.gpu, **update})
            with self.assertRaisesRegex(asr.AsrError, code):
                asr.gpu_lease(self.settings)

    def test_kernel_lock_excludes_second_owner(self):
        with asr.kernel_lock(self.root / "gpu.lock"):
            with self.assertRaisesRegex(asr.AsrError, "gpu_owner_busy"):
                with asr.kernel_lock(self.root / "gpu.lock"):
                    pass

    def test_model_bytes_must_match_pinned_source_and_receipt(self):
        asr.model_proof(self.settings)
        (self.settings.model_dir / "model.bin").write_bytes(b"changed model")
        with self.assertRaisesRegex(asr.AsrError, "model_hash"):
            asr.model_proof(self.settings)

    def test_environment_lock_hash_is_required(self):
        self.lock.write_text("different==2")
        with self.assertRaisesRegex(asr.AsrError, "environment_lock_hash"):
            asr.model_proof(self.settings)

    def test_changed_source_fails_before_loading_gpu(self):
        self.audio.write_bytes(b"altered")
        factory = Mock()
        with self.assertRaisesRegex(asr.AsrError, "source_hash"):
            self.run_fake(factory)
        factory.assert_not_called()

    def test_source_lease_must_match_audio_hash_and_identity(self):
        self.source_lease["expected_hashes"]["sha256"] = "f" * 64
        write(self.source_lease_path, self.source_lease)
        with self.assertRaisesRegex(asr.AsrError, "source_lease_hash"):
            asr.validate_admission(self.settings, self.admission_path)

    def test_unverified_language_is_not_assumed_english(self):
        self.admission["language"]["code"] = "fr"
        write(self.admission_path, self.admission)
        with self.assertRaisesRegex(asr.AsrError, "english_not_proven"):
            asr.validate_admission(self.settings, self.admission_path)

    def test_no_cpu_fallback_even_when_runtime_returns_cpu_model(self):
        runtime = FakeRuntime()
        runtime.model.model.device = "cpu"
        with self.assertRaisesRegex(asr.AsrError, "cpu_fallback_forbidden"):
            self.run_fake(Mock(return_value=runtime))
        self.assertTrue(runtime.closed)
        self.assertTrue(self.audio.exists())

    def test_versioned_bundle_is_idempotent_and_preserves_sources(self):
        factory = Mock(side_effect=FakeRuntime)
        receipt = self.run_fake(factory)
        repeated = self.run_fake(factory)
        self.assertEqual(receipt["run_id"], repeated["run_id"])
        self.assertEqual(factory.call_count, 1)
        self.assertTrue(self.audio.exists())
        verified = asr.verify_bundle(receipt["bundle"]["path"], receipt["bundle"])
        self.assertFalse(verified["provenance"]["quality"]["accuracy_claimed"])
        self.assertEqual(verified["provenance"]["source_audio"], self.job["audio"])

    def test_model_config_worker_or_environment_changes_change_identity(self):
        model = asr.model_proof(self.settings)
        original = asr.run_identity(self.admission, model, "env", "worker")[0]
        variants = [asr.run_identity(self.admission, {**model, "revision": "b" * 40}, "env", "worker")[0],
                    asr.run_identity(self.admission, model, "env2", "worker")[0],
                    asr.run_identity(self.admission, model, "env", "worker2")[0],
                    asr.run_identity(self.admission, model, "env", "worker", {"beam_size": 1})[0]]
        self.assertTrue(all(x != original for x in variants))

    def test_word_and_segment_character_offsets_match_exact_text(self):
        result, text, _ = asr.collect_segments(FakeRuntime(), self.audio, 1, lambda: None)
        for segment in result["segments"]:
            self.assertEqual(text[segment["char_start"]:segment["char_end"]], segment["text"])
            for word in segment["words"]:
                self.assertEqual(text[word["char_start"]:word["char_end"]], word["word"])

    def test_oversized_decode_window_is_rejected(self):
        runtime = FakeRuntime()
        runtime.windows = Mock(return_value=iter([(0, Audio(31))]))
        with self.assertRaisesRegex(asr.AsrError, "decode_window_gap"):
            asr.collect_segments(runtime, self.audio, 31, lambda: None)

    def test_stale_gpu_telemetry_prevents_more_inference(self):
        monitor = asr.Monitor(lambda: {}, lambda: None)
        monitor.start = time.monotonic() - 10
        monitor.samples.append({"elapsed_s": 0, "gpu_percent": 0, "vram_bytes": 1, "temperature_c": 30})
        with self.assertRaisesRegex(asr.AsrError, "telemetry_stale"):
            monitor.guard()

    def test_bundle_changed_after_receipt_is_rejected(self):
        receipt = self.run_fake()
        path = Path(receipt["bundle"]["path"])
        with path.open("ab") as output:
            output.write(b"changed")
        with self.assertRaisesRegex(asr.AsrError, "bundle_hash"):
            asr.verify_bundle(path, receipt["bundle"])

    def test_missing_drive_id_retains_inputs_and_does_not_journal(self):
        receipt = self.run_fake()
        remote = f"test:Audio/person/Videos/{self.video}/ASR/{receipt['run_id']}/{receipt['run_id']}.zip"
        drive = Mock()
        drive.stat.return_value = {"Size": receipt["bundle"]["bytes"], "Hashes": {"md5": receipt["bundle"]["md5"]}}
        receipt_path = Path(receipt["bundle"]["path"]).parent / "receipt.json"
        with self.assertRaisesRegex(asr.AsrError, "result_drive_proof"):
            asr.publish_result(receipt_path, remote, drive)
        self.assertTrue(self.audio.exists())
        self.assertFalse((self.root / "sync/asr_manifest.jsonl").exists())

    def test_verified_upload_journals_source_proof_but_does_not_delete_inputs(self):
        receipt = self.run_fake()
        remote = f"test:Audio/person/Videos/{self.video}/ASR/{receipt['run_id']}/{receipt['run_id']}.zip"
        drive = Mock()
        drive.stat.return_value = {"ID": "result-drive-id", "Size": receipt["bundle"]["bytes"], "Hashes": {"md5": receipt["bundle"]["md5"]}}
        record = asr.publish_result(Path(receipt["bundle"]["path"]).parent / "receipt.json", remote, drive)
        self.assertEqual(record["status"], "verified")
        self.assertEqual(record["source_audio_sha256"], self.job["audio"]["sha256"])
        self.assertEqual(record["quality_state"], "unreviewed_asr")
        self.assertEqual(record["metrics"], asr.verify_bundle(receipt["bundle"]["path"])["provenance"]["metrics"])
        self.assertEqual(json.loads((self.root / "sync/asr_manifest.jsonl").read_text()), record)
        self.assertTrue(self.audio.exists())

    def test_modified_receipt_identity_cannot_relabel_a_valid_bundle(self):
        receipt = self.run_fake()
        receipt_path = Path(receipt["bundle"]["path"]).parent / "receipt.json"
        remote = f"test:Audio/person/Videos/{self.video}/ASR/{receipt['run_id']}/{receipt['run_id']}.zip"
        for key, replacement in [("video_id", "ABCDEFGHIJK"), ("job_id", "different-job"),
                                 ("model", {"repository": "different"}), ("config_sha256", "f" * 64),
                                 ("artifact_manifest_sha256", "f" * 64)]:
            drive = Mock()
            write(receipt_path, {**receipt, key: replacement})
            with self.assertRaisesRegex(asr.AsrError, "result_identity_provenance"):
                asr.publish_result(receipt_path, remote, drive)
            drive.copy.assert_not_called()

    def test_wrong_result_location_is_rejected_before_upload(self):
        receipt = self.run_fake()
        misplaced = self.root / "misplaced.json"
        write(misplaced, receipt)
        drive = Mock()
        with self.assertRaisesRegex(asr.AsrError, "result_receipt_location"):
            asr.publish_result(misplaced, "test:other", drive)
        drive.copy.assert_not_called()

    def test_missing_private_root_is_rejected_without_inferring_parent_depth(self):
        receipt = self.run_fake()
        receipt.pop('private_root')
        misplaced = self.root / 'shallow.json'
        write(misplaced, receipt)
        drive = Mock()
        with self.assertRaisesRegex(asr.AsrError, 'result_receipt_location'):
            asr.publish_result(misplaced, 'test:other', drive)
        drive.copy.assert_not_called()

    def test_incomplete_managed_inventory_fails_closed(self):
        with self.assertRaisesRegex(asr.AsrError, "incomplete_storage_inventory"):
            asr.inventory(self.settings)

    def test_inventory_reserves_other_owners_and_requires_collector_stop(self):
        write(self.root / "sync/analysis_resource_plan.json", {"collector_dispatch_allowed": False,
              "accounting_cap_bytes": 100_000_000, "reservations": [{"state": "active", "max_bytes": 99_999_999}]})
        (self.root / "sync/STOP_DRIVE_INGEST").touch()
        with patch.object(asr, "HERE", self.root / "repo/pipeline"), patch.object(sys, "prefix", str(self.root)):
            with self.assertRaisesRegex(asr.AsrError, "managed_storage_admission"):
                asr.inventory(self.settings, extra=1)
            (self.root / "sync/STOP_DRIVE_INGEST").unlink()
            with self.assertRaisesRegex(asr.AsrError, "collector_not_parked"):
                asr.inventory(self.settings, extra=1)

    def test_managed_cap_cannot_exceed_eighteen_gb(self):
        with self.assertRaisesRegex(asr.AsrError, "managed_cap"):
            asr.Settings(self.root, self.settings.model_dir, self.settings.model_receipt, "gpu", "owner", [self.root], self.lock,
                         max_managed_bytes=18_000_000_001)

    def test_postrun_storage_honors_the_physical_reserve_after_existing_and_new_growth(self):
        write(self.root / "sync/analysis_resource_plan.json", {"collector_dispatch_allowed": False,
              "accounting_cap_bytes": 18_000_000_000, "reservations": [{"state": "active", "max_bytes": 30}]})
        (self.root / "sync/STOP_DRIVE_INGEST").touch()
        with patch.object(asr, "HERE", self.root / "repo/pipeline"), patch.object(sys, "prefix", str(self.root)):
            with patch.object(asr.shutil, "disk_usage", return_value=type("Disk", (), {"free": 12_000_000_079})):
                with self.assertRaisesRegex(asr.AsrError, "physical_disk_reserve"):
                    asr.inventory(self.settings, extra=50)
            with patch.object(asr.shutil, "disk_usage", return_value=type("Disk", (), {"free": 12_000_000_080})):
                result = asr.inventory(self.settings, extra=50)
                self.assertEqual(result["physical_free_floor_bytes"], 12_000_000_000)


if __name__ == "__main__":
    unittest.main()
