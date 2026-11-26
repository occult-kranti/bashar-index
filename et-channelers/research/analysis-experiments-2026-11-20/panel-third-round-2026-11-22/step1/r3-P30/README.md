# r3-P30: calibration battery for interval methods (with r4-P10's residual)

Third-round programme, step 1 (class a.1; its method card is in deposit 2). Written 2026-11-26T02:47:28Z (UTC, from
`date -u`) by a step-1 agent (a model agent working for the project lead; not a person). Exploratory; not a test of
H1-H10. Seen creators only; no label, no model call, no download.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Question

Which 90% interval should each class-a entry use at its creator count and data structure, so that a 90% interval covers
about 90% and the floor rule's one-sided 5% test keeps its size (programme 2.1, r3-P30; deposit 2's method card)? And,
as r4-P10's residual, how often do the register's fixed procedures (the floor rule, readings A and B at the deposited
margins) fire when the true effect sits at 0, half, one, one and a half and two margins?

## Base

Label-free analogues built from the seen creators' recognizer output: CAL's private numeric cache (counts per sentence
unit, seen creators only, SHA-256 `9383c3fd…c2ba`). Nine design classes, each a pool of between 60 and 71 of the 71 seen
creators (exact pool sizes withheld, nested-count rule). Because no label is read, no model-coded value enters this
entry; recognizer output is not checked by a person.

## Method (fixed in `code/prespec.json` at 02:24:29Z, before any pool or simulation existed)

**Prespecification timing** (added for publication, 2026-11-26; the lead's step-1 decision 43). `code/prespec.json` is published as `prespec.md` (a redacted copy, one private path replaced; its bytes are otherwise JSON). The recorded fixing time (02:24:29Z) precedes the file's last write (02:24:59Z) by under a minute. The file was not written again before the pools were built (about 02:26Z) and the battery ran (02:27:13Z to 02:31:57Z). Its SHA-256 was recorded by the battery at 02:31:57Z, so the order rests on the file's last-write time.

- **Design classes** (with the deposited margin of their measure type): A log ratio of rates between two parts of a
  recording, creator means (0.223); B difference in shares, creator means (5 points); B1 the same with one recording per
  creator, the design of BR-GS's and the bridge's bases (5 points); C standardised difference (0.20 SD); D probability of
  superiority within a recording (0.10); E within-creator rank correlation, one value per creator (0.10); F
  within-creator slopes on 3 to 8 points with their own variance, TL-7.1's design class (no slope margin is deposited:
  0.20 between-creator SD of the slopes, flagged); G per-creator differences between two classes of 2 to 5 recordings
  (0.223); H rare counts, log rate ratio with 0.5 added (0.223).
- **Methods:** t interval on creator means (`t_cm`, the deposit's default), creator bootstrap percentile and bootstrap-t,
  Hodges-Lehmann with the exact signed-rank interval, two-stage bootstrap (creators, then recordings), DerSimonian-Laird,
  HKSJ, HKSJ floored at the DL SE, DL with a creator-bootstrap percentile (TL-7.1's method, class F), and a t interval
  on recordings that ignores creators (shown, never selectable).
- **Counts simulated:** 5, 8, 12, 18, 23, 30, 40, 50, 71 creators, drawn with replacement from the class's pool (the
  pool is the population). These are design constants, not counts of any group. An entry with c eligible creators reads
  the row of the largest value at or below c.
- **Draws:** 2,000 simulated data sets per class, count and method (Monte Carlo SE of a coverage near 0.90 about
  0.007); 999 resamples per bootstrap interval; seeds fixed. Coverage is read at the pool's creator-balanced mean
  (for the random-effects methods, at the mean of the creators that enter them).
- **Holds:** coverage within 0.02 of 0.90 and each one-sided miss 0.07 or less. **Choice:** `t_cm` if it holds; else the
  holding method with the smallest coverage error; if none holds, the method with the smallest error is named and
  flagged, and a reading at that class and count is at most "undetermined" (deposit 2).
- **Size panel:** one-sided miss rates of every interval (nominal 0.05 each) and the creator-level sign-flip test (999
  random signs), two-sided at 0.10.
- **Readings table (r4-P10's residual):** the pool centred at 0 and shifted by delta (shift model; all methods used are
  translation-equivariant); for the chosen method, the share of data sets whose near bound lies beyond half the margin
  (floor rule), read A and read B.
- Run: `build_pools.py` 02:26Z; `battery.py` 02:27:13Z to 02:31:57Z (282 s, 4 worker processes, each passed one class and
  count and the small pools file), under `run_locked.sh`.

## What it shows (`public/interval-choice.csv` is the table the other step-1 entries read)

- **Ignoring creators is never admissible:** the t interval on recordings covers 39% to 71% in every class and count.
- **TL-7.1's slope pooling fails:** for class F, DerSimonian-Laird, its bootstrap (TL-7.1's method) and HKSJ cover the
  creator-balanced mean slope in 0.5% to 57% of data sets, falling as creators are added (they target a precision-weighted
  mean that differs from it when slopes and their precision go together); the t interval on slopes rises from 0.73 at 5
  creators to 0.89 at 71. No method holds below 71 creators, so a TL-7.1-style slope reading at its count is at most
  "undetermined" (relevant to r3-P36).
