"""Source-free bounded source/publication scheduler for a future executor.

The caller owns byte admission, source policy, actual archive verification and
owned-process closure. This module neither starts an executor nor interprets a
worker's acquisition status as an archive receipt. The finite-cohort adapter imports this module only under its own grant. Callbacks must be bounded and cooperate with the external stop signal.
"""
from __future__ import annotations

from collections import deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
import math
import re
from threading import Event, RLock
import time
from typing import Any

_CODE = re.compile(r'[A-Za-z0-9_.:-]{1,128}\Z')
_PHASES = frozenset({'copy_start', 'copy_finish', 'stat_start', 'stat_finish',
                     'receipt_verified', 'cleanup_start', 'cleanup_finish'})


class SchedulerError(ValueError):
    pass


def _need(value, code):
    if not value: raise SchedulerError(code)


def _code(value):
    return isinstance(value, str) and _CODE.fullmatch(value) is not None


@dataclass(frozen=True)
class WorkItem:
    key: str
    value: Any

    def __post_init__(self):
        _need(_code(self.key), 'invalid_item_key')


@dataclass(frozen=True)
class Acquisition:
    state: str  # ready, held or retained; never verified.
    value: Any = None
    reason: str | None = None
    fatal: bool = False

    def __post_init__(self):
        _need(self.state in {'ready', 'held', 'retained'} and type(self.fatal) is bool,
              'invalid_acquisition_state')
        _need(self.state != 'ready' or self.value is not None, 'ready_payload_required')
        _need(self.reason is None or _code(self.reason), 'invalid_acquisition_reason')


@dataclass(frozen=True)
class Publication:
    verified: bool
    proof: Any = None
    reason: str | None = None

    def __post_init__(self):
        _need(type(self.verified) is bool and (not self.verified or self.proof is not None), 'publication_proof_required')
        _need(self.reason is None or _code(self.reason), 'invalid_publication_reason')


@dataclass(frozen=True)
class JobOutcome:
    item: WorkItem
    state: str  # verified, held, retained, pending or inflight.
    acquisition: Acquisition | None = None
    publication: Publication | None = None
    reason: str | None = None


@dataclass(frozen=True)
class Timing:
    sequence: int
    kind: str
    key: str | None
    monotonic_seconds: float
    duration_seconds: float | None = None


@dataclass(frozen=True)
class Report:
    state: str  # complete, deferred, held or unclosed.
    reason: str | None
    outcomes: tuple[JobOutcome, ...]
    timings: tuple[Timing, ...]
    submitted: int  # Scheduler submissions, NOT proven source attempts.
    stop_callback_called: bool
    stop_callback_failed: bool
    max_source_futures: int
    max_outstanding: int


@dataclass(frozen=True)
class _Completed:
    acquisition: Acquisition
    finished_at: float


@dataclass(frozen=True)
class _Ready:
    item: WorkItem
    acquisition: Acquisition
    ready_at: float


class PublisherTrace:
    """Instrument the actual copy/stat/receipt boundaries in the caller's adapter."""
    def __init__(self, scheduler, key):
        self._scheduler = scheduler; self._key = key

    def mark(self, phase):
        _need(phase in _PHASES, 'unknown_publication_phase')
        self._scheduler._emit(phase, self._key)


