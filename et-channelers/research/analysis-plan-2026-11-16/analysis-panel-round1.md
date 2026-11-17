# Corpus analysis panel — ROUND 1

Date: 2026-11-16. Owner: analysis/statistics workstream. Status: research and experimental design only. No corpus embeddings, topic models, extraction models, ASR, or claim-outcome scoring were run for this memo.

The recommended sequence is measurement audit → lexical retrieval baseline → evaluated semantic retrieval → exploratory topics and networks → independently reviewed claim register. The corpus can support analysis of recorded language, attributed claims, and relationships between texts. Similarity, repetition, or a dense graph does not establish influence, scientific validity, healing efficacy, or the existence of a claimed entity.

## 1. Grounding in the repository

These are inspected file/schema facts, not a fresh inventory of the live collector:

| Existing component | Observed unit or behavior | Consequence for the next analysis |
|---|---|---|
| `plan/targets.csv`; `plan/coverage.csv` | 108 target-profile rows; 107 coverage rows. Profiles include roles, source channels and non-YouTube sources. | Neither number is a count of independent speakers or currently transcribed channelers. Reconcile membership and roles before choosing a denominator. |
| `pipeline/catalog.py` | `item_id`, `person_id`, source lane/tab, source host/URL, publication date, duration, text paths, `twin_of`, `twin_method`, interview type. | A platform item, a recording/work, an interview guest and a channel owner are different units. Preserve all four. |
| `pipeline/keywords.py` | Separate `titles`, `source`, `made`, `captions`; channel-tier TF-IDF; within-channel log-odds keyness; item prevalence; blackout lexicons; false-discovery counts. | Extend existing definitions rather than replacing them silently. A title is metadata, not a transcript. Existing z scores are exploratory evidence, not independently validated discoveries. |
| `pipeline/prediction_timeline.py` | Sentence candidates; date-said provenance; target windows; conditional/hedged cues; furniture exclusions and deduplication. | Target date and utterance/publication date must remain separate. Listing dates marked approximate cannot become exact event dates. |
| `pipeline/prediction_pilot.py`; `plan/prediction_samples.csv` | Four sample-summary rows; distinct rule-development/evaluation purposes; two-coder agreement, prediction-like categories, Wilson and stratified intervals. | Preserve the prior development/evaluation boundary. Agreement is not accuracy. Sampling candidates alone cannot estimate missed-prediction recall. |
| `pipeline/drive_ingest.py`, `youtube_captions.py`, `archive_catalog.py` | Native audio and immutable metadata; English published/original automatic captions in per-track ZIPs with timed segments and verified receipts. | Add a read-only, provenance-preserving adapter to the analysis catalog. Legacy `captions_path` consumers do not automatically become aware of new Drive ZIPs. Never count a missing/blocked/empty caption response as a measured zero. |
| `research/notes/CANONICAL_IDS.md` | Separate person/entity IDs, including general collective names and named subgroups. | Reuse IDs, but validate aliases and attribution. A catalog association is not evidence that a particular speaker uttered every claim in an item. |

The older `ANALYSIS_PLAN.md` is a useful hypothesis register, with dated snapshots and explicitly unverified references. Its hardware, model-price and corpus-size estimates are not adopted here. The current scope includes every queued duration; do not revive the older five-minute inclusion cutoff. Videos, Shorts, recorded streams and unknown tabs remain separate strata, with duration retained as a covariate.

### Proposed analysis units

Use `work_id` for a validated recording family; `item_id` for each distribution copy; `text_version_id` for a publisher text, published caption, automatic caption or later ASR rendition; `span_id` for exact character/time offsets in one version; `claim_id` for a reviewed proposition. Store model/parser/version hashes and the immutable artifact hash behind each derived row.

Resolve confirmed `twin_of` links into checked components, detecting cycles and conflicts. Exact media/text hashes provide strong duplicate evidence; near-duplicate title or embedding matches generate review candidates only. Clips retain their own item identity and an optional parent-work/time interval: they are valuable for the Shorts study but must not masquerade as independent full recordings. Use one primary text version per work in a main estimate, while paired source-version analyses measure transcription effects. Preserve all original versions.

