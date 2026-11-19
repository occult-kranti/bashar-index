#!/usr/bin/env python3
"""Export aggregate collection status only; private record content never leaves the root."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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
    from .drive_ingest import (CAPTION_POLICY, HARD_BLOCKS, MAX_LOCAL_BYTES, caption_receipt_complete,
                               caption_track_verified, receipt_complete, terminal_unavailable, tree_bytes)
    from .chromium_capture_service import browser_receipt_complete
    from . import qualified_edition_receipts, qualified_direct_audio_receipts, qualified_batch_status, publisher_caption_batch
else:  # -I deliberately removes the script directory from the default import path.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from drive_ingest import (CAPTION_POLICY, HARD_BLOCKS, MAX_LOCAL_BYTES, caption_receipt_complete,
                              caption_track_verified, receipt_complete, terminal_unavailable, tree_bytes)
    from chromium_capture_service import browser_receipt_complete
    import qualified_edition_receipts, qualified_direct_audio_receipts, qualified_batch_status, publisher_caption_batch

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


def owned_native_batch_command(identity, settings_path, coordinator_path=None, command_mode='direct', grant_path=None):
    """Verify the live Windows command binds this code and exact settings file."""
    if os.name != 'nt' or not owned_process_alive(identity):
        return False
    import ctypes
    from ctypes import wintypes
    class UnicodeString(ctypes.Structure):
        _fields_ = [('length', wintypes.USHORT), ('maximum', wintypes.USHORT), ('buffer', ctypes.c_void_p)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    native = ctypes.WinDLL('ntdll')
    shell = ctypes.WinDLL('shell32')
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    native.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p,
                                                wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]
    native.NtQueryInformationProcess.restype = wintypes.LONG
    shell.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x1000, False, identity['pid'])
    if not handle:
        return False
    try:
        length = wintypes.ULONG()
        native.NtQueryInformationProcess(handle, 60, None, 0, ctypes.byref(length))
        if not 0 < length.value <= 131072:
            return False
        buffer = ctypes.create_string_buffer(length.value)
        if native.NtQueryInformationProcess(handle, 60, buffer, length, ctypes.byref(length)) != 0:
            return False
        value = ctypes.cast(buffer, ctypes.POINTER(UnicodeString)).contents
        command = ctypes.wstring_at(value.buffer, value.length // 2)
        count = ctypes.c_int()
        argv = shell.CommandLineToArgvW(command, ctypes.byref(count))
        if not argv:
            return False
        try:
            args = [argv[i] for i in range(count.value)]
        finally:
            kernel.LocalFree(argv)
        if command_mode == 'qualified_batch':
            return (len(args) == 9 and args[1:3] == ['-I', '-B'] and
                    Path(args[3]).resolve() == Path(coordinator_path).resolve() and
                    args[4:6] == ['--run', '--settings'] and Path(args[6]).resolve() == settings_path.resolve() and
                    args[7] == '--grant' and grant_path is not None and Path(args[8]).resolve() == grant_path.resolve())
        if len(args) == 6 and args[1] in {'-I', '-u'}:
            args.pop(1)
        program = coordinator_path or Path(__file__).with_name('native_batch.py')
        if command_mode == 'bulk':
            return (len(args) == 5 and Path(args[1]).resolve() == Path(program).resolve() and
                    args[2:4] == ['run', '--settings'] and Path(args[4]).resolve() == settings_path.resolve())
        return (len(args) == 5 and Path(args[1]).resolve() == Path(program).resolve() and
                args[2] == '--settings' and Path(args[3]).resolve() == settings_path.resolve() and args[4] == '--execute')
    finally:
        kernel.CloseHandle(handle)


def bound_json(root, pin):
    """Read only a small, pinned JSON proof inside the private root."""
    if not isinstance(pin, dict):
        return {}
    try:
        path = Path(pin.get('path', '')).resolve()
        size = pin.get('bytes')
        if (not path.is_relative_to(root.resolve()) or path.suffix != '.json' or path.is_symlink() or
                type(size) is not int or not 0 < size <= 8_000_000 or path.stat().st_size != size):
            return {}
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != pin.get('sha256'):
            return {}
        value = json.loads(data.decode('utf-8-sig'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def direct_native_batch(root, now):
    """Direct frames have their own proof; they never impersonate a series."""
    try:
        return _direct_native_batch(root, now)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {}


def _direct_native_batch(root, now):
    lease = read_object(root / 'sync/stock_wpc_batch_v4_lease.json')
    expiry = lease.get('expires_at_epoch')
    if not (lease.get('state') in {'active', 'released'} and lease.get('authorized') is True and
            lease.get('source_scope_authorized') is True and lease.get('max_workers') in (1, 2) and
            lease.get('profile') == 'stock_headful_wpc_native_batch_v4' and
            type(expiry) in (int, float)):
        return {}
    if (root / 'sync/STOP_STOCK_WPC_BATCH_V4').exists():
        return {}
    if source_deadline([read_object(root / 'sync/stock_wpc_batch_v4_source_cooldown.json')]) > now:
        return {}
    http = read_object(root / 'sync/stock_wpc_batch_v4_http_state.json').get('state', {})
    if not isinstance(http, dict) or http.get('policy') != 'native-http-refusal-v4' or http.get('circuit_break') is not None:
        return {}
    drive_path = root / 'sync/drive_ingest_cooldown.json'
    if drive_path.exists():
        until = read_object(drive_path).get('until_epoch')
        if type(until) not in (int, float) or not 0 < until <= now:
            return {}
    code = hashlib.sha256(Path(__file__).with_name('native_batch.py').read_bytes()).hexdigest()
    worker = hashlib.sha256(Path(__file__).with_name('native_batch_worker.py').read_bytes()).hexdigest()
    candidates = (root / 'jobs').glob('native-*/runtime-frame*')
    for live in sorted(candidates)[:128]:
        if live.is_symlink() or any((live / name).exists() for name in
                ('local-publication-hold.json', 'drive-hold.json')):
            continue
        invoked = read_object(live / 'invocation.json')
        active = read_object(live / 'activation.json')
        settings, plan, grant = (bound_json(root, active.get(key)) for key in ('settings', 'plan', 'root_grant'))
        if not settings or not plan or not grant:
            continue
        bindings = all(invoked.get(key + '_sha256') == active.get(key, {}).get('sha256') == lease.get(key + '_sha256')
                       for key in ('settings', 'plan', 'root_grant'))
        ids = invoked.get('allowed_video_ids')
        started = invoked.get('started_at_epoch')
        if not (bindings and active.get('status') == 'active' and invoked.get('status') == 'running' and
                invoked.get('lease_id') == active.get('lease_id') == settings.get('lease_id') == lease.get('lease_id') == grant.get('lease_id') and
                grant.get('authorized') is True and grant.get('state') == 'admitted' and
                grant.get('plan_sha256') == lease.get('plan_sha256') and grant.get('settings_sha256') == lease.get('settings_sha256') and
                invoked.get('native_batch_sha256') == lease.get('coordinator_sha256') == grant.get('coordinator_sha256') == code and
                invoked.get('worker_sha256') == lease.get('worker_sha256') == grant.get('worker_sha256') == worker and
                isinstance(ids, list) and ids and all(isinstance(x, str) for x in ids) and len(ids) == len(set(ids)) and
                ids == active.get('allowed_video_ids') == lease.get('allowed_video_ids') == grant.get('allowed_video_ids') and
                invoked.get('source_count') == len(ids) and
                Path(settings.get('private_root', '')).resolve() == root.resolve() and
                Path(settings.get('plan_path', '')).resolve() == Path(active['plan']['path']).resolve() and
                type(started) in (int, float) and started <= now):
            continue
        terminal = read_object(live / 'terminal.json')
        exited = read_object(live / 'source-process-exit.json')
        if terminal or exited:
            if (lease.get('state') == 'released' and terminal.get('status') == 'terminal' and
                    all(terminal.get(key) is True for key in ('parent_process_exited', 'child_audits_complete',
                        'owned_jobs_closed', 'matching_reservation_released', 'matching_lease_released')) and
                    terminal.get('lease_id') == invoked.get('lease_id') and
                    all(terminal.get(key) == invoked.get(key) for key in
                        ('root_grant_sha256', 'plan_sha256', 'settings_sha256')) and
                    all(exited.get(key) == invoked.get(key) for key in ('pid', 'process_creation_filetime')) and
                    exited.get('exit_code') in (0, 3) and not owned_process_alive(invoked)):
                return {'state': 'ready', 'kind': 'native_v4_direct_batch', 'workers': lease['max_workers'],
                        'process_confirmed': False, 'proof': 'released_terminal_direct_frame',
                        'frame_items': len(ids), 'started_at': stamp(started), 'asr_handoff_enabled': False}
            continue
        if not (lease.get('state') == 'active' and now < expiry and
                owned_native_batch_command(invoked, Path(active['settings']['path']))):
            continue
        return {'state': 'running', 'kind': 'native_v4_direct_batch', 'workers': lease['max_workers'],
                'process_confirmed': True, 'proof': 'owned_bound_direct_process',
                'frame_items': len(ids), 'started_at': stamp(started), 'asr_handoff_enabled': False}
    return {}


def private_code_pin(root, pin):
    """Validate a small source-code proof without executing private code."""
    try:
        path = Path(pin['path']).resolve()
        size = pin['bytes']
        return (path.is_relative_to(root.resolve()) and path.suffix == '.py' and
                not path.is_symlink() and type(size) is int and 0 < size <= 131072 and
                path.stat().st_size == size and hashlib.sha256(path.read_bytes()).hexdigest() == pin['sha256'])
    except (OSError, ValueError, TypeError, KeyError):
        return False


def qualified_batch_state(root, now):
    return qualified_batch_status.read(root, now, object_reader=read_object, bound_reader=bound_json,
        code_reader=private_code_pin, alive=owned_process_alive, child_of=owned_process_child_of,
        command=lambda identity, settings, program, grant: owned_native_batch_command(
            identity, settings, program, command_mode='qualified_batch', grant_path=grant))


def rolling_native_state(root, now):
    """Read the currently running native handoff once, ignoring completed workers and stale PID files."""
    pattern = re.compile(r'native_rolling_handoff_([0-9]+)_lease\.json')
    frames = [(int(match[1]), path) for path in (root/'sync').glob('native_rolling_handoff_*_lease.json')
              if (match := pattern.fullmatch(path.name))]
    if not frames:
        return {}
    number, path = max(frames)
    lease = read_object(path)
    ids = lease.get('allowed_video_ids')
    if (lease.get('state') != 'active' or lease.get('profile') != f'native_rolling_handoff_{number}'
            or lease.get('source_authorized') is not True or not isinstance(ids, list) or not ids
            or any(not isinstance(i, str) or not re.fullmatch(r'[\w-]{11}', i, re.ASCII) for i in ids)
            or len(set(ids)) != len(ids) or type(lease.get('expires_at_epoch')) not in (int, float)
            or lease['expires_at_epoch'] <= now):
        return {}
    home = root/'provisioning'/f'native-rolling-handoff-{number}'
    runtime = home/'runtime'
    if (runtime/'owner-terminal.json').exists():
        return {}
    go = read_object(runtime/'GO')
    def pinned(path, digest):
        try:
            return bound_json(root, {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest})
        except OSError:
            return {}
    digest = lease.get('root_grant_sha256')
    grant = pinned(home/'root-grant.ACTIVE.json', digest)
    invocation = pinned(runtime/'invocation.json', go.get('invocation_sha256'))
    identity = invocation.get('identity')
    if (go.get('root_grant_sha256') != digest or invocation.get('root_grant_sha256') != digest
            or grant.get('allowed_video_ids') != ids or grant.get('profile') != lease['profile']
            or grant.get('enabled') is not True or grant.get('source_authorized') is not True
            or not isinstance(identity, dict) or go.get('identity') != identity
            or not all(invocation.get(k) is True for k in ('exact_handle_creation_verified', 'exact_command_verified', 'owned_job_attached'))
            or not owned_process_alive(identity)):
        return {}
    stages = {}
    for video in ids:
        folder = runtime/'observations'/video
        attempt = read_object(folder/'attempt.json')
        if attempt.get('video_id') != video or attempt.get('root_grant_sha256') != digest:
            stages[video] = 'queued'
        elif (folder/'publication-receipt.json').exists():
            stages[video] = 'processing'  # Only the canonical receipt ledger contributes to saved totals.
        elif read_object(folder/'range-transfer.json').get('final_response_equal') is True:
            stages[video] = 'awaiting_upload'
        elif read_object(folder/'range-1.json').get('response_status') in (401, 403, 404, 410, 429):
            stages[video] = 'waiting_for_source'
        else:
            wire = read_object(folder/'wire-1.json')
            stages[video] = ('downloading' if wire.get('method') == 'GET' and
                             pinned(folder/'attempt.json', wire.get('attempt_sha256')) == attempt else 'processing')
    workers = lease.get('source_workers')
    return {'public': {'state': 'running', 'kind': 'rolling_native_handoff', 'source_count': len(ids),
                       'workers': min(workers, len(ids)) if type(workers) is int and workers > 0 else 1,
                       'process_confirmed': True, 'proof': 'owned_live_process'}, 'video_stages': stages}


def native_v5_lane(root, now):
    """A private executor needs its actual grant, pinned files and live command."""
    try:
        return _native_v5_lane(root, now)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {}


def _native_v5_lane(root, now):
    paths = sorted((root / 'sync').glob('stock_wpc_batch_v5*_lease.json'),
                   key=lambda path: read_object(path).get('created_at_epoch', 0), reverse=True)
    for path in paths[:16]:
        result = _native_v5_lease(root, now, read_object(path), path.name[:-len('_lease.json')])
        if result:
            return result
    return {}


def _native_v5_lease(root, now, lease, namespace):
    if not (lease.get('state') in {'active', 'released'} and lease.get('authorized') is True and
            lease.get('source_scope_authorized') is True and isinstance(lease.get('profile'), str) and
            re.fullmatch(r'stock_headful_wpc_native_batch_v5(?:_recovery[0-9]+)?', lease['profile']) and
            re.fullmatch(r'stock_wpc_batch_v5(?:_recovery[0-9]+)?', namespace)):
        return {}
    for live in sorted((root / 'jobs').glob('native-http-v5-*/runtime-*'))[:64]:
        active, invoked = (read_object(live / name) for name in ('activation.json', 'invocation.json'))
        settings, plan, grant = (bound_json(root, active.get(key)) for key in ('settings', 'plan', 'root_grant'))
        ids = invoked.get('allowed_video_ids')
        if not (settings and plan and grant and isinstance(ids, list) and len(ids) == 20 and len(set(ids)) == 20 and
                all(isinstance(ident, str) and re.fullmatch(r'[A-Za-z0-9_-]{11}', ident) for ident in ids) and
                ids == lease.get('allowed_video_ids') == grant.get('allowed_video_ids') and
                {item['video_id'] for item in plan['items']} == set(ids) and
                invoked.get('source_count') == len(ids) and invoked.get('status') == 'running' and
                invoked.get('profile') == settings.get('profile') == grant.get('profile') == lease['profile'] and
                lease.get('max_workers') == settings.get('workers') == grant.get('workers') == 2 and
                invoked.get('lease_id') == active.get('lease_id') == settings.get('lease_id') == lease.get('lease_id') and
                all(invoked.get(key + '_sha256') == active[key]['sha256'] == lease.get(key + '_sha256')
                    for key in ('settings', 'plan')) and
                invoked.get('root_grant_sha256') == active['root_grant']['sha256'] == lease.get('root_admission_sha256') and
                grant.get('settings_sha256') == lease['settings_sha256'] and grant.get('plan_sha256') == lease['plan_sha256'] and
                grant.get('authorized') is True and grant.get('source_scope_authorized') is True and
                grant.get('synthetic_v4_breaker_override_authorized') is True and
                grant.get('asr_handoff') is False and settings.get('asr_handoff') is None and
                invoked.get('asr_handoff_enabled') is False and
                all(private_code_pin(root, active.get(key, {})) for key in ('code', 'worker', 'policy')) and
                invoked.get('native_batch_sha256') == lease.get('coordinator_sha256') == active['code']['sha256'] and
                invoked.get('worker_sha256') == lease.get('worker_sha256') == active['worker']['sha256'] and
                grant.get('http_policy_sha256') == active['policy']['sha256']):
            continue
        base = {'kind': 'native_v5_direct_batch', 'workers': lease.get('max_workers', 2),
                'frame_items': len(ids), 'asr_handoff_enabled': False,
                'started_at': stamp(invoked['started_at_epoch']), 'automatic_resume': False}
        prior = native_source_hold(root, now).get('completed_decisions')
        if type(prior) is int and prior >= 0:
            base['prior_completed_decisions'] = prior
        envelope = read_object(root / ('sync/' + namespace + '_http_state.json'))
        state = envelope.get('state', {})
        if not (envelope.get('schema_version') == 5 and isinstance(state, dict) and
                envelope.get('seed_sha256') == grant.get('http_policy_seed_sha256') == lease.get('http_policy_seed_sha256') and
                state.get('policy') == 'native-http-consecutive-transfer-v5' and
                state.get('root_review_sha256') == grant.get('root_policy_review_sha256')):
            continue
        cooldown = read_object(root / ('sync/' + namespace + '_source_cooldown.json'))
        until = cooldown.get('retry_not_before_epoch', 0)
        if type(until) not in (int, float) or not 0 <= until < 253402300799:
            return {}
        if (root / ('sync/STOP_' + namespace.upper())).exists() or state.get('circuit_break') or until > now:
            actual_refusal = bool(state.get('circuit_break') or until > now)
            return dict(base, state='paused', kind='native_v5_source_hold', process_confirmed=False,
                        proof='current_native_stop_or_refusal' if actual_refusal else 'owner_pause',
                        reason='source_control_hold' if actual_refusal else 'worker_startup',
                        retry_after=stamp(until) if until > now else None)
        terminal = read_object(live / 'terminal.json')
        summary = terminal.get('summary', {})
        if (lease['state'] == 'released' and terminal.get('status') == 'terminal' and
                all(terminal.get(key) is True for key in ('parent_process_exited', 'owned_jobs_closed',
                    'child_audits_complete', 'matching_lease_released', 'matching_reservation_released')) and
                terminal.get('lease_id') == lease['lease_id'] and
                all(terminal.get(key + '_sha256') == invoked.get(key + '_sha256')
                    for key in ('plan', 'settings', 'root_grant')) and
                all(type(summary.get(key)) is int and summary[key] >= 0
                    for key in ('verified', 'held', 'pending', 'skipped')) and
                sum(summary[key] for key in ('verified', 'held', 'pending', 'skipped')) == len(ids) and summary['pending'] == 0 and
                not owned_process_alive(invoked)):
            return dict(base, state='ready', process_confirmed=False, proof='released_terminal_direct_frame',
                        completed_frame_decisions=len(ids), verified_in_frame=summary['verified'],
                        held_in_frame=summary['held'], prior_completed_decisions=(prior or 0) + len(ids))
        expiry = min(lease.get('expires_at_epoch', 0), grant.get('expires_at_epoch', 0))
        if (lease['state'] == 'active' and now < expiry and
                owned_native_batch_command(invoked, Path(active['settings']['path']), Path(active['code']['path']))):
            return dict(base, state='running', process_confirmed=True, proof='owned_bound_direct_process')
    return {}


def native_bulk_lane(root, now):
    """Read a finite cohort's pinned scope and actual owned controller command."""
    try:
        return _native_bulk_lane(root, now)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, StopIteration):
        return {}


