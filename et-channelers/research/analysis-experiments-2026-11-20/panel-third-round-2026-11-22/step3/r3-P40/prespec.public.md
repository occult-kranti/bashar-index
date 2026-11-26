<!-- Redacted public copy of `prespec.md`, made 2026-11-26T14:25:54Z (UTC, from date -u) by the step-3 agent. The original was hashed at 2026-11-26T14:09:16Z, before any outcome of either entry was computed; the hash recorded at hashing time is kept privately, because the original holds exact creator counts that the public files print as bands (step-1 decision 49 item i). Redactions, marked [redacted: ...]: the SHA-256 of r3-P38's original prespecification. Nothing else differs. -->

# r3-P40 / r4-P25 (passed prophesied years against control years): prespecification

Written 2026-11-26 from 14:07:46Z (UTC, from `date -u`) by the step-3 agent for r3-P38 and r3-P40, a model agent
working for the project lead (not a person). Section 0 of `../r3-P38/prespec.md` (SHA-256 [redacted: kept privately]) binds this
entry: tier L, reads, placement, statistics, readings and privacy. What was known when both files were written is
listed there. This file is hashed with it, before any outcome of either entry is computed.

Exploratory; not a test of H1-H10. Cue counts: sense not resolved, precision unknown (no reader). TIME's roles are
model-coded and not checked by a person. Only "the first matching cue family" is printed, never a frame. No date is said
to have failed.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 2. r3-P40 / r4-P25

1. **Year mentions.** A token of r3-P42's extract equal to a four-digit year from 1800 to 2099 (after G1a's spoken-year
   normalisation by the shared matcher), with its spoken form read from the transcript: **digits**, **words** (converted
   by G1a), or **number** (digits with a separator, such as a thousands comma: not a year, left out). Each mention has
   its creator, recording, voice side (claimed, own, or outside the frozen primary definition), its position in its token
   sequence (one recording's run of units on one voice side), and the recording's upload year (TL-BUILD).
2. **Roles** (deposit 4), for passed mentions only (0.3):
   - **class 1**: 2012 (primary), 1987, 1999, 2000, 2003, 2011 (secondary);
   - **class 2, family A** (primary control): 2001, 2008; **family B** (second control family): 2020;
   - **class 3** (ordinary years, den-meth's match): a passed mention of a year that is not listed in deposit 4 and not
     within 2 years of a class-1 year, matched to at least one class-1 mention of the same creator, the same spoken form
     and the same voice side (outside-the-definition counts as its own side), with |d3 - d1| <= 1, where d is the upload
     year minus the named year. Sensitivity: |d3 - d1| <= 4, printed only if fewer than 5 creators hold a class-3
     mention under the first rule;
   - **reference rows**: (a) biographical: passed mentions of years outside classes 1 and 2 and other than 1844 and
     1954 whose TIME small-model role is "biography" (model-coded; the role is assigned only where TIME's hits line up,
     0.2 item 6); (b) 1844 and 1954: described only;
   - **ledger statements whose target had passed at upload** (0.3): described only, with the first matching cue family
     among L15 hits inside the statement's units.
3. **Cue families.** L15's counted hits (FULFIL, SPLIT, DEFER) by `Lexicon.match` on each token sequence. A hit
   belongs to a mention at position j if hit start - 30 <= j < hit end + 30 and j lies outside the hit (the matcher's own
   window arithmetic). The hits counted by the matcher with every year from 1800 to 2099 passed as target years must equal
   the hits that belong to at least one mention or A6 variant (a check; a difference stops the run). **Ordered
   classification**: FULFIL, then SPLIT, then DEFER (the programme's order: fulfilment, timeline split, deferral). A
   mention's first matching cue family is the first of these with a hit in its window; else "no cue family".
4. **Thin rule** (0.4): each cue family, and the pooled set of the three, is computed only if 3 or more of its forms
   are each used by 5 or more creators inside the windows of passed class-1, class-2, class-3 and biographical
   mentions (all voices). A thin family gets no segment of its own; its mentions still count in the pooled "any cue
   family" share if the pooled set is computed. If the pooled set is thin, every cue row prints "not computed (too few
   terms or creators)"; the memory timeline is still drawn.
5. **Rows.** Classes 1 (all six years; 2012 alone), 2A, 2B, 3 (and its sensitivity if used), biographical reference,
   1844 and 1954, and passed ledger statements; voices: all; claimed and own on the 11 voice-eligible creators (r3-P42's
   set). Per row: the creator-balanced share of mentions with any cue family (the mean, over creators with 1 or more
   mention in the row, of each creator's share) and its split by first matching cue family (computed families only),
   each with a 90% creator-bootstrap percentile interval (B = 1,000; seed ("r3-P40", "rows")). **Withdrawal**: a row with
   fewer than 5 creators holding a mention with a classified cue family prints "not printed (fewer than 5 creators with a
   classified cue family)".
6. **Contrasts (the readings).** D_A = S(class 1) - S(class 2A) and D_B = S(class 1) - S(class 2B), all voices, S the
   creator-balanced any-cue share of item 5; unpaired (each class over its own creators); the interval is a creator-cluster
   bootstrap percentile (the 23 creators resampled with replacement, B = 1,000, seed ("r3-P40", "contrast"); a draw in
   which either class has no creator is redrawn), fixed in advance and flagged "interval class not calibrated by
   r3-P30". Margin 0.05; no deposited direction: words of 0.4. **Holm across the two control families** (deposit 4):
   each family is first read on its 95% interval; if either family then reads "beyond the margin" or "within the margin
   (B)", the other is read on its 90% interval; otherwise both readings stay at 95%. **Named control row**: D_3 =
   S(class 1) - S(class 3); a reading beyond the margin also needs D_3's estimate on the same side. **Checks**: C2 over
   the pooled set's forms; **A1**: the same contrasts without the forms of deposit 3's public rule-coder collision table
   (a reading that holds only with them reads "not separable from the ledger's coded families"); **A6**: the same
   contrasts with r3-P42's six spoken-year variant forms (for 1844, 1954 and 1987) added as mentions ("undetermined
   (spoken-year variants)" if the reading changes); **r3-P42's band check**: whether S(class 1) lies inside the 90%
   bootstrap band of each control family's S ("no excess at target years" if inside), printed beside. A contrast needs
   5 or more creators with a classified cue family in each of its two classes; else it is withdrawn. By-voice contrasts
   are not read.
7. **Memory timeline** (years named by role). Creator-balanced mentions per 100,000 tokens (the mean over the 23
   creators of each creator's rate, all voices): one bar per listed year (class 1, family A, family B, 1844 and 1954)
   and decade bins for other passed years and for years open at upload. A bar is drawn only if 5 or more creators name a
   year of that role in it. No creator count is printed per bar.
8. **Plot**: the memory timeline beside stacked cue shares (first matching cue family) for class 1, class 2 (families A
   and B) and class 3, by voice (all, claimed, own), withdrawn rows marked.
9. **Predictions**: the account-prediction cells of r3-P40 and r4-P25 are silent in every column; nothing is scored.
10. **Order**: as `../r3-P38/prespec.md` section 1 item 10.
