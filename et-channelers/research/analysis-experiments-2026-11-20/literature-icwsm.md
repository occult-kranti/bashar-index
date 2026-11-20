# ICWSM methods digest for the channelers corpus

Written 2026-11-20 for the analysis panel. Read-only study: nothing in the worktree or the private archive was changed, no transcript text was read or sent anywhere, and every web query used general research terms only.

Reference keys: `R01`-`R41` are ICWSM papers, `N1`-`N10` are neighbouring sources. The full list with URLs and how each was read is in section 8.

## 0. What was done, and how far to trust it

- **Scope.** How papers at the International AAAI Conference on Web and Social Media (ICWSM), 2017 to 2026, do statistics and data analysis on text and video-platform corpora, and what this project can reuse.
- **Volume.** 32 ICWSM papers read in full text. 9 more ICWSM papers known only from an abstract or a search snippet. 10 neighbouring sources (two Pew Research Center methodology pages, a podcast corpus paper, three methods papers, others).
- **How they were read.** The proceedings site (ojs.aaai.org) refuses direct fetching. Five papers were read from the proceedings PDF through a scraping service until its daily allowance ran out. The other 27 were read from the authors' arXiv version in HTML; the ICWSM venue was confirmed from the arXiv comment field or from the proceedings listing found in search.
- **Limit 1: automated reading.** Each paper was read by an automated extractor that answered fixed questions about the full text. I did not page through the PDFs by eye. Numbers below are as the extractor reported them. Re-check any number against the PDF before it goes into a paper. Where the extractor found an inconsistency inside a paper, I pass it on.
- **Limit 2: arXiv versions** can differ from the proceedings versions.
- **Limit 3: pitfalls.** I did not see review reports. "Pitfalls" below come from the papers' own limitation sections and from gaps the reading found (a missing effect size, no correction, one validator).
- **Not found.** No ICWSM paper on channelling, mediumship, prophecy, failed predictions, astrology or new-age communities turned up in four separate searches. That is a gap in the literature, not proof of absence.

## 1. Corpus facts that decide what transfers

Counted today from `sync\edition_asr_manifest.jsonl` and `provisioning\claude-cohort-asr-20261120-v1\proposal.json`. The transcription run is still writing, so the manifest numbers are a snapshot.

| Fact | Value |
|---|---|
| Recordings in the run plan | 1,976 from 101 creators; 2 to 20 per creator, median 20; 2 creators have fewer than 10 |
| Source of text | 1,731 need speech-to-text; 214 already had English text; 1 had a language review; 30 have no audio |
| Finished transcripts (snapshot) | 1,233 rows at the last count and rising; in the first 1,230 rows: 95 creators, median 17 per creator, 24 creators with fewer than 5 finished so far |
| Hours finished (first 1,230 rows) | 519 hours; median recording 17.3 minutes; deciles 3.3, 6.6, 10.1, 13.4, 17.3, 23.3, 30.1, 42.9, 58.2 minutes |
| Short and long | 193 of 1,230 under 5 minutes (16%); 108 over 60 minutes (9%) |
| Languages (first 1,230 rows) | English 1,219 recordings from 90 creators; Japanese 4 (2 creators); Spanish 3 (1); Portuguese 3 (1); Czech 2 (1) |
| Review state | every finished transcript is marked `unreviewed_asr` |
| Upload dates | not present in the manifest or the proposal; not checked elsewhere |

Four consequences, used throughout this digest:

1. **The unit that carries inference is the creator** (about 100), not the recording (about 1,950) and not the word. Every ICWSM paper that got this right resampled or clustered at the account level (`R18`, `R21`, `R06`, `R07`).
2. **"Newest 20 per creator" is a quota sample.** Each creator has near-equal weight in recordings, but the calendar span of 20 recordings differs by creator. Cohort-level calendar trends are confounded with how often a creator posts.
3. **Language is confounded with creator.** At the snapshot there are 12 non-English recordings from 5 creators. No test of "language" is possible; only case descriptions and a within-recording check of original against translation.
4. **Recording length spans a factor of 17 between the first and ninth decile.** Rates must use words or speech minutes as the denominator, and short recordings need their own stratum.

## 2. Findings the panel needs

1. **The existing plan is stricter than the ICWSM norm on inference.** Many read papers report p-values without effect sizes (`R24`, `R27`, `R31`, `R26`), run many tests without correction (`R08`, `R10`, `R17`, `R26`), or test at the post level. The plan's Holm families, Benjamini-Hochberg sets, cluster bootstrap and equivalence tests can stay as they are.
2. **Where ICWSM papers are ahead of the plan is presentation and validation routine:** a coverage table, a precision-by-threshold table, a balance plot, an event-study plot, a coefficient plot, small multiples per account. Section 4 lists each figure with a paper that uses it.
3. **Speech-to-text error is usually admitted and rarely measured.** `R24` measured it on 9,860 lectures and found group differences; the podcast corpus `N1` measured 3.0% word error by hand on 18 episodes; `R25`, `R02` and `R03` name the problem and give no number. A measured error table by stratum would put this project ahead.
4. **Machine labels need a per-task human check, and the check needs more than one coder.** Across 27 tasks, GPT-4 had median F1 0.71 with a range of 0.06 to 0.97 (`R23`). Several papers validated with a single expert (`R11`, `R12`, `R14`, `N6` for 350 of 600 items).
5. **Narrative clusters from sentence embeddings, with a similarity threshold validated by hand, are now the standard way to track "the same story" across sources** (`R11`, `R12`, `R14`, `R15`). The threshold must be validated per language: at 0.7, precision was 85.2% for English pairs and 49.2% for Russian pairs (`R12`).
6. **For borrowing between accounts, four designs exist:** first-appearance tables (`R12`), Hawkes processes (`R12`), transfer entropy with shuffled series (`R15`), and lead scores against a token-swap null (`R16`). With at most 20 recordings per creator, only first-appearance counts with a shuffle null are feasible here.
7. **Quasi-experimental designs do not fit the newest-20 cohort.** Interrupted time series, difference in differences and regression discontinuity all need many observations on both sides of a date, in many units. They fit the long archives named in the existing plan, not this cohort. A feasibility count comes first (section 3.9).
8. **Keyness should be counted per creator, not per token.** Pew's sermon study counted a church once if a term appeared in any of its sermons, and dropped terms used by fewer than 4% or more than 95% of churches (`N5`). `R18` counted each word once per user.
9. **Religion and conspiracy papers handle labels and ethics with care worth copying:** one paper removed 15 items after a scholar from another tradition judged them acceptable there (`R32`); several release only derived labels and quote nothing verbatim (`R01`, `R05`, `R16`).
10. **The prediction and prophecy strand has no ICWSM template.** The plan's dated-statement families would be new at this venue.

## 3. Method cards

Each card gives: the question, the statistic or model, the standard figure or table, pitfalls, papers, and what to reuse here.

### 3.1 Describing the corpus: coverage, skew and sampling bias

- **Question.** What is in the corpus, how was it selected, and how does selection distort averages?
- **Statistic.** Counts by stratum. Skewed quantities on a log axis with median and quartiles. Share of a total held by the top 5%. Items with and without transcripts, by group. Inverse-probability weights when a ranking of the population exists.
- **Figure or table.**
  - Dataset table as Table 1 (nearly every paper).
  - Box plots plus log histograms with the top-5% share written on the plot: the top 5% of videos held 86.9% of views (`R29`).
  - Complementary cumulative distribution of comments per user (`R30`); cascade size (`R08`).
  - Videos with and without transcripts by group: 4,678 of 5,435 political videos and 100,582 of 150,843 news videos had transcripts (`R02`, Tables 14-16).
  - A coverage-gap table per show (`R03`, Table 2).
  - Moving average with and without sampling weights: mean videos per channel fell from 699.78 to 559.26 after weighting (`R29`).
