# rv-R6: how much recognition error can each word-based measure tolerate?

Exploratory (registry A2); not a test of H1-H10. Paper-review build item (built 2026-11-21 on seen creators; label
"Exploratory, paper review (registry A2/A7); not a test of H1-H10"), released in the public form of plan section 3 by
the release review (plan P10, 2026-11-22). Everything here is a tolerance under simulated error, not a measured error
rate: the recognizer's real error rate is unknown until a reference made by a person exists.

## What it asks

If the recognizer's words were wrong at a given rate, how far would each word-based measure move: the cohort mean, the
median and the 90th-percentile creator, the ICC, the creators' order, and a measure's correlation with silence? Two
designs: the same error rate for every creator (0 to 20%), and error rates that differ between creators.

## Base

71 seen creators, 1,176 recordings (English-only model, 300 or more words, filter v2). The injected errors follow the
edit profile of the bridge (35 seen recordings: substitution, deletion and insertion shares, chances by word class, the
words substituted and inserted; see rv-R3's confusion profile) or a uniform profile that keeps each recording's own word
distribution.

## What is shown

| File | What it holds | Place |
|---|---|---|
| `public/rv-r6-tolerance.csv` | The tolerance table: the error rate at which the cohort mean, the median and the 90th-percentile creator move 0.2 between-creator SD | S |
| `public/rv-r6-injection-curves.csv` | The tolerance curves' numbers | M |
| `public/rv-r6-creator-error.csv` | Per-creator error scenarios (ICC change, creator order, correlation with silence share) | S |

Figures (in the gallery, with their records in its `manifest.json`): rv-R6-a tolerance curves (M), rv-R6-b
per-creator error (S).

Main readings:

- The same error for every creator, bridge profile: word length and MATTR-1000 move the cohort mean by 0.2
  between-creator SD at about 4 to 5% and filled pauses at about 5% (1% for the most affected creators); pronoun,
  contraction and question-mark rates stay within 0.2 SD up to 20% (largest: second person -0.14 SD). Under the uniform
  profile no cohort mean reaches 0.2 SD.
- Error that differs between creators (median 3.5%): pronoun, contraction, question-mark and numeral rates, pace and log
  words keep their between-creator structure (ICC change at most 0.03, Spearman with the clean creator means 0.99 or
  more). Word length and MATTR-1000 keep their ICC but their creator order moves, and error that rises with the share of
  time without speech changes their correlation with that share by -0.16 and +0.18: error of this kind can create an
  association that is not in the speech. Filled pauses keep their creator order only in part (Spearman with the clean
  creator means 0.71 to 0.84 across the six scenarios at a 3.5% median): they are fragile under any of these scenarios.

## What is withheld, and why

Nothing is withheld: every printed figure is a cohort mean, a percentile over creators or a simulation summary. The
build's tolerance wording is reworded to "a tolerance, not a measured error rate" (D11's wording rule).

## Interval level

No confidence intervals: the curves are means of 2 replicate injections; the per-creator scenarios are means over 10
draws of creator rates, with their Monte Carlo spread (5th and 95th percentiles over the draws) in the table.

## Caveats

- The bridge's model-to-model disagreement (quartiles 2.7 to 4.8%, from the published bridge summary) is drawn as a
  guide; it is not an error rate.
- ICCs here are one-way REML on the raw scale and are not comparable with the latent-scale ICCs of rv-R5's VP-1.
- Exploratory; not a test of H1-H10.
