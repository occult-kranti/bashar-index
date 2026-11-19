import unittest

from pipeline.publisher_site_gallery import gallery_metadata


class PublisherGalleryTests(unittest.TestCase):
    def test_joins_both_ids_and_preserves_observation_provenance(self):
        row = {"video_id": "AbcDef12345", "channel_dir": "artist", "tab": "videos"}
        page = b'''<a href="https://www.youtube.com/watch?v=AbcDef12345"
                     data-video-id="AbcDef12345" data-video-title="An interview"
                     data-channel-id="owner" data-like-count="0" data-view-count="1.2K"
                     data-title="The creator's own description." data-published-date="1770000000"></a>'''
        def project(html):
            return gallery_metadata(html, "https://artist.example/videos", "owner",
                                    {row["video_id"]: row}, "2026-11-19T12:00:00Z")
        record, = project(page)
        self.assertEqual(record["metadata"]["like_count"], 0)
        self.assertNotIn("view_count", record["metadata"])
        self.assertEqual(record["metadata"]["timestamp"], 1770000000)
        self.assertIsNone(record["observation_source"]["engagement_as_of"])
        self.assertEqual(project(page.replace(b'data-channel-id="owner"', b'data-channel-id="guest"')), [])
        self.assertEqual(project(page.replace(b"watch?v=AbcDef12345", b"watch?v=AnotherId00")), [])
        repeated, = project(page + page)
        self.assertEqual(repeated["metadata"], record["metadata"])
        self.assertNotEqual(repeated["observation_source"]["page_sha256"], record["observation_source"]["page_sha256"])
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            project(page + page.replace(b'data-like-count="0"', b'data-like-count="1"'))
