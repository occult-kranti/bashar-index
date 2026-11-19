import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from pipeline import corpus_caption_view as corpus
from pipeline import drive_ingest as storage
from pipeline import youtube_captions


class CaptionViewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "caption.zip"
        self.remote = "test:archive"
        self.ident = "automatic_original.en-us.example"
        self.row = {"video_id": "example_123", "channel_dir": "test-creator", "tab": "videos",
                    "policy": storage.CAPTION_POLICY}
        self.raw = json.dumps({"events": [
            {"tStartMs": 0, "dDurationMs": 3000, "segs": [{"utf8": "A 🌔 moon."}]},
            {"tStartMs": 500, "segs": [{"utf8": "\n"}]},
            {"tStartMs": 1000, "dDurationMs": 4000, "segs": [{"utf8": "Second cue."}]},
            {"tStartMs": 9000, "segs": [{"utf8": "Last cue."}]},
        ]}).encode()
        self.track = {"status": "deleted", "kind": "automatic_original", "language": "en-us",
                      "machine_translated": False, "raw_format": "json3", "track_id": self.ident}
        self.row["tracks"] = [self.track]
        self.provenance = {**{k: v for k, v in self.track.items() if k != "status"},
                           "policy": storage.CAPTION_POLICY, "provider": "youtube",
                           "video_id": self.row["video_id"], "raw": self.proof(self.raw), "normalization_version": 1}
        self.normalized = youtube_captions.normalize_caption(self.raw, "json3")

    @staticmethod
    def proof(data):
        import hashlib
        return {"bytes": len(data), "md5": hashlib.md5(data).hexdigest(), "sha256": corpus.sha256(data)}

    def write(self, **extra):
        parts = {"raw.json3": self.raw, "provenance.json": json.dumps(self.provenance).encode(),
                 "segments.json": json.dumps(self.normalized).encode(), "transcript.txt": self.normalized["text"].encode(),
                 **extra}
        with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in parts.items():
                archive.writestr(name, data)
        self.track["bundle"] = {**self.proof(self.path.read_bytes()), "drive_id": "drive-1",
                                "remote": storage.remote_path(self.remote, self.row, f"captions.{self.ident}.zip")}

    def view(self):
        return corpus.caption_view(self.path, self.row, self.ident, remote=self.remote)

    def test_overlapping_and_open_ended_cues_roundtrip_unicode(self):
        self.write()
        view = self.view()
        self.assertEqual(view["known_cue_union_seconds"], 5)
        self.assertEqual(view["cues_without_end"], 1)
        self.assertFalse(view["speech_coverage_verified"])
        self.assertIsNone(view["speaker_attribution"])
        self.assertEqual(view["source_kind"], "automatic_original")
        self.assertEqual([s["source_segment_id"] for s in view["segments"]], ["json3:0", "json3:2", "json3:3"])
        self.assertEqual([view["text"][s["char_start"]:s["char_end"]] for s in view["segments"]],
                         ["A 🌔 moon.", "Second cue.", "Last cue."])
        self.assertEqual(view["text_version_id"], self.view()["text_version_id"])

    def test_null_is_distinct_from_measured_zero(self):
        self.assertIsNone(corpus.timed_union([{"start": 1, "end": None}]))
        self.assertEqual(corpus.timed_union([{"start": 1, "end": 1}]), 0.0)
        self.assertEqual(corpus.timed_union([{"start": 2, "end": 3}, {"start": 0, "end": 6}]), 6.0)

    def test_vtt_offsets_skip_non_cue_source_blocks(self):
        raw = b"WEBVTT\r\n\r\nNOTE author note\r\n\r\n00:01.000 --> 00:02.000\r\nA &amp; B"
        indices = []
        data = youtube_captions.normalize_caption(raw, "vtt", source_indices=indices)
        self.assertEqual((indices, data["text"]), ([2], "A & B"))

    def test_rehashed_inconsistent_members_and_wrong_video_rejected(self):
        self.write(**{"transcript.txt": b"another recording"})
        with self.assertRaisesRegex(ValueError, "reproduce"):
            self.view()
        self.provenance["video_id"] = "example_124"
        self.write()
        with self.assertRaisesRegex(ValueError, "provenance"):
            self.view()

    def test_independent_track_proof_and_source_policy(self):
        self.write()
        self.track["bundle"]["md5"] = "0" * 32
        with self.assertRaisesRegex(ValueError, "Drive object"):
            self.view()
        self.write()
        self.track["machine_translated"] = True
        with self.assertRaisesRegex(ValueError, "English"):
            self.view()
        self.track["machine_translated"] = False
        self.write(**{"../other.txt": b"unexpected"})
        with self.assertRaisesRegex(ValueError, "archive members"):
            self.view()


if __name__ == "__main__":
    unittest.main()
