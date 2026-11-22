# H6: levels of the amended p and the references it replaced, on constructed numbers

Registry 2026-11-21 11:08 (1) and 12:52 (1). Written 2026-11-21T13:13:58Z by simulate.h6_cluster_reference_levels (task fingerprint d97db4a2a7c4). Exact enumeration, no simulation: the data come from the true clusters (each cluster of a recording's asks in the claimed voice with the recording's claimed share s, all its asks with it), the tests read the clusters the rule sees; the probability, in percent, that each p is at most 0.005 / 0.05. Cluster p and ask-level p: conditional Monte Carlo tests with the stated draws (the analysis uses 99,999, the battery 9,999), their rejection probability given the data computed exactly from the binomial law of the draws; exact cluster test: the limit of many draws. Sign-flip of OE: stats.signflip_p over every joint outcome. Amended p: the larger of the cluster p and the sign-flip p, as h6_asks.amended_p. Kinds: burst, clusters of 2 to 4 asks on consecutive units (the rule sees them at any window); sparse_low_share and plain, single asks (clusters of one), where the cluster p and the ask-level p are the same test; gapped, one burst a creator whose consecutive asks lie 1 to 3 units apart, at claimed shares below one half, seen as one cluster under the window of 12:52 (1) (5 units) and as single asks under 11:08's adjacency rule (window 1); gapped_beyond_window, asks further apart than 5 units: the dependence the result says is not modelled, under 5 units and under the 10-unit sensitivity row.

## Monte Carlo draws 99999

