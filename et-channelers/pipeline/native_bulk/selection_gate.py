"""Immutable selected-media handshake for a future metadata-first executor.

This module starts no process, calls no source and grants no admission itself.
The parent budget owns reservation/guard/lock decisions. Its durable-writer
callback can commit the matching permission here only after that reservation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import uuid

MAX_AUDIO_BYTES = 2_000_000_000
JOB_HEADROOM_BYTES = 240_000_000
MAX_METADATA_BYTES = 2_000_000
MAX_CONTROL_BYTES = 32_768


class GateError(ValueError):
    """A safe reason code; never contains file paths or selected URLs."""


def need(condition, reason):
    if not condition:
        raise GateError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def digest_bytes(value):
    need(isinstance(value, bytes) and 0 < len(value) <= MAX_METADATA_BYTES, 'metadata_size')
    return hashlib.sha256(value).hexdigest()


def hash_value(value):
    return isinstance(value, str) and re.fullmatch(r'[a-f0-9]{64}', value) is not None


def positive_bytes(value, maximum=MAX_AUDIO_BYTES):
    return type(value) is int and 0 < value <= maximum


def instant(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


@dataclass(frozen=True)
class Binding:
    video_id: str
    lease_id: str
    plan_sha256: str
    attempt_sha256: str
    settings_sha256: str
    worker_sha256: str
    nonce_sha256: str

    def __post_init__(self):
        need(isinstance(self.video_id, str) and re.fullmatch(r'[A-Za-z0-9_-]{11}', self.video_id), 'video_binding')
        need(isinstance(self.lease_id, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', self.lease_id), 'lease_binding')
        need(all(hash_value(value) for key, value in asdict(self).items()
                 if key not in ('video_id', 'lease_id')), 'hash_binding')


REQUEST_FIELDS = {'schema_version', 'kind', 'binding', 'selected_metadata_sha256',
                  'expected_audio_bytes', 'maximum_audio_bytes', 'deadline_epoch', 'request_sha256'}
PERMISSION_FIELDS = {'schema_version', 'kind', 'binding', 'request_sha256',
                     'selected_metadata_sha256', 'maximum_audio_bytes', 'permit_sha256',
                     'issued_at_epoch', 'deadline_epoch', 'permission_sha256'}


def make_request(binding, metadata_bytes, expected_audio_bytes, deadline_epoch,
                 *, maximum_audio_bytes=MAX_AUDIO_BYTES):
    need(isinstance(binding, Binding), 'binding_required')
    need(positive_bytes(maximum_audio_bytes), 'maximum_audio_bytes')
    need(expected_audio_bytes is None or positive_bytes(expected_audio_bytes, maximum_audio_bytes), 'selected_size')
    need(instant(deadline_epoch), 'selection_deadline')
    request = {'schema_version': 1, 'kind': 'native_selected_media_request', 'binding': asdict(binding),
               'selected_metadata_sha256': digest_bytes(metadata_bytes),
               'expected_audio_bytes': expected_audio_bytes, 'maximum_audio_bytes': maximum_audio_bytes,
               'deadline_epoch': deadline_epoch}
    request['request_sha256'] = sha(request)
    return request


def validate_request(request, binding, metadata_bytes, deadline_epoch,
                     *, maximum_audio_bytes=MAX_AUDIO_BYTES, now=None):
    need(isinstance(binding, Binding), 'binding_required')
    need(isinstance(request, dict) and set(request) == REQUEST_FIELDS, 'request_schema')
    expected = make_request(binding, metadata_bytes, request.get('expected_audio_bytes'), deadline_epoch,
                            maximum_audio_bytes=maximum_audio_bytes)
    need(encoded(request) == encoded(expected), 'request_binding_changed')
    current = time.time() if now is None else now
    need(instant(current) and current < deadline_epoch, 'media_deadline')
    return request['expected_audio_bytes'] or maximum_audio_bytes


def make_permission(request, binding, metadata_bytes, deadline_epoch, *, permit_sha256,
                    maximum_audio_bytes=MAX_AUDIO_BYTES, now=None):
    """Call only from the budget's locked, guarded reservation commit callback."""
    current = time.time() if now is None else now
    allowance = validate_request(request, binding, metadata_bytes, deadline_epoch,
                                 maximum_audio_bytes=maximum_audio_bytes, now=current)
    need(hash_value(permit_sha256), 'permit_fingerprint')
    result = {'schema_version': 1, 'kind': 'native_selected_media_permission', 'binding': asdict(binding),
              'request_sha256': request['request_sha256'],
              'selected_metadata_sha256': request['selected_metadata_sha256'],
              'maximum_audio_bytes': allowance, 'permit_sha256': permit_sha256,
              'issued_at_epoch': current, 'deadline_epoch': deadline_epoch}
    result['permission_sha256'] = sha(result)
    return result


