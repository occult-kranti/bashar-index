# r3-P01 / r4-P01, part E: recognized syllables per acoustic nucleus, by self-presented voice (audio addendum)

Written 2026-11-26 (UTC, from `date -u`) by the audio-addendum agent, a model agent working for the project lead (not a
person), under the lead's decision 106.4. Prespecification: `../prespec.public.md` (published redacted), section 2 (hashed 2026-11-26T18:39:23Z,
before any outcome; `../prespec-hash-record.public.md`). Analysis 18:40:51Z to 18:41:02Z; publication from 18:45:44Z.

**Exploratory; not a test of H1-H10.** Seen creators only. Voice labels are model-coded (the small model, the label of
record on seen recordings) and not checked by a person; comparisons between instruments are agreement, never accuracy.
Acoustic features describe the sound of these recordings, never a speaker's state or a source; recovery was checked on
constructed audio only (an upper bound); no person listened. No audio was read, copied or decoded here: part E is computed
from the stored per-recording summaries of the audio pass.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What part E asks

r3-P01 (step 1) found no differential recognizer instability on families A, B1 and D, with the wording "no differential
instability detected among Whisper-family decodes; shared normalisation untested": two Whisper-family decodes can share a
deletion or a normalisation (a full form written for a contraction, a dropped filler) and agree on it. Part E is the
acoustic route to that shared error: per recording, the recognized syllables of the run recognizer of record divided by
the acoustic syllable nuclei (de Jong and Wempe's rule) over the same clean interiors, claimed voice over own voice. Fewer
recognized syllables per nucleus in the claimed voice would mean the recognizer writes less of that speech (deletion or
normalisation); it cannot see substitutions.

## How it ran

- **Tier: unsplit** (deposit 2's split policy names r3-P01): all seen creators, once. Departure from the split policy's
  wording, accepted as the lead's decision 106.1: data-tuned parts are fitted on the tuning pool T only and each reading is
  made once on all eligible creators (part E has no data-tuned part). Reason: T sits on the exploration side and is never
  read for a split reading, so fitting on T alone keeps both halves out of every fit (decision 88's reading).
  Limitation: half B is no longer sealed for the acoustic measures described here.
- **Base:** recordings holding both voices (primary definition; conversation and multi-presenter formats are not in the
  pass), passing the background gate (speech-to-background ratio 25 dB or more), with 60 s or more of clean interior on
  each side (battery criterion 7's minimum for rate measures). Creators: 40 to 49. A8 (12 or more): met.
- **E1 (primary):** per recording, log((S_c + 0.5) / (N_c + 0.5)) - log((S_o + 0.5) / (N_o + 0.5)); creator value: the
  precision-weighted mean over the creator's recordings, as r3-P01's creator values.
- **E2 (matched acoustic tempo, den-meth's form):** 10-s chunks of each side binned by acoustic articulation rate; the same
  log ratio within bins holding both sides; weighted over bins.
- **E3 (splice census):** E1 on recordings whose voice boundaries pass r4-P03's environment rule.
- **Interval:** r3-P01's rule: r3-P30's choice for design class A_log_ratio at the row's count (here the HKSJ interval
  with its SE floored at the DerSimonian-Laird SE, which holds at this count), random effects on creators with 2 or more
  recordings, each creator's variance floored at the Poisson sampling variance. The count prints as a band inside which
  r3-P30's choice is one method. Beside each row: the t interval on creator means, a sensitivity row (not the reading).
- **Margin:** 0.0222, r3-P01's hashed tolerance-arm margin for the syllable-rate contrast (part E's log ratio is the
  recognizer's rate contrast minus the acoustic one).
- **Battery caps (audio prespecification section 3; decision 106.3):** the nucleus rate recovers time-stretch changes with
  a slope of about 0.45 (criterion 1 not met), so "within the margin (B)", that is "no differential deletion detected",
  cannot be read; "beyond the margin" needs criterion 3 for rate (met) and E2 on the same side.

## Results

| Row | Creators | Estimate (90% interval) | Sensitivity: t interval | Words |
|---|---|---|---|---|
| E1 within recording (primary) | 40 to 49 | -0.068 (-0.105 to -0.031) | -0.075 (-0.117 to -0.034) | undetermined (the matched-tempo estimator does not agree) |
| E2 matched acoustic tempo | 40 to 49 | -0.041 (-0.070 to -0.013) | -0.047 (-0.083 to -0.011) | undetermined |
| E3 splice-census recordings | not computed or not printed | - | - | not computed or not printed |

**Reading of part E: undetermined.** E1's interval lies wholly below -0.0222 (claimed voice lower: fewer recognized
syllables per acoustic nucleus), but at matched acoustic tempo (E2) the interval reaches inside the margin, so the two
estimators named in the prespecification do not give the same words.

**In words.** Within recordings that hold both voices, the run recognizer writes about 4 to 7% fewer syllables per acoustic
nucleus in claimed-voice interiors than in own-voice interiors, on both estimators' point estimates; the within-recording
estimate is beyond r3-P01's margin, the tempo-matched one is not clearly so. Two readings remain open: differential
deletion or normalisation by the recognizer in the claimed voice, or the nucleus detector's compression of rate
differences (a slower or faster voice moves this ratio toward the recognizer's rate contrast even with no deletion; E2
holds acoustic tempo but cannot undo the compression). r3-P08's non-development row I5 (pooled interiors; published) points
the same way (about -0.043, interval including zero). r3-P01's wording stands: **shared normalisation is still untested**;
part E does not clear it and does not show it. A reading is never a finding.

Predictions deposited: none (deposit 2's cells for r3-P01 and r4-P01 are silent); nothing is scored. Multiplicity: 56
primaries in the programme; if every true effect sat at half its margin, about 2.8 readings beyond the margin would be
expected by chance. A reading is never a finding.

## Rows not computed

- E3 (splice-census recordings): not computed or not printed.
- **Family C over the whole seen roster and r3-P02's grid rows (the GPU re-decode): not run** (the lead's decision 106.4:
  a re-transcription of the seen recordings, read as covered by the owner's instruction of 26 November; it goes to the
  owner and to the fourth panel's agenda). See `../r3-P02/`.
- A recognizer of another family (package ruling); a person's word reference (class c, inside r3-P25).

## Departures and choices (stated)

1. The margin is r3-P01's own tolerance-arm row for the syllable-rate contrast (0.0222), not deposit 2's default ratio
   margin and not the speech member's 0.05 for A4: one margin, the entry's own (prespecification section 2).
2. The variance floor of the random-effects methods is the Poisson sampling variance of a recording's log ratio (r3-P01
   floored shares at their binomial variance); fixed in the prespecification.

## Files

| File | What |
|---|---|
| `public/data-r3-P01-partE.csv` | rows E1 to E3 with intervals, sensitivity rows and words |
| `public/data-r3-P01-partE-reading.csv` | A8, the battery conditions, the reading, the rows not run |
| `public/fig-r3-P01-partE.png`, `.pdf` | E1 and E2 against the margin, beside r3-P08's published rows for scale |
| `code/analyse_p01e.py`, `code/publish_p01e.py`, `code/style.py` | analysis, publication, the CHANGE group's style (copied unchanged); shared code in `../common/code/` |
| `contacts.md`, `status.json` | contacts; every file's SHA-256 |

## Privacy

No per-creator or per-recording value or point; no audio, waveform or spectrogram; no names, ids, titles or quotations.
Creator counts print as bands in which r3-P30's interval choice is one method, so decision 62 does not apply. Values that
could narrow a banded count are not printed. Checks: `../README.md`.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Change by the lead's decision 113

2026-11-26T19:57:53Z (UTC, from the clock). No number changed. The prespecification is cited as its published, redacted
copy (`../prespec.public.md`), hashed at 18:39:23Z (UTC), before any outcome; the hash is kept privately (step-1 decision 49 item i); its citation of the audio
prespecification's hash is replaced. CSV headers are rewritten by rerunning the code for headers only, and every hash in
`status.json` is refreshed; the originals are listed there under `not_published`.

## Change by the lead's decision 114

2026-11-26T20:13:50Z (UTC, from the clock). No number changed. The contact log carries the half-B limitation of decision 106.1.
