# r3-P12: a recording-condition census, covariates only

Written by the audio agent, a model agent working for the project lead (not a person); times from `date -u`. Class a.2,
run under the lead's ruling 4 (Tier 0 and Tier 1 audio). **Exploratory; not a test of H1-H10.** Seen creators only;
voice sides are model-coded and not checked by a person. Acoustic features describe the sound of these recordings, never a
speaker's state or a source; no person listened. This census is **covariates only**: it is never printed per creator and
is never a synthetic-voice screen (the veto on P10 and its proxies holds; no studio-regular or read-like quantity is
computed per creator).

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Question (programme):** how much "speaker" variance is the channel? Each delivery measure's creator share of variance,
raw and condition-adjusted. Prespecification: `../prespec.public.md` (published redacted), section 5 (hashed at 15:27:51Z (UTC), before the pass and before any outcome; the hash is kept privately (step-1 decision 49 item i)).

## How it ran

- **Tier:** S by count (outcome-free; the 23 non-development creators). The only data-tuned part, the
  condition adjustment, is fitted on the development creators' recordings only and applied unchanged; the shares are read
  once on all eligible non-development creators (prespecification section 4).
- **Recordings:** non-development recordings in the pass with usable features and 60 s or more of own-voice clean
  interior (own-solo definition); creators with 2 or more such recordings.
- **Delivery measures** (per recording, over its own-voice clean interiors): acoustic speech rate and articulation rate
  (log), long-pause share, F0 range (semitones relative to the recording; Tier 1), intensity variability (Tier 1),
  recognizer speech rate (log) and mean recognizer word probability.
- **Condition covariates** (exogenous): speech-to-background ratio, background level, bandwidth (log rolloff), high-band
  share, digital-silence share, clipping share, reverberation proxy, source codec class and source bit rate (log).
- **Statistic:** one-way random-effects ANOVA estimator of the between-creator share of variance (truncated at 0), raw and
  on residuals of the covariate fit; creator-cluster bootstrap 90% intervals (2,000 draws; fixed in the
  prespecification; interval class not calibrated by r3-P30). A description: no reading words.

## Results (run 2026-11-26 17:58Z to 17:59Z; figure relabelled and rerun 18:02Z, same numbers; rerun 19:14Z under the lead's decision 109, same numbers)

- **Gate census.** 178 of the 224 non-development recordings in the pass pass the background gate (speech-to-background
  ratio 25 dB or more); the count of non-development creators with a gated recording is not printed (privacy rule).
- **Creator shares of variance** (15 or more of the 23 creators): raw shares run from about 0.18 (recognizer word
  probability) to about 0.62 (F0 range); acoustic speech and articulation rates about 0.45 and 0.42, long-pause share
  about 0.58, recognizer speech rate about 0.48. Intervals are wide (creator-cluster bootstrap).
- **Condition-adjusted.** Only F0 range's creator share falls with the adjustment by an interval that excludes zero
  (from about 0.62 to 0.52; difference about 0.10, interval 0.01 to 0.20). For every other measure the raw-minus-adjusted
  interval includes zero. The covariates explain about 43% of the recording-level variance of long-pause share, 34% of F0
  range and 26% of articulation rate on these recordings, and little or none of the others (a negative value means the
  development-creator fit predicts these recordings worse than their mean).
- **In words:** with the covariates measured here, most of the between-creator variance in these delivery measures is not
  explained by recording condition; F0 range is the exception, part of whose creator share goes with condition. The
  covariates are not exhaustive (microphone, room and processing are only partly visible), so "not explained by measured
  condition" is not "speaker".

### Tables

**`public/data-r3-P12-gate.csv`**

| row | value |
|---|---|
| non-development recordings in the pass with usable features | 224 |
| of them passing the background gate (SBR 25 dB or more) | 178 |
| non-development creators with a recording in the pass | all 23 |
| non-development creators with a gated recording | not printed (privacy rule) |

**`public/data-r3-P12-shares.csv`**

