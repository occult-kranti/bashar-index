#!/usr/bin/env python3
"""Offline conditional collection estimates from metadata receipts, never media/text.

No collector, source request, Drive call or model is started. Output is an
allowlisted aggregate estimate, not a completion promise or scheduler input.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drive_ingest import (CAPTION_POLICY, caption_receipt_complete, receipt_complete,
                          terminal_unavailable)
from ingestion_status import bound_json, proof, read_object, record_row, source_deadline, stamp
from common import atomic_write_text

MIB = 1024 ** 2
DEFAULT_REMOTE = "etdrive:04 Audio"
TABS = {"videos", "shorts", "streams"}


def positive(value):
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (ValueError, TypeError):
        return None
    return result if math.isfinite(result) and result > 0 else None


def epoch(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.timestamp() if parsed.tzinfo else None
    except (ValueError, OverflowError):
        return None


def precise_stamp(value):
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def quantile(values, q):
    values = sorted(values)
    if not values:
        return None
    pos = (len(values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)


def distribution(values):
    return {"n": len(values), "p10": quantile(values, .1),
            "median": quantile(values, .5), "p90": quantile(values, .9)}


def read_snapshot(path, optional=False):
    if optional and not path.exists():
        return b"", {"sha256": None, "bytes": 0, "missing": True}
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError("Input changed during the read; retry at a stable checkpoint")
    return data, {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "missing": False}


def rows_from_bytes(data):
    rows, seen = [], set()
    for row in csv.DictReader(io.StringIO(data.decode("utf-8-sig"))):
        if record_row(row) is None or row["video_id"] in seen:
            raise ValueError("Queue contains an invalid or duplicate identity")
        if row.get("tab", "") not in TABS | {""}:
            raise ValueError("Queue contains an unknown source tab")
        seen.add(row["video_id"])
        rows.append(row)
    return rows


def records_from_bytes(data):
    records, malformed = [], 0
    for line in data.decode("utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            malformed += 1
            continue
        if isinstance(record, dict) and record_row(record):
            records.append(record)
        else:
            malformed += 1
    return records, malformed


def latest(records):
    return {record["video_id"]: record for record in records}


def verified_records(records, remote):
    return {key: rec for key, rec in latest(records).items()
            if positive(rec.get("bytes")) and proof(receipt_complete, rec, record_row(rec), remote)}


def timing_evidence(records, verified):
    """Receipt spans contain scheduling/metadata/Drive waits; never call them bandwidth."""
    attempts, lags = [], []
    grouped = collections.defaultdict(list)
    for rec in records:
        grouped[rec["video_id"]].append(rec)
    for key, final in verified.items():
        same = [r for r in grouped[key] if r.get("sha256") == final.get("sha256") and r.get("bytes") == final.get("bytes")]
        downloads = [r for r in same if r.get("status") == "download_complete"]
        if downloads:
            rec = downloads[-1]
            start, end = epoch(rec.get("updated_at")), epoch(rec.get("downloaded_at"))
            if start is not None and end is not None and end > start:
                attempts.append(end - start)
        downloaded = epoch(final.get("downloaded_at"))
        checks = [epoch(r.get("verified_at")) for r in same]
        checks = [t for t in checks if t is not None and downloaded is not None and t >= downloaded]
        if checks:
            lags.append(min(checks) - downloaded)
    return {"attempt_elapsed_seconds": distribution(attempts),
            "download_to_first_verification_seconds": distribution(lags),
            "pure_upload_seconds_measured": False,
            "receipt_spans_used_as_bandwidth": False,
            "interpretation": "Attempt time includes metadata/pacing; verification lag includes queueing, uploads and cooldowns. Neither is isolated transfer time."}


def progress_evidence(log_data, verified):
    """Accept only JSON progress numeric fields; never echo raw log content."""
    best = {}
    for data in log_data:
        # PowerShell redirects may emit UTF-16; logs otherwise use UTF-8.
        encoding = "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        for line in data.decode(encoding, errors="replace").splitlines():
            start, end = line.find("{"), line.rfind("}")
            if start < 0:
                continue
            try:
                row = json.loads(line[start:end + 1])
            except ValueError:
                continue
            if not isinstance(row, dict) or row.get("status") != "downloading":
                continue
            rec = verified.get(row.get("video_id"))
            size, elapsed, total = positive(row.get("bytes")), positive(row.get("elapsed_s")), positive(row.get("total_bytes"))
            if not rec or not size or not elapsed or elapsed < 5 or total != rec["bytes"] or size > total:
                continue
            key = row["video_id"]
            # One largest observed prefix per verified object; repeated copied logs do not inflate n.
            if key not in best or size > best[key][0]:
                best[key] = (size, elapsed, total)
    rates = [size / elapsed for size, elapsed, _ in best.values()]
    return {"verified_objects_with_progress": len(best), "per_worker_bytes_per_second": distribution(rates),
            "sampled_prefix_bytes": sum(v[0] for v in best.values()),
            "sampled_active_worker_seconds": sum(v[1] for v in best.values()),
            "median_observed_fraction": quantile([v[0] / v[2] for v in best.values()], .5),
            "interpretation": "Active download-prefix timings, excluding pre-request pacing and later upload/cooldown waits. They are not full-file completion times or measured aggregate concurrency; protocols/configurations may differ."}


def duration_projection(rows, verified, completed, reference_rows=None):
    groups, tabs, global_values = collections.defaultdict(list), collections.defaultdict(list), []
    effective = {}
    for row in reference_rows if reference_rows is not None else rows:
        duration = positive(verified.get(row["video_id"], {}).get("duration_s")) or positive(row.get("duration_s"))
        if duration:
            effective[row["video_id"]] = duration
            groups[(row["channel_dir"], row.get("tab") or "unknown")].append(duration)
            tabs[row.get("tab") or "unknown"].append(duration)
            global_values.append(duration)
    remaining = [r for r in rows if r["video_id"] not in completed]
    known = sum(effective.get(r["video_id"], 0) for r in remaining)
    totals = [known] * 3
    missing, strata, long_count = 0, collections.Counter(), 0
    missing_tabs = collections.Counter()
    imputed = {}
    for row in remaining:
        duration = effective.get(row["video_id"])
        if duration:
            long_count += duration > 8 * 3600
            continue
        missing += 1
        tab = row.get("tab") or "unknown"
        missing_tabs[tab] += 1
        pool = groups[(row["channel_dir"], tab)]
        basis = "channel_tab"
        if len(pool) < 5:
            pool, basis = tabs[tab], "tab"
        if len(pool) < 5 and tab == "shorts":
            # No observed Shorts durations: do not silently borrow long-video lengths.
            # These are declared illustrative scenarios, never a duration cap.
            strata["assumed_shorts_no_observations"] += 1
            for i, value in enumerate((15, 60, 180)):
                totals[i] += value
            continue
        if len(pool) < 5:
            pool, basis = global_values, "pooled"
        if not pool:
            strata["unresolved"] += 1
            continue
        strata[basis] += 1
        key = (basis, row["channel_dir"] if basis == "channel_tab" else "", tab if basis != "pooled" else "")
        if key not in imputed:
            imputed[key] = [quantile(pool, q) for q in (.25, .5, .9)]
        for i, value in enumerate(imputed[key]):
            totals[i] += value
    return {"remaining_items": len(remaining), "known_duration_items": len(remaining) - missing,
            "unknown_duration_items": missing, "known_duration_seconds": known,
            "unknown_duration_by_tab": dict(missing_tabs),
            "duration_seconds_scenarios": None if strata["unresolved"] else totals,
            "imputation_counts": dict(strata), "known_items_over_8_hours": long_count,
            "interpretation": "Unknown durations use channel/tab n>=5, else tab n>=5. With insufficient Shorts observations use explicit 15/60/180-second assumptions, not long-video pooling or a duration cap. Other sparse/unknown tabs fall back to pooled p25/median/p90. These are scenarios, not bounds/confidence intervals; no duration exclusion."}


def validate_stages(rows, stages):
    full = {r["video_id"] for r in rows}
    groups = {name: {r["video_id"] for r in group} for name, group in stages.items()}
    if any(not ids <= full for ids in groups.values()):
        raise ValueError("Stage queue is not part of the full snapshot")
    twenty, fifty = groups.get("newest20"), groups.get("newest50_inclusive")
    if twenty is not None and fifty is not None and not twenty <= fifty:
        raise ValueError("Newest tiers are inconsistent")
    if fifty is not None and "remaining_archive" in groups and groups["remaining_archive"] != full - fifty:
        raise ValueError("Final archive partition is inconsistent")


def conditional_hours(items, byte_count, download_bps, upload_bps, workers, metadata_interval):
    """Overlapped stages: slower sustained service sets the optimistic active floor."""
    if (not all(positive(v) for v in (download_bps, upload_bps, workers)) or
            not math.isfinite(metadata_interval) or metadata_interval < 0 or
            not math.isfinite(byte_count) or byte_count < 0 or items < 0):
        raise ValueError("Transfer rates/workers must be positive and pacing nonnegative")
    metadata = max(0, items - 1) * metadata_interval
    download = byte_count / (download_bps * workers)
    upload = byte_count / upload_bps  # aggregate link goodput: do not multiply by transfer count
    return {"metadata_start_floor_hours": metadata / 3600,
            "download_service_hours": download / 3600, "upload_service_hours": upload / 3600,
            "overlapped_active_floor_hours": max(metadata, download, upload) / 3600}


def estimate(rows, records, caption_records=(), *, stage_rows=None, logs=(), remote=DEFAULT_REMOTE,
             now=None, metadata_interval=10.0, caption_interval=15.0, workers=4,
             upload_mib=(1.0, 4.0, 10.0), assumed_download_mib=(.25, 1.0, 2.0),
             availability=(1.0, .5, .25), drive_until=0.0, private_cap=17_000_000_000):
    if (len(upload_mib) != 3 or len(assumed_download_mib) != 3 or
            not all(positive(v) for v in (*upload_mib, *assumed_download_mib)) or
            not all(positive(a) and a <= 1 for a in availability)):
        raise ValueError("Scenario rates and availability must be finite and positive")
    now = time.time() if now is None else now
    verified = verified_records(records, remote)
    audio_latest, caps = latest(records), latest(caption_records)
    unavailable = {key for key, rec in audio_latest.items() if terminal_unavailable(rec)}
    completed = set(verified) | unavailable
    durations = {r["video_id"]: positive(r.get("duration_s")) for r in rows}
    samples = [(positive(r.get("bytes")), positive(r.get("duration_s")) or durations.get(key))
               for key, r in verified.items()]
    samples = [(b, d) for b, d in samples if b and d]
    encoding = [b / d for b, d in samples]
    encoding_range = [quantile(encoding, q) for q in (.1, .5, .9)]
    progress = progress_evidence(logs, verified)
    measured = progress["per_worker_bytes_per_second"]
    download_range = [measured[k] for k in ("p10", "median", "p90")] if measured["n"] >= 3 else [v * MIB for v in assumed_download_mib]
    source_until = source_deadline(audio_latest.values())
    captions_until = source_deadline(caps.values())
    wait_hours = max(0, max(source_until, drive_until) - now) / 3600
    cap_wait_hours = max(0, max(captions_until, drive_until) - now) / 3600
    all_ids = {r["video_id"] for r in rows}
    caption_done = {key for key, rec in caps.items() if rec.get("policy") == CAPTION_POLICY and
                    proof(caption_receipt_complete, rec, record_row(rec), remote)}
    pending_caps = len(all_ids - unavailable - caption_done)
    result = {"schema_version": 1, "generated_at": dt.datetime.fromtimestamp(now, dt.timezone.utc).isoformat(),
              "status": "blocked" if wait_hours else "conditional_only", "guaranteed_completion_date": None,
              "no_finite_guaranteed_completion": True, "asr_included": False,
              "scope": "metadata-only conditional native audio and English-caption archive estimate",
              "configuration": {"assumed_not_live_runtime": True, "workers": workers, "upload_transfers": 4, "upload_batch_items": 8,
                                "ready_items": 16, "metadata_interval_seconds": metadata_interval,
                                "caption_interval_seconds": caption_interval, "private_ceiling_bytes": private_cap},
              "inventory": {"queue_items": len(rows), "queue_verified_pairs": len(all_ids & verified.keys()),
                            "terminal_unavailable_items": len(all_ids & unavailable), "verified_pairs_for_calibration": len(verified)},
              "encoding_evidence": {"sampled_pairs": len(samples), "sampled_audio_bytes": sum(b for b, _ in samples),
                                    "sampled_audio_seconds": sum(d for _, d in samples),
                                    "bytes_per_audio_second": distribution(encoding),
                                    "duration_weighted_bytes_per_audio_second": sum(b for b, _ in samples) / sum(d for _, d in samples) if samples else None,
                                    "representative_sample_claimed": False},
              "timing_evidence": timing_evidence(records, verified), "download_progress_evidence": progress,
              "assumptions": {"download_rate_basis": "observed active-prefix per-worker p10/median/p90" if measured["n"] >= 3 else "explicit assumed per-worker goodput; insufficient matched progress",
                              "download_bytes_per_second": download_range,
                              "aggregate_upload_mib_per_second": list(upload_mib), "upload_rate_measured": False,
                              "availability_fractions": list(availability), "availability_is_assumed": True,
                              "unknown_shorts_seconds_if_no_observed_stratum": [15, 60, 180],
                              "estimated_bytes_exclude_metadata_caption_and_catalog_overhead": True,
                              "model": "max(metadata request-start floor, audio bytes / aggregate download goodput, audio bytes / aggregate upload goodput); stages overlap. Add current wait once, then divide active time by assumed future availability."},
              "cooldowns": {"audio_current_wait_hours": wait_hours, "caption_current_wait_hours": cap_wait_hours,
                            "audio_retry_after": source_until if source_until > now else None,
                            "caption_retry_after": captions_until if captions_until > now else None,
                            "caption_does_not_block_audio": True}, "stages": {}}
    stages = dict(stage_rows or {})
    validate_stages(rows, stages)
    if "newest20" in stages and "newest50_inclusive" in stages:
        first = {r["video_id"] for r in stages["newest20"]}
        stages["newest50_incremental"] = [r for r in stages["newest50_inclusive"] if r["video_id"] not in first]
    stages["all_indexed"] = rows
    for name, group in stages.items():
        projection = duration_projection(group, verified, completed, reference_rows=rows)
        projection["metadata_start_floor_hours"] = max(0, projection["remaining_items"] - 1) * metadata_interval / 3600
        projection["known_items_estimated_over_private_cap"] = sum(
            (positive(row.get("duration_s")) or 0) * (encoding_range[2] or 0) > private_cap
            for row in group if row["video_id"] not in completed)
        scenarios = []
        if projection["duration_seconds_scenarios"] is not None and samples:
            # optimistic/base/cautious mix low/middle/high quantity with fast/middle/slow service.
            for i, label in enumerate(("optimistic", "central", "cautious")):
                quantity = projection["duration_seconds_scenarios"][i] * encoding_range[i]
                services = conditional_hours(projection["remaining_items"], quantity, download_range[2-i],
                                             upload_mib[2-i] * MIB, workers, metadata_interval)
                active = services["overlapped_active_floor_hours"]
                scenarios.append({"name": label, "audio_bytes": quantity, **services,
                                  "calendar_hours_by_availability": [{"fraction": a, "hours": wait_hours + active / a} for a in availability]})
        projection["scenarios"] = scenarios
        result["stages"][name] = projection
    phase_names = ("newest20", "newest50_incremental", "remaining_archive")
    if all(name in result["stages"] and result["stages"][name]["scenarios"] for name in phase_names):
        result["staged_archive_active_floor_hours"] = {
            label: sum(result["stages"][name]["scenarios"][i]["overlapped_active_floor_hours"] for name in phase_names)
            for i, label in enumerate(("optimistic", "central", "cautious"))}
    result["captions"] = {"pending_or_unknown_inventory_videos": pending_caps,
                          "tracks_per_pending_video_assumptions": [0, 1, 2],
                          "request_start_floor_hours": [max(0, pending_caps * n - 1) * caption_interval / 3600 for n in (0, 1, 2)],
                          "meaning": "0/1/2 tracks are illustrative scenarios, not an upper bound; regional/published variants can exceed two. Unknown caption availability is not absence. Backfill may need additional metadata requests.",
                          "caption_wait_hours": cap_wait_hours}
    result["limitations"] = ["Successful early items and partial progress are a selected sample; do not extrapolate a confidence interval.",
                             "Bandwidth scenarios omit API/verification latency, retries, captions/catalog overhead and pipeline fill/drain; active times are conditional floors.",
                             "Unknown durations, changed/deleted sources, ongoing streams and long items exceeding available spool capacity can prevent full completion.",
                             "Current and future refusals may recur indefinitely; no finite guaranteed finish date follows from this model.",
                             "Upload rates are aggregate assumptions; transfer counts alone do not establish bandwidth."]
    return result


def completed_service(root, live, remote=DEFAULT_REMOTE):
    """Whole admitted-run service from terminal saved proofs, including waits.

    Only small JSON evidence/receipt files are read. No media is hashed, probed,
    transferred, or fetched. Outcome IDs are joined privately and never exported.
    """
    state = read_object(live / 'series-state.json')
    invoked = read_object(live / 'source-invocation.json')
    exited = read_object(live / 'source-process-exit.json')
    released = read_object(live / 'native-allocation-released.json')
    start, end = epoch(invoked.get('at')), epoch(exited.get('at'))
    if not (state.get('status') in {'complete', 'finished_with_holds'} and
            state.get('proposal_sha256') == invoked.get('series_proposal_sha256') and
            state.get('authorization_sha256') == invoked.get('root_authorization_sha256') and
            isinstance(state.get('proposal_sha256'), str) and len(state['proposal_sha256']) == 64 and
            isinstance(state.get('authorization_sha256'), str) and len(state['authorization_sha256']) == 64 and
            exited.get('exit_code') == 0 and released.get('lease_id') and
            start is not None and end is not None and end > start):
        raise ValueError('No complete admitted-run timing proof')
    frames = state.get('frames')
    if not isinstance(frames, dict) or not frames:
        raise ValueError('Missing terminal frame outcomes')
    outcomes = {}
    for frame in frames.values():
        if frame.get('phase') != 'drained' or not isinstance(frame.get('outcomes'), dict):
            raise ValueError('Unfinished frame cannot calibrate an ETA')
        for key, value in frame['outcomes'].items():
            if key in outcomes:
                raise ValueError('Repeated frame identity')
            outcomes[key] = value
    records, _ = records_from_bytes(read_snapshot(root / 'sync/drive_ingest_manifest.jsonl')[0])
    verified = verified_records(records, remote)
    canonical = {key: verified[key] for key, outcome in outcomes.items()
                 if outcome.get('status') == 'canonical_verified' and key in verified}
    expected = sum(outcome.get('status') == 'canonical_verified' for outcome in outcomes.values())
    if not outcomes or len(canonical) != expected:
        raise ValueError('Terminal counts do not match complete receipt pairs')
    seconds = end - start
    return {'started_at': precise_stamp(start), 'ended_at': precise_stamp(end), 'elapsed_seconds': seconds,
            'first_pass_decisions': len(outcomes), 'verified_native_pairs': len(canonical),
            'held_or_uncertain_decisions': len(outcomes) - len(canonical),
            'verified_audio_bytes': sum(rec['bytes'] for rec in canonical.values()),
            'decisions_per_hour': len(outcomes) * 3600 / seconds,
            'verified_pairs_per_hour': len(canonical) * 3600 / seconds,
            'immediate_success_fraction': len(canonical) / len(outcomes),
            'includes_startup_source_metadata_upload_and_backpressure': True,
            'isolated_bandwidth_measurement': False}


def completed_recovery_service(root, live, remote=DEFAULT_REMOTE):
    active, invoked, terminal, exited = (read_object(live / name) for name in
        ('activation.json', 'invocation.json', 'terminal.json', 'source-process-exit.json'))
    start, end = positive(invoked.get('started_at_epoch')), epoch(exited.get('at'))
    summary = terminal.get('summary', {})
    required = ('parent_process_exited', 'child_audits_complete', 'owned_jobs_closed',
                'matching_reservation_released', 'matching_lease_released')
    if not (terminal.get('status') == 'terminal' and all(terminal.get(key) is True for key in required) and
            all(terminal.get(key + '_sha256') == invoked.get(key + '_sha256') == active.get(key, {}).get('sha256')
                and bound_json(root, active.get(key)) for key in ('plan', 'settings', 'root_grant')) and
            terminal.get('lease_id') == invoked.get('lease_id') == active.get('lease_id') and
            all(exited.get(key) == invoked.get(key) for key in ('pid', 'process_creation_filetime')) and
            exited.get('exit_code') in (0, 3) and start and end and end > start and
            all(type(summary.get(key)) is int and summary[key] >= 0 for key in ('verified', 'held', 'pending', 'skipped')) and
            summary['pending'] == 0 and sum(summary[key] for key in ('verified', 'held', 'pending', 'skipped')) == invoked.get('source_count')):
        raise ValueError('Missing bound terminal recovery evidence')
    records, _ = records_from_bytes(read_snapshot(root / 'sync/drive_ingest_manifest.jsonl')[0])
    verified = verified_records(records, remote)
    pairs = [rec for rec in verified.values() if rec.get('native_batch_plan_sha256') == invoked.get('plan_sha256')]
    if len(pairs) != summary['verified']:
        raise ValueError('Recovery terminal summary does not match canonical pairs')
    count, seconds = invoked['source_count'], end - start
    return {'started_at': precise_stamp(start), 'ended_at': precise_stamp(end), 'elapsed_seconds': seconds,
            'first_pass_decisions': count, 'verified_native_pairs': len(pairs),
            'held_or_uncertain_decisions': summary['held'], 'verified_audio_bytes': sum(rec['bytes'] for rec in pairs),
            'decisions_per_hour': count * 3600 / seconds, 'immediate_success_fraction': len(pairs) / count,
            'includes_startup_source_metadata_upload_and_backpressure': True, 'isolated_bandwidth_measurement': False}


def operational_estimate(root, live, next_selection, campaign_selection, status, *, now=None, remote=DEFAULT_REMOTE, recovery_live=None, service_direct=False):
    """Current, conditional first-pass scenarios; all-text completion stays unknown."""
    now = time.time() if now is None else now
    service = (completed_recovery_service if service_direct else completed_service)(root, live, remote)
    next_count = read_object(next_selection).get('counts', {}).get('selected')
    campaign = read_object(campaign_selection).get('counts', {})
    untouched, frames = campaign.get('selected'), campaign.get('frames')
    if (status.get('scope') != 'local_youtube_collection' or
            any(type(n) is not int or n <= 0 for n in (next_count, untouched, frames))):
        raise ValueError('Missing current aggregate queue evidence')
    rate = service['decisions_per_hour']
    def scenario(items, service_rate=rate):
        active = items / service_rate
        return {'items': items, 'same_service_active_hours': active,
                'planning_active_hours': [active, active * 2],
                'calendar_hours_at_half_availability': [active * 2, active * 4],
                'planning_multiplier_assumed': [1, 2], 'confidence_interval': False}
    counts = status.get('counts', {})
    coverage_keys = ('verified_pairs', 'asr_verified_videos', 'source_audio_available_target_videos',
                     'qualified_youtube_audio_edition_target_videos',
                     'source_audio_with_text_target_videos', 'text_available_videos',
                     'text_inventory_complete_videos', 'text_missing_videos', 'caption_verified_videos',
                     'caption_verified_tracks', 'caption_text_available_videos', 'caption_inventory_review_videos')
    coverage = {key: counts[key] for key in coverage_keys if type(counts.get(key)) is int}
    twenty = next((stage.get('total') for stage in status.get('stages', []) if stage.get('key') == 'newest20'), None)
    lane = status.get('native_lane', {})
    original_selection = untouched
    bulk = lane.get('kind') == 'native_v5_bulk'
    if bulk:
        remaining_scope, scope_frames = lane.get('source_count'), lane.get('planned_frames')
        if not (type(remaining_scope) is int and 0 < remaining_scope <= untouched and
                type(scope_frames) is int and scope_frames > 0):
            raise ValueError('Invalid finite-cohort scope')
        untouched, frames = remaining_scope, scope_frames
    next_state = 'running' if lane.get('kind') == 'native_v4_direct_batch' and lane.get('state') == 'running' else 'prepared_not_confirmed_running'
    recovery_paths = list(recovery_live or [])
    recovery = None
    if recovery_paths:
        plans = [read_object(path / 'invocation.json').get('plan_sha256') for path in recovery_paths]
        if len(set(plans)) != len(plans):
            raise ValueError('A recovery frame was supplied more than once')
        services = [completed_recovery_service(root, path, remote) for path in recovery_paths]
        start = min(epoch(value['started_at']) for value in services)
        end = max(epoch(value['ended_at']) for value in services)
        count = sum(value['first_pass_decisions'] for value in services)
        verified_count = sum(value['verified_native_pairs'] for value in services)
        # Include the elapsed admission gap between separately owned frames.
        seconds = end - start if len(services) > 1 else services[0]['elapsed_seconds']
        recovery = {'started_at': precise_stamp(start), 'ended_at': precise_stamp(end), 'elapsed_seconds': seconds,
                    'frame_service_seconds': sum(value['elapsed_seconds'] for value in services),
                    'completed_frames': len(services), 'first_pass_decisions': count,
                    'verified_native_pairs': verified_count,
                    'held_or_uncertain_decisions': sum(value['held_or_uncertain_decisions'] for value in services),
                    'verified_audio_bytes': sum(value['verified_audio_bytes'] for value in services),
                    'decisions_per_hour': count * 3600 / seconds,
                    'immediate_success_fraction': verified_count / count,
                    'includes_interframe_admission_wait': len(services) > 1,
                    'isolated_bandwidth_measurement': False}
    done = recovery['first_pass_decisions'] if recovery else 0
    if done > next_count:
        raise ValueError('Recovery decisions exceed selected scope')
    if done == next_count:
        next_state = 'terminal_with_holds' if recovery['held_or_uncertain_decisions'] else 'complete'
    v5 = lane.get('kind') in {'native_v5_direct_batch', 'native_v5_source_hold'}
    campaign_running = lane.get('kind') in {'native_v4_campaign', 'native_v5_direct_batch', 'native_v5_bulk'} and lane.get('state') == 'running'
    campaign_held = lane.get('kind') in {'native_v4_source_hold', 'native_v5_source_hold'} or bulk and lane.get('state') == 'paused'
    campaign_done = lane.get('prior_completed_decisions', 0) if v5 else lane.get('completed_decisions', 0) if campaign_running or campaign_held else 0
    cohort_items = lane.get('frame_items') if v5 and not lane.get('completed_frame_decisions') else lane.get('source_count') if campaign_running or campaign_held else None
    if type(campaign_done) is not int or not 0 <= campaign_done <= untouched:
        raise ValueError('Invalid campaign progress')
    cohort_items = cohort_items if type(cohort_items) is int and 0 < cohort_items <= untouched else None
    result = {'generated_at': stamp(now), 'status_snapshot_at': status.get('generated_at'),
            'status': 'conditional_only', 'guaranteed_completion_date': None,
            'full_audio_and_text_completion_hours': None, 'newest20_items': twenty,
            'coverage': coverage, 'measured_service': service,
            'next_recovery_batch': dict(scenario(next_count - done, recovery['decisions_per_hour'] if recovery else rate),
                selected_items=next_count, completed_decisions=done,
                completed_verified_pairs=recovery['verified_native_pairs'] if recovery else 0,
                completed_held_items=recovery['held_or_uncertain_decisions'] if recovery else 0,
                measured_service=recovery,
                state=next_state, current_frame_items=lane.get('frame_items') if next_state == 'running' else None,
                current_frame_started_at=lane.get('started_at') if next_state == 'running' else None,
                scope='Previously held native audio; two independently admitted frames'),
            'untouched_first_pass': dict(scenario(untouched - campaign_done), frames=frames,
                selected_items=untouched, completed_decisions=campaign_done,
                original_selected_items=original_selection,
                current_cohort_items=cohort_items, current_cohort_index=lane.get('cohort_index') if campaign_running or campaign_held else None,
                later_prepared_items=untouched - campaign_done - (cohort_items or 0) if v5 else untouched - cohort_items if cohort_items else untouched,
                state='running_admitted_cohort' if campaign_running else 'held_native_source' if campaign_held else 'prepared_campaign_disabled',
                scope='Decisions on the frozen untouched selection, including holds and failures'),
            'assumptions': [
                'Latest completed download-only direct frame is the service baseline; startup, source, upload and closure time are included.' if service_direct else 'Latest completed 40-decision run is the end-to-end service baseline; startup and initial ASR staging wait are included.',
                'Recovery item mix differs from the calibration run. A 1–2x service-time allowance is an explicit planning assumption, not a statistical interval.',
                'Active hours assume similar source availability, successful-file lengths, Drive service and storage backpressure. Admission waits and downtime add calendar time.',
                'Only a separately admitted cohort may run. Later prepared cohorts remain disabled; a scenario does not authorize or schedule them.',
                'ASR is separate and may overlap acquisition. Language review, uncertain attempts, item quarantines and unavailable sources prevent a reliable all-audio-plus-text finish date.'],
            'historical_8_to_12_active_hours_superseded': True,
            'calibration': 'completed_download_only_frame' if service_direct else 'completed_joint_series'}
    qualified = status.get('qualified_lane', {})
    if qualified.get('kind') == 'qualified_youtube_batch':
        result['qualified_batch'] = qualified
        result['status'] = 'qualified_batch_eta_unmeasured'
        result['historical_native_first_pass_scenario'] = result['untouched_first_pass']
        result['untouched_first_pass'] = dict(result['untouched_first_pass'], planning_active_hours=None,
            calendar_hours_at_half_availability=None, state='no_active_native_first_pass')
        result['assumptions'].append('The separately qualified-edition batch has no representative end-to-end service calibration. Local startup failures do not establish a transfer rate or a provider refusal; its batch and full-goal finish dates remain unknown.')
    return result


def mixed_receipt_pace(checkpoints):
    """Measure verified arrivals against the same creator, rank and recording selection."""
    points, selection, ownership, basis = {}, None, None, None
    for checkpoint in checkpoints:
        current_basis = checkpoint.get('selection_basis')
        digest = checkpoint.get('priority_scope_sha256', checkpoint.get('selection_sha256'))
        tick = epoch(checkpoint.get("generated_at"))
        if (checkpoint.get("scope") != "newest20_receipt_coverage" or current_basis not in ('mixed_channel_uploads', 'latest20plus_public_regular')
                or not re.fullmatch(r"[0-9a-f]{64}", digest or "") or tick is None or tick <= 0):
            raise ValueError("Expected a dated audio-receipt checkpoint with a recognized selection")
        summary = checkpoint["summary"]
        rows = checkpoint["channels"]
        scope = {}
        saved = 0
        for row in rows:
            creator, target, count = row["channel_dir"], row["target"], row["audio_total"]
            if (not isinstance(creator, str) or not creator or creator in scope or type(target) is not int
                    or type(count) is not int or not 0 <= count <= target <= 20):
                raise ValueError("Invalid creator totals in mixed checkpoint")
            scope[creator] = target
            saved += count
        total = sum(scope.values())
        if (not scope or summary.get("channels") != len(scope) or summary.get("latest20_target") != total
                or saved != summary.get("audio_available") or total - saved != summary.get("remaining_audio")):
            raise ValueError("Mixed receipt totals disagree with creator rows")
        if selection is not None and (digest != selection or ownership != scope or basis != current_basis):
            raise ValueError("Mixing different recording selections would distort the measured rate")
        selection, ownership, basis = digest, scope, current_basis
        if tick in points and saved != points[tick]:
            raise ValueError("Conflicting saved counts at the same time")
        points[tick] = saved
    if not points:
        raise ValueError("No dated recording checkpoints")
    history = sorted(points.items())
    total = sum(ownership.values())
    # A withdrawn receipt is an inventory correction. Measure new progress
    # only after the most recent correction; preserve its time for audit.
    start = 0
    for index in range(1, len(history)):
        if history[index][1] < history[index - 1][1]:
            start = index
    first, initial = history[start]
    last, saved = history[-1]
    seconds, delta, remaining = last - first, saved - initial, total - saved
    rate = delta * 3600 / seconds if seconds > 0 else None
    hours = remaining / rate if rate else None
    if remaining == 0:
        hours = 0.0
    intervals = []
    for (begin, previous), (end, current) in zip(history[start:], history[start+1:]):
        elapsed = end - begin
        intervals.append({"started_at": precise_stamp(begin), "ended_at": precise_stamp(end),
                          "wall_seconds": elapsed, "new_verified": current - previous,
                          "verified_per_wall_hour": (current - previous) * 3600 / elapsed})
    rate_basis = 'regular_verified_receipts' if basis == 'latest20plus_public_regular' else 'mixed_verified_receipts'
    return {"basis": rate_basis, "selection_sha256": selection, "total": total, "saved": saved,
            "remaining": remaining, "checkpoints": len(history) - start, "started_at": precise_stamp(first),
            "ended_at": precise_stamp(last), "wall_seconds": seconds, "new_verified": delta,
            "verified_per_wall_hour": rate, "conditional_hours_at_observed_rate": hours,
            "conditional_finish_at_utc": precise_stamp(last + 3600 * hours) if hours is not None else None,
            "checkpoint_intervals": intervals,
            "last_receipt_correction_at": precise_stamp(first) if start else None}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--remote", default=DEFAULT_REMOTE)
    ap.add_argument("--queue", type=Path)
    ap.add_argument("--progress-log", type=Path, action="append", default=[])
    ap.add_argument("--out", type=Path)
    ap.add_argument("--coverage-checkpoint", action="append", default=[], type=Path,
                    help="Dated collection_coverage JSON. Repeat for the same selection to measure verified arrivals per wall hour.")
    ap.add_argument("--refresh-operational", action="store_true", help="Replace the current operational section, retaining dated historical assumptions")
    ap.add_argument("--service-live", type=Path, help="Terminal series JSON proof directory; no media is read")
    ap.add_argument("--service-direct", action="store_true", help="Calibrate from a bound completed download-only direct frame")
    ap.add_argument("--next-selection", type=Path)
    ap.add_argument("--campaign-selection", type=Path)
    ap.add_argument("--status-snapshot", type=Path, help="Saved aggregate status checkpoint")
    ap.add_argument("--recovery-live", type=Path, action='append', default=[],
                    help="Completed direct-recovery proof directory; repeat for independent frames")
    ap.add_argument("--workers", type=int, choices=range(1, 9), default=4)
    ap.add_argument("--metadata-interval", type=float, default=10)
    ap.add_argument("--caption-interval", type=float, default=15)
    ap.add_argument("--upload-mib", type=float, nargs=3, default=(1, 4, 10),
                    metavar=("SLOW", "CENTRAL", "FAST"), help="Assumed aggregate upload MiB/s")
    ap.add_argument("--download-mib", type=float, nargs=3, default=(.25, 1, 2),
                    metavar=("SLOW", "CENTRAL", "FAST"), help="Per-worker fallback when matched progress is insufficient")
    ap.add_argument("--availability", type=float, nargs="+", default=(1, .5, .25),
                    help="Assumed future available fractions, each greater than zero and at most one")
    args = ap.parse_args(argv)
    if args.coverage_checkpoint:
        paths = [path.resolve() for path in args.coverage_checkpoint]
        if args.refresh_operational or (args.out and args.out.resolve() in paths):
            ap.error("Use a distinct output for the mixed receipt estimate")
        try:
            pace = mixed_receipt_pace([read_object(path) for path in paths])
            key = 'regular_receipt_pace' if pace['basis'] == 'regular_verified_receipts' else 'mixed_receipt_pace'
            result = {"schema_version": 2, "scope": "collection_eta", "generated_at": pace["ended_at"],
                      "current": {"generated_at": pace["ended_at"], key: pace}}
            data = json.dumps(result, indent=2, allow_nan=False) + "\n"
            if args.out:
                atomic_write_text(args.out, data)
            else:
                print(data, end="")
        except (OSError, TypeError, ValueError, KeyError) as error:
            ap.exit(2, f"Mixed receipt input error: {error}\n")
        return 0
    if args.refresh_operational:
        if not all((args.out, args.service_live, args.next_selection, args.campaign_selection, args.status_snapshot)):
            ap.error('Operational refresh requires output, terminal service, both selections and aggregate status')
        if args.out.resolve().is_relative_to(args.root.resolve()) or args.out.resolve() in {
                path.resolve() for path in (args.next_selection, args.campaign_selection, args.status_snapshot)}:
            ap.error('Output must be separate from private evidence')
        try:
            previous = read_object(args.out)
            historical = previous.get('historical_assumptions', previous)
            current = operational_estimate(args.root, args.service_live, args.next_selection,
                args.campaign_selection, read_object(args.status_snapshot), remote=args.remote, recovery_live=args.recovery_live,
                service_direct=args.service_direct)
            result = {'schema_version': 2, 'scope': 'collection_eta', 'generated_at': current['generated_at'],
                      'current': current, 'historical_assumptions': historical}
            args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        except (OSError, ValueError, TypeError, KeyError):
            ap.exit(2, 'ETA input error: incomplete terminal/selection/status evidence; no estimate written.\n')
        return 0
    if not all(math.isfinite(v) and v >= 0 for v in (args.metadata_interval, args.caption_interval)):
        ap.error("Intervals must be finite and nonnegative")
    try:
        inputs, input_paths = {}, set()
        def read(label, path, optional=False):
            input_paths.add(path.resolve())
            data, inputs[label] = read_snapshot(path, optional)
            return data
        full = rows_from_bytes(read("full_queue", args.queue or args.root / "jobs/queue_youtube_all_merged.csv"))
        stages = {}
        for label, filename in (("newest20", "queue_newest20_enriched.csv"), ("newest50_inclusive", "queue_newest50_enriched.csv"), ("remaining_archive", "queue_final_round.csv")):
            data = read(label, args.root / "jobs" / filename, True)
            if data:
                stages[label] = rows_from_bytes(data)
        audio, audio_bad = records_from_bytes(read("audio_journal", args.root / "sync/drive_ingest_manifest.jsonl", True))
        captions, cap_bad = records_from_bytes(read("caption_journal", args.root / "sync/drive_caption_manifest.jsonl", True))
        log_data = [read(f"progress_log_{i+1}", path) for i, path in enumerate(args.progress_log)]
        cooldown_data = read("drive_cooldown", args.root / "sync/drive_ingest_cooldown.json", True)
        cooldown = json.loads(cooldown_data) if cooldown_data else {}
        result = estimate(full, audio, captions, stage_rows=stages, logs=log_data, remote=args.remote,
                          workers=args.workers, metadata_interval=args.metadata_interval,
                          caption_interval=args.caption_interval, upload_mib=args.upload_mib,
                          assumed_download_mib=args.download_mib, availability=args.availability,
                          drive_until=positive(cooldown.get("until_epoch")) or 0)
        result["input_snapshots"] = inputs
        result["malformed_receipt_records_skipped"] = {"audio": audio_bad, "caption": cap_bad}
        encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.out:
            if args.out.resolve() in input_paths or args.out.resolve().is_relative_to(args.root.resolve()):
                raise ValueError("Output must be separate from private inputs")
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(encoded, encoding="utf-8", newline="\n")
        else:
            print(encoded, end="")
    except (OSError, ValueError, TypeError, KeyError):
        ap.exit(2, "ETA input error: incomplete, changed or invalid metadata snapshot; no estimate written.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
