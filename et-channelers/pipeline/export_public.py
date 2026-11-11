#!/usr/bin/env python3
"""Turn the private manifests into a table that is safe to publish: numbers and hashes, no text, no paths.

Per video: audio status, length, size, audio hash, transcript status, language, segment and word
counts, hash of the normalised text, model and library versions, and speed. This follows the Atlas
rule: raw captions and transcripts stay private; public outputs keep hashes and numeric features.

    python3 pipeline/export_public.py                      # writes <root>/public_export/media_manifest_public.csv
Review the file, then copy it into the repository yourself. Nothing here writes into the repository.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import add_root_arg, ensure_outside_git, latest_by_key, layout, read_jsonl, write_csv  # noqa: E402

FIELDS = ["video_id", "audio_status", "audio_duration_s", "audio_bytes", "audio_sha256", "transcript_status",
          "language", "language_probability", "n_segments", "n_words", "text_sha256", "engine", "engine_version",
          "model", "model_revision", "model_bin_sha256", "device", "compute_type", "x_real_time"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    paths = layout(ensure_outside_git(a.root))
    audio = latest_by_key(read_jsonl(paths.audio / "audio_manifest.jsonl"))
    trans = latest_by_key(read_jsonl(paths.transcripts / "transcripts_manifest.jsonl"))
    rows = []
    for vid in sorted(set(audio) | set(trans)):
        au, tr = audio.get(vid, {}), trans.get(vid, {})
        rows.append({
            "video_id": vid, "audio_status": au.get("status", ""), "audio_duration_s": au.get("duration_s", ""),
            "audio_bytes": au.get("bytes", ""), "audio_sha256": au.get("sha256") or tr.get("audio_sha256", ""),
            "transcript_status": tr.get("status", ""), "language": tr.get("language", ""),
            "language_probability": tr.get("language_probability", ""), "n_segments": tr.get("n_segments", ""),
            "n_words": tr.get("n_words", ""), "text_sha256": tr.get("text_sha256", ""),
            "engine": tr.get("engine", ""), "engine_version": tr.get("engine_version", ""),
            "model": tr.get("model", ""), "model_revision": tr.get("model_revision", ""),
            "model_bin_sha256": tr.get("model_bin_sha256", ""), "device": tr.get("device", ""), "compute_type": tr.get("compute_type", ""),
            "x_real_time": tr.get("x_real_time", "")})
    out = a.out or paths.public / "media_manifest_public.csv"
    write_csv(out, rows, FIELDS)
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
