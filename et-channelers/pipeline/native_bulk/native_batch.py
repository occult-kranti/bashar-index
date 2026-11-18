"""Two isolated stock-WPC native downloaders under one explicit batch lease.

Importing starts nothing. This does not resume old collectors or clear their
source refusals. See NATIVE_BATCH.md for the separate admission contract.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time

PUBLIC_PIPE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PUBLIC_PIPE));sys.path.insert(1,str(Path(__file__).resolve().parent))
import drive_ingest as storage
from native_batch_job import OwnedJob
from gpu_asr import encoded
import importlib.util

def _private(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
http_policy=_private('owned_native_http_bulk_policy','native_http_policy.py')
worker=_private('owned_native_worker_bulk','native_batch_worker.py')
bulk_contract=worker.bulk_contract()
ingestion_status=_private('owned_bulk_frozen_ingestion_coverage','frozen_ingestion_coverage.py')
worker_diagnostics=_private('owned_bulk_worker_diagnostics','worker_diagnostics.py')

MAX_SPOOL = 6_000_000_000
MAX_ASSET = 2_000_000_000
HEADROOM = 240_000_000
MANAGED = 16_000_000_000
FREE = 2_000_000_000
WINDOWS = os.name == 'nt'
SOURCE_FAILURES = {'source_403', 'source_429', 'bot_check', 'protection_failure', 'access_challenge'}
need, read, write, digest = worker.need, worker.read, worker.write, worker.digest


def handoff_module():
    try: from . import native_asr_handoff
    except ImportError: import native_asr_handoff
    return native_asr_handoff


def handoff_settings(root, remote, value):
    if value is None: return None
    fields = {'owner', 'lease_id', 'cap_bytes', 'max_pairs', 'retain_policy', 'capacity_wait_seconds', 'caption_bundle_paths'}
    need(type(value) is dict and set(value) <= fields and fields - {'caption_bundle_paths'} <= set(value), 'handoff_settings')
    need(value['retain_policy'] == 'explicit_original_english_v1' and
         type(value['capacity_wait_seconds']) is int and 1 <= value['capacity_wait_seconds'] <= 1800, 'handoff_settings')
    paths = value.get('caption_bundle_paths', {})
    need(type(paths) is dict and len(paths) <= 20 and all(
        isinstance(k, str) and re.fullmatch(r'[A-Za-z0-9_-]{11}', k) and type(v) is dict and len(v) <= 100 and
        all(isinstance(track, str) and isinstance(path, str) and len(path) <= 2048 for track, path in v.items())
        for k, v in paths.items()), 'handoff_caption_paths')
    return handoff_module().Settings(root=root, remote=remote,
        **{k: value[k] for k in ('owner', 'lease_id', 'cap_bytes', 'max_pairs', 'retain_policy')})


def load_plan(path):
    plan = read(path)
    items = plan.get('items', [])
    need(plan.get('schema_version') == 1 and 1 <= len(items) <= 20, 'plan_size')
    seen = set()
    for item in items:
        ident, channel = item.get('video_id', ''), item.get('channel_dir', '')
        row = item.get('queue_row', {})
        need(re.fullmatch(r'[A-Za-z0-9_-]{11}', ident) and ident not in seen and
             re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', channel) and
             item.get('video_url') == 'https://www.youtube.com/watch?v=' + ident and
             item.get('tab') in storage.SOURCE_FOLDERS and row.get('video_id') == ident and
             row.get('channel_dir') == channel and row.get('tab') == item['tab'] and
             hashlib.sha256(encoded(row)).hexdigest() == item.get('queue_row_sha256'), 'plan_target')
        duration = item.get('duration_seconds')
        need(duration is None or (type(duration) in (int, float) and math.isfinite(duration) and duration > 0), 'plan_duration')
        seen.add(ident)
    return digest(path), items


def source_error(result):
    value = result.get('diagnostics', {}).get('error_class')
    return value if value in SOURCE_FAILURES else None


def capacity_snapshot(root, spool, active_folders):
    """Count inactive files once; active child folders are charged full slots.

    Children cannot share a Python lock. Never combine their bytes measured at
    different instants with a sampled remaining reservation.
    """
    root, spool = Path(root).resolve(), Path(spool).resolve()
    active = {Path(p).resolve() for p in active_folders}
    need(all(p.is_relative_to(spool) and p != spool for p in active), 'capacity_scope')
    private_bytes = spool_bytes = 0
    for folder, directories, files in os.walk(root):
        base = Path(folder)
        for name in list(directories):
            path = base / name
            need(not storage.is_link(path), 'storage_link')
            if path in active: directories.remove(name)
        for name in files:
            path = base / name
            need(not storage.is_link(path), 'storage_link')
            try: size = path.stat().st_size
            except FileNotFoundError: continue
            private_bytes += size
            if path.is_relative_to(spool): spool_bytes += size
    return {'inactive_private_bytes': private_bytes, 'inactive_spool_bytes': spool_bytes}


class SlotBudget(storage.Budget):
    """Reuse reservation checks with the coordinator's partitioned snapshot."""
    inactive_bytes = 0

    def usage(self, reconcile=False):
        return self.inactive_bytes

    def _outstanding(self, omit=None):
        return sum(item['bytes'] for key, item in self.active.items() if key != omit)


def exception_diagnostic(error):
    allowed = {'PermissionError', 'FileNotFoundError', 'OSError', 'TimeoutError', 'RuntimeError', 'Held'}
    result = {'exception_class': type(error).__name__ if type(error).__name__ in allowed else 'OtherError'}
    for field in ('errno', 'winerror'):
        value = getattr(error, field, None)
        if type(value) is int and 0 <= value <= 65535: result[field] = value
    frames=[];tb=error.__traceback__
    allowed_modules={'native_batch.py','native_batch_worker.py','drive_ingest.py','pathlib.py','shutil.py','bulk_contract.py','native_http_policy.py','native_batch_job.py','native_audio_sink.py','worker_diagnostics.py'}
    while tb is not None and len(frames)<8:
        name=Path(tb.tb_frame.f_code.co_filename).name
        row={'module':name if name in allowed_modules else 'other_module','line':int(tb.tb_lineno)}
        function=tb.tb_frame.f_code.co_name
        if name in allowed_modules and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}',function):row['function']=function
        frames.append(row);tb=tb.tb_next
    result['frames']=frames
    return result


def cleanup_profile(profile, folder, processes_gone, *, remove=shutil.rmtree, sleep=time.sleep, clock=time.monotonic):
    """Bounded filesystem-only retries after the actual owned Job is empty.

    Only Win32 sharing/lock violations32/33 are retryable. The15.5s window
    bounds retry scheduling; a blocking filesystem call itself is not canceled.
    No Source request, forced unlock, ACL change or unowned kill occurs here.
    """
    started=clock();window=15.5
    result={'attempts':0,'cleaned':False,'failures':[],'first_failure':None,
            'retry_window_seconds':window,'scheduled_sleep_seconds':0.0}
    def owned_path():
        need(processes_gone and profile.resolve().parent==folder.resolve() and not profile.is_symlink() and
             not getattr(profile,'is_junction',lambda:False)(),'cleanup_path')
    def finish(reason=None):
        result['elapsed_seconds']=max(0,clock()-started)
        if reason is not None:result['stop_reason']=reason
        if not result['cleaned']:result['retained_for_owner_cleanup']=True
        return result
    owned_path()
    if not profile.exists():result['cleaned']=True;return finish()
    for delay in (0,.5,1,2,4,8):
        if delay:
            remaining=window-(clock()-started)
            if remaining<=0:return finish('retry_window_exhausted')
            actual=min(delay,remaining);sleep(actual);result['scheduled_sleep_seconds']+=actual
        owned_path();result['attempts']+=1
        try:
            remove(profile);result['cleaned']=not profile.exists()
            return finish(None if result['cleaned'] else 'profile_still_exists')
        except OSError as error:
            failure=exception_diagnostic(error);result['failures'].append(failure)
            if result['first_failure'] is None:result['first_failure']=failure
            if not profile.exists():result['cleaned']=True;return finish('profile_absent_after_failure')
            if getattr(error,'winerror',None) not in {32,33}:return finish('nonsharing_error_no_retry')
    return finish('retry_window_exhausted')