- **`t_cm` holds** for E (rank correlation) at every count; for H (rare counts) and B1 (one recording per creator) at 8
  creators or more (at 5: Hodges-Lehmann for H, bootstrap-t for B1); for G (2 to 5 recordings per class) at 12 or more
  (at 5 bootstrap-t, at 8 Hodges-Lehmann); and for C at 30 or more.
- **Where `t_cm` does not hold:** A (log ratio of rates) at every count (coverage 0.873 to 0.899, upper misses above
  0.07); HKSJ holds at most counts, none at 23 and 71. B (shares, creator means) at 12, 23, 30, 40, 50 and 71 (coverage
  0.884 to 0.920); Hodges-Lehmann or a random-effects interval holds instead, none at 30. D (probability of superiority):
  no method holds at any count below 71 (one-sided misses 0.07 to 0.11 from skew), so D readings are at most
  "undetermined" below 71. C below 18: none holds at 5, 8 and 12.
- **Size panel:** the sign-flip test's two-sided size at 0.10 lies between 0.06 and 0.13 for every class except F (0.11 to
  0.26).
- **Readings of the fixed procedures:** with the true effect at half the margin, the floor rule passes in 0.05% to 10.9%
  of data sets (above 5% for B, C, D and E at most counts; 7.5% to 10.9% for C at 5 to 12 creators and D at 5 to 18), and
  reading A in almost none. With no effect, reading B is near certain for A, B and D at 12 or more creators but rare for F and H (at
  most 0.47 at 71). With the effect at one and a half margins, reading A comes in 2% (F, 12 creators) to 100% (A).

**Half-effect disclosure** (deposit 2): the register holds 56 primaries; if every true effect sat at half its margin,
about 0.05 x 56 = 2.8 readings would pass the floor rule by chance at the 90% level's one-sided 5%. This battery shows
the per-primary rate behind that figure is 0.001 to 0.109 depending on class and count, so 2.8 is an approximation that
understates the rate for classes B to E (up to about 0.109 x 56 = 6.1 in the worst cell) and overstates it for F. A
reading A is never called a finding.

## Readings

None: r3-P30 is a method card's run (register kind "act"); it picks interval methods and reads no contrast.

## Files

