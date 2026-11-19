"""Invented text/tensors only. No neural inference, conversion, CUDA or Source."""
from copy import deepcopy
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace as N
import unittest
from unittest.mock import patch

from pipeline import corpus_semantic_retrieval as semantic
from pipeline import corpus_group_lexical as lexical
from pipeline.tests import test_corpus_group_lexical as fixture


class Tokens:
    def encode(self,text):
        spans=[(match.start(),match.end()) for match in re.finditer(r'\S+',text)]
        return N(ids=list(range(1000,1000+len(spans))),offsets=spans)


def chunk(name,creator,*,unit=None,audio=None,span=None,family=None):
    return {'chunk_id':name,'unit_id':unit or name,'span_sha256':span or name,
        'recording_family':('confirmed',family) if family else ('unresolved',unit or name),
        'associations':[{'channel_dir':creator,'source_audio_sha256':audio}]}


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.case=fixture.GroupLexicalTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
        self.root=self.case.root

    def test_long_chapter_tail_and_unicode_offsets_survive_without_512_token_truncation(self):
        text='Étoile 🌌 '+('stars '*600)+'end'
        view={'text':text,'segments':[{'source_segment_id':'chapter-1','char_start':0,'char_end':len(text),
            'time_start':0.,'time_end':100.}]}
        windows=semantic.chunk_spans(view,Tokens())
        covered={i for row in windows for i in range(row['token_start'],row['token_end'])}
        self.assertEqual(covered,set(range(603)));self.assertEqual(windows[-1]['token_end'],603)
        self.assertTrue(all(len(row['token_ids'])<=256 and not row['truncation_applied'] for row in windows))
        for row in windows:
            self.assertEqual(row['span_sha256'],lexical.digest(text[row['char_start']:row['char_end']].encode()))
        self.assertEqual(windows[0]['char_start'],0);self.assertEqual(windows[-1]['char_end'],len(text))
        with self.assertRaisesRegex(ValueError,'256'):semantic.chunk_spans(view,Tokens(),max_sequence_length=512)

    def test_paragraph_provenance_stays_untimed(self):
        view={'text':'First paragraph. Second paragraph.','segments':[
            {'source_segment_id':'doc:p0','source_member':'word/document.xml','source_paragraph_index':0,
             'paragraph_index':0,'char_start':0,'char_end':16,'time_start':None,'time_end':None},
            {'source_segment_id':'doc:p1','source_member':'word/document.xml','source_paragraph_index':1,
             'paragraph_index':1,'char_start':17,'char_end':34,'time_start':None,'time_end':None}]}
        row=semantic.chunk_spans(view,Tokens())[0]
        self.assertEqual([s['source_paragraph_index'] for s in row['source_segments']],[0,1])
        self.assertTrue(all(s['time_start'] is None and s['time_end'] is None for s in row['source_segments']))

    def test_exact_aliases_share_inference_but_keep_separate_timing_and_view_receipts(self):
        case=self.case;case.row('aaaaaaaaaaa','creator-a','Stars and galaxies.',audio='e'*64)
        row=case.row('bbbbbbbbbbb','creator-a','Stars and galaxies.',audio='e'*64)
        path=case.views['bbbbbbbbbbb'];view=json.loads(path.read_bytes())
        view['segments'][0].update(time_start=10.,time_end=11.);raw=lexical.encoded(view);path.write_bytes(raw)
        row['selected_primary']['file_sha256']=lexical.digest(raw)
        case.freeze();data=case.load();chunks=semantic.collect_chunks(case.root,data,Tokens(),'f'*64)
        self.assertEqual(len(chunks),1);self.assertEqual(len(chunks[0]['associations']),2)
        self.assertEqual([a['source_segments'][0]['time_start'] for a in chunks[0]['associations']],[0.,10.])
        self.assertNotEqual(*[a['view']['file_sha256'] for a in chunks[0]['associations']])

    def test_mask_mean_includes_specials_excludes_padding_and_normalizes(self):
        hidden=[[[1.,0.],[3.,0.],[999.,999.]],[[0.,1.],[0.,1.],[0.,1.]]]
        self.assertEqual(semantic.cpu_fixture_pool(hidden,[2,3],fixture_only=True),[[1.,0.],[0.,1.]])
        with self.assertRaisesRegex(ValueError,'fixture_only'):semantic.cpu_fixture_pool(hidden,[2,3])
        with self.assertRaises(ValueError):semantic.cpu_fixture_pool([[[0.,0.],[0.,0.]]],[2],fixture_only=True)

    def test_cross_creator_and_source_filters_apply_before_top_k(self):
        chunks=[chunk('a','creator-a',audio='source-a',family='work-a'),
            chunk('b','creator-a'),chunk('c','creator-b'),chunk('d','creator-c',family='work-a'),
            chunk('e','creator-d',audio='source-a'),chunk('f','creator-e',span='a')]
        vectors=[[1.,0.],[1.,0.],[.8,.6],[1.,0.],[1.,0.],[1.,0.]]
        hits=semantic.cpu_fixture_rank(vectors,chunks,top_k=1,fixture_only=True)
        hit=next(row for row in hits if row['query_chunk_id']=='a')
        self.assertEqual(hit['target_chunk_id'],'c');self.assertAlmostEqual(hit['cosine'],.8)
        self.assertFalse(hit['score_is_probability']);self.assertFalse(hit['event_relation_assigned'])
        with self.assertRaisesRegex(ValueError,'fixture_only'):semantic.cpu_fixture_rank(vectors,chunks)

    def test_model_artifact_and_actual_future_CUDA_fixture_are_required_without_loading_model(self):
        directory=self.root/'analysis/models/fixture';directory.mkdir(parents=True)
        files=[]
        for name in ('model.bin','config.json','tokenizer.json'):
            raw=b'invented-not-a-real-model';(directory/name).write_bytes(raw)
            files.append({'path':name,'bytes':len(raw),'sha256':lexical.digest(raw)})
        report={'model_revision':semantic.REVISION,'device':'cuda','compute_type':'float32','pooling':semantic.POOLING,
            'dimension':384,'maximum_sequence_length':256,'finite_unit_vectors':True,'full_window_tail_covered':True,
            'mask_mean_pooling_max_abs_error':0.,'repeatability_max_cosine_error':0.,'invented_fixture_only':True}
        raw=lexical.encoded(report);(directory/'fixture.json').write_bytes(raw)
        value={'schema_version':1,'repository':semantic.REPOSITORY,'revision':semantic.REVISION,
            'conversion':'ctranslate2_transformers_float32_no_integer_quantization','source_weights_sha256':'f'*64,
            'configuration':{'architecture':'BertModel','hidden_size':384,'max_sequence_length':256,'pooling':semantic.POOLING},
            'files':files,'validation':{'cuda_fixture_verified':False,
                'fixture':{'path':'fixture.json','bytes':len(raw),'sha256':lexical.digest(raw)},
                'sentence_transformers_reference_parity_verified':False}}
        manifest=directory/'manifest.json';raw=lexical.encoded(value);manifest.write_bytes(raw)
        with self.assertRaisesRegex(ValueError,'real_CUDA_fixture'):
            semantic.load_model_manifest(self.root,manifest,lexical.digest(raw))
        value['validation']['cuda_fixture_verified']=True;raw=lexical.encoded(value);manifest.write_bytes(raw)
        model=semantic.load_model_manifest(self.root,manifest,lexical.digest(raw))
        self.assertEqual(model['configuration']['max_sequence_length'],256)
        (directory/'model.bin').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'frozen_artifact_changed'):
            semantic.load_model_manifest(self.root,manifest,lexical.digest(raw))

    def test_completed_files_are_revalidated_before_reuse_without_inference(self):
        target=self.root/'generation';target.mkdir();files={}
        for name,raw in (('chunks.jsonl',b'{}\n'),('ranked-passages.jsonl',b''),('embeddings.f32',b'\0'*1536)):
            (target/name).write_bytes(raw);files[name]={'bytes':len(raw),'sha256':lexical.digest(raw)}
        manifest={'revision':'r','method':semantic.METHOD,'postrun_manifest_sha256':'a'*64,'model_manifest_sha256':'b'*64,'files':files}
        (target/'manifest.json').write_bytes(lexical.encoded(manifest))
        self.assertEqual(semantic.verified_existing(target,'r','a'*64,'b'*64),target)
        (target/'embeddings.f32').write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'file_changed'):semantic.verified_existing(target,'r','a'*64,'b'*64)

    def test_explicit_preview_is_dormant_and_normal_CLI_calls_verified_production_path(self):
        args=['--root',str(self.root),'--generation',str(self.root/'input'),'--manifest-sha256','a'*64,
            '--model-manifest',str(self.root/'model.json'),'--model-sha256','b'*64]
        with patch.object(semantic,'run',side_effect=AssertionError('GPU must not start')):
            self.assertEqual(semantic.main(args+['--describe']),0)
        with patch.object(semantic,'run',return_value=self.root/'output') as run:
            self.assertEqual(semantic.main(args),0)
        run.assert_called_once()

    def test_inert_production_transaction_survives_pacer_exit_and_reuses_verified_cache(self):
        case=self.case;case.row('aaaaaaaaaaa','creator-a','Stars and galaxies.')
        case.row('bbbbbbbbbbb','creator-b','Oceans and water.');case.freeze()
        data=case.load();events=[]
        class Host:
            def __init__(self,rows):self.rows=rows
            def astype(self,*args,**kwargs):return self
            def tobytes(self):return struct.pack('<'+'f'*(len(self.rows)*384),*(v for row in self.rows for v in row))
        class Array:
            def __init__(self,shape):self.rows=[[0.]*shape[1] for _ in range(shape[0])]
            def __setitem__(self,key,value):self.rows[key]=value
            def __getitem__(self,key):return N(get=lambda:Host(self.rows[key]))
        class Encoder:
            ct2=N(__version__='inert-fixture-no-model')
            def __init__(self,*args):events.append('encoder')
            def encode(self,ids):events.append('invented-vectors');return [[1.]+[0.]*383 for _ in ids]
            def close(self):events.append('closed')
        class Pacer:
            def __enter__(self):self.exited=False;return self
            def __exit__(self,*args):self.exited=True
            def block(self):return nullcontext()
            def summary(self):
                if not self.exited:raise AssertionError('summary before context exit')
                return {'inert_fixture':True,'GPU_initialized':False}
        cp=N(empty=lambda shape,**kwargs:Array(shape),float32='fixture-f32',__version__='inert-fixture',
            cuda=N(Device=lambda:N(pci_bus_id='00000000:01:00.0'),
                   runtime=N(memGetInfo=lambda:(10_000_000_000,10_000_000_000),deviceSynchronize=lambda:None)))
        from pipeline import drive_ingest,gpu_asr,gpu_workload_pacing
        model={'model_root':str(self.root/'model'),'validation':{'inert_fixture':True}}
        with patch.object(semantic.lexical,'load_inventory',return_value=data), \
                patch.object(semantic,'load_model_manifest',return_value=model), \
                patch.object(semantic,'LocalTokenizer',return_value=Tokens()), \
                patch.object(semantic,'CudaMeanEncoder',Encoder),patch.object(semantic,'gpu_rank',return_value=[]), \
                patch.object(gpu_asr,'kernel_lock',return_value=nullcontext()), \
                patch.object(drive_ingest,'storage_usage',return_value=(0,0)), \
                patch.object(drive_ingest,'reserved_project_growth',return_value=0), \
                patch.object(semantic.shutil,'disk_usage',return_value=N(free=100_000_000_000)), \
                patch.object(gpu_workload_pacing,'pace_cuda',side_effect=lambda **kwargs:Pacer()), \
                patch.dict(sys.modules,{'cupy':cp}):
            target=semantic.run(self.root,case.folder,case.manifest_sha,self.root/'model.json','f'*64)
            self.assertTrue((target/'manifest.json').is_file());self.assertEqual(events.count('encoder'),1)
            self.assertEqual((target/'embeddings.f32').stat().st_size,2*384*4)
            with patch.object(semantic,'CudaMeanEncoder',side_effect=AssertionError('cache must not infer')):
                self.assertEqual(semantic.run(self.root,case.folder,case.manifest_sha,self.root/'model.json','f'*64),target)
        self.assertEqual(events[-1],'closed')
        self.assertTrue(all(path.is_file() for path in case.views.values()),'original views retained')


if __name__=='__main__':unittest.main()
