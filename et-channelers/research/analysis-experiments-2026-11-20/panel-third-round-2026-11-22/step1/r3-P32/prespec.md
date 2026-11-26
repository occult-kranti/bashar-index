> Redacted copy: 1 private path replaced; the hash recorded at hashing time is kept privately.

# r3-P32 (carrying r4-P11): prespecification

Written 2026-11-26 from 07:23Z (UTC, from `date -u`; the hash time is in `prespec-record.md`) by a step-1 agent (a model
agent working for the project lead; not a person), before any outcome quantity of this entry was computed. Deposit 2 was
merged before this entry started. Exploratory; not a test of H1-H10. Seen creators only. Every label is model-coded and
not checked by a person; agreement between models is agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Known leak.** The writer has read, before writing this file, the public files and READMEs of the 17 step-1 entries
(their printed estimates among them: r3-P04's and r3-P05's rows, r3-P03's register-matched row, r3-P33's cascade) and
the released aggregates of nlp-R7 (boundary shifts of up to 3 units moved H1, H4 and H6 little on seen creators), VER-A,
VER-3R, VER-DEP and VER-MV. The zone width below (3 units) was chosen knowing nlp-R7's result. Nothing here is tuned on
an outcome of this entry; contrasts already computed on all seen creators are not split (split policy).

## 1. What runs

**Part 1, the error-aware hierarchical re-estimate:** a 90% prediction interval for a new creator on every controlled row
of the step-1 entries named below. **Part 2 (r4-P11), the boundary-restricted fragility analysis:** tipping curves of
the controlled rows of H1, H4 and H6 against the share of wrong boundary units, per error pattern, set against the
disagreement already measured (N09, an application of the fragility-index family; "not found in N searches" as deposited;
no novelty sentence is printed, ruling 12). A person's boundary sample (inside r3-P25) is class c and is not run.

## 2. Rows

Per-creator values are taken from the step-1 entries' private stores (seen, anonymous indices) or recomputed with their
own loaders (r3-P04's `common.py` and `p04_run.py`, r3-P05's `p05_run.py`, MR's `mrcommon.py`), on the same creator sets.

| Statistic (deposit 2 margin; named direction) | Rows (small model of record unless marked) |
|---|---|
| H1 claimed-minus-own log rate ratio (0.223; negative) | unmatched (reference row), position-matched (unit level, within tenths), XT-centred, ST-centred; middle model XT-centred |
| H4 standardised contraction drop (0.20 SD; positive) | unmatched (reference), position-matched, XT-centred, ST-centred, register-matched (r3-P03 R3), cue-free interiors (r3-P03 R2); middle model XT-centred |
| H6 observed-minus-expected claimed share of pay-or-enrol asks (0.05; negative) | unmatched (reference), position-matched (recording-by-tenth strata), XT-centred, ST-centred; r3-P05's K1 tenth-stratified score (creator z; no deposited margin fits the z scale: printed in its own units) |
| r3-P07 F1, time outside recognized speech, solo, S-centred (0.05 yardstick; no direction) | entries and exits: step, ramp before, ramp after (descriptions; r3-P07 reads no row) |

E5 has no controlled row (r3-P33): not re-estimated. The middle model's H6 rows are not published (fewer than 5 creators
with claimed-side asks). r3-P06's island statistic is a gate, not a voice contrast; r3-P01's rows are recognizer gaps.

## 3. Part 1 model and intervals

Creator values y_c, c = 1..k (k of 5 or more), creator mean ybar, SD s.

- **t prediction interval (primary):** ybar +- t(0.95, k-1) s sqrt(1 + 1/k): the model-coded value of one more creator
  like these, measured on that creator's own recordings. r3-P30 calibrated intervals of means, not prediction intervals,
  so this interval carries "interval class not calibrated by r3-P30" (lead's step-1 items 25 and 32; deposit 2's
  fallback family, the t interval on creator values).
