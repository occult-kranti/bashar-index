"""Build a private, offset-addressable text view from one verified English YouTube caption ZIP.

The normalized cue order and repeated text are retained. A union of timed cues measures
caption display time only. Each view retains the raw source artifact and parser identities.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import stat
import zipfile
from pathlib import Path

try:
    from . import common, drive_ingest, ingestion_status, youtube_captions
except ImportError:
    import common
    import drive_ingest
    import ingestion_status
    import youtube_captions


MAX_ARCHIVE = 32_000_000
MAX_EXPANDED = 64_000_000
SCHEMA = 1


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def members(path, expected, extension=None, *, manifest=False):
    """Read a bounded, pinned snapshot. No extraction to the filesystem."""
    if type(expected.get("bytes")) is not int or not 0 < expected["bytes"] <= MAX_ARCHIVE:
        raise ValueError("Unsupported caption archive size")
    with Path(path).open("rb") as source:
        raw = source.read(expected["bytes"] + 1)
    if (len(raw) != expected["bytes"] or sha256(raw) != expected["sha256"]
            or hashlib.md5(raw).hexdigest() != expected["md5"]):
        raise ValueError("Local caption archive differs from the verified Drive object")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        if extension is None:
            candidates = set(archive.namelist()) & {"raw.vtt", "raw.json3"}
            if len(candidates) != 1:
                raise ValueError("Missing or ambiguous raw caption archive member")
            extension = candidates.pop().split(".", 1)[1]
        names = {"raw." + extension, "provenance.json", "segments.json", "transcript.txt"}
        if manifest:
            names.add("manifest.json")
        if (len(infos) != len(names) or set(archive.namelist()) != names
                or sum(info.file_size for info in infos) > MAX_EXPANDED):
            raise ValueError("Unexpected caption archive members or expanded size")
        result = {}
        for info in infos:
            mode = stat.S_IFMT(info.external_attr >> 16)
            if (info.flag_bits & 1 or mode not in {0, stat.S_IFREG}
                    or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}):
                raise ValueError("Unsupported caption member")
            with archive.open(info) as member:
                content = member.read(info.file_size + 1)
            if len(content) != info.file_size:
                raise ValueError("Caption member length mismatch")
            result[info.filename] = content
    return result


def text_content(parts, extension, raw_proof, normalization_version=None):
    """Reproduce the saved transcript from the pinned source, retaining original cue locators."""
    original = parts["raw." + extension]
    if (len(original) != raw_proof.get("bytes") or sha256(original) != raw_proof.get("sha256")
            or hashlib.md5(original).hexdigest() != raw_proof.get("md5")):
        raise ValueError("Raw caption source hash mismatch")
    source_indices = []
    normalized = youtube_captions.normalize_caption(original, extension, source_indices=source_indices)
    if (json.loads(parts["segments.json"]) != normalized or normalized["text"].encode() != parts["transcript.txt"]
            or normalization_version is not None and normalization_version != normalized["normalization_version"]):
        raise ValueError("Caption text and cues must reproduce from the archived raw source")
    spans, cursor = [], 0
    for number, (cue, source_index) in enumerate(zip(normalized["segments"], source_indices, strict=True)):
        end = cursor + len(cue["text"])
        spans.append({"cue_index": number, "char_start": cursor, "char_end": end,
                      "source_segment_id": f"{extension}:{source_index}",
                      "time_start": cue["start"], "time_end": cue["end"]})
        cursor = end + 1
    return {"raw_sha256": raw_proof["sha256"], "text_sha256": sha256(parts["transcript.txt"]),
            "normalization_version": normalized["normalization_version"], "text": normalized["text"],
            "segments": spans, "offset_unit": "unicode_codepoint",
            "known_cue_union_seconds": timed_union(normalized["segments"]),
            "cues_without_end": sum(c["time_end"] is None for c in spans), "speech_coverage_verified": False,
            "speaker_attribution": None}


def timed_union(segments):
    """Known display time, excluding cues with absent ends. Preserve unknown exposure."""
    spans = []
    for segment in segments:
        start, end = segment["start"], segment["end"]
        if type(start) not in (int, float) or not math.isfinite(start) or start < 0:
            raise ValueError("Invalid cue start time")
        if end is None:
            continue
        if type(end) not in (int, float) or not math.isfinite(end) or end < start:
            raise ValueError("Invalid cue end time")
        spans.append((start, end))
    if not spans:
        return None
    total = 0.0
    current_end = 0.0
    for start, end in sorted(spans):
        total += max(0.0, end - max(start, current_end))
        current_end = max(current_end, end)
    return total


def caption_view(path, record, track_id, *, remote=ingestion_status.DEFAULT_REMOTE):
    video = record.get("video_id")
    if (not isinstance(video, str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video)
            or record.get("policy") != drive_ingest.CAPTION_POLICY):
        raise ValueError("Missing caption source identity or policy")
    tracks = [t for t in record.get("tracks", []) if t.get("track_id") == track_id]
    if len(tracks) != 1 or not drive_ingest.caption_track_verified(tracks[0], record, remote):
        raise ValueError("A unique verified caption track is required")
    track = tracks[0]
    extensions = {track[k] for k in ("ext", "raw_format") if track.get(k)}
    if len(extensions) != 1 or not extensions <= {"json3", "vtt"}:
        raise ValueError("Ambiguous or unavailable raw caption format")
    extension = extensions.pop()
    kind, language = track.get("kind"), track.get("language")
    if (kind not in {"published", "automatic_original"} or not isinstance(language, str)
            or not re.fullmatch(r"en(?:-[a-z0-9]+)*", language, re.I)
            or track.get("machine_translated") is not False):
        raise ValueError("Expected an original English or regional English track")
    bundle = track["bundle"]
    parts = members(path, bundle, extension)
    provenance = json.loads(parts["provenance.json"])
    identity = {"policy": drive_ingest.CAPTION_POLICY, "provider": "youtube", "video_id": video,
                "track_id": track_id, "kind": kind, "language": language, "machine_translated": False}
    if any(provenance.get(key) != value for key, value in identity.items()):
        raise ValueError("Caption provenance disagrees with the verified track")
    raw_formats = {provenance[k] for k in ("ext", "raw_format") if provenance.get(k)}
    if raw_formats != {extension}:
        raise ValueError("Stored caption format differs from the outer receipt")
    if type(provenance.get("normalization_version")) is not int:
        raise ValueError("Missing normalization version in caption provenance")
    content = text_content(parts, extension, provenance.get("raw", {}), provenance["normalization_version"])
    return {"schema_version": SCHEMA, "video_id": video, "channel_dir": record["channel_dir"],
            "track_id": track_id, "source_kind": kind, "language": language,
            "text_version_id": sha256(f"native-caption-view-v{SCHEMA}|{bundle['sha256']}".encode()),
            "bundle_sha256": bundle["sha256"], **content}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Private archive root")
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--track-id", required=True)
    parser.add_argument("--bundle", type=Path, required=True, help="Local copy of the verified caption ZIP")
    args = parser.parse_args(argv)
    root = common.ensure_outside_git(args.root)
    records = ingestion_status.latest_records(root / "sync/drive_caption_manifest.jsonl")
    view = caption_view(args.bundle, records.get(args.video_id, {}), args.track_id)
    folder = common.ensure_outside_git(root / "analysis" / "caption_views" / args.video_id)
    if not folder.is_relative_to(root):
        raise ValueError("Caption view destination leaves the private archive")
    path = folder / (view["text_version_id"] + ".json")
    common.atomic_write_text(path, json.dumps(view, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"video_id": args.video_id, "track_id": args.track_id,
                      "cues": len(view["segments"]), "text_version_id": view["text_version_id"]}))


if __name__ == "__main__":
    main()
