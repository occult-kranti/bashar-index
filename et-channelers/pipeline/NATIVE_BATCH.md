# Explicit native-audio batch

`native_batch.py` coordinates at most two isolated Windows child processes using
the installed, pinned stock headful WPC provider and upstream yt-dlp/HttpFD in one
live `YoutubeDL` context per item. It uses explicit original-track evidence or the
separately labeled legacy inference below, preserves
upstream availability/header behavior, prefers original HTTPS AAC/m4a when
available, and otherwise selects original HTTPS audio. There is no provider,
client, account, cookie-profile, proxy, or transport fallback. Importing any of
these modules starts no work.

This is a separate admission profile, `stock_headful_wpc_native_batch_v4`.
It does not resume old collectors, clear old cooldowns, or reuse a spent attempt.
It is initially limited to an immutable plan of at most 20 items. Native audio
and canonical pair counts remain distinct from publisher editions and ASR.

## Inputs and launch

The private plan contains `schema_version:1` and `items`, each with `video_id`,
`channel_dir`, `tab`, exact public `video_url`, `duration_seconds` (positive or
null), `queue_row`, and `queue_row_sha256`. The latter hashes sorted compact
UTF-8 JSON with non-ASCII characters preserved and one LF. No duration ceiling
or language exclusion applies. Source extraction must establish a positive
duration; a known plan duration must agree within the existing tolerance.
Currently live/upcoming media are held. Ended `post_live` streams are eligible
when a complete original audio format is actually available.

Settings JSON fields:

- `private_root`, `plan_path`, `pipeline_directory`, `python_executable`.
- `owner`, `lease_id`, `remote`, `rclone`, optional `rclone_config`.
- `workers` (1 or 2), `max_asset_bytes` (up to 2,000,000,000),
  `spool_cap_bytes` (up to 6,000,000,000), `job_wall_seconds` (600–7200).
- Exactly six disjoint `managed_roots`, including private data, project tools,
  all three project checkouts, and the task-owned `ms-playwright` cache.
- `browser_executable`: the owned stock Chromium executable; `plugin_directory`
  and `wpc_copy`: the private filtered directory containing only the unmodified
  pinned WPC plugin; `ffprobe` and `ffmpeg`: existing local tools.
- `code_pins`: `{path,sha256}` for dependencies, including worker, quality, Job
  Object helper, `native_track_policy.py`, `xtags_decode.py`, `native_metadata_snapshot.py`, `native_http_policy.py`,
  `drive_ingest.py`, `media_metadata.py`, `native_audio_sink.py`,
  and the exact installed WPC/extractor/runtime dependencies selected by owner.
- `preserved_controls`: nonempty `{path,sha256}` snapshots of the legacy STOP
  and refusal controls that must remain unchanged. Do not include the canonical
  audio journal, which this workflow intentionally appends after verification.
- `http_policy_seed` and `historical_http_review`: immutable `{path,sha256}`
  proposals. The review contains exactly `covered_event_ids` and
  `allowed_video_ids`; its allowlist must equal this plan's IDs.

The owner creates `sync/stock_wpc_batch_v4_lease.json` with `schema_version:1`,
`state:"active"`, `authorized:true`, `source_scope_authorized:true`, exact
`profile`, `owner`, `lease_id`, `settings_sha256`, `plan_sha256`,
`worker_sha256`, `coordinator_sha256`, `max_workers`, `spool_cap_bytes`, `remote`,
`expires_at_epoch`, `preserve_existing_cooldowns:true`, `http_policy_seed_sha256`,
`historical_http_review_sha256`, and `historical_http_review_authorized:true`.
The resource ledger
must contain its matching active reservation, a managed ceiling no higher than
16GB, and `collector_dispatch_allowed:false`; `STOP_DRIVE_INGEST` stays present.
This explicit source scope is an owner decision, not a tool-generated override.
Version 4 uses `sync/STOP_STOCK_WPC_BATCH_V4` and
`sync/stock_wpc_batch_v4_source_cooldown.json`; the shared spool and byte budget
are unchanged. Its settings pin the original version 2 and 3 STOP/cooldown files
as preserved history. The prior observation is retained, not silently cleared or
rewritten. A separate owner admission must bind the corrected scope and exclude
the previously spent attempts.

