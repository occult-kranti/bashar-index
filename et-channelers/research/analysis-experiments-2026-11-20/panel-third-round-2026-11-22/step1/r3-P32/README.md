# r3-P32 / r4-P11: an error-aware hierarchical re-estimate on the controlled contrasts, and a boundary-restricted fragility analysis

Third-round panel programme, step 1 (class a.1), the last of the seen re-estimates. **This entry carries r4-P11** (the
boundary-restricted fragility analysis; novelty N09, an application of the fragility-index family, kept in its deposited
form: "not found in 4 member searches (9 attacker searches); the concept is not new. Not found means only that." No
novelty sentence is printed before the second attack pass, ruling 12). Written 2026-11-26 (UTC times from `date -u`, in
`status.json`) by a step-1 agent (a model agent working for the project lead; not a person). Seen creators only. No model
call, no network call, no download, no GPU job. A person's boundary sample (inside r3-P25) is class c and was not run.

**Status.** Exploratory; not a test of H1-H10. Every label is model-coded and not checked by a person; agreement between
models is agreement, never accuracy; recognizer output is not checked by a person.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Prespecification

`prespec.md` (SHA-256 the hash recorded at hashing time is kept privately) was hashed at
**2026-11-26T07:24:24Z** (`prespec-record.md`), before any outcome quantity of this entry was computed; every analysis
script refuses to run if it changed. It fixes the model, the error patterns, the tipping grid, the margins (deposit 2)
and the reading rule. Known leak (stated there): the writer had read the step-1 entries' printed results and the
released aggregates of nlp-R7, VER-A, VER-3R, VER-DEP and VER-MV; the 3-unit zone was chosen knowing nlp-R7's result.
An outcome-free probe (`code/probe_p32.py`: zone counts, load time, the time of one evaluation, its value discarded) ran
after the hash.

## Part 1: prediction intervals for a new creator (`fig-r3-P32-prediction`, `data-r3-P32-prediction.csv`)

*Changed 2026-11-26T09:20:53Z by the lead's step-1 decision 49(a, e): on rows whose creator count is banded, the prediction intervals, the spread over creators and the predictive share are not printed; counts use the release's form for their set. No number changed.*

