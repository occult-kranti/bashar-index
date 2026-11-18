"""Inactive V5 policy: immutable V4 history plus serial native HTTP outcomes.

No I/O, requests, identity changes or retries. Only a separate Root admission can
apply the narrowly reviewed inherited synthetic-breaker exception. An HTTP403 is
an access refusal; it is never relabeled as a server HTTP429 rate-limit response.
"""
from copy import deepcopy
import math,re
import importlib.util
from pathlib import Path
_v4_spec=importlib.util.spec_from_file_location('owned_native_http_v4_frozen',Path(__file__).with_name('native_http_policy_v4_frozen.py'))
v4=importlib.util.module_from_spec(_v4_spec);_v4_spec.loader.exec_module(v4)
POLICY='native-http-consecutive-transfer-v5'
LIMIT=3
MAX_OUTCOMES=50000
PARENT_CENSORED_CODES={'parent_censored_bootstrap_deadline','parent_censored_job_deadline'}
PolicyError=v4.PolicyError
endpoint=v4.endpoint
def classify_http_failure(*args,**kwargs):
    event=v4.classify_http_failure(*args,**kwargs)
    if event['status']==403 and (event['retry_after_state']!='absent' or event['retry_after_requires_review']):
        event['action']='global_stop';event['retry_after_requires_review']=True
    return event
global_failure_event=v4.global_failure_event
parse_retry_after=v4.parse_retry_after
SHA=v4.SHA
ID=v4.ID

def need(value,code):
    if not value:raise PolicyError(code)

def quarantines(raw):
    v4._state(raw['state'])
    return sorted({r['event']['video_id'] for r in raw['state']['events'].values() if r['event']['status']==403 and r['event']['action']!='diagnostic'})

def empty_state(raw_v4,review_sha256,inherited_v4_sha256,inherited_consecutive_tail):
    need(isinstance(raw_v4,dict) and raw_v4.get('schema_version')==1,'v4_envelope')
    v4._state(raw_v4['state']);need(SHA.fullmatch(review_sha256) and SHA.fullmatch(inherited_v4_sha256),'review_sha')
    return {'schema_version':5,'policy':POLICY,'inherited_v4_envelope':deepcopy(raw_v4),'root_review_sha256':review_sha256,'inherited_v4_sha256':inherited_v4_sha256,'inherited_consecutive_tail':deepcopy(inherited_consecutive_tail),'outcomes':{},'next_sequence':1,'circuit_break':None}

def full_transfer_event(video_id,proof):
    v4._video(video_id)
    keys={'finished_count','finished_bytes','audio_bytes_written','known_selected_size','format_identity','worker_sha256','selected_metadata_sha256','selected_request_equal','final_response_equal','response_status','selection_validated','strict_quality','quality_proof_sha256','quality_module_sha256'}
    need(isinstance(proof,dict) and set(proof)==keys,'unsafe_transfer_fields')
    need(proof['finished_count']==1 and type(proof['audio_bytes_written']) is int and 0<proof['audio_bytes_written']==proof['finished_bytes']==proof['known_selected_size']<=2_000_000_000,'full_transfer_bytes')
    need(proof['format_identity']==v4._format(proof['format_identity']) and proof['format_identity'].get('filesize')==proof['known_selected_size'],'transfer_format_binding')
    need(SHA.fullmatch(proof['worker_sha256']) and SHA.fullmatch(proof['selected_metadata_sha256']),'transfer_code_metadata_binding')
    need(proof['selected_request_equal'] is True and proof['final_response_equal'] is True and proof['selection_validated'] is True and type(proof['response_status']) is int and 200<=proof['response_status']<300,'transfer_http_binding')
    quality=proof['strict_quality']
    need(isinstance(quality,dict) and set(quality)=={'quality_state','strict_probe_passed','audio_streams','video_streams','packet_count','container_duration_seconds','source_duration_seconds','codec'},'unsafe_quality_fields')
    need(quality['quality_state']=='complete_native_audio' and quality['strict_probe_passed'] is True and quality['audio_streams']==1 and quality['video_streams']==0 and type(quality['packet_count']) is int and quality['packet_count']>0 and quality['codec'] in {'aac','opus'},'strict_quality_required')
    duration=quality['container_duration_seconds'];expected=quality['source_duration_seconds']
    need(type(duration) in (int,float) and type(expected) in (int,float) and math.isfinite(duration) and math.isfinite(expected) and duration>0 and expected>0 and abs(duration-expected)<=max(2,expected*.002),'quality_duration')
    need(SHA.fullmatch(proof['quality_proof_sha256']) and SHA.fullmatch(proof['quality_module_sha256']),'quality_code_binding')
    return {'kind':'full_native_http_transfer_observed','video_id':video_id,'proof':deepcopy(proof)}

def refusal_event(event):
    v4._event(event);event=deepcopy(event)
    if event['status']==403 and (event['retry_after_state']!='absent' or event['retry_after_requires_review']):event.update(action='global_stop',retry_after_requires_review=True)
    return {'kind':'http_refusal','video_id':event['video_id'],'event':event}

