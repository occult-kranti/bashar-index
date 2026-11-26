# r3-P42: additions proposed by the cross-review (to the prespecification draft)

Written 2026-11-26 from 10:24 UTC (from `date -u`) by the step-2 cross-reviewer, a model agent working for the project
lead (not a person). This file proposes additions to `step2/r3-P42/prespec-draft.md`. It edits nothing, is not hashed as
the prespecification, and runs nothing. The lead or r3-P42's author adopts, changes or rejects each item before the
prespecification is hashed.

**Written from the literature only, blind to the corpus; no count has been made.**

> Exploratory programme; no measure in this study can tell whether a non-human source speaks; every measure describes
> the speech in these recordings and how the creators present it.

## 1. The question: can every list fail?

The draft's five checks (C1 placebos and pseudo-strata, C2 term influence, C3 differential functioning, C4 precision
bands, C5 two-author test) can make most readings fail. Six gaps remain:

1. **No list is checked against the frozen ledger coder.** The coder's families share tokens with L01, L03, L05, L06,
   L07, L08, L13, L14 and L15 (`addendum-2-lists/rule-coder-collisions.csv`, 371 form-level matches). With no check, a
   reading of r3-P40 or r3-P49 could restate the ledger's own qualifier and energetic families.
2. **No check follows the set-aside of decision 51 L1.** After it, CR-A keeps 3 of its 11 terms and ADV-NEG keeps 3 of
   6. A rate on the residual looks like a reading of the class, but it is not.
3. **r3-P43 is not checked against the members' table.** The register's layers do not reproduce the memos' codes (review
   report, section 5.4), so a balance run on the layers is not the balance the members fixed.
4. **The survival strip cannot fail as drafted.** Only its placebo band is named. No null tests the link to the entry
   dates.
5. **Term-influence strips (C2) could print single-name counts.** Without a floor, a strip labels terms used by fewer
   than 5 creators, including being names (decision 51 L6).
6. **The draft's C5 rule is stronger than the historians'.** occult and et both wrote that the blind second agent "is
   reported as agreement only and changes no item". The draft turns disagreement into "undetermined (author-dependent)".
   The lead decides which rule binds for r3-P43; the draft's stronger rule can stay for the other lists.

## 2. General additions (apply to every list unless stated)

- **G-A1. Coder-shared forms (decision 51 L2).** Every estimate of L01, L03, L05, L06, L07, L08, L13, L14 and L15 is
  printed twice: with all forms, and without the forms that the frozen rule coder also matches. A reading that holds only
  with them reads "not separable from the ledger's coded families". This binds especially:
  - r3-P40 (L15): DEFER's postponed, delayed and pushed-back forms are the coder's prevention family, and "divine
    timing" is its time-hedge. FULFIL's "already happened" and "happened energetically" are its outcome-booster.
  - r3-P49 (L06): 5 of 7 shift terms carry the coder's energetic-predicate tokens, so shift density and the ledger's
    NE class overlap by construction.
- **G-A2. Set-aside rule (decision 51 L1).** Before any check, the terms marked "yes" or "possible" are removed, using
  column `L1_set_aside` of the addendum-2 lists. Then:
  - Print the share of the list's forms that were set aside.
  - A class that loses more than half its terms reads "not computed (set aside under decision 51 L1; waits for r3-P54)",
    not a rate on the residual. At present that is CR-A (8 of 11).
  - Placebos are matched to the residual list.
  - r4-P29's base is formed after the set-aside (addendum A2-089).
  - The threshold of one half is a proposal for the lead.
- **G-A3. Thin sides.** A balance side, pair side or class with fewer than 3 terms used by 5 or more creators reads
  "not computed (too few terms)". The threshold is fixed here. For example, occult's B3 has a single R10a term (T073).
- **G-A4. Name floor (decision 51 L6).**
  - C2 strips, C3 flags and any per-term table name a term only if 5 or more creators use it. Other terms are pooled as
    "other terms (fewer than 5 creators each)".
  - No count is printed per being name on fewer than 5 creators.
  - This applies to L01 S14, L04 and the named rows of L01.
- **G-A5. Gate audit (register G5; addendum A2-085).**
  - For every gated list (L01, L07, L11, L13), print the share of gate decisions whose gate word lies inside another
    list's counted span.
  - If that share is above 10% (proposal), recompute with masking (G5b).
  - A reading that changes under masking reads "undetermined (gate overlap)".
- **G-A6. Collision-matrix rule.** If shared tokens carry more than 20% (proposal) of a list's creator-balanced count
  against another list, the two lists' readings are not read as independent. Both are printed with the shared tokens
  dropped. The matrix gains a row for the ledger coder's families.
- **G-A7. Grades.** The historians require every r3-P43 sentence to hold on grade A and B items. The register has no
  grade column. Until the historians grade the rows, print each L01 reading twice: with all rows, and without rows whose
  `dating_certainty` is uncertain, undated or contested. Disagreement reads "undetermined (grade)".
- **G-A8. Recall audit for spellings and spoken numerals.**
  - After the deposit and before the run, a rule generates the recogniser variants and hashes them as a sensitivity
    list. Two kinds:
    - corpus word types within edit distance 2 of each listed rare name (Kuthumi, Djwhal Khul, Sananda, Metatron and
      others);
    - year and numeral forms written in words ("twenty twelve"; "five d").
  - Readings are printed with and without the sensitivity list.
  - The variants never enter the hashed lists, and are reported as counts of variant types, never per creator.
