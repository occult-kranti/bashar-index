"""Bounded publisher-only VTT batch with injected, explicitly admitted I/O.

No default network, Drive, browser, audio or ASR implementation exists here.
Adapters own durable events, fresh controls, bounded transport and exact remote
stat proofs. Source text remains separate from native captions and transcripts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from email.utils import parsedate_to_datetime
import hashlib
import io
import json
import math
import re
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import zipfile

from .youtube_captions import normalize_caption

HOST = 'www.buzzsprout.com'
USER_AGENT = 'publisher-caption-reader/1.0 (python-urllib)'
MAX_RAW = 1_000_000
RESERVATION = 10_000_000
REQUEST_SECONDS = 30
_SHA = re.compile(r'[0-9a-f]{64}\Z')


class CaptionBatchError(ValueError):
    pass


def need(value, reason):
    if not value: raise CaptionBatchError(reason)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fingerprint(raw):
    return {'bytes':len(raw), 'md5':hashlib.md5(raw).hexdigest(), 'sha256':sha(raw)}


@dataclass(frozen=True)
class Candidate:
    video_id: str
    channel_dir: str
    episode_guid: str
    caption_url: str
    title: str
    feed_sha256: str
    authority_sha256: str
    episode_evidence_sha256: str
    native_audio_receipt_sha256: str
    language: str = 'en-US'

    def __post_init__(self):
        need(isinstance(self.video_id,str) and re.fullmatch(r'[A-Za-z0-9_-]{11}',self.video_id), 'video_id')
        need(isinstance(self.channel_dir,str) and re.fullmatch(r'[a-z0-9][a-z0-9-]{0,119}',self.channel_dir), 'channel')
        need(re.fullmatch(r'Buzzsprout-[0-9]+',self.episode_guid or ''), 'episode_guid')
        p=urlsplit(self.caption_url)
        need(p.scheme=='https' and p.netloc==HOST and not p.query and not p.fragment and
             re.fullmatch(r'/[0-9]+/'+self.episode_guid.split('-')[1]+r'/transcript\.vtt',p.path), 'static_vtt_url')
        need(isinstance(self.title,str) and len(self.title)<=1000 and self.language=='en-US', 'declared_language_or_title')
        need(all(isinstance(v,str) and _SHA.fullmatch(v) for v in (self.feed_sha256,self.authority_sha256,
             self.episode_evidence_sha256,self.native_audio_receipt_sha256)), 'evidence_pin')


def scope_sha256(candidates):
    need(isinstance(candidates,tuple) and 1<=len(candidates)<=3 and all(isinstance(c,Candidate) for c in candidates), 'immutable_exact_scope')
    need(len({c.video_id for c in candidates})==len(candidates) and
         len({c.caption_url for c in candidates})==len(candidates), 'duplicate_scope')
    return sha(encoded([asdict(c) for c in candidates]))


@dataclass(frozen=True)
class Grant:
    lease_id: str
    root_grant_sha256: str
    scope_sha256: str
    robots_sha256: str
    expires_at_epoch: float
    enabled: bool = False
    source_authorized: bool = False
    drive_authorized: bool = False
    reservation_bytes: int = RESERVATION
    vtt_GET_limit: int = 3


@dataclass(frozen=True)
class GuardProof:
    lease_id: str
    root_grant_sha256: str
    scope_sha256: str
    control_manifest_sha256: str
    checked_at_epoch: float
    managed_projected_bytes: int
    owner_projected_bytes: int
    physical_free_bytes: int
    reservation_bytes: int
    lease_active: bool = False
    reservation_active: bool = False
    root_stop: bool = False
    host_hold_until_epoch: float = 0
    drive_hold_until_epoch: float = 0
    denied_request_sha256s: tuple[str,...] = ()


@dataclass(frozen=True)
class FetchRequest:
    url: str
    deadline_epoch: float
    maximum_bytes: int = MAX_RAW
    method: str = 'GET'
    user_agent: str = USER_AGENT
    retries: int = 0
    redirects: int = 0


@dataclass(frozen=True)
class FetchResponse:
    final_url: str
    status: int
    body: bytes
    finished_at_epoch: float
    content_type: str = 'text/vtt'
    content_encoding: str = 'identity'
    content_length: int | None = None
    retry_after: str | None = None
    wire_GETs: int = 1
    redirects_followed: int = 0
    protection_detected: bool = False
    complete_body: bool = True


@dataclass(frozen=True)
class Artifacts:
    bundle: bytes
    provenance: bytes
    relative_parent: str

    def proofs(self):
        return {'bundle':fingerprint(self.bundle), 'provenance':fingerprint(self.provenance)}


def build_artifacts(candidate, raw, scope_pin):
    need(isinstance(raw,bytes) and 0<len(raw)<=MAX_RAW, 'caption_body_bound')
    normalized=normalize_caption(raw,'vtt')
    segments=encoded(normalized); text=normalized['text'].encode('utf-8')
    need(len(segments)<=4_000_000 and len(text)<=MAX_RAW, 'caption_normalization_bound')
    provenance={'schema_version':1,'content_kind':'publisher_source','provider':'Buzzsprout',
        'associated_youtube_id':candidate.video_id,'channel_dir':candidate.channel_dir,
        'episode_guid':candidate.episode_guid,'title':candidate.title,'scope_sha256':scope_pin,
        'association_method':'official_feed_item_exact_youtube_link','exact_reference_saved':True,
        'youtube_edit_identity_verified':False,'alignment_reviewed':False,'speech_coverage_verified':False,
        'manual_vs_automatic':'unknown','translation_status':'not_declared','language':candidate.language,
        'language_basis':'publisher_rss_channel','track_language_verified':False,'audio_binding':None,
        'associated_native_audio_receipt_sha256':candidate.native_audio_receipt_sha256,
        'feed_sha256':candidate.feed_sha256,'authority_sha256':candidate.authority_sha256,
        'episode_evidence_sha256':candidate.episode_evidence_sha256,'raw_source':fingerprint(raw),
        'segment_count':len(normalized['segments']),'normalization_version':normalized['normalization_version'],
        'native_youtube_caption':False,'changes_native_audio_count':False,'changes_full_asr_count':False}
    inner=encoded(provenance)
    need(len(inner)<=32_000, 'provenance_bound')
    members={'raw.vtt':raw,'segments.json':segments,'transcript.txt':text,'provenance.json':inner}
    members['manifest.json']=encoded({name:fingerprint(value) for name,value in members.items()})
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_STORED) as archive:
        for name,value in members.items():
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.external_attr=0o600<<16
            archive.writestr(info,value)
    bundle=output.getvalue()
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        need(archive.testzip() is None and set(archive.namelist())==set(members) and
             all(archive.read(name)==value for name,value in members.items()), 'caption_bundle_integrity')
    sidecar=encoded(dict(provenance,bundle=fingerprint(bundle)))
    need(len(bundle)<=6_100_000 and len(sidecar)<=64_000 and
         len(raw)+len(bundle)+len(sidecar)+1_000_000<=RESERVATION, 'caption_storage_bound')
    parent=candidate.channel_dir+'/PublisherSourceText/'+candidate.video_id+'/'+sha(bundle)
    return Artifacts(bundle,sidecar,parent)


class CaptionBatch:
    """Sequential one-attempt fetch→normalize→paired-proof→durable receipt→cleanup.

    All callbacks are explicit. guard returns fresh scope/resource/control facts;
    event is a durable private journal; retain_raw preserves the original before
    parsing. fetch MUST enforce the request deadline/body limit before returning.
    publish returns exact remote stat proofs for two artifacts. cleanup acts on
    owned files only after the durable pair_verified event. No native journal is
    used; original raw/proofs survive every unsuccessful path.
    """
    def __init__(self,candidates,grant,*,robots_raw,robots_checked_at_epoch,guard,event,
                 fetch,retain_raw,publish,cleanup,record_hold,clock=time.time):
        self.candidates=candidates;self.scope=scope_sha256(candidates);self.grant=grant
        need(isinstance(grant,Grant), 'grant_type')
        need(all(callable(f) for f in (guard,event,fetch,retain_raw,publish,cleanup,record_hold,clock)), 'io_adapters_required')
        need(isinstance(robots_raw,bytes) and 0<len(robots_raw)<=262144 and sha(robots_raw)==grant.robots_sha256, 'robots_pin')
        self.robots=RobotFileParser();self.robots.parse(robots_raw.decode('utf-8-sig').splitlines())
        self.robots_checked=robots_checked_at_epoch;self.guard=guard;self.event=event;self.fetch=fetch
        self.retain_raw=retain_raw;self.publish=publish;self.cleanup=cleanup;self.record_hold=record_hold
        self.clock=clock;self.started=False

    def _guard(self,stage,candidate):
        now=self.clock();g=self.grant
        need(g.enabled is True and g.source_authorized is True and g.drive_authorized is True and
             g.scope_sha256==self.scope and g.reservation_bytes==RESERVATION and
             type(g.vtt_GET_limit) is int and len(self.candidates)<=g.vtt_GET_limit<=3 and
             isinstance(g.root_grant_sha256,str) and _SHA.fullmatch(g.root_grant_sha256) and
             type(g.expires_at_epoch) in (int,float) and math.isfinite(g.expires_at_epoch) and now<g.expires_at_epoch,
             'exact_active_grant_required')
        p=self.guard(stage,candidate)
        now=self.clock()
        need(now<g.expires_at_epoch,'grant_expired_during_guard')
        need(isinstance(p,GuardProof) and p.lease_id==g.lease_id and p.root_grant_sha256==g.root_grant_sha256 and
             p.scope_sha256==self.scope and isinstance(p.control_manifest_sha256,str) and _SHA.fullmatch(p.control_manifest_sha256)
             and 0<=now-p.checked_at_epoch<=2 and p.root_stop is False and p.reservation_bytes==RESERVATION,
             'fresh_admission_required')
        need(p.lease_active is True and p.reservation_active is True,'active_lease_and_reservation_required')
        need(all(type(v) is int and v>=0 for v in (p.managed_projected_bytes,p.owner_projected_bytes,p.physical_free_bytes)) and
             p.managed_projected_bytes<=16_000_000_000 and p.owner_projected_bytes<=18_000_000_000 and
             p.physical_free_bytes>=2_000_000_000, 'caption_capacity')
        need(p.host_hold_until_epoch<=now and sha(candidate.caption_url.encode()) not in p.denied_request_sha256s,
             'publisher_host_or_exact_request_hold')
        need(p.drive_hold_until_epoch<=now,'drive_hold')
        need(type(self.robots_checked) in (int,float) and 0<=now-self.robots_checked<=86400 and
             self.robots.can_fetch(USER_AGENT,candidate.caption_url), 'robots_unknown_expired_or_disallowed')
        return p

    def run(self):
        need(not self.started,'caption_batch_one_shot');self.started=True
        outcomes=[];invoked=0;stopped=False
        for candidate in self.candidates:
            if stopped:
                outcomes.append({'video_id':candidate.video_id,'state':'pending'});continue
            retained=False;verified=False
            try:
                before=self._guard('source',candidate)
                request=FetchRequest(candidate.caption_url,min(self.clock()+REQUEST_SECONDS,self.grant.expires_at_epoch))
                request_pin=sha(encoded(asdict(request)))
                self.event({'kind':'request_started','video_id':candidate.video_id,'request_sha256':request_pin,
                            'scope_sha256':self.scope})  # Durable BEFORE the one permitted invocation.
                invoked+=1;response=self.fetch(request)
                need(isinstance(response,FetchResponse),'transport_response_contract')
                need(response.final_url==request.url and type(response.wire_GETs) is int and response.wire_GETs==1 and
                     type(response.redirects_followed) is int and response.redirects_followed==0,
                     'unexpected_transport_or_redirect')
                complete_200=(response.status==200 and isinstance(response.body,bytes) and 0<len(response.body)<=MAX_RAW and
                     response.complete_body is True and
                     (response.content_length is None or (type(response.content_length) is int and response.content_length==len(response.body))) and
                     response.finished_at_epoch<=request.deadline_epoch and self.clock()<=request.deadline_epoch)
                if complete_200:
                    # Retain accepted bytes even when a response directive or
                    # subsequent revocation prevents any further processing.
                    self.retain_raw(candidate,response.body,fingerprint(response.body));retained=True
                need(response.status not in (401,403,429) and response.retry_after is None and not response.protection_detected,
                     'publisher_refusal')
                if response.status in (404,410):
                    need(isinstance(response.body,bytes) and len(response.body)<=MAX_RAW and response.complete_body is True and
                         response.content_encoding.lower() in ('','identity') and
                         (response.content_length is None or (type(response.content_length) is int and response.content_length==len(response.body))) and
                         response.finished_at_epoch<=request.deadline_epoch and self.clock()<=request.deadline_epoch,
                         'unavailable_response_unproven')
                    self.event({'kind':'http_observation','video_id':candidate.video_id,'status':response.status,
                                'request_sha256':request_pin,'body_proof':fingerprint(response.body),'complete_body':True})
                    self.event({'kind':'item_unavailable','video_id':candidate.video_id,'status':response.status,
                                'request_sha256':request_pin,'automatic_retry':False})
                    outcomes.append({'video_id':candidate.video_id,'state':'unavailable','status':response.status})
                    continue
                need(complete_200,'caption_response_bound')
                self._guard('write',candidate)
                need(response.content_encoding.lower() in ('','identity') and
                     response.content_type.split(';')[0].lower().strip() in {'text/vtt','text/plain','application/octet-stream'},
                     'caption_content_type_or_encoding')
                artifacts=build_artifacts(candidate,response.body,self.scope)
                self._guard('publish',candidate);receipt=self.publish(candidate,artifacts)
                need(isinstance(receipt,dict) and set(receipt)=={'bundle','provenance'},'paired_archive_proof_required')
                ids=[]
                for name,expected in artifacts.proofs().items():
                    proof=receipt[name];filename='publisher-captions.zip' if name=='bundle' else 'provenance.json'
                    need(isinstance(proof,dict) and proof.get('local_proof')==expected,'paired_archive_local_mismatch')
                    observed=proof.get('remote_proof')
                    need(isinstance(observed,dict) and observed.get('bytes')==expected['bytes'] and
                         observed.get('md5')==expected['md5'] and isinstance(observed.get('drive_id'),str) and
                         bool(observed['drive_id']) and observed.get('relative_path')==artifacts.relative_parent+'/'+filename,
                         'paired_archive_remote_mismatch')
                    ids.append(observed['drive_id'])
                need(len(set(ids))==2,'paired_archive_identity')
                self.event({'kind':'pair_verified','video_id':candidate.video_id,'scope_sha256':self.scope,
                            'content_kind':'publisher_source','native_youtube_caption':False,'proofs':receipt})
                verified=True
                self.cleanup(candidate,receipt)
                outcomes.append({'video_id':candidate.video_id,'state':'verified','local_cleanup':'complete'})
            except Exception as error:
                supplied=error.args[0] if isinstance(error,CaptionBatchError) and error.args else None
                reason=supplied if isinstance(supplied,str) and re.fullmatch(r'[a-z0-9_]{1,80}',supplied) else 'publisher_caption_operation_failed'
                if reason=='publisher_refusal':
                    until=max(self.clock()+86400,before.host_hold_until_epoch);review=False
                    if response.retry_after is not None:
                        try:
                            raw=response.retry_after.strip(' \t')
                            need(bool(raw),'empty_retry_after_requires_review')
                            requested=self.clock()+int(raw) if raw.isdigit() else parsedate_to_datetime(raw).timestamp()
                            until=max(until,requested)
                        except (ValueError,TypeError,OverflowError,AttributeError):review=True
                    hold={'provider':'Buzzsprout','host':HOST,'endpoint':'publisher_transcript_vtt','status':response.status,
                          'request_sha256':request_pin,'retry_not_before_epoch':until,'retry_after_requires_review':review,
                          'request_url_sha256':sha(candidate.caption_url.encode()),
                          'automatic_retry':False}
                    try:
                        persisted=self.record_hold(hold)
                        need(isinstance(persisted,dict) and persisted.get('history_preserved') is True and
                             persisted.get('retry_not_before_epoch',0)>=until,'hold_persistence_failed')
                    except Exception:reason='hold_persistence_failed'
                outcomes.append({'video_id':candidate.video_id,'state':'verified' if verified else 'retained' if retained else 'held',
                                 'reason':reason,'local_cleanup':'retained' if retained else 'unproven'})
                stopped=True
        return {'schema_version':1,'status':'held' if stopped else 'complete','scope_sha256':self.scope,
                'transport_invocations':invoked,'outcomes':outcomes,'audio_requests':0,'YouTube_requests':0,'ASR_jobs':0}
