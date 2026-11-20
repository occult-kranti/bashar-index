"""Render an offline failed-links snapshot from an explicitly supplied public report.

API: render(report) -> str. CLI writes only --output; the caller supplies the
companion failed-links.csv alongside it. No source, receipt or network reads.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

CATEGORIES = {
    'provider_refusal': 'Provider refusal',
    'local_failure': 'Local failure',
    'transfer_failure': 'Incomplete transfer',
    'metadata_failure': 'Metadata lookup failure',
    'needs_review': 'Needs review',
}
SCOPE = 'latest20plus_public_regular'


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return value


def _text(value, name):
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 and c not in '\n\t\r' for c in value):
        raise ValueError(f'{name} must be readable text')
    return value.strip()


def _utc(value, name, *, optional=False):
    if optional and value in (None, ''):
        return None
    value = _text(value, name)
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError(f'{name} must be an ISO UTC timestamp') from error
    if 'T' not in value or parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError(f'{name} must be an ISO UTC timestamp')
    return parsed.astimezone(timezone.utc)


def _record_url(value, video_id):
    """Validate the public identity, then discard tracking or extraneous fields."""
    try:
        url = urlsplit(_text(value, 'url'))
        if url.scheme != 'https' or url.username or url.password or url.port not in (None, 443):
            raise ValueError('public HTTPS recording URL required')
        watch = (url.hostname in ('youtube.com', 'www.youtube.com') and url.path == '/watch'
                 and parse_qs(url.query).get('v') == [video_id])
        short = url.hostname in ('youtu.be', 'www.youtu.be') and url.path == '/' + video_id
        if not (watch or short):
            raise ValueError('URL must identify the exact selected recording')
    except (TypeError, AttributeError) as error:
        raise ValueError('invalid recording URL') from error
    return 'https://www.youtube.com/watch?v=' + video_id


def _public_report(report):
    if not isinstance(report, dict) or report.get('scope') != SCOPE:
        raise ValueError('latest20plus_public_regular report required')
    out = {k: _integer(report.get(k), k) for k in ('selected', 'verified', 'remaining', 'other_pending', 'creators')}
    out.update(generated_at=_utc(report.get('generated_at'), 'generated_at'),
               closed_at=_utc(report.get('closed_at'), 'closed_at'))
    rows = report.get('failures')
    if not isinstance(rows, list):
        raise ValueError('failures must be a list')
    if out['selected'] != out['verified'] + out['remaining'] or out['remaining'] != len(rows) + out['other_pending']:
        raise ValueError('selected/verified/remaining/failure counts do not reconcile')
    if out['creators'] > out['selected'] or out['closed_at'] > out['generated_at']:
        raise ValueError('invalid creator count or snapshot chronology')
    public = []
    owners = {}
    seen = set()
    for source in rows:
        if not isinstance(source, dict):
            raise ValueError('failure row must be an object')
        video = source.get('video_id')
        if not isinstance(video, str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}', video) or video in seen:
            raise ValueError('distinct exact recording IDs required')
        seen.add(video)
        creator = _text(source.get('creator'), 'creator')
        channel = _text(source.get('channel_dir'), 'channel_dir')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', channel) or channel in ('.', '..'):
            raise ValueError('canonical channel_dir required')
        if channel in owners and owners[channel] != creator:
            raise ValueError('conflicting creator names for one channel_dir')
        owners[channel] = creator
        category = source.get('category')
        if category not in CATEGORIES or source.get('format') != 'videos':
            raise ValueError('known category and canonical videos format required')
        duration = source.get('duration_s')
        if duration is not None:
            _integer(duration, 'duration_s')
        status = source.get('http_status')
        if status is not None and (type(status) is not int or not 100 <= status <= 599):
            raise ValueError('HTTP status must be null or an actual three-digit status')
        # Construct explicitly: private metadata, paths, headers and arbitrary
        # additional input keys never enter the HTML or an embedded JSON blob.
        public.append(dict(video_id=video, creator=creator, channel_dir=channel,
            title=_text(source.get('title'), 'title'), url=_record_url(source.get('url'), video),
            rank=_integer(source.get('rank'), 'rank', 1), duration_s=duration, category=category,
            reason=_text(source.get('reason'), 'reason'), next_step=_text(source.get('next_step'), 'next_step'),
            http_status=status, attempt_count=_integer(source.get('attempt_count'), 'attempt_count'),
            last_attempt_utc=_utc(source.get('last_attempt_utc'), 'last_attempt_utc', optional=True),
            last_refusal_utc=_utc(source.get('last_refusal_utc'), 'last_refusal_utc', optional=True)))
    if len(owners) > out['creators']:
        raise ValueError('failure creators exceed selection creators')
    out['failures'] = sorted(public, key=lambda r: (r['creator'].casefold(), r['channel_dir'], r['rank'], r['video_id']))
    out['failure_creators'] = len(owners)
    return out


def _time(value):
    if value is None:
        return '<span class="muted">Not recorded</span>'
    iso = value.isoformat().replace('+00:00', 'Z')
    return f'<time datetime="{escape(iso, quote=True)}">{value:%Y-%m-%d}<span class="subline">{value:%H:%M:%S} UTC</span></time>'


def _duration(value):
    if value is None:
        return 'Unknown'
    hours, rest = divmod(value, 3600)
    minutes, seconds = divmod(rest, 60)
    return f'{hours}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes}:{seconds:02d}'


STYLE = r'''
:root{color-scheme:light dark;--canvas:#f5f2eb;--paper:#fffdf8;--ink:#17211e;--muted:#58635d;--forest:#1f554b;--pale:#e7eee7;--line:#cbd0c5;--input:#798579;--bad:#963b34;--serif:Georgia,'Times New Roman',serif;--sans:system-ui,-apple-system,'Segoe UI',sans-serif}
@media(prefers-color-scheme:dark){:root{--canvas:#15161a;--paper:#1e2026;--ink:#ececea;--muted:#b0b4ae;--forest:#8aceb0;--pale:#263c35;--line:#454b48;--input:#929e93;--bad:#ffa69d}}
*{box-sizing:border-box}body{margin:0;background:var(--canvas);color:var(--ink);font:1rem/1.55 var(--sans)}a{color:var(--forest);text-underline-offset:3px}a:hover{text-decoration-thickness:2px}:focus-visible{outline:3px solid var(--forest);outline-offset:4px}button,input,select{font:inherit;min-height:44px}button,select{cursor:pointer}button,input,select{color:var(--ink);background:var(--paper);border:1px solid var(--input);border-radius:4px;padding:.55rem .7rem}button:hover{background:var(--pale)}[hidden]{display:none!important}.skip{position:absolute;top:-100px;left:1rem;background:var(--paper);padding:.7rem;z-index:2}.skip:focus{top:1rem}.page{max-width:1440px;margin:auto;padding:0 2rem 3rem}.masthead{display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;padding:1.5rem 0;border-bottom:1px solid var(--line)}.wordmark{font:1.35rem var(--serif)}.edition,.eyebrow{font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;color:var(--forest)}.hero{display:grid;grid-template-columns:minmax(0,1fr) 19rem;gap:2rem;padding:2.5rem 0 2rem}h1{font:400 clamp(2.25rem,4.4vw,3.6rem)/1.12 var(--serif);letter-spacing:-.035em;margin:.8rem 0 1rem}h2{font:400 1.8rem/1.2 var(--serif);margin:0 0 .6rem}p{margin:.45rem 0 1rem}.intro{max-width:64ch;color:var(--muted)}.snapshot{border-left:1px solid var(--line);padding-left:1.5rem}.snapshot dt{font-size:.83rem;color:var(--muted)}.snapshot dd{margin:.1rem 0 1rem;font-variant-numeric:tabular-nums}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin:0 0 1rem;border-block:1px solid var(--line);padding:1.5rem 0}.metric{padding:0 1.4rem;border-left:1px solid var(--line)}.metric:first-child{padding-left:0;border-left:0}.metric dt{color:var(--muted);font-size:.88rem}.metric dd{font:400 2.7rem/1.15 var(--serif);margin:.3rem 0;font-variant-numeric:tabular-nums}.metric small{display:block;font:normal .85rem/1.4 var(--sans);color:var(--muted);margin-top:.4rem}.note{font-size:.88rem;color:var(--muted)}.download{display:inline-flex;align-items:center;min-height:44px;font-weight:650}.section-head{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;padding-top:1.5rem}.filters{display:grid;grid-template-columns:minmax(15rem,2fr) repeat(2,minmax(10rem,1fr));gap:1rem;background:var(--paper);border:1px solid var(--line);border-radius:5px;padding:1rem;margin:1rem 0}.field{display:flex;flex-direction:column;gap:.3rem;min-width:0}.field label{font-size:.85rem;font-weight:650}.sort-controls{display:flex;align-items:end;flex-wrap:wrap;gap:.7rem;grid-column:1/-1}.sort-controls .field{flex:0 1 15rem}.result-count{font-size:.9rem;color:var(--muted);min-height:1.5em}.table-wrap{border:1px solid var(--line);border-radius:5px;background:var(--paper);overflow:auto}table{border-collapse:collapse;width:100%;font-size:.91rem}caption{text-align:left;padding:1rem;font-weight:600;border-bottom:1px solid var(--line)}th,td{padding:1rem .8rem;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}thead th{font-size:.8rem;letter-spacing:.02em;background:var(--pale)}th[aria-sort="ascending"]::after{content:' ↑'}th[aria-sort="descending"]::after{content:' ↓'}tbody tr:last-child td{border-bottom:0}.recording{min-width:13rem;max-width:25rem}.title-link{font-weight:650;display:inline-block;min-height:24px;overflow-wrap:anywhere}.subline{display:block;font-size:.8rem;color:var(--muted);margin-top:.25rem}.id{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.reason-cell{min-width:15rem;max-width:30rem}.reason-cell p{margin:.5rem 0}.tag{display:inline-block;border:1px solid var(--line);border-radius:3px;padding:.15rem .45rem;font-size:.76rem;font-weight:650}.provider_refusal{color:var(--bad)}.next-label{font-weight:650}.numeric{font-variant-numeric:tabular-nums;white-space:nowrap}time{white-space:nowrap}.muted{color:var(--muted)}.cell-label{display:none}footer{border-top:1px solid var(--line);padding-top:1.2rem;margin-top:2rem;color:var(--muted);font-size:.85rem}.empty{padding:1.5rem}
@media(max-width:1100px){.page{padding-inline:1rem}.hero{grid-template-columns:1fr}.snapshot{display:flex;flex-wrap:wrap;gap:1rem 2rem;border-left:0;padding-left:0}.snapshot>div{min-width:12rem}.snapshot dd{margin-bottom:0}.metrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:1.5rem 0}.metric:nth-child(3){border-left:0;padding-left:0}.filters{grid-template-columns:repeat(2,minmax(0,1fr))}.filters>.field:first-child{grid-column:1/-1}thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}table,tbody,tr,td{display:block}caption{display:block;width:100%}tbody tr{padding:.8rem 1rem;border-bottom:1px solid var(--line)}tbody tr:last-child{border-bottom:0}td{border:0!important;padding:.35rem 0;min-width:0!important;max-width:none!important}.cell-label{display:inline;font-weight:650;margin-right:.5rem}.recording{margin-bottom:.5rem}.reason-cell{margin:.5rem 0;padding:.65rem 0;border-block:1px solid var(--line)!important}.reason-cell>.cell-label{display:none}.numeric{white-space:normal}.subline{margin-top:.15rem}time .subline{display:inline;margin-left:.5rem}}
@media(max-width:420px){.filters{grid-template-columns:1fr}.metric{padding-right:.5rem;padding-left:.7rem}.metric dd{font-size:2.2rem}.sort-controls .field{flex-basis:100%}}
@media print{.filters,.download,.skip{display:none!important}body{background:white;color:black}.page{max-width:none;padding:0}a{color:inherit}.hero{padding-top:0}.metrics{break-inside:avoid}tr{break-inside:avoid}[hidden]{display:none!important}}
'''

SCRIPT = r'''
(() => {
  const controls = document.getElementById('filters');
  const table = document.getElementById('failure-table');
  const body = table.tBodies[0];
  const rows = Array.from(body.querySelectorAll('tr[data-record]'));
  const search = document.getElementById('search');
  const creator = document.getElementById('creator');
  const category = document.getElementById('category');
  const sort = document.getElementById('sort');
  const direction = document.getElementById('direction');
  const empty = document.getElementById('empty-row');
  const status = document.getElementById('visible-count');
  const numeric = new Set(['rank','duration','http','attempts','attempt','refusal']);
  let ascending = true;
  function draw() {
    const query = search.value.trim().toLocaleLowerCase();
    const key = sort.value;
    const ordered = rows.slice().sort((a,b) => {
      let x = a.dataset[key], y = b.dataset[key];
      if (x === '' || y === '') return x === y ? 0 : x === '' ? 1 : -1;
      const value = numeric.has(key) ? Number(x)-Number(y) : x.localeCompare(y,undefined,{sensitivity:'base'});
      return (value || a.dataset.record.localeCompare(b.dataset.record)) * (ascending ? 1 : -1);
    });
    let count = 0;
    for (const row of ordered) {
      row.hidden = !((!creator.value || row.dataset.owner === creator.value) &&
        (!category.value || row.dataset.category === category.value) &&
        (!query || row.dataset.search.toLocaleLowerCase().includes(query)));
      if (!row.hidden) count++;
      body.append(row);
    }
    body.append(empty); empty.hidden = count !== 0;
    table.querySelectorAll('thead th').forEach(th => th.removeAttribute('aria-sort'));
    const columnKey = key === 'attempts' ? 'http' : key;
    const column = table.querySelector('[data-sort-column="'+columnKey+'"]');
    if (column) column.setAttribute('aria-sort',ascending ? 'ascending' : 'descending');
    direction.textContent = ascending ? 'Ascending ↑' : 'Descending ↓';
    direction.setAttribute('aria-label','Change sort direction. Current: '+(ascending ? 'ascending' : 'descending'));
    status.textContent = 'Showing '+count.toLocaleString()+' of '+rows.length.toLocaleString()+
      ' failed recordings. Sorted by '+sort.options[sort.selectedIndex].text.toLocaleLowerCase()+
      ', '+(ascending ? 'ascending.' : 'descending.');
  }
  search.addEventListener('input',draw); creator.addEventListener('change',draw);
  category.addEventListener('change',draw); sort.addEventListener('change',draw);
  direction.addEventListener('click',() => {ascending=!ascending;draw();});
  document.getElementById('clear').addEventListener('click',() => {
    search.value='';creator.value='';category.value='';sort.value='creator';ascending=true;draw();search.focus();
  });
  draw(); controls.hidden=false;
})();
'''


def render(report) -> str:
    """Return complete static HTML, progressively enhanced by local inline JS."""
    data = _public_report(report)
    rows = data['failures']
    e = lambda value: escape(str(value), quote=True)
    row_html = []
    for row in rows:
        attrs = dict(record=row['video_id'], title=row['title'], creator=row['creator'], owner=row['channel_dir'],
            rank=row['rank'], duration='' if row['duration_s'] is None else row['duration_s'], category=row['category'],
            http='' if row['http_status'] is None else row['http_status'], attempts=row['attempt_count'],
            attempt='' if row['last_attempt_utc'] is None else row['last_attempt_utc'].timestamp(),
            refusal='' if row['last_refusal_utc'] is None else row['last_refusal_utc'].timestamp(),
            search=' '.join(row[k] for k in ('video_id','title','creator','reason','next_step')))
        attributes = ' '.join(f'data-{key}="{e(value)}"' for key, value in attrs.items())
        def cell(label, content, css=''):
            return f'<td role="cell" class="{css}"><span class="cell-label" aria-hidden="true">{label}:</span>{content}</td>'
        row_html.append(f'<tr role="row" {attributes}>' +
            cell('Recording', f'<a class="title-link" href="{e(row["url"])}">{e(row["title"])}</a><span class="subline id">{e(row["video_id"])}</span>', 'recording') +
            cell('Creator', e(row['creator'])) + cell('Rank', f'#{row["rank"]}', 'numeric') +
            cell('Duration', _duration(row['duration_s']), 'numeric') +
            cell('Issue', f'<span class="tag {row["category"]}">{CATEGORIES[row["category"]]}</span>'
                 f'<p>{e(row["reason"])}</p><p><span class="next-label">Next step:</span> {e(row["next_step"])}</p>', 'reason-cell') +
            cell('HTTP / attempts', ('<span class="muted">Not recorded</span>' if row['http_status'] is None else str(row['http_status'])) +
                 f'<span class="subline">{row["attempt_count"]} '+('attempt' if row['attempt_count']==1 else 'attempts')+'</span>', 'numeric') +
            cell('Last attempt', _time(row['last_attempt_utc'])) + cell('Last refusal', _time(row['last_refusal_utc'])) + '</tr>')
    creators = sorted({(r['channel_dir'],r['creator']) for r in rows}, key=lambda r: (r[1].casefold(),r[0]))
    creator_options = ''.join(f'<option value="{e(slug)}">{e(name)}</option>' for slug,name in creators)
    category_options = ''.join(f'<option value="{key}">{label}</option>' for key,label in CATEGORIES.items())
    counts = {key:sum(r['category']==key for r in rows) for key in CATEGORIES}
    category_counts = ' · '.join(f'{counts[key]:,} {label.lower()}' +
        ('s' if counts[key]!=1 and key!='needs_review' else '')
        for key,label in CATEGORIES.items() if counts[key])
    sort_options = ''.join(f'<option value="{key}">{label}</option>' for key,label in (
        ('creator','Creator'),('title','Recording title'),('rank','Selected rank'),('duration','Duration'),
        ('category','Issue category'),('http','HTTP status'),('attempts','Attempt count'),('attempt','Last attempt'),('refusal','Last refusal')))
    headers = ''.join(f'<th role="columnheader" scope="col" data-sort-column="{key}">{label}</th>' for key,label in (
        ('title','Recording'),('creator','Creator'),('rank','Rank'),('duration','Duration'),('category','Issue / next step'),
        ('http','HTTP / attempts'),('attempt','Last attempt'),('refusal','Last refusal')))
    metrics = ''.join(f'<div class="metric"><dt>{label}</dt><dd>{amount:,}<small>{detail}</small></dd></div>' for label,amount,detail in (
        ('Verified audio',data['verified'],f'of {data["selected"]:,} selected recordings'),
        ('Failed recordings',len(rows),f'across {data["failure_creators"]:,} creators'),
        ('Other pending',data['other_pending'],'not classified as failed in this report'),
        ('Total remaining',data['remaining'],'failed recordings + other pending')))
    empty_text = 'No failed recordings are listed in this snapshot.' if not rows else 'No recordings match these filters. Clear the filters to see all failed links.'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta name="color-scheme" content="light dark"><meta name="description" content="Closed-run failed recording links, recorded reasons and next steps for latest 20 regular uploads.">
<title>Failed recording links · Latest 20+ videos</title><style>{STYLE}</style></head>
<body><a class="skip" href="#failures-heading">Skip to failed recordings</a><div class="page">
<header class="masthead"><span class="wordmark">Channeling research archive</span><span class="edition">Collection snapshot · Latest 20+ videos</span></header>
<main id="main" tabindex="-1"><div class="hero"><div><p class="eyebrow">Public regular uploads</p><h1>Failed recording links</h1>
<p class="intro">Recorded acquisition failures and practical next steps for the latest 20 regular uploads per creator. Other pending recordings are counted separately.</p>
<p class="note">Scope: latest20plus_public_regular · {data['creators']:,} selected creators. Selection follows Videos-tab rank; dates and durations do not limit eligibility.</p></div>
<dl class="snapshot"><div><dt>Report generated</dt><dd>{_time(data['generated_at'])}</dd></div><div><dt>Closed-run evidence through</dt><dd>{_time(data['closed_at'])}</dd></div></dl></div>
<dl class="metrics" aria-label="Collection counts">{metrics}</dl>
<p class="note">Verified audio counts receipt-backed native, qualified and independent publisher editions. This is a supplied report snapshot; it does not refresh or check availability.</p>
<section aria-labelledby="failures-heading"><div class="section-head"><div><h2 id="failures-heading" tabindex="-1">{len(rows):,} failed recordings</h2><p class="note">{e(category_counts) if rows else 'Other pending work is not labelled as a failure.'}</p></div>
<a class="download" href="failed-links.csv" download>Download failed links CSV</a></div>
<div id="filters" class="filters" hidden aria-label="Filter and sort failed recordings">
<div class="field"><label for="search">Search title, ID, creator or reason</label><input id="search" type="search" autocomplete="off" aria-controls="failure-table" placeholder="Search these failed recordings"></div>
<div class="field"><label for="creator">Creator</label><select id="creator" aria-controls="failure-table"><option value="">All creators</option>{creator_options}</select></div>
<div class="field"><label for="category">Issue category</label><select id="category" aria-controls="failure-table"><option value="">All categories</option>{category_options}</select></div>
<div class="sort-controls"><div class="field"><label for="sort">Sort by</label><select id="sort" aria-controls="failure-table">{sort_options}</select></div><button id="direction" type="button">Ascending ↑</button><button id="clear" type="button">Clear filters</button></div></div>
<noscript><p class="note">All failed recordings are shown below. Search and sorting require JavaScript; the links and CSV work without it.</p></noscript>
<p id="visible-count" class="result-count" role="status" aria-live="polite" aria-atomic="true">Showing {len(rows):,} of {len(rows):,} failed recordings.</p>
<div class="table-wrap"><table id="failure-table" role="table"><caption>Failed recordings · rank is one-based within each creator’s selected regular uploads · all dates UTC</caption>
<thead role="rowgroup"><tr role="row">{headers}</tr></thead><tbody role="rowgroup">{''.join(row_html)}
<tr id="empty-row" role="row"{'' if not rows else ' hidden'}><td role="cell" class="empty" colspan="8">{empty_text}</td></tr></tbody></table></div></section>
</main><footer>Each link opens the exact public recording page. “Not recorded” and “Unknown” preserve missing evidence. A provider refusal records that request’s outcome, without asserting a permanent restriction on the recording. No live rate or completion estimate is inferred.</footer>
</div><script>{SCRIPT}</script></body></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path, help='Sanitized report JSON')
    parser.add_argument('--output', required=True, type=Path, help='Explicit output HTML path; keep failed-links.csv alongside it')
    args = parser.parse_args(argv)
    report = json.loads(args.report.read_text(encoding='utf-8-sig'))
    html = render(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding='utf-8', newline='\n')
    print(json.dumps({key:report[key] for key in ('selected','verified','remaining','other_pending')} | {'failed_recordings':len(report['failures'])}))


if __name__ == '__main__':
    main()
