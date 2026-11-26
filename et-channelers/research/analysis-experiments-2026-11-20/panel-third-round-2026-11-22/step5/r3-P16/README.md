# r3-P16: who shifts? Register shift by self-described mode (step 5, class a.2)

Run on 2026-11-26 (UTC, from `date -u`) by the step-5 agent, a model agent working for the project lead (not a person).
Prespecification `prespec.md` and `../common/prespec-common.md`, hashed at 14:11:38Z before the extract ran; analysis
14:22:36Z to 14:22:42Z; publication from 14:30Z.

**Exploratory; not a test of H1-H10; description only.** Every account predicts the same dose (D23), so this retires
none; only a flat or reversed ordering would inform. Mode is self-presentation from cue counts (sense not resolved,
precision unknown): "creators who describe their practice as X". Voice labels model-coded, not checked by a person.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Tier L**: the mode groups count deposit 3's L10 through the shared matcher on the 23 non-development creators (L10's
totals equal r3-P42's counts; the groups equal r3-P53's). The shift needs both voices and is computed on the 11
voice-eligible creators.

## Results in words

- **The shift over the 11** (S = claimed-own minus own-own distance in SD units of own-own; r3-P15's profiles on pooled
  parts): person-free, z-scored (the primary) 0.49 (0.11 to 1.27), **undetermined** (r3-P30 finds no method that holds for
  C_standardised at 11, so every reading is at most undetermined). The other variants: person-free unstandardised 0.50
  (-0.09 to 1.00); full z-scored 0.84 (0.31 to 1.54) and full unstandardised 2.18 (1.26 to 3.04), both "undetermined
  (r3-P30: no method holds at this count)". Fewer than 5 of the 11 do not shift (S below 0.20).
- **By self-described mode: not computed (too few terms or creators).** Only two of L10's eight modes are computed on
  tier L (higher self or Source; relay), and within the 11 one side of each comparison holds fewer than 5 creators, too few for a
  comparison. The six other modes read "not computed (too few terms or creators)" from step 2.
- **Delivery rows: not computed here (audio, later).**
- **The expected reading "undetermined" holds.**

**Predictions scored**: deposit 2's cells for r3-P16 say, for every account, "same as every other account (direction not
stated)": scored as **no account is retired, whatever the result (D23)**. Nothing else is scored.
Multiplicity: 56 primaries; about 2.8 readings beyond the margin expected by chance if every true effect sat at half its
margin, up to about 6.1 for the share, standardised, AUC and rank-correlation classes.

## Rows not computed

The shift by mode group (both computed modes); the six thin modes; delivery rows (audio, later).

## Files

| File | What |
|---|---|
| `public/data-r3-P16-shift.csv` | the shift over the 11 (four variants), the count of creators who do not shift, bins, group rows, predictions |
| `public/fig-r3-P16-shift.png/.pdf` | the distribution of S over the 11 with the noise band; S under the four variants |
| `code/analyse_p16.py`, `code/publish_p16.py`, `code/style.py` | analysis, publication, style; shared code in `../common/code/` |
| `prespec.md`, `contacts.md`, `status.json` | prespecification, contacts (none), status with every file's SHA-256 |

## Departures and choices (stated)

1. U1's estimate is r3-P30's Hodges-Lehmann estimate (the pseudo-median), the method chosen for C_standardised at 11.
2. Group counts within the 11 and the "does not shift" counts of the non-primary variants are not printed: the rows below
   the floor print only "not computed (too few terms or creators)" (a privacy choice made after the results; no value
   changes).

## Privacy

No per-creator row or point; no group mean (no group comparison computed). Checks: `../common/README.md`.
