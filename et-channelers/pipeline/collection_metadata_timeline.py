"""Offline, uncertainty-aware UI for Root-produced primary-recording date rows.

render(report) returns complete HTML. Date evidence and intervals are inputs;
this renderer never parses relative ages, chooses midpoints or fetches sources.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit,parse_qs

from .collection_failure_dashboard import STYLE as BASE_STYLE
from .dataset_timeline import spreadsheet_cell

METHODS={'publication':'Publication date','availability':'Availability metadata',
         'upload':'Upload fallback','relative':'Relative interval','unknown':'Unknown'}
SERIES=(('metadata','Publication / availability metadata'),('upload','Upload fallback'),('relative','Interval estimate'))
# The selection rule takes at most this many of each creator's newest public uploads; some creators have fewer.
SELECTION_CAP=20

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


def day_window(records, start, end):
    """A renderer view over the evidence builder's authoritative daily counts."""
    from .regular_recording_dates import daily_counts, DAY_FIELDS
    start, end = _day(start), _day(end)
    _need(start is not None and end is not None and start <= end, 'ordered daily window required')
    # Older compatible rows can carry exact_day without redundant equal bounds.
    prepared = [{**row, 'date_min': row['date_min'] or row['exact_day'],
                 'date_max': row['date_max'] or row['exact_day']} for row in records]
    counts = {row['date']: row for row in daily_counts(prepared)}
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    days = [counts.get((first+timedelta(days=i)).isoformat(),
                      {'date': (first+timedelta(days=i)).isoformat(), **{key: 0 for key in DAY_FIELDS[1:]}})
            for i in range((last-first).days+1)]
    assigned = possible = unknown = 0
    for row in prepared:
        lo, hi = row['date_min'], row['date_max']
        if not lo:
            unknown += 1
        elif lo <= end and hi >= start:
            if lo == hi:
                assigned += 1
            else:
                possible += 1
    return {'days': days, 'start': start, 'end': end, 'assigned': assigned,
            'possible_unique': possible, 'intersecting_unique': assigned+possible,
            'unknown': unknown, 'selected': len(records)}


def _next_month(key, step=1):
    index = int(key[:4])*12 + int(key[5:7]) - 1 + step
    return f'{index//12:04d}-{index%12+1:02d}'


def _month_last_day(key):
    return (date.fromisoformat(_next_month(key)+'-01')-timedelta(days=1)).isoformat()


def period_counts(records, start, end):
    """Exact days and estimated windows that touch one inclusive UTC period.

    An exact day, or an estimated window lying wholly inside the period, is
    definite. A window that also reaches outside the period is counted apart
    in every period it touches, so those counts must never be summed."""
    start, end = _day(start), _day(end)
    _need(start is not None and end is not None and start <= end, 'ordered period required')
    exact = window = crossing = 0; definite = set(); possible = set()
    for row in records:
        low = row['exact_day'] or row['date_min']; high = row['exact_day'] or row['date_max']
        if not low or high < start or low > end:
            continue
        if row['exact_day']:
            exact += 1; definite.add(row['channel_dir'])
        elif start <= low and high <= end:
            window += 1; definite.add(row['channel_dir'])
        else:
            crossing += 1; possible.add(row['channel_dir'])
    return {'start': start, 'end': end, 'exact': exact, 'window': window, 'crossing': crossing,
            'creators': len(definite), 'creators_upper': len(definite | possible)}


def month_overview(records, last_day, recent=12):
    """Every calendar month in the recent run, and each earlier month that holds a date.

    Each exact day and each window inside one month is placed in exactly one
    month; a month-crossing window stays apart and is reconciled once."""
    last_day = _day(last_day); _need(last_day is not None and recent >= 1, 'report day and recent months required')
    dated = [row for row in records if row['exact_day'] or row['date_min']]
    lows = [row['exact_day'] or row['date_min'] for row in dated]
    highs = [row['exact_day'] or row['date_max'] for row in dated]
    final = max([last_day] + highs)[:7]; first_recent = _next_month(last_day[:7], 1-recent)
    key = min([first_recent] + lows)[:7]; months = []
    while key <= final:
        row = {'month': key, **period_counts(records, key+'-01', _month_last_day(key))}
        row['recent'] = key >= first_recent
        row['partial_to'] = last_day if key == last_day[:7] and last_day < row['end'] else None
        if row['recent'] or row['exact'] or row['window'] or row['crossing']:
            months.append(row)
        key = _next_month(key)
    crossing = sum(1 for row in dated if not row['exact_day'] and row['date_min'][:7] != row['date_max'][:7])
    _need(sum(row['exact']+row['window'] for row in months)+crossing+len(records)-len(dated) == len(records),
          'month overview does not reconcile')
    earlier = [row for row in months if not row['recent']]
    return {'months': months, 'first_recent': first_recent, 'crossing_unique': crossing,
            'unknown': len(records)-len(dated), 'first_dated': min(lows) if lows else None,
            'earlier': period_counts(records, min(lows), (date.fromisoformat(first_recent+'-01')-timedelta(days=1)).isoformat())
            if lows and min(lows) < first_recent+'-01' else None,
            'earlier_max_creators': max((row['creators_upper'] for row in earlier), default=0),
            'maximum': max((row['exact']+row['window']+row['crossing'] for row in months), default=0)}