- **G-A9. Fixed values (the draft's "to fix").** The proposals:
  - K = 200 placebo draws, and 200 permutations for pseudo-strata.
  - Seeds derived from the SHA-256 of deposit 3's merge commit and the check's id.
  - Influence threshold: one term carrying more than half of the creator-balanced count, or moving the estimate across
    its margin.
  - Lower precision value: 0.5 for every list, plus a second band at 0.3 for terms with an E or Y collision or a
    `blind_note`. For L05, emic's per-code lower and upper bounds instead (see L05 below).
  - Dispersion bands as drafted.

## 3. Per list: the check that can make it fail

| List | Can it fail as drafted? | Added check |
|---|---|---|
| L01 dated strata (r3-P43) | Partly: C1 pseudo-strata, C2 and C5 can fail; the survival strip cannot | (a) **Memo-code check**: run B1 to B3 on the memo codes (`r3-P43-balances-a2.csv`) and print the register-layer version beside; differing readings read "undetermined (layer definition)". (b) **Date-permutation null for the survival strip**: permute entry dates across layers (K draws); the strip reads "dated order" only if its rank correlation with entry date lies outside the permutation band. (c) Items "not placed" by either memo (new age, gaia, indigo children, ufo, extraterrestrial, kundalini, reincarnation, christ consciousness, ectoplasm, aura) printed in and out. (d) G-A7. (e) L1 scope: whether the set-aside applies to r3-P43 and r3-P44 (programme section 5 scopes et's condition to them) is the lead's ruling; until then print both. |
| L02 pairs (r3-P44, r4-P27) | Partly: after L1 the decisive pair is not the pair the members predicted | The adversarial side after the set-aside holds abduction, greys, anunnaki and archons: abduction lore plus et's valence M, not his valence-A family. Print it only as "residual adversarial vocabulary (valence-A terms set aside)", never as the decisive pair. Apply G-A3. The decisive pair proper waits for r3-P54. |
| L03 density or dimension (r3-P45) | Yes (C5 required; permutation band) | (a) Single-form rule: if one form carries more than half of DIM hits, the share reads "single-form". (b) Camera exclusions (A2-079) applied. (c) G-A8 for spaced numerals. |
| L04 source-name classes (r3-P46) | Partly | G-A4 floor. A franchise class carried by one name (C2) reads "undetermined". The UNNAMED residual is printed with its size. |
| L05 control register (r3-P48) | Partly | (a) G-A2: CR-A "not computed" now. (b) C4 with emic's ranges by C code (C1 0.5-0.9; C2 0.4-0.85; C3w 0.5-0.9; C3e 0.4-0.85; C4 0.3-0.8; C5 0.3-0.75; bridge 0.2-0.7; C6 never in a denominator), through the crosswalk column `emic_C_code` once confirmed. (c) meas's scorecard rules (verbatim in `r3-P48-predictions.md`): rates, not shares; the primary placebo band; margins from P29; a fourth column for survival under the precision ranges. (d) et's window estimand cannot form A windows while the valence-A family is set aside: "not computed". |
| L06 shift terms (r3-P49) | Yes (C1 excess over placebo) | G-A1: print without the coder-shared energetic tokens; a concentration that holds only with them reads "not separable from the ledger's energetic family". |
| L07 named actors (r3-P51) | Partly | (a) G-A5 for both disclosure gates. (b) If the flagged (both gates) share exceeds the counted share, the institutional-against-consciousness split reads "not computable". (c) A sensitivity without the gate word "within" (A2-087). |
| L08 defanging (r4-P29) | Partly: a recall bound | (a) The base after the set-aside (A2-089); "fewer than 5 creators" if so. (b) Placebo phrases of matched length inside the same base units: both shares inside the band read "no excess". (c) G-A1: "mass arrests", "military tribunals", "being arrested" and the "your energy" forms are coder-shared. |
| L09 plural self-reference (r3-P52) | Yes (function-word placebo; own-noise band) | (a) The U.S. rule (A2-084) or a sensitivity without "us". (b) Frames run on a cased copy made before G1. |
| L10 modes (r3-P53) | Partly | Relay and dictation phrases are everyday (C4 at 0.3). Per-mode "fewer than 5 creators" is expected and printed as such. |
| L11 endorsement (r3-P55) | Partly | G-A5 for G-PLATFORM. "support this channel" printed with and without (A2-083). |
| L12 idiom, dissemination (r3-P56) | No reading of absence (a recall probe) | Print a reading only if idiom hits occur in 5 or more creators; G-A6 with L11 ("support this work"). |
| L13 destinations, suppression (r3-P60) | No, until the domain rows are fixed | (a) Print the share of OWNSITE links that are youtube.com, youtu.be or URL shorteners; above 20% the residual reads "not interpretable" until A2-093's rows are accepted. (b) "unalive" printed with and without (A2-082). (c) "censored" stays flagged. |
| L14 devices (r3-P61) | A pilot with no reading of its own (programme) | Report only as an instrument check for the comparison set. Emic's credential terms (A2-092) printed as a sensitivity if accepted. |
| L15 passed years (r3-P40) | Yes (control years are the test) | (a) G-A1: DEFER and FULFIL without coder-shared forms. (b) G-A8 for spoken years. (c) Target-year cue rates inside the control-year band read "no excess at target years". |

## 4. Order (unchanged, with one step added)

The lead's rulings on this file and on the review's decisions come first. Then deposit 3 is merged with the addendum-2
hashes. The variant sensitivity list (G-A8) is generated by rule and hashed. Then r3-P42 is hashed, and only then is
anything counted.
