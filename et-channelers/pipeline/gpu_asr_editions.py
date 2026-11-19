"""Private post-collection CUDA transcription of specific archived audio editions.

Inventory reads existing receipts. Execution requires a completed selection, the
same source-verified proposal, the existing unpaused GPU lease, and its model.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re

from . import (collection_coverage, common, corpus_asr_view, corpus_caption_view, corpus_publisher_variant_view,
               drive_ingest, gpu_asr as base, gpu_asr_multilingual as multi, ingestion_status as status,
               postrun_candidates, qualified_direct_audio_receipts, qualified_edition_receipts)

PROFILE = "postrun_verified_audio_editions_v1"
RESULT = "verified_edition_asr"
JOURNAL = "edition_asr_manifest.jsonl"
PROOF = ("remote", "drive_id", "bytes", "md5", "sha256")
PUBLISHER = "publisher_audio_edition"
EXTRACT = "qualified_youtube_audio_extract"
DIRECT = "qualified_youtube_direct_audio"
SOURCE_ORDER = (DIRECT, EXTRACT, PUBLISHER)
KIND_ORIGINAL = {DIRECT: "qualified_youtube_original_asr", EXTRACT: "qualified_youtube_original_asr",
                 PUBLISHER: "publisher_original_asr"}
KIND_ENGLISH = {DIRECT: "qualified_youtube_english_audio_translation", EXTRACT: "qualified_youtube_english_audio_translation",
                PUBLISHER: "publisher_english_audio_translation"}


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
             "source_timebase":"publisher_audio_seconds" if job_type == PUBLISHER else "qualified_youtube_audio_seconds",
             "recording_association_method":method, "source_receipt_sha256":digest(record)}
    value["source_key"] = digest({k:value[k] for k in ("video_id","channel_dir","tab","source_type","source_variant_id","audio","metadata")})
    return value


def source_catalogue(root, frame, remote):
    rows = {r["video_id"]:r for r in frame}
    found = defaultdict(dict)
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
         and all(record.get(k) is False for k in ("native_youtube_bytes","changes_native_asr_count",
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


def input_rows(root, frame, remote):
    root = Path(root)
    records = common.read_jsonl(root/"sync"/JOURNAL)
    if not records:
        return
    frame = list(frame)
    sources = source_catalogue(root, frame, remote)
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


def inventory(root, selection, expected, remote=status.DEFAULT_REMOTE):
    """Join one pinned roster to real audio receipts, existing English text and the native queue."""
    from . import stage_archived_text
    root = common.ensure_outside_git(root)
    frame, _, pin = collection_coverage.mixed_selection(Path(selection), {})
    need(pin == expected, "The frozen selection changed")
    sources = source_catalogue(root, frame, remote)
    native = status.latest_records(root/"sync/drive_ingest_manifest.jsonl")
    text = defaultdict(set)
    for job in stage_archived_text.input_rows(root, frame, remote):
        if job["kind"] == corpus_publisher_variant_view.CAPTION:
            if job["item"].get("track_key") is None:  # RSS-channel language alone cannot establish an English track.
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
        candidates = sorted(sources.get(video,{}).values(), key=lambda s:(SOURCE_ORDER.index(s["source_type"]),
                          s["recording_association_method"] == "publisher_owner_title_date_duration", s["source_key"]))
        disposition = ("existing_english_text" if text[video] and (has_native or candidates) else "existing_native_queue" if has_native
                       else "edition_asr_eligible" if candidates else "audio_missing")
        records.append({"video_id":video,"channel_dir":row["channel_dir"],"tab":row["tab"],"status":disposition,
                        "existing_text_kinds":sorted(text[video]),"native_audio_verified":bool(has_native),
                        "verified_edition_sources":[c["source_type"] for c in candidates],
                        "selected_source":candidates[0] if disposition == "edition_asr_eligible" else None})
    return {"schema_version":1,"profile":PROFILE,"selection_sha256":pin,"remote":remote,"rows":records,
            "counts":dict(Counter(r["status"] for r in records)),
            "eligible_by_source":dict(Counter(r["selected_source"]["source_type"] for r in records if r["selected_source"])),
            "source_timebases":dict(Counter(r["selected_source"]["source_timebase"] for r in records if r["selected_source"])),
            "selected_recordings":len(records)}


def audio_identity(item):
    audio = item["audio"]
    return audio["sha256"], audio["bytes"], audio["md5"]


def result_remote(item, run_id):
    return item["audio"]["remote"].rpartition("/")[0] + f"/ASR/{run_id}/{run_id}.zip"


def grouped_sources(plan, current):
    """Keep one inference per exact audio object content; retain each selected recording's proof."""
    fresh = {row["video_id"]: row for row in current["rows"]}
    groups = defaultdict(list)
    for row in plan["rows"]:
        source = row["selected_source"]
        if source is None:
            continue
        actual = fresh.get(row["video_id"])
        need(actual is not None, "Video outside the pinned selection")
        if actual["status"] in ("existing_native_queue", "existing_english_text"):
            continue
        need(actual["selected_source"] == source, "Archived input or recording association changed; refresh the plan")
        groups[audio_identity(source)].append(source)
    return [sorted(items, key=lambda x: (bool(x.get("canonical_associated_youtube_id")), x["video_id"], x["source_key"]))
            for items in groups.values()]


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
    stage_archived_text.fetch_batch(drive, remote, cache, needed)
    for name, path in files.items():
        result = base.hashes(path)
        need(all(result[k] == origin[name][k] for k in result), "Staged edition source hash mismatch")
    return files


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


