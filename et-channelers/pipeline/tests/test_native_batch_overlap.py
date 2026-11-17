"""Event/barrier fixtures execute only copied scheduling code; no child or I/O."""
import contextlib
from concurrent.futures import Future
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from pipeline import native_batch as new

class Scheduling(unittest.TestCase):
    def scenario(self,module,mode='normal'):
        entered=threading.Event();release=threading.Event();b_started=threading.Event();release_b=threading.Event();c_started=threading.Event()
        state={'running':0,'peak':0,'publishing':0,'writer_peak':0,'a_done':False,'published':False,'error':None}
        counter_lock=threading.Lock()
        with tempfile.TemporaryDirectory() as tmp:
            obj=object.__new__(module.NativeBatch);obj.root=Path(tmp);obj.spool=Path(tmp)/'spool';obj.jobs=obj.spool/'jobs'
            obj.s={'workers':2,'max_asset_bytes':2_000_000_000,'spool_cap_bytes':6_000_000_000,'remote':'fixture:'}
            obj.items=[{'video_id':x} for x in ('a','b','c')];obj.source_stop=threading.Event();obj.dispatch_paused=threading.Event();obj.lock=threading.RLock()
            obj.live_reservations={};obj.plan_sha='0'*64;obj.state_path=Path(tmp)/'state';obj.batch_journal=Path(tmp)/'journal';obj.budget=None
            def guard(**kw):
                obj.capacity={'inactive_spool_bytes':5_000_000_000 if mode=='capacity' and state['a_done'] and not state['published'] else 0}
                return 10_000_000_000
            obj.guard=guard;obj.finalize_handoff=lambda *a:None
            class Budget:
                def __init__(self,*a,**kw):pass
                def _outstanding(self):return sum(v['bytes'] for v in obj.live_reservations.values())
                def usage(self):return obj.capacity['inactive_spool_bytes']
            def child(item):
                ident=item['video_id']
                with obj.lock:obj.live_reservations[ident]={'bytes':2_240_000_000}
                with counter_lock:state['running']+=1;state['peak']=max(state['peak'],state['running'])
                try:
                    if ident=='a':
                        if not b_started.wait(2):raise AssertionError('peer not launched')
                        state['a_done']=True
                        if mode=='source_stop':obj.source_stop.set()
                        if mode=='handoff_pause':obj.dispatch_paused.set()
                    elif ident=='b':
                        b_started.set()
                        if not release_b.wait(4):raise AssertionError('peer release missing')
                    else:c_started.set()
                    return {'status':'local_complete','video_id':ident}
                finally:
                    with counter_lock:state['running']-=1
                    with obj.lock:obj.live_reservations.pop(ident,None)
            def publish(item,result):
                with counter_lock:state['publishing']+=1;state['writer_peak']=max(state['writer_peak'],state['publishing'])
                try:
                    if item['video_id']=='a':
                        entered.set()
                        if not release.wait(3):raise AssertionError('publisher release missing')
                        state['published']=True
                finally:
                    with counter_lock:state['publishing']-=1
            obj.execute_child=child;obj.publish=publish
            def run():
                try:state['counts']=obj.run()
                except BaseException as e:state['error']=type(e).__name__
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(module,'SlotBudget',Budget))
                stack.enter_context(patch.object(module.storage,'exclusive_lock',lambda *a:contextlib.nullcontext()))
                stack.enter_context(patch.object(module.storage,'load_state',lambda *a:{}))
                stack.enter_context(patch.object(module.storage,'receipt_complete',lambda *a:False))
                stack.enter_context(patch.object(module.storage,'journal',lambda *a:None))
                stack.enter_context(patch.object(module.storage,'read_drive_cooldown',lambda *a:{'until_epoch':9999999999} if mode=='drive_hold' and state['a_done'] else None))
                stack.enter_context(patch.object(module,'write',lambda *a:None))
                t=threading.Thread(target=run);t.start()
                try:
                    self.assertTrue(entered.wait(2),'publisher must be reached')
                    while_publish=c_started.wait(.15)
                finally:release.set();release_b.set();t.join(4)
            self.assertFalse(t.is_alive());self.assertIsNone(state['error']);self.assertLessEqual(state['peak'],2);self.assertEqual(state['writer_peak'],1)
            return while_publish,state
    def test_refill_starts_next_source_before_delayed_publish(self):
        active,state=self.scenario(new);self.assertTrue(active);self.assertEqual(state['counts']['verified'],3)
    def test_completed_retained_bytes_delay_refill_until_publication_frees_space(self):
        active,state=self.scenario(new,'capacity');self.assertFalse(active);self.assertEqual(state['counts']['verified'],3)
    def test_source_stop_keeps_unstarted_pending(self):
        active,state=self.scenario(new,'source_stop');self.assertFalse(active);self.assertEqual(state['counts']['pending'],1)
    def test_handoff_pause_keeps_unstarted_pending(self):
        active,state=self.scenario(new,'handoff_pause');self.assertFalse(active);self.assertEqual(state['counts']['pending'],1)
    def test_known_drive_cooldown_blocks_refill_without_clearing_it(self):
        active,state=self.scenario(new,'drive_hold');self.assertFalse(active);self.assertEqual(state['counts']['pending'],1)
    def test_delayed_child_reservation_is_charged_before_second_refill(self):
        # Both original children finish together, leaving 3.5GB. The executor
        # accepts C but delays its reservation until after parent dispatch.
        # Without a virtual charge, D is incorrectly submitted into the same
        # remaining 2.5GB slot and can fail before any source attempt exists.
        state={'retained':False,'c_finished':False,'published':[]};submitted=[];futures={}
        with tempfile.TemporaryDirectory() as tmp:
            obj=object.__new__(new.NativeBatch);obj.root=Path(tmp);obj.spool=Path(tmp)/'spool';obj.jobs=obj.spool/'jobs'
            obj.s={'workers':2,'max_asset_bytes':2_000_000_000,'spool_cap_bytes':6_000_000_000,'remote':'fixture:'}
            obj.items=[{'video_id':x} for x in 'abcd'];obj.source_stop=threading.Event();obj.dispatch_paused=threading.Event();obj.lock=threading.RLock()
            obj.live_reservations={};obj.plan_sha='0'*64;obj.state_path=Path(tmp)/'state';obj.batch_journal=Path(tmp)/'journal';obj.budget=None
            def guard(**kw):
                obj.capacity={'inactive_spool_bytes':(3_500_000_000 if state['retained'] else 0)+(100_000_000 if state['c_finished'] else 0)}
                return 10_000_000_000
            class Budget:
                def __init__(self,*a,**kw):pass
                def _outstanding(self):return 0
                def usage(self):return obj.capacity['inactive_spool_bytes']
            class DelayedExecutor:
                def __init__(self,**kw):assert kw['max_workers']==2
                def __enter__(self):return self
                def __exit__(self,*args):return False
                def submit(self,callback,item):
                    ident=item['video_id'];submitted.append(ident);f=Future();futures[ident]=f
                    if ident!='c':f.set_result({'status':'local_complete','video_id':ident})
                    if ident=='b':state['retained']=True
                    return f
            def publish(item,result):
                ident=item['video_id']
                if not state['published']:
                    self.assertEqual(submitted,['a','b','c'])
                    futures['c'].set_result({'status':'local_complete','video_id':'c'});state['c_finished']=True
                state['published'].append(ident)
                if {'a','b'}<=set(state['published']):state['retained']=False
            obj.guard=guard;obj.execute_child=lambda *a:None;obj.publish=publish;obj.finalize_handoff=lambda *a:None
            with contextlib.ExitStack() as stack:
                for target,name,value in [(new,'SlotBudget',Budget),(new,'ThreadPoolExecutor',DelayedExecutor),(new,'write',lambda *a:None),
                    (new.storage,'exclusive_lock',lambda *a:contextlib.nullcontext()),(new.storage,'load_state',lambda *a:{}),
                    (new.storage,'receipt_complete',lambda *a:False),(new.storage,'journal',lambda *a:None),(new.storage,'read_drive_cooldown',lambda *a:None)]:
                    stack.enter_context(patch.object(target,name,value))
                result=obj.run()
            self.assertEqual(submitted,['a','b','c','d']);self.assertEqual(result,{'verified':4,'skipped':0,'held':0,'pending':0})
if __name__=='__main__':unittest.main()
