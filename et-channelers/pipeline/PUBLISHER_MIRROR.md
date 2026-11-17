# Publisher mirror batches

`publisher_mirror.py` consumes **already accepted, hash-bound private publisher
metadata**. It does not discover sources, open a browser, contact YouTube, export
cookies, mint tokens, select alternate clients, transcribe, or transcode.
The resource owner must validate publisher ownership and episode association
before creating its private plan. An associated YouTube ID is a relationship,
not proof that the publisher edition has identical content or bytes.

The initial implementation allows one or two I/O workers. Each item reserves its
approved maximum audio bytes plus caption/control headroom before requests.
There is no duration exclusion. It reuses the ingestion `Budget`, shared root
lock, Rclone batch uploader/hash verifier, full-packet audio probe and caption
normalizer. Managed roots must include private data, tools, repository checkouts
and the Playwright browser cache. The combined ceiling is 16 GB, including other
active owners' reserved growth, with at least 2 GB free disk. The ordinary
collector remains parked. Other owners must declare their growth reservations;
uncoordinated external writers are outside this process's accounting guarantee.

## Private inputs

The settings document supplies `root`, `plan_path`, `owner`, `lease_id`,
`managed_roots`, `remote`, `ffprobe`, `spool_cap_bytes`, and `workers` (1 or 2).
The immutable plan has `schema_version: 1` and an `items` array. Each item uses:

```json
{
  "provider": "Rumble",
  "channel_dir": "reviewed-channel",
  "associated_youtube_id": "abcdefghijk",
  "watch_page_id": "reviewed-watch-id",
  "declared_embed_id": "publisher-declared-embed-id",
  "association_method": "publisher_owner_title_date_duration",
  "association_qualification": "Qualified publisher mirror; edit identity remains unverified.",
  "exact_youtube_crossreference": false,
  "human_verified": false,
  "accepted_metadata": {"path": "accepted/publisher.json", "sha256": "<exact SHA-256>"},
  "allowed_hosts": ["<exact accepted public CDN host>"],
  "audio": {
    "url_pointer": ["ua", "audio", "<actual JSON key>", "url"],
    "maximum_bytes": 100000000,
    "metadata_declared_bytes": 50000000,
    "codec": "aac", "extension": "aac", "duration_seconds": 2105
  },
  "captions": [{
    "track_id": "en-auto", "provider_language_key": "en-auto",
    "provider_label": "English (auto)", "language": "en",
    "kind": "automatic_original", "translated": false,
    "raw_format": "vtt", "url_pointer": ["cc", "en-auto", "path"],
    "maximum_bytes": 4000000
  }]
}
```

Values above are illustrative, not an admission. Maximum audio bytes must come
from the resource owner's accepted format estimate and explicit headroom. JSON
pointer elements are literal object keys or integer array indexes, not strings
to execute. The accepted JSON itself stays private. Transport URLs are read
from it into memory; persisted provenance removes URLs, credentials and paths
while retaining the remaining public metadata. Captions are restricted to
publisher-provided English or original English automatic tracks, never machine
translations. No caption inventory is represented by an empty array; the caller
must not confuse unavailable discovery with a confirmed empty inventory.

`sync/publisher_mirror_lease.json` requires `state: "active"`, matching
`owner`, `lease_id`, `worker_sha256`, `plan_sha256`, `remote`, `managed_roots`,
`max_workers`, `spool_cap_bytes`, and a future `expires_at_epoch`.
`sync/analysis_resource_plan.json` must contain one matching active reservation
with `max_bytes >= spool_cap_bytes`, `accounting_cap_bytes <= 16000000000`, and
`collector_dispatch_allowed: false`. `sync/STOP_DRIVE_INGEST` must remain present.
`sync/STOP_PUBLISHER_MIRROR` stops this separate lane; it is never auto-removed.

```powershell
python -I et-channelers/pipeline/publisher_mirror.py plan --settings <private-settings.json>
python -I et-channelers/pipeline/publisher_mirror.py run --settings <private-settings.json> --rclone <rclone.exe>
```

## Proof and recovery

Downloads use ordinary HTTPS GET with no proxies or headers copied from a browser.
Only exact accepted hosts and bounded same-host allowlist redirects are allowed.
A full HTTP 200 response requires identity encoding, no Content-Range, positive
Content-Length within admission, exact EOF length, incremental SHA-256/MD5, then
one full-packet `ffprobe` audio/codec/duration check. Published size estimates are
retained as estimates; a valid exact transport length may differ within the
owner's approved maximum. Caption ZIPs retain raw captions, normalized cues/text,
provenance and member hashes. Cue-union duration is not every-word coverage.

