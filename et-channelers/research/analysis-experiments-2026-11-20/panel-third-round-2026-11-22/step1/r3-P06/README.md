# r3-P06 / r4-P04: the labeller's prior on asks (codebook-induced association)

Third-round panel programme, step 1 (class a.1). Written 2026-11-26 (UTC times from `date -u` in status.json) by a model
agent working for the project lead (not a person). r4-P04's no-cost part (novelty N04: an application of
incorporation-bias tests; the method is theirs, only the target is this corpus's) is carried by this entry; arm A (the
same offer presented in the source's voice, as minimal pairs) and the name-swap arm are class c and were **not run**.

**Status.** Exploratory; not a test of H1-H10. Seen creators only. Every label is model-coded and not checked by a person;
agreement between models is agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What it asks

Do the stored voice labels put pay-or-enrol ask units into one- or two-unit own-voice islands inside claimed speech more
often than frame formulas, platform asks and length- and position-matched neutral units? If so, LAB-A's pattern (asks
seldom in the claimed voice) could be a property of the codebook's own-offer rule rather than of the speech.
Concentration is not error: the island footprint is one-sided (absence informative, presence undetermined).

## Rule B, as a fact of the frozen instruments (the lead's ruling 5)

Read from the frozen voice and asks prompts of freeze 1 (prompt hashes in status.json; the rule's wording is kept in the
private notes only):

- The frozen voice codebook counts a speaker naming a channel, show, website, offer, event or schedule as their own as
  evidence of the speaker's own voice, and that evidence can end a claimed-voice stretch.
- It counts a bare request (to buy, book, donate, subscribe or share), a link, a price, a date or an event that names
  nothing as the speaker's own as no evidence either way, and says that selling by itself neither starts nor ends a voice.
- Whether an offer that the claimed source itself names as its own counts as that evidence is **not specified by the
  frozen prompt**.
- The primary definition's rule B (in the frozen label code, not in the prompt) keeps the claimed voice in force over an
  own-voice span whose only evidence is such a naming and that directly follows a claimed span not closed by a
  leave-taking.
- The frozen asks prompts code every ask the same way whoever speaks; they say nothing about voice.

So, for arm A: an offer presented as a bare request in the source's first person carries no own-voice evidence under the
codebook; an offer the source names as its own is not specified by the frozen prompt, and arm A remains the only test.

## Method (prespecified in r3-P04's `code/prespec.json`, r3-P06 part, before any outcome)

- H6's definition (claimed voice V2 + V3 under rule B, broad own voice; rule A as a row); recordings with both voices (300
  words each side). Island: a run of 1 or 2 own-voice units with a claimed unit immediately before and after; region:
  claimed units and island units.
- Classes: pay-or-enrol ask units (final asks of the frozen asks instrument); platform ask units; frame-formula units
  (a hit of RX's frozen greeting, devotional-address or community-address sub-patterns, forms the frozen voice codebook
  names as occurring in every kind of voice; cue counts, per-unit flags rebuilt from the ENTRY item's seen word cache,
  numbers only); neutral units (no ask within 2 units, no frame hit).
