"""Independent fault-injection checks for the bounded Drive ingestion path."""
from __future__ import annotations

import io
import csv
import json
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import drive_ingest as ingest


class Response(io.BytesIO):
    def __init__(self, body, *, status=200, extra_headers=None):
        super().__init__(body)
        self.status = status
        self.headers = {"Content-Length": str(len(body)), **(extra_headers or {})}

    def getcode(self):
        return self.status


class Opener:
    def __init__(self, response):
        self.response = response

    def open(self, *args, **kwargs):
        return self.response


class ReviewCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def stream(self, body, *, full_size, status=200, extra_headers=None):
        info = {"url": "https://rr1.googlevideo.com/videoplayback", "filesize": full_size}
        budget = ingest.Budget(self.root, 10000, 1000, 0, reserve=0)
        with patch.object(ingest.urllib.request, "build_opener", return_value=Opener(
                Response(body, status=status, extra_headers=extra_headers))):
            return ingest.stream_audio(info, self.root / "media.part", budget,
                                       10**12, threading.Event())

    def test_known_full_size_rejects_short_successful_http_body(self):
        with self.assertRaises(ingest.IngestError):
            self.stream(b"short", full_size=100)

    def test_partial_http_response_is_not_a_completed_recording(self):
        with self.assertRaises(ingest.IngestError):
            self.stream(b"short", full_size=100, status=206,
                        extra_headers={"Content-Range": "bytes 0-4/100"})

    def test_exact_complete_stream_records_matching_hashes(self):
        result = self.stream(b"complete", full_size=8)
        self.assertEqual(result, ingest.hash_file(self.root / "media.part"))

    def test_existing_files_and_simultaneous_writes_share_one_cap(self):
        (self.root / "unrelated.partial").write_bytes(b"x" * 30)
        budget = ingest.Budget(self.root, 100, 100, 0, reserve=0)
        ready = threading.Barrier(2)

        def worker(name):
            with (self.root / name).open("wb") as target:
                ready.wait(timeout=5)
                try:
                    budget.write(target, b"a" * 40)
                except ingest.IngestError:
                    return False
                return True

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(worker, "one.part")
            second = pool.submit(worker, "two.part")
            results = [first.result(timeout=10), second.result(timeout=10)]
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(ingest.tree_bytes(self.root), 70)

    def test_journal_receipts_cannot_spend_past_the_total_cap(self):
        (self.root / "old.part").write_bytes(b"x" * 80)
        budget = ingest.Budget(self.root, 100, 100, 0, reserve=0)
        with patch.dict(ingest._ROOT_BUDGETS, {self.root.resolve(): budget}):
            with self.assertRaises(ingest.IngestError):
                ingest.journal(self.root / "receipt.jsonl", {"status": "a" * 30})
        self.assertEqual(ingest.tree_bytes(self.root), 80)

    def receipt(self):
        path = self.root / "audio.webm"
        path.write_bytes(b"complete recording")
        record = {"video_id": "abcdefghijk", "path": path.name,
                  "remote": "etdrive:channel/audio.webm", **ingest.hash_file(path)}
        return path, record

    @staticmethod
    def metadata(record):
        return {"Size": record["bytes"], "Hashes": {"MD5": record["md5"]},
                "ID": "verified-drive-id", "IsDir": False}

    def test_missing_remote_hash_retains_local_file(self):
        path, record = self.receipt()
        class Drive:
            def stat(self, remote):
                return {"Size": record["bytes"], "Hashes": {}, "IsDir": False}
        with self.assertRaises(ingest.IngestError):
            ingest.verify_and_delete(self.root, record, Drive(), self.root / "state.jsonl")
        self.assertTrue(path.exists())

    def test_edit_during_remote_verification_is_retained(self):
        path, record = self.receipt()
        metadata = self.metadata(record)
        class Drive:
            def stat(self, remote):
                path.write_bytes(b"edited after upload")
                return metadata
        with self.assertRaises(ingest.IngestError):
            ingest.verify_and_delete(self.root, record, Drive(), self.root / "state.jsonl")
        self.assertEqual(path.read_bytes(), b"edited after upload")

    def test_crash_at_unlink_leaves_durable_verified_receipt(self):
        path, record = self.receipt()
        metadata = self.metadata(record)
        class Drive:
            def stat(self, remote):
                return metadata
        journal = self.root / "state.jsonl"
        with patch.object(Path, "unlink", side_effect=OSError("injected crash")):
            with self.assertRaises(OSError):
                ingest.verify_and_delete(self.root, record, Drive(), journal)
        self.assertTrue(path.exists())
        self.assertEqual(json.loads(journal.read_text().splitlines()[-1])["status"], "verified")

    def test_verified_copy_is_deleted_with_durable_receipt(self):
        path, record = self.receipt()
        metadata = self.metadata(record)
        class Drive:
            def stat(self, remote):
                return metadata
        journal = self.root / "state.jsonl"
        done = ingest.verify_and_delete(self.root, record, Drive(), journal)
        self.assertFalse(path.exists())
        self.assertEqual(done["status"], "deleted")
        self.assertEqual([json.loads(line)["status"] for line in journal.read_text().splitlines()],
                         ["verified", "deleted"])

    def test_second_runner_cannot_acquire_same_private_root(self):
        with ingest.exclusive_lock(self.root):
            with self.assertRaises(ingest.IngestError):
                with ingest.exclusive_lock(self.root):
                    self.fail("two runners acquired exclusive root ownership")

    def test_verified_missing_local_receipt_cannot_change_destination_on_resume(self):
        state = self.root / "sync" / "drive_ingest_manifest.jsonl"
        row = {"video_id": "abcdefghijk", "channel_dir": "channel"}
        ingest.journal(state, {**row, "path": "audio/channel/abcdefghijk.webm",
                               "status": "verified",
                               "remote": "original:channel/YouTube native/abcdefghijk.webm"})
        args = SimpleNamespace(root=self.root, max_local_bytes=100_000_000,
                               max_item_bytes=1000, min_free_bytes=0,
                               rclone="unused", rclone_config=None, download_only=False,
                               remote="different:", limit=1, min_interval=0, workers=1)
        with patch.object(ingest.Rclone, "preflight"):
            with self.assertRaises(ingest.IngestError):
                ingest.run(args, [row])

    def test_duplicate_listing_ranks_cannot_select_more_than_twenty_per_channel(self):
        queue = self.root / "queue.csv"
        with queue.open("w", newline="", encoding="utf-8") as out:
            writer = csv.DictWriter(out, fieldnames=["video_id", "channel_dir", "tab", "listing_rank"])
            writer.writeheader()
            writer.writerows({"video_id": f"v{i:010d}", "channel_dir": "same-channel",
                              "tab": "videos", "listing_rank": 0} for i in range(21))
        try:
            rows = ingest.select_queue(queue, newest=20)
        except ValueError:
            return  # malformed queue may fail closed instead of silently clipping
        self.assertLessEqual(len(rows), 20)

    def test_youtube_cooldown_still_uploads_completed_local_files(self):
        path = self.root / "audio" / "channel" / "abcdefghijk.webm"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"completed local audio")
        row = {"video_id": "abcdefghijk", "channel_dir": "channel"}
        waiting = {"video_id": "lmnopqrstuv", "channel_dir": "channel"}
        record = {**row, "status": "downloaded", "path": "audio/channel/abcdefghijk.webm",
                  **ingest.hash_file(path)}
        metadata_path = path.with_suffix(".info.json")
        metadata_path.write_text('{"title":"Completed metadata"}', encoding="utf-8")
        record["metadata"] = {"path": "audio/channel/abcdefghijk.info.json",
                              "remote": "etdrive:channel/YouTube native/abcdefghijk.info.json",
                              **ingest.hash_file(metadata_path)}
        state = self.root / "sync" / "drive_ingest_manifest.jsonl"
        ingest.journal(state, record)
        ingest.journal(state, {**waiting, "status": "error", "error_class": "forbidden",
                               "retry_not_before_epoch": time.time() + 3600})
        args = SimpleNamespace(root=self.root, max_local_bytes=100_000_000,
                               max_item_bytes=1000, min_free_bytes=0,
                               rclone="unused", rclone_config=None, download_only=False,
                               remote="etdrive:", limit=0, min_interval=0, workers=1)
        drive = Mock()
        drive.stat.side_effect = lambda remote: self.metadata(
            record["metadata"] if remote.endswith(".info.json") else record)
        drive.stat_batch.side_effect = lambda remote, paths, manifest: {
            path: dict(self.metadata(record["metadata"] if path.endswith(".info.json") else record), ID=path)
            for path in paths}
        with patch.object(ingest, "Rclone", return_value=drive), \
                patch.object(ingest, "extract_audio") as download:
            result = ingest.run(args, [row, waiting])
        self.assertEqual(result, 3)
        self.assertFalse(path.exists())
        self.assertFalse(metadata_path.exists())
        drive.copy_pair.assert_called_once()
        drive.copy.assert_not_called()
        download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
