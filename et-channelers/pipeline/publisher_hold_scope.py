"""Decide which publisher refusal applies to a public RSS enclosure."""
from dataclasses import dataclass
import hashlib
import json
import math
import re


@dataclass(frozen=True)
class AssetRefusalReview:
    """Evidence that one legacy local timer was added for a particular denied resource."""

    ledger_entry_sha256: str
    denied_enclosure_sha256: str
    denied_guid: str
    denied_publisher_account: str
    server_wide_wait_observed: bool


def entry_hash(entry):
    return hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def hold_deadline(entry, provider, endpoint, *, enclosure_sha256, guid, publisher_account, review=None):
    """Return UTC epoch seconds, zero when unrelated, or infinity for a denied item.

    Preserve an unknown historic endpoint timer unless a review is pinned to its
    complete bytes, the old result was a plain 403, and the new publisher account,
    GUID and public enclosure are independently identified. New receipt formats
    can record item-specific denials directly. An explicit broader rest wins.
    """
    if entry.get('provider','').casefold()!=provider.casefold() or entry.get('endpoint')!=endpoint:
        return 0
    until=entry.get('retry_not_before_epoch',0)
    if not isinstance(until,(int,float)) or not math.isfinite(until) or until<0:
        return math.inf
    if entry.get('response_status')==429 or entry.get('retry_after_requires_review') or entry.get('retry_after') not in (None,'',0,'0') or entry.get('scope_kind')=='provider':
        return until or math.inf
    if entry.get('scope_kind')=='asset':
        resource=entry.get('enclosure_sha256')
        if not resource or not re.fullmatch('[a-f0-9]{64}',str(resource)) or not re.fullmatch('[a-f0-9]{64}',str(enclosure_sha256)):
            return until or math.inf
        if resource==enclosure_sha256 or (entry.get('publisher_account')==publisher_account and guid and entry.get('guid')==guid):
            return math.inf if entry.get('response_status') in (401,403) else until
        return 0
    if (review is None or review.server_wide_wait_observed or entry_hash(entry)!=review.ledger_entry_sha256 or
            entry.get('response_status')!=403 or not re.fullmatch('[a-f0-9]{64}',str(enclosure_sha256)) or
            not re.fullmatch('[a-f0-9]{64}',str(review.denied_enclosure_sha256)) or not review.denied_guid or
            not review.denied_publisher_account or not guid or not publisher_account):
        return until
    if enclosure_sha256==review.denied_enclosure_sha256 or guid==review.denied_guid:
        return math.inf
    return until if publisher_account==review.denied_publisher_account else 0
