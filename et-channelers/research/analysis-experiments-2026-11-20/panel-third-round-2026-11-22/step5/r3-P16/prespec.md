# r3-P16: who shifts? Register shift by self-described mode (prespecification)

Written 2026-11-26 from 14:07:22Z (UTC, from `date -u`) by the step-5 agent (a model agent working for the project lead;
not a person), before any outcome of this entry was computed. Shared rules: `../common/prespec-common.md`. Class a.2 (its
mode groups come from r3-P53's cue part, after ruling 11); the delivery rows need audio and are not computed here (audio,
later).

**Tier L**: the mode groups count deposit 3's L10 through the shared matcher; run once on the 23 non-development
creators, no split; the shift needs both voices and is computed on the 11 voice-eligible creators.

**Exploratory; not a test of H1-H10; description only.** Every account predicts the same dose (D23), so this retires
none; only a flat or reversed ordering would inform, and the expected reading is "undetermined". Wording: "creators who
describe their practice as X". Mode is self-presentation, from cue counts (sense not resolved, precision unknown). Voice
labels model-coded, not checked by a person.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Mode groups (as r3-P53 built them)

L10's classes through `lexmatch` on r3-P42's extract (any voice); a creator is in mode group X with 2 or more cue hits of
X. Only the two classes step 2 computed under the thin rule enter: MODE-HIGHERSELF ("higher self or Source") and
MODE-RELAY ("relay"). The six others print "not computed (too few terms or creators)" (step 2). The groups are recomputed
and must equal r3-P53's (a difference stops the run).

## 2. The shift (per voice-eligible creator)

r3-P15's profile machinery (person-free and full function-word profiles, parts of 200 usable tokens, 20 draws, formula
tokens removed), on pooled parts: the creator's claimed tokens and own tokens under the primary definition (units outside
H1's excluded formats), each in recording then time order and cut into halves. OO = d(own 1, own 2); CO = mean of
d(claimed 1, own 2) and d(claimed 2, own 1). **Standardised shift** S = (CO - OO) / SD, SD the between-creator SD of OO
over the 11. z-scoring over the 11 creators' parts in each draw (primary: person-free, z-scored; the unstandardised
variant printed beside). The **noise band** is the margin: a creator "does not shift" when S is below 0.20.

## 3. Rows

| Row | Statistic | Interval | Words |
|---|---|---|---|
| U1 | mean S over the 11 | C_standardised at 11 (no method holds: at most "undetermined") | "beyond the margin (claimed farther than own-own)", "within the margin (B)", "undetermined" |
| U2 | creators of the 11 who do not shift (S below 0.20) | count form only | described |
| U3 by group | for each computed mode: the mode group within the 11 and the other creators within the 11; mean S per group and the group difference (group minus others) | Welch t, 90% (a between-group difference of creator means; "interval class not calibrated by r3-P30") | "beyond the margin (the group shifts more)", "beyond the margin (the group shifts less)", "within the margin (B)", "undetermined" |
| U4 | creators who do not shift, by group | count form only | described |
| Delivery | rate and pauses by mode | - | "not computed here (audio, later)" |

- A group comparison is computed only if both groups within the 11 hold 5 or more creators and both counts print exactly;
  otherwise "not computed (too few terms or creators)" or "not printed (a group's count is not printed exactly)". Group
  means are printed only where both group counts print exactly.
- Distribution plot over the 11 (bins of 5 or more creators, step 2's rule, width 0.5 over -3 to 3) with the noise band;
  group means where printable; the share of creators who do not shift as its count form.
- **Predictions** (deposit 2's cells for r3-P16: every account "same as every other account (direction not stated)"):
  scored as "no account is retired, whatever the result (D23)". Nothing else is scored.
