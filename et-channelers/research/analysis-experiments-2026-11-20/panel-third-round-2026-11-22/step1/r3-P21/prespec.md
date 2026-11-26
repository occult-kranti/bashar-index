# r3-P21 prespecification: a drift audit of the frozen instruments

Written 2026-11-26 at about 06:34Z (UTC, from `date -u`; the exact time and this file's SHA-256 are in `prespec-record.md`) by a
step-1 agent (a model agent working for the lead; not a person), before any snapshot string, interface count or coded
value was tabulated. Looked at first, outcome-free: the names and sizes of the answer stores in `llm/answers/` (a
directory listing; no store of a hold-out, other-group or reliability run was opened), the field names of the first row of
three seen-side stores, the runner's and client's code (`runner.py`, `openai_client.py`, `fc_common.py`: what a stored
row holds and how a request id is made), and the frozen model aliases in `freeze.json`. Deposit 2 was merged before
this entry started.

Exploratory; not a test of H1-H10. Seen creators only for coded values. Every label is model-coded and not checked by a
person; agreement, never accuracy. No model or API call.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## The question (programme 2.1, r3-P21; margins register: a description, no margin)

(1) Did the model aliases resolve to one snapshot throughout? (2) Did the two interfaces (batch and standard) code
alike? Plot named by the programme: agreement with the record against the time gap between readings, by interface, over
the run-to-run band. The anchor re-read at a wave is class c and is not run.

## Sources (and what is never opened)

- **Read (run-ledger metadata and seen-side answer stores):** `llm/batch-jobs.jsonl` and `llm/spend.jsonl` (ledgers:
  tags, interface, requested model, times, counts; no coded value); the answer stores whose tag does not match the
  runner's unseen pattern (`holdout|rhold|other`, any case) and does not begin with `rel-` (reliability runs, closed by the
  lead's decision 11): production seen stores (`prod-*-seen*`), pilot, gate and panel stores (`pilot-*`, `p2-*`, `p3-*`,
  `p3b-*`, `p4-*`), second readings and PT (`r2-DBL-*`, `r2-PT`), smoke, probe and self-test stores, and the discovery
  store `r2-DISC` (candidate channels outside the roster; only its metadata fields are read).
- **From each row only:** `custom_id`, `status`, `tier`, `model` (the string the API returned), `at`, and whether
  `adopted_from` is present. The `text` field (the coded value) is read only in part 2, only for items found to be coded
  under both interfaces in a seen-side store.
- **Never opened:** any answer store of a hold-out, R-hold, other-group or reliability run; `llm/labels/holdout`,
  `llm/labels/other`; the reliability folders. Their snapshots are therefore reported as "not read (the stores hold
  hold-out or other-group values)"; their interface and time come from the ledgers only.

## Part 1: alias to snapshot

- For each requested alias (the price key of the returned string, `runner._priced`), the distinct returned strings, with
  counts of answered rows (status completed, incomplete, refused or empty) by interface and store group (production
  seen; pilot and gate; second readings, PT and discovery; smoke, probe and self-test), and the first and last `at` of each.
- Rows that carry no `model` field (error rows, or rows written before the field existed) are counted apart as "no
  returned string".
- **Wording:** "one snapshot per alias throughout the stores read" if every answered row of an alias names one string;
  otherwise "more than one snapshot", with the time each string first and last appears. A tabulation, not an estimate: no
  interval and no margin.

## Part 2: did the two interfaces code alike?

- **Items coded under both interfaces:** a request id with an answered row (status completed) under each interface in
  the same seen-side store. A request id holds the run tag, the hash of the input text and (for the forecast and newer
  instruments) the prompt signature, so two answers under one id answer the same request. Rows copied by adoption
  (`adopted_from`) are not independent readings and are left out.
- **If such items exist:** agreement = share of items whose two answers, parsed as JSON, are identical; per-field
  agreement on the label fields as a row. The creator of an item is not stored in the answer row; it is recovered only if
  the instrument's own request builder can be re-run on seen inputs without any call. A share is printed only on 5 or more
  creators (and with the time gap between the two readings, in hours); otherwise the count of such items is printed as a
  band and the agreement "not published (fewer than 5 creators, or creators not recoverable)".
- **If no item was coded under both interfaces:** the entry prints "not computable from stored runs".
- **The run-to-run band and agreement against the time gap**, as the programme draws them, need repeated readings matched
  item by item. Repeated gate runs are stored under separate tags whose request ids differ by tag, and an answer row holds
  no item key, so matching needs the instruments' request builders re-run on the gate inputs. That is not done here (it
  touches gate-sample texts beyond this entry's metadata scope); stated as not built, with the published stability
  figures (GATES, VER-SHARD) cited in words, not recomputed.

## Plot

If part 2 is computable: the programme's plot. If not: the alias-to-snapshot timeline (time on the x axis; one row per
alias and interface; marks per store group, sized by answered rows in bands), with "not computable from stored runs"
written on it. Counts in figures are of answered rows (requests), never of creators; no creator count is printed.

## Privacy

No creator, recording, id or title appears; request ids and batch ids are not printed; tags are printed only as store
groups. Every public file carries the agnosticism sentence and "exploratory; not a test of H1-H10".
