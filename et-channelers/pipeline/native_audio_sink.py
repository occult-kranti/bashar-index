"""Offline prototype: leased original-byte audio sink; importing starts nothing.

There is deliberately no HTTP listener, browser automation, downloader or CLI.
The accepted browser context owns source requests. This module accepts bounded
binary writes and never needs a media URL, cookie, token, or browser profile.
"""
from __future__ import annotations

import contextlib
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

MAX_CHUNK = 1_048_576
MAX_CONTROL = 1_048_576
CONTROL_RESERVE = 2 * MAX_CONTROL
MAX_SPOOL = 8_000_000_000
MAX_MANAGED = 16_000_000_000
DISK_FLOOR = 2_000_000_000
BINDING_FIELDS = {'videoId','itag','lastModified','xtags','mimeType','codec','contentLength',
                  'durationMs','language','originalBasis','trackId','noDRM','audioOnly','transportKind'}
MIME_EXT = {'audio/webm':'webm','audio/mp4':'m4a','audio/ogg':'ogg'}
CODECS = {'opus':'opus','vorbis':'vorbis','aac':'aac','mp4a.40.2':'aac'}
PILOT_V1='accepted_chrome_sabr_single_fullfile_v1'
PILOT_V2='accepted_chrome_sabr_diagnostic_followup_v2'
PILOT_V3='accepted_normal_chrome_context_followup_v3'
FOLLOWUP_KINDS={PILOT_V2,PILOT_V3}


class SinkError(Exception):
    def __init__(self, code):
        self.code = self.kind = code
        super().__init__(code)


def need(value, code):
    if not value:
        raise SinkError(code)


def raw_json(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def latest_receipts(path):
    if not Path(path).exists():return {}
    rows=[json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]
    return {r['video_id']:r for r in rows}


def atomic(path, value):
    raw = raw_json(value)
    need(len(raw) <= MAX_CONTROL, 'control_too_large')
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix+'.tmp')
    with part.open('wb') as out:
        out.write(raw); out.flush(); os.fsync(out.fileno())
    os.replace(part, path)


def digest(path, length=None):
    sha, md5, total = hashlib.sha256(), hashlib.md5(), 0
    with Path(path).open('rb') as src:
        while length is None or total < length:
            block = src.read(MAX_CHUNK if length is None else min(MAX_CHUNK,length-total))
            if not block: break
            sha.update(block); md5.update(block); total += len(block)
    return {'bytes':total,'sha256':sha.hexdigest(),'md5':md5.hexdigest()}


def binding(value):
    need(isinstance(value,dict) and set(value)==BINDING_FIELDS,'binding_fields')
    need(re.fullmatch(r'[A-Za-z0-9_-]{11}',str(value['videoId'])),'video_id')
    need(type(value['itag']) is int and 0<value['itag']<10000,'itag')
    need(isinstance(value['lastModified'],str) and re.fullmatch(r'[0-9]{1,30}',value['lastModified']),'last_modified')
    need(value['noDRM'] is True and value['audioOnly'] is True,'protected_or_video_format')
    need(isinstance(value['mimeType'],str) and value['mimeType'].split(';')[0].strip() in MIME_EXT and value['codec'] in CODECS,'native_codec')
    need(re.fullmatch(r'audio/(?:webm|mp4|ogg)(?:;\s*codecs="[A-Za-z0-9., -]+")?',value['mimeType']),'unsafe_mime')
    if ';' in value['mimeType']:
        need(CODECS.get(value['mimeType'].split('"')[1])==CODECS[value['codec']],'mime_codec_conflict')
    need(value['transportKind'] in {'direct_http','sabr_reassembled'},'transport_kind')
    need((type(value['contentLength']) is int and value['contentLength']>0) or (value['transportKind']=='sabr_reassembled' and value['contentLength'] is None),'unknown_source_length')
    need(type(value['durationMs']) is int and 0<value['durationMs']<2**53,'unknown_duration')
    for key in ('xtags','trackId','language','originalBasis'):
        limit=4096 if key=='xtags' else 200
        pattern=r'[A-Za-z0-9_.=,+/%; -]*' if key=='xtags' else r'[A-Za-z0-9_.=,; -]*'
        need(value[key] is None or isinstance(value[key],str) and len(value[key])<=limit and re.fullmatch(pattern,value[key]),'unsafe_binding_value')
    need(value['originalBasis'] in {'original_true','audio_track_original','original_default_confirmed','published_original'},'unproven_original_track')
    return json.loads(json.dumps(value))


def binding_hash(value):
    identity=binding(value);identity.pop('transportKind')
    return hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()


