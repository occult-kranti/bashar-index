# rv-D1: what was selected, archived and transcribed, and where each loss was

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Exploratory, paper review (registry A2/A7); not a test of H1-H10. Public form made at the release review (plan P10) on
2026-11-22 from the item's build of 2026-11-21 01:16 UTC (seen creators and run-level counts of all creators; not re-run).
Place: M (flow, date sentence); S (rank figure, tables); W (flow counts).

**Question.** What was selected, archived and transcribed, and where was each loss?

**Base.** All 101 creators of the roster and the 1,976 recordings of their newest-20 quota. Counts, durations, dates,
languages, editions and run positions come from the run ledger and the inventory (not a contact under plan section 5).
Hold-out and other creators enter only as counts.

**What is shown.**

| File | Content |
|---|---|
| `public/rv-D1-flow.csv` | Census flow by stage: creators, recordings, hours; group rows where safe (see below) |
| `public/rv-D1-dates.csv` | The corrected date sentence as counts |
| `public/rv-D1-rank-shares.csv` | By listing rank: share with a run transcript; audio edition of the run's recordings with 95% bands |
| `public/rv-D1-rank-odds.csv` | Odds ratios of three outcomes, ranks 1-5 against 6-20 (pooled, Mantel-Haenszel, conditional logit) |
| `public/rv-D1-smd-missingness.csv` | Standardised differences of recordings with other text and with no text against transcribed ones |
| `public/rv-D1-seen-subsets.csv` | The seen creators' analysis subsets |
| `public/rv-D1-h3-eligibility.csv` | H3's eligible creators and recordings by group, side by side (never pooled) |
| Gallery group B-D, `rv-D1` | fig-1 census flow (M, W); fig-2 coverage by listing rank (S); fig-3 odds ratios (S) |

**What it shows.** Of 1,976 selected recordings, 1,946 were archived with hash-verified audio (30 final download
failures, 21 creators, mostly provider refusals), 215 were set aside before the run (English text of another kind, from
68 creators, or a language review), 1,731 entered the run and 1,699 were transcribed (32 not transcribed, 15 creators,
most because no speech was found). 1,618 transcribed recordings are in English; 81 are in other languages, all from the
6 hold-out creators with a non-English transcript. Coverage is lowest at the newest ranks: at ranks 1 to 3 fewer than
three in four selected recordings have a run transcript, because recordings with English text of another kind sit there
(Mantel-Haenszel odds ratio 10.4, 95% creator-bootstrap interval 4.97 to 33.9, for other text or a language review at
ranks 1-5 against 6-20). Having no text at all (download failed or not transcribed) shows no clear dependence on rank
(Mantel-Haenszel odds ratio 1.04, 95% creator-bootstrap interval 0.50 to 1.95; the interval allows halving or doubling,
so independence of rank is not shown either); missing recordings are shorter than transcribed ones (SMD -0.76, 90%
interval -1.07 to -0.44).
Rank is listing order, not time: this describes coverage and reads no trend.

**Date sentence (corrected).** Every selected recording has a row in the project's published date table; the 36
identifiers that begin with a hyphen are written there with a leading apostrophe and drop out of a join that does not
strip it (the earlier sentence that 36 recordings have no date row was wrong). The table gives an exact upload day for
1,579 recordings and an interval estimated from the age the platform displayed for 397. For 142 of these intervals a
publication time stamp in the recording's own metadata confirms the day, so 1,721 recordings have a confirmed upload day
and 255 recordings of 67 creators keep an interval (median width 32 days; 9 wider than a year). Dates are upload dates
in UTC, not dates of speaking.

**Withheld, and why.**

- Group rows of the intermediate stages (download failures, set-aside, run, not transcribed): by group some loss cells
  rest on 1 to 4 creators, directly or by difference from a neighbouring stage. Group rows are printed for selection and
  for the transcripts only. The verifier found four such cells recoverable by subtraction in the built flow table; this
  form removes them.
- Counts by failure reason and by not-transcribed reason: some reasons rest on fewer than 5 creators.
- The other group's creator count is printed as "fewer than 10" (as in the paper), and its transcript count is not
  printed (shown by hours only, as in the paper); no release file of this group prints the run's total of transcribed
  audio files, from which it would follow by subtraction (rv-D6's event 15 is worded in recordings). Creator counts 1
  to 4 short of 101 read "all but fewer than 5 of 101".
- Counts and creators per listing rank (beside the roster they would give nested counts 1 to 4 apart); shares are
  rounded to 2 decimals. Every rank cell, with and without a transcript and by edition, holds 5 or more creators.
- Event counts and group sizes of the odds ratios, and the creator count behind the "no text of any kind" outcome:
  beside the census counts of download-failure and not-transcribed creators it gives their overlap, a cell of fewer than
  5 creators, by difference (the paper's rank-odds table no longer prints it: it reads 'n.p.' there, lead's decision D49).
- Recording and creator counts of the SMD groups (creator counts 1 apart from the roster and the transcribed count).
- H3 exclusions by reason (some rest on fewer than 5 creators), and the hyphen-identifier counts by group.
- The other-text table by text kind and rank band: its cells were not recounted by creator and several kinds hold fewer
  than 5 creators; the rank position of other-text recordings is shown by the rank figure and the SMD of listing rank.

**Interval levels.** Census counts carry no interval. Edition shares by rank: 95% creator-bootstrap bands (2,000 draws).
Odds ratios: 95% creator bootstrap (pooled, Mantel-Haenszel), 95% Wald (conditional logit). SMDs: 90% creator bootstrap.

**Caveats.** Recordings never listed (live streams, short videos, members-only material, other platforms, deleted
uploads) are outside the quota and are not counted. The hold-out is the tail of an English-first run (rv-D2).

**Fix pass (2026-11-22, after the release verifier).** The rank-odds wording now reads "shows no clear dependence on
rank" (an interval from halving to doubling does not show independence); the figures' data files and captions cite release
file names only. No table value changed.

**Writers.** Tables: `build_tables_D.py` (SHA-256
`d38dc81e39a5d9606ca78aae9138138e1a429de11a2082f3e3de533467d1bb92`); figures: `plot_D.py` (SHA-256
`ab68d497db1726d7fd12edfbec30e72b71efe5b208be0886822e8c014fa44caf`).
