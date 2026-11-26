# rv-L3: windows with non-language or pseudo-words

Exploratory, paper review (registry A2/A7); not a test of H1-H10. Status: reported (built before this round; plan 6.1).

**What it asks.** How many 30-s windows hold non-language or pseudo-words (for example glossolalia or misrecognised
speech), how often two models read the windows a simple flag picks out as non-language, and whether the lexical measures
move when flagged windows are left out.

**Base.** The seen creators' 30-s windows of 8 or more tokens (71 creators, 1,284 recordings, 62,624 eligible windows). The
flag (out-of-vocabulary share over 1/6 and window word probability under the creator's 10th percentile) was fixed on
development-creator windows; 574 windows were flagged (56 creators). Two OpenAI models read 200 flagged and 200 unflagged
windows.

**What is shown.** `public/rv-l3-precision.csv`: the share of read windows coded non-language, by sample (flagged,
unflagged), creator scope (all seen, development, check) and model, window-level (design-weighted; model-read, not a
check against a truth), creator mean and unweighted sample share. `public/rv-l3-precision-by-creator-load.csv` and
`public/rv-l3-precision-by-oov-band.csv`: post hoc groups, merged until each holds non-language and other reads from 5 or
more creators. `public/rv-l3-flag-counts.csv`: flagged minutes over creators (bins, median, 90th percentile), window
counts, the estimated non-language minutes and the agreement of the two models. `public/rv-l3-lexical-with-without.csv`:
four lexical measures with and without flagged windows. Figure (gallery group B-LV): the share of flagged windows read
as non-language, overall and by group. The lowest out-of-vocabulary band starts at the flag's theta, 1/6 (16.7%).

**What is withheld and why.** Not published: the windows read non-language by both models and the middle model's development and check rows where they differ from a printed row in fewer than 5 creators; the build's lowest creator-load bin (1 or 2 flagged windows) and top out-of-vocabulary band (over 40%), whose misses or positives come from fewer than 5 creators (both merged into neighbouring bins, plan section 3); the flagged windows held by the top 3, 5 and 10 creators (a top list); each creator's largest move and the creators moved where they lie 1 to 4 below the 56 creators with a flagged window; the cross-table with the voice pilot's labels (the creators behind its cells could not be counted); the creator counts that lie 1 to 4 below a nested count (a creator count 1 to 4 from a nested count).

**Interval level.** 95% (rv-L3's own: creator bootstrap of the design-weighted estimate, a design interval and Wilson
intervals); groups merged in this review carry a 95% creator-bootstrap interval (2,000 draws).

**Caveats.** Model-read, not checked by a person: a model cannot tell glossolalia from misrecognised speech without
audio. The unweighted sample share under-weights the few creators with many flagged windows and is not the window-level
share.
Bins and bands are post hoc. Words per minute is a recognizer-output measure (recognized words per minute inside the
recognizer's segments), not a direct measure of speaking.

Small cells (plan section 3; addenda 1 and 2; registry 2026-11-21 22:33 and 2026-11-22 00:13; decisions D21 and D28): no cell rests on fewer than 5 creators; a statistic is printed only where 5 or more creators carry a non-zero value; an agreement figure only where the positive code comes from 5 or more creators in each reading and the items coded differently from 0 or 5 or more creators; a share near 100% whose misses come from 1 to 4 creators reads "not published (misses from fewer than 5 creators)", never a bound; of two figures whose difference rests on 1 to 4 creators one is not printed; categories under 5 creators are pooled, never suppressed one by one, and a withheld cell is never recoverable by subtraction from printed cells. Nested creator counts never differ by 1 to 4, also against counts already public. These rules hide values; they choose no estimate.

No hold-out or other-group file was opened (no contact): every file read holds seen creators only (development or check creators), or run metadata. No model was called. Exploratory (registry A2); not a test of H1-H10. Released by the release review (plan P10) on 2026-11-22; the output was built before the exploratory round and is reported as built, in the public-safe form of plan section 3.

**Fix pass (2026-11-22, release review B-LV, after the release verifier's findings).** The measure is called the share of flagged windows read as non-language (model-read), not the flag's precision; the lowest band is labelled from theta, 1/6 (16.7%); two creator counts that lay 1 to 4 below a nested count are not published instead of bounded; a withheld cross-table no longer prints its cell sizes. No printed value changed.

**Writers.** `lv_l3.py` sha256 `02ef43fe37998e593d1bcea720001821f527a2e92c6bc58eabdfd1ad323501c7`; `lvcommon.py` sha256 `a630f290ccd1296164877c931d17b3d7e288edd2da41e14ba103435812dc5791`; figures by `lv_figs.py` sha256 `b4b8f71c0187e84cf80aed6cf37434023da12d98f734b30655ffbf3ad1cd551f` from the public tables only. Written 2026-11-22T07:08:52Z (UTC, from the clock) by `lv_status.py`.
