# rv-R2: can each registered rule reach a verdict at the eligible numbers of creators?

Exploratory (registry A2); not a test of H1-H10. Paper-review build item (built 2026-11-21; label "Exploratory, paper
review (registry A2/A7); not a test of H1-H10"), released in the public form of plan section 3 by the release review
(plan P10, 2026-11-22). Calibration of the registered rules, not tests of the hypotheses.

## What it asks

For each registered hypothesis H1-H10: how does the registered test behave under a creator-level placebo, does its
interval cover, what power does it have at the smallest effect of interest, how many hold-out creators are projected to
be eligible, and can it pass the first Holm step (0.005) at that number? A plasmode asks whether a wave of the same
creators could replicate a seen look.

## Base

- CAL's simulations on label-free analogues computed from seen creators (the analogues carry no labels and are not
  hypothesis quantities).
- Projected eligible hold-out creators: CAL's creator-property bound, simulated from pilot rates and the run ledger's
  English recordings per hold-out creator (not a contact); H5 an upper bound from pilot titles. These are projections,
  not counts of creators. The label-based re-projection, CAL-f (package CROSS), supersedes them and prints shares of
  the hold-out creators with English recordings.
- Plasmode: real seen cluster sizes (71 creators, 1,222 recordings) and real within-creator pace residuals.

## What is shown

| File | What it holds | Place |
|---|---|---|
| `public/rv-r2-calibration-eligibility.csv` | One row per hypothesis: state, placebo rejection, coverage, power, minimum, projection, smallest attainable p, type S and M | M |
| `public/rv-r2-projected-eligible.csv` | The eligibility dot plot's numbers | M |
| `public/rv-r2-power-curves.csv` | Power curves (CAL; normal model for H1-H4) | S |
| `public/rv-r2-type-sm.csv` | Power, type S and type M at the projected numbers | S |
| `public/rv-r2-plasmode.csv` | The persistence plasmode | S |

Figures (in the gallery, with their records in its `manifest.json`): rv-R2-a eligibility dot plot, M; rv-R2-b power
curves and rv-R2-c plasmode, S.

Main readings:

- H1, H4 and H6 cannot pass the first Holm step at their projected medians (smallest attainable p 0.031, 0.125 and
  0.031) and are announced in advance as "not determinable"; H5 is projected at 11 (6 to 15), probably below its
  minimum of 12.
- H2 is projected at 16 (13 to 18), above its minimum of 8, but its registered within-creator reference rejects about
  14 times the nominal rate under a creator-level placebo (7.3% and 6.8% against 0.5%).
- H3's registered shift test rejects 2.6 times nominal at 17 creators, and its estimate is not centred (-0.063).
- At 12 to 17 creators a creator sign-flip reaches 80% power only for effects 0.8 to 1.8 times the smallest effect of
  interest (H6 about 2.5 times at 17 creators); H3's recentred contrast needs 6 to 8 times.
- Plasmode: once a seen look passed at 0.05, a wave of the same creators passes a one-sided 0.005 test in 4.6 to 10.8%
  of cases at recording-level ICCs of 0.05 to 0.6 (9 to 22 times nominal); the wave pooled with 17 fresh creators in 3.1
  to 9.0%; 17 fresh creators alone at about nominal (0.5 to 0.8%). The pooled arm is a design simulation, not a pool of
  real hold-out results.

## What is withheld, and why

Nothing is withheld. Changes from the build's tables, for the public form only:

- The source notes named internal CAL files and printed seen-creator counts of each analogue (counts that can lie within
  1 to 4 of the 71 seen creators); they now name the analogue only.
- Erratum: the build's plasmode caption gave 1,211 recordings; the plasmode used 1,222 (its own table header).
- The smallest attainable p is printed exactly, as the power of two it is, with a 2-significant-digit decimal beside it
  (fix pass, 2026-11-22): printed to 5 decimals, 2^-17 (about 7.6e-06) at 17 creators read as 1e-05.

## Interval level

Monte Carlo rates throughout (placebo rejection, coverage, power), without confidence intervals; projections carry 90%
simulation ranges; the plasmode figure draws 90% Monte Carlo intervals (rate +/- 1.645 SE).

## Caveats

- Projections are simulated from pilot rates and run-ledger recording counts; the published first-round hold-out
  eligibility and CAL-f are the realised and label-based figures.
- H5 and H6 are sparse-count hypotheses: no normal-model power or type S/M is given for them (the normal model ignores
  half-count shrinkage and Poisson sparsity).
- Type S = 0 holds under the normal model only.
- Exploratory; not a test of H1-H10.