Every controlled row of r3-P04 (H1, H4, H6: position-matched, beyond the cross-creator transplant XT, beyond the
same-creator transplant ST; the middle model's XT rows), r3-P03 (H4 register-matched R3 and cue-free interiors R2),
r3-P05 (pay-or-enrol asks under position, the creator score z) and r3-P07 (time outside recognized speech at
claimed-voice boundaries, solo, S-centred; descriptions), on the per-creator values those entries computed, with the
same creator sets (counts as the source printed them). The unmatched rows are printed as reference rows. E5 has no
controlled row and is not re-estimated.

- **The t prediction interval** (90%): ybar +- t(0.95, k-1) s sqrt(1 + 1/k), the model-coded value of one more creator
  like these. **The error-aware hierarchical interval** (90%): recording noise removed where creator values are means of
  recording values; the creator-level label error two models of one vendor show (r3-P19's creator-by-model component)
  removed and the shared label shift (r3-P19's model main effect) added, both scaled by 1 / (1 - phi) with VER-DEP's phi
  of the two OpenAI models' errors (0.512). Both carry the words **"interval class not calibrated by r3-P30"** (lead's
  step-1 items 25 and 32: r3-P30 calibrated intervals of means, not prediction intervals).
- **What they show, printed as they come.** On **every** controlled row whose 90% t prediction interval for a new creator
  is printed, it **crosses the smallest effect**, also where the mean lies far beyond it:

| Row (creators as printed by the source) | Creator mean (90% t interval) | 90% prediction interval | Error-aware 90% interval | Predictive share beyond the margin |
|---|---|---|---|---|
| H1 position-matched (40 to 49) | -0.099 (-0.161 to -0.037) | not printed (count banded) | not printed (count banded) | not printed (count banded) |
| H1 XT-centred (40 to 49) | -0.076 (-0.157 to 0.005) | not printed (count banded) | not printed (count banded) | not printed (count banded) |
| H1 ST-centred (23 and fewer than 5 more) | -0.035 (-0.094 to 0.025) | not printed (count banded) | not printed (count banded) | not printed (count banded) |
| H4 position-matched (19 and fewer than 5 more) | 1.815 (1.132 to 2.498) | not printed (count banded) | not printed (count banded) | not printed (count banded) |
| H4 XT-centred (34) | 1.463 (1.122 to 1.804) | -0.554 to 3.479 | -0.539 to 3.464 | 0.85 |
| H4 ST-centred (all but fewer than 5 of 23) | 1.826 (1.389 to 2.263) | not printed (count banded) | not printed (count banded) | not printed (count banded) |
| H4 register-matched (44) | 1.610 (1.172 to 2.047) | -1.327 to 4.546 | -0.804 to 4.023 | 0.79 |
| H6 position-matched (all but fewer than 5 of 30) | -0.320 (-0.391 to -0.249) | not printed (count banded) | not printed (count banded) | not printed (count banded) |
| H6 XT-centred (all but fewer than 5 of 34) | -0.246 (-0.328 to -0.165) | not printed (count banded) | not printed (count banded) | not printed (count banded) |
| H6 ST-centred (16 and fewer than 5 more) | not printed: the row's count is banded (the lead's step-1 decision 56) | not printed (count banded) | not printed (count banded) | not printed (count banded) |

  Margins: H1 0.223 (log ratio, named direction negative), H4 0.20 SD (positive), H6 0.05 (negative). The other rows
  (unmatched, the middle model, cue-free interiors, r3-P05's score, r3-P07) are in the data file; where their prediction
  intervals are printed, they also cross their margin or yardstick (r3-P05's score has none). The predictive share is a model quantity under the t
  predictive distribution, not a count of creators.
- **In words.** The mean contraction drop (H4) and the mean ask placement (H6) lie far beyond their smallest effects on
  every controlled row whose mean is printed, but a new creator like these could fall short of the smallest effect, or on the other side of
  zero: the t predictive distribution puts about a tenth to three tenths of new creators short of the margin for H4 and H6. For the rate (H1),
  whose mean lies inside its margin, a new creator could lie beyond the margin in either direction. The error-aware
  intervals differ little from the plain ones where creator values are not means of recording values (the transplant
  and observed-minus-expected rows: no recording noise can be removed, and the measured label error is small beside the
  spread between creators); where recording noise can be removed they are narrower, and where the spread between
  creators is no larger than that noise (H1 position-matched, r3-P07's exit step) the error-aware interval shrinks to
  the interval of the mean. That is a statement about the label error that agreement between two models of one vendor
  can show; shared errors beyond VER-DEP's phi are untested.

## Part 2 (r4-P11): tipping curves against the share of wrong boundary units (`fig-r3-P32-tipping-H1`, `-H4`, `-H6`)

- **Error model.** Boundary units: units within 3 sentence units of a claimed-voice boundary of the label of record, per
  statistic definition. The share q of wrong boundary units is the share of those units whose side is changed, over all
  of them. Three patterns (displacement: boundaries moved, nearest units first; scattered: units at random;
  outcome-selected: units ordered by their single-flip influence toward the margin, greedy, a heuristic form of the
  fragility index's worst case) and two directions (claimed spans too long; too short). Every recording's map is
  perturbed (donors and maps included); XT and ST structure-only parts are recomputed with the perturbed maps (40 draws
  per point, common random numbers; the timing rule did not reduce the draws). Rows: unmatched (reference),
  position-matched, XT-centred, ST-centred for H1, H4 and H6, small model of record; and r3-P05's cohort ratio for
  pay-or-enrol asks under position. Bases: 240 (H1), 185 (H4) and 278 (H6) recordings.
- **Disagreement zones (public aggregates only; `r3-P32-zones.csv`).** Within-vendor (the two OpenAI models, nlp-R7's
  boundary disagreement mapped to the 3-unit zone): 0.136 to 0.192 for H1 and H6, 0.101 to 0.141 for H4; VER-A's
  third-model ticks inside it; cross-vendor (VER-3R, the reader of another vendor against the OpenAI majority, from units
  the OpenAI readers agree on to units they split on): 0.033 to 0.301; meas's outer anchor (twice the within-vendor upper
  end) drawn, not read. The direct check from the seen labels of both models (described, never read) gives 0.148 and
  0.197 for H1 and H6, 0.119 and 0.149 for H4, close to the mapped zones.

**Primary readings (`r3-P32-readings.csv`): every controlled row reads "robust to at least the disagreement already
measured; shared errors untested".** No curve of any pattern or direction carries any row to its smallest effect within
the shares the patterns can reach (up to about 0.4 to 0.5 for displacement and scattered errors), so no tipping point
exists on the grid, inside or beyond the zones. The same holds without the outcome-selected pattern.

| Row | At q = 0 (in margins) | Closest approach to the margin (in margins; pattern; realized q) |
|---|---|---|
| H1 unmatched / position-matched / XT / ST (inside the margin) | 0.32 / 0.44 / 0.31 / 0.15 | 0.46 / 0.79 / 0.46 / 0.27 (outcome-selected, spans too short; q 0.12 to 0.13) |
| H4 unmatched / position-matched / XT / ST (beyond) | 8.9 / 9.1 / 7.2 / 8.8 | 6.4 / 2.0 / 4.8 / 6.3 (outcome-selected, spans too short; q about 0.16) |
| H6 unmatched (beyond) | 8.5 | 6.0 (scattered, spans too short; q 0.45) |
| H6 position-matched / XT / ST (beyond) | 6.4 / 4.9 / not printed | 3.1 / 2.6 / not printed (outcome-selected, spans too short; q below 0.01); the ST row's curve is not printed for privacy (its count is banded) |
| r3-P05 cohort ratio (beyond; ratio 0.29) | 5.6 | 1.65, a ratio of about 0.69 (outcome-selected, spans too short; q below 0.01) |

**In words.** If the record's claimed-voice boundaries were wrong on as large a share of the units next to them as two
models of one vendor already disagree about, or as a reader of another vendor departs on the hardest units, none of the
controlled contrasts would reach its smallest effect: the contraction drop and the ask placement stay several margins
beyond it, and the rate stays inside it. The worst case is the outcome-selected pattern with spans too short: for H6 and
r3-P05 it moves into the claimed voice every pay-or-enrol ask within 3 units outside a claimed-voice boundary that a
one-unit change can move (fewer than 1 in 100 boundary units), and the claimed share of such asks still stays below the margin (the
r3-P05 cohort ratio rises from 0.29 to about 0.69, below 0.80). Because disagreement bounds error only from below under
correlated errors (VER-DEP), the reading is only "robust to at least the disagreement already measured; shared errors
untested"; errors the two models share, and errors away from boundaries, are not tested here.

**Described only (not read):** the near 90% t bound reaches the margin under some outcome-selected curves (H4
position-matched at q 0.066; H6 XT and ST at q below 0.01; H6 ST spans too long at 0.111) and under one scattered curve
(H6 XT, q 0.429): there the interval of the perturbed mean would no longer lie wholly beyond the margin, although its
point does (`r3-P32-tipping-points.csv`).

Multiplicity: 56 primaries in the programme; if every true effect sat at half its margin, about 2.8 readings A would be
expected at the deposited 5%, up to about 6.1 for the share, standardised, AUC and rank-correlation classes (r3-P30).
This entry reads no A or B, and no reading is a finding.

## Departures and choices (stated)

1. **r3-P05's tipping row is read on its cohort ratio** (log sum O / sum E against deposit 2's 0.80, the quantity r3-P05's
   reading uses), not on a creator mean, because the creator score has no deposited margin; prespec section 6 speaks of
   the row's creator mean. The score's prediction interval is in Part 1 (its own units, no margin).
2. **A "closest approach" column** was added to `r3-P32-readings.csv` after the curves were seen, because no curve
   reaches a margin; it is described only and changes no reading.
3. **Column names** containing "q0" were renamed ("at zero share") after the release's quantile scan misread them as
   quantile columns; no value changed.
4. **Carried values.** Creator sets are held at q = 0's; a creator left without a value at a point keeps its value from
   the nearest smaller q (prespecified). The carried share reaches 0.35 for H4 position-matched (creators losing 10
   contractible forms per side within matched tenths) and 0.14 for H6 position-matched and r3-P05; elsewhere 0.09 or
   less (`carried_share` in the curves file). Those curves partly show eligibility loss, not value change.
5. **The shared label shift is scaled to the creator spread** (prespecified); where that spread is not detectable beyond
   recording noise the allowance is zero, which understates it.
6. **XT and ST at q = 0** use 40 draws with common random numbers, so their curve starts differ slightly from r3-P04's
   200-draw values (H4 XT 1.446 against 1.463; the unmatched and position-matched values reproduce r3-P04's exactly).
7. **Greedy single flips** cannot move a multi-unit ask that needs two units changed to change side, so the
   outcome-selected pattern can understate the worst case (prespec: "a heuristic worst case, not the exact minimum").

## Fields or bases not stored

- Per-recording values of the XT- and ST-centred parts and of the observed-minus-expected rows are not stored by r3-P04
  (creator-level values only), so recording noise cannot be separated for those rows (the error-aware interval keeps it).
- r3-P05 stored no per-creator scores; they were recomputed here with r3-P05's own functions (mean score and cohort ratio
  reproduce r3-P05's printed -1.291 and 0.287 exactly).
- VER-3R's near-change stratum and the direction rows of the cross-vendor disagreements are withheld in the release, so
  the cross-vendor zone is bracketed between agreed and split units, not measured on boundary units.
- No person's boundary sample exists (class c, inside r3-P25), so no tipping share can be set against an error rate.
- No recognizer of another family and no acoustic boundary (a.2).

## Contacts

None (`contacts.md`).

## For the lead

1. Every row reads "robust to at least the disagreement already measured; shared errors untested". The described
   near-bound tipping of H4 position-matched (q 0.066, outcome-selected) and of H6 XT and ST (below 0.01) lies inside the
   measured disagreement: whether that should be cited beside r3-P33's cascade.
2. The cross-vendor zone could be measured on boundary units from VER-3R's stored seen units (check creators, private);
   this entry used the public aggregates only, as briefed.
3. An exact worst case (pairs of flips for multi-unit asks) is no-cost and could follow if the lead wants the
   fragility-index form sharpened.
4. N09 stays in its deposited form; no novelty sentence prints before the second attack pass.

## Files

SHA-256 of every file: `status.json`. Public data CSVs carry a commented header; PNGs at 200 dpi without text chunks;
PDFs without document information.

| File | What |
|---|---|
| `prespec.md`, `prespec-record.md` | the prespecification and its hash record |
| `public/data-r3-P32-prediction.csv` | Part 1: every controlled row, the source's printed row, the creator mean, both prediction intervals |
| `public/data-r3-P32-tipping-curves.csv` | Part 2: every curve point (figure data) |
| `public/r3-P32-tipping-points.csv` | tipping points per row, pattern and direction, with readings |
| `public/r3-P32-readings.csv` | the primary reading per row |
| `public/r3-P32-zones.csv` | the disagreement zones and the direct check |
| `public/fig-r3-P32-prediction.png/.pdf` | each contrast on a smallest-effect scale with its prediction intervals |
| `public/fig-r3-P32-tipping-H1/-H4/-H6.png/.pdf` | tipping curves per error pattern with the zones marked |
| `code/p32common.py`, `p32_run.py`, `p32_part1.py`, `p32_zonecheck.py`, `p32_publish.py`, `p32_plot.py`, `probe_p32.py`, `finalize.py` | this entry's code (reuses r3-P04's `common.py` and `p04_run.py`, r3-P05's `p05_run.py`, MR's `mrcommon.py`) |
| `code/style.py` | the CHANGE group's style, copied unchanged |
| `code/scans/` | the release's `zsolve.py`, `qscan_all2.py`, `quant.py`, `quant2.py`, pointed at this folder |
| `code/scan_ids.py`, `code/pubrules.py` | r3-P07's identifier scan, copied |
| `private/` | run outputs and logs (never published) |

Importing r3-P04's and r3-P05's code wrote Python bytecode caches (`__pycache__`) into their `code/` folders; they were removed at 2026-11-26T07:55:16Z (UTC, from `date -u`), so those folders hold exactly the files they held before. No other file outside this folder was written.

**Privacy scans:** zsolve.py 0 rows tested, 0 pinned, 0 narrowed; qscan_all2.py 0 rows with a hidden or banded base, 0
files with quantiles over numeric bases; quant.py and quant2.py 0 rows with a quantiles column; identifier scan 0 hits in
13 public files, no PNG text chunk, no PDF document information.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
