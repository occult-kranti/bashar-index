# Final certification — The Advisor-Skeptic, round 5 (loop 2)

I re-computed what was computable, re-grepped what was greppable, and read
every pixel of F7/F8. The round-5 surgery is real and correct. The artifact
still fails my criteria in four places — three small, one embarrassing — plus
one image-honesty violation in the folio specs.

## Verification by computation (what passed)

**E7 surgery: exact.** I rebuilt the flip distribution from the raw digests
via `window_rows` + `find_flips`: **35 window rows, 73 flips**; median
overshoot 2.0 y, median elapsed 1.0 y, median velocity **1.00 yr/yr, IQR
[0.50, 4.25]**; shares at/below/above 1.0 = 28.8/38.4/32.9% (quoted 29/38/33 ✓);
consecutive-restatement subset n = 38, median 1.0, IQR [1.0, 6.0]; elapsed ≥ 3 y
subset n = 32, median 0.4, IQR [0.4, 0.5]. Every serialized digit reproduces.
The [1.0, 1.0] CI is removed with its corpse on display
(`removed_degenerate_ci`), non-independence is disclosed wherever n = 73
appears, and the consecutive-restatement headline in FINAL_REPORT §4 is the
clean form I mandated. Criterion 3: **pass.**

**Consecutive-restatement headline: correct.** Verified above; note the two
subsets sum to 70, leaving three elapsed = 2 y pairs (velocities 3.0–3.5)
unmentioned in the prose — recoverable from the JSON definitions, so
non-blocking.

