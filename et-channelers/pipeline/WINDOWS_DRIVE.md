# Windows: newest 20, then 50, then the full audio archive

The November 19 run selects up to twenty public regular uploads from each creator's Videos tab. Use stable IDs to retain older entries, Shorts and completed streams. The current archive has a 23 GB project budget and a 12 GB physical free-space reserve. The launcher defaults to six source workers, three Drive upload transfers and twelve recordings per upload group. [Current selection and operating procedure](COLLECTION_PROCESS.md)

This collection lane saves the native audio stream for each queued video, uploads it to Google Drive,
checks the remote byte count and MD5 for the audio and its metadata sidecar, and then removes the
verified local copies. It does not download
the picture, re-encode audio, or start speech-to-text. Files keep their source container, usually
`.m4a` or `.webm`; the older pipeline's 24 kbps `.opus` size estimates do not apply.

The queue prepared on November 16, 2026 at 16:48 UTC contains 1,320 videos across 69 tracked channels, about 555.5
hours. It selects each channel's Videos tab, excluding Shorts and live-stream tabs. The adjacent
`queue_newest20.meta.json` records the listing and selection. A saved queue is a dated snapshot;
refresh it when a newer collection is wanted. Its rank order gives every channel's newest item a turn
before moving to second-newest items. Five channels currently contribute fewer than 20 items.

The newest-50 tier contains **3,220 videos across the same 69 channels**, including every newest-20
item, about 1,351.7 hours. Both tiers keep the established Videos-tab selection and original ranks.
There is no duration filter. `RunAll` now continues through these two tiers and then downloads the
remaining archive; the earlier instruction to hold the final round has been superseded.

The full catalog is `queue_youtube_all_merged.csv`: **63,929 unique saved items**, including
35,907 Videos-tab items, 17,422 Shorts, 10,533 recorded streams, and 67 legacy items whose tab was
not recorded. There are 107 source-directory labels, including linked host-show items; this is not
a full crawl of 107 channels. Saved history listings now cover all 69 tracked channels, after a
successful six-channel refresh added 5,130 listed items before deduplication. The merge also keeps
newest-20 items missing from the older full snapshot. Current broadcasts and upcoming streams are
not downloaded. Explicit premiere countdowns remain pending without stopping other channels; after
useful stage work finishes they receive one final revisit, then remain pending if still unavailable. Snapshot coverage does not establish that every historical upload is still available.
After excluding the 3,220 newest-50 IDs, **60,709 items** remain in the final round:
32,687 Videos-tab items, 17,422 Shorts, 10,533 recorded streams, and 67 unknown-tab legacy items.
The final round starts only after the newest-20 and newest-50 completion gates pass in `RunAll`.
`Run` still processes only newest 20, and `Index` only rebuilds the local queue files.
The 63,929-item catalog is saved on Drive. Its immutable checkpoints preserve all indexed rows plus
updated upload receipts; newest-50 and final-round queues are reproducible from the retained inputs.

## Connection checked on November 16, 2026

The user completed rclone's Google login. The `etdrive` remote now starts inside the existing
**ET Channelers Archive**. Its numbered folders and `04 Audio` directory were read back successfully;
the account reported about 5.47 TB available. The tools and newest-20 queue are installed, so proceed
to **Run from PowerShell** below.

