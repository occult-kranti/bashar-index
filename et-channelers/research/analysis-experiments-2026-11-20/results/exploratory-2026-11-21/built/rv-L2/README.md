# rv-L2: how much the recognizer moves the labels

Exploratory, paper review (registry A2/A7); not a test of H1-H10. Status: reported (built before this round; plan 6.1).

**What it asks.** Does transcribing the same recording with another recognizer change the model labels (claimed voice
and spoken asks) more than labelling the same transcript twice does?

**Base.** 25 bridge pairs of 25 development creators (seen creators): each recording transcribed by the run's recognizer
(E) and by the larger multilingual model (L); E labelled twice (E1, E2) and L once, with the frozen snapshot of the voice
and asks instruments of 2026-11-20 19:34/19:45. The forecast finder was not run (not frozen when rv-L2 was built).

**What is shown.** `public/rv-l2-label-flips.csv`: per label, the flip share between transcripts (E1 against L, E2 against
L), run to run (E1 against E2), the mean of the two between-transcript flips and its difference from run to run, with 90%
creator-bootstrap intervals; voice as shares of words or 1 - Jaccard over the words given a label, asks as shares of
matched events (primary rule: overlap of at least half of the shorter event; 'any overlap' as a sensitivity rule).
`public/rv-l2-asks-unit-rule-withdrawn.csv`: the withdrawn asks unit rule, printed as a withdrawn row (P6), never a result.
`public/rv-l2-where-flips-sit.csv`: where the voice flips sit among the three readings, the share of unaligned words and
the quartiles of word-level transcript disagreement. Figure (gallery group B-LV): the between-minus-run-to-run difference
for every row printed.

**Reading (rv-L2's own, as corrected by its verifier).** All-label flips were 23.3% and 15.2% between transcripts against
21.7% run to run: changing the recognizer adds no detectable label instability. One run (E1) carries much of the run-to-run
noise, so one run pair cannot size it. For asks, the 'any ask' difference is +0.099 (90% 0.010 to 0.188) under the primary
rule; rv-L2 reads this as no firm recognizer effect on asks, with a possible effect not ruled out, to be retested with 3
or more runs per transcript. Pointwise 90% intervals, no family-wise control: of the 7 difference rows printed here, about
1 would exclude 0 by chance, and 1 does (any ask). The earlier reading that K3 and K4 move beyond run noise rested on
asymmetric unit matching and is withdrawn.

**What is withheld and why.** Not published: rows of rare labels (V5 other material, V6 unseparated conversation, K2 money, K5 adverts: fewer than 5 creators); relayed voice V3 and the cannot-tell code V0 beyond their first comparison (the label is positive in both readings for fewer than 5 creators); the K1, K3 and K4 ask rows wherever their flips come from fewer than 5 creators; the 'any overlap' sensitivity rows that differ from the primary rule in fewer than 5 creators; the withdrawn rows of K2, K3 and K5; the counts of words lost to a failed window and of ask events overlapping unchecked events (each rests on fewer than 5 creators); the recording counts of V1 and of any ask (1 to 4 below the 25).

**Interval level.** 90% creator-bootstrap intervals (rv-L2's own).

**Caveats.** Model-coded; stability of labels across recognizers, not a measure of correctness; not checked by a person. Labels were made
with an instrument snapshot that was revised afterwards; the frozen copy rebuilds every stored request.

Small cells (plan section 3; addenda 1 and 2; registry 2026-11-21 22:33 and 2026-11-22 00:13; decisions D21 and D28): no cell rests on fewer than 5 creators; a statistic is printed only where 5 or more creators carry a non-zero value; an agreement figure only where the positive code comes from 5 or more creators in each reading and the items coded differently from 0 or 5 or more creators; a share near 100% whose misses come from 1 to 4 creators reads "not published (misses from fewer than 5 creators)", never a bound; of two figures whose difference rests on 1 to 4 creators one is not printed; categories under 5 creators are pooled, never suppressed one by one, and a withheld cell is never recoverable by subtraction from printed cells. Nested creator counts never differ by 1 to 4, also against counts already public. These rules hide values; they choose no estimate.

No hold-out or other-group file was opened (no contact): every file read holds seen creators only (development or check creators), or run metadata. No model was called. Exploratory (registry A2); not a test of H1-H10. Released by the release review (plan P10) on 2026-11-22; the output was built before the exploratory round and is reported as built, in the public-safe form of plan section 3.

**Fix pass (2026-11-22, release review B-LV, after the release verifier's findings).** The recording counts of V1 and of any ask, 1 to 4 below the 25, are no longer printed or bounded anywhere; the figure's title says no detectable instability rather than an equivalence; the chance statement now covers only the rows printed here. No printed value changed.

**Writers.** `lv_l2.py` sha256 `a35ad9ffb97e2484a7fae652c707dded6ed5ef3ce4d3d54a6508f411073b7b58`; `lvcommon.py` sha256 `a630f290ccd1296164877c931d17b3d7e288edd2da41e14ba103435812dc5791`; figures by `lv_figs.py` sha256 `b4b8f71c0187e84cf80aed6cf37434023da12d98f734b30655ffbf3ad1cd551f` from the public tables only. Written 2026-11-22T07:08:52Z (UTC, from the clock) by `lv_status.py`.
