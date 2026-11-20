"""Synthetic SQLite accounting and real local process races; no HTTP or tools."""
from decimal import Decimal
import multiprocessing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from pipeline import research_agent_budget as budget


def _compete(path,barrier,results,index):
    ledger=budget.BudgetLedger(path,cap_usd='0.10');barrier.wait()
    try:
        ledger.reserve('process-'+str(index),request_sha256=str(index)*64,max_input_tokens=1000,max_output_tokens=18_000)
        results.put('reserved')
    except budget.BudgetExceeded:results.put('budget_exhausted')


class ResearchBudgetTests(unittest.TestCase):
    def make(self,folder,cap='100.00'):
        return budget.BudgetLedger(Path(folder)/'shared.sqlite3',cap_usd=cap)

    def reserve(self,ledger,job='one',sha='a'*64,inputs=1000,outputs=1000):
        return ledger.reserve(job,request_sha256=sha,max_input_tokens=inputs,max_output_tokens=outputs)

    def dispatch(self,ledger,job='one',sha='a'*64,inputs=1000,outputs=1000,**kwargs):
        return ledger.mark_dispatched(job,request_sha256=sha,input_tokens_upper_bound=inputs,max_output_tokens=outputs,**kwargs)

    def test_exact_micro_USD_cached_discount_and_reasoning_counted_once(self):
        self.assertEqual(budget.usd_to_micro(Decimal('100.00')),100_000_000)
        self.assertEqual(budget.micro_to_usd(75),'0.000075')
        #600 uncached +200cached input,300output INCLUDING100reasoning.
        usage={'input_tokens':800,'output_tokens':300,'total_tokens':1100,
            'input_tokens_details':{'cached_tokens':200},'output_tokens_details':{'reasoning_tokens':100}}
        self.assertEqual(budget.usage_cost_micro_usd(usage),1815)
        self.assertEqual(budget.usage_cost_micro_usd({'input_tokens':1,'output_tokens':0}),1)
        with self.assertRaises(budget.BudgetError):budget.usd_to_micro(.1)
        with self.assertRaises(budget.BudgetError):budget.usd_to_micro('0.0000001')

    def test_idempotent_reserve_dispatch_settle_and_restart(self):
        with TemporaryDirectory() as folder:
            ledger=self.make(folder);first=self.reserve(ledger)
            self.assertEqual(first['reserved_micro_usd'],5250)
            self.assertEqual(self.reserve(ledger)['reservation_id'],first['reservation_id'])
            dispatched=self.dispatch(ledger)
            self.assertEqual(dispatched['state'],'in_flight');self.assertFalse(dispatched['can_dispatch'])
            with self.assertRaises(budget.AlreadyDispatched):self.dispatch(ledger)
            usage={'input_tokens':800,'cached_input_tokens':200,'output_tokens':300,'reasoning_tokens':100}
            charged=ledger.settle('one',response_id='resp-fictional-one',usage=usage)
            self.assertEqual(charged['charged_micro_usd'],1815)
            ledger=self.make(folder)
            self.assertEqual(ledger.settle('one',response_id='resp-fictional-one',usage=usage),charged)
            state=ledger.status();self.assertEqual(state['charged_micro_usd'],1815);self.assertEqual(state['reserved_micro_usd'],0)
            self.assertEqual(state['pending'],[]);self.assertEqual(state['available_micro_usd'],100_000_000-1815)
            with self.assertRaises(budget.BudgetConflict):ledger.settle('one',response_id='different-response',usage=usage)

    def test_request_identity_cap_and_price_policy_are_immutable(self):
        with TemporaryDirectory() as folder:
            ledger=self.make(folder);self.reserve(ledger)
            with self.assertRaises(budget.BudgetConflict):self.reserve(ledger,sha='b'*64)
            with self.assertRaises(budget.BudgetConflict):self.make(folder,cap='99.00')
            with self.assertRaises(budget.BudgetError):self.make(folder,cap='101.00')
            with self.assertRaises(TypeError):budget.POLICY['input_micro_usd_per_million']=0
            c=sqlite3.connect(ledger.path)
            try:
                with self.assertRaises(sqlite3.IntegrityError):c.execute('UPDATE metadata SET cap=1000000000')
            finally:c.close()

    def test_only_reviewed_text_model_limits_and_dispatch_params(self):
        with TemporaryDirectory() as folder:
            ledger=self.make(folder)
            for args in ({'model':'gpt-5.4-mini','max_input_tokens':1,'max_output_tokens':1},
                {'max_input_tokens':300_000,'max_output_tokens':128_000},
                {'max_input_tokens':1,'max_output_tokens':128_001}):
                with self.subTest(args=args),self.assertRaises(budget.BudgetError):
                    ledger.reserve('invalid',request_sha256='a'*64,**args)
            self.reserve(ledger)
            for params in ({'tools':[{'type':'web_search'}]},{'modalities':['audio']},{'modalities':['text','image']},
                           {'service_tier':'priority'},{'store':True},{'pricing_region':'eu'}):
                with self.subTest(params=params),self.assertRaises(budget.BudgetError):self.dispatch(ledger,**params)
            with self.assertRaises(budget.BudgetError):self.dispatch(ledger,inputs=1001)
            with self.assertRaises(budget.BudgetError):self.dispatch(ledger,outputs=1001)
            self.assertEqual(ledger.status()['pending'][0]['state'],'reserved')

    def test_crash_after_dispatch_holds_full_money_without_expiry_or_retry(self):
        with TemporaryDirectory() as folder:
            ledger=self.make(folder);self.reserve(ledger);self.dispatch(ledger)
            restarted=self.make(folder);state=restarted.status()
            self.assertEqual(state['reserved_micro_usd'],5250)
            self.assertFalse(state['pending'][0]['automatic_retry_allowed'])
            with self.assertRaises(budget.AlreadyDispatched):self.dispatch(restarted)
            with self.assertRaises(budget.BudgetError):restarted.cancel_unstarted('one')
            restarted.mark_uncertain('one','timeout_after_dispatch')
            self.assertEqual(self.make(folder).status()['pending'][0]['state'],'uncertain')
            recovered=restarted.settle('one',response_id='reconciled-response',usage={'input_tokens':2,'output_tokens':3})
            self.assertEqual(recovered['state'],'charged');self.assertFalse(restarted.status()['blocked'])

    def test_explicit_unbilled_resolution_never_reopens_same_job(self):
        with TemporaryDirectory() as folder:
            ledger=self.make(folder);self.reserve(ledger);self.dispatch(ledger);ledger.mark_uncertain('one','transport_unknown')
            ledger.confirm_unbilled('one',evidence_sha256='f'*64)
            self.assertEqual(ledger.status()['reserved_micro_usd'],0)
            self.assertEqual(self.reserve(ledger)['state'],'unbilled')
            with self.assertRaises(budget.AlreadyDispatched):self.dispatch(ledger)
            self.reserve(ledger,job='never-sent',sha='b'*64);ledger.cancel_unstarted('never-sent')
            self.assertEqual(ledger.status()['reserved_micro_usd'],0)

    def test_actual_unexpected_usage_is_recorded_and_blocks_future_admission(self):
        with TemporaryDirectory() as folder:
            ledger=self.make(folder);self.reserve(ledger);self.reserve(ledger,job='pending',sha='b'*64)
            self.dispatch(ledger,inputs=1,outputs=1)
            row=ledger.settle('one',response_id='unexpected-provider-usage',usage={'input_tokens':2,'output_tokens':2})
            self.assertTrue(row['policy_violation']);self.assertEqual(row['charged_micro_usd'],11)
            state=ledger.status();self.assertTrue(state['blocked']);self.assertEqual(state['spendable_micro_usd'],0)
            self.assertFalse(state['pending'][0]['can_dispatch'])
            with self.assertRaises(budget.BudgetExceeded):self.reserve(ledger,job='new',sha='c'*64)
            with self.assertRaises(budget.BudgetExceeded):self.dispatch(ledger,job='pending',sha='b'*64)

    def test_unknown_or_nontext_usage_does_not_release_reservation(self):
        with TemporaryDirectory() as folder:
            ledger=self.make(folder);self.reserve(ledger);self.dispatch(ledger)
            for usage in ({'input_tokens':1,'output_tokens':2,'input_tokens_details':{'audio_tokens':1}},
                          {'input_tokens':1,'output_tokens':2,'reasoning_tokens':3},
                          {'input_tokens':1,'output_tokens':2,'cached_input_tokens':2},
                          {'input_tokens':1,'output_tokens':2,'tool_calls':1},
                          {'input_tokens':1,'output_tokens':2,'input_tokens_details':[]}):
                with self.subTest(usage=usage),self.assertRaises(budget.BudgetError):ledger.settle('one',response_id='invalid',usage=usage)
            self.assertEqual(ledger.status()['reserved_micro_usd'],5250)

    def test_duplicate_provider_response_cannot_be_charged_to_two_jobs(self):
        with TemporaryDirectory() as folder:
            ledger=self.make(folder)
            for name,sha in [('one','a'*64),('two','b'*64)]:self.reserve(ledger,name,sha);self.dispatch(ledger,name,sha)
            usage={'input_tokens':10,'output_tokens':10}
            ledger.settle('one',response_id='same-provider-response',usage=usage)
            with self.assertRaises(budget.BudgetConflict):ledger.settle('two',response_id='same-provider-response',usage=usage)
            self.assertEqual(ledger.status()['reserved_micro_usd'],5250)

    def test_real_cross_process_reservations_cannot_overspend_shared_cap(self):
        with TemporaryDirectory() as folder:
            path=str(Path(folder)/'budget.sqlite3');self.make(folder,cap='0.10')
            context=multiprocessing.get_context('spawn');barrier=context.Barrier(2);results=context.Queue()
            workers=[context.Process(target=_compete,args=(path,barrier,results,i)) for i in (1,2)]
            for worker in workers:worker.start()
            for worker in workers:worker.join(20);self.assertEqual(worker.exitcode,0)
            outcomes=sorted(results.get(timeout=3) for _ in workers)
            self.assertEqual(outcomes,['budget_exhausted','reserved'])
            state=budget.BudgetLedger(path,cap_usd='0.10').status()
            self.assertLessEqual(state['charged_micro_usd']+state['reserved_micro_usd'],100_000)
            self.assertEqual(state['reserved_micro_usd'],81_750)


if __name__=='__main__':unittest.main()