def _native_bulk_lane(root, now):
    paths = sorted((root / 'sync').glob('stock_wpc_batch_v5_bulk*_lease.json'),
                   key=lambda path: read_object(path).get('created_at_epoch', 0), reverse=True)
    for path in paths[:16]:
        result = _native_bulk_lease(root, now, read_object(path), path.name[:-len('_lease.json')])
        if result:
            return result
    return {}


def _status_identity(value):
    if not isinstance(value, dict) or type(value.get('pid')) is not int or value['pid'] <= 0:
        return None
    creation = value.get('process_creation_filetime')
    if type(creation) not in (int, str) or not str(creation).isascii() or not str(creation).isdigit() or int(creation) <= 0:
        return None
    return value['pid'], str(creation)


def completed_bulk_lane(root, home, lease, state, result):
    """Show an actually closed latest cohort without probing historical PIDs."""
    if not (lease.get('state') == 'released' and lease.get('owned_native_processes_gone') is True and
            state.get('status') == 'complete' and state.get('current_frame') is None and
            result['completed_frames'] == result['planned_frames'] and
            result['completed_decisions'] == result['source_count']):
        return {}
    owner = home / 'owner-runtime-v1'
    terminal = read_object(owner / 'terminal.json')
    reviewed = read_object(owner / 'terminal-review.json')
    invoked = read_object(owner / 'invocation.json')
    exited = read_object(owner / 'source-process-exit.json')
    closed = read_object(owner / 'owned-controller-closure.json')
    grant = lease.get('root_admission_sha256')
    controller, launcher = _status_identity(state.get('controller_identity')), _status_identity(closed.get('identity'))
    bases, reviewed_bases = invoked.get('base_controller_identities'), reviewed.get('base_controller_identities')
    parent = invoked.get('parent_proof', {})
    rows = read_object(root / 'sync/analysis_resource_plan.json').get('reservations', [])
    own_rows = [row for row in rows if row.get('lease_id') == lease.get('lease_id')]
    if not (all(doc.get('root_grant_sha256') == grant for doc in (terminal, reviewed, invoked, exited)) and
            terminal.get('status') == 'terminal' and terminal.get('cohort_status') == 'complete' and
            terminal.get('source_count') == terminal.get('attempted_items') == result['source_count'] and
            terminal.get('closed_frames') == result['planned_frames'] and terminal.get('exit_code') == 0 and
            all(terminal.get(key) is True for key in ('owned_jobs_closed', 'child_audits_complete',
                'matching_lease_released', 'matching_reservation_released')) and
            reviewed.get('controller_state') == state and reviewed.get('owned_job_closed') is True and
            reviewed.get('child_audits_complete') is True and
            exited.get('derived_from_supervisor_actual_exit') is True and exited.get('exit_code') == 0 and
            terminal.get('at') == reviewed.get('at') == exited.get('at') and terminal.get('at') and
            all(closed.get(key) is True for key in ('attached', 'closed', 'owned_job_empty',
                'owned_process_closed', 'process_returned', 'job_returned')) and closed.get('exit_code') == 0 and
            launcher is not None and launcher == _status_identity(invoked.get('launcher_identity')) ==
                _status_identity(reviewed.get('launcher_identity')) == _status_identity(exited) and controller is not None and
            isinstance(bases, list) and len(bases) == 1 and isinstance(reviewed_bases, list) and len(reviewed_bases) == 1 and
            controller == _status_identity(bases[0]) == _status_identity(reviewed_bases[0]) and
            parent.get('parent_verified') is True and parent.get('same_owned_Windows_job') is True and
            _status_identity(parent.get('launcher_identity')) == launcher and
            _status_identity(parent.get('base_controller_identity')) == controller and
            ('parent_pid' not in bases[0] or bases[0]['parent_pid'] == launcher[0]) and
            len(own_rows) == 1 and own_rows[0].get('state') == 'released' and
            own_rows[0].get('root_grant_sha256') == grant and
            type(lease.get('spool_cap_bytes')) is int and
            own_rows[0].get('max_bytes') == lease['spool_cap_bytes'] and
            type(state.get('finished_at_epoch')) in (int, float) and
            state['finished_at_epoch'] >= state.get('started_at_epoch', 0)):
        return {}
    return dict(result, state='ready', process_confirmed=False, proof='released_completed_bulk_cohort',
                finished_at=stamp(state['finished_at_epoch']))


