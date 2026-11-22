# Simulation battery (synthetic creators only)

Workers 2, wall time 666.6 s, CPU time in tasks 79458.4 s.

Null rows: rejection rate of the p that enters Holm, at the first Holm step (0.005) and at 0.05, with the Monte Carlo SE. Planted rows: mean estimate against the large-sample target (label error included) and the planted value, coverage of the 90% interval used for A5 and of the registered 95% interval, and the share of sets that reach 'supported' at the first Holm step.

Guarded columns (A10 guard, registry 03:08): the larger of the registered and the amended p, and support only where both versions meet the support conditions.

Coverage 90%: HKSJ for H1, H2 and H4; for H5 and H6 the interval the MH estimate carries (the wider of the creator-bootstrap percentile and the jackknife t interval, registry 2026-11-21 04:55 (j)), with the bootstrap percentile alone beside it; the creator bootstrap for H9 (creators, then recordings, cells re-rarefied in every draw, registry 2026-11-21 06:44 (4); 99 draws in the battery). Supported needs, for H5 and H6, both the t interval on OE and the MH interval to exclude zero (06:44 (5)).

| H | scenario | creators | planted | reps | reject 0.005 (SE) | reject 0.05 (SE) | reject 0.005 guarded | reject 0.05 guarded | mean estimate | target | planted value | coverage 90% | coverage 90% MH bootstrap only | coverage 95% | supported at first step | supported, both versions |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | null | 12 | 0 | 2000 | 0.004006 (0.0016) | 0.05208 (0.0049) | 0.004006 | 0.05208 | -0.0005101 | -8.48e-05 | 0 | 0.901 |  | 0.951 | 0 | 0 |
| H1 | plant_large | 12 | -0.15 | 500 | 1 (0.0032) | 1 (0.0097) | 1 | 1 | -0.1423 | -0.1422 | -0.15 | 0.884 |  | 0.952 | 1 | 1 |
| H1 | plant_sesoi | 12 | -0.05 | 500 | 0.602 (0.0032) | 0.922 (0.0097) | 0.602 | 0.922 | -0.0474 | -0.046 | -0.05 | 0.876 |  | 0.938 | 0.014 | 0.014 |
| H1 | null | 17 | 0 | 2000 | 0.005 (0.0016) | 0.0545 (0.0049) | 0.005 | 0.0545 | -0.0001013 | -8.48e-05 | 0 | 0.897 |  | 0.951 | 0 | 0 |
| H1 | plant_large | 17 | -0.15 | 500 | 1 (0.0032) | 1 (0.0097) | 1 | 1 | -0.1422 | -0.1422 | -0.15 | 0.89 |  | 0.948 | 1 | 1 |
| H1 | plant_sesoi | 17 | -0.05 | 500 | 0.868 (0.0032) | 0.988 (0.0097) | 0.868 | 0.988 | -0.04819 | -0.046 | -0.05 | 0.902 |  | 0.94 | 0.014 | 0.014 |
| H2 | null | 12 | 0 | 2000 | 0.003 (0.0016) | 0.0475 (0.0049) | 0.001 | 0.0345 | 0.002796 | 0.007529 | 0 | 0.8805 |  | 0.9405 | 0.002 | 0.001 |
| H2 | plant_large | 12 | -0.7 | 500 | 0.932 (0.0032) | 1 (0.0097) | 0.93 | 1 | -0.364 | -0.3601 | -0.3441 | 0.87 |  | 0.94 | 0.932 | 0.93 |
| H2 | plant_sesoi | 12 | -0.2 | 500 | 0.068 (0.0032) | 0.31 (0.0097) | 0.044 | 0.278 | -0.1005 | -0.08446 | -0.1029 | 0.868 |  | 0.92 | 0.068 | 0.044 |
| H2 | null | 17 | 0 | 2000 | 0.004 (0.0016) | 0.049 (0.0049) | 0.002 | 0.041 | 0.006334 | 0.007529 | 0 | 0.8785 |  | 0.938 | 0.0025 | 0.0015 |
| H2 | plant_large | 17 | -0.7 | 500 | 0.996 (0.0032) | 0.998 (0.0097) | 0.996 | 0.998 | -0.363 | -0.3601 | -0.3441 | 0.878 |  | 0.944 | 0.996 | 0.996 |
| H2 | plant_sesoi | 17 | -0.2 | 500 | 0.116 (0.0032) | 0.404 (0.0097) | 0.084 | 0.384 | -0.1004 | -0.08446 | -0.1029 | 0.86 |  | 0.926 | 0.116 | 0.084 |
| H4 | null | 12 | 0 | 2000 | 0.004 (0.0016) | 0.056 (0.0049) | 0.004 | 0.056 | 0.006229 | 0.002012 | 0 | 0.8915 |  | 0.945 | 0.0015 | 0.0015 |
| H4 | plant_large | 12 | 1 | 500 | 0.974 (0.0032) | 1 (0.0097) | 0.974 | 1 | 1.058 | 1.03 | 1 | 0.894 |  | 0.952 | 0.974 | 0.974 |
| H4 | plant_sesoi | 12 | 0.5 | 500 | 0.414 (0.0032) | 0.82 (0.0097) | 0.414 | 0.82 | 0.5247 | 0.5257 | 0.5 | 0.916 |  | 0.964 | 0.36 | 0.36 |
| H4 | null | 17 | 0 | 2000 | 0.0055 (0.0016) | 0.05 (0.0049) | 0.0055 | 0.05 | -0.005244 | 0.002012 | 0 | 0.904 |  | 0.945 | 0.0005 | 0.0005 |
| H4 | plant_large | 17 | 1 | 500 | 0.996 (0.0032) | 1 (0.0097) | 0.996 | 1 | 1.058 | 1.03 | 1 | 0.92 |  | 0.966 | 0.996 | 0.996 |
| H4 | plant_sesoi | 17 | 0.5 | 500 | 0.674 (0.0032) | 0.946 (0.0097) | 0.674 | 0.946 | 0.5347 | 0.5257 | 0.5 | 0.89 |  | 0.936 | 0.516 | 0.516 |
| H5 | null | 12 | 0 | 2000 | 0.0065 (0.0016) | 0.0565 (0.0049) | 0.0005 | 0.0055 | 0.002562 | -0.01179 | 0 | 0.888 | 0.839 | 0.939 | 0.0065 | 0.0005 |
| H5 | plant_large | 12 | 0.8 | 500 | 1 (0.0032) | 1 (0.0097) | 0.188 | 0.188 | 0.8041 | 0.7852 | 0.8 | 0.902 | 0.834 | 0.954 | 1 | 0.188 |
| H5 | plant_sesoi | 12 | 0.4 | 500 | 0.674 (0.0032) | 0.962 (0.0097) | 0.098 | 0.162 | 0.403 | 0.3815 | 0.4 | 0.914 | 0.854 | 0.968 | 0.674 | 0.098 |
| H5 | null | 17 | 0 | 2000 | 0.0055 (0.0016) | 0.0505 (0.0049) | 0.0015 | 0.018 | 0.00273 | -0.01179 | 0 | 0.8995 | 0.86 | 0.947 | 0.0055 | 0.0015 |
| H5 | plant_large | 17 | 0.8 | 500 | 1 (0.0032) | 1 (0.0097) | 0.982 | 0.982 | 0.809 | 0.7852 | 0.8 | 0.884 | 0.846 | 0.924 | 1 | 0.982 |
| H5 | plant_sesoi | 17 | 0.4 | 500 | 0.904 (0.0032) | 0.998 (0.0097) | 0.748 | 0.952 | 0.401 | 0.3815 | 0.4 | 0.898 | 0.872 | 0.944 | 0.904 | 0.748 |
| H6 | null | 12 | 1 | 2000 | 0.0005045 (0.0016) | 0.0338 (0.0049) | 0.0005045 | 0.03229 | 0.01659 | 0.0236 | 0 | 0.912 | 0.851 | 0.958 | 0.0005 | 0.0005 |
| H6 | null_burst | 12 | 1 | 2000 | 0.0015 (0.0016) | 0.0425 (0.0049) | 0.001 | 0.0355 | -0.001673 | 0.0236 | 0 | 0.9415 | 0.8585 | 0.9825 | 0.0015 | 0.001 |
| H6 | null_gapped | 12 | 1 | 2000 | 0.0025 (0.0016) | 0.041 (0.0049) | 0.0025 | 0.0395 | -0.06785 | 0.0236 | 0 | 0.9448 | 0.8694 | 0.9679 | 0.001 | 0.001 |
| H6 | null_heterogeneous | 12 | 1 | 2000 | 0.001105 (0.0017) | 0.03204 (0.0051) | 0.001105 | 0.03204 | 0.003799 | 0.0236 | 0 | 0.917 | 0.845 | 0.96 | 0.001 | 0.001 |
| H6 | null_sparse_low_share | 12 | 1 | 2000 | 0.0025 (0.0016) | 0.0395 (0.0049) | 0.0015 | 0.019 | -0.02588 | 0.0236 | 0 | 0.935 | 0.859 | 0.9785 | 0.002 | 0.0005 |
| H6 | plant_large | 12 | 0.25 | 500 | 0.3623 (0.0035) | 0.8237 (0.011) | 0.3623 | 0.8237 | -1.456 | -1.303 | -1.386 | 0.9456 | 0.8407 | 0.9718 | 0.284 | 0.284 |
| H6 | plant_sesoi | 12 | 0.5 | 500 | 0.08 (0.0032) | 0.3432 (0.01) | 0.07789 | 0.3389 | -0.6676 | -0.7382 | -0.6931 | 0.898 | 0.838 | 0.946 | 0.074 | 0.072 |
| H6 | null | 17 | 1 | 2000 | 0.003 (0.0016) | 0.0385 (0.0049) | 0.0025 | 0.0355 | -0.0005649 | 0.0236 | 0 | 0.9055 | 0.85 | 0.954 | 0.0015 | 0 |
| H6 | null_burst | 17 | 1 | 2000 | 0.0035 (0.0016) | 0.04 (0.0049) | 0.003 | 0.034 | 0.0008458 | 0.0236 | 0 | 0.924 | 0.8705 | 0.9705 | 0.0035 | 0.003 |
| H6 | null_gapped | 17 | 1 | 2000 | 0.002 (0.0016) | 0.036 (0.0049) | 0.002 | 0.036 | -0.04509 | 0.0236 | 0 | 0.9585 | 0.8755 | 0.9845 | 0.002 | 0.002 |
| H6 | null_heterogeneous | 17 | 1 | 2000 | 0.002505 (0.0016) | 0.04459 (0.0049) | 0.002505 | 0.04459 | -0.01046 | 0.0236 | 0 | 0.9025 | 0.843 | 0.955 | 0.0005 | 0.0005 |
| H6 | null_sparse_low_share | 17 | 1 | 2000 | 0.0025 (0.0016) | 0.0395 (0.0049) | 0.002 | 0.0125 | -0.009133 | 0.0236 | 0 | 0.927 | 0.869 | 0.971 | 0.0025 | 0 |
| H6 | plant_large | 17 | 0.25 | 500 | 0.536 (0.0032) | 0.894 (0.0097) | 0.536 | 0.894 | -1.398 | -1.303 | -1.386 | 0.93 | 0.844 | 0.956 | 0.522 | 0.522 |
| H6 | plant_sesoi | 17 | 0.5 | 500 | 0.15 (0.0032) | 0.516 (0.0097) | 0.148 | 0.516 | -0.6953 | -0.7382 | -0.6931 | 0.892 | 0.836 | 0.95 | 0.142 | 0.128 |
| H9 | null | 12 | 0 | 1000 | 0.004 (0.0022) | 0.054 (0.0069) | 0.004 | 0.054 | 0.006759 | 0.05044 | 0 | 1 |  |  | 0 | 0 |
| H9 | plant_large | 12 | 0.12 | 200 | 0.99 (0.005) | 0.995 (0.015) | 0.99 | 0.995 | 0.9257 | 0.8795 |  | 1 |  |  | 0.99 | 0.99 |
| H9 | plant_sesoi | 12 | 0.06 | 200 | 0.135 (0.005) | 0.475 (0.015) | 0.135 | 0.475 | 0.2515 | 0.2338 |  | 1 |  |  | 0.025 | 0.025 |
| H9 | null | 17 | 0 | 1000 | 0.006 (0.0022) | 0.049 (0.0069) | 0.006 | 0.049 | -0.0001822 | 0.05044 | 0 | 1 |  |  | 0 | 0 |
| H9 | plant_large | 17 | 0.12 | 200 | 1 (0.005) | 1 (0.015) | 1 | 1 | 0.9114 | 0.8795 |  | 1 |  |  | 1 | 1 |
| H9 | plant_sesoi | 17 | 0.06 | 200 | 0.2 (0.005) | 0.615 (0.015) | 0.2 | 0.615 | 0.2426 | 0.2338 |  | 1 |  |  | 0.055 | 0.055 |

