"""Filesystem-only regressions for native progress/result commits."""
import errno
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

from pipeline import native_batch_worker as worker


class NativeControlWriteTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))

    def denied(self, code=5):
        error = PermissionError(errno.EACCES, 'private-path-and-token-must-not-appear')
        error.winerror = code
        return error

    def test_finished_hook_recovers_sharing_race_once_and_keeps_first_failure(self):
        state = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
        state.audio_written = 4; state.selected_metadata_saved = True
        audio = self.root / 'native-audio.m4a'; audio.write_bytes(b'data')
        actual = worker.os.replace; failures = [self.denied(5), self.denied(32)]
        def replace(source, destination):
            if failures: raise failures.pop(0)
            return actual(source, destination)
        with patch.object(worker, 'TARGET', 'aaaaaaaaaaa'), patch.object(worker.os, 'replace', side_effect=replace) as call, \
                patch.object(worker.time, 'sleep') as sleep:
            worker.record_progress(state, {'status': 'finished', 'downloaded_bytes': 4,
                                          'info_dict': {'id': 'aaaaaaaaaaa'}})
        self.assertEqual(call.call_count, 3); self.assertEqual(sleep.call_count, 2)
        self.assertEqual(worker.completed_file(state, self.root), audio)
        self.assertEqual(worker.read(self.root / 'progress.json')['native_finished_count'], 1)
        summary = state.summary()['control_write_diagnostics']
        self.assertEqual(summary['first_failure']['winerror'], 5)
        self.assertEqual((summary['failure_count'], summary['retry_count'], summary['recovered_writes']), (2, 2, 1))
        self.assertNotIn('private-path', json.dumps(summary))
        self.assertIsNone(state.error)

    def test_exhausted_progress_commit_holds_locally_and_preserves_previous_file(self):
        state = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
        state.save(force=True); old = (self.root / 'progress.json').read_bytes(); last = state.last_save
        first = self.denied(5)
        with patch.object(worker.os, 'replace', side_effect=first) as call, patch.object(worker.time, 'sleep') as sleep:
            with self.assertRaisesRegex(worker.Held, 'control_write_failed') as caught: state.save(force=True)
        self.assertIs(caught.exception.__cause__, first)
        self.assertNotIsInstance(caught.exception, OSError)
        self.assertEqual(call.call_count, 6); self.assertEqual(sleep.call_count, 5)
        self.assertEqual(sum(x.args[0] for x in sleep.call_args_list), .775)
        self.assertEqual((self.root / 'progress.json').read_bytes(), old)
        self.assertEqual(state.last_save, last)
        self.assertEqual(state.control_write_first_failure['winerror'], 5)
        self.assertFalse(list(self.root.glob('*.tmp')))
        chain = worker.safe_exception_chain(caught.exception)
        self.assertEqual(chain['nodes'][0]['code'], 'control_write_failed')
        self.assertNotIn('private-path', json.dumps(chain))

    def test_uncertain_final_result_write_never_reports_success(self):
        path = self.root / 'result.json'
        with patch.object(worker.os, 'replace', side_effect=self.denied(33)) as call, patch.object(worker.time, 'sleep'):
            with self.assertRaisesRegex(worker.Held, 'control_write_failed'):
                worker.write(path, {'status': 'local_complete'})
        self.assertEqual(call.call_count, 6)
        self.assertFalse(path.exists()); self.assertFalse(list(self.root.glob('*.tmp')))

    def test_unrelated_storage_failure_is_not_retried(self):
        error = OSError(errno.ENOSPC, 'private-path')
        with patch.object(worker.os, 'replace', side_effect=error) as call, patch.object(worker.time, 'sleep') as sleep:
            with self.assertRaisesRegex(worker.Held, 'control_write_failed') as caught:
                worker.write(self.root / 'result.json', {'status': 'held'})
        self.assertIs(caught.exception.__cause__, error)
        call.assert_called_once(); sleep.assert_not_called()

    def test_concurrent_writers_have_unique_complete_temporary_files(self):
        path = self.root / 'same.json'; actual = worker.os.replace
        barrier = threading.Barrier(2); seen = []; errors = []
        def replace(source, destination):
            seen.append((Path(source), worker.read(source)))
            barrier.wait(timeout=2)
            actual(source, destination)
        def submit(value):
            try: worker.write(path, {'writer': value})
            except BaseException as error: errors.append(error)
        with patch.object(worker.os, 'replace', side_effect=replace):
            threads = [threading.Thread(target=submit, args=(i,)) for i in (1, 2)]
            for thread in threads: thread.start()
            for thread in threads: thread.join(timeout=3)
        self.assertFalse(errors); self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(len({row[0] for row in seen}), 2)
        self.assertEqual({row[1]['writer'] for row in seen}, {1, 2})
        self.assertIn(worker.read(path)['writer'], (1, 2))
        self.assertFalse(list(self.root.glob('*.tmp')))

    def test_state_saves_serialize_snapshot_and_commit(self):
        state = worker.State({'preserved_controls': []}, self.root, time.time() + 60)
        actual = worker.write; first_entered = threading.Event(); release = threading.Event()
        second_started = threading.Event(); calls = []; errors = []
        def blocked(path, value, **kwargs):
            calls.append(value['phase'])
            if len(calls) == 1:
                first_entered.set()
                if not release.wait(timeout=2): raise AssertionError('fixture timeout')
            return actual(path, value, **kwargs)
        def first():
            try: state.save(force=True)
            except BaseException as error: errors.append(error)
        def second():
            state.phase = 'native_transfer'; second_started.set(); first()
        with patch.object(worker, 'write', side_effect=blocked):
            a = threading.Thread(target=first); a.start(); self.assertTrue(first_entered.wait(timeout=2))
            b = threading.Thread(target=second); b.start(); self.assertTrue(second_started.wait(timeout=2))
            self.assertEqual(calls, ['bootstrap']); release.set()
            a.join(timeout=3); b.join(timeout=3)
        self.assertFalse(errors); self.assertFalse(a.is_alive() or b.is_alive())
        self.assertEqual(calls, ['bootstrap', 'native_transfer'])
        self.assertEqual(worker.read(self.root / 'progress.json')['phase'], 'native_transfer')


if __name__ == '__main__': unittest.main()
