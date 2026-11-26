# rv-R3: what do the two recognizer models agree on, and for which uses?

Exploratory (registry A2); not a test of H1-H10. Paper-review build item (built 2026-11-21; label "Exploratory, paper
review (registry A2/A7); not a test of H1-H10"), released in the public form of plan section 3 by the release review
(plan P10, 2026-11-22). Neither transcript is a reference made by a person: everything here is agreement of two
machines, not an error rate.

## What it asks

On the same English audio, how far apart are the English-only model of the run and the larger multilingual model, for
17 measures, on the registered margin of +/-0.2 between-creator SD, and also in within-creator SD units; how large are
single-recording differences (Bland-Altman); which word classes disagree most?

## Base

- The 36 registered bridge recordings of 5 to 60 minutes, one per creator: 35 seen creators and one other-group
  creator, as registered and published (results/br-bridge.json). Every printed 36-recording number follows from the
  published summary (mean difference, SD of the differences, 36 recordings, registered between-creator SD; checked in
  the fix pass of 2026-11-22). The build's results that rest on recording-level values of all 36 recordings are held
  (see below).
- The class-disagreement, confusion-profile and MATTR/log-probability rows use the 35 seen recordings only.
- The within-creator SD: seen creators with 3 or more English-only recordings of 200 or more tokens (all but fewer than
  5 of the 71 seen creators; 1,112 recordings).

## What is shown

| File | What it holds | Place |
|---|---|---|
| `public/rv-r3-bridge-verdicts.csv` | The verdict table: per measure, both scales, per-measure and simultaneous intervals, limits of agreement (the single-omission and signed-rank columns are held) | M |
| `public/rv-r3-interval-plot.csv` | The interval plot's numbers | M |
| `public/rv-r3-verdict-tallies.csv` | Counts of measures by verdict (the bridge card) | M, W |
| `public/rv-r3-bland-altman.csv` | The published all-recording Bland-Altman summaries (mean difference, SD, normal limits) for pace, first-person singular and filled pauses; bins and percentiles held | S |
| `public/rv-r3-class-disagreement.csv` | Disagreement by word class | S |
| `public/rv-r3-confusion-profile.csv` | Edit profile by word class (used by rv-R6) | S |
| `public/rv-r3-mattr-logprob.csv` | MATTR and mean log word probability under both models | S |
| `public/rv-r3-seen-sds.csv` | Between- and within-creator SDs of the bridge measures | S |

Figures (in the gallery, with their records in its `manifest.json`): rv-R3-a interval plot (M), rv-R3-c class
disagreement (S), rv-R3-d bridge card (W). rv-R3-b (Bland-Altman panels, S) is held (lead's decision D42; below).

Main readings:

- On the registered scale 7 measures agree, 6 differ and 4 are not settled, with per-measure and with simultaneous
  intervals alike. Pace, pronoun and contraction rates, word length and vocabulary variety agree; word timing, pauses,
  segment length and filled pauses differ. In within-creator SD units: 8 / 6 / 3 (per measure) and 7 / 5 / 5
  (simultaneous).
- Pace: mean difference -0.36 words per speech minute, SD of the differences 4.15, normal limits of agreement -8.5 to
  +7.8 (the published summary). Filled pauses: many English-only transcripts hold none and the differences pile up at
  zero, so no normal limits are drawn.
- Capitalised words disagree 6.6 times as often as words in general (90% 5.0 to 8.4), filled pauses 15 times, numerals
  and first-person singular about 1.5 times; 30% of numeral disagreements are digit-against-word format.
- MATTR agrees between the models; mean log word probability is not settled (a recognizer measure).

## What is withheld, and why

- **Rows and tallies on the 35 seen recordings where a 36-recording version is published** (means, intervals and
  verdicts of the 17 measures; the variety row of the MATTR table; the median and quartiles of the overall word
  disagreement): not published. Beside the published 36-recording rows they would give the one other-group recording's
  values by difference (pairs rule, addendum 2 item 9).
- **Rows without the outlying recording** (verdicts, tallies, limits of agreement, pooled class disagreement) and the
  **leave-one-out ranges**: not published. Each would give one recording's values by difference.
- **The outlying recording's own word disagreement**, which the build printed to name it: not published (a
  single-recording value).
- **Held (lead's decision D42, 2026-11-22)**: the Bland-Altman bins by the mean of the two models with
  their medians and quartiles, the percentiles over the 36 differences, the recordings by size of difference, the count
  outside the normal limits, GRID's 90% intervals of the limits, the single-omission stability flags, the signed-rank
  verdicts with their counts of zero differences, and figure rv-R3-b. The build computed them from recording-level
  values of all 36 bridge recordings, the other-group creator's recording included, while plan row rv-R3 limits this
  output to the 35 seen recordings and published numbers for the other one. Reason: rests on a per-recording table that includes another group's recording;
  the bridge's published summary stands. The count of first-person pairs under 2 per 1,000
  words is not printed (its misses come from fewer than 5 creators, D21).
- **The count of creators behind the within-creator SD** is printed against the 71 seen creators, as the published
  bridge summary prints it.

Every class's disagreement and agreement come from 5 or more creators (checked in the release review on the build's
seen-recording counts, counts only).

## Interval level

90% per measure (t) and 90% simultaneous (Bonferroni over 17) for the verdicts; the Bland-Altman summaries carry no
interval (the published mean, SD and normal limits); 90% pair bootstrap (2,000 draws) for the class rows.

## Caveats

- The 36-recording rows include the one other-group creator, as the registered and published bridge does; they are
  printed only where they follow from the published summary. Plan section 5 rule 5 keeps other-group creators apart in
  outputs made after freeze 2; the held parts are the ones that would mix that creator's recording-level values with
  seen creators' (see the status entry).
- The verdicts say that the two models agree on average on English audio of 5 to 60 minutes; they say nothing about
  single recordings or other languages.
- Class disagreement counts insertions, so it can exceed 1 and is not a proportion.
- Exploratory; not a test of H1-H10.
