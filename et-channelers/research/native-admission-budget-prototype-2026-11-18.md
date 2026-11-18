# Metadata-first admission budget prototype, November 18

`pipeline/native_bulk/admission_budget.py` is an isolated, source-free resource ledger for a future executor. It launches no process, writes no runtime control, contacts no source or Drive service and grants no execution scope. Recovery5 runs its separately admitted two-worker contract; this prototype is excluded from that executor. ASR stays paused.

The intended first pilot has **four owned children in total: at most two bootstrap/metadata children and two media children**. Later reviewed settings may allow three or four simultaneous media children when their actual selection grants fit; four total children and two bootstrap-only children remain ceilings. This requires a new executor integration and scoped admission, not a worker-count edit.

## Evidence and bounds

The saved seven-frame profile contains 140 decisions, 120 paired archives and 125 known selected sizes. Its selected-size median is 17,226,970 bytes, p95 about 71.94 MB and maximum 145,141,353 bytes; 15 sizes are unknown. The observed browser-profile disk peak is 21.28 MB, but disk observations do not measure browser RAM or justify shrinking the existing **240 MB per-job headroom**. The profile was derived from saved metadata only, with zero Source/Drive requests or media hashes. Its evidence SHA256 is `1ff11cd75e659813a81b3c77d9782a67e3065618d328ca33f9a2cd168399da55`.

| Scenario | Source job reservations | With one reserved publisher envelope |
|---|---:|---:|
| Existing two full 2 GB audio slots + 240 MB each | 4.48 GB | 4.72 GB |
| Two unknown-size media slots + two 240 MB bootstrap slots | 4.96 GB | 5.20 GB |
| Four known files, each as large as the sample maximum + 240 MB each | 1.541 GB | 1.781 GB |
| Four full 2 GB audio slots + 240 MB each | 8.96 GB | 9.20 GB: exceeds 5.5 GB |

Every scenario must additionally fit inactive files, retained partials, publication backlog, other reservations and current storage. The sample has 188.2 MB of retained closed-folder files and a separately observed peak 191.4 MB of completed payload/canonical metadata. Adding these as a conservative scenario is not a measurement of simultaneous peak use. Unknown sizes never borrow the sample median, `filesize_approx` or a duration-derived estimate. These figures support a capacity experiment, not a throughput promise or a safe global file-size cap.

## Ledger contract

An immutable `JobKey` binds job ID, owner, lease, plan and attempt hashes. The allowed scope is a tuple supplied at construction; a settled or failed job cannot be admitted again. `Selection` binds the validated metadata hash, format hash and an integer declared size or explicit unknown. No URL, credential or source client is part of this component.

`admit_bootstrap()` charges the complete 240 MB envelope before a folder, attempt or child is created. `bind_selection()` retains one immutable selection. `reserve_media()` atomically upgrades that envelope to selected bytes + 240 MB, or **2 GB + 240 MB when unknown**. A failed upgrade leaves the same selected child waiting with its bootstrap reservation and produces no MediaGO. `Deferred` describes local capacity/backpressure; it is not an item quarantine, a source refusal, a new attempt or permission to re-extract.

`commit_media_go()` repeats fresh source/lease/HTTP/control and capacity checks under the shared dispatch lock before calling the durable writer. `MediaPermit.fingerprint()` binds the reservation to its immutable job, selection and byte ceiling. A failed or ambiguous commit is one-shot: the envelope stays charged, the job becomes `go_uncertain` and new dispatch holds for reconciliation. A visible permission is never overwritten or blindly replayed.

The declared size is an **enforced write ceiling**, not proof of accurate metadata or complete audio. `check_audio_write()` runs immediately before the child writes each audio chunk. Any byte beyond the granted selection size or the unchanged 2 GB hard cap fails before write. There is no size top-up, hint correction, truncation acceptance or retry; the partial and observations remain retained. Existing codec, original-track, packet/extent, quality and source-outcome rules still apply unchanged.

The inventory callback runs under the same lock and excludes entire active job folders. It counts all inactive files exactly once, including retained files and completed pairs awaiting publication. It provides per-job inactive footprints for reconciliation. Active folders are charged their complete envelope; the ledger never combines sampled child byte counts with a sampled remaining reservation.

Each mutation checks:

- Inactive spool + active envelopes + one **240 MB publisher-growth envelope** ≤ 5.5 GB.
- Inactive managed storage + those commitments + all other reserved growth + 64 MiB journal reserve ≤ 16 GB.
- The same managed projection + other owner-accounted storage ≤ 18 GB, preserving 2 GB of the 20 GB owner allowance.
- Physical free after full active commitments, publisher growth, other growth and journal reserve ≥ 2 GB. This deliberately conservative check can double-charge already-written active bytes; it avoids an unsafe cross-process sample.