def _native_bulk_lease(root, now, lease, namespace):
    if not (lease.get('state') in {'active', 'released'} and isinstance(lease.get('profile'), str) and
            re.fullmatch(r'stock_headful_wpc_native_batch_v5_bulk(?:_recovery[0-9]+|_recovery6_prototype)?', lease['profile']) and
            namespace == lease['profile'].replace('stock_headful_wpc_native_batch_', 'stock_wpc_batch_', 1) and
            all(lease.get(key) is True for key in ('authorized', 'source_scope_authorized', 'finite_cohort_scope_authorized'))):
        return {}
    for home in sorted((root / 'jobs').glob('native-http-v5-bulk-*'))[:16]:
        packet = read_object(home / 'root-review-packet.json')
        settings_pin = packet.get('controller_settings', {})
        settings = bound_json(root, settings_pin)
        if not settings:
            continue
        grant_path = Path(settings['root_admission_path'])
        grant = bound_json(root, {'path': str(grant_path), 'bytes': grant_path.stat().st_size,
                                  'sha256': lease.get('root_admission_sha256')})
        manifest = bound_json(root, settings.get('cohort_manifest'))
        mapping = bound_json(root, settings.get('frame_map'))
        ids, frames = manifest.get('allowed_video_ids'), mapping.get('frames')
        if not (grant and isinstance(ids, list) and 0 < len(ids) <= 1280 and len(set(ids)) == len(ids) and
                all(isinstance(ident, str) and re.fullmatch(r'[A-Za-z0-9_-]{11}', ident) for ident in ids) and
                ids == lease.get('allowed_video_ids') == grant.get('allowed_video_ids') and isinstance(frames, list) and
                [ident for frame in frames for ident in frame['video_ids']] == ids and
                grant.get('authorized') is True and grant.get('finite_cohort_scope_authorized') is True and
                grant.get('source_scope_authorized') is True and grant.get('ASR') is False and grant.get('GPU') is False and
                grant.get('profile') == lease['profile'] and grant.get('owner') == settings.get('owner') == lease.get('owner') == 'root' and
                settings.get('lease_id') == lease.get('lease_id') and
                settings_pin.get('sha256') == grant.get('controller_settings_sha256') == lease.get('controller_settings_sha256') and
                all(settings[key]['sha256'] == grant.get(key + '_sha256') == lease.get(key + '_sha256')
                    for key in ('cohort_manifest', 'frame_map'))):
            continue
        codes = {Path(pin['path']).name: pin for pin in packet.get('private_code', [])}
        fields = {'controller': 'native_bulk_controller.py', 'coordinator': 'native_batch.py',
                  'worker': 'native_batch_worker.py', 'http_policy': 'native_http_policy.py', 'contract': 'bulk_contract.py'}
        if not all(private_code_pin(root, codes.get(filename, {})) and
                   codes[filename]['sha256'] == grant.get(key + '_sha256') for key, filename in fields.items()):
            continue
        live = home / 'runtime'
        invoked = read_object(live / 'source-invocation.json')
        state = read_object(live / 'cohort-state.json')
        if not (invoked and state and invoked.get('controller_identity') == state.get('controller_identity') and
                invoked.get('root_grant_sha256') == state.get('root_grant_sha256') == lease.get('root_admission_sha256') and
                all(invoked.get(key + '_sha256') == state.get(key + '_sha256') == lease.get(key + '_sha256')
                    for key in ('controller_settings', 'cohort_manifest', 'frame_map'))):
            continue
        completed = state.get('frames')
        if not isinstance(completed, list) or len(completed) > len(frames):
            continue
        decisions = 0
        for index, row in enumerate(completed):
            summary = row.get('summary', {})
            if not (row.get('frame_index') == index and row.get('plan_sha256') == frames[index]['plan_sha256'] and
                    row.get('status') == 'terminal_closed' and
                    all(type(summary.get(key)) is int and summary[key] >= 0 for key in ('verified', 'held', 'pending', 'skipped')) and
                    summary['pending'] == 0 and sum(summary[key] for key in ('verified', 'held', 'pending', 'skipped')) == len(frames[index]['video_ids'])):
                return {}
            decisions += len(frames[index]['video_ids'])
        result = {'kind': 'native_v5_bulk', 'namespace': namespace, 'workers': 2, 'source_count': len(ids), 'planned_frames': len(frames),
                  'completed_frames': len(completed), 'completed_decisions': decisions,
                  'started_at': stamp(invoked['started_at_epoch']), 'asr_handoff_enabled': False,
                  'automatic_resume': False}
        ledger = read_object(root / ('sync/' + namespace + '_http_state.json'))
        if (ledger.get('schema_version') != 5 or ledger.get('seed_sha256') != grant.get('http_policy_seed_sha256')):
            continue
        held = ((root / ('sync/STOP_' + namespace.upper())).exists() or
                ledger.get('state', {}).get('circuit_break') or state.get('status') == 'held_reconciliation_required')
        if not held:
            completed_lane = completed_bulk_lane(root, home, lease, state, result)
            if completed_lane:
                return completed_lane
        expiry = min(lease.get('expires_at_epoch', 0), grant.get('expires_at_epoch', 0))
        if held or now >= expiry:
            reason = 'source_or_owner_hold'
            if ledger.get('state', {}).get('circuit_break'):
                reason = 'source_control_hold'
            elif state.get('failed_frame', {}).get('error_class') == 'bulk_child_diagnostics_missing':
                reason = 'worker_diagnostics_missing'
            return dict(result, state='paused', process_confirmed=False, proof='finite_cohort_hold',
                        reason=reason)
        if (lease['state'] == 'active' and state.get('status') == 'active' and
                owned_native_batch_command(invoked['controller_identity'], Path(settings_pin['path']),
                                           Path(codes['native_bulk_controller.py']['path']), command_mode='bulk')):
            current = state.get('current_frame') or {}
            return dict(result, state='running', process_confirmed=True, proof='owned_bound_bulk_process',
                        current_frame_index=current.get('frame_index'))
    return {}


