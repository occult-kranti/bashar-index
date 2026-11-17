"""Leased language-ID-only review. No acquisition, text generation or deletion."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time
import zipfile

RATE=16000
PROFILE='language-id-review-v2'
WINDOWS=[[181504,661504],[12681472,13161472],[17625088,18080512]]
CONFIG={'sample_rate':RATE,'source_windows_samples':WINDOWS,'maximum_calls':3,
        'max_window_samples':30*RATE,'max_total_samples':90*RATE,'max_pcm_bytes':5760000,
        'min_vad_samples':2*RATE,'minimum_probability':.90,'minimum_margin':.20,
        'decode_mode':'one_sequential_pass_before_model','max_frame_seconds':.25,
        'timestamp_tolerance_samples':800,'max_origin_seconds':.1,'max_source_duration_seconds':1600,
        'max_source_duration_delta_seconds':2,'max_wall_seconds':600,'max_output_bytes':1000000,
        'language_detection_segments':1,'vad_filter':False,'text_generation':False,
        'metadata_hold_overridden':False,'changes_collection_completion':False}


class ReviewError(RuntimeError):pass


def need(ok,code):
    if not ok:raise ReviewError(code)


def encoded(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
def digest(v):return hashlib.sha256(encoded(v)).hexdigest()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    need(Path(path).stat().st_size<=2000000,'document_size')
    return json.loads(Path(path).read_text(encoding='utf-8'))


def interval_evidence(windows,vad,total):
    need(windows==WINDOWS,'window_scope')
    need(len(windows)<=CONFIG['maximum_calls'] and sum(b-a for a,b in windows)<=CONFIG['max_total_samples'],'window_budget')
    cursor=0
    for a,b in vad:
        need(type(a) is int and type(b) is int and cursor<=a<b<=total,'vad_intervals')
        cursor=b
    rows=[];previous=0
    for a,b in windows:
        need(type(a) is int and type(b) is int and previous<=a<b<=total and b-a<=CONFIG['max_window_samples'],'window_bounds')
        overlap=sum(max(0,min(b,y)-max(a,x)) for x,y in vad)
        need(overlap>=CONFIG['min_vad_samples'],'insufficient_window_vad')
        rows.append({'source_samples':[a,b],'duration_seconds':(b-a)/RATE,'vad_overlap_samples':overlap,'vad_overlap_seconds':overlap/RATE})
        previous=b
    return rows


def normalize_score(value):
    language,probability,all_scores=value
    need(isinstance(language,str) and re.fullmatch(r'[a-z]{2,3}',language),'language_code')
    p=float(probability);scores={}
    for code,score in all_scores:
        need(isinstance(code,str) and re.fullmatch(r'[a-z]{2,3}',code) and code not in scores,'language_scores')
        number=float(score)
        need(math.isfinite(number) and 0<=number<=1,'language_scores')
        scores[code]=number
    need(len(scores)>=2 and language in scores and math.isfinite(p) and 0<=p<=1,'language_scores')
    need(abs(scores[language]-p)<=1e-6 and p+1e-6>=max(scores.values()),'language_score_identity')
    margin=p-max(v for k,v in scores.items() if k!=language)
    return {'language':language,'probability':p,'top_two_margin':float(margin),
            'strong_window_language_evidence':bool(p>=CONFIG['minimum_probability'] and margin>=CONFIG['minimum_margin']),
            'top_five':[{'language':k,'probability':v} for k,v in sorted(scores.items(),key=lambda pair:pair[1],reverse=True)[:5]],
            'lexical_meaning_confirmed':False,'full_recording_language_confirmed':False}


def require_binding(lease,binding):
    need(lease.get('language_review')==binding,'language_review_binding')


def validate_selection(selection,job,vad,windows,pinned,lease,args):
    need(selection.get('schema_version')==1 and selection.get('video_id')==job['video_id'],'selection_identity')
    need(selection.get('triage_result_sha256')==sha(args.vad_report) and selection.get('triage_lease_sha256')==sha(args.triage_lease)
         and selection.get('triage_proposal_sha256')==sha(args.triage_proposal) and selection.get('triage_lease_id')==lease['lease_id'],'selection_provenance')
    need(selection.get('metadata_flags')==job['metadata_flags'] and selection.get('metadata_hold_sha256')==job['hold_sha256'],'selection_hold')
    for kind in ['audio','metadata']:
        value=selection.get('source',{}).get(kind,{})
        need(value.get('proof')==job[kind+'_proof'] and Path(value.get('private_path','')).resolve()==Path(job[kind+'_path']).resolve(),'selection_source')
    need(selection.get('decoded_source_samples')==vad['decoded_samples'],'selection_extent')
    selected=selection.get('windows',[]);need(len(selected)==len(windows),'selection_windows')
    for item,window in zip(selected,windows):
        a,b=window['source_samples'];clipped=[[max(a,x),min(b,y)] for x,y in vad['vad_speech_source_samples'] if max(a,x)<min(b,y)]
        need([item.get('start_sample'),item.get('end_sample')]==[a,b] and item.get('sample_rate')==RATE
             and item.get('keep_internal_pauses') is True and item.get('contiguous_source_interval') is True
             and item.get('vad_positive_source_samples')==clipped,'selection_windows')
    model=selection.get('model',{})
    need(model.get('model_manifest_sha256')==digest(pinned) and all(model.get(k)==pinned[k] for k in ['repository','revision'])
         and model.get('model_sha256')==next(x['sha256'] for x in pinned['files'] if x['file']=='model.bin'),'selection_model')
    need(sha(selection['model_receipt_path'])==selection['model_receipt_sha256'],'selection_model_receipt')


def safe_error(error,phase,progress=None):
    frames=[];tb=error.__traceback__
    while tb:
        code=tb.tb_frame.f_code
        module=Path(code.co_filename).name;function=code.co_name
        frames.append({'module':module if re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',module) else 'unknown',
                       'function':function if re.fullmatch(r'[A-Za-z0-9_<>]{1,100}',function) else 'unknown','line':tb.tb_lineno})
        tb=tb.tb_next
    state=progress or {}
    return {'status':'held','error_class':str(error) if isinstance(error,ReviewError) else type(error).__name__,
            'phase':phase,'frames':frames[-10:],'raw_message_included':False,
            'window_index':state.get('window_index'),'decoded_samples':state.get('decoded_samples',0),
            'detect_calls_started':state.get('detect_calls_started',0),'detect_calls_completed':state.get('detect_calls_completed',0),
            'model_load_started':state.get('model_load_started',False),'model_loaded':state.get('model_loaded',False),
            'telemetry_started':state.get('telemetry_started',False)}


def load_helpers(pipeline):
    sys.path.insert(0,str(Path(pipeline).resolve()))
    import gpu_asr as base
    import gpu_asr_multilingual as multi
    return base,multi


def prepare(args):
    base,multi=load_helpers(args.pipeline)
    triage=read(args.triage_proposal);result=read(args.vad_report);lease=read(args.triage_lease)
    need(len(triage['jobs'])==1 and len(result['results'])==1,'single_source')
    job=triage['jobs'][0];vad=result['results'][0]
    need(lease['lease_id']==triage['lease_id'] and result['proposal_sha256']==sha(args.triage_proposal),'triage_binding')
    need(lease['result_sha256']==sha(args.vad_report) and lease['state']=='retained_awaiting_root_decision' and not lease['active_consumer'],'triage_not_retained')
    need(vad['source_audio']==job['audio_proof'] and vad['source_metadata']==job['metadata_proof'],'triage_source')
    need(vad['timebase']=='decoded_sample_clock_from_source_audio_start' and vad['first_pcm_pts_seconds']==0,'source_timebase')
    need(vad['assessed_source_samples']==[[0,vad['decoded_samples']]] and not vad['unassessed_decoded_samples'],'vad_extent')
    windows=interval_evidence(WINDOWS,vad['vad_speech_source_samples'],vad['decoded_samples'])
    need(sha(job['hold_path'])==job['hold_sha256']==vad['prior_hold_sha256'],'metadata_hold_hash')
    pinned=read(multi.PINNED)['model']
    validate_selection(read(args.selection),job,vad,windows,pinned,lease,args)
    value={'schema_version':1,'profile':PROFILE,'config':CONFIG,'config_sha256':digest(CONFIG),
           'worker_sha256':sha(__file__),'core_sha256':sha(base.__file__),'multilingual_sha256':sha(multi.__file__),
           'model':pinned,'model_manifest_sha256':digest(pinned),'source_job':job,
           'triage_lease_id':lease['lease_id'],'windows':windows,'decoded_source_samples':vad['decoded_samples'],
           'triage_proposal':{'path':str(Path(args.triage_proposal).resolve()),'sha256':sha(args.triage_proposal)},
           'triage_lease':{'path':str(Path(args.triage_lease).resolve()),'sha256':sha(args.triage_lease)},
           'vad_report':{'path':str(Path(args.vad_report).resolve()),'sha256':sha(args.vad_report)},
           'selection':{'path':str(Path(args.selection).resolve()),'sha256':sha(args.selection)},
           'text_generation_allowed':False,'metadata_hold_changed':False,'completion_changed':False}
    with Path(args.output).open('xb') as output:output.write(encoded(value))
    return {'proposal_sha256':digest(value),'worker_sha256':value['worker_sha256'],'retained_pcm_limit_bytes':CONFIG['max_pcm_bytes'],
            'selected_seconds':sum(x['duration_seconds'] for x in windows),'vad_overlap_seconds':sum(x['vad_overlap_seconds'] for x in windows)}


def verify_proposal(path,expected,base,multi):
    need(sha(path)==expected,'proposal_hash')
    p=read(path)
    need(p['profile']==PROFILE and p['config']==CONFIG and p['config_sha256']==digest(CONFIG),'proposal_config')
    need(p['worker_sha256']==sha(__file__) and p['core_sha256']==sha(base.__file__) and p['multilingual_sha256']==sha(multi.__file__),'worker_hash')
    for key in ['triage_proposal','triage_lease','vad_report','selection']:
        need(sha(p[key]['path'])==p[key]['sha256'],'immutable_evidence_changed')
    job=p['source_job'];need(sha(job['hold_path'])==job['hold_sha256'],'metadata_hold_changed')
    vad=read(p['vad_report']['path'])['results'][0]
    need(p['windows']==interval_evidence(WINDOWS,vad['vad_speech_source_samples'],vad['decoded_samples']),'window_evidence')
    need(p['model']==read(multi.PINNED)['model'],'model_pin')
    return p


def retain_streamed_windows(frames,windows,expected_samples,declared_seconds,guard,progress):
    """Keep only selected intervals from one contiguous, bounded frame iterator."""
    import numpy as np
    need(type(expected_samples) is int and 0<expected_samples<=CONFIG['max_source_duration_seconds']*RATE,'decode_expected_extent')
    need(math.isfinite(float(declared_seconds)) and 0<declared_seconds<=CONFIG['max_source_duration_seconds'],'source_duration_limit')
    need(abs(expected_samples/RATE-declared_seconds)<=CONFIG['max_source_duration_delta_seconds'],'source_duration_delta')
    need(0<len(windows)<=3 and sum(b-a for a,b in windows)<=CONFIG['max_total_samples'],'pcm_budget')
    previous=0
    for a,b in windows:
        need(type(a) is int and type(b) is int and previous<=a<b<=expected_samples and b-a<=CONFIG['max_window_samples'],'decode_window')
        previous=b
    arrays=[np.empty(b-a,dtype=np.float32) for a,b in windows]
    need(sum(x.nbytes for x in arrays)<=CONFIG['max_pcm_bytes'],'pcm_budget')
    written=[0]*len(arrays);total=0;origin=None;max_deviation=0
    for position,values in frames:
        guard();progress['window_index']=None
        need(position is not None and math.isfinite(float(position)),'decode_timestamp')
        if origin is None:
            origin=float(position);need(abs(origin)<=CONFIG['max_origin_seconds'],'decode_origin')
        deviation=abs(float(position)-origin-total/RATE)*RATE
        need(deviation<=CONFIG['timestamp_tolerance_samples'],'decode_discontinuity')
        max_deviation=max(max_deviation,deviation)
        need(0<len(values)<=CONFIG['max_frame_seconds']*RATE and np.isfinite(values).all(),'decode_frame')
        end=total+len(values);need(end<=expected_samples,'decode_sample_limit')
        for index,(a,b) in enumerate(windows):
            lo,hi=max(a,total),min(b,end)
            if lo<hi:
                progress['window_index']=index
                need(lo==a+written[index],'window_sample_gap')
                arrays[index][lo-a:hi-a]=values[lo-total:hi-total];written[index]+=hi-lo
        total=end;progress['decoded_samples']=total
    need(total==expected_samples,'decode_extent_mismatch')
    need(all(n==b-a for n,(a,b) in zip(written,windows)),'decode_windows_incomplete')
    progress['window_index']=None
    return arrays,{'source_samples':windows,'written_samples':written,'decoded_samples':total,
                   'expected_decoded_samples':expected_samples,'declared_duration_seconds':declared_seconds,
                   'decoded_duration_seconds':total/RATE,'declared_duration_delta_seconds':total/RATE-declared_seconds,
                   'first_pcm_pts_seconds':origin,'max_clock_deviation_samples':max_deviation,
                   'timebase':'decoded_sample_clock_from_source_audio_start','decode_passes':1,
                   'retained_pcm_bytes':sum(x.nbytes for x in arrays),'full_pcm_array_created':False,
                   'pcm_written_to_disk':False,'padding_applied':False}


def decode_windows(path,windows,expected_samples,declared_seconds,guard,progress):
    """Decode from source start to measured EOF before any model is loaded."""
    import av
    need(windows==WINDOWS,'window_scope')
    with av.open(str(path)) as container:
        need(len(container.streams.audio)==1 and not container.streams.video,'audio_streams')
        container.streams.audio[0].codec_context.thread_count=1
        resampler=av.AudioResampler(format='fltp',layout='mono',rate=RATE)
        def frames():
            for original in container.decode(audio=0):
                guard()
                need(original.sample_rate>0 and original.samples/original.sample_rate<=CONFIG['max_frame_seconds'],'decode_frame')
                yield from resampler.resample(original)
            yield from resampler.resample(None)
        def values():
            for frame in frames():
                need(frame.pts is not None and frame.time_base is not None,'decode_timestamp')
                yield float(frame.pts*frame.time_base),frame.to_ndarray().reshape(-1)
        return retain_streamed_windows(values(),windows,expected_samples,declared_seconds,guard,progress)


def run(args):
    args.phase='validate';started=time.monotonic();base,multi=load_helpers(args.pipeline)
    args.progress={'window_index':None,'decoded_samples':0,'detect_calls_started':0,'detect_calls_completed':0,
                   'model_load_started':False,'model_loaded':False,'telemetry_started':False}
    p=verify_proposal(args.proposal,args.proposal_sha256,base,multi)
    settings=base.Settings(**read(args.settings));job=p['source_job']
    binding={k:p[k] for k in ['worker_sha256','config_sha256','model_manifest_sha256','core_sha256','multilingual_sha256']}
    binding['proposal_sha256']=args.proposal_sha256
    source_path=base.within(args.source_lease,settings.root)
    output=base.within(args.output,settings.root)
    need(not output.exists(),'result_already_exists')
    runtime=monitor=None
    with base.kernel_lock(settings.root/'sync/asr_gpu_owner.lock'):
        inventory=base.inventory(settings,extra=2*CONFIG['max_output_bytes'])
        model=multi.model_proof(settings)
        need(p['model_manifest_sha256']==model['manifest_sha256'],'model_manifest')
        for kind in ['audio','metadata']:
            path=base.within(job[kind+'_path'],settings.root/'research/jamye-audio-triage-v1/input')
            proof=job[kind+'_proof'];actual=base.hashes(path)
            need(all(actual[k]==proof[k] for k in ['bytes','md5','sha256']),'source_hash')
        metadata=read(job['metadata_path'])
        need(metadata.get('source',{}).get('video_id')==job['video_id'],'metadata_identity')
        def guard():
            need(time.monotonic()-started<CONFIG['max_wall_seconds'],'review_wall_limit')
            gpu=base.gpu_lease(settings);require_binding(gpu,binding)
            need(all(gpu.get('model',{}).get(k)==model[k] for k in ['repository','revision','model_sha256']),'gpu_model_binding')
            lease=read(source_path);require_binding(lease,binding)
            need(lease.get('schema_version')==1 and lease.get('state')=='active' and lease.get('profile')==PROFILE,'source_lease_state')
            need(lease.get('lease_id')==args.source_lease_id and lease.get('owner')==settings.gpu_owner and base.unexpired(lease.get('expires_at')),'source_lease_owner')
            need(lease.get('text_generation_allowed') is False and lease.get('triage_lease_id')==p['triage_lease_id'],'source_lease_scope')
            need(lease.get('source_audio')==job['audio_proof'] and lease.get('source_metadata')==job['metadata_proof'],'source_lease_proof')
            need({str(Path(x).resolve()) for x in lease.get('input_paths',[])}=={str(Path(job[k+'_path']).resolve()) for k in ['audio','metadata']},'source_lease_paths')
        guard();gpu=base.gpu_lease(settings);rows=[]
        try:
            args.phase='sequential_decode'
            arrays,decode=decode_windows(job['audio_path'],WINDOWS,p['decoded_source_samples'],job['declared_duration_seconds'],guard,args.progress)
            need(decode['first_pcm_pts_seconds']==0,'decode_origin_changed')
            guard();args.phase='load_cuda_model';args.progress['model_load_started']=True
            runtime=multi.Runtime(settings,gpu);args.progress['model_loaded']=True
            need(runtime.model.model.device=='cuda' and runtime.model.model.compute_type=='int8_float16','cpu_fallback_forbidden')
            monitor=multi.Monitor(runtime,guard,gpu['rolling_utilization_target']*100,gpu['max_vram_bytes']);monitor.begin()
            args.progress['telemetry_started']=True
            for index,window in enumerate(p['windows']):
                args.progress['window_index']=index;audio=arrays[index]
                args.phase='language_id_only';monitor.guard()
                args.progress['detect_calls_started']+=1
                detected=runtime.detect(audio);args.progress['detect_calls_completed']+=1
                scores=normalize_score(detected)
                rows.append({**window,**scores});arrays[index]=None;del audio
            args.progress['window_index']=None
            telemetry=monitor.finish();monitor=None;guard()
            need(sha(job['hold_path'])==job['hold_sha256'],'metadata_hold_changed')
            review={'schema_version':1,'artifact_kind':'language_id_review','status':'complete_unreviewed_window_evidence',
                    'windows':rows,'decode':decode,'execution':args.progress,'text_generated':False,'metadata_hold_overridden':False,'changes_collection_completion':False,
                    'unknown_unprobed_intervals_preserved':True,'language_scores_are_not_calibrated_truth':True,
                    'human_reviewed':False,'lexical_meaning_confirmed':False,'full_recording_language_confirmed':False}
            provenance={'schema_version':1,'profile':PROFILE,'source_audio':job['audio_proof'],'source_metadata':job['metadata_proof'],
                        'metadata_flags':job['metadata_flags'],'prior_hold_sha256':job['hold_sha256'],
                        'source_lease_id':args.source_lease_id,'gpu_lease_id':settings.gpu_lease_id,'binding':binding,
                        'vad_report_sha256':p['vad_report']['sha256'],'model':model,'config':CONFIG,'inventory':inventory,
                        'device':'cuda:0','compute_type':'int8_float16','text_generation':False,'source_input_deleted':False}
            members={'review.json':encoded(review),'provenance.json':encoded(provenance),'telemetry.json':encoded(telemetry)}
            members['artifact_manifest.json']=encoded({k:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in members.items()})
            need(sum(map(len,members.values()))<CONFIG['max_output_bytes']//2,'output_budget')
            args.phase='write_review';output.parent.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as archive:
                for name,value in members.items():archive.writestr(name,value)
            with zipfile.ZipFile(output) as archive:need(archive.testzip() is None,'result_crc')
            return {'status':review['status'],'window_count':len(rows),'text_generated':False,'proof':base.hashes(output)}
        finally:
            previous_error=sys.exc_info()[1]
            try:
                if monitor:monitor.finish()
                if runtime:runtime.close()
            except Exception:
                if previous_error is None:raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['prepare','run'])
    for key in ['pipeline','triage-proposal','triage-lease','vad-report','selection','output','proposal','proposal-sha256','settings','source-lease','source-lease-id']:
        parser.add_argument('--'+key)
    args=parser.parse_args();args.phase='prepare'
    try:
        print(json.dumps(prepare(args) if args.mode=='prepare' else run(args)));return 0
    except Exception as error:
        print(json.dumps(safe_error(error,args.phase,getattr(args,'progress',None))));return 3


if __name__=='__main__':raise SystemExit(main())
