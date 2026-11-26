# r3-P02 / r4-P02: input stability and grid marks in the labels

Third-round programme, step 1, first run (class a.1; r4-P02 is carried). Written 2026-11-26T02:49:30Z (UTC, from
`date -u`) by a step-1 agent (a model agent working for the project lead; not a person). Exploratory; not a test of
H1-H10. Seen creators only; no model call, no download. Voice labels are model-coded (the small model of record, rule B;
the middle model as a row) and not checked by a person; transcripts are recognizer output, not checked by a person;
agreement between two decodes is agreement of two machines, not accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Question

Does the 30-s decoding grid leave marks in what the voice labeller reads? Two parts (programme 2.1, r3-P02; round-3
pooled P02; round-4 N02 and N03): (I) do claimed-voice boundaries lock to the decoder's seams, against a circular shift
and against the boundaries of the shifted-grid re-decode? (II) is punctuation near seams a mark of the grid (pauses make
punctuation; the label reads punctuation, D5), and does that differ by voice? Its result fixes the seam-zone exclusions
for r3-P01, r3-P06, r3-P07 and r3-P09.

## Bases (as the stored data hold them)

- **All seen labelled recordings** (1,284 voice-label files of the 71 seen creators; 13 hold no words after the artefact
  filter): seam-distance rows, the circular-shift reference, the D5 and window-phase rows. Primary I's base: the 65
  creators with a claimed-voice boundary. Middle-model row: the recordings it labelled in full (50 to 59 creators with a
  boundary).
- **BR-GS's 40 shifted-grid re-decodes** (one recording per creator; grid moved by 15 s): the re-decode reference of
  primary I (between 10 and 19 of these creators have a claimed-voice boundary) and primary II's grid row.
- **rv-R3's 35 seen bridge decodes** (the larger model, same worker and grid; one recording per creator): primary II's
  model row. The bridge plan's other-group row was dropped before any bridge file was opened (`contacts.md`).
- By-voice rows only on recordings holding both voices (10 or more units of each): between 5 and 9 creators (grid
  shift), 11 (model change).

## Method (fixed in `code/prespec.json` at 02:29:51Z, before any value of this entry was computed)