| kind | case | joint outcomes | cluster p 0.005 / 0.05 | exact cluster test | ask-level p (09:19) | sign-flip of OE | amended p (max of cluster and sign-flip) |
|---|---|---|---|---|---|---|---|
| burst | 17 creators, one burst of 3, s = 0.3 | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |
| burst | 17 creators, one burst of 3, s = 0.5 | 18 | 0.12 / 2.45 | 0.12 / 2.45 | 7.17 / 16.62 | 0.12 / 2.45 | 0.12 / 2.45 |
| burst | 17 creators, one burst of 3, s = 0.7 | 18 | 0.32 / 4.03 | 0.32 / 4.03 | 4.03 / 10.46 | 0.07 / 4.03 | 0.07 / 4.03 |
| burst | 17 creators, one burst of 2, s = 0.3 | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 1.93 / 7.74 | 1.93 / 7.74 | 0.23 / 1.93 |
| burst | 17 creators, one burst of 4, s = 0.5 | 18 | 0.12 / 2.45 | 0.12 / 2.45 | 7.17 / 16.62 | 0.12 / 2.45 | 0.12 / 2.45 |
| burst | 12 creators, one burst of 3, s = 0.3 | 13 | 0.00 / 1.38 | 0.00 / 1.38 | 8.50 / 8.50 | 1.38 / 8.50 | 0.00 / 1.38 |
| burst | 17 creators, three bursts of 2, s = 0.5 | 1140 | 0.24 / 4.60 | 0.23 / 4.60 | 2.44 / 13.12 | 0.33 / 3.51 | 0.16 / 3.15 |
| burst | 17 creators, three bursts of 2, s = 0.3 | 1140 | 0.20 / 3.36 | 0.20 / 3.36 | 3.36 / 12.10 | 1.04 / 7.67 | 0.19 / 3.35 |
| burst | 17 creators, bursts of 2 and 4, s = 0.7 | 1140 | 0.30 / 4.81 | 0.30 / 4.87 | 7.55 / 16.10 | 0.17 / 2.82 | 0.12 / 2.75 |
| burst | 17 creators, a burst of 3 at s = 0.3 and one ask at s = 0.6 (two recordings) | 1140 | 0.30 / 4.24 | 0.30 / 4.24 | 4.24 / 12.14 | 1.29 / 6.14 | 0.29 / 4.16 |
| sparse_low_share | 17 creators, T = 1 single asks, s = 0.3 | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 0.23 / 1.93 | 1.93 / 7.74 | 0.23 / 1.93 |
| sparse_low_share | 17 creators, T = 2 single asks, s = 0.3 | 171 | 0.32 / 3.34 | 0.32 / 3.34 | 0.32 / 3.34 | 0.99 / 6.00 | 0.30 / 3.34 |
| sparse_low_share | 17 creators, T = 3 single asks, s = 0.2 | 1140 | 0.42 / 4.21 | 0.48 / 4.21 | 0.42 / 4.21 | 1.29 / 6.71 | 0.38 / 4.19 |
| sparse_low_share | 17 creators, T = 1 single asks, s = 0.2 | 18 | 0.00 / 2.25 | 0.00 / 2.25 | 0.00 / 2.25 | 2.25 / 11.82 | 0.00 / 2.25 |
| sparse_low_share | 12 creators, T = 1, s = 0.3 | 13 | 0.00 / 1.38 | 0.00 / 1.38 | 0.00 / 1.38 | 1.38 / 8.50 | 0.00 / 1.38 |
| sparse_low_share | 17 creators, T cycled 1, 2, 3 single asks, s = 0.3 | 10976 | 0.44 / 3.94 | 0.44 / 3.94 | 0.44 / 3.94 | 1.52 / 7.42 | 0.42 / 3.94 |
| plain | 17 creators, T = 3 single asks, s = 0.5 | 1140 | 0.24 / 4.60 | 0.23 / 4.60 | 0.24 / 4.60 | 0.33 / 3.51 | 0.16 / 3.15 |
| plain | 17 creators, T = 4 single asks, s = 0.5 | 5985 | 0.31 / 3.41 | 0.25 / 3.41 | 0.31 / 3.41 | 0.22 / 3.00 | 0.14 / 2.52 |
| plain | 12 creators, T = 4 single asks, s = 0.5 | 1820 | 0.28 / 2.97 | 0.28 / 2.97 | 0.28 / 2.97 | 0.14 / 2.45 | 0.09 / 2.08 |
| plain | 17 creators, T = 2 single asks, s = 0.6 | 171 | 0.31 / 4.44 | 0.31 / 4.44 | 0.31 / 4.44 | 0.27 / 4.09 | 0.15 / 3.50 |
| plain | 17 creators, two recordings (2 single asks at s = 0.4, 2 at s = 0.6) | 5985 | 0.44 / 3.13 | 0.44 / 3.13 | 0.44 / 3.13 | 0.22 / 2.95 | 0.17 / 2.40 |
| gapped | 17 creators, one burst of 3 asks 2 units apart, s = 0.3 (window 5) | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |
| gapped | 17 creators, one burst of 3 asks 3 units apart, s = 0.4 (window 5) | 18 | 0.21 / 4.64 | 0.21 / 4.64 | 4.64 / 12.60 | 1.23 / 4.64 | 0.21 / 4.64 |
| gapped | 17 creators, one burst of 2 asks 3 units apart, s = 0.3 (window 5) | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 1.93 / 7.74 | 1.93 / 7.74 | 0.23 / 1.93 |
| gapped | 17 creators, one burst of 4 asks 1, 2 and 3 units apart, s = 0.35 (window 5) | 18 | 0.07 / 3.27 | 0.07 / 3.27 | 10.28 / 23.48 | 3.27 / 10.28 | 0.07 / 3.27 |
| gapped | 12 creators, one burst of 3 asks 2 units apart, s = 0.3 (window 5) | 13 | 0.00 / 1.38 | 0.00 / 1.38 | 8.50 / 8.50 | 1.38 / 8.50 | 0.00 / 1.38 |
| gapped | 9 creators at s = 0.3 and 8 at s = 0.5, one burst of 3 asks 2 units apart (window 5) | 90 | 0.20 / 4.76 | 0.20 / 4.76 | 4.76 / 13.09 | 1.13 / 4.76 | 0.20 / 4.76 |
| gapped | 17 creators, one burst of 3 asks 2 units apart, s = 0.3 (window 1, the rule of 11:08) | 18 | 7.74 / 20.19 | 7.74 / 20.19 | 7.74 / 20.19 | 1.93 / 7.74 | 1.93 / 7.74 |
| gapped | 17 creators, one burst of 3 asks 3 units apart, s = 0.4 (window 1, the rule of 11:08) | 18 | 4.64 / 12.60 | 4.64 / 12.60 | 4.64 / 12.60 | 1.23 / 4.64 | 1.23 / 4.64 |
| gapped | 17 creators, one burst of 2 asks 3 units apart, s = 0.3 (window 1, the rule of 11:08) | 18 | 1.93 / 7.74 | 1.93 / 7.74 | 1.93 / 7.74 | 1.93 / 7.74 | 1.93 / 7.74 |
| gapped | 17 creators, one burst of 4 asks 1, 2 and 3 units apart, s = 0.35 (window 1, the rule of 11:08) | 18 | 3.27 / 10.28 | 3.27 / 10.28 | 10.28 / 23.48 | 3.27 / 10.28 | 3.27 / 10.28 |
| gapped | 12 creators, one burst of 3 asks 2 units apart, s = 0.3 (window 1, the rule of 11:08) | 13 | 8.50 / 8.50 | 8.50 / 8.50 | 8.50 / 8.50 | 1.38 / 8.50 | 1.38 / 8.50 |
| gapped | 9 creators at s = 0.3 and 8 at s = 0.5, one burst of 3 asks 2 units apart (window 1, the rule of 11:08) | 90 | 4.76 / 13.09 | 4.76 / 13.09 | 4.76 / 13.09 | 1.13 / 4.76 | 1.13 / 4.76 |
| gapped_beyond_window | 17 creators, one burst of 3 asks 6 units apart, s = 0.3 (window 5: beyond it) | 18 | 7.74 / 20.19 | 7.74 / 20.19 | 7.74 / 20.19 | 1.93 / 7.74 | 1.93 / 7.74 |
| gapped_beyond_window | 17 creators, one burst of 3 asks 2 and 7 units apart, s = 0.3 (window 5: beyond it) | 18 | 1.93 / 7.74 | 1.93 / 7.74 | 7.74 / 20.19 | 1.93 / 7.74 | 1.93 / 7.74 |
| gapped_beyond_window | 17 creators, one burst of 3 asks 6 units apart, s = 0.3 (window 10, the sensitivity row) | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |
| gapped_beyond_window | 17 creators, one burst of 3 asks 2 and 7 units apart, s = 0.3 (window 10, the sensitivity row) | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |

## Monte Carlo draws 9999

| kind | case | joint outcomes | cluster p 0.005 / 0.05 | exact cluster test | ask-level p (09:19) | sign-flip of OE | amended p (max of cluster and sign-flip) |
|---|---|---|---|---|---|---|---|
| burst | 17 creators, one burst of 3, s = 0.3 | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |
| burst | 17 creators, one burst of 3, s = 0.5 | 18 | 0.14 / 2.45 | 0.12 / 2.45 | 7.17 / 16.62 | 0.12 / 2.45 | 0.12 / 2.45 |
| burst | 17 creators, one burst of 3, s = 0.7 | 18 | 0.32 / 4.03 | 0.32 / 4.03 | 4.03 / 10.46 | 0.07 / 4.03 | 0.07 / 4.03 |
| burst | 17 creators, one burst of 2, s = 0.3 | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 1.93 / 7.74 | 1.93 / 7.74 | 0.23 / 1.93 |
| burst | 17 creators, one burst of 4, s = 0.5 | 18 | 0.14 / 2.45 | 0.12 / 2.45 | 7.17 / 16.62 | 0.12 / 2.45 | 0.12 / 2.45 |
| burst | 12 creators, one burst of 3, s = 0.3 | 13 | 0.00 / 1.38 | 0.00 / 1.38 | 8.50 / 9.39 | 1.38 / 8.50 | 0.00 / 1.38 |
| burst | 17 creators, three bursts of 2, s = 0.5 | 1140 | 0.31 / 4.53 | 0.23 / 4.60 | 2.50 / 12.98 | 0.33 / 3.51 | 0.17 / 3.12 |
| burst | 17 creators, three bursts of 2, s = 0.3 | 1140 | 0.24 / 3.36 | 0.20 / 3.36 | 3.36 / 12.10 | 1.04 / 7.67 | 0.23 / 3.35 |
| burst | 17 creators, bursts of 2 and 4, s = 0.7 | 1140 | 0.34 / 4.35 | 0.30 / 4.87 | 7.53 / 16.10 | 0.17 / 2.82 | 0.13 / 2.67 |
| burst | 17 creators, a burst of 3 at s = 0.3 and one ask at s = 0.6 (two recordings) | 1140 | 0.34 / 4.24 | 0.30 / 4.24 | 4.22 / 12.14 | 1.29 / 6.14 | 0.33 / 4.16 |
| sparse_low_share | 17 creators, T = 1 single asks, s = 0.3 | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 0.23 / 1.93 | 1.93 / 7.74 | 0.23 / 1.93 |
| sparse_low_share | 17 creators, T = 2 single asks, s = 0.3 | 171 | 0.32 / 3.34 | 0.32 / 3.34 | 0.32 / 3.34 | 0.99 / 6.00 | 0.30 / 3.34 |
| sparse_low_share | 17 creators, T = 3 single asks, s = 0.2 | 1140 | 0.33 / 4.21 | 0.48 / 4.21 | 0.33 / 4.21 | 1.29 / 6.71 | 0.30 / 4.19 |
| sparse_low_share | 17 creators, T = 1 single asks, s = 0.2 | 18 | 0.00 / 2.25 | 0.00 / 2.25 | 0.00 / 2.25 | 2.25 / 11.82 | 0.00 / 2.25 |
| sparse_low_share | 12 creators, T = 1, s = 0.3 | 13 | 0.00 / 1.38 | 0.00 / 1.38 | 0.00 / 1.38 | 1.38 / 8.50 | 0.00 / 1.38 |
| sparse_low_share | 17 creators, T cycled 1, 2, 3 single asks, s = 0.3 | 10976 | 0.41 / 4.17 | 0.44 / 3.94 | 0.41 / 4.17 | 1.52 / 7.42 | 0.40 / 4.17 |
| plain | 17 creators, T = 3 single asks, s = 0.5 | 1140 | 0.31 / 4.53 | 0.23 / 4.60 | 0.31 / 4.53 | 0.33 / 3.51 | 0.17 / 3.12 |
| plain | 17 creators, T = 4 single asks, s = 0.5 | 5985 | 0.35 / 3.41 | 0.25 / 3.41 | 0.35 / 3.41 | 0.22 / 3.00 | 0.14 / 2.52 |
| plain | 12 creators, T = 4 single asks, s = 0.5 | 1820 | 0.28 / 2.99 | 0.28 / 2.97 | 0.28 / 2.99 | 0.14 / 2.45 | 0.09 / 2.08 |
| plain | 17 creators, T = 2 single asks, s = 0.6 | 171 | 0.31 / 4.43 | 0.31 / 4.44 | 0.31 / 4.43 | 0.27 / 4.09 | 0.15 / 3.49 |
| plain | 17 creators, two recordings (2 single asks at s = 0.4, 2 at s = 0.6) | 5985 | 0.39 / 3.26 | 0.44 / 3.13 | 0.39 / 3.26 | 0.22 / 2.95 | 0.15 / 2.43 |
| gapped | 17 creators, one burst of 3 asks 2 units apart, s = 0.3 (window 5) | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |
| gapped | 17 creators, one burst of 3 asks 3 units apart, s = 0.4 (window 5) | 18 | 0.21 / 4.48 | 0.21 / 4.64 | 4.64 / 12.60 | 1.23 / 4.64 | 0.21 / 4.48 |
| gapped | 17 creators, one burst of 2 asks 3 units apart, s = 0.3 (window 5) | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 1.93 / 7.74 | 1.93 / 7.74 | 0.23 / 1.93 |
| gapped | 17 creators, one burst of 4 asks 1, 2 and 3 units apart, s = 0.35 (window 5) | 18 | 0.07 / 3.27 | 0.07 / 3.27 | 10.28 / 23.48 | 3.27 / 10.28 | 0.07 / 3.27 |
| gapped | 12 creators, one burst of 3 asks 2 units apart, s = 0.3 (window 5) | 13 | 0.00 / 1.38 | 0.00 / 1.38 | 8.50 / 9.39 | 1.38 / 8.50 | 0.00 / 1.38 |
| gapped | 9 creators at s = 0.3 and 8 at s = 0.5, one burst of 3 asks 2 units apart (window 5) | 90 | 0.20 / 4.29 | 0.20 / 4.76 | 4.76 / 13.09 | 1.13 / 4.76 | 0.20 / 4.29 |
| gapped | 17 creators, one burst of 3 asks 2 units apart, s = 0.3 (window 1, the rule of 11:08) | 18 | 7.74 / 20.19 | 7.74 / 20.19 | 7.74 / 20.19 | 1.93 / 7.74 | 1.93 / 7.74 |
| gapped | 17 creators, one burst of 3 asks 3 units apart, s = 0.4 (window 1, the rule of 11:08) | 18 | 4.64 / 12.60 | 4.64 / 12.60 | 4.64 / 12.60 | 1.23 / 4.64 | 1.23 / 4.64 |
| gapped | 17 creators, one burst of 2 asks 3 units apart, s = 0.3 (window 1, the rule of 11:08) | 18 | 1.93 / 7.74 | 1.93 / 7.74 | 1.93 / 7.74 | 1.93 / 7.74 | 1.93 / 7.74 |
| gapped | 17 creators, one burst of 4 asks 1, 2 and 3 units apart, s = 0.35 (window 1, the rule of 11:08) | 18 | 3.31 / 10.28 | 3.27 / 10.28 | 10.28 / 23.48 | 3.27 / 10.28 | 3.27 / 10.28 |
| gapped | 12 creators, one burst of 3 asks 2 units apart, s = 0.3 (window 1, the rule of 11:08) | 13 | 8.50 / 9.39 | 8.50 / 8.50 | 8.50 / 9.39 | 1.38 / 8.50 | 1.38 / 8.50 |
| gapped | 9 creators at s = 0.3 and 8 at s = 0.5, one burst of 3 asks 2 units apart (window 1, the rule of 11:08) | 90 | 4.76 / 13.09 | 4.76 / 13.09 | 4.76 / 13.09 | 1.13 / 4.76 | 1.13 / 4.76 |
| gapped_beyond_window | 17 creators, one burst of 3 asks 6 units apart, s = 0.3 (window 5: beyond it) | 18 | 7.74 / 20.19 | 7.74 / 20.19 | 7.74 / 20.19 | 1.93 / 7.74 | 1.93 / 7.74 |
| gapped_beyond_window | 17 creators, one burst of 3 asks 2 and 7 units apart, s = 0.3 (window 5: beyond it) | 18 | 1.93 / 7.74 | 1.93 / 7.74 | 7.74 / 20.19 | 1.93 / 7.74 | 1.93 / 7.74 |
| gapped_beyond_window | 17 creators, one burst of 3 asks 6 units apart, s = 0.3 (window 10, the sensitivity row) | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |
| gapped_beyond_window | 17 creators, one burst of 3 asks 2 and 7 units apart, s = 0.3 (window 10, the sensitivity row) | 18 | 0.23 / 1.93 | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |
