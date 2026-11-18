"""Check generated public collection data without running collectors or models."""
from collections import Counter
import csv
import datetime as dt
import io
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.collection_coverage import csv_bytes

CHANNEL_FIELDS = ('channel', 'channel_dir', 'target', 'youtube_audio', 'publisher_only_audio',
                  'audio_total', 'with_saved_text', 'remaining_audio')
VIDEO_FIELDS = ('channel', 'channel_dir', 'video_id', 'title', 'url', 'listing_rank',
                'audio_source', 'saved_text', 'native_audio_bytes')


def need(value, reason):
    if not value:
        raise ValueError(reason)


def check(folder):
    folder = Path(folder)
    data = json.loads((folder / 'channel_download_coverage.json').read_text(encoding='utf-8'))
    need(data.get('schema_version') == 1 and data.get('scope') == 'newest20_receipt_coverage', 'coverage_schema')
    need(dt.datetime.fromisoformat(data['generated_at'].replace('Z', '+00:00')).tzinfo is not None, 'coverage_date')
    channels, summary = data['channels'], data['summary']
    need(isinstance(channels, list) and bool(channels), 'coverage_channels')
    by_channel = {}
    for row in channels:
        need(set(row) == set(CHANNEL_FIELDS), 'channel_fields')
        slug = row['channel_dir']
        need(isinstance(slug, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', slug)
             and slug not in by_channel, 'channel_identity')
        need(all(type(row[key]) is int and row[key] >= 0 for key in CHANNEL_FIELDS[2:]), 'channel_counts')
        need(0 < row['target'] <= 20 and row['audio_total'] == row['youtube_audio'] + row['publisher_only_audio']
             and row['audio_total'] + row['remaining_audio'] == row['target']
             and row['with_saved_text'] <= row['audio_total'], 'channel_totals')
        by_channel[slug] = row
    # Git stores text CSVs with LF even when a Windows exporter writes CRLF.
    actual_csv = (folder / 'channel_download_coverage.csv').read_bytes().replace(b'\r\n', b'\n')
    expected_csv = csv_bytes(channels, CHANNEL_FIELDS).replace(b'\r\n', b'\n')
    need(actual_csv == expected_csv, 'channel_csv_drift')
    reader = csv.DictReader(io.StringIO((folder / 'downloaded_videos.csv').read_text(encoding='utf-8-sig')))
    need(tuple(reader.fieldnames or ()) == VIDEO_FIELDS, 'video_csv_header')
    videos = list(reader)
    seen, ranks, counts = set(), set(), Counter()
    for row in videos:
        need(set(row) == set(VIDEO_FIELDS), 'video_fields')
        ident, slug = row['video_id'], row['channel_dir']
        if ident.startswith("'-"):
            ident = ident[1:]  # The exporter neutralizes spreadsheet formulas.
        need(re.fullmatch(r'[A-Za-z0-9_-]{11}', ident) and ident not in seen and slug in by_channel
             and row['url'] == 'https://www.youtube.com/watch?v=' + ident, 'video_identity')
        rank = int(row['listing_rank'])
        need(0 <= rank < 20 and (slug, rank) not in ranks, 'video_rank')
        source = row['audio_source']
        need(source in {'youtube_native', 'publisher_edition'} and row['saved_text'] in {'True', 'False'}, 'video_source_or_text')
        need((source == 'youtube_native' and row['native_audio_bytes'].isdigit() and int(row['native_audio_bytes']) > 0)
             or (source == 'publisher_edition' and row['native_audio_bytes'] == ''), 'video_bytes')
        expected_name = next(csv.DictReader(io.StringIO(csv_bytes([by_channel[slug]], CHANNEL_FIELDS).decode('utf-8-sig'))))['channel']
        need(row['channel'] == expected_name, 'video_channel_name')
        need(all(not row[key].startswith(('=', '+', '-', '@', '\t', '\r')) for key in ('channel', 'title')), 'unsafe_spreadsheet_cell')
        seen.add(ident); ranks.add((slug, rank)); counts[slug, source] += 1
        counts[slug, 'text'] += row['saved_text'] == 'True'
    for slug, row in by_channel.items():
        need(counts[slug, 'youtube_native'] == row['youtube_audio'] and
             counts[slug, 'publisher_edition'] == row['publisher_only_audio'] and
             counts[slug, 'text'] == row['with_saved_text'], 'video_channel_totals')
    mapping = {'latest20_target': 'target', 'youtube_native_audio': 'youtube_audio',
               'publisher_only_audio': 'publisher_only_audio', 'audio_available': 'audio_total',
               'audio_with_saved_text': 'with_saved_text', 'remaining_audio': 'remaining_audio'}
    need(type(summary.get('channels')) is int and summary['channels'] == len(channels) and all(type(summary.get(key)) is int and
         summary[key] == sum(row[field] for row in channels) for key, field in mapping.items()), 'summary_totals')
    for name, scope in (('ingestion_status.json', 'local_youtube_collection'), ('collection_eta.json', 'collection_eta')):
        value = json.loads((folder / name).read_text(encoding='utf-8'))
        need(value.get('scope') == scope, 'snapshot_scope')
    return {'channels': len(channels), 'audio': len(videos), 'target': summary['latest20_target']}


if __name__ == '__main__':
    try:
        print(json.dumps(check(Path(__file__).resolve().parents[1] / 'plan')))
    except (OSError, ValueError, TypeError, KeyError, StopIteration):
        raise SystemExit('Public collection snapshot validation failed; no input contents printed.')
