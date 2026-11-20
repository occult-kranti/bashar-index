"""Private post-collection CUDA transcription of specific archived audio editions.

Inventory reads existing receipts. Execution requires a completed selection, the
same source-verified proposal, the existing unpaused GPU lease, and its model.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import is_dataclass, replace
import hashlib
import json
import math
import os
from pathlib import Path
import re
import threading
import time
from types import SimpleNamespace
import zipfile

from . import (collection_coverage, common, corpus_asr_view, corpus_caption_view, corpus_publisher_variant_view, gpu_asr_batch as batch,
               drive_ingest, gpu_asr as base, gpu_asr_multilingual as multi, gpu_asr_review, ingestion_status as status,
               postrun_candidates, publisher_caption_batch, qualified_direct_audio_receipts, qualified_edition_receipts)

PROFILE = "postrun_verified_audio_editions_v1"
RESULT = "verified_edition_asr"
JOURNAL = "edition_asr_manifest.jsonl"
PROOF = ("remote", "drive_id", "bytes", "md5", "sha256")
PUBLISHER = "publisher_audio_edition"
EXTRACT = "qualified_youtube_audio_extract"
DIRECT = "qualified_youtube_direct_audio"
NATIVE = "native_youtube_audio"
ALL_SOURCES = "native_qualified_and_publisher"
OUTSTANDING_KIND = "owner_authorized_outstanding_recordings"
# Holds that only say "the probe windows held no clear speech" (music, meditation, silence).
FALLBACK_REASONS = {"no_reliable_speech", "language_confidence_insufficient",
                    "insufficient_independent_sensitive_speech_evidence"}
DETECTOR_BASES = {"metadata_and_model_agreement", "model_agreement_across_speech_probes"}
# Owner policy of 2026-11-20: a creator whose detected recordings are all English is taken as English.
CHANNEL_POLICY = "owner_2026-11-20_channel_language"
MIN_CREATOR_VOTES = 2
# A transcript made without probes whose mean log-probability is below this goes to the detector after
# all. English results of this run: median -0.12, 2nd percentile -0.40, lowest -0.61 (158 recordings).
DOUBT_LOG_PROBABILITY = -0.5
SOURCE_ORDER = (NATIVE, DIRECT, EXTRACT, PUBLISHER)
SOURCE_REVIEW_ERRORS = {"audio_stream_count", "decoded_duration_mismatch", "decoded_duration_limit", "no_complete_transcript",
                        "word_text_alignment", "segment_text_alignment", "segment_time", "word_time", "segment_order"}
KIND_ORIGINAL = {NATIVE: "original_asr", DIRECT: "qualified_youtube_original_asr", EXTRACT: "qualified_youtube_original_asr",
                 PUBLISHER: "publisher_original_asr"}
KIND_ENGLISH = {NATIVE: "english_audio_translation", DIRECT: "qualified_youtube_english_audio_translation", EXTRACT: "qualified_youtube_english_audio_translation",
                PUBLISHER: "publisher_english_audio_translation"}
TIMEBASE = {NATIVE: "native_youtube_audio_seconds", DIRECT: "qualified_youtube_audio_seconds",
            EXTRACT: "qualified_youtube_audio_seconds", PUBLISHER: "publisher_audio_seconds"}


def need(value, why):
    if not value:
        raise ValueError(why)


def digest(value):
    return hashlib.sha256(base.encoded(value)).hexdigest()


def proof(value):
    need(status.publisher_object_proof(value) and isinstance(value.get("remote"), str), "Invalid archived edition proof")
    return {key: value[key] for key in PROOF}


def source(job_type, row, variant, audio, metadata, duration, method, record):
    need(type(duration) in (float, int) and math.isfinite(duration) and duration > 0, "Missing verified edition duration")
    audio, metadata = proof(audio), proof(metadata)
    need(audio["drive_id"] != metadata["drive_id"] and audio["remote"].rpartition("/")[0] == metadata["remote"].rpartition("/")[0],
         "Audio and metadata must be distinct objects from the same edition")
    value = {"video_id":row["video_id"], "channel_dir":row["channel_dir"], "tab":row["tab"], "source_type":job_type,
             "source_variant_id":variant, "audio":audio, "metadata":metadata, "duration_seconds":duration,
             "source_timebase":TIMEBASE[job_type],
             "recording_association_method":method, "source_receipt_sha256":digest(record)}
    value["source_key"] = digest({k:value[k] for k in ("video_id","channel_dir","tab","source_type","source_variant_id","audio","metadata")})
    return value


def source_catalogue(root, frame, remote, *, native_records=None):
    rows = {r["video_id"]:r for r in frame}
    found = defaultdict(dict)
    for video, record in (native_records or {}).items():
        row = rows.get(video)
        if (row is None or row["channel_dir"] != record.get("channel_dir") or record.get("tab") not in (None, "", row["tab"])
                or not status.proof(drive_ingest.receipt_complete,record,status.record_row(record),remote)):
            continue
        try:
            quality = record.get("native_acquisition_quality") or {}
            if quality.get("strict_probe_passed") is True and quality.get("audio_streams") == 1:
                seconds = quality.get("container_duration_seconds")
            else:
                seconds = record.get("duration_s") or (record.get("native_format_binding") or {}).get("durationMs", 0) / 1000
            item = source(NATIVE,row,record["sha256"],record,record["metadata"],seconds,"verified_native_audio_and_metadata",record)
        except (ValueError,TypeError,KeyError,OverflowError):
            continue
        found[video][item["source_key"]] = item
    for record in common.read_jsonl(root / "sync/progressive_audio_extracts_manifest.jsonl"):
        video = record.get("video_id")
        if video not in rows:
            continue
        row = rows[video]
        if row["channel_dir"] != record.get("channel_dir") or row["tab"] != record.get("tab"):
            continue
        try:
            direct = record.get("source_format_id") == "140"
            validator = qualified_direct_audio_receipts if direct else qualified_edition_receipts
            checked = validator.validate(record, remote_base=remote)
            parts = []
            for name in ("audio","metadata"):
                obj = record[name]
                parts.append({**obj["local_proof"], **{k:obj["remote_proof"][k] for k in ("remote","drive_id")}})
            payload = record["qualification"]["payload"]
            seconds = (payload["selection"]["duration_seconds"] if direct
                       else payload["AAC_preservation"]["derived_audio"]["duration_seconds"])
            item = source(DIRECT if direct else EXTRACT, row, checked.variant_id, *parts, seconds, record["kind"], record)
        except (ValueError, TypeError, KeyError, OverflowError, qualified_edition_receipts.ReceiptHold):
            continue
        found[video].setdefault(item["source_key"], item)
    for name in ("publisher_variant_manifest.jsonl","publisher_mirror_manifest.jsonl"):
        receipts = common.read_jsonl(root / "sync" / name)
        aliases = {r["associated_youtube_id"] for r in receipts if r.get("kind") == "shared_publisher_audio_association"
                   and r.get("associated_youtube_id") in rows}
        anchors, accepted_aliases = {}, set()
        if aliases:
            owners = {video:(row["channel_dir"],row["tab"]) for video,row in rows.items()}
            required = {r.get("canonical_receipt_sha256") for r in receipts if r.get("associated_youtube_id") in aliases}
            for r in receipts:
                if r.get("kind") != "shared_publisher_audio_association":
                    key = status.publisher_receipt_digest(r)
                    if key in required:
                        anchors[key] = r
            accepted_aliases = status.publisher_mirror_evidence(root,aliases,remote,target_rows=rows.values())[0]
        for record in receipts:
            video = record.get("associated_youtube_id") or record.get("video_id")
            if video not in rows:
                continue
            row = rows[video]
            try:
                if record.get("kind") == "shared_publisher_audio_association":
                    anchor = anchors.get(record.get("canonical_receipt_sha256"))
                    need(video in accepted_aliases and anchor and status.shared_publisher_audio_reference(record,anchor,remote,owners),
                         "Publisher alias lacks a verified original edition and association")
                    item = source(PUBLISHER,row,anchor["variant_id"],anchor["audio"],anchor["provenance"],
                                  anchor.get("actual_probe_duration_s",anchor.get("measured_duration_s")),
                                  record["association_method"],record)
                    item.update(canonical_associated_youtube_id=anchor["associated_youtube_id"],
                                canonical_receipt_sha256=record["canonical_receipt_sha256"],
                                association_provenance=proof(record["provenance"]), audio_reference=proof(record["audio_reference"]))
                    item["source_key"] = digest([item["source_key"],item["canonical_receipt_sha256"],
                                                 item["association_provenance"],item["audio_reference"]])
                    found[video].setdefault(item["source_key"],item)
                    continue
                if record.get("association_method") == "publisher_episode_page_exact_youtube_id":
                    need(status.publisher_episode_page_reference(record), "Invalid paired publisher page")
                    audio, meta = record["audio"],record["provenance"]
                    folder = corpus_publisher_variant_view.FOLDERS[row["tab"]]
                    prefix = f"{remote}/{row['channel_dir']}/{folder}/{video}/PublisherVariants/{audio['sha256']}/"
                    need(record.get("status") == "verified" and record.get("source_tab") == row["tab"]
                         and record.get("channel_dir") == row["channel_dir"] and record.get("variant_id") == audio["sha256"]
                         and audio["remote"] == prefix+"publisher-audio.mp3" and meta["remote"] == prefix+"provenance.json"
                         and all(record.get(k) is False for k in ("human_verified","native_youtube_bytes","changes_native_audio_count",
                                 "changes_native_caption_count","changes_native_asr_count","recording_equivalence_verified")),
                         "Unbound publisher episode audio and metadata")
                    method = record["association_method"]
                else:
                    method = corpus_publisher_variant_view._source_method(record, row, remote)
                item = source(PUBLISHER, row, record["audio"]["sha256"], record["audio"], record["provenance"],
                              record.get("actual_probe_duration_s",record.get("measured_duration_s")), method, record)
            except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
                continue
            found[video].setdefault(item["source_key"], item)
    return found


def accepted_result(record, item):
    try:
        _validate_result(record, item)
    except (KeyError, TypeError, ValueError):
        return False
    return True


def _validate_result(record, item):
    origin = record["inference_source"]
    need(audio_identity(origin) == audio_identity(item), "ASR result belongs to different audio bytes")
    need(record.get("schema_version") == 1 and record.get("status") == "verified" and record.get("artifact_kind") == RESULT
         and record.get("profile") == PROFILE and record.get("output_contract") == multi.CONTRACT
         and record.get("source") == item and record.get("source_timebase") == item["source_timebase"]
         and record.get("source_key") == item["source_key"] and record.get("video_id") == item["video_id"]
         and record.get("channel_dir") == item["channel_dir"] and record.get("quality_state") == "unreviewed_asr"
         and record.get("native_youtube_bytes") is (item["source_type"] == NATIVE)
         and all(record.get(k) is False for k in ("changes_native_asr_count",
                   "recording_equivalence_verified","native_youtube_alignment_verified")), "Unknown or misbound edition ASR receipt")
    run = record["run_id"]
    need(re.fullmatch(r"asr-[a-f0-9]{24}", run) and status.publisher_object_proof(record)
         and record["remote"] == result_remote(origin, run)
         and record["drive_id"] not in {item["audio"]["drive_id"], item["metadata"]["drive_id"],
                                        origin["audio"]["drive_id"], origin["metadata"]["drive_id"]}
         and re.fullmatch("[a-f0-9]{64}",str(record.get("artifact_manifest_sha256")))
         and re.fullmatch("[a-f0-9]{64}",str(record.get("selection_sha256")))
         and re.fullmatch("[a-f0-9]{64}",str(record.get("proposal_sha256")))
         and record["language_decision"]["status"] == "accepted", "Invalid edition ASR publication identity")
    variants = record["text_variants"]
    original, english = variants["original"],variants["english"]
    need(original["text_kind"] == "original_asr" and original["language"] == record["language_decision"]["language"]
         and english["language"] == "en" and
         (original["language"] == "en" and english.get("same_as") == "original" and english["text_kind"] == "original_english_alias"
          or original["language"] != "en" and english["text_kind"] == "english_audio_translation"),
         "Edition ASR requires original text and an English view")


def input_rows(root, frame, remote, *, sources=None, records=None):
    root = Path(root)
    if records is None:
        records = common.read_jsonl(root/"sync"/JOURNAL)
    if not records:
        return
    frame = list(frame)
    if sources is None:
        natives = status.latest_records(root/"sync/drive_ingest_manifest.jsonl") if any(
            any((r.get(k) or {}).get('source_type') == NATIVE for k in ('source','inference_source')) for r in records) else None
        sources = source_catalogue(root, frame, remote, native_records=natives)
    rows = {r["video_id"]:r for r in frame}
    seen = set()
    for record in records:
        video = record.get("video_id")
        item = sources.get(video,{}).get(record.get("source_key"))
        origin = record.get("inference_source") or {}
        if (item is None or sources.get(origin.get("video_id"), {}).get(origin.get("source_key")) != origin
                or not accepted_result(record,item)):
            continue
        key = (video,item["source_key"],record["sha256"])
        if key not in seen:
            seen.add(key)
            yield {"kind":RESULT,"row":rows[video],"record":record,"edition":item,"proof":record,"track_id":record["run_id"]}


def inventory(root, selection, expected, remote=status.DEFAULT_REMOTE, *, include_native=True, inputs=None,
              reviews=None, review_sha256=None):
    """Join one pinned roster to real audio receipts, existing English text and the native queue."""
    from . import stage_archived_text
    root = common.ensure_outside_git(root)
    frame, _, pin = collection_coverage.mixed_selection(Path(selection), {})
    need(pin == expected, "The frozen selection changed")
    native, sources, results = inputs if inputs is not None else catalogue_inputs(root, frame, remote)
    language_reviews = {}
    if include_native:
        for receipt in common.read_jsonl(root / "sync/asr_language_manifest.jsonl"):
            decision = receipt.get("decision") or {}
            if (receipt.get("status") == decision.get("status") == "held"
                    and receipt.get("semantic_text_generated") is False and decision.get("reason")):
                identity = receipt.get("video_id"), receipt.get("source_audio_sha256"), receipt.get("source_audio_drive_id")
                language_reviews[identity] = decision["reason"]
    text = defaultdict(set)
    for job in stage_archived_text.input_rows(root, frame, remote, native_records=native,
                                             edition_sources=sources, edition_results=results):
        if job["kind"] == corpus_publisher_variant_view.CAPTION:
            if (job["item"].get("track_key") is None and
                    not publisher_caption_batch.confirmed_english_cues(job['item'].get('language_evidence'))):
                continue
        text[job["row"]["video_id"]].add(job["kind"])
    records = []
    for row in frame:
        video = row["video_id"]
        native_rec = native.get(video,{})
        # Older valid native receipts have a blank tab. Their object path is
        # verified against their own recording metadata by receipt_complete.
        has_native = (native_rec.get("channel_dir") == row["channel_dir"]
                      and status.proof(drive_ingest.receipt_complete, native_rec, status.record_row(native_rec), remote))
        candidates = sorted((s for s in sources.get(video,{}).values() if include_native or s["source_type"] != NATIVE),
                            key=lambda s:(SOURCE_ORDER.index(s["source_type"]),
                          s["recording_association_method"] == "publisher_owner_title_date_duration", s["source_key"]))
        prior_reviews = {candidate["source_key"]: language_reviews[key] for candidate in candidates
                         if (key := (video, candidate["audio"]["sha256"], candidate["audio"]["drive_id"])) in language_reviews}
        permit = (reviews or {}).get(video)
        eligible = [candidate for candidate in candidates if candidate["source_key"] not in prior_reviews
                    or gpu_asr_review.matches(permit,candidate)]
        if text[video] and (has_native or candidates):
            disposition = "existing_english_text"
        elif has_native and not include_native:
            disposition = "existing_native_queue"
        elif eligible:
            disposition = "edition_asr_eligible"
        else:
            disposition = "existing_language_review" if prior_reviews else "audio_missing"
        records.append({"video_id":video,"channel_dir":row["channel_dir"],"tab":row["tab"],"status":disposition,
                        "existing_text_kinds":sorted(text[video]),"native_audio_verified":bool(has_native),
                        "verified_language_reviews": prior_reviews,
                        "verified_edition_sources":[c["source_type"] for c in candidates],
                        "selected_source":eligible[0] if disposition == "edition_asr_eligible" else None})
    return {"schema_version":1,"profile":PROFILE,"selection_sha256":pin,"remote":remote,"rows":records,
            **({"prior_speech_review_sha256":review_sha256} if review_sha256 else {}),
            "source_scope":ALL_SOURCES if include_native else "qualified_and_publisher",
            "counts":dict(Counter(r["status"] for r in records)),
            "eligible_by_source":dict(Counter(r["selected_source"]["source_type"] for r in records if r["selected_source"])),
            "source_timebases":dict(Counter(r["selected_source"]["source_timebase"] for r in records if r["selected_source"])),
            "selected_recordings":len(records)}


def audio_identity(item):
    audio = item["audio"]
    return audio["sha256"], audio["bytes"], audio["md5"]


def catalogue_inputs(root, frame, remote):
    native = status.latest_records(root/"sync/drive_ingest_manifest.jsonl")
    return native, source_catalogue(root,frame,remote,native_records=native), common.read_jsonl(root/"sync"/JOURNAL)


def result_remote(item, run_id):
    parent = item["audio"]["remote"].rpartition("/")[0]
    if item["source_type"] == NATIVE:
        parent += "/"+item["video_id"]
    return parent + f"/ASR/{run_id}/{run_id}.zip"


def authorized_outstanding(root, path, expected, selection, frame):
    """Read the owner's dated list of selected recordings that still have no archived audio.

    The list permits speech recognition for every other selected recording. It is exact:
    a listed recording that has since been archived, or a missing one that is not listed,
    stops the run so that a fresh list and proposal are made.
    """
    path = base.within(common.ensure_outside_git(path), root)
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected, "Outstanding-recording authorization changed")
    document = json.loads(raw)
    listed = document.get("outstanding_video_ids")
    need(document.get("schema_version") == 1 and document.get("kind") == OUTSTANDING_KIND
         and document.get("selection_sha256") == selection and document.get("authorized_by") == "owner"
         and isinstance(document.get("instruction_utc"), str) and document["instruction_utc"]
         and isinstance(listed, list) and listed and all(isinstance(video, str) for video in listed)
         and len(set(listed)) == len(listed), "Invalid outstanding-recording authorization")
    need(set(listed) <= {row["video_id"] for row in frame}, "Authorization names a recording outside the selection")
    return frozenset(listed)


def partial_frame(snapshot, saved, frame, scopes, expected, outstanding):
    """The complete-frame checks, except that exactly the authorized recordings lack audio."""
    summary = snapshot["summary"]
    wanted = {(r["channel_dir"], r["video_id"]) for r in frame}
    actual = {(r["channel_dir"], r["video_id"]) for r in saved}
    by_creator = Counter(c for c, _ in wanted)
    missing = {video for _, video in wanted - actual}
    if (snapshot.get("selection_sha256") != expected or not scopes or not wanted or not outstanding
            or len(wanted) != len(frame) or len(actual) != len(saved) or not actual <= wanted
            or missing != set(outstanding)
            or summary["latest20_target"] != len(wanted) or summary["audio_available"] != len(actual)
            or summary["channels"] != len(scopes) or summary["remaining_audio"] != len(missing)
            or any(not (scope == "all_requested_positions_observed" and by_creator[c] == 20
                        or scope == "short_complete_displayed_list" and by_creator[c] < 20)
                   for c, scope in scopes.items()) or not set(by_creator) <= scopes.keys()):
        raise ValueError("The recordings without audio differ from the owner's authorized outstanding list")


def grouped_sources(plan, current, *, reviews=None, outstanding=frozenset()):
    """Keep one inference per exact audio object content; retain each selected recording's proof."""
    fresh = {row["video_id"]: row for row in current["rows"]}
    groups = defaultdict(list)
    for row in plan["rows"]:
        actual = fresh.get(row["video_id"])
        need(actual is not None, "Video outside the pinned selection")
        if plan.get("source_scope") == ALL_SOURCES:
            need(actual["status"] != "audio_missing" or row["video_id"] in outstanding,
                 "Saved recording lacks a typed ASR source")
            need(actual["status"] == "audio_missing" or row["video_id"] not in outstanding,
                 "An authorized outstanding recording now has audio; generate a fresh authorization and inventory")
            need(row["selected_source"] is not None or actual["status"] != "edition_asr_eligible",
                 "Newly ready audio is missing from this proposal; generate a fresh inventory")
        source = row["selected_source"]
        if source is None:
            continue
        if actual["status"] in ("existing_native_queue", "existing_english_text", "existing_language_review"):
            continue
        need(actual["selected_source"] == source, "Archived input or recording association changed; refresh the plan")
        groups[audio_identity(source)].append(source)
    ordered = [sorted(items, key=lambda x: (bool(x.get("canonical_associated_youtube_id")), x["video_id"], x["source_key"]))
               for items in groups.values()]
    if reviews:
        # Resolve shorter, already reviewed cases early in the same warmed batch.
        for group in ordered:
            group.sort(key=lambda item: not gpu_asr_review.matches(reviews.get(item["video_id"]), item))
        ordered.sort(key=lambda group: not gpu_asr_review.matches(reviews.get(group[0]["video_id"]), group[0]))
    return ordered