def make_reserved_permission(request, binding, metadata_bytes, deadline_epoch, *, permit,
                             expected_owner, maximum_audio_bytes=MAX_AUDIO_BYTES, now=None):
    """Couple a budget permit to the exact request inside its commit callback.

    The budget's pinned MediaPermit is trusted code, not parsed source input.
    Structural access also supports an isolated executor importing its own
    pinned module instance. A fingerprint alone never establishes byte parity.
    """
    current = time.time() if now is None else now
    allowance = validate_request(request, binding, metadata_bytes, deadline_epoch,
                                 maximum_audio_bytes=maximum_audio_bytes, now=current)
    job = getattr(permit, 'job', None)
    selection = getattr(permit, 'selection', None)
    need(job is not None and selection is not None, 'budget_permit_required')
    need(getattr(job, 'job_id', None) == binding.video_id and
         getattr(job, 'owner', None) == expected_owner and
         getattr(job, 'lease_id', None) == binding.lease_id and
         getattr(job, 'plan_sha256', None) == binding.plan_sha256 and
         getattr(job, 'attempt_sha256', None) == binding.attempt_sha256, 'budget_job_binding')
    need(getattr(selection, 'metadata_sha256', None) == request['selected_metadata_sha256'] and
         getattr(selection, 'declared_bytes', False) == request['expected_audio_bytes'] and
         type(getattr(permit, 'audio_write_limit', None)) is int and permit.audio_write_limit == allowance and
         type(getattr(permit, 'reserved_job_bytes', None)) is int and
         permit.reserved_job_bytes == allowance + JOB_HEADROOM_BYTES, 'budget_selection_or_bytes')
    fingerprint = getattr(permit, 'fingerprint', None)
    need(callable(fingerprint), 'budget_permit_fingerprint')
    return make_permission(request, binding, metadata_bytes, deadline_epoch,
                           permit_sha256=fingerprint(), maximum_audio_bytes=maximum_audio_bytes, now=current)


def validate_permission(permission, request, binding, metadata_bytes, deadline_epoch,
                        *, maximum_audio_bytes=MAX_AUDIO_BYTES, now=None):
    current = time.time() if now is None else now
    allowance = validate_request(request, binding, metadata_bytes, deadline_epoch,
                                 maximum_audio_bytes=maximum_audio_bytes, now=current)
    need(isinstance(permission, dict) and set(permission) == PERMISSION_FIELDS, 'permission_schema')
    need(instant(permission.get('issued_at_epoch')) and permission['issued_at_epoch'] <= current,
         'permission_issued_time')
    expected = make_permission(request, binding, metadata_bytes, deadline_epoch,
                               permit_sha256=permission.get('permit_sha256'),
                               maximum_audio_bytes=maximum_audio_bytes, now=permission['issued_at_epoch'])
    need(encoded(permission) == encoded(expected) and permission['maximum_audio_bytes'] == allowance,
         'permission_binding_changed')
    return allowance


def read_control(path):
    with Path(path).open('rb') as source:
        raw = source.read(MAX_CONTROL_BYTES + 1)
    need(0 < len(raw) <= MAX_CONTROL_BYTES, 'control_size')
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, ValueError):
        raise GateError('control_invalid_json') from None


def write_once(path, value):
    """Publish a flushed control atomically, without replacing any prior grant.

    A same-directory hard link exposes only the fully written file and fails
    if the destination exists. A failed temporary write/link stays retained
    for owner reconciliation; no unsafe replace or alternate publish is tried.
    """
    raw = encoded(value)
    need(len(raw) <= MAX_CONTROL_BYTES, 'control_size')
    path = Path(path)
    pending = path.with_name(path.name + '.pending-' + uuid.uuid4().hex)
    with pending.open('xb') as output:
        need(output.write(raw) == len(raw), 'control_short_write')
        output.flush(); os.fsync(output.fileno())
    os.link(pending, path)
    # Permission is already durable and visible. Housekeeping failure cannot
    # turn it into an apparent uncommitted reservation while a child sees GO.
    retained = False
    try:
        pending.unlink()
    except OSError:
        retained = True
    return {'published': True, 'temporary_retained': retained}


def wait_permission(folder, request, binding, *, guard, job_deadline_monotonic,
                    clock=time.time, monotonic=time.monotonic, sleep=time.sleep,
                    maximum_audio_bytes=MAX_AUDIO_BYTES, poll_seconds=.1):
    """Wait for this same selection; never fetch a new URL or reuse initial GO's 60s limit.

    Caller owns the folder and writes the request before entering. Metadata is
    rehashed immediately before accepting permission. Every wake checks the
    caller's source/lease/stop/HTTP guard and both wall and monotonic deadlines.
    """
    need(isinstance(binding, Binding), 'binding_required')
    need(instant(job_deadline_monotonic) and type(poll_seconds) in (int, float)
         and math.isfinite(poll_seconds) and 0 < poll_seconds <= .5, 'wait_limits')
    folder = Path(folder)
    need(read_control(folder / 'selected-request.json') == request, 'saved_request_changed')
    deadline = request.get('deadline_epoch')
    need(instant(deadline), 'selection_deadline')
    while True:
        guard()
        now = clock()
        need(instant(now) and now < deadline and monotonic() < job_deadline_monotonic, 'media_deadline')
        permission_path = folder / 'MediaGO.json'
        if permission_path.is_file():
            permission = read_control(permission_path)
            with (folder / 'selected-metadata.info.json').open('rb') as source:
                metadata = source.read(MAX_METADATA_BYTES + 1)
            allowance = validate_permission(permission, request, binding, metadata, deadline,
                                             maximum_audio_bytes=maximum_audio_bytes, now=now)
            guard()
            need(clock() < deadline and monotonic() < job_deadline_monotonic, 'media_deadline')
            return {'maximum_audio_bytes': allowance, 'permit_sha256': permission['permit_sha256'],
                    'request_sha256': request['request_sha256']}
        remaining = min(deadline - clock(), job_deadline_monotonic - monotonic())
        need(remaining > 0, 'media_deadline')
        sleep(min(poll_seconds, remaining))