def local_event(video_id,code):
    v4._video(video_id);need(isinstance(code,str) and re.fullmatch(r'[a-z0-9_]{1,80}',code),'unsafe_local_code')
    return {'kind':'local_non_media_outcome','video_id':video_id,'code':code}

def validate_outcome(value):
    need(isinstance(value,dict),'invalid_outcome');kind=value.get('kind')
    if kind=='full_native_http_transfer_observed':need(value==full_transfer_event(value.get('video_id'),value.get('proof')),'transfer_event')
    elif kind=='http_refusal':need(set(value)=={'kind','video_id','event'} and value==refusal_event(value['event']),'refusal_event')
    elif kind=='local_non_media_outcome':need(set(value)=={'kind','video_id','code'} and value==local_event(value['video_id'],value['code']),'local_event')
    else:raise PolicyError('unknown_outcome_kind')
    return value

def state(value):
    need(isinstance(value,dict) and set(value)=={'schema_version','policy','inherited_v4_envelope','root_review_sha256','inherited_v4_sha256','inherited_consecutive_tail','outcomes','next_sequence','circuit_break'},'invalid_state_fields')
    need(value['schema_version']==5 and value['policy']==POLICY,'policy_mismatch');v4._state(value['inherited_v4_envelope']['state']);need(SHA.fullmatch(value['root_review_sha256']) and SHA.fullmatch(value['inherited_v4_sha256']),'review_sha')
    tail=value['inherited_consecutive_tail'];need(isinstance(tail,list) and len(tail)<=20,'invalid_inherited_tail')
    for row in tail:
        need(set(row)=={'attempt_sha256','v4_event_id','video_id','at_epoch'} and SHA.fullmatch(row['attempt_sha256']),'unsafe_inherited_tail')
        old=value['inherited_v4_envelope']['state']['events'].get(row['v4_event_id']);need(old is not None and old['event']['action']=='item_quarantine' and old['event']['video_id']==row['video_id'] and old['at_epoch']==row['at_epoch'],'inherited_tail_binding')
    need(len({row['attempt_sha256'] for row in tail})==len(tail),'duplicate_inherited_attempt')
    need(isinstance(value['outcomes'],dict) and len(value['outcomes'])<=MAX_OUTCOMES,'outcome_limit')
    sequences=[]
    for key,row in value['outcomes'].items():
        need(SHA.fullmatch(key) and set(row)=={'sequence','attempt_sha256','at_epoch','outcome'},'unsafe_outcome_row');need(SHA.fullmatch(row['attempt_sha256']),'attempt_sha');v4._epoch(row['at_epoch']);validate_outcome(row['outcome']);sequences.append(row['sequence'])
    need(sorted(sequences)==list(range(1,len(sequences)+1)) and value['next_sequence']==len(sequences)+1,'serial_outcome_order')
    if value['circuit_break'] is not None:need(isinstance(value['circuit_break'],dict) and value['circuit_break'].get('reason') in {'three_consecutive_distinct_native_attempt_403','immediate_global_refusal','contradictory_attempt_outcome'},'invalid_circuit')
    return value

def reduce_outcomes(value):
    streak=[(row['attempt_sha256'],row['v4_event_id']) for row in value['inherited_consecutive_tail']];failed={x[0] for x in streak};succeeded=set();censored=set();trip=None
    if len(streak)>=LIMIT:trip={'reason':'three_consecutive_distinct_native_attempt_403','outcome_ids':[x[1] for x in streak[-LIMIT:]],'at_epoch':value['inherited_consecutive_tail'][-1]['at_epoch']}
    for key,row in sorted(value['outcomes'].items(),key=lambda pair:pair[1]['sequence']):
        outcome=row['outcome'];attempt=row['attempt_sha256'];kind=outcome['kind']
        if kind=='full_native_http_transfer_observed':
            if attempt in failed or attempt in censored:trip=trip or {'reason':'contradictory_attempt_outcome','outcome_ids':[key],'at_epoch':row['at_epoch']}
            elif attempt not in succeeded:succeeded.add(attempt);streak=[]
        elif kind=='http_refusal':
            event=outcome['event']
            if event['action']=='global_stop':trip=trip or {'reason':'immediate_global_refusal','outcome_ids':[key],'at_epoch':row['at_epoch']}
            elif event['action']=='item_quarantine':
                if attempt in succeeded:trip=trip or {'reason':'contradictory_attempt_outcome','outcome_ids':[key],'at_epoch':row['at_epoch']}
                if attempt not in failed:
                    failed.add(attempt);streak.append((attempt,key))
                    if len(streak)>=LIMIT:trip=trip or {'reason':'three_consecutive_distinct_native_attempt_403','outcome_ids':[x[1] for x in streak[-LIMIT:]],'at_epoch':row['at_epoch']}
        elif kind=='local_non_media_outcome' and outcome['code'] in PARENT_CENSORED_CODES:
            censored.add(attempt)
            if attempt in succeeded:trip=trip or {'reason':'contradictory_attempt_outcome','outcome_ids':[key],'at_epoch':row['at_epoch']}
        # Format/extractor/bootstrap/local verification failures never reset.
    return {'consecutive_distinct_403':len(streak),'trip':trip}

