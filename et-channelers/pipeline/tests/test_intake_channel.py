"""Offline regression checks for source identity and lossless channel intake."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import intake_channel as intake

CHANNEL = "UC" + "A" * 22


def listing():
    return {"channel_id": CHANNEL, "channel": "Example",
            "entries": [{"webpage_url": "https://www.youtube.com/@Example/videos",
                         "entries": [{"id": "ABCDEFGHIJK", "title": "Newest", "duration": 0},
                                     {"id": "LMNOPQRSTUV", "title": "Future", "live_status": "is_upcoming"},
                                     {"id": "WXYZabcdefg", "title": "Older", "duration": 300}]},
                        {"webpage_url": "https://www.youtube.com/@Example/shorts",
                         "entries": [{"id": "hijklmnopqr", "title": "Short"}]}]}


class ChannelIntakeTests(unittest.TestCase):
    def test_nested_tabs_keep_rank_missing_duration_and_unknown_entity(self):
        rows, tabs, excluded = intake.flatten_listing(listing(), "example", "Host", "interview_host", CHANNEL)
        self.assertEqual([r["listing_rank"] for r in rows], ["0", "2", "0"])
        self.assertEqual(rows[0]["duration_s"], "0")
        self.assertEqual(rows[-1]["duration_s"], "")
        self.assertTrue(all(r["entity"] == "" and r["channeling"] == "" for r in rows))
        self.assertEqual(tabs, {"videos": 3, "streams": 0, "shorts": 1})
        self.assertEqual(excluded[0]["reason"], "is_upcoming")

    def test_channel_identity_mismatch_fails_closed(self):
        bad = listing()
        bad["channel_id"] = "UC" + "B" * 22
        with self.assertRaisesRegex(ValueError, "Canonical"):
            intake.flatten_listing(bad, "example", "Host", "interview_host", CHANNEL)
        bad = listing()
        bad["entries"][0]["entries"][0]["channel_id"] = "UC" + "B" * 22
        with self.assertRaisesRegex(ValueError, "different channel"):
            intake.flatten_listing(bad, "example", "Host", "interview_host", CHANNEL)

    def test_append_preserves_existing_metadata_and_order_on_duplicate(self):
        old = [{"video_id": "ABCDEFGHIJK", "title": "Original", "entity": "Original source"}]
        before = copy.deepcopy(old)
        incoming = [{"video_id": "ABCDEFGHIJK", "title": "Changed", "entity": ""},
                    {"video_id": "LMNOPQRSTUV", "title": "New", "entity": ""}]
        merged, added = intake.append_only(old, incoming)
        self.assertEqual(old, before)
        self.assertEqual(merged[0], before[0])
        self.assertEqual(added, 1)

    def test_publish_refuses_changed_input_without_overwriting_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "jobs/q.csv"
            path.parent.mkdir()
            path.write_bytes(b"concurrent replacement")
            with mock.patch.object(intake.shutil, "disk_usage", return_value=mock.Mock(free=10**12)):
                with self.assertRaisesRegex(RuntimeError, "input changed"):
                    intake.publish(root, {"jobs/q.csv": b"old"}, {"jobs/q.csv": b"new"},
                                   {"person_id": "example"})
            self.assertEqual(path.read_bytes(), b"concurrent replacement")

    def test_publish_rolls_back_prior_replacements_on_write_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "jobs/a.csv"
            path.parent.mkdir()
            original = b"\xef\xbb\xbfexisting\r\n"
            path.write_bytes(original)
            real = intake.atomic_write_text
            def failing(destination, text):
                if Path(destination) == root / "jobs/b.csv":
                    raise OSError("simulated disk error")
                return real(destination, text)
            with mock.patch.object(intake, "atomic_write_text", side_effect=failing), \
                    mock.patch.object(intake.shutil, "disk_usage", return_value=mock.Mock(free=10**12)):
                with self.assertRaisesRegex(OSError, "simulated"):
                    intake.publish(root, {"jobs/a.csv": original, "jobs/b.csv": None},
                                   {"jobs/a.csv": b"replacement\n", "jobs/b.csv": b"new\n"},
                                   {"person_id": "example"})
            self.assertEqual(path.read_bytes(), original)
            receipt = next((root / "jobs/queue_backups").glob("*/intake_receipt.json"))
            self.assertEqual(json.loads(receipt.read_text())["status"], "rolled_back")
            self.assertFalse((root / "jobs/b.csv").exists())

    def test_staging_respects_private_cap_before_creating_backups(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with mock.patch.object(intake, "tree_bytes", return_value=17_000_000_000):
                with self.assertRaisesRegex(ValueError, "storage cap"):
                    intake.publish(root, {}, {"jobs/new.csv": b"x"}, {"person_id": "example"})
            self.assertFalse((root / "jobs/queue_backups").exists())


if __name__ == "__main__":
    unittest.main()
