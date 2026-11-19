"""Batch-stage verified English captions and native-recording ASR results for the private corpus."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

from . import (collection_coverage, common, corpus_asr_view, corpus_caption_view, corpus_publisher_view, corpus_publisher_variant_view,
               drive_ingest, gpu_asr, ingestion_status, postrun_candidates)


def input_rows(root, frame, remote):
    targets = {r["video_id"]: r for r in frame}
    editions = ingestion_status.latest_records(root / "sync/drive_ingest_manifest.jsonl")
    captions = ingestion_status.latest_records(root / "sync/drive_caption_manifest.jsonl")
    for video, row in targets.items():
        record = captions.get(video, {})
        if record.get("channel_dir") != row["channel_dir"] or record.get("policy") != drive_ingest.CAPTION_POLICY:
            continue
        for track in record.get("tracks", []):
            if isinstance(track, dict) and drive_ingest.caption_track_verified(track, row, remote):
                yield {"kind": "youtube_caption", "row": row, "record": record, "proof": track["bundle"],
                       "track_id": track["track_id"]}
    for record in ingestion_status.asr_records(root / "sync/asr_manifest.jsonl"):
        video = record["video_id"]
        edition = editions.get(video, {})
        if (video in targets and targets[video]["channel_dir"] == record.get("channel_dir")
                and ingestion_status.asr_receipt_complete(record, edition, remote)):
            yield {"kind": "native_asr", "row": targets[video], "record": record, "proof": record, "edition": edition}
    for record in common.read_jsonl(root / "sync/publisher_mirror_manifest.jsonl"):
        video = record.get("associated_youtube_id")
        if video not in targets:
            continue
        for track in record.get("caption_bundles") or [record.get("caption_bundle")]:
            if not isinstance(track, dict) or not track.get("usable_timed_text"):
                continue
            proof = corpus_publisher_view.verified_track(record, targets[video], track["sha256"], remote)
            yield {"kind": "publisher_caption", "row": targets[video], "record": record, "proof": proof}
    yield from corpus_publisher_variant_view.input_rows(root, frame, remote)


def existing_bundle(root, job):
    row, proof = job["row"], job["proof"]
    if job["kind"] in (corpus_publisher_variant_view.ASR, corpus_publisher_variant_view.CAPTION):
        return corpus_publisher_variant_view.local_bundle(root, job)
    if job["kind"] == "native_asr":
        run = job["record"]["run_id"]
        path = root / "asr/results" / row["video_id"] / run / (run + ".zip")
    elif proof.get("path"):
        path = root / proof["path"]
    else:
        return None
    if not path.resolve().is_relative_to(root) or not path.is_file():
        return None
    return drive_ingest.local_path(root, path.relative_to(root))


def text_views(root, job, path, remote):
    record, row, proof = job["record"], job["row"], job["proof"]
    video = row["video_id"]
    if job["kind"] in (corpus_publisher_variant_view.ASR, corpus_publisher_variant_view.CAPTION):
        views = corpus_publisher_variant_view.text_views(path, job, remote)
        return {f"publisher_variant_views/{video}/{name}-{v['text_version_id']}.json": v for name, v in views.items()}
    if job["kind"] == "youtube_caption":
        view = corpus_caption_view.caption_view(path, record, job["track_id"], remote=remote)
        return {"caption_views/" + video + "/" + view["text_version_id"] + ".json": view}
    if job["kind"] == "publisher_caption":
        view = corpus_publisher_view.publisher_view(path, record, row, proof["sha256"], remote=remote)
        return {"publisher_views/" + video + "/" + view["text_version_id"] + ".json": view}
    run = record["run_id"]
    receipt = record
    if corpus_asr_view.DATED_RUN.fullmatch(run):
        local = drive_ingest.local_path(root, f"asr/results/{video}/{run}/result-receipt.json")
        if local.is_file():
            receipt = json.loads(local.read_bytes())
    views = corpus_asr_view.asr_views(path, receipt, edition_receipt=job["edition"], drive_receipt=record, remote=remote)
    return {f"asr_views/{video}/{run}/{name}-{v['text_version_id']}.json": v for name, v in views.items()}


def fetch_batch(drive, remote, cache, needed):
    """Use one metadata pass and one rclone copy for the exact paths in this batch."""
    if not needed:
        return
    with TemporaryDirectory(dir=cache) as temp:
        manifest = Path(temp) / "paths.txt"
        manifest.write_text("".join(name + "\n" for name in needed), encoding="utf-8", newline="\n")
        found = drive.stat_batch(remote, list(needed), manifest)
        for name, proof in needed.items():
            drive_ingest.verify_remote(found[name], proof)
            if found[name].get("ID") != proof["drive_id"]:
                raise ValueError("Archived text now resolves to a different Drive object")
        bound = sum(p["bytes"] for p in needed.values()) + 1_048_576
        drive.execute(["copy", remote, str(cache), "--files-from-raw", str(manifest), "--no-traverse", "--immutable",
                       "--transfers", "3", "--checkers", "2", "--buffer-size", "1M", "--multi-thread-streams", "0",
                       "--max-transfer", str(bound) + "B", "--cutoff-mode", "hard", *drive.RETRY_FLAGS],
                      1800, "read archived transcript bundles")


def headroom(root):
    _, used = drive_ingest.storage_usage(root, drive_ingest.managed_roots(root))
    reserve = drive_ingest.reserved_project_growth(root)
    return min(drive_ingest.MAX_LOCAL_BYTES - used, shutil.disk_usage(root).free - drive_ingest.MIN_FREE_BYTES) - reserve


def prior_views(root, marker, key):
    if not marker.is_file():
        return 0
    record = json.loads(marker.read_bytes())
    files = record.get("views")
    if record.get("key") != key or not isinstance(files, dict) or not files:
        raise ValueError("Invalid text staging checkpoint")
    for name, proof in files.items():
        path = drive_ingest.local_path(root, name)
        if not path.is_file():
            return 0
        if list(drive_ingest.fingerprint(path)) != proof["fingerprint"]:
            if path.stat().st_size != proof["bytes"] or drive_ingest.hash_file(path)["sha256"] != proof["sha256"]:
                raise ValueError("A previously staged text view changed")
    return len(files)


def stage(root, selection, expected, drive, remote=ingestion_status.DEFAULT_REMOTE, *, inventory_only=False):
    root, selection = common.ensure_outside_git(root), common.ensure_outside_git(selection)
    frame, scopes, actual = collection_coverage.mixed_selection(selection, {})
    if actual != expected:
        raise ValueError("Recording selection changed")
    if not inventory_only:
        snapshot, saved = collection_coverage.coverage(root, selection=selection, remote=remote)
        postrun_candidates.complete_frame(snapshot, saved, frame, scopes, expected)
    jobs = list(input_rows(root, frame, remote))
    report = {"selection_sha256": actual, "eligible_audio": len(frame), "archive_inputs": dict(Counter(j["kind"] for j in jobs)),
              "recordings_with_inputs": len({j["row"]["video_id"] for j in jobs}), "views_staged": 0, "held": []}
    if inventory_only or not jobs:
        return report
    analysis = drive_ingest.local_path(root, "analysis")
    cache = drive_ingest.local_path(root, "analysis/text_bundle_cache")
    cache.mkdir(parents=True, exist_ok=True)
    revision = [hashlib.sha256(Path(mod.__file__).read_bytes()).hexdigest()
                for mod in (corpus_caption_view, corpus_asr_view, corpus_publisher_view, corpus_publisher_variant_view)]
    with gpu_asr.kernel_lock(analysis / ".archive-read.lock"):
        for start in range(0, len(jobs), 24):
            batch = jobs[start:start+24]
            plan, needed = [], {}
            for job in batch:
                proof = job["proof"]
                name = drive_ingest.remote_relative(remote, proof["remote"])
                key = gpu_asr.fingerprint([revision, job["kind"], job["row"]["video_id"], job["row"]["channel_dir"],
                    job["row"]["tab"], job["record"], job.get("edition"), job.get("track_id"), job.get("item"), proof["sha256"]])
                marker = drive_ingest.local_path(analysis, "text_stage_receipts/" + key + ".json")
                completed = prior_views(analysis, marker, key)
                if completed:
                    report["views_staged"] += completed
                    continue
                local = existing_bundle(root, job)
                if local is None:
                    local = drive_ingest.local_path(cache, name)
                    if not local.is_file():
                        prior = needed.setdefault(name, proof)
                        if any(prior[k] != proof[k] for k in ("drive_id", "md5", "sha256", "bytes")):
                            raise ValueError("Two archived text receipts disagree on a single path")
                plan.append((job, local, marker, key))
            if not plan:
                continue
            # Account for the new ZIPs and the largest temporary verification copy.
            room = headroom(root) - sum(p["bytes"] for p in needed.values()) - max(j["proof"]["bytes"] for j, *_ in plan) - 1_048_576
            if room < 0:
                raise ValueError("Archived text staging would exceed the project disk allowance")
            fetch_batch(drive, remote, cache, needed)
            retired, held_paths = {}, set()
            for job, path, marker, key in plan:
                before = drive_ingest.fingerprint(path)
                try:
                    views = text_views(root, job, path, remote)
                except (ValueError, KeyError, gpu_asr.AsrError, BadZipFile) as err:
                    held_paths.add(path)
                    report["held"].append({"video_id": job["row"]["video_id"], "kind": job["kind"],
                                           "bundle_sha256": job["proof"]["sha256"], "reason": str(err)})
                    continue
                outputs = {}
                for name, view in views.items():
                    out = drive_ingest.local_path(analysis, name)
                    data = json.dumps(view, ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"
                    if out.is_file():
                        if out.read_bytes() != data:
                            raise ValueError("Existing versioned text view differs from the verified artifact")
                    else:
                        if len(data) > room:
                            raise ValueError("A text view would consume the reserved free disk space")
                        common.atomic_write_text(out, data.decode("utf-8"))
                        room -= len(data)
                    report["views_staged"] += 1
                    outputs[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                     "fingerprint": list(drive_ingest.fingerprint(out))}
                gpu_asr.atomic_json(marker, {"key": key, "views": outputs})
                if path.is_relative_to(cache):
                    retired[path] = before
            for path, before in retired.items():
                if path not in held_paths and drive_ingest.fingerprint(path) == before:
                    path.unlink()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--selection-sha256", required=True)
    parser.add_argument("--remote", default=ingestion_status.DEFAULT_REMOTE)
    parser.add_argument("--rclone", default="rclone")
    parser.add_argument("--inventory-only", action="store_true", help="Read existing receipt journals and report eligible inputs")
    args = parser.parse_args(argv)
    drive = drive_ingest.Rclone(args.rclone, cooldown_path=args.root / "sync/drive_ingest_cooldown.json")
    result = stage(args.root, args.selection, args.selection_sha256, drive, args.remote, inventory_only=args.inventory_only)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
