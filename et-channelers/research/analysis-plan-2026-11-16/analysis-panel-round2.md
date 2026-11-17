# Corpus analysis panel — ROUND 2 decisions and contracts

Prepared 2026-11-16. Planning only: no embeddings, LLM extraction, ASR, model downloads or corpus-analysis jobs were executed. This document refines [analysis ROUND1](analysis-panel-round1.md) using [transcription ROUND1](transcription-panel-round1.md), current archive/normalization code, the new host's recorded identity evidence, and targeted primary-source research.

## Decisions

1. Build an append-only **text-version catalog** over verified archive artifacts; do not overwrite raw captions or pretend the legacy single `captions_path` represents all versions.
2. Evaluate extraction with a probability sample that includes **neither-system-selected windows**. Candidate-only review measures precision, not corpus recall.
3. Split confirmed recording families before chunking or model tuning. Use separate chronological and unseen-person evaluations; do not call either universally out-of-sample.
4. Keep channel/host, audible speaker, person identity and claimed-entity instance separate. A host's guest list is not the host's list of channeled entities.
5. Compare BM25 with one compact embedding challenger first. A second challenger is conditional on a measured benefit; global MTEB ranks are not local evidence.
6. Show text coverage and source/format composition alongside topic or claim trends. Network/community results require explicit null controls and stability analysis.
7. Keep physical measurements, metaphors, personal healing experiences, intervention studies and adjudicated evidence relationships as different fields and labels.

## 1. Concrete source and identity checks

`sources/extra_channels.csv` records **Multidimensional Soul**, handle **@Akanksshaa**, channel ID **UC1jF0BbiGpAB6ekXgByEPYg**, verified by the root workstream from the channel's own Videos-tab metadata. `sources/extra_targets.csv` currently uses `multidimensional-soul` with role `interview_host`. The discovery record also documents a self-description as an Akashic channeler. This round inspected those recorded primary-source observations; it did not make another live YouTube request. Primary locator: [the channel](https://www.youtube.com/channel/UC1jF0BbiGpAB6ekXgByEPYg).

**Attribution decision:** retain that verified host/channel identity and the self-description as a sourced statement. No specific claimed entity is established for the host by this evidence. For an interview, `host_person_id` may identify Akanksshaa, while `speaker_person_id` and a guest's claimed entity remain episode/segment-specific. Unknown guests or ambiguous speech remain unknown. A title naming a guest/entity is a discovery lead, not voice identification. Do not rename existing canonical IDs in an adapter; record alias mappings with provenance and review.

Current code facts affecting the adapter:

- Caption ZIPs contain `raw.json3` or `raw.vtt`, `segments.json`, `transcript.txt`, and `provenance.json`. Published and original automatic English tracks are separate. Translated `tlang` sources are excluded.
- `youtube_captions.py` preserves rolling automatic-caption repetition; a future de-rolling view must be a separately tested transformation with source-offset mappings, not an in-place correction.
- `archive_catalog.py` exposes verified caption bundle IDs, byte counts and hashes, including partial successes. Its compact bundle projection requests `ext`, while track provenance currently names the field `raw_format`. Treat a blank projected `ext` as missing metadata; validate the format from ZIP provenance/member names rather than guessing.
- Storage verification is not content-quality verification. A hash-valid bundle may still have poor coverage, incorrect names or ambiguous speakers. `caption_empty`, blocked and unresolved states are not absence observations.
- Transcription ROUND1's explicit CUDA owner, bounded windows, versioned derivations, shared storage leases and independently reviewed text remain prerequisites. Published captions are not automatically human gold.

## 2. Caption ZIP → analysis catalog contract

### Reader behavior

The reader takes an immutable archive manifest/delta snapshot and verified per-track proof, not a recursive Drive listing or a scan of surviving local files. A partially completed video may contribute an individually verified caption track; video-level incompleteness remains visible.

For each selected artifact: acquire the shared local reservation/lease; fetch the exact Drive object; verify expected byte length and complete SHA-256 against the recorded proof before declaring it usable. Inspect ZIP names, types and declared/uncompressed sizes before extraction; reject paths, links, duplicate members, unexpected members and over-budget expansion. Read into bounded temporary storage. Verify video/track/language/kind consistency between catalog, provenance and raw member, and reject machine-translated provenance. Never infer a person from a category folder name.

