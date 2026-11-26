# Verification layer: VER-DEP, VER-CAL, VER-ADJ-G, DR-2, VER-MV

Exploratory (registry A2); not a test of H1-H10. Written 2026-11-22 (UTC) in the exploratory round of the reporting plan
(registry 2026-11-21 23:17), and corrected the same day after an adversarial verification. Every label below is
model-coded, and no person checked any label. Agreement between models is reported as agreement, not a measure of correctness.
Known-answer items are constructed text, so agreement with the constructed answer is an upper bound for the corpus and
not a measure of correctness on the corpus. No model was called for any figure in this file.

Small cells. No figure, cell or bin rests on fewer than 5 creators. A code whose positive codes or whose disagreements
come from 1 to 4 creators is pooled into "other (pooled)" or withheld. For DR-2 and the asks block of VER-DEP, a figure is
printed only if no count resting on 1 to 4 creators can be solved from it and the other printed figures, including those
the registry and the first-round results already print (the disclosure check below). Intervals are 90%.

| Plan id | Status | Place | Tables |
|---|---|---|---|
| DR-2 | reported | S | `dr2-views.csv`, `dr2-codes.csv`, `dr2-confusion.csv` |
| VER-CAL | reported (voice and ask parts not run) | S | `ver-cal-summary.csv`, `ver-cal-bins.csv` |
| VER-DEP | reported (hold-out bounds and threshold distances not run) | S; M (bounds) | `ver-dep.csv` |
| VER-ADJ-G | not run | S | - |
| VER-MV | reported (tipping-point tables not released) | M; S | `ver-mv-rows.csv`, `ver-mv-crosswalk.csv` |

## The disclosure check (DR-2, asks)

A withheld cell can still be solved from figures that are printed. In a three-group table, for example, the two cells
between groups i and j sum to record_only(i) + record_only(j) - second_only(k). Checking pairs of nested sets does not
catch this. The check therefore takes every printed count of one set of units together:

- Every possible combination of codes is an unknown whole number, 0 or more.
- Every printed figure fixes the count of one set of these combinations. Figures that the registry and the first-round
  results already print are included.
- A mixed-integer programme then searches for any category of units resting on 1 to 4 creators whose count follows
  from the printed figures.

Figures are added in a fixed order: views, code rows, the registered H5 group rows, then cells. A figure that would make
such a count solvable is withheld.

Kappa is used through its linear content. The three H5 groupings print three kappas but leave only two margin dimensions
open, so the check treats their margins as known; the other views' kappas leave more dimensions open than they fix.
Code: `disclosure.py`, called by `dr2_public.py` and `ver_dep.py`.

## DR-2: a second model reading the same units

**In one sentence.** A second OpenAI model agreed with the record on the sentence-code groups (kappa 0.79) and on three
checkability parts (time window, named actor and observable outcome; kappa 0.69 to 0.79). Place and quantity are too rare
on this sample to publish.

- **Data.** The second reading of 2026-11-21 03:15 to 03:21 UTC (registry 02:50; its figures are in the registry row of
  04:55). It covers gate sample G of seen creators only. G holds check and development creators alike and is not the 23
  check creators of VER-3R.
  - Sentence codes: 400 units of 34 recordings of 32 creators. The record is the small model and the second reader the
    middle model, with the same prompt and effort.
  - Checkability: 300 coded forecast statements of 27 recordings, one recording per creator. The record is the middle
    model and the second reader the large model (gpt-6-sol) at effort low.
- **Verification.** Model-coded. The second reading is by another model of the same vendor, which measures reliability,
  not validity. Not checked by a person.