def chain_hash(previous,proof):
    payload=previous+'\n'+json.dumps(proof,sort_keys=True,separators=(',',':'),ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def pilot_lineage_hash(policy):
    value={'parent':policy['parent'],'normalPlaybackEvidence':policy['normalPlaybackEvidence']} if policy['kind']==PILOT_V3 else policy['parent']
    return hashlib.sha256(raw_json(value)).hexdigest()


def tree_bytes(root):
    total=0
    for directory,folders,files in os.walk(root,followlinks=False):
        for name in folders+files:
            path=Path(directory)/name
            need(not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(),'storage_link')
        for name in files:
            try: total+=(Path(directory)/name).stat().st_size
            except FileNotFoundError: pass  # concurrent verified upload may free another owned file
    return total


def inspect_audio(path, selected, executable):
    """ffprobe reads the whole file's packets; no transcoding or GPU is requested."""
    try:
        result=subprocess.run([str(executable),'-v','error','-count_packets','-show_entries',
            'stream=codec_type,codec_name,nb_read_packets,duration:format=duration,format_name',
            '-of','json',str(path)],capture_output=True,text=True,timeout=1800,check=False)
        need(result.returncode==0 and not result.stderr.strip(),'ffprobe_failed')
        value=json.loads(result.stdout)
    except (OSError,ValueError,subprocess.TimeoutExpired):
        raise SinkError('ffprobe_failed') from None
    streams=value.get('streams',[])
    need(len(streams)==1 and streams[0].get('codec_type')=='audio','not_audio_only')
    need(streams[0].get('codec_name')==CODECS[selected['codec']],'codec_mismatch')
    need(int(streams[0].get('nb_read_packets',0))>0,'no_audio_packets')
    seconds=float(value.get('format',{}).get('duration') or streams[0].get('duration') or 0)
    expected=selected['durationMs']/1000
    need(math.isfinite(seconds) and seconds>0 and abs(seconds-expected)<=max(2.0,expected*.002),'duration_mismatch')
    return {'method':'ffprobe_full_packet_scan','duration_seconds':seconds,'packets':int(streams[0]['nb_read_packets']),
            'codec':streams[0]['codec_name'],'audio_streams':1,'video_streams':0,
            'duration_tolerance_seconds':max(2.0,expected*.002),'decode_accuracy_claimed':False}


class Coordinator:
    def __init__(self,root,*,owner,lease_id,queue_path,managed_roots,remote,ffprobe,
                 core,metadata_builder,probe=inspect_audio,disk_free=None,on_batch_abort=None):
        self.root=Path(root).resolve(); self.spool=self.root/'native_batch'; self.owner=owner; self.lease_id=lease_id
        self.queue_path=Path(queue_path).resolve(); self.remote=remote.rstrip('/'); self.ffprobe=ffprobe
        self.core=core; self.metadata_builder=metadata_builder; self.probe=probe
        self.disk_free=disk_free or (lambda:shutil.disk_usage(self.root).free)
        self.source_stop=threading.Event();self.on_batch_abort=on_batch_abort
        roots=sorted({Path(p).resolve() for p in managed_roots},key=lambda p:len(p.parts))
        self.roots=[p for i,p in enumerate(roots) if not any(p.is_relative_to(q) for q in roots[:i])]
        need(any(self.root.is_relative_to(p) for p in self.roots),'private_not_accounted')
        need(self.queue_path.is_relative_to(self.root),'queue_outside_private')
        self.lock=threading.RLock();self.opened=False;self._inventory_at=0;self._external_bytes=0;self.live={};self.publishing=set();self._parent_cache=None

    def __enter__(self):
        self._exclusive=self.core.exclusive_lock(self.root);self._exclusive.__enter__()
        try:
            self.opened=True;self.guard();self.spool.mkdir(parents=True,exist_ok=True)
            self.inventory(force=True)
            rows=self.core.select_queue(self.queue_path,entire_queue=True)
            self.rows={row['video_id']:row for row in rows}
            return self
        except BaseException:
            self.opened=False;self._exclusive.__exit__(None,None,None);raise

    def __exit__(self,*args):
        self.opened=False;return self._exclusive.__exit__(*args)

    def states(self):
        return [read(p) for p in (self.spool/'jobs').glob('*/state.json')]

    def pilot_attempt_path(self,lease):
        name={PILOT_V2:'native_context_pilot_followup_v2.json',PILOT_V3:'native_context_normal_chrome_attempt_v3.json'}.get(lease.get('pilotPolicy',{}).get('kind'),'native_context_pilot_attempt.json')
        return self.root/'sync'/name

    def followup_parent(self,lease):
        """Finite v1 -> diagnostic v2 -> normal-context v3; every ancestor stays immutable."""
        policy=lease['pilotPolicy'];parent=policy.get('parent');normal=policy['kind']==PILOT_V3
        fields={'leaseSnapshot','codeSnapshot','attemptSha256','jobStateSha256','segmentLedgerSha256','partialSha256'}
        need(isinstance(parent,dict) and set(parent)==fields|({'diagnosticSnapshot'} if normal else set()),'pilot_parent_fields')
        key=raw_json(lease)
        if self._parent_cache and self._parent_cache[0]==key:
            _,files,state=self._parent_cache
            need(all(p.is_file() and (p.stat().st_size,p.stat().st_mtime_ns)==stamp for p,stamp in files),'pilot_parent_changed')
            return state
        checked=[]
        def proven(path,sha):
            path=Path(path).resolve()
            need(path.is_relative_to(self.root) and path.is_file() and isinstance(sha,str) and re.fullmatch(r'[a-f0-9]{64}',sha),'pilot_parent_path')
            need(digest(path)['sha256']==sha,'pilot_parent_changed')
            checked.append((path,(path.stat().st_size,path.stat().st_mtime_ns)));return path
        def snapshot(pin):
            need(isinstance(pin,dict) and set(pin)=={'path','sha256'},'pilot_parent_snapshot')
            return read(proven(pin['path'],pin['sha256']))
        previous=snapshot(parent['leaseSnapshot']);old=previous.get('pilotPolicy',{})
        need(old.get('kind')==(PILOT_V2 if normal else PILOT_V1) and old.get('approvedByResourceOwner') is True and
             previous.get('lease_id')!=self.lease_id and previous.get('owner')==self.owner and previous.get('max_workers')==1 and old.get('maxAttempts')==1,'pilot_parent_policy')
        need(all(old.get(k)==policy.get(k) for k in ('targetVideoId','transportKind','expectedDurationMs','durationToleranceMs')) and
             previous.get('remote')==lease['remote'] and previous.get('queue_sha256')==lease['queue_sha256'],'pilot_parent_scope')
        need((old.get('acceptedContext')=='automated_dedicated_chromium' and policy.get('acceptedContext')=='normal_user_chrome') if normal
             else old.get('acceptedContext')==policy.get('acceptedContext'),'pilot_parent_context')
        codes=snapshot(parent['codeSnapshot']);pins=codes.get('files',{})
        need(codes.get('schema_version')==1 and set(pins)=={'worker','gateway','sdk','observer','adapter'},'pilot_parent_codes')
        for name,pin in pins.items():
            expected=previous.get(name+'_sha256') if name in {'worker','gateway'} else old.get('codePins',{}).get(name,{}).get('sha256')
            need(isinstance(pin,dict) and set(pin)=={'path','sha256'} and pin['sha256']==expected,'pilot_parent_codes')
            proven(pin['path'],pin['sha256'])
        if normal:
            need(all(policy['codePins'][name]['sha256']==pins[name]['sha256'] for name in ('sdk','observer','adapter')),'pilot_context_code_changed')
        else:need(all(policy['codePins'][name]['sha256']!=pins[name]['sha256'] for name in ('sdk','adapter')),'pilot_diagnostics_unchanged')
        attempt=read(proven(self.pilot_attempt_path(previous),parent['attemptSha256']))
        need(attempt.get('attempts_spent')==1 and attempt.get('lease_id')==previous['lease_id'] and
             attempt.get('video_id')==policy['targetVideoId'] and attempt.get('canonical_cooldown_preserved') is True,'pilot_parent_attempt')
        ident=attempt.get('job_id','');need(isinstance(ident,str) and re.fullmatch(r'native-[a-f0-9]{24}',ident),'pilot_parent_job')
        folder=self.spool/'jobs'/ident;state=read(proven(folder/'state.json',parent['jobStateSha256']))
        need(state.get('state')=='retained' and state.get('error_class')=='protocol' and not state.get('source_error_class') and not state.get('record') and
             (normal or not state.get('diagnostic_parent_job_id')) and
             state.get('native_lease_id')==previous['lease_id'] and state.get('owner')==self.owner and state.get('job_id')==ident and
             state.get('video_id')==policy['targetVideoId'] and state.get('source_requests')==attempt.get('source_requests') and
             0<state.get('source_requests',0)<=old.get('sourceRequestBudget',0) and
             state.get('binding_sha256')==attempt.get('source_binding_sha256')==binding_hash(state['binding']),'pilot_parent_not_terminal')
        proven(folder/'segments.jsonl',parent['segmentLedgerSha256']);partial=proven(folder/'audio.part',parent['partialSha256'])
        need(partial.stat().st_size==state.get('offset') and state.get('prefix_sha256')==parent['partialSha256'],'pilot_parent_partial')
        ancestors=[ident]
        if normal:
            need(type(policy.get('maxContextFollowups')) is int and policy['maxContextFollowups']==1,'pilot_context_single_attempt')
            result=snapshot(parent['diagnosticSnapshot']);diag=result.get('sabr_diagnostics',{});counts=diag.get('counts',{});latest=diag.get('latest',{})
            requests=state['source_requests'];request=latest.get('request',{})
            need(result.get('video_id')==policy['targetVideoId'] and result.get('state')=='held' and result.get('error_class')=='sdk_stalled' and
                 result.get('source_refusals')==[] and diag.get('schemaVersion')==1 and diag.get('errorKind')=='sdk_stalled' and
                 all(counts.get(k)==requests for k in ('request','response','policy','protection')) and counts.get('observer_error')==0 and counts.get('reload')==0 and
                 latest.get('protection',{}).get('status')==2 and latest.get('response',{}).get('status')==200 and
                 request.get('selectedAudioMatches') is True and request.get('selectedAudioCount')==1 and request.get('selectedVideoCount')==0 and
                 request.get('playerTimeMs')==state['media_end_ms'] and request.get('bufferedDurationMs')==state['media_end_ms'] and request.get('bufferedStartMs')==0 and
                 latest.get('track',{}).get('endOfStream') is False,'pilot_parent_diagnostic')
            evidence=snapshot(policy.get('normalPlaybackEvidence'));statement=evidence.get('statement')
            need(set(evidence)=={'schema_version','basis','video_id','plays_beyond_seconds','approvedByResourceOwner','statement'} and
                 evidence['schema_version']==1 and evidence['basis']=='user_reported_normal_chrome_playback' and evidence['video_id']==policy['targetVideoId'] and
                 type(evidence['plays_beyond_seconds']) is int and evidence['plays_beyond_seconds']==90 and evidence['approvedByResourceOwner'] is True and
                 isinstance(statement,dict) and set(statement)=={'path','sha256'},'pilot_normal_playback_evidence')
            statement_path=proven(statement['path'],statement['sha256']);need(0<statement_path.stat().st_size<=16_384,'pilot_user_statement_bound')
            ancestor=self.followup_parent(previous);checked.extend(self._parent_cache[1])
            need(state.get('diagnostic_parent_job_id')==attempt.get('parent_job_id')==ancestor['job_id'] and
                 state.get('diagnostic_lineage_sha256')==attempt.get('lineage_sha256')==pilot_lineage_hash(old) and
                 attempt.get('parent_attempt_sha256')==old['parent']['attemptSha256'] and state['binding_sha256']==ancestor['binding_sha256'],'pilot_parent_lineage')
            ancestors.extend(ancestor['_ancestor_job_ids'])
        state={**state,'_ancestor_job_ids':ancestors};self._parent_cache=(key,checked,state);return state

    def pilot_policy(self,lease,context):
        policy=lease.get('pilotPolicy')
        if not policy or not context:return False
        need(policy.get('kind') in {PILOT_V1,*FOLLOWUP_KINDS} and policy.get('approvedByResourceOwner') is True,'pilot_policy')
        need(lease['max_workers']==1 and policy.get('maxAttempts')==1 and type(policy['maxAttempts']) is int,'pilot_single_attempt')
        need(policy.get('targetVideoId')=='EliqxbbQoRw' and policy.get('transportKind')=='sabr_reassembled' and
             policy.get('acceptedContext') in {'normal_user_chrome','automated_dedicated_chromium'},'pilot_scope')
        now=time.time();created=policy.get('createdAtEpoch',0);expires=policy.get('expiresAtEpoch',0)
        need(type(created) in {int,float} and type(expires) in {int,float} and math.isfinite(created) and math.isfinite(expires) and
             created<=now<expires and 0<expires-created<=3600,'pilot_expired')
        need(policy.get('expectedDurationMs')==1570961 and type(policy.get('durationToleranceMs')) is int and 0<=policy['durationToleranceMs']<=150,'pilot_duration_policy')
        selected=context['binding']
        if context.get('job_id') is not None:
            need(context.get('acquisition_provenance',{}).get('context_kind')==policy['acceptedContext'],'pilot_context_changed')
        need(selected['videoId']==policy['targetVideoId'] and selected['transportKind']=='sabr_reassembled' and
             abs(selected['durationMs']-policy['expectedDurationMs'])<=policy['durationToleranceMs'],'pilot_format_scope')
        need(selected['originalBasis']=='published_original' and selected['noDRM'] is True and selected['audioOnly'] is True,'pilot_original_unproven')
        need(type(policy.get('maxOutputBytes')) is int and 0<policy['maxOutputBytes']<=64_000_000 and context['output_budget_bytes']<=policy['maxOutputBytes'],'pilot_output_budget')
        need(type(policy.get('sourceRequestBudget')) is int and 0<policy['sourceRequestBudget']<=1000,'pilot_request_budget')
        pins=policy.get('codePins',{});need(set(pins)=={'sdk','observer','adapter'},'pilot_code_pins')
        for pin in pins.values():
            need(isinstance(pin,dict) and set(pin)=={'path','sha256'},'pilot_code_pin')
            path=Path(pin['path']).resolve();need(any(path.is_relative_to(root) for root in self.roots),'pilot_code_unaccounted')
            need(path.is_file() and digest(path)['sha256']==pin['sha256'],'pilot_code_changed')
        parent=self.followup_parent(lease) if policy['kind'] in FOLLOWUP_KINDS else None
        if parent:need(binding_hash(selected)==parent['binding_sha256'],'pilot_parent_binding')
        attempt=self.pilot_attempt_path(lease)
        if attempt.exists():
            spent=read(attempt)
            need(context.get('job_id')==spent.get('job_id') and spent.get('lease_id')==self.lease_id and
                 spent.get('source_binding_sha256')==binding_hash(selected),'pilot_attempt_spent')
            if parent:need(spent.get('parent_attempt_sha256')==policy['parent']['attemptSha256'] and
                           spent.get('lineage_sha256')==pilot_lineage_hash(policy),'pilot_parent_changed')
        else:
            need(context.get('job_id') is None and policy.get('bindFirstValidatedHash') is True,'pilot_binding_unproven')
        return policy

    def guard(self,source=False,context=None):
        need(self.opened,'coordinator_not_owned')
        need(not (self.root/'sync/STOP_NATIVE_BATCH').exists(),'stopped')
        lease=read(self.root/'sync/native_batch_lease.json')
        need(lease.get('state')=='active' and lease.get('owner')==self.owner and lease.get('lease_id')==self.lease_id,'native_lease_inactive')
        need(type(lease.get('expires_at_epoch')) in {int,float} and lease['expires_at_epoch']>time.time(),'native_lease_expired')
        need(lease.get('worker_sha256')==digest(Path(__file__))['sha256'],'worker_not_admitted')
        need(lease.get('queue_sha256')==digest(self.queue_path)['sha256'],'queue_changed')
        need(lease.get('remote')==self.remote and lease.get('native_encoded_audio_only') is True,'lease_destination_policy')
        declared=lease.get('managed_roots')
        need(isinstance(declared,list) and declared and all(isinstance(p,str) for p in declared),'managed_root_policy')
        required=[self.root,Path(sys.prefix).resolve(),Path(__file__).resolve().parents[2],*[Path(p).resolve() for p in declared]]
        need(all(any(p.is_relative_to(root) for root in self.roots) for p in required),'incomplete_storage_inventory')
        need(type(lease.get('spool_cap_bytes')) is int and 0<lease['spool_cap_bytes']<=MAX_SPOOL,'spool_policy')
        need(lease.get('max_workers') in {1,2,3,4},'worker_policy')
        plan=read(self.root/'sync/analysis_resource_plan.json')
        need(plan.get('collector_dispatch_allowed') is False and (self.root/'sync/STOP_DRIVE_INGEST').exists(),'collector_not_parked')
        need(0<plan.get('accounting_cap_bytes',0)<=MAX_MANAGED,'managed_cap_policy')
        own=[r for r in plan.get('reservations',[]) if r.get('lease_id')==self.lease_id and r.get('owner')==self.owner and r.get('state')=='active']
        need(len(own)==1 and own[0].get('max_bytes',0)>=lease['spool_cap_bytes'],'native_reservation_inactive')
        if lease['max_workers']>1:
            gate=read(self.root/'sync/native_single_worker_acceptance.json')
            proof=gate.get('receipt',{});row=proof.get('queue_row',{})
            need(gate.get('approved_by_resource_owner') is True and gate.get('worker_sha256')==lease['worker_sha256'] and
                 proof.get('native_transport_kind') in {'direct_http','sabr_reassembled'} and self.core.receipt_complete(proof,row,self.remote) and
                 latest_receipts(self.root/'sync/drive_ingest_manifest.jsonl').get(proof.get('video_id'))==proof,'single_fullfile_gate_missing')
        if source:
            cooldown=self.root/'sync/native_batch_source_cooldown.json'
            if cooldown.exists():
                value=read(cooldown)
                need(value.get('retry_not_before_epoch',0)<=time.time(),'source_cooldown')
            need(not self.source_stop.is_set(),'source_batch_stopped')
            prior=latest_receipts(self.root/'sync/drive_ingest_manifest.jsonl')
            blocked=any(r.get('source_error_class',r.get('error_class')) in {'forbidden','rate_limited','bot_check'} and
                float(r.get('retry_not_before_epoch',0))>time.time() for r in prior.values())
            exception=self.pilot_policy(lease,context) if lease.get('pilotPolicy') else False
            need(not blocked or exception,'canonical_source_cooldown')
        return lease,plan

    def inventory(self,extra=0,force=False):
        with self.lock:return self._inventory(extra,force)

    def _inventory(self,extra=0,force=False):
        lease,plan=self.guard()
        if force or time.monotonic()-self._inventory_at>5:
            total=sum(tree_bytes(p) for p in self.roots)
            self._external_bytes=total-tree_bytes(self.spool);self._inventory_at=time.monotonic()
        own=tree_bytes(self.spool)
        outstanding=sum(max(0,s['reservation_bytes']-tree_bytes(self.spool/'jobs'/s['job_id'])) for s in self.states() if s['state']!='deleted')
        other=sum(r['max_bytes'] for r in plan.get('reservations',[]) if r.get('state')=='active' and r.get('lease_id')!=self.lease_id)
        need(own+outstanding+extra<=lease['spool_cap_bytes'],'spool_storage_deferred')
        need(self._external_bytes+own+outstanding+extra+other<=min(MAX_MANAGED,plan['accounting_cap_bytes']),'managed_storage_deferred')
        need(self.disk_free()-outstanding-extra>=DISK_FLOOR,'disk_buffer')
        return {'managed_actual_bytes':self._external_bytes+own,'spool_actual_bytes':own,'outstanding_bytes':outstanding,'other_reserved_growth_bytes':other}

    def begin(self,selected,metadata,*,output_budget_bytes=None):
        selected=binding(selected)
        with self.lock:
            lease,_=self.guard();video=selected['videoId'];need(video in self.rows,'not_in_queue')
            row=self.rows[video]
            states=self.states()
            current=latest_receipts(self.root/'sync/drive_ingest_manifest.jsonl')
            need(not self.core.receipt_complete(current.get(video,{ }),row,self.remote),'already_verified')
            maximum=selected['contentLength'] if selected['transportKind']=='direct_http' else output_budget_bytes
            need(type(maximum) is int and maximum>0,'output_budget_required')
            context={'binding':selected,'output_budget_bytes':maximum,'job_id':None}
            self.guard(source=True,context=context)
            parent=self.followup_parent(lease) if lease.get('pilotPolicy',{}).get('kind') in FOLLOWUP_KINDS else None
            active=[s for s in states if s['state']!='deleted' and (not parent or s['job_id'] not in parent['_ancestor_job_ids'])]
            need(not any(s['video_id']==video for s in active),'source_already_leased')
            need(len(active)<lease['max_workers'],'worker_slots_full')
            self.inventory(maximum+CONTROL_RESERVE,force=True)
            try:meta=self.metadata_builder(metadata,row,self.core.utc_now())
            except (ValueError,TypeError,KeyError):raise SinkError('metadata_video_id') from None
            need(meta.get('source',{}).get('video_id')==video,'metadata_video_id')
            need(len(raw_json(meta))<=MAX_CONTROL//2,'metadata_too_large')
            lineage=pilot_lineage_hash(lease['pilotPolicy']) if parent else None
            ident='native-'+(hashlib.sha256((binding_hash(selected)+lineage).encode()).hexdigest() if parent else binding_hash(selected))[:24];folder=self.spool/'jobs'/ident
            need(not folder.exists(),'existing_job_requires_resume')
            if lease.get('pilotPolicy'):
                attempt_path=self.pilot_attempt_path(lease);need(not attempt_path.exists(),'pilot_attempt_spent')
                spent={'schema_version':3 if lease['pilotPolicy']['kind']==PILOT_V3 else 2 if parent else 1,'lease_id':self.lease_id,'job_id':ident,
                    'video_id':video,'source_binding_sha256':binding_hash(selected),'attempts_spent':1,'source_requests':0,
                    'spent_at_epoch':time.time(),'canonical_cooldown_preserved':True}
                if parent:spent.update(parent_job_id=parent['job_id'],parent_attempt_sha256=lease['pilotPolicy']['parent']['attemptSha256'],lineage_sha256=lineage)
                atomic(attempt_path,spent)
            state={'schema_version':1,'job_id':ident,'video_id':video,'state':'receiving','binding':selected,'binding_sha256':binding_hash(selected),
                   'queue_row':row,'queue_sha256':lease['queue_sha256'],'native_lease_id':self.lease_id,'owner':self.owner,
                   'offset':0,'next_seq':0,'prefix_sha256':hashlib.sha256(b'').hexdigest(),'output_budget_bytes':maximum,
                   'reservation_bytes':maximum+CONTROL_RESERVE,'segment_count':0,'segment_offset':0,'media_end_ms':0,'segment_ledger_sha256':'0'*64,
                   'created_at':self.core.utc_now()}
            previous=current.get(video,{})
            state['inherited_source_cooldown']={key:previous[key] for key in ('retry_not_before_epoch','source_error_class','native_browser_refusals','source_attempt_evidence') if key in previous}
            if lease.get('pilotPolicy'):
                state['acquisition_provenance']={'context_kind':lease['pilotPolicy']['acceptedContext'],
                    'basis':'resource_owner_lease_policy','pilot_policy_kind':lease['pilotPolicy']['kind'],'native_lease_id':self.lease_id}
            if parent:state.update(diagnostic_parent_job_id=parent['job_id'],diagnostic_lineage_sha256=lineage)
            if lease.get('pilotPolicy',{}).get('kind')==PILOT_V3:
                state['acquisition_provenance'].update(normal_playback_basis='user_reported_normal_chrome_playback',
                    normal_playback_evidence_sha256=lease['pilotPolicy']['normalPlaybackEvidence']['sha256'],normal_playback_observed_by_collector=False)
            folder.mkdir(parents=True);(folder/'audio.part').touch();atomic(folder/'metadata.pending.json',meta);atomic(folder/'state.json',state)
            sink=Sink(self,ident);self.live[ident]=sink;return sink

    def resume(self,job_id,selected):
        with self.lock:
            self.guard();need(re.fullmatch(r'native-[a-f0-9]{24}',job_id),'unsafe_job')
            need(job_id not in self.live,'job_already_open')
            sink=Sink(self,job_id);self.guard(source=True,context=sink.state());sink.verify_resume(selected);self.inventory(force=True)
            state=sink.state();state.update(resume_requires_response=state['offset']>0,resume_response_verified=False)
            atomic(sink.folder/'state.json',state);self.live[job_id]=sink;return sink

    def source_failure(self,code,retry_not_before_epoch=None):
        need(code in {'forbidden','rate_limited','bot_check'},'non_blocking_source_error')
        need(retry_not_before_epoch is None or type(retry_not_before_epoch) in {int,float} and math.isfinite(retry_not_before_epoch),'invalid_retry_deadline')
        self.source_stop.set()
        with self.lock:
            until=max(time.time()+86400,float(retry_not_before_epoch or 0))
            previous=latest_receipts(self.root/'sync/drive_ingest_manifest.jsonl')
            until=max([until]+[float(r.get('retry_not_before_epoch',0)) for r in previous.values()
                if r.get('source_error_class',r.get('error_class')) in {'forbidden','rate_limited','bot_check'}])
            old=self.root/'sync/native_batch_source_cooldown.json'
            if old.exists():until=max(until,read(old).get('retry_not_before_epoch',0))
            atomic(old,{'schema_version':1,'endpoint':'youtube_native_audio','error_class':code,'source_error_class':code,'retry_not_before_epoch':until,'updated_at':self.core.utc_now()})
            for state in self.states():
                if state.get('native_lease_id')==self.lease_id and state['state'] in {'receiving','retained'}:
                    state.update(state='retained',source_error_class=code,retry_not_before_epoch=until)
                    atomic(self.spool/'jobs'/state['job_id']/'state.json',state)
                    # Canonical journal preserves the source breaker for future native collectors.
                    old=previous.get(state['video_id'],{})
                    self.core.journal(self.root/'sync/drive_ingest_manifest.jsonl',{**old,**state['queue_row'],'status':'error','error_class':code,'source_error_class':code,'retry_not_before_epoch':until,'native_browser_refusals':int(old.get('native_browser_refusals',0))+1,'updated_at':self.core.utc_now()})
        if self.on_batch_abort:self.on_batch_abort(code)


class Sink:
    def __init__(self,coordinator,job_id):
        self.c=coordinator;self.job_id=job_id;self.folder=self.c.spool/'jobs'/job_id
        self.hash=hashlib.sha256();self._hash_loaded=False

    def state(self):return read(self.folder/'state.json')

    def verify_resume(self,selected):
        state=self.state();need(binding(selected)==state['binding'] and binding_hash(selected)==state['binding_sha256'],'resume_format_changed')
        need(state['state'] in {'receiving','retained'},'resume_state')
        part=self.folder/'audio.part';need(part.stat().st_size==state['offset'],'unacknowledged_tail_retained')
        observed=digest(part);need(observed['sha256']==state['prefix_sha256'],'resume_prefix_corrupt')
        need(state['binding']['transportKind']=='direct_http','sabr_protocol_resume_unproven')
        self._hash_loaded=False
        return {'byte_prefix_verified':True,'acknowledgedBytes':state['offset'],'nextSequence':state['next_seq'],
                'prefixSha256':state['prefix_sha256'],'sourceBindingSha256':state['binding_sha256'],
                'requires_exact_http_206_range_and_total':state['offset']>0,'sabrSnapshotResume':False}

    def authorize_direct_resume(self,*,status,range_start,total,binding_sha256):
        state=self.state();self.verify_resume(state['binding'])
        need(status==206 and range_start==state['offset'] and total==state['binding']['contentLength'] and binding_sha256==state['binding_sha256'],'resume_response_mismatch')
        state.update(state='receiving',resume_response_verified=True);atomic(self.folder/'state.json',state)

    def reserve(self,n):
        with self.c.lock:
            state=self.state();lease,_=self.c.guard(source=True,context=state)
            if lease.get('pilotPolicy'):need(state.get('source_requests',0)>0,'source_request_permit_required')
            need(type(n) is int and 0<n<=MAX_CHUNK,'chunk_size')
            need(state['offset']+n<=state['output_budget_bytes'],'output_budget_exceeded')
            self.c.inventory();return {'allowedBytes':n,'acknowledgedBytes':state['offset']}

    def authorize_request(self,proof):
        with self.c.lock:
            state=self.state();lease,_=self.c.guard(source=True,context=state)
            need(state['state']=='receiving' and set(proof)=={'sourceBindingSha256','requestSequence'} and
                 proof['sourceBindingSha256']==state['binding_sha256'],'source_request_identity')
            need(type(proof['requestSequence']) is int,'source_request_sequence')
            if lease.get('pilotPolicy'):
                path=self.c.pilot_attempt_path(lease);attempt=read(path)
                count=attempt['source_requests'];maximum=lease['pilotPolicy']['sourceRequestBudget']
                need(proof['requestSequence']==count+1 and count<maximum,'source_request_budget')
                attempt['source_requests']=count+1;atomic(path,attempt)
            else:
                count=state.get('source_requests',0);need(proof['requestSequence']==count+1,'source_request_sequence')
            state['source_requests']=count+1;atomic(self.folder/'state.json',state)
            return {'sourceBindingSha256':state['binding_sha256'],'requestSequence':count+1,'sourceRequests':count+1,'authorized':True}

    def write(self,value):
        with self.c.lock:
            state=self.state();need(state['state']=='receiving','source_not_receiving')
            need(not state.get('resume_requires_response') or state.get('resume_response_verified') is True,'resume_response_unverified')
            need(set(value)=={'offset','seq','bytes'} and type(value['seq']) is int and value['seq']==state['next_seq'] and type(value['offset']) is int and value['offset']==state['offset'],'chunk_sequence')
            data=value['bytes'];need(isinstance(data,(bytes,bytearray,memoryview)),'binary_required');self.reserve(len(data));data=bytes(data)
            part=self.folder/'audio.part';need(part.stat().st_size==state['offset'],'local_prefix_size_changed')
            if not self._hash_loaded:
                self.hash=hashlib.sha256()
                with part.open('rb') as src:
                    for block in iter(lambda:src.read(MAX_CHUNK),b''):self.hash.update(block)
                need(self.hash.hexdigest()==state['prefix_sha256'],'local_prefix_corrupt');self._hash_loaded=True
            with part.open('ab') as out:
                out.write(data);out.flush();os.fsync(out.fileno())
            self.hash.update(data);state.update(offset=state['offset']+len(data),next_seq=state['next_seq']+1,prefix_sha256=self.hash.hexdigest())
            atomic(self.folder/'state.json',state)
            return {'acknowledgedBytes':state['offset'],'nextSequence':state['next_seq'],'prefixSha256':state['prefix_sha256']}

    def segment(self,proof):
        """SABR VOD proof for one already-acknowledged native encoded segment."""
        fields={'number','initialization','startTimeMs','endTimeMs','declaredBytes','byteOffset','emittedBytes','sha256','initDiscardedBytes'}
        with self.c.lock:
            self.c.guard();state=self.state();need(state['binding']['transportKind']=='sabr_reassembled','not_sabr')
            need(isinstance(proof,dict) and set(proof)==fields,'segment_fields')
            for key in fields-{'initialization','sha256'}:
                need(type(proof[key]) is int and 0<=proof[key]<2**53,'segment_safe_integer')
            need(proof['number']==state['segment_count'],'segment_sequence')
            need(type(proof['initialization']) is bool and proof['initialization']==(proof['number']==0),'segment_initialization')
            need(type(proof['emittedBytes']) is int and proof['emittedBytes']>0 and proof['declaredBytes']==proof['emittedBytes'] and proof['initDiscardedBytes']==0,'segment_length')
            need(proof['byteOffset']==state['segment_offset'] and proof['byteOffset']+proof['emittedBytes']<=state['offset'],'segment_byte_coverage')
            need(isinstance(proof['sha256'],str) and re.fullmatch(r'[a-f0-9]{64}',proof['sha256']),'segment_hash_format')
            need(proof['endTimeMs']>=proof['startTimeMs'],'segment_time')
            if proof['initialization']:
                need(proof['startTimeMs']==proof['endTimeMs']==0,'initialization_time')
            else:
                need(proof['endTimeMs']>proof['startTimeMs'] and abs(proof['startTimeMs']-state['media_end_ms'])<=250,'segment_time_coverage')
            sha=hashlib.sha256();remaining=proof['emittedBytes']
            with (self.folder/'audio.part').open('rb') as source:
                source.seek(proof['byteOffset'])
                while remaining:
                    block=source.read(min(MAX_CHUNK,remaining));need(block,'segment_truncated');sha.update(block);remaining-=len(block)
            need(sha.hexdigest()==proof['sha256'],'segment_hash_mismatch')
            encoded=raw_json(proof);need(len(encoded)<4096,'segment_control_size')
            self.c.inventory(extra=len(encoded));state['reservation_bytes']+=len(encoded)
            ledger=self.folder/'segments.jsonl'
            # Ledger before summary; interrupted commits require explicit owner reconciliation.
            with ledger.open('ab') as output:output.write(encoded);output.flush();os.fsync(output.fileno())
            state.update(segment_count=state['segment_count']+1,segment_offset=state['segment_offset']+proof['emittedBytes'],
                         media_end_ms=proof['endTimeMs'],segment_ledger_bytes=ledger.stat().st_size,
                         segment_ledger_sha256=chain_hash(state['segment_ledger_sha256'],proof))
            atomic(self.folder/'state.json',state)
            return {'segmentCount':state['segment_count'],'ledgerSha256':state['segment_ledger_sha256']}

    def finish(self,completion):
        with self.c.lock:
            self.c.guard();state=self.state()
            need(state['state'] in {'receiving','retained','validation_queued','validating'},'finish_state')
            state['state']='validating';atomic(self.folder/'state.json',state)
        try:
            return self._finish_claimed(completion)
        except Exception as error:
            with self.c.lock:
                state=self.state()
                if state['state']=='validating':
                    state.update(state='retained',validation_error=getattr(error,'kind','validation_failed'))
                    atomic(self.folder/'state.json',state)
            raise

    def _finish_claimed(self,completion):
        self.c.guard();state=self.state();selected=state['binding']
        need(state['state']=='validating','finish_state')
        need(completion.get('sourceBindingSha256')==state['binding_sha256'] and completion.get('bytes')==state['offset'],'completion_identity')
        need(completion.get('protocolEos') is True and completion.get('reencoded') is False,'completion_eos')
        sabr=selected['transportKind']=='sabr_reassembled'
        if sabr:
            need(completion.get('container_reassembled') is True and completion.get('encoded_audio_not_reencoded') is True and
                 completion.get('isLive') is False and completion.get('stripDuplicateInit') is False,'sabr_vod_proof_required')
            need(state['segment_count']>=2 and state['segment_offset']==state['offset'] and completion.get('segmentCount')==state['segment_count'],'sabr_segment_coverage')
            need(completion.get('endSegmentNum')==state['segment_count']-1 and completion.get('endTimeMs')==state['media_end_ms'],'sabr_eos_identity')
            need(abs(state['media_end_ms']-selected['durationMs'])<=max(2000,selected['durationMs']*.002),'sabr_duration_coverage')
            ledger=self.folder/'segments.jsonl';need(ledger.stat().st_size==state['segment_ledger_bytes'],'sabr_uncommitted_segment')
            ledger_proof=digest(ledger)
            count=0;chain='0'*64
            with ledger.open(encoding='utf-8') as source:
                for line in source:
                    if line.strip():chain=chain_hash(chain,json.loads(line));count+=1
            need(count==state['segment_count'] and chain==state['segment_ledger_sha256']==completion.get('segmentLedgerSha256'),'sabr_segment_ledger_changed')
        else:
            need(state['offset']==selected['contentLength'],'truncated_native_file')
        part=self.folder/'audio.part';proof=digest(part)
        need(proof['bytes']==state['offset'] and proof['sha256']==state['prefix_sha256'],'completed_file_changed')
        evidence=self.c.probe(part,selected,self.c.ffprobe)
        # The injected adapter must report the same strict facts as the real full scan.
        need(evidence.get('audio_streams')==1 and evidence.get('video_streams')==0 and evidence.get('codec')==CODECS[selected['codec']],'invalid_probe_evidence')
        seconds=evidence.get('duration_seconds',0);expected=selected['durationMs']/1000
        need(type(seconds) in {int,float} and math.isfinite(seconds) and abs(seconds-expected)<=max(2,expected*.002),'duration_mismatch')
        video=state['video_id'];ext=MIME_EXT[selected['mimeType'].split(';')[0].strip()];audio=self.folder/(video+'.'+ext);metadata=self.folder/(video+'.info.json')
        meta=read(self.folder/'metadata.pending.json');meta.update(native_acquisition={'transport_kind':selected['transportKind'],'container_reassembled':sabr,
            'encoded_audio_not_reencoded':True,'source_binding':selected,'source_binding_sha256':state['binding_sha256'],'completion':evidence})
        if state.get('acquisition_provenance'):
            meta['native_acquisition']['provenance']=dict(state['acquisition_provenance'])
        if sabr:
            meta['native_acquisition']['sabr_segment_proof']={**ledger_proof,'ledger_chain_sha256':chain,'segment_count':state['segment_count'],'source_duration_ms':state['media_end_ms'],'init_discarded_bytes':0,'original_container_byte_identity_claimed':False}
            with self.c.lock:
                self.c.inventory(extra=ledger_proof['bytes']);state['reservation_bytes']+=ledger_proof['bytes'];atomic(self.folder/'state.json',state)
            # Stream the proof array into the one metadata sidecar, avoiding a growing RAM list.
            temp=metadata.with_suffix('.json.tmp')
            with temp.open('wb') as out,ledger.open('rb') as source:
                out.write(raw_json(meta).rstrip()[:-1]+b',"native_segment_proofs":[')
                first=True
                for line in source:
                    if not line.strip():continue
                    if not first:out.write(b',')
                    out.write(line.strip());first=False
                out.write(b']}\n');out.flush();os.fsync(out.fileno())
            os.replace(temp,metadata)
        else:atomic(metadata,meta)
        metadata_proof=digest(metadata)
        row=state['queue_row'];record={**row,**state.get('inherited_source_cooldown',{}),**proof,'status':'metadata_ready','path':str(audio.relative_to(self.c.root)).replace('\\','/'),
            'remote':self.c.core.remote_path(self.c.remote,row,ext),'metadata':{**metadata_proof,'path':str(metadata.relative_to(self.c.root)).replace('\\','/'),
            'remote':self.c.core.remote_path(self.c.remote,row,'info.json')},'native_transport_kind':selected['transportKind'],'native_format_binding':selected,
            'native_format_binding_sha256':state['binding_sha256'],'queue_row':row,'source_ext':ext,'source_format_id':str(selected['itag']),
            'duration_s':seconds,'downloaded_at':self.c.core.utc_now(),'native_validation':evidence}
        # Hashes and paths precede the promotion so a crash can be reconciled locally.
        state.update(state='local_validated',record=record);atomic(self.folder/'state.json',state)
        os.replace(part,audio);self.c.core.journal(self.c.root/'sync/drive_ingest_manifest.jsonl',record)
        return record


    def publish(self,drive):
        with self.c.lock:
            self.c.guard();state=self.state();need(state['state'] in {'local_validated','verified_cleanup','publishing'},'not_validated')
            need(self.job_id not in self.c.publishing,'upload_already_claimed')
            record=state['record'];audio=self.c.root/record['path'];metadata=self.c.root/record['metadata']['path']
            if not audio.exists() and (self.folder/'audio.part').exists():
                need(digest(self.folder/'audio.part')=={k:record[k] for k in ('bytes','md5','sha256')},'promotion_recovery_hash')
                os.replace(self.folder/'audio.part',audio)
            complete=(self.c.root/'sync/drive_ingest_manifest.jsonl')
            latest=latest_receipts(complete);old=latest.get(state['video_id'],{})
            recovering=old.get('status') in {'verified','deleted'} and old.get('sha256')==record['sha256'] and old.get('metadata',{}).get('sha256')==record['metadata']['sha256']
            self.c.publishing.add(self.job_id);state['state']='publishing';atomic(self.folder/'state.json',state)
        # Uploads run separately from the source write lock; no raw transport details leave browser.
        try:
            if not recovering:drive.copy_pair(audio,metadata,record['remote'],record['metadata']['remote'])
            with self.c.lock:
                self.c.guard()
                remote_proofs={'audio':drive.stat(record['remote']),'metadata':drive.stat(record['metadata']['remote'])}
                need(remote_proofs['audio'].get('ID') and remote_proofs['audio'].get('ID')!=remote_proofs['metadata'].get('ID'),'drive_pair_identity')
                result=self.c.core.verify_and_delete(self.c.root,record,drive,complete,require_metadata=True,allow_missing=recovering,remote_proofs=remote_proofs)
                need(self.c.core.receipt_complete(result,state['queue_row'],self.c.remote),'canonical_receipt_failed')
                state.update(state='deleted',record=result);atomic(self.folder/'state.json',state)
                self.c.live.pop(self.job_id,None)
                return result
        finally:
            with self.c.lock:self.c.publishing.discard(self.job_id)

    def retain(self,safe_error):
        need(safe_error in {'forbidden','rate_limited','bot_check','network','aborted','protocol','integrity'},'unsafe_error')
        with self.c.lock:
            state=self.state()
            if state['state']=='deleted':
                return {'retained':False,'state':'deleted','driveVerified':True,'proofStatePreserved':True}
            if state['state'] in {'validation_queued','validating','local_validated','publishing','verified_cleanup'}:
                state.update(late_control_error_class=safe_error,late_control_error_at=self.c.core.utc_now())
                atomic(self.folder/'state.json',state)
                return {'retained':False,'state':state['state'],'driveVerified':False,'proofStatePreserved':True}
            need(state['state'] in {'receiving','retained'},'retain_state')
            if safe_error not in {'forbidden','rate_limited','bot_check'}:
                state.update(state='retained',error_class=safe_error);atomic(self.folder/'state.json',state)
                return {'retained':True,'state':'retained','driveVerified':False,'proofStatePreserved':False}
        if safe_error in {'forbidden','rate_limited','bot_check'}:
            self.c.source_failure(safe_error)
            return {'retained':True,'state':self.state()['state'],'driveVerified':False,'proofStatePreserved':False}
