"""Offline, uncertainty-aware UI for Root-produced primary-recording date rows.

render(report) returns complete HTML. Date evidence and intervals are inputs;
this renderer never parses relative ages, chooses midpoints or fetches sources.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import date, datetime
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit,parse_qs

from .collection_failure_dashboard import STYLE as BASE_STYLE

METHODS={'publication':'Publication date','availability':'Availability metadata',
         'upload':'Upload fallback','relative':'Relative interval','unknown':'Unknown'}
SERIES=(('metadata','Publication / availability metadata'),('upload','Upload fallback'),('relative','Interval estimate'))

def _need(ok,message):
    if not ok:raise ValueError(message)

def _day(value):
    if value in (None,''):return None
    _need(isinstance(value,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',value),'ISO calendar date required')
    return date.fromisoformat(value).isoformat()

def _clock(value,*,required=False):
    if value in (None,'') and not required:return None
    _need(isinstance(value,str) and 'T' in value,'ISO UTC observation clock required')
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    _need(d.tzinfo is not None and d.utcoffset().total_seconds()==0,'UTC observation clock required')
    return d.isoformat().replace('+00:00','Z')

def _public_url(value,*,optional=False):
    if value in (None,'') and optional:return None
    _need(isinstance(value,str),'public source URL required')
    u=urlsplit(value)
    _need(u.scheme in ('https','http') and bool(u.hostname) and not u.username and not u.password,'public HTTP source URL required')
    _need(not u.hostname.lower().endswith('googlevideo.com') and not any(
        re.fullmatch(r'(?:sig|signature|token|auth|pot|lsig|x-amz-.+)',k,re.I) for k in parse_qs(u.query)),
        'unsigned public evidence link required')
    return value

def _validated(report):
    _need(isinstance(report,dict) and report.get('scope')=='latest20plus_public_regular_dates','primary regular date-report scope required')
    generated=_clock(report.get('generated_at'),required=True)
    sha=report.get('selection_sha256');_need(isinstance(sha,str) and re.fullmatch('[0-9a-f]{64}',sha),'selection SHA256 required')
    records=report.get('records');_need(isinstance(records,list) and bool(records),'date records required')
    rows=[];seen=set();owners={}
    for source in records:
        _need(isinstance(source,dict),'date record object required')
        v=source.get('video_id');channel=source.get('channel_dir');creator=source.get('creator');title=source.get('title')
        _need(isinstance(v,str) and re.fullmatch('[A-Za-z0-9_-]{11}',v) and v not in seen,'unique selected video ID required');seen.add(v)
        _need(isinstance(channel,str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*',channel),'canonical creator slug required')
        _need(isinstance(creator,str) and creator.strip() and isinstance(title,str),'public creator and title required')
        _need(channel not in owners or owners[channel]==creator,'one creator name per canonical slug required');owners[channel]=creator
        rank=source.get('rank');_need(type(rank) is int and rank>=1,'one-based selected rank required')
        target=_public_url(source.get('url'));u=urlsplit(target)
        _need((u.hostname in ('youtube.com','www.youtube.com') and u.path=='/watch' and parse_qs(u.query).get('v')==[v])
              or (u.hostname in ('youtu.be','www.youtu.be') and u.path=='/'+v),'recording URL/ID mismatch')
        method=source.get('date_method');_need(method in METHODS,'known date method required')
        exact=_day(source.get('exact_day'));low=_day(source.get('date_min'));high=_day(source.get('date_max'))
        _need((low is None)==(high is None) and (low is None or low<=high),'complete ordered date interval required')
        if method in ('publication','availability','upload'):
            _need(exact is not None and low in (None,exact) and high in (None,exact),'date-stamped metadata must bind the exact day')
        elif method=='relative':_need(exact is None and low is not None,'relative estimate needs bounds without an exact day')
        else:_need(exact is None and low is None,'unknown dates cannot gain a plotted date')
        year=source.get('year_bin');month=source.get('month_bin')
        # The evidence builder owns these bins. Check its whole-window rule,
        # never substitute a representative point for a crossing interval.
        left,right=(exact,exact) if exact else (low,high)
        expected_year=left[:4] if left and left[:4]==right[:4] else None
        expected_month=left[:7] if left and left[:7]==right[:7] else None
        _need(year==expected_year and month==expected_month,'supplied bins must contain the entire date interval')
        detail=source.get('method_detail');_need(isinstance(detail,str),'human date method detail required')
        _need(source.get('relative_label') is None or isinstance(source.get('relative_label'),str),'public relative label must be text')
        evidence=source.get('evidence_sha256')
        _need(evidence in (None,'') or isinstance(evidence,str) and re.fullmatch('[0-9a-f]{64}',evidence),'public evidence SHA256 required')
        rows.append({'video_id':v,'channel_dir':channel,'creator':creator,'title':title,
            'url':'https://www.youtube.com/watch?v='+v,'rank':rank,'date_method':method,'method_detail':detail,
            'source_url':_public_url(source.get('source_url'),optional=True),'exact_day':exact,'date_min':low,'date_max':high,
            'year_bin':year,'month_bin':month,'relative_label':str(source.get('relative_label') or ''),
            'observed_at':_clock(source.get('observed_at')),'publication_day':_day(source.get('publication_day')),
            'availability_day':_day(source.get('availability_day')),'upload_day':_day(source.get('upload_day')),
            'evidence_sha256':evidence or None})
    calibration=report.get('calibration') or {};compared=calibration.get('compared',0);within=calibration.get('within_interval',0)
    _need(type(compared) is int and type(within) is int and 0<=within<=compared,'calibration counts do not reconcile')
    return {'generated_at':generated,'selection_sha256':sha,'records':sorted(rows,key=lambda r:(r['creator'].casefold(),r['rank'],r['video_id'])),
            'calibration':{'compared':compared,'within_interval':within},'creators':owners}

def _series(row):return 'metadata' if row['date_method'] in ('publication','availability') else row['date_method']

def aggregate(records,period='year'):
    """Count only explicit bins; preserve crossing-window ambiguity separately."""
    _need(period in ('year','month'),'year or month bins required')
    bins=defaultdict(Counter);ambiguous=unknown=0
    for row in records:
        key=row[period+'_bin']
        if key:bins[key][_series(row)]+=1
        elif row['date_method']=='relative':ambiguous+=1
        else:unknown+=1
    placed=sum(sum(c.values()) for c in bins.values())
    _need(placed+ambiguous+unknown==len(records),'date-bin counts do not reconcile')
    return {'bins':[{'period':key,**{kind:counts[kind] for kind,_ in SERIES},'total':sum(counts.values())} for key,counts in sorted(bins.items())],
            'placed':placed,'ambiguous':ambiguous,'unknown':unknown,'selected':len(records)}

def _chart(result):
    maximum=max((row['total'] for row in result['bins']),default=0);bars=[]
    for row in result['bins']:
        label=', '.join(f'{name}: {row[kind]}' for kind,name in SERIES)
        segments=''.join(f'<span class="segment {kind}" style="width:{100*row[kind]/maximum:.6f}%" title="{escape(name)}: {row[kind]}"></span>' for kind,name in SERIES if row[kind])
        bars.append(f'<li class="bin"><span class="period">{row["period"]}</span><span class="bar" aria-hidden="true">{segments}</span><strong>{row["total"]:,}</strong><span class="sr-only">{label}</span></li>')
    return f'<p class="axis" id="chart-scale">Recordings per period · linear count scale, 0–{maximum:,}</p><ol class="bin-list" tabindex="0" aria-label="Nonempty calendar bins">{"".join(bars)}</ol>'+('' if bars else '<p class="empty">No records can be placed in a calendar bin for this filter.</p>')

EXTRA_STYLE=r'''
.timeline-metrics{grid-template-columns:repeat(5,minmax(0,1fr))}.timeline-metrics .metric dd{font-size:2.3rem}.legend{display:flex;flex-wrap:wrap;gap:.7rem 1.4rem;font-size:.84rem;margin:1rem 0}.swatch{display:inline-block;width:1rem;height:1rem;margin-right:.4rem;vertical-align:-.15rem;border:1px solid var(--ink)}.metadata{background:var(--forest)}.upload{background:#75648b}.relative{background-color:#c99a4e;background-image:repeating-linear-gradient(45deg,transparent,transparent 3px,#513c1e 3px,#513c1e 4px)}.chart{background:var(--paper);border:1px solid var(--line);border-radius:5px;padding:1rem}.axis{color:var(--muted);font-size:.85rem}.bin-list{list-style:none;padding:0;margin:0;max-height:30rem;overflow:auto}.bin{display:grid;grid-template-columns:5rem minmax(4rem,1fr) 4rem;align-items:center;gap:.8rem;margin:.45rem 0;min-height:1.5rem;font-size:.85rem}.bin strong{text-align:right;font-variant-numeric:tabular-nums}.bar{display:flex;min-width:0;height:1.15rem;background:var(--canvas)}.segment{height:100%;display:block}.period{font-variant-numeric:tabular-nums}.timeline-controls{grid-template-columns:2fr 1fr 1fr}.timeline-controls .period-controls{grid-column:1/-1;display:flex;align-items:end;flex-wrap:wrap;gap:.8rem}.timeline-controls .period-controls .field{min-width:11rem}.evidence-cell{min-width:13rem;max-width:24rem}.evidence-cell p{margin:.35rem 0}.date-range{font-variant-numeric:tabular-nums}.hash{font: .75rem ui-monospace,Consolas,monospace;overflow-wrap:anywhere}.full-hash{display:block;max-width:55ch;overflow-wrap:anywhere}.date-table td{overflow-wrap:anywhere}.date-table summary{min-height:24px;cursor:pointer}.source-link{display:inline-flex;min-height:24px;align-items:center}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}.static-note{font-size:.9rem;color:var(--muted)}
@media(max-width:1100px){.timeline-metrics{grid-template-columns:repeat(3,minmax(0,1fr))}.timeline-metrics .metric{padding-left:1rem;border-left:1px solid var(--line)}.timeline-metrics .metric:nth-child(3n+1){border-left:0;padding-left:0}.timeline-controls{grid-template-columns:1fr 1fr}.timeline-controls>.field:first-child{grid-column:1/-1}.evidence-cell{min-width:0;max-width:none}.bin{grid-template-columns:4.3rem minmax(3rem,1fr) 3rem;gap:.5rem}}
@media(max-width:550px){.timeline-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.timeline-metrics .metric{border-left:1px solid var(--line)!important;padding-left:1rem!important}.timeline-metrics .metric:nth-child(2n+1){border-left:0!important;padding-left:0!important}.timeline-controls{grid-template-columns:1fr}.chart{padding:.7rem}.bin{font-size:.8rem}.legend{display:grid;gap:.5rem}}
'''

SCRIPT=r'''
(() => {
 const table=document.getElementById('date-table'), rows=Array.from(table.querySelectorAll('tr[data-video]'));
 const creator=document.getElementById('creator'),method=document.getElementById('method'),search=document.getElementById('search'),period=document.getElementById('period');
 const kinds=[['metadata','Publication / availability metadata'],['upload','Upload fallback'],['relative','Interval estimate']];
 const chart=document.getElementById('chart'),status=document.getElementById('date-status');
 function el(tag,text,cls){const x=document.createElement(tag);if(text!==undefined)x.textContent=text;if(cls)x.className=cls;return x;}
 function draw(){
  const query=search.value.trim().toLocaleLowerCase(), bins=new Map();let selected=0,ambiguous=0,unknown=0;
  for(const row of rows){row.hidden=!((!creator.value||row.dataset.creator===creator.value)&&(!method.value||row.dataset.method===method.value)&&(!query||row.dataset.search.toLocaleLowerCase().includes(query)));
   if(row.hidden)continue;selected++;const key=row.dataset[period.value],type=row.dataset.method;
   if(!key){if(type==='relative')ambiguous++;else unknown++;continue;}
   if(!bins.has(key))bins.set(key,{metadata:0,upload:0,relative:0,total:0});const count=bins.get(key);count[['publication','availability'].includes(type)?'metadata':type]++;count.total++;
  }
  const placed=selected-ambiguous-unknown,maximum=Math.max(0,...Array.from(bins.values(),x=>x.total));
  const axis=el('p','Recordings per period · linear count scale, 0–'+maximum.toLocaleString(),'axis');axis.id='chart-scale';
  const list=el('ol',undefined,'bin-list');list.tabIndex=0;list.setAttribute('aria-label','Nonempty calendar '+period.value+' bins');
  for(const [key,count] of Array.from(bins).sort((a,b)=>a[0].localeCompare(b[0]))){
   const item=el('li',undefined,'bin'),bar=el('span',undefined,'bar');bar.setAttribute('aria-hidden','true');
   for(const [kind,label] of kinds)if(count[kind]){const segment=el('span',undefined,'segment '+kind);segment.style.width=String(100*count[kind]/maximum)+'%';segment.title=label+': '+count[kind];bar.append(segment);}
   item.append(el('span',key,'period'),bar,el('strong',count.total.toLocaleString()),el('span',kinds.map(([k,l])=>l+': '+count[k]).join(', '),'sr-only'));list.append(item);
  }
  chart.replaceChildren(axis,list);if(!bins.size)chart.append(el('p','No records can be placed in a calendar bin for this filter.','empty'));
  status.textContent=selected.toLocaleString()+' selected in this view: '+placed.toLocaleString()+' placed by '+period.value+', '+ambiguous.toLocaleString()+' '+period.value+'-ambiguous interval estimates, '+unknown.toLocaleString()+' unknown. Missing and ambiguous dates stay in the table and CSV.';
  document.getElementById('empty-row').hidden=selected!==0;
 }
 for(const control of [creator,method,period])control.addEventListener('change',draw);search.addEventListener('input',draw);
 document.getElementById('clear').addEventListener('click',()=>{creator.value='';method.value='';search.value='';period.value='year';draw();search.focus();});
 draw();document.getElementById('controls').hidden=false;
})();
'''

def render(report)->str:
    data=_validated(report);rows=data['records'];e=lambda x:escape(str(x),quote=True)
    counts=Counter(r['date_method'] for r in rows);year=aggregate(rows,'year');out=[]
    for r in rows:
        attrs={'video':r['video_id'],'creator':r['channel_dir'],'method':r['date_method'],'year':r['year_bin'] or '',
               'month':r['month_bin'] or '','search':' '.join([r['video_id'],r['title'],r['creator'],r['method_detail']])}
        attr=' '.join(f'data-{key}="{e(value)}"' for key,value in attrs.items())
        chosen=e(r['exact_day']) if r['exact_day'] else (e(r['date_min'])+' → '+e(r['date_max'])+'<span class="subline">Inclusive estimated interval</span>' if r['date_min'] else 'Unresolved')
        def cell(label,text,css=''):return f'<td role="cell" class="{css}"><span class="cell-label" aria-hidden="true">{label}:</span>{text}</td>'
        original=''.join(f'<span class="subline">{label}: {e(r[key])}</span>' for key,label in (
            ('publication_day','Publication'),('availability_day','Availability'),('upload_day','Upload')) if r[key])
        observed=f'<span class="subline">Observed {e(r["observed_at"])}</span>' if r['observed_at'] else ''
        source=f'<a class="source-link" href="{e(r["source_url"])}">Date evidence source</a>' if r['source_url'] else '<span class="muted">Date source not recorded</span>'
        if r['evidence_sha256']:source+=f'<details><summary>Evidence checksum</summary><span class="hash">{r["evidence_sha256"]}</span></details>'
        placement=f'Year: {e(r["year_bin"] or ("ambiguous" if r["date_method"]=="relative" else "unknown"))}<span class="subline">Month: {e(r["month_bin"] or ("ambiguous" if r["date_method"]=="relative" else "unknown"))}</span>'
        out.append(f'<tr role="row" {attr}>'+cell('Recording',f'<a class="title-link" href="{r["url"]}">{e(r["title"])}</a><span class="subline id">{r["video_id"]} · rank {r["rank"]}</span>','recording')+
            cell('Creator',e(r['creator']))+cell('Date / interval',chosen+original,'date-range')+
            cell('Method',f'<span class="tag">{METHODS[r["date_method"]]}</span><p>{e(r["method_detail"])}</p>'+ (f'<span class="subline">Listing label: {e(r["relative_label"])}</span>' if r['relative_label'] else '')+observed,'evidence-cell')+
            cell('Public source',source)+cell('Chart placement',placement)+'</tr>')
    options=''.join(f'<option value="{e(slug)}">{e(name)}</option>' for slug,name in sorted(data['creators'].items(),key=lambda x:(x[1].casefold(),x[0])))
    methods=''.join(f'<option value="{key}">{label}</option>' for key,label in METHODS.items())
    metrics=''.join(f'<div class="metric"><dt>{label}</dt><dd>{value:,}<small>{note}</small></dd></div>' for label,value,note in (
        ('Selected recordings',len(rows),f'{len(data["creators"]):,} creators'),('Date-stamped metadata',counts['publication']+counts['availability'],'publication / availability fields'),
        ('Upload fallback',counts['upload'],'not promoted to publication date'),('Interval estimates',counts['relative'],'no representative midpoint assigned'),('Unknown',counts['unknown'],'kept unresolved')))
    legends=''.join(f'<span><i class="swatch {kind}" aria-hidden="true"></i>{label}</span>' for kind,label in SERIES)
    calibration=data['calibration'];calnote=(f'Calibration: {calibration["within_interval"]:,} of {calibration["compared"]:,} date-stamped comparisons fell inside the saved listing-age interval.' if calibration['compared'] else 'No interval calibration comparisons were supplied.')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Publication metadata timeline · Latest 20+ videos</title><style>{BASE_STYLE}{EXTRA_STYLE}</style></head>
<body><a class="skip" href="#timeline-heading">Skip to date distribution</a><div class="page"><header class="masthead"><span class="wordmark">Channeling research archive</span><span class="edition">Latest 20+ videos · metadata timeline</span></header>
<main><div class="hero"><div><p class="eyebrow">Public regular uploads · selected by tab rank</p><h1>When were these recordings published?</h1><p class="intro">Date-stamped publication and availability metadata, upload fallbacks and listing-age estimates remain distinct. These dates describe the selected public uploads, not necessarily when a performance was recorded.</p></div>
<dl class="snapshot"><div><dt>Report generated · UTC</dt><dd>{e(data['generated_at'])}</dd></div><div><dt>Scope</dt><dd>Latest 20 regular uploads per creator</dd></div></dl></div>
<dl class="metrics timeline-metrics" aria-label="Full selection date coverage">{metrics}</dl><p class="note">Dates and durations do not determine eligibility. This is a capped selection, not each creator’s complete publication history.</p>
<div class="section-head"><h2 id="timeline-heading" tabindex="-1">Date distribution</h2><a class="download" href="recording-dates.csv" download>Download full recording dates CSV</a></div>
<div id="controls" class="filters timeline-controls" hidden><div class="field"><label for="search">Search title, ID or method</label><input id="search" type="search" autocomplete="off" aria-controls="date-table"></div>
<div class="field"><label for="creator">Creator</label><select id="creator" aria-controls="date-table"><option value="">All creators</option>{options}</select></div><div class="field"><label for="method">Date evidence</label><select id="method" aria-controls="date-table"><option value="">All evidence methods</option>{methods}</select></div>
<div class="period-controls"><div class="field"><label for="period">Calendar bins</label><select id="period" aria-controls="chart"><option value="year">Year</option><option value="month">Month</option></select></div><button id="clear" type="button">Clear filters</button></div></div>
<p class="legend">{legends}</p><p class="note">An interval enters a year or month only when its entire inclusive window fits. Crossing-boundary estimates are counted as ambiguous; no midpoint is assigned. Only nonempty calendar bins appear below.</p>
<p id="date-status" class="result-count" role="status" aria-live="polite">{len(rows):,} selected: {year['placed']:,} placed by year, {year['ambiguous']:,} year-ambiguous interval estimates, {year['unknown']:,} unknown.</p>
<div id="chart" class="chart" role="region" aria-label="Selected recording date distribution" tabindex="0">{_chart(year)}</div><p class="note">{e(calnote)} Calibration does not turn an estimated interval into an exact date.</p>
<section aria-labelledby="records-heading"><div class="section-head"><h2 id="records-heading">Recording-level date evidence</h2></div><p class="note">Every selected recording stays visible, including ambiguous or unresolved dates. Source links and evidence checksums identify the retained metadata; this page makes no source requests.</p>
<div class="table-wrap"><table id="date-table" class="date-table" role="table"><caption>Selected recording date evidence · rank is one-based · calendar dates and observation clocks use UTC</caption><thead role="rowgroup"><tr role="row">{''.join('<th role="columnheader" scope="col">'+x+'</th>' for x in ('Recording','Creator','Date / interval','Method','Public source','Chart placement'))}</tr></thead>
<tbody role="rowgroup">{''.join(out)}<tr id="empty-row" role="row" hidden><td role="cell" colspan="6" class="empty">No recordings match these filters.</td></tr></tbody></table></div></section>
<noscript><p class="static-note">The year chart and all recording links are available without JavaScript. Interactive calendar bins and filters require JavaScript; the adjacent full CSV preserves every date field.</p></noscript>
</main><footer><p>Selection SHA-256 <code class="full-hash">{data['selection_sha256']}</code></p><p>Dates are metadata evidence, not verified recording-session dates. Unknown does not mean no publication. No present-day rate, availability or future completion time is inferred.</p></footer></div><script>{SCRIPT}</script></body></html>'''

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(argv);report=json.loads(args.report.read_text(encoding='utf-8-sig'));html=render(report)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(html,encoding='utf8',newline='\n')
    print(json.dumps({'records':len(report['records']),'output_written':True}))

if __name__=='__main__':main()
