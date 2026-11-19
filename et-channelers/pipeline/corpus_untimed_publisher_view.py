"""Validate previously archived publisher transcripts and retain paragraph-level evidence."""
from __future__ import annotations

import hashlib
import io
import json
import re
import stat
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from . import common, ingestion_status as status, publisher_mirror


KIND = "publisher_untimed_transcript"
PAIRED_PAGE = "publisher_episode_page_exact_youtube_id"
FOLDERS = {"videos": "Videos", "shorts": "Shorts", "streams": "Streams"}
WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_TEXT_BYTES = 2_000_000
MAX_DOCX_BYTES = 5_000_000
MAX_OFFICE_EXPANSION = 20_000_000
ENGLISH_WORDS = set("the and to of is you that it in a i we this have for with so".split())


def _need(value, error):
    if not value:
        raise ValueError(error)


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _same_bytes(raw, proof):
    return (len(raw) == proof["bytes"] and hashlib.md5(raw).hexdigest() == proof["md5"]
            and _hash(raw) == proof["sha256"])


def _identity(record, row, remote):
    """Bind every accepted source, text, and metadata object to a single verified edition."""
    video, creator, tab = row["video_id"], row["channel_dir"], row["tab"]
    _need(status.record_row(row) and tab in FOLDERS and record.get("schema_version") == 1
          and record.get("status") == "verified" and record.get("associated_youtube_id") == video
          and record.get("channel_dir") == creator and record.get("source_tab", record.get("tab", "videos")) == tab
          and all(record.get(k) is False for k in (*publisher_mirror.NATIVE_FLAGS, "human_verified",
                                                    "recording_equivalence_verified")),
          "Unexpected publisher transcript edition or owner")
    if "tab" in record:
        _need(record["tab"] == tab, "Publisher transcript tab mismatch")
    evidence = record.get("source_tab_evidence")
    if evidence is not None:
        _need(isinstance(evidence, dict) and evidence.get("video_id") == video and evidence.get("tab") == tab
              and evidence.get("channel_dir") == creator and re.fullmatch("[a-f0-9]{64}", str(evidence.get("roster_sha256"))),
              "Invalid transcript selection evidence")
    audio, meta, text = (record.get(key) for key in ("audio", "provenance", "publisher_transcript"))
    _need(all(status.publisher_object_proof(x) for x in (audio, meta, text))
          and len({x["drive_id"] for x in (audio, meta, text)}) == 3
          and record.get("variant_id") == audio["sha256"], "Unverified publisher transcript source objects")
    parent = f"{remote.rstrip('/')}/{creator}/{FOLDERS[tab]}/{video}/PublisherVariants/{audio['sha256']}"
    _need(re.fullmatch(re.escape(parent) + r"/publisher-audio\.(?:mp3|aac|m4a|opus|ogg|webm|flac)", audio.get("remote", ""))
          and meta.get("remote") == parent + "/provenance.json" and text.get("remote") == parent + "/publisher-transcript.en.txt"
          and text["bytes"] <= MAX_TEXT_BYTES and text.get("timed") is False and text.get("language") == "en"
          and type(text.get("paragraphs")) is int and text["paragraphs"] > 0
          and record.get("caption_state") == "english_publisher_transcript_untimed", "Invalid archived untimed transcript")
    method = record.get("association_method")
    if method == PAIRED_PAGE:
        _need(status.publisher_episode_page_reference(record) and status.publisher_episode_transcript_reference(record, parent),
              "Publisher's two players and source document must identify the same episode")
        binding = record["publisher_episode_binding"]
        _need(all(not row.get(k) or row[k] == binding["publisher_channel_id"] for k in ("channel_id", "expected_channel_id")),
              "Official publisher channel mismatch")
        document = record["publisher_transcript_document"]
        source = record["publisher_transcript_provenance"]
        observation = source.get("observation", {})
        _need(document["bytes"] <= MAX_DOCX_BYTES and observation.get("accepted") is True
              and observation.get("http_status") == 200 and observation.get("eof_observed") is True
              and observation.get("declared_http_bytes") == observation.get("obtained_bytes") == document["bytes"]
              and observation.get("source_url") == source["source_url"]
              and all(observation.get("fingerprint", {}).get(k) == document[k] for k in ("bytes", "md5", "sha256"))
              and text.get("language_verification") == "english_document_lexical_check"
              and text.get("completeness") == "complete_publisher_declared_document"
              and text.get("audio_alignment_verified") is False
              and text.get("usable_timed_text", False) is False and text.get("source_timecodes_alignment_verified", False) is False,
              "Unverified untimed DOCX extraction provenance")
        return document, source["source_url"], "paired_official_episode_page"
    if record.get("provider") == "Riverside":
        _need(status.riverside_transcript_reference(record), "Invalid publisher RSS transcript reference")
        return text, text["source"], "publisher_declared_episode_text"
    url = urlsplit(text.get("source", ""))
    _need(record.get("kind") == "qualified_publisher_mirror_audio_variant"
          and method == "publisher_owner_title_date_duration" and record.get("exact_youtube_crossreference") is False
          and record.get("channel_dir") == "sounds-true" and record.get("provider") in ("Sounds True / ART19", "Sounds True / Blubrry")
          and url.scheme == "https" and url.netloc == "www.soundstrue.com" and not url.query and not url.fragment
          and re.fullmatch(r"/a/resources/transcript/[a-z0-9-]+/", url.path), "Unknown publisher transcript association")
    return text, text["source"], "qualified_title_date_duration"