- Score per creator (stat's exactly centred score): O = ask units in islands, E = the sum over ask units in the region of
  the more island-prone of the neutral share (same position band and unit-length band) and the frame share (same band);
  cohort ratio sum O / sum E with a creator-cluster bootstrap 90% interval; mean score with a t interval (r3-P30 class E_rank_correlation: the t interval on creator means at every simulated count).
- Gate (C24): the lower 90% bound of the log cohort ratio above zero withholds r3-P05's commerce reading. Reading:
  deposit 2's ratio margin (0.80 to 1.25); llm's 1.5 and 1.22 reported beside it as a pointer.
- r3-P02's exclusion row (the lead's note): units within 1 s of a run-grid seam left out, printed beside the unexcluded row.
- Deictic arm (secondary, not part of the gate): within creator, tenth and deictic form (first-person singular, plural,
  impersonal, mixed, from the feature files' counts), ask units coded own against non-ask units of the same stratum.

## Results

- **Reading: undetermined.** Pay-or-enrol ask units inside claimed regions sit in one- or two-unit own-voice islands in
  fewer than 5 creators, under every model, rule and the seam-exclusion row, so the concentration statistic is not
  printed; its cohort ratio and its mean score also disagree in direction (a sign-based score leans negative where few
  island units are expected). The near absence of island asks is the informative side of a one-sided footprint: in these
  labels the island route does not produce LAB-A's pattern. It does not say the labels are right.
- **Gate: did not fire** (the lower bound of the log ratio lies below zero; that interval rests on island asks of fewer than
  5 creators and is not printed). r3-P05's commerce-specific reading is not withheld by it.
- Islands are rare (about 0.4% of claimed-region units on the small model); no frame-formula unit sits in an island under
  either model (about 0.3 expected from neutral units on the small model).
- Platform asks: island units from fewer than 5 creators (not printed). Model difference: not computed (fewer than 5
  creators of the middle-model subset hold ask units in claimed regions). By position band: every band's island asks come
  from fewer than 5 creators (not drawn).
- **Deictic arm (secondary):** on the small model, pay-or-enrol ask units are coded own 1.41 times as often as non-ask
  units of the same deictic form and tenth (90% 1.29 to 1.51; mean score 3.20, 1.95 to 4.44); the lower bound lies beyond
  the margin. The middle model on its subset gives 1.24 (1.06 to 1.40), which crosses the margin; the seam-exclusion row
  gives 1.43. Under llm's pointer rule this arm alone would read "concentrated". Concentration is not error: a host who
  voices offers as themselves produces the same pattern, and only arm A (class c) can tell the two apart.

## Departures

- The island statistic's reference uses position bands of the first tenth, the second to ninth tenths and the last tenth.
- The deictic arm is reported as a secondary row; llm's round-3 memo had made it co-primary. The gate reads the island
  statistic only, as prespecified (den-meth's and den-soc's gate).
- den-mat's plasmode planting islands under both processes (r4-P04's method text) was not built.
- "Do claimed spans end just after asks more than after frame formulas?" (the pooled question) was not built.
- Dissemination asks are not a class of the frozen asks codebook (sharing is pooled into the platform class): not stored.

## Contacts

None (see `contacts.md`).

## For the lead

1. Whether the gate should also read the deictic statistic (it would fire there; it did not fire on the island statistic).
2. Arm A's scoring for an offer the source names as its own: not specified by the frozen prompt.

## Files (SHA-256)

| File | SHA-256 |
|---|---|
| `public/data-r3-P06-concentration.csv` | `624ca5fdd9655c97b4e6fea8617cce7fc045f363c25a3ce69906ef2e5e808416` |
| `public/fig-r3-P06-concentration.pdf` | `96a7ca5741c7408fbcbd973c6cece46958903425112d7e80dad90b22413f86d7` |
| `public/fig-r3-P06-concentration.png` | `7a4103f2c73a86f1bd38cba239dbd7b134f2dc92a852986588d41f89def226ce` |
| `public/r3-P06-footprint.csv` | `5b24f1e95da7bf51adcebfd0b00609d39825a89d41697d37544c615fadd0e2e9` |
| `public/r3-P06-reading.csv` | `617c56652ce4ba65ac7b1fe9637859dd7b9bb616eef430ca4934c7e772b6e29b` |
| `code/extract_frames.py` | `c2b6256f495a7e35f3b76b3d9d8daa0755819aec18b6b1b5487f5192d55c1235` |
| `code/p06_publish.py` | `acf43ec2f596d5d506da4d5b4c26e70c5df7cd39a7c19189db71125acd182a55` |
| `code/p06_run.py` | `ac0bc4b26a5cb0ca3ab801cf3abae18e837c91919ddd682efe389bf5b9ba62dd` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `../r3-P04/code/common.py (shared)` | `afb6dcf765d44997672e7341911a70990e889cd6407bf50145ebc41dc016874b` |
| `../r3-P04/code/intervals.py (shared)` | `f428af347014e1b390261794aa58fc6f573b612bb3148aac3db6883d965c599d` |
| `../r3-P04/code/prespec.json (shared)` | the hash recorded at hashing time is kept privately |
| `../r3-P04/code/pubcommon.py (shared)` | `b3a81fe31eee2e48d614ae72db333dbabaebef4a07fe38f52e52bffad0296d02` |
| `../r3-P04/code/scan_public.py (shared)` | `73bbe208ffa5e6ddadc59fa01173a4ae2b181ad748f325997087c723c1696ec9` |
| `../r3-P04/code/write_status.py (shared)` | `b24b1f356fbd180caef9dc8ccd3a591fcf3962d311f047b73717243d2071993f` |

Code files carry local paths and stay private; their hashes are the record. Per-creator numbers stay in `private/` under anonymous indices.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these recordings and how the creators present it.

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
