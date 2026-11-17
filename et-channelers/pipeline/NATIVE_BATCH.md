# Explicit native-audio batch

`native_batch.py` coordinates at most two isolated Windows child processes using
the installed, pinned stock headful WPC provider and upstream yt-dlp/HttpFD in one
live `YoutubeDL` context per item. It uses explicit original-track evidence or the
separately labeled legacy inference below, preserves
upstream availability/header behavior, prefers original HTTPS AAC/m4a when
available, and otherwise selects original HTTPS audio. There is no provider,
client, account, cookie-profile, proxy, or transport fallback. Importing any of
these modules starts no work.

This is a separate admission profile, `stock_headful_wpc_native_batch_v3`.
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
  Object helper, `native_track_policy.py`, `native_metadata_snapshot.py`,
  `drive_ingest.py`, `media_metadata.py`, `native_audio_sink.py`,
  and the exact installed WPC/extractor/runtime dependencies selected by owner.
- `preserved_controls`: nonempty `{path,sha256}` snapshots of the legacy STOP
  and refusal controls that must remain unchanged. Do not include the canonical
  audio journal, which this workflow intentionally appends after verification.

The owner creates `sync/stock_wpc_batch_v3_lease.json` with `schema_version:1`,
`state:"active"`, `authorized:true`, `source_scope_authorized:true`, exact
`profile`, `owner`, `lease_id`, `settings_sha256`, `plan_sha256`,
`worker_sha256`, `coordinator_sha256`, `max_workers`, `spool_cap_bytes`, `remote`,
`expires_at_epoch`, and `preserve_existing_cooldowns:true`. The resource ledger
must contain its matching active reservation, a managed ceiling no higher than
16GB, and `collector_dispatch_allowed:false`; `STOP_DRIVE_INGEST` stays present.
This explicit source scope is an owner decision, not a tool-generated override.
Version 3 uses `sync/STOP_STOCK_WPC_BATCH_V3` and
`sync/stock_wpc_batch_v3_source_cooldown.json`; the shared spool and byte budget
are unchanged. Its settings pin the original version 2 STOP and cooldown files
as preserved history. The prior observation is retained, not silently cleared or
rewritten. A separate owner admission must bind the corrected scope and exclude
the previously spent attempts.

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

Python downloader HTTP403/429, browser source-control HTTP403/429, bot checks,
or explicit protection failures stop this batch's source dispatch and cancel
siblings. A new scoped 24-hour refusal record and `STOP_STOCK_WPC_BATCH_V3` are
written without altering legacy history. Stock WPC opens the homepage; its
unbound browser media HTTP403/429 events remain counted diagnostics and are not
attributed to the selected target or used as a target-media breaker. Browser
source-control refusal still stops even without a verified video binding.
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
representation, and no track labels, audio language, default/dub/descriptive/
secondary indications, DRC/voice-boost flags, track tags, DRM alternatives,
duplicate base itags or conflicting returned-client inventory. Context-only
initial caption data and caption translation-language lists are not audio-track
evidence. The observation preserves original objects/callbacks and sends no
additional requests.

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
