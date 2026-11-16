"""Offline contracts for bounded stages, exact batch proofs, and owned-byte accounting."""
from __future__ import annotations

import concurrent.futures as cf
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


class StageFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / 'sync' / 'drive_ingest_manifest.jsonl'
        self.addCleanup(lambda: ingest._ROOT_BUDGETS.pop(self.root.resolve(), None))

    def args(self, **options):
        base = dict(root=self.root, max_local_bytes=100_000_000, max_item_bytes=0,
                    min_free_bytes=0, rclone='unused', rclone_config=None, download_only=False,
                    collect_metadata=True, remote='etdrive:04 Audio', limit=0,
                    min_interval=0, workers=4, upload_transfers=2, upload_batch_items=8,
                    upload_batch_seconds=0, ready_items=16, rate_bytes=1024 * 1024)
        return SimpleNamespace(**dict(base, **options))

    def item(self, number=1, legacy=False):
        row = dict(video_id=f'{number:011d}', channel_dir=f'channel-{number}', tab='videos')
        folder = f"audio/{row['channel_dir']}" + ('' if legacy else '/Videos')
        audio = self.root / folder / f"{row['video_id']}.webm"
        audio.parent.mkdir(parents=True, exist_ok=True)
        audio.write_bytes(b'audio fixture' + bytes([number]))
        metadata = audio.with_suffix('.info.json')
        metadata.write_text(json.dumps({'id': row['video_id']}), encoding='utf-8')
        rec = dict(row, **ingest.hash_file(audio), path=audio.relative_to(self.root).as_posix(),
                   remote=ingest.remote_path(self.args().remote, row, 'webm', legacy=legacy), status='queued_upload')
        rec['metadata'] = dict(ingest.hash_file(metadata), path=metadata.relative_to(self.root).as_posix(),
                               remote=ingest.remote_path(self.args().remote, row, 'info.json', legacy=legacy))
        return ingest.IngestResult(row, rec)

    def proof_drive(self, items):
        drive = Mock()
        proofs = {}
        for item in items:
            for expected in (item.record, item.record['metadata']):
                path = ingest.remote_relative(self.args().remote, expected['remote'])
                proofs[path] = {'Path': path, 'Size': expected['bytes'], 'Hashes': {'MD5': expected['md5']},
                                'ID': path, 'IsDir': False}
        drive.stat_batch.return_value = proofs
        return drive

    def files_exist(self, item):
        return all((self.root / rec['path']).exists() for rec in (item.record, item.record['metadata']))


