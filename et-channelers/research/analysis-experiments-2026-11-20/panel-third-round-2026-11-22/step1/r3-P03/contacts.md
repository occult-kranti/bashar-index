# r3-P03: hold-out and other-group contacts

Written 2026-11-26T02:59:30Z (UTC, from `date -u`) by the step-1 agent of r3-P01 and r3-P03 (a model agent; not a person).

**No hold-out or other-group contact was made.** No file holding measured values (text, labels, features, per-creator or
per-recording derived values, caches) of a hold-out or other-group creator was opened or scanned, and no recursive text
search was run over the run folder, llm/labels/holdout or llm/labels/other.

Reads that are not contacts (identifier lists and metadata, D31; seen-only stores):

| What | Why |
|---|---|
| `llm/creator-sets.json` | seen-only assertions and the identifier scan of public files (identifier list) |
| `bridge-ledger.jsonl` | the bridge's seen creators for the nested-count register (ledger metadata; the other-group row's bundle was never opened) |
| `sync/edition_asr_manifest.jsonl` through `prep.recordings()` | ledger rows; only seen transcripts were opened (prep's guard) |
| paper review cache `rv-words.private.pkl` and `rv-bridge-pairs.private.pkl` | seen only (built seen-only; asserted against creator-sets.json); read under `run_locked.sh` |
| wer-anchor `gridshift-plan.private.json` and `hyp/grid-NN-shift15.json` | BR-GS's 40 seen recordings (asserted); no other file of `hyp/` was opened |
| `labels/seen` through `adapter.load_seen_bundle` | seen voice and feature labels only |
| CROSS `transcript-pass.private.pkl` (cue hits), MR `printed-groups.private.json`, E `groups.private.json`, step0 `split.private.json` | seen-only stores (cue-hit positions; creator sets for the nested-count rule) |
| `llm/labels/seen/` and `llm/reliability/` folder names (a listing, no file opened) | to record whether punctuation-stripped labels are stored at unit level; the reliability folders were not opened because they may hold hold-out material |
| r3-P02 and r3-P30 public files and code; a hash of r3-P02's copy of style.py | the lead's binding results; no data |

Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
