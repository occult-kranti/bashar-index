# r3-P53 / r4-P30: self-described modes of mediation, and where the voice code files them

Third-round panel programme, step 2 (class a.2, ruling 11), the cue part (classification is class c). Run on 2026-11-26 (UTC,
from `date -u`) by the step-2 description agent, a model agent working for the project lead (not a person), in one run with
the other six step-2 description entries (shared code and run record in `../r3-P48/`; prespecification `prespec.md`, hashed
12:46:51Z with the shared rules of `../r3-P48/prespec.md` section 0).

**Exploratory; not a test of H1-H10.** The 23 non-development seen creators (tier L), run once with no split. Mode is
self-presentation: "creators who describe their practice as X", from cue counts in speech (sense not resolved, precision
unknown). Voice labels are model-coded and not checked by a person.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Results in words

- **Two of eight modes can be counted.** Relay and higher self or Source have 3 or more cue forms used by 5 or more
  creators; full trance, conscious or blended, dictation, received text read aloud, recitation of another receiver's message
  and light language ("vocalisation without recognisable words, self-described as light language") read "not computed (too
  few terms or creators)", as the programme expected (N30).
- **Creators who describe their practice as higher self or Source** (2 or more cues): 18 of the 23 (0.78). **As relay:**
  10 to 19 creators (a banded count). With 1 or more cue, relay gives the same group; the higher-self count: not printed
  (privacy rule).
- **LAB-V's claimed share per mode group** is not printed for either mode: a group's count is banded or a group is too
  small, and group means beside an overall mean could then solve for group sizes.
- **Where the voice code files the cues (r4-P30).** Of relay cues in recordings inside the voice definition, a
  creator-balanced 0.47 fall in claimed-voice units and 0.53 in own-voice units or units with no voice side; of higher-self
  cues, 0.43 and 0.57. The voice code files both kinds of self-description on both sides. No correct filing is defined, so
  no misfiling rate is read. The modes the programme names as most at risk of misfiling (conscious or blended, dictation,
  received text read aloud) are thin here. The shift by mode belongs to r3-P16.

## Classes not computed

MODE-TRANCE, MODE-CONSCIOUS, MODE-DICTATION, MODE-READALOUD, MODE-RECITATION, MODE-LIGHTLANG; LAB-V's claimed share per
group (privacy); the shift by mode (r3-P16).

## Files

| File | What |
|---|---|
| `public/data-r3-P53-modes.csv` | every mode with its status, group counts, filing shares |
| `public/fig-r3-P53-modes.*` | creators by mode (multi-label bars; a banded count drawn as its range) and filing shares |
| `prespec.md`, `prespec-hash-record.md` | the prespecification and its hash |
| `code/p53.py`, `code/publish_p53.py`, `code/style.py` | analysis (run by `../r3-P48/code/analyse_desc.py`) and publication |
| `contacts.md`, `status.json` | contacts (none); status with every file's SHA-256 |

## Privacy

Counts near published counts are banded; one count is not printed (privacy rule); the no-side part of the filing
shares rests on fewer than 5 creators and is merged with the own-voice part. Group means are printed only where group counts
print exactly (none here). Checks: see `../r3-P48/README.md` (0 problems).

## Departures

1. The filing shares print two parts (claimed; own or no side) in place of three, for the 5-creator floor.
2. The higher-self sensitivity count (1 or more cue) is not printed (privacy rule). Its note was worded as a rule under
   the lead's step-2 decision 86 (2026-11-26T14:54:05Z, UTC); the data file was rewritten by `code/publish_p53.py`; no number changed.
3. The group difference of LAB-V's claimed share would use the two-sample (Welch) t interval (run record); it is not
   printed.