The original shared OAuth client hit repeated quota errors. A dedicated Desktop app client has
now been applied to `etdrive`, preserving the archive root. Google authorization and Drive API
enablement succeeded; a 12-pair upload pilot verified both artifacts before local cleanup, bringing
this lane to 14 verified pairs. The owner chose to keep the OAuth app in Testing mode, so expect
reauthorization around November 23, 2026 if collection continues. For another
machine, follow the [official Desktop app setup](https://rclone.org/drive/#making-your-own-client-id),
then edit `etdrive` through `rclone config` and reauthenticate. Keep the same archive root folder.

## First-time setup on another machine

The tools are installed outside the repository at `$env:USERPROFILE\et-channelers-tools`.
Google authentication for rclone is separate from the ChatGPT Drive connector and from GitHub.

```powershell
$EtRclone = Join-Path $env:USERPROFILE 'et-channelers-tools\rclone.exe'
& $EtRclone config
```

Use these responses in the interactive configuration:

1. Create a new remote (`n`), named `etdrive`, with storage type `drive`.
2. Enter your own Google OAuth client ID and client secret using the setup linked above.
3. Select scope `drive` to work inside the existing archive. Leave the service-account path blank.
4. Authenticate in your browser using the account that owns the archive. Choose no Shared Drive
   unless this archive actually belongs to one. Save the remote.

These choices follow the [official Drive configuration guide](https://rclone.org/drive/#configuration).
The `drive` scope grants broad Drive access. Setting a root folder changes rclone's starting path;
it does **not** narrow the OAuth permission.

Set the starting folder to the existing **ET Channelers Archive**, then inspect it:

```powershell
& $EtRclone config update etdrive root_folder_id '1pMBEavFcXc3BrDbg0BqW0mKkpyOHjD_B' config_refresh_token false
& $EtRclone lsd 'etdrive:'
& $EtRclone about 'etdrive:'
```

`config_refresh_token false` keeps this folder update from repeating authentication; see
[rclone config update](https://rclone.org/commands/rclone_config_update/).
The folder listing should show the archive's existing numbered folders, including `04 Audio`.
Check the available Drive space. Keep the rclone configuration private; do not paste its contents
or authentication tokens into this repository or a handoff.

The destination for this collection is:

```text
etdrive:04 Audio
```

Inside it the collector uses `<channel_dir>/<source-tab-folder>/<video_id>.<ext>`. The folders are
`Videos`, `Shorts`, `Recorded streams`, and `Unclassified`, selected from the recorded source tab.
Duration never determines a video's category. Existing receipts in `YouTube native` remain usable;
the collector does not move those files. The stable video ID
ties each recording to its title and source URL in the private queue and manifests.
Alongside each recording it saves `<video_id>.info.json` containing the metadata supplied for that
video: for example its full description, tags, chapters, upload/release dates, duration, channel
identifiers, category and engagement counts when available. Missing provider fields stay absent.
Temporary stream URLs, request headers and local filesystem paths are excluded. Both files must
pass Drive checksum verification before local cleanup.
If you override `-Remote`, select an existing destination directory; the runner checks it before
downloading media.

## Run from PowerShell

From the repository directory, inspect the queue and local budget first:

```powershell
& .\et-channelers\pipeline\start_drive_ingest.ps1 -Mode Plan
```

After the Drive connection works, try one item, inspect its receipt, then continue the queue:

```powershell
& .\et-channelers\pipeline\start_drive_ingest.ps1 -Mode Run -Limit 1
& .\et-channelers\pipeline\start_drive_ingest.ps1 -Mode Status
& .\et-channelers\pipeline\start_drive_ingest.ps1 -Mode Run
```

To complete the newest 20, continue to the newest 50, and then collect the remaining archive:

```powershell
& .\et-channelers\pipeline\start_drive_ingest.ps1 -Mode RunAll
```

`RunAll` finishes the newest-20 queue, then checks that every available required ID has verified-upload
and local-cleanup receipts for **both audio and metadata** at the same Drive destination.
An explicit terminal `unavailable` receipt may pass the gate, but is counted separately from verified
pairs. Authentication requests, bot checks, 403/429 refusals, quota failures and generic errors never
qualify as unavailable or as a successful collection.
Only then does it process `queue_newest50_enriched.csv` with `--newest 50`, skipping completed IDs.
After the same check for all newest-50 items, it processes `queue_final_round.csv` with
`--entire-queue` and checks the final receipts. Local stage inputs are validated and rebuilt before
network work starts. Blocked or unverified items keep the later stage pending. Repeating `RunAll`
resumes this same order; the launcher itself has no automatic retry loop.

When `archive_catalog.py` is available, each passed stage also prepares and uploads a compact
catalog checkpoint before advancing. Repeated unchanged checkpoints upload nothing; receipt
changes produce immutable deltas and a small manifest, preserving the previous baseline. These
calls share the collector's Drive cooldown and single-run lock. A checkpoint error stops progression
and returns its exit code. `-SkipCatalogCheckpoint` explicitly skips this optional backup while
retaining every media verification gate. See [ARCHIVE_CATALOG.md](ARCHIVE_CATALOG.md).

The prepared stage files are in the private `jobs` folder:

- `queue_newest50_enriched.csv`: the original 3,220 IDs and ranks with person/source metadata.
- `queue_final_round.csv`: full catalog minus the newest-50 IDs, retaining every source tab and duration.
- `final_round_by_channel_tab.csv`: remaining counts and known hours grouped by source and tab.
- `collection_stages.meta.json`: input hashes, output hashes, counts, and `indexed_only_not_started` status.

Rebuild these indexes without downloading media using `-Mode Index`. The original newest-50 release
asset must be present as `jobs/queue_newest50.csv` (or pass `-FiftyQueue <path>`):

```powershell
& .\et-channelers\pipeline\start_drive_ingest.ps1 -Mode Index
```

To resume just the final round, `-Mode RunFinal` checks newest-50 completion and then processes
`queue_final_round.csv`. `RunAll` reaches that same work after both priority tiers.
Use `-FullQueue <path>` when refreshing the catalog used for indexing.

`prepare_all_queue.py` builds that merged queue from the newest-20 snapshot, the saved full queue,
and optionally a fresh discovery root. It also writes `.meta.json` with input hashes and coverage,
plus `.channels.csv` mapping source folders to readable person names. The enriched queue retains
source channel, primary person, and item-level entity labels separately; missing entities remain
unknown, and existing labels are marked as unverified source metadata. A host's Bashar-corpus item
can therefore be associated with Darryl Anka while retaining its host-show source.

To rebuild the union without making network requests:

```powershell
$EtPrivate = Join-Path $env:USERPROFILE 'et-channelers-private'
$EtPython = Join-Path $env:USERPROFILE 'et-channelers-tools\venv\Scripts\python.exe'
& $EtPython -I .\et-channelers\pipeline\prepare_all_queue.py `
    --newest "$EtPrivate\jobs\queue_newest20.csv" `
    --existing "$EtPrivate\jobs\queue_youtube_all.csv" `
    --discover-root "$EtPrivate" `
    --out "$EtPrivate\jobs\queue_youtube_all_merged.csv" `
    --newest-out "$EtPrivate\jobs\queue_newest20_enriched.csv"
```

Change `--discover-root <private-listing-root>` if fresh listings were saved elsewhere. Review
`tracked_channels_missing_full_listing` in the metadata sidecar before describing the queue as
covering all tracked channels' history; a snapshot still cannot prove that every historical upload
remains available.

The wrapper prefers the prepared private queue at
`$env:USERPROFILE\et-channelers-private\jobs\queue_newest20_enriched.csv`, falling back to the original
`queue_newest20.csv` when the enriched copy is absent. The enriched subset preserves the original
1,320 IDs, ranks, and order, with a sidecar recording the original queue hash. The release asset
stays unchanged. The wrapper runs in the foreground.
It sets the already-authorized YouTube override for this process and restores the previous environment
afterward. Keep the computer awake and rerun the same command after an interruption.

If local script policy blocks the reviewed wrapper, run it with a policy override for just that
PowerShell process:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\et-channelers\pipeline\start_drive_ingest.ps1 -Mode Plan
```

The launcher runs six download workers and three simultaneous Drive transfers by default.
Downloads and uploads have separate limits.

| Launcher option | Default | Allowed |
| --- | ---: | --- |
| `-DlWorkers` (`-Workers` alias) | 6 | 1–8 |
| `-UploadTransfers` | 3 | 1–4 |
| `-MaxLocalGb` | 23 decimal GB across managed roots | 1–23 |
| `-UploadBatchItems` | 12 pairs | 1–16, up to `ReadyItems` |
| `-UploadBatchSeconds` | 10 | 0–300; zero flushes immediately |
| `-ReadyItems` | 24 pairs | 1–64 |
| `-Newest` | 20 | 20 or 50 for a single queue in Plan or Run mode |
| `-RateMiB` | 2 per download worker | Positive; launcher maximum 100 |
| `-MinInterval` | 5 seconds | 0–3600 between metadata request starts |

After latest-20+ translation and both analysis rounds, run a prepared public-50 queue by passing its pending CSV and rank limit together.
This includes the recording at rank 50. The archive's scheduling receipt permits the media run when the earlier study is complete. Previewing the queue reads local files. [Forecast and schedule](COLLECTION_PROCESS.md#latest-50-forecast)

```powershell
& .\et-channelers\pipeline\start_drive_ingest.ps1 -Mode Plan -Newest 50 -Queue $pendingCsv
& .\et-channelers\pipeline\start_drive_ingest.ps1 -Mode Run -Newest 50 -Queue $pendingCsv
```

The installed yt-dlp version is pinned to official nightly `2026.11.15.232800` after a November
upstream client-policy fix. The previously failing item passed a normal-client bounded recheck,
then a full download/upload/verification cycle. Its isolated repair acknowledgement is retained
in the private journal; this does not disable cooldowns for later source refusals. The private
`jobs/ytdlp_nightly_2026-11-16_upgrade.json` records the version, provenance and rollback command.

## English captions and transcripts

Collection also saves published English captions and original English automatic captions, including
regional variants such as `en-US` and `en-GB`. Other languages and every machine-translated track
are excluded. Track identity, language and published/automatic provenance remain separate; an
automatic track is not described as a publisher-written transcript.

New audio items reuse their metadata extraction. Previously verified audio items receive a
metadata-only caption backfill, without downloading their audio again or overwriting the existing
immutable `.info.json`. Metadata extraction explicitly simulates subtitle output so it can report
caption access requirements without downloading duplicate tracks.

Each track is stored beside its audio as `<video_id>.captions.<track_id>.zip`, containing:

- `raw.json3` (preferred) or `raw.vtt`: the original timed source response.
- `segments.json`: parsed timing and text, with normalization provenance.
- `transcript.txt`: readable text derived from that track.
- `provenance.json`: language, track kind, acquisition time and hashes, excluding transport URLs.

One ZIP per track reduces Drive object and verification requests. ZIPs share the same storage
accounting, upload coordinator and checksum-before-delete rules as audio. The separate
`sync/drive_caption_manifest.jsonl` retains partial progress and verified Drive proofs. Caption
failures never invalidate verified audio receipts; completed audio and caption bundles can drain
to Drive independently. Caption fetches use one shared request slot and at least 15 seconds
between starts. A caption 403 or 429 establishes a separate persisted 24-hour caption cooldown;
audio acquisition and Drive uploads continue when their own endpoints are available. Previously
verified audio is not re-extracted for captions during that window. New audio metadata can still
record pending caption tracks for the later backfill.

Only a complete source inventory with no requested English track counts as `none`. Missing-token
warnings, missing inventories, empty responses and access errors remain pending. A 64 MiB raw-track
processing bound defers oversized caption responses rather than truncating them or claiming absence;
there is no audio-duration filter. No speech-to-text model is started.

The private catalog includes caption state, language, track kind and verified bundle locations.
The collection dashboard publishes only aggregate caption counts. Research, version details and
alternatives are documented in [YOUTUBE_CAPTIONS_RESEARCH.md](YOUTUBE_CAPTIONS_RESEARCH.md).

## Bounded local supervisor

The versioned supervisor is [`supervise_drive_ingest.ps1`](supervise_drive_ingest.ps1). Its default
private root is `$env:USERPROFILE\et-channelers-private`, and its default launcher is the adjacent
`start_drive_ingest.ps1`. `-PrivateRoot` and `-LauncherPath` allow explicit overrides. It runs in the
foreground; it is not installed as a service or scheduled task. It owns an exclusive OS file lock so
a second supervisor cannot share the same private root. The collector keeps its separate single-run lock.

```powershell
& .\et-channelers\pipeline\supervise_drive_ingest.ps1 `
    -Mode RunAll -DlWorkers 8 -UploadTransfers 4 -UploadBatchItems 12 -ReadyItems 64 -MaxLocalGb 17 -MaxAttempts 3
```

The existing private `jobs/resume_staged_ingest.ps1` is only a compatibility wrapper: it forwards to
the versioned supervisor in the checkout named by `-RepositoryRoot`. It does not keep a separate
copy of the retry behavior.

Drive quota exit code `75` receives an exponential 10, 20, 40, then 60 minute backoff. Exit `3`
can retry only when the saved audio journal confirms a future YouTube hard-block deadline (403, rate limit
or bot check). The next audio attempt waits for the latest applicable audio, Drive or backoff deadline.
Caption cooldowns are separate: after an otherwise successful run, a validated pending-caption
summary can schedule a backfill after its own deadline. The summary is saved atomically at
`sync/drive_caption_backfill_state.json`. A recognized caption deadline that expires during the
successful archive run permits one immediate revisit of earlier tiers. An unchanged older deadline
or pending backfill without a recognized deadline does not trigger a retry loop. No request is sent to a blocked endpoint during its
24-hour rest period. Other extraction, login, permission, storage
and premiere results do not trigger automatic retries. The default budget is three launches
(maximum four), persisted before each child starts, so restarting the helper does not restore spent attempts. The stop marker is checked at least every two seconds
while waiting; the running collector observes that same marker.

The private `sync/drive_ingest_resume_state.json` records the attempt count, next permitted attempt,
PID and outcome. After reviewing an exhausted retry budget, an operator may explicitly add
`-ResetRetryBudget`; that resets only the attempt count and still honors the stored wait and both source and Drive
cooldowns. Neither helper clears `sync/STOP_DRIVE_INGEST`. No process is started by merely updating
these scripts.

Offline Windows regression tests replace the child launcher with a temporary stub, so they never
start the collector or contact YouTube or Drive:

```powershell
python -m unittest discover -s et-channelers/pipeline/tests -p test_supervise_drive_ingest.py -v
```

## Storage, verification, and recovery

### Current source-client investigation (November 16 evening Eastern)

**Later investigation, 01:14 UTC November 17:** installed official nightly `2026.11.16.232655`
and the upstream browser-backed WPC provider `1.1.2`. The owner explicitly requested Chromium
automation and another repair attempt. [`browser_source_probe.py`](browser_source_probe.py)
confirmed anonymous Chrome playback with an allowlisted diagnostic record. Two small WPC-backed
range requests succeeded, but full native transfers continued to return 403, including a bounded
attempt on the new Dreemtime channel. Keeping Chromium alive during streaming and using yt-dlp's
native downloader did not establish a reliable full-file fix. No additional full audio was verified.
These observations supersede the earlier “not installed” WPC note below.

[`browser_audio.py`](browser_audio.py) retains an entered yt-dlp/WPC context until the source
worker closes its lease. `--browser-audio` / `-BrowserAudio` explicitly selects this experimental
path; imports and ordinary runs do not start browsers. Its four-session pool uses fresh headless
profiles, no personal account, and no proxy. Metadata-only backfills retain the normal CLI path.
The experimental path requires at most four workers and a private ceiling of at most **16 GB**
to reserve additional tool/browser scratch headroom within the 20 GB total and 2 GB buffer.
It tracks its own temporary profiles and blocks further leases after failed cleanup. It has not
passed sustained-transfer/storage validation and is **not enabled in the current supervisor**.
Admission and socket waits are bounded; synchronous in-process extraction has no hard total
wall-clock kill. Raw browser/network errors, tokens and URLs are never copied to receipts.

The ordinary four-worker supervisor preserves the latest source deadline (November 18 01:13:30 UTC)
and its existing retry count. No small range response is sufficient to clear a new full-file refusal.
See [the dated ETA model](../research/collection-eta-2026-11-16.md): measured prefix goodput and
explicit missing-duration/upload scenarios yield about 7.7–16.5 **active** days for indexed audio,
not a promised completion interval. `collection_eta.py` is offline and starts no jobs. Download
receipts now include `download_started_at` and `download_elapsed_s` for improved future calibration.

The optional launcher/supervisor argument `-YoutubeClient mweb` forwards
`--youtube-client mweb` to the collector's audio metadata extraction. The default remains
`default`; caption backfill retains its own extraction behavior and cooldown. Receipts record the
selected client and source format ID without signed media URLs or tokens.

The local tools environment contains official yt-dlp nightly `2026.11.15.232800`, Deno `2.9.8`,
and [Bgutil PO-token provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) `2.0.2`
(tag commit `26475e9d3665b972c4aeb83b4dbaafcf64b88438`). Its shared Node `24.18.0` HTTP provider
listens only on `127.0.0.1:4416`. This follows the upstream
[PO-token guidance](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide); player, media and subtitle
token contexts are distinct. A local console preload redacts token/visitor/cookie/authorization
diagnostics. Private provenance records the package-lock and preload hashes. A nonbreaking
production dependency audit fix removed high findings; four moderate transitive findings remain.
No browser cookies, account rotation or proxy rotation were introduced.

The [browser-backed WPC provider](https://github.com/coletdjnz/yt-dlp-getpot-wpc) was researched,
not installed. Its experimental browser dependency and per-extraction browser cost make it a
poor first choice for several parallel workers. Browser extensions and transcript libraries
do not themselves demonstrate recovery from a timedtext 429. The existing caption lane therefore
keeps its serialized 15-second start interval and recorded rest window.

One normal `mweb`/provider probe returned the exact HTTP 206 range, followed by a successful full
audio upload, Drive hash verification and local deletion. Only that item's prior refusal received
an append-only repair acknowledgment. A later four-worker trial encountered a new media 403;
the new deadline was preserved. The current supervisor waits until **2026-11-18 00:11:16 UTC**
with four source workers, four upload transfers, eight-pair batches, 16 ready/in-flight slots,
10-second metadata spacing and its existing 1-of-3 attempt count. It does not continuously probe
during the wait. The provider is not claimed to solve every media or caption refusal.

The provider process is local-session state, not an installed service. After a reboot, inspect
its health and the private provenance before restarting the collector; do not assume this page
establishes that either process is running. Keep credential and provider-token logs private.

The standalone wrapper requests six download workers, with at most one active item per channel. Its default
project budget is **23 decimal GB**. It includes the private directory, tools, the checkout, the browser cache
and additional project directories saved in `PRIVATE_ROOT/sync/managed_storage_roots.json`. This file has
`schema_version` 1 and a `managed_roots` array of absolute directory paths. The Python command also accepts
repeatable `--managed-root` paths. Nested paths count once. Existing files, partial downloads and space
reserved for active downloads must fit the budget. The wrapper
sets no arbitrary per-item size or duration cutoff (`--max-item-mb 0`). An item that cannot currently
fit the storage budget remains deferred, rather than being counted as completed or dropped from
the index. Each download worker runs at up to 2 MiB/s using 1 MiB HTTP chunks, and metadata
request starts are spaced by at least 5 seconds across all workers. Available channels take turns
so one large channel does not occupy every worker. Upcoming recordings and isolated missing-format
results stay pending while other channels continue, with one later revisit after useful audio work.
Three missing-format outcomes without intervening audio progress stop new source work for review,
so a broken player/runtime cannot churn through the entire queue. Each admission preserves **12 GB of free
disk space** after download and journal reservations. Run this collector
alone in its private root; a separate application writing there is outside its storage guarantee.
One upload coordinator overlaps acquisition with three Drive transfers, a limit of 24 outstanding
pairs and batches of twelve. The ten-second timer flushes smaller groups. Rclone uses two API
requests per second and 32 MiB chunks, up to 96 MiB of chunk buffers at the default concurrency. Each local file remains
until Drive returns the expected size and MD5. This is a bounded local spool, not a Drive desktop
sync folder and not a pipe that discards bytes before they can be verified.
This is a rolling local limit across collection tiers; it does not limit the size of the Drive archive.
The Python command enforces the same 23 GB maximum and 12 GB minimum disk reserve.

Remote metadata is read using [rclone lsjson](https://rclone.org/commands/rclone_lsjson/), whose
`--stat --hash` result supplies the size, object identity, and available hashes. Upload failure,
missing hashes, or mismatched bytes leave the local copy available for recovery. Resume the same
runner rather than manually deleting files or moving them with an unrelated sync command.

`Status` reports the latest state per video and the total local bytes. The durable upload receipts
are at `<private-root>/sync/drive_ingest_manifest.jsonl`; the native-audio inventory is at
`<private-root>/audio/audio_manifest.jsonl`. Keep these small records and the queue for transcription
and collection accounting later. A `deleted` receipt means its upload was verified before local
cleanup of both audio and metadata; `downloaded` means it still needs uploading. An `error` may retain
a complete or partial file. Older receipts for audio alone require metadata backfill before they
count as complete under the current collector.

Drive returned HTTP 403 `rateLimitExceeded` during the initial collection. This is a temporary quota
refusal, separate from the successful OAuth connection. The collector retains the affected local
files, records a cooldown, and stops starting new downloads; it does not repeatedly retry the quota.
Resume the same command after the recorded retry time. A persistent
`<private-root>/sync/STOP_DRIVE_INGEST` marker also prevents work when a stop has been requested;
the wrapper never clears that marker automatically.

Transfers and checksums need modest CPU work. This lane starts no GPU computation, audio encoding,
or transcription. A 70% GPU utilization target belongs to the later transcription setup; no GPU
utilization cap is claimed by this downloader.

YouTube requests use conservative pacing without cookies, account login, or proxies. A bot check,
403, or 429 should be investigated from the recorded status instead of repeatedly restarting the
queue. Source refusals and unverified uploads are not successful downloads.