- **Error-aware hierarchical prediction interval:** y_c = mu + u_c + e_c + b, with u_c ~ N(0, tau^2) the creator's
  deviation, e_c ~ N(0, v_c) the creator value's sampling noise (recording-level label noise included), b a label shift
  shared by every creator. v_c = pooled within-creator variance of recording values / n_c (the frozen
  `stats.creator_means_and_variances`) where the row's creator value is a mean of recording values; elsewhere v_c = 0
  (no recording noise removed; stated). tau_hat^2 = max(0, s^2 - mean v_c). Measured label error (r3-P19, two-reading
  design, small against middle model), scaled for shared errors by VER-DEP's phi of the two models' errors (0.512):
  rho_cm = creator-by-model component / (creator + creator-by-model); rho_m = model main effect / creator component;
  voice rows use the larger of the claimed-share and own-share values (rho_cm 0.0241, rho_m 0.0167); H6 rows add the
  pay-or-enrol asks values (rho_cm 0.0208, rho_m 0.0043). tau_aw^2 = tau_hat^2 (1 - rho_cm / (1 - phi));
  sigma_b^2 = tau_hat^2 rho_m / (1 - phi). Interval: ybar +- t(0.95, k-1) sqrt(tau_aw^2 + s^2/k + sigma_b^2): a new
  creator's contrast net of recording noise and of the creator-level label error two models of one vendor show, with the
  shared label shift's uncertainty added. "Interval class not calibrated by r3-P30." Shared errors beyond VER-DEP's phi
  are untested.
