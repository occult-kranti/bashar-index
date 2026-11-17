"""Finite HTTP refusal scope and durable-state transitions for native batch v4.

No I/O, requests, credential changes or automatic retries. The coordinator must
persist returned state before dispatch, under its collector/dispatch locks. A
historical review is an externally hash-pinned owner decision, not authorization
created by this module. It never erases the event or its item quarantine.
"""
from copy import deepcopy
from collections import Counter, deque
from datetime import timezone
from email.utils import parsedate_to_datetime
import math
import re
import time
from urllib.parse import urlsplit

POLICY = "native-http-refusal-v4"
WINDOW_SECONDS = 600
DISTINCT_LIMIT = 3
MAX_EVENTS = 50_000
MAX_RETRY_SECONDS = 366 * 24 * 3600
ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
GLOBAL_CODES = {"bot_check", "protection_failure", "access_challenge", "source_scope_unknown"}


class PolicyError(ValueError):
    pass


def _need(value, reason):
    if not value:
        raise PolicyError(reason)


def _epoch(value):
    _need(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 253402300799,
          "invalid_epoch")
    return float(value)


def _video(value):
    _need(isinstance(value, str) and ID.fullmatch(value), "invalid_video_id")
    return value


def endpoint(url):
    """Classify in memory. No URL or host is returned or stored."""
    if not isinstance(url, str) or not 1 <= len(url) <= 65536:
        return "unknown"
    try:
        value = urlsplit(url)
        if value.scheme != "https" or value.username or value.password or value.port not in (None, 443):
            return "unknown"
        host = (value.hostname or "").lower()
        if host.endswith(".googlevideo.com"):
            return "media"
        if host in {"www.youtube.com", "m.youtube.com", "youtube.com", "youtubei.googleapis.com"}:
            if value.path in {"/", "/watch"} or value.path.startswith("/youtubei/v1/player"):
                return "source_control"
            if value.path == "/api/timedtext":
                return "caption"
            return "provider_auxiliary"
        return "other"
    except (ValueError, TypeError):
        return "unknown"


def parse_retry_after(value, now_epoch):
    """Keep a bounded parsed deadline, never the raw header; never clamp early."""
    now_epoch = _epoch(now_epoch)
    result = {"retry_after_state": "absent", "retry_not_before_epoch": None,
              "retry_after_requires_review": False}
    if value is None:
        return result
    result.update(retry_after_state="invalid", retry_after_requires_review=True)
    if not isinstance(value, str) or len(value) > 128 or "\r" in value or "\n" in value:
        return result
    value = value.strip()
    try:
        if re.fullmatch(r"[0-9]{1,12}", value):
            deadline, kind = now_epoch + int(value), "delay_seconds"
        else:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                return result
            deadline, kind = max(now_epoch, date.astimezone(timezone.utc).timestamp()), "http_date"
        if not math.isfinite(deadline) or deadline > now_epoch + MAX_RETRY_SECONDS:
            return dict(result, retry_after_state="exceeds_bound")
        return {"retry_after_state": kind, "retry_not_before_epoch": deadline,
                "retry_after_requires_review": False}
    except (ValueError, TypeError, OverflowError):
        return result


def retry_after_not_recorded():
    """Historical evidence without captured headers does not prove absence."""
    return {"retry_after_state": "not_recorded", "retry_not_before_epoch": None,
            "retry_after_requires_review": True}


def _format(value):
    result = {}
    if not isinstance(value, dict):
        return result
    for key in ("format_id", "acodec", "ext"):
        item = value.get(key)
        if isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", item):
            result[key] = item
    for key in ("itag", "filesize"):
        item = value.get(key)
        if type(item) is int and 0 < item <= 2**53:
            result[key] = item
    preference = value.get("language_preference")
    if type(preference) in (int, float) and math.isfinite(preference) and -100 <= preference <= 100:
        result["language_preference"] = preference
    return result