def staged_pair(root, origin, remote, drive):
    """Resume already accepted source bytes. Stage one input pair in a checksum-addressed directory."""
    from . import stage_archived_text
    cache = drive_ingest.local_path(root, "asr/input/edition-" + origin["audio"]["sha256"])
    cache.mkdir(parents=True, exist_ok=True)
    needed, files = {}, {}
    for name in ("audio", "metadata"):
        obj = origin[name]
        rel = drive_ingest.remote_relative(remote, obj["remote"])
        files[name] = drive_ingest.local_path(cache, rel)
        if not files[name].exists():
            needed[rel] = obj
    if needed:
        stage_archived_text.fetch_batch(drive, remote, cache, needed)
    for name, path in files.items():
        result = base.hashes(path)
        need(all(result[k] == origin[name][k] for k in result), "Staged edition source hash mismatch")
    return files


class Staging:
    """Fetch the next few inputs while the recognizer works on the current one.

    ``staged_pair`` still checks every file against its receipt, here and again when the
    input is taken. A fetch that fails ahead of time is simply tried again in turn.
    """

    def __init__(self, root, remote, drive, depth, workers=2):
        self.root, self.remote, self.drive, self.depth = root, remote, drive, depth
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="stage")
        self.waiting = {}

    def ahead(self, origins, admit):
        for origin in origins:
            if len(self.waiting) >= self.depth:
                break
            key = origin["audio"]["sha256"]
            if key not in self.waiting:
                admit(sum(origin[name]["bytes"] for name in ("audio", "metadata")))
                self.waiting[key] = self.pool.submit(staged_pair, self.root, origin, self.remote, self.drive)

    def take(self, origin):
        future = self.waiting.pop(origin["audio"]["sha256"], None)
        if future is not None:
            try:
                return future.result()
            except Exception:
                pass
        return staged_pair(self.root, origin, self.remote, self.drive)

    def close(self):
        for future in self.waiting.values():
            future.cancel()
        self.pool.shutdown(wait=True)


