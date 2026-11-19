"""Qualified activity needs actual bound ownership; saved counts remain receipts."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import ingestion_status as status
from pipeline import qualified_batch_status as reader


class QualifiedBatchStatusTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); (self.root / 'sync').mkdir()
        self.home = self.root / 'provisioning/qualified-response18-parallel-batch-v2'
        (self.home / 'owner-runtime').mkdir(parents=True); (self.home / 'runtime').mkdir()
        self.profile = 'qualified_youtube_response18_parallel_batch_v2'
        self.ids = ['a' * 11, 'b' * 11]
        self.wrapper = {'pid': 10, 'process_creation_filetime': '100'}
        self.base = {'pid': 11, 'process_creation_filetime': '110'}
        codes = []
        for name in sorted(reader.ROLES):
            path = self.home / name; path.write_text('# source-free fixture\n'); codes.append(self.pin(path))
        self.scope = self.write(self.home / 'scope.json', {'video_ids': self.ids})
        self.settings = {'private_root': str(self.root), 'pipeline_directory': str(self.home),
                         'profile': self.profile, 'lease_id': self.profile, 'allowed_video_ids': self.ids, 'code_pins': codes}
        settings_pin = self.write(self.home / 'settings.json', self.settings)
        self.grant = {'enabled': True, 'owner': 'root', 'source_authorized': True, 'drive_publication_allowed': True,
                      'ASR_authorized': False, 'GPU_authorized': False, 'automatic_retry_allowed': False,
                      'qualified_success_HTTP_reset_allowed': False, 'profile': self.profile,
                      'literal_language_tags_authorized': True, 'default_is_not_original_authorized': True,
                      'native_route_handoff_authorized': True, 'two_stage_media_GO_required': True,
                      'atomic_derived_MOVE_required': True, 'maximum_source_bytes': 2_000_000_000,
                      'maximum_derived_bytes': 2_000_000_000,
                      'settings_sha256': settings_pin['sha256'], 'plan_sha256': self.scope['sha256'],
                      'allowed_video_ids': self.ids, 'source_workers': 2, 'publishers': 1,
                      'spool_cap_bytes': 5_000_000_000, 'not_before_epoch': 800, 'expires_at_epoch': 2000}
        self.grant_pin = self.write(self.home / 'root-grant.ACTIVE.json', self.grant)
        self.lease = {'profile': self.profile, 'lease_id': self.profile, 'state': 'active', 'owner': 'root',
                      'root_grant_sha256': self.grant_pin['sha256'], 'settings_sha256': settings_pin['sha256'],
                      'allowed_video_ids': self.ids, 'source_workers': 2, 'spool_cap_bytes': 5_000_000_000,
                      'created_at_epoch': 900}
        self.lease_path = self.root / 'sync' / (self.profile + '_lease.json'); self.write(self.lease_path, self.lease)
        self.row = {'lease_id': self.profile, 'state': 'active', 'max_bytes': 5_000_000_000,
                    'root_grant_sha256': self.grant_pin['sha256']}
        self.resources()
        self.invoked = {'root_grant_sha256': self.grant_pin['sha256'], 'settings_sha256': settings_pin['sha256'],
                        'plan_sha256': self.scope['sha256'], 'identity': self.wrapper, 'started_at_epoch': 900,
                        'source_count': 2, 'owned_job_attached': True, 'suspended_attach_before_resume': True}
        self.write(self.home / 'owner-runtime/invocation.json', self.invoked)
        self.write(self.home / 'runtime/source-invocation.json', {'parent_identity': self.base})
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))

    def pin(self, path):
        raw = path.read_bytes(); return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value), encoding='utf-8'); return self.pin(path)

    def resources(self): self.write(self.root / 'sync/analysis_resource_plan.json', {'reservations': [self.row]})

    def read(self, *, now=1000, alive=True, command=True, child=True):
        with patch.object(status, 'owned_process_alive', return_value=alive), \
             patch.object(status, 'owned_process_child_of', return_value=child), \
             patch.object(status, 'owned_native_batch_command', return_value=command):
            return status.qualified_batch_state(self.root, now)

    def attempt(self, video, *, bytes_written=0, phase='native_transfer', result=None, closed=False):
        run = self.root / self.profile / 'jobs' / video
        attempt = {'video_id': video, 'root_grant_sha256': self.grant_pin['sha256'],
                   'settings_sha256': self.invoked['settings_sha256'], 'plan_sha256': self.scope['sha256']}
        attempt_pin = self.write(run / 'attempt.json', attempt)
        self.write(run / 'child-binding.json', {'child_identity': {'pid': 12, 'process_creation_filetime': '120'},
                                               'Windows_job_attached': True, 'resumed': True})
        self.write(run / 'progress.json', {'phase': phase, 'audio_source_bytes_written': bytes_written})
        if result: self.write(run / 'result.json', {'status': result})
        if closed:
            self.write(run / 'parent-audit.json', {'owned_processes_gone': True, 'owned_closure': {'closed': True},
                       'root_grant_sha256': self.grant_pin['sha256'], 'settings_sha256': self.invoked['settings_sha256'],
                       'plan_sha256': self.scope['sha256'], 'attempt_sha256': attempt_pin['sha256']})
        return run

    def close(self):
        self.lease['state'] = self.row['state'] = 'released'; self.write(self.lease_path, self.lease); self.resources()
        report = self.write(self.home / 'runtime/cohort-report.json', {'root_grant_sha256': self.grant_pin['sha256'],
            'status': 'held', 'outcomes': [{'video_id': self.ids[0], 'state': 'held'}, {'video_id': self.ids[1], 'state': 'pending'}]})
        terminal = self.write(self.home / 'owner-runtime/terminal.json', {'root_grant_sha256': self.grant_pin['sha256'],
            'owned_job_closed': True, 'exit_code': 0, 'at_epoch': 1100, 'actual_cohort_report': report, 'verified_editions': 0})
        exited = self.write(self.home / 'owner-runtime/process-exit.json', {'root_grant_sha256': self.grant_pin['sha256'],
            'identity': self.wrapper, 'exit_code': 0, 'owned_closure': {'identity': self.wrapper, 'closed': True,
                                                                    'owned_job_empty': True, 'errors': []}})
        self.write(self.home / 'closure/release-proof.json', {'root_grant_sha256': self.grant_pin['sha256'],
            'released_lease': self.pin(self.lease_path), 'terminal': terminal, 'exit': exited})
        self.write(self.root / 'sync' / (self.profile + '_administrative_hold.json'), {'reason': 'local_worker'})

    def test_live_scope_counts_observed_body_not_phase_or_saved_status(self):
        self.attempt(self.ids[0])
        first = self.read()
        self.assertEqual(first['public']['state'], 'running')
        self.assertEqual(first['video_stages'], {self.ids[0]: 'processing', self.ids[1]: 'queued'})
        self.attempt(self.ids[0], bytes_written=123)
        self.assertEqual(self.read()['video_stages'][self.ids[0]], 'downloading')
        self.attempt(self.ids[0], result='local_extract_complete', closed=True)
        self.assertEqual(self.read()['video_stages'][self.ids[0]], 'awaiting_upload')
        self.assertNotIn('saved', self.read()['video_stages'].values())

    def test_live_identity_parent_and_command_are_all_required(self):
        for kwargs in ({'alive': False}, {'command': False}, {'child': False}):
            with self.subTest(kwargs=kwargs):
                result = self.read(**kwargs)
                self.assertFalse(result['public']['process_confirmed']); self.assertNotEqual(result['public']['state'], 'running')

    def test_closed_expired_scope_uses_actual_Job_proof_without_historical_PID_queries(self):
        self.attempt(self.ids[0], result='held', closed=True); self.close()
        with patch.object(status, 'owned_process_alive', side_effect=AssertionError('historical query forbidden')), \
             patch.object(status, 'owned_native_batch_command', side_effect=AssertionError('historical command forbidden')):
            result = status.qualified_batch_state(self.root, 4000)
        self.assertEqual(result['public']['state'], 'paused'); self.assertTrue(result['public']['future_growth_released'])
        self.assertEqual(result['public']['held_items'], 1); self.assertEqual(result['public']['not_started_items'], 1)
        self.assertNotIn(self.ids[1], result['video_stages'])
        public = json.dumps(result['public'])
        for private in (str(self.root), self.ids[0], 'process_creation_filetime', self.grant_pin['sha256']): self.assertNotIn(private, public)

    def test_missing_final_is_unresolved_and_wrong_exit_identity_rejects_closed_proof(self):
        self.attempt(self.ids[0]); self.close()
        self.assertEqual(self.read(now=4000)['public']['unresolved_items'], 1)
        path = self.home / 'owner-runtime/process-exit.json'; exitproof = json.loads(path.read_text())
        exitproof['identity']['process_creation_filetime'] = '999'; self.write(path, exitproof)
        self.assertEqual(self.read(now=4000), {})

    def test_mutated_scope_code_or_grant_cannot_establish_activity(self):
        (self.home / 'source_worker.py').write_text('# changed\n')
        self.assertEqual(self.read(), {})

    def test_rolling_scope_with_four_workers_and_separate_local_cooldown(self):
        old = self.home
        self.home = old.with_name('regular-public-intake-frame-v10')
        self.home.mkdir()
        self.profile = 'qualified_youtube_response18_parallel_batch_v10'
        ids = [f'{n:011d}' for n in range(96)]
        settings = dict(self.settings, pipeline_directory=str(self.home), profile=self.profile,
                        lease_id=self.profile, source_workers=4, publishers=1, maximum_cohort_items=len(ids),
                        spool_cap_bytes=6_000_000_000, allowed_video_ids=ids)
        for pin in settings['code_pins']:
            src = Path(pin['path'])
            dst = self.home / src.name
            dst.write_bytes(src.read_bytes())
            pin.update(self.pin(dst))
        scope = self.write(self.home / 'scope.json', {'allowed_video_ids': ids})
        settings_hash = self.write(self.home / 'settings.json', settings)['sha256']
        grant = dict(self.grant, profile=self.profile, allowed_video_ids=ids, maximum_cohort_items=len(ids),
                     settings_sha256=settings_hash, plan_sha256=scope['sha256'], source_workers=4,
                     spool_cap_bytes=6_000_000_000)
        grant_hash = self.write(self.home / 'root-grant.ACTIVE.json', grant)['sha256']
        lease = dict(self.lease, profile=self.profile, lease_id=self.profile, settings_sha256=settings_hash,
                     source_workers=4, spool_cap_bytes=6_000_000_000, root_grant_sha256=grant_hash,
                     allowed_video_ids=ids, created_at_epoch=950)
        self.write(self.root / 'sync' / (self.profile + '_lease.json'), lease)
        self.row.update(lease_id=self.profile, max_bytes=6_000_000_000, root_grant_sha256=grant_hash)
        self.resources()
        self.write(self.home / 'owner-runtime/invocation.json', dict(self.invoked, root_grant_sha256=grant_hash,
                   plan_sha256=scope['sha256'], settings_sha256=settings_hash, source_count=len(ids), source_workers=4))
        self.write(self.home / 'runtime/source-invocation.json', {'parent_identity': self.base})
        running = self.read()
        self.assertEqual(running['public']['workers'], 4)
        self.assertEqual(len(running['video_stages']), 96)
        (self.root / 'sync' / ('STOP_' + self.profile.upper())).touch()
        self.write(self.root / 'sync' / (self.profile + '_source_cooldown.json'),
                   {'scope': 'google_provider', 'until_epoch': 1800, 'root_grant_sha256': grant_hash})
        paused = self.read()['public']
        self.assertEqual((paused['state'], paused['workers'], paused['local_provider_cooldown_until_epoch']),
                         ('paused', 0, 1800))

    def test_malformed_matching_lease_fails_closed_instead_of_falling_back_live(self):
        newer = self.root / 'sync/qualified_youtube_response18_parallel_batch_v3_lease.json'
        for timestamp in ('unknown', None, float('inf'), True):
            self.write(newer, {'created_at_epoch': timestamp})
            with self.subTest(timestamp=timestamp): self.assertEqual(self.read(), {})
        newer.write_text('{broken', encoding='utf-8')
        self.assertEqual(self.read(), {})


if __name__ == '__main__': unittest.main()
