# Prediction timeline on seen creators (package TL)

Exploratory (registry A2); not a test of H1-H10. Added after the exploratory reporting plan where the captions say so.

Model-coded: every label behind these tables was produced by language models from frozen prompts; no person has checked them. What is dated and for when, and whether an outcome would be observable; never whether a prediction came true (registry 2026-11-21 02:50, methodological agnosticism). Agreement between readings is agreement, not a measure of correctness.

Verification that exists for these labels: the world-future class (F1) passes gate D on the seen gate sample on its lower bound (0.643 [0.503]) and fails it on the hold-out reliability sample R-hold (kappa 0.507 [90% 0.169, 0.792]; stability 0.903); the checkability parts are kept as the record by the owner's decision (registry 00:30) although they fail their gates: on the development pilot the two-model gate failed for time window (kappa 0.55) and place (not published: fewer than 5 creators); on R-hold gate D passes for time window (0.805) and fails for place (0.306), named actor (0.419) and observable outcome (0.328), quantity not published (fewer than 5 creators); a third model's re-reading of 300 seen check statements gives kappa 0.70 (time window), 0.69 (named actor) and 0.79 (observable outcome), with place and quantity not published (fewer than 5 creators), agreement, not a measure of correctness; the time expressions (FE) flag constructed year items correctly; commitment passes its gates (R-hold C 0.913, D 0.756); the source type of the source-type rows comes from the title codes, whose source family fails gate D on R-hold (0.659 [90% 0.414, 0.853]) and is kept as the record by the same decision. Not checked by a person.

Public cells rest on 5 or more creators; 'fewer than 5' means 1 to 4 creators, 'all but fewer than 5 of 71' means 67 to 70 of the 71 seen creators, and a range such as 55-59 is a band shown where an exact count could fix a difference of 1 to 4 creators against a nested printed count; no name, code, id, title or quotation is printed.

Release form (after the release review of the plotting pass, 2026-11-22): calendar periods that start before 2025 are pooled into one open bin with no start month and periods from 2031 on into one open bin; a percentile month before 2026 reads 'before 2026'; TL-7.7's pooled shares carry 90% creator-bootstrap intervals in place of the withdrawn leave-one-out ends. No printed count changed.

Written 2026-11-22T06:01:20Z; status of every plan id in the release's status table (`status-table.csv`). TL-RES and analysis 7.6 are not run (X: methodological agnosticism); TL-H (the hold-out pass) belongs to the hold-out packages.

## TL-BUILD (paragraph for the main text)

