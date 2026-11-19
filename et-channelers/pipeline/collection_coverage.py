"""Publish dated newest-20 channel coverage and public video inventories.

Reads saved receipt proofs only. No source requests, Drive calls or media reads.
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
import sys

try:
    from . import ingestion_status as status, drive_ingest as storage, publisher_feed_text
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import ingestion_status as status
    import publisher_feed_text
    import drive_ingest as storage


ACTIVITY_FIELDS = ('saved', 'downloading', 'processing', 'awaiting_upload', 'queued', 'waiting_for_source', 'other_pending')


def channel_activity(root, rows, available, at):
    """Partition missing entries using bound ownership and saved worker metadata."""
    by_video = {row['video_id']: row for row in rows}
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['channel_dir']].append(row)
    rolling = status.rolling_native_state(root, at.timestamp())
    lane = rolling.get('public') or status.native_bulk_lane(root, at.timestamp())
    qualified = status.qualified_batch_state(root, at.timestamp())
    qualified_stages = qualified.get('video_stages', {}) if lane.get('state') != 'running' else {}
    deferred = set(qualified.get('deferred_video_ids', ()))
    namespace = lane.get('namespace', '')
    rolling_stages = rolling.get('video_stages', {})
    scope, attempts = set(rolling_stages), {}
    if re.fullmatch(r'stock_wpc_batch_v5_bulk(?:_recovery[0-9]+|_recovery6_prototype)?', namespace):
        lease = status.read_object(root / 'sync' / (namespace + '_lease.json'))
        ids = lease.get('allowed_video_ids', [])
        if (lane.get('state') == 'running' and lane.get('process_confirmed') is True and lease.get('state') == 'active' and
                isinstance(ids, list) and len(ids) == lane.get('source_count') and set(ids) <= by_video.keys()):
            scope = set(ids)
            for path in (root / namespace / 'jobs').glob('*/*/attempt.json'):
                if path.parent.name in scope:
                    # Repeated attempt folders cannot establish current activity.
                    attempts[path.parent.name] = path.parent if path.parent.name not in attempts else None
    counters = defaultdict(Counter)
    for ident, row in by_video.items():
        field = 'other_pending'
        if ident in available:
            field = 'saved'
        elif ident in rolling_stages:
            field = rolling_stages[ident]
        elif ident in qualified_stages:
            stage = qualified_stages[ident]
            field = stage if stage in ACTIVITY_FIELDS else 'other_pending'
        elif ident in deferred and ident not in scope:
            field = 'waiting_for_source'
        elif ident in scope:
            if ident not in attempts:
                field = 'queued'
            elif attempts[ident] is not None:
                folder = attempts[ident]
                owner = status.read_object(folder / 'child-owner.json').get('owned_child')
                progress = status.read_object(folder / 'progress.json')
                result = status.read_object(folder / 'result.json')
                if lane.get('process_confirmed') is True and isinstance(owner, dict) and status.owned_process_alive(owner):
                    field = 'downloading' if progress.get('phase') == 'native_transfer' else 'processing'
                elif result.get('status') == 'local_complete':
                    field = 'awaiting_upload'
        counters[row['channel_dir']][field] += 1
    channels = []
    for slug, items in sorted(grouped.items()):
        names = Counter(item.get('source_channel_name') or slug for item in items)
        channels.append(dict(channel=names.most_common(1)[0][0], channel_dir=slug, target=len(items),
            **{field: counters[slug][field] for field in ACTIVITY_FIELDS}))
    return {'schema_version': 1, 'generated_at': at.isoformat().replace('+00:00', 'Z'),
        'state': 'running' if lane.get('state') == 'running' else qualified.get('public', {}).get('state', lane.get('state', 'unconfirmed')),
        'cohort_items': len(scope) if lane.get('state') == 'running' else qualified.get('public', {}).get('source_count', len(scope)),
        'summary': {field: sum(row[field] for row in channels) for field in ACTIVITY_FIELDS},
        'channels': channels}


def mixed_selection(path, names, *, parsed=None):
    """Use the shared mixed-frame validator; retain legacy display-name overrides."""
    selected = parsed if parsed is not None else status.selection_rows(path)
    rows = [dict(row, source_channel_name=names.get(row['channel_dir'], row['source_channel_name']))
            for row in selected['rows']]
    return rows, {name: group['scope'] for name, group in selected['creators'].items()}, selected['sha256']


def coverage(root, *, now=None, remote=status.DEFAULT_REMOTE, selection=None):
    root = Path(root)
    legacy = root / 'jobs/queue_newest20_enriched.csv'
    rows = list(csv.DictReader(io.StringIO(legacy.read_text(encoding='utf-8-sig')))) if legacy.exists() else []
    scopes, selection_hash = {}, None
    if selection is not None:
        names = {r['channel_dir']: r['source_channel_name'] for r in rows if r.get('source_channel_name')}
        selection_info = status.selection_rows(selection)
        rows, scopes, selection_hash = mixed_selection(selection, names, parsed=selection_info)
    if not rows and not scopes:
        raise ValueError('Newest-20 queue is empty')
    targets, ranks, grouped = set(), set(), defaultdict(list)
    for creator in scopes:
        grouped[creator] = []
    tabs = {'videos', 'shorts', 'streams', 'unknown'} if selection is not None else {'videos'}
    for row in rows:
        video, channel = row.get('video_id', ''), row.get('channel_dir', '')
        try:
            rank = int(row.get('listing_rank', ''))
        except ValueError as error:
            raise ValueError('Invalid newest-20 rank') from error
        if (not re.fullmatch(r'[A-Za-z0-9_-]{11}', video) or video in targets or
                not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', channel) or
                row.get('tab') not in tabs or not 0 <= rank < 20 or (channel, rank) in ranks):
            raise ValueError('Invalid or duplicate newest-20 queue entry')
        targets.add(video)
        ranks.add((channel, rank))
        grouped[channel].append(row)
    native = status.latest_records(root / 'sync/drive_ingest_manifest.jsonl')
    captions = status.latest_records(root / 'sync/drive_caption_manifest.jsonl')
    owners = {row['video_id']: row['channel_dir'] for row in rows}
    audio = {key for key, rec in native.items() if key in targets and rec.get('channel_dir') == owners[key] and
             status.proof(storage.receipt_complete, rec, status.record_row(rec), remote)}
    asr = {rec['video_id'] for rec in status.asr_records(root / 'sync/asr_manifest.jsonl')
           if rec.get('video_id') in audio and status.asr_receipt_complete(rec, native[rec['video_id']], remote)}
    caption_ids = {key for key, rec in captions.items() if key in audio and rec.get('channel_dir') == owners[key]
                   for track in (rec['tracks'] if isinstance(rec.get('tracks'), list) else []) if isinstance(track, dict) and
                   status.proof(storage.caption_track_verified, track, status.record_row(rec), remote)}
    publisher_articles, publisher_transcripts, variants, _, variant_asr = status.publisher_coverage(
        root, targets, remote, target_rows=rows)
    mirrors, mirror_captions, mirror_asr, mirror_transcripts = status.publisher_mirror_evidence(root, targets, remote, target_rows=rows)
    publisher_captions = status.publisher_timed_text_coverage(root, targets, remote, target_rows=rows)
    feed_documents = {job['row']['video_id'] for job in publisher_feed_text.input_rows(root, rows, remote)}
    written_messages, publisher_sessions = status.companion_writings(root, targets, remote, target_rows=rows)
    publishers = variants | mirrors
    qualified = status.qualified_edition_coverage(root, targets, remote, target_rows=rows)
    qualified_only = qualified - audio - publishers
    available = audio | publishers | qualified
    text = asr | caption_ids | variant_asr | mirror_captions | mirror_asr | mirror_transcripts
    if not text <= available <= targets:
        raise ValueError('Text or audio has no matching target audio edition')
    channels = []
    for key, items in sorted(grouped.items()):
        ids = {item['video_id'] for item in items}
        names = Counter(item.get('source_channel_name') or key for item in items)
        channels.append({'channel': names.most_common(1)[0][0] if names else key, 'channel_dir': key,
            'target': len(ids), 'youtube_audio': len(ids & audio),
            'publisher_only_audio': len(ids & (publishers - audio)),
            'qualified_youtube_only_audio': len(ids & qualified_only), 'audio_total': len(ids & available),
            'with_saved_text': len(ids & text), 'remaining_audio': len(ids - available)})
        if selection is not None:
            channels[-1].update(selection_scope=scopes[key], shortfall_to_20=20-len(items),
                                with_publisher_companion_text=len(ids & (written_messages | publisher_sessions | publisher_articles | publisher_transcripts | publisher_captions | feed_documents)),
                                with_independent_publisher_transcripts=len(ids & feed_documents),
                                with_independent_publisher_captions=len(ids & publisher_captions))
    videos = []
    for row in rows:
        video = row['video_id']
        if video in available:
            videos.append({'channel': row.get('source_channel_name') or row['channel_dir'],
                'channel_dir': row['channel_dir'], 'video_id': video, 'title': row.get('title', ''),
                'url': 'https://www.youtube.com/watch?v=' + video, 'listing_rank': int(row['listing_rank']),
                'audio_source': ('youtube_native' if video in audio else 'publisher_edition' if video in publishers else 'youtube_track_unverified'),
                'saved_text': video in text, 'native_audio_bytes': native[video]['bytes'] if video in audio else ''})
            if selection is not None:
                videos[-1]['tab'] = row['tab']
                videos[-1]['independent_publisher_caption'] = video in publisher_captions
                videos[-1]['independent_publisher_transcript'] = video in feed_documents
    at = dt.datetime.now(dt.timezone.utc) if now is None else now
    public = {'schema_version': 1, 'scope': 'newest20_receipt_coverage',
        'generated_at': at.isoformat().replace('+00:00', 'Z'),
        'summary': {'channels': len(channels), 'latest20_target': len(targets),
            'youtube_native_audio': len(audio), 'publisher_only_audio': len(publishers - audio),
            'qualified_youtube_audio': len(qualified), 'qualified_youtube_only_audio': len(qualified_only),
            'audio_available': len(available), 'native_asr': len(asr), 'native_caption_videos': len(caption_ids),
            'audio_with_saved_text': len(text), 'remaining_audio': len(targets - available)},
        'channels': channels, 'activity': channel_activity(root, rows, available, at)}
    if selection is not None:
        public.update(selection_basis='mixed_channel_uploads', selection_sha256=selection_hash)
        if selection_info.get('archive'):
            public.update(selection_basis=selection_info['basis'], archive=selection_info['archive'],
                          priority_scope_sha256=selection_info['priority_scope_sha256'])
        active = {row['channel_dir']: row for row in public['activity']['channels']}
        for row in channels:
            counts = active.get(row['channel_dir'], {})
            row.update({field: counts.get(field, 0) for field in ACTIVITY_FIELDS if field != 'saved'})
        public['summary'].update(selection_shortfall=sum(20-len(items) for items in grouped.values()),
                                 scope_by_creator=dict(Counter(scopes.values())),
                                 publisher_edition_untimed_transcripts=len(mirror_transcripts),
                                 independent_publisher_caption_videos=len(publisher_captions),
                                 independent_publisher_transcript_videos=len(feed_documents),
                                 audio_with_saved_text_or_independent_publisher_text=len(available & (text | publisher_captions | feed_documents)),
                                 audio_with_saved_text_or_independent_publisher_caption=len(available & (text | publisher_captions)),
                                 publisher_written_messages=len(written_messages), publisher_session_texts=len(publisher_sessions),
                                 publisher_articles=len(publisher_articles), publisher_declared_transcripts=len(publisher_transcripts),
                                 selected_by_format=dict(Counter(r['tab'] for r in rows)),
                                 saved_by_format=dict(Counter(r['tab'] for r in videos)))
    return public, videos


def csv_bytes(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    # Prevent public titles/channel names becoming spreadsheet formulas.
    for row in rows:
        writer.writerow({key: "'" + value if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r')) else value
                         for key, value in row.items()})
    return ('\ufeff' + stream.getvalue()).encode('utf-8')


def activity_csv(snapshot):
    """Compact operator table. Its mutually exclusive work states sum to the selected target."""
    rows = []
    for creator in snapshot['channels']:
        states = {key: creator[key] for key in ACTIVITY_FIELDS[1:]}
        if creator['audio_total'] + sum(states.values()) != creator['target']:
            raise ValueError('Creator activity does not reconcile with its selected recordings')
        scope = creator['selection_scope']
        notes = {'short_complete_displayed_list': 'All publicly listed completed uploads selected.',
                 'unobserved': 'No confirmed listing available.',
                 'incomplete_visible_positions': 'Public listing has unresolved positions.'}
        rows.append({'Creator': creator['channel'], 'Target': creator['target'], 'Saved audio': creator['audio_total'],
                     'Downloading': states['downloading'], 'Preparing or validating': states['processing'],
                     'Awaiting upload': states['awaiting_upload'], 'Queued': states['queued'],
                     'Other pending': states['other_pending'], 'Scope note': notes.get(scope, ''),
                     'Waiting for source': states['waiting_for_source'], 'Channel ID in archive': creator['channel_dir'],
                     'Snapshot UTC': snapshot['generated_at']})
    fields = ('Creator', 'Target', 'Saved audio', 'Downloading', 'Preparing or validating', 'Awaiting upload',
              'Queued', 'Other pending', 'Scope note', 'Waiting for source', 'Channel ID in archive', 'Snapshot UTC')
    return csv_bytes(rows, fields)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--selection', type=Path, help='Dated recording selection or additive Latest 20+ videos index')
    parser.add_argument('--activity-csv', type=Path, help='Optional private operator table for this recording selection')
    args = parser.parse_args(argv)
    if args.activity_csv and (not args.selection or args.activity_csv.resolve() in {
            args.out.resolve(), args.out.with_suffix('.csv').resolve(), (args.out.parent / 'downloaded_videos.csv').resolve()}):
        parser.error('The operator table needs a dated selection and a distinct CSV path')
    public, videos = coverage(args.root, selection=args.selection)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    outputs = {args.out: (json.dumps(public, ensure_ascii=False, indent=2) + '\n').encode('utf-8'),
        args.out.with_suffix('.csv'): csv_bytes(public['channels'],
            ('channel', 'channel_dir', 'target', 'youtube_audio', 'publisher_only_audio', 'qualified_youtube_only_audio', 'audio_total', 'with_saved_text', 'remaining_audio')
            + (('selection_scope', 'shortfall_to_20', 'with_publisher_companion_text', 'with_independent_publisher_captions', 'with_independent_publisher_transcripts', *ACTIVITY_FIELDS[1:]) if args.selection else ())),
        args.out.parent / 'downloaded_videos.csv': csv_bytes(videos,
            ('channel', 'channel_dir', 'video_id', 'title', 'url', 'listing_rank', 'audio_source', 'saved_text', 'native_audio_bytes')
            + (('tab', 'independent_publisher_caption', 'independent_publisher_transcript') if args.selection else ()))}
    if args.activity_csv:
        outputs[args.activity_csv] = activity_csv(public)
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_bytes(data)
        temporary.replace(path)
    print(json.dumps(public['summary']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
