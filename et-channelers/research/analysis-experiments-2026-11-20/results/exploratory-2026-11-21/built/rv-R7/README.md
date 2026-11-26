# rv-R7: where do the recognizer's inserted phrases and seams sit, and how good are the rules that remove them?

Exploratory (registry A2); not a test of H1-H10. Paper-review build item (built 2026-11-21 on seen creators; label
"Exploratory, paper review (registry A2/A7); not a test of H1-H10"), released in the public form of plan section 3 by
the release review (plan P10, 2026-11-22). It replaces the earlier draft's Table 8 and its abstract's 55%. No audio was
played: a phrase "appears to be inserted" by the recognizer; no rule has been confirmed by listening.

## What it asks

Where in the 30-s decoding window do the recognizer's segments start and the stand-alone two-word thanks phrase appear,
by the window's speech status; how many transcripts and creators carry it; how often each filter rule removes something;
and how far phase counts bound the precision of those rules?

## Base

1,284 English transcripts (English-only model) of the 71 seen creators; 65,102 full 30-s windows (the last, partial
window of a recording is left out). Speech status of a window: its coverage by recognizer segments other than
stand-alone thanks segments (0.5 or more: full of speech; above 0 and below 0.5: partial; 0: none).

## What is shown

| File | What it holds | Place |
|---|---|---|
| `public/rv-r7-artefact-rules.csv` | The rule table: removals by rule, per 1,000 windows, share of transcripts, creators, rate per speech hour, precision bound | M |
| `public/rv-r7-abstract-sentence.csv` | The abstract sentence (the build's plain-text copy is not part of a release, D56) | M |
| `public/rv-r7-thanks-by-phase.csv` | Figure panel (b): chance of the thanks phrase per 3-s stretch by speech status (merged cells, see below) | M |
| `public/rv-r7-segment-start-phase.csv` | Figure panel (a): segment starts by second of the window | M |
| `public/rv-r7-onset-density.csv` | Figure panels (c, d): word onsets and word probability by 0.25-s phase | M |
| `public/rv-r7-prevalence-and-seams.csv` | Prevalence, rate per speech hour, precision bound, seam measures | M, W |

Figures (in the gallery, with their records in its `manifest.json`): rv-R7-a seam anatomy (M), rv-R7-b artefact card
(W).

Main readings:

- A two-word thanks phrase starts 27 to 30 s into a window in 49.9% of English transcripts (90% creator bootstrap 45.2
  to 54.5%), in all but fewer than 5 of the 71 seen creators; the positional rule removes 1,422 such segments, 2.95 per
  speech hour (2.73 to 3.19); its precision, bounded by phase counts, is not published (misses not recounted by creator)
  (lead's decision D58, 2026-11-26).
- In windows full of speech the phrase starts in the last 3 s of 2.3% of windows (2.2 to 2.5%), 50 to 150 times as
  often as in any earlier 3-s stretch. In windows without other speech it starts only in the first 9 s and never in the
  last 3 s.
- 16.8% of recognizer segments start in second 0 of a window (uniform 3.3%); word onsets are 1.96 times each creator's
  flat level in the first 0.25 s and 0.59 in the last; mean word probability is 0.84 in the first and 0.78 in the last
  0.25 s, against about 0.97 to 0.98 mid-window (between 3 and 27 s; corrected in the fix pass of 2026-11-22: the
  release had printed about 0.96).
- Within recognizer segments 90.5% of word gaps are exactly zero, and 38.7% of pauses of 0.3 s or more fall at segment
  boundaries.
- The per-transcript share depends on weighting (0.41 to 0.71 across rv-R4's specifications), so the rate per window or
  per speech hour is the more stable statement.

## What is withheld, and why

- **Per-bin cells of the thanks phrase in partial and empty windows.** The build printed one chance per 3-s bin and
  status. In windows full of speech every bin rests on 8 or more creators with a non-zero count and is printed as built.
  In partly covered windows and in windows without other speech most bins rest on 1 to 4 creators. Those bins are
  merged by plan section 3's rule (a bin joins the non-empty neighbour that holds fewer creators, the inner one on a
  tie): partial windows give 0-9 s, 9-15 s, 15-27 s and 27-30 s; windows without other speech give 0-9 s, and every
  later 3-s stretch is 0 for every creator (printed as 0, addendum 2 item 9). A merged cell gives the mean chance per
  3-s stretch, with the build's creator bootstrap (the release review reproduced every build cell exactly before
  merging). Every printed non-zero cell rests on 5 or more creators. No per-bin bound for seconds 3 to 27 of empty or
  partial windows is printed; the build's caption count of the cases in the first 3 s of empty windows is not published
  (its complement rests on fewer than 5 creators).
- **Counts of creators within 1 to 4 of the 71** (creators with the phrase; creators contributing removals; creators in
  the onset panels): printed as "all but fewer than 5 of the 71 seen creators". The abstract sentence is changed to that
  form.
- **Leave-one-creator-out range ends**: not printed (an end gives one creator's influence); only whether every omission
  keeps the estimate inside its 90% interval (yes for every printed cell).
- **Pairs check of the positional removals** (fix pass, 2026-11-22): the rule table's 1,422 positional removals exceed
  the sum of the 27-30 s window hits of the phase table (1,417; a window counts once per 3-s stretch, full windows only)
  by 5: removals in a recording's last, partial window, or a second removal in the same window and stretch. That
  difference rests on 5 or more creators (checked on the seen word cache with `r7_pairs_check.py`), so both counts are
  printed; how the 5 split between the two sources is not printed.

## Interval level

90% creator bootstrap (2,000 draws) throughout; 90% t over creators for creator-equal shares and rates; 95% lower bounds
for the precision bound from phase counts.

## Caveats

- Precision bounds come from phase counts (GRID: the flat level of the other 3-s bins), not from listening; the bounds of
  the rules other than the positional rule are weak.
- E1 (package ER) cites this output without any per-bin bound; its own windows use a different definition.
- A statement about this pipeline's fixed windows and this recognizer, not about the recognizer family.
- Exploratory; not a test of H1-H10.
