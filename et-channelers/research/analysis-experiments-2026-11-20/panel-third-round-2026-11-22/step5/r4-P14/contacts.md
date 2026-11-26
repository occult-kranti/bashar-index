# Contacts (step 5)

Written 2026-11-26T14:34Z (UTC, from `date -u`) by the step-5 agent (a model agent working for the lead; not a person).
Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Contacts: none.** No file of a hold-out, other-group or reliability folder was opened, listed or searched; no recursive
text search ran over the run folder; no model or API call, no download, no audio, no git commit.

Reads (all seen-only; not contacts):

| Time (UTC) | Read | Through |
|---|---|---|
| 14:01Z | voice labels of the 71 seen creators (unit sides, word counts, map fields); rv-R3's bridge-pair list; the split; r3-P42's private counts | `adapter.load_seen_bundle` (labels/seen only); `common/code/eligibility.py` |
| 14:04Z | step 1's stored-membership register; step 2's full count register | `pubrules.known_register()`; `step2/r3-P48/private/count-register-full.private.json` |
| 14:13Z to 14:15Z | the seen transcripts (English-only model of record), the voice labels, RX's stored cue hits (CROSS transcript pass, seen records only), rv-R3's bridge pairs (seen) | `prep.load_units` (seen guard), 3 worker processes passed one creator's rows each; `common/code/extract_s5.py` |
| 14:22Z | step 2's description extract (L10 hits of the 23 non-development creators) and r3-P42's counts (hash checked) | `step2/r3-P48/code/desc_common.py` (r3-P16 only) |

The whole-position scan writes its JSON into the release scans' `out/` folder by design; the step-5 file was moved to
`common/private/solvers/` at 14:31Z. No other file outside `step5/` was written.
