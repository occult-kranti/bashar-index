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
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drive_ingest import (CAPTION_POLICY, caption_receipt_complete, receipt_complete,
                          terminal_unavailable)
from ingestion_status import proof, record_row, source_deadline

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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--remote", default=DEFAULT_REMOTE)
    ap.add_argument("--queue", type=Path)
    ap.add_argument("--progress-log", type=Path, action="append", default=[])
    ap.add_argument("--out", type=Path)
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
