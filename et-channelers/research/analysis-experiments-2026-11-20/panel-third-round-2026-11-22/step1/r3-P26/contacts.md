# r3-P26 / r4-P06: hold-out and other-group contacts

Written by the step-1 agent of r3-P26, r3-P33 and r3-P28 (a model agent working for the lead; not a person). Times are
in status.json (UTC, from `date -u`).

**No hold-out or other-group contact was made.** No file holding measured values of a hold-out or other-group creator
was opened or scanned, and no recursive text search ran over the run folder. llm/labels/holdout, llm/labels/other and the
reliability folders were not opened or listed.

Reads that are not contacts (seen-only stores, published aggregates, code):

| What | Why |
|---|---|
| `labels/seen` (voice, titles, asks) through the frozen analysis package's seen-only path, called by CROSS `mtmm.build()` | to rebuild MTMM's twelve seen creator-level measures (unchanged published code) |
| round-2 RX `rx-counts.private.pkl` | seen-only cue counts (its build log: 1,229 recordings of the 71 seen creators), read by `mtmm.build()` |
| round-2 PT `pt-b-recording-asks.private.csv` | page asks of seen recordings only (PT part b codes seen descriptions only) |
| CROSS, TL, VER public files; the step-1 entries' public files; the exploratory status table | published aggregates |
| code and frozen prompts (CROSS `mtmm.py` and `crosscommon.py`, RX `patterns_v1.py`, `titles.py`, PT `pt_b.py`, the voice codebook) | to code the dependence map; no data |
| `llm/` directory listing (file names only; the key file was not opened) | to locate the title instrument and prompts |

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

Exploratory; not a test of H1-H10.
