"""Portable finite-cohort fixtures only; no network, workers, Drive or private data."""
import ast
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

with patch('socket.socket.connect', side_effect=AssertionError('network forbidden')), \
        patch('subprocess.Popen', side_effect=AssertionError('process forbidden')):
    from pipeline.native_bulk import native_bulk_controller as controller

batch = controller.batch_module
worker = controller.worker
contract = controller.contract
policy = batch.http_policy
PACKAGE = Path(controller.__file__).resolve().parent
ID, OTHER, THIRD, FOURTH, PRIOR = (letter * 11 for letter in 'abcdz')
MEDIA = 'https://fixture.googlevideo.com/videoplayback?itag=140'


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def normalized_ast(value):
    """Ignore only the empty type-parameter field added in Python 3.12."""
    if isinstance(value, ast.AST):
        return {'node': type(value).__name__, 'fields': [
            [name, normalized_ast(field)] for name, field in ast.iter_fields(value)
            if not (name == 'type_params' and field == [])]}
    if isinstance(value, list):
        return [normalized_ast(item) for item in value]
    if isinstance(value, bytes):
        return {'bytes_hex': value.hex()}
    return value


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


def refusal(video=ID, status=403, unknown=False):
    return policy.classify_http_failure(status, MEDIA, None if unknown else MEDIA, MEDIA,
        'native_transfer', video, {'format_id': '140', 'filesize': 8},
        selection_validated=True, now_epoch=1000)


def state_and_review():
    event_id, attempt = sha('synthetic prior refusal'), sha('synthetic prior attempt')
    prior_event = policy.v4.classify_http_failure(403, MEDIA, MEDIA, MEDIA, 'native_transfer', PRIOR,
        {'format_id': '140', 'filesize': 8}, selection_validated=True, now_epoch=1000)
    raw = {'schema_version': 1, 'state': policy.v4.apply_event(policy.v4.empty_state(), prior_event, event_id, 1000)}
    raw_sha = sha(json.dumps(raw, sort_keys=True))
    tail = [{'attempt_sha256': attempt, 'v4_event_id': event_id, 'video_id': PRIOR, 'at_epoch': 1000}]
    review_sha = sha('synthetic review')
    value = policy.empty_state(raw, review_sha, raw_sha, tail)
    review = {'review_sha256': review_sha, 'allowed_video_ids': [ID, OTHER, THIRD, FOURTH],
              'quarantined_video_ids': [PRIOR], 'timeline_evidence_sha256s': [sha('proof one'), sha('proof two')],
              'historical_global_event_ids_covered': [], 'root_override_authorized': True,
              'inherited_v4_sha256': raw_sha, 'inherited_consecutive_tail': tail,
              'root_scope_kind': 'finite_immutable_cohort', 'cohort_manifest_sha256': sha('manifest'),
              'frame_map_sha256': sha('map')}
    return value, review


def full_success(video):
    return policy.full_transfer_event(video, {
        'finished_count': 1, 'finished_bytes': 8, 'audio_bytes_written': 8, 'known_selected_size': 8,
        'format_identity': {'format_id': '140', 'filesize': 8},
        'worker_sha256': sha('worker'), 'selected_metadata_sha256': sha('selection'),
        'selected_request_equal': True, 'final_response_equal': True, 'response_status': 200,
        'selection_validated': True, 'quality_proof_sha256': sha('quality'), 'quality_module_sha256': sha('probe'),
        'strict_quality': {'quality_state': 'complete_native_audio', 'strict_probe_passed': True,
                          'audio_streams': 1, 'video_streams': 0, 'packet_count': 10,
                          'container_duration_seconds': 10, 'source_duration_seconds': 10, 'codec': 'aac'}})


def terminal(video=ID):
    return {'schema_version': 1, 'video_id': video, 'status': 'held',
            'diagnostics': {'phase': 'terminal', 'error_class': 'native_downloader_failed',
                            'python_wire_requests': 3, 'python_body_bytes': 1234,
                            'audio_bytes_written': 0, 'native_finished_count': 0,
                            'full_native_http_transfer_observed': None, 'http_failure': None,
                            'http_escalation': None, 'global_failure_code': None}}


class PortableBulkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))

    def test_all_modules_import_from_package_without_workstation_paths(self):
        for name in ('native_batch', 'native_batch_worker', 'native_http_policy',
                     'native_http_policy_v4_frozen', 'bulk_contract', 'native_bulk_controller',
                     'frozen_ingestion_coverage'):
            module = importlib.import_module('pipeline.native_bulk.' + name)
            self.assertEqual(PACKAGE, Path(module.__file__).resolve().parent)
            self.assertIsNone(re.search(r'\b[A-Za-z]:[\\/]', Path(module.__file__).read_text(encoding='utf-8')))
        self.assertEqual(PACKAGE.parent, batch.PUBLIC_PIPE)
        self.assertEqual(PACKAGE.parent, worker.PUBLIC_PIPE)

    def test_explicit_sibling_policy_load_does_not_need_package_search_path(self):
        with patch.object(worker, '_HTTP_POLICY', None), \
                patch.object(sys, 'path', [x for x in sys.path if Path(x or '.').resolve() != PACKAGE]):
            loaded = worker.http_policy()
            self.assertEqual('native-http-consecutive-transfer-v5', loaded.POLICY)
            self.assertEqual(PACKAGE, Path(loaded.__file__).resolve().parent)

    def test_function_bodies_match_frozen_source_provenance(self):
        provenance = json.loads((PACKAGE / 'PROVENANCE.json').read_bytes())
        self.assertEqual('canonical_AST_without_empty_type_params_v1',
                         provenance['baseline_function_ast_algorithm'])
        for name, expected in provenance['baseline_function_ast_sha256'].items():
            tree = ast.parse((PACKAGE / name).read_text(encoding='utf-8'))
            functions = [normalized_ast(node) for node in ast.walk(tree)
                         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            actual = hashlib.sha256(json.dumps(functions, separators=(',', ':')).encode()).hexdigest()
            self.assertEqual(expected, actual, name)
        # Python 3.11 omits this field; Python 3.12+ supplies an empty list.
        old = ast.parse('def example():\n    return 1').body[0]
        modern = ast.parse('def example():\n    return 1').body[0]
        modern.type_params = []
        if 'type_params' not in modern._fields:
            modern._fields += ('type_params',)
        if 'type_params' in old._fields:
            old._fields = tuple(field for field in old._fields if field != 'type_params')
        self.assertEqual(normalized_ast(old), normalized_ast(modern))
        self.assertEqual(worker.PROFILE, contract.PROFILE)
        self.assertEqual(60, worker.GO_WAIT_SECONDS)

    def frames(self):
        ids = ['f' + str(i).zfill(10) for i in range(21)]
        rows = []
        for index, members in enumerate((ids[:20], ids[20:])):
            rows.append({'frame_index': index, 'plan_path': str(self.root / ('plan-' + str(index) + '.json')),
                         'plan_sha256': sha('plan ' + str(index)), 'video_ids': members,
                         'settings_path': str(self.root / ('settings-' + str(index) + '.json'))})
        return ids, {'schema_version': 1, 'cohort_manifest_sha256': sha('manifest'), 'frames': rows}

    def test_exact_finite_scope_and_ordered_frame_partition(self):
        ids, mapping = self.frames()
        manifest = {'schema_version': 1, 'cohort_id': 'synthetic', 'allowed_video_ids': ids}
        self.assertEqual(ids, contract.manifest_ids(manifest))
        self.assertEqual(2, len(contract.frames(mapping, sha('manifest'), ids)))
        mapping['frames'][1]['video_ids'] = [ids[0]]
        with self.assertRaises(contract.ContractError): contract.frames(mapping, sha('manifest'), ids)

    def test_scope_limits_omission_and_frame_widening_fail_closed(self):
        with self.assertRaises(contract.ContractError):
            contract.manifest_ids({'schema_version': 1, 'cohort_id': 'synthetic',
                                   'allowed_video_ids': ['f' + str(i).zfill(10) for i in range(1281)]})
        ids, mapping = self.frames()
        mapping['frames'][0]['video_ids'].append(ids[-1])
        with self.assertRaises(contract.ContractError): contract.frames(mapping, sha('manifest'), ids)
        ids, mapping = self.frames()
        mapping['frames'][0]['video_ids'].pop()
        with self.assertRaises(contract.ContractError): contract.frames(mapping, sha('manifest'), ids)

    def test_plan_mode_reads_synthetic_metadata_without_runtime(self):
        ids, mapping = self.frames()
        for row in mapping['frames']:
            write(Path(row['plan_path']), {'schema_version': 1, 'items': [{'video_id': x} for x in row['video_ids']]})
            row['plan_sha256'] = contract.digest(row['plan_path'])
        manifest_path, map_path = self.root / 'manifest.json', self.root / 'map.json'
        write(manifest_path, {'schema_version': 1, 'cohort_id': 'synthetic', 'allowed_video_ids': ids})
        mapping['cohort_manifest_sha256'] = contract.digest(manifest_path)
        write(map_path, mapping)
        settings = self.root / 'controller-settings.json'
        write(settings, {'root': str(self.root), 'owner': 'root', 'lease_id': 'synthetic',
                         'root_admission_path': str(self.root / 'absent-grant.json'),
                         'cohort_manifest': {'path': str(manifest_path), 'sha256': contract.digest(manifest_path)},
                         'frame_map': {'path': str(map_path), 'sha256': contract.digest(map_path)}})
        result = controller.main(['plan', '--settings', str(settings)])
        self.assertEqual(21, result['cohort_items'])
        self.assertEqual(0, result['source_requests'])
        self.assertFalse((self.root / 'runtime').exists())

    def test_streak_and_sticky_stop_survive_ledger_restart_and_later_success(self):
        value, review = state_and_review()
        value = policy.apply_outcome(value, policy.refusal_event(refusal(ID)), sha('first'), sha('attempt one'), 1001)
        path = self.root / 'ledger.json'; write(path, value)
        restored = json.loads(path.read_bytes())
        value = policy.apply_outcome(restored, policy.refusal_event(refusal(OTHER)), sha('second'), sha('attempt two'), 1002)
        self.assertEqual(3, policy.reduce_outcomes(value)['consecutive_distinct_403'])
        value = policy.apply_outcome(value, full_success(THIRD), sha('success'), sha('attempt three'), 1003)
        value = json.loads(json.dumps(value))
        self.assertTrue(policy.status(value, 1004, historical_review=review, candidate_video_id=FOURTH)['global_stop'])
        self.assertEqual(4, value['next_sequence'])

    def test_only_full_strict_quality_resets_and_late_success_is_rejected(self):
        value, _ = state_and_review()
        local = policy.apply_outcome(value, policy.local_event(ID, 'format_unavailable'), sha('local'), sha('local attempt'), 1001)
        self.assertEqual(1, policy.reduce_outcomes(local)['consecutive_distinct_403'])
        valid = policy.apply_outcome(local, full_success(OTHER), sha('strict'), sha('strict attempt'), 1002)
        self.assertEqual(0, policy.reduce_outcomes(valid)['consecutive_distinct_403'])
        proof = full_success(THIRD)['proof']; proof['strict_quality']['strict_probe_passed'] = False
        with self.assertRaises(policy.PolicyError): policy.full_transfer_event(THIRD, proof)
        with self.assertRaises(policy.PolicyError):
            policy.apply_outcome(valid, full_success(THIRD), sha('late'), sha('late attempt'), 1001)

    def parent(self, result):
        obj = batch.NativeBatch.__new__(batch.NativeBatch)
        obj.root = self.root; obj.jobs = self.root / 'jobs'; obj.jobs.mkdir(exist_ok=True)
        ident = result['video_id']; folder = obj.jobs / ident; folder.mkdir(exist_ok=True)
        write(folder / 'attempt.json', {'video_id': ident})
        write(folder / 'result.json', result)
        write(folder / 'parent-audit.json', {'owned_processes_gone': True})
        value, review = state_and_review()
        ledger = self.root / 'ledger.json'; write(ledger, {'schema_version': 5, 'state': value})
        obj.plan_sha = sha('plan'); obj.http_state_path = ledger; obj.http_review = review
        obj.s = {'adaptive_pause_seconds': 0}; obj.adaptive_pause_until = 0; obj.lock = threading.RLock()
        obj.source_stop = threading.Event(); obj.stop_path = self.root / 'STOP'
        obj.live_reservations = {ident: {'folder': folder, 'bytes': 1000}}
        obj.items = [{'video_id': ident}]
        obj.policy_envelope = lambda: json.loads(ledger.read_bytes())
        order = []
        def latch(*args, **kwargs):
            order.append('hold'); obj.source_stop.set()
        def release(video):
            order.append('release'); obj.live_reservations.pop(video)
        obj.latch_global = latch; obj.release_after_reconcile = release
        return obj, folder, ledger, order

    def test_complete_held_terminal_without_progress_is_authoritative(self):
        result = terminal(); obj, folder, ledger, order = self.parent(result)
        obj.finalize_child_result(ID, folder, result)
        self.assertEqual(['release'], order); self.assertFalse(obj.source_stop.is_set())
        self.assertEqual(1, policy.reduce_outcomes(json.loads(ledger.read_bytes())['state'])['consecutive_distinct_403'])
        self.assertFalse(controller.frame_closed(obj)[0]['progress_observed'])

    def test_final_only_http_is_committed_before_release_and_global_hold(self):
        for status, unknown, expected in ((403, False, ['release']), (429, False, ['hold', 'release']),
                                          (403, True, ['hold', 'release'])):
            with self.subTest(status=status, unknown=unknown):
                with tempfile.TemporaryDirectory() as temporary:
                    original_root = self.root; self.root = Path(temporary)
                    try:
                        result = terminal(); result['diagnostics'].update(error_class='source_' + str(status),
                            http_failure=refusal(ID, status, unknown), http_failure_at_epoch=1001)
                        obj, folder, ledger, order = self.parent(result)
                        original_release = obj.release_after_reconcile
                        def release(video):
                            state = json.loads(ledger.read_bytes())['state']
                            self.assertEqual(1, len(state['outcomes']))
                            if status == 403 and not unknown:
                                self.assertEqual(2, policy.reduce_outcomes(state)['consecutive_distinct_403'])
                            else:
                                self.assertIsNotNone(state['circuit_break'])
                            original_release(video)
                        obj.release_after_reconcile = release
                        obj.finalize_child_result(ID, folder, result)
                        self.assertEqual(expected, order)
                        self.assertFalse((folder / 'progress.json').exists())
                    finally:
                        self.root = original_root

    def test_progress_alone_or_incomplete_final_still_holds(self):
        result = terminal(); result.pop('diagnostics')
        obj, folder, _, order = self.parent(result)
        write(folder / 'progress.json', {'phase': 'terminal', 'error_class': None})
        obj.finalize_child_result(ID, folder, result)
        self.assertTrue(obj.source_stop.is_set()); self.assertEqual(['release'], order)
        with self.assertRaises(contract.ContractError): controller.frame_closed(obj)
        (folder / 'result.json').unlink()
        with self.assertRaises(contract.ContractError): controller.frame_closed(obj)

    def test_typed_parent_deadline_is_unknown_quarantine_not_worker_success(self):
        result = {'status': 'held', 'video_id': ID, 'diagnostics': {'error_class': 'child_result_missing'}}
        obj, folder, ledger, order = self.parent(result)
        (folder / 'result.json').unlink()
        grant = self.root / 'grant.json'; write(grant, {'synthetic': True})
        obj.settings_path = self.root / 'settings.json'
        obj.s.update(job_wall_seconds=600, root_admission_path=str(grant))
        write(obj.settings_path, obj.s)
        write(folder / 'attempt.json', {'schema_version': 1, 'video_id': ID,
              'plan_sha256': obj.plan_sha, 'worker_sha256': worker.digest(worker.__file__)})
        deadline = {'kind': 'bootstrap_deadline', 'configured_seconds': 90, 'actual_elapsed_seconds': 91}
        write(folder / 'parent-audit.json', {'schema_version': 1, 'video_id': ID,
              'owned_processes_gone': True, 'profile_cleaned': True, 'process_cleanup_errors': [],
              'error_class': 'bootstrap_deadline', 'parent_deadline': deadline,
              'owned_child_identity': {'pid': 42, 'process_creation_filetime': '12345'}, 'elapsed_seconds': 92})
        obj.guard = Mock()
        self.assertTrue(obj.finalize_child_result(ID, folder, result,
                        parent_deadline=deadline, parent_error='bootstrap_deadline'))
        self.assertFalse((folder / 'result.json').exists()); self.assertFalse((folder / 'progress.json').exists())
        proof = json.loads((folder / 'parent-censored.json').read_bytes())
        self.assertEqual('unknown', proof['source_access'])
        self.assertTrue(all(value is None for value in proof['source_counters'].values()))
        self.assertFalse(proof['counts_as_success']); self.assertFalse(proof['resets_streak'])
        self.assertFalse(obj.source_stop.is_set())
        state = json.loads(ledger.read_bytes())['state']
        self.assertEqual(1, policy.reduce_outcomes(state)['consecutive_distinct_403'])
        self.assertTrue(policy.status(state, time.time(), historical_review=obj.http_review,
                                     candidate_video_id=ID)['item_quarantined'])

    def test_timeout_local_row_does_not_mask_real_media_order_or_global_hold(self):
        value, _ = state_and_review()
        value = policy.apply_outcome(value, full_success(ID), sha('media one'), sha('attempt one'), 1100)
        value = policy.apply_outcome(value, policy.local_event(OTHER, 'parent_censored_job_deadline'),
                                     sha('local'), sha('attempt two'), 1110)
        value = policy.apply_outcome(value, full_success(THIRD), sha('media two'), sha('attempt three'), 1105)
        self.assertIsNone(value['circuit_break'])
        with self.assertRaises(policy.PolicyError):
            policy.apply_outcome(value, full_success(FOURTH), sha('late'), sha('attempt four'), 1104)
        value = policy.apply_outcome(value, policy.refusal_event(refusal(FOURTH, 429)),
                                     sha('global'), sha('attempt five'), 1111)
        self.assertEqual('immediate_global_refusal', value['circuit_break']['reason'])


class PortableCapacityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.events = []; self.world = {'a': 400, 'b': 800, 'other': 100}
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))
        obj = self.obj = batch.NativeBatch.__new__(batch.NativeBatch)
        obj.root = self.root; obj.spool = self.root / 'spool'; obj.lock = threading.RLock()
        obj.live_reservations = {key: {'folder': obj.spool / key, 'bytes': 1000} for key in ('a', 'b')}
        events = self.events
        class Budget:
            active = {'a': {'bytes': 1000}, 'b': {'bytes': 1000}}
            inactive_bytes = 0
            def release(self, video): events.append(('release', video, self.inactive_bytes)); self.active.pop(video)
            def _outstanding(self): return sum(row['bytes'] for row in self.active.values())
        obj.budget = Budget(); obj.source_stop = threading.Event(); obj.stop_path = self.root / 'STOP'
        obj._partition_cache = None; obj._partition_key = None; obj._partition_at = 0
        self.clock = [100.0]
        self.enterContext(patch.object(batch.time, 'monotonic', side_effect=lambda: self.clock[0]))
        self.scan = self.enterContext(patch.object(batch, 'capacity_snapshot', side_effect=self.snapshot))

    def snapshot(self, root, spool, folders):
        excluded = {Path(folder).name for folder in folders}; self.events.append(('scan', excluded))
        size = sum(value for key, value in self.world.items() if key not in excluded)
        return {'inactive_private_bytes': size, 'inactive_spool_bytes': size}

    def test_sibling_writes_keep_full_slots_and_expired_cache_reconciles(self):
        self.assertEqual(100, self.obj.capacity_partition()['inactive_private_bytes'])
        self.world['a'] = 950; self.world['other'] = 500; self.clock[0] += 11
        self.assertEqual(100, self.obj.capacity_partition()['inactive_private_bytes'])
        self.assertEqual(2000, self.obj.budget._outstanding())
        self.clock[0] += 1
        self.assertEqual(500, self.obj.capacity_partition()['inactive_private_bytes'])
        self.assertEqual(2, self.scan.call_count)

    def test_finalized_folder_is_counted_before_slot_release(self):
        self.obj.capacity_partition(); self.events.clear()
        with self.obj.lock: self.obj.release_after_reconcile('a')
        self.assertEqual([('scan', {'b'}), ('release', 'a', 500)], self.events)
        self.assertEqual(1500, self.obj.budget.inactive_bytes + self.obj.budget._outstanding())

    def test_scan_failure_retains_reservation_and_holds_dispatch(self):
        self.scan.side_effect = OSError('synthetic scan failure')
        with self.assertRaises(OSError): self.obj.release_after_reconcile('a')
        self.assertEqual({'a', 'b'}, set(self.obj.budget.active))
        self.assertTrue(self.obj.source_stop.is_set())

    def test_commitment_changes_and_publication_cleanup_invalidate_partition(self):
        self.obj.capacity_partition(); self.obj.budget.active['a']['bytes'] = 1100
        self.obj.capacity_partition(); self.assertEqual(2, self.scan.call_count)
        def publish(item, result): self.world['other'] = 20; return 'synthetic receipt'
        self.obj._publish_uncached = publish
        self.assertEqual('synthetic receipt', self.obj.publish({}, {}))
        self.assertEqual(20, self.obj.budget.inactive_bytes)


if __name__ == '__main__':
    unittest.main()
