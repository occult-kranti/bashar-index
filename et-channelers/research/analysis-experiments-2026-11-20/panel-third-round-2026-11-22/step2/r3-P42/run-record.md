# r3-P42: the run record (operational choices fixed before any list count)

Written 2026-11-26 between 11:40:48Z (the A6 hash) and 11:45:31Z (its first hash), UTC from `date -u`, by the r3-P42 agent (a model agent working for the project lead; not a
person), after deposit 3's merge (2026-11-26T11:14:53Z), the matcher's hash (11:35:21Z) and the A6 variant list's hash
(11:40:48Z), and **before any list term was counted**. It is hashed with `code/count_p42.py` and `code/p42common.py`
before the count runs. The prespecification (`deposits/deposit-3/r3-P42/prespec.md`, read with addendum 2d) binds; this
file only fixes what it leaves open. Every later change is a dated departure in the README.

Exploratory; not a test of H1-H10. Every count is a cue count, "sense not resolved, precision unknown", until a reader is
funded.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Units, text and voice

- **Creators.** The 23 non-development seen creators of the split (deposit 2, tier L), all their seen recordings, run
  once with no split. Text: the artefact-filtered transcript (`prep.load_units`), normalised by `lexmatch` (G1b, G1a, G1).
- **Voice.** The frozen voice labels under the primary definition (`voice_sets.definition()`: label of record, rule B,
  own voice broad, claimed voice V2 + V3). A recording outside the definition (claimant not admitted, or a model that did
  not label every unit) has no voice side: its tokens count in the all-voice totals only.
