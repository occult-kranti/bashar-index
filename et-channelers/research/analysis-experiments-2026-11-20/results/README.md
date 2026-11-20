# Results of the registered hypotheses

One row per registered hypothesis, whatever its outcome. A hypothesis that leaves the paper's headline claims
stays in this table. Numbers only; creators are never named.

| Id | Hypothesis | State | Estimate | Verdict by the registered rule | Reading |
|---|---|---|---|---|---|
| H1 | The claimed voice is slower than the creator's own voice | not run | | | waits for model labels |
| H2 | Checkable forecasts are worded less firmly | not run | | | waits for model labels |
| H3 | First-person singular is denser at the trimmed edges of a recording than in its middle | **tested 2026-11-20** | U = 0.169 on 17 hold-out creators, 169 recordings (90% interval -0.130 to 0.495; shift p = 0.0007) | supported | **dropped by the owner 2026-11-20**: fragile, see below |
| H4 | Fewer contractions in the embodied claimed voice | not run | | | waits for model labels |
| H5 | World claims in channelled recordings, practice in own-voice talks | not run | | | waits for model labels |
| H6 | The claimed voice rarely asks listeners to buy or enrol | not run | | | waits for model labels |
| H7 | More alike near almanac dates | not run | | | waits for the replication wave |
| H8 | The H3 contrast is larger than in sermons and wellness talks | not run | | | waits for the comparison set; rests on the contrast of the dropped H3, so its place is an open decision |
| H9 | Same family of beings: shared subject matter, not shared style | not run | | | waits for model labels |
| H10 | Passed dates are returned to less often | not run | | | waits for the replication wave |

## H3 in full

The procedure was frozen in [`../registry.md`](../registry.md) and committed before any hold-out transcript
was read; the code is [`../code/h3_position.py`](../code/h3_position.py). Files:
[`h3-holdout.json`](h3-holdout.json) (the registered test) and
[`h3-seen-exploratory.json`](h3-seen-exploratory.json) (the 61 creators seen earlier; exploratory).

| | Hold-out creators (registered test) | Seen creators (exploratory) |
|---|---|---|
| Creators, recordings | 17, 169 | 61, 558 |
| U, three minutes trimmed from each end, artefact filter on | 0.169 | 0.019 |
| 90% interval over creators | -0.130 to 0.495 | -0.129 to 0.165 |
| One-sided p against circular shifts | 0.0007 | 0.12 |
| Creators with a positive U | 9 of 17 | 36 of 61 |
| First-person singular per 1,000 words, edges against middle | 29.1 against 26.0 | 29.2 against 28.8 |
| U without the artefact filter | 0.166 | 0.019 |
| U without the trim (reported, not tested) | 0.348 | 0.427 |

**What the registered rule says.** Supported: the shift test passes the strictest Holm threshold (0.005) and
the estimate is above the smallest effect of interest (0.10).

**Why the result is fragile.** Three things point the other way, and they are stated here so that the verdict
is not read for more than it is.

1. The interval over creators includes zero, and only 9 of the 17 creators have a positive U. A few creators
   with a large contrast carry the mean.
2. The 61 creators seen earlier, a sample three and a half times larger, show no trimmed contrast (0.019).
   The hold-out is the tail of the transcription run, not a random draw.
3. The two procedures answer different questions. The circular shift asks whether position matters in these
   recordings at all, and it does not count the differences between creators as uncertainty. The interval
   does. The catalogue's own first rule makes the creator the unit, and by that standard the hold-out cannot
   tell 0.169 from zero: it was sized to detect about 0.54.

**Reading.** With the first and last three minutes removed, the evidence that self-reference recedes inside a
recording is weak and inconsistent between the two samples. Without the trim the contrast is large in both
(0.35 and 0.43): the surplus of "I" sits in the first and last three minutes.

**Decision.** The owner dropped H3 on 2026-11-20 after reading this result (registry amendment A6). It is
out of the claims of the paper and it is closed: no further confirmatory test, on the replication wave or
elsewhere. This row and the two result files stay, so that the count of hypotheses tested is honest: one
tested, none claimed so far. Holm correction still counts H3 as run. The untrimmed observation remains as a
description of how recordings open and close.

**What this changes for the hypotheses not yet run** (amendment made after seeing H3, in the stricter
direction): a hypothesis is called supported only if its registered test passes and the 90% interval over
creators excludes zero. This is recorded as amendment A5 in the registry.
