# r3-P09: do voice boundaries sit on changes in delivery or production?

Written by the audio agent, a model agent working for the project lead (not a person); times from `date -u`. Class a.2,
run after r3-P08 under the lead's ruling 4 (Tier 0 and Tier 1 audio). **Exploratory; not a test of H1-H10.** Seen
creators only. Voice boundaries are model-coded and not checked by a person; the instrument shares the label's location.
Acoustic features describe the sound of these recordings, never a speaker's state or a source; no person listened.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Question (programme):** do voice boundaries sit on changes in delivery or production? Pause share alone never yields
"change in delivery"; voiced-frame features at cue-free boundaries against edges matched on position, punctuation, pause
and segment start; one permutation-maximum band per boundary type. Prespecification: `../prespec.public.md` (published redacted), sections 4 and 8
(readings A5 and A6 of the speech member's table, with deposit 2's margins).

## How it ran

- **Tier:** X by count (outcome-free; the 23 non-development creators); the F0 standardisation unit is
  fitted on the development creators; the reading is made once on all eligible non-development creators. The cue-opened
  column is not computed (tier D by count).
- **Boundaries:** cue-free (no RX cue within 2 units), seam-free (not within 2 s of a 30-s seam), 60 s of span on each
  side, in recordings passing the background gate; boundaries with a detected environment change (r4-P03's rule) or a
  music-like share of 0.5 or more within 5 s leave the rows. Entries and exits apart.
- **Features:** voiced-frame primaries: articulation rate (log) and F0 range (in units of the between-creator SD of
  own-voice F0 range); pause-tied: long-pause share (a shared channel).
- **Estimand:** the sustained shift (10 to 60 s after minus 60 to 10 s before), per creator minus the mean shift of its
  matched non-boundary edges; 90% t interval on creator means, fixed (interval class not calibrated by r3-P30). The 30-s
  window row (5 to 30 s) is secondary.
- **Band:** feature curves in 10-s windows from -60 to +60 s; 200 null draws of local shifts within the same tenth of the
  same recording; each cell standardised by its null SD; one permutation-maximum band (90%) per boundary kind over
  features and windows.
- **Readings:** O1 when a voiced-frame feature's interval lies beyond its margin and its curve leaves the band; O2 when
  every voiced feature's interval lies inside its margin, no cell leaves the band, and battery criterion 5's power is 0.8
  or more; otherwise O3 (undetermined). A8 caps every reading at undetermined below 12 eligible creators
  (and then, under the lead's decision 109.1, no estimate, interval or reading is printed).

## Results (run 2026-11-26 18:01Z; rerun 18:05Z after r4-P03's floor rule; rerun 19:13Z under the lead's decision 109)

**Not measurable acoustically in this corpus (fewer than 12 eligible creators after the background gate: A8).** Under the
lead's decision 109.1 (a rule that does not depend on the data), every estimate, interval and reading row prints
"not printed (A8: fewer than 12 eligible creators after the background gate)", and the figure is not published.

- **Battery:** criterion 4 met (the sustained-shift interval rejects at about 6% of null sets at development own-voice
  edges); criterion 5 met (power about 0.80 at the margin under the floor rule, at the real creator count).
- **Decision 106.2:** A8 blocks this entry, which stays without a reading in this round. Running it with the tuning pool T
  added would be a new registration; it is on the fourth panel's agenda (the stored per-recording features make it
  cheap).

### Tables

**`public/data-r3-P09-boundaries.csv`**

| kind | feature | feature_text | creators | contrast | lo90 | hi90 | margin | words | leaves_band | shift_raw | shift_5_30 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| entry | art | articulation rate (log; voiced-frame) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.223 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  |
| entry | f0 | F0 range (SD units; voiced-frame; Tier 1) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.2 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  |
| entry | lps | long-pause share (pause-tied; shared channel) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.05 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  |
| exit | art | articulation rate (log; voiced-frame) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.223 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  |
| exit | f0 | F0 range (SD units; voiced-frame; Tier 1) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.2 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  |
| exit | lps | long-pause share (pause-tied; shared channel) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.05 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  |

**`public/data-r3-P09-reading.csv`**

| kind | creators | band_or_value | reading |
|---|---|---|---|
| entry | not printed (A8: fewer than 12 eligible creators after the background gate) |  | not printed (A8: fewer than 12 eligible creators after the background gate) |
| exit | not printed (A8: fewer than 12 eligible creators after the background gate) |  | not printed (A8: fewer than 12 eligible creators after the background gate) |
| A8 (12 or more eligible creators after the gate) |  |  | not measurable acoustically in this corpus (fewer than 12 eligible creators after the background gate: A8) |
| battery criterion 4 (null specificity; rejection rate of the sustained-shift interval at development own-voice edges) |  | 0.06 | met |
| battery criterion 5 (power at the margin, floor rule, at the real creator count) |  | 0.8 | met |
| A6 production: boundaries with a detected environment change minus matched edges (r4-P03) |  |  | not printed (A8: fewer than 12 eligible creators after the background gate) |


## Departures and rows not computed

- **Departure from the split policy's wording** (accepted as the lead's decision 106.1, decided 2026-11-26 18:16Z).
  Deposit 2's split policy builds a data-tuned rule on exploration half A and runs it once on sealed half B (tier S),
  or cross-fits it over the two halves (tier X). Here the F0 standardisation unit is fitted on the tuning pool
  T (the development creators) only, and the entry runs once on all eligible non-development creators (tier X by
  count).
  Reason: T sits on the exploration side and is never read for a split reading, so fitting on T alone keeps both halves
  out of every fit (decision 88's reading). **Limitation: half B is no longer sealed for the acoustic measures described
  here.**
- The cue-opened column: not computed (tier D by count).
- Criterion 4 is run on the sustained-shift interval at development own-voice edges rather than through the full band
  pipeline, and criterion 5 plants the margin at the feature level rather than in audio (both stated in
  `../common/code/bshared.py`).

## Privacy

No cell, bin or plotted group rests on fewer than 5 creators; no row or point is per creator or per recording; no audio,
waveform or spectrogram of any recording; no absolute pitch; no names, ids, titles or quotations. Creator counts print as
"all 23", as bands, or not at all; values that could narrow a banded count are not printed. A cell or count withheld under
the privacy rule reads "not printed (privacy rule)", whatever the reason; in the stacked class shares such a class is
counted in "other sound, unclassified". Every interval method is fixed in the prespecification, so decision 62 does not
apply to banded rows. The privacy checks are listed in `../common/README.md`.

Multiplicity: 56 primaries in the programme; if every true effect sat at half its margin, about 2.8 readings beyond the
margin would be expected by chance. A reading is never a finding.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Change by the lead's decision 109

2026-11-26T19:28:21Z (UTC, from the clock), after the independent privacy check of the seven audio entries.
No number changed: values are withheld, merged, re-banded or reworded.
Changes in this entry:

- under A8, every estimate, interval and reading row reads "not printed (A8: fewer than 12 eligible creators after
  the background gate)", and the figure is not published (decision 109.1);
