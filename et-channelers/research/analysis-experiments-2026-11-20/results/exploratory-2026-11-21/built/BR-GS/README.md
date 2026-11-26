# BR-GS: how the recognizer's words and the seam measures move when the decoding grid is shifted (seen creators)

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Exploratory (registry A2); not a test of H1-H10. Plan section 6.7, row BR-GS. Built on 2026-11-21 before the exploratory
round; this public form was made by the release review (plan P10) on 2026-11-22 (tables written 05:17 UTC; revised after
the release verification, tables rewritten 05:56 UTC: values rounded once, merged-row and detection-rate wording).
Recognizer output, not checked by a person.

## What it asks

How much do the seam measures move when the decoding grid is shifted? The run's recognizer decodes each recording in
contiguous 30-s windows; a window boundary is a "seam". The plan asks for the change in thanks-phrase segments, isolated
segments, pause measures and word measures between grids, in between-creator SD units with intervals, and for a check of
the positional precision bound of the artefact filter (the rule that removes a thanks phrase starting in a window's last
3 s).

## Base

40 seen recordings, one per creator (40 creators), drawn at random before any decode from the seen English transcripts of
record of 2 to 90 minutes, and decoded again with the run's recognizer and settings but with the grid moved by 15 s (the
first window 15 s long, every later one 30 s). 10 of the 40 were also decoded again on the run's own grid, as controls.
No hold-out or other-group material was read.

## The answer

- **The controls reproduce the record.** On the 10 controls, decoding again on the run's own grid with the same worker
  reproduced the transcript of record word for word and gave identical values on every measure. This holds for these
  controls only: BR-b's reproducibility row (earlier workers of the same recognizer and settings) finds recordings that
  are not reproduced word for word.
- **The grid alone changes about 4 recognized words in 100**: 3.71% of words (mean over recordings; 95% interval 2.87 to
  4.90%), 4.16% pooled over words (3.08 to 5.38%); 4.28% (3.14 to 5.64%) for the 31 recordings whose transcript of
  record came from the same worker version as the re-decode.
- **The changes cluster at seams**: 20.14% of them lie within 1 s of a run-grid seam (17.47 to 24.29%) and 18.64% within
  1 s of a shifted-grid seam (15.89 to 22.99%), against 6.7% if they were spread evenly.
- **Seam signature.** In the first 0.25 s of a window, word onsets are 1.92 (run grid) and 1.97 (shifted grid) times the
  recording's mean density; in the last 0.25 s, 0.60 and 0.59 times. Measured on the other grid (a placebo), the ratios
  are 0.94 to 1.04.
- **No word crosses a seam of its own grid** (0 in every recording); on the other grid 72.14% and 71.22% of seams fall
  inside a word. On its own grid a seam falls in a pause of 0.3 s or more 35.24% and 35.61% of the time, against 22.27%
  and 22.47% on the other grid; but the share of the time within 1 s of a seam spent in such pauses is about the same
  (20.78% and 22.08% on the own grid, 22.37% and 21.41% on the other), and the whole-recording pause share moves by -0.14 points
  (-0.58 to +0.30). Recognized word counts move by -0.18% (-0.49 to +0.04%).
- **In between-creator SD units** (the SD across seen creators of creator means on the transcripts of record):
  - thanks-phrase segments per hour of speech change by **-0.40 SD (95% interval -0.88 to +0.08)**;
  - isolated segments by +0.04 SD (-0.02 to +0.15);
  - the pause measures by at most 0.12 SD on average (pauses of 0.3 to 1 s per speech minute: -0.12 SD, -0.30 to +0.03);
  - the word measures by at most 0.04 SD, except filled pauses per 1,000 words: +0.23 SD (-0.07 to +0.69);
  - recognized words per minute of speech (a recognizer-output measure, not a direct measure of speaking): 0.00 SD (-0.03
    to +0.01); recognized words per minute of the span without pauses of 0.3 s or more: -0.02 SD (-0.09 to +0.05).
  Every interval includes 0 (22 rows, pointwise; about 1 would fall outside 0 by chance).
- **Precision check of the positional rule** (public form fixed by addendum 2 item 4): the positional rule removes 55
  thanks-phrase segments on the run grid and 37 on the shifted grid. Searched for in the other decode, within 1 s and
  within 2 s, they give **fewer than 5 creators with a recurring removal** on both grids. No recurring share, precision
  band or detection rate is printed.

## What is shown

| File | What it holds | Place |
|---|---|---|
| `public/br-gs-sd-units.csv` | Change of each measure in raw units and in between-creator SD units, with 95% intervals; the thanks-phrase row in its public form only | M (beside rv-R7) |
| `public/br-gs-grid-shift-summary.csv` | Changed share of words, edits near seams, onset ratios, where seams fall, pause shares and word counts, with 95% intervals, and the controls | S |
| `public/br-gs-onset-position.csv` | Word-onset density by position in the window (120 bins of 0.25 s), each decode on its own and on the other grid | S |
| `public/br-gs-precision-check.csv` | The precision check of the positional rule, in the public form of addendum 2 item 4 | S |

