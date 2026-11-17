"""Collector/handoff boundary tests; no network, source, browser or GPU."""
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pipeline import native_batch as batch, native_batch_worker as worker, drive_ingest as storage
from pipeline.tests import test_native_batch as fixtures


class NativeHandoffCallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))

    def prepared(self):
        obj, folder, result = fixtures.NativeBatchTests.prepared(self)
        obj.dispatch_paused = threading.Event(); obj.source_stop = threading.Event()
        obj.handoff = SimpleNamespace(lease_id='handoff-fixture', cap_bytes=500_000_000)
        obj.s['asr_handoff'] = {'capacity_wait_seconds': 5, 'caption_bundle_paths': {}}
        module = SimpleNamespace(CONTROL_RESERVE=1_000_000,
            retain_before_cleanup=Mock(return_value={'handoff_id': 'handoff-' + 'a' * 32, 'collector_trusted': {}}),
            finalize_after_cleanup=Mock())
        self.enterContext(patch.object(batch, 'handoff_module', return_value=module))
        return obj, folder, result, module

    def test_links_precede_cleanup_and_ready_follows_durable_canonical_proof(self):
        obj, folder, result, module = self.prepared(); stage = self.root / 'stage'; stage.mkdir()
        events = []; original_remove = storage.remove_local; original_hash = storage.hash_file
        def retain(settings, record, proofs, **kwargs):
            events.append('retain'); fresh = {}
            for kind, source in (('audio', record), ('metadata', record['metadata'])):
                path = self.root / source['path']; os.link(path, stage / kind)
                fresh[kind] = list(storage.fingerprint(path))
            return {'handoff_id': 'handoff-' + 'a' * 32, 'collector_trusted': fresh}
        def remove(path, *args, **kwargs):
            if Path(path).parent != folder: return original_remove(path, *args, **kwargs)
            self.assertEqual(events[0], 'retain'); self.assertTrue((stage / 'audio').exists())
            events.append('remove'); return original_remove(path, *args, **kwargs)
        def finalize(settings, key, done):
            events.append('finalize')
            self.assertTrue(storage.receipt_complete(done, fixtures.item(), obj.s['remote']))
            self.assertEqual(storage.load_state(obj.state_path)[fixtures.ID], done)
            self.assertFalse((self.root / done['path']).exists())
        module.retain_before_cleanup.side_effect = retain; module.finalize_after_cleanup.side_effect = finalize
        with patch.object(storage, 'remove_local', side_effect=remove), patch.object(storage, 'hash_file', wraps=original_hash) as hashes:
            done = obj.publish(fixtures.item(), result)
        self.assertEqual(events, ['retain', 'remove', 'remove', 'finalize'])
        # FakeDrive hashes its fixture uploads once; cleanup does not rehash media.
        audio_hashes = [c for c in hashes.call_args_list if Path(c.args[0]).suffix == '.webm']
        self.assertEqual(len(audio_hashes), 1)
        self.assertTrue(storage.receipt_complete(done, fixtures.item(), obj.s['remote']))

    def test_caption_satisfied_empty_updates_keep_existing_trusted_fingerprints(self):
        obj, folder, result, module = self.prepared(); original = storage.verify_and_delete
        def verify(*args, **kwargs):
            self.assertEqual(set(kwargs['trusted']), {'audio', 'metadata'})
            return original(*args, **kwargs)
        with patch.object(storage, 'verify_and_delete', side_effect=verify): obj.publish(fixtures.item(), result)
        module.finalize_after_cleanup.assert_called_once()

    def test_full_staging_waits_locally_without_reupload_or_cleanup(self):
        obj, folder, result, module = self.prepared()
        module.retain_before_cleanup.side_effect = [storage.IngestError('handoff_capacity', 'fixture'),
            {'handoff_id': 'handoff-' + 'a' * 32, 'collector_trusted': {}}]
        with patch.object(batch.time, 'sleep') as sleep: obj.publish(fixtures.item(), result)
        sleep.assert_called_once_with(1)
        self.assertEqual(obj.drive.calls, ['copy', 'stat'])
        self.assertFalse(obj.dispatch_paused.is_set()); self.assertFalse(obj.source_stop.is_set())

    def test_capacity_timeout_retains_source_and_only_pauses_dispatch(self):
        obj, folder, result, module = self.prepared(); obj.s['asr_handoff']['capacity_wait_seconds'] = 0
        module.retain_before_cleanup.side_effect = storage.IngestError('handoff_capacity', 'fixture')
        with patch.object(storage, 'verify_and_delete') as cleanup:
            with self.assertRaises(storage.IngestError): obj.publish(fixtures.item(), result)
        cleanup.assert_not_called(); self.assertTrue(obj.dispatch_paused.is_set())
        self.assertFalse(obj.source_stop.is_set())
        record = worker.read(folder / 'canonical-record.json')
        self.assertTrue((self.root / record['path']).exists())
        self.assertTrue((self.root / record['metadata']['path']).exists())
        self.assertFalse((self.root / 'sync/STOP_STOCK_WPC_BATCH_V4').exists())

    def test_consumer_queue_lock_contention_waits_at_both_handoff_boundaries(self):
        obj, folder, result, module = self.prepared()
        module.retain_before_cleanup.side_effect = [storage.IngestError('locked', 'fixture'),
            {'handoff_id': 'handoff-' + 'a' * 32, 'collector_trusted': {}}]
        module.finalize_after_cleanup.side_effect = [storage.IngestError('locked', 'fixture'), None]
        with patch.object(batch.time, 'sleep') as sleep: obj.publish(fixtures.item(), result)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(obj.drive.calls, ['copy', 'stat'])
        self.assertFalse(obj.dispatch_paused.is_set()); self.assertFalse(obj.source_stop.is_set())

    def test_lost_finalize_ack_recovers_from_marker_without_source_or_drive_calls(self):
        obj, folder, result, module = self.prepared()
        module.finalize_after_cleanup.side_effect = storage.IngestError('handoff_fixture', 'fixture')
        with self.assertRaises(storage.IngestError): obj.publish(fixtures.item(), result)
        done = worker.read(folder / 'canonical-record.json'); calls = list(obj.drive.calls)
        self.assertTrue(storage.receipt_complete(done, fixtures.item(), obj.s['remote']))
        module.finalize_after_cleanup.side_effect = None
        obj.finalize_handoff(folder, done)
        self.assertEqual(obj.drive.calls, calls)
        self.assertEqual(module.finalize_after_cleanup.call_count, 2)
        changed = dict(done, sha256='0' * 64)
        with self.assertRaisesRegex(worker.Held, 'handoff_checkpoint_binding'): obj.finalize_handoff(folder, changed)

    def test_optional_settings_require_explicit_english_routing_and_bounded_wait(self):
        self.assertIsNone(batch.handoff_settings(self.root, 'fixture:archive', None))
        options = {'owner': 'root', 'lease_id': 'fixture', 'cap_bytes': 500_000_000, 'max_pairs': 3,
                   'retain_policy': 'explicit_original_english_v1', 'capacity_wait_seconds': 900}
        settings = batch.handoff_settings(self.root, 'fixture:archive', options)
        self.assertEqual(settings.cap_bytes, 500_000_000)
        for change in ({'retain_policy': 'all_languages'}, {'capacity_wait_seconds': 0}, {'cap_bytes': 1_000_000_001}):
            with self.assertRaises((worker.Held, storage.IngestError)):
                batch.handoff_settings(self.root, 'fixture:archive', dict(options, **change))


if __name__ == '__main__': unittest.main()
