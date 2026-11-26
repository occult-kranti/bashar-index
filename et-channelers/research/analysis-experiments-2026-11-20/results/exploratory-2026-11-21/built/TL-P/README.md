# TL-P: does the timeline pipeline work? (method pilot)

Exploratory (registry A2); not a test of H1-H10. Status: reported (pilot built before this round; plan 6.6).

**What it asks.** Does the prediction-timeline pipeline work end to end: find dated forecast statements, write a card for
each, classify whether it is resolvable as worded and why not, cluster cards, dry-run analyses 7.1 and 7.2, and check the
resolver on known-answer items? By methodological agnosticism (registry 2026-11-21 02:50) the study reports what was
predicted, for when, and whether an outcome would be observable, never whether a prediction came true.

**Base.** Set W's forecast pilot: 37 recordings of development creators (seen creators); 172 statements with a bounded time
expression, of 21 creators, each given a card by a model.

**What is shown.** `public/tl-p-pilot.csv`: card classes of record (reasons not resolvable; no card was coded resolvable),
event types and flags (categories under 5 creators pooled), the card writer's run-to-run agreement, the timeline lanes,
horizon quartiles of the closed windows, the dry runs of analyses 7.1 and 7.2, the cluster counts at both thresholds, the
resolver's known-answer items with the gate outcome, the count of diagnostic cards as "fewer than 5 creators", and the cost
by step. Figure (gallery group B-LV): cards by class of record (classes of fewer than 5 creators pooled into "other",
and the smallest remaining class joined it until it held 5 or more creators, plan section 3).

**What is withheld and why.** Not published: the diagnostic cards (fewer than 5 creators, addendum 1 item 7) and any verdict on a real statement (methodological agnosticism); prediction text and source names; the card writer's own class (fewer than 5 creators in its resolvable cell); flags, repeat agreements and kappas that rest on fewer than 5 creators; the second model's card agreement and the card-writer gate (the resolvable code from fewer than 5 creators); the hindsight index (fewer than 5 creators); the split of the closed windows by status (the too-recent and matured cards come from fewer than 5 creators); the total of kept statements and the statements outside the timeline rows (not built in this release, lead's decision D55: not recounted by creator); the minima and maxima of horizons; year checks, cutoff strata, evidence checks and the capture-date dry run (small counts, or a year other than 2026).

**Interval level.** None: counts, quartiles and shares, as built.

**Caveats.** Model-coded cards; not checked by a person. A method pilot on 1 or 2 recordings per channel: analysis 7.1 had
no eligible channel by construction. The known-answer items were constructed from public event records inside the
resolvers' training period (an upper bound, not a validation), and the rules v2 were written after seeing those answers
(post hoc). The resolution step (TL-RES) is not run for the study.

Small cells (plan section 3; addenda 1 and 2; registry 2026-11-21 22:33 and 2026-11-22 00:13; decisions D21 and D28): no cell rests on fewer than 5 creators; a statistic is printed only where 5 or more creators carry a non-zero value; an agreement figure only where the positive code comes from 5 or more creators in each reading and the items coded differently from 0 or 5 or more creators; a share near 100% whose misses come from 1 to 4 creators reads "not published (misses from fewer than 5 creators)", never a bound; of two figures whose difference rests on 1 to 4 creators one is not printed; categories under 5 creators are pooled, never suppressed one by one, and a withheld cell is never recoverable by subtraction from printed cells. Nested creator counts never differ by 1 to 4, also against counts already public. These rules hide values; they choose no estimate.

No hold-out or other-group file was opened (no contact): every file read holds seen creators only (development or check creators), or run metadata. No model was called. Exploratory (registry A2); not a test of H1-H10. Released by the release review (plan P10) on 2026-11-22; the output was built before the exploratory round and is reported as built, in the public-safe form of plan section 3.

**Fix pass (2026-11-22, release review B-LV, after the release verifier's findings).** Withheld cells no longer print their card counts (fewer than 5 creators); the caption states the second pooling step. No printed value changed.

**Writers.** `lv_tlp.py` sha256 `e9c4a4ea9f52f9dd0e6d3c5f427577a181e9dc2f6bb5c6fdbaf093630814f4bb`; `lvcommon.py` sha256 `a630f290ccd1296164877c931d17b3d7e288edd2da41e14ba103435812dc5791`; figures by `lv_figs.py` sha256 `b4b8f71c0187e84cf80aed6cf37434023da12d98f734b30655ffbf3ad1cd551f` from the public tables only. Written 2026-11-22T07:08:52Z (UTC, from the clock) by `lv_status.py`.
