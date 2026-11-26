# r3-P15 / r4-P13: person or register? A distance ladder (prespecification)

Written 2026-11-26 from 14:07:22Z (UTC, from `date -u`) by the step-5 agent (a model agent working for the project lead;
not a person), before any outcome of this entry was computed. Shared rules: `../common/prespec-common.md` (section 0).
Class a.1, step 5, after r3-P01 to r3-P04 (published). **Tier: unsplit** (deposit 2's split policy names r3-P15): all 71
seen creators, once.

**Exploratory; not a test of H1-H10.** Voice labels model-coded, not checked by a person. The persona-or-register
question of stylometry (N11), asked of recognizer-transcribed speech inside the recording. Every reading is about speech
style, never about a source.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Profiles

- **Tokens**: `features.tokens` per word of the transcript as transcribed (filter v2), each read through `features.h9_parts`
  (contractions split into their function-word parts), as E2. Tokens inside the creator's formula 4-grams
  (`features.formula_ngrams`, n = 4, share 0.5, over the creator's recordings) are removed and never counted.
- **Full profile**: counts of the closed function-word list (`features.FUNCTION_WORDS`).
- **Person-free profile** (ling's and den-meth's primary): the same list without personal pronouns, possessives and
  reflexives of every person and number (i, me, my, myself, we, us, our, ours, ourselves, you, your, yours, yourself,
  yourselves, he, him, his, himself, she, her, hers, herself, it, its, itself, they, them, their, theirs, themselves) and
  without "am" (a first-person form). Names are not on the list; the formula removal stands in for channel brand phrases.
  Imperative-opening units are not removed (no tagger; a departure from ling's wording, stated).
- **Parts**: every profile is built from a part of exactly M = 200 usable tokens (non-formula tokens), drawn without
  replacement from the part's tokens (rarefaction; 20 draws; one draw gives both the full and the person-free vector).
  Relative frequencies within the profile's function tokens.
- **Two standardisations**, both printed: z-scored (each function word standardised over every part of the draw, all
  rungs and creators together; words with zero variance dropped) and unstandardised relative frequencies.
- **Distance**: 1 minus the cosine of two vectors, averaged over the 20 draws.

## 2. Rungs (per creator; the same M everywhere)

Units outside H1's excluded formats, primary definition, unless stated.

- **Same recording** (recordings holding 2M = 400 or more usable tokens on each voice side): each side cut in time order
  into a first and a second half (each 200 or more usable tokens). OO = d(own 1, own 2), the own-own noise band; CC =
  d(claimed 1, claimed 2), two halves of one claimed span-set; CO = mean of d(claimed 1, own 2) and d(claimed 2, own 1).
  Creator value: mean over its eligible recordings. A separate OO-only row on recordings with 400 or more own tokens
  (whatever the claimed side holds), and a CC-only row likewise.
- **Across recordings**: per recording a claimed part (primary definition, 200 or more usable claimed tokens) and an own
  part (own-solo definition, 200 or more usable own tokens). OO_x = mean d(own part r, own part r') over pairs of distinct
  recordings; CO_x = mean d(claimed part r, own part r') over r different from r'. Creators with 2 or more own parts and a
  claimed part with an own part of another recording. Not matched on days apart (no stored rule; a departure, stated).
- **Pooled (E2's own rule)**: claimed tokens of claimed-voice units of any format (primary definition) and own tokens of
  own-voice units of solo recordings (own-solo definition), each pooled over the creator's recordings in recording then
  time order and cut into halves; creators with 400 or more usable tokens in each. OO_p, CO_p as above;
  CX = mean d(claimed half h of the creator, claimed half h of each other pooled creator), h = 1, 2; OX likewise for own.
- **Decode** (rv-R3's bridge recordings holding 400 or more usable tokens on each side under decode A, the English-only
  model of record as stored in the bridge pair, and 200 or more per half under decode B, the larger model): each word of
  both decodes takes the voice side of the nearest word of record in time. Within decode A: OO_A, CO_A; within decode B:
  OO_B, CO_B; cross-decode: OO_AB = mean of d(own 1 under A, own 2 under B) and d(own 2 under A, own 1 under B), and the
  same-span decode distance d(own h under A, own h under B).

## 3. Contrasts (creator values; standardised by the between-creator SD of the creator values of the reference distance)

| Row | Contrast | Reference distance (SD unit) |
|---|---|---|
| P1 same recording | CO - OO | OO |
| P1b same recording | CC - OO (claimed-claimed against own-own, same recording set) | OO |
| P2 across recordings | CO_x - OO_x | OO_x |
| P3 persona or register (pooled) | CX - CO_p (positive: the claimed voice nearer the creator's own voice than other creators' claimed voices; minus E2's D) | CO_p |
| P3b pooled own against other creators | OX - OO_p (the between-person scale) | OO_p |
| P4 decode B | CO_B - OO_B | OO_B |
| P4b recognizer idiosyncrasy | OO_AB - OO_A (same-decode closeness inflated by a shared decode) | OO_A |

Each row for the person-free and the full profile under both standardisations (4 variants). **Primary**: P1, P2, P3 on
the person-free profile; a row reads beyond or within the margin only if the z-scored and the unstandardised variant
give the same words, else "undetermined". Full-profile rows are secondary. The rung distances themselves (creator-balanced
means with intervals) are printed as described rows for the ladder figure, with the own-own band.

## 4. Intervals and readings

- Design class C_standardised (standardised difference; creator means of recordings): r3-P30's choice at the row's count
  (the t interval at 30 or more creators; section 0.5). Margin 0.20 between-creator SD.
- Words: P1, P1b, P2, P4: "beyond the margin (claimed farther than own-own)", "beyond the margin (claimed nearer than
  own-own)", "within the margin (B)", "undetermined". P3: "beyond the margin (nearer the creator's own voice)", "beyond the
  margin (nearer other creators' claimed voices)", "within the margin (B)", "undetermined". P4b: "beyond the margin (a
  shared decode makes own-own halves closer)", etc.
- **The entry's reading** (person-free primaries; only these words):
  1. P1 reads B: "claimed and own voice are not told apart beyond the own-own band at this resolution (neither persona nor
     register shows in function-word style)".
  2. P1 reads beyond (claimed farther) and P3 beyond (nearer the creator's own voice): "a shift beyond the own-own band
     that stays nearer the speaker's own voice than other creators' claimed voices (speaker-attributable, persona-like)".
  3. P1 beyond (claimed farther) and P3 beyond (nearer other creators' claimed voices): "nearer other creators' claimed
     voices than the speaker's own voice (genre-register-like)".
  4. Otherwise "undetermined".
  The decode rows (P4, P4b) are printed beside it: on 5 to 9 bridge creators they read at most "undetermined" (r3-P30
  finds no method that holds for C_standardised below 18), and P4b says how much of same-creator closeness a shared
  decode could carry.
- Predictions deposited: none (deposit 2's cells for r3-P15 and r4-P13 are silent). Nothing is scored.

## 5. Plot

"The ladder": paired dot-intervals per rung (own-own same recording as the noise band; claimed-claimed same recording;
claimed-own same recording; own-own and claimed-own across recordings; claimed against other creators' claimed;
own against other creators' own; decode rows), one panel per profile (person-free, full), z-scored and unstandardised
side by side; E2's registered row marked for reference. Distributions over creators only; no point per creator.

## 6. Not run here

Topic-matched segments, the transplant placebo and the recitation-flagged sensitivity row (the recitation cue class is
thin on tier L: step 2) are not run; the middle-model rows are not computed; nothing acoustic.
