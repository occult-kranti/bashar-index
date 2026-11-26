> Redacted copy: 1 private path replaced; the hash recorded at hashing time is kept privately.

{
 "entry": "r3-P30 (carries the residual of the withdrawn r4-P10)",
 "written_utc": "2026-11-26T02:24:29Z (from date -u, before any pool was built or any simulation run)",
 "written_by": "a step-1 agent (a model agent working for the project lead; not a person)",
 "status": "Exploratory; not a test of H1-H10. Calibration on label-free analogues built from the seen creators' recognizer output (CAL's private numeric cache, seen creators only); no label is read; no model call.",
 "agnosticism": "No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these recordings and how the creators present it.",
 "why_these_choices": "The deposited method card (deposit 2, calibration-method-card.md) leaves open the design classes, the methods beyond those named, the grid of creator counts, the placebo scheme, the number of draws, the size and power targets and the selection rule. They are fixed here, by the agent, before any output of this battery exists. No contrast of any entry is read here: the battery uses label-free analogues only, so nothing is tuned on any entry's outcome.",
 "data": "CAL's private cache (a file in round 2's private CAL folder, SHA-256 9383c3fd37849983767213b9c2273e262260050c51aabcf0fec2785f81e2c2ba): per seen recording, per sentence unit, counts only. Recordings: English, English-only recognizer, not publisher audio (CAL's eligible_recordings).",
 "design_classes": {
  "A_log_ratio": "Log ratio of a rate between two parts of a recording (CAL's H1a analogue: words per minute in the middle block, 20-80% of words, against the edges; both sides 300 words or more); creator mean of recording values. Margin 0.223 (deposited: ratio of rates).",
  "B_share_difference": "Difference in shares between two parts of a recording: share of units carrying a hedge or condition marker, middle block minus edges (both sides 300 words or more); creator mean of recording values. Margin 0.05 (deposited: difference in shares).",
  "B1_share_one_recording": "As B_share_difference, but each simulated creator contributes one recording drawn at random (the design of BR-GS's and rv-R3's one-recording-per-creator bases). Margin 0.05.",
  "C_standardised": "Standardised difference (CAL's H4a analogue: contraction share middle minus edges, both sides 10 or more contractible forms, divided by the between-creator SD of the edge share); creator mean. Margin 0.20 (deposited: standardised difference).",
  "D_superiority": "Probability of superiority within a recording: the chance that a middle-block unit's word rate exceeds an edge unit's (units of 3 or more words and positive duration; both sides 20 units or more); creator mean of recording values. Margin 0.10 from 0.50 (deposited: AUC). Shift model without clipping.",
  "E_rank_correlation": "Within-creator Somers' D (CAL's H2a analogue: a 0-4 checkability proxy against an unhedged marker over future-marked units, pooled within three length bands; creators with 30 or more such units); one value per creator. Margin 0.10 (deposited: correlation or agreement coefficient).",
  "F_slope": "Pooled within-creator OLS slopes with their own variance (the TL-7.1 design class): per creator, 3 to 8 recordings drawn once with a fixed seed, slope of the recording's log words per minute on its log duration, variance s2/Sxx floored at 1e-4 as TL-7.1 floors it; one slope per creator. Margin: 0.20 between-creator SD of the slopes (no slope margin is deposited; the standardised-difference margin is used and flagged).",
  "G_few_recordings": "Discrete per-creator differences with 2 to 5 recordings per class: per creator, recordings split at the creator's median duration, 2 to 5 drawn once (fixed seed) from each half; value = mean log words per minute of the longer minus the shorter. One value per creator. Margin 0.223.",
  "H_rare_counts": "Rare counts: per creator, log rate ratio of ask-word hits (CAL's crude list) per word in the middle block against the edges, counts summed over the creator's recordings, 0.5 added to each count; creators with 5 or more hits in all. One value per creator. Margin 0.223."
 },
 "methods": {
  "t_cm": "t interval on creator means (the deposit's default until this battery has run)",
  "boot_pct": "creator bootstrap percentile (999 resamples)",
  "boot_t": "creator bootstrap-t (999 resamples)",
  "hl": "Hodges-Lehmann estimate with the exact signed-rank interval (Walsh averages); coverage is that of the nearest attainable level at or above 90%",
  "two_stage": "two-stage bootstrap percentile: creators, then recordings within each drawn creator (999 resamples); classes with recordings nested in creators (A, B, C, D)",
  "rec_t": "t interval on recording values, ignoring creators (a demonstration of the failure CAL found; never selectable)",
  "re_dl": "DerSimonian-Laird random-effects mean with a normal interval (creators with 2 or more recordings, or an own variance)",
  "re_hksj": "Hartung-Knapp-Sidik-Jonkman with t(k-1)",
  "re_hksj_floor": "HKSJ with its SE floored at the DL SE",
  "dl_boot": "DerSimonian-Laird point with a creator-bootstrap percentile interval (the method used for TL-7.1; class F only; 999 resamples)"
 },
 "counts_grid": [5, 8, 12, 18, 23, 30, 40, 50, 71],
 "counts_note": "Simulated numbers of creators: design constants, drawn with replacement from the class's seen pool (the pool is the population); not counts of creators of any group. An entry with c creators reads the row of the largest grid value at or below c.",
 "draws": "2,000 simulated data sets per class, count and method (Monte Carlo SE of a coverage near 0.90: 0.0067); 999 resamples per bootstrap interval; base seed 2026112630, one stream per class and count (crc32 of the class and count).",
 "truth": "The pool's creator-balanced mean of the class value (for re_dl, re_hksj, re_hksj_floor: of the creators that enter them).",
 "placebo": "Creator-level resampling of real seen creators (heterogeneity kept); coverage is read at the pool truth. One-sided misses (interval wholly above the truth; wholly below) are the size of the floor rule's one-sided 5% test. For the readings table the pool is centred at 0 and shifted by delta (shift model); every method used is translation-equivariant, so the shifted intervals are the centred ones moved by delta.",
 "level": "90% (two-sided), as the floor rule reads it.",
 "holds_rule": "A method holds coverage at a class and count if its coverage lies within 0.02 of 0.90 and each one-sided miss rate is 0.07 or less.",
 "selection_rule": "If t_cm holds, t_cm is chosen. Otherwise, among the methods that hold (rec_t excluded), the one with the smallest absolute coverage error is chosen (ties: the narrower mean width). If none holds, the method with the smallest absolute coverage error is named and flagged 'no method holds'; a reading at such a class and count is at most 'undetermined' (deposit 2: 'a reference that does not hold its size at the count').",
 "size_panel": "Per class, count and method: lower-tail and upper-tail miss rates of the 90% interval (nominal 0.05 each); and the creator-level sign-flip test of the truth (999 random sign draws), two-sided at 0.10.",
 "readings_table": "The register's fixed procedures (r4-P10's residual), for the chosen method at each class and count: with the true effect at 0, 0.5, 1, 1.5 and 2 times the margin, the share of data sets whose near 90% bound lies beyond half the margin (the floor rule), whose interval lies wholly beyond the margin in the named direction (reading A), and whose interval lies wholly inside plus or minus the margin (reading B).",
 "not_run": "circular, local-block and unit-shuffle references for autocorrelated series; blocked against unblocked curveball; rewired-dyad permutation; Freedman-Lane (named in round 3's pooled method, not in the adopted programme text); the registered tests of H2, H3 and H6 (CAL already reports them; not re-run); pooled-ratio estimands (E1's pooled row; a different estimand from the creator-equal one)."
}