def native_source_hold(root, now):
    """Report the actual native hold separately from parked legacy controls."""
    stop = root / 'sync/STOP_STOCK_WPC_BATCH_V4'
    cooldown = read_object(root / 'sync/stock_wpc_batch_v4_source_cooldown.json')
    until = source_deadline([cooldown])
    native_until = cooldown.get('retry_not_before_epoch')
    if (cooldown.get('error_class') in {'source_403', 'source_429', 'bot_check', 'protection_failure', 'access_challenge'} and
            type(native_until) in (int, float) and 0 < native_until < 253402300799):
        until = max(until, native_until)
    http = read_object(root / 'sync/stock_wpc_batch_v4_http_state.json').get('state', {})
    circuit = http.get('circuit_break') if isinstance(http, dict) else None
    if not stop.exists() and until <= now and not circuit:
        return {}
    lease = read_object(root / 'sync/stock_wpc_batch_v4_lease.json')
    result = {'state': 'paused', 'kind': 'native_v4_source_hold', 'workers': 2,
              'process_confirmed': False, 'proof': 'current_native_stop_or_refusal',
              'reason': 'repeated_bound_403' if isinstance(circuit, dict) and
                  circuit.get('reason') == 'three_distinct_403_in_600s' else 'source_control_hold',
              'retry_after': stamp(until) if until > now else None,
              'automatic_resume': False}
    candidates = [*(root / 'jobs').glob('native-campaign*/cohort*/live'),
                  *(root / 'jobs').glob('native-campaign*/live')]
    for live in sorted(candidates)[:64]:
        state = read_object(live / 'series-state.json')
        invoked = read_object(live / 'source-invocation.json')
        count, frames = invoked.get('source_count'), state.get('frames')
        if not (state.get('proposal_sha256') == invoked.get('series_proposal_sha256') == lease.get('series_proposal_sha256') and
                state.get('authorization_sha256') == invoked.get('root_authorization_sha256') == lease.get('root_authorization_sha256') and
                isinstance(state.get('proposal_sha256'), str) and re.fullmatch(r'[a-f0-9]{64}', state['proposal_sha256']) and
                type(count) is int and 0 < count <= 1280 and isinstance(frames, dict)):
            continue
        done = [frame for frame in frames.values() if isinstance(frame, dict) and frame.get('phase') == 'drained']
        if any(not isinstance(frame.get('outcomes'), dict) for frame in done):
            continue
        identities = [key for frame in done for key in frame.get('outcomes', {})]
        if len(identities) != len(set(identities)) or len(identities) > count:
            continue
        result.update(source_count=count, completed_decisions=len(identities), completed_frames=len(done))
        for key in ('cohort_index', 'planned_frames'):
            if type(invoked.get(key)) is int and 0 < invoked[key] <= 64:
                result[key] = invoked[key]
        break
    return result


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
                  *(root / 'jobs').glob('native-campaign*/live'),
                  *(root / 'jobs').glob('native-campaign*/cohort*/live')]
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
        result = {'workers': lease['max_workers'], 'asr_running': asr_running,
                  'asr_reported_at': stamp(heartbeat) if asr_running else None}
        if state.get('profile') == 'native-campaign-download-only-v1':
            frames = state.get('frames', {})
            result.update(kind='native_v4_campaign', asr_handoff_enabled=False,
                completed_decisions=sum(len(frame.get('outcomes', {})) for frame in frames.values()
                                        if isinstance(frame, dict) and frame.get('phase') == 'drained'),
                completed_frames=sum(isinstance(frame, dict) and frame.get('phase') == 'drained' for frame in frames.values()))
            for key in ('source_count', 'cohort_index', 'planned_frames'):
                if type(invoked.get(key)) is int and 0 < invoked[key] <= 2000:
                    result[key] = invoked[key]
        return result
    return {}


def completed_native_lane(root, now):
    """A released, bound terminal run proves readiness, never a running worker.

    Legacy SABR receipts and STOP_DRIVE_INGEST belong to the parked collector.
    Current v4 source/Drive holds still apply to this independently owned lane.
    """
    lease = read_object(root / 'sync/stock_wpc_batch_v4_lease.json')
    if not (lease.get('state') == 'released' and lease.get('owned_native_processes_gone') is True and
            lease.get('authorized') is True and lease.get('source_scope_authorized') is True and
            lease.get('profile') == 'stock_headful_wpc_native_batch_v4' and
            lease.get('max_workers') in (1, 2)):
        return {}
    if (root / 'sync/STOP_STOCK_WPC_BATCH_V4').exists():
        return {}
    if source_deadline([read_object(root / 'sync/stock_wpc_batch_v4_source_cooldown.json')]) > now:
        return {}
    http = read_object(root / 'sync/stock_wpc_batch_v4_http_state.json')
    if not (http.get('schema_version') == 1 and isinstance(http.get('state'), dict) and
            http['state'].get('policy') == 'native-http-refusal-v4' and
            http['state'].get('circuit_break') is None):
        return {}
    drive_path = root / 'sync/drive_ingest_cooldown.json'
    if drive_path.exists():
        until = read_object(drive_path).get('until_epoch')
        if type(until) not in (int, float) or not 0 < until <= now:
            return {}
    series, authorization = lease.get('series_proposal_sha256'), lease.get('root_authorization_sha256')
    if not all(isinstance(x, str) and re.fullmatch(r'[a-f0-9]{64}', x) for x in (series, authorization)):
        return {}
    for live in sorted((root / 'jobs').glob('native-series*/live'))[:64]:
        if live.is_symlink() or any((live / name).exists() for name in
                                   ('local-publication-hold.json', 'drive-hold.json', 'STOP_SERIES')):
            continue
        state = read_object(live / 'series-state.json')
        invoked = read_object(live / 'source-invocation.json')
        exited = read_object(live / 'source-process-exit.json')
        released = read_object(live / 'native-allocation-released.json')
        if (state.get('status') in {'complete', 'finished_with_holds'} and
                state.get('proposal_sha256') == invoked.get('series_proposal_sha256') == series and
                state.get('authorization_sha256') == invoked.get('root_authorization_sha256') == authorization and
                exited.get('exit_code') == 0 and released.get('lease_id') == lease.get('lease_id') and
                type(invoked.get('pid')) is int and str(invoked.get('process_creation_filetime', '')).isdigit() and
                not owned_process_alive(invoked)):
            return {'state': 'ready', 'workers': lease['max_workers'], 'kind': 'native_v4',
                    'process_confirmed': False, 'proof': 'released_terminal_run'}
    return {}


def queue_ids(root, names):
    for name in names:
        path = root / "jobs" / name
        if path.is_file():
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            return {r["video_id"] for r in rows if r.get("video_id")}, len({r.get("channel_dir") for r in rows})
    return set(), 0


