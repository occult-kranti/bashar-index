# r3-P01 / r4-P01: recognizer instability by self-presented voice (step 1, class a.1)

Written 2026-11-26T02:58:31Z and updated 2026-11-26T03:04:35Z with the sensitivity rows (UTC, from `date -u`) by a step-1 agent (a model agent working for the lead; not a person).
Exploratory; not a test of H1-H10. Seen creators only. Voice labels are model-coded; not checked by a person. No model call, no network call, no download, no GPU job.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## The tolerance arm came first and alone (hashed before the voice split)

The tolerance arm (`code/tolerance_arm.py`) ran 02:28:30Z to 02:29:11Z and opened no voice label. Its record,
`tolerance-arm-record.md`, was written at **2026-11-26T02:29:19Z** (from `date -u`) with these hashes, before the voice
split first ran (02:32:24Z):

| File | SHA-256 |
|---|---|
| `private/tolerance-margins.json` | `bd5a940aedc824b60d64346daf454d0ed9ccb0d494ba2dc160e4a5044994b455` |
| `public/data-r3-P01-margins.csv` | `5720e794bda5cfc7ea94044aed6154f84024bdcb3cfade6fbba762dab8593f3c` |
| `code/tolerance_arm.py` | `b56f55aaeb2bd6714fcd94e9c9260de58d120661a078f10be9fde67662172f27` |
| `code/p01common.py` (classes, zones, thresholds, reading rule) | `6f545af4a4b442b2506fbf277d77638aef12dc8347605418b2046144adcce800` |
| `tolerance-arm-record.md` (hashed 02:29:48Z) | `9fbce94b8f45ba5039ca5cc501ac8d9a932addefdf03880cc267c33d2e20a991` |

`voice_split.py` refuses to run unless the margins file still has its recorded hash; the four files above are unchanged.

