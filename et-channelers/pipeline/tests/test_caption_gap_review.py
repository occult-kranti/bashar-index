"""Pure offline gap geometry/provenance tests; no GPU or optional imports."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import importlib.util
import inspect
import subprocess
import sys
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import caption_gap_review as g


class GapTests(unittest.TestCase):
    def test_published_worker_matches_executed_v3_bytes(self):
        self.assertEqual(hashlib.sha256(Path(g.__file__).read_bytes()).hexdigest(),
            '04b3cd6e86abd2b5df0f9ea6914eb2c0565b5fcee11633385d51498d5f0197ca')

    def test_union_overlap_does_not_double_count_and_preserves_true_gaps(self):
        union=g.merge([[0,1000],[500,2000],[2100,2200]])
        self.assertEqual(union,[[0,2000],[2100,2200]])
        self.assertEqual(g.complement(union,3000),[[2000,2100],[2200,3000]])

    def test_vad_in_context_does_not_authorize_asr_inside_silent_gap(self):
        speech,uncued=g.speech_regions([list(range(64000))],[[0,64000]],[[2000,3000]],
            lambda _: [{'start':0,'end':16000}],lambda:None)
        self.assertEqual(speech,[[0,16000]])
        self.assertEqual(uncued,[])
        self.assertEqual(g.asr_ranges(uncued,64000),[])

    def test_vad_time_maps_to_original_source_then_intersects_gap(self):
        speech,uncued=g.speech_regions([list(range(64000))],[[160000,224000]],[[12000,13000]],
            lambda _: [{'start':16000,'end':56000}],lambda:None)
        self.assertEqual(speech,[[176000,216000]])
        self.assertEqual(uncued,[[192000,208000]])
        self.assertEqual(g.asr_ranges(uncued,300000),[{'core':[192000,208000],'decode':[160000,240000]}])

    def test_long_speech_gap_split_has_unique_cores_with_bounded_context(self):
        parts=g.asr_ranges([[100000,100000+31*16000]],1000000)
        self.assertEqual(len(parts),2)
        self.assertEqual(parts[0]['core'][1],parts[1]['core'][0])
        self.assertTrue(all(x['decode'][1]-x['decode'][0]<=28*16000 for x in parts))

    def test_bad_vad_samples_or_scope_are_rejected(self):
        with self.assertRaisesRegex(g.GapError,'vad_time'):
            g.speech_regions([[1,2]],[[0,2]],[[0,1]],lambda _:[{'start':0,'end':3}],lambda:None)
        with self.assertRaisesRegex(g.GapError,'asr_scope_limit'):
            g.asr_ranges([[0,901*16000]],1000*16000)

    def test_cached_proof_mismatch_fails_before_decode(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'input';path.write_bytes(b'actual')
            with self.assertRaisesRegex(g.GapError,'cached_input_hash'):
                g.proof_file(path,{'bytes':6,'sha256':'0'*64,'remote':'archive:x','drive_id':'id'})

    def test_changed_plan_or_worker_cannot_reuse_source_or_gpu_lease(self):
        binding={'plan_sha256':'1'*64,'worker_sha256':'2'*64,'proposal_sha256':'3'*64}
        g.require_binding({'gap_review':dict(binding)},binding,'gpu_gap_binding')
        for field in binding:
            changed=dict(binding);changed[field]='0'*64
            with self.assertRaisesRegex(g.GapError,'source_gap_binding'):
                g.require_binding({'gap_review':changed},binding,'source_gap_binding')

    def test_module_import_is_inert_and_cpu_asr_not_configurable(self):
        import sys,subprocess
        subprocess.run([sys.executable,'-I','-c',"import sys; sys.path.insert(0,sys.argv[1]); import caption_gap_review; assert 'faster_whisper' not in sys.modules; assert 'ctranslate2' not in sys.modules",str(Path(g.__file__).resolve().parent)],check=True)
        self.assertFalse(g.CONFIG['cpu_asr_fallback'])

    def test_safe_diagnostic_never_exports_error_message_source_line_or_locals(self):
        secret='https://signed.invalid/token?private=value'
        try:
            raise TypeError(secret)
        except TypeError as error:
            value=g.safe_diagnostic(error,'serialize_result',{'cuda_model_constructed':True,'telemetry_started':True,'secret':secret})
        raw=json.dumps(value)
        self.assertNotIn(secret,raw)
        self.assertNotIn('private=value',raw)
        self.assertEqual(value['phase'],'serialize_result')
        self.assertEqual(value['exception_class'],'TypeError')
        self.assertEqual(set(value['frames'][-1]),{'module','function','line'})
        self.assertLessEqual(len(value['frames']),12)
        self.assertTrue(value['runtime']['cuda_model_constructed'])
        self.assertTrue(value['runtime']['telemetry_started'])
        self.assertNotIn('secret',value['runtime'])

    def test_no_speech_bundle_retains_unreviewed_no_completion_semantics(self):
        with tempfile.TemporaryDirectory() as temp:
            members={'gap_review.json':g.encoded({'status':'no_vad_speech_detected_in_uncued_intervals','plan':{'duration_ms':1000},'decode':{'available_analysis_end_sample':16000},'uncued_speech_source_samples':[]}),
                     'segments.json':g.encoded({'selected_words':[]}), 'transcript.txt':b'',
                     'telemetry.json':g.encoded({'asr_model_loaded':False}),
                     'provenance.json':g.encoded({'quality_state':'unreviewed_gap_asr','speech_coverage_validated':False,'cpu_asr_fallback':False})}
            members['artifact_manifest.json']=g.encoded({n:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for n,v in members.items()})
            path=Path(temp)/'output.zip'
            with zipfile.ZipFile(path,'w') as archive:
                for n,v in members.items():archive.writestr(n,v)
            self.assertFalse(g.verify_result(path)['speech_coverage_validated'])

    def test_half_second_metadata_tail_is_clipped_never_padded(self):
        sentinel=object()
        array=[1]*24000+[sentinel]*8000
        arrays,windows,evidence=g.available_windows([array],[[128000,160000]],[24000],152000,160000)
        self.assertEqual(windows,[[128000,152000]])
        self.assertEqual(len(arrays[0]),24000)
        self.assertTrue(all(value==1 for value in arrays[0]))
        self.assertEqual(evidence['unreviewed_declared_tail_source_samples'],[[152000,160000]])
        self.assertEqual(evidence['missing_declared_tail_seconds'],0.5)
        self.assertFalse(evidence['tail_padded'])
        speech,uncued=g.speech_regions(arrays,windows,[[8500,10000]],lambda a:[{'start':0,'end':len(a)}],lambda:None)
        ranges=g.asr_ranges(uncued,evidence['available_analysis_end_sample'])
        self.assertTrue(all(x['decode'][1]<=152000 for x in ranges))
        self.assertEqual(uncued,[[136000,152000]])

    def test_eof_policy_does_not_hide_missing_internal_decode_or_large_delta(self):
        with self.assertRaisesRegex(g.GapError,'gap_decode_incomplete'):
            g.available_windows([[0]*32000],[[0,32000]],[31999],40000,40000)
        with self.assertRaisesRegex(g.GapError,'decoded_duration_mismatch'):
            g.available_windows([[0]*32000],[[0,32000]],[32000],32000,64001)

    def test_window_entirely_beyond_eof_is_retained_only_as_unreviewed_tail(self):
        arrays,windows,evidence=g.available_windows([[99]*8000],[[152000,160000]],[0],150000,160000)
        self.assertEqual(arrays,[])
        self.assertEqual(windows,[])
        self.assertEqual(evidence['unreviewed_declared_tail_source_samples'],[[150000,160000]])

    def test_model_numeric_values_normalize_to_json_safe_builtins(self):
        class Numeric:
            def __init__(self,value):self.value=value
            def __float__(self):return self.value
        word=SimpleNamespace(start=Numeric(.2),end=Numeric(.8),word=' synthetic',probability=Numeric(.9))
        value=g.word_evidence(word,[0,g.RATE],[0,g.RATE])
        self.assertTrue(all(type(value[k]) is float for k in ['start','end','probability']))
        self.assertTrue(all(type(value[k]) is bool for k in ['midpoint_inside_uncued_vad_speech','crosses_core_boundary']))
        self.assertEqual(json.loads(g.encoded(value)),value)

    def test_nonfinite_model_numeric_value_fails_closed(self):
        word=SimpleNamespace(start=.2,end=.8,word=' synthetic',probability=float('nan'))
        with self.assertRaisesRegex(g.GapError,'word_timing'):
            g.word_evidence(word,[0,g.RATE],[0,g.RATE])


class OptionalInstalledApiTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('numpy'),'optional NumPy is not installed; no inference test required')
    def test_numpy_flags_reproduce_old_json_error_and_normalize(self):
        import numpy as np
        word=SimpleNamespace(start=np.float64(.2),end=np.float64(.8),word=' synthetic',probability=np.float64(.9))
        old_flag=0<=(word.start+word.end)*g.RATE/2<g.RATE
        with self.assertRaises(TypeError):json.dumps({'selected':old_flag})
        value=g.word_evidence(word,[0,g.RATE],[0,g.RATE])
        self.assertEqual(type(value['midpoint_inside_uncued_vad_speech']),bool)
        self.assertEqual(type(value['crosses_core_boundary']),bool)
        self.assertEqual(json.loads(g.encoded(value)),value)

    @unittest.skipUnless(importlib.util.find_spec('numpy') and importlib.util.find_spec('faster_whisper'),
        'optional installed faster-whisper/NumPy API unavailable; no model is loaded')
    def test_installed_signatures_accept_configuration_without_model_construction(self):
        import numpy as np
        from faster_whisper.transcribe import WhisperModel
        from faster_whisper.vad import get_speech_timestamps,VadOptions
        config={'language':'en','task':'transcribe','beam_size':5,'best_of':1,'temperature':0,
                'condition_on_previous_text':False,'vad_filter':False,'word_timestamps':True}
        inspect.signature(WhisperModel.transcribe).bind(None,np.zeros(16,dtype=np.float32),**config)
        options=VadOptions(threshold=g.CONFIG['vad_threshold'],min_speech_duration_ms=g.CONFIG['vad_min_speech_ms'],
            min_silence_duration_ms=g.CONFIG['vad_min_silence_ms'],speech_pad_ms=0)
        inspect.signature(get_speech_timestamps).bind(np.zeros(16,dtype=np.float32),vad_options=options,sampling_rate=g.RATE)


if __name__=='__main__':unittest.main()