- **Pitfalls.** Averages over items let prolific accounts dominate. Missing transcripts are not missing at random. Sampling by popularity over-represents amplified content (`R01` says so). Several papers have numbers that disagree between sections (`R29`, `R31`, `R14`, `R02`), which a second script recomputing every table would catch.
- **Papers.** `R29`, `R30`, `R02`, `R03`, `N1`.
- **Reuse here.** One coverage sheet: per creator, recordings planned, finished, hours, speech hours, non-speech share, language, text source (speech-to-text or existing text), missing audio. A log-axis histogram of recording length with the 5-minute and 60-minute marks. A strip per creator showing the calendar span of its recordings, once upload dates are joined.

### 3.2 Transcript quality as a measured variable

- **Question.** How wrong are the transcripts, for which strata, and do the errors move results?
- **Statistic.** Word error rate = (substitutions + deletions + insertions) / reference words, on a hand-checked sample, by stratum. Median by group with Kruskal-Wallis (`R24`). Split into the three error kinds. Diarization error. Share of text removed by a repetition filter.
- **Numbers reported.**
  - 9,860 lecture videos, about 8,740 hours, 332 speakers. Median error for YouTube captions against Whisper base.en: 13.6% against 9.6% (female speakers), 14.5% against 11.9% (male). Error between the two systems correlates at r = 0.81 per lecture. Kruskal-Wallis at alpha 0.001 (`R24`).
  - 1.1 million podcast episodes transcribed with Whisper base.en. Hand-checked error 3.0% on the first five minutes of 18 episodes. Automated comparison gave 8 to 9% because professional transcripts drop disfluencies. A 4-gram repetition filter removed about 11% of the data. Diarization token error 1.8% (`N1`).
  - Topic vectors from noisy transcripts stayed usable but similarity to reference fell as noise rose (`N7`, abstract only).
- **Figure or table.** Box plots of error by attribute (`R24`, Fig. 3). Histogram of error (`R24`, Fig. 1). Error by show (`N1`). A table of medians with test statistic (`R24`, Table 3).
- **Pitfalls.** `R24` reports no effect sizes and no correction, and infers speaker attributes from names. `R25` calls its transcripts noisy and reports no error rate. `R02` says it found no systematic bias in topic extraction and shows no test. `R03` lists transcription, diarization and classifier error and checks 100 samples per show.
- **Reuse here.** The plan's gate M1 already asks for error per stratum. Add three things the stored fields allow:
  1. Per recording, the mean and the 10th percentile of segment log-probability, and the non-speech share. Plot hand-measured error against mean log-probability for the gold sample (a calibration plot). If the relation is tight, log-probability becomes a quality covariate for all 1,946 recordings.
  2. Rerun each headline result on the better-quality half and report both.
  3. Report the share of segments dropped by a repetition filter, per creator.

### 3.3 Labels from models and from people: agreement and validation

- **Question.** Can a label be trusted enough to count, and how does its error move the estimates?
- **Statistic.** Human against human: Krippendorff's alpha or Cohen's or Fleiss' kappa. Model against human: precision, recall, F1 per label on a held-out sample. Stability: share of repeated runs that agree.
- **Numbers reported.**
  - A workflow: 250 human-labelled items to tune the prompt, then 1,000 held-out items to score it. Over 27 tasks from 11 studies: median F1 0.71, range 0.06 to 0.97; 9 tasks had precision or recall below 0.5; recall beat precision in 20 of 27. A consistency score (at least five runs at temperature 0.7, share matching the modal label): items at 1.0, about 85% of annotations, had accuracy higher by 19.4% as reported (`R23`).
  - Religious videos: codebook from 100 pilot videos; alpha 0.86 (narrative), 0.83 (visual), 0.91 (comment gold set), 0.84 (comment check on 1,000). Items that differed across three model runs went to people (`R01`).
  - Cable shows: two authors on 500 pairs, kappa 0.81; a crowd round failed (Fleiss kappa 0.302, alpha -0.005) and was replaced (`R03`).
  - Pseudoscience videos: crowd kappa 0.14, then 0.24 after dropping 915 videos (13.8%) where all three annotators disagreed. Every positive from the classifier was checked by hand and the prevalence called a lower bound (`R28`).
  - Conspiracy videos: three crowd workers per video, Fleiss kappa 0.41 (`R27`).
  - Wellness influencers: two coders on 250 posts with kappa at least 0.6; model F1 at least 0.6 on 600 posts, 350 of them labelled by one coder (`N6`).
  - Stance toward politicians: 74% accuracy on 65 transcripts (`R02`).
  - Of 48 studies using supervised text classifiers, 85% reported precision or recall, 19% said misclassification could bias results, and 1 corrected for it. Error that depends on a covariate can bias a regression in either direction (`N2`).
- **Figure or table.** Precision against recall, one dot per task (`R23`, Fig. 2). Per-label precision, recall, F1 table. Accuracy by bucket of predicted probability (`R30`, Fig. 4). Consistency against accuracy (`R23`, Fig. 4).
- **Pitfalls.** Agreement measured on a pilot and not on the final codebook. Low kappa followed by business as usual (`R28`, `R27`). A validation set labelled by one person. Dropping disagreed items, which biases prevalence. Accuracy on unbalanced classes. Error that differs by group.
- **Reuse here.** The plan has alpha gates and prediction-powered estimates. Add: a consistency score as the rule for sending items to people; error tables split by creator group, by recording length band and by language, with a test of whether error depends on the covariates used later (`N2`, step 2); precision and recall shown separately, since recall above precision inflates counts.

### 3.4 Topic models and narrative clusters, and how they are validated

- **Question.** What is talked about, in what proportions, and are the topics real?
- **Approaches found.**

| Approach | Details reported | Validation reported | Paper |
|---|---|---|---|
| LDA, K = 200, on the first 1,000 words per episode | 1.1 million episodes | none stated | `N1` |
| BERTopic, 80 topics grouped into 15 categories | 21,000 episodes | coherence 0.689 | `R03` |
| Model writes a topic label per transcript, k-means on labels, people merge | over 100,000 transcripts | two researchers: 90% of videos had correct themes, 74% had all relevant ones; similarity 0.75 within theme, 0.66 between | `R02` |
| Sentence embeddings, UMAP, HDBSCAN | 1,056 topics; 33.7% of sentences left as outliers | one expert, 4,095 sentences in 25 topics, precision 98.9% | `R11` |
| Sentence embeddings, DP-means at cosine 0.8 | 29,875 clusters over 4.09 million texts | 250 pairs per threshold per language | `R12` |
| k-means on averaged word vectors, K by silhouette and Davies-Bouldin | K = 30 | none beyond the indices | `R08` |
| Multilingual contextual topic model, 50 topics, 15 kept | 1 million tweets | intrusion test: accuracy 0.731, alpha 0.67 | `R10` |
| Word-similarity graph plus Louvain, after LDA and biterm models were rejected for low coherence | 3,700 short texts | none | `R31` |
| Online agglomerative clustering at 0.85 | 2 million posts | 93.2% of top weekly clusters matched documented events | `R14` |

