# Prespecification: r4-P23 (the contact class in the frozen ledger)

Written 2026-11-26 between 14:09:41 and 14:11:29 UTC (both from `date -u`; the second is the first hashing; corrected and hashed again below) by a step-3 agent (a model agent working for the project lead; not a
person), before any outcome of this entry was computed. Its SHA-256 and the time of hashing are in
`prespec-hash-record.md`. Exploratory; not a test of H1-H10. No model or API call, no download.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Programme.** `programme.md` 2.1 step 3, r4-P23 (a.1 as cue strata inside the ledger: r3-P36's strata, no member-written
list); its class-b card b8 (et's registered prediction, for fresh creators); N22; deposit 2 (margins, account cells,
split policy); the lead's common rules. The rival reading the corpus supports so far is that the format sets the window.
Nothing is resolved or scored as come true; no statement is called "failed".

## 0. What was seen before this file

The release's TL-BUILD, TL-7.7 and TL-7.9 headlines; et's round-4 memo (et-n3), which cites TL-BUILD's figure "by
announced source" as showing little difference in bounded share between sources; deposits 1 to 4; the frozen ledger's
field structure (one closed-window row's fields, text redacted, contact class "world event"); outcome-free counts
(`../ft-common/code/eligibility.py`, SHA-256 `d31d2f48...3763c`): per non-development creator, the number of statements in
the contact class and in the world-event class. No bounded share was computed.

## 1. Data, classes and tier

- **Statements:** every row of the frozen ledger (SHA-256 `d2e8e3fd...a80a`, checked before use): kept, model-coded
  world-future statement candidates (LAB-F, TL-BUILD), bounded and unbounded.
- **Strata** (r3-P36's strata, as the ledger's frozen rule coder holds them; deposit 2): the contact class is any of et's
  five strata (contact event, intervention, evacuation, technology release, institutional disclosure); every other
  statement is "world event". Rule-based, not checked by a person; precision and recall unknown.
- **Tier L** (the lead's common rules: an entry that counts the ledger's frozen rule coder): once on the 23
  non-development creators, no split.
- **Eligible creators** (outcome-free): 5 or more statements in each class. Their count is "5 to 9" (printed so).

## 2. Primary, rows, intervals and readings

- **Bounded** (the coder's own input, which sets class NU): a closed window. **Primary:** per eligible creator, the
  bounded share of contact-class statements minus the bounded share of world-event statements; the creator mean.
- **Margin:** deposit 2's difference in shares, 5 points (0.05). **Named direction:** negative (et: contact statements
  bounded less often).
- **Interval:** 90% t interval on creator values, a fixed method. r3-P30's closest class (B1, one difference in shares
  per creator) chooses by count (creator bootstrap-t at 5 to 7 creators, the t interval at 8 or more); the count here
  is printed as a band, so a count-chosen method would be withheld (decision 62). The t interval is fixed instead; in
  r3-P30's B1 grid it over-covers at 5 creators (0.92). Flagged "interval fixed in advance; r3-P30's class B1 would choose
  by count".
- **Readings** (deposit 2): **A** if the interval lies wholly below -0.05; **B** if wholly inside -0.05 to +0.05;
  "beyond the margin, opposite to the named direction" if wholly above +0.05; otherwise **undetermined**; "not computed"
  with fewer than 5 eligible creators.
- **Rows** (same interval and reading rule, each a row, not a primary; rows 1 and 2 keep the eligibility rule, 5 or more
  statements in each class, recomputed on the row's own statements):
  1. "dated" (any bounded time expression, open or closed) in place of a closed window;
  2. date refusals (flag D) and energetic-only statements left out of both classes (N22: "kept out of scoring");
  3. the rival (the format sets the window): among bounded statements, the share whose window rests on the talk-level
     period alone, contact minus world event, for eligible creators with a bounded statement in each class
     (description; no direction named, so an interval wholly beyond the margin reads "beyond the margin (direction not
     named in advance)");
  4. the registered second half (b8): among bounded statements, the share with an energetic predicate (rule class NE or
     M), contact minus world event, for creators with 5 or more bounded statements in each class.
- **Description by stratum:** creator-balanced shares of the rule-based resolvability classes (R, NE, NU, M, NX) and of
  flags C and D, for the contact class, each of the five contact strata and the world-event class, over the creators with
  a statement in the stratum; a stratum on fewer than 5 creators prints "fewer than 5 creators"; class cells resting on
  fewer than 5 creators are pooled into "other classes (pooled for privacy)", and a stratum whose pooled cell still rests
  on fewer than 5 is not printed.

## 3. Prediction scored (deposit 2's account cells)

Platform-format account, r4-P23: "flat: contact and world-event statements bounded alike". Scored on the primary
reading: B "as predicted"; A or "beyond the margin, opposite" "not as predicted"; undetermined "not decided by this
reading". et's registered prediction (b8) is for fresh creators and is not scored here; its seen direction is described
only.

## 4. Privacy and plots

- The lead's common rules and step 1's `pubrules.Register` (copied with its hash); no per-creator values; with fewer than
  10 eligible creators a histogram with bins of 5 or more creators would hold at most one bin, so the programme's
  histogram is not drawn and the creator-level interval with the smallest-effect band is shown instead ("never one dot
  pair per creator").
- `fig-r4-P23-contact`: left, the primary and rows 1 to 4 (estimate and 90% interval) against the margin band; right,
  the creator-balanced stacked resolvability classes by stratum.
- 56 primaries; deposit 2's half-effect disclosure printed.
