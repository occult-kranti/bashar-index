"""Tests for dashboard_local.py (invented fragment, no network)."""
import json
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pipeline import dashboard_local, ingestion_status


FRAGMENT = (
    '<meta name="dash-one-writer">\n<style>.x{color:var(--color-fg)}</style>\n'
    '<div class="page"><b data-draw="g-people" data-source="totals" data-field="people" data-row="0">—</b></div>\n'
    "<script>dash.calc('totals', { inputs: ['targets'], fn: (t) => [{ people: t.length }] });</script>\n"
)


class BuildTests(unittest.TestCase):
    def test_wraps_fragment_in_a_page_with_a_host(self):
        html = dashboard_local.build(FRAGMENT, "../../plan/")
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertNotIn('dash-one-writer', html)
        self.assertIn("window.dash = {", html)
        self.assertIn('data-draw="g-people"', html)
        self.assertIn("dash.calc('totals'", html)
        self.assertIn(json.dumps("../../plan/"), html)
        self.assertIn('"bashar_channels": "bashar_host_channels"', html)
        for name in ("coverage", "sources", "targets", "contacts", "transcript_audio"):
            self.assertIn(json.dumps(name), html)
        self.assertEqual(html.count("<script"), 4)  # shared navigation, d3, host, fragment
        self.assertIn('@media (prefers-color-scheme: dark)', html)
        self.assertIn(':root[data-theme="dark"]', html)
        self.assertTrue(html.rstrip().endswith("</html>"))
        self.assertNotIn('<p class="local-note">', html)
        self.assertIn('data-page="collection"', html)
        self.assertIn("if (typeof fn === 'function') draws.set", html)

    def test_base_is_json_escaped(self):
        html = dashboard_local.build(FRAGMENT, "./da\"ta/")
        self.assertIn(json.dumps("./da\"ta/"), html)


