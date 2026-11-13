# Roadmap: audio and transcripts for the rest of the channels

Written 2026-11-11. The plan for taking the ET-channelers work from "466 videos indexed, 75 Bashar recordings partly read" to "every video on every tracked channel as private audio plus a timestamped transcript", and then to analysis and a paper. The tooling is in [`pipeline/`](pipeline/README.md); the channel table is in the [README](README.md#plan-for-the-rest) and in [`plan/channel_inventory.csv`](plan/channel_inventory.csv). Everything here is an AI-written plan and has not been reviewed by a person; figures marked "estimate" are arithmetic on a sample, not measurements.

## 0. Update 2026-11-13: the lanes that work from a cloud server

Sections 1 to 6 below are the 2026-11-11 plan and are kept as written. This section records what changed.

**YouTube from a cloud server still does not work.** A second pilot on 2026-11-13 from a GitHub Codespace got
three bot checks in three requests, and the captions endpoint was refused the same way. Nothing here tries to
get past that. The YouTube lane is for the owner's own computer, and is now one command (`pipeline/run_all.py`).

**What does work is collecting the same recordings and their texts from where the makers publish them.** The
pipeline gained four lanes (podcast episodes, creator-hosted files, publisher texts, YouTube captions), a
catalogue, and a tool that uploads to a private store, checks the copy and frees the disk. See
[`pipeline/README.md`](pipeline/README.md) and [`sources/README.md`](sources/README.md).

Snapshot at 2026-11-13T17:55:28Z (the current table is [`plan/coverage.csv`](plan/coverage.csv); jobs were still
running when this was written):

| Measure | Count |
|---|---|
| People tracked (92 in the index plus 4 from the ArchiveShelf inventory) | 96 |
| People with at least one listed downloadable source | 15 |
| People with audio downloaded | 12 |
| Audio files downloaded and encoded | 235 (152.8 h) |
| Texts obtained from the source (publisher's own transcript) | 3114 (2,113,118 words) |
| YouTube caption tracks | 0 |
| Transcripts made here by speech-to-text | 1 (1,642 words) |
| Audio files still waiting for a transcript | 234 |
| Items linked to an indexed YouTube video | 1445 |

Sources found so far: podcast feeds for 10 people (Aaron Abke, Aetherius Society, Athina Król, Elizabeth
April, L/L Research, Lorie Ladd, Louise Kay, Pavlina Klemm, Steve Nobel, Suzanne Lie) and Sounds True; 1,306
free-audio files on kryon.com (2002 to 2020); the 106 Ra Contact session texts and 104 original session
recordings on llresearch.org; 4,958 posts on danielscranton.com, each the published text of one message; and
257 Sam the Illusionist session texts that the ArchiveShelf project had already collected.

**Measured limits of the cloud machine (2 CPU cores, 15 GB free).**

* Encoding is the bottleneck for downloads: about 35 times real time per core at libopus complexity 10, about
  140 times at complexity 5 (4.3 against 13.1 CPU-seconds for a 10-minute file, 4.6% more bytes). The new lane
  uses 5.
* Speech-to-text with `base.en` ran at 7.0 times real time on the idle machine and 1.3 times while downloads
  were running. The whole set needs a GPU or the machine to itself.
* The disk cannot hold everything, so the downloader stops at a free-space floor and `sync_archive.py` exists.

**Open, in order.**

1. Put the collected audio and texts in a private store. The owner's `archiveshelf` repository was public on
   2026-11-13 and the cloud session's token could not write to it; `sync_archive.py` refuses a store that is
   not private. Make the repository private, then run `sync_archive.py push`.
2. Run the YouTube lane on the owner's computer with `run_all.py` (audio and captions for the queued videos).
3. Confirm or reject the 63 candidate feeds (`<root>/sources/feed_candidates.csv`). Likely own shows held back
   only because the title does not carry the name: Erin Lyons, Paul Hamden, Lauren Galey, and a second Aaron
   Abke show.
4. Transcribe on a GPU; compare a sample against the publisher's text where both exist (Ra, Daniel Scranton)
   to measure word error rate without a human transcriber.
5. Find sources for the 81 people who have none yet.
6. Merge the three bodies of work: ArchiveShelf as a filtered snapshot without its history (four independent
   reads agreed its history would put 257 third-party transcripts into this public repository), and one
   registry of people, channels and items across this index, ArchiveShelf and channels-ET.

## 1. Where things stand

| Item | State (2026-11-11) |
|---|---|
| Inventory of the 92 tracked people and groups, with video totals | done; 48 have a channel video count, 44 do not |
| Queue builder, channel lister, audio downloader, transcriber, verifier, public export, machine check | built; automated tests pass with stand-in tools |
| Real-tool checks that can run offline | done: ffmpeg encode, faster-whisper `tiny.en` on a public speech clip, yt-dlp option parsing |
| Real YouTube download | **tried once, refused.** From a cloud server, 3 of 3 pilot videos were refused (two bot checks, one HTTP 403). The run stopped by design. Nothing was downloaded. |
| GPU transcription speed, Windows run, long batches | not measured, not tested |
| Push to GitHub | not done from the cloud session (the repository was not enabled for it); the commit is delivered as a git bundle |
| Dashboard | [Channeler YouTube index](https://claude.ai/artifact/XFQHVyn2WSk7Xnn4yXpAa8) (owner's login). It shows the 2026-10-23 crawl and is not yet refreshed from `discover.py` output. |

The one hard fact that shapes the plan: **YouTube refuses automated downloads from cloud-server addresses, so the download step runs on the owner's own computer.** The scripts are built to stop on a block rather than retry into it, and they use no cookies, logins, proxies, alternative clients or mirror sites. If a block also appears on the owner's computer, the plan does not route around it: use audio files that are already held, wait, or narrow the set.

## 2. Size of the job

All figures come from [`plan/estimates.json`](plan/estimates.json) and are recomputed by `python3 et-channelers/pipeline/inventory.py`.

| Quantity | Value | Basis |
|---|---|---|
| Tracked entries / entries with a video count | 92 / 48 | `youtube_index.json`, observed 2026-10-23 |
| Videos on those 48 channels | 40,652 | sum of channel counts; the other 44 entries add an unknown amount, so this is a floor |
| Channels over 1,000 videos / median channel | 14 / 403.5 videos | same |
| Mean length in the measured sample | 19.8 min (median 13.1) | 449 videos from 16 crawled channels; 20.3% under 5 min, 7.8% over an hour |
| Audio, central estimate | 14,223 h | each channel's count times its own mean length (pooled mean where fewer than 10 lengths were read) |
| Audio, plausible range | 9,464 to 16,048 h | total videos times the first and third quartile of channel mean lengths |
| Disk at mono Opus 24 kbps / 32 kbps | 154 GB / 205 GB | 10.8 MB per hour at 24 kbps |
| Bashar pilot set (75 recordings) | about 141.3 h, about 1.5 GB at 24 kbps | 1,186,510 words in `data/videos.json` at an assumed 140 words per minute |
| Bashar official channel | 322 videos | channel count in the index (the 75 pilot recordings are mostly on other people's channels) |

Transcription time depends on one number nobody has measured here: how many times faster than real time the owner's GPU runs the chosen model.

| If the GPU runs at | All 14,223 h | Bashar-75 (141.3 h) |
|---|---|---|
| 15 times real time | 948 h | 9.4 h |
| 30 times | 474 h | 4.7 h |
| 60 times | 237 h | 2.4 h |
| 120 times | 119 h | 1.2 h |

For scale, the faster-whisper project's own benchmark reports 13 minutes of audio in 17 seconds with batching for `large-v2` on an RTX 3070 Ti 8 GB, about 46 times real time. That is the library authors' figure on their hardware, not a promise for this laptop; Phase 2 measures the real one. At those speeds the full set is a multi-week job for one GPU, which is why Phase 5 samples before Phase 6 scales.

## 3. Phases

Each phase has an exit test. Do not start the next phase until the test passes.

### Phase 0: access and setup (about an hour)

* Give the next session access to the repository (attach it in the app) so `git push` works, **or** use the git bundle below. Revoke the access token that was pasted into chat on 2026-11-11 (it also expires on its own on 2026-11-12).
* Decide where the private data lives. Recommended: audio and transcripts in a folder outside any Git checkout (default `~/et-channelers-private`), synced to Google Drive by Drive for Desktop; manifests, queue and QA sheets also in a **private** repository. GitHub rejects files over 100 MB and LFS quotas are small, so audio does not belong in a Git repository.
* Install Python, ffmpeg and the requirements; run `doctor.py`. Exit test: `doctor.py` prints no `MISSING`.

### Phase 1: Bashar-75 audio pilot

* `select_jobs.py --set bashar75`, dry run, then `download_audio.py --limit 3 --workers 1 --min-interval 3`, then `--all --workers 3 --min-interval 3`.
* If the output says `STOPPED`, stop. Do not retry through another route. Wait, lower the rate, or fall back to audio already held.
* Exit test: `verify.py --hash` reports no problems; every record in `audio_manifest.jsonl` is `ok` or has a recorded reason (`unavailable`, `login_required`); the list of unread ids is written down (20 of the 75 transcript pages errored earlier, so some of those videos may be gone or have no captions).

### Phase 2: transcription benchmark (about half a day)

* Pick 5 videos of different lengths. Run `tiny.en`, `small.en`, `distil-large-v3` and `large-v3` on them (`transcribe.py --limit 5 --model ...`). Record speed (times real time), VRAM, and word error rate against a hand-corrected 60-second window (`verify.py --qa-sample`).
* Check whether names come out right ("Bashar", "Darryl Anka", "Kryon" and the other channelers' names); if not, test whether hot-word hints help.
* Pin the winner: note the model repository, revision (`--model-revision`) and the weight hash the manifest records.
* Exit test: a chosen model, revision and batch size, with measured speed and error rate, written into this file.

### Phase 3: Bashar-75 transcripts and quality check

* Transcribe all downloaded recordings with the pinned model. Run `verify.py --hash --qa-sample 20` and have a person correct the sample windows (Channeling Atlas roadmap item N4).
* Exit test: word error rate on the sample is reported with its interval; transcripts with no segments or with repeated-phrase hallucinations are listed and rerun.
* This replaces the 12 hand-saved auto-caption files and the 20 unread pages as the base for the Bashar questions (names, astrology and calendars, and so on).

### Phase 4: finish the channel inventory

* Run `discover.py` on the 48 channels that have a URL (public metadata; minutes to an hour at a polite rate, depending on channel sizes). It records coverage against the expected count.
* Read the video lists for the 38 `metadata-only` channels, and search for the 31 `no_youtube` and 7 `not_found` people. The 44 entries with no count add to every total in this file.
* Refresh the dashboard from the new tables.
* Exit test: every entry has a count or a recorded reason it has none; `inventory.py --update-readme` regenerates the README table.

### Phase 5: selection rule and pilot on the wider set

* Decide the sampling rule before looking at transcripts (Atlas roadmap item N3): for example, a seeded sample of up to 20 videos per channel, 5 minutes to 3 hours long, flagged as channeling or not, English or auto-detected. `select_jobs.py` writes the seed, rule and input hashes next to the queue so the draw can be reproduced and reported.
* Pilot on 10 channels. Measure disk, hours, block rate and error rate.
* Exit test: the rule is written down and justified; the pilot's numbers replace the estimates above.

### Phase 6: scale out

* Run the selected set with shards across machines if more than one is available (`--shard 0/2`, `--shard 1/2`). Keep `--workers` low and `--min-interval` high; slower is better than blocked.
* Remove duplicates and re-uploads by audio fingerprint, not by title (Atlas item N5).
* Exit test: `verify.py --hash` clean; coverage table by channel; error classes tallied.

### Phase 7: analysis

* Questions to answer from the transcripts: how channelers use names, calendars and astrology, what they say about themselves and each other, and how the wording spreads between channels. Use the same denominators as the Atlas only after its identity audit (item N1).
* Quotes in any write-up stay at 30 words or fewer, with the recording and time stamp.

### Phase 8: release gate

* Nothing from the audio or the transcript text is published before the paper, and then only what the rights allow. The publishable part is `media_manifest_public.csv` (durations, sizes, hashes, counts, model and revision) and derived numbers.
* Before release: a rights check on every source, the Atlas release checklist (item N8), and a run of `guard_no_raw_media.py` over the repository.

## 4. Decisions still open

| # | Question | Default if nobody decides |
|---|---|---|
| D1 | What is "all Bashar videos": the 75 recordings in the index, or also the 322 on the official channel and every re-upload? | the 75, then the official channel |
| D2 | Which Whisper model? | decided by the Phase 2 benchmark |
| D3 | Language: force English or detect? | English for Bashar, detect for the rest |
| D4 | Sampling rule for the wider set | up to 20 per channel, seeded, 5 min to 3 h |
| D5 | Where does audio live, and for how long? | outside Git, synced to Drive, kept until the paper is final |
| D6 | Use captions where good ones exist, and transcribe only the gaps? | captions as a cross-check only, so every video is transcribed the same way |
| D7 | Make the repository private, or keep it public with data kept elsewhere? | public code and plan; private data |

## 5. Risks

| Risk | What it does | What the plan does about it |
|---|---|---|
| YouTube refuses downloads (seen on 2026-11-11 from a cloud server) | no audio | run from the owner's computer; the scripts stop after three blocks; no workaround is used; fall back to audio already held |
| Rights and terms | media is held by its rights holders; downloading is outside YouTube's terms | private storage, hashes only in public outputs, release only with the paper after a rights check |
| Speech-to-text errors on names, music, silence | wrong words, invented text in silent parts | voice-activity filter on; human-checked sample; pin the model; list files with no or repeated segments |
| Library changes | tools break between versions (already happened once: faster-whisper with PyAV 19) | versions in the requirements and the manifests; decoding done by ffmpeg; tests |
| Counts drift | the totals are from 2026-10-23 and are floors | `discover.py` records coverage; `inventory.py` regenerates the tables |
| Duplicates and re-uploads | the same session counted twice | fingerprint audio before analysis |
| Disk and time | 154 GB of audio and weeks of GPU time for the full set | sample first (Phase 5); measure before scaling |
| Data leaks into the repository | rights breach | `.gitignore` rules, Git-folder refusal in every script, `guard_no_raw_media.py`, review before each push |

## 6. Next session: checklist and starter prompt

1. **Get the commit onto your computer.** The cloud session could not push, so it delivered the work as `et-channelers-youtube-index.bundle` (and a zip of the folder). In your clone of the repository:

   ```sh
   git clone https://github.com/occult-kranti/bashar-index.git      # or open your existing clone, on main and up to date
   cd bashar-index
   git fetch <path to>/et-channelers-youtube-index.bundle research/et-channelers-youtube-index:research/et-channelers-youtube-index
   git switch research/et-channelers-youtube-index
   git push -u origin research/et-channelers-youtube-index         # your own GitHub login
   ```

   Open a pull request into `main`; the repository's convention is that `main` takes reviewed work through branches.
2. **Set up the machine.** Follow the Setup section of [`pipeline/README.md`](pipeline/README.md) in the VS Code terminal, ending with `doctor.py`.
3. **Run the pilot.** Dry run, then 3 videos, then the rest of Bashar-75 (Phase 1).
4. **Start Claude Code in that folder** and give it this prompt:

   > Read `et-channelers/ROADMAP.md` and `et-channelers/pipeline/README.md`. Run `doctor.py`, fix anything it reports, then run the Phase 1 pilot (3 videos) and show me the first lines of `audio_manifest.jsonl`. If any command prints STOPPED, stop and tell me; do not use cookies, proxies, other player clients or mirror sites to get past a block. Keep all audio and transcripts outside the repository, and run `et-channelers/scripts/guard_no_raw_media.py` before every commit.

5. **Keep the data private.** The default folder `~/et-channelers-private` is outside the repository. For Drive, point `--root` at a Drive for Desktop folder outside the repository.
6. **Decide D1, D3 and D7** from section 4 before Phase 3.