def _ordinal_day(value):
    day = int(value[8:]); suffix = 'th' if 10 <= day % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f'{day}{suffix}'


def _month_list(rows, maximum, label):
    items = []
    for row in rows:
        partial = f' to {row["partial_to"]}' if row['partial_to'] else ''
        detail = (f'{row["month"]}{partial}: {row["exact"]:,} with an exact day; {row["window"]:,} estimated windows inside the month; '
                  f'{row["crossing"]:,} more windows cross into it from a neighbouring month; {row["creators"]:,} creators'
                  + (f', up to {row["creators_upper"]:,} counting crossing windows' if row['creators_upper'] > row['creators'] else '') + '.')
        segments = ''.join(f'<span class="segment {kind}" style="width:{100*count/max(1, maximum):.6f}%"></span>'
                           for kind, count in (('m-exact', row['exact']), ('relative', row['window']), ('possible', row['crossing'])) if count)
        window = f'{row["window"]:,}' + (f'<span class="subline">+{row["crossing"]:,} crossing</span>' if row['crossing'] else '')
        people = f'{row["creators"]:,}' + (f'<span class="subline">up to {row["creators_upper"]:,}</span>' if row['creators_upper'] > row['creators'] else '')
        month = row['month'] + (f'<span class="subline">to the {_ordinal_day(row["partial_to"])}</span>' if row['partial_to'] else '')
        items.append(f'<li class="month-row"><span class="month-cells" aria-hidden="true"><span class="m-month">{month}</span>'
                     f'<span class="bar">{segments}</span><span class="m-num">{row["exact"]:,}</span><span class="m-num">{window}</span>'
                     f'<span class="m-num">{people}</span></span><span class="sr-only">{detail}</span></li>')
    head = ('<div class="month-row month-head" aria-hidden="true"><span class="month-cells"><span>Month</span><span>Recordings</span>'
            '<span class="m-num">Exact day</span><span class="m-num">Window</span><span class="m-num">Creators</span></span></div>')
    return head + f'<ol class="month-list" aria-label="{escape(label, quote=True)}">' + ''.join(items) + '</ol>'


def _month_panel(rows, generated_at, creator_count):
    """A static month-by-month view; it covers the whole selection and ignores the filters."""
    last_day = generated_at[:10]; overview = month_overview(rows, last_day)
    observed = sorted({row['observed_at'][:10] for row in rows if row['observed_at']})
    listing_day = observed[-1] if observed else last_day
    listing = ('the day the channel listings were read' if len(observed) <= 1 else
               'the day the last channel listings were read')
    weeks = period_counts(rows, (date.fromisoformat(listing_day)-timedelta(days=27)).isoformat(), listing_day)
    exact_days = sorted(row['exact_day'] for row in rows if row['exact_day'])
    share = 100*(weeks['exact']+weeks['window'])/max(1, len(rows))
    lead = (f'<p><strong>{weeks["exact"]+weeks["window"]:,} of the {len(rows):,} recordings ({share:.0f}%)</strong> are dated inside the four weeks '
            f'ending on {listing_day}, {listing} ({weeks["start"]} to {weeks["end"]}, UTC): {weeks["exact"]:,} by an exact day and {weeks["window"]:,} by an estimated '
            f'window lying wholly inside those weeks. They come from {weeks["creators"]:,} of the {creator_count:,} creators.'
            + (f' Half of the {len(exact_days):,} exact days fall on or after {exact_days[len(exact_days)//2]}.' if exact_days else '') + '</p>')
    recent = [row for row in overview['months'] if row['recent']]; earlier = [row for row in overview['months'] if not row['recent']]
    span = period_counts(rows, recent[0]['start'], recent[-1]['end'])
    held = (f'The {len(recent):,} months from {recent[0]["month"]} to {recent[-1]["month"]} hold {span["exact"]+span["window"]:,} of the '
            f'{len(rows):,} recordings ({100*(span["exact"]+span["window"])/max(1, len(rows)):.0f}%) by an exact day or a window wholly inside them, '
            f'from {span["creators"]:,} of the {creator_count:,} creators.')
    full = sum(1 for count in Counter(row['channel_dir'] for row in rows).values() if count >= SELECTION_CAP)
    other = creator_count - full; verb = lambda n: 'contributes' if n == 1 else 'contribute'
    if full == creator_count:
        reach = f'all {creator_count:,} creators contribute {SELECTION_CAP}' if creator_count > 1 else f'the creator contributes {SELECTION_CAP}'
    else:
        reach = (f'{full:,} of the {creator_count:,} creators {verb(full)} {SELECTION_CAP}; '
                 f'the other {other:,} {verb(other)} fewer')
    summary = ''
    if overview['earlier']:
        before = overview['earlier']
        summary = (f'<p class="note month-earlier">Earlier months, {before["start"][:7]} to {_next_month(overview["first_recent"], -1)}: '
                   f'{before["exact"]:,} exact days and {before["window"]:,} estimated windows lying wholly inside that period, from {before["creators"]:,} creators. '
                   f'No earlier month holds more than {overview["earlier_max_creators"]:,} creators.</p>'
                   f'<details class="month-details"><summary>Show the {len(earlier):,} earlier months that hold a date</summary>'
                   f'<div class="month-scroll" tabindex="0" role="region" aria-label="Earlier months">'
                   + _month_list(earlier, overview['maximum'], 'Earlier calendar months with a date, oldest first') +
                   '<p class="note">Months with no dated recording are left out.</p></div></details>')
    legend = ('<p class="legend month-legend"><span><i class="swatch m-exact" aria-hidden="true"></i>Exact day</span>'
              '<span><i class="swatch relative" aria-hidden="true"></i>Estimated window inside the month</span>'
              '<span><i class="swatch possible" aria-hidden="true"></i>Window crossing a month boundary · counted in each month it touches</span></p>')
    return (f'<section class="month-panel" aria-labelledby="month-heading"><div class="section-head"><h2 id="month-heading" tabindex="-1">Recordings and creators by month</h2></div>'
            f'<div class="month-grid"><div class="month-copy"><p class="intro">Each creator contributes up to their {SELECTION_CAP} newest public uploads ({reach}), '
            f'so the selection is not spread evenly in time. A creator who uploads often reaches {SELECTION_CAP} within weeks; one who uploads rarely reaches back years. '
            f'{held}</p>{lead}{legend}<p class="note">A creator counts in a month when one of their recordings has an exact day '
            'or a whole estimated window there; “up to” adds creators known only from crossing windows. Crossing windows may belong to either month and '
            'must not be summed. This panel covers the full selection; the filters below do not change it.</p></div>'
            f'<div class="chart month-chart"><p class="axis">The {len(recent):,} calendar months to the report date · linear scale <span class="nowrap">0–{overview["maximum"]:,}</span> recordings per month</p>'
            + _month_list(recent, overview['maximum'], f'Recordings and creators per calendar month, {recent[0]["month"]} to {recent[-1]["month"]}') +
            summary + '</div></div></section>')


