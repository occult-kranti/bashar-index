# Batch pipeline: audio and transcripts for the tracked channels

Code to take a list of YouTube videos to private audio files and timestamped transcripts, in parallel, with every step resumable. It was built on 2026-11-11 for the plan in [`../ROADMAP.md`](../ROADMAP.md). Everything is standard-library Python except the two external tools it drives (yt-dlp and faster-whisper) and ffmpeg.

**Status in one paragraph.** The code is written and covered by automated tests that use stand-in downloader and encoder tools. The parts that can run offline were also run for real: ffmpeg encoded mono Opus, faster-whisper `tiny.en` transcribed a public speech clip, and yt-dlp accepted every flag the scripts use. A real YouTube pilot was tried once from a cloud server and was refused on all 3 videos (two bot checks and one HTTP 403), so the scripts stopped, as designed. No audio has been downloaded. The download has to be run from the owner's own computer. Nothing was run on Windows or on a GPU.

## Rules for the data

| Data | Where it lives | May it go into Git? |
|---|---|---|
| Audio, captions, transcripts, QA sheets | the private folder (default `~/et-channelers-private`, set with `--root` or `$ET_PRIVATE_DIR`) | **No, never.** Every script refuses a folder inside a Git checkout. |
| Manifests (`audio_manifest.jsonl`, `transcripts_manifest.jsonl`), queue, discovery lists | the private folder | Only after review. They contain titles and error text. |
| `public_export/media_manifest_public.csv` | the private folder | Yes, after review. Numbers and hashes only: no text, no paths. |
| Inventory and estimates | [`../plan/`](../plan/) | Yes. Public metadata only. |

The recordings belong to their rights holders (the Bashar sessions: Darryl Anka / Bashar Communications, Inc.), and downloading media from YouTube is outside YouTube's terms unless a feature offers it. That is why the output is private and nothing derived from it is published before the paper. [`../scripts/guard_no_raw_media.py`](../scripts/guard_no_raw_media.py) fails if the repository holds audio, caption files, speech-to-text JSON, files over 5 MB, or credentials; run it before every push.

**What the scripts will not do.** They use no cookies, logins, proxies, alternative player clients or mirror sites. If YouTube answers with a bot check, HTTP 403 or 429, the run stops after three such answers in a row (exit code 3) and nothing is retried into the block. Removed, private and age-gated videos are recorded once and skipped on later runs. The tests assert that the command lines contain none of those options.

## Setup

You need Python 3.9 or newer, ffmpeg (with the libopus encoder), and for transcription an NVIDIA GPU is strongly recommended.

```powershell
# Windows PowerShell (macOS/Linux: use python3, source .../bin/activate, brew/apt for ffmpeg)
winget install Gyan.FFmpeg                         # once; open a new terminal afterwards
git clone <this repository>; cd <repository folder>
python -m venv $HOME\et-venv
& $HOME\et-venv\Scripts\Activate.ps1
pip install -r et-channelers\pipeline\requirements.txt
python et-channelers\pipeline\doctor.py --root $HOME\et-channelers-private
```

