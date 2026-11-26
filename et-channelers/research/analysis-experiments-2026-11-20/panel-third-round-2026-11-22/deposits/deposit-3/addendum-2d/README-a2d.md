# Addendum 2d: the "thin class" rule corrected, and one term set aside (decision 60)

Written 2026-11-26 from 11:01 UTC (from `date -u`) by the step-2 cross-reviewer, a model agent working for the project
lead (not a person).

**Written from the literature only, blind to the corpus; no count has been made.**

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. A correction of r3-P42's prespecification, section 3, made before any count

The hashed prespecification (`r3-P42/prespec.md`, section 3, the thin rule) says that "a class, layer, part or balance
side with fewer than 3 terms used by 5 or more creators reads 'not computed (too few terms)'". The file is not edited.
Read literally, the rule marked most classes that the register writes as a single row (one row holding many forms)
"not computed", whatever the data. Its evident purpose was to stop readings that rest on too few distinct terms.

**Correction (decision 60 item 1).** In the thin rule, "term" means:
- a register row for L01's layers, the composition parts, balance sides and L02's pairs;
- an expanded form for every other list's classes.

A class of those other lists with fewer than 3 expanded forms used by 5 or more creators reads "not computed (too few
terms)". Every other part of the prespecification stands. This correction was dated and hashed before any data was
read.

**Classes affected.** These 51 classes would have read "not computed" under the literal wording, and are computed
under the correction if their forms meet the floor. Rows and forms per class are in `thin-rule-classes-a2d.csv`.

| List | Classes |
|---|---|
| L03 | DIM |
| L05 | ADV-AMB, CR-D |
| L07 | INST-CORP, INST-GOV, INST-MEDIA, INST-RELIG, LEGAL |
| L08 | RES-INNER, RES-OUTSIDE |
| L09 | FP-PL, FP-SG |
| L10 | MODE-CONSCIOUS, MODE-DICTATION, MODE-HIGHERSELF, MODE-READALOUD, MODE-RECITATION, MODE-RELAY, MODE-TRANCE |
| L11 | ENDORSE |
| L12 | DISSEM, IDIOM |
| L13 | DEST-ALTVID, DEST-AUDIO, DEST-EMAIL, DEST-MEMB, DEST-MSG, DEST-SERVICE, DEST-SHOP, DEST-SOCIAL, DEST-UNRESOLVED, SUPP-HIDDEN, SUPP-PLATFORM |
| L14 | AUTHORITY-C, COMMIT-C, COMMIT-D, DISCOUNT-C, GUARANTEE-C, PRICE, RECIP-C, RECIP-D, SCARCITY-C, SCARCITY-D, SOCIAL-C, SOCIAL-D, UNITY-D, URGENCY-C, URGENCY-D |
| L15 | DEFER, FULFIL, SPLIT |

**Classes thin by design under either reading** (fewer than 3 counted forms; they read "not computed (too few terms)"):

| List | Classes |
|---|---|
| L05 | BRIDGE, CR-E |
| L07 | DISC-CONSC, INST-SPACE |
| L10 | MODE-LIGHTLANG |
| L11 | REF-CREATOR |
| L13 | DEST-LINKHUB, DEST-SELF |

L03's DEN class has no counted term left after the set-asides.

## 2. T070 (photon belt) set aside

Its only source was found not to support it (addendum 2, A2-009 and A2-101). The writer's standard is that a term
without a supporting source is not counted. T070 is set aside from every count, and returns if a supporting source is
cited (decision 60 item 2). The affected files are regenerated as "-a2d" in `lists/`, beside the crosswalk and the
balance file.

**Which version binds.** For each list, the "-a2d" file binds if there is one, then "-a2c", then "-a2b", then "-a2", then
the original.
