"""Choose a graceful producer-frame boundary for already observed native audio.

A ticket is scheduling evidence. The existing closed-frame native adapter
still validates the selected asset, signed lifetime, budget and current
provider state before any media request.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import re


VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")


@dataclass(frozen=True)
class ProducerTicket:
    video_id: str
    source_bytes: int
    expiry_epoch: int
    closed_at_epoch: float
    result_sha256: str
    audit_sha256: str
    private_metadata_sha256: str


def _read_json(path, maximum):
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if not raw or len(raw) > maximum:
        raise ValueError("Invalid producer artifact size")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Invalid producer artifact structure")
    return data, hashlib.sha256(raw).hexdigest()


def closed_ticket(job, *, video_id, channel_id, grant_sha256, attempt_sha256, closed_at):
    """Validate the closed metadata-producing child without exposing a media URL."""
    job = Path(job)
    if (not isinstance(video_id, str) or not VIDEO_ID.fullmatch(video_id) or job.name != video_id
            or not isinstance(channel_id, str) or not re.fullmatch(r"UC[A-Za-z0-9_-]{22}", channel_id)
            or not all(isinstance(x, str) and SHA256.fullmatch(x) for x in (grant_sha256, attempt_sha256))
            or type(closed_at) not in (float, int) or not math.isfinite(closed_at) or closed_at <= 0):
        raise ValueError("Invalid producer identity")
    audit, audit_sha = _read_json(job / "parent-audit.json", 512_000)
    result, result_sha = _read_json(job / "result.json", 2_000_000)
    meta, meta_sha = _read_json(job / "native-route-private.metadata.json", 2_000_000)
    _, attempt = _read_json(job / "attempt.json", 64_000)
    closure = audit.get("owned_closure") or {}
    cleanup = audit.get("profile_cleanup") or {}
    safe = result.get("safe_native_route") or {}
    if not all(isinstance(v,dict) for v in (closure,cleanup,safe)):
        raise ValueError("Invalid producer closure or route")
    identity = safe.get("fresh_source_identity") or {}
    selection = meta.get("private_selected_info") or {}
    diagnostics = result.get("diagnostics") or {}
    if not all(isinstance(v,dict) for v in (identity,selection,diagnostics)):
        raise ValueError("Invalid producer selection or diagnostics")
    literal = meta.get("expires_query_literal")
    if (attempt != attempt_sha256 or audit.get("video_id") != video_id
            or audit.get("root_grant_sha256") != grant_sha256 or audit.get("attempt_sha256") != attempt_sha256
            or audit.get("owned_processes_gone") is not True or audit.get("parent_error") is not None
            or any(closure.get(k) is not True for k in ("closed","owned_process_closed","owned_job_empty","job_handle_released"))
            or closure.get("errors") != [] or cleanup.get("cleaned") is not True
            or result.get("status") != "native_route_pending" or result.get("video_id") != video_id
            or type(diagnostics.get("media_requests")) is not int or diagnostics["media_requests"] != 0
            or diagnostics.get("phase") != "terminal"
            or safe != meta.get("safe_route") or safe.get("video_id") != video_id
            or safe.get("native_saved") is not False or safe.get("source_media_GETs") != 0
            or safe.get("provider_explicit_original_label") is not True or identity.get("fresh_identity_match") is not True
            or identity.get("video_id") != video_id or identity.get("fresh_channel_id") != channel_id
            or identity.get("expected_channel_id") != channel_id or meta.get("not_saved") is not True
            or meta.get("Source_media_GETs") != 0 or selection.get("id") != video_id or selection.get("channel_id") != channel_id
            or selection.get("vcodec") != "none" or selection.get("format_id") != safe.get("format_id")
            or not isinstance(literal, list) or len(literal) != 1 or not isinstance(literal[0], str)
            or not re.fullmatch(r"[0-9]{1,12}",literal[0])
            or type(selection.get("filesize")) is not int or not 0 < selection["filesize"] <= 2_000_000_000):
        raise ValueError("Unqualified producer ticket")
    if any((job / name).exists() for name in ("MEDIA_GO.json","response-headers.json","BODY_GO.json","native-audio.mp4","audio-extract.m4a")):
        raise ValueError("Producer already admitted selected media")
    return ProducerTicket(video_id, selection["filesize"], int(literal[0]), float(closed_at), result_sha, audit_sha, meta_sha)


def group_size_for_switch(switch_seconds, native_seconds_per_pair):
    """Target at most one quarter of active time in an additional owner switch."""
    if any(type(x) not in (int,float) or not math.isfinite(x) or x<=0
           for x in (switch_seconds,native_seconds_per_pair)):
        raise ValueError("Expected measured positive durations")
    return min(24,max(6,math.ceil(3*switch_seconds/native_seconds_per_pair)))


class NativeHandoffQueue:
    """Only producer admissions pause. The owner can always drain and seal."""
    def __init__(self, *, group_size=16, native_min_lifetime=180, drain_margin=300):
        if (type(group_size) is not int or not 1 <= group_size <= 24
                or type(native_min_lifetime) is not int or native_min_lifetime < 180
                or type(drain_margin) is not int or not 0 <= drain_margin <= 3600):
            raise ValueError("Invalid handoff boundary")
        self.group_size = group_size
        self.native_min_lifetime = native_min_lifetime
        self.drain_margin = drain_margin
        self._tickets = {}
        self._boundary = None

    def observe(self, ticket):
        if (not isinstance(ticket, ProducerTicket) or not VIDEO_ID.fullmatch(ticket.video_id)
                or type(ticket.source_bytes) is not int or ticket.source_bytes <= 0
                or type(ticket.expiry_epoch) is not int or not all(SHA256.fullmatch(v)
                for v in (ticket.result_sha256,ticket.audit_sha256,ticket.private_metadata_sha256))):
            raise ValueError("Invalid closed producer ticket")
        previous = self._tickets.setdefault(ticket.video_id,ticket)
        if previous != ticket:
            raise ValueError("Changed closed producer ticket")

    def boundary(self, now, *, producer_memory_idle=False):
        if type(now) not in (float,int) or not math.isfinite(now):
            raise ValueError("Invalid handoff clock")
        if self._boundary is None:
            valid = [t for t in self._tickets.values() if t.expiry_epoch > now + self.native_min_lifetime]
            valid.sort(key=lambda t:(t.expiry_epoch,t.closed_at_epoch,t.video_id))
            reason = None
            if len(valid) >= self.group_size:
                reason = "native_handoff_batch_ready"
            elif valid and valid[0].expiry_epoch <= now + self.native_min_lifetime + self.drain_margin:
                reason = "native_handoff_expiry_near"
            elif producer_memory_idle and len(valid)>=min(6,self.group_size):
                reason = "native_handoff_producer_memory_idle"
            if reason:
                self._boundary = {"reason":reason, "at_epoch":now, "eligible_at_boundary":len(valid),
                    "video_ids":[t.video_id for t in valid], "known_native_bytes":sum(t.source_bytes for t in valid),
                    "earliest_literal_expiry":valid[0].expiry_epoch}
        return {**self._boundary,"video_ids":list(self._boundary["video_ids"])} if self._boundary else None

    def evidence(self):
        return {"tickets":[asdict(t) for t in self._tickets.values()],
                "boundary":dict(self._boundary) if self._boundary else None,
                "group_size":self.group_size, "minimum_native_lifetime_seconds":self.native_min_lifetime,
                "drain_margin_seconds":self.drain_margin, "native_media_requests":0,
                "counts_as_downloaded":False}
