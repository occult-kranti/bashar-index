"""Finite-cohort integration: two full-slot sources and one publisher.

No metadata-first admission, transport change, extra Drive RPC or Source retry.
The scheduler's fatal Event is the actual batch source_stop Event. A bounded
unclosed scheduler report never lets the collector owner abandon callbacks.
"""
from __future__ import annotations

from dataclasses import asdict
import re
import threading
import time

PUBLISHER_ENVELOPE = 240_000_000
MAX_OUTSTANDING = 4
MAX_SPOOL = 5_500_000_000
SAFE_CODE = re.compile(r'[A-Za-z0-9_.:-]{1,128}\Z')


def safe_code(error):
    value = getattr(error, 'kind', getattr(error, 'code', 'parallel_callback_failed'))
    return value if isinstance(value, str) and SAFE_CODE.fullmatch(value) else 'parallel_callback_failed'


class ObservedDrive:
    """Time the existing calls, preserving all arguments/results and RPC count."""
    def __init__(self, original, batch, scheduler, current):
        self.original = original; self.batch = batch
        self.scheduler = scheduler; self.current = current

    def __getattr__(self, name):
        return getattr(self.original, name)

    def _call(self, phase, function, *args, **kwargs):
        self.batch.need_unlocked_publication()
        key = getattr(self.current, 'key', None)
        with self.batch.lock: self.batch.invalidate_partition()
        self.scheduler._emit(phase+'_start', key)
        started = time.monotonic()
        try: return function(*args, **kwargs)
        finally:
            self.scheduler._emit(phase+'_finish', key, time.monotonic()-started)
            with self.batch.lock: self.batch.invalidate_partition()

    def copy_pair(self, *args, **kwargs):
        return self._call('copy', self.original.copy_pair, *args, **kwargs)

    def copy(self, *args, **kwargs):
        return self._call('copy', self.original.copy, *args, **kwargs)

    def stat(self, *args, **kwargs):
        return self._call('stat', self.original.stat, *args, **kwargs)

    def stat_batch(self, *args, **kwargs):
        return self._call('stat', self.original.stat_batch, *args, **kwargs)


class ObservedStorage:
    """Transparent module view; the mature verify-before-delete body is reused."""
    def __init__(self, original, batch, scheduler, current):
        self.original = original; self.batch = batch
        self.scheduler = scheduler; self.current = current

    def __getattr__(self, name):
        return getattr(self.original, name)

    def verify_and_delete(self, *args, **kwargs):
        self.batch.need_unlocked_publication()
        key = getattr(self.current, 'key', None)
        self.scheduler._emit('finalize_start', key)
        started = time.monotonic()
        try: return self.original.verify_and_delete(*args, **kwargs)
        finally:
            self.scheduler._emit('finalize_finish', key, time.monotonic()-started)


