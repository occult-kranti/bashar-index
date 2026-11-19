from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import postrun_candidates as study


def fingerprint(text):
    return sha256(text.encode()).hexdigest()


class PostrunTests(unittest.TestCase):
    channel = "UC" + "A" * 22
    video = "abcDE123456"
    other = "abcDE654321"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.selection = self.root / "selection.json"
        items = [dict(channel_dir="example", channel_id=self.channel, source_position=i, slot=i+1,
                      title="Sample", tab="shorts", video_id=vid) for i, vid in enumerate([self.video, self.other])]
        self.selection.write_text(json.dumps({"per_channel": 20, "channels": [{"channel_dir": "example",
            "channel_id": self.channel, "items": items, "selected": 2, "scope": "short_complete_displayed_list"}]}))
        self.pin = sha256(self.selection.read_bytes()).hexdigest()
        self.saved = [{"video_id": r["video_id"], "channel_dir": "example"} for r in items]
        self.snapshot = {"selection_sha256": self.pin, "summary": {"latest20_target": 2, "audio_available": 2,
                                                                  "channels": 1, "remaining_audio": 0}}

    def write_view(self, kind, text, language="en"):
        version = fingerprint(text + kind + language)
        directory = self.root / "analysis" / "caption_views" / self.video
        directory.mkdir(parents=True, exist_ok=True)
        view = {"video_id": self.video, "channel_dir": "example", "text_version_id": version, "text": text,
                "source_kind": kind, "language": language, "bundle_sha256": fingerprint("bundle"),
                "raw_sha256": fingerprint("raw"), "text_sha256": fingerprint(text), "offset_unit": "unicode_codepoint",
                "speech_coverage_verified": False, "segments": [{"source_segment_id": "json3:0", "char_start": 0,
                    "char_end": len(text), "time_start": 0.0, "time_end": 3.0}]}
        path = directory / (version + ".json")
        path.write_text(json.dumps(view), encoding="utf-8")
        return path

    def execute(self, **kwargs):
        with patch.object(study.collection_coverage, "coverage", return_value=(self.snapshot, self.saved)):
            return study.run(self.root, self.selection, self.pin, **kwargs)

    def test_mixed_incomplete_selection_does_not_open_any_text_or_create_an_output(self):
        self.saved.pop()
        with patch.object(study, "select_views", side_effect=AssertionError("text was opened")):
            with self.assertRaisesRegex(ValueError, "verified audio"):
                self.execute()
        self.assertFalse((self.root / "analysis").exists())

    def test_detector_evidence_uses_one_pinned_view_and_keeps_missing_episode(self):
        self.write_view("automatic_original", "A competing machine rendition.")
        self.write_view("published", "Our reading is 528 Hz.")
        first = self.execute()
        meta = json.loads((first / "manifest.json").read_bytes())
        self.assertEqual((meta["selected_audio"], meta["eligible_primary_texts"], meta["missing_primary_texts"]), (2, 1, 1))
        self.assertEqual((first / "concordance.jsonl").stat().st_size, meta["files"]["concordance.jsonl"])
        roster = json.loads((first / "view-inventory.json").read_bytes())
        self.assertEqual(roster[0]["selected_primary"]["source_kind"], "published")
        self.assertEqual(len(roster[0]["other_eligible_views"]), 1)
        self.assertIsNone(roster[1]["selected_primary"])
        rows = [json.loads(line) for line in (first / "concordance.jsonl").read_text(encoding="utf-8").splitlines()]
        frequency, = [r for r in rows if r.get("rule_id") == "frequency_numeric_hz"]
        self.assertEqual((frequency["matched_text"], frequency["review_status"]), ("528 Hz", "unreviewed_candidate"))
        comparison = json.loads((first / "episode-comparison.json").read_bytes())
        measure, = [c for c in comparison["heatmap"] if c["topic"] == frequency["candidate_family"]]
        self.assertEqual((measure["assessed_episodes"], measure["eligible_episodes"]), (1, 2))
        with patch.object(study.episode_comparison, "compare", side_effect=AssertionError("unneeded rerun")):
            self.assertEqual(first, self.execute())

    def test_unobserved_or_incomplete_short_lists_do_not_authorize_analysis(self):
        frame = self.saved
        for label in ("unobserved", "incomplete_visible_positions", "all_requested_positions_observed"):
            with self.subTest(scope=label), self.assertRaisesRegex(ValueError, "complete public listings"):
                study.complete_frame(self.snapshot, self.saved, frame, {"example": label}, self.pin)

    def test_adding_an_upload_calendar_creates_a_separate_frozen_generation(self):
        old = self.execute()
        catalog = self.root / "catalog.zip"
        pin = fingerprint("archived catalog")
        with self.assertRaisesRegex(ValueError, "together"):
            self.execute(upload_catalog=catalog)
        dates = {self.video: "2026-09-01", self.other: None}
        with patch.object(study.episode_upload_calendar, "read_catalog", return_value=(dates, {"upload_day_only": 1})) as read:
            new = self.execute(upload_catalog=catalog, upload_catalog_sha256=pin)
        self.assertEqual(read.call_args.args[:2], (catalog, pin))
        self.assertNotEqual(old, new)
        comparison = json.loads((new / "episode-comparison.json").read_bytes())
        self.assertEqual(comparison["upload_periods"]["catalog_sha256"], pin)
        self.assertEqual(comparison["upload_periods"]["quarters"], ["2026-Q3"])
        self.assertFalse(comparison["publication_periods"]["quarters"])
        self.assertNotIn("upload_periods", json.loads((old / "episode-comparison.json").read_bytes()))

    def test_malformed_or_unknown_family_membership_cannot_silently_change_estimates(self):
        file = self.root / "family.jsonl"
        file.write_text('{"wrong":true}\ninvalid', encoding="utf-8")
        with self.assertRaises((KeyError, ValueError)):
            self.execute(families=file)
        file.write_text(json.dumps({"video_id": "outside", "recording_family_id": "f",
                                    "recording_family_evidence_sha256": "a" * 64}))
        with self.assertRaisesRegex(ValueError, "family assignment"):
            self.execute(families=file)
