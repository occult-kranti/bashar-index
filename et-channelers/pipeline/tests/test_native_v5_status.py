"""Status must follow actual private grants and processes, never an old lane."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import ingestion_status as status


class V5StatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.live = self.root / 'jobs/native-http-v5-test/runtime-v1'
        self.live.mkdir(parents=True)
        (self.root / 'sync').mkdir()
        self.now = 1000
        self.ids = [f'{n:011d}' for n in range(20)]
        self.profile = 'stock_headful_wpc_native_batch_v5'
        self.pins = {}
        for key in ('code', 'worker', 'policy'):
            path = self.root / (key + '.py')
            path.write_text('# pinned source\n', encoding='utf-8')
            self.pins[key] = self.pin(path)
        self.seed_sha = '1' * 64
        self.review_sha = '2' * 64
        grant = dict(authorized=True, source_scope_authorized=True,
            synthetic_v4_breaker_override_authorized=True, asr_handoff=False,
            profile=self.profile, workers=2, expires_at_epoch=2000,
            allowed_video_ids=self.ids, http_policy_sha256=self.pins['policy']['sha256'],
            http_policy_seed_sha256=self.seed_sha, root_policy_review_sha256=self.review_sha)
        settings = dict(lease_id='owned-v5', profile=self.profile, workers=2, asr_handoff=None)
        for key, value in (('settings', settings), ('plan', {'items': [{'video_id': i} for i in self.ids]})):
            path = self.root / (key + '.json')
            self.save(path, value)
            self.pins[key] = self.pin(path)
        grant.update(settings_sha256=self.pins['settings']['sha256'], plan_sha256=self.pins['plan']['sha256'])
        path = self.root / 'grant.json'
        self.save(path, grant)
        self.pins['root_grant'] = self.pin(path)
        self.save(self.live / 'activation.json', dict(self.pins, lease_id='owned-v5'))
        self.lease = dict(state='active', authorized=True, source_scope_authorized=True,
            profile=self.profile, lease_id='owned-v5', max_workers=2, allowed_video_ids=self.ids,
            expires_at_epoch=2000, coordinator_sha256=self.pins['code']['sha256'],
            worker_sha256=self.pins['worker']['sha256'], http_policy_seed_sha256=self.seed_sha,
            root_admission_sha256=self.pins['root_grant']['sha256'],
            **{key + '_sha256': self.pins[key]['sha256'] for key in ('settings', 'plan')})
        self.save(self.root / 'sync/stock_wpc_batch_v5_lease.json', self.lease)
        invoked = dict(status='running', profile=self.profile, lease_id='owned-v5', source_count=20,
            allowed_video_ids=self.ids, started_at_epoch=900, asr_handoff_enabled=False,
            native_batch_sha256=self.pins['code']['sha256'], worker_sha256=self.pins['worker']['sha256'],
            root_grant_sha256=self.pins['root_grant']['sha256'],
            **{key + '_sha256': self.pins[key]['sha256'] for key in ('settings', 'plan')})
        self.save(self.live / 'invocation.json', invoked)
        self.http = dict(schema_version=5, seed_sha256=self.seed_sha,
            state=dict(policy='native-http-consecutive-transfer-v5', root_review_sha256=self.review_sha,
                       circuit_break=None))
        self.save(self.root / 'sync/stock_wpc_batch_v5_http_state.json', self.http)

    def save(self, path, value):
        path.write_text(json.dumps(value), encoding='utf-8')

    def pin(self, path):
        raw = path.read_bytes()
        return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def lane(self, alive=True):
        with patch.object(status, 'owned_native_batch_command', return_value=alive):
            return status.native_v5_lane(self.root, self.now)

    def test_bound_live_command_is_running_but_dead_process_is_not(self):
        self.assertEqual(self.lane()['state'], 'running')
        self.assertEqual(self.lane(False), {})

    def test_changed_private_code_or_grant_cannot_claim_running(self):
        Path(self.pins['code']['path']).write_text('# changed\n', encoding='utf-8')
        self.assertEqual(self.lane(), {})

    def test_wrong_policy_seed_cannot_claim_running(self):
        self.http['seed_sha256'] = '3' * 64
        self.save(self.root / 'sync/stock_wpc_batch_v5_http_state.json', self.http)
        self.assertEqual(self.lane(), {})

    def test_administrative_stop_is_distinguished_from_actual_refusal(self):
        (self.root / 'sync/STOP_STOCK_WPC_BATCH_V5').write_bytes(b'owner bootstrap pause\n')
        lane = self.lane()
        self.assertEqual((lane['state'], lane['reason']), ('paused', 'worker_startup'))
        self.assertEqual(lane['proof'], 'owner_pause')
        self.http['state']['circuit_break'] = {'reason': 'immediate_global_refusal'}
        self.save(self.root / 'sync/stock_wpc_batch_v5_http_state.json', self.http)
        self.assertEqual(self.lane()['reason'], 'source_control_hold')

    def test_expired_owner_cannot_claim_running(self):
        self.lease['expires_at_epoch'] = self.now
        self.save(self.root / 'sync/stock_wpc_batch_v5_lease.json', self.lease)
        self.assertEqual(self.lane(), {})


if __name__ == '__main__':
    unittest.main()
