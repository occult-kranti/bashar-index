"""Read a verified native body's HTTP EOF clock without confusing it with QC.

No media reads, network, policy mutation or Source authorization. A coordinator
may use a later proven body to order its local health observations; item holds
and authoritative provider restrictions remain the coordinator's responsibility.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

SHA=re.compile(r'[0-9a-f]{64}\Z')
ID=re.compile(r'[A-Za-z0-9_-]{11}\Z')


class CompletionClockHold(ValueError):
    pass


def need(value, code):
    if not value:
        raise CompletionClockHold(code)


def epoch(value):
    return type(value) in (int,float) and math.isfinite(value) and value>0


def checked(pin):
    need(isinstance(pin,dict) and type(pin.get('bytes')) is int and 0<pin['bytes']<=2_000_000
         and isinstance(pin.get('path'),str) and isinstance(pin.get('sha256'),str)
         and SHA.fullmatch(pin['sha256']),'native_clock_pin_schema')
    with Path(pin['path']).open('rb') as f:
        raw=f.read(2_000_001)
    need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'native_clock_pin_changed')
    value=json.loads(raw)
    need(isinstance(value,dict),'native_clock_document_schema')
    return value


def completed_native_body(transfer, receipt):
    """Bind contiguous direct HTTP ranges to an already verified native pair.

    The returned clock is the last protocol EOF, before local ingest/QC/Drive.
    Unsupported redirect/prefix evidence never becomes an invented success.
    """
    need(isinstance(transfer,dict) and isinstance(receipt,dict),'native_clock_input_schema')
    total=receipt.get('bytes');digest=receipt.get('sha256');video=receipt.get('video_id')
    quality=receipt.get('native_validation');binding=receipt.get('native_format_binding');meta=receipt.get('metadata')
    need(receipt.get('status') in ('verified','deleted') and type(total) is int and 0<total<=2_000_000_000
         and isinstance(digest,str) and SHA.fullmatch(digest) and isinstance(video,str) and ID.fullmatch(video)
         and isinstance(binding,dict) and binding.get('videoId')==video and binding.get('contentLength')==total
         and binding.get('audioOnly') is True and binding.get('noDRM') is True,'native_clock_verified_pair_required')
    need(isinstance(meta,dict) and isinstance(meta.get('drive_id'),str) and meta['drive_id']
         and isinstance(receipt.get('drive_id'),str) and receipt['drive_id'] and meta['drive_id']!=receipt['drive_id'],
         'native_clock_distinct_pair_required')
    need(isinstance(receipt.get('md5'),str) and re.fullmatch('[0-9a-f]{32}',receipt['md5'])
         and type(meta.get('bytes')) is int and meta['bytes']>0
         and isinstance(meta.get('md5'),str) and re.fullmatch('[0-9a-f]{32}',meta['md5'])
         and isinstance(meta.get('sha256'),str) and SHA.fullmatch(meta['sha256'])
         and isinstance(receipt.get('remote'),str) and '/' in receipt['remote']
         and meta.get('remote')==receipt['remote'].rpartition('/')[0]+'/'+video+'.info.json',
         'native_clock_paired_metadata_proof_required')
    need(isinstance(quality,dict) and quality.get('quality_state')=='complete_native_audio'
         and quality.get('strict_probe_passed') is True and quality.get('audio_streams')==1
         and quality.get('video_streams')==0 and type(quality.get('packet_count')) is int and quality['packet_count']>0,
         'native_clock_strict_quality_required')
    need(transfer.get('whole_file')=={'bytes':total,'sha256':digest} and transfer.get('whole_source_bytes')==total,
         'native_clock_whole_file_binding')
    need(transfer.get('selected_request_equal') is True and transfer.get('final_response_equal') is True
         and transfer.get('Native_HTTP_positive_equality_eligible') is True and transfer.get('redirects')==[]
         and transfer.get('response_status') in (200,206),
         'native_clock_direct_literal_binding_required')
    need(all(type(transfer.get(k)) is int and transfer[k]==0 for k in ('retries','metadata_requests','browser_starts','WPC_requests')),
         'native_clock_no_extra_route_required')
    prefix=transfer.get('prefix');rows=transfer.get('range_responses');finished=transfer.get('actual_HttpFD_finished')
    need(isinstance(prefix,dict) and type(prefix.get('bytes')) is int and 0<=prefix['bytes']<total
         and isinstance(prefix.get('sha256'),str) and SHA.fullmatch(prefix['sha256'])
         and (prefix['bytes'] or prefix['sha256']==hashlib.sha256(b'').hexdigest()),'native_clock_prefix_binding')
    need(isinstance(rows,list) and 0<len(rows)<=256 and type(transfer.get('wire_requests_attempted')) is int
         and transfer['wire_requests_attempted']==len(rows),'native_clock_range_inventory')
    offset=prefix['bytes'];obtained=0;last=0;uri=None
    for index,row in enumerate(rows,1):
        need(isinstance(row,dict) and row.get('kind')=='range_response' and row.get('range_number')==index,
             'native_clock_range_schema')
        start=row.get('response_start');end=row.get('response_end');requested=row.get('requested_end')
        need(type(start) is int and type(end) is int and type(requested) is int
             and start==row.get('requested_start')==offset and start<=end<total
             and end==row.get('expected_response_end')==min(requested,total-1)
             and row.get('response_total')==row.get('expected_total')==total,'native_clock_contiguous_ranges')
        length=end-start+1
        need(row.get('response_status') in (200,206) and (row['response_status']==206 or start==0 and end==total-1 and len(rows)==1)
             and row.get('protocol_eof') is True and row.get('body_bytes_obtained')==row.get('response_content_length')==length
             and isinstance(row.get('body_sha256'),str) and SHA.fullmatch(row['body_sha256'])
             and row.get('retry_after_header_count')==0 and row.get('selected_request_equal') is True
             and row.get('final_response_equal') is True,'native_clock_complete_bound_response')
        selected=row.get('selected_URI_sha256')
        need(isinstance(selected,str) and SHA.fullmatch(selected) and selected==row.get('response_URI_sha256')
             and (uri is None or selected==uri),'native_clock_same_selected_request')
        uri=selected
        times=[row.get(k) for k in ('request_started_at_epoch','response_observed_at_epoch','last_read_at_epoch','completed_at_epoch')]
        need(all(epoch(t) for t in times) and last<=times[0]<=times[1]<=times[2]<=times[3],
             'native_clock_ordered_HTTP_EOF_required')
        last=times[-1];offset=end+1;obtained+=length
    need(offset==total and transfer.get('new_source_bytes_obtained')==obtained and prefix['bytes']+obtained==total
         and isinstance(finished,dict) and finished.get('status')=='finished'
         and finished.get('downloaded_bytes')==finished.get('total_bytes')==total,'native_clock_full_HttpFD_completion')
    qc=quality.get('strict_quality_completed_at_epoch')
    need(epoch(qc) and qc>=last,'native_clock_QC_after_body_required')
    return dict(video_id=video,body_completed_at_epoch=last,quality_completed_at_epoch=qc,
                bytes=total,sha256=digest,range_count=len(rows),clock_basis='last_contiguous_HTTP_protocol_EOF',
                native_HTTP_positive_equality_eligible=True)


def later_verified_native_pairs(handoff_pin, latest_refusal_epoch):
    """Return only later full-body clocks from this exact closed, released run.

    Pins are immutable metadata. A missing or inconsistent proof raises a local
    CompletionClockHold; it is never a new remote refusal or permission reset.
    """
    need(type(latest_refusal_epoch) in (int,float) and math.isfinite(latest_refusal_epoch) and latest_refusal_epoch>=0,
         'native_clock_refusal_epoch')
    handoff=checked(handoff_pin);closure=handoff.get('owned_closure');grant=handoff.get('root_grant')
    need(isinstance(closure,dict) and closure.get('closed') is True and closure.get('owned_job_empty') is True
         and closure.get('errors')==[] and isinstance(grant,dict),'native_clock_closed_owned_run_required')
    release=checked(handoff['actual_release']);resource=release.get('released_owned_resource_row')
    need(release.get('status')=='released' and isinstance(resource,dict) and resource.get('state')=='released'
         and resource.get('root_grant_sha256')==grant.get('sha256'),'native_clock_matching_release_required')
    result=checked(handoff['actual_batch_result'])
    need(result.get('root_grant_sha256')==grant.get('sha256') and result.get('all_source_threads_returned') is True
         and result.get('all_publisher_threads_returned') is True,'native_clock_finished_threads_required')
    pairs=handoff.get('pairs');need(isinstance(pairs,list) and len(pairs)<=96,'native_clock_pair_inventory')
    selected=[];seen=set();home=Path(handoff_pin['path']).resolve().parent.parent
    for pair in pairs:
        video=pair.get('video_id');need(isinstance(video,str) and ID.fullmatch(video) and video not in seen,'native_clock_unique_pair')
        seen.add(video)
        need(any(r.get('video_id')==video and r.get('status')=='paired_verified_deleted' for r in result.get('results',[])),
             'native_clock_actual_paired_result_required')
        pins={key:pair[key] for key in ('range_transfer','canonical_receipt')}
        for key,name in (('range_transfer','range-transfer.json'),('canonical_receipt','publication-receipt.json')):
            need(Path(pins[key]['path']).resolve()==home/'runtime/observations'/video/name,'native_clock_exact_observation_path')
        receipt=checked(pins['canonical_receipt']);transfer=checked(pins['range_transfer'])
        need(pair.get('audio_Drive_ID')==receipt.get('drive_id') and pair.get('metadata_Drive_ID')==receipt.get('metadata',{}).get('drive_id')
             and pair.get('audio_bytes')==receipt.get('bytes') and pair.get('audio_md5')==receipt.get('md5')
             and pair.get('native_format_binding')==receipt.get('native_format_binding'),'native_clock_handoff_pair_binding')
        clock=completed_native_body(transfer,receipt)
        if clock['body_completed_at_epoch']>latest_refusal_epoch:
            selected.append({**clock,'range_transfer':pins['range_transfer'],'canonical_receipt':pins['canonical_receipt']})
    return dict(handoff=handoff_pin,latest_refusal_epoch=latest_refusal_epoch,pairs=selected,
                Source=0,Drive=0,provider_history_mutated=False)
