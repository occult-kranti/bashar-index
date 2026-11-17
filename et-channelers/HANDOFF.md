# Handoff, 2026-11-14: from the 2-core Codespace to the 16 GB one

## Current checkpoint: CUDA results and Chrome capture, November 17 04:00 UTC

This section supersedes the older runtime and provisioning observations below. **47 native audio/metadata pairs remain verified on Drive.** There are 20 verified English caption bundles across 17 recordings, with 15 complete inventories. The new CUDA lane has **25 English ASR bundles verified on Drive**, representing 9.65 audio hours and 5,343 segments. These are derived texts for already archived audio; they are not 25 additional audio acquisitions. Their accuracy remains unreviewed. Two caption inventories have unresolved alternatives despite verified English tracks spanning most of their timelines; timing extent is not measured speech coverage.

The separate hash-locked Python 3.12 environment is working on the RTX 4070 Laptop GPU with CUDA int8/float16 inference. The English model is pinned to `c3058b475261292e64a0412df1d2681c06260fab`; the multilingual large-v3 model is downloaded and pinned to `edaa852ec7e145841d8ffdb056a99866b5f0a478`. Only one model may own the GPU at a time. The completed English batches peaked at 1.639 GB VRAM, 67% over a 30-second utilization window and 75°C; brief utilization samples reached 100%, so the 70% target is explicitly soft. A five-input multilingual/unknown-language frame covers 49.4 minutes. Its adapter requires original text plus a separately typed English view, with silence, light-language and ambiguous language held rather than invented translation. See [GPU setup and contracts](pipeline/GPU_ASR_SETUP.md). The immutable runtime-source/dependency/provenance archive is separately verified on Drive.

**74 priority channels are indexed:** 1,420 newest-20 videos, 3,449 inclusive newest-50 videos, 67,594 total unique IDs and 64,145 final-round IDs. Charlie Wilde, Infini Global and Odyssey of Ascension are registered. The explicitly requested older Bashar video is pinned separately and does not replace any newest-20 item. Infini Global remains a publisher with unverified ownership; the named speaker and source must be reviewed per upload. The [intake audit](research/intake-three-channels-2026-11-16.md) documents these distinctions. Four official-biography relationships extend the directory to **119 relationships / 31 people / 90 source labels**, preserving Roxanne's existing Atlas identities. The Bashar video remains pending performer evidence.

**Native acquisition remains parked.** The last direct-media 403 was recorded at 01:40:49 UTC, preserving its native retry deadline of **November 18 01:40:49 UTC**. English caption transport has the independent **November 17 23:20:02 UTC** deadline. The bounded anonymous Chromium observer found HTTP 200 responses carrying an in-body stream-protection rejection after a 60-second prefix. No complete browser/SABR recovery has been archived. The owner confirmed the same Dreemtime video plays beyond 90 seconds in normal Chrome; further unchanged anonymous probes are unnecessary.

The [user-activated Chrome extension](browser_capture_extension/README.md) and [loopback spool/uploader](pipeline/chromium_capture_service.py) are implemented. Thirty offline service tests and eight extension fixture tests pass. The service is listening on `127.0.0.1:8768`, waiting for the owner's required Chrome extension activation. Each of up to four explicitly activated tabs can process its same-origin queue in sequence. It records re-encoded Opus audio, guards video identity/ad state/content clock, validates full decoded duration/non-silence, uploads audio and metadata together, records exact Drive identities/size/MD5 plus local SHA-256, then deletes only matching owned files. Browser recordings use a separate ledger and folder; do not count a prefix or a browser recording as native audio. A successful complete YouTube trial remains outstanding.

The shared resource phase keeps a **16 GB managed ceiling**, **20 GB total limit** and **2 GB buffer**. Reservations are 8 GB for environment/models, 200 MB for leased ASR inputs/jobs, 300 MB for bounded source research and 5 GB for browser capture. The service also protects 3 GB of future growth by other owners and a free-disk floor. Models, tools, checkouts and incomplete captures count. The older 17 GB collector does not share these reservations and must remain parked with the root-owned STOP text quoted below. User activation of Chrome capture does not authorize clearing that marker.

The [74-channel ETA supplement](research/collection-eta-2026-11-17.md) separates conditional native throughput from browser playback. Native newest-20 capacity is 3.81–9.27 active hours **after access recovers**, under explicitly assumed bandwidth and API pacing. Four real-time browser workers would need at least 145.43 playback hours (6.06 days) for known remaining newest-20 durations, even with ideal balancing and no interruptions. Neither is a guaranteed completion date. Embeddings, scientific corpus analysis and the held-out ASR calibration study remain unexecuted.

