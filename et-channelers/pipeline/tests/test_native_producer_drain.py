import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pipeline import native_producer_drain as drain


SHA='a'*64
CHANNEL='UC'+'a'*22


def put(path,value):
    path.write_text(json.dumps(value),encoding='utf-8')
    return drain.pin(path)


def closed_job(jobs,video):
    job=jobs/video;job.mkdir()
    attempt=put(job/'attempt.json',{'video_id':video})
    put(job/'parent-audit.json',{'video_id':video,'root_grant_sha256':SHA,'attempt_sha256':attempt['sha256'],
        'owned_processes_gone':True,'parent_error':None,'profile_cleanup':{'cleaned':True},
        'owned_closure':{'closed':True,'owned_process_closed':True,'owned_job_empty':True,'job_handle_released':True,'errors':[]}})
    safe={'video_id':video,'native_saved':False,'source_media_GETs':0,'provider_explicit_original_label':True,'format_id':'140',
        'fresh_source_identity':{'video_id':video,'fresh_channel_id':CHANNEL,'expected_channel_id':CHANNEL,'fresh_identity_match':True}}
    put(job/'result.json',{'status':'native_route_pending','video_id':video,'safe_native_route':safe,
        'diagnostics':{'phase':'terminal','media_requests':0}})
    put(job/'native-route-private.metadata.json',{'not_saved':True,'Source_media_GETs':0,'safe_route':safe,
        'expires_query_literal':['1700'],'private_selected_info':{'id':video,'channel_id':CHANNEL,'filesize':123,
        'vcodec':'none','format_id':'140','url':'private-fixture-not-exported'}})
    return job


class ProducerDrainTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.jobs=self.root/'profile'/'jobs';self.jobs.mkdir(parents=True)
        self.ids=[f'{i:011}' for i in range(6)]
        self.registry={'video_ids':self.ids,'candidates':[{'video_id':v,'expected_channel_id':CHANNEL} for v in self.ids]}
        self.frame=self.root/'frame';self.frame.mkdir()
        self.kernel=self.root/'kernel.py';self.kernel.write_text('# inert import-path fixture\n')
        self.control=self.frame/'scope_drain.py'
        self.control.write_text("from pathlib import Path\ndef issue(frame,scope):\n p=Path(frame)/'actual-local-control.json'\n with p.open('x') as f:f.write(scope)\n return {'control':str(p),'Source_requests':0,'active_body_cancelled':False}\n")
        put(self.frame/'settings.json',{'code_pins':[drain.pin(self.control)]})

    def monitor(self):return drain.ClosedProducerMonitor(self.jobs,self.registry,grant_sha256=SHA,group_size=6)

    def request(self,monitor,boundary):
        return drain.request_once(self.frame,monitor,boundary,scope_sha256=SHA,
            kernel_code=self.kernel,kernel_sha256=drain.pin(self.kernel)['sha256'])

    def test_actual_closed_validator_caches_immutable_tickets_and_one_installed_drain(self):
        for video in self.ids:closed_job(self.jobs,video)
        monitor=self.monitor()
        with patch.object(drain,'closed_ticket',wraps=drain.closed_ticket) as validate:
            boundary=monitor.poll(1000)
            self.assertEqual(monitor.poll(1002),boundary)
            self.assertEqual(validate.call_count,6)
        self.assertEqual(monitor.evidence()['immutable_child_validations'],6)
        self.assertNotIn('private-fixture-not-exported',repr(monitor.evidence()))
        result=self.request(monitor,boundary)
        self.assertEqual(result['status'],'admission_only_drain_requested')
        self.assertFalse(result['active_body_cancelled']);self.assertEqual(result['Source_requests'],0)
        self.assertEqual(self.request(monitor,boundary),result)  # no second control invocation
        self.assertEqual((self.frame/'actual-local-control.json').read_text(),SHA)

    def test_active_missing_is_pending_but_corrupt_or_changed_closed_evidence_holds(self):
        monitor=self.monitor();self.assertIsNone(monitor.poll(1000))
        job=closed_job(self.jobs,self.ids[0]);monitor.poll(1001)
        original=(job/'result.json').read_bytes()
        (job/'result.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'changed_closed'):monitor.poll(1002)
        (job/'result.json').write_bytes(original)
        other=closed_job(self.jobs,self.ids[1]);(other/'parent-audit.json').write_text('{')
        with self.assertRaises(json.JSONDecodeError):self.monitor().poll(1002)

    def test_closed_missing_private_or_new_media_go_is_not_silently_skipped(self):
        job=closed_job(self.jobs,self.ids[0]);private=job/'native-route-private.metadata.json'
        raw=private.read_bytes();private.unlink()
        with self.assertRaises(FileNotFoundError):self.monitor().poll(1000)
        private.write_bytes(raw);monitor=self.monitor();monitor.poll(1000)
        put(job/'MEDIA_GO.json',{})
        with self.assertRaisesRegex(ValueError,'acquired_media'):monitor.poll(1001)

    def test_unresolved_intent_and_control_tamper_prevent_replay(self):
        for video in self.ids:closed_job(self.jobs,video)
        monitor=self.monitor();boundary=monitor.poll(1000)
        def failed(*a,**k):raise PermissionError('local control failure')
        with self.assertRaises(PermissionError):
            drain.request_once(self.frame,monitor,boundary,scope_sha256=SHA,kernel_code=self.kernel,
                kernel_sha256=drain.pin(self.kernel)['sha256'],request=failed)
        self.assertFalse((self.frame/'actual-local-control.json').exists())
        with self.assertRaisesRegex(ValueError,'unresolved'):self.request(monitor,boundary)
        (self.frame/'native-producer-drain-intent.json').unlink()
        self.control.write_text('# changed\n')
        with self.assertRaisesRegex(ValueError,'control_changed'):self.request(monitor,boundary)

    def test_wrong_grant_or_channel_and_expired_tickets_never_request_drain(self):
        for video in self.ids:closed_job(self.jobs,video)
        monitor=self.monitor();self.assertIsNone(monitor.poll(1600))
        self.assertFalse((self.frame/'actual-local-control.json').exists())
        self.registry['candidates'][0]['expected_channel_id']='UC'+'b'*22
        with self.assertRaisesRegex(ValueError,'Unqualified'):self.monitor().poll(1000)

    def test_restarted_cli_reuses_final_proof_without_polling_or_replaying(self):
        self.registry['profile']='profile'
        put(self.frame/'registry.json',self.registry)
        put(self.frame/'root-grant.ACTIVE.json',{})
        actual_grant=drain.pin(self.frame/'root-grant.ACTIVE.json')['sha256']
        for video in self.ids:
            job=closed_job(self.jobs,video)
            audit=json.loads((job/'parent-audit.json').read_bytes())
            audit['root_grant_sha256']=actual_grant;put(job/'parent-audit.json',audit)
        monitor=drain.ClosedProducerMonitor(self.jobs,self.registry,grant_sha256=actual_grant,group_size=6)
        boundary=monitor.poll(1000);self.request(monitor,boundary)
        args=['--frame',str(self.frame),'--private-root',str(self.root),'--scope-sha256',SHA,
            '--kernel-code',str(self.kernel),'--kernel-sha256',drain.pin(self.kernel)['sha256'],'--threshold','6']
        with patch.object(drain.ClosedProducerMonitor,'poll',side_effect=AssertionError('must not poll')):
            with patch.object(drain,'request_installed_drain',side_effect=AssertionError('must not replay')):
                self.assertEqual(drain.main(args),0)


if __name__=='__main__':unittest.main()
