# YouTube archive catalog

The private archive stores native audio and a full sanitized `.info.json` for each
video. The catalog is a compact research index of those objects. It keeps source
identity, person-attribution basis, source tab, listing provenance, dates, duration,
receipt state, exact Drive paths, object IDs and checksums. Descriptions, tags,
chapters and other provider metadata remain in the per-video `.info.json`; the
catalog does not replace those files or reread them during checkpoints.

Optional caption evidence comes from the separate
`sync/drive_caption_manifest.jsonl`. The current policy collects English published
captions and original English automatic captions, including regional variants, and
excludes machine-translated tracks. Per-track ZIP bundles hold the original timed
caption, derived text/segments and provenance. The catalog reads receipts only; it
never opens these bundles, copies transcript text into CSV, or overwrites the audio
metadata. See [caption research and selection policy](YOUTUBE_CAPTIONS_RESEARCH.md).

New media uses `<channel>/Videos`, `Shorts`, `Recorded streams` or `Unclassified`,
selected from the recorded source tab. There is no duration exclusion. Existing
verified paths, including `YouTube native` and the original storage channel, are
preserved. `source_folder` describes the source classification; `audio_remote` and
`metadata_remote` give the actual locations. Missing person/entity attribution stays
unknown. Existing entity labels are unverified source metadata.

## Files and checkpoints

Local generated files stay outside Git, under
`<private-root>/catalog/youtube_archive/`. On Drive the corresponding files live
under `etdrive:04 Audio/_catalog/youtube/`:

```text
objects/<sha256>.items.csv.gz       compressed baseline or changed-item batch
objects/<sha256>.channels.csv       latest source-channel/tab counts
manifests/<sha256>.json             ordered baseline, deltas, hashes and provenance
```

The first checkpoint uploads three small catalog objects. Later checkpoints write
only changed item rows, the changed channel index and a new manifest. Repeating an
unchanged checkpoint reuses the same files. A change to the source queue creates a
new complete baseline, so removed queue IDs cannot survive as stale catalog rows.
Every video has one stable YouTube ID; later delta rows replace earlier rows with
that ID. Recorded streams, Shorts and unknown legacy items remain distinct source
categories. Source directories include linked hosts and must not be described as
the number of fully discovered tracked channels.

Objects and manifests are immutable and addressed by their SHA-256. Uploads use
the collector's rclone adapter, rate-limit cooldown and remote size/MD5 check.
Previously verified catalog receipts avoid repeated remote checks. The new manifest
is uploaded last, after every referenced object has a durable verification receipt.
No Drive-wide listing or synchronization is used. The exact latest manifest path is
printed and recorded locally in `uploads.jsonl`; there is no mutable remote pointer.
Old checkpoints remain usable. A receipt records a successful verification at its
capture time; it is not a continuous audit against later manual Drive edits.

Checkpoint preparation and upload take the collector's private-root lock. Run them
at startup or between completed collection phases, when no ingestion process owns
the root. Local preparation respects a 17 GB private-root ceiling and a separate
3 GB free-disk floor. The 20 GB project budget allocates up to 1 GB for tools and
repositories and preserves a 2 GB buffer. Those folders used about 0.66 GB when
measured on November 16, 2026, leaving about 0.34 GB for their growth; lower the
private-root cap if that overhead exceeds 1 GB. Catalog data is retained locally and is not audio spool
data to delete. Malformed ingestion journal fragments remain untouched, are counted
in manifest parse warnings, and never count as verified receipts.

## Prepare and upload

From the repository root in PowerShell:

