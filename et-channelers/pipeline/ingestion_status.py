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
                               caption_track_verified, receipt_complete, terminal_unavailable)
else:  # -I deliberately removes the script directory from the default import path.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from drive_ingest import (CAPTION_POLICY, HARD_BLOCKS, caption_receipt_complete,
                              caption_track_verified, receipt_complete, terminal_unavailable)

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


def snapshot(root, now=None, remote=DEFAULT_REMOTE):
    """Allowlisted public values only; no private strings are copied to the result."""
    now = dt.datetime.now(dt.timezone.utc).timestamp() if now is None else now
    latest = latest_records(root / "sync" / "drive_ingest_manifest.jsonl")
    captions = latest_records(root / "sync" / "drive_caption_manifest.jsonl")
    verified = {key for key, rec in latest.items() if proof(receipt_complete, rec, record_row(rec), remote)}
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
    source_until = source_deadline(latest.values())
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
    resolved = verified | unavailable
    complete20, complete50 = bool(twenty) and twenty <= resolved, bool(fifty) and fifty <= resolved
    return {"schema_version": 1, "generated_at": stamp(now), "scope": "local_youtube_collection",
            "operation": {"state": state, "retry_after": stamp(until) if until else None,
                          "workers": workers, "full_archive_requested": archive_all,
                          "cooldown_provider": provider, "caption_state": caption_state,
                          "caption_retry_after": stamp(caption_until) if caption_until else None},
            "counts": {"verified_pairs": len(verified), "audio_downloaded": len(audio),
                       "caption_verified_videos": len(caption_verified), "caption_verified_tracks": len(verified_tracks),
                       "caption_none_english": len(caption_none), "caption_pending_videos": len(caption_pending),
                       "unavailable": len(unavailable),
                       "awaiting_upload": len(audio - verified), "channels": channels,
                       "indexed_total": len(full | twenty | fifty), "final_round_indexed": len(remaining)},
            "storage": {"local_bytes": local_bytes, "ceiling_bytes": ceiling},
            "stages": [{"key": "newest20", "label": "Newest 20", "total": len(twenty),
                        "verified": len(twenty & verified), "unavailable": len(twenty & unavailable),
                        "state": "complete" if complete20 else "in_progress"},
                       {"key": "newest50", "label": "Extend to 50", "total": len(fifty),
                        "verified": len(fifty & verified), "unavailable": len(fifty & unavailable),
                        "state": "complete" if complete50 else "in_progress" if complete20 else "waiting"},
                       {"key": "final_archive" if archive_all else "final_index",
                        "label": "Archive the remainder" if archive_all else "Index the remainder", "total": len(remaining),
                        "verified": len(remaining & verified), "unavailable": len(remaining & unavailable),
                        "state": ("complete" if remaining and remaining <= resolved else "in_progress" if complete50 else "waiting")
                                 if archive_all else "indexed" if remaining else "waiting"}]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--remote", default=DEFAULT_REMOTE, help="Exact archive destination used by receipt proofs")
    args = ap.parse_args(argv)
    public = snapshot(args.root, remote=args.remote)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    temporary.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.out)
    print(json.dumps(public, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
