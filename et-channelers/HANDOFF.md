# Handoff, 2026-11-14: from the 2-core Codespace to the 16 GB one

Written for whoever picks this up next: the owner, or the Claude session in the new Codespace. The work so
far ran on a 2-core, 8 GB Codespace. Everything was paused on 2026-11-14 around 03:30 UTC so it can carry
on in a Codespace with 16 GB of memory (GitHub's 4-core machine: check with `nproc`). Nothing is lost by the
move: every file collected is in the private GitHub store, and the pipeline's state is in a handoff release.

## 1. State in one paragraph

* **Collected:** 1,138 audio files (819.5 hours, 10.11 GB, mono 24 kbps Opus), 8,425 texts published by the
  sources themselves, and 61 speech-to-text transcripts (30.6 hours). Every one of them is in the private store.
* **Bashar's archive.org sessions:** 262 of 903 downloaded, 636.7 hours left.
* **Podcast episodes:** 828 of 4,057 downloaded, 1,442.6 hours left.
* **Interviews on other shows:** 28 of 29 downloaded.
* **Speech-to-text is the bottleneck.** This machine made about 1.3 hours of text per hour, so the backlog
  needs a faster engine or a GPU (section 6).
* **Google Drive:** tables, transcripts and the earlier work are up. The browsable audio copy is in progress
  (section 5).

## 2. Where everything is

| What | Where |
|---|---|
| Code, tables, docs (public; never audio or transcript text) | `occult-kranti/bashar-index`, folder `et-channelers/` |
| Audio, transcripts, texts (private) | `occult-kranti/et-channelers-archive`, release `archive-v1`: checked tar bundles, read back with `sync_archive.py pull` |
| The same texts as plain files (private) | the same repository, folder `texts/` (person, then `from-source/` or `made-here/`) |
| ArchiveShelf's 16 podcast episodes (private) | the same repository, release `archiveshelf-podcast-audio-v1` (byte-identical to ArchiveShelf's, by GitHub's digests) |
| Pipeline state without media; the Kimi snapshot; reader notes; Claude's memory files | the same repository, release `handoff-2026-11-14`, with `SHA256SUMS` |
| Browsable copy by person | the owner's Google Drive, folder "ET Channelers Archive" (its read-me explains the layout). The folder ids and every uploaded file's id are in the private ledger `sync/drive_manifest.jsonl`, which is in the state bundle |
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
```

Pull other people's audio when it is about to be transcribed, not all at once. The disk is 32 GB, and the
sync deletes local audio once its stored copy is checked (`--only <person-id>` picks one person).

## 4. What was paused, and how to start it again

| Job | Paused where | Start again with |
|---|---|---|
| Sync to the private store, every 5 minutes, and the text mirror every 30 | after a final pass: nothing on disk unstored | `ET_GH_TOKEN_FILE=~/.config/et-channelers/github_token ET_HOLD_UNTRANSCRIBED_FOR=darryl-anka bash et-channelers/pipeline/save_to_github.sh` |
| Bashar's archive.org sessions | 262 of 903 | `setsid nohup ~/et-venv/bin/python -I et-channelers/pipeline/download_enclosures.py --queue ~/et-channelers-private/jobs/queue_archive_org_all.csv --all --workers 2 --per-host 2 --min-interval 1.5 --min-free-gb 3 >> ~/et-channelers-private/logs/archive_org_download.log 2>&1 < /dev/null &` |
| Collection cycles: feeds, new episodes, texts, tables. They wait while another download runs | between cycles | `setsid nohup bash et-channelers/pipeline/keep_collecting.sh >> ~/et-channelers-private/logs/collect.log 2>&1 < /dev/null &` |
| Speech-to-text, Bashar's sessions first | 61 done | `ET_ASR_WORKERS=2 ET_ASR_THREADS=2 setsid nohup bash et-channelers/pipeline/keep_transcribing.sh >> ~/et-channelers-private/logs/asr.log 2>&1 < /dev/null &` |

Every job skips what is finished. Kill a job by its process id, never with `pkill -f`, which also matches the
shell that runs it.

## 5. Work in progress

* **Google Drive copy** (`pipeline/drive_stage.py`). Audio goes in by person and source:
  * "Podcast - <show>", "archive.org sessions", "Audio from own website", "Interviews on other shows";
  * file names are "<date> <title> [<item id>].opus";
  * files over 7.3 MB are cut between Ogg pages into parts that each play on their own, with no re-encoding.

  Texts go in as volumes per person; texts from the source and speech-to-text made here are never in one file.
  The 77 folders exist. The plan has 1,948 files (9.93 GB); see the ledger for how many are up. To go on:
  `drive_stage.py plan`, then `batches --link-dir <the Claude session's scratchpad>/drive_up`, then the
  uploads, then `record`.

  **The Claude Drive connector reads a file by reference only from the main session's scratchpad folder.**
  It also refuses a file with more than one hard link, which is why `--link-dir` copies each file. Subagents
  and other folders are refused too, so the uploads run in the main session, about 30 per message (roughly
  2 seconds per 7 MB file). For unattended uploads, rclone with a one-time Google login is the alternative
  (not set up).
* **Agent workflows** that were running in the old session (they cannot move): deep research on the analyses
  (by year, last N, predictions and warnings, question banks, UI), readers of the Kimi snapshot, the analysis
  plan, the source scouts, and a review of the dashboard and the store. What they finished is in
  `ANALYSIS_PLAN.md`, `ROADMAP.md` (phases 4b and 7c) and `notes/2026-11-14/`. Run again what is not there.
* **Dashboard v2** (sources with links and methods; Bashar tables): the page is written but not yet published.
  Publish it after the review findings are fixed.

## 6. Decisions waiting for the owner

1. **A faster speech-to-text engine.** Installing `onnx-asr` with NVIDIA's Parakeet TDT 0.6B (int8, CPU) was
   refused by the session's permission check, so it was never measured. It is expected to be several times
   faster than Whisper base.en and more accurate. Allow it, or transcribe on a GPU
   (`ET_ASR_MODEL=large-v3 ET_ASR_DEVICE=cuda ET_ASR_COMPUTE=float16`).
2. **The Kimi snapshot's YouTube material.** Its audio was fetched through converter sites and its subtitles
   through paste-link services: ways around YouTube's refusal that this project does not use. Proposed: use
   what it already holds privately, marked with how it was obtained, and never repeat the method.
3. **The token in `kimiiii.txt`.** It gave this session full access. Revoke it, delete the file, and give the
   new Codespace a fine-grained token limited to the two repositories.
4. **ArchiveShelf** is still public, and it carries third-party audio and transcripts. Make it private again.
5. **Unattended Drive sync with rclone** (one Google login), instead of uploads from a Claude session.

## 7. Known problems

* **Disk.** `--hold-untranscribed-for darryl-anka` keeps every untranscribed Bashar session on disk. At the
  speed of this machine's speech-to-text, that fills the disk before the download ends. Planned fix: keep only
  a window of the sessions the transcriber reaches next, and pull the rest back when it gets to them.
* **Load-sensitive tests.** `test_workers_are_not_stuck_behind_a_busy_channel` and the runner test failed once
  under load 13 and passed alone.
* **YouTube from a cloud server.** Audio and captions are refused (bot checks, HTTP 403). They need the
  owner's own connection (the laptop lane in `pipeline/README.md`). Channel listings work from the cloud.
* **tv.bashar.org** is paid and behind a login: not collected.
* **No video is held.** Every lane keeps audio only.

## 8. Order of work for the next session

1. Set up and check (section 3). Then start the sync, the collection cycles and the archive.org download.
2. Choose the speech-to-text engine (section 6.1). Start `keep_transcribing.sh` sized to the machine.
3. Fix the disk hold (section 7). Finish the Drive copy and its read-me.
4. Fold in the Kimi snapshot (ROADMAP phase 4b). Fix the review findings. Publish dashboard v2.
5. After collection: the analyses of phases 7, 7a and 7c (`ANALYSIS_PLAN.md`).

The rules do not change:
* audio and transcript text stay private, and quotes are at most 30 words;
* robots.txt is obeyed;
* no way around a block is used;
* nothing private goes into this repository or into an outbound request;
* every change comes on a branch, with both test suites and both guards passing before the merge.