Figures (gallery group B-BR): the SD-unit changes (BR-GS-fig-1, M), word onsets by position (BR-GS-fig-2, S), where seams
fall (BR-GS-fig-3, S), and the words changed and edits near seams (BR-GS-fig-4, S). The precision check has no figure (two
counts and a status, given in its table).

## What is withheld, and why

| Part | Public form | Reason |
|---|---|---|
| Recurring removals, recurring share, precision band | "fewer than 5 creators with a recurring removal"; no share, no band | the recurring removals come from fewer than 5 creators; a band read with that status would bound such a cell (addendum 2 item 4) |
| Detection rate on the thanks phrases the filter keeps | "not estimable" | public form fixed by addendum 2 item 4 |
| Thanks-phrase row: SD, means on each grid, change per hour | not published | BR-GS's public form for thanks phrases is the change in SD units (addendum 2 item 4, as the lead fixed it for this release) |
| Thanks phrases in a window's last 3 s; thanks phrases removed by the filter | merged into the row of all thanks phrases | addendum 2 item 7 (rows that rest on fewer than 5 creators or give such a cell by difference are merged) |
| Isolated segments of 1 to 3 words removed by the filter | merged into the row of all isolated segments | it rests on fewer than 5 creators (addendum 2 item 7) |
| 10th and 90th percentiles of the per-recording change | not published | with 40 recordings each would rest on one or two recordings |
| Number of recordings with a removal; number of creators behind the SDs | not printed | not part of the public form fixed for BR-GS (addendum 2 item 4) |

Every printed row is non-zero in 5 or more recordings (one per creator) on each grid and in the change, or 0 in every
recording; no two printed rows differ in fewer than 5 recordings. The release review rechecked every printed row against
the item's seen per-recording values (2026-11-22, 05:15 UTC; again after the revision, 05:56 UTC).

## Choices made while building (added after the exploratory reporting plan; addendum 2 item 5)

The filter's positional rule is applied on each decode's own grid (on the shifted grid a segment is late when its start,
less 15 s, falls in the last 3 s of a 30-s window); segment rates are per hour of speech of each decode; the definitions
of thanks-phrase segments (exactly "thank you"), isolated segments (5 s or more without speech on both sides), the
artefact filter (version 2) and the pause and word measures are those of the GRID item; SD units use the SD across seen
creators (those with 3 or more transcripts of record of 200 words or more after the filter) of creator means on the
transcripts of record, ddof 1. The changed share of words uses the normaliser wa-norm-v2, which was chosen after the
result (see BR-b).

## Interval level

95% percentile intervals from 2,000 resamples of the 40 recordings (one per creator, so a creator bootstrap), with a seed
of its own for each row (addendum 2 item 6). Pointwise intervals; no family-wise control. The onset densities are pooled
values without intervals. Interval levels differ between the round's packages (D18).

In the SD-unit table each row carries two intervals, as built: one in raw units and one in SD units. They come from
separately seeded resamples, so the raw interval divided by the SD can differ from the SD-unit interval in the last
printed digit. The SD-unit interval is the one of record; this README, the figure and other packages cite it.

Every value is rounded once, from the unrounded value (the builder's tables hold values already rounded to 5 decimals;
`gs_unrounded.py` replays the builder's statistics with the same seeds and checks them against those tables). Against
the release review's first tables this moved six cells of the summary table by 0.0001 (for example the share of seams
inside a word on the other grid, 72.14% rather than 72.15%) and gave more digits to some small raw changes.

## Caveats

- 40 recordings of 2 to 90 minutes, English-only recognizer model; the 10 controls bound run-to-run variation only for
  those recordings.
- The SD units use the between-creator SD of the transcripts of record, not of the re-decodes; a change of a tenth of an
  SD in one recording is not a change of a creator's mean. The table gives the mean change over the 40 recordings.
- The thanks-phrase row's change in SD units has a wide interval. Most recordings have no isolated segment on either
  grid, so that row's mean change rests on a minority of the recordings.
- In the precision check, a spoken phrase that the other decode words differently would not recur, and an inserted
  phrase tied to silence rather than to the grid would recur; the two biases pull in opposite directions.
- The analyses apply the positional rule on the 30-s grid from 0, which is the run grid.
- Recognizer output, not checked by a person.

## Code

Public tables written by `br_public.py` (SHA-256 `a03e56ab5f6ff37c3ab1cefacba8f4ad51975a9d0aa71042bf49c0dd6170da66`)
from the item's own tables and the unrounded values of `gs_unrounded.py` (SHA-256
`0c5d08b8f481014e7fb149c79ce3a33ebb5269482b720125a143f957968e4e72`); every printed row checked by `verify_br.py` (SHA-256
`592d9b7da6d4e9df228494036e5a0a48b3514fcd130679a80202986f4eb31efd`); figures drawn by `plot_br.py` (SHA-256
`47a09ba3f3dbd224e2d4a4063353b70f9d72809bf090aa058eee039e5f151433`). The first public form (`br_public.py` SHA-256
`f1dacf5a7a03b00eb5747a6d0d8805c647dda42253b1d1da271344b8eaebd7fe`, `verify_br.py` SHA-256
`514fb7a46afb8d5e1ce947156520cf70b39438fc69cfde314f45b5252062443a`) was never published.