The owner seeds `sync/stock_wpc_batch_v4_http_state.json` once as
`{schema_version:1,seed_sha256,state:<immutable seed contents>}`. Subsequent
batches reuse this state; they never replace it with an empty ledger. Seed
events must remain byte-equivalent data in every later state. The historical
selected-media403 retains unknown final-response binding, its original event
time and permanent item quarantine. Only the separately hash-bound owner review
can permit the exact other plan IDs; it cannot authorize that held item or
discount any new global event. Preparing a review does not authorize execution.

After that admission, the owner can run:

```powershell
python -I et-channelers/pipeline/native_batch.py --settings <private-settings.json> --execute
```

There is no default execution or source action on `--help`. Child launch attaches
a Windows Job Object before writing GO. Cleanup stops only that owned tree;
personal Chrome is not discovered or touched.
After the Job Object proves no owned processes remain, profile deletion gets at
most three filesystem-only attempts. A still-locked profile is retained and
continues to count against storage. Its bounded exception type/errno/WinError is
recorded separately from the first parent failure; a directory lock is not a
YouTube refusal. Uncertain process cleanup still stops new dispatch. Storage
admission is checked before another child starts, including retained profiles.

## Bounds and stopping

Audio uses a hard pre-write per-file cap. At most two children reserve their
audio cap plus 240MB each for profile/metadata/control overhead. The shared spool
ceiling is explicitly admitted per run, up to 6GB; all six roots and other active reservations count against 16GB,
with at least 2GB free disk. Existing `Budget` reservation checks use a partitioned
snapshot: each active child folder is excluded from the filesystem walk and
charged its full reserved slot, while inactive and retained files are counted
once. Browser writes therefore cannot be counted twice across scans. Each
child's actual folder/profile limits remain checked separately. Retained bytes
can reduce concurrency to one worker; another slot waits before any source
attempt is spent. A capacity failure retains its numeric snapshot in the parent
audit. Oversize media are held for a larger reviewed
reservation, never excluded by duration. There is no Range-resume/redownload of
held attempts.

Each child limits Python-returned body bytes to its audio cap plus 100MiB and
wire requests to `ceil(audio_cap/8MiB)+32`, with zero ordinary retries and 2MiB/s
download pacing. Browser request counts (256 observed) and its 150MB profile
limit are observed stop targets, not a claim of hard all-target browser network
or disk interception. Bootstrap is bounded to 90s; the owner supplies the whole
job deadline. Parent/child lease and cancellation checks run at least once per
second while progressing; parent monitoring can terminate blocked children.

Every HTTP429, browser source-control403, bot/protection failure and unbound
Python403 stops source dispatch and cancels siblings. A Python403 is item-only
when a validated selection's exact URL equals both the outgoing GET request
and final error-response URL, in the native transfer phase on a media endpoint.
These comparisons use memory only; URLs, credentials and raw headers are not
persisted. Redirects or missing final binding remain global. Safe proof records
include booleans, format identifiers and bounded parsed Retry-After information.
The failed child always stops; no alternate URL, format, client or retry follows.

An exactly bound media403 permanently quarantines that video while other
admitted resources may continue. Three distinct media403 IDs in600seconds latch
a shared global breaker. A reviewed historical403 counts conservatively in its
actual time window without claiming verified binding. The threshold is an owner
policy, not a provider claim. Events deduplicate by immutable attempt identity;
success, later batches and elapsed time do not clear quarantines or a latched
global stop. The coordinator atomically fsyncs policy state under its dispatch
lock and reads pending child failures immediately before authorizing GO.
Worker capture timestamps survive replay; missing timestamps hold for review.
The first HTTP observation is retained separately from a later global HTTP or
bot/protection escalation, so an earlier item403 cannot mask a stronger stop.
A global event writes a scoped cooldown (at least24hours and no earlier than a
parsed server delay) and `STOP_STOCK_WPC_BATCH_V4`, without altering old controls.

Stock WPC opens the homepage; its unbound browser media403 events remain counted
diagnostics without selected-video attribution. Unbound browser media429 is
global. Browser source-control refusal still stops without a video binding.
Requested video ID labels the attempted scope; it does not prove a homepage
refusal occurred on that watch page. Completed pairs can still upload. No
automatic source retry occurs after an attempt folder exists.

## Completion, quality and recovery

