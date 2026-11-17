"""Offline hardlink crash recovery, capacity, proof and lock-order regressions."""
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_asr_handoff as handoff
import drive_ingest as storage
import gpu_asr_queue as queue

REMOTE = 'testdrive:Audio'


def proof(data):
    return {'bytes': len(data), 'md5': hashlib.md5(data).hexdigest(), 'sha256': hashlib.sha256(data).hexdigest()}


def observed(record):
    return {'ID': record['drive_id'], 'Size': record['bytes'], 'Hashes': {'MD5': record['md5']}, 'IsDir': False}


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.settings = handoff.Settings(self.root, 'fixture', 'allocation-fixture', REMOTE)
        self.authorize()

    def authorize(self):
        s = self.settings
        queue.atomic(s.path('sync/native_asr_handoff_lease.json'), {
            'schema_version': 1, 'profile': handoff.PROFILE, 'state': 'active', 'owner': s.owner,
            'lease_id': s.lease_id, 'remote': s.remote, 'cap_bytes': s.cap_bytes, 'max_pairs': s.max_pairs,
            'retain_policy': s.retain_policy,
            'expires_at_epoch': (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).timestamp()})
        queue.atomic(s.path('sync/analysis_resource_plan.json'), {
            'collector_dispatch_allowed': False, 'accounting_cap_bytes': 16_000_000_000,
            'reservations': [{'state': 'active', 'owner': s.owner, 'lease_id': s.lease_id, 'max_bytes': s.cap_bytes}]})

    def source(self, index=0, *, language='en', inferred=False, size=100):
        ident = f'VID{index:08d}'
        folder = self.root / 'stock_wpc_batch/jobs/fixture' / ident
        folder.mkdir(parents=True)
        audio = folder / (ident + '.webm')
        metadata = folder / (ident + '.info.json')
        audio.write_bytes(bytes([index + 1]) * size)
        queue.atomic(metadata, {'source': {'video_id': ident}, 'languages': {'audio': language},
            'archive_audio': {'video_id': ident, **proof(audio.read_bytes())},
            'native_selection': {'format': {'duration': 63}, 'original_audio_evidence': {
                'original_explicitly_verified': not inferred, 'origin_inferred': inferred,
                'original_label_present': not inferred, 'language_preference': -1 if inferred else 10,
                'language': language, 'source_language': language}}})
        row = {'video_id': ident, 'channel_dir': 'fixture-channel', 'tab': 'videos'}
        record = dict(row, status='prepared', path=audio.relative_to(self.root).as_posix(),
            remote=storage.remote_path(REMOTE, row, 'webm'), **proof(audio.read_bytes()))
        record['metadata'] = dict(path=metadata.relative_to(self.root).as_posix(),
            remote=storage.remote_path(REMOTE, row, 'info.json'), **proof(metadata.read_bytes()))
        remote = {k: {'ID': ident + '-' + k, 'Size': p['bytes'], 'Hashes': {'MD5': p['md5']}, 'IsDir': False}
                  for k, p in (('audio', record), ('metadata', record['metadata']))}
        return record, remote

    def retain(self, record, remote, **kwargs):
        return handoff.retain_before_cleanup(self.settings, record, remote, **kwargs)

    def archived(self, record, remote, *, remove=True):
        done = json.loads(json.dumps(record))
        done.update(status='deleted', drive_id=remote['audio']['ID'])
        done['metadata']['drive_id'] = remote['metadata']['ID']
        if remove:
            for p in (record, record['metadata']): self.settings.path(p['path']).unlink()
        storage.journal(self.settings.path('sync/drive_ingest_manifest.jsonl'), done)
        return done

    def ready(self):
        record, remote = self.source()
        state = self.retain(record, remote)
        done = self.archived(record, remote)
        return handoff.finalize_after_cleanup(self.settings, state['handoff_id'], done)

    def result(self, state):
        admission = handoff.read(Path(state['admission_path']))
        job = admission['job']
        run = 'asr-' + '1' * 24
        record = {'status': 'verified', 'artifact_kind': 'asr_bundle', 'video_id': state['video_id'],
            'run_id': run, 'job_id': job['job_id'], 'source_lease_id': state['source_lease_id'],
            'source_audio_sha256': job['audio']['sha256'], 'source_audio_drive_id': job['audio']['drive_id'],
            'source_metadata': job['metadata'], 'drive_id': 'result-object', **proof(b'result'),
            'remote': f"{job['audio']['remote'].rpartition('/')[0]}/{state['video_id']}/ASR/{run}/{run}.zip"}
        storage.journal(self.settings.path('sync/asr_manifest.jsonl'), record)
        terminal = {'source_lease_id': state['source_lease_id'], 'run_id': run,
                    'process_exited': True, 'consumers_active': False}
        return record, terminal

    def assert_kind(self, kind, function, *args, **kwargs):
        with self.assertRaises(storage.IngestError) as error:
            function(*args, **kwargs)
        self.assertEqual(kind, error.exception.kind)

    def test_both_hooks_and_retirement_work_while_collector_lock_is_held(self):
        with storage.exclusive_lock(self.root):
            state = self.ready()
            self.assertEqual('ready', state['status'])
            result, terminal = self.result(state)
            before = self.settings.path('sync/drive_ingest_manifest.jsonl').read_bytes()
            released = handoff.retire_after_result(self.settings, state['handoff_id'], result, observed(result), consumer_terminal=terminal)
        self.assertEqual('released', released['status'])
        self.assertEqual(before, self.settings.path('sync/drive_ingest_manifest.jsonl').read_bytes())
        self.assertFalse(any(self.settings.path(x['path']).exists() for x in state['links'].values()))
        self.assertFalse(self.settings.path('sync/gpu_lease.json').exists())

    def test_partial_link_crash_is_reserved_and_recovers_without_copy(self):
        self.settings = handoff.Settings(self.root, 'fixture', 'allocation-fixture', REMOTE, max_pairs=1)
        self.authorize()
        record, remote = self.source()
        original = os.link
        calls = []
        def fail_second(source, target):
            calls.append(target)
            if len(calls) == 2: raise OSError('injected crash')
            original(source, target)
        with mock.patch.object(handoff.os, 'link', side_effect=fail_second):
            with self.assertRaises(OSError): self.retain(record, remote)
        other = self.source(1)
        self.assert_kind('handoff_capacity', self.retain, *other)
        state = self.retain(record, remote)
        again = self.retain(record, remote)
        self.assertEqual(state, again)
        self.assertFalse(handoff.state_path(self.settings, state['handoff_id']).with_name('ready.json').exists())
        for item in state['links'].values():
            self.assertTrue(os.path.samefile(self.settings.path(item['source_path']), self.settings.path(item['path'])))

    def test_canonical_receipt_must_be_durable_before_ready(self):
        record, remote = self.source()
        state = self.retain(record, remote)
        done = dict(record, status='deleted', drive_id='fake')
        self.assert_kind('handoff_canonical_not_durable', handoff.finalize_after_cleanup, self.settings, state['handoff_id'], done)
        done = self.archived(record, remote)
        first = handoff.finalize_after_cleanup(self.settings, state['handoff_id'], done)
        self.assertEqual(first, handoff.finalize_after_cleanup(self.settings, state['handoff_id'], done))
        self.assertTrue(handoff.read(handoff.state_path(self.settings, state['handoff_id']).with_name('ready.json'))['admissions'])

    def test_crash_before_ready_marker_can_be_reconciled_without_reclaiming_consumer(self):
        record, remote = self.source()
        state = self.retain(record, remote)
        done = self.archived(record, remote)
        with mock.patch.object(handoff, 'publish_ready', side_effect=OSError('injected crash')):
            with self.assertRaises(OSError): handoff.finalize_after_cleanup(self.settings, state['handoff_id'], done)
        final = handoff.finalize_after_cleanup(self.settings, state['handoff_id'], done)
        marker = handoff.state_path(self.settings, state['handoff_id']).with_name('ready.json')
        self.assertTrue(handoff.read(marker)['admissions'])
        lease_path = self.settings.path(final['source_lease'])
        lease = handoff.read(lease_path); lease.update(phase='processing', consumer_owner='fixture-gpu')
        queue.atomic(lease_path, lease)
        handoff.finalize_after_cleanup(self.settings, state['handoff_id'], done)
        self.assertEqual('processing', handoff.read(lease_path)['phase'])
        self.assertEqual([], handoff.read(marker)['admissions'])

    def test_crash_after_first_retirement_unlink_recovers_only_remaining_owned_link(self):
        state = self.ready()
        result, terminal = self.result(state)
        original = Path.unlink
        calls = []
        def fail_second(path, **kwargs):
            calls.append(path)
            if len(calls) == 2: raise OSError('injected crash')
            return original(path, **kwargs)
        with mock.patch.object(Path, 'unlink', fail_second):
            with self.assertRaises(OSError):
                handoff.retire_after_result(self.settings, state['handoff_id'], result, observed(result), consumer_terminal=terminal)
        final = handoff.retire_after_result(self.settings, state['handoff_id'], result, observed(result), consumer_terminal=terminal)
        self.assertEqual('released', final['status'])
        self.assertFalse(any(self.settings.path(x['path']).exists() for x in final['links'].values()))

    def test_generated_english_admission_passes_existing_worker_source_validation(self):
        import gpu_asr
        state = self.ready()
        settings = gpu_asr.Settings(self.root, self.root / 'models', self.root / 'model-receipt.json',
                                    'inactive-fixture-gpu', 'fixture', [self.root])
        admission, objects, _ = gpu_asr.validate_admission(settings, Path(state['admission_path']))
        self.assertEqual({'audio', 'metadata'}, set(objects))
        self.assertEqual('en', admission['language']['code'])

    def test_whole_pair_capacity_keeps_originals_and_does_not_create_second_intent(self):
        self.settings = handoff.Settings(self.root, 'fixture', 'allocation-fixture', REMOTE,
                                         cap_bytes=handoff.CONTROL_RESERVE + 5000)
        self.authorize()
        self.retain(*self.source(size=3000))
        record, remote = self.source(1, size=3000)
        self.assert_kind('handoff_capacity', self.retain, record, remote)
        self.assertTrue(self.settings.path(record['path']).exists())
        self.assertEqual(1, len(list(self.settings.path('asr/jobs/native-handoff').glob('*/handoff.json'))))

    def test_mutated_bytes_refuse_finalize_and_retire_without_deletion(self):
        record, remote = self.source()
        state = self.retain(record, remote)
        self.settings.path(state['links']['audio']['path']).write_bytes(b'changed')
        done = self.archived(record, remote)
        self.assert_kind('handoff_input_changed', handoff.finalize_after_cleanup, self.settings, state['handoff_id'], done)
        self.assertTrue(self.settings.path(state['links']['audio']['path']).exists())

    def test_wrong_drive_identity_and_live_consumer_cannot_retire(self):
        state = self.ready()
        result, terminal = self.result(state)
        self.assert_kind('handoff_consumer_active', handoff.retire_after_result, self.settings, state['handoff_id'], result,
                         observed(result), consumer_terminal=dict(terminal, consumers_active=True))
        self.assert_kind('handoff_result_drive_identity', handoff.retire_after_result, self.settings, state['handoff_id'], result,
                         dict(observed(result), ID='wrong'), consumer_terminal=terminal)
        self.settings.path(state['links']['metadata']['path']).write_bytes(b'changed')
        self.assert_kind('handoff_input_changed', handoff.retire_after_result, self.settings, state['handoff_id'], result,
                         observed(result), consumer_terminal=terminal)

    def test_inferred_english_is_disabled_large_v3_proposal(self):
        record, remote = self.source(language='en', inferred=True)
        state = self.retain(record, remote)
        state = handoff.finalize_after_cleanup(self.settings, state['handoff_id'], self.archived(record, remote))
        self.assertEqual('deferred_language_review', state['status'])
        self.assertFalse(state['links'])
        proposal = handoff.read(Path(state['admission_path']))
        self.assertFalse(proposal['text_generation_allowed'])
        self.assertFalse(proposal['language_evidence']['explicit_original_english'])
        self.assertEqual('Systran/faster-whisper-large-v3', proposal['desired_model']['repository'])
        self.assertEqual([], handoff.read(handoff.state_path(self.settings, state['handoff_id']).with_name('ready.json'))['admissions'])

    def test_metadata_for_another_audio_version_cannot_be_staged(self):
        record, remote = self.source()
        path = self.settings.path(record['metadata']['path'])
        metadata = handoff.read(path); metadata['archive_audio']['sha256'] = '0' * 64
        queue.atomic(path, metadata)
        record['metadata'].update(proof(path.read_bytes()))
        remote['metadata'].update(Size=record['metadata']['bytes'], Hashes={'MD5': record['metadata']['md5']})
        self.assert_kind('handoff_metadata_audio_binding', self.retain, record, remote)
        self.assertFalse(self.settings.path('asr/input').exists())

    def caption(self, record, *, usable=True, wrong_video=False):
        ident = record['video_id']
        track_id = 'automatic.en'
        detail = {'provider': 'youtube', 'video_id': 'BAD00000000' if wrong_video else ident,
                  'track_id': track_id, 'policy': storage.CAPTION_POLICY, 'language': 'en', 'machine_translated': False}
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr('provenance.json', json.dumps(detail))
            archive.writestr('segments.json', json.dumps({'segments': [{'start': 0, 'end': 1, 'text': 'Fixture'}] if usable else []}))
            archive.writestr('transcript.txt', 'Fixture' if usable else '')
        data = stream.getvalue()
        path = self.settings.path('asr/jobs/cached-caption.zip'); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        track = {'track_id': track_id, 'status': 'deleted', 'language': 'en', 'machine_translated': False,
                 'bundle': dict(remote=storage.remote_path(REMOTE, record, f'captions.{track_id}.zip'), drive_id='caption', **proof(data))}
        cap = {'video_id': ident, 'status': 'deleted', 'policy': storage.CAPTION_POLICY, 'unresolved': [], 'tracks': [track]}
        storage.journal(self.settings.path('sync/drive_caption_manifest.jsonl'), cap)
        return {track_id: str(path)}

    def test_usable_bound_captions_take_priority_but_empty_or_wrong_video_do_not(self):
        for index, options, expected in [(0, {}, 'caption_satisfied'), (1, {'usable': False}, 'ready'),
                                        (2, {'wrong_video': True}, 'ready')]:
            record, remote = self.source(index)
            state = self.retain(record, remote, caption_bundle_paths=self.caption(record, **options))
            final = handoff.finalize_after_cleanup(self.settings, state['handoff_id'], self.archived(record, remote))
            self.assertEqual(expected, final['status'])
            self.assertEqual(expected != 'caption_satisfied', bool(final['links']))

    def test_deferred_languages_do_not_consume_the_single_staging_slot(self):
        self.settings = handoff.Settings(self.root, 'fixture', 'allocation-fixture', REMOTE, max_pairs=1)
        self.authorize()
        for index, language, inferred in [(0, 'en', True), (1, 'pt-BR', False)]:
            record, remote = self.source(index, language=language, inferred=inferred)
            state = self.retain(record, remote)
            self.assertFalse(state['links'])
            final = handoff.finalize_after_cleanup(self.settings, state['handoff_id'], self.archived(record, remote))
            self.assertEqual('deferred_language_review', final['status'])
        english = self.retain(*self.source(2))
        self.assertEqual(2, len(english['links']))

    def test_retain_policy_must_match_the_admitted_lease(self):
        lease = handoff.read(self.settings.path('sync/native_asr_handoff_lease.json'))
        lease['retain_policy'] = 'unreviewed_policy'
        queue.atomic(self.settings.path('sync/native_asr_handoff_lease.json'), lease)
        self.assert_kind('handoff_lease', self.retain, *self.source())

    def test_empty_complete_inventory_does_not_suppress_english_asr(self):
        record, remote = self.source()
        storage.journal(self.settings.path('sync/drive_caption_manifest.jsonl'), {
            'video_id': record['video_id'], 'status': 'none', 'policy': storage.CAPTION_POLICY,
            'captured_at': '2026-11-17T00:00:00Z', 'tracks': [], 'unresolved': []})
        state = self.retain(record, remote)
        final = handoff.finalize_after_cleanup(self.settings, state['handoff_id'], self.archived(record, remote))
        self.assertEqual('ready', final['status'])


if __name__ == '__main__':
    unittest.main()
