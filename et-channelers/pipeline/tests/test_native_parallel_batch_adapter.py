"""Real NativeBatch.run adapter; synthetic bounded callbacks, no external I/O."""
from contextlib import contextmanager
import ast
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from threading import Event, Lock, RLock, Thread
import time
import types
import unittest
from unittest.mock import patch

from pipeline.native_bulk import native_bulk_controller as controller
m = controller.batch_module
adapter = m.parallel_adapter; sm = m.parallel_scheduler


class FakeBudget:
    def __init__(self, env): self.env = env; self.active = {}; self.cap = 16_000_000_000
    def usage(self): return self.env.inactive
    def _outstanding(self): return sum(x['bytes'] for x in self.active.values())


class Fixture:
    def __init__(self, root, count=6, body=20_000_000):
        self.root = root; self.inactive = 0; self.body = body
        self.limit = 16_000_000_000; self.physical = 30_000_000_000
        self.source = None; self.publication = None; self.events = []; self.started = []
        self.source_peak = self.pub_peak = self.sources = self.pubs = 0
        self.collector_owned = False; self.collector_entries = 0
        self.current_lock = Lock(); self.copy_calls = self.stat_calls = 0
        b = m.NativeBatch.__new__(m.NativeBatch); self.batch = b
        b.root = root; b.spool = root/'spool'; b.jobs = b.spool/'jobs'
        b.state_path = root/'sync/state.jsonl'; b.batch_journal = root/'sync/batch.jsonl'
        b.stop_path = root/'sync/STOP'; b.plan_sha = 'a'*64; b.handoff = None
        b.s = {'workers':2,'max_asset_bytes':2_000_000_000,'spool_cap_bytes':5_500_000_000,'remote':'fixture:archive'}
        b.items = [{'video_id':'t'+str(i).zfill(10),'channel_dir':'fixture','tab':'Videos'} for i in range(count)]
        b.lock = RLock(); b.source_stop = Event(); b.dispatch_paused = Event(); b.live_reservations = {}
        b.budget = None; b.adaptive_pause_until = 0
        b.capacity_partition = self.partition; b.release_after_reconcile = self.release
        b.invalidate_partition = lambda:None; b.finalize_handoff = lambda *a:None
        b.guard = self.guard; b.execute_child = self.execute; b.publish = self.publish
        b.drive = types.SimpleNamespace(copy_pair=self.copy, copy=self.copy,stat=self.stat,stat_batch=self.stat)
        b.root.joinpath('sync').mkdir()

    def partition(self, **kwargs):
        return {'inactive_private_bytes':self.inactive,'inactive_spool_bytes':self.inactive}

    def guard(self, *, source=False, **kwargs):
        if source and self.batch.source_stop.is_set(): raise m.worker.Held('batch_source_stopped')
        self.batch.capacity = self.partition()
        if self.batch.budget: self.batch.budget.inactive_bytes = self.inactive
        return self.limit

    def release(self, ident):
        self.batch.live_reservations.pop(ident,None)
        self.batch.budget.active.pop(ident,None)

    @contextmanager
    def collector(self, root):
        self.collector_entries += 1; self.collector_owned = True
        try: yield
        finally: self.collector_owned = False

    def execute(self, item):
        ident = item['video_id']
        with self.batch.lock:
            self.guard(source=True)
            self.batch.live_reservations[ident] = {'folder':self.batch.jobs/ident,'bytes':2_240_000_000}
            self.batch.budget.active[ident] = {'bytes':2_240_000_000}
            (self.batch.jobs/ident).mkdir(exist_ok=True)
        with self.current_lock:
            self.sources += 1; self.source_peak = max(self.source_peak,self.sources); self.started.append(ident)
        try:
            if self.source: self.source(item)
            with self.batch.lock: self.inactive += self.body
            return {'schema_version':1,'video_id':ident,'status':'local_complete','diagnostics':{'phase':'terminal'}}
        finally:
            with self.current_lock: self.sources -= 1
            with self.batch.lock: self.batch.release_after_reconcile(ident)

    def copy(self, *args):
        assert not self.batch.lock._is_owned(), 'copy holds batch.lock'
        self.copy_calls += 1
        if self.publication: self.publication()

    def stat(self, *args):
        assert not self.batch.lock._is_owned(), 'stat holds batch.lock'
        self.stat_calls += 1
        return {}

    def finalize(self, record):
        self.events.append(('paired_receipt',record['video_id']))
        self.events.append(('cleanup',record['video_id']))
        with self.batch.lock: self.inactive -= self.body
        return record

    def publish(self, item, result):
        ident = item['video_id']; b = self.batch
        with self.current_lock:
            self.pubs += 1; self.pub_peak = max(self.pub_peak,self.pubs)
        try:
            b.drive.copy_pair(None,None,None,None); b.drive.stat_batch(None,None,None)
            remote = m.storage.remote_path(b.s['remote'],item,'m4a')
            done = {'status':'deleted','video_id':ident,'path':f'spool/jobs/{ident}/{ident}.m4a',
                'remote':remote,'bytes':self.body,'md5':'a'*32,'sha256':'b'*64,'drive_id':'audio-'+ident,
                'metadata':{'remote':remote.rpartition('/')[0]+f'/{ident}.info.json',
                    'md5':'c'*32,'sha256':'d'*64,'drive_id':'metadata-'+ident}}
            done = m.storage.verify_and_delete(done)
            m.write(b.jobs/ident/'canonical-record.json',done)
            return done
        finally:
            with self.current_lock: self.pubs -= 1

    def patches(self, stack, drain=None):
        original_storage = m.storage
        stack.enterContext(patch.object(original_storage,'exclusive_lock',side_effect=self.collector))
        stack.enterContext(patch.object(original_storage,'load_state',return_value={}))
        stack.enterContext(patch.object(original_storage,'read_drive_cooldown',return_value=None))
        stack.enterContext(patch.object(original_storage,'verify_and_delete',side_effect=self.finalize))
        stack.enterContext(patch.object(m,'SlotBudget',side_effect=lambda *a,**kw:FakeBudget(self)))
        stack.enterContext(patch.object(m.shutil,'disk_usage',side_effect=lambda *a:types.SimpleNamespace(free=self.physical)))
        if drain is not None:
            original = sm.ParallelScheduler
            def create(*a,**kw): kw['drain_timeout_seconds']=drain; return original(*a,**kw)
            stack.enterContext(patch.object(sm,'ParallelScheduler',side_effect=create))


