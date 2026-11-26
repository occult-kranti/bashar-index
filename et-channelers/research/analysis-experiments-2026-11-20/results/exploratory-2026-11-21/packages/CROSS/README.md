# Package CROSS: cross-instrument outputs on seen creators

Exploratory (registry A2); not a test of H1-H10.

Outputs of the exploratory reporting plan (section 6.3 and 6.7) made on the 71 seen creators after the first round.
Every table is a distribution or a cohort-level estimate; no row describes a creator, a recording or a title. Every label
is model-coded and not checked by a person; each CSV's header and each figure's caption names the verification that
exists. Agreement between models or methods is agreement, never accuracy. Choices that the plan and the programme left
open were fixed in each script before its first run and are labelled "added after the exploratory reporting plan";
changes made on verification (2026-11-22) are labelled as such.

| Plan id | Files | What |
|---|---|---|
| CAL-f | `cal-f-eligibility.csv`, `cal-f-null-centre.csv` | Eligible seen creators per registered rule from the first-round labels (frozen eligibility code), with the registered and the amended minimum, the projection onto the hold-out creators with English recordings (shares only; a post hoc check, not a forecast), and the null centre of each registered statistic on seen labels (CAL part a). CAL parts b and c on labels: not built in this round (no model call needed); part d: the simulation battery stands in (registry 15:14 (2)). |
| PT-cd | `pt-c-written-spoken.csv`, `pt-c-paired-shares.png`, `pt-d-chapters.csv` | Written (page) against spoken asks per ask class, with a paired creator-level difference, between and within creators; creator-written chapter starts against model voice boundaries, against circular shifts. The TC part: not run. |
| RX-CB | `rx-cb-curve.csv`, `rx-cb-curve.png`, `rx-cb-spans-opened.csv` | Distance of framing-cue hits (cue counts) to model claimed-voice boundaries against circular shifts and placebo lists; share of claimed-voice spans opened by a cue. Points of the curve removed by the increment guard (see Small cells) are not released. |
| MTMM | `mtmm-matrix.csv`, `mtmm-summary.csv`, `mtmm-pass-list.csv` | Creator-level agreement of three constructs by four methods (subject not run), the 4 x 4 summary and the convergent and discriminant pass list, with each measure's input and the pairs that share an input marked. Not a human check. The timeline rows of TL-7.8 are package TL's (`TL/public/tl-7-8-mtmm-rows.csv`). |
| BR-y | `br-y-years-numbers.csv` | Years and numbers of the recognizer's text against other machine texts of the same recordings (agreement of two machines, not an error rate; BR-b holds the error rates) and against the page text. |
| NE-F | `ne-f-30pct-criterion.csv` | The full pass was not run (needs model calls); the no-model part, the 30% criterion on claimed-voice windows, is computed on the NE pilot's speech windows. |

## MTMM measures

Each measure is one share per seen creator. Input in brackets.

| Construct | Small model | Middle model | Rule | Page |
|---|---|---|---|---|
| voice | [transcript] recordings with a claimed-voice span (V2/V3, rule B) of 300 words or more | [transcript] the same, middle model, on the recordings it labelled in full | [transcript] recordings with an RX framing-cue hit (J1, J2a, J2b, J3; cue counts) | [title] transcribed recordings whose title is coded P1 (presented as carrying a source's words), title code of record |
| source family | [title] titles whose small-model reading names a star-people family | [title] the same, middle-model reading | [transcript] recordings with an RX star-peoples name hit (G1; cue counts) | [title] titles whose word-list cross-check (the title instrument's rule field) names a star-people family |
| asks | [transcript] recordings with a candidate the small critic read as a pay-or-enrol ask | [transcript] the same, middle critic, same candidates | [transcript] recordings with an RX price hit (F1) | [page description] recordings with a written pay-or-enrol ask (PT part b) |

Shared inputs: three of source family's four methods read only titles, so its convergent pass rests mainly on
title-only pairs (the pass list gives the median over the pairs that cross inputs beside it); the title presentation
code of record (voice, page) and the middle-model family code come from the same middle-model title reading where the
title was not adjudicated; the two ask cells read the same candidates and the two voice cells the same units.

## Small cells

Counts of creators below 5 are printed as "fewer than 5"; where two printed counts of nested groups would differ by 1
to 4, one is printed against the other ("all but fewer than 5 of N", or "of the base" where the other group is itself
printed as text), checked against the true size of every printed group (except CAL-f's H5 count, which its writer
checked against the 71 only; a separate check by the release verifier on 2026-11-22 found it nested only in its
own null base, which is printed as "19 and fewer than 5 more") and against the counts other outputs publish
for groups that hold these by definition (PT's creators with page text, with a written ask of a class and with
creator-written chapters; LAB's creators with a spoken ask of a class; BR-b's creators per reference class). A statistic is printed only where 5 or more
creators carry a non-zero value; agreement figures only where positive codes come from 5 or more creators and
disagreements from none or 5 or more. Where cells add up to a whole (written only, spoken only, both, neither), a second
cell is withheld beside a withheld one, so that none can be solved from the others; a normalised row that differs from
the exact row on the same items in 1 to 4 creators is withheld. A cumulative curve (RX-CB) is printed only at
distances where the step from the previous printed point (from 0 for the first) and the share beyond the last
printed point come from 0 or from 5 or more creators (increment guard); a point not printed widens the next
step.

## Interval levels

Interval levels differ between the outputs of this package and between packages; each CSV header and figure caption
states its own (lead's decision D18):

- CAL-f: the projections carry 90% creator-bootstrap intervals; the counts and the null means carry none.
- PT-cd: the shares and the paired written-minus-spoken difference carry 90% t intervals; the between-creator rho and
  the chapter shares 90% creator-bootstrap intervals; the within-creator permutations and the circular shifts are shown
  as 95% ranges of 999 draws.
- RX-CB: 90% creator-bootstrap intervals, against a 95% permutation-maximum band over the curve's points (distances)
  or a 95% range (spans opened) of 999 circular shifts.
- MTMM: 90% creator-bootstrap intervals.
- BR-y: 95% Clopper-Pearson intervals.
- NE-F: 90% creator-bootstrap intervals.

This section was added on 2026-11-22 by the release pass (plotting group X-VERCROSS) under the lead's decisions D13 and
D18; no number, row or other file changed.

The H5 exception and the increment guard in "Small cells" and the last sentence of the RX-CB row were added on
2026-11-22 by the release pass (plotting group X-VERCROSS) after the release verifier's report; rx_cb.py was
rerun with the guard, and no printed value changed other than the points it removes.

## Figures in the release

The PNG files named in this README are the package's own drawings, which a release does not copy (D56). Every output of the package is drawn in the release gallery (`gallery/index.html`; records in `gallery/manifest.json`), under these figure ids: BR-y: BR-y-fig-1; CAL-f: CAL-f-fig-1, CAL-f-fig-2, CAL-f-fig-3; MTMM: MTMM-fig-1, MTMM-fig-2; PT-cd: PT-cd-fig-1, PT-cd-fig-2, PT-cd-fig-3; RX-CB: RX-CB-fig-1, RX-CB-fig-2. Edited on 2026-11-26 in release pass 2's fix step (fix2, f01_edits.py; its SHA-256 is in the round's records), for privacy and consistency only.
