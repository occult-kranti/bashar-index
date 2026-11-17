"""Offline receipt bridge into publisher_variant_asr's existing leased worker.

Each cohort item supplies private_root, archive_receipt_path,
provenance_reference_path, accepted_metadata_path, mapping_path, feed_path,
audio_path and provenance_path. The last two are exact future input locations;
this module never downloads, decodes, runs inference, uploads or deletes files.
Use publisher_variant_asr prepare/run normally; its policy, leases, model pins,
full-duration checks and separate publisher result journal remain authoritative.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

try:
    from . import publisher_variant_asr as worker
except ImportError:
    import publisher_variant_asr as worker

PROFILE = "publisher-mirror-rss-english-source-v1"
KINDS = {"qualified_publisher_mirror_audio_variant", "publisher_mirror_audio_variant"}
HASH = re.compile(r"[0-9a-f]{64}\Z")
ENGLISH = re.compile(r"en(?:-[a-z0-9]+)*\Z", re.I)
ASSOCIATION_KEYS = ("provider", "watch_page_id", "associated_youtube_id", "channel_dir",
                    "association_method", "association_qualification", "exact_youtube_crossreference", "human_verified")


def need(condition, code):
    worker.need(condition, "mirror_" + code)


def path_in_root(value, root):
    path = Path(value).absolute()
    need(path.is_relative_to(root), "path_outside_private")
    for parent in (path, *path.parents):
        need(not parent.is_symlink() and not getattr(parent, "is_junction", lambda: False)(), "linked_path")
        if parent == root:
            break
    need(path.resolve().is_relative_to(root), "path_outside_private")
    return path.resolve()


def read_bytes(path, maximum):
    before = path.stat()
    need(0 < before.st_size <= maximum, "document_size")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    after = path.stat()
    need((before.st_size, before.st_mtime_ns, before.st_ino) ==
         (after.st_size, after.st_mtime_ns, after.st_ino) and len(raw) == before.st_size, "evidence_changed")
    return raw


def hashes(raw):
    return {"bytes": len(raw), "md5": hashlib.md5(raw).hexdigest(), "sha256": hashlib.sha256(raw).hexdigest()}


def json_file(path, maximum=8_000_000):
    raw = read_bytes(path, maximum)
    return json.loads(raw), hashes(raw)


def english(value):
    return isinstance(value, str) and ENGLISH.fullmatch(value) is not None


def source_proof(value):
    result = worker.proof(value)
    need(type(result["bytes"]) is int and ":" in result["remote"] and
         all(part not in {".", "..", ""} for part in result["remote"].split("/")), "source_proof")
    return result


def exact_link(value, video_id):
    try:
        url = urlsplit(value)
        query = parse_qs(url.query)
        need(url.scheme == "https" and not url.username and not url.password and url.port in (None, 443)
             and not url.fragment, "exact_source_link")
        need((url.hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"} and url.path == "/watch"
              and query.get("v") == [video_id]) or
             (url.hostname == "youtu.be" and url.path == "/" + video_id and "v" not in query), "exact_source_link")
    except (ValueError, TypeError):
        need(False, "exact_source_link")


def feed_evidence(raw, accepted, mapping_item):
    need(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "feed_entities")
    root = ET.fromstring(raw)
    channels = [x for x in root if x.tag == "channel"]
    need(len(channels) == 1, "feed_channel")
    channel = channels[0]
    languages = [x.text.strip() for x in channel if x.tag == "language" and x.text]
    need(len(languages) <= 1, "feed_language_ambiguous")
    code = languages[0] if languages else None
    feed = accepted["feed"]
    need(feed.get("language_scope") == "publisher_rss_channel" and code == feed.get("language")
         and code == feed.get("channel", {}).get("language"), "feed_language_binding")
    episode = accepted["episode"]
    matches = [x for x in channel if x.tag == "item" and x.findtext("guid") == episode.get("guid")]
    need(len(matches) == 1 and episode.get("guid") == mapping_item.get("episode_guid"), "feed_episode")
    enclosures = matches[0].findall("enclosure")
    need(len(enclosures) == 1, "feed_enclosure")
    enclosure = dict(enclosures[0].attrib)
    for key in ("url", "length", "type"):
        need(enclosure.get(key) == episode.get("audio", {}).get(key) ==
             mapping_item.get("source_audio_enclosure", {}).get(key), "feed_enclosure_binding")
    return code


def caption_decision(archive, parent):
    tracks = archive.get("caption_bundles") or ([archive["caption_bundle"]] if archive.get("caption_bundle") else [])
    need(isinstance(tracks, list), "caption_inventory")
    usable, ids = [], {archive["audio"]["drive_id"], archive["provenance"]["drive_id"]}
    for track in tracks:
        proof = source_proof(track)
        need(proof["remote"] == parent + "/Captions/" + proof["sha256"] + "/captions.zip" and
             proof["drive_id"] not in ids, "caption_proof")
        ids.add(proof["drive_id"])
        if english(track.get("language")) and track.get("usable_timed_text") is True:
            usable.append({**proof, "language": track["language"], "coverage": track.get("coverage"),
                           "language_basis": track.get("language_basis"), "track_language_verified": track.get("track_language_verified")})
    return {"inventory_state": archive.get("caption_state", "unknown"), "usable_english_bundles": usable,
            "speech_coverage_verified": False, "decision": "publisher_text_available_review_before_asr" if usable else "no_usable_saved_english_caption"}


def prepare_mirror_job(item, archive=None):
    """Return the old worker job shape, with explicit held/eligible status."""
    root = Path(item["private_root"]).absolute()
    need(root == root.resolve() and not root.is_symlink() and not getattr(root, "is_junction", lambda: False)(), "private_root")
    fields = ("archive_receipt_path", "provenance_reference_path", "accepted_metadata_path", "mapping_path", "feed_path", "audio_path", "provenance_path")
    paths = {key: path_in_root(item[key], root) for key in fields}
    need(paths["audio_path"] != paths["provenance_path"], "input_path_collision")
    saved, receipt_hash = json_file(paths["archive_receipt_path"])
    if archive is not None:
        need(saved == archive, "receipt_changed")
    archive = saved
    kind = archive.get("kind")
    need(archive.get("status") == "verified" and kind in KINDS, "archive_type")
    for flag in ("native_youtube_bytes", "changes_native_audio_count", "changes_native_asr_count", "changes_native_caption_count"):
        need(archive.get(flag) is False, "native_promotion")
    audio, provenance = source_proof(archive["audio"]), source_proof(archive["provenance"])
    need(audio["drive_id"] != provenance["drive_id"] and archive.get("variant_id") == audio["sha256"], "source_identity")
    channel, video = archive.get("channel_dir"), archive.get("associated_youtube_id")
    need(isinstance(channel, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", channel) and
         isinstance(video, str) and re.fullmatch(r"[A-Za-z0-9_-]{11}", video), "association_identity")
    parent = audio["remote"].rpartition("/")[0]
    need(parent.endswith(f"/{channel}/Videos/{video}/PublisherVariants/{audio['sha256']}") and
         provenance["remote"] == parent + "/provenance.json", "source_remote")
    metadata, observed = json_file(paths["provenance_reference_path"], 3_000_000)
    need(observed == {key: provenance[key] for key in observed}, "provenance_hash")
    need(metadata.get("artifact_kind") == kind and metadata.get("item_id") == archive.get("item_id") and
         metadata.get("accepted_api_sha256") == archive.get("accepted_api_sha256"), "provenance_identity")
    for flag in ("native_youtube_bytes", "changes_native_audio_count", "changes_native_asr_count", "changes_native_caption_count"):
        need(metadata.get(flag) is False, "provenance_native_promotion")
    need(all(metadata.get("audio", {}).get(k) == audio[k] for k in ("bytes", "md5", "sha256")), "audio_provenance")
    association = metadata.get("association", {})
    need(all(association.get(k) == archive.get(k) for k in ASSOCIATION_KEYS) and archive.get("human_verified") is False,
         "association_binding")
    method = archive.get("association_method")
    if method == "publisher_rss_exact_youtube_id":
        need(kind == "publisher_mirror_audio_variant" and archive.get("exact_youtube_crossreference") is True, "exact_association")
        need(association.get("original_youtube_link") == archive.get("original_youtube_link"), "exact_source_link")
        exact_link(archive.get("original_youtube_link"), video)
    else:
        need(method == "publisher_owner_title_date_duration" and kind == "qualified_publisher_mirror_audio_variant" and
             archive.get("exact_youtube_crossreference") is False, "qualified_association")
    need(metadata.get("recording_equivalence_verified") is False and archive.get("recording_equivalence_verified") is False,
         "edition_equivalence")
    duration = archive.get("actual_probe_duration_s")
    need(type(duration) in (int, float) and math.isfinite(duration) and duration > 0 and
         metadata.get("probe", {}).get("duration_seconds") == duration, "duration")
    accepted, accepted_hash = json_file(paths["accepted_metadata_path"])
    need(accepted_hash["sha256"] == archive["accepted_api_sha256"] and
         accepted.get("artifact_kind") == "accepted_official_publisher_rss_episode", "accepted_metadata")
    published = metadata.get("publisher_metadata", {})
    need(published.get("mapping_sha256") == accepted.get("mapping_sha256") and
         published.get("episode", {}).get("guid") == accepted.get("episode", {}).get("guid") and
         all(published.get("feed", {}).get(key) == accepted.get("feed", {}).get(key)
             for key in ("language", "language_scope", "sha256", "bytes")), "archived_publisher_evidence")
    mapping, mapping_hash = json_file(paths["mapping_path"])
    need(mapping_hash["sha256"] == accepted.get("mapping_sha256"), "mapping_hash")
    candidates = [x for x in mapping.get("items", []) if x.get("youtube_video_id") == video]
    need(len(candidates) == 1 and candidates[0].get("status") == "ready" and
         candidates[0].get("channel_dir") == channel, "mapping_item")
    mapped = candidates[0]
    need(accepted.get("association_evidence") == mapped, "accepted_mapping_binding")
    if method == "publisher_rss_exact_youtube_id":
        need(mapped.get("association_method") == "official_feed_item_exact_youtube_link" and
             mapped.get("exact_youtube_reference") == archive.get("original_youtube_link"), "mapping_source_link")
    else:
        need(mapped.get("association_method") in {"official_publisher_distinctive_title_date_duration_qualified_edition",
             "official_publisher_distinctive_full_title_date_duration"} and not mapped.get("exact_youtube_reference"), "mapping_qualification")
    feed_raw = read_bytes(paths["feed_path"], 8_000_000)
    feed_hash = hashes(feed_raw)
    need(feed_hash["sha256"] == accepted.get("feed", {}).get("sha256") and
         feed_hash["bytes"] == accepted["feed"].get("bytes"), "feed_hash")
    code = feed_evidence(feed_raw, accepted, mapped)
    caption = caption_decision(archive, parent)
    explicit_hold = any(container.get(key) is True for container in (accepted, mapped, metadata)
                        for key in ("nonlexical", "requires_language_review", "nonlexical_content", "requires_language_detection"))
    status = ("held_language_review" if explicit_hold else "pending_publisher_language_evidence" if not english(code)
              else "publisher_text_available_review_before_asr" if caption["usable_english_bundles"] else "eligible")
    bridge = {"profile": PROFILE, "worker_sha256": worker.sha(__file__), "accepted_metadata_sha256": accepted_hash["sha256"],
              "mapping_sha256": mapping_hash["sha256"], "feed_sha256": feed_hash["sha256"], "caption_availability": caption}
    language = {"code": code.lower(), "basis": "hash_bound_publisher_rss_channel", "scope": "publisher_rss_channel_declaration",
                "evidence_sha256": accepted_hash["sha256"], "feed_sha256": feed_hash["sha256"],
                "episode_language_independently_verified": False, "native_youtube_language_asserted": False} if english(code) else None
    return {"variant_id": audio["sha256"], "status": status, "audio": audio, "provenance": provenance,
            **{key: str(paths[key]) for key in ("audio_path", "provenance_path", "provenance_reference_path", "archive_receipt_path")},
            "provenance_data": metadata, "archive_receipt_sha256": receipt_hash["sha256"], "receipt_selector": None,
            "language_evidence_path": str(paths["accepted_metadata_path"]), "language_evidence_sha256": accepted_hash["sha256"],
            "language": language, "source_kind": "publisher_audio_variant", "associated_youtube_id": video, "channel_dir": channel,
            "measured_duration_seconds": duration, "publisher_declared_duration_seconds": archive.get("provider_declared_duration_s"),
            "episode_guid": accepted["episode"]["guid"], "association": {**association, "recording_equivalence_verified": False,
            "source_artifact_kind": kind, "source_adapter": bridge}, "native_youtube_bytes": False}
