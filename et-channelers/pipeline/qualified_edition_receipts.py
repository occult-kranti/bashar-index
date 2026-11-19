"""Pure AudioExtracts receipt reader. No filesystem or I/O capability.

This category never supplies Native, caption, ASR or original-speaker proof.
Only an exact paired archive with its canonical provenance bytes can count.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,math,re

KIND='qualified_youtube_audio_edition'
ENCODING='canonical-json-utf8-sorted-compact-no-newline-v1'
VERIFIER_SHA='519b5dd2232fa77be1c998763256da320be07b0b8021e71e9cd6978d35e528ec'
LEGACY_CONTRACT='progressive_MP4_AAC_packet_preserving_streamcopy'
PROFILE_CONTRACT='progressive_MP4_AAC_LC_HE_AAC_packet_preserving_streamcopy_v1'
PROFILE_COMPONENT_SHA='5915a2b689de11fed5ea41956f084e55c967c22e6c63b925202e48611ec058a4'
PROFILE_COMPONENT_BYTES=8131
STREAM_CONTRACT='progressive_MP4_AAC_LC_HE_AAC_streaming_packet_preservation_v1'
STREAM_COMPONENT_SHA='f903fddac2f02850d409a4511c897d47a04f976cf38a2ca8924b54d0c24a5f60'
STREAM_COMPONENT_BYTES=18424
CDN_TRANSPORT_CONTRACT='qualified18_one_checked_googlevideo_redirect_v1'
CDN_FINAL_LENGTH_CONTRACT='qualified18_one_checked_googlevideo_redirect_v2'
CDN_TRANSPORT_SHA='a59c8d872a0899be78d470f52f26c6d6ea99bb14cebc1030419b7d2fd5c69773'
CDN_TRANSPORT_ARTIFACTS=((CDN_TRANSPORT_SHA,12266),('a06ab2b1430cb47ab4dfeea89350ad74d3cf83695e0b441d0356c4746282b504',12266))
CDN_POLICY_SHA='4cff87c7539fea300852f6ae62cc623916702bcea961e5fcd2574e5b3913e1e1'
CDN_FINAL_LENGTH_POLICY_SHA='ef405ed76d4d889e02fd32f8b42a5451bea6c94004ede6009989e1592dd657a2'
CDN_ACTOR_SHA='319ab9e92c1cbe2b015d67dd31cc664a9e20c51fe9943bc14abdfd2bd38308f3'
CDN_ACTOR_CAPABILITY_VERSION=7
CDN_ACTOR_ARTIFACTS=((CDN_ACTOR_SHA,54801),
 ('fa3aecb38f3547b8561470f746750f72ca8623a825e4aa0b52d467ac2f9074de',54801),
 ('5cbd39d10752f27f99a99b44005b89b0de74672a48efa7fa0ecbfc316a211201',56232),
 ('bcc11f9d275e95ab8897880467a8d9d35489e9e67e1c0fa62b941e6f9069a520',57064),
 ('70662fce727f22671482fdcbf807627c880b3df0bb0c217c866d4cf2033c2445',57349))
CDN_IDENTITY_FIELDS=['id','itag','clen','lmt','mime','dur','xtags','expire']
SHA=re.compile(r'[0-9a-f]{64}\Z');MD5=re.compile(r'[0-9a-f]{32}\Z')
FLAGS=('original_audio_track_identity_verified','origin_inferred','spoken_language_verified',
       'speaker_identity_verified','recording_edit_identity_verified',
       'full_speech_coverage_verified','native_canonical_promotion',
       'native_HTTP_success_reset_allowed')

class ReceiptHold(ValueError):pass
def need(v,code):
 if not v:raise ReceiptHold(code)
def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
def sha(v):return hashlib.sha256(v).hexdigest()
def file_proof(v):return {'bytes':len(v),'md5':hashlib.md5(v).hexdigest(),'sha256':sha(v)}
def digest(v):return isinstance(v,str) and SHA.fullmatch(v) is not None
def positive(v,limit):return type(v) is int and 0<v<=limit
def finite(v):return type(v) in (int,float) and math.isfinite(v) and v>0
def proof(v,limit):
 need(isinstance(v,dict) and positive(v.get('bytes'),limit) and digest(v.get('sha256')) and
      isinstance(v.get('md5'),str) and MD5.fullmatch(v['md5']),'file_fingerprint')
 return v
def identity(v):
 need(isinstance(v,dict) and all(v.get(k) is False for k in FLAGS) and
      v.get('translation_status')=='unknown' and 'native_quality_state' in v and
      v['native_quality_state'] is None,'explicit_qualified_identity_required')

def artifact_matches(value,expected_sha,expected_bytes):
 return (isinstance(value,dict) and value.get('sha256')==expected_sha and
         type(value.get('bytes')) is int and value['bytes']==expected_bytes)

def selected_response_binding(http,selection,video,size):
 """Only the reviewed actor may attest one checked HTTPS CDN redirect.

 The exact pinned actor/policy checks both private URIs, their same-version
 query identity and expiry before opening the follow. This pure reader sees
 their hashes and the safe witness; it never reconstructs a private URI.
 Receipts without this versioned contract retain literal single-GET equality.
 """
 need(isinstance(http,dict) and http.get('selected_video_id')==video and http.get('selected_format_id')=='18'
      and digest(http.get('selected_url_sha256')) and
      http.get('selected_url_sha256')==http.get('request_url_sha256'),'single_selected_response_binding')
 if 'transport_contract' not in http:
  need(http.get('request_url_sha256')==http.get('final_url_sha256'),'single_selected_response_binding')
  return False
 verified_policy=(
      http.get('transport_contract')==CDN_TRANSPORT_CONTRACT and
      artifact_matches(http.get('redirect_policy_artifact'),CDN_POLICY_SHA,6701)
      or http.get('transport_contract')==CDN_FINAL_LENGTH_CONTRACT and
      artifact_matches(http.get('redirect_policy_artifact'),CDN_FINAL_LENGTH_POLICY_SHA,7338))
 need(verified_policy and
      any(artifact_matches(http.get('transport_artifact'),sha,size) for sha,size in CDN_TRANSPORT_ARTIFACTS) and
      any(artifact_matches(http.get('source_actor_artifact'),sha,size) for sha,size in CDN_ACTOR_ARTIFACTS),
      'pinned_single_CDN_redirect_transport')
 need(selection.get('uri_sha256')==http['selected_url_sha256'] and digest(http.get('final_url_sha256')),
      'selected_URI_hash_binding')
 count=http.get('redirect_count');chain=http.get('redirect_chain')
 need(type(count) is int and count in (0,1) and type(chain) is list and len(chain)==count and
      type(http.get('media_requests')) is int and http['media_requests']==1+count and
      type(http.get('retry_count')) is int and http['retry_count']==0,'one_original_one_follow_no_replay')
 if not count:
  need(http['final_url_sha256']==http['selected_url_sha256'],'literal_no_redirect_response_binding')
  return True
 row=chain[0]
 fields={'schema_version','status','request_url_sha256','location_sha256','final_url_sha256',
         'destination_hostname','retry_after_header_count','retry_after_present','same_selected_asset_version',
         'identity_query_fields','declared_source_bytes','expires_at_epoch','identity_query_sha256',
         'observed_at_epoch','observed_before_follow','maximum_redirects',
         'observation_durable_before_follow','follow_only_after_approval',
         'explicit_redirect_body_reads','redirect_body_writes'}
 need(type(row) is dict and type(row.get('schema_version')) is int,'checked_redirect_proof_schema')
 if row['schema_version']==2 and http['transport_contract']==CDN_FINAL_LENGTH_CONTRACT:
  need(set(row)==fields|{'extent_basis'} and row['extent_basis']=='final_http_content_length' and
       row['declared_source_bytes'] is None and type(http.get('content_length')) is int and
       http['content_length']==size and positive(size,2_000_000_000),'checked_redirect_final_HTTP_extent')
 else:
  need(row['schema_version']==1 and set(row)==fields,'checked_redirect_proof_schema')
  need(type(row.get('declared_source_bytes')) is int and row['declared_source_bytes']==size,
       'checked_redirect_version_extent_expiry')
 need(type(row.get('status')) is int and row['status'] in (301,302,303,307,308) and
      row.get('request_url_sha256')==http['request_url_sha256'] and
      row.get('final_url_sha256')==http['final_url_sha256'] and
      row['final_url_sha256']!=row['request_url_sha256'] and
      digest(row.get('location_sha256')) and digest(row.get('identity_query_sha256')),
      'checked_redirect_asset_binding')
 host=row.get('destination_hostname')
 need(isinstance(host,str) and len(host)<=253 and
      re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+googlevideo\.com',host),
      'checked_HTTPS_Googlevideo_destination')
 need(row.get('identity_query_fields')==CDN_IDENTITY_FIELDS and
      row.get('same_selected_asset_version') is True and
      finite(row.get('observed_at_epoch')) and type(row.get('expires_at_epoch')) is int and
      row['expires_at_epoch']>row['observed_at_epoch'],'checked_redirect_version_extent_expiry')
 need(type(row.get('retry_after_header_count')) is int and row['retry_after_header_count']==0 and
      row.get('retry_after_present') is False and row.get('observed_before_follow') is True and
      row.get('observation_durable_before_follow') is True and row.get('follow_only_after_approval') is True and
      type(row.get('maximum_redirects')) is int and row['maximum_redirects']==1 and
      all(type(row.get(k)) is int and row[k]==0 for k in ('explicit_redirect_body_reads','redirect_body_writes')),
      'durable_redirect_approval_no_RetryAfter_or_body')
 return True

def quality_profiles(q):
 if q.get('quality_contract')==LEGACY_CONTRACT:return {'LC'}
 if q.get('quality_contract')==STREAM_CONTRACT:
  need(artifact_matches(q.get('quality_component_artifact'),STREAM_COMPONENT_SHA,STREAM_COMPONENT_BYTES) and
       artifact_matches(q.get('base_verifier_artifact'),VERIFIER_SHA,10864) and
       q.get('base_verifier_role')=='digest_compatibility_reference_only' and
       q.get('base_verifier_execution_claimed') is False and
       q.get('packet_summary_mode')=='incremental_ffprobe_JSON_one_packet_buffer_v1' and
       q.get('packet_count_bound_basis')=='positive_packet_payload_sizes_sum_not_exceeding_actual_file_bytes' and
       type(q.get('maximum_source_bytes')) is int and q['maximum_source_bytes']==2_000_000_000 and
       positive(q.get('maximum_derived_bytes'),2_000_000_000) and
       type(q.get('maximum_packet_record_bytes')) is int and q['maximum_packet_record_bytes']==65536 and
       type(q.get('maximum_stderr_bytes')) is int and q['maximum_stderr_bytes']==1_000_000 and
       q.get('fixed_packet_count_or_duration_cutoff') is False,
       'pinned_streaming_preservation_component')
  return {'LC','HE-AAC'}
 need(q.get('quality_contract')==PROFILE_CONTRACT and
      artifact_matches(q.get('quality_component_artifact'),PROFILE_COMPONENT_SHA,PROFILE_COMPONENT_BYTES) and
      artifact_matches(q.get('base_verifier_artifact'),VERIFIER_SHA,10864),
      'pinned_profile_preservation_component')
 return {'LC','HE-AAC'}

def quality(q,selection,source_file,derived_file):
 need(isinstance(q,dict) and type(q.get('schema_version')) is int and q['schema_version']==1 and
      q.get('AAC_packet_payload_preserved') is True and q.get('audio_reencode_requested') is False and
      q.get('original_audio_track_identity_verified') is False and
      q.get('spoken_language_verified') is False and q.get('GPU_requested') is False and
      q.get('remuxed_container') is True and q.get('full_speech_coverage_claimed') is False and
      q.get('native_canonical_promotion') is False,'AAC_verifier_result')
 profiles=quality_profiles(q)
 need(q.get('private_muxed_source_file')==source_file and q.get('derived_audio_file')==derived_file and
      q.get('raw_muxed_source_and_packet_proofs_private') is True and
      q.get('cleanup_performed') is False and q.get('Drive_publication_performed') is False,
      'AAC_actual_file_proof_binding')
 a=q.get('source_audio');b=q.get('derived_audio')
 need(isinstance(a,dict) and isinstance(b,dict) and type(a.get('video_streams')) is int and
      type(b.get('video_streams')) is int and a['video_streams']==1 and b['video_streams']==0,
      'source_and_derived_stream_topology')
 for key in ('codec','profile','sample_rate','channels','extradata_sha256'):
  need(key in a and key in b and a[key]==b[key],'AAC_configuration_changed')
 need(a['codec']=='aac' and a['profile'] in profiles and positive(a['sample_rate'],384000) and
      positive(a['channels'],8) and digest(a['extradata_sha256']),'AAC_configuration')
 before=q.get('source_AAC_packets');after=q.get('derived_AAC_packets')
 need(isinstance(before,dict) and isinstance(after,dict),'AAC_packet_summaries')
 count_limit=min(source_file['bytes'],derived_file['bytes']) if q.get('quality_contract')==STREAM_CONTRACT else 200_000
 for key in ('packet_count','packet_payload_bytes','packet_sequence_sha256','skip_samples',
             'discard_padding','padding_sequence_sha256','packet_duration_samples_sha256'):
  need(key in before and key in after and before[key]==after[key],'AAC_packet_sequence_changed')
 need(before.get('algorithm')==after.get('algorithm')=='SHA256_of_ordered_size64be_and_packet_SHA256' and
      positive(before['packet_count'],count_limit) and positive(after['packet_count'],count_limit) and
      positive(before['packet_payload_bytes'],min(source_file['bytes'],derived_file['bytes'])) and
      positive(after['packet_payload_bytes'],min(source_file['bytes'],derived_file['bytes'])) and
      all(digest(before[k]) for k in ('packet_sequence_sha256','padding_sequence_sha256','packet_duration_samples_sha256')),
      'AAC_packet_summary_bound')
 if q.get('quality_contract')==STREAM_CONTRACT:
  need(before['packet_count']<=before['packet_payload_bytes'] and
       after['packet_count']<=after['packet_payload_bytes'],'positive_payload_packet_count_bound')
 need(all(type(v[k]) is int and v[k]>=0 for v in (before,after) for k in ('skip_samples','discard_padding')),
      'AAC_padding_summary')
 tolerance=q.get('duration_tolerance_seconds')
 need(type(tolerance) in (int,float) and math.isfinite(tolerance) and tolerance==.05,'AAC_duration_tolerance')
 need(finite(a.get('duration_seconds')) and finite(b.get('duration_seconds')) and
      abs(a['duration_seconds']-b['duration_seconds'])<=tolerance and
      finite(before.get('packet_duration_sum_seconds')) and finite(after.get('packet_duration_sum_seconds')) and
      abs(before['packet_duration_sum_seconds']-after['packet_duration_sum_seconds'])<=tolerance,'AAC_duration_changed')
 need(abs(a['duration_seconds']-selection['duration_seconds'])<=max(2,selection['duration_seconds']*.002),
      'selected_edition_incomplete_or_changed')

def qualification(q,video,audio,variant):
 need(isinstance(q,dict) and q.get('payload_encoding')==ENCODING and digest(q.get('payload_sha256')),
      'qualification_encoding')
 payload=q.get('payload');need(isinstance(payload,dict) and sha(encoded(payload))==q['payload_sha256'],
                             'qualification_payload_hash')
 artifact=q.get('verifier_artifact')
 preservation=payload.get('AAC_preservation')
 need(isinstance(preservation,dict),'AAC_verifier_result')
 if artifact_matches(artifact,VERIFIER_SHA,10864):
  need(preservation.get('quality_contract')==LEGACY_CONTRACT,'verifier_contract_binding')
  source_limit,derived_limit=100_000_000,50_000_000
 else:
  streaming=artifact_matches(artifact,STREAM_COMPONENT_SHA,STREAM_COMPONENT_BYTES)
  need((streaming or artifact_matches(artifact,PROFILE_COMPONENT_SHA,PROFILE_COMPONENT_BYTES)) and
       artifact_matches(q.get('base_verifier_artifact'),VERIFIER_SHA,10864) and
       preservation.get('quality_contract')==(STREAM_CONTRACT if streaming else PROFILE_CONTRACT) and
       preservation.get('quality_component_artifact')==artifact and
       preservation.get('base_verifier_artifact')==q['base_verifier_artifact'],
       'pinned_AAC_verifier_artifact')
  if streaming:
   quality_profiles(preservation)
   source_limit=2_000_000_000;derived_limit=preservation['maximum_derived_bytes']
  else:source_limit=derived_limit=32_000_000
 identity(payload)
 source=proof(payload.get('source_file'),source_limit)
 derived=proof(payload.get('derived_audio_file'),derived_limit)
 need(source['sha256']==variant and derived==audio,'qualification_file_binding')
 select=payload.get('selection');http=payload.get('source_http')
 need(isinstance(select,dict) and select.get('video_id')==video and select.get('format_id')=='18' and
      select.get('protocol')=='https' and type(select.get('filesize')) is int and select['filesize']==source['bytes'] and
      finite(select.get('duration_seconds')) and select.get('live_status') in {'not_live','was_live'} and
      select.get('has_drm') is False and select.get('is_drc') is False and digest(select.get('metadata_sha256')),
      'exact_selected_recording')
 size=source['bytes']
 cdn_transport=selected_response_binding(http,select,video,size)
 if cdn_transport:need(artifact_matches(artifact,STREAM_COMPONENT_SHA,STREAM_COMPONENT_BYTES),
                       'reviewed_CDN_actor_streaming_quality_required')
 for key in ('content_length','received_bytes','written_bytes','exact_on_write_limit'):
  need(type(http.get(key)) is int and http[key]==size,'full_observed_body_length')
 need(type(http.get('status')) is int and 'content_range' in http and
      (http['status']==200 and http['content_range'] is None or
       http['status']==206 and type(http['content_range']) is list and
       all(type(v) is int for v in http['content_range']) and http['content_range']==[0,size-1,size]), 'full_response_extent')
 need(http.get('body_sha256')==source['sha256'] and http.get('body_complete') is True and
      http.get('headers_checked_before_sink_write') is True and
      type(http.get('finished_count')) is int and http['finished_count']==1 and
      type(http.get('media_requests')) is int and http['media_requests']==(1+http['redirect_count'] if cdn_transport else 1) and
      type(http.get('redirect_count')) is int and (http['redirect_count'] in (0,1) if cdn_transport else http['redirect_count']==0) and
      type(http.get('retry_count')) is int and http['retry_count']==0,'whole_body_no_replay')
 quality(payload.get('AAC_preservation'),select,source,derived)
 return payload

@dataclass(frozen=True)
class QualifiedEdition:
 video_id:str
 channel_dir:str
 variant_id:str
 source_kind:str=KIND
 native_promotion:bool=False
 text_or_ASR_coverage:bool=False

def validate(record,*,remote_base):
 need(isinstance(record,dict) and type(record.get('schema_version')) is int and record['schema_version']==1 and record.get('kind')==KIND and
      record.get('status') in {'verified','deleted'},'qualified_verified_receipt_required')
 video=record.get('video_id');channel=record.get('channel_dir');variant=record.get('variant_id')
 need(isinstance(video,str) and re.fullmatch(r'[A-Za-z0-9_-]{11}',video) and
      isinstance(channel,str) and re.fullmatch(r'[a-z0-9][a-z0-9-]{0,119}',channel) and
      record.get('tab') in {'videos','shorts','streams'} and digest(variant) and
      record.get('source_format_id')=='18' and digest(record.get('root_grant_sha256')),'record_identity')
 identity(record)
 need(record.get('native_count_increment')==0 and type(record.get('native_count_increment')) is int,
      'no_native_count_promotion')
 audio=record.get('audio');metadata=record.get('metadata')
 need(isinstance(audio,dict) and isinstance(metadata,dict),'paired_audio_metadata_required')
 audio_local=proof(audio.get('local_proof'),2_000_000_000);meta_local=proof(metadata.get('local_proof'),2_000_000)
 qualification(record.get('qualification'),video,audio_local,variant)
 provenance=record.get('provenance')
 need(isinstance(provenance,dict) and type(provenance.get('schema_version')) is int and
      provenance['schema_version']==1 and provenance.get('kind')==KIND and
      all(provenance.get(k)==record[k] for k in ('video_id','channel_dir','tab','variant_id','source_format_id')) and
      provenance.get('audio')==audio_local and provenance.get('qualification')==record['qualification'],
      'archived_provenance_content_binding')
 identity(provenance)
 need(file_proof(encoded(provenance))==meta_local,'archived_provenance_file_hash')
 need(isinstance(remote_base,str) and ':' in remote_base and not remote_base.endswith('/'),'remote_base')
 parent=f'{channel}/AudioExtracts/{video}/{variant}';ids=[]
 for part,local,leaf in ((audio,audio_local,'audio-extract.m4a'),(metadata,meta_local,'provenance.json')):
  remote=part.get('remote_proof')
  need(isinstance(remote,dict) and type(remote.get('bytes')) is int and remote['bytes']==local['bytes'] and
       remote.get('md5')==local['md5'] and isinstance(remote.get('drive_id'),str) and bool(remote['drive_id']) and
       remote.get('relative_path')==parent+'/'+leaf and remote.get('remote')==remote_base+'/'+parent+'/'+leaf,
       'actual_paired_remote_proof')
  need('sha256' not in remote,'local_SHA_is_not_observed_remote_SHA')
  ids.append(remote['drive_id'])
 need(len(set(ids))==2,'distinct_paired_Drive_IDs')
 return QualifiedEdition(video,channel,variant)

def covered(records,*,targets,remote_base):
 """Read exact valid private receipts; malformed/legacy shapes contribute zero."""
 ids=set();rejected=0
 for record in records:
  try:
   edition=validate(record,remote_base=remote_base)
   if edition.video_id in targets:ids.add(edition.video_id)
  except (ReceiptHold,TypeError,ValueError,KeyError,OverflowError):rejected+=1
 return {'qualified_youtube_edition_video_ids':ids,'rejected_records':rejected,
         'native_audio_increment':0,'caption_or_ASR_increment':0}
