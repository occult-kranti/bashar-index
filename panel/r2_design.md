# Panel R2 — The Coder: pre-registered analysis design (design round, loop 1)

*Ground truth re-verified against the clone at `/mnt/agents/lab2/bashar-index` (HEAD cff3988) by direct inspection: `analysis.json` (16 top-level keys incl. `predictions` [29 year-records, per-record `year`/`docs`/`examples[{video_id, text}]`], `questions` [20 tag-buckets, `count`/`pct`/`examples[{video_id, question}]`, total count = 949], `share_by_type` over the four content types, `share_by_year` covering 2024–2026 only); `videos.json` (75 records; `content_type` counts: Full session re-upload 27, Interview with Darryl Anka 21, Clip/excerpt 15, Official highlight 12; `year_reliable`: 40 true / 35 false); `digests/*.json` (75 files; fields incl. `digest_source` [youtubetotranscript.com URL], `predictions_and_dates`, `qa_topics`, `key_terms`, `researcher_note`); `catalog_sessions.json` (684 rows, title/date/type/source_url, archive.org-dominant); `glossary.json` (104 terms with `related`). Every pre-registration below is written **before any analysis code runs** and is frozen at this timestamp: design round 2, loop 1.*

This document implements all four advisor binding requirements, the multiple-comparison policy, the analysis-suite architecture, the acquisition plan as step zero, and the figure plan. Nothing here adjudicates ontology; every output carries the grading scheme (Established / Frontier / Speculative / Untestable / Refuted / Misattributed).

---

## 1. Pre-registration texts (verbatim, frozen)

### 1(a). H1 — Prediction-ratchet analysis

**Frozen escape-hatch lexicon** (counted case-insensitively, as whole phrases, on prediction claim text exactly as recorded in digest `predictions_and_dates[].prediction`/`context` strings and `analysis.json.predictions[].examples[].text`; **this list may not be edited after the first scoring run**):

> "probable", "probability", "probable realities", "probable reality", "most probable", "likely", "window", "window of", "depends on", "dependent on", "up to you", "up to humanity", "collective choice", "collective decision", "your choice", "if you", "should you", "as long as", "provided that", "conditional", "vibrational", "vibrationally", "frequency", "energy reading", "reading of the energy", "current energy", "at this time", "as of now", "timeline", "timelines", "parallel reality", "parallel realities", "shift", "sensitive to", "subject to change", "may change", "can change", "not set in stone", "no such thing as a prediction", "potential", "potentially", "possible", "possibly", "we sense", "we perceive", "our sensing", "approximate", "approximately", "around", "give or take".