class Publications:
    """Upload, verify and journal finished results on one background thread, in order.

    A failure surfaces in the main loop at the next collection. The local result stays on
    disk, so the next run publishes it without another fetch or inference.
    """

    def __init__(self, backlog=3):
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="publish")
        self.pending = deque()
        self.backlog = backlog

    def submit(self, work, run_id):
        self.pending.append((self.pool.submit(work), run_id))

    def collect(self, results, *, wait):
        while self.pending and (wait or self.pending[0][0].done() or len(self.pending) > self.backlog):
            future, run_id = self.pending.popleft()
            recorded = future.result()
            results.append({"state":"verified","video_ids":[x["video_id"] for x in recorded],"run_id":run_id})

    def close(self):
        self.pool.shutdown(wait=True)


class Lookahead:
    """Recognize the next few 30-second windows concurrently; hand results back strictly in order.

    The source clock is still decoded once, in order, on the caller's thread. Each window is
    recognized exactly as it would be alone (same model, same settings, no shared context),
    so only the waiting changes. ``skip`` names windows a checkpoint already holds.
    """

    def __init__(self, windows, engine, config, workers, skip=None):
        self.source, self.config, self.depth = windows, config, 2 * workers
        self.runtime = SimpleNamespace(model=engine, windows=windows)
        self.skip = skip or (lambda index: False)
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="window")
        self.pending = deque()
        self.current = None

    def _recognize(self, audio):
        iterator, info = self.runtime.model.transcribe(audio, **self.config)
        return list(iterator), info

    def windows(self, path, duration):
        source = enumerate(self.source(path, duration))
        finished = False
        while True:
            while not finished and len(self.pending) < self.depth:
                try:
                    index, (start, audio) = next(source)
                except StopIteration:
                    finished = True
                    break
                self.pending.append((start, audio, None if self.skip(index) else self.pool.submit(self._recognize, audio)))
            if not self.pending:
                return
            start, audio, self.current = self.pending.popleft()
            yield start, audio

    def transcribe(self, audio):
        need(self.current is not None, "Window was not submitted for recognition")
        segments, info = self.current.result()
        return iter(segments), info

    def close(self):
        for _, _, future in self.pending:
            if future is not None:
                future.cancel()
        self.pending.clear()
        self.pool.shutdown(wait=True)


