# Panel R1 — The Expert (computational linguistics + anomalistics): research program v1

*Ground truth: full clone at `/mnt/agents/lab2/bashar-index` (HEAD cff3988). All structures cited below verified against the clone: `data/analysis.json` (keys: method, tags, headline, share_overall/by_type/by_year/by_era, clusters, terms, entities, tools, predictions, tag_pairs, questions), `data/digests/*.json` (75 files; per-digest fields include `topic_percentages`, `qa_topics`, `key_terms`, `predictions_and_dates`, `tools_or_exercises`, `named_entities`, `researcher_note`), `data/catalog_sessions.json` (684 rows, title/date/type/source_url only — no content), `data/videos.json` (75 records with `year_reliable` flags), `data/glossary.json` (104 terms).*

Grading scheme throughout: **Established / Frontier / Speculative / Untestable / Refuted / Misattributed**.

---

## 1. Research questions, ranked by testability × interest

I score testability as (falsifiability × data already in hand × method maturity) and interest as (novelty × consequence × publishability). Ranked:

**Q1 (rank 1). Prediction-ratchet analysis.** The only fully falsifiable surface of the corpus, and the only question answerable *entirely from repo data today*. The ledger exists (`analysis.json.predictions`, 29 year-records; `teachings.md` §4); the slip is documented in-corpus (2026/27 → 2028–29); the escape architecture ("probable realities" framing) is quoted. Highest testability, high interest — the 2016 cluster and the live 2027 slip make it timely and preregisterable-adjacent.

**Q2 (rank 2). Doctrine-consistency network across the corpus.** Testable now on structured repo data (glossary relations, tag co-occurrence, diagram labels, per-digest entities). The repo already surfaces one contradiction class (four-law vs. five-law Laws of Creation; Shalanaya/Yahyel ordering). The folk claim under test — "40 years without contradicting himself" — is the community's strongest consistency argument, so a quantitative coherence score has real evidential weight in both directions.

