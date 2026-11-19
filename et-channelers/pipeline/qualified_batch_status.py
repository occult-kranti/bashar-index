"""Read bounded qualified-batch ownership proofs without executing private code.

Only ``public`` is exportable. The private stage map joins the selected queue;
neither a progress flag nor a local result establishes saved-audio coverage.
"""
from __future__ import annotations
import hashlib
import math
from pathlib import Path
import re

if __package__:
    from . import host_capacity
else:
    import host_capacity

PROFILE = re.compile(r'qualified_youtube_response18_parallel_batch(?:_recovery[1-9][0-9]*)?_v[1-9][0-9]*\Z')
VIDEO = re.compile(r'[A-Za-z0-9_-]{11}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')
ROLES = {'controller.py', 'source_worker.py', 'batch_contract.py', 'worker_contract.py',
         'owned_child.py', 'owner_supervisor.py', 'io_helpers.py', 'media_gate.py',
         'runtime_policy.py', 'wpc_boundary.py', 'publisher.py', 'receipt_builder.py',
         'quality_component.py', 'qualified_edition_receipts.py'}


def identity(value):
    if not isinstance(value, dict) or type(value.get('pid')) is not int or value['pid'] <= 0:
        return None
    creation = str(value.get('process_creation_filetime', ''))
    return (value['pid'], creation) if creation.isascii() and creation.isdigit() and int(creation) > 0 else None


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def read(root, now, *, object_reader, bound_reader, code_reader, alive, child_of, command):
    """One current finite scope; malformed newer ownership never falls back live."""
    root = Path(root).resolve()
    paths = list((root / 'sync').glob('qualified_youtube_response18_parallel_batch*_lease.json'))
    if not paths:
        return {}
    objects = {}
    def small(path):
        path = Path(path)
        if path in objects:
            return objects[path]
        try:
            if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= 8_000_000:
                return {}
        except OSError:
            return {}
        objects[path] = object_reader(path)
        return objects[path]
    try:
        leases = [(path, small(path)) for path in paths]
        if any(not positive(value.get('created_at_epoch')) for _, value in leases):
            return {}
        paths = [path for path, _ in sorted(leases, key=lambda pair: pair[1]['created_at_epoch'], reverse=True)]
        return _read(root, now, paths[0], small, bound_reader, code_reader, alive, child_of, command)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {}


