# r3-P33: prespecification and the printed selection rule (written before the rule is applied)

Third-round programme, step 1, class a.1, after r3-P06 and r3-P30. Written by a step-1 agent (a model agent working for
the project lead; not a person). Exploratory; not a test of H1-H10. Seen creators only. No model call, no network call.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What the programme and deposit 2 fix

- Programme (r3-P33): the README's most informative descriptions were chosen without a printed rule (A6); envelopes are
  labelled lower bounds; r3-P06 places the rule-reversal end of the asks envelope. Plot: den-meth's artefact cascade, one
  panel per seen headline, rows in a fixed order: unmatched; position-matched; beyond both transplants; register-matched;
  middle model; acoustic, when ruled in; the asks envelope. Builds on the public README's list, rv-R4, VER-MV, LAB-A,
  LAB-V, PT-cd, TL-7.1, E5. The roster-history arm is class b (not run here).
- Deposit 2 (margins register): kind "description"; no margin stated, so the lead's defaults by measure type hold;
  "envelopes are labelled lower bounds; a headline keeps reading A only through every row". Account cells: silent.
- The programme's correction text (r3-P35) asks for "the rule behind the README's most informative descriptions, or
  'chosen after the results were seen'".

## Part 1. How the README's 17 descriptions were chosen (a fact to be looked up, not decided)

The audit looks for a printed selection rule in: the public README itself (`exploratory-2026-11-21/public-README.md`),
the status table, the collector's code (`collect/code/*.py`, read file by file), the collector's records in `collect/`
(file by file), the lead's decisions of 2026-11-22, the deviations summary and the addendum-3 draft, and the published
programme. If no rule is found, the answer printed is **"chosen after the results were seen"**, with the list of places
searched. No recursive text search runs over the run folder.

## Part 2. The selection rule of this audit (printed here; applied after this file is hashed)

S1. **Unit.** A *stated seen quantity*: a number or direction stated in one of the README's 17 descriptions, or in the
    status-table headline of an output that programme-decisions.json cites for r3-P33 (rv-R4, VER-MV, LAB-A, LAB-V,
    PT-cd, TL-7.1, E5), that rests on seen creators only.
S2. **Hold-out.** Statements about hold-out creators (README items 10, 12, the hold-out values of item 11, E3-H in item
    14, and VER-MV) are listed as "hold-out: not audited (seen creators only)"; a seen comparator printed inside such an
    item (item 11's seen value) is audited as a seen quantity.
S3. **Kind.** Each stated seen quantity is a *contrast* (a difference, ratio, slope or correlation between two voices,
    two parts of a recording, two surfaces, or an estimate against a stated reference, with a creator-level interval
    printed in its source output's public files or status headline) or a *level* (a share, mean, count or agreement
    figure with no stated contrast). Levels and agreement figures get no informativeness class (deposit 2's margins are
    margins of contrasts); a contrast with no printed interval is "contrast without an interval: not classed".
S4. **Informativeness class** of every contrast, read on the interval its source output printed (its level and method
    are stated), against deposit 2's margin for its measure type (a margin fixed after these results were published, so
    labelled **"for design only"**): *beyond the margin* (wholly beyond, in either direction; the named direction where
    the source names one); *non-zero, size undetermined* (excludes zero, crosses the margin); *trivial* (excludes zero,
    wholly inside the margin); *equivalent* (includes zero, wholly inside the margin); *uninformative* (includes zero and
    crosses the margin). A contrast whose unit fits no deposited type reads "no deposited margin fits: excludes / includes
    zero". Where r3-P30's interval-choice table finds no method that holds for the design class at that count, the class
    is followed by "(r3-P30: no method holds; at most undetermined)".
S5. **Detectable size.** For every contrast that is not "beyond the margin", the size an analysis like it would detect
    with 80% power at a one-sided 5% level: (1.645 + 0.842) x SE, with SE = (upper - lower) / (2 z) and z = 1.645 for a
    90% interval, 1.960 for a 95% interval (a normal approximation from the printed interval). Printed beside the margin.
S6. **Cascade panels.** One panel per seen by-voice headline contrast of a registered statistic or of E5, the panels the
    programme's plot names: H1 (claimed-minus-own unit rate, log ratio; margin 0.223), H4 (contraction drop,
    between-creator SD; margin 0.20), H6 (placement of pay-or-enrol asks, observed minus expected share; margin 0.05),
    E5 long pauses (per 100 words) and E5 fillers (per 1,000 words) (no deposited margin fits these units: read against
    zero only). They are the by-voice contrasts stated in README items 2, 7 and 15.
S7. **Cascade rows**, in the programme's fixed order: (1) unmatched; (2) position-matched; (3) beyond both transplants
    (the cross-creator transplant XT and the same-creator transplant ST as two sub-rows); (4) register-matched; (5)
    middle model; (6) acoustic (a.2: not ruled in, blank); (7) the asks envelope (H6 only). Values come only from the
    step-1 entries' public files (r3-P04, r3-P03, r3-P05, r3-P06, r3-P01) and E5's public file, small model of record
    unless the row is the middle model's. A row that no entry computed or published is blank and labelled with why
    ("not built", "a.2", "not published: fewer than 5 creators", "not applicable").
S8. **Row readings.** Deposit 2's words on each row's printed interval and margin: beyond the margin in the named
    direction (A); inside the margin (B); crosses the margin (undetermined); "beyond the margin, opposite to the named
    direction" (the lead's step-1 decision 2). A row is capped at undetermined where its source says no interval method
    holds at its count, or that its reference is not admissible (r3-P04). Rows without a margin read "excludes zero" or
    "includes zero".
S9. **Cascade reading per panel:** "keeps A through every computed row" if every computed row reads A; otherwise "A on
    k of m computed rows; first row without A: <row> (<why>)". Blank rows are listed; the acoustic row is never computed
    here, so no panel can keep A "through every row".
S10. **Envelopes are lower bounds.** The asks envelope (labelled against rule-reversal; small against middle model) is
    printed as a lower bound on label uncertainty, never inside an interval. If its far end differs from the labelled
    value in fewer than 5 creators, it is not printed (pairs rule) and the row says so.
S11. **Panel-wide band** (a disclosure, not a test; deposit 2 applies no family-wise adjustment): beside each row's 90%
    interval a thinner bar widened by z(1 - 0.05/56) / z(0.95) on each side of the estimate (Bonferroni over the
    register's 56 primaries, a normal approximation from the printed interval).
S12. **rv-R4** (weighting and window specifications) is cited as a survival column where it covers a stated quantity
    (pace, time without speech, the thanks phrase at a window end, term-cue shares); no new perturbation is run. The
    round-3 survival matrix (listing-rank, vintage, visibility, audience reweighting, leave-k-out) is not run here (the
    adopted programme's step-1 text fixes the cascade; leave-k-out fragility is r3-P32's).

## Privacy

Every value is copied from a published file; counts are printed as their source printed them. No per-creator value, no
quantile of creator values. A derived number (detectable size, panel-wide band) is a function of one printed interval.

## Known leak

The writer has read the public README, the status table's headlines and the step-1 entries' public files (and r3-P26's
results) before writing this rule. The rule follows the programme's named panels and rows; it chooses no estimate.

## Plots

`fig-r3-P33-cascade` (five panels, rows in the fixed order, 90% intervals, thin panel-wide bars, lines at zero, half the
margin and the margin, blank labelled rows); `fig-r3-P33-informativeness` (every classed contrast on a margin scale,
coloured by class, with its detectable size). Captions state the interval level and "exploratory; not a test of H1-H10".
