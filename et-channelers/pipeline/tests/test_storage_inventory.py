import json
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pipeline import drive_ingest, native_batch, storage_inventory


class StorageInventoryTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.spool = self.root / 'spool'
        self.active = self.spool / 'running'
        self.active.mkdir(parents=True)

    def test_inactive_files_measured_once_and_disappearing_files_skipped(self):
        outside = self.root / 'index.json'
        kept = self.spool / 'ready.part'
        vanished = self.spool / 'cleaned.m4a'
        excluded = self.active / 'growing.part'
        for path, size in [(outside, 1), (kept, 7), (vanished, 11), (excluded, 17)]:
            path.write_bytes(bytes(size))
        observed = []
        check = storage_inventory._checked_stat

        def stat_after_cleanup(path):
            observed.append(Path(path))
            if Path(path) == vanished:
                vanished.unlink()
            return check(path)

        with patch.object(storage_inventory, '_checked_stat', side_effect=stat_after_cleanup):
            got = native_batch.capacity_snapshot(self.root, self.spool, [self.active])
        self.assertEqual(got, {'inactive_private_bytes': 8, 'inactive_spool_bytes': 7})
        self.assertEqual(observed.count(kept), 1)
        self.assertNotIn(excluded, observed)
        self.assertEqual(drive_ingest.tree_bytes(self.root), 25)

    def test_directory_read_error_does_not_grant_spare_bytes(self):
        with patch.object(storage_inventory.os, 'scandir', side_effect=PermissionError()):
            with self.assertRaises(PermissionError):
                native_batch.capacity_snapshot(self.root, self.spool, [])

    def test_separate_tool_tree_counts_fresh_entries_without_statting_each_file_again(self):
        unchanged = self.root / 'runtime.bin'
        unchanged.write_bytes(b'12345')
        (self.active / 'busy').write_bytes(b'large')
        with patch.object(storage_inventory, '_checked_stat', wraps=storage_inventory._checked_stat) as calls:
            self.assertEqual(storage_inventory.measure(self.root, spool=self.spool, excluded=[self.active],
                                                       enumeration_sizes=True), (5, 0))
            self.assertNotIn(unchanged, [Path(call.args[0]) for call in calls.call_args_list])
        unchanged.write_bytes(b'new-size')
        self.assertEqual(storage_inventory.measure(self.root, enumeration_sizes=True),
                         storage_inventory.measure(self.root))

    def test_symlink_and_windows_junction_are_rejected_before_descent(self):
        ordinary = os.stat(self.active)
        for mode, tag in [(stat.S_IFLNK, 0), (ordinary.st_mode, 0xA0000003)]:
            with self.subTest(mode=mode, tag=tag):
                info = type('Entry', (), {'st_mode': mode, 'st_reparse_tag': tag})()
                with patch.object(storage_inventory.os, 'stat', return_value=info):
                    with self.assertRaises(storage_inventory.LinkedEntry):
                        storage_inventory._checked_stat(self.active)

    def test_managed_roots_do_not_double_count_nested_checkouts_or_private_files(self):
        (self.active / 'audio').write_bytes(b'abc')
        tools = self.root / 'tools'
        checkout = tools / 'checkout'
        checkout.mkdir(parents=True)
        (tools / 'tool').write_bytes(b'1234')
        (checkout / 'code').write_bytes(b'56')
        for others in [(tools, checkout, self.active), (checkout, self.root, self.active), (tools, tools)]:
            with self.subTest(roots=others):
                self.assertEqual(storage_inventory.project_usage(self.spool, others), (3, 9))

    def test_archived_managed_root_is_charged_before_downloading_and_at_reconciliation(self):
        tools = self.root / 'tools'
        tools.mkdir()
        config = self.spool / 'sync' / 'managed_storage_roots.json'
        config.parent.mkdir()
        config.write_text(json.dumps({'schema_version': 1, 'managed_roots': [str(tools)]}), encoding='utf-8')
        old = tools / 'old.bin'
        old.write_bytes(bytes(50))
        cap = config.stat().st_size + 100
        roots = drive_ingest.managed_roots(self.spool, (tools,))
        budget = drive_ingest.Budget(self.spool, cap, 100, 0, reserve=5, cached=True, other_roots=roots)
        with self.assertRaises(drive_ingest.IngestError):
            budget.reserve_item('large', self.spool / 'large.part', 46)
        old.unlink()
        budget.usage(reconcile=True)
        budget.reserve_item('large', self.spool / 'large.part', 46)

    def test_other_active_reservations_protect_the_aggregate_cap_and_disk_floor(self):
        ledger = self.spool / 'sync' / 'analysis_resource_plan.json'
        ledger.parent.mkdir()
        ledger.write_text(json.dumps({'reservations': [{'state': 'active', 'max_bytes': 30},
                                                       {'state': 'released', 'max_bytes': 400}]}))
        existing = ledger.stat().st_size
        budget = drive_ingest.Budget(self.spool, existing + 100, 100, 100, reserve=5)
        disk = type('Disk', (), {'free': 180})
        with patch.object(drive_ingest.shutil, 'disk_usage', return_value=disk):
            with self.assertRaisesRegex(drive_ingest.IngestError, 'buffer is currently unavailable'):
                budget.reserve_item('over-cap', self.spool / 'a', 66)
            with self.assertRaisesRegex(drive_ingest.IngestError, 'free-disk floor'):
                budget.reserve_item('over-floor', self.spool / 'b', 46)
            budget.reserve_item('fits', self.spool / 'c', 45)


if __name__ == '__main__':
    unittest.main()
