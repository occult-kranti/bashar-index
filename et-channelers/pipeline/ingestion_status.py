#!/usr/bin/env python3
"""Export aggregate collection status only; private record content never leaves the root."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
from pathlib import Path

if __package__:
    from .drive_ingest import terminal_unavailable
else:  # -I deliberately removes the script directory from the default import path.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from drive_ingest import terminal_unavailable


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


def pairs_recorded(record):
    metadata = record.get("metadata")
    return bool(record.get("status") == "deleted" and isinstance(metadata, dict)
                and all(record.get(k) and metadata.get(k) for k in ("drive_id", "md5", "sha256")))


def snapshot(root, now=None):
    """Allowlisted public values only; no private strings are copied to the result."""
    now = dt.datetime.now(dt.timezone.utc).timestamp() if now is None else now
    latest = {}
    manifest = root / "sync" / "drive_ingest_manifest.jsonl"
    if manifest.is_file():
        with manifest.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue  # a live writer may have an unfinished last record
                if isinstance(record, dict) and record.get("video_id"):
                    latest[record["video_id"]] = record
    verified = {key for key, rec in latest.items() if pairs_recorded(rec)}
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
    supervisor = read_object(root / "sync" / "drive_ingest_resume_state.json")
    configured = supervisor.get("schema_version") == 2
    archive_all = configured and supervisor.get("mode") in {"RunAll", "RunFinal"}
    workers = supervisor.get("download_workers") if configured else 4
    workers = workers if type(workers) is int and 1 <= workers <= 8 else 4
    retry = supervisor.get("until_epoch") if configured else None
    if type(retry) in (int, float) and 0 < retry < 253402300799:
        until = max(until or 0, retry)
    halted = configured and supervisor.get("state") in {
        "stopped", "retry_budget_exhausted", "stopped_after_nonquota_result"}
    state = "paused" if (root / "sync" / "STOP_DRIVE_INGEST").exists() else \
        "paused" if halted else "cooldown" if until and until > now else "ready" if latest else "unknown"
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
                          "workers": workers, "full_archive_requested": archive_all},
            "counts": {"verified_pairs": len(verified), "audio_downloaded": len(audio),
                       "unavailable": len(unavailable),
                       "awaiting_upload": len(audio - verified), "channels": channels,
                       "indexed_total": len(full | twenty | fifty), "final_round_indexed": len(remaining)},
            "storage": {"local_bytes": local_bytes, "ceiling_bytes": 19_000_000_000},
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
    args = ap.parse_args(argv)
    public = snapshot(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    temporary.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.out)
    print(json.dumps(public, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
