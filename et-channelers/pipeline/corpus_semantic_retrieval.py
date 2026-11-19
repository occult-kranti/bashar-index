"""Offset-bound, cross-creator passage retrieval from frozen English views.

Production: a locally converted float32 MiniLM BERT encoder on CTranslate2 CUDA,
explicit attention-mask mean pooling/L2 on CuPy, and blocked GPU nearest passages.
No model downloads, conversion, CPU inference, event labels or speaker attribution.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

from . import common,corpus_group_lexical as lexical,host_capacity

REPOSITORY='sentence-transformers/all-MiniLM-L6-v2'
REVISION='1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
METHOD='minilm_ct2_float32_mask_mean_l2_cross_creator_v1'
POOLING='attention_mask_mean_including_cls_sep_then_l2'


def load_model_manifest(root,path,sha256):
    root=Path(root).resolve();path=Path(path).resolve()
    if not path.is_relative_to(root):raise ValueError('managed_private_model_manifest_required')
    raw=lexical._checked(path,sha256);value=lexical._object(raw)
    config=value.get('configuration') or {};validation=value.get('validation') or {}
    if (value.get('schema_version')!=1 or value.get('repository')!=REPOSITORY or value.get('revision')!=REVISION
            or value.get('conversion')!='ctranslate2_transformers_float32_no_integer_quantization'
            or config.get('architecture')!='BertModel' or config.get('hidden_size')!=384
            or config.get('max_sequence_length')!=256 or config.get('pooling')!=POOLING
            or not lexical.SHA.fullmatch(str(value.get('source_weights_sha256','')))
            or not isinstance(value.get('files'),list) or not value['files']):
        raise ValueError('pinned_MiniLM_float32_conversion_required')
    # This record can only be supplied after the separate, real CUDA fixture.
    # Authoring CPU fixtures never mark a real conversion/parity as performed.
    proof=validation.get('fixture') or {}
    if validation.get('cuda_fixture_verified') is not True or type(proof.get('bytes')) is not int or proof['bytes']<=0:
        raise ValueError('post_collection_real_CUDA_fixture_required')
    fixture=lexical._object(lexical._checked(lexical._contained(path.parent,proof['path']),proof.get('sha256'),proof['bytes']))
    error=fixture.get('mask_mean_pooling_max_abs_error');repeat=fixture.get('repeatability_max_cosine_error')
    if (fixture.get('model_revision')!=REVISION or fixture.get('device')!='cuda' or fixture.get('compute_type')!='float32'
            or fixture.get('pooling')!=POOLING or fixture.get('dimension')!=384 or fixture.get('maximum_sequence_length')!=256
            or fixture.get('finite_unit_vectors') is not True or fixture.get('full_window_tail_covered') is not True
            or type(error) not in (int,float) or not math.isfinite(error) or not 0<=error<=1e-6
            or type(repeat) not in (int,float) or not math.isfinite(repeat) or not 0<=repeat<=1e-4):
        raise ValueError('CUDA_pooling_protocol_fixture_changed')
    names=set()
    for proof in value['files']:
        name=proof['path']
        if name in names or type(proof.get('bytes')) is not int or proof['bytes']<=0:
            raise ValueError('unique_local_model_artifacts_required')
        names.add(name);local=lexical._contained(path.parent,name)
        lexical._checked(local,proof.get('sha256'),proof['bytes'])
    if not {'model.bin','config.json','tokenizer.json'}<=names:
        raise ValueError('complete_converted_encoder_and_tokenizer_required')
    return dict(value,manifest_sha256=sha256,model_root=str(path.parent))


class LocalTokenizer:
    """CPU text indexing only, never neural inference or silent truncation."""
    def __init__(self,path):
        from tokenizers import Tokenizer
        self.tokenizer=Tokenizer.from_file(str(path));self.tokenizer.no_truncation();self.tokenizer.no_padding()
        self.special=(self.tokenizer.token_to_id('[CLS]'),self.tokenizer.token_to_id('[SEP]'))
        if self.special!=(101,102):raise ValueError('pinned_BERT_special_tokens_required')
    def encode(self,text):return self.tokenizer.encode(text,add_special_tokens=False)


def chunk_spans(view,tokenizer,*,max_sequence_length=256,overlap_tokens=64):
    """Cover the entire view, including arbitrarily long chapters, in token windows."""
    if (max_sequence_length!=256 or type(overlap_tokens) is not int or not 0<=overlap_tokens<254):
        raise ValueError('MiniLM_256_token_context_required')
    text=view['text'];encoding=tokenizer.encode(text);ids=list(encoding.ids);offsets=list(encoding.offsets)
    if len(ids)!=len(offsets) or any(type(token) is not int or token<0 for token in ids):
        raise ValueError('tokenizer_ids_offsets_required')
    previous=(0,0)
    for start,end in offsets:
        if type(start) is not int or type(end) is not int or not 0<=start<end<=len(text) or start<previous[0] or end<previous[1]:
            raise ValueError('original_unicode_codepoint_offsets_required')
        previous=(start,end)
    windows=[];start=0
    while start<len(ids):
        end=min(len(ids),start+254);a=offsets[start][0];b=offsets[end-1][1]
        segments=[]
        for segment in view['segments']:
            left=max(a,segment['char_start']);right=min(b,segment['char_end'])
            if left<right:
                segments.append({'source_segment_id':segment['source_segment_id'],'char_start':left,'char_end':right,
                    'source_segment_char_start':left-segment['char_start'],'source_segment_char_end':right-segment['char_start'],
                    'time_start':segment.get('time_start'),'time_end':segment.get('time_end'),
                    **{key:segment[key] for key in ('source_member','source_paragraph_index','paragraph_index') if key in segment}})
        if not segments:raise ValueError('passage_requires_source_address')
        token_ids=[101]+ids[start:end]+[102]
        windows.append({'token_start':start,'token_end':end,'char_start':a,'char_end':b,'token_ids':token_ids,
            'span_sha256':lexical.digest(text[a:b].encode('utf-8')),'source_segments':segments,
            'full_view_token_count':len(ids),'truncation_applied':False,'token_count_with_specials':len(token_ids)})
        if end==len(ids):break
        start=end-overlap_tokens
    return windows


def collect_chunks(root,data,tokenizer,model_sha256,*,overlap_tokens=64):
    """Infer once for an exact audio/text unit, retain each alias's own source map."""
    root=Path(root).resolve();order,units,_,_=lexical.groups_for(data);chunks=[]
    for unit in order:
        windows=None;combined=[]
        for alias in sorted(units[unit]['aliases'],key=lambda row:row['video_id']):
            selected=alias['view'];raw=lexical._checked(lexical._contained(root,selected['path']),selected['file_sha256'])
            view=lexical._object(raw);current=chunk_spans(view,tokenizer,overlap_tokens=overlap_tokens)
            if windows is None:
                windows=current
                for window in windows:
                    identity=[METHOD,model_sha256,unit,window['token_start'],window['token_end'],window['span_sha256'],
                              lexical.digest(lexical.encoded(window['token_ids']))]
                    combined.append({k:v for k,v in window.items() if k!='source_segments'}|{
                        'chunk_id':lexical.digest(lexical.encoded(identity)),'unit_id':unit,
                        'recording_family':units[unit]['family'],'associations':[]})
            if len(current)!=len(windows):raise ValueError('shared_text_tokenization_changed')
            for item,window,original in zip(combined,current,windows):
                if any(window[k]!=original[k] for k in ('token_ids','char_start','char_end','span_sha256')):
                    raise ValueError('shared_text_tokenization_changed')
                item['associations'].append({'video_id':alias['video_id'],'channel_dir':alias['channel_dir'],
                    'view':dict(selected),'text_sha256':alias['text_sha256'],'text_version_id':alias['text_version_id'],
                    'source_kind':alias['source_kind'],'source_audio_sha256':alias['source_audio_sha256'],
                    'source_edition_id':alias['source_edition_id'],'edition_receipt_sha256':alias['edition_receipt_sha256'],
                    'source_timebase':alias['source_timebase'],'source_segments':window['source_segments'],
                    'timestamps_are_source_segment_bounds_not_verified_word_alignment':True})
        chunks.extend(combined)
    return sorted(chunks,key=lambda row:row['chunk_id'])


