# Contacts, r3-P02 / r4-P02 (step 1)

Times are UTC from `date -u` (file times converted from the local clock where noted).

## Logged read, ruled not a contact (D31; the lead's step-1 decision 6): the bridge plan's other-group row (selection metadata, parsed in memory)

- **What:** `bridge-plan.json` (the run's bridge selection plan) holds 36 rows; one belongs to a creator outside the
  seen and hold-out sets (the "other" group). Each row carries selection metadata (channel folder, audio hash, video id,
  minutes, non-speech share, pace cell). The file was parsed whole in memory and its rows filtered to seen creators by
  channel folder (`prep.groups()`); no value of the other-group row was printed, stored, compared or used, and that
  row's bridge transcript was never opened. GRID (its bridge script, in round 2's private code folder) and MR (`mrcommon.py`) read the same
  plan the same way; it is logged here because the file holds that row's selection values.
- **When:** three parses: a structure probe at about 2026-11-26T02:18Z (it printed only the key names and the count of
  seen rows; logged at 02:18:32Z); a test of the extractor between 02:33Z and 02:35Z (one seen row used); the extraction
  run 2026-11-26T02:35:03Z to 02:35:31Z.
- **Not read:** `bridge-ledger.jsonl`; any bridge transcript outside the 35 seen rows.

## Not contacts (the run's standing practice)

- `prep.recordings()` reads the run ledger's manifest (rows of every group: channel folder, audio hash, duration,
  language), as every package does, to select seen rows; no transcript of another group was opened (`prep.allowed`
  refuses one).
- The seen voice and feature labels were read through the frozen package's seen-only path (`adapter.load_seen_bundle`),
  which refuses labels/holdout and labels/other before listing.
- BR-GS's grid-shift plan holds the 40 seen rows only (checked: 40 of 40 seen).
- No recursive text search was run over the run folder, llm/labels/holdout or llm/labels/other.

Written 2026-11-26T02:50:56Z.

Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
