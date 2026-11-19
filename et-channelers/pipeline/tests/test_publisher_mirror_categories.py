import json
from pathlib import Path
import tempfile
import unittest

from pipeline import ingestion_status


class PublisherMirrorCategoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'sync').mkdir()
        (self.root / 'jobs').mkdir()
        self.video = 'example1234'
        self.remote = 'archive:Audio'
        self.channel = 'test-channel'

    def receipt(self, folder, include_tab=False):
        parent = f'{self.remote}/{self.channel}/{folder}/{self.video}/PublisherVariants/' + 'a' * 64

        def artifact(name, digest):
            return {'remote': parent + '/' + name, 'bytes': 256, 'drive_id': digest,
                    'md5': digest * 32, 'sha256': digest * 64}

        row = {'schema_version': 1, 'status': 'verified', 'kind': 'qualified_publisher_mirror_audio_variant',
               'associated_youtube_id': self.video, 'channel_dir': self.channel, 'variant_id': 'a' * 64,
               'association_method': 'publisher_owner_title_date_duration', 'exact_youtube_crossreference': False,
               'native_youtube_bytes': False, 'changes_native_audio_count': False, 'changes_native_asr_count': False,
               'changes_native_caption_count': False, 'human_verified': False, 'audio': artifact('publisher-audio.aac', 'a'),
               'provenance': artifact('provenance.json', 'b'),
               'caption_bundle': {**artifact('Captions/' + 'c' * 64 + '/captions.zip', 'c'),
                                  'language': 'en', 'usable_timed_text': True}}
        if include_tab:
            row.update(source_tab=folder.lower(), source_tab_evidence={
                'channel_dir': self.channel, 'video_id': self.video, 'tab': folder.lower(), 'roster_sha256': 'd' * 64})
        return row

    def coverage(self, receipt, selected_tab=None):
        (self.root / 'sync/publisher_mirror_manifest.jsonl').write_text(json.dumps(receipt) + '\n', encoding='utf-8')
        rows = [] if selected_tab is None else [{'channel_dir': self.channel, 'video_id': self.video, 'tab': selected_tab}]
        return ingestion_status.publisher_mirror_coverage(self.root, {self.video}, self.remote, rows)

    def test_regular_legacy_and_evidenced_categories(self):
        good = ({self.video}, {self.video}, set())
        self.assertEqual(self.coverage(self.receipt('Videos')), good)
        for folder in ('Shorts', 'Streams'):
            with self.subTest(folder=folder):
                self.assertEqual(self.coverage(self.receipt(folder), folder.lower()), good)
                self.assertEqual(self.coverage(self.receipt(folder, include_tab=True)), good)
                self.assertEqual(self.coverage(self.receipt(folder)), (set(), set(), set()))

    def test_conflicting_or_unbound_evidence_fails(self):
        empty = (set(), set(), set())
        row = self.receipt('Streams', include_tab=True)
        self.assertEqual(self.coverage(row, 'shorts'), empty)
        row['source_tab_evidence']['video_id'] = 'other123456'
        self.assertEqual(self.coverage(row, 'streams'), empty)
        legacy = self.receipt('Videos')
        self.assertEqual(self.coverage(legacy, 'streams'), empty)
        row = self.receipt('Shorts', include_tab=True)
        row['provenance']['remote'] = row['provenance']['remote'].replace('/Shorts/', '/Videos/')
        self.assertEqual(self.coverage(row), empty)

    def test_timed_text_is_bound_to_its_own_source_variant(self):
        row = self.receipt('Streams', include_tab=True)
        row['caption_bundle']['remote'] = row['caption_bundle']['remote'].replace('/Streams/', '/Videos/')
        self.assertEqual(self.coverage(row), ({self.video}, set(), set()))
