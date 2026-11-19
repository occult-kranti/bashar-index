"""Local scheduling health, separate from Native identity and receipt coverage.

Callers supply only already validated complete-transfer proofs and bound HTTP
refusal observations. This module never downloads, validates an archive,
rewrites provider history, changes identity, or authorizes a refused asset.
"""
from dataclasses import dataclass, replace
import math
import re

POLICY_VERSION = 'media-transport-health-v1'
ID = re.compile(r'[A-Za-z0-9_-]{11}')
SHA = re.compile(r'[0-9a-f]{64}')


class HealthHold(ValueError):
    pass


def require(value, reason):
    if not value:
        raise HealthHold(reason)


def finite_clock(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


@dataclass(frozen=True)
class Health:
    failure_waves: int = 0
    not_before_epoch: float = 0
    quarantined_ids: frozenset = frozenset()
    normal_pool_allowed: bool = False
    global_hold: str | None = None
    complete_transfer_count: int = 0
    Native_success_or_reset_inferred: bool = False


def backoff_seconds(failure_waves):
    require(type(failure_waves) is int and failure_waves > 0, 'positive_failure_wave_required')
    return min(1800, 60 * 2 ** min(failure_waves - 1, 5))


def advance(state, *, observed_at_epoch, complete_proofs=(), refusals=()):
    """Apply one joined scheduling wave; concurrent successes do not hide403s.

    A complete proof is {video_id, evidence_sha256, evidence_kind}; its producer
    must already have checked the full HTTP extent and the relevant receipt or
    complete Native-transfer proof. Metadata-only handoffs are not successes.
    """
    require(isinstance(state, Health) and state.Native_success_or_reset_inferred is False,
            'separate_transport_health_required')
    require(finite_clock(observed_at_epoch), 'finite_observation_clock_required')
    completed = set()
    for proof in complete_proofs:
        require(isinstance(proof, dict) and ID.fullmatch(str(proof.get('video_id', '')))
                and SHA.fullmatch(str(proof.get('evidence_sha256', '')))
                and proof.get('evidence_kind') in {'validated_complete_qualified_transfer',
                                                  'validated_complete_native_transfer'},
                'validated_full_transfer_reference_required')
        completed.add(proof['video_id'])
    denied = set()
    global_reason = state.global_hold
    deadline = state.not_before_epoch
    for event in refusals:
        require(isinstance(event, dict) and ID.fullmatch(str(event.get('video_id', ''))),
                'exact_refusal_target_required')
        retry_at = event.get('retry_not_before_epoch')
        if retry_at is not None:
            require(finite_clock(retry_at), 'finite_server_deadline_required')
            deadline = max(deadline, retry_at)
        scoped = (event.get('status') == 403 and event.get('action') == 'item_quarantine'
                  and event.get('binding_verified') is True
                  and event.get('retry_after_state') == 'absent'
                  and event.get('retry_after_requires_review') is False and retry_at is None)
        if scoped:
            denied.add(event['video_id'])
        else:
            # 429, explicit/ambiguous Retry-After, login/protection and unknown
            # response scopes never become local item-backoff exceptions.
            global_reason = ('server_rate_or_wait' if event.get('status') == 429
                             or event.get('retry_after_state') != 'absent'
                             else 'global_or_unbound_response')
    require(not completed & denied, 'contradictory_same_wave_target_evidence')
    quarantines = state.quarantined_ids | denied
    if global_reason is not None:
        return replace(state, global_hold=global_reason, normal_pool_allowed=False,
                       quarantined_ids=quarantines, not_before_epoch=deadline)
    if denied:
        count = state.failure_waves + 1
        return replace(state, failure_waves=count, normal_pool_allowed=False,
                       quarantined_ids=quarantines,
                       not_before_epoch=max(deadline, observed_at_epoch + backoff_seconds(count)))
    if completed:
        return replace(state, failure_waves=0, normal_pool_allowed=True,
                       not_before_epoch=observed_at_epoch,
                       complete_transfer_count=state.complete_transfer_count + len(completed))
    return state


def source_limit(state, *, configured_sources, now_epoch):
    require(type(configured_sources) is int and 1 <= configured_sources <= 6,
            'bounded_source_pool_required')
    require(finite_clock(now_epoch), 'finite_dispatch_clock_required')
    if state.global_hold is not None or now_epoch < state.not_before_epoch:
        return 0
    return configured_sources if state.normal_pool_allowed else 1


def may_dispatch(state, video_id, *, active_sources, configured_sources, now_epoch):
    require(ID.fullmatch(str(video_id)) is not None, 'exact_dispatch_target_required')
    require(type(active_sources) is int and active_sources >= 0, 'actual_source_count_required')
    return (video_id not in state.quarantined_ids and active_sources <
            source_limit(state, configured_sources=configured_sources, now_epoch=now_epoch))
