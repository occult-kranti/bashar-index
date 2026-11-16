# Windows: newest 20 first, then the YouTube audio archive to Drive

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

The full phase now uses `queue_youtube_all_merged.csv`: **63,929 unique saved items**, including
35,907 Videos-tab items, 17,422 Shorts, 10,533 recorded streams, and 67 legacy items whose tab was
not recorded. There are 107 source-directory labels, including linked host-show items; this is not
a full crawl of 107 channels. Saved history listings now cover all 69 tracked channels, after a
successful six-channel refresh added 5,130 listed items before deduplication. The merge also keeps
newest-20 items missing from the older full snapshot. Current broadcasts and upcoming streams are
not downloaded. Snapshot coverage does not establish that every historical upload is still available.

## Connection checked on November 16, 2026

The user completed rclone's Google login. The `etdrive` remote now starts inside the existing
**ET Channelers Archive**. Its numbered folders and `04 Audio` directory were read back successfully;
the account reported about 5.47 TB available. The tools and newest-20 queue are installed, so proceed
to **Run from PowerShell** below.

The current remote uses rclone's shared OAuth client, which worked during verification but emits
a retirement warning. For continuity, create your own client using the
[official Desktop app setup](https://rclone.org/drive/#making-your-own-client-id), then edit `etdrive`
through `rclone config` and reauthenticate. Keep the same archive root folder.

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

Inside it the collector uses `<channel_dir>/YouTube native/<video_id>.<ext>`. The stable video ID
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

To complete the newest 20 first and automatically continue with the full saved archive:

```powershell
& .\et-channelers\pipeline\start_drive_ingest.ps1 -Mode RunAll
```

`RunAll` finishes the newest-20 queue, then checks that every required ID has verified-upload and
local-cleanup receipts for **both audio and metadata** at the same Drive destination.
Only then does it start `queue_youtube_all_merged.csv`
with the explicit `--entire-queue` option. Already completed IDs are skipped. If an item is unavailable,
blocked, or unverified, the second phase stays pending. Repeating `RunAll` resumes this same order.
Use `-FullQueue <path>` when a refreshed full-history snapshot is ready.

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

## Storage, verification, and recovery

The wrapper requests four workers, with at most one active item per channel, and a maximum
private-root budget of **19 decimal GB**, leaving
1 GB of the user's 20 GB local allowance for tools and supporting files outside that root. Existing
files, partial downloads, and reserved space for active downloads must fit the budget. Each item
has a 1,024 MB limit, each worker downloads at up to 2 MiB/s using 1 MiB HTTP chunks, and metadata
request starts are spaced by at least 5 seconds across all workers. Available channels take turns
so one large channel does not occupy every worker. A 3 GB free-disk floor also protects space for
other applications. Run this collector
alone in its private root; a separate application writing there is outside its storage guarantee.
Uploads overlap acquisition; each local file remains
until Drive returns the expected size and MD5. This is a bounded local spool, not a Drive desktop
sync folder and not a pipe that discards bytes before they can be verified.
This is a rolling local limit across both phases; it does not limit the size of the Drive archive.
The underlying Python command also rejects a configured ceiling above 20 GB.

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

Transfers and checksums need modest CPU work. This lane starts no GPU computation, audio encoding,
or transcription. A 70% GPU utilization target belongs to the later transcription setup; no GPU
utilization cap is claimed by this downloader.

YouTube requests use conservative pacing without cookies, account login, or proxies. A bot check,
403, or 429 should be investigated from the recorded status instead of repeatedly restarting the
queue. Source refusals and unverified uploads are not successful downloads.