- **Threshold tables.** Precision at cosine 0.4, 0.5, 0.6, 0.7 was 92.6%, 95.6%, 98.3%, 99.8% for matching comments to clusters (`R11`). At 0.8: 99.2% English, 89.2% Russian, 89.6% mixed; at 0.7: 85.2%, 49.2%, 62.4% (`R12`). Agreement by threshold from 0.60 to 0.80: 74%, 86%, 90%, 94%, 98% on 50 pairs each (`R15`).
- **Figure or table.** Top themes by period (`R02`, Tables 1-4). Episodes per topic (`R03`, Fig. 8). Topics per channel over time (`R03`, Fig. 9). Two-dimensional map of channels by theme mix (`R02`, Figs. 2-3). Precision by threshold (`R11`, Table 6; `R12`, Table 2). Share of items matched against threshold (`R11`, Fig. 7).
- **Pitfalls.** Coherence scores alone. One validator. A large outlier share dropped without comment. Topics fitted on the first N words only. One topic per sentence or per document assumed (`R11`; `R02` found only 74% completeness). Thresholds that work in one language and fail in another. `R15` gives three different threshold values in one paper.
- **Reuse here.** Fit on windows, not whole recordings: a median recording is 17 minutes and holds several themes. Report the unassigned share per creator. Validate with an intrusion test by two raters and a precision-by-threshold table per language. Use two levels of topics. Show a creator-by-topic heat map (section 5, item 2).

### 3.5 Keyness and distinctive vocabulary

- **Question.** Which words mark one group of creators against another?
- **Statistics found.**
  - Weighted log-odds with an informative Dirichlet prior: top 100 domains or hashtags per language against all, after removing the 200 most common overall and anything seen fewer than 10 times (`R10`); a target window against a reference with the whole corpus as background (`R13`); with a general English background to pick topic keywords, then a sweep over matching thresholds (`R27`).
  - Specificity as pointwise mutual information, log of a word's frequency in a community over its frequency in all communities; each word counted once per user; nouns only; top 5% of words by frequency (`R18`).
  - Sparse additive generative model for the 500 most distinctive keywords, checked by hand (`R22`).
  - Ratio of shares: share of churches in a tradition using a term over the share outside it; a church counts if the term appears in any of its sermons; terms used by fewer than 250 churches (4%) or more than 95% are dropped (`N5`).
  - Largest change between the first and last 12 months, as a table (`R21`, Table 4).
  - Attribution from a classifier that separates two sources, top 10 tokens per class (`R17`).
- **Figure or table.** Ranked term tables per group. Example words placed by specificity and volatility (`R18`, Fig. 1A).
- **Pitfalls.** Token-level tests overstate evidence. Names of people and beings dominate the lists. Frequency cut-offs are arbitrary and rarely varied. No intervals or significance reported (`R10`, `N5`). In transcripts, misspelt coined names create false distinctive terms.
- **Reuse here.** Keep the plan's weighted log-odds with recordings or creators resampled. Add the creator-count version as the headline table: a term counts for a creator if it appears in at least 2 of that creator's recordings; drop terms used by fewer than 4% or more than 95% of creators; show both lists side by side. Merge spelling variants of coined names before any keyness run.

### 3.6 Comparing groups: tests, effect sizes, corrections

- **Question.** Is a difference between groups larger than chance, and how large?
- **What the papers do.**

| Test | Effect size | Correction | Paper |
|---|---|---|---|
| Chi-squared with Cochran's rule checked | Cramér's V; table shows only V above 0.1 | Bonferroni | `R01` |
| Kruskal-Wallis, alpha 0.001 | none | none | `R24` |
| Two-sample Kolmogorov-Smirnov on style counts | none | none | `R31` |
| Wilcoxon rank-sum between outlet categories | percentage points | Bonferroni | `R21` |
| Mann-Whitney U | rank-biserial 0.60, 0.46, 0.34 | not stated | `R15` |
| Mann-Whitney U | none, no p shown | none | `R27` |
| Mann-Whitney U on originating topics | means | Bonferroni, p at most 0.005 | `R11` |
| Welch t | percent difference | none | `R03`, `R32` |
| ANOVA with Tukey's test | none | Tukey | `R04` |
| Daily segmented regression plus lexical shifts | standard deviations | Benjamini-Hochberg | `R05` |
| Bootstrap, 95% interval, resampled by community | Spearman rho | Bonferroni on model comparisons | `R18` |
| Bootstrap, 10,000 draws, one video per user per draw | percent difference | none | `R26` |
| Monthly means with bootstrap intervals | none | none | `R20` |

- **Figure or table.** A results table with statistic, degrees of freedom, p, effect size. Box plots or cumulative distributions by group.
- **Pitfalls.** p-values alone. No correction over many outcomes. Posts by one account treated as independent. With millions of items everything is significant. A non-significant result read as "no difference" (`R28`).
- **Reuse here.** No change to the plan's tests. Adopt one table format for every comparison: effect size, 95% interval, number of creators and number of recordings on each side, and the correction family. The bootstrap of `R26` (one item per account per draw) is a simple way to give creators equal weight when their recording counts differ.

### 3.7 Nested data: recordings inside creators

- **Question.** How to estimate an effect when observations cluster in accounts?
- **Models found.**
  - Negative binomial with a random intercept per account for weekly post counts; multilevel beta regression for a 0-to-1 score; Bayesian fit with 95% credible intervals (`R07`).
  - Linear probability model with outlet fixed effects, a separate linear trend per outlet category, and standard errors clustered by outlet; 989 outlets, about 6.7 million quotes (`R21`).
  - User fixed effects with errors clustered by user (`R06`).
  - Users inside counties, about 5.9 million users in 1,784 counties (`R36`, abstract only).
  - In a multiverse study, a logistic mixed model gave fewer estimates crossing zero than a regression on group-level aggregates (`N3`, case 3).
- **Figure or table.** Coefficient plot with intervals (`R07`, Fig. 7; `R09`, Figs. 4-5; `R06`, Fig. 3). Regression table.
- **Pitfalls.** Ignoring the clustering. Too few clusters for clustered errors. Random slopes left out. Fits that fail and are not reported (`N3`). `R07` describes random slopes in the text and shows random intercepts in the equations.
- **Reuse here.** About 100 creators with up to 20 recordings each supports a random intercept per creator. Random slopes over time will be weak. For rates per 10,000 words: negative binomial with log words as offset and a creator intercept. For shares: beta or fractional logit. For any creator group with fewer than 10 creators: no model; show the creators as dots.

### 3.8 Change over time

- **Question.** Does a measure rise, fall, jump or change meaning?
- **Statistics found.**
  - Least-squares slope on a monthly series, and Welch t between periods; 24 shows, 2010 to 2024 (`R03`).
  - Linear trend per outlet category, in percentage points per year, with outlet fixed effects (`R21`).
  - Monthly means with 95% bootstrap intervals, no trend test (`R20`).
  - Change points: offline detection averaged over several cost functions and settings, with standard deviation mostly under one day (`R09`); a classifier asked to tell "before" from "after" at each trial date, recursive, minimum segment four days (`R13`).
  - Volatility: log of a word's frequency this month over its frequency across the community's whole history; averaged into "dynamicity", which correlated with monthly retention at rho = 0.70 over 283 communities (`R18`).
  - Weekly bigram language models; cross-entropy of newcomers' text under the core users' model; cosine distance to weekly centroids, in a narrow band of about 0.66 to 0.74 (`R05`).
  - Mean of 1 minus cosine between contextual embeddings of the same keyword in two sources, per year (`R17`).
  - Aligned word embeddings to follow a theory's neighbourhood over time, 2012 to 2022 (`N8`, abstract only).
  - Three-day rolling averages with 95% bands around one news event (`N1`, Fig. 3).
