# Native audio byte sink and local gateway

The first actual automated Chromium trial reached 1,133,713 bytes / 69.892 seconds
and held before EOS; no complete native artifact or Drive upload was established.
Its partial and spent admission are retained. The receiver is now stopped for
offline diagnostic changes. See the [investigation record](../research/native-audio-investigation-2026-11-17.md).
Importing either module starts no server, browser, source request, Drive operation,
codec process or GPU work. It does not use MediaRecorder or playback capture.
A real one-worker, one-full-file acceptance is required before the owner may admit
up to four source leases. A matching explicit lease is required for any new work.

`native_audio_sink.py` owns bounded files, proof and deletion. The accepted
browser context owns transport. `native_audio_gateway.py` provides the thin
loopback bridge; `browser_sabr_adapter.mjs` provides the separate browser-side
SABR parser. Media URLs, cookies, PO tokens, player config and browser profiles remain
in the browser. The gateway rejects transport/session fields. The metadata
sidecar retains sanitized public research metadata and the complete safe format
identity; it never relabels re-encoded playback as native audio.
The sole input URL exception is `metadata.thumbnails[index].url` on HTTPS
`*.ytimg.com`, without userinfo, port, query or fragment. The same URL at another
path is rejected; temporary media endpoints remain forbidden.

## Admission and resource ownership

The existing `sync/drive_ingest.lock` prevents concurrent conventional ingestion.
The collector remains parked by its existing STOP marker. The new
`sync/STOP_NATIVE_BATCH` requests a stop and is never removed automatically.
Only exact IDs in the hash-bound private queue can begin. Completed native pairs
already in the canonical journal are skipped.

The owner must create `sync/native_batch_lease.json` with these fields:

```json
{
  "state": "active",
  "owner": "<assigned owner>",
  "lease_id": "<new lease ID>",
  "expires_at_epoch": 0,
  "worker_sha256": "<native_audio_sink.py SHA-256>",
  "queue_sha256": "<exact private queue CSV SHA-256>",
  "managed_roots": ["<private root>", "<tools root>", "<repository>", "<other managed checkout>"],
  "remote": "<exact audio archive root>",
  "native_encoded_audio_only": true,
  "spool_cap_bytes": 8000000000,
  "max_workers": 1
}
```

The zero expiry above is deliberately invalid. The existing shared resource
plan also needs one active reservation with this lease ID/owner and sufficient
`max_bytes`. The implementation counts actual managed files, outstanding full
file reservations, metadata/proof overhead, and other owners' reserved growth.
It enforces the smaller admitted spool cap (at most 8 GB), total managed cap
(at most 16 GB), and at least 2 GB of free disk. Roots must include private data,
the running environment, this repository and every owner-declared managed root.
Existing models/tools are counted even while idle. No duration or 100 MB item
limit is imposed; an item that cannot fit is deferred.

Increasing `max_workers` above one additionally requires
`sync/native_single_worker_acceptance.json`: the resource owner's explicit
approval, the exact worker SHA, and the complete canonical deleted-pair receipt
under `receipt`. It must equal the durable journal entry. A fake count or a local
file alone cannot satisfy this gate. The owner, not this worker, issues approval.

Existing YouTube audio cooldowns remain enforced by default. The only optional
exception is the resource-owner-approved policy below, for one materially
different browser-context SABR attempt. Any 403, 429 or bot block stops
all source writes, invokes the batch-abort callback, and durably preserves a
minimum 24-hour/new-provider deadline without shortening an existing one.
Locally completed files may still finish verified Drive upload.

The optional root-lease `pilotPolicy` has this exact shape; it is inactive unless
the owner supplies real code hashes and a future expiry of at most one hour:

```json
{
  "kind": "accepted_chrome_sabr_single_fullfile_v1",
  "approvedByResourceOwner": true,
  "targetVideoId": "EliqxbbQoRw",
  "transportKind": "sabr_reassembled",
  "acceptedContext": "normal_user_chrome",
  "maxAttempts": 1,
  "createdAtEpoch": 0,
  "expiresAtEpoch": 0,
  "expectedDurationMs": 1570961,
  "durationToleranceMs": 150,
  "maxOutputBytes": 64000000,
  "sourceRequestBudget": 1000,
  "bindFirstValidatedHash": true,
  "codePins": {
    "sdk": {"path": "<managed SDK bundle>", "sha256": "<reviewed SHA-256>"},
    "observer": {"path": "<managed observer source>", "sha256": "<reviewed SHA-256>"},
    "adapter": {"path": "<managed source adapter>", "sha256": "<reviewed SHA-256>"}
  }
}
```