def _creators(chunk):return {row['channel_dir'] for row in chunk['associations']}
def _audio(chunk):return {row['source_audio_sha256'] for row in chunk['associations'] if row.get('source_audio_sha256')}


def eligible_pair(left,right):
    return (left['unit_id']!=right['unit_id'] and not _creators(left)&_creators(right)
        and not _audio(left)&_audio(right) and left['span_sha256']!=right['span_sha256']
        and not (left['recording_family'][0]=='confirmed' and left['recording_family']==right['recording_family']))


def cpu_fixture_rank(vectors,chunks,*,top_k=5,fixture_only=False):
    if fixture_only is not True:raise ValueError('CPU_semantic_math_is_fixture_only_no_CPU_inference')
    if (len(vectors)!=len(chunks) or type(top_k) is not int or not 1<=top_k<=100
            or len({len(row) for row in vectors})>1):raise ValueError('embedding_chunk_count_or_dimension_mismatch')
    normalized=[]
    for row in vectors:
        if not row or any(type(v) not in (int,float) or not math.isfinite(v) for v in row):raise ValueError('finite_embedding_required')
        norm=math.sqrt(sum(v*v for v in row))
        if not norm:raise ValueError('zero_embedding')
        normalized.append([v/norm for v in row])
    result=[]
    for i,query in enumerate(chunks):
        scored=[(sum(a*b for a,b in zip(normalized[i],normalized[j])),target['chunk_id'],j)
            for j,target in enumerate(chunks) if eligible_pair(query,target)]
        for rank,(score,_,j) in enumerate(sorted(scored,key=lambda x:(-x[0],x[1]))[:top_k],1):
            result.append(_hit(query,chunks[j],rank,score))
    return result


