"""Invented public snapshots; no source, remote files or real dashboards are read."""
from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from pipeline import collection_failure_dashboard as dashboard


def fixture():
    rows=[]
    for video,name,slug,category,status,duration in (
        ('alpha123456','Alpha creator','alpha','provider_refusal',403,3601),
        ('beta1234567','Beta creator','beta','transfer_failure',200,None),
        ('gamma123456','Alpha creator','alpha','local_failure',None,34)):
        rows.append(dict(video_id=video,creator=name,channel_dir=slug,title='A complete recording '+video,
            url='https://www.youtube.com/watch?v='+video,rank=len(rows)+1,duration_s=duration,
            category=category,reason={'provider_refusal':'The provider returned HTTP 403.',
                'transfer_failure':'The response ended before the whole file arrived.',
                'local_failure':'The local browser could not start.'}[category],
            next_step='Use the appropriate existing recovery route.',http_status=status,attempt_count=1,
            last_attempt_utc='2026-11-19T22:00:00Z',last_refusal_utc='2026-11-19T22:00:01Z' if status==403 else None,
            format='videos'))
    return dict(generated_at='2026-11-19T23:00:00Z',closed_at='2026-11-19T22:30:00Z',
        scope='latest20plus_public_regular',selected=10,verified=5,remaining=5,other_pending=2,creators=3,failures=rows)


class Markup(HTMLParser):
    def __init__(self,html):
        super().__init__(convert_charrefs=True);self.tags=[];self.text=[];self.records=[];self.feed(html)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs);self.tags.append((tag,attrs))
        if tag=='tr' and 'data-record' in attrs:self.records.append(attrs)
    def handle_data(self,value):self.text.append(value)


