# r3-P14: read aloud, recited or spontaneous? The text part (prespecification)

Written 2026-11-26 from 14:07:22Z (UTC, from `date -u`) by the step-5 agent (a model agent working for the project lead;
not a person), before any outcome of this entry was computed. Shared rules: `../common/prespec-common.md`. Class a.1 for
the text part. The self-described attribution uses r3-P53's mode cues (step 2). The acoustic part (a.2), two public
calibration corpora (class b) and listening (class c) are not run.

**Tier.** The text score has a data-tuned part (its standardisation constants), and 10 to 19 non-development creators are
eligible (the 11 voice-eligible creators, r3-P42's set; eligibility from word counts only): **tier X**, two-fold
cross-fitting (section 0.4 of the shared file). The attribution counts deposit 3's L10: **tier L**.

**Exploratory; not a test of H1-H10.** Voice labels model-coded, not checked by a person. Public name of the attribution:
"received text read aloud, self-described"; of the score: "read-like delivery profile" (text features only). The score is
never printed per creator, never read as a synthetic-voice screen, and never worded "scripted" or "not live". Reading a
received text aloud is, in emic's reading (a reading by a non-holder), a respected mode.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Units

The 11 voice-eligible non-development creators; claimed voice and own voice under the primary definition, units outside
H1's excluded formats. Guided practice (claimed-voice and own-voice units of guided-practice recordings) as a third and
fourth group where 5 or more of the 11 hold 300 or more words in it (the outcome-free count is below 5 for both:
"not computed (too few terms or creators)").

## 2. Text features (lexical, punctuation-free, lower-cased; recognizer word times)

- **Pause events**: gaps of 1 s or more between consecutive words of the same voice side in one run (seam rule: a gap
  under 5 s containing a multiple of 30 s is dropped).
- **Slots** (ling's clause-slot rule, round 3 Q1, as closed lists written now): the gap before word i is
  - **W, inside a phrase**, if word i-1 is a determiner or possessive {the, a, an, my, your, his, its, our, their, every,
    each, another}, or a preposition {of, in, on, at, for, with, from, by, into, onto, upon, about, through, between,
    among, within, without, under, toward, towards, during, across, against, behind, beyond, beneath}, or a modal
    {can, could, will, would, shall, should, may, might, must} while word i is not a pronoun {i, me, you, he, him, she,
    her, it, we, us, they, them};
  - otherwise **B, a clause-boundary candidate**, if word i is a subordinator {because, although, unless, whereas, if,
    when, until, whenever, whether} or a wh-relative {which, who, whose, where}, or a coordinator {and, but, or, so, yet}
    or discourse marker {now, well, okay} while word i+1 is a subject pronoun or existential there {i, you, he, she, it,
    we, they, there};
  - otherwise **A** (ambiguous; its share is printed and never used). Archaic forms take no slot of their own.
- **Within-phrase pause share** per creator and voice: (W + 0.5) / (W + B + 1) (Jeffreys-smoothed, so it is defined for
  every creator).
- **Repair rate** per creator and voice: lexical repairs per 1,000 words: immediate one-word repetitions (a word equal to
  the word before it, both alphabetic, in one run; "had had" and "that that" excepted) plus two-word repetitions (words
  i-2, i-1 equal to words i, i+1, all alphabetic, in one run). Self-repair phrases are not counted (their senses are not
  resolved without a reader); fillers are not part of the score.
- **Score** (read-like delivery profile; higher: more within-phrase pausing and more repairs): the mean of z(logit of the
  within-phrase pause share) and z(log of (repair rate + 0.5)), each z formed with the fitting side's constants (mean and
  SD over the fitting side's creator values, claimed and own values of each fitting creator pooled). Fitting side
  creators: half A or B with T, each with 1,000 or more words on each voice side (word counts only).
- **Score difference** per reading creator: claimed minus own.

## 3. Rows, intervals and readings

| Row | Statistic | Class (r3-P30) | Margin |
|---|---|---|---|
| S (primary) | cross-fitted score difference, claimed minus own | C_standardised (at 11: no method holds, so at most "undetermined") | 0.20 |
| W | within-phrase pause share difference, claimed minus own | B_share_difference | 0.05 |
| R | repair rate, log ratio claimed over own (0.5 added; counts summed within creator) | H_rare_counts | 0.223 |
| A-share | share of pause events in A slots, by voice | described | - |
| G | guided-practice groups | - | "not computed (too few terms or creators)" |
| Attribution | creators who describe their practice as received text read aloud (L10 MODE-READALOUD) | tier L | "not computed (too few terms or creators)" (step 2) |

- Words: S: "beyond the margin (claimed voice lower on the read-like delivery profile score: fewer within-phrase pauses
  and repairs)", "beyond the margin (claimed voice higher on the score)", "within the margin (B)", "undetermined". W and R:
  "beyond the margin (claimed higher)", "beyond the margin (claimed lower)", "within the margin (B)", "undetermined".
- The poles are not named: no reference corpus anchors the score here (the calibration corpora are class b). The known-
  groups check (page-matched spans against conversations) is not in the programme's text part and is not run.
- Plot: within-phrase pause share and repair rate for claimed voice and own voice (creator-balanced means with intervals;
  guided practice not computed), and a histogram of the score difference with bins of 5 or more creators (step 2's rule,
  bin width 0.5 over -3 to 3).
- Predictions deposited: none (deposit 2's cells for r3-P14 are silent). Nothing is scored.

## 4. Not run

The acoustic part (audio, later); the calibration corpora (class b); listening (class c); position matching (r3-P04's
references are not rebuilt for these features; a departure, stated).
