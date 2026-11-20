"""Invented date evidence only; no source, media or real selection reads."""
from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from pipeline import collection_metadata_timeline as timeline
from pipeline.tests.test_collection_failure_dashboard import Markup


def fixture():
    definitions=[
        ('publication','1985-03-04','1985-03-04','1985-03-04','1985','1985-03'),
        ('availability','2024-02-09',None,None,'2024','2024-02'),
        ('upload','2025-10-10','2025-10-10','2025-10-10','2025','2025-10'),
        ('relative',None,'2026-06-01','2026-06-30','2026','2026-06'),
        ('relative',None,'2026-08-01','2026-09-03','2026',None),
        ('relative',None,'2025-12-20','2026-01-10',None,None),
        ('unknown',None,None,None,None,None)]
    rows=[]
    for i,(method,exact,low,high,year,month) in enumerate(definitions):
        video='record'+str(i).zfill(5)
        rows.append(dict(video_id=video,channel_dir='alpha' if i<4 else 'beta',creator='Alpha' if i<4 else 'Beta',
            title='Synthetic recording '+str(i),url='https://www.youtube.com/watch?v='+video,rank=i+1,
            date_method=method,method_detail='Literal fixture evidence, not a guessed date.',
            source_url='https://www.youtube.com/watch?v='+video,exact_day=exact,date_min=low,date_max=high,
            year_bin=year,month_bin=month,relative_label='A relative age' if method=='relative' else None,
            observed_at='2026-11-19T23:00:00Z',publication_day=exact if method=='publication' else None,
            availability_day=exact if method=='availability' else None,upload_day=exact if method=='upload' else None,
            evidence_sha256='b'*64 if method!='unknown' else None))
    return dict(scope='latest20plus_public_regular_dates',generated_at='2026-11-19T23:30:00Z',
        selection_sha256='a'*64,records=rows,calibration={'compared':3,'within_interval':2})


