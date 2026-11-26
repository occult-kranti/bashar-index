# rv-R5: how is each measure's variance split between and within creators?

Exploratory (registry A2); not a test of H1-H10. Paper-review build item (built 2026-11-21 on seen creators; label
"Exploratory, paper review (registry A2/A7); not a test of H1-H10"), released in the public form of plan section 3 by
the release review (plan P10, 2026-11-22). It replaces the earlier draft's Table 7, Figure 2 and Figure A2.

## What it asks

What share of each word, timing and recognizer measure's variance lies between creators (ICC), on which scale, with
which interval; how much does a creator mean gain from more recordings (design effect, reliability); and how much does
shrinkage change creator pace?

## Base

One creator set: 71 seen creators, 1,211 English-only recordings with 60 s of speech and 200 or more words after
artefact filter v2 (MATTR: 1,106 recordings with 500 words). The earlier draft's own figures (snapshot of the run) are
listed beside the check of its Table 7.

## What is shown

| File | What it holds | Place |
|---|---|---|
| `public/rv-r5-vp1.csv` | Table VP-1: ICC raw and adjusted with both intervals, filter off, design effect, n_eff, reliability of a creator mean, split-half, length correlations | M |
| `public/rv-r5-icc.csv` | The ICC figure's numbers | M, W |
| `public/rv-r5-icc-scale.csv` | ICC of count measures on three scales | S |
| `public/rv-r5-pace-shrinkage.csv` | Raw and shrunken creator pace in bins of 5 or more creators (150 to 170 merged, see below) | S |
| `public/rv-r5-table7-check.csv` | Whether the earlier draft's Table 7 log-probability ICC carries over | S |

Figures (in the gallery, with their records in its `manifest.json`): rv-R5-a ICC figure (M, W), rv-R5-b pace
shrinkage (S).

Main readings:

- Pace 0.58 (95% creator bootstrap 0.47 to 0.66), share of time without speech 0.55 (0.41 to 0.67), contractions 0.72
  (0.57 to 0.77), repeated five-word share 0.37 (0.26 to 0.46), filled pauses 0.65 (0.50 to 0.75).
- The recognizer's log-probability measures have the lowest shares and the widest intervals: mean ln word probability
  per word 0.21 (0.06 to 0.53); the earlier draft's mean segment log-probability 0.40 (0.15 to 0.63), which reproduces
  its Table 7 (0.42 with Table 7's estimator and the filter off).
- The creator-resampling intervals are up to 3.6 times wider than the parametric ones (the log-probability rows); for
  pace about 1.1 times.
- For counts the ICC depends on the scale (first-person singular: 0.28 on the raw rate, 0.46 on the log rate, 0.53 on
  the negative-binomial latent scale).
- With about 17 recordings per creator the median shrinkage factor of pace is 0.96, so the raw spread (SD 17.5 words
  per minute) overstates the between-creator spread (16.8) only slightly.

## What is withheld, and why

- The creator counts of the split-half and within-creator correlation columns that lie within 1 to 4 of the 71 seen
  creators are printed as "all but fewer than 5 of 71" (plan section 3).
- **Pace-shrinkage bins 150 to 160 and 160 to 170** (fix pass, 2026-11-22): merged into one bin, 150 to 170, in both
  series. Shrinkage pulls every creator toward the grand mean by a near-constant factor (0.950 to 0.965 between the 10th
  and 90th percentile), so raw and shrunken bins that differ would bound the raw pace of the creators that change bin
  (pairs rule, addendum 2 item 9). After the merge the raw and the
  shrunken series hold the same number of creators in every bin.

## Interval level

95% creator-resampling bootstrap of the same estimator (1,000 draws; 200 for the negative-binomial rows): the interval
the text uses. 95% parametric bootstrap beside it for comparison only. Split-half: 95% creator bootstrap; within-creator
correlation with length: 90% t over creators. Note that this output's level (95%) differs from the 90% of most other
outputs of the round (D18).

## Caveats

- Every ICC is on the scale named in its row; ICCs on different scales are not comparable.
- The ICC is a design fact of this roster under the newest-20 quota; without a benchmark corpus it says nothing about a
  genre.
- Exploratory; not a test of H1-H10.
