# Registered hypotheses, first round: results on the hold-out creators (model-coded)

Status: final. Published 2026-11-21T23:33:53Z (UTC) by `publish_results.py` from the private report of the registered tests (`run.py analyse`). Machine-readable twin: `first-round-2026-11-21.json` (schema `et-channelers/first-round-results` 1.3.0).

## How to read these results

- **Model-coded.** Every label behind these results was produced by language models from frozen prompts; no person has checked the labels (registry A1, A8). Every result is model-coded, and the strongest verdicts available are "supported (model-coded)" and "refuted (model-coded)". Agreement between models is reported as agreement, not accuracy (A1).
- **Registered rule.** A hypothesis is "supported (model-coded)" only if its Holm step passes (Holm-adjusted p at most 0.05, the count fixed at 10: H3 and H8 enter at p = 1, H7 and H10, not run, at p = 1; A9, A10.1), its registered support rule holds (hypotheses.md), the A5 interval excludes zero and its registered effect-size condition holds (A8). It is "refuted (model-coded)" when its registered refutation holds; refutations read from intervals are unadjusted (A10.1). Fewer eligible creators than its minimum gives "not determinable" (A10.2), an instrument below its reliability floor "not run for want of an instrument" (A10.5); otherwise the result is "not determined", with the conditions that failed.
- **A5.** A5 (registry, 2026-11-20, after H3 was tested): "supported" also requires the 90% interval over creators to exclude zero. For the amended versions of H5 and H6, both the t interval on the creator OE values and the wider Mantel-Haenszel interval must exclude it (decision of 2026-11-21 06:44 (5)).
- **A10 guard.** A10 guard (registry 2026-11-21 03:08, completed at 04:55): wherever A10 replaces a registered estimator, reference, minimum, interval or centring, the registered and the amended versions are computed on the same data. The larger of their two p values enters Holm (a version that cannot be run has p = 1). A verdict stands only if both versions give it; otherwise the result reads "not determined: the registered and the amended versions differ". If either version is not determinable, the result is "not determinable", with the reason naming the version, and it is flagged uninformative. Both versions are printed.
- **Uninformative.** A result is uninformative when its 90% creator interval contains both zero and the smallest effect of interest in either direction, or its verdict is not determinable (registry 02:50).
- **Wording.** Supported and refuted verdicts read "verified by a third model, on known-answer texts and by a reader of another vendor", with the figures entered in the run's config (registry A10 part 2, 2026-11-21 03:08).
- **Holm.** Holm over m = 10 at family-wise 0.05; ties are ordered by the registry's hypothesis order, as the analysis orders them; p values are printed as the report rounds them (4 decimals).
- **Scope.** Confirmatory estimates read the hold-out creators only (decision of 2026-11-21 04:55 (h)); H9 pairs hold-out cells with seen cells. The first round runs H1, H2, H4, H5, H6 and H9.
- **Small cells.** No figure here rests on fewer than 5 creators. Such a count is printed as "fewer than 5"; two printed counts of hold-out creators never differ by 1 to 4 (a count that would is stated against the other, as "all but fewer than 5 of N"), nor lie 1 to 4 from a count of hold-out creators published elsewhere (such a count is stated against its minimum); an estimate, its interval and a version's p are printed only where the result is determinable and the version rests on 5 or more creators with a non-zero value; a robustness row resting on fewer than 5 creators is listed without a verdict, and the flag "robust to the labeller" reads the published rows only; an agreement figure (a kappa or a share of items coded alike, on R-hold or the hold-out) is printed only where its positive code comes from 5 or more creators in each reading and the creators with an item the readings code differently are none or 5 or more (a minor code both readings give alike is not a cell of its own); counts of valid calls or quotations are given as shares, without their shortfalls. No creator, channel, recording, title or quotation appears.

## Holm procedure (m = 10, family-wise 0.05)

| Step | Hypothesis | Status | p entering Holm | Holm-adjusted p | Step passed |
|---|---|---|---|---|---|
| 1 (threshold 0.005) | H1 | run in the first round | 1 | 1 | no |
| 2 (threshold 0.005556) | H2 | run in the first round | 1 | 1 | no |
| 3 (threshold 0.00625) | H3 | closed by the owner (A6); counted as run, it enters Holm at p = 1 | 1 | 1 | no |
| 4 (threshold 0.007143) | H4 | run in the first round | 1 | 1 | no |
| 5 (threshold 0.008333) | H5 | run in the first round | 1 | 1 | no |
| 6 (threshold 0.01) | H6 | run in the first round | 1 | 1 | no |
| 7 (threshold 0.0125) | H7 | not run: it needs the replication wave, and none exists (A4; decision of 2026-11-21 04:55 (h)); enters Holm at p = 1 | 1 | 1 | no |
| 8 (threshold 0.016667) | H8 | dropped by the owner (A9); counted as run, it enters Holm at p = 1 | 1 | 1 | no |
| 9 (threshold 0.025) | H9 | run in the first round | 1 | 1 | no |
| 10 (threshold 0.05) | H10 | not run in the first round (decision of 2026-11-21 04:55 (m)); enters Holm at p = 1 | 1 | 1 | no |

## Results

