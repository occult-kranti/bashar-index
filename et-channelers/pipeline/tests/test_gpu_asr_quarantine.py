"""Offline hold retention, ownership, crash recovery and accounting checks."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gpu_asr_quarantine as quarantine
import gpu_asr_queue as queue
from gpu_asr import AsrError, kernel_lock
from drive_ingest import IngestError


def proof(raw, name):
    return {'remote':'testdrive:Audio/test/Videos/'+name, 'drive_id':'object-'+name,
            'bytes':len(raw), 'md5':hashlib.md5(raw).hexdigest(), 'sha256':hashlib.sha256(raw).hexdigest()}


class QuarantineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.video = 'TESTHOLD001'
        self.lease_id = 'asr-source-held-fixture'
        self.source = self.root/'asr/input'/self.video
        self.source.mkdir(parents=True)
        self.folder = self.root/'asr/held'/self.lease_id
        self.target = self.folder/'input'
        self.lease_path = self.root/'asr/leases'/f'{self.video}.json'
        self.admission_path = self.root/'asr/jobs/frames/multilingual-v1/admissions/held.json'
        self.audio = b'exact native audio fixture'
        self.metadata = queue.encoded({'source':{'video_id':self.video}, 'languages':{'audio':'und'}})
        audio_path, metadata_path = self.source/f'{self.video}.webm', self.source/f'{self.video}.info.json'
        audio_path.write_bytes(self.audio)
        metadata_path.write_bytes(self.metadata)
        audio_proof, metadata_proof = proof(self.audio, audio_path.name), proof(self.metadata, metadata_path.name)
        self.lease = {'schema_version':1, 'video_id':self.video, 'job_id':'multi-held-fixture',
            'lease_id':self.lease_id, 'status':'active', 'phase':'held_language_review', 'owner':'worker',
            'frame_id':'multilingual-v1', 'consumer_owner':'worker', 'hold_reason':'no_reliable_speech',
            'sourceDriveID':audio_proof['drive_id'], 'expected_bytes':audio_proof['bytes'],
            'expected_hashes':{k:audio_proof[k] for k in ('md5','sha256')},
            'private_path':str(audio_path), 'metadata_private_path':str(metadata_path),
            'admission_path':str(self.admission_path), 'proposal_sha256':'a'*64}
        objects = [{'kind':kind, 'private_path':str(path), 'source':item,
                    'local':{k:item[k] for k in ('bytes','md5','sha256')}, 'source_drive_id_rechecked':True}
                   for kind, path, item in [('audio',audio_path,audio_proof), ('metadata',metadata_path,metadata_proof)]]
        self.admission = {'schema_version':1, 'video_id':self.video, 'job_id':self.lease['job_id'],
            'source_lease':str(self.lease_path), 'source_lease_id':self.lease_id,
            'job':{'video_id':self.video, 'job_id':self.lease['job_id'], 'audio':audio_proof, 'metadata':metadata_proof},
            'verified_input_objects':objects}
        self.held = {'schema_version':1, 'video_id':self.video, 'job_id':self.lease['job_id'],
            'source_lease_id':self.lease_id, 'source_audio_sha256':audio_proof['sha256'],
            'source_audio_drive_id':audio_proof['drive_id'], 'status':'held', 'semantic_text_generated':False,
            'source_delete_allowed':False, 'proposal_sha256':'a'*64, 'decision':{'reason':'no_reliable_speech'}}
        queue.atomic(self.lease_path, self.lease)
        queue.atomic(self.admission_path, self.admission)
        queue.journal(self.root/'sync/asr_language_manifest.jsonl', self.held)
        queue.atomic(self.root/'asr/jobs/ready.json', {'preparation_complete':True,'eligible_remaining':0})

    def apply(self, **kwargs):
        return quarantine.quarantine_hold(self.root,self.video,self.lease_id,operator='test-root',**kwargs)

    def test_retains_exact_inputs_history_and_incomplete_status_without_slot(self):
        original_lease = self.lease_path.read_bytes()
        original_admission = self.admission_path.read_bytes()
        plan = quarantine.plan_quarantine(self.root,self.video,self.lease_id)
        self.assertEqual(plan['state'],'quarantine_planned')
        self.assertFalse(self.folder.exists())
        result = self.apply()
        self.assertEqual(result['state'],'quarantined_hold')
        self.assertFalse(result['completion_claimed'])
        self.assertFalse(result['source_delete_allowed'])
        self.assertFalse(self.source.exists())
        self.assertEqual((self.target/f'{self.video}.webm').read_bytes(),self.audio)
        self.assertEqual((self.target/f'{self.video}.info.json').read_bytes(),self.metadata)
        self.assertEqual((self.folder/'lease.before.json').read_bytes(),original_lease)
        self.assertEqual((self.folder/'admission.before.json').read_bytes(),original_admission)
        self.assertEqual(self.admission_path.read_bytes(),original_admission)
        self.assertFalse((self.root/'sync/asr_manifest.jsonl').exists())
        ready = queue.refresh_ready(self.root,frame_id='multilingual-v1')
        self.assertEqual(ready['active_inputs'],0)
        self.assertEqual(ready['admissions'],[])
        self.assertGreaterEqual(queue.tree_bytes(self.root/'asr'),len(self.audio)+len(self.metadata))
        journal = (self.root/'sync/asr_quarantine_manifest.jsonl').read_bytes()
        self.assertEqual(self.apply(),result)
        self.assertEqual((self.root/'sync/asr_quarantine_manifest.jsonl').read_bytes(),journal)

    def test_resume_after_atomic_move_before_lease_commit(self):
        original = Path.rename
        def moved_then_failed(path,target):
            original(path,target)
            raise OSError('simulated process interruption after move')
        with mock.patch.object(Path,'rename',moved_then_failed), self.assertRaises(OSError):
            self.apply()
        self.assertFalse(self.source.exists())
        self.assertTrue(self.target.exists())
        self.assertEqual(json.loads(self.lease_path.read_bytes())['status'],'active')
        self.assertEqual(self.apply()['state'],'quarantined_hold')

    def test_resume_before_move_and_after_lease_commit(self):
        with mock.patch.object(Path,'rename',side_effect=OSError('before move')), self.assertRaises(OSError):
            self.apply()
        self.assertTrue(self.source.exists())
        self.assertTrue((self.folder/'transaction.json').exists())
        actual = queue.atomic
        def failed_final_receipt(path,value):
            if path.name == 'transaction.json' and value.get('state') == 'quarantined_hold':
                raise OSError('after lease update')
            actual(path,value)
        with mock.patch.object(queue,'atomic',failed_final_receipt), self.assertRaises(OSError):
            self.apply()
        self.assertEqual(json.loads(self.lease_path.read_bytes())['status'],'quarantined_hold')
        self.assertEqual(self.apply()['state'],'quarantined_hold')

    def test_both_locations_are_retained_for_review(self):
        with mock.patch.object(Path,'rename',side_effect=OSError('before move')), self.assertRaises(OSError):
            self.apply()
        shutil.copytree(self.source,self.target)
        with self.assertRaises(IngestError):self.apply()
        self.assertTrue(self.source.exists())
        self.assertTrue(self.target.exists())
        self.assertEqual(json.loads(self.lease_path.read_bytes())['status'],'active')

    def test_changed_input_and_changed_history_cannot_retire_lease(self):
        (self.source/f'{self.video}.webm').write_bytes(b'corrupt')
        with self.assertRaises(IngestError):self.apply()
        self.assertFalse(self.folder.exists())
        (self.source/f'{self.video}.webm').write_bytes(self.audio)
        with mock.patch.object(Path,'rename',side_effect=OSError('before move')), self.assertRaises(OSError):
            self.apply()
        (self.folder/'lease.before.json').write_bytes(b'{}')
        with self.assertRaises(IngestError):self.apply()
        self.assertTrue(self.source.exists())

    def test_processing_or_unproven_hold_is_not_quarantined(self):
        queue.atomic(self.lease_path,dict(self.lease,phase='processing'))
        with self.assertRaises(IngestError):self.apply()
        queue.atomic(self.lease_path,self.lease)
        queue.journal(self.root/'sync/asr_language_manifest.jsonl',dict(self.held,semantic_text_generated=True))
        with self.assertRaises(IngestError):self.apply()
        self.assertFalse(self.folder.exists())

    def test_live_gpu_owner_and_storage_cap_block_before_move(self):
        with kernel_lock(self.root/'sync/asr_gpu_owner.lock'), self.assertRaises(AsrError):self.apply()
        with self.assertRaises(IngestError):self.apply(max_input_bytes=1)
        self.assertTrue(self.source.exists())
        self.assertFalse(self.folder.exists())

    def test_real_input_junction_or_symlink_is_rejected_without_touching_target(self):
        outside=self.root/'preserved';self.source.rename(outside)
        if os.name=='nt':
            import _winapi
            _winapi.CreateJunction(str(outside),str(self.source))
        else:
            self.source.symlink_to(outside,target_is_directory=True)
        try:
            with self.assertRaises(IngestError):self.apply()
            self.assertEqual((outside/f'{self.video}.webm').read_bytes(),self.audio)
        finally:
            if os.name=='nt':os.rmdir(self.source)
            else:self.source.unlink()

    def test_held_bytes_still_prevent_admission_over_workspace_cap(self):
        self.apply()
        empty={'jobs':[],'counts':{}}
        with mock.patch.object(queue,'build_plan',return_value=empty):
            ready=queue.prepare_inputs(self.root,self.root/'unused.csv','testdrive:Audio',object(),
                model_repository='test/model',model_revision='a'*40,frame_id='next-english')
        self.assertEqual(ready['active_inputs'],0)
        with mock.patch.object(queue,'build_plan',return_value=empty), self.assertRaises(IngestError):
            queue.prepare_inputs(self.root,self.root/'unused.csv','testdrive:Audio',object(),
                model_repository='test/model',model_revision='a'*40,frame_id='after-next-english',
                max_input_bytes=queue.tree_bytes(self.root/'asr'))
        self.assertTrue(self.target.exists())


if __name__=='__main__':
    unittest.main()
