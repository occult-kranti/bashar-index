#!/usr/bin/env python3
"""Consistency checks on the private audio and transcript folders, and a human-check sample.

    python3 pipeline/verify.py                  # checks only; exit code 1 if anything is wrong
    python3 pipeline/verify.py --hash           # also re-hash every file (slow, catches silent corruption)
    python3 pipeline/verify.py --qa-sample 20   # also write qa/qa_sample.csv: random 60 s windows to correct by hand

The QA sheet contains transcript text, so it stays in the private folder. It exists to measure
word error rate on a sample (Atlas roadmap item N4), not to be published.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import add_root_arg, ensure_outside_git, latest_by_key, layout, read_jsonl, sha256_file, write_csv  # noqa: E402


def check_audio(paths, with_hash):
    problems, ok = [], 0
    for vid, rec in latest_by_key(read_jsonl(paths.audio / "audio_manifest.jsonl")).items():
        if rec["status"] != "ok":
            continue
        ok += 1
        f = paths.audio / rec["path"]
        if not f.exists():
            problems.append(f"{vid}: audio file missing")
            continue
        if f.stat().st_size != rec["bytes"]:
            problems.append(f"{vid}: audio size {f.stat().st_size} != recorded {rec['bytes']}")
        if with_hash and sha256_file(f) != rec["sha256"]:
            problems.append(f"{vid}: audio hash differs from manifest")
        exp, got = rec.get("expected_duration_s"), rec.get("duration_s")
        if exp and got and abs(got - exp) > max(5, 0.03 * exp):
            problems.append(f"{vid}: audio is {got:.0f}s but the listing says {exp}s (truncated or wrong video?)")
    return ok, problems


def check_transcripts(paths, with_hash):
    problems, ok = [], 0
    audio_ok = {v for v, r in latest_by_key(read_jsonl(paths.audio / "audio_manifest.jsonl")).items() if r["status"] == "ok"}
    records = read_jsonl(paths.transcripts / "transcripts_manifest.jsonl")
    done = {v for v, r in latest_by_key(records).items() if r["status"] == "ok"}
    for vid, rec in latest_by_key(records).items():
        if rec["status"] != "ok":
            continue
        ok += 1
        base = paths.transcripts / rec["channel_dir"] / vid
        if not base.with_suffix(".json").exists() or not base.with_suffix(".txt").exists():
            problems.append(f"{vid}: transcript file missing")
            continue
        try:
            doc = json.loads(base.with_suffix(".json").read_text(encoding="utf-8"))
        except ValueError:
            problems.append(f"{vid}: transcript JSON does not parse")
            continue
        segs = doc.get("segments") or []
        if not segs:
            problems.append(f"{vid}: no segments")
        elif any(s["end"] < s["start"] for s in segs) or any(b["start"] < a["start"] for a, b in zip(segs, segs[1:])):
            problems.append(f"{vid}: segment times out of order")
        elif doc.get("duration_s") and segs[-1]["end"] > doc["duration_s"] + 5:
            problems.append(f"{vid}: last segment ends after the audio does")
        if with_hash and sha256_file(base.with_suffix(".json")) != rec["json_sha256"]:
            problems.append(f"{vid}: transcript hash differs from manifest")
    problems += [f"{v}: audio downloaded but not transcribed" for v in sorted(audio_ok - done)]
    problems += [f"{v}: transcript has no successful audio record" for v in sorted(done - audio_ok)]
    return ok, problems


def qa_sample(paths, n, windows, seconds, seed):
    rng = random.Random(seed)
    rows = []
    ids = sorted(v for v, r in latest_by_key(read_jsonl(paths.transcripts / "transcripts_manifest.jsonl")).items()
                 if r["status"] == "ok")
    for vid in rng.sample(ids, min(n, len(ids))):
        rec = latest_by_key(read_jsonl(paths.transcripts / "transcripts_manifest.jsonl"))[vid]
        doc = json.loads((paths.transcripts / rec["channel_dir"] / f"{vid}.json").read_text(encoding="utf-8"))
        total = doc.get("duration_s") or 0
        for _ in range(windows):
            start = round(rng.uniform(0, max(0.0, total - seconds)), 1)
            text = " ".join(s["text"] for s in doc["segments"] if s["end"] > start and s["start"] < start + seconds)
            rows.append({"video_id": vid, "start_s": start, "end_s": round(start + seconds, 1),
                         "machine_text": text, "human_text": "", "notes": ""})
    write_csv(paths.qa / "qa_sample.csv", rows, ["video_id", "start_s", "end_s", "machine_text", "human_text", "notes"])
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--hash", action="store_true")
    ap.add_argument("--qa-sample", type=int, default=0, help="number of videos to sample")
    ap.add_argument("--windows", type=int, default=3, help="windows per sampled video")
    ap.add_argument("--window-seconds", type=int, default=60)
    ap.add_argument("--seed", type=int, default=20261111)
    a = ap.parse_args()
    paths = layout(ensure_outside_git(a.root))
    n_audio, bad_a = check_audio(paths, a.hash)
    n_tr, bad_t = check_transcripts(paths, a.hash)
    print(f"audio ok: {n_audio} | transcripts ok: {n_tr} | problems: {len(bad_a) + len(bad_t)}")
    for line in (bad_a + bad_t)[:50]:
        print("  " + line)
    if a.qa_sample:
        print(f"wrote {qa_sample(paths, a.qa_sample, a.windows, a.window_seconds, a.seed)} QA windows to {paths.qa / 'qa_sample.csv'}")
    sys.exit(1 if (bad_a or bad_t) else 0)


if __name__ == "__main__":
    main()