## H6: the amended p, its two halves and the references it replaced

Same sets, rejection rates at 0.005 / 0.05. Amended p (registry 2026-11-21 11:08 (1), the row's p in the table above): the larger of the cluster p and the sign-flip of OE. Cluster p: the conditional Monte Carlo reference that draws each cluster of asks (asks within 5 units of each other, chaining, registry 2026-11-21 12:52 (1)) as one unit with the recording's claimed share (11:08 (1)). Sign-flip of OE: the creator sign-flip of the OE centred per recording (06:44 (3) to 09:19 (1)). Ask-level p: the conditional reference that draws asks one by one (09:19 (1) to 11:08 (1)). Pooled OE: the sign-flip of CAL-A11's pooled OE (before 06:44 (3)). Amended p, window 1 (11:08) and window 10: the amended p with the clusters of 11:08 (the same, overlapping or adjacent units) and of the 10-unit sensitivity row (12:52 (1)). Guarded: the larger of the amended and the registered p (A10 guard). 9,999 Monte Carlo draws of each conditional reference in the battery (99,999 in the analysis). Scenarios: null_heterogeneous, ask rates that differ between a creator's recordings with their claimed share; null_sparse_low_share, claimed shares below one half and 1 to 3 asks a creator; null_burst, 1 or 2 bursts of 2 to 4 asks a creator in one voice at claimed shares 0.3 to 0.7; null_gapped, one burst of 2 to 4 asks a creator in one voice whose consecutive asks lie 1 to 3 units apart, at claimed shares below one half (12:52 (1)); no difference inside any recording in the null scenarios.

| scenario | creators | reps | amended p | cluster p | sign-flip of OE | ask-level p | pooled OE | amended p, window 1 (11:08) | amended p, window 10 | guarded | mean largest cluster |
|---|---|---|---|---|---|---|---|---|---|---|---|
| null | 12 | 2000 | 0.0005045 / 0.0338 | 0.002523 / 0.04188 | 0.002018 / 0.03935 | 0.004036 / 0.04692 | 0.002018 / 0.03935 | 0.0005045 / 0.03532 | 0.0005045 / 0.0333 | 0.0005045 / 0.03229 | 2 |
| null_burst | 12 | 2000 | 0.0015 / 0.0425 | 0.0015 / 0.0465 | 0.0015 / 0.05 | 0.06 / 0.1565 | 0.001 / 0.047 | 0.0015 / 0.0425 | 0.0015 / 0.042 | 0.001 / 0.0355 | 4.25 |
| null_gapped | 12 | 2000 | 0.0025 / 0.041 | 0.0025 / 0.041 | 0.016 / 0.0735 | 0.0555 / 0.1605 | 0.029 / 0.0845 | 0.0155 / 0.0735 | 0.002 / 0.04 | 0.0025 / 0.0395 | 3.98 |
| null_heterogeneous | 12 | 2000 | 0.001105 / 0.03204 | 0.001657 / 0.04309 | 0.003867 / 0.03978 | 0.001657 / 0.04696 | 0.01492 / 0.1309 | 0.001105 / 0.03315 | 0.001105 / 0.03204 | 0.001105 / 0.03204 | 2.23 |
| null_sparse_low_share | 12 | 2000 | 0.0025 / 0.0395 | 0.0025 / 0.04 | 0.012 / 0.0775 | 0.0035 / 0.04 | 0.0125 / 0.074 | 0.0035 / 0.0395 | 0.0025 / 0.0385 | 0.0015 / 0.019 | 1.3 |
| plant_large | 12 | 500 | 0.3623 / 0.8237 | 0.5266 / 0.872 | 0.372 / 0.8237 | 0.5411 / 0.8744 | 0.3841 / 0.8164 | 0.3671 / 0.8237 | 0.3623 / 0.8213 | 0.3623 / 0.8237 | 1.67 |
| plant_sesoi | 12 | 500 | 0.08 / 0.3432 | 0.1537 / 0.4 | 0.09684 / 0.3621 | 0.1663 / 0.4042 | 0.1095 / 0.3663 | 0.08211 / 0.3411 | 0.08 / 0.3432 | 0.07789 / 0.3389 | 1.76 |
| null | 17 | 2000 | 0.003 / 0.0385 | 0.0045 / 0.051 | 0.004 / 0.044 | 0.005 / 0.053 | 0.0035 / 0.041 | 0.003 / 0.038 | 0.002 / 0.037 | 0.0025 / 0.0355 | 2.13 |
| null_burst | 17 | 2000 | 0.0035 / 0.04 | 0.004 / 0.0425 | 0.004 / 0.0465 | 0.0515 / 0.1575 | 0.004 / 0.0485 | 0.0035 / 0.041 | 0.003 / 0.04 | 0.003 / 0.034 | 4.36 |
| null_gapped | 17 | 2000 | 0.002 / 0.036 | 0.002 / 0.036 | 0.0095 / 0.0775 | 0.0575 / 0.155 | 0.02 / 0.0885 | 0.0095 / 0.0775 | 0.002 / 0.0355 | 0.002 / 0.036 | 4 |
| null_heterogeneous | 17 | 2000 | 0.002505 / 0.04459 | 0.00501 / 0.05361 | 0.002505 / 0.05311 | 0.004509 / 0.05611 | 0.02104 / 0.1643 | 0.002505 / 0.04559 | 0.002004 / 0.04359 | 0.002505 / 0.04459 | 2.4 |
| null_sparse_low_share | 17 | 2000 | 0.0025 / 0.0395 | 0.0025 / 0.0395 | 0.009 / 0.0595 | 0.003 / 0.041 | 0.009 / 0.0645 | 0.003 / 0.0405 | 0.0025 / 0.04 | 0.002 / 0.0125 | 1.35 |
| plant_large | 17 | 500 | 0.536 / 0.894 | 0.682 / 0.92 | 0.544 / 0.894 | 0.698 / 0.922 | 0.56 / 0.896 | 0.536 / 0.894 | 0.536 / 0.892 | 0.536 / 0.894 | 1.85 |
| plant_sesoi | 17 | 500 | 0.15 / 0.516 | 0.214 / 0.564 | 0.162 / 0.536 | 0.228 / 0.576 | 0.166 / 0.55 | 0.15 / 0.52 | 0.144 / 0.514 | 0.148 / 0.516 | 1.88 |

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
