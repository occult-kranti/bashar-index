# The new-files round (2026-11-27): descriptive persistence on new recordings of the seen creators

Exploratory; not a test of H1-H10.
New recordings of seen creators: a descriptive persistence check, not a confirmation and not a fresh-creator wave.
Rule-based and recognizer-based; not checked by a person; agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these recordings and how the creators present it.


Computed on 2026-11-27 between 04:58Z and 05:44Z (UTC, from the clock); this README was written at 2026-11-27T06:32:30Z (UTC, from the clock). Both by a model agent working for the project lead (not a person), under the round's plan (hashed 2026-11-26T22:49:35Z; published only as a redacted copy, its hash kept privately) and the lead's decision 119.

## What this round is

The question, for each measure: do the seen creators' new recordings give a value inside a margin, fixed before any new value was read, of the value the latest-20+ release or programme printed?

- **Data.** The new uploads, which are later than the latest-20 capture, and the latest-50+ batch, which is mostly older listing positions. Each recording counts once, and only seen creators enter. The bands are in [`scope/`](scope/README.md).
- **What it is not.** It is descriptive. It is not a confirmation, not a test of H1-H10, and not a fresh-creator wave. r3-P20's prediction is not tested here, and r4-P20's rider is not scored. A wave of the same creators tests persistence only.
- **Order of work.**
  1. Every published value used here was first reproduced, to its printed decimals, by the reused code from the latest-20+ inputs.
  2. The reproduction record was hashed.
  3. Only then were the new transcripts opened, through an allow-list.
- **No model or API call, no spend.** The only transfer was a read-only copy of the project's own Drive metadata objects, for the page cues (decision 119.2).

## Readings, in words

| Group | Rows | persists | shifts | undetermined | not computed or not printed |
|---|---|---|---|---|---|
| [recognizer-seams](recognizer-seams/README.md) | 24 | 9 | 0 | 12 | 3 |
| [pace-variance](pace-variance/README.md) | 14 | 4 | 0 | 10 | 0 |
| [patterns-topics](patterns-topics/README.md) | 42 | 7 | 0 | 34 | 1 |
| [lexicon-tier-L](lexicon-tier-L/README.md) | 17 | 3 | 0 | 4 | 10 |
| [page-dates](page-dates/README.md) | 5 | 0 | 0 | 5 | 0 |
| all | 102 | 23 | 0 | 65 | 14 |

- **The pattern.** No row shifts. The rows that persist are those whose new interval is narrow enough to sit inside the margin: recognizer and seam measures, stance wording, some topics, three lexicon classes.
- **Why most rows are undetermined.** A creator here contributes about 3 or 4 new recordings, against about 17 in the latest-20+ corpus. Most new 90% intervals are therefore wider than the margins, and the rows read undetermined.
- **What the words mean.** "persists" is an equivalence description at one-sided 5% per bound. It is expected more often than for fresh creators, because the creators are the same (rv-R2). With no family-wise adjustment, a few "shifts" would have been unsurprising.
- **No paired rows.** Within-creator pairs were computed privately and are not printed (decision 119.1).

## Not computed

Every output of the release and of the programme that needs model-coded labels, an audio pass, a second decode, dated spans or quantiles is listed with its printed reason in [`not-computed.csv`](not-computed.csv). So are the planned rows this pass did not include.

## Privacy

- No creator, channel, person, id, title or transcript text is printed.
- No per-creator row or point, and no quantile.
- Creator sets print only as bands. Any cell that is withheld or not computed reads one label: "not computed or not printed".
- PNG files carry no text chunks; PDF files carry no document information.

## Files

- **Measure groups:** `recognizer-seams/`, `pace-variance/`, `patterns-topics/`, `lexicon-tier-L/` and `page-dates/`. Each holds its README, `public/` (data CSV with a commented header, figures as PNG at 200 dpi and PDF), `contacts.md` and `status.json`.
- **Scope:** `scope/` (the scope table in bands).
- **Not published:** the code, the private working files and the check files.