- **Figure or table.** Line with a band. Small multiples, one panel per show or community (`R03`, Figs. 10-13; `R20`, Fig. 1; `R09`, Fig. 3). Event marks on the time axis (`R14`, Fig. 3; `R16`, Fig. 2).
- **Pitfalls.** A change in who is in the sample read as a change within units; unit fixed effects or centring fix it (`R21`). One actor driving the trend: without its most-quoted speaker, `R21`'s overall rise was no longer significant. Gaps in coverage (`R03`). Seasonality. A trend described in words with no test (`R20`). Embedding distances that move with word position (`R17`).
- **Reuse here.** For the cohort, use order within creator (recording 1 to 20), not calendar time: a Theil-Sen slope per creator, pooled with a random-effects mean, plus a leave-one-creator-out plot. Calendar-month panels only for months to which at least 20 creators contribute. The distinctiveness and dynamicity pair of `R18` transfers directly (section 5, item 3).

### 3.9 Event studies and quasi-experiments

- **Question.** Did a dated event or rule change move a measure, beyond what would have happened anyway?
- **Interrupted time series.**
  - `R04`: y ~ k + m·t + H(t)·(k_A + m_A·t), with extra terms per user cohort; four dramatic events; two months each side; outcomes are engagement and dictionary categories; ANOVA with Tukey's test.
  - `R05`: y_t = b0 + b1·t + b2·D_t + b3·P_t on a daily standardised series; one event; a level drop of 1.14 standard deviations; survival curves for four newcomer cohorts; inactivity windows of 15, 30 and 60 days as a check. No placebo date.
  - `R22`: forecast from the pre-period compared with the actual series, for 120 communities. Equation, window and treatment of autocorrelation are not stated.
  - `R33` (abstract only): interrupted series and regression discontinuity around an interface change.
- **Difference in differences.**
  - `R06`: one-to-one propensity matching on eight covariates; standardised mean differences under 0.10 shown in balance plots; user fixed effects; four-week bins with the four weeks before as reference; errors clustered by user; other matching methods as a check. No placebo and no formal test of parallel trends.
  - `R07`: coarsened exact matching then Mahalanobis distance; negative binomial with account intercepts; parallel trends judged from group trend coefficients; a Wilcoxon signed-rank test as a second route. Posts by blocked accounts fell 21.4%; toxicity did not move.
  - `R09`: log pageviews ~ year × period × language, with the same calendar window of the previous year as control; the event date per language is a detected change point; five weeks each side.
  - `N4`: stacked design over 165 events and 101 people, controls are people not yet treated, leads and lags with month -3 as reference, errors clustered by person. Attention fell 63% (95% interval 46% to 75%) on one measure after 12 months.
- **Regression discontinuity.**
  - `R08`: y = m·x + b + beta·1{x > x0} on the daily normalised use of each of the top 10,000 hashtags; polynomial degree chosen by information criteria; no bandwidth; no correction across hashtags.
  - `R34` (abstract and snippet only): discontinuity around a policy date, with structural topic models for the discourse.
- **Propensity stratification.** `R10`: 25 strata, standardised differences under 0.1, effect on the treated, robust errors, repeated over 232 network subsets; the summary is the share of subsets with a significant positive effect.
- **Figure or table.** Event-study plot of leads and lags with intervals (`R06`, Fig. 3; `N4`, Fig. 7). Balance plot before and after matching (`R06`, Fig. 5; `R07`, Fig. 4). Scatter with fitted segments either side of the date (`R04`, Fig. 4; `R05`, Fig. 2; `R08`, Fig. 6). Survival curves (`R05`, Fig. 5). Coefficients across several set-ups (`R09`, Fig. 4).
- **Pitfalls.** Dates chosen after looking at the series. Other events at the same time (`R05` and `R08` say so). A spike just before the date (`N4`, month -1). Autocorrelation ignored in least-squares fits. No placebo dates (`R05`, `R06`, `R09`). Regression to the mean (`N4` discusses it). The event itself changing attention (`N4`).
- **Reuse here.** Mostly not for this cohort. A creator has at most 20 irregular time points, all recent. Before any dated design, run a feasibility count: for each candidate date, the number of creators with at least 5 recordings before and 5 after. The plan's fixed dates (2012, 2020, 2023) lie outside the newest-20 window of most creators; those tests belong to the long archives. `R09`'s "same weeks last year" control needs deeper history than this cohort has. What does transfer: the event-study plot and the balance plot as formats, and the rule of naming dates before looking.

### 3.10 Borrowing and diffusion between accounts

- **Question.** Does wording or a storyline move from one account to another, and who leads?
- **Designs found.**
  - **First appearance.** Share of each site's topic clusters that appeared first elsewhere: 13.9% of website topics first appeared on Telegram, 33.2% of Telegram topics first appeared on websites (`R12`, Table 6). Count of topics a site originated and how many outside articles followed (`R11`, Tables 2-3; Mann-Whitney with Bonferroni; correlations 0.41 to 0.58).
  - **Hawkes processes.** One process per source (17), daily counts for each of 29,875 clusters, fitted by Gibbs sampling. Outputs: a background rate (which also absorbs sources not in the data), a weight (expected extra mentions on B per mention on A), and the delay shape. Summaries: percent of a source's content attributable to another, and efficiency. No intervals reported (`R12`).
  - **Transfer entropy.** Direction between two platforms per narrative, tested against 1,000 shuffles of the source series at the 95th percentile; an origin needs a 24-hour lead; at least 10 posts on the receiving side. 1,552 narratives moved; 238 passed the test (`R15`).
  - **Lead score with a null.** Word-level lead from one community to another from time- and community-specific embeddings; kept only if above the 95th percentile of 100 data sets with tokens swapped between communities; 65 persistent communities merged into 12 groups (`R16`).
  - **Granger tests.** Monthly series, lags 1 to 12, stationarity checked, 18 tests with no correction (`R17`). Daily series, lags 1 to 5, the lag with the lowest p reported (`R26`). Author to narrative, then lagged rank correlations above 0.3 (`R14`).
  - **Membership flows.** Parent weight of a new community = share of its first 100 members active in the parent in the month before (`R19`). Yearly migration matrices in two normalisations with a random baseline of 100 draws (`R20`). Overlap matrices with a bootstrapped random baseline of 1,000 draws (`R20`).
- **Figure or table.** Source-by-source influence matrix (`R12`, Figs. 4-5). Similarity matrix among sources (`R12`, Fig. 2). Network with node size by weighted out-degree (`R11`, Fig. 4). Sankey diagram of leadership (`R16`, Fig. 5). Genealogy graph (`R19`, Fig. 2c). Delay distributions in days (`R12`, Figs. 6-7).
- **Pitfalls.** An outside cause (a news event) looks like influence. Daily resolution. "First" depends on which sources were collected (`R12` sampled only channels the websites linked to). Choosing the best lag after the fact. No uncertainty on Hawkes weights. Shared genre formulas inflate similarity. Granger tests on trending series.
- **Reuse here.** The plan's Q2 uses a matrix permutation regression on shared distinctive passages. Add a cluster-level view: narrative clusters across creators, a first-appearance table per creator, and a creator-by-creator lead matrix. Use a shuffle null (permute dates within creator, 1,000 times) for the lead counts. Compare a pair of creators only inside the calendar window both cover, because under "newest 20" a lead can simply mean one creator's window reaches further back. Hawkes fitting with about 100 processes and at most 20 events each is too sparse to report. All of this needs upload dates.

### 3.11 Conspiracy, religion, wellness and prediction content

