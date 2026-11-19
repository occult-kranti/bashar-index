import unittest

from pipeline.publisher_description_links import kind, public_link


class DescriptionLinksTests(unittest.TestCase):
    def test_normalizes_tracking_and_discards_access_parameters(self):
        self.assertEqual(public_link("https://BLOG.example/episode/8/?utm_source=mail#news"),
                         "https://blog.example/episode/8")
        self.assertEqual(public_link("https://blog.example/?p=118&ref=mail"), "https://blog.example/?p=118")
        for value in ("https://x.example/path?access_token=fixture", "https://x.example/path/bundle_token=fixture",
                      "https://x.example/path/signature%3Dfixture", "https://user:pass@x.example/p",
                      "https://www.youtube.com/watch?v=example_123", "http://x.example:abcd/"):
            self.assertIsNone(public_link(value))

    def test_sources_distinguish_store_group_or_channel_from_recording(self):
        self.assertEqual(kind("https://facebook.com/groups/12345"), "social_profile")
        self.assertEqual(kind("https://facebook.com/groups/12345/posts/45678"), "social_post")
        self.assertEqual(kind("https://example.com/store/p/record"), "website")
        self.assertEqual(kind("https://rumble.com/user/person"), "website")
        self.assertEqual(kind("https://publisher.example/episode/8"), "publisher_page")
        self.assertEqual(kind("https://cdn.example/p/track.vtt"), "caption_file")
        self.assertEqual(kind("https://podcast.example/8.mp3"), "media_file")


if __name__ == "__main__":
    unittest.main()