class BatchTests(StageFixture):
    def test_cross_channel_batch_uploads_once_and_verifies_once_before_pair_deletion(self):
        items = [self.item(1), self.item(2)]
        drive = self.proof_drive(items)
        expected = set(drive.stat_batch.return_value)

        def copied(root, remote, manifest, transfers):
            self.assertEqual(root, self.root / 'audio')
            self.assertEqual(set(manifest.read_text().splitlines()), expected)
            self.assertTrue(all(self.files_exist(item) for item in items))
            self.assertEqual(transfers, 2)

        def checked(remote, paths, manifest):
            self.assertEqual(set(paths), expected)
            self.assertEqual(set(manifest.read_text().splitlines()), expected)
            self.assertTrue(all(self.files_exist(item) for item in items))
            return drive.stat_batch.return_value

        drive.copy_batch.side_effect = copied
        drive.stat_batch.side_effect = checked
        results = ingest.upload_batch(self.args(), items, drive, self.state, threading.Event())
        self.assertEqual([r.status for r in results], ['deleted', 'deleted'])
        self.assertFalse(any(self.files_exist(item) for item in items))
        drive.copy_batch.assert_called_once()
        drive.stat_batch.assert_called_once()
        drive.copy.assert_not_called()
        drive.copy_pair.assert_not_called()
        drive.stat.assert_not_called()
        self.assertFalse((self.root / 'sync' / 'drive_ingest_batch_files.txt').exists())
        records = [json.loads(line) for line in self.state.read_text().splitlines()]
        self.assertEqual([r['status'] for r in records], ['verified', 'deleted', 'verified', 'deleted'])

    def test_one_bad_or_missing_proof_retains_every_pair(self):
        for fault in ('missing', 'size', 'md5', 'identity'):
            with self.subTest(fault=fault):
                items = [self.item(1), self.item(2)]
                drive = self.proof_drive(items)
                key = list(drive.stat_batch.return_value)[-1]
                if fault == 'missing':
                    del drive.stat_batch.return_value[key]
                elif fault == 'size':
                    drive.stat_batch.return_value[key]['Size'] += 1
                elif fault == 'md5':
                    drive.stat_batch.return_value[key]['Hashes'] = {}
                else:
                    drive.stat_batch.return_value[key]['ID'] = ''
                stop = threading.Event()
                results = ingest.upload_batch(self.args(), items, drive, self.state, stop)
                self.assertEqual([r.status for r in results], ['error', 'error'])
                self.assertTrue(stop.is_set())
                self.assertTrue(all(self.files_exist(item) for item in items))

    def test_legacy_pairs_keep_paths_but_share_one_verification(self):
        items = [self.item(1, legacy=True), self.item(2)]
        drive = self.proof_drive(items)
        results = ingest.upload_batch(self.args(), items, drive, self.state, threading.Event())
        self.assertEqual([r.status for r in results], ['deleted', 'deleted'])
        drive.copy_batch.assert_called_once()
        drive.copy_pair.assert_called_once()
        drive.stat_batch.assert_called_once()
        self.assertIn('/YouTube native/', results[0].record['remote'])

    def test_later_pair_failure_does_not_overwrite_prior_deleted_receipt(self):
        items = [self.item(1), self.item(2)]
        drive = self.proof_drive(items)
        original = ingest.verify_and_delete

        def retire(root, rec, *args, **kwargs):
            if rec['video_id'] == items[1].row['video_id']:
                raise ingest.IngestError('local_changed', 'fixture changed')
            return original(root, rec, *args, **kwargs)

        with patch.object(ingest, 'verify_and_delete', side_effect=retire):
            results = ingest.upload_batch(self.args(), items, drive, self.state, threading.Event())
        self.assertEqual([r.status for r in results], ['deleted', 'error'])
        self.assertEqual(ingest.load_state(self.state)[items[0].row['video_id']]['status'], 'deleted')
        self.assertTrue(self.files_exist(items[1]))

    def test_exact_batch_metadata_rejects_duplicate_paths_ids_extras_and_missing(self):
        valid = [{'Path': 'channel/Videos/item.webm', 'ID': 'one'},
                 {'Path': 'channel/Videos/item.info.json', 'ID': 'two'}]
        paths = [value['Path'] for value in valid]
        cases = [valid + [valid[0]], [valid[0]], valid + [{'Path': 'other', 'ID': 'three'}],
                 [valid[0], dict(valid[1], ID='one')], {'Path': paths[0]}]
        for entries in cases:
            with self.subTest(entries=entries), patch.object(ingest, 'run_tool', return_value=SimpleNamespace(
                    returncode=0, stdout=json.dumps(entries))):
                with self.assertRaises(ingest.IngestError):
                    ingest.Rclone('unused').stat_batch(self.args().remote, paths, self.root / 'manifest')

    def test_batch_commands_use_direct_exact_file_lookup_not_archive_traversal(self):
        tool = Mock(return_value=SimpleNamespace(returncode=0, stdout='[]'))
        with patch.object(ingest, 'run_tool', tool):
            drive = ingest.Rclone('unused')
            drive.copy_batch(self.root, self.args().remote, self.root / 'manifest')
            drive.stat_batch(self.args().remote, [], self.root / 'manifest')
        for call in tool.call_args_list:
            self.assertIn('--files-from-raw', call.args[0])
            self.assertIn('--no-traverse', call.args[0])
        self.assertIn('--hash-type', tool.call_args_list[-1].args[0])