Integration baseline: merged [PR #30](https://github.com/occult-kranti/bashar-index/pull/30), commit `d66e5e3`; retained branch `feat/browser-recovery-entity-directory`. This continuation is `feat/gpu-caption-fallback`. Root owns integration, resource allocation, capture service and public status; environment owner owns CUDA runtime/multilingual adapter; source owner owns the Chrome extension; queue owner owns source leases, intake and evidence review. All dashboard links are in the [root guide](../README.md#public-interfaces).

## Active goal update: contained GPU transcription, 01:32 UTC November 17

The owner's newly activated goal explicitly requests latest-20 audio for every channel, captions where available, and local GPU speech-to-text otherwise. This supersedes the earlier planning-only transcription instruction. A separate `tools/asr-venv` and one pinned English model are being provisioned; the collector environment is unchanged. The model candidate is `Systran/faster-distil-whisper-large-v3` at revision `c3058b475261292e64a0412df1d2681c06260fab`. No accuracy or GPU compatibility result is claimed before the smoke tests and source pilot.

Private `sync/analysis_resource_plan.json` reserves 8 GB for environment/model/install staging, 200 MB for the first verified audio input, and 300 MB for an isolated maintainer SABR investigation, within a tighter 16 GB managed ceiling and the 20 GB total/2 GB buffer policy. The ordinary waiting supervisor was parked with the owner-specific STOP text `Codex resource phase: isolated ASR provisioning and bounded SABR investigation`. Do not remove that marker until the resource phase is explicitly reconciled. This serial phase prevents the old collector, which does not honor the new ASR reservations, from filling its spool during setup. Source deadlines remain recorded; the older waiting-PID observation below is superseded by the parked state.

The systems owner provisions and measures the isolated environment. The queue owner identifies verified audio without complete English captions and holds immutable source leases; non-English material is not forced through an English-only model. The source owner investigates a maintainer-linked SABR test build after an anonymous Safari probe returned no audio/HLS formats. One GPU lease is assigned explicitly before inference. No embedding or scientific corpus-analysis job is activated by this goal update.

## Latest checkpoint: Chromium investigation and Dreemtime, 01:14 UTC November 17

This section supersedes older runtime observations below. **No new full audio was acquired during the browser investigation:** 47 audio/metadata pairs remain verified on Drive, alongside 20 English-caption bundles across 17 videos. Native full-file attempts returned media 403 for the prior failing Elena item and a previously unattempted Dreemtime item. Anonymous Chrome playback was successful and two small WPC-backed range probes returned 206, but those probes did **not** establish full-file recovery. The newer official nightly is `2026.11.16.232655`; WPC `1.1.2` is installed locally. Persistent cookies, personal browser profiles and proxy rotation were not used.

The new browser probe and in-process browser lease helper are explicit, experimental tools. Keeping a browser open and using yt-dlp's native downloader were tested without a full-file success. Do not claim a reliable Chromium workaround or automatically activate this path. Browser mode permits at most four leases and requires a private cap of at most 16 GB, reserving extra browser/tool overhead; temporary-profile cleanup failures require review. The ordinary native lane retains its 17 GB private cap. New download receipts now record actual stream start and elapsed time for future ETA calibration.

**Dreemtime Academy / Hayden Crawford** is registered as an interview host: canonical `UCE6KE5xH13AMUajXvz_w8vA`, 1,101 indexed items (338 Videos, 117 recorded-stream listings, 646 Shorts). The queues now contain 1,360 newest-20 items, 3,320 newest-50 items, 66,446 unique IDs and 63,126 final-round items across 71 tracked priority channels. All preceding queue rows/order/metadata were retained and backed up under the ingestion lock. Per-episode speaker/entity attribution remains pending.

At 01:14 UTC, **supervisor PID 186764** is waiting on the latest actual source deadline, **2026-11-18 01:13:30 UTC / November 17, 8:13 p.m. Eastern**. It keeps four source workers, four upload transfers, eight-pair batches, 16 ready/in-flight slots, 10-second metadata spacing and the existing 1-of-3 attempt count. No retry budget was reset. Captions retain their independent November 17 23:20:02 UTC deadline. The experimental shared-browser service was stopped; it was not a proven repair. Consult private state before using dated PIDs.

The [conditional ETA report](research/collection-eta-2026-11-16.md) estimates about 3.6–8.9 active hours for newest 20, 9.1–22.2 active hours through newest 50, and 7.7–16.5 active days for all indexed audio, before overhead and future downtime. It models roughly 1.05–1.49 TB and explicitly imputes missing durations. Caption request floors are separate. Repeated refusals mean there is no finite guaranteed completion date; the report's earlier cooldown timestamp is a dated input, superseded by current state above.

The Atlas `#/entities` view adds a separate 115-relationship/28-person/86-label extension with evidence links and filters; its historical scientific datasets remain byte-identical. Root [README](../README.md) now explains the entire repository, and [BRANCHES](../BRANCHES.md) inventories 30 remote branch tips, ancestry and worktrees. [Common-event research](research/cross-channel-events-2026-11-16.md) adds the user's Dreemtime/Sam candidate to the future analysis roadmap; metadata alone does not confirm a shared event. No new ASR, model, embedding or corpus-analysis job was started.

## Current continuation: collection and research, November 16 evening Eastern

PR #27 merged at `3a2e488`; its branch remains. The following checkpoint supersedes older runtime counts and restart directions below. The research continuation is on `feat/channeler-research-plan`.

At **2026-11-17 00:21 UTC**, the current YouTube lane has **47 verified audio/metadata pairs**, 20 verified English caption bundles across 17 videos, and no completed pairs awaiting upload. The new requested channel, **Multidimensional Soul / @Akanksshaa**, is registered as an interview host, with 1,417 indexed items (730 Videos, 684 Shorts, three streams). Do not assign guest speech or guest entities to the host. There are now **70 tracked channels**, 65,345 unique indexed IDs, 1,340 newest-20 items, 3,270 newest-50 items and 62,075 final-round items. Queue backups and intake provenance remain private. The private catalog checkpoint reflects these counts.

The official yt-dlp nightly plus a local **Bgutil 2.0.2** PO-token provider and the explicitly selected `mweb` client recovered one previously blocked full audio file and verified it on Drive. A subsequent four-worker trial received a new media 403. **Supervisor PID 137316 is waiting**, with four download workers, four upload transfers, eight-pair batches, 16 ready/in-flight slots and 10-second metadata spacing. Its existing attempt count is 1 of 3; it was not reset. The source deadline is **2026-11-18 00:11:16 UTC / November 17, 7:11 p.m. Eastern**. Caption-only cooldown remains **2026-11-17 23:20:02 UTC**. These deadlines are preserved; the provider is not a universal fix for refusals. Provider PID 76376 binds only `127.0.0.1:4416`; anonymous token diagnostics are redacted. PIDs are dated observations: inspect saved state before acting.

Automatic approval review rejected a proposed eight-worker restart with a retry-budget reset, returning only “blocked by policy.” The accepted smaller continuation preserves the budget and waits for the existing source deadline. Do not retry the rejected compound action or reinterpret the source refusal as item-only without reviewed evidence.

Measured local footprint at this checkpoint is approximately 0.115 GB private plus 0.691 GB tools/repository. Keep the private ceiling at 17 GB and the owner's 2 GB total buffer. No ASR packages/models, transcription, embeddings or corpus-analysis jobs were started. The owner explicitly requests planning those next, not running them now; this supersedes the historical CPU speech-to-text restart instructions in sections 8–9.

The [consolidated research plan](research/analysis-plan-2026-11-16/README.md) combines two search rounds and a third critique by systems, analysis and identity owners. Its [channeler–entity table](research/analysis-plan-2026-11-16/channeler-entity-table.md) contains 115 sourced relationships for 28 people, plus a separate host row. The lead independently reviewed 30 primary pages; this verifies documented self-attribution, not external beings or treatment effects. Seven channel-ownership gaps remain. Only the explicitly requested new channel was added to collection queues. The disabled implementation plan covers GPU scheduling, captions-first ASR, TF–IDF/BM25, embedding/topic comparisons, shared-entity networks, prediction windows, hypotheses, experiment designs, frequency/healing evidence and figures.

## Local Windows continuation, 2026-11-16

PR #28 is merged on `main` at `22d89f2`; the published dashboards are current. PR #26 and its branch are retained. The new ingestion work is on
`feat/windows-drive-ingest`. The owner's current priority supersedes the older restart instructions below:
collect native YouTube audio plus available metadata, newest 20 per tracked channel first, then newest 50,
then the entire remaining catalogue. The owner explicitly authorized the full archive after the dashboard release; `RunAll` now advances through all three receipt-gated phases. Do not start transcription or the legacy collection loops for this task.

The local rclone remote `etdrive` points at the existing ET Channelers Archive. A dedicated Desktop
OAuth client is now authenticated and its Drive API is enabled. The owner chose to retain Testing
mode; expect Google reauthorization around November 23, 2026 if collection is still running.
The working folder is outside Git. [`pipeline/WINDOWS_DRIVE.md`](pipeline/WINDOWS_DRIVE.md) gives the commands,
recovery rules and Drive client setup. The launcher separates source workers (default four, configurable up to eight) from up to four upload transfers, batches up to 16 pairs, and caps the working folder at 17 GB
(the owner's total local ceiling is 20 GB, with 2 GB reserved and up to 1 GB for tools/repositories), and applies no project storage cap on Drive. Native audio uses
no transcoding or GPU inference. A pilot audio upload was read back by size and MD5 before local deletion;
ordinary 1 MiB HTTP range requests substantially improved a second pilot's download speed.

The restored newest-20 snapshot has 1,320 items across 69 channels. Newest 50 contains 3,220 items, including
the 1,320 in the first phase. There is no duration filter or default per-item size cutoff; storage admission
uses the selected stream's byte length within the total local budget. Insufficient space defers an item,
never silently excludes it. New Drive files use source-tab folders (Videos, Shorts, Recorded streams,
Unclassified); old verified receipts retain their original paths. The older all-items snapshot has 58,766
unique IDs and lacks six channels' full histories; those six have now been listed successfully across
Videos, Shorts and recorded Streams (5,130 listing rows). `prepare_all_queue.py` merges these snapshots,
preserves provenance, and records known source-person mappings without inventing entity labels. The merged
queue contains 63,929 unique items and has full listing snapshots for all 69 tracked channels. The remaining
60,709 items are indexed for the final round after the newest-50 tier. Its output
and per-item metadata remain private. Saved snapshots are not a claim that future uploads are already listed.

The new `drive_ingest_manifest.jsonl` records this lane's Drive objects and checksums. It is independent of
the older `sync_manifest.jsonl` and `drive_manifest.jsonl`; use the new runner's status and Drive restore
instructions for these files. Never overwrite the shared historical Drive ledger with this lane's receipts.

The initial four-worker run stopped on a confirmed Drive HTTP 403 `rateLimitExceeded` response. Two pilot
pairs were verified and cleaned up; four complete local audio/metadata pairs were retained. The Drive
cooldown prevents new upload/preflight requests until its wait expires; this is separate from YouTube's
refusal rest period. Resume the new phase launcher after Drive access recovers, draining retained pairs first. A later bounded prefetch added eight new pairs: 12 await upload, two are verified on Drive, and local usage was about 0.45 GB. These are dated observations, not a live job claim. After the dedicated Desktop OAuth client was authorized and its Drive API enabled, a 12-pair upload pilot passed every size/hash/Drive-ID check and removed both artifacts locally: 14 pairs are now verified, with about 54 MB remaining in the private root. This observation supersedes the earlier quota-blocked status. The new bounded supervisor preserves cooldown deadlines and a persisted retry budget. The private catalog uses a compressed full baseline plus changed-item deltas and hash-verified manifests; see `pipeline/ARCHIVE_CATALOG.md`.

At 22:44 UTC the reviewed supervisor was restarted in `RunAll` with six download workers, two upload transfers, eight pairs per batch and at most 32 ready/in-flight pairs. The private catalog checkpoint was uploaded and verified (63,929 indexed items, 14 verified pairs at that checkpoint); a subsequent live collection pair brought media receipts to 15. Upcoming premieres are deferred without halting other channels and receive one late revisit after useful stage work. This is a dated observation; consult the private supervisor state and receipts for current progress. The owner kept the OAuth app in Testing mode.

At 23:16 UTC the owner-selected configuration was running with eight download workers, four Drive upload transfers, 12-pair batches and a 64-item ready/in-flight bound. The private root is capped at 17 GB: measured tools/repositories used 0.66 GB, preserving about 2.34 GB below the 20 GB total allowance. The user narrowed text collection to English published captions and original English automatic captions; translations and other languages are excluded. Existing audio is backfilled with metadata-only requests. Caption ZIPs and receipts are independent of audio pairs.

The previous YouTube media 403 was repaired using the official yt-dlp nightly 2026.11.15.232800 (upstream fix #18051). At the owner's explicit request to override/fix and continue, one bounded normal-client recheck returned the exact HTTP 206 range; an append-only repair acknowledgement superseded only that item's old cooldown. A full audio/upload/verification run then passed, and English-caption backfill on the same item passed without redownloading audio. At 23:16 UTC there were 35 verified audio/metadata pairs, one verified English caption ZIP and 34 earlier audio items awaiting captions. Future source refusals still establish their own persisted rest windows. Caption refusals now pause only caption acquisition; audio refusals and Drive quotas retain their independent controls. See `pipeline/YOUTUBE_CAPTIONS_RESEARCH.md` for the investigated alternatives and limitations.

At 23:30 UTC, receipts confirmed 35 audio/metadata pairs and 20 English caption ZIPs across 17 videos; 15 videos had complete requested caption inventories, and one had no English track. A timedtext HTTP 429 at 23:20 UTC established a caption-only wait until 2026-11-17 23:20 UTC. The updated collector serializes caption requests with at least 15 seconds between starts, preserves pending English tracks and continues audio while that endpoint rests. The bounded supervisor can revisit earlier tiers after the caption deadline, using the existing attempt budget. The caption journal and atomic backfill summary preserve this state independently of audio receipts.

At 23:36 UTC the updated supervisor resumed with 8 download workers and 4 upload transfers. Two fresh audio downloads reached the ready queue while caption requests stayed deferred. Isolated missing-format items now remain pending, receive one late revisit after audio progress, and no longer halt other channels; three such failures without audio progress stop dispatch for tool review. The operator reset the bounded retry budget for this reviewed restart without clearing any caption/source/Drive deadline. Logs and runtime state remain private; public progress is a dated aggregate snapshot.

The 23:39 UTC checkpoint supersedes that running status: 11 additional audio/metadata pairs were uploaded, verified and retired locally, for 46 total. A new media HTTP 403 on a different item established an audio-source rest until 2026-11-17 23:37:28 UTC; the still-running bounded supervisor waits for that deadline. All completed pairs drained to Drive, while incomplete bytes remain for recovery. The caption-only deadline remains 23:20:02 UTC that day. This later refusal was not cleared by the earlier upstream-repair acknowledgement. The published status distinguishes these source waits; it does not claim continuing downloads.

## Dashboard interface update - 16 November 2026

The maintained dashboard directory is [`../dashboards/index.html`](../dashboards/index.html) ([published URL](https://occult-kranti.github.io/bashar-index/dashboards/)). Six repository pages now share navigation. The prediction workbench preserves the exact 480 public records and their 2026-11-16T19:36:03Z build date; it adds no new evidence or verdicts. Its public-only refresh mode re-renders already-published records, while a fresh evidence build still requires the original private catalogue and quote-share guard.

The channel index now runs standalone and has a reproducible template/generator. Its historical sample (92 channel entries, 466 video rows, 457 nonempty video IDs, nine rows without an ID) is distinct from the current collection queue. The collection page reads a sanitized counts-only `plan/ingestion_status.json` beside the dated archive tables. It shows newest 20, extension to 50, then the remaining archive when the full-archive supervisor is configured; indexed coverage is never presented as downloaded media. No private media, titles, paths, contacts or raw errors are exported by that status file. An expired cooldown alone does not establish that a worker is running.

See [`../dashboards/README.md`](../dashboards/README.md) for rebuild and verification commands. This interface change was developed in an isolated worktree; it does not restart collection jobs or merge the separate Windows ingestion branch. Older handoff sections below retain their original observation dates.


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
  12.4, read all 10,150 items with text here and found 6,041 candidate statements about the future for 27 people
  (5,517 once near-copies are collapsed), 499 of them with a target window (section 5; seven filters added on
  2026-11-16 drop page furniture, editorial notes, promotion and past references). Two samples labelled by
  two independent agent coders shaped the rules (42% real predictions among windowed candidates at first); a
  third, fresh sample measured them: **about 56% of windowed candidates are real predictions** (weighted by
  person; 95% interval about 47% to 65%), from 19% (Swaruu) to 88% (Sam) by person. They stay candidates, not
  findings, until the model pass.
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
       each channel's Videos tab (no request), since 2026-11-16 in rank order by default (every channel's newest,
       then every channel's second newest, ...; `--order as-is` keeps channel by channel); `run_all.py --newest N`
       passes it on and lists only that much of each channel, and `run_all.py --queue FILE` runs the lanes over a
       queue file instead (below). Each queue has its own meta file.
    4. Fresh listings: **made on 2026-11-15** from this Codespace, Videos tab only, 50 per channel, one request
       every 5 seconds: 63 channels, 2,920 videos, no failures, 15 of them new since 2026-11-13. **Relisted on 2026-11-16** for 69 channels (3,220 videos, no failures) after the owner named nine channels (section 5). They are in
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
       - a blog's reader comments: the text is cut at Blogger's "N comments:" line (and since 2026-11-16 the
         stored texts themselves no longer carry them, section 7);
       - **since 2026-11-16 (PR #18), seven filters designed on the three labelled samples and reviewed**: page
         furniture (translation listings, related-post blocks, bylines after a title), editorial notes (footnotes,
         citations), promotion (event logistics, product notices), lists of any time ("in a month, or two, or
         three"), dated headers (a session date followed by a speaker label), past anchors ("since 2019", "back
         in 2017", "ago") and a past verb governing the dated clause. None drops a sentence whose year is later
         than the date said, and none lost a labelled real prediction (156 of 156); together they drop 58 of the
         112 labelled false positives. **The fourth fresh sample measured them on 2026-11-16** (`fourth_2026-11-16`, 90
         windowed candidates from 10 people, none seen before, two independent blinded coders, kappa 0.93 on
         prediction-like): 45 of 90 real predictions, **54.7% weighted by person (95% about 45% to 65%)**, against
         55.9% before the filters, so the filters cut false positives without moving the measured precision; by
         person 38% (Gosia) to 69% (Scranton) among those with 16 units; speech-to-text 2 of 10. Row 4 of
         `plan/prediction_samples.csv`.
       Near-copies are collapsed (12.4: shared five-word runs, Broder 1997, at a resemblance of 0.5): the first
       said keeps the statement, later copies are counted, and the timeline shows each once with how often it was
       said. Families of one event in different words are the model pass's work.
       Run over everything with text here (not yet the YouTube tiers; last on 2026-11-16, 03:50 UTC, after the
       stored blog texts were rewritten without reader comments and with the seven new filters): 10,150 items, 27
       people, **6,041 candidates, 5,517 distinct (5,344 from source texts, 173 from speech-to-text), 499 with a
       target window (480 distinct)**; the texts lane had added items since the last run, so the candidates rose
       while the filters cut the windowed share,
       from 1977 (L/L Research) to 2075 (Aaron Abke), apart from an undated range from 1926 ("1926 to 2012", Sam)
       that the model pass must weed out; 1,480 are undated (Swaruu 659, Sam 615, Blossom Goodchild
       152, L/L Research 52, Jamie Butler 2). Per person and kind in `plan/prediction_counts.csv` (counts only);
       the candidates and timelines are in the private folder's `analysis/predictions/` (`<person>.jsonl`,
       `<person>.md`, quotes cut to 30 words).
    8. Three samples for the model pass: **run on 2026-11-15** (`pipeline/prediction_pilot.py`). Each is a seeded
       sample of windowed candidates shown without person, title or date (12.5), labelled by two agent coders
       working apart with the 12.4 types (prediction, conditional prediction, warning, prophecy, timeline as
       schedule, self-validation, refusal to date, future-tense teaching, not future, promotion). Both coders are
       runs of one model, so agreement is between two runs, not between people.

       | Sample | Units | Type kappa | Prediction-like kappa | Prediction-like (both coders) | Shaped which rules |
       |---|---|---|---|---|---|
       | pilot, 8 per person, 19 people | 106 | 0.90 | 0.98 | 44 (42%) | questions, reports, page furniture |
       | validation, 16 per person, the 7 largest (pilot excluded) | 112 | 0.88 | 0.91 | 61 (54%) | blog comments, post headers |
       | third, 16 per person, fresh (both earlier samples excluded), under the current rules | 99 | 0.95 | 0.96 | 54 (55%) | none: it only measures |

       Under the rules as they now stand, 82 pilot units and 97 validation units are still candidates, and no
       prediction of the source was lost (the one prediction-like unit cut was a reader's comment): 44 of 82 (54%)
       and 60 of 97 (62%) are prediction-like. Weighted by each person's windowed candidates, the validation
       sample gave 36% before the comment cut, since 528 of the 1,017 windowed candidates were Suzanne Lie's and 14
       of her 16 were comments or headers; after it, about 68%, but her share rested on one unit. Both samples
       shaped the rules they measure, so the third, fresh sample gives **the figure to quote: 55.9% of windowed
       candidates are prediction-like by both coders, weighted by each person's windowed candidates (stratified
       95% interval about 47% to 65%; unweighted 54 of 99, Wilson 45% to 64%)**. It covers the 9 people with units
       left, 532 of the 572 windowed candidates; the other 40, of 11 small channels, were all in the first two
       samples. By person: Sam 14 of 16, Daniel Scranton 10 of 16, Suzanne Lie 9 of 16 (now that comments are
       cut), L/L Research 8 of 16, Laarkmaa 7 of 12, Darryl Anka 3 of 4, Swaruu 3 of 16 (the other 13 are about the
       past or present: past events, transcript date headers, hypotheticals, translation listings). What the
       rules still let through: past or present statements (23 of 99), future-tense teaching (12 to 13) and
       promotion (6); filters for these must be shaped on a new sample, not this one. The
       samples, keys and labels are in `analysis/predictions/pilot_2026-11-15/`, `validation_2026-11-15/` and
       `third_2026-11-15/` (private). Next: the
       bulk model pass (is it the entity's claim; prediction or future-tense teaching; certainty; families
       linked), which waits for an API key and the owner's go-ahead on cost and data terms (12.5, D14); then the
       same over each YouTube tier as it is transcribed.
  - **The queues** (built on 2026-11-15 and rebuilt on 2026-11-16 from those listings, in rank order, in the private folder's `jobs/` and on the private
    store's release `handoff-2026-11-14`), each with its `.meta.json`; the columns add `tab`, `listing_rank` (0 is
    the newest) and `upload_date_approx`:

    | Queue file | Videos | Known hours | What it holds |
    |---|---|---|---|
    | `queue_blackouts_titles_all.csv` | 43 | 17.6 | titles that name blackouts, the power grid or the internet going down |
    | `queue_blackouts_titles_weak_all.csv` | 225 | | titles that name solar flares, storms or CMEs (a weaker sign) |
    | `queue_newest10.csv` | 672 | 262.6 | the newest 10 of every channel's Videos tab (69 channels since 2026-11-16) |
    | `queue_newest20.csv` | 1,320 | 555.5 | the newest 20 (includes the 10) |
    | `queue_newest50.csv` | 3,220 | 1,351.7 | the newest 50 (includes the 20) |
    | `queue_youtube_all.csv` | 58,766 | | every video the channel listings hold; captions only is the realistic use |

    The three newest tiers were written channel by channel (their meta says `"order": "as-is"`); `--newest N`
    lists again and builds its queue in rank order, `--queue` keeps the file's order.
  - **On the owner's computer.** What `run_all.py` does now (2026-11-16): with `--newest N` the queue is in rank
    order by default (every channel's newest video, then every channel's second newest, and so on, so a run stopped
    halfway has the newest of every channel); `--queue PATH` (repeatable) runs the YouTube lanes over queue files
    instead of listing and building a queue, merged in order into `<root>/jobs/queue_run.csv` with a repeated video
    kept once (not with `--newest`, `--per-channel` or `--set`; a missing file or one without a `video_id` column stops the
    run with exit code 2 before anything starts); with `--transcribe MODEL` speech-to-text runs beside the
    downloads, one pass every 300 s (`--transcribe-every`), and once more at the end; before anything starts the
    tools are run for their versions (`TOOLS`; `--ytdlp`, `--ffmpeg`, `--ffprobe` name other paths), a yt-dlp or
    ffmpeg that is missing or cannot be run stops the run with exit code 6, and a yt-dlp released more than 60 days
    ago gets a warning (YouTube changes often; an old yt-dlp fails in ways that look like blocks: update it first);
    the plan and the run print an `ESTIMATE` (videos, known hours, what each lane still has to do and the least
    time it takes at its pace); and each download records the video's exact upload date as `published`. The pace
    is unchanged: audio 2 workers and one start every 10 s, captions 1 worker and never faster than every 5 s nor
    than the audio lane; no cookies, logins or proxies.

    The runs, in this order (each run skips what is already stored, so a stopped run is started again with the
    same command). PowerShell first, then the same in a Unix shell:

    ```powershell
    $env:ET_YOUTUBE_ROBOTS_OVERRIDE = "1"
    $S = "gh:occult-kranti/et-channelers-archive@archive-v1"
    $Q = "$HOME\et-queues"
    # 1. the queues from the release of the private store
    gh release download handoff-2026-11-14 -R occult-kranti/et-channelers-archive -p "queue_*.csv" -D $Q --clobber
    # 2. the blackout-titled videos first: audio and captions (43 videos, about 18 h; the plan, then --go)
    python et-channelers\pipeline\run_all.py --store $S --lanes "youtube,captions" --queue $Q\queue_blackouts_titles_all.csv
    python et-channelers\pipeline\run_all.py --store $S --lanes "youtube,captions" --queue $Q\queue_blackouts_titles_all.csv --go
    # 3. the newest 10 of every channel: --newest 10 lists again and takes them in rank order ...
    python et-channelers\pipeline\run_all.py --store $S --lanes "youtube,captions" --newest 10 --go
    #    ... or the queue as built on 2026-11-15, in the file's order, without listing
    python et-channelers\pipeline\run_all.py --store $S --lanes "youtube,captions" --queue $Q\queue_newest10.csv --go
    # 4. then the newest 20, then 50 (the same two ways)
    python et-channelers\pipeline\run_all.py --store $S --lanes "youtube,captions" --newest 20 --go
    python et-channelers\pipeline\run_all.py --store $S --lanes "youtube,captions" --newest 50 --go
    # 5. captions only, for everything listed: runs in the background over days, resumable
    python et-channelers\pipeline\run_all.py --store $S --lanes captions --queue $Q\queue_youtube_all.csv --go
    ```

    ```bash
    export ET_YOUTUBE_ROBOTS_OVERRIDE=1
    S=gh:occult-kranti/et-channelers-archive@archive-v1
    Q=~/et-queues
    gh release download handoff-2026-11-14 -R occult-kranti/et-channelers-archive -p "queue_*.csv" -D $Q --clobber    # 1
    python3 et-channelers/pipeline/run_all.py --store $S --lanes "youtube,captions" --queue $Q/queue_blackouts_titles_all.csv        # 2, the plan
    python3 et-channelers/pipeline/run_all.py --store $S --lanes "youtube,captions" --queue $Q/queue_blackouts_titles_all.csv --go   # 2, run it
    python3 et-channelers/pipeline/run_all.py --store $S --lanes "youtube,captions" --newest 10 --go                                 # 3 (or --queue $Q/queue_newest10.csv)
    python3 et-channelers/pipeline/run_all.py --store $S --lanes "youtube,captions" --newest 20 --go                                 # 4
    python3 et-channelers/pipeline/run_all.py --store $S --lanes "youtube,captions" --newest 50 --go
    python3 et-channelers/pipeline/run_all.py --store $S --lanes captions --queue $Q/queue_youtube_all.csv --go                    # 5
    ```

    Add `--transcribe large-v3 --devices 0` (a GPU) or `--transcribe base.en` (CPU) to a run to transcribe beside
    the downloads. Step 5 is 58,766 caption requests at one every 10 s: about 7 days of pacing alone, so it runs in
    the background over days; stop it whenever the computer is needed and start it again with the same command,
    and everything already fetched is skipped. The weak blackout queue (`queue_blackouts_titles_weak_all.csv`, 225
    videos) can follow step 2 the same way if the owner wants it before the tiers. If a run prints `STOPPED` with
    exit code 3, YouTube refused requests: wait and run the same command again, do not push on. The quotes around
    `"youtube,captions"` matter in PowerShell: unquoted, the comma makes a list and python is handed two words.
    `--clobber` lets step 1 be run again over files already downloaded. A `--queue` run has no channel listing of
    its own and `catalog.py` reads only `jobs/queue.csv`, so the local catalogue of a `--queue` run carries the
    manifests' fields (the upload date among them) but no title or source url; those come with the Codespace
    rebuild below, which has the full listing.

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
  and none is held. On 2026-11-16: round `dc630af7` (195 files), `624da673` (2 transcribed episodes the sync had
  deleted before their Drive copy; rule fixed in PR #18), `8e25cdd8` (181 files, 1.02 GB) and `98788010` (7): the
  L/L Research "Ra Contact" session recordings, the last of the 86 transcribed recordings whose audio was not
  yet here (`transcript_audio.py --gaps` listed them; `download_enclosures.py` fetched 85, one file on
  llresearch.org's storage failed). After them 4,399 files (23.05 GB) are on Drive and every audio file on disk
  is among them. `drive_stage.py done` takes `--out <stage folder>` as well as `--round`.
* **The audio behind every transcript** (`transcript_audio.py`, PR #17; `plan/transcript_audio.csv`, the
  dashboard's "Audio behind the transcripts"): of 10,175 items with a transcript of any kind, 324 have their
  recording downloaded (all 324 in the store and on Drive, 88 still on disk); 5,272 are web pages with no
  recording, 4,565 are YouTube videos that only the owner's computer can fetch, 13 are interview episodes held by
  the live-channeling rule, 1 download failed. A recording whose audio is in the store or on Drive in every part
  counts as downloaded whatever the audio manifest says (since 2026-11-16: a download run that the full disk
  stopped between writing 13 files and their finished lines had left them as "not yet").
* **Contacts.** The websites-and-contacts table (`analysis/coverage/contacts.csv`, private; the dashboard's
  "Websites and contacts") carries, since 2026-11-16, each channel's public About page (`channel_about.py`,
  64 channels read, 57 declare links, 5 write an address in the description; the address behind YouTube's
  "view email" button sits behind a captcha and is not read) beside the addresses the makers' own podcast feeds
  publish (7); 11 rows have an address, each with its source named. Nothing of it is in the repository.
* **The public page of prediction timelines** (the owner's decision of 2026-11-16, within ANALYSIS_PLAN 12.9):
  `dashboard/predictions.html`, served by GitHub Pages at
  <https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/predictions.html>, built by
  `prediction_page.py --root <private> --out dashboard/predictions.html --publish-counts`. It lists the 480
  distinct candidates with a target window (20 people; 331 items), each with the person, the date said and its
  basis, the window, the kind of text, conditional and hedged, the item id, a public link and a quote of at most
  30 words (442 shown, 38 withheld: an item's quotes stay within 5% of its words, and a quote that is a
  questioner's turn, names a third party from the private list `analysis/predictions/questioner_names.txt`, or
  reproduces another author's byline shows its time expression instead); a timeline chart per person, a table
  view, filters, an index by target year, a methods note with the 56% caveat. The guard runs on the records and
  on the finished page and refuses to write it (exit 2) on any rule broken. An adversarial review found two
  questioner quotes, five third-party names and a count off by 29; all fixed before the first publish. The full
  private timelines (54 files) are zipped in Drive "05 Analysis" as
  `Prediction timelines, full private copy 2026-11-16`.
* **Blackouts of the power grid and the internet** (`theme_search.py` with `themes/blackouts.json`, 2026-11-16,
  ANALYSIS_PLAN 12.4.1; the owner's question of 2026-11-16, centred on each channel's newest 10 videos). A hit is
  a sentence or title that speaks literally of electric power, the grid, a blackout or outage, or of the internet,
  communications, satellites or electronics failing or being cut (metaphysical grids, media blackouts, fainting
  and the like are excluded by scoped rules); precision 0.87 on texts from the source and 0.83 on titles against
  the design labels, 0.93 and 0.97 on a fresh blinded sample of 63 hits coded by two coders (kappa 0.88). Newest
  10 (612 videos, 63 channels): 4 titles match, in 3 channels (Aaron Abke, a global blackout; Gigi Young, cyber
  attacks; Michelle Robinson, twice: cyber attacks and power outages with a 2027 target, and power-grid risks);
  38 of the videos have a text here through a twin, with 0 hits in those texts; the rest waits for the captions
  and audio the owner's computer fetches, the four matching videos first (`jobs/queue_blackouts_newest10.csv`,
  and `_newest20`, `_newest50`, `_all` with 40 videos). Everything stored: 9,998 source texts hold 80 distinct
  hits in 38 texts (Gosia 40, Sam 27, L/L Research 6, Suzanne Lie 4, Blossom Goodchild 2, Scranton 1), 198
  speech-to-text transcripts hold 4 (Stewart Pearce), 72,655 video titles hold 30 (Elizabeth April 7, Ismael
  Perez 4, Michelle Robinson 4, Ivan Teller 3, Sam 3, Paul White Gold Eagle 2, seven others 1); 32 hits speak of
  the future, 13 are prediction candidates, 3 name a target year (2021, 2024 to 2027). Counts in
  `plan/theme_blackouts.csv` and `plan/theme_blackouts_newest10.csv`; the hits and the coders' sample stay in
  `analysis/themes/blackouts/`; `theme_search.py leaks` proves no stored text entered the lexicon file or the
  tests. An adversarial review found two example sentences too close to stored text, twin titles counted twice
  and kinds pooled in the precision figure; all fixed before this commit.
* **Typd (SameRainbows/typd-app) was checked on 2026-11-16 at the owner's request** as a possible speech-to-text
  engine: it is an Electron dictation app whose model (Qwen3-ASR 1.7B, trained further for dictation) needs an
  NVIDIA GPU with 4 GB or an Apple-silicon Mac, calls its CPU fallback "much slower", and is trained to write
  what the speaker meant (fillers gone, self-corrections resolved) rather than every word, so it cannot run on
  this 2-core machine and would not give the verbatim, time-aligned transcripts the quotes and offsets need.
  The engine stays faster-whisper (base.en, int8, CPU). **Speech-to-text was paused at 05:39 UTC the same
  day** (the `keep_transcribing.sh` loop and its worker killed by process id) to give both cores to the
  downloads and their Opus conversion while the backlog is fetched and copied to Drive; start it again with
  `resume_jobs.sh` (or `setsid nohup bash -c 'while true; do bash et-channelers/pipeline/keep_transcribing.sh;
  sleep 1800; done' >> ~/et-channelers-private/logs/asr.log 2>&1 < /dev/null &`) once the downloads are done.
  With the loop paused, untranscribed audio stays on disk (the sync's hold rule), so watch the free space.
* **The public predictions page was redesigned on 2026-11-16** (`prediction_page.py`, same guard, 54 tests): a
  zoomable and pannable timeline over the full data extent with semantic ticks, counted stacks for dense years, a
  shaded past and a now line, a brush mini-map, zoom buttons and keyboard keys, a hover lead line from the year said
  to the target; rows by person, kind of text, decade said or certainty; cards regrouped by moving the same nodes (so
  every quote still occurs once); faceted filters with counts, search with quoted phrases and minus exclusion, window
  presets, a "list follows the window" switch, a sortable table and a CSV of the public fields; the whole view lives
  in the URL hash (old `d=` fragments still work); the page degrades to the lists and table without d3 (the one
  external script, from cdnjs). Built by a workflow of three design agents, a judge, one implementer, an adversarial
  reviewer and a fix pass (three majors fixed: a wheel-scroll trap, a sticky axis misaligned with a classic
  scrollbar, a focusable link inside aria-hidden). No browser on this machine: verified by the tests, node --check
  and the guard on the real data (480 statements, 442 quotes, max item share 5.0%, 925 KB).
* **Nine YouTube channels named by the owner on 2026-11-16** ("go through all channels for the past 20 videos,
  download transcripts and audios; add these"): four were already tracked with the same channel ids (Sam the
  Illusionist, Saraharyana, Lee Carroll's Kryon channel, which the index held without an address and now has
  one in `sources/extra_channels.csv`, and Rachel & Kevin Pasdon's Disciples of Light); five are new people in
  `sources/extra_targets.csv` and `extra_channels.csv`, with their official sites from their About pages in
  `official_sites.csv`: Lee Harris (channels "the Z's"), Lily Nova (an ET contactee: role `contactee`), Kelly
  Kolodney (the channel is called The Angel Raphael), Debbra Lupien (the Akashic Records, Archangel Metatron)
  and The Judah Channel (a collective named Judah). Channel ids came from each channel's Videos-tab listing by
  yt-dlp; the About pages were read (69 channels now); the private contacts table has 107 rows. Every channel's
  newest 50 videos were relisted into `/workspaces/et-yt-newest` and the three newest queues rebuilt in rank
  order (table above) and uploaded to the private release `handoff-2026-11-14`. **Captions and audio still
  cannot be fetched from this Codespace**: YouTube's bot check answers cloud machines, and the environment's
  safety classifier refused the fetch step again on 2026-11-16 (no cookies, proxies or alternate clients are
  used, by the project's rule); the newest-20 queue (1,320 videos, 555.5 h) is for the owner's computer, see
  "One command on your own computer" in `pipeline/README.md`.
* **Podcast backlog round 3 and the disk rule, 2026-11-16 17:36 UTC.** The owner asked to keep downloading audio and
  pushing it to Drive at the same time. With 4.0 GB free and the download's 3 GB floor, the local copies of 805
  recordings (6.30 GB) that are verified in the private store (`sync_manifest.jsonl`) and fully on Drive
  (`drive_manifest.jsonl`) but not yet transcribed were removed; 150 were kept, in audio-manifest order, for
  speech-to-text. Their ids are in `jobs/local_audio_removed_20261116T173617Z.txt`; `sync_archive.py pull --root
  <private> --store gh:occult-kranti/et-channelers-archive@archive-v1 --ids <ids>` (with the token in the
  environment) brings any of them back when speech-to-text reaches them. Round 3 (`jobs/queue_backlog_3.csv`,
  `select_episodes.py --relation own,host,file,archive --max-hours 250 --seed 20261113`: 3,324 rows, 2,976 already
  here, 348 new from 5 hosts, 174.2 h) started at 17:36 UTC (`download_enclosures.py --all --workers 3 --per-host 2
  --min-interval 1.5 --min-free-gb 3`, log `logs/backlog_download.log`); Drive rounds of 100 follow as it lands.
* **Evening of 2026-11-16 (18:00 to 20:15 UTC): round 2 of the public page, the scout squad, three Codespace restarts,
  and the move to the owner's own VS Code.** The public predictions page got its second round (`prediction_page.py`,
  same guard; a workflow of three designers, a judge and an implementer, then checks by hand because the Codespace
  kept restarting): browser full screen and an expanded mode (`fs=1` in the address), Filters and List sheets on
  phones, a keyboard model with a help dialog (`?`), a probe year, lead lines, pinned statements with details under
  the chart, `j`/`k` through the statements in view, Copy link, CSV download; 62 tests; the page is 973 KB and
  renders with no script error at 1280 and 400 px (Playwright). A squad of 79 `et-source-scout` agents (one per
  tracked person without a source outside YouTube) found 136 proposals for 60 people (47 certain, 35 likely, 54
  candidates); the skeptic stage was cut short by the restarts, so nothing is registered: the proposals are in the
  private `analysis/coverage/scout_proposals_2026-11-16.jsonl` and on the release `handoff-2026-11-14`, each with
  its evidence and the file and row it belongs in. Drive: rounds `7f0dde3b` (31 of its 100 landed before the first
  restart; the 31 recorded, the rest renumbered) and `8dfaaeb9` (100) went up, 5,523 files (27.9 GB) in 78 folders
  at 18:40 UTC, the ledger on the release; round `65a4647c` (100 of 147 waiting files) is staged under
  `~/et-drive/stage-all` and not uploaded. The Codespace VM restarted at about 18:11, 19:05 and 19:44 UTC (the
  `/tmp` volume came back empty each time; no OOM kill was recorded), ending every job and workflow; the jobs were
  restarted at 19:46 UTC and the owner then asked for no more restarts and for a handoff to their own VS Code
  (section 9). Lessons: keep the "i id" lines of a Drive round in `~/et-drive/stage-all/ids_<round>.txt` as they
  arrive, so a break loses nothing; a resumed workflow replays its cached stages but a long review agent that is
  killed three times never finishes, so do its checks by hand. The collection dashboard now has a local copy,
  `dashboard/collection/index.html`, that reads the same tables from `plan/*.csv`.
* **Speech-to-text restarted at 15:13 UTC on 2026-11-16** (`resume_jobs.sh` with the Drive hold and the backlog
  queue) once the backlog download of 389 episodes had finished (387 fetched, 2 failed). Disk: the root volume was
  at 3.2 GB free; 4.4 GB were freed (the Copilot cache, the pip caches, the local copy of the ArchiveShelf release
  shards, which match the GitHub release byte for byte, and the staging cut pieces of files already recorded on
  Drive). The Drive staging copies live on the separate /tmp volume (34 GB free), so they cost the root volume
  nothing.
* **Keywords and TF-IDF of the newest tiers** (`keywords.py`, 2026-11-16; `plan/keywords_newest10.csv`, counts
  and p-values only): each channel's newest 10/20/50 titles against its own history and the other channels,
  and its texts as they arrive (kinds apart). In the newest 10: "2026" is the term rising most across channels
  (7.0% of titles against 0.9% before), with "channeled message", "november", "starseeds" and "activation";
  "channeling" and "love" fall. Titles naming blackouts, the grid or outages: 4 of 612 against 37 of 58,105
  before (Fisher p 0.0009; Aaron Abke, Gigi Young, Michelle Robinson ×2); 5 of 1,200 in the newest 20, 7 of
  2,920 in the newest 50. The terms and titles themselves are in `analysis/keywords/<scope>/` (private).
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
* **Reader comments in stored blog texts.** Suzanne Lie's 1,361 posts stored by 2026-11-15 end with their
  Blogger comment block (2,603,261 words with them, 1,954,916 without: a quarter are readers' words), so her
  counts of words from the source include readers' words. The prediction pass cuts them (section 5). Since
  2026-11-15 the texts lane leaves comment threads and reply forms out of what it stores
  (`fetch_publisher_text.is_comment_block`: Blogger's `comments` block, WordPress's `comments-area`, `respond`);
  the page as fetched is still kept in `.source.gz`. **Rewritten on 2026-11-16** (`fetch_publisher_text.py
  --rederive --apply`): 1,384 stored texts rebuilt from their `.source.gz` without the comment threads (16.25M
  words to 15.60M; Suzanne Lie's 1,361 posts 2.94M to 2.29M), 1,389 manifest lines appended, 58 pages' YouTube
  ids corrected (29 false "page-embed" twins gone), the old texts saved in `backups/publisher-texts-before-
  rederive-20261116T033153Z.tar.gz`; the store sync uploads the changed texts as new versions. Still open: 42 of
  her pages keep as their only YouTube id a sidebar link to an archive post, which the catalogue still reads as a
  twin; the fix is to read ids inside the post body only.
* **Transcribed audio could be deleted before its Drive copy was made.** `sync_archive.py` deleted audio that had a
  transcript before reading the hold notes, so a file transcribed quickly left the disk before a Drive round took
  it: two Steve Nobel episodes were in the store but not on Drive. Fixed on 2026-11-16 (the holds are read first;
  `pull --ids` brings a few items back from the store); both are on Drive (round `624da673`).
* **tv.bashar.org** is paid and behind a login: not collected.
* **No video is held.** Every lane keeps audio only. The 153 archive.org video files of Bashar sessions are
  listed, not fetched.

## 8. Order of work for the next session

1. Set up and check (section 3): the token in `~/.config/et-channelers/github_token`, the private folder, the
   state and the newer Drive ledger from the release `handoff-2026-11-14`, `sync_archive.py status`.
2. Start what the machine can carry (section 4, `resume_jobs.sh`): the sync, the collection cycles,
   speech-to-text sized to the cores, the Drive hold, and the podcast backlog round 3 (`jobs/queue_backlog_3.csv`,
   136 episodes left at 19:50 UTC on 2026-11-16). The Codespace jobs were left running at 19:46 UTC and die with
   the next restart; do not count on them.
3. Drive: the staged round `65a4647c` and whatever round 3 adds. The Claude Drive connector is not available
   outside Claude; use rclone with a one-time Google login (decision 6.5) or leave the Drive rounds to a Claude
   session; `drive_stage.py` does everything but the upload.
4. YouTube from the owner's own connection (section 5, "One command on your own computer" in
   `pipeline/README.md`): the blackout-titled queue first, then the newest 10, 20 and 50 of every channel; store,
   copy to Drive, rebuild the tables.
5. The scouted sources: read `analysis/coverage/scout_proposals_2026-11-16.jsonl` (private; on the release),
   check each "certain" and "likely" proposal against the person's own site, register feeds with
   `find_feeds.py --only <ids> --all --check-links --merge`, sites as `sources/official_sites.csv` rows, text
   pages with `list_site_pages.py --merge`, then fetch, queue and download (`select_episodes.py`,
   `download_enclosures.py`).
6. As text arrives: `prediction_timeline.py`, `prediction_page.py --publish-counts`, `theme_search.py --scope
   newest10`, `keywords.py`; refresh the tables (`targets.py`, `sources_table.py`, `catalog.py --publish`,
   `transcript_audio.py --publish-counts`) and the dashboard datasets.
7. Choose the speech-to-text engine for the backlog (6.1, a GPU); the model pass over the prediction candidates
   needs an API key and the owner's go-ahead (D14).
8. Fold in the Kimi snapshot (ROADMAP phase 4b); after collection, the analyses of phases 7, 7a and 7c.

The rules do not change:
* audio and transcript text stay private, and quotes are at most 30 words;
* robots.txt is obeyed;
* no way around a block is used;
* nothing private goes into this repository or into an outbound request;
* every change comes on a branch, with the three test suites and both guards passing before the merge.

## 9. Prompt for the next session (the owner's own VS Code, 2026-11-16 evening)

Paste this into the coding agent (Codex or another) in VS Code, with the repository open at its root:

> You are taking over the ET-channelers collection and analysis (folder `et-channelers/` of this repository)
> from a Claude Code session that ran in a GitHub Codespace until 2026-11-16, about 20:15 UTC. You now run on the
> owner's own computer, which is the one machine that may fetch YouTube captions and audio. Act as the owner's
> engineer and team lead: read before acting, keep the rules below, parallelise with agents where it helps, and
> report counts and dates, never a sentence of the private texts.
>
> Read first, in this order: `et-channelers/HANDOFF.md` (sections 1, 2, 3, 5, 7 and 8), `et-channelers/ROADMAP.md`
> (section 00 and the table of rows), `et-channelers/pipeline/README.md` (set-up, "One command on your own
> computer", "A browsable copy on Google Drive"), and `et-channelers/ANALYSIS_PLAN.md` section 12 when you reach the
> analyses.
>
> What exists. Public repository `occult-kranti/bashar-index` (GitHub Pages serves it; the public predictions page
> is `et-channelers/dashboard/predictions.html`). Private store `occult-kranti/et-channelers-archive`: release
> `archive-v1` (checked bundles of audio, transcripts and texts; `pipeline/sync_archive.py push/pull/status`),
> `archiveshelf-podcast-audio-v1`, and `handoff-2026-11-14` (the state without media: the audio, sync and Drive
> manifests, the queues `queue_newest10/20/50.csv`, `queue_blackouts_titles_all.csv`, `queue_youtube_all.csv`,
> `scout_proposals_2026-11-16.jsonl`, the memory files). The private data folder is expected at
> `~/et-channelers-private` (set `ET_PRIVATE_DIR` otherwise): `audio/`, `transcripts/`, `texts/`, `sync/`
> (manifests and holds), `jobs/`, `logs/`, `analysis/`. The owner's Google Drive folder "ET Channelers Archive"
> holds a browsable copy (5,523 files, 27.9 GB, 78 folders at 18:40 UTC on 2026-11-16; 147 files of podcast
> backlog round 3 still waiting, 100 of them staged as round `65a4647c`). The collection dashboard is a claude.ai
> page (address in HANDOFF section 2) with a local copy `et-channelers/dashboard/collection/index.html` that reads
> `et-channelers/plan/*.csv`.
>
> Where it stood at the handoff. Collected and in the store: the 903 Bashar archive.org sessions, three podcast
> backlog rounds (351, 389 and 348 episodes; round 3 had 136 episodes left), creators' files 111 of 1,410, 29 of
> 30 interviews, 10,267 items with text (texts from the source 10,042; 250 transcripts made here by faster-whisper;
> the two kinds are never mixed in one table or file). Prediction candidates: 6,041 (5,517 distinct), 499 with a
> target window, about 56% of windowed candidates real predictions (fresh samples, kappa 0.91 to 0.96); the public
> page shows 480 windowed statements with quotes of at most 30 words. Blackout theme search built and run
> (`theme_search.py`); keywords of the newest tiers built (`keywords.py`). Contacts: a private table (107 rows, 69
> About pages, 12 addresses) that never enters the repository. Sources scouted on 2026-11-16 for the 79 people
> without a source outside YouTube: 136 proposals for 60 people, unverified, in the proposals file. YouTube: 69
> channels listed (3,220 newest videos in `/workspaces/et-yt-newest` of the Codespace and the queues on the
> release); captions and audio were never fetched from the cloud (bot checks; the project uses no cookies,
> proxies or alternate clients), so the queues wait for this computer.
>
> Do, in order (HANDOFF section 8 has the detail):
> 1. Set up as in HANDOFF section 3: ask me for the GitHub token and keep it in
>    `~/.config/et-channelers/github_token` (never print it, never put it on a command line; `export
>    GH_TOKEN="$(tr -d '[:space:]' < ~/.config/et-channelers/github_token)"` when a tool needs it); a Python
>    virtual environment with the pipeline's requirements; restore the state and the memory files from the release
>    `handoff-2026-11-14`, copy its `drive_manifest.jsonl` over the restored one, pull the transcripts and texts
>    (`sync_archive.py pull`), and show me `sync_archive.py status`.
> 2. Start the jobs sized to this machine (`pipeline/resume_jobs.sh` with `ET_DRIVE_HOLD=1` and
>    `ET_BACKLOG_QUEUE=<private>/jobs/queue_backlog_3.csv`); finish backlog round 3.
> 3. Run the YouTube tiers from this connection: `run_all.py` as "One command on your own computer" says, the
>    blackout-titled queue first, then the newest 10, 20 and 50 of every channel; store each tier, rebuild the
>    tables, copy to Drive (rclone, decision 6.5, since the Claude Drive connector is not here).
> 4. Check and register the scouted sources (step 5 of section 8), fetch and queue what they add.
> 5. As text lands: the prediction pass and page, the blackout search over captions and speech-to-text, the
>    keywords; refresh the tables and the dashboard copy.
> 6. Bring HANDOFF, ROADMAP and the README to the day's state in the same pull request as each piece of work;
>    work on a branch, run the three test suites (`pipeline/tests/`) and both guards, push, open the PR and
>    merge it.
>
> Rules that do not change: audio, captions and transcript text stay in the private folder and the private store,
> never in this repository, in a chat reply or in an outbound request; quotes are at most 30 words and 5% of an
> item; the contacts table (addresses) lives in the private folder only; robots.txt is obeyed and no way around a
> block is used (no cookies, logins, proxies, mirror sites or alternate players); every lexicon example and test
> fixture is invented; kill a job by its pid, never by pattern; no `rm` with a shell variable in the path; nothing
> about the owner or the project goes into a search query. Commit messages end with the agent's co-author line and
> pull requests with its footer, as the repository's history shows.