def _daily_chart(result):
    maximum = max((row['possible_total'] for row in result['days']), default=0)
    bars = []
    for row in result['days']:
        series = (('metadata', row['publication']+row['availability'], 'Publication / availability'),
                  ('upload', row['upload'], 'Upload fallback'),
                  ('relative', row['relative_single_day'], 'Single-day interval'),
                  ('possible', row['relative_possible_extra'], 'Possible multi-day overlap'))
        detail = (f"{row['date']}: {row['assigned_total']} assigned; at most {row['possible_total']} "
                  f"including {row['relative_possible_extra']} possible multi-day overlaps")
        segments = ''.join(f'<span class="segment {kind}" style="width:{100*count/max(1,maximum):.6f}%" title="{label}: {count}"></span>'
                           for kind, count, label in series if count)
        bars.append(f'<li class="bin day-bin"><button type="button" class="day-link" data-day="{row["date"]}" aria-label="{detail}; show evidence">{row["date"]}</button>'
                    f'<span class="bar" aria-hidden="true">{segments}</span><strong>{row["assigned_total"]}<span class="subline">up to {row["possible_total"]}</span></strong>'
                    f'<span class="sr-only">{detail}</span></li>')
    return (f'<p class="axis" id="chart-scale">Daily assigned count / inclusive upper bound · linear scale 0–{maximum:,}. '
            'Possible overlaps are not additive across days.</p><ol class="bin-list daily-list" tabindex="0" aria-label="UTC calendar days including zero counts">'
            + ''.join(bars)+'</ol>')

def _chart(result, scale_id='chart-scale'):
    maximum=max((row['total'] for row in result['bins']),default=0);bars=[]
    for row in result['bins']:
        label=', '.join(f'{name}: {row[kind]}' for kind,name in SERIES)
        segments=''.join(f'<span class="segment {kind}" style="width:{100*row[kind]/maximum:.6f}%" title="{escape(name)}: {row[kind]}"></span>' for kind,name in SERIES if row[kind])
        bars.append(f'<li class="bin"><span class="period">{row["period"]}</span><span class="bar" aria-hidden="true">{segments}</span><strong>{row["total"]:,}</strong><span class="sr-only">{label}</span></li>')
    return f'<p class="axis" id="{scale_id}">Recordings per period · linear count scale, 0–{maximum:,}</p><ol class="bin-list" tabindex="0" aria-label="Nonempty calendar bins">{"".join(bars)}</ol>'+('' if bars else '<p class="empty">No records can be placed in a calendar bin for this filter.</p>')

