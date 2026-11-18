"""One isolated native-audio child of an explicitly admitted batch.

No admission is generated here. The resource owner must create a fresh, exact
admission after reviewing the contract. Existing cooldown files stay immutable.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlsplit

PUBLIC_PIPE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PUBLIC_PIPE))

TARGET = None  # bound from the hash-pinned plan before optional imports
PROFILE = 'stock_headful_wpc_native_batch_v5_bulk_recovery6_prototype'
LEASE_NAME = 'stock_wpc_batch_v5_bulk_recovery6_prototype_lease.json'
STOP_NAME = 'STOP_STOCK_WPC_BATCH_V5_BULK_RECOVERY6_PROTOTYPE'
COOLDOWN_NAME = 'stock_wpc_batch_v5_bulk_recovery6_prototype_source_cooldown.json'
HTTP_STATE_NAME = 'stock_wpc_batch_v5_bulk_recovery6_prototype_http_state.json'
# yt-dlp's numeric filter grammar does not accept a leading minus sign.
# The pre-transfer raw-inventory gate still requires exactly preference -1.
LEGACY_FORMAT_SELECTOR = ('bestaudio[protocol=https][vcodec=none][language_preference<0][format_id!*=drc][ext=m4a]/'
                          'bestaudio[protocol=https][vcodec=none][language_preference<0][format_id!*=drc]')
GO_WAIT_SECONDS = 60

LIMITS = {'audio_bytes': 64 * 1024**2, 'python_body_bytes': 100 * 1024**2,
          'python_wire_requests': 64, 'browser_observed_requests': 256,
          'profile_bytes': 150_000_000, 'spool_bytes': 256_000_000,
          'rate_bytes_per_second': 2 * 1024**2, 'bootstrap_seconds': 90, 'wall_seconds': 600}


class Held(Exception):
    def __init__(self, code): self.code = code; super().__init__(code)


def control_paths(root):
    sync = Path(root) / 'sync'
    return {'lease_path': sync / LEASE_NAME, 'batch_stop_path': sync / STOP_NAME,
            'source_cooldown_path': sync / COOLDOWN_NAME, 'http_state_path': sync / HTTP_STATE_NAME}


def need(value, code):
    if not value: raise Held(code)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


CONTROL_REPLACE_DELAYS = (.025, .05, .1, .2, .4)


def write(path, value, *, on_failure=None):
    """Commit one control file; retry only bounded Windows sharing failures.

    Every writer owns a distinct same-directory temporary file. A failed commit
    never replaces the old proof or reports success, including result.json.
    """
    path = Path(path)
    raw = encoded(value); need(len(raw) <= 16 * 1024**2, 'control_size')
    tmp = None; first = None; first_summary = None; retries = 0; stage = 'create'
    def failure(error, retry):
        nonlocal first, first_summary
        safe = {'stage': stage, 'exception_class': 'PermissionError' if isinstance(error, PermissionError) else 'OSError'}
        for key in ('errno', 'winerror'):
            number = getattr(error, key, None)
            if type(number) is int and 0 <= number <= 65535: safe[key] = number
        if first is None: first = error; first_summary = safe
        if on_failure is not None: on_failure(safe, retry)
    try:
        descriptor, name = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=path.parent)
        tmp = Path(name); stage = 'write_fsync'
        with os.fdopen(descriptor, 'wb') as output:
            output.write(raw); output.flush(); os.fsync(output.fileno())
        stage = 'replace'
        for attempt in range(len(CONTROL_REPLACE_DELAYS) + 1):
            try:
                os.replace(tmp, path)
                return {'retry_attempts': retries, 'first_failure': first_summary}
            except OSError as error:
                retry = getattr(error, 'winerror', None) in {5, 32, 33} and attempt < len(CONTROL_REPLACE_DELAYS)
                failure(error, retry)
                if not retry: raise
                retries += 1; time.sleep(CONTROL_REPLACE_DELAYS[attempt])
    except OSError as error:
        if first is None: failure(error, False)
        # Held is deliberately not OSError: yt-dlp must not relabel a failed
        # local progress write as UnavailableVideoError.
        failure_error = Held('control_write_failed')
        failure_error.control_diagnostic = {'stage':stage,'target':path.name if path.name in {'result.json','progress.json'} else 'other_control','retry_attempts':retries}
        raise failure_error from first
    finally:
        if tmp is not None:
            try: tmp.unlink(missing_ok=True)
            except OSError: pass  # Only our temporary file; original failure still propagates.


def read(path):
    need(Path(path).stat().st_size <= 16 * 1024**2, 'control_size')
    return json.loads(Path(path).read_bytes())


def tree_bytes(path):
    total = 0
    for folder, directories, files in os.walk(path):
        for name in directories + files:
            p = Path(folder) / name
            need(not p.is_symlink() and not getattr(p, 'is_junction', lambda: False)(), 'storage_link')
        for name in files:
            try: total += (Path(folder) / name).stat().st_size
            except FileNotFoundError: pass
    return total


def endpoint(url):
    parsed = urlsplit(url); host = parsed.hostname or ''
    if host.endswith('.googlevideo.com'): return 'media'
    if host in {'www.youtube.com', 'm.youtube.com', 'youtube.com', 'youtubei.googleapis.com'}:
        if parsed.path == '/api/timedtext': return 'caption'
        if parsed.path in {'/', '/watch'} or '/youtubei/v1/player' in parsed.path: return 'source_control'
        return 'auxiliary'
    return 'other'


_HTTP_POLICY=None
def http_policy():
    global _HTTP_POLICY
    if _HTTP_POLICY is None:
        import importlib.util
        path=Path(__file__).with_name('native_http_policy.py')
        spec=importlib.util.spec_from_file_location('owned_native_http_v5_policy',path)
        value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);_HTTP_POLICY=value
    return _HTTP_POLICY


_BULK_CONTRACT=None

def bulk_contract():
    global _BULK_CONTRACT
    if _BULK_CONTRACT is None:
        import importlib.util
        spec=importlib.util.spec_from_file_location('owned_native_bulk_contract',Path(__file__).with_name('bulk_contract.py'))
        value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);_BULK_CONTRACT=value
    return _BULK_CONTRACT


def retain_http_failure(state, event, refusal):
    """Keep first evidence plus at most one stronger global HTTP observation."""
    if state.http_failure is None:
        state.http_failure = event; state.http_failure_at_epoch = time.time()
    elif (state.http_failure['action'] == 'item_quarantine' and event['action'] == 'global_stop'
          and state.http_escalation is None):
        state.http_escalation = event; state.http_escalation_at_epoch = time.time()
    else:
        return
    state.error = event['code']; state.refusal = refusal; state.save(force=True)


def record_browser_response(state, url, status, retry_after=None):
    """Observe WPC's homepage browser without attributing its media to TARGET."""
    category = endpoint(url)
    key = category + ':' + str(status)
    state.browser_status_counts[key] = state.browser_status_counts.get(key, 0) + 1
    if status not in (403, 429):
        return False
    if category == 'media' and status == 403 and retry_after is None:
        # Stock WPC navigates to the homepage, not the requested video. These
        # events have no selected-format or video binding, even after Python
        # selects a format. Keep evidence without manufacturing a target refusal.
        key = str(status)
        state.browser_unbound_media_failures[key] = state.browser_unbound_media_failures.get(key, 0) + 1
        state.save(force=True)
        return False
    if category == 'source_control' or status == 429 or status == 403 and retry_after is not None:
        event = http_policy().classify_http_failure(status, url, url, None,
            state.phase, TARGET, None, transport='wpc_browser', selection_validated=False,
            retry_after=retry_after, now_epoch=time.time())
        retain_http_failure(state, event, {'endpoint': category, 'status': status, 'requested_video_id': TARGET,
                         'transport_origin': 'wpc_browser', 'source_binding': 'provider_source_control',
                         'requested_video_binding_verified': False})
        return True
    return False


