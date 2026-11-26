# r3-P36 / r4-P21: a calendar null tested where it can fail; which calendar the dated windows keep

Third-round programme, step 3 (forecasts and time), class a.1. The programme pairs r4-P21 with r3-P36 ("r3-P36 /
r4-P21"), so r4-P21 sits in this folder; its anchor-class half is in `../r3-P37/`. Written 2026-11-26 by a step-3 agent
(a model agent working for the project lead; not a person); times from `date -u`. Exploratory; not a test of H1-H10.
Windows and absolute types are model-coded (LAB-F's FE; TL-BUILD); the deixis typing is the frozen ledger's rule coder;
nothing is checked by a person. Never "recede".

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Design

Prespecification: `prespec.md` (hashed 2026-11-26T14:11:40Z, before any outcome; `prespec-hash-record.md`). TL-7.1's
estimand: within a channel, the slope of the window midpoint on the upload day (1 = constant lead, 0 = fixed target), on
confirmed upload days, for channels with 3 or more units over 60 or more days. Relative and period-framed windows give a
constant lead by construction (D15), so only **explicit absolute windows** are used: closed windows that do not rest on
the talk-level period alone and are model-coded absolute (a year or an event-table day).

- **Tiers.** The rule-typed panels (calendar unit; doubly absolute) and r4-P21's typing are **tier L** (the 23
  non-development creators). The pooled panel uses model-coded fields only; fewer than 10 of the non-development creators
  are eligible, so it is **tier D**: a description on every eligible seen channel (the tuning pool included, as TL-7.1
  was), "no overfitting check possible".
- **Interval and reading.** 90% t interval on channel slopes, fixed in advance. r3-P30's class F_slope holds no interval
  method at any count below 71, so every reading is capped at "undetermined" whatever the data. Reading words: the
  register's pointer (stat): "closer to a rolling horizon" / "closer to fixed events" / "undetermined" around the
  midpoint 0.5. Reference: TL-7.1's within-channel permutation of upload days (9,999 draws), 95% band.

## Results

**The count first** (`public/data-r3-P36-explicit-count.csv`): 241 explicit absolute window units on 40 to 49 seen
creators (confirmed days); 90 units on 10 to 19 of the 23 non-development creators.

**Slopes** (`public/data-r3-P36-slopes.csv`, `public/fig-r3-P36-slopes.png`):

| Row | Channels | Mean slope | 90% interval | Permutation band (95%) | Reading |
|---|---|---|---|---|---|
| Pooled: explicit absolute windows (tier D) | all but fewer than 5 of TL-7.1's primary channels (printed there as 10-14) | -5.17 | -17.80 to 7.46 | -10.60 to 10.79 (inside) | undetermined (capped); description only |
| Control: year-flagged statements out (tier D) | not computed or not printed | | | | not computed or not printed |
| Tier L: pooled; calendar unit year; calendar unit month; doubly absolute | not computed or not printed | | | | not computed or not printed |

Channel span (the newest-20 quota): the across-channel coefficient of channel slope on channel span is 4.70 per 100 days
(90% interval -5.75 to 15.15), described; bins of 5 or more channels are not drawn because values that could narrow a
banded count are not printed.

In words: once windows taken from the talk's period are left out, the mean within-channel slope on explicit absolute
windows is very imprecise and lies inside the permutation band; it cannot be told from 0, from 1 or from the permutation
reference. **The calendar null cannot be distinguished from a calendar habit here.** TL-7.1's published slope near 1
(above its band) pooled period-framed windows with explicit ones and weighted channels by precision
(DerSimonian-Laird); this description changes both the unit set and the estimator, so the difference cannot be put on
either change alone. N20's decomposition by calendar unit and the doubly absolute panel do not print on tier L.

**r4-P21, which calendar the dated windows keep** (`public/data-r4-P21-typing.csv`, `public/fig-r4-P21-typing.png`;
tier L, closed windows, creator-balanced):
- the rule-based form-and-function cells (absolute in both; naming the current, next or an earlier period; deictic form;
  event-anchored; unbounded; none in the statement text): **not printed** (a pooled cell rests on fewer than 5 creators);
- the unit of calendar-absolute forms (10 to 19 creators): year names 0.613; month and decade names
  not printed (privacy rule);
- FE's model-coded kinds (shares of closed-window statements holding each; not exclusive): month 0.190, year or range
  0.235, season or part of a year 0.164, counted span 0.136, named relative period 0.253; calendar day and event-fixed
  times not printed (fewer than 5 creators).
The typing is TimeML's anchored-against-absolute distinction and is not claimed as new.

**Predictions scored:** none deposited (deposit 2's cells for r3-P36 and r4-P21 are silent).

**Not computed or not printed:** the control row and every tier-L slope panel (the decomposition by calendar unit, the
doubly absolute panel, the pooled panel on tier L); the deixis-cell bar; the channel-span bins.

Multiplicity: 56 primaries; about 2.8 readings A would be expected by chance if every true effect sat at half its margin.

## Departures

- The slope interval is a fixed t interval on channel slopes, not r3-P30's count-chosen method for class F_slope: no
  method holds for that class below 71 channels, and a fixed method keeps the description printable under a banded count
  (decision 62). Stated in the prespecification.
- The slope is not a measure type of deposit 2's margin table; the register's pointer (stat's round-4 rule) gives the
  reading words, capped by r3-P30. Stated in the prespecification.
- The programme's plot asks for the slope against channel span in bins of 5 or more channels; one coefficient is printed
  instead (privacy; stated in the prespecification).
- The pooled panel describes the tuning pool's channels with the rest (tier D). Stated in the prespecification.

## For the lead (settled)

- **Settled** (the lead's decision 84): N20's decomposition and a calibrated precision-weighted slope method go
  on the fourth panel's agenda, with a larger tier; until then every slope reads "undetermined".
- N20's decomposition (calendar unit; doubly absolute) cannot print on tier L. Running the frozen typing on the tuning
  pool would be a new registration (as decision 65 item 1 put it for the lexicons).
- An unweighted mean of channel slopes is dominated by imprecise channels; r3-P30 calibrated no precision-weighted method
  that holds for F_slope. A calibrated weighted method would be needed before any slope can read other than undetermined.

## Files

`prespec.md`, `prespec-hash-record.md`, `code/p36_run.py`, shared code in `../ft-common/code/`, `public/` (three CSV files,
two figures as PNG and PDF), `contacts.md`, `status.json` (hashes). `private/results.private.json` (per-channel values) is
never published.

## Changes at the joint staging of steps 3 to 5 (2026-11-26T14:59:32Z, UTC from `date -u`)

- **Stated against each other (the lead's decision 72).** r3-P38's eligible creators and r4-P21's tier-L creators
  with a closed window (the base of its deixis typing) are each printed as "all but fewer than 5 of 23"; by
  definition both lie inside r4-P23's tier-L creators with ledger statements, which is also printed as "all but
  fewer than 5 of 23". All three are stated against the same 23 and nest inside one another, so no printed form
  narrows another (checked at the joint staging with the private counts). No number or form changed.
- **Fixed 90% t intervals** in place of r3-P30's count-chosen methods are accepted (the lead's decision 82); every
  slope reads "undetermined" until a calibrated precision-weighted slope class exists (decision 84; the fourth
  panel's agenda, with N20's decomposition on a larger tier).

## Change by the lead's decision 99 (2026-11-26T16:19:27Z, UTC from `date -u`)

- The month and decade shares of r4-P21's calendar-absolute forms are not printed (privacy rule), and a count form
  in the tier-L panels was changed. The CSVs, both figures (redrawn by this entry's own plot functions; the typing figure's code now names
  the units whose share is not printed) and this README were changed. No number changed.

## Change by the lead's decision 103 (2026-11-26T17:16:20Z, UTC from `date -u`)

- Some rows read "not computed or not printed"; count forms are made uniform. The slopes CSV, its figure (redrawn by this entry's own plot
  function, which now names withheld rows) and this README were changed; the settled notes to the lead are marked.
  No number changed.

## Change by the lead's decision 104 (2026-11-26T17:33:22Z, UTC from `date -u`)

- Rows not computed and rows not printed carry one label ("not computed or not printed") in their count, method and status
  cells and are listed together; change notes are worded in general terms. The CSV, the figure (redrawn by this
  entry's own plot function) and this README were changed. No number changed.
