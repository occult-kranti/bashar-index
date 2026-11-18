"""Portable finite-cohort fixtures only; no network, workers, Drive or private data."""
import ast
import hashlib
import heapq
import importlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
from concurrent.futures import Future
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


class SchedulerFixture:
    """Deterministic source closures/publication delays; no real executor."""
    def __init__(self, root, durations, publish_seconds=5, body_bytes=20_000_000,
                 hold_on=None, revoke_after_first=False):
        self.root, self.durations = root, durations
        self.publish_seconds, self.body_bytes = publish_seconds, body_bytes
        self.hold_on, self.revoke_after_first = hold_on, revoke_after_first
        self.now, self.sequence, self.inactive = 0, 0, 0
        self.events, self.queue, self.futures, self.started, self.published = [], [], [], [], []
        self.publication_source_counts = []; self.closed = set(); self.lease_valid = True
        self.max_sources = self.max_projected = 0

    def observe(self):
        running = sum(not future.done() for future in self.futures)
        self.max_sources = max(self.max_sources, running)
        self.max_projected = max(self.max_projected, self.inactive + running * (2_000_000_000 + batch.HEADROOM))

    def advance(self, until):
        while self.queue and self.queue[0][0] <= until:
            self.now, _, callback = heapq.heappop(self.queue); callback()
        self.now = until

    def wait(self, futures, return_when=None):
        while not any(future.done() for future in futures): self.advance(self.queue[0][0])
        return {f for f in futures if f.done()}, {f for f in futures if not f.done()}

    def executor(self, max_workers):
        env = self
        class FakeExecutor:
            def __enter__(self): return self
            def __exit__(self, *args):
                while env.queue: env.advance(env.queue[0][0])
            def submit(self, function, item):
                future = Future(); env.futures.append(future); env.started.append(item['video_id'])
                env.events.append((env.now, 'source_start', item['video_id']))
                def complete():
                    future.set_result(function(item)); env.observe()
                env.sequence += 1
                heapq.heappush(env.queue, (env.now + env.durations[len(env.started) - 1], env.sequence, complete))
                env.observe(); return future
        return FakeExecutor()

    def run(self):
        self.root.mkdir(exist_ok=True); (self.root / 'sync').mkdir()
        obj = batch.NativeBatch.__new__(batch.NativeBatch); self.batch = obj
        obj.root = self.root; obj.spool = self.root / 'spool'; obj.jobs = obj.spool / 'jobs'
        obj.plan_sha = sha('scheduler plan'); obj.state_path = self.root / 'sync/native.jsonl'
        obj.batch_journal = self.root / 'sync/batch.jsonl'
        obj.items = [{'video_id': 'n' + str(i).zfill(10), 'channel_dir': 'fixture', 'tab': 'Videos',
                      'max_audio_bytes': 2_000_000_000} for i in range(len(self.durations))]
        obj.s = {'workers': 2, 'max_asset_bytes': 2_000_000_000, 'spool_cap_bytes': 5_500_000_000, 'remote': 'fixture:'}
        obj.lock = threading.RLock(); obj.source_stop = threading.Event(); obj.dispatch_paused = threading.Event()
        obj.adaptive_pause_until = 0; obj.live_reservations = {}; obj.budget = None; obj.capacity = {'inactive_spool_bytes': 0}
        obj.handoff = None; obj.finalize_handoff = lambda *args: None
        def guard(*, source=False, video_id=None, **kwargs):
            if not self.lease_valid: raise worker.Held('lease_revoked')
            if source: self.events.append((self.now, 'source_guard', video_id))
            obj.capacity = {'inactive_spool_bytes': self.inactive}; return 16_000_000_000
        def execute(item):
            self.closed.add(item['video_id'])
            if item['video_id'] == self.hold_on:
                obj.source_stop.set(); return {'status': 'held'}
            self.inactive += self.body_bytes; return {'status': 'local_complete'}
        def publish(item, result):
            obj.guard()
            if item['video_id'] not in self.closed: raise AssertionError('publication before owned closure')
            self.publication_source_counts.append(len(self.started)); self.advance(self.now + self.publish_seconds)
            self.inactive -= self.body_bytes; self.published.append(item['video_id']); self.observe()
            if self.revoke_after_first: self.lease_valid = False
        obj.guard, obj.execute_child, obj.publish = guard, execute, publish
        budget = SimpleNamespace(usage=lambda: self.inactive, _outstanding=lambda: 0)
        with patch.object(batch, 'ThreadPoolExecutor', side_effect=self.executor), \
                patch.object(batch, 'wait', side_effect=self.wait), \
                patch.object(batch, 'SlotBudget', return_value=budget):
            self.summary = obj.run()
        return self


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
                     'frozen_ingestion_coverage', 'worker_diagnostics'):
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

    def test_fatal_diagnostics_keep_safe_classes_and_control_stage_without_messages(self):
        diagnostics = batch.worker_diagnostics
        cause = PermissionError('https://fixture.invalid/?token=secret Authorization: fixture')
        cause.winerror = 5
        error = worker.Held('control_write_failed'); error.__cause__ = cause
        error.control_diagnostic = {'stage': 'replace', 'target': 'result.json', 'retry_attempts': 5,
                                    'url': 'https://fixture.invalid/private'}
        event = diagnostics.sanitized_event({'kind': 'native_worker_fatal', 'exceptions': diagnostics.exception_rows(error)})
        rendered = json.dumps(event)
        self.assertIn('PermissionError', rendered); self.assertIn('replace', rendered)
        self.assertEqual(5, event['exceptions'][1]['winerror'])
        self.assertNotIn('fixture.invalid', rendered); self.assertNotIn('Authorization', rendered)
        self.assertFalse(event['worker_result_authority']); self.assertEqual('unknown', event['source_access'])

    def test_durable_outer_fatal_is_separate_from_worker_result(self):
        diagnostics = batch.worker_diagnostics
        folder = self.root / ID; folder.mkdir()
        config = folder / 'config.json'; write(config, {'run_root': str(folder)})
        with patch.object(diagnostics.os, 'write') as stderr:
            result = diagnostics.report_fatal(PermissionError('secret URL'), ['--config', str(config)])
        self.assertTrue(result['fatal_file_written']); self.assertTrue((folder / 'worker-fatal.json').is_file())
        self.assertFalse((folder / 'result.json').exists())
        self.assertNotIn('secret URL', (folder / 'worker-fatal.json').read_text())
        self.assertTrue(stderr.call_args.args[1].startswith(diagnostics.PREFIX))

    def test_stderr_bounds_discard_unstructured_oversized_and_unknown_fields(self):
        diagnostics = batch.worker_diagnostics
        event = {'kind': 'native_worker_fatal', 'exceptions': [{'exception_class': 'PermissionError', 'winerror': 5,
                 'message': 'https://fixture.invalid/?token=secret'}], 'url': 'https://fixture.invalid/private'}
        line = diagnostics.PREFIX + json.dumps(event).encode() + b'\n'
        capture = diagnostics.StderrCapture(self.root)
        capture.consume(io.BytesIO(b'raw secret\n' + b'x' * (diagnostics.LINE_CAP + 1) + b'\n' + line * 500))
        summary = capture.finish(); saved = capture.path.read_bytes()
        self.assertLessEqual(len(saved), diagnostics.CAP); self.assertTrue(summary['retention_truncated'])
        self.assertEqual(1, summary['oversized_lines_discarded'])
        self.assertNotIn(b'fixture.invalid', saved); self.assertNotIn(b'raw secret', saved)
        self.assertFalse(summary['worker_result_authority'])

    def test_closed_fatal_still_holds_without_live_reservation(self):
        obj = batch.NativeBatch.__new__(batch.NativeBatch)
        obj.lock = threading.RLock(); obj.live_captures = {}; obj.live_reservations = {}
        folder = self.root / ID; folder.mkdir(); write(folder / 'worker-fatal.json', {'kind': 'native_worker_fatal'})
        obj.administrative_hold = Mock()
        self.assertTrue(obj.observe_worker_diagnostics(folder)); obj.administrative_hold.assert_called_once()

    def test_scheduler_refills_before_the_second_blocking_publication(self):
        env = SchedulerFixture(self.root, [1, 1, 1, 1, 40, 1]).run()
        self.assertEqual(6, env.publication_source_counts[1]); self.assertEqual(6, env.summary['verified'])
        for at, kind, ident in env.events:
            if kind == 'source_start':
                self.assertTrue(any(t <= at and k == 'source_guard' and value == ident for t, k, value in env.events))

    def test_scheduler_publisher_bound_fixture_has_no_parallel_publication(self):
        env = SchedulerFixture(self.root, [5] * 6, publish_seconds=20).run()
        self.assertEqual(125, env.now); self.assertEqual(6, len(set(env.published)))

    def test_scheduler_full_slots_and_actual_bytes_preserve_backpressure(self):
        env = SchedulerFixture(self.root, [1] * 6, publish_seconds=10, body_bytes=1_300_000_000).run()
        self.assertLessEqual(env.max_sources, 2); self.assertLessEqual(env.max_projected, 5_500_000_000)
        self.assertEqual(6, env.summary['verified']); self.assertEqual(0, env.inactive)

    def test_scheduler_source_hold_stops_refill(self):
        env = SchedulerFixture(self.root, [1] * 6, publish_seconds=10, hold_on='n0000000002').run()
        self.assertEqual(4, len(env.started)); self.assertEqual(2, env.summary['pending'])

    def test_scheduler_revoked_lease_prevents_more_source_and_publication(self):
        env = SchedulerFixture(self.root, [1] * 6, revoke_after_first=True).run()
        self.assertEqual(4, len(env.started)); self.assertEqual(1, len(env.published))
        self.assertEqual(2, env.summary['pending']); self.assertGreater(env.inactive, 0)

    def GO_fixture(self):
        obj = batch.NativeBatch.__new__(batch.NativeBatch)
        obj.lock = threading.RLock(); obj.source_stop = threading.Event(); obj.dispatch_paused = threading.Event()
        obj.adaptive_pause_until = 0; obj.observe_worker_diagnostics = lambda: False
        clock = SimpleNamespace(now=0.0)
        process = SimpleNamespace(poll=lambda: None)
        def sleep(seconds): clock.now += seconds
        def run():
            with patch.object(batch.time, 'time', side_effect=lambda: clock.now), \
                    patch.object(batch.time, 'monotonic', side_effect=lambda: clock.now), \
                    patch.object(batch.time, 'sleep', side_effect=sleep):
                return obj.await_owned_GO(ID, self.root, process, 0.0)
        return obj, clock, process, run

    def test_pre_GO_sibling_pause_after_spawn_waits_then_commits(self):
        obj, clock, process, run = self.GO_fixture(); calls = []
        def guard(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1: obj.adaptive_pause_until = 30.0
        obj.guard = guard; result = run()
        self.assertTrue((self.root / 'GO').is_file()); self.assertTrue(result['pause_observed'])
        self.assertGreaterEqual(result['waited_seconds'], 30); self.assertLess(result['waited_seconds'], worker.GO_WAIT_SECONDS)
        self.assertGreater(len(calls), 1); self.assertTrue(all(row['source'] and row['force'] for row in calls))

    def test_pre_GO_revocation_or_global_guard_hold_never_commits(self):
        obj, clock, process, run = self.GO_fixture()
        def guard(**kwargs):
            obj.adaptive_pause_until = 30
            if clock.now >= 1: raise worker.Held('lease_revoked')
        obj.guard = guard
        with self.assertRaises(worker.Held) as caught: run()
        self.assertEqual('lease_revoked', caught.exception.code); self.assertFalse((self.root / 'GO').exists())

    def test_pre_GO_child_exit_and_captured_fatal_each_block_commit(self):
        obj, clock, process, run = self.GO_fixture(); obj.guard = lambda **kwargs: None
        process.poll = lambda: 3
        with self.assertRaises(worker.Held) as caught: run()
        self.assertEqual('child_exited_before_GO', caught.exception.code); self.assertFalse((self.root / 'GO').exists())
        process.poll = lambda: None; obj.observe_worker_diagnostics = lambda: obj.source_stop.set()
        with self.assertRaises(worker.Held): run()
        self.assertFalse((self.root / 'GO').exists())

    def test_pre_GO_parent_bound_expires_inside_child_window_without_timeout_exemption(self):
        obj, clock, process, run = self.GO_fixture(); obj.adaptive_pause_until = 1000
        obj.guard = lambda **kwargs: None
        with self.assertRaises(worker.Held) as caught: run()
        self.assertEqual('pre_GO_dispatch_wait_deadline', caught.exception.code)
        self.assertEqual(worker.GO_WAIT_SECONDS - 5, clock.now); self.assertFalse((self.root / 'GO').exists())

    def test_parent_exception_context_keeps_frames_and_numbers_without_private_text(self):
        try: raise PermissionError(13, 'https://fixture.invalid/private?token=secret')
        except PermissionError as error: value = batch.exception_diagnostic(error)
        self.assertEqual('PermissionError', value['exception_class']); self.assertEqual(13, value['errno'])
        self.assertTrue(value['frames']); self.assertNotIn('fixture.invalid', str(value))
        self.assertNotIn(str(self.root), str(value))

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