Exploratory (registry A2); not a test of H1-H10. Of the world-future statements that the first-round instruments kept on the seen creators (model-coded: the world-future class by a small model with a second model's reading, which passes its two-model gate on the seen gate sample and fails it on the hold-out reliability sample; time expressions by a small model, windows computed by code; not checked by a person), about 27% (weighted) carry a bounded time expression, and 23% of all kept statements have a closed window the program can compute. Windows are mostly short and near: the median horizon of a closed window is about 69 days after the upload day and about three quarters lie within a year, with a long tail of windows years ahead. Pooled over statements, about 64% of dated statements take their window from the period the talk announces for itself rather than from their own words; when each creator counts equally the share is about 53%. Grouped by the source their recording's title announces (a recording-level proxy), titles that announce a deceased person or a higher self come from too few creators to be shown apart. What is dated and for when is described; matured windows are counted but never resolved, and no prediction is said to have come true or failed.

## TL-BUILD: reported

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Among the seen creators' kept world-future statements (model-coded, not checked by a person), about 27% carry a bounded time expression; closed windows lie a median of about 69 days after the upload day and about three quarters within a year; pooled over statements, about 64% of dated statements take their window from the talk-level period rather than from their own words (about 53% when each creator counts equally); titles announcing a deceased person or a higher self come from too few creators to be shown apart.

Place: S; M (one paragraph); W (counts only). Outputs: tl-build-lanes.csv, tl-build-classes.csv, tl-build-measures.csv, tl-build-status.csv, tl-build-year-flags.csv, tl-build-composition.csv, tl-build-calendar.csv, tl-build-source-types.csv, tl-build-calendar.png, README-TL.md.

## TL-SPEC: not run

Not run: resolvability as worded needs the blind card writer and its second reader, which need model calls, and no money is left under the hard stop.

Place: S; M. Outputs: none.

## TL-7.1: reported

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

In the channels eligible under the protocol rule with confirmed upload days, the targets of absolute windows moved about one day later per day of upload (pooled slope about 1.0, 90% interval 0.38 to 1.50, above the within-channel permutation band): closer to a constant lead than to fixed targets in the primary, while the row pooling confirmed and estimated upload days has a wide interval (about -2.3 to 1.5) and the estimated panel alone has too few eligible channels; described within each channel's span.

Place: S. Outputs: tl-7-1-receding-horizons.csv.

## TL-7.2: reported

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

The positive control was too small to show its excess, so cross-channel overlap of narrow future windows is not read as shared attention beyond the calendar; the main count lies inside the horizon-preserving redraw reference and above the circular-shift reference; the analysis within event clusters was not run (needs model calls).

Place: S. Outputs: tl-7-2-convergence.csv.

## TL-7.3: not run

Not run: restated, postponed and advanced predictions need event clusters confirmed by two models, which need model calls, and no money is left under the hard stop.

Place: S. Outputs: none.

## TL-7.4: reported

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Within creator, no clear difference shows between windows more than a year ahead and nearer ones in the shares of statements coded with an observable outcome, a quantity or commitment (and, over all closed windows, a named actor): 7 of the 10 cells are released and every released 90% interval includes zero, though the commitment intervals still allow differences of more than 10 percentage points; the place cells and one named-actor cell are not released because one band's YES codes come from fewer than 5 creators. (Wording changed after the release review of the plotting pass, 2026-11-22: 'differ little' claimed more than the intervals show.)

Place: S. Outputs: tl-7-4-specificity-by-horizon.csv.

## TL-7.7: reported

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

With confirmed upload days, about 65% of dated statements (about 54% creator-equal) take their window from the talk-level period alone (both panels together about 64%, 53% creator-equal), and the share differs between the merged upload months without a steady direction inside the months covered.

Place: S. Outputs: tl-7-7-frame-share-by-month.csv.

## TL-7.8: reported

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

At the creator level the four time-window readings agree with one another (Spearman about 0.66 to 0.96) far more than with the hedging or condition readings (about -0.21 to 0.00), but the FC-FE and rule-FE cells are partly by construction (FE ran only where the FC time part, the rule or FB's time expression called for it); on the statements where FE was due the time cells are about 0.45 to 0.92; at the statement level the FC and FE readings agree well (kappa 0.79) while the TIME_RE rule agrees only weakly with either (about 0.27 to 0.30); agreement, not a measure of correctness.

Place: S. Outputs: tl-7-8-mtmm-rows.csv, tl-7-8-statement-agreement.csv.

## TL-7.9: reported

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Of the pending closed windows, the largest group becomes first checkable in January 2027 (mostly windows ending in December 2026), and the rest spread thinly over later years; when outcomes would become observable is described, never whether they occur.

Place: S. Outputs: tl-7-9-due-calendar.csv, tl-7-9-due-calendar.png.

## Figures in the release

The PNG files named in this README are the package's own drawings, which a release does not copy (D56). Every output of the package is drawn in the release gallery (`gallery/index.html`; records in `gallery/manifest.json`), under these figure ids: TL-7.1: TL-7.1-fig-1; TL-7.2: TL-7.2-fig-1; TL-7.4: TL-7.4-fig-1; TL-7.7: TL-7.7-fig-1; TL-7.8: TL-7.8-fig-1, TL-7.8-fig-2, TL-7.8-fig-3; TL-7.9: TL-7.9-fig-1; TL-BUILD: TL-BUILD-fig-1, TL-BUILD-fig-2, TL-BUILD-fig-3, TL-BUILD-fig-4, TL-BUILD-fig-5, TL-BUILD-fig-6, TL-BUILD-fig-7. Edited on 2026-11-26 in release pass 2's fix step (fix2, f01_edits.py; its SHA-256 is in the round's records), for privacy and consistency only.