- **What exists.**
  - Religious videos on YouTube: 1,100 videos from 820 creators, audio transcribed by a model, narrative and persuasion strategies coded and cross-tabulated by religion with chi-squared, Cramér's V and Bonferroni (`R01`).
  - Circulators of fabricated religious sayings: 559 accounts against 559 debunkers; a classifier on who they follow, retweet and like reached 87.6% macro F1; a scholar from another tradition reviewed the top 62 items and 15 were removed as acceptable there; the paper avoids the word "disinformation" and releases no data (`R32`).
  - Conspiracy videos: 596,967 videos from 1,912 channels with transcripts; 3,161 labelled by crowd workers at Fleiss kappa 0.41; "Extraterrestrials/UFOs" is one of the four largest topics among labelled conspiracy videos; the authors say labels depend on annotators' beliefs (`R27`).
  - A canonical text and its copies: six aggregator sites compared as raters (Fleiss kappa below 0 overall, 0.24 without one site); style features per posting identity compared with Kolmogorov-Smirnov tests (`R31`).
  - Conspiracy communities after dramatic events (`R04`, `R05`).
  - Pseudoscience videos (`R28`).
  - Sermons: 49,719 sermons from 6,431 churches over eight weeks, transcribed automatically; words counted per church; the authors could not always separate the sermon from the rest of the service; no texts or church names released (`N5`).
  - Health and wellness influencers: 535,512 posts by 6,334 accounts; speech detected, then transcribed; only the first five minutes of each YouTube video; a 13-topic codebook applied by a model (`N6`).
  - Podcasts: in a 1.1-million-episode corpus, Religion is the largest category (`N1`, Fig. 10).
- **What does not exist at ICWSM, as far as four searches show.** Channelled messages; prophecy and dated predictions; what speakers say after a predicted date passes; astrology or new-age communities.
- **Pitfalls.** Truth labels that depend on a tradition. Annotators' beliefs. Quoting believers. Spotlighting small communities.
- **Reuse here.** The plan's banner (claims reported as claims) matches `R32`'s stance. The style comparison of `R31` is a simple descriptive companion to the plan's register tests: per voice, distributions of sentence length, vocabulary richness, digits and punctuation, compared within a creator. `N5`'s problem of separating the sermon from the service is this project's problem of separating channelled speech from introductions, music and adverts; the time stamps and non-speech figures let this project measure it.

### 3.12 More than one language

- **What the papers do.**
  - Validate the language detector: on 1,000 tweets per country in 32 countries, the platform's detector agreed best with five other tools (alpha 0.824) (`R10`).
  - Validate thresholds per language (`R12`, section 3.4 above).
  - Translate everything to English first and say nothing about the effect (`R13`).
  - Use multilingual sentence embeddings (`R12`, `R14`, `R15`).
  - Admit that English queries bias the sample (`R01`).
  - One methods paper found machine translation adequate for bag-of-words models and LDA on one parliamentary corpus (`N9`, known from a search summary only).
- **Pitfalls.** Language confounded with country, platform or account. Translation that normalises style. Mixed-language items.
- **Reuse here.** With 1 or 2 creators per non-English language at the snapshot, compare languages descriptively only: place each non-English creator as a marked dot on the English creators' distribution for every measure. Run one measurement study inside recordings: for each non-English recording, compare original and translation on topic assignment, the top distinctive terms, and embedding position. The sample size is the number of non-English recordings, to be recounted when the run ends. State in every caption that "language" here means "these five creators".

### 3.13 Robustness sections

- **What the papers vary.**
  - Similarity thresholds (`R11`, `R12`, `R15`), keyword-match thresholds (`R27`, Fig. 2), inclusion thresholds for channels and users (`R26`, Fig. 4).
  - Matching method (`R06`). Window length (`R05`). Model class (`R32`: two other classifiers; `R13`: a second learner).
  - Leaving out the most influential actor (`R21`).
  - Labelled-only subset (`R08`, Fig. 7). Polynomial degree (`R08`). Seasonality terms (`R21`).
  - Synthetic data with a planted signal and rising noise: change-point detection held until a noise ratio of about 0.8 (`R13`).
  - A rerun months later: the audit of `R28` in a second period; the same model in April and November, F1 +0.022 (`R23`).
  - A multiverse: 144, 324 and 960 specifications in three case studies; a specification curve with a panel of the choices beneath, and a mark for fits that failed (`N3`).
- **Pitfalls.** Checks that only confirm direction. No placebo. Failed fits not reported. A multiverse so large it includes poor specifications.
- **Reuse here.** The plan already has a specification curve. Add: leave-one-creator-out for every pooled estimate; a mark on the curve for every specification that failed to run; a second run of the coding model on the control set at the end of the project.

### 3.14 Ethics, data statements and limitations

- **The venue's checklist.** A 2024 template exists, adapted from other venues' checklists. It asks whether the authors read the ethics guidelines, whether new datasets will be findable, accessible, interoperable and reusable, and whether a datasheet was written (`N10`, from a search summary). Papers read here answer it in an appendix (`R03`, `R25`, `R26`, `R32`, `R16`). Two answers were found to contradict the paper's own text (`R32` marks societal impact as not applicable while discussing privacy threats; `R25` reports no misuse potential).
- **What is released.**
  - Derived labels and aggregate statistics only; no raw comments; no video files (`R01`).
  - Nothing (`R32`).
  - Video ids and labels; comment text obtainable again through the platform; commenters anonymised (`R27`).
  - No comment text; random user ids; comments only for videos with more than 30 commenters (`R29`).
  - A trained model in place of per-user labels, citing limits on political-opinion data (`R30`).
  - Transcript text of public political videos (`R25`).
  - Research-only access, with removal on a creator's request (`N1`).
- **Quoting and naming.** No verbatim quotes (`R01`, `R05`). Paraphrases checked for traceability (`R16`). Named accounts limited to the top five per community that are public and have at least 3,000 followers (`R16`). Only public figures named (`R13`).
- **Ethics review statements.** Exempt (`R13`); approved with a reference number (`R27`); approved (`R26`, `R28`, `R32`); "public data only" with no review stated (`R06`, `R07`, `R12`, `R30`).
- **What limitation sections list.** One platform and language. Tool error (transcription, toxicity scorers, embeddings). Observational, not causal. Selection of accounts. A short window. No audience side.
- **Reuse here.** The plan's private and public split is stricter than most of these. Add: a datasheet; a table of transcript availability by creator group; a written distinction between creators (public speakers) and audience members who ask questions (private persons, never quoted, never named); a removal route for creators.

## 4. Figure and table inventory

| Figure or table | What it answers | Paper | Use here |
|---|---|---|---|
| Dataset table with counts by stratum | What is in the corpus | all | Creators, recordings, hours, speech hours, words, by language and text source |
| With and without transcript, by group | Is missing text related to group | `R02` | Planned, finished, missing audio, existing text, by creator group |
| Log histogram or box plot with top-5% share | How skewed | `R29` | Recording length; words per creator; share of all dated statements from the top 5% of creators |
| Complementary cumulative distribution | How heavy the tail | `R30`, `R08` | Recordings by length; named beings by number of creators naming them |
| Box plots of error by stratum | Is transcription worse for some | `R24` | Error and log-probability by language, length band, format |
| Calibration plot | Does a proxy track the truth | `R30` (bucketed accuracy) | Hand-measured error against mean log-probability; label accuracy against model confidence |
| Precision against recall, one dot per label | Which labels are usable | `R23` | One dot per code in the codebook |
| Precision-by-threshold table | Where to cut similarity | `R11`, `R12` | Per language, for narrative clusters and for passage reuse |
| Group-by-category table in percent, with chi-squared and Cramér's V | Does content mix differ by group | `R01` | Format, speech strategy, theme by entity family |
| Heat map | Who talks about what; which measures move together | `R10` (Fig. S4, correlations between outcomes), `R13` (Fig. 6, robustness grid), `R20` (Fig. 2, overlap matrix with colour). No paper read was confirmed to show an account-by-topic heat map; `R03` Fig. 9 shows topics per channel over time, chart type not confirmed | Creators by topics, rows normalised, rows clustered |
| Two-dimensional map of accounts | Which accounts are alike | `R02`, `N1` | Creators by topic mix, with a quality score per cluster as `R02` does |
| Plane of two language measures | A typology | `R18` | Distinctiveness against dynamicity, one dot per creator |
| Small multiples over time | Per-account trajectories | `R03`, `R20`, `R09` | One panel per creator, recording order on the x-axis |
| Line with bootstrap band | A trend with uncertainty | `R20`, `N1` | Cohort means by recording order |
| Fitted segments around a date | A jump or slope change | `R04`, `R05`, `R08` | Long archives only |
| Event-study plot of leads and lags | Parallel trends and effect timing | `R06`, `N4` | Long archives only |
| Balance plot before and after matching | Are compared groups alike | `R06`, `R07` | Shorts against matched windows of long videos (plan family Y) |
| Coefficient plot with intervals | Many effects at a glance | `R09`, `R07` | Mixed-model coefficients; per-creator slopes as a forest plot |
| Survival curves | Persistence | `R05` | How long a dated statement stays in use before it is dropped or re-dated |
| Source-by-source matrix | Who leads whom | `R12`, `R20` | Creator-by-creator lead counts with a shuffle null |
| Sankey diagram | Flows between groups | `R16` | Which entity family's wording leads which; themes carried from long recordings into short ones |
| Network diagram | Structure of ties | `R11`, `R19`, `N1` | Already planned (networks) |
| Specification curve with choices panel and failure marks | Does a claim survive other choices | `N3` | Every confirmatory result |
| Sensitivity plot against a threshold | Is a cut-off driving the result | `R27`, `R26` | Minimum recordings per creator; similarity cut-offs |
| "Most and least" table | Extremes | `R03` (Table 1), `R21` (Table 4) | Topics with most and least hedging; terms with the largest change between first and last five recordings |

