# r3-P27: hold-out and other-group contacts

Written 2026-11-26T06:47:04Z (UTC, from `date -u`) by the step-1 agent of r3-P07, r3-P21 and r3-P27 (a model agent; not a person).

**No hold-out or other-group contact was made.** Both groups (development and check creators) are seen creators; no
file holding values of a hold-out or other-group creator was opened or scanned; no recursive text search was run over the
run folder; `llm/labels/holdout`, `llm/labels/other` and the reliability folders were never opened.

Reads that are not contacts:

| What | Why |
|---|---|
| step0 `split.private.json` | the development (tuning pool) and check (non-development) membership, seen creators only |
| `llm/creator-sets.json` | seen-only assertion |
| `llm/labels/seen` (voice, asks, features) through MR's `mrcommon.load_bundle` | seen labels; frozen per-recording functions |
| r3-P04 `private/p04.private.json` (creator counts per statistic only) | to keep this entry's bases consistent with r3-P04's printed counts (seen only) |
| the paper's sources (`appendix-protocol.tex`, `data.tex`, public repository) | the definition of development and check creators |
| `pubrules.known_register` inputs (as in r3-P07) | nested-count rule |

Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
