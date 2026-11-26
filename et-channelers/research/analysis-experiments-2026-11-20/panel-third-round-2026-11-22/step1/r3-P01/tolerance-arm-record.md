# r3-P01 / r4-P01: tolerance-arm record (written before any voice split)

Written 2026-11-26T02:29:19Z (UTC, from `date -u`) by a step-1 agent (a model agent working for the lead; not a person),
after the tolerance arm ran (02:28:30Z to 02:29:11Z, from `date -u`) and before any claimed-against-own quantity was
computed. No voice label had been opened by any script of this entry when this record was written
(`tolerance_arm.py` does not import the label adapter). Exploratory; not a test of H1-H10.

## Hashes (SHA-256)

| File | SHA-256 |
|---|---|
| `private/tolerance-margins.json` (margins and every input aggregate) | `bd5a940aedc824b60d64346daf454d0ed9ccb0d494ba2dc160e4a5044994b455` |
| `public/data-r3-P01-margins.csv` (the margins, public form) | `5720e794bda5cfc7ea94044aed6154f84024bdcb3cfade6fbba762dab8593f3c` |
| `code/tolerance_arm.py` | `b56f55aaeb2bd6714fcd94e9c9260de58d120661a078f10be9fde67662172f27` |
| `code/p01common.py` (the fixed specification: classes, seam zone, thresholds, readings) | `6f545af4a4b442b2506fbf277d77638aef12dc8347605418b2046144adcce800` |
| `code/test_p01common.py` | `3c0b4aaca7a645bc39fe74a394b5a50ce46e05ee1e06f3668eec24e160b9f724` |
| `code/probe_inputs.py` (structure probe; counts only, no voice split) | `9d5b09432520543527d67a8b9ac4250159aa3436f0de8f42f04eb0e329c13d7d` |

## Binding margins (targeted-error model; claimed-minus-own difference in the share of a class's tokens)

| Row | Margin | Transport margin (family D, own scale) |
|---|---|---|
| contractible pairs, all (H4's list) | 0.0295 | 0.0295 (share) |
| contractible A | 0.0382 | 0.0382 (share) |
| contractible B | 0.0448 | 0.0448 (share) |
| contractible C | 0.0278 | 0.0278 (share) |
| archaic forms | 0.2000 | 0.2231 (log ratio) |
| first-person plurals | 0.0857 | 0.0857 (log ratio) |
| names | 0.0967 | 0.0967 (log ratio) |
| function words | 0.0095 | 0.0095 (log ratio) |
| filled pauses | 0.2000 | 0.2231 (log ratio) |
| all words | 0.0222 | 0.0222 (log ratio of syllable rate) |
| filter removals (per kept word) | 0.0222 | - |

Calibration, voice-free, not binding: q_A = 0.3486 (bridge), q_S = 0.0650 (grid shift); the calibrated margins
(margin / q) are in the CSV.

## Fixed now for the voice split (before it is computed)

- **Voice definition.** The registered claimed voice (V2 + V3, rule B, broad own voice, claimants sole speaker and host
  or owner; `voice_sets.definition`), small model of record on every seen recording (primary); the middle model on the
  seen recordings it labelled in full (row). Recordings: English-only recognizer model, outside H1's excluded formats
  (conversation, multi-presenter), holding both a claimed and an own unit, voice units matching the cached word list.
- **Families.** A: share of class tokens with word probability below 0.5. B1: words removed by the artefact filter per
  kept word, attributed to the voice of the nearest kept word. B2: share of class tokens whose midpoint lies within 1 s
  of an internal 30-s seam. C1: symmetric non-agreement share of class tokens between the English-only model and the
  larger model on rv-R3's 35 seen bridge recordings (difflib matching blocks on plain forms; no contraction expansion);
  C2: the same between the run-grid and the shifted-grid decode on BR-GS's 40 seen recordings; the other decode's words
  take the voice of the nearest word of record in time. C1 and C2 are never pooled. D: the by-voice contrast of the
  class (contraction share drop for contractible rows; log rate ratio otherwise; log syllable rate for all words)
  recomputed on stable tokens only (probability at least 0.5 and outside the seam zone) minus the same on all tokens;
  on the bridge base, the larger model's contrast minus the record's; on the grid base, the shifted decode's minus the
  record's.
- **Creator values.** A, B: precision-weighted mean over a creator's recordings of the within-recording claimed-minus-own
  difference (weight n_claimed n_own / (n_claimed + n_own)); a creator enters a class row with at least 10 class tokens
  on each side. C: one recording per creator, at least 10 class tokens (both decodes) on each side. D: pooled counts
  over the creator's both-voice recordings (log ratios with 0.5 added to counts), same eligibility.
- **Interval and reading.** 90% t interval on creator means (deposit 2; r3-P30's interval choice did not exist). Reading
  per row: "differential instability detected" (reading A) when the interval lies wholly beyond the margin on either
  side; "no differential instability detected among Whisper-family decodes; shared normalisation untested" (reading B)
  when it lies wholly inside it; otherwise "undetermined"; "not computed" under 5 creators. The binding margin is the
  targeted-error margin; the calibrated reading is printed beside it and never replaces it. A family's summary reading
  on a base is B only if every computed row of that family on that base reads B; A if any row reads A; otherwise
  undetermined.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
