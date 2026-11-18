"""A live cohort needs an owned command and consistent immutable scope proofs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import ingestion_status as status


class BulkStatusTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'jobs/native-http-v5-bulk-fixture'
        self.live = self.home / 'runtime'
        self.live.mkdir(parents=True)
        (self.root / 'sync').mkdir()
        self.namespace = 'stock_wpc_batch_v5_bulk_recovery2'
        self.ids = ['00000000001', '00000000002']
        self.codes = []
        fields = {'controller': 'native_bulk_controller.py', 'coordinator': 'native_batch.py',
            'worker': 'native_batch_worker.py', 'http_policy': 'native_http_policy.py', 'contract': 'bulk_contract.py'}
        self.code_hashes = {}
        for key, name in fields.items():
            path = self.root / name
            path.write_text('# bound private code\n', encoding='utf-8')
            pin = self.pin(path); self.codes.append(pin); self.code_hashes[key + '_sha256'] = pin['sha256']
        manifest = self.put('manifest.json', {'allowed_video_ids': self.ids})
        mapping = self.put('map.json', {'frames': [{'frame_index': 0, 'plan_sha256': '9' * 64, 'video_ids': self.ids}]})
        self.grant_path = self.home / 'grant.json'
        settings = self.put('settings.json', {'root_admission_path': str(self.grant_path), 'owner': 'root',
            'lease_id': 'bulk-test', 'cohort_manifest': manifest, 'frame_map': mapping})
        self.grant = dict(authorized=True, finite_cohort_scope_authorized=True, source_scope_authorized=True,
            owner='root', profile='stock_headful_wpc_native_batch_v5_bulk_recovery2', ASR=False, GPU=False,
            allowed_video_ids=self.ids, expires_at_epoch=2000, controller_settings_sha256=settings['sha256'],
            cohort_manifest_sha256=manifest['sha256'], frame_map_sha256=mapping['sha256'],
            http_policy_seed_sha256='1' * 64, **self.code_hashes)
        self.write(self.grant_path, self.grant)
        self.lease = dict(self.grant, state='active', root_admission_sha256=self.pin(self.grant_path)['sha256'], lease_id='bulk-test')
        self.write(self.root / ('sync/' + self.namespace + '_lease.json'), self.lease)
        self.put('root-review-packet.json', {'controller_settings': settings, 'private_code': self.codes})
        self.invoked = dict(controller_identity={'pid': 1234, 'process_creation_filetime': '5678'},
            started_at_epoch=900, root_grant_sha256=self.lease['root_admission_sha256'],
            **{key: self.grant[key] for key in ('controller_settings_sha256', 'cohort_manifest_sha256', 'frame_map_sha256')})
        self.write(self.live / 'source-invocation.json', self.invoked)
        self.state = dict(self.invoked, status='active', frames=[], current_frame={'frame_index': 0})
        self.save_state()
        self.write(self.root / ('sync/' + self.namespace + '_http_state.json'),
            {'schema_version': 5, 'seed_sha256': '1' * 64, 'state': {'circuit_break': None}})

    def write(self, path, value):
        path.write_text(json.dumps(value), encoding='utf-8')

    def put(self, name, value):
        path = self.home / name; self.write(path, value); return self.pin(path)

    def pin(self, path):
        data = path.read_bytes()
        return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def save_state(self):
        self.write(self.live / 'cohort-state.json', self.state)

    def lane(self, alive=True):
        with patch.object(status, 'owned_native_batch_command', return_value=alive):
            return status.native_bulk_lane(self.root, 1000)

    def test_metadata_alone_cannot_claim_running(self):
        self.assertEqual(self.lane()['source_count'], 2)
        self.assertTrue(self.lane()['process_confirmed'])
        self.assertEqual(self.lane(False), {})
        Path(self.codes[0]['path']).write_text('# changed\n', encoding='utf-8')
        self.assertEqual(self.lane(), {})

    def test_partial_or_inconsistent_frame_cannot_inflate_completed_decisions(self):
        self.state['frames'] = [{'frame_index': 0, 'plan_sha256': '9' * 64, 'status': 'terminal_closed',
            'summary': {'verified': 1, 'held': 1, 'pending': 0, 'skipped': 0}}]
        self.save_state()
        self.assertEqual(self.lane()['completed_decisions'], 2)
        self.state['frames'][0]['summary']['pending'] = 1
        self.save_state()
        self.assertEqual(self.lane(), {})

    def test_actual_cohort_hold_overrides_live_process(self):
        self.state['status'] = 'held_reconciliation_required'
        self.save_state()
        self.assertEqual(self.lane()['state'], 'paused')
        self.assertFalse(self.lane()['process_confirmed'])

    def test_missing_worker_diagnostics_is_an_administrative_hold(self):
        self.state.update(status='held_reconciliation_required',
            failed_frame={'error_class': 'bulk_child_diagnostics_missing'})
        self.save_state()
        self.assertEqual(self.lane()['reason'], 'worker_diagnostics_missing')

    def test_actual_source_circuit_takes_precedence_over_diagnostic_hold(self):
        self.state.update(status='held_reconciliation_required',
            failed_frame={'error_class': 'bulk_child_diagnostics_missing'})
        self.save_state()
        self.write(self.root / ('sync/' + self.namespace + '_http_state.json'),
            {'schema_version': 5, 'seed_sha256': '1' * 64,
             'state': {'circuit_break': {'reason': 'provider_hold'}}})
        self.assertEqual(self.lane()['reason'], 'source_control_hold')
