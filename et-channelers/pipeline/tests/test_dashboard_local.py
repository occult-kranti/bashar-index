"""Tests for dashboard_local.py (invented fragment, no network)."""
import json
import csv
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
        self.assertNotIn('SECRET FILE', json.dumps(result))
        self.assertNotIn('supervisor_pid', json.dumps(result))

    def test_private_fields_never_enter_public_counts_and_audio_alone_is_not_a_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'jobs').mkdir()
            (root / 'sync').mkdir()
            for name in ('queue_newest20_enriched.csv', 'queue_newest50_enriched.csv', 'queue_youtube_all_merged.csv'):
                with (root / 'jobs' / name).open('w', newline='') as handle:
                    writer = csv.DictWriter(handle, fieldnames=['video_id','channel_dir','title'])
                    writer.writeheader()
                    writer.writerow({'video_id':'PRIVATE-ID-A','channel_dir':'PRIVATE-PERSON','title':'SECRET TITLE'})
                    writer.writerow({'video_id':'PRIVATE-ID-B','channel_dir':'PRIVATE-PERSON','title':'SECRET TITLE'})
            first = {'video_id':'PRIVATE-ID-A','status':'deleted','bytes':10,'drive_id':'SECRET DRIVE ID',
                     'md5':'PRIVATE HASH','sha256':'PRIVATE HASH','title':'SECRET TITLE',
                     'url':'https://private.invalid/SECRET','path':str(root),'token':'SECRET TOKEN',
                     'metadata':{'drive_id':'PRIVATE METADATA ID','md5':'PRIVATE HASH','sha256':'PRIVATE HASH'}}
            second = dict(first, video_id='PRIVATE-ID-B', metadata=None)
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps(first)+'\n'+json.dumps(second)+'\n')
            result = ingestion_status.snapshot(root, now=1800000000)
        serialized = json.dumps(result)
        for value in ('PRIVATE-ID','PRIVATE-PERSON','SECRET','PRIVATE HASH',str(root),'https://'):
            self.assertNotIn(value, serialized)
        self.assertEqual(result['scope'], 'local_youtube_collection')
        self.assertEqual(result['counts']['verified_pairs'], 1)
        self.assertEqual(result['counts']['awaiting_upload'], 1)
        self.assertEqual(result['stages'][0]['total'], 2)

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