- **Beside them:** the mean with the 90% t interval on creator means (the centre of both prediction intervals; the
  source entry's printed estimate, interval and method are copied beside it, and their readings stand); the predictive
  share beyond the margin in the named direction under the t predictive distribution (a model quantity, not a count).
- **Description words for a prediction interval** (no reading A or B): "wholly beyond the margin in the named
  direction", "wholly beyond the margin, opposite to the named direction", "wholly inside the margin", "crosses the
  margin". r3-P07's rows (no direction): "wholly inside", "wholly beyond (above or below)", "crosses".

## 4. Part 2 error model

- **Boundary units.** For each statistic's own voice definition (H1 and H6: claimed V2 + V3; H4: V2; rule B, broad own
  voice) and the label of record, a boundary is a change between a claimed-voice unit and any other unit
  (`mrcommon.boundaries`). The zone Z of a recording is the set of units within w = 3 sentence units of a boundary (3 on
  each side). The share q of wrong boundary units is the number of zone units whose side differs from the record's,
  over all zone units (pooled over the row's recordings; realized shares are plotted). A one-unit zone (w = 1) is read
  off the displacement curves (one unit at every boundary is q = 1/6 of a three-unit zone; table only).
- **Three error patterns, two directions** (r4-P11's round-4 text). Direction *in*: claimed zone units are wrong (the
  record's claimed spans are too long); such a unit takes the side of the first unit beyond its nearest boundary.
  Direction *out*: non-claimed zone units are wrong (the record's spans are too short); such a unit becomes claimed.
  Patterns: **displacement** (each boundary moves by d units, nearest units first; d spread over boundaries so the
  recording's changed units approach q |Z|; 3 replicates); **scattered** (that many eligible zone units drawn at random;
  3 replicates); **outcome-selected** (the fragility index's worst case; eligible zone units ordered by their single-flip
  influence on the recording's registered value toward the row's margin crossing, only units that move it that way
  flipped, greedy; 1 run). Toward the crossing: H4 and H6 (beyond the margin at q = 0 in every computed small-model
  controlled row) toward zero; H1 (inside) toward the named direction. Greedy single-flip order is a heuristic worst case,
  not the exact minimum.
- **Grid** (nominal q): 0, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50 (one direction can change at
  most the zone units on its side, about half of Z).
- **What is recomputed under each perturbation.** Every recording's side list for the statistic is perturbed (the error
  is assumed in every map, donors included). Unmatched and position-matched rows from the perturbed lists (frozen
  per-recording functions through mrcommon's side-list hook; r3-P04's unit-level functions); XT and ST structure-only
  parts recomputed with the perturbed maps, with common random numbers across the grid (the same donor, map and shift
  draws at every point); r3-P05's K1 score with the perturbed lists. Draws per point: 40 for XT and 40 for ST, reduced to
  20, then 10, if one perturbation run of a statistic takes more than 20 s, then 40 s (a timing rule fixed here; no value
  is looked at to apply it). Creator and recording sets are held at q = 0's; a creator left without a value at a point
  keeps its value from the nearest smaller q (carried forward; the share of creator-points carried is printed).
- **Not in Part 2:** the middle-model rows (a second reading, not the record's boundaries), r3-P03's rows (its quintile
  model would need refitting under each perturbation), r3-P07's rows (their unit is the boundary itself).

## 5. Disagreement zones (from released public aggregates only)

- **Within-vendor (the two OpenAI models; nlp-R7's `nlp-r7-boundary-disagreement.csv`).** For each boundary of one
  model the nearest boundary of the same kind of the other model lies at distance d (shares printed at d = 0, d of 1 or
  less, 3 or less, 10 or less; unmatched otherwise). A displaced boundary makes min(|d|, 3) of a boundary's 6 zone units
  differ; an unmatched boundary 3. Expected share of differing zone units = sum over the printed distance classes
  (1 unit: 1; 2 to 3 units: 2 to 3, bracketed; 4 to 10 and unmatched: 3) / 6. From the printed shares: H1 and H6 (V2 + V3)
  0.136 to 0.145 counted from the record's boundaries, 0.185 to 0.192 from the middle model's: zone **0.136 to 0.192**;
  H4 (V2) 0.101 to 0.108 and 0.134 to 0.141: zone **0.101 to 0.141**. The approximation ignores overlapping zones.
- **VER-A tick (inside the within-vendor zone).** On words where the two cheap readers split, a blind third model of the
  same vendor gave the record's label on 0.341 of them (`ver-a-sides-on-disputed-words.csv`), so the record is outvoted on
  about 0.659: marked at 0.659 x the zone's ends (H1/H6 0.090 to 0.127; H4 0.066 to 0.093).
- **Cross-vendor (VER-3R, `ver3r-strata-and-packets.csv`).** The reader of another vendor departs from the OpenAI readers'
  majority on 0.033 of units in the pooled strata the OpenAI readers agree on and on 0.301 of units where they split:
  zone **0.033 to 0.301** (boundary units are a mix of the two; the near-change stratum alone is not published).
- **Shared errors.** VER-DEP: the two OpenAI models' errors are correlated (phi about 0.5), so disagreement bounds error
  only from below. meas's outer anchor (twice the within-vendor zone's upper end: 0.384 for H1 and H6, 0.282 for H4) is
  drawn as a dashed line, described, never read.
- **Direct check (described, never read).** From the seen labels of both models on the recordings the middle model
  labelled in full: the share of the record's zone units the middle model puts on another side (and the reverse),
  beside the mapped zone.

## 6. Tipping points and the reading rule

- **Tipping point q\*** of a row under one pattern and direction: the smallest realized q at which the row's point
  estimate (creator mean; the mean over replicates) reaches its margin from its q = 0 side (beyond to inside, or inside
  to beyond in the named direction), by linear interpolation between grid points; "not reached" if it does not within
  the pattern's largest realized q. Beside it, described only: the q at which the 90% t interval's near bound reaches the
  margin (where a row's interval lies wholly beyond it at q = 0).
- **Reading per row and pattern-direction** (programme 2.1, r3-P32):
  - "**robust to at least the disagreement already measured; shared errors untested**": q\* above the upper end of every
    zone (0.301), or not reached;
  - "**carried to its smallest effect within the disagreement already measured**": q\* at or below the upper end of the
    within-vendor zone;
  - "**undetermined**": otherwise (q\* inside the cross-vendor zone, above the within-vendor zone).
- **Row reading** (primary): the least robust of its six pattern-direction readings. Beside it, described: the same over
  the four patterns that do not select by outcome.
- **Multiplicity.** 56 primaries in the programme; if every true effect sat at half its margin, about 2.8 readings A
  would be expected at the deposited 5%, up to about 6.1 for the share, standardised, AUC and rank-correlation classes
  (r3-P30). This entry reads no A or B; no reading is a finding.

## 7. Plots and files

- `fig-r3-P32-prediction`: each controlled row on a smallest-effect scale (value / margin), the mean with its interval,
  the t prediction interval and the error-aware one, at equal prominence, numbers printed beside.
- `fig-r3-P32-tipping-H1`, `-H4`, `-H6`: per row a panel of six tipping curves (colour: pattern; line: direction), value
  / margin against realized q, the margin and zero marked, the within-vendor zone, the VER-A tick, the cross-vendor zone
  and meas's dashed anchor marked.
- Public: data CSVs with a commented header, readings CSVs, PNG at 200 dpi without text chunks, PDF without document
  information. Style copied from the CHANGE group's private plotting code folder.

## 8. Privacy (binding)

No cell, bin, bar or plotted group on fewer than 5 creators; no per-creator points or rows; creator counts printed as the
source entries printed them for the same sets, and any other count checked against 101, 71, 48, 23, 18, 6, 36 and every
count printed by the other step-1 entries (1 to 4 apart: stated against it); no quantile of creator values; no value
recoverable by subtraction, complement or sums; no names, ids, titles or quotations. The release's quantile solvers and an
identifier scan run before the entry is finished.
