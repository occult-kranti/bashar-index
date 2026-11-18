"""Isolated metadata-first admission ledger; no filesystem, source or process I/O.

This is a future integration component, not an executor or an execution grant.
Its inventory and guard callbacks must share the controller's dispatch lock and
resource ownership checks. A selection's declared size is an enforced write
ceiling, never evidence that the declaration or the completed audio is correct.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re
from threading import RLock
from typing import Callable

GB = 1_000_000_000
AUDIO_CAP = 2 * GB
JOB_HEADROOM = 240_000_000
PUBLISH_HEADROOM = JOB_HEADROOM
JOURNAL_RESERVE = 64 * 1024 * 1024
MANAGED_CAP = 16 * GB
OWNER_CAP = 20 * GB
SPARE = 2 * GB
SPOOL_CAP = 5_500_000_000
_SHA = re.compile(r'[0-9a-f]{64}\Z')
_ID = re.compile(r'[A-Za-z0-9_.:-]{1,128}\Z')
_ACTIVE = frozenset({'bootstrap', 'waiting_media', 'media_reserved', 'media', 'go_uncertain'})
_MEDIA = frozenset({'media_reserved', 'media', 'go_uncertain'})
_PENDING = frozenset({'ready', 'publishing'})


class BudgetError(ValueError):
    """Invalid binding, violated write bound or administrative uncertainty."""


class Deferred(BudgetError):
    """Local capacity/backpressure: retain the same job and selection; no GO."""


def _need(value, code):
    if not value:
        raise BudgetError(code)


def _bytes(value):
    return type(value) is int and 0 <= value <= 2**63 - 1


def _sha(value):
    return isinstance(value, str) and _SHA.fullmatch(value) is not None


@dataclass(frozen=True)
class JobKey:
    job_id: str
    owner: str
    lease_id: str
    plan_sha256: str
    attempt_sha256: str

    def __post_init__(self):
        _need(all(isinstance(v, str) and _ID.fullmatch(v) for v in
                  (self.job_id, self.owner, self.lease_id)), 'invalid_job_identity')
        _need(_sha(self.plan_sha256) and _sha(self.attempt_sha256), 'invalid_job_pins')


@dataclass(frozen=True)
class Selection:
    metadata_sha256: str
    format_sha256: str
    declared_bytes: int | None

    def __post_init__(self):
        _need(_sha(self.metadata_sha256) and _sha(self.format_sha256), 'invalid_selection_pins')
        _need(self.declared_bytes is None or
              (_bytes(self.declared_bytes) and 0 < self.declared_bytes <= AUDIO_CAP), 'invalid_selected_size')


@dataclass(frozen=True)
class Limits:
    max_children: int = 4
    max_bootstraps: int = 2
    max_media: int = 2
    max_pending_pairs: int = 2
    max_pending_bytes: int = 500_000_000

    def __post_init__(self):
        _need(type(self.max_children) is int and 2 <= self.max_children <= 4, 'child_limit')
        _need(type(self.max_bootstraps) is int and 1 <= self.max_bootstraps <= min(2, self.max_children), 'bootstrap_limit')
        _need(type(self.max_media) is int and 1 <= self.max_media <= self.max_children, 'media_limit')
        _need(type(self.max_pending_pairs) is int and 1 <= self.max_pending_pairs <= 20, 'publication_limit')
        _need(_bytes(self.max_pending_bytes) and 0 < self.max_pending_bytes <= SPOOL_CAP, 'publication_bytes')


@dataclass(frozen=True)
class Inventory:
    """One same-lock partition: active job folders are completely excluded.

    All other managed/spool files, including completed and retained owned files,
    are in the inactive totals. included_jobs binds their measured folder sizes.
    Other growth excludes this ledger's exact matching source reservation.
    Physical free is conservative: full active envelopes are subtracted again,
    rather than mixing child sizes sampled at different write instants.
    """
    inactive_managed_bytes: int
    inactive_spool_bytes: int
    other_growth_bytes: int
    owner_other_bytes: int
    physical_free_bytes: int
    included_jobs: tuple[tuple[str, int], ...] = ()

    def __post_init__(self):
        _need(all(_bytes(v) for v in (self.inactive_managed_bytes, self.inactive_spool_bytes,
              self.other_growth_bytes, self.owner_other_bytes, self.physical_free_bytes)), 'invalid_inventory')
        _need(self.inactive_spool_bytes <= self.inactive_managed_bytes, 'invalid_partition')
        _need(isinstance(self.included_jobs, tuple) and all(isinstance(row, tuple) and len(row) == 2 and
              isinstance(row[0], str) and _ID.fullmatch(row[0]) and _bytes(row[1])
              for row in self.included_jobs), 'invalid_inactive_job_inventory')
        _need(len(dict(self.included_jobs)) == len(self.included_jobs) and
              sum(size for _, size in self.included_jobs) <= self.inactive_spool_bytes, 'invalid_inactive_job_totals')


@dataclass(frozen=True)
class Projection:
    active_reserved_bytes: int
    publisher_growth_bytes: int
    managed_bytes: int
    owner_bytes: int
    spool_bytes: int
    physical_free_after_commit: int

    def violation(self):
        if self.spool_bytes > SPOOL_CAP: return 'spool_capacity'
        if self.managed_bytes > MANAGED_CAP: return 'managed_capacity'
        if self.owner_bytes > OWNER_CAP - SPARE: return 'owner_capacity'
        if self.physical_free_after_commit < SPARE: return 'physical_spare'
        return None


@dataclass(frozen=True)
class MediaPermit:
    job: JobKey
    selection: Selection
    audio_write_limit: int
    reserved_job_bytes: int

    def __post_init__(self):
        _need(isinstance(self.job, JobKey) and isinstance(self.selection, Selection), 'invalid_media_permit')
        expected = self.selection.declared_bytes if self.selection.declared_bytes is not None else AUDIO_CAP
        _need(type(self.audio_write_limit) is int and self.audio_write_limit == expected and
              type(self.reserved_job_bytes) is int and self.reserved_job_bytes == expected + JOB_HEADROOM,
              'invalid_media_permit_bytes')

    def fingerprint(self):
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True, separators=(',', ':'),
                                         ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


@dataclass(frozen=True)
class ClosedJob:
    job: JobKey
    audit_sha256: str
    owned_processes_gone: bool
    source_history_committed: bool
    audio_bytes: int
    job_bytes: int
    strict_quality_sha256: str | None = None

    def __post_init__(self):
        _need(_sha(self.audit_sha256) and _bytes(self.audio_bytes) and _bytes(self.job_bytes) and
              self.audio_bytes <= self.job_bytes, 'invalid_closure')
        _need(self.strict_quality_sha256 is None or _sha(self.strict_quality_sha256), 'invalid_quality_pin')


@dataclass(frozen=True)
class ArchiveProof:
    job: JobKey
    paired_receipt_sha256: str
    cleanup_audit_sha256: str
    remaining_job_bytes: int

    def __post_init__(self):
        _need(_sha(self.paired_receipt_sha256) and _sha(self.cleanup_audit_sha256) and
              _bytes(self.remaining_job_bytes), 'invalid_archive_proof')


@dataclass(frozen=True)
class _Job:
    key: JobKey
    stage: str = 'bootstrap'
    charge: int = JOB_HEADROOM
    selection: Selection | None = None
    permit: MediaPermit | None = None
    retained_bytes: int = 0


class AdmissionBudget:
    """Atomic in-process ledger for one immutable, externally admitted scope.

    snapshot(excluded_job_ids) and fresh_guard() execute under dispatch_lock.
    The adapter must use that SAME lock for real GO writes, HTTP ingestion and
    partition changes. No callback may launch source work or perform uploads.
    A failed/ambiguous durable GO write is one-shot and holds all new dispatch.
    """
    def __init__(self, allowed_jobs: tuple[JobKey, ...], *, limits: Limits,
                 snapshot: Callable[[frozenset[str]], Inventory], fresh_guard: Callable[[], None],
                 dispatch_lock=None):
        _need(isinstance(allowed_jobs, tuple) and bool(allowed_jobs) and
              all(isinstance(job, JobKey) for job in allowed_jobs), 'immutable_job_scope_required')
        self._allowed = {job.job_id: job for job in allowed_jobs}
        _need(len(self._allowed) == len(allowed_jobs) and len({(j.owner, j.lease_id) for j in allowed_jobs}) == 1,
              'duplicate_or_mixed_owner_scope')
        _need(isinstance(limits, Limits) and callable(snapshot) and callable(fresh_guard), 'invalid_budget_adapter')
        self.limits = limits
        self._snapshot = snapshot; self._guard = fresh_guard
        self.dispatch_lock = dispatch_lock if dispatch_lock is not None else RLock()
        self._jobs = {}; self._hold = None

    def _key(self, job):
        _need(isinstance(job, JobKey) and self._allowed.get(job.job_id) == job, 'job_binding_mismatch')

    def _job(self, job):
        self._key(job)
        _need(job.job_id in self._jobs, 'job_not_admitted')
        return self._jobs[job.job_id]

    def _dispatch(self):
        _need(self._hold is None, 'administrative_hold')
        self._guard()  # External exact lease, immutable pins, HTTP/STOP and expiry checks.

    def _backpressure(self):
        pending = [j for j in self._jobs.values() if j.stage in _PENDING]
        if len(pending) >= self.limits.max_pending_pairs or sum(j.retained_bytes for j in pending) >= self.limits.max_pending_bytes:
            raise Deferred('publication_backpressure')

    def _projection(self, jobs):
        active = frozenset(k for k, j in jobs.items() if j.stage in _ACTIVE)
        inventory = self._snapshot(active)
        _need(isinstance(inventory, Inventory), 'inventory_type')
        observed = dict(inventory.included_jobs)
        _need(not active.intersection(observed) and observed.keys() <= self._allowed.keys(), 'inventory_job_partition')
        for key, job in jobs.items():
            if job.stage not in _ACTIVE:
                _need(observed.get(key, -1) >= job.retained_bytes, 'closed_job_not_reconciled')
        outstanding = sum(j.charge for j in jobs.values() if j.stage in _ACTIVE)
        # Keep one publisher's future control/metadata growth available BEFORE
        # source admission, so a full ready queue cannot deadlock publication.
        committed = outstanding + PUBLISH_HEADROOM
        managed = inventory.inactive_managed_bytes + committed + inventory.other_growth_bytes + JOURNAL_RESERVE
        return Projection(outstanding, PUBLISH_HEADROOM, managed, managed + inventory.owner_other_bytes,
                          inventory.inactive_spool_bytes + committed,
                          inventory.physical_free_bytes - committed - inventory.other_growth_bytes - JOURNAL_RESERVE)

    def _fits(self, jobs):
        projection = self._projection(jobs)
        if projection.violation(): raise Deferred(projection.violation())
        return projection

    def admit_bootstrap(self, job: JobKey):
        with self.dispatch_lock:
            self._key(job); self._dispatch(); self._backpressure()
            _need(job.job_id not in self._jobs, 'job_already_spent')
            active = [j for j in self._jobs.values() if j.stage in _ACTIVE]
            if len(active) >= self.limits.max_children: raise Deferred('child_slots')
            if sum(j.stage in {'bootstrap', 'waiting_media'} for j in active) >= self.limits.max_bootstraps:
                raise Deferred('bootstrap_slots')
            proposed = dict(self._jobs, **{job.job_id: _Job(job)})
            projection = self._fits(proposed)
            self._jobs = proposed
            return projection

    def bind_selection(self, job: JobKey, selection: Selection):
        with self.dispatch_lock:
            current = self._job(job); self._dispatch()
            _need(isinstance(selection, Selection) and current.stage in {'bootstrap', 'waiting_media'}, 'selection_stage')
            _need(current.selection is None or current.selection == selection, 'selection_changed')
            self._fits(self._jobs)
            self._jobs[job.job_id] = replace(current, stage='waiting_media', selection=selection)

    def reserve_media(self, job: JobKey):
        with self.dispatch_lock:
            current = self._job(job); self._dispatch(); self._backpressure()
            _need(current.stage == 'waiting_media' and current.selection is not None, 'media_reservation_stage')
            if sum(j.stage in _MEDIA for j in self._jobs.values()) >= self.limits.max_media:
                raise Deferred('media_slots')
            size = current.selection.declared_bytes if current.selection.declared_bytes is not None else AUDIO_CAP
            permit = MediaPermit(job, current.selection, size, size + JOB_HEADROOM)
            proposed = dict(self._jobs, **{job.job_id: replace(current, stage='media_reserved', charge=permit.reserved_job_bytes, permit=permit)})
            self._fits(proposed)
            self._jobs = proposed
            return permit

    def commit_media_go(self, job: JobKey, permit: MediaPermit, durable_writer: Callable[[MediaPermit], None]):
        with self.dispatch_lock:
            current = self._job(job); self._dispatch(); self._backpressure()
            _need(current.stage == 'media_reserved' and current.permit == permit and callable(durable_writer), 'media_go_binding')
            self._fits(self._jobs)
            self._jobs[job.job_id] = replace(current, stage='go_uncertain')
            try:
                durable_writer(permit)  # Exact immutable permit; ack before ANY selected-media request.
            except BaseException:
                self._hold = 'media_go_commit_failed'
                raise BudgetError('media_go_commit_failed') from None
            self._jobs[job.job_id] = replace(current, stage='media')
            return permit

    def settle_owned(self, proof: ClosedJob):
        """Reconcile the closed folder into inactive bytes BEFORE releasing its envelope."""
        with self.dispatch_lock:
            _need(isinstance(proof, ClosedJob), 'closure_type')
            current = self._job(proof.job)
            _need(current.stage in _ACTIVE, 'closure_stage')
            audio_limit = current.permit.audio_write_limit if current.permit else 0
            if (proof.owned_processes_gone is not True or proof.source_history_committed is not True or
                    (proof.audio_bytes > 0 and current.stage not in {'media', 'go_uncertain'}) or
                    proof.job_bytes > current.charge or proof.audio_bytes > audio_limit):
                self._jobs[proof.job.job_id] = replace(current, charge=max(current.charge, proof.job_bytes))
                self._hold = 'closure_or_write_bound_unproven'
                raise BudgetError('closure_or_write_bound_unproven')
            ready = proof.strict_quality_sha256 is not None
            _need(not ready or (current.stage == 'media' and proof.audio_bytes > 0), 'quality_without_media')
            proposed = dict(self._jobs, **{proof.job.job_id: replace(current, stage='ready' if ready else 'retained',
                charge=0, retained_bytes=proof.job_bytes)})
            projection = self._projection(proposed)
            self._jobs = proposed
            if projection.violation(): self._hold = projection.violation()
            return projection

    def begin_publication(self, job: JobKey):
        with self.dispatch_lock:
            current = self._job(job)
            _need(current.stage == 'ready', 'publication_stage')
            if any(j.stage == 'publishing' for j in self._jobs.values()): raise Deferred('single_publisher')
            self._fits(self._jobs)
            self._jobs[job.job_id] = replace(current, stage='publishing')

    def finish_publication(self, proof: ArchiveProof):
        with self.dispatch_lock:
            _need(isinstance(proof, ArchiveProof), 'archive_type')
            current = self._job(proof.job)
            _need(current.stage == 'publishing' and proof.remaining_job_bytes <= current.retained_bytes, 'archive_stage')
            proposed = dict(self._jobs, **{proof.job.job_id: replace(current, stage='archived', retained_bytes=proof.remaining_job_bytes)})
            projection = self._projection(proposed)
            self._jobs = proposed
            if projection.violation(): self._hold = projection.violation()
            return projection

    def view(self):
        with self.dispatch_lock:
            return {'administrative_hold': self._hold,
                    'jobs': {key: {'stage': j.stage, 'reserved_bytes': j.charge,
                                  'retained_bytes': j.retained_bytes} for key, j in self._jobs.items()}}


def check_audio_write(permit: MediaPermit, job: JobKey, selection_sha256: str,
                      written_bytes: int, chunk_bytes: int):
    """Child-side check immediately BEFORE write; no top-up or size correction.

    The adapter must first authenticate this exact durable MediaGO permit. This
    helper does not establish ownership, durable acknowledgement or source access.
    """
    _need(isinstance(permit, MediaPermit) and permit.job == job and
          permit.selection.metadata_sha256 == selection_sha256, 'write_binding')
    _need(_bytes(written_bytes) and _bytes(chunk_bytes), 'invalid_write_size')
    expected = permit.selection.declared_bytes if permit.selection.declared_bytes is not None else AUDIO_CAP
    _need(permit.audio_write_limit == expected and permit.reserved_job_bytes == expected + JOB_HEADROOM,
          'write_permit_changed')
    _need(written_bytes + chunk_bytes <= AUDIO_CAP, 'audio_hard_cap')
    _need(written_bytes + chunk_bytes <= permit.audio_write_limit, 'selected_write_cap')
    return written_bytes + chunk_bytes