@contextmanager
def offline_model_environment(root):
    temporary = root / "asr/tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    settings = {"HF_HUB_OFFLINE":"1", "HF_HUB_DISABLE_IMPLICIT_TOKEN":"1", "TRANSFORMERS_OFFLINE":"1",
                "HF_HOME":str(root / "asr/cache"), "TEMP":str(temporary), "TMP":str(temporary),"OMP_NUM_THREADS":"2"}
    previous = {key:os.environ.get(key) for key in settings}
    os.environ.update(settings)
    try:
        yield
    finally:
        for key,value in previous.items():
            if value is None:
                os.environ.pop(key,None)
            else:
                os.environ[key] = value


def english_model(settings, lease):
    """Verify the lease's pinned English-only model. Returns (proof, directory), or None without one."""
    binding = base.english_binding(lease) if lease.get("additional_models_allowed") is True else None
    if binding is None:
        return None
    directory = base.within(binding["model_dir"], settings.root)
    receipt = base.within(binding["model_receipt"], settings.root)
    pinned = base.model_proof(SimpleNamespace(model_dir=directory, model_receipt=receipt,
                                              environment_lock=settings.environment_lock))
    need(all(binding[k] == pinned[k] for k in ("repository","revision","model_sha256")),
         "GPU lease binds a different English model")
    return pinned, directory, binding.get("parallel_windows", 1)


def load_english(directory, workers=1):
    """The same CUDA settings as the multilingual model; no CPU path."""
    from faster_whisper import WhisperModel
    engine = WhisperModel(str(directory), device="cuda", device_index=0, compute_type="int8_float16",
                          cpu_threads=2, num_workers=workers, local_files_only=True)
    need(engine.model.device == "cuda" and engine.model.compute_type == "int8_float16", "CUDA model required")
    return engine


def fallback_language(decision, channel_choice):
    """Owner policy of 2026-11-20 for a recording whose probe windows held no clear speech.

    Many recordings open with music or contain long meditations, so three probes can miss the
    talking. Rather than hold the recording: one strong probe with no rival decides; otherwise
    ``channel_choice`` (the creator's established language, or the stated default) decides.
    Two plausible languages, or any other kind of hold, still go to a person.
    """
    if decision.get("reason") not in FALLBACK_REASONS:
        return None
    probes = [p for p in decision.get("probes") or [] if isinstance(p, dict) and p.get("language")]
    strong = {p["language"] for p in probes if (p.get("probability") or 0) >= multi.MIN_PROBABILITY}
    plausible = {p["language"] for p in probes if (p.get("probability") or 0) >= .5}
    if len(plausible) > 1:
        return None
    if len(strong) == 1:
        return next(iter(strong)), "single_strong_probe"
    return channel_choice


def quiet_spans(document, duration, least=30.0):
    """Stretches of at least ``least`` seconds with no recognized speech: music, meditation or silence."""
    spans, cursor = [], 0.0
    for item in document["segments"]:
        if item["start"] - cursor >= least:
            spans.append([round(cursor, 1), round(item["start"], 1)])
        cursor = max(cursor, item["end"])
    if duration - cursor >= least:
        spans.append([round(cursor, 1), round(duration, 1)])
    return spans


def transcript_confidence(document):
    """Speech-time-weighted mean of the recognizer's log-probability per segment; None if it reported none."""
    weight = total = 0.0
    for item in document["segments"]:
        value = item.get("avg_logprob")
        if type(value) in (int, float) and math.isfinite(value):
            span = max(.01, item["end"] - item["start"])
            weight, total = weight + span, total + span * value
    return total / weight if weight else None


