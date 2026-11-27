# r3-P30 version 2: the card of the calibration battery (f4-Q09 (ii))

Fourth-round panel, deposit 5, addendum 1, part C. Written 2026-11-27 from 13:35:23Z (UTC, from `date -u`) by a drafting
agent working for the project lead (a model agent, not a person), under decision 144.2 (C), before any part of the
battery exists and before any of its outputs. This card is the prespecification that deposit 5 names in section 3.2 ("r3-P30
version 2's battery seeds are fixed in its own prespecification, hashed before it runs") and that deposit 5a names in
section 3.7 ("the seed, the truncation quantile, the three residual-variance scenarios and the smoothed choice rule are
fixed in version 2's prespecification, hashed before its battery runs"). Its SHA-256 and the time it was taken are in the
addendum's private hash record.

**Status.** Exploratory; not a test of H1-H10. A calibration act like r3-P30: no rule is tuned, no contrast is read, no
label is read and no published entry is re-read. Every simulated data set is a label-free analogue built from the seen
creators' recognizer output (CAL's seen-only cache) and, for one class, from the stored upload days of seen recordings.
Recognizer output and listing metadata are not checked by a person. A reading A is never called a finding.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Privacy.** No creator, channel, title, id or quotation of corpus text appears here, and no person, being or group of
the corpus is named. Every number is printed on main, is one of deposit 2's margins, is a design constant fixed here, or
is a date; besides these, decision and section numbers and the publication year of one cited method. The battery
describes interval methods, not the corpus: no pool statistic other than those r3-P30 printed is ever printed.

Contents: 1 inputs; 2 what the battery does and how its table is used; 3 classes; 4 methods; 5 counts; 6 data sets; 7
measures and the rule for choosing; 8 seeds; 9 order of runs and machine rules; 10 printing; 11 departures from r3-P30
and points for the lead; 12 what this card does not do.

---

## 1. Inputs

### 1.1 Published inputs, pinned to commit `1461979` of `main`

Paths are relative to `et-channelers/research/analysis-experiments-2026-11-20/`. Each SHA-256 is that of the file's bytes
at the pinned commit (`git show 1461979:<path> | sha256sum`). The run checks each hash before it starts; a file whose
hash differs stops the run and the lead is told.

| Input | Path | SHA-256 at `1461979` |
|---|---|---|
| The fourth panel's programme (f4-Q09 (ii); section 4.2, the dependency table) | `panel-fourth-round-2026-11-27/programme.md` | `31cadaa571998408e55e52f94673301aa9195283521533a0f4c954cb55f9b3f1` |
| Deposit 5: the registration (sections 2.1, 2.5, 2.7, 3.2, 3.3, 4.9) | `panel-fourth-round-2026-11-27/deposits/deposit-5/registration.md` | `a1e7a80046807a7fb8f4cc8a1d274477ee7b1601d65a3b93a21f042f2228f541` |
| Deposit 5a: the registration (sections 2.2, 2.5, 3.7, 3.11, 3.15) | `panel-fourth-round-2026-11-27/deposits/deposit-5a/registration.md` | `c3c624ce275c068d97bddd902a68bfd2375940f4bff6c87f734a961e3d33bdab` |
| Deposit 2: r3-P30's method card | `panel-third-round-2026-11-22/deposits/deposit-2/calibration-method-card.md` | `096db5079522ce5d0a2050fe47cf87bbb2dbecef6958984caf164b878c729a57` |
| Deposit 2: margins and readings | `panel-third-round-2026-11-22/deposits/deposit-2/lead-margins-and-readings-2026-11-26.md` | `c25c8979eb272b19125a0597658295241d1d4c40a33f0a22015032f90bbf18cd` |
| r3-P30: README | `panel-third-round-2026-11-22/step1/r3-P30/README.md` | `1161389cb1c3f51bdb3e9f160f0bd7ad24ab6b8da75aff712576808bfe9b897f` |
| r3-P30: prespecification (published copy) | `panel-third-round-2026-11-22/step1/r3-P30/prespec.md` | `5194026af97d2836dca69ba36012235d4e759d9d5d6025c83db3379a78967763` |
| r3-P30: status | `panel-third-round-2026-11-22/step1/r3-P30/status.json` | `6cdfa67f3c26ea139061ecdc1032234cb8998b872e3607d7cad2ea1308a8fbec` |
| r3-P30: interval choice by class and count (version 1's choice table) | `panel-third-round-2026-11-22/step1/r3-P30/public/interval-choice.csv` | `fcfe22cfba84b8b5eedd059ff605afb0055761b88c4c4d96e708d24400a6e1f6` |
| r3-P30: coverage grid (figure data) | `panel-third-round-2026-11-22/step1/r3-P30/public/data-r3-P30-coverage-grid.csv` | `4a4412acd8befa4ceda22d7da63044bb197c161effe9d4d4e7534f4a3fe99930` |
| r3-P30: size panel | `panel-third-round-2026-11-22/step1/r3-P30/public/data-r3-P30-size.csv` | `f6496eab5ba96e1ac5b5af324a954829e77c219a560affd0f6064b7c46d72afc` |
| r3-P30: readings table (r4-P10's residual) | `panel-third-round-2026-11-22/step1/r3-P30/public/data-r3-P30-readings.csv` | `29c7583af74bda194acecebea37b88ba9fa3449069b33f8bc6874ae1d24b177e` |
| r3-P30: classes | `panel-third-round-2026-11-22/step1/r3-P30/public/data-r3-P30-classes.csv` | `314d359d6ddb8006d13ebbceab0b6dd6e5b2b8058e22243edc3a2802215cf283` |
| r3-P36: the published slopes (TL-7.1's printed channel band) | `panel-third-round-2026-11-22/step3/r3-P36/public/data-r3-P36-slopes.csv` | `dada83123483abc68482cea773746b567340587b86e2a2d2f2c3006ea838d9cc` |

### 1.2 Private inputs (read by the run only, each hash checked or recorded first)

| Input | Hash |
|---|---|
| CAL's private seen-only cache (per seen recording, per sentence unit, counts only) | `9383c3fd37849983767213b9c2273e262260050c51aabcf0fec2785f81e2c2ba` (printed in r3-P30's prespecification) |
| r3-P30's `build_pools.py` and `battery.py` (code, reused unchanged where section 3.1 says so) | `01facd62f515e6a289d62a734577a2f2182a85561497649b59c487062e339f56` and `24367d512882a2dde275ad035605a0c233eb377ce50cd10ec0e2b274bf5688cf` (printed in r3-P30's README) |
| r3-P30's private pools file (the nine classes' pools) | checked against the SHA-256 that r3-P30's private battery record holds for it |
| The stored upload day of each seen recording (listing metadata; the confirmed upload days r3-P36 used), from a seen-only store | recorded in the run's status file before it is read |

From the upload-day store the run reads the upload day and the recording key of seen recordings only, and no other field:
no timeline row, window, label or title.

---

## 2. What the battery does and how its table is used

- **Question.** Which 90% interval method holds coverage for each design class at each simulated creator count, with the
  Monte Carlo error made small at the counts the fourth panel's entries use? Does r3-P30's choice survive more simulated
  data sets and a smoothed choice rule fixed in advance? And which method holds for the classes the fourth panel adds:
  the precision-weighted slope class (decision 84), a kappa class (f4-Q09's flag), and the three classes deposit 5 names
  in f4-Q09 (ii) (paired persistence, an ICC class, cross-fitted standardised contrasts)?
- **Kind.** An act (as r3-P30): no tier, no reading, no account cell.
- **How the entries use the table** (restated from deposits 5 and 5a; this card changes none of it):
  1. **f4-Q07's slopes** take the slope class's choice at their count (deposit 5a, section 2.2), by the scenario rule of
     section 7.5. T-Q07-2 is deposited before any slope is drawn (deposit 5a, section 3.15). Slopes stay descriptions at
     tier D, with no reading words (decision 128).
  2. **Every other fixed interval** of deposits 5 and 5a stays fixed. Version 2's choice at the row's count prints beside
     the row; where it names another method, that prints as a limitation of the row and never replaces the fixed
     interval (deposit 5, section 2.1).
  3. **f4-Q09's primary** carries the flag "interval class not calibrated by r3-P30" until the kappa class of section 3.3
     has run; only that class clears it. Its interval stays the registered creator bootstrap (deposit 5a, section 2.2),
     and version 2's kappa row prints beside it.
  4. **f4-Q09 (iii), the decidability gate,** reads version 2's mean widths in margins and its readings table (section
     7.7) at each fourth-panel primary's count band.
  5. **No published entry is re-read.** Where version 2 would have chosen another method at a published entry's count,
     f4-Q09's ledger prints that as a limitation of the entry (f4-Q09 (ii)).
  6. **No registered rule is loosened** by this table (decision 129.13). A consequence that deposit 5 or 5a fixed from
     r3-P30's printed table (for example, f4-Q05b's standardised rows below 18 reading "undetermined") stands, whatever
     version 2 finds.

