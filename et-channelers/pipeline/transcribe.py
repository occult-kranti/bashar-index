#!/usr/bin/env python3
"""Parallel, resumable speech-to-text with faster-whisper. Transcripts never go into Git.

Reads    <root>/audio/<channel_dir>/<video_id>.<ext>
Writes   <root>/transcripts/<channel_dir>/<video_id>.json   segments with timestamps and confidence
         <root>/transcripts/<channel_dir>/<video_id>.txt    plain text
         <root>/transcripts/transcripts_manifest.jsonl      one line per video (model, speed, hashes)

One process per GPU (--devices 0,1) or per CPU worker (--workers N). Videos are split longest-first
so the processes finish together (with --order round-robin they are dealt out in turn instead, so every
folder gets text early), and reruns skip finished videos.

    python3 pipeline/transcribe.py --limit 3 --model small.en --device cpu      # smoke test
    python3 pipeline/transcribe.py --model large-v3 --devices 0                  # one GPU
    python3 pipeline/transcribe.py --model distil-large-v3 --devices 0,1 --batch-size 24
    python3 pipeline/transcribe.py --engine stub --limit 3                       # no model, for tests
Pin the model for a paper: pass --model-revision <commit> (or a local folder as --model). The manifest
stores the model repo and revision, the SHA-256 of its weights, library versions, and the audio and text hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (AUDIO_EXT, ITEM_RE, add_root_arg, lane_of, append_jsonl, archived_ids, atomic_write_text, ensure_outside_git,  # noqa: E402
                    latest_by_key, layout, lpt_assign, normalise_text, parse_shard, probe_duration, read_jsonl,
                    sha256_file, sha256_text, stable_shard, utc_now)


class StubEngine:
    """Deterministic fake used by the tests: no model, no GPU."""

    def __init__(self):
        self.info = {"engine": "stub", "engine_version": "0", "model": "stub",
                     "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}

    def transcribe(self, path, a):
        data = Path(path).read_bytes()
        if data.startswith(b"CORRUPT"):
            raise ValueError("stub: cannot decode audio")
        if data.startswith(b"CRASH"):
            os._exit(11)                              # the process is gone, as after a fault in a native library
        if data.startswith(b"KILLME"):                # stopped from outside, once: the file itself is fine
            flag = Path(path).with_suffix(".killed-once")
            if not flag.exists():
                flag.write_text("x")
                os.kill(os.getpid(), 15)
                time.sleep(5)
        time.sleep(a.stub_delay)
        digest = hashlib.sha256(data).hexdigest()
        segs = [{"id": i, "start": i * 5.0, "end": i * 5.0 + 4.0, "text": f"stub segment {i} {digest[:8]}",
                 "avg_logprob": -0.1, "no_speech_prob": 0.01} for i in range(3)]
        return segs, {"language": "en", "language_probability": 1.0, "duration": probe_duration(path) or 15.0}


def decode_audio(path, ffmpeg="ffmpeg", sample_rate=16000):
    """Decode any audio file to mono float32 samples with ffmpeg (already required for downloads).
    faster-whisper's own decoder calls av.open(..., metadata_errors=...), which current PyAV releases
    reject (faster-whisper 1.2.1 + av 19), so the pipeline never relies on it."""
    import numpy as np
    done = subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(path), "-vn",
                           "-map", "0:a:0", "-ac", "1", "-ar", str(sample_rate), "-f", "f32le", "-"],
                          capture_output=True)
    if done.returncode != 0 or not done.stdout:
        raise RuntimeError("ffmpeg could not decode the file: " + done.stderr.decode("utf-8", "replace").strip()[-300:])
    return np.frombuffer(done.stdout, dtype=np.float32)


def describe_model(path):
    """Provenance for a model folder without leaking local paths: repo id and revision if it sits in the
    Hugging Face cache, otherwise the folder name, plus the hash of the weights."""
    p = Path(path)
    info = {"model": p.name}
    parts = p.parts
    for i, part in enumerate(parts):
        if part.startswith("models--") and i + 2 < len(parts) and parts[i + 1] == "snapshots":
            info["model"], info["model_revision"] = part[len("models--"):].replace("--", "/"), parts[i + 2]
    if (p / "model.bin").exists():
        info["model_bin_sha256"] = sha256_file(p / "model.bin")
    return info


class FasterWhisperEngine:
    def __init__(self, a):
        try:
            import faster_whisper
            from faster_whisper import BatchedInferencePipeline, WhisperModel
            from faster_whisper.utils import download_model
        except ImportError:
            raise SystemExit("faster-whisper is not installed: pip install -r pipeline/requirements.txt")
        kwargs = {"device": a.device, "compute_type": a.compute_type}
        if a.cpu_threads:
            kwargs["cpu_threads"] = a.cpu_threads
        # resolve a model name to a concrete (optionally pinned) snapshot first, so its identity can be recorded
        path = a.model if Path(a.model).is_dir() else download_model(a.model, revision=a.model_revision or None)
        self.model = WhisperModel(path, **kwargs)
        self.batched = None if a.no_batch else BatchedInferencePipeline(model=self.model)
        self.info = {"engine": "faster-whisper", "engine_version": faster_whisper.__version__,
                     **describe_model(path), "device": a.device, "compute_type": a.compute_type,
                     "batch_size": None if a.no_batch else a.batch_size, "vad_filter": True, "audio_decoder": "ffmpeg"}

    def transcribe(self, path, a):
        common = dict(language=None if a.language == "auto" else a.language, beam_size=a.beam_size, vad_filter=True)
        audio = decode_audio(path, a.ffmpeg)
        if self.batched is not None:
            segments, info = self.batched.transcribe(audio, batch_size=a.batch_size, **common)
        else:
            segments, info = self.model.transcribe(audio, condition_on_previous_text=False, **common)
        segs = [{"id": i, "start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                 "avg_logprob": round(s.avg_logprob, 4), "no_speech_prob": round(s.no_speech_prob, 4)}
                for i, s in enumerate(segments)]
        return segs, {"language": info.language, "language_probability": round(info.language_probability, 4),
                      "duration": round(info.duration, 2)}


def load_engine(a):
    return StubEngine() if a.engine == "stub" else FasterWhisperEngine(a)


def manifest_records(out_dir):
    records = read_jsonl(out_dir / "transcripts_manifest.jsonl")
    for part in sorted(out_dir.glob("transcripts_manifest.part-*.jsonl")):
        records += read_jsonl(part)
    return records


def merge_parts(out_dir):
    main = out_dir / "transcripts_manifest.jsonl"
    for part in sorted(out_dir.glob("transcripts_manifest.part-*.jsonl")):
        taken = part.with_name(part.name + f".merging{os.getpid()}")
        os.replace(part, taken)                        # a worker still appending starts a fresh part file
        for rec in read_jsonl(taken):
            append_jsonl(main, rec)
        taken.unlink()


def declared_languages(root, audio_meta):
    """{item id: 'de'} for recordings that came from a podcast feed which states its language."""
    stated = {}
    for rec in read_jsonl(layout(root).feeds / "feeds_manifest.jsonl"):
        if rec.get("feed_key") and rec.get("language"):
            stated[rec["feed_key"]] = str(rec["language"]).strip()[:2].lower()
    return {ident: stated[rec["feed_key"]] for ident, rec in audio_meta.items() if rec.get("feed_key") in stated}


def wanted_language(a):
    """The one language this run can produce, or 'auto'. A model whose name ends in .en knows English only."""
    return "en" if str(a.model).rstrip("/").endswith(".en") else (a.language or "auto").strip()[:2].lower() \
        if (a.language or "auto") != "auto" else "auto"


def find_jobs(a, audio_dir, out_dir):
    audio_meta = latest_by_key(read_jsonl(audio_dir / "audio_manifest.jsonl"))
    done = latest_by_key(manifest_records(out_dir))
    stored = archived_ids(a.root, "asr")   # transcripts already uploaded and removed here
    languages, want, other = declared_languages(a.root, audio_meta), wanted_language(a), {}
    only = {x.strip() for x in (a.only or "").split(",") if x.strip()}
    lanes = {x.strip() for x in (a.lanes or "").split(",") if x.strip()}
    i, n = parse_shard(a.shard)
    jobs = []
    for f in sorted(audio_dir.rglob("*")):
        if f.suffix.lower() not in AUDIO_EXT or not ITEM_RE.match(f.stem) or stable_shard(f.stem, n) != i:
            continue
        if any(part.startswith(".") for part in f.relative_to(audio_dir).parts):
            continue  # scratch folders such as .work
        chan = f.parent.name if f.parent != audio_dir else "unsorted"
        if only and chan not in only:
            continue
        if lanes and lane_of(f.stem) not in lanes:
            continue
        spoken = languages.get(f.stem, "")
        if want != "auto" and spoken and spoken != want:
            # An English-only model given German speech still writes confident English words. The feed
            # says what language it is in, so such a file waits for a run that asks for that language.
            other.setdefault((spoken, chan), 0)
            other[(spoken, chan)] += 1
            continue
        prev = done.get(f.stem)
        if prev and prev["status"] == "ok" and (f.stem in stored or (out_dir / chan / f"{f.stem}.json").exists()):
            continue
        if prev and prev["status"] == "error" and not a.retry_failed:
            continue
        weight = audio_meta.get(f.stem, {}).get("duration_s") or f.stat().st_size / 3000.0  # ~24 kbps bytes per second
        jobs.append({"video_id": f.stem, "channel_dir": chan, "path": str(f), "weight": float(weight)})
    for (spoken, chan), count in sorted(other.items()):
        how = "--model base.en" if spoken == "en" else f"a multilingual model: --model base --language {spoken}"
        print(f"left out: {count} recording(s) in {chan} are in '{spoken}' according to their feed, and this run is for "
              f"'{want}'. Run them with {how} --only {chan}", file=sys.stderr)
    return jobs


def run_jobs(a, jobs, manifest, out_dir, marker=None):
    """Transcribe the jobs one after another. `marker` is a file that names the job in hand: if the
    process dies (a fault inside a native library leaves no Python error), the restart reads it."""
    engine = load_engine(a)
    for job in jobs:
        rec = {"video_id": job["video_id"], "channel_dir": job["channel_dir"], "started": utc_now(), **engine.info}
        if marker is not None:
            atomic_write_text(marker, json.dumps({"video_id": job["video_id"], "channel_dir": job["channel_dir"]}))
        t0 = time.time()
        try:
            segs, info = engine.transcribe(job["path"], a)
            text = " ".join(s["text"] for s in segs).strip()
            doc = {"video_id": job["video_id"], "engine": engine.info, "language": info["language"],
                   "language_probability": info["language_probability"], "duration_s": info["duration"],
                   "segments": segs}
            target = out_dir / job["channel_dir"]
            atomic_write_text(target / f"{job['video_id']}.json", json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
            atomic_write_text(target / f"{job['video_id']}.txt", text + "\n")
            wall = max(time.time() - t0, 1e-6)
            rec.update(status="ok", duration_s=info["duration"], wall_s=round(wall, 1),
                       x_real_time=round(info["duration"] / wall, 1), language=info["language"],
                       language_probability=info["language_probability"], n_segments=len(segs),
                       n_words=len(text.split()), audio_sha256=sha256_file(job["path"]),
                       text_sha256=sha256_text(normalise_text(text)),
                       json_sha256=sha256_file(target / f"{job['video_id']}.json"))
        except Exception as exc:  # noqa: BLE001 - one bad file must not stop the batch
            rec.update(status="error", error_class=type(exc).__name__, error_tail=str(exc)[-300:])
        append_jsonl(manifest, rec)
    if marker is not None and marker.exists():
        marker.unlink()


def run_share(a, out_dir):
    """One worker process: its share of the jobs, minus what an earlier life of this worker settled."""
    part = out_dir / f"transcripts_manifest.part-{a.worker_index}.jsonl"
    marker = a.jobs_file.with_suffix(".current")
    settled = {r["video_id"] for r in read_jsonl(part)}
    if marker.exists():                                # the worker died with this file in hand
        try:
            fatal = json.loads(marker.read_text(encoding="utf-8"))
        except ValueError:
            fatal = {}
        if fatal.get("video_id") and fatal["video_id"] not in settled:
            append_jsonl(part, {"video_id": fatal["video_id"], "channel_dir": fatal.get("channel_dir", ""), "started": utc_now(),
                                "status": "error", "error_class": "worker_died",
                                "error_tail": "the worker process ended while this file was being transcribed"})
            settled.add(fatal["video_id"])
    jobs = [j for j in json.loads(a.jobs_file.read_text(encoding="utf-8")) if j["video_id"] not in settled]
    run_jobs(a, jobs, part, out_dir, marker)


def child_cmd(a, root, audio_dir, out_dir, jobs_file, k):
    cmd = [sys.executable, str(Path(__file__).resolve()), "--root", str(root), "--audio-dir", str(audio_dir),
           "--out", str(out_dir), "--engine", a.engine, "--model", a.model, "--model-revision", a.model_revision, "--ffmpeg", a.ffmpeg, "--device", a.device,
           "--compute-type", a.compute_type, "--batch-size", str(a.batch_size), "--language", a.language,
           "--beam-size", str(a.beam_size), "--cpu-threads", str(a.cpu_threads),
           "--stub-delay", str(a.stub_delay), "--jobs-file", str(jobs_file), "--worker-index", str(k)]
    return cmd + (["--no-batch"] if a.no_batch else [])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--audio-dir", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--engine", choices=("faster-whisper", "stub"), default="faster-whisper")
    ap.add_argument("--model", default="large-v3", help="model name or a local folder (pin this for a paper)")
    ap.add_argument("--ffmpeg", default="ffmpeg", help="used to decode audio for the model")
    ap.add_argument("--model-revision", default="", help="Hugging Face commit to pin (recorded in the manifest)")
    ap.add_argument("--device", default="auto", choices=("auto", "cuda", "cpu"))
    ap.add_argument("--compute-type", default="auto", help="auto, float16, int8_float16, int8 ...")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--no-batch", action="store_true", help="use plain sequential decoding")
    ap.add_argument("--language", default="en",
                    help="'en', another two-letter code, or 'auto'. Recordings whose podcast feed states a different "
                         "language are left out and named, so they can be run with a model that knows it")
    ap.add_argument("--beam-size", type=int, default=5)
    ap.add_argument("--workers", type=int, default=1, help="processes (ignored when --devices is given)")
    ap.add_argument("--devices", default="", help="GPU ids, one process each, e.g. 0,1")
    ap.add_argument("--cpu-threads", type=int, default=0, help="threads per process (0 = library default)")
    ap.add_argument("--restarts", type=int, default=20,
                    help="how often one worker process is started again after ending early. A worker that ended by "
                         "itself skips the file it was on; one stopped from outside tries it again")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="comma-separated audio folders (person ids)")
    ap.add_argument("--lanes", default="", help="comma-separated kinds of item: ia (archive.org), pod (podcast), "
                                                "web (the maker's site), youtube; default all")
    ap.add_argument("--order", choices=("as-is", "round-robin"), default="as-is",
                    help="round-robin: one file per folder in turn, shortest first")
    ap.add_argument("--shard", help="i/n")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--stub-delay", type=float, default=0.05, help=argparse.SUPPRESS)
    ap.add_argument("--jobs-file", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--worker-index", type=int, default=0, help=argparse.SUPPRESS)
    a = ap.parse_args()

    root = ensure_outside_git(a.root)
    paths = layout(root)
    audio_dir = ensure_outside_git(a.audio_dir or paths.audio)
    out_dir = ensure_outside_git(a.out or paths.transcripts)
    out_dir.mkdir(parents=True, exist_ok=True)
    if a.jobs_file:  # child process: run its share and exit
        run_share(a, out_dir)
        return

    merge_parts(out_dir)
    jobs = find_jobs(a, audio_dir, out_dir)
    if a.order == "round-robin":  # one file per folder in turn, shortest first, so every person gets text early
        groups, mixed, depth = {}, [], 0
        for job in sorted(jobs, key=lambda j: (j["weight"], j["video_id"])):
            groups.setdefault(job["channel_dir"], []).append(job)
        while any(len(g) > depth for g in groups.values()):
            mixed += [groups[c][depth] for c in sorted(groups) if len(groups[c]) > depth]
            depth += 1
        jobs = mixed
    if a.limit:
        jobs = jobs[:a.limit]
    hours = sum(j["weight"] for j in jobs) / 3600
    devices = [d for d in a.devices.split(",") if d.strip()]
    workers = len(devices) or max(1, a.workers)
    print(f"{len(jobs)} to transcribe (about {hours:.1f} h of audio) with {workers} process(es)", file=sys.stderr)
    if not jobs:
        return
    manifest = out_dir / "transcripts_manifest.jsonl"
    if workers == 1:
        if devices:
            os.environ["CUDA_VISIBLE_DEVICES"] = devices[0]
        run_jobs(a, jobs, manifest, out_dir)
        return
    if devices and a.device == "auto":
        a.device = "cuda"
    if not a.cpu_threads and not devices:
        a.cpu_threads = max(1, (os.cpu_count() or workers) // workers)
    procs = []
    if a.order == "round-robin":
        # Dealing the list out like cards keeps the rotation inside every process. Splitting by length
        # (below) would put the longest recordings first and the last person's files hours away.
        parts = [jobs[k::workers] for k in range(workers)]
    else:
        parts = lpt_assign(jobs, workers, lambda j: j["weight"])
    def start(k):
        jobs_file = out_dir / ".jobs" / f"worker-{k}.json"
        env = dict(os.environ)
        if devices:
            env["CUDA_VISIBLE_DEVICES"] = devices[k]
        return subprocess.Popen(child_cmd(a, root, audio_dir, out_dir, jobs_file, k), env=env)

    running, restarts, failed = {}, {}, 0
    for k, part in enumerate(parts):
        if not part:
            continue
        stale = out_dir / ".jobs" / f"worker-{k}.current"
        if stale.exists():
            stale.unlink()                             # left by an earlier run: not this run's file in hand
        atomic_write_text(out_dir / ".jobs" / f"worker-{k}.json", json.dumps(part))
        running[k] = start(k)
    # A worker that dies (a fault in a native library gives no Python error) is started again and carries
    # on after the file it died on, so one bad file costs one file and not half of a two-day run.
    while running:
        for k, proc in list(running.items()):
            code = proc.poll()
            if code is None:
                continue
            del running[k]
            if code != 0 and restarts.get(k, 0) < a.restarts:
                restarts[k] = restarts.get(k, 0) + 1
                # Stopped from outside (terminated or killed, for instance when memory ran short): the file in
                # hand is not to blame and is tried again. Ended by itself: that file is skipped.
                outside = code in (-15, -9, -2, -1)
                marker = out_dir / ".jobs" / f"worker-{k}.current"
                if outside and marker.exists():
                    marker.unlink()
                print(f"worker {k} ended with code {code} ({'stopped from outside, its file is tried again' if outside else 'its file is skipped'}): "
                      f"starting it again ({restarts[k]} of {a.restarts})", file=sys.stderr, flush=True)
                running[k] = start(k)
            elif code != 0:
                failed += 1
        if running:
            time.sleep(0.2)
    merge_parts(out_dir)
    if failed:
        sys.exit(f"{failed} worker process(es) failed; rerun to continue")


if __name__ == "__main__":
    main()
