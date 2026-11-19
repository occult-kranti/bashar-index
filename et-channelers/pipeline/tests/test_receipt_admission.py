from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
from types import SimpleNamespace as N
import unittest
from unittest.mock import Mock, patch

from pipeline import drive_ingest as ingest
from pipeline import receipt_admission
from pipeline.receipt_admission import ExactOwnerReceiptGate, ReceiptSnapshotChanged
from pipeline.tests.test_shared_publisher_audio import SharedPublisherAudio


class ReceiptAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'sync').mkdir();self.remote='archive:Audio';self.lock=threading.Lock()
        self.row={'video_id':'abcdefghijk','channel_dir':'example','tab':'videos','url':'https://www.youtube.com/watch?v=abcdefghijk'}
        self.path=self.root/'sync/drive_ingest_manifest.jsonl'
        self.gate=ExactOwnerReceiptGate(self.root,self.remote,receipt_lock=self.lock)

    def native(self,row=None):
        row=row or self.row;video=row['video_id'];channel=row['channel_dir']
        remote=f'{self.remote}/{channel}/Videos/{video}'
        return {**row,'status':'deleted','path':f'audio/{channel}/Videos/{video}.webm','remote':remote+'.webm',
            'bytes':123,'md5':'a'*32,'sha256':'b'*64,'drive_id':'audio-id',
            'metadata':{'path':f'audio/{channel}/Videos/{video}.info.json','remote':remote+'.info.json',
                'bytes':77,'md5':'c'*32,'sha256':'d'*64,'drive_id':'metadata-id'}}

    def append(self,path,record):
        with path.open('a',encoding='utf-8') as stream:stream.write(json.dumps(record)+'\n')

    def test_exact_verified_native_only_and_cache_invalidation(self):
        self.assertIsNone(self.gate.verified_audio(self.row))
        self.append(self.path,self.native());proof=self.gate.verified_audio(self.row)
        self.assertEqual(proof['source_kind'],'youtube_native');self.assertEqual(proof['video_id'],self.row['video_id'])
        self.assertEqual(self.gate.journal_parses,1)
        self.gate.verified_audio(self.row);self.assertEqual(self.gate.journal_parses,1)
        for change in ({'video_id':'different00'},{'channel_dir':'other'},{'tab':'streams'}):
            self.assertIsNone(self.gate.verified_audio({**self.row,**change}))
        missing=deepcopy(self.native());missing['metadata']['drive_id']='audio-id'
        self.append(self.path,missing);self.assertIsNone(self.gate.verified_audio(self.row))

    def test_qualified_and_shared_publisher_use_real_strict_readers(self):
        fixture=Path(__file__).with_name('fixtures')/'qualified_edition_receipt.json'
        record=json.loads(fixture.read_bytes())
        remote=record['audio']['remote_proof']['remote'].removesuffix('/'+record['audio']['remote_proof']['relative_path'])
        self.append(self.root/'sync/progressive_audio_extracts_manifest.jsonl',record)
        gate=ExactOwnerReceiptGate(self.root,remote,receipt_lock=self.lock)
        row={k:record[k] for k in ('video_id','channel_dir','tab')}
        with patch.object(Path,'read_text',side_effect=AssertionError('whole journal read forbidden')):
            self.assertEqual(gate.verified_audio(row)['source_kind'],'youtube_qualified_edition')
        fake=N(remote=self.remote,video='YsSEFz__Rqg',original='O2Pf891igG0',channel='dallisa-hocking')
        anchor,alias=SharedPublisherAudio.receipts(fake)
        publisher=self.root/'sync/publisher_mirror_manifest.jsonl'
        self.append(publisher,anchor);self.append(publisher,alias)
        row={'video_id':fake.video,'channel_dir':fake.channel,'tab':'videos'}
        gate=ExactOwnerReceiptGate(self.root,self.remote,receipt_lock=self.lock,selected_ids={fake.video})
        with patch.object(Path,'read_text',side_effect=AssertionError('whole journal read forbidden')):
            self.assertEqual(gate.verified_audio(row)['source_kind'],'publisher_audio')
        self.append(self.path,self.native())
        with patch.object(gate,'_validate',side_effect=AssertionError('unrelated sibling append must not invalidate positive')):
            self.assertEqual(gate.verified_audio(row)['source_kind'],'publisher_audio')

    def test_text_companions_and_wrong_file_proofs_do_not_block_audio(self):
        rec=self.native();rec['changes_selected_audio_count']=False;self.append(self.path,rec)
        self.assertIsNone(self.gate.verified_audio(self.row))
        self.append(self.root/'sync/publisher_companion_manifest.jsonl',self.native())
        self.assertIsNone(self.gate.verified_audio(self.row))
        bad=self.native();bad['sha256']='';self.append(self.path,bad)
        self.assertIsNone(self.gate.verified_audio(self.row))

    def test_legacy_blank_tab_requires_original_exact_path_and_conflicting_tab_is_rejected(self):
        rec=self.native();rec['tab']='';self.append(self.path,rec)
        self.assertEqual(self.gate.verified_audio(self.row)['source_kind'],'youtube_native')
        rec['tab']='streams';self.append(self.path,rec)
        self.assertIsNone(self.gate.verified_audio(self.row))
        rec['tab']='';rec['remote']=rec['remote'].replace('/Videos/','/Streams/')
        self.append(self.path,rec);self.assertIsNone(self.gate.verified_audio(self.row))
        rec=self.native();rec['status']='verified';self.append(self.path,rec)
        self.assertIsNone(self.gate.verified_audio(self.row))  # existing recovery finalizes this nonterminal state

    def test_streaming_has_no_old_journal_or_line_ceiling_and_does_not_read_whole_file(self):
        self.path.write_bytes(b'placeholder')
        large=(json.dumps({'video_id':'unrelated00','note':'x'*2_100_000})+'\n').encode()
        selected=(json.dumps(self.native())+'\n').encode()
        count=33;size=count*len(large)+len(selected)
        self.assertGreater(size,64_000_000)
        original_stamp=receipt_admission._stamp;original_open=Path.open
        stamp=(1,2,size,3,4)
        class Stream:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def __iter__(self):
                for _ in range(count):yield large
                yield selected
            def read(self,*a):raise AssertionError('whole journal allocation forbidden')
        def opening(path,*args,**kwargs):
            return Stream() if path==self.path else original_open(path,*args,**kwargs)
        with patch.object(receipt_admission,'_stamp',side_effect=lambda p:stamp if p==self.path else original_stamp(p)), \
                patch.object(Path,'open',opening):
            proof=self.gate.verified_audio(self.row)
        self.assertEqual(proof['journal_bytes'],size);self.assertTrue(proof['existing_verified_audio'])

    def test_changed_index_computation_does_not_hold_owner_journal_mutex(self):
        self.append(self.path,self.native());validate=self.gate._validate
        def unlocked(row,indices):
            self.assertTrue(self.lock.acquire(blocking=False))
            self.lock.release();return validate(row,indices)
        with patch.object(self.gate,'_validate',side_effect=unlocked):
            self.assertTrue(self.gate.verified_audio(self.row)['existing_verified_audio'])
        with patch.object(self.gate,'_index',side_effect=AssertionError('unchanged cached decision must not scan')):
            self.assertTrue(self.gate.verified_audio(self.row)['existing_verified_audio'])

    def test_complete_append_uses_the_same_owner_mutex_and_persistent_malformed_holds(self):
        held=threading.Event();release=threading.Event();observed=threading.Event();results=[]
        def writer():
            with self.lock:
                with self.path.open('w',encoding='utf-8') as stream:
                    raw=json.dumps(self.native());stream.write(raw[:20]);stream.flush();held.set()
                    if not release.wait(3):raise AssertionError('writer release timed out')
                    stream.write(raw[20:]+'\n');stream.flush()
        def reader():
            results.append(self.gate.verified_audio(self.row));observed.set()
        write=threading.Thread(target=writer);write.start();self.assertTrue(held.wait(3))
        read=threading.Thread(target=reader);read.start();self.assertFalse(observed.wait(.03))
        release.set();write.join(3);read.join(3)
        self.assertFalse(write.is_alive());self.assertFalse(read.is_alive());self.assertTrue(results[0]['existing_verified_audio'])
        self.path.write_bytes(b'{"partial":')
        with self.assertRaises(ReceiptSnapshotChanged):self.gate.verified_audio(self.row)
        self.path.write_bytes(b'{bad}\n')
        with self.assertRaises(json.JSONDecodeError):self.gate.verified_audio(self.row)

    def test_complete_external_append_during_snapshot_is_resampled_without_source_retry(self):
        validate=self.gate._validate;calls=[]
        def concurrent(row,indices):
            result=validate(row,indices);calls.append(1)
            if len(calls)==1:self.append(self.path,self.native())
            return result
        with patch.object(self.gate,'_validate',side_effect=concurrent):
            proof=self.gate.verified_audio(self.row)
        self.assertTrue(proof['existing_verified_audio']);self.assertEqual(len(calls),2)

    def test_worker_rechecks_after_limiter_and_covered_sibling_does_not_stop_unrelated(self):
        gate=ExactOwnerReceiptGate(self.root,self.remote,receipt_lock=ingest._JOURNAL_LOCK)
        args=N(root=self.root,remote=self.remote,collect_metadata=True,download_only=False,receipt_gate=gate)
        stop=Mock();stop.is_set.return_value=False
        limiter=Mock()
        limiter.wait.side_effect=lambda:ingest.journal(self.path,self.native())
        with patch.object(ingest,'extract_audio') as source:
            result=ingest.ingest_one(args,self.row,Mock(),limiter,stop,Mock(),self.path,stage_only=True)
        self.assertEqual(result.status,'already_covered');source.assert_not_called();stop.set.assert_not_called()
        other={**self.row,'video_id':'unrelated00','channel_dir':'other'}
        limiter.wait.side_effect=None
        with patch.object(ingest,'extract_audio',side_effect=ingest.IngestError('no_formats','inert')) as source, \
                contextlib.redirect_stderr(io.StringIO()):
            result=ingest.ingest_one(args,other,Mock(),limiter,stop,Mock(),self.path,stage_only=True)
        source.assert_called_once();self.assertEqual(result.status,'deferred_format');stop.set.assert_not_called()

    def test_normal_public_run_reaches_gate_and_keeps_unrelated_worker(self):
        fake=N(remote=self.remote,video='YsSEFz__Rqg',original='O2Pf891igG0',channel='dallisa-hocking')
        anchor,alias=SharedPublisherAudio.receipts(fake)
        publisher=self.root/'sync/publisher_mirror_manifest.jsonl'
        self.append(publisher,anchor);self.append(publisher,alias)
        covered={'video_id':fake.video,'channel_dir':fake.channel,'tab':'videos','url':'https://www.youtube.com/watch?v='+fake.video}
        other={**self.row,'video_id':'unrelated00'}
        args=N(root=self.root,remote=self.remote,max_local_bytes=100_000_000,max_item_bytes=0,min_free_bytes=0,
            rclone='inert',rclone_config=None,download_only=False,collect_metadata=True,collect_captions=False,
            limit=0,min_interval=0,workers=2,upload_transfers=3,upload_batch_items=6,upload_batch_seconds=0,
            ready_items=16,rate_bytes=100,http_chunk_bytes=0)
        self.addCleanup(lambda:ingest._ROOT_BUDGETS.pop(self.root.resolve(),None))
        with patch.object(ingest,'Rclone',return_value=Mock()), \
                patch.object(ingest,'extract_audio',side_effect=ingest.IngestError('no_formats','inert')) as source, \
                contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            result=ingest.run(args,[covered,other])
        self.assertEqual(result,3)  # unrelated no-format is deferred, not silently lost
        self.assertEqual(source.call_count,1);self.assertEqual(source.call_args.args[1]['video_id'],other['video_id'])
        self.assertIsInstance(args.receipt_gate,ExactOwnerReceiptGate)


if __name__=='__main__':unittest.main()