Completed downloads, their probe results and completed upload artifacts resume
without another source request. Partial/ambiguous transfers remain held for
review; this first version deliberately implements no Range resume or automatic
source retry. A 403/429 sets a 24-hour breaker for that exact provider and endpoint
category (`audio` or `caption`). Active calls in that scope stop at their next
guard; unrelated providers and the other category remain independently eligible.
The two-worker global limit and YouTube state remain unchanged. Valid completed
audio still uploads if a caption fails, with explicit `caption_state: pending`.
That pending state requires a separately admitted future caption backfill; the
first version does not silently re-request a refused caption. Exit 3 reports
held items or pending captions.

Scoped deadlines are stored in `sync/publisher_mirror_source_cooldowns.json`;
the separate refusal journal records provider/category, accepted metadata and
request-binding hashes, never transport URLs. The old singular
`publisher_mirror_source_cooldown.json` remains a global hold unless its exact
bytes are explicitly scoped by an owner-authorized
`publisher_mirror_legacy_scope_binding.json`. That binding must prove the original
deadline and audio-only failure through immutable state, plan and accepted
metadata hashes. Missing/stale proof keeps the global hold. The old file is never
rewritten, its deadline is not shortened, and this mechanism does not retry the
failed request.

One `copy_batch` and one exact `stat_batch` verify each item's named artifacts.
All Drive IDs, sizes and MD5s must match before the fsynced publisher journal and
local receipt are written, and before any owned deletion. Normal-path streamed
hashes are reused only while local fingerprints remain unchanged. Recovery
rehashes retained files, rechecks remote proofs if cleanup was interrupted, and
never deletes changed or out-of-spool paths. Already complete matching receipts
skip source, probe and Drive work.

The publisher-specific probe also accepts MP3. Raw ADTS AAC uses a complete
header walk only after `ffprobe` confirms AAC-LC: every frame must contain one
raw-data block, retain the same sample rate/channel configuration, fit completely
before EOF, and agree with the probed packet count. Its duration is the sum of
those 1,024-sample frames, not the raw-AAC bitrate duration estimate. The estimate
and its difference are preserved separately. Unsupported framing/profile or a
count disagreement is held. The existing native YouTube probe is unchanged.

## Explicit RSS references and language scope

A publisher RSS item with an explicit YouTube source reference may instead use
`association_method: publisher_rss_exact_youtube_id`,
`exact_youtube_crossreference: true`, `human_verified: false`, and its actual
`original_youtube_link`. The link must be a public HTTPS YouTube watch/share URL
whose video ID equals the associated ID. Its receipt kind is
`publisher_mirror_audio_variant`; the link is deliberately retained in association
provenance and the journal. This is the sole source-link exception to URL removal.
It establishes an explicit publisher reference, not identical edits or bytes:
`recording_equivalence_verified` remains false. Qualified items retain the earlier
kind and association policy. MP3 uses `codec: mp3` and `extension: mp3`.

When a published transcript has only an English RSS channel declaration, its
plan must preserve that weaker scope: `language: en-US`, `kind: published`,
`language_basis: publisher_rss_channel`, `track_language_verified: false`,
`translated: null`, and `translation_status: not_declared`. The publisher's human
versus automatic origin remains unspecified. These fields survive into caption
provenance and receipts. This selects the original publisher-provided transcript
pointer without requesting a translation; it does not independently verify the
track's language or origin. Explicit translation requests remain rejected.

An observed HEAD redirect may inform an owner-approved exact-host allowlist.
A HEAD refusal remains distinct from a GET result. No unknown redirect host is
invented or automatically admitted, and acquisition still requires a new valid
owner lease and stops on its own HTTP refusals.

Remote objects use
`<archive>/<channel>/Videos/<associated-ID>/PublisherVariants/<audio-SHA>/`:
`publisher-audio.<ext>`, `provenance.json`, and
`Captions/<bundle-SHA>/captions.zip` for each track.
`sync/publisher_mirror_manifest.jsonl` preserves the original
`kind: qualified_publisher_mirror_audio_variant`, `status: verified`, source
association fields and `audio`/`provenance` proofs. It adds `caption_bundles` and
keeps the original `caption_bundle` alias when exactly one bundle exists.
`native_youtube_bytes` and all three `changes_native_*_count` flags remain false.
This module never writes the native audio, caption or ASR completion ledgers.
