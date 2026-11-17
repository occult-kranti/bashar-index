"""Live executor reporting must not promote stale leases or expose identities."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import ingestion_status as status


class NativeSeriesStatusTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.live = self.root / 'jobs/native-series-test/live'
        self.live.mkdir(parents=True)
        (self.root / 'sync').mkdir()
        self.identity = {'pid': 4321, 'process_creation_filetime': '123456789'}
        self.lease = dict(state='active', authorized=True, source_scope_authorized=True,
                          profile='stock_headful_wpc_native_batch_v4', expires_at_epoch=1100,
                          max_workers=2, series_proposal_sha256='a' * 64,
                          root_authorization_sha256='b' * 64, controller_identity=self.identity)
        self.put(self.root / 'sync/stock_wpc_batch_v4_lease.json', self.lease)
        self.put(self.live / 'series-state.json', dict(status='running', proposal_sha256='a' * 64,
                                                     authorization_sha256='b' * 64))
        self.put(self.live / 'source-invocation.json', dict(self.identity,
                 series_proposal_sha256='a' * 64, root_authorization_sha256='b' * 64))
        self.put(self.live / 'consumer-state.json', dict(self.identity, heartbeat_epoch=999,
                 phase='gpu_running', status='waiting_or_processing', gpu_lease_id='private-gpu',
                 series_proposal_sha256='a' * 64))
        self.put(self.root / 'sync/gpu_lease.json', dict(state='active', lease_id='private-gpu',
                 expires_at=status.stamp(1100), series_proposal_sha256='a' * 64))
        (self.root / 'sync/STOP_DRIVE_INGEST').touch()

    def put(self, path, value):
        path.write_text(json.dumps(value), encoding='utf-8')

    def test_separate_live_executor_is_running_while_legacy_collector_stays_parked(self):
        with patch.object(status, 'owned_process_alive', return_value=True):
            result = status.snapshot(self.root, now=1000)
        self.assertEqual(result['operation']['state'], 'running')
        self.assertEqual(result['operation']['workers'], 2)
        self.assertEqual(result['operation']['asr_last_reported_state'], 'running')
        self.assertEqual(result['operation']['caption_state'], 'paused')
        serialized = json.dumps(result)
        for private in ('4321', '123456789', 'native-series-test', 'a' * 64, 'b' * 64):
            self.assertNotIn(private, serialized)
        self.assertTrue((self.root / 'sync/STOP_DRIVE_INGEST').exists())

    def test_dead_or_reused_pid_and_expired_or_mismatched_lease_never_claim_running(self):
        with patch.object(status, 'owned_process_alive', return_value=False):
            self.assertEqual(status.snapshot(self.root, now=1000)['operation']['state'], 'paused')
        with patch.object(status, 'owned_process_alive', return_value=True):
            for change in ({'expires_at_epoch': 999}, {'root_authorization_sha256': 'c' * 64},
                           {'controller_identity': dict(self.identity, process_creation_filetime='999')}):
                self.put(self.root / 'sync/stock_wpc_batch_v4_lease.json', dict(self.lease, **change))
                self.assertEqual(status.snapshot(self.root, now=1000)['operation']['state'], 'paused')

    def test_local_hold_or_global_source_stop_prevents_running_claim(self):
        with patch.object(status, 'owned_process_alive', return_value=True):
            for path in (self.live / 'local-publication-hold.json', self.live / 'drive-hold.json',
                         self.live / 'STOP_SERIES', self.root / 'sync/STOP_STOCK_WPC_BATCH_V4'):
                path.write_text('{}', encoding='utf-8')
                self.assertEqual(status.snapshot(self.root, now=1000)['operation']['state'], 'paused')
                path.unlink()
            self.put(self.root / 'sync/drive_ingest_cooldown.json', {'until_epoch': 1100})
            self.assertEqual(status.snapshot(self.root, now=1000)['operation']['state'], 'paused')
            self.put(self.root / 'sync/drive_ingest_cooldown.json', {})
            self.assertEqual(status.snapshot(self.root, now=1000)['operation']['state'], 'paused')

    def test_stale_consumer_does_not_claim_current_gpu_inference(self):
        self.put(self.live / 'consumer-state.json', dict(self.identity, heartbeat_epoch=900,
                 phase='gpu_running', series_proposal_sha256='a' * 64))
        with patch.object(status, 'owned_process_alive', return_value=True):
            result = status.snapshot(self.root, now=1000)
        self.assertEqual(result['operation']['state'], 'running')
        self.assertEqual(result['operation']['asr_last_reported_state'], 'unconfirmed')

    def test_released_gpu_or_terminal_consumer_cannot_claim_inference(self):
        with patch.object(status, 'owned_process_alive', return_value=True):
            self.put(self.root / 'sync/gpu_lease.json', dict(state='released', lease_id='private-gpu',
                     expires_at=status.stamp(1100), series_proposal_sha256='a' * 64))
            self.assertFalse(status.active_native_series(self.root, 1000)['asr_running'])
            self.put(self.root / 'sync/gpu_lease.json', dict(state='active', lease_id='private-gpu',
                     expires_at=status.stamp(1100), series_proposal_sha256='a' * 64))
            self.put(self.live / 'consumer-state.json', dict(self.identity, heartbeat_epoch=999,
                     status='complete', phase='gpu_running', gpu_lease_id='private-gpu',
                     series_proposal_sha256='a' * 64))
            self.assertFalse(status.active_native_series(self.root, 1000)['asr_running'])


if __name__ == '__main__':
    unittest.main()
