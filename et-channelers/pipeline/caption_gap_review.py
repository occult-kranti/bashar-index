"""Explicit, leased, offline review of uncued intervals; no source acquisition.

Imports are inert. Published captions are immutable inputs. VAD and decode use
existing host preprocessing; recognition is CUDA-only and limited to VAD-positive
uncued ranges. Results are alternatives requiring review, never completion proof.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import zipfile

VERSION = 'caption-gap-review-v3'
RATE = 16000
CONFIG = {'vad_context_ms': 2000, 'asr_context_ms': 2000, 'asr_core_ms': 24000,
          'vad_threshold': 0.5, 'vad_min_speech_ms': 100, 'vad_min_silence_ms': 200,
          'vad_speech_pad_ms': 0, 'sample_rate': RATE, 'max_source_seconds': 4600,
          'max_gap_seconds': 240, 'max_retained_pcm_bytes': 64000000,
          'max_asr_input_seconds': 900, 'max_output_bytes': 20000000,
          'max_wall_seconds': 1800,
          'decoded_duration_tolerance_seconds': 2,
          'eof_policy': 'clip_to_measured_samples_preserve_unreviewed_metadata_tail',
          'word_scalar_policy': 'explicit_finite_float_and_python_bool_v1',
          'max_asr_workspace_bytes': 200000000, 'cpu_asr_fallback': False,
          'speech_coverage_validated': False, 'human_reviewed': False}
FILES = {'gap_review.json', 'segments.json', 'transcript.txt', 'telemetry.json',
         'provenance.json', 'artifact_manifest.json'}


class GapError(RuntimeError):
    pass


def need(condition, kind):
    if not condition:
        raise GapError(kind)


PHASES = {'initialization','validate_inputs','verify_model','claim_source','decode',
          'vad','load_cuda_model','asr_transcribe','asr_words','serialize_result',
          'verify_result','write_receipt','cleanup'}


def safe_diagnostic(error, phase, runtime_state=None):
    """Code locations only: never exception messages, source lines, or locals."""
    frames=[];current=error.__traceback__
    while current is not None:
        code=current.tb_frame.f_code
        module=Path(code.co_filename).name
        function=code.co_name
        frames.append({'module':module if re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',module) else 'unknown',
                       'function':function if re.fullmatch(r'[A-Za-z0-9_<>]{1,100}',function) else 'unknown',
                       'line':int(current.tb_lineno)})
        current=current.tb_next
    name=type(error).__name__
    runtime_state=runtime_state or {}
    return {'schema_version':1,'phase':phase if phase in PHASES else 'initialization',
            'exception_class':name if re.fullmatch(r'[A-Za-z0-9_]{1,80}',name) else 'Exception',
            'frames':frames[-12:],'messages_or_locals_included':False,
            'runtime':{k:runtime_state.get(k) is True for k in ('cuda_model_load_attempted','cuda_model_constructed','telemetry_start_attempted','telemetry_started')}}


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(',', ':')) + '\n').encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def merge(intervals):
    result = []
    for a, b in sorted(intervals):
        need(type(a) is int and type(b) is int and 0 <= a < b, 'interval_invalid')
        if result and a <= result[-1][1]:
            result[-1][1] = max(result[-1][1], b)
        else:
            result.append([a, b])
    return result


def complement(intervals, end):
    result, cursor = [], 0
    for a, b in merge(intervals):
        need(b <= end, 'interval_duration')
        if a > cursor:
            result.append([cursor, a])
        cursor = b
    if cursor < end:
        result.append([cursor, end])
    return result


def intersection(left, right):
    result = []
    for a, b in left:
        for c, d in right:
            if max(a, c) < min(b, d):
                result.append([max(a, c), min(b, d)])
    return merge(result)


def padded(intervals, padding, end):
    return merge([[max(0, a-padding), min(end, b+padding)] for a, b in intervals])


def proof_file(path, proof):
    path = Path(path)
    need(path.is_file() and not path.is_symlink(), 'cached_input_missing')
    need(path.stat().st_size == proof['bytes'] and file_hash(path) == proof['sha256'], 'cached_input_hash')
    need(proof.get('drive_id') and proof.get('remote'), 'archive_proof_missing')


def read_proposal(path, expected):
    path = Path(path)
    need(path.stat().st_size < 2000000 and file_hash(path) == expected, 'proposal_hash')
    proposal = json.loads(path.read_text(encoding='utf-8'))
    video_id = proposal['source']['video_id']
    need(video_id == 'BBiOB7z3pOU', 'proposal_scope')
    c = proposal['coverage']; end = c['duration_ms']
    need(type(end) is int and 0 < end <= CONFIG['max_source_seconds']*1000, 'duration_policy')
    metadata = proposal['source_metadata']
    proof_file(metadata['private_path'], metadata['proof'])
    info = json.loads(Path(metadata['private_path']).read_text(encoding='utf-8'))
    need(info.get('source', {}).get('video_id') == video_id, 'metadata_identity')
    language = info.get('languages', {}).get('audio') or info.get('metadata', {}).get('language')
    need(language in {'en', 'en-US', 'en-GB', 'en-AU', 'en-CA'} and language == metadata['language'], 'english_not_proven')
    need(round(float(info['metadata']['duration'])*1000) == end, 'metadata_duration')
    all_cues = []
    for track in proposal['caption_tracks']:
        proof_file(track['private_path'], track['proof'])
        with zipfile.ZipFile(track['private_path']) as bundle:
            names = bundle.namelist()
            need(len(names) == len(set(names)) and sum(i.file_size for i in bundle.infolist()) <= 20000000, 'caption_zip_limits')
            need(bundle.testzip() is None, 'caption_crc')
            provenance = json.loads(bundle.read('provenance.json'))
            source = json.loads(bundle.read('segments.json'))
        need(all(provenance.get(k) == track[k] for k in ('track_id', 'kind', 'language')), 'caption_identity')
        need(provenance.get('video_id') == video_id and provenance.get('machine_translated') is False, 'caption_source')
        cues = []
        for segment in source['segments']:
            a, b = segment.get('start'), segment.get('end')
            need(all(type(x) in (int, float) and math.isfinite(x) for x in (a, b)) and 0 <= a <= b, 'unknown_caption_timing')
            a, b = max(0, min(end, round(a*1000))), max(0, min(end, round(b*1000)))
            if a < b:
                cues.append([a, b])
        need(cues == track['cue_intervals_ms'] and digest(cues) == track['cue_intervals_sha256'], 'caption_intervals')
        all_cues.extend(cues)
    union = merge(all_cues); gaps = complement(union, end)
    need(union == c['cue_union_ms'] and digest(union) == c['cue_union_sha256'], 'cue_union')
    need(gaps == c['uncovered_intervals_ms'] and digest(gaps) == c['uncovered_intervals_sha256'], 'gap_intervals')
    need(sum(b-a for a,b in gaps) <= CONFIG['max_gap_seconds']*1000, 'gap_scope_limit')
    return proposal


def make_plan(proposal, proposal_sha, pipeline):
    duration = proposal['coverage']['duration_ms']
    gaps = proposal['coverage']['uncovered_intervals_ms']
    windows = padded(gaps, CONFIG['vad_context_ms'], duration)
    pcm_bytes = sum(b-a for a,b in windows)*RATE*4//1000
    need(pcm_bytes <= CONFIG['max_retained_pcm_bytes'], 'pcm_budget')
    vad_root = Path(sys.prefix)/'Lib/site-packages/faster_whisper'
    need((vad_root/'assets/silero_vad_v6.onnx').is_file(), 'existing_vad_required')
    return {'schema_version': 1, 'profile': VERSION, 'video_id': proposal['source']['video_id'],
            'proposal_sha256': proposal_sha, 'worker_sha256': file_hash(__file__),
            'core_worker_sha256': file_hash(Path(pipeline)/'gpu_asr.py'),
            'config_sha256': digest(CONFIG), 'config': CONFIG,
            'vad_model_sha256': file_hash(vad_root/'assets/silero_vad_v6.onnx'),
            'vad_source_sha256': file_hash(vad_root/'vad.py'),
            'source_audio': proposal['source_audio'], 'source_metadata': proposal['source_metadata']['proof'],
            'duration_ms': duration, 'uncued_ms': sum(b-a for a,b in gaps),
            'vad_windows_ms': windows, 'vad_input_ms': sum(b-a for a,b in windows),
            'retained_pcm_bytes': pcm_bytes, 'output_kind': 'derived_gap_asr_unreviewed',
            'changes_provider_captions': False, 'whole_audio_transcribed': False,
            'absence_of_vad_speech_is_not_completion': True,
            'host_preprocessing': 'PyAV decode and existing CPU Silero VAD; all ASR CUDA'}


def available_windows(arrays, ranges, written, total, declared_samples):
    """Clip only the contiguous decoded EOF, never missing interior samples."""
    need(type(total) is int and total > 0, 'decode_empty')
    need(abs(total-declared_samples) <= CONFIG['decoded_duration_tolerance_seconds']*RATE, 'decoded_duration_mismatch')
    need(len(arrays)==len(ranges)==len(written), 'decode_window_count')
    usable, available = [], []
    for array,(a,b),n in zip(arrays,ranges,written):
        expected=max(0,min(b,total)-a)
        need(len(array)==b-a and n==expected, 'gap_decode_incomplete')
        if expected:
            usable.append(array[:expected])
            available.append([a,a+expected])
    analysis_end=min(total,declared_samples)
    tail=[[analysis_end,declared_samples]] if total<declared_samples else []
    return usable,available,{'declared_duration_samples':declared_samples,
            'decoded_sample_count':total,'decoded_seconds':total/RATE,
            'duration_delta_seconds':(total-declared_samples)/RATE,
            'available_analysis_end_sample':analysis_end,
            'unreviewed_declared_tail_source_samples':tail,
            'missing_declared_tail_seconds':max(0,declared_samples-total)/RATE,
            'planned_vad_input_samples':sum(b-a for a,b in ranges),
            'available_vad_input_samples':sum(b-a for a,b in available),
            'available_vad_windows_source_samples':available,
            'metadata_duration_changed':False,'tail_padded':False,
            'speech_coverage_validated':False}


def decode_windows(path, duration_ms, windows_ms, guard):
    import av
    import numpy as np
    ranges = [[a*16, b*16] for a,b in windows_ms]
    arrays = [np.empty(b-a, dtype=np.float32) for a,b in ranges]
    written = [0]*len(arrays); total = 0; origin = None
    maximum = duration_ms*16+CONFIG['decoded_duration_tolerance_seconds']*RATE
    with av.open(str(path)) as container:
        need(len(container.streams.audio) == 1 and not container.streams.video, 'audio_only_source')
        resampler = av.AudioResampler(format='fltp', layout='mono', rate=RATE)
        def frames():
            for original in container.decode(audio=0):
                need(original.sample_rate > 0 and original.samples/original.sample_rate <= 30, 'decode_frame_limit')
                yield from resampler.resample(original)
            yield from resampler.resample(None)
        for frame in frames():
            guard()
            values = frame.to_ndarray().reshape(-1)
            need(np.isfinite(values).all() and total+len(values) <= maximum, 'decode_limit')
            need(frame.pts is not None and frame.time_base is not None, 'decode_time_missing')
            timestamp = float(frame.pts*frame.time_base)
            if origin is None:
                origin = timestamp
                need(abs(origin) <= 0.1, 'decode_origin')
            need(abs(timestamp-origin-total/RATE) <= 0.05, 'decode_discontinuity')
            for i,(a,b) in enumerate(ranges):
                lo, hi = max(total,a), min(total+len(values),b)
                if lo < hi:
                    arrays[i][lo-a:hi-a] = values[lo-total:hi-total]
                    written[i] += hi-lo
            total += len(values)
    usable,available,evidence=available_windows(arrays,ranges,written,total,duration_ms*16)
    evidence.update(first_pcm_pts_seconds=origin,
                    timebase='decoded_sample_clock_from_source_audio_start', pcm_written_to_disk=False)
    return usable,available,evidence


def speech_regions(arrays, windows_samples, gaps_ms, vad, guard):
    found = []
    need(len(arrays)==len(windows_samples),'vad_window_count')
    for audio,(a,b) in zip(arrays, windows_samples):
        need(len(audio)==b-a,'vad_window_extent')
        guard()
        for item in vad(audio):
            lo, hi = item['start'], item['end']
            need(type(lo) is int and type(hi) is int and 0 <= lo < hi <= len(audio), 'vad_time')
            found.append([a+lo, a+hi])
    speech = merge(found)
    return speech, intersection(speech, [[a*16,b*16] for a,b in gaps_ms])


def asr_ranges(speech_gaps, duration_samples):
    # Core intervals never overlap; context may, and is labelled rather than
    # silently inserted into the missing-text output.
    result = []
    for a,b in speech_gaps:
        for start in range(a,b,CONFIG['asr_core_ms']*16):
            end = min(b,start+CONFIG['asr_core_ms']*16)
            result.append({'core': [start,end], 'decode': [max(0,start-CONFIG['asr_context_ms']*16),min(duration_samples,end+CONFIG['asr_context_ms']*16)]})
    need(sum(item['decode'][1]-item['decode'][0] for item in result) <= CONFIG['max_asr_input_seconds']*RATE, 'asr_scope_limit')
    return result


def require_binding(record, binding, kind):
    need(record.get('gap_review') == binding, kind)


def word_evidence(word, decode_range, core_range):
    """Normalize installed-model scalar types at the provenance boundary."""
    lo,hi=decode_range;ca,cb=core_range
    relative_start,relative_end,probability=map(float,(word.start,word.end,word.probability))
    need(all(math.isfinite(x) for x in (relative_start,relative_end,probability)) and
         0<=relative_start<=relative_end<=(hi-lo)/RATE+0.05 and 0<=probability<=1,'word_timing')
    need(isinstance(word.word,str),'word_text_type')
    start,end=lo/RATE+relative_start,lo/RATE+relative_end
    midpoint=(start+end)*RATE/2
    return {'start':start,'end':end,'text':word.word.strip(),'probability':probability,
            'midpoint_inside_uncued_vad_speech':bool(ca<=midpoint<cb),
            'crosses_core_boundary':bool(start*RATE<ca or end*RATE>cb)}


def verify_result(path):
    need(Path(path).stat().st_size <= CONFIG['max_output_bytes'], 'result_size')
    with zipfile.ZipFile(path) as bundle:
        need(len(bundle.namelist()) == len(FILES) and set(bundle.namelist()) == FILES, 'result_members')
        need(sum(i.file_size for i in bundle.infolist()) <= CONFIG['max_output_bytes'], 'result_expansion')
        need(bundle.testzip() is None, 'result_crc')
        manifest = json.loads(bundle.read('artifact_manifest.json'))
        need(set(manifest) == FILES-{'artifact_manifest.json'}, 'result_manifest')
        for name, proof in manifest.items():
            raw=bundle.read(name)
            need(len(raw)==proof['bytes'] and hashlib.sha256(raw).hexdigest()==proof['sha256'], 'result_hash')
        provenance=json.loads(bundle.read('provenance.json'))
        need(provenance['quality_state']=='unreviewed_gap_asr' and provenance['speech_coverage_validated'] is False and provenance['cpu_asr_fallback'] is False, 'result_quality')
        review=json.loads(bundle.read('gap_review.json'))
        duration=review['decode']['available_analysis_end_sample']/RATE
        speech_gaps=review['uncued_speech_source_samples']
        transcript=bundle.read('transcript.txt').decode('utf-8')
        words=json.loads(bundle.read('segments.json'))['selected_words']
        for word in words:
            need(transcript[word['char_start']:word['char_end']]==word['text'], 'result_text_offsets')
            need(all(type(word[k]) in (int,float) and math.isfinite(word[k]) for k in ['start','end']) and 0<=word['start']<=word['end']<=duration+0.05,'result_word_time')
            midpoint=(word['start']+word['end'])*RATE/2
            need(any(a<=midpoint<b for a,b in speech_gaps) and word['midpoint_inside_uncued_vad_speech'] is True,'result_word_scope')
        if review['status']=='no_vad_speech_detected_in_uncued_intervals':
            need(not speech_gaps and not words and not transcript,'empty_vad_evidence')
    return provenance


def execute(args):
    args._phase='validate_inputs'
    args._runtime_state={}
    started=time.monotonic()
    sys.path.insert(0,str(Path(args.pipeline).resolve()))
    import gpu_asr as core
    import gpu_asr_queue as queue
    proposal=read_proposal(args.proposal,args.proposal_sha256)
    plan=make_plan(proposal,args.proposal_sha256,args.pipeline)
    plan_sha=digest(plan)
    data=json.loads(Path(args.settings).read_text(encoding='utf-8'))
    settings=core.Settings(**data)
    binding={k:plan[k] for k in ['proposal_sha256','worker_sha256','core_worker_sha256','config_sha256']}
    binding['plan_sha256']=plan_sha
    runtime=monitor=None
    with core.kernel_lock(settings.root/'sync/asr_gpu_owner.lock'):
        lease=core.gpu_lease(settings)
        require_binding(lease,binding,'gpu_gap_binding')
        admission,objects,admission_sha=core.validate_admission(settings,args.admission)
        require_binding(admission,binding,'source_gap_binding')
        need(admission['job']['audio']==plan['source_audio'] and admission['job']['metadata']==plan['source_metadata'],'proposal_source_binding')
        args._phase='verify_model'
        model=core.model_proof(settings)
        inventory=core.inventory(settings,extra=CONFIG['max_output_bytes'])
        need(queue.tree_bytes(settings.root/'asr')+CONFIG['max_output_bytes'] <= CONFIG['max_asr_workspace_bytes'],'asr_workspace_cap')
        run_id='gap-'+digest({'plan':plan_sha,'admission':admission_sha,'model':model})[:24]
        output=Path(settings.output_root)/run_id
        need(not output.exists(),'gap_run_exists_no_automatic_retry')
        args._phase='claim_source'
        queue.claim_input(settings.root,admission,settings.gpu_owner)
        last_guard=[-1.0]
        def guard():
            need(time.monotonic()-started <= CONFIG['max_wall_seconds'],'gap_review_wall_limit')
            # Decode frames can be 20ms; bound control-file reads without
            # allowing more than half a second of lease-check staleness.
            if time.monotonic()-last_guard[0] < 0.5:
                return
            last_guard[0]=time.monotonic()
            current=core.gpu_lease(settings)
            require_binding(current,binding,'gpu_gap_binding')
            source=core.read_json(admission['source_lease'])
            need(source.get('status')=='active' and source.get('lease_id')==admission['source_lease_id'] and source.get('consumer_owner')==settings.gpu_owner and core.unexpired(source.get('expires_at')),'source_lease_lost')
        try:
            args._phase='decode'
            arrays,available_windows_samples,decode=decode_windows(objects['audio'],plan['duration_ms'],plan['vad_windows_ms'],guard)
            args._phase='vad'
            from faster_whisper.vad import get_speech_timestamps, VadOptions
            options=VadOptions(threshold=CONFIG['vad_threshold'],min_speech_duration_ms=CONFIG['vad_min_speech_ms'],min_silence_duration_ms=CONFIG['vad_min_silence_ms'],speech_pad_ms=0)
            vad=lambda audio:get_speech_timestamps(audio,vad_options=options,sampling_rate=RATE)
            speech,uncued=speech_regions(arrays,available_windows_samples,proposal['coverage']['uncovered_intervals_ms'],vad,guard)
            ranges=asr_ranges(uncued,decode['available_analysis_end_sample'])
            selected=[]; windows=[]; parts=[]; offset=0
            telemetry={'sample_count':0,'asr_model_loaded':False}
            if ranges:
                args._phase='load_cuda_model'
                args._runtime_state['cuda_model_load_attempted']=True
                runtime=core.CudaRuntime(settings,lease)
                args._runtime_state['cuda_model_constructed']=True
                monitor=core.Monitor(runtime.sample,guard,lease['rolling_utilization_target']*100,lease['max_vram_bytes'])
                args._runtime_state['telemetry_start_attempted']=True
                monitor.begin()
                args._runtime_state['telemetry_started']=True
            for n,item in enumerate(ranges):
                monitor.guard()
                lo,hi=item['decode']; ca,cb=item['core']
                containing=[i for i,(a,b) in enumerate(available_windows_samples) if a<=lo and hi<=b]
                need(len(containing)==1,'asr_range_not_retained')
                i=containing[0]; origin=available_windows_samples[i][0]
                audio=arrays[i][lo-origin:hi-origin]
                config=dict(core.CONFIG,vad_filter=False)
                config.pop('vad_parameters',None)
                args._phase='asr_transcribe'
                iterator,_=runtime.model.transcribe(audio,**config)
                evidence=[]
                for segment in iterator:
                    monitor.guard()
                    need(segment.words is not None,'word_timing_required')
                    args._phase='asr_words'
                    for word in segment.words:
                        value=word_evidence(word,[lo,hi],[ca,cb])
                        evidence.append(value)
                        if value['midpoint_inside_uncued_vad_speech'] and value['text']:
                            if parts:offset+=1
                            chosen=dict(value,char_start=offset,char_end=offset+len(value['text']),window=n)
                            selected.append(chosen);parts.append(value['text']);offset=chosen['char_end']
                            need(offset<1000000,'text_budget')
                windows.append({'core_source_samples':[ca,cb],'decode_source_samples':[lo,hi],'words':evidence})
            if monitor:
                telemetry=monitor.finish();monitor=None
                telemetry['asr_model_loaded']=True
            guard()
            args._phase='serialize_result'
            status='vad_speech_with_asr_candidates' if selected else 'vad_speech_no_recognized_words' if uncued else 'no_vad_speech_detected_in_uncued_intervals'
            review={'schema_version':1,'status':status,'plan':plan,'decode':decode,
                    'vad_speech_source_samples':speech,'uncued_speech_source_samples':uncued,
                    'asr_input_seconds':sum(x['decode'][1]-x['decode'][0] for x in ranges)/RATE,
                    'speech_coverage_validated':False,'provider_captions_changed':False,'missing_words_confirmed':False}
            provenance={'schema_version':1,'artifact_kind':'caption_gap_review','quality_state':'unreviewed_gap_asr',
                        'speech_coverage_validated':False,'run_id':run_id,'source_video_id':admission['video_id'],
                        'source_audio':plan['source_audio'],'source_metadata':plan['source_metadata'],
                        'source_lease_id':admission['source_lease_id'],'source_admission_sha256':admission_sha,
                        'plan_sha256':plan_sha,'proposal_sha256':args.proposal_sha256,'worker_sha256':plan['worker_sha256'],
                        'caption_inputs':[{k:t[k] for k in ('track_id','kind','language','proof','cue_intervals_sha256')} for t in proposal['caption_tracks']],
                        'cue_union_sha256':proposal['coverage']['cue_union_sha256'],
                        'uncued_intervals_sha256':proposal['coverage']['uncovered_intervals_sha256'],
                        'source_duration_alignment':decode,
                        'model':model,'config':CONFIG,'gpu_lease_id':settings.gpu_lease_id,'inventory':inventory,
                        'compute':{'asr_model_loaded':bool(ranges),'asr_device':'cuda:0' if ranges else None,
                                   'vad_device':'CPUExecutionProvider','compute_type':'int8_float16' if ranges else None},
                        'cpu_asr_fallback':False,'word_times_are_estimates':True,'finished_at':core.now()}
            members={'gap_review.json':encoded(review),'segments.json':encoded({'schema_version':1,'timebase':'source_audio_seconds','selected_words':selected,'windows':windows}),
                     'transcript.txt':(' '.join(parts)+('\n' if parts else '')).encode(),'telemetry.json':encoded(telemetry),'provenance.json':encoded(provenance)}
            members['artifact_manifest.json']=encoded({k:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in members.items()})
            need(sum(map(len,members.values()))<=CONFIG['max_output_bytes']//2,'output_budget')
            output.mkdir(parents=True,exist_ok=False)
            artifact=output/(run_id+'.zip')
            with zipfile.ZipFile(artifact,'x',compression=zipfile.ZIP_DEFLATED) as bundle:
                for name,raw in members.items():bundle.writestr(name,raw)
            args._phase='verify_result'
            verify_result(artifact)
            receipt={'schema_version':1,'status':'local_gap_review_complete_unreviewed','artifact_kind':'caption_gap_review',
                     'run_id':run_id,'video_id':admission['video_id'],'bundle':str(artifact),'proof':core.hashes(artifact),
                     'plan_sha256':plan_sha,'source_lease_id':admission['source_lease_id'],'source_audio':plan['source_audio'],
                     'changes_collection_completion':False,'source_inputs_deleted':False}
            args._phase='write_receipt'
            core.atomic_json(output/'local_receipt.json',receipt)
            with queue.queue_lock(settings.root):
                source=core.read_json(admission['source_lease'])
                need(source.get('lease_id')==admission['source_lease_id'] and source.get('consumer_owner')==settings.gpu_owner,'source_lease_lost')
                source.update(phase='awaiting_result_upload',result_kind='caption_gap_review',result_receipt=str(output/'local_receipt.json'))
                queue.atomic(Path(admission['source_lease']),source)
            return {'status':receipt['status'],'run_id':run_id,'selected_word_count':len(selected),'speech_gap_seconds':sum(b-a for a,b in uncued)/RATE,'asr_input_seconds':review['asr_input_seconds'],'bundle_bytes':receipt['proof']['bytes']}
        finally:
            original_error=sys.exc_info()[1]
            try:
                if monitor:monitor.finish()
                if runtime:runtime.close()
            except Exception:
                # Never replace the original source/ASR failure with cleanup.
                if original_error is None:
                    args._phase='cleanup'
                    raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['plan','run','verify'])
    parser.add_argument('--pipeline');parser.add_argument('--proposal');parser.add_argument('--proposal-sha256')
    parser.add_argument('--output');parser.add_argument('--settings');parser.add_argument('--admission');parser.add_argument('--bundle')
    args=parser.parse_args(argv)
    try:
        if args.mode=='verify':
            value=verify_result(args.bundle);print(json.dumps({'verified':True,'run_id':value['run_id']}));return 0
        if args.mode=='plan':
            value=make_plan(read_proposal(args.proposal,args.proposal_sha256),args.proposal_sha256,args.pipeline)
            if args.output:
                with Path(args.output).open('xb') as target:target.write(encoded(value))
            print(json.dumps({'plan_sha256':digest(value),**{k:value[k] for k in ['duration_ms','uncued_ms','vad_input_ms','retained_pcm_bytes','worker_sha256']}}));return 0
        print(json.dumps(execute(args)));return 0
    except Exception as error:
        diagnostic=safe_diagnostic(error,getattr(args,'_phase','initialization'),getattr(args,'_runtime_state',None))
        code=diagnostic['exception_class']
        if isinstance(error,GapError) or (type(error).__module__=='gpu_asr' and type(error).__name__=='AsrError'):
            value=str(error)
            if re.fullmatch(r'[a-z0-9_]{1,79}',value):code=value
        print(json.dumps({'status':'held','error_class':code,'diagnostic':diagnostic}));return 3


if __name__=='__main__':
    raise SystemExit(main())
