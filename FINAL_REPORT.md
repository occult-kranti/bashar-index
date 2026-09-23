# The Anatomy of a Self-Sealing Prophecy
## Final report of the Bashar-Index evidence-honest panel (rounds 1–5)

*All statistics below are from `analysis/results/*.json`, re-run end-to-end at
seed 42 in round 5 against the frozen repository snapshot (git HEAD
`cff3988`). The panel's standing banner applies to every doctrinal and
predictive statement in this report: **this work measures genre discipline,
not truth.** Nothing here speaks to the origin of the material, and no result
should be read as evidence for or against any claim about non-human
intelligence. What is measured is how a modern channeled-prophecy corpus
behaves as an object: what it sells, what it promises, how its promises move,
and what it would take to falsify them.*

---

## 1. The corpus

The Bashar Index is a public web archive documenting the teachings of
"Bashar," an entity channeled by Darryl Anka since 1983 — one of the most
influential bodies of material in the contemporary contactee/disclosure
subculture, and unusual among such corpora in that it makes *dated* claims.
The panel worked over the repository's machine-readable layer: **75 video
digests** (structured per-video summaries with topic shares, key terms, and
extracted predictions), **949 audience questions** classified into 20 topic
tags (available only as aggregate counts plus 99 sampled examples), a
104-term glossary (248 related-term edges), and a catalog of sessions with
reliability-flagged dates.
From the digests' `predictions_and_dates` fields we built a **prediction
ledger of 164 dated claims**, each carrying its stated deadline or window, a
conditionality score against a frozen 50-phrase "escape-hatch" lexicon
("probable," "window," "up to you," "subject to change," …), and a date
reliability flag. Thirty-eight rows come from videos whose year survives only
in the upload title; they are kept in the ledger, flagged, and excluded from
every time series.

A short history orients the numbers. Anka began channeling in 1983 after a
guided-meditation class, following two close-range UFO sightings in the 1970s
that he describes as the initiation of his research. Through the 1990s the
movement was a seminar-and-cassette operation; the 2016 documentary *First
Contact* and the migration to YouTube transformed it into a streaming
catalog, and it is this streaming era — hundreds of sessions, interviews, and
clips, 2016 to mid-2026 — that the digest layer captures. The doctrine itself
is a compact metaphysics (five laws, parallel realities, "permission slips,"
vibrational frequency) wrapped around a single escalating promise: that
humanity is approaching "open contact" with the Sassani and allied
civilizations, with the date stated, restated, and — as this report documents
— repeatedly re-stated.

Two properties make this corpus worth studying. First, it is *modern*: most
reliable-date material is 2016–2026, dense with a specific, repeated,
datable prophecy — open extraterrestrial contact, currently promised for the
late 2020s. Second, it is *self-documenting*: the doctrine explicitly teaches
that predictions are "readings of current energy," not fixed futures — a
built-in epistemic escape hatch. The question the panel set out to answer was
whether that escape hatch is used *systematically*, and whether the system
around it can be described honestly without ever adjudicating the prophecy
itself.

## 2. Methods and machinery

The design was frozen before scoring (round 2, pinned to commit `cff3988`),
with exactly **four pre-registered primary tests** corrected as a Holm family
at α = 0.05; everything else ships badged EXPLORATORY, and the reporting
layer (`report.py`) *refuses to serialize* an unbadged p-value or a test
without an effect size and confidence interval — enforcement is a build
error, not a convention. Every stochastic procedure uses seed 42 (10,000
bootstrap and permutation resamples). Every artifact carries its grade
(Frontier for digest-level claims, Speculative for anything transcript-level)
and, where applicable, its EXPLORATORY banner — figures included: each of
F1–F8 embeds its badge, its n, and its digest-level in the image itself, and
no figure carries a p-value in its title except with its badge. The
machine-readable evidence layer (`results/*.json`) is the source of truth for
every number quoted here; this report contains no statistic that is not
serialized there with its provenance block. The panel ran five rounds with an
advisor-skeptic who twice re-ran the code independently; the audit trail is
summarized in §8.

## 3. P3 — the demand sociology (the confirmed finding)

