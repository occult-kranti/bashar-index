# VER-GC: does the published free-text guided form beat the typed form?

Exploratory (registry A2); not a test of H1-H10. Status: reported (built before this round; plan 6.5).

**What it asks.** For the forecast class (FB), the forecast commitment (FD) and the ask check (ASK), does the published
free-text guided form (G) give higher two-model agreement, no worse stability, under 2% invalid answers and no worse planted
recovery than the typed form (T), as the rule fixed before any call requires?

**Base.** Development creators (seen creators). FB: 400 items of 34 recordings of 31 creators; FD: 200 items of 33
recordings of forecast-class creators (creator count not published: a creator count 1 to 4 from a nested count); ASK: 150 items of 45 recordings of 32 creators; 100 items of each read by both models; planted
(constructed) items placed in development-creator transcripts: FB 100, FD 100, ASK 140 (their creator counts are not printed: they nest within counts printed for VER-SHARD).

**What is shown.** `public/ver-gc-forms.csv`: per instrument and form, two-model agreement (kappa and share the same),
a two-code agreement, stability over two small-model runs, invalid first answers, planted recovery, the G-minus-T
differences with 90% intervals and the rule's outcome. Figure (gallery group B-LV): agreement and stability, G against T.

**What is withheld and why.** Not published: the invalid-answer shares that rest on one call (fewer than 5 creators); the forecast class's guided-form planted recovery and the G-minus-T recovery differences whose discordant items come from fewer than 5 creators; planted recovery shares whose misses come from fewer than 5 creators (D21); the forecast commitment's committed-or-not kappa (disagreements or a code from fewer than 5 creators); the per-class label distributions (not part of the plan row's public form); and any rule condition whose figure is not published (stating it would bound a withheld share).

**Interval level.** 90% two-stage cluster-bootstrap intervals (creator, then recording; 2,000 draws), VER-GC's own, for the
differences; the per-form figures are points, as built.

**Caveats.** Model-coded; cross-read by two OpenAI models; no human or external reference; agreement, not a measure of correctness.
Planted recovery is on constructed text: an upper bound, not a measure of correctness on the corpus.

Small cells (plan section 3; addenda 1 and 2; registry 2026-11-21 22:33 and 2026-11-22 00:13; decisions D21 and D28): no cell rests on fewer than 5 creators; a statistic is printed only where 5 or more creators carry a non-zero value; an agreement figure only where the positive code comes from 5 or more creators in each reading and the items coded differently from 0 or 5 or more creators; a share near 100% whose misses come from 1 to 4 creators reads "not published (misses from fewer than 5 creators)", never a bound; of two figures whose difference rests on 1 to 4 creators one is not printed; categories under 5 creators are pooled, never suppressed one by one, and a withheld cell is never recoverable by subtraction from printed cells. Nested creator counts never differ by 1 to 4, also against counts already public. These rules hide values; they choose no estimate.

No hold-out or other-group file was opened (no contact): every file read holds seen creators only (development or check creators), or run metadata. No model was called. Exploratory (registry A2); not a test of H1-H10. Released by the release review (plan P10) on 2026-11-22; the output was built before the exploratory round and is reported as built, in the public-safe form of plan section 3.

**Fix pass (2026-11-22, release review B-LV, after the release verifier's findings).** The forecast commitment's creator count, 1 to 4 below a nested count, is not published instead of bounded. No printed value changed.

**Writers.** `lv_vergc.py` sha256 `4279aa918d380223ef6ee445263eeab38edbc9ec200bb6f640d21c2fbb88c292`; `lvcommon.py` sha256 `a630f290ccd1296164877c931d17b3d7e288edd2da41e14ba103435812dc5791`; figures by `lv_figs.py` sha256 `b4b8f71c0187e84cf80aed6cf37434023da12d98f734b30655ffbf3ad1cd551f` from the public tables only. Written 2026-11-22T07:08:52Z (UTC, from the clock) by `lv_status.py`.
