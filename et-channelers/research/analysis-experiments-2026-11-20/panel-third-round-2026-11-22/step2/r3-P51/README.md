# r3-P51 / r4-P28: named actors and contested content, by voice

Third-round panel programme, step 2 (class a.2, ruling 11), description only. Run on 2026-11-26 (UTC, from `date -u`) by the
step-2 description agent, a model agent working for the project lead (not a person), in one run with the other six step-2
description entries (shared code and run record in `../r3-P48/`; prespecification `prespec.md`, hashed 12:46:51Z with
the shared rules of `../r3-P48/prespec.md` section 0).

**Exploratory; not a test of H1-H10.** The 23 non-development seen creators (tier L), run once with no split. Cue counts:
sense not resolved, precision unknown. Voice labels are model-coded and not checked by a person. Named institutions and
contested content are described as vocabulary in speech, neutrally: a count is not a stance.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Results in words

- **Every class is too thin.** All eleven classes of L07 (contested public-health content, institutional and
  consciousness-based disclosure, security, space, international, government, religious, media and corporate institutions,
  and den-soc's criminal-law rows) and every sub-register of L05 read "not computed (too few terms or creators)"; CR-A reads
  "not computed until r3-P54 (waits for the owner's ethics act)". So no unmatched, position-matched or middle-model class row
  exists, the institutional-against-consciousness disclosure split is "not computable (a disclosure class is thin)", and the
  row by stratum composition is not computed (a title-profile stratum holds fewer than 5 voice-eligible creators).
- **The model-free named-actor proxy** (runs of two or more capitalised, not sentence-initial tokens, minus listed source
  names; it also catches place and organisation names and the recognizer's capitalisation) can be computed. On the 11
  voice-eligible creators, the per-creator log rate ratio of claimed over own voice averages -0.70 (90% t interval on
  creator means, r3-P30's choice for class H at this count, -1.21 to -0.19): proxy runs are less frequent in the claimed
  voice, but the interval reaches inside the margin (log 1.25), so the reading is **"undetermined"**. Position-matched (own
  voice re-weighted to the claimed voice's tenths of the recording): -0.50 (-1.05 to 0.05), "undetermined". The middle model
  labelled too few of these creators' recordings in full: "not computed (too few terms or creators)".
- **The three-way prediction table** (meaning, news hook, attribution shield) was not deposited before any count: "not
  scored". No direction is deposited, so the words are "beyond the margin (...)", "within the margin (B)" or "undetermined".

Multiplicity (deposit 2): no family-wise adjustment; 56 primaries, about 2.8 readings beyond a margin expected by chance at
half-margin effects.

## Classes not computed

All L07 classes and L05 sub-registers (thin; CR-A waits for r3-P54); the disclosure split; the stratum row; the middle-model
row of the proxy; the prediction table (not scored).

## Files

| File | What |
|---|---|
| `public/data-r3-P51-classes.csv` | every class and sub-register with its status; the disclosure split, stratum and prediction-table rows |
| `public/data-r3-P51-proxy.csv` | the named-actor proxy: overall rate and the voice contrasts |
| `public/fig-r3-P51-voice.*` | the proxy's paired-difference dot plot beside the class statuses (PNG 200 dpi; PDF without document information) |
| `prespec.md`, `prespec-hash-record.md` | the prespecification and its hash (shared rules: `../r3-P48/prespec.md`) |
| `code/p51.py`, `code/publish_p51.py`, `code/style.py` | analysis (run by `../r3-P48/code/analyse_desc.py`) and publication |
| `contacts.md`, `status.json` | contacts (none); status with every file's SHA-256 |

## Privacy

No name, run or person is printed or stored outside `private/` (counts only). Creator counts printed: 23 and the 11
voice-eligible creators (r3-P42's set, same form); the middle-model set prints "fewer than 5". Every check of
`../r3-P48/README.md` (identifier scan, solvers, nesting check) covers this folder: 0 problems.

## Departures

- The middle-model row is "not computed" (fewer than 5 eligible creators), as the programme anticipated for small groups.
- "By stratum composition" is read as the title-profile stratum of CSS-5 (the prespecification's choice).
- Shared departures of the run: `../r3-P48/README.md` (none changes this entry's rows).

## For the lead

- Whether "a row by stratum composition" meant the title-profile stratum (as fixed here) or a composition of L01's strata
  (r3-P43's, not computed on these creators either) (decided: decision 69).