This policy also requires `max_workers=1`, published-original track evidence,
audio-only/no-DRM identity, and exact target/duration/code agreement. Before any
source request, `begin` atomically spends its sole attempt and binds the complete
selected-format hash in `sync/native_context_pilot_attempt.json`. A second begin,
wrong hash, changed code, expired policy or additional worker fails closed.
Every source fetch must first spend an authenticated request permit. A lost
permit ACK cannot be blindly retried. Source requests are capped at 1,000;
the root can choose smaller budgets. The old STOP marker and rejected-lane
deadlines/counters remain preserved. A new refusal always defeats the exception.
This is not a general cooldown bypass, a four-worker exception or permission to
reset the attempt file.
`acceptedContext` accepts exactly `normal_user_chrome` or
`automated_dedicated_chromium`. The chosen value is bound to the job at admission
and recorded under `native_acquisition.provenance.context_kind`, with the lease
policy as its stated basis. Changing context during the same attempt is rejected.
No profile paths, cookies or browser session material enter this provenance.

### One separate diagnostic follow-up

After the actual v1 trial held before EOS, the owner may admit exactly one
`accepted_chrome_sabr_diagnostic_followup_v2` policy. It retains the same target,
format binding, context, destination and queue. It requires changed SDK **and**
adapter hashes and a `parent` object with `leaseSnapshot`/`codeSnapshot` file
path+SHA pairs plus `attemptSha256`, `jobStateSha256`, `segmentLedgerSha256`
and `partialSha256`. Every parent file stays inside the private root. The code
snapshot contains immutable copies of all five v1 worker/gateway/SDK/observer/
adapter files, each matching the original lease.

The v1 parent must be retained for a protocol failure, with one spent attempt,
matching binding and valid partial proof. A source refusal, altered parent,
unchanged diagnostic code, third lineage or replay is rejected. The new spend
is written to `sync/native_context_pilot_followup_v2.json`; the v1 receipt is
never reset or overwritten. The exact parent alone is excluded from active
source-slot conflicts. Its bytes and reservation continue to count. A fresh
refusal updates only the current lease's jobs and preserves the parent intact.

The diagnostic build exports a validated, at-most-16-event/16-KB numeric,
boolean and enum summary to extension session storage. It classifies underlying
SDK errors without exporting their raw messages. It records protection status,
request playhead/buffer progress, policy/seek/reload and format events; HTTP 200
is not itself classified as successful protocol acceptance. This follow-up does
not authorize a general retry loop or parallel batch collection.

### One change to the normal Chrome context

`accepted_normal_chrome_context_followup_v3` is restricted to the proven
automated-v2-to-normal-Chrome transition, with one attempt and
`maxContextFollowups=1`. It keeps the same target, full format, queue,
destination and reviewed v2 SDK/observer/adapter hashes. The parent additionally
requires `diagnosticSnapshot: {path,sha256}` proving the observed SDK stall,
pending protection and correct playhead/format. Both earlier lineage chains
are rechecked and counted in storage; neither is modified or resumed.

`normalPlaybackEvidence: {path,sha256}` binds the owner's existing playback
report and its exact private statement. It is explicitly typed
`user_reported_normal_chrome_playback`, never collector-observed continuous
playback. The media provenance contains the evidence hash and basis, not the
statement or local paths. The fixed new spend receipt is
`sync/native_context_normal_chrome_attempt_v3.json`; replay or another lineage
is rejected. The live source identity/permission guard still runs at activation.

The owned status page offers read-only **Check target tab**, idle-only
**Reload helper**, and **Start admitted native trial**. Start repeats the exact
single-target and actual granted-host-permission checks, then pairs with the
receiver before injecting the unchanged native runtime. Only messages from
this extension's exact status page can invoke these controls. The validated
protocol report is available for scoped UI automation without CDP, exported
profiles or cookies. The controls do not auto-start source work.

### Repaired acceptance gate: v4

`accepted_browser_sps1_repair_v4` is one separately recorded observation session
and at most one native source attempt. The owner chooses an exact existing
browser-context enum. Its observation receipt must match that context; only one
leaf trial, v3 or v4, is admitted. V4 preserves both earlier spent ancestors and
the unspent v3 admission snapshot, requires changed SDK/observer hashes with
the same adapter, and rejects later replay. All retained storage still counts.

