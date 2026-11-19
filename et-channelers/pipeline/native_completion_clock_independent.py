"""Independent strict direct-pair health clocks; immutable v1 proof stays unchanged."""
import math
from pathlib import Path
import re

if __package__:
    from . import native_completion_clock as strict
else:
    import native_completion_clock_strict_v1 as strict

CompletionClockHold = strict.CompletionClockHold


def _pair_clock(pair,home,result):
    video=pair['video_id']
    strict.need(any(row.get('video_id')==video and row.get('status')=='paired_verified_deleted'
        for row in result.get('results',[])),'native_clock_actual_paired_result_required')
    pins={key:pair[key] for key in ('range_transfer','canonical_receipt')}
    for key,name in (('range_transfer','range-transfer.json'),('canonical_receipt','publication-receipt.json')):
        strict.need(Path(pins[key]['path']).resolve()==home/'runtime/observations'/video/name,
            'native_clock_exact_observation_path')
    receipt=strict.checked(pins['canonical_receipt']);transfer=strict.checked(pins['range_transfer'])
    strict.need(pair.get('audio_Drive_ID')==receipt.get('drive_id')
        and pair.get('metadata_Drive_ID')==receipt.get('metadata',{}).get('drive_id')
        and pair.get('audio_bytes')==receipt.get('bytes') and pair.get('audio_md5')==receipt.get('md5')
        and pair.get('native_format_binding')==receipt.get('native_format_binding'),'native_clock_handoff_pair_binding')
    return {**strict.completed_native_body(transfer,receipt),**pins}


def independent_later_verified_native_pairs(handoff_pin,latest_refusal_epoch):
    """Bad/unsupported individual proof supplies no health, not a new refusal.

    Closed ownership, release, returned threads and unique global inventory are
    still mandatory. Every accepted individual pair uses unchanged v1 direct
    HTTP equality, contiguous range/EOF/hash/QC/canonical receipt checks.
    """
    strict.need(type(latest_refusal_epoch) in (int,float) and math.isfinite(latest_refusal_epoch)
        and latest_refusal_epoch>=0,'native_clock_refusal_epoch')
    handoff=strict.checked(handoff_pin);closure=handoff.get('owned_closure');grant=handoff.get('root_grant')
    strict.need(isinstance(closure,dict) and closure.get('closed') is True and closure.get('owned_job_empty') is True
        and closure.get('errors')==[] and isinstance(grant,dict),'native_clock_closed_owned_run_required')
    release=strict.checked(handoff['actual_release']);resource=release.get('released_owned_resource_row')
    strict.need(release.get('status')=='released' and isinstance(resource,dict) and resource.get('state')=='released'
        and resource.get('root_grant_sha256')==grant.get('sha256'),'native_clock_matching_release_required')
    result=strict.checked(handoff['actual_batch_result'])
    strict.need(result.get('root_grant_sha256')==grant.get('sha256') and result.get('all_source_threads_returned') is True
        and result.get('all_publisher_threads_returned') is True,'native_clock_finished_threads_required')
    pairs=handoff.get('pairs')
    strict.need(isinstance(pairs,list) and len(pairs)<=96 and isinstance(result.get('results'),list),'native_clock_pair_inventory')
    if 'paired_count' in handoff:strict.need(handoff['paired_count']==len(pairs),'native_clock_pair_count_binding')
    seen=set()
    for pair in pairs:
        video=pair.get('video_id') if isinstance(pair,dict) else None
        strict.need(isinstance(video,str) and strict.ID.fullmatch(video) and video not in seen,'native_clock_unique_pair')
        seen.add(video)
    selected=[];skipped=[];valid=0;not_later=0;home=Path(handoff_pin['path']).resolve().parent.parent
    for pair in pairs:
        try:clock=_pair_clock(pair,home,result)
        except (strict.CompletionClockHold,OSError,ValueError,TypeError,KeyError,AttributeError) as error:
            code=str(error) if isinstance(error,strict.CompletionClockHold) and re.fullmatch(r'native_clock_[a-zA-Z0-9_]+',str(error)) else None
            skipped.append({'video_id':pair['video_id'],'status':'no_health_proof','error_class':type(error).__name__,
                'safe_code':code,'new_refusal_inferred':False})
            continue
        valid+=1
        if clock['body_completed_at_epoch']>latest_refusal_epoch:selected.append(clock)
        else:not_later+=1
    return {'handoff':handoff_pin,'latest_refusal_epoch':latest_refusal_epoch,'pairs':selected,
        'global_pair_inventory_validated':True,'direct_pairs_validated':valid,'valid_direct_pairs_not_later':not_later,
        'unsupported_or_invalid_pairs':skipped,'Source':0,'Drive':0,'provider_history_mutated':False,
        'new_refusal_inferred':False,'Native_HTTP_positive_created':False}


def later_verified_native_pairs(handoff_pin,latest_refusal_epoch):
    """Versioned-file compatibility entry; v1's original module is not changed."""
    return independent_later_verified_native_pairs(handoff_pin,latest_refusal_epoch)
