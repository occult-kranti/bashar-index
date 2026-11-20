"""Durable shared USD cap for post-collection text research, without HTTP or secrets.

Reserve worst-case tokens, commit mark_dispatched BEFORE the one paid call,
then settle provider usage. A timeout/crash after dispatch never auto-retries
or releases money. The caller owns phase, request bytes, credentials and HTTP.

Fixed reviewed standard/global text policy:
https://developers.openai.com/api/docs/models/gpt-5.4-mini
Reasoning tokens are included in output usage, not billed a second time:
https://developers.openai.com/api/docs/guides/reasoning
"""
from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
import uuid
from types import MappingProxyType

MODEL='gpt-5.4-mini-2026-03-17'
MICRO=1_000_000
GLOBAL_CAP_MICRO_USD=100*MICRO
POLICY=MappingProxyType({'schema_version':1,'currency':'USD','model':MODEL,'service_tier':'default','pricing_region':'global',
    'input_micro_usd_per_million':750_000,'cached_input_micro_usd_per_million':75_000,
    'output_micro_usd_per_million':4_500_000,'context_limit_tokens':400_000,'maximum_output_tokens':128_000,
    'reasoning_included_in_output_tokens':True,'modalities':('text',),'tools':(),
    'source':'https://developers.openai.com/api/docs/models/gpt-5.4-mini',
    'rounding':'ceiling_to_micro_USD_once_per_request'})


def _encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
POLICY_JSON=_encoded(dict(POLICY))
POLICY_SHA256=hashlib.sha256(POLICY_JSON.encode()).hexdigest()


class BudgetError(ValueError):pass
class BudgetExceeded(BudgetError):pass
class BudgetConflict(BudgetError):pass
class AlreadyDispatched(BudgetError):pass


def _need(ok,message,kind=BudgetError):
    if not ok:raise kind(message)


def _integer(value,name,minimum=0):
    _need(type(value) is int and value>=minimum,name+'_must_be_nonnegative_integer')
    return value


def usd_to_micro(value):
    _need(not isinstance(value,(float,bool)),'USD_requires_exact_decimal_or_string')
    try:d=Decimal(value)
    except (InvalidOperation,ValueError,TypeError) as error:raise BudgetError('invalid_USD_amount') from error
    _need(d.is_finite() and d>=0 and d*MICRO==(d*MICRO).to_integral_value(),'USD_must_be_finite_exact_microdollars')
    return int(d*MICRO)


def micro_to_usd(value):
    _integer(value,'micro_USD')
    return f'{value//MICRO}.{value%MICRO:06d}'


def _identity(value,name,*,digest=False):
    _need(isinstance(value,str) and (bool(re.fullmatch('[0-9a-f]{64}',value)) if digest else bool(value.strip()) and len(value)<=200),name+'_invalid')
    return value


def _limits(model,input_tokens,output_tokens):
    _need(model==MODEL,'unreviewed_model_or_alias')
    _integer(input_tokens,'max_input_tokens',1);_integer(output_tokens,'max_output_tokens',1)
    _need(output_tokens<=POLICY['maximum_output_tokens'] and input_tokens+output_tokens<=POLICY['context_limit_tokens'],'model_token_limit_exceeded')


def normalize_usage(raw):
    """Responses-style or normalized text usage; reasoning remains within output."""
    _need(isinstance(raw,dict),'usage_object_required')
    allowed={'input_tokens','output_tokens','total_tokens','input_tokens_details','output_tokens_details','cached_input_tokens','reasoning_tokens'}
    _need(not set(raw)-allowed,'unpriced_or_unknown_usage_field')
    inputs=_integer(raw.get('input_tokens'),'input_tokens');outputs=_integer(raw.get('output_tokens'),'output_tokens')
    inp=raw.get('input_tokens_details');out=raw.get('output_tokens_details')
    inp={} if inp is None else inp;out={} if out is None else out
    _need(isinstance(inp,dict) and isinstance(out,dict),'token_detail_object_required')
    _need(not set(inp)-{'cached_tokens'} and not set(out)-{'reasoning_tokens'},'nontext_or_unpriced_token_details')
    cached=_integer(raw.get('cached_input_tokens',inp.get('cached_tokens',0)),'cached_input_tokens')
    reasoning=_integer(raw.get('reasoning_tokens',out.get('reasoning_tokens',0)),'reasoning_tokens')
    if 'cached_tokens' in inp:_need(cached==inp['cached_tokens'],'conflicting_cached_usage')
    if 'reasoning_tokens' in out:_need(reasoning==out['reasoning_tokens'],'conflicting_reasoning_usage')
    _need(cached<=inputs and reasoning<=outputs,'usage_subsets_exceed_total')
    if 'total_tokens' in raw:_need(type(raw['total_tokens']) is int and raw['total_tokens']==inputs+outputs,'usage_total_mismatch')
    return {'input_tokens':inputs,'cached_input_tokens':cached,'output_tokens':outputs,'reasoning_tokens':reasoning}


