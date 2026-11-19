from hashlib import md5, sha256
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from pipeline import corpus_publisher_view as publisher, youtube_captions


def signature(data):
    return {"bytes": len(data), "md5": md5(data).hexdigest(), "sha256": sha256(data).hexdigest()}


class PublisherViewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "captions.zip"
        self.row = {"channel_dir": "sample", "video_id": "abcdefghijk", "tab": "streams"}
        self.audio = signature(b"sample audio")
        self.base = "demo:Audio/sample/Streams/abcdefghijk/PublisherVariants/" + self.audio["sha256"]
        self.metadata = signature(b"metadata")
        self.record = {"schema_version": 1, "status": "verified", "channel_dir": "sample", "source_tab": "streams",
                       "associated_youtube_id": "abcdefghijk", "association_method": "publisher_owner_title_date_duration",
                       "kind": "qualified_publisher_mirror_audio_variant", "exact_youtube_crossreference": False,
                       "variant_id": self.audio["sha256"], "provider": "Rumble", "watch_page_id": "v00000",
                       "accepted_api_sha256": "b" * 64, **publisher.publisher_mirror.NATIVE_FLAGS,
                       "audio": {**self.audio, "drive_id": "a", "remote": self.base + "/publisher-audio.aac"},
                       "provenance": {**self.metadata, "drive_id": "m", "remote": self.base + "/provenance.json"}}
        self.raw = b"WEBVTT\n\nNOTE test\n\n00:01.000 --> 00:03.000\nThe moon.\n"
        self.source = {"kind": "publisher_english_caption", "language": "en", "caption_kind": "automatic_original",
                       "raw_format": "vtt", "raw_source_proof": signature(self.raw),
                       "source_audio_sha256": self.audio["sha256"], "accepted_metadata_sha256": "b" * 64,
                       "watch_page_id": "v00000"}

    def archive(self, corrupt_manifest=False):
        normalized = youtube_captions.normalize_caption(self.raw, "vtt")
        parts = {"raw.vtt": self.raw, "segments.json": json.dumps(normalized).encode(),
                 "transcript.txt": normalized["text"].encode(), "provenance.json": json.dumps(self.source).encode()}
        manifest = {name: signature(data) for name, data in parts.items()}
        if corrupt_manifest:
            manifest["raw.vtt"]["sha256"] = "e" * 64
        parts["manifest.json"] = json.dumps(manifest).encode()
        with ZipFile(self.path, "w") as archive:
            for name, content in parts.items():
                archive.writestr(name, content)
        bundle = signature(self.path.read_bytes())
        self.hash = bundle["sha256"]
        self.record["caption_bundle"] = {**bundle, "drive_id": "c", "usable_timed_text": True, "language": "en",
                                         "kind": "automatic_original", "coverage": {"segment_count": 1},
                                         "remote": f"{self.base}/Captions/{self.hash}/captions.zip"}

    def view(self):
        return publisher.publisher_view(self.path, self.record, self.row, self.hash, remote="demo:Audio")

    def test_publisher_timebase_is_bound_to_edition_and_unicode_spans(self):
        self.archive()
        view = self.view()
        self.assertEqual(view["source_timebase"], "publisher_audio_seconds")
        self.assertEqual(view["source_edition_id"], "sha256:" + self.audio["sha256"])
        self.assertEqual(view["source_kind"], "publisher_english_caption")
        self.assertEqual(view["caption_kind"], "automatic_original")
        self.assertEqual(view["segments"][0]["source_segment_id"], "vtt:2")
        self.assertEqual(view["text"], "The moon.")
        self.assertEqual(view["known_cue_union_seconds"], 2.0)

    def test_standard_publisher_and_early_substack_schemas(self):
        self.source["raw_caption"] = self.source.pop("raw_source_proof")
        self.source["accepted_api_sha256"] = self.source.pop("accepted_metadata_sha256")
        self.source["normalization_version"] = 1
        self.archive()
        self.assertEqual(self.view()["text"], "The moon.")
        self.record["provider"] = "Substack"
        self.source = {"original": True, "source": "https://example.substack.com/p/article", "language": "en",
                       "watch_page_id": "v00000", "source_audio_sha256": self.audio["sha256"], "raw": signature(self.raw),
                       "native_youtube_caption": False}
        self.archive()
        self.assertEqual(self.view()["language_evidence"], {"publisher_marks_original": True})

    def test_buzzsprout_bound_episode_uses_its_rss_language_and_keeps_authorship_unknown(self):
        self.record.update(provider="Buzzsprout", watch_page_id="123", item_id="Example-Show-Buzzsprout-123")
        self.source = {"provider": "Buzzsprout", "source_audio_sha256": self.audio["sha256"],
                       "publisher_episode_guid": "Buzzsprout-123", "prior_standalone_drive_item": "prior-object",
                       "prior_standalone_bundle_sha256": "d" * 64, "vtt": signature(self.raw),
                       "full_speech_coverage_verified": False}
        self.archive()
        self.record["caption_bundle"].update(kind="publisher_provided_unspecified", provider_language_key="en-gb")
        view = self.view()
        self.assertEqual(view["caption_kind"], "publisher_provided_unspecified")
        self.assertEqual(view["language_evidence"]["provider_language_key"], "en-gb")
        self.assertEqual(view["source_timebase"], "publisher_audio_seconds")
        self.record["watch_page_id"] = "124"
        with self.assertRaisesRegex(ValueError, "episode identity"):
            self.view()

    def test_rehashed_other_recording_manifest_or_track_cannot_be_admitted(self):
        self.archive(corrupt_manifest=True)
        with self.assertRaisesRegex(ValueError, "manifest"):
            self.view()
        self.source["source_audio_sha256"] = "3" * 64
        self.archive()
        with self.assertRaisesRegex(ValueError, "source audio"):
            self.view()
        self.source["source_audio_sha256"] = self.audio["sha256"]
        self.archive()
        self.record["caption_bundle"]["remote"] = self.record["caption_bundle"]["remote"].replace("Streams", "Videos")
        with self.assertRaisesRegex(ValueError, "different editions"):
            self.view()