class StatusExportTests(unittest.TestCase):
    def test_isolated_cli_exports_only_aggregates_from_an_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'private'
            (root / 'sync').mkdir(parents=True)
            (root / 'jobs').mkdir()
            (root / 'jobs/queue_newest20.csv').write_text(
                'video_id,channel_dir,title\n12345678901,PRIVATE-PERSON,SECRET TITLE\n', encoding='utf-8')
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps({
                'video_id': '12345678901', 'status': 'unavailable', 'error_class': 'unavailable',
                'title': 'SECRET TITLE', 'path': str(root), 'url': 'https://private.invalid/SECRET',
            }) + '\n', encoding='utf-8')
            output = Path(folder) / 'public/status.json'
            result = subprocess.run(
                [sys.executable, '-I', str(Path(ingestion_status.__file__).resolve()),
                 '--root', str(root), '--out', str(output)],
                cwd=folder, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            public = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(json.loads(result.stdout), public)
            self.assertEqual(public['counts']['unavailable'], 1)
            self.assertEqual(public['counts']['verified_pairs'], 0)
            self.assertEqual(public['counts']['channels'], 1)
            self.assertFalse(output.with_suffix('.json.tmp').exists())
            for private in ('SECRET', 'PRIVATE-PERSON', '12345678901', str(root), 'https://'):
                self.assertNotIn(private, json.dumps(public))

    def test_supervisor_backoff_and_full_archive_plan_are_public_aggregates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            (root / 'sync/drive_ingest_resume_state.json').write_text(json.dumps({
                'schema_version': 2, 'mode': 'RunAll', 'download_workers': 6,
                'state': 'waiting_for_drive_cooldown', 'until_epoch': 1800001200,
                'private_log': 'SECRET FILE', 'supervisor_pid': 1234}))
            result = ingestion_status.snapshot(root, now=1800000000)
        self.assertEqual(result['operation']['state'], 'cooldown')
        self.assertEqual(result['operation']['workers'], 6)
        self.assertTrue(result['operation']['full_archive_requested'])
        self.assertEqual(result['stages'][-1]['key'], 'final_archive')
        self.assertEqual(result['storage']['ceiling_bytes'], 17_000_000_000)
        self.assertNotIn('SECRET FILE', json.dumps(result))
        self.assertNotIn('supervisor_pid', json.dumps(result))

    def test_source_and_drive_cooldowns_are_typed_public_aggregates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps({
                'video_id': 'PRIVATE-ID', 'error_class': 'forbidden',
                'retry_not_before_epoch': 1800001200, 'error': 'PRIVATE ERROR'}) + '\n', encoding='utf-8')
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['state'], 'cooldown')
            self.assertEqual(result['operation']['cooldown_provider'], 'youtube')
            self.assertEqual(result['operation']['retry_after'], ingestion_status.stamp(1800001200))
            (root / 'sync/drive_ingest_cooldown.json').write_text(
                json.dumps({'until_epoch': 1800001800}), encoding='utf-8')
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['cooldown_provider'], 'both')
            self.assertEqual(result['operation']['retry_after'], ingestion_status.stamp(1800001800))
            self.assertNotIn('PRIVATE', json.dumps(result))

    def test_source_backoff_and_budget_from_supervisor_are_allowlisted(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            state = {'schema_version': 2, 'state': 'waiting_for_youtube_cooldown',
                     'cooldown_provider': 'youtube', 'until_epoch': 1800001200,
                     'private_root_ceiling_bytes': 16_000_000_000}
            target = root / 'sync/drive_ingest_resume_state.json'
            target.write_text(json.dumps(state), encoding='utf-8')
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['state'], 'cooldown')
            self.assertEqual(result['operation']['cooldown_provider'], 'youtube')
            self.assertEqual(result['storage']['ceiling_bytes'], 16_000_000_000)
            state.update(state='retry_budget_exhausted', private_root_ceiling_bytes=19_000_000_000,
                         cooldown_provider='PRIVATE VALUE')
            target.write_text(json.dumps(state), encoding='utf-8')
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['state'], 'paused')
            self.assertEqual(result['storage']['ceiling_bytes'], 17_000_000_000)
            self.assertNotIn('PRIVATE VALUE', json.dumps(result))

    def test_private_fields_never_enter_public_counts_and_audio_alone_is_not_a_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'jobs').mkdir()
            (root / 'sync').mkdir()
            for name in ('queue_newest20_enriched.csv', 'queue_newest50_enriched.csv', 'queue_youtube_all_merged.csv'):
                with (root / 'jobs' / name).open('w', newline='') as handle:
                    writer = csv.DictWriter(handle, fieldnames=['video_id','channel_dir','title'])
                    writer.writeheader()
                    writer.writerow({'video_id':'PRIVATEidA1','channel_dir':'PRIVATE-PERSON','title':'SECRET TITLE'})
                    writer.writerow({'video_id':'PRIVATEidB1','channel_dir':'PRIVATE-PERSON','title':'SECRET TITLE'})
            destination = 'etdrive:04 Audio/PRIVATE-PERSON/Videos/PRIVATEidA1'
            first = {'video_id':'PRIVATEidA1','channel_dir':'PRIVATE-PERSON','status':'deleted','bytes':10,'drive_id':'SECRET DRIVE ID',
                     'md5':'PRIVATE HASH','sha256':'PRIVATE HASH','title':'SECRET TITLE',
                     'url':'https://private.invalid/SECRET','path':'audio/PRIVATEidA1.webm','token':'SECRET TOKEN',
                     'remote': destination+'.webm',
                     'metadata':{'drive_id':'PRIVATE METADATA ID','md5':'PRIVATE HASH','sha256':'PRIVATE HASH',
                                 'remote':destination+'.info.json'}}
            second = dict(first, video_id='PRIVATEidB1', metadata=None)
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps(first)+'\n'+json.dumps(second)+'\n')
            result = ingestion_status.snapshot(root, now=1800000000)
        serialized = json.dumps(result)
        for value in ('PRIVATEid','PRIVATE-PERSON','SECRET','PRIVATE HASH',str(root),'https://'):
            self.assertNotIn(value, serialized)
        self.assertEqual(result['scope'], 'local_youtube_collection')
        self.assertEqual(result['counts']['verified_pairs'], 1)
        self.assertEqual(result['counts']['awaiting_upload'], 1)
        self.assertEqual(result['stages'][0]['total'], 2)

    def test_caption_counts_require_current_policy_and_exact_remote_proofs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            def audio(video):
                remote = f'etdrive:04 Audio/PRIVATE-PERSON/Videos/{video}'
                return {'video_id':video, 'channel_dir':'PRIVATE-PERSON', 'status':'deleted',
                        'path':f'audio/{video}.webm', 'remote':remote+'.webm', 'bytes':10,
                        'drive_id':'SECRET AUDIO ID', 'md5':'a'*32, 'sha256':'b'*64,
                        'metadata':{'drive_id':'SECRET META ID','md5':'c'*32,'sha256':'d'*64,
                                    'remote':remote+'.info.json'}}
            def caption(video, status='deleted', tracks=1, **changes):
                value = {'video_id':video,'channel_dir':'PRIVATE-PERSON', 'status':status,
                         'policy':ingestion_status.CAPTION_POLICY, 'captured_at':'2026-11-16T00:00:00Z',
                         'unresolved':[], 'text':'SECRET CAPTION TEXT', 'tracks':[]}
                for n in range(tracks):
                    identity = f'published.en.{n}'
                    value['tracks'].append({'track_id':identity,'language':'en','kind':'published',
                        'machine_translated':False,'status':'deleted','bundle':{'bytes':20,'drive_id':'SECRET TRACK ID',
                            'md5':'e'*32,'sha256':'f'*64,
                            'remote':f'etdrive:04 Audio/PRIVATE-PERSON/Videos/{video}.captions.{identity}.zip'}})
                value.update(changes)
                return value
            a, b, c, d, e, f, g = [f'PRIVATEid{n}1' for n in 'ABCDEFG']
            audio_rows = [audio(video) for video in (a, b, e)]
            rows = [caption(a, tracks=2), caption(b, status='pending', tracks=2),
                    caption(c, status='none', tracks=0), caption(d, status='none', tracks=0, unresolved=['access']),
                    caption(f), caption(g, policy='outdated')]
            rows[1]['tracks'][1]['status'] = 'ready'
            rows[4]['tracks'][0]['bundle']['remote'] = 'etdrive:WRONG/PRIVATE/file.zip'
            for name, records in [('drive_ingest_manifest.jsonl',audio_rows),('drive_caption_manifest.jsonl',rows)]:
                (root / 'sync' / name).write_text(''.join(json.dumps(row)+'\n' for row in records), encoding='utf-8')
            result = ingestion_status.snapshot(root, now=1800000000)
        self.assertEqual(result['counts']['verified_pairs'], 3)
        self.assertEqual(result['counts']['caption_verified_videos'], 1)
        self.assertEqual(result['counts']['caption_verified_tracks'], 3)
        self.assertEqual(result['counts']['caption_none_english'], 1)
        self.assertEqual(result['counts']['caption_pending_videos'], 5)
        for private in ('PRIVATE', 'SECRET', 'etdrive:', 'WRONG', str(root)):
            self.assertNotIn(private, json.dumps(result))

    def test_caption_deadline_is_independent_of_resolved_audio_and_latest_per_lane(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps({
                'video_id':'PRIVATEidA1','status':'deleted'})+'\n', encoding='utf-8')
            rows = [{'video_id':'PRIVATEidA1','error_class':'forbidden','retry_not_before_epoch':1800009000},
                    {'video_id':'PRIVATEidA1','status':'pending','error_class':'drive_rate_limited',
                     'source_error_class':'rate_limited',
                     'retry_not_before_epoch':1800001200,'error':'SECRET URL'}]
            target = root / 'sync/drive_caption_manifest.jsonl'
            target.write_text(''.join(json.dumps(row)+'\n' for row in rows), encoding='utf-8-sig')
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertIsNone(result['operation']['cooldown_provider'])
            self.assertIsNone(result['operation']['retry_after'])
            self.assertEqual(result['operation']['state'], 'ready')
            self.assertEqual(result['operation']['caption_state'], 'cooldown')
            self.assertEqual(result['operation']['caption_retry_after'], ingestion_status.stamp(1800001200))
            (root / 'sync/drive_ingest_resume_state.json').write_text(json.dumps({
                'schema_version':2, 'state':'waiting_for_caption_cooldown', 'await_caption_backfill':True,
                'until_epoch':1800001200, 'cooldown_provider':'captions'}), encoding='utf-8')
            waiting = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(waiting['operation']['state'], 'ready')
            self.assertIsNone(waiting['operation']['retry_after'])
            (root / 'sync/drive_ingest_resume_state.json').write_text(json.dumps({
                'schema_version':2, 'state':'waiting_for_youtube_cooldown', 'source_until_epoch':1800001200,
                'until_epoch':1800001201, 'cooldown_provider':'youtube'}), encoding='utf-8')
            migrated = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(migrated['operation']['state'], 'ready')
            self.assertIsNone(migrated['operation']['retry_after'])
            self.assertNotIn('SECRET', json.dumps(result))
            (root / 'sync/drive_ingest_resume_state.json').unlink()
            with target.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps({'video_id':'PRIVATEidA1','status':'deleted'})+'\n')
            self.assertNotEqual(ingestion_status.snapshot(root, now=1800000000)['operation']['state'], 'cooldown')

    def test_cooldown_and_stop_are_reported_without_claiming_a_running_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            (root / 'sync/drive_ingest_cooldown.json').write_text(json.dumps({'until_epoch':1800000600,'reason':'PRIVATE ERROR'}))
            self.assertEqual(ingestion_status.snapshot(root, now=1800000000)['operation']['state'], 'cooldown')
            (root / 'sync/STOP_DRIVE_INGEST').touch()
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['state'], 'paused')
            self.assertNotIn('PRIVATE ERROR', json.dumps(result))


if __name__ == "__main__":
    unittest.main()
