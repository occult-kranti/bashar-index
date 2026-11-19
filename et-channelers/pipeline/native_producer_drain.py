"""Pause new producer admissions after proved closed native tickets; no media I/O.

The installed frame control remains responsible for authority and its lock.
This monitor neither starts native work nor interrupts already admitted bodies.
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import time

from .native_handoff_queue import NativeHandoffQueue, SHA256, VIDEO_ID, closed_ticket


def _json(path, maximum=2_000_000):
    with Path(path).open('rb') as stream:
        raw=stream.read(maximum+1)
    if not 0<len(raw)<=maximum:
        raise ValueError('bounded_producer_metadata_required')
    value=json.loads(raw)
    if not isinstance(value,dict):
        raise ValueError('producer_metadata_object_required')
    return value


def _fingerprint(path):
    path=Path(path)
    if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
        raise ValueError('linked_producer_artifact_rejected')
    value=path.stat()
    return (value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns)


def _present(path):
    try:
        _fingerprint(path)
    except FileNotFoundError as error:
        if error.errno!=errno.ENOENT or error.filename is not None and Path(error.filename)!=path:
            raise
        return False
    return True


def pin(path, maximum=2_000_000):
    path=Path(path)
    before=_fingerprint(path)
    with path.open('rb') as stream:
        raw=stream.read(maximum+1)
    if not 0<len(raw)<=maximum or _fingerprint(path)!=before:
        raise ValueError('changed_or_oversize_producer_artifact')
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def _write_new(path,value):
    raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with Path(path).open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())


class ClosedProducerMonitor:
    """Stat cached immutable evidence; parse each newly closed child only once.

    Missing results/audits before a child closes mean pending. Malformed,
    unreadable, changed or missing evidence of an already closed child raises;
    it is never converted to an empty batch. No progress sample is cached here.
    """
    def __init__(self, jobs, registry, *, grant_sha256, group_size=16):
        self.jobs=Path(jobs)
        if not self.jobs.is_absolute() or self.jobs.resolve()!=self.jobs.absolute():
            raise ValueError('exact_unlinked_jobs_root_required')
        ids=registry.get('video_ids');rows=registry.get('candidates')
        if (not isinstance(ids,list) or not 1<=len(ids)<=96 or len(set(ids))!=len(ids)
                or any(not isinstance(v,str) or not VIDEO_ID.fullmatch(v) for v in ids)
                or not isinstance(rows,list) or len(rows)!=len(ids)
                or not isinstance(grant_sha256,str) or not SHA256.fullmatch(grant_sha256)):
            raise ValueError('finite_producer_registry_required')
        self.rows={}
        for row in rows:
            video=row.get('video_id');channel=row.get('expected_channel_id')
            if (video not in ids or video in self.rows or not isinstance(channel,str)
                    or not re.fullmatch(r'UC[A-Za-z0-9_-]{22}',channel)):
                raise ValueError('producer_channel_identity_required')
            self.rows[video]=row
        self.ids=ids[:];self.grant=grant_sha256
        self.queue=NativeHandoffQueue(group_size=group_size)
        self._closed={};self._native=set();self.validation_count=0

    def poll(self, now, *, producer_memory_idle=False):
        if type(now) not in (int,float) or not math.isfinite(now) or now<=0:
            raise ValueError('valid_producer_observation_clock_required')
        for video in self.ids:
            job=self.jobs/video
            if job.is_symlink() or getattr(job,'is_junction',lambda:False)():
                raise ValueError('linked_producer_job_rejected')
            if video in self._closed:
                if any(_fingerprint(path)!=value for path,value in self._closed[video].items()):
                    raise ValueError('changed_closed_producer_evidence')
                # A closed zero-media ticket must never acquire a media GO.
                if video in self._native and any(_present(job/name) for name in
                        ('MEDIA_GO.json','response-headers.json','BODY_GO.json','native-audio.mp4','audio-extract.m4a')):
                    raise ValueError('closed_producer_acquired_media')
                continue
            audit_path=job/'parent-audit.json';result_path=job/'result.json'
            if not _present(audit_path) or not _present(result_path):
                continue
            paths=[audit_path,result_path,job/'attempt.json']
            before={path:_fingerprint(path) for path in paths}
            audit=_json(audit_path,512_000);result=_json(result_path)
            closure=audit.get('owned_closure') or {}
            if (audit.get('video_id')!=video or audit.get('root_grant_sha256')!=self.grant
                    or result.get('video_id')!=video or audit.get('owned_processes_gone') is not True
                    or not isinstance(closure,dict) or any(closure.get(k) is not True for k in
                        ('closed','owned_process_closed','owned_job_empty','job_handle_released'))
                    or closure.get('errors')!=[]):
                raise ValueError('closed_producer_ownership_unproven')
            attempt=pin(job/'attempt.json',64_000)
            if audit.get('attempt_sha256')!=attempt['sha256']:
                raise ValueError('closed_producer_attempt_changed')
            if result.get('status')=='native_route_pending':
                private=job/'native-route-private.metadata.json'
                before[private]=_fingerprint(private)
                ticket=closed_ticket(job,video_id=video,channel_id=self.rows[video]['expected_channel_id'],
                    grant_sha256=self.grant,attempt_sha256=attempt['sha256'],closed_at=now)
                self.queue.observe(ticket)
                self._native.add(video)
            if any(_fingerprint(path)!=value for path,value in before.items()):
                raise ValueError('producer_evidence_changed_during_validation')
            self._closed[video]=before;self.validation_count+=1
        return self.queue.boundary(now,producer_memory_idle=producer_memory_idle)

    def evidence(self):
        return {**self.queue.evidence(),'validated_closed_children':len(self._closed),
            'immutable_child_validations':self.validation_count,'progress_samples_cached':False}


def request_installed_drain(frame, scope_sha256, *, kernel_code, kernel_sha256):
    """Use the pinned installed control with its required isolated-import path.

    Avoid executing scope_drain.py directly under -I: its shared kernel import
    needs this explicit verified bootstrap. The control rechecks live authority.
    """
    frame=Path(frame).resolve();kernel=Path(kernel_code).resolve()
    if not SHA256.fullmatch(scope_sha256) or pin(kernel)['sha256']!=kernel_sha256:
        raise ValueError('pinned_scope_and_kernel_required')
    settings=_json(frame/'settings.json')
    control=frame/'scope_drain.py'
    matches=[p for p in settings.get('code_pins',[]) if Path(p['path']).resolve()==control]
    if len(matches)!=1 or pin(control)!=matches[0]:
        raise ValueError('installed_admission_only_control_changed')
    previous=sys.path[:]
    try:
        sys.path.insert(0,str(kernel.parent));sys.path.insert(0,str(frame))
        spec=importlib.util.spec_from_file_location('_installed_producer_drain',control)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module.issue(frame,scope_sha256)
    finally:
        sys.path[:]=previous


def request_once(frame, monitor, boundary, *, scope_sha256, kernel_code, kernel_sha256,
                 request=request_installed_drain):
    """Durable intent before one local request; unresolved intent never replays."""
    frame=Path(frame);intent=frame/'native-producer-drain-intent.json'
    proof=frame/'native-producer-drain-proof.json'
    binding={'frame':str(frame),'grant_sha256':monitor.grant,'scope_sha256':scope_sha256,
        'installed_admission_only_control':pin(frame/'scope_drain.py'),
        'kernel_component':pin(kernel_code)}
    if binding['kernel_component']['sha256']!=kernel_sha256 or not SHA256.fullmatch(scope_sha256):
        raise ValueError('producer_control_binding_changed')
    if proof.exists():
        saved=_json(proof)
        if saved.get('binding')!=binding or saved.get('status')!='admission_only_drain_requested':
            raise ValueError('producer_drain_proof_mismatch')
        return saved
    if intent.exists():
        raise ValueError('unresolved_producer_drain_intent')
    if boundary is None or boundary!=monitor.queue.boundary(boundary['at_epoch']):
        raise ValueError('validated_producer_boundary_required')
    _write_new(intent,{'schema_version':1,'binding':binding,'boundary':boundary,'evidence':monitor.evidence(),
        'Source_requests':0,'Drive_requests':0,'active_body_cancelled':False})
    result=request(frame,scope_sha256,kernel_code=kernel_code,kernel_sha256=kernel_sha256)
    if not isinstance(result,dict):
        raise ValueError('installed_drain_result_required')
    value={'schema_version':1,'status':'admission_only_drain_requested','binding':binding,
        'boundary':boundary,'evidence':monitor.evidence(),'installed_control_result':result,
        'Source_requests':0,'Drive_requests':0,'active_body_cancelled':False,'at_epoch':time.time()}
    _write_new(proof,value)
    return value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('frame','private-root','scope-sha256','kernel-code','kernel-sha256'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--threshold',type=int,default=16)
    parser.add_argument('--poll-seconds',type=float,default=2)
    parser.add_argument('--maximum-seconds',type=float,default=8*3600)
    args=parser.parse_args(argv)
    if (not 6<=args.threshold<=24 or not math.isfinite(args.poll_seconds) or not .05<=args.poll_seconds<=60
            or not math.isfinite(args.maximum_seconds) or not 0<args.maximum_seconds<=8*3600):
        raise ValueError('finite_producer_monitor_bounds_required')
    frame=Path(args.frame).resolve();root=Path(args.private_root).resolve()
    registry=_json(frame/'registry.json');profile=registry.get('profile')
    if not isinstance(profile,str) or not re.fullmatch(r'[A-Za-z0-9_]{1,128}',profile):
        raise ValueError('producer_profile_required')
    inputs={name:pin(frame/name) for name in ('registry.json','root-grant.ACTIVE.json','settings.json')}
    fingerprints={name:_fingerprint(frame/name) for name in inputs}
    monitor=ClosedProducerMonitor(root/profile/'jobs',registry,
        grant_sha256=inputs['root-grant.ACTIVE.json']['sha256'],group_size=args.threshold)
    if (_present(frame/'native-producer-drain-proof.json')
            or _present(frame/'native-producer-drain-intent.json')):
        # A restarted monitor must not wait for an expired ticket or replay an
        # action whose intent was already committed by a previous process.
        request_once(frame,monitor,None,scope_sha256=args.scope_sha256,
            kernel_code=args.kernel_code,kernel_sha256=args.kernel_sha256)
        print(json.dumps({'status':'existing_admission_only_drain_proof',
            'proof':pin(frame/'native-producer-drain-proof.json'),'Source_requests':0,'Drive_requests':0}))
        return 0
    deadline=time.monotonic()+args.maximum_seconds
    while time.monotonic()<deadline:
        if any(_fingerprint(frame/name)!=value for name,value in fingerprints.items()):
            raise ValueError('producer_frame_binding_changed')
        if _present(frame/'handoff/final-batch-terminal-handoff.json'):
            print(json.dumps({'status':'producer_already_sealed','Source_requests':0,'Drive_requests':0}))
            return 0
        boundary=monitor.poll(time.time())
        if boundary:
            request_once(frame,monitor,boundary,scope_sha256=args.scope_sha256,
                kernel_code=args.kernel_code,kernel_sha256=args.kernel_sha256)
            print(json.dumps({'proof':pin(frame/'native-producer-drain-proof.json'),
                'native_tickets':len(boundary['video_ids']),'Source_requests':0,'Drive_requests':0}))
            return 0
        time.sleep(args.poll_seconds)
    raise ValueError('finite_producer_monitor_expired')


if __name__=='__main__':
    raise SystemExit(main())
