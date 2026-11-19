"""Current channel inventory: receipt boundaries, source joins and safe export."""
import csv
import datetime as dt
import io
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch
from pipeline import collection_coverage as coverage
from pipeline.tests.test_qualified_edition_receipts import receipt_fixture
from pipeline.tests.test_qualified_direct_audio_receipts import fixture as direct_fixture, seal as seal_direct


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'jobs').mkdir()
        (self.root / 'sync').mkdir()
        self.queue = [{'video_id': 'abcdefghijk', 'channel_dir': 'example', 'source_channel_name': 'Example',
                       'tab': 'videos', 'listing_rank': '0', 'title': 'Public title'}]
        self.audio = {'video_id': 'abcdefghijk', 'channel_dir': 'example', 'status': 'deleted',
            'path': 'audio/example/Videos/abcdefghijk.webm', 'tab': 'videos',
            'remote': 'etdrive:04 Audio/example/Videos/abcdefghijk.webm', 'bytes': 20,
            'drive_id': 'PRIVATE AUDIO', 'md5': 'a' * 32, 'sha256': 'b' * 64,
            'metadata': {'drive_id': 'PRIVATE METADATA', 'md5': 'c' * 32, 'sha256': 'd' * 64,
                'bytes': 20, 'remote': 'etdrive:04 Audio/example/Videos/abcdefghijk.info.json'}}
        self.asr = {'video_id': 'abcdefghijk', 'channel_dir': 'example', 'run_id': 'run-1',
            'status': 'verified', 'artifact_kind': 'asr_bundle', 'drive_id': 'PRIVATE RESULT',
            'remote': 'etdrive:04 Audio/example/Videos/abcdefghijk/ASR/run-1/run-1.zip',
            'bytes': 10, 'md5': 'e' * 32, 'sha256': 'f' * 64,
            'source_audio_drive_id': 'PRIVATE AUDIO', 'source_audio_sha256': 'b' * 64,
            'private_text': 'PRIVATE TRANSCRIPT', 'quality_state': 'unreviewed_asr'}

    def journal(self, name, records):
        (self.root / 'sync' / name).write_text(''.join(json.dumps(x) + '\n' for x in records), encoding='utf-8')

    def run_coverage(self):
        with (self.root / 'jobs/queue_newest20_enriched.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(self.queue[0]))
            writer.writeheader()
            writer.writerows(self.queue)
        return coverage.coverage(self.root)

    def test_right_video_under_another_creator_cannot_complete_the_recording(self):
        self.queue[0]['channel_dir'] = 'different-creator'
        self.journal('drive_ingest_manifest.jsonl', [self.audio])
        self.journal('asr_manifest.jsonl', [self.asr])
        public, saved = self.run_coverage()
        self.assertEqual(saved, [])
        self.assertEqual(public['summary']['remaining_audio'], 1)
        self.assertEqual(public['summary']['native_asr'], 0)

    def mirror(self):
        digest = '1' * 64
        parent = 'etdrive:04 Audio/example/Videos/abcdefghijk/PublisherVariants/' + digest
        def obj(remote, value):
            return {'remote': remote, 'bytes': 20, 'drive_id': 'PRIVATE ' + value,
                    'sha256': digest if value == 'audio' else '2' * 64, 'md5': '3' * 32}
        return {'schema_version': 1, 'status': 'verified', 'kind': 'publisher_mirror_audio_variant',
            'association_method': 'publisher_rss_exact_youtube_id', 'exact_youtube_crossreference': True,
            'original_youtube_link': 'https://www.youtube.com/watch?v=abcdefghijk',
            'associated_youtube_id': 'abcdefghijk', 'channel_dir': 'example', 'variant_id': digest,
            'native_youtube_bytes': False, 'changes_native_audio_count': False,
            'changes_native_asr_count': False, 'changes_native_caption_count': False, 'human_verified': False,
            'audio': obj(parent + '/publisher-audio.mp3', 'audio'),
            'provenance': obj(parent + '/provenance.json', 'provenance'),
            'caption_bundle': dict(obj(parent + '/Captions/' + '2' * 64 + '/captions.zip', 'caption'),
                                   usable_timed_text=True, language='en')}

    def test_source_receipts_keep_publisher_editions_deduplicated(self):
        self.journal('drive_ingest_manifest.jsonl', [self.audio])
        mirror = self.mirror()
        self.journal('publisher_mirror_manifest.jsonl', [mirror, mirror])
        public, videos = self.run_coverage()
        self.assertEqual(public['summary']['audio_available'], 1)
        self.assertEqual(public['summary']['youtube_native_audio'], 1)
        self.assertEqual(public['summary']['publisher_only_audio'], 0)
        self.assertEqual(public['summary']['audio_with_saved_text'], 1)
        self.assertEqual(len(videos), 1)
        self.assertEqual(public['channels'][0]['target'], 1)
        self.assertNotIn('PRIVATE', json.dumps((public, videos)))
        self.assertNotIn(str(self.root), json.dumps((public, videos)))
        self.journal('drive_ingest_manifest.jsonl', [dict(self.audio, drive_id='')])
        public, videos = self.run_coverage()
        self.assertEqual(public['channels'][0]['publisher_only_audio'], 1)
        self.assertEqual(videos[0]['audio_source'], 'publisher_edition')

    def test_dangling_caption_or_wrong_source_asr_does_not_credit_text(self):
        self.journal('drive_ingest_manifest.jsonl', [self.audio])
        self.journal('asr_manifest.jsonl', [dict(self.asr, source_audio_sha256='0' * 64)])
        self.journal('publisher_caption_manifest.jsonl', [{'status': 'verified', 'video_id': 'abcdefghijk'}])
        public, _ = self.run_coverage()
        self.assertEqual(public['summary']['audio_with_saved_text'], 0)
        self.journal('asr_manifest.jsonl', [self.asr, dict(self.asr, run_id='run-2', status='pending')])
        public, videos = self.run_coverage()
        self.assertEqual(public['summary']['native_asr'], 1)
        self.assertTrue(videos[0]['saved_text'])

    def test_unverified_audio_never_appears_as_a_download(self):
        self.journal('drive_ingest_manifest.jsonl', [dict(self.audio, status='prepared')])
        public, videos = self.run_coverage()
        self.assertEqual(public['channels'][0]['remaining_audio'], 1)
        self.assertEqual(videos, [])

    def test_qualified_youtube_edition_adds_audio_with_explicit_source_and_zero_text(self):
        self.journal('progressive_audio_extracts_manifest.jsonl', [receipt_fixture()])
        self.journal('asr_manifest.jsonl', [self.asr])
        public, videos = self.run_coverage()
        self.assertEqual(1, public['summary']['audio_available'])
        self.assertEqual(1, public['summary']['qualified_youtube_only_audio'])
        self.assertEqual(0, public['summary']['youtube_native_audio'])
        self.assertEqual(0, public['summary']['publisher_only_audio'])
        self.assertEqual(0, public['summary']['audio_with_saved_text'])
        self.assertEqual('youtube_track_unverified', videos[0]['audio_source'])
        self.assertEqual(1, public['activity']['summary']['saved'])
        self.assertNotIn('source-provenance', json.dumps((public, videos)))

    def direct_edition(self):
        record = direct_fixture()
        record.update(channel_dir='example', tab='videos')
        seal_direct(record)
        for key in ('audio', 'metadata'):
            proof = record[key]['remote_proof']
            proof['remote'] = proof['remote'].replace('testdrive:Audio', 'etdrive:04 Audio', 1)
        return record

    def test_qualified_direct_audio_counts_unknown_track_without_native_or_text(self):
        self.journal('progressive_audio_extracts_manifest.jsonl', [self.direct_edition()])
        self.journal('asr_manifest.jsonl', [self.asr])
        public, videos = self.run_coverage()
        self.assertEqual(1, public['summary']['audio_available'])
        self.assertEqual(1, public['summary']['qualified_youtube_only_audio'])
        self.assertEqual(0, public['summary']['youtube_native_audio'])
        self.assertEqual(0, public['summary']['audio_with_saved_text'])
        self.assertEqual('youtube_track_unverified', videos[0]['audio_source'])

    def test_direct_and_muxed_editions_deduplicate_with_each_other_and_native(self):
        self.journal('progressive_audio_extracts_manifest.jsonl', [self.direct_edition(), receipt_fixture()])
        public, videos = self.run_coverage()
        self.assertEqual(1, public['summary']['audio_available'])
        self.assertEqual(1, public['summary']['qualified_youtube_only_audio'])
        self.journal('drive_ingest_manifest.jsonl', [self.audio])
        public, videos = self.run_coverage()
        self.assertEqual(1, public['summary']['audio_available'])
        self.assertEqual(0, public['summary']['qualified_youtube_only_audio'])
        self.assertEqual('youtube_native', videos[0]['audio_source'])

    def test_native_and_publisher_overlap_do_not_double_count_or_mislabel_edition(self):
        self.journal('progressive_audio_extracts_manifest.jsonl', [receipt_fixture(), receipt_fixture()])
        self.journal('drive_ingest_manifest.jsonl', [self.audio])
        public, videos = self.run_coverage()
        self.assertEqual(1, public['summary']['audio_available'])
        self.assertEqual(0, public['summary']['qualified_youtube_only_audio'])
        self.assertEqual('youtube_native', videos[0]['audio_source'])
        self.journal('drive_ingest_manifest.jsonl', [])
        self.journal('publisher_mirror_manifest.jsonl', [self.mirror()])
        public, videos = self.run_coverage()
        self.assertEqual(1, public['summary']['publisher_only_audio'])
        self.assertEqual(0, public['summary']['qualified_youtube_only_audio'])
        self.assertEqual('publisher_edition', videos[0]['audio_source'])

    def test_qualified_proof_must_match_queue_creator_and_tab(self):
        self.journal('progressive_audio_extracts_manifest.jsonl', [receipt_fixture()])
        self.queue[0]['channel_dir'] = 'different-creator'
        public, videos = self.run_coverage()
        self.assertEqual(0, public['summary']['audio_available']); self.assertEqual([], videos)

    def test_legacy_or_partial_edition_receipt_never_credits_a_download(self):
        record = receipt_fixture(); record['audio']['remote_proof']['bytes'] -= 1
        legacy = receipt_fixture(); legacy['kind'] = 'youtube_progressive_AAC_packet_preserving_extract'
        self.journal('progressive_audio_extracts_manifest.jsonl', [record, legacy])
        public, videos = self.run_coverage()
        self.assertEqual(0, public['summary']['audio_available']); self.assertEqual([], videos)

    def test_duplicate_video_or_rank_does_not_inflate_the_target(self):
        self.queue.append(dict(self.queue[0]))
        with self.assertRaises(ValueError):
            self.run_coverage()

    def test_csv_preserves_unicode_and_neutralizes_spreadsheet_formulas(self):
        raw = coverage.csv_bytes([{'title': '=1+1', 'channel': 'Athina Król'}], ('title', 'channel'))
        row = next(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        self.assertEqual(row, {'title': "'=1+1", 'channel': 'Athina Król'})

    def test_isolated_cli_writes_all_three_public_files(self):
        self.journal('drive_ingest_manifest.jsonl', [self.audio])
        self.run_coverage()
        out = self.root / 'public/channel_download_coverage.json'
        result = subprocess.run([sys.executable, '-I', str(Path(coverage.__file__).resolve()),
            '--root', str(self.root), '--out', str(out)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(out.read_text())['summary']['audio_available'], 1)
        for path in (out, out.with_suffix('.csv'), out.parent / 'downloaded_videos.csv'):
            self.assertTrue(path.is_file())
            self.assertNotIn('PRIVATE', path.read_text(encoding='utf-8-sig'))

    def test_mixed_selection_preserves_formats_empty_creators_and_written_excerpts(self):
        video = self.queue[0]['video_id']
        channel = 'UC' + 'd' * 22
        groups = [{'channel_dir':'example','channel_id':channel,'selected':1,'scope':'short_complete_displayed_list',
                   'items':[{'channel_dir':'example','channel_id':channel,'video_id':video,'slot':1,'source_position':2,'tab':'shorts','title':'Example short'}]},
                  {'channel_dir':'unseen','channel_id':'UC'+'e'*22,'selected':0,'scope':'unobserved','items':[]}]
        selection = self.root / 'selection.json'
        selection.write_text(json.dumps({'per_channel':20,'channels':groups}))
        message = {'video_id':video,'channel_dir':'example','status':'verified','schema_version':1,'language':'en','timed':False,
                   'artifact_kind':'exact_linked_publisher_written_message','youtube_caption':False,'changes_full_asr_count':False,
                   'changes_selected_audio_count':False,'changes_native_audio_count':False,'full_video_text_verified':False,'word_count':45,
                   'bundle':{'bytes':150,'md5':'a'*32,'sha256':'c'*64,'drive_id':'PRIVATE TEXT',
                             'remote':'etdrive:04 Audio/example/Shorts/'+video+'/PublisherText/'+'c'*64+'/published-message.en.zip'}}
        self.journal('publisher_companion_manifest.jsonl', [message])
        public, saved = coverage.coverage(self.root, selection=selection)
        self.assertEqual(saved, [])
        self.assertEqual(public['summary']['channels'], 2)
        self.assertEqual(public['summary']['selected_by_format'], {'shorts':1})
        self.assertEqual(public['summary']['selection_shortfall'], 39)
        self.assertEqual(public['summary']['publisher_written_messages'], 1)
        self.assertEqual(public['summary']['audio_with_saved_text'], 0)
        self.assertEqual(public['channels'][1]['selection_scope'], 'unobserved')
        groups[0]['items'][0]['channel_id'] = groups[1]['channel_id']
        selection.write_text(json.dumps({'per_channel':20,'channels':groups}))
        with self.assertRaises(ValueError):
            coverage.coverage(self.root, selection=selection)

    def test_closed_refusals_apply_only_to_uncovered_inactive_recordings(self):
        at = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
        channel = 'UC' + 'd' * 22
        videos = ['00000000001', '00000000002', '00000000003', '00000000004']
        rows = [dict(self.queue[0], video_id=video, expected_channel_id=channel) for video in videos]
        evidence = [{'at_epoch': at.timestamp() - 2, 'status': 403}]
        states = [dict(row, disposition='current_source_refusal', current_source_refusals=evidence) for row in rows]
        states[-1].update(disposition='local_or_administrative_hold', current_source_refusals=[])
        source = self.root / 'closed.json'
        closed = dict(kind='strict_primary_closed_disposition_snapshot', schema_version=1, at_epoch=at.timestamp()-1,
                      primary_scope_count=len(rows), rows=states)
        source.write_text(json.dumps(closed))
        active = {'public': {'state': 'running'}, 'video_stages': {videos[1]: 'downloading'}}
        with patch.object(coverage.status, 'rolling_native_state', return_value=active):
            result = coverage.channel_activity(self.root, rows, {videos[0]}, at, dispositions=source)
        self.assertEqual({k: v for k, v in result['summary'].items() if v},
                         dict(saved=1, downloading=1, waiting_for_source=1, other_pending=1))
        for invalid in (dict(closed, at_epoch=at.timestamp()+1), dict(closed, rows=states[:-1]),
                        dict(closed, rows=[*states[:-1], states[0]]),
                        dict(closed, rows=[dict(states[0], expected_channel_id='UC'+'z'*22), *states[1:]]),
                        dict(closed, rows=[dict(states[0], current_source_refusals=[]), *states[1:]])):
            source.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                coverage.read_closed_dispositions(source, rows, at)

    def test_untimed_transcript_must_belong_to_its_publisher_audio_edition(self):
        record = self.mirror()
        record.pop('caption_bundle')
        parent = record['audio']['remote'].rpartition('/')[0]
        record['caption_state'] = 'english_publisher_transcript_untimed'
        record['publisher_transcript'] = {'remote':parent+'/publisher-transcript.en.txt','drive_id':'PRIVATE TEXT','md5':'f'*32,
                                          'sha256':'d'*64,'bytes':320,'language':'en','timed':False,'paragraphs':5}
        self.journal('publisher_mirror_manifest.jsonl',[record])
        public, saved = self.run_coverage()
        self.assertTrue(saved[0]['saved_text'])
        self.assertEqual(public['summary']['native_caption_videos'], 0)
        record['publisher_transcript']['remote'] = record['publisher_transcript']['remote'].replace('1'*64, '0'*64)
        self.journal('publisher_mirror_manifest.jsonl',[record])
        self.assertFalse(self.run_coverage()[1][0]['saved_text'])


if __name__ == '__main__':
    unittest.main()
