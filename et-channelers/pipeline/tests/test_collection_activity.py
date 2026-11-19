"""Creator activity partitions never promote progress to a saved receipt."""
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import collection_coverage as coverage


class ActivityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); (self.root / 'sync').mkdir()
        self.ids = [letter * 11 for letter in 'abcdef']
        self.rows = [dict(video_id=ident, channel_dir='example', source_channel_name='Example') for ident in self.ids]
        self.namespace = 'stock_wpc_batch_v5_bulk_recovery3'
        self.write(self.root / 'sync' / (self.namespace + '_lease.json'),
                   {'state': 'active', 'allowed_video_ids': self.ids[:5]})
        self.lane = dict(namespace=self.namespace, state='running', process_confirmed=True, source_count=5)
        for ident, phase, pid in [(self.ids[1], 'native_transfer', 11), (self.ids[2], 'bootstrap', 12)]:
            folder = self.folder(ident)
            self.write(folder / 'child-owner.json', {'owned_child': {'pid': pid, 'process_creation_filetime': '123'}})
            self.write(folder / 'progress.json', {'phase': phase, 'audio_bytes_written': 200})
        self.write(self.folder(self.ids[3]) / 'result.json', {'status': 'local_complete'})
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value), encoding='utf-8')

    def folder(self, ident, frame='frame'):
        path = self.root / self.namespace / 'jobs' / frame / ident
        self.write(path / 'attempt.json', {})
        return path

    def activity(self, saved=None, alive=True):
        with patch.object(coverage.status, 'native_bulk_lane', return_value=self.lane), \
             patch.object(coverage.status, 'owned_process_alive', return_value=alive):
            return coverage.channel_activity(self.root, self.rows, set(saved or self.ids[:1]), dt.datetime.now(dt.timezone.utc))

    def test_saved_transfer_processing_upload_queue_and_other_are_disjoint(self):
        data = self.activity()
        self.assertEqual(data['summary'], {key: 1 for key in coverage.ACTIVITY_FIELDS})
        self.assertEqual(sum(data['summary'].values()), len(self.rows))
        self.assertNotIn(str(self.root), json.dumps(data))
        self.assertNotIn('process_creation_filetime', json.dumps(data))

    def test_dead_or_reused_worker_cannot_claim_a_transfer(self):
        counts = self.activity(alive=False)['summary']
        self.assertEqual((counts['downloading'], counts['processing']), (0, 0))
        self.assertEqual(counts['other_pending'], 3)

    def test_saved_receipt_takes_precedence_over_old_worker_state(self):
        counts = self.activity(saved=self.ids[:2])['summary']
        self.assertEqual(counts['saved'], 2)
        self.assertEqual(counts['downloading'], 0)
        self.assertEqual(sum(counts.values()), len(self.rows))

    def test_paused_or_duplicate_attempts_cannot_claim_current_work(self):
        self.folder(self.ids[1], 'duplicate')
        self.assertEqual(self.activity()['summary']['downloading'], 0)
        self.lane.update(state='paused', process_confirmed=False)
        data = self.activity()
        self.assertEqual(data['cohort_items'], 0)
        self.assertEqual(data['summary']['queued'], 0)
        self.assertEqual(data['summary']['other_pending'], 5)

    def test_qualified_batch_stages_partition_targets_but_saved_receipt_wins(self):
        qualified = {'public': {'state': 'running', 'source_count': 5}, 'video_stages': {
            self.ids[0]: 'downloading', self.ids[1]: 'downloading', self.ids[2]: 'processing',
            self.ids[3]: 'awaiting_upload', self.ids[4]: 'queued', self.ids[5]: 'unresolved'}}
        with patch.object(coverage.status, 'native_bulk_lane', return_value={}), \
             patch.object(coverage.status, 'qualified_batch_state', return_value=qualified):
            data = coverage.channel_activity(self.root, self.rows, {self.ids[0]}, dt.datetime.now(dt.timezone.utc))
        self.assertEqual(data['summary'], {key: 1 for key in coverage.ACTIVITY_FIELDS})
        self.assertEqual(data['state'], 'running'); self.assertEqual(data['cohort_items'], 5)
