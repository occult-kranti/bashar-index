"""Small offline adapter tests; no corpus/model/network/GPU."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reviewed_full_asr',HERE/'reviewed_metadata_asr.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
PIPELINE=HERE
sys.path.insert(0,str(PIPELINE))
import gpu_asr as base
import gpu_asr_multilingual as multi


class Audio:
    def __init__(self,size):self.size=size
    def __len__(self):return self.size


class Runtime:
    def __init__(self,window_lengths):self.lengths=window_lengths;self.model=self;self.configs=[]
    def windows(self,path,duration):
        total=0
        for length in self.lengths:
            yield total/16000,Audio(length);total+=length
    def transcribe(self,audio,**config):
        self.configs.append(config)
        word=SimpleNamespace(start=.1,end=.4,probability=.9,word=' Example')
        segment=SimpleNamespace(start=.1,end=.4,text=' Example',words=[word],avg_logprob=-.1,no_speech_prob=.02,compression_ratio=1.)
        return iter([segment]),SimpleNamespace(duration_after_vad=len(audio)/16000)


class ReviewedFullTests(unittest.TestCase):
    def proposal(self):
        return {'source_job':{'audio_proof':{'sha256':'a'*64},'metadata_proof':{'sha256':'b'*64},'metadata_flags':{'claimed_light_language':True},'hold_sha256':'c'*64},
                'windows':[{'source_samples':[0,480000]},{'source_samples':[960000,1440000]},{'source_samples':[1600000,1800000]}]}

    def test_resolution_preserves_flag_hold_and_machine_review_scope(self):
        result=w.assessment_for(self.proposal())
        self.assertTrue(result['original_metadata_flags']['claimed_light_language'])
        self.assertTrue(result['original_hold_preserved'])
        self.assertEqual(result['reviewer_kind'],'root_agent')
        for key in ['human_reviewed','every_interval_english_confirmed','every_interval_lexical_confirmed','source_metadata_mutated','accuracy_confirmed']:
            self.assertIs(result[key],False)
        self.assertEqual(result['partial_result_sha256'],w.PARTIAL_RESULT_SHA)
        self.assertEqual(result['lid_result_sha256'],w.LID_RESULT_SHA)

    def test_assessment_hash_changes_with_source_or_hold(self):
        proposal=self.proposal();before=w.digest(w.assessment_for(proposal))
        proposal['source_job']['hold_sha256']='d'*64
        self.assertNotEqual(before,w.digest(w.assessment_for(proposal)))

    def task(self,lengths,expected):
        runtime=Runtime(lengths);calls=[];progress={'decoded_samples':0,'window_index':None,'transcribe_calls_started':0,'transcribe_calls_completed':0}
        timings={'decode_seconds':0.,'inference_seconds':0.}
        task=w.tracked_task(runtime,multi,lambda force=False:calls.append(force),progress,timings,expected)
        return runtime,task,progress,timings,calls

    def test_existing_collector_handles_full_extent_and_source_time(self):
        runtime,task,progress,timings,calls=self.task([480000,20000],500000)
        segments,text,_=base.collect_segments(task,'fixture',31.25,lambda:None)
        self.assertEqual(segments['duration_seconds'],31.25)
        self.assertEqual(segments['segments'][1]['start'],30.1)
        self.assertEqual(progress['transcribe_calls_completed'],2)
        self.assertTrue(all(x==w.CONFIG for x in runtime.configs))
        self.assertTrue(any(calls));self.assertGreaterEqual(timings['inference_seconds'],0)
        self.assertIn('Example',text)

    def test_wrong_or_extra_sample_extent_stops_before_sealing(self):
        for lengths,expected in [([10000],11000),([10001],10000)]:
            runtime,task,progress,_,_=self.task(lengths,expected)
            with self.subTest(lengths=lengths),self.assertRaises(w.ReviewError):
                base.collect_segments(task,'fixture',expected/16000,lambda:None)

    def test_call_bound_rejects_extra_api_work(self):
        runtime,task,progress,_,_=self.task([10000],10000)
        progress['transcribe_calls_started']=w.POLICY['max_transcribe_calls']
        with self.assertRaisesRegex(w.ReviewError,'call_limit'):task.transcribe(Audio(10000))
        self.assertEqual(runtime.configs,[])

    def test_existing_pair_writer_verifier_preserves_english_alias_and_review(self):
        runtime,task,_,_,_=self.task([16000],16000)
        segments,text,_=base.collect_segments(task,'fixture',1,lambda:None)
        segments.update(language='en',character_offset_unit='unicode_code_points',text_kind='original_asr')
        source={'drive_id':'fixture-audio','sha256':'a'*64};metadata={'drive_id':'fixture-metadata','sha256':'b'*64};model={'model_sha256':'c'*64}
        identity={'output_contract':multi.CONTRACT,'model':model,'source_audio':source,'source_metadata':metadata,'proposal_sha256':'d'*64,
                  'worker_sha256':'e'*64,'environment_lock_sha256':'f'*64,'configs':{'original':w.CONFIG}}
        run_id='asr-'+base.fingerprint(identity)[:24]
        provenance={**identity,'run_id':run_id,'identity':identity,'source_lease_id':'fixture-lease','compute':{'cpu_asr_fallback':False},
                    'job_id':'fixture-job','source_video_id':'abcdefghijk','metrics':{'audio_seconds':1},
                    'quality':{'accuracy_claimed':False,'speech_coverage_validated':False,'human_reviewed':False},
                    'reviewed_metadata_resolution':w.assessment_for(self.proposal()),'original_metadata_hold_preserved':True}
        admission={'video_id':'abcdefghijk','job_id':'fixture-job','source_lease_id':'fixture-lease','job':{'audio':source,'metadata':metadata}}
        with tempfile.TemporaryDirectory() as directory:
            settings=SimpleNamespace(root=Path(directory),output_root=Path(directory)/'asr/results')
            with patch.object(base,'inventory',return_value={}):
                receipt=multi.write_pair(settings,admission,run_id,{'original':(segments,text,w.CONFIG)},{},provenance)
            proof=multi.verify_pair(receipt['bundle']['path'])
            self.assertEqual(proof['provenance']['text_variants']['english']['text_kind'],'original_english_alias')
            self.assertFalse(proof['provenance']['quality']['human_reviewed'])
            self.assertTrue(proof['provenance']['original_metadata_hold_preserved'])
            self.assertFalse((settings.root/'sync/asr_manifest.jsonl').exists())


if __name__=='__main__':unittest.main()
