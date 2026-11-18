"""Finite cohort metadata binding. No source, process launch, or admission writes."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time

PROFILE = 'stock_headful_wpc_native_batch_v5_bulk_recovery4'
MAX_COHORT = 1280
MAX_FRAME = 20
SHA = re.compile(r'[a-f0-9]{64}\Z')
VIDEO = re.compile(r'[A-Za-z0-9_-]{11}\Z')
CODE = Path(__file__).resolve().parent


class ContractError(ValueError):
    pass


def need(value, code):
    if not value:
        raise ContractError(code)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    path = Path(path)
    need(path.stat().st_size <= 16 * 1024**2, 'bulk_metadata_size')
    return json.loads(path.read_bytes())


def terminal_result_complete(value, video_id):
    """A closed worker's atomic terminal result is authoritative; progress is optional."""
    return (isinstance(value, dict) and value.get('schema_version') == 1 and
            value.get('video_id') == video_id and value.get('status') in {'held', 'local_complete'} and
            isinstance(value.get('diagnostics'), dict) and value['diagnostics'].get('phase') == 'terminal')


def parent_deadline_valid(value, settings):
    if not isinstance(value, dict) or set(value) != {'kind', 'configured_seconds', 'actual_elapsed_seconds'}:
        return False
    kind, configured, elapsed = (value.get(key) for key in ('kind', 'configured_seconds', 'actual_elapsed_seconds'))
    expected = 90 if kind == 'bootstrap_deadline' else settings.get('job_wall_seconds') if kind == 'job_deadline' else None
    return (type(configured) in (int, float) and type(elapsed) in (int, float) and
            math.isfinite(configured) and math.isfinite(elapsed) and configured > 0 and
            configured == expected and elapsed >= configured)


def parent_censored_valid(folder, video_id, settings_path, plan_sha256):
    """Validate retained parent evidence; it never asserts worker success or zero access."""
    try:
        folder = Path(folder); value = read(folder/'parent-censored.json'); settings = read(settings_path)
        need(value.get('schema_version') == 1 and value.get('kind') == 'parent_censored_native_attempt' and
             value.get('video_id') == video_id and value.get('profile') == PROFILE and
             value.get('plan_sha256') == plan_sha256 and parent_deadline_valid(value.get('deadline'), settings),
             'parent_censored_scope')
        need(all(value.get(key) is False for key in ('counts_as_success', 'resets_streak', 'automatic_retry',
                                                   'worker_terminal_result_fabricated')) and
             value.get('item_quarantined') is True and value.get('source_access') == 'unknown' and
             value.get('source_counters_state') == 'unknown' and value.get('source_counters') == {
                 'python_wire_requests': None, 'python_body_bytes': None,
                 'audio_bytes_written': None, 'browser_observed_requests': None}, 'parent_censored_truth')
        need(value.get('provenance_validated') is True and
             value.get('settings_sha256') == digest(settings_path) and
             value.get('root_grant_sha256') == digest(settings['root_admission_path']) and
             value.get('coordinator_sha256') == digest(CODE/'native_batch.py') and
             value.get('worker_sha256') == digest(CODE/'native_batch_worker.py') and
             value.get('attempt_sha256') == digest(folder/'attempt.json'), 'parent_censored_provenance')
        attempt = read(folder/'attempt.json')
        need(attempt.get('schema_version') == 1 and attempt.get('video_id') == video_id and
             attempt.get('plan_sha256') == plan_sha256 and attempt.get('worker_sha256') == value['worker_sha256'],
             'parent_censored_attempt_binding')
        proof = value.get('parent_audit', {})
        need(proof.get('filename') == 'parent-audit.json' and
             proof.get('sha256') == digest(folder/'parent-audit.json') and
             proof.get('bytes') == (folder/'parent-audit.json').stat().st_size, 'parent_censored_audit_pin')
        audit = read(folder/'parent-audit.json'); identity = value.get('owned_child_identity', {})
        need(audit.get('schema_version') == 1 and audit.get('video_id') == video_id and
             type(identity.get('pid')) is int and identity['pid'] > 0 and
             isinstance(identity.get('process_creation_filetime'), str) and
             identity['process_creation_filetime'].isdigit() and int(identity['process_creation_filetime']) > 0 and
             audit.get('owned_child_identity') == identity and audit.get('owned_processes_gone') is True and
             audit.get('profile_cleaned') is True and audit.get('process_cleanup_errors') == [] and
             audit.get('parent_deadline') == value['deadline'] and audit.get('error_class') == value['deadline']['kind'],
             'parent_censored_owned_closure')
        need(type(audit.get('elapsed_seconds')) in (int, float) and math.isfinite(audit['elapsed_seconds']) and
             audit['elapsed_seconds'] >= value['deadline']['actual_elapsed_seconds'], 'parent_censored_elapsed')
        return True
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return False