def record_python_http_refusal(state, url, status, *, final_url=None, method='GET', retry_after=None):
    """Every refusal ends this child; only exactly bound media403 is item-scoped."""
    if status not in (403, 429):
        return
    event = http_policy().classify_http_failure(status, url, final_url,
        state.selected_asset_url, state.phase, TARGET, state.selected_summary,
        transport='yt_dlp_python', method=method, selection_validated=state.selected_metadata_saved,
        retry_after=retry_after, now_epoch=time.time())
    retain_http_failure(state, event, {'endpoint': endpoint(url), 'status': status, 'video_id': TARGET,
                     'transport_origin': 'yt_dlp_python'})


def original_track_proof(info):
    # Pinned _video.py assigns 10 only from an explicit original-track label
    # (or a manifest language matched to that label); default is a separate 5.
    need(info.get('language_preference') == 10 and isinstance(info.get('language'), str) and
         re.fullmatch(r'[A-Za-z]{2,3}(?:-[A-Za-z0-9]+)*', info['language']) and
         re.search(r'\boriginal\b', info.get('format_note', ''), re.I), 'original_audio_unproven')
    return {'basis': 'pinned_ytdlp_explicit_original_track_label', 'language': info['language'],
            'source_language': info['language'], 'original_explicitly_verified': True, 'origin_inferred': False,
            'language_preference': 10, 'original_label_present': True, 'default_is_not_original': True}


def validate_selection(info, target, expected, maximum, codecs, legacy=None):
    need(info.get('id') == target and not info.get('is_live') and info.get('live_status') not in {'is_live', 'is_upcoming'}, 'source_identity')
    need(info.get('protocol') == 'https' and info.get('vcodec') == 'none' and info.get('acodec') in codecs, 'native_audio_selection')
    need(info.get('isDrc') is not True and info.get('is_drc') is not True and
         not re.search(r'(?:^|-)drc(?:-|$)', str(info.get('format_id', '')), re.I), 'native_audio_selection')
    need(info.get('has_drm') is not True, 'drm_not_admitted')
    try: original = original_track_proof(info)
    except Held:
        try: from .native_track_policy import legacy_selection_proof
        except ImportError: from native_track_policy import legacy_selection_proof
        original = legacy_selection_proof(info, legacy)
        need(original is not None, 'original_audio_unproven')
    duration = info.get('duration')
    need(type(duration) in (int, float) and math.isfinite(duration) and duration > 0 and
         (expected is None or abs(duration - expected) <= max(2, duration * .002)), 'source_duration')
    declared = info.get('filesize')
    need(declared is None or (type(declared) is int and 0 < declared <= maximum), 'asset_budget_deferred')
    available = info.get('available_at')
    need(available is None or (type(available) in (int, float) and math.isfinite(available)), 'availability_timestamp')
    return original