The one hypothesis that survived every robustness check is about **packaging,
not prophecy**. Do the different formats in which the material is sold —
free interviews, short clips, official highlight reels, and paid full-length
sessions — deliver systematically different content? Yes. The χ² test of
topic-share × content-type over the 75 videos gives Cramér's **V = 0.212**,
clearing the pre-registered V > 0.2 threshold — narrowly (the bias-corrected
estimate is 0.206, below the bar), but the cluster-bootstrap 95% CI
**[0.211, 0.300]** clears it entirely, and a within-year permutation test
(p = 10⁻⁴) is robust to the pseudo-replication that makes the asymptotic
p-value (≈10⁻¹⁷⁵) meaningless as count inference. That asymptotic figure is
retained only as a decorative artifact and is never quoted without this
caveat.

The direction of the effect is the finding's real content. Free **interviews
(+6.9)** and **clips/excerpts (+3.1)** over-deliver
`et_contact_disclosure_2027` content relative to the corpus average;
**official highlight clips (−3.0)** and **paid full sessions (−6.4)**
under-deliver it, skewing instead to relationships, health, abundance, and
life guidance. The front door sells contact; the back room sells life
advice. This asymmetry — disclosure as marketing surface, personal guidance
as product — is the movement's economic engine, and it is measurable from
public data alone. A 99-question cross-check (E5, EXPLORATORY; Monte-Carlo
permutation p = 0.031, V = 0.558) confirms the direction at question level
within the two sampled formats, though its labels permute across questions
clustered within videos and its p inherits a mild pseudo-replication problem
of its own; the confirmed claim remains digest-level. P3 is the family's only
Holm-significant test.

## 4. P4 — the disclosure-share trend (the pre-registered null)

The family's fourth primary asked whether disclosure content is *escalating*:
does the `et_contact_disclosure_2027` share of audience questions rise over
the late streaming era, against the frozen 16.8% base rate? No. The binomial
GLM of disclosure-question share on year over the reliable-year videos of
2024–2026 (**n = 34 videos, 556 questions**) gives a log-odds slope of
**−0.149 per year** (95% CI **[−0.60, +0.30]**, one-sided p = 0.741 for a
rising slope), and the fitted shares are non-monotone: the disclosure share
is **flat-to-declining** against its frozen base rate. P4 is therefore a
clean pre-registered null — the corpus does not escalate its disclosure
content in the era closest to the deadline — and it is reported here with
the same prominence as the family's one confirmed test, because a
pre-registered null is a result, not an omission. Figure F5 plots the fitted
trend with its badge and n. With P1, P2, and P4 all null, the Holm family
stands at exactly one significant test in four.

## 5. The failed ratchet — P1, P2, and the ledger

The pre-registered **ratchet hypothesis** held that as a stated deadline
approaches, the claims about it become *more* conditional — hedging as an
approach-avoidance mechanism, quantified by a conditionality index C
(lexicon hits per token) against Δ, the time remaining to the deadline.

**P1 rejects it.** The one-sided Jonckheere–Terpstra permutation test across
ordinal Δ bins (n = 88 reliably dated claims with parseable deadlines) gives
p = 0.948, Somers' D = −0.309: conditionality is flat-to-*falling* near
resolution, the direction the pre-registration assigned to *un*hedged
forecasting. Two companion statistics must be kept distinct (a round-3
conflation was corrected in the audit): the uncontrolled Spearman ρ = −0.214
(EXPLORATORY p = 0.046) does not control for era, while the era-controlled
partial correlation ρ = −0.203 has a bootstrap CI [−0.386, −0.005] that
grazes zero (naive asymptotic p ≈ 0.059, reported but never upgraded). The
negative trend is weak, era-fragile, and carried by a three-claim bin. A
rejected H1 is a null for the ratchet hypothesis — it is **not** a discovered
virtue, and no sentence of the form "the corpus hedges honestly" is licensed
anywhere in the panel's output.

**P2 fails to certify drift.** The Theil–Sen slope of the contact window's
lower bound over restatements (n = 25) has CI [−1.2, 1.0], which does not
certify recession at ≥ 1 year per year.

