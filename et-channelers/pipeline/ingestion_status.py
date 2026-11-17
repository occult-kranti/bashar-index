#!/usr/bin/env python3
"""Export aggregate collection status only; private record content never leaves the root."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

if __package__:
    from .drive_ingest import (CAPTION_POLICY, HARD_BLOCKS, caption_receipt_complete,
                               caption_track_verified, receipt_complete, terminal_unavailable, tree_bytes)
    from .chromium_capture_service import browser_receipt_complete
else:  # -I deliberately removes the script directory from the default import path.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from drive_ingest import (CAPTION_POLICY, HARD_BLOCKS, caption_receipt_complete,
                              caption_track_verified, receipt_complete, terminal_unavailable, tree_bytes)
    from chromium_capture_service import browser_receipt_complete

DEFAULT_REMOTE = "etdrive:04 Audio"


def stamp(value=None):
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z") \
        if value is not None else dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_object(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def queue_ids(root, names):
    for name in names:
        path = root / "jobs" / name
        if path.is_file():
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            return {r["video_id"] for r in rows if r.get("video_id")}, len({r.get("channel_dir") for r in rows})
    return set(), 0


def record_row(record):
    video_id, channel = record.get("video_id"), record.get("channel_dir")
    if not isinstance(video_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return None
    if not isinstance(channel, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", channel):
        return None
    return {"video_id": video_id, "channel_dir": channel}


def proof(predicate, record, row, remote):
    if row is None:
        return False
    try:
        return bool(predicate(record, row, remote))
    except (KeyError, TypeError, ValueError, AttributeError):
        return False  # malformed private records are never completion evidence


def latest_records(path):
    records = {}
    if path.is_file():
        with path.open(encoding="utf-8-sig") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue  # a live writer may have an unfinished last record
                if isinstance(record, dict) and isinstance(record.get("video_id"), str) and record["video_id"]:
                    records[record["video_id"]] = record
    return records


def source_deadline(records):
    return max((rec.get('retry_not_before_epoch', 0) for rec in records
                if (rec.get('source_error_class') or rec.get('error_class')) in HARD_BLOCKS
                and type(rec.get('retry_not_before_epoch')) in (int, float)
                and 0 < rec['retry_not_before_epoch'] < 253402300799), default=0)


def asr_receipt_complete(record, audio, remote):
    """A generated transcript counts only with bundle and exact source proofs."""
    run_id = record.get('run_id', '')
    row = record_row(audio)
    if (not row or not proof(receipt_complete, audio, row, remote) or
            not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', run_id)):
        return False
    expected = audio['remote'].rpartition('/')[0] + '/' + row['video_id'] + '/ASR/' + run_id + '/' + run_id + '.zip'
    return (record.get('status') == 'verified' and record.get('artifact_kind') == 'asr_bundle' and
            record.get('video_id') == row['video_id'] and record.get('channel_dir') == row['channel_dir'] and
            record.get('remote') == expected and bool(record.get('drive_id')) and
            type(record.get('bytes')) is int and record['bytes'] > 0 and
            isinstance(record.get('md5'), str) and bool(re.fullmatch(r'[0-9a-f]{32}', record['md5'])) and
            isinstance(record.get('sha256'), str) and bool(re.fullmatch(r'[0-9a-f]{64}', record['sha256'])) and
            record.get('source_audio_drive_id') == audio.get('drive_id') and
            record.get('source_audio_sha256') == audio.get('sha256'))


def asr_records(path, identity_key='run_id'):
    records = {}
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict) and isinstance(record.get('video_id'), str) and isinstance(record.get(identity_key), str):
                records[(record['video_id'], record[identity_key])] = record
    return records.values()


def snapshot(root, now=None, remote=DEFAULT_REMOTE, managed_roots=()):
    """Allowlisted public values only; no private strings are copied to the result."""
    now = dt.datetime.now(dt.timezone.utc).timestamp() if now is None else now
    latest = latest_records(root / "sync" / "drive_ingest_manifest.jsonl")
    captions = latest_records(root / "sync" / "drive_caption_manifest.jsonl")
    verified = {key for key, rec in latest.items() if proof(receipt_complete, rec, record_row(rec), remote)}
    browser_verified = set()
    for rec in asr_records(root / 'sync/browser_capture_manifest.jsonl', 'capture_id'):
        row = record_row(rec)
        if row and rec.get('tab') in {'videos', 'shorts', 'streams', ''} and proof(
                browser_receipt_complete, rec, dict(row, tab=rec['tab']), remote):
            browser_verified.add(rec['video_id'])
    archived = verified | browser_verified
    asr_verified = {rec['video_id'] for rec in asr_records(root / 'sync/asr_manifest.jsonl')
                    if asr_receipt_complete(rec, latest.get(rec['video_id'], {}), remote)}
    runtime = read_object(root / 'asr/jobs/batch_runtime_state.json')
    asr_state, asr_reported_at = 'unconfirmed', None
    try:
        reported = dt.datetime.fromisoformat(runtime.get('updated_at', '').replace('Z', '+00:00'))
        if reported.tzinfo and 0 <= now - reported.timestamp() <= 600 and runtime.get('state') in {
                'running', 'complete', 'stopped_error'}:
            asr_state, asr_reported_at = runtime['state'], stamp(reported.timestamp())
    except (ValueError, TypeError, AttributeError):
        pass
    caption_verified, caption_none, verified_tracks = set(), set(), set()
    for key, rec in captions.items():
        row = record_row(rec)
        if rec.get("policy") != CAPTION_POLICY:
            continue
        tracks = rec.get("tracks")
        if not isinstance(tracks, list):
            continue
        for track in tracks:
            if isinstance(track, dict) and proof(caption_track_verified, track, row, remote):
                verified_tracks.add((key, track["track_id"]))
        if proof(caption_receipt_complete, rec, row, remote):
            (caption_none if rec.get("status") == "none" else caption_verified).add(key)
    caption_pending = (verified | captions.keys()) - caption_verified - caption_none
    # A verified track remains available while other tracks or inventory entries
    # need review. Availability is not a claim about complete speech coverage.
    caption_text_available = {key for key, _ in verified_tracks} & archived
    text_available = (asr_verified | caption_text_available) & archived
    text_inventory_complete = (asr_verified | caption_verified) & archived
    unavailable = {key for key, rec in latest.items() if terminal_unavailable(rec)}
    audio = {key for key, rec in latest.items() if rec.get("bytes", 0) and rec.get("sha256")}
    twenty, channels = queue_ids(root, ("queue_newest20_enriched.csv", "queue_newest20.csv"))
    fifty, _ = queue_ids(root, ("queue_newest50_enriched.csv", "queue_newest50.csv"))
    full, _ = queue_ids(root, ("queue_youtube_all_merged.csv", "queue_youtube_all.csv"))
    remaining, _ = queue_ids(root, ("queue_final_round.csv",))
    cooldown = read_object(root / "sync" / "drive_ingest_cooldown.json")
    # Support the runner's fixed filename, without exposing it in the export.
    if not cooldown:
        cooldown = read_object(root / "sync" / "drive_cooldown.json")
    until = cooldown.get("until_epoch")
    until = float(until) if isinstance(until, (int, float)) and 0 < until < 253402300799 else None
    drive_until = until or 0
    native_cooldown = read_object(root / 'sync/native_batch_source_cooldown.json')
    native_until = source_deadline([native_cooldown]) if (
        native_cooldown.get('schema_version') == 1 and native_cooldown.get('endpoint') == 'youtube_native_audio') else 0
    # A passive browser refusal can precede BEGIN and therefore has no audio receipt.
    source_until = max(source_deadline(latest.values()), native_until)
    caption_until = source_deadline(captions.values())
    until = max(until or 0, source_until) or None
    supervisor = read_object(root / "sync" / "drive_ingest_resume_state.json")
    configured = supervisor.get("schema_version") == 2
    archive_all = configured and supervisor.get("mode") in {"RunAll", "RunFinal"}
    workers = supervisor.get("download_workers") if configured else 4
    workers = workers if type(workers) is int and 1 <= workers <= 8 else 4
    ceiling = supervisor.get('private_root_ceiling_bytes') if configured else None
    ceiling = ceiling if type(ceiling) is int and 1_000_000_000 <= ceiling <= 17_000_000_000 else 17_000_000_000
    retry = supervisor.get("until_epoch") if configured else None
    caption_wait = configured and (supervisor.get('await_caption_backfill') is True or
        supervisor.get('state') in {'waiting_for_caption_cooldown', 'caption_backfill_retry_budget_exhausted'})
    legacy_source = supervisor.get('source_until_epoch') if configured else None
    legacy_caption_wait = (configured and supervisor.get('cooldown_scope_version') != 1
        and type(legacy_source) in (int, float) and type(retry) in (int, float)
        and caption_until > now and abs(legacy_source - caption_until) < 0.001
        and abs(retry - legacy_source) <= 1.001)
    if type(retry) in (int, float) and 0 < retry < 253402300799 and not caption_wait and not legacy_caption_wait:
        until = max(until or 0, retry)
    provider = 'both' if source_until > now and drive_until > now else \
        'youtube' if source_until > now else 'drive' if drive_until > now else None
    if not provider and until and until > now and configured:
        provider = supervisor.get('cooldown_provider')
        if provider not in {'drive', 'youtube', 'both'}:
            provider = 'youtube' if supervisor.get('state') == 'waiting_for_youtube_cooldown' else 'drive'
    halted = configured and supervisor.get("state") in {
        "stopped", "retry_budget_exhausted", "stopped_after_nonquota_result"}
    state = "paused" if (root / "sync" / "STOP_DRIVE_INGEST").exists() else \
        "paused" if halted else "cooldown" if until and until > now else "ready" if latest or captions else "unknown"
    caption_state = 'paused' if (root / 'sync' / 'STOP_DRIVE_INGEST').exists() or (
        configured and supervisor.get('state') == 'caption_backfill_retry_budget_exhausted') else \
        'cooldown' if caption_until > now else 'pending' if caption_pending else \
        'complete' if captions or verified else 'unknown'
    local_bytes = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(base) / name).is_symlink()]
        for name in files:
            try:
                path = Path(base) / name
                if not path.is_symlink():
                    local_bytes += path.stat().st_size
            except OSError:
                pass
    storage = {"local_bytes": local_bytes, "ceiling_bytes": ceiling}
    if managed_roots:
        all_roots = sorted({root.resolve(), *(Path(p).resolve() for p in managed_roots)}, key=lambda p:len(p.parts))
        included = []
        for candidate in all_roots:
            if not any(candidate.is_relative_to(parent) for parent in included):
                included.append(candidate)
        storage['managed_bytes'] = sum(tree_bytes(path) for path in included)
        plan = read_object(root / 'sync/analysis_resource_plan.json')
        managed_cap = plan.get('accounting_cap_bytes')
        if type(managed_cap) is int and 1_000_000_000 <= managed_cap <= 18_000_000_000:
            storage['managed_ceiling_bytes'] = managed_cap
    resolved = archived | unavailable
    complete20, complete50 = bool(twenty) and twenty <= resolved, bool(fifty) and fifty <= resolved
    return {"schema_version": 1, "generated_at": stamp(now), "scope": "local_youtube_collection",
            "operation": {"state": state, "retry_after": stamp(until) if until else None,
                          "asr_last_reported_state": asr_state, "asr_reported_at": asr_reported_at,
                          "workers": workers, "full_archive_requested": archive_all,
                          "cooldown_provider": provider, "caption_state": caption_state,
                          "caption_retry_after": stamp(caption_until) if caption_until else None},
            "counts": {"verified_pairs": len(verified), "audio_downloaded": len(audio),
                       "browser_recorded_videos": len(browser_verified), "audio_archived_videos": len(archived),
                       "asr_verified_videos": len(asr_verified),
                       "text_artifact_videos": len((asr_verified | caption_verified) & archived),
                       "text_pending_videos": len(archived - asr_verified - caption_verified),
                       "text_available_videos": len(text_available),
                       "text_inventory_complete_videos": len(text_inventory_complete),
                       "text_missing_videos": len(archived - text_available),
                       "caption_text_available_videos": len(caption_text_available),
                       "caption_inventory_review_videos": len(caption_text_available - caption_verified),
                       "caption_verified_videos": len(caption_verified), "caption_verified_tracks": len(verified_tracks),
                       "caption_none_english": len(caption_none), "caption_pending_videos": len(caption_pending),
                       "unavailable": len(unavailable),
                       "awaiting_upload": len(audio - verified), "channels": channels,
                       "indexed_total": len(full | twenty | fifty), "final_round_indexed": len(remaining)},
            "storage": storage,
            "stages": [{"key": "newest20", "label": "Newest 20", "total": len(twenty),
                        "verified": len(twenty & archived), "unavailable": len(twenty & unavailable),
                        "state": "complete" if complete20 else "in_progress"},
                       {"key": "newest50", "label": "Extend to 50", "total": len(fifty),
                        "verified": len(fifty & archived), "unavailable": len(fifty & unavailable),
                        "state": "complete" if complete50 else "in_progress" if complete20 else "waiting"},
                       {"key": "final_archive" if archive_all else "final_index",
                        "label": "Archive the remainder" if archive_all else "Index the remainder", "total": len(remaining),
                        "verified": len(remaining & archived), "unavailable": len(remaining & unavailable),
                        "state": ("complete" if remaining and remaining <= resolved else "in_progress" if complete50 else "waiting")
                                 if archive_all else "indexed" if remaining else "waiting"}]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--remote", default=DEFAULT_REMOTE, help="Exact archive destination used by receipt proofs")
    ap.add_argument("--managed-root", type=Path, action="append", default=[],
                    help="Additional project tool/repository roots to include in aggregate storage accounting")
    args = ap.parse_args(argv)
    public = snapshot(args.root, remote=args.remote, managed_roots=args.managed_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    temporary.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.out)
    print(json.dumps(public, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
