# r3-P28: hold-out and other-group contacts

Written by the step-1 agent of r3-P26, r3-P33 and r3-P28 (a model agent working for the lead; not a person). Times are in
status.json (UTC, from `date -u`).

**No hold-out or other-group contact was made.** No file holding measured values (labels, text, features) of a
hold-out or other-group creator was opened. The key file was not opened, read or printed.

Reads that are not contacts:

| What | Why |
|---|---|
| `llm/openai_client.py` | the price table and caps, parsed as text (not imported, not run); the key-reading function was skipped when the file was printed |
| `llm/spend.jsonl` (the cost ledger), at about 06:21Z, 06:44:35Z and 06:47:42Z | read for amounts only, as the brief directs: phase, tag, kind, interface, USD, token and request counts; purpose strings were masked (identifiers replaced) before any use. The ledger holds one row per paid event of every group, including hold-out labelling runs and R-hold reliability runs; their amounts enter only the ledger's sum (the committed spend). No identifier, label or text is in what was kept or printed |
| the published programme, the registry and the exploratory round's status table | members' estimates and the registry's money rows |

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

Exploratory; not a test of H1-H10.