---

## 3. Classes

Eighteen choice cells in six parts. Every class's pool is a set of real seen creators (or their channels), drawn with
replacement in each simulated data set, and the pool is the population, as in r3-P30. Each pool prints only as a band in
the register's printed forms (section 10.3).

### 3.1 r3-P30's nine classes, unchanged

`A_log_ratio`, `B_share_difference`, `B1_share_one_recording`, `C_standardised`, `D_superiority`, `E_rank_correlation`,
`F_slope`, `G_few_recordings`, `H_rare_counts`: every interval class r3-P30 holds, with r3-P30's definitions, margins,
truths and methods (its prespecification). The pools are r3-P30's private pools file itself, read unchanged after its
hash check; nothing is rebuilt and no fixed draw inside a pool is redrawn. Each cell runs r3-P30's `run_cell` (in
`battery.py`, hash in section 1.2) unchanged, with three constants replaced: the data sets per cell (section 6), the base
seed (section 8) and the counts (section 5). r3-P30's `F_slope` stays as r3-P30 defined it (TL-7.1's design class, margin
0.20 between-creator SD of the slopes, flagged); the precision-weighted class of section 3.2 is new and replaces nothing.

### 3.2 `F_slope_pw`: the precision-weighted slope class (decision 84; f4-Q07 and f4-Q09)