EXTRA_STYLE=r'''
.timeline-metrics{grid-template-columns:repeat(5,minmax(0,1fr))}.timeline-metrics .metric dd{font-size:2.3rem}.legend{display:flex;flex-wrap:wrap;gap:.7rem 1.4rem;font-size:.84rem;margin:1rem 0}.swatch{display:inline-block;width:1rem;height:1rem;margin-right:.4rem;vertical-align:-.15rem;border:1px solid var(--ink)}.metadata{background:var(--forest)}.upload{background:#75648b}.relative{background-color:#c99a4e;background-image:repeating-linear-gradient(45deg,transparent,transparent 3px,#513c1e 3px,#513c1e 4px)}.chart{background:var(--paper);border:1px solid var(--line);border-radius:5px;padding:1rem}.axis{color:var(--muted);font-size:.85rem}.bin-list{list-style:none;padding:0;margin:0;max-height:30rem;overflow:auto}.bin{display:grid;grid-template-columns:5rem minmax(4rem,1fr) 4rem;align-items:center;gap:.8rem;margin:.45rem 0;min-height:1.5rem;font-size:.85rem}.bin strong{text-align:right;font-variant-numeric:tabular-nums}.bar{display:flex;min-width:0;height:1.15rem;background:var(--canvas)}.segment{height:100%;display:block}.period{font-variant-numeric:tabular-nums}.timeline-controls{grid-template-columns:2fr 1fr 1fr}.timeline-controls .period-controls{grid-column:1/-1;display:flex;align-items:end;flex-wrap:wrap;gap:.8rem}.timeline-controls .period-controls .field{min-width:11rem}.evidence-cell{min-width:13rem;max-width:24rem}.evidence-cell p{margin:.35rem 0}.date-range{font-variant-numeric:tabular-nums}.hash{font: .75rem ui-monospace,Consolas,monospace;overflow-wrap:anywhere}.full-hash{display:block;max-width:55ch;overflow-wrap:anywhere}.date-table td{overflow-wrap:anywhere}.date-table summary{min-height:24px;cursor:pointer}.source-link{display:inline-flex;min-height:24px;align-items:center}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}.static-note{font-size:.9rem;color:var(--muted)}
.possible{background:repeating-linear-gradient(90deg,transparent,transparent 3px,#8e8069 3px,#8e8069 4px);outline:1px dashed var(--muted);outline-offset:-1px}.day-bin{grid-template-columns:6.5rem minmax(3rem,1fr) 4.8rem;min-height:2.1rem}.day-bin strong .subline{font-size:.73rem;font-weight:400;white-space:nowrap}.day-link,.month-link{font:inherit;color:var(--forest);background:none;border:0;text-decoration:underline;text-underline-offset:.18rem;padding:.4rem .1rem;text-align:left;cursor:pointer;min-height:32px}.day-link[aria-pressed="true"]{font-weight:800;outline:2px solid var(--forest)}.day-controls{grid-column:1/-1;display:flex;flex-wrap:wrap;align-items:end;gap:.7rem}.day-controls .field{min-width:9rem;flex:1}.day-buttons{display:flex;flex-wrap:wrap;gap:.4rem}.day-buttons button{min-height:40px;padding:.45rem .7rem}.day-buttons button[aria-pressed="true"]{background:var(--forest);color:var(--paper)}.range-error{color:#a02121;flex-basis:100%;margin:.25rem 0}.day-selection{padding:.7rem 0;border-bottom:1px solid var(--line)}.day-selection button{margin-left:.6rem}.download-links{display:flex;gap:.8rem;flex-wrap:wrap}.daily-legend{margin-bottom:.5rem}.static-overview{margin-top:1rem}.static-overview summary{cursor:pointer;padding:.5rem 0}
@media(max-width:1100px){.timeline-metrics{grid-template-columns:repeat(3,minmax(0,1fr))}.timeline-metrics .metric{padding-left:1rem;border-left:1px solid var(--line)}.timeline-metrics .metric:nth-child(3n+1){border-left:0;padding-left:0}.timeline-controls{grid-template-columns:1fr 1fr}.timeline-controls>.field:first-child{grid-column:1/-1}.evidence-cell{min-width:0;max-width:none}.bin{grid-template-columns:4.3rem minmax(3rem,1fr) 3rem;gap:.5rem}}
@media(max-width:550px){.timeline-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.timeline-metrics .metric{border-left:1px solid var(--line)!important;padding-left:1rem!important}.timeline-metrics .metric:nth-child(2n+1){border-left:0!important;padding-left:0!important}.timeline-controls{grid-template-columns:1fr}.chart{padding:.7rem}.bin{font-size:.8rem}.legend{display:grid;gap:.5rem}}
.month-panel{margin:.5rem 0}.month-grid{display:grid;grid-template-columns:minmax(0,25rem) minmax(0,1fr);gap:1.25rem 2rem;align-items:start}.month-copy .intro{margin-top:0}.month-legend{display:grid;gap:.45rem}.m-exact{background:var(--forest)}.month-list{list-style:none;padding:0;margin:0}.month-row{margin:.25rem 0}.nowrap{white-space:nowrap}.month-cells{display:grid;grid-template-columns:5rem minmax(4rem,1fr) 4rem 5.6rem 5rem;align-items:center;gap:.8rem;min-height:2.05rem;font-size:.85rem;font-variant-numeric:tabular-nums}.month-head .month-cells{color:var(--muted);font-size:.78rem;min-height:0;padding-bottom:.35rem;border-bottom:1px solid var(--line)}.m-num{text-align:right}.m-num .subline,.m-month .subline{font-size:.73rem;margin-top:0;white-space:nowrap}.month-earlier{margin:1rem 0 .25rem}.month-details summary{cursor:pointer;padding:.5rem 0;min-height:24px}.month-scroll{max-height:26rem;overflow:auto;padding-right:.25rem}
@media(max-width:1100px){.month-grid{grid-template-columns:1fr}}
@media(max-width:550px){.month-cells{grid-template-columns:4.2rem minmax(2.4rem,1fr) 2.7rem 4.3rem 3.9rem;gap:.35rem;font-size:.8rem}.month-head .month-cells{font-size:.72rem}}
@media(max-width:550px){.day-bin{grid-template-columns:5.8rem minmax(2rem,1fr) 4.1rem;gap:.35rem}.day-controls .field{min-width:0;width:calc(50% - .7rem)}.day-link{font-size:.76rem}.day-buttons{width:100%}.download-links{font-size:.85rem}.section-head{flex-wrap:wrap}}
'''

