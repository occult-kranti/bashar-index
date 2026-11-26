# r3-P28: prespecification of the funding ladder (written before any price of this entry is computed)

Third-round programme, step 1, class a.1 (writing; it funds nothing). Written by a step-1 agent (a model agent working for
the project lead; not a person). Exploratory; not a test of H1-H10. No model call, no network call; nothing is sent.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What the programme fixes

r3-P28 prices the unfunded arms against the ledger and says what each buys (accuracy, counterfactual sensitivity,
comparability over time); it funds nothing. Builds on rv-D8 and the not-run rows that need model calls (HR, TL-SPEC,
TL-7.3, VER-ADJ-G, NE-F, CSS-11). Plot: a funding ladder, arms on a log-cost axis with the 2-USD reporting line and the
person check (r3-P25) as the reference purchase. Deposit 2: kind "act", no margin, no reading.

## Sources (amounts only)

- **Price table:** `llm/openai_client.py` `PRICES` (USD per million tokens, input, cached input, output, per interface
  and model), `RUNAWAY_CEILING` (130), `TOTAL_CAP` (120), `TAG_CAPS`. The key file is never opened.
- **Spend records:** `llm/spend.jsonl`, read for amounts only: phase, tag, kind, interface, USD, token counts, request
  counts, and the purpose string reduced to its instrument words (any identifier masked before use; nothing printed but
  sums). Group words in purposes ("seen", "holdout") are used only to pick seen-creator anchors.
- **Members' estimates:** programme section 2.3's table (the unfunded arms, in the panel's spending order) and the
  registry's money rows (HR part a; tier lines).
- **Sizes:** stored counts already published (1,293 English recordings of the 71 seen creators; BR-GS's 40 grid-shift
  recordings; 9,033 coded forecast statements and the 27% bounded share; asks found; units coded).

## Pricing rule (fixed here)

1. **Ledger anchor** of an arm: the measured seen-creator job of the same instrument and model that the arm would re-run
   (or the closest named analogue), as measured USD per request and per recording or item: total measured USD of the
   job's rows divided by its completed requests (and by its recordings where the base is the recordings).
2. **Size:** a stored count of the units the arm would read; where the programme fixes no size and no stored count
   applies, the row prints the anchor's price per item and the members' estimate only ("size not fixed").
3. **Range:** low end = size x anchor price at the batch interface (the price table's batch prices are half the
   standard ones for every model, so a standard-measured anchor is halved); high end = size x anchor price at the
   standard interface x 1.25 (the registry records the small model's batch queue returning nothing for hours, so the
   standard interface is the realistic fallback; 1.25 covers repeats and answers lost in transport, which the ledger
   holds as allowance rows).
4. **Flags:** "report to the lead first" when the high end (or the members' high estimate) exceeds 2 USD; "above the
   headroom" when it exceeds the hard stop minus the ledger's committed sum; "a hold-out contact" when the arm would read
   hold-out material (HR, VER-NEXT, R-hold re-reads), which the programme sets aside (r3-P73).
5. **What it buys** (one class per arm): accuracy (only a person check); counterfactual sensitivity (an arm that changes
   one input and re-reads); precision or recall of a cue list or finder; a new field; comparability over time (anchor
   re-reads, drift, transport); outcome resolution; wave and comparison labels.
6. Human-coder arms are printed in hours and at the members' USD where given; they are not priced from the ledger.

## Outputs

`r3-P28-funding-ladder.csv` (every arm: entry, kind, members' estimate, ledger anchor and its per-item price, size and
basis, priced range, flags, what it buys); `r3-P28-ledger-anchors.csv` (the anchors: instrument, model, interface,
measured USD, requests, USD per request); `r3-P28-budget.csv` (hard stop, warning, committed sum, headroom, the closed
discovery cap); `fig-r3-P28-funding-ladder` (arms on a log-cost axis, members' range as a bar, ledger range as a thicker
bar, the 2-USD line, the headroom line, r3-P25's minimal person check as the reference band). The annotation protocol is
text in the README.