def diagnostic_reason(message):
    """Classify anchored upstream errors in memory; never retain their text."""
    text = str(message)[:4096].strip()
    text = re.sub(r'^ERROR:\s*', '', text, flags=re.I)
    text = re.sub(r'^\[youtube\]\s+[A-Za-z0-9_-]{11}:\s*', '', text, flags=re.I)
    patterns = ((r'^Requested format is not available(?:[.!]|$)', 'format_unavailable'),
        (r'^No video formats found(?:[!.]|$)', 'no_formats'),
        (r'^This video is DRM protected', 'drm_not_admitted'),
        (r'^(?:Premieres in\b|This live event will begin\b)', 'deferred_live'),
        (r'^Sign in to confirm you(?:[\u2019\']re| are) not a bot', 'bot_check'),
        (r'^(?:CAPTCHA\b|Protection rejected\b)', 'access_challenge'),
        (r'^(?:Private video\b|This video is private\b)', 'private_video'),
        (r'^Video unavailable(?:[.!:]|$)', 'video_unavailable'))
    return next((code for pattern, code in patterns if re.search(pattern, text, re.I)), None)


def safe_exception_chain(error):
    """Bounded classes/codes/frame locations only; never exception messages."""
    names = {'Held', 'QualityHold', 'DownloadError', 'ExtractorError', 'UnavailableVideoError',
        'HTTPError', 'TransportError', 'ContentTooShortError', 'OSError', 'PermissionError',
        'FileNotFoundError', 'TimeoutError', 'ConnectionError', 'ConnectionResetError',
        'ConnectionAbortedError', 'BrokenPipeError', 'RuntimeError', 'ValueError', 'TypeError',
        'AttributeError', 'NameError', 'OverflowError', 'AssertionError'}
    codes = {'deadline', 'bootstrap_deadline', 'owner_stop', 'batch_source_stop', 'lease_revoked',
        'source_history_changed', 'python_body_cap', 'python_request_cap', 'audio_byte_cap',
        'short_local_write', 'output_scope', 'storage_link', 'source_403', 'source_429',
        'browser_observed_request_cap', 'original_audio_unproven', 'native_completion_unproven',
        'audio_probe_failed', 'audio_probe_invalid', 'audio_extent', 'warning_decode_failed', 'control_write_failed'}
    todo = [('root', error)]; seen = set(); nodes = []
    while todo and len(nodes) < 8:
        link, value = todo.pop(0)
        if not isinstance(value, BaseException) or id(value) in seen: continue
        seen.add(id(value)); name = type(value).__name__
        node = {'link': link, 'exception_class': name if name in names else 'OtherError'}
        for field in ('errno', 'winerror'):
            number = getattr(value, field, None)
            if type(number) is int and 0 <= number <= 65535: node[field] = number
        code = getattr(value, 'code', None)
        if name in {'Held', 'QualityHold'} and isinstance(code, str) and code in codes: node['code'] = code
        frames = []; frame = value.__traceback__
        while frame is not None and len(frames) < 8:
            filename = Path(frame.tb_frame.f_code.co_filename).name
            function = frame.tb_frame.f_code.co_name
            frames.append({'module': filename if re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', filename) else 'other',
                'function': function if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}', function) else 'other',
                'line': frame.tb_lineno})
            frame = frame.tb_next
        node['frames'] = frames; nodes.append(node)
        todo.extend([('cause', value.__cause__), ('context', value.__context__), ('wrapped_cause', getattr(value, 'cause', None))])
        info = getattr(value, 'exc_info', None)
        if isinstance(info, tuple) and len(info) == 3: todo.append(('exc_info', info[1]))
    return {'schema_version': 1, 'nodes': nodes, 'truncated': bool(todo), 'raw_messages_retained': False}


def save_format_inventory(state, info):
    need(info.get('id') == TARGET, 'inventory_identity')
    formats = info.get('formats') or []
    need(isinstance(formats, list), 'format_inventory_shape')
    output = []
    def token(value):
        return value if isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_.:+-]{1,80}', value) else None
    for value in formats[:512]:
        if not isinstance(value, dict): continue
        fmt = {key: token(value.get(key)) for key in ('format_id', 'protocol', 'ext', 'acodec', 'vcodec', 'language')}
        # This hook precedes yt-dlp protocol completion. URL scheme is a
        # transport hint only: it never establishes server access or success.
        url = value.get('url')
        fmt['url_present'] = isinstance(url, str) and bool(url)
        try: scheme = urlsplit(url).scheme.lower() if fmt['url_present'] else None
        except ValueError: scheme = None
        fmt['url_scheme'] = scheme if scheme in {'https', 'http'} else ('other' if scheme else None)
        fmt['protocol_state'] = 'reported' if fmt['protocol'] else 'pre_normalization_missing'
        fmt['transport_hint'] = fmt['protocol'] or fmt['url_scheme']
        fmt['access_proven'] = False
        for key in ('language_preference', 'filesize', 'filesize_approx', 'duration', 'available_at'):
            number = value.get(key)
            fmt[key] = number if type(number) in (int, float) and math.isfinite(number) and abs(number) <= 2**53 else None
        note = value.get('format_note')
        fmt['original_label_present'] = bool(isinstance(note, str) and re.search(r'\boriginal\b', note[:4096], re.I))
        fmt['has_drm'] = value.get('has_drm') if type(value.get('has_drm')) is bool else None
        fmt['drc_variant'] = bool(re.search(r'(?:^|-)drc(?:-|$)', fmt['format_id'] or '', re.I))
        fmt['eligible_original_https_audio'] = bool(fmt['protocol'] == 'https' and fmt['vcodec'] == 'none' and
            fmt['acodec'] in {'opus', 'aac', 'mp4a.40.2'} and fmt['language_preference'] == 10 and
            fmt['original_label_present'] and fmt['language'] and fmt['has_drm'] is not True and not fmt['drc_variant'])
        output.append(fmt)
    live = info.get('live_status')
    record = {'schema_version': 1, 'video_id': TARGET, 'stage': 'before_format_selection',
        'worker_sha256': digest(__file__), 'format_count': len(formats), 'retained_format_count': len(output),
        'truncated': len(formats) > 512, 'formats': output,
        'original_https_audio_candidates': sum(x['eligible_original_https_audio'] for x in output),
        'protocol_pending_count': sum(x['protocol_state'] == 'pre_normalization_missing' for x in output),
        'https_audio_transport_hints': sum(x['transport_hint'] == 'https' and x['vcodec'] == 'none' and x['acodec'] not in {None, 'none'} for x in output),
        'transport_hints_prove_access': False,
        'live_status': live if live in {'not_live', 'is_live', 'is_upcoming', 'was_live', 'post_live'} else None,
        'is_live': info.get('is_live') if type(info.get('is_live')) is bool else None}
    write(state.run / 'format-inventory.json', record)
    state.format_inventory_saved = True; state.save(force=True)


