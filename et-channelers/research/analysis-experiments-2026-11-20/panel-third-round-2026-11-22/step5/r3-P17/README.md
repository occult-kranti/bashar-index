# r3-P17: a calm-register control, text rows (step 5, class a.1)

Run on 2026-11-26 (UTC, from `date -u`) by the step-5 agent, a model agent working for the project lead (not a person).
Prespecification `prespec.md` with `../common/prespec-common.md`, hashed at 14:11:38Z before the extract ran; analysis at
14:18:56Z; publication from 14:25Z.

**Exploratory; not a test of H1-H10.** Voice labels and the recording's main kind (voice map) are model-coded and not
checked by a person. Text rows only: rate and pauses come from the recognizer's word times; the acoustic primary is not
computed here (audio, later).

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Tier: unsplit** (the split policy names r3-P17): all 71 seen creators. Guided practice is split by voice, since, in
occult's reading (a reading by a non-holder), many guided meditations in this milieu are led in a claimed voice.

## Groups (300 or more words per creator)

Claimed voice outside guided practice: all but fewer than 5 of 56 creators. Own-voice guided practice: 25. Own-voice talks
(solo format): 54. Claimed-voice guided practice: not computed (too few terms or creators).

## Contrasts and readings (t interval on creator means, fixed in advance; margins |log ratio| 0.223 and 0.05)

| Contrast | Creators | Articulation rate (log ratio) | Long-pause share (difference) |
|---|---|---|---|
| C3 claimed voice against own-voice guided practice (primary) | 10 to 19 | 0.07 (0.02 to 0.12): within the margin (B) | -0.26 (-0.35 to -0.17): beyond the margin (claimed lower) |
| C2 own-voice guided practice against own-voice talks | 20 to 29 | -0.10 (-0.15 to -0.05): within the margin (B) | 0.27 (0.21 to 0.34): beyond the margin (guided practice higher) |
| C1 claimed voice against own-voice talks | 43 | -0.06 (-0.09 to -0.03): within the margin (B) | 0.01 (-0.01 to 0.04): within the margin (B) |
| C4 claimed-voice against own-voice guided practice | - | not computed (too few terms or creators) | not computed |

**The entry's reading** (prespec section 3):
- **Articulation rate: not informative at this size (undetermined).** The claimed voice is within the margin of both
  own-voice talks and own-voice guided practice, so there is no rate difference for a calm register to account for.
- **Long-pause share: the claimed voice differs from own-voice guided practice.** Guided practice holds far more time in
  long gaps (about 0.38 of its run time against about 0.10 for the claimed voice and for own-voice talks); the claimed
  voice's long-pause share is within the margin of own-voice talks.

So on these text rows the claimed voice does not look like the calm register of the same creators' guided practice. The
expected reading was "not informative at this size"; for the long-pause share it is informative. Acoustic delivery may
differ (audio, later).

Predictions deposited: none (deposit 2's cells are silent; occult's reading is not attributed to an account).
Multiplicity: 56 primaries; about 2.8 readings beyond the margin expected by chance if every true effect sat at half its
margin, up to about 6.1 for the share, standardised, AUC and rank-correlation classes. A reading is never a finding.

## Rows not computed

The acoustic primary (audio, later); claimed-voice guided practice and C4 (too few terms or creators); the sensitivity rows
without recitation-flagged recordings (the recitation cue class is thin on tier L, step 2); middle-model rows.

## Files

| File | What |
|---|---|
| `public/data-r3-P17-groups.csv` | creator-balanced means per group (described rows) |
| `public/data-r3-P17-contrasts.csv` | C1 to C4 with intervals and readings |
| `public/data-r3-P17-reading.csv` | the entry's reading per measure |
| `public/fig-r3-P17-calm-register.png/.pdf` | group means beside the contrasts and their margins |
| `code/analyse_p17.py`, `code/publish_p17.py`, `code/style.py` | analysis, publication, style; shared code in `../common/code/` |
| `prespec.md`, `contacts.md`, `status.json` | prespecification, contacts (none), status with every file's SHA-256 |

## Departures and choices (stated)

1. The interval is the t interval on creator means for every row, fixed in the prespecification rather than chosen by
   count (two of the contrast sets print as bands). For the rate rows r3-P30's class G chooses the same method at 12 or more
   creators; the share rows compare groups of different recordings, which no r3-P30 class describes ("interval class not
   calibrated by r3-P30").
2. Distributions are drawn as creator-balanced means with intervals, not histograms: two of the groups print as bands.
3. Long gaps are not capped (long silences belong to the register this control is about).

## Privacy

No per-creator row or point. Counts follow the register rules; rows below the 5-creator floor print only "not computed".
Checks: `../common/README.md`.
