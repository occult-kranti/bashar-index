"""Live executor reporting must not promote stale leases or expose identities."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import ingestion_status as status


class NativeSeriesStatusTests(unittest.TestCase):
    def test_actual_native_refusal_hold_replaces_legacy_state_without_claiming_a_worker(self):
        self.put(self.root / 'sync/STOP_STOCK_WPC_BATCH_V4', {})
        self.put(self.root / 'sync/stock_wpc_batch_v4_source_cooldown.json', {'error_class': 'source_403', 'retry_not_before_epoch': 1200})
        self.put(self.root / 'sync/stock_wpc_batch_v4_http_state.json', {'state': {'circuit_break': {
            'reason': 'three_distinct_403_in_600s', 'at_epoch': 999, 'event_ids': ['PRIVATE']}}})
        public = status.snapshot(self.root, now=1000)
        self.assertEqual(public['operation']['state'], 'paused')
        self.assertEqual(public['operation']['cooldown_provider'], 'youtube')
        self.assertEqual(public['operation']['retry_after'], status.stamp(1200))
        self.assertEqual(public['native_lane']['reason'], 'repeated_bound_403')
        self.assertFalse(public['native_lane']['process_confirmed'])
        self.assertFalse(public['native_lane']['automatic_resume'])
        self.assertNotIn('PRIVATE', json.dumps(public))

    def test_held_campaign_keeps_only_bound_completed_frame_totals(self):
        self.put(self.root / 'sync/STOP_STOCK_WPC_BATCH_V4', {})
        live = self.root / 'jobs/native-campaign-test/cohort1/live'
        live.mkdir(parents=True)
        self.put(live / 'series-state.json', {'proposal_sha256': 'a' * 64, 'authorization_sha256': 'b' * 64,
            'frames': {'0': {'phase': 'drained', 'outcomes': {'PRIVATE-A': {}, 'PRIVATE-B': {}}},
                       '1': {'phase': 'dispatch_intent', 'outcomes': {'PRIVATE-C': {}}}}})
        self.put(live / 'source-invocation.json', {'series_proposal_sha256': 'a' * 64,
            'root_authorization_sha256': 'b' * 64, 'source_count': 600, 'cohort_index': 1, 'planned_frames': 30})
        result = status.native_source_hold(self.root, 1000)
        self.assertEqual(result['completed_decisions'], 2)
        self.assertEqual(result['source_count'], 600)
        self.assertNotIn('PRIVATE', json.dumps(result))
        self.put(live / 'source-invocation.json', {'series_proposal_sha256': 'wrong'})
        self.assertNotIn('completed_decisions', status.native_source_hold(self.root, 1000))

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

    def test_separate_frame_must_be_an_owned_child_of_the_series(self):
        child = dict(pid=5432, process_creation_filetime='123456999')
        self.put(self.root / 'sync/stock_wpc_batch_v4_lease.json', dict(self.lease, controller_identity=child))
        with patch.object(status, 'owned_process_alive', return_value=True), \
                patch.object(status, 'owned_process_child_of', return_value=True) as relation:
            self.assertEqual(status.snapshot(self.root, now=1000)['operation']['state'], 'running')
            relation.assert_called_with(child, self.identity)
        with patch.object(status, 'owned_process_alive', return_value=True), \
                patch.object(status, 'owned_process_child_of', return_value=False):
            self.assertEqual(status.snapshot(self.root, now=1000)['operation']['state'], 'paused')

    def test_campaign_uses_the_same_lease_and_process_proof_requirements(self):
        previous = self.live
        self.live = self.root / 'jobs/native-campaign-test/live'
        self.live.mkdir(parents=True)
        for name in ('series-state.json', 'source-invocation.json', 'consumer-state.json'):
            self.put(self.live / name, json.loads((previous / name).read_bytes()))
        self.put(previous / 'series-state.json', {'status': 'finished_with_holds'})
        with patch.object(status, 'owned_process_alive', return_value=True):
            self.assertEqual(status.snapshot(self.root, now=1000)['operation']['state'], 'running')
        with patch.object(status, 'owned_process_alive', return_value=False):
            self.assertEqual(status.snapshot(self.root, now=1000)['operation']['state'], 'paused')

    def test_nested_download_only_cohort_reports_only_drained_decisions_and_no_asr(self):
        live = self.root / 'jobs/native-campaign-download-test/cohort1/live'; live.mkdir(parents=True)
        self.put(self.live / 'series-state.json', {'status': 'finished_with_holds'})
        self.put(live / 'series-state.json', dict(status='running', profile='native-campaign-download-only-v1',
                 proposal_sha256='a' * 64, authorization_sha256='b' * 64,
                 frames={'0': {'phase': 'drained', 'outcomes': {'PRIVATE-ID': {'status': 'canonical_verified'}}},
                         '1': {'phase': 'dispatch_intent'}}))
        self.put(live / 'source-invocation.json', dict(self.identity, series_proposal_sha256='a' * 64,
                 root_authorization_sha256='b' * 64, source_count=600, cohort_index=1, planned_frames=30))
        with patch.object(status, 'owned_process_alive', return_value=True):
            result = status.snapshot(self.root, now=1000)
        self.assertEqual(result['native_lane']['kind'], 'native_v4_campaign')
        self.assertEqual(result['native_lane']['source_count'], 600)
        self.assertEqual(result['native_lane']['completed_decisions'], 1)
        self.assertFalse(result['native_lane']['asr_handoff_enabled'])
        self.assertFalse(result['operation']['full_archive_requested'])
        self.assertNotIn('PRIVATE', json.dumps(result))

    def terminal_fixture(self):
        self.put(self.root / 'sync/stock_wpc_batch_v4_lease.json', dict(self.lease,
                 state='released', owned_native_processes_gone=True, lease_id='PRIVATE-LEASE'))
        self.put(self.live / 'series-state.json', dict(status='finished_with_holds',
                 proposal_sha256='a' * 64, authorization_sha256='b' * 64))
        self.put(self.live / 'source-process-exit.json', {'exit_code': 0})
        self.put(self.live / 'native-allocation-released.json', {'lease_id': 'PRIVATE-LEASE'})
        self.put(self.root / 'sync/stock_wpc_batch_v4_http_state.json', dict(schema_version=1,
                 state={'policy': 'native-http-refusal-v4', 'circuit_break': None}))

    def test_terminal_native_lane_ready_is_separate_from_legacy_hold(self):
        self.terminal_fixture()
        self.put(self.root / 'sync/native_batch_source_cooldown.json', dict(schema_version=1,
                 endpoint='youtube_native_audio', source_error_class='forbidden', retry_not_before_epoch=1100))
        with patch.object(status, 'owned_process_alive', return_value=False):
            result = status.snapshot(self.root, now=1000)
        self.assertEqual(result['operation']['state'], 'ready')
        self.assertEqual(result['legacy_operation']['state'], 'paused')
        self.assertFalse(result['native_lane']['process_confirmed'])
        self.assertEqual(result['native_lane']['proof'], 'released_terminal_run')
        self.assertTrue((self.root / 'sync/STOP_DRIVE_INGEST').exists())
        for private in ('PRIVATE', '4321', '123456789', 'a' * 64):
            self.assertNotIn(private, json.dumps(result))

    def test_terminal_lane_requires_release_dead_process_and_current_policy_without_hold(self):
        self.terminal_fixture()
        with patch.object(status, 'owned_process_alive', return_value=True):
            self.assertFalse(status.completed_native_lane(self.root, 1000))
        with patch.object(status, 'owned_process_alive', return_value=False):
            for path, value in [(self.live / 'source-process-exit.json', {'exit_code': 1}),
                                (self.live / 'native-allocation-released.json', {'lease_id': 'WRONG'}),
                                (self.root / 'sync/stock_wpc_batch_v4_http_state.json', dict(schema_version=1,
                                 state={'policy': 'native-http-refusal-v4', 'circuit_break': {'code': 'hold'}}))]:
                original = path.read_text(encoding='utf-8'); self.put(path, value)
                self.assertFalse(status.completed_native_lane(self.root, 1000))
                path.write_text(original, encoding='utf-8')

    def test_direct_frame_requires_all_pins_exact_root_command_and_live_identity(self):
        live = self.root / 'jobs/native-recovery-test/runtime-frame1-v1'; live.mkdir(parents=True)
        def pin(name, value):
            path = live / name; self.put(path, value); data = path.read_bytes()
            return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        code = hashlib.sha256(Path(status.__file__).with_name('native_batch.py').read_bytes()).hexdigest()
        worker = hashlib.sha256(Path(status.__file__).with_name('native_batch_worker.py').read_bytes()).hexdigest()
        ids = ['PRIVATE-ID']
        plan = pin('plan.json', {'items': ids})
        settings = pin('settings.json', {'private_root': str(self.root), 'lease_id': 'PRIVATE-LEASE', 'plan_path': plan['path']})
        grant = pin('grant.json', dict(authorized=True, state='admitted', lease_id='PRIVATE-LEASE',
                    allowed_video_ids=ids, plan_sha256=plan['sha256'], settings_sha256=settings['sha256'],
                    coordinator_sha256=code, worker_sha256=worker))
        lease = dict(self.lease, lease_id='PRIVATE-LEASE', root_grant_sha256=grant['sha256'],
                     settings_sha256=settings['sha256'], plan_sha256=plan['sha256'],
                     coordinator_sha256=code, worker_sha256=worker, allowed_video_ids=ids)
        self.put(self.root / 'sync/stock_wpc_batch_v4_lease.json', lease)
        self.put(self.root / 'sync/stock_wpc_batch_v4_http_state.json', dict(schema_version=1,
                 state={'policy': 'native-http-refusal-v4', 'circuit_break': None}))
        self.put(live / 'activation.json', dict(status='active', settings=settings, plan=plan,
                 root_grant=grant, lease_id='PRIVATE-LEASE', allowed_video_ids=ids))
        invoked = dict(self.identity, status='running', lease_id='PRIVATE-LEASE',
                       root_grant_sha256=grant['sha256'], settings_sha256=settings['sha256'],
                       plan_sha256=plan['sha256'], native_batch_sha256=code, worker_sha256=worker,
                       allowed_video_ids=ids, source_count=1, started_at_epoch=999)
        self.put(live / 'invocation.json', invoked)
        with patch.object(status, 'owned_native_batch_command', return_value=True):
            result = status.direct_native_batch(self.root, 1000)
            self.assertEqual(result['state'], 'running')
            self.assertEqual(result['frame_items'], 1)
            self.assertFalse(result['asr_handoff_enabled'])
            for private in ('PRIVATE', str(self.root), '4321', code, worker):
                self.assertNotIn(private, json.dumps(result))
            for changed in [dict(invoked, native_batch_sha256='c' * 64),
                            dict(invoked, allowed_video_ids=['OTHER-ID']), dict(invoked, settings_sha256='c' * 64)]:
                self.put(live / 'invocation.json', changed)
                self.assertFalse(status.direct_native_batch(self.root, 1000))
            self.put(live / 'invocation.json', invoked)
            path = Path(settings['path']); path.write_text('{}', encoding='utf-8')
            self.assertFalse(status.direct_native_batch(self.root, 1000))
        with patch.object(status, 'owned_native_batch_command', return_value=False):
            self.assertFalse(status.direct_native_batch(self.root, 1000))
        # Restore the settings pin, then prove terminal exit=3 with a held item
        # can establish readiness only after both owned resources are released.
        self.put(Path(settings['path']), {'private_root': str(self.root), 'lease_id': 'PRIVATE-LEASE', 'plan_path': plan['path']})
        self.put(self.root / 'sync/stock_wpc_batch_v4_lease.json', dict(lease, state='released'))
        self.put(live / 'source-process-exit.json', dict(self.identity, exit_code=3))
        terminal = dict(status='terminal', lease_id='PRIVATE-LEASE', root_grant_sha256=grant['sha256'],
                        settings_sha256=settings['sha256'], plan_sha256=plan['sha256'],
                        parent_process_exited=True, child_audits_complete=True, owned_jobs_closed=True,
                        matching_reservation_released=True, matching_lease_released=True)
        self.put(live / 'terminal.json', terminal)
        with patch.object(status, 'owned_process_alive', return_value=False):
            self.assertEqual(status.direct_native_batch(self.root, 1000)['state'], 'ready')
            for change in ({'matching_lease_released': False}, {'root_grant_sha256': 'c' * 64}):
                self.put(live / 'terminal.json', dict(terminal, **change))
                self.assertFalse(status.direct_native_batch(self.root, 1000))


if __name__ == '__main__':
    unittest.main()