def completed_file(state, run):
    """A limit sentinel is not success without one finished native file."""
    files = [p for p in run.glob('native-audio.*') if p.suffix != '.part']
    need(state.finished_count == 1 and state.finished_bytes == state.audio_written > 0 and
         len(files) == 1 and not list(run.glob('*.part')) and
         files[0].stat().st_size == state.audio_written and state.selected_metadata_saved,
         'native_completion_unproven')
    return files[0]


def persist_selection(state, info, build_metadata):
    """Persist only the sanitizer's output before starting the media request."""
    need(not state.selected_metadata_saved, 'multiple_selections_not_admitted')
    state.selected_summary = {k: info.get(k) for k in ('id','format_id','protocol','ext','acodec','vcodec','language',
        'language_preference','duration','filesize','available_at')}
    metadata = build_metadata(info, {'video_id': TARGET}, time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    metadata['native_selection'] = {'phase': 'validated_before_native_transfer', 'format': state.selected_summary,
        'original_audio_evidence': state.original_track, 'worker_sha256': digest(__file__)}
    if state.original_track.get('origin_inferred'):
        state.selected_summary['language'] = None
        metadata['languages']['audio'] = None
        metadata['metadata']['language'] = None
        metadata['native_selection']['source_language'] = None
    if state.raw_audio_inventory is not None:
        metadata['native_track_inventory'] = state.raw_audio_inventory
    write(state.run / 'selected-metadata.info.json', metadata)
    state.selected_metadata_saved = True
    state.phase = 'native_transfer'; state.save(force=True)


def record_progress(state, value):
    if value.get('status') == 'finished':
        need(value.get('info_dict', {}).get('id') == TARGET, 'finished_identity')
        count = value.get('downloaded_bytes')
        need(type(count) is int and count > 0, 'finished_bytes')
        with state._save_lock:
            state.finished_count += 1; state.finished_bytes = count
            state.save(force=True)
    elif value.get('status') == 'downloading':
        state.save()


def observe_full_native_http_transfer(state,run,quality):
    """Record the full bound transfer only after strict local quality passes."""
    if state.full_native_http_transfer_observed is not None:return
    audio=completed_file(state,run)
    selected=state.selected_summary or {};declared=selected.get('filesize')
    if not(type(declared) is int and declared>0 and declared==state.audio_written==state.finished_bytes and state.selected_http_response and state.http_failure is None and state.http_escalation is None and state.global_failure_code is None):return
    if quality.get('quality_state')!='complete_native_audio' or quality.get('strict_probe_passed') is not True:return
    write(run/'source-quality.json',quality)
    strict_quality={key:quality[key] for key in ('quality_state','strict_probe_passed','audio_streams','video_streams','packet_count','container_duration_seconds','source_duration_seconds','codec')}
    proof={'finished_count':state.finished_count,'finished_bytes':state.finished_bytes,'audio_bytes_written':state.audio_written,'known_selected_size':declared,
        'strict_quality':strict_quality,'quality_proof_sha256':digest(run/'source-quality.json'),'quality_module_sha256':digest(PUBLIC_PIPE/'native_batch_quality.py'),
        'format_identity':http_policy().v4._format(selected),'worker_sha256':digest(__file__),'selected_metadata_sha256':digest(run/'selected-metadata.info.json'),**state.selected_http_response}
    event=http_policy().full_transfer_event(TARGET,proof)
    state.full_native_http_transfer_at_epoch=time.time();state.full_native_http_transfer_observed=event;state.save(force=True)


def download_once(ydl, state, run, url):
    from yt_dlp.utils import MaxDownloadsReached
    try:
        ydl.extract_info(url, download=True)
    except MaxDownloadsReached:
        # This sentinel also occurs on skipped/simulated paths. Require the
        # finished callback and exact final bytes while this context is alive.
        completed_file(state, run)
        state.limit_sentinel_observed = True
    state.guard()


def validate(config, admission, *, now=None):
    now = time.time() if now is None else now
    config = read(config)
    settings_path = Path(config['settings_path'])
    admission,_ = bulk_contract().frame_admission(settings_path,admission,now=now)
    need(admission.get('schema_version') == 1 and admission.get('state') == 'active' and admission.get('authorized') is True and
         admission.get('profile') == PROFILE and admission.get('preserve_existing_cooldowns') is True and
         admission.get('worker_sha256') == digest(__file__) and admission.get('settings_sha256') == digest(settings_path), 'admission_scope')
    need(type(admission.get('expires_at_epoch')) in (int, float) and now < admission['expires_at_epoch'], 'admission_expired')
    settings = read(settings_path)
    root_path=settings.get('root_admission_path');need(isinstance(root_path,str) and digest(root_path)==admission.get('root_admission_sha256'),'v5_root_admission_pin')
    root_grant=read(root_path);need(root_grant.get('authorized') is True and root_grant.get('owner')=='root' and root_grant.get('profile')==PROFILE and root_grant.get('synthetic_v4_breaker_override_authorized') is True and root_grant.get('source_scope_authorized') is True,'v5_root_admission_required')
    need(admission.get('source_scope_authorized') is True and admission.get('owner') == settings.get('owner') and
         admission.get('lease_id') == settings.get('lease_id') and admission.get('max_workers') == settings.get('workers') and
         admission.get('spool_cap_bytes') == settings.get('spool_cap_bytes'), 'admission_binding')
    need(admission.get('plan_sha256') == digest(settings['plan_path']), 'plan_changed')
    plan = read(settings['plan_path'])
    items = [i for i in plan['items'] if i.get('video_id') == config.get('video_id')]
    need(len(items) == 1 and config.get('item') == items[0], 'target_binding')
    item = items[0]
    root = Path(settings['private_root']).resolve(); run = Path(config['run_root']).resolve()
    expected = root / 'stock_wpc_batch_v5_bulk_recovery6_prototype/jobs' / admission['plan_sha256'][:16] / item['video_id']
    need(run == expected.resolve(), 'run_path')
    controls = control_paths(root)
    need(Path(config.get('lease_path', '')).resolve() == controls['lease_path'] and
         Path(config.get('batch_stop_path', '')).resolve() == controls['batch_stop_path'], 'control_paths')
    settings.update(config)
    settings['expected_duration_seconds'] = item.get('duration_seconds')
    settings['audio_limit_bytes'] = item.get('max_audio_bytes', settings['max_asset_bytes'])
    need(type(settings['audio_limit_bytes']) is int and 0 < settings['audio_limit_bytes'] <= 2_000_000_000, 'asset_budget')
    LIMITS.update(audio_bytes=settings['audio_limit_bytes'], python_body_bytes=settings['audio_limit_bytes'] + 100 * 1024**2,
                  python_wire_requests=math.ceil(settings['audio_limit_bytes'] / (8 * 1024**2)) + 32,
                  spool_bytes=settings['audio_limit_bytes'] + 240_000_000, wall_seconds=settings['job_wall_seconds'])
    need(Path(settings['browser_executable']).name.lower() in {'chrome.exe', 'chromium.exe'} and
         'ms-playwright' in Path(settings['browser_executable']).parts, 'owned_browser_required')
    roots = [Path(p).resolve() for p in settings['managed_roots']]
    need(len(roots) == 6 and any('ms-playwright' in p.parts for p in roots) and
         all(any(p.is_relative_to(r) for r in roots) for p in (root, Path(settings['browser_executable']), Path(sys.prefix))), 'managed_roots')
    duration = settings['expected_duration_seconds']
    need(duration is None or (type(duration) in (int, float) and math.isfinite(duration) and duration > 0), 'duration_admission')
    for pin in settings['code_pins']:
        need(digest(pin['path']) == pin['sha256'], 'dependency_changed')
    need(settings.get('preserved_controls') and all(digest(p['path']) == p['sha256'] for p in settings['preserved_controls']), 'source_history_changed')
    return settings, run


class State:
    def __init__(self, settings, run, expires):
        self.settings, self.run, self.expires = settings, run, expires
        self.started = time.monotonic(); self.phase = 'bootstrap'; self.error = None
        self.python_requests = self.dispatches = self.python_bytes = self.audio_written = 0
        self.browser_requests = 0; self.browser_status_counts = {}; self.browser = None
        self.browser_unbound_media_failures = {}
        self.audio_md5, self.audio_sha256 = hashlib.md5(), hashlib.sha256()
        self.last_check = self.last_save = 0; self.finished = False; self.available_at = None
        self.pump = None
        self.original_track = None
        self.selected_asset_url = None  # ephemeral; never serialized or exported
        self.http_failure = None
        self.http_failure_at_epoch = None
        self.http_escalation = None; self.http_escalation_at_epoch = None
        self.global_failure_code = None; self.global_failure_at_epoch = None
        self.selected_summary = None; self.selected_metadata_saved = False
        self.finished_count = 0; self.finished_bytes = None; self.limit_sentinel_observed = False
        self.refusal = None
        self.selected_http_response=None
        self.full_native_http_transfer_observed=None
        self.full_native_http_transfer_at_epoch=None
        self.format_inventory_saved = False; self.diagnostic_reason = None
        self.raw_audio_inventory = None
        self._save_lock = threading.RLock()
        self.control_write_first_failure = None
        self.control_write_failure_count = self.control_write_retry_count = self.control_write_recovered_count = 0

    def guard(self):
        if self.pump: self.pump()
        need(not self.error, self.error or 'held')
        need(time.time() < self.expires and time.monotonic() - self.started < LIMITS['wall_seconds'], 'deadline')
        if self.phase == 'bootstrap': need(time.monotonic() - self.started < LIMITS['bootstrap_seconds'], 'bootstrap_deadline')
        if time.monotonic() - self.last_check >= 1:
            need(not (self.run / 'STOP').exists(), 'owner_stop')
            if self.settings.get('batch_stop_path'): need(not Path(self.settings['batch_stop_path']).exists(), 'batch_source_stop')
            if self.settings.get('lease_path'):
                lease = read(self.settings['lease_path'])
                need(lease.get('state') == 'active' and lease.get('lease_id') == self.settings['lease_id'] and
                     lease.get('expires_at_epoch', 0) > time.time(), 'lease_revoked')
            for pin in self.settings['preserved_controls']: need(digest(pin['path']) == pin['sha256'], 'source_history_changed')
            self.last_check = time.monotonic()

    def summary(self):
        return {'phase': self.phase, 'error_class': self.error, 'python_wire_requests': self.python_requests,
            'python_dispatches': self.dispatches, 'python_body_bytes': self.python_bytes, 'audio_bytes_written': self.audio_written,
            'browser_observed_requests': self.browser_requests, 'browser_http_status_counts': self.browser_status_counts,
            'browser_unbound_media_failures': self.browser_unbound_media_failures,
            'browser_media_failure_binding': 'unbound_provider_context',
            'browser_wire_request_count_is_hard_bound': False, 'browser_response_body_bytes_not_measured': True,
            'available_at_epoch': self.available_at, 'elapsed_seconds': round(time.monotonic() - self.started, 3),
            'selected_metadata_saved': self.selected_metadata_saved, 'native_finished_count': self.finished_count,
            'native_finished_bytes': self.finished_bytes, 'limit_sentinel_observed': self.limit_sentinel_observed,
            'source_refusal': self.refusal, 'http_failure': self.http_failure,
            'full_native_http_transfer_observed':self.full_native_http_transfer_observed,
            'full_native_http_transfer_at_epoch':self.full_native_http_transfer_at_epoch,
            'http_failure_at_epoch': self.http_failure_at_epoch,
            'http_escalation': self.http_escalation, 'http_escalation_at_epoch': self.http_escalation_at_epoch,
            'global_failure_code': self.global_failure_code, 'global_failure_at_epoch': self.global_failure_at_epoch,
            'format_inventory_saved': self.format_inventory_saved,
            'diagnostic_reason': self.diagnostic_reason,
            'control_write_diagnostics': {'first_failure': self.control_write_first_failure,
                'failure_count': self.control_write_failure_count, 'retry_count': self.control_write_retry_count,
                'recovered_writes': self.control_write_recovered_count},
            'legacy_track_inference_eligible': bool(self.raw_audio_inventory and self.raw_audio_inventory.get('eligible'))}

    def save(self, force=False):
        with self._save_lock:
            if force or time.monotonic() - self.last_save >= 1:
                def failed(safe, retry):
                    if self.control_write_first_failure is None: self.control_write_first_failure = safe
                    self.control_write_failure_count += 1
                    self.control_write_retry_count += int(retry)
                outcome = write(self.run / 'progress.json', self.summary(), on_failure=failed)
                if outcome['retry_attempts']: self.control_write_recovered_count += 1
                # Retry evidence appears in the next progress/final result;
                # last_save changes only after an acknowledged atomic commit.
                self.last_save = time.monotonic()


class MeteredResponse:
    def __init__(self, response, state): self.response, self.state = response, state
    def __getattr__(self, name): return getattr(self.response, name)
    def read(self, amount=None):
        self.state.guard()
        left = LIMITS['python_body_bytes'] - self.state.python_bytes
        need(left > 0, 'python_body_cap')
        data = self.response.read(left if amount is None or amount < 0 else min(left, amount))
        self.state.python_bytes += len(data)
        return data
    def __enter__(self): return self
    def __exit__(self, *args): self.response.close()


class MeteredFile:
    def __init__(self, stream, state): self.stream, self.state = stream, state
    def __getattr__(self, name): return getattr(self.stream, name)
    def write(self, data):
        self.state.guard()
        need(self.state.audio_written + len(data) <= LIMITS['audio_bytes'], 'audio_byte_cap')
        n = self.stream.write(data); need(n == len(data), 'short_local_write')
        self.state.audio_written += n
        self.state.audio_md5.update(data); self.state.audio_sha256.update(data)
        return n
    def close(self):
        if not self.stream.closed:
            self.stream.flush(); os.fsync(self.stream.fileno()); self.stream.close()


def child(config, admission_path):
    global TARGET
    admission = read(admission_path); settings, run = validate(config, admission)
    TARGET = settings['video_id']
    waiting = time.monotonic()
    write(run/'bootstrap.json',{'schema_version':1,'phase':'waiting_for_parent_GO','pid':os.getpid(),'at_epoch':time.time(),'source_started':False,'GO_wait_seconds':GO_WAIT_SECONDS})
    while not (run / 'GO').is_file() and time.monotonic() - waiting < GO_WAIT_SECONDS:
        time.sleep(.05)
    need((run / 'GO').is_file(), 'parent_job_not_bound')
    temp = run / 'profile-temp'; temp.mkdir(exist_ok=True)
    os.environ['TEMP'] = os.environ['TMP'] = str(temp)
    os.environ['DENO_DIR'] = str(temp / 'deno-cache')
    import tempfile
    tempfile.tempdir = None
    import asyncio
    import http.client
    import logging
    logging.disable(logging.CRITICAL)
    import nodriver
    import yt_dlp
    from yt_dlp import plugins
    from yt_dlp.globals import plugin_dirs
    from yt_dlp.networking._urllib import UrllibRH
    from yt_dlp.networking.exceptions import HTTPError
    import yt_dlp.downloader.common as fd_common
    sys.path.insert(0, settings['pipeline_directory'])
    import media_metadata
    import native_audio_sink
    import drive_ingest as storage
    from native_batch_quality import inspect_quality, QualityHold
    from native_track_policy import legacy_track_inventory
    from yt_dlp.extractor.youtube import YoutubeIE
    state = State(settings, run, admission['expires_at_epoch'])
    state.started=waiting  # GO wait/imports share the existing90-second bootstrap budget
    asyncio.set_event_loop(asyncio.new_event_loop())
    original_start, original_open, original_put = nodriver.start, fd_common.sanitize_open, http.client.HTTPConnection.putrequest
    original_formats = YoutubeIE._extract_formats_and_subtitles

    def observed_formats(extractor, video_id, player_responses, player_url, live_status, duration):
        # Observe the entire returned raw arrays before upstream URL/SABR filters.
        # Original objects, callbacks and generator behavior remain unchanged.
        need(video_id == TARGET, 'raw_inventory_identity')
        state.raw_audio_inventory = legacy_track_inventory(video_id, player_responses, 'mweb')
        write(run / 'raw-audio-inventory.json', state.raw_audio_inventory)
        return original_formats(extractor, video_id, player_responses, player_url, live_status, duration)

    async def observed_start(*args, **kwargs):
        config_object = kwargs.get('config')
        need(config_object is not None and not config_object.headless and not config_object.expert and
             Path(config_object.user_data_dir).resolve().is_relative_to(temp), 'browser_configuration')
        browser = await original_start(*args, **kwargs)
        state.browser = browser
        browser_loop = asyncio.get_running_loop()
        def pump():
            if not browser_loop.is_running() and not browser_loop.is_closed():
                browser_loop.run_until_complete(asyncio.sleep(0))
        state.pump = pump
        async def requested(event):
            state.browser_requests += 1
            if state.browser_requests > LIMITS['browser_observed_requests']:
                state.error = 'browser_observed_request_cap'; browser.stop()
        async def responded(event):
            retry_after = next((v for k, v in event.response.headers.items() if k.lower() == 'retry-after'), None)
            if record_browser_response(state, event.response.url, int(event.response.status), retry_after):
                browser.stop()
        browser.main_tab.add_handler(nodriver.cdp.network.RequestWillBeSent, requested)
        browser.main_tab.add_handler(nodriver.cdp.network.ResponseReceived, responded)
        await browser.main_tab.send(nodriver.cdp.network.enable())
        return browser

    def put_request(connection, method, url, *args, **kwargs):
        state.guard(); need(state.python_requests < LIMITS['python_wire_requests'], 'python_request_cap')
        state.python_requests += 1
        return original_put(connection, method, url, *args, **kwargs)

    def open_file(filename, mode):
        target = Path(filename).resolve()
        need(target.parent == run and target.name.startswith('native-audio.') and mode == 'wb', 'output_scope')
        handle, final = original_open(filename, mode)
        return MeteredFile(handle, state), final

    class Quiet:
        def debug(self, *_): pass
        def warning(self, *_): pass
        def error(self, message):
            reason = diagnostic_reason(message)
            if reason:
                state.diagnostic_reason = reason
                if reason in {'bot_check', 'access_challenge'}:
                    state.error = reason
                    if state.global_failure_code is None:
                        state.global_failure_code = reason; state.global_failure_at_epoch = time.time()
                state.save(force=True)

    class NativeYoutubeDL(yt_dlp.YoutubeDL):
        def process_video_result(self, info_dict, download=True):
            save_format_inventory(state, info_dict)
            if state.raw_audio_inventory and state.raw_audio_inventory.get('eligible'):
                self.format_selector = self.build_format_selector(LEGACY_FORMAT_SELECTOR)
            return super().process_video_result(info_dict, download=download)
        def build_request_director(self, handlers, preferences=None):
            return super().build_request_director([UrllibRH], preferences)
        def urlopen(self, request):
            state.guard(); state.dispatches += 1
            try: response = super().urlopen(request)
            except HTTPError as error:
                response = getattr(error, 'response', None)
                headers = getattr(response, 'headers', {})
                record_python_http_refusal(state, getattr(request, 'url', ''), error.status,
                    final_url=getattr(response, 'url', None), method=getattr(request, 'method', 'GET'),
                    retry_after=headers.get('Retry-After'))
                raise
            state.guard()
            requested=getattr(request,'url','');final=getattr(response,'url',None);status=getattr(response,'status',None)
            if state.phase=='native_transfer' and state.selected_metadata_saved and requested==state.selected_asset_url and final==state.selected_asset_url and endpoint(requested)=='media' and type(status) is int and 200<=status<300:
                state.selected_http_response={'selected_request_equal':True,'final_response_equal':True,'response_status':status,'selection_validated':True}
            return MeteredResponse(response, state)
        def process_info(self, info):
            state.original_track = validate_selection(info, TARGET, settings['expected_duration_seconds'], LIMITS['audio_bytes'],
                native_audio_sink.CODECS, state.raw_audio_inventory)
            state.available_at = info.get('available_at')
            persist_selection(state, info, media_metadata.build_metadata)
            state.selected_asset_url = info.get('url')
            return super().process_info(info)

    result = {'schema_version': 1, 'profile': PROFILE, 'video_id': TARGET, 'status': 'held'}
    try:
        nodriver.start = observed_start
        YoutubeIE._extract_formats_and_subtitles = observed_formats
        plugin_dirs.value = [settings['plugin_directory']]
        plugins.load_all_plugins()
        import yt_dlp_plugins.extractor.getpot_wpc as wpc
        need(Path(wpc.__file__).resolve() == Path(settings['wpc_copy']).resolve() and wpc.__version__ == '1.1.2', 'plugin_scope')
        from yt_dlp.extractor.youtube.pot._registry import _pot_providers
        need(set(_pot_providers.value) == {'WPC'}, 'unexpected_provider')
        http.client.HTTPConnection.putrequest = put_request
        fd_common.sanitize_open = open_file
        options = {'format': 'bestaudio[protocol=https][vcodec=none][language_preference=10][format_id!*=drc][ext=m4a]/bestaudio[protocol=https][vcodec=none][language_preference=10][format_id!*=drc]', 'outtmpl': str(run / 'native-audio.%(ext)s'),
            'quiet': True, 'noprogress': True, 'logger': Quiet(), 'proxy': '', 'noplaylist': True, 'max_downloads': 1,
            'retries': 0, 'fragment_retries': 0, 'extractor_retries': 0, 'file_access_retries': 0,
            'continuedl': False, 'overwrites': False, 'fixup': 'never', 'postprocessors': [], 'updatetime': False,
            'cachedir': False, 'geo_bypass': False, 'socket_timeout': 20, 'buffersize': 65536, 'noresizebuffer': True,
            'ratelimit': LIMITS['rate_bytes_per_second'], 'max_filesize': LIMITS['audio_bytes'], 'js_runtimes': {'deno': {}},
            'extractor_args': {'youtube': {'player_client': ['mweb']}, 'youtubepot-wpc': {'browser_path': [settings['browser_executable']]}},
            'progress_hooks': [lambda value: record_progress(state, value)]}
        with NativeYoutubeDL(options) as ydl:
            download_once(ydl, state, run, 'https://www.youtube.com/watch?v=' + TARGET)
        state.phase = 'local_verification'; state.save(force=True)
        audio = completed_file(state, run)
        proof = inspect_quality(audio, state.selected_summary, settings['ffprobe'], settings['ffmpeg'], state.guard)
        observe_full_native_http_transfer(state,run,proof)
        state.guard()
        metadata = read(run / 'selected-metadata.info.json')
        metadata['native_acquisition_completion'] = {'finished_bytes': state.finished_bytes, 'finished_count': state.finished_count,
            'limit_sentinel_observed': state.limit_sentinel_observed, 'strict_probe_passed': proof['strict_probe_passed']}
        metadata['native_acquisition_quality'] = proof
        write(run / 'metadata.json', metadata)
        result.update(status='local_complete', video_id=TARGET, audio={'filename': audio.name, 'bytes': audio.stat().st_size,
            'sha256': state.audio_sha256.hexdigest(), 'md5': state.audio_md5.hexdigest(),
            'fingerprint': list(storage.fingerprint(audio))}, probe=proof,
            metadata={'filename': 'metadata.json', 'sha256': digest(run / 'metadata.json')},
            original_audio_evidence=state.original_track, drive_uploaded=False)
    except BaseException as error:
        state.error = state.error or (error.code if isinstance(error, (Held, QualityHold)) else state.diagnostic_reason or 'native_downloader_failed')
        if state.error in {'bot_check', 'protection_failure', 'access_challenge'} and state.global_failure_code is None:
            state.global_failure_code = state.error; state.global_failure_at_epoch = time.time()
        result['exception_class'] = type(error).__name__
        try: result['exception_diagnostics'] = safe_exception_chain(error)
        except Exception: result['exception_diagnostics'] = {'schema_version': 1, 'diagnostic_failed': True, 'raw_messages_retained': False}
    finally:
        state.selected_asset_url = None
        fd_common.sanitize_open, http.client.HTTPConnection.putrequest, nodriver.start = original_open, original_put, original_start
        YoutubeIE._extract_formats_and_subtitles = original_formats
        state.phase = 'terminal'; result['diagnostics'] = state.summary()
        write(run / 'result.json', result)
    return 0 if result['status'] == 'local_complete' else 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True); parser.add_argument('--admission', required=True)
    parser.add_argument('--child', action='store_true')
    args = parser.parse_args()
    need(args.child, 'requires_parent_supervisor')
    return child(Path(args.config), Path(args.admission))


if __name__ == '__main__':
    try: exit_code = main()
    except BaseException as error:
        if isinstance(error, SystemExit) and error.code in (None, 0): raise
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location('owned_outer_fatal_diagnostics',Path(__file__).with_name('worker_diagnostics.py'))
            diagnostics = importlib.util.module_from_spec(spec); spec.loader.exec_module(diagnostics)
            diagnostics.report_fatal(error)
        except BaseException:
            try: os.write(2,b'NATIVE_FATAL_V1 {"kind":"native_worker_fatal","exceptions":[{"exception_class":"OtherException"}]}\n')
            except OSError: pass
        print(json.dumps({'status': 'held_before_worker', 'error_class': error.code if isinstance(error, Held) else 'configuration_failed'}))
        sys.exit(3)
    else: sys.exit(exit_code)