| measure | measure_text | creators | creator_share_raw | raw_lo90 | raw_hi90 | creator_share_adjusted | adjusted_lo90 | adjusted_hi90 | raw_minus_adjusted | diff_lo90 | diff_hi90 | covariates_r2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| speech_rate | acoustic speech rate (log nuclei per second) | 15 or more of the 23 | 0.449 | 0.297 | 0.612 | 0.514 | 0.327 | 0.666 | -0.065 | -0.173 | 0.096 | 0.038 |
| art_rate | acoustic articulation rate (log) | 15 or more of the 23 | 0.419 | 0.197 | 0.616 | 0.417 | 0.263 | 0.526 | 0.002 | -0.144 | 0.186 | 0.264 |
| long_pause_share | long-pause share | 15 or more of the 23 | 0.58 | 0.197 | 0.696 | 0.494 | 0.194 | 0.69 | 0.086 | -0.093 | 0.179 | 0.428 |
| f0_range | F0 range (semitones; Tier 1) | 15 or more of the 23 | 0.622 | 0.41 | 0.796 | 0.519 | 0.325 | 0.681 | 0.103 | 0.011 | 0.204 | 0.339 |
| int_var | intensity variability (dB; Tier 1) | 15 or more of the 23 | 0.247 | 0.072 | 0.443 | 0.266 | 0.093 | 0.446 | -0.019 | -0.092 | 0.072 | -0.017 |
| rec_rate | recognizer speech rate (log recognized syllables per second) | 15 or more of the 23 | 0.479 | 0.278 | 0.617 | 0.565 | 0.283 | 0.708 | -0.086 | -0.188 | 0.101 | -0.075 |
| rec_p | recognizer word probability (mean) | 15 or more of the 23 | 0.181 | 0.099 | 0.447 | 0.233 | 0.14 | 0.428 | -0.052 | -0.095 | 0.021 | -0.188 |


## Departures and rows not computed

- **Departure from the split policy's wording** (accepted as the lead's decision 106.1, decided 2026-11-26 18:16Z).
  Deposit 2's split policy builds a data-tuned rule on exploration half A and runs it once on sealed half B (tier S),
  or cross-fits it over the two halves (tier X). Here the only data-tuned part, the condition adjustment,
  is fitted on the tuning pool T (the development creators) only, and the shares are read once on all eligible
  non-development creators (tier S by count).
  Reason: T sits on the exploration side and is never read for a split reading, so fitting on T alone keeps both halves
  out of every fit (decision 88's reading). **Limitation: half B is no longer sealed for the acoustic measures described
  here.**
- No studio-regular row and no per-creator value are computed or printed (the veto on P10 and its proxies).

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
No number changed: values are withheld, merged, re-banded or reworded, and the figure is redrawn by this entry's code.
Changes in this entry:

- the shares rows' creator count prints as the band "15 or more of the 23" (decision 109.2);
- one creator count of the gate census reads "not printed (privacy rule)" (decision 109.2);
- the departure from the split policy's wording is printed with its reason and its limitation, as the lead accepted
  it on 2026-11-26 at 18:16Z (decisions 106.1 and 109.5);
- the privacy paragraph is reworded in general terms (decision 109.3);
- every hash in this README's file table and in `status.json` is refreshed.

## Change by the lead's decision 111

2026-11-26T19:37:45Z (UTC, from the clock). No number changed. The tier by count prints as its letter only,
and the prespecification is cited as its published, redacted copy (`../prespec.public.md`; the original stays
private and unchanged).

## Change by the lead's decision 112

2026-11-26T19:49:16Z (UTC, from the clock). No number changed. The original prespecification's hash is no longer
printed: the CSV headers (rewritten by this entry's code), `status.json` and this README cite `../prespec.public.md`,
hashed at 15:27:51Z (UTC), before the pass and before any outcome; the hash is kept privately (step-1 decision 49 item i).

## Files

| File | SHA-256 |
|---|---|
| `code/analyse_p12.py` | `757aff24491da0453845af732406c25dcefe3c08562c8299f0110c5c0477efb7` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `public/data-r3-P12-gate.csv` | `0a1e499165ab0002b28c7d7d6dbf3377086aa3b71abb705146f473395fbb9b8e` |
| `public/data-r3-P12-shares.csv` | `00ef2e07479ae01c66f52574613f66de11253f3831725c816e8f89918bc93988` |
| `public/fig-r3-P12-census.pdf` | `ef20d8f77a67cd064247ced423cf4c7977044bb6c313be416d5aad764aa11a26` |
| `public/fig-r3-P12-census.png` | `9f76366be502eaa68dccb7d6f9e7099068ceecc160b8be976d7d82cf924d33c8` |

`status.json` carries the same hashes; `contacts.md` lists every read with its time.
