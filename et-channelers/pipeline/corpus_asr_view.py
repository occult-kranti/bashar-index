"""Private, versioned corpus views of verified local ASR ZIPs; no inference.

The English view is the concordance input. Multilingual original text remains
available separately; an English-original alias never invents a translation.
Offsets count Unicode codepoints in the unchanged archived transcript.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import io
import json
import math
from pathlib import Path
import re
import stat
import sys
import tempfile
import zipfile

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from . import common, corpus_caption_view, gpu_asr, gpu_asr_multilingual, ingestion_status
except ImportError:
    import common
    import corpus_caption_view
    import gpu_asr
    import gpu_asr_multilingual
    import ingestion_status

SCHEMA = 1
NORMALIZATION = "asr-preserved-codepoints-v1"
SHA = re.compile(r"[a-f0-9]{64}")
DATED_RUN = re.compile(r"asr-[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}")


def need(value, code):
    if not value:
        raise ValueError(code)


def _parts(path, receipt, *, paired_max_bytes=None):
    expected = receipt if receipt.get("artifact_kind") == "asr_bundle" else receipt.get("bundle", {})
    size = expected.get("bytes")
    limit=gpu_asr.MAX_RESULT_BYTES if paired_max_bytes is None else paired_max_bytes
    need(type(limit) is int and 0 < limit <= 256_000_000 and type(size) is int and 0 < size <= limit, "asr_bundle_size")
    with Path(path).open("rb") as source:
        raw = source.read(size + 1)
    need(len(raw) == size, "asr_bundle_size")
    paired = receipt.get("output_contract") == gpu_asr_multilingual.CONTRACT
    need(receipt.get("output_contract") in (None, gpu_asr_multilingual.CONTRACT), "unknown_asr_contract")
    verifier = gpu_asr_multilingual.verify_pair if paired else gpu_asr.verify_bundle
    # The existing verifiers accept paths, so give them an exact owned snapshot
    # rather than reopening a concurrently replaceable original ASR ZIP. This
    # bounded private temporary copy is removed after verification; no extraction.
    with tempfile.TemporaryDirectory(prefix="private-asr-view-") as folder:
        parent = Path(folder).resolve()
        need(parent.parent == Path(tempfile.gettempdir()).resolve()
             and parent.name.startswith("private-asr-view-"), "private_asr_snapshot_location")
        snapshot = parent / "bundle.zip"
        snapshot.write_bytes(raw)
        proof = verifier(snapshot, expected, max_bytes=paired_max_bytes) if paired and paired_max_bytes is not None else verifier(snapshot, expected)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for item in archive.infolist():
            mode = stat.S_IFMT(item.external_attr >> 16)
            need(not item.flag_bits & 1 and mode in (0, stat.S_IFREG)
                 and item.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED), "unsafe_asr_member")
        parts = {name: archive.read(name) for name in archive.namelist()}
    return paired, proof, parts


def _source_proof(proof):
    need(isinstance(proof, dict) and type(proof.get("bytes")) is int and proof["bytes"] > 0
         and SHA.fullmatch(proof.get("sha256", ""))
         and re.fullmatch(r"[a-f0-9]{32}", proof.get("md5", ""))
         and isinstance(proof.get("drive_id"), str) and bool(proof["drive_id"]), "asr_source_object_proof")
    return {key: proof[key] for key in ("bytes", "md5", "sha256", "drive_id")}


def _dated_binding(receipt, proof, parts, edition, publication, remote):
    """Bind the original dated worker format to the archived ZIP and recording."""
    p = proof["provenance"]
    archived_only = receipt.get("artifact_kind") == "asr_bundle"
    if archived_only:
        publication = receipt
    need(isinstance(edition, dict) and isinstance(publication, dict)
         and ingestion_status.asr_receipt_complete(publication, edition, remote), "dated_asr_drive_receipt")
    need(edition.get("channel_dir") == publication.get("channel_dir") and receipt.get("video_id") == p.get("source_video_id")
         and publication.get("video_id") == p.get("source_video_id"), "dated_asr_channel_video")
    for key in ("run_id", "source_lease_id", "metrics"):
        need(p.get(key) is not None and p[key] == receipt.get(key) == publication.get(key), "dated_asr_run_identity")
    for key in ("job_id", "model"):
        if not archived_only or key in publication:
            need(p.get(key) is not None and p[key] == receipt.get(key) == publication.get(key), "dated_asr_run_identity")
    model = p.get("model") or {}
    need(isinstance(model, dict) and model.get("repository") and SHA.fullmatch(model.get("model_sha256", ""))
         and re.fullmatch(r"[a-f0-9]{40}", model.get("revision", "")), "dated_asr_model")
    need((archived_only or receipt.get("status") == p.get("status")) and p.get("status") == "local_transcription_complete_unreviewed"
         and receipt.get("quality_state") == publication.get("quality_state") == "unreviewed_asr"
         and all(p["quality"].get(k) is False for k in
                 ("human_reference_available", "accuracy_claimed", "speech_coverage_validated", "host_guest_identity_assigned")),
         "dated_asr_quality")
    need(all(publication.get(k) == proof["bundle"][k] for k in ("bytes", "md5", "sha256")), "dated_asr_archive_binding")
    config = p["config"]
    # Preserve the writer's original JSON serialization for this outer hash.
    need(config.get("task") == "transcribe" and config.get("language") == "en", "dated_asr_config")
    for field, expected, error in (
        ("provenance_sha256", hashlib.sha256(parts["provenance.json"]).hexdigest(), "dated_asr_archive_binding"),
        ("config_sha256", hashlib.sha256(json.dumps(config, sort_keys=True, allow_nan=False).encode()).hexdigest(), "dated_asr_config"),
    ):
        if not archived_only or field in publication:
            need(receipt.get(field) == publication.get(field) == expected, error)
    audio, metadata = _source_proof(p["source_audio"]), _source_proof(p["source_metadata"])
    need(audio["drive_id"] != metadata["drive_id"] and audio["sha256"] == receipt.get("source_audio_sha256")
         and audio["drive_id"] == publication.get("source_audio_drive_id"), "dated_asr_source_proof")
    for field, expected in (("source_metadata_drive_id", metadata["drive_id"]), ("source_metadata_sha256", metadata["sha256"])):
        if not archived_only or field in publication:
            need(publication.get(field) == expected, "dated_asr_source_proof")
    duration = p["metrics"].get("audio_seconds")
    need(type(duration) in (int, float) and math.isfinite(duration) and duration > 0, "asr_audio_duration")
    return dict(p, channel_dir=edition["channel_dir"]), audio, metadata, duration


def _receipt_binding(receipt, proof, paired, edition=None, remote=ingestion_status.DEFAULT_REMOTE):
    p = proof["provenance"]
    fields = ("run_id", "job_id", "source_lease_id", "source_metadata", "model")
    if receipt.get("artifact_kind") == "asr_bundle":
        need(isinstance(edition, dict) and ingestion_status.asr_receipt_complete(receipt, edition, remote),
             "archived_asr_recording_receipt")
        need(receipt.get("quality_state") == "unreviewed_asr" and receipt.get("metrics") == p.get("metrics")
             and receipt.get("channel_dir") == p.get("channel_dir"), "archived_asr_provenance")
        if paired:
            need(receipt.get("text_variants") == p.get("text_variants"), "archived_asr_variants")
        need(receipt.get("source_audio_drive_id") == p["source_audio"].get("drive_id")
             and receipt.get("source_audio_sha256") == p["source_audio"].get("sha256"), "archived_asr_source_audio")
    else:
        need(receipt.get("status") == "local_transcription_complete_unreviewed", "incomplete_asr_receipt")
        fields += ("source_audio",)
    need(re.fullmatch(r"asr-[a-f0-9]{24}", p.get("run_id", ""))
         and re.fullmatch(r"[A-Za-z0-9_-]{11}", p.get("source_video_id", "")), "asr_run_video_identity")
    for key in fields:
        need(receipt.get(key) == p.get(key) and p.get(key) is not None, "asr_receipt_provenance_identity")
    need(receipt.get("video_id") == p["source_video_id"]
         and receipt.get("artifact_manifest_sha256") == proof["artifact_manifest_sha256"], "asr_receipt_manifest_identity")
    audio, metadata = _source_proof(p["source_audio"]), _source_proof(p["source_metadata"])
    need(audio["drive_id"] != metadata["drive_id"], "distinct_asr_source_objects")
    quality = p.get("quality", {})
    need(all(quality.get(k) is False for k in ("accuracy_claimed", "human_reviewed", "speech_coverage_validated", "host_guest_identity_assigned")),
         "asr_quality_claims")
    duration = p.get("metrics", {}).get("audio_seconds")
    need(type(duration) in (int, float) and math.isfinite(duration) and duration > 0, "asr_audio_duration")
    if not paired:
        identity = p.get("identity", {})
        need("asr-" + gpu_asr.fingerprint(identity)[:24] == p["run_id"]
             and all(identity.get(k) == p.get(v) for k, v in
                     (("video_id", "source_video_id"), ("audio", "source_audio"), ("metadata", "source_metadata"),
                      ("model", "model"), ("config", "config"), ("worker_sha256", "worker_sha256"),
                      ("environment_lock_sha256", "environment_lock_sha256"))), "asr_identity_provenance")
        need(p.get("config", {}).get("task") == "transcribe" and p["config"].get("language") == "en"
             and receipt.get("config_sha256") == gpu_asr.fingerprint(p["config"]), "english_asr_config")
    return p, audio, metadata, duration


def _edition_binding(record, p, audio, metadata):
    if record is None:
        return None
    need(record.get("status") in ("verified", "deleted")
         and record.get("video_id", record.get("associated_youtube_id")) == p["source_video_id"]
         and record.get("channel_dir") == p["channel_dir"], "asr_edition_identity")
    def object_proof(value):
        if "remote_proof" not in value:
            return _source_proof(value)
        local, remote = value["local_proof"], value["remote_proof"]
        need(all(local.get(k) == remote.get(k) for k in ("bytes", "md5")), "asr_edition_remote_proof")
        return _source_proof({**local, "drive_id": remote.get("drive_id")})
    need(object_proof(record.get("audio", record)) == audio, "asr_audio_edition_mismatch")
    need(object_proof(record.get("metadata", record.get("provenance", {}))) == metadata,
         "asr_metadata_edition_mismatch")
    return gpu_asr.fingerprint(record)


def _segments(document, text, language, duration, *, dated=False):
    need(document.get("language") == language and document.get("timebase") == "source_audio_seconds"
         and document.get("human_reviewed") is False and document.get("speaker_identity") == "unassigned",
         "asr_segment_schema")
    need(type(document.get("duration_seconds")) in (int, float)
         and math.isfinite(document["duration_seconds"]) and abs(document["duration_seconds"] - duration) <= 2,
         "asr_segment_duration")
    need(isinstance(text, str) and text.strip() and any(c.isalnum() for c in text), "asr_empty_text")
    rows = document.get("segments")
    need(isinstance(rows, list) and rows, "asr_missing_segments")
    previous_char, previous_time, ids = 0, -1, set()
    for row in rows:
        start, end, ident = row.get("char_start"), row.get("char_end"), row.get("id")
        need(type(ident) is int and ident >= 0 and ident not in ids, "asr_segment_id")
        ids.add(ident)
        need(type(start) is int and type(end) is int and previous_char <= start < end <= len(text)
             and not text[previous_char:start].strip() and text[start:end] == row.get("text"), "asr_codepoint_mapping")
        need(all(type(row.get(k)) in (int, float) and math.isfinite(row[k]) for k in ("start", "end"))
             and 0 <= row["start"] <= row["end"] <= duration + .5 and row["start"] >= previous_time, "asr_segment_times")
        previous_char, previous_time = end, row["start"]
        for word in row.get("words", []):
            a, b = word.get("char_start"), word.get("char_end")
            if dated and a is None and b is None:
                need(isinstance(word.get("word"), str) and bool(word["word"].strip()), "asr_word_text")
            else:
                need(type(a) is int and type(b) is int and start <= a < b <= end and text[a:b] == word.get("word"),
                     "asr_word_codepoint_mapping")
            need(all(type(word.get(k)) in (int, float) and math.isfinite(word[k]) for k in ("start", "end", "probability"))
                 and 0 <= word["start"] <= word["end"] <= duration + .5 and 0 <= word["probability"] <= 1, "asr_word_times")
    need(not text[previous_char:].strip(), "asr_unmapped_trailing_text")
    return rows


def asr_views(path, receipt, *, edition_receipt=None, drive_receipt=None, remote=ingestion_status.DEFAULT_REMOTE):
    """Return English and, for multilingual ZIPs, original-language views.

    This reads only the explicitly supplied local artifact and receipt. The
    existing verifiers execute on one bounded snapshot without GPU libraries.
    """
    paired, proof, parts = _parts(path, receipt)
    dated = not paired and DATED_RUN.fullmatch(proof["provenance"].get("run_id", "")) is not None
    if dated:
        p, audio, metadata, duration = _dated_binding(receipt, proof, parts, edition_receipt, drive_receipt, remote)
    else:
        p, audio, metadata, duration = _receipt_binding(receipt, proof, paired, edition_receipt, remote)
    edition_hash = _edition_binding(edition_receipt, p, audio, metadata)
    adapter_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    original_language = p["text_variants"]["original"]["language"] if paired else "en"
    variants = p["text_variants"] if paired else {"english": {"text_kind": "original_asr", "language": "en"}}
    views = {}
    for name, descriptor in variants.items():
        canonical = descriptor.get("same_as", name)
        prefix = canonical + "/" if paired else ""
        member = prefix + "segments.json"
        text = parts[prefix + "transcript.txt"].decode("utf-8")
        document = json.loads(parts[member])
        rows = _segments(document, text, descriptor["language"], duration, dated=dated)
        spans = [{"cue_index": index, "char_start": row["char_start"], "char_end": row["char_end"],
                  "source_segment_id": f"{member}:{row['id']}", "raw_segment_id": row["id"], "source_member": member,
                  "time_start": row["start"], "time_end": row["end"], "words": deepcopy(row.get("words", []))}
                 for index, row in enumerate(rows)]
        alias = name != canonical
        translated = descriptor["text_kind"] == "english_audio_translation"
        version = hashlib.sha256(f"private-asr-view-v{SCHEMA}|{proof['bundle']['sha256']}|{member}|{adapter_hash}".encode()).hexdigest()
        views[name] = {"schema_version": SCHEMA, "video_id": p["source_video_id"], "channel_dir": p["channel_dir"],
            "run_id": p["run_id"], "track_id": "asr:" + p["run_id"] + ":" + name,
            "variant": name, "canonical_variant": canonical, "alias_of_variant": canonical if alias else None,
            "source_kind": "english_audio_translation" if translated else "original_asr", "text_kind": descriptor["text_kind"],
            "language": descriptor["language"], "original_language": original_language, "translation_performed": translated,
            "translation_semantics_verified": False, "preferred_english_concordance_view": name == "english",
            "text_version_id": version, "bundle_sha256": proof["bundle"]["sha256"],
            "raw_sha256": hashlib.sha256(parts[member]).hexdigest(), "raw_text_sha256": hashlib.sha256(parts[prefix + "transcript.txt"]).hexdigest(),
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "normalization_version": NORMALIZATION,
            "text": text, "segments": spans, "raw_segments": deepcopy(document), "offset_unit": "unicode_codepoint",
            "source_timebase": "source_audio_seconds", "duration_seconds": duration,
            "known_cue_union_seconds": corpus_caption_view.timed_union(rows), "cue_time_kind": "model_estimated_segment_spans",
            "cues_without_end": 0, "word_times_are_model_estimates": True,
            "speech_coverage_verified": False, "accuracy_claimed": False, "human_reviewed": False, "speaker_attribution": None,
            "source_edition_id": "sha256:" + audio["sha256"], "source_audio_sha256": audio["sha256"],
            "source_audio": audio, "source_metadata": metadata, "edition_receipt_sha256": edition_hash,
            "artifact_manifest_sha256": proof["artifact_manifest_sha256"], "source_admission_sha256": p.get("source_admission_sha256"),
            "model": deepcopy(p["model"]), "compute_config": deepcopy(descriptor.get("config", p.get("config"))),
            "quality_state": "unreviewed_asr", "view_adapter_sha256": adapter_hash}
    return views


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Private archive root outside Git")
    parser.add_argument("--receipt", required=True, type=Path, help="Local ASR result receipt or the verified ASR Drive journal record")
    parser.add_argument("--bundle", type=Path, help="Pinned local ZIP copy; defaults to the receipt path")
    parser.add_argument("--edition-receipt", type=Path, help="Optional matching verified audio edition receipt")
    parser.add_argument("--drive-receipt", type=Path, help="Verified ASR upload receipt for early, dated run IDs")
    parser.add_argument("--variant", choices=("english", "original", "all"), default="english")
    args = parser.parse_args(argv)
    root = common.ensure_outside_git(args.root)
    def private(path):
        value = common.ensure_outside_git(path)
        need(value.is_relative_to(root), "asr_view_input_outside_private_root")
        return value
    receipt = gpu_asr.read_json(private(args.receipt))
    bundle_path = args.bundle or receipt.get("bundle", {}).get("path")
    if not bundle_path:
        parser.error("Supply the staged ZIP with --bundle for an archived ASR result")
    bundle = private(bundle_path)
    edition = gpu_asr.read_json(private(args.edition_receipt)) if args.edition_receipt else None
    publication = gpu_asr.read_json(private(args.drive_receipt)) if args.drive_receipt else None
    views = asr_views(bundle, receipt, edition_receipt=edition, drive_receipt=publication)
    need(args.variant == "all" or args.variant in views, "asr_variant_not_present")
    selected = views if args.variant == "all" else {args.variant: views[args.variant]}
    output = []
    for name, view in selected.items():
        folder = private(root / "analysis/asr_views" / view["video_id"] / view["run_id"])
        path = folder / (name + "-" + view["text_version_id"] + ".json")
        common.atomic_write_text(path, json.dumps(view, ensure_ascii=False, allow_nan=False) + "\n")
        output.append({"variant": name, "language": view["language"], "segments": len(view["segments"]),
                       "text_version_id": view["text_version_id"]})
    print(json.dumps({"video_id": receipt["video_id"], "private_views": output}))
    return output


if __name__ == "__main__":
    main()