def selection_rows(path, *, content=None):
    """One pinned canonical mixed snapshot, with strict owner/position joins."""
    raw = Path(path).read_bytes() if content is None else content
    value = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(value, dict) or value.get('schema_version', 1) != 1:
        raise ValueError('Unsupported mixed selection schema')
    scopes = {'all_requested_positions_observed', 'short_complete_displayed_list',
              'incomplete_visible_positions', 'unobserved'}
    groups, owners, seen, rows, positions = {}, {}, set(), [], defaultdict(set)
    def creator(name, channel, scope=None):
        if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', name)
                or not isinstance(channel, str) or not re.fullmatch(r'UC[A-Za-z0-9_-]{22}', channel)
                or scope is not None and scope not in scopes
                or name in groups and groups[name]['channel_id'] != channel
                or channel in owners and owners[channel] != name):
            raise ValueError('Mixed selection creator identity mismatch')
        owners[channel] = name
        group = groups.setdefault(name, {'channel_id': channel, 'scope': None})
        if scope is not None:
            if group['scope'] not in (None, scope):
                raise ValueError('Conflicting mixed selection availability')
            group['scope'] = scope
    def add(item, name, channel, rank):
        video, tab = item.get('video_id'), item.get('tab')
        if (not isinstance(video, str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}', video) or video in seen
                or type(rank) is not int or not 0 <= rank < 20 or rank in positions[name]
                or tab not in {'videos', 'shorts', 'streams', 'unknown'}):
            raise ValueError('Invalid mixed selection row, rank or format')
        creator(name, channel)
        seen.add(video); positions[name].add(rank)
        rows.append({'video_id': video, 'channel_dir': name, 'expected_channel_id': channel,
                     'listing_rank': rank, 'tab': tab, 'title': item.get('title', ''),
                     'source_channel_name': item.get('source_channel_name') or item.get('channel_name') or name,
                     'upload_date_approx': item.get('upload_date_approx'),
                     'selected_publication_date': item.get('publication_date'),
                     'selected_date_quality': item.get('date_quality', 'unknown'),
                     'selected_date_basis': item.get('publication_date_basis'),
                     'selected_date_source_sha256': item.get('exact_date_evidence_sha256')})
    basis, archive = 'canonical_mixed_latest20', {}
    if value.get('selection_kind') == 'additive_latest20plus_videos_v1':
        selected_rows, channel_list = value.get('rows'), value.get('channels')
        if (value.get('latest_regular_per_creator') != 20 or not isinstance(selected_rows, list)
                or not isinstance(channel_list, list) or value.get('row_count') != len(selected_rows)):
            raise ValueError('Invalid Latest 20+ selection counts')
        declared = {}
        for group in channel_list:
            name, channel, count = group['channel_dir'], group['channel_id'], group['public_regular_count']
            if name in declared or type(count) is not int or not 0 <= count <= 20:
                raise ValueError('Invalid public regular creator count')
            complete = group.get('public_listing_complete') is True
            scope = ('all_requested_positions_observed' if count == 20 else 'short_complete_displayed_list'
                     if complete else 'incomplete_visible_positions' if count else 'unobserved')
            creator(name, channel, scope)
            declared[name] = count
        membership_keys = set()
        for item in selected_rows:
            name, video = item['channel_dir'], item['video_id']
            if name not in declared or (name, video) in membership_keys:
                raise ValueError('Duplicate recording or unknown creator in the archive union')
            membership_keys.add((name, video))
            if item.get('fresh_public_regular') is not True:
                continue
            members = [m for m in item['memberships'] if m.get('kind') == 'fresh_public_regular']
            channel = groups[name]['channel_id']
            if (len(members) != 1 or item.get('public_media_dispatch_excluded') is not False or
                members[0].get('access_status') != 'public_listing' or members[0].get('tab') != 'videos' or
                members[0].get('expected_channel_id') != channel or item.get('current_primary_channel_id') != channel):
                raise ValueError('Public regular membership lacks its creator, format or access evidence')
            member = members[0]
            selected_item = {**item, 'tab': 'videos', 'title': member.get('title') or item.get('title', ''),
                             'publication_date': member.get('publication_date'), 'date_quality': member.get('date_quality', 'unknown')}
            reference = item.get('publication_date_evidence') or {}
            if item.get('publication_date_quality') in ('instant', 'date'):
                digest = reference.get('public_watch_sha256') or (reference.get('overlay') or {}).get('sha256')
                date = item.get('publication_date')
                try:
                    day = dt.date.fromisoformat(date).isoformat() if isinstance(date, str) else None
                except ValueError:
                    day = None
                bound = (reference.get('row_channel_dir'), reference.get('row_video_id')) == (name, video)
                if day and bound and isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest):
                    selected_item.update(publication_date=day, date_quality='exact', exact_date_evidence_sha256=digest)
            add(selected_item, name, channel, member.get('listing_rank'))
        if any(len(positions[name]) != count for name, count in declared.items()):
            raise ValueError('Public regular membership differs from its creator totals')
        shape, basis = value['selection_kind'], 'latest20plus_public_regular'
        archive = {'label': 'Latest 20+ videos', 'total': len(membership_keys),
                   'literal_latest20': sum(x.get('fresh_regular') is True for x in selected_rows),
                   'literal_members_only': sum(x.get('fresh_regular') is True and x.get('public_media_dispatch_excluded') is True for x in selected_rows),
                   'formats': dict(Counter(x['tab'] for x in selected_rows))}
    elif value.get('per_channel') == 20 and isinstance(value.get('channels'), list):
        for group in value['channels']:
            if not isinstance(group, dict):
                raise ValueError('Invalid mixed selection creator')
            name, channel, items = group.get('channel_dir'), group.get('channel_id'), group.get('items')
            if (name in groups or group.get('scope') not in scopes or not isinstance(items, list)
                    or type(group.get('selected')) is not int or group['selected'] != len(items)):
                raise ValueError('Invalid mixed selection creator count')
            creator(name, channel, group.get('scope'))
            previous = -1
            for rank, item in enumerate(items):
                position = item.get('source_position')
                if (item.get('channel_dir') != name or item.get('channel_id') != channel
                        or type(item.get('slot')) is not int or item.get('slot') != rank + 1
                        or type(position) is not int or position <= previous):
                    raise ValueError('Mixed selection row belongs to another creator/position')
                previous = position
                add(item, name, channel, rank)
        shape = 'recording_selection_channels_v1'
    elif value.get('target_limit') == 20 and isinstance(value.get('rows'), list):
        if (value.get('schema_version') != 1 or type(value.get('row_count')) is not int
                or value.get('row_count') != len(value['rows'])):
            raise ValueError('Mixed roster row count mismatch')
        for item in value.get('observations', []):
            creator(item.get('channel_dir'), item.get('expected_channel_id'))
        for item in value['rows']:
            add(item, item.get('channel_dir'), item.get('expected_channel_id'), item.get('selected_position_after_visible_exclusions'))
        for item in value.get('creator_coverage', []):
            name, scope = item.get('creator'), item.get('scope')
            if name not in groups or scope not in scopes:
                raise ValueError('Mixed roster creator coverage mismatch')
            creator(name, groups[name]['channel_id'], scope)
        shape = 'completed_recording_roster_v1'
    else:
        raise ValueError('Expected canonical mixed latest20 selection JSON')
    for name, group in groups.items():
        count = len(positions[name])
        if positions[name] != set(range(count)):
            raise ValueError('Mixed selection ranks must be consecutive chosen positions')
        scope = group['scope'] or ('all_requested_positions_observed' if count == 20 else 'incomplete_visible_positions')
        if (count > 20 or scope == 'all_requested_positions_observed' and count != 20
                or scope == 'unobserved' and count):
            raise ValueError('Mixed selection availability/count conflict')
        group.update(scope=scope, target=count, shortfall_to_20=20-count)
    result = {'rows': rows, 'creators': groups, 'sha256': hashlib.sha256(raw).hexdigest(),
              'shape': shape, 'basis': basis, 'format_counts': dict(Counter(row['tab'] for row in rows))}
    if archive:
        priority = sorted((r['channel_dir'], r['expected_channel_id'], r['listing_rank'], r['video_id']) for r in rows)
        result.update(archive=archive, priority_scope_sha256=hashlib.sha256(json.dumps(priority, separators=(',', ':')).encode()).hexdigest())
    return result


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


def selected_recording_owners(root, target_rows=None):
    """Return a channel and source tab per video, rejecting conflicting selections."""
    if target_rows is None:
        for name in ('queue_newest20_enriched.csv', 'queue_newest20.csv'):
            path = root / 'jobs' / name
            if path.is_file():
                with path.open(encoding='utf-8-sig', newline='') as handle:
                    target_rows = list(csv.DictReader(handle))
                break
    owners = {}
    for row in target_rows or ():
        ident = row.get('video_id')
        owner = (row.get('channel_dir'), row.get('tab'))
        owners[ident] = owner if ident not in owners or owners[ident] == owner else None
    return owners


def qualified_edition_coverage(root, targets, remote, target_rows=None):
    """Count paired qualified audio without granting native or text coverage."""
    root = Path(root)
    owners = selected_recording_owners(root, target_rows)
    path = root / 'sync/progressive_audio_extracts_manifest.jsonl'
    accepted = set()
    if not path.is_file() or path.stat().st_size > 64_000_000:
        return accepted
    with path.open(encoding='utf-8-sig') as handle:
        while line := handle.readline(2_000_001):
            if len(line) > 2_000_000:
                return set()  # incomplete inventory must never inflate counts
            try:
                record = json.loads(line)
                reader = (qualified_direct_audio_receipts if isinstance(record, dict) and
                          record.get('source_format_id') == '140' else qualified_edition_receipts)
                edition = reader.validate(record, remote_base=remote)
            except (qualified_edition_receipts.ReceiptHold, TypeError, ValueError, KeyError, OverflowError):
                continue
            if edition.video_id in targets and owners.get(edition.video_id) == (edition.channel_dir, record['tab']):
                accepted.add(edition.video_id)
    return accepted


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


