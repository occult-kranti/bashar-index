# r3-P27: tuning leak, development against check creators

Third-round programme, step 1 (class a.1). Written 2026-11-26 (UTC times from `date -u` in `status.json`) by a step-1
agent (a model agent working for the lead; not a person). Exploratory; not a test of H1-H10. Seen creators only; no model
call, no download. Every label is model-coded and not checked by a person; agreement, never accuracy. A difference
between the groups is a shrinkage factor for seen priors, not proof of tuning.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Which groups

Established before any value (prespecification): the paper defines development and check creators as subsets of the seen
creators (prompts developed on the first; gate and verification samples drawn from the second); the split policy says
r3-P27 uses that partition as it is; the split file records development 48 and non-development 23, disjoint, together
the 71 seen creators. **Both groups are seen creators, so the entry ran.** No hold-out or other-group file was needed or
opened.

## Prespecification and rows

- `prespec.md` (SHA-256 `40dc7e2f34109b299b5c87081673ed7939b61fc63fc32dac213825360739f0b1`), hashed at
  2026-11-26T06:39:57Z (`prespec-record.md`), before any value of this entry was computed.
- **G1** the small and middle models' agreement on claimed voice (V2 or V3, rule B) or not, share of sentence units,
  creator means over the recordings the middle model labelled in full (48 development, 23 check creators); margin 5
  points; named direction: development higher. **C1 to C3** the seen claimed-minus-own statistics (small model of record,
  frozen functions, unmatched): H1 log rate ratio (margin log 0.223), H4 standardised contraction drop (0.20 SD), H6 OE of
  pay-or-enrol asks (0.05); two-sided.
