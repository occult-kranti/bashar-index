# r3-P07: hold-out and other-group contacts

Written 2026-11-26T06:47:04Z (UTC, from `date -u`) by the step-1 agent of r3-P07, r3-P21 and r3-P27 (a model agent; not a person).

**No hold-out or other-group contact was made.** No file holding values of a hold-out or other-group creator was opened
or scanned; no recursive text search was run over the run folder; `llm/labels/holdout`, `llm/labels/other` and the
reliability folders were never opened.

Reads that are not contacts (seen-only stores, identifier lists and metadata):

| What | Why |
|---|---|
| `llm/creator-sets.json` | seen-only assertions; identifier scan of public files |
| `llm/labels/seen/voice` through `adapter.load_seen_bundle` (MR's `mrcommon.py`) | seen voice labels |
| paper review cache `rv-words.private.pkl` | seen word times (asserted seen only), under `run_locked.sh` |
| MR `printed-groups.private.json`, E `groups.private.json`, step0 `split.private.json`, `bridge-ledger.jsonl`, wer-anchor `gridshift-plan.private.json` (through `pubrules.known_register`) | seen creator sets for the nested-count rule |
| `llm/labels/seen/voice` files (`code/scan_ids.py`) | seen audio hashes, video ids and creator codes as needles for the identifier scan |
| `llm/labels` folder names (a listing; no file of holdout or other opened) | to see the seen folder's layout |
| r3-P01, r3-P02, r3-P04 and r3-P30 public files, READMEs and code | binding results and loaders |

Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