Before browser launch the owner records one observation session in
`sync/native_context_sps1_observation_v4.json`, hash-bound by the policy. Before
BEGIN, `metadata.native_source_acceptance` must contain exactly the reviewed ten
safe fields: basis, HTTP/SPS status, complete-response flag, video identity,
same-video/configuration/catalog flags, UTC timestamp and independent UUID.
SPS1 must be fresh and tied to this session. Missing/pending/rejected acceptance
spends no native attempt. A successful BEGIN binds the proof in
`sync/native_context_sps1_repair_v4.json`; it cannot change during the job or
at finish, and is preserved in `native_acquisition.source_acceptance`.

The passive observer adds no source request, preserves original player bodies,
and skips media while parsing the matching ordinary response. A pre-BEGIN
refusal still stops source work and must be durably recorded by the resource
owner; it is not a failed file download. No time, format or Drive validation is
waived by SPS1. The latest isolated trial received SPS3 before BEGIN and created
no native output or source attempt; full-file access remains unproved.

## Transport identity and completion

The adapter identity has exactly `videoId`, `itag`, `lastModified`, `xtags`,
`mimeType`, `codec`, `contentLength`, `durationMs`, `language`, `originalBasis`,
`trackId`, `noDRM=true`, and `audioOnly=true`. It is SHA-256 hashed as compact
sorted-key JSON, with nulls retained. Duration and byte counters are safe
integers. The separate `transportKind` is preserved and must also match resume
state. Original-track evidence is mandatory; the browser adapter must establish
it from the published selected format, not infer it from a missing track flag.

- `direct_http`: reserve the exact `contentLength`; the finished native file
  must match it. A resume must rehash the durable prefix and match the entire
  format identity, then prove HTTP 206 with the exact offset and total.
- `sabr_reassembled`: reserve an explicit `outputBudgetBytes`. Format
  `contentLength` is source metadata, **not** an emitted-file length assertion.
  Record `container_reassembled=true` and `encoded_audio_not_reencoded=true`.
  The original container's whole-file byte identity is not claimed.

SABR accepts only strict VOD with `isLive=false`, no duplicate-init stripping,
and one positive-length initialization segment numbered zero followed by
contiguous media segments. Every segment has exactly:

```text
number, initialization, startTimeMs, endTimeMs, declaredBytes,
byteOffset, emittedBytes, sha256, initDiscardedBytes
```

Declared and emitted byte counts must match, init-discard count must be zero,
and the sink rereads every segment's byte range to verify SHA-256. Boundaries
must agree within 250 ms; final duration must agree within the greater of two
seconds or 0.2%. The final EOS, sequence, total bytes, media end and segment
hash-chain must all agree. The complete segment proof is streamed into the one
metadata sidecar, so long recordings do not require an unbounded finish JSON
or an extra Drive object. Proof overhead receives its own storage admission.

Both transports require a full-file SHA-256/MD5 pass and `ffprobe` full packet
scan proving one audio stream, no video, the selected codec, positive packet
count and source duration within tolerance. This is packet/container validation,
not human speech coverage or decoded waveform accuracy. No ASR or re-encoding
runs here. A saved arbitrary SABR snapshot cannot authorize resume; ordinary
SABR `verify_resume` fails closed.

## Gateway contract

The server binds only `127.0.0.1`, default port 8781. Every request must use the
exact `Host: 127.0.0.1:<port>`. Pairing, mutations, preflight and health require
the configured `chrome-extension://<ID>` Origin. Chrome extension workers may
omit Origin only on authenticated `GET /v1/jobs/<id>/status`: that narrow route
still requires the exact Host, loopback client and valid RAM-only bearer. Any
present wrong or `null` Origin is rejected, including on status requests.
There are no wildcards or cookie authentication. The extension's explicit user
activation may call:

1. `GET /health`: minimal availability/protocol information, no secret or data.
2. `POST /v1/pair` with `{"explicitUserActivation":true}`: idempotent RAM-only
   bearer delivery to that exact extension Origin. The extension may retain it
   in memory or `chrome.storage.session`, never persistent local/sync storage.
   A lost pairing ACK or extension reload returns the same current token without
   spending a source attempt or restarting the backend.

All following requests require `Authorization: Bearer <in-memory token>`:

