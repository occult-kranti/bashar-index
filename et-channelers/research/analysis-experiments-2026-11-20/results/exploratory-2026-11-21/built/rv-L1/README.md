# rv-L1: what kinds of recordings the channels publish (interim sample)

Exploratory, paper review (registry A2/A7); not a test of H1-H10. Status: **superseded** as the census by LAB-K; both are
reported (plan 6.1, 6.8).

**What it asks.** What kinds of recordings the channels publish, and how often a recording holds a claimed voice
(channelled, or a relayed message), on an interim probability sample, before the first-round census (LAB-K) existed.

**Base.** 96 recordings of the 48 development creators (seen creators), two per creator: one drawn from the shorter and one
from the longer half of each creator's recordings; whole transcripts read in 2,500-word windows by an earlier snapshot of
the voice instrument (2026-11-20 19:45), the small model five times and the middle model once. Shares are creator-weighted
(each creator counts once; within-creator weights from the length strata), by recordings or by speech hours.

**What is shown.** `public/rv-l1-kinds-and-bands.csv`: shares of a creator's recordings by main kind (both weightings)
and by claimed-voice band, with 95% creator-bootstrap intervals. `public/rv-l1-agreement.csv`: two-model kappa on the
main kind (0.80, 95% 0.69 to 0.89), Fleiss' kappa over the five small runs (0.93), specific agreement and five-run
stability where they pass the agreement rule. `public/rv-l1-creators-without-a-claimed-recording.csv`: creators with no
sampled recording at 25% (19 of 48 under each model, as LAB already prints) and at 50%. The presence rows, the main-kind
row and the 25% count are printed beside LAB-K in `LAB/lab-k-beside-rv-l1.csv`, the comparison the plan asks for; they
are not repeated here. Figures (gallery group B-LV): the kinds under the small model, and the claimed-voice bands under
both models. Both go to the supplement: the plan row also names the dashboard for the kinds distribution, but under D24
(one figure of each overlapping pair on the dashboard) the dashboard shows LAB-K's census kinds figure, which supersedes
rv-L1, and LAB-K's figure that sets rv-L1 beside it.

**What is withheld and why.** Status superseded: LAB/public/lab-k-beside-rv-l1.csv already prints rv-L1's presence rows, main-kind row and its count of creators without a 25% recording beside LAB-K; this release adds the parts that file lacks. Not published: the middle model's shares for the channelled, relayed, guided-practice and advert kinds (they would differ from the printed small-model rows, or from LAB's printed claimed-voice row by difference, in fewer than 5 creators; the middle model's guided practice, own-voice talk and advert are printed as one pooled row); the small model's relayed share by speech hours (pooled into one claimed-voice row); the per-kind specific agreement and five-run stability of kinds whose disagreements come from fewer than 5 creators; each small run's kappa; the counts of creators without a recording at 10% and the range over runs and thresholds (counts 1 to 4 from a nested count).

**Interval level.** 95% creator-bootstrap percentile intervals (2,000 draws, rv-L1's own); rows pooled in this review
carry their own 95% interval (2,000 creator draws), except the pooled speech-hours row (a point sum, no interval).

**Caveats.** Model-coded by an earlier instrument; not checked by a person; agreement between models is agreement, not
accuracy. Two recordings per creator: counts of creators without a claimed recording depend mostly on how many recordings
each creator has. The main-kind share is a different quantity from the presence rows; the draft's "17 of 34" counted
presence and is replaced by them (LAB-K). Interim: LAB-K's census of all 1,293 seen recordings is the figure of record.

Small cells (plan section 3; addenda 1 and 2; registry 2026-11-21 22:33 and 2026-11-22 00:13; decisions D21 and D28): no cell rests on fewer than 5 creators; a statistic is printed only where 5 or more creators carry a non-zero value; an agreement figure only where the positive code comes from 5 or more creators in each reading and the items coded differently from 0 or 5 or more creators; a share near 100% whose misses come from 1 to 4 creators reads "not published (misses from fewer than 5 creators)", never a bound; of two figures whose difference rests on 1 to 4 creators one is not printed; categories under 5 creators are pooled, never suppressed one by one, and a withheld cell is never recoverable by subtraction from printed cells. Nested creator counts never differ by 1 to 4, also against counts already public. These rules hide values; they choose no estimate.

No hold-out or other-group file was opened (no contact): every file read holds seen creators only (development or check creators), or run metadata. No model was called. Exploratory (registry A2); not a test of H1-H10. Released by the release review (plan P10) on 2026-11-22; the output was built before the exploratory round and is reported as built, in the public-safe form of plan section 3.

**Fix pass (2026-11-22, release review B-LV, after the release verifier's findings).** The kinds figure moves to the supplement only (D24; the dashboard carries LAB-K's census figure); every figure's own footer now says model-coded and not checked by a person. No table value changed.

**Writers.** `lv_l1.py` sha256 `f8b666b02c9ddc6766fa93f3b9c7f33c08c841d16b662df861b37a025e3c0c48`; `lvcommon.py` sha256 `a630f290ccd1296164877c931d17b3d7e288edd2da41e14ba103435812dc5791`; `closure.py` sha256 `6f86c8f0c66a8f0ad3d0c7c67df5d00715de4bd88a2562393a8a91163c549422`; figures by `lv_figs.py` sha256 `b4b8f71c0187e84cf80aed6cf37434023da12d98f734b30655ffbf3ad1cd551f` from the public tables only. Written 2026-11-22T07:08:52Z (UTC, from the clock) by `lv_status.py`.