class ParallelScheduler:
    """One finite ordered run: <=2 source futures, one publisher, <=6 outstanding.

    before_submit(item, active_items) must atomically check bytes including
    virtual commitments for submitted children not yet visible to the byte
    ledger. False means local capacity deferral. If there is no owned work or
    publication able to release space, return pending items immediately.

    Source/publish/guard/observer failures stop new submissions and new
    publications. stop_owned(reason, active_items) is called ONCE; in-flight
    callbacks may drain, but ready/unpublished outputs are preserved. A drain
    deadline returns explicit inflight outcomes, never fictional closure.
    """
    def __init__(self, items, *, execute_source, publish, before_submit,
                 source_guard, drive_guard, stop_owned, stop_requested=lambda:False,
                 observe=None, source_workers=2, max_outstanding=4,
                 poll_seconds=.02, drain_timeout_seconds=30., max_timing_events=32768,
                 fatal_event=None):
        self.items = tuple(items)
        _need(bool(self.items) and len(self.items) <= 1280 and all(isinstance(x, WorkItem) for x in self.items), 'finite_work_scope')
        _need(len({x.key for x in self.items}) == len(self.items), 'duplicate_work_item')
        _need(type(source_workers) is int and 1 <= source_workers <= 2, 'source_worker_limit')
        _need(type(max_outstanding) is int and source_workers <= max_outstanding <= 6, 'outstanding_limit')
        _need(all(callable(x) for x in (execute_source, publish, before_submit, source_guard,
              drive_guard, stop_owned, stop_requested)) and (observe is None or callable(observe)), 'callback_required')
        _need(type(poll_seconds) in (int, float) and math.isfinite(poll_seconds) and 0 < poll_seconds <= .5,
              'poll_limit')
        _need(type(drain_timeout_seconds) in (int, float) and math.isfinite(drain_timeout_seconds) and
              0 < drain_timeout_seconds <= 1800, 'drain_limit')
        _need(type(max_timing_events) is int and 32 <= max_timing_events <= 32768, 'timing_limit')
        self.execute_source = execute_source; self.publish = publish; self.before_submit = before_submit
        self.source_guard = source_guard; self.drive_guard = drive_guard
        self.stop_owned = stop_owned; self.stop_requested = stop_requested; self.observe = observe
        self.source_workers = source_workers; self.max_outstanding_limit = max_outstanding
        self.poll_seconds = poll_seconds; self.drain_timeout_seconds = drain_timeout_seconds
        self.max_timing_events = max_timing_events
        _need(fatal_event is None or isinstance(fatal_event, Event), 'fatal_event_contract')
        self._lock = RLock(); self._event_lock = RLock(); self._failure_lock = RLock()
        self._fatal = fatal_event if fatal_event is not None else Event()
        self._owned_futures = []
        self._reason = None; self._timings = []; self._ran = False

    def _fail(self, reason):
        # Publish the reason BEFORE the flag. A separate lock lets a publisher
        # stop dispatch even while the manager is inside its byte callback.
        with self._failure_lock:
            if self._reason is None: self._reason = reason
            self._fatal.set()

    def callbacks_closed(self):
        """Callback closure only; the caller must separately prove owned jobs."""
        return all(future.done() for future in self._owned_futures)

    def _emit(self, kind, key=None, duration=None):
        with self._event_lock:
            if len(self._timings) >= self.max_timing_events:
                self._fail('timing_capacity')
                return
            event = Timing(len(self._timings)+1, kind, key, time.monotonic(), duration)
            self._timings.append(event)
        if self.observe:
            try: self.observe(event)
            except BaseException: self._fail('timing_observer_failed')

    def _source(self, item):
        self._emit('source_start', item.key)
        try:
            _need(not self._fatal.is_set(), 'source_held_before_callback')
            self.source_guard(item)
            _need(not self._fatal.is_set(), 'source_held_after_guard')
            result = self.execute_source(item)
            _need(isinstance(result, Acquisition), 'source_result_contract')
        except BaseException:
            result = Acquisition('retained', reason='source_callback_failed', fatal=True)
        if result.fatal: self._fail(result.reason or 'source_fatal')
        finished = time.monotonic()
        self._emit('source_finish', item.key)
        return _Completed(result, finished)

    def _publication(self, ready):
        item = ready.item
        try:
            self.drive_guard(item)
            self._emit('publication_start', item.key, max(0., time.monotonic()-ready.ready_at))
            if self._fatal.is_set():
                result = Publication(False, reason='publication_held_before_callback')
            else:
                result = self.publish(item, ready.acquisition, PublisherTrace(self, item.key))
                _need(isinstance(result, Publication), 'publication_result_contract')
                if not result.verified: self._fail(result.reason or 'publication_unverified')
        except BaseException:
            result = Publication(False, reason='publication_callback_failed')
            self._fail('publication_callback_failed')
        self._emit('publication_finish', item.key)
        return result

    def run(self):
        with self._lock:
            _need(not self._ran, 'scheduler_one_shot')
            self._ran = True
        pending = deque(self.items); active = {}; ready = deque(); publisher = None
        outcomes = {}; submitted = 0; peak_source = 0; peak_outstanding = 0
        stop_called = False; stop_failed = False; drain_until = None; deferred = False; idle_at = None
        source_pool = ThreadPoolExecutor(max_workers=self.source_workers, thread_name_prefix='source-prototype')
        publisher_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='publisher-prototype')

        def preserve_ready(reason):
            while ready:
                value = ready.popleft()
                outcomes[value.item.key] = JobOutcome(value.item, 'retained', value.acquisition, reason=reason)

        try:
            while pending or active or ready or publisher:
                progressed = False
                try:
                    if self.stop_requested(): self._fail('external_stop')
                except BaseException: self._fail('stop_guard_failed')

                # Consume publication failures BEFORE any next admission.
                if publisher and publisher[0].done():
                    future, value = publisher
                    try: result = future.result()
                    except BaseException:
                        result = Publication(False, reason='publication_future_failed')
                        self._fail('publication_future_failed')
                    outcomes[value.item.key] = JobOutcome(value.item, 'verified' if result.verified else 'retained',
                        value.acquisition, result, result.reason)
                    publisher = None; progressed = True

                for future in [future for future in active if future.done()]:
                    item = active.pop(future)
                    if future.cancelled():
                        outcomes[item.key] = JobOutcome(item, 'pending', reason='cancelled_before_callback')
                    else:
                        try: completion = future.result()
                        except BaseException:
                            completion = _Completed(Acquisition('retained', reason='source_future_failed', fatal=True), time.monotonic())
                            self._fail('source_future_failed')
                        acquired = completion.acquisition
                        if acquired.state == 'ready':
                            ready.append(_Ready(item, acquired, completion.finished_at))
                            self._emit('ready', item.key)
                        else:
                            outcomes[item.key] = JobOutcome(item, acquired.state, acquired, reason=acquired.reason)
                    progressed = True

                if self._fatal.is_set():
                    if not stop_called:
                        stop_called = True; drain_until = time.monotonic()+self.drain_timeout_seconds
                        self._emit('stop_requested')
                        try: self.stop_owned(self._reason or 'fatal', tuple(active.values()))
                        except BaseException:
                            stop_failed = True; self._emit('stop_callback_failed')
                            self._fail('stop_callback_failed')
                        for future in active: future.cancel()  # Running owned work must cooperate with stop_owned.
                    preserve_ready('stopped_before_publication')
                    if not active and not publisher: break
                    if time.monotonic() >= drain_until:
                        for item in active.values():
                            outcomes[item.key] = JobOutcome(item, 'inflight', reason='owned_drain_deadline')
                        if publisher:
                            value = publisher[1]
                            outcomes[value.item.key] = JobOutcome(value.item, 'inflight', value.acquisition,
                                                                reason='publisher_drain_deadline')
                        break
                else:
                    # Only this manager submits source. The byte callback sees
                    # every active future, including virtual not-yet-visible reservations.
                    while pending and len(active) < self.source_workers:
                        outstanding = len(active)+len(ready)+(publisher is not None)
                        if outstanding >= self.max_outstanding_limit: break
                        item = pending[0]
                        try:
                            with self._lock:
                                if self._fatal.is_set(): break
                                self.source_guard(item)
                                allowed = self.before_submit(item, tuple(active.values()))
                                _need(type(allowed) is bool, 'admission_decision_required')
                                if not allowed or self._fatal.is_set(): break
                                future = source_pool.submit(self._source, item)
                                self._owned_futures.append(future)
                                active[future] = item; pending.popleft(); submitted += 1
                            self._emit('source_submitted', item.key)
                            peak_source = max(peak_source, len(active))
                            peak_outstanding = max(peak_outstanding, len(active)+len(ready)+(publisher is not None))
                            progressed = True
                        except BaseException:
                            self._fail('source_admission_failed')
                            break

                    if not self._fatal.is_set() and publisher is None and ready:
                        value = ready.popleft()
                        publication_future = publisher_pool.submit(self._publication, value)
                        self._owned_futures.append(publication_future)
                        publisher = (publication_future, value)
                        peak_outstanding = max(peak_outstanding, len(active)+len(ready)+1)
                        progressed = True

                    # A byte ceiling with no in-flight work cannot release itself.
                    # Preserve the ordered unstarted tail instead of spinning forever.
                    if pending and not active and not ready and publisher is None and not self._fatal.is_set():
                        deferred = True
                        self._emit('capacity_deferred', pending[0].key)
                        break

                if progressed and idle_at is not None:
                    self._emit('manager_idle_finish', duration=time.monotonic()-idle_at); idle_at = None
                if not progressed:
                    if idle_at is None:
                        idle_at = time.monotonic(); self._emit('manager_idle_start')
                    futures = tuple(active)+((publisher[0],) if publisher else ())
                    if futures: wait(futures, timeout=self.poll_seconds, return_when=FIRST_COMPLETED)

        except BaseException:
            self._fail('manager_failed')
            preserve_ready('manager_failed_before_publication')
            if not stop_called:
                stop_called = True
                try: self.stop_owned('manager_failed', tuple(active.values()))
                except BaseException:
                    stop_failed = True; self._emit('stop_callback_failed')
            for future, item in active.items():
                future.cancel()
                outcomes[item.key] = JobOutcome(item, 'inflight', reason='manager_failed_drain_unproven')
            if publisher:
                value = publisher[1]
                outcomes[value.item.key] = JobOutcome(value.item, 'inflight', value.acquisition,
                                                     reason='manager_failed_drain_unproven')
        finally:
            # Never claim arbitrary callback threads can be killed. The caller's
            # bounded owned-process supervisor remains responsible for closure.
            source_pool.shutdown(wait=False, cancel_futures=True)
            publisher_pool.shutdown(wait=False, cancel_futures=True)
            if idle_at is not None: self._emit('manager_idle_finish', duration=time.monotonic()-idle_at)

        for item in pending:
            outcomes[item.key] = JobOutcome(item, 'pending', reason='not_submitted')
        _need(set(outcomes) == {item.key for item in self.items}, 'outcome_partition')
        state = 'unclosed' if any(x.state == 'inflight' for x in outcomes.values()) else (
                'held' if self._fatal.is_set() else 'deferred' if deferred else 'complete')
        return Report(state, self._reason if self._fatal.is_set() else 'capacity_deferred' if deferred else None,
                      tuple(outcomes[item.key] for item in self.items), tuple(self._timings), submitted,
                      stop_called, stop_failed, peak_source, peak_outstanding)