| File | What | SHA-256 |
|---|---|---|
| `public/interval-choice.csv` | Chosen method per class and count, whether it holds, its coverage, misses and width; `t_cm`'s coverage beside it | `fcfe22cfba84b8b5eedd059ff605afb0055761b88c4c4d96e708d24400a6e1f6` |
| `public/data-r3-P30-coverage-grid.csv` | Coverage, error, one-sided misses, width and Monte Carlo SE of every method (figure data) | `4a4412acd8befa4ceda22d7da63044bb197c161effe9d4d4e7534f4a3fe99930` |
| `public/data-r3-P30-size.csv` | Size panel: one-sided misses per method, sign-flip size | `f6496eab5ba96e1ac5b5af324a954829e77c219a560affd0f6064b7c46d72afc` |
| `public/data-r3-P30-readings.csv` | r4-P10's residual: floor-rule pass, reading A and B by true effect (figure data) | `29c7583af74bda194acecebea37b88ba9fa3449069b33f8bc6874ae1d24b177e` |
| `public/data-r3-P30-classes.csv` | The nine classes, margins, pool band, between-creator SD in margins | `314d359d6ddb8006d13ebbceab0b6dd6e5b2b8058e22243edc3a2802215cf283` |
| `public/fig-r3-P30-coverage-grid.png` / `.pdf` | Coverage grid with the size panel (200 dpi; PDF without document information) | `667ac026af6ec95b21f0aed762e8b47b62ad9df039693fc4e8eaedfc87d98772` / `e6a1c99d97a07ff78674e650fcfe7d419775c3052d81c42d75e1ea0681130e77` |
| `public/fig-r3-P30-readings.png` / `.pdf` | Share read A against the true effect, per class | `576cb99826c98713f321ed8fceee68f0bd5b147f98e7244220e97dbc6e704b12` / `633cd905f055de41976edb29495182937b380cea1a6f99c0d65d4ebd1a811a96` |
| `code/prespec.json` | The design, fixed before the run | the hash recorded at hashing time is kept privately |
| `code/build_pools.py` | Class pools from CAL's cache (private output) | `01facd62f515e6a289d62a734577a2f2182a85561497649b59c487062e339f56` |
| `code/battery.py` | The battery (private output) | `24367d512882a2dde275ad035605a0c233eb377ce50cd10ec0e2b274bf5688cf` |
| `code/write_public.py` | Public tables | `f847f4000b2711f4e356569310be02089d3b7c9cd8f36f7815cf5da9cd135d89` |
| `code/plot_p30.py` | Figures | `3a5c3d177838009db74b94efae490d492b0ee12e0377b338d055fe70048659c4` |
| `code/style.py` | Chart style, copied unchanged from the CHANGE group's private plotting code folder | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |

Private (not published): `private/pools.private.pkl`, `private/battery.private.npz` (per-draw interval ends),
`private/battery.private.json`, logs.

## What is withheld, and why

- Exact pool sizes of the classes: printed as "between 60 and 71 of the 71 seen creators" (several pools are 1 to 4 below
  the 71 or each other; nested-count rule).
- No per-creator value or row exists in any public file.

## Departures from the programme, and choices it left open

1. The method card leaves open the classes, methods, counts, placebo scheme, draws, size and power targets and the
   selection rule; they were fixed by this agent in `code/prespec.json` before the run, from the step-1 entries' designs
   and CAL's methods. The lead may replace them.
2. Calibration rests on label-free analogues only; CAL-f's label-based parts (b) and (c) and the registered tests of H2,
   H3 and H6 (CAL reports them) were not re-run.
3. Not run (named in round 3's pooled method, not in the adopted programme text): circular, local-block and unit-shuffle
   references for autocorrelated series; blocked against unblocked curveball; rewired-dyad permutation; Freedman-Lane;
   pooled-ratio estimands (E1's pooled row is a different estimand from the creator-equal one).
4. 999 bootstrap resamples per interval (CAL used 2,000).
5. Class F's margin is not deposited (no slope measure type); 0.20 between-creator SD of the slopes is used and flagged.
6. The shift model moves AUC values without clipping at 0 and 1.

## For the lead to decide

- **The choice rule flips between neighbouring methods** where several sit within Monte Carlo error of the 0.02
  tolerance (class B: `t_cm`, Hodges-Lehmann and random-effects intervals alternate across counts; class A: HKSJ and
  floored HKSJ). The pre-specified choice is printed and binding here; whether to fix one method per class across counts
  is the lead's decision, not made after the results by this agent.
- **The random-effects choice can change the estimand.** Where a random-effects interval is chosen (A at most counts; B at
  50 and 71), its precision-weighted estimate can sit away from the creator mean in real data; r3-P02's primary I shows
  this (the floor rule then gives "undetermined", estimators disagreeing).
- **D below 71 creators, F below 71, A at 23 and 71, B at 30, C at 5 to 12:** no method holds; readings there are at most
  "undetermined".
- **The half-effect disclosure's 2.8** understates the chance passes for classes B to E (per-primary rate up to 0.109).

No contact with hold-out or other-group material (`contacts.md`).

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
