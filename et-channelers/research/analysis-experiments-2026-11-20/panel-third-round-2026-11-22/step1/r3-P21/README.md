# r3-P21: a drift audit of the frozen instruments

Third-round programme, step 1 (class a.1, identifier tabulation). Written 2026-11-26 (UTC times from `date -u` in
`status.json`) by a step-1 agent (a model agent working for the lead; not a person). Exploratory; not a test of H1-H10.
No model or API call. Every label is model-coded and not checked by a person; agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Question

(1) Did the model aliases resolve to one snapshot throughout? (2) Did the two interfaces (batch and standard) code alike?

## Prespecification and sources

- `prespec.md` (SHA-256 `869d53e649efba94369f17ce080210b9d9060c35a45e4f1ed40883e6a1fe18e4`), hashed at
  2026-11-26T06:34:50Z (`prespec-record.md`), before any snapshot string, interface count or coded value was tabulated.
- Read: the spend ledger and the batch-job ledger (metadata of every run), and 126 seen-side answer stores (production
  seen, pilot and gate, second readings and PT, smoke, probe and self-test, and the discovery store's metadata): from
  each row only the request id, status, interface, the model string the API returned and the time. Never opened: the 24
  answer stores of hold-out, R-hold, other-group and reliability runs, `llm/labels/holdout`, `llm/labels/other`, the
  reliability folders. Coded values (`text`) were not read: part 2 found no item to compare.

## Readings (descriptions; no margin, no interval: a tabulation)

- **Part 1, alias to snapshot: one returned string per alias throughout the stores read, but every string is the bare
  alias, with no dated snapshot.** The small model's alias came back as itself in about 188,000 answered requests
  (standard and batch), the middle model's in about 32,000, the two large-model aliases in about 3,400, from
  20 November 20:59 to 21 November 11:09 UTC. Whether an alias resolved to one snapshot behind that string **cannot be
  told from stored runs**. The hold-out, R-hold and other-group runs (ledger: batch jobs created 21 November 16:16 to
  18:05 UTC, standard rows to 18:40 UTC, after freeze 1 at 16:06 UTC) were not opened, so their strings are not read; on
  the seen side the record ended at 11:09 UTC, so seen and hold-out codings lie about 5 to 13 hours apart, with nothing
  stored that could show a change of snapshot in between.
- **Part 2, did the interfaces code alike: not computable from stored runs.** No request was answered under both
  interfaces in any seen-side store (rows copied by adoption left out). The seen production record does mix interfaces,
  but by instrument and model, not by item: for voice, the small model's map and labels came through the standard
  interface and the middle model's labels through batch; for asks, forecasts parts B and C, sentence codes and titles
  each interface coded different requests (`public/r3-P21-interfaces.csv`, section A). A comparison of those codings would
  compare different items, models and times, so it is not made.

## Figure

`fig-r3-P21-snapshots`: the alias-to-string timeline by interface and store group. The programme's plot (agreement with
the record against the time gap between readings, by interface, over the run-to-run band) cannot be drawn: no item has
readings under both interfaces, and repeated readings are not matched item by item in the stores (below).

## Files

| File | SHA-256 |
|---|---|
| `public/fig-r3-P21-snapshots.pdf` | `f275e9e84211df5f826714fc40aecc665403caa3b3421b43848c40451493e5a4` |
| `public/fig-r3-P21-snapshots.png` | `ccd9261cc276db9b2bbbf73018b4e87b20909b77834472e99a256a1347ad0e45` |
| `public/r3-P21-interfaces.csv` | `e08b75d4f10cf7538e3d5cce4b71e402f8d5c4309ebb7e0807e29fba0d92251a` |
| `public/r3-P21-snapshots.csv` | `ff4edd14fa0584337bb3655938777cb43a0e9d3265d6737ef692bd0072009474` |
| `code/finalize.py` | `f3711f285ef2310f56383d4aa121c8cd25157913ab3d85edde2ce1ef91e3d7fe` |
| `code/p21_publish.py` | `efbd2b71454ea7d5b49e5d4755d6187d43cad5095b72a233fd802a853d7416d4` |
| `code/p21_run.py` | `c2726408c49c22d726433dd8e3da90bf1de4deda18d8b13d9c7e11e894a8f01e` |
| `code/pubrules.py` | `241499756e6c5f3145e1cb077412e5be91281470f82b34a4cb965615b814255c` |
| `code/scan_ids.py` | `8e13207c018538e592903f635f90c4bdce058848f8d9292bef3a2945fcaae14c` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `code/scans/qscan_all2.py` | `f3c5f0ca854a68e143e306cb52083e9d0dc127859b495b252fc5ca4f33976b69` |
| `code/scans/quant.py` | `a2478a09a37c3c759485fdfa3e0f98c6cd1d9a3094cc3b58c566588a9b1cae5c` |
| `code/scans/quant2.py` | `7421b55e42d6fd55880a4b44dbc42c89c5991f18ba652374a2a4e93865ce9248` |
| `code/scans/zsolve.py` | `85f81e9866da1fd527216198137927650fff6352b8b03f58bb118a58fecec864` |
| `prespec.md` | `869d53e649efba94369f17ce080210b9d9060c35a45e4f1ed40883e6a1fe18e4` |
| `prespec-record.md` | `7b253b45cc9e9a7ee3c149f90019856a25346a9e61dd10106929b15250e88ca7` |
| `contacts.md` | `58dc4b4c377e3f4a6d579fb0cd13eab424be041522a2fe06b465366893037347` |

Private (not published): `private/` (per-creator and per-recording values, sums, run logs). Public data CSVs carry a commented header; PNGs at 200 dpi without text chunks; PDFs without document information.

**Privacy scans** (copies in `code/scans/`, `REL` set to this entry's `public/`): zsolve.py: 0 rows tested, 0 pinned, 0 narrowed; qscan_all2.py: 0 files with quantile columns, 0 rows with a hidden or banded base; identifier scan (creator codes, audio hashes, video ids): 0 hits; PNG text chunks and PDF document information: none. quant.py and quant2.py copied; they read the 'quantiles' column of one release file, and no public file of this entry has such a column, so they were not run on it.

## Departures and choices (stated)

1. The programme's plot is replaced by the timeline (part 2 not computable).
2. The run-to-run band is not built: repeated gate runs are stored under separate run tags whose request ids differ by
   tag, and an answer row holds no item key; matching them needs the instruments' request builders re-run on gate-sample
   inputs, which this metadata entry does not do. The published stability figures (GATES; VER-SHARD) stand as they are.
3. The anchor re-read at a wave (class c, 3 to 6 USD) is not run.

## Fields not stored

A dated snapshot name (the API returned the alias); an item key in answer rows (needed to match repeated readings); the
returned model string in the spend ledger (it holds the requested model only, for a few setup rows).

## For the lead

- The frozen instruments' model identity is fixed only at the alias level in the stored runs. Drift between the seen
  record (21 November, before 11:09 UTC) and the hold-out record (after 16:06 UTC) cannot be excluded from stored data;
  only the class-c anchor re-read (or a vendor statement of the alias's snapshot history) could address it.
- Interface effects cannot be separated from instrument, model and time effects in the stored seen record.

## Contacts

None (`contacts.md`). A listing that showed run-tag names only; no file of a hold-out or other-group run was opened (metadata under D31; the lead's step-1 decision 21).

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