But the ledger itself — the finding, with the statistics as annotation —
tells the cleaner story. The contact window's documented slip chain runs
**2020 → 2023–33 → 2025–33 → 2026/27 → 2028–29**, each re-issue logged as a
ratchet event. Across the corpus there are **73 window-polarity flips** — a
later-stated window lying entirely beyond an earlier-stated one — computed as
all-pairs ratios from 35 window rows and therefore non-independent (each row
enters ~4 pairs; this structure is disclosed wherever n = 73 appears). The
median flip overshoots the violated bound by 2 years; the median slip
velocity is **1.0 year per year with IQR [0.5, 4.25]** — only 29% of flips
sit at exactly 1.0, with 38% below and 33% above and a tail of 5–24 yr/yr
jumps. (The round-4 bootstrap CI of [1.0, 1.0] has been **removed as a
degenerate artifact**: resampling dependent ratios made the discrete median's
interval collapse to zero width.) The clean form of the claim is the
**consecutive-restatement subset**: pairs of restatements one year apart
(n = 38) recede at median **1.0 yr/yr**, while pairs three or more years
apart (n = 32) recede at median 0.4 yr/yr. The ratchet fails as a *hedging*
mechanism and succeeds as a *calendar* mechanism: deadlines do not become
more conditional as they approach — they are simply replaced, annually, on
schedule. The failure mode is institutionalized, not improvised.

## 6. Doctrine dynamics — a fixed vocabulary with liquid emphasis

The doctrinal network (126 nodes, 635 edges over the 104-term glossary, 248
related-term edges) is
stable in *vocabulary* but not in *emphasis*. Kendall's W of within-digest
term-salience ranks is **0.009** overall (95% CI [0.007, 0.014]) — 0.013 in
the early era, 0.019 in the late era — meaning salience ranks are essentially
uncorrelated across digests. Between consecutive digests, the rank
correlation of the top-15 terms averages just +0.16 and the top-5 turnover
averages 47%. The doctrine claims immutability and delivers churn — but churn
of *emphasis*, never of lexicon. The four exploratory contradiction flags
(including the "four laws / five laws" arity conflict, found in at least two
late-era digests, with a third digest undated — all three flagged
year-unreliable in the ledger) are disclosed in `doctrine_results.json`. All doctrine
outputs carry the quietism banner: this is genre discipline, not truth.

## 7. The 2027 rubric and its retroactive calibration

Because the corpus makes a datable prediction, the panel pre-registered its
falsification instrument *before* the outcome window. The rubric is frozen
(this text verbatim, timestamped at `cff3988`):

> **Claim under test:** "open contact" within the window currently stated as
> 2027 (in-corpus slips logged as ratchet events, never edits to the rubric).
> Scored blind to timing against the public record by a coder blind to the
> panel's drift results; only events after pre-registration count;
> retrospective re-interpretation never scores.
>
> **Success (full):** a national government or the UN formally confirms
> non-human intelligence and initiates a public diplomatic/communication
> exchange, OR a non-human craft/entity is publicly presented and
> independently verified by ≥2 major scientific institutions, before
> 2030-01-01.
>
> **Partial (tightened):** an official government statement using explicit
> non-human-origin language (not "unknown") about materials or craft,
> verified by a national laboratory or peer-reviewed analysis; or a
> mass-witnessed (≥1,000 independent witnesses), multi-instrument (≥2
> independent instrument classes, e.g. radar + optical — not two cameras)
> event officially unresolved and endorsed as anomalous by ≥2 national
> space/defense agencies.
>
> **Failure:** neither criterion met by 2030-01-01.

Round 5 stress-tested this instrument before it matters. `rubric_calibration.py`
applied the frozen rubric, unchanged, to the ledger's historical dated claims
under a pre-specified protocol: a deterministic eligibility screen, then
blind-ish scoring in which claim text sets only the deadline while the
outcome is looked up from a frozen public-record fact table. Of 164 ledger
rows, **2 resolved open-contact claims** were scorable (the 2020 window
start; the 2025 "early markers" claim) and both score **failure** —
historical pass rate **0/2**. Fifty-five open-window claims (including every
2026/27 claim) are disclosed as not yet scorable, and the 2016 cluster —
documentary premieres and "everything will change" rhetoric — passes through
the screen and is excluded with reasons. The calibration's honest reading:
the rubric has perfect historical *specificity* — no event in the public
record has ever satisfied it, and the serialized near-miss review shows why
(2017 AATIP: "unknown," not explicit non-human-origin language; 2021 ODNI:
not endorsed anomalous by two agencies; 2023 hearings: testimony, not
verification; 2024 AARO: an affirmative *denial*) — while its *sensitivity*
is unknowable from a history containing no true positive. The baseline for
the 2027 watch is therefore this: a full or partial score at the deadline
would be unprecedented against the corpus's entire dated-claim history, and a
failure continues the documented base rate. Per the advisor's binding
constraint, the rubric is **frozen regardless of this outcome** — the
no-tuning clause is embedded in the code, the results JSON, and the analysis
README; a rubric fitted to the past would be worthless for 2027.