def pinned(pin):
    need(isinstance(pin, dict) and isinstance(pin.get('path'), str) and
         isinstance(pin.get('sha256'), str) and SHA.fullmatch(pin['sha256']), 'bulk_pin')
    need(digest(pin['path']) == pin['sha256'], 'bulk_pin_changed')
    return read(pin['path'])


def manifest_ids(value):
    need(isinstance(value, dict) and value.get('schema_version') == 1 and
         isinstance(value.get('cohort_id'), str) and 0 < len(value['cohort_id']) <= 120,
         'bulk_manifest')
    ids = value.get('allowed_video_ids')
    need(isinstance(ids, list) and 0 < len(ids) <= MAX_COHORT and
         all(isinstance(x, str) and VIDEO.fullmatch(x) for x in ids) and
         len(ids) == len(set(ids)), 'bulk_exact_finite_scope')
    return ids


def frames(value, cohort_sha, ids):
    need(isinstance(value, dict) and value.get('schema_version') == 1 and
         value.get('cohort_manifest_sha256') == cohort_sha, 'bulk_frame_map')
    rows = value.get('frames')
    need(isinstance(rows, list) and 0 < len(rows) <= MAX_COHORT, 'bulk_frame_count')
    combined = []
    plans = set()
    paths = set()
    for index, row in enumerate(rows):
        need(isinstance(row, dict) and type(row.get('frame_index')) is int and
             row['frame_index'] == index, 'bulk_frame_order')
        members = row.get('video_ids')
        need(isinstance(members, list) and 0 < len(members) <= MAX_FRAME and
             all(isinstance(x, str) and VIDEO.fullmatch(x) for x in members) and
             len(members) == len(set(members)), 'bulk_frame_members')
        need(isinstance(row.get('plan_sha256'), str) and SHA.fullmatch(row['plan_sha256']) and
             row['plan_sha256'] not in plans, 'bulk_frame_plan_pin')
        need(all(isinstance(row.get(k), str) and Path(row[k]).is_absolute()
                 for k in ('plan_path', 'settings_path')), 'bulk_frame_paths')
        need(str(Path(row['settings_path']).resolve()).lower() not in paths, 'bulk_frame_settings_unique')
        paths.add(str(Path(row['settings_path']).resolve()).lower())
        plans.add(row['plan_sha256'])
        combined.extend(members)
    need(combined == ids and len(combined) == len(set(combined)), 'bulk_frame_partition')
    return rows


def metadata(settings_path):
    settings_path = Path(settings_path).resolve()
    settings = read(settings_path)
    manifest = pinned(settings['cohort_manifest'])
    ids = manifest_ids(manifest)
    mapping = pinned(settings['frame_map'])
    rows = frames(mapping, settings['cohort_manifest']['sha256'], ids)
    return settings, manifest, ids, rows


def grant_binding(settings, ids, rows, lease, now=None):
    now = time.time() if now is None else now
    need(type(now) in (int, float) and math.isfinite(now), 'bulk_clock')
    grant_path = Path(settings['root_admission_path'])
    need(digest(grant_path) == lease.get('root_admission_sha256'), 'bulk_root_grant_pin')
    grant = read(grant_path)
    need(grant.get('authorized') is True and grant.get('owner') == settings.get('owner') == 'root' and
         grant.get('profile') == lease.get('profile') == PROFILE and
         all(grant.get(k) is True and lease.get(k) is True for k in
             ('source_scope_authorized', 'synthetic_v4_breaker_override_authorized', 'finite_cohort_scope_authorized')),
         'bulk_root_scope_not_admitted')
    need(lease.get('schema_version') == 1 and lease.get('state') == 'active' and
         lease.get('authorized') is True and lease.get('owner') == settings['owner'] and
         lease.get('lease_id') == settings['lease_id'], 'bulk_lease_owner')
    need(type(grant.get('not_before_epoch')) in (int, float) and
         type(grant.get('expires_at_epoch')) in (int, float) and
         type(lease.get('expires_at_epoch')) in (int, float) and
         grant['not_before_epoch'] <= now < lease['expires_at_epoch'] <= grant['expires_at_epoch'],
         'bulk_grant_or_lease_expired')
    need(grant.get('source_invocations') == 1 and grant.get('workers') == 2 and
         grant.get('publishers') == 1 and grant.get('retries') == 0 and
         grant.get('spool_cap_bytes') == lease.get('spool_cap_bytes') == 5_500_000_000,
         'bulk_bounded_admission')
    need(grant.get('allowed_video_ids') == lease.get('allowed_video_ids') == ids,
         'bulk_grant_manifest_membership')
    for key in ('cohort_manifest', 'frame_map'):
        need(grant.get(key + '_sha256') == lease.get(key + '_sha256') == settings[key]['sha256'],
             'bulk_grant_metadata_binding')
    for key, filename in (('coordinator_sha256', 'native_batch.py'),
                          ('worker_sha256', 'native_batch_worker.py'),
                          ('http_policy_sha256', 'native_http_policy.py'),
                          ('contract_sha256', 'bulk_contract.py'),
                          ('controller_sha256', 'native_bulk_controller.py')):
        need(grant.get(key) == digest(CODE / filename), 'bulk_code_grant_binding')
    allowed_settings = grant.get('frame_settings')
    need(isinstance(allowed_settings, list) and len(allowed_settings) == len(rows), 'bulk_all_frame_settings')
    for row, binding in zip(rows, allowed_settings):
        need(isinstance(binding, dict) and binding.get('frame_index') == row['frame_index'] and
             binding.get('plan_sha256') == row['plan_sha256'] and
             isinstance(binding.get('settings_sha256'), str) and SHA.fullmatch(binding['settings_sha256']),
             'bulk_frame_settings_binding')
    return grant