Deposit 5a (section 3.7) fixes the candidates and that the analogue slopes come from the seen recognizer cache, with
within-channel x set to the stored upload dates and heteroscedastic error. The details are fixed here.

- **Pool.** Seen channels whose recordings with a defined log words per minute (r3-P30's per-recording rate, as its
  `F_slope` computes it) and a stored upload day number 3 or more and span 60 or more days (TL-7.1's protocol rule).
- **Units, fixed once per channel** (pool stream, section 8). The number of units m is drawn uniformly from 3 to the
  smaller of 8 and the channel's eligible recordings, as r3-P30's `F_slope` drew them; then m recordings are drawn
  without replacement, the draw repeated until they span 60 days or more (at most 1,000 draws; a channel with no such
  draw leaves the pool). Each unit's x is its upload day in days, centred on the channel's mean over its units.
- **Regime, fixed once per channel, label-free.** The least-squares slope of log words per minute on upload day over all
  of the channel's eligible recordings. The channel's true slope is 1 (rolling horizon) where that slope is positive and
  0 (fixed target) otherwise. The pool is thus a real mixture of the two regimes, the mixture the programme warns about.
- **Spread, fixed once per channel.** The residual SD of that regression, divided by the pool's median residual SD.
- **Each simulated data set.** k channels are drawn with replacement. Each drawn channel's unit responses are its true
  slope times x, plus normal error with SD equal to the scenario's scale times the channel's spread, drawn fresh. The
  channel's slope is the least-squares slope over its units, with variance s²/Sxx (s² on m − 2 degrees of freedom), floored
  at 1e-4 as TL-7.1 floors it.
- **Three residual-variance scenarios** (cells `F_slope_pw_s30`, `F_slope_pw_s365`, `F_slope_pw_s3650`): a residual SD of
  the window midpoint around the channel's line of 30, 365 and 3,650 days (about a month, a year and a decade), fixed
  before any data and tuned on no slope. The three scenarios share each data set's channel draw and its standard normal
  errors; only the scale differs. The same three scenarios draw f4-Q07's design curve (F-C2c).
- **Truth.** The pool's creator-balanced mean of the true slopes, for every method; every drawn channel enters every method.
- **Margin.** The regime distance 1 (deposit 5a, section 3.7); widths print in regime units.
- **Why the response is built.** TL-7.1's response (window midpoints) is model-coded and may not enter a label-free
  battery. The class keeps the real upload-day designs (count, spacing, span) and a real, label-free pattern of regimes
  and spreads across channels, so that any link between a channel's regime and its precision is the corpus's own and is
  not set by this card. No regime share, slope, span, spread or upload day is ever printed.

### 3.3 `K_kappa`: the kappa class (f4-Q09's primary; single agreement coefficients)

- **Units.** CAL's sentence units of 3 or more words (r3-P30's `D_superiority` unit rule), in recording order, each
  weighted by its word count.