Store `recorded_at`, `published_at`, `captured_at`, `date_basis`, and a date uncertainty interval separately. An upload of an old lecture is not a new utterance. For cross-platform repetition, distinguish first observed in this archive from first said anywhere.

## 2. Search audit and source quality

Five diverse Exa search angles succeeded, requesting 10 results each: **50 requested candidate slots and 50 returned result entries**. These are discovery entries, not 50 independently validated papers. Five initial calls were rejected for a missing required `objective` field and returned no results; counting those attempted requests gives 100 requested slots in total, of which only 50 executed. No additional discovery searches were run.

| Search angle | Requested results | Validation focus |
|---|---:|---|
| Original IR methods for TF-IDF/BM25 normalization | 10 | Author-hosted methods and the original retrieval formulation |
| Sentence embeddings, retrieval evaluation and leakage | 10 | Original benchmarks and failure analysis, not leaderboard rankings |
| BERTopic/NMF, topic stability and longitudinal prevalence | 10 | Original method papers and sensitivity studies |
| Bipartite projections and multiple testing | 10 | Degree heterogeneity, null models and false discoveries |
| Scientific claim/evidence extraction and forecast evaluation | 10 | Evidence-linked labels and proper evaluation units |

**Opened pages:** 20 distinct URLs were requested with Exa fetch; 19 returned source content. The guessed `/consort-2025` path failed; the official root and the original BMJ article succeeded. Search entries that were mirrors, lectures, derivative surveys or irrelevant applications were not treated as independent evidence. Two arXiv versions or DOI/PMC representations of the same paper are one research contribution. Author/source location and concrete methodological content informed selection; citation counts returned by a search tool were not used as a credibility score.

