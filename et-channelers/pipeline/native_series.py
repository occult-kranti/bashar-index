"""Disabled planning and durable orchestration for at most three native frames.

The runtime adapter owns NativeBatch leases, process drainage, live resource
measurement, and exact source-attempt evidence. This module neither creates
that adapter nor clears controls. Importing or planning cannot start a source
request. A separately pinned root authorization is required by Controller.
"""
from __future__ import annotations

import csv
from contextlib import contextmanager
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import time

try:
    from . import drive_ingest as storage, native_http_policy as http_policy
except ImportError:
    import drive_ingest as storage
    import native_http_policy as http_policy

PROFILE = 'native-series-v1'
MAX_FRAMES = 3
FRAME_SIZE = 20
MANAGED = 16_000_000_000
SPARE = 2_000_000_000
SPOOL = 6_000_000_000
MIN_SPOOL = 5_500_000_000
ASR = 1_000_000_000
SHA = re.compile(r'[a-f0-9]{64}')
VIDEO = re.compile(r'[A-Za-z0-9_-]{11}')


class Held(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def need(value, code):
    if not value:
        raise Held(code)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode('utf-8')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read(path):
    path = Path(path)
    need(path.stat().st_size <= 20_000_000, 'document_limit')
    return json.loads(path.read_bytes())


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + '.tmp')
    with part.open('wb') as output:
        output.write(encoded(value)); output.flush(); os.fsync(output.fileno())
    os.replace(part, path)


@contextmanager
def series_lock(path):
    """Independent of collector/ASR locks; a second controller cannot race."""
    target = Path(path).with_suffix('.lock')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('a+b') as handle:
        if handle.tell() == 0: handle.write(b'0'); handle.flush()
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            try: msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError: raise Held('series_locked') from None
            try: yield
            finally:
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try: fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError: raise Held('series_locked') from None
            try: yield
            finally: fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def checked(pin_value):
    need(isinstance(pin_value, dict) and SHA.fullmatch(str(pin_value.get('sha256', ''))), 'pin_shape')
    path = Path(pin_value['path'])
    need(not storage.is_link(path), 'pin_link')
    raw = path.read_bytes()
    need(sha(raw) == pin_value['sha256'] and len(raw) == pin_value['bytes'], 'pin_changed')
    return raw


