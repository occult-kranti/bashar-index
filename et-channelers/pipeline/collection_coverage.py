"""Publish dated newest-20 channel coverage and public video inventories.

Reads saved receipt proofs only. No source requests, Drive calls or media reads.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import datetime as dt
import io
import json
from pathlib import Path
import re
import sys

try:
    from . import ingestion_status as status, drive_ingest as storage
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import ingestion_status as status
    import drive_ingest as storage


def coverage(root, *, now=None, remote=status.DEFAULT_REMOTE):
    root = Path(root)
    rows = list(csv.DictReader(io.StringIO((root / 'jobs/queue_newest20_enriched.csv').read_text(encoding='utf-8-sig'))))
    if not rows:
        raise ValueError('Newest-20 queue is empty')
    targets, ranks, grouped = set(), set(), defaultdict(list)
    for row in rows:
        video, channel = row.get('video_id', ''), row.get('channel_dir', '')
        try:
            rank = int(row.get('listing_rank', ''))
        except ValueError as error:
            raise ValueError('Invalid newest-20 rank') from error
        if (not re.fullmatch(r'[A-Za-z0-9_-]{11}', video) or video in targets or
                not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', channel) or
                row.get('tab') != 'videos' or not 0 <= rank < 20 or (channel, rank) in ranks):
            raise ValueError('Invalid or duplicate newest-20 queue entry')
        targets.add(video)
        ranks.add((channel, rank))
        grouped[channel].append(row)
    native = status.latest_records(root / 'sync/drive_ingest_manifest.jsonl')
    captions = status.latest_records(root / 'sync/drive_caption_manifest.jsonl')
    audio = {key for key, rec in native.items() if key in targets and
             status.proof(storage.receipt_complete, rec, status.record_row(rec), remote)}
    asr = {rec['video_id'] for rec in status.asr_records(root / 'sync/asr_manifest.jsonl')
           if rec.get('video_id') in audio and status.asr_receipt_complete(rec, native[rec['video_id']], remote)}
    caption_ids = {key for key, rec in captions.items() if key in audio
                   for track in (rec['tracks'] if isinstance(rec.get('tracks'), list) else []) if isinstance(track, dict) and
                   status.proof(storage.caption_track_verified, track, status.record_row(rec), remote)}
    _, _, variants, _, variant_asr = status.publisher_coverage(root, targets, remote)
    mirrors, mirror_captions, mirror_asr = status.publisher_mirror_coverage(root, targets, remote)
    available = audio | variants | mirrors
    text = asr | caption_ids | variant_asr | mirror_captions | mirror_asr
    if not text <= available <= targets:
        raise ValueError('Text or audio has no matching target audio edition')
    channels = []
    for key, items in sorted(grouped.items()):
        ids = {item['video_id'] for item in items}
        names = Counter(item.get('source_channel_name') or key for item in items)
        channels.append({'channel': names.most_common(1)[0][0], 'channel_dir': key,
            'target': len(ids), 'youtube_audio': len(ids & audio),
            'publisher_only_audio': len(ids & (available - audio)), 'audio_total': len(ids & available),
            'with_saved_text': len(ids & text), 'remaining_audio': len(ids - available)})
    videos = []
    for row in rows:
        video = row['video_id']
        if video in available:
            videos.append({'channel': row.get('source_channel_name') or row['channel_dir'],
                'channel_dir': row['channel_dir'], 'video_id': video, 'title': row.get('title', ''),
                'url': 'https://www.youtube.com/watch?v=' + video, 'listing_rank': int(row['listing_rank']),
                'audio_source': 'youtube_native' if video in audio else 'publisher_edition',
                'saved_text': video in text, 'native_audio_bytes': native[video]['bytes'] if video in audio else ''})
    at = dt.datetime.now(dt.timezone.utc) if now is None else now
    return {'schema_version': 1, 'scope': 'newest20_receipt_coverage',
        'generated_at': at.isoformat().replace('+00:00', 'Z'),
        'summary': {'channels': len(channels), 'latest20_target': len(targets),
            'youtube_native_audio': len(audio), 'publisher_only_audio': len(available - audio),
            'audio_available': len(available), 'native_asr': len(asr), 'native_caption_videos': len(caption_ids),
            'audio_with_saved_text': len(text), 'remaining_audio': len(targets - available)},
        'channels': channels}, videos


def csv_bytes(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    # Prevent public titles/channel names becoming spreadsheet formulas.
    for row in rows:
        writer.writerow({key: "'" + value if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r')) else value
                         for key, value in row.items()})
    return ('\ufeff' + stream.getvalue()).encode('utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    public, videos = coverage(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    outputs = {args.out: (json.dumps(public, ensure_ascii=False, indent=2) + '\n').encode('utf-8'),
        args.out.with_suffix('.csv'): csv_bytes(public['channels'],
            ('channel', 'channel_dir', 'target', 'youtube_audio', 'publisher_only_audio', 'audio_total', 'with_saved_text', 'remaining_audio')),
        args.out.parent / 'downloaded_videos.csv': csv_bytes(videos,
            ('channel', 'channel_dir', 'video_id', 'title', 'url', 'listing_rank', 'audio_source', 'saved_text', 'native_audio_bytes'))}
    for path, data in outputs.items():
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_bytes(data)
        temporary.replace(path)
    print(json.dumps(public['summary']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