def _read(root, now, lease_path, obj, bound, code, alive, child_of, command):
    lease = obj(lease_path); profile = lease.get('profile', '')
    if not (isinstance(profile, str) and PROFILE.fullmatch(profile) and
            lease_path.name == profile + '_lease.json' and lease.get('lease_id') == profile and
            lease.get('owner') == 'root' and lease.get('state') in {'active', 'released'}):
        return {}
    settings_hash, grant_hash = lease.get('settings_sha256'), lease.get('root_grant_sha256')
    if not all(isinstance(value, str) and SHA.fullmatch(value) for value in (settings_hash, grant_hash)):
        return {}
    # Resolve the version directly. Each historical layout must bind the same actual invocation.
    suffix = profile.removeprefix('qualified_youtube_response18_parallel_batch_').replace('_', '-')
    layouts = [f'qualified-response18-parallel-batch-{suffix}', f'regular-public-intake-frame-{suffix}']
    if suffix == 'v8':
        layouts.append('regular-fresh-intake-v1')
    homes = [root / 'provisioning' / name for name in layouts]
    homes = [home for home in homes if obj(home / 'owner-runtime/invocation.json').get('root_grant_sha256') == grant_hash]
    if len(homes) != 1:
        return {}
    home = homes[0].resolve()
    def pinned(path, expected):
        path = Path(path)
        return bound(root, {'path': str(path), 'bytes': path.stat().st_size, 'sha256': expected})
    settings_path, grant_path = home / 'settings.json', home / 'root-grant.ACTIVE.json'
    settings, grant = pinned(settings_path, settings_hash), pinned(grant_path, grant_hash)
    plan_hash = grant.get('plan_sha256'); scope = pinned(home / 'scope.json', plan_hash)
    ids = grant.get('allowed_video_ids')
    workers, spool = grant.get('source_workers'), grant.get('spool_cap_bytes')
    # Older grants used fixed two-worker, twenty-item defaults. New frames bind their limits explicitly.
    max_items = grant.get('maximum_cohort_items', 20)
    if not (settings and scope and grant.get('enabled') is True and grant.get('owner') == 'root' and
            grant.get('source_authorized') is True and grant.get('drive_publication_allowed') is True and
            all(grant.get(key) is True for key in ('literal_language_tags_authorized', 'default_is_not_original_authorized',
                 'native_route_handoff_authorized', 'two_stage_media_GO_required', 'atomic_derived_MOVE_required')) and
            grant.get('ASR_authorized') is False and grant.get('GPU_authorized') is False and
            grant.get('automatic_retry_allowed') is False and grant.get('qualified_success_HTTP_reset_allowed') is False and
            grant.get('profile') == settings.get('profile') == settings.get('lease_id') == profile and
            grant.get('settings_sha256') == settings_hash and
            Path(settings.get('pipeline_directory', '')).resolve() == home and
            Path(settings.get('private_root', '')).resolve() == root and
            isinstance(ids, list) and type(max_items) is int and 1 <= len(ids) <= max_items and
            max_items == settings.get('maximum_cohort_items', 20) and len(set(ids)) == len(ids) and
            all(isinstance(value, str) and VIDEO.fullmatch(value) for value in ids) and
            ids == settings.get('allowed_video_ids') == scope.get('video_ids', scope.get('allowed_video_ids')) == lease.get('allowed_video_ids') and
            scope.get('allowed_video_ids', ids) == ids and
            type(workers) is int and 1 <= workers <= 6 and workers == settings.get('source_workers', 2) == lease.get('source_workers') and
            grant.get('publishers') == settings.get('publishers', 1) == 1 and
            grant.get('maximum_source_bytes') == grant.get('maximum_derived_bytes') == 2_000_000_000 and
            type(spool) is int and 0 < spool <= host_capacity.MAX_MANAGED_BYTES and
            spool == settings.get('spool_cap_bytes', 5_000_000_000) == lease.get('spool_cap_bytes')):
        return {}
    pins = {Path(row.get('path', '')).name: row for row in settings.get('code_pins', [])
            if isinstance(row, dict) and Path(row.get('path', '')).parent.resolve() == home}
    if not ROLES <= pins.keys() or not all(code(root, pins[name]) for name in ROLES):
        return {}
    rows = obj(root / 'sync/analysis_resource_plan.json').get('reservations', [])
    matching = [row for row in rows if row.get('lease_id') == profile]
    if not (len(matching) == 1 and matching[0].get('root_grant_sha256') == grant_hash and
            matching[0].get('max_bytes') == spool):
        return {}
    owner = home / 'owner-runtime'; invoked = obj(owner / 'invocation.json')
    launcher = invoked.get('identity'); started = invoked.get('started_at_epoch')
    if not (identity(launcher) and positive(started) and started <= now + 5 and
            invoked.get('settings_sha256') == settings_hash and invoked.get('plan_sha256') == plan_hash and
            invoked.get('source_count') == len(ids) and invoked.get('source_workers', 2) == workers and
            invoked.get('owned_job_attached') is True and
            invoked.get('suspended_attach_before_resume') is True):
        return {}
    terminal, exited = obj(owner / 'terminal.json'), obj(owner / 'process-exit.json')
    report = bound(root, terminal.get('actual_cohort_report'))
    closure = exited.get('owned_closure', {})
    closed = (terminal.get('owned_job_closed') is True and closure.get('closed') is True and
              closure.get('owned_job_empty') is True and not closure.get('errors') and
              identity(launcher) == identity(exited.get('identity')) == identity(closure.get('identity')) and
              terminal.get('root_grant_sha256') == exited.get('root_grant_sha256') == grant_hash and
              type(exited.get('exit_code')) is int and terminal.get('exit_code') == exited['exit_code'] and
              positive(terminal.get('at_epoch')) and started <= terminal['at_epoch'] <= now + 5)
    release = obj(home / 'closure/release-proof.json')
    released = (lease.get('state') == matching[0].get('state') == 'released' and
                release.get('root_grant_sha256') == grant_hash and
                bound(root, release.get('released_lease')) == lease and
                bound(root, release.get('terminal')) == terminal and bound(root, release.get('exit')) == exited)
    if lease.get('state') == 'released' and not closed:
        return {}
    admin = obj(root / 'sync' / (profile + '_administrative_hold.json'))
    provider_stop = (root / 'sync' / ('STOP_' + profile.upper())).is_file()
    current = (lease.get('state') == matching[0].get('state') == 'active' and
               positive(grant.get('expires_at_epoch')) and now < grant['expires_at_epoch'] and
               positive(grant.get('not_before_epoch')) and grant['not_before_epoch'] <= now)
    process_confirmed = False
    if not closed and current:
        controller = obj(home / 'runtime/source-invocation.json').get('parent_identity')
        if controller and identity(controller) and alive(launcher) and alive(controller):
            process_confirmed = ((identity(controller) == identity(launcher) or child_of(controller, launcher)) and
                                 command(controller, settings_path, home / 'controller.py', grant_path))
        elif alive(launcher):
            process_confirmed = command(launcher, settings_path, home / 'controller.py', grant_path)
    state = 'paused' if admin or provider_stop else 'ready' if closed and report.get('status') == 'complete' else \
        'paused' if closed else 'running' if process_confirmed else 'unconfirmed'
    stages = {}; attempted = 0; audits_complete = True
    for video in ids:
        run = root / profile / 'jobs' / video; attempt = obj(run / 'attempt.json')
        if not attempt:
            if state == 'running': stages[video] = 'queued'
            continue
        if not (attempt.get('video_id') == video and attempt.get('root_grant_sha256') == grant_hash and
                attempt.get('settings_sha256') == settings_hash and attempt.get('plan_sha256') == plan_hash):
            return {}
        attempted += 1; progress, result, audit = (obj(run / name) for name in ('progress.json', 'result.json', 'parent-audit.json'))
        binding = obj(run / 'child-binding.json'); worker = binding.get('child_identity')
        own_closed = (audit.get('owned_processes_gone') is True and audit.get('owned_closure', {}).get('closed') is True and
                      audit.get('root_grant_sha256') == grant_hash and audit.get('settings_sha256') == settings_hash and
                      audit.get('plan_sha256') == plan_hash and
                      audit.get('attempt_sha256') == hashlib.sha256((run / 'attempt.json').read_bytes()).hexdigest())
        audits_complete = audits_complete and own_closed
        if own_closed and result.get('status') == 'local_extract_complete':
            stages[video] = 'awaiting_upload'
        elif state == 'running' and identity(worker) and binding.get('Windows_job_attached') is True and alive(worker):
            count = progress.get('audio_source_bytes_written', 0)
            stages[video] = 'downloading' if progress.get('phase') == 'native_transfer' and type(count) is int and count > 0 else 'processing'
        else:
            stages[video] = 'held' if own_closed and result else 'unresolved'
    outcomes = report.get('outcomes', [])
    verified = sum(row.get('state') == 'verified' for row in outcomes if isinstance(row, dict))
    if report and (report.get('root_grant_sha256') != grant_hash or terminal.get('verified_editions') != verified or
                   not isinstance(outcomes, list) or len(outcomes) != len(ids) or
                   {row.get('video_id') for row in outcomes if isinstance(row, dict)} != set(ids) or
                   any(row.get('state') not in {'verified', 'held', 'retained', 'pending', 'inflight'} for row in outcomes)):
        return {}
    if closed:
        for outcome in outcomes:
            if outcome['state'] == 'verified':
                # A published pair has left the spool. The receipt reader determines archive coverage.
                stages.pop(outcome['video_id'], None)
    cooldown = obj(root / 'sync' / (profile + '_source_cooldown.json'))
    retry_at = cooldown.get('until_epoch')
    local_deadline = (retry_at if provider_stop and cooldown.get('root_grant_sha256') == grant_hash and
                      cooldown.get('scope') == 'google_provider' and positive(retry_at) else None)
    public = {'kind': 'qualified_youtube_batch', 'state': state, 'workers': workers if state == 'running' else 0,
              'process_confirmed': process_confirmed, 'source_count': len(ids), 'attempted_items': attempted,
              'not_started_items': len(ids) - attempted, 'held_items': sum(value == 'held' for value in stages.values()),
              'unresolved_items': sum(value == 'unresolved' for value in stages.values()),
              'awaiting_upload': sum(value == 'awaiting_upload' for value in stages.values()),
              'reported_verified_pairs': verified, 'child_audits_complete': audits_complete,
              'owned_processes_closed': bool(closed), 'future_growth_released': bool(released),
              'started_at_epoch': started, 'finished_at_epoch': terminal.get('at_epoch') if closed else None,
              'reason': 'provider_hold' if provider_stop else 'administrative_review' if admin or state == 'paused' else None,
              'local_provider_cooldown_until_epoch': local_deadline,
              'ETA_state': 'unmeasured', 'planning_active_hours': None, 'Native_count_increment': 0}
    deferred = [row['video_id'] for row in outcomes if row['state'] == 'pending'] if closed and local_deadline and now < local_deadline else []
    return {'public': public, 'video_stages': stages, 'scope_video_ids': ids, 'deferred_video_ids': deferred}
