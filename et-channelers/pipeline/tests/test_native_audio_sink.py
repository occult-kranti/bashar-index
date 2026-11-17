"""Offline failure-mode fixtures; no source, Drive, browser, codec or GPU jobs."""
import concurrent.futures
import copy
import csv
import hashlib
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import threading
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import native_audio_sink as n
import drive_ingest as core
from media_metadata import build_metadata

VIDEO='abcdefghijk'
def selected(video=VIDEO,length=8,kind='direct_http'):
    return {'videoId':video,'itag':251,'lastModified':'1794000000000000','xtags':None,'mimeType':'audio/webm; codecs="opus"',
        'codec':'opus','contentLength':length,'durationMs':10000,'language':'en','originalBasis':'published_original',
        'trackId':'en.4','noDRM':True,'audioOnly':True,'transportKind':kind}

def probe(path,binding,executable):
    return {'method':'offline_probe_fixture','duration_seconds':10.0,'packets':20,'codec':'opus','audio_streams':1,'video_streams':0}

class Drive:
    def __init__(self):self.objects={};self.copy_calls=0;self.bad_metadata=False;self.after_copy=None
    def copy_pair(self,a,m,ar,mr):
        self.copy_calls+=1
        for index,(p,remote) in enumerate(((a,ar),(m,mr))):
            h=n.digest(p);self.objects[remote]={'Size':h['bytes'],'ID':'drive-'+str(index),'Hashes':{'md5':h['md5']},'IsDir':False}
        if self.after_copy:self.after_copy()
    def stat(self,remote):
        value=copy.deepcopy(self.objects[remote])
        if self.bad_metadata and remote.endswith('.info.json'):value['Hashes']['md5']='0'*32
        return value