class FailureDashboardTests(unittest.TestCase):
    def test_all_rows_and_counts_are_static_without_javascript(self):
        report=fixture();before=deepcopy(report);html=dashboard.render(report);doc=Markup(html)
        self.assertEqual(report,before)
        self.assertEqual(len(doc.records),3)
        self.assertTrue(all('hidden' not in row for row in doc.records))
        self.assertEqual([r['data-record'] for r in doc.records],['alpha123456','gamma123456','beta1234567'])
        text=' '.join(doc.text)
        for value in ('of 10 selected recordings','Other pending','not classified as failed','1:00:01','Unknown','Not recorded','Closed-run evidence through'):
            self.assertIn(value,text)
        links=[a['href'] for tag,a in doc.tags if tag=='a']
        self.assertEqual(sum(x.startswith('https://www.youtube.com/watch?v=') for x in links),3)
        self.assertIn('failed-links.csv',links)
        self.assertTrue(any(tag=='noscript' for tag,_ in doc.tags))

    def test_privacy_whitelist_and_canonical_links_do_not_export_technical_payload(self):
        report=fixture();report['private_payload']={'cookies':'SECRET-TOP','path':'C:/private/SECRET-PATH'}
        row=report['failures'][0];row['headers']={'Authorization':'SECRET-ROW'};row['signed_url']='SECRET-SIGNED'
        row['url']+='&signature=SECRET-QUERY#SECRET-FRAGMENT'
        html=dashboard.render(report)
        self.assertNotIn('SECRET-',html)
        self.assertIn('href="https://www.youtube.com/watch?v=alpha123456"',html)
        self.assertNotIn('application/json',html)

    def test_untrusted_display_text_is_escaped_and_never_creates_html(self):
        report=fixture();report['failures'][0]['title']='</script><img src=x onerror=alert(1)> & "title"'
        report['failures'][0]['reason']='<b onclick="bad()">Reason</b>'
        doc=Markup(dashboard.render(report))
        self.assertEqual(sum(tag=='script' for tag,_ in doc.tags),1)
        self.assertFalse(any(tag in ('img','b') or any(k.startswith('on') for k in attrs) for tag,attrs in doc.tags))
        self.assertIn('</script><img src=x onerror=alert(1)> & "title"',' '.join(doc.text))

    def test_counts_identity_format_and_utc_validation(self):
        changes=[lambda d:d.update(verified=6),lambda d:d.update(other_pending=1),
            lambda d:d.update(scope='historical_mixed'),lambda d:d.update(generated_at='2026-11-19T23:00:00'),
            lambda d:d['failures'][0].update(url='https://www.youtube.com/watch?v=wrong123456'),
            lambda d:d['failures'][0].update(url='javascript:alert(1)'),
            lambda d:d['failures'][1].update(video_id='alpha123456'),
            lambda d:d['failures'][2].update(creator='Conflicting owner'),
            lambda d:d['failures'][0].update(format='shorts'),lambda d:d['failures'][0].update(category='secret_local_code'),
            lambda d:d['failures'][0].update(rank=0),lambda d:d['failures'][0].update(duration_s=True),
            lambda d:d['failures'][0].update(http_status=True),lambda d:d['failures'][0].update(attempt_count=-1)]
        for mutate in changes:
            d=fixture();mutate(d)
            with self.subTest(d=d),self.assertRaises(ValueError):dashboard.render(d)

    def test_old_and_undated_recordings_remain_and_no_live_clock_is_invented(self):
        report=fixture();report['failures'][0]['published_at']='2001-01-01';report['failures'][1]['published_at']=None
        report['failures'][1].update(last_attempt_utc=None,last_refusal_utc=None,attempt_count=0)
        html=dashboard.render(report)
        self.assertEqual(len(Markup(html).records),3)
        self.assertIn('dates and durations do not limit eligibility',html)
        self.assertIn('0 attempts',html);self.assertNotIn('new Date(',html)
        self.assertEqual(dashboard.render(report),html)

    def test_accessible_local_controls_and_offline_assets(self):
        html=dashboard.render(fixture());doc=Markup(html)
        by_id={a['id']:(tag,a) for tag,a in doc.tags if 'id' in a}
        labels={a['for'] for tag,a in doc.tags if tag=='label'}
        for key in ('search','creator','category','sort'):
            self.assertIn(key,labels);self.assertIn('aria-controls',by_id[key][1])
        self.assertEqual(by_id['visible-count'][1]['aria-live'],'polite')
        self.assertIn('hidden',by_id['filters'][1])
        self.assertTrue(any(tag=='caption' for tag,_ in doc.tags))
        self.assertTrue(all(a.get('scope')=='col' for tag,a in doc.tags if tag=='th'))
        self.assertFalse(any(tag in ('link','iframe','img') or tag=='script' and 'src' in a for tag,a in doc.tags))
        self.assertNotIn('fetch(',html);self.assertNotIn('innerHTML',html)
        self.assertIn('default-src &#39;none&#39;'.replace('&#39;',"'"),html)
        self.assertIn(':focus-visible',html)

    def test_empty_failures_keep_other_pending_honest(self):
        report=fixture();report.update(failures=[],verified=8,remaining=2,other_pending=2)
        html=dashboard.render(report)
        self.assertEqual(Markup(html).records,[])
        self.assertIn('No failed recordings are listed in this snapshot.',html)
        self.assertIn('not classified as failed',html)

    def test_json_cli_writes_only_explicit_html_and_leaves_csv_to_caller(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);source=folder/'report.json';target=folder/'out/failed-links.html'
            source.write_text(json.dumps(fixture()),encoding='utf8')
            with redirect_stdout(StringIO()) as stdout:
                dashboard.main(['--report',str(source),'--output',str(target)])
            self.assertTrue(target.read_text(encoding='utf8').startswith('<!doctype html>'))
            self.assertEqual(json.loads(stdout.getvalue())['failed_recordings'],3)
            self.assertFalse((target.parent/'failed-links.csv').exists())
            self.assertEqual(json.loads(source.read_bytes()),fixture())


if __name__=='__main__':unittest.main()