class OwnedAccountingTests(StageFixture):
    def budget(self, cap=10000, reserve=500):
        budget = ingest.Budget(self.root, cap, 0, 0, reserve=reserve, cached=True)
        ingest._ROOT_BUDGETS[self.root.resolve()] = budget
        return budget

    def test_owned_writes_do_not_walk_tree_per_network_chunk(self):
        with patch.object(ingest, 'tree_bytes', wraps=ingest.tree_bytes) as scan:
            budget = self.budget()
            with open(self.root / 'audio.part', 'wb') as out:
                for _ in range(200):
                    budget.write(out, b'abcdef')
            self.assertEqual(budget.usage(), 1200)
            self.assertEqual(scan.call_count, 1)

    def test_parallel_writes_cannot_spend_same_bytes(self):
        budget = self.budget(cap=1000, reserve=50)
        barrier = threading.Barrier(4)

        def write(number):
            barrier.wait()
            with open(self.root / str(number), 'wb') as out:
                for _ in range(20):
                    try:
                        budget.write(out, b'x' * 20)
                    except ingest.IngestError:
                        return

        with cf.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(write, range(4)))
        self.assertLessEqual(ingest.tree_bytes(self.root), 950)
        self.assertEqual(budget.usage(), ingest.tree_bytes(self.root))

    def test_journal_control_replacement_and_unlink_track_exact_bytes(self):
        budget = self.budget()
        ingest.journal(self.state, {'video_id': '00000000001', 'status': 'queued_upload'})
        ingest.control_file(self.root / 'sync' / 'control.json', b'old', atomic=True)
        ingest.control_file(self.root / 'sync' / 'control.json', b'new-longer', atomic=True)
        with ingest.batch_manifest(self.root, ['channel/Videos/id.webm']):
            self.assertEqual(budget.usage(), ingest.tree_bytes(self.root))
        self.assertEqual(budget.usage(), ingest.tree_bytes(self.root))
        ingest.remove_local(self.root / 'sync' / 'control.json')
        self.assertEqual(budget.usage(), ingest.tree_bytes(self.root))

    def test_control_and_journal_cannot_exceed_cap_after_media_fills_buffer(self):
        budget = self.budget(cap=2000, reserve=100)
        with open(self.root / 'data', 'wb') as out:
            budget.write(out, b'x' * 1900)
        for action in (lambda: ingest.control_file(self.root / 'control', b'x' * 101),
                       lambda: ingest.journal(self.state, {'payload': 'x' * 101})):
            with self.assertRaises(ingest.IngestError):
                action()
        self.assertEqual(budget.usage(), 1900)

    def test_periodic_reconciliation_counts_external_control_files(self):
        budget = self.budget()
        (self.root / 'external-supervisor-record').write_bytes(b'control')
        budget._reconciled_at -= 13
        self.assertEqual(budget.usage(), len(b'control'))


