# rv-R1: H3 at the creator level

Exploratory (registry A2); not a test of H1-H10. Paper-review build item (built 2026-11-21 on seen creators; label
"Exploratory, paper review (registry A2/A7); not a test of H1-H10"), released here in the public form of plan section 3
by the release review (plan P10, 2026-11-22). H3 is closed (amendment A6): nothing here is a verdict, and no p in it is
a test of H3.

## What it asks

What does the registered H3 contrast (first-person singular at the edges of a recording against its middle, U) show
when the creator, not the recording, is the unit? The plan row asks for the registered U, a t interval on creator means,
a sign test, the recentred U with a creator sign-flip p, the placebo rejection of the registered rule, power, type M, the
detectable effect, and four figures.

## Base

- Hold-out: 17 creators and 169 recordings, from the published summaries only (no new hold-out contact).
- Seen: the 61 creators and 558 recordings eligible under the frozen H3 rules at the registered 180-s trim (English-only
  model, no publisher audio, 600 s and 800 words after the trim, 50 words in every bin), recomputed by the build with
  artefact filter v2 (the frozen code uses v1: U 0.0193 against the published 0.0194).
- Calibration: CAL's creator-level placebo on seen creators (4,000 sets of 12 or 17 of the 61 creators).

## What is shown

| File | What it holds | Place |
|---|---|---|
| `public/rv-r1-h3-creator-level.csv` | The H3 table: registered row, creator-level reading, seen rows, seen beside hold-out, calibration, power, restated status | M |
| `public/rv-r1-h3-seen-beside-cal.csv` | H3-SEEN: the published seen row with CAL's recentred value beside it | S |
| `public/rv-r1-u-histogram.csv` | Figure (a): creators below zero and at or above zero, registered and recentred U (bins merged at zero, see below) | S |
| `public/rv-r1-u-percentiles.csv` | Figure (a): mean with its 90% t interval and the 10th to 90th percentiles over creators, registered and recentred U | S |
| `public/rv-r1-placebo-p.csv` | Figure (b): placebo p-values against a uniform p, four procedures | S |
| `public/rv-r1-recentred-u-by-trim.csv` | Figure (c): U against the trim | S |
| `public/rv-r1-first-person-15s.csv` | Figure (d): first-person singular in 15-s bins over the first and last 300 s | S |
| `public/rv-r1-power-simulation.csv` | Power, type S and type M of the creator sign-flip (shift model) | S |
| `public/rv-r1-dashboard-row.csv` | The wording built for the dashboard's H3 results row: the hold-out reading with the seen reading beside it and the pointer to the balance table (rv-D2) | W |

Figures (in the gallery, with their records in its `manifest.json`): rv-R1-a to rv-R1-d, place S.

Main readings:

- Hold-out, registered rule: U 0.169 (90% two-stage percentile -0.130 to 0.494), shift p 0.0007, "supported" by the
  registered rule. At the creator level the 90% t interval on the 17 creator means is -0.137 to 0.476 and 9 of 17
  creators are positive (sign test p 0.50).
- Seen creators: registered U 0.019 (90% t -0.121 to 0.160); recentred U 0.083 (-0.046 to 0.211), creator sign-flip
  p 0.146; 41 of 61 creators above zero.
- H3-SEEN beside CAL: the published seen row (U 0.0194, 90% two-stage percentile -0.129 to 0.1648, shift p 0.1225,
  undetermined) and CAL's recentred value (0.0826, 90% t -0.0455 to 0.2107).
- Calibration: the registered rule says "supported" in 1.63% (12 creators) and 1.32% (17) of creator-level placebo sets
  against a nominal 0.5%; the creator sign-flip on recentred U stays near nominal (0.32% and 0.35%).
- At the smallest effect of interest (U 0.10) the creator-level test has about 2 to 7% power, and a passing estimate
  would be exaggerated about 3 to 5 times. The U detectable with 80% power is 0.58 to 0.79.
- The first-person surplus sits in the first and last minutes: on a fixed set of 55 creators the recentred contrast falls
  from 0.52 untrimmed to 0.14 at 180 s and 0.02 at 300 s; the rate is 45 per 1,000 words in the first 15 s and 39 in
  the last 15 s, against 29.5 in the middle.
- Restated status: passed its registered rule; the rule was not calibrated at the creator level; not determined at the
  creator level; withdrawn (A6).

## What is withheld, and why

- **The inverse-variance pool of seen and hold-out creators, and its recentred version**: not published. Hold-out
  results are printed beside seen results and never pooled (plan section 5 rule 4; lead's decision D1). The
  hold-out-minus-seen difference is printed in their place (0.150, z 0.71).
- **The hold-out recentred value (0.232)** is printed but marked superseded: it subtracted the seen creators' reference
  centre. H3-X (package HOLD) uses the hold-out's own exact centre (recentred U 0.353, 90% t 0.025 to 0.682).
- **The eligible-at-each-trim rows other than 0 s and 180 s** (figure c): not published. Their creator sets lie within
  1 to 4 creators of a printed nested set, and their difference from the fixed-set row at the same trim was not shown to
  rest on 5 or more creators. The fixed set (55 creators at every trim) carries the curve. The 300-s row is the same set
  as the fixed set.
- **Counts of creators with positive recentred U by trim, and per-bin creator counts of figure (d)**: not printed
  (neighbouring counts differ by 1 to 4). Every bin of figure (d) rests on 49 or more of the 61 creators.
- **Figure (a)'s five-bin histograms** (fix pass, 2026-11-22): the registered and the recentred histograms differed in
  1 to 4 creators in four of their five bins, so beside each other they would isolate fewer than 5 creators (pairs rule,
  addendum 2 item 9). Their bins are merged by plan section 3's rule until the two series differ by 0 or 5 or more
  creators in every bin, which leaves two bins: below zero (25 registered, 20 recentred) and zero or above (36 and 41).
  The shape of each distribution is printed instead as percentiles over creators (10th, 25th, 50th, 75th and 90th;
  `rv-r1-u-percentiles.csv`, added after the exploratory reporting plan), and figure (a) draws them as box plots.

## Interval level

90% throughout: two-stage percentile bootstrap for the registered row, t intervals on creator means for the
creator-level rows, creator bootstrap (2,000 draws) for figure (d), the binomial band of a uniform p for figure (b).
Monte Carlo rows (calibration, power) carry Monte Carlo standard errors, not confidence intervals.

## Caveats

- The seen rows use artefact filter v2; the frozen code's rows (filter v1) are in H3-X. The two differ in the third
  decimal (for example the lower end of the recentred interval: -0.0455 here, -0.045 in H3-X). The seen creator
  sign-flip p-values differ by the filter version and by the Monte Carlo draws: 0.146 here against
  0.1480 in H3-X for recentred U, 0.412 against 0.4131 for raw U.
- The hold-out is the tail of an English-first run and is not exchangeable with the seen creators: read the hold-out rows
  beside the balance table (rv-D2).
- The dashboard row is a proposed wording; the dashboard's owner decides before any public change.
- Exploratory; not a test of H1-H10.
