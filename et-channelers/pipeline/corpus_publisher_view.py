"""Build a private English caption view for the publisher audio edition that supplied its timebase."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

if __package__:
    from . import collection_coverage, common, corpus_caption_view as native, ingestion_status as status, publisher_mirror
else:
    import collection_coverage, common, corpus_caption_view as native, ingestion_status as status, publisher_mirror


def verified_track(record, row, bundle_hash, remote=status.DEFAULT_REMOTE):
    video, creator = row["video_id"], row["channel_dir"]
    folder = {"videos": "Videos", "shorts": "Shorts", "streams": "Streams"}.get(row.get("tab"))
    if (not folder or not status.record_row(row) or record.get("schema_version") != 1 or record.get("status") != "verified"
            or record.get("associated_youtube_id") != video or record.get("channel_dir") != creator
            or record.get("source_tab", record.get("tab", row["tab"])) != row["tab"]
            or any(record.get(k) is not False for k in publisher_mirror.NATIVE_FLAGS)):
        raise ValueError("Publisher edition does not match the selected recording")
    method = record.get("association_method")
    if method == "publisher_rss_exact_youtube_id" and record.get("exact_youtube_crossreference") is True:
        publisher_mirror.exact_youtube_link(record.get("original_youtube_link"), video)
    elif method != "publisher_owner_title_date_duration" or record.get("exact_youtube_crossreference") is not False:
        raise ValueError("Unknown recording association")
    if record.get("kind") != publisher_mirror.kind_for(record):
        raise ValueError("Publisher recording association type disagrees with receipt")
    audio, metadata = record.get("audio"), record.get("provenance")
    tracks = record.get("caption_bundles") or [record.get("caption_bundle")]
    matches = [t for t in tracks if isinstance(t, dict) and t.get("sha256") == bundle_hash]
    if len(matches) != 1 or not all(status.publisher_object_proof(obj) for obj in (audio, metadata, matches[0])):
        raise ValueError("Expected one verified publisher caption bundle and its two source objects")
    track = matches[0]
    parent = f"{remote}/{creator}/{folder}/{video}/PublisherVariants/{audio['sha256']}"
    if (audio["sha256"] != record.get("variant_id") or len({obj["drive_id"] for obj in (audio, metadata, track)}) != 3
            or not re.fullmatch(re.escape(parent) + r"/publisher-audio\.(?:mp3|m4a|aac|ogg|opus|flac|webm)", audio["remote"])
            or metadata["remote"] != parent + "/provenance.json"
            or track["remote"] != f"{parent}/Captions/{bundle_hash}/captions.zip"
            or track.get("usable_timed_text") is not True):
        raise ValueError("Publisher caption and recording are in different editions")
    return track


def publisher_view(path, record, row, bundle_hash, *, remote=status.DEFAULT_REMOTE):
    track = verified_track(record, row, bundle_hash, remote)
    video, creator = row["video_id"], row["channel_dir"]
    audio, method = record["audio"], record["association_method"]
    parts = native.members(path, track, manifest=True)
    manifest = json.loads(parts.pop("manifest.json"))
    if (not isinstance(manifest, dict) or manifest.keys() != parts.keys()
            or any(manifest[name].get("bytes") != len(data) or manifest[name].get("sha256") != native.sha256(data)
                   or "md5" in manifest[name] and manifest[name]["md5"] != hashlib.md5(data).hexdigest()
                   for name, data in parts.items())):
        raise ValueError("Publisher caption member manifest mismatch")
    provenance = json.loads(parts["provenance.json"])
    buzzsprout = record.get("provider") == provenance.get("provider") == "Buzzsprout"
    language = provenance.get("language", track.get("language") if buzzsprout else None)
    raw_format, = [name.split(".", 1)[1] for name in parts if name.startswith("raw.")]
    if (not isinstance(language, str) or not re.fullmatch(r"en(?:-[A-Za-z0-9]+)*", language, re.I)
            or language.lower() != track.get("language", "").lower()
            or provenance.get("raw_format", raw_format) != raw_format
            or provenance.get("source_audio_sha256") != audio["sha256"]):
        raise ValueError("Publisher caption language, raw format or source audio mismatch")
    if provenance.get("kind") == "publisher_english_caption":
        caption_kind = provenance.get("caption_kind")
        evidence = provenance.get("language_evidence") or {}
        raw_proof = provenance.get("raw_caption") or provenance.get("raw_source_proof")
        metadata_hash = provenance.get("accepted_api_sha256", provenance.get("accepted_metadata_sha256"))
        if (not re.fullmatch("[a-f0-9]{64}", metadata_hash or "") or metadata_hash != record.get("accepted_api_sha256")
                or provenance.get("watch_page_id", record.get("watch_page_id")) != record.get("watch_page_id")):
            raise ValueError("Publisher caption metadata belongs to a different recording")
    elif record.get("provider") == "Substack" and provenance.get("original") is True:
        # This earlier format used the publisher article URL in its source field.
        article = urlsplit(provenance.get("source", ""))
        if (article.scheme != "https" or not (article.hostname or "").endswith(".substack.com")
                or provenance.get("native_youtube_caption") is not False
                or not record.get("watch_page_id") or provenance.get("watch_page_id") != record["watch_page_id"]):
            raise ValueError("Substack caption lacks its publisher and episode identity")
        caption_kind, evidence, raw_proof = track.get("kind"), {"publisher_marks_original": True}, provenance.get("raw")
    elif buzzsprout:
        # The episode's RSS language is recorded on the track. The host does
        # not say whether a person or a model prepared the VTT.
        guid = provenance.get("publisher_episode_guid")
        tag = track.get("provider_language_key", "")
        if (not re.fullmatch(r"Buzzsprout-[0-9]+", guid or "")
                or guid != "Buzzsprout-" + str(record.get("watch_page_id"))
                or not str(record.get("item_id", "")).endswith("-" + guid)
                or not re.fullmatch(r"en(?:-[A-Za-z0-9]+)*", tag, re.I)
                or not provenance.get("prior_standalone_drive_item")
                or not re.fullmatch(r"[0-9a-f]{64}", provenance.get("prior_standalone_bundle_sha256") or "")
                or provenance.get("full_speech_coverage_verified") is not False or raw_format != "vtt"):
            raise ValueError("Buzzsprout caption lacks its original English track and episode identity")
        caption_kind = "publisher_provided_unspecified"
        evidence = {"provider_language_key": tag, "publisher_episode_guid": guid, "authorship": "undeclared"}
        raw_proof = provenance.get("vtt")
    else:
        raise ValueError("Unrecognized publisher caption provenance")
    if (not isinstance(raw_proof, dict) or caption_kind not in {"published", "automatic_original", "publisher_provided_unspecified"}
            or track.get("kind", caption_kind) != caption_kind):
        raise ValueError("Publisher caption origin or original file fingerprint is missing")
    content = native.text_content(parts, raw_format, raw_proof, provenance.get("normalization_version"))
    if track.get("coverage", {}).get("segment_count", len(content["segments"])) != len(content["segments"]):
        raise ValueError("Publisher caption count disagrees with its receipt")
    return {"schema_version": 1, "video_id": video, "channel_dir": creator, "source_kind": "publisher_english_caption",
            "track_id": track.get("provider_language_key") or caption_kind + "." + language, "caption_kind": caption_kind,
            "language": language, "language_evidence": evidence, "bundle_sha256": bundle_hash,
            "text_version_id": native.sha256(("publisher-caption-v1|" + audio["sha256"] + "|" + bundle_hash).encode()),
            "source_edition_id": "sha256:" + audio["sha256"], "source_audio_sha256": audio["sha256"],
            "edition_receipt_sha256": publisher_mirror.sha(publisher_mirror.encoded(record)),
            "source_timebase": "publisher_audio_seconds", "recording_association_method": method, **content}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("root", "selection", "bundle"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--bundle-sha256", required=True)
    args = parser.parse_args(argv)
    root = common.ensure_outside_git(args.root)
    bundle = common.ensure_outside_git(args.bundle)
    if not bundle.is_relative_to(root):
        parser.error("Use a staged publisher bundle under the private archive")
    rows, _, _ = collection_coverage.mixed_selection(args.selection, {})
    row, = [r for r in rows if r["video_id"] == args.video_id]
    for record in reversed(common.read_jsonl(root / "sync/publisher_mirror_manifest.jsonl")):
        tracks = record.get("caption_bundles") or [record.get("caption_bundle")]
        if record.get("associated_youtube_id") != args.video_id or not any(
                isinstance(t, dict) and t.get("sha256") == args.bundle_sha256 for t in tracks):
            continue
        view = publisher_view(bundle, record, row, args.bundle_sha256)
        out = common.ensure_outside_git(root / "analysis/publisher_views" / args.video_id / (view["text_version_id"] + ".json"))
        if not out.is_relative_to(root):
            parser.error("The publisher view destination is outside the private archive")
        common.atomic_write_text(out, json.dumps(view, allow_nan=False, ensure_ascii=False) + "\n")
        print(json.dumps({"video_id": args.video_id, "text_version_id": view["text_version_id"], "cues": len(view["segments"])}))
        return
    parser.error("Missing verified publisher caption receipt")


if __name__ == "__main__":
    main()