def classify_http_failure(status, request_url, final_url, selected_url, phase, video_id,
                          format_identity, *, transport="yt_dlp_python", method="GET",
                          selection_validated=False, retry_after=None, now_epoch=None):
    """Only exact selected request AND final media URL equality permits item scope.

    ``selected_url`` must be supplied only after the worker validates the source
    identity/format. Redirected CDN URLs conservatively retain global scope.
    Browser bootstrap media403 has no target binding; it remains diagnostic.
    Every429 is global, including browser media. Unknown Python403 is global.
    """
    _video(video_id)
    _need(type(status) is int and status in (403, 429), "unsupported_http_failure")
    _need(transport in {"yt_dlp_python", "wpc_browser"}, "invalid_transport")
    now_epoch = _epoch(time.time() if now_epoch is None else now_epoch)
    request_endpoint, final_endpoint = endpoint(request_url), endpoint(final_url)
    selected_endpoint = endpoint(selected_url)
    request_equal = bool(selected_endpoint == "media" and request_url == selected_url)
    final_equal = bool(selected_endpoint == "media" and final_url == selected_url)
    bound = bool(transport == "yt_dlp_python" and method == "GET" and phase == "native_transfer"
                 and selection_validated is True and request_equal and final_equal
                 and request_endpoint == final_endpoint == "media")
    action = "global_stop"
    if status == 403:
        if bound:
            action = "item_quarantine"
        elif (transport == "wpc_browser" and request_endpoint == final_endpoint == "media"):
            action = "diagnostic"
    event = {"action": action, "code": "source_" + str(status), "status": status,
             "endpoint": final_endpoint, "request_endpoint": request_endpoint,
             "response_endpoint": final_endpoint, "video_id": video_id, "transport": transport,
             "phase": phase if phase in {"bootstrap", "native_transfer", "local_verification"} else "unknown",
             "selection_validated": selection_validated is True, "selected_request_equal": request_equal,
             "final_response_equal": final_equal, "binding_verified": bound,
             "format_identity": _format(format_identity), **parse_retry_after(retry_after, now_epoch)}
    return event


def global_failure_event(code, video_id, *, transport="yt_dlp_python", phase="unknown"):
    _need(code in GLOBAL_CODES, "unsupported_global_failure")
    _video(video_id)
    _need(transport in {"yt_dlp_python", "wpc_browser"}, "invalid_transport")
    return {"action": "global_stop", "code": code, "status": None, "endpoint": "unknown",
            "request_endpoint": "unknown", "response_endpoint": "unknown", "video_id": video_id,
            "transport": transport, "phase": phase if phase in {"bootstrap", "native_transfer", "local_verification"} else "unknown",
            "selection_validated": False, "selected_request_equal": False, "final_response_equal": False,
            "binding_verified": False, "format_identity": {}, **parse_retry_after(None, 0)}


EVENT_KEYS = frozenset(global_failure_event("source_scope_unknown", "aaaaaaaaaaa"))


