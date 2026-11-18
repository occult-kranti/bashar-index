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

`frozen_ingestion_coverage.py` contains the tested coverage/proof implementation from the source revision recorded in `PROVENANCE.json`. Its functions are preserved; only imports are adapted to this package's parent pipeline. The executor imports this frozen module for local receipt coverage, never invokes its exporter CLI, and does not depend on edits to the live status exporter. Source-critical parent pipeline dependencies remain pinned by the admission contract.

`PROVENANCE.json` records source-code hashes and the portability changes. It contains no runtime proposals or operational evidence. Targeted synthetic tests live in `pipeline/tests/test_native_bulk_portable.py`; they forbid network connections and process launch.
