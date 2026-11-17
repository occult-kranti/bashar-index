"""Explicit three-window partial ASR review; no acquisition or full-ASR promotion."""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import zipfile

PROFILE='partial-asr-review-v1'
LID_WORKER_SHA256='cce88fd0e5881f5ef67b45f3a303f2116967739aeb45c6d577963e9f3fc22f28'
RATE=16000
CONFIG={'language':'en','task':'transcribe','beam_size':5,'best_of':1,'temperature':0,
        'condition_on_previous_text':False,'vad_filter':False,'word_timestamps':True}
POLICY={'profile':PROFILE,'maximum_transcribe_calls':3,'maximum_input_seconds':90,
        'retained_pcm_limit_bytes':5760000,'heartbeat_seconds':1,'wall_seconds':600,
        'max_output_bytes':2000000,'max_text_characters':100000,'max_segments':1000,
        'max_words':15000,'timestamp_tolerance_seconds':.05,'metadata_hold_override':False,
        'full_asr_allowed':False,'translate_allowed':False,'asr_config':CONFIG}
FILES={'review.json','original/segments.json','original/transcript.txt','provenance.json','telemetry.json','artifact_manifest.json'}


class ReviewError(RuntimeError):pass
def need(value,code):
    if not value:raise ReviewError(code)
