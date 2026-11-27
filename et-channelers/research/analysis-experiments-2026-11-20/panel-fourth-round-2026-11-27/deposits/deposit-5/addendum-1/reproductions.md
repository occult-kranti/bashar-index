# Deposit 5, addendum 1: the reproductions of published values (step 0, part B)

Written 2026-11-27 from 13:48:41Z (UTC, from `date -u`) by the step-0 (B) agent, a model agent working for the
project lead (not a person), under the lead's decision 144.2 (B) and registration section 3.3, step 0. Its
prespecification was hashed at 2026-11-27T13:43:27Z, before any reproduction ran. Updated from 16:42Z with the comparison
of R1 to R11 (run by the lead under decisions 148 to 151) and from 16:47Z with decision 154's verdicts.

**Status.** Exploratory; not a test of H1-H10. Nothing here is a reading of any fourth-panel entry. Where labels are
involved, they are model-coded and not checked by a person.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## The rule

Every published value that an entry of deposit 5 reuses was listed from the registration (sections 1.1, 4.2, 4.3, 4.4,
4.6 and 4.12). Each was to be reproduced by rerunning its published code on its published creator set, before any
48-creator file is read, and compared with main to the printed precision. Step 0 may not open deposit 2's private split
record (the half memberships), nor use any file or code that reads it. Before anything ran, each published code chain
was read as text: **a reproduction whose published code, or a stored input it needs, reads the split record or a stored
copy of its half memberships is not run.** No other route was sought, and no value was adjusted.

**The owner's answer and the lead's run (decisions 148 to 151).** The owner then allowed code to read the split record
in memory for these reproductions, with nothing from it published. The step-0 (B) agent wrote a runner and a
comparison without opening the record; the lead reviewed them and ran the runner with the re-decode paused. Its third
start ran clean from 2026-11-27T16:24:18Z to 16:36:51Z: every step exited 0, and no archive file changed during any
unit. The agent then ran the comparison, which reads only main's public files and the reproduced public files.

**Runtime settings (disclosed under decision 150.1; they count as unchanged code).**
- Every script ran with its bytes unchanged, checked against the SHA-256 values in main's status files before the run,
  from a temporary copy of the archive's panel folder outside the archive, with the guarded environment and one worker.
- Two shared modules hold absolute archive paths; their output-folder constants were pointed at the copy, so that no
  archive file could be overwritten.
- One worker replaced a pool of 3 that one extract script fixes in its code, and the step-2 extract ran with
  `--workers 1`.
- Existing private caches were read in place, not rebuilt: the audio pass's stored features and label extract, the
  step-5 extract, the stored labels and the earlier rounds' extracts. Units R2 to R11 read r3-P42's stored extract and
  counts, which the downstream code checks by SHA-256; R1 ran last and rebuilt them.
- An audit hook blocked any write outside the copy and the output folder, and a check after each unit found no archive
  file changed. The runner was corrected twice before its clean start (the folder list of that check, and one code
  folder the copy lacked); no published code changed.
- r3-P17 was not rerun (no fourth-panel entry reuses it).

**Reading words.** "Reproduced": every cell of every public CSV of the entry equal to main as printed (header comment
lines, which carry write times and change notes, are compared apart). "Did not reproduce": otherwise, with the file and
the cell positions; no value is printed. Positions count data rows from 1 after the header row and columns from 0.
"Reproduced: every printed value equal" (decision 154.2): every value that main prints is equal, and the only differing
cells are cells that main later withheld or relabelled under the third panel's privacy decisions 92, 99 and 104 (main is
empty or has text where the rerun has the values those decisions removed).

## Results

Paths are relative to `et-channelers/research/analysis-experiments-2026-11-20/panel-third-round-2026-11-22/` on main
(commit 1461979); each SHA-256 is that of main's bytes.

