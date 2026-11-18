"""Timeline grain, calendar quality, provenance, reconciliation and safe export."""
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import dataset_timeline as timeline


def row(video='abcdefghijk', channel='creator', rank=0, date='20261031', **changes):
    value = {'video_id': video, 'channel_dir': channel, 'listing_rank': str(rank),
             'source_channel_name': 'Creator ' + channel, 'title': 'Public title',
             'upload_date_approx': date}
    value.update(changes)
    return value


def overlay(video='abcdefghijk', date='2026-11-01', **changes):
    item = {'video_id': video, 'upload_date': date, 'provenance': 'saved_youtube_metadata',
            'source_sha256': 'a' * 64}
    item.update(changes)
    return {'schema_version': 1, 'items': [item]}


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('Popen forbidden')))

    def test_exact_estimate_and_unknown_stay_distinct(self):
        data = timeline.build_timeline([row(), row('lmnopqrstuv', rank=1, date='20260228'),
                                        row('wxyzABCDEFG', channel='other', date='')], overlay())
        self.assertEqual({'exact': 1, 'estimated': 1, 'unknown': 1}, data['summary']['date_quality_counts'])
        first = data['records'][0]
        self.assertEqual('2026-11-01', first['upload_date'])
        self.assertEqual('2026-10-31', first['original_estimated_date'])
        self.assertTrue(first['estimate_differs_from_exact'])
        self.assertEqual('saved_youtube_metadata', first['exact_date_provenance']['kind'])
        self.assertIsNone(data['records'][2]['upload_date'])
        self.assertIsNone(data['summary']['saved_audio_count'])

    def test_overlay_can_resolve_unknown_without_inventing_estimate(self):
        data = timeline.build_timeline([row(date='')], overlay(date='20260228'))
        record = data['records'][0]
        self.assertEqual('2026-02-28', record['upload_date'])
        self.assertEqual('exact', record['date_quality'])
        self.assertIsNone(record['original_estimated_date'])
        self.assertFalse(record['estimate_differs_from_exact'])

    def test_invalid_partial_and_impossible_dates_rejected(self):
        for date in ['20260229', '2026-02-30', '2026-11', 'yesterday', 20261101]:
            with self.subTest(date=date), self.assertRaises(timeline.TimelineError):
                timeline.build_timeline([row(date=date)])
        with self.assertRaises(timeline.TimelineError):
            timeline.build_timeline([row()], overlay(date=''))
        self.assertEqual('2024-02-29', timeline.calendar_date('20240229', 'day'))

    def test_overlay_membership_conflict_and_provenance_are_validated(self):
        for value in [overlay(video='lmnopqrstuv'), overlay(provenance='C:/private/raw.json'),
                      overlay(source_sha256='not-a-hash')]:
            with self.assertRaises(timeline.TimelineError):
                timeline.build_timeline([row()], value)
        conflict = overlay()
        conflict['items'].append(dict(conflict['items'][0], upload_date='2026-11-02'))
        with self.assertRaisesRegex(timeline.TimelineError, 'conflicting'):
            timeline.build_timeline([row()], conflict)
        identical = overlay(); identical['items'] *= 2
        self.assertEqual(1, timeline.build_timeline([row()], identical)['summary']['date_quality_counts']['exact'])

    def test_unique_video_creator_rank_and_sample_boundary(self):
        bad_sets = [[row(), row()], [row(), row('lmnopqrstuv')], [row(rank=20)],
                    [row(video='bad')], [row(channel='../private')], [row(rank=True)],
                    [row(), row('lmnopqrstuv', rank=1, source_channel_name='Changed name')]]
        for values in bad_sets:
            with self.subTest(values=values), self.assertRaises(timeline.TimelineError):
                timeline.build_timeline(values)

    def test_month_creator_and_audio_totals_reconcile(self):
        rows = [row(), row('lmnopqrstuv', rank=1, date='20261115'),
                row('wxyzABCDEFG', channel='other', date='')]
        data = timeline.build_timeline(rows, overlay(), {'abcdefghijk', 'wxyzABCDEFG'})
        self.assertEqual(3, data['summary']['total_records'])
        self.assertEqual(2, data['summary']['creator_count'])
        self.assertEqual(2, data['summary']['saved_audio_count'])
        for group in ['monthly', 'creators']:
            self.assertEqual(3, sum(item['record_count'] for item in data[group]))
            self.assertEqual(2, sum(item['saved_audio_count'] for item in data[group]))
            for quality in timeline.QUALITIES:
                self.assertEqual(data['summary']['date_quality_counts'][quality],
                                 sum(item[quality + '_count'] for item in data[group]))
        creator = next(item for item in data['creators'] if item['channel_dir'] == 'creator')
        self.assertEqual('2026-11-01', creator['earliest_upload_date'])
        self.assertEqual('2026-11-15', creator['latest_upload_date'])
        self.assertEqual(14, creator['span_days'])
        self.assertEqual('unknown', data['monthly'][-1]['month'])

    def test_all_unknown_has_no_fabricated_range(self):
        data = timeline.build_timeline([row(date='')])
        self.assertIsNone(data['summary']['earliest_upload_date'])
        self.assertIsNone(data['summary']['latest_upload_date'])
        self.assertIsNone(data['creators'][0]['span_days'])
        self.assertEqual(1, data['monthly'][0]['unknown_count'])

    def test_private_inputs_are_not_exported(self):
        source = row(private_path='C:/PRIVATE/raw.json', drive_id='PRIVATE-ID', transcript='PRIVATE-TEXT')
        exact = overlay(evidence_path='C:/PRIVATE/cache.json', token='PRIVATE-TOKEN')
        data = timeline.build_timeline([source], exact)
        exported = json.dumps(data)
        self.assertNotIn('PRIVATE', exported)
        self.assertNotIn('evidence_path', exported)
        self.assertNotIn('drive_id', exported)

    def test_csv_formula_neutralization_and_roundtrip(self):
        source = row(video='-bcdefghijk', source_channel_name='=Creator', title='  @Title')
        data = timeline.build_timeline([source])
        with tempfile.TemporaryDirectory() as temp:
            timeline.write_outputs(data, temp)
            text = (Path(temp) / 'dataset_timeline_videos.csv').read_text(encoding='utf-8-sig')
            exported = next(csv.DictReader(io.StringIO(text)))
        self.assertEqual("'-bcdefghijk", exported['video_id'])
        self.assertEqual("'=Creator", exported['channel_name'])
        self.assertEqual("'  @Title", exported['title'])
        for value in ['=x', '+x', '-x', '@x', '\tx', '\rx', '\nx']:
            self.assertTrue(timeline.spreadsheet_cell(value).startswith("'"))

    def test_audio_snapshot_is_subset_and_supports_safe_id_escape(self):
        rows = [row(video='-bcdefghijk')]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'coverage.csv'
            path.write_text("video_id,channel_dir,audio_source\n'-bcdefghijk,creator,publisher_edition\n", encoding='utf-8')
            ids = timeline.load_audio_ids(path, rows)
            self.assertEqual({'-bcdefghijk'}, ids)
            path.write_text('video_id,channel_dir,audio_source\nabcdefghijk,creator,youtube_native\n', encoding='utf-8')
            with self.assertRaises(timeline.TimelineError): timeline.load_audio_ids(path, rows)

    def test_html_embeds_safe_json_and_local_bundle_once(self):
        data = timeline.build_timeline([row(title='</script><img>__PLOTLY_JS__\u2028')])
        template = '<script>__PLOTLY_JS__</script><script>const DATA=__TIMELINE_DATA__;</script>'
        html = timeline.render_html(data, template, 'var x="</ScRiPt>";')
        self.assertIn('<\\/script>', html)
        self.assertIn('\\u003c/script>', html)
        self.assertIn('\\u2028', html)
        self.assertEqual(1, html.count('var x='))
        self.assertIn('__PLOTLY_JS__', html)  # A marker in data must not be expanded recursively.
        self.assertNotIn('</script><img>', html)
        with self.assertRaises(timeline.TimelineError): timeline.render_html(data, '__TIMELINE_DATA__', 'bundle')

    def test_cli_writes_reconciled_three_data_exports_without_rendering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); queue = root / 'private-queue.csv'; out = root / 'output'
            values = [row(), row('lmnopqrstuv', rank=1, date='')]
            with queue.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(values[0])); writer.writeheader(); writer.writerows(values)
            data = timeline.main(['--queue', str(queue), '--out-dir', str(out),
                                  '--expected-videos', '2', '--expected-creators', '1'])
            self.assertEqual(2, data['summary']['total_records'])
            self.assertEqual(3, len(list(out.iterdir())))
            public = json.loads((out / 'dataset_timeline.json').read_text(encoding='utf-8'))
            self.assertNotIn(str(root), json.dumps(public))
            with (out / 'dataset_timeline_monthly.csv').open(encoding='utf-8-sig', newline='') as stream:
                monthly = list(csv.DictReader(stream))
            self.assertEqual(2, sum(int(item['record_count']) for item in monthly))

    def test_source_hash_binds_the_parsed_snapshot_during_local_refresh(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); queue = root / 'queue.csv'; out = root / 'output'
            with queue.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(row()))
                writer.writeheader(); writer.writerow(row())
            original = queue.read_bytes()
            build = timeline.build_timeline
            def refresh_after_parse(*args, **kwargs):
                queue.write_text('newer snapshot', encoding='utf-8')
                return build(*args, **kwargs)
            with patch.object(timeline, 'build_timeline', side_effect=refresh_after_parse):
                data = timeline.main(['--queue', str(queue), '--out-dir', str(out)])
            self.assertEqual('abcdefghijk', data['records'][0]['video_id'])
            self.assertEqual(hashlib.sha256(original).hexdigest(), data['source']['selection_csv_sha256'])


if __name__ == '__main__':
    unittest.main()
