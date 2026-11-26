# r3-P04 / r4-P09: position-matched contrasts, the registered negative controls, one null engine

Third-round panel programme, step 1 (class a.1). Written 2026-11-26 (UTC times from `date -u` in status.json) by a model
agent working for the project lead (not a person). r4-P09 (the span-structure transplant reference, novelty N08, an
application of in-space placebo designs; the method is not new) is carried by this entry.

**Status.** Exploratory; not a test of H1-H10. Seen creators only. Every label is model-coded and not checked by a person;
agreement between models is agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What it asks

How much of each seen claimed-minus-own contrast (H1 rate, H4 contraction share, H6 placement of pay-or-enrol asks) is
produced by where the voices sit in a recording and how long their spans are, with no difference of voice at all; and
does any contrast remain beyond that. "Claimed voice" here is the first-person claimed voice and the reported claimed
voice together (V2 + V3; H4 uses the first-person claimed voice alone), as the creators present it.

## Prespecification and bases

**Prespecification timing** (added for publication, 2026-11-26; the lead's step-1 decision 43). `code/prespec.json`, which covers r3-P04, r3-P05 and r3-P06, is published as `prespec.md` (a redacted copy, one private path replaced; its bytes are otherwise JSON). The recorded fixing time (02:31:06Z) precedes the file's last write (02:32:03Z) by under a minute; the hash was taken after the last write (02:32:08Z) and before the first outcome (r3-P06's frame flags from 02:37:31Z; the analysis from 02:52:38Z).

- `code/prespec.json` (sha256 the hash recorded at hashing time is kept privately), written at
  2026-11-26T02:31:06Z before any outcome of this entry, of r3-P05 or of r3-P06 was computed; only outcome-free counts
  (formats, label-based eligibility, own-voice-only recordings, length-band cut points) were looked at first
  (`code/probe_counts.py`). Deposit 2 was merged before this entry started. Known leak (split policy): the writer had seen
  the exploratory round's published aggregates (LAB-A, MR-18d, nlp-R7 among them); these contrasts run on all seen
  creators and are not split.
- Labels through the frozen seen-only path (MR's `mrcommon.py`, reused); statistics by the frozen per-recording functions
  of `h1_rate`, `h4_contraction` and `h6_asks`; side lists replaced in memory only. 1,284 seen recordings of the
  English-only recognizer, 71 creators. Small model (the seen label of record) primary; middle model on the recordings it
  labelled in full as rows.
- Rows of one statistic rest on one creator set (creators with an observed value, a value under the cross-creator
  transplant and one under the registered permutation); the same-creator rows on its creators who also have
  own-voice-only recordings.

## References

- **XT, cross-creator transplant matched on format and length band** (the printed estimate's reference): every recording
  receives, 200 times, the span map of a recording of another creator with the same map format and recording-length
  tertile that enters the same statistic, laid on by word position; only units on the claimed or own side receive a side.
- **ST, same-creator transplant onto own-voice-only recordings, shifted by up to half a tenth** (den-meth's reference;
  read here as deposit 2's "position-matched reference"): the creator's own span maps on the creator's recordings without
  a claimed voice (talks, not conversations), 200 draws.
- **R0, the registered within-recording run permutation** (MR-18d): a benchmark known not to be centred; never read.
- **Admissibility** (prespecified): a plasmode at a planted zero on own-voice-only recordings (the creator's real maps as
  pseudo-labels; 400 replicates resampling creators); a reference is admissible when its size lies in the 95% Monte Carlo
  band of 0.10 and its null centre within 0.10 x the margin.

## Primaries and readings (small model; deposit 2's margins; 90% intervals by r3-P30's choice)

| Statistic (margin) | Unmatched | XT-centred (printed) | ST-centred | Admissible | Reading |
|---|---|---|---|---|---|
| H1 log rate ratio (0.223) | not printed: the row's count is banded | not printed: the row's count is banded | not printed: the row's count is banded | XT, ST | **undetermined**; some rows' readings are not printed for privacy |
| H1, sensitivity (not the reading): the registry's H1 smallest effect (0.05) | same rows | same rows | same rows | ST (XT's null centre -0.006 exceeds 0.10 x 0.05) | undetermined; some rows' readings are not printed for privacy |
| H4 standardised drop (0.20 SD) | 1.79 (1.41 to 2.16) | 1.46 (1.12 to 1.80) | not printed: the row's count is banded | none | **no reference holds size at this count** |
| H6 OE of pay-or-enrol asks (0.05) | not printed: the row's count is banded | not printed: the row's count is banded | not printed: the row's count is banded | ST | not printed: it rests only on rows whose count is banded |

- **H1.** The unmatched, structure-only, centred and position-matched rows are not printed (the rows' counts are
  banded); the reading is undetermined, and some rows' readings are not printed for privacy. The registered negative
  control (greeting to
  own-voice main part, claimant as registered) rests on fewer than 5 creators (not computed); the same control with
  own-voice-only recordings admitted (a departure row) slows by -0.109 (-0.187 to -0.030), and the claimed contrast minus
  it is -0.016 (-0.139 to 0.108): by the registry writer's rule this is worded as slowing between frame and main part, not
  as a property of the claimed voice. Deposit 2's ratio margin (0.80 to 1.25) is wider than the registry's H1 smallest
  effect. **Sensitivity (not the reading):** the same H1 rows read against
  the registry's H1 smallest effect (hypotheses.md H1: "slower" if the upper bound of the ratio is below 0.95, "no slowing"
  if the interval lies inside 0.95 to 1.05; entered in the frozen constants as 0.05 on the log scale) give
  **undetermined**: at that margin XT fails the centring tolerance (null centre -0.006 against 0.005), and ST's interval
  is not printed (the row's count is banded); some rows' readings are not printed for privacy. The reading stays under deposit 2's margin (the lead's decision of 2026-11-26).
- **H4.** The contrast stays far beyond the margin after the cross-creator transplant (structure-only part 0.32, 0.17 to
  0.47 under XT); the ST rows and the position-matched row are not printed (the rows' counts are banded); the tempo control
  is small (0.10, -0.08 to 0.28). But the plasmode cannot resolve the centring tolerance at this count (centres +0.12 and -0.04 SD with spreads of
  0.27 and 0.36 SD over replicates, against a tolerance of 0.02), so by the prespecified rule no reference holds size: an
  expected, printable reading (K8).
- **H6.** The unmatched, structure-only, centred and position-matched rows are not printed (the rows' counts are
  banded). XT is not admissible (null centre -0.014 against 0.005; spread 0.10), so the reading rests on ST alone; it is
  not printed: it rests only on rows whose count is banded. On the log Mantel-Haenszel scale (a row): -2.75
  unmatched, XT-centred -2.11 (-3.03 to -1.35). H6 registers no negative control. Concentration of asks in islands and
  ask placement under position are r3-P06 and r3-P05.
- The registered run permutation (R0) holds size for H1 but over-rejects for H6 (0.305 at a planted zero), as MR-18d led
  one to expect.
- Middle model (rows): H1 and H4 XT-centred rows not printed (the rows' counts are banded); H6 rows withheld
  (claimed-side asks from fewer than 5 creators); ST not computed (fewer than 5 creators with both kinds of recording).
- Counts first: on the small model 12 or more creators hold claimed and own units in one tenth for every statistic, so
  voice and position can be separated (`public/r3-P04-counts.csv`).

Half-effect disclosure: 56 primaries; if every true effect sat at half its margin, about 2.8 readings A would be expected
at the deposited 5%, up to about 6.1 for the share, standardised, AUC and rank-correlation classes (r3-P30's readings
table). A reading A is never called a finding. Interval rule: r3-P30's `interval-choice.csv` (sha256 fcfe22cf...), which
existed when the readings were made; the row of the largest simulated count at or below the row's creator count; where
no method holds there, a reading is at most undetermined. Its random-effects methods use creators with two or more
recordings (as its battery does); cohort ratios carry a creator-cluster bootstrap (not calibrated by r3-P30).

## Departures

- Planted effects at half and the full margin were not simulated (size at a planted zero only).
- The plasmode runs on own-voice-only recordings (another occasion); its creator count is smaller than the analysis count.
- The H1 negative-control row with own-voice-only recordings' claimant admitted is a departure row beside the registered
  control (which admits sole speakers and hosts only, and so rests on fewer than 5 creators).
- Rows of one statistic were restricted to one creator set after the first run, for privacy (no mean of one quantity over
  nested sets 1 to 4 creators apart); estimates did not change otherwise.
- E5's pause and filler rows were not built: fillers are not stored in the feature files (MR-18c computed them from text);
  H1's pause part is available from the frozen function but not printed here.
- The deposit names the second admissible reference differently in two places ("the position-matched reference" in the
  lead's margins file; "the span-structure transplant" in the margins register; stat's round-4 memo names den-meth's
  same-creator transplant). This entry reads ST as that reference and prints, for the lead, the reading if it were the
  within-tenth matched contrast instead.

## Contacts

None. No hold-out or other-group file was listed, opened or scanned (see `contacts.md`).

## Limitations and the lead's decisions (2026-11-26)

- The reading of H1 stays under deposit 2's margin; the registry's H1 smallest effect is printed as a sensitivity row,
  not the reading.
- The centring tolerance stays as prespecified (0.10 x the margin). Its resolution is a limitation: at the plasmode's
  creator counts (printed in `data-r3-P04-size.csv`) the null centre's spread over replicates (0.27 and 0.36 SD for H4; 0.10 for H6's XT) is far wider than the
  tolerance, so "no reference holds size" for H4 and XT's exclusion for H6 reflect that resolution as much as any bias.
- The second admissible reference is ST, as prespecified; the within-tenth matched contrast stays a described
  alternative (`reading_if_second_reference_were_the_position_matched_contrast`).

## Files (SHA-256)

| File | SHA-256 |
|---|---|
| `public/data-r3-P04-forest.csv` | `4b147a333396c41c5772a257dcead1d9b6abfdedad684f1aea7867802651fb83` |
| `public/data-r3-P04-null-bars.csv` | `36510f18d4a481cfe83fcd8aed49db2d5770ab84af3ea8083a64788734e6b40f` |
| `public/data-r3-P04-size.csv` | `5fde538466795106511a9e77527913c423786477d3ef4867ba11509e3eaf34e4` |
| `public/fig-r3-P04-forest.pdf` | `822ebcb2cccf064e51f9166e61432ff7244c6d9bd0186bae0bebdf1bd7f268e4` |
| `public/fig-r3-P04-forest.png` | `fcd6c904f1b5c339f923ba66ba76126c922840109d639086222eca7f7312a2ab` |
| `public/fig-r3-P04-null-bars.pdf` | `1537ace9224ad0fab5246d0b8caf098b67d02eed504ad138f9f067b69d5efee7` |
| `public/fig-r3-P04-null-bars.png` | `9eaacbb7c654e243dbd066f572086996b1f37bb5d757ec267f1f15758e706c61` |
| `public/fig-r3-P04-size.pdf` | `59f93621a633f75e886f1992e30037d6dba2fec8eef445c94298f4b4314df028` |
| `public/fig-r3-P04-size.png` | `9b54fbb074dda7b78b4073e6e9184618deb950449c732f7a129045d789b7a77f` |
| `public/fig-r3-P04-structure.pdf` | `ca9ef883dbd8ba02ac7bc11f539a5296af6e0d1b2c06e9dd95f7be3bbdfabeef` |
| `public/fig-r3-P04-structure.png` | `7155c703a94cbb534a872a0efcc175efebbd61a24dd48b79c710f07e71f38964` |
| `public/r3-P04-counts.csv` | `8db0fa1478dc8d2baf7609b12cd4ffc8b212d59a8824bb32e19d0dee1160a662` |
| `public/r3-P04-h6-logmh.csv` | `6bc6e141f49aa587c13b0a2a5373f81cc2669bae9b0423971dcee469933bbfe5` |
| `public/r3-P04-readings.csv` | `e0d94f4df41b75426702ad4792c1e1c21cb1af055917ed26206261bf1838bac0` |
| `code/common.py` | `afb6dcf765d44997672e7341911a70990e889cd6407bf50145ebc41dc016874b` |
| `code/intervals.py` | `f428af347014e1b390261794aa58fc6f573b612bb3148aac3db6883d965c599d` |
| `code/p04_publish.py` | `3587577c774c21c1411bdb4e3df1ab64ee43ad00b941cd3e5172e81fccd42744` |
| `code/p04_run.py` | `857a38cebdd587f38cd8c91e9bccdf5c909d82d712ef5b30fd1cfa62024b5435` |
| `code/prespec.json` | the hash recorded at hashing time is kept privately |
| `code/probe_counts.py` | `4692150268ae8985b35efe885830d99b6cd141885cdc356b6d88b4c7cfca1751` |
| `code/pubcommon.py` | `b3a81fe31eee2e48d614ae72db333dbabaebef4a07fe38f52e52bffad0296d02` |
| `code/scan_public.py` | `73bbe208ffa5e6ddadc59fa01173a4ae2b181ad748f325997087c723c1696ec9` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `code/write_status.py` | `b24b1f356fbd180caef9dc8ccd3a591fcf3962d311f047b73717243d2071993f` |
| `code/write_status_p04.py` | `c21d3c6697e6fb4460a2688ca87a57a0212ecbb13ddac4abfd61ef565e1aacc6` |

Code files carry local paths and stay private; their hashes are the record. Per-creator numbers stay in `private/` under anonymous indices.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these recordings and how the creators present it.

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