class MetadataTimelineTests(unittest.TestCase):
    def test_whole_window_year_and_month_counts_never_choose_midpoints(self):
        rows=timeline._validated(fixture())['records']
        year=timeline.aggregate(rows,'year');month=timeline.aggregate(rows,'month')
        self.assertEqual((year['selected'],year['placed'],year['ambiguous'],year['unknown']),(7,5,1,1))
        self.assertEqual((month['selected'],month['placed'],month['ambiguous'],month['unknown']),(7,4,2,1))
        self.assertEqual(sum(x['total'] for x in year['bins']),5)
        self.assertEqual(next(x for x in year['bins'] if x['period']=='2026')['relative'],2)
        self.assertFalse(any(x['period']=='2026-09' for x in month['bins']))

    def test_static_chart_and_all_rows_sources_methods_exist_without_js(self):
        report=fixture();before=deepcopy(report);html=timeline.render(report);doc=Markup(html)
        self.assertEqual(report,before)
        rows=[a for tag,a in doc.tags if tag=='tr' and 'data-video' in a]
        self.assertEqual(len(rows),7);self.assertTrue(all('hidden' not in r for r in rows))
        text=' '.join(doc.text)
        for word in ('1985','2025-12-20','2026-01-10','Publication date','Availability metadata','Upload fallback','Relative interval','Unknown','Month: ambiguous'):
            self.assertIn(word,text)
        links=[a['href'] for tag,a in doc.tags if tag=='a']
        self.assertIn('recording-dates.csv',links)
        self.assertEqual(sum(u.startswith('https://www.youtube.com/watch?v=') for u in links),14)
        self.assertIn('no midpoint',html.lower());self.assertIn('2 of 3 date-stamped comparisons',html)
        self.assertTrue(any(tag=='ol' and a.get('class')=='bin-list' for tag,a in doc.tags))

    def test_unknown_only_does_not_fabricate_a_calendar_bin(self):
        report=fixture();report['records']=report['records'][-1:]
        html=timeline.render(report)
        self.assertIn('No records can be placed in a calendar bin',html)
        self.assertIn('1 unknown',html)
        self.assertNotIn('class="bin"',html)

    def test_bad_interval_bins_exact_dates_and_identity_fail_closed(self):
        changes=[lambda d:d['records'][5].update(year_bin='2026'),
            lambda d:d['records'][4].update(month_bin='2026-08'),
            lambda d:d['records'][3].update(exact_day='2026-06-15'),
            lambda d:d['records'][0].update(exact_day=None),
            lambda d:d['records'][0].update(date_min='1985-03-05'),
            lambda d:d['records'][6].update(date_min='2026-01-01',date_max='2026-01-02'),
            lambda d:d['records'][1].update(video_id=d['records'][0]['video_id']),
            lambda d:d['records'][0].update(url='https://www.youtube.com/watch?v=wrong123456'),
            lambda d:d['records'][1].update(creator='Wrong owner'),
            lambda d:d.update(selection_sha256='invalid'),lambda d:d.update(calibration={'compared':1,'within_interval':2})]
        for mutate in changes:
            report=fixture();mutate(report)
            with self.subTest(report=report),self.assertRaises(ValueError):timeline.render(report)

    def test_privacy_whitelist_url_policy_and_display_escaping(self):
        report=fixture();report['private_dump']='SECRET-PRIVATE';report['records'][0]['headers']={'Cookie':'SECRET-COOKIE'}
        report['records'][0]['title']='</script><img src=x onerror=bad()> & "Unicode café"'
        html=timeline.render(report);doc=Markup(html)
        self.assertNotIn('SECRET-',html)
        self.assertEqual(sum(tag=='script' for tag,_ in doc.tags),1)
        self.assertFalse(any(tag=='img' or any(k.startswith('on') for k in a) for tag,a in doc.tags))
        self.assertIn('</script><img src=x onerror=bad()> & "Unicode café"',' '.join(doc.text))
        for url in ('file:///private/evidence','javascript:bad()','https://cdn.googlevideo.com/videoplayback?sig=private','https://example.com/?token=secret'):
            report=fixture();report['records'][0]['source_url']=url
            with self.subTest(url=url),self.assertRaises(ValueError):timeline.render(report)

    def test_offline_accessible_controls_no_external_renderer_or_live_date(self):
        html=timeline.render(fixture());doc=Markup(html)
        labels={a['for'] for tag,a in doc.tags if tag=='label'}
        self.assertTrue({'search','creator','method','period'}<=labels)
        self.assertTrue(any(a.get('aria-live')=='polite' for _,a in doc.tags))
        self.assertTrue(all(a.get('scope')=='col' for tag,a in doc.tags if tag=='th'))
        self.assertTrue(any(tag=='noscript' for tag,_ in doc.tags))
        self.assertFalse(any(tag in ('iframe','link') or tag=='script' and 'src' in a for tag,a in doc.tags))
        for forbidden in ('fetch(','new Date()','Date.now(','innerHTML','Plotly'):
            self.assertNotIn(forbidden,html)
        self.assertIn('repeating-linear-gradient',html)

    def test_cli_writes_only_explicit_html_not_csv_or_date_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            temp=Path(temp);source=temp/'dates.json';target=temp/'out/timeline.html'
            source.write_text(json.dumps(fixture()),encoding='utf8');original=source.read_bytes()
            with redirect_stdout(StringIO()) as output:timeline.main(['--report',str(source),'--output',str(target)])
            self.assertEqual(json.loads(output.getvalue())['records'],7)
            self.assertIn('Publication metadata timeline',target.read_text(encoding='utf8'))
            self.assertEqual(source.read_bytes(),original);self.assertFalse((target.parent/'recording-dates.csv').exists())

    def test_daily_counts_separate_single_day_and_nonadditive_possible_intervals(self):
        report=fixture();rows=timeline._validated(report)['records']
        direct=deepcopy(rows[0]);direct.update(exact_day='2026-11-18',date_min='2026-11-18',date_max='2026-11-18')
        single=deepcopy(rows[3]);single.update(date_min='2026-11-19',date_max='2026-11-19')
        multi=deepcopy(rows[4]);multi.update(date_min='2026-11-18',date_max='2026-11-20')
        result=timeline.day_window([direct,single,multi,rows[-1]],'2026-11-17','2026-11-19')
        self.assertEqual((result['assigned'],result['possible_unique'],result['unknown']),(2,1,1))
        self.assertEqual([x['assigned_total'] for x in result['days']],[0,1,1])
        self.assertEqual([x['relative_possible_extra'] for x in result['days']],[0,1,1])
        self.assertEqual([x['possible_total'] for x in result['days']],[0,2,2])
        self.assertEqual(sum(x['relative_possible_extra'] for x in result['days']),2)
        self.assertEqual(result['intersecting_unique'],3)

    def test_daily_default_static_zoom_and_download_contract(self):
        html=timeline.render(fixture());doc=Markup(html)
        inputs={a['id']:a for tag,a in doc.tags if tag=='input'}
        self.assertEqual(inputs['date-from']['value'],'2026-10-21')
        self.assertEqual(inputs['date-to']['value'],'2026-11-19')
        self.assertEqual(sum(tag=='button' and 'data-day' in a for tag,a in doc.tags),30)
        self.assertTrue(any(tag=='option' and a.get('value')=='day' and 'selected' in a for tag,a in doc.tags))
        self.assertIn('dates-by-day.csv',[a.get('href') for tag,a in doc.tags if tag=='a'])
        self.assertIn('not additive across days',html)
        self.assertIn('possible daily counts must not be summed as distinct recordings',html)
        self.assertIn('recent 30 UTC days',html)
        self.assertIn('All-year overview',html)
        self.assertTrue({'date-from','date-to'}<={a['for'] for tag,a in doc.tags if tag=='label'})

    def test_daily_leap_days_zeroes_and_old_metadata_without_redundant_bounds(self):
        rows=timeline._validated(fixture())['records']
        result=timeline.day_window([rows[1]],'2024-02-08','2024-03-01')
        self.assertEqual(len(result['days']),23)
        self.assertEqual(sum(x['availability'] for x in result['days']),1)
        self.assertIn('2024-02-29',[x['date'] for x in result['days']])
        old=timeline.day_window([rows[0]],'1985-03-04','1985-03-04')
        self.assertEqual(old['days'][0]['publication'],1)
        self.assertEqual(old['assigned'],1)

    def test_unknown_daily_dates_never_gain_assigned_or_possible_counts(self):
        rows=timeline._validated(fixture())['records'][-1:]
        result=timeline.day_window(rows,'2026-11-18','2026-11-19')
        self.assertEqual((result['assigned'],result['possible_unique'],result['unknown']),(0,0,1))
        self.assertTrue(all(x['possible_total']==0 for x in result['days']))
        with self.assertRaises(ValueError):timeline.day_window(rows,'2026-11-19','2026-11-18')


if __name__=='__main__':unittest.main()
