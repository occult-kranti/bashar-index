"""Independent checks for buffer admission, archive compatibility and Drive rest."""
import io
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
    def __init__(self, body, length):
        super().__init__(body)
        self.headers = {"Content-Length": str(length)}
        self.status = 200
        self.body_reads = 0

    def read(self, size=-1):
        self.body_reads += 1
        return super().read(size)

    read1 = read


class LimitsReview(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.row = {"video_id": "abcdefghijk", "channel_dir": "channel", "tab": "videos"}

    def test_default_buffer_admits_recording_larger_than_one_gigabyte(self):
        defaults = ingest.parser().parse_args(["run"])
        self.assertEqual(defaults.max_item_mb, 0)
        budget = ingest.Budget(self.root, 19_000_000_000, 0, 0)
        with patch.object(ingest.shutil, "disk_usage", return_value=SimpleNamespace(free=10**12)):
            budget.reserve_item("large", self.root / "large.part", 2_000_000_000,
                                ingest.METADATA_HEADROOM)
        self.assertEqual(budget.active["large"]["bytes"], 2_000_000_000 + ingest.METADATA_HEADROOM)

    def test_very_long_duration_is_not_rejected_by_metadata_selection(self):
        info = {"id": self.row["video_id"], "duration": 365 * 86400, "filesize": 2_000_000_000,
                "vcodec": "none", "acodec": "opus", "ext": "webm", "protocol": "https",
                "url": "https://rr1.googlevideo.com/videoplayback", "is_live": False}
        result = SimpleNamespace(returncode=0, stdout=json.dumps(info), stderr="")
        args = SimpleNamespace(ytdlp="unused", timeout=1, max_item_bytes=0)
        with patch.object(ingest, "run_tool", return_value=result) as tool:
            selected = ingest.extract_audio(args, dict(self.row, url="https://www.youtube.com/watch?v=abcdefghijk"))
        self.assertEqual(selected["duration"], 365 * 86400)
        tool.assert_called_once()

    def test_parallel_reservations_include_each_metadata_allowance(self):
        cap = 19_000_000_000
        per_audio = (cap - ingest.JOURNAL_RESERVE) // 4
        budget = ingest.Budget(self.root, cap, 0, 0)
        ready = threading.Barrier(4)

        def reserve(index):
            ready.wait(timeout=5)
            try:
                budget.reserve_item(str(index), self.root / f"{index}.part", per_audio,
                                    ingest.METADATA_HEADROOM)
            except ingest.IngestError as error:
                self.assertEqual(error.kind, "deferred_storage")
                return False
            return True

        with patch.object(ingest.shutil, "disk_usage", return_value=SimpleNamespace(free=10**12)):
            with ThreadPoolExecutor(max_workers=4) as pool:
                outcomes = list(pool.map(reserve, range(4)))
        self.assertEqual(outcomes.count(True), 3)
        self.assertLessEqual(sum(item["bytes"] for item in budget.active.values()), cap - ingest.JOURNAL_RESERVE)
        self.assertEqual(ingest.tree_bytes(self.root), 0)

    def test_unknown_size_header_must_fit_with_other_reserved_recordings_before_body_read(self):
        mib = 1024 * 1024
        budget = ingest.Budget(self.root, 20 * mib, 0, 0, reserve=mib)
        part = self.root / "unknown.part"
        budget.reserve_item("unknown", part)
        budget.reserve_item("other", self.root / "other.part", 10 * mib)
        response = Response(b"body must not be consumed", 12 * mib)
        opener = Mock()
        opener.open.return_value = response
        with patch.object(ingest.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(ingest.IngestError) as raised:
                ingest.stream_audio({"url": "https://rr1.googlevideo.com/videoplayback"}, part,
                                    budget, 10**12, threading.Event())
        self.assertEqual(raised.exception.kind, "deferred_storage")
        self.assertEqual(response.body_reads, 0)
        self.assertEqual(part.stat().st_size, 0)

    def test_unknown_size_complete_response_is_admitted_and_hashed(self):
        budget = ingest.Budget(self.root, 20_000_000, 0, 0, reserve=0)
        part = self.root / "unknown.part"
        budget.reserve_item("unknown", part)
        response = Response(b"whole audio", 11)
        opener = Mock()
        opener.open.return_value = response
        with patch.object(ingest.urllib.request, "build_opener", return_value=opener):
            measured = ingest.stream_audio({"url": "https://rr1.googlevideo.com/videoplayback"}, part,
                                           budget, 10**12, threading.Event())
        self.assertEqual(measured, ingest.hash_file(part))
        self.assertEqual(budget.active["unknown"]["bytes"], 11)

    def test_archive_category_uses_source_tab_even_when_duration_suggests_otherwise(self):
        for tab, duration, folder in [("videos", 3, "Videos"), ("shorts", 86400, "Shorts"),
                                      ("streams", 2, "Recorded streams"), ("", 50, "Unclassified")]:
            row = dict(self.row, tab=tab, duration_s=duration)
            self.assertEqual(ingest.remote_path("etdrive:04 Audio", row, "webm"),
                             f"etdrive:04 Audio/channel/{folder}/abcdefghijk.webm")

    def test_legacy_verified_pair_keeps_original_folder_and_exact_destination_boundary(self):
        old = "etdrive:04 Audio/channel/YouTube native/abcdefghijk.webm"
        metadata_remote = old.rpartition("/")[0] + "/abcdefghijk.info.json"
        record = {"status": "deleted", "path": "audio/channel/abcdefghijk.webm", "remote": old,
                  "drive_id": "audio-id", "md5": "m", "sha256": "s",
                  "metadata": {"remote": metadata_remote, "drive_id": "metadata-id", "md5": "mm", "sha256": "ss"}}
        self.assertTrue(ingest.receipt_complete(record, self.row, "etdrive:04 Audio"))
        self.assertEqual(ingest.item_remote_path("etdrive:04 Audio", self.row, "info.json", record), metadata_remote)
        for remote, row in [("wrong:04 Audio", self.row), ("etdrive:04 Audio other", self.row),
                            ("etdrive:04 Audio", dict(self.row, video_id="lmnopqrstuv")),
                            ("etdrive:04 Audio", dict(self.row, channel_dir="other"))]:
            self.assertFalse(ingest.receipt_complete(record, row, remote))

    def test_quota_failure_is_durable_before_next_instance_can_send_a_request(self):
        path = self.root / "sync" / "drive_ingest_cooldown.json"
        failure = SimpleNamespace(returncode=1, stdout="", stderr="HTTP 403 rateLimitExceeded SECRET_PRIVATE")
        first = ingest.Rclone("unused", cooldown_path=path)
        with patch.object(ingest, "run_tool", return_value=failure) as tool:
            with self.assertRaises(ingest.IngestError) as raised:
                first.stat("etdrive:existing.webm")
            self.assertEqual(raised.exception.kind, "drive_rate_limited")
            saved = json.loads(path.read_text())
            self.assertGreater(saved["until_epoch"], time.time())
            self.assertEqual(saved["reason"], "rateLimitExceeded")
            self.assertNotIn("SECRET_PRIVATE", path.read_text())
            second = ingest.Rclone("unused", cooldown_path=path)
            with self.assertRaises(ingest.IngestError) as held:
                second.stat("etdrive:existing.webm")
            self.assertEqual(held.exception.kind, "drive_cooldown")
            tool.assert_called_once()

    def test_active_durable_cooldown_stops_run_before_connection_or_youtube(self):
        path = self.root / "sync" / "drive_ingest_cooldown.json"
        ingest.write_drive_cooldown(path, "rateLimitExceeded")
        args = SimpleNamespace(root=self.root, download_only=False)
        with patch.object(ingest, "Rclone") as drive, patch.object(ingest, "extract_audio") as youtube:
            result = ingest.run(args, [self.row])
        self.assertEqual(result, 75)
        drive.assert_not_called()
        youtube.assert_not_called()

    def test_worker_already_waiting_for_drive_observes_new_quota_cooldown(self):
        path = self.root / "sync" / "drive_ingest_cooldown.json"
        entered, release = threading.Event(), threading.Event()

        def response(*args, **kwargs):
            entered.set()
            self.assertTrue(release.wait(timeout=5))
            return SimpleNamespace(returncode=1, stdout="", stderr="HTTP 403 rateLimitExceeded")

        def request():
            try:
                ingest.Rclone("unused", cooldown_path=path).stat("etdrive:existing.webm")
            except ingest.IngestError as error:
                return error.kind
            self.fail("quota-limited request unexpectedly succeeded")

        with patch.object(ingest, "_DRIVE_CALLS", threading.BoundedSemaphore(1)), \
                patch.object(ingest, "run_tool", side_effect=response) as tool:
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(request)
                self.assertTrue(entered.wait(timeout=5))
                second = pool.submit(request)
                release.set()
                outcomes = [first.result(timeout=10), second.result(timeout=10)]
            self.assertEqual(outcomes, ["drive_rate_limited", "drive_cooldown"])
            tool.assert_called_once()


if __name__ == "__main__":
    unittest.main()
