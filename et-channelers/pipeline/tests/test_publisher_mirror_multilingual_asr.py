"""Offline German publisher pairing, lease, duration and publication contracts."""
import contextlib
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

from pipeline import publisher_mirror_multilingual_asr as m
from pipeline.tests import test_publisher_mirror_asr as source_fixtures


class Audio:
    def __init__(self, samples):
        self.samples = samples

    def __len__(self):
        return self.samples


class Runtime:
    def __init__(self):
        self.model = SimpleNamespace(model=SimpleNamespace(device="cuda", compute_type="int8_float16"), transcribe=self.transcribe)
        self.dependencies, self.calls, self.closed = {"fixture": "offline"}, [], False
        self.detected, self.probability, self.short_pass, self.empty_translation = "de", .98, False, False

    def windows(self, path, duration):
        total = round((duration - (4 if self.short_pass else 0)) * 16000)
        for start in range(0, total, 480000):
            yield start / 16000, Audio(min(480000, total - start))

    def speech(self, audio):
        return audio, len(audio) / 16000

    def detect(self, audio):
        return self.detected, self.probability, [(self.detected, self.probability), ("fr", .01)]

    def transcribe(self, audio, **config):
        self.calls.append(config)
        if self.empty_translation and config["task"] == "translate":
            return iter([]), SimpleNamespace(duration_after_vad=0)
        text = "Hallo" if config["task"] == "transcribe" else "Hello"
        word = SimpleNamespace(start=0, end=.2, word=text, probability=.98)
        segment = SimpleNamespace(start=0, end=.2, text=text, words=[word], avg_logprob=-.1, no_speech_prob=.01, compression_ratio=1)
        return iter([segment]), SimpleNamespace(duration_after_vad=len(audio) / 16000)

    def close(self):
        self.closed = True


class Heartbeat:
    def __init__(self, validate, wall_seconds):
        self.validate, self.counters = validate, {"calls": 0}

    def __call__(self, force=False):
        self.counters["calls"] += 1
        self.validate()


class Monitor:
    def __init__(self, runtime, guard, target, max_vram):
        self.guard = guard
        self.finished = False

    def begin(self):
        self.guard()

    def finish(self):
        self.finished = True
        return {"fixture": True}


