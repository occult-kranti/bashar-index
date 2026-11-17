"""Separate English ASR of verified publisher editions; never native promotion."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import time

PROFILE='publisher-variant-english-asr-v1'
HEARTBEAT_SHA='572d005fa3aba6157669d0318ac47bb20297eb0cc3146132679ed4d45779fe71'
CONFIG={'language':'en','task':'transcribe','beam_size':5,'best_of':1,'temperature':0,
        'condition_on_previous_text':False,'vad_filter':True,'vad_parameters':{'min_silence_duration_ms':500},'word_timestamps':True}
POLICY={'profile':PROFILE,'max_sources':2,'max_input_bytes':256000000,'window_seconds':30,
        'duration_tolerance_seconds':2,'wall_seconds':2700,'heartbeat_seconds':1,'config':CONFIG,
        'native_youtube_bytes':False,'changes_native_asr_count':False,'changes_native_audio_count':False}
ARTIFACTS={'publisher_podcast_audio_variant','qualified_publisher_podcast_audio_variant'}
PROOF_KEYS=['remote','drive_id','bytes','md5','sha256']


class VariantError(RuntimeError):pass
def need(value,code):
    if not value:raise VariantError(code)
def encoded(value):return (json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    need(Path(path).stat().st_size<=3000000,'document_size')
    return json.loads(Path(path).read_text(encoding='utf-8'))
def load_helpers(pipeline,heartbeat_path):
    need(sha(heartbeat_path)==HEARTBEAT_SHA,'heartbeat_hash')
    spec=importlib.util.spec_from_file_location('pinned_partial_heartbeat',heartbeat_path)
    heartbeat=importlib.util.module_from_spec(spec);spec.loader.exec_module(heartbeat)
    sys.path.insert(0,str(Path(pipeline).resolve()))
    import gpu_asr as base
    import gpu_asr_multilingual as multi
    return heartbeat,base,multi
def proof(value):
    result={key:value.get(key) for key in PROOF_KEYS}
    need(isinstance(result['bytes'],int) and result['bytes']>0 and isinstance(result['drive_id'],str) and result['drive_id']
         and isinstance(result['remote'],str) and result['remote'],'source_proof')
    need(re.fullmatch(r'[a-f0-9]{32}',result['md5'] or '') and re.fullmatch(r'[a-f0-9]{64}',result['sha256'] or ''),'source_hash_shape')
    return result


def publisher_language(metadata,archive,external=None,external_sha=None):
    if external is not None:
        need(external.get('artifact_kind')=='publisher_feed_language_evidence' and external.get('scope')=='publisherRSSchannel','publisher_language_scope')
        need(proof(external['source_audio_proof'])==proof(archive['audio'])
             and proof(external['unchanged_provenance_proof'])==proof(archive['provenance']),'publisher_language_source')
        need(external.get('episode_guid')==metadata.get('episode_guid') and external.get('source_audio_url')==metadata.get('source_audio_url'),'publisher_language_episode')
        need(external.get('native_youtube_language_asserted') is False and external.get('episode_spoken_language_verified') is False,'publisher_language_claim')
        code=external.get('declared_language');basis='separate_publisher_feed_language_evidence';evidence_sha=external_sha
    else:
        code=metadata.get('publisher_feed_language');basis='archived_variant_provenance.publisher_feed_language';evidence_sha=archive['provenance']['sha256']
        if code is not None:
            need(metadata.get('language_evidence_scope')=='publisher RSS channel declaration; not independently detected per-episode speech language','publisher_language_scope')
    if not isinstance(code,str) or not re.fullmatch(r'en(?:-[A-Za-z0-9]+)*',code,re.IGNORECASE):return None
    need(re.fullmatch(r'[a-f0-9]{64}',evidence_sha or '') is not None,'publisher_language_hash')
    return {'code':code.lower(),'basis':basis,'scope':'publisher_rss_channel_declaration',
            'evidence_sha256':evidence_sha,'episode_language_independently_verified':False,'native_youtube_language_asserted':False}


def prepare_job(item):
    document=read(item['archive_receipt_path']);archive=document['variant'] if item.get('receipt_selector')=='variant' else document
    need(archive.get('status')=='verified' and archive.get('native_youtube_bytes') is False and archive.get('artifact_kind') in ARTIFACTS,'variant_archive')
    audio,provenance=proof(archive['audio']),proof(archive['provenance'])
    need('/PublisherVariants/'+audio['sha256']+'/' in audio['remote'] and provenance['remote'].rpartition('/')[0]==audio['remote'].rpartition('/')[0],'variant_remote_identity')
    need(sha(item['provenance_reference_path'])==provenance['sha256'],'provenance_reference_hash')
    metadata=read(item['provenance_reference_path'])
    need(metadata.get('native_youtube_bytes') is False and metadata.get('artifact_kind')==archive['artifact_kind'],'variant_metadata_type')
    need(metadata.get('video_id')==archive.get('video_id') and metadata.get('episode_guid')==archive.get('episode_guid'),'variant_association')
    duration=float(archive['measured_duration_s'])
    need(math.isfinite(duration) and duration>0 and float(metadata['measured_duration_s'])==duration,'variant_duration')
    evidence_path=item.get('language_evidence_path');external=read(evidence_path) if evidence_path else None
    evidence_sha=sha(evidence_path) if evidence_path else None
    language=publisher_language(metadata,archive,external,evidence_sha)
    return {'variant_id':audio['sha256'],'status':'eligible' if language else 'pending_publisher_language_evidence',
            'audio':audio,'provenance':provenance,'audio_path':str(Path(item['audio_path']).resolve()),
            'provenance_path':str(Path(item['provenance_path']).resolve()),'provenance_data':metadata,
            'provenance_reference_path':str(Path(item['provenance_reference_path']).resolve()),
            'archive_receipt_path':str(Path(item['archive_receipt_path']).resolve()),'archive_receipt_sha256':sha(item['archive_receipt_path']),
            'receipt_selector':item.get('receipt_selector'),'language_evidence_path':str(Path(evidence_path).resolve()) if evidence_path else None,
            'language_evidence_sha256':evidence_sha,'language':language,'source_kind':'publisher_audio_variant',
            'associated_youtube_id':archive['video_id'],'channel_dir':archive['channel_dir'],'measured_duration_seconds':duration,
            'publisher_declared_duration_seconds':archive.get('publisher_declared_duration_s'),'episode_guid':archive['episode_guid'],
            'association':{key:metadata.get(key) for key in ['identity_basis','identity_chain','edition_relation','direct_watch_link_present',
                                                          'exact_youtube_id_linked_on_page','association_human_verified','edition_human_verified']},
            'native_youtube_bytes':False}


def prepare(args):
    heartbeat,base,multi=load_helpers(args.pipeline,args.heartbeat_worker);cohort=read(args.cohort)
    need(0<len(cohort['items'])<=POLICY['max_sources'],'cohort_size');jobs=[prepare_job(item) for item in cohort['items']]
    need(len({j['variant_id'] for j in jobs})==len(jobs),'duplicate_variant')
    need(sum(j['audio']['bytes']+j['provenance']['bytes'] for j in jobs)<=POLICY['max_input_bytes'],'cohort_input_budget')
    model=read(base.PROVENANCE_PATH)['model']
    value={'schema_version':1,'profile':PROFILE,'worker_sha256':sha(__file__),'config':POLICY,'config_sha256':digest(POLICY),
           'core_sha256':sha(base.__file__),'multilingual_sha256':sha(multi.__file__),'model':model,'model_manifest_sha256':digest(model),
           'heartbeat_worker_path':str(Path(args.heartbeat_worker).resolve()),'heartbeat_sha256':HEARTBEAT_SHA,
           'cohort_path':str(Path(args.cohort).resolve()),'cohort_sha256':sha(args.cohort),'jobs':jobs,
           'changes_native_audio_count':False,'changes_native_asr_count':False}
    with Path(args.output).open('xb') as output:output.write(encoded(value))
    return {'proposal_sha256':digest(value),'worker_sha256':value['worker_sha256'],'eligible':sum(j['status']=='eligible' for j in jobs),
            'pending_language_evidence':sum(j['status']!='eligible' for j in jobs)}


def binding_for(p,proposal_sha):
    return {**{key:p[key] for key in ['worker_sha256','config_sha256','core_sha256','multilingual_sha256','model_manifest_sha256','heartbeat_sha256','cohort_sha256']},
            'proposal_sha256':proposal_sha}


def verify_proposal(args):
    need(sha(args.proposal)==args.proposal_sha256,'proposal_hash');p=read(args.proposal)
    need(p['profile']==PROFILE and p['worker_sha256']==sha(__file__) and p['config']==POLICY and p['config_sha256']==digest(POLICY),'proposal_binding')
    heartbeat,base,multi=load_helpers(args.pipeline,p['heartbeat_worker_path'])
    need(p['core_sha256']==sha(base.__file__) and p['multilingual_sha256']==sha(multi.__file__),'helper_changed')
    need(sha(p['cohort_path'])==p['cohort_sha256'],'cohort_hash')
    jobs=[prepare_job(item) for item in read(p['cohort_path'])['items']]
    need(jobs==p['jobs'] and p['model']==read(base.PROVENANCE_PATH)['model'],'proposal_evidence_changed')
    return p,heartbeat,base,multi


def task_runtime(runtime,multi,heartbeat,progress,timing,duration):
    class Task(multi.TaskRuntime):
        def windows(self,path,expected):
            iterator=super().windows(path,expected);total=0
            while True:
                heartbeat(force=True);before=time.monotonic()
                try:start,audio=next(iterator)
                except StopIteration:timing['decode_seconds']+=time.monotonic()-before;break
                timing['decode_seconds']+=time.monotonic()-before
                need(round(start*16000)==total and len(audio)<=30*16000,'variant_window_geometry')
                total+=len(audio);need(total<=int((duration+2)*16000),'variant_decode_limit')
                progress['decoded_samples']=total;yield start,audio
            need(total>0 and abs(total/16000-duration)<=2,'variant_decoded_duration')
        def transcribe(self,audio):
            heartbeat(force=True);need(progress['transcribe_calls_started']<math.ceil((duration+2)/30),'variant_call_limit')
            progress['transcribe_calls_started']+=1;before=time.monotonic();iterator,info=super().transcribe(audio)
            timing['inference_seconds']+=time.monotonic()-before
            def measured():
                while True:
                    heartbeat();begin=time.monotonic()
                    try:value=next(iterator)
                    except StopIteration:
                        timing['inference_seconds']+=time.monotonic()-begin;progress['transcribe_calls_completed']+=1;return
                    timing['inference_seconds']+=time.monotonic()-begin;yield value
            return measured(),info
    return Task(runtime,CONFIG)


def verify_variant(base,receipt):
    need(receipt.get('artifact_kind')=='publisher_variant_asr' and receipt.get('source_kind')=='publisher_audio_variant'
         and receipt.get('native_youtube_bytes') is False and receipt.get('changes_native_asr_count') is False,'variant_receipt_type')
    verified=base.verify_bundle(receipt['bundle']['path'],receipt['bundle']);provenance=verified['provenance']
    need(provenance.get('source_kind')=='publisher_audio_variant' and provenance.get('native_youtube_bytes') is False
         and provenance.get('changes_native_asr_count') is False,'variant_output_type')
    need(provenance['variant_id']==provenance['source_audio']['sha256']==receipt['variant_id'],'variant_output_identity')
    need('asr-'+base.fingerprint(provenance['identity'])[:24]==receipt['run_id']==provenance['run_id'],'variant_run_identity')
    for key in ['source_audio','source_metadata','model','source_lease_id','job_id']:
        need(receipt[key]==provenance[key],'variant_receipt_proof')
    need(all(provenance['identity'][k]==provenance[k] for k in ['source_audio','source_metadata','model','config','worker_sha256',
                                                             'proposal_sha256','environment_lock_sha256','variant_asr']), 'variant_identity_proof')
    need(receipt['config_sha256']==base.fingerprint(provenance['config']) and receipt['artifact_manifest_sha256']==verified['artifact_manifest_sha256'],'variant_manifest_identity')
    need(provenance['identity']['source_variant']==provenance['source_variant'] and provenance['language_evidence']==provenance['source_variant']['language'],'variant_evidence_identity')
    need(provenance['quality']['accuracy_claimed'] is False and provenance['quality']['human_reviewed'] is False,'variant_quality')
    return verified


def run(args):
    args.phase='validate';p,hb,base,multi=verify_proposal(args);settings=base.Settings(**read(args.settings));binding=binding_for(p,args.proposal_sha256)
    admissions=read(args.admissions)['items'];eligible=[j for j in p['jobs'] if j['status']=='eligible']
    need({a['variant_id'] for a in admissions}=={j['variant_id'] for j in eligible} and len(admissions)==len(eligible),'variant_admissions')
    admission_map={a['variant_id']:a for a in admissions};runtime=None;receipts=[]
    with base.kernel_lock(settings.root/'sync/asr_gpu_owner.lock'):
        need(base.gpu_lease(settings).get('variant_asr')==binding,'variant_gpu_admission')
        inventory=base.inventory(settings);model=base.model_proof(settings)
        need(model['manifest_sha256']==p['model_manifest_sha256'],'english_model_manifest')
        try:
            for job in eligible:
                args.progress={'variant_id':job['variant_id'],'decoded_samples':0,'transcribe_calls_started':0,'transcribe_calls_completed':0}
                item=admission_map[job['variant_id']];source_path=base.within(item['source_lease_path'],settings.root)
                paths={key:base.within(job[key+'_path'],settings.root) for key in ['audio','provenance']}
                def validate():
                    gpu=base.gpu_lease(settings);source=read(source_path)
                    need(gpu.get('variant_asr')==binding and source.get('variant_asr')==binding,'variant_lease_binding')
                    need(all(gpu.get('model',{}).get(k)==model[k] for k in ['repository','revision','model_sha256']),'gpu_model_binding')
                    need(source.get('schema_version')==1 and source.get('state')=='active' and source.get('profile')==PROFILE,'variant_source_state')
                    need(source.get('owner')==settings.gpu_owner and source.get('lease_id')==item['source_lease_id'],'variant_source_owner')
                    need(source.get('source_variant_id')==job['variant_id'] and source.get('source_audio')==job['audio'] and source.get('source_provenance')==job['provenance'],'variant_source_proof')
                    need(source.get('publisher_language_evidence_sha256')==job['language']['evidence_sha256'] and source.get('native_youtube_bytes') is False,'variant_language_lease')
                    need({str(Path(x).resolve()) for x in source.get('input_paths',[])}=={str(x) for x in paths.values()},'variant_source_paths')
                    return min(hb.epoch(gpu['expires_at']),hb.epoch(source['expires_at']))
                heartbeat=hb.Heartbeat(validate,POLICY['wall_seconds']);heartbeat(force=True);begin=time.monotonic();timing={'decode_seconds':0.,'inference_seconds':0.}
                for key,path in paths.items():
                    observed=base.hashes(path);need(all(observed[k]==job[key][k] for k in ['bytes','md5','sha256']),'variant_input_hash')
                need(read(paths['provenance'])==job['provenance_data'],'variant_provenance_changed')
                source_variant={k:job[k] for k in ['variant_id','source_kind','associated_youtube_id','channel_dir','measured_duration_seconds',
                                                    'publisher_declared_duration_seconds','episode_guid','association','native_youtube_bytes','language']}
                identity={'schema':1,'profile':PROFILE,'worker_sha256':sha(__file__),'proposal_sha256':args.proposal_sha256,
                          'source_variant':source_variant,'source_audio':job['audio'],'source_metadata':job['provenance'],
                          'model':model,'config':CONFIG,'variant_asr':binding,'environment_lock_sha256':base.hashes(settings.environment_lock)['sha256']}
                run_id='asr-'+base.fingerprint(identity)[:24];source_id='publisher-'+job['variant_id'];job_id='variant-asr-'+job['variant_id'][:24]
                destination=settings.output_root/source_id/run_id;need(not destination.exists(),'variant_result_exists')
                admission={'video_id':source_id,'job_id':job_id,'source_lease_id':item['source_lease_id'],'job':{'audio':job['audio'],'metadata':job['provenance']}}
                monitor=None
                try:
                    args.phase='load_english_cuda';heartbeat(force=True);gpu=base.gpu_lease(settings)
                    if runtime is None:
                        before=time.monotonic();runtime=multi.Runtime(settings,gpu);timing['model_load_seconds']=time.monotonic()-before
                    else:timing['model_load_seconds']=0.
                    need(runtime.model.model.device=='cuda' and runtime.model.model.compute_type=='int8_float16','cpu_fallback_forbidden')
                    monitor=multi.Monitor(runtime,heartbeat,gpu['rolling_utilization_target']*100,gpu['max_vram_bytes']);monitor.begin()
                    args.phase='variant_transcribe';started_at=base.now()
                    task=task_runtime(runtime,multi,heartbeat,args.progress,timing,job['measured_duration_seconds'])
                    segments,text,vad=base.collect_segments(task,paths['audio'],job['measured_duration_seconds'],monitor.guard)
                    heartbeat(force=True);telemetry=monitor.finish();monitor=None
                    need(round(segments['duration_seconds']*16000)==args.progress['decoded_samples'],'variant_sample_extent')
                    for key,path in paths.items():
                        observed=base.hashes(path);need(all(observed[k]==job[key][k] for k in ['bytes','md5','sha256']),'variant_input_changed')
                    timing['elapsed_seconds']=time.monotonic()-begin;telemetry.update(guard=heartbeat.counters,timings=timing)
                    duration=segments['duration_seconds']
                    provenance={'schema_version':1,'status':'local_transcription_complete_unreviewed','run_id':run_id,'job_id':job_id,
                                'source_video_id':source_id,'source_kind':'publisher_audio_variant','variant_id':job['variant_id'],
                                'associated_youtube_id':job['associated_youtube_id'],'channel_dir':job['channel_dir'],'source_variant':source_variant,
                                'native_youtube_bytes':False,'changes_native_asr_count':False,'changes_native_audio_count':False,
                                'source_lease_id':item['source_lease_id'],'source_audio':job['audio'],'source_metadata':job['provenance'],
                                'original_publisher_provenance':job['provenance_data'],'language_evidence':job['language'],
                                'model':model,'identity':identity,'config':CONFIG,'worker_sha256':sha(__file__),'variant_asr':binding,'proposal_sha256':args.proposal_sha256,
                                'source_admission_sha256':args.proposal_sha256,'started_at':started_at,'finished_at':base.now(),
                                'dependencies':runtime.dependencies,'environment_lock_sha256':identity['environment_lock_sha256'],
                                'compute':{'device':'cuda:0','compute_type':'int8_float16','cpu_asr_fallback':False,'gpu_lease_id':settings.gpu_lease_id},
                                'metrics':{'audio_seconds':duration,'decoded_samples':args.progress['decoded_samples'],'measured_container_duration_seconds':job['measured_duration_seconds'],
                                           'decoded_minus_container_duration_seconds':duration-job['measured_duration_seconds'],'duration_difference_interpretation':'unreviewed_container_or_encoder_delay_difference',
                                           'duration_after_vad_seconds':vad,'segment_count':len(segments['segments']),'inference_decode_pacing_seconds':timing['elapsed_seconds']},
                                'quality':{'accuracy_claimed':False,'human_reviewed':False,'speech_coverage_validated':False,
                                           'word_times_are_model_estimates':True,'native_youtube_alignment_validated':False,'edition_equivalence_human_verified':False},'inventory':inventory}
                    args.phase='write_variant_result';heartbeat(force=True)
                    receipt=base.write_bundle(settings,admission,run_id,segments,text,telemetry,provenance)
                    receipt.update(artifact_kind='publisher_variant_asr',variant_id=job['variant_id'],source_kind='publisher_audio_variant',
                                   associated_youtube_id=job['associated_youtube_id'],native_youtube_bytes=False,changes_native_asr_count=False)
                    receipt_path=destination/'receipt.json';base.atomic_json(receipt_path,receipt);verify_variant(base,receipt)
                    receipts.append({'receipt_path':str(receipt_path),'run_id':run_id,'variant_id':job['variant_id'],'proof':receipt['bundle']})
                finally:
                    original=sys.exc_info()[1]
                    try:
                        if monitor:monitor.finish()
                    except Exception:
                        if original is None:raise
        finally:
            original=sys.exc_info()[1]
            try:
                if runtime:runtime.close()
            except Exception:
                if original is None:raise
    return {'status':'local_publisher_variant_asr_complete','results':receipts,'native_asr_promoted':False,'uploaded':False}


def publish_result(receipt_path,drive,pipeline):
    sys.path.insert(0,str(Path(pipeline).resolve()));import gpu_asr as base
    receipt_path=Path(receipt_path).resolve();receipt=read(receipt_path);root=Path(receipt['private_root']).resolve()
    need(receipt_path.is_relative_to(root/'asr/results'),'variant_receipt_location')
    bundle=Path(receipt['bundle']['path']).resolve()
    need(bundle==receipt_path.parent/(receipt['run_id']+'.zip'),'variant_bundle_location')
    verified=verify_variant(base,receipt);p=verified['provenance']
    remote=p['source_audio']['remote'].rpartition('/')[0]+'/ASR/'+receipt['run_id']+'/'+receipt['run_id']+'.zip'
    drive.copy(bundle,remote);observed=drive.stat(remote)
    hashes={k.lower():v for k,v in observed.get('Hashes',{}).items()} if isinstance(observed,dict) else {}
    need(isinstance(observed,dict) and observed.get('ID') and observed.get('Size')==verified['bundle']['bytes']
         and hashes.get('md5','').lower()==verified['bundle']['md5'],'variant_drive_proof')
    record={'schema_version':1,'status':'verified','artifact_kind':'publisher_variant_asr','verified_at':base.now(),
            'variant_id':receipt['variant_id'],'associated_youtube_id':p['associated_youtube_id'],'channel_dir':p['channel_dir'],
            'source_audio':p['source_audio'],'source_provenance':p['source_metadata'],'source_variant':p['source_variant'],
            'source_lease_id':p['source_lease_id'],'run_id':receipt['run_id'],'remote':remote,'drive_id':observed['ID'],**verified['bundle'],
            'quality_state':'unreviewed_asr','model':p['model'],'language_evidence':p['language_evidence'],'metrics':p['metrics'],
            'native_youtube_bytes':False,'changes_native_audio_count':False,'changes_native_asr_count':False}
    with base.kernel_lock(root/'sync/publisher_variant_asr_manifest_append.lock'):
        with (root/'sync/publisher_variant_asr_manifest.jsonl').open('ab') as journal:
            journal.write(encoded(record));journal.flush();os.fsync(journal.fileno())
        receipt.update(drive_upload='verified',remote_proof=record);base.atomic_json(receipt_path,receipt)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['prepare','run'])
    for key in ['pipeline','heartbeat-worker','cohort','output','proposal','proposal-sha256','settings','admissions']:
        parser.add_argument('--'+key)
    args=parser.parse_args()
    try:print(json.dumps(prepare(args) if args.mode=='prepare' else run(args)));return 0
    except Exception as error:
        frames=[];tb=error.__traceback__
        while tb:
            frames.append({'module':Path(tb.tb_frame.f_code.co_filename).name,'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno});tb=tb.tb_next
        print(json.dumps({'status':'held','error_class':str(error) if isinstance(error,VariantError) else type(error).__name__,
                          'phase':getattr(args,'phase','prepare'),'progress':getattr(args,'progress',{}),'frames':frames[-10:]}));return 3


if __name__=='__main__':raise SystemExit(main())
