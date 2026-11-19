"""Storage, queue and crash-safety tests for native audio Drive ingestion."""
from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import drive_ingest as ingest


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def recording(self):
        path = self.root / "audio" / "person" / "12345678901.webm"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"private audio fixture")
        rec = dict(ingest.hash_file(path), video_id="12345678901", channel_dir="person",
                   path="audio/person/12345678901.webm", remote="etdrive:person/YouTube native/12345678901.webm",
                   status="downloaded")
        return path, rec

    def drive(self, rec):
        drive = Mock()
        drive.stat.return_value = {"Size": rec["bytes"], "Hashes": {"MD5": rec["md5"]},
                                   "IsDir": False, "ID": "verified-drive-file-id"}
        return drive


class BudgetTests(Fixture):
    def test_existing_files_and_reservations_count(self):
        (self.root / "old.bin").write_bytes(b"x" * 30)
        budget = ingest.Budget(self.root, 100, 30, 0, reserve=5)
        budget.reserve_item("one", self.root / "one.part")
        budget.reserve_item("two", self.root / "two.part")
        with self.assertRaisesRegex(ingest.IngestError, "buffer is currently unavailable"):
            budget.reserve_item("three", self.root / "three.part")

    def test_write_refuses_before_exceeding_per_item_limit(self):
        budget = ingest.Budget(self.root, 100, 10, 0, reserve=5)
        path = self.root / "one.part"
        budget.reserve_item("one", path)
        with open(path, "wb") as out:
            budget.write(out, b"x" * 9)
            with self.assertRaises(ingest.IngestError):
                budget.write(out, b"xx")
        self.assertEqual(path.stat().st_size, 9)

    def test_new_unrelated_bytes_count_at_each_write(self):
        budget = ingest.Budget(self.root, 100, 80, 0, reserve=5)
        path = self.root / "one.part"
        budget.reserve_item("one", path)
        (self.root / "other.bin").write_bytes(b"x" * 90)
        with open(path, "wb") as out:
            with self.assertRaises(ingest.IngestError):
                budget.write(out, b"x" * 6)
        self.assertEqual(path.stat().st_size, 0)

    def test_never_allows_user_cap_over_the_project_ceiling(self):
        ingest.Budget(self.root, ingest.MAX_LOCAL_BYTES, 100, 0)
        with self.assertRaises(ValueError):
            ingest.Budget(self.root, ingest.MAX_LOCAL_BYTES + 1, 100, 0)

    def test_second_process_lock_is_rejected(self):
        with ingest.exclusive_lock(self.root):
            with self.assertRaises(ingest.IngestError):
                with ingest.exclusive_lock(self.root):
                    self.fail("second lock must not enter")

    def test_durable_journal_cannot_cross_hard_storage_ceiling(self):
        (self.root / "old.bin").write_bytes(b"x" * 90)
        budget = ingest.Budget(self.root, 100, 10, 0, reserve=5)
        ingest._ROOT_BUDGETS[self.root.resolve()] = budget
        self.addCleanup(ingest._ROOT_BUDGETS.pop, self.root.resolve())
        with self.assertRaises(ingest.IngestError):
            ingest.journal(self.root / "receipt.jsonl", {"status": "verified"})
        self.assertLessEqual(ingest.tree_bytes(self.root), 100)


