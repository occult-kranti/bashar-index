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

The scheduler drains finished source work, refills the existing two slots when guards and full reservations permit, then publishes one ready pair. Publication remains serial. This ordering does not promise a production speedup; publication-bound work can still determine throughput.

Each child has bounded sanitized stderr capture and a separate durable fatal diagnostic path. Only allowlisted exception classes, numeric errors and control-write stages are retained; unstructured stderr, URLs and credentials are discarded. A fatal diagnostic cannot replace a worker result or prove zero source access. Unknown crashes, control-write failures and diagnostic failures hold the batch, including fatal evidence found after a child has closed. HTTP evidence is ingested before any diagnostic hold or slot release.

An owned child can wait up to 55 seconds before GO when a sibling extends the adaptive pause after it was spawned. The parent repeats source, lease, stop, process and diagnostic checks throughout this wait. It commits GO only after the pause expires and before the child's existing 60-second window. Revocation, a global hold, a child exit or the bounded wait deadline prevents GO; this administrative deadline never becomes a censored source timeout.

`frozen_ingestion_coverage.py` contains the tested coverage/proof implementation from the source revision recorded in `PROVENANCE.json`. Its functions are preserved; only imports are adapted to this package's parent pipeline. The executor imports this frozen module for local receipt coverage, never invokes its exporter CLI, and does not depend on edits to the live status exporter. Source-critical parent pipeline dependencies remain pinned by the admission contract.

`PROVENANCE.json` records source-code hashes and the portability changes. It contains no runtime proposals or operational evidence. Targeted synthetic tests live in `pipeline/tests/test_native_bulk_portable.py`; they forbid network connections and process launch.

After owned-process closure, profile cleanup may retry only Windows sharing/lock errors 32 and 33. The retry schedule is bounded to 15.5 seconds of scheduled waits; a filesystem call itself is not canceled. Exact parent-path, symlink and junction checks repeat before each attempt. Other errors receive no retry, actual absence determines the cleanup result, and retained or uncertain profiles keep the existing strict hold. These filesystem retries never repeat a source request, change permissions, unlock handles, or affect another process.
