"""Research fidelity and credential-removal tests for metadata snapshots."""
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from media_metadata import build_metadata


class MetadataTests(unittest.TestCase):
    def build(self, info=None, row=None):
        return build_metadata({"id": "abcdefghijk", **(info or {})},
                              {"video_id": "abcdefghijk", **(row or {})}, "2026-11-16T22:00:00Z")

    def test_rich_research_metadata_survives(self):
        fields = {"title": "Session", "description": "Published description", "tags": ["one", "two"],
                  "categories": ["Education"], "chapters": [{"title": "Opening", "start_time": 0, "end_time": 20}],
                  "channel_id": "UC-source", "channel_url": "https://www.youtube.com/@source",
                  "uploader_url": "https://www.youtube.com/@source", "upload_date": "20261116",
                  "timestamp": 1794866400, "view_count": 15, "like_count": 2,
                  "thumbnails": [{"url": "https://i.ytimg.com/vi/abcdefghijk/default.jpg?rs=public", "width": 320}],
                  "language": "en", "duration": 90.5, "availability": "public"}
        self.assertEqual(self.build(fields)["metadata"], {"id": "abcdefghijk", **fields})

    def test_nested_credentials_transport_urls_and_private_paths_are_removed(self):
        info = {"url": "https://r1.googlevideo.com/videoplayback?sig=SECRET_A",
                "http_headers": {"Authorization": "Bearer SECRET_B"},
                "formats": [{"format_id": "251", "acodec": "opus", "filesize": 123,
                             "url": "https://r2.googlevideo.com/videoplayback?token=SECRET_C",
                             "http_headers": {"Cookie": "SECRET_D"}}],
                "extra": {"refresh_token": "SECRET_E", "filepath": "C:\\private\\secret.webm",
                          "more": [{"client-secret": "SECRET_F", "public_field": "keep"}]},
                "_filename": "/home/private/secret.webm", "_internal": {"value": "SECRET_G"}}
        result = self.build(info)
        serialized = json.dumps(result)
        self.assertNotIn("SECRET_", serialized)
        self.assertNotIn("googlevideo", serialized)
        self.assertNotIn("private", serialized)
        self.assertEqual(result["metadata"]["formats"], [{"format_id": "251", "acodec": "opus", "filesize": 123}])
        self.assertEqual(result["metadata"]["extra"], {"more": [{"public_field": "keep"}]})

    def test_subtitle_languages_survive_without_temporary_fetch_urls(self):
        result = self.build({"subtitles": {"de": [{"ext": "vtt", "url": "https://www.youtube.com/api/timedtext?v=abcdefghijk"}]},
                             "automatic_captions": {"en-orig": [{"ext": "json3", "name": "English", "url": "https://www.youtube.com/api/timedtext?sig=SECRET"}]}})
        self.assertEqual(result["languages"]["manual_subtitles"], ["de"])
        self.assertEqual(result["languages"]["automatic_captions"], ["en-orig"])
        self.assertNotIn("timedtext", json.dumps(result))
        self.assertEqual(result["metadata"]["subtitles"]["de"], [{"ext": "vtt"}])

    def test_free_text_retains_public_links_but_redacts_embedded_transport_and_bearer(self):
        result = self.build({"description": "Read https://example.org/paper and https://r1.googlevideo.com/videoplayback?sig=SECRET_A then Bearer SECRET_BBBBB."})
        text = result["metadata"]["description"]
        self.assertIn("https://example.org/paper", text)
        self.assertNotIn("SECRET", text)
        self.assertIn("[transport URL omitted]", text)

    def test_signed_generic_urls_userinfo_and_local_path_values_are_removed(self):
        result = self.build({"extra": ["https://example.org/file?X-Amz-Signature=SECRET_A",
                                       "https://name:SECRET_B@example.org/", "file:///private/a",
                                       "C:\\private\\a", "\\\\server\\private", "/workspaces/private/a",
                                       "https://example.org/public"]})
        self.assertEqual(result["metadata"]["extra"], ["https://example.org/public"])

    def test_queue_provenance_and_uncertain_entity_basis_survive(self):
        row = {"primary_person_name": "Person", "entity": "", "entity_label_basis": "unknown",
               "queue_provenance": "newest20+saved_full", "source_channel_name": "Channel"}
        result = self.build(row=row)
        self.assertEqual(result["queue"], {"video_id": "abcdefghijk", **row})
        self.assertEqual(result["source"]["url"], "https://www.youtube.com/watch?v=abcdefghijk")

    def test_snapshot_is_valid_json_even_with_nonfinite_measurements(self):
        result = self.build({"duration": math.nan, "formats": [{"abr": math.inf}]})
        encoded = json.dumps(result, allow_nan=False)
        self.assertEqual(json.loads(encoded)["metadata"]["formats"], [{"abr": None}])

    def test_wrong_item_is_rejected(self):
        with self.assertRaises(ValueError):
            self.build({"id": "lmnopqrstuv"})

    def test_inputs_are_not_mutated(self):
        source = {"formats": [{"format_id": "251", "url": "https://r1.googlevideo.com/videoplayback"}]}
        before = json.dumps(source)
        self.build(source)
        self.assertEqual(json.dumps(source), before)

    def test_camel_case_session_keys_are_removed_recursively(self):
        result = self.build({"extra": {"accessToken": "SECRET_A", "visitorData": "SECRET_B",
                                       "HTTPHeaders": {"Authorization": "SECRET_C"},
                                       "localPath": "relative-private-file", "sessionId": "SECRET_D",
                                       "channelId": "public-source"}})
        self.assertEqual(result["metadata"]["extra"], {"channelId": "public-source"})


if __name__ == "__main__":
    unittest.main()
