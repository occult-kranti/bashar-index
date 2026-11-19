"""Read complete English podcast documents matched to numbered regular-video episodes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

if __package__:
    from . import common, ingestion_status as status
    from .interview_guest_discovery import normalize_title, numbered_episode_title
else:
    import common, ingestion_status as status
    from interview_guest_discovery import normalize_title, numbered_episode_title


KIND = "numbered_publisher_episode_transcript"
UUID = re.compile(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}")
SHA = re.compile(r"[a-f0-9]{64}")


def valid_record(record, row, remote):
    if not isinstance(record, dict) or not isinstance(row, dict):
        return False
    video, creator, owner = record.get("video_id"), record.get("channel_dir"), record.get("channel_id")
    doc, meta = record.get("proof"), record.get("provenance")
    if (not status.record_row(row) or row.get("video_id") != video or row.get("channel_dir") != creator
            or row.get("tab") != "videos" or not isinstance(owner, str) or not re.fullmatch(r"UC[A-Za-z0-9_-]{22}", owner)
            or any(row.get(k) and row[k] != owner for k in ("channel_id", "expected_channel_id"))
            or not status.publisher_object_proof(doc) or not status.publisher_object_proof(meta)
            or doc["drive_id"] == meta["drive_id"] or not 0 < doc["bytes"] <= 2_000_000):
        return False
    episode, show = record.get("episode_guid"), record.get("show_id")
    if not all(isinstance(key, str) and UUID.fullmatch(key) for key in (episode, show)):
        return False
    title = record.get("youtube_title")
    if not isinstance(title, str) or not isinstance(record.get("episode_title"), str):
        return False
    suffix = numbered_episode_title(title)
    if (not suffix or (row.get("title") and normalize_title(row["title"]) != normalize_title(title))
            or suffix[0] != normalize_title(record["episode_title"])):
        return False
    for value, stated in zip(suffix[1:], (record.get("season"), record.get("episode_number"))):
        if not isinstance(stated, str) or not re.fullmatch(r"[0-9]{1,5}", stated) or value != int(stated):
            return False
    times = record.get("youtube_duration_s"), record.get("episode_duration_s")
    word_count, hits = record.get("words"), record.get("english_common_words")
    return (record.get("schema_version") == 1 and record.get("kind") == KIND and record.get("status") == "verified"
            and record.get("provider") == "Riverside" and record.get("tab") == "videos"
            and record.get("source_url") == f"https://hosting-media.riverside.com/media/podcasts/{show}/episodes/{episode}/transcripts.txt"
            and isinstance(record.get("feed_url"), str)
            and bool(re.fullmatch(r"https://api\.riverside\.fm/hosting/[A-Za-z0-9_-]+\.rss", record["feed_url"]))
            and all(isinstance(record.get(k), str) and SHA.fullmatch(record[k]) for k in ("selection_sha256", "feed_sha256"))
            and all(type(n) is int and n > 0 for n in times) and abs(times[0] - times[1]) <= 2
            and (not row.get("duration_s") or row["duration_s"] == times[0])
            and doc.get("remote") == f"{remote}/{creator}/Videos/{video}/PublisherTranscripts/{doc['sha256']}/publisher-transcript.en.txt"
            and meta.get("remote") == f"{remote}/{creator}/Metadata/Batches/{meta['sha256']}/catalog-and-publisher-text.json"
            and record.get("publisher_declares_transcript") is True and record.get("mime_type") == "text/plain"
            and record.get("language") == "en" and str(record.get("show_language")).lower().split("-")[0] == "en"
            and type(record.get("paragraphs")) is int and record["paragraphs"] > 0
            and type(word_count) is int and word_count > 0 and type(hits) is int and max(1, .12*word_count) <= hits <= word_count
            and all(record.get(k) is False for k in ("timed", "recording_equivalence_verified", "native_youtube_alignment_verified"))
            and "source_audio_sha256" in record and record["source_audio_sha256"] is None)


def input_rows(root, frame, remote):
    targets = {r["video_id"]:r for r in frame}
    seen = set()
    for record in common.read_jsonl(Path(root)/"sync/publisher_feed_transcripts.jsonl"):
        if not isinstance(record, dict) or not isinstance(record.get("video_id"), str):
            continue
        row = targets.get(record["video_id"])
        if not valid_record(record, row, remote):
            continue
        key = record["video_id"], record["episode_guid"], record["proof"]["sha256"]
        if key not in seen:
            seen.add(key)
            yield {"kind":KIND, "row":row, "record":record, "proof":record["proof"], "track_id":KIND+":en"}


def text_view(path, job, remote):
    if __package__:
        from .corpus_untimed_publisher_view import ENGLISH_WORDS, _plain_paragraphs
    else:
        from corpus_untimed_publisher_view import ENGLISH_WORDS, _plain_paragraphs
    record, row, proof = job["record"], job["row"], job["proof"]
    if job["kind"] != KIND or not valid_record(record, row, remote) or proof != record["proof"]:
        raise ValueError("Unbound publisher episode document")
    with Path(path).open("rb") as stream:
        raw = stream.read(proof["bytes"]+1)
    if (len(raw) != proof["bytes"] or hashlib.sha256(raw).hexdigest() != proof["sha256"]
            or hashlib.md5(raw).hexdigest() != proof["md5"]):
        raise ValueError("Publisher episode document differs from its archive receipt")
    text = raw.decode("utf-8")
    words = re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())
    paragraphs = _plain_paragraphs(text)
    if (len(paragraphs) != record["paragraphs"] or len(words) != record["words"]
            or sum(word in ENGLISH_WORDS for word in words) != record["english_common_words"]):
        raise ValueError("Publisher document paragraph or language evidence changed")
    member = "publisher-transcript.en.txt"
    segments = []
    cursor = 0
    for index, (ordinal, value) in enumerate(paragraphs):
        start = text.index(value, cursor)
        cursor = start + len(value)
        segments.append({"paragraph_index":index, "source_paragraph_index":ordinal, "source_member":member,
                         "source_segment_id":f"{member}:paragraph:{ordinal}", "char_start":start, "char_end":cursor,
                         "time_start":None, "time_end":None})
    edition = "publisher:" + hashlib.sha256((record["feed_url"]+"\n"+record["episode_guid"]).encode()).hexdigest()
    version = hashlib.sha256((KIND+"|"+edition+"|"+proof["sha256"]).encode()).hexdigest()
    return {"schema_version":1, "video_id":row["video_id"], "channel_dir":row["channel_dir"], "source_kind":KIND,
            "language":"en", "text":text, "text_sha256":proof["sha256"], "bundle_sha256":proof["sha256"],
            "raw_sha256":proof["sha256"], "text_version_id":version, "source_document_sha256":proof["sha256"],
            "source_metadata_sha256":record["provenance"]["sha256"], "source_url":record["source_url"],
            "source_edition_id":edition, "source_audio_sha256":None, "segments":segments, "paragraph_count":len(segments),
            "offset_unit":"unicode_codepoint", "source_timebase":None, "usable_timed_text":False, "speech_coverage_verified":False,
            "recording_association_method":"same_publisher_title_season_episode_duration", "recording_equivalence_verified":False,
            "native_youtube_alignment_verified":False, "source_timecodes_alignment_verified":False,
            "edition_receipt_sha256":hashlib.sha256(json.dumps(record,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()}