**Q3 (rank 3). Stylometric separability: channeled-Bashar register vs. Anka-interview register.** Highest interest of the five — the first computational authorship study of any channeled corpus, with a direct precedent (llm-stylometry's per-author cross-entropy resolving the 15th Oz book) — but **not testable on repo data as shipped** (§3 below: digests are LLM paraphrase; there are no raw transcripts). It ranks third only because acquisition is the gating cost, not because the question is weak. The repo's own diagnostic — k-means on vocabulary yields silhouette 0.01–0.05, "vocabulary nearly the same in every recording" — is a tantalizing prior result that begs for a function-word-level redo on real text.

**Q4 (rank 4). Q&A demand dynamics.** 949 classified questions are already in `analysis.json.questions` (tag, count, pct, examples with video_id). Fully testable on repo data, moderate interest: it reframes the corpus as half counseling service, half cosmology, and the commercial-segmentation hypothesis (paid self-help vs. free disclosure marketing) is sociologically novel. Ranked below Q1–Q2 because year-resolution is limited (only 2024–2026 reliable).

**Q5 (rank 5). Bashar as lexical bridge: Seth/Ra (1963–84) → law-of-attraction self-help (post-2006).** The most historically interesting question and the least testable *from this repo*: it requires external corpora (Seth/Yale archive, lawofone.info, ACIM, Abraham-Hicks, plus self-help baselines) and a cross-corpus embedding pipeline. Keep on the roadmap; do not start in round 1.

---

## 2. Hypotheses, data, methods, nulls, grades

### Q1 — Prediction ratchet

**H1 (formal).** Let *c(d)* be the conditionality index of forward predictions made at date *d* (fraction of escape-hatch markers in the claim text: "probable", "window", "depends on collective choice", "vibrational"), and let *Δ* be the time remaining to the stated deadline. H1: *c* increases monotonically as *Δ* → 0, and post-deadline claims are re-issued with shifted windows rather than retracted (ratchet, not revision). Secondary: stated window bounds *w(t)* drift rightward with *t* at rate ≥ 1 (window moves faster than time).

**Data in repo:** `analysis.json.predictions` (29 year-records with per-video example texts), per-digest `predictions_and_dates` fields (75 digests), `teachings.md` §4 ledger, `skeptical_coverage.md` (Ross & Carrie annotations of conditionality). **To acquire:** dated session dates for each prediction-bearing digest (partially present via `session_date_or_event` + `researcher_note` corrections; the repo's own misdated-video flag shows this is doable but requires case work); original pre-2020 transcripts for the Blueprint-era claims (world government 2011–13, quarantine end 2012).

**Method.** Structured ledger: one row per claim (claim text, date made, deadline, conditionality index via regex/classifier over escape-hatch lexicon, outcome, post-hoc reframe). Score with Brier where a probability was stated (the 88% female-president claim); compute window-bound time series and regress lower/upper bounds on calendar time; quantify "reframe rate" = fraction of failed claims later redescribed as vibrational/conditional.

**Null vs. claim.** Null (honest forecasting): conditionality flat in *Δ*, windows stationary or drifting with rate < 1, failures acknowledged as failures. Claim (immunizing stratagem, cf. 06_fringe B3 pattern): rising conditionality, super-unity drift, universal reframing. Prior from the documented 2016→"Window of Discovery" retcon and 2027→2028–29 slip: claim strongly favored. **Grade: Frontier as a measurable pattern (test runnable now); the underlying metaphysical claims are Refuted (2016 cluster) to Untestable (as hedged).**

### Q2 — Doctrine-consistency network

**H2.** The doctrinal graph (concepts as nodes; relations from `glossary.json.related`, `tag_pairs`, diagram `key_labels`) is *statistically* coherent — few hard contradictions, high cross-session stability of core-term usage — but coherence is *maintained by elasticity*: node definitions drift (e.g., "frequency" with no operational definition) rather than snap. Formally: contradiction count per 100 concept-relations < 5; per-term distributional semantics stable within the 2024–26 window but unstable on definitional probing.

**Data in repo:** everything needed for the structural half — 104 glossary terms with sources, 56 diagram records with labels, `analysis.json.tag_pairs` and `entities`, per-digest `topic_percentages` and `key_terms`. **To acquire:** raw transcripts for definitional-drift probing (word-in-context embeddings of "frequency", "permission slip", "density" across decades).

**Method.** Build the graph in networkx; encode each relation; auto-flag contradictions (mutually exclusive orderings, arity conflicts like 4-vs-5 laws, alias conflicts). For term dynamics: per-digest key-term frequency buckets (already in digests) → rank-stability (Kendall's W across docs) and cohort analysis (official clips vs. re-uploads vs. interviews).

**Null vs. claim.** Null (single-author improvisation): accumulating contradictions with corpus size; term inventories unstable. Claim (maintained persona/system): sub-linear contradiction growth, stable core lexicon — which the silhouette-0.01 finding already weakly supports. Note the trap: **high consistency is predicted by both the ET hypothesis and the one-author persona hypothesis**; Q2 cannot discriminate them, and I will say so loudly. **Grade: Frontier as descriptive corpus science; the community's "no contradictions in 40 years" claim is testable only on title metadata pre-2024, so era-extended versions are Speculative.**

### Q3 — Stylometric separability (Bashar persona vs. Anka)

**H3.** Function-word and rhythm-level features separate channeled-session text from Anka-interview text at accuracy significantly above register-matched controls (topic-matched expository speech), and the gap is temporally stable across decades. Rival sub-hypotheses: H3a (persona): gap collapses under register control or matches known role-play/pseudonym magnitudes (80–95%); H3b (anomalous source): gap survives register control and exceeds role-play baselines.

**Data in repo:** the *design* — 21 flagged Anka interviews vs. 27 full sessions, `format` field, video IDs for acquisition; the repo's vocabulary-silhouette diagnostic as prior. **To acquire (blocking):** raw auto-transcripts for all 75 video IDs (the digest pipeline's upstream source, `youtubetotranscript.com`, is named in `digest_source` per file), plus archive.org audio transcripts for 1984–96 era sessions, plus Anka's own books (*The New Metaphysics*, *Blueprint for Change*) and interview text as the Anka-author corpus.

**Method.** (i) Burrows' Delta over the 150 most frequent function words, with bootstrap CIs; (ii) per-author small causal LMs, llm-stylometry style: LM_Anka vs. LM_Bashar cross-entropy on held-out sessions; the attribution statistic is ΔCE = CE_Anka − CE_Bashar per document; (iii) unmasking curves (Koppel–Schler) for cross-topic robustness; (iv) register controls: same-topic Anka panel (Anka discussing Bashar in interviews vs. Bashar discussing the same topic in session). Audio-side extension: x-vector/ECAPA-TDNN speaker embeddings + prosody on session vs. interview audio (IONS 2019 found voice-parameter shifts in trance — measurable either way).

**Null vs. claim.** Null (one trained persona): ΔCE ≈ 0 after register control; Delta clusters by register, not speaker-state. Claim: persistent decade-stable gap. Critical honesty note carried from the fringe review: **even a large positive gap does not establish non-human origin** — stylometry routinely separates one author's personas; the informative result is the negative. Both outcomes publishable. **Grade: Frontier — genuinely doable, never done for any channeled corpus; blocked on transcript acquisition.**

### Q4 — Q&A demand dynamics

**H4.** Question mix is demand-driven and channel-segmented: paid/full-session Q&A skews to life guidance (health, relationships, abundance), while free clips and interviews skew to contact/disclosure. Formally: topic distribution differs by `content_type` with Cramér's V > 0.2, and `et_contact_disclosure_2027` share rises monotonically across 2024→2026 (the marketing-timeline hypothesis).

**Data in repo:** all of it — `analysis.json.questions` (949 classified), `videos.json.content_type`, `share_by_type`, `share_by_year` (2024–26 only). **To acquire:** view/engagement counts per video (demand-side outcome variable); nothing else.

**Method.** χ² / log-linear models of tag × content_type; permutation CIs; time trend via logistic regression of disclosure-tag share on year. Base rates already known: misc life guidance 24.7%, contact/disclosure 16.8%.

**Null vs. claim.** Null (doctrine-driven): mix invariant across channels and years. Claim (market-driven): segmentation and the 2024→26 disclosure ramp. **Grade: Frontier as media sociology; safe to run on digests because topic tags are content-level, not style-level (see §3).**

### Q5 — Lexical bridge (Seth/Ra → Bashar → LOA self-help)

**H5.** Bashar's signature lexicon ("frequency", "vibration", "permission slip", "excitement", "parallel realities", "density") occupies a temporal and semantic midpoint: cosine-bridging analysis shows Bashar terms transferring Seth/Ra-era senses into post-2006 self-help usage, with Bashar as highest-betweenness node in a term-diffusion graph.

**Data in repo:** term list (`glossary.json`, `key_terms.csv`) and Bashar-side usage stats. **To acquire (blocking):** Seth corpus (Yale MS 1090 derivative texts), lawofone.info full corpus (free), ACIM, Abraham-Hicks, Ramtha, plus self-help controls (Hay House corpus, *The Secret*).

**Method.** Diachronic word-embeddings per corpus-decade (aligned Procrustes spaces); term-level semantic-nearest-neighbor tracking; betweenness in a cross-corpus shared-lexicon graph; first-use dating via dated sessions.

**Null vs. claim.** Null: independent parallel invention from common esoteric sources (Blavatsky→New Thought trunk); Bashar not privileged. Claim: Bashar is the diffusion hub. The IONS inter-channeler consistency finding ("same ET source vs. same bookshelf") is the confound this study could partially resolve. **Grade: Speculative-to-Frontier; genuinely interesting digital-humanities question, but round 3+ work.**

---

## 3. The corpus-bias problem, and what is safe on digests

The pipeline is three lossy filters: YouTube availability (what survives/uploaded in 2024–26) → auto-transcription (ASR errors on a fast-talking trance register) → single-LLM digest (paraphrase into a fixed 20-tag schema per `src/DIGEST_SPEC.md`, one model, generated 2026-09-11). The repo is admirably honest about all three (`analysis.json.method.caveats`), and we should be exactly as honest downstream.

**Safe on digests (content-level, schema-mediated claims):** topic mixes and tag shares (the digest LLM estimates them, but errors are plausibly unbiased across categories); question inventories and their classification; entity and tool occurrence counts; the prediction ledger as *claims about what was said* (each digest prediction has a verbatim-adjacent context string); per-digest researcher notes. Rule of thumb: **any variable that is a classification into the fixed schema, or a count of named things, is usable**, with a multi-model spot-verification pass on a 10% random subsample (re-digest N=8 transcripts with a different model, measure agreement; the repo's own misdated-video catch proves the failure mode is real).

**Not safe on digests (form-level claims):** anything about word choice, syntax, rhythm, hedging density, function words, type-token ratio, entropy — all stylometry, all of Q3. Digest text is the digesting model's register, not Bashar's. A stylometric result on digests would be a stylometry of one LLM's summarization habits; publishing such a result about "Bashar" would be the program's first retraction. Also unsafe: era-level content claims before 2024 (the 684-catalogue is title/date metadata only), and verbatim quotation beyond the ≤30-word quotes (which are ASR-mediated anyway).

**Mitigations to build in now:** (i) every digest-level analysis carries a `digest_level: content` tag in code; (ii) the transcript-acquisition pipeline (§4, B5) is critical-path — it converts Q3 and the drift half of Q2 from Speculative to Frontier; (iii) year handling uses only `year_reliable: true` records, plus `researcher_note`-corrected dates, never title dates; (iv) interview-vs-session comparisons use the repo's own 21-interview flag as the design variable rather than any text feature.

---

## 4. First-round build list for the coder (repo data alone, runnable now)

Ordered; each is a self-contained Python script against the clone.

- **B1. Prediction-ledger scorer.** Parse `analysis.json.predictions` + per-digest `predictions_and_dates` into `ledger.csv` (claim, video_id, year-mentioned, date-made where recoverable from `session_date_or_event`/`researcher_note`, conditionality lexicon hits, window lower/upper bounds). Emit the **sliding-window gantt**: every stated contact window vs. a "now" line. Tests H1. One day. This is the panel's most quotable deliverable.
- **B2. Window-drift quantification.** From B1's bounds: regress stated lower/upper contact-window bounds on session date; report drift rate and its CI; specifically reconstruct the 2020 → 2023–2033 → 2025–2033 → 2026/27 → 2028–29 sequence from digest texts. One day, depends on B1.
- **B3. Glossary-term frequency dynamics.** Per-digest `key_terms` freq buckets → term × doc matrix; Kendall's W rank stability across the 75 docs; cohort contrasts (official clips / re-uploads / full sessions / interviews); occurrence counts for the known movers ("2027" in 28 docs, "2026" in 23, "permission slip" in 45 — verify against `key_terms.csv`). Tests the repo-side half of H2. Half a day.
- **B4. Doctrine-graph builder + consistency checker.** networkx graph from `glossary.json` relations + `tag_pairs` + diagram `key_labels`; programmatic contradiction flags (arity conflicts, alias/order conflicts); force-layout export. Tests H2's structural half; infrastructure for everything later. One to two days.
- **B5. Transcript acquisition pipeline (critical path).** For each of the 75 video IDs in `videos.json`, fetch and *archive the raw auto-transcript* (the digest_source URL is recorded per digest); store alongside digests with checksums. This unblocks Q3 and the drift analyses. Days, mostly I/O. Do not digest; archive raw.
- **B6. Q&A demand tables.** `analysis.json.questions` × `videos.json.content_type` × reliable year: χ²/log-linear segmentation, disclosure-share trend 2024→26, with permutation CIs. Tests H4. Half a day.
- **B7. Pipeline robustness re-run.** Re-run `src/topics.py` (seed 42) with k ∈ {4,5,6,7}, weighting on/off, interviews excluded, to bracket the 0.346-silhouette 5-cluster solution. Half a day.

Explicitly **not** in round 1: anything stylometric on digest text (Q3 needs B5 first), cross-corpus embeddings (Q5), era-level content claims from the 684-catalogue.

## 5. Recommended panel goal statement, v1

*This panel will treat the Bashar corpus — 40+ years of dated sessions, a complete doctrine stack, a documented prediction ledger, and a living commercial ecosystem — as the best-instrumented natural experiment in the channeling genre, and will ask only those questions the evidence can actually answer: whether the persona is computationally distinguishable from its human author (with the explicit caveat that separability cannot establish non-human origin, while non-separability under register control would dissolve the corpus's strongest folk-evidence claim); whether the prediction record behaves as honest forecasting or as an immunizing ratchet with a sliding contact window, scored quantitatively from the ledger and preregistered where still live; whether the doctrine is a stable system or an elastic one; and what the audience actually demands of it. We commit to the corpus's own honesty standard — claims reported as claims, digest-level and transcript-level evidence never conflated, nulls specified before analysis — on the premise that for a belief system this well documented, the sociological and linguistic questions are answerable, the ontological ones are not, and confusing the two is the only unforgivable error.*

I expect the advisor to attack the goal statement on its quietism about ontology; my defense is that the permission-slip/"probable realities" architecture makes ontological falsification impossible *by the doctrine's own construction*, and a panel that pretends otherwise will produce theater, not evidence. Challenge welcome.
