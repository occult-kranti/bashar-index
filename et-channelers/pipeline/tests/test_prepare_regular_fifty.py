import gzip
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pipeline import prepare_regular_fifty
from pipeline import collect_regular_videos
from pipeline.tests.test_regular_video_index import CHANNEL, card, page_bytes


def row(i):
    return {"channel_dir": "example", "video_id": f"x{i:010d}", "expected_channel_id": CHANNEL,
            "observed_primary_channel_id": CHANNEL, "public_listing_rank": i, "tab": "videos",
            "title": str(i), "duration_s": 60, "access_status": "public_listing"}


class NextCohortTests(unittest.TestCase):
    def test_cli_indexes_fifty_and_preserves_original_twenty(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root/"sweep"
            channel = folder/"example"
            channel.mkdir(parents=True)
            roster = root/"channels.json"
            roster.write_text(json.dumps({"channels": [{"channel_dir": "example", "channel_id": CHANNEL}]}))
            data = page_bytes([card(i, duration="0:35") for i in range(53)])
            (channel/"videos.html.gz").write_bytes(gzip.compress(data))
            (channel/"videos.json").write_text(json.dumps({
                "expected_channel_id": CHANNEL, "creator": "example", "tab": "videos",
                "wire_sha256": hashlib.sha256(data).hexdigest()}))
            (channel/"videos.attempt.json").write_text(json.dumps({"started": "2026-11-19T12:00:00Z"}))
            args = ["index", "--root", str(root), "--channels", str(roster), "--out", str(folder)]
            with patch("builtins.print"):
                collect_regular_videos.main(args)
                old = (folder/"fresh-videos.json").read_bytes()
                collect_regular_videos.main(args + ["--per-channel", "50"])
                with self.assertRaisesRegex(ValueError, "distinct filename"):
                    collect_regular_videos.main(args + ["--per-channel", "50", "--index-name", "fresh-videos.json"])
            new = json.loads((folder/"fresh-videos-50.json").read_bytes())
            self.assertEqual((new["per_channel"], new["summary"]["public_regular_targets"]), (50, 50))
            self.assertEqual(json.loads(old)["summary"]["public_regular_targets"], 20)
            self.assertEqual((folder/"fresh-videos.json").read_bytes(), old)

    def test_keeps_previous_membership_and_reuses_already_saved_recordings(self):
        videos = [row(i) for i in range(50)]
        previous = {"latest_regular_per_creator": 20, "channels": [{"channel_dir": "example", "channel_id": CHANNEL}],
                    "rows": [dict(row(i), fresh_public_regular=True) for i in range(19, 39)]}
        fresh = {"per_channel": 50, "channels": [{"channel_dir": "example", "channel_id": CHANNEL,
                  "public_items": videos, "public_listing_complete": True}]}
        verified = {("example", row(i)["video_id"]) for i in [*range(19, 39), 43]}
        result = prepare_regular_fifty.prepared_queue(previous, fresh, verified)
        self.assertEqual((result["target"], result["already_saved"], result["remaining"]), (50, 21, 29))
        self.assertEqual(result["rows"][0]["listing_rank"], 0)
        self.assertTrue(result["rows"][43]["verified_audio"])
        self.assertFalse(result["rows"][43]["previous_cohort"])
        with self.assertRaisesRegex(ValueError, "previous cohort"):
            prepare_regular_fifty.prepared_queue(previous, fresh, set())
        fresh["channels"][0]["public_items"] = videos[:37]
        with self.assertRaisesRegex(ValueError, "incomplete"):
            prepare_regular_fifty.prepared_queue(previous, fresh, verified)
        fresh["channels"][0]["exhausted"] = True
        result = prepare_regular_fifty.prepared_queue(previous, fresh, verified)
        self.assertEqual(result["previous_cohort_outside_current_50"], 2)
        fresh["channels"][0]["public_items"][0] = dict(videos[0], tab="shorts")
        with self.assertRaisesRegex(ValueError, "listing row"):
            prepare_regular_fifty.prepared_queue(previous, fresh, verified)
