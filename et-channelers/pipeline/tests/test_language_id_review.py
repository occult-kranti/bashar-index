"""Offline fixtures only. No corpus, network, model construction or GPU."""
import ast
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import wave

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('language_review',HERE/'language_id_review.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)


class LanguageReviewTests(unittest.TestCase):
    def test_fixed_contiguous_windows_keep_pauses(self):
        vad=[[181504,300288],[302336,381696],[386304,657152],[12681472,13161472],[17625088,18080512]]
        rows=worker.interval_evidence(worker.WINDOWS,vad,24473647)
        self.assertEqual([r['vad_overlap_samples'] for r in rows],[468992,480000,455424])
        self.assertEqual(sum(b-a for a,b in worker.WINDOWS),1415424)
        self.assertEqual(rows[0]['duration_seconds'],30)
        self.assertAlmostEqual(rows[0]['vad_overlap_seconds'],29.312)

    def test_window_change_and_overlapping_vad_fail(self):
        with self.assertRaisesRegex(worker.ReviewError,'window_scope'):
            worker.interval_evidence([[181504,661505]]+worker.WINDOWS[1:],worker.WINDOWS,24473647)
        with self.assertRaisesRegex(worker.ReviewError,'vad_intervals'):
            worker.interval_evidence(worker.WINDOWS,[[181504,661504],[200000,700000]],24473647)

    def test_insufficient_speech_and_unavailable_extent_fail(self):
        with self.assertRaisesRegex(worker.ReviewError,'insufficient_window_vad'):
            worker.interval_evidence(worker.WINDOWS,[[181504,190000]],24473647)
        with self.assertRaises(worker.ReviewError):
            worker.interval_evidence(worker.WINDOWS,worker.WINDOWS,18080511)

    def test_scores_are_finite_plain_json_and_not_semantic_truth(self):
        class Scalar:
            def __float__(self):return .92
        result=worker.normalize_score(('en',Scalar(),[('en',Scalar()),('es',.06),('fr',.02)]))
        self.assertIs(type(result['probability']),float)
        self.assertIs(result['strong_window_language_evidence'],True)
        self.assertFalse(result['lexical_meaning_confirmed'])
        self.assertFalse(result['full_recording_language_confirmed'])
        json.dumps(result,allow_nan=False)
        uncertain=worker.normalize_score(('en',.6,[('en',.6),('es',.4)]))
        self.assertIs(uncertain['strong_window_language_evidence'],False)

    def test_invalid_or_inconsistent_scores_fail(self):
        for value in [('en',float('nan'),[('en',.9),('es',.1)]),('en',.9,[('en',.9),('en',.1)]),
                      ('en',.9,[('en',.8),('es',.2)]),('en',.2,[('en',.2),('es',.8)])]:
            with self.subTest(value=value),self.assertRaises(worker.ReviewError):worker.normalize_score(value)

    def test_admission_binds_all_hashes(self):
        binding={'proposal_sha256':'a'*64,'worker_sha256':'b'*64,'config_sha256':'c'*64}
        worker.require_binding({'language_review':binding.copy()},binding)
        for key in binding:
            changed=dict(binding);changed[key]='f'*64
            with self.assertRaisesRegex(worker.ReviewError,'language_review_binding'):
                worker.require_binding({'language_review':changed},binding)

    def test_safe_diagnostic_drops_exception_message(self):
        try:raise TypeError('private text or credential')
        except Exception as error:result=worker.safe_error(error,'language_id_only')
        self.assertNotIn('private text',json.dumps(result))
        self.assertEqual(result['error_class'],'TypeError')
        self.assertEqual(set(result['frames'][0]),{'module','function','line'})

    def test_only_runtime_detect_is_called(self):
        tree=ast.parse((HERE/'language_id_review.py').read_text())
        calls=[node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)]
        self.assertIn('detect',calls)
        self.assertFalse({'transcribe','translate','run_jobs','publish_result','release_input'}&set(calls))

    def test_actual_cpu_streamed_fixture_exact_samples(self):
        try:import av;import numpy as np
        except ImportError:self.skipTest('Existing optional PyAV/NumPy unavailable')
        # Generated fixture stays in RAM; no source media or model is accessed.
        samples=np.arange(44*worker.RATE,dtype=np.int32)%1000
        pcm=samples.astype('<i2').tobytes();buffer=io.BytesIO()
        with wave.open(buffer,'wb') as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(worker.RATE);wav.writeframes(pcm)
        original=av.open
        windows=[[16000,32000],[160000,176000],[660000,680000]]
        with patch.object(av,'open',side_effect=lambda _:original(io.BytesIO(buffer.getvalue()))),patch.object(worker,'WINDOWS',windows):
            arrays,proof=worker.decode_windows('synthetic-only',windows,len(samples),44,lambda:None,{})
        for audio,(a,b) in zip(arrays,windows):
            expected=samples[a:b].astype(np.float32)/32768
            np.testing.assert_array_equal(audio,expected)
        self.assertEqual(proof['written_samples'],[b-a for a,b in windows])
        self.assertEqual(proof['decoded_samples'],len(samples))
        self.assertFalse(proof['padding_applied'])

    def test_full_fixed_window_stream_has_bounded_retention(self):
        try:import numpy as np
        except ImportError:self.skipTest('Existing optional NumPy unavailable')
        total=24473647;state={}
        def frames():
            for start in range(0,total,4000):
                yield start/worker.RATE,(np.arange(start,min(start+4000,total),dtype=np.int32)%997).astype(np.float32)
        arrays,proof=worker.retain_streamed_windows(frames(),worker.WINDOWS,total,1530,lambda:None,state)
        for array,(a,b) in zip(arrays,worker.WINDOWS):
            np.testing.assert_array_equal(array,(np.arange(a,b,dtype=np.int32)%997).astype(np.float32))
        self.assertEqual(sum(x.nbytes for x in arrays),5661696)
        self.assertEqual(proof['decoded_samples'],total)
        self.assertFalse(proof['full_pcm_array_created'])
        self.assertEqual(state['decoded_samples'],total)

    def test_bad_stream_extent_clock_or_budget_holds(self):
        try:import numpy as np
        except ImportError:self.skipTest('Existing optional NumPy unavailable')
        windows=[[0,16]];values=np.ones(16,dtype=np.float32)
        cases=[([(0,values)],32,32/worker.RATE,'decode_extent_mismatch'),
               ([(0,values),(1,values)],32,32/worker.RATE,'decode_discontinuity'),
               ([(0,np.ones(33,dtype=np.float32))],32,32/worker.RATE,'decode_sample_limit')]
        for frames,total,duration,code in cases:
            with self.subTest(code=code),self.assertRaisesRegex(worker.ReviewError,code):
                worker.retain_streamed_windows(iter(frames),windows,total,duration,lambda:None,{})

    def test_failure_diagnostic_reports_call_progress_without_raw_text(self):
        state={'window_index':1,'decoded_samples':24473647,'detect_calls_started':2,'detect_calls_completed':1,
               'model_load_started':True,'model_loaded':True,'telemetry_started':True}
        result=worker.safe_error(TypeError('do not log'), 'language_id_only',state)
        self.assertEqual(result['window_index'],1)
        self.assertEqual(result['detect_calls_started'],2)
        self.assertEqual(result['detect_calls_completed'],1)
        self.assertTrue(result['model_loaded'])
        self.assertNotIn('do not log',json.dumps(result))

    def test_decode_is_before_model_construction(self):
        tree=ast.parse((HERE/'language_id_review.py').read_text())
        run=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='run')
        decode=next(node.lineno for node in ast.walk(run) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='decode_windows')
        model=next(node.lineno for node in ast.walk(run) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='Runtime')
        self.assertLess(decode,model)


if __name__=='__main__':unittest.main()
