> Redacted copy: 1 private path replaced; the hash recorded at hashing time is kept privately.

# r3-P20 prespecification: why reliability did not transport (gate ladder, disagreement model) and the registered prediction

Written 2026-11-26T06:31:30Z (UTC, from `date -u`) by a step-1 agent (a model agent working for the
lead; not a person), before any seen-outside-G agreement, decile agreement, disagreement-model coefficient or prediction
of this entry was computed. Deposit 2 was merged before; nothing here is tuned on outcomes. Exploratory; not a test of
H1-H10. Seen creators only for every computed value; the gate-sample (G) and hold-out (R-hold) rungs are the published
values of `exploratory-2026-11-21/built/GATES/public/GATES-gates.csv` (and rv-D2-H's published covariate summary), copied,
never recomputed: no hold-out file is opened.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**What this agent had seen before writing it.** The published G and R-hold gate values (GATES), rv-D2-H's headline
(hold-out English creators: lower recognizer confidence, SMD about -0.8), nlp-R13, rv-L2, VER-*; the voice gate-rerun
notes of G (`llm/pilot2/gate-rerun.md`). No agreement on seen recordings outside G had been computed or seen.

## The ladder (one row per instrument statistic)

Rungs: (1) G, published; (2) **seen outside G**, computed here; (3) R-hold, published; (4) the published floor.
"Outside G" (primary): seen recordings not in the gate sample's recordings (voice G: `llm/pilot/set-g.private.json`;
asks: the asks gate's G recordings; titles: titles of videos not read in the titles gate on G; forecasts: statements of
recordings not in G). Secondary row: creators with no recording in G.

| Instrument | Statistic (as the gate defines it) | Rung 2 computable? |
|---|---|---|
| voice | Cohen's kappa claimed / own / other, small against middle, over words (gate D) | yes: recordings the middle model labelled in full |
| voice | kappa embodied / own / other (gate D) | yes |
| voice | stability over runs (gate C) | not stored outside G (production labelled once) |
| asks | specific agreement on K1, small against middle check, on ranges both read (gate D) | yes: both checks are stored per range |
| forecasts | class of record F1-or-not, small against middle (gate D) | not stored outside G (the middle critic read only routed candidates) |
| forecasts | commitment, small against middle | not stored outside G (no second commitment reading) |
| forecasts | checkability parts time window, named actor, observable outcome: record (middle) against small, 3 values | yes: fc and fc_second per statement |
| sentence codes | stability; kappa small against middle | not stored outside G (one reading) |
| titles | presentation (4 codes) middle against small kappa; source family kappa; P1-or-not kappa | yes |

Kappa as `voice_gate_stats.kappa` (unweighted Cohen's kappa over the pooled table); specific agreement 2a / (2a + b + c).
Every computed agreement figure follows the rule of 2026-11-21 22:33: printed only where the positive code (each code of
the table) comes from 5 or more creators in each reading and the creators with an item coded differently are 0 or 5 or
more; otherwise "not published (fewer than 5 creators)", with codes pooled by VER's rule where that lets it pass.

**Reading per row (the transport gap).** Gap = rung 2 minus rung 1 (G published, treated as fixed). Margin: deposit 2's
0.10 for agreement coefficients. A "the seen value outside G differs from G beyond the margin" if the 90% interval of
the gap lies wholly beyond +-0.10; B "transports within the margin" if wholly inside; undetermined otherwise. Interval:
90% creator-cluster bootstrap, percentile, 2,000 draws, seed 2026112620; r3-P30 holds no class for pooled kappas: flagged
"interval method not calibrated by r3-P30 for this design class". The R-hold rung is described against rung 2 only as
"inside" or "outside" the rung-2 interval widened by R-hold's own published half-width (chance), never read A or B.

## Agreement against quality decile

Quality of a recording: mean word probability of its kept (filtered) words, from the seen word cache
(the paper review's private cache file). Bases: voice (rung-2 recordings; kappa
claimed / own / other over words per bin) and checkability time window (rung-2 statements, by their recording's quality).
Bins: deciles of recording quality (recordings ranked; equal counts); if any decile fails the 5-creator rule or the 22:33
rule, quintiles; then terciles; cut points are not printed. Bin kappa with its 90% creator bootstrap interval.

## Disagreement model

- Voice: units of the rung-2 recordings; outcome: the small and the middle model's groups differ (claimed / own / other);
  logistic regression weighted by unit words, predictors: recording quality (z over recordings, between-creator SD
  units: divided by the SD of creator means of quality), the unit's deviation of mean word probability from its recording
  (z), log unit words, edge (unit in the first or last tenth of the recording's words), map format (solo reference;
  mixed, conversation, audience session, unclear pooled with mixed). Coefficients with 90% creator-cluster bootstrap
  intervals (1,000 draws).
- Checkability time window: statements of rung-2 recordings; outcome: record and small differ; predictors: recording
  quality (same scale), log statement words.
- **Counterfactual (transcript quality).** Every recording's quality shifted by -0.8 between-creator SD (rv-D2-H's
  published SMD for recognizer confidence, "about -0.8"), units' deviations kept; predicted word-weighted disagreement,
  and the implied kappa = 1 - P(disagree) / (1 - P(chance agreement)), chance agreement held at its rung-2 value. Printed
  beside the G, rung-2 and R-hold values.

## What the ladder separates (descriptive words, fixed now)

- **Overfitting or selection on the gate sample**: the transport gap (rung 2 minus G).
- **Transcript quality**: the counterfactual change at the hold-out's published quality shift.
- **Chance**: whether R-hold's published value lies inside the rung-2 interval widened by R-hold's published half-width.

## The registered reliability prediction (class b, registered with r4-P07; written now, not tested)

For each rung-2 statistic, a 90% prediction interval for a wave's reliability sample, in the 2 x 2 of r4-P07 (model
snapshot: same / new; material: new uploads of known (seen) speakers / fresh speakers):
- known speakers, same snapshot: rung-2 estimate +- 1.645 x sqrt(SE_boot^2 + SE_R^2), SE_boot the rung-2 bootstrap SD,
  SE_R = R-hold's published 90% half-width / 1.645 where R-hold publishes an interval for that statistic, else SE_R =
  2 x SE_boot;
- fresh speakers, same snapshot: the union of that interval and the same interval shifted by the counterfactual change
  (voice and checkability time window; other statistics: the known-speaker interval, with "no quality model" stated);
- new snapshot: the same intervals; the prediction states no drift (VER-NEXT did not run), so a drift moves the value
  outside them. Season is a named confound.
The prediction file is written once, hashed with `date -u`, and never revised; it is not compared with any data here.

## Rules

No cell, bin, bar or plotted group on fewer than 5 creators; counts through r3-P01's `pubrules.Register`; no per-creator
or per-recording value published; "agreement" or "consistency", never "accuracy"; multiplicity: 56 primaries, half-effect
disclosure as r3-P30 prints it.
