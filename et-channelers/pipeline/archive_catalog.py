#!/usr/bin/env python3
"""Private, incremental research catalog for native audio and full metadata on Drive.

prepare is offline. upload sends only unacknowledged immutable catalog objects,
then their manifest, through the collector's existing Drive adapter. Neither
operation lists Drive, reads media, modifies per-video metadata, or deletes files.
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ID_RE, ensure_outside_git, utc_now
from drive_ingest import (MAX_LOCAL_BYTES, SOURCE_FOLDERS, IngestError, Rclone, exclusive_lock,
                          caption_receipt_complete, caption_track_verified, journal, receipt_complete,
                          tree_bytes, valid_recorded_remote, verify_remote)
from prepare_all_queue import snapshot

SCHEMA = 1
CATALOG_DIR = Path("catalog/youtube_archive")
REMOTE_DIR = "_catalog/youtube"
QUEUE_FIELDS = ["video_id", "url", "channel_dir", "source_channel_name", "primary_person_id",
                "primary_person_name", "primary_person_role", "primary_person_basis", "tab", "listing_rank",
                "title", "duration_s", "upload_date_approx", "channeling", "entity", "entity_label_basis",
                "sources", "queue_provenance"]
CAPTION_FIELDS = ["caption_state", "caption_receipt_status", "caption_error_class", "caption_captured_at",
                  "caption_policy", "caption_inventory_status", "caption_tracks", "caption_verified_tracks", "caption_published_tracks",
                  "caption_automatic_original_tracks", "caption_languages", "caption_verified_languages",
                  "caption_excluded_translated", "caption_excluded_languages", "caption_excluded_noncaption", "caption_unresolved", "caption_bundles"]
FIELDS = QUEUE_FIELDS + ["source_folder", "archive_channel_dir", "archive_state", "receipt_status",
                         "error_class", "published", "downloaded_at", "verified_at", "deleted_at"] + [
    f"{kind}_{field}" for kind in ("audio", "metadata")
    for field in ("remote", "drive_id", "bytes", "md5", "sha256")] + CAPTION_FIELDS
CHANNEL_FIELDS = ["channel_dir", "source_channel_name", "primary_people", "person_attribution_bases",
                  "tab", "source_folder", "items", "verified_pairs", "downloaded_unverified",
                  "known_duration_hours", "unknown_duration_items", "entity_labels_unverified",
                  "caption_complete_videos", "caption_videos_with_verified_tracks", "caption_verified_tracks",
                  "caption_none_videos", "caption_verified_languages"]


def encoded_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "md5": hashlib.md5(data).hexdigest()}


def csv_bytes(rows, fields):
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def valid_channel(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", value)


def read_receipts(path):
    """Read one byte snapshot; malformed journal evidence never becomes a receipt."""
    data = path.read_bytes() if path.exists() else b""
    latest, lines = {}, data.splitlines(keepends=True)
    warnings = {"malformed_lines": 0, "unfinished_tail": 0}
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except (ValueError, UnicodeError):
            if i == len(lines) - 1 and not line.endswith(b"\n"):
                warnings["unfinished_tail"] += 1
            else:
                warnings["malformed_lines"] += 1
            continue
        if isinstance(record, dict) and record.get("video_id"):
            latest[record["video_id"]] = record
    return latest, hashlib.sha256(data).hexdigest(), warnings


def compact_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def caption_fields(record, source, remote):
    """Expose provenance/proof only; never read bundles or copy text/request fields."""
    result = dict.fromkeys(CAPTION_FIELDS, "")
    result["caption_state"] = "unknown"
    if not record:
        return result
    owner = record.get("channel_dir") or source["channel_dir"]
    if not valid_channel(owner):
        raise ValueError("Caption receipt has an unsafe archive channel directory")
    tracks, unresolved = record.get("tracks"), record.get("unresolved")
    if not isinstance(tracks, list) or any(not isinstance(track, dict) for track in tracks):
        raise ValueError("Caption receipt tracks must be objects in a list")
    if not isinstance(unresolved, list):
        raise ValueError("Caption receipt unresolved tracks must be a list")
    if any(not isinstance(track.get("track_id"), str) or not isinstance(track.get("language", ""), str)
           for track in tracks):
        raise ValueError("Caption track identities and languages must be strings")
    if len({track.get("track_id") for track in tracks}) != len(tracks):
        raise ValueError("Caption receipt contains duplicate track identities")
    row = dict(source, channel_dir=owner)
    proven = [track for track in tracks if caption_track_verified(track, row, remote)]
    complete = caption_receipt_complete(record, row, remote)
    state = "none" if complete and record.get("status") == "none" else "verified" if complete else (
        "verified_retained" if tracks and len(proven) == len(tracks) and not unresolved else
        "partially_verified" if proven else "downloaded_unverified" if record.get("status") == "ready" else "pending")
    def languages(selected):
        return dict(sorted(collections.Counter(
            track.get("language") or "unknown" for track in selected).items()))
    bundles = []
    for track in proven:
        bundle = track["bundle"]
        # Native provenance uses raw_format; keep ext for existing catalog readers.
        formats = [track.get(key) for key in ("raw_format", "ext") if track.get(key) not in (None, "")]
        extension = ""
        if formats and all(isinstance(value, str) and value in {"json3", "vtt"} for value in formats):
            if len(set(formats)) == 1:
                extension = formats[0]
        bundles.append({**{key: track.get(key, "") for key in ("track_id", "language", "kind")},
                        "ext": extension,
                        **{key: bundle.get(key, "") for key in ("remote", "drive_id", "bytes", "md5", "sha256")}})
    result.update(caption_state=state, caption_receipt_status=record.get("status", ""),
                  caption_error_class=record.get("error_class", ""), caption_captured_at=record.get("captured_at", ""),
                  caption_policy=record.get("policy", ""), caption_inventory_status=record.get("inventory_status", ""),
                  caption_tracks=len(tracks), caption_verified_tracks=len(proven),
                  caption_published_tracks=sum(t.get("kind") == "published" for t in tracks),
                  caption_automatic_original_tracks=sum(t.get("kind") == "automatic_original" for t in tracks),
                  caption_languages=compact_json(languages(tracks)), caption_verified_languages=compact_json(languages(proven)),
                  caption_unresolved=len(unresolved), caption_bundles=compact_json(sorted(bundles, key=lambda b: b["track_id"])))
    for field in ("excluded_translated", "excluded_languages", "excluded_noncaption"):
        value = record.get(field, 0)
        if isinstance(value, list):
            value = len(value)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("Caption excluded counts must be nonnegative integers or lists")
        result[f"caption_{field}"] = value
    return result


def item_rows(queue, receipts, remote, caption_receipts=None):
    """Queue identity and attribution stay separate from the actual storage owner."""
    items = {}
    for source in queue:
        video_id, channel = source.get("video_id", ""), source.get("channel_dir", "")
        if not ID_RE.fullmatch(video_id) or not valid_channel(channel) or video_id in items:
            raise ValueError("Catalog queue must have unique valid IDs and safe source directories")
        tab = source.get("tab") or ""
        if tab not in SOURCE_FOLDERS:
            raise ValueError("Catalog queue contains an unknown source tab")
        row = {field: source.get(field, "") or "" for field in QUEUE_FIELDS}
        row.update(url=f"https://www.youtube.com/watch?v={video_id}", source_folder=SOURCE_FOLDERS[tab],
                   archive_state="queued", primary_person_basis=source.get("primary_person_basis") or "unknown",
                   entity_label_basis=source.get("entity_label_basis") or "unknown")
        record = receipts.get(video_id, {})
        owner = record.get("channel_dir") or channel
        if not valid_channel(owner):
            raise ValueError("Receipt has an unsafe archive channel directory")
        receipt_row = dict(source, channel_dir=owner)
        if record.get("remote"):
            extension = Path(record.get("path", "")).suffix.lstrip(".")
            if not valid_recorded_remote(remote, receipt_row, extension, record["remote"]):
                raise ValueError("Receipt points outside the selected archive/channel/item")
        metadata = record.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError("Receipt metadata must be an object")
        if metadata.get("remote") and metadata["remote"] != record.get("remote", "").rpartition("/")[0] + f"/{video_id}.info.json":
            raise ValueError("Metadata receipt does not accompany its audio item")
        pair = receipt_complete(record, receipt_row, remote)
        row["archive_state"] = "verified_pair" if pair else "downloaded_unverified" if record.get("bytes") and record.get("sha256") else "queued"
        row.update(archive_channel_dir=owner if record else "", receipt_status=record.get("status", ""),
                   error_class=record.get("error_class", ""))
        for field in ("published", "downloaded_at", "verified_at", "deleted_at"):
            row[field] = record.get(field, "")
        if record.get("duration_s") is not None:
            row["duration_s"] = record["duration_s"]
        for kind, artifact in (("audio", record), ("metadata", metadata)):
            for field in ("remote", "drive_id", "bytes", "md5", "sha256"):
                row[f"{kind}_{field}"] = artifact.get(field, "")
        row.update(caption_fields((caption_receipts or {}).get(video_id, {}), source, remote))
        items[video_id] = {key: "" if row.get(key) is None else str(row.get(key, "")) for key in FIELDS}
    return items


def caption_counts(rows):
    rows = list(rows)
    language_counts = collections.Counter()
    for row in rows:
        language_counts.update(json.loads(row.get("caption_verified_languages") or "{}"))
    return {"caption_complete_videos": sum(r.get("caption_state") == "verified" for r in rows),
            "caption_videos_with_verified_tracks": sum(int(r.get("caption_verified_tracks") or 0) > 0 for r in rows),
            "caption_verified_tracks": sum(int(r.get("caption_verified_tracks") or 0) for r in rows),
            "caption_none_videos": sum(r.get("caption_state") == "none" for r in rows),
            "caption_verified_languages": dict(sorted(language_counts.items()))}


def channels(rows):
    grouped = collections.defaultdict(list)
    for row in rows:
        grouped[(row["channel_dir"], row["tab"])].append(row)
    result = []
    for (channel, tab), members in sorted(grouped.items()):
        durations = []
        for row in members:
            try:
                duration = float(row["duration_s"])
                if duration >= 0 and duration < float("inf"):
                    durations.append(duration)
            except (TypeError, ValueError):
                pass
        caption_summary = caption_counts(members)
        caption_summary["caption_verified_languages"] = compact_json(caption_summary["caption_verified_languages"])
        result.append({"channel_dir": channel, "source_channel_name": members[0]["source_channel_name"],
                       "primary_people": " | ".join(sorted({r["primary_person_name"] for r in members} - {""})),
                       "person_attribution_bases": "+".join(sorted({r["primary_person_basis"] for r in members})),
                       "tab": tab or "unknown", "source_folder": SOURCE_FOLDERS[tab], "items": len(members),
                       "verified_pairs": sum(r["archive_state"] == "verified_pair" for r in members),
                       "downloaded_unverified": sum(r["archive_state"] == "downloaded_unverified" for r in members),
                       "known_duration_hours": round(sum(durations) / 3600, 3),
                       "unknown_duration_items": len(members) - len(durations),
                       "entity_labels_unverified": sum(bool(r["entity"]) for r in members), **caption_summary})
    return result


def catalog_path(folder, relative):
    if not isinstance(relative, str) or "\\" in relative:
        raise ValueError("Invalid catalog-relative path")
    path = (folder / relative).resolve()
    if not path.is_relative_to(folder.resolve()) or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Catalog path escapes its private directory")
    return path


def checked_bytes(folder, descriptor):
    data = catalog_path(folder, descriptor["file"]).read_bytes()
    actual = digest(data)
    if any(actual[key] != descriptor.get(key) for key in actual):
        raise ValueError("Catalog object integrity check failed")
    return data


def load_manifest(path):
    data = path.read_bytes()
    if path.stem != hashlib.sha256(data).hexdigest():
        raise ValueError("Catalog manifest filename/hash mismatch")
    manifest = json.loads(data)
    if manifest.get("schema_version") != SCHEMA or manifest.get("merge_rule") != "video_id_last_wins":
        raise ValueError("Unsupported catalog manifest")
    return manifest


def rebuild(manifest_path):
    """Verify and merge baseline + deltas in order; return rows sorted by video ID."""
    manifest_path = Path(manifest_path)
    manifest = load_manifest(manifest_path)
    folder, result = manifest_path.parent.parent, {}
    for descriptor in [manifest["baseline"], *manifest["deltas"]]:
        data = gzip.decompress(checked_bytes(folder, descriptor)).decode("utf-8")
        for row in csv.DictReader(io.StringIO(data)):
            if not ID_RE.fullmatch(row.get("video_id", "")):
                raise ValueError("Catalog contains an invalid video ID")
            result[row["video_id"]] = row
    if len(result) != manifest["counts"]["items"]:
        raise ValueError("Catalog rebuilt item count differs from manifest")
    return [result[key] for key in sorted(result)]


def atomic_bytes(path, data, root, cap, min_free):
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("Immutable catalog object already exists with different bytes")
        return
    if tree_bytes(root) + len(data) > cap or shutil.disk_usage(root).free - len(data) < min_free:
        raise IngestError("storage_limit", "Catalog checkpoint does not fit the local storage budget")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp{os.getpid()}")
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def join_remote(remote, relative):
    return remote.rstrip("/") + ("" if remote.endswith(":") else "/") + relative


def upload_plan(root, manifest_path, remote):
    root, manifest_path = Path(root).resolve(), Path(manifest_path).resolve()
    folder = root / CATALOG_DIR
    if manifest_path.parent != folder / "manifests":
        raise ValueError("Manifest is outside the selected private catalog")
    manifest = load_manifest(manifest_path)
    if manifest["archive_remote"] != remote.rstrip("/"):
        raise ValueError("Catalog belongs to a different archive destination")
    descriptors = [manifest["baseline"], *manifest["deltas"], manifest["channels"]]
    descriptors.append(dict(file=manifest_path.relative_to(folder).as_posix(), kind="manifest", **digest(manifest_path.read_bytes())))
    files = [dict(item, path=str(catalog_path(folder, item["file"])),
                  remote=join_remote(remote, f"{REMOTE_DIR}/{item['file']}")) for item in descriptors]
    return {"root": str(root), "manifest_path": str(manifest_path), "manifest_remote": files[-1]["remote"],
            "files": files, "counts": manifest["counts"], "receipt_parse_warnings": manifest["inputs"].get("receipt_parse_warnings", {}),
            "caption_receipt_parse_warnings": manifest["inputs"].get("caption_receipt_parse_warnings", {})}


def prepare_catalog(root, queue, remote, max_local_bytes=17_000_000_000, min_free_bytes=3_000_000_000):
    """Create a baseline, or a delta of changed rows; a no-op reuses the same manifest."""
    root = ensure_outside_git(root)
    if not remote or not 0 < max_local_bytes <= MAX_LOCAL_BYTES:
        raise ValueError("Catalog needs an archive destination and a local ceiling at most 20 GB")
    root.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(root):
        folder, pointer = root / CATALOG_DIR, root / CATALOG_DIR / "current.json"
        sources, queue_input = snapshot(Path(queue))
        if not sources:
            raise ValueError("Catalog queue is empty")
        receipts, receipt_sha, warnings = read_receipts(root / "sync/drive_ingest_manifest.jsonl")
        caption_receipts, caption_sha, caption_warnings = read_receipts(root / "sync/drive_caption_manifest.jsonl")
        current = item_rows(sources, receipts, remote, caption_receipts)
        previous, old_rows = None, {}
        if pointer.exists():
            prior = json.loads(pointer.read_text(encoding="utf-8"))
            old_path = catalog_path(folder, prior["manifest"])
            previous = load_manifest(old_path)
            if previous["archive_remote"] != remote.rstrip("/"):
                raise ValueError("Existing catalog belongs to another archive destination")
            if previous["inputs"]["queue_sha256"] == queue_input["sha256"]:
                old_rows = {r["video_id"]: r for r in rebuild(old_path)}
        changed = [current[key] for key in sorted(current) if current[key] != old_rows.get(key)]
        if (old_rows and not changed and previous["inputs"].get("receipt_parse_warnings") == warnings
                and previous["inputs"].get("caption_receipt_parse_warnings") == caption_warnings):
            return dict(upload_plan(root, old_path, remote), changed_items=0, new_snapshot=False)

        def store(data, suffix, kind, count):
            evidence = digest(data)
            relative = f"objects/{evidence['sha256']}.{suffix}"
            atomic_bytes(catalog_path(folder, relative), data, root, max_local_bytes, min_free_bytes)
            return dict(file=relative, kind=kind, rows=count, **evidence)

        delta = bool(old_rows)
        item_object = store(gzip.compress(csv_bytes(changed, FIELDS), compresslevel=6, mtime=0), "items.csv.gz",
                            "delta" if delta else "baseline", len(changed)) if changed or not delta else None
        summaries = channels(current.values())
        channel_object = store(csv_bytes(summaries, CHANNEL_FIELDS), "channels.csv", "channels", len(summaries))
        manifest = {"schema_version": SCHEMA, "created_at": utc_now(), "archive_remote": remote.rstrip("/"),
                    "merge_rule": "video_id_last_wins", "full_metadata": "Per-video .info.json beside native audio; this catalog does not replace it.",
                    "attribution": "Missing person/entity stays unknown; existing entity labels remain source metadata, not verified attribution.",
                    "duration_filter": None, "inputs": {"queue_sha256": queue_input["sha256"], "receipt_snapshot_sha256": receipt_sha,
                                                          "receipt_parse_warnings": warnings,
                                                          "caption_receipt_snapshot_sha256": caption_sha,
                                                          "caption_receipt_parse_warnings": caption_warnings},
                    "baseline": previous["baseline"] if delta else item_object,
                    "deltas": [*previous["deltas"], *([item_object] if item_object else [])] if delta else [], "channels": channel_object,
                    "counts": {"items": len(current), "source_directories": len({r["channel_dir"] for r in current.values()}),
                               "verified_pairs": sum(r["archive_state"] == "verified_pair" for r in current.values()),
                               "tabs": dict(collections.Counter(r["tab"] or "unknown" for r in current.values())),
                               **caption_counts(current.values())}}
        data = encoded_json(manifest)
        manifest_path = folder / "manifests" / f"{hashlib.sha256(data).hexdigest()}.json"
        atomic_bytes(manifest_path, data, root, max_local_bytes, min_free_bytes)
        pointer_data = encoded_json({"manifest": manifest_path.relative_to(folder).as_posix()})
        # Content-addressed scratch is safe to reuse after a crash; a different
        # pending checkpoint never blocks the next pointer update.
        temporary = pointer.with_name(f"current.{hashlib.sha256(pointer_data).hexdigest()}.next.json")
        atomic_bytes(temporary, pointer_data, root, max_local_bytes, min_free_bytes)
        os.replace(temporary, pointer)
        return dict(upload_plan(root, manifest_path, remote), changed_items=len(changed), new_snapshot=True)


def upload_catalog(plan, drive):
    """Upload new immutable objects first, manifest last; durable receipts avoid relisting."""
    root = ensure_outside_git(plan["root"])
    manifest = load_manifest(Path(plan["manifest_path"]))
    canonical = upload_plan(root, plan["manifest_path"], manifest["archive_remote"])
    receipt_path = root / CATALOG_DIR / "uploads.jsonl"
    uploaded, reused, warnings = 0, 0, 0
    with exclusive_lock(root):
        if (root / "sync/STOP_DRIVE_INGEST").exists():
            raise IngestError("stopped", "Persistent collection stop marker is present; no catalog upload started")
        recorded = {}
        if receipt_path.exists():
            lines = receipt_path.read_bytes().splitlines(keepends=True)
            for i, line in enumerate(lines):
                try:
                    entry = json.loads(line)
                except (ValueError, UnicodeError):
                    warnings += 1
                    continue
                if not isinstance(entry, dict):
                    warnings += 1
                    continue
                if entry.get("status") == "verified" and entry.get("drive_id"):
                    recorded[entry["remote"]] = entry
        for item in canonical["files"]:
            prior = recorded.get(item["remote"], {})
            if all(prior.get(key) == item[key] for key in ("bytes", "sha256", "md5")):
                reused += 1
                continue
            if (root / "sync/STOP_DRIVE_INGEST").exists():
                raise IngestError("stopped", "Collection stop requested; unfinished catalog checkpoint retained")
            data = Path(item["path"]).read_bytes()
            if digest(data) != {key: item[key] for key in ("bytes", "sha256", "md5")}:
                raise ValueError("Catalog object changed before upload")
            drive.copy(Path(item["path"]), item["remote"])
            proof = drive.stat(item["remote"])
            verify_remote(proof, item)
            if not proof.get("ID"):
                raise IngestError("drive_verify", "Catalog verification has no Drive object ID")
            journal(receipt_path, {"status": "verified", "remote": item["remote"], "drive_id": proof["ID"],
                                   "bytes": item["bytes"], "md5": item["md5"], "sha256": item["sha256"], "verified_at": utc_now()})
            uploaded += 1
        if uploaded:
            journal(receipt_path, {"status": "checkpoint_complete", "manifest_remote": canonical["manifest_remote"],
                                   "completed_at": utc_now()})
    return {"uploaded_objects": uploaded, "reused_objects": reused, "manifest_remote": canonical["manifest_remote"],
            "upload_receipt_parse_warnings": warnings}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("prepare", "upload", "rebuild"))
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--queue", type=Path)
    ap.add_argument("--remote", default="etdrive:04 Audio")
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--rclone", default="rclone")
    ap.add_argument("--rclone-config", type=Path)
    args = ap.parse_args(argv)
    try:
        if args.command == "prepare":
            if not args.queue:
                ap.error("prepare requires --queue")
            result = prepare_catalog(args.root, args.queue, args.remote)
            print(json.dumps({key: result[key] for key in ("manifest_path", "manifest_remote", "counts", "changed_items", "new_snapshot",
                                                         "receipt_parse_warnings", "caption_receipt_parse_warnings")}, indent=2))
        else:
            path = args.manifest
            if path is None:
                folder = args.root / CATALOG_DIR
                path = catalog_path(folder, json.loads((folder / "current.json").read_text(encoding="utf-8"))["manifest"])
            if args.command == "rebuild":
                if not args.out:
                    ap.error("rebuild requires --out")
                ensure_outside_git(args.out.parent)
                data = csv_bytes(rebuild(path), FIELDS)
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_bytes(data)
                print(json.dumps({"out": str(args.out), "bytes": len(data)}))
            else:
                drive = Rclone(args.rclone, args.rclone_config, args.root / "sync/drive_ingest_cooldown.json")
                print(json.dumps(upload_catalog(upload_plan(args.root, path, args.remote), drive), indent=2))
    except IngestError as exc:
        print(f"{exc.kind}: {exc}", file=sys.stderr)
        return 75 if exc.kind in {"drive_cooldown", "drive_rate_limited"} else 130 if exc.kind == "stopped" else 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
