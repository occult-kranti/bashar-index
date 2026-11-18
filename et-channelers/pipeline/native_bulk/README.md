# Finite native cohorts

This package preserves the reviewed finite-cohort executor as portable source. It does not replace a running executor, install a grant, or include runtime data. Source execution still requires an explicit owner grant, matching lease and reservation, pinned code and metadata, and current admission checks.

Run the metadata-only plan command from the directory containing `pipeline/`:

```powershell
python -m pipeline.native_bulk plan --settings "<controller-settings.json>"
```

The supplied settings must point to the caller's cohort manifest and frame map. Plan mode validates their membership, order and plan hashes and creates no runtime state. No settings, grants, credentials, episode identifiers, receipts or media are bundled here.

The controller admits one immutable ordered cohort of at most 1,280 items, partitioned into frames of at most 20. A single grant binds the cohort, frame map and every frame's settings. Frames run serially with two source workers and one publisher. All frames retain one outcome ledger, sequence and sticky stop history; the controller never initializes or clears that ledger. An interrupted invocation requires reconciliation.

The source and publication rules are unchanged: fixed mweb/stock-WPC transport, zero retries, full reservations, strict native-audio quality and durable remote proof before owned cleanup. Only a bound full transfer with strict quality can reset the consecutive failure streak. A complete terminal result is authoritative even when progress was never written. Final HTTP evidence is committed before reservation release.

This snapshot includes the typed parent-deadline path. An explicit parent bootstrap or job deadline can produce separate censored evidence only after validating its configured limit, measured elapsed time, owned child identity and closure, cleanup and current admission provenance. Access and counters remain unknown; the target is quarantined without success or a streak reset. Missing final results for unknown failures, control-write or provenance failures, and all global source refusals still hold the batch. The descriptor never substitutes fabricated worker progress or a worker result. Non-media timeout rows do not reorder genuine media outcomes; true late media and sticky holds remain protected.

The bounded capacity cache preserves full active reservations and reconciles a finished folder as inactive before releasing its slot. Windows process identity and owned-process closure checks remain required for execution. Metadata-only planning and the synthetic tests can import the package independently of a workstation layout.

The scheduler drains finished source work and refills the existing two slots while one separate publication thread handles copy/stat/finalization. The finite adapter admits at most four outstanding acquisitions; it keeps full real or virtual slots for submitted work that has not yet reserved its child folder. Actual inactive bytes and a separate 240 MB publication envelope must fit the 5.5 GB spool, the managed allowance/journal reserve and the 2 GB physical floor, including other owners' future commitments. Metadata-first sizing, MediaGO and extra source workers are not integrated.

The scheduler and batch share the same fatal-stop Event. A publication, guard or observer failure reaches the mature source/GO guards immediately, without waiting for the manager's later stop callback. Copy/stat calls run outside the dispatch lock. A local-complete acquisition becomes a verified Publication only after the mature paired receipt predicate passes and the saved canonical record matches. Global HTTP history is still ingested by source finalization, never reset by the publisher.

A bounded scheduler drain can report unclosed callbacks. The collector owner retains its lock until those callbacks actually return; it never invents thread cancellation or releases their resources. Ready outputs remain retained after a fatal event. The controller additionally requires actual owned-job audits, complete callback closure, a complete scheduler partition and zero pending/inflight items before advancing a frame. A noncooperating callback can therefore keep the owner waiting for reconciliation.

The worker's four control paths must match the exact profile. The Source6 prototype uses its own STOP marker; a preserved predecessor STOP remains history rather than the new profile's dispatch marker. Tests exercise the real worker guard against both markers.

## Dated actual trial

The separately admitted Source6 trial began on November 18 at 19:02:38 UTC. Its first frame closed with **15 verified pairs / five holds**, 422,862,190 audio bytes, no pending/inflight items and proven callback closure. The holds were three unavailable-format cases, one scoped source403 and one parent-censored timeout. Source access for the censored attempt remains unknown.

Saved events show **seven source-future submissions strictly inside actual copy intervals**, with a 246.595-second union of source-future/copy overlap. Peak source futures were two and peak outstanding acquisitions four. Copy duration median was 13.797 seconds; stat median was 2.468 seconds; finalization median was 0.047 seconds. Partition calls include cache hits: their median was zero and p95 was 2.687 seconds. Phase intervals overlap and must not be added as exclusive wall-time shares. Source futures include admission/bootstrap/cleanup, so these events do not prove simultaneous audio transfers. This different content sample establishes actual scheduling overlap, not a controlled production speedup.

Each child has bounded sanitized stderr capture and a separate durable fatal diagnostic path. Only allowlisted exception classes, numeric errors and control-write stages are retained; unstructured stderr, URLs and credentials are discarded. A fatal diagnostic cannot replace a worker result or prove zero source access. Unknown crashes, control-write failures and diagnostic failures hold the batch, including fatal evidence found after a child has closed. HTTP evidence is ingested before any diagnostic hold or slot release.

An owned child can wait up to 55 seconds before GO when a sibling extends the adaptive pause after it was spawned. The parent repeats source, lease, stop, process and diagnostic checks throughout this wait. It commits GO only after the pause expires and before the child's existing 60-second window. Revocation, a global hold, a child exit or the bounded wait deadline prevents GO; this administrative deadline never becomes a censored source timeout.

`frozen_ingestion_coverage.py` contains the tested coverage/proof implementation from the source revision recorded in `PROVENANCE.json`. Its functions are preserved; only imports are adapted to this package's parent pipeline. The executor imports this frozen module for local receipt coverage, never invokes its exporter CLI, and does not depend on edits to the live status exporter. Source-critical parent pipeline dependencies remain pinned by the admission contract.

`PROVENANCE.json` records the ten implementation-source hashes and package-relative portability changes. It contains no runtime proposals or private operational files. Canonical function AST checks work across Python 3.11 and newer. Source-free adapter fixtures in `pipeline/tests/test_native_parallel_batch_adapter.py` complement the policy/quality/cleanup fixtures in `test_native_bulk_portable.py` and the scheduler Event tests. They forbid network and process launch, exercise blocked publication/refill and guard failures, and keep real deletion out of the adapter tests.

After owned-process closure, profile cleanup may retry only Windows sharing/lock errors 32 and 33. The retry schedule is bounded to 15.5 seconds of scheduled waits; a filesystem call itself is not canceled. Exact parent-path, symlink and junction checks repeat before each attempt. Other errors receive no retry, actual absence determines the cleanup result, and retained or uncertain profiles keep the existing strict hold. These filesystem retries never repeat a source request, change permissions, unlock handles, or affect another process.