def publisher_coverage(root, targets, remote, target_rows=None):
    """Supplementary publisher editions never establish native/ASR completion."""
    owners = selected_recording_owners(root, target_rows) if target_rows is not None else None
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
        if owners is not None and (not owners.get(row['video_id']) or owners[row['video_id']][0] != row['channel_dir']):
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


def publisher_timed_text_coverage(root, targets, remote, target_rows=None):
    """Count independently archived publisher text without inventing audio binding."""
    found = set()
    owners = selected_recording_owners(root, target_rows)
    path = root / 'sync/publisher_caption_manifest.jsonl'
    for line in path.read_text(encoding='utf-8-sig').splitlines() if path.is_file() else []:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        if record.get('artifact_kind') == 'publisher_edition_caption_batch':
            found.update(publisher_caption_batch.verified_videos(record, targets, remote, owners))
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


def publisher_object_proof(value):
    return (isinstance(value, dict) and type(value.get('bytes')) is int and value['bytes'] > 0 and
            isinstance(value.get('drive_id'), str) and bool(value['drive_id']) and
            all(isinstance(value.get(key), str) and re.fullmatch(pattern, value[key])
                for key, pattern in (('sha256', '[0-9a-f]{64}'), ('md5', '[0-9a-f]{32}'))))


def companion_writings(root, targets, remote, target_rows=None):
    """Publisher-written messages and session text can accompany only part of a video."""
    path = root / 'sync/publisher_companion_manifest.jsonl'
    owners = selected_recording_owners(root, target_rows)
    messages, sessions = set(), set()
    if not path.exists():
        return messages, sessions
    with path.open(encoding='utf-8-sig') as stream:
        for line in stream:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            video, kind, bundle = rec.get('video_id'), rec.get('artifact_kind'), rec.get('bundle')
            if not isinstance(video, str) or video not in targets or not owners.get(video) or not publisher_object_proof(bundle):
                continue
            creator, tab = owners[video]
            folder = {'videos':'Videos', 'shorts':'Shorts', 'streams':'Streams'}.get(tab)
            if (not folder or rec.get('schema_version') != 1 or rec.get('status') != 'verified' or creator != rec.get('channel_dir')
                    or rec.get('language') != 'en' or any(rec.get(k) is not False for k in
                        ('timed', 'youtube_caption', 'changes_full_asr_count', 'changes_selected_audio_count', 'changes_native_audio_count'))):
                continue
            parent = f"{remote}/{creator}/{folder}/{video}/PublisherText/{bundle['sha256']}/"
            if (kind == 'exact_linked_publisher_written_message' and rec.get('full_video_text_verified') is False
                    and type(rec.get('word_count')) is int and rec['word_count'] > 0
                    and bundle.get('remote') == parent + 'published-message.en.zip'):
                messages.add(video)
            if (kind == 'publisher_session_transcript' and rec.get('full_video_speech_alignment_verified') is False
                    and type(rec.get('session_number')) is int and rec['session_number'] > 0
                    and rec.get('association_method') in {'publisher_embedded_exact_youtube_id', 'qualified_same_publisher_exact_title_date_and_named_source'}
                    and re.fullmatch('[0-9a-f]{64}', str(rec.get('source_pdf_sha256', '')))
                    and bundle.get('remote') == parent + 'publisher-session.en.zip'):
                sessions.add(video)
    return messages, sessions


def publisher_episode_page_reference(record):
    """Reviewed official paired-player evidence, distinct from an RSS YouTube link."""
    binding = record.get('publisher_episode_binding')
    if not isinstance(binding, dict):
        return False
    video = record.get('associated_youtube_id')
    episode = binding.get('episode_number')
    uuid = binding.get('art19_episode_uuid')
    if (record.get('kind') != 'publisher_episode_page_exact_youtube_id' or
            record.get('association_method') != 'publisher_episode_page_exact_youtube_id' or
            record.get('exact_youtube_crossreference') is not True or
            record.get('recording_equivalence_verified') is not False or
            record.get('provider') != 'ART19' or record.get('channel_dir') != 'julie-ryan' or
            binding.get('publisher_channel_id') != 'UCMYtR_CBJeC6MKbzuQ2dd6A' or
            type(episode) is not int or episode <= 0 or
            not isinstance(uuid, str) or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', uuid) or
            not re.fullmatch('[0-9a-f]{64}', str(binding.get('reviewed_pair_sha256', '')))):
        return False
    try:
        enclosure = urlsplit(binding.get('rss_enclosure_url', ''))
        return (binding.get('episode_page_url') == f'https://askjulieryan.com/podcast/{episode}/' and
                binding.get('youtube_player_url') == 'https://www.youtube.com/embed/' + video and
                record.get('original_youtube_link') == 'https://www.youtube.com/watch?v=' + video and
                binding.get('art19_player_url') ==
                    f'https://art19.com/shows/97147093-d307-4e02-8559-09ab2b7767ce/episodes/{uuid}/embed' and
                binding.get('rss_feed_url') == 'https://rss.art19.com/ask-julie-ryan' and
                enclosure.scheme == 'https' and enclosure.netloc == 'rss.art19.com' and
                enclosure.path == f'/episodes/{uuid}.mp3' and not enclosure.fragment and
                isinstance(binding.get('rss_guid'), str) and bool(binding['rss_guid']))
    except (ValueError, TypeError):
        return False


def publisher_episode_transcript_reference(record, parent):
    """Bind an untimed document and its English text to the same official episode."""
    evidence = record.get('publisher_transcript_provenance')
    document = record.get('publisher_transcript_document')
    transcript = record.get('publisher_transcript')
    if not isinstance(evidence, dict) or not publisher_object_proof(document):
        return False
    binding = record['publisher_episode_binding']
    try:
        source = urlsplit(evidence.get('source_url', ''))
        return (evidence.get('episode_page_url') == binding['episode_page_url'] and
                evidence.get('art19_episode_uuid') == binding['art19_episode_uuid'] and
                evidence.get('associated_youtube_id') == record['associated_youtube_id'] and
                evidence.get('declared_label') == 'Episode Transcript' and
                evidence.get('language_verification') == 'english_document_lexical_check' and
                evidence.get('source_document_sha256') == document['sha256'] and
                source.scheme == 'https' and source.netloc == 'askjulieryan.com' and
                source.path.startswith('/wp-content/uploads/') and source.path.endswith('.docx') and
                not source.query and not source.fragment and
                document.get('remote') == parent + '/publisher-transcript.source.docx' and
                len({document['drive_id'], transcript['drive_id'], record['audio']['drive_id'],
                     record['provenance']['drive_id']}) == 4)
    except (ValueError, TypeError, KeyError):
        return False


def publisher_receipt_digest(record):
    """Stable association identity; shared files retain distinct listing receipts."""
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False).encode('utf-8')).hexdigest()


def shared_publisher_audio_reference(record, anchor, remote, owners):
    """One verified publisher file, with a separate qualified listing association."""
    row = record_row({'video_id': record.get('associated_youtube_id'), 'channel_dir': record.get('channel_dir')})
    if (not row or record.get('kind') != 'shared_publisher_audio_association' or
            record.get('schema_version') != 1 or record.get('status') != 'verified' or
            record.get('association_method') != 'publisher_owner_title_date_duration' or
            record.get('exact_youtube_crossreference') is not False or
            record.get('publisher_source_reused') is not True or
            record.get('recording_equivalence_verified') is not False or
            record.get('youtube_edit_equivalence_verified') is not False or
            not all(record.get(k) is False for k in ('native_youtube_bytes', 'changes_native_audio_count',
                'changes_native_asr_count', 'changes_native_caption_count', 'human_verified')) or
            record.get('source_tab') != 'videos' or record.get('caption_bundles') != [] or
            record.get('publisher_transcript') is not None):
        return False
    owner = owners.get(row['video_id'])
    if row['video_id'] in owners and (not owner or owner != (row['channel_dir'], 'videos')):
        return False
    evidence = record.get('source_tab_evidence')
    if (not isinstance(evidence, dict) or evidence.get('video_id') != row['video_id'] or
            evidence.get('channel_dir') != row['channel_dir'] or evidence.get('tab') != 'videos' or
            not re.fullmatch('[0-9a-f]{64}', str(evidence.get('roster_sha256', '')))):
        return False
    audio, provenance, pointer = (record.get(k) for k in ('audio', 'provenance', 'audio_reference'))
    source_provenance = record.get('canonical_provenance')
    if not all(publisher_object_proof(a) for a in (audio, provenance, pointer, source_provenance)):
        return False
    fields = ('remote', 'drive_id', 'bytes', 'md5', 'sha256')
    if (record.get('canonical_associated_youtube_id') != anchor.get('associated_youtube_id') or
            row['video_id'] == anchor.get('associated_youtube_id') or
            anchor.get('channel_dir') != row['channel_dir'] or anchor.get('source_tab', 'videos') != 'videos' or
            record.get('provider') != anchor.get('provider') or
            record.get('canonical_receipt_sha256') != publisher_receipt_digest(anchor) or
            any(audio[k] != anchor['audio'][k] or source_provenance[k] != anchor['provenance'][k] for k in fields) or
            record.get('variant_id') != audio['sha256'] or
            not re.fullmatch('[0-9a-f]{64}', str(record.get('accepted_api_sha256', ''))) or
            record['accepted_api_sha256'] != anchor.get('accepted_api_sha256') or
            not isinstance(record.get('source_episode_guid'), str) or not 0 < len(record['source_episode_guid']) <= 512):
        return False
    payload = record.get('canonical_provenance_payload')
    if not isinstance(payload, dict) or record.get('canonical_provenance_encoding') != 'sorted_compact_utf8_json_newline_v1':
        return False
    try:
        raw = (json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False,
                          separators=(',', ':')) + '\n').encode('utf-8')
    except (ValueError, TypeError):
        return False
    source = payload.get('qualified_source')
    if (len(raw) > 1_000_000 or len(raw) != source_provenance['bytes'] or
            hashlib.sha256(raw).hexdigest() != source_provenance['sha256'] or
            hashlib.md5(raw).hexdigest() != source_provenance['md5'] or
            not isinstance(source, dict) or source.get('guid') != record['source_episode_guid'] or
            payload.get('creator') != row['channel_dir'] or payload.get('feed_sha256') != record['accepted_api_sha256'] or
            payload.get('audio') != {k: audio[k] for k in ('bytes', 'md5', 'sha256')}):
        return False
    parent = f"{remote}/{row['channel_dir']}/Videos/{row['video_id']}/PublisherVariants/{audio['sha256']}"
    return (provenance['remote'] == parent + '/provenance.json' and
            pointer['remote'] == parent + '/publisher-audio.ref.json' and
            pointer.get('points_to_drive_id') == audio['drive_id'] and
            pointer.get('source_audio_sha256') == audio['sha256'] and
            pointer.get('source_audio_bytes') == audio['bytes'] and
            len({audio['drive_id'], source_provenance['drive_id'], provenance['drive_id'], pointer['drive_id']}) == 4)