def cpu_fixture_pool(hidden,lengths,*,fixture_only=False):
    """Toy tensor arithmetic only; never invoke a neural model on the CPU."""
    if fixture_only is not True:raise ValueError('CPU_pooling_is_fixture_only')
    if len(hidden)!=len(lengths):raise ValueError('pooling_batch_lengths')
    output=[]
    for row,length in zip(hidden,lengths):
        if (type(length) is not int or not 2<=length<=len(row) or not row
                or len({len(token) for token in row})!=1 or not row[0]):raise ValueError('pooling_shape')
        mean=[sum(token[column] for token in row[:length])/length for column in range(len(row[0]))]
        norm=math.sqrt(sum(v*v for v in mean))
        if not norm or not all(math.isfinite(v) for v in mean):raise ValueError('pooling_finite_nonzero')
        output.append([v/norm for v in mean])
    return output


def _hit(left,right,rank,score):
    return {'query_chunk_id':left['chunk_id'],'target_chunk_id':right['chunk_id'],'rank':rank,
        'cosine':min(1.,max(-1.,float(score))),
        'pair_id':lexical.digest(lexical.encoded(sorted((left['chunk_id'],right['chunk_id'])))),
        'review_status':'unreviewed_semantic_retrieval_candidate','event_relation_assigned':False,
        'speaker_identity_attributed':False,'score_is_probability':False}


def _codes(values):
    codes={value:i for i,value in enumerate(sorted({v for v in values if v is not None}))}
    return [codes.get(v,-1) for v in values]