def infer(settings, origin, audio_path, runtime, model, proposal, selection, guard):
    """Transcribe original speech, translate non-English speech; both use the inference edition's clock."""
    need(runtime.model.model.device == "cuda" and runtime.model.model.compute_type == "int8_float16", "CUDA model required")
    lease = base.gpu_lease(settings)
    monitor = multi.Monitor(runtime, guard, lease["rolling_utilization_target"] * 100, lease["max_vram_bytes"])
    job = {"duration_seconds":origin["duration_seconds"], "declared_audio_language":"und", "metadata_content_flags":{}}
    start = base.now()
    try:
        monitor.begin()
        decision = multi.detect_language(runtime, audio_path, job, monitor.guard)
        if decision["status"] != "accepted":
            return {"status":"language_review", "decision":decision, "audio_identity":audio_identity(origin)}
        language = decision["language"]
        configs = {"original": {**base.CONFIG, "language":language, "task":"transcribe"}}
        if language != "en":
            configs["english"] = {**base.CONFIG, "language":language, "task":"translate"}
        variants, metrics = {}, {}
        for key, config in configs.items():
            monitor.guard()
            segments, transcript, voiced = base.collect_segments(multi.TaskRuntime(runtime,config), audio_path,
                                                                origin["duration_seconds"], monitor.guard)
            segments.update(language=language if key == "original" else "en", character_offset_unit="unicode_code_points",
                            text_kind="original_asr" if key == "original" else "english_audio_translation")
            variants[key] = (segments, transcript, config)
            metrics[key] = {"duration_after_vad_seconds":voiced, "segments":len(segments["segments"])}
    finally:
        telemetry = monitor.finish()
    guard()
    worker = digest([base.hashes(Path(m.__file__))["sha256"] for m in (base, multi)] + [base.hashes(Path(__file__))["sha256"]])
    identity = {"output_contract":multi.CONTRACT, "profile":PROFILE, "source_audio":origin["audio"],
            "source_metadata":origin["metadata"], "source_key":origin["source_key"], "source_timebase":origin["source_timebase"],
            "selection_sha256":selection, "model":model, "proposal_sha256":proposal, "worker_sha256":worker,
            "environment_lock_sha256":base.hashes(settings.environment_lock)["sha256"], "configs":configs}
    run_id = "asr-" + base.fingerprint(identity)[:24]
    admission = {"video_id":"edition-"+origin["audio"]["sha256"], "job_id":origin["source_key"],
                 "source_lease_id":settings.gpu_lease_id, "job":{"audio":origin["audio"], "metadata":origin["metadata"]}}
    provenance = {**identity, "schema_version":1, "identity":identity, "run_id":run_id,
            "source_video_id":origin["video_id"], "channel_dir":origin["channel_dir"], "inference_source":origin,
            "language_decision":decision, "started_at":start, "finished_at":base.now(),
            "source_admission_sha256":digest([selection,proposal,origin]),
            "compute":{"device":"cuda:0", "compute_type":"int8_float16", "cpu_asr_fallback":False,
                       "model_workers":1, "batch_size":1, "gpu_lease_id":settings.gpu_lease_id},
            "metrics":{"audio_seconds":origin["duration_seconds"], "tasks":metrics}, "dependencies":runtime.dependencies,
            "quality":{"accuracy_claimed":False,"human_reviewed":False,"speech_coverage_validated":False,
                       "translation_semantics_human_verified":False,"word_times_are_model_estimates":True,
                       "native_youtube_alignment_verified":False}}
    return multi.write_pair(settings, admission, run_id, variants, telemetry, provenance)


