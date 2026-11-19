"""Offline admission, scope, ownership and verified cleanup regressions."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import gpu_asr_queue as queue
from drive_ingest import CAPTION_POLICY, journal, IngestError

REMOTE='testdrive:Audio'


def hashes(data):
    return {'bytes':len(data),'md5':hashlib.md5(data).hexdigest(),'sha256':hashlib.sha256(data).hexdigest()}


class FakeDrive:
    def __init__(self):
        self.objects={}
        self.downloads=[]
        self.wrong_id=False
        self.corrupt=False

    def add(self,remote,data):
        self.objects[remote]=data
        return dict(remote=remote,drive_id='object-'+hashlib.sha256(data).hexdigest(),**hashes(data))

    def stat(self,remote):
        data=self.objects[remote]
        return {'ID':'wrong' if self.wrong_id else 'object-'+hashlib.sha256(data).hexdigest(),
                'Size':len(data),'Hashes':{'MD5':hashlib.md5(data).hexdigest()},'IsDir':False}

    def download(self,remote,path,max_bytes):
        self.downloads.append(remote)
        path.write_bytes(b'corrupted' if self.corrupt else self.objects[remote])


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.path=self.root/'jobs/newest20.csv'
        self.path.parent.mkdir()
        self.drive=FakeDrive()
        self.rows=[]

    def add(self,index=0,*,language='en',origin=True,audio_size=100,caption='pending'):
        video_id=f'VID{index:08d}'
        row={'video_id':video_id,'channel_dir':'test-channel','tab':'videos','listing_rank':str(index),'duration_s':'63'}
        parent=f'{REMOTE}/test-channel/Videos'
        audio=self.drive.add(f'{parent}/{video_id}.webm',bytes([index+1])*audio_size)
        metadata=self.drive.add(f'{parent}/{video_id}.info.json',queue.encoded({'source':{'video_id':video_id},'languages':{'audio':language}}))
        record=dict(row,**audio,path=f'audio/test-channel/{video_id}.webm',duration_s=63,status='deleted',metadata=metadata)
        journal(self.root/'sync/drive_ingest_manifest.jsonl',record)
        tracks=[]
        if origin:
            tracks=[{'track_id':'automatic.en','kind':'automatic_original','language':'en','machine_translated':False,'status':'pending'}]
        cap={'video_id':video_id,'channel_dir':'test-channel','status':caption,'captured_at':'2026-11-17T00:00:00Z',
             'policy':CAPTION_POLICY,'inventory_status':'tracks_reported','tracks':tracks,'unresolved':[]}
        if caption in {'deleted','partial'}:
            tracks[0].update(status='deleted',bundle=self.drive.add(f'{parent}/{video_id}.captions.automatic.en.zip',b'caption'))
            if caption=='partial':
                cap.update(status='pending',unresolved=[{'reason':'other_track_pending'}])
        journal(self.root/'sync/drive_caption_manifest.jsonl',cap)
        self.rows.append(row)
        with self.path.open('w',encoding='utf-8',newline='') as output:
            writer=csv.DictWriter(output,fieldnames=list(row));writer.writeheader();writer.writerows(self.rows)
        return record

    def plan(self):
        return queue.build_plan(self.root,self.path,REMOTE,'example/model','a'*40)

    def prepare(self,**kwargs):
        return queue.prepare_inputs(self.root,self.path,REMOTE,self.drive,model_repository='example/model',
                                    model_revision='a'*40,min_free_bytes=0,**kwargs)

    def admission(self,ready):
        return json.loads(Path(ready['admissions'][0]).read_text(encoding='utf-8'))

    def result(self,admission,durable=True):
        job=admission['job'];run='asr-test-1';parent=job['audio']['remote'].rpartition('/')[0]
        bundle=self.drive.add(f'{parent}/{job["video_id"]}/ASR/{run}/{run}.zip',b'versioned-result')
        result=dict(bundle,schema_version=1,status='verified',artifact_kind='asr_bundle',run_id=run,
                    video_id=job['video_id'],job_id=job['job_id'],source_audio_sha256=job['audio']['sha256'],
                    source_audio_drive_id=job['audio']['drive_id'],source_lease_id=admission['source_lease_id'])
        if durable:
            journal(self.root/'sync/asr_manifest.jsonl',result)
        return result

    def language_review(self,record,**changes):
        path=self.root/'asr/jobs/language_review'/f'{record["video_id"]}.info.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(self.drive.objects[record['metadata']['remote']])
        item={'video_id':record['video_id'],'audio_sha256':record['sha256'],
              'metadata_proof':queue.proof(record['metadata']),
              'verified_local_metadata':{'private_path':str(path),'source':queue.proof(record['metadata']),
                 'local':hashes(path.read_bytes()),'source_drive_id_rechecked':True},
              'decision':'declared_english'}
        item.update(changes)
        evidence=self.root/'asr/jobs/language_review.json'
        queue.atomic(evidence,{'schema_version':1,'records':[item]})
        return evidence,path

    def native(self,record,**changes):
        binding={'videoId':record['video_id'],'itag':251,'lastModified':'123456789',
            'xtags':'explicit-original-fixture-tags','mimeType':'audio/webm; codecs="opus"','codec':'opus',
            'contentLength':record['bytes'],'durationMs':63000,'language':'en','originalBasis':'published_original',
            'trackId':'en.4','noDRM':True,'audioOnly':True,'transportKind':'sabr_reassembled'}
        binding.update(changes)
        identity={k:v for k,v in binding.items() if k!='transportKind'}
        record=dict(record,native_transport_kind='sabr_reassembled',native_format_binding=binding,
            native_format_binding_sha256=queue.sha(json.dumps(identity,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()))
        journal(self.root/'sync/drive_ingest_manifest.jsonl',record)
        return record

    def test_native_original_english_candidate_rechecks_sidecar_before_audio(self):
        self.native(self.add(origin=False,language='en-US'),language='en-US')
        job=self.plan()['jobs'][0]
        self.assertEqual(job['decision'],'eligible_native_original_english')
        self.assertEqual(job['language']['basis'],'verified_native_original_format_candidate')
        ready=self.prepare();self.assertEqual(len(ready['admissions']),1)
        self.assertEqual(len(self.drive.downloads),2)
        self.assertTrue(self.drive.downloads[0].endswith('.info.json'))
        self.assertTrue(self.drive.downloads[1].endswith('.webm'))

    def test_native_default_dub_foreign_or_wrong_identity_does_not_admit(self):
        record=self.add(origin=False)
        for changes in ({'originalBasis':'original_default_confirmed'},{'originalBasis':'dubbed'},
                        {'language':'ja'},{'audioOnly':False},{'videoId':'OTHERID0001'},
                        {'durationMs':True},{'xtags':''}):
            with self.subTest(changes=changes):
                self.native(record,**changes)
                self.assertEqual(self.plan()['jobs'][0]['decision'],'hold_language_unconfirmed')
        self.assertEqual(self.drive.downloads,[])

    def test_native_missing_full_metadata_proof_and_changed_binding_hash_are_not_evidence(self):
        record=self.native(self.add(origin=False))
        changed=dict(record,native_format_binding_sha256='0'*64)
        journal(self.root/'sync/drive_ingest_manifest.jsonl',changed)
        self.assertEqual(self.plan()['jobs'][0]['decision'],'hold_language_unconfirmed')
        journal(self.root/'sync/drive_ingest_manifest.jsonl',dict(record,metadata={}))
        self.assertEqual(self.plan()['counts'],{'audio_not_verified':1})

    def test_native_claimed_english_with_foreign_metadata_holds_without_audio(self):
        self.native(self.add(origin=False,language='es-US'))
        self.assertEqual(self.plan()['jobs'][0]['decision'],'eligible_native_original_english')
        self.assertEqual(self.prepare()['admissions'],[])
        self.assertEqual(len(self.drive.downloads),1)
        self.assertTrue(self.drive.downloads[0].endswith('.info.json'))
        lease=json.loads(next((self.root/'asr/leases').glob('*.json')).read_text())
        self.assertEqual(lease['status'],'language_hold')

    def test_native_conflicting_english_metadata_declarations_hold_before_audio(self):
        record=self.add(origin=False)
        body=queue.encoded({'source':{'video_id':record['video_id']},'languages':{'audio':'en'},'metadata':{'language':'es'}})
        record['metadata']=self.drive.add(record['metadata']['remote'],body)
        self.native(record)
        self.assertEqual(self.prepare()['admissions'],[])
        self.assertEqual(len(self.drive.downloads),1)
        lease=json.loads(next((self.root/'asr/leases').glob('*.json')).read_text())
        self.assertEqual(lease['phase'],'metadata_language_conflict')

    def test_caption_alternatives_and_unknown_language_are_not_automatic_asr(self):
        self.add(0,caption='deleted');self.add(1,caption='partial');self.add(2,origin=False,caption='none');self.add(3)
        counts=self.plan()['counts']
        self.assertEqual(counts,{'exclude_complete_english_captions':1,'defer_caption_coverage_review':1,
                                 'hold_language_unconfirmed':1,'eligible_original_english':1})
        self.assertEqual(len(self.prepare()['admissions']),1)

    def test_rejects_non_newest20_scope_before_any_transfer(self):
        self.add(20)
        with self.assertRaises(ValueError):self.prepare()
        self.assertEqual(self.drive.downloads,[])

    def test_mixed_selection_includes_short_and_stream_and_matches_owner(self):
        for i in range(3):
            self.add(i)
        groups = []
        for name, channel, indices in [('test-channel', 'UC' + 'A'*22, [0, 1]),
                                       ('other-creator', 'UC' + 'B'*22, [2])]:
            items = [{'channel_dir': name, 'channel_id': channel, 'video_id': self.rows[i]['video_id'],
                      'tab': 'shorts' if i == 0 else 'streams', 'slot': rank + 1, 'source_position': rank}
                     for rank, i in enumerate(indices)]
            groups.append({'channel_dir': name, 'channel_id': channel, 'scope': 'short_complete_displayed_list',
                           'selected': len(items), 'items': items})
        selection = self.root/'jobs/selected.json'
        queue.atomic(selection, {'schema_version': 1, 'per_channel': 20, 'channels': groups})
        plan = queue.build_plan(self.root, selection, REMOTE, 'example/model', 'a'*40)
        self.assertEqual(plan['scope'], 'canonical_mixed_latest20')
        self.assertEqual(plan['input_sources']['selection_sha256'], queue.sha(selection.read_bytes()))
        self.assertEqual([job['source']['tab'] for job in plan['jobs']], ['shorts', 'streams'])
        self.assertEqual(plan['counts']['audio_not_verified'], 1)
        self.assertEqual(self.plan()['scope'], 'newest20_videos_snapshot')

    def test_space_for_long_recordings_includes_shared_reservations_and_disk_floor(self):
        with patch.object(queue, 'storage_usage', return_value=(100, 10_000_000_000)), \
             patch.object(queue, 'reserved_project_growth', return_value=1_000_000_000), \
             patch.object(queue.shutil, 'disk_usage', return_value=SimpleNamespace(free=14_000_000_000)):
            self.assertTrue(queue.room_for_inputs(self.root, 220_000_000, queue.MAX_INPUT_BYTES, queue.MIN_FREE_BYTES))
            self.assertFalse(queue.room_for_inputs(self.root, 1_100_000_000, queue.MAX_INPUT_BYTES, queue.MIN_FREE_BYTES))
            self.assertFalse(queue.room_for_inputs(self.root, 7_200_000_000, queue.MAX_INPUT_BYTES, 0))

    def test_library_api_rejects_input_storage_inside_git_checkout(self):
        self.add();(self.root/'.git').mkdir()
        with self.assertRaises(SystemExit):self.prepare()
        self.assertEqual(self.drive.downloads,[])

    def test_declared_metadata_language_overrides_english_inventory(self):
        self.add(language='ja')
        ready=self.prepare()
        self.assertEqual(ready['admissions'],[])
        self.assertEqual(len(self.drive.downloads),1)
        self.assertTrue(self.drive.downloads[0].endswith('.info.json'))
        lease=json.loads(next((self.root/'asr/leases').glob('*.json')).read_text())
        self.assertEqual(lease['status'],'language_hold')

    def test_three_active_slots_include_processing_and_prepare_is_idempotent(self):
        for i in range(4):self.add(i)
        first=self.prepare()
        self.assertEqual(len(first['admissions']),3)
        admission=self.admission(first)
        queue.claim_input(self.root,admission,'test-worker')
        second=self.prepare()
        self.assertEqual(second['active_inputs'],3)
        self.assertEqual(len(second['admissions']),2)
        self.assertEqual(len(self.drive.downloads),6)
        with self.assertRaises(IngestError):queue.claim_input(self.root,admission,'second-worker')

    def test_whole_asr_bytes_limit_stops_before_metadata_download(self):
        self.add(audio_size=180_000)
        ready=self.prepare(max_input_bytes=200_000)
        self.assertEqual(ready['admissions'],[])
        self.assertEqual(self.drive.downloads,[])

    def test_wrong_drive_identity_never_admits_source(self):
        self.add();self.drive.wrong_id=True
        with self.assertRaises(IngestError):self.prepare()
        self.assertEqual(self.drive.downloads,[])

    def test_transfer_buffer_headroom_must_fit_reservation(self):
        rec=self.add()
        path=self.root/'asr/input/probe.webm'
        with self.assertRaises(IngestError):
            queue.pull_verified(self.drive,rec,path,rec['bytes']+queue.TRANSFER_HEADROOM-1)
        self.assertEqual(self.drive.downloads,[])

    def test_corrupt_download_is_retained_as_partial_never_ready(self):
        self.add();self.drive.corrupt=True
        with self.assertRaises(IngestError):self.prepare()
        self.assertTrue(list((self.root/'asr/input').rglob('*.part')))
        ready=json.loads((self.root/'asr/jobs/ready.json').read_text())
        self.assertEqual(ready['admissions'],[])

    def test_release_requires_durable_same_source_result_and_exact_drive_id(self):
        self.add();admission=self.admission(self.prepare());result=self.result(admission,durable=False)
        paths=[Path(item['private_path']) for item in admission['verified_input_objects']]
        with self.assertRaises(IngestError):queue.release_input(self.root,admission,result,self.drive)
        self.assertTrue(all(path.exists() for path in paths))
        wrong=dict(result,source_audio_sha256='0'*64)
        journal(self.root/'sync/asr_manifest.jsonl',wrong)
        with self.assertRaises(IngestError):queue.release_input(self.root,admission,wrong,self.drive)
        journal(self.root/'sync/asr_manifest.jsonl',result)
        self.drive.wrong_id=True
        with self.assertRaises(IngestError):queue.release_input(self.root,admission,result,self.drive)
        self.assertTrue(all(path.exists() for path in paths))

    def test_release_deletes_only_owned_inputs_after_proof_and_recovers_partial_cleanup(self):
        self.add();admission=self.admission(self.prepare());result=self.result(admission)
        original=self.root/'audio/archived-original.webm';original.parent.mkdir();original.write_bytes(b'keep')
        Path(admission['verified_input_objects'][0]['private_path']).unlink()
        released=queue.release_input(self.root,admission,result,self.drive)
        self.assertEqual(released['status'],'released')
        self.assertTrue(original.exists())
        self.assertFalse(any(Path(item['private_path']).exists() for item in admission['verified_input_objects']))
        self.assertEqual(self.plan()['counts']['asr_result_already_verified'],1)

    def test_foreign_input_path_cannot_authorize_deletion(self):
        self.add();admission=self.admission(self.prepare());result=self.result(admission)
        foreign=self.root/'original.webm';foreign.write_bytes(b'keep')
        admission['verified_input_objects'][0]['private_path']=str(foreign)
        with self.assertRaises(ValueError):queue.release_input(self.root,admission,result,self.drive)
        self.assertTrue(foreign.exists())

    def test_final_preparation_marker_survives_consumer_claim_and_release(self):
        self.add();ready=self.prepare();self.assertTrue(ready['preparation_complete'])
        admission=self.admission(ready)
        queue.claim_input(self.root,admission,'worker')
        queue.release_input(self.root,admission,self.result(admission),self.drive)
        final=json.loads((self.root/'asr/jobs/ready.json').read_text())
        self.assertTrue(final['preparation_complete'])
        self.assertEqual(final['queue_snapshot'],ready['queue_snapshot'])
        self.assertEqual(final['active_inputs'],0)
        self.assertEqual(final['admissions'],[])

    def test_language_evidence_promotes_actual_declared_english_without_caption_inventory(self):
        record=self.add(origin=False,language='en-US')
        evidence,_=self.language_review(record)
        plan=queue.build_plan(self.root,self.path,REMOTE,'example/model','a'*40,
                              language_evidence=evidence,evidence_only=True)
        self.assertEqual(len(plan['jobs']),1)
        self.assertEqual(plan['jobs'][0]['decision'],'eligible_declared_english')
        self.assertEqual(plan['jobs'][0]['language']['code'],'en-US')
        self.assertIn('language_evidence_sha256',plan['input_sources'])

    def test_language_review_label_cannot_override_non_english_actual_metadata(self):
        record=self.add(origin=False,language='ja')
        evidence,_=self.language_review(record,decision='declared_english')
        plan=queue.build_plan(self.root,self.path,REMOTE,'example/model','a'*40,
                              language_evidence=evidence,evidence_only=True)
        self.assertEqual(plan['jobs'],[])

    def test_language_evidence_rejects_wrong_source_proof_or_modified_sidecar(self):
        record=self.add(origin=False,language='en')
        for mutation in ({'audio_sha256':'0'*64},{'metadata_proof':dict(record['metadata'],drive_id='different')}):
            evidence,_=self.language_review(record,**mutation)
            with self.assertRaises(IngestError):
                queue.build_plan(self.root,self.path,REMOTE,'example/model','a'*40,language_evidence=evidence,evidence_only=True)
        evidence,sidecar=self.language_review(record)
        sidecar.write_bytes(sidecar.read_bytes()+b' ')
        with self.assertRaises(IngestError):
            queue.build_plan(self.root,self.path,REMOTE,'example/model','a'*40,language_evidence=evidence,evidence_only=True)

    def test_next_frame_waits_for_release_and_never_replaces_primary_ready(self):
        self.add(0);second=self.add(1,origin=False)
        primary=self.prepare();first=self.admission(primary)
        evidence,_=self.language_review(second)
        ready_path=self.root/'asr/jobs/ready.json';before=ready_path.read_bytes()
        with self.assertRaises(IngestError):
            self.prepare(language_evidence=evidence,evidence_only=True,frame_id='english-metadata-v1')
        self.assertEqual(ready_path.read_bytes(),before)
        queue.release_input(self.root,first,self.result(first),self.drive)
        before=ready_path.read_bytes()
        next_ready=self.prepare(language_evidence=evidence,evidence_only=True,frame_id='english-metadata-v1')
        self.assertEqual(len(next_ready['admissions']),1)
        self.assertEqual(ready_path.read_bytes(),before)
        self.assertTrue((self.root/'asr/jobs/frames/english-metadata-v1/ready.json').exists())


if __name__=='__main__':unittest.main()