Preserve raw bytes, their hash, the existing normalization output and its version. Generate an analysis view with its own configuration hash. If de-rolling, punctuation, tokenization or speaker attribution changes, append a new version and retain the mapping back to the old raw segments. Unknown end timestamps remain null; do not fabricate word timestamps or infer full-session coverage from the last caption timestamp alone.

The adapter is idempotent on `(artifact_sha256, parser_revision, normalization_config_hash, output_schema)`. Derived catalog partitions are immutable and hash-addressed. A newer capture or changed normalization appends a version; it does not replace source metadata or a previous evaluation input. The existing capture filenames are not a general versioning scheme for future changed provider captions: future recaptures need an explicit append-only artifact policy first.

### Minimal schemas

All keys below are proposed contracts, not tables already implemented. Times are seconds relative to the source recording or explicit UTC instants; lengths/byte counts carry units. Nullable fields are intentional.

| Table / primary key | Required fields | Invariants |
|---|---|---|
| `works / work_id` | `family_id`, source item IDs, relation type (`same_recording`, `excerpt_of`, `unresolved`), parent interval when known, merge evidence/reviewer, recording-date interval and basis | Confirmed same-recording families are equivalence classes; excerpt relations are directed and do not imply full duplication. No unresolved link silently merges families. |
| `source_items / item_id` | `platform`, platform ID, channel ID, host-person ID/basis, source tab, duration, recorded/published/captured dates, source URL, current collection state | Source tab and duration remain distinct. An interview host does not become every speaker. Unknown date/identity is null. |
| `artifacts / artifact_id` | `work_id`, `item_id`, Drive ID, canonical remote, bytes, MD5, SHA-256, artifact kind, verified receipt/snapshot ID | A proof authorizes one exact object. Analysis never deletes authoritative Drive audio. |
| `text_versions / text_version_id` | `artifact_id`, source audio hash if known, track ID, kind (`publisher`, `published_caption`, `automatic_caption`, `local_asr`, `human_reference`), language/origin, parser/model revision, configuration hash, raw/text hashes, quality status and coverage basis | `text_version_id = SHA256(canonical derivation inputs)`. Hash identity excludes mutable local paths. Same track ID with changed content is a new version. |
| `segments / (text_version_id, segment_id)` | raw segment IDs, start/end or null, verbatim text, normalized text, raw/normalized character offsets, transformation mapping, diarized speaker label or null | Normalized spans map back to original evidence. A diarization label is not a person ID. Overlaps/repetitions are retained or explicitly transformed. |
| `speaker_attributions / attribution_id` | work/segment range, speaker label, person ID or null, role (`host`, `guest`, `quoted_person`, `unknown`), evidence/source, review status | Confidence/provenance of identity remains separate from ASR token scores and storage verification. |
| `analysis_views / view_id` | frozen input version IDs, eligibility rule, preferred-version policy, tokenization/de-rolling hash, coverage table hash | One primary text version per work for a main estimate; paired versions enter a separate calibration analysis. Selection is recorded before outcomes are inspected. |

A legacy compatibility view may populate `captions_path` with a deliberately selected version and expose `caption_version_id`, `caption_kind`, `caption_language`, `selection_policy`, and `coverage_status`. It must not erase alternate tracks or label automatic captions as publisher text. New analyses should join normalized tables directly.

### Adapter acceptance cases, before implementation approval

Exact duplicate import produces no new derivation; changed raw bytes produce a distinct version; translated track is rejected; blocked inventory remains pending; a single verified track in a partially verified video remains usable with coverage caveat; zero-content normalization is rejected; malicious ZIP paths/size expansion fail before promotion; uncertain timestamps stay uncertain; changed normalization leaves prior claims/splits reproducible. Round-trip a sample claim span to its raw caption segment and timestamp. These are future checks, not checks claimed to have run.

## 3. Probability sample for regex and LLM extraction

The evaluation target is **claim mentions in the frozen, observed English text view**, not all speech ever produced and not only sentences selected by a detector. Build non-overlapping anchor windows (proposed 150 normalized words) covering every eligible text, including windows with no system output. Review adjacent context and source audio when attribution/timing matters. Assign each gold claim and prediction to the window containing its first evidence token, so a cross-boundary span is counted once.

### Two-stage design

