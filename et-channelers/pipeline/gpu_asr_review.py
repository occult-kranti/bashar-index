"""Edition-bound re-evaluation of previously inconclusive speech/language probes."""
import hashlib
import json
import math
from pathlib import Path

from . import drive_ingest, gpu_asr as base, gpu_asr_multilingual as multi


def read_plan(root, path, expected_sha256, selection_sha256):
    """Bind every admitted review to an existing individual hold and its audio/metadata pair."""
    raw = base.within(path, root).read_bytes()
    base.require(hashlib.sha256(raw).hexdigest() == expected_sha256, "review_plan_hash")
    plan = json.loads(raw)
    base.require(plan.get("schema_version") == 1 and plan.get("selection_sha256") == selection_sha256,
                 "review_plan_selection")
    accepted = {}
    for row in plan["recordings"]:
        video = row["video_id"]
        if row["status"] == "reviewed_no_spoken_content":
            continue
        base.require(row["status"] == "needs_post_collection_lexical_review" and video not in accepted
                     and row["selection_sha256"] == selection_sha256 and row["edition"] == "native_youtube_audio",
                     "invalid_review_candidate")
        prior = row["existing_hold"]
        path = drive_ingest.local_path(root, prior["path"])
        old = path.read_bytes()
        base.require(hashlib.sha256(old).hexdigest() == prior["sha256"] and len(old) == prior["bytes"], "review_hold_changed")
        hold = json.loads(old)
        base.require(hold.get("video_id") == video and hold.get("status") == hold["decision"].get("status") == "held"
                     and hold.get("semantic_text_generated") is False
                     and hold.get("source_audio_sha256") == row["audio"]["sha256"]
                     and hold.get("source_audio_drive_id") == row["audio"]["drive_id"]
                     and hold["decision"]["reason"] == row["prior_hold_reason"]
                     and row["prior_hold_reason"] in {"no_reliable_speech","language_confidence_insufficient",
                                                      "mixed_or_conflicting_language","metadata_detection_conflict"},
                     "review_hold_not_bound_to_this_audio")
        accepted[video] = {"channel_dir":row["channel_dir"],"audio":row["audio"],"metadata":row["metadata"],
                           "retained_audio":row.get("retained_audio"),"retained_metadata":row.get("retained_metadata"),
                           "source_review_sha256":base.fingerprint(row),"reason":row["prior_hold_reason"]}
    return accepted


def matches(review, source):
    return bool(review and source["source_type"] == "native_youtube_audio"
                and source["channel_dir"] == review["channel_dir"]
                and source["audio"] == review["audio"] and source["metadata"] == review["metadata"])


def retained_pair(root, review):
    """Open archived local copies only if both named objects still match their verified proofs."""
    paths = {}
    for key in ("audio","metadata"):
        relative = review["retained_" + key]
        if not relative:
            return None
        path = drive_ingest.local_path(root,relative)
        if not path.is_file():
            return None
        observed = base.hashes(path)
        base.require(all(review[key][k] == value for k,value in observed.items()), "retained_review_source_changed")
        paths[key] = path
    return paths


def relaxed_speech(runtime, audio):
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    spans = get_speech_timestamps(audio, VadOptions(threshold=.35, min_silence_duration_ms=500))
    parts = [audio[s["start"]:s["end"]] for s in spans]
    voiced = runtime.np.concatenate(parts) if parts else runtime.np.empty(0,dtype=runtime.np.float32)
    return voiced, len(voiced) / base.SAMPLE_RATE


def scan_language(runtime, path, job, guard, *, relaxed=relaxed_speech):
    """Examine disjoint ten-second intervals through the actual decoder EOF, including quiet edges."""
    probes = []
    samples = 0
    for start, audio in runtime.windows(path, job["duration_seconds"]):
        base.require(abs(start - samples / base.SAMPLE_RATE) < .001, "review_window_timebase")
        for off in range(0, len(audio), 10 * base.SAMPLE_RATE):
            guard()
            chunk = audio[off:off+10*base.SAMPLE_RATE]
            speech, seconds = runtime.speech(chunk)
            strict_seconds = seconds
            mode = "standard"
            if seconds < multi.MIN_SPEECH_SECONDS and len(chunk) >= multi.MIN_SPEECH_SECONDS * base.SAMPLE_RATE:
                alternative, relaxed_seconds = relaxed(runtime,chunk)
                if relaxed_seconds > seconds:
                    speech, seconds, mode = alternative, relaxed_seconds, "sensitive"
            row = {"start":start+off/base.SAMPLE_RATE,"duration_seconds":len(chunk)/base.SAMPLE_RATE,
                   "speech_seconds":seconds,"standard_vad_seconds":strict_seconds,"used_vad":mode,
                   "language":None,"probability":0.0,"margin":0.0}
            if seconds >= multi.MIN_SPEECH_SECONDS:
                guard()
                language, probability, scores = runtime.detect(speech)
                others = [float(p) for candidate,p in scores if candidate != language]
                row.update(language=language,probability=float(probability),margin=float(probability)-max(others,default=0.0))
                base.require(all(math.isfinite(row[k]) for k in ("probability","margin"))
                             and 0 <= row["probability"] <= 1, "language_probability_invalid")
            probes.append(row)
        samples += len(audio)
    base.require(samples > 0 and abs(samples/base.SAMPLE_RATE-job["duration_seconds"]) <= 2, "review_decode_incomplete")
    decision = multi.decide_language(job,probes)
    strong = [p for p in probes if p["speech_seconds"] >= multi.MIN_SPEECH_SECONDS
              and p["probability"] >= multi.MIN_PROBABILITY and p["margin"] >= multi.MIN_MARGIN]
    only_sensitive = bool(strong) and all(p["used_vad"] == "sensitive" for p in strong)
    if decision["status"] == "accepted" and only_sensitive and (len(strong) < 3 or sum(p["speech_seconds"] for p in strong) < 8):
        decision = {"status":"held","reason":"insufficient_independent_sensitive_speech_evidence"}
    return {**decision,"probes":probes,"probe_method":"all_disjoint_10_second_intervals_standard_then_sensitive",
            "fully_scanned_samples":samples,"fully_scanned_seconds":samples/base.SAMPLE_RATE,
            "only_sensitive_strong_probes":only_sensitive,"human_verified":False,
            "no_speech_finding_established":False}
