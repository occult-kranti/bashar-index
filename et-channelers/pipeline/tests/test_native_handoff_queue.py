import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pipeline.native_handoff_queue import NativeHandoffQueue, ProducerTicket, closed_ticket, group_size_for_switch


VID = 'aB01234_bcd'
CHANNEL = 'UC' + 'a' * 22
SHA = 'a'*64


def ticket(i,expiry=1700):
    return ProducerTicket(f'{i:011}',100+i,expiry,1000+i,SHA,SHA,SHA)


class NativeHandoffQueueTests(unittest.TestCase):
    def test_threshold_only_stops_new_admissions_and_preserves_late_draining_tickets(self):
        q=NativeHandoffQueue(group_size=6)
        for i in range(5):
            q.observe(ticket(i))
            self.assertIsNone(q.boundary(1000))
        q.observe(ticket(0))
        self.assertIsNone(q.boundary(1000))
        q.observe(ticket(5))
        first=q.boundary(1000)
        self.assertEqual(first['reason'],'native_handoff_batch_ready')
        q.observe(ticket(6))
        self.assertEqual(q.boundary(1050),first)
        self.assertEqual(len(q.evidence()['tickets']),7)
        self.assertEqual(q.evidence()['native_media_requests'],0)
        self.assertFalse(q.evidence()['counts_as_downloaded'])

    def test_expiry_margin_skips_expired_tickets_and_bounds_short_lived_handoff(self):
        q=NativeHandoffQueue()
        q.observe(ticket(0,1179))
        self.assertIsNone(q.boundary(1000))
        q.observe(ticket(1,1480))
        self.assertEqual(q.boundary(1000)['video_ids'],[f'{1:011}'])
        self.assertEqual(q.boundary(1000)['reason'],'native_handoff_expiry_near')

    def test_measured_switch_cost_and_temporary_memory_pressure_choose_different_boundaries(self):
        self.assertEqual(group_size_for_switch(112,22),16)
        self.assertEqual(group_size_for_switch(29,22),6)
        self.assertEqual(group_size_for_switch(600,22),24)
        q=NativeHandoffQueue()
        for i in range(6):q.observe(ticket(i))
        self.assertIsNone(q.boundary(1000))
        self.assertEqual(q.boundary(1000,producer_memory_idle=True)['reason'],'native_handoff_producer_memory_idle')

    def test_closed_evidence_requires_current_owner_identity_and_zero_selected_requests(self):
        with TemporaryDirectory() as temp:
            job=Path(temp)/VID;job.mkdir()
            def put(name,data):
                raw=json.dumps(data).encode()
                (job/name).write_bytes(raw)
                return hashlib.sha256(raw).hexdigest()
            attempt=put('attempt.json',{'video_id':VID})
            closure={'closed':True,'owned_process_closed':True,'owned_job_empty':True,'job_handle_released':True,'errors':[]}
            put('parent-audit.json',{'video_id':VID,'root_grant_sha256':SHA,'attempt_sha256':attempt,
                'owned_processes_gone':True,'parent_error':None,'owned_closure':closure,'profile_cleanup':{'cleaned':True}})
            safe={'video_id':VID,'native_saved':False,'source_media_GETs':0,'provider_explicit_original_label':True,
                'format_id':'140','fresh_source_identity':{'video_id':VID,'fresh_channel_id':CHANNEL,'expected_channel_id':CHANNEL,'fresh_identity_match':True}}
            result={'status':'native_route_pending','video_id':VID,'safe_native_route':safe,'diagnostics':{'phase':'terminal','media_requests':0}}
            put('result.json',result)
            private={'not_saved':True,'Source_media_GETs':0,'safe_route':safe,'expires_query_literal':['1700'],
                'private_selected_info':{'id':VID,'channel_id':CHANNEL,'filesize':123,'vcodec':'none','format_id':'140','url':'private-test-placeholder'}}
            put('native-route-private.metadata.json',private)
            def selected(grant=SHA):
                return closed_ticket(job,video_id=VID,channel_id=CHANNEL,grant_sha256=grant,attempt_sha256=attempt,closed_at=1000)
            value=selected();self.assertEqual((value.video_id,value.source_bytes),(VID,123))
            self.assertNotIn('private-test-placeholder',repr(value))
            with self.assertRaises(ValueError):selected('b'*64)
            (job/'MEDIA_GO.json').write_bytes(b'{}')
            with self.assertRaises(ValueError):selected()
            (job/'MEDIA_GO.json').unlink()
            result['diagnostics']['media_requests']=1;put('result.json',result)
            with self.assertRaises(ValueError):selected()
