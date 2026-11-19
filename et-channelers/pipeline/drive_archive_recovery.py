"""Recover a native pair from an earlier Drive run using its original archive metadata."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

if __package__:
    from . import drive_ingest
else:
    import drive_ingest


def require(value, reason):
    if not value:
        raise ValueError(reason)


def named_object(remote, target, entry, proof):
    relative = drive_ingest.remote_relative(remote, target)
    require(isinstance(entry, dict) and entry.get("IsDir") is False
            and isinstance(entry.get("ID"), str) and entry["ID"], "Missing Drive file identity")
    name = PurePosixPath(relative).name
    require(entry.get("Name") == name and entry.get("Path") in (name, relative), "Drive result path mismatch")
    if entry["Path"] == name:
        require(entry.get("remote") == target, "Single-object stat needs its exact queried path")
    drive_ingest.verify_remote(entry, proof)


def recovered_record(row, remote, raw_metadata, metadata_local_path, audio_remote, audio_entry,
                     metadata_remote, metadata_entry):
    """Build a local record only when producer hashes, creator, format and both Drive objects agree.

    A batch readback supplies archive-relative paths. An individual stat must also record its full
    remote argument. The audio SHA-256 comes from its historical producer. Drive independently
    supplies the byte count, MD5 and file identity. No media needs to be transferred.
    """
    video, owner = row["video_id"], row["channel_dir"]
    require(drive_ingest.ID_RE.fullmatch(video) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", owner),
            "Invalid selected recording or creator")
    side = json.loads(raw_metadata)
    source, info, saved = side["source"], side["metadata"], side["archive_audio"]
    require(side.get("schema_version") == 1 and source.get("platform") == "youtube"
            and source.get("video_id") == video == info.get("id") == saved.get("video_id"),
            "Archived metadata identifies a different recording")
    queue = side.get("queue") or {}
    require(queue.get("channel_dir") == owner and queue.get("video_id") == video
            and info.get("channel_id") == row.get("expected_channel_id")
            and re.fullmatch(r"UC[A-Za-z0-9_-]{22}", str(info.get("channel_id", ""))),
            "Archived metadata identifies a different uploader")
    ext = info.get("ext")
    require(ext in drive_ingest.NATIVE_EXTENSIONS and saved.get("file_name") == f"{video}.{ext}"
            and saved.get("encoding") == "native audio; no re-encode" and info.get("vcodec") == "none"
            and info.get("acodec") not in ("none", "", None), "Missing native audio format evidence")
    require(type(saved.get("bytes")) is int and saved["bytes"] > 0
            and re.fullmatch(r"[0-9a-f]{32}", str(saved.get("md5", "")))
            and re.fullmatch(r"[0-9a-f]{64}", str(saved.get("sha256", ""))), "Missing historical audio hashes")
    if info.get("filesize") is not None:
        require(info["filesize"] == saved["bytes"], "Selected format size disagrees with archived audio")
    require(saved.get("remote") == audio_remote and drive_ingest.valid_recorded_remote(remote, row, ext, audio_remote),
            "Audio path disagrees with the historical metadata or selected creator")
    parent = audio_remote.rpartition("/")[0]
    require(metadata_remote == f"{parent}/{video}.info.json", "Metadata is outside its canonical pair")
    audio = {k: saved[k] for k in ("bytes", "md5", "sha256")}
    metadata = {"bytes": len(raw_metadata), "md5": hashlib.md5(raw_metadata).hexdigest(),
                "sha256": hashlib.sha256(raw_metadata).hexdigest()}
    named_object(remote, audio_remote, audio_entry, audio)
    named_object(remote, metadata_remote, metadata_entry, metadata)
    require(not saved.get("drive_id") or saved["drive_id"] == audio_entry["ID"], "Historical Drive identity mismatch")
    local = Path(metadata_local_path)
    require(not local.is_absolute() and ".." not in local.parts, "Expected a private relative metadata path")
    return {**row, **audio, "status": "metadata_ready", "url": source.get("url"),
            "path": "audio/" + drive_ingest.remote_relative(remote, audio_remote),
            "metadata": {**metadata, "path": local.as_posix(), "remote": metadata_remote},
            "remote": audio_remote, "source_ext": ext, "source_format_id": info.get("format_id"),
            "duration_s": info.get("duration"), "downloaded_at": side.get("captured_at"),
            "archive_recovery": {"origin": "archived_native_metadata", "original_tab": queue.get("tab"),
                                 "original_audio_sha256": saved["sha256"], "media_downloaded_this_recovery": False}}
