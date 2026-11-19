"""Private creator/claimed-source lexical comparisons from a frozen post-run view inventory.

No model inference. Production arithmetic requires CuPy CUDA; CPU arithmetic is
an explicit fixture oracle only. Importing this module never imports CUDA.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile

from . import common,corpus_concordance,episode_comparison,host_capacity,keywords

METHOD='episode_tfidf_reviewed_family_centroids_cosine_v1'
SHA=re.compile(r'[0-9a-f]{64}\Z')
VIDEO=re.compile(r'[A-Za-z0-9_-]{11}\Z')
LABEL=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}\Z')


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')


def digest(raw):return hashlib.sha256(raw).hexdigest()


def _contained(root,relative):
    part=Path(relative)
    if part.is_absolute() or '..' in part.parts:raise ValueError('relative_private_artifact_required')
    path=root/part
    if path.resolve()!=path.absolute() or not path.resolve().is_relative_to(root):
        raise ValueError('linked_or_foreign_text_artifact')
    return path


def _checked(path,sha,expected_bytes=None):
    if not isinstance(sha,str) or not SHA.fullmatch(sha):raise ValueError('artifact_sha256_required')
    raw=Path(path).read_bytes()
    if digest(raw)!=sha or expected_bytes is not None and len(raw)!=expected_bytes:
        raise ValueError('frozen_artifact_changed')
    return raw


def _object(raw):
    value=json.loads(raw)
    if not isinstance(value,dict):raise ValueError('artifact_object_required')
    return value


def load_inventory(root,generation,manifest_sha256,*,assignments=None,assignments_sha256=None):
    """Revalidate the immutable producer generation; no discovery or corpus run."""
    root=Path(root).resolve();generation=Path(generation).resolve()
    if not generation.is_relative_to(root/'analysis'):
        raise ValueError('postrun_generation_under_private_analysis_required')
    manifest_raw=_checked(generation/'manifest.json',manifest_sha256);manifest=_object(manifest_raw)
    if (manifest.get('phase')!='candidate_retrieval' or not SHA.fullmatch(str(manifest.get('revision','')))
            or generation.name!=manifest['revision'] or not SHA.fullmatch(str(manifest.get('selection_sha256','')))):
        raise ValueError('frozen_completed_postrun_generation_required')
    inventory_path=generation/'view-inventory.json';raw=inventory_path.read_bytes();roster=json.loads(raw)
    if (not isinstance(roster,list) or not roster or manifest.get('files',{}).get('view-inventory.json')!=len(raw)
            or manifest.get('selected_audio')!=len(roster)):
        raise ValueError('postrun_inventory_denominator_changed')
    # The producer revision already binds the entire roster, not just its size.
    method=digest(encoded(manifest['methods']))
    expected={digest(encoded([manifest['selection_sha256'],method,roster,figures])) for figures in (False,True)}
    if manifest['revision'] not in expected:raise ValueError('postrun_inventory_revision_changed')
    frame=episode_comparison.primary_frame(roster)
    observed=sum(row.get('selected_primary') is not None for row in roster)
    if (manifest.get('eligible_primary_texts')!=observed or manifest.get('missing_primary_texts')!=len(roster)-observed
            or manifest.get('creators')!=len({row['channel_dir'] for row in roster})):
        raise ValueError('postrun_text_missingness_changed')
    inventory_sha=digest(raw);reviews={};review_pin=None
    if assignments is not None:
        path=Path(assignments).resolve()
        if not path.is_relative_to(root):raise ValueError('private_episode_review_required')
        review_raw=_checked(path,assignments_sha256);review=_object(review_raw)
        if (review.get('schema_version')!=1 or review.get('selection_sha256')!=manifest['selection_sha256']
                or review.get('view_inventory_sha256')!=inventory_sha or not isinstance(review.get('assignments'),list)):
            raise ValueError('episode_review_inventory_binding')
        review_pin={'path':path.relative_to(root).as_posix(),'bytes':len(review_raw),'sha256':digest(review_raw)}
        byid={row['video_id']:row for row in roster}
        for item in review['assignments']:
            video=item.get('video_id');row=byid.get(video)
            if (row is None or video in reviews or item.get('channel_dir')!=row['channel_dir']
                    or item.get('review_state')!='episode_specific_reviewed'
                    or item.get('scope')!='whole_recording_claimed_source'
                    or not LABEL.fullmatch(str(item.get('claimed_entity_id','')))
                    or item.get('text_version_id')!=(row.get('selected_primary') or {}).get('text_version_id')):
                raise ValueError('episode_specific_claimed_source_review_required')
            proof=item.get('evidence') or {}
            if type(proof.get('bytes')) is not int or proof['bytes']<=0:
                raise ValueError('nonempty_episode_review_evidence_required')
            evidence=_contained(root,proof['path'])
            _checked(evidence,proof.get('sha256'),proof.get('bytes'))
            reviews[video]=dict(item)
    documents=[];missing=[];seen=set()
    for row in roster:
        video=row['video_id'];channel=row['channel_dir'];selected=row.get('selected_primary')
        if (not VIDEO.fullmatch(video) or not LABEL.fullmatch(channel) or video in seen):
            raise ValueError('exact_selected_recording_identity_required')
        seen.add(video)
        if selected is None:
            missing.append({'video_id':video,'channel_dir':channel,'reason':'no_eligible_primary_English_text'})
            continue
        path=_contained(root,selected['path']);view_raw=_checked(path,selected['file_sha256']);view=_object(view_raw)
        if (view.get('video_id')!=video or view.get('channel_dir')!=channel or selected.get('video_id')!=video
                or view.get('source_kind')!=selected.get('source_kind') or view.get('text_version_id')!=selected.get('text_version_id')
                or view.get('language')!=selected.get('language') or view.get('bundle_sha256')!=selected.get('bundle_sha256')
                or view.get('speech_coverage_verified') is not False):
            raise ValueError('primary_view_provenance_changed')
        # Reuse the existing source/time/codepoint validation; no claims are inferred.
        episode_comparison.prepare_observation({'view':view,'assessed_topics':[],
            'assessment_method_sha256':digest(METHOD.encode()),'matches':[]},frame,set())
        if view.get('source_kind') in {'publisher_untimed_transcript','numbered_publisher_episode_transcript'}:
            corpus_concordance.validate_paragraph_view(view)
        counts=Counter(token for run in keywords.tokens(view['text']) for token in run if token is not None)
        audio=view.get('source_audio_sha256');edition=view.get('source_edition_id')
        source=('audio:'+audio if isinstance(audio,str) and SHA.fullmatch(audio)
                else 'edition:'+edition if isinstance(edition,str) and edition else 'video:'+video)
        unit=digest(encoded([source,view['text_sha256'],view['source_kind'],view['language'].lower()]))
        documents.append({'unit_id':unit,'video_id':video,'channel_dir':channel,'counts':counts,
            'family':frame[video]['group'],'source_kind':view['source_kind'],
            'text_version_id':view['text_version_id'],'text_sha256':view['text_sha256'],
            'view':dict(selected),'source_audio_sha256':audio,'source_edition_id':edition,
            'source_timebase':view.get('source_timebase'),'edition_receipt_sha256':view.get('edition_receipt_sha256'),
            'claimed_entity':reviews.get(video,{}).get('claimed_entity_id')})
    return {'manifest':manifest,'manifest_sha256':manifest_sha256,'inventory_sha256':inventory_sha,
        'generation':generation.relative_to(root).as_posix(),'roster':roster,'documents':documents,
        'missing':missing,'reviews':reviews,'review_pin':review_pin,
        'source_methods':{'tokenizer_sha256':digest(Path(keywords.__file__).read_bytes()),
                          'adapter_sha256':digest(Path(__file__).read_bytes())}}


def groups_for(data):
    """Exact audio/text aliases vote once; reviewed families are balanced within groups."""
    units={};groups={};selected={};assigned=set()
    for row in data['roster']:
        key='creator:'+row['channel_dir'];selected.setdefault(key,set()).add(row['video_id'])
        groups.setdefault(key,{'kind':'creator','label':row['channel_dir'],'units':set()})
        review=data['reviews'].get(row['video_id'])
        if review:
            assigned.add(row['video_id']);key='claimed_entity:'+review['claimed_entity_id']
            selected.setdefault(key,set()).add(row['video_id'])
            groups.setdefault(key,{'kind':'claimed_entity','label':review['claimed_entity_id'],'units':set()})
    for doc in data['documents']:
        unit=doc['unit_id'];old=units.get(unit)
        if old is None:
            units[unit]={'counts':doc['counts'],'source_kind':doc['source_kind'],
                'family':doc['family'] if doc['family'][0]=='confirmed' else ('unresolved',unit),'aliases':[]}
        elif old['counts']!=doc['counts'] or old['source_kind']!=doc['source_kind']:
            raise ValueError('shared_audio_text_unit_conflict')
        units[unit]['aliases'].append({k:v for k,v in doc.items() if k!='counts'})
        groups['creator:'+doc['channel_dir']]['units'].add(unit)
        if doc['claimed_entity']:
            groups['claimed_entity:'+doc['claimed_entity']]['units'].add(unit)
    for value in units.values():
        claims={alias['claimed_entity'] for alias in value['aliases'] if alias['claimed_entity']}
        families={tuple(alias['family']) for alias in value['aliases'] if alias['family'][0]=='confirmed'}
        if len(claims)>1 or len(families)>1:raise ValueError('shared_source_review_conflict')
        if families:value['family']=next(iter(families))
    order=sorted(units);unitpos={u:i for i,u in enumerate(order)};matrix_groups=[]
    for key,group in sorted(groups.items()):
        family=Counter(units[u]['family'] for u in group['units']);n=len(family)
        weights={unitpos[u]:1/(n*family[units[u]['family']]) for u in group['units']} if n else {}
        available={alias['video_id'] for u in group['units'] for alias in units[u]['aliases']
            if alias['video_id'] in selected[key]}
        matrix_groups.append({'id':key,'kind':group['kind'],'label':group['label'],'weights':weights,
            'unit_ids':sorted(group['units']),'families':sorted(family),'selected_recordings':len(selected[key]),
            'observed_recordings':len(available),'missing_primary_texts':len(selected[key]-available),
            'unique_text_units':len(group['units']),'reviewed_family_or_singleton_units':n,
            'source_kind_units':dict(Counter(units[u]['source_kind'] for u in group['units']))})
    return order,units,matrix_groups,sorted(row['video_id'] for row in data['roster'] if row['video_id'] not in assigned)


def cpu_fixture_math(counts,groups,*,fixture_only=False,top_terms=20):
    if fixture_only is not True:raise ValueError('CPU_math_is_fixture_only')
    weights,df,idf=keywords.tfidf({str(i):c for i,c in enumerate(counts)})
    vectors=[]
    for group in groups:
        values=defaultdict(float)
        for index,weight in group['weights'].items():
            for term,value in weights[str(index)].items():values[term]+=weight*value
        norm=math.sqrt(sum(v*v for v in values.values()))
        vectors.append({term:v/norm for term,v in values.items()} if norm else {})
    scores=[[sum(v*right.get(t,0.) for t,v in left.items()) if left and right else None
             for right in vectors] for left in vectors]
    top=[sorted(row.items(),key=lambda x:(-x[1],x[0]))[:top_terms] for row in vectors]
    return {'cosine':scores,'top_terms':top,'vocabulary':sorted(idf),'df':dict(df),'idf':idf,
        'backend':{'name':'python_cpu_fixture_reference','production_execution':False,
            'CPU':'fixture lexical arithmetic only','GPU':'not imported or initialized'}}


def cuda_math(counts,groups,*,block_size=32,top_terms=20,gpu_memory_budget=1_000_000_000):
    """Sparse TF-IDF/centroids and blockwise cosine; never allocate V×V or N×N."""
    if type(block_size) is not int or not 1<=block_size<=256 or type(gpu_memory_budget) is not int or gpu_memory_budget<=0:
        raise ValueError('explicit_CUDA_block_and_memory_budget_required')
    terms=sorted({t for row in counts for t in row});n=len(counts);v=len(terms);g=len(groups)
    if not terms:
        return {'cosine':[[None]*g for _ in groups],'top_terms':[[] for _ in groups],
            'vocabulary':[],'df':{},'idf':{},'backend':{'name':'cupy_cuda12x_csr_v1',
            'production_execution':False,'reason':'no_lexical_terms','GPU_initialized':False}}
    positions={t:i for i,t in enumerate(terms)};rows=[];columns=[];values=[]
    for i,row in enumerate(counts):
        for term,value in sorted(row.items()):
            if type(value) is not int or value<=0:raise ValueError('positive_token_counts_required')
            rows.append(i);columns.append(positions[term]);values.append(value)
    gi=[];di=[];gw=[]
    for i,group in enumerate(groups):
        for doc,weight in sorted(group['weights'].items()):gi.append(i);di.append(doc);gw.append(weight)
    centroid_bound=sum(min(v,sum(len(counts[d]) for d in group['weights'])) for group in groups)
    # Conservative transient estimate for CSR/COO, weighting, multiplication and one dense score block.
    estimate=128*(len(values)+centroid_bound+len(gw)+n+v+g)+8*min(block_size,g)*g
    if estimate>gpu_memory_budget:raise ValueError('CUDA_sparse_working_budget_deferred')
    # Deliberately lazy: only an explicit, completed real run reaches these imports.
    import cupy as cp
    from cupyx.scipy import sparse
    from . import gpu_workload_pacing
    free,total=cp.cuda.runtime.memGetInfo()
    if estimate>free or estimate>gpu_memory_budget:raise ValueError('CUDA_free_memory_deferred')
    with gpu_workload_pacing.pace_cuda(pci_bus_id=cp.cuda.Device().pci_bus_id,
            synchronize=lambda:cp.cuda.get_current_stream().synchronize(),target=.70) as pacer:
        with pacer.block():
            r=cp.asarray(rows,dtype=cp.int32);c=cp.asarray(columns,dtype=cp.int32)
            df=cp.bincount(c,minlength=v);idf=cp.log((1.+n)/(1.+df))+1.
            value=(1.+cp.log(cp.asarray(values,dtype=cp.float64)))*idf[c]
            norm=cp.sqrt(cp.bincount(r,weights=value*value,minlength=n));value/=cp.maximum(norm[r],1e-300)
            documents=sparse.coo_matrix((value,(r,c)),shape=(n,v)).tocsr()
        with pacer.block():
            assignment=sparse.coo_matrix((cp.asarray(gw,dtype=cp.float64),
                (cp.asarray(gi,dtype=cp.int32),cp.asarray(di,dtype=cp.int32))),shape=(g,n)).tocsr()
            centroids=(assignment@documents).tocsr()
            norms=cp.sqrt(cp.asarray(centroids.multiply(centroids).sum(axis=1)).reshape(-1))
            centroids.data/=cp.repeat(cp.maximum(norms,1e-300),cp.diff(centroids.indptr))
            nonzero=(norms>0).get().tolist()
        scores=[];top=[]
        for start in range(0,g,block_size):
            with pacer.block():
                block=(centroids[start:start+block_size]@centroids.T).toarray().get().tolist()
            for i,row in enumerate(block,start):
                scores.append([min(1.,max(0.,float(value))) if nonzero[i] and nonzero[j] else None
                    for j,value in enumerate(row)])
        for i in range(g):
            with pacer.block():
                row=centroids.getrow(i);indexes=row.indices.get().tolist();weights=row.data.get().tolist()
            top.append(sorted(((terms[j],float(value)) for j,value in zip(indexes,weights)),key=lambda x:(-x[1],x[0]))[:top_terms])
        with pacer.block():
            df_host=df.get().tolist();idf_host=idf.get().tolist()
    pacing=pacer.summary()
    return {'cosine':scores,'top_terms':top,'vocabulary':terms,
        'df':dict(zip(terms,df_host)),'idf':dict(zip(terms,idf_host)),
        'backend':{'name':'cupy_cuda12x_csr_v1','cupy_version':cp.__version__,
            'cuda_runtime_version':cp.cuda.runtime.runtimeGetVersion(),'production_execution':True,
            'estimated_GPU_working_bytes':estimate,'GPU_budget_bytes':gpu_memory_budget,'GPU_total_bytes':total,
            'cosine_block_rows':block_size,'dtype':'float64',
            'utilization_pacing':pacing,
            'GPU':'TF/DF/IDF, row norms, sparse family-weighted centroids, blocked cosine',
            'CPU':'verified input IO, tokenization, sparse indexing, top-term ordering, graph components and export'}}


def assemble(data,*,backend='cuda',fixture_only=False,threshold=.35,top_terms=20,block_size=32,gpu_memory_budget=1_000_000_000):
    if type(threshold) not in (float,int) or not 0<threshold<=1 or type(top_terms) is not int or not 1<=top_terms<=100:
        raise ValueError('explicit_lexical_parameters_required')
    order,units,groups,unassigned=groups_for(data)
    counts=[units[u]['counts'] for u in order]
    if backend=='cpu_fixture':math_result=cpu_fixture_math(counts,groups,fixture_only=fixture_only,top_terms=top_terms)
    elif backend=='cuda':math_result=cuda_math(counts,groups,block_size=block_size,top_terms=top_terms,gpu_memory_budget=gpu_memory_budget)
    else:raise ValueError('unknown_lexical_backend')
    matrix=math_result.pop('cosine');top=math_result.pop('top_terms');pairs=[];edges=[]
    parent=list(range(len(groups)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,left in enumerate(groups):
        left['top_terms']=[{'term':term,'weight':weight} for term,weight in top[i]]
        for j in range(i+1,len(groups)):
            right=groups[j];shared=set(left['unit_ids'])&set(right['unit_ids'])
            shared_family=set(map(tuple,left['families']))&set(map(tuple,right['families']))
            row={'left':left['id'],'right':right['id'],'cosine':matrix[i][j],
                'shared_text_units':len(shared),'shared_reviewed_family_or_singleton_units':len(shared_family),
                'overlap_is_not_independent':bool(shared or shared_family)}
            pairs.append(row)
            if (left['kind']==right['kind'] and not shared and not shared_family
                    and matrix[i][j] is not None and matrix[i][j]>=threshold):
                edges.append(row);parent[find(j)]=find(i)
    components=defaultdict(list)
    for i,group in enumerate(groups):
        if math_result['vocabulary'] and group['top_terms']:components[(group['kind'],find(i))].append(group['id'])
    public_groups=[{k:v for k,v in row.items() if k not in {'weights','families'}} for row in groups]
    return {'schema_version':1,'method':METHOD,'selection_sha256':data['manifest']['selection_sha256'],
        'postrun_manifest_sha256':data['manifest_sha256'],'view_inventory_sha256':data['inventory_sha256'],
        'episode_assignment_file':data['review_pin'],'source_methods':data['source_methods'],
        'selected_recordings':len(data['roster']),'observed_primary_texts':len(data['documents']),
        'missing_primary_texts':data['missing'],'unassigned_claimed_source_video_ids':unassigned,
        'unique_audio_text_units':len(units),'collapsed_exact_audio_text_aliases':len(data['documents'])-len(units),
        'documents':[{'unit_id':u,'source_kind':units[u]['source_kind'],
            'token_count':sum(units[u]['counts'].values()),'zero_lexical_terms':not bool(units[u]['counts']),
            'recording_family':units[u]['family'],'associations':units[u]['aliases']} for u in order],
        'source_kind_units':dict(Counter(units[u]['source_kind'] for u in order)),
        'groups':public_groups,'cosine_overlap':pairs,'clusters':{
            'method':'within_kind_cosine_threshold_connected_components','threshold':threshold,
            'shared_source_edges_excluded':True,'edges':edges,
            'components':sorted(components.values(),key=lambda ids:tuple(ids))},
        'speaker_identity_attributed':False,'claimed_entity_labels_are_reviewed_episode_claims':True,
        'weighting':'equal_reviewed_family_then_equal_text_unit_unresolved_units_are_singletons',
        'interpretation':'Descriptive English lexical overlap; missing text is unknown, not absence. Connected components can be transitive. Cross-kind scores may share input texts and are not independent evidence.',
        **math_result}


def run(root,generation,manifest_sha256,*,assignments=None,assignments_sha256=None,threshold=.35,
        block_size=32,gpu_memory_budget=1_000_000_000):
    """Explicit post-collection only; uses the existing exclusive GPU owner lock."""
    root=common.ensure_outside_git(root)
    from . import drive_ingest,gpu_asr
    with gpu_asr.kernel_lock(root/'sync/asr_gpu_owner.lock'):
        data=load_inventory(root,generation,manifest_sha256,assignments=assignments,assignments_sha256=assignments_sha256)
        result=assemble(data,threshold=threshold,block_size=block_size,gpu_memory_budget=gpu_memory_budget)
        raw=encoded(result)+b'\n';growth=len(raw)+64*1024
        _,occupied=drive_ingest.storage_usage(root,drive_ingest.managed_roots(root))
        future=drive_ingest.reserved_project_growth(root)
        if (occupied+future+growth>host_capacity.MAX_MANAGED_BYTES
                or shutil.disk_usage(root).free-future-growth<host_capacity.MIN_DISK_SPARE):
            raise ValueError('analysis_output_storage_deferred')
        revision=digest(raw);parent=root/'analysis/group_lexical';parent.mkdir(parents=True,exist_ok=True)
        target=parent/revision
        manifest_raw=encoded({'schema_version':1,'revision':revision,
            'method':METHOD,'analysis_sha256':digest(raw),'analysis_bytes':len(raw),'backend':result['backend'],
            'postrun_manifest_sha256':manifest_sha256,'Source_requests':0,'model_inference':False})+b'\n'
        if target.exists():
            if ((target/'analysis.json').read_bytes()!=raw or (target/'manifest.json').read_bytes()!=manifest_raw):
                raise ValueError('existing_lexical_generation_changed')
            return target
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            stage=Path(temporary)/'outputs';stage.mkdir()
            common.atomic_write_text(stage/'analysis.json',raw.decode('utf-8'))
            common.atomic_write_text(stage/'manifest.json',manifest_raw.decode('utf-8'))
            os.rename(stage,target)
        return target


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--generation',type=Path,required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--entity-assignments',type=Path);parser.add_argument('--assignments-sha256')
    parser.add_argument('--cosine-threshold',type=float,default=.35)
    parser.add_argument('--cosine-block-rows',type=int,default=32)
    parser.add_argument('--gpu-working-mb',type=int,default=1000)
    parser.add_argument('--describe','--dry-run',action='store_true')
    args=parser.parse_args(argv)
    if args.describe:
        print(json.dumps({'execution_enabled':False,'method':METHOD,'backend':'cupy_cuda12x_csr_v1',
            'GPU_initialized':False,'model_inference':False,'requires':'frozen completed postrun manifest'}))
        return 0
    print(run(args.root,args.generation,args.manifest_sha256,assignments=args.entity_assignments,
        assignments_sha256=args.assignments_sha256,threshold=args.cosine_threshold,
        block_size=args.cosine_block_rows,gpu_memory_budget=args.gpu_working_mb*1_000_000))
    return 0


if __name__=='__main__':raise SystemExit(main())