The 240 MB publisher-growth envelope stays reserved before source dispatch so pending publication cannot be starved of its metadata/control workspace. It is inside the existing 5.5 GB scope, not an additional external allocation. The adapter must enforce this publication growth bound before writes. Root's outer matching lease/resource admission and current physical/storage checks remain prerequisites.

`settle_owned()` requires exact closure provenance, owned processes gone and observed source history committed. It reconciles the finished folder into inactive inventory before releasing its future-growth envelope. Oversized files, unclosed jobs or uncommitted history keep their charge and hold dispatch. A strict-quality proof pin is required for the ready-publication state; the module does not itself prove audio quality. Closed files stay counted if publication or cleanup fails. Global capacity trouble may hold future dispatch while safely recording an already closed job.

Only one pair can enter publication. New bootstraps and MediaGO pause at two pending pairs or 500 MB pending output by default; already admitted media remains bounded and may drain. The thresholds are conservative tuning inputs, not caps that discard completed files. Paired receipt and cleanup proof pins precede retirement, and retained survivors remain measured. Source and Drive holds stay distinct: publication of valid existing output may drain while source dispatch is held, subject to the publisher's unchanged Drive guards.

## Exact integration hooks

1. **Controller settings/contract:** explicitly admit the new limits and pin this module, the gate and the changed worker/parent. The current constructor and bulk contract require two full source slots; changing `workers` alone is insufficient.
2. **`NativeBatch.execute_child()` before folder/attempt/fork:** replace the full `max_audio_bytes + HEADROOM` admission with `admit_bootstrap()`, using the existing dispatch `RLock`, exact owner/lease and capacity partition. Bind the attempt once. Keep owned Job attachment, sanitized diagnostics and initial parent GO unchanged.
3. **Worker `NativeYoutubeDL.process_info()`:** validate the exact selection and persist sanitized metadata, then write the immutable selected request and enter `waiting_media_capacity`. The current `persist_selection()` immediately sets `native_transfer` before `super().process_info()`; the new worker must wait for MediaGO before entering that call or marking transfer. The parent must service requests while polling owned children rather than block behind publication.
4. **Capacity wait:** keep this same selection and owned job. Use the remaining configured job deadline, continuous worker/parent guards and bounded polling, as `selection_gate.wait_permission()` does. Do not reuse the initial 60-second GO window or let the old 90-second `bootstrap` branch falsely classify a deliberate capacity wait as source failure. Expiry produces truthful administrative capacity evidence and owned closure, not automatic re-extraction, zero-request claims or a censored source timeout.
5. **Parent selected-request handler:** validate request binding, saved metadata, worker/settings/plan/attempt/nonce and size. Derive `Selection.declared_bytes` from that validated request. Reserve media under the shared lock; ingest pending HTTP/fatal observations and repeat guards before commit. In the durable callback, assert gate `maximum_audio_bytes == permit.audio_write_limit`, bind `permit.fingerprint()` and atomically publish the exact MediaGO. An opaque fingerprint alone does not prove that the two modules used the same allowance.
6. **Child audio writer:** authenticate the durable gate acknowledgement and bind it to this permit/selection before calling `check_audio_write()` at the existing `MeteredFile.write()` boundary. Keep the original on-write hard cap, profile cap and all auxiliary writers within their reserved headroom. Never rewrite selected `filesize` to match observed bytes or treat a budget permit as a strict-quality proof.
7. **Finalization and publication:** preserve the existing order of HTTP/fatal ingestion, owned process closure and actual-folder reconciliation. Feed that same-lock partition into `settle_owned()`. Use the unchanged native publication/Drive proof logic between `begin_publication()` and `finish_publication()`, outside the dispatch lock during network I/O. Preserve retained output on every failure; do not free bytes from `local_complete` alone.
8. **Scheduler/instrumentation:** retain drain → refill eligible source work → publish one ordering and a single publisher. Measure bootstrap/selection wait, media time, publisher start/finish, forced scans, ready bytes, profile disk/RAM, guarded deferrals and verified paired completions. Compare the initial four-child/two-media pilot with the frozen two-child baseline before considering three/four media workers. No current source grant is expanded by the prototype.

Focused fixtures cover simultaneous upgrades, all storage ceilings, unknown and underestimated sizes, immutable ownership/selection, failed GO commits, revocation, retained-file reconciliation and publication backpressure. Joint fixtures use the real selection gate for known/unknown grants and reject mismatched budget/gate allowances before publishing permission. These are source-free contract checks; actual protocol acceptance and performance require a separately admitted future integration.