```powershell
$EtPython = Join-Path $env:USERPROFILE 'et-channelers-tools\venv\Scripts\python.exe'
$EtRoot = Join-Path $env:USERPROFILE 'et-channelers-private'
$EtRclone = Join-Path $env:USERPROFILE 'et-channelers-tools\rclone.exe'
$EtCatalog = '.\et-channelers\pipeline\archive_catalog.py'

# Offline: read the saved full queue and the latest ingestion receipts.
& $EtPython -I $EtCatalog prepare --root $EtRoot `
    --queue (Join-Path $EtRoot 'jobs\queue_youtube_all_merged.csv') `
    --remote 'etdrive:04 Audio'
if ($LASTEXITCODE -ne 0) { throw 'Catalog preparation failed; upload has not started.' }

# Explicit upload: unchanged, previously verified objects are reused.
& $EtPython -I $EtCatalog upload --root $EtRoot `
    --remote 'etdrive:04 Audio' --rclone $EtRclone
```

Pass `--rclone-config <path>` only when using a separate configuration. No credential
values belong in commands, source files or catalogs. Exit 75 means a Drive cooldown
or quota response; retain local files and resume after the recorded window. Other
ingestion errors return 3. Failed uploads do not publish a completion receipt and
never delete local catalog or media files.
The collector's persistent stop marker also prevents catalog network requests and
returns 130; the helper never clears it.

## Rebuild for analysis

Retain the printed manifest path. Retrieve that exact manifest and the objects it
names, preserving their `manifests/` and `objects/` relative directories. A complete
baseline plus the manifest's ordered delta list is sufficient; earlier superseded
channel-index files and manifests are unnecessary.

The standard-library reader verifies the manifest filename's SHA-256, then each
compressed object's byte count, SHA-256 and MD5 before decompressing. It merges by
`video_id` with the last row winning and validates the resulting item count:

```powershell
& $EtPython -I $EtCatalog rebuild --root $EtRoot `
    --out (Join-Path $EtRoot 'analysis\youtube_archive_items.csv')
```

This defaults to the locally selected checkpoint. To reconstruct a particular
restored checkpoint, pass `--manifest <path-to-manifests/hash.json>`. Read the CSV
with Python's `csv.DictReader` or an analysis tool, then use each row's exact
`metadata_remote` to access its full metadata and `audio_remote` for later
transcription. Only `archive_state=verified_pair` means both artifacts have completed
the ingestion verification/deletion workflow. `downloaded_unverified` retains work
that still needs successful upload or verification.

Caption state is independent of audio state. `caption_state=unknown` means no caption
receipt is available. `none` means a completed discovery found no tracks under the
recorded policy, not that the video has no captions in any language. `pending` includes
source-access failures; `downloaded_unverified` retains work awaiting Drive proof.
`partially_verified` preserves proven tracks while others remain unresolved.
`verified_retained` means every selected track has Drive proof but the complete
receipt/deletion workflow has not finished; `verified` means that workflow completed
under the current policy.

`caption_bundles` is a compact JSON array of verified track identities, languages,
types, source formats, exact Drive paths, object IDs, byte counts and hashes. It
excludes local paths, request URLs, track names and transcript bodies. The JSON
`caption_languages` field counts selected tracks; `caption_verified_languages` counts
only tracks with valid artifact proof. `caption_inventory_status` preserves the
provider's discovery outcome; separate exclusion counts distinguish non-English
tracks, generated translations and non-caption items. Source-channel/tab summaries and manifest
counts distinguish videos with any verified track from fully completed caption
policies. Caption journal hashes and malformed-line counts are recorded separately
from audio journal provenance. Partial successes survive pending/error receipts,
and malformed fragments never establish absence or verification.

These additive caption columns preserve existing catalog checkpoints. The first
checkpoint after adding them may contain a delta for every item; earlier baseline
rows remain readable and are replaced by stable video ID in the normal merge order.

The module API is `prepare_catalog(root, queue, remote)` followed by
`upload_catalog(plan, drive)`, where `drive` is the existing `drive_ingest.Rclone`
adapter. `rebuild(manifest_path)` returns the verified, deduplicated rows. Catalog
publication is a checkpoint operation, not an upload after every media item.