- the departure from the split policy's wording is printed with its reason and its limitation, as the lead accepted
  it on 2026-11-26 at 18:16Z (decisions 106.1 and 109.5);
- the privacy paragraph is reworded in general terms (decision 109.3);
- every hash in this README's file table and in `status.json` is refreshed.

## Change by the lead's decision 111

2026-11-26T19:37:45Z (UTC, from the clock). No number changed. The tier by count prints as its letter only,
and the prespecification is cited as its published, redacted copy (`../prespec.public.md`; the original stays
private and unchanged). The cue-opened column's count prints as its tier letter, D.

## Change by the lead's decision 112

2026-11-26T19:49:16Z (UTC, from the clock). No number changed. The original prespecification's hash is no longer
printed: the CSV headers (rewritten by this entry's code), `status.json` and this README cite `../prespec.public.md`,
hashed at 15:27:51Z (UTC), before the pass and before any outcome; the hash is kept privately (step-1 decision 49 item i).

## Files

| File | SHA-256 |
|---|---|
| `code/analyse_p09.py` | `d50374c2338c2640bed59510cbab1dc7bcfca19034308d551dc0ec0661c65535` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `public/data-r3-P09-boundaries.csv` | `5b6222af852717c7c1a63e03840c61d52350961b48958701c54cb1fa43a51a46` |
| `public/data-r3-P09-reading.csv` | `3c12d8ceb20723c0c6ffa25e5ac9fcefd66b57060ce09bb78665463d6f9aa311` |

`status.json` carries the same hashes; `contacts.md` lists every read with its time.
