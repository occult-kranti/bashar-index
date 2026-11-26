# HOLD: hold-out passes of the exploratory reporting plan

Exploratory (registry A2); not a test of H1-H10. Every output here was run after freeze 2 (2026-11-21 16:10:00 UTC) and
after the registered first-round tests, by code written after freeze 2. That departs from the plan's "code frozen in the
freeze-2 record" (sections 5 and 8) and is stated in each status entry. Each hold-out run was made after the same code
ran on the seen creators, and is logged as a hold-out contact (a second run of a changed driver is logged as a repeat
contact). Hold-out results are printed beside the seen results and never pooled with them (plan section 5, rule 4).

**Balance table.** The hold-out is the tail of an English-first run and is not exchangeable with the seen creators, so
read every hold-out column beside the balance table: rv-D2 (the paper review's ledger and inventory table) and its
transcript part on the hold-out, rv-D2-H (package HOLD2: `rv-D2-H-transcript-covariates.csv`, `rv-D2-H-sentences.csv`, and the gallery figure of the love
plot). In short: the hold-out's English recordings have fewer recognized words per minute inside the
recognizer's segments (a recognizer-output measure, not a direct measure of speaking), carry lower recognizer
confidence, and have more time before the first and after the last recognized segment than the seen creators'
recordings (time outside recognized segments is not the same as silence); for these covariates the 90% interval of the standardised difference lies away from zero.

**Public form** (plan section 3 and the round's rules): distributions and creator-level aggregates only.

- No cell rests on fewer than 5 creators with a non-zero value, or on a complement of fewer than 5.
- Categories under 5 creators are pooled into "other", decided on all columns of a display together.
- A creator count is not printed where it would lie 1 to 4 from the count of a group it may be nested in (including
  the public counts 23, 18, 17 and 6 of the hold-out). It then reads "all but fewer than 5 of N" or "5 or more".
- **Pair rule.** A cell whose per-creator values differ from those of a printed cell in 1 to 4 creators is not
  printed, because the difference of the two cells would rest on those creators. This holds between the two versions
  of ENTRY and between the rows of one display family in LAB-H.
- No minima or maxima: 10th and 90th percentiles instead.
- **Dominance.** A creator-balanced mean, share or share's complement is not printed where the printed mean,
  interval and creator count would show that one creator holds half or more of the summed creator values (rule
  added on 2026-11-22 after the results were seen, for privacy only; it hides values and chooses none).
- No names, codes, ids, titles, quotations, and no per-creator or per-recording rows.
- Every label is model-coded. Agreement figures are agreement, not a measure of correctness. Nothing was checked by a person.

## H3-X: H3 at the creator level on the hold-out (`h3x-creator-level.csv`)

H3 is closed (amendment A6). Nothing in this table is a verdict, and no p in it is a test of H3.

- **What was run.** The frozen H3 code (`h3_position.py`, artefact filter v1) made every recording's ten bins and its U.
  It reproduced the published registered row exactly on both groups. The creator-level rows come from the meta-review's
  MR-05 hold-out parts and V13:
  - the t interval on creator means;
  - the exact centre of the circular-shift reference: the mean U over the ten offsets of each recording, which needs no
    draws;
  - recentred U;
  - the exact creator sign-flip p over all 2^17 sign patterns (hold-out) or 199,999 draws (seen);
  - the 20% trimmed mean;
  - leave-one-creator-out stability;
  - the hold-out without its pilot-era recordings (V13). These are the hold-out audio files that were already in the run
    ledger at line 1,253, the point at which the first panel's pilot ran. They were found from ledger fields only.
- **Departures.**
  - The plan row's random-effects pool with the seen creators is not run, because hold-out results are never pooled with
    seen ones (plan section 5, rule 4). The hold-out-minus-seen difference is printed in its place. The lead confirmed
    this on 2026-11-22 (decision D1); addendum 3 records it as a correction of the plan row.
  - The leave-one-out range is given as sign stability only. With the creator count and the mean public, a numeric end
    of the range would give the most extreme creator's value.
  - The count of hold-out creators with a positive recentred U is not printed, because it lies 1 to 4 from the published
    count of creators with a positive U.
- **Reading.**
  - On the hold-out the shift reference's centre lies further below zero than on the seen creators. Recentring therefore
    moves the hold-out estimate more. This supersedes rv-R1's approximation, which used the seen creators' centre.
  - CAL found that the registered shift test over-rejects under a creator-level placebo, while the creator sign-flip on
    recentred U holds close to its nominal level. These are calibration facts, not a re-test.

## LAB-H: model-coded descriptions of the first-round labels on the hold-out (`lab-h-descriptions.csv`)

These are LAB-V, LAB-A, LAB-F, LAB-S, LAB-T and LAB-K on the hold-out creators (18 with English labels; titles for 23),
beside the seen creators. They are descriptions, apart from the registered tests.

- **Definitions.** The driver uses the LAB package's definitions. On the seen creators it reproduces the LAB package's
  published seen values, for example the claimed side, own voice, the bands, the voice of the asks, the weighted
  forecast rate, the F1 share and the title family row.
  - Voice: a creator's share pools the words of its recordings.
  - Bands: LAB-K's bands of a recording's claimed share.
  - Asks: overlapping asks of one class are counted once. The voice of an ask is the side that holds most of the
    words of its units (LAB-A, h6_asks).
  - Forecasts: weighted by the inverse inclusion probabilities. Read candidates are weighted by 1 / valve p,
    statements by 1 / candidate p, coded statements by 1 / inclusion p.
  - Titles: the family rows use the families named as a source. A family named as a source or as a topic is a
    separate row under its own name.
- **Intervals.** Values are creator-balanced means over creators, with 90% t intervals over creators, clipped to the
  range of a share. The 10th, 50th and 90th percentiles are given for the primary rows.
- **Voice: primaries and models.**
  - The registered primaries are printed first, with quantiles: the claimed side under rule B, and own voice under the
    primary definition (rule B, broad).
  - Rule A's claimed side and the other own-voice definitions (rule B strict, rule A broad, rule A strict) are
    robustness rows.
  - The codes table shows the codes under rule B.
  - Every voice-dependent display names its model in the column:
    - hold-out, middle model gpt-6.1-terra (the hold-out record);
    - hold-out, small model gpt-6-luna (beside; its stability on R-hold is below its floor);
    - seen, middle model on the middle-model subset (the seen comparison for voice, registry 02:53);
    - seen, small model on all seen recordings (the seen record, beside).
  - Voice-dependent displays are the voice shares, the claimed share within a format, the bands and the voice of the
    ask.
- **Verification.** Each row carries a `verification` column. It states which verification exists for that instrument
  and group, with figures, and "not checked by a person". The voice rows also say that the voice label responds to
  punctuation and case. Under these checks:
  - the forecast class of record fails gate D on R-hold, so the forecast rows rest on a class below its floor;
  - the sentence codes fail gate C on R-hold;
  - checkability and the title codes are below their floors and kept as records.
- **Withheld by the rules.**
  - The robustness rows and the rule-B code table of the middle-model columns, wherever they differ from a printed
    primary row in 1 to 4 creators. In the middle-model columns rule B moves the words of few creators, so most of
    these rows are withheld there.
  - Third-party adverts (K5).
  - Some per-class views of the voice of the ask.
  - The hold-out counts of creators without a 25% recording.
  - On the hold-out, the title family groups. Two groups rest on fewer than 5 creators. Pooling them needs the
    per-title family sets, which this run did not keep, so only "any source family" is printed there.
  - Seen counts other than the whole base read "5 or more". The LAB package's seen counts are of record.
  - The hold-out small-model column of the rule-B code table: one of its codes is dominated by fewer than 5
    creators, and the codes of a column sum to one, so the whole column is withheld.
- **Departures.**
  - LAB-S does not show cut units apart, because that needs the transcript text of the units.
  - The LAB-T hold-out base of 23 includes the titles of the hold-out creators whose recordings are mostly not in
    English. Every seen creator is English.
  - The seen columns are this package's computation. The seen descriptions of record are the LAB package's.

## ENTRY-H: when a channelled source enters, on the hold-out (`entry-h.csv`)

The table covers E4, E1, E3, E2 (position by tenth, with pointwise intervals and no family-wise control, and the
whole-recording rates) and T (family counts with the check precision). Everything is a cue count.

- **Versions.**
  - Version 1 (entry-patterns-v1, entry-rule-v1) is the version of record.
  - Version 2 was revised after the model check on seen creators and is a revision row. On the hold-out it meets text it
    was not revised on.
  - **Pair rule between the versions.** A version-2 cell, hit total or recording total is not printed if its
    per-creator values differ from version 1's in 1 to 4 creators. A version-2 creator count is phrased if it lies 1 to
    4 from version 1's count, or if its group differs from version 1's in 1 to 4 creators.
  - **Shared categories.** E4's bins and the families pooled into "other" are decided on both versions together. On
    the hold-out, most version-2 cells are withheld under this rule.
- **Precision.** The column `check_precision_v1` gives the model check of version 1 on seen creators, as ENTRY's family
  table prints it (model-coded, not checked by a person). The check found that most first-entrance cues are not where
  a source begins to speak.
- **Leave-one-out.** It is given as a statement, without numeric ends:
  - E4: whether every leave-one-creator-out mean stays inside the 90% interval;
  - E3: whether the sign of the mean survives leaving out any one creator.
- **Whole-recording rates (E2).** A rate is printed only where the family's withheld tenth cells rest together on 0 or
  5 or more creators. The whole rate is close to the mean of the ten tenth rates. The hold-out's version-1 rate of
  "self-introduction, we" is withheld: it is dominated by fewer than 5 creators.
- **Rates by tenth (E2).** A family's tenth row (one group, one version) is printed only when every one of its ten
  cells is printed. A row with a withheld or dominated cell is withheld as a whole, because a printed 0 beside a
  withheld cell would show in which tenths the hits of fewer than 5 creators lie. Tenths are not merged here, because
  merging needs the private counts. Every hold-out tenth row is withheld.
- **How it was run.** Hold-out transcripts were opened through prep after freeze 2 and built into a private word cache
  by ENTRY's frozen `build_cache()`. Each version's frozen `hits()` and `entrance()` ran through this package's
  collector, because ENTRY's own version-1 collector was replaced in place by version 2. On the seen creators the
  collector reproduced ENTRY's stored rows:
  - version 2 exactly;
  - version 1 exactly for entrances, and for family counts in 1,228 of 1,229 recordings.
- **Not shown for the hold-out.**
  - E1 by length third, because each third rests on fewer than 5 creators.
  - E2 by tenth of running time (every row; see above).
  - The version-2 supported tier, for the same reason.
  - The version-2 person split.
  - ENTRY-T's masked templates and I-against-we by source group, which need the matched text of hits.
  - Any model reading of hold-out hits: ENTRY-MC and a fresh ENTRY-V2 reading would need model calls, and no money is
    left under the hard stop (registry 2026-11-21 18:41).
- **E1 tiers.** E1 pools both version-2 tiers. ENTRY's seen primary for version 2 is the supported tier, so the seen E1
  rows here differ from ENTRY's published seen E1.

## E13: non-English creators on language-free timing (`e13-placements.csv`)

E13 is a stated count, not a test.

- **Who is placed.** The hold-out creators whose recordings are mostly not in English (5 or more creators; all are
  hold-out creators). Each is placed by the mean of its non-English recordings, against the 95% prediction interval
  for a new English (seen) creator.
- **Not placed.** A hold-out creator with one non-English recording among English ones is not one of the registered
  non-English creators and is not placed.
- **Measures used.** The bridge finds every pause, word-time and segment measure different between the two recognizer
  models, and the non-English recordings come from the larger model. So only two recognizer-independent measures are
  used:
  - speech share after voice activity detection. The bridge found speech seconds equal under both models in all pairs;
  - recording length.
- **Count base.** The registered count is restated for these two measures: each placement has a 5% chance of falling
  outside by chance. Neither the number of placements nor the expected count is printed (lead's decision D32).
- **Result.** No placement falls outside.

## Not run or not released in this package

These are listed in the release's status table (`status-table.csv`):

- **TL-H (not run).** The timeline procedure freeze, which the plan requires before the timeline's hold-out
  statements are read, was never made. The cards would also need model calls.
- **NONEN (not run).**
  - Its measure, the agreement of topic and source codes between the original and the English view, needs those codes
    on both views. That needs model calls.
  - The code-only paired counts of the language case panel were not run either: segment ratio, coverage, loops and
    names in each view. The paired views exist only for non-English hold-out recordings, so the code could not run on
    seen creators first. Its loop and name rules would also be fixed on hold-out text.
- **E4, hold-out part (not run).** Its condition is not met: H1 is not determinable on the hold-out.
- **E9, hold-out part (not released by this package; superseded, see `E9H/`).** Under H9's eligibility, which E9's
  seen run uses, fewer than 5 hold-out creators qualify. Its public form here was therefore "fewer than 5 creators".
  By the owner's order of 2026-11-22 02:22 UTC (registry), an exception to the small-cell rule for this one output, it
  was later computed and released by package E9H (`E9H/e9h-shared-runs-seen-and-holdout.csv`): E9's statistic is not
  computable on the hold-out creators.

_Pointer added on 2026-11-22 by the collector of the second wave (by hand, after the consistency scan of
the collector's collect_consistency_w2.py, sha256 1133519b3514737c; E9H's request): the E9 paragraph points to E9H's release; no number, count, row
or column changed._

_Wording edited on 2026-11-22 by fix1_apply.py (sha256 19199f9b5b8a47e2) under the lead's release-review decisions (registry 2026-11-22 02:09): the pace covariate is worded as a recognizer-output measure, and the creator with one non-English recording among English ones is described the same way throughout; no number, count, row or column changed, only wording (this line reworded on 2026-11-22 by fix1_apply2.py, sha256 9ba939ada52da07d)._

_Edited on 2026-11-22 (2026-11-22T05:15:07Z) by the plotting group X-HOLD's apply_d32.py (sha256 991fa748b6980548) under the lead's decisions D32 and D1: E13 and the LAB-T note describe the hold-out creators whose recordings are mostly not in English without a creator count, E13 prints neither the number of placements nor the expected count (its result is unchanged), and H3-X's departure (no pool with the seen creators) is marked as confirmed; no other number, count, row or column changed._

_Release fix of 2026-11-22 (2026-11-22T06:14:18Z) by the plotting group X-HOLD's apply_release_fixes.py (sha256 a5c389b3f05b1084), after the verifier's report, for privacy only: the dominance rule and the whole-row rule for E2 by tenth are applied to `entry-h.csv`; one column of LAB-H's rule-B code table is withheld; the balance-table sentence no longer calls the time outside recognized segments silence; provenance lines name scripts, not paths. Values were only withheld, never changed._

## Quantiles that could narrow a withheld count (release pass 2's fifth fix step (fix6), 2026-11-26)

Under the lead's decision D70, which extends D67, no quantile is printed in a row whose count of creators with a non-zero value is withheld or printed as a band, nor in a row where the quantiles alone could narrow such a count (to fewer than 5, to within 4 of the row's base or to within 4 of another printed count): quantiles were dropped where they could narrow a withheld count. Such rows print their means and intervals only. File: lab-h-descriptions.csv (LAB-H; the 10th, 50th and 90th percentiles blank in rows of the hold-out creators). Edited on 2026-11-26 in release pass 2's fifth fix step (fix6, f91_d70_quantiles.py, SHA-256 1a03a8648a6fc3ce380ec018255a5e4e7a60d3b4134c579c8f5a20ae289eb418); no other value changed.

## Figures in the release

The PNG files named in this README are the package's own drawings, which a release does not copy (D56). Every output of the package is drawn in the release gallery (`gallery/index.html`; records in `gallery/manifest.json`), under these figure ids: ENTRY-H: ENTRY-H-fig-1, ENTRY-H-fig-2, ENTRY-H-fig-3; H3-X: H3-X-fig-1; LAB-H: LAB-H-fig-1, LAB-H-fig-2, LAB-H-fig-3, LAB-H-fig-4, LAB-H-fig-5, LAB-H-fig-6, LAB-H-fig-7. Edited on 2026-11-26 in release pass 2's fix step (fix2, f01_edits.py; its SHA-256 is in the round's records), for privacy and consistency only.