1. Freeze a work-family frame and development/test separation. Select an initial target of 80 work families by stratified probability sampling across source kind, tab, broad date coverage and host/monologue role. Collapse sparse metadata strata by a documented rule before selection; every eligible family must have positive inclusion probability. Do not claim 80 works represent every channeler.
2. Run frozen regex and LLM configurations only when that inference phase is authorized. Within each sampled work, classify windows into four disjoint strata: regex+/LLM+, regex+/LLM−, regex−/LLM+, and **regex−/LLM−**.
3. Sample up to eight windows per work, initially two per nonempty stratum, with a prespecified redistribution rule for small/empty strata. Log every stratum population `N_wh`, sample `n_wh`, random seed and selected window. Inclusion probability is `pi_i = pi_work * n_wh/N_wh`, conditional on the realized stratified design. The neither-system stratum must retain positive probability.
4. Two human coders independently annotate all sampled windows without seeing which system selected them or its proposed labels. Train on separate development material, then adjudicate test disagreements. Audit exact span support, proposition type, negation/conditionality, speaker attribution, numerical/unit content and dates. Do not use an LLM judge as the independent gold coder.

This is a fixed probability design, not an implementation of ADASTRAT's adaptive algorithm. Original research supports handling skewed extraction categories and sampling-based precision/recall; its guarantees do not automatically transfer to a different sampler. [Lowe & King](https://aclanthology.org/W03-2803.pdf), [Sabharwal & Xue](https://proceedings.mlr.press/r16/sabharwal18a.html).