def frame_admission(settings_path, lease, *, now=None):
    settings_path = Path(settings_path).resolve()
    settings, manifest, ids, rows = metadata(settings_path)
    index = settings.get('cohort_frame_index')
    need(type(index) is int and 0 <= index < len(rows), 'bulk_frame_index')
    row = rows[index]
    need(Path(row['settings_path']).resolve() == settings_path and
         Path(row['plan_path']).resolve() == Path(settings['plan_path']).resolve() and
         digest(row['plan_path']) == row['plan_sha256'], 'bulk_current_frame_binding')
    plan = read(row['plan_path'])
    need(plan.get('schema_version') == 1 and isinstance(plan.get('items'), list) and
         [x.get('video_id') for x in plan['items']] == row['video_ids'], 'bulk_current_frame_membership')
    controller = pinned(settings['cohort_controller_settings'])
    need(all(controller.get(k) == settings.get(k) for k in ('owner', 'lease_id', 'root_admission_path')) and
         controller.get('cohort_manifest') == settings['cohort_manifest'] and
         controller.get('frame_map') == settings['frame_map'] and
         Path(controller['root']).resolve() == Path(settings['private_root']).resolve(), 'bulk_controller_binding')
    grant = grant_binding(settings, ids, rows, lease, now)
    need(grant.get('controller_settings_sha256') == lease.get('controller_settings_sha256') ==
         settings['cohort_controller_settings']['sha256'] and
         grant['frame_settings'][index]['settings_sha256'] == digest(settings_path), 'bulk_current_settings_pin')
    review = pinned(settings['historical_http_review'])
    need(grant.get('root_policy_review_sha256') == settings['historical_http_review']['sha256'] and
         review.get('allowed_video_ids') == ids and review.get('root_scope_kind') == 'finite_immutable_cohort' and
         review.get('cohort_manifest_sha256') == settings['cohort_manifest']['sha256'] and
         review.get('frame_map_sha256') == settings['frame_map']['sha256'], 'bulk_review_exact_scope')
    proof = pinned(settings['never_attempted_scope_proof'])
    need(grant.get('never_attempted_scope_sha256') == settings['never_attempted_scope_proof']['sha256'] and
         proof.get('all_candidates_proven_never_attempted') is True and proof.get('allowed_video_ids') == ids and
         all(proof.get(k) == [] for k in ('prior_attempt_overlaps', 'quarantine_overlaps',
                                        'uncertain_overlaps', 'canonical_or_publisher_overlaps')),
         'bulk_never_attempted_cohort_required')
    view = dict(lease, settings_sha256=digest(settings_path), plan_sha256=row['plan_sha256'])
    return view, grant


def windows_identity(pid=None, handle=None):
    """Read identity only from this process or an already-owned child handle."""
    need(os.name == 'nt', 'bulk_windows_identity_required')
    pid = os.getpid() if pid is None else pid
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    need(handle is not None or pid == os.getpid(), 'bulk_identity_handle_scope')
    handle = kernel.GetCurrentProcess() if handle is None else wintypes.HANDLE(int(handle))
    creation, exit_time, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
    need(kernel.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time),
                                ctypes.byref(kernel_time), ctypes.byref(user_time)), 'bulk_identity_query')
    return {'pid': pid, 'process_creation_filetime': str((creation.dwHighDateTime << 32) | creation.dwLowDateTime)}
