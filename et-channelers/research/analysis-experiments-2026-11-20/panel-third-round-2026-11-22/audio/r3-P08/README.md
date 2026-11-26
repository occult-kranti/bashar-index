# r3-P08: an acoustic instrument on label-located spans

Written by the audio agent, a model agent working for the project lead (not a person); times from `date -u`. Class a.2,
run under the lead's ruling 4 (Tier 0 and Tier 1 audio). **Exploratory; not a test of H1-H10.** Seen creators only.
Voice labels are model-coded (the small model) and not checked by a person; comparisons between instruments are
agreement, never accuracy. Acoustic features describe the sound of these recordings (delivery and recording conditions),
never a speaker's state or a source; recovery was checked on constructed audio only (an upper bound); no person listened.
The instrument is independent of the transcript in measurement, not in location: every span comes from the label.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Question (programme):** "one contrast, five instruments": the claimed-over-own rate ratio under the run recognizer, the
larger recognizer, the shifted grid, the acoustic nucleus rate and recognized syllables per nucleus. Meas's battery
criteria are binding. Prespecification: `../prespec.public.md` (published redacted), sections 3, 4 and 6; the acoustic reading table A1 to A8 (the
speech member's round-3 memo) supplies the rows, with deposit 2's margins.

## How it ran

- **Tier:** X by count (outcome-free; the 23 non-development creators); no part tuned on either half
  (the F0 and intensity standardisation unit is fitted on the development creators), so the reading is made once on all
  eligible non-development creators.
- **Spans:** clean interiors (10 s dropped inside each span end) under the primary voice definition, excluded formats out,
  in recordings passing the background gate (speech-to-background ratio 25 dB or more); pooled by side per creator;
  eligible with 60 s or more on each side. Units coded as another participant are never processed.
- **Instruments:** I1 the run recognizer (recognized syllables per second of interior time); I2 the larger recognizer
  (rv-R3's bridge decode, only on its recordings); I3 the shifted grid (BR-GS's re-decode, only on its recordings); I4 the
  acoustic nucleus speech rate (primary, A1); I5 recognized syllables per nucleus (A4, deletion).
- **Rows besides:** articulation rate, long-pause share (A2; a shared channel, never counted as convergence), F0 range
  (A3; two-sided; Tier 1), intensity variability (Tier 1), a same-recording row, and the negative control (own voice in the
  first minute against own-voice interiors after it).
- **Statistics:** 90% t interval on creator means, fixed in the prespecification (interval class not calibrated by
  r3-P30); margins from deposit 2 (log 0.223; 0.05; 0.20 SD). The primary reads "beyond the margin" only with I1 in the
  same direction, the negative control and I5 within the margin, A8 and battery criterion 3; it reads "within the margin
  (B)" only with battery criteria 1 (slope) and 3 and A8.

## Results (run 2026-11-26 17:59Z to 18:00Z; the battery caps of prespecification section 3 were applied to the secondary rows in a rerun at 18:00:30Z, an implementation correction with no change of design)

- **A8:** 12 or more eligible non-development creators after the background gate: met.
- **Primary (I4, acoustic nucleus speech rate):** claimed over own log ratio about -0.002 (90% interval -0.063 to 0.059),
  inside deposit 2's margin (0.223), but the reading is **undetermined (battery criterion 1 (rate slope) not met)**: on
  constructed audio the nucleus rate recovers time-stretch changes with a slope of about 0.45, so a "within the margin"
  reading is not licensed.
- **I1, the run recognizer:** about -0.045 (-0.121 to 0.031): **within the margin (B)** (agreement between voices on the
  recognizer's rate, never accuracy).
- **I2 (larger recognizer) and I3 (shifted grid):** not computed (too few terms or creators): fewer than 5 non-development
  creators hold a bridge or grid-shift recording with 60 s of each voice.
- **I5, recognized syllables per nucleus (A4):** about -0.043 (-0.098 to 0.011): undetermined (battery criterion 1 not
  met).
- **Rows:** articulation rate about +0.016, same-recording row about +0.013 and negative control about +0.042, each
  undetermined (battery criterion 1 not met); long-pause share +0.009 (-0.034 to 0.053) undetermined; F0 range +0.10 SD
  (-0.46 to 0.65) undetermined; intensity variability +0.38 SD (-0.26 to 1.01) undetermined.
- **In words:** neither the recognizer nor the acoustic instrument shows a claimed-over-own rate difference beyond the
  deposited margin; the recognizer's contrast lies within it; the acoustic contrast cannot be read as "within" because
  the instrument compresses rate changes. No pitch or intensity row is readable.
- **Battery (meas's criteria; `public/data-r3-P08-battery.csv`):** criterion 1 met for inserted-pause detection (all
  of 300 ms or more found), octave errors (about 0.6% of voiced frames) and pitch shifts (errors about 0.02 and 0.05
  semitones), not met for pause edges (median 25 ms against 20 ms), rate error at the extreme stretches and the rate
  slope (about 0.45); criterion 2 not met (reverberation biases rate by about +0.07 log); criterion 3 met for rate (bias
  under 0.074 log) and not met for pitch range (reverberation lowers it by about 0.6 semitones); criterion 6 in
  `../r4-P03/`; criterion 7: every measure reaches split-half reliability 0.7 by 60 s except F0 range (120 s); criteria 4
  and 5 met (`../r3-P09/`).

### Tables

**`public/data-r3-P08-battery.csv`**

| criterion | check | value | pass_rule | result |
|---|---|---|---|---|
| 1 absolute recovery | inserted pauses of 300 ms or more detected (median over excerpts) | 1.0 | 0.95 or more | met |
| 1 absolute recovery | median edge error of detected inserted pauses (s) | 0.025 | 0.020 or less | not met |
| 1 absolute recovery | speech-rate error under time stretch 0.85 (absolute %, median) | 4.39 | 3 or less | not met |
| 1 absolute recovery | speech-rate error under time stretch 0.9 (absolute %, median) | 2.51 | 3 or less | met |
| 1 absolute recovery | speech-rate error under time stretch 0.95 (absolute %, median) | 2.05 | 3 or less | met |
| 1 absolute recovery | speech-rate error under time stretch 1.05 (absolute %, median) | 2.84 | 3 or less | met |
| 1 absolute recovery | speech-rate error under time stretch 1.1 (absolute %, median) | 4.76 | 3 or less | not met |
| 1 absolute recovery | speech-rate error under time stretch 1.15 (absolute %, median) | 10.21 | 3 or less | not met |
| 1 absolute recovery | rate recovery slope (median) | 0.453 | 0.9 to 1.1 | not met |
| 1 absolute recovery | octave-guard share of voiced frames (median) | 0.0057 | under 0.02 | met |
| 1 absolute recovery | median pitch shift error (semitones) | 0.018 | 0.5 or less | met |
| 1 absolute recovery | F0 range of shifted copies, absolute difference (semitones) | 0.053 | 0.5 or less | met |
| 2 and 3 by stratum | quieter_12db: median bias of speech_rate (log; inside the gate) | 0.0 |  |  |
| 2 and 3 by stratum | quieter_12db: median bias of art_rate (log; inside the gate) | 0.0 |  |  |
| 2 and 3 by stratum | quieter_12db: median bias of f0_range (semitones; inside the gate) | 0.0 |  |  |
| 2 and 3 by stratum | reverb_rt06: median bias of speech_rate (log; inside the gate) | 0.071 |  |  |
| 2 and 3 by stratum | reverb_rt06: median bias of art_rate (log; inside the gate) | 0.059 |  |  |
| 2 and 3 by stratum | reverb_rt06: median bias of f0_range (semitones; inside the gate) | -0.606 |  |  |
| 2 and 3 by stratum | noise_sbr20: median bias of speech_rate (log; removed by the gate) | -0.05 |  |  |
| 2 and 3 by stratum | noise_sbr20: median bias of art_rate (log; removed by the gate) | -0.056 |  |  |
| 2 and 3 by stratum | noise_sbr20: median bias of f0_range (semitones; removed by the gate) | -0.109 |  |  |
| 2 and 3 by stratum | noise_sbr15: median bias of speech_rate (log; removed by the gate) | -0.14 |  |  |
| 2 and 3 by stratum | noise_sbr15: median bias of art_rate (log; removed by the gate) | -0.136 |  |  |
| 2 and 3 by stratum | noise_sbr15: median bias of f0_range (semitones; removed by the gate) | -0.171 |  |  |
| 2 and 3 by stratum | bed_minus15: median bias of speech_rate (log; removed by the gate) | -0.184 |  |  |
| 2 and 3 by stratum | bed_minus15: median bias of art_rate (log; removed by the gate) | -0.141 |  |  |
| 2 and 3 by stratum | bed_minus15: median bias of f0_range (semitones; removed by the gate) | -0.094 |  |  |
| 2 robustness | speech rate within 3% in the strata the gate admits |  |  | not met |
| 3 differential recovery | rate bias under the admitted strata under a third of the margin (log 0.074) |  |  | met |
| 3 differential recovery | F0-range bias under the admitted strata under a third of 0.20 SD |  |  | not met |
| 6 splice classes | AUC, same-session cut against unedited points | 0.463 | 0.8 or more | not met |
| 6 splice classes | AUC, session join against unedited points | 0.908 | 0.8 or more | met |
| 6 splice classes | AUC, gain step against unedited points | 0.494 | 0.8 or more | not met |
| 6 splice classes | AUC, music-bed onset against unedited points | 0.957 | 0.8 or more | met |
| 6 splice classes | AUC, spectral change without an edit against unedited points | 0.991 | 0.8 or more | met |
| 7 reliability | speech_rate: split-half (Spearman-Brown) at 60 s | 0.836 | 0.7 |  |
| 7 reliability | speech_rate: split-half (Spearman-Brown) at 120 s | 0.934 | 0.7 |  |
| 7 reliability | speech_rate: split-half (Spearman-Brown) at 240 s | 0.966 | 0.7 |  |
| 7 reliability | speech_rate: split-half (Spearman-Brown) at 480 s | 0.974 | 0.7 |  |
| 7 reliability | speech_rate: minimum span (s) | 60 |  |  |
| 7 reliability | art_rate: split-half (Spearman-Brown) at 60 s | 0.862 | 0.7 |  |
| 7 reliability | art_rate: split-half (Spearman-Brown) at 120 s | 0.931 | 0.7 |  |
| 7 reliability | art_rate: split-half (Spearman-Brown) at 240 s | 0.965 | 0.7 |  |
| 7 reliability | art_rate: split-half (Spearman-Brown) at 480 s | 0.977 | 0.7 |  |
| 7 reliability | art_rate: minimum span (s) | 60 |  |  |
| 7 reliability | long_pause_share: split-half (Spearman-Brown) at 60 s | 0.876 | 0.7 |  |
| 7 reliability | long_pause_share: split-half (Spearman-Brown) at 120 s | 0.948 | 0.7 |  |
| 7 reliability | long_pause_share: split-half (Spearman-Brown) at 240 s | 0.969 | 0.7 |  |
| 7 reliability | long_pause_share: split-half (Spearman-Brown) at 480 s | 0.978 | 0.7 |  |
| 7 reliability | long_pause_share: minimum span (s) | 60 |  |  |
| 7 reliability | f0_range: split-half (Spearman-Brown) at 60 s | 0.677 | 0.7 |  |
| 7 reliability | f0_range: split-half (Spearman-Brown) at 120 s | 0.754 | 0.7 |  |
| 7 reliability | f0_range: split-half (Spearman-Brown) at 240 s | 0.893 | 0.7 |  |
| 7 reliability | f0_range: split-half (Spearman-Brown) at 480 s | 0.937 | 0.7 |  |
| 7 reliability | f0_range: minimum span (s) | 120 |  |  |
| 7 reliability | int_var: split-half (Spearman-Brown) at 60 s | 0.826 | 0.7 |  |
| 7 reliability | int_var: split-half (Spearman-Brown) at 120 s | 0.823 | 0.7 |  |
| 7 reliability | int_var: split-half (Spearman-Brown) at 240 s | 0.962 | 0.7 |  |
| 7 reliability | int_var: split-half (Spearman-Brown) at 480 s | 0.978 | 0.7 |  |
| 7 reliability | int_var: minimum span (s) | 60 |  |  |

**`public/data-r3-P08-contrasts.csv`**

| row | row_text | scale | creators | estimate | lo90 | hi90 | margin | words |
|---|---|---|---|---|---|---|---|---|
| I4 | I4 acoustic nucleus speech rate (primary, A1) | log ratio | 12 or more | -0.002 | -0.063 | 0.059 | 0.223 | undetermined (battery criterion 1 (rate slope) not met) |
| I1 | I1 run recognizer: recognized syllables per second | log ratio | 12 or more | -0.045 | -0.121 | 0.031 | 0.223 | within the margin (B) |
| I2 | I2 larger recognizer (rv-R3 bridge recordings only) | log ratio | fewer than 5 |  |  |  | 0.223 | not computed (too few terms or creators) |
| I3 | I3 shifted grid (BR-GS recordings only) | log ratio | fewer than 5 |  |  |  | 0.223 | not computed (too few terms or creators) |
| I5 | I5 recognized syllables per nucleus (A4, deletion) | log ratio | 12 or more | -0.043 | -0.098 | 0.011 | 0.223 | undetermined (battery criterion 1 (rate slope) not met) |
| art | acoustic articulation rate | log ratio | 12 or more | 0.016 | -0.016 | 0.048 | 0.223 | undetermined (battery criterion 1 (rate slope) not met) |
| lps | long-pause share (shared channel, A2; never convergence) | difference | 12 or more | 0.009 | -0.034 | 0.053 | 0.05 | undetermined |
| f0 | F0 range (Tier 1, A3; two-sided) | standardised difference (between-creator SD of own-voice F0 range, from T) | 12 or more | 0.096 | -0.459 | 0.651 | 0.2 | undetermined |
| iv | intensity variability (Tier 1) | standardised difference (between-creator SD, from T) | 12 or more | 0.375 | -0.257 | 1.006 | 0.2 | undetermined |
| same | same-recording row: I4 within recordings holding both voices | log ratio | 12 or more | 0.013 | -0.079 | 0.105 | 0.223 | undetermined (battery criterion 1 (rate slope) not met) |
| nc | negative control: own voice in the first 60 s against own-voice interiors after it (I4) | log ratio | 12 or more | 0.042 | -0.072 | 0.157 | 0.223 | undetermined (battery criterion 1 (rate slope) not met) |

**`public/data-r3-P08-reading.csv`**

| row | value |
|---|---|
| eligible non-development creators after the background gate | 12 or more |
| A8 (12 or more eligible creators) | met |
| battery criterion 1, rate slope 0.9 to 1.1 | not met |
| battery criterion 1, pitch parts | met |
| battery criterion 3, rate (differential bias under a third of the margin) | met |
| battery criterion 3, pitch range | not met |
| primary I4 words before the conditions | within the margin (B) |
| reading of the primary (A1 with A4, A8 and the battery) | undetermined (battery criterion 1 (rate slope) not met) |
| why | not met: battery criterion 1 (rate slope) |


## Departures and rows not computed

- **Departure from the split policy's wording** (accepted as the lead's decision 106.1, decided 2026-11-26 18:16Z).
  Deposit 2's split policy builds a data-tuned rule on exploration half A and runs it once on sealed half B (tier S),
  or cross-fits it over the two halves (tier X). Here the only data-tuned part, the F0 and intensity
  standardisation unit, is fitted on the tuning pool T (the development creators) only, and the reading is made
  once on all eligible non-development creators (tier X by count).
  Reason: T sits on the exploration side and is never read for a split reading, so fitting on T alone keeps both halves
  out of every fit (decision 88's reading). **Limitation: half B is no longer sealed for the acoustic measures described
  here.**
- Praat (parselmouth) cross-check of the nucleus detector: not computed (tool not installed); the detector is a numpy
  implementation of de Jong and Wempe's rule.
- The battery's codec stratum (re-encoding at platform bit rates): not computed (not built in this batch).
- Margins are deposit 2's defaults (the programme states none); the speech member's tighter thresholds (a 5% slowing,
  plus or minus 0.05 log for A4) are not used, to avoid a second fork.

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

## Change by the lead's decision 114

2026-11-26T20:13:50Z (UTC, from the clock). No number changed. The results say "never accuracy"
for the agreement between voices, as every other output does.

## Files

| File | SHA-256 |
|---|---|
| `code/analyse_p08.py` | `33ff4d0f2ae17dab2d47f464628a4ed132d2f845907c7793cd7c7fc9f5f8ef4b` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `public/data-r3-P08-battery.csv` | `fd5050b4b39c50a45ea46aa81a4f501928f023c66fc5e1d5af9ddcc374ee71e6` |
| `public/data-r3-P08-contrasts.csv` | `c14525b1690a4ea2fbfbe92cc602118e38a7025bb6738c823e270110879915e7` |
| `public/data-r3-P08-reading.csv` | `6baf646d03f88d4f7137f4752485179665d6d987fd71c6041d39c3bcc0dcd38d` |
| `public/fig-r3-P08-five-instruments.pdf` | `575c541ab655b67fa72c483e02b58c06f3745f9585071dcd253c292dc3f09807` |
| `public/fig-r3-P08-five-instruments.png` | `ed121efb54466f89cb8a5d8e95bc1876f895ed13746091a2988a9fae5466e7d6` |

`status.json` carries the same hashes; `contacts.md` lists every read with its time.