- **Pool.** Seen creators with 30 or more such units (r3-P30's `E_rank_correlation` floor).
- **Reference coding R** (three categories, rule-based from the cache's own per-unit fields): a hedge or condition marker
  present (the marker of r3-P30's `B_share_difference`); otherwise a future marker present (the marker that defines
  the future-marked units of r3-P30's `E_rank_correlation`); otherwise unmarked.
- **Coding W5:** the word-weighted most frequent R category among the unit and the two units on each side within its
  recording (the window of f4-Q09 (vi)'s proxy); ties go to the unit's own R category, then in the order
  hedge-or-condition, future, unmarked. **Coding W3:** the same over the unit and one unit on each side.
- **Estimands** (one set of data sets, two choice cells):
  - `K_kappa_diff`: word-weighted Cohen's kappa of W5 against R minus that of W3 against R, pooled over every unit of the
    data set's creators (a creator drawn twice enters twice). The analogue of f4-Q09's primary: a coder that reads
    context, against the reference, minus a second coder against the same reference, on the same units.
  - `K_kappa_single`: the word-weighted kappa of W5 against R (single agreement coefficients, such as T-C1a's step
    kappas and f4-Q09's sensitivity rows).
- **Construction.** Each pool creator's two word-weighted 3 × 3 tables are built once; a data set (and each bootstrap
  resample) sums its drawn creators' tables.
- **Truth.** Each estimand on the whole pool, each creator once. **Margin** 0.10 (deposit 2, agreement coefficients).
- **Limits.** The analogue has no fitting step, so the variance that cross-fitting adds to f4-Q09's proxy is not
  calibrated here; T-C1a's kappas weigh statements, not words. If either marker is not stored per unit in the cache, the
  class stops and the lead is told; the run chooses no substitute.

### 3.4 The three other classes deposit 5 names (f4-Q09 (ii))

- **`C_standardised_xfit`: cross-fitted standardised contrasts** (f4-Q05b's standardised rows; any X+T standardised row).
  r3-P30's `C_standardised` analogue (CAL's own H4a code: the contraction share, middle block minus edges, both sides 10
  or more contractible forms; creator mean of recording values), with the standardiser cross-fitted. In each data set the
  distinct drawn creators are split by the data set's stream into two folds as equal in size as possible (every copy of
  a creator drawn twice stays in its fold); each fold's values are divided by the between-creator SD of the edge share
  over the other fold's distinct creators. A fold with fewer than 2 distinct creators gives the data set no interval.
  Truth: `C_standardised`'s (the pool's standardiser). Margin 0.20 SD.
- **`P_paired_persistence`: paired persistence** (later waves' persistence rows; no fourth-panel entry reads it at a
  count). Pool: seen creators with 6 or more recordings with a defined log words per minute. In each data set, for each
  draw, 3 of the creator's recordings are drawn at random as the "new" set (f4-Q13's smaller draw, k = 3); the value is
  the mean log words per minute of the new set minus that of the creator's other recordings. Truth 0 (new and old are
  exchangeable within creator by construction). Margin 0.223.
- **`I_icc`: the ICC class** (a retest ICC on recordings never opened, class b; no fourth-panel entry reads it at a count).
  Pool and split as `P_paired_persistence`, on its own stream. Over the data set's draws (rows) and the two sets
  (columns), the two-way single-measure ICC in two forms, two choice cells: `I_icc_cons` (consistency) and `I_icc_abs`
  (absolute agreement). Truth: for each form, the mean over 2,000 seeded splits (truth stream, section 8) of the pool's
  ICC, each pool creator once. Margin 0.10.

### 3.5 The eighteen choice cells

| Part | Choice cells | Margin | Default (the role `t_cm` has in r3-P30) |
|---|---|---|---|
| r3-P30's nine | `A_log_ratio` to `H_rare_counts` | r3-P30's | `t_cm` |
| Precision-weighted slopes | `F_slope_pw_s30`, `F_slope_pw_s365`, `F_slope_pw_s3650` | 1 regime unit | `t_cm` (the unweighted t on channel slopes, deposit 5a's comparator) |
| Kappa | `K_kappa_diff`, `K_kappa_single` | 0.10 | `kb_pct` (the registered creator bootstrap, deposit 5a, section 2.2) |
| Cross-fitted standardised | `C_standardised_xfit` | 0.20 SD | `t_cm` |
| Paired persistence | `P_paired_persistence` | 0.223 | `t_cm` |
| ICC | `I_icc_cons`, `I_icc_abs` | 0.10 | `kb_pct` |

---

## 4. Methods

Every interval is 90% two-sided. "Selectable" means the choice rule may name it.

| Id | Method | Cells | Selectable |
|---|---|---|---|
| `t_cm` | t interval on creator values (creator means; for the slope classes, channel slopes), k − 1 degrees of freedom | all but K and I | yes; the default |
| `boot_pct`, `boot_t`, `hl`, `two_stage`, `re_dl`, `re_hksj`, `re_hksj_floor`, `dl_boot`, `rec_t` | r3-P30's methods, with r3-P30's code and resamples (999) | r3-P30's nine, exactly as r3-P30 ran them per class; `C_standardised_xfit` takes every method r3-P30 ran for `C_standardised`, on the cross-fitted values; `P_paired_persistence` takes `boot_pct`, `boot_t` and `hl` | yes, except `rec_t` (shown, never selectable, as in r3-P30) |
| `boot_pct_refit` | creator bootstrap percentile, 999 resamples, the folds redrawn and the standardiser refitted in each resample | `C_standardised_xfit` | yes |
| `re_hksj`, `re_hksj_floor` | inverse-variance random effects (DerSimonian-Laird between-channel variance) with Hartung-Knapp-Sidik-Jonkman, without and with the DerSimonian-Laird floor, t on k − 1 degrees of freedom | `F_slope_pw` | yes |
| `reml_satt`, `reml_kr` | REML random-slope model on the units (channel intercepts as fixed effects, a random slope per channel, one residual variance); the fixed slope's t interval on Satterthwaite or Kenward-Roger degrees of freedom (Kenward-Roger also adjusts the SE) | `F_slope_pw` | yes, if run (section 11, point 2) |
| `wcb_webb` | wild cluster bootstrap-t: the pooled within-channel least-squares slope with a CR1 cluster-robust SE; residuals multiplied by one Webb weight per channel (six points, plus or minus √(1/2), 1 and √(3/2), each with probability 1/6), unrestricted, 999 replicates; percentile-t interval | `F_slope_pw` | yes |
| `pw_t_trunc90` | precision-weighted t: weights 1/v, each capped at the 0.90 quantile of the data set's weights; estimate Σwb/Σw; SE² = [k/(k − 1)] Σw²(b − estimate)²/(Σw)²; t on k − 1 degrees of freedom | `F_slope_pw` | yes |
| `kb_pct` | creator bootstrap percentile, 2,000 resamples | K, I | yes; the default |
| `kb_basic` | basic (reverse percentile) bootstrap, the same resamples | K | yes |
| `kb_bca` | bias-corrected and accelerated bootstrap, the same resamples, the acceleration from the delete-one-creator jackknife | K, I | yes |
| `kb_t` | bootstrap-t, 2,000 resamples, each resample's SE from its delete-one-creator jackknife | K | yes |
| `jack_t` | delete-one-creator jackknife SE around the full estimate, t on k − 1 degrees of freedom | K | yes |
| `t_creator` | t interval on per-creator values of the estimand (a creator-balanced estimand, not the pooled one) | K | never (shown) |
| `icc_f` | the F-based interval for the form (McGraw and Wong 1996) | I | yes |

For r3-P30's methods, r3-P30's own code and its handling of degenerate resamples apply. For every new method, a data set
in which it returns no finite interval counts as not covering and in neither one-sided miss, and the share of such data
sets prints (`no_interval_share`).

---

## 5. Counts

**The grid** (creators, or channels, simulated per data set; design constants, never counts of any group): 5, 8, 9, 10,
11, 12, 14, 18, 19, 20, 22, 23, 29, 30, 39, 40, 48, 49, 50, 59, 60, 67, 69, 70, 71. It holds r3-P30's original grid (5,
8, 12, 18, 23, 30, 40, 50, 71).

