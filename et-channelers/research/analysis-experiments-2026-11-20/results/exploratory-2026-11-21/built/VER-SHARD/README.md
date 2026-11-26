# VER-SHARD: do smaller shards recover planted decisions better at acceptable cost?

Exploratory (registry A2); not a test of H1-H10. Status: reported (built before this round; plan 6.5).

**What it asks.** For the sentence codes (S), the forecast checkability parts (FC) and TIME's roles, does a smaller shard
(fewer units per call) recover planted decisions better, or code more stably, at no more than 1.5 times the cost?

**Base.** Development creators (seen creators). S: KA's 27 constructed windows of 20 creators, 405 target units (310
planted codes), 15 units per call against 5, with 1 per call as a reference; FC: 387 of KA's 388 planted forecast
statements (39 creators; 1,934 part decisions), five parts per call against one; TIME: 1,200 stored hits of development
creators (creator count not published: a creator count 1 to 4 from a nested count), 10 hits per call against 3. Three small-model runs per arm.

**What is shown.** `public/ver-shard.csv`: recovery, stability (mean agreement over the three run pairs), all-three-same
shares, Fleiss' kappa, usable decisions, quotation checks, the smaller-minus-current differences with 90% intervals, the
cost per run and the rule's outcome (primary, literal and O9-strict readings). Figure (gallery group B-LV): stability at
both sizes.

**What is withheld and why.** Not published: shares whose misses come from fewer than 5 creators, or are not shown to come from 5 or more (usable decisions and exact quotations near 100%, the time-window part's recovery, which is shown pooled with the quantity part; D21); the share of TIME answers inconsistent with the codebook in the 10-hit arm (fewer than 5 creators); the shares of rare sentence codes on unplanted units and the problem counts (not part of the plan row's public form).

**Interval level.** 90% creator-bootstrap intervals (2,000 draws, KA's statistics), VER-SHARD's own.

**Caveats.** Model-coded; not checked by a person; constructed-text recovery is an upper bound, not a measure of correctness on the corpus.
Where planted truths were not re-read in this review, run-to-run disagreements give a lower bound on the creators behind
misses. Costs include a cache-write allowance; the ratio is also printed without it.

Small cells (plan section 3; addenda 1 and 2; registry 2026-11-21 22:33 and 2026-11-22 00:13; decisions D21 and D28): no cell rests on fewer than 5 creators; a statistic is printed only where 5 or more creators carry a non-zero value; an agreement figure only where the positive code comes from 5 or more creators in each reading and the items coded differently from 0 or 5 or more creators; a share near 100% whose misses come from 1 to 4 creators reads "not published (misses from fewer than 5 creators)", never a bound; of two figures whose difference rests on 1 to 4 creators one is not printed; categories under 5 creators are pooled, never suppressed one by one, and a withheld cell is never recoverable by subtraction from printed cells. Nested creator counts never differ by 1 to 4, also against counts already public. These rules hide values; they choose no estimate.

No hold-out or other-group file was opened (no contact): every file read holds seen creators only (development or check creators), or run metadata. No model was called. Exploratory (registry A2); not a test of H1-H10. Released by the release review (plan P10) on 2026-11-22; the output was built before the exploratory round and is reported as built, in the public-safe form of plan section 3.

**Fix pass (2026-11-22, release review B-LV, after the release verifier's findings).** The checkability base reads 387 of KA's 388 planted statements; TIME's creator count, 1 to 4 below a nested count, is not published instead of bounded; withheld rows no longer state how many calls or answers miss. No printed value changed.

**Writers.** `lv_vershard.py` sha256 `cd4858e75b0916bb49ac515a059c4c53a34bdb70306fef465e889799e22962c4`; `lvcommon.py` sha256 `a630f290ccd1296164877c931d17b3d7e288edd2da41e14ba103435812dc5791`; figures by `lv_figs.py` sha256 `b4b8f71c0187e84cf80aed6cf37434023da12d98f734b30655ffbf3ad1cd551f` from the public tables only. Written 2026-11-22T07:08:52Z (UTC, from the clock) by `lv_status.py`.
