"""Preserve one conflicting canonical metadata object before a caller replaces it.

The caller holds the collector lock. This helper never uploads/deletes media or
new metadata. A matching archived audio object and verified local pair are
required. Interrupted moves recover only from the durable exact-object intent.
"""
import json
from pathlib import Path
import re

try:
    from . import drive_ingest as storage
except ImportError:  # private isolated runtime imports the pinned files directly
    import drive_ingest as storage


def _need(condition, reason):
    if not condition:
        raise storage.IngestError("metadata_snapshot", reason)


def _proof(value):
    _need(isinstance(value, dict) and not value.get("IsDir"), "Metadata object is missing or is a directory")
    hashes = {str(k).lower(): str(v).lower() for k, v in (value.get("Hashes") or {}).items()}
    size, identity, md5 = value.get("Size"), value.get("ID"), hashes.get("md5", "")
    _need(isinstance(size, int) and not isinstance(size, bool) and size > 0 and
          isinstance(identity, str) and bool(identity) and re.fullmatch(r"[a-f0-9]{32}", md5),
          "Exact Drive identity, positive size and MD5 are required")
    return {"drive_id": identity, "bytes": size, "md5": md5}


def _same(value, expected):
    return _proof(value) == expected


def _unique_stat(drive, remote):
    """One filtered, nonrecursive parent read also detects duplicate Drive names."""
    parent, _, name = remote.rpartition("/")
    try:
        result = drive.execute(["lsjson", parent, "--max-depth", "1", "--files-only",
                                "--hash-type", "MD5", "--include", "/" + name,
                                "--no-modtime", "--no-mimetype", "--disable", "ListR",
                                *drive.RETRY_FLAGS], 300, "exact metadata uniqueness read")
    except storage.IngestError as error:
        if error.kind == "drive_not_found":
            return None
        raise
    try:
        rows = json.loads(result.stdout)
        _need(isinstance(rows, list), "Invalid exact metadata listing")
        _need(all(isinstance(r, dict) and r.get("Name", r.get("Path")) == name for r in rows),
              "Unexpected metadata listing entry")
        _need(len(rows) <= 1, "Duplicate metadata names require review")
        return rows[0] if rows else None
    except (ValueError, TypeError) as error:
        raise storage.IngestError("metadata_snapshot", "Invalid exact metadata listing") from error


def preserve_conflicting_metadata(root, record, drive, *, observed_audio, observed_metadata, trusted=None):
    """Return preserved lineage or None if metadata already matches.

    ``trusted`` may contain fingerprints returned by the caller's current local
    pair validation; otherwise local hashes are checked here. The existing audio
    proof must match this pair. All original Drive objects retain their IDs.
    """
    root = Path(root).resolve()
    ident, channel, tab = (record.get(k, "") for k in ("video_id", "channel_dir", "tab"))
    _need(re.fullmatch(r"[A-Za-z0-9_-]{11}", ident) is not None and
          re.fullmatch(r"[a-z0-9][a-z0-9-]*", channel) is not None and tab in storage.SOURCE_FOLDERS,
          "Invalid canonical source identity")
    audio = storage.local_path(root, record["path"])
    meta = record.get("metadata", {})
    metadata = storage.local_path(root, meta.get("path", ""))
    _need(audio.name == ident + audio.suffix and audio.suffix in {".m4a", ".webm"} and
          metadata.name == ident + ".info.json" and audio.parent == metadata.parent,
          "Local source pair is not canonical")
    suffix = f"/{channel}/{storage.SOURCE_FOLDERS[tab]}/{audio.name}"
    remote = record.get("remote", "")
    _need(remote.endswith(suffix) and ":" in remote[:-len(suffix)], "Noncanonical audio destination")
    expected_meta = remote.rpartition("/")[0] + "/" + metadata.name
    _need(meta.get("remote") == expected_meta, "Metadata destination differs from the exact audio item")
    storage.validate_local(audio, record, (trusted or {}).get("audio"))
    storage.validate_local(metadata, meta, (trusted or {}).get("metadata"))
    audio_proof = _proof(observed_audio)
    storage.verify_remote(observed_audio, record)
    # Text inventories are independently versioned; a replacement cannot silently
    # change the source metadata beneath an already verified caption inventory.
    caption = storage.load_state(root / "sync/drive_caption_manifest.jsonl").get(ident, {})
    _need(not any(t.get("status") in {"verified", "deleted"} and t.get("bundle", {}).get("drive_id")
                  for t in caption.get("tracks", [])), "Verified caption dependencies require explicit reconciliation")
    journal = root / "sync/native_metadata_lineage_manifest.jsonl"
    previous = storage.load_state(journal).get(ident, {})
    recovery = bool(previous.get("kind") == "native_metadata_snapshot_preservation" and
                    previous.get("original", {}).get("remote") == expected_meta and
                    previous.get("new_canonical_expected", {}).get("sha256") == meta.get("sha256") and
                    previous.get("audio_proof") == audio_proof)
    if observed_metadata is not None:
        old = _proof(observed_metadata)
        _need(old["drive_id"] != audio_proof["drive_id"], "Audio and metadata identities are not distinct")
        if old["bytes"] == meta["bytes"] and old["md5"] == meta["md5"].lower():
            return None
    else:
        _need(recovery, "Missing metadata has no durable preservation intent")
        old = {k: previous["original"][k] for k in ("drive_id", "bytes", "md5")}
    snapshot = expected_meta.rpartition("/")[0] + f"/{ident}/MetadataSnapshots/{old['md5']}.info.json"
    preserved = _unique_stat(drive, snapshot)
    current = _unique_stat(drive, expected_meta)
    if preserved is not None:
        _need(recovery and previous.get("snapshot_remote") == snapshot and _same(preserved, old) and current is None,
              "Existing snapshot or ambiguous move requires review")
    else:
        _need(current is not None and _same(current, old), "Canonical metadata changed before preservation")
        intent = {"schema_version": 1, "kind": "native_metadata_snapshot_preservation", "video_id": ident,
                  "status": "move_intent", "created_at": storage.utc_now(),
                  "original": dict(old, remote=expected_meta), "snapshot_remote": snapshot,
                  "new_canonical_expected": dict(meta), "audio_proof": audio_proof,
                  "audio_not_modified": True, "human_reviewed": False}
        storage.journal(journal, intent)
        # An error after a successful move leaves this intent for the next call;
        # no automatic retry or replacement is performed here.
        drive.execute(["moveto", expected_meta, snapshot, "--immutable", "--no-traverse",
                       "--retries", "1", "--low-level-retries", "1", "--contimeout", "15s",
                       "--timeout", "60s", "--tpslimit", "2", "--tpslimit-burst", "1"],
                      300, "exact metadata preservation move")
        preserved = _unique_stat(drive, snapshot)
        _need(preserved is not None and _same(preserved, old), "Preserved metadata identity or hash differs")
        previous = intent
    lineage = dict(previous, status="old_metadata_preserved", preserved_at=storage.utc_now(),
                   preserved=dict(old, remote=snapshot, original_drive_id_preserved=True))
    storage.journal(journal, lineage)
    return lineage