def infer(settings, origin, audio_path, runtime, model, proposal, selection, guard, *, checkpoint_path=None,
          capacity_check=None, worker_sha=None, metadata_path=None, rolling_history=None, review=None, english=None,
          parallel_windows=1, language_fallback=None, prior_decision=None, channel_language=None):
    """Transcribe original speech, translate non-English speech; both use the inference edition's clock.

    ``english`` is ``(proof, engine)`` or ``(proof, engine, parallel_windows)`` for the lease's
    English-only model. The multilingual model still decides the language. Speech it accepts as
    English is then transcribed by the English model, and the result names that model with the
    deciding model beside it.

    ``channel_language`` (``{"language", "votes"}``) is the language of a creator whose detected
    recordings all agree. Such a recording is transcribed without probes unless its metadata
    names another language; a transcript that reads poorly sends it to the detector after all.
    """
    need(runtime.model.model.device == "cuda" and runtime.model.model.compute_type == "int8_float16", "CUDA model required")
    lease = base.gpu_lease(settings)
    monitor = multi.Monitor(runtime, guard, lease["rolling_utilization_target"] * 100, lease["max_vram_bytes"],
                            rolling_history=rolling_history,
                            **({"soft_temperature": lease["soft_temperature_c"]} if lease.get("soft_temperature_c") else {}))
    job = {"duration_seconds":origin["duration_seconds"], "declared_audio_language":"und", "metadata_content_flags":{}}
    if metadata_path is not None and origin["source_type"] == NATIVE and origin["metadata"]["bytes"] <= base.MAX_RESULT_BYTES:
        metadata = base.read_json(metadata_path)
        if (metadata.get("source") or {}).get("video_id") == origin["video_id"]:
            job["declared_audio_language"] = ((metadata.get("languages") or {}).get("audio")
                                              or (metadata.get("metadata") or {}).get("language") or "und")
            job["metadata_content_flags"] = metadata.get("metadata_content_flags") or {}
    start = base.now()
    worker = worker_sha or worker_digest()
    environment=base.hashes(settings.environment_lock)["sha256"]
    checkpoint=None
    try:
        monitor.begin()
        if checkpoint_path is not None:
            binding=digest([origin,model,proposal,selection,worker,environment,base.CONFIG,base.WINDOW_SECONDS,base.SAMPLE_RATE])
            checkpoint = batch.WindowStore(checkpoint_path, binding, capacity_check,
                                           max_bytes=3 * batch.paired_limit(origin["duration_seconds"]))
        decision=checkpoint.load('language',0) if checkpoint is not None else None
        if decision is None and prior_decision is not None:
            decision = prior_decision          # the detector's saved answer for this same audio
        if decision is None:
            if any(job["metadata_content_flags"].get(key) for key in multi.METADATA_HOLD_FLAGS):
                decision = multi.decide_language(job, [])
            elif review is not None:
                need(gpu_asr_review.matches(review, origin), "Mismatched individual speech-review edition")
                decision = gpu_asr_review.scan_language(runtime, audio_path, job, monitor.guard)
            elif (channel_language is not None and multi.language_code(job["declared_audio_language"])
                  in ("und", "mul", "zxx", channel_language["language"])):
                decision = {"status":"accepted", "language":channel_language["language"],
                            "basis":"creator_established_language", "policy":CHANNEL_POLICY,
                            "creator_detector_votes":channel_language["votes"], "detector_decision":None}
            else:
                decision = multi.detect_language(runtime, audio_path, job, monitor.guard)
            if checkpoint is not None:
                checkpoint.save('language',0,decision)
        if decision["status"] != "accepted" and language_fallback is not None:
            choice = fallback_language(decision, language_fallback.get("channel"))
            if choice is not None:
                decision = {"status":"accepted", "language":choice[0], "basis":choice[1],
                            "policy":"owner_2026-11-20_language_fallback", "detector_decision":decision}
        if decision["status"] != "accepted":
            return {"status":"language_review", "decision":decision, "audio_identity":audio_identity(origin)}
        def recognize(decision):
            language = decision["language"]
            fast = english is not None and language == "en"
            text_model = english[0] if fast else model
            streams = (english[2] if len(english) > 2 else 1) if fast else parallel_windows
            configs = {"original": {**base.CONFIG, "language":language, "task":"transcribe"}}
            if language != "en":
                configs["english"] = {**base.CONFIG, "language":language, "task":"translate"}
            if review is not None and decision.get("only_sensitive_strong_probes"):
                for config in configs.values():
                    config["vad_parameters"] = {**config["vad_parameters"], "threshold": .35}
            variants, metrics = {}, {}
            for key, config in configs.items():
                monitor.guard()
                # Decoding the source clock belongs to the runtime; only the recognizer differs.
                # Windows from one model, or one language, are never resumed with another.
                saved_as=key+"@"+(text_model["model_sha256"][:16] if fast else language)
                ahead=None
                if streams > 1:
                    held=(lambda index,name=saved_as:checkpoint.load(name,index) is not None) if checkpoint is not None else None
                    task=ahead=Lookahead(runtime.windows,english[1] if fast else runtime.model,config,streams,held)
                else:
                    task=multi.TaskRuntime(SimpleNamespace(windows=runtime.windows,model=english[1]) if fast else runtime,config)
                if checkpoint is not None:
                    task=batch.CheckpointedTask(task,checkpoint,saved_as)
                try:
                    segments, transcript, voiced = base.collect_segments(task, audio_path,
                                                                        origin["duration_seconds"], monitor.guard)
                finally:
                    if ahead is not None:
                        ahead.close()
                segments.update(language=language if key == "original" else "en", character_offset_unit="unicode_code_points",
                                text_kind="original_asr" if key == "original" else "english_audio_translation")
                variants[key] = (segments, transcript, config)
                quiet = quiet_spans(segments, origin["duration_seconds"])
                metrics[key] = {"duration_after_vad_seconds":voiced, "segments":len(segments["segments"]),
                                "non_speech_seconds":round(max(0.0, origin["duration_seconds"] - voiced), 1),
                                "quiet_stretches_of_30s_or_more":len(quiet),
                                "quiet_seconds_in_those_stretches":round(sum(b - a for a, b in quiet), 1),
                                "quiet_stretches":quiet[:200]}
            return fast, text_model, streams, configs, variants, metrics

        fast, text_model, streams, configs, variants, metrics = recognize(decision)
        if decision.get("policy") == CHANNEL_POLICY and decision.get("detector_decision") is None:
            confidence = transcript_confidence(variants["original"][0])
            if confidence is not None and confidence < DOUBT_LOG_PROBABILITY:
                # No probes were run and the transcript reads poorly: the detector looks at this one after all.
                second = checkpoint.load('language-recheck',0) if checkpoint is not None else None
                if second is None:
                    second = multi.detect_language(runtime, audio_path, job, monitor.guard)
                    if checkpoint is not None:
                        checkpoint.save('language-recheck',0,second)
                doubt = {"transcript_log_probability":round(confidence, 3), "doubt_below":DOUBT_LOG_PROBABILITY}
                if second["status"] != "accepted":
                    # Unclear probes: one strong probe in another language decides, as for any held recording;
                    # two plausible languages or a conflict with the metadata wait for a person.
                    choice = fallback_language(second, (decision["language"], decision["basis"]))
                    if choice is None:
                        return {"status":"language_review", "audio_identity":audio_identity(origin),
                                "decision":{**second, "replaced_creator_language":decision["language"], **doubt}}
                    if choice[0] != decision["language"]:
                        second = {"status":"accepted", "language":choice[0], "basis":choice[1],
                                  "policy":"owner_2026-11-20_language_fallback", "detector_decision":second}
                if second["status"] == "accepted" and second["language"] != decision["language"]:
                    decision = {**second, "replaced_creator_language":decision["language"], **doubt}
                    fast, text_model, streams, configs, variants, metrics = recognize(decision)
                else:
                    decision = {**decision, "detector_decision":second, **doubt}
    finally:
        try:
            telemetry = monitor.finish()
        finally:
            if checkpoint is not None:checkpoint.close()
    guard()
    identity = {"output_contract":multi.CONTRACT, "profile":PROFILE, "source_audio":origin["audio"],
            "source_metadata":origin["metadata"], "source_key":origin["source_key"], "source_timebase":origin["source_timebase"],
            "selection_sha256":selection, "model":text_model, "proposal_sha256":proposal, "worker_sha256":worker,
            "environment_lock_sha256":environment, "configs":configs}
    if fast:
        identity["language_decision_model"] = model
    if review is not None:
        identity["individual_speech_review_sha256"] = review["source_review_sha256"]
    run_id = "asr-" + base.fingerprint(identity)[:24]
    admission = {"video_id":"edition-"+origin["audio"]["sha256"], "job_id":origin["source_key"],
                 "source_lease_id":settings.gpu_lease_id, "job":{"audio":origin["audio"], "metadata":origin["metadata"]}}
    provenance = {**identity, "schema_version":1, "identity":identity, "run_id":run_id,
            "source_video_id":origin["video_id"], "channel_dir":origin["channel_dir"], "inference_source":origin,
            "language_decision":decision, "started_at":start, "finished_at":base.now(),
            "source_admission_sha256":digest([selection,proposal,origin]),
            "compute":{"device":"cuda:0", "compute_type":"int8_float16", "cpu_asr_fallback":False,
                       "model_workers":streams, "batch_size":1, "gpu_lease_id":settings.gpu_lease_id,
                       "models_loaded":1 if english is None else 2,
                       "text_model_role":"english_only" if fast else "multilingual"},
            "metrics":{"audio_seconds":origin["duration_seconds"], "tasks":metrics}, "dependencies":runtime.dependencies,
            "quality":{"accuracy_claimed":False,"human_reviewed":False,"speech_coverage_validated":False,
                       "translation_semantics_human_verified":False,"word_times_are_model_estimates":True,
                       "native_youtube_alignment_verified":False}}
    receipt = multi.write_pair(settings, admission, run_id, variants, telemetry, provenance,
                               max_bytes=batch.paired_limit(origin['duration_seconds']),capacity_check=capacity_check)
    return {**receipt, "language_decision":decision}


def worker_digest():
    return digest([base.hashes(Path(m.__file__))["sha256"] for m in (base,multi,batch,gpu_asr_review)] + [base.hashes(Path(__file__))["sha256"]])


def publish(settings, local_receipt, associations, drive, *, existing_remote=None, journal_index=None):
    path = base.within(local_receipt["bundle"]["path"], settings.output_root)
    verified = multi.verify_pair(path, local_receipt["bundle"],max_bytes=batch.paired_limit(max(i['duration_seconds'] for i in associations)))
    p = verified["provenance"]
    origin = p["inference_source"]
    need(p["profile"] == PROFILE and p["identity"]["source_key"] == origin["source_key"] and
         p["source_audio"] == origin["audio"] and p["source_metadata"] == origin["metadata"] and
         p["source_timebase"] == origin["source_timebase"] and
         local_receipt["run_id"] == p["run_id"] and all(audio_identity(i) == audio_identity(origin) for i in associations),
         "Result does not match this audio edition")
    remote_path = result_remote(origin, p["run_id"])
    stored = existing_remote
    if stored is None:
        drive.copy(path, remote_path)
        found = drive.stat(remote_path)
        drive_ingest.verify_remote(found, verified["bundle"])
        stored = {**verified["bundle"], "remote":remote_path, "drive_id":found.get("ID")}
    need(proof(stored) == stored and stored["remote"] == remote_path and
         all(stored[k] == v for k,v in verified["bundle"].items()), "Published result changed")
    records = []
    for item in associations:
        record = {**stored, "schema_version":1,"status":"verified","artifact_kind":RESULT, "profile":PROFILE,
            "output_contract":multi.CONTRACT, "video_id":item["video_id"], "channel_dir":item["channel_dir"],
            "source":item, "inference_source":origin, "source_key":item["source_key"], "source_timebase":item["source_timebase"],
            "run_id":p["run_id"], "selection_sha256":p["selection_sha256"], "proposal_sha256":p["proposal_sha256"],
            "artifact_manifest_sha256":verified["artifact_manifest_sha256"], "text_variants":p["text_variants"],
            "language_decision":p["language_decision"], "quality_state":"unreviewed_asr", "native_youtube_bytes":item["source_type"] == NATIVE,
            "changes_native_asr_count":False,"recording_equivalence_verified":False,"native_youtube_alignment_verified":False}
        _validate_result(record, item)
        records.append(record)
    journal = settings.root/"sync"/JOURNAL
    with base.kernel_lock(journal.with_suffix(".lock")):
        previous = (journal_index.refresh(journal) if journal_index is not None else
                    {(r.get("source_key"),r.get("run_id")):r for r in common.read_jsonl(journal)})
        for record in records:
            key = (record["source_key"],record["run_id"])
            if key in previous:
                need(previous[key] == record, "Append-only edition-ASR receipt conflict")
            else:
                common.append_jsonl(journal, record)
        with journal.open("ab") as handle:
            os.fsync(handle.fileno())
    return records


