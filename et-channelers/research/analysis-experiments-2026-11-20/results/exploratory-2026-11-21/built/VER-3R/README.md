# VER-3R: does a reader of another vendor, reading blind, agree with the OpenAI readers?

Exploratory, VER-3R analysis (registry A2/A11); not a test of H1-H10. Status: reported. Built and sealed before freeze 1,
opened after freeze 1 with its seal verified (registry 2026-11-21 04:59). Its headline figure is published in the
first-round results; these are its full tables, consistent with that figure.

**What it asks.** Does a model of another vendor (an Anthropic model), reading blind with ten units of context on each
side and the name masked, agree with the OpenAI readers' majority on the claimed / own / other voice contrast (gate VG-6),
and where do the readers disagree?

**Base.** VER-3R's four-stratum sample: 200 sentence units of 23 check creators (seen creators; 26 English recordings of
the gate sample G), weighted to a frame of 5,896 units. Readers: the small model (three runs and two label repeats), the
middle model (two runs), the third model of the same vendor (gpt-6-sol, guided steps), the RX frames rule and the reader
of another vendor (four agents on four disjoint packets of 50 units).

**What is shown.** `public/ver3r-reader-pairs.csv`: agreement and kappa of every pair of readers (55 pairs).
`public/ver3r-gate-and-sensitivity.csv`: VG-6, kappa 0.91 (90% 0.84 to 0.95), passes (kappa 0.60 or more and lower bound
0.50 or more), and its sensitivity rows, among them the kappa of the embodied contrast that H4 uses (0.91, 0.83 to 0.96,
as already published).
`public/ver3r-disagreement-cells.csv`: where the two vendors' readers differ. `public/ver3r-strata-and-packets.csv`: by
sampling stratum and packet. `public/ver3r-latent-class.csv`: Dawid-Skene error rates three ways (heuristic) and the
all-same share. `public/ver3r-reader-profile.csv`: fine-code agreement, cue types, stated confidence and codes of the reader
of another vendor. Figure (gallery group B-LV): kappa of the reader of another vendor against each reader.

**What is withheld and why.** Not published: the four confusion cells of the two vendors' readers that rest on fewer than 5 creators (shown pooled) and the direction rows of the claimed/own disagreements (tipping-point input (e)); the agreement within the near-change, agree-claimed and agree-not-claimed strata (shown pooled); the sensitivity row without the units coded V0 and its unit count (the units left out come from fewer than 5 creators); the two-class sensitivity row (with the gate and the printed cells it would give a cell of fewer than 5 creators); the agreement of the embodied contrast against the OpenAI majority (it differs from the gate row in fewer than 5 creators; its kappa and interval were already published and stay) and the embodied row against the third model of the same vendor (pairs rule); the unit count and the unweighted columns of the three-model-majority rows (the units without such a majority come from fewer than 5 creators), and those of its rows that would fix that set; the rows of the reader of another vendor against the middle model's second run (pairs rule); every other figure that the joint audit of the fix pass refuses (it would fix a cell of fewer than 5 creators with other printed figures, or differ from a printed figure in fewer than 5 creators: one packet's third-model agreement, one majority-vote resolved share, the four-reader all-same share, and some fine-code, cue and code counts); the latent-class conditional error cells and the majority-vote cells and resolved shares that rest on fewer than 5 creators; the all-ten-readers all-same share; the fine-code cross-tables (shown as pooled agreement); RX coverage counts (fewer than 5 creators).

**Interval level.** 90% percentile intervals from a creator bootstrap (4,999 draws; 999 for the latent-class models), seed
20261121; their coverage is not audited (23 creators). Pooled rows computed in this review use the analysis's own code and
bootstrap draws.

**Caveats.** Model-coded; no person checked any label; agreement between readers, not a measure of correctness. The OpenAI majority holds
four of the OpenAI runs, so their kappas with it are inflated by construction. Cross-vendor agreement is weaker evidence of
independence than it looks. The weighted estimates rest heavily on the 30 agree-not-claimed units (73% of the frame).
Latent-class rates are heuristic under conditional independence, which readers of one vendor break. Permitted wording
(registry 04:59): "model-coded; a model of another vendor (Anthropic), reading blind with ten units of context on each side,
agreed with the OpenAI readers' majority ... kappa 0.91 ...; not validated by a person".

Small cells (plan section 3; addenda 1 and 2; registry 2026-11-21 22:33 and 2026-11-22 00:13; decisions D21 and D28): no cell rests on fewer than 5 creators; a statistic is printed only where 5 or more creators carry a non-zero value; an agreement figure only where the positive code comes from 5 or more creators in each reading and the items coded differently from 0 or 5 or more creators; a share near 100% whose misses come from 1 to 4 creators reads "not published (misses from fewer than 5 creators)", never a bound; of two figures whose difference rests on 1 to 4 creators one is not printed; categories under 5 creators are pooled, never suppressed one by one, and a withheld cell is never recoverable by subtraction from printed cells. Nested creator counts never differ by 1 to 4, also against counts already public. These rules hide values; they choose no estimate.

No hold-out or other-group file was opened (no contact): every file read holds seen creators only (development or check creators), or run metadata. No model was called. Exploratory (registry A2); not a test of H1-H10. Released by the release review (plan P10) on 2026-11-22; the output was built before the exploratory round and is reported as built, in the public-safe form of plan section 3.

**Fix pass (2026-11-22, release review B-LV, after the release verifier's findings).** Chains of printed figures gave withheld confusion cells (the gate, the two-class row and a printed cell; the claimed/own row's unit count with the pooled cell), the embodied rows differed from printed rows in fewer than 5 creators, and two unit counts gave small cells by complement. Every linear figure of the six tables is now gated together in the weighted and the unweighted space (joint audit), and the figures that fail are withheld; the kappas already published stay.

**Release pass 2, fix step (2026-11-26).** VER-DEP prints the same sealed latent-class figures, and the two packages withheld opposite cells. Both now follow the stricter rule: a reader's Dawid-Skene error rate is printed only where its departures from the fitted latent class come from none or 5 or more creators (VER-DEP's rule, now applied here to the one-coin and six-reader models too), so the one-coin error rate of the reader of another vendor reads "not published"; VER-DEP withholds the four readers' all-same share, which this item's joint audit withholds. Every other linear voice figure that VER-DEP prints is one that this item prints. `lv_ver3r.py` was rerun; no other figure changed.

**Writers.** `lv_ver3r.py` sha256 `bb1a4065fb1ffcbf4427e795c46671728083f3ba419c7b02ddfc0c8a58d5470e` (release pass 2, fix step; before it `a6a4b581c6a04214eb8ce3e5e6294f32c6904e697143e3b9958e0223aac0974d`); `lvcommon.py` sha256 `a630f290ccd1296164877c931d17b3d7e288edd2da41e14ba103435812dc5791`; figures by `lv_figs.py` sha256 `b4b8f71c0187e84cf80aed6cf37434023da12d98f734b30655ffbf3ad1cd551f` from the public tables only. Written 2026-11-22T07:08:52Z (UTC, from the clock) by `lv_status.py`.
