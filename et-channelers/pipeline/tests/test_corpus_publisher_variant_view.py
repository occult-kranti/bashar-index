"""Exercise publisher archive readers with invented text. No model or network is used."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from pipeline import corpus_publisher_variant_view as reader
from pipeline import gpu_asr, gpu_asr_multilingual, publisher_mirror, youtube_captions
from pipeline.tests import test_corpus_asr_view as asr_fixtures
from pipeline.tests import test_publisher_caption_batch as caption_fixtures


REMOTE = caption_fixtures.REMOTE
CREATOR = caption_fixtures.CREATOR
VIDEO = caption_fixtures.VIDEO
OWNER = caption_fixtures.CHANNEL
VTT = ("WEBVTT\n\n00:00:00.250 --> 00:00:03.500\nA light \U0001f319\n\n"
       "00:00:03.000 --> 00:00:05.000\nSecond line\n").encode()


def digest(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "md5": hashlib.md5(raw).hexdigest()}


class PublisherCorpusTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "sync").mkdir()

    def write_journal(self, name, rows):
        (self.root / "sync" / name).write_bytes(b"".join(publisher_mirror.encoded(row) for row in rows))

    def caption(self, rumble=True, multi_prefix=False, wrong_normalization=False):
        row = {"video_id": VIDEO, "channel_dir": CREATOR, "tab": "shorts" if rumble else "videos",
               "expected_channel_id": OWNER}
        normal = youtube_captions.normalize_caption(VTT, "vtt")
        if rumble:
            record = caption_fixtures.receipt()
            item = record["items"][0]
            item.update(source_sha256=digest(VTT)["sha256"], source_bytes=len(VTT), segment_count=2,
                        first_cue_start=.25, last_cue_end=5.0, word_count=len(normal["text"].split()))
            prefix = VIDEO + "/" + item["publisher_watch_id"] + "/en-auto/"
            segments = deepcopy(normal["segments"])
            if wrong_normalization:
                segments[1]["text"] = "different normalized transcript"
            members = {prefix + "publisher.vtt": VTT, prefix + "provenance.json": publisher_mirror.encoded(item),
                       prefix + "transcript.en.txt": normal["text"].encode(),
                       prefix + "segments.json": publisher_mirror.encoded(segments)}
            members["manifest.json"] = publisher_mirror.encoded({name: digest(data) for name, data in members.items()})
        else:
            item = {**row, "language": "en-gb", "language_basis": "publisher_rss_channel", "track_language_verified": False,
                    "caption_kind": "publisher_provided_unspecified", "translation_status": "not_declared",
                    "audio_binding": None, "native_youtube_caption": False, "recording_equivalence_verified": False,
                    "speech_coverage_verified": False, "source_sha256": digest(VTT)["sha256"], "source_bytes": len(VTT),
                    "segment_count": 2, "publisher_episode_guid": "Buzzsprout-12345",
                    "source_url": "https://www.buzzsprout.com/67890/12345/transcript.vtt",
                    "official_blog_url": "https://author.example/episode",
                    "official_blog_youtube_reference": "https://youtu.be/" + VIDEO,
                    "association_basis": "official_blog_exact_youtube_reference_plus_publisher_episode_identity"}
            record = {"schema_version": 1, "artifact_kind": "publisher_provided_timed_text_batch", "status": "verified",
                      "items": [item], "changes_native_audio_count": False, "changes_full_asr_count": False}
            prefix = VIDEO + "/" if multi_prefix else ""
            provenance = {"item": item} if multi_prefix else {
                "associated_youtube_id": VIDEO, "publisher_episode_guid": item["publisher_episode_guid"],
                "source_sha256": item["source_sha256"], "source_url": item["source_url"], "source_audio_binding": None}
            members = {prefix + "publisher.vtt": VTT, prefix + "segments.json": publisher_mirror.encoded(normal),
                       prefix + "provenance.json": publisher_mirror.encoded(provenance)}
            members["SHA256SUMS.txt"] = "".join(digest(value)["sha256"] + "  " + name + "\n"
                                                for name, value in sorted(members.items())).encode()
        archive = self.root / "captions.zip"
        with ZipFile(archive, "w") as output:
            for name, value in members.items():
                output.writestr(name, value)
        proof = digest(archive.read_bytes())
        proof.update(drive_id="verified-bundle", remote=f"{REMOTE}/{CREATOR}/PublisherCaptions/Batches/{proof['sha256']}/publisher-captions.zip")
        record["proof"] = proof
        self.write_journal("publisher_caption_manifest.jsonl", [record, deepcopy(record)])
        return archive, record, row

    def test_edition_captions_reproduce_unicode_and_times_without_binding_to_audio(self):
        path, record, row = self.caption()
        (job,) = reader.input_rows(self.root, [row], REMOTE)
        view = reader.text_views(path, job, REMOTE)["caption"]
        self.assertEqual(view["source_timebase"], "publisher_caption_seconds")
        self.assertEqual(view["language_evidence"]["track_key"], "en-auto")
        self.assertEqual(view["raw_sha256"], digest(VTT)["sha256"])
        self.assertIsNone(view["source_audio_sha256"])
        self.assertFalse(view["native_youtube_alignment_verified"])
        self.assertEqual(view["known_cue_union_seconds"], 4.75)
        cue = view["segments"][1]
        self.assertEqual(view["text"][cue["char_start"]:cue["char_end"]], "Second line")
        self.assertEqual(list(reader.input_rows(self.root, [dict(row, expected_channel_id="UC" + "b"*22)], REMOTE)), [])
        path.write_bytes(path.read_bytes() + b"tamper")
        with self.assertRaisesRegex(ValueError, "archived receipt"):
            reader.text_views(path, job, REMOTE)

    def test_rss_language_and_single_item_partial_batch_keep_declared_uncertainty(self):
        for prefixed in (False, True):
            with self.subTest(prefixed=prefixed):
                path, record, row = self.caption(rumble=False, multi_prefix=prefixed)
                (job,) = reader.input_rows(self.root, [row], REMOTE)
                view = reader.text_views(path, job, REMOTE)["caption"]
                self.assertEqual(view["language"], "en-gb")
                self.assertEqual(view["language_evidence"]["authorship"], "not_declared")
                self.assertFalse(view["language_evidence"]["track_language_verified"])
                broken = deepcopy(record)
                broken["items"][0]["publisher_episode_guid"] = "Buzzsprout-999"
                self.write_journal("publisher_caption_manifest.jsonl", [broken])
                self.assertEqual(list(reader.input_rows(self.root, [row], REMOTE)), [])

    def test_internally_checksummed_caption_must_reproduce_from_untouched_vtt(self):
        path, _, row = self.caption(wrong_normalization=True)
        (job,) = reader.input_rows(self.root, [row], REMOTE)
        with self.assertRaisesRegex(ValueError, "text or source-edition proof"):
            reader.text_views(path, job, REMOTE)

    def publisher_asr(self, language=None):
        row = {"video_id": VIDEO, "channel_dir": CREATOR, "tab": "videos"}
        digest_audio = "a"*64
        parent = f"{REMOTE}/{CREATOR}/Videos/{VIDEO}/PublisherVariants/{digest_audio}"
        audio = {"bytes": 120, "md5": "a"*32, "sha256": digest_audio, "drive_id": "audio",
                 "kind": "publisher_podcast_audio_variant", "remote": parent + "/publisher-audio.mp3"}
        meta = {"bytes": 80, "md5": "b"*32, "sha256": "b"*64, "drive_id": "metadata",
                "kind": "publisher_podcast_variant_provenance", "remote": parent + "/provenance.json"}
        source = {"source_kind": "publisher_audio_variant", "channel_dir": CREATOR, "variant_id": audio["sha256"],
                  "associated_youtube_id": VIDEO, "native_youtube_bytes": False,
                  "association": {"exact_youtube_id_linked_on_page": True}}
        edition = {"schema_version": 1, "status": "verified", "video_id": VIDEO, "channel_dir": CREATOR,
                   "artifact_kind": "publisher_podcast_audio_variant", "native_youtube_bytes": False,
                   "changes_native_audio_count": False, "changes_full_asr_count": False, "audio": audio, "provenance": meta}
        model = {"repository": "example/model", "model_sha256": "c"*64, "revision": "d"*40}
        model_input = {"source_audio": audio, "source_metadata": meta, "source_variant": source, "model": model}
        config = dict(gpu_asr.CONFIG)
        options = {"config": config}
        if language:
            configs = {"original": {**config, "language": language, "task": "transcribe"}}
            if language != "en":
                configs["english"] = {**config, "language": language, "task": "translate"}
            options = {"output_contract": gpu_asr_multilingual.CONTRACT, "configs": configs,
                       "proposal_sha256": "e"*64, "worker_sha256": "f"*64, "environment_lock_sha256": "1"*64}
        identity = {**model_input, **options}
        run = "asr-" + gpu_asr.fingerprint(identity)[:24]
        source_id = "publisher-" + audio["sha256"]
        language_evidence = {"scope": "publisher_rss_channel_declaration", "code": language or "en",
                             "native_youtube_language_asserted": False}
        flags = {"native_youtube_bytes": False, "changes_native_audio_count": False, "changes_native_asr_count": False}
        p = {**model_input, **options, **flags, "source_kind": "publisher_audio_variant", "source_video_id": source_id,
             "source_lease_id": "lease", "run_id": run, "identity": identity, "channel_dir": CREATOR,
             "associated_youtube_id": VIDEO, "variant_id": digest_audio, "metrics": {"audio_seconds": 7},
             "language_evidence": language_evidence, "compute": {"cpu_asr_fallback": False}, "profile": "publisher-fixture",
             "status": "local_transcription_complete_unreviewed",
             "quality": {k:False for k in ("accuracy_claimed", "human_reviewed", "speech_coverage_validated", "native_youtube_alignment_validated")}}
        admission = {"video_id": source_id, "job_id": "job", "source_lease_id": "lease", "job": {"audio": audio, "metadata": meta}}
        settings = SimpleNamespace(root=self.root, output_root=self.root/"asr/results/publisher-test")
        document = asr_fixtures.AsrViewTests.document
        with patch.object(gpu_asr, "inventory", return_value={}):
            if language:
                rows = {"original": (*document(["\u00dcber \U0001f319"], language, True), configs["original"])}
                if language != "en":
                    rows["english"] = (*document(["About \U0001f319"], "en", True), configs["english"])
                written = gpu_asr_multilingual.write_pair(settings, admission, run, rows, {}, p)
            else:
                doc, transcript = document(["A sentence \U0001f319"])
                written = gpu_asr.write_bundle(settings, admission, run, doc, transcript, {}, p)
        path = Path(written["bundle"]["path"])
        with ZipFile(path) as bundle:
            archived = json.loads(bundle.read("provenance.json"))
        record = {"schema_version": 1, "artifact_kind": reader.ASR, "status": "verified", "quality_state": "unreviewed_asr",
                  **flags, "associated_youtube_id": VIDEO, "channel_dir": CREATOR, "variant_id": digest_audio, "run_id": run,
                  "source_variant": source, "source_audio": audio, "source_provenance": meta, "source_lease_id": "lease",
                  "model": model, "language_evidence": language_evidence, "metrics": p["metrics"], "profile": p["profile"],
                  "drive_id": "archive", "remote": parent + f"/ASR/{run}/{run}.zip", **digest(path.read_bytes())}
        if language:
            record.update(output_contract=gpu_asr_multilingual.CONTRACT, text_variants=archived["text_variants"],
                          artifact_manifest_sha256=written["artifact_manifest_sha256"])
        self.write_journal("publisher_variant_manifest.jsonl", [edition])
        self.write_journal("publisher_variant_asr_manifest.jsonl", [record, record])
        return path, row, record

    def test_asr_requires_a_distinct_source_pair_and_correct_publisher_edition(self):
        path, row, record = self.publisher_asr()
        (job,) = reader.input_rows(self.root, [row], REMOTE)
        self.assertEqual(reader.local_bundle(self.root, job), path)
        original = reader.text_views(path, job, REMOTE)["english"]
        self.assertEqual(original["source_kind"], "publisher_original_asr")
        self.assertFalse(original["translation_performed"])
        self.assertEqual(original["source_timebase"], "publisher_audio_seconds")
        self.assertEqual(original["source_audio_sha256"], record["variant_id"])
        self.assertFalse(original["native_youtube_alignment_verified"])
        self.assertEqual(list(reader.input_rows(self.root, [dict(row, tab="streams")], REMOTE)), [])
        wrong = deepcopy(record)
        wrong["source_audio"]["drive_id"] = "wrong-edition"
        self.write_journal("publisher_variant_asr_manifest.jsonl", [wrong])
        self.assertEqual(list(reader.input_rows(self.root, [row], REMOTE)), [])
        wrong = deepcopy(job)
        wrong["record"]["source_lease_id"] = "different"
        with self.assertRaisesRegex(ValueError, "recording binding"):
            reader.text_views(path, wrong, REMOTE)

    def test_paired_publisher_translation_and_english_alias_have_traceable_text_versions(self):
        for language in ("de", "en"):
            with self.subTest(language=language):
                path, row, _ = self.publisher_asr(language)
                (job,) = reader.input_rows(self.root, [row], REMOTE)
                result = reader.text_views(path, job, REMOTE)
                original, english = result["original"], result["english"]
                self.assertEqual(original["language"], language)
                self.assertEqual(english["language"], "en")
                self.assertEqual(english["translation_performed"], language != "en")
                self.assertEqual(english["text_version_id"] == original["text_version_id"], language == "en")
                self.assertEqual(english["same_text_as_variant"], "original" if language == "en" else None)
                self.assertFalse(english["human_reviewed"])
