# Corrections of 2026-11-21 to the frozen texts and the superseded paper draft

Written 2026-11-21, 19:30 UTC (clock: `date -u`). The second-round analysis panel listed corrections to six public
documents (its digest, section 4, items A to F). The lead adopted them under the owner's delegation (registry row of
2026-11-21 03:08 UTC: "the section-4 corrections go into one docs PR that says the lead's review stands in for the
owner's"). This note covers the three places that are not edited:

- [`hypotheses.md`](hypotheses.md) and [`registry.md`](registry.md) are frozen (the registry holds the SHA-256 of
  the hypotheses text), so neither is rewritten. Each correction is listed here with the place where the registry
  already records it.
- The paper draft of 2026-11-20 ([`../../paper/cohort-draft-2026-11-20/`](../../paper/cohort-draft-2026-11-20/README.md))
  is superseded by the measurement-and-protocol paper of 2026-11-21 and is kept as written. Its corrected statements
  are listed here.

The other corrections are applied in place: the [analysis catalogue](README.md) (items B1 to B7), the
[results of the registered hypotheses](results/README.md) (C1 to C6), the findings dashboard (F1 to F4) and the
note on the recording-dates CSV of the collection timeline (F5). Section 5 lists the changes made in place after the
pre-publish verification of the same day (B8 to B24, C7 to C12, D1); section 6 is an item for the owner.

"Registry" below means `registry.md` as it stands on the analysis branch `feat/partial-cohort-asr-2026-11-20`, where
the rows of 2026-11-21 and amendment A10 were entered before freeze 2; this repository's main branch has the registry
as frozen on 2026-11-20 and receives the later rows when that branch is merged. Every number here is a cohort-level
value on the creators seen before the freeze (exploratory, panel round 2) unless a line says otherwise.

## 1. The hypotheses text (`hypotheses.md`, frozen)

| Where | Frozen wording | Correction | Where the registry records it |
|---|---|---|---|
| Section 14.4 (rejected), the line on the first half of H7 | "The first half of H7 (near pairs more alike than far pairs) as a test: close to certain from shared news and season." | On seen creators the near-date resemblance is small (exploratory description): anchor-matched, recordings within 3 days against 14 to 60 days apart, +0.0010 cosine (90% interval -0.0009 to +0.0030; 66 creators); +0.0020 on exact days only. It is not run as a test until its margin is set from the seen creators. | A10.6: the anchor-matched contrast is H7's estimator, the near-against-far contrast S stays a description with its block band and is not tested, and H7 is not run in the first round (decision of 04:55 (h); row of 16:06 (1)). The value +0.0010 is the panel's and is not in the registry. |
| H2, "Confirmed on": "Not run" below 8 creators | minimum 8 creators with 30 statements | The minimum is 9: with 8 creators the smallest two-sided sign-flip p is 2/256 = 0.0078, above the first Holm step. | A10.3 ("H2's minimum is 9 creators with 30 verified statements, not 8"), under the guard, so the registered version is computed beside it. |

## 2. The registry (`registry.md`, frozen entries)