def apply_outcome(value,outcome,outcome_id,attempt_sha256,at_epoch):
    state(value);validate_outcome(outcome);v4._epoch(at_epoch);need(SHA.fullmatch(outcome_id) and SHA.fullmatch(attempt_sha256),'outcome_binding')
    old=value['outcomes'].get(outcome_id)
    if old is not None:
        need(old['outcome']==outcome and old['attempt_sha256']==attempt_sha256,'outcome_id_collision');return deepcopy(value)
    need(outcome['video_id'] not in quarantines(value['inherited_v4_envelope']),'inherited_quarantined_target')
    need(len(value['outcomes'])<MAX_OUTCOMES,'outcome_limit')
    need(all(row['outcome']['video_id']==outcome['video_id'] for row in value['outcomes'].values() if row['attempt_sha256']==attempt_sha256),'attempt_identity_collision')
    media=[x for x in value['outcomes'].values() if x['outcome']['kind']!='local_non_media_outcome']
    if outcome['kind']!='local_non_media_outcome' and media:need(at_epoch>=max(x['at_epoch'] for x in media),'late_outcome_order_unproven')
    result=deepcopy(value);result['outcomes'][outcome_id]={'sequence':result['next_sequence'],'attempt_sha256':attempt_sha256,'at_epoch':at_epoch,'outcome':deepcopy(outcome)};result['next_sequence']+=1
    result['circuit_break']=result['circuit_break'] or reduce_outcomes(result)['trip'];return result

def authorized_review(value,review,candidate):
    if not isinstance(review,dict):return False
    required={'review_sha256','allowed_video_ids','quarantined_video_ids','timeline_evidence_sha256s','historical_global_event_ids_covered','root_override_authorized','inherited_v4_sha256','inherited_consecutive_tail'}
    if not required<=set(review):return False
    need(review.get('root_scope_kind')=='finite_immutable_cohort' and all(isinstance(review.get(k),str) and SHA.fullmatch(review[k]) for k in ('cohort_manifest_sha256','frame_map_sha256')),'finite_manifest_review_required')
    allowed=review['allowed_video_ids'];old=value['inherited_v4_envelope']['state'];old_globals={k for k,x in old['events'].items() if x['event']['action']=='global_stop'}
    need(all(old['events'][k]['historical'] for k in old_globals),'cannot_override_observed_global_refusal')
    circuit=old['circuit_break']
    if circuit is not None:
        need(all(old['events'][k]['event']['action']=='item_quarantine' and old['events'][k]['event']['retry_after_state']=='absent' and old['events'][k]['event']['retry_after_requires_review'] is False for k in circuit['event_ids']),'cannot_override_server_directed_or_ambiguous_hold')
    need(review['review_sha256']==value['root_review_sha256'] and review['inherited_v4_sha256']==value['inherited_v4_sha256'] and review['inherited_consecutive_tail']==value['inherited_consecutive_tail'],'review_binding')
    need(isinstance(allowed,list) and 0<len(allowed)==len(set(allowed))<=1280 and all(ID.fullmatch(x) for x in allowed),'finite_manifest_scope_required')
    need(review['quarantined_video_ids']==quarantines(value['inherited_v4_envelope']) and not set(allowed)&set(review['quarantined_video_ids']),'review_cannot_retry_quarantines')
    need(set(review['historical_global_event_ids_covered'])==old_globals,'historical_global_review_required')
    need(len(review['timeline_evidence_sha256s'])>=2 and all(SHA.fullmatch(x) for x in review['timeline_evidence_sha256s']),'two_independent_timeline_proofs_required')
    return review['root_override_authorized'] is True and candidate in allowed

def status(value,now_epoch,*,historical_review=None,candidate_video_id=None):
    state(value);v4._epoch(now_epoch)
    if candidate_video_id is not None:v4._video(candidate_video_id)
    authorized=authorized_review(value,historical_review,candidate_video_id)
    held=set(quarantines(value['inherited_v4_envelope']))
    for row in value['outcomes'].values():
        outcome=row['outcome']
        if outcome['kind']=='http_refusal' and outcome['event']['status']==403 and outcome['event']['action']!='diagnostic':held.add(outcome['video_id'])
        if outcome['kind']=='local_non_media_outcome' and outcome['code'] in PARENT_CENSORED_CODES:held.add(outcome['video_id'])
    future=any(x['at_epoch']>now_epoch for x in value['outcomes'].values());circuit=value['circuit_break'] or reduce_outcomes(value)['trip'];stopped=not authorized or bool(circuit) or future
    return {'global_stop':stopped,'dispatch_allowed':bool(candidate_video_id and not stopped and candidate_video_id not in held),'item_quarantined':candidate_video_id in held,'quarantined_video_ids':sorted(held),'circuit_break':deepcopy(circuit),'consecutive_distinct_403':reduce_outcomes(value)['consecutive_distinct_403'],'inherited_v4_circuit_break':deepcopy(value['inherited_v4_envelope']['state']['circuit_break']),'inherited_v4_history_retained':True,'root_review_exception_applied':authorized,'clock_regressed':future}
