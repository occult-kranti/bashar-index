"""Creator activity partitions never promote progress to a saved receipt."""
import datetime as dt
import hashlib
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
        self.assertEqual(data['summary'], dict.fromkeys(coverage.ACTIVITY_FIELDS, 1) | {'waiting_for_source': 0})
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
        self.assertEqual(data['summary'], dict.fromkeys(coverage.ACTIVITY_FIELDS, 1) | {'waiting_for_source': 0})
        self.assertEqual(data['state'], 'running'); self.assertEqual(data['cohort_items'], 5)

    def test_rolling_native_handoff_uses_live_owner_and_publication_receipts(self):
        now = dt.datetime.now(dt.timezone.utc)
        frame = self.root/'provisioning/native-rolling-handoff-8'
        runtime = frame/'runtime'
        grant_path = frame/'root-grant.ACTIVE.json'
        ids = self.ids[:5]
        profile = 'native_rolling_handoff_8'
        def digest(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        self.write(grant_path, {'enabled': True, 'source_authorized': True, 'profile': profile,
                                'allowed_video_ids': ids})
        grant = digest(grant_path)
        identity = {'pid': 111, 'process_creation_filetime': '123'}
        self.write(self.root/'sync'/f'{profile}_lease.json', {'state': 'active', 'profile': profile,
                   'source_authorized': True, 'expires_at_epoch': now.timestamp()+90, 'source_workers': 6,
                   'allowed_video_ids': ids, 'root_grant_sha256': grant})
        invoked = runtime/'invocation.json'
        self.write(invoked, {'identity': identity, 'root_grant_sha256': grant, 'exact_handle_creation_verified': True,
                             'exact_command_verified': True, 'owned_job_attached': True})
        self.write(runtime/'GO', {'identity': identity, 'root_grant_sha256': grant, 'invocation_sha256': digest(invoked)})
        for ident in ids[:4]:
            folder = runtime/'observations'/ident
            self.write(folder/'attempt.json', {'video_id': ident, 'root_grant_sha256': grant})
            if ident in ids[:2]:
                self.write(folder/'wire-1.json', {'attempt_sha256': digest(folder/'attempt.json'), 'method': 'GET'})
        self.write(runtime/'observations'/ids[3]/'range-transfer.json', {'final_response_equal': True})
        with patch.object(coverage.status, 'owned_process_alive', return_value=True):
            data = coverage.channel_activity(self.root, self.rows, {ids[0]}, now)
            self.assertEqual(data['state'], 'running')
            self.assertEqual(data['summary'], dict.fromkeys(coverage.ACTIVITY_FIELDS, 1) | {'waiting_for_source': 0})
            self.assertNotIn(str(self.root), json.dumps(data))
            self.write(runtime/'observations'/ids[1]/'range-1.json', {'response_status': 403})
            self.assertEqual(coverage.status.rolling_native_state(self.root, now.timestamp())['video_stages'][ids[1]], 'waiting_for_source')
            self.write(runtime/'owner-terminal.json', {'status': 'terminal'})
            self.assertEqual(coverage.status.rolling_native_state(self.root, now.timestamp()), {})
        (runtime/'owner-terminal.json').unlink()
        with patch.object(coverage.status, 'owned_process_alive', return_value=False):
            self.assertEqual(coverage.status.rolling_native_state(self.root, now.timestamp()), {})
