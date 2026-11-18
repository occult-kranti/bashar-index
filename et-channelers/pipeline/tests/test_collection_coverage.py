"""Current channel inventory: receipt boundaries, source joins and safe export."""
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from pipeline import collection_coverage as coverage


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


if __name__ == '__main__':
    unittest.main()
