# Roadmap: audio and transcripts for the rest of the channels

Written 2026-11-11. The plan for taking the ET-channelers work from "466 videos indexed, 75 Bashar recordings partly read" to "every video on every tracked channel as private audio plus a timestamped transcript", and then to analysis and a paper. The tooling is in [`pipeline/`](pipeline/README.md); the channel table is in the [README](README.md#plan-for-the-rest) and in [`plan/channel_inventory.csv`](plan/channel_inventory.csv). Everything here is an AI-written plan and has not been reviewed by a person; figures marked "estimate" are arithmetic on a sample, not measurements.

## 0. Update 2026-11-13: the lanes that work from a cloud server

Sections 1 to 6 below are the 2026-11-11 plan and are kept as written. This section records what changed.

**YouTube audio and captions from a cloud server still do not work.** A second pilot on 2026-11-13 from a
GitHub Codespace got three bot checks in three requests, and the captions endpoint was refused the same way.
Nothing here tries to get past that. The YouTube lane is for the owner's own computer, and is now one command
(`pipeline/run_all.py`). (Listing what a channel holds does work from the cloud: see the end of this section.)

**What does work is collecting the same recordings and their texts from where the makers publish them.** The
pipeline gained four lanes (podcast episodes, creator-hosted files, publisher texts, YouTube captions), a
catalogue, and a tool that uploads to a private store, checks the copy and frees the disk. See
[`pipeline/README.md`](pipeline/README.md) and [`sources/README.md`](sources/README.md).

Snapshot at 2026-11-13T19:43:16Z (the current table is [`plan/coverage.csv`](plan/coverage.csv); jobs were still
running when this was written):

| Measure | Count |
|---|---|
| People tracked (92 in the index, 4 from the ArchiveShelf inventory, and Stewart Pearce, added 2026-11-13) | 97 |
| People with at least one listed downloadable source | 16 |
| People with audio downloaded | 13 |
| Audio files downloaded and encoded | 632 (363.7 h) |
| Texts obtained from the source (publisher's own transcript) | 5321 (3,792,150 words) |
| YouTube caption tracks | 0 |
| Transcripts made here by speech-to-text | 6 (23,038 words) |
| Audio files still waiting for a transcript | 626 |
| Items linked to an indexed YouTube video | 3275 |

Sources found so far: podcast feeds for 11 people (Aaron Abke, Aetherius Society, Athina Król, Elizabeth
April, L/L Research, Lorie Ladd, Louise Kay, Pavlina Klemm, Steve Nobel, Stewart Pearce, Suzanne Lie) and
Sounds True; 1,306
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

### Later on 2026-11-13: one list of everyone, whole channels counted, and what kind each recording is

**The channel listing answers from the cloud.** Audio and captions are still refused, but listing what a
channel holds asks for no video stream, and YouTube answers it. `discover.py` listed the Videos, Live and
Shorts tabs of all 63 channels with a usable address, without one refusal: 32,570 videos and 10,014 live
streams (21,269 hours where the length is given) and 16,115 shorts. That is the size of the YouTube job,
counted instead of estimated, and the queue for the owner's computer can now be built from complete lists
(`run_all.py` lists the channels first when asked for everything).

**One list.** [`plan/targets.csv`](plan/targets.csv) joins this index, the ArchiveShelf channel intake and
the people added since: 103 rows (102 people and groups, and one name left out at the owner's request).
The three truncated names of the ArchiveShelf intake were tied to channels by the channel's own name
(Pleiadian Laarkmaa, Rachel & Kevin Pasdon, LightingClarity); the owner has not confirmed them. Added at
the owner's request the same day: **Michelle Robinson Medium** (93 videos, 110 shorts, 11 posts saved) and
**Jamie Butler, The Everyday Medium**, who had been left out before (209 videos, 605 live streams, 550
hours listed; 25 posts saved; her old podcast feed is gone).

**The earlier Bashar Index work is used, not only cited.** Three tables are made from the data package at
the top of this repository:

* [`plan/bashar_recordings.csv`](plan/bashar_recordings.csv): the 75 digested recordings (27 channeled
  sessions, 27 clips of sessions, 21 interviews; 1,186,510 words read for the digests), each with whether it
  is still on YouTube (68 are; 6 are gone, 1 is private) and whether it is in the archive (5 are, as the
  same interview from the show's podcast).
* [`plan/bashar_sessions.csv`](plan/bashar_sessions.csv): its catalogue of 684 sessions since 1984. 393 point
  at a recording deposited on archive.org, which answers from a cloud server: 937 audio files (983 hours,
  mostly 1984 to 1999) and 153 video files of several gigabytes each. 274 sessions are only on the official
  streaming site, which is not collected.
* [`plan/bashar_podcasts.csv`](plan/bashar_podcasts.csv): the 48 podcast appearances it listed, with the
  type it gave and the kind found here.

**What kind of interview.** An interview is fetched only when the entity speaks in it, and the kind comes
from the transcript or the show notes, never from the title (`interview_types.py`). Nine interview shows
of the Bashar list have a verified podcast feed; their feeds hold 189 episodes that name 28 tracked people.
So far: 8 contain live channeling (fetched), 5 are unclear, 32 are conversations, 3 are commentary or
clips, and 141 are not classified because no transcript is held. Of the 42 that name Darryl Anka or
Bashar, the 13 classified so far are conversations, unclear or commentary: none has Bashar speaking,
whatever the title says. Twenty of those 42 were downloaded before this rule was set; they are kept, and
their kind follows from their transcripts as speech-to-text reaches them.

Snapshot at 2026-11-14T00:16Z, with downloads and speech-to-text running; the current figures are in
[`plan/targets_summary.json`](plan/targets_summary.json) and [`plan/coverage.csv`](plan/coverage.csv).

| Measure | Count |
|---|---|
| People and groups tracked | 102 |
| State: partly captured / planned, YouTube only / planned, no source yet / captured | 27 / 40 / 35 / 0 |
| Channels listed in full | 63 of 64 on record |
| Distinct pieces of work listed (a video and its podcast or page twin count once) | 69,186 |
| ... of which in the archive as audio or text | 8,568 |
| Listed YouTube items whose content is already here through a twin | 3,355 |
| Audio files held | 851 (510.6 h) for 19 people |
| Texts obtained from the source | 8,424 (13,308,502 words) for 18 people |
| Transcripts made here by speech-to-text | 53 (155,285 words), running |
| Audio waiting for a transcript | 793 |
| Bashar session audio listed on archive.org / queued for now | 937 files (983 h) / 180 files (176 h) |

Nobody is "captured": that state needs the person's channel to be listed and every listed item to be here,
and no YouTube audio can be fetched from this machine.

**Mistakes caught, each now stopped by a rule and a test** (details in
[`pipeline/README.md`](pipeline/README.md)): two podcasts by other people called Michelle Robinson were
accepted on the name; one German episode was transcribed with the English-only model; people were called
captured whose channel had not been counted; two unrelated shows passed for interview shows because their
long titles contained the same words; interviews were taken for channeling on the strength of their
titles; a course site and a mailing-list service were registered as two people's own websites; and a
speech-to-text worker stopped from outside left half of a run undone.

**Speech-to-text here.** The Codespace's two CPUs are one core. `base.en` runs at about 9 times real time
on the idle machine and well below that while downloads run, so the hours held take days; `tiny.en` is 1.8
times faster and a little less accurate; larger models are slower than that. A machine with eight real
cores or a GPU is the way to finish in hours.

**Open, in order** (this replaces the list above where they differ).

1. Put the collected audio and texts in a private store (unchanged: `archiveshelf` is public and this
   session cannot write to it). **The disk is now the limit**: about 180 of the 983 hours of Bashar session
   audio on archive.org fit; the rest waits for the store, which frees the disk as it uploads.
2. On the owner's computer: `run_all.py --go` for audio and captions of every listed video.
3. Speech-to-text for the interviews already held, so each gets its kind; then for the sessions.
4. The 153 archive.org video files of Bashar sessions (529 GB as video): fetch the audio track only, on a
   machine with room.
5. Interview shows: seven of the sixteen in the Bashar list have no feed registered, and the same lookup
   can be run for interview shows outside the list.
6. Confirm the three names tied to channels by name only.
7. Register the pages of the remaining official sites with `list_site_pages.py`, and confirm or reject
   the candidate feeds.
8. Find sources for the 35 people with no channel or site on record.
9. Merge ArchiveShelf's code as a filtered snapshot (unchanged).

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
