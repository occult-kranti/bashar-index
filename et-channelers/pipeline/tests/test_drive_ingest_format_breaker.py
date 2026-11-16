"""A systemic format failure stops dispatch without misclassifying removed videos."""
import contextlib
import io
import json
import threading
import unittest
from unittest.mock import Mock, patch

from test_drive_ingest_stages import StageFixture
import drive_ingest as ingest


class FormatBreakerTests(StageFixture):
    def rows(self, count):
        return [dict(video_id=f'{index:011d}', channel_dir=f'channel-{index}', tab='videos')
                for index in range(1, count + 1)]

    def failed(self, row):
        return ingest.IngestResult(row, dict(row, status='deferred_format', error_class='no_formats'),
                                   status='deferred_format')

    def test_three_format_failures_stop_new_dispatch_and_leave_remaining_queue(self):
        rows = self.rows(10)
        output = io.StringIO()
        with patch.object(ingest, 'Rclone', return_value=Mock()), \
                patch.object(ingest, 'ingest_one', side_effect=lambda args, row, *a, **k: self.failed(row)) as source, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(ingest.run(self.args(workers=1), rows), 3)
        self.assertEqual(source.call_count, 3)
        result = json.loads(output.getvalue().splitlines()[-1])
        self.assertEqual(result['consecutive_format_failures'], 3)
        self.assertEqual(result['pending_items'], 7)
        self.assertFalse(result['youtube_cooldown'])

    def test_caption_only_success_cannot_reset_format_failure_streak(self):
        rows = self.rows(10)

        def source(args, row, *unused, **kwargs):
            if row is rows[2]:
                return ingest.IngestResult(row, dict(row, status='deleted'), status='deleted', caption_only=True)
            return self.failed(row)

        with patch.object(ingest, 'Rclone', return_value=Mock()), \
                patch.object(ingest, 'ingest_one', side_effect=source) as worker, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(ingest.run(self.args(workers=1), rows), 3)
        self.assertEqual(worker.call_count, 4)

    def test_completed_audio_resets_streak_while_drive_upload_is_still_waiting(self):
        rows, calls = self.rows(5), []
        release_upload = threading.Event()

        def source(args, row, *unused, **kwargs):
            calls.append(row['video_id'])
            if row is rows[2]:
                return ingest.IngestResult(row, dict(row, status='queued_upload'))
            if row is rows[4]:
                release_upload.set()
                return 'downloaded'
            if calls.count(row['video_id']) > 1:
                return 'downloaded'  # one bounded late revisit after useful audio work
            return self.failed(row)

        def upload(args, items, *unused):
            release_upload.wait(2)
            return [ingest.IngestResult(item.row, item.record, status='deleted') for item in items]

        with patch.object(ingest, 'Rclone', return_value=Mock()), \
                patch.object(ingest, 'ingest_one', side_effect=source), \
                patch.object(ingest, 'upload_batch', side_effect=upload), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(ingest.run(self.args(workers=1), rows), 0)
        self.assertTrue(release_upload.is_set())
        self.assertEqual(calls[:5], [row['video_id'] for row in rows])


if __name__ == '__main__':
    unittest.main()
