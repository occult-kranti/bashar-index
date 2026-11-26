# r3-P20: hold-out and other-group contacts

Written 2026-11-26T06:56:22Z (UTC, from `date -u`) by the step-1 agent of r3-P19, r3-P20 and r3-P23 (a model agent; not a person).

**No hold-out or other-group contact was made.** The hold-out rung of the gate ladder is copied from the published
GATES table (`exploratory-2026-11-21/built/GATES/public/GATES-gates.csv`, which prints the R-hold values as the
first-round results file published them), and the hold-out's quality shift is rv-D2-H's published SMD (status table
headline). No R-hold value was recomputed and no file holding hold-out or other-group measured values was opened or
scanned; the reliability folders (decision 11), `llm/labels/holdout` and `llm/labels/other` were not opened or listed;
`llm/reliability_samples.json` was not opened; no recursive text search was run.

Reads that are not contacts:

| What | Why |
|---|---|
| `GATES-gates.csv` (public), the status table (public) | published aggregates (allowed inputs) |
| r3-P19's private copy of the seen production labels (`r3-P19/private/roster.private.pkl`) | seen only (frozen seen-only loader) |
| the paper review's seen word cache (`rv-words.private.pkl`) through r3-P01's seen-only loader, under `run_locked.sh` | seen only (asserted against creator-sets.json) |
| `llm/pilot/set-g.private.json`, `llm/pilot/titles-final-g.labels.private.json` (video keys of the middle reading only, hashed at once) | set G is seen-only; used to define "outside G" |
| `llm/creator-sets.json`, `prep.recordings()` ledger rows, r3-P01's `pubrules.known_register()` | identifier lists and metadata (D31); seen creator sets |

Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
