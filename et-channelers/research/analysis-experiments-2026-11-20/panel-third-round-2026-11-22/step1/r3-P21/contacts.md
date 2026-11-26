# r3-P21: hold-out and other-group contacts

Written 2026-11-26T06:47:04Z (UTC, from `date -u`) by the step-1 agent of r3-P07, r3-P21 and r3-P27 (a model agent; not a person).

**No hold-out or other-group contact was made.** No file holding values of a hold-out or other-group creator was opened
or scanned. The 24 answer stores of hold-out, R-hold, other-group and reliability runs (the runner's unseen pattern and
the `rel-` prefix) were never opened; `llm/labels/holdout`, `llm/labels/other` and the reliability folders were never
opened; no recursive text search was run.

Reads that are not contacts:

| What | Why |
|---|---|
| `llm/spend.jsonl`, `llm/batch-jobs.jsonl` | run-ledger metadata (tag, interface, requested model, times, counts, batch states), including rows of hold-out runs: metadata, not a contact (the brief; D31) |
| 126 seen-side answer stores in `llm/answers/` | fields `custom_id`, `status`, `tier`, `model`, `at`, `adopted_from` only; `text` never read |
| directory listings of `llm/answers/` and `llm/logs/` (names and sizes) | to choose the seen-side stores; the names are run tags (for example a hold-out run's tag), not recording or creator identifiers; no such file was opened. **For the lead:** recorded here in case the lead wishes to rule on listings of run-tag names (by analogy with D31, they carry no hold-out value). |
| `llm/logs/seen-voice.txt`, `seen-voice-labels-small-standard.txt` (first lines) | seen run logs (interface and request counts) |
| `llm/freeze.json`, `freeze2.json`, `config.json` (keys and model aliases), `runner.py`, `openai_client.py`, `fc_common.py` | instrument metadata and code |

Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
