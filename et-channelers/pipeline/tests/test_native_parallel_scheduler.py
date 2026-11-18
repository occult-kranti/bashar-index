"""Controlled source-free events expose manager/publication overlap and failure retention."""
from threading import current_thread, Event, Lock, Thread
import time
import unittest
from unittest.mock import patch

from pipeline.native_bulk import parallel_scheduler as scheduler


def items(count):
    return tuple(scheduler.WorkItem(str(index), {'fixture': index}) for index in range(count))


def acquired(item):
    return scheduler.Acquisition('ready', value={'owned_output': item.key})


def published(item, value, trace):
    trace.mark('copy_start'); trace.mark('copy_finish')
    trace.mark('stat_start'); trace.mark('stat_finish'); trace.mark('receipt_verified')
    return scheduler.Publication(True, proof={'paired_receipt': item.key})


def make(work, source=acquired, publisher=published, **changes):
    options = dict(execute_source=source, publish=publisher, before_submit=lambda item, active:True,
        source_guard=lambda item:None, drive_guard=lambda item:None,
        stop_owned=lambda reason, active:None, drain_timeout_seconds=.5, poll_seconds=.005)
    options.update(changes)
    return scheduler.ParallelScheduler(work, **options)


class Running:
    def __init__(self, runner):
        self.report = None; self.error = None
        def run():
            try: self.report = runner.run()
            except BaseException as error: self.error = error
        self.thread = Thread(target=run)
        self.thread.start()

    def finish(self, test):
        self.thread.join(3)
        test.assertFalse(self.thread.is_alive(), 'manager did not finish')
        if self.error: raise self.error
        return self.report


class ParallelSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))

    def test_fourth_source_starts_while_first_publisher_is_blocked(self):
        pub_started = Event(); release_pub = Event(); release_second = Event(); fourth = Event()
        admissions = []
        def source(item):
            if item.key == '1': self.assertTrue(release_second.wait(2))
            if item.key == '2': self.assertTrue(pub_started.wait(2))
            if item.key == '3':
                self.assertTrue(pub_started.is_set()); self.assertFalse(release_pub.is_set()); fourth.set()
            return acquired(item)
        def publisher(item, result, trace):
            if item.key == '0':
                trace.mark('copy_start'); pub_started.set(); self.assertTrue(release_pub.wait(2)); trace.mark('copy_finish')
            return scheduler.Publication(True, proof={'paired_receipts': item.key})
        def admission(item, active):
            admissions.append((item.key, tuple(x.key for x in active)))
            return True
        running = Running(make(items(6), source, publisher, before_submit=admission))
        try:
            self.assertTrue(fourth.wait(2), 'publication blocked source refilling')
            self.assertTrue(running.thread.is_alive())
        finally:
            release_pub.set(); release_second.set()
        report = running.finish(self)
        self.assertEqual('complete', report.state)
        self.assertTrue(all(x.state == 'verified' for x in report.outcomes))
        self.assertLessEqual(report.max_source_futures, 2); self.assertLessEqual(report.max_outstanding, 4)
        timing = {(event.kind,event.key):event.sequence for event in report.timings}
        self.assertLess(timing[('source_start','3')], timing[('publication_finish','0')])
        self.assertTrue(any(key == '1' and '0' in active for key, active in admissions))

    def test_outstanding_ceiling_and_one_publisher_hold_under_fast_sources(self):
        release = Event(); fourth = Event(); fifth = Event(); started = []; lock = Lock()
        publisher_count = 0; publisher_peak = 0
        def source(item):
            with lock:
                started.append(item.key)
                if len(started) == 4: fourth.set()
                if len(started) == 5: fifth.set()
            return acquired(item)
        def publisher(item, result, trace):
            nonlocal publisher_count, publisher_peak
            with lock:
                publisher_count += 1; publisher_peak = max(publisher_peak,publisher_count)
            try:
                if item.key == '0': self.assertTrue(release.wait(2))
                return scheduler.Publication(True, proof={'pair':item.key})
            finally:
                with lock: publisher_count -= 1
        running = Running(make(items(12), source, publisher, max_outstanding=4))
        try:
            self.assertTrue(fourth.wait(2))
            self.assertFalse(fifth.wait(.03), 'ready files bypassed the outstanding ceiling')
        finally: release.set()
        report = running.finish(self)
        self.assertEqual(1, publisher_peak)
        self.assertEqual(4, report.max_outstanding)
        self.assertEqual(12, sum(x.state == 'verified' for x in report.outcomes))

    def test_six_outstanding_is_a_bounded_parameter_not_unlimited_prefetch(self):
        release = Event(); sixth = Event(); seventh = Event(); count = [0]; lock = Lock()
        def source(item):
            with lock:
                count[0] += 1
                if count[0] == 6: sixth.set()
                if count[0] == 7: seventh.set()
            return acquired(item)
        def publisher(item, result, trace):
            if item.key == '0': self.assertTrue(release.wait(2))
            return scheduler.Publication(True, proof={'pair':item.key})
        running = Running(make(items(10), source, publisher, max_outstanding=6))
        try:
            self.assertTrue(sixth.wait(2)); self.assertFalse(seventh.wait(.03))
        finally: release.set()
        report = running.finish(self)
        self.assertEqual(6, report.max_outstanding)

    def test_publisher_failure_stops_admission_and_retains_every_unpublished_output(self):
        pub_started = Event(); fail_pub = Event(); owned_stop = Event(); fourth_ready = Event()
        started = []; uploads = []; stops = []
        def source(item):
            started.append(item.key)
            if item.key == '1': self.assertTrue(owned_stop.wait(2))
            if item.key in {'2','3'}: self.assertTrue(pub_started.wait(2))
            if item.key == '3': fourth_ready.set()
            return acquired(item)
        def publisher(item, result, trace):
            uploads.append(item.key); trace.mark('copy_start'); pub_started.set()
            self.assertTrue(fail_pub.wait(2))
            raise OSError('private signed URL/token/path must not reach diagnostics')
        def stop(reason, active): stops.append((reason, tuple(x.key for x in active))); owned_stop.set()
        running = Running(make(items(7), source, publisher, stop_owned=stop))
        try:
            self.assertTrue(fourth_ready.wait(2)); fail_pub.set()
        finally:
            fail_pub.set(); owned_stop.set()
        report = running.finish(self)
        self.assertEqual('held', report.state)
        self.assertEqual('publication_callback_failed', report.reason)
        self.assertEqual(['0'], uploads); self.assertEqual(1,len(stops))
        by_key = {x.item.key:x for x in report.outcomes}
        for key in ['0','1','2','3']:
            self.assertEqual('retained', by_key[key].state)
            self.assertIsNotNone(by_key[key].acquisition.value)
        for key in ['4','5','6']: self.assertEqual('pending',by_key[key].state)
        self.assertEqual(4, report.submitted)
        self.assertNotIn('private signed', repr(report))

    def test_source_fatal_signals_owned_stop_and_does_not_publish_ready_siblings(self):
        second = Event(); stop = Event(); uploads = []; stops = []
        def source(item):
            if item.key == '0':
                self.assertTrue(second.wait(2))
                return scheduler.Acquisition('held', reason='global_source_hold', fatal=True)
            second.set(); self.assertTrue(stop.wait(2)); return acquired(item)
        def request_stop(reason, active): stops.append(reason); stop.set()
        report = make(items(5), source, lambda *args:uploads.append(args), stop_owned=request_stop).run()
        by_key = {x.item.key:x for x in report.outcomes}
        self.assertEqual('held', report.state); self.assertEqual(['global_source_hold'],stops)
        self.assertEqual('held',by_key['0'].state); self.assertEqual('retained',by_key['1'].state)
        self.assertEqual('pending',by_key['2'].state); self.assertFalse(uploads)

    def test_fatal_during_worker_guard_prevents_source_callback_after_guard_returns(self):
        guarded = Event(); release = Event(); stopped = Event(); source_calls = []
        def guard(item):
            if item.key == '1' and current_thread().name.startswith('source-prototype'):
                guarded.set(); self.assertTrue(release.wait(2))
        def source(item):
            source_calls.append(item.key)
            self.assertTrue(guarded.wait(2))
            return scheduler.Acquisition('held',reason='source_global_hold',fatal=True)
        def stop(reason, active): stopped.set(); release.set()
        try:
            report = make(items(2),source,source_guard=guard,stop_owned=stop).run()
        finally: release.set()
        self.assertTrue(stopped.is_set()); self.assertEqual(['0'],source_calls)
        self.assertEqual('held',report.state); self.assertEqual('retained',report.outcomes[1].state)

    def test_initial_capacity_false_returns_pending_without_waiting_or_spending_work(self):
        calls = []
        runner = make(items(3), lambda x:calls.append('source'), lambda *x:calls.append('publish'),
                      before_submit=lambda item, active:False, stop_owned=lambda *x:calls.append('stop'))
        started = time.monotonic(); report = runner.run()
        self.assertLess(time.monotonic()-started, .5)
        self.assertEqual('deferred', report.state); self.assertEqual(0,report.submitted)
        self.assertTrue(all(x.state == 'pending' for x in report.outcomes)); self.assertFalse(calls)

    def test_capacity_rechecks_after_publication_releases_bytes(self):
        permit = Event(); published_first = Event(); admissions = []
        def admission(item, active):
            admissions.append((item.key,len(active)))
            return item.key == '0' or permit.is_set()
        def publisher(item, result, trace):
            permit.set(); published_first.set()
            return scheduler.Publication(True, proof={'exact_pair':item.key})
        report = make(items(3), publisher=publisher, before_submit=admission).run()
        self.assertTrue(published_first.is_set()); self.assertEqual('complete',report.state)
        self.assertEqual(3,report.submitted)
        self.assertGreater(sum(key == '1' for key,_ in admissions),1)

    def test_held_item_is_explicit_and_does_not_become_verified_or_fatal(self):
        def source(item):
            return scheduler.Acquisition('held', reason='format_unavailable') if item.key == '0' else acquired(item)
        report = make(items(2),source).run()
        self.assertEqual('complete',report.state)
        self.assertEqual(['held','verified'],[x.state for x in report.outcomes])
        self.assertFalse(report.stop_callback_called)

    def test_missing_publisher_proof_is_retained_and_stops_more_publications(self):
        uploads = []
        def publisher(item, result, trace):
            uploads.append(item.key)
            return scheduler.Publication(True)  # Constructor rejects inferred verification.
        report = make(items(4), publisher=publisher).run()
        self.assertEqual('held',report.state); self.assertFalse(any(x.state == 'verified' for x in report.outcomes))
        self.assertEqual(1,len(uploads))
        self.assertTrue(all(x.state in {'retained','pending'} for x in report.outcomes))

    def test_drive_guard_runs_before_upload_and_source_guard_before_submission(self):
        source_calls = []; upload_calls = []
        def drive_guard(item): raise RuntimeError('drive hold')
        report = make(items(2), lambda item:(source_calls.append(item.key) or acquired(item)),
            lambda *args:upload_calls.append(args), drive_guard=drive_guard).run()
        self.assertEqual('held',report.state); self.assertFalse(upload_calls); self.assertTrue(source_calls)
        source_calls.clear()
        report = make(items(2), lambda item:source_calls.append(item.key),
                      source_guard=lambda item:(_ for _ in ()).throw(RuntimeError('source hold'))).run()
        self.assertEqual('held',report.state); self.assertFalse(source_calls)
        self.assertTrue(all(x.state == 'pending' for x in report.outcomes))

    def test_uncooperative_owned_callback_returns_unclosed_not_fictional_drain(self):
        second = Event(); release = Event()
        def source(item):
            if item.key == '0':
                self.assertTrue(second.wait(2))
                return scheduler.Acquisition('held',reason='source_fatal',fatal=True)
            second.set(); self.assertTrue(release.wait(2)); return acquired(item)
        try:
            report = make(items(2), source, drain_timeout_seconds=.03).run()
            self.assertEqual('unclosed',report.state)
            self.assertEqual('inflight',report.outcomes[1].state)
            self.assertEqual('owned_drain_deadline',report.outcomes[1].reason)
        finally: release.set()

    def test_stop_callback_failure_is_visible_without_replay(self):
        count = []
        def stop(*args): count.append(1); raise RuntimeError('failure')
        report = make(items(1), lambda item:scheduler.Acquisition('held', reason='fatal', fatal=True), stop_owned=stop).run()
        self.assertEqual(1,len(count)); self.assertTrue(report.stop_callback_called); self.assertTrue(report.stop_callback_failed)

    def test_actual_publication_phase_marks_and_ready_wait_are_recorded(self):
        report = make(items(2)).run()
        kinds = {x.kind for x in report.timings}
        self.assertTrue({'ready','publication_start','copy_start','copy_finish','stat_start','stat_finish',
                         'receipt_verified','publication_finish','source_submitted'} <= kinds)
        starts = [x for x in report.timings if x.kind == 'publication_start']
        self.assertTrue(all(x.duration_seconds >= 0 for x in starts))
        self.assertEqual(list(range(1,len(report.timings)+1)),[x.sequence for x in report.timings])

    def test_timing_observer_failure_cannot_discard_completed_payload(self):
        def observer(event):
            if event.kind == 'publication_start': raise RuntimeError('private')
        report = make(items(3), observe=observer).run()
        self.assertEqual('held',report.state); self.assertEqual('timing_observer_failed',report.reason)
        self.assertTrue(any(x.acquisition is not None and x.acquisition.value is not None and x.state == 'retained'
                            for x in report.outcomes))

    def test_inputs_are_finite_unique_bounded_and_scheduler_is_one_shot(self):
        for changes in [dict(source_workers=3),dict(max_outstanding=7),dict(drain_timeout_seconds=0)]:
            with self.subTest(changes=changes),self.assertRaises(scheduler.SchedulerError): make(items(1),**changes)
        with self.assertRaises(scheduler.SchedulerError): make((items(1)[0],items(1)[0]))
        runner = make(items(1)); runner.run()
        with self.assertRaisesRegex(scheduler.SchedulerError,'one_shot'): runner.run()


if __name__ == '__main__': unittest.main()
