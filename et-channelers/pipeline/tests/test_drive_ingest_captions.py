"""Offline caption ownership, disk accounting, cooldown and independent receipt checks."""
import hashlib
import json
import sys
import threading
import time
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import drive_ingest as ingest
import youtube_captions as captions
from test_drive_ingest_stages import StageFixture


class CaptionIntegrationTests(StageFixture):
    raw = b'{"events":[{"tStartMs":1000,"dDurationMs":2000,"segs":[{"utf8":"Hello world"}]}]}'

    def setup_caption(self):
        item = self.item()
        item.row['url'] = f"https://www.youtube.com/watch?v={item.row['video_id']}"
        args = self.args(collect_captions=True, caption_state={}, ytdlp='unused', timeout=30)
        budget = ingest.Budget(self.root, 100_000_000, 0, 0, cached=True)
        ingest._ROOT_BUDGETS[self.root.resolve()] = budget
        info = {'id': item.row['video_id'], 'subtitles': {'en': [{'ext': 'json3', 'name': 'English',
                'url': 'https://www.youtube.com/api/timedtext?v=' + item.row['video_id'] + '&lang=en&fmt=json3&sig=private'}]},
                'automatic_captions': {}}
        return args, item, budget, info

    def fake_fetch(self, spec, output, *, budget, **unused):
        budget.admit_size(Path(output.name), len(self.raw))
        budget.write(output, self.raw)
        return {'bytes': len(self.raw), 'md5': hashlib.md5(self.raw).hexdigest(),
                'sha256': hashlib.sha256(self.raw).hexdigest(), 'content_type': 'application/json'}

    def prepared(self):
        args, item, budget, info = self.setup_caption()
        with patch.object(captions, 'fetch_track', side_effect=self.fake_fetch), patch.object(ingest, 'extract_audio') as extract:
            item.captions = ingest.prepare_captions(args, item.row, item.record, budget, Mock(), threading.Event(), info)
            extract.assert_not_called()
        return args, item, budget

    def proof(self, bundle):
        path = ingest.remote_relative(self.args().remote, bundle['remote'])
        return {'Path': path, 'ID': 'caption-object', 'Size': bundle['bytes'], 'Hashes': {'MD5': bundle['md5']}}

    def test_reuses_info_and_bundles_raw_timing_text_provenance_with_exact_budget(self):
        args, item, budget = self.prepared()
        self.assertEqual(item.captions['status'], 'ready')
        bundle = item.captions['tracks'][0]['bundle']
        with zipfile.ZipFile(self.root / bundle['path']) as archive:
            self.assertEqual(set(archive.namelist()), {'raw.json3', 'segments.json', 'transcript.txt', 'provenance.json'})
            self.assertEqual(archive.read('raw.json3'), self.raw)
            self.assertEqual(archive.read('transcript.txt'), b'Hello world')
            self.assertEqual(json.loads(archive.read('segments.json'))['segments'][0]['start'], 1)
            self.assertNotIn('private', archive.read('provenance.json').decode())
        self.assertEqual(budget.usage(), ingest.tree_bytes(self.root))
        self.assertFalse(list(self.root.rglob('*.raw.part')))
        self.assertNotIn('https://', json.dumps(item.captions))

    def test_caption_hash_and_id_verified_before_zip_deletion(self):
        args, item, budget = self.prepared()
        bundle = item.captions['tracks'][0]['bundle']
        drive = Mock()
        relative = ingest.remote_relative(args.remote, bundle['remote'])
        drive.stat_batch.return_value = {relative: self.proof(bundle)}
        self.assertTrue(ingest.upload_captions(args, [item], drive, threading.Event()))
        drive.copy_batch.assert_called_once()
        drive.stat_batch.assert_called_once()
        self.assertFalse((self.root / bundle['path']).exists())
        self.assertTrue(ingest.caption_receipt_complete(item.captions, item.row, args.remote))
        self.assertEqual(budget.usage(), ingest.tree_bytes(self.root))

    def test_successful_caption_retry_clears_stale_drive_failure(self):
        args, item, _ = self.prepared()
        item.captions.update(status='pending', error_class='drive_auth', error='Earlier auth failure')
        bundle = item.captions['tracks'][0]['bundle']
        drive = Mock()
        drive.stat_batch.return_value = {ingest.remote_relative(args.remote, bundle['remote']): self.proof(bundle)}
        self.assertTrue(ingest.upload_captions(args, [item], drive, threading.Event()))
        self.assertTrue(ingest.caption_receipt_complete(item.captions, item.row, args.remote))
        self.assertNotIn('error_class', item.captions)
        self.assertNotIn('error', item.captions)

    def test_bad_caption_proof_keeps_zip_after_audio_pair_is_safely_saved(self):
        args, item, _ = self.prepared()
        drive = self.proof_drive([item])
        audio_proofs = drive.stat_batch.return_value
        bundle = item.captions['tracks'][0]['bundle']
        relative = ingest.remote_relative(args.remote, bundle['remote'])
        bad = dict(self.proof(bundle), ID='')
        drive.stat_batch.side_effect = [audio_proofs, {relative: bad}]
        result = ingest.upload_batch(args, [item], drive, self.state, threading.Event())[0]
        self.assertEqual(result.status, 'deleted')
        self.assertTrue(ingest.receipt_complete(result.record, item.row, args.remote))
        self.assertTrue((self.root / bundle['path']).exists())
        self.assertEqual(item.captions['status'], 'pending')

    def test_caption_403_stops_fetching_but_completed_audio_still_queues(self):
        args, item, budget, info = self.setup_caption()
        stop = threading.Event()
        with patch.object(ingest, 'extract_audio', return_value=info), patch.object(captions, 'fetch_track',
                side_effect=captions.CaptionError('forbidden')):
            result = ingest.ingest_one(args, item.row, budget, Mock(), stop, Mock(), self.state,
                                       item.record, stage_only=True)
        self.assertEqual(result.status, 'ready')
        self.assertTrue(stop.is_set())
        self.assertEqual(result.captions['error_class'], 'forbidden')
        self.assertEqual(result.captions['source_error_class'], 'forbidden')
        self.assertGreater(result.captions['retry_not_before_epoch'], time.time())
        self.assertEqual(result.record['status'], 'queued_upload')
        drive = self.proof_drive([result])
        uploaded = ingest.upload_batch(args, [result], drive, self.state, stop)[0]
        self.assertTrue(ingest.receipt_complete(uploaded.record, item.row, args.remote))
        self.assertEqual(uploaded.captions['status'], 'pending')

    def test_caption_only_backfill_never_fetches_audio_or_checks_old_remote_pair(self):
        args, item, budget, info = self.setup_caption()
        item.record.update(status='deleted', drive_id='old-audio')
        item.record['metadata']['drive_id'] = 'old-info'
        for record in (item.record, item.record['metadata']):
            ingest.remove_local(self.root / record['path'])
        with patch.object(ingest, 'extract_audio', return_value=info) as extract, \
                patch.object(ingest, 'stream_audio') as stream, patch.object(captions, 'fetch_track', side_effect=self.fake_fetch):
            result = ingest.ingest_one(args, item.row, budget, Mock(), threading.Event(), Mock(), self.state,
                                       item.record, stage_only=True)
        extract.assert_called_once_with(args, item.row, metadata_only=True)
        stream.assert_not_called()
        self.assertTrue(result.caption_only)
        bundle = result.captions['tracks'][0]['bundle']
        drive = Mock()
        drive.stat_batch.return_value = {ingest.remote_relative(args.remote, bundle['remote']): self.proof(bundle)}
        out = ingest.upload_batch(args, [result], drive, self.state, threading.Event())[0]
        self.assertTrue(ingest.receipt_complete(out.record, item.row, args.remote))
        drive.stat.assert_not_called()
        self.assertEqual(len(drive.stat_batch.call_args.args[1]), 1)
        self.assertFalse(self.state.exists())

    def test_ready_caption_resume_reuses_exact_zip_without_new_extraction(self):
        args, item, budget = self.prepared()
        with patch.object(ingest, 'extract_audio') as extract, patch.object(captions, 'fetch_track') as fetch:
            restored = ingest.prepare_captions(args, item.row, item.record, budget, Mock(), threading.Event())
        extract.assert_not_called()
        fetch.assert_not_called()
        self.assertEqual(restored['tracks'][0]['bundle'], item.captions['tracks'][0]['bundle'])

    def test_verified_receipt_precedes_delete_and_recovers_without_refetch(self):
        args, item, budget = self.prepared()
        bundle = item.captions['tracks'][0]['bundle']
        relative = ingest.remote_relative(args.remote, bundle['remote'])
        drive = Mock()
        drive.stat_batch.return_value = {relative: self.proof(bundle)}
        original = ingest.remove_local

        def fail_zip(path, **options):
            if path.suffix == '.zip':
                raise OSError('simulated deletion interruption')
            return original(path, **options)

        with patch.object(ingest, 'remove_local', side_effect=fail_zip), self.assertRaises(OSError):
            ingest.upload_captions(args, [item], drive, threading.Event())
        saved = ingest.load_state(self.root / 'sync/drive_caption_manifest.jsonl')[item.row['video_id']]
        self.assertEqual(saved['tracks'][0]['status'], 'verified')
        self.assertEqual(saved['tracks'][0]['bundle']['drive_id'], 'caption-object')
        ingest.remove_local(self.root / bundle['path'])  # crash after actual unlink, before deleted append
        args.caption_state[item.row['video_id']] = saved
        with patch.object(ingest, 'extract_audio') as extract, patch.object(captions, 'fetch_track') as fetch:
            item.captions = ingest.prepare_captions(args, item.row, item.record, budget, Mock(), threading.Event())
        extract.assert_not_called()
        fetch.assert_not_called()
        drive.reset_mock()
        self.assertTrue(ingest.upload_captions(args, [item], drive, threading.Event()))
        drive.copy_batch.assert_not_called()
        self.assertTrue(ingest.caption_receipt_complete(item.captions, item.row, args.remote))

    def test_partial_caption403_preserves_and_uploads_completed_track(self):
        args, item, budget, info = self.setup_caption()
        info['subtitles']['en-GB'] = [dict(info['subtitles']['en'][0],
            url=info['subtitles']['en'][0]['url'].replace('lang=en&', 'lang=en-GB&'))]
        calls = 0

        def fetch(*values, **options):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise captions.CaptionError('forbidden')
            return self.fake_fetch(*values, **options)

        stop = threading.Event()
        with patch.object(captions, 'fetch_track', side_effect=fetch):
            item.captions = ingest.prepare_captions(args, item.row, item.record, budget, Mock(), stop, info)
        self.assertTrue(stop.is_set())
        self.assertEqual(len(item.captions['tracks']), 2)
        ready = [track for track in item.captions['tracks'] if track.get('bundle')]
        self.assertEqual(len(ready), 1)
        bundle = ready[0]['bundle']
        drive = Mock()
        drive.stat_batch.return_value = {ingest.remote_relative(args.remote, bundle['remote']): self.proof(bundle)}
        self.assertTrue(ingest.upload_captions(args, [item], drive, stop))
        self.assertEqual(item.captions['status'], 'pending')
        self.assertEqual(ready[0]['status'], 'deleted')
        self.assertFalse(ingest.caption_receipt_complete(item.captions, item.row, args.remote))

    def test_caption_source_deadline_survives_later_drive_error(self):
        args, item, _ = self.prepared()
        deadline = time.time() + 86400
        item.captions.update(status='pending', error_class='forbidden', source_error_class='forbidden',
                             retry_not_before_epoch=deadline)
        drive = Mock()
        drive.copy_batch.side_effect = ingest.IngestError('drive_rate_limited', 'Drive is resting')
        self.assertFalse(ingest.upload_captions(args, [item], drive, threading.Event()))
        latest = ingest.load_state(self.root / 'sync/drive_caption_manifest.jsonl')[item.row['video_id']]
        self.assertEqual(latest['error_class'], 'drive_rate_limited')
        self.assertEqual(latest['source_error_class'], 'forbidden')
        self.assertEqual(latest['retry_not_before_epoch'], deadline)

    def test_caption_cooldown_blocks_new_audio_requests(self):
        args, item, _, _ = self.setup_caption()
        for record in (item.record, item.record['metadata']):
            ingest.remove_local(self.root / record['path'])
        ingest.journal(self.root / 'sync/drive_caption_manifest.jsonl',
                       {'video_id': item.row['video_id'], 'status': 'pending', 'error_class': 'forbidden',
                        'retry_not_before_epoch': time.time() + 1000})
        with patch.object(ingest, 'Rclone'), patch.object(ingest, 'ingest_one') as source:
            self.assertEqual(ingest.run(args, [item.row]), 3)
        source.assert_not_called()

    def test_final_item_caption403_drains_audio_and_returns_pending_exit(self):
        args, item, _, info = self.setup_caption()
        ingest.journal(self.state, item.record)
        drive = self.proof_drive([item])
        with patch.object(ingest, 'Rclone', return_value=drive), \
                patch.object(ingest, 'extract_audio', return_value=info), \
                patch.object(captions, 'fetch_track', side_effect=captions.CaptionError('forbidden')):
            self.assertEqual(ingest.run(args, [item.row]), 3)
        done = ingest.load_state(self.state)[item.row['video_id']]
        self.assertTrue(ingest.receipt_complete(done, item.row, args.remote))
        self.assertEqual(ingest.load_state(self.root / 'sync/drive_caption_manifest.jsonl')[item.row['video_id']]['error_class'],
                         'forbidden')

    def test_caption_only_extraction_has_no_audio_selector_and_keeps_access_warning(self):
        args, item, _, _ = self.setup_caption()
        info = {'id': item.row['video_id'], 'subtitles': {}, 'automatic_captions': {}}
        tool = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(info),
                    stderr='WARNING: [youtube] Subtitles require a Subs PO token; missing token'))
        with patch.object(ingest, 'run_tool', tool):
            result = ingest.extract_audio(args, item.row, metadata_only=True)
        command = tool.call_args.args[0]
        self.assertIn('--ignore-no-formats-error', command)
        self.assertNotIn('-f', command)
        self.assertNotIn('--no-warnings', command)
        self.assertEqual(captions.select_tracks(result)['inventory_status'], 'incomplete')
        for flag in ('--simulate', '--write-subs', '--write-auto-subs'):
            self.assertIn(flag, command)
        self.assertEqual(command[command.index('--sub-langs') + 1], 'en.*')
        self.assertEqual(command[command.index('--sub-format') + 1], 'json3/vtt')

    def test_new_audio_extraction_declares_caption_intent_without_downloading_captions(self):
        args, item, _, info = self.setup_caption()
        info.update(vcodec='none', protocol='https', ext='webm', url='https://rr1.googlevideo.com/videoplayback')
        tool = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(info),
                    stderr='WARNING: [youtube] Video requires a GVS PO token'))
        with patch.object(ingest, 'run_tool', tool):
            result = ingest.extract_audio(args, item.row)
        command = tool.call_args.args[0]
        self.assertIn('--simulate', command)
        self.assertIn('-f', command)
        self.assertIn('--write-auto-subs', command)
        self.assertNotIn('_caption_access_warning', result)

    def test_zip_writer_counts_duplicate_bytes_and_respects_whole_root_limit(self):
        (self.root / 'raw').write_bytes(b'x' * 70)
        budget = ingest.Budget(self.root, 100, 0, 0, reserve=0, cached=True)
        with open(self.root / 'bundle.part', 'wb') as output:
            writer = ingest._BudgetZipWriter(output, budget)
            writer.write(b'z' * 25)
            with self.assertRaises(ingest.IngestError):
                writer.write(b'z' * 6)
        self.assertEqual(ingest.tree_bytes(self.root), 95)
        self.assertEqual(budget.usage(), 95)

    def test_cli_captions_default_and_explicit_disable(self):
        self.assertTrue(ingest.parser().parse_args(['status']).collect_captions)
        self.assertFalse(ingest.parser().parse_args(['status', '--no-captions']).collect_captions)


if __name__ == '__main__':
    unittest.main()