**The used counts** are every grid count but 8. Each is a count printed on main or an edge of a printed count form that a
fourth-panel entry uses:

| Count | Why it is used (all printed on main) |
|---|---|
| 11, 23, 48, 71 | the published voice-eligible set, the published reference, the development creators, the seen creators (deposit 5, sections 2.2 and 2.5) |
| 5, 9 | the privacy floor ("not computed" below 5) and the band "5 to 9" (r4-P23's printed eligible set; deposit 5a, section 2.5) |
| 10, 19; 20, 29; 30, 39; 40, 49; 50, 59; 60, 69 | the ten-bands of the register's printed forms (deposit 5a, section 2.5), among them r3-P36's "10 to 19" and "40 to 49" |
| 67, 70 | "all but fewer than 5 of" the 71 (deposit 5a, section 2.5) |
| 12, 22 | A8's floor and the band "12 to 22" (deposit 5, section 4.6) |
| 18 | "standardised features need 18 or more" (section 4.6); "18 to 39 eligible" (section 4.4) |
| 29, 30, 39, 40 | "23 to 29" (section 4.6); "30 or more creators" (section 4.3); "18 to 39" (section 4.4); "the 40 row" and "about 40" (sections 4.1, 4.2, 4.12) |
| 59 | the creators with a closed window (deposit 5a, section 2.5) |
| 10, 14 | TL-7.1's printed channel band "10-14" (r3-P36's published slopes), for the slope class |

**Reading a row.** (a) An exact count on the grid reads its own row. (b) An exact count off the grid reads the row of the
largest grid count at or below it (r3-P30's rule). (c) A banded count reads the band rule (section 7.5), so that no
choice reveals a withheld count. (d) Below 5: "not computed".

---

## 6. Data sets

- **Per cell:** 20,000 simulated data sets per cell and count at the used counts; 2,000 elsewhere (count 8), as the
  programme's dependency table fixes. `P_paired_persistence` and `I_icc` have no used count (no fourth-panel entry reads
  them at a count), so they take 2,000 at every grid count.