| Method/source | Primary or official source opened | What it supports here; quality and limitation |
|---|---|---|
| Sparse retrieval | [Robertson & Spärck Jones, *Simple, proven approaches to text retrieval*](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-356.pdf) | Authors' Cambridge technical report with retrieval formulation and empirical evaluation context. Supports a transparent lexical baseline; not a validation of this corpus. |
| Regex concordance | [Python `re` documentation](https://docs.python.org/3/library/re.html) | Maintained implementation documentation. Supports reproducible Unicode matching; regex matches alone do not establish semantic relevance. |
| Sentence embeddings | [Reimers & Gurevych, Sentence-BERT](https://aclanthology.org/D19-1410/) | Original ACL paper with architecture and experiments. Supports cached sentence vectors for similarity search; does not make cosine a truth probability. |
| Retrieval versus other embedding tasks | [Muennighoff et al., MTEB](https://arxiv.org/html/2210.07316) | Benchmark authors compare multiple task types. Supports task-specific evaluation rather than assuming an STS winner is the best retriever. |
| Retrieval leakage | [Fröbe et al., train–test leakage](https://downloads.webis.de/publications/papers/froebe_2022e.pdf) | Authors' controlled retrieval study. Near-duplicate queries can affect evaluation; a local held-out split cannot prove a pretrained model never saw public material. |
| Topic extraction | [Grootendorst, BERTopic](https://arxiv.org/abs/2203.05794) | Original method paper: embeddings, clustering and class-based TF-IDF. Its topic representation is not an independently observed latent truth. |
| Interpretable topic baseline | [Lee & Seung, NMF](https://proceedings.neurips.cc/paper/2000/hash/f9d1152547c0bde01830b7e8bd60024c-Abstract.html) | Original optimization paper for nonnegative factorization. Convergence of an optimization objective does not establish stable or meaningful topics. |
| Covariates and topic uncertainty | [Roberts, Stewart & Tingley, STM](https://www.jstatsoft.org/article/view/v091i02) | Authors' JSS software/method paper with replication resources. Supports metadata-aware topic prevalence and uncertainty estimation; covariate association is not causal identification. |
| Topic stability | [Greene, O'Callaghan & Cunningham](http://derekgreene.com/papers/greene14topics.pdf) | Original perturbation/stability study. Supports multiple seeds/subsamples and topic alignment; stability alone does not establish substantive validity. |
| Bipartite projections | [Tumminello et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC3069038/) | Original open-access study accounting for heterogeneous degrees. Supports testing a projection against an explicit null instead of interpreting every shared neighbor. |
| Multiple testing | [Benjamini & Hochberg, 1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x) | Original FDR paper; the opened abstract explicitly describes an independence result. Dependence among terms needs further justification or a conservative alternative, not an automatic guarantee. |
| Scientific evidence links | [Wadden et al., SciFact](https://aclanthology.org/2020.emnlp-main.609/) | Original claim–abstract/rationale dataset. Useful schema and evaluation design; its task is narrower than establishing global scientific truth. |
| Evidence-sensitive verification | [Thorne et al., FEVER](https://aclanthology.org/N18-1074/) | Original benchmark separates supported/refuted/insufficient-evidence labels and evidence retrieval. Domain and annotation conventions differ from channeling speech. |
| Forecast scoring | [Gneiting & Raftery](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf) | Original theory and applications of proper scoring rules. Applicable only where an actual probabilistic forecast and adjudicable outcome exist. |
| Experimental reporting | [CONSORT 2025 statement](https://www.bmj.com/content/389/bmj-2024-081123), [SPIRIT–CONSORT](https://www.consort-spirit.org/) | Original guideline and official organization. Reporting completeness helps appraisal; it is not an efficacy certificate or a substitute for risk-of-bias assessment. |
| Causal questions | [Hernán & Robins, *Causal Inference: What If*](https://miguelhernan.org/whatifbook) | Authors' textbook and code landing page opened. Its detailed chapters were not independently reviewed in this round; detailed causal design remains a ROUND2 gap. |
| Physical frequency | [BIPM SI brochure](https://www.bipm.org/en/publications/si-brochure), [NIST time/frequency definition](https://www.nist.gov/pml/owm/si-units-time) | Official metrology sources. Hertz measures cycles per second; a spoken metaphor such as “higher vibration” supplies no measured physical frequency. |

## 3. Measurement and evaluation contract

### Keep denominators visible

For term or claim label `k`, channeler `c`, period `t`, let `y_ctk` be its count and `W_ct` the eligible token total. Report `10,000*y_ctk/W_ct` only for the same text-kind/tokenization policy. Also report `p_ctk = works_with_k / eligible_works`; repeated mentions within one recording do not become repeated independent observations. For timed claims, a separate rate per transcribed hour is possible only when transcript coverage is known, not simply because total audio duration exists.

The pooled token-weighted rate and the equally weighted mean of channeler rates answer different questions. Publish both only with those labels. Do not average percentages and label the result a corpus rate. Missing captions, unknown speakers and untranscribed hours are missing exposure, not zero counts. Compare English-only caption findings with the English-observed population, not all speech by multilingual channelers.

### Duplicates, dependence and splits

Split recording families before chunking, deduplication tuning, vocabulary fitting or annotation-model training. No clip, repost, translated copy, publisher rendition or caption track from the same family may cross a held-out boundary. Use two distinct evaluations: a blocked chronological test for future periods and a person-held-out test for transfer to unseen channelers. Tune on development data only; preserve a frozen test manifest with hashes. If a cutoff date is uncertain or straddled, quarantine that family from the temporal test.

Dense embeddings may have pretraining exposure to public source texts. Record this uncertainty; an unseen local file is not proof of unseen model training data. Hide held-out claim outcomes, later edits and later commentary from prediction extraction and retrospective labeling.

Estimate intervals by resampling independent work families within prespecified channeler/source strata; for a fixed panel, state that the uncertainty is conditional on that panel. Avoid sentence-level bootstrap pseudo-replication. Show sensitivity to alternative duplicate rules, source versions and date assignments. Small strata may provide insufficient variance information; do not turn that into a zero-width interval. When exposure is highly selective, an interval reflects sampling/model uncertainty, not correction of missing-not-at-random material.

For many exploratory tests, predefine the tested family and show effect size, raw p value, adjusted q value and denominator. The BH rule sorts p values and selects the largest `i` with `p_(i) <= i*q/m`; its assumptions require examination for correlated terms. Keep a short confirmatory family separately registered, with a conservative familywise procedure or an explicitly justified dependence-aware method chosen before outcomes. Never select a favorite month or dictionary and then report its nominal p value as confirmatory evidence.

## 4. Methods and scoped experiments

### E0 — Measurement and attribution audit

Proposed first pilot: up to 120 distinct work families, balanced across available people, periods, source kinds and tabs, plus a separate 30-work development set. These are design targets, not a claim that every matched cell is available. Publish unavailable cells rather than filling them with unrelated material. Two independent coders assess text fidelity, speaker identity, quoted/reported speech, dates, entity attribution and claim type; adjudication follows independent coding.

Use a random sample of all eligible sentences as well as enriched candidate samples. Estimate candidate-screen precision and missed-positive recall separately, with sampling weights where enrichment changes inclusion probabilities. Report per-label confusion matrices, positive/negative agreement and adjudicator uncertainty. Reuse existing pilot taxonomies where appropriate, but do not reuse their development items as a new test. No automated claim-results release until the downstream task has a separately chosen, auditable error tolerance.

### E1 — Concordance and lexical retrieval baseline

Extend `theme_search.py` with versioned positive patterns, exclusions, negation/reporting flags and literal-sense controls. A concordance returns matching spans, surrounding context, speaker attribution and timestamps. Regex is a high-precision candidate generator whose misses are measured; “frequency” near “healing” is not itself a causal healing claim. Keep the raw text intact and store normalization/token offsets separately.

For TF-IDF use the current explicit convention, for positive term count `f_td`:

`w_td = (1 + ln f_td) * (1 + ln((N+1)/(df_t+1)))`, followed by L2 normalization.

Define the fitted document unit and IDF population. Channel-tier “distinctive words” and passage retrieval are separate models; fit IDF only on the allowed training/reference corpus. A common positive-IDF BM25 variant for passages is:

`score(q,d) = sum_t IDF(t) * f_td*(k1+1) / [f_td + k1*(1-b+b*length(d)/mean_length)]`,

with `IDF(t)=ln(1+(N-df_t+0.5)/(df_t+0.5))`. Tune `k1` and `b` on development relevance judgments, not on the final comparison. This formula is a stated implementation choice, not a claim that every cited BM25 implementation is identical.

Pilot 60 genuine research questions spanning exact entities, paraphrases, negation, predictions and measurement claims. Build a blinded pooled relevance set from multiple retrieval methods plus random negatives; acknowledge that incomplete pooling can miss relevant results. Report work-level Recall@20, nDCG@10, and retrieval failures by question type. Multiple overlapping chunks from one recording must not inflate retrieval success.

### E2 — Semantic and hybrid retrieval

Only after E1 freezes its test set, compare one compact embedding encoder with BM25 and a simple hybrid rank fusion. Store unit-normalized vectors and use cosine `u·v/(||u|| ||v||)` as a retrieval score, never an entailment probability. Sweep a small prespecified passage-length/overlap grid on development data. Collapse retrieved chunks to work families for evaluation; retain offsets for evidence inspection.

Report paired differences across queries with uncertainty, as well as failures involving antonyms, quoted denials, names, numbers and vague metaphors. Keep a cross-encoder or generative answer layer out of the first pilot unless retrieval gains justify its extra cost. Similarity links are labeled textual resemblance, not influence or shared truth.

### E3 — Topic discovery and longitudinal distributions

Compare a sparse TF-IDF/NMF baseline with a bounded BERTopic pilot using the same eligible work-family sample. For NMF, solve a declared nonnegative approximation such as `min ||X-WH||_F^2`, with `W,H >= 0`. Row-normalized NMF weights are descriptive mixture weights, not automatically calibrated topic probabilities. BERTopic cluster assignments and outlier scores likewise are not interchangeable with a probabilistic topic posterior.

Vary seeds, a small topic-count/resolution grid and work-family bootstrap samples. Align topics by term overlap and representative passages before measuring stability; report unmatched topics and outlier coverage. Human review includes both representative and random assigned passages. Coherence, stability and meaningful labels are separate checks; none alone selects a “true” topic model.

For a fixed, documented topic map, define `P_ctk = sum_d a_d*theta_dk / sum_d a_d` over eligible documents in channeler-period cells. Use `a_d=1` for recording prevalence or a documented token/time weight for exposure; do not mix them. A secondary STM-style design can examine association with period, source kind, genre and channeler while carrying uncertainty, if the measurement audit supports those covariates.

Show fixed-panel trends beside all-observed-channel trends. Their difference reveals composition effects. Use month/quarter bins only when exposure supports them. Unknown dates remain separate. Descriptive retrospective models fitted on the whole archive must be labeled retrospective; a temporal prediction test freezes vocabulary/topic mapping before the future block. Jensen–Shannon divergence may describe distributional change, but a jump can reflect coverage or transcription changes rather than changed beliefs.

### E4 — Channeler–claimed-entity graph

Maintain a bipartite graph between verified person IDs and **claimed-entity IDs**, with evidence-linked, dated edges. An edge means an observed attributed claim of channeling/identification; distinguish this from mentioning, interviewing, quoting or criticizing an entity. Keep the source host/channel as a separate node type rather than conflating it with the medium. Allow unknown/ambiguous attribution and confidence/provenance fields.

For person `c` and entity `e`, store both a binary relation and the number of distinct supporting work families, plus the denominator of reviewed works. Generic “Arcturians” and a named council need an explicit broader/narrower relation, not an unreviewed alias merge. Record spelling aliases and temporal identity changes; source metadata alone is an unverified mapping.

Start with the bipartite matrix. If projecting to people, `B*B^T` measures shared entity labels, not collaboration. Use degree-aware null comparisons and multiplicity control before emphasizing unusual overlap. Show edge stability under uncertain attribution and alternative alias decisions. A nearly saturated projection or mostly one-to-one register may be less informative than the original evidence table; do not force a network narrative.

### E5 — Predictions and scientific/experimental/healing/frequency claims

Use a claim register with exact span/time evidence, attributed speaker, claim type, negation, modality, quoted-source status, target/event window, date provenance, physical quantity/unit where present, and review status. Suggested categories distinguish prediction, conditional prediction, warning, retrospective self-validation, practical instruction, causal/mechanistic assertion, reported experiment, hypothesis, personal experience and metaphor. Multiple labels may be necessary; preserve a rule for the primary analysis rather than silently counting overlaps as disjoint totals.

For predictions, define outcome resolution rules and acceptable evidence before adjudication. Retain conditionality and an explicit unresolved/ambiguous category. Blind resolvers to the speaker when feasible. Score all eligible matured predictions in the registered set, including failures; display not-yet-matured and unresolved denominators separately. If no numerical probability was actually stated, do not invent one from tone. When probabilities exist, use Brier score `mean((p_i-y_i)^2)` and calibration with adequate bins/intervals; vague forecasts remain a separate classification task.

For scientific or healing claims, retrieve external evidence and label the relationship of each cited source to the precise claim, population, intervention, comparator and outcome. Extraction of an assertion is not its validation; repeated anecdotes and citations to one underlying study are not independent replications. Distinguish a proposed experiment, an experiment described by a speaker, an accessible protocol/registered study, and independently appraisable results. CONSORT-style reporting fields help identify what is missing but do not establish efficacy. This is a document-analysis study, not a proposal to administer treatments.

For “frequency,” retain at least: literal measured physical frequency; asserted numerical Hz without measurement evidence; musical/audio reference; metaphor; unresolved sense. Physical interpretation requires the measured variable, unit, sensor or procedure, observation interval and uncertainty. Do not infer a biological or spiritual field from an audio spectrum, or convert “higher vibration” into hertz. `Hz = s^-1` is a physical unit definition, not evidence for any claimed mechanism.

## 5. Figures that answer concrete questions

No analytical plot is generated in this planning round. Each future figure requires its denominator, coverage note and reproducible data table.

| Figure | Question and design | Required safeguard |
|---|---|---|
| Coverage matrix | Channeler × period cells for eligible works, observed English words and transcribed hours; small multiples by text kind/tab. | Missing is visually distinct from zero. No interpolation across unobserved eras. |
| Retrieval comparison | Paired query-level change in Recall@20/nDCG@10 for BM25, embedding and hybrid, with aggregate intervals. | Same frozen judgments; duplicate-aware work-level scores; show adverse cases. |
| Keyness effect plot | Rate difference/log-odds against support count, with adjusted significance as a secondary encoding. | Sparse terms and furniture remain identifiable; no p-value-only ranking. |
| Topic trajectory small multiples | Fixed-panel and all-observed topic shares over time, with uncertainty and exposure bars. | Fixed topic map; clear weight definition; changing source mix shown alongside trends. |
| Topic stability heatmap | Aligned topics × seed/subsample, plus outlier/unmatched mass. | A compelling two-dimensional embedding is not a validation metric. |
| Bipartite incidence matrix | Reviewed people × claimed entities, sized by distinct supporting families or exposure-adjusted rate. | Unknown attributions visible; evidence drill-down; no causal arrowheads. |
| Prediction timeline and resolution panel | Utterance date → forecast window, conditionality, maturity and adjudicated outcome. | No hindsight redating; ambiguous/unresolved denominators retained; probabilistic calibration only where probabilities exist. |
| Claim/evidence audit | Counts of claim types and evidence statuses; frequency-sense confusion matrix from independent coding. | Counts measure reviewed statements, not scientific support or population prevalence. |

For cross-channel lagged resemblance, an exploratory lag plot may be useful after duplicate removal and date audits. It still cannot identify influence: shared external events, common source material, publishing schedules and archive selection are plausible alternatives. Any stronger causal question requires a separate design and independent exposure evidence.

## 6. Resource envelope and decision sequence

The present collection budget remains authoritative: 17 GB private spool within the overall 20 GB constraint, with the reserved buffer preserved. Research preparation must not launch competing model workloads. When analysis is later authorized, stream verified Drive artifacts in bounded partitions, cache only needed derived data, and retain hashes/manifests on Drive. Sparse counting and metadata joins are CPU housekeeping; embeddings/model inference can use a separately measured GPU queue. A 70% GPU utilization ceiling is an operational target requiring measurement/control, not a guarantee inferred from batch size. No GPU inference is authorized by this planning memo.

The first decision is whether E0 establishes usable text/date/attribution measurements. The second is whether semantic retrieval improves the fixed benchmark enough to justify its cost. Topic models and graph projections remain exploratory until their stability and annotation checks pass. Confirmatory questions are selected and registered before opening their holdout outcomes. All publication continues through existing public-data/quote guards; raw transcripts, evidence text and large artifacts remain private.

## 7. ROUND 2 gaps and assignments

1. **Data engineer:** specify the caption-ZIP → text-version adapter and reconcile legacy catalog fields with current native-audio/metadata receipts. Verify coverage from frozen whole-journal snapshots, not dashboard counters from different dates.
2. **Measurement lead:** design independent random-negative audits for prediction/claim recall; assess timestamps, rolling-caption repetition and matched source-text/automatic-caption error. Identify feasible balanced cells before fixing sample sizes.
3. **Statistician:** choose a small confirmatory family, an effect-size target/power or precision analysis, dependence-aware multiplicity handling and cluster/stratum resampling. Recheck the assumptions of existing keyness and prediction intervals rather than inheriting them by name.
4. **Retrieval lead:** freeze relevance guidelines and recording-family splits; choose a compact encoder by the local benchmark, not a global leaderboard. Audit pretrained exposure uncertainty and numerical/negation failures.
5. **Network/identity lead:** adjudicate person/host/entity aliases and claim-edge semantics; assess whether the actual register is informative enough for projection. Validate graph null assumptions and uncertainty propagation.
6. **Domain reviewer:** separate scientific evidence retrieval from truth adjudication, define physical-frequency and healing-claim rubrics, and review protocol/outcome requirements. Detailed causal-method chapters and contemporary risk-of-bias guidance remain to be opened in ROUND2; the current landing-page review is not that work.
7. **Panel adversary:** test alternative explanations—source availability, genre, prompt examples, model-generated digests, reposts and changing participants—before interpreting temporal or cross-person patterns. The existing 75 digests are exploratory leads, not a substitute for verbatim source material or a clean confirmatory dataset.

ROUND1 conclusion: the corpus is suitable for a carefully scoped study of language and attributed claims once measurement and coverage are audited. It does not, by its size alone, provide evidence of causal influence, experimental validity or metaphysical truth.
