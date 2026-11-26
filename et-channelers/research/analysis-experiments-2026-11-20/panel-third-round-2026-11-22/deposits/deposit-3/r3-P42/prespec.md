# r3-P42: lexicon checks without a reader (final prespecification, deposit 3)

Final text written 2026-11-26 from 10:39 UTC (from `date -u`) by the step-2 cross-reviewer, a model agent working for
the project lead (not a person). It merges the writer's draft (`prespec-draft.md`, 09:41 UTC) with the cross-review's
additions (`../review/r3-P42-prespec-additions.md`) and the lead's decisions 54 and 55 (2026-11-26). Every value the
draft left "to fix" is fixed here. It is hashed before the first lexicon count and is not revised after any count is
seen.

**Written blind to the corpus; no count has been made.**

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. What the programme asks

Programme step 2 says the lists are "hashed as a first draft before any count, and checked by a two-author test and a
placebo generator drawn from the corpus vocabulary, matched on frequency band and on dispersion over creators
(pseudo-strata of the same terms for partition claims)". r3-P42 "makes the lists able to fail as structure (not as
meaning): placebos, term influence, differential functioning across profiles and voices, precision bands". The plot is
"term-influence strips against the full estimate; each placebo's spread as a grey band on every lexicon figure".

Every count is a cue count, "sense not resolved, precision unknown", until a reader is funded. Readings follow the
lead's margins and readings of 2026-11-26 (deposit 2) and the floor rule. Fewer than 5 eligible creators reads "not
computed (fewer than 5 creators)".

## 2. Inputs (fixed)

- **Lists.** For each list, the latest deposited version: the addendum-2b file if there is one, else the addendum-2
  file, else the original. The matching rules are G1 to G10 of `r3-P41/README.md` as amended by
  `addendum-2b/rules-a2b.md` (G1a spoken years, G1b the country, G1c link hosts, G5 and G5b gates, and the set-aside).
  For each list:

  | List | Version used |
  |---|---|
  | L01 | the two a2b files (S01 alone; all other layers) |
  | L02 | a2b |
  | L03 | a2b |
  | L04 | a2b |
  | L05 | a2b |
  | L06 | a2 |
  | L07 | a2b |
  | L08 | a2b |
  | L09 | a2b |
  | L10 | original |
  | L11 | a2b |
  | L12 | original |
  | L13 | a2b |
  | L14 | a2b |
  | L15 | a2 |

- **Units.** All non-development seen creators, run once with no split (split policy, tier L). Voice comes from the
  frozen voice labels, read by the counting agent only.
- **Crosswalk and balances.** `addendum-2b/r3-P43-crosswalk-a2b.csv` and `addendum-2b/r3-P43-balances-a2b.csv`.
- **The frozen rule coder** (deposit 2, SHA-256 `4fe41740...5aef71`) supplies the coder-shared flags (section 4, A1).
  The public collision table gives the list side and the coder family only.

## 3. Fixed values

| Item | Value |
|---|---|
| Placebo draws (C1) | K = 200 per list and per class or layer that a reading rests on |
| Pseudo-strata permutations (C1) | 200 |
| Date-permutation null for the survival strip | 200 |
| Composition test permutations; sign-flip draws by voice | 1,999 each |
| Creator-cluster bootstrap (C3, intervals, collision matrix) | B = 1,000 |
| Intervals and bands | central 90% |
| Frequency band | decile of total token frequency over all eligible creators |
| Dispersion band (creators using the term) | 1-4, 5-9, 10-19, 20-39, 40 or more |
| Length match | same number of tokens (1, 2, 3, 4 or more) |
| Influence threshold (C2) | one term carries more than 0.5 of the creator-balanced count, or dropping it moves the estimate across its margin or changes the reading |
| Precision values (C4) | every term at 1.0; every term at 0.5; terms with an E or Y collision or a `blind_note` at 0.3 while the rest stay at 1.0; L05 by emic's ranges (section 5, L05) |
| Thin rule | a class, layer, part or balance side with fewer than 3 terms used by 5 or more creators reads "not computed (too few terms)" |
| Name floor | no term is named in any strip, flag or table unless 5 or more creators use it; no count per being name on fewer than 5 creators (decision 51 L6) |
| Collision-matrix rule | shared tokens carrying more than 0.20 of a list's creator-balanced count: both lists are reprinted with the shared tokens dropped |
| Gate-audit rule | gate evidence inside another list's counted span above 0.10 of gate decisions: recompute with G5b; a changed reading reads "undetermined (gate overlap)" |
| Unresolved links (L13) | DEST-UNRESOLVED above 0.20 of a creator-balanced link count: funnel depth reads "undetermined (unresolved links)" |
| Zero replacement (composition) | multiplicative replacement at 0.5, with 0.1 as a printed sensitivity (two small counts, occult) |

**Seeds.** Each check's seed is the first 8 hex digits of `SHA-256("r3-P42|<check>|deposit-3")`, read as an integer. A
list's stream is `numpy.random.default_rng([seed, list number])`; the list number is 1 to 15 from L01 to L15.

