# Prespecification: r3-P36 (forecast structure: a calendar null tested where it can fail), carrying r4-P21 (which calendar the dated windows keep: TimeML typing)

Written 2026-11-26 between 14:09:41 and 14:11:29 UTC (both from `date -u`; the second is the first hashing; corrected and hashed again below) by a step-3 agent (a model agent working for the project lead; not a
person), before any outcome of this entry was computed. Its SHA-256 and the time of hashing are in
`prespec-hash-record.md`. Exploratory; not a test of H1-H10. No model or API call, no download.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Programme.** `programme.md` 2.1 step 3 ("r3-P36 / r4-P21"; a.1, after the ledger hash and r3-P30); the decisions file
(r3-P36 carries r4-P21 in part; r4-P21's other carrier, r3-P37, holds the anchor classes); the register's pointer for
this entry (stat's round-4 readings for the slope); deposit 2; the lead's common rules for steps 3 to 5. The programme
pairs r4-P21 with r3-P36, so r4-P21 sits in this folder. "Never 'recede'."

## 0. What was seen before this file

- Published: TL-7.1 (on the channels eligible under the protocol rule, confirmed upload days: a pooled slope near 1 with
  a 90% interval of about 0.38 to 1.50, above the within-channel permutation band; frame-only windows included), TL-7.7
  (about 65% of dated statements take their window from the talk's period), TL-BUILD, LAB-F's gates, TIME; step 1's r3-P30
  grid (design class F_slope: no interval method holds coverage at any simulated count below 71); deposits 1 to 4; the
  round memos of stat, ling, den-meth, den-soc and et on this entry, and the synthesis's K2.
- The frozen ledger's field structure (one row's fields, text redacted) and outcome-free counts
  (`../ft-common/code/eligibility.py`, SHA-256 `d31d2f48...3763c`): per creator, the number of explicit absolute window
  units and their upload-day span, by panel, on the 23 non-development creators and on all seen creators. No slope,
  window midpoint or permutation was computed.

## 1. Units, panels and tiers

- **Units.** Ledger statements (frozen ledger, SHA-256 `d2e8e3fd...a80a`, checked before use) with a closed window
  (`lane` closed), an upload day, and these properties:
  - **explicit absolute window** (D15: relative and period-framed windows give a constant lead by construction): not
    frame-only (the window does not rest on the talk-level period alone) and model-coded absolute (FE's year or
    event-table day, TL-7.1's absolute class). This count is printed first.
  - **calendar unit** (N20; ling's typing, the ledger's rule-based deixis field): the rule form is calendar-absolute and
    the unit is a year or a month name;
  - **doubly absolute**: the rule cell "absolute in both" (a named year, decade or month that is neither the current nor
    the next period of the upload day).
- **Slope** (TL-7.1's estimand): within a channel, the least-squares slope of the window midpoint (days) on the upload
  day (days) over the channel's units; b = 1 is a constant lead, b = 0 a fixed target. Confirmed upload days only.
  **Eligible channel:** TL-7.1's protocol rule, 3 or more units over 60 or more days of upload days.
- **Tiers** (outcome-free counts, printed as bands):
  - Panels typed by the ledger's frozen rule coder (calendar unit; doubly absolute) and r4-P21's typing table are
    **tier L**: once on the 23 non-development creators, no split. The eligible channels number "fewer than 5" for every
    rule-typed panel, and for the pooled panel too, on these creators. These rows print "not computed (too few
    creators)"; this is known before any slope.
  - The **pooled panel** (explicit absolute windows; model-coded fields only, no rule coder) is an "other entry": fewer
    than 10 of the non-development creators are eligible, so it is **tier D**: a description only, labelled "no
    overfitting check possible", described on every eligible seen channel (the tuning pool included, as TL-7.1 was), with
    the year-flagged statements left out as its control row (TL-7.1's).

## 2. Estimates, references, intervals and readings

- **Estimate:** the mean of channel slopes. **Interval:** 90% t interval on channel slopes, a fixed method (stat's round-4
  memo: "a t interval on channel slopes"). r3-P30's design class F_slope fits this design, but at every simulated count
  below 71 no method holds coverage, so the table offers no calibrated choice; the fixed method keeps the description
  printable under a banded count (decision 62 exempts fixed methods), and the reading is capped as below. The
  DerSimonian-Laird pooling of TL-7.1 is not used.
- **Reference:** TL-7.1's within-channel permutation of upload days among each channel's recordings, 9,999 draws, the
  same estimator (mean of channel slopes); its 95% band (TL-7.1's level) and the share of permuted values at least as
  far from 0 as the observed one.
- **Readings.** The slope is not a measure type of deposit 2's margin table; the register's pointer (stat's round-4
  rule) is used as the reading words: "closer to a rolling horizon" if the near 90% bound lies above the midpoint 0.5,
  "closer to fixed events" if the far bound lies below 0.5, otherwise "undetermined". r3-P30 caps every reading of
  class F_slope at "undetermined" below 71 channels, so every slope row here reads "undetermined" whatever the data; the
  estimate, interval and band are described. As a tier-D row the pooled panel is a description in any case.
- **The calendar null.** On relative and period-framed windows the null cannot fail (a constant lead by construction);
  they are not estimated. On explicit absolute windows it could fail only through a reading other than "undetermined";
  with r3-P30's cap the programme's expected wording applies: "cannot be distinguished from a calendar habit here". Never
  "recede".
- **Channel span** (the newest-20 quota; den-meth): the span of each eligible channel's unit upload days. Bins of 5 or
  more channels would print group sizes beside a banded count, so the span view is one across-channel least-squares
  coefficient of channel slope on channel span (per 100 days) with a 90% t interval (df = channels - 2), described.

## 3. r4-P21: which calendar the dated windows keep (tier L, description)

On the 23 non-development creators, every closed-window statement with an upload day: creator-balanced shares (each
creator with a closed window weighs equally) of the ledger's rule-based deixis cells (absolute in both; absolute form
naming the current period; the next period; an earlier period; deictic form; event-anchored; unbounded; none in the
statement text) and, for calendar-absolute forms, of the unit (year, month, decade); FE's model-coded kinds (D1 to D7)
beside, as the model-coded typing. Cells where fewer than 5 creators have a non-zero share are pooled into "other cells
(pooled for privacy)", and a pooled cell that still rests on fewer than 5 creators is not printed (with the bar it would
let a reader complete). The typing is TimeML's anchored-against-absolute distinction (ling; den-meth) and is not claimed
as new; only N20's decomposition by calendar unit would be, and it is not computed here.

## 4. Privacy, predictions, plots, seeds

- Privacy: the lead's common rules and step 1's `pubrules.Register` (copied with its hash) for every count; the pooled
  panel's channel count nests in TL-7.1's printed band and is printed in a band; no group means that solve for sizes; no
  per-channel values, minima or maxima.
- Predictions: deposit 2's account cells for r3-P36 and r4-P21 are silent. Nothing is scored.
- Plots: `fig-r3-P36-slopes` (the pooled panel and its control row against the permutation band, with lines at 0, 0.5
  and 1; the rule-typed panels marked "not computed (fewer than 5 eligible channels)"; the span coefficient beside);
  `fig-r4-P21-typing` (creator-balanced stacked shares of the typing cells, tier L).
- Seeds: the first 8 hex digits of SHA-256("r3-P36|<stream>|step-3") as an integer, `numpy.random.default_rng([seed,
  k])`; stream "permutation". 56 primaries; deposit 2's half-effect disclosure printed.