def prepare(directory, queue_path, items, *, evidence_pins, seed_pin, history_pins):
    """Freeze a disabled latest20 proposal, never an authorization.

    The caller selects candidates using its saved availability/attempt audit.
    Every selected row must be byte-equivalent to a row in this queue snapshot.
    Prior selection alone is not source spend; reeligible selected rows carry
    an explicit launch-evidence proof in selection_evidence.
    """
    directory = Path(directory)
    need(not directory.exists(), 'proposal_exists')
    queue_pin = pin(queue_path)
    raw = checked(queue_pin)
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    by_id = {}
    for row in rows:
        ident = row.get('video_id', '')
        need(ident not in by_id, 'queue_duplicate')
        by_id[ident] = row
    need(1 <= len(items) <= MAX_FRAMES * FRAME_SIZE, 'series_size')
    seen = set()
    for item in items:
        ident = item.get('video_id', '')
        row = item.get('queue_row', {})
        need(VIDEO.fullmatch(ident) and ident not in seen and by_id.get(ident) == row, 'queue_target')
        need(row.get('tab') == 'videos' and str(row.get('listing_rank', '')).isdigit() and
             0 <= int(row['listing_rank']) < 20, 'latest20_only')
        need(item.get('channel_dir') == row['channel_dir'] and item.get('tab') == row['tab'] and
             item.get('video_url') == 'https://www.youtube.com/watch?v=' + ident and
             item.get('queue_row_sha256') == sha(encoded(row)), 'row_binding')
        duration = item.get('duration_seconds')
        need(duration is None or type(duration) in (int, float) and math.isfinite(duration) and duration > 0,
             'duration_invalid')
        selection = item.get('selection_evidence', {})
        need(selection.get('status') in {'no_prior_selection', 'selected_proven_never_started'}, 'selection_evidence')
        if selection['status'] == 'selected_proven_never_started':
            need(selection.get('source_attempted') is False and bool(selection.get('proofs')), 'launch_evidence_missing')
            documents = [json.loads(checked(proof)) for proof in selection['proofs']]
            need(any(document.get('video_id') == ident and document.get('source_attempted') is False and
                     document.get('owned_processes_gone') is True and document.get('go_was_issued') is False and
                     document.get('source_requests') == 0 and document.get('launch_evidence_complete') is True
                     for document in documents), 'launch_evidence_missing')
        seen.add(ident)
    need(bool(evidence_pins) and bool(history_pins), 'history_missing')
    for proof in [seed_pin, *evidence_pins, *history_pins]: checked(proof)
    directory.mkdir(parents=True)
    frames = []
    for offset in range(0, len(items), FRAME_SIZE):
        frame = {'schema_version': 1, 'scope': 'latest20', 'queue_snapshot': queue_pin,
                 'items': items[offset:offset + FRAME_SIZE]}
        path = directory / ('frame-' + str(len(frames) + 1) + '-' + sha(encoded(frame)) + '.json')
        atomic(path, frame)
        frames.append({'index': len(frames), 'plan': pin(path),
                       'video_ids': [x['video_id'] for x in frame['items']], 'settings': None,
                       'runtime_binding_state': 'pending_owner_review'})
    proposal = {'schema_version': 1, 'profile': PROFILE, 'execute_allowed': False, 'scope': 'latest20',
        'queue_snapshot': queue_pin, 'proposed_allowed_video_ids': [x['video_id'] for x in items],
        'frames': frames, 'http_policy_seed': seed_pin, 'evidence': evidence_pins, 'preserved_controls': history_pins,
        'limits': {'max_frames': MAX_FRAMES, 'max_items_per_frame': FRAME_SIZE, 'workers': 2,
                   'native_spool_bytes': SPOOL, 'asr_staging_bytes': ASR, 'managed_bytes': MANAGED,
                   'disk_spare_bytes': SPARE},
        'requires': ['root_frozen_allowlist', 'exact_runtime_and_frame_settings_pins',
                     'same_v4_ledger', 'drained_previous_frame', 'live_resource_and_asr_capacity'],
        'no_automatic_retry': True, 'latest50_authorized': False}
    target = directory / ('proposal-' + sha(encoded(proposal)) + '.json')
    atomic(target, proposal)
    return pin(target)


