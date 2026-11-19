import json
from pathlib import Path
import tempfile
import unittest

from pipeline import collection_coverage, ingestion_status
from pipeline.publisher_caption_batch import verified_videos


REMOTE = 'archive:Audio'
CREATOR = 'test-channel'
VIDEO = 'abcdefghijk'
CHANNEL = 'UC' + 'a' * 22


def receipt():
    digest = 'b' * 64
    item = {
        'provider': 'Rumble', 'publisher_account': 'https://rumble.com/user/example',
        'publisher_watch_url': 'https://rumble.com/vxabcd-example.html', 'publisher_watch_id': 'vxabcd',
        'publisher_embed_id': 'v7777', 'publisher_title': 'Quiet & Still', 'publisher_date': '2026-11-18T10:00:00Z',
        'declared_downloadable': True, 'association_method': 'same_publisher_normalized_title_date_and_duration',
        'source_documents': {k:'c' * 64 for k in ('listing', 'watch', 'embed')}, 'channel_dir': CREATOR, 'video_id': VIDEO,
        'tab': 'shorts', 'selection_sha256': 'd' * 64, 'selected_channel_id': CHANNEL, 'selected_title': 'Quiet & Still #example',
        'selected_duration_s': 61, 'publisher_duration_s': 60, 'listed_upload_date': '2026-11-18',
        'recording_equivalence_verified': False, 'source_format': 'vtt', 'native_youtube_caption': False,
        'speech_coverage_verified': False, 'audio_binding': None, 'caption_kind': 'automatic_original',
        'track_key': 'en-auto', 'language': 'en', 'caption_label': 'English (auto)', 'track_url_sha256': 'd' * 64,
        'source_sha256': 'a' * 64, 'source_bytes': 200, 'segment_count': 4, 'first_cue_start': .25,
        'last_cue_end': 59.75, 'word_count': 90,
    }
    return {'schema_version': 1, 'artifact_kind': 'publisher_edition_caption_batch', 'status': 'verified',
            'changes_native_audio_count': False, 'changes_native_caption_count': False, 'changes_full_asr_count': False,
            'channel_dir': CREATOR, 'items': [item],
            'proof': {'sha256': digest, 'md5': 'a' * 32, 'bytes': 512, 'drive_id': 'private-archive-id',
                      'remote': f'{REMOTE}/{CREATOR}/PublisherCaptions/Batches/{digest}/publisher-captions.zip'}}


class PublisherCaptionBatchTests(unittest.TestCase):
    def verify(self, record, tab='shorts'):
        return verified_videos(record, {VIDEO}, REMOTE, {VIDEO: (CREATOR,tab)})

    def test_companion_requires_target_owner_and_a_real_edition_boundary(self):
        record = receipt()
        self.assertEqual(self.verify(record), {VIDEO})
        self.assertFalse(self.verify(record, 'videos'))
        for key, value in (
            ('publisher_account', 'https://rumble.com.evil/user/example'), ('publisher_watch_url', 'https://rumble.com/vother-example.html'),
            ('publisher_duration_s', 120), ('listed_upload_date', '2025-11-18'), ('declared_downloadable', False),
            ('source_documents', {}), ('selection_sha256', 'missing'), ('publisher_title', 'Other edition'),
            ('last_cue_end', 124), ('first_cue_start', float('nan')), ('speech_coverage_verified', True),
            ('audio_binding', 'another-audio'), ('native_youtube_caption', True), ('source_sha256', []),
            ('track_key', 'en-translated'), ('caption_label', 'English (auto-translated)'),
        ):
            with self.subTest(field=key):
                broken = receipt()
                broken['items'][0][key] = value
                self.assertFalse(self.verify(broken))
        record['items'][0].update(track_key='en-US', caption_label='English', caption_kind='publisher_provided_unspecified')
        self.assertEqual(self.verify(record), {VIDEO})
        record['proof']['remote'] = record['proof']['remote'].replace('/test-channel/', '/other/')
        self.assertFalse(self.verify(record))

    def test_collection_keeps_publisher_companion_separate_from_downloaded_text_and_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'sync').mkdir()
            (root / 'jobs').mkdir()
            ledger = root / 'sync/publisher_caption_manifest.jsonl'
            ledger.write_text(json.dumps(receipt()) + '\n', encoding='utf-8')
            row = {'video_id': VIDEO, 'channel_dir': CREATOR, 'channel_id': CHANNEL, 'tab': 'shorts',
                   'title': 'Quiet & Still #example', 'slot': 1, 'source_position': 1}
            listing = root / 'selection.json'
            listing.write_text(json.dumps({'per_channel':20, 'channels':[{'channel_dir': CREATOR, 'channel_id': CHANNEL,
                'items': [row], 'selected': 1, 'scope':'short_complete_displayed_list'}]}), encoding='utf-8')
            self.assertEqual(ingestion_status.publisher_timed_text_coverage(root, {VIDEO}, REMOTE, [row]), {VIDEO})
            report, videos = collection_coverage.coverage(root, remote=REMOTE, selection=listing)
            self.assertEqual(report['channels'][0]['with_independent_publisher_captions'], 1)
            self.assertEqual(report['summary']['independent_publisher_caption_videos'], 1)
            self.assertEqual(report['summary']['audio_available'], 0)
            self.assertEqual(report['summary']['native_caption_videos'], 0)
            self.assertEqual(report['summary']['audio_with_saved_text_or_independent_publisher_caption'], 0)
            self.assertEqual(videos, [])
