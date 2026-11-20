"""Schedule project-funded text research after private audio and local speech completion."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

from . import collection_coverage, common, drive_ingest, gpu_asr, postrun_candidates, research_agent_budget
from . import research_agent_evidence as packets, research_agents as agents, stage_archived_text, study_schedule


HOME = Path("research/project-text-agents")
SETUP = "settings.json"
METHODS = ("study-design", "source-audit")
ROUND_ONE = ("corpus-statistics", "claims-and-events")
ROUND_TWO = ("replication-review", "synthesis-review")


def save(path, obj):
    common.atomic_write_text(path, json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def read(path):
    return json.loads(path.read_bytes())


def checked_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Research evidence must remain inside the private archive")
    return path


def configure(root, key, asr_state, rclone):
    root = common.ensure_outside_git(root)
    parent = root / HOME
    selected = read(root / study_schedule.CONTROL)["selection"]
    if study_schedule.pin(root, checked_path(root, selected["path"])) != selected:
        raise ValueError("The configured latest-20+ selection has changed")
    state = checked_path(root, asr_state)
    key = Path(key).resolve()
    clone = Path(rclone).resolve()
    if not key.is_file() or not clone.is_file() or not state.parent.is_dir():
        raise ValueError("The credential file, uploader or local speech handoff directory is missing")
    config = {"schema_version": 1, "selection": selected, "credential_file": str(key),
              "asr_state": str(state.relative_to(root)), "rclone": str(clone),
              "model": research_agent_budget.MODEL, "cap_usd": "100.00"}
    study_schedule.write_once(parent / SETUP, config)
    return research_agent_budget.BudgetLedger(parent / "budget.sqlite3", cap_usd="100.00").status()


def collection_handoff(root, config, marker):
    selected = config["selection"]
    path = checked_path(root, selected["path"])
    proof = marker.get("selection") or {}
    if (marker.get("kind") != "verified_collection_ready_for_local_speech_recognition"
            or marker.get("backend") != "local_cuda" or proof.get("sha256") != selected["sha256"]
            or Path(proof.get("path", "")).resolve() != path or study_schedule.pin(root, path) != selected):
        raise ValueError("The local audio handoff does not match the frozen study")
    snapshot, saved = collection_coverage.coverage(root, selection=path)
    frame, scopes, expected = collection_coverage.mixed_selection(path, {})
    postrun_candidates.complete_frame(snapshot, saved, frame, scopes, expected)
    if (marker.get("selected_count") != len(frame) or marker.get("creator_count") != len(scopes)
            or expected != selected["sha256"]):
        raise ValueError("Handoff membership disagrees with verified audio receipts")
    return snapshot, frame


def terminal_ready(terminal, selection, count):
    return (terminal.get("status") == "all_selected_audio_assessed" and terminal.get("backend") == "local_cuda"
            and terminal.get("selection", {}).get("sha256") == selection["sha256"]
            and terminal.get("verified_audio") == count and terminal.get("unprocessed") == [])


def finish_round(parent, key_path, phase, roles, evidence):
    reports = agents.panel(parent, key_path, phase, roles, evidence)
    out = agents.save_round(parent, phase, reports)
    return reports, out


def numerical_evidence(root, record, selection, manifest):
    if (record.get("schema_version") != 1 or record.get("state") != "complete"
            or record.get("selection_sha256") != selection["sha256"]
            or record.get("generation_manifest_sha256") != manifest["sha256"]):
        raise ValueError("Numerical results must match the exact validated text generation")
    required = {"tfidf", "cluster_sensitivity", "passage_retrieval"}
    result = {}
    for row in record.get("analyses", []):
        method = row["method"]
        key = "NUMERICAL-" + method
        if (method not in required or key in result or row.get("status") not in ("measured", "not_estimable")
                or not isinstance(row.get("summary"), dict) or not row["summary"]):
            raise ValueError("A numerical result has no distinct method or quantitative evidence")
        proof = row["artifact"]
        if study_schedule.pin(root, checked_path(root, proof["path"])) != proof:
            raise ValueError("A numerical source artifact changed")
        result[key] = {"status": row["status"], "artifact_sha256": proof["sha256"], "summary": row["summary"]}
    if len(result) != len(required) or len(agents.encode(result)) > 45_000:
        raise ValueError("The numerical panel needs three compact, source-bound results")
    return result


def tick(root):
    root = common.ensure_outside_git(root)
    parent = root / HOME
    cfg = read(parent / SETUP)
    if cfg.get("cap_usd") != "100.00" or cfg.get("model") != research_agent_budget.MODEL:
        raise ValueError("The configured project budget or model changed")
    selected = cfg["selection"]
    state = checked_path(root, cfg["asr_state"])
    ready = state / "backend-ready.json"
    if not ready.is_file():
        return {"state": "waiting_for_all_audio_receipts"}
    if (parent / "corpus-panels-complete.json").is_file():
        return {"state": "corpus_panels_complete"}
    key = Path(cfg["credential_file"])
    catalog = parent / "methods-complete.json"
    if not catalog.exists():
        snapshot, frame = collection_handoff(root, cfg, read(ready))
        method = packets.method_evidence(snapshot)
        reports, file = finish_round(parent, key, "methods", METHODS, method)
        save(catalog, {"selection_sha256": selected["sha256"], "handoff": study_schedule.pin(root, ready),
                       "report": study_schedule.pin(root, file), "evidence": method,
                       "jobs": [row["job_id"] for row in reports]})
    methods = read(catalog)
    if (methods["selection_sha256"] != selected["sha256"] or methods["handoff"] != study_schedule.pin(root, ready)
            or study_schedule.pin(root, root / methods["report"]["path"]) != methods["report"]):
        raise ValueError("A completed methods review no longer matches its evidence")
    terminal = state / "terminal.json"
    if not terminal.is_file():
        return {"state": "methods_complete_waiting_for_local_transcription"}
    text_ready = parent / "text-generation-ready.json"
    numerical = parent / "numerical-evidence.json"
    if text_ready.is_file() and not numerical.is_file():
        return {"state": "waiting_for_local_numerical_analysis"}
    snapshot, frame = collection_handoff(root, cfg, read(ready))
    if not terminal_ready(read(terminal), selected, len(frame)):
        return {"state": "waiting_for_local_transcription"}
    selection_path = checked_path(root, selected["path"])
    decisions = parent / "reviewed-non-speech.json"
    if text_ready.is_file():
        frozen = read(text_ready)
        generation = checked_path(root, frozen["generation"])
        if (frozen.get("selection_sha256") != selected["sha256"] or
                any(frozen[k] != study_schedule.pin(root, generation / name) for k, name in
                    (("manifest", "manifest.json"), ("view_inventory", "view-inventory.json")))):
            raise ValueError("The frozen text input to numerical analysis changed")
    else:
        drive = drive_ingest.Rclone(cfg["rclone"], cooldown_path=root / "sync/drive_ingest_cooldown.json")
        stage_archived_text.stage(root, selection_path, selected["sha256"], drive)
        views = postrun_candidates.select_views(root, frame)
        missing = sorted(r["video_id"] for r in frame if r["video_id"] not in views)
        review = read(decisions) if decisions.is_file() else {}
        reviewed = {r["video_id"] for r in review.get("recordings", []) if r.get("finding") == "no_spoken_content"}
        if missing and (review.get("selection_sha256") != selected["sha256"] or set(missing) != reviewed):
            return {"state": "waiting_for_verified_text_or_non_speech_review", "recordings": missing}
        generation = postrun_candidates.run(root, selection_path, selected["sha256"], figures=True)
        frozen = {"selection_sha256": selected["sha256"], "generation": generation.relative_to(root).as_posix(),
                  "manifest": study_schedule.pin(root, generation / "manifest.json"),
                  "view_inventory": study_schedule.pin(root, generation / "view-inventory.json")}
    study_schedule.validate_generation(root, generation, selected["sha256"], frame, decisions if decisions.is_file() else None)
    if not text_ready.exists():
        study_schedule.write_once(text_ready, frozen)
    if not numerical.is_file():
        return {"state": "waiting_for_local_numerical_analysis"}
    evidence = packets.corpus_evidence(generation, methods["evidence"])
    evidence.update(numerical_evidence(root, read(numerical), selected, frozen["manifest"]))
    first, first_path = finish_round(parent, key, "round-one", ROUND_ONE, evidence)
    reviewed_evidence = dict(evidence)
    for record in first:
        reviewed_evidence["FIRST-" + record["role"]] = record["report"]
    second, second_path = finish_round(parent, key, "round-two", ROUND_TWO, reviewed_evidence)
    save(parent / "corpus-panels-complete.json", {"selection_sha256": selected["sha256"],
        "generation": study_schedule.pin(root, generation / "manifest.json"),
        "first_panel": study_schedule.pin(root, first_path), "second_panel": study_schedule.pin(root, second_path),
        "jobs": [r["job_id"] for r in first + second], "generated_at": now()})
    return {"state": "corpus_panels_complete"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def watch(root, once=False):
    parent = root / HOME
    with gpu_asr.kernel_lock(parent / "coordinator.lock"):
        previous = None
        while True:
            try:
                outcome = tick(root)
            except (agents.ResearchHold, research_agent_budget.BudgetError) as err:
                outcome = {"state": "research_request_requires_reconciliation", "reason": str(err)}
            except Exception as err:
                # Save the exception class, never a credential path, API response body or request header.
                outcome = {"state": "local_evidence_or_processing_error", "reason": type(err).__name__}
            if previous != outcome:
                save(parent / "status.json", {**outcome, "observed_at": now(), "pid": os.getpid()})
                previous = outcome
            if once or outcome["state"] == "corpus_panels_complete":
                return outcome
            slow = outcome["state"] in ("waiting_for_verified_text_or_non_speech_review",
                                       "research_request_requires_reconciliation", "local_evidence_or_processing_error")
            time.sleep(600 if slow else 60)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("configure")
    for name in ("credential-file", "asr-state", "rclone"):
        init.add_argument("--" + name, required=True, type=Path)
    sub.add_parser("status")
    worker = sub.add_parser("watch")
    worker.add_argument("--once", action="store_true")
    args = parser.parse_args()
    root = common.ensure_outside_git(args.root)
    if args.action == "configure":
        result = configure(root, args.credential_file, args.asr_state, args.rclone)
    elif args.action == "watch":
        result = watch(root, args.once)
    else:
        result = research_agent_budget.BudgetLedger(root / HOME / "budget.sqlite3").status()
        path = root / HOME / "status.json"
        result["coordinator"] = read(path) if path.is_file() else None
    print(json.dumps(result))


if __name__ == "__main__":
    main()