## 8. What remains blocked, and the audit trail

**Blocked.** The authorship question (stylometry of Anka-era vs. Bashar-era
transcripts) requires real transcripts, and this environment has no network
egress: the acquisition pilot (`acquisition.py`) fails per-ID with logged
timeouts, and **no transcript text was fabricated**. The module therefore
ships as a *registered report*: the target list, the WER gates (15% overall /
10% function-word, with a mandatory Whisper hallucination screen, and the
disclosed caveat that these gates are optimistic on 1984–96 cassette audio),
and the 6+6 matched-pair pilot whose empirical ΔCE variance must replace the
panel's earlier asserted power statement before any stylometry claim runs.
The protocol is the deliverable when the data cannot be.

**Audit trail (five rounds).** Round 1 set the program; round 2 froze the
design, lexicon, and rubric under advisor amendments (absolute freeze hash,
stated-n rule, CI-based P2, tightened partial criteria). Round 3 implemented
the pipeline; the advisor's audit found four discrepancies — a doubled
exclusion count (76 vs. the true 38), a silently swallowed exception that had
dropped the E5 cross-check, a provenance block listing files never read, and
a residual-direction sentence contradicting its own figure — plus an E2/E3
conflation that had upgraded an uncontrolled p into a headline. Round 4 fixed
all of them (verifiably: the advisor re-ran the modules and reproduced every
digit), added the doctrine-dynamics module, and caught one new overprecision
— the degenerate [1.0, 1.0] velocity CI — mandating the surgery applied in
round 5. Round 5 (this report) applied the surgery, re-ran everything clean
at seed 42, added the rubric calibration under the no-tuning clause, and
consolidated. Every fix is serialized in the results JSONs, corpse on
display; no primary result changed under any fix. The Holm family stands at
exactly four tests, P3 alone significant.

**What ships.** With this report: the evidence layer (`results/*.json` as
machine-readable findings; `results/ledger.csv` as a downloadable
164-row dataset), figures F1–F8 badged, the frozen rubric as a standalone
timestamped pre-registration page, and the acquisition registered-report
appendix. What does not ship: the decorative 10⁻¹⁷⁵ without its
pseudo-replication caveat, any "honest forecasting" sentence, any unbadged
exploratory claim, and any version of the slip-velocity headline without its
IQR. If a reader remembers one sentence, it should be the honest one: *the
prophecy's deadlines fail on schedule, the packaging predicts the content,
the vocabulary never changes while the emphasis never holds still — and the
instrument that could settle the truth of it is frozen, published, and
waiting for 2027.*

## 9. Limitations

The digests are pipeline-generated summaries, not transcripts; per-question
tags are not stored, so P3/P4 are digest-level claims about estimated share
vectors. Every reliable-date prediction is post-2015, so era control rests
entirely on the partial correlation. Window-drift points are restatements of
canonical windows, not independent events; the 73 flips are non-independent
ratios of 35 rows; the 5–10y Δ bin has n = 3. E5's permutation inherits
within-video clustering. The calibration's resolved cohort is small (n = 2)
because the doctrine keeps its windows open — itself a datum. And the
standing quietism applies: nothing here measures whether Bashar exists. What
it measures is how the promise behaves — and on that, the corpus has been
remarkably forthcoming.

*— The Bashar-Index panel: Coder-Expert (rounds 1–5) and Advisor-Skeptic
(rounds 1–4 audits). Evidence layer: `analysis/results/*.json`,
`analysis/results/ledger.csv`, figures F1–F8, all seed 42, all badged.*
