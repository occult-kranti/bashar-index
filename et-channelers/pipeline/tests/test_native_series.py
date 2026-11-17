"""Offline series authorization, interruption, evidence and backpressure gates."""
import csv
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import native_series as series, native_http_policy as policy


class Runtime:
    def __init__(self, test):
        self.test, self.pins, self.calls = test, test.auth['runtime_pins'], []
        self.fail_run = False
        self.snapshot_change = {}
        self.outcome = 'canonical_verified'

    def snapshot(self, frame):
        value = {'observed_at_epoch': 1000, 'owned_native_processes': 0, 'active_frame': None,
                 'stop_present': False, 'drive_hold': False, 'source_hold': False,
                 'managed_bytes': 8_000_000_000, 'other_growth_reservations_bytes': 1_000_000_000,
                 'disk_free_bytes': 20_000_000_000, 'asr_staging_bytes': 0, 'asr_pairs': 0,
                 'asr_accepting': True, 'asr_cap_bytes':series.ASR,'attempt_history_complete':True,
                 'attempt_history_sha256':'a'*64,'http_policy': {'seed_sha256': self.test.seed['sha256'], 'state': policy.empty_state()},
                 'canonical_receipts': {}, 'attempted_or_uncertain_ids': []}
        value.update(self.snapshot_change)
        return value

    def activate(self, binding): self.calls.append('activate')
    def run(self, binding):
        self.calls.append('run')
        if self.fail_run: raise OSError('injected interruption')

    def drain(self, binding):
        self.calls.append('drain')
        frame = next(f for f in self.test.proposal['frames'] if f['plan']['sha256'] == binding['plan_sha256'])
        outcomes = {}
        for ident in frame['video_ids']:
            attempted = self.outcome not in {'proven_never_started', 'uncertain'}
            doc = {'video_id': ident, 'plan_sha256': binding['plan_sha256'], 'owned_processes_gone': True,
                   'source_attempted': attempted, 'go_was_issued': attempted, 'source_requests': int(attempted),
                   'launch_evidence_complete': True}
            if self.outcome == 'canonical_verified': doc['canonical_receipt'] = self.test.receipt(ident)
            proof = self.test.save('evidence-' + ident + '.json', doc)
            outcomes[ident] = {'status': self.outcome, 'source_attempted': attempted if self.outcome != 'uncertain' else None,
                               'evidence': proof}
        return {'owned_native_processes': 0, 'drained': True, 'plan_sha256': binding['plan_sha256'], 'outcomes': outcomes}


class SeriesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('no network')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('no process')))
        self.rows = [{'video_id': f'video{i:06d}', 'channel_dir': 'channel'+str(i), 'tab': 'videos', 'listing_rank': '1'} for i in range(60)]
        queue = self.root/'queue.csv'
        with queue.open('w', newline='', encoding='utf-8') as output:
            writer = csv.DictWriter(output, fieldnames=list(self.rows[0])); writer.writeheader(); writer.writerows(self.rows)
        items = [dict(row, queue_row=row, queue_row_sha256=series.sha(series.encoded(row)),
                      video_url='https://www.youtube.com/watch?v='+row['video_id'], duration_seconds=None,
                      selection_evidence={'status':'no_prior_selection'}) for row in self.rows]
        self.seed = self.save('seed.json', policy.empty_state())
        history = self.save('history.json', {'preserved':True})
        self.proposal_pin = series.prepare(self.root/'proposal',queue,items,evidence_pins=[history],seed_pin=self.seed,history_pins=[history])
        self.proposal = series.read(self.proposal_pin['path'])
        runtime_pin = self.save('runtime.txt', {'fixture_only':True})
        bindings = []
        for frame in self.proposal['frames']:
            review = self.save(f"review{frame['index']}.json", {'covered_event_ids':[], 'allowed_video_ids':frame['video_ids']})
            settings = self.save(f"settings{frame['index']}.json", {
                'plan_path':frame['plan']['path'],'workers':2,'spool_cap_bytes':series.SPOOL,
                'profile':'stock_headful_wpc_native_batch_v4','http_policy_seed':self.seed,
                'code_pins':[runtime_pin],'preserved_controls':[history],'historical_http_review':review,'remote':'fixture:archive'})
            lease = self.save(f"lease{frame['index']}.json", {'settings_sha256':settings['sha256'],'plan_sha256':frame['plan']['sha256'],
                'owner':'root','authorized':True,'source_scope_authorized':True,'expires_at_epoch':2000})
            bindings.append({'plan_sha256':frame['plan']['sha256'],'settings':settings,'lease':lease})
        self.auth = {'schema_version':1,'authorized':True,'owner':'root','proposal_sha256':self.proposal_pin['sha256'],
            'allowed_video_ids':self.proposal['proposed_allowed_video_ids'],'http_policy_seed_sha256':self.seed['sha256'],
            'issued_at_epoch':999,'expires_at_epoch':2000,'frame_bindings':bindings,'runtime_pins':[runtime_pin]}
        self.auth_pin = self.save('authorization.json', self.auth)
        self.runtime = Runtime(self)

    def save(self, name, value):
        path=self.root/name;series.atomic(path,value);return series.pin(path)

    def controller(self):
        return series.Controller(self.proposal_pin,self.auth_pin,self.root/'state.json',self.runtime,clock=lambda:1000)

    def receipt(self, ident):
        row=next(x for x in self.rows if x['video_id']==ident)
        prefix=f"fixture:archive/{row['channel_dir']}/Videos/{ident}"
        return {'status':'deleted','video_id':ident,'path':ident+'.m4a','remote':prefix+'.m4a',
            'drive_id':'audio-'+ident,'md5':'a'*32,'sha256':'b'*64,'bytes':100,
            'metadata':{'remote':prefix+'.info.json','drive_id':'meta-'+ident,'md5':'c'*32,'sha256':'d'*64,'bytes':50}}

    def test_disabled_plan_does_not_authorize_and_cannot_expand_to_latest50(self):
        self.assertFalse(self.proposal['execute_allowed']);self.assertEqual([20,20,20],[len(x['video_ids']) for x in self.proposal['frames']])
        for key,value in [('authorized',False),('allowed_video_ids',self.auth['allowed_video_ids']+['outside0000'])]:
            changed=dict(self.auth,**{key:value})
            with self.assertRaises(series.Held):series.validate_authorization(self.proposal_pin,changed,1000)
        self.assertEqual([],self.runtime.calls)

    def test_expired_or_changed_code_never_activates(self):
        self.auth['expires_at_epoch']=900;self.auth_pin=self.save('authorization.json',self.auth)
        with self.assertRaisesRegex(series.Held,'authorization_expired'):self.controller()
        self.auth['expires_at_epoch']=2000;self.auth_pin=self.save('authorization.json',self.auth)
        Path(self.auth['runtime_pins'][0]['path']).write_text('changed')
        with self.assertRaisesRegex(series.Held,'pin_changed'):self.controller()
        self.assertEqual([],self.runtime.calls)

    def test_frames_drain_sequentially_and_successful_attempts_are_not_holds(self):
        final=self.controller().run()
        self.assertEqual(['activate','run','drain']*3,self.runtime.calls)
        self.assertEqual('finished',final['status']);self.assertEqual(60,len(final['source_spent']))
        self.controller().run()
        self.assertEqual(9,len(self.runtime.calls))

    def test_last_frame_finalization_hold_is_not_reported_finished_or_retried(self):
        original=self.runtime.drain;held=[True]
        def drain(binding):
            result=original(binding)
            result['local_reconciliation_required']=held[0] and binding['plan_sha256']==self.proposal['frames'][-1]['plan']['sha256']
            return result
        self.runtime.drain=drain
        with self.assertRaisesRegex(series.Held,'local_reconciliation_required'):self.controller().run()
        state=series.read(self.root/'state.json')
        self.assertEqual('drained_local_hold',state['frames']['2']['phase'])
        self.assertNotIn(state['status'],{'finished','finished_with_holds'})
        with self.assertRaisesRegex(series.Held,'interrupted_frame_requires_reconciliation'):self.controller().run()
        self.assertEqual(3,self.runtime.calls.count('run'))
        self.controller().reconcile()
        self.assertEqual('held_local_reconciliation_required',series.read(self.root/'state.json')['status'])
        # The owner supplies new local-only evidence; reconciliation does not
        # activate a frame or repeat any already completed source request.
        held[0]=False;self.controller().reconcile()
        self.assertEqual('finished',self.controller().run()['status'])
        self.assertEqual(3,self.runtime.calls.count('run'))

    def test_interruption_is_reservation_not_fabricated_source_spend(self):
        self.runtime.fail_run=True
        with self.assertRaises(OSError):self.controller().run()
        state=series.read(self.root/'state.json')
        self.assertEqual({},state['source_spent']);self.assertEqual(20,len(state['frames']['0']['reserved_ids']))
        with self.assertRaisesRegex(series.Held,'interrupted_frame_requires_reconciliation'):self.controller().run()
        self.assertEqual(['activate','run'],self.runtime.calls)
        self.runtime.outcome='proven_never_started';self.controller().reconcile()
        state=series.read(self.root/'state.json')
        self.assertEqual(20,len(state['never_started']));self.assertEqual({},state['source_spent'])
        self.assertEqual(['activate','run','drain'],self.runtime.calls)

    def test_uncertain_drain_is_not_automatically_retried(self):
        self.runtime.outcome='uncertain'
        final=self.controller().run()
        self.assertEqual(60,len(final['uncertain']));self.assertEqual({},final['source_spent'])
        self.assertEqual('finished_with_holds',final['status'])
        self.controller().run();self.assertEqual(9,len(self.runtime.calls))

    def test_stop_drive_or_asr_pressure_prevents_next_frame(self):
        for change,code in [({'stop_present':True},'series_stopped'),({'drive_hold':True},'provider_hold'),
                            ({'asr_pairs':3},'asr_backpressure'),({'managed_bytes':10_000_000_001},'resource_backpressure'),
                            ({'disk_free_bytes':1_999_999_999},'resource_backpressure')]:
            self.runtime.snapshot_change=change
            with self.subTest(code=code),self.assertRaisesRegex(series.Held,code):self.controller().run()
        self.assertEqual([],self.runtime.calls)

    def test_new_global429_survives_success_and_blocks_next_frame(self):
        original=self.runtime.drain
        def drain(binding):
            result=original(binding)
            event=policy.classify_http_failure(429,'https://www.youtube.com/youtubei/v1/player',None,None,'metadata',self.rows[0]['video_id'],{},now_epoch=1000)
            state=policy.apply_event(policy.empty_state(),event,'a'*64,1000)
            self.runtime.snapshot_change={'http_policy':{'seed_sha256':self.seed['sha256'],'state':state}}
            return result
        self.runtime.drain=drain
        with self.assertRaisesRegex(series.Held,'http_policy_hold'):self.controller().run()
        self.assertEqual(['activate','run','drain'],self.runtime.calls)
        self.assertEqual(1,len(self.runtime.snapshot_change['http_policy']['state']['events']))

    def test_attempted_id_is_excluded_even_without_global_stop(self):
        self.runtime.snapshot_change={'attempted_or_uncertain_ids':[self.rows[0]['video_id']]}
        with self.assertRaisesRegex(series.Held,'source_attempt_history'):self.controller().run()
        self.assertEqual([],self.runtime.calls)

    def test_incomplete_attempt_history_cannot_silently_mean_no_attempts(self):
        self.runtime.snapshot_change={'attempt_history_complete':False}
        with self.assertRaisesRegex(series.Held,'attempt_history_incomplete'):self.controller().run()
        self.assertEqual([],self.runtime.calls)

    def test_forged_never_started_label_cannot_release_uncertainty(self):
        controller=self.controller();self.runtime.outcome='proven_never_started'
        frame=self.proposal['frames'][0];evidence=self.runtime.drain(self.auth['frame_bindings'][0])
        ident=frame['video_ids'][0];doc=series.read(evidence['outcomes'][ident]['evidence']['path']);doc['go_was_issued']=True
        evidence['outcomes'][ident]['evidence']=self.save('bad-launch.json',doc)
        with self.assertRaisesRegex(series.Held,'never_started_unproven'):controller.finish(frame,evidence)

    def test_only_exact_complete_canonical_pair_skips_prior_attempt_guard(self):
        ident=self.rows[0]['video_id']
        self.runtime.snapshot_change={'attempted_or_uncertain_ids':[ident],'canonical_receipts':{ident:self.receipt(ident)}}
        controller=self.controller();pending=controller.guard(self.proposal['frames'][0]);self.assertNotIn(ident,pending)
        self.runtime.snapshot_change['canonical_receipts'][ident]['metadata']['drive_id']='audio-'+ident
        with self.assertRaisesRegex(series.Held,'source_attempt_history'):controller.guard(self.proposal['frames'][0])
        self.runtime.snapshot_change['canonical_receipts'][ident]=self.receipt(ident)
        self.runtime.snapshot_change['canonical_receipts'][ident]['metadata']['remote']='fixture:wrong'
        with self.assertRaisesRegex(series.Held,'source_attempt_history'):controller.guard(self.proposal['frames'][0])

    def test_queue_ranks_are_zero_based_and_latest50_row_cannot_enter(self):
        for rank, accepted in [('0',True),('19',True),('20',False)]:
            row=dict(self.rows[0],listing_rank=rank)
            path=self.root/('rank'+rank+'.csv')
            with path.open('w',newline='',encoding='utf-8') as output:
                writer=csv.DictWriter(output,fieldnames=list(row));writer.writeheader();writer.writerow(row)
            item=dict(row,queue_row=row,queue_row_sha256=series.sha(series.encoded(row)),
                      video_url='https://www.youtube.com/watch?v='+row['video_id'],duration_seconds=None,
                      selection_evidence={'status':'no_prior_selection'})
            args=(self.root/('rank'+rank),path,[item])
            kwargs=dict(evidence_pins=[self.seed],seed_pin=self.seed,history_pins=[self.seed])
            if accepted:series.prepare(*args,**kwargs)
            else:
                with self.assertRaisesRegex(series.Held,'latest20_only'):series.prepare(*args,**kwargs)

    def test_frozen_55gb_lease_templates_still_need_separate_root_authorization(self):
        for i,binding in enumerate(self.auth['frame_bindings']):
            settings=series.read(binding['settings']['path']);settings['spool_cap_bytes']=5_500_000_000
            binding['settings']=self.save(f'draft-settings{i}.json',settings)
            lease=series.read(binding['lease']['path'])
            lease.update(state='draft',authorized=False,source_scope_authorized=False,root_admission_required=True,
                         expires_at_epoch=None,max_frame_seconds=14_400,settings_sha256=binding['settings']['sha256'])
            binding['lease']=self.save(f'draft-lease{i}.json',lease)
        self.auth_pin=self.save('authorization.json',self.auth)
        self.assertEqual('latest20',self.controller().proposal['scope'])
        self.auth['authorized']=False;self.auth_pin=self.save('authorization.json',self.auth)
        with self.assertRaisesRegex(series.Held,'series_not_authorized'):self.controller()
        self.assertEqual([],self.runtime.calls)


if __name__=='__main__':unittest.main()