def publish(settings, local_receipt, associations, drive, *, existing_remote=None):
    path = base.within(local_receipt["bundle"]["path"], settings.output_root)
    verified = multi.verify_pair(path, local_receipt["bundle"])
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
            "language_decision":p["language_decision"], "quality_state":"unreviewed_asr", "native_youtube_bytes":False,
            "changes_native_asr_count":False,"recording_equivalence_verified":False,"native_youtube_alignment_verified":False}
        _validate_result(record, item)
        records.append(record)
    journal = settings.root/"sync"/JOURNAL
    with base.kernel_lock(journal.with_suffix(".lock")):
        previous = {(r.get("source_key"),r.get("run_id")):r for r in common.read_jsonl(journal)}
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
    """Recover the verified ZIP even after a crash between ZIP rename and atomic receipt writes."""
    parent = drive_ingest.local_path(settings.output_root, "edition-" + origin["audio"]["sha256"])
    for path in sorted(parent.glob("asr-*/*.zip")):
        path = drive_ingest.local_path(parent,path.relative_to(parent))
        verified = multi.verify_pair(path)
        p = verified["provenance"]
        if (p.get("profile") == PROFILE and p.get("inference_source") == origin
                and p.get("selection_sha256") == selection and p.get("proposal_sha256") == proposal
                and path.name == p["run_id"] + ".zip" and path.parent.name == p["run_id"]):
            return {"run_id":p["run_id"], "bundle":{"path":str(path), **verified["bundle"]}}
    return None


