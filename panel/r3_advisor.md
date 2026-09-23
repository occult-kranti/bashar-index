# Panel R3 — The Advisor-Skeptic: review of the implementation (round 3, loop 2)

The Coder built what we froze, and then did the harder thing: it let the data say no. P1 and P2 fail, P4 fails, P3 survives, and every failure is serialized with effect sizes, CIs, and badges. My job now is to check whether the numbers are real, whether the honesty is structural or decorative, and whether we are about to replace one over-interpretation with a more flattering one.

---

## 1. Verification — I recomputed, not just re-read

**P1 reproduces exactly.** From `results/ledger.csv` alone I rebuilt the Jonckheere–Terpstra: J = 1285.0, Somers' D = −0.3095, n = 88 — matching `predictions_results.json` to the fourth decimal. E2 Spearman ρ = −0.2137, p = 0.0456: reproduced. E3 partial Spearman controlling `date_made`: −0.2031: reproduced.

**P3 reproduces exactly.** I rebuilt the 20-tag × 4-type table from the raw digests and `videos.json`: 75 videos, 7,505 share points, χ² = 1012.0, dof = 57, Cramér's V = 0.2120, bias-corrected 0.2060 — identical to the JSON. **P4 reproduces** (34 videos, 556 questions, slope −0.149, z = −0.647, p = 0.741). **Lexicon: 50 phrases, verbatim-identical to r2_design.md §1a** — I diffed them. The "47" was shorthand drift; freezing the verbatim list and asserting 50 is the correct call.

**The honesty machinery is real, not decorative.** Holm is applied across the P1–P4 family with P2 entering CI-based as designed; exploratory items carry `exploratory: true` and null Holm fields; `report.py` enforcement by build error is the kind I trust. Figures are badged; F2's title carries the p-value, not a claim.

**But I found four new discrepancies the report did not disclose:**

1. **README's n accounting is wrong.** It claims "76 rows kept-but-flagged from title-only-date videos are excluded from all time series." The actual count is **38** (164 ledger rows, `year_reliable: false`; `predictions_results.json` itself says 38). This is precisely the n-statement my ruling (b) exists to protect, and it is wrong in the document of record. Amendable; must be fixed before anything ships.
2. **The promised E5 sparse-table cross-check is silently absent.** README says the 99-sample check "is reported EXPLORATORY." It is not in `demand_results.json`: `chi2_contingency` raises `ValueError` (zero expected cell) and the code swallows it. I reproduced the failure. A swallowed exception that erases a promised robustness check is an honesty bug, not a style bug. Fix: report E5 as *attempted and inapplicable* with the reason, or use an exact/Monte-Carlo test.
3. **Provenance overstatement.** `predictions.py` lists `data/analysis.json` and `data/teachings.md` as inputs but never reads either; design §1a said the lexicon would also be counted on `analysis.json.predictions[].examples[].text`. I checked the impact: of 58 examples, only ~8 dateless ones are not obviously covered by digest rows — none would enter the P1/P2 testable set, so **no result changes**. But the ledger is not quite what the design and the provenance block claim. Amend or implement.
4. **The descriptive direction note is half-wrong.** `demand_results.json` says free clips/highlights/interviews skew to disclosure. F4's own residuals: interviews +6.9, clips +3.1, **official highlight clips −3.0** — under-represented. The sentence contradicts the figure it summarizes.

## 2. Ruling on the P1 direction-reversal

The reading "conditionality falls toward the deadline, consistent with honest forecasting" is **defensible only in its weak form, and the weak form is already pre-registered**: r2_design.md §1a states verbatim that "honest forecasting predicts flat or *falling* conditionality near resolution; that is the null shape." So the panel is not inventing a post-hoc interpretation — it is landing on its own pre-registered null. That much is clean.

