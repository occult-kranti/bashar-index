"""Publisher text-only scope, admission, no-retry transport and paired-proof ordering."""
from dataclasses import replace
import io
import json
import unittest
from unittest.mock import patch
import zipfile

from pipeline import publisher_caption_batch as caption

RAW=b'WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nSource caption text.\n'
ROBOTS=b'User-agent: *\nDisallow:\n'


def candidate(letter='a',episode='123'):
    return caption.Candidate(letter*11,'creator','Buzzsprout-'+episode,
        'https://www.buzzsprout.com/42/'+episode+'/transcript.vtt','Public episode title',
        *[char*64 for char in 'bcde'])


class Fixture:
    def __init__(self,count=3):
        self.items=tuple(candidate(char,str(123+i)) for i,char in enumerate('agh'[:count]))
        self.scope=caption.scope_sha256(self.items);self.now=1000.;self.events=[];self.fetches=[]
        self.raw=[];self.cleanups=[];self.holds=[];self.responses={};self.bad_receipt=False
        self.grant=caption.Grant('caption-lease','f'*64,self.scope,caption.sha(ROBOTS),1100.,True,True,True)
        self.proof=caption.GuardProof('caption-lease','f'*64,self.scope,'e'*64,self.now,
            15_700_000_000,15_700_000_000,20_000_000_000,caption.RESERVATION,True,True)

    def guard(self,stage,item):return replace(self.proof,checked_at_epoch=self.now)
    def event(self,value):self.events.append(value)
    def fetch(self,request):
        self.fetches.append(request)
        self.assert_request=request
        return self.responses.get(request.url,caption.FetchResponse(request.url,200,RAW,self.now,content_length=len(RAW)))
    def retain(self,item,raw,proof):self.raw.append((item.video_id,raw,proof))
    def publish(self,item,artifacts):
        out={}
        for name,proof in artifacts.proofs().items():
            filename='publisher-captions.zip' if name=='bundle' else 'provenance.json'
            out[name]={'local_proof':proof,'remote_proof':{'bytes':proof['bytes'],'md5':proof['md5'],
                       'drive_id':'fixture-'+name,'relative_path':artifacts.relative_parent+'/'+filename}}
        if self.bad_receipt:out['provenance']['remote_proof']['md5']='0'*32
        return out
    def cleanup(self,item,receipt):
        assert self.events[-1]['kind']=='pair_verified'
        assert self.events[-1]['video_id']==item.video_id
        self.cleanups.append(item.video_id)
    def hold(self,value):
        self.holds.append(value)
        return {'history_preserved':True,'retry_not_before_epoch':value['retry_not_before_epoch']}
    def batch(self,**changes):
        values=dict(robots_raw=ROBOTS,robots_checked_at_epoch=999.,guard=self.guard,event=self.event,
            fetch=self.fetch,retain_raw=self.retain,publish=self.publish,cleanup=self.cleanup,
            record_hold=self.hold,clock=lambda:self.now)
        values.update(changes)
        return caption.CaptionBatch(self.items,self.grant,**values)


class PublisherCaptionTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch('socket.socket.connect',side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen',side_effect=AssertionError('process forbidden')))

    def test_three_sequential_text_requests_and_durable_pair_before_cleanup(self):
        f=Fixture();result=f.batch().run()
        self.assertEqual('complete',result['status']);self.assertEqual(3,result['transport_invocations'])
        self.assertEqual(3,len(f.raw));self.assertEqual(3,len(f.cleanups));self.assertFalse(f.holds)
        self.assertTrue(all(x['state']=='verified' for x in result['outcomes']))
        self.assertEqual(['request_started','pair_verified']*3,[x['kind'] for x in f.events])
        for request in f.fetches:
            self.assertEqual(('GET',0,0,1_000_000),(request.method,request.retries,request.redirects,request.maximum_bytes))
            self.assertEqual(1030.,request.deadline_epoch)
        self.assertEqual((0,0,0),(result['audio_requests'],result['YouTube_requests'],result['ASR_jobs']))

    def test_bundle_retains_raw_and_normalized_sources_with_qualified_labels(self):
        c=candidate();pair=caption.build_artifacts(c,RAW,'f'*64)
        with zipfile.ZipFile(io.BytesIO(pair.bundle)) as z:
            self.assertIsNone(z.testzip());self.assertEqual(RAW,z.read('raw.vtt'))
            self.assertIn('Source caption text.',z.read('transcript.txt').decode())
            provenance=json.loads(z.read('provenance.json'))
            self.assertEqual({'raw.vtt','segments.json','transcript.txt','provenance.json','manifest.json'},set(z.namelist()))
        self.assertEqual('publisher_source',provenance['content_kind'])
        self.assertEqual('unknown',provenance['manual_vs_automatic'])
        self.assertFalse(provenance['track_language_verified']);self.assertFalse(provenance['alignment_reviewed'])
        self.assertFalse(provenance['native_youtube_caption']);self.assertIsNone(provenance['audio_binding'])
        self.assertEqual(c.native_audio_receipt_sha256,provenance['associated_native_audio_receipt_sha256'])
        self.assertLess(len(RAW)+len(pair.bundle)+len(pair.provenance)+1_000_000,caption.RESERVATION)
        self.assertNotIn(b'/Users/',pair.provenance)

    def test_first403_preserves_retry_after_and_stops_all_remaining_requests(self):
        f=Fixture();c=f.items[0]
        f.responses[c.caption_url]=caption.FetchResponse(c.caption_url,403,b'',1000.,retry_after='172800')
        result=f.batch().run()
        self.assertEqual(1,len(f.fetches));self.assertEqual(['held','pending','pending'],[x['state'] for x in result['outcomes']])
        self.assertEqual(173800.,f.holds[0]['retry_not_before_epoch']);self.assertFalse(f.holds[0]['automatic_retry'])
        self.assertEqual(caption.sha(c.caption_url.encode()),f.holds[0]['request_url_sha256'])
        self.assertFalse(f.cleanups)

    def test429_invalid_retry_after_requires_review_and_hold_write_failure_is_explicit(self):
        f=Fixture();c=f.items[0]
        f.responses[c.caption_url]=caption.FetchResponse(c.caption_url,429,b'',1000.,retry_after='unparseable')
        result=f.batch().run()
        self.assertTrue(f.holds[0]['retry_after_requires_review']);self.assertEqual(1,len(f.fetches))
        f=Fixture();c=f.items[0];f.responses[c.caption_url]=caption.FetchResponse(c.caption_url,403,b'',1000.)
        result=f.batch(record_hold=lambda record:None).run()
        self.assertEqual('hold_persistence_failed',result['outcomes'][0]['reason'])
        self.assertEqual(1,len(f.fetches))

    def test_retry_after_optional_whitespace_is_preserved_and_empty_requires_review(self):
        for raw,minimum,review in [('172800 ',173800.,False),(' \t172800\t',173800.,False),('',87400.,True),(' \t',87400.,True)]:
            f=Fixture();c=f.items[0]
            f.responses[c.caption_url]=caption.FetchResponse(c.caption_url,403,b'',1000.,retry_after=raw)
            f.batch().run()
            self.assertGreaterEqual(f.holds[0]['retry_not_before_epoch'],minimum)
            self.assertEqual(review,f.holds[0]['retry_after_requires_review'])

    def test_post_fetch_revocation_preserves_accepted_raw_before_stopping_work(self):
        f=Fixture();writes=[]
        def guard(stage,item):
            writes.append(stage)
            return replace(f.proof,root_stop=stage!='source')
        result=f.batch(guard=guard).run()
        self.assertEqual(['source','write'],writes)
        self.assertEqual(1,len(f.fetches));self.assertEqual(1,len(f.raw))
        self.assertEqual(RAW,f.raw[0][1]);self.assertEqual('retained',result['outcomes'][0]['state'])
        self.assertFalse(f.cleanups);self.assertFalse(any(e['kind']=='pair_verified' for e in f.events))

    def test_disabled_grant_host_hold_stale_or_inactive_reservation_prevent_get(self):
        cases=[dict(enabled=False),dict(scope_sha256='0'*64),dict(reservation_bytes=9_000_000)]
        for changes in cases:
            f=Fixture();f.grant=replace(f.grant,**changes)
            result=f.batch().run();self.assertEqual(0,len(f.fetches));self.assertEqual('held',result['status'])
        for changes in [dict(host_hold_until_epoch=1001.),dict(root_stop=True),dict(lease_active=False),
                        dict(reservation_active=False),dict(managed_projected_bytes=16_000_000_001),
                        dict(drive_hold_until_epoch=1001.),dict(physical_free_bytes=1_999_999_999)]:
            f=Fixture();f.proof=replace(f.proof,**changes);f.batch().run();self.assertFalse(f.fetches)

    def test_actual_robots_disallow_expiry_or_changed_pin_prevents_get(self):
        f=Fixture();denied=b'User-agent: *\nDisallow: /42/\n';f.grant=replace(f.grant,robots_sha256=caption.sha(denied))
        result=f.batch(robots_raw=denied).run();self.assertFalse(f.fetches);self.assertEqual('held',result['status'])
        f=Fixture();f.batch(robots_checked_at_epoch=-100000.).run();self.assertFalse(f.fetches)
        with self.assertRaises(caption.CaptionBatchError):Fixture().batch(robots_raw=b'changed')

    def test_oversize_redirect_deadline_or_extra_wire_request_never_publish(self):
        changes=[dict(body=b'x'*(caption.MAX_RAW+1)),dict(final_url='https://other.invalid/transcript.vtt'),
                 dict(finished_at_epoch=1031.),dict(wire_GETs=2),dict(wire_GETs=True),dict(redirects_followed=1),
                 dict(complete_body=False)]
        for value in changes:
            f=Fixture();c=f.items[0]
            response=caption.FetchResponse(c.caption_url,200,RAW,1000.)
            f.responses[c.caption_url]=replace(response,**value)
            result=f.batch().run();self.assertEqual(1,len(f.fetches));self.assertFalse(f.cleanups)
            self.assertEqual('held',result['status'])

    def test_malformed_vtt_is_retained_without_alternate_format_or_retry(self):
        f=Fixture();c=f.items[0]
        f.responses[c.caption_url]=caption.FetchResponse(c.caption_url,200,b'not webvtt',1000.)
        result=f.batch().run();self.assertEqual(1,len(f.raw));self.assertEqual(1,len(f.fetches))
        self.assertEqual('retained',result['outcomes'][0]['state']);self.assertFalse(f.cleanups)

    def test_pair_hash_mismatch_or_receipt_write_failure_preserves_raw(self):
        f=Fixture();f.bad_receipt=True
        result=f.batch().run();self.assertEqual('retained',result['outcomes'][0]['state']);self.assertFalse(f.cleanups)
        self.assertFalse(any(e['kind']=='pair_verified' for e in f.events))
        f=Fixture()
        def event(value):
            if value['kind']=='pair_verified':raise OSError('private message')
            f.events.append(value)
        result=f.batch(event=event).run();self.assertFalse(f.cleanups)
        self.assertEqual('retained',result['outcomes'][0]['state'])
        self.assertNotIn('private message',str(result))

    def test_cleanup_failure_keeps_verified_truth_and_stops_new_fetches(self):
        f=Fixture()
        def cleanup(*args):raise OSError('sharing')
        result=f.batch(cleanup=cleanup).run()
        self.assertEqual('verified',result['outcomes'][0]['state'])
        self.assertEqual('retained',result['outcomes'][0]['local_cleanup'])
        self.assertEqual(1,len(f.fetches));self.assertEqual('held',result['status'])

    def test_request_journal_failure_precedes_network_and_batch_is_one_shot(self):
        f=Fixture()
        def event(value):raise OSError('cannot durably spend request')
        batch=f.batch(event=event);result=batch.run();self.assertFalse(f.fetches)
        self.assertEqual(0,result['transport_invocations'])
        with self.assertRaises(caption.CaptionBatchError):batch.run()

    def test_plan_rejects_audio_youtube_credentials_duplicates_and_wrong_episode(self):
        for url in ['https://www.buzzsprout.com/42/123.mp3','https://youtube.com/42/123/transcript.vtt',
                    'https://user@www.buzzsprout.com/42/123/transcript.vtt','https://www.buzzsprout.com/42/124/transcript.vtt']:
            with self.subTest(url=url),self.assertRaises(caption.CaptionBatchError):replace(candidate(),caption_url=url)
        with self.assertRaises(caption.CaptionBatchError):caption.scope_sha256((candidate(),candidate()))

    def test_injected_adaptor_error_cannot_export_raw_path_token_or_url(self):
        f=Fixture()
        def guard(*args):raise caption.CaptionBatchError('PRIVATE https://host.invalid/token C:/private')
        result=f.batch(guard=guard).run()
        self.assertEqual('publisher_caption_operation_failed',result['outcomes'][0]['reason'])
        self.assertNotIn('PRIVATE',str(result));self.assertFalse(f.fetches)

    def test_local_sha256_is_explicitly_distinct_from_observed_remote_md5_size_id(self):
        f=Fixture(count=1);result=f.batch().run()
        proof=next(e for e in f.events if e['kind']=='pair_verified')['proofs']['bundle']
        self.assertIn('sha256',proof['local_proof']);self.assertNotIn('sha256',proof['remote_proof'])
        self.assertEqual('verified',result['outcomes'][0]['state'])

    def test_complete_first404_or410_continues_other_distinct_pointers_without_retry(self):
        for status in [404,410]:
            f=Fixture();c=f.items[0]
            f.responses[c.caption_url]=caption.FetchResponse(c.caption_url,status,b'not found',1000.,content_type='text/plain',content_length=9)
            result=f.batch().run()
            self.assertEqual('complete',result['status']);self.assertEqual(3,len(f.fetches))
            self.assertEqual(['unavailable','verified','verified'],[x['state'] for x in result['outcomes']])
            self.assertEqual(2,len(f.cleanups));self.assertFalse(f.holds)
            self.assertTrue(any(e['kind']=='http_observation' and e['status']==status for e in f.events))
            self.assertTrue(any(e['kind']=='item_unavailable' and e['automatic_retry'] is False for e in f.events))

    def test404_retry_after_incomplete_or_unknown5xx_still_holds_remaining_scope(self):
        for change in [dict(status=404,retry_after='60'),dict(status=404,complete_body=False),dict(status=500)]:
            f=Fixture();c=f.items[0]
            f.responses[c.caption_url]=replace(caption.FetchResponse(c.caption_url,200,RAW,1000.),**change)
            result=f.batch().run()
            self.assertEqual('held',result['status']);self.assertEqual(1,len(f.fetches))
            self.assertEqual(['held','pending','pending'],[x['state'] for x in result['outcomes']])

    def test_accepted200_with_retry_after_still_preserves_raw_before_host_hold(self):
        f=Fixture();item=f.items[0]
        f.responses[item.caption_url]=caption.FetchResponse(item.caption_url,200,RAW,1000.,retry_after='60')
        result=f.batch().run()
        self.assertEqual(1,len(f.raw));self.assertEqual(RAW,f.raw[0][1]);self.assertEqual(1,len(f.holds))
        self.assertEqual('retained',result['outcomes'][0]['state']);self.assertFalse(f.cleanups)


if __name__=='__main__':unittest.main()