**No-tuning clause: present and honored.** The clause appears in the README
(block quote), the module header and `FROZEN_RUBRIC` comment, and twice in
`rubric_results.json` (note + dedicated field); the module writes only to
`results/`; the rubric text is consistent across README, module, and JSON.
Criterion 6: **pass** (but see blocker 4 on the report's "verbatim" quote).

**Holm family intact.** `family_holm.json`: exactly P1–P4, α = 0.05, P3 alone
significant; P2 enters CI-based as designed (the global Holm multiplier of 3 on
P3's p reflects three p-values plus P2's CI verdict — internally consistent
and disclosed in the policy line). `report.family_summary()` ran clean through
the Holm computation in my sandbox, failing only at file write (permissions) —
enforcement green. Criterion 4: **pass.**

**Stated-n sweep.** 88 (P1), 25 (P2), 75 videos, 949 questions, 20 tags, 164
ledger rows, 38 flagged (I recounted `year_reliable: false` in ledger.csv:
exactly 38), 99 (E5), 73-from-35, 126 nodes / 635 edges, 2 resolved / 55 open,
W = 0.009 (0.013 early / 0.019 late), mean ρ +0.16, turnover 47% — all match
the JSONs. E2 (ρ = −0.214, p = 0.0456) and E3 (ρ = −0.203, CI [−0.386,
−0.0046], naive p = 0.0592) are separated in the README, the JSON, and the
report; 0.0592 is never upgraded; 1e-175 is caged everywhere it appears.
Criteria 1 (mostly) and 2: **pass**, with one exception below.

**Quietism banner.** Present on `doctrine_results.json`,
`doctrine_dynamics_results.json`, the report's standing header, and F7/F8. No
panel site exists to badge; the report is the landing artifact and carries it.
Criterion 7: **pass** (site clause vacuous).

## Blockers

**B1 — Criterion 5 fails: `doctrine_results.json` provenance does not match
actual file reads.** `doctrine_graph.py` reads `teachings.md` (line 136) and
`videos.json` (lines 139, 261) and never reads `data/analysis.json` (no
`load_analysis` call, no open). The serialized provenance lists
`glossary.json`, `digests/*.json`, **`analysis.json`** — one input that was
never read, two that were read unlisted. This is the round-3 D3 defect class in
the one module whose provenance I had not yet grepped, and it contradicts
`predictions_results.json.provenance_correction_r3`, which itself states
"teachings.md is read by doctrine_graph.py." One-line fix: amend the inputs
list to what the code actually reads.

**B2 — "248-term glossary" is false.** `data/glossary.json` has **104**
entries; 248 is the glossary *related-edge* count
(`doctrine_results.json.graph.glossary_related_edges`). FINAL_REPORT §1 and §5
both assert a 248-term glossary. A stated corpus n that matches no JSON.

**B3 — P4 is invisible in the final report.** One of the four pre-registered
primaries — a null (slope −0.149, p = 0.741, n = 34 videos / 556 questions,
non-monotone) — receives no sentence anywhere in FINAL_REPORT; its n never
appears; F5 ships without prose. The equal-prominence honesty standard this
panel ratified applies to its own nulls.

**B4 — The §6 rubric quotation claims "verbatim" and is not.** The blockquote
drops "e.g. radar + optical — not two cameras" from the Partial criterion and
inserts "to 2028–29" into the claim-under-test parenthetical. The frozen text
itself is intact and consistent in README/module/JSON; the report's verbatim
claim is what is false. Restore the full text or strike "verbatim." Plate 6's
overlay has the same disease ("verbatim from the frozen rubric" over an
abridged summary).

**B5 — Plate 5 asserts two false claims about Peres et al. (2012).** The
caption's "increased frontal/parietal activity during psychography despite
reduced sensory guidance" inverts the study's headline finding: experienced
mediums showed **decreased** frontal rCBF (the increase was the less-expert
subgroup). And "control: five non-medium writers" invents a control group —
the control was within-subject non-trance writing. This violates the standing
rule that no image may assert a false claim. Fix the caption and label, or pull
the plate.

## Ruling (a): the 0/2 calibration — publishable-honest

Print it. The calibration makes no detection claim; it establishes historical
**specificity** and a base rate, with the Clopper–Pearson [0, 0.84] upper bound
disclosed as descriptive annotation alongside the doctrinal-correlation
caveat, badged EXPLORATORY, no p-value by design. The reason n = 2 — the
doctrine keeps its windows open; 55 open claims disclosed — is itself reported
as a datum, and sensitivity is declared unknowable from a history with no true
positive. The thinness is the finding, and it is labeled as such. That is the
standard.

## Ruling (b): image_specs.md honesty

Plates 1, 2, 3, 4, 7 are substantively honest: no burned-in numerals, banners
as overlays, captions that match the JSONs, the blocker drawn into Plate 2's
artwork itself. Three required fixes: B5 (Plate 5); B4's twin on Plate 6
("verbatim" → "summary" or restore full text); and Plate 3's overlay carries
E7 statistics (73 flips, IQR) under a Frontier-only banner while its figure
twin F7a is EXPLORATORY — mirror the badge on the overlay. Cosmetic: F7's
title collides with its subtitle text; F8's title clips at the right edge.

Minor, non-blocking: "three late-era digests" for the arity flag overstates —
one of the three (`mgSgI0ElfTI`) is year-unreliable; "at least two late-era,
one undated" is the supported sentence. "Tail of 6–24 yr/yr" rounds over one
5.0 value (README's "tail to 24" is accurate).

The E7 surgery is exemplary, the calibration module is disciplined, and the
family is clean. But I will not sign a final artifact whose provenance block
repeats the round-3 sin, whose corpus description invents a number, whose
nulls go unmentioned, and whose folio misstates the one external study it
cites. All five fixes are one-liners. Apply them and this ships.

NOT CERTIFIED — blockers: B1 (doctrine_graph provenance mismatch), B2
("248-term glossary"), B3 (P4 absent from the final report), B4 (false
"verbatim" on the rubric quote, report + Plate 6), B5 (Plate 5 misstates Peres
et al. 2012: effect direction and invented control group).

*— The Advisor-Skeptic, round 5, loop 2 (final). ~980 words.*

---

## Re-certification — The Advisor-Skeptic, round 5 (loop 3)

I re-verified each blocker against the artifacts, not the changelog.

**B1 — provenance: FIXED.** `doctrine_results.json.provenance.inputs` now lists
exactly `glossary.json`, `digests/*.json`, `teachings.md`, `videos.json`. I
grepped `doctrine_graph.py`: `teachings.md` opened at line 136,
`load_videos()` at lines 139/261, `load_glossary()`/`load_digests()` at
344/345, and `grep -n "load_analysis\|analysis.json" doctrine_graph.py`
returns nothing. Serialized provenance now matches actual reads, and agrees
with `predictions_results.json.provenance_correction_r3`. Criterion 5: pass.

**B2 — glossary count: FIXED.** FINAL_REPORT §1 and §6 both read "104-term
glossary (248 related-term edges)". I loaded `data/glossary.json`: exactly 104
entries; 248 is `graph.glossary_related_edges`, now attributed correctly. No
"248-term" string survives anywhere in the report or the folio.

**B3 — P4: FIXED.** §4 now reports the null with equal prominence, and every
digit reproduces from `demand_results.json`: slope −0.149 (JSON −0.14923),
one-sided p = 0.741, CI [−0.60, +0.30] (JSON [−0.6017, 0.3032]), n = 34
videos / 556 questions, `monotone_fitted_shares: false`, frozen base rate
16.8%. F5 has prose. Equal-prominence standard met.

**B4 — rubric quote: FIXED.** I diffed the §7 blockquote against
`rubric_calibration.py:FROZEN_RUBRIC` and README §"2027 prospective rubric".
The Partial criterion now carries "e.g. radar + optical — not two cameras";
the claim-under-test reads "currently stated as 2027 (in-corpus slips logged
as ratchet events, never edits to the rubric)" — the inserted "to 2028–29" is
gone. The "before 2030-01-01" deadline clauses match the frozen README text.
The "verbatim" claim is now true (modulo ≥/>= typography). Plate 6's overlay
is now labeled "abridged summaries of the frozen rubric" with a pointer to the
full text. Pass.

**B5 — Plate 5: FIXED and externally verified.** The caption now states
experienced mediums showed DECREASED frontal rCBF (hypofrontality) during
psychography relative to their own non-trance writing, with the increase
confined to the less-expert subgroup, and the control is within-subject
non-trance writing — no invented non-medium control group. I cross-checked
against the primary source (Peres et al. 2012, PLoS ONE, PMC3500298): ten
mediums, five experienced / five less expert; experienced showed consistently
lower rCBF (left anterior cingulate, right precentral gyrus, et al.) in trance
vs. their own control writing; less expert showed the opposite. The plate now
matches the study. Plate 3's overlay carries the EXPLORATORY banner mirroring
F7a. Pass.

**Sweep.** All seven `results/*.json` parse. Inflated-claim grep of
FINAL_REPORT is clean (no "248-term", no un-caveated 1e-175, no "honest
forecasting"). Both round-5 minors are fixed and verified: "tail of 5–24
yr/yr", and the arity sentence now reads "at least two late-era digests, with
a third digest undated — all three flagged year-unreliable" — confirmed
against `videos.json` (0htF1V0v6ec: 2026/unreliable; mgSgI0ElfTI:
null/unreliable; os4a7-7bnLw: 2025/unreliable).

All five blockers resolved; no new defects introduced. This ships.

CERTIFIED

*— The Advisor-Skeptic, round 5, loop 3 (re-certification).*
