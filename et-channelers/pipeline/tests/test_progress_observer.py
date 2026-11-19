import errno
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pipeline import progress_observation_io as io
from pipeline.progress_observer import ProgressObserver


class ProgressObserverTests(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.job=Path(self.folder.name)/'aB01234_bcd';self.job.mkdir()
        io.atomic_observation(self.job/'progress.json',{'received':7},root=self.job)

    def test_changed_then_stable_does_not_default_or_lose_counts(self):
        observer=ProgressObserver(read_progress=lambda *a,**k:next(samples))
        def read(*a,**k):
            value=next(samples)
            if isinstance(value,Exception):raise value
            return value
        samples=iter([io.ObservationChanged('replace'),{'received':9}]);observer.read_progress=read
        self.assertEqual(observer.documents(self.job,active=True),[('progress.json',{'received':9})])
        self.assertTrue(observer.permits_new_dispatch())
        self.assertEqual(observer.states[self.job.name]['read_attempts'],2)

    def test_persistent_instability_blocks_admission_body_and_sibling_bootstrap(self):
        calls=[]
        def changing(*a,**k):calls.append(1);raise io.ObservationChanged('replace')
        observer=ProgressObserver(read_progress=changing)
        self.assertEqual(observer.documents(self.job,active=True),[])
        self.assertEqual(len(calls),3);self.assertFalse(observer.permits_new_dispatch())
        self.assertFalse(observer.permits_first_bootstrap('other000001',started_videos={self.job.name}))
        # First startup can produce its own initial sample; later started siblings cannot bypass it.
        self.assertTrue(observer.permits_first_bootstrap(self.job.name,started_videos=set()))
        observer.read_progress=io.read_observation
        observer.documents(self.job,active=True);self.assertTrue(observer.permits_new_dispatch())

    def test_only_exact_mutable_enoent_is_resampled(self):
        for error in (PermissionError(errno.EACCES,'denied',str(self.job/'progress.json')),
                      FileNotFoundError(errno.ENOENT,'missing',str(self.job/'grant.json')),
                      OSError(errno.EIO,'io')):
            with self.subTest(error=type(error).__name__):
                observer=ProgressObserver(read_progress=lambda *a,**k: (_ for _ in ()).throw(error))
                with self.assertRaises(type(error)):observer.documents(self.job,active=True)
        missing=FileNotFoundError(errno.ENOENT,'replace gap',str(self.job/'progress.json'))
        observer=ProgressObserver(read_progress=lambda *a,**k:(_ for _ in ()).throw(missing))
        self.assertEqual(observer.documents(self.job,active=True),[])
        self.assertEqual(observer.states[self.job.name]['read_attempts'],3)

    def test_bad_json_structure_and_vanished_immutable_result_propagate(self):
        (self.job/'progress.json').write_bytes(b'{')
        with self.assertRaises(json.JSONDecodeError):ProgressObserver().documents(self.job,active=True)
        (self.job/'progress.json').write_bytes(b'[]')
        with self.assertRaisesRegex(ValueError,'structure'):ProgressObserver().documents(self.job,active=True)
        io.atomic_observation(self.job/'progress.json',{'received':7},root=self.job)
        (self.job/'result.json').write_bytes(b'{}')
        error=FileNotFoundError(errno.ENOENT,'immutable vanished',str(self.job/'result.json'))
        observer=ProgressObserver(read_final=lambda p:(_ for _ in ()).throw(error))
        with self.assertRaises(FileNotFoundError):observer.documents(self.job,active=True)

    def test_missing_initial_progress_requires_stable_sample_or_validated_closed_terminal(self):
        (self.job/'progress.json').unlink();observer=ProgressObserver()
        self.assertEqual(observer.documents(self.job,active=True),[])
        self.assertFalse(observer.permits_new_dispatch())
        with self.assertRaises(ValueError):
            observer.accept_validated_closed_terminal(self.job.name,validated_terminal={},owned_closure_validated=False)
        # Merely seeing result.json does not erase the unknown state.
        (self.job/'result.json').write_bytes(b'{}');observer.documents(self.job,active=True)
        self.assertFalse(observer.permits_new_dispatch())
        observer.accept_validated_closed_terminal(self.job.name,validated_terminal={},owned_closure_validated=True)
        self.assertTrue(observer.permits_new_dispatch())

    def test_held_shared_delete_reader_allows_atomic_replace_and_stale_read_is_rejected(self):
        path=self.job/'progress.json'
        with io.open_observation(path,root=self.job) as held:
            old=held.read();io.atomic_observation(path,{'received':11},root=self.job)
            self.assertEqual(json.loads(old),{'received':7})
        self.assertEqual(io.read_observation(path,root=self.job),{'received':11})
        original=io._read_bounded
        def replace_while_reading(stream):
            raw=original(stream);io.atomic_observation(path,{'received':12},root=self.job);return raw
        with patch.object(io,'_read_bounded',replace_while_reading):
            with self.assertRaises(io.ObservationChanged):io.read_observation(path,root=self.job)

    def test_failed_writer_keeps_pending_and_safe_actual_stage(self):
        path=self.job/'progress.json';error=PermissionError(errno.EACCES,'private filename')
        with patch.object(io,'_replace',side_effect=error):
            with self.assertRaises(PermissionError) as caught:io.atomic_observation(path,{'received':12},root=self.job)
        self.assertEqual(caught.exception.safe_io_failure['stage'],'replace')
        self.assertFalse(caught.exception.safe_io_failure['automatic_retry_allowed'])
        self.assertTrue(path.with_name(path.name+'.native.pending').exists())
        self.assertEqual(io.read_observation(path,root=self.job),{'received':7})
        with self.assertRaisesRegex(ValueError,'pending_control_requires_review'):
            io.atomic_observation(path,{'received':13},root=self.job)

    def test_immutable_or_foreign_paths_never_enter_mutable_helper(self):
        for path in (self.job/'root-grant.ACTIVE.json',self.job.parent/'progress.json'):
            with self.assertRaises(ValueError):io.read_observation(path,root=self.job)


if __name__=='__main__':unittest.main()
