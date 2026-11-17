"""Offline generated fixtures. No corpus, decode, network, model or GPU."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import zipfile

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('partial_review',HERE/'partial_asr_review.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)


class Clock:
    def __init__(self):self.mono=0.;self.wall=1000.
    def advance(self,seconds):self.mono+=seconds;self.wall+=seconds


class PartialReviewTests(unittest.TestCase):
    def heartbeat(self,clock,validate):return w.Heartbeat(validate,10,lambda:clock.mono,lambda:clock.wall)

    def test_full_lease_reads_are_cached_and_forced_boundaries_checked(self):
        clock=Clock();reads=[]
        beat=self.heartbeat(clock,lambda:reads.append(clock.mono) or 1100)
        beat(force=True)
        for _ in range(10000):beat()
        self.assertEqual(len(reads),1)
        clock.advance(.99);beat();self.assertEqual(len(reads),1)
        clock.advance(.01);beat();self.assertEqual(len(reads),2)
        beat(force=True);self.assertEqual(len(reads),3)
        self.assertEqual(beat.counters['forced_checks'],2)

    def test_revocation_detected_at_heartbeat_or_forced_boundary(self):
        clock=Clock();state={'active':True}
        def validate():w.need(state['active'],'revoked');return 1100
        beat=self.heartbeat(clock,validate);beat();state['active']=False
        clock.advance(.9);beat()
        clock.advance(.1)
        with self.assertRaisesRegex(w.ReviewError,'revoked'):beat()
        state['active']=True;beat(force=True);state['active']=False
        with self.assertRaisesRegex(w.ReviewError,'revoked'):beat(force=True)

    def test_known_lease_expiry_is_not_delayed_until_next_read(self):
        clock=Clock();reads=[];beat=self.heartbeat(clock,lambda:reads.append(1) or 1000.25)
        beat();clock.advance(.3)
        with self.assertRaisesRegex(w.ReviewError,'cached_lease_expired'):beat()
        self.assertEqual(len(reads),1)

    def test_monotonic_expiry_survives_wallclock_rollback(self):
        clock=Clock();beat=self.heartbeat(clock,lambda:1000.25);beat()
        clock.mono=.3;clock.wall=900
        with self.assertRaisesRegex(w.ReviewError,'cached_lease_expired'):beat()

    def test_wall_deadline_and_naive_expiry_fail(self):
        clock=Clock();beat=self.heartbeat(clock,lambda:1100);beat();clock.advance(10)
        with self.assertRaisesRegex(w.ReviewError,'worker_wall_limit'):beat()
        with self.assertRaisesRegex(w.ReviewError,'lease_expiry_timezone'):w.epoch('2026-01-01T00:00:00')

    def test_source_time_and_unicode_word_offsets_preserve_gap(self):
        builder={'text':'','segments':[],'word_count':0}
        segment=SimpleNamespace(start=.1,end=.8,text=' Hi 🌍 ',words=[SimpleNamespace(start=.1,end=.4,word=' Hi',probability=.9),SimpleNamespace(start=.4,end=.8,word=' 🌍',probability=.8)])
        w.append_segment(builder,segment,0,[16000,32000])
        other=SimpleNamespace(start=.1,end=.3,text='Again.',words=[SimpleNamespace(start=.1,end=.3,word='Again.',probability=.7)])
        w.append_segment(builder,other,1,[160000,176000])
        self.assertEqual(builder['text'],'Hi 🌍\nAgain.')
        self.assertEqual(builder['segments'][0]['start'],1.1)
        self.assertEqual(builder['segments'][1]['start'],10.1)
        for row in builder['segments']:
            for item in [row]+row['words']:
                self.assertEqual(builder['text'][item['char_start']:item['char_end']],item['text'])
        self.assertEqual(builder['segments'][0]['words'][1]['char_start'],3)

    def test_timing_estimate_clipping_is_explicit_and_outliers_hold(self):
        builder={'text':'','segments':[],'word_count':0}
        segment=SimpleNamespace(start=.9,end=1.02,text='word',words=[SimpleNamespace(start=.9,end=1.02,word='word',probability=.8)])
        w.append_segment(builder,segment,0,[16000,32000])
        self.assertTrue(builder['segments'][0]['timestamp_clipped'])
        self.assertEqual(builder['segments'][0]['end'],2.)
        self.assertEqual(builder['segments'][0]['model_relative_end'],1.02)
        segment.end=2
        with self.assertRaisesRegex(w.ReviewError,'segment_time'):w.append_segment(builder,segment,0,[16000,32000])

    def test_unprocessed_inventory_covers_complement_without_claiming_speech(self):
        windows=[[181504,661504],[12681472,13161472],[17625088,18080512]];total=24473647
        gaps=w.complement(windows,total)
        self.assertEqual(sum(b-a for a,b in gaps)+sum(b-a for a,b in windows),total)
        self.assertEqual(gaps[0],[0,181504]);self.assertEqual(gaps[-1],[18080512,total])
        with self.assertRaises(w.ReviewError):w.complement([[0,10],[9,12]],15)

    def members(self):
        review={'artifact_kind':'partial_asr_review','full_recording_transcript':False,'changes_collection_completion':False,
                'processed_source_samples':[[16000,32000]],'decoded_source_samples':48000,'unprocessed_source_samples':[[0,16000],[32000,48000]]}
        provenance={'profile':w.PROFILE,'quality_state':'unreviewed_partial_asr','metadata_hold_overridden':False,'full_asr_promoted':False,'cpu_asr_fallback':False,
                    'english_view':{'text_kind':'original_english_alias','same_as':'original','language':'en','translation_performed':False}}
        segments={'text_kind':'partial_original_asr','language':'en','segments':[{'window_index':0,'start':1.1,'end':1.5,'text':'test','char_start':0,'char_end':4,'words':[]}]}
        return {'review.json':w.encoded(review),'provenance.json':w.encoded(provenance),'original/segments.json':w.encoded(segments),'original/transcript.txt':b'test','telemetry.json':b'{}'}

    def write_bundle(self,path,members):
        entries=dict(members);entries['artifact_manifest.json']=w.encoded({name:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in entries.items()})
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as bundle:
            for name,raw in entries.items():bundle.writestr(name,raw)

    def test_artifact_is_distinct_partial_and_rejects_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.zip';members=self.members();self.write_bundle(path,members)
            result=w.verify_bundle(path);self.assertEqual(result['text'],'test')
            provenance=json.loads(members['provenance.json']);provenance['full_asr_promoted']=True
            members['provenance.json']=w.encoded(provenance);self.write_bundle(path,members)
            with self.assertRaisesRegex(w.ReviewError,'partial_provenance'):w.verify_bundle(path)

    def test_bundle_member_offsets_and_output_bounds_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.zip';members=self.members();members['original/transcript.txt']=b'wrong';self.write_bundle(path,members)
            with self.assertRaisesRegex(w.ReviewError,'segment_offset'):w.verify_bundle(path)
            members=self.members();members['unexpected.txt']=b'extra';self.write_bundle(path,members)
            with self.assertRaisesRegex(w.ReviewError,'bundle_members'):w.verify_bundle(path)
        builder={'text':'','segments':[],'word_count':0}
        segment=SimpleNamespace(start=0,end=1,text='toolong',words=[])
        with patch.dict(w.POLICY,{'max_text_characters':3}),self.assertRaisesRegex(w.ReviewError,'text_limit'):
            w.append_segment(builder,segment,0,[0,16000])

    def test_no_translation_or_normal_asr_manifest_path(self):
        source=(HERE/'partial_asr_review.py').read_text();tree=ast.parse(source)
        calls=[node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)]
        self.assertIn('transcribe',calls);self.assertNotIn('translate',calls);self.assertNotIn('detect',calls)
        self.assertNotIn("sync/asr_manifest.jsonl",source)
        self.assertIn('sync/partial_asr_review_manifest.jsonl',source)
        self.assertFalse(w.CONFIG['vad_filter'])

    def test_safe_error_has_counters_but_no_exception_text(self):
        args=SimpleNamespace(phase='partial_transcribe',progress={'transcribe_calls_started':1,'transcribe_calls_completed':0})
        result=w.safe_error(ValueError('private transcript'),args)
        self.assertNotIn('private transcript',json.dumps(result))
        self.assertEqual(result['progress']['transcribe_calls_completed'],0)


if __name__=='__main__':unittest.main()