## 5. Proposed additions to the analysis plan

Ranked by value against cost. Items 1 to 6 need only fields already stored (segments, time stamps, log-probability, non-speech seconds, word counts). "Source" names the paper the design comes from; items marked *own* are my proposal, not taken from a paper.

1. **Coverage and quality sheet.** One table and three plots: length histogram (log axis), non-speech share per creator (sorted bars), mean segment log-probability per creator (box plots). Source: `R29`, `R02`, `R24`.
2. **Creator-by-topic heat map.** Windows of fixed word length, two-level topics, share per creator, rows clustered, plus the unassigned share as its own column. Validation: intrusion test by two raters. Source: two-level topics from `R03`, intrusion test from `R10`; the heat-map form itself is *own*.
3. **Distinctiveness and dynamicity plane.** Per creator: mean specificity of its words against all creators, and mean volatility across its own recordings in order. One dot per creator, coloured by entity family. Each word counted once per recording. Intervals by bootstrap over recordings. Source: `R18`.
4. **Format profile from time stamps.** Per recording: speech share, number and length of quiet stretches of 30 seconds or more, words per speech minute, share of time in turns by a second speaker where diarization exists. Cluster recordings into formats (monologue, question and answer, guided meditation, interview); show small multiples per creator. Test format differences across groups with Kruskal-Wallis plus an effect size. Source: *own*, using the non-speech fields; `N5` names the problem.
5. **Position curves.** Normalise each recording to 0-1 and plot where in the recording dated statements, calls to action, product mentions and long silences fall, by format. Source: *own*; `R30` analyses position among comments, `R25` uses time-stamped spans.
6. **Quality calibration.** Hand-measured error on the gold sample against mean log-probability; then every headline result rerun on the better half. Source: `R24`, `N1`, `N7`.
7. **Creator-count keyness.** The `N5` rule next to weighted log-odds; a table of terms that are distinctive under one method and not the other.
8. **Cross-entropy matrix between creators.** A small language model per creator on equal-sized samples of 10-word spans; score every other creator's held-out spans; an asymmetric creator-by-creator heat map; cluster it. Extends the plan's register measure from pairs to the whole cohort. Source: `R18`, `R05`.
9. **Label reliability pack.** Consistency score from five runs, a confidence calibration plot, precision against recall per code, and error tables by creator group, length band and language. Source: `R23`, `N2`.
10. **Mixed models with a forest plot.** Negative binomial with a creator intercept for each dictionary rate; one coefficient plot; leave-one-creator-out beneath it. Source: `R07`, `R21`.
11. **Order-based trends.** Theil-Sen slope over recording order per creator, pooled; forest plot of creators. Source: `R21`, `R03`, adapted to the quota sample.
12. **Narrative clusters and first appearance.** Multilingual sentence embeddings on windows, threshold validated per language on 250 pairs, clusters that at least 3 creators share; per creator, the share of its clusters that it used first; a lead matrix with a date-shuffle null. Needs upload dates. Source: `R11`, `R12`, `R15`, `R16`.
13. **Concentration.** Share of all dated statements, all named beings and all reused passages that come from the top 5% of creators; a Lorenz curve each. Source: `R29`, `R11` (3.9% of users wrote half the matched comments).
14. **Style distributions by voice.** Within creators who voice more than one being: sentence length, vocabulary richness, digits, punctuation, compared with Kolmogorov-Smirnov and an effect size. Source: `R31`.
15. **Language case panel.** Non-English creators as marked dots on every English distribution; a paired original-against-translation check per recording. Source: `R10`, `R12`, `N9`.
16. **Specification curve with failure marks** for each confirmatory result. Source: `N3`.
17. **Feasibility count for dated designs.** For each candidate date: creators with at least 5 recordings each side. Decide from the count whether any event analysis is run on the cohort. Source: `R04`, `R05`, `N4`.

## 6. Checklist of objections to prepare for

Drawn from the limitation sections and reading gaps above.

1. What is the unit of inference, and is every interval resampled at that unit?
2. How many creators are on each side of each comparison?
3. How were creators chosen, and how does "newest 20" shape the time axis?
4. What is the word error rate, by stratum, and do results hold on the better-transcribed half?
5. Which parts of a recording were analysed (speech only; the channelled voice only) and how was that measured?
6. For every model-made label: human agreement, model precision and recall, number of coders, and whether error differs by group.
7. For every topic or cluster: the unassigned share, the validation beyond a coherence score, and the sensitivity to the number of topics or the threshold.
8. For every keyness list: is it counted per creator, are names masked, were cut-offs varied?
9. For every trend: is it within creators, and does it survive leaving out the most influential creator?
10. For every claim of borrowing: what is the null, was the lag chosen in advance, could a common outside event explain it?
11. For every dated design: were dates fixed in advance, is there a placebo date, what else happened then?
12. How many tests are in each family and what correction was used?
13. Is any difference smaller than the measurement shift between text kinds or models?
14. For "language": how many creators per language?
15. What is released, what is quoted, who is named, and how can a creator ask for removal?
16. Is the framing neutral about belief, and are truth labels avoided or tied to a stated standard?

## 7. Gaps and things not verified

- No ICWSM paper found on channelling, prophecy, dated predictions or what follows a failed date.
- No ICWSM paper found that measures how speech-to-text error changes a downstream estimate (a regression coefficient, a topic share). `N7` does it for topic vectors only and was read as an abstract.
- No ICWSM paper found using a specification curve; `N3` is a 2026 preprint from outside the venue.
- The official 2026 submission guidelines were not opened; the checklist description rests on the 2024 template and on the papers' own appendices.
- Papers `R33` to `R41` were not read in full. Their methods are stated here only as far as an abstract or snippet goes.
- Upload dates for this corpus were not located in the two files read, so every proposal that needs dates is conditional on joining them.
- Methods cited inside the papers but not opened in this session are **unverified** here: Monroe, Colaresi and Quinn 2008 (weighted log-odds); Chang et al. 2009 (word intrusion); Gebru et al. 2021 (datasheets); the FAIR principles statement; Cengiz et al. (stacked difference in differences); Linderman and Adams 2015 and Zannettou et al. 2018 (Hawkes fitting and the influence summaries); Del Giudice and Gangestad 2021 (types of analytic decision); Rivers and Lewis 2014 and the Menlo Report (ethics guidance); "WEIRD ICWSM" (arXiv 2406.02090, seen in search results only).

