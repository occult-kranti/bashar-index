# r3-P15 / r4-P13: person or register? A distance ladder (step 5, class a.1)

Run on 2026-11-26 (UTC, from `date -u`) by the step-5 agent, a model agent working for the project lead (not a person).
Prespecification `prespec.md` with the shared rules `../common/prespec-common.md`, hashed together at 14:11:38Z
(`../common/prespec-hash-record.md`) before the extract ran. Extract 14:13:46Z to 14:15:17Z; analysis 14:18:00Z to
14:18:08Z; publication from 14:24Z.

**Exploratory; not a test of H1-H10.** Voice labels are model-coded (the small model, the label of record on seen
recordings) and not checked by a person. Recognizer text only; no audio. Every reading is about speech style, never about
a source.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Tier: unsplit** (deposit 2's split policy names r3-P15): all 71 seen creators, once. r4-P13 is carried here.

## What was measured

Function-word profiles (the closed list of the hypotheses code; contractions read as their parts; the creator's formula
4-grams removed, as E2), in parts of exactly 200 usable tokens (20 rarefaction draws), full and **person-free** (personal
pronouns, possessives, reflexives and "am" removed), each **z-scored** and **unstandardised**. Distance = 1 - cosine.
Rungs: own-own and claimed-claimed halves of one recording (the noise band), claimed-own in the same recording, across
recordings, pooled (E2's own rule) against other creators' claimed and own voices, and a decode rung on rv-R3's bridge
recordings (the record decode against the larger model of the same family).

Creator sets: same-recording rung 41 creators; own-own row 50; claimed-claimed row all but fewer than 5 of 56;
across-recordings rung 53; pooled rung 54; decode rung 5 to 9.

## Primaries and readings (margin 0.20 between-creator SD; 90% interval, r3-P30's choice for C_standardised: the t interval at these counts)

| Row (person-free) | z-scored | unstandardised | Primary reading |
|---|---|---|---|
| P1 same recording: claimed-own minus own-own (41) | 0.35 (0.10 to 0.60) | 0.26 (0.08 to 0.43) | **undetermined** (both intervals reach inside the margin) |
| P2 across recordings (53) | 0.65 (0.43 to 0.87), beyond | 0.35 (0.16 to 0.54), undetermined | **undetermined** (the standardisations disagree) |
| P3 persona or register, pooled: claimed against other creators' claimed minus claimed-own (54) | 1.27 (1.03 to 1.50) | 0.79 (0.56 to 1.01) | **beyond the margin (nearer the creator's own voice)** |
| P4, P4b decode rung (5 to 9) | - | - | not printed: the row's count is banded |

**The entry's reading** (prespec section 4): **undetermined**. P1, the same-recording rung on the person-free profile,
does not read beyond the margin, so neither "persona-like" nor "genre-register-like" is printed.

Described beside it (not the primary): on the **full** profile P1 and P2 read beyond the margin (claimed farther than
own-own) under both standardisations, so part of the claimed-own distance sits in pronouns, possessives and "am". On every
variant the claimed voice is nearer the creator's own voice than other creators' claimed voices (P3), in the direction of
E2's row (here at 200 tokens per part). **Claimed-claimed halves of one recording are nearer each other than own-own
halves** (P1b, person-free, beyond the margin under both standardisations: -0.57 (-0.88 to -0.26) and -0.56 (-0.78 to
-0.35)): the claimed voice is more uniform within a recording on these function words. Own voice against other creators'
own (P3b) is beyond the margin on every variant: the between-person scale of the ladder.

The decode rung's contrasts are withheld (decision 62: banded count, count-chosen method); its rung distances print as
described rows (their means; their intervals are not printed: privacy rule). P4b (how much a shared decode makes same-creator halves closer, the "recognizer text carries the speaker"
attack) is therefore not readable here.

Predictions deposited: none (deposit 2's cells for r3-P15 and r4-P13 are silent); nothing is scored.
Multiplicity: 56 primaries; if every true effect sat at half its margin, about 2.8 readings beyond the margin would be
expected by chance at the deposited 5%, up to about 6.1 for the share, standardised, AUC and rank-correlation classes. A
reading is never a finding.

## Rows not computed

The decode contrasts P4 and P4b (not printed: the row's count is banded); topic-matched segments, the transplant placebo and
the recitation-flagged sensitivity row (the recitation cue class is thin on tier L, step 2); middle-model rows; anything
acoustic.

## Files

| File | What |
|---|---|
| `public/data-r3-P15-ladder.csv` | every rung distance, profile and standardisation (described rows) |
| `public/data-r3-P15-contrasts.csv` | the standardised contrasts P1 to P4b with intervals and readings |
| `public/data-r3-P15-reading.csv` | the primaries and the entry's reading |
| `public/fig-r3-P15-ladder.png/.pdf` | the ladder: paired dot-intervals per rung with the own-own noise band |
| `public/fig-r3-P15-contrasts.png/.pdf` | the standardised rungs against the margin |
| `code/analyse_p15.py`, `code/publish_p15.py`, `code/style.py` | analysis, publication, the CHANGE group's style (unchanged); shared code in `../common/code/` |
| `prespec.md`, `contacts.md`, `status.json` | prespecification, contacts (none), status with every file's SHA-256 |

## Departures and choices (stated)

1. Imperative-opening units are not removed from the person-free profile (no tagger); the across-recordings rung is not
   matched on days apart.
2. Parts of 200 usable tokens (E2 used 1,500 per creator) so that rungs inside one recording exist; the noise band is
   computed at the same size.
3. The small model only (the middle model labelled few seen recordings in full).

## Privacy

Distributions over creators only; no per-creator row or point; no text, name, id or title. Counts follow the register rules
of step 1 and step 2; values that could narrow a banded count are not printed. Checks: `../common/README.md`.

## Change by the lead's decision 99 (2026-11-26T16:19:27Z, UTC from `date -u`)

- The decode rung's ladder intervals are not printed (privacy rule), as its contrasts are not. The ladder CSV and the
  ladder figure (redrawn by this entry's own figure function, changed so that it draws no decode interval) were
  changed. No number changed.