SCRIPT=r'''
(() => {
 const table=document.getElementById('date-table'), rows=Array.from(table.querySelectorAll('tr[data-video]'));
 const creator=document.getElementById('creator'),method=document.getElementById('method'),search=document.getElementById('search'),period=document.getElementById('period');
 const kinds=[['metadata','Publication / availability metadata'],['upload','Upload fallback'],['relative','Interval estimate']];
 const chart=document.getElementById('chart'),status=document.getElementById('date-status');
 const from=document.getElementById('date-from'),to=document.getElementById('date-to'),dayControls=document.getElementById('day-controls');
 const error=document.getElementById('range-error'),selection=document.getElementById('day-selection');
 const initialFrom=from.value,initialTo=to.value,DAY=86400000,PAGE_DAYS=366;let selectedDay='',dayPage=0;
 const ordinal=s=>Date.parse(s+'T00:00:00Z')/DAY;
 const iso=n=>new Date(n*DAY).toISOString().slice(0,10);
 function el(tag,text,cls){const x=document.createElement(tag);if(text!==undefined)x.textContent=text;if(cls)x.className=cls;return x;}
 function baseMatch(row){const query=search.value.trim().toLocaleLowerCase();return (!creator.value||row.dataset.creator===creator.value)&&(!method.value||row.dataset.method===method.value)&&(!query||row.dataset.search.toLocaleLowerCase().includes(query));}
 function overlaps(row,start,end){return row.dataset.low&&row.dataset.low<=end&&row.dataset.high>=start;}
 function daily(values){
  const first=ordinal(from.value),last=ordinal(to.value),pages=Math.ceil((last-first+1)/PAGE_DAYS);
  dayPage=Math.max(0,Math.min(dayPage,pages-1));const visibleFirst=first+dayPage*PAGE_DAYS,visibleLast=Math.min(last,visibleFirst+PAGE_DAYS-1),days=[];let assigned=0,possible=0,unknown=0;
  for(let n=visibleFirst;n<=visibleLast;n++)days.push({date:iso(n),metadata:0,upload:0,relative:0,possible:0,total:0,upper:0});
  for(const row of values){const low=row.dataset.low,high=row.dataset.high,type=row.dataset.method;
   if(!low){unknown++;continue;}if(!overlaps(row,from.value,to.value))continue;
   if(low===high){assigned++;const at=ordinal(low);if(at>=visibleFirst&&at<=visibleLast){const count=days[at-visibleFirst];count[['publication','availability'].includes(type)?'metadata':type]++;count.total++;}}
   else {possible++;for(let n=Math.max(visibleFirst,ordinal(low));n<=Math.min(visibleLast,ordinal(high));n++)days[n-visibleFirst].possible++;}
  }
  for(const count of days)count.upper=count.total+count.possible;
  return {days,assigned,possible,unknown,pages,visibleFirst:iso(visibleFirst),visibleLast:iso(visibleLast)};
 }
 function chooseDay(day){selectedDay=selectedDay===day?'':day;draw();if(selectedDay)document.getElementById('records-heading').focus();}
 function drillMonth(key){const first=ordinal(key+'-01'),next=key.slice(5)==='12'?String(Number(key.slice(0,4))+1)+'-01-01':key.slice(0,5)+String(Number(key.slice(5))+1).padStart(2,'0')+'-01';
  from.value=iso(first);to.value=iso(Math.min(ordinal(next)-1,ordinal(initialTo)));period.value='day';selectedDay='';dayPage=0;draw();from.focus();}
 function draw(){
  const values=rows.filter(baseMatch);const bins=new Map();let selected=values.length,ambiguous=0,unknown=0;
  dayControls.hidden=period.value!=='day';document.getElementById('possible-legend').hidden=period.value!=='day';
  document.getElementById('day-pages').hidden=true;
  if(period.value==='day'&&(!from.value||!to.value||from.value>to.value||to.value>initialTo)){
   error.hidden=false;error.textContent='Choose an ordered daily date range ending no later than the report date.';return;
  }error.hidden=true;
  if(period.value!=='day')selectedDay='';
  for(const row of rows)row.hidden=!baseMatch(row)||(!!selectedDay&&!overlaps(row,selectedDay,selectedDay));
  selection.hidden=!selectedDay;document.getElementById('selected-day-text').textContent=selectedDay?'Evidence for '+selectedDay+': exact and single-day dates, plus possible overlapping intervals.':'';
  document.getElementById('day-permalink').setAttribute('href','?date='+selectedDay);
  for(const button of document.querySelectorAll('[data-window]'))button.setAttribute('aria-pressed',String(Number(button.dataset.window)===ordinal(to.value)-ordinal(from.value)+1));
  if(period.value==='day'){
   const result=daily(values),maximum=Math.max(0,...result.days.map(x=>x.upper));
   document.getElementById('day-pages').hidden=result.pages<=1;
   document.getElementById('visible-days').textContent='Showing '+result.visibleFirst+' to '+result.visibleLast+' · page '+(dayPage+1)+' of '+result.pages+'. Summary counts cover the full requested range.';
   document.getElementById('previous-days').disabled=dayPage===0;document.getElementById('next-days').disabled=dayPage+1>=result.pages;
   const axis=el('p','Daily assigned count / inclusive upper bound · linear scale 0–'+maximum.toLocaleString()+'. Possible overlaps are not additive across days.','axis');axis.id='chart-scale';
   const list=el('ol',undefined,'bin-list daily-list');list.tabIndex=0;list.setAttribute('aria-label','UTC calendar days including zero counts');
   for(const count of result.days){
    const detail=count.date+': '+count.total+' assigned; at most '+count.upper+' including '+count.possible+' possible multi-day overlaps';
    const item=el('li',undefined,'bin day-bin'),button=el('button',count.date,'day-link'),bar=el('span',undefined,'bar');
    button.type='button';button.dataset.day=count.date;button.setAttribute('aria-label',detail+'; show evidence');button.setAttribute('aria-pressed',String(selectedDay===count.date));button.addEventListener('click',()=>chooseDay(count.date));bar.setAttribute('aria-hidden','true');
    for(const [kind,label] of [...kinds,['possible','Possible multi-day overlap']])if(count[kind]){const s=el('span',undefined,'segment '+kind);s.style.width=String(100*count[kind]/Math.max(1,maximum))+'%';s.title=label+': '+count[kind];bar.append(s);}
    const total=el('strong',String(count.total));total.append(el('span','up to '+count.upper,'subline'));
    item.append(button,bar,total,el('span',detail,'sr-only'));list.append(item);
   }
   chart.replaceChildren(axis,list);
   status.textContent=selected.toLocaleString()+' selected in filters; '+from.value+' to '+to.value+': '+result.assigned.toLocaleString()+' assigned a single day, '+result.possible.toLocaleString()+' distinct multi-day intervals could intersect this window; '+result.unknown.toLocaleString()+' unknown. Possible-day upper bounds must not be summed.';
  } else {
   for(const row of values){const key=row.dataset[period.value],type=row.dataset.method;
   if(!key){if(type==='relative')ambiguous++;else unknown++;continue;}
   if(!bins.has(key))bins.set(key,{metadata:0,upload:0,relative:0,total:0});const count=bins.get(key);count[['publication','availability'].includes(type)?'metadata':type]++;count.total++;
   }
  const placed=selected-ambiguous-unknown,maximum=Math.max(0,...Array.from(bins.values(),x=>x.total));
  const axis=el('p','Recordings per period · linear count scale, 0–'+maximum.toLocaleString(),'axis');axis.id='chart-scale';
  const list=el('ol',undefined,'bin-list');list.tabIndex=0;list.setAttribute('aria-label','Nonempty calendar '+period.value+' bins');
  for(const [key,count] of Array.from(bins).sort((a,b)=>a[0].localeCompare(b[0]))){
   const item=el('li',undefined,'bin'),bar=el('span',undefined,'bar');bar.setAttribute('aria-hidden','true');
   for(const [kind,label] of kinds)if(count[kind]){const segment=el('span',undefined,'segment '+kind);segment.style.width=String(100*count[kind]/maximum)+'%';segment.title=label+': '+count[kind];bar.append(segment);}
   const label=el(period.value==='month'?'button':'span',key,period.value==='month'?'period month-link':'period');if(period.value==='month'){label.type='button';label.setAttribute('aria-label','Zoom to days in '+key);label.addEventListener('click',()=>drillMonth(key));}
   item.append(label,bar,el('strong',count.total.toLocaleString()),el('span',kinds.map(([k,l])=>l+': '+count[k]).join(', '),'sr-only'));list.append(item);
  }
  chart.replaceChildren(axis,list);if(!bins.size)chart.append(el('p','No records can be placed in a calendar bin for this filter.','empty'));
  status.textContent=selected.toLocaleString()+' selected in this view: '+placed.toLocaleString()+' placed by '+period.value+', '+ambiguous.toLocaleString()+' '+period.value+'-ambiguous interval estimates, '+unknown.toLocaleString()+' unknown. Missing and ambiguous dates stay in the table and CSV.';
  }
  document.getElementById('empty-row').hidden=rows.some(row=>!row.hidden);
 }
 for(const control of [creator,method,period])control.addEventListener('change',draw);search.addEventListener('input',draw);
 for(const input of [from,to])input.addEventListener('change',()=>{selectedDay='';dayPage=0;draw();});
 for(const button of document.querySelectorAll('[data-window]'))button.addEventListener('click',()=>{const end=ordinal(to.value||initialTo);from.value=iso(end-Number(button.dataset.window)+1);to.value=iso(end);selectedDay='';dayPage=0;draw();});
 for(const [id,direction] of [['previous-window',-1],['next-window',1]])document.getElementById(id).addEventListener('click',()=>{const length=ordinal(to.value)-ordinal(from.value)+1;if(!(length>0))return;const end=Math.min(ordinal(initialTo),ordinal(to.value)+direction*length);from.value=iso(end-length+1);to.value=iso(end);selectedDay='';dayPage=0;draw();});
 for(const [id,direction] of [['previous-days',-1],['next-days',1]])document.getElementById(id).addEventListener('click',()=>{dayPage+=direction;selectedDay='';draw();chart.focus();});
 document.getElementById('clear-day').addEventListener('click',()=>{selectedDay='';draw();chart.focus();});
 document.getElementById('clear').addEventListener('click',()=>{creator.value='';method.value='';search.value='';period.value='day';from.value=initialFrom;to.value=initialTo;selectedDay='';dayPage=0;draw();search.focus();});
 const requested=new URLSearchParams(location.search).get('date');
 if(requested&&/^\d{4}-\d{2}-\d{2}$/.test(requested)&&Number.isFinite(ordinal(requested))&&iso(ordinal(requested))===requested){
  const bounds=rows.filter(row=>row.dataset.low),low=bounds.map(row=>row.dataset.low).sort()[0],high=bounds.map(row=>row.dataset.high).sort().pop();
  if(low&&high){const first=ordinal(low),last=Math.min(ordinal(high),ordinal(initialTo)),chosen=Math.max(first,Math.min(last,ordinal(requested)));
   selectedDay=iso(chosen);const end=Math.min(last,Math.max(first,chosen-14)+29);from.value=iso(Math.max(first,end-29));to.value=iso(end);
  }
 }
 draw();document.getElementById('controls').hidden=false;
})();
'''

