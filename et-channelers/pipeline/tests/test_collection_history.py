"""Regressions for the public projection of private collection history."""
import csv
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pipeline import collection_history as history


VID = "ABCdef123_-"
CID = "UC" + "a" * 22


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def read_table(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def data():
    row = {"video_id": VID, "expected_channel_id": CID, "channel_dir": "example", "tab": "videos"}
    selection = {"rows": [dict(row, source_channel_name="Example")], "creators": {"example": {}},
                 "basis": "latest20plus_public_regular", "sha256": "a" * 64}
    snapshot = {"kind": "strict_primary_closed_disposition_snapshot", "at_epoch": 2051222400,
                "counts": {"verified_audio_receipt": 1}, "strict_verified_audio": 1, "complete_creators": 1,
                "rows": [dict(row, disposition="verified_audio_receipt", verified_receipt_route="youtube_native",
                              closed_attempt_history=[])]}
    return selection, snapshot


class CollectionHistoryTests(unittest.TestCase):
    def test_local_problem_and_source_response_keep_distinct_meanings(self):
        self.assertEqual(history.result_fields({"source_response": {"status": 403}})[:2], ("provider_refused", 403))
        self.assertEqual(history.result_fields({"http_status": 429})[:2], ("rate_limited", 429))
        self.assertEqual(history.result_fields({"error_class": "wpc_browser_start_failed"})[:2],
                         ("local_browser_start_failed", ""))
        self.assertEqual(history.result_fields({"source_response": {"status": 200, "body_complete": False}}),
                         ("terminal_outcome_unavailable", 200, "no"))

    def test_event_time_has_precedence_and_a_missing_clock_is_explicit(self):
        self.assertEqual(history.event_time({"started_at": "2026-11-19T23:00:00-01:00"}, 0),
                         ("2026-11-20T00:00:00Z", "recorded_event_time"))
        self.assertEqual(history.event_time({"started_at": "unparseable"}, 10)[1], "file_modified_time")
        self.assertEqual(history.event_time({}, None), ("", "unavailable"))

    def test_selection_rejects_another_creator_or_date_snapshot_with_wrong_totals(self):
        selection, snapshot = data()
        for field, value in (("expected_channel_id", "UC" + "b" * 22), ("tab", "shorts"),
                             ("disposition", "opaque diagnostic"), ("verified_receipt_route", "unspecified")):
            with self.subTest(field=field):
                changed = dict(snapshot, rows=[dict(snapshot["rows"][0], **{field: value})])
                with self.assertRaises(ValueError):
                    history.validate_snapshot(selection, changed)
        with self.assertRaises(ValueError):
            history.validate_snapshot(selection, dict(snapshot, complete_creators=0))

    def test_unrelated_results_do_not_invent_protocol_outcomes(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            write(folder / "result.json", {"video_id": VID, "status": "failed"})
            self.assertEqual(history.matching_result(folder / "gpu-attempt.json", VID, 2051222400), {})
            self.assertEqual(history.matching_result(folder / "attempt.json", "other000001", 2051222400), {})
            write(folder / "videos.result.json", {"video_id": VID, "status": "complete"})
            self.assertEqual(history.matching_result(folder / "videos.attempt.json", VID, 2051222400)["status"],
                             "complete")

    def test_export_deduplicates_and_keeps_later_receipt_separate_from_earlier_denial(self):
        selection, snapshot = data()
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            archive = folder / "archive"
            marker = {"video_id": VID, "at_epoch": 1700000000, "private_debug_note": "diagnostic-never-export"}
            first = archive / "native" / VID / "attempt.json"
            write(first, marker)
            key = hashlib.sha256(first.read_bytes()).hexdigest()
            write(archive / "copied" / VID / "attempt.json", marker)
            write(archive / "fixtures" / "attempt.json", {"video_id": VID})
            write(archive / "unknown" / "attempt.json", {"video_id": "unknown0001"})
            snapshot["rows"][0]["closed_attempt_history"] = [
                {"attempt": {"sha256": key}, "route": "native_selected_offer",
                 "source_response": {"status": 403}, "result_present": True}]
            selected_path, snapshot_path = folder / "selection.json", folder / "closed.json"
            write(selected_path, selection)
            write(snapshot_path, snapshot)
            out = folder / "report"
            with patch.object(history.ingestion_status, "selection_rows", return_value=selection):
                summary = history.export(archive, selected_path, snapshot_path, out)
            self.assertEqual(summary["attempt_evidence_records"], 2)
            self.assertEqual(summary["inventory"]["fixture_markers_excluded"], 1)
            rows = read_table(out / "attempt-history.csv")
            known = next(row for row in rows if row["video_id"] == VID)
            unknown = next(row for row in rows if not row["video_id"])
            self.assertEqual((known["outcome"], known["audio_receipt_at_checkpoint"]),
                             ("provider_refused", "youtube_native"))
            self.assertEqual(known["clock_basis"], "recorded_event_time")
            self.assertEqual(unknown["recording_url"], "")
            self.assertEqual(read_table(out / "creator-status.csv")[0]["outstanding"], "0")
            self.assertEqual(read_table(out / "recording-status.csv")[0]["distinct_attempt_evidence"], "1")
            for file in out.iterdir():
                contents = file.read_text(encoding="utf-8-sig")
                self.assertNotIn("diagnostic-never-export", contents)
                self.assertNotIn("unknown0001", contents)


if __name__ == "__main__":
    unittest.main()
