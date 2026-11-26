# r4-P14: archaic agreement in the transcripts (prespecification)

Written 2026-11-26 from 14:07:22Z (UTC, from `date -u`) by the step-5 agent (a model agent working for the project lead;
not a person), before any outcome of this entry was computed. Shared rules: `../common/prespec-common.md`. Class a.1;
another recognizer family is a.2 (package ruling) and a listening check is class c; neither runs.

**Tier X** by count (the 11 voice-eligible non-development creators; eligibility from word counts only). The rule below
has no data-tuned part, so the two folds apply the same rule and the cross-fit is the identity; the reading is made once
on the 11. It counts step 1's archaic closed list (r3-P01, hashed with its tolerance arm), not a deposit-3 list, so it is
not tier L.

**Exploratory; not a test of H1-H10.** The recognizer is a grammar prior: it may regularise the very agreement at issue,
so only presence and the transcribed pattern are read (N12). Neutral wording only: "historical agreement pattern",
"non-historical agreement pattern", never a pejorative word.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Forms and patterns (written now from general descriptions of Early Modern English agreement, blind to the corpus)

Archaic forms: r3-P01's closed list of 30 (thee, thou, thy, thine, thyself, ye, hath, doth, dost, hast, shalt, canst,
couldst, wouldst, shouldst, mayst, mightst, didst, hadst, wast, wert, unto, hither, thither, whither, whence, thence,
wherefore, ere, verily). Agreement is read on adjacent plain tokens of one voice run:
- **thou + verb** (verb = the next token): historical if the verb is a second-person singular form {art, wast, wert,
  hast, hadst, dost, didst, shalt, wilt, canst, couldst, wouldst, shouldst, mayst, mightst, must}; non-historical if it is
  a form of another person or number {am, is, are, was, were, has, have, hath, does, do, doth, did, will, shall, can,
  could, would, should, may, might}; else not classified.
- **verb + thou** (inversion, the previous token): the same verb sets, read the same way.
- **ye + verb**: historical with a plural or base form {are, were, have, had, do, did, shall, will, can, could, would,
  should, may, might, must, be}; non-historical with {art, wast, wert, hast, hadst, dost, didst, shalt, canst, is, was,
  has, hath, does, doth, am}.
- **thee + finite verb** (thee in subject position, the next token a finite verb from either set above): the
  "object form in subject position" pattern, counted as non-historical; thee followed by anything else: not classified.
- **hath, doth** with the previous token as subject: historical with {he, she, it, this, that, one, who, which}; non-
  historical with {i, you, we, they, thou, ye}; otherwise (a noun or nothing) not classified.
- **-st and second-person verb forms** {art, hast, dost, shalt, wilt, canst, wast, wert, couldst, wouldst, shouldst,
  mayst, mightst, didst, hadst} with the previous token as subject: historical with thou; non-historical with {i, you,
  we, they, he, she, it, ye}; otherwise not classified (inversion with thou after the verb is historical).
Each classified pair counts once.

## 2. Rows (per creator and voice side: claimed voice and own voice, primary definition, units outside H1's excluded formats)

| Row | Statistic | Class (r3-P30) | Margin |
|---|---|---|---|
| R1 presence | share of the 11 with at least one archaic form, by voice, and the difference (paired) | B_share_difference | 0.05 |
| R2 rate | archaic forms per 10,000 words, log ratio claimed over own (0.5 added, counts summed within creator) | H_rare_counts | 0.223 |
| R3 agreement (the transcribed pattern) | per voice, the creator-balanced share of non-historical among classified pairs, over creators with a classified pair; binned over creators | described | - |
| R4 decode strip | on rv-R3's bridge recordings of the 11: archaic forms and classified pairs under the record decode and the larger model (nearest-word voice) | described | - |
| R5 control strip | the same statistics on own voice (the control), printed beside the claimed voice | described | - |

- A value non-zero for fewer than 5 creators of its base prints "not printed (fewer than 5 creators carry the estimate)";
  agreement shares need 5 or more creators with classified pairs per voice, else "not computed (too few terms or
  creators)". No form is named with a count on fewer than 5 creators.
- Words for R1 and R2: "beyond the margin (claimed higher)", "beyond the margin (claimed lower)", "within the margin (B)",
  "undetermined". R3 to R5 are described only: presence and the transcribed pattern, never what was said.
- Predictions deposited: none (deposit 2's cells for r4-P14 are silent). Nothing is scored.

## 3. Plot

Binned agreement shares over creators (bins of 5 or more creators) for the claimed voice beside the own-voice and decode
control strips; where the bins cannot be filled, a status panel.