def publisher_mirror_evidence(root, targets, remote, target_rows=None):
    """Separate timed captions, ASR and transcripts attached to verified publisher editions."""
    audio_ids, caption_ids, asr_ids, untimed_ids, sources = set(), set(), set(), set(), {}
    path = root / 'sync/publisher_mirror_manifest.jsonl'
    if not path.is_file():
        return audio_ids, caption_ids, asr_ids, untimed_ids
    owners = selected_recording_owners(root, target_rows)
    folders = {'videos': 'Videos', 'shorts': 'Shorts', 'streams': 'Streams'}
    records = []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            records.append(record)
    # Validate the existing anchor with its normal receipt contract even when
    # only the other listing was requested. Aliases cannot anchor other aliases.
    anchor_ids = {r['canonical_associated_youtube_id'] for r in records
        if r.get('kind') == 'shared_publisher_audio_association' and
        isinstance(r.get('canonical_associated_youtube_id'), str)}
    validation_targets = set(targets) | anchor_ids
    source_receipts = {}

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

    for record in records:
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
        paired_page = publisher_episode_page_reference(record)
        if not (qualified or exact or paired_page):
            continue
        row = record_row({'video_id': record.get('associated_youtube_id'), 'channel_dir': record.get('channel_dir')})
        audio, provenance = record.get('audio'), record.get('provenance')
        if (not row or row['video_id'] not in validation_targets or not publisher_object_proof(audio) or not publisher_object_proof(provenance) or
                audio['drive_id'] == provenance['drive_id'] or record.get('variant_id') != audio['sha256']):
            continue
        owner = owners.get(row['video_id'])
        if row['video_id'] in owners and (not owner or owner[0] != row['channel_dir']):
            continue
        selected_tab = owner[1] if owner and isinstance(owner[1], str) and owner[1] in folders else None
        receipt_tab = record.get('source_tab', record.get('tab'))
        if receipt_tab is not None and (
                not isinstance(receipt_tab, str) or receipt_tab not in folders or
                ('tab' in record and record['tab'] != receipt_tab) or
                (selected_tab and selected_tab != receipt_tab)):
            continue
        tab_evidence = record.get('source_tab_evidence')
        if tab_evidence is not None and (
                not isinstance(tab_evidence, dict) or tab_evidence.get('tab') != receipt_tab or
                tab_evidence.get('video_id') != row['video_id'] or
                tab_evidence.get('channel_dir') != row['channel_dir'] or
                not isinstance(tab_evidence.get('roster_sha256'), str) or
                not re.fullmatch('[0-9a-f]{64}', tab_evidence['roster_sha256'])):
            continue
        if receipt_tab in ('shorts', 'streams') and not (selected_tab or tab_evidence):
            continue
        # Historical untyped receipts used Videos. A known selection or typed
        # receipt binds both the audio and its provenance to the same category.
        folder = folders[receipt_tab or selected_tab or 'videos']
        parent = (remote + '/' + row['channel_dir'] + '/' + folder + '/' + row['video_id'] +
                  '/PublisherVariants/' + audio['sha256'])
        if (not isinstance(audio.get('remote'), str) or
                not re.fullmatch(re.escape(parent) + r'/publisher-audio\.(?:aac|m4a|mp3|opus|ogg|webm|flac)', audio['remote']) or
                provenance.get('remote') != parent + '/provenance.json'):
            continue
        if row['video_id'] in anchor_ids:
            try:
                source_receipts[publisher_receipt_digest(record)] = record
            except (ValueError, TypeError):
                pass
        sources[(row['video_id'], audio['sha256'])] = record
        if row['video_id'] not in targets:
            continue
        audio_ids.add(row['video_id'])
        transcript = record.get('publisher_transcript')
        if (publisher_object_proof(transcript) and transcript['drive_id'] not in {audio['drive_id'], provenance['drive_id']}
                and transcript.get('timed') is False and transcript.get('language') == 'en'
                and type(transcript.get('paragraphs')) is int and transcript['paragraphs'] > 0
                and record.get('caption_state') == 'english_publisher_transcript_untimed'
                and transcript.get('remote') == parent + '/publisher-transcript.en.txt'
                and (not paired_page or publisher_episode_transcript_reference(record, parent))):
            untimed_ids.add(row['video_id'])
        captions = record.get('caption_bundles')
        if not isinstance(captions, list):
            captions = [record.get('caption_bundle')]
        for caption in captions:
            if (publisher_object_proof(caption) and caption.get('usable_timed_text') is True and
                    caption['drive_id'] not in {audio['drive_id'], provenance['drive_id']} and
                    isinstance(caption.get('language'), str) and re.fullmatch(r'en(?:[-_][A-Za-z0-9-]+)?', caption['language']) and
                    caption.get('remote') == parent + '/Captions/' + caption['sha256'] + '/captions.zip'):
                caption_ids.add(row['video_id'])
    for record in records:
        if (not isinstance(record.get('associated_youtube_id'), str) or
                record['associated_youtube_id'] not in targets or record.get('kind') != 'shared_publisher_audio_association' or
                not isinstance(record.get('canonical_receipt_sha256'), str)):
            continue
        anchor = source_receipts.get(record.get('canonical_receipt_sha256'))
        if anchor and shared_publisher_audio_reference(record, anchor, remote, owners):
            audio_ids.add(record['associated_youtube_id'])
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
        source = sources.get((video_id, variant_id)) if video_id in targets else None
        if (not source or record.get('schema_version') != 1 or record.get('status') != 'verified' or
                record.get('artifact_kind') != 'publisher_variant_asr' or not publisher_object_proof(record) or
                record['drive_id'] in {source['audio']['drive_id'], source['provenance']['drive_id']} or
                record.get('quality_state') != 'unreviewed_asr' or record.get('channel_dir') != source['channel_dir'] or
                not re.fullmatch('[A-Za-z0-9_-]{1,120}', run_id) or
                not all(record.get(key) is False for key in ('native_youtube_bytes', 'changes_native_audio_count', 'changes_native_asr_count'))):
            continue
        same_source = True
        for key, source_key in (('source_audio', 'audio'), ('source_provenance', 'provenance')):
            value, expected = record.get(key), source[source_key]
            if not publisher_object_proof(value) or any(value.get(field) != expected[field] for field in ('bytes', 'drive_id', 'remote', 'md5', 'sha256')):
                same_source = False
        if not same_source:
            continue
        if (record.get('profile') == 'publisher-mirror-german-and-english-asr-v1' and
                record.get('output_contract') != 'original-and-english-v1'):
            continue
        parent = source['audio']['remote'].rpartition('/')[0]
        if record.get('remote') == parent + '/ASR/' + run_id + '/' + run_id + '.zip':
            asr_ids.add(video_id)
    return audio_ids, caption_ids, asr_ids, untimed_ids


def publisher_mirror_coverage(root, targets, remote, target_rows=None):
    """Existing audio, timed-caption and ASR view used by collection workers."""
    return publisher_mirror_evidence(root, targets, remote, target_rows)[:3]


