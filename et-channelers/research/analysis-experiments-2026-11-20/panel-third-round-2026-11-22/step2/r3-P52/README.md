# r3-P52 / r4-P12: plural self-reference at recording level

Third-round panel programme, step 2 (class a.2, ruling 11), a description, not for registration. Run on 2026-11-26 (UTC,
from `date -u`) by the step-2 description agent, a model agent working for the project lead (not a person), in one run with
the other six step-2 description entries (shared code and run record in `../r3-P48/`; prespecification `prespec.md`,
hashed 12:46:51Z with the shared rules of `../r3-P48/prespec.md` section 0).

**Exploratory; not a test of H1-H10.** The 23 non-development seen creators (tier L), run once with no split. Cue counts.
Voice and map labels are model-coded and not checked by a person. The first person in claimed-voice recordings is
"presented as the source's".

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What it measures

ling's recording-level primary: no span label selects the units. Claimed-voice recordings (inside the frozen voice
definition, 300 or more claimed-voice words) are compared with the same creator's own-voice talks (no claimed-voice unit
under the record model's labels; not a conversation or multi-presenter format). Every token of a recording counts, outside
units holding a self-naming or address frame. The statistic is the within-creator shift of the first-person-plural share,
FP-PL / (FP-PL + FP-SG).

## Results in words

- **Eligible creators: 12** (printed first).
- **Primary:** the shift is 0.07 (Hodges-Lehmann, r3-P30's choice for class B at 12 creators, 90% -0.09 to 0.19):
  **"undetermined"** against the margin of 0.05. The creator mean (0.06) sits inside the band of matched function-word
  placebos (-0.10 to 0.11) and inside the own-voice noise band (-0.11 to 0.11). No single form decides (C2); the reading is
  the same at every precision value (C4). The sensitivity (any claimed word makes a claimed-voice recording) gives 0.05
  (-0.07 to 0.18), undetermined.
- **Spread over creators:** the noise-corrected between-creator SD of the shift is 0.15 (creator bootstrap 90% 0.00 to
  0.21), against the hashed threshold of 0.05: **"undetermined"** (neither "concentrated" nor "spread"). "A taught or copied
  format" is a third reading this statistic cannot tell apart from the other two. Recordings vary within creators far more
  than the binomial model allows (design effect about 20), which is why the noise bands are wide. The lower and upper halves
  of the 12 creators by shift average -0.14 and 0.26.
- **Beside r3-P42's span-level check:** r3-P42 found the first-person-plural share 0.21 higher in claimed-voice spans than in
  own-voice spans of the same recordings, outside its bands but term-dependent ("we"). At recording level, without span
  labels selecting the units, no such shift is told apart from noise or placebos on these creators.

Multiplicity (deposit 2): no family-wise adjustment; 56 primaries, about 2.8 readings beyond a margin expected by chance at
half-margin effects; a reading beyond the margin would never be called a finding.

## Files

| File | What |
|---|---|
| `public/data-r3-P52-shift.csv` | eligible count, primary, bands, spread, C2, C4, sensitivity, the two halves, reading |
| `public/fig-r3-P52-shift.*` | the shift with its interval, the halves, the noise and placebo bands and the hashed thresholds |
| `prespec.md`, `prespec-hash-record.md` | the prespecification and its hash |
| `code/p52.py`, `code/publish_p52.py`, `code/style.py` | analysis (run by `../r3-P48/code/analyse_desc.py`) and publication |
| `contacts.md`, `status.json` | contacts (none); status with every file's SHA-256 |

## Privacy

Creator counts printed: 12 (the eligible set; checked against every printed set, none nested within 1 to 4) and 6 for each
rule-sized half. No per-creator row or point. Checks: see `../r3-P48/README.md` (0 problems).

## Departures

1. **The display uses two rule-sized halves (6 and 6 creators) in place of a fixed-width histogram.** With 12 creators,
   every histogram whose bins hold 5 or more creators prints bin counts that the count rule bands, and banded bins that sum
   to the printed 12 would narrow each other to 4 or fewer values. The halves' means were added to the analysis after the
   first run (13:10), with no other change.
2. The own-voice talks are read from the bundle's record-model labels (step 1's own-only rule), as the prespecification
   says; the extract alone holds no sides for recordings outside the voice definition.

## For the lead

- The display departure (halves for the histogram) (decided: decision 69).