def validate_authorization(proposal_pin, authorization, now):
    proposal = json.loads(checked(proposal_pin))
    need(proposal.get('profile') == PROFILE and proposal.get('scope') == 'latest20' and
         proposal.get('execute_allowed') is False and proposal.get('latest50_authorized') is False, 'proposal_scope')
    need(authorization.get('schema_version') == 1 and authorization.get('authorized') is True and
         authorization.get('owner') == 'root' and authorization.get('proposal_sha256') == proposal_pin['sha256'],
         'series_not_authorized')
    deadline = authorization.get('expires_at_epoch')
    need(type(deadline) in (int, float) and math.isfinite(deadline) and now < deadline, 'authorization_expired')
    issued = authorization.get('issued_at_epoch')
    need(type(issued) in (int, float) and math.isfinite(issued) and issued <= now and
         0 < deadline - issued <= 43_200, 'authorization_window')
    ids = proposal['proposed_allowed_video_ids']
    need(len(ids) == len(set(ids)) <= 60 and authorization.get('allowed_video_ids') == ids, 'allowlist_expansion')
    need(authorization.get('http_policy_seed_sha256') == proposal['http_policy_seed']['sha256'], 'ledger_seed_changed')
    bindings = authorization.get('frame_bindings', [])
    need(len(bindings) == len(proposal['frames']) <= MAX_FRAMES and bool(authorization.get('runtime_pins')), 'runtime_unbound')
    for value in authorization['runtime_pins'] + proposal['preserved_controls'] + proposal['evidence'] + [proposal['queue_snapshot'], proposal['http_policy_seed']]:
        checked(value)
    for frame, binding in zip(proposal['frames'], bindings):
        need(binding.get('plan_sha256') == frame['plan']['sha256'], 'frame_binding')
        plan = json.loads(checked(frame['plan'])); settings = json.loads(checked(binding['settings']))
        lease = json.loads(checked(binding['lease']))
        need([x['video_id'] for x in plan['items']] == frame['video_ids'] and 1 <= len(plan['items']) <= FRAME_SIZE, 'frame_target')
        need(settings.get('plan_path') == frame['plan']['path'] and settings.get('workers') == 2 and
             type(settings.get('spool_cap_bytes')) is int and MIN_SPOOL <= settings['spool_cap_bytes'] <= SPOOL and
             settings.get('profile') == 'stock_headful_wpc_native_batch_v4', 'settings_scope')
        draft = (lease.get('state') == 'draft' and lease.get('authorized') is False and
                 lease.get('source_scope_authorized') is False and lease.get('root_admission_required') is True and
                 lease.get('expires_at_epoch') is None and type(lease.get('max_frame_seconds')) is int and
                 1 <= lease['max_frame_seconds'] <= 43_200)
        admitted = (lease.get('authorized') is True and lease.get('source_scope_authorized') is True and
                    type(lease.get('expires_at_epoch')) in (int, float) and lease['expires_at_epoch'] <= deadline)
        need(settings['http_policy_seed']['sha256'] == proposal['http_policy_seed']['sha256'] and
             lease.get('settings_sha256') == binding['settings']['sha256'] and
             lease.get('plan_sha256') == frame['plan']['sha256'] and lease.get('owner') == 'root' and
             (draft or admitted), 'lease_binding')
        for value in settings['code_pins'] + settings['preserved_controls']: checked(value)
        review = json.loads(checked(settings['historical_http_review']))
        need(set(review['allowed_video_ids']) == set(frame['video_ids']), 'frame_review_scope')
    return proposal


def fresh_snapshot(snapshot, now, spool_bytes=SPOOL, asr_cap_bytes=ASR):
    """Runtime measurements are evidence, never inferred from a stale PID file."""
    stamp = snapshot.get('observed_at_epoch')
    need(type(stamp) in (int, float) and 0 <= now - stamp <= 15, 'stale_runtime_snapshot')
    need(snapshot.get('owned_native_processes') == 0 and snapshot.get('active_frame') is None, 'frame_not_drained')
    need(snapshot.get('stop_present') is False, 'series_stopped')
    need(snapshot.get('drive_hold') is False and snapshot.get('source_hold') is False, 'provider_hold')
    attempted = snapshot.get('attempted_or_uncertain_ids')
    need(isinstance(attempted, list) and all(isinstance(v, str) and VIDEO.fullmatch(v) for v in attempted) and
         len(attempted) == len(set(attempted)) and snapshot.get('attempt_history_complete') is True and
         SHA.fullmatch(str(snapshot.get('attempt_history_sha256', ''))), 'attempt_history_incomplete')
    for key in ('managed_bytes', 'other_growth_reservations_bytes', 'disk_free_bytes', 'asr_staging_bytes', 'asr_pairs'):
        need(type(snapshot.get(key)) is int and snapshot[key] >= 0, 'resource_evidence_missing')
    need(type(spool_bytes) is int and MIN_SPOOL <= spool_bytes <= SPOOL, 'settings_scope')
    need(snapshot['managed_bytes'] + snapshot['other_growth_reservations_bytes'] + spool_bytes <= MANAGED and
         snapshot['disk_free_bytes'] >= SPARE, 'resource_backpressure')
    need(type(asr_cap_bytes) is int and 0 < asr_cap_bytes <= ASR and snapshot.get('asr_cap_bytes') == asr_cap_bytes,
         'asr_capacity_binding')
    need(snapshot.get('asr_accepting') is True and snapshot['asr_staging_bytes'] < asr_cap_bytes and
         snapshot['asr_pairs'] < 3, 'asr_backpressure')