def snapshot(root, now=None, remote=DEFAULT_REMOTE, managed_roots=(), selection=None):
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
    selected = selection_rows(selection) if selection is not None else None
    target_rows = selected['rows'] if selected is not None else None
    if selected is not None:
        twenty = {row['video_id'] for row in target_rows}
        channels = len(selected['creators'])
    chosen_native = ({row['video_id'] for row in target_rows
                      if row['video_id'] in latest and latest[row['video_id']].get('channel_dir') == row['channel_dir']
                      and proof(receipt_complete, latest[row['video_id']], row, remote)}
                     if selected is not None else archived & twenty)
    fifty, _ = queue_ids(root, ("queue_newest50_enriched.csv", "queue_newest50.csv"))
    full, _ = queue_ids(root, ("queue_youtube_all_merged.csv", "queue_youtube_all.csv"))
    remaining, _ = queue_ids(root, ("queue_final_round.csv",))
    publisher_texts, publisher_transcripts, publisher_variants, publisher_qualified, publisher_asr = publisher_coverage(root, twenty, remote, target_rows=target_rows)
    mirror_audio, mirror_captions, mirror_asr, mirror_transcripts = publisher_mirror_evidence(root, twenty, remote, target_rows=target_rows)
    companion_messages, companion_sessions = companion_writings(root, twenty, remote, target_rows=target_rows)
    qualified_audio = qualified_edition_coverage(root, twenty, remote, target_rows=target_rows)
    publisher_timed_text = publisher_timed_text_coverage(root, twenty, remote, target_rows=target_rows)
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
    legacy_operation = {'state': state, 'retry_after': stamp(until) if until else None,
                        'cooldown_provider': provider, 'workers': workers, 'full_archive_requested': archive_all}
    series = active_native_series(root, now)
    native_lane = (rolling_native_state(root, now).get('public') or native_bulk_lane(root, now) or native_v5_lane(root, now) or native_source_hold(root, now) or direct_native_batch(root, now) or completed_native_lane(root, now)) if not series else {
        'state': 'running', 'workers': series['workers'], 'kind': 'native_v4',
        'process_confirmed': True, 'proof': 'owned_live_process'}
    qualified_state = qualified_batch_state(root, now)
    qualified_lane = dict(qualified_state.get('public', {}))
    source_available = chosen_native | publisher_variants | mirror_audio | qualified_audio
    selected_text = (text_available & chosen_native) | publisher_asr | mirror_captions | mirror_asr | mirror_transcripts
    qualified_awaiting = {video for video, stage in qualified_state.get('video_stages', {}).items()
                         if stage == 'awaiting_upload' and video not in source_available}
    if qualified_lane:
        qualified_lane['saved_audio_items'] = len(source_available & set(qualified_state.get('scope_video_ids', [])))
        qualified_lane['awaiting_upload'] = len(qualified_awaiting)
    if series.get('kind') == 'native_v4_campaign':
        native_lane.update({key: value for key, value in series.items() if key not in
                           ('workers', 'asr_running', 'asr_reported_at')})
    if series:
        state, workers, until, provider = 'running', series['workers'], None, None
        archive_all = False
        if series['asr_running']:
            asr_state, asr_reported_at = 'running', series['asr_reported_at']
    elif native_lane:
        state, workers, until, provider = native_lane['state'], native_lane['workers'], None, None
        if native_lane.get('kind') in {'native_v4_source_hold', 'native_v5_source_hold'}:
            provider = 'youtube'
            retry = native_lane.get('retry_after')
            until = dt.datetime.fromisoformat(retry.replace('Z', '+00:00')).timestamp() if retry else None
        archive_all = False
    if qualified_lane and (qualified_lane['state'] == 'running' or state != 'running'):
        state, workers, until, provider = qualified_lane['state'], qualified_lane['workers'], None, None
        deadline = qualified_lane.get('local_provider_cooldown_until_epoch')
        if qualified_lane.get('reason') == 'provider_hold' and deadline and deadline > now:
            state, until, provider = 'cooldown', deadline, 'youtube'
        archive_all = False
    asr_stop = root / 'asr/STOP_ASR'
    if asr_stop.exists():
        gpu = read_object(root / 'sync/gpu_lease.json')
        asr_state = 'paused' if gpu.get('state') == 'released' else 'stopping'
        try:
            asr_reported_at = stamp(asr_stop.stat().st_mtime)
        except OSError:
            asr_reported_at = None
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
        storage['managed_bytes'] = sum(local_bytes if path == root.resolve() else tree_bytes(path) for path in included)
        plan = read_object(root / 'sync/analysis_resource_plan.json')
        managed_cap = plan.get('accounting_cap_bytes')
        if type(managed_cap) is int and 1_000_000_000 <= managed_cap <= MAX_LOCAL_BYTES:
            storage['managed_ceiling_bytes'] = managed_cap
    resolved = archived | unavailable
    complete20 = bool(twenty) and twenty <= (source_available if selected is not None else resolved)
    complete50 = bool(fifty) and fifty <= resolved
    public = {"schema_version": 1, "generated_at": stamp(now), "scope": "local_youtube_collection",
            "operation": {"state": state, "retry_after": stamp(until) if until else None,
                          "asr_last_reported_state": asr_state, "asr_reported_at": asr_reported_at,
                          "workers": workers, "full_archive_requested": archive_all,
                          "cooldown_provider": provider, "caption_state": caption_state,
                          "caption_retry_after": stamp(caption_until) if caption_until else None},
            "legacy_operation": legacy_operation, "native_lane": native_lane, "qualified_lane": qualified_lane,
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
                       "publisher_mirror_untimed_transcript_target_videos": len(mirror_transcripts),
                       "publisher_written_message_target_videos": len(companion_messages),
                       "publisher_session_text_target_videos": len(companion_sessions),
                       "publisher_standalone_timed_text_target_videos": len(publisher_timed_text),
                       "qualified_youtube_audio_edition_target_videos": len(qualified_audio),
                       "source_audio_available_target_videos": len(source_available),
                       "source_audio_with_text_target_videos": len(selected_text),
                       "caption_verified_videos": len(caption_verified), "caption_verified_tracks": len(verified_tracks),
                       "caption_none_english": len(caption_none), "caption_pending_videos": len(caption_pending),
                       "unavailable": len(unavailable),
                       "awaiting_upload": len((audio - verified) | qualified_awaiting), "channels": channels,
                       "indexed_total": len(full | twenty | fifty), "final_round_indexed": len(remaining)},
            "storage": storage, "browser_support": browser_extension_status(root),
            "stages": [{"key": "newest20", "label": "Latest 20 mixed recordings" if selected is not None else "Newest 20", "total": len(twenty),
                        "verified": len(source_available) if selected is not None else len(twenty & archived), "unavailable": len(twenty & unavailable),
                        "state": "complete" if complete20 else "in_progress"},
                       {"key": "newest50", "label": "Extend to 50", "total": len(fifty),
                        "verified": len(fifty & archived), "unavailable": len(fifty & unavailable),
                        "state": "complete" if complete50 else "in_progress" if complete20 else "waiting"},
                       {"key": "final_archive" if archive_all else "final_index",
                        "label": "Archive the remainder" if archive_all else "Index the remainder", "total": len(remaining),
                        "verified": len(remaining & archived), "unavailable": len(remaining & unavailable),
                        "state": ("complete" if remaining and remaining <= resolved else "in_progress" if complete50 else "waiting")
                                 if archive_all else "indexed" if remaining else "waiting"}]}
    if selected is not None:
        selected_unavailable = {row['video_id'] for row in target_rows if row['video_id'] in unavailable
                                and latest[row['video_id']].get('channel_dir') == row['channel_dir']}
        def counts(ids):
            return {'total': len(ids), 'verified_audio': len(ids & source_available),
                    'youtube_native': len(ids & chosen_native),
                    'publisher_only': len(ids & (publisher_variants | mirror_audio) - chosen_native),
                    'qualified_only': len(ids & qualified_audio - chosen_native - publisher_variants - mirror_audio),
                    'unavailable': len(ids & selected_unavailable - source_available),
                    'remaining_audio': len(ids - source_available)}
        by_format = {tab: counts({row['video_id'] for row in target_rows if row['tab'] == tab})
                     for tab in ('videos', 'shorts', 'streams', 'unknown')}
        public['selection'] = {'basis': selected['basis'], 'source_shape': selected['shape'], 'sha256': selected['sha256'],
            'label': 'Latest 20 regular uploads per channel' if selected.get('archive') else 'Canonical latest20 mixed-format completed-recording selection', 'creator_count': channels,
            **counts(twenty), 'by_format': by_format,
            'creators': [{'channel_dir': name, **info,
                          **counts({row['video_id'] for row in target_rows if row['channel_dir'] == name})}
                         for name, info in sorted(selected['creators'].items())],
            'completion_requires_verified_chosen_audio': True,
            'unavailable_is_not_audio_completion': True, 'historical_transfer_rate_reused': False}
        public['counts']['latest20_target'] = len(twenty)
        if selected.get('archive'):
            public['selection'].update(archive=selected['archive'], priority_scope_sha256=selected['priority_scope_sha256'])
            public['stages'][0]['label'] = 'Latest 20 regular uploads'
        public['counts']['selected_native_pairs'] = len(chosen_native)
        public['counts']['native_archive_inventory_scope'] = 'historical_all_saved_native_receipts'
        public['stages'][0].update(unavailable=len(selected_unavailable - source_available), remaining=len(twenty - source_available),
                                   selection_sha256=selected['sha256'], basis=selected['basis'])
        for stage in public['stages'][1:]:
            stage['basis'] = 'legacy_videos_queue'
    return public


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--remote", default=DEFAULT_REMOTE, help="Exact archive destination used by receipt proofs")
    ap.add_argument("--selection", type=Path, help="Use a dated regular or mixed recording selection in place of the historical CSV queue")
    ap.add_argument("--managed-root", type=Path, action="append", default=[],
                    help="Additional project tool/repository roots to include in aggregate storage accounting")
    args = ap.parse_args(argv)
    public = snapshot(args.root, remote=args.remote, managed_roots=args.managed_root, selection=args.selection)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    temporary.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.out)
    print(json.dumps(public, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