def render(report)->str:
    data=_validated(report);rows=data['records'];e=lambda x:escape(str(x),quote=True)
    counts=Counter(r['date_method'] for r in rows);year=aggregate(rows,'year');out=[]
    last_day=data['generated_at'][:10]
    first_day=(date.fromisoformat(last_day)-timedelta(days=29)).isoformat()
    daily=day_window(rows,first_day,last_day)
    for r in rows:
        attrs={'video':r['video_id'],'creator':r['channel_dir'],'method':r['date_method'],'year':r['year_bin'] or '',
               'month':r['month_bin'] or '', 'low':r['date_min'] or r['exact_day'] or '',
               'high':r['date_max'] or r['exact_day'] or '',
               'search':' '.join([r['video_id'],r['title'],r['creator'],r['method_detail']])}
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
    guarded=sum(spreadsheet_cell(r['video_id'])!=r['video_id'] for r in rows)
    csvnote=(f' In the full CSV, the {guarded:,} {"ID that begins" if guarded==1 else "IDs that begin"} with a hyphen {"carries" if guarded==1 else "carry"} a leading apostrophe '
             'so spreadsheets keep them as text; remove it before matching IDs.' if guarded else '')
    observed=sorted({r['observed_at'][:10] for r in rows if r['observed_at']})
    listed=(observed[0] if len(observed)==1 else f'{observed[0]} to {observed[-1]}') if observed else 'Not recorded'
    calibration=data['calibration'];calnote=(f'Calibration: {calibration["within_interval"]:,} of {calibration["compared"]:,} date-stamped comparisons fell inside the saved listing-age interval.' if calibration['compared'] else 'No interval calibration comparisons were supplied.')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Publication metadata timeline · Latest 20+ videos</title><style>{BASE_STYLE}{EXTRA_STYLE}</style></head>
