# rv-R4: do the headlines survive other weightings and windows?

Exploratory (registry A2); not a test of H1-H10. Paper-review build item (built 2026-11-21 on seen creators; label
"Exploratory, paper review (registry A2/A7); not a test of H1-H10"), released in the public form of plan section 3 by
the release review (plan P10, 2026-11-22).

## What it asks

Do the paper's headline numbers (pace median and ICC, share of time without speech, speech coverage of the last 15 s,
the share of transcripts with a thanks phrase at a window end, five term-cue shares) change their sentence under other
weightings (creator-equal, recording-equal, hour-pooled, precision-weighted, inverse-span), windows (each creator's own
newest 120 days; 1 August to 19 November 2026), a 5-minute length floor, posting-rate thirds, or the span of a creator's
newest 20 recordings? The margin for "changes the sentence" was fixed before the run.

## Base

Seen creators only (71), closed run. Restricted windows keep fewer creators; their counts are printed as 60 (the
calendar window), against a printed count ("all but fewer than 5 of 71", "all but fewer than 5 of 60") or not printed,
so that no two nested printed counts differ by 1 to 4. Posting-rate thirds: 24, 23 and 24 creators.

## What is shown

| File | What it holds | Place |
|---|---|---|
| `public/rv-r4-summary.csv` | Per headline: baseline, margin, range over specifications, specifications beyond the margin, and one sentence for the main text | S; M (sentences) |
| `public/rv-r4-specifications.csv` | Every specification of every headline (dot plot and specification curves) | S |
| `public/rv-r4-span-bins.csv` | Creator means in seven bins of channel span | S |
| `public/rv-r4-span-loess.csv` | LOESS of creator means on log span | S |
| `public/rv-r4-posting-rate.csv` | Log posting rate as a covariate | S |

Figures (in the gallery, with their records in its `manifest.json`): rv-R4-a headline sensitivity, rv-R4-b
specification curves, rv-R4-c span bins (all S).

Main readings (40 specifications per headline; pace ICC 6):

- Pace median: 2 beyond the margin of 5 words per minute, both hour-pooled, none with an interval wholly outside the
  band. Pace ICC: 1 of 6 (each creator's own newest 120 days).
- Share of time without speech: 3 beyond the margin, none with an interval outside the band.
- Speech coverage of the last 15 s: 9 beyond the margin, none outside the band.
- Thanks phrase at a window end (baseline 0.49): 20 beyond the margin, 8 with an interval outside the band; it rises to
  about 0.70 when recordings are weighted by hours, because a longer recording has more windows in which to hold one.
- Term-cue shares (cue counts of fixed word lists): 6 to 19 beyond the margin, 5 to 7 of them hour-pooled.
- Counted on the public table, 44 of the 98 specifications beyond a margin are hour-pooled. Of the 76 curve
  specifications beyond a margin, 38 are hour-pooled and 31 of the other 38 carry the 5-minute floor; in the dot plot,
  14 of the 22 are posting-rate thirds. Correction: the build's caption said 'nearly all of them hour-pooled'.
- Log posting rate explains at most 3.4% of the between-creator variance of any headline; adjusting the pace ICC for it
  changes 0.578 to 0.581. Across seven bins of channel span the creator means move within wide intervals; speech
  coverage of the last 15 s is highest where the newest 20 recordings span under 52 days.

## What is withheld, and why

- **Exact creator counts of restricted windows** (own newest 120 days, the 5-minute floor): printed as bands against a
  printed count or not printed (nested counts 1 to 4 apart). The estimates themselves are printed: the release review
  checked that every pair of printed specifications differs in 5 or more creators (the 5-minute floor touches 19 or more
  creators in every window and headline set; counts only).
- **The outer values of channel span** that the build's caption printed (its minimum and maximum): not published (they
  bound single creators). Only rounded inner bin edges are printed and the end bins are open. The LOESS is printed only
  at the build's grid points between the 10th and 90th percentiles of the creators' log span, with the log span rounded
  to 2 decimals (fix pass, 2026-11-22: the build drew it from the 5th to the 95th percentile, whose ends sit between the
  4th and 5th most extreme creators; plan section 3 uses the 10th and 90th).

## Interval level

90% creator bootstrap (2,000 draws; 500 for the ICC) for every specification; 90% t intervals over the 10 or 11
creators of a span bin; 90% creator bootstrap (500) for the LOESS band and the covariate slopes.

## Caveats

- In this roster, under the newest-20 quota; no period or trend is described.
- Term cues are cue counts (fixed word lists, precision not gated).
- Exploratory; not a test of H1-H10.