**Margins (consequence-based; binding: targeted-error model).** Each margin is the smallest claimed-minus-own difference
in the share of a class's unstable tokens that, if every unstable token in the noisier voice were an error falling on
the class, would move the by-voice contrast reading that class by deposit 2's default margin: contractible pairs 0.0295
(all; 0.20 x H4's yardstick), class A 0.0382, class B 0.0448, class C 0.0278; archaic forms 0.20; first-person plurals
0.0857; names 0.0967; function words 0.0095; filled pauses 0.20; all words and filter removals 0.0222. A calibrated
version (margin / q, with q measured voice-free on the stored second decodes: q_A = 0.349 for low confidence, q_S =
0.065 for the seam zone) is printed beside and never binds.

## Primaries and readings (small model of record; within the stated bases only)

Reading words: "no differential instability detected among Whisper-family decodes; shared normalisation untested"
(reading B), "differential instability detected" (reading A) or "undetermined". r3-P01 names no direction, so a row
beyond the margin on either side would read A; none does.

| Base | Family | Family reading |
|---|---|---|
| Stored fields: 59 creators, 443 recordings (MR-18c's all-units base) | A confidence (probability below 0.5) | **no differential instability detected among Whisper-family decodes; shared normalisation untested** (every computed class row whose reading is printed lies inside its margin; some rows' readings are not printed for privacy) |
| same | B1 filter removals per kept word | **no differential instability detected ...; shared normalisation untested** |
| same | B2 seam share (within 1 s of a 30-s seam) | **undetermined** (some rows' readings are not printed for privacy; claimed-voice words sit slightly more often in seam zones, e.g. all words +0.0068, 90% 0.0038 to 0.0099, against a margin of 0.0222) |
| same | D transport (contrast on stable tokens minus on all tokens) | **no differential instability detected ...; shared normalisation untested** (some rows' readings are not printed for privacy) |
| C1: rv-R3's seen bridge recordings holding both voices (10 to 19, one per creator) | C1 non-agreement (larger model against record) | **undetermined** (some rows' readings are not printed for privacy) |
| same | D transport on C1 | **undetermined** (some rows' readings are not printed for privacy) |
| C2: BR-GS's seen grid-shift recordings holding both voices (13, one per creator) | C2 non-agreement (shifted against run grid) | **undetermined** (some rows' readings are not printed for privacy) |
| same | D transport on C2 | **undetermined** (some rows' readings are not printed for privacy) |

C1 and C2 are never pooled. Archaic forms: not computed on any base (fewer than 5 creators with 10 archaic tokens on
each side). Contractible class B: not computed on C1 and C2. Filled pauses: computed on the stored fields only (5 to 9
creators). Middle-model rows (on the seen recordings it labelled in full, 30 to 39 creators) are listed; values that
could narrow a banded count are not printed; the middle model has too
few recordings with both voices in either second-decode base (fewer than 5).

**Seam-zone exclusion rows** (r3-P02's pre-specified rule: leave out the zone within 1 s of a run-grid seam; small model;
printed beside the unexcluded rows, never replacing them): A excluded, B1 excluded: every computed row whose reading is
printed inside its margin; C1 excluded and C2 excluded: undetermined; some rows' readings are not printed for privacy
(data-r3-P01-readings.csv).

**Headline panel (same spans, same units; H1's span rule, small model, seen creators).** This entry
reproduces each headline's point estimate on these spans. The recognizer gaps against the published headlines (MR-18c's
unit rate, beside the headline -0.0709; E5's fillers per 1,000 words, beside -0.134; E5's pauses of 1 s or more per 100
words next to a low-confidence word or spanning a seam, beside 0.446) are not printed: the rows' counts are banded. r3-P02
(described, not read): the coupling of pauses with sentence marks is weaker in the claimed voice, which bears on the
pause contrast. E2's profile statistic has no counterpart on its own scale (departure below).

**Overall, in the only words allowed:** on the stored fields, families A, B1 and D read "no differential instability
detected among Whisper-family decodes; shared normalisation untested"; the seam share (B2) and both second-decode bases
(C1, C2) are undetermined. No row whose reading is printed reads "differential instability detected"; some rows' readings
are not printed for privacy (the lead's step-1 decision 56). "Erasure" is out of reach (part E, a
recognizer of another family or a person's reference would be needed), and no reading is restricted to boundaries that
pass the splice census (r4-P03 has not run).

Multiplicity: 56 primaries in the programme; if every true effect sat at half its margin, the readings of A expected by
chance are about 2.8 at the deposited 5%, up to about 6.1 for the share, standardised, AUC and rank-correlation classes
(r3-P30's readings table). A reading is never a finding.

## Intervals

90%, by the method r3-P30's `public/interval-choice.csv` (SHA-256 `fcfe22cfba84b8b5eedd059ff605afb0055761b88c4c4d96e708d24400a6e1f6`)
selects for each row's design class at its creator count (largest simulated count at or below it): stored-field A, B1,
B2 and share-class D rows as B_share_difference; rate-class D rows as H_rare_counts; C rows as B1_share_one_recording;
the MR-18c gap as A_log_ratio; the E5 gaps as B_share_difference. The file appeared at 02:35:12Z, after the first voice
split had run with t intervals on creator means; it was applied before publication. Where r3-P30 finds that no method
holds, a reading is at most undetermined. The random-effects methods use, as r3-P30's battery does, the plain mean of a
creator's recording values and its variance over k recordings, for creators with 2 or more recordings (so those rows
rest on 51 of the 59 creators); because some creators have identical recording values (variance 0, which would give
them unbounded weight), each creator's variance is floored at the binomial sampling variance of its recording values
(Jeffreys-adjusted shares): a choice made here, stated.

**Sensitivity rows (lead's decision of 2026-11-26; added 2026-11-26T03:04:35Z).** Beside every row read with a random-effects (HKSJ)
interval, the data file now carries a row labelled "sensitivity (not the reading)": the t interval on creator means over
all of the row's creators (for example 59 rather than 51). They never change a reading. In
`data-r3-P01-readings.csv` each family that holds such rows has a sensitivity summary beside its reading: A, B1, D and
the seam-zone-excluded A and B1 read the same under the sensitivity rows ("no differential instability detected ...");
B2 stays undetermined (under the t interval its function-word row also crosses its margin: +0.0059, 90% 0.0019 to
0.0100, margin 0.0095). The MR-18c gap's sensitivity interval is 0.0003 (-0.0067 to 0.0073), in
`data-r3-P01-headlines.csv` (the gap's own interval is not printed: the row's count is banded). The figure captions say where these rows are; they are not drawn.

## Files

| File | What | SHA-256 |
|---|---|---|
| `public/data-r3-P01-margins.csv` | the tolerance arm's margins (hashed before the voice split) | `5720e794bda5cfc7ea94044aed6154f84024bdcb3cfade6fbba762dab8593f3c` |
| `public/data-r3-P01-instability.csv` | every row: base, model, family, class, estimate, 90% interval, margin, reading, calibrated reading, r3-P30 class and method; seam-zone exclusion rows and sensitivity rows beside | `b83dbfef5683513d136aa54a478037ba5931a08a4c5d3b553bc9f917910e236c` |
| `public/data-r3-P01-readings.csv` | family readings per base and model, with the sensitivity summaries (not the reading) | `909c14d5026b5d1e59de8ac5a24380879f8082ea142534003a309d5e705b9524` |
| `public/data-r3-P01-headlines.csv` | the headline panel's data, with the sensitivity interval of the MR-18c gap | `3d965397618b326f1ecfd0613fdad6f82390327695fa80bdc594674572790df8` |
| `public/fig-r3-P01-instability.png` | rows per word class and family (A, B, C1, C2) in margin units, margin shaded | `b67aa42577db238ea78fc398ea99c72948f286d7c43a52f31e64b7f624b12ba8` |
| `public/fig-r3-P01-instability.pdf` | the same, PDF | `5e3a14111923305434088d6c9b21e1a1052e6c7826e7d0b45bd68600093877b8` |
| `public/fig-r3-P01-transport.png` | family D on the three bases | `dee70dce1a01c966efee483e5de408ed4b6875ae203da73861e614526cc57511` |
| `public/fig-r3-P01-transport.pdf` | the same, PDF | `76be8d0bc4da0f7da037ec7d1b2ed66bfd9162cf0cd5efd799a3144c96f46509` |
| `public/fig-r3-P01-headlines.png` | each by-voice headline beside the recognizer gap | `f85ba34f7bf3b8924c26373644c76acc9e7b028e96520cf1774b9c62dbc51fca` |
| `public/fig-r3-P01-headlines.pdf` | the same, PDF | `fb84982577bbf4e694ccb0895daa7ff15ed4b640bce8d62a6bdf570cb9932b6d` |
| `code/probe_inputs.py` | structure probe (counts only) | `9d5b09432520543527d67a8b9ac4250159aa3436f0de8f42f04eb0e329c13d7d` |
| `code/p01common.py` | fixed specification and loaders (hashed with the tolerance arm) | `6f545af4a4b442b2506fbf277d77638aef12dc8347605418b2046144adcce800` |
| `code/test_p01common.py` | unit checks on constructed tokens | `3c0b4aaca7a645bc39fe74a394b5a50ce46e05ee1e06f3668eec24e160b9f724` |
| `code/tolerance_arm.py` | the tolerance arm (no voice label opened) | `b56f55aaeb2bd6714fcd94e9c9260de58d120661a078f10be9fde67662172f27` |
| `code/voice_split.py` | families A, B, C1, C2, D, exclusion rows, headline gaps | `11aed4ddb0484d0a10426e116f1a0a5ad38382d274a1425cac16d575fc675e9f` |
| `code/pubrules.py` | privacy rules and r3-P30's interval methods (shared with r3-P03) | `241499756e6c5f3145e1cb077412e5be91281470f82b34a4cb965615b814255c` |
| `code/publish_p01.py` | public tables, readings and sensitivity rows | `bdb553b79270a2d138c826cc44f6205ff88bb1a1d95366cc2e6e4ff550c3d7e9` |
| `code/plot_p01.py` | figures | `376cc538e2249564020308fada8e543809d8ffa1bb32508923f3b27deb329202` |
| `code/style.py` | the CHANGE group's style, copied verbatim | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `tolerance-arm-record.md` | the tolerance arm's record (02:29:19Z) | `9fbce94b8f45ba5039ca5cc501ac8d9a932addefdf03880cc267c33d2e20a991` |
| `contacts.md` | contacts (none) | `9b3321a8e8cf0420d5807683e28820fcc5b3c7501557f3c22750bf78bd369e88` |
| `private/` | margins with inputs, per-creator and per-recording values, run logs, the publish and plot scripts as they stood before the sensitivity rows (never published) | - |

README.md and status.json: their SHA-256 are reported to the lead (status.json lists this README's).
The public data CSVs carry a commented header; PNGs at 200 dpi without text chunks; PDFs without document information.
Every public file was scanned for seen creator codes, audio hashes and video ids (none found).

## Departures and choices (stated)

1. **Seam zone** for family B2 and the stable-token rule of family D: a word's midpoint within 1 s of an internal 30-s
   seam, fixed from BR-GS before r3-P02 had reported. r3-P02 later recommended an exclusion row for the zone within 1 s
   of a run-grid seam; it is printed as separate exclusion rows (its `seam_distance` on each word's midpoint) beside the
   unexcluded rows.
2. **Interval method**: see Intervals (r3-P30's file arrived after the first run; applied at publication; variance floor).
3. **Word classes** (fixed in `p01common.py` before any count by voice): contractible pairs by ling's classes A, B and C
   on H4's closed list (a fixed rule on `prep.contractible_pairs`); archaic forms from a closed list of 30 forms written
   by this agent from general descriptions of Early Modern English, blind to the corpus (not the step-2 lexicon; sense
   not resolved, precision unknown); first-person plurals as features.py counts them; names as capitalised forms the
   recording never writes in lower case (prep's not-names list); function words H9's list; filled pauses and all words
   added as reference rows.
4. **Family C alignment**: difflib matching blocks on plain forms with no contraction expansion (a non-expanding
   normaliser), symmetric non-agreement over both decodes; the second decode's words take the voice of the nearest word
   of record in time.
5. **E2** is not set beside a recognizer gap in its own units (a z-scored profile cosine has no instability counterpart);
   the function-word rows stand in.
6. **Base**: the registered claimed voice (V2 + V3, rule B, broad own voice), recordings outside H1's excluded formats
   holding both voices, 13 recordings left out because their voice units did not match the cached words.
7. **Not run** (a.2 or class c, as the programme says): part E, the GPU re-decode, a recognizer of another family, a
   person's word reference, the splice census (r4-P03), rendering direction of contractible pairs (the C rows count any
   non-agreement, not its direction).

## Bases or fields not stored

- A second decode exists only for rv-R3's 35 seen bridge recordings and BR-GS's 40 seen grid-shift recordings, one per
  creator; of these, 10 to 19 and 13 hold both voices under the small model, and fewer than 5 under the middle model.
- No person-made word reference exists for any seen recording (BR-b), so nothing here is an error rate.
- No recognizer of another family and no acoustic syllable count is stored.

## Contacts

None (see `contacts.md`).

## The lead's decisions (2026-11-26)

- The two-sided reading of r3-P01 stands ("beyond the margin on either side"; no named direction).
- The random-effects rows stand as read; the t interval on all creators is printed beside each as a sensitivity row (not
  the reading).
- Stripped labels count as "not stored among the seen instruments"; the reliability folders stay closed.

## Notes

- The seam-share differences (claimed voice slightly more often near seams) are inside their margins but consistent in
  sign across classes; they bear on r3-P07's boundary anatomy, not on this entry's reading.

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