def local_bundle(root, job):
    record = job["record"]
    path = drive_ingest.local_path(root, "asr/results/edition-" + record["source"]["audio"]["sha256"] +
                                  "/" + record["run_id"] + "/" + record["run_id"] + ".zip")
    return path if path.is_file() else None


def recover_local_result(settings, origin, selection, proposal):
    """Recover a fully verified result across the ZIP rename and receipt-write boundaries."""
    parent = drive_ingest.local_path(settings.output_root, "edition-" + origin["audio"]["sha256"])
    files = sorted(parent.glob("asr-*/*.zip")) + sorted(parent.glob("asr-*/*.zip.part"))
    for path in files:
        path = drive_ingest.local_path(parent, path.relative_to(parent))
        run_id = path.parent.name
        pending = path.suffix == ".part"
        if not re.fullmatch(r"asr-[0-9a-f]{24}", run_id) or path.name != run_id + (".zip.part" if pending else ".zip"):
            continue
        try:
            verified = multi.verify_pair(path, max_bytes=batch.paired_limit(origin["duration_seconds"]))
        except (zipfile.BadZipFile, base.AsrError, KeyError, json.JSONDecodeError):
            if not pending:
                raise
            # A crash before the ZIP central directory was written leaves a partial file.
            # Keep it separate from both the durable windows and the next write attempt.
            path.rename(path.with_name(path.name + ".interrupted-" + str(time.time_ns())))
            continue
        p = verified["provenance"]
        if (p.get("profile") == PROFILE and p.get("inference_source") == origin
                and p.get("selection_sha256") == selection and p.get("proposal_sha256") == proposal
                and p["run_id"] == run_id):
            if pending:
                destination = path.with_suffix("")
                need(not destination.exists(), "Completed result appeared during recovery")
                path.rename(destination)
                path = destination
            return {"run_id":p["run_id"], "language_decision":p.get("language_decision") or {},
                    "bundle":{"path":str(path), **verified["bundle"]}}
    return None


def release_staged(root, origin, remote, checkpoint=None):
    cache=drive_ingest.local_path(root,"asr/input/edition-"+origin['audio']['sha256'])
    if cache.is_dir():
        for name in ('audio','metadata'):
            obj=origin[name]
            path=drive_ingest.local_path(cache,drive_ingest.remote_relative(remote,obj['remote']))
            if path.is_file():
                need(base.hashes(path)=={k:obj[k] for k in ('bytes','md5','sha256')},'Input changed before cleanup')
                path.unlink()
    if checkpoint is not None and checkpoint.is_file():checkpoint.unlink()


