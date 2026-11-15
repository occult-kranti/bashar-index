# Handoff, 2026-11-14: from the 2-core Codespace to the 16 GB one

Written for whoever picks this up next: the owner, or the Claude session in the new Codespace. The work so
far ran on a 2-core, 8 GB Codespace. Collection was paused on 2026-11-14 around 03:30 UTC so it can carry
on in a Codespace with 16 GB of memory (GitHub's 4-core machine: check with `nproc`). Nothing is lost by the
move: every file collected is in the private GitHub store, the pipeline's state is in a handoff release, and
a browsable copy of everything is on the owner's Google Drive. Section 9 is a prompt for the next session.

## 1. State in one paragraph

* **Collected:** 1,138 audio files (819.5 hours, 10.11 GB, mono 24 kbps Opus), 8,425 texts published by the
  sources themselves, and 61 speech-to-text transcripts (30.6 hours). Every one of them is in the private store.
* **Google Drive: done.** Everything collected by the pause is in the folder "ET Channelers Archive": 1,138
  recordings as 1,958 playable files of at most 7.3 MB (10.13 GB), and 40 text volumes. That is 1,998 files in
  77 folders, by person and source. The Bashar sessions downloaded since then are there too (next line): with
  them Drive holds 3,420 files (17.9 GB) in the same 77 folders.
* **Bashar's archive.org sessions** (his own channeled sessions, not interviews): **done on 2026-11-15.** All 903
  recordings are downloaded (911.3 hours by archive.org's listing), with no failures, and all 903 are on Drive
  (section 5). Their audio is in the private store and on Drive, not in this repository.
* **Podcast episodes:** 1,069 of 2,648 downloaded, 1,206.1 hours left (2026-11-15, 21:33 UTC). **Creators' own
  audio files** (Kryon's and L/L Research's sites): 111 of 1,410 downloaded, 1,299 left, of unknown length.
* **Interviews on other shows:** 29 of 30 downloaded.
* **Speech-to-text is the bottleneck.** This machine made about 1.3 hours of text per hour, so the backlog
  needs a faster engine or a GPU (section 6.1).
* **YouTube: the owner opted in on 2026-11-15** (section 6.6, choice b). YouTube steps now run with
  `ET_YOUTUBE_ROBOTS_OVERRIDE=1`. From this Codespace channel listings work, but YouTube answers audio and
  captions with its bot check, so those come from the owner's own computer.
* **Next task (set by the owner on 2026-11-15):** the newest 10, then 20, then 50 videos of every tracked
  channel, then a timeline of the predictions made on each channel (section 5). Decision 6.6 is made and the
  three queues are built; the downloads run on the owner's computer.
* **Prediction timelines, first pass (2026-11-15):** `prediction_timeline.py`, the rules pass of ANALYSIS_PLAN
  12.4, read all 9,467 items with text here and found 5,599 candidate statements about the future for 27 people
  (5,148 once near-copies are collapsed), 558 of them with a target window (section 5). Two samples labelled by
  two independent agent coders shaped and measured the rules: 42% of windowed candidates were real predictions at
  first, 54% to 62% under the rules as they now stand, after cutting blog comment threads that had been read as
  the source's words. They stay candidates, not findings, until the model pass.
* **Podcast backlog, this round downloaded (2026-11-15):** 351 new episodes queued (250-hour cap), all tried by
  20:51 UTC; 2 failed (one would not convert, one Kryon file is no longer offered). Three Drive rounds of the new
  audio (76, 170 and 348 files) bring Drive to 4,014 files (21.03 GB) in the same 77 folders; no audio is waiting
  for Drive. The next 250 hours (`select_episodes.py --max-hours 250`) wait for room: about 3 GB of the new
  audio stays on disk until it is transcribed, and 3.9 GB is free.

**Since the pause** (03:30 to 07:45 UTC, no collecting): the Drive copy was finished (the last 50 files were
17 Bashar sessions and 4 podcast episodes that had arrived after the Drive plan was made); the tables were
rebuilt from the store, so `plan/bashar_sessions.csv` counted the 262 sessions held then; the review fixes and the
YouTube robots.txt gate were finished; the deep research on the analyses was folded into `ANALYSIS_PLAN.md`;
`drive_stage.py` gained `round` and `done` for uploads made one call at a time.

**The pre-merge review** (07:56 to 09:30 UTC; five reviewers, and each finding checked by a second agent that
tried to refute it): 34 findings confirmed and fixed, 3 rejected. What matters for the next task:
* One refusal from archive.org's own host, or from one of its storage nodes, no longer holds back every queued
  Bashar session for a day or more. archive.org sends each file from one of about a hundred storage nodes, and
  Podbean a show's episodes from dozens: a success now counts for every host along the way, an item is held
  back only by the host that last answered for it, and a whole feed only when its last three items all came
  from one host that is being left alone (files without a feed are never grouped: archive.org keeps the files
  of one item together on one node).
* In the audio lane, no redirect is followed to a host that is being left alone, and every host a redirect leads to
  has its own start rate and its own Retry-After. A Retry-After sent with a 503 is obeyed too (audio, feeds, texts).
  Since then the feeds, texts and site-pages lanes follow the same redirect rules (section 7).
* A 429 for a site's robots.txt counts as a refusal, so the site rests on later runs as well.
* `drive_stage.py round` prints a round id, and `done --round <id>` must be given it. `done` records only the
  lines it is given (it used to give the ledger every earlier round again), and refuses a Drive id that the
  ledger already holds for another file.
* `keep_collecting.sh`: its lock is no longer inherited by the cycle and the sleep, so a loop stopped with
  `kill <pid>` can be started again at once.
* Corrected figures: archive.org hours are 911.3 (not 911.2; totals now add unrounded hours), captured audio
  819.5 hours, and the podcast backlog above.

**A second pass checked the fixes** (15:41 to about 17:00 UTC; five reviewers and five refuters): 20 more
findings, 18 confirmed and fixed, each with a test that fails without its fix where the fix is code. The ones that
change behaviour: a request already waiting for its turn obeys a Retry-After that arrives meanwhile; a success
no longer erases a refusal that came after the download started; a lone 403 or 429 still holds its host for the
Retry-After it carried, on later runs too; a huge Retry-After is capped at 32 days instead of crashing every
later run; robots.txt is read once per site, through the site's turn, and one 429 for it counts once; and
`done` refuses an upload whose file changed or left the plan after the round was printed, and lists the Drive
ids of uploads from an older round, to trash.

## 2. Where everything is

| What | Where |
|---|---|
| Code, tables, docs (public; never audio or transcript text) | `occult-kranti/bashar-index`, folder `et-channelers/` |
| Audio, transcripts, texts (private) | `occult-kranti/et-channelers-archive`, release `archive-v1`: checked tar bundles, read back with `sync_archive.py pull` |
| The same texts as plain files (private) | the same repository, folder `texts/` (person, then `from-source/` or `made-here/`) |
| ArchiveShelf's 16 podcast episodes (private) | the same repository, release `archiveshelf-podcast-audio-v1` (byte-identical to ArchiveShelf's, by GitHub's digests) |
| Pipeline state without media; the Kimi snapshot; reader notes; Claude's memory files | the same repository, release `handoff-2026-11-14`, with `SHA256SUMS` |
| The Drive ledger (the Drive id of every folder and file) | `<root>/sync/drive_manifest.jsonl`. The newest copy is the asset `drive_manifest.jsonl` of the release `handoff-2026-11-14`, newer than the one inside the state bundle (section 3, step 3) |
| Browsable copy by person | the owner's Google Drive, folder "ET Channelers Archive" (its read-me explains the layout): `03 Transcripts/<person>/`, `04 Audio/<person>/<source>/` |
| Collection dashboard | <https://claude.ai/artifact/898o4zpkocZ8qXjvR1xDfb> (a claude.ai "Data" page; datasets are this repository's `plan/*.csv`) |
| The old Codespace | still holds `/workspaces/et-channelers-private` until it is deleted. Do not delete it before the new one has been checked (step 4 below) |

## 3. Set up the new Codespace

Open the Codespace on `main` of `occult-kranti/bashar-index`, so the repository is at `/workspaces/bashar-index`. Then:

```bash
# 1. tools
sudo apt-get update && sudo apt-get install -y ffmpeg
python3 -m venv ~/et-venv && ~/et-venv/bin/pip install -r et-channelers/pipeline/requirements.txt

# 2. a GitHub login that can read and write the private repository. The Codespace's own token can reach only
#    bashar-index. Use a token of the owner's, kept in a file outside every repository (paste, then Ctrl-D),
#    or run `gh auth login`.
mkdir -p ~/.config/et-channelers && (umask 077; cat > ~/.config/et-channelers/github_token)
export GH_TOKEN="$(tr -d '[:space:]' < ~/.config/et-channelers/github_token)"; unset GITHUB_TOKEN

# 3. the private folder: outside the repository, on the disk that survives a rebuild
mkdir -p /workspaces/et-channelers-private && ln -sfn /workspaces/et-channelers-private ~/et-channelers-private
gh release download handoff-2026-11-14 -R occult-kranti/et-channelers-archive -D /tmp/handoff
(cd /tmp/handoff && sha256sum -c SHA256SUMS)
tar xzf /tmp/handoff/state-2026-11-14.tar.gz -C /workspaces/et-channelers-private
cp /tmp/handoff/drive_manifest.jsonl /workspaces/et-channelers-private/sync/drive_manifest.jsonl   # the newer ledger
tar xzf /tmp/handoff/scratch-notes-2026-11-14.tar.gz -C /workspaces/et-channelers-private   # crosswalks, judge snapshot
mkdir -p ~/.claude/projects/-workspaces-bashar-index \
  && tar xzf /tmp/handoff/claude-memory-2026-11-14.tar.gz -C ~/.claude/projects/-workspaces-bashar-index
mkdir -p /workspaces/_incoming/kimi-agent-youtube-et \
  && unzip -q /tmp/handoff/kimi-agent-youtube-et-channel-analysis.zip -d /workspaces/_incoming/kimi-agent-youtube-et \
  && tar xzf /tmp/handoff/incoming-notes-and-kimi-work-2026-11-14.tar.gz -C /workspaces/_incoming

# 4. the media, then a check: every kind should show on_disk_not_stored 0 and the counts in section 1
S=gh:occult-kranti/et-channelers-archive@archive-v1
~/et-venv/bin/python -I et-channelers/pipeline/sync_archive.py pull --root ~/et-channelers-private --store $S --kinds asr,pubtext
~/et-venv/bin/python -I et-channelers/pipeline/sync_archive.py pull --root ~/et-channelers-private --store $S --kinds audio --only darryl-anka
~/et-venv/bin/python -I et-channelers/pipeline/sync_archive.py status --root ~/et-channelers-private --store $S

# 5. the tables from what is here, and a check that the Drive ledger knows everything that is stored
for s in "catalog.py --publish" targets.py sources_table.py; do ~/et-venv/bin/python -I et-channelers/pipeline/$s --root ~/et-channelers-private; done
~/et-venv/bin/python -I et-channelers/pipeline/drive_stage.py status --out ~/et-drive/stage   # on_drive_files 1998
```

Pull other people's audio when it is about to be transcribed, not all at once. The disk is 32 GB, and the
sync deletes local audio once its stored copy is checked (`--only <person-id>` picks one person).

## 4. What was paused, and how to start it again

After a Codespace restart, one command starts every job below that is not running, the Drive hold and the
podcast backlog included:

```bash
ET_PRIVATE_DIR=~/et-channelers-private ET_DRIVE_HOLD=1 ET_BACKLOG_QUEUE=~/et-channelers-private/jobs/queue_backlog.csv \
  bash et-channelers/pipeline/resume_jobs.sh
```

| Job | Paused where | Start again with |
|---|---|---|
| Sync to the private store, every 5 minutes, and the text mirror every 30 | running again since 2026-11-15, 15:24 UTC, with every new file held until it is transcribed | `ET_GH_TOKEN_FILE=~/.config/et-channelers/github_token ET_HOLD_UNTRANSCRIBED=1 bash et-channelers/pipeline/save_to_github.sh` (with `ET_HOLD_UNTRANSCRIBED=1` the downloads stop at the disk floor until speech-to-text catches up; on a large disk `ET_HOLD_UNTRANSCRIBED_FOR=<person ids>` holds only those) |
| Bashar's archive.org sessions | finished on 2026-11-15: 903 of 903, no failures (the command skips them all) | `setsid nohup ~/et-venv/bin/python -I et-channelers/pipeline/download_enclosures.py --queue ~/et-channelers-private/jobs/queue_archive_org_all.csv --all --workers 2 --per-host 2 --min-interval 1.5 --min-free-gb 3 >> ~/et-channelers-private/logs/archive_org_download.log 2>&1 < /dev/null &` |
| Collection cycles: feeds, new episodes, texts, tables. They wait while another download runs | running again since 2026-11-15, 15:24 UTC (the listing step is skipped: the cycle does not set the YouTube override). Fixed that day: the 80-hour cap of `select_episodes.py` counted episodes already here, so every cycle chose the same newest, finished episodes and the backlog of about 1,900 did not move; now only new audio counts | `setsid nohup bash et-channelers/pipeline/keep_collecting.sh >> ~/et-channelers-private/logs/collect.log 2>&1 < /dev/null &` |
| Podcast backlog: the episodes and creators' files not here yet | started 2026-11-15, 16:52 UTC, from `jobs/queue_backlog.csv` (`select_episodes.py --max-hours 250`: 2,113 rows, 1,762 of them already here and not counted, 351 new); the Codespace restarted at about 18:37 UTC and `resume_jobs.sh` started it and the other jobs again: 302 left then; all 302 tried by 20:51 UTC, 2 failed (`pod-f2e693c0c4456d22` would not convert, `web-38f4fbcf72f5f65c` no longer offered) | `setsid nohup ~/et-venv/bin/python -I et-channelers/pipeline/download_enclosures.py --root ~/et-channelers-private --queue ~/et-channelers-private/jobs/queue_backlog.csv --all --workers 3 --per-host 2 --min-interval 1.5 --min-free-gb 3 >> ~/et-channelers-private/logs/backlog_download.log 2>&1 < /dev/null &` |
| Drive hold: new audio stays on disk until its Drive round is recorded | holder process and note `sync/holds/drive-<pid>.json`, refreshed after each round | `resume_jobs.sh` with `ET_DRIVE_HOLD=1` (a long `sleep` is the holder, found by `pgrep -n -f "^sleep 2592000$"`; `$!` after `setsid` is not its id), then after each Drive round `~/et-venv/bin/python -I et-channelers/pipeline/drive_hold.py --root ~/et-channelers-private` |
| Speech-to-text, Bashar's sessions first | 61 done; running again since 2026-11-15 on new files as they arrive (stored files must be pulled back to be transcribed). `keep_transcribing.sh` ends when nothing is left, so it runs inside a loop that starts it again every 30 minutes | `ET_ASR_WORKERS=1 ET_ASR_THREADS=2 setsid nohup bash -c 'while true; do bash et-channelers/pipeline/keep_transcribing.sh; sleep 1800; done' >> ~/et-channelers-private/logs/asr.log 2>&1 < /dev/null &` (2 cores: 1 worker; 4 cores: 2) |

Every job skips what is finished. Kill a job by its process id, never with `pkill -f`, which also matches the
shell that runs it.

To stop the collection loop and the cycle it is running together, kill its group: `kill -- -<pid>` (it was
started with `setsid`). `kill <pid>` stops the loop only; the cycle then finishes on its own.

Exit codes worth knowing: **8** means another cycle was already running (it holds the lock), so this one did
nothing; `keep_collecting.sh` tries again at its next cycle. **9** means a step was skipped by rule: a YouTube
step without `ET_YOUTUBE_ROBOTS_OVERRIDE=1`. `run_cycle.py` reports it as "skipped by rule" and goes on with the
next step, and `run_all.py` leaves the YouTube lanes out of its plan. In the cycle log a skipped listing shows
as "skipped by rule", not as a failure.

## 5. The next big task, and other work in progress

* **Next task (set by the owner on 2026-11-15): the newest videos of every tracked channel, then a timeline of
  predictions for each channel.**
  - **What.** The audio of the newest 10 videos of each of the 63 tracked YouTube channels first, then the newest
    20, then the newest 50; each tier includes the one before. Only the channel's "videos" tab: no shorts and no
    live streams. Audio only (mono 24 kbps Opus), like every lane.
  - **Size.** From the channel listings made on 2026-11-13, before the robots.txt rule (newest first; they carry no
    upload dates). None of these videos is here already by another route.

    | Tier | Videos | Hours | Audio, about | Speech-to-text at 1.3x / 9.2x real time |
    |---|---|---|---|---|
    | newest 10 | 612 | 233.4 | 2.7 GB | 7.5 / 1.1 days |
    | newest 20 | 1,200 | 496.0 | 5.7 GB | 15.9 / 2.2 days |
    | newest 50 | 2,920 | 1,217.0 | 14.0 GB | 39.0 / 5.5 days |

    3 channels have fewer than 10 videos, 5 fewer than 20 and 7 fewer than 50; for them the tier takes them all.
  - **What it needs, and where each stands (2026-11-15).**
    1. Decision 6.6: **made by the owner on 2026-11-15, choice (b)**. YouTube steps run with
       `ET_YOUTUBE_ROBOTS_OVERRIDE=1`.
    2. The owner's own connection. On 2026-11-15 a one-video probe from this Codespace, with the override set, got
       YouTube's bot check for audio and for captions (`error_class` `bot_check`; yt-dlp 2026.10.26 suggested
       cookies, which this project does not use). So the downloads run on the owner's computer (below), which
       puts each file in the private store; from there `drive_stage.py` copies it to Drive as before.
    3. A "newest N per channel" choice: **added on 2026-11-15**. `select_jobs.py --newest N` takes the first N of
       each channel's Videos tab in listing order (no request); `run_all.py --newest N` passes it on and lists
       only that much of each channel. Each queue now has its own meta file.
    4. Fresh listings: **made on 2026-11-15** from this Codespace, Videos tab only, 50 per channel, one request
       every 5 seconds: 63 channels, 2,920 videos, no failures, 15 of them new since 2026-11-13. They are in
       `/workspaces/et-yt-newest` (a root of their own, so the full listings of 58,699 videos are untouched).
    5. Upload dates: approximate ones come with the listing ("3 years ago"; `discover.py` now keeps them, which it
       missed before): 2,919 of 2,920. For older videos they are right to the year only; the download on the
       owner's computer records the exact date.
    6. Speech-to-text (6.1): on a 2-core machine the tiers take weeks, with a GPU or the faster engine days.
    7. The rules pass of the timelines: **built on 2026-11-15** (`pipeline/prediction_timeline.py`, ANALYSIS_PLAN
       12.4 step 1). Rules flag each sentence that speaks of the future (or hedges about it with a time) and has
       a time expression, a prediction word or a prophecy theme. Each time expression becomes a target window
       counted from the date said ("in two years" from 2021 is 2023; "by 2030" keeps one bound; "soon" gets
       none). The date said is the published date, else the listing's approximate upload date (`--listing`), else
       an ISO date in the title (L/L Research), else a year and month in the source address (Suzanne Lie's blog,
       L/L Research). What is dropped:
       - a window that ends before the date said (a past reference, even with "will" in the sentence), and in an
         undated item one that ends before 2000, or before the person's oldest dated item when that is older
         (L/L Research: 1974; `--undated-floor`);
       - promotion ("register now", prices, links) and page furniture (cross-links, comment counts, "Continue
         reading", e-mail addresses), questions (a questioner's guess is not the entity's claim), reports of
         earlier statements ("you said this was going to happen in 2008") and blog post date headers;
       - a blog's reader comments: the text is cut at Blogger's "N comments:" line. 893 of Suzanne Lie's 986
         posts carry a comment thread, about a quarter of the stored text, and before the cut most of her
         windowed candidates were readers' words (section 7).
       Near-copies are collapsed (12.4: shared five-word runs, Broder 1997, at a resemblance of 0.5): the first
       said keeps the statement, later copies are counted, and the timeline shows each once with how often it was
       said. Families of one event in different words are the model pass's work.
       Run over everything with text here (not yet the YouTube tiers): 9,467 items, 27 people, **5,599
       candidates, 5,148 distinct (5,490 from source texts, 109 from speech-to-text), 558 with a target window**,
       from 1977 (L/L Research) to 2075 (Aaron Abke), apart from an undated range from 1926 ("1926 to 2012", Sam)
       that the model pass must weed out; 1,540 are undated (Swaruu 703, Sam 627, Blossom Goodchild
       153, L/L Research 55, Jamie Butler 2). Per person and kind in `plan/prediction_counts.csv` (counts only);
       the candidates and timelines are in the private folder's `analysis/predictions/` (`<person>.jsonl`,
       `<person>.md`, quotes cut to 30 words).
    8. Two samples for the model pass: **run on 2026-11-15** (`pipeline/prediction_pilot.py`). Each is a seeded
       sample of windowed candidates shown without person, title or date (12.5), labelled by two agent coders
       working apart with the 12.4 types (prediction, conditional prediction, warning, prophecy, timeline as
       schedule, self-validation, refusal to date, future-tense teaching, not future, promotion). Both coders are
       runs of one model, so agreement is between two runs, not between people.

       | Sample | Units | Type kappa | Prediction-like kappa | Prediction-like (both coders) | Shaped which rules |
       |---|---|---|---|---|---|
       | pilot, 8 per person, 19 people | 106 | 0.90 | 0.98 | 44 (42%) | questions, reports, page furniture |
       | validation, 16 per person, the 7 largest (pilot excluded) | 112 | 0.88 | 0.91 | 61 (54%) | blog comments, post headers |

       Under the rules as they now stand, 82 pilot units and 97 validation units are still candidates, and no
       prediction of the source was lost (the one prediction-like unit cut was a reader's comment): 44 of 82 (54%)
       and 60 of 97 (62%) are prediction-like. Weighted by each person's windowed candidates, the validation
       sample gave 36% before the comment cut, since 528 of the 1,017 windowed candidates were Suzanne Lie's and 14
       of her 16 were comments or headers; after it, about 68%, but her share now rests on one unit. Both samples
       shaped the rules they measure, so a third, fresh sample must give the figure to quote. The samples, keys and
       labels are in `analysis/predictions/pilot_2026-11-15/` and `validation_2026-11-15/` (private). Next: the
       bulk model pass (is it the entity's claim; prediction or future-tense teaching; certainty; families
       linked), which waits for an API key and the owner's go-ahead on cost and data terms (12.5, D14); then the
       same over each YouTube tier as it is transcribed.
  - **The queues** (built on 2026-11-15 from those listings, in the private folder's `jobs/`):
    `queue_newest10.csv` (612 videos, 233.4 h), `queue_newest20.csv` (1,200, 496.2 h) and `queue_newest50.csv`
    (2,920, 1,216.9 h), each with its `.meta.json`. The columns add `tab`, `listing_rank` (0 is the newest) and
    `upload_date_approx`.
  - **On the owner's computer**, one tier after the other (each run skips what is already stored):

    ```powershell
    $env:ET_YOUTUBE_ROBOTS_OVERRIDE = "1"           # Unix shell: export ET_YOUTUBE_ROBOTS_OVERRIDE=1
    python et-channelers\pipeline\run_all.py --store gh:occult-kranti/et-channelers-archive@archive-v1 --lanes youtube,captions --newest 10        # the plan
    python et-channelers\pipeline\run_all.py --store gh:occult-kranti/et-channelers-archive@archive-v1 --lanes youtube,captions --newest 10 --go   # run it
    # then --newest 20 --go, then --newest 50 --go
    ```

    Then, in the Codespace: `sync_archive.py pull` the new audio and captions, `drive_stage.py` to Drive, rebuild
    the tables.
  - **Then the analysis, tier by tier.** For each channel, a timeline of the predictions in its videos, as
    ANALYSIS_PLAN 5.6 and 12.4 define them: every statement about the future (prediction, conditional
    prediction, warning, prophecy, "timeline" as a schedule; future-tense teaching is not one), with the date it
    was said (the upload date), its target window resolved from the time expression ("soon" gets no invented
    bounds), its certainty and specificity, and repeats linked into one claim. Texts from the source and
    speech-to-text stay apart. First a timeline from the newest 10, then grown with 20 and 50.
  - **Where it goes.** The timelines quote and paraphrase transcripts, so they stay private: the private store
    and Drive's "05 Analysis", quotes at most 30 words. This repository and the dashboard show counts only
    until the owner decides D16.

* **Every Bashar session on archive.org, downloaded and on Google Drive** (added at the owner's request).
  **Done on 2026-11-15.** The Bashar Index catalogued 684 sessions. 393 point at a recording somebody deposited
  on archive.org, which answers from a cloud server. archive.org lists 937 audio files there; 34 are a second
  encoding of a recording already counted, so there are **903 recordings (911.3 hours by archive.org's listing;
  six have no listed length)**. **All 903 are downloaded, with no failures, and all of them are on Drive** in
  "04 Audio / Darryl Anka / archive.org sessions". Their audio is in the private store (the private repository
  and its releases) and on Drive, never in this repository. 274 sessions are only on the official streaming
  site, which is paid and behind a login: not collected. These are channeled sessions, not interviews, so the
  interview rule (fetch only with live channeling) does not apply.

  How it was done: the archive.org download (section 4), and, as sessions arrived and were stored, rounds to
  Drive:

  ```bash
  S=~/et-drive/stage-bashar; X=<the Claude session's scratchpad>/drive_up
  ~/et-venv/bin/python -I et-channelers/pipeline/drive_stage.py plan    --out $S --only darryl-anka --kinds audio
  ~/et-venv/bin/python -I et-channelers/pipeline/drive_stage.py batches --out $S --n 1 --link-dir $X
  ~/et-venv/bin/python -I et-channelers/pipeline/drive_stage.py round   --out $S --size 200   # prints "round <id>"
  #   one Google Drive create_file call per line: title, parentId, base64Content = the ref ("sha256:<hex>:<path>"),
  #   contentMimeType audio/ogg, disableConversionToGoogleType true; then one "i <Drive id>" line per upload:
  ~/et-venv/bin/python -I et-channelers/pipeline/drive_stage.py done    --out $S --round <id> < ids.txt
  gh release upload handoff-2026-11-14 ~/et-channelers-private/sync/drive_manifest.jsonl -R occult-kranti/et-channelers-archive --clobber
  ```

  The copy of the 641 later sessions took 18 rounds (1,422 files) of `plan`, `batches`, `round` and `done`, and
  after each round its ledger (`sync/drive_manifest.jsonl`) was uploaded to the release `handoff-2026-11-14`.
  All of Bashar's archive.org sessions now fill 2,031 files (11.0 GB) on Drive. The tables were rebuilt on
  2026-11-15: `plan/bashar_sessions.csv` shows all 903 here (909.7 hours measured).

* **The podcast backlog, to Drive as it arrives.** The same rounds, with their own stage folder, over all new
  audio: `drive_stage.py plan --out ~/et-drive/stage-all --kinds audio --known-folder "04 Audio=<its id>"`,
  then `batches --link-dir <scratchpad>/drive_up/all`, `round`, the uploads and `done`, then `drive_hold.py`,
  then delete the staged copies (`files/` under the stage folder and the copies in the link folder) and upload
  the ledger. On 2026-11-15: round `5a85b2d7`, 76 files (0.39 GB), round `bfd76e68`, 170 files (0.93 GB),
  and round `78de76b5`, 348 files (1.79 GB, 206 recordings); after it all 315 audio files on disk are on Drive
  and none is held.
* **The Claude Drive connector reads a file by reference only from the main session's scratchpad folder.**
  It also refuses a file with more than one hard link, which is why `--link-dir` copies each file. Subagents
  and other folders are refused too, so the uploads run in the main session, about 2 seconds per 7 MB file.
  For unattended uploads, rclone with a one-time Google login is the alternative (not set up; decision 6.5).
* **Agent workflows** of the old session are finished or harvested: the deep research on the analyses is the
  section "Timelines, predictions and question banks" of `ANALYSIS_PLAN.md` (its critique is
  `notes/2026-11-14/research_critique.md`; the raw findings stay private); the Kimi readers' plan is
  `notes/2026-11-14/kimi_integration_plan.md`; the review of the dashboard and the store was fixed in full.
* **Dashboard v2** (sources with links and methods; Bashar tables; the Drive copy) is published at the address
  in section 2.

## 6. Decisions waiting for the owner

1. **A faster speech-to-text engine.** Parakeet TDT 0.6b v3 (`onnx-asr`, int8, CPU) was measured on the old
   machine on 2026-11-13 (`pipeline/README.md`, "Speech-to-text on this machine"): 3.2 times real time on
   podcast speech and a word error rate of 0.831 on an old tape, against `base.en`'s 9.2 times and 0.729. On two
   threads it was slower, not faster. (A later attempt to install it again was refused by the session's
   permission check.) Choose: measure it again on the 4-core machine, or transcribe on a GPU
   (`ET_ASR_MODEL=large-v3 ET_ASR_DEVICE=cuda ET_ASR_COMPUTE=float16`), or keep `base.en`.
2. **The Kimi snapshot's YouTube material.** Its audio of 42 videos was fetched through a converter site and
   its subtitles through paste-link services: ways around YouTube's refusal that this project does not use.
   The readers found that the zip holds no audio or transcript text, only tables, code and the paper.
   Proposed: do not take the converter audio or subtitles even if offered later; fetch the same videos
   through the laptop lane if you allow it (6.6 b); cite their figures only labelled by route, apart from ours
   (`notes/2026-11-14/kimi_integration_plan.md`).
3. **The token in `kimiiii.txt`.** It gave this session full access. Revoke it, delete the file, and give the
   new Codespace a fine-grained token limited to the two repositories.
4. **ArchiveShelf** is still public, and it carries third-party audio and transcripts. Make it private again.
5. **Unattended Drive sync with rclone** (one Google login), instead of uploads from a Claude session.
6. **YouTube's robots.txt** (read 2026-11-14). It disallows, for every crawler, `/youtubei/` (which channel
   listings and the player go through), `/feeds/videos.xml` (channel RSS), `/api/` and `/timedtext_video`,
   among other paths. The project obeys robots.txt, so `discover.py`, `fetch_captions.py` and
   `download_audio.py` now send nothing, and exit 9, unless `ET_YOUTUBE_ROBOTS_OVERRIDE=1` is set. Choose:
   (a) leave the YouTube lanes off (the default);
   (b) opt in yourself, on your own connection, by setting the variable: it says you accept sending requests
   that robots.txt disallows (it does not get past bot checks, and nothing here tries to);
   (c) use the YouTube Data API v3 with your own key for listings (not built; captions of other people's
   videos are not available through it).
   **Decided by the owner on 2026-11-15: (b).** The override is set for YouTube steps. From this Codespace only
   listings work; audio and captions get the bot check, and nothing is done to get past it (section 5).
   Also decide what to keep of what came through those paths before the rule: 63 channel listings (58,699
   videos, live streams and shorts) and 15 RSS entries, and the counts made from them. Until you decide they
   are kept, labelled by route, and not refreshed.
7. **The owner's email address is in the public commits.** The author address of this repository's commits is
   a personal Gmail address. To stop that for new commits: turn on "Keep my email addresses private" and
   "Block command line pushes that expose my email" in GitHub's email settings, and set
   `git config --global user.email <id>+occult-kranti@users.noreply.github.com` (GitHub shows the exact
   address). Old commits keep it unless history is rewritten, which would break every clone and fork.

## 7. Known problems

* **Disk.** `--hold-untranscribed-for darryl-anka` keeps every untranscribed Bashar session on disk. At the
  speed of this machine's speech-to-text, that fills the disk before the download ends. Planned fix: keep only
  a window of the sessions the transcriber reaches next, and pull the rest back when it gets to them. Until
  then, watch `df -h` while Bashar's sessions are held for speech-to-text; their download is finished (all 903,
  section 5).
* **A pull can race the sync.** The sync deletes local audio once its stored copy is checked. Audio pulled for
  transcription is safe only once `transcribe.py` has it queued (each run names its files in
  `<root>/sync/holds/`) or when its person is in `ET_HOLD_UNTRANSCRIBED_FOR`. Pull with the sync loop stopped,
  or add the person to the hold first.
* **Sync log.** A failed text-mirror run is logged as `MIRROR RUN FAILED (exit N)`; the reason is on the
  `STOPPED` line above it. The loop goes on and the next run starts afresh.
* **suzanneliephd.blogspot.com** answered HTTP 429 (never 403) nine times, twice on 2026-11-13 at 21:34 UTC and
  seven times on 2026-11-14 at 02:38 UTC, and the texts step stopped for that host: 1 of the 8 posts asked for
  came through, out of 1,656 registered. The texts step leaves it alone until 2026-11-15 02:38:35 UTC; after
  that the next cycle asks for the other 1,655 at one request a second. Consider a slower `--min-interval`
  for that host, or fetching its posts in small daily batches.
* **Tiny last parts on Drive.** The cutter fills each part up to 7.3 MB, so a recording can end in a very
  small last part (the smallest so far is 4,305 bytes, about a second). It plays; planned fix: split into
  parts of equal size.
* **Redirects outside the audio lane: fixed.** `Hops` is now in `feeds.py`, and the feeds, texts (robots.txt
  included) and site-pages lanes use it as the audio lane does: no redirect is followed to a host that is being
  left alone on this run, or (feeds, texts) resting from an earlier one (the item is not asked for and not
  recorded, so a later run picks it up); every host a redirect leads to waits for its own turn and its own Retry-After; an answer is
  charged to the host that gave it (`final_host`, and `via_hosts` for the hosts in between); and a success counts
  for every host along the way (`common.resting_hosts_along`, shared by the audio, feeds and texts lanes). Older
  records without `final_host` are read by their first host, as before. Only 2 of 23 feeds redirect (rss.pdrl.fm
  to rss.libsyn.com, which is also another feed's first host), and no refusal through a redirect is on record.
* **Load-sensitive tests.** `test_workers_are_not_stuck_behind_a_busy_channel` and the runner test failed once
  under load 13 and passed alone.
* **YouTube from a cloud server.** Apart from robots.txt (section 6.6), audio and captions are refused from a
  cloud server (bot checks, HTTP 403; checked again on 2026-11-15 with the override set). They need the owner's
  own connection (the laptop lane in `pipeline/README.md`).
* **Reader comments in stored blog texts.** 893 of Suzanne Lie's 986 stored posts end with their Blogger comment
  thread (about a quarter of the stored text), so her counts of words from the source include readers' words.
  The prediction pass cuts them (section 5); the texts lane should cut them when it stores a post, and the tables
  be rebuilt.
* **tv.bashar.org** is paid and behind a login: not collected.
* **No video is held.** Every lane keeps audio only. The 153 archive.org video files of Bashar sessions are
  listed, not fetched.

## 8. Order of work for the next session

1. Set up and check (section 3), with the newer Drive ledger.
2. YouTube (section 6.6) was decided on 2026-11-15: (b). Decide the commit email (6.7).
3. Start the sync, the collection cycles, speech-to-text, the Drive hold and the podcast backlog (section 4:
   `resume_jobs.sh` starts whatever is not running), sized to the machine. Copy the backlog to Drive in rounds.
4. Bashar's sessions on Drive: done on 2026-11-15. Next, the owner's task (section 5): `--newest N` and the
   three queues are done; the owner runs the newest 10, 20 and 50 on their computer, each tier is then stored
   and put on Drive; then a timeline of predictions per channel. The rules pass is built and has run over
   everything with text here; next is its model pass.
5. Choose the speech-to-text engine (6.1). Start `keep_transcribing.sh` sized to the machine. Fix the disk
   hold (section 7).
6. Fold in the Kimi snapshot (ROADMAP phase 4b).
7. After collection: the analyses of phases 7, 7a and 7c (`ANALYSIS_PLAN.md`).

The rules do not change:
* audio and transcript text stay private, and quotes are at most 30 words;
* robots.txt is obeyed;
* no way around a block is used;
* nothing private goes into this repository or into an outbound request;
* every change comes on a branch, with the three test suites and both guards passing before the merge.

## 9. Prompt for the next session

Paste this into Claude Code in the new Codespace, at `/workspaces/bashar-index`:

> You are taking over the ET-channelers collection from an earlier Claude session, in a new 16 GB Codespace.
> Act as team lead and owner of the repository and the Codespace; parallelise with agents where it helps.
> Read `et-channelers/HANDOFF.md` first, then section 00 of `et-channelers/ROADMAP.md` and
> `et-channelers/pipeline/README.md`.
>
> 1. Set up as in HANDOFF section 3. Ask me for the GitHub token and keep it in
>    `~/.config/et-channelers/github_token`; never print it or put it on a command line. Restore the state and
>    the memory files from the release `handoff-2026-11-14`, copy its newer `drive_manifest.jsonl` over the
>    restored one, pull the transcripts, the texts and Bashar's audio, and show me `sync_archive.py status`:
>    every kind should show `on_disk_not_stored` 0. Rebuild the tables and check that `drive_stage.py status`
>    shows 3,420 files on Drive.
> 2. Run the three test suites in `et-channelers/pipeline/tests/` and both guards in `et-channelers/scripts/`.
> 3. Size the jobs to the machine (`nproc`, `free -g`, `df -h`), then start the sync loop (with
>    `ET_HOLD_UNTRANSCRIBED=1`), the collection cycles (podcast feeds and episodes, creators' files, texts, tables)
>    and speech-to-text (HANDOFF section 4). Copy what arrives to my Drive in rounds while it is held on disk.
> 4. All 903 Bashar sessions are already on my Drive. The next task is mine (HANDOFF section 5): the newest 10,
>    then 20, then 50 videos of every tracked channel, then a timeline of the predictions made on each channel.
>    `--newest N` and the three queues are done (HANDOFF section 5); the downloads run on my own computer. Pull
>    each tier I have stored, put it on my Drive with `drive_stage.py` (`plan`, `batches --link-dir <your
>    scratchpad>/drive_up`, `round --size 200`, the uploads, `done --round <the id round printed>`), and upload
>    the ledger to the handoff release after each round. Then transcribe each tier and build the timelines
>    (ANALYSIS_PLAN 5.6 and 12.4); they stay private.
> 5. I chose HANDOFF 6.6 (b) on 2026-11-15: run YouTube steps with `ET_YOUTUBE_ROBOTS_OVERRIDE=1`. From the
>    Codespace only channel listings work; audio and captions get YouTube's bot check, and you never try to get
>    past it. Bring me decisions 6.1 to 6.5 and 6.7 when you reach them, with your recommendation.
> 6. Keep `ROADMAP.md`, `HANDOFF.md` and the dashboard up to date; work on a branch, run the three test suites and
>    both guards before each merge, and push and merge as you go.
>
> Rules: audio, captions and transcript text never go into the public repository; quotes are at most 30 words;
> obey robots.txt; use no way around a block (no cookies, proxies, other clients or mirror sites); put nothing
> private in an outbound request; keep texts from the source apart from speech-to-text in every table; report
> counts as they are, failures included.
