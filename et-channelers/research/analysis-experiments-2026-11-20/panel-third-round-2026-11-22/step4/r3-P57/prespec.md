# r3-P57 / r4-P32: sample-to-offer congruence (prespecification)

Written 2026-11-26 (UTC, from `date -u`; the hash time is in `prespec-hash-record.md`) by the step-4 agent, a model agent
working for the project lead (not a person), before any outcome of this entry was computed. Shared rules:
`../common/prespec-shared.md` (cited by SHA-256 in the hash record). r4-P32 is carried here (programme 2.5).

Exploratory; a description on seen creators, worded "a funnel, whatever its age", "offers, not income" and "in this
platform-surviving roster". The public title stays neutral ("sample-to-offer congruence"). Voice, kind and asks labels
are model-coded and not checked by a person. Confirmation is class b (card b6, fresh creators).

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Units and tier

- **Recordings.** Seen recordings of the eligible creators that carry an asks label file. **Claimed-voice recordings**:
  the voice map's main kind "claimed voice" (small model, the production map; LAB-K). **Own-voice talks**: main kind
  "own-voice talk". Other kinds (conversation, guided practice, promotion, reading, mixed, unclear) are left out, as
  round 3's method sets promotion and conversation aside.
- **Eligible creators** (outcome-free): 1 or more recordings of each kind. Among the 23 non-development creators the
  count lies in **10 to 19: tier X** (two-fold cross-fitting over halves A and B; no parameter is fitted, so the
  cross-fitted estimate is the pooled estimate of the fixed rules over the eligible creators of both folds; fold-level
  values are not printed). The eligible count prints in the form `Counts` gives it.
- **Asks** (CSS's seen-only extract of the frozen asks instrument, label of record, final asks): any final ask of class
  K1 pay-or-enrol, K3 platform, K4 off-platform, K2 money gifts with K5 third-party adverts (pooled, as LAB-A pools them),
  and any ask. Recording level: a recording "carries" a class if one final ask of that class is in it, in any voice.
- **Offers.** The object of each K1 ask (session, event or course, membership, product, several, unclear). **Client
  service** = "session" (sessions or readings; CSS-10's client offer). A recording's offer is congruent when one of its
  K1 asks has the object "session".

## 2. Primaries (b6's prediction, read on seen creators as a description)

- **P1, the ask half.** The within-creator Mantel-Haenszel odds ratio of a K1 ask, claimed-voice recordings against
  own-voice talks, stratified by creator and within-creator length tertile (round 3's method; tertiles of the creator's
  eligible recordings' durations, one stratum where a creator has fewer than 3). Second estimator: the MH odds ratio by
  creator only. Interval: creator-cluster percentile bootstrap, B = 2,000, 90% (a fixed method; interval class not
  calibrated by r3-P30). Round 3's creator-level t interval on per-creator log odds ratios would be r3-P30's class G,
  whose method is chosen by the count; with this entry's banded eligible count it is not printed (decision 62).
  **b6's rule**: supported (non-inferiority at 0.8) when the lower 90% bound lies above 0.8; den-soc's retirement
  condition for the ask half when the upper bound lies below 0.8 and the congruence half shows no congruence (P2 not
  supported); otherwise undetermined. If the two estimators give different words: undetermined.
- **P2, the congruence half.** Over creators with 1 or more K1-ask recordings of each kind: the creator-balanced share of
  K1-ask recordings whose offer is client service, claimed-voice against own-voice; the ratio of the two creator-balanced
  shares, with a creator-cluster percentile bootstrap (B = 2,000, 90%; fixed method). **b6's rule** (deposit 2's words,
  named direction claimed higher): supported (A) when the interval lies wholly above 1.25; den-soc's retirement rule
  (equivalent: B) when it lies inside 0.8 to 1.25; otherwise undetermined. Fewer than 5 creators: not computed. An own-
  voice share of 0 makes the ratio undefined: "not computed (no client-service offer in own-voice talks)".
- **The prediction** (deposit 2's account cell, business account: "as b6, read on seen creators as a description") is
  scored as these two rules give it, never changed after the result.

## 3. Described rows (no reading of their own beyond the margin words)

- Creator-balanced shares of recordings carrying each ask class (K1, K3, K4, K2 with K5, any ask), claimed-voice
  recordings and own-voice talks, and the creator-balanced difference (claimed minus own) with a creator-cluster
  percentile bootstrap (B = 2,000, 90%; fixed method; interval class not calibrated by r3-P30); margin 0.05; words
  "beyond the margin (claimed higher / own higher)", "within the margin (B)", "undetermined".
- Sensitivity rows for P1 and P2: (a) share-based classes: 25% or more of the recording's words in a claimed voice (small
  model, rule B, V2 + V3; LAB-K's threshold) against recordings with no claimed-voice word, on the creators with both
  (count printed by `Counts`); (b) the "several" object counted as client service (a bracket, meas); (c) client service on
  either evidence: a session object or a written booking cue or link on the recording's page (PT part (a); page
  templates repeat across a channel, so this row leans toward a ratio of 1).
- Creator-balanced mean log10 duration difference (claimed minus own), described, as a covariate.

## 4. Plot

Paired bars: creator-balanced shares of recordings with an ask by class, claimed-voice recordings against own-voice
talks (with the bootstrap interval of each difference beside them); a paired bar of the client-service share of offers
(P2); the b6 scorecard as text. No per-creator point.

## 5. Consistency checks

Against LAB-A (spoken pay-or-enrol asks in about four in ten of a creator's recordings, all seen recordings), r3-P05
(pay-or-enrol asks rarer in the claimed voice than position predicts: a span-level result, which this recording-level
description does not contradict if claimed-voice recordings carry own-voice asks) and r3-P56 (pay asks per hour lower in
the claimed voice). Differences of unit are stated, not reconciled after the fact.