def run(settings, selection, expected, plan_path, proposal, drive, *, limit=1, runtime_factory=multi.Runtime):
    """Run only after complete selected audio, held collector, bound plan, and explicit active GPU lease."""
    root = settings.root
    frame, scopes, actual = collection_coverage.mixed_selection(Path(selection), {})
    need(actual == expected, "Frozen recording selection changed")
    plan_path = base.within(common.ensure_outside_git(plan_path), root)
    raw = plan_path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == proposal, "ASR proposal changed")
    plan = json.loads(raw)
    need(0 < limit <= 20 and plan.get("profile") == PROFILE and plan.get("selection_sha256") == expected and
         [r["video_id"] for r in frame] == [r["video_id"] for r in plan["rows"]], "Invalid frozen ASR proposal")
    remote = plan["remote"]
    snapshot, saved = collection_coverage.coverage(root, selection=selection, remote=remote)
    postrun_candidates.complete_frame(snapshot,saved,frame,scopes,expected)
    def guard():
        lease = base.gpu_lease(settings)
        need(lease.get("input_frame_sha256") == proposal, "GPU lease belongs to a different ASR proposal")
        need((root/"sync/STOP_DRIVE_INGEST").is_file(), "Collector resumed")
        return lease
    results = []
    runtime = None
    with base.kernel_lock(root/"sync/asr_gpu_owner.lock"), offline_model_environment(root):
        lease = guard()
        base.inventory(settings)
        current = inventory(root, selection, expected, remote)
        groups = grouped_sources(plan, current)
        prior_results = {audio_identity(j["edition"]):j for j in input_rows(root,frame,remote)}
        model = None
        try:
            for associations in groups:
                if len(results) >= limit:
                    break
                origin = associations[0]
                key = "edition-" + origin["audio"]["sha256"]
                pending = drive_ingest.local_path(root, "asr/jobs/" + key + "/pending.json")
                language_hold = pending.with_name("language-review.json")
                if language_hold.is_file() and base.read_json(language_hold).get("proposal_sha256") == proposal:
                    continue
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
                            base.inventory(settings, extra=2*existing["bytes"])
                            stage_archived_text.fetch_batch(drive,remote,cache,{rel:existing})
                    local = {"bundle":{**existing,"path":str(bundle_path)}, "run_id":known["record"]["run_id"]}
                else:
                    local = recover_local_result(settings, origin, expected, proposal)
                    if local is None:
                        if model is None:
                            model = multi.model_proof(settings)
                            need(all(lease.get("model",{}).get(k) == model[k] for k in
                                     ("repository","revision","model_sha256")), "GPU lease binds a different offline model")
                        base.inventory(settings, extra=sum(origin[k]["bytes"] for k in ("audio","metadata"))+3*base.MAX_RESULT_BYTES)
                        paths = staged_pair(root, origin, remote, drive)
                        if runtime is None:
                            runtime = runtime_factory(settings,lease)
                        local = infer(settings,origin,paths["audio"],runtime,model,proposal,expected,guard)
                        if local.get("status") == "language_review":
                            base.atomic_json(language_hold, {**local, "source":origin, "proposal_sha256":proposal})
                            results.append({"video_ids":[x["video_id"] for x in associations], "state":"language_review"})
                            continue
                guard()
                recorded = publish(settings,local,associations,drive,existing_remote=existing)
                # A prior process may have published the result after writing pending.
                origin = recorded[0]["inference_source"]
                cache = drive_ingest.local_path(root, "asr/input/edition-" + origin["audio"]["sha256"])
                for name in ("audio","metadata"):
                    obj = origin[name]
                    path = drive_ingest.local_path(cache, drive_ingest.remote_relative(remote,obj["remote"]))
                    if path.is_file():
                        need(base.hashes(path) == {k:obj[k] for k in ("bytes","md5","sha256")}, "Input changed before cleanup")
                        path.unlink()
                results.append({"state":"verified","video_ids":[x["video_id"] for x in recorded],"run_id":local["run_id"]})
        finally:
            if runtime is not None:
                runtime.close()
    return results


def text_views(path, job):
    record, item = job["record"], job["edition"]
    _validate_result(record, item)
    _, parsed, parts = corpus_asr_view._parts(path, {"output_contract":multi.CONTRACT, "bundle":record})
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
    inspect.add_argument("--remote", default=status.DEFAULT_REMOTE)
    execute.add_argument("--plan-sha256",required=True)
    execute.add_argument("--model-dir",required=True,type=Path)
    execute.add_argument("--model-receipt",required=True,type=Path)
    execute.add_argument("--environment-lock",type=Path,default=base.DEFAULT_LOCK)
    execute.add_argument("--managed-root",type=Path,action="append",required=True)
    execute.add_argument("--gpu-lease-id",required=True)
    execute.add_argument("--gpu-owner",required=True)
    execute.add_argument("--rclone",default="rclone")
    execute.add_argument("--rclone-config",type=Path)
    execute.add_argument("--limit",type=int,default=1)
    args = parser.parse_args(argv)
    root = common.ensure_outside_git(args.root)
    if args.action == "inventory":
        plan = inventory(root,args.selection,args.selection_sha256,args.remote)
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
                             args.managed_root,args.environment_lock)
    drive = drive_ingest.Rclone(args.rclone,args.rclone_config,root/"sync/drive_cooldown.json")
    result = run(settings,args.selection,args.selection_sha256,args.plan,args.plan_sha256,drive,limit=args.limit)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