`doctor.py` lists what is installed, what is missing and how to fix it. It checks ffmpeg and libopus, yt-dlp, a JavaScript runtime (yt-dlp needs one for YouTube; `pip install deno` is in the requirements), faster-whisper, whether CTranslate2 sees a GPU, and the free space on the data drive. For GPU use, faster-whisper needs the NVIDIA cuBLAS and cuDNN 9 libraries for CUDA 12; see the GPU section of the [faster-whisper README](https://github.com/SYSTRAN/faster-whisper#gpu).

## Run order

```powershell
$P = "et-channelers\pipeline"
python $P\select_jobs.py --set bashar75                 # 1. queue of the 75 Bashar recordings
python $P\download_audio.py                             # 2. dry run: how many, how long, how much disk
python $P\download_audio.py --limit 3 --workers 1 --min-interval 3     # 3. pilot, 3 videos
python $P\download_audio.py --all --workers 3 --min-interval 3         # 4. everything in the queue
python $P\verify.py --hash                              # 5. sizes, hashes, durations
python $P\transcribe.py --limit 3 --model large-v3 --devices 0         # 6. transcription pilot on the GPU
python $P\transcribe.py --model large-v3 --devices 0 --model-revision <commit>   # 7. everything, model pinned
python $P\verify.py --hash --qa-sample 20               # 8. checks + sheet for a human word-error-rate check
python $P\export_public.py                              # 9. publishable numbers and hashes
```

If step 3 prints `STOPPED` (exit code 3), do not push on: wait, lower `--workers`, raise `--min-interval`, or stop. Finished items are skipped when you rerun. To work from audio you already hold, put files named `<11-character-video-id>.opus` (or `.m4a`, `.mp3`, `.wav`, ...) in `<root>/audio/<channel>/` and start at step 6.

For the other channels: `discover.py` lists every video on each tracked channel (public metadata), `select_jobs.py --set all --per-channel 20 --seed 7 --min-seconds 300` draws a reproducible sample, and the same download and transcription steps follow. Two machines can split a queue with `--shard 0/2` and `--shard 1/2`.

## The scripts

| Script | Job | Notable options |
|---|---|---|
| [`inventory.py`](inventory.py) | channel and video totals and hour/disk estimates from the committed index; rewrites the table in the README | `--update-readme`, `--refresh-bashar75` |
| [`select_jobs.py`](select_jobs.py) | builds the queue from the Bashar-75 list, the index, and discovery output | `--set bashar75\|indexed\|channeling\|all`, `--per-channel K --seed N`, `--min-seconds`, `--max-seconds`, `--order`, `--shards N`, `--export-ids` |
| [`discover.py`](discover.py) | every video on a channel via yt-dlp flat listing, one atomic file per channel, coverage against the expected count | `--only id,id`, `--workers`, `--min-interval`, `--retry-failed` |
| [`download_audio.py`](download_audio.py) | yt-dlp downloads a small audio stream to a scratch folder, ffmpeg re-encodes it to mono 16 kHz Opus, scratch is deleted | `--limit N` (pilot), `--all`, `--workers`, `--per-channel`, `--min-interval`, `--shard i/n`, `--bitrate`, `--limit-rate`, `--retry-failed` |
| [`transcribe.py`](transcribe.py) | faster-whisper with batching and VAD; one process per GPU; longest files first so processes finish together | `--model`, `--model-revision`, `--devices 0,1`, `--workers`, `--batch-size`, `--language en\|auto`, `--compute-type`, `--shard i/n` |
| [`verify.py`](verify.py) | file sizes, optional re-hash, audio-versus-listing length, transcript sanity, audio without transcript; builds the QA sheet | `--hash`, `--qa-sample N` |
| [`export_public.py`](export_public.py) | the publishable table: durations, sizes, hashes, language, word counts, model and revision, speed | `--out` |
| [`doctor.py`](doctor.py) | checks the machine | `--root`, `--need-gb` |
| [`common.py`](common.py) | shared helpers: manifests, shards, rate limiter, circuit breaker, Git guard | – |
| [`tests/test_pipeline.py`](tests/test_pipeline.py) | the automated tests | – |

## How it works

* **Resumable.** Each step appends one JSON line per item to a manifest (latest line wins). A rerun skips finished work, repairs missing files, and ignores a torn last line left by a crash. Files are written to a temporary name and renamed.
* **Parallel without overlap.** Videos are split across workers and machines by a stable hash of the id (`--shard i/n`), so shards never overlap and do not depend on Python's randomised `hash()`.
* **Polite.** A global limit on how often downloads start (`--min-interval`, with a little jitter), a per-channel cap on simultaneous downloads, and a scheduler that never leaves a worker idle behind a busy channel.
* **Stops instead of pushing through.** Three hard blocks in a row (bot check, 403, 429) trip a circuit breaker; a success resets the count. Only network errors are retried (exponential backoff). A re-encode failure is not retried.
* **Safe by default.** `download_audio.py` only prints its plan unless `--limit` or `--all` is given. Every script refuses a data folder inside a Git checkout.
* **Why ffmpeg encodes, not yt-dlp.** yt-dlp copies the stream unchanged when the source is already Opus, which would ignore the bitrate and channel settings. The pipeline downloads a stream and encodes it itself, so every file is mono 16 kHz Opus at the stated bitrate (24 kbps is about 10.8 MB per hour).
* **Why ffmpeg decodes, not PyAV.** faster-whisper 1.2.1 calls `av.open(..., metadata_errors=...)`, which PyAV 19 rejects, and its requirement is only `av>=11`, so a fresh install fails with `TypeError`. `transcribe.py` decodes with ffmpeg and hands the samples to the model. The test suite checks this.
* **Provenance.** Each audio record keeps the yt-dlp and ffmpeg versions and the target format. Each transcript record keeps the model repository, revision and weight hash, the library version, device, compute type, speed (times real time) and hashes of the audio, the JSON and the normalised text.

## Layout of the private folder

```
<root>/
  jobs/queue.csv, queue.meta.json            what was selected, with seed and input hashes
  discover/channels/<person>.jsonl           every video on a channel
  discover/videos_all.jsonl, discover_manifest.jsonl
  audio/<channel>/<video_id>.opus            re-encoded audio
  audio/audio_manifest.jsonl                 one line per attempt: status, bytes, sha256, duration, error class
  transcripts/<channel>/<video_id>.json|.txt
  transcripts/transcripts_manifest.jsonl
  qa/qa_sample.csv                           60-second windows for a human to correct
  public_export/media_manifest_public.csv    the only file meant to leave this folder
```

## What was tested

| Check | Result |
|---|---|
| Automated tests (stand-in yt-dlp and ffmpeg written to a temp folder; no network) | pass: scheduling, worker and channel caps, start-rate spacing, resume and repair, retries, unavailable and age-gated skipping, circuit breaker (stops after three blocks without retrying, not tripped by blocks separated by successes), shard partition, Git-folder refusal, no cookie or proxy options in the command lines, transcript worker processes and per-GPU device pinning, verify and QA sheet, public export has no text or paths, repository guard, doctor |
| Safety rails broken on purpose (breaker never counts, channel cap ignored, Git guard disabled, resume ignores the manifest) | the tests failed each time, so they do test those rails |
| Real ffmpeg | mono Ogg Opus produced from a 44.1 kHz stereo file; duration read back by ffprobe |
| Real yt-dlp (2026.10.26) | every flag the scripts use is accepted; no network used |
| Real faster-whisper 1.2.1, model `Systran/faster-whisper-tiny.en`, CPU int8, 2 vCPU | transcribed a 10-second public speech clip correctly (14.5 times real time, a figure that includes start-up and means nothing for a GPU); model repository, revision and weight hash recorded; this is how the PyAV problem was found |
| Real YouTube, from a cloud server (2026-11-11) | 3 of 3 pilot videos refused: two "confirm you're not a bot" responses and one HTTP 403. The breaker stopped the run. No workaround was tried. |
| Windows, a GPU, large models, long batches | **not tested** |

Run the tests with `python3 -I et-channelers/pipeline/tests/test_pipeline.py` (about 40 seconds; standard library only; the encoder and decoder tests are skipped if ffmpeg or numpy is missing).

## Known limits

* Audio at 24 kbps is a planning choice. Compare word error rate against a higher bitrate on the QA sample before committing to the full set.
* `--language en` is right for the Bashar sessions; some tracked channels are not in English, so use `--language auto` for the wider set.
* The yt-dlp listing returns what is public today, which can differ from the counts in the index (observed 2026-10-23); `discover_manifest.jsonl` records the coverage per channel.
* The stand-in tools cannot reproduce YouTube's behaviour. Treat the first real runs on your machine as the real test, and read the first lines of `audio_manifest.jsonl` after the pilot.