class BatchAdapter:
    def __init__(self, batch, module, scheduler_module):
        self.batch = batch; self.module = module; self.sm = scheduler_module
        self.current = threading.local(); self.virtual = {}
        self.original_storage = module.storage
        self.original_drive = batch.drive
        self.original_partition = batch.capacity_partition
        self.original_release = batch.release_after_reconcile
        self.scheduler = None; self.observations = []
        self.observation_lock = threading.RLock()

    def need_unlocked_publication(self):
        self.module.need(not getattr(self.batch.lock, '_is_owned', lambda:False)(),
                         'publication_holds_batch_lock')

    def observe(self, event):
        # No Source URL, command line, exception message or private RPC argument.
        with self.observation_lock:
            self.observations.append(asdict(event))

    def _timed(self, kind, function, *args, **kwargs):
        self.scheduler._emit(kind+'_start', getattr(self.current, 'key', None))
        started = time.monotonic()
        try: return function(*args, **kwargs)
        finally: self.scheduler._emit(kind+'_finish', getattr(self.current, 'key', None), time.monotonic()-started)

    def install(self):
        batch = self.batch
        batch.need_unlocked_publication = self.need_unlocked_publication
        batch.drive = ObservedDrive(self.original_drive, batch, self.scheduler, self.current)
        self.module.storage = ObservedStorage(self.original_storage, batch, self.scheduler, self.current)
        batch.capacity_partition = lambda **kwargs:self._timed('partition', self.original_partition, **kwargs)
        batch.release_after_reconcile = lambda ident:self._timed('partition_release', self.original_release, ident)

    def restore(self):
        self.batch.drive = self.original_drive
        self.module.storage = self.original_storage
        self.batch.capacity_partition = self.original_partition
        self.batch.release_after_reconcile = self.original_release

    def commitments(self, active=(), candidate=None):
        """Called under batch.lock; account even before a child reserves its slot."""
        batch = self.batch
        unseen = dict(self.virtual)
        for item in active: unseen[item.key] = item.value
        virtual = sum(item.get('max_audio_bytes', batch.s['max_asset_bytes']) + self.module.HEADROOM
                      for key, item in unseen.items() if key not in batch.live_reservations)
        amount = batch.budget._outstanding() + virtual + PUBLISHER_ENVELOPE
        if candidate is not None:
            maximum = candidate.value.get('max_audio_bytes', batch.s['max_asset_bytes'])
            self.module.need(type(maximum) is int and 0 < maximum <= batch.s['max_asset_bytes'], 'asset_deferred')
            amount += maximum + self.module.HEADROOM
        return amount

    def fits(self, amount, limit):
        batch = self.batch; m = self.module
        return (batch.capacity['inactive_spool_bytes'] + amount <= batch.s['spool_cap_bytes'] and
                batch.budget.usage() + amount <= limit - m.storage.JOURNAL_RESERVE and
                m.shutil.disk_usage(batch.root).free - amount - getattr(batch, 'others', 0) >= m.FREE)

    def source_guard(self, item):
        batch = self.batch
        with batch.lock:
            batch.guard(source=True, force=True, video_id=item.key)
            self.module.need(not batch.source_stop.is_set() and not batch.dispatch_paused.is_set(), 'batch_source_stopped')
            self.module.need(not self.module.storage.read_drive_cooldown(batch.root/'sync/drive_ingest_cooldown.json'), 'drive_cooldown')

    def before_submit(self, item, active):
        batch = self.batch
        with batch.lock:
            limit = batch.guard(source=True, force=True, video_id=item.key)
            self.module.need(not batch.source_stop.is_set() and not batch.dispatch_paused.is_set(), 'batch_source_stopped')
            self.module.need(not self.module.storage.read_drive_cooldown(batch.root/'sync/drive_ingest_cooldown.json'), 'drive_cooldown')
            self.module.need(item.key not in self.virtual and item.key not in batch.live_reservations, 'duplicate_virtual_slot')
            if not self.fits(self.commitments(active, item), limit): return False
            # Publish virtual commitment before the executor can start a callback.
            self.virtual[item.key] = item.value
            return True

    def drive_guard(self, item):
        batch = self.batch
        with batch.lock:
            limit = batch.guard(force=True)
            self.module.need(not batch.source_stop.is_set() and not batch.dispatch_paused.is_set(), 'batch_source_stopped')
            self.module.need(not self.module.storage.read_drive_cooldown(batch.root/'sync/drive_ingest_cooldown.json'), 'drive_cooldown')
            self.module.need(self.fits(self.commitments(), limit), 'publisher_envelope_capacity')

    def record_failure(self, item, error):
        # Stop synchronously before attempting any journal write that could fail.
        self.batch.source_stop.set()
        self.module.storage.journal(self.batch.batch_journal,
            {'schema_version':1, 'profile':self.module.worker.PROFILE, 'video_id':item.key,
             'status':'held', 'error_class':safe_code(error), 'plan_sha256':self.batch.plan_sha,
             'diagnostic':self.module.exception_diagnostic(error)})

    def acquire(self, item):
        batch = self.batch
        self.current.key = item.key
        try:
            self.module.need(not batch.source_stop.is_set(), 'batch_source_stopped')
            if item.key in getattr(batch, '_parallel_prepared', {}):
                result = batch._parallel_prepared[item.key]
            else: result = batch.execute_child(item.value)
            self.module.need(isinstance(result, dict) and result.get('status') in {'local_complete','held'}, 'parallel_source_result')
            fatal = batch.source_stop.is_set()
            return self.sm.Acquisition('ready' if result['status']=='local_complete' else 'held', result,
                reason='batch_source_stopped' if fatal else None, fatal=fatal)
        except BaseException as error:
            self.record_failure(item, error)
            return self.sm.Acquisition('retained', reason=safe_code(error), fatal=True)
        finally:
            # execute_child has ingested final HTTP before releasing its real
            # slot; no Source outcome is moved into the publication thread.
            with batch.lock: self.virtual.pop(item.key, None)
            self.current.key = None

    def publish(self, item, acquisition, trace):
        batch = self.batch; m = self.module
        self.current.key = item.key
        try:
            self.need_unlocked_publication()
            m.need(not batch.source_stop.is_set(), 'batch_source_stopped')
            done = batch.publish(item.value, acquisition.value)
            saved_path = batch.jobs/item.key/'canonical-record.json'
            m.need(m.storage.receipt_complete(done, item.value, batch.s['remote']) and
                   saved_path.exists() and m.read(saved_path)==done, 'canonical_receipt_incomplete')
            trace.mark('receipt_verified')
            return self.sm.Publication(True, {'canonical_record_sha256':m.digest(saved_path),
                'audio_drive_id':done['drive_id'], 'metadata_drive_id':done['metadata']['drive_id']})
        except BaseException as error:
            self.record_failure(item, error)
            return self.sm.Publication(False, reason=safe_code(error))
        finally: self.current.key = None

    def stop_owned(self, reason, active):
        # The existing execute_child guards observe this same Event and close
        # each exact OwnedJob in finally. No unowned kill or source retry.
        self.batch.source_stop.set()
        with self.batch.lock: self.batch.administrative_hold('parallel scheduler held; Root review required')

    def persist_owner(self, state, report=None):
        self.module.write(self.batch.jobs/'parallel-owner-status.json',
            {'schema_version':1, 'profile':self.module.worker.PROFILE, 'status':state,
             'callbacks_closed':self.scheduler.callbacks_closed(),
             'owned_jobs_or_resources_closed':False, 'lease_or_reservation_released':False,
             'scheduler_report_state':None if report is None else report.state})

    def wait_owned_callbacks(self):
        # The generic scheduler returns a bounded unclosed report; this owner
        # retains its collector lock until callbacks actually return. A stuck
        # callback therefore remains owned and cannot admit the next frame.
        while not self.scheduler.callbacks_closed():
            self.batch.source_stop.set()
            time.sleep(.05)
        self.batch.parallel_callback_closure_proven = True


