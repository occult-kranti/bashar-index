"""Generated-only CI updates still need matching tables and safe inventories."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[2] / 'scripts/check_collection_snapshot.py'
spec = importlib.util.spec_from_file_location('public_snapshot_check', path)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class SnapshotChecks(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.channel = dict(channel='A channel', channel_dir='a-channel', target=2, youtube_audio=1,
            publisher_only_audio=0, audio_total=1, with_saved_text=1, remaining_audio=1)
        self.data = dict(schema_version=1, scope='newest20_receipt_coverage', generated_at='2026-11-18T00:00:00Z',
            channels=[self.channel], summary=dict(channels=1, latest20_target=2, youtube_native_audio=1,
                publisher_only_audio=0, audio_available=1, audio_with_saved_text=1, remaining_audio=1))
        self.video = dict(channel='A channel', channel_dir='a-channel', video_id='-0000000000',
            title='=A title', url='https://www.youtube.com/watch?v=-0000000000', listing_rank=0,
            audio_source='youtube_native', saved_text=True, native_audio_bytes=100)
        self.save()

    def save(self):
        (self.root / 'channel_download_coverage.json').write_text(json.dumps(self.data), encoding='utf-8')
        (self.root / 'channel_download_coverage.csv').write_bytes(checker.csv_bytes([self.channel], checker.CHANNEL_FIELDS))
        (self.root / 'downloaded_videos.csv').write_bytes(checker.csv_bytes([self.video], checker.VIDEO_FIELDS))
        for name, scope in (('ingestion_status.json', 'local_youtube_collection'), ('collection_eta.json', 'collection_eta')):
            (self.root / name).write_text(json.dumps({'scope': scope}), encoding='utf-8')

    def test_matching_tables_accept_formula_escaped_ids_and_titles(self):
        self.assertEqual(checker.check(self.root), {'channels': 1, 'audio': 1, 'target': 2})

    def test_git_normalized_lf_and_windows_crlf_tables_are_equivalent(self):
        for name in ('channel_download_coverage.csv', 'downloaded_videos.csv'):
            p = self.root / name
            p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
        self.assertEqual(checker.check(self.root), {'channels': 1, 'audio': 1, 'target': 2})
        p = self.root / 'channel_download_coverage.csv'
        p.write_bytes(p.read_bytes().replace(b'A channel', b'A changed channel'))
        with self.assertRaisesRegex(ValueError, 'channel_csv_drift'):
            checker.check(self.root)

    def test_changed_summary_cannot_pass_a_generated_only_release(self):
        self.data['summary']['audio_available'] = 2
        self.save()
        with self.assertRaisesRegex(ValueError, 'summary_totals'):
            checker.check(self.root)

    def test_activity_partition_and_ownership_cannot_inflate_work(self):
        stages = dict(saved=1, downloading=0, processing=0, awaiting_upload=0, queued=1, other_pending=0)
        self.data['activity'] = dict(schema_version=1, state='running', summary=dict(stages),
            channels=[dict(channel_dir='a-channel', target=2, **stages)])
        self.save(); checker.check(self.root)
        self.data['activity']['channels'][0]['queued'] = 2
        self.save()
        with self.assertRaisesRegex(ValueError, 'activity_partition'):
            checker.check(self.root)
        self.data['activity']['channels'][0].update(queued=0, downloading=1)
        self.data['activity']['summary'].update(queued=0, downloading=1)
        self.data['activity']['state'] = 'paused'; self.save()
        with self.assertRaisesRegex(ValueError, 'activity_ownership'):
            checker.check(self.root)

    def test_missing_inventory_row_and_duplicate_identity_are_rejected(self):
        p = self.root / 'downloaded_videos.csv'
        p.write_bytes(checker.csv_bytes([], checker.VIDEO_FIELDS))
        with self.assertRaisesRegex(ValueError, 'video_channel_totals'):
            checker.check(self.root)
        p.write_bytes(checker.csv_bytes([self.video, self.video], checker.VIDEO_FIELDS))
        with self.assertRaisesRegex(ValueError, 'video_identity'):
            checker.check(self.root)

    def test_spreadsheet_formula_cannot_be_inserted_by_editing_generated_csv(self):
        p = self.root / 'downloaded_videos.csv'
        p.write_bytes(p.read_bytes().replace(b"'=A title", b'=A title'))
        with self.assertRaisesRegex(ValueError, 'unsafe_spreadsheet_cell'):
            checker.check(self.root)