| Where | Frozen wording | Correction | Where the registry records it |
|---|---|---|---|
| H3 freeze table, row "Interval procedure" | "its coverage has not been audited (the coverage audit CA has not run)" | Audited afterwards on seen creators: at nominal 90% the two-stage percentile interval covered 0.894 (sets of 12 creators) and 0.889 (17), and the t interval on creator means 0.913 and 0.913. The frozen entry stands as the record of what was run. | A10.7, "Why" (CAL's audit at 12 and 17 creators; the t interval on creator means came closest to nominal), and the deviation table, row 2026-11-20 20:38 (percentile bootstrap chosen because the audit had not run). The coverage figures themselves are the panel's. |
| Header table, "Smallest effects of interest": the H7 placeholder | the placeholder 0.01 for H7, "set from the seen creators before their tests" | The panel proposed stating H7's margin in units of its own estimator's spread under the 28-day-block reference on seen creators: SD 0.0007 cosine (0.0010 on exact days only), so 0.01 is about 14 SD. Not adopted in that form. | A10.6 (decision of 04:55 (i)): the margin is k x SD_L, with SD_L and k fixed before any wave recording is collected and k not fixed now; the placeholder 0.01 is kept and a verdict must hold against both margins. H7 is not run in the first round. At hold-out size the SD would be about twice as large; that is an assumption from square-root scaling, not a measurement. |
| H3 reading, seen creators (also C1) | raw trimmed contrast 0.019 read as "no contrast" | The contrast's no-effect value under its own reference is -0.063; recentred, the seen value is 0.083 (90% t interval -0.046 to 0.211; creator sign-flip p 0.15), not distinguishable from zero at creator level. Under a creator-level placebo on sets of 17 seen creators the registered shift test rejected at its nominal 0.5% in 1.3% of sets (2.0% at 8 creators). | A10.7 point 3 (example H3: "recentred, its seen value moves from 0.019 to 0.083"; the registered verdict is unchanged), the guard of A10, and the row of 03:08 (paper wording "supported by the registered rule; not determined at creator level (exploratory)", with the recentred value and the placebo rate). H3 stays dropped (A6). |

## 3. The superseded paper draft of 2026-11-20 (not edited)

| Item | Statement in the draft (`main.tex`) | Corrected fact |
|---|---|---|
| A1 | "Dates and duplicates": 36 selected recordings have no row in the published date table (`\NNoDateRow`) | Every selected recording has a row. The CSV writes the 36 ids that begin with a hyphen with a leading apostrophe; read without it, they join like every other id. Local time stamps confirm 142 of the 397 intervals, so 1,721 recordings have a confirmed day and 255 keep an interval (median width 32 days). |
| A2 | Abstract: the bridge shows that word-based measures agree between the models | They agree on average, on English recordings of 5 to 60 minutes; single recordings differ by up to about half a between-creator SD; pause and filler measures do not agree; nothing is said about other languages. |
| A3, A8 | The inserted thanks phrase (`\ThanksPct` and the macros beside it), on a snapshot that included hold-out audio | On the 1,284 English transcripts of the 71 seen creators, a stand-alone thanks phrase starts in the last 3 s of a 30-second decoding window in 49.9% of transcripts (55.6% hold one somewhere); window-phase counts attribute at least 94.9% of those end-of-window segments to the recognizer. The base is the seen transcripts (registry, 03:08). |
| A4 | SY row: near against far pairs, dates permuted within creator | Anchor-matched near (within 3 days) against far (14 to 60 days) pairs, names and date words masked; dates permuted within 28-day blocks of each creator, with the within-creator permutation as a second band. |
| A5 | Bridge section: the measures "agree" | They agree on average. For single recordings the limits of agreement are -0.51 to +0.46 between-creator SD for pace and -0.44 to +0.55 for word length in letters, and 5 of the 36 recordings differ by more than the margin on pace. Leaving out any one recording changes none of the 13 settled verdicts, and an exact signed-rank interval gives the same seven agreements. |
| A6 | Comparisons across languages may read word-based measures | English recordings transcribed by the two models may be compared on the seven word-based measures on average. The bridge makes no measure comparable across languages. Pause measures are used inside one model only and after the seam rule (the capped, weighted rule; registry, 03:08): the 30-second decoding grid makes about 3.0% of pauses of 0.3 to 30 s and 2.5% of pause time. |
| A7 | "Recognizer confidence follows delivery" (pooled Spearman 0.49, `\RhoLogpPace`) | Correlations are stated at two levels. Pace with the share of time without speech: -0.37 across channels, -0.34 within. Mean segment log-probability with pace: 0.54 between creators and 0.43 within (the pooled 0.49 lies between them); mean word log-probability with pace: 0.11 across and 0.10 within. |
| A9 | Limitations: the bridge allows pace, pronoun and vocabulary measures to be read across the two models | It shows mean agreement on English audio only; it takes the model out of a language comparison but not language or creator, so other languages remain description. |
| A10 | Rule R1 and the limitation "coverage has not been audited" | A mean of creator values gets the t interval on creator means (coverage 0.885 to 0.915 at nominal 0.90 in the seen-creator audit at 12 and 17 creators); the two-stage bootstrap is a sensitivity row (A10.7). |
| A11 | H3 | See section 2, row "H3 reading". |
| A12 | "No artefact filter has been applied" (the findings section and the limitations) | Stale: the H3 test and the bridge used the artefact filter (version 1). The draft's descriptive numbers were computed without it. |

## 4. The public bridge file

[`results/br-bridge.json`](results/br-bridge.json) printed the smallest and the largest word disagreement of the 36
pairs, each one recording's own value. Both fields were removed from the public copy on 2026-11-21; the file says so in
`word_disagreement.public_form`. The code `code/br_bridge.py` is unchanged, because its SHA-256 is the record of the
registered run: a rerun would write both fields again and must be stripped the same way before it is published.

## 5. Changes after the pre-publish verification of 2026-11-21

Written 2026-11-21, 21:37 UTC (clock: `date -u`). An adversarial check of the public outputs before the first-round
results were published found cells of fewer than five creators, single-creator and single-recording extremes and
stale result states in three of the documents covered here. They are changed in place as follows. The rules applied
are the owner's rules of the public outputs: no figure, cell or bin rests on fewer than 5 creators; no two printed
creator counts of nested groups differ by 1 to 4, also against counts already public; no statistic rests on fewer
than 5 creators with a non-zero value; nothing per creator or per recording. No change adds a new number: each removes,
pools or restates a number that was printed, or cites one that the findings dashboard already publishes.

**The analysis catalogue ([`README.md`](README.md)).**

| Item | Where | Was | Now | Why |
|---|---|---|---|---|
| B8 | Status paragraph | status of 20 November evening: H3 and the bridge have run | status of 21 November: the first round of registered tests has run (five not determinable, one not run for want of an instrument, model-coded), with a link to the first-round results file | stale result state |
| B9 | 2.1, Selected recordings | each of the five creators with fewer than 20 selected recordings given with its own count | "five have fewer" | per-creator counts |
| B10 | 2.1, Language | a row per language, the non-English rows resting on fewer than 5 creators | English, and the other languages pooled (12 files of the five creators of 2.5, item 5) | cells of fewer than 5 creators; the dashboard pools them the same way |
| B11 | 2.1, Window of the newest 20 | the shortest and the longest span per creator | median only | each bound is one creator's value |
| B12 | 2.2, length, words and pace rows | the longest recording, the most words in a recording, the range of pace over recordings | removed; the counts of recordings of 5 minutes or less and over 60 minutes stay, since each holds more than 80 recordings and so, at 20 per creator, five or more creators | each bound is one recording's value |
| B13 | 2.2, question share | the count of recordings that reach 20% | removed | it may rest on fewer than 5 creators |
| B14 | 2.2, other counts: creator medians | the smallest and largest creator median of pace, length and non-speech share, and of words per creator | removed; the dashboard's 10th and 90th percentiles over the seen creators on the finished run are cited instead | each bound is one creator's value |
| B15 | 2.2, other counts: duplicates | exact counts of shared audio files, re-uploads and files with identical filler, and the range of the filler's length | "a few" | cells of fewer than 5 creators |
| B16 | 2.2, window-level pilot; LX pilot | two pilot creator counts that lie 1 to 4 from the 71 seen creators | "about 70" | the groups may be nested in or hold the 71 |
| B17 | SD, data and unit | the pilot's count of these creators, which lies 1 to 4 from the 71 | all but fewer than 5 of the 71 seen creators | nested in the 71 (10 or more transcripts) |
| B18 | 2.3, kinds of the read sample | six kinds, some of them resting on fewer than 5 creators | the channelled kind and the other kinds pooled (17 and 17) | cells of fewer than 5 creators; the dashboard pools them the same way |
| B19 | 2.3 and SG; section 6 | the exact number of read recordings with real audience questions | "few of the 42" | fewer than 5 creators |
| B20 | 2.3, names of beings; translated views | the range of spellings of one name in one recording; the most repeats in a translated view | "several spellings"; "long runs of repeats" | each bound is one recording's value |
| B21 | 2.4 | clips and hours of the earlier study's channeler in this cohort | "too little of that channeler's speech" | a per-creator row for an identifiable creator |
| B22 | 2.5, item 4; T1-1; EB | the shortest and longest window in days and years; the longest file and its speech minutes | "from days to years"; a log axis of days; "a file of several hours can hold only minutes of speech" | each is one creator's or one recording's value |
| B23 | CX-7 | combinations of name families with at least 2 creators | at least 5 creators (R15) | a planned public cell of fewer than 5 creators |
| B24 | LG, data and unit; pitfalls | creators per language; the creators of one language | "four languages, each spoken by fewer than five of them"; "creators who share a language" | cells of fewer than 5 creators |

**The results of the registered hypotheses ([`results/README.md`](results/README.md)).**

| Item | Where | Was | Now | Why |
|---|---|---|---|---|
| C7 | Table, rows H1, H2, H4, H5, H6, H9 | "not run", "waits for model labels" | run in the first round on 2026-11-21, with the verdicts, eligible counts, Holm-adjusted p and uninformative flags as [`first-round-2026-11-21.md`](results/first-round-2026-11-21.md) states them (model-coded); a paragraph above the table links that file | stale result state; it contradicted the results file and the dashboard |
| C8 | Table, rows H7 and H10 | "waits for the replication wave" | not run, with the reasons the results file and the registry give (no replication wave exists; A4, decisions of 04:55 (h) and (m)); each enters Holm at p = 1 | the first round's wording |
| C9 | Table, row H3 | verdict "supported" | "passed its registered rule (supported by it); not determined at creator level"; withdrawn (A6) | the dashboard's and the registry's wording (row of 03:08) |
| C10 | H3, the positional rule | displays by position "show the seen creators only until freeze 2" | stated in the past, with the time of freeze 2 | freeze 2 has passed |
| C11 | H3, decision | "one tested, none claimed so far"; "the hypotheses not yet run" | H3 tested, then the six of the first round run, none claimed; "the hypotheses run after H3" | stale result state |
| C12 | BR | the exact count of the seen creators the spread comes from, which lies 1 to 4 from the 71 | the seen creators with three or more recordings, all but fewer than 5 of the 71 | nested in the 71 seen creators |

**The public bridge file ([`results/br-bridge.json`](results/br-bridge.json)).**

| Item | Where | Was | Now | Why |
|---|---|---|---|---|
| D1 | `between_creator_sd_from.creators_with_three_or_more_recordings` | the exact count, an integer | "all but fewer than 5 of the 71 seen creators", with a `public_form` note in the same block | as C12; no script reads this field, and `code/br_bridge.py` is unchanged |

The findings dashboard's README needed no change for these findings. The first-round results file and its JSON twin
live on the analysis branch `feat/partial-cohort-asr-2026-11-20`; the links to them in the catalogue and in the results
README resolve on this repository's main branch once that branch is merged.

## 6. For the owner: registered result files that print a nested pair

- [`results/h3-holdout.json`](results/h3-holdout.json), H3's registered result on main (commit `ccbd62f`), prints, beside the registered test's counts, the counts of the untrimmed contrast that was reported beside the test. Under the rules of the public outputs those counts would be stated against the registered test's counts. Changing a registered result file whose hash is cited is the owner's decision; until then the results README and the dashboard print only the registered test's counts and the untrimmed U.
- [`results/h3-seen-exploratory.json`](results/h3-seen-exploratory.json) and the frozen H3 entry of the registry
  ("Seen creators, exploratory") print the seen pair in the same way: 61 creators for the trimmed contrast and, for
  the untrimmed one, a count fewer than 5 higher. The dashboard writes that count as "61 and fewer than 5 more".
- Neither file is edited here. Each is the record of a registered run that the registry and the results README cite,
  and the registry is frozen, so changing a registered result file needs the owner's decision. The options are: (a)
  in the public copies, replace each untrimmed creator count by its form against the trimmed one ("17 and fewer than
  5 more", "61 and fewer than 5 more") with a `public_form` note, as was done for the bridge file in sections 4 and 5;
  (b) drop the untrimmed blocks from the public copies and keep only U as the results README prints it; or (c) keep
  the files as the record and accept the pairs.