def encoded(value):return (json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    need(Path(path).stat().st_size<=2000000,'document_size')
    return json.loads(Path(path).read_text(encoding='utf-8'))
def load_lid(path):
    need(sha(path)==LID_WORKER_SHA256,'lid_worker_hash')
    spec=importlib.util.spec_from_file_location('frozen_language_review_v2',path)
    lid=importlib.util.module_from_spec(spec);spec.loader.exec_module(lid)
    return lid
def binding_for(p,proposal_sha):
    keys=['worker_sha256','config_sha256','model_manifest_sha256','core_sha256','multilingual_sha256','lid_worker_sha256','lid_result_sha256']
    return {**{key:p[key] for key in keys},'proposal_sha256':proposal_sha}
def epoch(value):
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    need(parsed.tzinfo is not None,'lease_expiry_timezone')
    return parsed.timestamp()


class Heartbeat:
    """Cheap checks per frame; full lease reads at most once per second unless forced."""
    def __init__(self,validate,wall_seconds=600,monotonic=time.monotonic,wall=time.time):
        self.validate,self.monotonic,self.wall=validate,monotonic,wall
        self.deadline=monotonic()+wall_seconds;self.next_full=-math.inf
        self.expiry_epoch=self.expiry_mono=math.inf
        self.counters={'fast_checks':0,'full_checks':0,'forced_checks':0}
    def __call__(self,force=False):
        self.counters['fast_checks']+=1;now=self.monotonic();current=self.wall()
        need(now<self.deadline,'worker_wall_limit')
        need(now<self.expiry_mono and current<self.expiry_epoch,'cached_lease_expired')
        if force or now>=self.next_full:
            self.counters['full_checks']+=1;self.counters['forced_checks']+=int(force)
            expiry=float(self.validate())
            need(math.isfinite(expiry) and expiry>self.wall(),'lease_expired')
            now=self.monotonic();need(now<self.deadline,'worker_wall_limit')
            self.expiry_epoch=expiry;self.expiry_mono=now+(expiry-self.wall())
            self.next_full=now+POLICY['heartbeat_seconds']


def complement(windows,total):
    result=[];cursor=0
    for a,b in windows:
        need(type(a) is int and type(b) is int and cursor<=a<b<=total,'interval_bounds')
        if cursor<a:result.append([cursor,a])
        cursor=b
    if cursor<total:result.append([cursor,total])
    return result


def read_manifest_zip(path,files,limit):
    need(Path(path).stat().st_size<=limit,'bundle_size')
    with zipfile.ZipFile(path) as bundle:
        need(len(bundle.namelist())==len(files) and set(bundle.namelist())==files,'bundle_members')
        need(sum(x.file_size for x in bundle.infolist())<=limit,'bundle_expansion')
        need(bundle.testzip() is None,'bundle_crc')
        members={name:bundle.read(name) for name in files}
    manifest=json.loads(members['artifact_manifest.json'])
    need(set(manifest)==files-{'artifact_manifest.json'},'bundle_manifest')
    for name,proof in manifest.items():
        need(proof=={'bytes':len(members[name]),'sha256':hashlib.sha256(members[name]).hexdigest()},'bundle_member_hash')
    return members


def verify_lid(path,expected_sha,proposal,proposal_sha):
    need(sha(path)==expected_sha,'lid_result_hash')
    members=read_manifest_zip(path,{'review.json','provenance.json','telemetry.json','artifact_manifest.json'},1000000)
    review=json.loads(members['review.json']);provenance=json.loads(members['provenance.json'])
    expected={key:proposal[key] for key in ['worker_sha256','config_sha256','model_manifest_sha256','core_sha256','multilingual_sha256']}
    expected['proposal_sha256']=proposal_sha
    need(provenance.get('binding')==expected and provenance.get('profile')=='language-id-review-v2','lid_binding')
    job=proposal['source_job']
    need(provenance.get('source_audio')==job['audio_proof'] and provenance.get('source_metadata')==job['metadata_proof'],'lid_source')
    need(provenance.get('prior_hold_sha256')==job['hold_sha256'] and provenance.get('metadata_flags')==job['metadata_flags'],'lid_hold')
    need(review.get('status')=='complete_unreviewed_window_evidence' and review.get('text_generated') is False,'lid_status')
    need(review.get('execution',{}).get('detect_calls_completed')==3 and review.get('decode',{}).get('decoded_samples')==proposal['decoded_source_samples'],'lid_extent')
    rows=review.get('windows',[]);need(len(rows)==3,'lid_windows')
    for row,window in zip(rows,proposal['windows']):
        need(row.get('source_samples')==window['source_samples'] and row.get('language')=='en','lid_window_identity')
        probability=float(row.get('probability',-1));margin=float(row.get('top_two_margin',-1))
        need(math.isfinite(probability) and .9<=probability<=1 and math.isfinite(margin) and .2<=margin<=1,'lid_window_evidence')
    return review


def prepare(args):
    lid=load_lid(args.lid_worker);base,multi=lid.load_helpers(args.pipeline)
    prior=lid.verify_proposal(args.lid_proposal,args.lid_proposal_sha256,base,multi)
    verify_lid(args.lid_result,args.lid_result_sha256,prior,args.lid_proposal_sha256)
    value={'schema_version':1,'profile':PROFILE,'worker_sha256':sha(__file__),'config':POLICY,'config_sha256':digest(POLICY),
           'core_sha256':prior['core_sha256'],'multilingual_sha256':prior['multilingual_sha256'],
           'model':prior['model'],'model_manifest_sha256':prior['model_manifest_sha256'],'source_job':prior['source_job'],
           'windows':prior['windows'],'decoded_source_samples':prior['decoded_source_samples'],'triage_lease_id':prior['triage_lease_id'],
           'lid_worker_path':str(Path(args.lid_worker).resolve()),'lid_worker_sha256':LID_WORKER_SHA256,
           'lid_proposal_path':str(Path(args.lid_proposal).resolve()),'lid_proposal_sha256':args.lid_proposal_sha256,
           'lid_result_path':str(Path(args.lid_result).resolve()),'lid_result_sha256':args.lid_result_sha256,
           'metadata_hold_override':False,'full_asr_allowed':False,'partial_text_generation_allowed':True}
    with Path(args.output).open('xb') as stream:stream.write(encoded(value))
    return {'proposal_sha256':digest(value),'worker_sha256':value['worker_sha256'],'profile':PROFILE}


def append_segment(builder,segment,index,bounds):
    a,b=bounds;duration=(b-a)/RATE;start,end=float(segment.start),float(segment.end)
    need(all(math.isfinite(x) for x in [start,end]) and 0<=start<=end<=duration+POLICY['timestamp_tolerance_seconds'],'segment_time')
    need(isinstance(segment.text,str),'segment_text');value=segment.text.strip()
    if not value:return
    need(len(builder['segments'])<POLICY['max_segments'],'segment_limit')
    offset=len(builder['text']);prefix='\n' if offset else '';offset+=len(prefix)
    need(offset+len(value)<=POLICY['max_text_characters'],'text_limit')
    words=[];cursor=0
    for word in segment.words or []:
        ws,we,probability=map(float,[word.start,word.end,word.probability])
        need(all(math.isfinite(x) for x in [ws,we,probability]) and 0<=ws<=we<=duration+.05 and 0<=probability<=1,'word_numeric')
        need(isinstance(word.word,str),'word_text');token=word.word.strip();at=value.find(token,cursor) if token else -1
        need(at>=0,'word_offset');cursor=at+len(token)
        words.append({'text':token,'start':a/RATE+min(ws,duration),'end':a/RATE+min(we,duration),
                      'model_relative_start':ws,'model_relative_end':we,'timestamp_clipped':bool(we>duration or ws>duration),
                      'probability':probability,'char_start':offset+at,'char_end':offset+at+len(token)})
    builder['word_count']+=len(words);need(builder['word_count']<=POLICY['max_words'],'word_limit')
    item={'window_index':index,'start':a/RATE+min(start,duration),'end':a/RATE+min(end,duration),
          'model_relative_start':start,'model_relative_end':end,'timestamp_clipped':bool(end>duration or start>duration),
          'text':value,'char_start':offset,'char_end':offset+len(value),'words':words}
    need(not builder['segments'] or item['start']>=builder['segments'][-1]['start'],'segment_order')
    builder['segments'].append(item);builder['text']+=prefix+value


def verify_bundle(path):
    members=read_manifest_zip(path,FILES,POLICY['max_output_bytes'])
    review=json.loads(members['review.json']);provenance=json.loads(members['provenance.json'])
    segments=json.loads(members['original/segments.json']);text=members['original/transcript.txt'].decode('utf-8')
    need(review.get('artifact_kind')=='partial_asr_review' and review.get('full_recording_transcript') is False and review.get('changes_collection_completion') is False,'partial_semantics')
    need(provenance.get('profile')==PROFILE and provenance.get('quality_state')=='unreviewed_partial_asr' and provenance.get('metadata_hold_overridden') is False
         and provenance.get('full_asr_promoted') is False and provenance.get('cpu_asr_fallback') is False,'partial_provenance')
    need(review['unprocessed_source_samples']==complement(review['processed_source_samples'],review['decoded_source_samples']),'unprocessed_inventory')
    need(segments.get('text_kind')=='partial_original_asr' and segments.get('language')=='en','text_variant')
    need(provenance['english_view']=={'text_kind':'original_english_alias','same_as':'original','language':'en','translation_performed':False},'english_alias')
    need(len(text)<=POLICY['max_text_characters'] and len(segments['segments'])<=POLICY['max_segments'],'text_limit')
    for row in segments['segments']:
        need(text[row['char_start']:row['char_end']]==row['text'],'segment_offset')
        a,b=review['processed_source_samples'][row['window_index']]
        for word in [row]+row['words']:
            need(all(math.isfinite(float(word[k])) for k in ['start','end']) and a/RATE<=word['start']<=word['end']<=b/RATE,'source_time')
            need(text[word['char_start']:word['char_end']]==word['text'],'word_offset')
    return {'review':review,'provenance':provenance,'segments':segments,'text':text}


def run(args):
    args.phase='validate';args.progress={'window_index':None,'decoded_samples':0,'transcribe_calls_started':0,'transcribe_calls_completed':0,'model_load_started':False,'model_loaded':False,'telemetry_started':False}
    started=time.monotonic();timings={};need(sha(args.proposal)==args.proposal_sha256,'proposal_hash');p=read(args.proposal)
    need(p['profile']==PROFILE and p['worker_sha256']==sha(__file__) and p['config']==POLICY and p['config_sha256']==digest(POLICY),'proposal_binding')
    lid=load_lid(p['lid_worker_path']);base,multi=lid.load_helpers(args.pipeline)
    prior=lid.verify_proposal(p['lid_proposal_path'],p['lid_proposal_sha256'],base,multi)
    verify_lid(p['lid_result_path'],p['lid_result_sha256'],prior,p['lid_proposal_sha256'])
    need(all(p[key]==prior[key] for key in ['source_job','windows','decoded_source_samples','triage_lease_id','model','model_manifest_sha256','core_sha256','multilingual_sha256']),'prior_proposal_mismatch')
    settings=base.Settings(**read(args.settings));job=p['source_job'];binding=binding_for(p,args.proposal_sha256)
    source_path=base.within(args.source_lease,settings.root);output=base.within(args.output,settings.root)
    need(not output.exists(),'result_exists');paths={kind:base.within(job[kind+'_path'],settings.root/'research/jamye-audio-triage-v1/input') for kind in ['audio','metadata']}
    model_expected={'repository':p['model']['repository'],'revision':p['model']['revision'],'model_sha256':next(x['sha256'] for x in p['model']['files'] if x['file']=='model.bin')}
    def validate():
        gpu=base.gpu_lease(settings);source=read(source_path)
        need(gpu.get('partial_review')==binding and source.get('partial_review')==binding,'partial_lease_binding')
        need(all(gpu.get('model',{}).get(k)==v for k,v in model_expected.items()),'gpu_model_binding')
        need(source.get('schema_version')==1 and source.get('state')=='active' and source.get('profile')==PROFILE,'source_state')
        need(source.get('lease_id')==args.source_lease_id and source.get('owner')==settings.gpu_owner,'source_owner')
        need(source.get('partial_text_generation_allowed') is True and source.get('full_asr_allowed') is False and source.get('metadata_hold_override') is False,'source_scope')
        need(source.get('source_audio')==job['audio_proof'] and source.get('source_metadata')==job['metadata_proof'] and source.get('triage_lease_id')==p['triage_lease_id'],'source_proof')
        need({str(Path(x).resolve()) for x in source.get('input_paths',[])}=={str(x) for x in paths.values()},'source_paths')
        return min(epoch(gpu['expires_at']),epoch(source['expires_at']))
    heartbeat=Heartbeat(validate,POLICY['wall_seconds']);runtime=monitor=None
    with base.kernel_lock(settings.root/'sync/asr_gpu_owner.lock'):
        heartbeat(force=True);inventory=base.inventory(settings,extra=2*POLICY['max_output_bytes'])
        before=time.monotonic();model=multi.model_proof(settings);need(model['manifest_sha256']==p['model_manifest_sha256'],'model_manifest')
        for kind,path in paths.items():
            actual=base.hashes(path);need(all(actual[k]==job[kind+'_proof'][k] for k in ['bytes','md5','sha256']),'source_hash')
        timings['proof_seconds']=time.monotonic()-before
        try:
            args.phase='sequential_decode';heartbeat(force=True);before=time.monotonic()
            arrays,decode=lid.decode_windows(paths['audio'],lid.WINDOWS,p['decoded_source_samples'],job['declared_duration_seconds'],heartbeat,args.progress)
            need(decode['first_pcm_pts_seconds']==0,'source_origin');timings['decode_seconds']=time.monotonic()-before
            args.phase='load_cuda_model';heartbeat(force=True);gpu=base.gpu_lease(settings);before=time.monotonic();args.progress['model_load_started']=True
            runtime=multi.Runtime(settings,gpu);args.progress['model_loaded']=True
            need(runtime.model.model.device=='cuda' and runtime.model.model.compute_type=='int8_float16','cpu_fallback_forbidden')
            timings['model_load_seconds']=time.monotonic()-before;heartbeat(force=True)
            monitor=multi.Monitor(runtime,heartbeat,gpu['rolling_utilization_target']*100,gpu['max_vram_bytes']);monitor.begin();args.progress['telemetry_started']=True
            builder={'segments':[],'text':'','word_count':0};timings['transcribe_seconds']=[]
            for index,window in enumerate(p['windows']):
                args.phase='partial_transcribe';args.progress['window_index']=index;heartbeat(force=True);monitor.guard();heartbeat(force=True);before=time.monotonic()
                args.progress['transcribe_calls_started']+=1
                iterator,info=runtime.model.transcribe(arrays[index],**CONFIG)
                while True:
                    monitor.guard()
                    try:segment=next(iterator)
                    except StopIteration:break
                    append_segment(builder,segment,index,window['source_samples'])
                args.progress['transcribe_calls_completed']+=1;timings['transcribe_seconds'].append(time.monotonic()-before);arrays[index]=None
            args.progress['window_index']=None;heartbeat(force=True);telemetry=monitor.finish();monitor=None
            need(sha(job['hold_path'])==job['hold_sha256'],'metadata_hold_changed')
            windows=[w['source_samples'] for w in p['windows']];declared=round(job['declared_duration_seconds']*RATE)
            review={'schema_version':1,'artifact_kind':'partial_asr_review','status':'complete_unreviewed_partial_asr',
                    'processed_source_samples':windows,'decoded_source_samples':p['decoded_source_samples'],
                    'unprocessed_source_samples':complement(windows,p['decoded_source_samples']),
                    'unavailable_declared_tail_samples':[[p['decoded_source_samples'],declared]] if declared>p['decoded_source_samples'] else [],
                    'input_seconds':sum(b-a for a,b in windows)/RATE,'decode':decode,'execution':args.progress,
                    'full_recording_transcript':False,'changes_collection_completion':False,'human_reviewed':False,
                    'transcript_coverage_validated':False,'unprocessed_spans_are_not_nonlexical_claims':True}
            segments={'schema_version':1,'text_kind':'partial_original_asr','language':'en','timebase':'source_audio_seconds',
                      'character_offset_unit':'unicode_code_points','speaker_identity':'unassigned','segments':builder['segments']}
            provenance={'schema_version':1,'profile':PROFILE,'quality_state':'unreviewed_partial_asr','binding':binding,
                        'source_audio':job['audio_proof'],'source_metadata':job['metadata_proof'],'metadata_flags':job['metadata_flags'],
                        'prior_hold_sha256':job['hold_sha256'],'metadata_hold_overridden':False,'full_asr_promoted':False,
                        'source_lease_id':args.source_lease_id,'gpu_lease_id':settings.gpu_lease_id,'model':model,'config':POLICY,
                        'english_view':{'text_kind':'original_english_alias','same_as':'original','language':'en','translation_performed':False},
                        'accuracy_claimed':False,'word_times_are_model_estimates':True,'device':'cuda:0','compute_type':'int8_float16',
                        'cpu_asr_fallback':False,'inventory':inventory,'lid_result_sha256':p['lid_result_sha256']}
            timings['elapsed_seconds']=time.monotonic()-started;telemetry.update(guard=heartbeat.counters,timings=timings)
            members={'review.json':encoded(review),'original/segments.json':encoded(segments),'original/transcript.txt':builder['text'].encode(),
                     'provenance.json':encoded(provenance),'telemetry.json':encoded(telemetry)}
            members['artifact_manifest.json']=encoded({k:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in members.items()})
            need(sum(map(len,members.values()))<=POLICY['max_output_bytes']//2,'output_limit');args.phase='write_result';heartbeat(force=True)
            output.parent.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as bundle:
                for name,raw in members.items():bundle.writestr(name,raw)
            with output.open('r+b') as handle:handle.flush();os.fsync(handle.fileno())
            verify_bundle(output);proof=base.hashes(output)
            receipt={'schema_version':1,'artifact_kind':'partial_asr_review','status':'local_partial_review_unreviewed','profile':PROFILE,
                     'source_audio':job['audio_proof'],'source_metadata':job['metadata_proof'],'binding':binding,
                     'source_lease_id':args.source_lease_id,'bundle':{'path':str(output),**proof},'changes_collection_completion':False}
            with (settings.root/'sync/partial_asr_review_manifest.jsonl').open('ab') as journal:
                journal.write(encoded(receipt));journal.flush();os.fsync(journal.fileno())
            return {'status':receipt['status'],'artifact_kind':'partial_asr_review','transcribe_calls_completed':args.progress['transcribe_calls_completed'],
                    'segment_count':len(builder['segments']),'word_count':builder['word_count'],'proof':proof,'guard':heartbeat.counters,'timings':timings}
        finally:
            original=sys.exc_info()[1]
            try:
                if monitor:monitor.finish()
                if runtime:runtime.close()
            except Exception:
                if original is None:raise


def safe_error(error,args):
    frames=[];tb=error.__traceback__
    while tb:
        frames.append({'module':Path(tb.tb_frame.f_code.co_filename).name,'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno});tb=tb.tb_next
    return {'status':'held','error_class':str(error) if isinstance(error,ReviewError) else type(error).__name__,
            'phase':getattr(args,'phase','prepare'),'progress':getattr(args,'progress',{}),'frames':frames[-10:],'raw_message_included':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['prepare','run','verify'])
    for key in ['pipeline','lid-worker','lid-proposal','lid-proposal-sha256','lid-result','lid-result-sha256','output','proposal','proposal-sha256','settings','source-lease','source-lease-id','bundle']:
        parser.add_argument('--'+key)
    args=parser.parse_args()
    try:
        if args.mode=='verify':verify_bundle(args.bundle);result={'status':'verified_local_partial_review'}
        else:result=prepare(args) if args.mode=='prepare' else run(args)
        print(json.dumps(result));return 0
    except Exception as error:print(json.dumps(safe_error(error,args)));return 3


if __name__=='__main__':raise SystemExit(main())
