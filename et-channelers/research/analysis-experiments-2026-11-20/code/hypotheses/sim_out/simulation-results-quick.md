# Simulation battery (synthetic creators only)

Workers 4, wall time 497.4 s, CPU time in tasks 1895.9 s.

Null rows: rejection rate of the p that enters Holm, at the first Holm step (0.005) and at 0.05, with the Monte Carlo SE. Planted rows: mean estimate against the large-sample target (label error included) and the planted value, coverage of the 90% interval used for A5 and of the registered 95% interval, and the share of sets that reach 'supported' at the first Holm step.

Guarded columns (A10 guard, registry 03:08): the larger of the registered and the amended p, and support only where both versions meet the support conditions.

Coverage 90%: HKSJ for H1, H2 and H4; for H5 and H6 the interval the MH estimate carries (the wider of the creator-bootstrap percentile and the jackknife t interval, registry 2026-11-21 04:55 (j)), with the bootstrap percentile alone beside it; the creator bootstrap for H9 (creators, then recordings, cells re-rarefied in every draw, registry 2026-11-21 06:44 (4); 99 draws in the battery). Supported needs, for H5 and H6, both the t interval on OE and the MH interval to exclude zero (06:44 (5)).

| H | scenario | creators | planted | reps | reject 0.005 (SE) | reject 0.05 (SE) | reject 0.005 guarded | reject 0.05 guarded | mean estimate | target | planted value | coverage 90% | coverage 90% MH bootstrap only | coverage 95% | supported at first step | supported, both versions |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | null | 12 | 0 | 30 | 0.03333 (0.013) | 0.06667 (0.04) | 0.03333 | 0.06667 | 0.0005659 | -8.48e-05 | 0 | 0.8667 |  | 0.8667 | 0 | 0 |
| H1 | plant_large | 12 | -0.15 | 15 | 1 (0.018) | 1 (0.056) | 1 | 1 | -0.1446 | -0.1422 | -0.15 | 0.9333 |  | 0.9333 | 1 | 1 |
| H1 | plant_sesoi | 12 | -0.05 | 15 | 0.5333 (0.018) | 1 (0.056) | 0.5333 | 1 | -0.04526 | -0.046 | -0.05 | 0.8667 |  | 0.8667 | 0 | 0 |
| H1 | null | 17 | 0 | 30 | 0 (0.013) | 0.1667 (0.04) | 0 | 0.1667 | -0.006385 | -8.48e-05 | 0 | 0.7667 |  | 0.8 | 0 | 0 |
| H1 | plant_large | 17 | -0.15 | 15 | 1 (0.018) | 1 (0.056) | 1 | 1 | -0.1462 | -0.1422 | -0.15 | 1 |  | 1 | 1 | 1 |
| H1 | plant_sesoi | 17 | -0.05 | 15 | 1 (0.018) | 1 (0.056) | 1 | 1 | -0.04899 | -0.046 | -0.05 | 0.9333 |  | 0.9333 | 0 | 0 |
| H2 | null | 12 | 0 | 30 | 0 (0.013) | 0.03333 (0.04) | 0 | 0.03333 | 0.01674 | 0.007529 | 0 | 0.8667 |  | 0.9667 | 0 | 0 |
| H2 | plant_large | 12 | -0.7 | 15 | 0.9333 (0.018) | 1 (0.056) | 0.9333 | 1 | -0.3605 | -0.3601 | -0.3441 | 0.9333 |  | 0.9333 | 0.9333 | 0.9333 |
| H2 | plant_sesoi | 12 | -0.2 | 15 | 0.1333 (0.018) | 0.4 (0.056) | 0.06667 | 0.3333 | -0.1221 | -0.08446 | -0.1029 | 0.8667 |  | 0.9333 | 0.1333 | 0.06667 |
| H2 | null | 17 | 0 | 30 | 0.03333 (0.013) | 0.03333 (0.04) | 0 | 0.03333 | 0.01719 | 0.007529 | 0 | 0.9667 |  | 0.9667 | 0.03333 | 0 |
| H2 | plant_large | 17 | -0.7 | 15 | 1 (0.018) | 1 (0.056) | 1 | 1 | -0.3614 | -0.3601 | -0.3441 | 0.8667 |  | 0.9333 | 1 | 1 |
| H2 | plant_sesoi | 17 | -0.2 | 15 | 0.2 (0.018) | 0.4667 (0.056) | 0.06667 | 0.4667 | -0.1125 | -0.08446 | -0.1029 | 0.8667 |  | 0.8667 | 0.2 | 0.06667 |
| H4 | null | 12 | 0 | 30 | 0 (0.013) | 0 (0.04) | 0 | 0 | 0.007563 | 0.002012 | 0 | 1 |  | 1 | 0 | 0 |
| H4 | plant_large | 12 | 1 | 15 | 1 (0.018) | 1 (0.056) | 1 | 1 | 1.095 | 1.03 | 1 | 1 |  | 1 | 1 | 1 |
| H4 | plant_sesoi | 12 | 0.5 | 15 | 0.2667 (0.018) | 0.7333 (0.056) | 0.2667 | 0.7333 | 0.4702 | 0.5257 | 0.5 | 1 |  | 1 | 0.2 | 0.2 |
| H4 | null | 17 | 0 | 30 | 0 (0.013) | 0.03333 (0.04) | 0 | 0.03333 | 0.02643 | 0.002012 | 0 | 0.9 |  | 0.9333 | 0 | 0 |
| H4 | plant_large | 17 | 1 | 15 | 1 (0.018) | 1 (0.056) | 1 | 1 | 1.063 | 1.03 | 1 | 0.8667 |  | 0.8667 | 1 | 1 |
| H4 | plant_sesoi | 17 | 0.5 | 15 | 0.6667 (0.018) | 0.9333 (0.056) | 0.6667 | 0.9333 | 0.536 | 0.5257 | 0.5 | 0.8667 |  | 0.8667 | 0.5333 | 0.5333 |
| H5 | null | 12 | 0 | 30 | 0 (0.013) | 0 (0.04) | 0 | 0 | -0.01599 | -0.01179 | 0 | 0.9667 | 0.9333 | 1 | 0 | 0 |
| H5 | plant_large | 12 | 0.8 | 15 | 1 (0.018) | 1 (0.056) | 0.2 | 0.2 | 0.8243 | 0.7852 | 0.8 | 0.8 | 0.8 | 0.9333 | 1 | 0.2 |
| H5 | plant_sesoi | 12 | 0.4 | 15 | 0.8667 (0.018) | 1 (0.056) | 0 | 0.1333 | 0.4725 | 0.3815 | 0.4 | 0.8667 | 0.8 | 0.9333 | 0.8667 | 0 |
| H5 | null | 17 | 0 | 30 | 0 (0.013) | 0.06667 (0.04) | 0 | 0 | 0.006288 | -0.01179 | 0 | 0.9 | 0.9 | 0.9333 | 0 | 0 |
| H5 | plant_large | 17 | 0.8 | 15 | 1 (0.018) | 1 (0.056) | 1 | 1 | 0.8565 | 0.7852 | 0.8 | 0.8667 | 0.8 | 0.8667 | 1 | 1 |
| H5 | plant_sesoi | 17 | 0.4 | 15 | 1 (0.018) | 1 (0.056) | 0.8 | 0.9333 | 0.4199 | 0.3815 | 0.4 | 0.9333 | 0.9333 | 0.9333 | 1 | 0.8 |
| H6 | null | 12 | 1 | 30 | 0 (0.013) | 0.06667 (0.04) | 0 | 0.06667 | -0.05963 | 0.0236 | 0 | 0.9667 | 0.9 | 1 | 0 | 0 |
| H6 | null_burst | 12 | 1 | 30 | 0 (0.013) | 0.06667 (0.04) | 0 | 0.03333 | 0.0024 | 0.0236 | 0 | 0.9667 | 0.8 | 1 | 0 | 0 |
| H6 | null_gapped | 12 | 1 | 30 | 0 (0.013) | 0.06667 (0.04) | 0 | 0.06667 | 0.0475 | 0.0236 | 0 | 0.9655 | 0.8621 | 1 | 0 | 0 |
| H6 | null_heterogeneous | 12 | 1 | 30 | 0 (0.014) | 0.04 (0.044) | 0 | 0.04 | -0.05725 | 0.0236 | 0 | 0.8333 | 0.8 | 0.9333 | 0 | 0 |
| H6 | null_sparse_low_share | 12 | 1 | 30 | 0 (0.013) | 0 (0.04) | 0 | 0 | 0.01471 | 0.0236 | 0 | 0.9667 | 0.8333 | 1 | 0 | 0 |
| H6 | plant_large | 12 | 0.25 | 15 | 0.5 (0.022) | 0.6 (0.069) | 0.5 | 0.6 | -1.385 | -1.303 | -1.386 | 0.7333 | 0.6 | 0.8 | 0.3333 | 0.3333 |
| H6 | plant_sesoi | 12 | 0.5 | 15 | 0.07143 (0.019) | 0.2857 (0.058) | 0.07143 | 0.2857 | -0.7354 | -0.7382 | -0.6931 | 1 | 0.9333 | 1 | 0.06667 | 0.06667 |
| H6 | null | 17 | 1 | 30 | 0 (0.013) | 0.1 (0.04) | 0 | 0.1 | -0.1705 | 0.0236 | 0 | 0.8 | 0.7667 | 0.9 | 0 | 0 |
| H6 | null_burst | 17 | 1 | 30 | 0 (0.013) | 0.1 (0.04) | 0 | 0.06667 | 0.004492 | 0.0236 | 0 | 0.9667 | 0.8667 | 0.9667 | 0 | 0 |
| H6 | null_gapped | 17 | 1 | 30 | 0 (0.013) | 0.06667 (0.04) | 0 | 0.06667 | -0.1437 | 0.0236 | 0 | 0.9667 | 0.9 | 0.9667 | 0 | 0 |
| H6 | null_heterogeneous | 17 | 1 | 30 | 0 (0.013) | 0.1 (0.04) | 0 | 0.1 | -0.0654 | 0.0236 | 0 | 0.9 | 0.8667 | 0.9667 | 0 | 0 |
| H6 | null_sparse_low_share | 17 | 1 | 30 | 0 (0.013) | 0 (0.04) | 0 | 0 | -0.02586 | 0.0236 | 0 | 0.9667 | 0.9333 | 0.9667 | 0 | 0 |
| H6 | plant_large | 17 | 0.25 | 15 | 0.6 (0.018) | 1 (0.056) | 0.6 | 1 | -1.525 | -1.303 | -1.386 | 1 | 0.8667 | 1 | 0.6 | 0.6 |
| H6 | plant_sesoi | 17 | 0.5 | 15 | 0.2 (0.018) | 0.6667 (0.056) | 0.2 | 0.6667 | -0.6574 | -0.7382 | -0.6931 | 0.9333 | 0.9333 | 1 | 0.1333 | 0.1333 |
| H9 | null | 12 | 0 | 30 | 0.03333 (0.013) | 0.06667 (0.04) | 0.03333 | 0.06667 | 0.02286 | 0.05044 | 0 | 1 |  |  | 0 | 0 |
| H9 | plant_large | 12 | 0.12 | 15 | 1 (0.018) | 1 (0.056) | 1 | 1 | 0.9547 | 0.8795 |  | 1 |  |  | 1 | 1 |
| H9 | plant_sesoi | 12 | 0.06 | 15 | 0.06667 (0.018) | 0.4 (0.056) | 0.06667 | 0.4 | 0.2335 | 0.2338 |  | 1 |  |  | 0 | 0 |
| H9 | null | 17 | 0 | 30 | 0 (0.013) | 0.06667 (0.04) | 0 | 0.06667 | -0.006847 | 0.05044 | 0 | 1 |  |  | 0 | 0 |
| H9 | plant_large | 17 | 0.12 | 15 | 1 (0.018) | 1 (0.056) | 1 | 1 | 0.9385 | 0.8795 |  | 1 |  |  | 1 | 1 |
| H9 | plant_sesoi | 17 | 0.06 | 15 | 0.1333 (0.018) | 0.4 (0.056) | 0.1333 | 0.4 | 0.2293 | 0.2338 |  | 1 |  |  | 0 | 0 |

