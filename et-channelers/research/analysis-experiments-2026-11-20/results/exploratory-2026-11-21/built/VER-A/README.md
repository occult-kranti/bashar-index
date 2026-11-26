# VER-A: where the two cheap readers split, how does a blind third reader side?

Exploratory (registry A2); not a test of H1-H10. Status: reported (pilot built before this round; plan 6.5).

**What it asks.** Where the small and the middle model's round-1 voice labels disagree, which side does a blind third
reader (gpt-6-sol, guided form G) take, how far does it depart from agreed labels on decoys, how stable is it over repeat
runs, and does the guided form beat the typed form (T) on constructed boundary items?

**Base.** Set W: 32 recordings of 32 development creators (seen creators), one recording each, so recordings count
creators. 83 region windows were adjudicated; the disputed words lie in 101 regions of 21 recordings.

**What is shown.** `public/ver-a-sides-on-disputed-words.csv`: the share of disputed words on which the third reader gives
the small model's label, the middle model's label, neither, or both in its set, overall and by label pair, format and
region kind (groups of fewer than 5 recordings pooled; within groups only the shares the joint audit lets through).
`public/ver-a-labels-round2-reference.csv`: agreement per label,
the round-2 readers on the same words, and agreement with the designer-coded reference spans.
`public/ver-a-verdicts-gates-constructed.csv`: the per-pair verdicts, VG-5 and VG-4 outcomes, kappas over all labelled
units, the constructed boundary items and the form and effort rules' outcomes (T stays the default form).
`public/ver-a-cost.csv`: the calls and their cost. Figure (gallery group B-LV): the overall sides with 90% intervals.

**Reading.** The third model gave the middle model's label on about half of the disputed words (0.49, 90% 0.25 to 0.81)
and the small model's on about a third (0.34, 0.09 to 0.56); the intervals overlap widely, and the pilot's own protocol
verdict is indeterminate for every label pair with 5 or more recordings, so no side is shown to be favoured.

**What is withheld and why.** Not built in this release (lead's decision D55): the decoy departure, the three-run stability, the departure on agreed context and the side row of gpt-6.2-sol (their creators could not be recounted in this review without the transcript pipeline; VG-4's outcome, fails, is already public in VER/ver.md). Not published: every label pair, format and region kind with fewer than 5 recordings (pooled), and within a group every side share that would rest on fewer than 5 creators, or with which a sum, difference or word-weighted mix of printed figures (the overall row is such a mix of the groups of each partition) would fix a share of fewer than 5 creators or bound it within 0.05 (joint audit of the fix pass); per-label shares of labels on fewer than 5 recordings; the reference-span agreement of the two cheap readers and the per-label reference rows; the round-2 consensus rows that would give a cell of fewer than 5 creators by difference; the constructed boundary items' shares whose misses come from fewer than 5 host recordings (D21), and the paired G-minus-T recovery (its discordant items come from fewer than 5 creators); the creator count of VG-5's pair and format (a creator count 1 to 4 from a nested count); which reader the third reader favoured in a pair.

**Interval level.** 90% creator-bootstrap intervals (VER-A's own); groups pooled in this review carry their own 90%
creator-bootstrap interval (2,000 draws); several rows are points without intervals, as built.

**Caveats.** Model-coded; a third model of the same vendor, not a person and not another vendor; agreement, not a measure of correctness.
The reference spans are themselves a language model's coding (vendor not recorded) and are descriptive only. The pilot ran
on the fallback model at low effort; the effort arm moved to KA.

Small cells (plan section 3; addenda 1 and 2; registry 2026-11-21 22:33 and 2026-11-22 00:13; decisions D21 and D28): no cell rests on fewer than 5 creators; a statistic is printed only where 5 or more creators carry a non-zero value; an agreement figure only where the positive code comes from 5 or more creators in each reading and the items coded differently from 0 or 5 or more creators; a share near 100% whose misses come from 1 to 4 creators reads "not published (misses from fewer than 5 creators)", never a bound; of two figures whose difference rests on 1 to 4 creators one is not printed; categories under 5 creators are pooled, never suppressed one by one, and a withheld cell is never recoverable by subtraction from printed cells. Nested creator counts never differ by 1 to 4, also against counts already public. These rules hide values; they choose no estimate.

No hold-out or other-group file was opened (no contact): every file read holds seen creators only (development or check creators), or run metadata. No model was called. Exploratory (registry A2); not a test of H1-H10. Released by the release review (plan P10) on 2026-11-22; the output was built before the exploratory round and is reported as built, in the public-safe form of plan section 3.

**Fix pass (2026-11-22, release review B-LV, after the release verifier's findings).** The first pass gated each group of a partition in its own closure family, so the overall row, read as a word-weighted mix of the format groups, gave withheld sides of the solo recordings by difference. Every word-weighted figure of the sides table and of the per-label and round-2 table is now gated together (joint audit: no sum, difference or mix of printed figures may fix a share of fewer than 5 creators, and every withheld share of fewer than 5 creators must keep a feasible range reaching 0.05 on both sides of its value, also when a light group's weight is taken as known); shares that fail are now withheld. The title no longer states a direction (the pilot's verdicts are indeterminate); withheld rows no longer print small counts or bounds.

**Writers.** `lv_vera.py` sha256 `9bf3361489f16f559f2fbc9af80af6a91709c3fd2d070085c9abd095e0addf89`; `lvcommon.py` sha256 `a630f290ccd1296164877c931d17b3d7e288edd2da41e14ba103435812dc5791`; `span_audit.py` sha256 `29643538c5bb18f8dcaa327496eb4aa21c69bd1ac6a20fb9cea7951ff952d3f1`; figures by `lv_figs.py` sha256 `b4b8f71c0187e84cf80aed6cf37434023da12d98f734b30655ffbf3ad1cd551f` from the public tables only. Written 2026-11-22T07:08:52Z (UTC, from the clock) by `lv_status.py`.
