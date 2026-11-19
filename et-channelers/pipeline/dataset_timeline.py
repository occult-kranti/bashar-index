"""Public upload-date distribution for the selected newest20 sample; local inputs only.

Exact dates are optional saved-YouTube-metadata overrides. The original queue
estimate remains visible. This module never discovers or downloads source data.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import re

VIDEO = re.compile(r'[A-Za-z0-9_-]{11}\Z')
CHANNEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')
QUALITIES = ('exact', 'estimated', 'unknown')
VIDEO_FIELDS = ('video_id', 'channel_dir', 'channel_name', 'title', 'url', 'listing_rank',
                'upload_date', 'date_quality', 'original_estimated_date',
                'estimate_differs_from_exact', 'saved_audio', 'exact_date_source_sha256')
MONTH_FIELDS = ('month', 'record_count', 'exact_count', 'estimated_count', 'unknown_count',
                'saved_audio_count')


class TimelineError(ValueError):
    pass


def need(value, reason):
    if not value:
        raise TimelineError(reason)


def calendar_date(value, field):
    """Accept an explicit calendar day, never invent the missing month/day."""
    if value is None or value == '':
        return None
    need(isinstance(value, str), field + ' must be a calendar-day string')
    value = value.strip()
    if not value:
        return None
    if re.fullmatch(r'[0-9]{8}', value):
        value = value[:4] + '-' + value[4:6] + '-' + value[6:]
    need(bool(re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value)), field + ' is not an ISO calendar day')
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError:
        raise TimelineError(field + ' is not a valid calendar day') from None


def exact_dates(overlay, selected_ids):
    if overlay is None:
        return {}
    need(isinstance(overlay, dict) and overlay.get('schema_version') == 1 and
         isinstance(overlay.get('items'), list), 'unsupported exact-date overlay schema')
    result = {}
    for item in overlay['items']:
        need(isinstance(item, dict), 'invalid exact-date overlay item')
        video = item.get('video_id')
        need(isinstance(video, str) and video in selected_ids, 'exact-date overlay ID is outside the selected sample')
        date = calendar_date(item.get('upload_date'), 'exact upload_date')
        need(date is not None, 'exact-date overlay has no date')
        need(item.get('provenance') == 'saved_youtube_metadata', 'unsupported exact-date provenance')
        digest = item.get('source_sha256')
        need(isinstance(digest, str) and SHA.fullmatch(digest), 'exact-date evidence SHA256 is invalid')
        safe = {'upload_date': date, 'provenance': {'kind': 'saved_youtube_metadata', 'source_sha256': digest}}
        if video in result:
            need(result[video] == safe, 'conflicting exact-date overlay records')
        result[video] = safe
    return result


def build_timeline(rows, overlay=None, saved_audio_ids=None, *, generated_at=None):
    """One row per selected video; every aggregate reconciles to that grain."""
    need(isinstance(rows, list) and bool(rows), 'selected sample is empty')
    selected = {}; ranks = set(); names = {}; creator_sizes = Counter()
    for row in rows:
        need(isinstance(row, dict), 'invalid selected sample row')
        video, channel = row.get('video_id'), row.get('channel_dir')
        need(isinstance(video, str) and VIDEO.fullmatch(video) and video not in selected,
             'selected video IDs must be unique and valid')
        need(isinstance(channel, str) and CHANNEL.fullmatch(channel), 'invalid channel identifier')
        raw_rank = row.get('listing_rank')
        need(isinstance(raw_rank, (str, int)) and not isinstance(raw_rank, bool) and
             re.fullmatch(r'[0-9]+', str(raw_rank)), 'invalid listing rank')
        rank = int(raw_rank)
        need(0 <= rank < 20 and (channel, rank) not in ranks, 'duplicate or out-of-sample listing rank')
        ranks.add((channel, rank)); creator_sizes[channel] += 1
        need(creator_sizes[channel] <= 20, 'creator exceeds the selected20 sample')
        name = (row.get('source_channel_name') or row.get('channel_name') or
                row.get('channel') or row.get('primary_person_name') or channel)
        need(isinstance(name, str), 'invalid public channel name')
        name = name.strip() or channel
        need(channel not in names or names[channel] == name, 'conflicting channel names')
        names[channel] = name
        title = row.get('title', '')
        need(isinstance(title, str), 'invalid public title')
        estimate = calendar_date(row.get('upload_date_approx'), 'upload_date_approx')
        selected[video] = {'video_id': video, 'channel_dir': channel, 'channel_name': name,
                           'title': title, 'url': 'https://www.youtube.com/watch?v=' + video,
                           'listing_rank': rank, 'original_estimated_date': estimate}
    overrides = exact_dates(overlay, set(selected))
    if saved_audio_ids is not None:
        saved_audio_ids = set(saved_audio_ids)
        need(saved_audio_ids <= set(selected), 'audio coverage contains IDs outside the selected sample')
    records = []
    for video, row in selected.items():
        exact = overrides.get(video); estimate = row['original_estimated_date']
        date = exact['upload_date'] if exact else estimate
        records.append(dict(row, upload_date=date,
            date_quality='exact' if exact else 'estimated' if estimate else 'unknown',
            original_estimate_provenance='queue_upload_date_approx' if estimate else None,
            exact_date_provenance=exact['provenance'] if exact else None,
            estimate_differs_from_exact=bool(exact and estimate and exact['upload_date'] != estimate),
            saved_audio=video in saved_audio_ids if saved_audio_ids is not None else None))
    by_creator = defaultdict(list); by_month = defaultdict(list)
    for row in records:
        by_creator[row['channel_dir']].append(row)
        by_month[row['upload_date'][:7] if row['upload_date'] else 'unknown'].append(row)

    def counts(members):
        quality = Counter(row['date_quality'] for row in members)
        return {'record_count': len(members), **{key + '_count': quality[key] for key in QUALITIES},
                'saved_audio_count': sum(row['saved_audio'] is True for row in members)
                if saved_audio_ids is not None else None}

    creators = []
    for channel, members in sorted(by_creator.items(), key=lambda item: (names[item[0]].casefold(), item[0])):
        dates = sorted(row['upload_date'] for row in members if row['upload_date'])
        creators.append(dict(channel_dir=channel, channel_name=names[channel], **counts(members),
            earliest_upload_date=dates[0] if dates else None, latest_upload_date=dates[-1] if dates else None,
            span_days=(dt.date.fromisoformat(dates[-1]) - dt.date.fromisoformat(dates[0])).days if dates else None))
    monthly = [dict(month=month, **counts(by_month[month]))
               for month in sorted(by_month, key=lambda value: (value == 'unknown', value))]
    dates = sorted(row['upload_date'] for row in records if row['upload_date'])
    quality = Counter(row['date_quality'] for row in records)
    summary = {'total_records': len(records), 'creator_count': len(creators),
               'date_quality_counts': {key: quality[key] for key in QUALITIES},
               'known_date_count': len(dates),
               'original_estimate_count': sum(bool(row['original_estimated_date']) for row in records),
               'exact_estimate_differences': sum(row['estimate_differs_from_exact'] for row in records),
               'earliest_upload_date': dates[0] if dates else None,
               'latest_upload_date': dates[-1] if dates else None,
               'saved_audio_count': sum(row['saved_audio'] is True for row in records)
               if saved_audio_ids is not None else None}
    need(sum(row['record_count'] for row in creators) == len(records) ==
         sum(row['record_count'] for row in monthly) == sum(quality.values()), 'timeline totals do not reconcile')
    return {'schema_version': 1, 'scope': 'selected_newest20_upload_timeline',
            'generated_at': generated_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
            'scope_note': 'Selected up to 20 videos per creator, not each creator\'s complete production history.',
            'date_note': 'Queue dates are estimates. Exact overrides use saved YouTube upload-date metadata; upload dates are not recording dates.',
            'saved_audio_note': 'Saved audio reflects the supplied receipt-coverage snapshot, not a live download poll.'
            if saved_audio_ids is not None else 'Saved audio coverage was not supplied.',
            'summary': summary, 'creators': creators, 'monthly': monthly, 'records': records}


def load_audio_ids(path, selected_rows, *, content=None):
    """Read the public downloaded_videos.csv snapshot; never inspect Drive/media."""
    selected = {row['video_id']: row['channel_dir'] for row in selected_rows}
    content = Path(path).read_bytes() if content is None else content
    rows = list(csv.DictReader(io.StringIO(content.decode('utf-8-sig'), newline='')))
    found = set()
    for row in rows:
        video = row.get('video_id', '')
        if video.startswith("'-"):
            video = video[1:]  # Existing spreadsheet-safe downloaded-video export.
        need(video in selected, 'audio snapshot ID is outside the selected sample')
        need(not row.get('channel_dir') or row['channel_dir'] == selected[video], 'audio snapshot creator mismatch')
        need(row.get('audio_source') in {'youtube_native', 'publisher_edition', 'youtube_track_unverified'},
             'unsupported audio snapshot source label')
        found.add(video)
    return found


def spreadsheet_cell(value):
    if value is None:
        return ''
    text = str(value)
    if text.startswith(('\t', '\r', '\n')) or text.lstrip(' \ufeff').startswith(('=', '+', '-', '@')):
        return "'" + text
    return text


def csv_bytes(rows, fields):
    stream = io.StringIO(newline=''); writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({field: spreadsheet_cell(row.get(field)) for field in fields})
    return ('\ufeff' + stream.getvalue()).encode('utf-8')


def safe_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')


def render_html(data, template, plotly_js):
    need(template.count('__TIMELINE_DATA__') == 1 and template.count('__PLOTLY_JS__') == 1,
         'timeline template must contain each placeholder exactly once')
    bundle = re.sub(r'</script', lambda match: '<\\/script', plotly_js, flags=re.IGNORECASE)
    values = {'__TIMELINE_DATA__': safe_json(data), '__PLOTLY_JS__': bundle}
    html = re.sub(r'__TIMELINE_DATA__|__PLOTLY_JS__', lambda match: values[match[0]], template)
    need(len(html.encode('utf-8')) < 5_000_000, 'standalone timeline exceeds the HTML size bound')
    return html


def write_outputs(data, out_dir, *, template_path=None, plotly_path=None):
    need(bool(template_path) == bool(plotly_path), 'template and local Plotly bundle must be supplied together')
    video_rows = []
    for row in data['records']:
        provenance = row['exact_date_provenance'] or {}
        video_rows.append(dict(row, exact_date_source_sha256=provenance.get('source_sha256')))
    payloads = {'dataset_timeline.json': (safe_json(data) + '\n').encode('utf-8'),
                'dataset_timeline_videos.csv': csv_bytes(video_rows, VIDEO_FIELDS),
                'dataset_timeline_monthly.csv': csv_bytes(data['monthly'], MONTH_FIELDS)}
    if template_path:
        html = render_html(data, Path(template_path).read_text(encoding='utf-8'),
                           Path(plotly_path).read_text(encoding='utf-8'))
        payloads['timeline.html'] = html.encode('utf-8')
    output = Path(out_dir); output.mkdir(parents=True, exist_ok=True)
    for filename, content in payloads.items():
        (output / filename).write_bytes(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--exact-dates', type=Path)
    parser.add_argument('--coverage-csv', type=Path)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--template', type=Path)
    parser.add_argument('--plotly-js', type=Path)
    parser.add_argument('--expected-videos', type=int)
    parser.add_argument('--expected-creators', type=int)
    args = parser.parse_args(argv)
    # Parse and hash the same saved bytes even if a later local refresh replaces a file.
    queue_bytes = args.queue.read_bytes()
    overlay_bytes = args.exact_dates.read_bytes() if args.exact_dates else None
    coverage_bytes = args.coverage_csv.read_bytes() if args.coverage_csv else None
    rows = list(csv.DictReader(io.StringIO(queue_bytes.decode('utf-8-sig'), newline='')))
    overlay = json.loads(overlay_bytes.decode('utf-8-sig')) if overlay_bytes is not None else None
    audio = load_audio_ids(args.coverage_csv, rows, content=coverage_bytes) if args.coverage_csv else None
    data = build_timeline(rows, overlay, audio)
    need(args.expected_videos is None or len(data['records']) == args.expected_videos, 'unexpected selected video count')
    need(args.expected_creators is None or len(data['creators']) == args.expected_creators, 'unexpected creator count')
    data['source'] = {'selection_csv_sha256': hashlib.sha256(queue_bytes).hexdigest(),
                      'exact_date_overlay_sha256': hashlib.sha256(overlay_bytes).hexdigest() if overlay_bytes is not None else None,
                      'coverage_csv_sha256': hashlib.sha256(coverage_bytes).hexdigest() if coverage_bytes is not None else None}
    write_outputs(data, args.out_dir, template_path=args.template, plotly_path=args.plotly_js)
    print(json.dumps(data['summary'], ensure_ascii=True))
    return data


if __name__ == '__main__':
    main()