Before the format selector runs, an allowlisted scalar format inventory is
fsynced (up to512 representations with an explicit truncation flag). It records
format/language/original-label evidence without URLs, tokens, headers or raw
errors. Bounded exception chains retain only finite class/code/errno/WinError
values and module/function/line locations, including wrapped downloader errors;
raw messages, locals, URLs and tokens are never recorded. Finite anchored errors distinguish unavailable format, live deferral,
and explicit access checks. This normalized diagnostic inventory alone cannot
support a legacy inference or retrospectively explain older held attempts.

A read-only wrapper also observes `_extract_formats_and_subtitles` before the
pinned extractor filters URL-less or SABR representations. A second policy
branch is eligible only when the complete returned mweb audio-bearing inventory
has valid target/playability, valid untruncated arrays, at least one audio
representation, and no semantic track labels, audio language, default/dub/
descriptive/secondary indications, voice-boost flags, unknown track tags, DRM
alternatives or conflicting returned-client inventory. Normal base itags must
be unique. An explicit DRC counterpart is permitted only under the narrow
decoded-processing rule below; it cannot be selected. Context-only
initial caption data and caption translation-language lists are not audio-track
evidence. The observation preserves original objects/callbacks and sends no
additional requests.

Top-level `xtags` and transport query projections use different encodings.
The bounded `xtags_decode.py` decodes top-level FormatXTags protobuf and parses
the URL/cipher query projections independently. An explicit `isDrc:true` row
may be recognized as processing-only only when every present projection is
valid and contains exactly the known `drc=1` pair, with a matching unique normal
itag/codec base. Malformed, duplicate, unknown, compound or semantic tags hold.
Declared semantic fields remain evidence even when their value is false;
`isOriginal:false` is not treated as absence. DRC-only catalogs and ambiguous
duplicates hold. Only the non-DRC representation can pass transfer selection.
The decoder is an exact required code pin; importing it performs no I/O.

Only that branch permits a normalized unlabeled preference-1 format, bound to
the exact raw audio-only itag, codec and known source size. Codec/bitrate
representations such as139/140/251 do not themselves imply multiple tracks.
Preference5/default is never treated as original. Labeled multitrack responses
continue to require preference10 and an explicit original label. Missing raw
inventory cannot be replaced by normalized-format guesses. The selector uses
`language_preference<0` because the installed parser treats `=-1` as a string;
the pre-transfer gate still requires exactly numeric -1, the same raw itag and
codec, and equal positive known raw/normalized byte sizes. Missing sizes hold.
The extractor can copy subtitle language into normalized audio formats. That
normalized language is ignored as audio evidence only in the complete raw-bound
legacy branch, and all emitted source-audio language fields remain null.

The accepted legacy provenance says
`origin_basis:provider_single_legacy_track_inference`, `origin_inferred:true`,
`original_explicitly_verified:false`, and `source_language:null` with status
`unknown`. Metadata audio language remains null; no voice/original-language
claim is made. Completeness describes the parsed returned-client arrays, not
proof of a provider-global inventory. Language-ID/ASR admission remains a
separate decision.

Sanitized selected metadata is fsynced before the media request. Exactly one
matching native finished callback, equal streamed/final byte counts and no
partial file are required before a post-download `MaxDownloadsReached` sentinel
can be treated as completed transport. MD5/SHA256 are computed during writes.

One complete ffprobe packet scan must establish one native audio stream and the
expected extent. Clean probe output is labeled `complete_native_audio`, with
speech accuracy unreviewed and no full-decode claim. The only codec-warning
exception is exactly one `Error parsing Opus packet header.` line: exact selected
source size, positive packet count, source/container extent within 2s, and one
successful full single-thread decode ending within 2s of both are additionally
required. Other warnings/errors hold. Accepted exception output is explicitly
`complete_with_codec_warning`, `clean_decode:false`, and
`strict_probe_passed:false`. Existing native sink policy is unchanged.

Canonical upload reuses exact-pair `Rclone.copy_pair`, batched named-object
stat/MD5/size plus distinct Drive IDs, and `verify_and_delete(require_metadata=True)`.
The canonical verified journal precedes deletion. After an immutable pair-copy
conflict, the exact remote audio must match before the metadata helper may move
old canonical metadata to its content-addressed `MetadataSnapshots` path.
The move preserves and verifies its Drive identity, size and MD5; durable
lineage precedes the new canonical metadata upload. Existing differing audio is
never moved or overwritten. Ambiguous objects or dependencies remain held.
Stored quality/provenance are included in the
sidecar and receipt. The new batch journal contains only safe scalar proof.