- **Resamples:** 999 per bootstrap interval of r3-P30's methods and of `boot_pct_refit` and `wcb_webb` (as r3-P30); 2,000
  for `kb_pct`, `kb_basic`, `kb_bca` and `kb_t` (deposit 5a's registered kappa interval).
- **Design totals** (data sets, each evaluated by every method of its cell):

| Part | Data-set cells | Data sets |
|---|---|---|
| r3-P30's nine | 9 | 9 × (24 × 20,000 + 2,000) = 4,338,000 |
| `F_slope_pw` (three scenarios) | 3 | 3 × 482,000 = 1,446,000 |
| `K_kappa` (two estimands, one set) | 1 | 482,000 |
| `C_standardised_xfit` | 1 | 482,000 |
| `P_paired_persistence` | 1 | 25 × 2,000 = 50,000 |
| `I_icc` (two forms, one set) | 1 | 50,000 |
| **All** | 16 | **6,848,000** |

- The Monte Carlo SE of a coverage near 0.90 is √(0.9 × 0.1 / n) for n data sets (0.0067 at 2,000, as r3-P30 printed).
  No time estimate is printed here.

---

## 7. Measures and the rule for choosing

### 7.1 Truth, coverage and misses (as r3-P30)

Coverage is the share of a cell's data sets whose 90% interval contains the cell's truth (section 3). The lower miss is the
share of intervals lying wholly above the truth, the upper miss the share wholly below (nominal 0.05 each; the size of the
floor rule's one-sided test).

### 7.2 Measures per method, cell and count

As r3-P30 printed them: `coverage_90`, `coverage_error` (coverage minus 0.90), `lower_miss`, `upper_miss`,
`mean_width_in_margins` (mean interval width divided by the cell's margin), `monte_carlo_se`. Added: the Monte Carlo 95%
interval (Wilson score) of the coverage and of each one-sided miss; the Monte Carlo SE of the mean width;
`no_interval_share` (section 4); `holds_deposited` and `holds_smoothed` (section 7.3).

### 7.3 When a method holds

- **Deposited rule (r3-P30's, printed beside):** coverage within 0.02 of 0.90 and each one-sided miss 0.07 or less.
- **Smoothed rule (version 2's, binding):** the Monte Carlo 95% interval of the coverage overlaps 0.88 to 0.92, and the
  lower end of the Monte Carlo 95% interval of each one-sided miss is 0.07 or less. A method thus fails to hold only where
  it misses the tolerance by more than Monte Carlo error.

### 7.4 The choice at a cell and count (fixed now)

1. If the cell's default (section 3.5) holds under the smoothed rule, it is chosen.
2. Otherwise, among the selectable methods that hold under the smoothed rule, the narrowest (smallest mean width in
   margins) is chosen: methods that hold within Monte Carlo error are treated as tied on coverage, and ties go to the
   narrower method. Equal widths to four decimals go to the smaller absolute coverage error, then to the order of section 4.
3. If none holds, the selectable method with the smallest absolute coverage error is named (ties: the narrower) and
   flagged "no method holds"; deposit 2 calls such a count "a reference that does not hold its size at the count".

Printed beside, never binding: the choice of r3-P30's deposited rule (section 7.3) on version 2's data sets, and
r3-P30's printed choice at the r3-P30 row the count reads (the largest r3-P30 grid count at or below it).

### 7.5 Bands and the slope scenarios

- **The band rule.** A printed band reads the grid counts from the largest grid count at or below its lowest possible
  count to the largest grid count at or below its highest. Its choice: the cell's default if it holds (smoothed) at every
  one of them; otherwise the selectable method that holds at every one with the smallest mean, over them, of its mean
  width in margins; otherwise "no method holds across the band", naming the method with the smallest largest absolute
  coverage error over them. Bands printed in the band table: "5 to 9", the ten-bands "10 to 19" to "60 to 69", "all but
  fewer than 5 of" the 71; for the slope cells also TL-7.1's "10-14" and r3-P36's "all but fewer than 5 of" it. A printed
  form an entry uses later takes the same rule on the printed grid table, with no new simulation.
- **The slope scenario rule (f4-Q07; T-Q07-2).** As the band rule, with "at every grid count of the band" read as "at every
  grid count of the band in each of the three scenarios", and the width averaged over the band's grid counts in the
  middle scenario (365 days). The real residual variance is never estimated to pick a scenario.

### 7.6 Choice stability

For each choice cell and count: 1,000 resamples of the cell's data sets, drawn with replacement with every method's
outcomes kept together (stability stream, section 8); the rule of section 7.4 is applied to each. **Choice stability** is the
share of resamples whose choice equals the choice on all the data sets; the most frequent other choice and its share print
beside. Also printed: whether the choice equals r3-P30's printed choice, the deposited rule's choice and the choice at the
next grid count.

### 7.7 Size panel and readings table (as r3-P30)

- **Size panel:** per method, the one-sided misses, their sum and the larger one; for cells with creator values (r3-P30's
  nine, `F_slope_pw`, `C_standardised_xfit`, `P_paired_persistence`), r3-P30's creator-level sign-flip test of the truth
  (999 random signs), two-sided at 0.10. For K and I: "not applicable (pooled or across-creator estimand)".
- **Readings table** (r4-P10's residual): for each cell's chosen method at each count, with the true effect at 0, 0.5, 1,
  1.5 and 2 margins (r3-P30's shift model), the share passing the floor rule, read A and read B. Not for `F_slope_pw`
  (tier D, no reading words). For K and I the shift moves the coefficient without regenerating the codings, as r3-P30's
  shift moved AUC values without clipping. At 0.5 margins this is the per-primary rate behind deposit 5's disclosure (K =
  33, about 1.65 expected passes); f4-Q09's ledger prints the class range beside it, as r3-P30 did for the third panel's 56
  and its 2.8.

---

## 8. Seeds (design constants)

- **Base seed `2026112771`.** It is new: deposit 5 uses `2026112761` to `2026112767` and `20261127`, deposit 5a uses
  `2026112751` and `2026112752`, the frozen ledger `2026112601`, and r3-P30 `2026112630`. It is used nowhere else in
  deposit 5.
- **Streams**, derived as r3-P30 derived its own (a generator seeded with the base seed and the CRC-32 of a key):
  `<cell>|<count>` for a cell's data sets; `<cell>|<count>|stability` for its choice-stability resamples;
  `F_slope_pw|pool` for the slope class's fixed unit draws; `I_icc|truth` for the ICC truth's splits. The three slope
  scenarios share the stream `F_slope_pw|<count>`; K's two estimands and I's two forms share their class's stream.
- r3-P30's pools keep the draws r3-P30 fixed in them; only the simulation streams are new.

---

## 9. Order of runs and machine rules

1. **This card is hashed first** (the addendum's private hash record). Then the battery's code is written to this card;
   its SHA-256 is recorded in the run's status file before the first cell runs. Any detail this card leaves open is fixed
   in the code's header before the run and listed in the run's README as a departure; nothing fixed here changes.
2. **Checks before the first cell:** every hash of section 1; the state of the package ruling for `reml_satt` and
   `reml_kr` (section 11, point 2), recorded; free memory commit.
3. **One background job, one worker** (a single process, no pool): the guarded analysis environment with isolated Python
   (`-I`), its memory guard never switched off and its ceiling never raised. At most two heavy jobs at a time on the
   machine, the GPU re-decode counting as one while it runs. The job holds only the small pools and one cell's arrays in
   memory; a cell that reaches the ceiling is split into smaller chunks of data sets, never given a higher ceiling.
4. **Cell order:** `F_slope_pw` (f4-Q07 waits on it), then `K_kappa`, then r3-P30's nine in r3-P30's order, then
   `C_standardised_xfit`, `P_paired_persistence` and `I_icc`; counts in ascending order within a cell. Each finished cell
   writes its row to the run's ledger; after any stop the job resumes from the ledger with the same streams.
5. **After the last cell:** the public files of section 10, the identifier scan, the private-path search and the name
   screen, the hashes; then a dated addendum, one independent check and one PR. The battery and that deposit come
   **before f4-Q07's slopes and before f4-Q09** (deposit 5a, section 3.15; deposit 5, section 3.3). An entry that prints
   before then shows version 2's column as "pending".
6. **No model or API call; no download.** No hold-out, other-group or reliability folder and no split file is opened.

---

## 10. Printing

Every public file carries in its header the status label, the agnosticism sentence and what the file is, as r3-P30's
files do. Every caption also says: label-free analogues of seen creators, recognizer output not checked by a person; the
data sets per point; "creators simulated is a design constant, not a count of any group"; the files it draws on.

### 10.1 Tables (CSV)

| File | Rows | Columns |
|---|---|---|
| `interval-choice-v2.csv` (the table entries read) | choice cell × grid count | cell, what it is, margin, creators simulated, data sets, used count (yes or no), chosen method and its name, holds (smoothed), coverage with its Monte Carlo 95% interval, lower and upper miss each with its Monte Carlo 95% interval, mean width in margins with its Monte Carlo SE, choice stability, the most frequent other choice and its share, the deposited rule's choice and whether it holds, the r3-P30 row read, r3-P30's printed choice and whether it held, same as r3-P30 (yes, no, or "no r3-P30 class"), the default's coverage and whether it holds (smoothed), note |
| `T-Q09-1-choice-v2.csv` | the rows of `interval-choice-v2.csv` at the used counts | version 2's choice with coverage, Monte Carlo interval, holds and width, beside r3-P30's choice with its coverage and holds (f4-Q09's T-Q09-1) |
| `T-Q07-2-slope-choice.csv` | `F_slope_pw`: scenario × grid count × candidate; then each printed band | every candidate's coverage, misses (each with its Monte Carlo 95% interval), mean width in regime units, holds (smoothed); the chosen method per scenario and count; the scenario rule's choice per band (deposit 5a's T-Q07-2) |
| `interval-choice-v2-bands.csv` | choice cell × printed band | the band, the grid counts it reads, the band's choice, whether it holds across the band, the lowest coverage and the largest one-sided miss over those counts, the range of mean widths in margins |
| `data-r3-P30v2-coverage-grid.csv` | choice cell × method × grid count | r3-P30's columns, plus the Monte Carlo intervals, `no_interval_share`, `holds_deposited`, `holds_smoothed` |
| `data-r3-P30v2-size.csv` | as r3-P30's size panel | r3-P30's columns; "not applicable" for K and I's sign-flip test |
| `data-r3-P30v2-readings.csv` | choice cell (not `F_slope_pw`) × grid count × true effect | r3-P30's columns |
| `data-r3-P30v2-classes.csv` | choice cell | what it is, margin, pool (band), `sd_in_margins` (for r3-P30's nine as r3-P30 printed it, and for `C_standardised_xfit`, `C_standardised`'s; "not printed" for the others), default method, data sets at the used counts and elsewhere |

### 10.2 Figures (PNG at 200 dpi and PDF without document information, each with its data CSV)

- **`fig-r3-P30v2-coverage-grid-a`** (r3-P30's nine) and **`-b`** (the nine new cells): r3-P30's layout. Rows: cell and
  method; x: creators simulated (the grid). Left: coverage minus 0.90, diverging colour saturating at plus or minus 0.10;
  right (size panel): the larger one-sided miss, 0 to 0.20. A dot marks version 2's chosen method, a ring a method named
  although none holds, and a square outline r3-P30's printed choice where it differs.
- **F-C2b, the slope class's coverage grid** (deposit 5a, section 3.11): one row of panels per scenario. Left: x, channels
  simulated (5 to 71); y, 90% coverage, one line per candidate, the band 0.88 to 0.92 shaded. Right: the larger one-sided
  miss per candidate, with a line at 0.07.
- **`fig-r3-P30v2-readings`:** r3-P30's layout, one panel per cell (not `F_slope_pw`): x, the true effect in margins (0
  to 2); y, the share read A; one line each for 12, 23, 40, 48 and 71 creators simulated; a dashed line at 0.05. The
  caption carries deposit 5's disclosure (K = 33, about 1.65) beside the third panel's 56 and 2.8, and "a reading A is
  never called a finding".
- **`fig-r3-P30v2-choice-stability`:** x, creators simulated (the grid); y, choice cell; tile colour, choice stability (0
  to 1); in each tile the chosen method's id; an outline where it differs from r3-P30's printed choice; a ring where no
  method holds.

### 10.3 Privacy (deposit 5, section 2.5)

- Every simulated count is 5 or more, so no cell rests on fewer than 5 creators. No per-creator or per-channel value,
  row or point exists in any public file; nothing is drawn per creator.
- Each pool prints only as a band in the register's printed forms (`pubrules.Register`), registered against every printed
  group (the 71, the 48, the 23, the 11, every printed nested set), so that no printed count narrows another; r3-P30's
  nine print as r3-P30 printed them ("between 60 and 71 of the 71 seen creators").
- No pool truth, regime share, slope, span, spread, upload day or kappa of the pool is printed.
- Every public file passes the identifier scan, the search for private paths and the name screen against the people
  directories before it is published.

### 10.4 Labels

Every file and caption: "Exploratory; not a test of H1-H10." and "No measure in this study can tell whether a non-human
source speaks; every measure describes the speech in these recordings and how the creators present it."

---

## 11. Departures from r3-P30 and points for the lead

**Departures from r3-P30, fixed here:** the new base seed; the denser grid; 20,000 data sets at the used counts; the
smoothed rule binding, with r3-P30's rule printed beside; Monte Carlo intervals and choice stability; the band and
scenario rules; the no-interval rule for new methods; 2,000 resamples for K's and I's bootstraps; the built response of
`F_slope_pw`; one worker instead of r3-P30's four.

**Points for the lead, before the run:**
1. **Classes.** The brief names r3-P30's classes, the slope class and a kappa class; deposit 5 (section 4.9) also names
   paired persistence, an ICC class and cross-fitted standardised contrasts as version 2's new classes. This card
   includes all three; the two persistence classes take 2,000 data sets at every count because no fourth-panel entry
   reads them at a count. Dropping any of them before the run is a dated note that prints as a departure.
2. **`reml_satt` and `reml_kr` need a package** that fits REML random-slope models with Satterthwaite and Kenward-Roger
   degrees of freedom in the guarded environment (the programme's section 8, item 3, the owner's act). Without it, both
   print "not run (package ruling pending)", the choice is made among the other candidates, and no home-made substitute
   is used. The lead decides whether the battery waits for the ruling.
3. **Where version 2 finds no method holds** at a class and count where r3-P30 found one, deposit 2's words ("a reference
   that does not hold its size at the count") would cap a fourth-panel reading at "undetermined"; deposits 5 and 5a say
   only that version 2's choice prints beside the fixed interval (slopes apart). Whether such a cell caps a reading is a
   ruling before any count.
4. **Size of the job:** 6,848,000 simulated data sets in all (section 6). The used counts follow the programme's "edges of
   printed bands"; a smaller set (the exact counts and the counts deposit 5's decidability lines name) would shrink the
   job, at the cost of 2,000-data-set cells at the ten-band edges that the band rule reads.
5. **Whether the battery waits for this addendum's merge** before it runs (r3-P30 ran only after its deposit merged);
   this card asks only that it run after the card is hashed.

---

## 12. What this card does not do

It runs nothing and computes nothing; it tunes no rule and reads no contrast, label, forecast, voice or outcome; it re-reads
no published entry; it changes no registered margin, reading word, interval or tier; it makes no model or API call; it opens
no hold-out, other-group or reliability folder and no split file.
