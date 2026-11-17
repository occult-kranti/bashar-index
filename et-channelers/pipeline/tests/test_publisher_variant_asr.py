"""Offline publisher-edition admission/publication tests. No media or GPU."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('publisher_variant_asr',HERE/'publisher_variant_asr.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
PIPELINE=HERE
sys.path.insert(0,str(PIPELINE))
import gpu_asr as base
import gpu_asr_multilingual as multi


class Audio:
    def __init__(self,length):self.length=length
    def __len__(self):return self.length


class Runtime:
    def __init__(self,duration):self.total=round(duration*16000);self.model=self;self.calls=0
    def windows(self,path,duration):
        for start in range(0,self.total,480000):yield start/16000,Audio(min(480000,self.total-start))
    def transcribe(self,audio,**config):
        self.calls+=1
        word=SimpleNamespace(start=0.,end=.1,word=' Test',probability=.9)
        segment=SimpleNamespace(start=0.,end=.1,text=' Test',words=[word],avg_logprob=-.1,no_speech_prob=.01,compression_ratio=1.)
        return iter([segment]),SimpleNamespace(duration_after_vad=len(audio)/16000)


class VariantTests(unittest.TestCase):
    def source(self):
        parent='remote:archive/PublisherVariants/'+'a'*64
        audio={'remote':parent+'/audio.mp3','drive_id':'audio-id','bytes':10,'md5':'b'*32,'sha256':'a'*64}
        metadata={'remote':parent+'/provenance.json','drive_id':'metadata-id','bytes':20,'md5':'c'*32,'sha256':'d'*64}
        archive={'audio':audio,'provenance':metadata}
        source={'episode_guid':'publisher-episode','source_audio_url':'https://example.test/audio.mp3',
                'publisher_feed_language':'en-us','language_evidence_scope':'publisher RSS channel declaration; not independently detected per-episode speech language'}
        return archive,source

    def test_inline_publisher_language_is_not_native_language(self):
        archive,source=self.source();result=w.publisher_language(source,archive)
        self.assertEqual(result['code'],'en-us')
        self.assertEqual(result['scope'],'publisher_rss_channel_declaration')
        self.assertFalse(result['native_youtube_language_asserted'])
        self.assertFalse(result['episode_language_independently_verified'])

    def test_missing_or_nonenglish_declaration_stays_pending(self):
        archive,source=self.source();source.pop('publisher_feed_language')
        self.assertIsNone(w.publisher_language(source,archive))
        source['publisher_feed_language']='ja'
        self.assertIsNone(w.publisher_language(source,archive))

    def evidence(self,archive,source):
        return {'artifact_kind':'publisher_feed_language_evidence','scope':'publisherRSSchannel','source_audio_proof':archive['audio'],
                'unchanged_provenance_proof':archive['provenance'],'episode_guid':source['episode_guid'],'source_audio_url':source['source_audio_url'],
                'declared_language':'en','native_youtube_language_asserted':False,'episode_spoken_language_verified':False}

    def test_external_evidence_binds_unchanged_variant_and_episode(self):
        archive,source=self.source();evidence=self.evidence(archive,source)
        result=w.publisher_language(source,archive,evidence,'e'*64)
        self.assertEqual(result['basis'],'separate_publisher_feed_language_evidence')
        evidence['episode_guid']='other'
        with self.assertRaisesRegex(w.VariantError,'publisher_language_episode'):w.publisher_language(source,archive,evidence,'e'*64)

    def test_external_evidence_cannot_relabel_native_source_or_changed_bytes(self):
        archive,source=self.source();evidence=self.evidence(archive,source);evidence['native_youtube_language_asserted']=True
        with self.assertRaisesRegex(w.VariantError,'publisher_language_claim'):w.publisher_language(source,archive,evidence,'e'*64)
        evidence=self.evidence(archive,source);evidence['source_audio_proof']={**archive['audio'],'sha256':'f'*64}
        with self.assertRaisesRegex(w.VariantError,'publisher_language_source'):w.publisher_language(source,archive,evidence,'e'*64)

    def task(self,duration):
        runtime=Runtime(duration);progress={'decoded_samples':0,'transcribe_calls_started':0,'transcribe_calls_completed':0}
        timing={'decode_seconds':0.,'inference_seconds':0.}
        return runtime,w.task_runtime(runtime,multi,lambda force=False:None,progress,timing,duration),progress

    def test_long_variant_is_processed_without_duration_exclusion(self):
        duration=7935.722676;runtime,task,progress=self.task(duration)
        segments,text,_=base.collect_segments(task,'fixture',duration,lambda:None)
        self.assertEqual(progress['decoded_samples'],round(duration*16000))
        self.assertEqual(progress['transcribe_calls_completed'],265)
        self.assertEqual(runtime.calls,265)
        self.assertAlmostEqual(segments['duration_seconds'],duration,places=4)

    def make_receipt(self,root):
        archive,source=self.source();language=w.publisher_language(source,archive)
        variant={'variant_id':archive['audio']['sha256'],'language':language,'association':{'edition_human_verified':False,'direct_watch_link_present':False}}
        model={'model_sha256':'e'*64};identity={'source_variant':variant,'source_audio':archive['audio'],'source_metadata':archive['provenance'],'model':model,'config':w.CONFIG,
                                              'worker_sha256':'1'*64,'proposal_sha256':'2'*64,'environment_lock_sha256':'3'*64,'variant_asr':{}}
        run_id='asr-'+base.fingerprint(identity)[:24];source_id='publisher-'+variant['variant_id']
        runtime,task,_=self.task(1);segments,text,_=base.collect_segments(task,'fixture',1,lambda:None)
        provenance={**identity,'run_id':run_id,'job_id':'fixture-job','source_video_id':source_id,'source_lease_id':'fixture-lease','source_audio':archive['audio'],
                    'source_metadata':archive['provenance'],'source_kind':'publisher_audio_variant','variant_id':variant['variant_id'],'source_variant':variant,
                    'language_evidence':language,'native_youtube_bytes':False,'changes_native_asr_count':False,'channel_dir':'publisher-fixture',
                    'associated_youtube_id':'abcdefghijk','identity':identity,'model':model,'config':w.CONFIG,'compute':{'cpu_asr_fallback':False},
                    'metrics':{'audio_seconds':1,'decoded_samples':16000},'quality':{'accuracy_claimed':False,'human_reviewed':False}}
        settings=SimpleNamespace(root=root,output_root=root/'asr/results/publisher-variants')
        admission={'video_id':source_id,'job_id':'fixture-job','source_lease_id':'fixture-lease','job':{'audio':archive['audio'],'metadata':archive['provenance']}}
        with patch.object(base,'inventory',return_value={}):receipt=base.write_bundle(settings,admission,run_id,segments,text,{},provenance)
        receipt.update(artifact_kind='publisher_variant_asr',source_kind='publisher_audio_variant',variant_id=variant['variant_id'],native_youtube_bytes=False,changes_native_asr_count=False)
        receipt_path=Path(receipt['bundle']['path']).parent/'receipt.json';base.atomic_json(receipt_path,receipt)
        (root/'sync').mkdir(exist_ok=True)
        return receipt,receipt_path

    def test_existing_writer_preserves_separate_variant_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt,path=self.make_receipt(Path(directory));proof=w.verify_variant(base,receipt)
            self.assertTrue(proof['provenance']['source_video_id'].startswith('publisher-'))
            self.assertFalse(proof['provenance']['source_variant']['association']['edition_human_verified'])
            receipt['native_youtube_bytes']=True
            with self.assertRaisesRegex(w.VariantError,'variant_receipt_type'):w.verify_variant(base,receipt)

    def test_publication_writes_only_variant_journal_and_variant_remote(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);receipt,path=self.make_receipt(root);copies=[]
            drive=SimpleNamespace(copy=lambda local,remote:copies.append(remote),stat=lambda remote:{'ID':'new-proof','Size':receipt['bundle']['bytes'],'Hashes':{'MD5':receipt['bundle']['md5']}})
            record=w.publish_result(path,drive,PIPELINE)
            self.assertTrue((root/'sync/publisher_variant_asr_manifest.jsonl').exists())
            self.assertFalse((root/'sync/asr_manifest.jsonl').exists())
            self.assertFalse(record['changes_native_asr_count'])
            self.assertEqual(copies,[receipt['source_audio']['remote'].rpartition('/')[0]+'/ASR/'+receipt['run_id']+'/'+receipt['run_id']+'.zip'])

    def test_failed_drive_hash_cannot_publish_or_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);receipt,path=self.make_receipt(root)
            drive=SimpleNamespace(copy=lambda *args:None,stat=lambda remote:{'ID':'new-proof','Size':receipt['bundle']['bytes'],'Hashes':{'md5':'0'*32}})
            with self.assertRaisesRegex(w.VariantError,'variant_drive_proof'):w.publish_result(path,drive,PIPELINE)
            self.assertFalse((root/'sync/publisher_variant_asr_manifest.jsonl').exists())
            self.assertTrue(Path(receipt['bundle']['path']).exists())

    def test_mutated_receipt_and_provenance_cannot_disagree_with_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt,path=self.make_receipt(Path(directory));verified=base.verify_bundle(receipt['bundle']['path'])
            original=verified['provenance']['source_audio'];changed={**original,'drive_id':'different-object'}
            receipt['source_audio']=changed;verified['provenance']['source_audio']=changed
            with patch.object(base,'verify_bundle',return_value=verified),self.assertRaisesRegex(w.VariantError,'variant_identity_proof'):
                w.verify_variant(base,receipt)


if __name__=='__main__':unittest.main()