**Prespecification timing** (added for publication, 2026-11-26; the lead's step-1 decision 43). `code/prespec.json` is published as `prespec.json` (verbatim; decision 48). The recorded fixing time (02:29:51Z) precedes the file's last write (02:30:19Z) by under a minute. The file was not written again before the first outcome (the private label copy at 02:32:11Z; the word pass from 02:35:03Z). Its SHA-256 was first recorded in status.json at 02:52:43Z, after the run, so the order rests on the file's last-write time.

- **Seam:** a multiple of 30 s (the record's grid); the re-decode's seams at 15 s and every 30 s after. Seam zone: within
  1 s (BR-GS's band). The seam distance of any word or boundary is `p02_lib.seam_distance(t)` of its stored time, so the
  per-token seam-distance flag asked for r3-P39 and r3-P52 is a function, not a stored file.
- **Primary I.** A claimed-voice boundary is a change between a claimed-voice unit (V2 or V3) and any other unit,
  timed at the midpoint of the gap between the two units (feature-file unit times). Creator value: near-seam share of
  the creator's boundaries minus the reference share. Reference R1 (primary): each recording's label sequence rotated
  over its fixed sentence units (999 random rotations). Reference R2: each labelled boundary moved to the nearest
  sentence-unit boundary of the shifted-grid re-decode (units rebuilt by prep's rule after the same filter). Named rows
  (same direction needed for A): middle model, entries apart, exits apart. Margin 5 points; named direction positive.
  A: both references beyond the margin and the named rows the same way; B: both inside; else undetermined.
- **Primary II.** Words of record matched to the second decode's words (same normalised text, start within 0.5 s).
  Sentence-mark agreement: among matched pairs where either decode ends the word with . ? or !, the share where both do.
  Creator value: agreement in a placebo-seam zone (the seam zone moved to the points farthest from every real seam: 7.5
  s for the grid shift, 15 s for the model change) minus agreement in the real-seam zone. IIa grid shift (primary row),
  IIb model change (named row). Margin 5 points; named direction positive. A: IIa beyond and IIb the same way; B: both
  inside; else undetermined. The voice difference (claimed minus own) is read on its own, two-sided (no direction named).
- **Intervals:** 90%, by the method r3-P30's `interval-choice.csv` names for the class at the base's count (class B for
  creator values pooled over recordings; B1 for one recording per creator); the t interval on creator means is printed
  beside. Described rows use the t interval on creator means. A reading is capped at undetermined where r3-P30 finds no
  method that holds.
- Runs (under `run_locked.sh`, 4 worker processes at most, each passed one recording's label slice and paths):
  `p02_labels.py` 02:32:11Z (seen-only adapter path); `p02_extract.py` 02:35:03Z to 02:35:31Z; `p02_analyse.py` first
  run 02:40:42Z, last run 02:44:16Z (wording fixes only: count bands, series names, a complement check); `p02_plots.py`
  reads the public CSVs only.

## Readings (the primaries, in words)

- **Primary I (seam lock of claimed-voice boundaries): undetermined** (some rows' readings are not printed for
  privacy). Against the circular shift (65 creators),
  claimed-voice boundaries lie near a seam *less* often than the rotated labels would: about 10% of boundaries against
  13% for the reference and 6.7% for an even spread (sentence-unit boundaries themselves lie near a seam 6.3 points more
  often than an even spread). The chosen interval (HKSJ floored, r3-P30 class B row 50) is -0.047 (90% -0.057 to -0.037),
  crossing the margin's negative side, while the t interval on creator means (-0.043 to -0.022) lies inside: the
  estimators disagree. Entries (-0.071; -0.084 to -0.057) lie wholly beyond the margin, in the direction opposite to
  the named one; the exits row and the middle model's row are not printed (the rows' counts are banded). Against the
  re-decode (between 10 and 19 creators) the row is not printed (the row's count is banded). Neither reading A nor B.
- **Primary II (punctuation agreement near seams): undetermined.** Under the grid shift (40 creators), sentence-mark
  agreement is 0.39 within 1 s of a seam of either grid against 0.71 in the placebo zone: a difference of 32.5 points
  (90% 28.5 to 36.5; t interval, B1 row 40), wholly beyond the margin as a row. Under the model change on the same grid
  (35 creators) the difference is -2.4 points (-9.0 to 4.3): its named row points the other way, so the pre-specified
  reading is undetermined.
- **Voice difference of the seam effect (claimed minus own): undetermined** under the model change (-14.9 points; -44.3
  to 14.6; 11 creators); under the grid shift (between 5 and 9 creators) not printed: the row's count is banded.
- **Seam-zone rule (pre-specified):** neither primary reads B, so an exclusion row for the seam zone (within 1 s of a
  run-grid seam) is recommended for r3-P01, r3-P06, r3-P07 and r3-P09.

**Half-effect disclosure** (deposit 2): the register holds 56 primaries; if every true effect sat at half its margin,
about 0.05 x 56 = 2.8 readings would pass the floor rule by chance at the 90% level's one-sided 5% (r3-P30 finds the
per-primary rate for share differences near 0.04 to 0.06). A reading A is never called a finding.

## Described rows (not read; `public/r3-P02-described-rows.csv`)

- Comma agreement and unit-end agreement fall at seams under the grid shift as sentence marks do (placebo minus real:
  +26.0 and +25.6 points); capital-letter agreement barely moves (+1.0). Under the model change comma agreement moves by
  +7.4 points (-1.5 to 16.2), unit-end agreement by -3.6 (-9.6 to 2.4) and capital-letter agreement by +0.6.
- The re-decode's unit boundaries sit near *its own* seams (+6.0 points over an even spread) and not near the record's
  (+0.4): unit boundaries follow the grid that made them. A labelled boundary moves 4.5 s on average when projected onto
  the re-decode's units.
- On all seen labelled recordings, a word ending within 1 s of a seam carries a sentence mark about twice as often as a
  word 5 to 15 s from one (0.125 against 0.058 per word), in both voices.
- D5: a word followed by a gap under 0.3 s ends with a sentence mark 2% of the time, after 0.3 to 1 s 45%, after 1 s or
  more 63%. The coupling (1 s or more minus under 0.3 s) is 5.6 points weaker in claimed voice than in own voice (90%
  2.3 to 8.8 points; 50 to 59 creators): described, not read.
- Own-voice islands of 1 or 2 units inside claimed voice do not sit nearer seams than the circular shift (-1.7 points;
  -7.2 to 3.7; 23 creators). On the primary definition's recordings, I-R1 is -3.7 points (-5.3 to -2.1).
- r4-P02 (`fig-r3-P02-window-phase`): edits, removed thanks phrases (partly by the filter's construction) and segment
  starts peak at the record's seams in both voices (segment starts: about 18% in the first second after a seam against
  about 3% per second elsewhere); on a placebo grid moved by 15 s the peaks move with the seams.

## Files

| File | What | SHA-256 |
|---|---|---|
| `public/r3-P02-readings.csv` | Read rows with base, method, estimate, interval, t interval beside, reading; the two primary readings and the seam-zone rule | `47e91e0e88028024b6bb015e1bb288316569945cdf10f2838009044f03661661` |
| `public/r3-P02-described-rows.csv` | Described rows (comma, case, unit-end agreement; sentence-unit rows; seam bands; D5; islands; subset) | `5a0a33eaad2a4b2633c1495e4576913fdd09b01f139735f542e9cb8bfbd799e2` |
| `public/data-r3-P02-punctuation-profile.csv` | Figure data: agreement by seam-distance band and voice | `8a397da5a3256beddc2653120827bb8c5b82120bc1d490fe5246aac4883cd289` |
| `public/data-r3-P02-boundary-phase.csv` | Figure data: boundaries folded modulo 30 s, circular-shift band, unit boundaries | `528ccc85496def78cc57a09bb9b19c422a6e86393cd5530d0352892336d5118c` |
| `public/data-r3-P02-window-phase.csv` | Figure data (r4-P02): edits, removed thanks phrases, segment starts by phase, own and placebo grid, by voice | `3b83be1b9ad41b773fc1a114bff16ece4bf119e0bb263d5c02186ec8f9a412e9` |
| `public/fig-r3-P02-punctuation-profile.png` / `.pdf` | Punctuation agreement against seam distance, one line per voice | `b894d6a8c4899e7f06e6e42803d4e515010a4f4f438b8b21371d9acb73808764` / `cbb6bfaee1a56cdda2c2a7aa04bfb06b8699b528965c77e9f2217287a9622d9b` |
| `public/fig-r3-P02-boundary-phase.png` / `.pdf` | Boundaries folded modulo 30 s against the circular-shift band, entries and exits apart, one row per model | `222dd6a381cef7778ade8a7b27b35dd6bf2322e62d9e55c96ba563c84d3a6cfe` / `e53b3ce54a82954e3611cead7125a0aabaaf799c8e2d8c242be13dcf0d0519ca` |
| `public/fig-r3-P02-window-phase.png` / `.pdf` | r4-P02: shares by window phase on own and placebo grids, by voice | `2eb424ffbc071686eac421fe44124c394c974bbe2c01ccdcaa98a8146e3c962e` / `9996e830d558c92fd6ad97b497fbe520ac2d51396ed4188ffbcb8b98c0526bcf` |
| `public/fig-r3-P02-readings.png` / `.pdf` | The read rows against the margin | `c39af60be26bf9337168e1c0b77c8e5216a0a099e2bdbaf8221574060099df8d` / `c8c14c591e3f87cb5bb2b39359e22528f76a104ba6af4b53b2c46698d295e935` |
| `code/prespec.json` | The design, fixed before the run | `d3bee6135919e4265714ebc9fe6545194034b8c526253ee91c66fdb8eef055fe` |
| `code/probe_bundle.py` | Structure probe (keys and counts only) | `ed8df6812211560c978c2e2978b641374c8d16c9821695a409219240f427ec99` |
| `code/p02_labels.py` | Private label copy (seen-only adapter path) | `f9273827d0e06e12a4052fdafac6d2154b9360cc05b2d35e4108964c0ec21592` |
| `code/p02_extract.py` | Word pass and pair alignment (aggregates per recording, private) | `9f5e3dc53b610186df4d89b4271d947fbfb86b469346166ae35e8bd71b605650` |
| `code/p02_lib.py` | Intervals by r3-P30's choice, readings, nested-count register, seam distance | `35d3e016e58a10d528149f268511f4ff42e7d2b8750b1470cff969a7225dc658` |
| `code/p02_analyse.py` | Estimates, readings, public tables | `49165448595ceaff0f688dd5a0455cb9e0c55b9717bd563f0c180bb7cebc67f2` |
| `code/p02_plots.py` | Figures (from public CSVs) | `bd2a5e26d1805d5f3a1e0bb100225b7efc72bd5266f8e26443667c2422a7e955` |
| `code/style.py` | Chart style, copied unchanged | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |

Private (not published): `private/labels.private.pkl`, `private/extract.private.pkl`, `private/analyse.private.json`
(including the printed-count register), logs.

## What is withheld, and why

- Creator counts 1 to 4 away from a nested printed group, or from 101, 23, 18 or 6, are printed against that group
  ("all but fewer than 5 of 65") or as a band ("between 10 and 19", "between 5 and 9").
- Window-phase bins whose events come from 1 to 4 creators: "not published" (mostly the removed thanks phrases outside
  a window's last 3 s, by voice).
- No per-creator value, id, name, title or quotation is in any public file; no near-100% share has misses from 1 to 4
  creators (checked for every agreement row).

## Departures from the programme, and choices it left open

1. The programme names the references and plots but not the measures; the agent fixed them in `code/prespec.json`
   (boundary time at the gap midpoint; 1-s seam zone; R2 as the projection of labelled boundaries onto the re-decode's
   units, since the re-decode carries no labels and relabelling is class c; primary II's reference as the placebo-seam
   zone, the circular shift of the seam grid).
2. The voice difference is read two-sided (no direction was named).
3. R1's chosen method (HKSJ floored) needs a within-creator variance: a 200-draw bootstrap of each creator's recordings
   (creators with one recording left out of that method).
4. The per-token seam-distance flag is a function of stored word times (`p02_lib.seam_distance`), not a stored file.
5. Not run: relabelling the shifted-grid or bridge transcripts (class c, about 1 to 5 USD); a grid shift over the whole
   seen roster (GPU re-decode, a.2); the per-span input-perturbation share for r3-P19 (round-3 pooled method, not in the
   adopted text); labels on the bridge's larger-model transcripts (rv-L2's 25 pairs used a pre-freeze instrument
   snapshot).
6. Removed thanks phrases are identified by replaying the artefact filter's thanks rule; their peak in a window's last
   3 s is partly by construction of that rule.

## Fields or bases not stored

- No labels on any second decode (shifted grid or bridge): R2 and the by-voice pair rows rest on the record's labels.
- Shifted-grid decodes exist only for BR-GS's 40 recordings and bridge decodes only for rv-R3's 35 seen recordings,
  one per creator each.

## For the lead to decide

- **Primary II's named row.** The model change keeps the grid, so both decodes put their seam marks at the same seams;
  IIb was bound to point away from IIa. Under the pre-specified rule II reads undetermined although IIa alone lies wholly
  beyond the margin. Whether IIb should have been a named control row is the lead's call; nothing was changed here.
- **Primary I points the other way.** Relative to the sentence units they sit on, claimed-voice boundaries avoid the
  seams (entries and exits wholly beyond the margin's negative side), while R2 suggests some boundaries sit on units the
  grid made. The deposited readings have no word for "beyond the margin against the named direction"; it reads
  undetermined.
- **Seam-zone exclusion** recommended for r3-P01, r3-P06, r3-P07 and r3-P09 (pre-specified rule).
- **The D5 coupling is weaker in claimed voice** (described, not read): sentence marks follow pauses less closely there,
  which bears on any pause or punctuation contrast by voice.
- Contacts: the bridge plan was parsed to drop its one other-group row (`contacts.md`).

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