def check_pair_proofs(proofs, record):
    for key, expected in (('audio', record), ('metadata', record['metadata'])):
        storage.verify_remote(proofs[key], expected)
        need(bool(proofs[key].get('ID')), 'drive_identity_missing')
    need(proofs['audio']['ID'] != proofs['metadata']['ID'], 'drive_identity_duplicate')


def validate_record(record, item, folder, root, remote, plan_sha):
    ident = item['video_id']
    extension = Path(record.get('path', '')).suffix.lstrip('.')
    metadata = record.get('metadata') or {}
    need(record.get('video_id') == ident and record.get('channel_dir') == item['channel_dir'] and
         record.get('tab') == item['tab'] and record.get('native_batch_profile') == worker.PROFILE and
         record.get('native_batch_plan_sha256') == plan_sha and extension in {'m4a', 'webm'}, 'checkpoint_identity')
    expected_audio = folder / (ident + '.' + extension)
    expected_metadata = folder / (ident + '.info.json')
    need(record.get('path') == expected_audio.relative_to(root).as_posix() and
         metadata.get('path') == expected_metadata.relative_to(root).as_posix() and
         record.get('remote') == storage.remote_path(remote, item, extension) and
         metadata.get('remote') == storage.remote_path(remote, item, 'info.json'), 'checkpoint_paths')
    for proof in (record, metadata):
        need(type(proof.get('bytes')) is int and proof['bytes'] > 0 and
             isinstance(proof.get('md5'), str) and re.fullmatch(r'[0-9a-f]{32}', proof['md5']) and
             isinstance(proof.get('sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', proof['sha256']), 'checkpoint_proof')


class NativeBatch:
    def __init__(self, settings_path, drive=None):
        self.settings_path = Path(settings_path).resolve()
        self.s = read(self.settings_path)
        self.root = Path(self.s['private_root']).resolve()
        self.plan_sha, self.items = load_plan(self.s['plan_path'])
        self.spool = self.root / 'stock_wpc_batch_v5_bulk_recovery5'
        self.jobs = self.spool / 'jobs' / self.plan_sha[:16]
        controls = worker.control_paths(self.root)
        self.lease_path = controls['lease_path']
        self.stop_path = controls['batch_stop_path']
        self.cooldown_path = controls['source_cooldown_path']
        self.http_state_path = controls['http_state_path']
        self.state_path = self.root / 'sync/drive_ingest_manifest.jsonl'
        self.batch_journal = self.root / 'sync/stock_wpc_batch_v5_bulk_recovery5_manifest.jsonl'
        self.lock = threading.RLock(); self.source_stop = threading.Event()
        self.dispatch_paused = threading.Event()
        self.handoff = handoff_settings(self.root, self.s['remote'], self.s.get('asr_handoff'))
        self.last_guard = self.last_inventory = 0; self.lease = None
        self.live_reservations = {}; self.live_captures = {}; self.budget = None;self.adaptive_pause_until=0
        self._partition_cache=None;self._partition_key=None;self._partition_at=0
        self.external = self.others = 0
        need(type(self.s.get('workers')) is int and 1 <= self.s['workers'] <= 2, 'worker_count')
        need(type(self.s.get('max_asset_bytes')) is int and 0 < self.s['max_asset_bytes'] <= MAX_ASSET and
             type(self.s.get('spool_cap_bytes')) is int and 2 * (self.s['max_asset_bytes'] + HEADROOM) <= self.s['spool_cap_bytes'] <= MAX_SPOOL,
             'spool_admission')
        need(type(self.s.get('job_wall_seconds')) is int and 600 <= self.s['job_wall_seconds'] <= 7200, 'job_deadline')
        roots = [Path(p).resolve() for p in self.s['managed_roots']]
        need(len(roots) == len(set(roots)) == 6 and any('ms-playwright' in p.parts for p in roots) and
             all(not p.is_relative_to(q) for p in roots for q in roots if p != q), 'managed_roots')
        need(all(any(p.is_relative_to(q) for q in roots) for p in (self.root, Path(__file__).resolve(), Path(self.s['python_executable']).resolve())), 'managed_roots')
        self.roots = roots
        required={Path(__file__).with_name(name).resolve() for name in ('native_batch_worker.py','native_http_policy.py','native_http_policy_v4_frozen.py','bulk_contract.py','native_bulk_controller.py','frozen_ingestion_coverage.py')}
        required.update((PUBLIC_PIPE/name).resolve() for name in ('native_batch_quality.py','native_batch_job.py','native_track_policy.py','xtags_decode.py','drive_ingest.py','media_metadata.py','native_audio_sink.py','native_metadata_snapshot.py','publisher_mirror.py','chromium_capture_service.py'))
        need(self.handoff is None,'v5_no_asr_handoff')
        if self.handoff:
            required.update(Path(__file__).with_name(name).resolve() for name in (
                'native_asr_handoff.py', 'gpu_asr_queue.py', 'gpu_asr_provenance.json', 'gpu_asr_multilingual_provenance.json'))
            need(set(self.s['asr_handoff'].get('caption_bundle_paths', {})) <= {i['video_id'] for i in self.items}, 'handoff_caption_scope')
        supplied = {Path(pin['path']).resolve() for pin in self.s['code_pins']}
        need(required <= supplied, 'required_code_pins')
        need(Path(self.s['pipeline_directory']).resolve() == Path(__file__).parent.resolve(), 'pipeline_directory')
        self.http_seed = self.s['http_policy_seed']
        self.http_review_pin = self.s['historical_http_review']
        for pin in (self.http_seed, self.http_review_pin):
            need(digest(pin['path']) == pin['sha256'], 'http_policy_proposal_changed')
        self.http_review = dict(read(self.http_review_pin['path']), review_sha256=self.http_review_pin['sha256'])
        need({i['video_id'] for i in self.items} <= set(self.http_review['allowed_video_ids']), 'http_review_plan_binding')
        self.drive = drive or storage.Rclone(self.s['rclone'], self.s.get('rclone_config'), self.root / 'sync/drive_ingest_cooldown.json')

    def partition_key(self):
        active=tuple(sorted((key,str(value['folder'].resolve()),value['bytes']) for key,value in self.live_reservations.items()))
        commitments=tuple(sorted((key,value['bytes']) for key,value in self.budget.active.items())) if self.budget else ()
        return active,commitments

    def invalidate_partition(self):
        self._partition_cache=None;self._partition_key=None;self._partition_at=0

    def capacity_partition(self,*,force=False):
        key=self.partition_key();now=time.monotonic()
        if force or self._partition_cache is None or self._partition_key!=key or now-self._partition_at>=12:
            value=capacity_snapshot(self.root,self.spool,[row['folder'] for row in self.live_reservations.values()])
            self._partition_cache=dict(value);self._partition_key=key;self._partition_at=time.monotonic()
        return dict(self._partition_cache)

    def release_after_reconcile(self,ident):
        # Caller holds dispatch lock. Include the finalized folder as inactive
        # BEFORE releasing its full slot, while still excluding active siblings.
        self.invalidate_partition()
        remaining=[row['folder'] for key,row in self.live_reservations.items() if key!=ident]
        try:
            value=capacity_snapshot(self.root,self.spool,remaining)
            self.budget.inactive_bytes=value['inactive_private_bytes']
            self.budget.release(ident);self.live_reservations.pop(ident,None)
            self._partition_cache=dict(value);self._partition_key=self.partition_key();self._partition_at=time.monotonic()
        except BaseException:
            self.source_stop.set()
            if not self.stop_path.exists():self.stop_path.write_bytes(b'bulk accounting reconciliation failed; Root review required\n')
            raise

    def policy_envelope(self):
        envelope=read(self.http_state_path);seed=read(self.http_seed['path'])
        need(envelope.get('schema_version')==5 and envelope.get('seed_sha256')==self.http_seed['sha256'],'http_state_binding')
        http_policy.state(envelope['state'])
        need(envelope['state']['inherited_v4_envelope']==seed['state']['inherited_v4_envelope'] and envelope['state']['inherited_consecutive_tail']==seed['state']['inherited_consecutive_tail'] and envelope['state']['root_review_sha256']==self.http_review_pin['sha256'],'inherited_history_changed')
        original=seed['state'];current=envelope['state']
        need(all(current['outcomes'].get(k)==v for k,v in original['outcomes'].items()) and current['next_sequence']>=original['next_sequence'] and (original['circuit_break'] is None or current['circuit_break']==original['circuit_break']),'inherited_outcomes_changed')
        return envelope

    def root_policy_gate(self,lease):
        _,grant=bulk_contract.frame_admission(self.settings_path,lease)
        raw=self.policy_envelope()['state']
        need(grant.get('inherited_v4_sha256')==raw['inherited_v4_sha256'] and grant.get('inherited_consecutive_tail')==raw['inherited_consecutive_tail'],'root_inherited_tail_binding')
        self.http_review['root_override_authorized']=True
        return grant

    def fresh_source_coverage(self,video_id):
        targets,_=ingestion_status.queue_ids(self.root,('queue_newest20_enriched.csv','queue_newest20.csv'))
        latest=ingestion_status.latest_records(self.root/'sync/drive_ingest_manifest.jsonl')
        native={key for key,record in latest.items() if ingestion_status.proof(ingestion_status.receipt_complete,record,ingestion_status.record_row(record),self.s['remote'])}
        publisher=ingestion_status.publisher_coverage(self.root,targets,self.s['remote'])[2]
        mirrors=ingestion_status.publisher_mirror_coverage(self.root,targets,self.s['remote'])[0]
        need(video_id not in native|publisher|mirrors,'source_already_covered')

    def observe_pending_failures(self,extra=None):
        # All currently durable source outcomes are ordered before any new GO.
        records=[]
        for ident,reservation in list(self.live_reservations.items()):
            path=reservation['folder']/'progress.json'
            if path.exists():records.append({'video_id':ident,'diagnostics':read(path)})
        if extra is not None:records.append(extra)
        observations=[]
        for record in records:
            ident=record.get('video_id');diagnostics=record.get('diagnostics',{});attempt=self.jobs/ident/'attempt.json'
            if not attempt.exists():continue
            attempt_sha=digest(attempt)
            success=diagnostics.get('full_native_http_transfer_observed')
            if success is not None:
                at=diagnostics.get('full_native_http_transfer_at_epoch');observations.append((at,ident,attempt_sha,'full_transfer',success))
            failure_slots=[(key,diagnostics.get(key),diagnostics.get(key+'_at_epoch')) for key in ('http_failure','http_escalation') if diagnostics.get(key) is not None]
            global_code=diagnostics.get('global_failure_code')
            if global_code in {'bot_check','protection_failure','access_challenge'}:failure_slots.append(('global_failure',http_policy.global_failure_event(global_code,ident),diagnostics.get('global_failure_at_epoch')))
            if source_error(record) and not failure_slots:self.latch_global(ident,'source_scope_unknown',timestamp_unproven=True);return
            for slot,event,at in failure_slots:observations.append((at,ident,attempt_sha,slot,http_policy.refusal_event(event)))
        if not observations:return
        envelope=self.policy_envelope()
        for at,ident,attempt_sha,slot,outcome in sorted(observations,key=lambda x:(x[0] if type(x[0]) in (int,float) else -1,x[1],x[3])):
            try:
                need(type(at) in (int,float) and math.isfinite(at) and 0<at<=time.time()+5,'source_outcome_timestamp')
                need(outcome.get('video_id')==ident,'source_outcome_target')
                if slot=='full_transfer':
                    need(outcome['proof']['worker_sha256']==digest(worker.__file__) and digest(self.jobs/ident/'selected-metadata.info.json')==outcome['proof']['selected_metadata_sha256'],'transfer_selection_binding')
                    quality=read(self.jobs/ident/'source-quality.json')
                    need(digest(self.jobs/ident/'source-quality.json')==outcome['proof']['quality_proof_sha256'] and digest(PUBLIC_PIPE/'native_batch_quality.py')==outcome['proof']['quality_module_sha256'] and all(quality.get(key)==value for key,value in outcome['proof']['strict_quality'].items()),'transfer_quality_binding')
                event_id=hashlib.sha256(encoded({'plan':self.plan_sha,'video_id':ident,'attempt':attempt_sha,'observation':slot})).hexdigest()
                state=http_policy.apply_outcome(envelope['state'],outcome,event_id,attempt_sha,at)
            except (http_policy.PolicyError,worker.Held):self.latch_global(ident,'source_scope_unknown',timestamp_unproven=True);return
            if state!=envelope['state']:
                write(self.http_state_path,dict(envelope,state=state));envelope['state']=state
                if outcome['kind']=='http_refusal' and outcome['event']['action']=='item_quarantine':self.adaptive_pause_until=max(self.adaptive_pause_until,time.time()+self.s.get('adaptive_pause_seconds',30))
            scope=http_policy.status(state,time.time(),historical_review=self.http_review,candidate_video_id=ident)
            if scope['circuit_break']:
                event=outcome.get('event');self.latch_global(ident,event['code'] if event else 'source_scope_unknown',event=event,event_id=event_id,circuit=scope['circuit_break'])


    def guard(self, *, source=False, force=False, video_id=None, force_inventory=False):
        with self.lock:
            now = time.monotonic()
            if force or now - self.last_guard >= 1:
                lease = read(self.lease_path)
                lease,_ = bulk_contract.frame_admission(self.settings_path,lease)
                need(lease.get('schema_version') == 1 and lease.get('state') == 'active' and lease.get('authorized') is True and
                     lease.get('profile') == worker.PROFILE and lease.get('owner') == self.s['owner'] and lease.get('lease_id') == self.s['lease_id'] and
                     lease.get('settings_sha256') == digest(self.settings_path) and lease.get('plan_sha256') == self.plan_sha == digest(self.s['plan_path']) and
                     lease.get('worker_sha256') == digest(worker.__file__) and lease.get('coordinator_sha256') == digest(__file__) and
                     lease.get('preserve_existing_cooldowns') is True and lease.get('max_workers') == self.s['workers'] and
                     lease.get('spool_cap_bytes') == self.s['spool_cap_bytes'] and lease.get('remote') == self.s['remote'], 'batch_lease')
                need(lease.get('source_scope_authorized') is True, 'source_scope_not_admitted')
                need(lease.get('http_policy_seed_sha256') == self.http_seed['sha256'] and
                     lease.get('historical_http_review_sha256') == self.http_review_pin['sha256'] and
                     lease.get('historical_http_review_authorized') is True, 'historical_http_review_not_admitted')
                for pin in self.s['code_pins'] + self.s['preserved_controls'] + [self.http_seed, self.http_review_pin]:
                    need(digest(pin['path']) == pin['sha256'], 'pinned_dependency_or_history_changed')
                need(self.s['preserved_controls'] and (self.root / 'sync/STOP_DRIVE_INGEST').exists(), 'old_collector_not_parked')
                resource = read(self.root / 'sync/analysis_resource_plan.json')
                need(resource.get('collector_dispatch_allowed') is False and 0 < resource.get('accounting_cap_bytes', 0) <= MANAGED, 'resource_policy')
                reservations = resource.get('reservations', [])
                own = [x for x in reservations if x.get('state') == 'active' and x.get('lease_id') == self.s['lease_id'] and x.get('owner') == self.s['owner']]
                need(len(own) == 1 and own[0].get('max_bytes', 0) >= self.s['spool_cap_bytes'], 'resource_reservation')
                self.others = sum(x['max_bytes'] for x in reservations if x.get('state') == 'active' and x.get('lease_id') != self.s['lease_id'])
                self.cap = resource['accounting_cap_bytes']; self.lease = lease; self.root_policy_gate(lease); self.last_guard = now
                if getattr(self, 'handoff', None): handoff_module().admission_lease(self.handoff)
            need(type(self.lease.get('expires_at_epoch')) in (int, float) and time.time() < self.lease['expires_at_epoch'], 'lease_expired')
            if source:
                self.observe_pending_failures()
                self.observe_worker_diagnostics()
                if video_id is not None and not (self.jobs/video_id/'GO').exists():self.fresh_source_coverage(video_id)
                need(not self.source_stop.is_set() and not self.stop_path.exists(), 'batch_source_stopped')
                if self.cooldown_path.exists():
                    need(read(self.cooldown_path).get('retry_not_before_epoch', 0) <= time.time(), 'batch_source_cooldown')
                need(video_id in self.http_review['allowed_video_ids'], 'http_review_target_not_admitted')
                scope = http_policy.status(self.policy_envelope()['state'], time.time(),
                    historical_review=self.http_review, candidate_video_id=video_id)
                need(scope['dispatch_allowed'], 'item_quarantined' if scope['item_quarantined'] else 'http_policy_stopped')
            if force_inventory or now - self.last_inventory >= 12:
                self.external = sum(storage.tree_bytes(p) for p in self.roots if p != self.root)
                self.last_inventory = now
            limit = self.cap - self.external - self.others
            need(limit > storage.JOURNAL_RESERVE and shutil.disk_usage(self.root).free >= FREE, 'managed_storage')
            if self.budget:
                self.budget.cap = limit
                self.capacity = self.capacity_partition()
                self.budget.inactive_bytes = self.capacity['inactive_private_bytes']
                self.capacity.update(active_reserved_bytes=self.budget._outstanding(),
                    private_limit_bytes=limit - storage.JOURNAL_RESERVE, spool_limit_bytes=self.s['spool_cap_bytes'])
                for projected, ceiling, code in (
                    (self.budget.usage() + self.budget._outstanding(), limit - storage.JOURNAL_RESERVE, 'managed_storage'),
                    (self.capacity['inactive_spool_bytes'] + self.budget._outstanding(), self.s['spool_cap_bytes'], 'spool_storage')):
                    if projected > ceiling:
                        error = worker.Held(code); error.capacity_evidence = dict(self.capacity, projected_bytes=projected)
                        raise error
            return limit

    def refuse(self,result):
        with self.lock:self.observe_pending_failures(extra=result)

    def latch_global(self, ident, error, *, event=None, event_id=None, circuit=None, timestamp_unproven=False):
        self.source_stop.set()
        if not self.cooldown_path.exists():
            write(self.cooldown_path, {'schema_version': 1, 'profile': worker.PROFILE,
                'plan_sha256': self.plan_sha, 'error_class': error,
                'retry_not_before_epoch': max(time.time() + 86400, (event or {}).get('retry_not_before_epoch') or 0),
                'source_scope': 'stock_wpc_native_batch_v5', 'requested_video_id': ident,
                'http_event_id': event_id, 'http_failure': event, 'circuit_break': circuit,
                'timestamp_unproven': timestamp_unproven})
        if not self.stop_path.exists():
            with self.stop_path.open('xb') as marker:
                marker.write(b'native v5 global refusal; explicit review required\n'); marker.flush(); os.fsync(marker.fileno())

    def wait_adaptive_dispatch(self,video_id):
        while True:
            with self.lock:
                self.guard(source=True,force=True,video_id=video_id)
                if time.time()>=self.adaptive_pause_until:return
            time.sleep(.25)

    def await_owned_GO(self,ident,folder,process,spawned_at):
        # Parent finishes or holds before the child's existing60s GO wait.
        deadline=spawned_at+worker.GO_WAIT_SECONDS-5
        waited_from=time.monotonic();pause_observed=False
        while True:
            with self.lock:
                self.guard(source=True,force=True,video_id=ident)
                need(not self.dispatch_paused.is_set(),'dispatch_paused')
                need(process.poll() is None,'child_exited_before_GO')
                self.observe_worker_diagnostics()
                need(not self.source_stop.is_set(),'batch_source_stopped')
                need(time.monotonic()<deadline,'pre_GO_dispatch_wait_deadline')
                remaining=self.adaptive_pause_until-time.time()
                if remaining<=0:
                    (folder/'GO').write_bytes(b'owned_job_bound\n')
                    return {'pause_observed':pause_observed,'waited_seconds':time.monotonic()-waited_from,'GO_committed_at_epoch':time.time(),'bounded_seconds':worker.GO_WAIT_SECONDS-5}
                pause_observed=True
            time.sleep(min(.25,max(.001,remaining)))

    def administrative_hold(self,reason):
        self.source_stop.set()
        if not self.stop_path.exists():self.stop_path.write_bytes((reason+'; Root reconciliation required\n').encode())

    def parent_timeout_descriptor(self,ident,folder,result,parent_deadline,parent_error):
        if parent_error not in {'bootstrap_deadline','job_deadline'} or not bulk_contract.parent_deadline_valid(parent_deadline,self.s):return False
        if self.source_stop.is_set() or self.stop_path.exists():return False
        progress=read(folder/'progress.json') if (folder/'progress.json').exists() else {}
        records=[result.get('diagnostics',{}),progress]
        if any(not isinstance(value,dict) or value.get('error_class')=='control_write_failed' or value.get('full_native_http_transfer_observed') is not None for value in records):return False
        try:
            audit=read(folder/'parent-audit.json')
            if not(audit.get('owned_processes_gone') is True and audit.get('profile_cleaned') is True and audit.get('process_cleanup_errors')==[] and audit.get('error_class')==parent_error and audit.get('parent_deadline')==parent_deadline):return False
            # Source=False still checks live Root/code/history/lease/resources;
            # it does not erase a source hold or admit another request.
            self.guard(force=True)
            envelope=self.policy_envelope()
            scope=http_policy.status(envelope['state'],time.time(),historical_review=self.http_review,candidate_video_id=ident)
            if scope['global_stop']:return False
            descriptor={'schema_version':1,'kind':'parent_censored_native_attempt','video_id':ident,'profile':worker.PROFILE,
                'plan_sha256':self.plan_sha,'attempt_sha256':digest(folder/'attempt.json'),'worker_sha256':digest(worker.__file__),
                'coordinator_sha256':digest(__file__),'settings_sha256':digest(self.settings_path),
                'root_grant_sha256':digest(self.s['root_admission_path']),'deadline':parent_deadline,
                'owned_child_identity':audit.get('owned_child_identity'),'owned_processes_gone':True,'profile_cleaned':True,
                'parent_audit':{'filename':'parent-audit.json','bytes':(folder/'parent-audit.json').stat().st_size,'sha256':digest(folder/'parent-audit.json')},
                'source_access':'unknown','source_counters_state':'unknown','source_counters':{'python_wire_requests':None,'python_body_bytes':None,'audio_bytes_written':None,'browser_observed_requests':None},
                'item_quarantined':True,'automatic_retry':False,'counts_as_success':False,'resets_streak':False,
                'worker_terminal_result_fabricated':False,'provenance_validated':True,'at_epoch':time.time()}
            for name in ('result.json','progress.json'):
                path=folder/name
                if path.exists():descriptor[name.replace('.json','')+'_observation']={'bytes':path.stat().st_size,'sha256':digest(path)}
            write(folder/'parent-censored.json',descriptor)
            need(bulk_contract.parent_censored_valid(folder,ident,self.settings_path,self.plan_sha),'parent_censored_invalid')
            event=http_policy.local_event(ident,'parent_censored_'+parent_error)
            attempt=descriptor['attempt_sha256'];key=hashlib.sha256(encoded({'plan':self.plan_sha,'video_id':ident,'attempt':attempt,'observation':'parent_censored_timeout'})).hexdigest()
            state=http_policy.apply_outcome(envelope['state'],event,key,attempt,descriptor['at_epoch'])
            write(self.http_state_path,dict(envelope,state=state))
            scope=http_policy.status(state,time.time(),historical_review=self.http_review,candidate_video_id=ident)
            if scope['global_stop']:self.latch_global(ident,'source_scope_unknown',event_id=key,circuit=scope['circuit_break'])
            return True
        except Exception:
            self.administrative_hold('parent timeout evidence or provenance invalid')
            return False

    def observe_worker_diagnostics(self,folder=None):
        with self.lock:
            fatal = any(getattr(capture,'events',0)>0 or getattr(capture,'failure',None) is not None
                        for capture in getattr(self,'live_captures',{}).values())
            folders = [row['folder'] for row in getattr(self,'live_reservations',{}).values()]
            if folder is not None: folders.append(folder)
            for path in folders:
                path=Path(path)
                if (path/'worker-fatal.json').exists():fatal=True
                audit=path/'parent-audit.json'
                if audit.exists():
                    try:
                        value=read(audit).get('child_diagnostic_capture') or {}
                        if value.get('structured_events',0)>0 or value.get('capture_failure') is not None:fatal=True
                    except (OSError,ValueError,TypeError,AttributeError):fatal=True
            if fatal:self.administrative_hold('worker fatal or diagnostic capture failure')
            return fatal

    def finalize_child_result(self,ident,folder,result,*,parent_deadline=None,parent_error=None):
        # Final/progress HTTP is always committed before timeout isolation or
        # slot release. Parent-censored evidence never fabricates worker state.
        with self.lock:
            try:
                self.observe_pending_failures(result)
                fatal_seen=self.observe_worker_diagnostics(folder)
                if fatal_seen:parent_error='worker_fatal_observed'
                diagnostics=result.get('diagnostics',{})
                progress=read(folder/'progress.json') if (folder/'progress.json').exists() else {}
                if any(isinstance(value,dict) and value.get('error_class')=='control_write_failed' for value in (diagnostics,progress)):
                    self.administrative_hold('control write failure')
                known_deadline=parent_error in {'bootstrap_deadline','job_deadline'} and bulk_contract.parent_deadline_valid(parent_deadline,self.s)
                if parent_error and parent_error not in {'source_refusal','item_quarantined'} and not known_deadline:
                    self.administrative_hold('unclassified parent failure')
                complete=(folder/'result.json').exists() and bulk_contract.terminal_result_complete(result,ident)
                censored=False if complete or fatal_seen else self.parent_timeout_descriptor(ident,folder,result,parent_deadline,parent_error)
                if not complete and not censored:self.administrative_hold('bulk terminal result missing or incomplete')
                self.release_after_reconcile(ident)
                return censored
            except BaseException:
                self.administrative_hold('terminal evidence or provenance failure')
                raise


    def execute_child(self, item):
        ident = item['video_id']; folder = self.jobs / ident
        self.wait_adaptive_dispatch(ident)
        while True:
            with self.lock:
                self.guard(source=True, force=True, video_id=ident)
                need(not self.dispatch_paused.is_set(), 'dispatch_paused')
                need(not folder.exists(), 'attempt_already_exists')
                maximum = item.get('max_audio_bytes', self.s['max_asset_bytes'])
                need(type(maximum) is int and 0 < maximum <= self.s['max_asset_bytes'], 'asset_deferred')
                fits = self.capacity['inactive_spool_bytes'] + self.budget._outstanding() + maximum + HEADROOM <= self.s['spool_cap_bytes']
                if fits:
                    self.budget.reserve_item(ident, folder / 'native-audio.part', maximum, HEADROOM)
                    self.live_reservations[ident] = {'folder': folder, 'bytes': maximum + HEADROOM}
                    folder.mkdir(parents=True)
                    config = {'settings_path': str(self.settings_path), 'video_id': ident, 'item': item, 'run_root': str(folder),
                        'lease_path': str(self.lease_path), 'batch_stop_path': str(self.stop_path)}
                    write(folder / 'config.json', config)
                    write(folder / 'attempt.json', {'schema_version': 1, 'video_id': ident, 'attempts_spent': 1,
                        'plan_sha256': self.plan_sha, 'lease_id': self.s['lease_id'], 'worker_sha256': digest(worker.__file__),
                        'created_at': storage.utc_now(), 'source_history_preserved': True})
                    break
                need(bool(self.live_reservations), 'spool_storage_deferred')
            time.sleep(.5)  # wait for an existing owned worker/upload; no source attempt spent
        job = None; process = None; attached = False; closed = False; error = None
        first_exception = None; first_capacity_failure = None; process_cleanup_errors = []; profile_cleanup = None;child_identity=None;parent_deadline=None
        started = time.monotonic(); peak_profile = 0; diagnostic_capture=None; diagnostic_summary=None; parent_stage='before_spawn';GO_wait=None
        try:
            self.wait_adaptive_dispatch(ident)
            need(WINDOWS, 'windows_child_required')
            job = OwnedJob()
            diagnostic_capture = worker_diagnostics.StderrCapture(folder)
            with self.lock:self.live_captures[ident]=diagnostic_capture
            parent_stage='spawn_child';spawned_at=time.monotonic()
            process = subprocess.Popen([self.s['python_executable'], '-I', str(Path(worker.__file__).resolve()), '--child',
                '--config', str(folder / 'config.json'), '--admission', str(self.lease_path)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW)
            parent_stage='attach_owned_job'
            job.attach(process); attached = True
            diagnostic_capture.start(process.stderr)
            child_identity=bulk_contract.windows_identity(process.pid,process._handle)
            write(folder/'child-owner.json',{'schema_version':1,'owned_child':child_identity,'plan_sha256':self.plan_sha,'cohort_frame_index':self.s['cohort_frame_index']})
            parent_stage='pre_GO_wait'
            GO_wait=self.await_owned_GO(ident,folder,process,spawned_at)
            while process.poll() is None:
                parent_stage='live_source_guard'
                self.guard(source=True, video_id=ident)
                need(diagnostic_capture.failure is None,'diagnostic_capture_failed')
                need(diagnostic_capture.events == 0,'worker_fatal_observed')
                elapsed = time.monotonic() - started
                if elapsed>=self.s['job_wall_seconds']:
                    parent_deadline={'kind':'job_deadline','configured_seconds':self.s['job_wall_seconds'],'actual_elapsed_seconds':elapsed}
                    raise worker.Held('job_deadline')
                parent_stage='progress_read'
                status = read(folder / 'progress.json') if (folder / 'progress.json').exists() else {}
                if status.get('phase','bootstrap')=='bootstrap' and elapsed>=90:
                    parent_deadline={'kind':'bootstrap_deadline','configured_seconds':90,'actual_elapsed_seconds':elapsed}
                    raise worker.Held('bootstrap_deadline')
                if status.get('error_class') in SOURCE_FAILURES:
                    self.refuse({'video_id': ident, 'diagnostics': status}); raise worker.Held('source_refusal')
                parent_stage='profile_accounting'
                profile_size = storage.tree_bytes(folder / 'profile-temp'); peak_profile = max(peak_profile, profile_size)
                need(profile_size <= 150_000_000 and storage.tree_bytes(folder) <= maximum + HEADROOM, 'observed_child_spool')
                time.sleep(.5)
        except BaseException as exc:
            error = getattr(exc, 'code', getattr(exc, 'kind', 'native_child_failed'))
            first_exception = exception_diagnostic(exc)
            first_capacity_failure = getattr(exc, 'capacity_evidence', None)
            if error in {'diagnostic_capture_failed','worker_fatal_observed','pre_GO_dispatch_wait_deadline'}:
                with self.lock: self.administrative_hold('child diagnostic failure or fatal worker observation')
        finally:
            if process and not attached and process.poll() is None: process.kill()
            if job:
                try: closed = job.stop_and_verify()
                except Exception as exc:
                    process_cleanup_errors.append(exception_diagnostic(exc)); error = error or 'owned_cleanup_failed'
                finally: job.close()
            if process:
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired as exc:
                    process_cleanup_errors.append(exception_diagnostic(exc)); process.kill(); process.wait(timeout=5)
                    error = error or 'child_cleanup_failed'
            if diagnostic_capture is not None:
                try: diagnostic_summary = diagnostic_capture.finish()
                except BaseException as diagnostic_error:
                    diagnostic_summary = {'capture_failure':worker_diagnostics.exception_rows(diagnostic_error),'worker_result_authority':False}
                    error = 'diagnostic_capture_failed'
                    first_exception = first_exception or exception_diagnostic(diagnostic_error)
            if not closed or process_cleanup_errors:
                self.source_stop.set()
                self.stop_path.write_bytes(b'owned child cleanup requires review\n')
            if closed:
                profile = folder / 'profile-temp'
                if profile.exists():
                    try: profile_cleanup = cleanup_profile(profile, folder, closed)
                    except Exception as exc:
                        profile_cleanup = {'cleaned': False, 'attempts': 0, 'failures': [exception_diagnostic(exc)]}
                        error = error or 'cleanup_path'; self.source_stop.set()
                        self.stop_path.write_bytes(b'owned profile path requires review\n')
            write(folder / 'parent-audit.json', {'schema_version': 1, 'video_id': ident, 'owned_processes_gone': closed,
                'profile_cleaned': not (folder / 'profile-temp').exists(), 'observed_profile_peak_bytes': peak_profile,
                'browser_disk_limit_is_observed_stop_target': True, 'error_class': error,
                'first_parent_exception': first_exception, 'parent_operation_stage':parent_stage, 'pre_GO_wait':GO_wait, 'process_cleanup_errors': process_cleanup_errors,
                'child_diagnostic_capture':diagnostic_summary,
                'capacity_failure': first_capacity_failure,
                'profile_cleanup': profile_cleanup,
                'child_exit': process.returncode if process else None,
                'owned_child_identity':child_identity,
                'parent_deadline':parent_deadline,
                'elapsed_seconds': time.monotonic() - started})
            with self.lock:
                try:
                    result = read(folder/'result.json') if (folder/'result.json').exists() else None
                except (OSError,ValueError,TypeError):result=None
                if not isinstance(result,dict):result={'status':'held','video_id':ident,'diagnostics':{'error_class':error or 'child_result_missing_or_invalid'}}
                # Commit terminal source evidence while this child remains in
                # the scan set and the same lock still excludes every new GO.
                try:censored=self.finalize_child_result(ident,folder,result,parent_deadline=parent_deadline,parent_error=error)
                finally:
                    if ident not in self.live_reservations:self.live_captures.pop(ident,None)
                if censored:result={'status':'held','video_id':ident,'parent_censored_descriptor':'parent-censored.json','source_access':'unknown'}
        if error or not closed: result = dict(result, status='held', parent_error_class=error or 'cleanup_unproven')
        return result

    def retain_handoff(self, folder, record, proofs, known):
        if not getattr(self, 'handoff', None): return
        module = handoff_module(); options = self.s['asr_handoff']
        started = time.monotonic()
        while True:
            self.guard()
            try:
                retained = module.retain_before_cleanup(self.handoff, record, proofs, trusted=known,
                    caption_bundle_paths=options.get('caption_bundle_paths', {}).get(record['video_id'], {}))
                # Empty updates (caption-satisfied/deferred-language) must not
                # discard the collector's existing trusted fingerprints.
                known.update({k: tuple(v) for k, v in retained.get('collector_trusted', {}).items()})
                try:
                    write(folder / 'asr-handoff.json', {'schema_version': 1, 'handoff_id': retained['handoff_id'],
                        'allocation_lease_id': self.handoff.lease_id, 'video_id': record['video_id'],
                        'audio_sha256': record['sha256'], 'metadata_sha256': record['metadata']['sha256']})
                except Exception:
                    self.dispatch_paused.set(); raise
                return
            except storage.IngestError as error:
                if error.kind not in {'handoff_capacity', 'locked'}:
                    self.dispatch_paused.set(); raise
                elapsed = time.monotonic() - started
                try:
                    write(folder / 'asr-handoff-wait.json', {'schema_version': 1,
                        'state': 'waiting_for_queue_lock' if error.kind == 'locked' else 'waiting_for_consumer',
                        'video_id': record['video_id'], 'elapsed_seconds': round(elapsed, 3),
                        'original_files_retained': True, 'new_source_request': False})
                except Exception:
                    self.dispatch_paused.set(); raise
                # An oversized English input cannot fit after a consumer drain.
                oversized = error.kind == 'handoff_capacity' and record['bytes'] + record['metadata']['bytes'] + module.CONTROL_RESERVE > self.handoff.cap_bytes
                if oversized or self.dispatch_paused.is_set() or elapsed >= options['capacity_wait_seconds']:
                    self.dispatch_paused.set(); raise
                time.sleep(1)  # local capacity only; no source/upload retry

    def finalize_handoff(self, folder, done):
        marker = folder / 'asr-handoff.json'
        if not getattr(self, 'handoff', None) or not marker.exists(): return
        try:
            binding = read(marker)
            need(binding.get('allocation_lease_id') == self.handoff.lease_id and
                 binding.get('video_id') == done['video_id'] and binding.get('audio_sha256') == done['sha256'] and
                 binding.get('metadata_sha256') == done['metadata']['sha256'], 'handoff_checkpoint_binding')
            started = time.monotonic()
            while True:
                self.guard()
                try:
                    handoff_module().finalize_after_cleanup(self.handoff, binding['handoff_id'], done)
                    break
                except storage.IngestError as error:
                    if error.kind != 'locked' or time.monotonic() - started >= self.s['asr_handoff']['capacity_wait_seconds']: raise
                    time.sleep(1)  # lock was not acquired; no ambiguous mutation retry
        except Exception:
            self.dispatch_paused.set(); raise

    def publish(self,item,result):
        with self.lock:self.invalidate_partition()
        try:return self._publish_uncached(item,result)
        finally:
            with self.lock:
                self.invalidate_partition()
                if self.budget:
                    value=self.capacity_partition(force=True)
                    self.budget.inactive_bytes=value['inactive_private_bytes']

    def _publish_uncached(self, item, result):
        self.guard()
        ident = item['video_id']; folder = self.jobs / ident
        record_path = folder / 'canonical-record.json'
        if record_path.exists():
            record = read(record_path)
            validate_record(record, item, folder, self.root, self.s['remote'], self.plan_sha)
            trusted = None  # resumed source is hashed once by shared verifier
        else:
            need(result.get('status') == 'local_complete' and result.get('video_id') == ident, 'local_result')
            proof = result['audio']; source = folder / proof['filename']
            need(source.parent == folder and source.suffix in {'.m4a', '.webm'} and
                 storage.fingerprint(source) == tuple(proof['fingerprint']) and source.stat().st_size == proof['bytes'], 'local_audio_changed')
            audio = folder / (ident + source.suffix)
            need(not audio.exists(), 'local_name_conflict')
            metadata_source = folder / result['metadata']['filename']
            need(metadata_source.parent == folder and digest(metadata_source) == result['metadata']['sha256'], 'local_metadata_changed')
            metadata_value = read(metadata_source)
            remote = storage.remote_path(self.s['remote'], item, audio.suffix.lstrip('.'))
            metadata_value['queue'] = item['queue_row']
            metadata_value['archive_audio'] = {k: proof[k] for k in ('bytes', 'md5', 'sha256')}
            metadata_value['archive_audio'].update(video_id=ident, remote=remote, file_name=audio.name, encoding='native audio; no re-encode')
            metadata_value['native_batch_provenance'] = {'profile': worker.PROFILE, 'plan_sha256': self.plan_sha,
                'worker_sha256': digest(worker.__file__), 'coordinator_sha256': digest(__file__), 'lease_id': self.s['lease_id'],
                'quality_state': result['probe']['quality_state'], 'human_reviewed': False}
            metadata = folder / (ident + '.info.json')
            if metadata.exists(): need(read(metadata) == metadata_value, 'local_metadata_conflict')
            else: write(metadata, metadata_value)
            meta_proof = storage.hash_file(metadata)
            record = dict(video_id=ident, channel_dir=item['channel_dir'], tab=item['tab'], status='prepared',
                path=audio.relative_to(self.root).as_posix(), remote=remote, **{k: proof[k] for k in ('bytes', 'md5', 'sha256')},
                metadata={**meta_proof, 'path': metadata.relative_to(self.root).as_posix(), 'remote': remote.rpartition('/')[0] + '/' + metadata.name},
                native_batch_profile=worker.PROFILE, native_batch_plan_sha256=self.plan_sha, native_batch_lease_id=self.s['lease_id'],
                quality_state=result['probe']['quality_state'], native_acquisition_quality=result['probe'])
            validate_record(record, item, folder, self.root, self.s['remote'], self.plan_sha)
            write(record_path, record)  # planned rename survives a crash
            os.replace(source, audio)
            trusted = {'audio': storage.fingerprint(audio), 'metadata': storage.fingerprint(metadata)}
            storage.journal(self.state_path, record)
        audio, metadata = (storage.local_path(self.root, p['path']) for p in (record, record['metadata']))
        if not audio.exists():
            original = folder / ('native-audio' + audio.suffix)
            if original.exists():
                storage.validate_local(original, record)
                os.replace(original, audio)
                trusted = dict(trusted or {}, audio=storage.fingerprint(audio))
        prior = storage.load_state(self.state_path).get(ident, {})
        prior_verified = prior.get('status') in {'verified', 'deleted'} and all(
            prior.get(key) == record.get(key) for key in ('bytes', 'md5', 'sha256', 'remote')) and all(
            prior.get('metadata', {}).get(key) == record['metadata'].get(key) for key in ('bytes', 'md5', 'sha256', 'remote'))
        known = {}
        for key, path, expected in (('audio', audio, record), ('metadata', metadata, record['metadata'])):
            if path.exists(): known[key] = storage.validate_local(path, expected, (trusted or {}).get(key))
            else: need(prior_verified, 'local_missing_without_drive_proof')
        if not prior_verified:
            def preserve_metadata(observed_audio):
                storage.verify_remote(observed_audio, record)
                need(bool(observed_audio.get('ID')), 'drive_identity_missing')
                try: observed_metadata = self.drive.stat(record['metadata']['remote'])
                except storage.IngestError as missing:
                    if missing.kind != 'drive_not_found': raise
                    observed_metadata = None
                try: from .native_metadata_snapshot import preserve_conflicting_metadata
                except ImportError: from native_metadata_snapshot import preserve_conflicting_metadata
                lineage = preserve_conflicting_metadata(self.root, record, self.drive,
                    observed_audio=observed_audio, observed_metadata=observed_metadata, trusted=known)
                if lineage:
                    record['metadata_lineage'] = lineage
                    write(record_path, record)
                    storage.journal(self.state_path, record)

            pending_lineage = storage.load_state(self.root / 'sync/native_metadata_lineage_manifest.jsonl').get(ident, {})
            if (not record.get('metadata_lineage') and
                    pending_lineage.get('kind') == 'native_metadata_snapshot_preservation' and
                    pending_lineage.get('original', {}).get('remote') == record['metadata']['remote'] and
                    pending_lineage.get('new_canonical_expected', {}).get('sha256') == record['metadata']['sha256']):
                # A lost move ACK can leave canonical metadata absent. Read back
                # the exact preserved object before allowing its replacement.
                preserve_metadata(self.drive.stat(record['remote']))
            try:
                self.drive.copy_pair(audio, metadata, record['remote'], record['metadata']['remote'])
            except storage.IngestError as error:
                if error.kind != 'drive_conflict': raise
                # Preserve only conflicting canonical metadata, after the exact
                # new audio is verified remotely. Audio is never replaced.
                try: observed_audio = self.drive.stat(record['remote'])
                except storage.IngestError as missing:
                    if missing.kind != 'drive_not_found': raise
                    self.drive.copy(audio, record['remote'])  # immutable
                    observed_audio = self.drive.stat(record['remote'])
                preserve_metadata(observed_audio)
                self.drive.copy_pair(audio, metadata, record['remote'], record['metadata']['remote'])
        relative = [storage.remote_relative(self.s['remote'], p['remote']) for p in (record, record['metadata'])]
        with storage.batch_manifest(self.root, relative) as manifest:
            remote = self.drive.stat_batch(self.s['remote'], relative, manifest)
        proofs = {'audio': remote[relative[0]], 'metadata': remote[relative[1]]}
        check_pair_proofs(proofs, record)
        self.retain_handoff(folder, record, proofs, known)
        done = storage.verify_and_delete(self.root, record, self.drive, self.state_path, require_metadata=True,
            allow_missing=prior_verified, trusted=known, remote_proofs=proofs)
        need(storage.receipt_complete(done, item, self.s['remote']), 'canonical_receipt_incomplete')
        write(record_path, done)
        self.finalize_handoff(folder, done)
        storage.journal(self.batch_journal, {'schema_version': 1, 'profile': worker.PROFILE, 'video_id': ident,
            'status': 'verified', 'plan_sha256': self.plan_sha, 'quality_state': done['quality_state'],
            'audio_drive_id': done['drive_id'], 'metadata_drive_id': done['metadata']['drive_id']})
        return done

    def drain_completed_source_futures(self,active,ready,counts):
        complete=[future for future in active if future.done()]
        for future in complete:
            item = active.pop(future)
            try:
                result = future.result()
                if result.get('status') == 'local_complete': ready.append((item, result))
                else: counts['held'] += 1
            except Exception as exc:
                counts['held'] += 1
                kind = getattr(exc, 'kind', getattr(exc, 'code', 'native_batch_failed'))
                storage.journal(self.batch_journal, {'schema_version': 1, 'profile': worker.PROFILE, 'video_id': item['video_id'],
                    'status': 'held', 'error_class': kind, 'plan_sha256': self.plan_sha})
                if kind.startswith('drive_'): self.source_stop.set()

    def run(self):
        self.spool.mkdir(exist_ok=True)
        counts = {'verified': 0, 'skipped': 0, 'held': 0, 'pending': 0}
        with storage.exclusive_lock(self.root):
            self.jobs.mkdir(parents=True, exist_ok=True)
            limit = self.guard(force=True, force_inventory=True)
            self.budget = SlotBudget(self.root, limit, self.s['max_asset_bytes'], FREE, cached=False)
            previous = storage.load_state(self.state_path)
            pending = []
            for item in self.items:
                if storage.receipt_complete(previous.get(item['video_id'], {}), item, self.s['remote']):
                    # Recover readiness after a lost finalize ACK, never pull or
                    # download an already archived source again.
                    self.finalize_handoff(self.jobs / item['video_id'], previous[item['video_id']])
                    counts['skipped'] += 1; continue
                folder = self.jobs / item['video_id']
                if folder.exists():
                    result = read(folder / 'result.json') if (folder / 'result.json').exists() else {}
                    if result.get('status') == 'local_complete' or (folder / 'canonical-record.json').exists():
                        try: self.publish(item, result); counts['verified'] += 1
                        except Exception: counts['held'] += 1
                    else: counts['held'] += 1
                else: pending.append(item)
            with ThreadPoolExecutor(max_workers=self.s['workers']) as pool:
                active = {}; ready = []  # frame/byte bounded completions; one publisher
                while active or pending or ready:
                    self.drain_completed_source_futures(active,ready,counts)
                    while pending and len(active) < self.s['workers'] and not self.source_stop.is_set() and not self.dispatch_paused.is_set():
                        if time.time()<self.adaptive_pause_until:break
                        try:
                            with self.lock:
                                limit = self.guard(source=True, video_id=pending[0]['video_id'])
                                if time.time()<self.adaptive_pause_until:break
                                if storage.read_drive_cooldown(self.root / 'sync/drive_ingest_cooldown.json'):
                                    self.dispatch_paused.set(); break
                                maximum = pending[0].get('max_audio_bytes', self.s['max_asset_bytes'])
                                need(type(maximum) is int and 0 < maximum <= self.s['max_asset_bytes'], 'asset_deferred')
                                # Completed files remain inactive bytes. Do not queue a child
                                # against space the single publisher has yet to release.
                                # A submitted future may still be waiting for this lock.
                                # Charge its whole slot until execute_child makes the real
                                # reservation visible; never submit twice against one slot.
                                virtual = sum(candidate.get('max_audio_bytes', self.s['max_asset_bytes']) + HEADROOM
                                    for future, candidate in active.items()
                                    if not future.done() and candidate['video_id'] not in self.live_reservations)
                                committed = self.budget._outstanding() + virtual + maximum + HEADROOM
                                if (self.capacity['inactive_spool_bytes'] + committed > self.s['spool_cap_bytes'] or
                                        self.budget.usage() + committed > limit - storage.JOURNAL_RESERVE):
                                    break
                                item = pending.pop(0); active[pool.submit(self.execute_child, item)] = item
                        except Exception:
                            counts['pending'] += len(pending); pending.clear(); break
                    if ready:
                        # One publisher; yield scheduler after exactly one pair.
                        item,result=ready.pop(0)
                        try: self.publish(item, result); counts['verified'] += 1
                        except Exception as exc:
                            counts['held'] += 1
                            kind = getattr(exc, 'kind', getattr(exc, 'code', 'native_batch_failed'))
                            storage.journal(self.batch_journal, {'schema_version': 1, 'profile': worker.PROFILE, 'video_id': item['video_id'],
                                'status': 'held', 'error_class': kind, 'plan_sha256': self.plan_sha})
                            if kind.startswith('drive_'): self.source_stop.set()
                        continue
                    if not active:
                        if pending and time.time()<self.adaptive_pause_until and not self.source_stop.is_set():
                            self.guard(force=True);time.sleep(max(0,min(.25,self.adaptive_pause_until-time.time())));continue
                        counts['pending'] += len(pending); break
                    wait(active, return_when=FIRST_COMPLETED)
            write(self.jobs / 'summary.json', {'schema_version': 1, 'profile': worker.PROFILE, 'plan_sha256': self.plan_sha, **counts})
        return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', required=True); parser.add_argument('--execute', action='store_true')
    args = parser.parse_args(argv); need(args.execute, 'explicit_execution_required')
    result = NativeBatch(args.settings).run(); print(json.dumps(result))
    return 0 if not result['held'] and not result['pending'] else 3


if __name__ == '__main__':
    try: sys.exit(main())
    except worker.Held as error:
        print(json.dumps({'status': 'held', 'error_class': error.code})); sys.exit(3)