| Id | Published value(s) reused, and by which entry | Source on main (SHA-256) | Result | Output hash |
|---|---|---|---|---|
| R1 | r3-P42's lexicon-check rows on the 23 (f4-Q02) | `step2/r3-P42/README.md` (`f158269f7449dbaea4ce8b734489799fa22bb0b942f0ce4a20891f862686bbe1`) | observed values reproduced; placebo bands depend on the worker order; the readings in the named rows are sensitive to the placebo draw (decision 154.3). Every observed statistic is equal. The matched-placebo bands differ: `data-r3-P42-classes.csv` 82 band cells (columns `placebo_band_5`, `placebo_band_95`) and 8 reading cells in rows 1, 9 and 85 (columns `c1_reading`, `a1_reading`, `reading`, `c4_reading`); `data-r3-P42-dif.csv` 67 cells (columns `placebo_term_spread_5`, `placebo_term_spread_95`); `data-r3-P42-l01.csv` 10 band cells (rows 1, 5, 17, 19, 20); `data-r3-P42-lists.csv` 3 band cells (rows 25 and 36); `data-r3-P42-influence.csv` 4 text cells (rows 1 to 4, columns `reading_without_term`, `why`); `data-r3-P42-pairs.csv` 2 cells (rows 21 and 120, column `placebo_reading`); `data-r3-P42-collisions.csv` equal. The cause is below | manifest of unit R1's files (kept privately): `3fba99d485f8d122d6ba94f5cb032700e41f48a61b10fce230f3db73760f01ed` |
| R2 | r3-P43 to r3-P46 on the 23: composition test, survival strip, layer pairs, density side, name classes (f4-Q02, U6) | `step2/r3-P43/README.md` (`f55d61713d621f8486d4a88bff223686ce155482fee07052ce178b2750af05a7`); `step2/r3-P44/README.md` (`bc1612cdf0d42ddc7115e58a8a12b6fdeced0916b331266dc58249b3e7224009`); `step2/r3-P45/README.md` (`abdb09dea6b1575e290efdb80e95791ba8442c8dc490100ff05892e9f12e59ae`); `step2/r3-P46/README.md` (`756c6ce1ec3f9f2de147848ed67ff3889241663d3a3fd1e6e37a8850f9675a45`) | reproduced (10 files; only the header write times differ) | manifest of unit R2's files (kept privately): `2165445b87eacfb156f9a61175a4412c560767cea89d6f93081652942b8a8b4c` |
| R3 | r3-P48, r3-P49, r3-P50 on the 23 (f4-Q02) | `step2/r3-P48/README.md` (`bfce2a3cd8b7c586581f16056087147021c9f96156161941a2d4ae32582e8dcd`) | reproduced (6 files) | manifest of unit R3-R4's files (kept privately): `d82f3ff887c389ded2ec3fdd43f92e659fb182f5af9e9594bae74c43b8c2d190` |
| R4 | r3-P51, r3-P52, r3-P53, r3-P55, r3-P56 and r4-P29 on the 23 (f4-Q02) | `step2/r3-P51/README.md` (`2804084b243ef297d175ce73feb859cd24c1c67f4b6ee6c5d85b1cbd7e2a9337`); `step2/r3-P52/README.md` (`5feeb56399fed427c4512acb13327b4d4cf12101791cacb9214f25b269440a66`); `step2/r3-P53/README.md` (`83f25bece7fb6b84230751f65854562730717bd41134af4a9a99f7803b380aa6`); `step2/r3-P55/README.md` (`936094234ba02c74136197a13e822d73ecec4c00ac763aa137b1072dafe1e729`); `step2/r3-P56/README.md` (`0ff05d5ac39ea8a487bf4c56ebaf7953f66ac90f43d0db67191fd95ad01816fe`); `step2/r4-P29/README.md` (`38660bb561e85f341a2891abcd0e108a8b64c015ab642583b4f7fb3b9d9f1f89`) | reproduced (7 files) | manifest of unit R3-R4's files (kept privately): `d82f3ff887c389ded2ec3fdd43f92e659fb182f5af9e9594bae74c43b8c2d190` |
| R5 | r3-P38 on the 23 (f4-Q02) | `step3/r3-P38/README.md` (`bb6c8a7eb86cb8670897e1d8c204dee91d327c1a6af6235b1671a0b54f8ea073`) | reproduced (2 files) | manifest of unit R5-R6's files (kept privately): `ab2d82e68fc93e203ec97568ec166f1dafb4b6b1093270fca25d12d09beb5dac` |
| R6 | r3-P40's timeline, rows and contrasts on the 23 (f4-Q04's reference) | `step3/r3-P40/README.md` (`b2d096ea1e644baf68361155bb7288d9ddc9f4c58c4f37cc3f9e89c62880ae38`); `step3/r3-P40/public/data-r3-P40-timeline.csv` (`645096e9514c1e05efe4bd847ff53169b6b27d9a0b987933e3a661b92c6b640a`) | reproduced: every printed value equal. `data-r3-P40-timeline.csv` (f4-Q04's reference) and `data-r3-P40-contrasts.csv` are equal in every cell; `data-r3-P40-rows.csv` differs only in rows 17 to 19, column `status` (the class-3 rows, 3 text cells), and the three files' header notes differ: main's files were changed after the code ran by the third panel's step-3 decisions 99 and 104 (no value changed) | manifest of unit R5-R6's files (kept privately): `ab2d82e68fc93e203ec97568ec166f1dafb4b6b1093270fca25d12d09beb5dac` |
| R7 | r3-P57's congruence half on the 23 (f4-Q02, P32) | `step4/r3-P57/README.md` (`63e560d840b3cdaee1c08a35d9737b2aa525104c792b21341e15b64643acb0b3`) | reproduced (2 files) | manifest of unit R7's files (kept privately): `da06267dab97bf773cc3509b88f6865934ddb22c4a8d6505116570eb825ff148` |
| R8 | r3-P14's text part, r3-P16, r3-P18 and r4-P14, the X+T rows (f4-Q02) | `step5/r3-P14/README.md` (`3c12f05bee2c38fcbafa52f7c3791c832b8b1f27f5fe438c0bc68cfe852c9b71`); `step5/r3-P16/README.md` (`b46a550140564e1b9170c6a101ae227d2b926a5327ac5ab70c319039fd9f0a90`); `step5/r3-P18/README.md` (`80890e92aab57bfc6dfc86b563f59bb8b794ab62a5f64c9d5ab741aa99d48fe1`); `step5/r4-P14/README.md` (`bc63f11c6fbbed00e3ed7f381e92c9f6b17b78e50ce56e8559374f5d57df7237`) | reproduced: every printed value equal. r3-P14's, r3-P16's and r4-P14's files and r3-P18's uncued file are equal in every cell; `data-r3-P18-adjudication.csv` differs only in rows 1 to 32, columns 4 to 11 (256 cells), and `data-r3-P18-concordance.csv` only in rows 1 to 10, column `hold_length_L` (10 cells): cells that main withheld or merged under the step-5 privacy decisions 92 and 99, after the code ran | manifest of unit R8-R9's files (kept privately): `6770456c0c3fbb4f1f6f0f60a6a3cdf8ee0cd542f08c19966a6b5f82a7eb7711` |
| R9 | r3-P15's ladder on all seen creators (f4-Q03's function-word reference) | `step5/r3-P15/README.md` (`719a14597ac63afa0d56927e76b34d5c729a8614a00b205b1c0b6d2934f39a28`) | reproduced: every printed value equal. `data-r3-P15-contrasts.csv` and `data-r3-P15-reading.csv` are equal in every cell; `data-r3-P15-ladder.csv` differs only in rows 45 to 72, columns `t90_low`, `t90_high`, `interval` (84 cells): the decode rung's intervals, which decision 99 withheld on main after the code ran | manifest of unit R8-R9's files (kept privately): `6770456c0c3fbb4f1f6f0f60a6a3cdf8ee0cd542f08c19966a6b5f82a7eb7711` |
| R10 | r4-P03's census (its rule and flags reused by f4-Q05b and f4-Q12) | `audio/r4-P03/README.md` (`f5312691a833fb992d5db1a4fb4235f1318e3e9325ba04c0aeb6d11e0b5b46fe`) | reproduced (3 files) | manifest of unit R10's files (kept privately): `bc1916ed41e513d035e9d9d2e2242279dbf80b5e7a0f1b996e4a6fa5da53f103` |
| R11 | r3-P09's boundary rows (its rule reused by f4-Q05b) | `audio/r3-P09/README.md` (`50d0a28ef864178b0fdb097ce350724c195924c3749577cd45d70adf54f14f64`) | reproduced (2 files) | manifest of unit R11's files (kept privately): `304edfc05a5103b8be4bd5cb553704864c21124123db0adc639f52d2280c094a` |
| R12 | r3-P30's interval-choice table and battery tables (a pinned input of the registration; the reruns' interval choice) | `step1/r3-P30/public/interval-choice.csv` (`fcfe22cfba84b8b5eedd059ff605afb0055761b88c4c4d96e708d24400a6e1f6`); `step1/r3-P30/public/data-r3-P30-classes.csv` (`314d359d6ddb8006d13ebbceab0b6dd6e5b2b8058e22243edc3a2802215cf283`); `step1/r3-P30/public/data-r3-P30-coverage-grid.csv` (`4a4412acd8befa4ceda22d7da63044bb197c161effe9d4d4e7534f4a3fe99930`); `step1/r3-P30/public/data-r3-P30-readings.csv` (`29c7583af74bda194acecebea37b88ba9fa3449069b33f8bc6874ae1d24b177e`); `step1/r3-P30/public/data-r3-P30-size.csv` (`f6496eab5ba96e1ac5b5af324a954829e77c219a560affd0f6064b7c46d72afc`); code hashes in `step1/r3-P30/status.json` (`6cdfa67f3c26ea139061ecdc1032234cb8998b872e3607d7cad2ea1308a8fbec`) | reproduced: the published code, byte-identical to the hashes on main, was rerun on its published base (CAL's seen-only cache, all 71 seen creators) with one worker, the pools at 13:43:54Z and the battery to 14:01:07Z; the pools and all five tables came out byte-identical to main | the five reproduced tables have exactly the SHA-256 values in the source column |
| R13 | deposit 3's lists and register, and step 2's shared matcher, by hash identity (f4-Q02 and every list entry) | `deposits/deposit-3/hashes.md` (`e12fb42545f77a36031644100af4df95f759c60cbb0f13275e45a7f7efca5c01`); `step2/README.md` (`2d8d6c5c2e3d63d48bbb5a85e433ff0bf1550b40abdc2db4159f62ffc4e74470`) | reproduced: every one of the 88 files that `hashes.md` lists has the listed SHA-256 on main, and the private copy the matcher reads is byte-identical to main; the matcher's SHA-256 equals step 2's index | the comparison table (kept privately): `24c7842078a045092f022d14cf3f5d37d56cb7d24de22c78ea89d4a7bde66f48` |

**R1: the cause (decision 154.3).** The lead ran a structure-only diagnostic of r3-P42's stored and rebuilt private
caches (it prints types, lengths and counts, never a value) at 2026-11-27T16:45:01Z. The vocabulary, and three fields of
the counts that hold vocabulary-indexed or per-recording entries, differ in order only; the recording entries of the
extract and the count tables differ in content, consistent with entries that refer to vocabulary positions. The step-2
extract collects recordings through an unordered worker pool, so the order in which the vocabulary is built depends on
how the workers are scheduled (three workers in the original run, one in this rerun), and the seeded placebo draw
indexes that order. The published bands are therefore one draw among the draws the code can give, and the readings that
rest on them in the rows named above are sensitive to the placebo draw. The observed statistics do not depend on that
order and were reproduced.

**The fourth panel's response (decision 154.3).** Every use of r3-P42's matched-placebo generator in deposit 5 (f4-Q02's
rerun of r3-P42, and every new family drawn under the generator's seed) puts the recordings and the vocabulary in a
canonical order before the seeded draw, and each entry's prespecification also reports the bands' Monte Carlo spread
over a fixed number of reseeded draws. Both are fixed before any count; the method is unchanged. A separate, dated
correction note goes to r3-P42's README on main, in its own pull request after this addendum.

r3-P54 has no published value (its list waits for the owner's act); f4-Q09 (i) reads published values only and reruns
nothing.

## What this leaves open

- **R1.** The observed values are reproduced; the matched-placebo bands, and the readings in the rows named above, are
  sensitive to the placebo draw. The fourth panel's response and the correction note to r3-P42's README are stated above.
- **The reproduced private files hold values that main withholds** (the differing cells of R8 and R9). They stay private
  and are never printed.
- The temporary copy of the panel folder that the runner used was removed by the lead after the comparison; the
  reproduced files stay in the private archive.
- Disclosed: R12's published base and the feasibility tables of this addendum read fields of the 48 (recognizer-output
  counts in CAL's cache for R12; memberships, upload calendars, recording kinds, gates and boundary positions for the
  tables). No list count and no contrast outcome of the 48, or of any creator, was read by the step-0 (B) agent.

## Privacy

No creator, channel, title, id or quotation appears here, and no count of creators other than the published set sizes.
No private path is printed.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