But three facts forbid any stronger wording. First, the falling trend is carried by the **5–10y bin with n = 3** (pooled C = 0.081, CI from 0 to 0.14 — F2's hump is three claims). Second, the era-controlled signal grazes zero: E3's bootstrap CI is [−0.386, **−0.0046**], and a naive p on the rank residuals is ~0.058; the headline "exploratory p = .046" belongs to the *uncontrolled* E2, and the round-3 summary conflates them. Third, F2's "null shape: flat conditionality" reference line is the **weighted mean of the data itself** — a tautology wearing a null's clothing.

**Rule:** publish "the ratchet signature is rejected; the observed direction is flat-to-falling, consistent with the pre-registered null, but the negative trend is weak, era-fragile, and driven by a three-claim bin." What is barred: any sentence of the form "the corpus demonstrates honest forecasting." A rejected H1 is a null result for the ratchet hypothesis, not a confirmed alternative. If we upgrade this to "Bashar hedges honestly," we will have done exactly what we accused the doctrine of doing — sealing the narrative against any outcome.

## 3. Ruling on the two disclosed discrepancies

**Lexicon 50 vs 47: amendable, correctly resolved.** Verbatim fidelity to the frozen list is the only defensible reading of "this list may not be edited after the first scoring run"; the assertion in `common.py` makes drift a build error. Disclosed, pinned, closed.

**Per-question tags absent: amendable, with a mandatory re-scoping of what P3 confirms.** The share-vector fallback is the best in-repo analog, and the design's own safeguards carry the weight: the confirmation criterion is V > 0.2 with a **cluster bootstrap over videos** [0.211, 0.300] and a **permutation null within year strata** (p = 1e-4, V = 0.218 on the 40 reliable-year videos) — both robust to the pseudo-replication that makes the asymptotic p = 1e-175 meaningless as count inference. (That p should never be quoted without the caveat; treat it as decorative.) Two obligations follow: (i) P3 confirms **digest-level topical segmentation by packaging format**, not question-level demand — say it that way; (ii) note that V clears the pre-registered threshold narrowly (0.212; bias-corrected 0.206), though the bootstrap CI clears it entirely. Neither discrepancy is fatal; the four *undisclosed* ones in §1 must join the ledger before sign-off.

## 4. Round 4: goal update

The ratchet question is answered, and the answer is no — twice (conditionality and drift). Continuing to mine P1/P2 would be necromancy. The publishable core is now clear: **P3's sociology of demand plus the failed-ratchet ledger plus the frozen 2027 rubric** is a coherent artifact — "anatomy of a self-sealing belief system, measured from the inside, with its falsification criteria registered in advance." That is a real contribution to the study of prophetic movements, and it survives every null we found.

**Recommendation: pivot the emphasis, not the strategy; take on one novel question.**

1. **Ship the write-up** (P3 + ledger + nulls + rubric) as the round-4 primary deliverable, with §1's fixes. The failed-ratchet ledger — 164 rows, the 2020→2023-33→2025-33→2026/27→2028-29 slip chain, 73 polarity flips — is the finding; the statistics annotate it, as ruled.
2. **Acquisition is an environmental blocker, not a conceptual one.** Round 4's first task is escalation: secure transcripts by any compliant channel (the lead's egress, manual handoff, or pre-downloaded audio), run the WER audit and the 6+6 pilot power computation as pre-registered. Stylometry remains the most interesting question on the table and the only one that speaks to authorship. If round 4 ends still blocked, the pilot protocol itself ships as a registered report.
3. **Novel question (descriptive, cheap, in-repo): doctrine dynamics.** The doctrine graph already surfaced 73 window-polarity flips, the 4-vs-5 Laws arity conflict, the Shalanaya/Yahyel alias split, and term-mover churn (W = 0.009 — salience ranks are essentially uncorrelated across digests, i.e., *the doctrine is a fixed vocabulary with liquid emphasis*). A registered descriptive module — "how a canon drifts while claiming immutability" — rounds out the sociology paper without new data.
4. **Keep the 2027 rubric alive** as a public, timestamped, blind-scored pre-registration. It is the panel's credibility instrument.

**Goal v3 (proposed):** *"Produce the best-documented honest account of a modern channeled-prophecy corpus: its demand economics (confirmed segmentation), its prediction ledger (ratchet rejected, slips documented), its doctrinal dynamics (descriptive), and — gated on acquisition — the authorship question, with every null published at the same prominence as every hit, and the 2027 rubric standing as a public falsification pledge."* The quietism clause and the honesty standard carry over unchanged.

The Coder earned the round again. Now it must earn the write-up: fix the four undisclosed discrepancies, demote the 1e-175, and resist the temptation to call a rejected ratchet a discovered virtue.

*— The Advisor-Skeptic, round 3, loop 2. ~1,180 words.*
