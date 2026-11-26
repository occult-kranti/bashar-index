# r3-P55: hold-out and other-group contacts

Written 2026-11-26T13:19:29Z (UTC, from `date -u`) by the step-2 description agent (a model agent working for the project
lead; not a person), for the seven step-2 description entries (r3-P48 with r3-P49 / r4-P18 and r3-P50; r3-P51 / r4-P28;
r4-P29; r3-P52 / r4-P12; r3-P53 / r4-P30; r3-P55; r3-P56), which share one run.

Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**No hold-out or other-group contact was made.** No file holding measured values (text, labels, features, per-creator or
per-recording derived values, caches) of a hold-out or other-group creator was opened or scanned. `llm/labels/holdout`,
`llm/labels/other` and the reliability folders were never opened, and no recursive search was run over the run folder.

Reads that are not contacts (instruments, code, rules, identifier lists and metadata, D31; seen-only stores):

| When (UTC) | What | Why |
|---|---|---|
| 12:32:11 to 12:44:25 | deposit 3, deposit 2, the programme, the lead's rulings and step 1's public files (git `origin/main`, merge 6701474); `step2/lead-step2-decisions.md`, `step1/lead-step1-decisions.md`; `step2/lead-extract-memo-definitions.md` (definitional sections of the memos, no corpus figures) | instruments and rules; no data |
| 12:32:11 to 12:44:25 | r3-P42's README, run record, prespecification, status, public files and code (`analyse_p42.py`, `count_p42.py`, `extract_p42.py`, `p42common.py`, `publish_p42.py`, `plot_p42.py`); the shared matcher; step 1's `pubrules.py`, r3-P04's `common.py`, r3-P05's `p05_run.py` and `p05_publish.py`; MR's `mrcommon.py`; the frozen package's `voice_sets.py`, `constants.py`, `adapter.py`; PT's `ptcommon.py`; the scan scripts | loaders and rules to reuse (code, not data) |
| from 12:50:29 | r3-P42's private extract and counts (the 23 non-development seen creators only) | the run's inputs; no transcript was read again |
| 12:50:29 to 12:52:50 | the seen-only bundle through MR's `mrcommon.load_bundle()` (`adapter.load_seen_bundle`: `labels/seen` voice, asks and features files; group checked before any field is read); only the 23 creators' recordings kept | own-voice talks (r3-P52), middle-model sides (r3-P51), asks and unit times (r3-P56) |
| 12:52:50 and 13:02:14 | PT's seen-only `page_text()` (titles and descriptions of seen recordings); only the extract's recordings kept | page text for r3-P50 |
| 12:59:24 onward (each analysis run) | step 1's `pubrules.known_register()` (`llm/creator-sets.json`, `bridge-ledger.jsonl`, the grid-shift plan, MR's and E's printed groups, step 0's split) | the nested-count rule (seen-only creator sets; identifier lists and metadata) |
| 13:16 to 13:19 | the staged public files (copies of step 1's published tree and these entries' `public/`, in a scratch folder) and `llm/creator-sets.json` with the extract's audio hashes and video ids as needles | the privacy solvers and the identifier scan (public files only) |

Every time above is UTC from `date -u` (ranges bracketed by stamps taken with `date -u`).
