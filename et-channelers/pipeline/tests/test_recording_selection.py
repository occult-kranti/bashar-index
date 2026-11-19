import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recording_selection import select_channel
from uploads_playlist import uploads_url


CHANNEL = "UC" + "A" * 22
IDS = [f"{n:011d}" for n in range(4)]


def item(pos, *, labels=(), badges=()):
    return {"video_id": IDS[pos], "position_zero_based": pos, "byline_channel_id": CHANNEL,
            "watch_playlist_id": "UU" + CHANNEL[2:], "display_metadata": [list(labels)],
            "duration_or_badges_as_shown": list(badges), "title": "Example"}


def frames(items, unresolved=()):
    return {"items": items, "canonical_url": uploads_url(CHANNEL), "unresolved_positions": list(unresolved),
            "primary_array_closed": True, "complete_http": True, "continuation_visible": False}


class SelectionTest(unittest.TestCase):
    def test_source_confirms_upcoming_and_backfills_next_position(self):
        sample = frames([item(0, labels=["Scheduled for tomorrow"]), item(1), item(2, badges=["0:58"]), item(3)])
        watch = {(CHANNEL, IDS[1]): {"is_upcoming": True}}
        saved_tab = {("creator", IDS[2]): {"videos"}}
        report = select_channel("creator", CHANNEL, sample, 2, saved_tab, {IDS[2]: {"shorts"}}, watch)
        self.assertEqual([r["video_id"] for r in report["items"]], IDS[2:])
        self.assertEqual([r["tab"] for r in report["items"]], ["shorts", "unknown"])
        self.assertEqual([r["source_position"] for r in report["items"]], [2, 3])
        self.assertEqual([r["slot"] for r in report["items"]], [1, 2])
        self.assertEqual([r["video_id"] for r in report["excluded"]], IDS[:2])
        self.assertEqual(report["scope"], "all_requested_positions_observed")

    def test_missing_middle_frame_never_certifies_newest_positions(self):
        data = frames([item(0), item(2)], unresolved=[1])
        self.assertEqual(select_channel("creator", CHANNEL, data, 2, {}, {}, {})["scope"], "incomplete_visible_positions")
        self.assertEqual(select_channel("creator", CHANNEL, data, 2, {}, {}, {})["selected"], 1)

    def test_short_catalog_and_colliding_labels_retain_uncertainty(self):
        data = frames([item(0, badges=["0:45"])])
        report = select_channel("creator", CHANNEL, data, 20, {("creator", IDS[0]): {"videos", "shorts"}}, {}, {})
        self.assertEqual(report["scope"], "short_complete_displayed_list")
        self.assertEqual(report["items"][0]["tab"], "unknown")
        self.assertEqual(report["items"][0]["observed_tabs"], ["shorts", "videos"])
        data["items"][0]["byline_channel_id"] = "UC" + "B" * 22
        with self.assertRaisesRegex(ValueError, "Unbound source row"):
            select_channel("creator", CHANNEL, data, 20, {}, {}, {})


if __name__ == "__main__":
    unittest.main()
