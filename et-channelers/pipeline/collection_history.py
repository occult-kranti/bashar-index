"""Export public attempt evidence without publishing private requests, logs or media."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re

from . import common, dataset_timeline, ingestion_status


FIELDS = ("evidence_id", "observed_utc", "clock_basis", "collection_scope", "creator", "video_id",
          "recording_url", "work_area", "record_type", "outcome", "http_status", "source_body_complete",
          "audio_receipt_at_checkpoint", "recorded_in_closed_batch")
VIDEOS = re.compile(r"[A-Za-z0-9_-]{11}")
SHA = re.compile(r"[0-9a-f]{64}")
RECOVERY_MARKERS = {"attempt-start.json", "execution-attempt.json", "publication-attempt.json",
                    "provenance-pull-attempt.json", "audio-pull-attempt.json", "input-stage-attempt.json",
                    "gpu-attempt.json", "homepage-attempt.json", "feed-attempt.json",
                    "apple-linked-show-attempt.json", "publisher-blog-page-attempt.json",
                    "publisher-podcast-page-attempt.json", "publisher-show-page-attempt.json"}
FINAL_STATES = {
    "local_extract_complete":"local_audio_prepared", "native_route_pending":"additional_audio_evidence_requested",
    "paired_verified_deleted":"remote_pair_verified_local_files_retired", "verified":"verification_recorded",
    "held":"held", "complete":"completed_stage", "completed":"completed_stage", "ok":"completed_stage",
    "success":"completed_stage", "failed":"failed_stage", "error":"failed_stage", "deferred":"deferred",
    "downloaded":"download_recorded", "source_refused":"source_refused", "quarantined":"quality_review",
    "cached": "existing_artifact_reused", "local_complete": "local_stage_complete",
    "metadata_review_complete": "metadata_review_complete", "one_process_admitted": "worker_admitted",
    "one_two_edition_batch_admitted": "worker_admitted", "one_copy_then_readback": "publication_scheduled",
}
ERRORS = {
    "gpu_owner_busy":"local_worker_contention", "wpc_browser_start_failed":"local_browser_start_failed",
    "wpc_provider_attempt_failed":"metadata_provider_failed", "qualified_downloader_failed":"download_failed",
    "source_dispatch_held":"source_start_held", "provider_policy_dispatch_held":"source_start_held",
    "administrative_dispatch_held":"administrative_hold", "target_already_archived":"existing_archive_reused",
    "FileNotFoundError":"missing_local_file", "native_route_pending":"additional_audio_evidence_requested",
}
RECEIPTS = {"youtube_native", "youtube_track_unverified", "publisher_edition"}
DISPOSITIONS = {"verified_audio_receipt", "current_source_refusal", "local_or_administrative_hold",
                "closed_native_ticket_pending", "attempted_requires_reconciliation",
                "ordinary_ready_scoped_local_recovery", "ordinary_ready_unattempted"}


def utc(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def digest(data):
    return sha256(data).hexdigest()


def category(parts):
    trace = "/".join(parts).lower()
    for area, phrases in (
        ("Local speech and language", ("asr", "language-id", "language-review")),
        ("Publisher and podcast", ("publisher", "rumble", "feed-", "podcast", "apple-linked")),
        ("Channel discovery and indexing", ("discovery", "mixed-uploads", ".attempt.json")),
        ("Caption retrieval", ("caption", "subtitle")),
        ("Browser observation", ("browser", "chromium")),
        ("Qualified YouTube edition", ("qualified_youtube", "qualified-")),
        ("Native YouTube audio", ("native", "stock_wpc")),
        ("Archive publication", ("publication-attempt", "provenance-pull", "audio-pull"))):
        if any(p in trace for p in phrases):
            return area
    return "Other retained project evidence"


def event_time(record, fallback):
    for key in ("attempt_at_epoch", "created_at_epoch", "source_started_at_epoch", "started_at_epoch", "at_epoch", "created_at", "started_at"):
        raw = record.get(key)
        if isinstance(raw, str):
            try:
                instant = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if instant.tzinfo is not None:
                    raw = instant.timestamp()
            except (ValueError, OverflowError):
                continue
        if type(raw) in (int, float) and 946684800 <= raw <= 4133980800:
            return utc(raw), "recorded_event_time"
    return (utc(fallback), "file_modified_time") if fallback is not None else ("", "unavailable")


def result_fields(record):
    response = record.get("source_response")
    response = response if isinstance(response, dict) else {}
    status = response.get("status", record.get("http_status"))
    http = status if type(status) is int and 100 <= status <= 599 else ""
    error = str(record.get("error_class") or record.get("exception_class") or "")
    explicit = re.fullmatch(r"(?:source_|selected_HTTP_|http_)([45][0-9]{2})", error, re.I)
    if explicit and not http:
        http = int(explicit[1])
    if http in (401, 403):
        outcome = "provider_refused"
    elif http == 429:
        outcome = "rate_limited"
    elif record.get("parent_cancellation_present") and not record.get("result_present"):
        outcome = "interrupted_by_owner"
    elif error in ERRORS:
        outcome = ERRORS[error]
    else:
        value = record.get("status") or record.get("state")
        outcome = FINAL_STATES.get(str(value), "other_recorded_outcome" if value else "terminal_outcome_unavailable")
    body = response.get("body_complete")
    return outcome, http, ("yes" if body else "no") if type(body) is bool else ""


def marker_paths(root):
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = [d for d in subdirs if d.lower() not in {".git", "__pycache__", "node_modules", "models", "venv", "site-packages"}]
        for name in files:
            simple = name.lower()
            if simple == "attempt.json" or simple.endswith(".attempt.json") or simple in RECOVERY_MARKERS:
                yield Path(directory) / name


def json_file(path, cutoff, *, max_bytes=5_000_000):
    try:
        info = path.stat()
        if info.st_mtime > cutoff or info.st_size > max_bytes:
            return None
        raw = path.read_bytes()
        if len(raw) != info.st_size:
            return None
        doc = json.loads(raw)
        return (doc, digest(raw), info.st_mtime) if isinstance(doc, dict) else None
    except (FileNotFoundError, ValueError, OSError):
        return None


def write_csv(path, records, fields):
    common.atomic_write_text(path, dataset_timeline.csv_bytes(records, fields).decode("utf-8"))


def validate_snapshot(frame, snap):
    primary = {r["video_id"]: r for r in frame["rows"]}
    status = {r["video_id"]: r for r in snap["rows"]}
    if (frame["basis"] != "latest20plus_public_regular"
            or snap.get("kind") != "strict_primary_closed_disposition_snapshot"
            or not primary or len(status) != len(snap["rows"]) or primary.keys() != status.keys()):
        raise ValueError("The disposition snapshot must cover the complete regular selection")
    creators = Counter()
    verified_creators = Counter()
    counts = Counter()
    for vid, selected in primary.items():
        row = status[vid]
        route, disposition = row.get("verified_receipt_route"), row["disposition"]
        if (row["channel_dir"] != selected["channel_dir"]
                or row["expected_channel_id"] != selected["expected_channel_id"]
                or row["tab"] != selected["tab"] or disposition not in DISPOSITIONS
                or route is not None and route not in RECEIPTS
                or bool(route) != (disposition == "verified_audio_receipt")):
            raise ValueError("Invalid creator, recording format or receipt disposition")
        creators[row["channel_dir"]] += 1
        if route:
            verified_creators[row["channel_dir"]] += 1
        counts[disposition] += 1
    complete = sum(verified_creators[key] == count for key, count in creators.items())
    if (counts != snap["counts"] or counts["verified_audio_receipt"] != snap["strict_verified_audio"]
            or complete != snap["complete_creators"]):
        raise ValueError("Declared snapshot counts disagree with its individual receipts")
    return primary, status


def matching_result(path, vid, cutoff):
    name = path.name.lower()
    if name == "attempt.json":
        name = "result.json"
    elif name.endswith(".attempt.json"):
        name = name[:-len(".attempt.json")] + ".result.json"
    else:
        return {}
    payload = json_file(path.with_name(name), cutoff)
    if not vid or not payload or payload[0].get("video_id") != vid:
        return {}
    return payload[0]


def export(root, selection_file, snapshot_file, out):
    root = common.ensure_outside_git(root)
    snapraw = snapshot_file.read_bytes()
    snap = json.loads(snapraw)
    selected_bytes = selection_file.read_bytes()
    frame = ingestion_status.selection_rows(selection_file, content=selected_bytes)
    primary, status = validate_snapshot(frame, snap)
    retained = {r["video_id"]: r for r in json.loads(selected_bytes)["rows"]
                if isinstance(r.get("video_id"), str) and VIDEOS.fullmatch(r["video_id"])}
    cutoff = snap["at_epoch"]
    evidence = {}
    paths = Counter()
    def row_for(sha, vid, area, kind, rec, mtime=None):
        public = vid in primary or vid in retained
        known = primary.get(vid) or retained.get(vid) or {}
        route = (status.get(vid) or {}).get("verified_receipt_route")
        receipt = route if route in RECEIPTS else ""
        when, basis = event_time(rec, mtime)
        outcome, http, body = result_fields(rec)
        return {"evidence_id": sha, "observed_utc": when, "clock_basis": basis,
                "collection_scope": "current_regular" if vid in primary else "retained_index" if vid in retained else "outside_or_unbound",
                "creator": known.get("source_channel_name") or known.get("channel_dir") or "",
                "video_id": vid if public else "", "recording_url": "https://www.youtube.com/watch?v="+vid if public else "",
                "work_area": area, "record_type": kind, "outcome": outcome, "http_status": http,
                "source_body_complete": body, "audio_receipt_at_checkpoint": receipt, "recorded_in_closed_batch":"no"}
    for vid, item in status.items():
        for n, rec in enumerate(item["closed_attempt_history"]):
            pin = rec.get("attempt") or {}
            key = pin.get("sha256")
            if not isinstance(key,str) or not SHA.fullmatch(key):
                # Some old batch results survive without a separate per-item marker.
                key = digest(json.dumps([vid, n, rec], sort_keys=True).encode())
                kind = "closed_summary_without_individual_marker"
            else:
                kind = "attempt_marker"
            area = "Native YouTube audio" if rec["route"] == "native_selected_offer" else "Ordinary public acquisition"
            current = row_for(key, vid, area, kind, rec)
            current["recorded_in_closed_batch"] = "yes"
            evidence[(vid,key)] = current
    for path in marker_paths(root):
        parts = path.relative_to(root).parts
        try:
            if path.stat().st_mtime > cutoff:
                continue
        except OSError:
            continue
        if any("fixture" in part.lower() or part.lower() in ("tests", "testdata", "synthetic") for part in parts):
            paths["fixture_markers_excluded"] += 1
            continue
        loaded = json_file(path, cutoff)
        if loaded is None:
            paths["oversize_or_unreadable_marker"] += 1
            continue
        doc, key, stamp = loaded
        vid = doc.get("video_id")
        if not isinstance(vid, str) or not VIDEOS.fullmatch(vid):
            vid = next((p for p in reversed(parts[:-1]) if p in retained), "")
        paths["retained_marker_paths"] += 1
        ident = vid, key
        if ident in evidence:
            paths["duplicate_or_already_bound_marker_paths"] += 1
            if evidence[ident]["clock_basis"] == "unavailable":
                evidence[ident]["observed_utc"], evidence[ident]["clock_basis"] = event_time(doc, stamp)
            continue
        combined = dict(doc)
        result = matching_result(path, vid, cutoff)
        for key_name in ("status", "state", "exception_class", "error_class", "http_status", "source_response"):
            if key_name in result:
                combined[key_name] = result[key_name]
        evidence[ident] = row_for(key, vid, category(parts), "attempt_marker", combined, stamp)
    out.mkdir(parents=True, exist_ok=True)
    records = sorted(evidence.values(), key=lambda row: (row["observed_utc"], row["video_id"], row["evidence_id"]))
    write_csv(out / "attempt-history.csv", records, FIELDS)
    recordings = []
    groups = Counter(video for video, _ in evidence if video in primary)
    for video, record in primary.items():
        state = status[video]
        recordings.append({
            "creator": record["source_channel_name"],
            "creator_key": record["channel_dir"],
            "video_id": video,
            "url": "https://www.youtube.com/watch?v=" + video,
            "checkpoint_disposition": state["disposition"],
            "verified_audio": state["verified_receipt_route"] or "",
            "distinct_attempt_evidence": groups[video],
        })
    recordings.sort(key=lambda row: (row["creator"].casefold(), row["video_id"]))
    write_csv(out / "recording-status.csv", recordings, tuple(recordings[0]))
    creator_counts = {}
    for row in recordings:
        creator = row["creator_key"]
        counts = creator_counts.setdefault(creator, Counter())
        counts["selected"] += 1
        counts[row["checkpoint_disposition"]] += 1
        if row["verified_audio"]:
            counts[row["verified_audio"]] += 1
    creator_rows = []
    for creator in frame["creators"]:
        counts = creator_counts.get(creator, Counter())
        verified = counts["verified_audio_receipt"]
        creator_rows.append({"creator_key": creator, "selected": counts["selected"], "verified": verified,
                             "outstanding": counts["selected"] - verified,
                             **{k: counts[k] for k in sorted(RECEIPTS)},
                             **{k: counts[k] for k in sorted(DISPOSITIONS - {"verified_audio_receipt"})}})
    creator_rows.sort(key=lambda r: r["creator_key"].casefold())
    write_csv(out / "creator-status.csv", creator_rows, tuple(creator_rows[0]))
    counts = Counter((row["work_area"], row["outcome"]) for row in records)
    by_outcome = [
        {"work_area": area, "outcome": outcome, "evidence_records": count}
        for (area, outcome), count in sorted(counts.items())
    ]
    write_csv(out / "attempt-summary.csv", by_outcome, ("work_area", "outcome", "evidence_records"))
    summary = {
        "as_of_utc": utc(cutoff),
        "selection_sha256": frame["sha256"],
        "snapshot_sha256": digest(snapraw),
        "selected_recordings": len(primary),
        "selected_creators": len(frame["creators"]),
        "verified_audio": snap["strict_verified_audio"],
        "complete_creators": snap["complete_creators"],
        "selection_dispositions": snap["counts"],
        "attempt_evidence_records": len(records),
        "distinct_current_videos_with_attempt_evidence": len(groups),
        "scope_counts": dict(Counter(row["collection_scope"] for row in records)),
        "work_area_counts": dict(Counter(row["work_area"] for row in records)),
        "clock_basis_counts": dict(Counter(row["clock_basis"] for row in records)),
        "inventory": dict(paths),
    }
    common.atomic_write_text(out / "checkpoint.json", json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("root", "selection", "snapshot", "out"):
        parser.add_argument("--" + arg, type=Path, required=True)
    options = parser.parse_args()
    print(json.dumps(export(options.root, options.selection, options.snapshot, options.out), ensure_ascii=True))