def complete_pair(record, item, remote):
    if not storage.receipt_complete(record, item, remote): return False
    metadata = record['metadata']
    return bool(record.get('video_id') == item['video_id'] and
        record.get('drive_id') != metadata.get('drive_id') and all(
            type(proof.get('bytes')) is int and proof['bytes'] > 0 and
            re.fullmatch(r'[a-f0-9]{32}', str(proof.get('md5', ''))) and
            SHA.fullmatch(str(proof.get('sha256', ''))) for proof in (record, metadata)))


class Controller:
    """Single owner, called under the runtime's cross-process series lock.

    Runtime protocol: snapshot(frame), activate(binding), run(binding),
    drain(binding). run returns no authority; drain returns terminal per-item
    evidence. No source restart occurs for a persisted dispatch-intent frame.
    An explicit reconcile call can consume existing terminal evidence only.
    """
    def __init__(self, proposal_pin, authorization_pin, state_path, runtime, *, clock=time.time):
        self.proposal_pin, self.authorization_pin = proposal_pin, authorization_pin
        self.authorization = json.loads(checked(authorization_pin))
        self.clock, self.runtime, self.path = clock, runtime, Path(state_path)
        self.proposal = validate_authorization(proposal_pin, self.authorization, clock())
        need(runtime.pins == self.authorization['runtime_pins'], 'runtime_identity')
        self.state = read(self.path) if self.path.exists() else {
            'schema_version': 1, 'profile': PROFILE, 'proposal_sha256': proposal_pin['sha256'],
            'authorization_sha256': authorization_pin['sha256'], 'frames': {}, 'source_spent': {},
            'uncertain': {}, 'never_started': {}, 'status': 'pending'}
        need(self.state.get('proposal_sha256') == proposal_pin['sha256'] and
             self.state.get('authorization_sha256') == authorization_pin['sha256'], 'state_binding')

    def save(self):
        atomic(self.path, self.state)

    def guard(self, frame):
        self.authorization = json.loads(checked(self.authorization_pin))
        validate_authorization(self.proposal_pin, self.authorization, self.clock())
        snapshot = self.runtime.snapshot(frame)
        binding = self.authorization['frame_bindings'][frame['index']]
        settings = json.loads(checked(binding['settings']))
        fresh_snapshot(snapshot, self.clock(), settings['spool_cap_bytes'], settings.get('asr_handoff', {}).get('cap_bytes', ASR))
        envelope = snapshot.get('http_policy', {})
        need(envelope.get('seed_sha256') == self.proposal['http_policy_seed']['sha256'], 'ledger_seed_changed')
        seed = json.loads(checked(self.proposal['http_policy_seed']))
        need(all(envelope.get('state', {}).get('events', {}).get(k) == v for k, v in seed['events'].items()), 'ledger_history_changed')
        review_pin = settings['historical_http_review']
        review = dict(json.loads(checked(review_pin)), review_sha256=review_pin['sha256'])
        plan = json.loads(checked(frame['plan']))
        canonical = snapshot.get('canonical_receipts', {})
        pending = []
        for item in plan['items']:
            ident = item['video_id']
            if complete_pair(canonical.get(ident, {}), item, settings['remote']): continue
            need(ident not in self.state['source_spent'] and ident not in self.state['uncertain'], 'source_retry_denied')
            need(ident not in snapshot.get('attempted_or_uncertain_ids', []), 'source_attempt_history')
            scope = http_policy.status(envelope['state'], self.clock(), historical_review=review, candidate_video_id=ident)
            need(scope['dispatch_allowed'] and not scope['item_quarantined'], 'http_policy_hold')
            pending.append(ident)
        return pending

    def finish(self, frame, evidence):
        """Exact terminal launch evidence distinguishes spent from unstarted."""
        need(evidence.get('owned_native_processes') == 0 and evidence.get('drained') is True, 'frame_not_drained')
        need(evidence.get('plan_sha256') == frame['plan']['sha256'], 'drain_plan')
        outcomes = evidence.get('outcomes', {})
        need(set(outcomes) == set(frame['video_ids']), 'drain_outcomes')
        settings = json.loads(checked(self.authorization['frame_bindings'][frame['index']]['settings']))
        items = {x['video_id']: x for x in json.loads(checked(frame['plan']))['items']}
        for ident, value in outcomes.items():
            proof = value.get('evidence')
            need(proof is not None, 'attempt_evidence_missing'); checked(proof)
            document = json.loads(checked(proof))
            need(document.get('video_id') == ident and document.get('plan_sha256') == frame['plan']['sha256'] and
                 document.get('owned_processes_gone') is True, 'terminal_evidence_binding')
            status = value.get('status')
            need(status in {'canonical_verified', 'attempt_spent', 'proven_never_started', 'uncertain'}, 'outcome_status')
            attempted = value.get('source_attempted')
            need(type(attempted) is bool or attempted is None, 'attempt_classification')
            if attempted is True:
                need(document.get('source_attempted') is True and (document.get('go_was_issued') is True or
                     type(document.get('source_requests')) is int and document['source_requests'] > 0), 'spent_unproven')
            if status == 'canonical_verified':
                need(complete_pair(document.get('canonical_receipt', {}), items[ident], settings['remote']), 'canonical_proof_missing')
            if status == 'proven_never_started':
                need(attempted is False and document.get('video_id') == ident and
                     document.get('plan_sha256') == frame['plan']['sha256'] and
                     document.get('source_attempted') is False and document.get('owned_processes_gone') is True and
                     document.get('go_was_issued') is False and document.get('source_requests') == 0 and
                     document.get('launch_evidence_complete') is True, 'never_started_unproven')
                self.state['never_started'][ident] = proof
                self.state['uncertain'].pop(ident, None)
            elif attempted is True:
                self.state['source_spent'][ident] = proof
                self.state['uncertain'].pop(ident, None)
            elif status == 'canonical_verified':
                # The runtime proves the exact durable canonical pair; this is
                # not a claim that this series itself made a source request.
                self.state['uncertain'].pop(ident, None)
            else:
                self.state['uncertain'][ident] = proof
        local_hold = evidence.get('local_reconciliation_required') is True
        final = {'phase': 'drained_local_hold' if local_hold else 'drained',
                 'outcomes': outcomes, 'evidence_sha256': sha(encoded(evidence))}
        self.state['frames'][str(frame['index'])] = final
        self.state['status'] = 'held_local_reconciliation_required' if local_hold else 'pending'
        self.save()

    def reconcile(self):
        """No activate/run call, even when a crash occurred before activation."""
        with series_lock(self.path):
            if self.path.exists(): self.state = read(self.path)
            need(self.state['authorization_sha256'] == self.authorization_pin['sha256'], 'state_binding')
            for frame in self.proposal['frames']:
                state = self.state['frames'].get(str(frame['index']), {})
                if state.get('phase') in {'dispatch_intent', 'drained_local_hold'}:
                    self.finish(frame, self.runtime.drain(self.authorization['frame_bindings'][frame['index']]))
        return self.state

    def run(self):
        with series_lock(self.path):
            if self.path.exists(): self.state = read(self.path)
            need(self.state['authorization_sha256'] == self.authorization_pin['sha256'], 'state_binding')
            return self._run_locked()

    def _run_locked(self):
        for frame in self.proposal['frames']:
            previous = self.state['frames'].get(str(frame['index']), {})
            if previous.get('phase') == 'drained': continue
            need(not previous, 'interrupted_frame_requires_reconciliation')
            pending = self.guard(frame)
            # Reservation intent is NOT proof of a source attempt. It merely
            # prevents restart from silently launching an uncertain frame.
            self.state['frames'][str(frame['index'])] = {'phase': 'dispatch_intent', 'reserved_ids': pending}
            self.state['status'] = 'running'; self.save()
            binding = self.authorization['frame_bindings'][frame['index']]
            try:
                self.runtime.activate(binding)
                self.runtime.run(binding)
                self.finish(frame, self.runtime.drain(binding))
                need(self.state['frames'][str(frame['index'])]['phase'] == 'drained', 'local_reconciliation_required')
            except BaseException:
                self.state['status'] = 'held_reconciliation_required'; self.save(); raise
        holds = any(value['status'] != 'canonical_verified' for frame in self.state['frames'].values()
                    for value in frame.get('outcomes', {}).values())
        self.state['status'] = 'finished_with_holds' if holds else 'finished'
        self.save()
        return self.state