class QueueTests(Fixture):
    def queue(self, rows):
        path = self.root / "queue.csv"
        with open(path, "w", newline="", encoding="utf-8") as out:
            writer = csv.DictWriter(out, fieldnames=["video_id", "channel_dir", "tab", "listing_rank", "url"])
            writer.writeheader()
            writer.writerows(rows)
        return path

    def rows(self, count=21):
        return [dict(video_id=f"{i:011d}", channel_dir="person", tab="videos", listing_rank=i,
                     url="https://attacker.invalid/") for i in range(count)]

    def test_only_twenty_and_canonical_urls(self):
        rows = ingest.select_queue(self.queue(self.rows()))
        self.assertEqual(len(rows), 20)
        self.assertEqual(rows[0]["url"], "https://www.youtube.com/watch?v=00000000000")

    def test_newest_fifty_retains_first_fifty_without_duration_filter(self):
        rows = ingest.select_queue(self.queue(self.rows(51)), newest=50)
        self.assertEqual(len(rows), 50)
        self.assertEqual(rows[-1]["listing_rank"], 49)
        with self.assertRaises(ValueError):
            ingest.select_queue(self.queue(self.rows(1)), newest=51)

    def test_bad_paths_ranks_tabs_rejected(self):
        for change in ({"channel_dir": "../outside"}, {"channel_dir": "C:/outside"},
                       {"listing_rank": "-1"}, {"listing_rank": ""}, {"tab": "shorts"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                ingest.select_queue(self.queue([dict(self.rows(1)[0], **change)]))

    def test_duplicate_rank_cannot_admit_twenty_one_items(self):
        rows = self.rows(21)
        rows[-1]["listing_rank"] = 0
        with self.assertRaisesRegex(ValueError, "duplicate listing ranks"):
            ingest.select_queue(self.queue(rows))

    def test_duplicate_ids_do_not_double_download(self):
        row = self.rows(1)[0]
        self.assertEqual(len(ingest.select_queue(self.queue([row, row]))), 1)

    def test_entire_queue_explicitly_includes_all_tabs_and_unknown_legacy_rank(self):
        rows = self.rows(24)
        rows[21].update(tab="shorts", listing_rank=0)
        rows[22].update(tab="streams", listing_rank=0)
        rows[23].update(tab="", listing_rank="")
        selected = ingest.select_queue(self.queue(rows), entire_queue=True)
        self.assertEqual(len(selected), 24)
        self.assertIsNone(selected[-1]["listing_rank"])


class VerificationTests(Fixture):
    def test_verified_hash_size_receipt_precedes_deletion(self):
        path, rec = self.recording()
        journal = self.root / "sync" / "drive_ingest_manifest.jsonl"
        result = ingest.verify_and_delete(self.root, rec, self.drive(rec), journal)
        self.assertFalse(path.exists())
        records = [json.loads(line) for line in journal.read_text().splitlines()]
        self.assertEqual([r["status"] for r in records], ["verified", "deleted"])
        self.assertEqual(result["drive_id"], "verified-drive-file-id")

    def test_missing_md5_wrong_md5_wrong_size_never_delete(self):
        path, rec = self.recording()
        for change in ({"Hashes": {}}, {"Hashes": {"MD5": "bad"}}, {"Size": rec["bytes"] + 1}):
            drive = self.drive(rec)
            drive.stat.return_value.update(change)
            with self.subTest(change=change), self.assertRaises(ingest.IngestError):
                ingest.verify_and_delete(self.root, rec, drive, self.root / "receipt.jsonl")
            self.assertTrue(path.exists())
            self.assertFalse((self.root / "receipt.jsonl").exists())

    def test_local_edit_before_upload_receipt_not_deleted(self):
        path, rec = self.recording()
        path.write_bytes(b"new private bytes")
        drive = self.drive(rec)
        with self.assertRaises(ingest.IngestError):
            ingest.verify_and_delete(self.root, rec, drive, self.root / "receipt.jsonl")
        drive.stat.assert_not_called()
        self.assertEqual(path.read_bytes(), b"new private bytes")

    def test_failed_receipt_write_never_deletes(self):
        path, rec = self.recording()
        with patch.object(ingest, "journal", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                ingest.verify_and_delete(self.root, rec, self.drive(rec), self.root / "receipt.jsonl")
        self.assertTrue(path.exists())

    def test_edit_during_verification_is_retained(self):
        path, rec = self.recording()
        drive = self.drive(rec)
        remote_metadata = drive.stat.return_value

        def changed(_):
            path.write_bytes(b"changed during upload verification")
            return remote_metadata

        drive.stat.side_effect = changed
        with self.assertRaises(ingest.IngestError):
            ingest.verify_and_delete(self.root, rec, drive, self.root / "receipt.jsonl")
        self.assertTrue(path.exists())

    def test_receipt_path_cannot_escape(self):
        with self.assertRaises(ingest.IngestError):
            ingest.local_path(self.root, "../outside.webm")


class RecoveryTests(Fixture):
    def args(self):
        return SimpleNamespace(root=self.root, download_only=False, remote="etdrive:", collect_metadata=False)

    def attempt(self, rec, drive, args=None):
        row = {"video_id": rec["video_id"], "channel_dir": rec["channel_dir"]}
        stop = threading.Event()
        result = ingest.ingest_one(args or self.args(), row, Mock(), Mock(), stop, drive,
                                   self.root / "sync" / "drive_ingest_manifest.jsonl", rec)
        return result, stop

    def test_upload_failure_retains_complete_audio_for_resume(self):
        path, rec = self.recording()
        drive = self.drive(rec)
        drive.copy.side_effect = ingest.IngestError("drive_upload", "Drive unavailable")
        result, stop = self.attempt(rec, drive)
        self.assertEqual(result, "error")
        self.assertTrue(stop.is_set())
        self.assertTrue(path.exists())
        state = ingest.load_state(self.root / "sync" / "drive_ingest_manifest.jsonl")
        self.assertEqual(state[rec["video_id"]]["sha256"], rec["sha256"])

    def test_uploaded_before_crash_reconciles_existing_complete_file(self):
        path, rec = self.recording()
        rec["status"] = "error"
        result, stop = self.attempt(rec, self.drive(rec))
        self.assertEqual(result, "deleted")
        self.assertFalse(path.exists())
        self.assertFalse(stop.is_set())

    def test_crash_before_rename_recovers_only_hashed_completed_partial(self):
        path, rec = self.recording()
        part = path.with_suffix(path.suffix + ".part")
        path.rename(part)
        rec["status"] = "download_complete"
        result, stop = self.attempt(rec, self.drive(rec))
        self.assertEqual(result, "deleted")
        self.assertFalse(path.exists())
        self.assertFalse(part.exists())
        self.assertFalse(stop.is_set())

    def test_prepared_final_without_hashes_fails_closed(self):
        path, rec = self.recording()
        rec = {k: v for k, v in rec.items() if k not in {"bytes", "md5", "sha256"}}
        rec["status"] = "prepared"
        drive = Mock()
        result, stop = self.attempt(rec, drive)
        self.assertEqual(result, "error")
        self.assertTrue(path.exists())
        drive.copy.assert_not_called()

    def test_download_only_reuses_existing_file_without_drive(self):
        path, rec = self.recording()
        args = self.args()
        args.download_only = True
        result, _ = self.attempt(rec, None, args)
        self.assertEqual(result, "downloaded")
        self.assertTrue(path.exists())


class RangeTests(Fixture):
    class Response(io.BytesIO):
        def __init__(self, body, status=206, content_range=None, declared_length=None, etag='"same"'):
            super().__init__(body)
            self.status = status
            self.headers = {"Content-Length": str(len(body) if declared_length is None else declared_length),
                            "ETag": etag}
            if content_range:
                self.headers["Content-Range"] = content_range

    def stream(self, responses, size=10):
        info = {"id": "12345678901", "url": "https://test.googlevideo.com/audio", "filesize": size}
        budget = ingest.Budget(self.root, 1000, 100, 0, reserve=5)
        opener = Mock()
        opener.open.side_effect = responses
        path = self.root / "audio.part"
        with patch.object(ingest.urllib.request, "build_opener", return_value=opener):
            result = ingest.stream_audio(info, path, budget, 10**9, threading.Event(), http_chunk_bytes=4)
        return result, path, opener

    def test_complete_contiguous_ranges_preserve_bytes_and_hashes(self):
        result, path, opener = self.stream([
            self.Response(b"abcd", content_range="bytes 0-3/10"),
            self.Response(b"efgh", content_range="bytes 4-7/10"),
            self.Response(b"ij", content_range="bytes 8-9/10")])
        self.assertEqual(path.read_bytes(), b"abcdefghij")
        self.assertEqual(result, ingest.hash_file(path))
        self.assertEqual([call.args[0].get_header("Range") for call in opener.open.call_args_list],
                         ["bytes=0-3", "bytes=4-7", "bytes=8-9"])

    def test_bad_range_offset_does_not_append_wrong_bytes(self):
        with self.assertRaises(ingest.IngestError):
            self.stream([self.Response(b"abcd", content_range="bytes 0-3/10"),
                         self.Response(b"fghi", content_range="bytes 5-8/10")])
        self.assertEqual((self.root / "audio.part").read_bytes(), b"abcd")

    def test_truncated_range_never_completes(self):
        with self.assertRaises(ingest.IngestError):
            self.stream([self.Response(b"abc", content_range="bytes 0-3/10", declared_length=4)])
        self.assertEqual((self.root / "audio.part").read_bytes(), b"abc")

    def test_initial_range_ignored_can_fall_back_to_full_response(self):
        result, path, opener = self.stream([self.Response(b"abcdefghij", status=200)])
        self.assertEqual(result["bytes"], 10)
        self.assertEqual(opener.open.call_count, 1)

    def test_later_range_ignored_fails_before_appending_duplicate_bytes(self):
        with self.assertRaises(ingest.IngestError):
            self.stream([self.Response(b"abcd", content_range="bytes 0-3/10"),
                         self.Response(b"abcdefghij", status=200)])
        self.assertEqual((self.root / "audio.part").read_bytes(), b"abcd")

    def test_changed_etag_fails_before_appending_different_edition(self):
        with self.assertRaises(ingest.IngestError):
            self.stream([self.Response(b"abcd", content_range="bytes 0-3/10"),
                         self.Response(b"efgh", content_range="bytes 4-7/10", etag='"changed"')])
        self.assertEqual((self.root / "audio.part").read_bytes(), b"abcd")

    def test_wrong_total_fails_before_first_write(self):
        with self.assertRaises(ingest.IngestError):
            self.stream([self.Response(b"abcd", content_range="bytes 0-3/11")])
        self.assertEqual((self.root / "audio.part").stat().st_size, 0)


class PairedMetadataTests(Fixture):
    def pair(self):
        audio, rec = self.recording()
        metadata = audio.with_suffix(".info.json")
        metadata.write_text('{"description":"research metadata"}', encoding="utf-8")
        rec["metadata"] = dict(ingest.hash_file(metadata), path="audio/person/12345678901.info.json",
                               remote="etdrive:person/YouTube native/12345678901.info.json")
        drive = Mock()
        records = {rec["remote"]: rec, rec["metadata"]["remote"]: rec["metadata"]}
        drive.stat.side_effect = lambda remote: {"Size": records[remote]["bytes"],
                                                  "Hashes": {"MD5": records[remote]["md5"]},
                                                  "IsDir": False, "ID": "id-" + Path(remote).suffix}
        return audio, metadata, rec, drive

    def test_both_uploaded_objects_are_verified_before_either_is_deleted(self):
        audio, metadata, rec, drive = self.pair()
        state = self.root / "sync" / "receipts.jsonl"
        done = ingest.verify_and_delete(self.root, rec, drive, state, require_metadata=True)
        self.assertFalse(audio.exists())
        self.assertFalse(metadata.exists())
        self.assertTrue(ingest.receipt_complete(done, rec, "etdrive:"))
        self.assertEqual(drive.stat.call_count, 2)

    def test_metadata_hash_mismatch_preserves_both_local_files(self):
        audio, metadata, rec, drive = self.pair()
        good_stat = drive.stat.side_effect
        drive.stat.side_effect = lambda remote: (dict(good_stat(remote), Hashes={"MD5": "wrong"})
                                                  if remote.endswith(".json") else good_stat(remote))
        with self.assertRaises(ingest.IngestError):
            ingest.verify_and_delete(self.root, rec, drive, self.root / "receipt.jsonl", require_metadata=True)
        self.assertTrue(audio.exists())
        self.assertTrue(metadata.exists())

    def missing_identity_retains_pair(self, extension):
        audio, metadata, rec, drive = self.pair()
        good_stat = drive.stat.side_effect

        def proof(remote):
            value = good_stat(remote)
            if remote.endswith(extension):
                value.pop("ID")
            return value

        drive.stat.side_effect = proof
        state = self.root / "receipt.jsonl"
        with self.assertRaisesRegex(ingest.IngestError, "identity is missing"):
            ingest.verify_and_delete(self.root, rec, drive, state, require_metadata=True)
        self.assertTrue(audio.exists())
        self.assertTrue(metadata.exists())
        self.assertFalse(state.exists())

    def test_missing_audio_id_preserves_both_local_files(self):
        self.missing_identity_retains_pair(".webm")

    def test_missing_metadata_id_preserves_both_local_files(self):
        self.missing_identity_retains_pair(".info.json")

    def test_audio_only_receipt_cannot_pass_completion_gate(self):
        _, rec = self.recording()
        rec.update(status="deleted", drive_id="audio-id")
        self.assertFalse(ingest.receipt_complete(rec, rec, "etdrive:"))

    def test_crash_after_audio_unlink_recovers_metadata_without_redownload(self):
        audio, metadata, rec, drive = self.pair()
        rec["status"] = "verified"
        audio.unlink()
        done = ingest.verify_and_delete(self.root, rec, drive, self.root / "receipt.jsonl",
                                        require_metadata=True, allow_missing=True)
        self.assertFalse(metadata.exists())
        self.assertEqual(done["status"], "deleted")

    def test_metadata_upload_failure_keeps_both_files(self):
        audio, metadata, rec, drive = self.pair()
        drive.copy_pair.side_effect = ingest.IngestError("drive_upload", "sidecar upload failed")
        args = SimpleNamespace(root=self.root, download_only=False, remote="etdrive:", collect_metadata=True)
        result = ingest.ingest_one(args, rec, Mock(), Mock(), threading.Event(), drive,
                                   self.root / "receipt.jsonl", rec)
        self.assertEqual(result, "error")
        self.assertTrue(audio.exists())
        self.assertTrue(metadata.exists())

    def test_batch_command_includes_only_the_exact_two_files(self):
        audio, metadata, rec, _ = self.pair()
        tool = Mock(return_value=SimpleNamespace(returncode=0))
        with patch.object(ingest, "run_tool", tool):
            ingest.Rclone("rclone").copy_pair(audio, metadata, rec["remote"], rec["metadata"]["remote"])
        command = tool.call_args.args[0]
        includes = [command[i + 1] for i, value in enumerate(command) if value == "--include"]
        self.assertEqual(includes, ["/12345678901.webm", "/12345678901.info.json"])
        self.assertIn("--max-depth", command)
        self.assertEqual(command[command.index("--transfers") + 1], "2")

    def test_normal_path_reuses_stream_hashes_without_local_rehash(self):
        audio, metadata, rec, drive = self.pair()
        trusted = {"audio": ingest.fingerprint(audio), "metadata": ingest.fingerprint(metadata)}
        with patch.object(ingest, "hash_file", side_effect=AssertionError("redundant local hash")):
            done = ingest.verify_and_delete(self.root, rec, drive, self.root / "receipt.jsonl",
                                            require_metadata=True, trusted=trusted)
        self.assertEqual(done["status"], "deleted")
        self.assertEqual(drive.stat.call_count, 2)

    def test_old_remote_audio_gets_metadata_backfill_without_audio_download(self):
        audio, rec = self.recording()
        audio.unlink()
        rec.update(status="deleted", drive_id="old-audio-id")
        args = SimpleNamespace(root=self.root, download_only=False, remote="etdrive:", collect_metadata=True)
        budget = ingest.Budget(self.root, 1_000_000, 100_000, 0, reserve=10)
        drive = Mock()

        def stat(remote):
            expected = ingest.hash_file(self.root / "audio/person/12345678901.info.json") if remote.endswith(".json") else rec
            return {"Size": expected["bytes"], "Hashes": {"MD5": expected["md5"]}, "ID": "remote-id", "IsDir": False}

        drive.stat.side_effect = stat
        builder = SimpleNamespace(build_metadata=lambda info, row, captured_at: {"metadata": info, "captured_at": captured_at})
        with patch.dict(sys.modules, {"media_metadata": builder}), \
                patch.object(ingest, "extract_audio", return_value={"id": rec["video_id"], "description": "all metadata"}) as extract, \
                patch.object(ingest, "stream_audio") as stream:
            result = ingest.ingest_one(args, rec, budget, Mock(), threading.Event(), drive,
                                       self.root / "receipt.jsonl", rec)
        self.assertEqual(result, "deleted")
        extract.assert_called_once()
        stream.assert_not_called()
        self.assertEqual(drive.copy.call_count, 1)
        self.assertTrue(str(drive.copy.call_args.args[0]).endswith(".info.json"))


class RunControlTests(Fixture):
    def args(self):
        return SimpleNamespace(root=self.root, max_local_bytes=100_000_000,
                               max_item_bytes=0, min_free_bytes=0, rclone="unused",
                               rclone_config=None, download_only=False, collect_metadata=True,
                               remote="etdrive:", limit=0, min_interval=0, workers=2)

    def test_persistent_stop_marker_prevents_all_requests_and_is_not_removed(self):
        marker = self.root / "sync" / "STOP_DRIVE_INGEST"
        marker.parent.mkdir()
        marker.touch()
        with patch.object(ingest, "Rclone") as drive, patch.object(ingest, "extract_audio") as extract:
            result = ingest.run(self.args(), [])
        self.assertEqual(result, 130)
        self.assertTrue(marker.exists())
        drive.assert_not_called()
        extract.assert_not_called()

    def test_stop_control_wait_detects_persistent_marker(self):
        marker = self.root / "STOP"
        control = ingest.StopControl(marker)
        self.assertFalse(control.is_set())
        marker.touch()
        self.assertTrue(control.wait(60))

    def test_storage_deferred_item_retries_once_after_other_items_finish(self):
        rows = [{"video_id": "00000000001", "channel_dir": "first"},
                {"video_id": "00000000002", "channel_dir": "second"}]
        calls = {row["video_id"]: 0 for row in rows}

        def attempt(args, row, *unused, **options):
            key = row["video_id"]
            calls[key] += 1
            return "deferred_storage" if key == "00000000001" and calls[key] == 1 else "deleted"

        with patch.object(ingest, "Rclone", return_value=Mock()), patch.object(ingest, "ingest_one", side_effect=attempt):
            result = ingest.run(self.args(), rows)
        self.assertEqual(result, 0)
        self.assertEqual(calls, {"00000000001": 2, "00000000002": 1})

    def test_storage_deferral_without_available_buffer_stays_incomplete(self):
        rows = [{"video_id": "00000000001", "channel_dir": "first"}]
        with patch.object(ingest, "Rclone", return_value=Mock()), \
                patch.object(ingest, "ingest_one", return_value="deferred_storage") as attempt:
            result = ingest.run(self.args(), rows)
        self.assertEqual(result, 3)
        attempt.assert_called_once()


if __name__ == "__main__":
    unittest.main()