Resuming skips complete canonical receipts without source calls. Complete local
results and prepared records are uploaded without another source request; an
interrupted verified deletion rechecks the exact remote pair. Changed/untrusted
resumed local files are hashed once by the shared verifier. Held/partial/spent
source attempts are retained and never silently restarted. Captions and ASR are
separate consumers of the canonical metadata/audio; this pilot does not claim
their completion.

Optional `asr_handoff` settings bind `owner`, `lease_id`, `cap_bytes` (at most
1 GB), `max_pairs` (at most three), `retain_policy:
explicit_original_english_v1`, and `capacity_wait_seconds` (1–1800). An optional
`caption_bundle_paths` map is keyed by video ID, then track ID, with private
cached ZIP paths. The helper, queue, and model-provenance files must be pinned;
the separate handoff lease and resource reservation must already be active.
The initial successor uses a 500 MB allowance while another ASR frame drains.

After exact Drive pair proof, the helper retains English audio/metadata hardlinks
before collector cleanup. Only explicit original-English evidence enables this
route; inferred or foreign language produces a disabled metadata-only review
without occupying a staging slot. A correctly bound, cached usable English
caption can suppress ASR; unbound publisher text cannot. Missing or unproven
caption coverage remains explicit and does not disable the English handoff.
Readiness is finalized only after the canonical receipt is durable. The caller
merges fingerprints refreshed after link creation to avoid redundant hashing.
A bound local marker recovers a lost readiness acknowledgement without source
requests. The consumer takes only its separate ASR lock, never the collector's
lifetime lock.

Full staging waits locally before further dispatch. On bounded timeout or an
oversized input, the original files remain and future dispatch pauses; existing
workers are not cancelled merely because staging is full. No HTTP cooldown is
created or cleared. A later owner-approved continuation can finish the local
handoff without redownloading the source.

Control writes use unique same-directory temporary files and fsync before
replace. Windows sharing/access-denied errors 5/32/33 receive at most six local
replace attempts with 775 ms total backoff. Progress snapshot/commit is
serialized, and the first sanitized failure and retry counters remain in
diagnostics. Exhausted or unrelated errors fail as `control_write_failed`;
uncertain final-result writes never count as success.

## Upload overlap and diagnostic successor

The reviewed successor refills a free source slot before synchronously publishing
a dequeued completion. It retains at most two tracked source futures and two
queued completions, with one canonical writer. Pending futures consume virtual
slots until actual child reservations exist, so the parent cannot promise the
same free bytes twice. Retained completed files remain charged. Source stops,
Drive cooldowns, staging pauses and insufficient capacity prevent refill.

Raw inventory rows add allowlisted label field/key categories and classify at
most eight tag projections independently across top-level, URL, cipher and
cipher-URL origins. Equality and `all_exact_drc_only` are observation flags;
they contain no URL/query values and do not change admission. Incomplete,
opaque or compound tags remain unresolved. A separately admitted metadata-only
review completed before selection with no audio output. Its original aggregate
enum could not distinguish duplicated projections; the corrected diagnostics
will collect that evidence from fresh admitted targets, without repeating the
held target. Normal browser bootstrap remains observable network activity.

## Proven decoded-format recovery

After primary-schema review and a separate exact admission, one full-native
trial validated 13 audio-bearing representations, including six DRC counterparts
whose tags decoded as processing-only. It selected normal AAC and archived
10,339,840 bytes / 638.850612 seconds / 27,513 packets after strict probe and
paired Drive verification. No re-encoding or source-language upgrade occurred.
The original metadata-only trial and failed attempts remain preserved. See
[protocol evidence and limits](../research/decoded-native-audio-formats-2026-11-18.md).

This repair does not grant recovery of old holds or change HTTP refusal policy.
At the November 18 00:05 UTC snapshot, the 40-target source continuation and
separate 42-input English consumer are active under their own amendment. The
healthy consumer publishes one valid input per process; the retained
word-alignment/segment-timing-error item is excluded. The separate 30-item DRC
recovery and finite campaign remain disabled pending exact review.