| Check | Seed |
|---|---|
| C1-placebo | 3989941755 |
| C1-pseudo-strata | 3051987102 |
| C1-date-permutation | 1517066409 |
| C2-term-influence | 3951918056 (deterministic; for ties only) |
| C3-bootstrap | 612259125 |
| C4-precision | 3992606446 (deterministic; unused) |
| C5-two-author | 2366589369 (unused) |
| G-A8-variants | 1611084756 (deterministic; unused) |
| collision-bootstrap | 2599928295 |

The composition test and the sign-flip draws use the C1-pseudo-strata seed with stream numbers 101 and 102.

## 4. The checks

### C1. Placebo lists and pseudo-strata

- **Draw.** For each list, and for each class or layer a reading rests on, draw K placebo term sets from the corpus
  vocabulary of the same creators. Each placebo term is matched to one real term on frequency band, dispersion band and
  length. Further matching by list:
  - L09: word class (function words for pronouns);
  - L13: link hosts drawn from the same page text;
  - titles (L04): matched on word class.
- **Candidates excluded.** Placebo candidates exclude every form on any step-2 list or addendum, every set-aside term,
  numerals, and spans matched by the named-person pattern.
- **Matched to the residual.** Placebos are matched to the list after the set-aside, not before.
- **Pseudo-strata.** For L01, L02, L05's sub-registers, L10's modes and L14's families: keep the real terms and permute
  their layer or class labels, preserving class sizes. A layer or class reading needs its estimate beyond the
  pseudo-strata band as well as the placebo band.
- **Reading.** An estimate inside the central 90% of its placebo distribution reads "no excess over matched placebos".
  The list fails as structure. The grey band on every lexicon figure is this distribution.

### C2. Term influence

- Leave-one-term-out over every term used by 1 or more creators. Also leave-one-form-out for terms with 5 or more forms.
- **Reading.** The reading fails as structure ("undetermined (term-dependent)") if any single term crosses the influence
  threshold.
- The term-influence strip names terms under the name floor.

### C3. Differential functioning across profiles and voices

- For each term, compare its share of the list's count across voices (claimed against own) and across creator profiles
  (title profiles, audience band, economy type) with the spread placebo terms show in the same comparison (creator
  bootstrap).
- **Reading.** A term outside the placebo-term spread is flagged "functions differently". A list reading by voice is
  printed with and without flagged terms; disagreement reads "undetermined".

### C4. Precision bands

- Recompute each estimate under the precision values of section 3.
- **Reading.** A band that crosses the margin reads "undetermined at unknown precision". The class-c precision reads
  (r3-P41, r3-P43, r3-P60, under 1 to 3 USD each) are the only way to narrow it.

### C5. Two-author test

- A second agent, blind to the corpus and to these lists' terms, writes an independent list for each class from the
  class definitions in `lists-README.md` and the same literature rule. It is hashed before any count.