def input_rows(root, frame, remote=status.DEFAULT_REMOTE, *, journal_records=None, additional_verified_records=()):
    """Read verified journal rows, optionally reusing a caller's journal snapshot and closed batch receipts."""
    targets = {row["video_id"]: row for row in frame}
    if journal_records is None:
        journal_records = common.read_jsonl(Path(root) / "sync/publisher_mirror_manifest.jsonl")
    sources = (journal_records, additional_verified_records)
    seen = set()
    for source in sources:
        for record in source:
            if not isinstance(record, dict) or "publisher_transcript" not in record:
                continue
            video = record.get("associated_youtube_id")
            if video not in targets:
                continue
            row = targets[video]
            try:
                proof, _, _ = _identity(record, row, remote)
            except (AttributeError, KeyError, TypeError, ValueError):
                continue
            key = (video, record["variant_id"], record["publisher_transcript"]["sha256"], proof["sha256"])
            if key not in seen:
                seen.add(key)
                yield {"kind": KIND, "row": row, "record": record, "proof": proof, "track_id": KIND + ":en"}


def local_bundle(root, job):
    """Prefer an explicitly retained publisher document. A missing artifact can be staged using job['proof']."""
    root = Path(root).resolve()
    record, row, proof = job["record"], job["row"], job["proof"]
    is_docx = record.get("association_method") == PAIRED_PAGE
    suffix = ".docx" if is_docx else ".txt"
    cache = root / "corpus/inputs/publisher-transcripts" / (proof["sha256"] + suffix)
    if not status.record_row(row) or not re.fullmatch("[a-f0-9]{64}", str(proof.get("sha256"))):
        return None
    candidates = [cache]
    if is_docx:
        pattern = row["channel_dir"] + "-publisher-*/batch-*/" + row["video_id"] + "/publisher-transcript.retained.source.docx"
        candidates.extend((root / "jobs").glob(pattern))
    else:
        candidates.extend((root / "jobs").glob(row["channel_dir"] + "-*/publisher-transcript.en.txt"))
    matches = [path for path in candidates if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root)
               and path.stat().st_size == proof["bytes"]]
    if len(matches) <= 1:
        return next(iter(matches), None)
    # Two different editions can have identical exported length. Select by the archived checksum in that case.
    return next((path for path in matches if _same_bytes(path.read_bytes(), proof)), None)


