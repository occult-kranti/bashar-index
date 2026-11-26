# r3-P55: endorsement placed in the claimed voice at matched positions

Third-round panel programme, step 2 (class a.2, ruling 11), co-occurrence as a lower bound, in one pass with r3-P56 after
r3-P06. Run on 2026-11-26 (UTC, from `date -u`) by the step-2 description agent, a model agent working for the project lead
(not a person), in one run with the other six step-2 description entries (shared code and run record in `../r3-P48/`;
prespecification `prespec.md`, hashed 12:46:51Z with the shared rules of `../r3-P48/prespec.md` section 0).

**Exploratory; not a test of H1-H10.** The 23 non-development seen creators (tier L), run once with no split. Cue counts:
sense not resolved, precision unknown. Voice labels model-coded, not checked by a person. Not asking is not standing outside
commerce; endorsement and offers are described neutrally, as the creators make them.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Results in words

- **The primary is not computed**, as expected: the co-occurrence of a REF-CREATOR term (the creator referred to as "this
  channel" or "this instrument") and an endorsement predicate needs REF-CREATOR, which is thin by design ("not computed (too
  few terms or creators)"). The within-creator claimed-minus-own difference, its position-matched band and its histogram
  do not exist.
- **den-soc's rows.** ENDORSE (endorsement predicates) passes the thin rule, but fewer than 5 voice-eligible creators carry
  it in either voice, so "endorsement present, by voice" is not printed (with or without "support this channel"). "No price
  in the claimed voice": claimed-voice endorsement hits rest on fewer than 5 creators (not printed). Beside it, the
  own-voice share (over 5 to 9 creators) is not printed either (privacy rule; the lead's step-2 decision 95, 2026-11-26T15:34:10Z UTC; the
  data file and figure were rewritten by `code/publish_p55.py`; no number changed).
- **occult's historical row** was not in deposit 3: "not scored (not deposited)".
- No prediction is scored.

## Classes not computed

REF-CREATOR and the co-occurrence; the endorsement rows by voice and the claimed-voice no-price row (fewer than 5 creators).

## Files

| File | What |
|---|---|
| `public/data-r3-P55-rows.csv` | status and den-soc's rows |
| `public/fig-r3-P55-status.*` | the status figure |
| `prespec.md`, `prespec-hash-record.md` | the prespecification and its hash |
| `code/p55.py`, `code/publish_p55.py`, `code/style.py` | analysis (run by `../r3-P48/code/analyse_desc.py`) and publication |
| `contacts.md`, `status.json` | contacts (none); status with every file's SHA-256 |

## Privacy

The own-voice row's count is banded ("5 to 9"); its share is a description with no interval. Checks: see
`../r3-P48/README.md` (0 problems).

## Departures

None specific; shared departures in `../r3-P48/README.md`.