def run(settings, selection, expected, plan_path, proposal, drive, *, limit=1, runtime_factory=multi.Runtime,
        lease_maintenance=None, reviews=None, review_sha256=None, outstanding=None, prefetch=0,
        background_publish=False, english_loader=load_english, drive_slots=2, language_fallback=False,
        english_first=False, channel_language=False):
    """Run only after complete selected audio, held collector, bound plan, and explicit active GPU lease.

    With ``outstanding`` (the owner's exact list from ``authorized_outstanding``) every other
    selected recording is processed and the listed ones stay pending for a later run.
    ``prefetch`` inputs are fetched ahead and ``background_publish`` uploads results while the
    next recording is recognized; both leave every per-file check in place. ``drive_slots`` is how
    many Drive calls may run at once (each still paced by its own request limit).
    ``language_fallback`` applies the owner's policy for recordings whose probes held no clear
    speech (see ``fallback_language``): the creator's established language decides at once, and a
    last sweep uses English for creators with no detected language at all.
    ``channel_language`` transcribes a creator whose detected recordings are all English (at least
    two, and no published recording in another language) without probing each recording; ``english_first`` does those creators first, then the
    creators not yet known, and last the creators detected mostly in another language.
    """
    root = settings.root
    frame, scopes, actual = collection_coverage.mixed_selection(Path(selection), {})
    need(actual == expected, "Frozen recording selection changed")
    plan_path = base.within(common.ensure_outside_git(plan_path), root)
    raw = plan_path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == proposal, "ASR proposal changed")
    plan = json.loads(raw)
    need(plan.get("prior_speech_review_sha256") == review_sha256 and (not reviews or review_sha256),
         "Individual speech-review plan changed")
    need((limit is None or type(limit) is int and limit > 0) and plan.get("profile") == PROFILE and plan.get("selection_sha256") == expected and
         [r["video_id"] for r in frame] == [r["video_id"] for r in plan["rows"]], "Invalid frozen ASR proposal")
    remote = plan["remote"]
    snapshot, saved = collection_coverage.coverage(root, selection=selection, remote=remote)
    if outstanding is None:
        postrun_candidates.complete_frame(snapshot,saved,frame,scopes,expected)
    else:
        partial_frame(snapshot,saved,frame,scopes,expected,outstanding)
    def guard():
        if lease_maintenance is not None:
            lease_maintenance()
        lease = base.gpu_lease(settings)
        need(lease.get("input_frame_sha256") == proposal, "GPU lease belongs to a different ASR proposal")
        need((root/"sync/STOP_DRIVE_INGEST").is_file(), "Collector resumed")
        return lease
    results = []
    runtime = None
    unified=plan.get('source_scope')==ALL_SOURCES
    rolling_history = deque() if unified else None
    need(plan.get('source_scope') in (None,'qualified_and_publisher',ALL_SOURCES),'Unknown audio selection policy')
    with base.kernel_lock(root/"sync/asr_gpu_owner.lock"), offline_model_environment(root):
        lease = guard()
        budget=batch.StorageBudget(settings) if unified else None
        if budget is None:base.inventory(settings)
        else:budget.admit(0)
        inputs=catalogue_inputs(root,frame,remote)
        current = inventory(root, selection, expected, remote, include_native=unified,inputs=inputs,
                            reviews=reviews, review_sha256=review_sha256)
        groups = grouped_sources(plan, current, reviews=reviews, outstanding=outstanding or frozenset())
        prior_results = {audio_identity(j["edition"]):j for j in input_rows(root,frame,remote,sources=inputs[1],records=inputs[2])}
        journal_index=batch.PublicationIndex() if unified else None
        worker=worker_digest() if unified else None
        if unified:
            # The previous owner may have stopped between durable publication and local cleanup.
            for known in prior_results.values():
                origin=known['record']['inference_source']
                checkpoint=drive_ingest.local_path(root,'asr/jobs/edition-'+origin['audio']['sha256']+'/windows.sqlite')
                release_staged(root,origin,remote,checkpoint)
        model = None
        english_pin = english = None
        need(type(prefetch) is int and 0 <= prefetch <= 16 and type(drive_slots) is int and 2 <= drive_slots <= 8,
             "Invalid prefetch depth or Drive concurrency")
        usual_slots = drive_ingest._DRIVE_CALLS
        if drive_slots != 2:
            drive_ingest._DRIVE_CALLS = threading.BoundedSemaphore(drive_slots)
        staging = Staging(root, remote, drive, prefetch, max(2, drive_slots - 2)) if prefetch else None
        publications = Publications() if background_publish else None

        def admit(amount):
            if budget is None:
                base.inventory(settings, extra=amount)
            else:
                budget.admit(amount)

        # A creator's language is established by at least two detector decisions, four in five agreeing.
        votes = defaultdict(Counter)       # detector decisions
        taken = defaultdict(Counter)       # transcribed on the creator's language without probes: no vote, but part of the ratio
        spoken = defaultdict(Counter)      # every published language, whatever decided it

        def tally(channel, decision):
            if decision.get("status") != "accepted" or not decision.get("language"):
                return
            spoken[channel][decision["language"]] += 1
            if decision.get("basis") in DETECTOR_BASES:
                votes[channel][decision["language"]] += 1
            elif decision.get("policy") == CHANNEL_POLICY:
                taken[channel][decision["language"]] += 1

        for known in prior_results.values():
            tally(known["record"]["inference_source"]["channel_dir"], known["record"].get("language_decision") or {})

        def channel_choice(channel, last_sweep):
            if votes[channel]:
                cast = votes[channel] + taken[channel]
                language, count = cast.most_common(1)[0]
                decided = votes[channel][language] >= MIN_CREATOR_VOTES and count >= .8 * sum(cast.values())
                return (language, "creator_established_language") if decided else None
            return ("en", "owner_default_english") if last_sweep else None

        def english_creator(channel):
            cast = votes[channel]
            return cast["en"] >= MIN_CREATOR_VOTES and set(cast) == {"en"} and set(spoken[channel]) == {"en"}

        if english_first:
            def tier(group):
                cast = votes[group[0]["channel_dir"]]
                if english_creator(group[0]["channel_dir"]):
                    return 0
                return 2 if cast and cast.most_common(1)[0][0] != "en" else 1
            groups = sorted(groups, key=tier)       # stable: the proposal's order holds within each tier

        def needs_input(candidates):
            """A coming recording whose audio will be read: nothing saved, held or individually reviewed."""
            first = candidates[0]
            name = "edition-" + first["audio"]["sha256"]
            saved = drive_ingest.local_path(settings.output_root, name)
            return (not gpu_asr_review.matches((reviews or {}).get(first["video_id"]), first)
                    and audio_identity(first) not in prior_results
                    and not drive_ingest.local_path(root, "asr/jobs/" + name + "/language-review.json").is_file()
                    and not (saved.is_dir() and any(saved.glob("asr-*/*.zip*"))))

        try:
            sweeps = [(False, position, group) for position, group in enumerate(groups)]
            if language_fallback:
                sweeps += [(True, position, group) for position, group in enumerate(groups)]
            for last_sweep, position, associations in sweeps:
                if publications is not None:
                    publications.collect(results, wait=False)
                if limit is not None and len(results) + (len(publications.pending) if publications else 0) >= limit:
                    break
                origin = associations[0]
                review = (reviews or {}).get(origin["video_id"])
                if not gpu_asr_review.matches(review, origin):
                    review = None
                key = "edition-" + origin["audio"]["sha256"]
                pending = drive_ingest.local_path(root, "asr/jobs/" + key + "/pending.json")
                checkpoint=pending.with_name('windows.sqlite') if unified else None
                language_hold = pending.with_name("language-review.json")
                previous = base.read_json(language_hold) if language_hold.is_file() else {}
                same_review = previous.get("individual_speech_review_sha256") == (review or {}).get("source_review_sha256")
                held = (previous.get("proposal_sha256") == proposal or same_review and
                        previous.get("status") in ("language_review", "source_review") and previous.get("source") == origin)
                policy = {"channel": channel_choice(origin["channel_dir"], last_sweep)} if language_fallback else None
                prior_decision = None
                if held:
                    # A recording held for unclear probes is taken up again once the policy can name its language.
                    if (policy is None or previous.get("status") != "language_review" or previous.get("source") != origin
                            or fallback_language(previous.get("decision") or {}, policy["channel"]) is None):
                        continue
                    prior_decision = previous["decision"]
                elif last_sweep:
                    continue                      # the last sweep is only for recordings still held
                guard()
                existing = None
                known = prior_results.get(audio_identity(origin))
                if known:
                    existing = proof(known["record"])
                    bundle_path = local_bundle(root, known)
                    if bundle_path is None:
                        cache = drive_ingest.local_path(root, "asr/results/edition-bundle-cache")
                        cache.mkdir(parents=True, exist_ok=True)
                        rel = drive_ingest.remote_relative(remote, existing["remote"])
                        bundle_path = drive_ingest.local_path(cache, rel)
                        if not bundle_path.exists():
                            from . import stage_archived_text
                            if budget is None:base.inventory(settings,extra=2*existing['bytes'])
                            else:budget.admit(2*existing['bytes'])
                            stage_archived_text.fetch_batch(drive,remote,cache,{rel:existing})
                    local = {"bundle":{**existing,"path":str(bundle_path)}, "run_id":known["record"]["run_id"]}
                else:
                    local = recover_local_result(settings, origin, expected, proposal)
                    if local is None:
                        if model is None:
                            model = multi.model_proof(settings)
                            need(all(lease.get("model",{}).get(k) == model[k] for k in
                                     ("repository","revision","model_sha256")), "GPU lease binds a different offline model")
                            english_pin = english_model(settings, lease)
                        input_bytes=sum(origin[k]['bytes'] for k in ('audio','metadata'))
                        if budget is None:base.inventory(settings,extra=input_bytes+3*base.MAX_RESULT_BYTES)
                        else:budget.admit(input_bytes+5*batch.paired_limit(origin['duration_seconds']))
                        if staging is not None:
                            staging.ahead([g[0] for g in groups[position+1:position+1+4*prefetch] if needs_input(g)], admit)
                        paths = (gpu_asr_review.retained_pair(root, review) if review else None) or (
                            staging.take(origin) if staging is not None else staged_pair(root, origin, remote, drive))
                        if runtime is None:
                            streams = lease.get("parallel_windows", 1)
                            runtime = runtime_factory(replace(settings, model_workers=streams)
                                                      if streams > 1 and is_dataclass(settings) else settings, lease)
                            if english_pin is not None:
                                english = (english_pin[0], english_loader(english_pin[1], english_pin[2]), english_pin[2])
                        options = ({"checkpoint_path": checkpoint, "capacity_check": budget.physical, "worker_sha": worker,
                                    "metadata_path": paths["metadata"], "rolling_history": rolling_history, "review": review} if unified else {})
                        if english is not None:
                            options["english"] = english
                        if lease.get("parallel_windows", 1) > 1 and is_dataclass(settings):
                            options["parallel_windows"] = lease["parallel_windows"]
                        if policy is not None:
                            options.update(language_fallback=policy, prior_decision=prior_decision)
                        if channel_language and prior_decision is None and english_creator(origin["channel_dir"]):
                            options["channel_language"] = {"language":"en", "votes":votes[origin["channel_dir"]]["en"]}
                        try:
                            local = infer(settings, origin, paths["audio"], runtime, model, proposal, expected, guard, **options)
                        except base.AsrError as error:
                            if not unified or error.kind not in SOURCE_REVIEW_ERRORS:
                                raise
                            local = {"status": "source_review", "reason": error.kind}
                        if local.get("status") in ("language_review", "source_review"):
                            evidence = {"individual_speech_review_sha256": review["source_review_sha256"],
                                        "retained_input_paths": {key:str(path) for key,path in paths.items()}} if review else {}
                            batch.write_review(language_hold, {**local, **evidence, "source": origin, "proposal_sha256": proposal})
                            if unified and review is None:
                                release_staged(root,origin,remote,checkpoint)
                            results.append({"video_ids":[x["video_id"] for x in associations], "state":local["status"]})
                            continue
                tally(origin["channel_dir"], local.get("language_decision") or {})
                if prior_decision is not None and language_hold.is_file():
                    language_hold.replace(language_hold.with_name("language-review.resolved-by-policy.json"))
                guard()

                def finish(local=local, associations=associations, existing=existing, checkpoint=checkpoint):
                    recorded = publish(settings,local,associations,drive,existing_remote=existing,journal_index=journal_index)
                    release_staged(root,recorded[0]['inference_source'],remote,checkpoint)
                    return recorded

                if publications is None:
                    recorded = finish()
                    results.append({"state":"verified","video_ids":[x["video_id"] for x in recorded],"run_id":local["run_id"]})
                else:
                    publications.submit(finish, local["run_id"])
            if publications is not None:
                publications.collect(results, wait=True)
        finally:
            try:
                if staging is not None:
                    staging.close()
                if publications is not None:
                    publications.close()
            finally:
                drive_ingest._DRIVE_CALLS = usual_slots
                if runtime is not None:
                    runtime.close()
    return results


