# New-files round: pace-variance

Exploratory; not a test of H1-H10.
New recordings of seen creators: a descriptive persistence check, not a confirmation and not a fresh-creator wave.
Rule-based and recognizer-based; not checked by a person; agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these recordings and how the creators present it.


Written 2026-11-27T06:32:30Z (UTC, from the clock) by the new-files round's computing agent (a model agent working for the lead; not a person), under the plan (published as the redacted copy `../plan.public.md`; the original was hashed at 2026-11-26T22:49:35Z and its hash is kept privately) and the lead's decision 119.

## What ran

- **Measures:** rv-R4's pace ICC and CH-H's creator-equal means and ICCs.
- **Data:** the seen creators' new recordings (the new uploads and the latest-50+ batch, each recording once). Hold-out and other-group recordings were never opened (an allow-list built from ledger rows).
- **Order:** every published value below was first reproduced, to its printed decimals, by the reused code from the latest-20+ inputs. The reproduction record was hashed before any new file was opened.
- **Who enters:** a creator enters a row with 3 or more new recordings in the measure's base. Creator sets print as bands, or not at all.
- **No split:** deposit 2's halves do not apply as a sealed check, because the new files are new recordings of the same creators. Each row runs once, with no split.

## Readings, in words

Each row's word compares the new recordings' 90% creator interval with the margin fixed in the plan before any new value was read:

- **persists:** the interval lies inside the margin of the published value;
- **shifts:** it lies wholly outside;
- **undetermined:** otherwise.

No word is a finding, a replication or a confirmation. None says anything about H1-H10.

| Reading | Rows |
|---|---|
| persists | 4 |
| undetermined | 10 |

| Row | Published | New (90% interval) | Margin | Reading |
|---|---|---|---|---|
| G2.2 CH-H: pace, creator-equal mean (words per minute of speech) | 148.5759 | 146.7277 (142.5474 to 150.908) | +/- 5.0 | undetermined |
| G2.3 CH-H: contraction rate per 1,000 words, creator-equal mean | 28.5678 | 29.9185 (26.3833 to 33.4537) | ratio 0.80 to 1.25 | persists |
| G2.3 CH-H: first-person singular per 1,000 words, creator-equal mean | 28.2734 | 27.5736 (23.8811 to 31.266) | ratio 0.80 to 1.25 | persists |
| G2.3 CH-H: first-person plural per 1,000 words, creator-equal mean | 16.9774 | 18.6603 (16.0603 to 21.2603) | ratio 0.80 to 1.25 | undetermined |
| G2.3 CH-H: second person per 1,000 words, creator-equal mean | 48.3701 | 45.4203 (41.9185 to 48.9221) | ratio 0.80 to 1.25 | persists |
| G2.3 CH-H: word length (letters), creator-equal mean | 4.3093 | 4.2876 (4.2372 to 4.338) | ratio 0.80 to 1.25 | persists |
| G2.4 CH-H: mean log words per recording | 7.7229 | 7.9084 (7.746 to 8.0708) | +/- 0.223 | undetermined |
| G2.5 CH-H: ICC (between-creator share of variance): contraction rate | 0.6157 | 0.6071 (0.4677 to 0.6992) | +/- 0.1 | undetermined |
| G2.5 CH-H: ICC (between-creator share of variance): word length | 0.581 | 0.6278 (0.4015 to 0.7714) | +/- 0.1 | undetermined |
| G2.5 CH-H: ICC (between-creator share of variance): log words | 0.4318 | 0.5142 (0.3819 to 0.6304) | +/- 0.1 | undetermined |
| G2.5 CH-H: ICC (between-creator share of variance): first-person singular | 0.2887 | 0.4026 (0.2418 to 0.5507) | +/- 0.1 | undetermined |
| G2.5 CH-H: ICC (between-creator share of variance): first-person plural | 0.3884 | 0.4522 (0.3063 to 0.5497) | +/- 0.1 | undetermined |
| G2.5 CH-H: ICC (between-creator share of variance): second person | 0.425 | 0.3864 (0.2432 to 0.513) | +/- 0.1 | undetermined |
| G2.1 rv-R4: pace ICC | 0.5779 | 0.5457 (0.4089 to 0.6568) | +/- 0.1 | undetermined |

Full rows, with each value's source file, the interval method and the creator-set band (column creators), are in `public/data-pace-variance.csv`. Figures (PNG and PDF): `public/fig-pace-variance.png`.

## Within-creator pairing

Within-creator pairs were computed privately and are not printed (decision 119.1).

## Not computed in this group

- G2.6 rv-R5 (raw ICCs of twelve recognizer and register measures): not computed in this pass (its published value was not reproduced before the new files were opened, and the round's order does not allow adding it afterwards).
- G2.7 E3 (edge against middle articulation rate; second-person address rise): not computed in this pass (its published value was not reproduced before the new files were opened, and the round's order does not allow adding it afterwards).

## Departures

- **The hashed plan served as every group's prespecification.** It was hashed at 2026-11-26T22:49:35Z, before any outcome. No separate group prespecifications were written (decision 121.6).
- **CH-H's pace ICC is not printed again.** G2.1 (rv-R4's pace ICC) carries it.
- **Secondary by-source rows** (plan 3.5) were not computed in this pass.

## Privacy

- No per-creator row or point, no quantile, no exact count of creators.
- Every withheld or not computed cell reads one label.
- Values that could narrow a banded count are not printed.