- **r3-P43**: the result is printed as **agreement only** and changes no item and no reading (decision 54 item 6, in the
  two historians' words).
- **Every other list**: the reading is printed under both lists, and disagreement (A against B or undetermined) reads
  "undetermined (author-dependent)". r3-P45 is partly post hoc and must carry this test.

### A1. Coder-shared forms (decision 51 L2)

- Every estimate of L01, L03, L05, L06, L07, L08, L13, L14 and L15 is printed twice: with all forms, and without the
  forms marked in the public collision table (`rule-coder-collisions-public.csv`).
- A reading that holds only with them reads "not separable from the ledger's coded families".
- This binds r3-P40 (L15 deferral and fulfilment) and r3-P49 (L06), where most forms are coder-shared.

### A2. Set-aside (decisions 51 L1 and 54 items 2 and 3)

- Terms marked "yes" or "possible" are removed before every check, in the entries listed in `rules-a2b.md`.
- The share of each list's forms set aside is printed.
- These print "**not computed until r3-P54 (waits for the owner's ethics act)**":
  - CR-A of r3-P48;
  - r4-P27's decisive pair (L02 P000);
  - et's A-window estimand for r3-P48, with its negative control;
  - any other class that loses more than half of its terms.
- No residual is built after the fact.
- r4-P29's base is formed after the set-aside.
- **r3-P38.** Its counts follow the frozen coder unchanged, with a sensitivity row that drops statements whose
  prevention-family match lies on a span matched by a register term marked "yes" or "possible".

### A3. Gate audit (G5 and G5b)

- For L01, L05, L07, L11 and L13, print the share of gate decisions whose evidence lies inside another list's counted
  span.
- Above 0.10, apply the gate-audit rule of section 3.
- Per G5b, gates are evaluated with those spans masked.

### A4. Collision matrix (r3-P41's plot)

- **Cells.** Lists against lists, plus one row for the ledger coder's families. Each cell is the creator-balanced share
  of a list's count carried by tokens that also count on the other list (G3), in cells of 5 or more creators, with
  bootstrap intervals.
- **Beside it.** The flagged share of context-assigned tokens per list (G6).
- **Rule.** The collision-matrix rule of section 3.

### A5. Grades

- Every r3-P43 reading is printed twice: on all rows, and without rows whose dating certainty is uncertain, undated or
  contested.
- The historians require statements to hold on grade A and B items, so disagreement reads "undetermined (grade)".

### A6. Recall audit for spellings and spoken numerals

- **When.** After the deposit and before the run.
- **What is generated** (by rule, and hashed as a sensitivity list):
  - the corpus word types within edit distance 2 of each listed rare name of L01 and L04;
  - year and numeral words that G1a does not convert.
- **How it is used.** Readings are printed with and without the list.
- **Never.** The variants never enter the hashed lists, and their counts are never printed per creator.

## 5. The check that can make each list fail

| List | Fails when |
|---|---|
| L01 dated strata (r3-P43) | **Composition test (the shared primary, decision 54 item 4).** Creator-level PERMANOVA on Aitchison distance over the parts R1, RNT, R2, R3, R4, R5, R6, R7, R8, R9, R10a, R11 (crosswalk codes; set-aside terms removed). Profile labels are permuted within quintile blocks of total words (1,999 permutations), with a dispersion check beside. The baseline, devotional, imported and contested columns (and items placed by neither memo) are printed beside, never inside. A sensitivity row puts New Thought beside the composition (et's placement). A second sensitivity row drops thin parts. A test inside the placebo and pseudo-strata bands reads "no stratigraphic structure beyond placebos". **Balances: two named families**, occult's B1 to B3 and et's B1 to B3 (`r3-P43-balances-a2b.csv`), each with Holm within its family, and directions as fixed in `r3-P48-predictions.md`. Profile tests use 1,999 label permutations; voice tests use 1,999 within-creator sign flips. Terms that define a CSS-5 profile are left out of counts compared by profile. Thin sides read "not computed (too few terms)". **Survival strip**: reads "dated order" only outside the date-permutation band. Plus A1, A5, A6, C2 and C5 (agreement only). |
| L02 pairs (r3-P44, r4-P27) | A pair counts as structure only outside both the blocked curveball null and the placebo band. The decisive pair P000 is not computed until r3-P54. Layer pairs exclude set-aside terms. |
| L03 density or dimension (r3-P45) | Inside the permutation band of shuffled density/dimension labels. One form carrying more than half of DIM hits reads "single-form". C5 is required, with the draft rule. A1. |
| L04 source-name classes (r3-P46) | A class carried by one name (C2) reads "undetermined". Name floor. UNNAMED printed with its size. |
| L05 control register (r3-P48) | Per-sub-register rate distributions by profile and voice. CR-A is not computed until r3-P54. Other classes are computed on terms not set aside, inside C1, C2 and C3. C4 uses emic's ranges through the accepted crosswalk: C1 0.5-0.9; C2 0.4-0.85; C3w 0.5-0.9; C3e 0.4-0.85; C4 0.3-0.8; C5 0.3-0.75; bridge 0.2-0.7; C6 never in a denominator. The prediction scorecard follows meas's four rules (verbatim in `r3-P48-predictions.md`). It never uses 100% stacked bars. A1. |
| L06 shift terms (r3-P49) | No excess over matched placebos (C1; a creator random-intercept model), never the shift curve alone. A1: a concentration that holds only with coder-shared forms reads "not separable from the ledger's energetic family". |
| L07 named actors (r3-P51) | Description only. If the flagged share (both disclosure gates pass) exceeds the counted share, the institutional-against-consciousness split reads "not computable". A3. Position-matched rows as the programme states. |
| L08 defanging (r4-P29) | The base after the set-aside, or "fewer than 5 creators". Placebo phrases of matched length inside the same base units: both shares inside the band read "no excess". A recall bound: a small share is never read as absence. A1. |
| L09 plural self-reference (r3-P52) | The function-word placebo and the own-noise band. The eligible count is printed first. Frames run on a cased copy made before G1. |
| L10 modes (r3-P53) | Mode cue rates by voice inside the placebo band, or fewer than 5 creators per mode (the expected reading). Relay and dictation phrases at precision 0.3 (C4). |
| L11 endorsement (r3-P55) | Co-occurrence is a lower bound. A3 for G-PLATFORM. Inside the position-matched band reads "no difference". |
| L12 idiom and dissemination (r3-P56) | A reading only if idiom hits occur in 5 or more creators. Absence is uninformative (a recall probe). A4 with L11. |
| L13 destinations and suppression (r3-P60) | The unresolved-links rule; "censored" stays flagged. Platform and suppression shares inside their permutation bands read "no difference". |
| L14 devices (r3-P61) | A pilot with no reading of its own: an instrument check for the comparison set only (programme). |
| L15 passed years (r3-P40) | Target-year cue rates inside the control-year band read "no excess at target years". A1 (deferral and fulfilment forms without coder-shared forms). A6 for spoken years. Year roles come from the frozen ledger by rule and the contested-year ruling. |

## 6. Order

1. Deposit 3 is merged. It holds the original register and lists, addendum 2, addendum 2b, this file and their hashes.
2. The A6 variant list is generated by rule and hashed.
3. The second author's lists (C5) are hashed.
4. The run is made once, after which nothing in this file changes.
