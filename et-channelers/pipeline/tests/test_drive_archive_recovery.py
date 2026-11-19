import hashlib
import json
from pathlib import Path
import unittest

from pipeline import drive_archive_recovery as recovery


class ArchivePairRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.remote = "fixture:Audio"
        self.video = "-0123456789"
        self.row = {"video_id": self.video, "channel_dir": "creator", "expected_channel_id": "UC" + "a" * 22,
                    "tab": "streams"}
        self.data = b"a native format"
        self.audio_name = self.video + ".webm"
        self.meta_name = self.video + ".info.json"
        parent = self.remote + "/creator/Videos/"
        self.audio_path, self.meta_path = parent + self.audio_name, parent + self.meta_name
        self.meta = {
            "schema_version": 1, "source": {"platform": "youtube", "video_id": self.video},
            "metadata": {"id": self.video, "channel_id": self.row["expected_channel_id"], "ext": "webm",
                         "vcodec": "none", "acodec": "opus", "filesize": len(self.data), "format_id": "251"},
            "queue": {"video_id": self.video, "channel_dir": "creator", "tab": "videos"},
            "archive_audio": {"video_id": self.video, "file_name": self.audio_name, "remote": self.audio_path,
                              "encoding": "native audio; no re-encode", "bytes": len(self.data),
                              "md5": hashlib.md5(self.data).hexdigest(), "sha256": hashlib.sha256(self.data).hexdigest()},
        }

    def build(self, change_audio=None):
        raw = json.dumps(self.meta).encode()
        def entry(name, content):
            return {"Name": name, "Path": "creator/Videos/" + name, "IsDir": False, "ID": "id-" + name,
                    "Size": len(content), "Hashes": {"md5": hashlib.md5(content).hexdigest()}}
        audio = entry(self.audio_name, self.data)
        if change_audio:
            audio.update(change_audio)
        return recovery.recovered_record(self.row, self.remote, raw, Path("review/old.info.json"),
                                         self.audio_path, audio, self.meta_path, entry(self.meta_name, raw))

    def test_reuses_archived_pair_even_when_updated_tab_classification_differs(self):
        record = self.build()
        self.assertEqual(record["tab"], "streams")
        self.assertEqual(record["archive_recovery"]["original_tab"], "videos")
        self.assertEqual(record["remote"], self.audio_path)
        self.assertEqual(record["metadata"]["remote"], self.meta_path)
        self.assertFalse(record["archive_recovery"]["media_downloaded_this_recovery"])

    def test_single_object_stat_requires_exact_queried_remote(self):
        with self.assertRaisesRegex(ValueError, "exact queried path"):
            self.build({"Path": self.audio_name})
        self.assertEqual(self.build({"Path": self.audio_name, "remote": self.audio_path})["source_ext"], "webm")

    def test_rejects_wrong_uploader_format_size_and_remote_audio_checksum(self):
        self.meta["metadata"]["channel_id"] = "UC" + "b" * 22
        with self.assertRaisesRegex(ValueError, "uploader"):
            self.build()
        self.meta["metadata"]["channel_id"] = self.row["expected_channel_id"]
        self.meta["metadata"]["filesize"] += 1
        with self.assertRaisesRegex(ValueError, "size"):
            self.build()
        self.meta["metadata"]["filesize"] -= 1
        with self.assertRaisesRegex(recovery.drive_ingest.IngestError, "MD5"):
            self.build({"Hashes": {"md5": "0" * 32}})
