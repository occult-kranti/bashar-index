"""Carry an already observed public video edition through a native-audio handoff."""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
from tempfile import mkstemp

try:
    from .media_metadata import build_metadata
except ImportError:  # The frozen collection worker loads the pipeline as top-level modules.
    from media_metadata import build_metadata


PUBLIC_FIELDS = frozenset('''id display_id title fulltitle alt_title description thumbnail thumbnails
    webpage_url webpage_url_basename channel channel_id channel_url channel_follower_count channel_is_verified
    uploader uploader_id uploader_url creator creators artist artists album album_artist track track_number
    disc_number composer genre series season season_number episode episode_number release_year
    upload_date timestamp release_date release_timestamp modified_date modified_timestamp availability
    live_status was_live is_live duration duration_string language location license age_limit
    view_count concurrent_view_count average_rating like_count dislike_count comment_count repost_count
    tags categories chapters subtitles automatic_captions'''.split())
MAX_CAPTURE_BYTES = 4 * 1024 * 1024
# Leave room in the mature Sink's 512 KiB envelope for transport and quality evidence.
INLINE_BUDGET = 192 * 1024
_ID = re.compile(r'[A-Za-z0-9_-]{11}')
_CHANNEL = re.compile(r'UC[A-Za-z0-9_-]{22}')


def _json(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def _identity(info, video_id, channel_id):
    if (not isinstance(info, dict) or not _ID.fullmatch(str(video_id)) or
            not _CHANNEL.fullmatch(str(channel_id)) or info.get('id') != video_id or info.get('channel_id') != channel_id):
        raise ValueError('public episode identity mismatch')


def _caption_inventory(tracks):
    """Keep public language and edition labels without retaining a caption delivery URL or inline text."""
    result = {}
    for language, formats in (tracks.items() if isinstance(tracks, dict) else ()):
        if not isinstance(language, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}', language) or language == 'live_chat':
            continue
        entries = []
        for track in formats if isinstance(formats, list) else ():
            if isinstance(track, dict):
                entry = {key: track[key] for key in ('name', 'ext', 'kind') if isinstance(track.get(key), str)}
                if entry and entry not in entries:
                    entries.append(entry)
        result[language] = entries
    return result


def store_capture(directory, info, *, video_id, channel_id, captured_at):
    """Atomically preserve the public fields of the observed edition; perform no network I/O."""
    _identity(info, video_id, channel_id)
    fields = {key: info[key] for key in PUBLIC_FIELDS if key in info}
    for key in ('subtitles', 'automatic_captions'):
        if key in fields:
            fields[key] = _caption_inventory(fields[key])
    doc = build_metadata(fields, {'video_id': video_id, 'expected_channel_id': channel_id}, captured_at)
    doc['observation_kind'] = 'public_episode_at_native_handoff'
    raw = _json(doc)
    if len(raw) > MAX_CAPTURE_BYTES:
        raise OverflowError('public metadata exceeded the local capture budget')
    digest = hashlib.sha256(raw).hexdigest()
    folder = Path(directory)
    name = f'public-episode.{digest}.info.json'
    target = folder / name
    if target.exists():
        if target.is_symlink() or target.read_bytes() != raw:
            raise ValueError('existing public observation has changed')
    else:
        fd, name_on_disk = mkstemp(dir=folder, prefix='.public-episode-')
        temp = Path(name_on_disk)
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
    return {'status': 'captured', 'filename': name, 'bytes': len(raw), 'sha256': digest,
            'video_id': video_id, 'channel_id': channel_id, 'captured_at': captured_at}


def observe_handoff(directory, info, *, video_id, channel_id, captured_at):
    try:
        return store_capture(directory, info, video_id=video_id, channel_id=channel_id, captured_at=captured_at)
    except (OSError, OverflowError) as error:
        # A failed optional metadata write does not consume or cancel the valid audio offer.
        return {'status': 'unavailable', 'reason': 'local_write_failed' if isinstance(error, OSError) else 'capture_size_limit',
                'video_id': video_id, 'channel_id': channel_id, 'captured_at': captured_at}


def merge_capture(native, route, directory):
    """Attach the exact source edition to canonical metadata without changing native transport evidence."""
    ref = route.get('public_episode_capture')
    if ref is None:  # Older handoffs contain only the selected format metadata.
        return native
    base = native['metadata']
    _identity(base, ref.get('video_id'), ref.get('channel_id'))
    if ref.get('status') == 'unavailable':
        if ref.get('reason') not in ('local_write_failed', 'capture_size_limit'):
            raise ValueError('invalid public capture status')
        return {**native, 'public_episode_observation': {'status': 'unavailable', 'reason': ref['reason']}}
    digest = ref.get('sha256')
    if (ref.get('status') != 'captured' or not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest)
            or ref.get('filename') != f'public-episode.{digest}.info.json' or type(ref.get('bytes')) is not int
            or not 0 < ref['bytes'] <= MAX_CAPTURE_BYTES):
        raise ValueError('invalid public observation descriptor')
    folder = Path(directory).resolve(strict=True)
    source = folder / ref['filename']
    if source.is_symlink() or source.resolve(strict=True).parent != folder or source.stat().st_size != ref['bytes']:
        raise ValueError('public observation location or length changed')
    raw = source.read_bytes()
    if len(raw) != ref['bytes'] or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('public observation hash changed')
    capture = json.loads(raw)
    _identity(capture.get('metadata'), ref['video_id'], ref['channel_id'])
    if (capture.get('observation_kind') != 'public_episode_at_native_handoff' or
            capture.get('captured_at') != ref.get('captured_at') or capture.get('source') != native.get('source')):
        raise ValueError('public observation edition mismatch')
    merged = dict(native)
    public = capture['metadata']
    provenance = {'status': 'captured', 'sha256': digest, 'bytes': len(raw), 'captured_at': capture['captured_at'],
                  'native_metadata_built_at': native['captured_at']}
    merged['captured_at'] = capture['captured_at']
    merged['languages'] = {**capture['languages'], 'audio': native['languages'].get('audio') or capture['languages'].get('audio')}
    if len(raw) > INLINE_BUDGET:
        # Preserve the entire dated observation losslessly when a large list of chapters or artwork would crowd the Sink.
        compressed = base64.b64encode(gzip.compress(raw, compresslevel=6, mtime=0)).decode('ascii')
        public = {key: public[key] for key in ('id','channel_id','title','upload_date','release_date','timestamp','release_timestamp','duration') if key in public}
        if len(compressed) <= INLINE_BUDGET:
            provenance['full_snapshot_gzip_base64'] = compressed
        else:
            provenance.update(full_snapshot_retained_locally=True, separate_archive_required=True, filename=ref['filename'])
    merged['metadata'] = {**public, **{key: value for key, value in base.items() if value is not None}}
    merged['public_episode_observation'] = provenance
    return merged
