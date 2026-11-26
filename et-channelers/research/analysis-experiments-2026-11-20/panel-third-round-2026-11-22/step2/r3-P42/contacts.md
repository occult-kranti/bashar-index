# r3-P42: hold-out and other-group contacts

Written from 2026-11-26T11:38:51Z (UTC, from `date -u`) by the r3-P42 agent (a model agent working for the project lead; not a person),
and kept up to date during the run.

Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**No hold-out or other-group contact was made.** No file holding measured values (text, labels, features, per-creator or
per-recording derived values, caches) of a hold-out or other-group creator was opened or scanned. `llm/labels/holdout`,
`llm/labels/other` and the reliability folders were never opened, and no recursive text search was run over the run
folder.

Reads that are not contacts (identifier lists and metadata, D31; seen-only stores):

| When (UTC) | What | Why |
|---|---|---|
| between 11:16:08 and 11:30:50 | deposit 3 (git `origin/main`), the programme, the lead's rulings, deposit 2's public files | instruments and rules; no data |
| between 11:16:08 and 11:30:50 | `step1/lead-step1-decisions.md`, `step2/lead-step2-decisions.md`, step-1 code (`p01common.py`, `pubrules.py`, `extract_p03.py`), `llm/prep.py`, the hypotheses package's `adapter.py` and `voice_sets.py`, CSS and PT code, the frozen rule coder `step0/code/rule_coder.py` (code, not data: decision 51 L2) | loaders and rules to reuse |
| between 11:16:08 and 11:30:50 | `step0/split.private.json` (keys, then the draw's audience bands) | the 23 non-development seen creators (the run's units) and their audience band |
| between 11:16:08 and 11:30:50 | CSS `analysis.private.json` and `extract.private.json` (keys and table shapes only) | to find where seen creator profiles are stored |
| between 11:16:08 and 11:30:50 | `sync/edition_asr_manifest.jsonl` through `prep.recordings()` | ledger rows of the 23 creators (counts of recordings only); no transcript opened |
| from 11:36:39 | transcripts through `prep.load_units` (seen guard; each row checked seen and non-development); `labels/seen` voice and title files through `adapter.load_seen_bundle`; title files through `adapter.json_seen_files` / `read_seen_json` (seen only); PT's `page_text()` (TABLE's whitelisted extract, seen rows only; the group column is tested before a row is built, D31); CSS's seen-only `extract.private.json` through `css_analyse.evidence` | the run's inputs, 23 non-development seen creators only (`code/extract_p42.py`) |
| 11:45:48 to 12:02:28 | the private extract and counts of this entry (`private/`), seen only | the run |
| between 12:02:28 and 12:05:45 | step 1's `pubrules.known_register()` (reads `llm/creator-sets.json`, `bridge-ledger.jsonl`, wer-anchor `gridshift-plan.private.json`, MR `printed-groups.private.json`, E `groups.private.json`, step0 `split.private.json`) | the nested-count check of the voice-eligible set (seen-only creator sets; identifier lists and metadata, D31) |
| up to 12:12:09 | a scratch copy of the staged step-1 tree (`step1-publish-20261126/.../step1/`, public files only) with this entry's `public/` added; the solver scripts in `collect/code/pass2/scans/` and the coordinator's four new solvers | the privacy solvers (public files only) |
| between 12:12:09 and 12:13:26 | `pubrules.scan_identifiers` over `public/`, with the extract's audio hashes, video ids and page keys as extra needles | identifier scan (0 hits) |

Every time above is UTC from `date -u` (ranges bracketed by stamps taken with `date -u`; the full stamps are in `run-record-hash.md`, `a6-variants-hash-record.md` and `status.json`).
