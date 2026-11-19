import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import archive_regular_selection as archive
from drive_ingest import IngestError


class Drive:
    def __init__(self):
        self.calls = []
        self.objects = {}
        self.corrupt = False

    def copy_batch(self, root, remote, manifest, transfers):
        self.calls.append(('copy', transfers))
        for name in manifest.read_text(encoding='utf-8').splitlines():
            data = (root/name).read_bytes()
            self.objects[name] = {'ID': name, 'Size': len(data), 'Hashes': {'md5': hashlib.md5(data).hexdigest()}}

    def stat_batch(self, remote, paths, manifest):
        self.calls.append(('stat', len(paths)))
        return {name: {**self.objects[name], 'Hashes': {'md5': '0'*32}} if self.corrupt else self.objects[name]
                for name in paths}


class ArchiveRegularSelectionTests(unittest.TestCase):
    def setUp(self):
        home = tempfile.TemporaryDirectory(); self.addCleanup(home.cleanup)
        self.root = Path(home.name); self.sweep = self.root/'sweep'; self.selected = self.root/'list'
        self.sweep.mkdir(); self.selected.mkdir()
        fresh = self.sweep/'index.json'; fresh.write_bytes(b'{}'); (self.sweep/'sweep-status.json').write_bytes(b'{}')
        union = {'selection_kind': 'additive_latest20plus_videos_v1', 'row_count': 2,
                 'sources': [{'kind':'fresh_regular', 'artifact': {'path':str(fresh), 'sha256': hashlib.sha256(b'{}').hexdigest()}}],
                 'channels': [{'channel_dir':'example'}]}
        self.raw = json.dumps(union).encode(); (self.selected/'selection.json').write_bytes(self.raw)
        for f in ('recording-index.json', 'summary.json', 'verified-counts.json', 'priority.csv'):
            (self.selected/f).write_bytes(b'fixture')
        self.coverage = self.root/'coverage.json'
        self.coverage.write_text(json.dumps({'selection_basis':'latest20plus_public_regular',
            'selection_sha256': hashlib.sha256(self.raw).hexdigest(), 'priority_scope_sha256':'a'*64,
            'generated_at':'2026-11-19T12:00:00Z', 'summary':{'latest20_target':1}, 'channels':[{k:1 for k in
                ('channel','channel_dir','target','audio_total','remaining_audio','with_saved_text','youtube_audio',
                 'publisher_only_audio','qualified_youtube_only_audio','selection_scope')}]}), encoding='utf-8')
        self.drive = Drive()
        self.enterContext(patch.object(archive, 'storage_usage', return_value=(0,0)))
        self.enterContext(patch.object(archive, 'managed_roots', return_value=[]))
        self.enterContext(patch.object(archive.shutil, 'disk_usage', return_value=type('Disk', (), {'free':30_000_000_000})()))

    def publish(self):
        return archive.publish(self.root, self.sweep, self.selected, self.coverage, 'test:04 Audio', self.drive)

    def test_batched_verification_and_reentry_without_remote_requests(self):
        result = self.publish()
        self.assertEqual((result['priority_recordings'], result['union_recordings']), (1,2))
        self.assertEqual(self.drive.calls, [('copy',1),('stat',3)])
        self.assertFalse(list((self.root/'jobs').rglob('*.zip')))
        self.assertEqual(self.publish(), result)
        self.assertEqual(len(self.drive.calls), 2)
        self.assertTrue((self.selected/'selection.json').exists())

    def test_checksum_failure_preserves_package_for_retry(self):
        self.drive.corrupt = True
        with self.assertRaises(IngestError):
            self.publish()
        self.assertEqual(len(list((self.root/'jobs').rglob('*.zip'))), 1)
        self.assertFalse(list((self.root/'jobs').rglob('verified-drive-files.json')))
        self.drive.corrupt = False
        self.assertEqual(len(self.publish()['files']), 3)

    def test_retained_catalog_and_date_overlay_are_preserved_by_hash(self):
        union = json.loads(self.raw)
        retained = self.root/'supplement.json'
        dates = self.root/'dates.jsonl'
        retained.write_bytes(b'{"rows":[]}')
        dates.write_bytes(b'{}\n')
        def descriptor(path):
            raw = path.read_bytes()
            return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        union['sources'].append({'kind':'retained_addition', 'artifact':descriptor(retained)})
        union['date_overlay'] = descriptor(dates)
        args = (self.root, self.sweep, self.selected, self.coverage, union, [dates])
        entries = archive.archive_entries(*args)
        self.assertIn((retained, 'index/sources/01-retained_addition/supplement.json'), entries)
        self.assertEqual([name for path, name in entries if path == dates], ['index/sources/02-date_overlay/dates.jsonl'])
        retained.write_bytes(b'{"rows":{}}')
        with self.assertRaisesRegex(ValueError, 'differs from the selection'):
            archive.archive_entries(*args)

    def test_receipt_cannot_satisfy_a_different_drive_destination(self):
        first = self.publish()
        second = archive.publish(self.root, self.sweep, self.selected, self.coverage, 'elsewhere:Archive', self.drive)
        self.assertTrue(all(p['remote'].startswith('elsewhere:Archive/') for p in second['files'].values()))
        self.assertEqual(self.publish(), first)
        self.assertEqual(len(self.drive.calls), 4)

    def test_duplicate_object_ids_keep_all_files_for_recovery(self):
        actual = self.drive.stat_batch
        def same_id(*args):
            return {name: {**proof, 'ID': 'one-object'} for name, proof in actual(*args).items()}
        self.drive.stat_batch = same_id
        with self.assertRaisesRegex(ValueError, 'distinct Drive IDs'):
            self.publish()
        self.assertEqual(len(list((self.root/'jobs').rglob('*.zip'))), 1)
        self.assertFalse(list((self.root/'jobs').rglob('verified-drive-files.json')))

    def test_changed_local_copy_survives_upload_and_restart(self):
        original = self.drive.copy_batch
        def copy_then_change(root, dest, manifest, transfers):
            original(root, dest, manifest, transfers)
            (root/archive.NAMES[1]).write_bytes(b'concurrent replacement')
        self.drive.copy_batch = copy_then_change
        self.publish()
        leftover, = list((self.root/'jobs').rglob(archive.NAMES[1]))
        self.publish()
        self.assertEqual(leftover.read_bytes(), b'concurrent replacement')
        self.assertEqual(len(self.drive.calls), 2)