def _event(event):
    _need(isinstance(event, dict) and set(event) == EVENT_KEYS, "unsafe_event_fields")
    _video(event["video_id"])
    _need(event["action"] in {"item_quarantine", "global_stop", "diagnostic"}, "invalid_action")
    _need(event["transport"] in {"yt_dlp_python", "wpc_browser"}, "invalid_transport")
    _need(event["phase"] in {"bootstrap", "native_transfer", "local_verification", "unknown"}, "invalid_phase")
    for key in ("endpoint", "request_endpoint", "response_endpoint"):
        _need(event[key] in {"media", "source_control", "caption", "provider_auxiliary", "other", "unknown"}, "invalid_endpoint")
    for key in ("selection_validated", "selected_request_equal", "final_response_equal", "binding_verified", "retry_after_requires_review"):
        _need(type(event[key]) is bool, "invalid_boolean")
    _need(event["format_identity"] == _format(event["format_identity"]), "unsafe_format_identity")
    if event["status"] is None:
        _need(event["code"] in GLOBAL_CODES and event["action"] == "global_stop", "invalid_global_event")
    else:
        _need(type(event["status"]) is int and event["status"] in (403, 429) and
              event["code"] == "source_" + str(event["status"]), "invalid_http_event")
        if event["status"] == 429:
            _need(event["action"] == "global_stop", "rate_limit_must_be_global")
    if event["action"] == "item_quarantine":
        _need(event["status"] == 403 and event["transport"] == "yt_dlp_python" and event["phase"] == "native_transfer"
              and all(event[k] for k in ("selection_validated", "selected_request_equal", "final_response_equal", "binding_verified"))
              and event["request_endpoint"] == event["response_endpoint"] == "media", "unproven_item_scope")
    if event["action"] == "diagnostic":
        _need(event["status"] == 403 and event["transport"] == "wpc_browser" and
              event["request_endpoint"] == event["response_endpoint"] == "media" and not event["binding_verified"],
              "invalid_diagnostic_scope")
    _need(event["retry_after_state"] in {"absent", "not_recorded", "invalid", "exceeds_bound", "delay_seconds", "http_date"}, "invalid_retry_state")
    if event["retry_after_state"] == "not_recorded":
        _need(event["retry_not_before_epoch"] is None and event["retry_after_requires_review"] is True,
              "unrecorded_retry_header_requires_review")
    if event["retry_not_before_epoch"] is not None:
        _epoch(event["retry_not_before_epoch"])
    return event


def empty_state():
    return {"schema_version": 1, "policy": POLICY, "window_seconds": WINDOW_SECONDS,
            "distinct_limit": DISTINCT_LIMIT, "events": {}, "circuit_break": None}


def _historical_event(event):
    _need(event["status"] == 403 and event["action"] == "global_stop" and not event["binding_verified"] and
          event["transport"] == "yt_dlp_python" and event["request_endpoint"] == "media" and
          event["response_endpoint"] == "unknown" and event["phase"] == "native_transfer" and event["selection_validated"],
          "historical_scope_must_stay_uncertain_global")


def _state(state):
    _need(isinstance(state, dict) and set(state) == set(empty_state()), "invalid_state_fields")
    _need(state["schema_version"] == 1 and state["policy"] == POLICY and
          state["window_seconds"] == WINDOW_SECONDS and state["distinct_limit"] == DISTINCT_LIMIT, "policy_mismatch")
    _need(isinstance(state["events"], dict) and len(state["events"]) <= MAX_EVENTS, "event_ledger_limit")
    for key, row in state["events"].items():
        _need(isinstance(key, str) and SHA.fullmatch(key), "invalid_event_id")
        _need(isinstance(row, dict) and set(row) == {"event", "at_epoch", "historical"} and type(row["historical"]) is bool,
              "invalid_event_record")
        _epoch(row["at_epoch"])
        _event(row["event"])
        if row["historical"]:
            _historical_event(row["event"])
    circuit = state["circuit_break"]
    if circuit is not None:
        _need(isinstance(circuit, dict) and set(circuit) == {"at_epoch", "event_ids", "reason"} and
              circuit["reason"] == "three_distinct_403_in_600s", "invalid_circuit")
        _epoch(circuit["at_epoch"])
        _need(isinstance(circuit["event_ids"], list) and all(k in state["events"] for k in circuit["event_ids"]), "invalid_circuit_events")
    return state


def _countable(row):
    event = row["event"]
    return event["action"] == "item_quarantine" or bool(row["historical"] and event["status"] == 403)


def _recent(state, now_epoch):
    return {key: row for key, row in state["events"].items()
            if _countable(row) and 0 <= now_epoch - row["at_epoch"] < WINDOW_SECONDS}


def _find_circuit(state):
    """Out-of-order delivery cannot hide a historical threshold crossing."""
    ordered = sorted((row["at_epoch"], key, row["event"]["video_id"])
                     for key, row in state["events"].items() if _countable(row))
    window, counts = deque(), Counter()
    for at_epoch, key, ident in ordered:
        while window and at_epoch - window[0][0] >= WINDOW_SECONDS:
            _, _, previous = window.popleft()
            counts[previous] -= 1
            if not counts[previous]:
                del counts[previous]
        window.append((at_epoch, key, ident)); counts[ident] += 1
        if len(counts) >= DISTINCT_LIMIT:
            return {"at_epoch": at_epoch, "event_ids": sorted(row[1] for row in window),
                    "reason": "three_distinct_403_in_600s"}
    return None


