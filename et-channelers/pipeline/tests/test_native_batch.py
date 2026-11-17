"""No source, browser, optional media imports, subprocesses, or real Drive."""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pipeline import native_batch as batch, native_batch_worker as worker, native_batch_quality as quality
from pipeline import drive_ingest as storage

ID = 'aaaaaaaaaaa'


def item(duration=10):
    row = {'video_id': ID, 'channel_dir': 'fixture', 'tab': 'videos'}
    return dict(row, queue_row=row, queue_row_sha256=hashlib.sha256(batch.encoded(row)).hexdigest(),
                video_url='https://www.youtube.com/watch?v=' + ID, duration_seconds=duration)


def scan(stderr='', duration=10, codec='opus'):
    return SimpleNamespace(returncode=0, stderr=stderr, stdout=json.dumps({'streams': [
        {'codec_type': 'audio', 'codec_name': codec, 'nb_read_packets': '500'}], 'format': {'duration': duration}}))


class FakeDrive:
    def __init__(self): self.calls = []; self.record = None; self.missing_id = False; self.fail_copy = False
    def copy_pair(self, audio, metadata, ar, mr):
        self.calls.append('copy')
        if self.fail_copy: raise storage.IngestError('drive_conflict', 'fixture')
        self.record = (storage.hash_file(audio), storage.hash_file(metadata))
    def stat_batch(self, remote, paths, manifest):
        self.calls.append('stat')
        return {path: {'Size': p['bytes'], 'Hashes': {'MD5': p['md5']}, 'ID': '' if self.missing_id else str(i + 1)}
                for i, (path, p) in enumerate(zip(paths, self.record))}
    def stat(self, remote):
        raise storage.IngestError('drive_conflict', 'fixture requires explicit conflict evidence')


class NativeBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.enterContext(patch.object(worker, 'TARGET', ID))
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))

    def prepared(self):
        obj = batch.NativeBatch.__new__(batch.NativeBatch)
        obj.root = self.root; obj.jobs = self.root / 'native_batch/jobs/fixture'; obj.jobs.mkdir(parents=True)
        obj.s = {'remote': 'fixture:archive', 'lease_id': 'fixture'}; obj.plan_sha = '0' * 64
        obj.guard = Mock(); obj.state_path = self.root / 'sync/drive_ingest_manifest.jsonl'
        obj.batch_journal = self.root / 'sync/native_batch_manifest.jsonl'; obj.drive = FakeDrive()
        folder = obj.jobs / ID; folder.mkdir()
        audio = folder / 'native-audio.webm'; audio.write_bytes(b'fixture bytes')
        metadata = folder / 'metadata.json'; worker.write(metadata, {'source': {'video_id': ID}})
        result = {'status': 'local_complete', 'video_id': ID, 'audio': {'filename': audio.name,
            **storage.hash_file(audio), 'fingerprint': list(storage.fingerprint(audio))},
            'metadata': {'filename': metadata.name, 'sha256': worker.digest(metadata)},
            'probe': {'quality_state': 'complete_native_audio'}}
        return obj, folder, result

    def test_unknown_or_long_duration_is_admitted_but_row_change_is_not(self):
        path = self.root / 'plan.json'
        for duration in (None, 100_000):
            worker.write(path, {'schema_version': 1, 'items': [item(duration)]})
            self.assertEqual(batch.load_plan(path)[1][0]['duration_seconds'], duration)
        value = item(); value['queue_row']['channel_dir'] = 'different'
        worker.write(path, {'schema_version': 1, 'items': [value]})
        with self.assertRaisesRegex(worker.Held, 'plan_target'): batch.load_plan(path)

    def test_ended_stream_original_is_allowed_and_pending_live_is_held(self):
        info = {'id': ID, 'protocol': 'https', 'vcodec': 'none', 'acodec': 'opus', 'duration': 100_000,
                'language': 'de', 'language_preference': 10, 'format_note': 'German original', 'live_status': 'post_live'}
        self.assertEqual(worker.validate_selection(info, ID, None, 2_000_000_000, {'opus'})['language'], 'de')
        for status in ('is_live', 'is_upcoming'):
            with self.assertRaisesRegex(worker.Held, 'source_identity'):
                worker.validate_selection(dict(info, live_status=status), ID, None, 2_000_000_000, {'opus'})
        with self.assertRaisesRegex(worker.Held, 'asset_budget_deferred'):
            worker.validate_selection(dict(info, filesize=2_000_000_001), ID, None, 2_000_000_000, {'opus'})

    def test_packet_scan_clean_requires_no_full_decode(self):
        file = self.root / 'audio'; file.write_bytes(b'123')
        runner = Mock(return_value=scan())
        proof = quality.inspect_quality(file, {'acodec': 'opus', 'duration': 10}, 'probe', 'decode', run=runner)
        self.assertEqual(runner.call_count, 1); self.assertTrue(proof['strict_probe_passed'])
        self.assertIsNone(proof['clean_decode'])

    def test_only_known_warning_plus_exact_bytes_full_decode_can_pass(self):
        file = self.root / 'audio'; file.write_bytes(b'123')
        warning = '[opus @ 000012ab] Error parsing Opus packet header.\n'
        decode = SimpleNamespace(returncode=0, stdout='out_time_us=10000000\nprogress=end\n', stderr=warning)
        runner = Mock(side_effect=[scan(warning), decode])
        proof = quality.inspect_quality(file, {'acodec': 'opus', 'duration': 10, 'filesize': 3}, 'p', 'd', run=runner)
        self.assertEqual(runner.call_count, 2); self.assertEqual(proof['quality_state'], 'complete_with_codec_warning')
        self.assertFalse(proof['clean_decode']); self.assertFalse(proof['strict_probe_passed'])
        for stderr in ('unrelated decode failure', warning + warning):
            with self.assertRaisesRegex(quality.QualityHold, 'codec_warning_unrecognized'):
                quality.inspect_quality(file, {'acodec': 'opus', 'duration': 10, 'filesize': 3}, 'p', 'd', run=Mock(return_value=scan(stderr)))

    def test_warning_without_exact_size_or_complete_decode_is_held(self):
        file = self.root / 'audio'; file.write_bytes(b'123')
        warning = 'Error parsing Opus packet header.'
        with self.assertRaisesRegex(quality.QualityHold, 'warning_exact_source_size_required'):
            quality.inspect_quality(file, {'acodec': 'opus', 'duration': 10}, 'p', 'd', run=Mock(return_value=scan(warning)))
        decode = SimpleNamespace(returncode=0, stdout='out_time_us=6000000\nprogress=end\n', stderr='')
        with self.assertRaisesRegex(quality.QualityHold, 'warning_decode_extent'):
            quality.inspect_quality(file, {'acodec': 'opus', 'duration': 10, 'filesize': 3}, 'p', 'd', run=Mock(side_effect=[scan(warning), decode]))

    def test_exact_canonical_pair_is_durable_before_cleanup(self):
        obj, folder, result = self.prepared()
        original_remove = storage.remove_local
        observed = []
        def remove(path, *a, **kw):
            if path.name in {ID + '.webm', ID + '.info.json'}:
                latest = storage.load_state(obj.state_path)[ID]
                observed.append(latest['status'])
                self.assertEqual(latest['status'], 'verified')
                self.assertTrue(latest['drive_id']); self.assertTrue(latest['metadata']['drive_id'])
            return original_remove(path, *a, **kw)
        with patch.object(storage, 'remove_local', side_effect=remove): done = obj.publish(item(), result)
        self.assertEqual(observed, ['verified', 'verified'])
        self.assertTrue(storage.receipt_complete(done, item(), obj.s['remote']))
        self.assertEqual(obj.drive.calls, ['copy', 'stat'])

    def test_missing_drive_id_retains_both_files(self):
        obj, folder, result = self.prepared(); obj.drive.missing_id = True
        with self.assertRaisesRegex(worker.Held, 'drive_identity_missing'): obj.publish(item(), result)
        self.assertTrue((folder / (ID + '.webm')).exists()); self.assertTrue((folder / (ID + '.info.json')).exists())

    def test_immutable_conflict_retains_local_pair_for_resume_without_source(self):
        obj, folder, result = self.prepared(); obj.drive.fail_copy = True
        with self.assertRaises(storage.IngestError): obj.publish(item(), result)
        self.assertTrue((folder / 'canonical-record.json').exists())
        obj.drive.fail_copy = False
        self.assertTrue(storage.receipt_complete(obj.publish(item(), result), item(), obj.s['remote']))

    def test_conflicting_metadata_preservation_follows_exact_remote_audio_proof(self):
        obj, folder, result = self.prepared()
        original_copy = obj.drive.copy_pair; calls = []
        def copy(*args):
            calls.append('copy')
            if len(calls) == 1: raise storage.IngestError('drive_conflict', 'fixture old metadata')
            return original_copy(*args)
        audio_proof = {'ID': 'audio-id', 'Size': result['audio']['bytes'], 'Hashes': {'MD5': result['audio']['md5']}}
        old_metadata = {'ID': 'old-metadata-id', 'Size': 999, 'Hashes': {'MD5': 'a' * 32}}
        def stat(remote): return old_metadata if remote.endswith('.info.json') else audio_proof
        helper = Mock(return_value={'status': 'old_metadata_preserved', 'original_drive_id_preserved': True})
        module = SimpleNamespace(preserve_conflicting_metadata=helper)
        with patch.object(obj.drive, 'copy_pair', side_effect=copy), patch.object(obj.drive, 'stat', side_effect=stat), \
                patch.dict(sys.modules, {'pipeline.native_metadata_snapshot': module}):
            done = obj.publish(item(), result)
        helper.assert_called_once()
        self.assertEqual(helper.call_args.kwargs['observed_audio'], audio_proof)
        self.assertEqual(helper.call_args.kwargs['observed_metadata'], old_metadata)
        self.assertEqual(len(calls), 2)
        self.assertTrue(done['metadata_lineage']['original_drive_id_preserved'])

    def test_conflicting_audio_never_reaches_metadata_preservation(self):
        obj, folder, result = self.prepared(); obj.drive.fail_copy = True
        helper = Mock()
        with patch.object(obj.drive, 'stat', return_value={'ID': 'wrong-audio', 'Size': 999, 'Hashes': {'MD5': 'a' * 32}}), \
                patch.dict(sys.modules, {'pipeline.native_metadata_snapshot': SimpleNamespace(preserve_conflicting_metadata=helper)}):
            with self.assertRaises(storage.IngestError): obj.publish(item(), result)
        helper.assert_not_called()
        self.assertTrue((folder / (ID + '.webm')).exists())

    def test_lost_metadata_move_ack_is_recovered_before_any_new_copy(self):
        obj, folder, result = self.prepared(); obj.drive.fail_copy = True
        with self.assertRaises(storage.IngestError): obj.publish(item(), result)
        record = worker.read(folder / 'canonical-record.json')
        storage.journal(self.root / 'sync/native_metadata_lineage_manifest.jsonl', {
            'video_id': ID, 'kind': 'native_metadata_snapshot_preservation', 'status': 'move_intent',
            'original': {'remote': record['metadata']['remote']},
            'new_canonical_expected': {'sha256': record['metadata']['sha256']}})
        obj.drive.fail_copy = False; obj.drive.calls.clear(); order = []
        def stat(remote):
            if remote.endswith('.info.json'): raise storage.IngestError('drive_not_found', 'moved')
            return {'ID': 'audio-id', 'Size': record['bytes'], 'Hashes': {'MD5': record['md5']}}
        def preserve(*args, **kwargs):
            self.assertIsNone(kwargs['observed_metadata']); self.assertEqual(obj.drive.calls, [])
            order.append('preserved')
            return {'status': 'old_metadata_preserved'}
        module = SimpleNamespace(preserve_conflicting_metadata=preserve)
        with patch.object(obj.drive, 'stat', side_effect=stat), patch.dict(sys.modules, {'pipeline.native_metadata_snapshot': module}):
            done = obj.publish(item(), result)
        self.assertEqual(order, ['preserved']); self.assertEqual(obj.drive.calls, ['copy', 'stat'])
        self.assertEqual(done['metadata_lineage']['status'], 'old_metadata_preserved')

    def test_changed_completed_audio_stops_before_upload(self):
        obj, folder, result = self.prepared()
        (folder / 'native-audio.webm').write_bytes(b'changed')
        with self.assertRaisesRegex(worker.Held, 'local_audio_changed'): obj.publish(item(), result)
        self.assertEqual(obj.drive.calls, [])

    def test_source_breaker_is_finite_and_has_no_automatic_retry(self):
        for value in ('source_403', 'source_429', 'bot_check', 'protection_failure'):
            self.assertEqual(batch.source_error({'diagnostics': {'error_class': value}}), value)
        self.assertIsNone(batch.source_error({'diagnostics': {'error_class': 'source_duration'}}))
        self.assertIsNone(batch.source_error({'diagnostics': {'error_class': 'unsafe raw message'}}))

    def test_v4_controls_preserve_v3_history_and_enforce_new_scope(self):
        sync = self.root / 'sync'; sync.mkdir()
        old_stop = sync / 'STOP_STOCK_WPC_BATCH_V3'; old_stop.write_bytes(b'unchanged v2 refusal')
        old_cooldown = sync / 'stock_wpc_batch_v3_source_cooldown.json'
        worker.write(old_cooldown, {'retry_not_before_epoch': time.time() + 86400})
        original = {p: p.read_bytes() for p in (old_stop, old_cooldown)}
        paths = worker.control_paths(self.root)
        self.assertEqual(paths['lease_path'].name, 'stock_wpc_batch_v4_lease.json')
        self.assertEqual(paths['batch_stop_path'].name, 'STOP_STOCK_WPC_BATCH_V4')
        self.assertEqual(paths['source_cooldown_path'].name, 'stock_wpc_batch_v4_source_cooldown.json')
        obj = batch.NativeBatch.__new__(batch.NativeBatch)
        obj.root = self.root; obj.lock = threading.RLock(); obj.source_stop = threading.Event()
        obj.stop_path = paths['batch_stop_path']; obj.cooldown_path = paths['source_cooldown_path']
        obj.last_guard = obj.last_inventory = time.monotonic()
        obj.lease = {'expires_at_epoch': time.time() + 60}
        obj.cap = batch.MANAGED; obj.external = obj.others = 0; obj.budget = None
        obj.observe_pending_failures = Mock(); obj.http_review = {'review_sha256':'a'*64,'covered_event_ids':[],'allowed_video_ids':[ID]}
        obj.policy_envelope = Mock(return_value={'state':batch.http_policy.empty_state()})
        with patch.object(batch.shutil, 'disk_usage', return_value=SimpleNamespace(free=10_000_000_000)):
            obj.guard(source=True, video_id=ID)
            obj.stop_path.write_bytes(b'new scope stopped')
            with self.assertRaisesRegex(worker.Held, 'batch_source_stopped'): obj.guard(source=True, video_id=ID)
            obj.stop_path.unlink()
            worker.write(obj.cooldown_path, {'retry_not_before_epoch': time.time() + 86400})
            with self.assertRaisesRegex(worker.Held, 'batch_source_cooldown'): obj.guard(source=True, video_id=ID)
        self.assertEqual({p: p.read_bytes() for p in original}, original)

    def test_unbound_wpc_media_refusals_are_counted_without_target_or_batch_refusal(self):
        state = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
        for phase in ('bootstrap', 'transfer'):
            state.phase = phase
            state.selected_metadata_saved = phase == 'transfer'
            for status in (403,):
                self.assertFalse(worker.record_browser_response(
                    state, 'https://r1.googlevideo.com/videoplayback?token=NEVER-EXPORT', status))
                state.guard()
                self.assertIsNone(state.refusal)
                self.assertIsNone(batch.source_error({'diagnostics': state.summary()}))
        saved = worker.read(self.root / 'progress.json')
        self.assertEqual(saved['browser_http_status_counts'], {'media:403': 2})
        self.assertEqual(saved['browser_unbound_media_failures'], {'403': 2})
        self.assertEqual(saved['browser_media_failure_binding'], 'unbound_provider_context')
        self.assertNotIn('NEVER-EXPORT', json.dumps(saved))
        self.assertIsNone(saved['http_failure'])
        self.assertEqual(saved['audio_bytes_written'], 0)

    def test_wpc_source_control_refusals_remain_fatal_without_claimed_video_binding(self):
        for url in ('https://www.youtube.com/', 'https://www.youtube.com/youtubei/v1/player'):
            for status in (403, 429):
                state = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
                self.assertTrue(worker.record_browser_response(state, url, status))
                self.assertEqual(batch.source_error({'diagnostics': state.summary()}), 'source_' + str(status))
                self.assertEqual(state.refusal['source_binding'], 'provider_source_control')
                self.assertFalse(state.refusal['requested_video_binding_verified'])
                with self.assertRaisesRegex(worker.Held, 'source_' + str(status)):
                    state.guard()

    def test_python_media_and_control_refusals_still_stop_after_incidental_browser_error(self):
        for url in ('https://r1.googlevideo.com/videoplayback?token=NEVER-EXPORT',
                    'https://www.youtube.com/youtubei/v1/player'):
            for status in (403, 429):
                state = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
                state.selected_metadata_saved = True
                worker.record_browser_response(state, 'https://r2.googlevideo.com/videoplayback', 403)
                worker.record_python_http_refusal(state, url, status)
                self.assertEqual(batch.source_error({'diagnostics': state.summary()}), 'source_' + str(status))
                self.assertEqual(state.refusal['transport_origin'], 'yt_dlp_python')
                with self.assertRaisesRegex(worker.Held, 'source_' + str(status)):
                    state.guard()
                self.assertNotIn('NEVER-EXPORT', json.dumps(worker.read(self.root / 'progress.json')))

    def test_exact_selected_media403_is_item_scoped_and_browser429_is_global(self):
        state = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
        url = 'https://r1.googlevideo.com/videoplayback?private=NEVER-EXPORT'
        state.phase = 'native_transfer'; state.selected_metadata_saved = True
        state.selected_asset_url = url; state.selected_summary = {'format_id': '140', 'filesize': 123}
        worker.record_python_http_refusal(state, url, 403, final_url=url, retry_after='120')
        self.assertEqual(state.http_failure['action'], 'item_quarantine')
        self.assertTrue(state.http_failure['binding_verified'])
        self.assertEqual(state.http_failure['retry_after_state'], 'delay_seconds')
        self.assertNotIn('NEVER-EXPORT', json.dumps(state.summary()))
        for final in (None, 'https://www.youtube.com/watch?v=' + ID, url + 'changed'):
            other = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
            other.phase = state.phase; other.selected_metadata_saved = True
            other.selected_asset_url = url; other.selected_summary = state.selected_summary
            worker.record_python_http_refusal(other, url, 403, final_url=final)
            self.assertEqual(other.http_failure['action'], 'global_stop')
        browser = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
        self.assertTrue(worker.record_browser_response(browser, url, 429))
        self.assertEqual(browser.http_failure['action'], 'global_stop')
        self.assertFalse(browser.http_failure['binding_verified'])

    def policy_coordinator(self):
        obj = batch.NativeBatch.__new__(batch.NativeBatch)
        obj.root = self.root; obj.jobs = self.root / 'jobs'; obj.jobs.mkdir(exist_ok=True)
        obj.lock = threading.RLock(); obj.source_stop = threading.Event(); obj.live_reservations = {}
        obj.plan_sha = '0' * 64; obj.last_guard = obj.last_inventory = time.monotonic()
        obj.lease = {'expires_at_epoch': time.time() + 60}; obj.budget = None
        obj.cap = batch.MANAGED; obj.external = obj.others = 0
        paths = worker.control_paths(self.root); paths['http_state_path'].parent.mkdir(exist_ok=True)
        obj.stop_path = paths['batch_stop_path']; obj.cooldown_path = paths['source_cooldown_path']
        obj.http_state_path = paths['http_state_path']
        seed = self.root / 'seed.json'; worker.write(seed, batch.http_policy.empty_state())
        obj.http_seed = {'path': str(seed), 'sha256': worker.digest(seed)}
        worker.write(obj.http_state_path, {'schema_version': 1, 'seed_sha256': obj.http_seed['sha256'], 'state': batch.http_policy.empty_state()})
        obj.http_review = {'review_sha256': 'a' * 64, 'covered_event_ids': [],
                           'allowed_video_ids': [c * 11 for c in 'abcde']}
        return obj

    def failure(self, obj, ident, status=403):
        folder = obj.jobs / ident; folder.mkdir(exist_ok=True)
        worker.write(folder / 'attempt.json', {'video_id': ident, 'attempts_spent': 1})
        url = 'https://r1.googlevideo.com/videoplayback?private=' + ident
        event = batch.http_policy.classify_http_failure(status, url, url, url, 'native_transfer',
            ident, {'format_id': '140'}, selection_validated=True)
        return {'video_id': ident, 'diagnostics': {'error_class': 'source_' + str(status), 'http_failure': event,
                                                  'http_failure_at_epoch': time.time()}}

    def test_item_quarantine_is_durable_deduplicated_and_does_not_stop_peer(self):
        obj = self.policy_coordinator(); failure = self.failure(obj, ID)
        obj.refuse(failure); first = obj.http_state_path.read_bytes()
        obj.refuse(failure)
        self.assertEqual(first, obj.http_state_path.read_bytes())
        self.assertFalse(obj.source_stop.is_set()); self.assertFalse(obj.stop_path.exists())
        with self.assertRaisesRegex(worker.Held, 'item_quarantined'): obj.guard(source=True, video_id=ID)
        obj.guard(source=True, video_id='b' * 11)
        self.assertEqual(len(obj.policy_envelope()['state']['events']), 1)

    def test_worker_global_escalation_after_item403_is_preserved_and_durable(self):
        obj = self.policy_coordinator(); self.failure(obj, ID)
        state = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
        url = 'https://r1.googlevideo.com/videoplayback?private=NEVER-EXPORT'
        state.phase = 'native_transfer'; state.selected_metadata_saved = True; state.selected_asset_url = url
        state.selected_summary = {'format_id': '140'}
        worker.record_python_http_refusal(state, url, 403, final_url=url)
        first = dict(state.http_failure); first_time = state.http_failure_at_epoch
        obj.refuse({'video_id': ID, 'diagnostics': state.summary()})
        self.assertFalse(obj.source_stop.is_set())
        self.assertTrue(worker.record_browser_response(state, url, 429))
        self.assertEqual(state.http_failure, first); self.assertEqual(state.http_failure_at_epoch, first_time)
        self.assertEqual(state.http_escalation['action'], 'global_stop')
        obj.refuse({'video_id': ID, 'diagnostics': state.summary()})
        self.assertTrue(obj.source_stop.is_set())
        self.assertEqual(len(obj.policy_envelope()['state']['events']), 2)
        self.assertNotIn('NEVER-EXPORT', obj.http_state_path.read_text())

    def test_bot_failure_cannot_be_masked_by_an_earlier_item403(self):
        obj = self.policy_coordinator(); failure = self.failure(obj, ID)
        failure['diagnostics'].update(error_class='bot_check', global_failure_code='bot_check',
                                      global_failure_at_epoch=time.time())
        obj.refuse(failure)
        self.assertTrue(obj.source_stop.is_set())
        self.assertEqual({r['event']['code'] for r in obj.policy_envelope()['state']['events'].values()}, {'source_403','bot_check'})

    def test_replayed_progress_preserves_capture_time_and_unknown_time_holds(self):
        obj = self.policy_coordinator(); failure = self.failure(obj, ID)
        captured = time.time() - 120; failure['diagnostics']['http_failure_at_epoch'] = captured
        obj.refuse(failure); obj.refuse(failure)
        self.assertEqual(next(iter(obj.policy_envelope()['state']['events'].values()))['at_epoch'], captured)
        other = self.failure(obj, 'b' * 11); other['diagnostics'].pop('http_failure_at_epoch')
        obj.refuse(other)
        self.assertTrue(obj.source_stop.is_set()); self.assertTrue(worker.read(obj.cooldown_path)['timestamp_unproven'])
        self.assertEqual(len(obj.policy_envelope()['state']['events']), 1)

    def test_concurrent_refusals_are_not_lost_and_third_observation_blocks_dispatch(self):
        obj = self.policy_coordinator()
        first, second = [self.failure(obj, c * 11) for c in 'ab']
        with batch.ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(obj.refuse, [first, second]))
        self.assertEqual(len(obj.policy_envelope()['state']['events']), 2)
        self.assertFalse(obj.stop_path.exists())
        third = self.failure(obj, 'c' * 11); folder = obj.jobs / ('c' * 11)
        worker.write(folder / 'progress.json', third['diagnostics'])
        obj.live_reservations['c' * 11] = {'folder': folder}
        with self.assertRaisesRegex(worker.Held, 'batch_source_stopped'):
            obj.guard(source=True, video_id='d' * 11)
        self.assertTrue(obj.stop_path.exists()); self.assertFalse((obj.jobs / ('d' * 11)).exists())
        state = obj.policy_envelope()['state']
        self.assertEqual(len(state['events']), 3)
        self.assertTrue(batch.http_policy.status(state, time.time() + 10000)['global_stop'])
        self.assertIsNotNone(worker.read(obj.cooldown_path)['circuit_break'])

    def test_rate_limit_state_survives_new_coordinator_and_no_history_reset(self):
        obj = self.policy_coordinator(); obj.refuse(self.failure(obj, ID, 429))
        state = obj.policy_envelope()['state']
        self.assertTrue(batch.http_policy.status(state, time.time() + 10000)['global_stop'])
        # A fresh Event object cannot erase the persisted global refusal.
        obj.source_stop = threading.Event()
        with self.assertRaisesRegex(worker.Held, 'batch_source_stopped'):
            obj.guard(source=True, video_id='b' * 11)
        self.assertEqual(obj.policy_envelope()['state'], state)

    def test_active_profile_growth_cannot_double_count_reserved_slots(self):
        spool = self.root / 'spool'; folders = [spool / 'a', spool / 'b']
        for folder in folders: folder.mkdir(parents=True)
        for folder in folders: (folder / 'profile').write_bytes(b'X' * 5)
        budget = batch.SlotBudget(self.root, 1000, 224, 0, reserve=1)
        budget.active = {str(i): {'path': folder / 'missing.part', 'bytes': 224} for i, folder in enumerate(folders)}
        first = batch.capacity_snapshot(self.root, spool, folders)
        for folder in folders: (folder / 'profile').write_bytes(b'X' * 25)
        second = batch.capacity_snapshot(self.root, spool, folders)
        # The old cross-time sum falsely reported488 for450 capacity.
        self.assertGreater(2 * (224 - 5) + 50, 450)
        self.assertEqual(first, second)
        self.assertEqual(second['inactive_spool_bytes'] + budget._outstanding(), 448)
        (self.root / 'unrelated').write_bytes(b'owned other bytes')
        snapshot = batch.capacity_snapshot(self.root, spool, folders)
        self.assertEqual(snapshot['inactive_private_bytes'], len(b'owned other bytes'))
        self.assertEqual(snapshot['inactive_spool_bytes'], 0)

    def test_retained_media_respects_explicit_cap_and_six_gb_allows_two_slots(self):
        spool = self.root / 'spool'; active = spool / 'active'; active.mkdir(parents=True)
        retained = spool / 'retained.part'
        with retained.open('wb') as handle: handle.truncate(60_000_000)
        snapshot = batch.capacity_snapshot(self.root, spool, [active])
        slot = 2_000_000_000 + batch.HEADROOM
        budget = batch.SlotBudget(self.root, batch.MANAGED, 2_000_000_000, 0)
        budget.active = {'active': {'path': active / 'audio.part', 'bytes': slot}}
        projected = snapshot['inactive_spool_bytes'] + budget._outstanding() + slot
        self.assertGreater(projected, 4_500_000_000)
        self.assertLess(projected, batch.MAX_SPOOL)
        self.assertEqual(batch.MAX_SPOOL, 6_000_000_000)
        budget.release('active')
        self.assertLess(snapshot['inactive_spool_bytes'] + budget._outstanding() + slot, 4_500_000_000)
        self.assertTrue(retained.exists())

    def test_child_lease_revocation_and_batch_stop_prevent_next_write(self):
        lease = self.root / 'lease.json'; stop = self.root / 'batch-stop'
        worker.write(lease, {'state': 'active', 'lease_id': 'fixture', 'expires_at_epoch': time.time() + 60})
        state = worker.State({'preserved_controls': [], 'lease_path': str(lease), 'lease_id': 'fixture',
            'batch_stop_path': str(stop)}, self.root, time.time() + 60)
        state.guard()
        worker.write(lease, {'state': 'released', 'lease_id': 'fixture', 'expires_at_epoch': time.time() + 60})
        state.last_check = 0
        with self.assertRaisesRegex(worker.Held, 'lease_revoked'): state.guard()
        stop.touch(); state.last_check = 0
        with self.assertRaisesRegex(worker.Held, 'batch_source_stop'): state.guard()
        state.expires = time.time() - 1
        with self.assertRaisesRegex(worker.Held, 'deadline'): state.guard()

    def test_first_refusal_is_durable_once_and_preserves_old_control(self):
        obj = batch.NativeBatch.__new__(batch.NativeBatch)
        obj.lock = threading.RLock(); obj.source_stop = threading.Event(); obj.plan_sha = '0' * 64
        obj.cooldown_path = self.root / 'new-cooldown.json'; obj.stop_path = self.root / 'new-stop'
        old = self.root / 'old-cooldown.json'; old.write_bytes(b'untouched old history')
        obj.refuse({'video_id': ID, 'diagnostics': {'error_class': 'source_403', 'source_refusal': {'endpoint': 'source_control', 'status': 403}}})
        first = obj.cooldown_path.read_bytes()
        obj.refuse({'video_id': ID, 'diagnostics': {'error_class': 'source_429'}})
        self.assertEqual(obj.cooldown_path.read_bytes(), first)
        self.assertEqual(old.read_bytes(), b'untouched old history')
        self.assertTrue(obj.source_stop.is_set()); self.assertTrue(obj.stop_path.exists())

    def test_verification_crash_with_one_deleted_file_recovers_without_copy(self):
        obj, folder, result = self.prepared()
        real_remove = storage.remove_local
        def interruption(path, *args, **kwargs):
            if path.name == ID + '.info.json': raise OSError('fixture deletion interruption')
            return real_remove(path, *args, **kwargs)
        with patch.object(storage, 'remove_local', side_effect=interruption), self.assertRaises(OSError):
            obj.publish(item(), result)
        self.assertFalse((folder / (ID + '.webm')).exists())
        self.assertEqual(storage.load_state(obj.state_path)[ID]['status'], 'verified')
        done = obj.publish(item(), result)
        self.assertTrue(storage.receipt_complete(done, item(), obj.s['remote']))
        self.assertEqual(obj.drive.calls.count('copy'), 1)

    def test_wrong_resumed_checkpoint_cannot_move_upload_or_delete(self):
        obj, folder, result = self.prepared(); obj.drive.fail_copy = True
        with self.assertRaises(storage.IngestError): obj.publish(item(), result)
        record_path = folder / 'canonical-record.json'; original = worker.read(record_path)
        before = list(obj.drive.calls)
        mutations = [dict(original, video_id='bbbbbbbbbbb'),
                     dict(original, native_batch_plan_sha256='f' * 64),
                     dict(original, path='unrelated-owned-input.webm'),
                     dict(original, remote='fixture:archive/other/aaaaaaaaaaa.webm'),
                     dict(original, metadata={**original['metadata'], 'path': 'unrelated.info.json'})]
        for value in mutations:
            worker.write(record_path, value)
            with self.assertRaises(worker.Held): obj.publish(item(), result)
            self.assertEqual(obj.drive.calls, before)
            self.assertTrue((folder / (ID + '.webm')).exists())
            self.assertTrue((folder / (ID + '.info.json')).exists())

    def test_fake_child_is_attached_before_go_and_cleaned_before_return(self):
        obj = batch.NativeBatch.__new__(batch.NativeBatch)
        obj.lock = threading.RLock(); obj.source_stop = threading.Event(); obj.plan_sha = '0' * 64
        obj.dispatch_paused = threading.Event()
        obj.root = self.root; obj.spool = self.root; obj.jobs = self.root / 'jobs'; obj.guard = Mock(); obj.live_reservations = {}
        obj.s = {'max_asset_bytes': 1000, 'lease_id': 'fixture', 'python_executable': 'unused', 'job_wall_seconds': 600, 'spool_cap_bytes': 500_000_000}
        obj.settings_path = self.root / 'settings'; obj.lease_path = self.root / 'lease'; obj.stop_path = self.root / 'batch-stop'
        obj.budget = Mock(); obj.budget._outstanding.return_value = 0; events = []; folder = obj.jobs / ID
        obj.capacity = {'inactive_spool_bytes': 0}
        class Process:
            returncode = 0
            def poll(self): return 0
            def wait(self, timeout): events.append('wait'); return 0
        class Job:
            def attach(self, proc):
                self_case.assertFalse((folder / 'GO').exists()); events.append('attach')
            def stop_and_verify(self): events.append('stop'); return True
            def close(self): events.append('close')
        def launch(*args, **kwargs):
            events.append('launch'); self.assertFalse((folder / 'GO').exists())
            (folder / 'profile-temp').mkdir(); (folder / 'profile-temp/cache').write_bytes(b'fixture')
            worker.write(folder / 'result.json', {'status': 'held', 'video_id': ID, 'diagnostics': {'error_class': 'fixture'}})
            return Process()
        self_case = self
        with patch.object(batch, 'WINDOWS', True), patch.object(batch, 'OwnedJob', Job), \
                patch.object(batch.subprocess, 'CREATE_NO_WINDOW', 0, create=True), \
                patch.object(batch.subprocess, 'Popen', side_effect=launch):
            self.assertEqual(obj.execute_child(item())['status'], 'held')
        self.assertEqual(events, ['launch', 'attach', 'stop', 'close', 'wait'])
        self.assertFalse((folder / 'profile-temp').exists()); obj.budget.release.assert_called_once_with(ID)
        audit = worker.read(folder / 'parent-audit.json')
        self.assertTrue(audit['owned_processes_gone']); self.assertTrue(audit['profile_cleaned'])

    def test_profile_cleanup_retries_only_filesystem_after_owned_processes_gone(self):
        profile = self.root / 'profile-temp'; profile.mkdir(); marker = profile / 'lock'; marker.touch()
        failure = PermissionError('private path and message must not escape'); failure.winerror = 32
        calls = []
        def remove(path):
            calls.append(path)
            if len(calls) == 1: raise failure
            marker.unlink(); path.rmdir()
        sleep = Mock()
        outcome = batch.cleanup_profile(profile, self.root, True, remove=remove, sleep=sleep)
        self.assertTrue(outcome['cleaned']); self.assertEqual(outcome['attempts'], 2)
        self.assertEqual(outcome['failures'], [{'exception_class': 'PermissionError', 'winerror': 32}])
        self.assertNotIn('private path', json.dumps(outcome)); sleep.assert_called_once_with(.25)
        profile.mkdir(); remove = Mock()
        with self.assertRaisesRegex(worker.Held, 'cleanup_path'):
            batch.cleanup_profile(profile, self.root, False, remove=remove)
        remove.assert_not_called()

    def test_locked_profile_is_retained_after_three_local_attempts(self):
        profile = self.root / 'profile-temp'; profile.mkdir()
        remove = Mock(side_effect=PermissionError('fixture')); sleep = Mock()
        outcome = batch.cleanup_profile(profile, self.root, True, remove=remove, sleep=sleep)
        self.assertFalse(outcome['cleaned']); self.assertTrue(outcome['retained_for_owner_cleanup'])
        self.assertEqual(remove.call_count, 3); self.assertEqual(sleep.call_count, 2)
        self.assertTrue(profile.exists())

    def test_format_inventory_is_bounded_and_excludes_transport_material(self):
        state = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
        fmt = {'format_id': '140', 'url': 'https://media.invalid/?sig=secret', 'http_headers': {'cookie': 'secret'},
               'protocol': 'https', 'acodec': 'mp4a.40.2', 'vcodec': 'none', 'ext': 'm4a', 'language': 'en-US',
               'language_preference': 10, 'format_note': 'English original'}
        with patch.object(worker, 'TARGET', ID): worker.save_format_inventory(state, {'id': ID, 'formats': [fmt] * 513})
        value = worker.read(self.root / 'format-inventory.json')
        self.assertEqual(value['format_count'], 513); self.assertEqual(value['retained_format_count'], 512)
        self.assertTrue(value['truncated']); self.assertEqual(value['original_https_audio_candidates'], 512)
        raw = json.dumps(value)
        for secret in ('secret', 'http_headers', 'https://', 'cookie'): self.assertNotIn(secret, raw)

    def test_error_reason_is_anchored_and_does_not_guess_http_refusal(self):
        self.assertEqual(worker.diagnostic_reason('ERROR: [youtube] aaaaaaaaaaa: Requested format is not available. Use --list-formats'), 'format_unavailable')
        self.assertEqual(worker.diagnostic_reason('No video formats found!'), 'no_formats')
        self.assertEqual(worker.diagnostic_reason("Sign in to confirm you're not a bot"), 'bot_check')
        self.assertIsNone(worker.diagnostic_reason('A video title says Requested format is not available'))
        self.assertIsNone(worker.diagnostic_reason('HTTP Error 403 with private URL'))

    def test_wrapped_os_error_diagnostics_retain_codes_without_raw_messages(self):
        class UnavailableVideoError(Exception): pass
        try:
            try:
                error = PermissionError(13, 'https://media.invalid/?secret=NEVER-EXPORT')
                error.winerror = 32
                raise error
            except OSError as cause:
                raise UnavailableVideoError('private source details NEVER-EXPORT') from cause
        except Exception as error:
            proof = worker.safe_exception_chain(error)
        self.assertEqual([n['exception_class'] for n in proof['nodes']], ['UnavailableVideoError', 'PermissionError'])
        self.assertEqual(proof['nodes'][1]['errno'], 13); self.assertEqual(proof['nodes'][1]['winerror'], 32)
        self.assertNotIn('NEVER-EXPORT', json.dumps(proof)); self.assertNotIn(str(self.root), json.dumps(proof))
        self.assertTrue(proof['nodes'][0]['frames'])

    def test_download_error_exc_info_and_cyclic_context_are_bounded(self):
        class DownloadError(Exception): pass
        held = worker.Held('python_body_cap'); outer = DownloadError('NEVER-EXPORT')
        outer.exc_info = (type(held), held, None); held.__context__ = outer
        proof = worker.safe_exception_chain(outer)
        self.assertEqual(len(proof['nodes']), 2)
        self.assertEqual(proof['nodes'][1]['link'], 'exc_info')
        self.assertEqual(proof['nodes'][1]['code'], 'python_body_cap')
        self.assertNotIn('NEVER-EXPORT', json.dumps(proof))

    @unittest.skipUnless(importlib.util.find_spec('yt_dlp'), 'optional installed yt-dlp fixture')
    def test_installed_legacy_selector_accepts_numeric_negative_preference(self):
        from yt_dlp import YoutubeDL
        class Offline(YoutubeDL):
            def urlopen(self, *args, **kwargs): raise AssertionError('source forbidden')
        def fmt(preference):
            return {'format_id': '140', 'url': 'https://media.invalid/fixture', 'protocol': 'https',
                    'ext': 'm4a', 'acodec': 'mp4a.40.2', 'vcodec': 'none',
                    'language_preference': preference, 'language': 'en'}
        with Offline({'quiet': True, 'format': worker.LEGACY_FORMAT_SELECTOR}, auto_init=False) as ydl:
            self.assertEqual([f['format_id'] for f in ydl._select_formats([fmt(-1)], ydl.format_selector)], ['140'])
            drc = dict(fmt(-1), format_id='140-drc', quality=100)
            self.assertEqual([f['format_id'] for f in ydl._select_formats([fmt(-1), drc], ydl.format_selector)], ['140'])
            self.assertEqual(ydl._select_formats([drc], ydl.format_selector), [])
            for preference in (0, 5, 10, None):
                self.assertEqual(ydl._select_formats([fmt(preference)], ydl.format_selector), [])

    @unittest.skipUnless(importlib.util.find_spec('yt_dlp'), 'optional installed yt-dlp fixture')
    def test_installed_selector_failure_retains_inventory_before_selection(self):
        from yt_dlp import YoutubeDL
        from yt_dlp.extractor.common import InfoExtractor
        from yt_dlp.utils import DownloadError
        state = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
        class Log:
            def debug(self, *_): pass
            def warning(self, *_): pass
            def error(self, message): state.diagnostic_reason = worker.diagnostic_reason(message)
        class Offline(YoutubeDL):
            def process_video_result(self, info_dict, download=True):
                worker.save_format_inventory(state, info_dict)
                return super().process_video_result(info_dict, download=download)
            def urlopen(self, *args, **kwargs): raise AssertionError('source forbidden')
        info = {'id': ID, 'title': 'Invented fixture', 'duration': 10, 'formats': [
            {'format_id': '140', 'url': 'https://media.invalid/fixture', 'protocol': 'https', 'ext': 'm4a',
             'acodec': 'mp4a.40.2', 'vcodec': 'none', 'language_preference': -1}]}
        class FixtureIE(InfoExtractor):
            IE_NAME = 'youtube'
            _VALID_URL = r'offlinefixture:(?P<id>[a-z]{11})'
            def _real_extract(self, url): return info
        with patch.object(worker, 'TARGET', ID), Offline({'logger': Log(), 'quiet': True,
                'format': 'bestaudio[language_preference=10]'}, auto_init=False) as ydl:
            ydl.add_info_extractor(FixtureIE())
            with self.assertRaises(DownloadError): ydl.extract_info('offlinefixture:' + ID)
        self.assertTrue(state.format_inventory_saved)
        self.assertEqual(worker.read(self.root / 'format-inventory.json')['original_https_audio_candidates'], 0)
        self.assertEqual(state.diagnostic_reason, 'format_unavailable')


if __name__ == '__main__': unittest.main()