| Hypothesis | Verdict (A10 guard) | Eligible creators | Estimate [90% creator interval] | Holm-adjusted p | Uninformative | Robust to the labeller |
|---|---|---|---|---|---|---|
| H1 | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | not published (the result is not determinable) | 1 | yes | no |
| H2 | not run for want of an instrument: below the reliability floor (forecast class of record (F1 against the rest, registry 03:12) fails gate D on R-hold: kappa small against middle, weighted by the inverse of the sampling probability, 0.507 [90% 0.169, 0.792] against the floor 0.60 and the bound 0.50 (A10.5); its gate C passes (0.903 [0.877, 0.927]); commitment passes (C 0.913 [0.868, 0.949], D 0.756 [0.585, 0.862]); checkability is kept as the record under the owner's 00:30 exception (A10.5, not extended to the class), with R-hold D place 0.306, named actor 0.419, observable outcome 0.328, time window 0.805 [lower 90% bound 0.647] (quantity not published: its figure rests on fewer than 5 creators), and C observable outcome 0.826) | at least the minimum of 9 | not published (the result is not determinable) | 1 | yes | yes |
| H4 | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | not published (the result is not determinable) | 1 | yes | no |
| H5 | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | not published (the result is not determinable) | 1 | yes | yes (read from the published rows only; rows resting on fewer than 5 creators are not counted) |
| H6 | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | not published (the result is not determinable) | 1 | yes | yes |
| H9 | not determinable in both versions (amended: too few eligible creators (fewer than 5 of 8); registered: the family-label permutation cannot reach the first Holm step (eligible creators: fewer than 5; the number of distinct labelings is not published)) | fewer than 5; minimum 8 | not published (the result is not determinable) | 1 | yes | not assessable: every robustness row rests on fewer than 5 creators |

Estimates are those of the amended version; both versions are below. Holm count 10: H3 closed by the owner (A6); counted as run, it enters Holm at p = 1; H7 not run: it needs the replication wave, and none exists (A4; decision of 2026-11-21 04:55 (h)); enters Holm at p = 1; H8 dropped by the owner (A9); counted as run, it enters Holm at p = 1; H10 not run in the first round (decision of 2026-11-21 04:55 (m)); enters Holm at p = 1.

## H1

**not determinable: too few eligible creators (below the minimum of 12)**

- Holm: p entering Holm 1 (the larger of the two versions), Holm-adjusted 1, step 1 of 10 (threshold 0.005), not passed.
- A10 guard applies (the versions' verdicts agree); it replaces: interval: random-effects pool by DerSimonian-Laird with normal intervals (registered) -> HKSJ with t(k-1) (A10.7, CAL-A14 point 2).
- Uninformative: yes (the verdict is not determinable).
- VG-6: Gate VG-6 passed (kappa 0.91): no cap applies (registry 2026-11-21 03:21).
- Reliability gates on R-hold (A10.5), passed: voice (record: middle model on the small map; R-hold, A10.5): A 0.995 of all calls (record configuration 0.996; map stage alone 0.972, flagged: a per-stage reading would fail A); B claimed quotations 0.997; C claimed/own/other same in 5 runs 0.920 [0.839, 0.989] against 0.90 (0.80); D kappa middle against small claimed/own/other 0.832 [0.692, 0.929] and embodied/own/other 0.815 [0.679, 0.909] against 0.60 (0.50); VG-6 passes (0.91 [0.84, 0.95]); feature files: deterministic, 297 hold-out files of features-4 written by the features.py that freeze 2 pins (no floor).

| Version | Verdict | Eligible creators | p entering the guard | Estimate [90% creator interval] | Scale | Uninformative |
|---|---|---|---|---|---|---|
| amended | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | 1 (by rule: the version is not determinable) | not published (the result is not determinable) |  | yes |
| registered | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | 1 (by rule: the version is not determinable) | not published (the result is not determinable) |  | yes |

- Labels were produced by language models from frozen prompts; no person has checked them (A8). The estimate is model-coded.
- The voice label responds to punctuation and case.
- Verification (A11, registry 03:08): verified by a third model (voice label: gpt-6-sol with guided steps against the OpenAI readers' majority on claimed, own and other voice, kappa 0.79 (90% 0.61 to 0.90), agreement 87.6%, 200 seen check units of 23 creators weighted to 5,896 units (VER-3R); a third model of the same vendor, not a person), on known-answer texts (voice revision 3, middle model (hold-out record), 30 creators: region accuracy 0.96 (0.94 to 0.98), claimed recall 0.97 (0.95 to 0.99) on embodied and 0.93 (0.88 to 0.96) on relayed passages, claimed precision 1.00 (0.99 to 1.00) (constructed texts; an upper bound for the corpus, not accuracy on it; KA battery)) and by a reader of another vendor (voice label: an Anthropic model reading blind with ten units of context on each side against the OpenAI readers' majority on claimed, own and other voice, kappa 0.91 (90% 0.84 to 0.95), 200 seen check units of 23 creators (gate VG-6, registry 04:59); no person checked any label).

Robustness rows (robust to the labeller: no):

| Row | Verdict | Uninformative |
|---|---|---|
| second model (small against middle) | not determined (Holm step, registered rule, A5 interval, effect-size condition) | yes |
| rule A (offer ends a claimed voice) | not determinable: too few eligible creators (below the minimum of 12) | yes |
| strict own voice | not determinable: too few eligible creators (below the minimum of 12) | yes |
| labels as the model gives them (rule A, strict) | not determinable: too few eligible creators (below the minimum of 12) | yes |
| claimant cannot_tell admitted | not determinable: too few eligible creators (below the minimum of 12) | yes |
| recognizer model stratified: other and unknown models included (registry 03:08) | not determinable: too few eligible creators (below the minimum of 12) | yes |

## H2

**not run for want of an instrument: below the reliability floor (forecast class of record (F1 against the rest, registry 03:12) fails gate D on R-hold: kappa small against middle, weighted by the inverse of the sampling probability, 0.507 [90% 0.169, 0.792] against the floor 0.60 and the bound 0.50 (A10.5); its gate C passes (0.903 [0.877, 0.927]); commitment passes (C 0.913 [0.868, 0.949], D 0.756 [0.585, 0.862]); checkability is kept as the record under the owner's 00:30 exception (A10.5, not extended to the class), with R-hold D place 0.306, named actor 0.419, observable outcome 0.328, time window 0.805 [lower 90% bound 0.647] (quantity not published: its figure rests on fewer than 5 creators), and C observable outcome 0.826)**

- Holm: p entering Holm 1 (the larger of the two versions), Holm-adjusted 1, step 2 of 10 (threshold 0.005556), not passed.
- A10 guard applies (the versions' verdicts agree); it replaces: reference: commitment permuted within creator and length band, 9,999 draws (registered) -> two-sided sign-flip of creator D (A10.1, CAL-A8); minimum: 8 creators (registered) -> 9, the two-sided minimum (A10.3, CAL-A10); interval: creator bootstrap (creators, then recordings, R1) of the pooled D (registered) -> HKSJ with t(k-1) (A10.7, CAL-A14).
- Uninformative: yes (the verdict is not determinable).
- VG-6: Gate VG-6 (the other-vendor read of the voice label, registry 2026-11-21 03:21) concerns H1, H4 and H6 only.
- Reliability gates on R-hold (A10.5), not passed: forecast class of record (F1 against the rest, registry 03:12) fails gate D on R-hold: kappa small against middle, weighted by the inverse of the sampling probability, 0.507 [90% 0.169, 0.792] against the floor 0.60 and the bound 0.50 (A10.5); its gate C passes (0.903 [0.877, 0.927]); commitment passes (C 0.913 [0.868, 0.949], D 0.756 [0.585, 0.862]); checkability is kept as the record under the owner's 00:30 exception (A10.5, not extended to the class), with R-hold D place 0.306, named actor 0.419, observable outcome 0.328, time window 0.805 [lower 90% bound 0.647] (quantity not published: its figure rests on fewer than 5 creators), and C observable outcome 0.826.

| Version | Verdict | Eligible creators | p entering the guard | Estimate [90% creator interval] | Scale | Uninformative |
|---|---|---|---|---|---|---|
| amended | not run for want of an instrument: below the reliability floor (forecast class of record (F1 against the rest, registry 03:12) fails gate D on R-hold: kappa small against middle, weighted by the inverse of the sampling probability, 0.507 [90% 0.169, 0.792] against the floor 0.60 and the bound 0.50 (A10.5); its gate C passes (0.903 [0.877, 0.927]); commitment passes (C 0.913 [0.868, 0.949], D 0.756 [0.585, 0.862]); checkability is kept as the record under the owner's 00:30 exception (A10.5, not extended to the class), with R-hold D place 0.306, named actor 0.419, observable outcome 0.328, time window 0.805 [lower 90% bound 0.647] (quantity not published: its figure rests on fewer than 5 creators), and C observable outcome 0.826) | at least the minimum of 9 | not published | not published (the result is not determinable) |  | yes |
| registered | not run for want of an instrument: below the reliability floor (forecast class of record (F1 against the rest, registry 03:12) fails gate D on R-hold: kappa small against middle, weighted by the inverse of the sampling probability, 0.507 [90% 0.169, 0.792] against the floor 0.60 and the bound 0.50 (A10.5); its gate C passes (0.903 [0.877, 0.927]); commitment passes (C 0.913 [0.868, 0.949], D 0.756 [0.585, 0.862]); checkability is kept as the record under the owner's 00:30 exception (A10.5, not extended to the class), with R-hold D place 0.306, named actor 0.419, observable outcome 0.328, time window 0.805 [lower 90% bound 0.647] (quantity not published: its figure rests on fewer than 5 creators), and C observable outcome 0.826) | at least the minimum of 8 | not published | not published (the result is not determinable) |  | yes |

- Labels were produced by language models from frozen prompts; no person has checked them (A8). The estimate is model-coded.
- Checkability: the two-model gate failed for time window (kappa 0.55) and place (0.29; floor 0.60) after both allowed revisions; by the owner's decision the middle model codes every statement and is the record, and the largest model re-reads a sample of about 300 statements (registry, owner decisions before freeze 1).
- Verification (A11, registry 03:08): verified by a third model (checkability: gpt-6-sol re-read 300 seen check statements against the record (middle model): kappa time window 0.70 (0.55 to 0.92), place 0.80, named actor 0.69, observable outcome 0.79, quantity 0.72 (registry 04:55), and 300 hold-out statements; the VER-3R figure covers the voice label only), on known-answer texts (forecasts: 388 planted statements of 39 creators, found 0.98 (0.97 to 0.99), critic F1 given found 0.90 (0.88 to 0.92) before its 02:53 revision, relayed arm 0.74 after it (registry 03:12), decoys accepted as F1 0.04 (0.00 to 0.10); checkability, middle model: time window 0.99, place 0.90, named actor 1.00, observable outcome 0.88, quantity 0.97; hedge 1.00 (constructed texts; an upper bound for the corpus, not accuracy on it; KA battery)) and by a reader of another vendor (no reader of another vendor read the forecast, commitment or checkability codes; VG-6 covers the voice label only).

Robustness rows (robust to the labeller: yes):

| Row | Verdict | Uninformative |
|---|---|---|
| flagged statements included (shared scenario or withdrawal wording, M9) | not run for want of an instrument (as the verdict above) | yes |
| all five checkability parts (the score as registered before M9) | not run for want of an instrument (as the verdict above) | yes |
| cannot-tell parts counted as YES | not run for want of an instrument (as the verdict above) | yes |
| cannot-tell parts counted as NO | not run for want of an instrument (as the verdict above) | yes |
| cannot-tell commitment counted as committed | not run for want of an instrument (as the verdict above) | yes |
| cannot-tell commitment counted as not committed | not run for want of an instrument (as the verdict above) | yes |
| FRAME parts counted (R10) | not run for want of an instrument (as the verdict above) | yes |
| time window from the period of the talk (FRAME) counted as NO (second reading, registry 04:55) | not run for want of an instrument (as the verdict above) | yes |
| time-window part alone | not run for want of an instrument (as the verdict above) | yes |
| checkability: small | not run for want of an instrument (as the verdict above) | yes |
| recognizer model stratified: other and unknown models included (registry 03:08) | not run for want of an instrument (as the verdict above) | yes |

## H4

**not determinable: too few eligible creators (below the minimum of 12)**

- Holm: p entering Holm 1 (the larger of the two versions), Holm-adjusted 1, step 4 of 10 (threshold 0.007143), not passed.
- A10 guard applies (the versions' verdicts agree); it replaces: interval: random-effects pool by DerSimonian-Laird with normal intervals and prediction interval (registered) -> HKSJ with t(k-1) (A10.7, CAL-A14 point 2).
- Uninformative: yes (the verdict is not determinable).
- VG-6: Gate VG-6 passed (kappa 0.91): no cap applies (registry 2026-11-21 03:21).
- Reliability gates on R-hold (A10.5), passed: voice (record: middle model on the small map; R-hold, A10.5): A 0.995 of all calls (record configuration 0.996; map stage alone 0.972, flagged: a per-stage reading would fail A); B claimed quotations 0.997; C claimed/own/other same in 5 runs 0.920 [0.839, 0.989] against 0.90 (0.80); D kappa middle against small claimed/own/other 0.832 [0.692, 0.929] and embodied/own/other 0.815 [0.679, 0.909] against 0.60 (0.50); VG-6 passes (0.91 [0.84, 0.95]) (embodied stability 0.920 [0.839, 0.989]; VG-6 embodied 0.91 [0.83, 0.96]); feature files: deterministic, 297 hold-out files of features-4 written by the features.py that freeze 2 pins (no floor).

| Version | Verdict | Eligible creators | p entering the guard | Estimate [90% creator interval] | Scale | Uninformative |
|---|---|---|---|---|---|---|
| amended | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | 1 (by rule: the version is not determinable) | not published (the result is not determinable) |  | yes |
| registered | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | 1 (by rule: the version is not determinable) | not published (the result is not determinable) |  | yes |

- Labels were produced by language models from frozen prompts; no person has checked them (A8). The estimate is model-coded.
- The voice label responds to punctuation and case.
- Verification (A11, registry 03:08): verified by a third model (voice label: gpt-6-sol with guided steps against the OpenAI readers' majority on claimed, own and other voice, kappa 0.79 (90% 0.61 to 0.90), agreement 87.6%, 200 seen check units of 23 creators weighted to 5,896 units (VER-3R); a third model of the same vendor, not a person), on known-answer texts (voice revision 3, middle model (hold-out record), 30 creators: region accuracy 0.96 (0.94 to 0.98), claimed recall 0.97 (0.95 to 0.99) on embodied and 0.93 (0.88 to 0.96) on relayed passages, claimed precision 1.00 (0.99 to 1.00); embodied exact among claimed 1.00 (1.00 to 1.00) (constructed texts; an upper bound for the corpus, not accuracy on it; KA battery)) and by a reader of another vendor (voice label: an Anthropic model reading blind with ten units of context on each side against the OpenAI readers' majority on claimed, own and other voice, kappa 0.91 (90% 0.84 to 0.95), 200 seen check units of 23 creators (gate VG-6, registry 04:59); no person checked any label; on the embodied contrast that H4 uses, kappa 0.91 (0.83 to 0.96)).

Robustness rows (robust to the labeller: no):

| Row | Verdict | Uninformative |
|---|---|---|
| second model (small against middle) | supported (model-coded) (flag: labels below the reliability floor: the small model's own stability on R-hold is 0.872 [0.807, 0.924] against its floor of 0.90; reported as computed, it is not a result of H4, whose primary is not determinable (registry 2026-11-21 19:30 (4))) | no |
| rule A (offer ends a claimed voice) | not determinable: too few eligible creators (below the minimum of 12) | yes |
| strict own voice | not determinable: too few eligible creators (below the minimum of 12) | yes |
| labels as the model gives them (rule A, strict) | not determinable: too few eligible creators (below the minimum of 12) | yes |
| claimant cannot_tell admitted | not determinable: too few eligible creators (below the minimum of 12) | yes |
| recognizer model stratified: other and unknown models included (registry 03:08) | not determinable: too few eligible creators (below the minimum of 12) | yes |

## H5

**not determinable: too few eligible creators (below the minimum of 12)**

- Holm: p entering Holm 1 (the larger of the two versions), Holm-adjusted 1, step 5 of 10 (threshold 0.008333), not passed.
- A10 guard applies (the versions' verdicts agree); it replaces: estimator: half-count difference of log ratios pooled by random effects (registered) -> OE for the Holm p and the Mantel-Haenszel odds ratio as the estimate (A10.4, CAL-A11); reference: sign-flip of half-count values, 9,999 draws (registered) -> sign-flip of OE, exact up to 20 creators (A10.1, A10.4); minimum: 10 hits per group and side (registered) -> 10 per group, the margin only (A10.4); interval: creator bootstrap (creators, then recordings, R1) of the pooled half-count estimate (registered) -> for A5 both the t interval on OE and the MH log odds ratio's interval, the wider of the creator-bootstrap percentile and the jackknife t interval until the coverage repeat (A10.7; registry 04:55 (j), 06:44 (5)).
- Uninformative: yes (the verdict is not determinable).
- VG-6: Gate VG-6 (the other-vendor read of the voice label, registry 2026-11-21 03:21) concerns H1, H4 and H6 only.
- Reliability gates on R-hold (A10.5), not passed: sentence codes fail gate C on R-hold: the H5 group kept in all 5 runs 0.816 [90% 0.757, 0.867] against the floor 0.85 (A10.5); their gate D passes (kappa 0.695 [0.617, 0.759]); voice passes; title codes kept as the record under the owner's decision of about 00:30 UTC (A10.5 exception, not extended), reported with their failed gates and adjudication figures: R-hold C presentation 0.870 [0.805, 0.930] against 0.90, D presentation 0.630 [0.453, 0.787] against 0.70, D source family 0.659 [0.414, 0.853] against 0.60 (0.50); the large model decided about 29 percent of hold-out titles.

| Version | Verdict | Eligible creators | p entering the guard | Estimate [90% creator interval] | Scale | Uninformative |
|---|---|---|---|---|---|---|
| amended | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | 1 (by rule: the version is not determinable) | not published (the result is not determinable) |  | yes |
| registered | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | 1 (by rule: the version is not determinable) | not published (the result is not determinable) |  | yes |

- Labels were produced by language models from frozen prompts; no person has checked them (A8). The estimate is model-coded.
- Titles: the gate failed (presentation kappa 0.45, stability 0.87; floors 0.70, 0.90); by the owner's decision the middle model is the record and the largest model decides every title on which middle and small disagree. Own-voice talks and channelled sessions are made for different occasions: the difference is voice plus occasion.
- Verification (A11, registry 03:08): verified by a third model (voice label: gpt-6-sol with guided steps against the OpenAI readers' majority on claimed, own and other voice, kappa 0.79 (90% 0.61 to 0.90), agreement 87.6%, 200 seen check units of 23 creators weighted to 5,896 units (VER-3R); a third model of the same vendor, not a person; the sentence codes had no third-model reading (their second reading, registry 04:55, was by the middle model)), on known-answer texts (sentence codes: primary code exact 1.00 (1.00 to 1.00), small and middle model, 310 planted prototypes of 20 creators (a ceiling); voice revision 3, middle model (hold-out record), 30 creators: region accuracy 0.96 (0.94 to 0.98), claimed recall 0.97 (0.95 to 0.99) on embodied and 0.93 (0.88 to 0.96) on relayed passages, claimed precision 1.00 (0.99 to 1.00); titles: presentation exact, middle model 1.00 (0.99 to 1.00), adjudicated form 0.996 (0.988 to 1.000), 240 constructed titles in 12 lists; source family was not planted (constructed texts; an upper bound for the corpus, not accuracy on it; KA battery)) and by a reader of another vendor (voice label: an Anthropic model reading blind with ten units of context on each side against the OpenAI readers' majority on claimed, own and other voice, kappa 0.91 (90% 0.84 to 0.95), 200 seen check units of 23 creators (gate VG-6, registry 04:59); no person checked any label; no reader of another vendor read the sentence codes or the title codes).

Robustness rows (robust to the labeller: yes (read from the published rows only; rows resting on fewer than 5 creators are not counted)):

| Row | Verdict | Uninformative |
|---|---|---|
| Q2 merged with Q1 (sensitivity A: world = Q1 + Q2) | not determinable: too few eligible creators (below the minimum of 12) | yes |
| Q2 excluded (units coded Q2 left out) | not determinable: too few eligible creators (below the minimum of 12) | yes |
| sensitivity B: world = Q1 + Q2, practice + Q3 | not determinable: too few eligible creators (below the minimum of 12) | yes |
| sensitivity C: practice + Q8 | not determinable: too few eligible creators (below the minimum of 12) | yes |
| sensitivity D: a secondary code counts half | not determinable: too few eligible creators (below the minimum of 12) | yes |
| relaxed minimum: 5 per group | not determinable: too few eligible creators (below the minimum of 12) | yes |
| registered per-side minimum (10 per group and side) | not determinable: too few eligible creators (below the minimum of 12) | yes |
| units next to a self-naming cue kept (before M9) | not determinable: too few eligible creators (below the minimum of 12) | yes |
| titles: middle model without adjudication | not published: rests on fewer than 5 creators | |
| titles: small model without adjudication | not determinable in both versions (amended: too few eligible creators (below the minimum of 12); registered: too few eligible creators (fewer than 5 of 12)) | yes |
| recognizer model stratified: other and unknown models included (registry 03:08) | not determinable: too few eligible creators (below the minimum of 12) | yes |

## H6

**not determinable: too few eligible creators (below the minimum of 12)**

- Holm: p entering Holm 1 (the larger of the two versions), Holm-adjusted 1, step 6 of 10 (threshold 0.01), not passed.
- A10 guard applies (the versions' verdicts agree); it replaces: estimator: creator mean of half-count log rate ratios (registered) -> OE = (a - sum_i T_i s_i)/T, centred per recording, for the Holm p and the Mantel-Haenszel rate ratio with creator-by-recording strata as the estimate (A10.4, CAL-A11; registry 06:44 (3)); reference: sign-flip of half-count log ratios (registered) -> the mean OE over creators with T >= 1, p the larger of its cluster-level conditional Monte Carlo p (asks within 5 units of each other chain into one cluster, registry 12:52 (1); each cluster in the claimed voice with the recording's claimed share s_i) and the creator sign-flip p of OE (A10.4; registry 11:08 (1), amending 09:19 (1)); minimum: 12 creators with both voices (registered) -> also 8 or more with T >= 1 (A10.4); interval: creator bootstrap (creators, then recordings, R1) of the mean log ratio (registered) -> for A5 both the t interval on OE and the MH interval, the wider of the creator-bootstrap percentile and the jackknife t interval until the coverage repeat (A10.7; registry 04:55 (j), 06:44 (5)).
- Uninformative: yes (the verdict is not determinable).
- VG-6: Gate VG-6 passed (kappa 0.91): no cap applies (registry 2026-11-21 03:21).
- Reliability gates on R-hold (A10.5), passed: voice (record: middle model on the small map; R-hold, A10.5): A 0.995 of all calls (record configuration 0.996; map stage alone 0.972, flagged: a per-stage reading would fail A); B claimed quotations 0.997; C claimed/own/other same in 5 runs 0.920 [0.839, 0.989] against 0.90 (0.80); D kappa middle against small claimed/own/other 0.832 [0.692, 0.929] and embodied/own/other 0.815 [0.679, 0.909] against 0.60 (0.50); VG-6 passes (0.91 [0.84, 0.95]); asks (R-hold, A10.5): A 1.000; B find quotations 0.972; C pay-or-enrol stability not published (it rests on fewer than 5 creators); it passes its floor of 0.75; D critics' specific agreement on pay-or-enrol 0.833 [0.706, 0.938] against 0.60 (0.50); E relative recall not published (it rests on fewer than 5 creators); it passes its floor of 0.80.

| Version | Verdict | Eligible creators | p entering the guard | Estimate [90% creator interval] | Scale | Uninformative |
|---|---|---|---|---|---|---|
| amended | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | 1 (by rule: the version is not determinable) | not published (the result is not determinable) |  | yes |
| registered | not determinable: too few eligible creators (below the minimum of 12) | below the minimum of 12 | 1 (by rule: the version is not determinable) | not published (the result is not determinable) |  | yes |

- Labels were produced by language models from frozen prompts; no person has checked them (A8). The estimate is model-coded.
- The voice label responds to punctuation and case.
- Verification (A11, registry 03:08): verified by a third model (voice label: gpt-6-sol with guided steps against the OpenAI readers' majority on claimed, own and other voice, kappa 0.79 (90% 0.61 to 0.90), agreement 87.6%, 200 seen check units of 23 creators weighted to 5,896 units (VER-3R); a third model of the same vendor, not a person), on known-answer texts (voice revision 3, middle model (hold-out record), 30 creators: region accuracy 0.96 (0.94 to 0.98), claimed recall 0.97 (0.95 to 0.99) on embodied and 0.93 (0.88 to 0.96) on relayed passages, claimed precision 1.00 (0.99 to 1.00); asks, union find: planted asks found 0.98 (0.97 to 0.99), kept as pay-or-enrol 0.97 (0.96 to 0.98), planted non-asks kept as asks 0.01 (0.00 to 0.03); 400 planted asks of 41 creators (constructed texts; an upper bound for the corpus, not accuracy on it; KA battery)) and by a reader of another vendor (voice label: an Anthropic model reading blind with ten units of context on each side against the OpenAI readers' majority on claimed, own and other voice, kappa 0.91 (90% 0.84 to 0.95), 200 seen check units of 23 creators (gate VG-6, registry 04:59); no person checked any label).
- H6's detectable effect comes from the simulation battery (run.py simulate), whose results are not on file.

Robustness rows (robust to the labeller: yes):

| Row | Verdict | Uninformative |
|---|---|---|
| second model (small against middle) | not determinable in the amended version: too few eligible creators (at least the minimum of 12; creators with an ask below the minimum of 8) (registered version: not determined (Holm step)) | yes |
| rule A (offer ends a claimed voice) | not determinable: too few eligible creators (below the minimum of 12) | yes |
| strict own voice | not determinable: too few eligible creators (below the minimum of 12) | yes |
| labels as the model gives them (rule A, strict) | not determinable: too few eligible creators (below the minimum of 12) | yes |
| claimant cannot_tell admitted | not determinable in the amended version: too few eligible creators (at least the minimum of 12; creators with an ask below the minimum of 8) (registered version: not determined (Holm step)) | yes |
| recognizer model stratified: other and unknown models included (registry 03:08) | not determinable: too few eligible creators (below the minimum of 12) | yes |

## H9

**not determinable in both versions (amended: too few eligible creators (fewer than 5 of 8); registered: the family-label permutation cannot reach the first Holm step (eligible creators: fewer than 5; the number of distinct labelings is not published))**

- Holm: p entering Holm 1 (the larger of the two versions), Holm-adjusted 1, step 9 of 10 (threshold 0.025), not passed.
- A10 guard applies (the versions' verdicts agree); it replaces: minimum: none besides a reference that can reach the first Holm step (registered) -> also 8 hold-out creators with a cell, the one-sided minimum (A10.2, CAL-A9).
- Uninformative: yes (the verdict is not determinable).
- VG-6: Gate VG-6 (the other-vendor read of the voice label, registry 2026-11-21 03:21) concerns H1, H4 and H6 only.
- Reliability gates on R-hold (A10.5), passed: flagged: title codes kept as the record under the owner's decision of about 00:30 UTC (A10.5 exception, not extended), reported with their failed gates and adjudication figures: R-hold C presentation 0.870 [0.805, 0.930] against 0.90, D presentation 0.630 [0.453, 0.787] against 0.70, D source family 0.659 [0.414, 0.853] against 0.60 (0.50); the large model decided about 29 percent of hold-out titles; feature files: deterministic, 297 hold-out files of features-4 written by the features.py that freeze 2 pins (no floor).

| Version | Verdict | Eligible creators | p entering the guard | Estimate [90% creator interval] | Scale | Uninformative |
|---|---|---|---|---|---|---|
| amended | not determinable: too few eligible creators (fewer than 5 of 8) | fewer than 5; minimum 8 | 1 (by rule: the version is not determinable) | not published (the result is not determinable) |  | yes |
| registered | not determinable: the family-label permutation cannot reach the first Holm step (eligible creators: fewer than 5; the number of distinct labelings is not published) | fewer than 5; no minimum | 1 (by rule: the version is not determinable) | not published (the result is not determinable) |  | yes |

- Labels were produced by language models from frozen prompts; no person has checked them (A8). The estimate is model-coded.
- Titles: the gate failed (presentation kappa 0.45, family 0.49; floors 0.70, 0.60); record as for H5. A title names the being a recording is published under, not who speaks in a span.
- Verification (A11, registry 03:08): verified by a third model (title codes: the large model decides every title on which the middle and small models disagree (owner, about 00:30); on G it sided with the middle model on 46 of 55 disputed family codes, and middle against large on disputed presentation codes gave kappa 0.85 (0.75 to 0.92), with gpt-6.2-sol; production uses gpt-6-sol; the VER-3R figure covers the voice label only), on known-answer texts (titles: presentation exact, middle model 1.00 (0.99 to 1.00), adjudicated form 0.996 (0.988 to 1.000), 240 constructed titles in 12 lists; source family was not planted (constructed texts; an upper bound for the corpus, not accuracy on it; KA battery)) and by a reader of another vendor (no reader of another vendor read the title codes; VG-6 covers the voice label only).

Robustness rows (robust to the labeller: not assessable: every robustness row rests on fewer than 5 creators):

| Row | Verdict | Uninformative |
|---|---|---|
| without the title-and-opening agreement rule | not published: rests on fewer than 5 creators | |
| councils without a star name (S8) not specific | not published: rests on fewer than 5 creators | |
| within one tradition: star peoples (ET) | not published: rests on fewer than 5 creators | |
| within one tradition: angels, masters, deities (AD) | not published: rests on fewer than 5 creators | |
| each family's 100 most distinguishing words deleted | not published: rests on fewer than 5 creators | |
| titles: middle model without adjudication | not published: rests on fewer than 5 creators | |
| titles: small model without adjudication | not published: rests on fewer than 5 creators | |
| recognizer model stratified: other and unknown models included (registry 03:08) | not published: rests on fewer than 5 creators | |

## Checkability on the hold-out: the large model against the record

The large model (gpt-6-sol) re-read 300 hold-out statements against the middle model (the record of checkability), after the hold-out labels were made (Cohen's kappa over the three codes YES, NO and CANNOT_TELL, and the share of statements given the same code, both weighted by the inverse of the sampling probability; 95% cluster-bootstrap intervals (creators, then recordings)): time window 0.742 [0.548, 0.872] (agreement 0.940); named actor 0.781 [0.491, 0.940] (agreement 0.967); observable outcome 0.761 [0.557, 0.912] (agreement 0.953); place not published (its YES codes rest on fewer than 5 creators; its disagreements between the two readings come from fewer than 5 creators); quantity not published (its disagreements between the two readings come from fewer than 5 creators); all five parts the same in 0.839 [0.781, 0.902] of statements. This is agreement between two models of one vendor, not accuracy. Checkability is kept as the record under the owner's 00:30 exception (A10.5); its gates on R-hold are under H2.

## Counts written before the outcomes (counts.json)

ASR-model rule: applied; required recognizer model english_only. Figures whose creators are fewer than 5, or not counted, are withheld.

| Source | Group | Creators | Recordings | Kept | Excluded | Creators with an excluded recording | Other model | Unknown model | Conflicting sources | Cross-check mismatch |
|---|---|---|---|---|---|---|---|---|---|---|
| primary | holdout | withheld | 297 | withheld | withheld | fewer than 5 | 0 | withheld | 0 |  |
| primary | seen | 71 | 1293 | 1284 | 9 | 9 | 0 | 9 | 0 |  |

Hold-out cross-check against the resolved recognizer model (primary, holdout): checked 297; agree withheld; disagree 0; not in table 0; table states none withheld.

Asks of one class on overlapping unit ranges, counted once (registry 2026-11-21 12:52 (2)): holdout: asks merged away withheld, ask files with a merge withheld, groups withheld; seen: asks merged away withheld, ask files with a merge withheld, groups withheld.

A withheld figure rests on fewer than 5 creators, or on creators that counts.json does not count, or would give such a figure by subtraction from a printed one; the reasons are listed under "Withheld".

## Source

- report.json sha256 `b5b0e3a00a7bbda5679c56da263c0bcc5f003a29a96bbdaf3258e0ce73d48da5` (written 2026-11-21T19:03:30Z)
- report.md sha256 `a83b84b4f4770f9ca3c031f36664e34496a5a7f69cb197659bfebaf652711802`; counts.json sha256 `7859ff768435f528bca8f38c6c03c51b49b64542d21ea431b503c5df1750bdbf`
- analyse config sha256 `0f7f62475f07c89d112c076cbfd624e608e7893dcd18f53a3edd9358487cec3f`
- freeze-2 record (llm/freeze2.json) sha256 `5ef43dd88164f5389c48ece8b08d639d6e3b6464173b63fea3db7ad68effb008`, written 2026-11-21T16:10:00Z; registry commit `941a55623f509dfbb4fa5b2f98bd281dd870e930`
- analysis code: the 22 module hashes the report records match freeze 2 (digest `9cbeb773a6a64b7300c605e54de67421289e53c583ded138fff46011fa77551f`; constants.py `cf54452896a51e5b779bb5e624cebe775f24fbc4d32414a43322eebd97f05c89`)
- published 2026-11-21T23:33:53Z by publish_results.py (sha256 `30efe82334e18920748799f21ef320a635d9a106e272379fefb30079cac016a0`)

## Withheld under the rules of the public outputs

- cohort: hold-out creators in the label sources (beside the public counts of hold-out creators (23, of whom 6 have non-English transcripts) it would show the creators with transcripts in both, fewer than 5)
- H1 amended version: estimate and its 90% creator interval (the result is not determinable)
- H1 registered version: estimate and its 90% creator interval (the result is not determinable)
- H2 amended version: estimate and its 90% creator interval (the result is not determinable)
- H2 amended version: p entering the guard (the result is not determinable)
- H2 registered version: estimate and its 90% creator interval (the result is not determinable)
- H2 registered version: p entering the guard (the result is not determinable)
- H2 gates: the R-hold figure of checkability quantity, gate D (it rests on fewer than 5 creators (positive codes or disagreements, over the statements it reads))
- H4 amended version: estimate and its 90% creator interval (the result is not determinable)
- H4 registered version: estimate and its 90% creator interval (the result is not determinable)
- H5 amended version: estimate and its 90% creator interval (the result is not determinable)
- H5 registered version: estimate and its 90% creator interval (the result is not determinable)
- H6 amended version: estimate and its 90% creator interval (the result is not determinable)
- H6 registered version: estimate and its 90% creator interval (the result is not determinable)
- H6 gates: C pay-or-enrol stability (it rests on fewer than 5 creators (the asks not found in all but one run, over the R-hold items it reads))
- H6 gates: E relative recall (it rests on fewer than 5 creators (the accepted asks one finder missed, over the R-hold items it reads))
- H9 amended version: estimate and its 90% creator interval (the result is not determinable)
- H9 registered version: estimate and its 90% creator interval (the result is not determinable)
- ASR-model rule, holdout: creators (beside the public counts of hold-out creators (23, of whom 6 have non-English transcripts) it would show the creators with transcripts in both, fewer than 5)
- ASR-model rule, holdout: kept (with the recordings it gives the excluded count, whose creators are fewer than 5 or not counted)
- ASR-model rule, holdout: excluded (it rests on fewer than 5 creators)
- ASR-model rule, holdout: excluded_unknown_model (the number of creators behind it is not recorded in counts.json)
- ASR-model rule, holdout: agree (with the checked count it gives the other cells, whose creators are not counted)
- ASR-model rule, holdout: table_states_none (the number of creators behind it is not recorded in counts.json)
- checkability on the hold-out (the large model against the record): place (its YES codes rest on fewer than 5 creators; its disagreements between the two readings come from fewer than 5 creators)
- checkability on the hold-out (the large model against the record): quantity (its disagreements between the two readings come from fewer than 5 creators)
