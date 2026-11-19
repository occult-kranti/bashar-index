import copy
import json
from pathlib import Path
import tempfile
import unittest

from pipeline import ingestion_status as status


class EpisodePageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'sync').mkdir()
        self.video = 'GEhE9JPrK78'
        self.uuid = '1fc8d52c-59c7-4837-926d-2ee83a64dd8c'
        self.remote = 'archive:Audio'
        self.parent = f'{self.remote}/julie-ryan/Videos/{self.video}/PublisherVariants/' + 'a' * 64

    def record(self):
        def art(name, letter):
            return dict(bytes=256, md5=letter * 32, sha256=letter * 64,
                        drive_id=letter, remote=self.parent + '/' + name)
        return dict(schema_version=1, status='verified', kind='publisher_episode_page_exact_youtube_id',
                    association_method='publisher_episode_page_exact_youtube_id', exact_youtube_crossreference=True,
                    recording_equivalence_verified=False, provider='ART19', channel_dir='julie-ryan',
                    associated_youtube_id=self.video, variant_id='a' * 64, source_tab='videos',
                    original_youtube_link='https://www.youtube.com/watch?v=' + self.video,
                    native_youtube_bytes=False, changes_native_audio_count=False, changes_native_asr_count=False,
                    changes_native_caption_count=False, human_verified=False,
                    audio=art('publisher-audio.mp3', 'a'), provenance=art('provenance.json', 'b'),
                    publisher_episode_binding=dict(episode_number=860, art19_episode_uuid=self.uuid,
                        publisher_channel_id='UCMYtR_CBJeC6MKbzuQ2dd6A', reviewed_pair_sha256='e' * 64,
                        episode_page_url='https://askjulieryan.com/podcast/860/',
                        youtube_player_url='https://www.youtube.com/embed/' + self.video,
                        art19_player_url=f'https://art19.com/shows/97147093-d307-4e02-8559-09ab2b7767ce/episodes/{self.uuid}/embed',
                        rss_feed_url='https://rss.art19.com/ask-julie-ryan', rss_guid='gid://example/860',
                        rss_enclosure_url=f'https://rss.art19.com/episodes/{self.uuid}.mp3?public_rss=1'),
                    publisher_transcript={**art('publisher-transcript.en.txt', 'c'), 'language': 'en', 'timed': False, 'paragraphs': 50},
                    publisher_transcript_document=art('publisher-transcript.source.docx', 'd'),
                    publisher_transcript_provenance=dict(episode_page_url='https://askjulieryan.com/podcast/860/',
                        art19_episode_uuid=self.uuid, associated_youtube_id=self.video, declared_label='Episode Transcript',
                        source_url='https://askjulieryan.com/wp-content/uploads/2026/10/transcript-Anjel.docx',
                        source_document_sha256='d' * 64, language_verification='english_document_lexical_check'),
                    caption_state='english_publisher_transcript_untimed', caption_bundles=[])

    def view(self, record):
        (self.root / 'sync/publisher_mirror_manifest.jsonl').write_text(json.dumps(record) + '\n', encoding='utf-8')
        return status.publisher_mirror_evidence(self.root, {self.video}, self.remote,
            [{'video_id': self.video, 'channel_dir': 'julie-ryan', 'tab': 'videos'}])

    def test_paired_publisher_edition_and_separate_untimed_transcript(self):
        self.assertEqual(self.view(self.record()), ({self.video}, set(), set(), {self.video}))

    def test_wrong_player_video_uuid_episode_or_owner_cannot_count(self):
        for field, value in [('youtube_player_url', 'https://www.youtube.com/embed/other000000'),
                             ('art19_episode_uuid', 'ffffffff-ffff-ffff-ffff-ffffffffffff'),
                             ('episode_number', 861), ('publisher_channel_id', 'UCforeign'),
                             ('rss_enclosure_url', 'https://rss.art19.com/episodes/foreign.mp3')]:
            row = self.record()
            row['publisher_episode_binding'][field] = value
            with self.subTest(field=field):
                self.assertEqual(self.view(row), (set(), set(), set(), set()))

    def test_transcript_foreign_episode_source_hash_language_or_object_is_separate(self):
        for field, value in [('episode_page_url', 'https://askjulieryan.com/podcast/861/'),
                             ('associated_youtube_id', 'other000000'),
                             ('art19_episode_uuid', 'ffffffff-ffff-ffff-ffff-ffffffffffff'),
                             ('source_document_sha256', 'e' * 64),
                             ('source_url', 'https://foreign.example/transcript.docx'),
                             ('language_verification', 'unknown')]:
            row = self.record()
            row['publisher_transcript_provenance'][field] = value
            with self.subTest(field=field):
                self.assertEqual(self.view(row), ({self.video}, set(), set(), set()))
        row = self.record()
        row['publisher_transcript_document']['drive_id'] = row['audio']['drive_id']
        self.assertEqual(self.view(row), ({self.video}, set(), set(), set()))


if __name__ == '__main__':
    unittest.main()