def _document(raw):
    """Reproduce the publisher worker's Word paragraph extraction, retaining original XML paragraph ordinals."""
    with ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        _need("word/document.xml" in archive.namelist() and 0 < len(infos) <= 500 and len(set(archive.namelist())) == len(infos)
              and sum(i.file_size for i in infos) <= MAX_OFFICE_EXPANSION, "Unbounded publisher DOCX")
        item = archive.getinfo("word/document.xml")
        _need(not item.flag_bits & 1 and stat.S_IFMT(item.external_attr >> 16) in (0, stat.S_IFREG)
              and item.compress_type in (ZIP_STORED, ZIP_DEFLATED), "Invalid Word document member")
        xml = archive.read(item)
    # Plain Word paragraphs are the source. Relationships and embedded objects are unused.
    charset = "utf-16" if xml[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    source = xml.decode(charset)
    _need(not re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", source, re.I), "Document type definitions are unsupported")
    try:
        tree = ElementTree.fromstring(source)
    except ElementTree.ParseError as error:
        raise ValueError("Invalid publisher Word XML") from error
    _need(tree.tag == WORD + "document", "Invalid Word document namespace")
    paragraphs = []
    for ordinal, node in enumerate(tree.iterfind(".//" + WORD + "p")):
        value = "".join(text.text or "" for text in node.iterfind(".//" + WORD + "t")).strip()
        if value:
            paragraphs.append((ordinal, value))
    _need(paragraphs, "Empty publisher document")
    return paragraphs


def _plain_paragraphs(text):
    # The publisher's export uses blank lines between paragraphs. Text offsets refer to the untouched UTF-8 document.
    sections = re.split(r"\r?\n(?:[ \t]*\r?\n)+", text)
    return [(i, section.rstrip("\r\n")) for i, section in enumerate(sections) if section.strip()]


def text_views(path, job, remote=status.DEFAULT_REMOTE):
    """Return an English publisher-edition view with paragraph offsets and absent media times."""
    _need(job["kind"] == KIND, "Unsupported publisher text input")
    record, row = job["record"], job["row"]
    proof, source_url, match = _identity(record, row, remote)
    _need(all(job["proof"].get(k) == proof[k] for k in ("bytes", "sha256", "md5", "remote", "drive_id")),
          "Publisher input receipt changed")
    with Path(path).open("rb") as stream:
        raw = stream.read(proof["bytes"] + 1)
    _need(_same_bytes(raw, proof), "Publisher transcript source size or checksum mismatch")
    text_proof = record["publisher_transcript"]
    is_docx = record["association_method"] == PAIRED_PAGE
    if is_docx:
        paragraphs = _document(raw)
        text = "\n\n".join(p for _, p in paragraphs) + "\n"
        _need(_same_bytes(text.encode("utf-8"), text_proof), "DOCX paragraphs do not reproduce the verified English text")
        words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text.lower())
        hits = sum(word in ENGLISH_WORDS for word in words)
        _need(len(words) == text_proof.get("words") and hits == text_proof.get("english_common_words")
              and len(words) >= 500 and hits >= len(words) * .12 and "julie" in words[:500],
              "Publisher document language evidence changed")
        source_member = "word/document.xml"
    else:
        text = raw.decode("utf-8")
        paragraphs = _plain_paragraphs(text)
        source_member = "publisher-transcript.en.txt"
        if record.get("provider") == "Riverside":
            words = re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())
            _need(len(words) == text_proof["words"]
                  and sum(word in ENGLISH_WORDS for word in words) == text_proof["english_common_words"],
                  "Publisher RSS transcript language evidence changed")
    _need(len(paragraphs) == text_proof["paragraphs"], "Publisher transcript paragraph count changed")
    spans = []
    cursor = 0
    for index, (ordinal, value) in enumerate(paragraphs):
        start = text.find(value, cursor)
        _need(start >= cursor and not text[cursor:start].strip(), "Unmapped publisher transcript text")
        end = start + len(value)
        spans.append({"paragraph_index": index, "source_paragraph_index": ordinal, "source_member": source_member,
                      "source_segment_id": f"{source_member}:paragraph:{ordinal}", "char_start": start, "char_end": end,
                      "time_start": None, "time_end": None})
        cursor = end
    _need(not text[cursor:].strip(), "Trailing content lacks publisher paragraph provenance")
    audio = record["audio"]
    version = "untimed-publisher-v1|" + audio["sha256"] + "|" + proof["sha256"] + "|" + text_proof["sha256"]
    view = {"schema_version": 1, "video_id":row["video_id"], "channel_dir":row["channel_dir"],
            "source_kind":KIND, "track_id":job["track_id"], "text_kind":"publisher_declared_untimed_transcript",
            "language":"en", "language_evidence":{"basis":text_proof.get("language_verification", "publisher_transcript_receipt")},
            "text":text, "text_sha256":text_proof["sha256"], "raw_sha256":proof["sha256"], "bundle_sha256":proof["sha256"],
            "text_version_id":_hash(version.encode()), "segments":spans, "offset_unit":"unicode_codepoint",
            "paragraph_count":len(spans), "source_timebase":None, "usable_timed_text":False, "known_cue_union_seconds":None,
            "source_timecodes_present":bool(re.search(r"\[\d{2}:\d{2}:\d{2}\]", text)), "source_timecodes_alignment_verified":False,
            "source_edition_id":"sha256:" + audio["sha256"], "source_audio_sha256":audio["sha256"],
            "source_audio_drive_id":audio["drive_id"], "source_url":source_url, "source_document_sha256":proof["sha256"],
            "source_metadata_sha256":record["provenance"]["sha256"], "edition_receipt_sha256":_hash(publisher_mirror.encoded(record)),
            "recording_association_method":record["association_method"], "association_evidence":match,
            "recording_equivalence_verified":False, "native_youtube_alignment_verified":False,
            "speech_coverage_verified":False, "speaker_attribution":None, "human_reviewed":False}
    return {"english":view}
