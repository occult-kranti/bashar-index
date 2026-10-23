# Channeling Atlas

## Current analytical release — 23 October 2026

The analysis merges the original atlas with the supplied Claude archive: **925 unique uploads**, **881 usable durations**, **178 publishing groups with measured lengths**, and a **30-document English-caption pilot**. These are convenience-sample records, not counts of unique or currently active human mediums. The historical discovery and service-audit layers described below remain available.

- Interactive per-account duration tables, titles, captions and learned embeddings: `#/analysis`.
- Source-linked report: `dist/analysis/report.html`.
- Complete working paper: `dist/analysis/channeling-atlas-paper.pdf`.
- Importable LaTeX source: `dist/analysis/channeling-atlas-overleaf.zip`.
- Data/code and first three review rounds: `research/analysis/`.
- Paper source, 28-source scholarly register, generated figures, three further review rounds and update protocol: `research/paper/`.

The dashboard analysis was published before paper work began. The manuscript uses the official AAAI 2027 preprint template and marks human authorship, construct validation, institutional ethics determination and checklist completion as TBD. It has not been submitted.

## Earlier atlas and discovery layers

A static research website with 26 public practitioner/lineage profiles, 49 documentary timeline entries, 190 source records and 14 selected community discussions. The expanded YouTube index contains 25 account records and 58 unique videos; the earlier 14 video/channel/catalog routes remain available. Original profile/activity cutoff: October 22, 2026. Deep-discovery expansion checked October 23, 2026.

The October 23 expansion contains 873 unique linked records: 482 videos, 169 playlists, 157 account routes and 65 websites, grouped under 106 practitioner/lineage/partial-name records. It includes the complete extracted YouTube-link metadata from the pinned `occult-kranti/bashar-index` repository plus manual browser searches and species-led web discovery. Explicit account aliases are merged; unresolved aliases remain visible. The 191 search/seed entries include failed Exa requests, not 191 successful source reviews.

`#/discovery` is the main expanded index. `dist/exports/channeling-research-csv.zip` includes master and type-specific CSVs, a person/practice table, query ledger, provenance summary, upstream MIT license, unresolved-attribution links and 106 individual files under `by-channeler/`. These entries include historical lineages, partial names, possible aliases, narrators, music/light-language and non-ET guide context; they are not a unique-human or annual-active census.

Ra is the central entry point. The earlier-history timeline includes Spiritualism, Theosophy, Alice Bailey, Van Tassel's Ashtar material and Seth. Featured contemporary profiles are Darryl Anka / Bashar, Athina Król / Ashtar and Tyler Ellison / Ryokah.

## Content boundaries

A source record documents an attributed claim and how its text or metadata was accessed. It does not validate extraterrestrial origins, spiritual identities or medical/financial outcomes. The public-source sample is curated, not exhaustive. YouTube access levels and source-date conflicts are retained. Private communications, closed groups and paid recordings were not accessed.

The comparison groups are editorial categories, not astronomical maps or verified species. Shared names do not establish shared origins or direct influence. Predictions remain in a separate forecast register rather than appearing as future historical occurrences.

The annual activity window is October 22, 2025–October 22, 2026. The reviewed sample supports 13 distinct named humans with dated ET-associated material, including messages, recordings and channeling-related interviews. It is a confirmed minimum within the sample, not a worldwide census or a count limited to new YouTube performances. The Elan project has January 2026 material, but the cited exchange does not identify its human channeler; it remains unconfirmed outside the named-human count.

Service audits cover 14 contemporary ET-associated candidates, including Elan. Five have verified future public session dates and one has a displayed future private opening. Displayed prices, currency uncertainty, free replays, paid live access and private booking availability are distinguished. The schedule uses the late-evening October 22, 2026 New York cutoff; an offer is not evidence that a session occurred, and an undated or stale listing is not a confirmed future date.

## Files and reproducibility

- `dist/`: published buildless HTML, CSS, JavaScript and JSON.
- `research/*.json`: bounded source-led workstreams, including source-access notes.
- `research/deep/*.json`: source/query-led discovery workstreams; `repo_raw/` retains the pinned input audit and upstream license.
- `research/extend_discovery.py`: deduplicates media IDs and explicitly linked account aliases, retains provenance, and generates CSVs/ZIP.
- `research/validate_discovery.py`: checks URL/media identity, source trails, practitioner links, every CSV and archive integrity.
- `research/youtube/*.json`: YouTube accounts, individual videos, annual activity evidence and supplementary service audits.
- `research/compile.py`: deduplicates and compiles the published dataset with editorial synthesis.
- `research/extend_youtube.py`: merges the expanded index, dated activity checks and service audits into the compiled dataset.
- `research/validate.py`: validates references, source identity, chronology, required caveats and named profile anchors.

Run `python3 research/compile.py`, `python3 research/validate.py` `python3 research/validate_discovery.py` and `node --check dist/app.js` after relevant changes. Serve `dist/` for local development. Hosted configuration is in `.openai/hosting.json` and must retain the existing Site identity.

## Verification

Research data validation checks all source and profile references and keeps anticipated occurrences outside the documentary timeline. Independent editorial checks of the initial profiles and the current activity/service update found no blocking count, date, attribution or currency issue. Initial browser checks and their limits are preserved in `research/qa.md`; the expanded index, session filters, chart navigation, detail records and CSV exports also passed rendered-browser checks. A separate narrow-viewport browser run was unavailable.