Let `TP_i`, `FP_i`, `FN_i` be matched claim-mention counts for one system in reviewed window `i`, with `w_i=1/pi_i`. Estimate totals as `TP_hat=sum(w_i*TP_i)` and similarly for FP/FN; then report `P_hat=TP_hat/(TP_hat+FP_hat)` and `R_hat=TP_hat/(TP_hat+FN_hat)`. Horvitz–Thompson weighting motivates the totals; the ratios are not themselves claimed to be exactly unbiased. Preserve the two-stage design in variance/replicate weights, including work-family clustering and finite population corrections where applicable. A naive binomial interval over enriched windows is inappropriate. [Horvitz & Thompson](https://doi.org/10.1080/01621459.1952.10483446).

Specify span matching and proposition-equivalence rules before scoring. Unsupported invented quotations count as false positives. Technical model failures are reported and included in a defined failure-sensitive analysis, not dropped. No missed positives in a small neither-system sample does not prove perfect recall; report a defensible one-sided uncertainty bound or collect more labels. Publish per-label weighted counts, intervals and sample support, not only an aggregate F1.

| Evaluation table | Essential fields |
|---|---|
| `sample_units` | frame/view/split ID, work/window ID, first-stage stratum and probability, regex/LLM mask, `N_wh`, `n_wh`, final inclusion probability, seed |
| `human_labels` | coder ID, anchor window, exact evidence span, claim labels, attributed speaker, uncertainty, adjudication version |
| `system_outputs` | model/rules revision, prompt hash, input version, output span/label, raw structured output hash, technical status |
| `matched_evaluation` | system output ↔ gold claim matching, TP/FP/FN disposition, sampling weight, disagreement reason, metric version |

Measure annotation time on a small development batch before committing to the full human workload. The proposed 640-window maximum is a planning envelope, not a power calculation or a completed sample.

## 4. Held-out splits and coverage estimands

Assign confirmed recording families, including excerpts and alternate text versions, to a common split. For a fixed historical training frame, use a versioned deterministic family-hash split into development and untouched test groups. For prospective evaluation, use a separate cutoff based on the recording/publication evidence available by that cutoff. Families with uncertain dates crossing the boundary are excluded from the temporal test and reported. Do not fit vocabulary, chunk-size selection, IDF, topic maps, regex changes or prompts on future blocks.

An unseen-person test excludes all reviewed works attributed to selected people, including guest appearances on other channels. Mixed-speaker works cannot leak a held-out person's speech through the host's training partition; quarantine the work or use reviewed speaker segments with an explicit split rule. If a later duplicate/identity merge connects two splits, flag contamination and invalidate affected metrics rather than silently relocating records after inspecting results.

Separate estimands:

- **Observed-corpus rate:** claim mentions per 10,000 eligible words in one text-kind/tab stratum.
- **Recording prevalence:** fraction of eligible recording families containing a reviewed claim/topic.
- **Fixed-panel comparison:** channeler-specific rates standardized to an explicitly chosen format/period composition, using `p_std,c = sum_h a_h*p_ch`, with common weights `a_h` fixed before comparison.
- **Archive coverage:** observed text/known audio or listed works, with denominator provenance and unknown-duration counts.

Do not weight missing transcripts as if missingness were random. Standardization requires overlapping observed cells; if a channeler has no comparable interviews or old recordings, report the missing contrast. Show raw and standardized estimates, and sensitivity to publisher versus automatic captions. All queued durations remain in scope; Shorts and long recordings are stratified, not discarded.

## 5. Modern retrieval shortlist and local selection rule

The table records model-author specifications inspected in this round. It is not a local speed/memory ranking. No model was installed, downloaded or run.

| Candidate | Verified specification | Role and required evaluation discipline |
|---|---|---|
| BM25 | Transparent sparse baseline from ROUND1 | Fit IDF on the allowed frame; tune only on development judgments. Retain exact matches, numbers and names. |
| `BAAI/bge-small-en-v1.5` | Author config has 384 hidden dimensions and 512 positional capacity; card gives an English retrieval-query instruction. [Card](https://huggingface.co/BAAI/bge-small-en-v1.5), [config](https://huggingface.co/BAAI/bge-small-en-v1.5/raw/main/config.json) | Compact established baseline, not the newest model. Include prompt/special-token allowance within the input bound; never silently truncate evidence. |
| `google/embeddinggemma-300m` | 300M parameters; 2K context; 768-dimensional output with 512/256/128 options; distinct query/document prompt forms. [Author card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card) | First modern challenger for the resource-limited pilot. Test full output against one reduced dimension only after the main baseline. Review the exact Gemma terms/revision before provisioning. |
| `Qwen/Qwen3-Embedding-0.6B` | 0.6B parameters; 32K context; up to 1024 dimensions, configurable output; query instruction and no corresponding document instruction in the example. [Author card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) | Conditional second challenger. Long context is a supported capability, not evidence that full-session embedding is useful or fits the laptop workload. |

Model-author benchmark claims are treated as hypotheses for local testing. Pin the model revision, tokenizer, pooling, prompt templates, context/truncation policy, precision and library versions. Use the correct query/document interface for each model; do not penalize a model by omitting its required instruction. Keep titles as a separately declared input ablation because metadata may reveal names or later framing absent from the speech.

MTEB's maintained implementation supports explicit tasks, versions and splits. Select retrieval tasks relevant to the question, and preserve those identities in reports; an aggregate across classification, clustering and retrieval tasks does not select this corpus's retriever. [MTEB maintainers](https://github.com/embeddings-benchmark/mteb).

Local pilot proposal: up to 10,000 common evidence windows, using identical character spans that fit every candidate tokenizer's declared bound. Freeze 60 research questions: 20 development, 40 untouched test, covering entity names, paraphrases, negation, dates/numbers, physical-unit claims and metaphors. Pool multiple systems' results for blinded graded relevance judgments, add a probability sample outside the pool, and label incomplete-pool recall honestly. Score work-level nDCG@10, Recall@20, reciprocal rank, evidence-window recall and attribution errors. Compare paired query differences and meaningful failure strata, not only means.

Use a single GPU owner shared with ASR, small measured batches and cached vectors. At float16, one million 768-dimensional vectors alone occupy `1,000,000*768*2 = 1.536 GB`, before indexes, IDs and metadata. The 10,000-window pilot needs 15.36 MB for that matrix alone. Model weights and temporary indexes consume the same project allowance; these calculations are not measured runtime memory. No promise of a strict instantaneous 70% utilization cap is inferred from model size.

## 6. Identity and claim schema

Separate a **canonical label/concept** from a **speaker-attributed claimed-entity instance**. Two speakers using “Arcturians” may mean different groups; two spellings may refer to the same claimed entity. Neither decision follows from string similarity alone.

| Schema | Fields and interpretation |
|---|---|
| `person_identity` | canonical person ID; verified aliases; channel/account IDs; source evidence; valid time; unresolved identity links |
| `claimed_entity_concept` | canonical label, aliases, broader/narrower labels, concept type; no assertion of external existence |
| `claimed_entity_instance` | instance ID scoped by attributed speaker/lineage and reviewed identity claim; optional concept ID; explicit same-as/disputed/unknown relation and evidence |
| `claim_mentions` | text version/span/time, speaker attribution ID, claim category, literal assertion, modality/negation, quoted/reported source, target date interval/basis, entity instance or null, extraction/review versions |
| `evidence_relations` | claim ID, external study/result ID, population/intervention/comparator/outcome/time, supports/refutes/no-information/indirect relation, exact rationale locator, reviewer, risk-of-bias/uncertainty fields |

For a guest's self-attribution in an interview, the edge attaches to that guest and that claim instance. The host retains the hosting relation. Narration about someone else's claim uses `reported_by` and `attributed_to` separately. Topic co-occurrence does not authorize a same-entity merge or an influence edge.

Frequency annotations retain `sense = measured_physical | asserted_physical_unmeasured | audio_music_reference | metaphor | ambiguous`; separate numeric value/range, unit, measured variable, apparatus/procedure, measurement uncertainty and causal assertion. ROUND1's NIST/BIPM definitions remain the physical-unit authority. A numeric “Hz” is still only an assertion unless measurement evidence exists; a waveform spectrum of recorded speech does not measure an alleged biological or spiritual mechanism.

Healing evidence annotations distinguish personal experience/testimonial, uncontrolled case or before-after observation, comparative observational intervention study, randomized intervention result, and evidence synthesis. Appraise the precise result, not the prominence of the speaker or a whole paper's reputation. Cochrane's [RoB 2 guidance](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-08) addresses trial-result bias; [ROBINS-I guidance](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-25) requires attention to confounding and a specified target comparison for nonrandomized interventions. [GRADE guidance](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14) assesses a body of evidence for an outcome. These are different assessment levels. Do not manufacture a GRADE rating from an anecdote or use model confidence as medical evidence. This plan authorizes document review only, not treatment advice or human intervention experiments.

## 7. Falsifiable questions, dynamic topics and communities

Use static, frozen NMF/topic baselines before adding temporal flexibility. Evaluate whether dynamic models improve held-out representation and coherent time evolution without hiding abrupt changes behind forced smoothness. The original [dynamic-topic evaluation study](https://aclanthology.org/2024.acl-long.11/) proposes temporal and dynamic quality measures; these complement rather than replace human review and recovery of known synthetic shifts. [TopicCheck](https://aclanthology.org/N15-1018/) supplies a concrete alignment/stability precedent. Neither a stable label nor a smooth curve proves a real-world mechanism.

For community detection, repeated partitions and a consensus matrix reveal optimization instability. Preserve a grid of resolution and temporal-coupling settings rather than selecting the prettiest graph. In multislice models, temporal coupling itself rewards persistent communities; it cannot be counted as independent evidence of persistence. [Mucha et al.](https://www.math.ucla.edu/~mason/papers/multislice.pdf), [Lancichinetti & Fortunato](https://www.nature.com/articles/srep00336). Compare optimization variance with explicit null randomizations; community algorithms can return a partition even when substantive structure is weak. [Bassett et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC3618100/).

| Falsifiable question | Statistic / preregistered contrast | Null or negative control; interpretation limit |
|---|---|---|
| Does reviewed person–claimed-entity overlap exceed what activity and label popularity explain? | Bipartite overlap or selected projection edge weight among observed, reviewed cells | Degree-preserving swaps within period/source strata, retaining missing-cell restrictions; multiple-test control. A significant edge is unusual attribution overlap, not evidence of shared external entities. |
| Do topic shares change within the same observed people/format/text-kind panel? | Standardized within-person change with work-family uncertainty; topic-map stability across seeds | Matched no-change synthetic corpora and date-label/block controls justified by the observed dependence structure. Missing old captions or new interview formats cannot be interpreted as belief change. |
| Is apparent cross-channel resemblance explained by reposts, introductions or generic vocabulary? | Retrieval/similarity excess after confirmed duplicate and furniture exclusions | Same-period matched random pairs, shuffled attribution within eligible strata, and a furniture-only view. Temporal precedence alone is not influence. |
| Is community persistence greater than induced smoothing and observation continuity? | Co-assignment probabilities, variation across partitions, persistence among nodes present in both periods | Same node-presence masks and degree distributions, zero-coupling comparison, resolution/coupling grid. Never count absent/unobserved nodes as isolated. |
| Does a prediction extractor identify auditable forecasts beyond generic future tense? | Weighted precision/recall for dated/conditional forecasts on untouched work families | Noncandidate windows, logistics/promotion, questions, quoted predictions, retrospective self-validation and undated teaching. Outcome adjudication is a later, separately blinded task. |
| Can physical-frequency assertions be distinguished from metaphor reliably? | Weighted sense confusion matrix and exact numeric/unit/speaker agreement | Metaphorical high-frequency language, quoted denials, musical references and dimensionless numbers. Agreement validates annotation usefulness, not the asserted physics. |

No p value is meaningful without an exchangeability/design argument for its null. Keep tests on work families, account for repeated people, and distinguish fixed-panel inference from broader population claims. Graph projection, threshold selection, topic alignment and parameter sweeps are themselves analysis choices subject to sensitivity checks and multiplicity.

## 8. Publication-quality figure package

These are specifications, not generated results. Export vector PDF/SVG plus source CSV/Parquet, figure code, input snapshot and view IDs. Use legible labels, colorblind-safe categorical colors, uncertainty with its meaning stated, and identical scales for comparable panels. Show sample/exposure counts adjacent to every rate. Never render missing data as zero.

1. **Coverage plate:** channeler × period heatmaps faceted by Videos/Shorts/recorded streams and text kind; separate panels for observed words, known audio hours and missingness.
2. **Extraction evaluation plate:** weighted precision–recall estimates with uncertainty, the four detector-selection strata and sampled/estimated gold counts, plus attribution/date/unit error breakdowns. Show failures and uncertain labels.
3. **Retrieval comparison:** paired query-level differences with aggregate intervals and a separate speed/memory panel measured under the same hardware/throttle; plot exact-number and negation queries as prespecified strata.
4. **Topic dynamics:** fixed-panel standardized trajectories and exposure bars, paired with topic-alignment/stability matrices. Show unmatched/outlier mass and known-date coverage; reserve alluvial ribbons for matched, stable topics and display uncertain transitions.
5. **Claimed-entity relations:** primary bipartite incidence matrix with reviewed distinct-family support and missing-cell masks; secondary projection only if the declared null test is informative. Each highlighted edge links to provenance, not long public transcript excerpts.
6. **Community uncertainty:** consensus co-assignment heatmap and resolution/coupling sensitivity surface; a network drawing is a navigation aid, not the statistical result.
7. **Predictions and evidence:** utterance-date/target-window timeline with maturity and unresolved outcomes; separate calibrated-probability plots only for forecasts with actual stated probabilities.
8. **Frequency/healing claim audit:** sense/type × evidence-availability matrix and reviewed confusion matrices. A forest plot of treatment effects is inappropriate unless comparable independent study results and an explicit synthesis protocol actually exist.

## 9. Search audit, decisions left open and handoff

Five targeted Exa searches requested **5 results each: 25 requested, 25 returned entries**. The angles were compact embedding model cards, probability sampling of extraction quality, dynamic communities, dynamic-topic validation, and intervention-evidence appraisal. **18 distinct primary/official URLs were opened successfully**: four model/benchmark pages; four sampling/topic pages; three dynamic-network papers; three Cochrane chapters; and four follow-ups comprising the Horvitz–Thompson original, full extraction/dynamic-topic papers and the BGE author config. A paper landing page and its PDF are two opened URLs but one research contribution. No search entry or leaderboard position was treated as validated local performance. The host identity evidence was read from the root's recorded primary observation, not counted as a new web fetch.

Model cards are authoritative about interfaces but interested sources for performance comparisons; the proposed local benchmark decides adoption. Sampling and community papers supply methodological precedents, not proof that their assumptions hold here. Cochrane's opened chapter pages identify their edition/update dates; detailed appraisal must select and record the specific tool version rather than assuming a generic “current” URL freezes it.

Ready for implementation design: normalized schema and version keys; adapter acceptance cases; probability-sampling frame and weighting; speaker/host/entity distinction; compact retrieval comparison; and figure/null-control specifications. Still unresolved: actual matched-text coverage, feasible strata/sample precision, available human coding time, full model license/dependency review, local model throughput/quality, and which graph contrasts have enough observed support. These are measurement or pilot decisions, not reasons to run all models now.

Owners: ingestion/transcription implements shared leases and verified artifact reading; corpus engineering implements versioned adapter/views; evaluation owns human labels and weights; identity reviewer owns speaker/entity adjudication; retrieval/topic researchers own frozen experiments; the research lead approves a narrow, resource-accounted pilot after these contracts are reviewed. Existing public-data and quote guards remain the publication boundary.
