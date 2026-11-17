# Automated native audio and English-ASR series

`native_series.py` coordinates up to three separately planned 20-item native
frames. It does not download on import or grant itself additional source scope.
The Windows runtime adapter, immutable plans, code pins and root authorization
are saved privately. The working downloader uses isolated owned Chromium, the
stock WPC provider and upstream yt-dlp HTTPS transfer. It does not wait through
playback or use screen recording.

## First completed execution, 22:27 UTC

The initial three-frame series closed with 30 new canonical pairs (10/11/9),
11.19 measured source hours and 27m22.68s source wall time. Its local English
consumer verified 18 ASR bundles covering 7.85 source hours. All matching source,
staging and GPU allocations are released. Thirty item holds remain separate;
three source attempts have uncertain evidence and cannot be silently retried.
The following admission describes that completed execution, not a running job.

## Initial admitted execution

The November 17 series started once at 21:52:52 UTC for exactly 60 untouched
latest-20 entries. Its common expiry is November 18 at 01:49:57 UTC. This is a
bounded execution, not permission to start latest 50 or retry held assets.

| Work | Owner and bounds |
|---|---|
| Native acquisition | Two isolated source workers; 5.5 GB reserved spool; exact plans and installed dependency pins |
| Drive archival | Paired native audio and sanitized full metadata, exact named-object identity/size/MD5 verification, durable receipt before local retirement |
| English handoff | 500 MB shared allowance, at most three audio/metadata pairs; retained locally after Drive proof, no Drive input pull |
| CUDA ASR | One separately admitted owner, existing pinned Distil model, 6.5 GB VRAM maximum and soft 70% rolling utilization target |
| Shared storage | All six managed roots plus active growth reservations stay within 16 GB; physical free-space gate leaves 2 GB spare |

Only explicit original-English audio enters this initial handoff. Unknown or
foreign source language creates a metadata-only review record without consuming
a staging slot. Source language is not copied from captions. A separate
language-review admission can use the existing multilingual model and save
original transcript plus English translation. Model-inferred English retains
its inference provenance and does not rewrite unknown source metadata.

## Durable execution and backpressure

The series records dispatch intent before launching a frame. Every item then
needs an exact canonical receipt, spent-attempt evidence, uncertainty hold, or
proof that no source attempt started. A crash cannot silently reissue that
frame. Reconciliation inspects and drains existing work; it never launches a
replacement source request.

The next frame requires drained owned children/profiles, current resource and
source-control checks, and the exact live English consumer identity with a fresh
heartbeat. Completed files that lack canonical publication or a finalized local
handoff hold the series for reconciliation. Ordinary per-item no-format or
bound-media refusal holds do not erase successes or restart the held item.

Handoff readiness follows the durable canonical pair receipt. The consumer uses
its own queue lock, not the collector's lifetime lock. It verifies ASR result
objects before retiring owned links. Full staging pauses new dispatch locally;
a capacity timeout retains original files. It does not clear a source cooldown
or manufacture one. Source and consumer share the original expiry and cannot
extend it themselves.

The v4 HTTP ledger persists across all frames. A media 403 is item-specific only
when both requested and final response URLs bind to the selected asset. Unknown
or control refusals, every provider 429 and explicit protection checks stop
dispatch. Three distinct bound-media 403s within ten minutes trip a durable
global breaker. Previous denials remain quarantined, and historical STOP and
cooldown files remain preserved. See [native batch policy](NATIVE_BATCH.md).

## Status and recovery

The public [collection snapshot](../plan/ingestion_status.json) exposes aggregate
counts and times only. A running series requires a matching active unexpired
lease, root/series identities and the actual Windows PID plus creation time.
Global source/series/Drive holds prevent that claim. GPU activity additionally
needs a fresh nonterminal consumer heartbeat and matching active GPU lease.
The parked legacy collector's STOP stays present and does not mask this separate
executor. Publishing a snapshot does not make the dashboard a live process API.

Do not switch, reset or edit pinned runtime files during an active series. Use
the private invocation receipt to identify the existing process before doing
anything after a restart. Reconcile interrupted work; preserve original
attempts and ambiguous files. Never count a prepared plan, downloaded prefix,
local complete file or detector result as a Drive-verified archive/transcript.

Current counts, admissions and dated outcomes are in [HANDOFF](../HANDOFF.md).
The [measured ETA](../research/collection-eta-2026-11-17.md) separates first-pass
attempt capacity from the unresolved work needed for complete acquisition.
