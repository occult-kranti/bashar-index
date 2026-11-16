"""Explicit upcoming errors defer one item without stopping other channels."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import drive_ingest as ingest


class PremiereTests(unittest.TestCase):
    def setUp(self):
        self.row = {'video_id': 'DmeE1ogs9s8', 'channel_dir': 'premiere-channel', 'tab': 'videos',
                    'url': 'https://www.youtube.com/watch?v=DmeE1ogs9s8'}
        self.args = SimpleNamespace(ytdlp='unused', timeout=1)
        self.countdown = 'ERROR: [youtube] DmeE1ogs9s8: Premieres in 20 minutes'

    def classify(self, stderr):
        with patch.object(ingest, 'run_tool', return_value=SimpleNamespace(returncode=1, stdout='', stderr=stderr)):
            with self.assertRaises(ingest.IngestError) as raised:
                ingest.extract_audio(self.args, self.row)
        return raised.exception.kind

    def test_explicit_premiere_and_scheduled_live_errors_are_deferred_live(self):
        for message in (self.countdown,
                        'ERROR: [youtube] DmeE1ogs9s8: This live event will begin in 3 hours.',
                        'ERROR: [youtube] DmeE1ogs9s8: Premieres in a few moments'):
            with self.subTest(message=message):
                self.assertEqual(self.classify(message), 'live')

    def test_access_blocks_keep_priority_over_a_premiere_message(self):
        for message, expected in (
                ('HTTP Error 403: Forbidden', 'forbidden'),
                ('HTTP Error 429: Too Many Requests', 'rate_limited'),
                ('Sign in to confirm you are not a bot', 'bot_check'),
                ('This is a members-only video', 'login_required'),
                ('Video unavailable. This content is not available, try again later', 'rate_limited')):
            with self.subTest(expected=expected):
                self.assertEqual(self.classify(message + '\n' + self.countdown), expected)

    def test_unrelated_messages_and_other_item_errors_are_not_reclassified(self):
        for message, expected in (
                ('ERROR: [youtube] DmeE1ogs9s8: Private video', 'unavailable'),
                ('ERROR: [youtube] DmeE1ogs9s8: This live event has ended', 'other'),
                ('[info] title: Premieres in 20 minutes\nERROR: unrelated failure', 'other'),
                ('ERROR: [youtube] abcdefghijk: Premieres in 20 minutes', 'other')):
            with self.subTest(message=message):
                self.assertEqual(self.classify(message), expected)

    def premiere_run(self, available_on_revisit, failure_kind='live'):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.addCleanup(lambda: ingest._ROOT_BUDGETS.pop(root.resolve(), None))
            args = SimpleNamespace(root=root, ytdlp='unused', timeout=1, max_local_bytes=100_000_000,
                                   max_item_bytes=0, min_free_bytes=0, rclone='unused', rclone_config=None,
                                   download_only=False, collect_metadata=True, remote='etdrive:04 Audio',
                                   limit=0, min_interval=0, workers=1, upload_transfers=2,
                                   upload_batch_items=1, upload_batch_seconds=0, ready_items=2, rate_bytes=1024)
            available = {'video_id': 'abcdefghijk', 'channel_dir': 'available-channel', 'tab': 'videos',
                         'url': 'https://www.youtube.com/watch?v=abcdefghijk'}
            info = {'id': available['video_id'], 'ext': 'webm', 'protocol': 'https', 'vcodec': 'none',
                    'filesize': 10, 'duration': 10, 'upload_date': '20260101',
                    'url': 'https://fixture.googlevideo.com/audio'}
            selections = []

            def select(command, timeout):
                selections.append(command[-1])
                if command[-1] == self.row['url']:
                    if not available_on_revisit or selections.count(self.row['url']) == 1:
                        error = self.countdown if failure_kind == 'live' else (
                            'ERROR: [youtube] DmeE1ogs9s8: Requested format is not available')
                        return SimpleNamespace(returncode=1, stdout='', stderr=error)
                    return SimpleNamespace(returncode=0, stdout=json.dumps(dict(info, id=self.row['video_id'])), stderr='')
                return SimpleNamespace(returncode=0, stdout=json.dumps(info), stderr='')

            def stream(info, part, budget, *unused):
                with open(part, 'wb') as out:
                    budget.write(out, b'0123456789')
                return ingest.hash_file(part)

            drive = Mock()

            def proofs(remote, paths, manifest):
                return {path: {'Size': (record := ingest.hash_file(root / 'audio' / path))['bytes'],
                               'Hashes': {'MD5': record['md5']}, 'ID': path, 'IsDir': False}
                        for path in paths}

            drive.stat_batch.side_effect = proofs
            with patch.object(ingest, 'Rclone', return_value=drive), \
                    patch.object(ingest, 'run_tool', side_effect=select), \
                    patch.object(ingest, 'stream_audio', side_effect=stream) as transfer, \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = ingest.run(args, [self.row, available])
            state = ingest.load_state(root / 'sync' / 'drive_ingest_manifest.jsonl')
            pending = state[self.row['video_id']]
            if available_on_revisit:
                self.assertEqual(result, 0)
                self.assertTrue(ingest.receipt_complete(pending, self.row, args.remote))
            else:
                self.assertEqual(result, 3, 'the pending premiere must keep the phase gate closed')
                self.assertEqual(pending['status'], 'deferred_live' if failure_kind == 'live' else 'deferred_format')
                self.assertEqual(pending['error_class'], failure_kind)
                self.assertFalse(ingest.receipt_complete(pending, self.row, args.remote))
            self.assertNotIn('retry_not_before_epoch', pending)
            self.assertFalse(ingest.terminal_unavailable(pending))
            self.assertTrue(ingest.receipt_complete(state[available['video_id']], available, args.remote))
            self.assertEqual(selections, [self.row['url'], available['url'], self.row['url']])
            self.assertEqual(transfer.call_count, 2 if available_on_revisit else 1)
            self.assertEqual(drive.copy_batch.call_count, 2 if available_on_revisit else 1)

    def test_future_premiere_stays_pending_after_one_late_revisit(self):
        self.premiere_run(available_on_revisit=False)

    def test_premiere_available_after_other_channel_finishes_is_archived(self):
        self.premiere_run(available_on_revisit=True)

    def test_no_formats_defers_one_item_while_other_channel_archives(self):
        self.premiere_run(available_on_revisit=False, failure_kind='no_formats')

    def test_format_available_after_other_audio_finishes_is_archived(self):
        self.premiere_run(available_on_revisit=True, failure_kind='no_formats')

    def test_no_formats_never_overrides_access_blocks(self):
        for error, expected in [('HTTP Error 403: Forbidden', 'forbidden'),
                                ('HTTP Error 429: Too Many Requests', 'rate_limited')]:
            self.assertEqual(self.classify(error + '\nRequested format is not available'), expected)


if __name__ == '__main__':
    unittest.main()