- Group intervals: r3-P30's choice for the class at the group's count. Difference: Welch's t interval on creator means
  (two-group differences are not a class r3-P30 simulated; deposit 2's t-interval fallback, stated) with a stratified
  creator bootstrap beside; disagreement, or a group count at which r3-P30 finds no method that holds, gives
  "undetermined".

## Readings (of the difference, development minus check)

| Row | Development | Check | Difference (Welch 90%; bootstrap 90%) | Reading | Shrinkage, check / development |
|---|---|---|---|---|---|
| G1 voice agreement | 0.940 (0.892 to 0.968), 48 | 0.982 (0.957 to 0.995), 23 | -0.065 (-0.110 to -0.021; -0.108 to -0.024) | **undetermined** (crosses the margin; points opposite to the named direction) | not a contrast |
| C1 H1 | not printed (decision 50(a)); 30 to 39 creators | not printed (decision 50(a)); 5 to 14 creators | -0.156 (-0.279 to -0.033; -0.272 to -0.050) | **undetermined** (crosses the margin) | not printed (decision 50(a)) |
| C2 H4 | not printed (decision 50(a)); 20 to 29 creators | not printed (decision 50(a)); 5 to 14 creators | -0.53 (-1.41 to 0.35; -1.32 to 0.26) | **undetermined** | not printed (decision 50(a)) |
| C3 H6 | not printed (decision 50(a)); 20 to 29 creators | not printed (decision 50(a)); 5 to 14 creators | -0.111 (-0.311 to 0.089; -0.283 to 0.062) | **undetermined** (crosses the margin) | not printed (decision 50(a)) |

- **No row reads A or B.** On the agreement figure the check creators, not the development creators, show the higher
  share (the difference points against what tuning would predict, partly beyond the margin); the pooled kappas are alike
  (development 0.826, 0.760 to 0.878; check 0.821, 0.719 to 0.885), and claimed voice is less common in the check
  creators' middle-labelled recordings, so the share difference may mostly reflect how much claimed voice each group's
  recordings hold (units both models call "not claimed" agree trivially); not resolved here. Disagreements come from 5 or
  more creators in each group.
- **Shrinkage.** Not printed on C1 to C3 (the lead's step-1 decision 50(a), 2026-11-26T09:32:46Z): values are withheld where they could narrow a banded count (wording of the lead's step-1 decision 53(b)); the difference, its interval and its reading stay. No number changed.
- C1's group estimates are r3-P30's random-effects estimates (r3-P30's choice at each group's count), and no plain
  creator mean of either group is printed (r3-P04 printed one over a set this entry cannot reconstruct); the difference of
  the two random-effects estimates is not printed (values that could narrow a banded count are not printed).
- Not computable on both groups: the gate sample G, the cross-vendor read (VER-3R) and the second readings (DBL) were
  drawn from check creators only; the pilot's set W was development recordings under pre-freeze prompts.

Multiplicity: the register holds 56 primaries; if every true effect sat at half its margin, about 2.8 readings A would be
expected by chance at the deposited 5% (up to about 6.1 for the share, standardised, AUC and rank-correlation classes,
r3-P30). A reading A is never called a finding.

## Files

| File | SHA-256 |
|---|---|
| `public/fig-r3-P27-paired-forest.pdf` | `fc2f752d757297ddccad877b643d0940b3f0c134e45024202bf1abcb941a1272` |
| `public/fig-r3-P27-paired-forest.png` | `58cbec12b3ff5eeee3ae866dd8770f3480452f23f4d87f6b66379fc9b9039214` |
| `public/r3-P27-paired-forest.csv` | `a60beb922f5baf835f0be1442f75e54073ef235d321681d463ade1399afe6361` |
| `code/finalize.py` | `f3711f285ef2310f56383d4aa121c8cd25157913ab3d85edde2ce1ef91e3d7fe` |
| `code/p27_publish.py` | `5ac5eaf1c73a6053d0886ddcb717eadbc35d042823b4d85040af2df6594467c3` |
| `code/p27_run.py` | `55443d6303f0a3f4c46548c736b6da00984050603170e84dd4c5c57858a08cf5` |
| `code/pubrules.py` | `241499756e6c5f3145e1cb077412e5be91281470f82b34a4cb965615b814255c` |
| `code/scan_ids.py` | `8e13207c018538e592903f635f90c4bdce058848f8d9292bef3a2945fcaae14c` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `code/scans/qscan_all2.py` | `2110295383173e4ab29d06a2c5cb677c74942c105ac6338bdd5e5f0c9532dcae` |
| `code/scans/quant.py` | `a2478a09a37c3c759485fdfa3e0f98c6cd1d9a3094cc3b58c566588a9b1cae5c` |
| `code/scans/quant2.py` | `7421b55e42d6fd55880a4b44dbc42c89c5991f18ba652374a2a4e93865ce9248` |
| `code/scans/zsolve.py` | `45a7b23d4a38522855b982aecb85989280e48c6e82ad2a0069dbea590a1ddc0b` |
| `prespec.md` | `40dc7e2f34109b299b5c87081673ed7939b61fc63fc32dac213825360739f0b1` |
| `prespec-record.md` | `4f0992c716418c0db882c2979c12cedf526f4b634663744d32626a87d809401c` |
| `contacts.md` | `18c3730db9d32bb2d7f659c9165413f003362add6a77ebef9ac832d75b49277d` |

Private (not published): `private/` (per-creator and per-recording values, sums, run logs). Public data CSVs carry a commented header; PNGs at 200 dpi without text chunks; PDFs without document information.

**Privacy scans** (copies in `code/scans/`, `REL` set to this entry's `public/`): zsolve.py: 0 rows tested, 0 pinned, 0 narrowed; qscan_all2.py: 0 files with quantile columns, 0 rows with a hidden or banded base; identifier scan (creator codes, audio hashes, video ids): 0 hits; PNG text chunks and PDF document information: none. quant.py and quant2.py copied; they read the 'quantiles' column of one release file, and no public file of this entry has such a column, so they were not run on it.

## Departures and choices (stated)

1. The difference's interval is Welch's t (not simulated by r3-P30), with the bootstrap as the agreement check.
2. G1's group estimates use r3-P30's chosen method (Hodges-Lehmann at both counts), so the points are pseudo-medians of
   creator values, not means; the Welch difference uses creator means.
3. (Not printed since decision 50(a).) C1's shrinkage interval used 400 stratified draws of the random-effects estimates (2,000 for C2 and C3).
4. Counts near another printed group are banded ("30 to 39", "20 to 29", "5 to 9").

## Fields not stored

Agreement figures on development creators under the frozen prompts other than G1 (gate, cross-vendor and second readings
were drawn from check creators only).

## For the lead

- H1's shrinkage factor is not printed (decision 50(a)); the difference reads undetermined; it is not proof of tuning.
- The G1 difference points against the tuning direction; the lead may wish to note it beside VER-3R and GATES, which
  rest on check creators only.

## Contacts

None (`contacts.md`).

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.

## Correction by the lead's decision 134 (2026-11-27T09:41:55Z, UTC from `date -u`)

The gate sample G: an earlier sentence said the gate sample was drawn from the check creators; it holds a seeded draw from the seen creators and every check creator, so its agreement figures describe development and check creators alike; no number or reading changes. The sentences above that name G among the samples "drawn from check creators only"
should be read with this note; the cross-vendor read and the second readings are not affected by it.