- **Token sequences.** One per recording and maximal run of consecutive label units on one side (claimed, own, or none).
  No form match and no gate window crosses a sequence (G5's "same recording and same label unit sequence").
- **Rates** are per 10,000 tokens. The **creator-balanced** value of a set of terms is the mean over creators of each
  creator's rate. A creator enters a **voice contrast** with at least 1,000 tokens on each side. The voice contrast is
  the creator-balanced log rate ratio, log(mean claimed rate) minus log(mean own rate), over those creators (margin:
  log 1.25, deposit 2).
- **Profiles** (C3 and the profile tests): the title profile (CSS-5's rule on the P1 title labels: star peoples without
  angelic or devotional figures, against angelic or devotional figures with or without star peoples; the ladder of CSS-5
  where a PERMANOVA needs several groups: the five profiles, then angelic joined with both, then any family against none,
  the first level at which every group holds 5 or more creators); the audience band (under 10,000 against 10,000 or more;
  the split's band); the economy type (client offers in 2 or more recordings, either evidence, against none; CSS-10's
  evidence, creators without page evidence left out). A contrast needs 5 or more creators in each group; its statistic is
  the log ratio of the two groups' creator-balanced rates. Group sizes and group means are never printed.
- **Concentration** (L06, and beside every class): the creator random-intercept variance of a gamma-Poisson model,
  by moments: phi = sum((y - mu)^2 - mu) / sum(mu^2), mu = tokens x pooled rate.

## C1: placebos and pseudo-strata

- **Candidates.** N-grams of 1 to 4 tokens inside one sequence. Excluded: any n-gram with a token inside a match of any
  form of any step-2 list (any rule kind, set-aside terms and frames included, before gates), a numeral (a token with a
  digit, or a number word) or a T190 named-person span. Tables: all speech; inside L08's base units (L08); inside the
  +/-30-token windows of L15's target-year tokens (L15). L09: function words of H9's closed list only (unigrams).
  L04: n-grams of title content words (not function words). L13: link hosts of the OWNSITE residual in the same page text.
- **Matching.** A real term (with 1 or more counted hits) is matched to one candidate with the same length (tokens of its
  most frequent counted span, 1 to 4 or more), frequency band (decile of total frequency among the candidates of that
  length, ties kept together) and dispersion band (creators using it: 1-4, 5-9, 10-19, 20-39, 40+). An empty cell is
  widened by one decile at a time, then by one dispersion band; the share of widened matches is printed. A term with no
  hit has no placebo. Within one draw a list never reuses a candidate (up to 20 redraws).
- **Draws.** K = 200 per list; each draw holds one placebo per real term, so class and layer sets are the draw's union
  over their terms. Stream `default_rng([seed C1-placebo, list number])`, terms in sorted order within each draw.
- **Estimates read against placebos.** Not the rate itself (frequency matching makes it equal by construction) but the
  structure a reading rests on: the voice contrast, the three profile contrasts, and phi; per list the statistic of
  section 5 (below). Reading: inside the central 90% of the 200 placebo values, "no excess over matched placebos" (the
  list or class fails as structure); outside, "outside the placebo band (above)" or "(below)".
- **Pseudo-strata** (L01 layers, L05 sub-registers, L10 modes, L14 families; L13's two suppression halves): the real
  terms keep their counts and their class labels are permuted, class sizes kept, 200 times (stream
  `[seed C1-pseudo-strata, list number]`). A class reading needs its estimate outside both bands.

## C2, C3, C4

- **C2.** Leave one term out (every term used by 1 or more creators), with the matched placebo of that term dropped from
  every draw; leave one form out for terms with 5 or more used forms. A term is influential if it carries more than 0.5
  of the creator-balanced count, or its removal changes the C1 reading, or moves a ratio estimate across log 1.25 (a
  share estimate across 0.05). Any influential term reads "undetermined (term-dependent)". Strips name only terms used by
  5 or more creators; the others are pooled.
- **C3.** For each term, its share of the class's creator-balanced count in the claimed voice minus its share in the own
  voice (voice-eligible creators); likewise group A minus group B for each profile. The matched placebo term's same
  difference inside its placebo set gives a spread over the 200 draws (central 90%); a creator bootstrap (B = 1,000,
  stream `[seed C3-bootstrap, list number]`) gives the term's 90% interval. A term whose interval lies wholly outside the
  placebo-term spread is flagged "functions differently". The class's voice reading is printed with and without flagged
  terms; disagreement reads "undetermined".
- **C4.** Term weights: every term 1.0; every term 0.5; terms whose register collisions name E or Y, or with a
  `blind_note`, at 0.3 and the rest 1.0 (L10: relay and dictation at 0.3); L05 by emic's ranges through `emic_C_code`
  (a class named by two codes takes the wider range; CR-E has none). The band is the range of the estimate over the
  weights; it reads "undetermined at unknown precision" when a weight changes the C1 reading or the side of the margin.
  Uniform weights leave a ratio unchanged, so the band moves only where weights differ between terms.

## The list checks (prespec section 5)

- **L01.** Parts: the 12 occult codes of the crosswalk (`memo_code_occult`, leading code; T084 and T090 split by form as
  the crosswalk says), set-aside terms removed. A creator enters with 1 or more composition hits. Multiplicative zero
  replacement at 0.5 (sensitivity 0.1); Aitchison distance (clr); PERMANOVA pseudo-F on the CSS-5 ladder's groups; labels
  permuted within quintile blocks of total tokens (1,999; stream `[seed C1-pseudo-strata, 101]`); dispersion check
  (distance to group centroid, F, same permutations). Bands: placebo (each composition row replaced by its matched
  placebo) and pseudo-strata (row labels permuted among parts). Sensitivity rows: RNT beside (et's placement), thin parts
  dropped, zero replacement 0.1, grades (A5), coder-shared forms dropped (A1), variants (A6).
  **Balances**: ilr balance of side A's parts against side B's parts (`r3-P43-balances-a2d.csv`, terms after all
  set-asides; occult family by occult codes, et family by et codes), zero replacement as above. Profile test: star against
  angelic or devotional (1,999 label permutations within the quintile blocks), with the L04 source-name rows left out of
  counts compared by profile; voice test: claimed minus own (1,999 within-creator sign flips; stream `[seed
  C1-pseudo-strata, 102]`); et B2 ("toward G4 in every profile") as a one-sample sign-flip test of the mean balance.
  Holm within each family. Directions from `r3-P48-predictions.md`. **Survival strip**: Spearman correlation of each
  dated layer's entry year (first year of `register-strata.csv`; S14 undated and S12 imported left out) with the share of
  creators using the layer; date-permutation null, 200 (stream `[seed C1-date-permutation, 1]`), and the placebo band.
- **L02.** Creator-by-layer incidence (a creator uses a layer with 1 or more counted hits). Pair statistic: creators using
  both. Null: curveball trades blocked by audience band, row and column margins kept within blocks, 200 draws after
  burn-in (stream `[seed C1-pseudo-strata, 2]`). Placebo band: incidence from the matched placebos. Structure only outside
  both. P000 not computed until r3-P54; P001 is L05 (not set aside, CR-A left out) against L06.
- **L03.** DIM only (DEN has no counted term): voice contrast, phi; "single-form" if one form carries more than half of
  DIM hits.
- **L04.** Creator-balanced share of titles naming an OPEN or FRANCHISE name, against title placebos; C2 by name; UNNAMED
  (a P1 title with no listed name) printed as a share of P1 titles and a number of titles.
- **L05.** Every class (CR-A not computed until r3-P54) by voice, by the three profiles, and phi; L05 as a whole is its
  classes other than CR-A.
- **L06.** phi against the placebo band (the creator random-intercept excess); voice contrast; A1 without coder-shared
  forms.
- **L07.** Description: voice contrast per class; the disclosure split is "not computable" if the flagged (both gates)
  creator-balanced count exceeds the counted one; A3.
- **L08.** For RES-INNER and RES-OUTSIDE, the creator-balanced share of a class's hits that fall inside the base units
  (units holding an L05 ADV-NEG, ADV-AMB or CR-A hit of a term not set aside), against the same share for placebo
  phrases matched on length, frequency and dispersion over all speech; both inside the band read "no excess"; a small
  share is never read as absence (a recall bound). (Amended before any count was read: a rate inside the base against
  placebos matched on frequency inside the base would be equal by construction.)
- **L09.** The creator-balanced first-person-plural share FP-PL / (FP-PL + FP-SG), outside frame units, claimed minus own
  (margin 0.05), against function-word placebos and an own-noise band (each voice-eligible creator's own-voice sequences
  split at random into two halves, 200 times, stream `[seed C1-pseudo-strata, 9]`).
- **L10.** Mode cue rates by voice inside the placebo band; a mode used by fewer than 5 creators reads "fewer than 5
  creators".
- **L11.** ENDORSE by voice, with and without "support this channel"; the co-occurrence needs REF-CREATOR, which is thin
  by design: "not computed (too few terms)".
- **L12.** A reading only if IDIOM is used by 5 or more creators.
- **L13.** Speech: the platform share of suppression talk (SUPP-PLATFORM over both halves, creator-balanced) against the
  pseudo-strata band of the two halves; "censored" stays flagged. Page links: creator-balanced share of links by class and
  by funnel depth; DEST-UNRESOLVED above 0.20 makes funnel depth "undetermined (unresolved links)"; class shares against
  host placebos.
- **L14.** Device families by voice and the priced share (a pilot; an instrument check only).
- **L15.** The creator-balanced share of the cue families' hits that fall inside the +/-30-token windows of target-year
  tokens (literature years 1844, 1954, 1987 and 2012), against the same share for placebo phrases matched over all speech.
  (Amended before any count was read, for the same reason as L08.) The control-year band needs year roles that deposit 3 does not fix (the ledger's passed years by a
  rule not deposited, control years "matched on anniversary demand" by a rule not deposited, the contested year a ruling
  not yet made): the failing check reads "not computed (year roles not fixed)".

## A1 to A6 and the collision matrix

- **A1.** Every estimate of L01, L03, L05, L06, L07, L08, L13, L14 and L15 again without the forms of
  `rule-coder-collisions-public.csv` for that term and list, with placebos re-matched.
- **A2.** The share of each list's forms set aside; a class losing more than half its terms to the trope set-aside reads
  "not computed until r3-P54 (waits for the owner's ethics act)"; ADV-NEG at exactly half is computed (decision 57 item 4).
- **A3.** Share of gate decisions whose evidence lies inside another list's counted span (L01, L05, L07, L11, L13); above
  0.10 the estimates are recomputed with the unmasked decisions and a changed reading reads "undetermined (gate overlap)".
- **A4.** Cell (list i, list j): the creator-balanced share of list i's count carried by its hits that overlap a counted
  hit of list j; printed in cells with 5 or more creators contributing; 90% creator bootstrap (B = 1,000, stream
  `[seed collision-bootstrap, list number of i]`). Coder row: the share carried by coder-shared forms. Above 0.20 both
  lists' estimates are reprinted without the shared hits. Beside it: the flagged share of each list (G6).
- **A5.** L01 readings again without rows whose `dating_certainty` contains "uncertain" or "undated", or whose
  `memo_contested` is yes or partly; disagreement reads "undetermined (grade)".
- **A6.** Readings again with the hashed variant forms added to their terms (L15: spoken years substituted, then
  matched).
- **C5.** No second author's list was hashed before the run (none exists): "not computed in this run".

## Privacy (binding: step-1 decisions 49 to 59 and 62)

Every public cell rests on 5 or more creators; no per-creator row or point; no names, ids, titles or corpus text; term
tables print deposited list terms only, and only terms used by 5 or more creators. No creator count is printed except the
23 non-development creators (deposit 2's count); counts that would be nested near it are not printed. Intervals come from
fixed methods only (placebo and permutation bands, the prespec's creator bootstrap), never from a method chosen by the
creator count. No group means, no quantiles of creator values, no spread over creators.
