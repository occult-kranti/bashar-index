"""Keep later media collection behind the completed latest-20 text study for the configured archive."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from . import common
else:
    import common


CONTROL = "sync/regular_fifty_after_study.json"
RELEASE = "sync/latest20_completed_study.json"


def pin(root, path):
    path = Path(path).resolve()
    if not path.is_relative_to(root) or not path.is_file() or not path.stat().st_size:
        raise ValueError("The study needs a nonempty evidence file inside the private archive")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": path.relative_to(root).as_posix(), "sha256": digest.hexdigest()}


def write_once(path, data):
    if __package__:
        from .gpu_asr import kernel_lock
    else:
        from gpu_asr import kernel_lock
    path.parent.mkdir(parents=True, exist_ok=True)
    with kernel_lock(path.parent / "study-schedule.lock"):
        if path.exists():
            if json.loads(path.read_bytes()) != data:
                raise ValueError("A different study is already recorded at " + path.name)
        else:
            common.atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def configure(root, selection):
    root = common.ensure_outside_git(root)
    proof = pin(root, selection)
    source = json.loads((root / proof["path"]).read_bytes())
    requested = source.get("latest_regular_per_creator", source.get("per_channel"))
    if requested != 20:
        raise ValueError("Select the latest-20 study that must finish first")
    schedule = {"schema_version": 1, "selection": proof, "before": ["regular_50_media", "remaining_media"]}
    write_once(root / CONTROL, schedule)
    return schedule


def require_completed_study(root):
    """Called once before a later media run. Other archives retain their existing workflow."""
    root = Path(root).resolve()
    control = root / CONTROL
    if not control.exists():
        return
    schedule = json.loads(control.read_bytes())
    receipt = root / RELEASE
    if not receipt.is_file():
        raise ValueError("Latest-50 audio is scheduled after the latest-20 transcripts, translations and both analysis rounds")
    completed = json.loads(receipt.read_bytes())
    required = {"generation", "view_inventory", "first_panel_report", "second_panel_report"}
    if (schedule.get("schema_version") != 1 or completed.get("state") != "completed_study"
            or completed.get("selection") != schedule.get("selection") or set(completed.get("evidence", {})) != required):
        raise ValueError("The completed study belongs to another selection or lacks a panel report")
    for evidence in [schedule["selection"], *completed["evidence"].values(), *completed.get("non_speech_reviews", {}).values()]:
        if pin(root, root / evidence["path"]) != evidence:
            raise ValueError("A completed study artifact has changed")


def finish(root, generation, first_panel, second_panel, non_speech=None):
    """Record the final generation and both substantive panel outputs after the research work is complete."""
    if __package__:
        from . import collection_coverage, postrun_candidates as study
    else:
        import collection_coverage
        import postrun_candidates as study
    root = common.ensure_outside_git(root)
    schedule = json.loads((root / CONTROL).read_bytes())
    selected = schedule["selection"]
    source = root / selected["path"]
    if selected != pin(root, source):
        raise ValueError("The frozen latest-20 selection changed")
    frame, scopes, expected = collection_coverage.mixed_selection(source, {})
    snapshot, saved = collection_coverage.coverage(root, selection=source)
    study.complete_frame(snapshot, saved, frame, scopes, expected)
    evidence = {name: pin(root, path) for name, path in {
        "generation": generation / "manifest.json", "view_inventory": generation / "view-inventory.json",
        "first_panel_report": first_panel, "second_panel_report": second_panel}.items()}
    if evidence["first_panel_report"]["sha256"] == evidence["second_panel_report"]["sha256"]:
        raise ValueError("Record the distinct first-panel and second-panel findings")
    english, translated, reviews = validate_generation(root, generation, expected, frame, non_speech)
    receipt = {"schema_version": 1, "state": "completed_study", "selection": selected, "selected_audio": len(frame),
               "english_texts": english, "translated_primary_texts": translated,
               "non_speech_reviews": reviews, "evidence": evidence}
    write_once(root / RELEASE, receipt)
    require_completed_study(root)
    return receipt


def validate_generation(root, generation, expected, frame, non_speech=None):
    """Verify English views, paired translations and individual exceptions before corpus interpretation."""
    if __package__:
        from . import postrun_candidates as study
    else:
        import postrun_candidates as study

    root = Path(root).resolve()
    generation = Path(generation).resolve()
    if not generation.is_relative_to(root):
        raise ValueError("Text analysis must use a generation inside the private archive")
    manifest = json.loads((generation / "manifest.json").read_bytes())
    roster = json.loads((generation / "view-inventory.json").read_bytes())
    pairs = {(r["channel_dir"], r["video_id"]) for r in frame}
    revisions = {study.digest(study.encoded([expected, study.digest(study.encoded(manifest["methods"]).encode()),
                                            roster, figures]).encode()) for figures in (False, True)}
    if (manifest.get("selection_sha256") != expected or manifest.get("phase") != "candidate_retrieval"
            or manifest.get("revision") != generation.name or generation.name not in revisions
            or manifest.get("selected_audio") != len(pairs) or len(roster) != len(pairs)
            or {(r["channel_dir"], r["video_id"]) for r in roster} != pairs):
        raise ValueError("The final text generation must cover this exact completed audio selection")
    missing = {r["video_id"] for r in roster if r["selected_primary"] is None}
    if manifest.get("missing_primary_texts") != len(missing) or manifest.get("eligible_primary_texts") != len(pairs) - len(missing):
        raise ValueError("The final corpus reports inconsistent text coverage")
    reviews = {}
    if non_speech is not None:
        review = json.loads((root / pin(root, non_speech)["path"]).read_bytes())
        if review.get("selection_sha256") != expected:
            raise ValueError("The non-speech reviews belong to another selection")
        for row in review["recordings"]:
            video = row["video_id"]
            if video in reviews or row.get("finding") != "no_spoken_content":
                raise ValueError("Expected an individual review of a recording without speech")
            reviews[video] = pin(root, root / row["evidence"]["path"])
            if reviews[video] != row["evidence"]:
                raise ValueError("The reviewed non-speech evidence changed")
            reviewed = json.loads((root / reviews[video]["path"]).read_bytes())
            source = reviewed.get("source") or {}
            audio = source.get("audio") or {}
            if (reviewed.get("finding") != "no_spoken_content" or source.get("video_id") != video
                    or (source.get("channel_dir"), video) not in pairs or source.get("selection_sha256") != expected
                    or not study.episode_comparison.digest(audio.get("sha256")) or not audio.get("drive_id")):
                raise ValueError("Non-speech evidence must identify the selected recording and its archived audio")
    if missing != reviews.keys():
        raise ValueError("Spoken recordings still need usable English text")
    translated = 0
    for row in roster:
        chosen = row["selected_primary"]
        if chosen is None:
            continue
        path = (root / chosen["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("A selected English text is missing from the private archive")
        raw = path.read_bytes()
        if study.digest(raw) != chosen["file_sha256"]:
            raise ValueError("The selected English text changed after analysis")
        english = json.loads(raw)
        text = english.get("text")
        if (english.get("video_id") != row["video_id"] or english.get("channel_dir") != row["channel_dir"]
                or english.get("source_kind") != chosen["source_kind"] or chosen["source_kind"] not in study.PRIMARY_ORDER
                or str(english.get("language", "")).lower().replace("_", "-").split("-")[0] != "en"
                or not isinstance(text, str) or not text.strip() or english.get("text_sha256") != study.digest(text.encode())):
            raise ValueError("Selected English text has a recording, language or content mismatch")
        if not chosen["source_kind"].endswith("english_audio_translation"):
            continue
        if not english.get("original_language") or not english.get("run_id") or not english.get("source_edition_id"):
            raise ValueError("English translation lacks original-language or edition evidence")
        for candidate in path.parent.glob("original-*.json"):
            if not candidate.resolve().is_relative_to(root):
                raise ValueError("A paired original-language view is outside the private archive")
            original = json.loads(candidate.read_bytes())
            if (all(original.get(k) == english.get(k) for k in ("video_id", "channel_dir", "run_id", "source_edition_id"))
                    and original.get("variant") == "original" and original.get("language") == english["original_language"]
                    and original.get("text") and original.get("text_sha256") == study.digest(original["text"].encode())):
                break
        else:
            raise ValueError("An English translation still needs its matching original-language transcript")
        translated += 1
    return len(pairs) - len(missing), translated, reviews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    commands = parser.add_subparsers(dest="action", required=True)
    setup = commands.add_parser("schedule")
    setup.add_argument("--selection", type=Path, required=True)
    close = commands.add_parser("finish")
    for name in ("generation", "first-panel", "second-panel"):
        close.add_argument("--" + name, type=Path, required=True)
    close.add_argument("--non-speech", type=Path, help="Reviewed private evidence for selected recordings without speech")
    args = parser.parse_args()
    if args.action == "schedule":
        result = configure(args.root, args.selection)
    else:
        result = finish(args.root, args.generation, args.first_panel, args.second_panel, args.non_speech)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