def text_views(path, job):
    record, item = job["record"], job["edition"]
    _validate_result(record, item)
    _, parsed, parts = corpus_asr_view._parts(path, {"output_contract":multi.CONTRACT, "bundle":record},
                                             paired_max_bytes=batch.paired_limit(record['inference_source']['duration_seconds']))
    p = parsed["provenance"]
    origin = record["inference_source"]
    need(parsed["artifact_manifest_sha256"] == record["artifact_manifest_sha256"] and
         p["profile"] == PROFILE and p["inference_source"] == origin and p["source_audio"] == origin["audio"] and
         p["source_metadata"] == origin["metadata"] and p["source_timebase"] == origin["source_timebase"] and
         p["source_key"] == origin["source_key"] and p["source_admission_sha256"] ==
         digest([record["selection_sha256"],record["proposal_sha256"],origin]) and
         all(record[k] == p[k] for k in ("run_id","text_variants","selection_sha256","proposal_sha256","language_decision")),
         "ASR ZIP and published association disagree")
    views = {}
    adapter = base.hashes(Path(__file__))["sha256"]
    for name, descriptor in p["text_variants"].items():
        canonical = descriptor.get("same_as",name)
        member = canonical+"/segments.json"
        text = parts[canonical+"/transcript.txt"].decode("utf8")
        document = json.loads(parts[member])
        rows = corpus_asr_view._segments(document,text,descriptor["language"],origin["duration_seconds"])
        segments = [{"cue_index":i,"char_start":r["char_start"],"char_end":r["char_end"], "raw_segment_id":r["id"],
                    "source_segment_id":f"{member}:{r['id']}", "source_member":member, "time_start":r["start"],
                    "time_end":r["end"],"words":deepcopy(r.get("words",[]))} for i,r in enumerate(rows)]
        translated = descriptor["text_kind"] == "english_audio_translation"
        views[name] = {"schema_version":1, "video_id":item["video_id"],"channel_dir":item["channel_dir"],
            "text_version_id":digest([PROFILE,record["sha256"],item["source_key"],member,adapter]),
            "run_id":p["run_id"],"track_id":p["run_id"]+":"+name, "variant":name,"canonical_variant":canonical,
            "source_kind":(KIND_ENGLISH if translated else KIND_ORIGINAL)[item["source_type"]],
            "language":descriptor["language"],"original_language":p["language_decision"]["language"],
            "translation_performed":translated, "translation_semantics_verified":False, "text_kind":descriptor["text_kind"],
            "bundle_sha256":record["sha256"],"raw_sha256":hashlib.sha256(parts[member]).hexdigest(),
            "text_sha256":hashlib.sha256(text.encode()).hexdigest(),"text":text,"segments":segments,"raw_segments":document,
            "offset_unit":"unicode_codepoint","normalization_version":corpus_asr_view.NORMALIZATION,
            "source_timebase":item["source_timebase"],"inference_timebase":origin["source_timebase"],
            "source_edition_id":"sha256:"+item["audio"]["sha256"],"source_audio_sha256":item["audio"]["sha256"],
            "edition_receipt_sha256":item["source_receipt_sha256"],"source_audio":item["audio"],"source_metadata":item["metadata"],
            "associated_source_key":item["source_key"],"inference_source_key":origin["source_key"],
            "recording_association_method":item["recording_association_method"],"artifact_manifest_sha256":parsed["artifact_manifest_sha256"],
            "duration_seconds":origin["duration_seconds"],"known_cue_union_seconds":corpus_caption_view.timed_union(rows),
            "cue_time_kind":"model_estimated_segment_spans","word_times_are_model_estimates":True,
            "native_youtube_alignment_verified":False,"recording_equivalence_verified":False,"speech_coverage_verified":False,
            "quality_state":"unreviewed_asr","human_reviewed":False,"speaker_attribution":None,"view_adapter_sha256":adapter}
    return views


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    inspect = commands.add_parser("inventory", help="read only local selection and receipt indexes")
    execute = commands.add_parser("run", help="process a completed frozen selection with an exclusive CUDA lease")
    for cmd in (inspect,execute):
        cmd.add_argument("--root", required=True,type=Path)
        cmd.add_argument("--selection", required=True,type=Path)
        cmd.add_argument("--selection-sha256", required=True)
        cmd.add_argument("--plan",required=True,type=Path)
        cmd.add_argument("--speech-review",type=Path,help="dated individual prior-hold assessments")
        cmd.add_argument("--speech-review-sha256")
    inspect.add_argument("--remote", default=status.DEFAULT_REMOTE)
    inspect.add_argument("--editions-only",action="store_true",help="leave native recordings in the separate historical queue")
    execute.add_argument("--plan-sha256",required=True)
    execute.add_argument("--model-dir",required=True,type=Path)
    execute.add_argument("--model-receipt",required=True,type=Path)
    execute.add_argument("--environment-lock",type=Path,default=base.DEFAULT_LOCK)
    execute.add_argument("--managed-root",type=Path,action="append",required=True)
    execute.add_argument("--gpu-lease-id",required=True)
    execute.add_argument("--gpu-owner",required=True)
    execute.add_argument("--rclone",default="rclone")
    execute.add_argument("--rclone-config",type=Path)
    execute.add_argument("--limit",type=int,help="stop after this many newly verified or newly reviewed audio groups; default drains the proposal")
    execute.add_argument("--authorized-outstanding",type=Path,
                         help="owner's dated list of selected recordings that have no archived audio yet; all others are processed")
    execute.add_argument("--authorized-outstanding-sha256")
    execute.add_argument("--prefetch",type=int,default=0,help="fetch this many coming inputs while the current one is recognized (0 to 16)")
    execute.add_argument("--drive-slots",type=int,default=2,help="Drive calls that may run at once (2 to 8)")
    execute.add_argument("--background-publish",action="store_true",help="upload and verify results while the next recording is recognized")
    execute.add_argument("--language-fallback",action="store_true",
                         help="for unclear probes use one strong probe, else the creator's established language, else English in a last sweep")
    execute.add_argument("--channel-language",action="store_true",
                         help="transcribe creators whose detected recordings are all English without probing each recording")
    execute.add_argument("--english-first",action="store_true",
                         help="do creators established as English first, then unknown creators, then other languages")
    args = parser.parse_args(argv)
    root = common.ensure_outside_git(args.root)
    need(bool(args.speech_review) == bool(args.speech_review_sha256), "Supply both speech-review path and digest")
    need(bool(getattr(args,"authorized_outstanding",None)) == bool(getattr(args,"authorized_outstanding_sha256",None)),
         "Supply both the outstanding-recording authorization path and digest")
    reviews = (gpu_asr_review.read_plan(root,args.speech_review,args.speech_review_sha256,args.selection_sha256)
               if args.speech_review else None)
    if args.action == "inventory":
        plan = inventory(root,args.selection,args.selection_sha256,args.remote,include_native=not args.editions_only,
                         reviews=reviews,review_sha256=args.speech_review_sha256)
        destination = base.within(common.ensure_outside_git(args.plan),root)
        raw = base.encoded(plan)
        if destination.exists():
            need(destination.read_bytes() == raw, "ASR inventory changed; use a new proposal path")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
        print(json.dumps({"counts":plan["counts"],"eligible_by_source":plan["eligible_by_source"],"proposal_sha256":hashlib.sha256(raw).hexdigest()}))
        return 0
    settings = base.Settings(root,args.model_dir,args.model_receipt,args.gpu_lease_id,args.gpu_owner,
                             drive_ingest.managed_roots(root,args.managed_root),args.environment_lock)
    drive = drive_ingest.Rclone(args.rclone,args.rclone_config,root/"sync/drive_cooldown.json")
    outstanding = None
    if args.authorized_outstanding:
        frame = collection_coverage.mixed_selection(Path(args.selection), {})[0]
        outstanding = authorized_outstanding(root,args.authorized_outstanding,args.authorized_outstanding_sha256,
                                             args.selection_sha256,frame)
    result = run(settings,args.selection,args.selection_sha256,args.plan,args.plan_sha256,drive,limit=args.limit,
                 reviews=reviews,review_sha256=args.speech_review_sha256,outstanding=outstanding,
                 prefetch=args.prefetch,background_publish=args.background_publish,drive_slots=args.drive_slots,
                 language_fallback=args.language_fallback,english_first=args.english_first,
                 channel_language=args.channel_language)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