class StageSchedulingTests(StageFixture):
    def test_high_buffer_pressure_drains_existing_pair_before_new_source_work(self):
        item = self.item(1)
        ingest.journal(self.state, item.record)
        new_row = dict(video_id='00000000002', channel_dir='channel-2')
        drive = self.proof_drive([item])
        prepared = []

        def prepare(args, row, *unused, **options):
            prepared.append(row['video_id'])
            if row == item.row:
                return item
            self.assertFalse(self.files_exist(item), 'new source work started before pressure was relieved')
            return 'deleted'

        with patch.object(ingest, 'Rclone', return_value=drive), \
                patch.object(ingest, 'ingest_one', side_effect=prepare), \
                patch.object(ingest.Budget, 'pressure', lambda budget: 0.9 if self.files_exist(item) else 0.1):
            result = ingest.run(self.args(), [item.row, new_row])
        self.assertEqual(result, 0)
        self.assertEqual(prepared, [item.row['video_id'], new_row['video_id']])

    def test_stop_marker_retains_ready_pair_without_starting_upload(self):
        item = self.item(1)
        drive = self.proof_drive([item])

        def prepare(*unused, **options):
            (self.root / 'sync' / 'STOP_DRIVE_INGEST').touch()
            ingest.journal(self.state, item.record)
            return item

        with patch.object(ingest, 'Rclone', return_value=drive), \
                patch.object(ingest, 'ingest_one', side_effect=prepare):
            result = ingest.run(self.args(), [item.row])
        self.assertEqual(result, 130)
        self.assertTrue(self.files_exist(item))
        drive.copy_batch.assert_not_called()
        drive.stat_batch.assert_not_called()

    def test_next_download_runs_while_prior_upload_waits(self):
        rows = [dict(video_id=f'{n:011d}', channel_dir='same-channel') for n in (1, 2)]
        uploading, second_download = threading.Event(), threading.Event()

        def prepare(args, row, *unused, **options):
            self.assertTrue(options['stage_only'])
            if row == rows[1]:
                self.assertTrue(uploading.wait(2), 'upload stage never ran independently')
                second_download.set()
            return ingest.IngestResult(row, dict(row))

        def upload(args, items, *unused):
            if items[0].row == rows[0]:
                uploading.set()
                self.assertTrue(second_download.wait(2), 'source worker waited for upload completion')
            return [ingest.IngestResult(item.row, item.record, status='deleted') for item in items]

        with patch.object(ingest, 'Rclone', return_value=Mock()), \
                patch.object(ingest, 'ingest_one', side_effect=prepare), \
                patch.object(ingest, 'upload_batch', side_effect=upload):
            result = ingest.run(self.args(workers=1, ready_items=2, upload_batch_items=1), rows)
        self.assertEqual(result, 0)
        self.assertTrue(second_download.is_set())

    def test_slow_upload_bounds_combined_ready_and_downloading_items(self):
        rows = [dict(video_id=f'{n:011d}', channel_dir=f'channel-{n}') for n in range(1, 7)]
        upload_started, release_upload = threading.Event(), threading.Event()
        calls, calls_lock = [], threading.Lock()

        def prepare(args, row, *unused, **options):
            with calls_lock:
                calls.append(row['video_id'])
            return ingest.IngestResult(row, dict(row))

        def upload(args, items, *unused):
            upload_started.set()
            self.assertTrue(release_upload.wait(3))
            return [ingest.IngestResult(item.row, item.record, status='deleted') for item in items]

        with patch.object(ingest, 'Rclone', return_value=Mock()), \
                patch.object(ingest, 'ingest_one', side_effect=prepare), \
                patch.object(ingest, 'upload_batch', side_effect=upload), \
                cf.ThreadPoolExecutor(max_workers=1) as runner:
            future = runner.submit(ingest.run, self.args(ready_items=3, upload_batch_items=1), rows)
            try:
                self.assertTrue(upload_started.wait(2))
                threading.Event().wait(0.15)
                with calls_lock:
                    self.assertLessEqual(len(calls), 3)
            finally:
                release_upload.set()
            self.assertEqual(future.result(timeout=3), 0)

    def test_stage_only_capture_leaves_complete_pair_without_drive_upload(self):
        row = dict(video_id='abcdefghijk', channel_dir='channel', tab='videos', url='https://www.youtube.com/watch?v=abcdefghijk')
        info = dict(id=row['video_id'], ext='webm', filesize=10, duration=20, upload_date='20260101', vcodec='none')
        budget = ingest.Budget(self.root, 100_000_000, 0, 0)
        drive = Mock()

        def stream(info, part, budget, *unused):
            with open(part, 'wb') as out:
                budget.write(out, b'0123456789')
            return ingest.hash_file(part)

        with patch.object(ingest, 'extract_audio', return_value=info), patch.object(ingest, 'stream_audio', side_effect=stream):
            result = ingest.ingest_one(self.args(), row, budget, Mock(), threading.Event(), drive, self.state, stage_only=True)
        self.assertEqual(result.status, 'ready')
        self.assertIn('/Videos/', result.record['path'])
        self.assertEqual(Path(result.record['path']).parent, Path(result.record['metadata']['path']).parent)
        self.assertTrue(self.files_exist(result))
        self.assertEqual(ingest.load_state(self.state)[row['video_id']]['status'], 'queued_upload')
        self.assertEqual(drive.mock_calls, [])

    def test_terminal_unavailable_never_means_rate_or_login_failure(self):
        for kind in ('forbidden', 'rate_limited', 'bot_check', 'login_required', 'drive_rate_limited'):
            self.assertFalse(ingest.terminal_unavailable({'status': 'unavailable', 'error_class': kind}))
        self.assertTrue(ingest.terminal_unavailable({'status': 'unavailable', 'error_class': 'unavailable'}))
        self.assertFalse(ingest.terminal_unavailable({'status': 'error', 'error_class': 'unavailable'}))
        self.assertFalse(ingest.terminal_unavailable({'status': 'unavailable', 'error_class': 'unavailable', 'sha256': 'captured-audio'}))


if __name__ == '__main__':
    unittest.main()