- **Departure from the plan row.** The plan says "300 forecast candidates". What was read a second time is 300 coded
  statements, on the five checkability parts only, not the forecast class or commitment (registry 04:55: "it covers
  checkability and the sentence codes, not commitment").
- **What is printed.**
  - Every confusion table was rebuilt from the stored readings and checked cell for cell against the driver's results.
  - Point figures and intervals come from the driver, so they equal the registry's numbers. Pooled codes, which the driver
    does not hold, have intervals from this package's two-stage bootstrap and are marked as such.
  - Sentence-code group views (view-level figures only for the two variants, as in the registry):
    - registered grouping: kappa 0.786 [0.735, 0.832];
    - Q2 moved to world claim: 0.745;
    - Q2 moved to practice and feeling: 0.749.
  - Primary code (12 values): kappa 0.684 [0.634, 0.727]. Code rows are printed for Q1, Q3, Q4, Q5, Q7 and Q8. Six codes
    rest on too few creators and are pooled into "other (pooled)": Q0, Q2, Q6, Q9, QN and QX.
  - Registered H5 group rows: the world-claim row is printed. It holds the same units as Q1's row. The practice-and-
    feeling and neither rows are withheld by the disclosure check: with the printed figures they would let the cells
    between world claim and practice be solved, and those rest on fewer than 5 creators. The code rows of the two variant
    groupings are not printed.
  - Checkability, 3 values: time window 0.703 [0.554, 0.920]; named actor 0.687 [0.553, 0.765]; observable outcome
    0.787 [0.741, 0.858]. The time-window disagreements are concentrated in very few creators (registry 04:55), so that
    kappa rests mostly on them.
    - Place is withheld: its disagreements come from fewer than 5 creators.
    - Quantity is withheld: its YES codes come from fewer than 5 creators in one reading.
    - The YES rows (each part's YES code against the rest) are withheld for every part.
    - Only one view per part is printed.
    - The registry row of 04:55 and the first-round results print kappas for place and quantity, which this package
      withholds under the small-cell rules. Reconciling the two is left to the lead (errata).
  - Number of YES parts: kappa 0.619 [0.479, 0.758], with the row for 0 and a pooled row for 1 to 3.
  - Confusion cells: only cells of 5 or more creators that pass the disclosure check are printed. That is 3 cells of the
    H5 group table, 12 of the primary-code table, one or two per checkability part, and two of the number-of-YES-parts
    table. The other cells are not listed, so the file does not show which cells are empty. The code rows are each
    table's public form.

## VER-CAL: does stated confidence track known answers?

**In one sentence.** On constructed known-answer items, the confidence that the models stated sat near the top of the
scale for every instrument (mean 0.96 to 0.99) and tracked agreement with the constructed answer only roughly. For the
small model, voice labels on which two runs split agreed with the constructed answer far less often than those on which
the runs agreed.

- **Data.** The KA battery's constructed items.
  - The forecast, sentence-code and voice items are planted into windows of seen development creators.
  - The title arm is 12 constructed lists of template titles under made-up creators (KA title-items rule). Its cluster
    count is a count of those lists, not of creators.
  - Stated confidence comes from KA's confidence arm. It covers the forecast critic (class), the checkability parts, the
    commitment code, the sentence codes and the title presentation, each read by the small and the middle model.
  - Consistency-based confidence comes from two runs of the same items: the voice label (KA's repeat arm, 30 items, voice
    revision 2, variant A, both models; the units are speech units, weighted by words) and the sentence codes (small
    model, 80 targets).
- **Statistics.** KA's definitions are reproduced exactly, and KA's stored scores were checked against them:
  - mean confidence and agreement with the constructed answer (KA calls it accuracy; protocol 4.12 licenses "agreement
    with the constructed answer");
  - expected calibration error over 10 equal bins, and the Brier score;
  - 90% intervals from 2,000 cluster bootstrap draws;
  - reliability bins merged until each holds 5 or more clusters and both its wrong and its right answers come from 0 or
    5 or more clusters. Under this rule the middle model's checkability curve and its voice-consistency curve collapse to
    one bin each.
- **Verification.** Model-coded, against constructed known answers. Not checked by a person. Confidence may only order
  review queues (protocol 4.12). It is not a gate and not evidence that a label is right.
- **Withheld.** Agreement, ECE and Brier score are not printed for three rows (title presentation, both models; forecast
  critic, middle model): their wrong answers come from fewer than 5 creators, or for titles fewer than 5 constructed
  lists. Mean confidence is printed for these rows.
- **Not run.**
  - Stated confidence on the voice label and the ask check: the confidence arm was not bought for them (registry 02:40;
    KA README).
  - The third reader's confidence: gpt-6-sol's answer schema (VER-A, VER-3R) has no confidence field, and VER-ADJ-G and
    VER-ADJ-H did not run.
  - VER-3R's reader of another vendor does state a confidence. Its units have no known answers, because it is compared
    with the OpenAI majority, so it is outside VER-CAL; VER-3R reports it.
- **Factual correction to the plan row.** The plan records the whole KA confidence arm as not bought (X). According to
  KA's README, only its voice and ask parts were not bought, and the forecast, sentence and title parts ran. Those parts
  are reported here. This correction is for an addendum by the lead.

## VER-DEP: what several readers imply about shared errors

**In one sentence.** On the voice sample of seen check creators, the four readers of four models together count for
fewer than two independent votes (heuristic). On
constructed items, the errors of the two OpenAI models were substantially correlated (phi about 0.5). A three-group
correction for asks ended at a boundary and tells nothing.

- **Voice.** The 200 units of the HUMAN sample of the 23 check creators (VER-3R), weighted to the sampling frame. The
  readers are the small, middle and large (gpt-6-sol) OpenAI models and a reader of another vendor (Anthropic).
  - All-same share of the four readers: not published. With the figures VER-3R prints it differs from a printed figure,
    or follows from a sum or difference of printed figures, in fewer than 5 creators (VER-3R's joint audit, applied to
    both packages in release pass 2's fix step, 2026-11-26).
  - Effective votes from departures from the other readers' majority: 1.745 [1.377, 2.293] (heuristic).
  - Dawid-Skene error rates and prevalences, three ways (independent, OpenAI bloc, one coin), and each reader's
    departure from the others' majority; the one-coin rate of the reader of another vendor is withheld (its departures
    from the latent class come from fewer than 5 creators), here and in VER-3R. All of these are from the sealed VER-3R analysis, whose hashes were checked
    before use.
  - Every latent-class figure is labelled "estimated under conditional independence, which readers of one vendor are
    known to break". None is accuracy.
- **Errors on known-answer items (true errors, constructed text).** These compare the small and the middle model.
  - Voice revision 3 arms (weighted by words): phi of the errors 0.512 [0.435, 0.595]; effective votes 1.322 [1.255, 1.394].
  - Checkability parts: phi 0.549 [0.446, 0.643]; effective votes 1.291 [1.217, 1.388].
  - Commitment code and sentence codes: not estimable, because a model made no error.
  - Forecast class and title presentation: withheld, because the errors come from fewer than 5 creators (for titles,
    fewer than 5 constructed lists).
- **Asks: three groups.** The unit is the recording: 1,062 seen recordings with a description, of all but fewer than 5
  of the 71 seen creators. Three groups label each recording:
  - the OpenAI ask labels (pay or enrol);
  - the RX price pattern, a rule on the transcript;
  - the paid-offer links in the description, a rule on the page.

  The three groups give the same code on 0.371 [0.303, 0.437] of the recordings.

  Effective votes from departures are not estimable with three binary groups. A recording has a reference for two groups
  at once only when all three agree, so departures never co-occur.

  The three-indicator latent-class model (DMM type) is just identified and has no test. The fit reached a boundary: the
  price pattern's sensitivity and specificity both reached 1, so the latent class is that rule's own code. The correction
  is printed but flagged as not informative. Departure: the classical latent-class model was fitted; the DMM paper's
  estimator was not reimplemented. Every asks figure passed the disclosure check over the eight response patterns.
- **Not run.**
  - Dawid-Skene outside voice: no other sample carries three or more readers of different models without being selected
    by disagreement.
  - DMM on the voice sample: the RX frames rule codes too few of the 200 units for a latent-class model
    (primary rule: units of fewer than 5 creators; secondary rule: too few units).
  - DMM on the title family: not run in this round. Its three groups are not stored joined per title, and most families
    hold fewer than 5 creators.
  - Hold-out (F2), not computed: the partial-identification bounds of H1, H2, H4, H5 and H6, and the threshold distances
    of these and H9. No registered estimate is published beside which they could stand, and computing them would be a
    further hold-out contact. H1, H4, H5 and H6 are not determinable, with eligible creators below the minimum of 12. H2 is
    not run for want of an instrument; its eligible creators are at least the minimum of 9. H9 is not determinable in
    both versions. All of this is as published.
  - Made after a hold-out contact on 2026-11-21 (an unplanned planning read of the frozen report; `contacts.md` item 1).
  - Third-reader and latent-class figures on R-hold: not run, because they need model calls.

## VER-ADJ-G: the third reader on the gate samples

**Not run: needs model calls; no money left under the hard stop (registry 2026-11-21 18:41).**

- No pass of the design exists: blind third reader, 10% decoys, three repeats, every instrument, the G-seen gate samples.
  The ledger has no VER-ADJ tag.
- The large-model readings that do exist on seen creators follow other designs:
  - the 200 voice units of VER-3R (23 check creators);
  - the 300 checkability statements of DR-2 (gate sample G);
  - the title adjudications, which read only disputed titles.
- None of them has the blind decoys or repeats that VG-4 and VG-5 need, so neither gate can be computed.

## VER-MV: every multiverse row and the tipping-point tables

Made after a hold-out contact on 2026-11-21 (unplanned planning read of the frozen report at about 23:19 UTC;
`contacts.md` item 1).

**In one sentence.** Every robustness row that the frozen code computed for the six registered hypotheses of the first
round is listed in the published results, and every verification row from M1 to M13 is accounted for, most as not run.
The tipping-point tables are not released, because no registered result was determinable or run.

- **Completeness.** The frozen report's 48 robustness rows were checked against the published first-round results
  (2026-11-21 22:33 UTC). All 48 are listed, either published with their verdict or listed as resting on fewer than 5
  creators.
  - `ver-mv-rows.csv` copies each row's published verdict and flag.
  - Every registered primary is not determinable or not run, and the rows carry no verdict of their own.
  - One flag: H4's second-model row reads "supported (model-coded)" with the flag "labels below the reliability floor".
    It is not a result of H4.
- **M1 to M13** (`ver-mv-crosswalk.csv`).
  - Reported: M1, the primary, and M2, the second model. H5's M2 covers titles only. H9's M2 is listed but rests on fewer
    than 5 creators.
  - Not run, as the crosswalk says row by row:
    - M3, the rewordings: HR (b, c) was not bought.
    - M4, M5 and M7: no third reader read the hold-out, and VG-4 failed in the voice pilot.
    - M6, M9 and M10: these would need model calls on the hold-out.
    - M11, where three groups exist:
      - asks (H6): reported as a description on seen recordings (VER-DEP);
      - title family (H5, H9): not run;
      - voice sample (H1, H4, H6): not run, because the RX frames rule codes too few of the 200 units for
        a latent-class model (VER-DEP).
    - M12: the 200 units of the HUMAN sample, each read with ten units of context on each side, carry no contrast of the
      registered form. The cross-vendor agreement is printed beside the verdicts.
    - M13: unfunded.
  - M8: does not apply as a separate row.
- **Tipping-point tables.** The frozen code computed them for H1, H2, H4, H5 and H6 (none for H9). They are not released,
  because each is arithmetic on an estimate that the published results do not print.
  - H1, H4, H5 and H6 are not determinable, with eligible creators below the minimum of 12.
  - H2 is not run for want of an instrument (the forecast class is below its reliability floor on R-hold). Its eligible
    creators are at least the minimum of 9, as published.
  - The verification figures that the protocol prints beside them are given as pointers: KA (a), VER-A (b, c), VER-DEP
    (d), VER-3R (e), and (f), which was not computed (VER-DEP).
- **Hold-out contact.** The frozen report was loaded for row names and for the presence of each tipping-point table only:
  in one run and one logged repeat. The files were then corrected from public files only (`ver_mv_fix.py`, not a
  contact). All of this is in `contacts.md`. The code was written after freeze 2, which departs from the plan's "code
  frozen in the freeze-2 record".

Release-review edit, 2026-11-22 (release pass, plotting group X-VERCROSS, after the release verifier's report):
the counts of units that the RX frames rule codes on the voice sample are withheld, because they rest on fewer
than 5 creators; the two sentences that gave them (VER-DEP and VER-MV) now give the reason only. Nothing else
changed.