## 8. References

Access: **full** = full text read by automated extraction this session; **abstract** = abstract, search summary or snippet only. Venue for arXiv-read papers was confirmed by the arXiv comment field or the proceedings listing.

### ICWSM papers, full text read (verified)

| Key | Title | Authors | Year | URL |
|---|---|---|---|---|
| R01 | The Digital Landscape of God: Narrative, Visuals and Viewer Engagement of Religious Videos on YouTube | Chen, Xin, Q. Xiao, R. Xiao, J. Xiao, Zhang, Shen, Lu | 2026 | https://ojs.aaai.org/index.php/ICWSM/article/view/42649 |
| R02 | In Times of Crisis: An Exploratory Study of Media and Political Discourse on YouTube During the 2024 French Elections | Sosnovik, Violot, Humbert | 2026 | https://ojs.aaai.org/index.php/ICWSM/article/view/42746 ; https://arxiv.org/abs/2512.17768 |
| R03 | Disagreement Is Disappearing on U.S. Cable Debate Shows | Zaman, Garimella | 2026 | https://ojs.aaai.org/index.php/ICWSM/article/download/42773/50333 |
| R04 | Conspiracies Online: User Discussions in a Conspiracy Community Following Dramatic Events | Samory, Mitra | 2018 | https://ojs.aaai.org/index.php/ICWSM/article/view/15039 |
| R05 | Effects of Mainstream Visibility on Conspiracy Communities: Reddit after Epstein's 'Suicide' | Attanasio, Corso, De Francisci Morales, Pierri | 2026 | https://ojs.aaai.org/index.php/ICWSM/article/view/42631 |
| R06 | Spillover of Antisocial Behavior from Fringe Platforms: The Unintended Consequences of Community Banning | Russo, Verginer, Horta Ribeiro, Casiraghi | 2023 | https://ojs.aaai.org/index.php/ICWSM/article/view/22184 ; https://arxiv.org/abs/2209.09803 |
| R07 | The Effects of Group Sanctions on Participation and Toxicity: Quasi-experimental Evidence from the Fediverse | Colglazier, TeBlunthuis, Shaw | 2024 | https://ojs.aaai.org/index.php/ICWSM/article/view/31316 ; https://arxiv.org/abs/2404.02109 |
| R08 | Characterizing Online Engagement with Disinformation and Conspiracies in the 2020 U.S. Presidential Election | Sharma, Ferrara, Liu | 2022 | https://ojs.aaai.org/index.php/ICWSM/article/view/19345 ; https://arxiv.org/abs/2107.08319 |
| R09 | Sudden Attention Shifts on Wikipedia During the COVID-19 Crisis | Horta Ribeiro, Gligorić, Peyrard, Lemmerich, Strohmaier, West | 2021 | https://arxiv.org/abs/2005.08505 |
| R10 | Bridging Nations: Quantifying the Role of Multilinguals in Communication on Social Media | Mendelsohn, Ghosh, Jurgens, Budak | 2023 | https://ojs.aaai.org/index.php/ICWSM/article/download/22174/21953 ; https://arxiv.org/abs/2304.03797 |
| R11 | Happenstance: Utilizing Semantic Search to Track Russian State Media Narratives about the Russo-Ukrainian War on Reddit | Hanley, Kumar, Durumeric | 2023 | https://ojs.aaai.org/index.php/ICWSM/article/download/22149/21928/26212 ; https://arxiv.org/abs/2205.14484 |
| R12 | Partial Mobilization: Tracking Multilingual Information Flows amongst Russian Media Outlets and Telegram | Hanley, Durumeric | 2024 | https://ojs.aaai.org/index.php/ICWSM/article/view/31332 ; https://arxiv.org/abs/2301.10856 |
| R13 | Discovering Collective Narratives Shifts in Online Discussions | Zhao, Guo, Lerman, Ahn | 2024 | https://ojs.aaai.org/index.php/ICWSM/article/view/31427 ; https://arxiv.org/abs/2307.08541 |
| R14 | Modeling Information Narrative Evolution on Telegram During the Russia-Ukraine War | Gerard, Volkova, Penafiel, Lerman, Weninger | 2025 | https://ojs.aaai.org/index.php/ICWSM/article/view/35834 ; https://arxiv.org/abs/2409.07684 |
| R15 | Bridging the Narrative Divide: Cross-Platform Discourse Networks in Fragmented Ecosystems | Gerard, Hanley, Luceri, Ferrara | 2026 | https://ojs.aaai.org/index.php/ICWSM/article/download/42670/50230/46771 ; https://arxiv.org/abs/2505.21729 |
| R16 | Words and Action: Modeling Linguistic Leadership in #BlackLivesMatter Communities | Roytburg, Olorunisola, Soni, Klein | 2025 | https://ojs.aaai.org/index.php/ICWSM/article/view/35895 ; https://arxiv.org/abs/2412.02637 |
| R17 | Same Words, Different Meanings: Semantic Polarization in Broadcast Media Language Forecasts Polarization on Social Media Discourse | Ding, Horning, Rho | 2023 | https://ojs.aaai.org/index.php/ICWSM/article/download/22135/21914/26198 ; https://arxiv.org/abs/2301.08832 |
| R18 | Community Identity and User Engagement in a Multi-Community Landscape | Zhang, Hamilton, Danescu-Niculescu-Mizil, Jurafsky, Leskovec | 2017 | https://ojs.aaai.org/index.php/ICWSM/article/download/14904/14754 ; https://arxiv.org/abs/1705.09665 |
| R19 | Tracing Community Genealogy: How New Communities Emerge from the Old | Tan | 2018 | https://ojs.aaai.org/index.php/ICWSM/article/download/15003/14853/18522 ; https://arxiv.org/abs/1804.01990 |
| R20 | The Evolution of the Manosphere Across the Web | Horta Ribeiro, Blackburn, Bradlyn, De Cristofaro, Stringhini, Long, Greenberg, Zannettou | 2021 | https://arxiv.org/abs/2001.07600 |
| R21 | Quotatives Indicate Decline in Objectivity in U.S. Political News | Hu, Horta Ribeiro, West, Spitz | 2023 | https://arxiv.org/abs/2210.15476 |
| R22 | Exploring the Magnitude and Effects of Media Influence on Reddit Moderation (arXiv title: Reddit and the Fourth Estate) | Habib, Nithyanand | 2022 | https://ojs.aaai.org/index.php/ICWSM/article/download/19291/19063/23304 ; https://arxiv.org/abs/2111.00084 |
| R23 | Keeping Humans in the Loop: Human-Centered Automated Annotation with Generative AI | Pangakis, Wolken | 2025 | https://ojs.aaai.org/index.php/ICWSM/article/download/35883/38037/39951 ; https://arxiv.org/abs/2409.09467 |
| R24 | A Deep Dive into the Disparity of Word Error Rates across Thousands of NPTEL MOOC Videos | Rai, Jaiswal, Mukherjee | 2024 | https://ojs.aaai.org/index.php/ICWSM/article/view/31390 ; https://arxiv.org/abs/2307.10587 |
| R25 | Misinformation Span Detection in Videos via Audio Transcripts | Matos, Lima, Zannettou, Benevenuto, Santos | 2026 | https://ojs.aaai.org/index.php/ICWSM/article/view/42786 ; https://arxiv.org/abs/2604.21767 |
| R26 | Examining the Role of YouTube Production and Consumption Dynamics on the Formation of Extreme Ideologies | Chandio, Nithyanand | 2026 | https://ojs.aaai.org/index.php/ICWSM/article/view/42645 ; https://arxiv.org/abs/2603.08049 |
| R27 | YouNICon: YouTube's CommuNIty of Conspiracy Videos | Liaw, Huang, Benevenuto, Kwak, An | 2023 | https://ojs.aaai.org/index.php/ICWSM/article/view/22218 ; https://arxiv.org/abs/2304.05274 |
| R28 | "It is just a flu": Assessing the Effect of Watch History on YouTube's Pseudoscientific Video Recommendations | Papadamou, Zannettou, Blackburn, De Cristofaro, Stringhini, Sirivianos | 2022 | https://ojs.aaai.org/index.php/ICWSM/article/download/19329/19101/23342 ; https://arxiv.org/abs/2010.11638 |
| R29 | YouNiverse: Large-Scale Channel and Video Metadata from English-Speaking YouTube | Horta Ribeiro, West | 2021 | https://arxiv.org/abs/2012.10378 |
| R30 | Cross-Partisan Discussions on YouTube: Conservatives Talk to Liberals but Liberals Don't Talk to Conservatives | Wu, Resnick | 2021 | https://arxiv.org/abs/2104.05365 |
| R31 | The Gospel according to Q: Understanding the QAnon Conspiracy from the Perspective of Canonical Information | Papasavva, Aliapoulios, Ballard, De Cristofaro, Stringhini, Zannettou, Blackburn | 2022 | https://ojs.aaai.org/index.php/ICWSM/article/download/19330/19102/23343 ; https://arxiv.org/abs/2101.08750 |
| R32 | Fabricating Holiness: Characterizing Religious Misinformation Circulators on Arabic Social Media | Fawzi, Ross, Magdy | 2026 | https://ojs.aaai.org/index.php/ICWSM/article/view/42665 ; https://arxiv.org/abs/2508.07845 |