def apply_event(state, event, event_id, at_epoch, *, historical=False):
    _state(state); _event(event); at_epoch = _epoch(at_epoch)
    _need(isinstance(event_id, str) and SHA.fullmatch(event_id), "invalid_event_id")
    _need(type(historical) is bool, "invalid_historical_flag")
    if historical:
        _historical_event(event)
    existing = state["events"].get(event_id)
    if existing is not None:
        _need(existing["event"] == event and existing["historical"] == historical, "event_id_collision")
        return deepcopy(state)  # repeated polling cannot refresh the original failure time
    _need(len(state["events"]) < MAX_EVENTS, "event_ledger_limit")
    result = deepcopy(state)
    result["events"][event_id] = {"event": deepcopy(event), "at_epoch": at_epoch, "historical": historical}
    if result["circuit_break"] is None:
        result["circuit_break"] = _find_circuit(result)
    return result


def seed_historical_event(state, event, event_id, at_epoch):
    """Only an explicit owner admission may persist a seed built by this helper."""
    return apply_event(state, event, event_id, at_epoch, historical=True)


def status(state, now_epoch, *, historical_review=None, candidate_video_id=None):
    _state(state); now_epoch = _epoch(now_epoch)
    if candidate_video_id is not None:
        _video(candidate_video_id)
    rows = state["events"]
    quarantined = {r["event"]["video_id"] for r in rows.values()
                   if r["event"]["status"] == 403 and r["event"]["action"] != "diagnostic"}
    global_ids = {key for key, row in rows.items() if row["event"]["action"] == "global_stop"}
    covered = set()
    if historical_review is not None:
        _need(isinstance(historical_review, dict) and set(historical_review) ==
              {"review_sha256", "covered_event_ids", "allowed_video_ids"}, "invalid_historical_review")
        _need(isinstance(historical_review["review_sha256"], str) and SHA.fullmatch(historical_review["review_sha256"]), "unbound_owner_review")
        ids, allowed = historical_review["covered_event_ids"], historical_review["allowed_video_ids"]
        _need(isinstance(ids, list) and all(isinstance(k, str) for k in ids) and
              len(ids) == len(set(ids)) and all(k in rows and rows[k]["historical"] for k in ids),
              "review_cannot_cover_new_events")
        _need(isinstance(allowed, list) and len(allowed) <= 20000 and all(isinstance(v, str) and ID.fullmatch(v) for v in allowed),
              "invalid_review_targets")
        historical_held = {r["event"]["video_id"] for r in rows.values() if r["historical"] and r["event"]["status"] == 403}
        _need(not historical_held.intersection(allowed), "review_cannot_retry_historical_items")
        if candidate_video_id in allowed:
            covered = set(ids)
    recent = _recent(state, now_epoch)
    clock_regressed = any(row["at_epoch"] > now_epoch for row in rows.values())
    remaining_global = global_ids - covered
    circuit = state["circuit_break"] or _find_circuit(state)
    stopped = bool(remaining_global or circuit or clock_regressed)
    item_held = candidate_video_id in quarantined
    return {"global_stop": stopped, "dispatch_allowed": bool(candidate_video_id and not stopped and not item_held),
            "item_quarantined": item_held, "quarantined_video_ids": sorted(quarantined),
            "distinct_403_count": len({r["event"]["video_id"] for r in recent.values()}),
            "bound_asset_403_count": len({r["event"]["video_id"] for r in recent.values() if not r["historical"]}),
            "historical_403_count": len({r["event"]["video_id"] for r in recent.values() if r["historical"]}),
            "global_event_ids": sorted(remaining_global), "retained_historical_global_event_ids": sorted(global_ids & covered),
            "circuit_break": deepcopy(circuit), "clock_regressed": clock_regressed,
            "owner_scope_exception_applied": bool(covered)}
