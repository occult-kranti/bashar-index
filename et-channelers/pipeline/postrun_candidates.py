"""Run the first, private text-analysis pass once every selected recording has verified audio.

Use stage_archived_text to prepare verified English source views.
The optional family file contains reviewed video_id, recording_family_id and evidence hashes.
The revisioned result retains one primary English view per selected video, all missing
entries, source-addressable candidates, detector-negative windows and comparison tables.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory

if __package__:
    from . import collection_coverage, common, corpus_concordance, episode_comparison, episode_figures, gpu_asr, publisher_caption_batch
else:
    import collection_coverage, common, corpus_concordance, episode_comparison, episode_figures, gpu_asr, publisher_caption_batch


# Use an English source track before ASR. A machine translation remains a distinct text version.
PRIMARY_ORDER = ("published", "automatic_original", "publisher_english_caption", "standalone_publisher_caption", "publisher_untimed_transcript",
                 "numbered_publisher_episode_transcript",
                 "original_asr", "english_audio_translation", "qualified_youtube_original_asr",
                 "qualified_youtube_english_audio_translation", "publisher_original_asr", "publisher_english_audio_translation")
VIEWS = (("caption_views", "*/*.json", PRIMARY_ORDER[:2]),
         ("publisher_views", "*/*.json", ("publisher_english_caption",)),
         ("publisher_transcript_views", "*/*.json", ("publisher_untimed_transcript", "numbered_publisher_episode_transcript")),
         ("asr_views", "*/*/english-*.json", ("original_asr", "english_audio_translation")),
         ("publisher_variant_views", "*/*.json", ("standalone_publisher_caption", "publisher_original_asr", "publisher_english_audio_translation")),
         ("edition_asr_views", "*/english-*.json", ("qualified_youtube_original_asr", "qualified_youtube_english_audio_translation",
             "publisher_original_asr", "publisher_english_audio_translation")))


def encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def complete_frame(snapshot, saved, frame, scopes, expected):
    summary = snapshot["summary"]
    wanted = {(r["channel_dir"], r["video_id"]) for r in frame}
    actual = {(r["channel_dir"], r["video_id"]) for r in saved}
    by_creator = Counter(c for c, _ in wanted)
    if (snapshot.get("selection_sha256") != expected or not scopes or not wanted
            or len(wanted) != len(frame) or len(actual) != len(saved) or wanted != actual
            or summary["latest20_target"] != len(wanted) or summary["audio_available"] != len(wanted)
            or summary["channels"] != len(scopes) or summary["remaining_audio"] != 0
            or any(not (scope == "all_requested_positions_observed" and by_creator[c] == 20
                        or scope == "short_complete_displayed_list" and by_creator[c] < 20)
                   for c, scope in scopes.items()) or not set(by_creator) <= scopes.keys()):
        raise ValueError("The pinned collection still needs verified audio or complete public listings")


def select_views(root, frame):
    """Index adapter outputs, keeping full transcript bytes out of the inventory."""
    target = {r["video_id"]: r["channel_dir"] for r in frame}
    candidates = defaultdict(list)
    for directory, pattern, kinds in VIEWS:
        base = root / "analysis" / directory
        for path in sorted(base.glob(pattern)):
            relative = path.relative_to(base)
            video = relative.parts[0]
            if video not in target:
                continue
            if not path.resolve().is_relative_to(base.resolve()) or not base.resolve().is_relative_to(root):
                raise ValueError("A primary view is outside its private archive directory")
            raw = path.read_bytes()
            view = json.loads(raw)
            kind = view.get("source_kind")
            if directory == "edition_asr_views":
                timebase = "qualified_youtube_audio_seconds" if kind in (
                    "qualified_youtube_original_asr", "qualified_youtube_english_audio_translation") else "publisher_audio_seconds"
                if (view.get("source_timebase") != timebase or view.get("native_youtube_alignment_verified") is not False
                    or view.get("recording_equivalence_verified") is not False or view.get("variant") != "english"
                    or not all(episode_comparison.digest(view.get(k)) for k in ("source_audio_sha256", "edition_receipt_sha256",
                               "associated_source_key", "inference_source_key", "artifact_manifest_sha256"))
                    or view.get("source_edition_id") != "sha256:" + view["source_audio_sha256"]):
                    raise ValueError("Edition ASR needs its verified audio object, listing association and original timebase")
            if directory == "publisher_variant_views":
                if (view.get("video_id") != video or view.get("channel_dir") != target[video] or kind not in kinds
                        or not episode_comparison.digest(view.get("edition_receipt_sha256"))
                        or view.get("native_youtube_alignment_verified") is not False):
                    raise ValueError("Publisher text needs a verified source-edition receipt")
                evidence = view.get('language_evidence') or {}
                if ((kind == "standalone_publisher_caption" and evidence.get('basis') != 'publisher_labels_original_English_track'
                         and not publisher_caption_batch.confirmed_english_cues(evidence))
                        or not re.fullmatch(r"en(?:-[A-Z0-9]+)*", view.get("language") or "", re.I)):
                    continue
            if (view.get("video_id") != video or view.get("channel_dir") != target[video] or kind not in kinds
                    or not re.fullmatch(r"en(?:-[A-Z0-9]+)*", view.get("language") or "", re.I)
                    or not all(episode_comparison.digest(view.get(k)) for k in
                               ("text_version_id", "bundle_sha256", "raw_sha256", "text_sha256"))
                    or view.get("speech_coverage_verified") is not False):
                raise ValueError("Primary-view identity, language or source provenance is invalid")
            if kind == "publisher_english_caption" and (not episode_comparison.digest(view.get("edition_receipt_sha256"))
                    or not episode_comparison.digest(view.get("source_audio_sha256"))):
                raise ValueError("Publisher caption needs verified recording-edition provenance")
            paragraph_evidence = {}
            if kind == "publisher_untimed_transcript":
                if (not all(episode_comparison.digest(view.get(k)) for k in
                            ("source_audio_sha256", "edition_receipt_sha256", "source_metadata_sha256", "source_document_sha256"))
                        or view.get("source_edition_id") != "sha256:" + view["source_audio_sha256"]
                        or view.get("bundle_sha256") != view["source_document_sha256"] or view["raw_sha256"] != view["bundle_sha256"]
                        or view.get("recording_equivalence_verified") is not False or view.get("native_youtube_alignment_verified") is not False
                        or view.get("recording_association_method") not in ("publisher_episode_page_exact_youtube_id",
                                                                          "publisher_owner_title_date_duration")
                        or view.get("text_version_id") != digest(("untimed-publisher-v1|" + view["source_audio_sha256"] + "|"
                               + view["source_document_sha256"] + "|" + view["text_sha256"]).encode())):
                    raise ValueError("Publisher transcript needs verified untimed recording-edition provenance")
            if kind == "numbered_publisher_episode_transcript":
                source_id = view.get("source_edition_id")
                if (not isinstance(source_id, str) or not re.fullmatch(r"publisher:[0-9a-f]{64}", source_id)
                        or view.get("source_audio_sha256") is not None or view.get("native_youtube_alignment_verified") is not False
                        or view.get("recording_equivalence_verified") is not False
                        or view.get("recording_association_method") != "same_publisher_title_season_episode_duration"
                        or view.get("source_document_sha256") != view["raw_sha256"] or view["bundle_sha256"] != view["text_sha256"]
                        or view["raw_sha256"] != view["text_sha256"]
                        or not all(episode_comparison.digest(view.get(key)) for key in ("edition_receipt_sha256", "source_metadata_sha256"))
                        or view["text_version_id"] != digest((kind+"|"+source_id+"|"+view["text_sha256"]).encode())):
                    raise ValueError("Unbound independently archived episode transcript")
            if kind in ("publisher_untimed_transcript", "numbered_publisher_episode_transcript"):
                corpus_concordance.validate_paragraph_view(view)
                paragraph_evidence = {"evidence_granularity":"paragraph", "paragraph_count":view["paragraph_count"],
                    "source_document_sha256":view["source_document_sha256"], "edition_receipt_sha256":view["edition_receipt_sha256"],
                    "recording_association_method":view["recording_association_method"]}
            rank = (PRIMARY_ORDER.index(kind), kind == "publisher_english_caption" and view.get("caption_kind") != "published",
                    view["language"].lower() != "en", view["language"].lower(),
                    view["text_version_id"], relative.as_posix())
            candidates[video].append((rank, {"video_id": video, "path": path.relative_to(root).as_posix(),
                "file_sha256": digest(raw), "text_version_id": view["text_version_id"], "source_kind": kind,
                "language": view["language"], "source_edition_id": view.get("source_edition_id"),
                "caption_kind": view.get("caption_kind"), "source_timebase": view.get("source_timebase"),
                "bundle_sha256": view["bundle_sha256"], **paragraph_evidence}))
    return {video: [item for _, item in sorted(options, key=lambda x: x[0])]
            for video, options in sorted(candidates.items())}


def attach_families(frame, path):
    if not path:
        return frame
    reviewed = {r["video_id"]: r for r in frame}
    seen = set()
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        assignment = json.loads(line)
        video = assignment["video_id"]
        if (video not in reviewed or video in seen or not episode_comparison.label(assignment.get("recording_family_id"))
                or not episode_comparison.digest(assignment.get("recording_family_evidence_sha256"))):
            raise ValueError("Invalid reviewed recording-family assignment")
        seen.add(video)
        reviewed[video] = dict(reviewed[video], recording_family_id=assignment["recording_family_id"],
                               recording_family_evidence_sha256=assignment["recording_family_evidence_sha256"])
    return list(reviewed.values())


def candidates(root, frame, choices, method, topics, engine, output, counts):
    for row in frame:
        video = row["video_id"]
        if video not in choices:
            continue
        selected = choices[video][0]
        raw = (root / selected["path"]).read_bytes()
        if digest(raw) != selected["file_sha256"]:
            raise ValueError("A staged primary view changed during analysis")
        view = json.loads(raw)
        matches = []
        for record in engine.records(view, work_family_id=row.get("recording_family_id")):
            output.write(encoded(record) + "\n")
            counts[record["record_type"]] += 1
            if record["record_type"] == "candidate":
                matches.append({"topic": record["candidate_family"], "char_start": record["start_codepoint"],
                                "char_end": record["end_codepoint"]})
            elif not record["has_detector_match"]:
                counts["detector_negative_windows"] += 1
        yield {"view": view, "assessed_topics": topics, "assessment_method_sha256": method, "matches": matches}


def run(root, selection, expected, *, families=None, figures=False, out=None):
    root = common.ensure_outside_git(root)
    if not episode_comparison.digest(expected):
        raise ValueError("Pin the intended collection with its exact SHA-256")
    selection = common.ensure_outside_git(selection)
    snapshot, saved = collection_coverage.coverage(root, selection=selection)
    frame, scopes, selection_hash = collection_coverage.mixed_selection(selection, {})
    if selection_hash != expected:
        raise ValueError("The selected recording file changed")
    complete_frame(snapshot, saved, frame, scopes, expected)
    if families:
        families = common.ensure_outside_git(families)
        if not families.is_relative_to(root):
            raise ValueError("The private recording-family file belongs under the archive root")
    frame = attach_families(frame, families)
    choices = select_views(root, frame)
    engine = corpus_concordance.Concordance()
    topics = sorted({family for _, family, _ in engine.rules})
    methods = {name: digest(Path(module.__file__).read_bytes()) for name, module in (
        ("concordance", corpus_concordance), ("comparison", episode_comparison), ("figures", episode_figures))}
    methods.update(driver=digest(Path(__file__).read_bytes()), lexicon=engine.revision)
    method = digest(encoded(methods).encode())
    roster = [{"video_id": row["video_id"], "channel_dir": row["channel_dir"], "tab": row["tab"],
               "selected_primary": choices[row["video_id"]][0] if row["video_id"] in choices else None,
               "other_eligible_views": choices.get(row["video_id"], [])[1:],
               "recording_family_id": row.get("recording_family_id"),
               "recording_family_evidence_sha256": row.get("recording_family_evidence_sha256")} for row in frame]
    revision = digest(encoded([expected, method, roster, figures]).encode())
    parent = common.ensure_outside_git(out or root / "analysis" / "candidate_runs")
    if not parent.is_relative_to(root) or parent == root:
        raise ValueError("Analysis outputs belong in the private archive")
    parent.mkdir(parents=True, exist_ok=True)
    final = parent / revision
    with gpu_asr.kernel_lock(parent / ".candidate-runs.lock"):
        if final.exists():
            manifest = json.loads((final / "manifest.json").read_bytes())
            if (manifest.get("revision") != revision or not manifest.get("files")
                    or any(not (final / name).is_file() or (final / name).stat().st_size != size
                           for name, size in manifest["files"].items())):
                raise ValueError("The existing analysis folder is incomplete or changed")
            return final
        with TemporaryDirectory(dir=parent) as temporary:
            stage = Path(temporary) / "outputs"
            stage.mkdir()
            counts = Counter()
            with (stage / "concordance.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
                comparison = episode_comparison.compare(frame, candidates(root, frame, choices, method, topics,
                                                                          engine, stream, counts), topics)
            comparison.update(assessment="unreviewed_english_lexicon_candidates", assessment_method_sha256=method)
            common.atomic_write_text(stage / "episode-comparison.json", encoded(comparison) + "\n")
            common.atomic_write_text(stage / "view-inventory.json", encoded(roster) + "\n")
            if figures:
                episode_figures.export(comparison, stage / "figures", label="English text | Unreviewed term matches")
            manifest = {"revision": revision, "selection_sha256": expected, "methods": methods,
                        "phase": "candidate_retrieval", "selected_audio": len(frame), "creators": len(scopes),
                        "eligible_primary_texts": len(choices), "missing_primary_texts": len(frame) - len(choices),
                        "primary_view_order": PRIMARY_ORDER, "counts": dict(counts),
                        "files": {p.relative_to(stage).as_posix(): p.stat().st_size
                                  for p in stage.rglob("*") if p.is_file() and not p.name.startswith(".")}}
            common.atomic_write_text(stage / "manifest.json", encoded(manifest) + "\n")
            os.rename(stage, final)
    return final


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--selection-sha256", required=True)
    parser.add_argument("--families", type=Path, help="Private JSONL of reviewed recording-family assignments")
    parser.add_argument("--out", type=Path, help="Private parent for immutable output generations")
    parser.add_argument("--figures", action="store_true", help="Include SVG, PNG and CSV figure exports")
    args = parser.parse_args(argv)
    result = run(args.root, args.selection, args.selection_sha256, families=args.families,
                 figures=args.figures, out=args.out)
    print(result)


if __name__ == "__main__":
    main()