### ICWSM papers, abstract or snippet only (existence verified, content not read in full)

| Key | Title | Authors | Year | URL | What was seen |
|---|---|---|---|---|---|
| R33 | To Thread or Not to Thread: The Impact of Conversation Threading on Online Discussion | Aragón, Gómez, Kaltenbrunner | 2017 | https://ojs.aaai.org/index.php/ICWSM/article/view/14880 | Abstract: interrupted time series and regression discontinuity |
| R34 | Changes in YouTube's Content Moderation Policy Had Little Detectable Impact on Election Denial Content | Pisharody, Norton, Greene, Shapiro | 2025 | https://ojs.aaai.org/index.php/ICWSM/article/view/35887 | Abstract summary and a snippet naming regression discontinuity and structural topic models |
| R35 | The Cross-Partisan Voices of Podcasts and Their Social Media Ties | DeMets, Saveski | 2026 | https://ojs.aaai.org/index.php/ICWSM/article/view/42658 | Abstract summary: about 5,000 podcast participants, over 10,000 episodes transcribed |
| R36 | Well-Being Depends on Social Comparison: Hierarchical Models of Twitter Language Suggest That Richer Neighbors Make You Less Happy | Giorgi, Guntuku, Eichstaedt, Pajot, Schwartz, Ungar | 2021 | https://ojs.aaai.org/index.php/ICWSM/article/view/18132 | Search summary |
| R37 | A Two-Year Dataset for Gender and Topic Diversity in Canadian TV News (title cut off in the listing) | Pehlivan and others (full list not retrieved) | 2025 | https://ojs.aaai.org/index.php/ICWSM/article/download/35957/38111/40025 | Snippet: 3,982 videos, 999 hours, transcripts, diarization, topic labels |
| R38 | Harmful YouTube Video Dataset Annotated by Domain Experts, GPT-... (title cut off) | Jo and others (full list not retrieved) | 2025 (inferred from article number) | https://ojs.aaai.org/index.php/ICWSM/article/download/35951/38105/40019 | Snippet: reliability 0.88 by Holsti's index, kappa 0.76 |
| R39 | Analyzing Offensive Content and Emotional Dynamics in Black Lives ... (title cut off) | Okpala and others (full list not retrieved) | 2025 | https://ojs.aaai.org/index.php/ICWSM/article/download/35878/38032 | Snippet: word intrusion used to check topics |
| R40 | Gender Differences in the Global Music Industry (subtitle not retrieved) | Wang, Horvát (as in the listing: "Y Wang") | 2019 | https://ojs.aaai.org/index.php/ICWSM/article/download/3249/3117/6298 | Snippet: log-odds with informative Dirichlet prior on tags |
| R41 | Same Vaccine, Different Voices: A Cross-Modality Analysis of HPV Vaccine ... (title cut off) | not retrieved | 2025 (inferred from article number) | https://ojs.aaai.org/index.php/ICWSM/article/download/35936/38090 | Snippet: text posts, 1,228 audio podcasts and 1,225 videos compared |

Note on `R40`: the second author's name is recalled, not seen in the listing; treat the author list as unverified.

### Neighbouring sources

| Key | Title | Authors | Year | Venue | URL | Access |
|---|---|---|---|---|---|---|
| N1 | Mapping the Podcast Ecosystem with the Structured Podcast Research Corpus | Litterer, Jurgens, Card | 2024 | arXiv preprint (later venue not checked) | https://arxiv.org/abs/2411.07892 | full (first 100,000 characters) |
| N2 | Misclassification in Automated Content Analysis Causes Bias in Regression. Can We Fix It? Yes We Can! | TeBlunthuis, Hase, Chan | 2024 | Communication Methods and Measures | https://arxiv.org/abs/2307.06483 | full (first 100,000 characters) |
| N3 | Making Uncertainty Visible: Multiverse Analysis for Robust Computational Social Science | Linde, Sun, Balluff, Radovanović, Chan | 2026 | arXiv preprint | https://arxiv.org/abs/2605.19745 | full (first 100,000 characters) |
| N4 | Deplatforming Norm-Violating Influencers on Social Media Reduces Overall Online Attention Toward Them | Horta Ribeiro, Jhaver, Cluet i Martinell, Reignier-Tayar, West | 2024 | arXiv preprint (venue not stated on the page) | https://arxiv.org/abs/2401.01253 | full |
| N5 | The Digital Pulpit: A Nationwide Analysis of Online Sermons | Pew Research Center | 2019 | report | https://www.pewresearch.org/data-labs/2019/12/16/the-digital-pulpit-a-nationwide-analysis-of-online-sermons/ | full |
| N6 | What do health and wellness influencers post about: methodology | Pew Research Center | 2026 | report | https://www.pewresearch.org/data-labs/2026/10/07/health-influencers-methodology/ | full |
| N7 | Topic Model Robustness to Automatic Speech Recognition Errors in Podcast Transcripts | Fetic, Jordahn, Lima, Egebæk, Nielsen, Biering, Hansen | 2021 | arXiv preprint | https://arxiv.org/abs/2109.12306 | abstract |
| N8 | Measuring the Semantic Structure and Evolution of Conspiracy Theories | Keim, Chandio, Khalid, Nithyanand | 2026 | arXiv preprint | https://arxiv.org/abs/2603.26062 | abstract |
| N9 | No Longer Lost in Translation: Evidence that Google Translate Works for Comparative Bag-of-Words Text Applications | de Vries, Schoonvelde, Schumacher | 2018 | Political Analysis 26(4) | https://www.cambridge.org/core/product/43CB03805973BB8AD567F7AE50E72CA6 | search summary only |
| N10 | AAAI ICWSM 2024 paper checklist (template) | conference template | 2024 | template | https://www.overleaf.com/latex/templates/aaai-icwsm-2024-paper-checklist/vxbztbhhrbch | search summary only |
