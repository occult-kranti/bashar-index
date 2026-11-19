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
 need(isinstance(http,dict) and http.get('selected_video_id')==video and http.get('selected_format_id')=='18' and
      digest(http.get('selected_url_sha256')) and
      http.get('selected_url_sha256')==http.get('request_url_sha256')==http.get('final_url_sha256'),
      'single_selected_response_binding')
 size=source['bytes']
 for key in ('content_length','received_bytes','written_bytes','exact_on_write_limit'):
  need(type(http.get(key)) is int and http[key]==size,'full_observed_body_length')
 need(type(http.get('status')) is int and 'content_range' in http and
      (http['status']==200 and http['content_range'] is None or
       http['status']==206 and type(http['content_range']) is list and
       all(type(v) is int for v in http['content_range']) and http['content_range']==[0,size-1,size]), 'full_response_extent')
 need(http.get('body_sha256')==source['sha256'] and http.get('body_complete') is True and
      http.get('headers_checked_before_sink_write') is True and
      type(http.get('finished_count')) is int and http['finished_count']==1 and
      type(http.get('media_requests')) is int and http['media_requests']==1 and
      type(http.get('redirect_count')) is int and http['redirect_count']==0 and
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