| Route | Body / response |
|---|---|
| `POST /v1/begin` | `{identity,transportKind,outputBudgetBytes,metadata}` → job ID, binding SHA, offset/sequence zero, maximum 1 MiB chunk |
| `POST /v1/jobs/<id>/request` | `{sourceBindingSha256,requestSequence}` starting at one → matching binding/sequence, cumulative `sourceRequests`, `authorized=true`; required before every pilot source fetch |
| `POST /v1/jobs/<id>/chunk` | Binary octet-stream, headers `X-Native-Offset` and `X-Native-Seq`; exact sequential ACK only after file and prefix receipt are fsynced |
| `POST /v1/jobs/<id>/segment` | One scalar segment proof → `{segmentCount,ledgerSha256}` |
| `POST /v1/jobs/<id>/finish` | Bound full-file/EOS proof → HTTP 202, validation queued, **not** local or Drive completion |
| `GET /v1/jobs/<id>/status` | Binding/state/count/error information; `nativeProof` appears after local validation; `driveVerified=true` only after canonical proof and cleanup |
| `POST /v1/jobs/<id>/retain` | Allowlisted error class; a source block returns `stopAllSourceWorkers=true` |
| `POST /v1/jobs/<id>/publish` | Empty object; explicit retry of a validated retained pair, still subject to Drive cooldown |

Segment chain starts at 64 zero characters and advances as
`SHA256(previousHex + "\n" + compactSortedJson(segment))`. The streaming finish
proof contains `sourceBindingSha256`, `bytes`, `protocolEos=true`,
`reencoded=false`, `container_reassembled=true`,
`encoded_audio_not_reencoded=true`, `isLive=false`,
`stripDuplicateInit=false`, `segmentCount`, `segmentLedgerSha256`,
`endSegmentNum` and `endTimeMs`.

The source adapter must await each write/segment ACK and propagate a batch stop
to every active transport. Its finish callback polls authenticated status until
the same binding has `nativeProof`, then returns those hashes to the SDK adapter.
The completion request is durable and at most 16 KiB. Reposting the exact same
finish body is idempotent; changed completion bodies are rejected. Long scans
run outside the source write lock and do not need a long browser HTTP request.
A lost finish ACK is recovered through status, without source redownload. An
ambiguous chunk ACK instead requires a hold; it must not be blindly resent.
At most eight loopback requests, two validation tasks and two uploads may
run concurrently; active source/file leases are separately capped by the lease.
An exclusive per-job claim prevents duplicate uploads. Request bodies and
headers are never logged. The gateway can generate the RAM-only token, or an
embedding caller can provide it. A CLI environment seed is optional and is
removed from the child environment after reading; it is never printed/saved.

## Drive proof, recovery and validation

The canonical archive layout and `Rclone.copy_pair` upload exactly one native
audio file plus its `.info.json` sidecar. Both remote objects must have distinct
Drive IDs and matching sizes/MD5. `verify_and_delete` writes the verified pair
receipt before deleting either exact owned local file, then writes the deleted
receipt. Source or metadata changes during upload fail closed. A crash between
the two deletions resumes from the durable verified receipt without uploading
another copy. Unacknowledged download tails, corrupt prefixes and unknown SABR
resumes remain retained for explicit recovery.
Late tab-close or client-timeout controls cannot downgrade queued validation,
validated/uploading data, cleanup proof, or a deleted completion. Those controls
only annotate in-progress proof states; a completed job remains
`driveVerified=true`. An upload failure keeps its publish/recovery path available.

Offline checks:

```powershell
python -I -m unittest discover -s et-channelers/pipeline/tests -p 'test_native_audio*.py'
```

The fixtures use invented bytes, mocked codec evidence and a fake Drive. Local
HTTP fixtures test origin/Host/bearer rejection, idempotent pairing, bounded chunk
admission and truthful upload state. They establish failure handling, not real
source compatibility. A single real native full-file pilot remains required.

The 39 focused offline fixtures also cover the one-attempt pilot policy,
preservation of a longer existing refusal deadline, streamed SABR proof, and
lost-finish-ACK recovery. Before scaling to four workers, profile the exclusive
owner's historical-state scans and verification I/O; replace repeated scans with
an active-lease registry and periodic reconciliation without weakening proof.

On 2026-11-17 at 05:11:33 UTC, an additional private, real-codec fixture passed
the gateway end to end: a generated three-second AAC/MP4 (13,576 bytes) had one
AAC audio stream, zero video streams and 142 packets. Real `ffprobe` scanning,
the actual metadata builder with a static public thumbnail, binary chunk ACKs,
asynchronous validation, fake-Drive pair proof and owned-pair deletion all
passed. The complete temporary fixture occupied 24,455 bytes and was removed.
No YouTube, real Drive or GPU operation occurred; it was not counted as a real
source. An independently generated Opus/WebM fixture emitted a packet-header
warning from the installed codec tools before entering this pipeline and was
correctly rejected. That observation does not establish a problem with actual
YouTube Opus files, and no codec-error check was suppressed.
