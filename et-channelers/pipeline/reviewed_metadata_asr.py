"""One reviewed-metadata full-source ASR admission, preserving original holds."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import time

PROFILE='reviewed-metadata-full-english-asr-v1'
PARTIAL_WORKER_SHA='572d005fa3aba6157669d0318ac47bb20297eb0cc3146132679ed4d45779fe71'
PARTIAL_RESULT_SHA='50ab6612e71802afbc4c7fa9adc0fd30565568b8f0bc87fef26be21c923c470f'
LID_RESULT_SHA='59d2f80a1572ad96b1e3c7ebf134437b8adee388056eed86cae9527da2695b91'
CONFIG={'language':'en','task':'transcribe','beam_size':5,'best_of':1,'temperature':0,
        'condition_on_previous_text':False,'vad_filter':True,'vad_parameters':{'min_silence_duration_ms':500},'word_timestamps':True}
POLICY={'profile':PROFILE,'max_source_seconds':1600,'window_seconds':30,'wall_seconds':1800,
        'max_transcribe_calls':54,'heartbeat_seconds':1,'metadata_flag_mutation_allowed':False,
        'original_hold_preserved':True,'human_reviewed':False,'every_interval_english_confirmed':False,
        'every_interval_lexical_confirmed':False,'config':CONFIG}


class ReviewError(RuntimeError):pass
def need(value,code):
    if not value:raise ReviewError(code)
def encoded(value):return (json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    need(Path(path).stat().st_size<=2000000,'document_size')
    return json.loads(Path(path).read_text(encoding='utf-8'))
def helper(path):
    need(sha(path)==PARTIAL_WORKER_SHA,'partial_helper_hash')
    spec=importlib.util.spec_from_file_location('frozen_partial_review_v1',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def assessment_for(partial_proposal):
    job=partial_proposal['source_job']
    return {'schema_version':1,'profile':PROFILE,'reviewer_kind':'root_agent','human_reviewed':False,
            'resolution':'admit_full_source_unreviewed_english_asr','basis':'three_sampled_excerpts_contain_coherent_ordinary_english',
            'reviewed_source_samples':[row['source_samples'] for row in partial_proposal['windows']],
            'lid_result_sha256':LID_RESULT_SHA,'partial_result_sha256':PARTIAL_RESULT_SHA,
            'source_audio':job['audio_proof'],'source_metadata':job['metadata_proof'],
            'original_metadata_flags':job['metadata_flags'],'original_hold_sha256':job['hold_sha256'],
            'original_hold_preserved':True,'source_metadata_mutated':False,
            'every_interval_english_confirmed':False,'every_interval_lexical_confirmed':False,
            'accuracy_confirmed':False,'full_transcript_already_exists':False}


def evidence(partial,proposal_path,proposal_sha,result_path):
    need(sha(proposal_path)==proposal_sha,'partial_proposal_hash');p=read(proposal_path)
    need(p['worker_sha256']==PARTIAL_WORKER_SHA and p['config']==partial.POLICY and p['config_sha256']==partial.digest(partial.POLICY),'partial_proposal_binding')
    need(p['lid_result_sha256']==LID_RESULT_SHA and sha(result_path)==PARTIAL_RESULT_SHA,'review_evidence_hash')
    proof=partial.verify_bundle(result_path);provenance=proof['provenance'];job=p['source_job']
    need(provenance['binding']==partial.binding_for(p,proposal_sha),'partial_result_binding')
    need(provenance['source_audio']==job['audio_proof'] and provenance['source_metadata']==job['metadata_proof'],'partial_source')
    need(proof['review']['processed_source_samples']==[x['source_samples'] for x in p['windows']]
         and proof['review']['execution']['transcribe_calls_completed']==3 and proof['text'].strip(),'partial_scope')
    need(provenance['prior_hold_sha256']==job['hold_sha256'] and provenance['metadata_flags']==job['metadata_flags'],'partial_hold')
    return p


def prepare(args):
    partial=helper(args.partial_worker);prior=evidence(partial,args.partial_proposal,args.partial_proposal_sha256,args.partial_result)
    lid=partial.load_lid(prior['lid_worker_path']);base,multi=lid.load_helpers(args.pipeline)
    lid_prior=lid.verify_proposal(prior['lid_proposal_path'],prior['lid_proposal_sha256'],base,multi)
    partial.verify_lid(prior['lid_result_path'],prior['lid_result_sha256'],lid_prior,prior['lid_proposal_sha256'])
    need(all(prior[k]==lid_prior[k] for k in ['source_job','windows','decoded_source_samples','model','model_manifest_sha256','core_sha256','multilingual_sha256']),'review_chain')
    need(0<prior['decoded_source_samples']/16000<=POLICY['max_source_seconds'],'source_duration')
    assessment=assessment_for(prior)
    metadata_path=prior['source_job']['metadata_path']
    need(sha(metadata_path)==prior['source_job']['metadata_proof']['sha256'],'metadata_hash')
    channel=read(metadata_path).get('queue',{}).get('channel_dir')
    need(isinstance(channel,str) and re.fullmatch(r'[a-z0-9-]+',channel),'source_channel')
    value={'schema_version':1,'profile':PROFILE,'worker_sha256':sha(__file__),'config':POLICY,'config_sha256':digest(POLICY),
           'assessment':assessment,'assessment_sha256':digest(assessment),'partial_worker_path':str(Path(args.partial_worker).resolve()),
           'partial_worker_sha256':PARTIAL_WORKER_SHA,'partial_proposal_path':str(Path(args.partial_proposal).resolve()),
           'partial_proposal_sha256':args.partial_proposal_sha256,'partial_result_path':str(Path(args.partial_result).resolve()),
           'partial_result_sha256':PARTIAL_RESULT_SHA,'lid_result_sha256':LID_RESULT_SHA,
           **{k:prior[k] for k in ['source_job','decoded_source_samples','model','model_manifest_sha256','core_sha256','multilingual_sha256','triage_lease_id']},
           'vad_report_sha256':lid_prior['vad_report']['sha256'],'channel_dir':channel,'job_id':'reviewed-full-'+digest(assessment)[:24]}
    with Path(args.output).open('xb') as output:output.write(encoded(value))
    return {'proposal_sha256':digest(value),'worker_sha256':value['worker_sha256'],'assessment_sha256':value['assessment_sha256']}


def verify_proposal(args):
    need(sha(args.proposal)==args.proposal_sha256,'proposal_hash');p=read(args.proposal)
    need(p['profile']==PROFILE and p['worker_sha256']==sha(__file__) and p['config']==POLICY and p['config_sha256']==digest(POLICY),'proposal_binding')
    partial=helper(p['partial_worker_path']);prior=evidence(partial,p['partial_proposal_path'],p['partial_proposal_sha256'],p['partial_result_path'])
    need(p['assessment']==assessment_for(prior) and p['assessment_sha256']==digest(p['assessment']),'review_resolution')
    lid=partial.load_lid(prior['lid_worker_path']);base,multi=lid.load_helpers(args.pipeline)
    lid_prior=lid.verify_proposal(prior['lid_proposal_path'],prior['lid_proposal_sha256'],base,multi)
    partial.verify_lid(prior['lid_result_path'],prior['lid_result_sha256'],lid_prior,prior['lid_proposal_sha256'])
    for key in ['source_job','decoded_source_samples','model','model_manifest_sha256','core_sha256','multilingual_sha256','triage_lease_id']:
        need(p[key]==prior[key]==lid_prior[key],'proposal_chain')
    need(p['vad_report_sha256']==lid_prior['vad_report']['sha256'],'vad_binding')
    return p,partial,base,multi


def binding_for(p,proposal_sha):
    keys=['worker_sha256','config_sha256','assessment_sha256','model_manifest_sha256','core_sha256','multilingual_sha256',
          'partial_worker_sha256','partial_result_sha256','lid_result_sha256','vad_report_sha256']
    return {**{k:p[k] for k in keys},'proposal_sha256':proposal_sha}


def tracked_task(runtime,multi,heartbeat,progress,timings,expected_samples):
    class Task(multi.TaskRuntime):
        def windows(self,path,duration):
            iterator=super().windows(path,duration);samples=0
            while True:
                heartbeat(force=True);before=time.monotonic()
                try:start,audio=next(iterator)
                except StopIteration:
                    timings['decode_seconds']+=time.monotonic()-before;break
                timings['decode_seconds']+=time.monotonic()-before
                need(round(start*16000)==samples,'source_window_gap');samples+=len(audio)
                need(samples<=expected_samples and len(audio)<=30*16000,'source_sample_bound')
                progress['decoded_samples']=samples;progress['window_index']=progress['transcribe_calls_started']
                yield start,audio
            need(samples==expected_samples,'source_sample_extent')
        def transcribe(self,audio):
            heartbeat(force=True);need(progress['transcribe_calls_started']<POLICY['max_transcribe_calls'],'call_limit')
            progress['transcribe_calls_started']+=1;before=time.monotonic()
            iterator,info=super().transcribe(audio)
            timings['inference_seconds']+=time.monotonic()-before
            def measured():
                while True:
                    heartbeat();begin=time.monotonic()
                    try:item=next(iterator)
                    except StopIteration:
                        timings['inference_seconds']+=time.monotonic()-begin
                        progress['transcribe_calls_completed']+=1;return
                    timings['inference_seconds']+=time.monotonic()-begin
                    yield item
            return measured(),info
    return Task(runtime,CONFIG)


def run(args):
    args.phase='validate';args.progress={'window_index':None,'decoded_samples':0,'transcribe_calls_started':0,'transcribe_calls_completed':0,'model_loaded':False}
    begun=time.monotonic();p,partial,base,multi=verify_proposal(args);settings=base.Settings(**read(args.settings));job=p['source_job']
    binding=binding_for(p,args.proposal_sha256);source_path=base.within(args.source_lease,settings.root)
    paths={kind:base.within(job[kind+'_path'],settings.root/'research/jamye-audio-triage-v1/input') for kind in ['audio','metadata']}
    model_expected={'repository':p['model']['repository'],'revision':p['model']['revision'],'model_sha256':next(x['sha256'] for x in p['model']['files'] if x['file']=='model.bin')}
    def validate():
        gpu=base.gpu_lease(settings);source=read(source_path)
        need(gpu.get('reviewed_asr')==binding and source.get('reviewed_asr')==binding,'reviewed_lease_binding')
        need(all(gpu.get('model',{}).get(k)==v for k,v in model_expected.items()),'gpu_model_binding')
        need(source.get('schema_version')==1 and source.get('state')=='active' and source.get('profile')==PROFILE,'source_state')
        need(source.get('lease_id')==args.source_lease_id and source.get('owner')==settings.gpu_owner,'source_owner')
        need(source.get('full_text_generation_allowed') is True and source.get('metadata_flag_mutation_allowed') is False
             and source.get('assessment_sha256')==p['assessment_sha256'],'source_scope')
        need(source.get('source_audio')==job['audio_proof'] and source.get('source_metadata')==job['metadata_proof']
             and source.get('triage_lease_id')==p['triage_lease_id'],'source_proof')
        need({str(Path(x).resolve()) for x in source.get('input_paths',[])}=={str(x) for x in paths.values()},'source_paths')
        return min(partial.epoch(gpu['expires_at']),partial.epoch(source['expires_at']))
    heartbeat=partial.Heartbeat(validate,POLICY['wall_seconds']);runtime=monitor=None;timings={'decode_seconds':0.,'inference_seconds':0.}
    with base.kernel_lock(settings.root/'sync/asr_gpu_owner.lock'):
        heartbeat(force=True);inventory=base.inventory(settings);before=time.monotonic();model=multi.model_proof(settings)
        need(model['manifest_sha256']==p['model_manifest_sha256'],'model_manifest')
        for kind,path in paths.items():
            observed=base.hashes(path);need(all(observed[k]==job[kind+'_proof'][k] for k in ['bytes','md5','sha256']),'source_hash')
        metadata=read(paths['metadata'])
        need(metadata.get('source',{}).get('video_id')==job['video_id'] and metadata.get('queue',{}).get('channel_dir')==p['channel_dir'],'metadata_identity')
        timings['proof_seconds']=time.monotonic()-before
        identity={'schema':1,'output_contract':multi.CONTRACT,'profile':PROFILE,'worker_sha256':sha(__file__),
                  'proposal_sha256':args.proposal_sha256,'assessment_sha256':p['assessment_sha256'],
                  'source_audio':job['audio_proof'],'source_metadata':job['metadata_proof'],'model':model,
                  'environment_lock_sha256':base.hashes(settings.environment_lock)['sha256'],'configs':{'original':CONFIG},
                  'decode':{'sample_rate':16000,'window_seconds':30,'expected_samples':p['decoded_source_samples']},'reviewed_asr':binding}
        run_id='asr-'+base.fingerprint(identity)[:24];destination=settings.output_root/job['video_id']/run_id
        need(not destination.exists(),'result_already_exists')
        admission={'video_id':job['video_id'],'job_id':p['job_id'],'source_lease_id':args.source_lease_id,
                   'job':{'audio':job['audio_proof'],'metadata':job['metadata_proof']}}
        try:
            args.phase='load_cuda';heartbeat(force=True);gpu=base.gpu_lease(settings);before=time.monotonic()
            runtime=multi.Runtime(settings,gpu);args.progress['model_loaded']=True
            need(runtime.model.model.device=='cuda' and runtime.model.model.compute_type=='int8_float16','cpu_fallback_forbidden')
            timings['model_load_seconds']=time.monotonic()-before;heartbeat(force=True)
            monitor=multi.Monitor(runtime,heartbeat,gpu['rolling_utilization_target']*100,gpu['max_vram_bytes']);monitor.begin()
            args.phase='full_source_transcribe';started_at=base.now();begin=time.monotonic()
            task=tracked_task(runtime,multi,heartbeat,args.progress,timings,p['decoded_source_samples'])
            segments,text,vad_seconds=base.collect_segments(task,paths['audio'],job['declared_duration_seconds'],monitor.guard)
            need(round(segments['duration_seconds']*16000)==p['decoded_source_samples'],'full_sample_extent')
            need(args.progress['transcribe_calls_completed']==math.ceil(p['decoded_source_samples']/(30*16000)),'full_call_extent')
            segments.update(language='en',character_offset_unit='unicode_code_points',text_kind='original_asr')
            heartbeat(force=True);telemetry=monitor.finish();monitor=None
            need(sha(job['hold_path'])==job['hold_sha256'],'original_hold_changed')
            for kind,path in paths.items():
                observed=base.hashes(path);need(all(observed[k]==job[kind+'_proof'][k] for k in ['bytes','md5','sha256']),'source_changed')
            timings['elapsed_seconds']=time.monotonic()-begun;telemetry.update(guard=heartbeat.counters,timings=timings)
            duration=p['decoded_source_samples']/16000;declared=job['declared_duration_seconds']
            provenance={'schema_version':1,'run_id':run_id,'job_id':p['job_id'],'source_video_id':job['video_id'],
                        'channel_dir':p['channel_dir'],'source_lease_id':args.source_lease_id,'source_audio':job['audio_proof'],
                        'source_metadata':job['metadata_proof'],'source_admission_sha256':args.proposal_sha256,
                        'proposal_sha256':args.proposal_sha256,'model':model,'identity':identity,'worker_sha256':sha(__file__),
                        'environment_lock_sha256':identity['environment_lock_sha256'],'dependencies':runtime.dependencies,
                        'started_at':started_at,'finished_at':base.now(),'reviewed_metadata_resolution':p['assessment'],
                        'original_metadata_flags':job['metadata_flags'],'original_hold_sha256':job['hold_sha256'],
                        'original_metadata_hold_preserved':True,'source_metadata_mutated':False,'reviewed_asr':binding,
                        'language_decision':{'language':'en','basis':'root_agent_review_of_three_bound_excerpts','human_confirmed':False,
                                             'full_recording_language_proven':False,'all_intervals_lexical_proven':False},
                        'compute':{'device':'cuda:0','compute_type':'int8_float16','cpu_asr_fallback':False,'gpu_lease_id':settings.gpu_lease_id},
                        'metrics':{'audio_seconds':duration,'declared_duration_seconds':declared,'unavailable_rounded_tail_seconds':max(0,declared-duration),
                                   'duration_after_vad_seconds':vad_seconds,'segment_count':len(segments['segments']),
                                   'detection_decode_inference_pacing_seconds':time.monotonic()-begin},
                        'quality':{'accuracy_claimed':False,'human_reviewed':False,'speech_coverage_validated':False,
                                   'word_times_are_model_estimates':True,'window_boundary_effects_unvalidated':True,'host_guest_identity_assigned':False}}
            args.phase='write_verified_pair';heartbeat(force=True)
            receipt=multi.write_pair(settings,admission,run_id,{'original':(segments,text,CONFIG)},telemetry,provenance)
            return {'status':receipt['status'],'run_id':run_id,'receipt_path':str(destination/'receipt.json'),
                    'bundle':receipt['bundle'],'segments':len(segments['segments']),'guard':heartbeat.counters,'timings':timings,'uploaded':False}
        finally:
            original=sys.exc_info()[1]
            try:
                if monitor:monitor.finish()
                if runtime:runtime.close()
            except Exception:
                if original is None:raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['prepare','run'])
    for key in ['pipeline','partial-worker','partial-proposal','partial-proposal-sha256','partial-result','output','proposal','proposal-sha256','settings','source-lease','source-lease-id']:
        parser.add_argument('--'+key)
    args=parser.parse_args()
    try:print(json.dumps(prepare(args) if args.mode=='prepare' else run(args)));return 0
    except Exception as error:
        frames=[];tb=error.__traceback__
        while tb:
            frames.append({'module':Path(tb.tb_frame.f_code.co_filename).name,'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno});tb=tb.tb_next
        print(json.dumps({'status':'held','error_class':str(error) if isinstance(error,ReviewError) else type(error).__name__,
                          'phase':getattr(args,'phase','prepare'),'progress':getattr(args,'progress',{}),'frames':frames[-10:]}));return 3


if __name__=='__main__':raise SystemExit(main())