<body><a class="skip" href="#timeline-heading">Skip to date distribution</a><div class="page"><header class="masthead"><span class="wordmark">Channeling research archive</span><span class="edition">Latest 20+ videos · metadata timeline</span></header>
<main><div class="hero"><div><p class="eyebrow">Public regular uploads · selected by tab rank</p><h1>When were these recordings published?</h1><p class="intro">Date-stamped publication and availability metadata, upload fallbacks and listing-age estimates remain distinct. These dates describe the selected public uploads, not necessarily when a performance was recorded.</p></div>
<dl class="snapshot"><div><dt>Report generated · UTC</dt><dd>{e(data['generated_at'])}</dd></div><div><dt>Channel listings read · UTC</dt><dd>{e(listed)}</dd></div><div><dt>Scope</dt><dd>Up to the newest {SELECTION_CAP} public Videos-tab uploads per creator</dd></div></dl></div>
<dl class="metrics timeline-metrics" aria-label="Full selection date coverage">{metrics}</dl><p class="note">Dates and durations do not determine eligibility. This is a capped selection, not each creator’s complete publication history.</p>
{_month_panel(rows,data['generated_at'],len(data['creators']))}
<div class="section-head"><h2 id="timeline-heading" tabindex="-1">Date distribution</h2><div class="download-links"><a class="download" href="dates-by-day.csv" download>Download daily counts CSV</a><a class="download" href="recording-dates.csv" download>Download full recording dates CSV</a></div></div>
<p class="note">In the recording dates CSV, the ids that begin with a hyphen carry one leading apostrophe so that spreadsheets do not read them as formulas: strip it on read, or use <a href="recording-dates.json">recording-dates.json</a>, whose ids are written without it.</p>
<div id="controls" class="filters timeline-controls" hidden><div class="field"><label for="search">Search title, ID or method</label><input id="search" type="search" autocomplete="off" aria-controls="date-table"></div>
<div class="field"><label for="creator">Creator</label><select id="creator" aria-controls="date-table"><option value="">All creators</option>{options}</select></div><div class="field"><label for="method">Date evidence</label><select id="method" aria-controls="date-table"><option value="">All evidence methods</option>{methods}</select></div>
<div class="period-controls"><div class="field"><label for="period">Calendar bins</label><select id="period" aria-controls="chart"><option value="day" selected>Day · zoomed window</option><option value="month">Month</option><option value="year">Year</option></select></div><button id="clear" type="button">Clear filters</button></div>
<div id="day-controls" class="day-controls"><div class="field"><label for="date-from">From · UTC</label><input id="date-from" type="date" value="{first_day}" max="{last_day}" aria-controls="chart"></div><div class="field"><label for="date-to">To · UTC</label><input id="date-to" type="date" value="{last_day}" max="{last_day}" aria-controls="chart"></div>
<div class="day-buttons" role="group" aria-label="Daily zoom window"><button type="button" data-window="7" aria-pressed="false">7 days</button><button type="button" data-window="30" aria-pressed="true">30 days</button><button type="button" data-window="90" aria-pressed="false">90 days</button><button id="previous-window" type="button" aria-label="Previous date window">← Previous</button><button id="next-window" type="button" aria-label="Next date window">Next →</button></div><p id="range-error" class="range-error" role="alert" hidden></p></div></div>
<nav id="day-pages" class="day-buttons" aria-label="Daily chart pages" hidden><p id="visible-days" role="status" aria-live="polite"></p><button id="previous-days" type="button" aria-label="Previous days page">Previous page</button><button id="next-days" type="button" aria-label="Next days page">Next page</button></nav>
<p class="legend">{legends}<span id="possible-legend"><i class="swatch possible" aria-hidden="true"></i>Possible multi-day overlap · upper bound only</span></p><p class="note">A daily assigned count includes date-stamped metadata, upload fallbacks and intervals contained in one UTC day. A multi-day interval can overlap several days: its possible daily counts must not be summed as distinct recordings. No midpoint is assigned. Year/month views place only whole-window estimates; click a month to zoom into its days.</p>
<p id="date-status" class="result-count" role="status" aria-live="polite">{len(rows):,} selected; {first_day} to {last_day}: {daily['assigned']:,} assigned a single day, {daily['possible_unique']:,} distinct multi-day intervals could intersect this window; {daily['unknown']:,} unknown. Possible-day upper bounds must not be summed.</p>
<div id="chart" class="chart" role="region" aria-label="Selected recording date distribution" tabindex="0">{_daily_chart(daily)}</div><p class="note">{e(calnote)} Calibration does not turn an estimated interval into an exact date.</p>
<details class="static-overview"><summary>All-year overview · no zoom</summary><div class="chart" aria-label="Full selection year overview">{_chart(year,'year-overview-scale')}</div></details>
<section aria-labelledby="records-heading"><div class="section-head"><h2 id="records-heading" tabindex="-1">Recording-level date evidence</h2></div><p class="note">The full table includes every selected recording. Creator, method and search filters apply throughout; clicking a day shows its definite dates and possible overlaps. The full CSV always preserves every row.{csvnote} Source links and evidence checksums identify retained metadata; this page makes no source requests.</p>
<p id="day-selection" class="day-selection" hidden><span id="selected-day-text"></span> <a id="day-permalink" href="?date={last_day}">Link to this UTC day</a><button id="clear-day" type="button">Show all dates</button></p>
<div class="table-wrap"><table id="date-table" class="date-table" role="table"><caption>Selected recording date evidence · rank is one-based · calendar dates and observation clocks use UTC</caption><thead role="rowgroup"><tr role="row">{''.join('<th role="columnheader" scope="col">'+x+'</th>' for x in ('Recording','Creator','Date / interval','Method','Public source','Chart placement'))}</tr></thead>
<tbody role="rowgroup">{''.join(out)}<tr id="empty-row" role="row" hidden><td role="cell" colspan="6" class="empty">No recordings match these filters.</td></tr></tbody></table></div></section>
<noscript><p class="static-note">This static chart shows the recent 30 UTC days ending on the report date. All recording links and an expandable year overview work without JavaScript. Date zoom, month drilldown and filters require JavaScript; both adjacent CSV files remain available.</p></noscript>
</main><footer><p>Selection SHA-256 <code class="full-hash">{data['selection_sha256']}</code></p><p>Dates are metadata evidence, not verified recording-session dates. Unknown does not mean no publication. No present-day rate, availability or future completion time is inferred.</p></footer></div><script>{SCRIPT}</script></body></html>'''

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(argv);report=json.loads(args.report.read_text(encoding='utf-8-sig'));html=render(report)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(html,encoding='utf8',newline='\n')
    print(json.dumps({'records':len(report['records']),'output_written':True}))

if __name__=='__main__':main()
