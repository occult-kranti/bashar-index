import contextlib
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import latest_tab_candidates as inventory


class AcrossTabCandidateTests(unittest.TestCase):
    def test_real_entrypoint_keeps_colliding_ranks_all_tabs_and_source_date_precision(self):
        def item(number, tab, rank, channel="example"):
            return {"channel_dir": channel, "tab": tab, "video_id": f"A{number:010d}",
                    "listing_rank": rank, "title": f"Item {number}", "upload_date_approx": "20260104"}

        regular = item(1, "videos", 0)
        catalog = [regular, item(2, "videos", 0), item(3, "videos", 1), item(4, "videos", 1),
                   item(5, "videos", 2), item(6, "shorts", 0), item(7, "streams", 0),
                   item(1, "videos", 4), item(8, "videos", 0, "untracked")]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            merged, frozen, receipts, out = [root / name for name in
                                              ("merged.csv", "frozen.csv", "receipts.jsonl", "candidates.csv")]
            inventory.write_csv(merged, catalog, regular.keys())
            inventory.write_csv(frozen, [regular], regular.keys())
            records = [{"channel_dir": channel, "video_id": f"A{number:010d}", "published": day}
                       for channel, number, day in [("example", 1, "2026-01-04"),
                                                    ("example", 6, "2026-01-06"),
                                                    ("example", 6, "2026-01-07"),
                                                    ("different", 7, "2026-01-03")]]
            receipts.write_text("\n".join(map(json.dumps, records)), encoding="utf-8")
            overlay = root / "dates.json"
            entry = {"video_id": regular["video_id"], "upload_date": "20260103",
                     "provenance": "saved_youtube_metadata", "source_sha256": "e" * 64}
            overlay.write_text(json.dumps({"schema_version": 1, "items": [
                entry, dict(entry, video_id="A0000000099")
            ]}), encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                inventory.main(["--catalog", str(merged), "--selected", str(frozen), "--per-tab", "2",
                                "--ingest-receipts", str(receipts), "--exact-dates", str(overlay),
                                "--out", str(out)])
            with out.open(encoding="utf-8", newline="") as stream:
                by_id = {row["video_id"]: row for row in csv.DictReader(stream)}
        self.assertEqual(set(by_id), {f"A{n:010d}" for n in (1, 2, 3, 4, 6, 7)})
        self.assertEqual(by_id[regular["video_id"]]["recorded_publication_date"], "2026-01-04")
        self.assertEqual(by_id[regular["video_id"]]["youtube_upload_date"], "2026-01-03")
        self.assertEqual(by_id[regular["video_id"]]["upload_date_metadata_sha256"], "e" * 64)
        self.assertEqual(by_id["A0000000006"]["youtube_upload_date"], "")
        self.assertEqual(by_id["A0000000003"]["at_tab_cutoff_tie"], "True")
        self.assertEqual(by_id["A0000000006"]["date_evidence"], "conflicting recorded dates")
        self.assertEqual(by_id["A0000000007"]["recorded_publication_date"], "")
        self.assertEqual(by_id["A0000000007"]["needs_stream_completion_check"], "True")
        self.assertEqual(json.loads(stdout.getvalue())["ids_outside_frozen_queue"], 5)
        self.assertEqual(json.loads(stdout.getvalue())["ids_with_exact_upload_dates"], 1)

    def test_malformed_upload_date_evidence_cannot_enter_the_inventory(self):
        row = {"video_id": "A0000000001", "upload_date": "2026-01-03",
               "provenance": "saved_youtube_metadata", "source_sha256": "invalid"}
        with self.assertRaisesRegex(ValueError, "SHA256"):
            inventory.add_upload_dates([row], {"schema_version": 1, "items": [row]})