def report_value(report, observations):
    return {'schema_version':1, 'state':report.state, 'reason':report.reason,
        'scheduler_submissions_not_source_attempts':report.submitted,
        'stop_callback_called':report.stop_callback_called, 'stop_callback_failed':report.stop_callback_failed,
        'max_source_futures':report.max_source_futures, 'max_outstanding':report.max_outstanding,
        'outcomes':[{'video_id':x.item.key, 'state':x.state, 'reason':x.reason,
                     'publication_verified':bool(x.publication and x.publication.verified)} for x in report.outcomes],
        'timings':observations, 'lease_or_reservation_released':False}


def run_batch(batch, module, scheduler_module):
    m = module; sm = scheduler_module
    m.need(batch.s['spool_cap_bytes'] <= MAX_SPOOL, 'parallel_spool_ceiling')
    batch.spool.mkdir(exist_ok=True)
    counts = {'verified':0, 'skipped':0, 'held':0, 'pending':0, 'inflight':0}
    batch.parallel_callback_closure_proven = False
    with m.storage.exclusive_lock(batch.root):
        batch.jobs.mkdir(parents=True, exist_ok=True)
        limit = batch.guard(force=True, force_inventory=True)
        batch.budget = m.SlotBudget(batch.root, limit, batch.s['max_asset_bytes'], m.FREE, cached=False)
        previous = m.storage.load_state(batch.state_path)
        pending = []; batch._parallel_prepared = {}
        for item in batch.items:
            ident = item['video_id']; folder = batch.jobs/ident
            if m.storage.receipt_complete(previous.get(ident, {}), item, batch.s['remote']):
                batch.finalize_handoff(folder, previous[ident]); counts['skipped'] += 1
            elif folder.exists():
                result = m.read(folder/'result.json') if (folder/'result.json').exists() else {}
                if result.get('status')=='local_complete' or (folder/'canonical-record.json').exists():
                    batch._parallel_prepared[ident] = result
                    pending.append(sm.WorkItem(ident,item))
                else: counts['held'] += 1
            else: pending.append(sm.WorkItem(ident,item))
        if not pending:
            batch.parallel_callback_closure_proven = True
            m.write(batch.jobs/'summary.json', dict(schema_version=1, profile=m.worker.PROFILE,
                plan_sha256=batch.plan_sha, parallel_state='complete', parallel_callbacks_closed=True, **counts))
            return dict(counts, parallel_state='complete', parallel_callbacks_closed=True)
        adapter = BatchAdapter(batch, m, sm)
        adapter.scheduler = sm.ParallelScheduler(pending, execute_source=adapter.acquire, publish=adapter.publish,
            before_submit=adapter.before_submit, source_guard=adapter.source_guard, drive_guard=adapter.drive_guard,
            stop_owned=adapter.stop_owned, stop_requested=lambda:batch.source_stop.is_set() or
                batch.dispatch_paused.is_set() or batch.stop_path.exists(), observe=adapter.observe,
            source_workers=batch.s['workers'], max_outstanding=MAX_OUTSTANDING,
            drain_timeout_seconds=30., fatal_event=batch.source_stop)
        adapter.install()
        report = None
        try:
            report = adapter.scheduler.run()
            if not adapter.scheduler.callbacks_closed(): adapter.persist_owner('unclosed_callbacks_retained', report)
            adapter.wait_owned_callbacks()
            adapter.persist_owner('callbacks_closed_owned_job_audits_still_required', report)
            for outcome in report.outcomes:
                if outcome.state=='verified': counts['verified'] += 1
                elif outcome.state=='pending': counts['pending'] += 1
                elif outcome.state=='inflight': counts['inflight'] += 1
                else: counts['held'] += 1
            m.write(batch.jobs/'parallel-scheduler-report.json', report_value(report, adapter.observations))
            m.write(batch.jobs/'summary.json', dict(schema_version=1, profile=m.worker.PROFILE,
                plan_sha256=batch.plan_sha, parallel_state=report.state,
                parallel_callbacks_closed=batch.parallel_callback_closure_proven, **counts))
            return dict(counts, parallel_state=report.state, parallel_callbacks_closed=batch.parallel_callback_closure_proven)
        except BaseException:
            batch.source_stop.set()
            raise
        finally:
            # Includes report/control write failures: never restore/leave the
            # collector lock while any actual callback remains outstanding.
            adapter.wait_owned_callbacks()
            adapter.restore()