def gpu_rank(vectors,chunks,cp,pacer,*,top_k=5,block_size=32):
    """Exact blocked ranking; mask same-source/creator BEFORE selecting top-k."""
    n=len(chunks)
    if vectors.shape!=(n,384) or type(top_k) is not int or not 1<=top_k<=100 or not 1<=block_size<=256:
        raise ValueError('bounded_semantic_rank_shape_required')
    creators=sorted({creator for chunk in chunks for creator in _creators(chunk)})
    creatorpos={creator:i for i,creator in enumerate(creators)};words=(len(creators)+63)//64
    masks=[[sum(1<<(creatorpos[c]%64) for c in _creators(chunk) if creatorpos[c]//64==word)
        for chunk in chunks] for word in range(words)]
    with pacer.block():
        creator_masks=cp.asarray(masks,dtype=cp.uint64)
        units=cp.asarray(_codes([row['unit_id'] for row in chunks]),dtype=cp.int32)
        spans=cp.asarray(_codes([row['span_sha256'] for row in chunks]),dtype=cp.int32)
        families=cp.asarray(_codes([row['recording_family'][1] if row['recording_family'][0]=='confirmed' else None for row in chunks]),dtype=cp.int32)
        # One audio/text inference unit has one exact audio hash or no such proof.
        audio=cp.asarray(_codes([next(iter(_audio(row)),None) for row in chunks]),dtype=cp.int32)
    hits=[]
    for start in range(0,n,block_size):
        stop=min(n,start+block_size)
        with pacer.block():
            scores=vectors[start:stop]@vectors.T
            allowed=(units[start:stop,None]!=units[None,:])&(spans[start:stop,None]!=spans[None,:])
            for word in range(words):
                allowed&=(creator_masks[word,start:stop,None]&creator_masks[word,None,:])==0
            allowed&=~((families[start:stop,None]>=0)&(families[start:stop,None]==families[None,:]))
            allowed&=~((audio[start:stop,None]>=0)&(audio[start:stop,None]==audio[None,:]))
            masked=cp.where(allowed,scores,-cp.inf)
            # CuPy argsort is stable; chunk IDs were sorted before inference.
            positions=cp.argsort(-masked,axis=1)[:,:min(top_k,n)]
            selected=cp.take_along_axis(masked,positions,axis=1)
            host_positions=positions.get().tolist();host_scores=selected.get().tolist()
        for i,(indices,values) in enumerate(zip(host_positions,host_scores),start):
            for rank,(j,score) in enumerate(zip(indices,values),1):
                if math.isfinite(score):hits.append(_hit(chunks[i],chunks[j],rank,score))
    return hits


class CudaMeanEncoder:
    def __init__(self,model,cp):
        import ctranslate2
        self.ct2=ctranslate2;self.cp=cp
        self.encoder=ctranslate2.Encoder(model['model_root'],device='cuda',compute_type='float32',
            inter_threads=1,intra_threads=1,max_queued_batches=1)
        if self.encoder.device!='cuda' or self.encoder.compute_type!='float32':raise ValueError('CUDA_float32_encoder_required')

    def encode(self,ids):
        if not ids or any(not 2<=len(row)<=256 for row in ids):raise ValueError('no_silent_token_truncation')
        result=self.encoder.forward_batch(ids);hidden=result.last_hidden_state
        if str(hidden.device)!='cuda':raise ValueError('CUDA_hidden_states_required_no_CPU_fallback')
        cp=self.cp
        # CT2 can use another stream. Finish its synchronous batch before a
        # different library consumes the CUDA Array Interface view.
        cp.cuda.runtime.deviceSynchronize()
        value=cp.asarray(hidden)
        if value.shape!=(len(ids),max(map(len,ids)),384):raise ValueError('MiniLM_hidden_state_shape')
        lengths=cp.asarray([len(row) for row in ids],dtype=cp.int32)
        mask=cp.arange(value.shape[1])[None,:]<lengths[:,None]
        pooled=(value*mask[:,:,None]).sum(axis=1)/lengths[:,None]
        norms=cp.linalg.norm(pooled,axis=1,keepdims=True)
        if not bool(cp.all(cp.isfinite(pooled))) or not bool(cp.all(norms>0)):raise ValueError('invalid_sentence_embedding')
        return (pooled/norms).astype(cp.float32).copy()

    def close(self):self.encoder.unload_model()


def _jsonl_bytes(rows):return sum(len(lexical.encoded(row))+1 for row in rows)


def verified_existing(target,revision,manifest_sha256,model_sha256,*,expected_chunk_ids=None):
    summary=lexical._object((target/'manifest.json').read_bytes())
    if (summary.get('revision')!=revision or summary.get('method')!=METHOD
            or summary.get('postrun_manifest_sha256')!=manifest_sha256 or summary.get('model_manifest_sha256')!=model_sha256
            or not isinstance(summary.get('files'),dict) or set(summary['files'])!={'chunks.jsonl','ranked-passages.jsonl','embeddings.f32'}):
        raise ValueError('existing_semantic_generation_binding_changed')
    if expected_chunk_ids is not None:
        proof=summary['files']['embeddings.f32']
        if (summary.get('unique_inference_chunks')!=len(expected_chunk_ids) or proof.get('shape')!=[len(expected_chunk_ids),384]
                or proof.get('bytes')!=4*len(expected_chunk_ids)*384):
            raise ValueError('existing_semantic_vector_index_changed')
        with (target/'chunks.jsonl').open('rb') as source:
            actual=[json.loads(line)['chunk_id'] for line in source]
        if actual!=expected_chunk_ids:raise ValueError('existing_semantic_chunk_order_changed')
    for name,proof in summary['files'].items():
        path=lexical._contained(target,name);value=hashlib.sha256();size=0
        with path.open('rb') as source:
            while block:=source.read(1024*1024):value.update(block);size+=len(block)
        if size!=proof.get('bytes') or value.hexdigest()!=proof.get('sha256'):
            raise ValueError('existing_semantic_generation_file_changed')
    return target


def run(root,generation,manifest_sha256,model_manifest,model_sha256,*,top_k=5,overlap_tokens=64,
        batch_size=16,block_size=32,gpu_memory_budget=1_000_000_000):
    root=common.ensure_outside_git(root)
    from . import drive_ingest,gpu_asr,gpu_workload_pacing
    with gpu_asr.kernel_lock(root/'sync/asr_gpu_owner.lock'):
        data=lexical.load_inventory(root,generation,manifest_sha256)
        model=load_model_manifest(root,model_manifest,model_sha256)
        tokenizer=LocalTokenizer(Path(model['model_root'])/'tokenizer.json')
        chunks=collect_chunks(root,data,tokenizer,model_sha256,overlap_tokens=overlap_tokens);n=len(chunks)
        if not n:raise ValueError('no_nonempty_primary_text_chunks')
        if (type(batch_size) is not int or not 1<=batch_size<=64 or type(block_size) is not int
                or not 1<=block_size<=256 or type(top_k) is not int or not 1<=top_k<=100):
            raise ValueError('bounded_semantic_batch_required')
        methods={**data['source_methods'],'semantic_adapter_sha256':lexical.digest(Path(__file__).read_bytes()),
            'gpu_pacing_sha256':lexical.digest(Path(gpu_workload_pacing.__file__).read_bytes())}
        revision=lexical.digest(lexical.encoded([METHOD,manifest_sha256,model_sha256,
            overlap_tokens,top_k,batch_size,block_size,methods,[row['chunk_id'] for row in chunks]]))
        parent=root/'analysis/semantic_retrieval';target=parent/revision
        if target.exists():return verified_existing(target,revision,manifest_sha256,model_sha256,
            expected_chunk_ids=[row['chunk_id'] for row in chunks])
        # Retain only final exact vectors, compact chunk addresses and top-k,
        # not a dense N×N similarity result. Estimate the bounded sorting block.
        owners=len({c for row in chunks for c in _creators(row)})
        estimate=(4*n*384*3 + 32*block_size*n + 8*((owners+63)//64)*n
            + 4*batch_size*256*384*8 + 180_000_000)
        if type(gpu_memory_budget) is not int or estimate>gpu_memory_budget:
            raise ValueError('semantic_GPU_working_budget_deferred')
        address_rows=[{k:v for k,v in row.items() if k!='token_ids'} for row in chunks]
        output_reserve=_jsonl_bytes(address_rows)+4*n*384+n*top_k*1024+1_000_000
        _,occupied=drive_ingest.storage_usage(root,drive_ingest.managed_roots(root))
        future=drive_ingest.reserved_project_growth(root)
        if (occupied+future+output_reserve>host_capacity.MAX_MANAGED_BYTES
                or shutil.disk_usage(root).free-future-output_reserve<host_capacity.MIN_DISK_SPARE):
            raise ValueError('semantic_output_storage_deferred')
        import cupy as cp
        if estimate>cp.cuda.runtime.memGetInfo()[0]:raise ValueError('semantic_CUDA_free_memory_deferred')
        parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            stage=Path(temporary)/'outputs';stage.mkdir();files={}
            with gpu_workload_pacing.pace_cuda(pci_bus_id=cp.cuda.Device().pci_bus_id,
                    synchronize=lambda:cp.cuda.runtime.deviceSynchronize(),target=.70) as pacer:
                with pacer.block():encoder=CudaMeanEncoder(model,cp)
                try:
                    vectors=cp.empty((n,384),dtype=cp.float32)
                    for start in range(0,n,batch_size):
                        with pacer.block():
                            batch=chunks[start:start+batch_size]
                            vectors[start:start+len(batch)]=encoder.encode([row['token_ids'] for row in batch])
                    hits=gpu_rank(vectors,chunks,cp,pacer,top_k=top_k,block_size=block_size)
                    for name,rows in (('chunks.jsonl',address_rows),('ranked-passages.jsonl',hits)):
                        path=stage/name;digest=hashlib.sha256();size=0
                        with path.open('xb') as stream:
                            for row in rows:
                                raw=lexical.encoded(row)+b'\n';stream.write(raw);digest.update(raw);size+=len(raw)
                        files[name]={'bytes':size,'sha256':digest.hexdigest()}
                    path=stage/'embeddings.f32';digest=hashlib.sha256();size=0
                    with path.open('xb') as stream:
                        for start in range(0,n,batch_size):
                            with pacer.block():raw=vectors[start:start+batch_size].get().astype('<f4',copy=False).tobytes()
                            stream.write(raw);digest.update(raw);size+=len(raw)
                    files[path.name]={'bytes':size,'sha256':digest.hexdigest(),'dtype':'little_endian_float32','shape':[n,384]}
                    summary={'schema_version':1,'revision':revision,'method':METHOD,'repository':REPOSITORY,'model_revision':REVISION,
                        'model_manifest_sha256':model_sha256,'model_validation':model['validation'],
                        'method_artifacts':methods,
                        'postrun_manifest_sha256':manifest_sha256,'view_inventory_sha256':data['inventory_sha256'],
                        'selected_recordings':len(data['roster']),'observed_primary_texts':len(data['documents']),
                        'missing_primary_texts':data['missing'],'unique_inference_chunks':n,'ranked_candidates':len(hits),
                        'backend':'ctranslate2_cuda_float32_mean_pool_cupy_blocked_v1','ctranslate2_version':encoder.ct2.__version__,
                        'cupy_version':cp.__version__,'pooling':POOLING,'max_sequence_length':256,'overlap_tokens':overlap_tokens,
                        'batch_size':batch_size,'cosine_block_rows':block_size,'estimated_GPU_working_bytes':estimate,
                        'top_k':top_k,'speaker_identity_attributed':False,'event_relation_assigned':False,'scores_are_probabilities':False,
                        'inferred_labels':'unreviewed retrieval candidates only','files':files,'Source_requests':0,
                        'CUDA':'model inference, explicit mask pooling/L2, blocked cosine, pre-top-k eligibility masks/ranking',
                        'CPU':'verified IO, tokenizer offsets, alias/source indexing and output serialization'}
                finally:
                    with pacer.block():encoder.close()
            summary['utilization_pacing']=pacer.summary()
            common.atomic_write_text(stage/'manifest.json',lexical.encoded(summary).decode('utf-8')+'\n')
            os.rename(stage,target)
        return target


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','generation','model-manifest'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--manifest-sha256',required=True);parser.add_argument('--model-sha256',required=True)
    parser.add_argument('--top-k',type=int,default=5);parser.add_argument('--overlap-tokens',type=int,default=64)
    parser.add_argument('--batch-size',type=int,default=16);parser.add_argument('--cosine-block-rows',type=int,default=32)
    parser.add_argument('--gpu-working-mb',type=int,default=1000);parser.add_argument('--describe','--dry-run',action='store_true')
    args=parser.parse_args(argv)
    if args.describe:
        print(json.dumps({'execution_enabled':False,'method':METHOD,'repository':REPOSITORY,'revision':REVISION,
            'conversion_performed':False,'CUDA_tests_performed':False,'requires':'completed corpus + pinned local float32 conversion and real CUDA fixture'}))
        return 0
    print(run(args.root,args.generation,args.manifest_sha256,args.model_manifest,args.model_sha256,
        top_k=args.top_k,overlap_tokens=args.overlap_tokens,batch_size=args.batch_size,
        block_size=args.cosine_block_rows,gpu_memory_budget=args.gpu_working_mb*1_000_000))
    return 0


if __name__=='__main__':raise SystemExit(main())
