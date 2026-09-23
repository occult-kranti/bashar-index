"""acquisition.py — step zero: transcript/audio fetch pilot (B5).

Pre-registered plan (r2_design.md §4): fetch raw transcripts for all 75 video
IDs via the recorded digest_source (youtubetotranscript.com) with YouTube
timedtext captions via yt-dlp as fallback; archive raw with SHA-256; WER audit
(jiwer) gates stylometry. This module runs a PILOT of up to 5 IDs.

Honesty rule: if the network is blocked or a fetch fails, the failure is logged
per-ID and reported; NO transcript text is ever fabricated. Dry-run mode
(`--dry-run`) only enumerates targets and writes the plan.

WER realism (advisor ruling (e), implemented in the audit spec below):
  * Whisper large-v3 on 1984-96 cassette audio: 15% overall WER is a hope, not
    a gate; function-word WER <= 10% is harder, not easier.
  * A Whisper hallucination screen is mandatory (flag low-audio-energy /
    high-text-output spans; exclude them).
  * The pass-only-spans fallback induces era/audio-quality selection bias; the
    era-extension arm may degrade to descriptive. Stated now, in advance.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

import common
from common import RESULTS
import report

PILOT_N = 5
TIMEOUT_S = 45


def select_pilot():
    vmap = {v["video_id"]: v for v in common.load_videos()}
    pilot = []
    for d in common.load_digests():
        v = vmap[d["video_id"]]
        if v.get("year_reliable") and d.get("digest_source"):
            pilot.append({
                "video_id": d["video_id"],
                "digest_source": d["digest_source"],
                "content_type": v["content_type"],
                "year": v["year"],
            })
        if len(pilot) >= PILOT_N:
            break
    return pilot


def try_ytdlp(video_id: str, outdir: str):
    """Attempt timedtext auto-caption fetch via yt-dlp. Returns status dict."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--skip-download",
             "--write-auto-subs", "--write-subs", "--sub-langs", "en.*",
             "--sub-format", "vtt", "--no-warnings",
             "-o", os.path.join(outdir, f"{video_id}.%(ext)s"), url],
            capture_output=True, text=True, timeout=TIMEOUT_S)
        return {"ok": proc.returncode == 0,
                "elapsed_s": round(time.time() - t0, 1),
                "stderr_tail": (proc.stderr or proc.stdout)[-400:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "elapsed_s": TIMEOUT_S,
                "stderr_tail": f"timeout after {TIMEOUT_S}s"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "elapsed_s": round(time.time() - t0, 1),
                "stderr_tail": f"{type(e).__name__}: {e}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="enumerate targets and plan only; no network calls")
    args = ap.parse_args()

    outdir = os.path.join(common.HERE, "transcripts", "youtube")
    os.makedirs(outdir, exist_ok=True)
    pilot = select_pilot()

    env = {"yt_dlp_installed": False, "yt_dlp_version": None}
    try:
        import yt_dlp  # noqa: F401
        env["yt_dlp_installed"] = True
        env["yt_dlp_version"] = yt_dlp.version.__version__
    except ImportError:
        pass

    attempts = []
    blocked_reason = None
    if args.dry_run:
        blocked_reason = "dry-run mode requested; no network calls made"
    elif not env["yt_dlp_installed"]:
        blocked_reason = "yt-dlp not installable in this environment"
    else:
        for p in pilot:
            st = try_ytdlp(p["video_id"], outdir)
            attempts.append({"video_id": p["video_id"], **st})
            if not st["ok"]:
                tail = st["stderr_tail"].lower()
                if any(k in tail for k in ("timeout", "resolve", "network",
                                           "urlopen", "connection", "403",
                                           "429", "proxy")):
                    blocked_reason = (
                        "network/egress blocked or source unreachable "
                        f"(first failure: {p['video_id']}: "
                        f"{st['stderr_tail'][:160]})")
                    break

    fetched = [f for f in os.listdir(outdir) if f.endswith(".vtt")]
    n_ok = sum(1 for a in attempts if a["ok"]) + len(fetched)

    doc_extra = {
        "mode": "dry-run" if args.dry_run else "pilot",
        "targets_total_planned": 75,
        "pilot_ids": pilot,
        "attempts": attempts,
        "transcripts_fetched": n_ok,
        "blocked": blocked_reason is not None,
        "blockage_note": blocked_reason,
        "honesty": ("No transcript text was fabricated. Where fetching failed, "
                    "the failure is logged per-ID above. Stylometry (Q3) "
                    "remains BLOCKED until real transcripts pass the WER audit."),
        "wer_audit_spec": {
            "gates": {"overall_wer_max": 0.15, "function_word_wer_max": 0.10},
            "sample": "12 transcripts (4 interviews, 4 sessions, 4 archive.org)",
            "hallucination_screen": ("mandatory: flag low-audio-energy spans "
                                     "with high text output and exclude them "
                                     "(Whisper invents fluent text in "
                                     "low-signal regions)"),
            "realism_note": ("Advisor ruling (e): on 1984-96 cassette audio the "
                             "15%/10% gates are optimistic; the pass-only-spans "
                             "fallback induces era/audio-quality selection "
                             "bias — the era-extension arm may degrade to "
                             "descriptive. Stated in advance."),
            "status": "not run — no transcripts acquired",
        },
        "next_steps": [
            "run `python acquisition.py` in an environment with egress to "
            "youtubetotranscript.com / youtube.com",
            "archive raw text + .meta.json with SHA-256 manifest per §4 layout",
            "WER audit (jiwer) on the 12-transcript stratified sample",
            "6+6 matched-pair pilot -> empirical DeltaCE variance -> real "
            "bootstrap power analysis BEFORE the stylometry power statement",
        ],
    }
    tests = []  # no inferential tests in this module
    doc = report.finalize(
        "acquisition", tests,
        common.provenance(["data/videos.json", "data/digests/*.json"],
                          reverification="n/a"),
        grade="Speculative", digest_level="transcript", extra=doc_extra)
    path = report.write_results(doc, "acquisition_results.json")
    print(f"mode={doc_extra['mode']} fetched={n_ok} blocked={doc_extra['blocked']}")
    if blocked_reason:
        print("blockage:", blocked_reason)
    print("wrote", path)


if __name__ == "__main__":
    main()
