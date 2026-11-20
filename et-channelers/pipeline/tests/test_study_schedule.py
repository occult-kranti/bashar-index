import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pipeline import drive_ingest, postrun_candidates as study, study_schedule as schedule


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.selected = self.root / "cohort.json"
        self.selected.write_text(json.dumps({"latest_regular_per_creator": 20, "selection": "fixture"}))
        self.sha = schedule.configure(self.root, self.selected)["selection"]["sha256"]
        self.first, self.second = self.root / "analysis-one.md", self.root / "analysis-two.md"
        self.first.write_text("Synthetic first panel measures.")
        self.second.write_text("Synthetic second panel reproduces the estimates and reviews discordant sources.")
        self.frame = [{"video_id": "v", "channel_dir": "example"}]
        self.state = {"selection_sha256": self.sha, "summary": {"audio_available": 1, "latest20_target": 1,
                                                                "channels": 1, "remaining_audio": 0}}

    def generation(self, primary):
        roster = [dict(self.frame[0], selected_primary=primary)]
        methods = {"comparison": "a" * 64}
        key = study.digest(study.encoded([self.sha, study.digest(study.encoded(methods).encode()), roster, False]).encode())
        folder = self.root / "analysis" / key
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "view-inventory.json").write_text(json.dumps(roster))
        (folder / "manifest.json").write_text(json.dumps({"selection_sha256": self.sha, "revision": key,
             "selected_audio": 1, "missing_primary_texts": int(primary is None), "eligible_primary_texts": int(primary is not None),
             "methods": methods, "phase": "candidate_retrieval"}))
        return folder

    def finish(self, folder, **kwargs):
        with patch.object(study.collection_coverage, "mixed_selection",
                          return_value=(self.frame, {"example": "short_complete_displayed_list"}, self.sha)), \
                patch.object(study.collection_coverage, "coverage", return_value=(self.state, self.frame)):
            return schedule.finish(self.root, folder, self.first, self.second, **kwargs)

    def primary(self, filename="caption.json", **overrides):
        path = self.root / filename
        text = "Fixture evidence from the selected recording."
        view = dict(self.frame[0], source_kind="published", language="en-GB", text=text, text_sha256=study.digest(text.encode()))
        view.update(overrides)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(view), encoding="utf-8")
        return dict(source_kind=view["source_kind"], path=filename, file_sha256=schedule.pin(self.root, path)["sha256"])

    def test_cohort_gate_precedes_network_and_permits_metadata_plans(self):
        queue = self.root / "pending.csv"
        with queue.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["video_id", "channel_dir", "tab", "listing_rank"])
            writer.writerow(["abcDE123456", "example", "videos", 49])
        command = ["--root", str(self.root), "--queue", str(queue), "--newest", "50"]
        with patch.object(drive_ingest, "youtube_gate", side_effect=AssertionError("unexpected source contact")):
            self.assertEqual(drive_ingest.main(["plan", *command]), 0)
            self.assertEqual(drive_ingest.main(["run", *command, "--all", "--remote", "sample:archive"]), 3)
        with self.assertRaisesRegex(ValueError, "after the latest-20"):
            schedule.require_completed_study(self.root)

    def test_both_distinct_completed_reports_and_full_text_needed_before_release(self):
        with self.assertRaisesRegex(ValueError, "usable English"):
            self.finish(self.generation(None))
        primary = self.primary()
        folder = self.generation(primary)
        self.second.write_bytes(self.first.read_bytes())
        with self.assertRaisesRegex(ValueError, "distinct"):
            self.finish(folder)
        self.second.write_text("Second panel checked sources and alternate explanations.")
        self.finish(folder)
        schedule.require_completed_study(self.root)
        self.second.write_text("Changed result.")
        with self.assertRaisesRegex(ValueError, "changed"):
            schedule.require_completed_study(self.root)

    def test_translation_must_be_paired_with_the_original_edition(self):
        base = self.root / "text"
        base.mkdir()
        view = {"video_id": "v", "channel_dir": "example", "run_id": "run", "source_edition_id": "edition",
                "original_language": "ja", "language": "en", "variant": "english", "source_kind":"publisher_english_audio_translation",
                "text":"Hello", "text_sha256":study.digest(b"Hello")}
        english = base / "english-t.json"
        english.write_text(json.dumps(view))
        primary = dict(source_kind="publisher_english_audio_translation", path="text/english-t.json",
                       file_sha256=schedule.pin(self.root, english)["sha256"])
        folder = self.generation(primary)
        with self.assertRaisesRegex(ValueError, "matching original-language"):
            self.finish(folder)
        original = dict(view, variant="original", language="ja", text="こんにちは", text_sha256=study.digest("こんにちは".encode()))
        (base / "original-t.json").write_text(json.dumps(original))
        self.assertEqual(self.finish(folder)["translated_primary_texts"], 1)

    def test_all_primary_views_must_still_bind_to_the_selected_recording_and_text(self):
        primary = self.primary()
        folder = self.generation(primary)
        (self.root / primary["path"]).write_text("changed")
        with self.assertRaisesRegex(ValueError, "changed after analysis"):
            self.finish(folder)
        (self.root / primary["path"]).unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            self.finish(folder)
        for change in ({"video_id":"different"}, {"language":"es"}, {"text_sha256":"0"*64}, {"text":""}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "mismatch"):
                self.finish(self.generation(self.primary(**change)))

    def test_no_speech_exception_requires_matching_review_evidence(self):
        reason = self.root / "speech-review.json"
        reason.write_text(json.dumps({"finding":"no_spoken_content", "source":{"video_id":"v","channel_dir":"example",
            "selection_sha256":self.sha,"audio":{"sha256":"a"*64,"drive_id":"fixture-audio"}}}))
        reviews = self.root / "reviews.json"
        reviews.write_text(json.dumps({"selection_sha256": self.sha, "recordings": [
            {"video_id": "v", "finding": "no_spoken_content", "evidence": schedule.pin(self.root, reason)}]}))
        result = self.finish(self.generation(None), non_speech=reviews)
        self.assertEqual(result["english_texts"], 0)
        self.assertIn("v", result["non_speech_reviews"])