**Conditionality index.** For claim *i* with token count *Tᵢ* (whitespace tokens of the claim text) and lexicon hit count *hᵢ* (each distinct lexicon phrase occurrence counts once; overlapping matches counted at the longest match):

  **cᵢ = hᵢ / Tᵢ**; the corpus-level conditionality at date *d* is **C(d) = Σhᵢ / ΣTᵢ** over claims made at *d* (pooled, not averaged, so short claims don't dominate).

**Monotonicity test (one-sided).** Claims are binned by *Δ* = (stated deadline − date made) into {>10y, 5–10y, 1–5y, <1y, post-deadline}. H1 predicts C *increases* as Δ→0. Test: one-sided Jonckheere–Terpstra trend against the ordered alternative at α=0.05, plus Spearman ρ(C, −Δ) reported with bootstrap CI (10,000 resamples over claims, seed 42). Honest forecasting predicts flat or *falling* conditionality near resolution; that is the null shape.

**Window-drift estimator.** Each stated contact-window bound (lower *L(t)*, upper *U(t)*) is a point (session date *t*, bound year). Drift rate = slope of Theil–Sen regression of bound year on calendar date, fit separately to L and U, with 95% CI by bootstrap over bounds (seed 42). **Drift-rate definition: drift ≥ 1.0 means the stated deadline recedes at least as fast as time passes (super-unity drift) — the ratchet signature.** H1 claims slope ≥ 1 with CI lower bound reported; honest forecasting predicts slope ≈ 0 (fixed deadline) or < 1 (converging estimate).

**2027 prospective scoring rubric (frozen, blind to outcome timing).** The claim under test: "open contact" within the window currently stated as 2027 (with the in-corpus slip to 2028–29 recorded as a ratchet event, not an edit to the rubric). Minimal definition of open contact, scored against public record by a coder blind to the panel's drift results:

- **Success (full):** a national government or the UN formally confirms non-human intelligence and initiates a public diplomatic/communication exchange, OR a non-human craft/entity is publicly presented and independently verified by ≥2 major scientific institutions, before 2030-01-01.
- **Partial:** official government acknowledgment of non-human-origin materials or craft without public exchange (e.g., declassification with institutional verification); or a mass-witnessed, multi-instrument-recorded event officially unresolved and endorsed as anomalous by ≥2 national space/defense agencies.
- **Failure:** neither criterion met by 2030-01-01. Retrospective re-interpretation of prior events (e.g., "2017 NYT UAP story was contact") does **not** score; only events occurring after this pre-registration count.
- Scoring is **blind to timing**: the same rubric applies whether the event occurs in 2027 or 2029; the ratchet analysis is about window movement, the rubric is about outcome. If the window is re-issued again before resolution, each re-issue is logged as a ratchet event with the new bounds.

### 1(b). H4 — Q&A demand dynamics

**Data:** `analysis.json.questions` (949 classified questions across the 20 fixed tags; each example carries `video_id`) joined to `videos.json.content_type` (four levels) and, for the trend test only, `videos.json.year` restricted to `year_reliable: true` (2024–2026). Questions from a video inherit that video's content type; a video contributes its questions as independent rows (clustering by video acknowledged; see sensitivity below).

**Segmentation test (primary).** Contingency table tag (20) × content_type (4) over question counts. Pearson χ² test of independence, α=0.05. Effect size **Cramér's V** with bias-corrected 95% CI by percentile bootstrap (10,000 resamples, seed 42). **Threshold: the hypothesis is confirmed only if V > 0.2** (at least a small-to-medium association; below this, segmentation is commercially meaningless even if p < 0.05). Directional reading: residuals will be inspected for the predicted pattern (paid/full sessions → `misc_life_guidance`, `relationships_family_sexuality`, `health_body_healing_death`, `abundance_money_career`; free clips/highlights/interviews → `et_contact_disclosure_2027`), but residual direction is descriptive, not a fifth test.

**Null model.** Doctrine-driven invariance: tag mix independent of content type (χ² null), and disclosure share flat across years (slope = 0). Additional permutation null: shuffle content_type labels within year strata (10,000 permutations, seed 42) to control for the 2024–26 upload mix; report permuted p alongside asymptotic p. Sensitivity: re-run with video-level proportions (each video one 20-vector, Kruskal–Wallis across types) to check the row-independence assumption.

**Trend test (primary).** Logistic regression: per-question indicator `tag == et_contact_disclosure_2027` on calendar year (continuous, 2024–2026), reliable years only. H4 confirmed if slope > 0 (one-sided α=0.05) **and** the fitted share increases monotonically across the three year points. Base rate noted frozen: 16.8% overall.

### 1(c). Q3 — Stylometry design: the negative is the target outcome

**Registered position.** The publishable target of the stylometric study is the **negative result**: ΔCE ≈ 0 (and Burrows' Delta inseparability) between channeled-session text and register-matched Anka speech, on real transcripts, with adequate power. A null means: at function-word and language-model level, the "Bashar" persona is not distinguishable from Darryl Anka's own expository register once topic is controlled — which dissolves the community's strongest folk-evidence claim ("he couldn't fake this for 40 years") while saying nothing about ontology. It is publishable because (i) it is the first computational authorship study of any channeled corpus, (ii) the method (llm-stylometry per-author cross-entropy) has a resolved precedent, (iii) the null is informative against a specific, widely-held empirical claim, and (iv) it is cheap to replicate on other channeled corpora. The panel commits in writing: **a null meeting the four quality gates (power statement, pre-registered run as specified, ASR/provenance audit passed, effect sizes with CIs) will be published with the same prominence as a positive.** Equally: a positive (persistent, register-controlled gap exceeding the 80–95% role-play/pseudonym baseline band) does not establish non-human origin — stylometry routinely separates one author's personas — and any output implying otherwise is a retraction-level error.

**Feature sets:** (F1) 150 most frequent function words → Burrows' Delta with bootstrap CIs; (F2) per-register small causal LMs (LM_Bashar, LM_Anka) → held-out ΔCE per document; (F3) Koppel–Schler unmasking curves for cross-topic robustness. **Register control:** topic-matched pairs (Anka discussing Bashar/contact in interviews vs. Bashar on the same topic in session), using digest `topic_percentages` only as a *matching* index (content-level, schema-mediated — permitted under the digest rules), never as a text feature. **Detectable-effect statement:** with 21 interviews and a matched 21-session Bashar set, bootstrap power analysis on the role-play baseline band says we detect ΔCE ≥ 0.15 nats/token at ≥80% power; smaller effects are reported as CIs, not claimed as zeros.

### 1(d). Digest re-verification protocol (gates all digest-level claims)

**Sample:** 8 of 75 digests (10.7%), drawn by seeded RNG (seed 2027) stratified across content_type (≥1 per stratum) before any digest-level result is reported. **Procedure:** re-digest the same raw transcript (or the recorded `digest_source` fetch) with a *different* LLM than the original pipeline model, using `src/DIGEST_SPEC.md` verbatim — same prompt, different model. **Agreement metrics:** (i) topic_percentages: per-document L1 distance on the 20-tag vector, pooled median; (ii) tag assignment of questions: Cohen's κ on the tag × question classification; (iii) key_terms: Jaccard overlap of term sets; (iv) predictions_and_dates: human-adjudicated match rate (claim + date both present). **Pass/fail:** PASS requires median L1 ≤ 0.15, κ ≥ 0.60, Jaccard ≥ 0.40, prediction match ≥ 75%. FAIL on any metric: all digest-level results that depend on the failed dimension are downgraded one grade (Frontier → Speculative) and re-run with doubled subsample (N=16) before any claim ships. Results are reported in every output's provenance block.

---

## 2. Multiple-comparison policy

**Primary tests (exactly four), Holm-corrected as a family at α=0.05:**

1. **P1 — H1 conditionality:** Jonckheere–Terpstra monotone increase of C as Δ→0 (one-sided).
2. **P2 — H1 drift:** Theil–Sen slope of contact-window lower bound L(t) ≥ 1 (CI-based).
3. **P3 — H4 segmentation:** χ² on tag × content_type with V > 0.2 threshold.
4. **P4 — H4 trend:** logistic slope > 0 for disclosure share on year.

**Everything else is exploratory:** labeled `exploratory` in code, output JSON, and figures; **no p-value appears in any artifact without an "EXPLORATORY" banner** — enforced by a shared `report.py` helper that refuses to format unbadged p-values. **Post-hoc rule:** any test invented after seeing a result inherits a null prior and is reported as hypothesis-generating only. **B7 cluster-robustness sweep:** reports *all* k ∈ {4,5,6,7} silhouettes, not the best. Effect sizes with CIs are mandatory everywhere; p-only reporting is a build error.

---

## 3. Analysis suite architecture — `/mnt/agents/lab2/analysis/`

```
analysis/
  README.md            # provenance block standard, grading scheme, seed registry
  common.py            # data loaders, digest_level tagging, provenance + badging
  report.py            # JSON results writer, exploratory banner, Holm correction
  predictions.py       # P1, P2 + ledger build (B1, B2)
  demand.py            # P3, P4 (B6)
  doctrine_graph.py    # Q2 structural half (B3, B4)
  stylometry.py        # Q3 (blocked until acquisition lands)
  acquisition.py       # step zero: transcript/audio fetch + WER audit (B5)
  results/             # <module>_<date>.json, schema below
  figures/             # fig_*.py → PNG/SVG, style per §5
  transcripts/         # acquired raw text/audio (§4 layout)
```

**Results JSON schema (all modules):**
```json
{"module": "...", "git_head": "cff3988", "seed": 42,
 "digest_level": "content|transcript|metadata",
 "tests": [{"id": "P1", "family": "primary", "statistic": ..., "p": ...,
            "p_holm": ..., "effect": ..., "ci95": [...], "exploratory": false}],
 "provenance": {"inputs": [...], "reverification": "pass|fail|n/a"},
 "grade": "Frontier", "generated": "..."}
```

**predictions.py.** Inputs: `analysis.json.predictions[].examples[].text`, `digests/*/predictions_and_dates`, `digests/*/session_date_or_event`, `digests/*/researcher_note`, `videos.json.session_date_or_event`, `teachings.md` §4 (manual ledger rows, source-tagged). Outputs: `results/ledger.csv` (claim, video_id, date_made, deadline, window bounds, lexicon hits, cᵢ, outcome, reframe flag), `results/predictions_*.json`, gantt figure. Seed 42. Acceptance: every ledger row traceable to a repo string; ≥1 documented slip reconstructed (2020→2023–33→2025–33→2026/27→2028–29); dates from title-only sources (`year_reliable: false`) excluded from time series but kept in the ledger with flag.

**demand.py.** Inputs: `analysis.json.questions`, `videos.json.{content_type, year, year_reliable}`. Outputs: contingency tables, V with CI, trend fit, `results/demand_*.json`, two figures. Seed 42. Acceptance: 949 questions accounted for; reliable-year subset = 40 videos; permutation null reported; video-cluster sensitivity run.

**doctrine_graph.py.** Inputs: `glossary.json` (`term`, `related`), `analysis.json.tag_pairs`, `diagrams.json.key_labels`, per-digest `key_terms`. Outputs: networkx graph export (GraphML), contradiction flags (arity/alias/order conflicts, e.g. 4-vs-5 Laws), Kendall's W term-rank stability across 75 digests, cohort contrasts by content_type. Acceptance: the known 4-vs-5-laws and Shalanaya/Yahyel conflicts are flagged programmatically; all outputs badged `digest_level: content`; consistency results never carry origin-language (advisor ruling 2b — consistency is descriptive corpus science, not evidence about origin).

**stylometry.py.** Inputs: `transcripts/` (post-acquisition only), matching index from `topic_percentages`. Outputs per §1(c): Delta with CIs, ΔCE per document, unmasking curves, power statement. Acceptance: ASR audit passed (§4) before any run; register-controlled pairs ≥ 21; the module **refuses to run on digest text** (hard assert on input path).

**acquisition.py.** Step zero. See §4. Acceptance: ≥90% of the 75 video IDs archived raw with SHA-256, or an explicit per-ID failure log; WER audit report emitted before stylometry unlocks.

---

## 4. Acquisition plan (step zero)

**Targets.** (i) All 75 `videos.json` IDs — the digest pipeline's upstream; `digest_source` gives the exact `youtubetotranscript.com` URL per digest; fallback: YouTube timedtext captions via `yt-dlp --write-auto-subs`. (ii) The 21 flagged Anka interviews (filter `content_type == "Interview with Darryl Anka"`) — the H3 contrast class. (iii) A matched Bashar-session set: 21 full sessions matched to interviews on year (reliable years) and dominant topic (via `topic_percentages`), drawn from the 27 re-uploads + official sources. (iv) Era extension: `catalog_sessions.json` has 393 archive.org rows (1984–96 audio) — fetch audio, transcribe with a fixed ASR model (Whisper large-v3, pinned), giving the cross-decade arm. No digesting, no summarizing: **archive raw**.

**ASR quality audit (pre-registered gate for Q3).** Stratified sample: 12 transcripts (4 interviews, 4 sessions, 4 archive.org ASR). 3 × 60-second spans each, hand-transcribed against audio; WER computed with `jiwer` after normalization (lowercase, strip punctuation, expand contractions). Function-word WER reported separately (that is the load-bearing subset for F1). Gate: overall WER ≤ 15% and function-word WER ≤ 10%; if failed, stylometry runs only on spans passing the gate and the limitation is stated in results. ASR error is reported as a provenance field, mirroring the digest-honesty standard.

**Storage layout.**
```
transcripts/
  youtube/{video_id}.txt        # raw auto-transcript, verbatim
  youtube/{video_id}.meta.json  # fetch URL, method, timestamp, sha256
  archive_org/{slug}.wav|mp3 + .whisper.json
  audit/wer_report.json
```
Checksums in a manifest; originals immutable; any cleaning lives in derived files.

**Legal/ToS note.** Personal, non-commercial research use only; transcripts and audio are stored privately in `lab2`, never redistributed, never committed to a public repo; quotation in outputs stays within the repo's own ≤30-word discipline; YouTube/auto-caption fetching is rate-limited and attributed; archive.org items are public uploads fetched per item terms. This matches the repo's own hygiene posture.

---

## 5. Figure plan (matplotlib; site/report)

House style locked: figure facecolor `#191715`, axes `#191715`, foreground amber `#e8a33d` / copper `#b5713a` accents, serif family (DejaVu Serif), light grid `#3a352f`, white text `#ede6da`. Figures:

- **F1. Sliding-window gantt** (predictions.py): every stated contact window as a horizontal span vs. a "now" line; re-issues chained; amber spans, copper "now". The panel's most quotable deliverable — and, per the advisor, a *figure*, not a finding.
- **F2. Conditionality vs. Δ** (predictions.py): pooled C per Δ bin with bootstrap CIs; monotone-trend annotation with P1 result; null-shape overlay (flat line) for contrast.
- **F3. Window-bound drift** (predictions.py): L(t)/U(t) scatter + Theil–Sen fits; reference slope-1 line; drift rate + CI in caption.
- **F4. Demand mosaic** (demand.py): tag × content_type standardized residuals, amber-positive/copper-negative diverging scale.
- **F5. Disclosure-share trend** (demand.py): 2024–2026 fitted logistic with permutation-null band.
- **F6. Term-rank stability** (doctrine_graph.py): Kendall's W across docs; top-mover terms slope graph ("2027", "2026", "permission slip").
- **F7. Stylometry ΔCE distribution** (stylometry.py, post-acquisition): per-document ΔCE for matched pairs, with the 80–95% role-play band shaded and the ΔCE≈0 null line — designed to look equally good around a null.

Every figure embeds its badge: `digest_level` tag, grade, and EXPLORATORY banner where applicable.

---

## Commitments restated

Four primary tests, Holm-corrected; everything else badged exploratory; frozen lexicon (§1a) — post-hoc lexicon tuning is astrology with extra steps and is barred; acquisition is step zero and gates Q3; the negative stylometry result, if it meets the four quality gates, ships with the same prominence as a positive. If we are not willing to publish the null, we are not doing science.

*— The Coder, round 2, loop 1.*
