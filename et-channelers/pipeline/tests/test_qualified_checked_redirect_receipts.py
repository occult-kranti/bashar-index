"""Synthetic paired proofs only. No Source, Drive, media or tool processes."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import urlencode
from pipeline import qualified_edition_receipts as receipts
from pipeline.tests.test_qualified_edition_receipts import receipt_fixture,reseal,streaming_receipt

FIXTURE=Path(__file__).with_name('fixtures')/'qualified_checked_redirect_http.json'

def prospective_http():return json.loads(FIXTURE.read_bytes())

def redirect_receipt():
 record=streaming_receipt(receipt_fixture());payload=record['qualification']['payload'];source=payload['source_file']
 http=prospective_http();size=source['bytes']
 identity={'id':['selected-asset'],'itag':['18'],'clen':[str(size)],'lmt':['1234567'],
           'mime':['video/mp4'],'dur':['1.0'],'xtags':['lang=en'],'expire':['1999999999']}
 query=urlencode({k:v[0] for k,v in identity.items()})
 original='https://r1.example.googlevideo.com/videoplayback?'+query
 final=original.replace('r1.example','r2.example');original_sha=receipts.sha(original.encode());final_sha=receipts.sha(final.encode())
 http.update(selected_url_sha256=original_sha,request_url_sha256=original_sha,final_url_sha256=final_sha,
             body_sha256=source['sha256'])
 for key in ('content_length','received_bytes','written_bytes','exact_on_write_limit'):http[key]=size
 http['redirect_chain'][0].update(declared_source_bytes=size,request_url_sha256=original_sha,
     final_url_sha256=final_sha,location_sha256=final_sha,identity_query_sha256=receipts.sha(receipts.encoded(identity)))
 payload['source_http']=http;payload['selection']['uri_sha256']=original_sha
 return reseal(record)

class CheckedRedirectReceiptTests(unittest.TestCase):
 def setUp(self):
  self.enterContext(patch('socket.socket.connect',side_effect=AssertionError('Source forbidden')))
  self.enterContext(patch('subprocess.Popen',side_effect=AssertionError('process forbidden')))
  self.record=redirect_receipt()
 def validate(self,record):return receipts.validate(record,remote_base='etdrive:04 Audio')
 def test_final_response_extent_is_supported_only_by_the_corresponding_policy(self):
  record=deepcopy(self.record)
  http=record['qualification']['payload']['source_http']
  http.update(transport_contract=receipts.CDN_FINAL_LENGTH_CONTRACT,
              redirect_policy_artifact={'sha256':receipts.CDN_FINAL_LENGTH_POLICY_SHA,'bytes':7338})
  http['redirect_chain'][0].update(schema_version=2,declared_source_bytes=None,extent_basis='final_http_content_length')
  self.validate(reseal(record))
  for field,value in (('declared_source_bytes',2048),('extent_basis','estimated')):
   invalid=deepcopy(record);invalid['qualification']['payload']['source_http']['redirect_chain'][0][field]=value
   with self.subTest(field=field),self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  invalid=deepcopy(record);invalid['qualification']['payload']['source_http']['content_length']-=1
  with self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  invalid=deepcopy(record);invalid['qualification']['payload']['source_http']['transport_contract']=receipts.CDN_TRANSPORT_CONTRACT
  with self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
 def test_capability_accepts_reviewed_actors_rejects_unused_and_foreign_actors(self):
  self.assertEqual(receipts.CDN_ACTOR_CAPABILITY_VERSION,6)
  self.assertEqual(set(receipts.CDN_ACTOR_ARTIFACTS),{
    ('319ab9e92c1cbe2b015d67dd31cc664a9e20c51fe9943bc14abdfd2bd38308f3',54801),
    ('fa3aecb38f3547b8561470f746750f72ca8623a825e4aa0b52d467ac2f9074de',54801),
    ('5cbd39d10752f27f99a99b44005b89b0de74672a48efa7fa0ecbfc316a211201',56232),
    ('bcc11f9d275e95ab8897880467a8d9d35489e9e67e1c0fa62b941e6f9069a520',57064),
    ('70662fce727f22671482fdcbf807627c880b3df0bb0c217c866d4cf2033c2445',57349)})
  for sha,size in receipts.CDN_ACTOR_ARTIFACTS:
   record=deepcopy(self.record);record['qualification']['payload']['source_http']['source_actor_artifact']={'sha256':sha,'bytes':size}
   self.assertFalse(self.validate(reseal(record)).native_promotion)
  for artifact in ({'sha256':'a'*64,'bytes':54801},{'sha256':receipts.CDN_ACTOR_SHA,'bytes':54802},
    {'sha256':'a8390e8c5ef9c775c33460624ab6a12054147bd2fd3074da963b4da50a6dc2bc','bytes':54801},
    {'sha256':'89f7e5d6d98a89367a627a8ba5f37014ab7d0282325c2fbfea20e45f3bb9198c','bytes':56232},
    {'sha256':'bcc11f9d275e95ab8897880467a8d9d35489e9e67e1c0fa62b941e6f9069a520','bytes':57063}):
   record=deepcopy(self.record);record['qualification']['payload']['source_http']['source_actor_artifact']=artifact
   with self.assertRaisesRegex(receipts.ReceiptHold,'pinned_single_CDN_redirect_transport'):self.validate(reseal(record))
 def test_exact_inert_prospective_transport_and_full_paired_receipt_pass(self):
  http=prospective_http();self.assertTrue(receipts.selected_response_binding(http,
      {'uri_sha256':http['selected_url_sha256']},'abcdefghijk',4))
  edition=self.validate(self.record);self.assertFalse(edition.native_promotion);self.assertFalse(edition.text_or_ASR_coverage)
  self.assertNotEqual(self.record['qualification']['payload']['source_http']['request_url_sha256'],
                      self.record['qualification']['payload']['source_http']['final_url_sha256'])
  direct=deepcopy(self.record);http=direct['qualification']['payload']['source_http']
  http.update(final_url_sha256=http['request_url_sha256'],redirect_chain=[],redirect_count=0,media_requests=1)
  self.assertFalse(self.validate(reseal(direct)).native_promotion)
 def test_foreign_artifacts_unknown_contracts_and_legacy_verifier_cannot_claim_bridge(self):
  for name in ('transport_artifact','redirect_policy_artifact','source_actor_artifact'):
   for field,value in (('sha256','a'*64),('bytes',True),('bytes',1)):
    invalid=deepcopy(self.record);invalid['qualification']['payload']['source_http'][name][field]=value
    with self.subTest(name=name,field=field,value=value),self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  for value in (None,'unknown','qualified18_one_checked_googlevideo_redirect_v2'):
   invalid=deepcopy(self.record);invalid['qualification']['payload']['source_http']['transport_contract']=value
   with self.subTest(contract=value),self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  invalid=receipt_fixture();payload=invalid['qualification']['payload'];payload['source_http']=deepcopy(self.record['qualification']['payload']['source_http']);payload['selection']['uri_sha256']=payload['source_http']['selected_url_sha256']
  with self.assertRaisesRegex(receipts.ReceiptHold,'reviewed_CDN_actor_streaming_quality_required'):self.validate(reseal(invalid))
 def test_refusal_RetryAfter_body_before_approval_and_multihop_are_rejected(self):
  cases=[('status',403),('status',429),('status',200),('retry_after_header_count',1),
         ('retry_after_present',True),('observed_before_follow',False),
         ('observation_durable_before_follow',False),('follow_only_after_approval',False),
         ('explicit_redirect_body_reads',1),('redirect_body_writes',1),('maximum_redirects',2)]
  for key,value in cases:
   invalid=deepcopy(self.record);invalid['qualification']['payload']['source_http']['redirect_chain'][0][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  for key,value in (('media_requests',3),('redirect_count',2),('retry_count',1)):
   invalid=deepcopy(self.record);invalid['qualification']['payload']['source_http'][key]=value
   with self.subTest(key=key),self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  invalid=deepcopy(self.record);http=invalid['qualification']['payload']['source_http'];http['redirect_chain']*=2
  with self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
 def test_cross_asset_foreign_host_expired_or_incomplete_version_witness_rejected(self):
  mutations=[('declared_source_bytes',2049),('same_selected_asset_version',False),
    ('request_url_sha256','d'*64),('final_url_sha256','e'*64),('identity_query_sha256','invalid'),
    ('identity_query_fields',receipts.CDN_IDENTITY_FIELDS[1:]),('destination_hostname','r2.googlevideo.com.evil.example'),
    ('destination_hostname','https://r2.googlevideo.com'),('destination_hostname','.googlevideo.com'),
    ('expires_at_epoch',1),('observed_at_epoch',float('inf'))]
  for key,value in mutations:
   invalid=deepcopy(self.record);invalid['qualification']['payload']['source_http']['redirect_chain'][0][key]=value
   with self.subTest(key=key),self.assertRaises((receipts.ReceiptHold,ValueError)):self.validate(reseal(invalid))
  invalid=deepcopy(self.record);invalid['qualification']['payload']['selection']['uri_sha256']='f'*64
  with self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  invalid=deepcopy(self.record);invalid['qualification']['payload']['source_http']['redirect_chain'][0]['private_URI']='forbidden'
  with self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
 def test_bridge_keeps_whole_body_AAC_remote_and_identity_guards(self):
  for section,key,value in (('source_http','written_bytes',2047),('source_http','body_sha256','f'*64),
      ('source_http','headers_checked_before_sink_write',False),('source_http','body_complete',False)):
   invalid=deepcopy(self.record);invalid['qualification']['payload'][section][key]=value
   with self.subTest(key=key),self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  invalid=deepcopy(self.record);invalid['qualification']['payload']['AAC_preservation']['derived_AAC_packets']['packet_sequence_sha256']='f'*64
  with self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  invalid=deepcopy(self.record);invalid['audio']['remote_proof']['drive_id']=invalid['metadata']['remote_proof']['drive_id']
  with self.assertRaises(receipts.ReceiptHold):self.validate(invalid)
  invalid=deepcopy(self.record);invalid['native_canonical_promotion']=True
  with self.assertRaises(receipts.ReceiptHold):self.validate(invalid)
 def test_legacy_single_GET_equality_stays_strict_and_invalid_records_count_zero(self):
  legacy=receipt_fixture();self.assertFalse(self.validate(legacy).native_promotion)
  invalid=deepcopy(legacy);invalid['qualification']['payload']['source_http'].update(redirect_count=1,media_requests=2)
  with self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  invalid=deepcopy(legacy);invalid['qualification']['payload']['source_http']['final_url_sha256']='e'*64
  with self.assertRaises(receipts.ReceiptHold):self.validate(reseal(invalid))
  result=receipts.covered([self.record,reseal(invalid)],targets={'abcdefghijk'},remote_base='etdrive:04 Audio')
  self.assertEqual(result['qualified_youtube_edition_video_ids'],{'abcdefghijk'});self.assertEqual(result['rejected_records'],1)
  self.assertEqual(result['native_audio_increment'],0);self.assertEqual(result['caption_or_ASR_increment'],0)

if __name__=='__main__':unittest.main()