class Fixtures(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'sync').mkdir();self.queue=self.root/'queue.csv'
        self.managed=[self.root,Path(n.__file__).resolve().parents[2],Path(sys.prefix).resolve()]
        real_tree=n.tree_bytes
        self.tree_patch=patch.object(n,'tree_bytes',side_effect=lambda p:real_tree(p) if Path(p).resolve().is_relative_to(self.root) else 0)
        self.tree_patch.start()
        with self.queue.open('w',newline='',encoding='utf-8') as out:
            w=csv.DictWriter(out,fieldnames=['video_id','channel_dir','tab','listing_rank']);w.writeheader()
            for i,v in enumerate([VIDEO,'bcdefghijkl','cdefghijklm','defghijklmn','efghijklmno']):w.writerow({'video_id':v,'channel_dir':'fixture','tab':'videos','listing_rank':i})
        self.lease={'state':'active','owner':'fixture','lease_id':'native-test','expires_at_epoch':time.time()+3600,'worker_sha256':n.digest(Path(n.__file__))['sha256'],
            'queue_sha256':n.digest(self.queue)['sha256'],'remote':'test:Audio','native_encoded_audio_only':True,'spool_cap_bytes':8_000_000_000,'max_workers':1,'managed_roots':[str(p) for p in self.managed]}
        self.plan={'collector_dispatch_allowed':False,'accounting_cap_bytes':16_000_000_000,'reservations':[{'owner':'fixture','lease_id':'native-test','state':'active','max_bytes':8_000_000_000}]}
        n.atomic(self.root/'sync/native_batch_lease.json',self.lease);n.atomic(self.root/'sync/analysis_resource_plan.json',self.plan);(self.root/'sync/STOP_DRIVE_INGEST').touch()
    def tearDown(self):self.tree_patch.stop();self.tmp.cleanup()
    def coordinator(self,**kwargs):return n.Coordinator(self.root,owner='fixture',lease_id=self.lease['lease_id'],queue_path=self.queue,managed_roots=self.managed,remote='test:Audio',ffprobe='offline',core=core,metadata_builder=build_metadata,probe=probe,disk_free=lambda:50_000_000_000,**kwargs)
    def begin(self,c,sel=None):
        sel=sel or selected();return c.begin(sel,{'id':sel['videoId'],'title':'Invented fixture','language':'en','url':'https://example.googlevideo.com/videoplayback?token=secret'})
    def pilot(self,budget=2):
        with self.queue.open('a',newline='',encoding='utf-8') as out:
            csv.writer(out).writerow(['EliqxbbQoRw','fixture','videos','5'])
        pins={}
        for key in ('sdk','observer','adapter'):
            path=self.root/(key+'.js');path.write_text('// invented offline pin')
            pins[key]={'path':str(path),'sha256':n.digest(path)['sha256']}
        now=time.time();self.lease['queue_sha256']=n.digest(self.queue)['sha256']
        self.lease['pilotPolicy']={'kind':'accepted_chrome_sabr_single_fullfile_v1','approvedByResourceOwner':True,
            'targetVideoId':'EliqxbbQoRw','transportKind':'sabr_reassembled','acceptedContext':'normal_user_chrome','maxAttempts':1,
            'createdAtEpoch':now-1,'expiresAtEpoch':now+600,'expectedDurationMs':1570961,'durationToleranceMs':150,
            'maxOutputBytes':64_000_000,'sourceRequestBudget':budget,'codePins':pins,'bindFirstValidatedHash':True}
        n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        self.old_deadline=now+7*86400
        core.journal(self.root/'sync/drive_ingest_manifest.jsonl',{'video_id':'EliqxbbQoRw','status':'error','error_class':'forbidden',
            'source_error_class':'forbidden','retry_not_before_epoch':self.old_deadline,'native_browser_refusals':2})
        x=selected('EliqxbbQoRw',kind='sabr_reassembled');x['durationMs']=1570961
        return x
    def fill(self,s,data=b'12345678'):
        state=s.state();return s.write({'offset':state['offset'],'seq':state['next_seq'],'bytes':data})
    def finish(self,s,**extra):return s.finish({'sourceBindingSha256':s.state()['binding_sha256'],'bytes':s.state()['offset'],'protocolEos':True,'reencoded':False,**extra})

    def followup(self,context='normal_user_chrome'):
        x=self.pilot();gateway=self.root/'gateway.py';gateway.write_text('# offline gateway')
        self.lease['pilotPolicy']['acceptedContext']=context
        self.lease['gateway_sha256']=n.digest(gateway)['sha256'];n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        with self.coordinator() as c:
            sink=c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
            sink.authorize_request({'sourceBindingSha256':sink.state()['binding_sha256'],'requestSequence':1});self.fill(sink)
            sink.segment({'number':0,'initialization':True,'startTimeMs':0,'endTimeMs':0,'declaredBytes':8,'byteOffset':0,'emittedBytes':8,'sha256':hashlib.sha256(b'12345678').hexdigest(),'initDiscardedBytes':0})
            sink.retain('protocol');parent_folder=sink.folder
        frozen=self.root/'frozen';frozen.mkdir();pins={}
        for name,path in {'worker':Path(n.__file__),'gateway':gateway,**{k:Path(v['path']) for k,v in self.lease['pilotPolicy']['codePins'].items()}}.items():
            target=frozen/(name+'.source');shutil.copyfile(path,target);pins[name]={'path':str(target),'sha256':n.digest(target)['sha256']}
        n.atomic(frozen/'lease.json',self.lease);n.atomic(frozen/'code.json',{'schema_version':1,'files':pins})
        parent={'leaseSnapshot':{'path':str(frozen/'lease.json'),'sha256':n.digest(frozen/'lease.json')['sha256']},
            'codeSnapshot':{'path':str(frozen/'code.json'),'sha256':n.digest(frozen/'code.json')['sha256']},
            'attemptSha256':n.digest(self.root/'sync/native_context_pilot_attempt.json')['sha256'],
            'jobStateSha256':n.digest(parent_folder/'state.json')['sha256'],'segmentLedgerSha256':n.digest(parent_folder/'segments.jsonl')['sha256'],
            'partialSha256':n.digest(parent_folder/'audio.part')['sha256']}
        self.lease['lease_id']='native-followup';self.plan['reservations'][0]['lease_id']='native-followup'
        policy=self.lease['pilotPolicy'];policy.update(kind='accepted_chrome_sabr_diagnostic_followup_v2',parent=parent)
        for name in ('sdk','adapter'):
            path=Path(policy['codePins'][name]['path']);path.write_text('// reviewed offline diagnostics '+name);policy['codePins'][name]['sha256']=n.digest(path)['sha256']
        n.atomic(self.root/'sync/native_batch_lease.json',self.lease);n.atomic(self.root/'sync/analysis_resource_plan.json',self.plan)
        return x,parent_folder

    def normal_followup(self):
        x,first=self.followup(context='automated_dedicated_chromium')
        with self.coordinator() as c:
            sink=c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
            sink.authorize_request({'sourceBindingSha256':sink.state()['binding_sha256'],'requestSequence':1});self.fill(sink)
            for number,data in enumerate((b'1234',b'5678')):
                sink.segment({'number':number,'initialization':number==0,'startTimeMs':0,'endTimeMs':0 if number==0 else 69892,
                    'declaredBytes':4,'byteOffset':number*4,'emittedBytes':4,'sha256':hashlib.sha256(data).hexdigest(),'initDiscardedBytes':0})
            sink.retain('protocol');second=sink.folder
        frozen=self.root/'frozen-v2';frozen.mkdir();pins={}
        oldpins=n.read(self.root/'frozen/code.json')['files']
        paths={'worker':Path(n.__file__),'gateway':Path(oldpins['gateway']['path']),**{k:Path(v['path']) for k,v in self.lease['pilotPolicy']['codePins'].items()}}
        for name,path in paths.items():
            target=frozen/(name+'.source');shutil.copyfile(path,target);pins[name]={'path':str(target),'sha256':n.digest(target)['sha256']}
        n.atomic(frozen/'lease.json',self.lease);n.atomic(frozen/'code.json',{'schema_version':1,'files':pins})
        diagnostics={'schemaVersion':1,'errorKind':'sdk_stalled','counts':{'request':1,'response':1,'policy':1,'protection':1,'observer_error':0,'reload':0},
            'latest':{'protection':{'status':2},'response':{'status':200},'track':{'endOfStream':False},
                'request':{'selectedAudioMatches':True,'selectedAudioCount':1,'selectedVideoCount':0,'playerTimeMs':69892,'bufferedDurationMs':69892,'bufferedStartMs':0}}}
        n.atomic(frozen/'diagnostic.json',{'video_id':x['videoId'],'state':'held','error_class':'sdk_stalled','source_refusals':[],'sabr_diagnostics':diagnostics})
        parent={'leaseSnapshot':{'path':str(frozen/'lease.json'),'sha256':n.digest(frozen/'lease.json')['sha256']},
            'codeSnapshot':{'path':str(frozen/'code.json'),'sha256':n.digest(frozen/'code.json')['sha256']},
            'diagnosticSnapshot':{'path':str(frozen/'diagnostic.json'),'sha256':n.digest(frozen/'diagnostic.json')['sha256']},
            'attemptSha256':n.digest(self.root/'sync/native_context_pilot_followup_v2.json')['sha256'],
            'jobStateSha256':n.digest(second/'state.json')['sha256'],'segmentLedgerSha256':n.digest(second/'segments.jsonl')['sha256'],'partialSha256':n.digest(second/'audio.part')['sha256']}
        statement=self.root/'user-statement.txt';statement.write_text('Invented offline statement: normal playback continues beyond ninety seconds.')
        evidence=self.root/'normal-playback.json';n.atomic(evidence,{'schema_version':1,'basis':'user_reported_normal_chrome_playback','video_id':x['videoId'],
            'plays_beyond_seconds':90,'approvedByResourceOwner':True,'statement':{'path':str(statement),'sha256':n.digest(statement)['sha256']}})
        self.lease['lease_id']='native-normal-context';self.plan['reservations'][0]['lease_id']=self.lease['lease_id']
        self.lease['pilotPolicy'].update(kind=n.PILOT_V3,acceptedContext='normal_user_chrome',maxContextFollowups=1,parent=parent,
            normalPlaybackEvidence={'path':str(evidence),'sha256':n.digest(evidence)['sha256']})
        n.atomic(self.root/'sync/native_batch_lease.json',self.lease);n.atomic(self.root/'sync/analysis_resource_plan.json',self.plan)
        return x,first,second

    def test_normal_context_preserves_two_ancestors_and_labels_user_report(self):
        x,first,second=self.normal_followup()
        paths=[self.root/'sync/native_context_pilot_attempt.json',self.root/'sync/native_context_pilot_followup_v2.json',*first.iterdir(),*second.iterdir()]
        before={p:p.read_bytes() for p in paths}
        with self.coordinator() as c:
            sink=c.begin(x,{'id':x['videoId']},output_budget_bytes=8);state=sink.state()
            self.assertNotIn(sink.job_id,{first.name,second.name});self.assertEqual(len(c.states()),3)
            self.assertGreater(c.inventory()['outstanding_bytes'],2*n.CONTROL_RESERVE)
            provenance=state['acquisition_provenance'];self.assertEqual(provenance['normal_playback_basis'],'user_reported_normal_chrome_playback')
            self.assertIs(provenance['normal_playback_observed_by_collector'],False)
            self.assertNotIn('Invented offline statement',json.dumps(state))
            sink.authorize_request({'sourceBindingSha256':state['binding_sha256'],'requestSequence':1})
            spent=n.read(self.root/'sync/native_context_normal_chrome_attempt_v3.json');self.assertEqual(spent['schema_version'],3);self.assertEqual(spent['attempts_spent'],1)
            sink.retain('forbidden')
        self.assertEqual(before,{p:p.read_bytes() for p in paths})

    def test_normal_context_rejects_wrong_context_changed_code_and_false_evidence(self):
        x,first,second=self.normal_followup();baseline=copy.deepcopy(self.lease['pilotPolicy'])
        bad=copy.deepcopy(baseline);bad['acceptedContext']='automated_dedicated_chromium'
        changed=self.root/'changed-sdk.js';changed.write_text('// unauthorized transport change')
        changedpin={'path':str(changed),'sha256':n.digest(changed)['sha256']}
        changedpolicy=copy.deepcopy(baseline);changedpolicy['codePins']['sdk']=changedpin
        evidencepath=Path(baseline['normalPlaybackEvidence']['path']);evidence=n.read(evidencepath);evidence['basis']='fresh_measured_playback'
        wrong=self.root/'wrong-evidence.json';n.atomic(wrong,evidence)
        wrongpolicy=copy.deepcopy(baseline);wrongpolicy['normalPlaybackEvidence']={'path':str(wrong),'sha256':n.digest(wrong)['sha256']}
        diagpath=Path(baseline['parent']['diagnosticSnapshot']['path']);diag=n.read(diagpath);diag['sabr_diagnostics']['latest']['protection']['status']=3
        refused=self.root/'refused-diagnostic.json';n.atomic(refused,diag)
        refusedpolicy=copy.deepcopy(baseline);refusedpolicy['parent']['diagnosticSnapshot']={'path':str(refused),'sha256':n.digest(refused)['sha256']}
        for policy,error in ((bad,'pilot_parent_context'),(changedpolicy,'pilot_context_code_changed'),(wrongpolicy,'pilot_normal_playback_evidence'),(refusedpolicy,'pilot_parent_diagnostic')):
            with self.subTest(error=error):
                self.lease['pilotPolicy']=policy;n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
                with self.coordinator() as c:
                    with self.assertRaisesRegex(n.SinkError,error):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
                self.assertFalse((self.root/'sync/native_context_normal_chrome_attempt_v3.json').exists())
        self.lease['pilotPolicy']=baseline;n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        (first/'audio.part').write_bytes(b'corrupt!')
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'pilot_parent_changed'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)

    def test_normal_context_reservations_replay_and_fourth_attempt_denied(self):
        x,first,second=self.normal_followup();self.lease['spool_cap_bytes']=2*n.CONTROL_RESERVE+30_000;n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'spool_storage_deferred'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
        self.assertFalse((self.root/'sync/native_context_normal_chrome_attempt_v3.json').exists())
        self.lease['spool_cap_bytes']=8_000_000_000;n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        with self.coordinator() as c:
            c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
            with self.assertRaisesRegex(n.SinkError,'pilot_attempt_spent'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
        self.lease['lease_id']='native-fourth';self.plan['reservations'][0]['lease_id']='native-fourth'
        n.atomic(self.root/'sync/native_batch_lease.json',self.lease);n.atomic(self.root/'sync/analysis_resource_plan.json',self.plan)
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'pilot_attempt_spent'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)

    def test_followup_unique_job_preserves_parent_even_after_new_refusal(self):
        x,parent=self.followup();paths=[self.root/'sync/native_context_pilot_attempt.json',*parent.iterdir()]
        before={p:p.read_bytes() for p in paths}
        with self.coordinator() as c:
            sink=c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
            self.assertNotEqual(sink.job_id,parent.name)
            self.assertEqual(sink.state()['diagnostic_parent_job_id'],parent.name)
            self.assertGreater(c.inventory()['outstanding_bytes'],n.CONTROL_RESERVE)
            proof={'sourceBindingSha256':sink.state()['binding_sha256'],'requestSequence':1}
            self.assertTrue(sink.authorize_request(proof)['authorized'])
            spent=n.read(self.root/'sync/native_context_pilot_followup_v2.json');self.assertEqual(spent['attempts_spent'],1)
            self.assertEqual(spent['parent_attempt_sha256'],self.lease['pilotPolicy']['parent']['attemptSha256'])
            self.assertEqual(n.latest_receipts(self.root/'sync/drive_ingest_manifest.jsonl')[x['videoId']]['retry_not_before_epoch'],self.old_deadline)
            sink.retain('rate_limited')
            self.assertTrue((self.root/'sync/STOP_DRIVE_INGEST').exists())
            self.assertTrue((self.root/'sync/native_batch_source_cooldown.json').exists())
        self.assertEqual(before,{p:p.read_bytes() for p in paths})

    def test_followup_rejects_changed_proof_binding_codes_and_third_lineage(self):
        x,parent=self.followup();policy=self.lease['pilotPolicy'];baseline=copy.deepcopy(policy)
        cases=[]
        bad=copy.deepcopy(baseline);bad['parent']['attemptSha256']='0'*64;cases.append((bad,x,'pilot_parent_changed'))
        bad=copy.deepcopy(baseline);old=n.read(Path(bad['parent']['codeSnapshot']['path']))['files']['sdk'];bad['codePins']['sdk']=old;cases.append((bad,x,'pilot_diagnostics_unchanged'))
        altered=copy.deepcopy(x);altered['lastModified']='999';cases.append((baseline,altered,'pilot_parent_binding'))
        for bad,selection,error in cases:
            with self.subTest(error=error):
                self.lease['pilotPolicy']=bad;n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
                with self.coordinator() as c:
                    with self.assertRaisesRegex(n.SinkError,error):c.begin(selection,{'id':x['videoId']},output_budget_bytes=8)
                self.assertFalse((self.root/'sync/native_context_pilot_followup_v2.json').exists())
        self.lease['pilotPolicy']=baseline
        state=n.read(parent/'state.json');state['source_error_class']='forbidden';n.atomic(parent/'state.json',state)
        baseline['parent']['jobStateSha256']=n.digest(parent/'state.json')['sha256'];n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'pilot_parent_not_terminal'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
        del state['source_error_class'];state['diagnostic_parent_job_id']='native-'+'0'*24;n.atomic(parent/'state.json',state)
        baseline['parent']['jobStateSha256']=n.digest(parent/'state.json')['sha256'];n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'pilot_parent_not_terminal'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)

    def test_followup_spent_once_and_parent_reservation_still_limits_storage(self):
        x,parent=self.followup();self.lease['spool_cap_bytes']=n.CONTROL_RESERVE+20_000;n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'spool_storage_deferred'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
            self.assertFalse((self.root/'sync/native_context_pilot_followup_v2.json').exists())
        self.lease['spool_cap_bytes']=8_000_000_000;n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        with self.coordinator() as c:
            c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
            with self.assertRaisesRegex(n.SinkError,'pilot_attempt_spent'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
        self.lease['lease_id']='native-third';self.plan['reservations'][0]['lease_id']='native-third'
        n.atomic(self.root/'sync/native_batch_lease.json',self.lease);n.atomic(self.root/'sync/analysis_resource_plan.json',self.plan)
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'pilot_attempt_spent'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)

    def test_followup_excludes_only_exact_parent_from_source_slots(self):
        x,parent=self.followup();other=self.root/'native_batch/jobs'/('native-'+'f'*24);other.mkdir()
        state=n.read(parent/'state.json');state.update(job_id=other.name,video_id=VIDEO,native_lease_id='unrelated-lease')
        n.atomic(other/'state.json',state)
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'worker_slots_full'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
        self.assertFalse((self.root/'sync/native_context_pilot_followup_v2.json').exists())

    def test_inactive_lease_no_spool_or_job(self):
        self.lease['state']='proposed';n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        with self.assertRaisesRegex(n.SinkError,'native_lease_inactive'):
            with self.coordinator():pass
        self.assertFalse((self.root/'native_batch').exists())

    def test_four_workers_require_real_durable_first_pair(self):
        self.lease['max_workers']=4;n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        n.atomic(self.root/'sync/native_single_worker_acceptance.json',{'approved_by_resource_owner':True,'worker_sha256':self.lease['worker_sha256'],'receipt':{}})
        with self.assertRaisesRegex(n.SinkError,'single_fullfile_gate_missing'):
            with self.coordinator():pass

    def test_chunk_order_size_length_and_truncation_fail_closed(self):
        with self.coordinator() as c:
            s=self.begin(c)
            for bad in ({'offset':0,'seq':1,'bytes':b'1'},{'offset':1,'seq':0,'bytes':b'1'},{'offset':0,'seq':0,'bytes':b'x'*(n.MAX_CHUNK+1)}):
                with self.assertRaises(n.SinkError):s.write(bad)
            self.fill(s,b'1234')
            with self.assertRaisesRegex(n.SinkError,'truncated_native_file'):self.finish(s)
            self.assertEqual((s.folder/'audio.part').read_bytes(),b'1234')
            with self.assertRaises(n.SinkError):self.fill(s,b'56789')

    def test_missing_metadata_identity_and_drm_never_admitted(self):
        with self.coordinator() as c:
            x=selected();x['noDRM']=False
            with self.assertRaises(n.SinkError):self.begin(c,x)
            with self.assertRaises(n.SinkError):c.begin(selected(),{'id':'wrong_video'})
            self.assertEqual(c.states(),[])

    def test_success_core_pair_proof_before_delete_and_private_metadata(self):
        with self.coordinator() as c:
            s=self.begin(c);self.fill(s);record=self.finish(s)
            metadata=self.root/record['metadata']['path'];self.assertNotIn('googlevideo',metadata.read_text())
            d=Drive();result=s.publish(d)
            self.assertTrue(core.receipt_complete(result,c.rows[VIDEO],'test:Audio'))
            self.assertEqual(d.copy_calls,1);self.assertFalse(metadata.exists());self.assertFalse((self.root/record['path']).exists())
            self.assertEqual(n.latest_receipts(self.root/'sync/drive_ingest_manifest.jsonl')[VIDEO]['status'],'deleted')

    def test_metadata_bad_drive_hash_preserves_both(self):
        with self.coordinator() as c:
            s=self.begin(c);self.fill(s);r=self.finish(s);d=Drive();d.bad_metadata=True
            with self.assertRaises(core.IngestError):s.publish(d)
            self.assertTrue((self.root/r['path']).exists());self.assertTrue((self.root/r['metadata']['path']).exists())

    def test_source_edit_during_upload_preserves_pair(self):
        with self.coordinator() as c:
            s=self.begin(c);self.fill(s);r=self.finish(s);d=Drive();d.after_copy=lambda:(self.root/r['path']).write_bytes(b'87654321')
            with self.assertRaises(core.IngestError):s.publish(d)
            self.assertTrue((self.root/r['metadata']['path']).exists())

    def test_delete_crash_recovers_verified_objects_without_recopy(self):
        with self.coordinator() as c:
            s=self.begin(c);self.fill(s);r=self.finish(s);d=Drive();original=core.remove_local;calls=[]
            def crash(path,*a,**k):
                calls.append(path)
                if len(calls)==2:raise OSError('invented power loss')
                original(path,*a,**k)
            with patch.object(core,'remove_local',side_effect=crash):
                with self.assertRaises(OSError):s.publish(d)
            self.assertEqual(n.latest_receipts(self.root/'sync/drive_ingest_manifest.jsonl')[VIDEO]['status'],'verified')
            self.assertEqual(s.publish(d)['status'],'deleted');self.assertEqual(d.copy_calls,1)

    def test_retain_after_verified_deletion_preserves_terminal_proof(self):
        with self.coordinator() as c:
            s=self.begin(c);self.fill(s);self.finish(s);receipt=s.publish(Drive());before=s.state()
            result=s.retain('aborted')
            self.assertTrue(result['driveVerified']);self.assertFalse(result['retained']);self.assertEqual(s.state(),before)
            self.assertEqual(n.latest_receipts(self.root/'sync/drive_ingest_manifest.jsonl')[VIDEO],receipt)

    def test_retain_during_and_after_upload_failure_keeps_publish_recovery(self):
        with self.coordinator() as c:
            s=self.begin(c);self.fill(s);record=self.finish(s);drive=Drive();drive.bad_metadata=True
            observed=[]
            drive.after_copy=lambda:observed.append(s.retain('aborted'))
            with self.assertRaises(core.IngestError):s.publish(drive)
            self.assertEqual(observed[0]['state'],'publishing');self.assertTrue(observed[0]['proofStatePreserved'])
            result=s.retain('network');self.assertEqual(result['state'],'publishing');self.assertEqual(s.state()['record'],record)
            self.assertTrue((self.root/record['path']).exists());self.assertTrue((self.root/record['metadata']['path']).exists())
            drive.bad_metadata=False;drive.after_copy=None;self.assertEqual(s.publish(drive)['status'],'deleted')

    def test_resume_full_identity_prefix_and_http_response(self):
        with self.coordinator() as c:
            s=self.begin(c);self.fill(s,b'1234');job=s.job_id
        with self.coordinator() as c:
            bad=selected();bad['lastModified']='999'
            with self.assertRaisesRegex(n.SinkError,'resume_format_changed'):c.resume(job,bad)
            s=c.resume(job,selected())
            with self.assertRaisesRegex(n.SinkError,'resume_response_unverified'):self.fill(s,b'5678')
            with self.assertRaises(n.SinkError):s.authorize_direct_resume(status=200,range_start=4,total=8,binding_sha256=s.state()['binding_sha256'])
            s.authorize_direct_resume(status=206,range_start=4,total=8,binding_sha256=s.state()['binding_sha256']);self.fill(s,b'5678');self.finish(s)

    def test_corrupt_prefix_or_unacked_tail_never_resumes(self):
        with self.coordinator() as c:
            s=self.begin(c);self.fill(s,b'1234');job=s.job_id
        for content in (b'12345',b'abcd'):
            (s.folder/'audio.part').write_bytes(content)
            with self.coordinator() as c:
                with self.assertRaises(n.SinkError):c.resume(job,selected())

    def test_403_stops_all_future_source_writes_and_persists(self):
        stopped=[]
        with self.coordinator(on_batch_abort=stopped.append) as c:
            s=self.begin(c);self.fill(s,b'1234');s.retain('forbidden')
            self.assertTrue(c.source_stop.is_set());self.assertEqual(stopped,['forbidden'])
            with self.assertRaises(n.SinkError):self.fill(s,b'5678')
            self.assertGreater(n.read(self.root/'sync/native_batch_source_cooldown.json')['retry_not_before_epoch'],time.time()+86300)
        with self.coordinator() as c:
            with self.assertRaises(n.SinkError):self.begin(c,selected('bcdefghijkl'))

    def test_managed_and_disk_reservations_not_just_spool(self):
        self.plan['reservations'].append({'owner':'other','lease_id':'other','state':'active','max_bytes':16_000_000_000})
        n.atomic(self.root/'sync/analysis_resource_plan.json',self.plan)
        with self.assertRaisesRegex(n.SinkError,'managed_storage_deferred'):
            with self.coordinator():pass

    def test_single_slot_concurrent_begin_cannot_double_spend(self):
        with self.coordinator() as c:
            def begin(video):
                try:return self.begin(c,selected(video)).job_id
                except n.SinkError as e:return e.code
            with concurrent.futures.ThreadPoolExecutor(2) as pool:results=list(pool.map(begin,[VIDEO,'bcdefghijkl']))
            self.assertEqual(results.count('worker_slots_full'),1);self.assertEqual(len(c.states()),1)

    def test_parallel_postpilot_reservations_include_metadata_headroom(self):
        with self.coordinator() as c:
            s=self.begin(c);self.fill(s);self.finish(s);receipt=s.publish(Drive())
            n.atomic(self.root/'sync/native_single_worker_acceptance.json',{'approved_by_resource_owner':True,'worker_sha256':self.lease['worker_sha256'],'receipt':receipt})
            self.lease.update(max_workers=4,spool_cap_bytes=n.CONTROL_RESERVE*2+20000)
            n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
            def attempt(video):
                try:self.begin(c,selected(video));return 'admitted'
                except n.SinkError as error:return error.code
            with concurrent.futures.ThreadPoolExecutor(4) as pool:out=list(pool.map(attempt,['bcdefghijkl','cdefghijklm','defghijklmn','efghijklmno']))
            self.assertEqual(out.count('admitted'),2);self.assertEqual(out.count('spool_storage_deferred'),2)

    def test_duplicate_publish_has_exclusive_perjob_claim(self):
        entered,release=threading.Event(),threading.Event()
        with self.coordinator() as c:
            s=self.begin(c);self.fill(s);self.finish(s);drive=Drive();old=drive.copy_pair
            def wait(*args):entered.set();release.wait(2);old(*args)
            drive.copy_pair=wait
            with concurrent.futures.ThreadPoolExecutor(1) as pool:
                first=pool.submit(s.publish,drive);self.assertTrue(entered.wait(1))
                with self.assertRaisesRegex(n.SinkError,'upload_already_claimed'):s.publish(drive)
                release.set();self.assertEqual(first.result()['status'],'deleted')
            self.assertEqual(drive.copy_calls,1)

    def test_xtags_base64_percent_encoding_remains_bound(self):
        value=selected();value['xtags']='YWNvbnQ9b3JpZ2luYWw%3D/+'
        self.assertEqual(n.binding(value)['xtags'],value['xtags'])

    def test_sabr_segment_proof_different_source_container_length(self):
        with self.coordinator() as c:
            x=selected(length=900,kind='sabr_reassembled');s=c.begin(x,{'id':VIDEO},output_budget_bytes=8);self.fill(s)
            ledger='0'*64
            for i,data in enumerate((b'1234',b'5678')):
                proof={'number':i,'initialization':i==0,'startTimeMs':0,'endTimeMs':0 if i==0 else 10000,'declaredBytes':4,'byteOffset':i*4,'emittedBytes':4,'sha256':hashlib.sha256(data).hexdigest(),'initDiscardedBytes':0}
                ack=s.segment(proof);ledger=n.chain_hash(ledger,proof);self.assertEqual(ack['ledgerSha256'],ledger)
            record=self.finish(s,container_reassembled=True,encoded_audio_not_reencoded=True,isLive=False,stripDuplicateInit=False,segmentCount=2,segmentLedgerSha256=ledger,endSegmentNum=1,endTimeMs=10000)
            self.assertEqual(record['bytes'],8);meta=n.read(self.root/record['metadata']['path']);self.assertEqual(len(meta['native_segment_proofs']),2)
            self.assertFalse(meta['native_acquisition']['sabr_segment_proof']['original_container_byte_identity_claimed'])

    def test_sabr_without_segments_or_arbitrary_snapshot_cannot_complete(self):
        with self.coordinator() as c:
            s=c.begin(selected(kind='sabr_reassembled'),{'id':VIDEO},output_budget_bytes=8);self.fill(s)
            with self.assertRaises(n.SinkError):self.finish(s)
            with self.assertRaisesRegex(n.SinkError,'sabr_protocol_resume_unproven'):s.verify_resume(s.state()['binding'])

    def test_sabr_wrong_segment_hash_and_timing_rejected(self):
        with self.coordinator() as c:
            s=c.begin(selected(kind='sabr_reassembled'),{'id':VIDEO},output_budget_bytes=8);self.fill(s)
            proof={'number':0,'initialization':True,'startTimeMs':0,'endTimeMs':0,'declaredBytes':4,'byteOffset':0,'emittedBytes':4,'sha256':'0'*64,'initDiscardedBytes':0}
            with self.assertRaisesRegex(n.SinkError,'segment_hash_mismatch'):s.segment(proof)
            proof['sha256']=hashlib.sha256(b'1234').hexdigest();s.segment(proof)
            proof.update(number=1,initialization=False,startTimeMs=1000,endTimeMs=10000,byteOffset=4,sha256=hashlib.sha256(b'5678').hexdigest())
            with self.assertRaisesRegex(n.SinkError,'segment_time_coverage'):s.segment(proof)

    def test_ffprobe_rejects_video_wrong_codec_or_duration(self):
        base={'streams':[{'codec_type':'audio','codec_name':'opus','nb_read_packets':'3'}],'format':{'duration':'10'}}
        for value in ({**base,'streams':base['streams']+[{'codec_type':'video'}]}, {**base,'format':{'duration':'3'}}, {**base,'streams':[{'codec_type':'audio','codec_name':'aac','nb_read_packets':'3'}]}):
            result=subprocess.CompletedProcess([],0,json.dumps(value),'')
            with patch.object(n.subprocess,'run',return_value=result):
                with self.assertRaises(n.SinkError):n.inspect_audio(Path('invented.webm'),selected(),'ffprobe')

    def test_canonical_cooldown_default_denies_without_exception(self):
        core.journal(self.root/'sync/drive_ingest_manifest.jsonl',{'video_id':VIDEO,'source_error_class':'forbidden','retry_not_before_epoch':time.time()+86400})
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'canonical_source_cooldown'):self.begin(c)

    def test_pilot_exact_scope_once_bound_and_request_budget(self):
        x=self.pilot(budget=1)
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'pilot_format_scope'):c.begin(selected(kind='sabr_reassembled'),{'id':VIDEO},output_budget_bytes=8)
            sink=c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
            spent=n.read(self.root/'sync/native_context_pilot_attempt.json');self.assertEqual(spent['attempts_spent'],1)
            with self.assertRaisesRegex(n.SinkError,'source_request_permit_required'):self.fill(sink)
            with self.assertRaisesRegex(n.SinkError,'source_request_identity'):sink.authorize_request({'sourceBindingSha256':'0'*64,'requestSequence':1})
            ack=sink.authorize_request({'sourceBindingSha256':sink.state()['binding_sha256'],'requestSequence':1});self.assertTrue(ack['authorized'])
            with self.assertRaisesRegex(n.SinkError,'source_request_budget'):sink.authorize_request({'sourceBindingSha256':sink.state()['binding_sha256'],'requestSequence':2})
            self.fill(sink)
            self.assertEqual(n.latest_receipts(self.root/'sync/drive_ingest_manifest.jsonl')[x['videoId']]['retry_not_before_epoch'],self.old_deadline)
            state=sink.state();state['state']='deleted';n.atomic(sink.folder/'state.json',state)
            with self.assertRaisesRegex(n.SinkError,'pilot_attempt_spent'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)

    def test_pilot_expiry_changed_code_and_output_budget_denied(self):
        x=self.pilot()
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'pilot_output_budget'):c.begin(x,{'id':x['videoId']},output_budget_bytes=64_000_001)
            pin=Path(self.lease['pilotPolicy']['codePins']['sdk']['path']);pin.write_text('// changed')
            with self.assertRaisesRegex(n.SinkError,'pilot_code_changed'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
            pin.write_text('// invented offline pin');self.lease['pilotPolicy']['expiresAtEpoch']=time.time()-1
            n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
            with self.assertRaisesRegex(n.SinkError,'pilot_expired'):c.begin(x,{'id':x['videoId']},output_budget_bytes=8)

    def test_new_refusal_overrides_exception_preserves_longer_prior_deadline(self):
        x=self.pilot()
        with self.coordinator() as c:
            sink=c.begin(x,{'id':x['videoId']},output_budget_bytes=8)
            sink.authorize_request({'sourceBindingSha256':sink.state()['binding_sha256'],'requestSequence':1})
            sink.retain('rate_limited')
            with self.assertRaisesRegex(n.SinkError,'source_cooldown'):sink.authorize_request({'sourceBindingSha256':sink.state()['binding_sha256'],'requestSequence':2})
            value=n.latest_receipts(self.root/'sync/drive_ingest_manifest.jsonl')[x['videoId']]
            self.assertGreaterEqual(value['retry_not_before_epoch'],self.old_deadline);self.assertEqual(value['native_browser_refusals'],3)
            self.assertTrue((self.root/'sync/STOP_DRIVE_INGEST').exists())

    def test_automated_context_enum_and_sidecar_provenance(self):
        selected_format=self.pilot()
        self.lease['pilotPolicy']['acceptedContext']='unreviewed_context'
        n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
        with self.coordinator() as c:
            with self.assertRaisesRegex(n.SinkError,'pilot_scope'):
                c.begin(selected_format,{'id':selected_format['videoId']},output_budget_bytes=8)
            self.assertFalse((self.root/'sync/native_context_pilot_attempt.json').exists())
            self.lease['pilotPolicy']['acceptedContext']='automated_dedicated_chromium'
            n.atomic(self.root/'sync/native_batch_lease.json',self.lease)
            sink=c.begin(selected_format,{'id':selected_format['videoId']},output_budget_bytes=8)
            sink.authorize_request({'sourceBindingSha256':sink.state()['binding_sha256'],'requestSequence':1})
            self.fill(sink)
            ledger='0'*64
            for number,data in enumerate((b'1234',b'5678')):
                proof={'number':number,'initialization':number==0,'startTimeMs':0,'endTimeMs':0 if number==0 else 1570961,
                    'declaredBytes':4,'byteOffset':number*4,'emittedBytes':4,'sha256':hashlib.sha256(data).hexdigest(),'initDiscardedBytes':0}
                ledger=sink.segment(proof)['ledgerSha256']
            c.probe=lambda *_:{**probe(None,None,None),'duration_seconds':1570.961}
            record=self.finish(sink,container_reassembled=True,encoded_audio_not_reencoded=True,isLive=False,stripDuplicateInit=False,
                segmentCount=2,segmentLedgerSha256=ledger,endSegmentNum=1,endTimeMs=1570961)
            provenance=n.read(self.root/record['metadata']['path'])['native_acquisition']['provenance']
            self.assertEqual(provenance,{'context_kind':'automated_dedicated_chromium','basis':'resource_owner_lease_policy',
                'pilot_policy_kind':'accepted_chrome_sabr_single_fullfile_v1','native_lease_id':'native-test'})
            self.assertNotIn('profile',json.dumps(provenance));self.assertNotIn('cookie',json.dumps(provenance))

if __name__=='__main__':unittest.main()
