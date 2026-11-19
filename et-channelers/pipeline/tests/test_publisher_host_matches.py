import unittest

from pipeline.publisher_host_matches import screen


class HostMatchesTests(unittest.TestCase):
    names = {"example": "Angel Example"}
    item = {"video_id": "abc12345678", "channel_dir": "example", "title": "Sunrise experiment",
            "duration_or_badges_as_shown": ["1:05"], "tab": "videos"}

    def episode(self, number, **kwargs):
        return dict({"feed_key": "host", "video_id": "episode-" + str(number),
                     "title": "Weekly interview", "duration_s": 600, "youtube_ids": []}, **kwargs)

    def test_notes_can_link_a_different_length_edition_or_unknown_duration(self):
        episode = self.episode(1, youtube_ids=[self.item["video_id"]])
        for badges, measured in [(["1:05"], 65), ([], None), (["1:05", "2:30"], None)]:
            with self.subTest(badges=badges):
                result, = screen([dict(self.item, duration_or_badges_as_shown=badges)], [episode], self.names)
                self.assertEqual(result["selected_display_seconds"], measured)
                self.assertEqual(result["edition_basis"], "item_notes_link")
                self.assertEqual(result["review_status"], "candidate")

    def test_show_wide_promotion_is_ignored_per_feed(self):
        episodes = [self.episode(i, youtube_ids=[self.item["video_id"]]) for i in range(4)]
        episodes.append(self.episode(5, feed_key="other", youtube_ids=[self.item["video_id"]]))
        self.assertEqual([x["feed_key"] for x in screen([self.item], episodes, self.names)], ["other"])

    def test_retitle_requires_both_runtime_and_guest_or_title(self):
        episodes = [self.episode(1, title="Angel Example joins us", duration_s=67),
                    self.episode(2, title="Angel Example joins us", duration_s=77),
                    self.episode(3, title="An unrelated guest", duration_s=65)]
        result, = screen([self.item], episodes, self.names)
        self.assertEqual(result["episode_id"], "episode-1")
        self.assertEqual(result["edition_basis"], "runtime_and_title_or_guest")
        self.assertEqual(result["review_status"], "candidate")
