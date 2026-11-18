"""ASR aggregate proofs, versioning and project-wide storage accounting."""
import json
from pathlib import Path
import tempfile
import unittest
from pipeline import ingestion_status as status


class ASRStatusTests(unittest.TestCase):
    def test_stop_control_distinguishes_released_gpu_from_stopping_owner(self):
        (self.root / 'asr').mkdir()
        (self.root / 'asr/STOP_ASR').write_text('user requested pause', encoding='utf-8')
        gpu = self.root / 'sync/gpu_lease.json'
        gpu.write_text(json.dumps({'state': 'released', 'pid': 'PRIVATE'}), encoding='utf-8')
        result = status.snapshot(self.root)
        self.assertEqual(result['operation']['asr_last_reported_state'], 'paused')
        self.assertNotIn('PRIVATE', json.dumps(result))
        gpu.write_text(json.dumps({'state': 'active'}), encoding='utf-8')
        self.assertEqual(status.snapshot(self.root)['operation']['asr_last_reported_state'], 'stopping')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'private'
        (self.root / 'sync').mkdir(parents=True)
        self.audio = {'video_id':'abcdefghijk','channel_dir':'example','status':'deleted',
            'path':'audio/example/Videos/abcdefghijk.webm',
            'remote':'etdrive:04 Audio/example/Videos/abcdefghijk.webm',
            'bytes':20,'drive_id':'PRIVATE SOURCE ID','md5':'a'*32,'sha256':'b'*64,
            'metadata':{'drive_id':'PRIVATE METADATA ID','md5':'c'*32,'sha256':'d'*64,
                        'remote':'etdrive:04 Audio/example/Videos/abcdefghijk.info.json'}}
        self.asr = {'video_id':'abcdefghijk','channel_dir':'example','run_id':'run-1',
            'status':'verified','artifact_kind':'asr_bundle','drive_id':'PRIVATE RESULT ID',
            'remote':'etdrive:04 Audio/example/Videos/abcdefghijk/ASR/run-1/run-1.zip',
            'bytes':10,'md5':'e'*32,'sha256':'f'*64,
            'source_audio_drive_id':'PRIVATE SOURCE ID','source_audio_sha256':'b'*64,
            'private_text':'PRIVATE TRANSCRIPT','quality_state':'unreviewed_asr'}
        (self.root/'sync/drive_ingest_manifest.jsonl').write_text(json.dumps(self.audio)+'\n')

    def write_asr(self, records):
        (self.root/'sync/asr_manifest.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))

    def test_verified_result_counts_without_exporting_text_or_identity(self):
        self.write_asr([self.asr])
        result = status.snapshot(self.root)
        self.assertEqual(result['counts']['asr_verified_videos'], 1)
        self.assertEqual(result['counts']['text_artifact_videos'], 1)
        self.assertEqual(result['counts']['text_pending_videos'], 0)
        for private in ('PRIVATE', 'abcdefghijk', 'etdrive:', 'run-1', str(self.root)):
            self.assertNotIn(private, json.dumps(result))

    def test_dangling_wrong_source_destination_or_incomplete_proof_never_counts(self):
        for mutation in ({'status':'local_complete'}, {'drive_id':''}, {'bytes':0}, {'bytes':True},
                         {'md5':'bad'}, {'sha256':'bad'}, {'source_audio_drive_id':'wrong'},
                         {'source_audio_sha256':'0'*64}, {'channel_dir':'wrong'},
                         {'remote':self.asr['remote'].replace('abcdefghijk','ZYXWVUTSRQP')},
                         {'run_id':'../escape'}, {'artifact_kind':'caption_bundle'}):
            with self.subTest(mutation=mutation):
                self.write_asr([dict(self.asr, **mutation)])
                result = status.snapshot(self.root)
                self.assertEqual(result['counts']['asr_verified_videos'], 0)
                self.assertEqual(result['counts']['text_pending_videos'], 1)

    def test_new_pending_version_keeps_old_verified_version_and_deduplicates(self):
        self.write_asr([self.asr, dict(self.asr, run_id='run-2', status='pending'), self.asr])
        self.assertEqual(status.snapshot(self.root)['counts']['asr_verified_videos'], 1)
        self.audio['sha256'] = '0'*64
        (self.root/'sync/drive_ingest_manifest.jsonl').write_text(json.dumps(self.audio)+'\n')
        self.assertEqual(status.snapshot(self.root)['counts']['asr_verified_videos'], 0)

    def test_managed_roots_include_models_and_tools_once_with_no_paths_exported(self):
        tools = Path(self.temp.name)/'tools'
        tools.mkdir()
        (tools/'model.bin').write_bytes(b'x'*100)
        (self.root/'sync/analysis_resource_plan.json').write_text(
            json.dumps({'accounting_cap_bytes':16000000000,'private':'PRIVATE'}))
        result = status.snapshot(self.root, managed_roots=(Path(self.temp.name), tools))
        self.assertEqual(result['storage']['managed_bytes'], status.tree_bytes(Path(self.temp.name)))
        self.assertEqual(result['storage']['managed_ceiling_bytes'], 16000000000)
        self.assertNotIn(str(self.temp.name), json.dumps(result))
        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_asr_runtime_report_is_typed_fresh_and_never_a_live_process_claim(self):
        target = self.root/'asr/jobs/batch_runtime_state.json'
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps({'state':'running','updated_at':'2027-01-15T08:00:00Z',
            'pid':123,'video_id':'PRIVATE','private_text':'PRIVATE'}))
        now = status.dt.datetime.fromisoformat('2027-01-15T08:01:00+00:00').timestamp()
        public = status.snapshot(self.root, now=now)
        self.assertEqual(public['operation']['asr_last_reported_state'], 'running')
        self.assertNotIn('PRIVATE', json.dumps(public))
        self.assertNotIn('pid', json.dumps(public))
        self.assertEqual(status.snapshot(self.root, now=now+601)['operation']['asr_last_reported_state'], 'unconfirmed')
        target.write_text(json.dumps({'state':'PRIVATE','updated_at':'2027-01-15T08:01:00Z'}))
        self.assertEqual(status.snapshot(self.root, now=now)['operation']['asr_last_reported_state'], 'unconfirmed')

    def test_browser_recording_counts_separately_and_deduplicates_native_source(self):
        capture_id = 'capture-' + 'a'*32
        parent = 'etdrive:04 Audio/example/Videos/abcdefghijk/Browser capture/' + capture_id
        rec = {'video_id':'abcdefghijk','channel_dir':'example','tab':'videos','capture_id':capture_id,
               'status':'verified','artifact_kind':'browser_recorded_audio','reencoded':True,
               'coverage_state':'complete_content_clock_and_decoded_duration'}
        for key, filename in (('audio','audio.webm'),('metadata','capture.info.json')):
            rec[key] = {'remote':parent+'/'+filename,'drive_id':'PRIVATE '+key,
                        'bytes':15,'md5':'1'*32,'sha256':'2'*64}
        path = self.root/'sync/browser_capture_manifest.jsonl'
        path.write_text(json.dumps(rec)+'\n')
        result = status.snapshot(self.root)
        self.assertEqual(result['counts']['verified_pairs'], 1)
        self.assertEqual(result['counts']['browser_recorded_videos'], 1)
        self.assertEqual(result['counts']['audio_archived_videos'], 1)
        self.assertNotIn('PRIVATE', json.dumps(result))
        rec['metadata']['drive_id'] = rec['audio']['drive_id']
        path.write_text(json.dumps(rec)+'\n')
        self.assertEqual(status.snapshot(self.root)['counts']['browser_recorded_videos'], 0)

    def test_browser_pending_version_keeps_prior_verified_capture(self):
        capture_id = 'capture-' + 'b'*32
        parent = 'etdrive:04 Audio/example/Shorts/ZYXWVUTSRQP/Browser capture/' + capture_id
        rec = {'video_id':'ZYXWVUTSRQP','channel_dir':'example','tab':'shorts','capture_id':capture_id,
               'status':'verified','artifact_kind':'browser_recorded_audio','reencoded':True,
               'coverage_state':'complete_content_clock_and_decoded_duration'}
        for key, filename in (('audio','audio.webm'),('metadata','capture.info.json')):
            rec[key] = {'remote':parent+'/'+filename,'drive_id':'PRIVATE '+key,
                        'bytes':15,'md5':'1'*32,'sha256':'2'*64}
        pending = dict(rec, capture_id='capture-'+'c'*32, status='pending')
        (self.root/'sync/browser_capture_manifest.jsonl').write_text(json.dumps(rec)+'\n'+json.dumps(pending)+'\n')
        result = status.snapshot(self.root)
        self.assertEqual(result['counts']['browser_recorded_videos'], 1)
        self.assertEqual(result['counts']['audio_archived_videos'], 2)
        self.assertEqual(result['counts']['text_pending_videos'], 2)


if __name__ == '__main__':
    unittest.main()
