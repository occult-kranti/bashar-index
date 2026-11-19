from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pipeline import native_completion_clock as m


class NativeCompletionClockTests(unittest.TestCase):
    def fixture(self):
        data=b'abcdefgh';digest=hashlib.sha256(data).hexdigest();uri='a'*64;video='example1234'
        rows=[]
        for i in range(2):
            start=i*4;end=start+3;clock=10+i*4
            rows.append(dict(kind='range_response',range_number=i+1,response_start=start,requested_start=start,
                response_end=end,expected_response_end=end,requested_end=end,response_total=8,expected_total=8,
                response_status=206,protocol_eof=True,body_bytes_obtained=4,response_content_length=4,
                body_sha256=hashlib.sha256(data[start:end+1]).hexdigest(),retry_after_header_count=0,
                selected_request_equal=True,final_response_equal=True,selected_URI_sha256=uri,response_URI_sha256=uri,
                request_started_at_epoch=clock,response_observed_at_epoch=clock+1,last_read_at_epoch=clock+2,completed_at_epoch=clock+3))
        receipt=dict(video_id=video,status='deleted',bytes=8,sha256=digest,md5=hashlib.md5(data).hexdigest(),drive_id='audio-id',
            remote='archive:Audio/creator/Videos/'+video+'/'+video+'.m4a',
            metadata=dict(drive_id='metadata-id',bytes=100,md5='b'*32,sha256='b'*64,
                remote='archive:Audio/creator/Videos/'+video+'/'+video+'.info.json'),
            native_format_binding=dict(videoId=video,contentLength=8,audioOnly=True,noDRM=True),
            native_validation=dict(quality_state='complete_native_audio',strict_probe_passed=True,audio_streams=1,
                video_streams=0,packet_count=10,strict_quality_completed_at_epoch=30))
        transfer=dict(whole_file=dict(bytes=8,sha256=digest),whole_source_bytes=8,selected_request_equal=True,
            final_response_equal=True,Native_HTTP_positive_equality_eligible=True,redirects=[],response_status=206,
            retries=0,metadata_requests=0,browser_starts=0,WPC_requests=0,prefix=dict(bytes=0,sha256=hashlib.sha256(b'').hexdigest()),
            range_responses=rows,wire_requests_attempted=2,new_source_bytes_obtained=8,
            actual_HttpFD_finished=dict(status='finished',downloaded_bytes=8,total_bytes=8))
        return transfer,receipt

    def test_protocol_EOF_is_earlier_than_QC_and_not_inferred_from_it(self):
        transfer,receipt=self.fixture();clock=m.completed_native_body(transfer,receipt)
        self.assertEqual(clock['body_completed_at_epoch'],17)
        self.assertEqual(clock['quality_completed_at_epoch'],30)
        transfer['range_responses'][-1].pop('completed_at_epoch')
        with self.assertRaises(m.CompletionClockHold):m.completed_native_body(transfer,receipt)

    def test_gap_truncation_URI_hash_QC_RA_and_file_mismatch_hold(self):
        transfer,receipt=self.fixture()
        changes=[('response_start',5),('body_bytes_obtained',3),('protocol_eof',False),
                 ('response_URI_sha256','c'*64),('retry_after_header_count',1),('completed_at_epoch',float('nan'))]
        for field,value in changes:
            wrong=deepcopy(transfer);wrong['range_responses'][-1][field]=value
            with self.subTest(field=field),self.assertRaises(m.CompletionClockHold):m.completed_native_body(wrong,receipt)
        wrong=deepcopy(receipt);wrong['sha256']='f'*64
        with self.assertRaises(m.CompletionClockHold):m.completed_native_body(transfer,wrong)
        wrong=deepcopy(receipt);wrong['native_validation']['strict_probe_passed']=False
        with self.assertRaises(m.CompletionClockHold):m.completed_native_body(transfer,wrong)

    def test_owned_prefix_has_exact_remaining_coverage(self):
        transfer,receipt=self.fixture();transfer['prefix']=dict(bytes=4,sha256=hashlib.sha256(b'abcd').hexdigest())
        transfer['range_responses']=transfer['range_responses'][1:];transfer['range_responses'][0]['range_number']=1
        transfer['wire_requests_attempted']=1;transfer['new_source_bytes_obtained']=4
        self.assertEqual(m.completed_native_body(transfer,receipt)['body_completed_at_epoch'],17)

    def test_closed_pinned_API_orders_by_body_not_late_QC_and_rejects_changed_pins(self):
        transfer,receipt=self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp);obs=home/'runtime/observations'/receipt['video_id'];obs.mkdir(parents=True)
            def write(path,value):
                path.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(value).encode();path.write_bytes(raw)
                return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            tp=write(obs/'range-transfer.json',transfer);rp=write(obs/'publication-receipt.json',receipt)
            result=write(home/'runtime/result.json',dict(root_grant_sha256='e'*64,all_source_threads_returned=True,
                all_publisher_threads_returned=True,results=[dict(video_id=receipt['video_id'],status='paired_verified_deleted')]))
            release=write(home/'runtime/release.json',dict(status='released',released_owned_resource_row=dict(state='released',root_grant_sha256='e'*64)))
            handoff=write(home/'handoff/final.json',dict(owned_closure=dict(closed=True,owned_job_empty=True,errors=[]),
                root_grant=dict(sha256='e'*64),actual_release=release,actual_batch_result=result,pairs=[dict(
                    video_id=receipt['video_id'],range_transfer=tp,canonical_receipt=rp,audio_Drive_ID=receipt['drive_id'],
                    metadata_Drive_ID=receipt['metadata']['drive_id'],audio_bytes=8,audio_md5=receipt['md5'],native_format_binding=receipt['native_format_binding'])]))
            self.assertEqual(len(m.later_verified_native_pairs(handoff,16)['pairs']),1)
            self.assertEqual(m.later_verified_native_pairs(handoff,18)['pairs'],[])
            (obs/'range-transfer.json').write_text('{}')
            with self.assertRaisesRegex(m.CompletionClockHold,'pin_changed'):m.later_verified_native_pairs(handoff,16)


if __name__=='__main__':unittest.main()