def usage_cost_micro_usd(usage):
    u=normalize_usage(usage)
    numerator=((u['input_tokens']-u['cached_input_tokens'])*POLICY['input_micro_usd_per_million']+
               u['cached_input_tokens']*POLICY['cached_input_micro_usd_per_million']+
               u['output_tokens']*POLICY['output_micro_usd_per_million'])
    return (numerator+MICRO-1)//MICRO


class BudgetLedger:
    """One canonical SQLite path must be shared by every research process.

    States: reserved -> in_flight -> charged, or in_flight -> uncertain ->
    charged/unbilled. Only reserved can be cancelled. No state authorizes a
    second dispatch of an existing job, and pending money has no expiry.
    """
    def __init__(self,path,cap_usd='100.00'):
        self.path=Path(path).resolve();self.cap=usd_to_micro(cap_usd)
        _need(0<self.cap<=GLOBAL_CAP_MICRO_USD,'cap_must_not_exceed_global_100_USD')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        # A process can open an existing WAL or rollback-journal database.
        # Switching journal modes while a second worker opens the ledger can
        # fail before SQLite's transaction busy timeout takes effect.
        with self._transaction() as c:
            c.execute('CREATE TABLE IF NOT EXISTS metadata (singleton INTEGER PRIMARY KEY CHECK(singleton=1), cap INTEGER NOT NULL, policy_sha256 TEXT NOT NULL, policy_json TEXT NOT NULL)')
            c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,reservation_id TEXT NOT NULL UNIQUE,request_sha256 TEXT NOT NULL,
                model TEXT NOT NULL,max_input INTEGER NOT NULL,max_output INTEGER NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('reserved','in_flight','uncertain','charged','cancelled','unbilled')),
                reserved INTEGER NOT NULL CHECK(reserved>=0),charged INTEGER NOT NULL DEFAULT 0 CHECK(charged>=0),
                dispatch_id TEXT UNIQUE,response_id TEXT UNIQUE,input_bound INTEGER,output_limit INTEGER,
                usage_json TEXT,reason_code TEXT,resolution_evidence_sha256 TEXT,
                policy_violation INTEGER NOT NULL DEFAULT 0 CHECK(policy_violation IN (0,1)),created REAL NOT NULL,updated REAL NOT NULL)''')
            old=c.execute('SELECT * FROM metadata WHERE singleton=1').fetchone()
            if old is None:c.execute('INSERT INTO metadata VALUES(1,?,?,?)',(self.cap,POLICY_SHA256,POLICY_JSON))
            else:_need(old['cap']==self.cap and old['policy_sha256']==POLICY_SHA256 and old['policy_json']==POLICY_JSON,'immutable_budget_cap_or_price_policy_changed',BudgetConflict)
            c.execute("CREATE TRIGGER IF NOT EXISTS immutable_policy_update BEFORE UPDATE ON metadata BEGIN SELECT RAISE(ABORT,'immutable budget policy'); END")
            c.execute("CREATE TRIGGER IF NOT EXISTS immutable_policy_delete BEFORE DELETE ON metadata BEGIN SELECT RAISE(ABORT,'immutable budget policy'); END")

    def _connect(self):
        c=sqlite3.connect(self.path,timeout=10,isolation_level=None);c.row_factory=sqlite3.Row
        c.execute('PRAGMA busy_timeout=10000');c.execute('PRAGMA synchronous=FULL');return c

    @contextmanager
    def _transaction(self):
        c=self._connect()
        try:
            c.execute('BEGIN IMMEDIATE');yield c;c.commit()
        except BaseException:c.rollback();raise
        finally:c.close()

    @staticmethod
    def _job(c,job_id):
        row=c.execute('SELECT * FROM jobs WHERE job_id=?',(job_id,)).fetchone()
        _need(row is not None,'unknown_job');return row

    @staticmethod
    def _public(row):
        result={'job_id':row['job_id'],'reservation_id':row['reservation_id'],'request_sha256':row['request_sha256'],
            'model':row['model'],'state':row['state'],'max_input_tokens':row['max_input'],'max_output_tokens':row['max_output'],
            'reserved_micro_usd':row['reserved'],'reserved_usd':micro_to_usd(row['reserved']),
            'held_micro_usd':row['reserved'] if row['state'] in ('reserved','in_flight','uncertain') else 0,
            'charged_micro_usd':row['charged'],'charged_usd':micro_to_usd(row['charged']),
            'dispatch_id':row['dispatch_id'],'response_id':row['response_id'],'reason_code':row['reason_code'],
            'dispatched_input_tokens_upper_bound':row['input_bound'],'dispatched_max_output_tokens':row['output_limit'],
            'can_dispatch':row['state']=='reserved','automatic_retry_allowed':False,
            'policy_sha256':POLICY_SHA256,'policy_violation':bool(row['policy_violation'])}
        if row['usage_json']:result['usage']=json.loads(row['usage_json'])
        return result

    @staticmethod
    def _totals(c):
        row=c.execute("SELECT COALESCE(SUM(charged),0) charged,COALESCE(SUM(CASE WHEN state IN ('reserved','in_flight','uncertain') THEN reserved ELSE 0 END),0) reserved,COALESCE(MAX(policy_violation),0) violated FROM jobs").fetchone()
        return row['charged'],row['reserved'],bool(row['violated'])

    def reserve(self,job_id,*,request_sha256,max_input_tokens,max_output_tokens,model=MODEL):
        _identity(job_id,'job_id');_identity(request_sha256,'request_sha256',digest=True)
        _limits(model,max_input_tokens,max_output_tokens)
        amount=usage_cost_micro_usd({'input_tokens':max_input_tokens,'output_tokens':max_output_tokens})
        with self._transaction() as c:
            old=c.execute('SELECT * FROM jobs WHERE job_id=?',(job_id,)).fetchone()
            if old is not None:
                _need((old['request_sha256'],old['model'],old['max_input'],old['max_output'])==
                    (request_sha256,model,max_input_tokens,max_output_tokens),'job_id_reused_for_different_request',BudgetConflict)
                result=self._public(old)
                charged,reserved,violated=self._totals(c)
                result['can_dispatch']=result['can_dispatch'] and not violated and charged+reserved<=self.cap
                return result
            charged,reserved,violated=self._totals(c)
            _need(not violated,'prior_usage_bound_violation_blocks_new_calls',BudgetExceeded)
            _need(charged+reserved+amount<=self.cap,'shared_USD_budget_exhausted',BudgetExceeded)
            now=time.time();c.execute('INSERT INTO jobs(job_id,reservation_id,request_sha256,model,max_input,max_output,state,reserved,created,updated) VALUES(?,?,?,?,?,?,\'reserved\',?,?,?)',
                (job_id,uuid.uuid4().hex,request_sha256,model,max_input_tokens,max_output_tokens,amount,now,now))
            return self._public(self._job(c,job_id))

    def mark_dispatched(self,job_id,*,request_sha256,input_tokens_upper_bound,max_output_tokens,
                        service_tier='default',tools=(),modalities=('text',),store=False,pricing_region='global'):
        _identity(request_sha256,'request_sha256',digest=True)
        _integer(input_tokens_upper_bound,'input_tokens_upper_bound');_integer(max_output_tokens,'max_output_tokens',1)
        _need(service_tier=='default' and pricing_region=='global' and store is False,'standard_global_private_text_policy_required')
        _need(isinstance(tools,(list,tuple)) and len(tools)==0 and isinstance(modalities,(list,tuple)) and list(modalities)==['text'],'tools_and_nontext_modalities_forbidden')
        with self._transaction() as c:
            row=self._job(c,job_id)
            _need(row['state']=='reserved','job_already_dispatched_or_terminal_no_retry',AlreadyDispatched)
            _need(row['request_sha256']==request_sha256,'dispatch_request_fingerprint_mismatch',BudgetConflict)
            _need(input_tokens_upper_bound<=row['max_input'] and max_output_tokens<=row['max_output'],'request_exceeds_reserved_token_bounds')
            charged,reserved,violated=self._totals(c)
            _need(not violated and charged+reserved<=self.cap,'shared_budget_blocked',BudgetExceeded)
            c.execute("UPDATE jobs SET state='in_flight',dispatch_id=?,input_bound=?,output_limit=?,updated=? WHERE job_id=?",
                (uuid.uuid4().hex,input_tokens_upper_bound,max_output_tokens,time.time(),job_id))
            return self._public(self._job(c,job_id))

    def mark_uncertain(self,job_id,reason_code):
        _need(isinstance(reason_code,str) and re.fullmatch('[A-Za-z0-9_.-]{1,128}',reason_code),'safe_uncertainty_reason_code_required')
        with self._transaction() as c:
            row=self._job(c,job_id);_need(row['state'] in ('in_flight','uncertain'),'only_dispatched_jobs_can_be_uncertain')
            if row['state']=='uncertain':_need(row['reason_code']==reason_code,'uncertainty_reason_changed',BudgetConflict)
            c.execute("UPDATE jobs SET state='uncertain',reason_code=?,updated=? WHERE job_id=?",(reason_code,time.time(),job_id))
            return self._public(self._job(c,job_id))

    def settle(self,job_id,*,response_id,usage):
        _identity(response_id,'response_id');normalized=normalize_usage(usage);encoded=_encoded(normalized);cost=usage_cost_micro_usd(normalized)
        with self._transaction() as c:
            row=self._job(c,job_id)
            if row['state']=='charged':
                _need(row['response_id']==response_id and row['usage_json']==encoded,'charged_job_response_or_usage_changed',BudgetConflict)
                return self._public(row)
            _need(row['state'] in ('in_flight','uncertain'),'usage_requires_a_durable_dispatch')
            other=c.execute('SELECT job_id FROM jobs WHERE response_id=?',(response_id,)).fetchone()
            _need(other is None,'response_id_already_charged_to_another_job',BudgetConflict)
            violation=(normalized['input_tokens']>row['input_bound'] or normalized['output_tokens']>row['output_limit'] or cost>row['reserved'])
            # A real unexpected liability must not disappear in a rolled-back
            # exception. Record it, then block every future paid admission.
            c.execute("UPDATE jobs SET state='charged',charged=?,response_id=?,usage_json=?,policy_violation=?,reason_code=?,updated=? WHERE job_id=?",
                (cost,response_id,encoded,int(violation),'actual_usage_exceeded_preflight_bound' if violation else None,time.time(),job_id))
            return self._public(self._job(c,job_id))

    def cancel_unstarted(self,job_id):
        with self._transaction() as c:
            row=self._job(c,job_id)
            _need(row['state'] in ('reserved','cancelled'),'dispatched_or_uncertain_money_cannot_be_cancelled')
            c.execute("UPDATE jobs SET state='cancelled',updated=? WHERE job_id=?",(time.time(),job_id))
            return self._public(self._job(c,job_id))

    def confirm_unbilled(self,job_id,*,evidence_sha256):
        """Explicit external reconciliation only; the same job still cannot retry."""
        _identity(evidence_sha256,'resolution_evidence_sha256',digest=True)
        with self._transaction() as c:
            row=self._job(c,job_id);_need(row['state'] in ('uncertain','unbilled'),'explicit_uncertain_reconciliation_required')
            if row['state']=='unbilled':_need(row['resolution_evidence_sha256']==evidence_sha256,'unbilled_evidence_changed',BudgetConflict)
            c.execute("UPDATE jobs SET state='unbilled',resolution_evidence_sha256=?,updated=? WHERE job_id=?",(evidence_sha256,time.time(),job_id))
            return self._public(self._job(c,job_id))

    def status(self):
        with self._transaction() as c:
            charged,reserved,violated=self._totals(c);available=max(0,self.cap-charged-reserved)
            pending=[self._public(row) for row in c.execute("SELECT * FROM jobs WHERE state IN ('reserved','in_flight','uncertain') ORDER BY created,job_id")]
            blocked=violated or charged+reserved>self.cap
            if blocked:
                for row in pending:row['can_dispatch']=False
            return {'schema_version':1,'currency':'USD','model':MODEL,'policy_sha256':POLICY_SHA256,
                'cap_micro_usd':self.cap,'cap_usd':micro_to_usd(self.cap),
                'charged_micro_usd':charged,'charged_usd':micro_to_usd(charged),
                'reserved_micro_usd':reserved,'reserved_usd':micro_to_usd(reserved),
                'available_micro_usd':available,'available_usd':micro_to_usd(available),
                'overrun_micro_usd':max(0,charged+reserved-self.cap),'blocked':blocked,
                'spendable_micro_usd':0 if blocked else available,
                'pending':pending,'automatic_retry_of_dispatched_jobs_allowed':False}