class PublisherPairTests(unittest.TestCase):
    def setUp(self):
        self.fixture = source_fixtures.MirrorAsrTests("runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        (self.root / "sync").mkdir()
        self.fixture.feed_language = "de"
        self.fixture.item.update(audio_path=str(self.root / "asr/input/pair/audio.mp3"),
                                 provenance_path=str(self.root / "asr/input/pair/provenance.json"))
        self.fixture.write_fixture()
        self.item = self.fixture.item
        self.cohort, self.proposal = self.root / "cohort.json", self.root / "proposal.json"
        self.cohort.write_bytes(m.base.encoded({"items": [self.item]}))
        self.hb = SimpleNamespace(Heartbeat=Heartbeat, epoch=lambda value: float(value))
        self.helpers = patch.object(m.variant, "load_helpers", return_value=(self.hb, m.base, m.multi))
        self.helpers.start()
        self.addCleanup(self.helpers.stop)
        self.args = SimpleNamespace(pipeline=str(m.base.HERE), heartbeat_worker="fixture", cohort=str(self.cohort), output=str(self.proposal))
        m.prepare(self.args)
        self.prepared = m.variant.read(self.proposal)
        self.binding = m.binding_for(self.prepared, m.variant.sha(self.proposal))
        self.job = self.prepared["jobs"][0]
        self.audio = Path(self.item["audio_path"])
        self.audio.parent.mkdir(parents=True)
        self.audio.write_bytes(b"invented publisher audio")
        self.metadata = Path(self.item["provenance_path"])
        self.metadata.write_bytes(Path(self.item["provenance_reference_path"]).read_bytes())
        self.model = {"repository": self.prepared["model"]["repository"], "revision": self.prepared["model"]["revision"],
                      "model_sha256": next(x["sha256"] for x in self.prepared["model"]["files"] if x["file"] == "model.bin"),
                      "manifest_sha256": self.prepared["model_manifest_sha256"]}
        self.lease_path = self.root / "asr/leases/publisher-pair.json"
        self.source = {"schema_version": 1, "state": "active", "profile": m.PROFILE, "owner": "fixture-owner", "lease_id": "source-lease",
            "expires_at": 9999999999, "source_variant_id": self.job["variant_id"], "source_audio": self.job["audio"],
            "source_provenance": self.job["provenance"], "publisher_language_evidence_sha256": self.job["language"]["evidence_sha256"],
            "input_paths": [str(self.audio), str(self.metadata)], "native_youtube_bytes": False, m.BINDING_KEY: self.binding}
        m.base.atomic_json(self.lease_path, self.source)
        self.admission = {"variant_id": self.job["variant_id"], "source_lease_path": str(self.lease_path), "source_lease_id": "source-lease"}
        self.admissions = self.root / "admissions.json"
        self.admissions.write_bytes(m.base.encoded({"items": [self.admission]}))
        self.lock = self.root / "environment.lock"
        self.lock.write_bytes(b"fixture-environment")
        self.settings = SimpleNamespace(root=self.root, output_root=self.root / "asr/results", environment_lock=self.lock,
                                        gpu_owner="fixture-owner", gpu_lease_id="gpu-lease")
        self.settings_path = self.root / "settings.json"
        self.settings_path.write_text("{}", encoding="utf-8")
        self.args.proposal = str(self.proposal)
        self.args.proposal_sha256 = m.variant.sha(self.proposal)
        self.args.settings = str(self.settings_path)
        self.args.admissions = str(self.admissions)
        self.gpu = {m.BINDING_KEY: self.binding, "model": self.model, "expires_at": 9999999999,
                    "rolling_utilization_target": .7, "max_vram_bytes": 6500000000}

    def run_fake(self, runtime=None):
        runtime = runtime or Runtime()
        with patch.object(m.base, "Settings", return_value=self.settings), patch.object(m.base, "gpu_lease", return_value=self.gpu), \
                patch.object(m.base, "inventory", return_value={}), patch.object(m.multi, "model_proof", return_value=self.model), \
                patch.object(m.multi, "Monitor", Monitor):
            result = m.run(self.args, runtime_factory=lambda *_: runtime)
        return result, runtime

    def test_german_feed_preserved_and_large_model_pinned(self):
        job = self.job
        self.assertEqual(job["status"], "eligible")
        self.assertEqual(job["language"]["code"], "de")
        self.assertFalse(job["language"]["episode_language_independently_verified"])
        self.assertEqual(self.prepared["model"]["repository"], "Systran/faster-whisper-large-v3")
        self.assertEqual(self.prepared["model"]["revision"], "edaa852ec7e145841d8ffdb056a99866b5f0a478")

    def test_english_unknown_and_nonlexical_stay_outside_german_worker(self):
        for code in ("en", None):
            self.fixture.feed_language = code
            self.fixture.write_fixture()
            self.assertNotEqual(m.prepare_job(self.item)["status"], "eligible")
        self.fixture.feed_language = "de"
        self.fixture.mapped["claimed_light_language"] = True
        self.fixture.write_fixture()
        self.assertEqual(m.prepare_job(self.item)["status"], "held_language_review")

    def test_pair_contains_distinct_german_and_english_with_equal_full_passes(self):
        result, runtime = self.run_fake()
        receipt = result["receipt"]
        verified = m.verify_result(receipt)
        p = verified["provenance"]
        self.assertEqual(p["text_variants"]["original"]["language"], "de")
        self.assertEqual(p["text_variants"]["english"]["language"], "en")
        self.assertEqual({x["task"] for x in runtime.calls}, {"transcribe", "translate"})
        self.assertTrue(all(x["language"] == "de" for x in runtime.calls))
        self.assertEqual(p["metrics"]["tasks"]["original"]["decoded_samples"], round(61.3 * 16000))
        self.assertEqual(p["metrics"]["tasks"]["original"]["decoded_samples"], p["metrics"]["tasks"]["english"]["decoded_samples"])
        self.assertFalse(result["source_delete_allowed"])
        self.assertFalse(p["quality"]["speech_coverage_validated"])
        self.assertTrue(self.audio.exists() and self.metadata.exists() and runtime.closed)
        self.assertFalse((self.root / "sync/asr_manifest.jsonl").exists())

    def test_conflicting_language_or_low_confidence_holds_without_semantic_output(self):
        for detected, probability in (("en", .98), ("de", .4)):
            runtime = Runtime()
            runtime.detected, runtime.probability = detected, probability
            result, _ = self.run_fake(runtime)
            self.assertEqual(result["status"], "held")
            self.assertFalse(result["semantic_text_generated"])
            self.assertEqual(runtime.calls, [])
            self.assertTrue(self.audio.exists() and self.metadata.exists() and runtime.closed)
        self.assertTrue((self.root / "sync/publisher_variant_language_manifest.jsonl").exists())

    def test_short_decode_and_empty_translation_cannot_complete_pair(self):
        for field in ("short_pass", "empty_translation"):
            runtime = Runtime()
            setattr(runtime, field, True)
            with self.subTest(field=field), self.assertRaises(m.base.AsrError):
                self.run_fake(runtime)
            self.assertTrue(runtime.closed)
            self.assertFalse(list((self.root / "asr/results").glob("**/*.zip")))
            self.assertTrue(self.audio.exists())

    def test_wrong_source_lease_or_changed_input_fails_before_model_load(self):
        self.source["source_audio"] = {**self.source["source_audio"], "drive_id": "wrong-object"}
        m.base.atomic_json(self.lease_path, self.source)
        runtime = Runtime()
        with self.assertRaisesRegex(m.base.AsrError, "source_proof"):
            self.run_fake(runtime)
        self.assertFalse(runtime.closed)  # factory never called
        self.source["source_audio"] = self.job["audio"]
        m.base.atomic_json(self.lease_path, self.source)
        self.audio.write_bytes(b"changed")
        with self.assertRaisesRegex(m.base.AsrError, "input_hash"):
            self.run_fake()

    def test_changed_cohort_or_helper_pin_invalidates_proposal(self):
        self.cohort.write_bytes(self.cohort.read_bytes() + b" ")
        with self.assertRaisesRegex(m.base.AsrError, "cohort_hash"):
            self.run_fake()

    def test_publication_only_after_pair_proof_and_only_publisher_journal(self):
        result, _ = self.run_fake()
        receipt = result["receipt"]
        drive = SimpleNamespace(copy=Mock(), stat=Mock(return_value={"ID": "result-object", "Size": receipt["bundle"]["bytes"],
                                                                  "Hashes": {"MD5": receipt["bundle"]["md5"]}}))
        record = m.publish_result(result["receipt_path"], drive)
        self.assertEqual(record["output_contract"], "original-and-english-v1")
        self.assertFalse(record["changes_native_asr_count"])
        self.assertEqual(set(record["text_variants"]), {"original", "english"})
        self.assertTrue((self.root / "sync/publisher_variant_asr_manifest.jsonl").exists())
        self.assertFalse((self.root / "sync/asr_manifest.jsonl").exists())
        self.assertTrue(self.audio.exists() and self.metadata.exists())

    def test_upload_failure_or_missing_pair_retains_inputs_and_no_journal(self):
        result, _ = self.run_fake()
        receipt = result["receipt"]
        drive = SimpleNamespace(copy=Mock(), stat=Mock(return_value={"ID": "result-object", "Size": receipt["bundle"]["bytes"],
                                                                   "Hashes": {"MD5": "0" * 32}}))
        with self.assertRaisesRegex(m.base.AsrError, "drive_proof"):
            m.publish_result(result["receipt_path"], drive)
        self.assertFalse((self.root / "sync/publisher_variant_asr_manifest.jsonl").exists())
        self.assertTrue(self.audio.exists() and self.metadata.exists())
        path = Path(receipt["bundle"]["path"])
        with zipfile.ZipFile(path) as archive:
            members = {name: archive.read(name) for name in archive.namelist() if name != "english/transcript.txt"}
        with zipfile.ZipFile(path, "w") as archive:
            for name, raw in members.items():
                archive.writestr(name, raw)
        changed = copy.deepcopy(receipt)
        changed["bundle"].update(m.base.hashes(path))
        with self.assertRaises(m.base.AsrError):
            m.verify_result(changed)

    def test_mutated_association_receipt_is_rejected_before_upload(self):
        result, _ = self.run_fake()
        path = Path(result["receipt_path"])
        receipt = m.variant.read(path)
        receipt["associated_youtube_id"] = "other1234567"
        m.base.atomic_json(path, receipt)
        drive = SimpleNamespace(copy=Mock(), stat=Mock())
        with self.assertRaisesRegex(m.base.AsrError, "receipt_identity"):
            m.publish_result(path, drive)
        drive.copy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