## H6: the amended p, its two halves and the references it replaced

Same sets, rejection rates at 0.005 / 0.05. Amended p (registry 2026-11-21 11:08 (1), the row's p in the table above): the larger of the cluster p and the sign-flip of OE. Cluster p: the conditional Monte Carlo reference that draws each cluster of asks (asks within 5 units of each other, chaining, registry 2026-11-21 12:52 (1)) as one unit with the recording's claimed share (11:08 (1)). Sign-flip of OE: the creator sign-flip of the OE centred per recording (06:44 (3) to 09:19 (1)). Ask-level p: the conditional reference that draws asks one by one (09:19 (1) to 11:08 (1)). Pooled OE: the sign-flip of CAL-A11's pooled OE (before 06:44 (3)). Amended p, window 1 (11:08) and window 10: the amended p with the clusters of 11:08 (the same, overlapping or adjacent units) and of the 10-unit sensitivity row (12:52 (1)). Guarded: the larger of the amended and the registered p (A10 guard). 9,999 Monte Carlo draws of each conditional reference in the battery (99,999 in the analysis). Scenarios: null_heterogeneous, ask rates that differ between a creator's recordings with their claimed share; null_sparse_low_share, claimed shares below one half and 1 to 3 asks a creator; null_burst, 1 or 2 bursts of 2 to 4 asks a creator in one voice at claimed shares 0.3 to 0.7; null_gapped, one burst of 2 to 4 asks a creator in one voice whose consecutive asks lie 1 to 3 units apart, at claimed shares below one half (12:52 (1)); no difference inside any recording in the null scenarios.

| scenario | creators | reps | amended p | cluster p | sign-flip of OE | ask-level p | pooled OE | amended p, window 1 (11:08) | amended p, window 10 | guarded | mean largest cluster |
|---|---|---|---|---|---|---|---|---|---|---|---|
| null | 12 | 30 | 0 / 0.06667 | 0 / 0.06667 | 0 / 0.06667 | 0.03333 / 0.06667 | 0 / 0.06667 | 0 / 0.06667 | 0 / 0.06667 | 0 / 0.06667 | 2.07 |
| null_burst | 12 | 30 | 0 / 0.06667 | 0 / 0.06667 | 0 / 0.06667 | 0.06667 / 0.2 | 0 / 0.1 | 0 / 0.06667 | 0 / 0.06667 | 0 / 0.03333 | 4.27 |
| null_gapped | 12 | 30 | 0 / 0.06667 | 0 / 0.06667 | 0.03333 / 0.06667 | 0.06667 / 0.1667 | 0.03333 / 0.1 | 0.03333 / 0.06667 | 0 / 0.06667 | 0 / 0.06667 | 4 |
| null_heterogeneous | 12 | 30 | 0 / 0.04 | 0 / 0.04 | 0 / 0.08 | 0 / 0.04 | 0.04 / 0.16 | 0 / 0.04 | 0 / 0.04 | 0 / 0.04 | 2.36 |
| null_sparse_low_share | 12 | 30 | 0 / 0 | 0 / 0 | 0 / 0.1 | 0 / 0 | 0 / 0.06667 | 0 / 0 | 0 / 0 | 0 / 0 | 1.23 |
| plant_large | 12 | 15 | 0.5 / 0.6 | 0.5 / 0.6 | 0.5 / 0.6 | 0.5 / 0.6 | 0.5 / 0.6 | 0.5 / 0.6 | 0.5 / 0.6 | 0.5 / 0.6 | 1.3 |
| plant_sesoi | 12 | 15 | 0.07143 / 0.2857 | 0.1429 / 0.2857 | 0.07143 / 0.2857 | 0.1429 / 0.2857 | 0.07143 / 0.2857 | 0.07143 / 0.2857 | 0.07143 / 0.2857 | 0.07143 / 0.2857 | 1.71 |
| null | 17 | 30 | 0 / 0.1 | 0 / 0.1 | 0 / 0.1 | 0 / 0.1 | 0 / 0.1 | 0 / 0.1 | 0 / 0.1 | 0 / 0.1 | 2.17 |
| null_burst | 17 | 30 | 0 / 0.1 | 0 / 0.1 | 0 / 0.1 | 0.1 / 0.1667 | 0 / 0.06667 | 0 / 0.1 | 0 / 0.1 | 0 / 0.06667 | 4.3 |
| null_gapped | 17 | 30 | 0 / 0.06667 | 0 / 0.06667 | 0.03333 / 0.1 | 0.1 / 0.2333 | 0.03333 / 0.1333 | 0.03333 / 0.1 | 0 / 0.06667 | 0 / 0.06667 | 4 |
| null_heterogeneous | 17 | 30 | 0 / 0.1 | 0 / 0.1 | 0 / 0.1667 | 0 / 0.1333 | 0.06667 / 0.2667 | 0 / 0.1 | 0 / 0.1333 | 0 / 0.1 | 2.37 |
| null_sparse_low_share | 17 | 30 | 0 / 0 | 0 / 0 | 0 / 0.03333 | 0 / 0.03333 | 0 / 0.03333 | 0 / 0.03333 | 0 / 0 | 0 / 0 | 1.47 |
| plant_large | 17 | 15 | 0.6 / 1 | 0.8667 / 1 | 0.6 / 1 | 0.8667 / 1 | 0.7333 / 1 | 0.6 / 1 | 0.6 / 1 | 0.6 / 1 | 1.73 |
| plant_sesoi | 17 | 15 | 0.2 / 0.6667 | 0.2 / 0.6667 | 0.2 / 0.6667 | 0.2 / 0.7333 | 0.1333 / 0.6667 | 0.2 / 0.6667 | 0.2 / 0.6667 | 0.2 / 0.6667 | 1.67 |

## The 'not determinable' boundary

| H | generated | eligible | minimum | determinable | raw p | registered-version p | Holm input p | verdict | uninformative |
|---|---|---|---|---|---|---|---|---|---|
| H1 | 11 | 11 | 12 | False | 0.0004883 | 0.0004883 | 1 | not determinable: too few eligible creators (11 of 12) | True |
| H1 | 12 | 12 | 12 | True | 0.0002441 | 0.0002441 | 0.0002441 | supported (model-coded) | False |
| H4 | 11 | 11 | 12 | False | 0.0004883 | 0.0004883 | 1 | not determinable: too few eligible creators (11 of 12) | True |
| H4 | 12 | 12 | 12 | True | 0.0002441 | 0.0002441 | 0.0002441 | supported (model-coded) | False |
| H6 | 11 | 11 | 12 | False | 0.08691 | 0.03564 | 1 | not determinable: too few eligible creators (11 of 12) | True |
| H6 | 12 | 12 | 12 | True | 0.007812 | 0.0004883 | 0.007812 | not determined (Holm step) | False |
| H2 | 8 | 8 | 9 | False | 0.007812 | 0.005 | 1 | not determinable in the amended version: too few eligible creators (8 of 9) (registered version: not determined (Holm step)) | True |
| H2 | 9 | 9 | 9 | True | 0.003906 | 0.005 | 0.005 | supported (model-coded) | False |
| H5 | 11 | 11 | 12 | False | 0.0004883 | 0.0169 | 1 | not determinable in both versions (amended: too few eligible creators (11 of 12); registered: too few eligible creators (6 of 12)) | True |
| H5 | 12 | 12 | 12 | True | 0.0004883 | 0.0001 | 0.0004883 | supported (model-coded) | False |
| H9 | 7 | 7 | 8 | False | 0.0015 | 0.0015 | 1 | not determinable in the amended version: too few eligible creators (7 of 8) (registered version: not determined (Holm step)) | True |
| H9 | 8 | 8 | 8 | True | 0.0005 | 0.0005 | 0.0005 | supported (model-coded) | False |
