#!/usr/bin/env python3
"""Export aggregate collection status only; private record content never leaves the root."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

if __package__:
    from .drive_ingest import (CAPTION_POLICY, HARD_BLOCKS, caption_receipt_complete,
                               caption_track_verified, receipt_complete, terminal_unavailable, tree_bytes)
    from .chromium_capture_service import browser_receipt_complete
else:  # -I deliberately removes the script directory from the default import path.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from drive_ingest import (CAPTION_POLICY, HARD_BLOCKS, caption_receipt_complete,
                              caption_track_verified, receipt_complete, terminal_unavailable, tree_bytes)
    from chromium_capture_service import browser_receipt_complete

DEFAULT_REMOTE = "etdrive:04 Audio"


def stamp(value=None):
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z") \
        if value is not None else dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_object(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def owned_process_alive(identity):
    """Read-only Windows PID/creation-time proof; a reused PID is insufficient."""
    pid, created = identity.get('pid'), identity.get('process_creation_filetime')
    if os.name != 'nt' or type(pid) is not int or pid <= 0 or not str(created).isdigit():
        return False
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        code = wintypes.DWORD()
        return bool(kernel.GetProcessTimes(handle, *(ctypes.byref(x) for x in times)) and
                    kernel.GetExitCodeProcess(handle, ctypes.byref(code)) and code.value == 259 and
                    str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime) == str(created))
    finally:
        kernel.CloseHandle(handle)


def owned_process_child_of(child, parent):
    """Prove a separately launched frame belongs to the live series process."""
    if os.name != 'nt':
        return False
    if not owned_process_alive(child) or not owned_process_alive(parent):
        return False
    if int(child['process_creation_filetime']) < int(parent['process_creation_filetime']):
        return False
    import ctypes
    from ctypes import wintypes
    class BasicInformation(ctypes.Structure):
        _fields_ = [('reserved1', ctypes.c_void_p), ('peb', ctypes.c_void_p),
                    ('reserved2', ctypes.c_void_p * 2), ('pid', ctypes.c_size_t),
                    ('parent_pid', ctypes.c_size_t)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    native = ctypes.WinDLL('ntdll')
    native.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p,
                                                wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]
    native.NtQueryInformationProcess.restype = wintypes.LONG
    handle = kernel.OpenProcess(0x1000, False, child['pid'])
    if not handle:
        return False
    try:
        info, returned = BasicInformation(), wintypes.ULONG()
        return (native.NtQueryInformationProcess(handle, 0, ctypes.byref(info), ctypes.sizeof(info),
                                                 ctypes.byref(returned)) == 0 and
                info.pid == child['pid'] and info.parent_pid == parent['pid'])
    finally:
        kernel.CloseHandle(handle)


def active_native_series(root, now):
    """Do not let the parked legacy collector mask a separately owned executor."""
    lease = read_object(root / 'sync/stock_wpc_batch_v4_lease.json')
    expiry = lease.get('expires_at_epoch')
    if not (lease.get('state') == 'active' and lease.get('authorized') is True and
            lease.get('source_scope_authorized') is True and
            lease.get('profile') == 'stock_headful_wpc_native_batch_v4' and
            type(expiry) in (int, float) and now < expiry and
            lease.get('max_workers') in (1, 2)):
        return {}
    if (root / 'sync/STOP_STOCK_WPC_BATCH_V4').exists():
        return {}
    cooldown = read_object(root / 'sync/stock_wpc_batch_v4_source_cooldown.json')
    if source_deadline([cooldown]) > now:
        return {}
    drive_cooldown_path = root / 'sync/drive_ingest_cooldown.json'
    if drive_cooldown_path.exists():
        try:
            if float(read_object(drive_cooldown_path)['until_epoch']) > now:
                return {}
        except (KeyError, ValueError, TypeError):
            return {}
    candidates = [*(root / 'jobs').glob('native-series*/live'),
                  *(root / 'jobs').glob('native-campaign*/live')]
    for live in sorted(candidates)[:64]:
        if live.is_symlink() or any((live / name).exists() for name in
                                   ('local-publication-hold.json', 'drive-hold.json', 'STOP_SERIES')):
            continue
        state = read_object(live / 'series-state.json')
        invoked = read_object(live / 'source-invocation.json')
        series, authorization = lease.get('series_proposal_sha256'), lease.get('root_authorization_sha256')
        identity = {key: invoked.get(key) for key in ('pid', 'process_creation_filetime')}
        frame_identity = lease.get('controller_identity')
        controller_bound = isinstance(frame_identity, dict) and (
            frame_identity == identity or owned_process_child_of(frame_identity, identity))
        if not (isinstance(series, str) and re.fullmatch(r'[a-f0-9]{64}', series) and
                isinstance(authorization, str) and re.fullmatch(r'[a-f0-9]{64}', authorization) and
                state.get('status') == 'running' and state.get('proposal_sha256') == series and
                state.get('authorization_sha256') == authorization and
                invoked.get('series_proposal_sha256') == series and
                invoked.get('root_authorization_sha256') == authorization and
                controller_bound and
                owned_process_alive(invoked)):
            continue
        consumer = read_object(live / 'consumer-state.json')
        heartbeat = consumer.get('heartbeat_epoch')
        gpu = read_object(root / 'sync/gpu_lease.json')
        try:
            gpu_expiry = dt.datetime.fromisoformat(gpu.get('expires_at', '').replace('Z', '+00:00'))
            gpu_active = bool(gpu_expiry.tzinfo and gpu_expiry.timestamp() > now and
                              gpu.get('state') == 'active' and gpu.get('authorized', True) is True and
                              gpu.get('lease_id') == consumer.get('gpu_lease_id') and
                              gpu.get('series_proposal_sha256') == series)
        except (ValueError, TypeError, AttributeError):
            gpu_active = False
        asr_running = (consumer.get('series_proposal_sha256') == series and
                       consumer.get('status') == 'waiting_or_processing' and gpu_active and
                       consumer.get('phase') == 'gpu_running' and
                       type(heartbeat) in (int, float) and 0 <= now - heartbeat <= 15 and
                       owned_process_alive(consumer))
        return {'workers': lease['max_workers'], 'asr_running': asr_running,
                'asr_reported_at': stamp(heartbeat) if asr_running else None}
    return {}


def queue_ids(root, names):
    for name in names:
        path = root / "jobs" / name
        if path.is_file():
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            return {r["video_id"] for r in rows if r.get("video_id")}, len({r.get("channel_dir") for r in rows})
    return set(), 0


def record_row(record):
    video_id, channel = record.get("video_id"), record.get("channel_dir")
    if not isinstance(video_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return None
    if not isinstance(channel, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", channel):
        return None
    return {"video_id": video_id, "channel_dir": channel}


def proof(predicate, record, row, remote):
    if row is None:
        return False
    try:
        return bool(predicate(record, row, remote))
    except (KeyError, TypeError, ValueError, AttributeError):
        return False  # malformed private records are never completion evidence


def latest_records(path):
    records = {}
    if path.is_file():
        with path.open(encoding="utf-8-sig") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue  # a live writer may have an unfinished last record
                if isinstance(record, dict) and isinstance(record.get("video_id"), str) and record["video_id"]:
                    records[record["video_id"]] = record
    return records


def source_deadline(records):
    return max((rec.get('retry_not_before_epoch', 0) for rec in records
                if (rec.get('source_error_class') or rec.get('error_class')) in HARD_BLOCKS
                and type(rec.get('retry_not_before_epoch')) in (int, float)
                and 0 < rec['retry_not_before_epoch'] < 253402300799), default=0)


def asr_receipt_complete(record, audio, remote):
    """A generated transcript counts only with bundle and exact source proofs."""
    run_id = record.get('run_id', '')
    row = record_row(audio)
    if (not row or not proof(receipt_complete, audio, row, remote) or
            not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', run_id)):
        return False
    expected = audio['remote'].rpartition('/')[0] + '/' + row['video_id'] + '/ASR/' + run_id + '/' + run_id + '.zip'
    return (record.get('status') == 'verified' and record.get('artifact_kind') == 'asr_bundle' and
            record.get('video_id') == row['video_id'] and record.get('channel_dir') == row['channel_dir'] and
            record.get('remote') == expected and bool(record.get('drive_id')) and
            type(record.get('bytes')) is int and record['bytes'] > 0 and
            isinstance(record.get('md5'), str) and bool(re.fullmatch(r'[0-9a-f]{32}', record['md5'])) and
            isinstance(record.get('sha256'), str) and bool(re.fullmatch(r'[0-9a-f]{64}', record['sha256'])) and
            record.get('source_audio_drive_id') == audio.get('drive_id') and
            record.get('source_audio_sha256') == audio.get('sha256'))


def asr_records(path, identity_key='run_id'):
    records = {}
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict) and isinstance(record.get('video_id'), str) and isinstance(record.get(identity_key), str):
                records[(record['video_id'], record[identity_key])] = record
    return records.values()


def publisher_coverage(root, targets, remote):
    """Supplementary publisher editions never establish native/ASR completion."""
    def rows(name):
        path = root / 'sync' / name
        if path.is_file():
            for line in path.read_text(encoding='utf-8-sig').splitlines():
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, dict):
                    yield record

    def object_proof(value, kind, kind_field='kind'):
        return (isinstance(value, dict) and (kind_field is None or value.get(kind_field) == kind) and
                type(value.get('bytes')) is int and value['bytes'] > 0 and
                isinstance(value.get('drive_id'), str) and bool(value['drive_id']) and
                isinstance(value.get('md5'), str) and bool(re.fullmatch('[0-9a-f]{32}', value['md5'])) and
                isinstance(value.get('sha256'), str) and bool(re.fullmatch('[0-9a-f]{64}', value['sha256'])))

    def separate(record, kind):
        return (record.get('schema_version') == 1 and record.get('status') == 'verified' and record.get('artifact_kind') == kind and
                record.get('changes_native_audio_count') is False and record.get('changes_full_asr_count') is False)

    def original_video(link):
        if not isinstance(link, str):
            return None
        try:
            url = urlsplit(link)
            if url.scheme not in {'http', 'https'} or url.username or url.password:
                return None
            if url.hostname in {'youtu.be', 'www.youtu.be'}:
                return url.path.lstrip('/')
            if url.hostname in {'youtube.com', 'www.youtube.com'} and url.path == '/watch':
                values = parse_qs(url.query).get('v', [])
                return values[0] if len(values) == 1 else None
        except ValueError:
            pass
        return None

    texts, transcripts, variants, qualified, variant_asr, variant_sources = set(), set(), set(), set(), set(), {}
    for record in rows('publisher_companion_manifest.jsonl'):
        kind = record.get('artifact_kind')
        if not isinstance(kind, str) or kind not in {'publisher_authored_article_batch', 'publisher_transcript_batch'}:
            continue
        item = record.get('proof')
        if not separate(record, kind) or not object_proof(item, kind, None):
            continue
        namespace, filename = ('PublisherText', 'publisher-text.zip') if kind == 'publisher_authored_article_batch' else ('PublisherTranscripts', 'publisher-transcripts.zip')
        expected = (re.escape(remote) + r'/[A-Za-z0-9][A-Za-z0-9_.-]{0,119}/' + namespace + '/Batches/' +
                    item['sha256'] + '/' + re.escape(filename))
        if not isinstance(item.get('remote'), str) or not re.fullmatch(expected, item['remote']):
            continue
        entries = record.get('items')
        for entry in entries if isinstance(entries, list) else []:
            if (isinstance(entry, dict) and isinstance(entry.get('video_id'), str) and
                    re.fullmatch('[A-Za-z0-9_-]{11}', entry['video_id']) and entry['video_id'] in targets and
                    all(isinstance(entry.get(key), str) and re.fullmatch('[0-9a-f]{64}', entry[key])
                        for key in ('author_html_sha256', 'text_sha256'))):
                if kind == 'publisher_authored_article_batch':
                    texts.add(entry['video_id'])
                elif (entry.get('text_kind') == 'publisher_transcript_untimed' and
                      entry.get('publisher_declares_transcript') is True and
                      isinstance(entry.get('language'), str) and re.fullmatch(r'en(?:[-_][A-Za-z0-9-]+)?', entry['language']) and
                      original_video(entry.get('original_youtube_link')) == entry['video_id']):
                    transcripts.add(entry['video_id'])
    for record in rows('publisher_variant_manifest.jsonl'):
        kind = record.get('artifact_kind')
        if kind == 'publisher_podcast_audio_variant':
            provenance_kind = 'publisher_podcast_variant_provenance'
        elif (kind == 'qualified_publisher_podcast_audio_variant' and
              record.get('identity_basis') == 'publisher_rss_source_id_references' and
              record.get('direct_watch_link_present') is False and record.get('association_human_verified') is False):
            provenance_kind = 'qualified_publisher_variant_provenance'
        else:
            continue
        row = record_row(record)
        audio, provenance = record.get('audio'), record.get('provenance')
        if (not separate(record, kind) or record.get('native_youtube_bytes') is not False or not row or
                row['video_id'] not in targets or not object_proof(audio, kind) or
                not object_proof(provenance, provenance_kind)):
            continue
        parent = remote + '/' + row['channel_dir'] + '/Videos/' + row['video_id'] + '/PublisherVariants/' + audio['sha256']
        if audio.get('remote') == parent + '/publisher-audio.mp3' and provenance.get('remote') == parent + '/provenance.json':
            variants.add(row['video_id'])
            if kind == 'qualified_publisher_podcast_audio_variant':
                qualified.add(row['video_id'])
            variant_sources[(row['video_id'], audio['sha256'])] = record

    def same_object(left, right):
        # ASR receipts normalize source proofs to object-identity fields, while
        # acquisition receipts additionally retain their publisher-role kind.
        return object_proof(left, None, None) and all(
            left[key] == right[key] for key in ('bytes', 'md5', 'sha256', 'remote', 'drive_id'))

    for record in rows('publisher_variant_asr_manifest.jsonl'):
        video_id, variant_id, run_id = record.get('associated_youtube_id'), record.get('variant_id'), record.get('run_id')
        if not all(isinstance(value, str) for value in (video_id, variant_id, run_id)):
            continue
        source = variant_sources.get((video_id, variant_id))
        if (not source or record.get('schema_version') != 1 or record.get('status') != 'verified' or
                not object_proof(record, 'publisher_variant_asr', 'artifact_kind') or
                record.get('native_youtube_bytes') is not False or record.get('changes_native_audio_count') is not False or
                record.get('changes_native_asr_count') is not False or record.get('quality_state') != 'unreviewed_asr' or
                record.get('channel_dir') != source['channel_dir'] or
                not same_object(record.get('source_audio'), source['audio']) or
                not same_object(record.get('source_provenance'), source['provenance']) or
                not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', run_id)):
            continue
        expected = source['audio']['remote'].rpartition('/')[0] + '/ASR/' + run_id + '/' + run_id + '.zip'
        if record.get('remote') == expected:
            variant_asr.add(video_id)
    return texts, transcripts, variants, qualified, variant_asr


def browser_extension_status(root):
    """A local compatibility receipt cannot establish live source acceptance."""
    record = read_object(root / 'sync/browser_extensions_state.json')
    if not record:
        return {'state': 'not_recorded'}
    invalid = {'state': 'not_verified'}
    if (record.get('schema_version') != 1 or record.get('status') != 'verified_local' or
            record.get('scope') != 'project_isolated_chromium' or record.get('name') != 'uBlock Origin Lite' or
            not all(record.get(key) is True for key in
                    ('local_filtering_verified', 'downloader_coexistence_verified', 'profiles_cleaned'))):
        return invalid
    for key in ('version', 'browser_version'):
        if not isinstance(record.get(key), str) or not re.fullmatch(r'[0-9]{1,8}(?:\.[0-9]{1,8}){1,3}', record[key]):
            return invalid
    if not isinstance(record.get('mode'), str) or record['mode'] not in {'basic', 'optimal', 'complete'}:
        return invalid
    item = record.get('proof')
    if (not isinstance(item, dict) or not isinstance(item.get('path'), str) or
            type(item.get('bytes')) is not int or not 0 < item['bytes'] <= 65_536 or
            not isinstance(item.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', item['sha256'])):
        return invalid
    try:
        relative = Path(item['path'])
        path = (root / relative).resolve()
        if relative.is_absolute() or path.name != 'audit-summary.json' or not path.is_relative_to(root.resolve()):
            return invalid
        content = path.read_bytes()
        if len(content) != item['bytes'] or hashlib.sha256(content).hexdigest() != item['sha256']:
            return invalid
        tested = dt.datetime.fromisoformat(record.get('tested_at', '').replace('Z', '+00:00'))
        if not tested.tzinfo:
            return invalid
    except (OSError, ValueError, TypeError, AttributeError):
        return invalid
    return {'state': 'verified_local', 'name': 'uBlock Origin Lite', 'version': record['version'],
            'browser_version': record['browser_version'], 'mode': record['mode'],
            'tested_at': stamp(tested.timestamp()), 'local_filtering_verified': True,
            'downloader_coexistence_verified': True, 'source_acceptance_verified': False}


def publisher_timed_text_coverage(root, targets, remote):
    """Count independently archived publisher text without inventing audio binding."""
    found = set()
    path = root / 'sync/publisher_caption_manifest.jsonl'
    for line in path.read_text(encoding='utf-8-sig').splitlines() if path.is_file() else []:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        if (record.get('schema_version') != 1 or record.get('status') != 'verified' or
                record.get('artifact_kind') != 'publisher_provided_timed_text_batch' or
                record.get('changes_native_audio_count') is not False or
                record.get('changes_full_asr_count') is not False):
            continue
        bundle = record.get('proof')
        if (not isinstance(bundle, dict) or type(bundle.get('bytes')) is not int or bundle['bytes'] <= 0 or
                not isinstance(bundle.get('drive_id'), str) or not bundle['drive_id'] or
                not isinstance(bundle.get('md5'), str) or not re.fullmatch('[0-9a-f]{32}', bundle['md5']) or
                not isinstance(bundle.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', bundle['sha256'])):
            continue
        entries = record.get('items')
        for item in entries if isinstance(entries, list) else []:
            if not isinstance(item, dict):
                continue
            video, channel = item.get('video_id'), item.get('channel_dir')
            if (not isinstance(video, str) or not re.fullmatch('[A-Za-z0-9_-]{11}', video) or video not in targets or
                    not isinstance(channel, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', channel) or
                    bundle.get('remote') != remote + '/' + channel + '/PublisherCaptions/Batches/' + bundle['sha256'] + '/publisher-captions.zip' or
                    type(item.get('source_bytes')) is not int or item['source_bytes'] <= 0 or
                    not isinstance(item.get('source_sha256'), str) or not re.fullmatch('[0-9a-f]{64}', item['source_sha256']) or
                    type(item.get('segment_count')) is not int or item['segment_count'] <= 0 or
                    not isinstance(item.get('language'), str) or not re.fullmatch('en(?:-[A-Za-z]{2,8})?', item['language']) or
                    item.get('language_basis') != 'publisher_rss_channel' or
                    item.get('track_language_verified') is not False or
                    item.get('caption_kind') != 'publisher_provided_unspecified' or
                    item.get('translation_status') != 'not_declared' or
                    item.get('recording_equivalence_verified') is not False or
                    item.get('speech_coverage_verified') is not False or
                    item.get('native_youtube_caption') is not False or item.get('audio_binding') is not None):
                continue
            try:
                link = urlsplit(item.get('official_blog_youtube_reference', ''))
                blog = urlsplit(item.get('official_blog_url', ''))
                source = urlsplit(item.get('source_url', ''))
                values = parse_qs(link.query).get('v', [])
                linked = link.path.lstrip('/') if link.hostname == 'youtu.be' else (
                    values[0] if link.hostname in {'youtube.com', 'www.youtube.com'} and link.path == '/watch' and len(values) == 1 else None)
                if (linked != video or link.scheme != 'https' or link.username or link.password or
                        blog.scheme != 'https' or not blog.hostname or blog.username or blog.password or
                        source.scheme != 'https' or source.hostname != 'www.buzzsprout.com' or
                        source.username or source.password or source.query or source.fragment or
                        not re.fullmatch(r'/[0-9]+/[0-9]+/transcript\.vtt', source.path)):
                    continue
            except (ValueError, TypeError, AttributeError):
                continue
            found.add(video)
    return found


def publisher_mirror_coverage(root, targets, remote):
    """Count verified publisher mirrors without promoting native YouTube progress."""
    audio_ids, caption_ids, asr_ids, sources = set(), set(), set(), {}
    path = root / 'sync/publisher_mirror_manifest.jsonl'
    if not path.is_file():
        return audio_ids, caption_ids, asr_ids

    def object_proof(value):
        return (isinstance(value, dict) and type(value.get('bytes')) is int and value['bytes'] > 0 and
                isinstance(value.get('drive_id'), str) and bool(value['drive_id']) and
                all(isinstance(value.get(key), str) and re.fullmatch(pattern, value[key])
                    for key, pattern in (('sha256', '[0-9a-f]{64}'), ('md5', '[0-9a-f]{32}'))))

    def exact_reference(record):
        try:
            url = urlsplit(record.get('original_youtube_link', ''))
            if url.scheme not in {'https', 'http'} or url.username or url.password:
                return False
            if url.hostname in {'youtu.be', 'www.youtu.be'}:
                return url.path.lstrip('/') == record.get('associated_youtube_id')
            return (url.hostname in {'youtube.com', 'www.youtube.com'} and url.path == '/watch' and
                    parse_qs(url.query).get('v') == [record.get('associated_youtube_id')])
        except (ValueError, TypeError, AttributeError):
            return False

    for line in path.read_text(encoding='utf-8-sig').splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if (not isinstance(record, dict) or record.get('schema_version') != 1 or
                record.get('status') != 'verified' or
                not all(record.get(key) is False for key in ('native_youtube_bytes', 'changes_native_audio_count',
                    'changes_native_asr_count', 'changes_native_caption_count', 'human_verified'))):
            continue
        qualified = (record.get('kind') == 'qualified_publisher_mirror_audio_variant' and
                     record.get('association_method') == 'publisher_owner_title_date_duration' and
                     record.get('exact_youtube_crossreference') is False)
        exact = (record.get('kind') == 'publisher_mirror_audio_variant' and
                 record.get('association_method') == 'publisher_rss_exact_youtube_id' and
                 record.get('exact_youtube_crossreference') is True and exact_reference(record))
        if not (qualified or exact):
            continue
        row = record_row({'video_id': record.get('associated_youtube_id'), 'channel_dir': record.get('channel_dir')})
        audio, provenance = record.get('audio'), record.get('provenance')
        if (not row or row['video_id'] not in targets or not object_proof(audio) or not object_proof(provenance) or
                audio['drive_id'] == provenance['drive_id'] or record.get('variant_id') != audio['sha256']):
            continue
        parent = (remote + '/' + row['channel_dir'] + '/Videos/' + row['video_id'] +
                  '/PublisherVariants/' + audio['sha256'])
        if (not isinstance(audio.get('remote'), str) or
                not re.fullmatch(re.escape(parent) + r'/publisher-audio\.(?:aac|m4a|mp3|opus|ogg|webm|flac)', audio['remote']) or
                provenance.get('remote') != parent + '/provenance.json'):
            continue
        audio_ids.add(row['video_id'])
        sources[(row['video_id'], audio['sha256'])] = record
        captions = record.get('caption_bundles')
        if not isinstance(captions, list):
            captions = [record.get('caption_bundle')]
        for caption in captions:
            if (object_proof(caption) and caption.get('usable_timed_text') is True and
                    caption['drive_id'] not in {audio['drive_id'], provenance['drive_id']} and
                    isinstance(caption.get('language'), str) and re.fullmatch(r'en(?:[-_][A-Za-z0-9-]+)?', caption['language']) and
                    caption.get('remote') == parent + '/Captions/' + caption['sha256'] + '/captions.zip'):
                caption_ids.add(row['video_id'])
    asr_path = root / 'sync/publisher_variant_asr_manifest.jsonl'
    for line in asr_path.read_text(encoding='utf-8-sig').splitlines() if asr_path.is_file() else []:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        video_id, variant_id, run_id = (record.get(key) for key in ('associated_youtube_id', 'variant_id', 'run_id'))
        if not all(isinstance(value, str) for value in (video_id, variant_id, run_id)):
            continue
        source = sources.get((video_id, variant_id))
        if (not source or record.get('schema_version') != 1 or record.get('status') != 'verified' or
                record.get('artifact_kind') != 'publisher_variant_asr' or not object_proof(record) or
                record['drive_id'] in {source['audio']['drive_id'], source['provenance']['drive_id']} or
                record.get('quality_state') != 'unreviewed_asr' or record.get('channel_dir') != source['channel_dir'] or
                not re.fullmatch('[A-Za-z0-9_-]{1,120}', run_id) or
                not all(record.get(key) is False for key in ('native_youtube_bytes', 'changes_native_audio_count', 'changes_native_asr_count'))):
            continue
        same_source = True
        for key, source_key in (('source_audio', 'audio'), ('source_provenance', 'provenance')):
            value, expected = record.get(key), source[source_key]
            if not object_proof(value) or any(value.get(field) != expected[field] for field in ('bytes', 'drive_id', 'remote', 'md5', 'sha256')):
                same_source = False
        if not same_source:
            continue
        if (record.get('profile') == 'publisher-mirror-german-and-english-asr-v1' and
                record.get('output_contract') != 'original-and-english-v1'):
            continue
        parent = source['audio']['remote'].rpartition('/')[0]
        if record.get('remote') == parent + '/ASR/' + run_id + '/' + run_id + '.zip':
            asr_ids.add(video_id)
    return audio_ids, caption_ids, asr_ids


def snapshot(root, now=None, remote=DEFAULT_REMOTE, managed_roots=()):
    """Allowlisted public values only; no private strings are copied to the result."""
    now = dt.datetime.now(dt.timezone.utc).timestamp() if now is None else now
    latest = latest_records(root / "sync" / "drive_ingest_manifest.jsonl")
    captions = latest_records(root / "sync" / "drive_caption_manifest.jsonl")
    verified = {key for key, rec in latest.items() if proof(receipt_complete, rec, record_row(rec), remote)}
    supported_native = {key for key in verified if
                        latest[key].get('acquisition_profile') == 'stock_headful_wpc_native_full_v1' or
                        latest[key].get('native_batch_profile') in ('stock_headful_wpc_native_batch_v1', 'stock_headful_wpc_native_batch_v2', 'stock_headful_wpc_native_batch_v3', 'stock_headful_wpc_native_batch_v4', 'stock_headful_wpc_native_drc_recovery_v1')}
    browser_verified = set()
    for rec in asr_records(root / 'sync/browser_capture_manifest.jsonl', 'capture_id'):
        row = record_row(rec)
        if row and rec.get('tab') in {'videos', 'shorts', 'streams', ''} and proof(
                browser_receipt_complete, rec, dict(row, tab=rec['tab']), remote):
            browser_verified.add(rec['video_id'])
    archived = verified | browser_verified
    asr_verified = {rec['video_id'] for rec in asr_records(root / 'sync/asr_manifest.jsonl')
                    if asr_receipt_complete(rec, latest.get(rec['video_id'], {}), remote)}
    runtime = read_object(root / 'asr/jobs/batch_runtime_state.json')
    asr_state, asr_reported_at = 'unconfirmed', None
    try:
        reported = dt.datetime.fromisoformat(runtime.get('updated_at', '').replace('Z', '+00:00'))
        if reported.tzinfo and 0 <= now - reported.timestamp() <= 600 and runtime.get('state') in {
                'running', 'complete', 'stopped_error'}:
            asr_state, asr_reported_at = runtime['state'], stamp(reported.timestamp())
    except (ValueError, TypeError, AttributeError):
        pass
    caption_verified, caption_none, verified_tracks = set(), set(), set()
    for key, rec in captions.items():
        row = record_row(rec)
        if rec.get("policy") != CAPTION_POLICY:
            continue
        tracks = rec.get("tracks")
        if not isinstance(tracks, list):
            continue
        for track in tracks:
            if isinstance(track, dict) and proof(caption_track_verified, track, row, remote):
                verified_tracks.add((key, track["track_id"]))
        if proof(caption_receipt_complete, rec, row, remote):
            (caption_none if rec.get("status") == "none" else caption_verified).add(key)
    caption_pending = (verified | captions.keys()) - caption_verified - caption_none
    # A verified track remains available while other tracks or inventory entries
    # need review. Availability is not a claim about complete speech coverage.
    caption_text_available = {key for key, _ in verified_tracks} & archived
    text_available = (asr_verified | caption_text_available) & archived
    text_inventory_complete = (asr_verified | caption_verified) & archived
    unavailable = {key for key, rec in latest.items() if terminal_unavailable(rec)}
    audio = {key for key, rec in latest.items() if rec.get("bytes", 0) and rec.get("sha256")}
    twenty, channels = queue_ids(root, ("queue_newest20_enriched.csv", "queue_newest20.csv"))
    fifty, _ = queue_ids(root, ("queue_newest50_enriched.csv", "queue_newest50.csv"))
    full, _ = queue_ids(root, ("queue_youtube_all_merged.csv", "queue_youtube_all.csv"))
    remaining, _ = queue_ids(root, ("queue_final_round.csv",))
    publisher_texts, publisher_transcripts, publisher_variants, publisher_qualified, publisher_asr = publisher_coverage(root, twenty, remote)
    mirror_audio, mirror_captions, mirror_asr = publisher_mirror_coverage(root, twenty, remote)
    publisher_timed_text = publisher_timed_text_coverage(root, twenty, remote)
    cooldown = read_object(root / "sync" / "drive_ingest_cooldown.json")
    # Support the runner's fixed filename, without exposing it in the export.
    if not cooldown:
        cooldown = read_object(root / "sync" / "drive_cooldown.json")
    until = cooldown.get("until_epoch")
    until = float(until) if isinstance(until, (int, float)) and 0 < until < 253402300799 else None
    drive_until = until or 0
    native_cooldown = read_object(root / 'sync/native_batch_source_cooldown.json')
    native_until = source_deadline([native_cooldown]) if (
        native_cooldown.get('schema_version') == 1 and native_cooldown.get('endpoint') == 'youtube_native_audio') else 0
    # A passive browser refusal can precede BEGIN and therefore has no audio receipt.
    source_until = max(source_deadline(latest.values()), native_until)
    caption_until = source_deadline(captions.values())
    until = max(until or 0, source_until) or None
    supervisor = read_object(root / "sync" / "drive_ingest_resume_state.json")
    configured = supervisor.get("schema_version") == 2
    archive_all = configured and supervisor.get("mode") in {"RunAll", "RunFinal"}
    workers = supervisor.get("download_workers") if configured else 4
    workers = workers if type(workers) is int and 1 <= workers <= 8 else 4
    ceiling = supervisor.get('private_root_ceiling_bytes') if configured else None
    ceiling = ceiling if type(ceiling) is int and 1_000_000_000 <= ceiling <= 17_000_000_000 else 17_000_000_000
    retry = supervisor.get("until_epoch") if configured else None
    caption_wait = configured and (supervisor.get('await_caption_backfill') is True or
        supervisor.get('state') in {'waiting_for_caption_cooldown', 'caption_backfill_retry_budget_exhausted'})
    legacy_source = supervisor.get('source_until_epoch') if configured else None
    legacy_caption_wait = (configured and supervisor.get('cooldown_scope_version') != 1
        and type(legacy_source) in (int, float) and type(retry) in (int, float)
        and caption_until > now and abs(legacy_source - caption_until) < 0.001
        and abs(retry - legacy_source) <= 1.001)
    if type(retry) in (int, float) and 0 < retry < 253402300799 and not caption_wait and not legacy_caption_wait:
        until = max(until or 0, retry)
    provider = 'both' if source_until > now and drive_until > now else \
        'youtube' if source_until > now else 'drive' if drive_until > now else None
    if not provider and until and until > now and configured:
        provider = supervisor.get('cooldown_provider')
        if provider not in {'drive', 'youtube', 'both'}:
            provider = 'youtube' if supervisor.get('state') == 'waiting_for_youtube_cooldown' else 'drive'
    halted = configured and supervisor.get("state") in {
        "stopped", "retry_budget_exhausted", "stopped_after_nonquota_result"}
    state = "paused" if (root / "sync" / "STOP_DRIVE_INGEST").exists() else \
        "paused" if halted else "cooldown" if until and until > now else "ready" if latest or captions else "unknown"
    caption_state = 'paused' if (root / 'sync' / 'STOP_DRIVE_INGEST').exists() or (
        configured and supervisor.get('state') == 'caption_backfill_retry_budget_exhausted') else \
        'cooldown' if caption_until > now else 'pending' if caption_pending else \
        'complete' if captions or verified else 'unknown'
    series = active_native_series(root, now)
    if series:
        state, workers, until, provider = 'running', series['workers'], None, None
        if series['asr_running']:
            asr_state, asr_reported_at = 'running', series['asr_reported_at']
    local_bytes = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(base) / name).is_symlink()]
        for name in files:
            try:
                path = Path(base) / name
                if not path.is_symlink():
                    local_bytes += path.stat().st_size
            except OSError:
                pass
    storage = {"local_bytes": local_bytes, "ceiling_bytes": ceiling}
    if managed_roots:
        all_roots = sorted({root.resolve(), *(Path(p).resolve() for p in managed_roots)}, key=lambda p:len(p.parts))
        included = []
        for candidate in all_roots:
            if not any(candidate.is_relative_to(parent) for parent in included):
                included.append(candidate)
        storage['managed_bytes'] = sum(tree_bytes(path) for path in included)
        plan = read_object(root / 'sync/analysis_resource_plan.json')
        managed_cap = plan.get('accounting_cap_bytes')
        if type(managed_cap) is int and 1_000_000_000 <= managed_cap <= 18_000_000_000:
            storage['managed_ceiling_bytes'] = managed_cap
    resolved = archived | unavailable
    complete20, complete50 = bool(twenty) and twenty <= resolved, bool(fifty) and fifty <= resolved
    return {"schema_version": 1, "generated_at": stamp(now), "scope": "local_youtube_collection",
            "operation": {"state": state, "retry_after": stamp(until) if until else None,
                          "asr_last_reported_state": asr_state, "asr_reported_at": asr_reported_at,
                          "workers": workers, "full_archive_requested": archive_all,
                          "cooldown_provider": provider, "caption_state": caption_state,
                          "caption_retry_after": stamp(caption_until) if caption_until else None},
            "counts": {"verified_pairs": len(verified), "audio_downloaded": len(audio),
                       "supported_native_verified_videos": len(supported_native),
                       "browser_recorded_videos": len(browser_verified), "audio_archived_videos": len(archived),
                       "asr_verified_videos": len(asr_verified),
                       "text_artifact_videos": len((asr_verified | caption_verified) & archived),
                       "text_pending_videos": len(archived - asr_verified - caption_verified),
                       "text_available_videos": len(text_available),
                       "text_inventory_complete_videos": len(text_inventory_complete),
                       "text_missing_videos": len(archived - text_available),
                       "caption_text_available_videos": len(caption_text_available),
                       "caption_inventory_review_videos": len(caption_text_available - caption_verified),
                       "publisher_text_target_videos": len(publisher_texts),
                       "publisher_transcript_target_videos": len(publisher_transcripts),
                       "publisher_audio_variant_target_videos": len(publisher_variants),
                       "publisher_audio_qualified_variant_target_videos": len(publisher_qualified),
                       "publisher_variant_asr_target_videos": len(publisher_asr),
                       "publisher_mirror_audio_target_videos": len(mirror_audio),
                       "publisher_mirror_caption_target_videos": len(mirror_captions),
                       "publisher_mirror_asr_target_videos": len(mirror_asr),
                       "publisher_standalone_timed_text_target_videos": len(publisher_timed_text),
                       "source_audio_available_target_videos": len((archived & twenty) | publisher_variants | mirror_audio),
                       "source_audio_with_text_target_videos": len((text_available & twenty) | publisher_asr | mirror_captions | mirror_asr),
                       "caption_verified_videos": len(caption_verified), "caption_verified_tracks": len(verified_tracks),
                       "caption_none_english": len(caption_none), "caption_pending_videos": len(caption_pending),
                       "unavailable": len(unavailable),
                       "awaiting_upload": len(audio - verified), "channels": channels,
                       "indexed_total": len(full | twenty | fifty), "final_round_indexed": len(remaining)},
            "storage": storage, "browser_support": browser_extension_status(root),
            "stages": [{"key": "newest20", "label": "Newest 20", "total": len(twenty),
                        "verified": len(twenty & archived), "unavailable": len(twenty & unavailable),
                        "state": "complete" if complete20 else "in_progress"},
                       {"key": "newest50", "label": "Extend to 50", "total": len(fifty),
                        "verified": len(fifty & archived), "unavailable": len(fifty & unavailable),
                        "state": "complete" if complete50 else "in_progress" if complete20 else "waiting"},
                       {"key": "final_archive" if archive_all else "final_index",
                        "label": "Archive the remainder" if archive_all else "Index the remainder", "total": len(remaining),
                        "verified": len(remaining & archived), "unavailable": len(remaining & unavailable),
                        "state": ("complete" if remaining and remaining <= resolved else "in_progress" if complete50 else "waiting")
                                 if archive_all else "indexed" if remaining else "waiting"}]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--remote", default=DEFAULT_REMOTE, help="Exact archive destination used by receipt proofs")
    ap.add_argument("--managed-root", type=Path, action="append", default=[],
                    help="Additional project tool/repository roots to include in aggregate storage accounting")
    args = ap.parse_args(argv)
    public = snapshot(args.root, remote=args.remote, managed_roots=args.managed_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    temporary.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.out)
    print(json.dumps(public, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
