from pathlib import Path
import json,sys,tempfile,unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validated_projection_cache import ValidatedProjectionCache,ProjectionChanged


class ProjectionCacheTests(unittest.TestCase):
    def test_one_local_snapshot_change_resamples_to_current_hold(self):
        state={'generation':1};calls=[];cache=ValidatedProjectionCache()
        def compute():
            calls.append(1)
            if state['generation']==1:state['generation']=2;return {'allowed':True}
            return {'allowed':False}
        value=cache.project(['inert'],fingerprint=lambda p:state['generation'],now_epoch=10,compute=compute)
        self.assertFalse(value['allowed']);self.assertEqual(len(calls),2)

    def test_persistent_snapshot_instability_stops_after_three_local_reads(self):
        state={'generation':1};calls=[];cache=ValidatedProjectionCache()
        def compute():calls.append(1);state['generation']+=1;return {'allowed':True}
        with self.assertRaises(ProjectionChanged):
            cache.project(['inert'],fingerprint=lambda p:state['generation'],now_epoch=10,compute=compute)
        self.assertEqual(len(calls),3);self.assertEqual(cache.hits,0)

    def test_portable_file_wrapper_observes_every_dependency_again(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'ledger.json';path.write_text('{"trip":null}')
            def fingerprint(p):
                stat=p.stat();return stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,stat.st_ino,stat.st_dev
            cache=ValidatedProjectionCache();calls=[]
            def compute():calls.append(1);return json.loads(path.read_text())
            self.assertEqual(cache.project([path,path],fingerprint=fingerprint,now_epoch=10,compute=compute),{'trip':None})
            path.write_text('{"trip":"held"}')
            self.assertEqual(cache.project([path],fingerprint=fingerprint,now_epoch=10.1,compute=compute),{'trip':'held'})
            self.assertEqual(len(calls),2)

    def test_changed_ledger_and_authority_recompute_instead_of_reusing_allow(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=Path(directory)/'ledger.json';authority=Path(directory)/'authority.json'
            ledger.write_text('{"trip":null}');authority.write_text('{"allowed":true}')
            def key():
                return tuple((p.stat().st_mtime_ns,p.stat().st_ctime_ns,p.stat().st_size) for p in (ledger,authority))
            def compute():return {'allowed':json.loads(authority.read_text())['allowed'] and json.loads(ledger.read_text())['trip'] is None}
            cache=ValidatedProjectionCache();current=key()
            self.assertTrue(cache.get(current,now_epoch=10,current_key=key,compute=compute)['allowed'])
            ledger.write_text('{"trip":"actual_new_denial"}')
            with self.assertRaises(ProjectionChanged):cache.get(current,now_epoch=10.1,current_key=key,compute=compute)
            self.assertFalse(cache.get(key(),now_epoch=10.1,current_key=key,compute=compute)['allowed'])
            ledger.write_text('{"trip":null}');authority.write_text('{"allowed":false}')
            self.assertFalse(cache.get(key(),now_epoch=10.2,current_key=key,compute=compute)['allowed'])

    def test_mixed_snapshot_during_computation_is_never_cached_or_returned(self):
        state={'generation':1};calls=[];cache=ValidatedProjectionCache()
        def key():return state['generation']
        def compute():calls.append(1);state['generation']=2;return {'allowed':True}
        with self.assertRaises(ProjectionChanged):cache.get(1,now_epoch=10,current_key=key,compute=compute)
        self.assertEqual(cache.hits,0)
        self.assertEqual(cache.get(2,now_epoch=10.1,current_key=key,compute=lambda:{'allowed':False}),{'allowed':False})

    def test_clock_regression_expiry_and_caller_mutation_do_not_reuse_stale_view(self):
        cache=ValidatedProjectionCache(maximum_age_seconds=.5);calls=[]
        def compute():calls.append(1);return {'held_ids':['exact']}
        value=cache.get('key',now_epoch=10,current_key=lambda:'key',compute=compute);value['held_ids'].clear()
        self.assertEqual(cache.get('key',now_epoch=10.1,current_key=lambda:'key',compute=compute)['held_ids'],['exact'])
        cache.get('key',now_epoch=9.9,current_key=lambda:'key',compute=compute)
        cache.get('key',now_epoch=10.5,current_key=lambda:'key',compute=compute)
        self.assertEqual(len(calls),3)

    def test_mature_failure_is_not_replaced_by_previous_cached_success(self):
        cache=ValidatedProjectionCache();cache.get(1,now_epoch=10,current_key=lambda:1,compute=lambda:True)
        def fail():raise ValueError('current_actual_hold')
        with self.assertRaisesRegex(ValueError,'current_actual_hold'):cache.get(2,now_epoch=10.1,current_key=lambda:2,compute=fail)
        with self.assertRaisesRegex(ValueError,'current_actual_hold'):cache.get(2,now_epoch=10.2,current_key=lambda:2,compute=fail)


if __name__=='__main__':unittest.main()
