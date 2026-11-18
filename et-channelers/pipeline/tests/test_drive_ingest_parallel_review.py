"""Independent crash-recovery and bounded download-only review regressions."""
import contextlib
import io
import json
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import drive_ingest as ingest


class ParallelReview(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.state = self.root / "sync/drive_ingest_manifest.jsonl"
        self.addCleanup(lambda: ingest._ROOT_BUDGETS.pop(self.root.resolve(), None))

    def args(self, **changes):
        defaults = dict(root=self.root, max_local_bytes=100_000_000, max_item_bytes=0,
                        min_free_bytes=0, rclone="unused", rclone_config=None, download_only=False,
                        collect_metadata=True, remote="etdrive:04 Audio", limit=0, min_interval=0,
                        workers=4, upload_transfers=2, upload_batch_items=8, upload_batch_seconds=0,
                        ready_items=16, rate_bytes=1024 * 1024, http_chunk_bytes=0)
        return SimpleNamespace(**dict(defaults, **changes))

    def pair(self, number=1, with_metadata=True):
        row = dict(video_id=f"{number:011d}", channel_dir=f"channel-{number}", tab="videos",
                   listing_rank="0", url=f"https://www.youtube.com/watch?v={number:011d}")
        path = self.root / f"audio/{row['channel_dir']}/Videos/{row['video_id']}.webm"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"native invented audio" * 20)
        rec = dict(row, **ingest.hash_file(path), path=path.relative_to(self.root).as_posix(),
                   remote=ingest.remote_path(self.args().remote, row, "webm"), status="downloaded")
        if with_metadata:
            metadata = path.with_suffix(".info.json")
            metadata.write_text('{"invented":true}', encoding="utf-8")
            rec["metadata"] = dict(ingest.hash_file(metadata), path=metadata.relative_to(self.root).as_posix(),
                                   remote=ingest.remote_path(self.args().remote, row, "info.json"))
        return row, rec

    def drive(self, rec):
        drive = Mock()
        proofs = {expected["remote"]: {"Size": expected["bytes"], "Hashes": {"MD5": expected["md5"]},
                                       "ID": kind + "-object", "IsDir": False}
                  for kind, expected in (("audio", rec), ("metadata", rec["metadata"]))}
        drive.stat.side_effect = lambda remote: proofs[remote]
        drive.stat_batch.return_value = {ingest.remote_relative(self.args().remote, remote): proof
                                        for remote, proof in proofs.items()}
        return drive

    def test_high_pressure_recovers_existing_audio_that_lacks_metadata(self):
        row, rec = self.pair(with_metadata=False)
        ingest.journal(self.state, rec)
        info = dict(id=row["video_id"], ext="webm", duration=60, vcodec="none")
        metadata_path = (self.root / rec["path"]).with_suffix(".info.json")

        def upload(args, items, *unused):
            self.assertTrue(metadata_path.exists())
            return [ingest.IngestResult(item.row, item.record, status="deleted") for item in items]

        with patch.object(ingest, "Rclone", return_value=Mock()), \
                patch.object(ingest, "extract_audio", return_value=info) as extract, \
                patch.object(ingest, "stream_audio") as stream, \
                patch.object(ingest, "upload_batch", side_effect=upload), \
                patch.object(ingest.Budget, "pressure", lambda budget: 0.1 if metadata_path.exists() else 0.9), \
                contextlib.redirect_stdout(io.StringIO()):
            result = ingest.run(self.args(), [row])
        self.assertEqual(result, 0, "existing audio must be allowed to complete its sidecar under pressure")
        extract.assert_called_once()
        stream.assert_not_called()

    def test_pressure_recovery_still_respects_youtube_rest_for_missing_metadata(self):
        row, rec = self.pair(with_metadata=False)
        rec["retry_not_before_epoch"] = 10**12
        ingest.journal(self.state, rec)
        with patch.object(ingest, "Rclone", return_value=Mock()), \
                patch.object(ingest, "extract_audio") as extract, \
                patch.object(ingest.Budget, "pressure", return_value=0.9), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = ingest.run(self.args(), [row])
        self.assertEqual(result, 3)
        extract.assert_not_called()

    def test_download_only_limit_twelve_ignores_drive_cooldown_without_drive_calls(self):
        ingest.write_drive_cooldown(self.root / "sync/drive_ingest_cooldown.json")
        rows = [dict(video_id=f"{n:011d}", channel_dir=f"channel-{n}", tab="videos",
                     listing_rank="0", url=f"https://www.youtube.com/watch?v={n:011d}") for n in range(1, 14)]

        def extract(args, row):
            return dict(id=row["video_id"], ext="webm", filesize=100, duration=60, vcodec="none")

        def stream(info, part, budget, *unused):
            with part.open("wb") as handle:
                budget.write(handle, b"x" * 100)
            return ingest.hash_file(part)

        with patch.object(ingest, "Rclone") as drive, patch.object(ingest, "extract_audio", side_effect=extract) as source, \
                patch.object(ingest, "stream_audio", side_effect=stream), contextlib.redirect_stdout(io.StringIO()):
            result = ingest.run(self.args(download_only=True, limit=12, max_local_bytes=2_000_000_000), rows)
        self.assertEqual(result, 0)
        drive.assert_not_called()
        self.assertEqual(source.call_count, 12)
        state = ingest.load_state(self.state)
        self.assertEqual(len(state), 12)
        self.assertTrue(all((self.root / rec["path"]).exists() and
                            (self.root / rec["metadata"]["path"]).exists() for rec in state.values()))
        self.assertLess(ingest.tree_bytes(self.root), 2_000_000_000)

    def test_audio_promotion_keeps_reservation_checks_outside_the_path_transition(self):
        row = dict(video_id="00000000001", channel_dir="channel-1", tab="videos",
                   listing_rank="0", url="https://www.youtube.com/watch?v=00000000001")
        args = self.args(download_only=True)
        budget = ingest.Budget(self.root, args.max_local_bytes, 0, 0, cached=True)
        ingest._ROOT_BUDGETS[self.root.resolve()] = budget
        promoted, release_promotion, reservation_started = (threading.Event() for _ in range(3))
        budget_was_available = []
        original_replace = ingest.os.replace

        def stream(info, part, current_budget, *unused):
            with part.open("wb") as handle:
                current_budget.write(handle, b"x" * 100)
            return ingest.hash_file(part)

        def hold_promoted_path(source, destination):
            original_replace(source, destination)
            if str(source).endswith(".webm.part"):
                promoted.set()
                self.assertTrue(release_promotion.wait(timeout=3))

        def reserve_next_item():
            self.assertTrue(promoted.wait(timeout=3))
            available = budget.lock.acquire(blocking=False)
            budget_was_available.append(available)
            if available:
                budget.lock.release()
            reservation_started.set()
            budget.reserve_item("next", self.root / "next.webm.part", 100)

        info = dict(id=row["video_id"], ext="webm", filesize=100, duration=60, vcodec="none")
        with patch.object(ingest, "extract_audio", return_value=info), \
                patch.object(ingest, "stream_audio", side_effect=stream), \
                patch.object(ingest.os, "replace", side_effect=hold_promoted_path), \
                ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(ingest.ingest_one, args, row, budget, Mock(), threading.Event(),
                                None, self.state)
            second = pool.submit(reserve_next_item)
            try:
                self.assertTrue(reservation_started.wait(timeout=3))
                # Reservation checks cannot observe a renamed partial while its
                # active slot still points to the old path.
                self.assertEqual(budget_was_available, [False])
            finally:
                release_promotion.set()
            self.assertEqual(first.result(timeout=3), "downloaded")
            second.result(timeout=3)
        self.assertTrue((self.root / "audio/channel-1/Videos/00000000001.webm").is_file())

    def test_crash_between_pair_deletions_resumes_from_durable_verified_receipt(self):
        row, rec = self.pair()
        drive = self.drive(rec)
        original_remove = ingest.remove_local
        calls = []

        def fail_second(path, *args, **kwargs):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("invented interruption after audio deletion")
            return original_remove(path, *args, **kwargs)

        with patch.object(ingest, "remove_local", side_effect=fail_second):
            with self.assertRaises(OSError):
                ingest.verify_and_delete(self.root, rec, drive, self.state, require_metadata=True)
        prior = ingest.load_state(self.state)[row["video_id"]]
        self.assertEqual(prior["status"], "verified")
        self.assertFalse((self.root / rec["path"]).exists())
        self.assertTrue((self.root / rec["metadata"]["path"]).exists())
        results = ingest.upload_batch(self.args(), [ingest.IngestResult(row, prior, allow_missing=True)],
                                      drive, self.state, threading.Event())
        self.assertEqual(results[0].status, "deleted")
        self.assertFalse((self.root / rec["metadata"]["path"]).exists())
        self.assertTrue(ingest.receipt_complete(ingest.load_state(self.state)[row["video_id"]], row, self.args().remote))

    def test_cached_byte_count_remains_exact_during_upload_retirement_and_new_download(self):
        row, rec = self.pair()
        budget = ingest.Budget(self.root, 20_000, 0, 0, reserve=2_000, cached=True)
        ingest._ROOT_BUDGETS[self.root.resolve()] = budget
        drive = self.drive(rec)
        start = threading.Barrier(2)

        def write_new():
            start.wait(timeout=3)
            with (self.root / "next.part").open("wb") as handle:
                for _ in range(100):
                    budget.write(handle, b"x" * 100)

        def retire():
            start.wait(timeout=3)
            ingest.verify_and_delete(self.root, rec, drive, self.state, require_metadata=True)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(write_new), pool.submit(retire)]
            for future in futures:
                future.result(timeout=5)
        self.assertEqual(budget.usage(), ingest.tree_bytes(self.root))
        self.assertLessEqual(budget.usage(), budget.cap)


if __name__ == "__main__":
    unittest.main()
