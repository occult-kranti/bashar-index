from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pipeline import postrun_candidates, publisher_feed_text as feed, stage_archived_text as stage


class NumberedEpisodeTranscriptTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root/"sync").mkdir()
        self.remote = "archive:Audio"
        self.raw = b"We have a question.\n\nWhat is the answer?"
        self.row = dict(video_id="aaaaaaaaaaa", channel_dir="example", tab="videos", channel_id="UC"+"h"*22,
                        title="A question | EP 2-003", duration_s=56)
        md = hashlib.md5(self.raw).hexdigest()
        sha = hashlib.sha256(self.raw).hexdigest()
        show = "11111111-1111-4111-8111-111111111111"
        guid = "22222222-2222-4222-8222-222222222222"
        self.record = {
            **self.row, "schema_version":1, "kind":feed.KIND, "status":"verified", "provider":"Riverside",
            "youtube_title":self.row["title"], "youtube_duration_s":56, "episode_title":"A question",
            "episode_duration_s":55, "episode_guid":guid, "season":"2", "episode_number":"3", "show_id":show,
            "language":"en", "show_language":"en", "mime_type":"text/plain", "words":8, "english_common_words":5,
            "feed_url":"https://api.riverside.fm/hosting/show.rss", "feed_sha256":"a"*64, "selection_sha256":"b"*64,
            "source_url":f"https://hosting-media.riverside.com/media/podcasts/{show}/episodes/{guid}/transcripts.txt",
            "paragraphs":2, "publisher_declares_transcript":True, "timed":False, "recording_equivalence_verified":False,
            "native_youtube_alignment_verified":False, "source_audio_sha256":None,
            "proof":{"bytes":len(self.raw), "md5":md, "sha256":sha, "drive_id":"original-document",
                     "remote":f"{self.remote}/example/Videos/aaaaaaaaaaa/PublisherTranscripts/{sha}/publisher-transcript.en.txt"},
            "provenance":{"bytes":1250, "md5":"d"*32, "sha256":"e"*64, "drive_id":"publication-metadata",
                          "remote":f"{self.remote}/example/Metadata/Batches/{'e'*64}/catalog-and-publisher-text.json"}}

    def test_same_episode_duration_and_owner_are_required(self):
        self.assertTrue(feed.valid_record(self.record, self.row, self.remote))
        for key, value in (("episode_number","5"), ("channel_id","UC"+"z"*22), ("episode_duration_s",67),
                           ("episode_title","A different question"), ("source_audio_sha256","7"*64),
                           ("native_youtube_alignment_verified",True), ("source_url","https://example.org/transcript")):
            with self.subTest(key=key):
                self.assertFalse(feed.valid_record({**self.record,key:value}, self.row, self.remote))
        altered = deepcopy(self.record)
        altered["provenance"]["drive_id"] = altered["proof"]["drive_id"]
        self.assertFalse(feed.valid_record(altered, self.row, self.remote))
        for key in ("provenance", "proof"):
            altered = deepcopy(self.record)
            del altered[key]["remote"]
            self.assertFalse(feed.valid_record(altered, self.row, self.remote))

    def test_short_document_is_deduplicated_and_available_for_paragraph_search(self):
        line = json.dumps(self.record)+"\n"
        (self.root/"sync/publisher_feed_transcripts.jsonl").write_text(line+line)
        (job,) = stage.input_rows(self.root, [self.row], self.remote)
        local = self.root/"document.txt"
        local.write_bytes(self.raw)
        views = stage.text_views(self.root, job, local, self.remote)
        (name, view), = views.items()
        path = self.root/"analysis"/name
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(view))
        (selected,) = postrun_candidates.select_views(self.root,[self.row])[self.row["video_id"]]
        self.assertEqual(selected["paragraph_count"],2)
        self.assertEqual(selected["evidence_granularity"],"paragraph")
        self.assertEqual(view["text"].encode(),self.raw)
        self.assertIsNone(view["source_audio_sha256"])
        self.assertIsNone(view["segments"][1]["time_start"])
        local.write_bytes(self.raw+b"!")
        with self.assertRaisesRegex(ValueError,"differs"):
            stage.text_views(self.root,job,local,self.remote)
