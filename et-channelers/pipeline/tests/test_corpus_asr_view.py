"""Fixture ZIP verification and private corpus mapping; no inference/source."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from pipeline import corpus_asr_view as corpus
from pipeline import gpu_asr as base
from pipeline import gpu_asr_multilingual as multi
from pipeline.corpus_concordance import Concordance


class AsrViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = SimpleNamespace(root=self.root, output_root=self.root / "asr/results")
        self.audio = {"bytes": 128, "md5": "a" * 32, "sha256": "a" * 64, "drive_id": "audio-1", "remote": "test:audio/example.m4a"}
        self.meta = {"bytes": 64, "md5": "b" * 32, "sha256": "b" * 64, "drive_id": "metadata-1", "remote": "test:audio/example.info.json"}
        self.model = {"model_sha256": "c" * 64, "repository": "fixture/model", "revision": "d" * 40}
        self.admission = {"video_id": "example_123", "job_id": "job-one", "source_lease_id": "source-one",
                          "job": {"audio": self.audio, "metadata": self.meta}}
        self.quality = {"accuracy_claimed": False, "human_reviewed": False, "speech_coverage_validated": False,
                        "host_guest_identity_assigned": False}

    @staticmethod
    def document(lines, language="en", paired=False):
        text = "\n".join(lines) + "\n"
        cursor, rows = 0, []
        for index, line in enumerate(lines):
            rows.append({"id": 7 + index * 4, "start": index * 3, "end": index * 3 + 3.4,
                         "text": line, "char_start": cursor, "char_end": cursor + len(line),
                         "words": [{"word": line, "char_start": cursor, "char_end": cursor + len(line),
                                    "start": index * 3, "end": index * 3 + 3, "probability": .9}]})
            cursor += len(line) + 1
        value = {"schema_version": 1, "language": language, "timebase": "source_audio_seconds", "duration_seconds": 7,
                 "segments": rows, "speaker_identity": "unassigned", "human_reviewed": False}
        if paired:
            value["character_offset_unit"] = "unicode_code_points"
        return value, text

    def bundle(self, *, language=None, alias=False):
        p = {"job_id": "job-one", "source_video_id": "example_123", "source_lease_id": "source-one", "channel_dir": "fixture-person",
             "source_audio": self.audio, "source_metadata": self.meta, "model": self.model, "compute": {"cpu_asr_fallback": False},
             "metrics": {"audio_seconds": 7}, "quality": self.quality, "worker_sha256": "d" * 64,
             "environment_lock_sha256": "e" * 64, "source_admission_sha256": "f" * 64}
        if language is None:
            run, identity = base.run_identity(self.admission, self.model, "e" * 64, "d" * 64)
            p.update(run_id=run, identity=identity, config=base.CONFIG)
            doc, text = self.document(["🌙 528 Hz", "control group"])
            with patch.object(base, "inventory", return_value={}), patch.object(base.CudaRuntime, "__init__", side_effect=AssertionError("GPU forbidden")):
                receipt = base.write_bundle(self.settings, self.admission, run, doc, text, {}, p)
        else:
            original = {**base.CONFIG, "language": language, "task": "transcribe"}
            configs = {"original": original}
            if not alias:
                configs["english"] = {**base.CONFIG, "language": language, "task": "translate"}
            identity = {"output_contract": multi.CONTRACT, "source_audio": self.audio, "source_metadata": self.meta,
                        "model": self.model, "proposal_sha256": "1" * 64, "worker_sha256": "d" * 64,
                        "environment_lock_sha256": "e" * 64, "configs": configs}
            run = "asr-" + base.fingerprint(identity)[:24]
            p.update(run_id=run, identity=identity, proposal_sha256="1" * 64)
            lines = ["🌙 528 Hz", "control group"] if language == "en" else ["こんにちは 🌙", "周波数 528 Hz"]
            doc, text = self.document(lines, language, True)
            variants = {"original": (doc, text, original)}
            if not alias:
                eng, translated = self.document(["🌙 528 Hz", "control group"], "en", True)
                variants["english"] = (eng, translated, configs["english"])
            with patch.object(base, "inventory", return_value={}), patch.object(multi.Runtime, "__init__", side_effect=AssertionError("GPU forbidden")):
                receipt = multi.write_pair(self.settings, self.admission, run, variants, {}, p)
        return Path(receipt["bundle"]["path"]), receipt, doc

    def rewrite(self, path, receipt, edit):
        with zipfile.ZipFile(path) as archive:
            parts = {name: archive.read(name) for name in archive.namelist()}
        edit(parts)
        manifest = json.loads(parts["artifact_manifest.json"])
        manifest["files"] = [{"file": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                             for name, raw in parts.items() if name != "artifact_manifest.json"]
        parts["artifact_manifest.json"] = base.encoded(manifest)
        with zipfile.ZipFile(path, "w") as archive:
            for name, raw in parts.items():
                archive.writestr(name, raw)
        receipt["bundle"].update(base.hashes(path))
        receipt["artifact_manifest_sha256"] = hashlib.sha256(parts["artifact_manifest.json"]).hexdigest()

    def test_english_raw_codepoints_times_and_concordance_roundtrip(self):
        path, receipt, document = self.bundle()
        views = corpus.asr_views(path, receipt)
        view = views["english"]
        self.assertEqual(view["raw_segments"], document)
        self.assertEqual(view["segments"][1]["char_start"], len("🌙 528 Hz\n"))
        self.assertEqual(view["segments"][0]["time_end"], 3.4)
        self.assertEqual(view["source_edition_id"], "sha256:" + self.audio["sha256"])
        self.assertEqual(view["text_version_id"], corpus.asr_views(path, receipt)["english"]["text_version_id"])
        self.assertIsNone(view["speaker_attribution"])
        self.assertFalse(view["speech_coverage_verified"])
        hit = next(r for r in Concordance().records(view) if r.get("rule_id") == "frequency_numeric_hz")
        self.assertEqual(view["text"][hit["start_codepoint"]:hit["end_codepoint"]], "528 Hz")
        self.assertEqual(hit["raw_segment_ids"], ["segments.json:7"])

    def test_published_zip_survives_retirement_of_the_local_worker_receipt(self):
        creator, video = "fixture-person", "example_123"
        parent = f"test:audio/{creator}/Videos"
        self.audio["remote"] = f"{parent}/{video}.m4a"
        self.meta["remote"] = f"{parent}/{video}.info.json"
        edition = dict(self.audio, channel_dir=creator, video_id=video, status="deleted",
                       path=f"audio/{creator}/Videos/{video}.m4a", metadata=self.meta, tab="videos")
        path, local, _ = self.bundle()
        run = local["run_id"]
        published = {key: local[key] for key in ("run_id", "job_id", "source_lease_id", "model", "config_sha256",
                                                  "source_metadata", "artifact_manifest_sha256")}
        published.update(base.hashes(path), status="verified", artifact_kind="asr_bundle", quality_state="unreviewed_asr",
                         channel_dir=creator, video_id=video, drive_id="zip-id", metrics={"audio_seconds": 7},
                         source_audio_drive_id=self.audio["drive_id"], source_audio_sha256=self.audio["sha256"],
                         remote=f"{parent}/{video}/ASR/{run}/{run}.zip")
        views = corpus.asr_views(path, published, edition_receipt=edition, remote="test:audio")
        self.assertEqual(views, corpus.asr_views(path, local, edition_receipt=edition))
        with self.assertRaisesRegex(ValueError, "archived_asr_recording_receipt"):
            corpus.asr_views(path, published)
        with self.assertRaisesRegex(ValueError, "archived_asr_recording_receipt"):
            corpus.asr_views(path, dict(published, source_audio_drive_id="different"), edition_receipt=edition, remote="test:audio")
        with self.assertRaisesRegex(ValueError, "archived_asr_provenance"):
            corpus.asr_views(path, dict(published, metrics={}), edition_receipt=edition, remote="test:audio")

    def test_dated_english_archive_with_separate_drive_receipt_and_no_word_offsets(self):
        video, creator, run = "example_123", "fixture-person", "asr-20261117T023456Z-1234abcd"
        parent = f"test:audio/{creator}/Videos"
        self.audio["remote"] = f"{parent}/{video}.m4a"
        self.meta["remote"] = f"{parent}/{video}.info.json"
        doc, text = self.document(["Earlier recording"])
        for word in doc["segments"][0]["words"]:
            del word["char_start"], word["char_end"]
        quality = dict(self.quality, human_reference_available=False)
        del quality["human_reviewed"]
        p = {"run_id": run, "status": "local_transcription_complete_unreviewed", "source_video_id": video,
             "source_lease_id": "source-one", "source_audio": self.audio, "source_metadata": self.meta,
             "metrics": {"audio_seconds": 7}, "config": {"language": "en", "task": "transcribe"},
             "model": self.model, "compute": {"cpu_asr_fallback": False}, "quality": quality, "job_id": "job-one"}
        with patch.object(base, "inventory", return_value={}):
            written = base.write_bundle(self.settings, self.admission, run, doc, text, {}, p)
        bundle = Path(written["bundle"]["path"])
        local = {key: p[key] for key in ("run_id", "job_id", "model", "source_lease_id", "metrics", "status")}
        local.update(video_id=video, bundle=written["bundle"], quality_state="unreviewed_asr",
                     source_audio_sha256=self.audio["sha256"], provenance_sha256=hashlib.sha256(base.encoded(p)).hexdigest(),
                     config_sha256=hashlib.sha256(json.dumps(p["config"], sort_keys=True).encode()).hexdigest())
        edition = dict(self.audio, video_id=video, channel_dir=creator, tab="videos",
                       path=f"audio/{creator}/Videos/{video}.m4a", status="deleted", metadata=self.meta)
        published = dict(local, **base.hashes(bundle), drive_id="archive", status="verified", channel_dir=creator,
                         source_audio_drive_id=self.audio["drive_id"], source_metadata_drive_id=self.meta["drive_id"],
                         source_metadata_sha256=self.meta["sha256"], artifact_kind="asr_bundle",
                         remote=f"{parent}/{video}/ASR/{run}/{run}.zip")
        def view():
            return corpus.asr_views(bundle, local, edition_receipt=edition, drive_receipt=published, remote="test:audio")["english"]
        result = view()
        self.assertEqual(result["text"], text)
        self.assertEqual(result["channel_dir"], creator)
        self.assertNotIn("char_start", result["segments"][0]["words"][0])
        earliest = {k: v for k, v in published.items() if k not in {
            "job_id", "model", "provenance_sha256", "config_sha256", "source_metadata_drive_id", "source_metadata_sha256",
            "bundle"}}
        def archived(record=earliest, audio=edition):
            return corpus.asr_views(bundle, record, edition_receipt=audio, remote="test:audio")["english"]
        self.assertEqual(result, archived())
        with self.assertRaisesRegex(ValueError, "dated_asr_run_identity"):
            archived(dict(earliest, source_lease_id="wrong-lease"))
        with self.assertRaisesRegex(ValueError, "dated_asr_run_identity"):
            archived(dict(earliest, job_id="different"))
        with self.assertRaisesRegex(ValueError, "dated_asr_archive_binding"):
            archived(dict(earliest, provenance_sha256="0" * 64))
        with self.assertRaisesRegex(ValueError, "asr_metadata_edition_mismatch"):
            archived(audio=dict(edition, metadata=dict(self.meta, sha256="0" * 64)))
        published["provenance_sha256"] = "a" * 64
        with self.assertRaisesRegex(ValueError, "dated_asr_archive_binding"):
            view()

    def test_japanese_original_and_separate_english_translation(self):
        path, receipt, _ = self.bundle(language="ja")
        views = corpus.asr_views(path, receipt)
        self.assertEqual(views["original"]["language"], "ja")
        self.assertIn("こんにちは", views["original"]["text"])
        self.assertNotEqual(views["original"]["text_version_id"], views["english"]["text_version_id"])
        self.assertTrue(views["english"]["translation_performed"])
        self.assertFalse(views["english"]["translation_semantics_verified"])
        with self.assertRaisesRegex(ValueError, "English"):
            list(Concordance().records(views["original"]))
        self.assertTrue(list(Concordance().records(views["english"])))

    def test_original_english_alias_reuses_version_and_never_claims_translation(self):
        path, receipt, _ = self.bundle(language="en", alias=True)
        views = corpus.asr_views(path, receipt)
        self.assertEqual(views["original"]["text_version_id"], views["english"]["text_version_id"])
        self.assertEqual(views["english"]["alias_of_variant"], "original")
        self.assertFalse(views["english"]["translation_performed"])
        self.assertEqual(views["english"]["source_kind"], "original_asr")

    def test_receipt_and_optional_edition_must_bind_same_actual_audio_objects(self):
        path, receipt, _ = self.bundle()
        row = {"video_id": "example_123", "channel_dir": "fixture-person", "status": "verified",
               **self.audio, "metadata": self.meta}
        view = corpus.asr_views(path, receipt, edition_receipt=row)["english"]
        self.assertEqual(view["edition_receipt_sha256"], base.fingerprint(row))
        row["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "audio_edition"):
            corpus.asr_views(path, receipt, edition_receipt=row)
        wrong = deepcopy(receipt);wrong["source_audio"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "receipt_provenance"):
            corpus.asr_views(path, wrong)

    def test_rehashed_semantic_byte_offsets_unmapped_text_and_timing_still_rejected(self):
        path, receipt, _ = self.bundle()
        def edit(parts):
            doc = json.loads(parts["segments.json"]);doc["segments"][1]["char_start"] += 1
            parts["segments.json"] = base.encoded(doc)
        self.rewrite(path, receipt, edit)
        with self.assertRaisesRegex(ValueError, "codepoint_mapping"):
            corpus.asr_views(path, receipt)

    def test_rehashed_word_times_and_speaker_claim_are_not_accepted(self):
        path, receipt, _ = self.bundle()
        original = path.read_bytes()
        changes = [("asr_word_codepoint_mapping", lambda d: d["segments"][0]["words"][0].update(char_start=1)),
                   ("asr_segment_times", lambda d: d["segments"][0].update(end=float("nan"))),
                   ("asr_segment_schema", lambda d: d.update(speaker_identity="host"))]
        for expected, change in changes:
            with self.subTest(expected=expected):
                path.write_bytes(original)
                current = deepcopy(receipt)
                def edit(parts):
                    doc = json.loads(parts["segments.json"]);change(doc)
                    parts["segments.json"] = json.dumps(doc).encode()
                self.rewrite(path, current, edit)
                with self.assertRaisesRegex(ValueError, expected):
                    corpus.asr_views(path, current)

    def test_qualified_edition_pair_checks_remote_extent_and_distinct_object_identity(self):
        path, receipt, _ = self.bundle()
        def wrapped(proof):
            return {"local_proof": {k: proof[k] for k in ("bytes", "md5", "sha256")},
                    "remote_proof": {k: proof[k] for k in ("bytes", "md5", "drive_id")}}
        row = {"status": "verified", "video_id": "example_123", "channel_dir": "fixture-person",
               "audio": wrapped(self.audio), "metadata": wrapped(self.meta)}
        self.assertIsNotNone(corpus.asr_views(path, receipt, edition_receipt=row)["english"]["edition_receipt_sha256"])
        row["metadata"]["remote_proof"]["bytes"] += 1
        with self.assertRaisesRegex(ValueError, "edition_remote_proof"):
            corpus.asr_views(path, receipt, edition_receipt=row)

    def test_verified_snapshot_is_not_reopened_between_integrity_and_mapping(self):
        path, receipt, _ = self.bundle()
        original = base.verify_bundle
        def verify(snapshot, expected):
            result = original(snapshot, expected)
            path.write_bytes(b"changed after snapshot")
            return result
        with patch.object(base, "verify_bundle", side_effect=verify):
            self.assertIn("528 Hz", corpus.asr_views(path, receipt)["english"]["text"])

    def test_unsafe_encrypted_or_link_member_not_accepted_by_legacy_verifier(self):
        path, receipt, _ = self.bundle()
        with zipfile.ZipFile(path) as archive:
            parts = {name: archive.read(name) for name in archive.namelist()}
        with zipfile.ZipFile(path, "w") as archive:
            for name, raw in parts.items():
                info = zipfile.ZipInfo(name)
                info.external_attr = (0o120777 if name == "segments.json" else 0o100600) << 16
                archive.writestr(info, raw)
        receipt["bundle"].update(base.hashes(path))
        with self.assertRaisesRegex(ValueError, "unsafe_asr_member"):
            corpus.asr_views(path, receipt)

    def test_private_isolated_cli_defaults_to_english_and_imports_no_gpu_packages(self):
        path, receipt, _ = self.bundle(language="ja")
        receipt_path = path.parent / "receipt.json"
        script = Path(corpus.__file__)
        code = "import runpy,sys;sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__');assert not {'numpy','av','pynvml','ctranslate2','faster_whisper'}&set(sys.modules)"
        result = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(script), "--root", str(self.root),
                                 "--receipt", str(receipt_path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual([x["variant"] for x in output["private_views"]], ["english"])
        self.assertEqual(len(list((self.root / "analysis/asr_views").rglob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