class Running:
    def __init__(self, function):
        self.result = self.error = None
        def run():
            try: self.result = function()
            except BaseException as error: self.error = error
        self.thread = Thread(target=run); self.thread.start()
    def finish(self, case):
        self.thread.join(4); case.assertFalse(self.thread.is_alive())
        if self.error: raise self.error
        return self.result


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.enterContext(patch('socket.socket.connect',side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen',side_effect=AssertionError('Popen forbidden')))
        self.enterContext(patch('shutil.rmtree',side_effect=AssertionError('real delete forbidden')))
        self.enterContext(patch('pathlib.Path.unlink',side_effect=AssertionError('real delete forbidden')))
        def fixture_write(path, value):
            path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(value),encoding='utf-8')
        self.enterContext(patch.object(m,'write',side_effect=fixture_write))
        self.enterContext(patch.object(m.worker,'write',side_effect=fixture_write))

    def fixture(self, count=6, **kwargs):
        return Fixture(self.root,count,**kwargs)

    def test_fourth_job_refills_while_publisher_blocked_exact_limits_and_timers(self):
        f = self.fixture(); pub = Event(); release = Event(); second = Event(); fourth = Event()
        def source(item):
            if item['video_id'].endswith('1'): self.assertTrue(second.wait(2))
            if item['video_id'].endswith('2'): self.assertTrue(pub.wait(2))
            if item['video_id'].endswith('3'): fourth.set()
        def publication():
            if not pub.is_set(): pub.set(); self.assertTrue(release.wait(2))
        f.source=source; f.publication=publication
        f.patches(self)
        running=Running(f.batch.run)
        try:
            self.assertTrue(fourth.wait(2)); self.assertTrue(f.collector_owned)
            self.assertFalse(release.is_set()); self.assertEqual(4,len(f.started))
        finally: release.set(); second.set()
        result=running.finish(self)
        self.assertEqual(6,result['verified']); self.assertEqual('complete',result['parallel_state'])
        self.assertLessEqual(f.source_peak,2); self.assertEqual(1,f.pub_peak); self.assertEqual(1,f.collector_entries)
        self.assertEqual(6,f.copy_calls); self.assertEqual(6,f.stat_calls)
        report=m.read(f.batch.jobs/'parallel-scheduler-report.json')
        self.assertEqual(4,report['max_outstanding'])
        kinds={x['kind'] for x in report['timings']}
        self.assertTrue({'copy_start','copy_finish','stat_start','stat_finish','finalize_start','finalize_finish','partition_release_start','receipt_verified'}<=kinds)
        for item in f.batch.items:
            ident=item['video_id']; self.assertLess(f.events.index(('paired_receipt',ident)),f.events.index(('cleanup',ident)))
        self.assertFalse(f.collector_owned)

    def test_publication_failure_retains_ready_and_pending(self):
        f=self.fixture(8); pub=Event(); fourth=Event()
        def source(item):
            if item['video_id'].endswith('1'): self.assertTrue(f.batch.source_stop.wait(2))
            if item['video_id'].endswith('2'): self.assertTrue(pub.wait(2))
            if item['video_id'].endswith('3'): fourth.set()
        def publication():
            pub.set(); self.assertTrue(fourth.wait(2)); raise RuntimeError('private URL must never enter report')
        f.source=source; f.publication=publication; f.patches(self)
        result=f.batch.run()
        self.assertEqual(0,result['verified']); self.assertGreater(result['held'],0); self.assertGreater(result['pending'],0)
        self.assertEqual(0,len(f.events)); self.assertGreater(f.inactive,0); self.assertEqual(1,f.copy_calls)
        report=m.read(f.batch.jobs/'parallel-scheduler-report.json')
        self.assertTrue(all(not x['publication_verified'] for x in report['outcomes']))
        self.assertNotIn('private URL',json.dumps(report)); self.assertEqual('held',report['state'])

    def test_shared_fatal_blocks_actual_existing_GO_guard(self):
        f=self.fixture(2); reached=Event(); pub=Event()
        old=f.execute
        def execute(item):
            if item['video_id'].endswith('1'):
                reached.set(); self.assertTrue(pub.wait(2)); self.assertTrue(f.batch.source_stop.wait(2))
                folder=f.batch.jobs/item['video_id']; folder.mkdir(exist_ok=True)
                with self.assertRaises(m.worker.Held):
                    m.NativeBatch.await_owned_GO(f.batch,item['video_id'],folder,types.SimpleNamespace(poll=lambda:None),time.monotonic())
                self.assertFalse((folder/'GO').exists())
                return {'status':'held','video_id':item['video_id'],'diagnostics':{'phase':'terminal'}}
            return old(item)
        def publication():
            self.assertTrue(reached.wait(2)); pub.set(); raise RuntimeError('fatal publication')
        f.batch.execute_child=execute; f.publication=publication; f.patches(self)
        result=f.batch.run(); self.assertTrue(f.batch.source_stop.is_set()); self.assertEqual(0,result['verified'])

    def test_unclosed_callback_keeps_collector_owner_and_never_claims_release(self):
        f=self.fixture(2); pub=Event(); release=Event()
        def source(item):
            if item['video_id'].endswith('1'):
                self.assertTrue(pub.wait(2)); raise RuntimeError('source fatal while publication blocked')
        def publication(): pub.set(); self.assertTrue(release.wait(3))
        f.source=source; f.publication=publication; f.patches(self,drain=.03)
        running=Running(f.batch.run)
        path=f.batch.jobs/'parallel-owner-status.json'
        try:
            end=time.monotonic()+2
            while not path.exists() and time.monotonic()<end: time.sleep(.005)
            self.assertTrue(path.exists()); status=m.read(path)
            self.assertEqual('unclosed_callbacks_retained',status['status'])
            self.assertFalse(status['callbacks_closed']); self.assertFalse(status['lease_or_reservation_released'])
            self.assertTrue(f.collector_owned); self.assertTrue(running.thread.is_alive())
        finally: release.set()
        result=running.finish(self)
        self.assertEqual('unclosed',result['parallel_state']); self.assertGreater(result['inflight'],0)
        self.assertTrue(result['parallel_callbacks_closed']); self.assertFalse(f.collector_owned)
        self.assertTrue(f.batch.source_stop.is_set())

    def test_capacity_deferred_items_remain_pending_not_completed(self):
        f=self.fixture(3); f.inactive=5_500_000_000; f.patches(self)
        result=f.batch.run()
        self.assertEqual(3,result['pending']); self.assertEqual(0,result['verified']); self.assertEqual([],f.started)
        self.assertEqual('deferred',result['parallel_state'])

    def test_actual_controller_does_not_complete_a_deferred_frame(self):
        c=controller.BulkController.__new__(controller.BulkController)
        c.settings_path=self.root/'controller.json';m.write(c.settings_path,{})
        grant=self.root/'grant.json';m.write(grant,{})
        c.s={'root_admission_path':str(grant),'cohort_manifest':{'sha256':'a'*64},
             'frame_map':{'sha256':'b'*64}}
        c.root=self.root;c.runtime=self.root/'runtime';c.state_path=c.runtime/'cohort-state.json'
        c.invocation_path=c.runtime/'source-invocation.json';c.plan=lambda:None;c.admit=lambda row:{}
        row={'frame_index':0,'plan_sha256':'c'*64,'settings_path':'fixture','video_ids':['t0000000000']}
        c.frames=[row]
        b=types.SimpleNamespace(http_state_path=self.root/'ledger.json',jobs=self.root/'jobs',items=[],
            live_reservations={},parallel_callback_closure_proven=True,guard=lambda **kw:None,
            source_stop=Event(),dispatch_paused=Event(),stop_path=self.root/'STOP',
            run=lambda:{'verified':0,'held':0,'pending':1,'inflight':0,'parallel_state':'deferred',
                        'parallel_callbacks_closed':True})
        c.factory=lambda settings:b
        with patch.object(controller.worker,'control_paths',return_value={'http_state_path':b.http_state_path}), \
                patch.object(controller.contract,'windows_identity',return_value={'pid':1,'process_creation_filetime':'2'}):
            with self.assertRaisesRegex(controller.contract.ContractError,'bulk_frame_held_requires_review'):c.run()
        state=m.read(c.state_path)
        self.assertEqual('held_reconciliation_required',state['status'])
        self.assertEqual([],state['frames']);self.assertIsNotNone(state['current_frame'])

    def test_unverified_publication_cannot_be_counted(self):
        f=self.fixture(1); f.batch.publish=lambda *a:{'status':'deleted'}; f.patches(self)
        result=f.batch.run(); self.assertEqual(0,result['verified']); self.assertEqual(1,result['held'])
        self.assertTrue(f.batch.source_stop.is_set())

    def test_local_format_and_valid_parent_censor_continue_without_publication(self):
        f=self.fixture(4); original=f.batch.execute_child
        def execute(item):
            if item['video_id'].endswith('0'):
                return {'schema_version':1,'video_id':item['video_id'],'status':'held',
                        'diagnostics':{'phase':'terminal','error_class':'format_unavailable'}}
            if item['video_id'].endswith('1'):
                return {'video_id':item['video_id'],'status':'held','parent_censored_descriptor':'parent-censored.json','source_access':'unknown'}
            return original(item)
        f.batch.execute_child=execute; f.patches(self)
        result=f.batch.run()
        self.assertEqual(2,result['held']); self.assertEqual(2,result['verified'])
        self.assertEqual('complete',result['parallel_state']); self.assertEqual(0,result['pending'])
        self.assertFalse(f.batch.source_stop.is_set())

    def test_guard_failure_holds_all_unstarted_items_without_source_callback(self):
        f=self.fixture(3); original=f.batch.guard
        def guard(*,source=False,**kwargs):
            if source: raise m.worker.Held('lease_revoked')
            return original(source=source,**kwargs)
        f.batch.guard=guard; f.patches(self)
        result=f.batch.run()
        self.assertEqual([],f.started); self.assertEqual(3,result['pending'])
        self.assertEqual('held',result['parallel_state']); self.assertTrue(f.batch.source_stop.is_set())

    def test_publisher_requires_durable_matching_canonical_receipt(self):
        f=self.fixture(1); original=f.batch.publish
        def publication(item,result):
            done=original(item,result)
            m.write(f.batch.jobs/item['video_id']/'canonical-record.json',dict(done,drive_id='wrong'))
            return done
        f.batch.publish=publication; f.patches(self)
        result=f.batch.run(); self.assertEqual(0,result['verified'])
        self.assertEqual(1,result['held']); self.assertTrue(f.batch.source_stop.is_set())


    def test_full_virtual_slots_envelope_and_independent_ceilings(self):
        f=self.fixture(3); b=f.batch; b.budget=FakeBudget(f); f.patches(self)
        a=adapter.BatchAdapter(b,m,sm); work=[sm.WorkItem(x['video_id'],x) for x in b.items]
        self.assertTrue(a.before_submit(work[0],()))
        self.assertEqual(2_480_000_000,a.commitments())
        self.assertTrue(a.before_submit(work[1],(work[0],)))
        self.assertEqual(4_720_000_000,a.commitments())
        self.assertFalse(a.before_submit(work[2],tuple(work[:2])))
        b.live_reservations[work[0].key]={'bytes':2_240_000_000}; b.budget.active[work[0].key]={'bytes':2_240_000_000}
        self.assertEqual(4_720_000_000,a.commitments(), 'real reservation must replace virtual charge')
        self.assertFalse(a.fits(4_720_000_000,4_720_000_000+m.storage.JOURNAL_RESERVE-1))
        f.physical=m.FREE+4_720_000_000-1
        self.assertFalse(a.fits(4_720_000_000,16_000_000_000))
        f.physical=m.FREE+4_720_000_000+500_000_000; b.others=500_000_001
        self.assertFalse(a.fits(4_720_000_000,16_000_000_000), 'other owner future bytes preserve physical spare')
        b.others=0
        f.physical=30_000_000_000; f.inactive=780_000_001; f.guard()
        self.assertFalse(a.fits(4_720_000_000,16_000_000_000))


    def test_final_http_evidence_committed_before_full_slot_release(self):
        for code in ['source_403','source_429']:
            b=m.NativeBatch.__new__(m.NativeBatch); b.lock=RLock(); b.s={}; events=[]
            b.observe_pending_failures=lambda value:events.append(('http',value['diagnostics']['error_class']))
            b.observe_worker_diagnostics=lambda folder:False
            b.administrative_hold=lambda reason:events.append(('hold',reason))
            b.release_after_reconcile=lambda ident:events.append(('release',ident))
            b.parent_timeout_descriptor=lambda *a:False
            folder=self.root/code; folder.mkdir()
            result={'schema_version':1,'video_id':'t0000000000','status':'held','diagnostics':{'phase':'terminal','error_class':code}}
            m.write(folder/'result.json',result)
            self.assertFalse(b.finalize_child_result('t0000000000',folder,result))
            self.assertEqual([('http',code),('release','t0000000000')],events)


if __name__=='__main__': unittest.main()
