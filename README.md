# Bashar Index, Channeling Atlas and ET-channeler archive

This repository contains **three related research projects with separate datasets and build pipelines**: the original Bashar reference site, the cross-channel Channeling Atlas, and the ET-channeler discovery/collection project. They share public navigation; their people, uploads, recordings, documents and claims are different units and must not be added together.

**Start here:** [all dashboards](https://occult-kranti.github.io/bashar-index/dashboards/) · [branch inventory and history](BRANCHES.md) · [collection handoff](et-channelers/HANDOFF.md) · [future transcription/analysis plan](et-channelers/research/analysis-plan-2026-11-16/README.md).

Repository checkpoint: **17 November 2026, 00:45 UTC**. GitHub `main` is [`0ad27f0`](https://github.com/occult-kranti/bashar-index/commit/0ad27f0c52ebfdfcccd1e33421bd09f40fcc3a2a), including merged [PR #29](https://github.com/occult-kranti/bashar-index/pull/29). Current unmerged work is on `feat/browser-recovery-entity-directory`; see [BRANCHES.md](BRANCHES.md) for verified ancestry and worktrees. **New ASR, model downloads, embeddings and corpus-analysis jobs remain off.** Earlier results remain published; their presence does not mean a new analysis is running.

## The three research lanes

| Lane | Scope and dated denominator | Source and continuation |
|---|---|---|
| **Bashar Index** | September reference: **684 catalogued sessions/events (1984–2027), 75 AI-generated recording digests and 56 original diagram redrawings**. The catalogue and the 75-recording analysis are different samples. | [Root site](index.html), [data package](data/README.md), [digest schema](src/DIGEST_SPEC.md), [panel report](FINAL_REPORT.md), [analysis](analysis/README.md). |
| **Channeling Atlas** | Frozen **23 October 2026** release: **925 uploads**, 881 usable durations, 178 publishing groups with measured lengths and a **30-document English-caption pilot**. These are convenience-sample units, not 925 people or a census of channelers. | [Atlas handoff and roadmap](channeling-atlas/README.md), [analysis sources](channeling-atlas/research/analysis/README.md), [working paper](channeling-atlas/research/paper/README.md). Scientific baseline pinned at `bbe4801`. |
| **ET-channelers** | Historical October index: **92 people/group entries, 466 video rows (457 distinct IDs)**. Current local acquisition has a separate **71-channel / 66,446-ID listing snapshot**, including Dreemtime Academy. An indexed ID is not a downloaded recording or a transcript. | [Historical index provenance](et-channelers/README.md), [pipeline](et-channelers/pipeline/README.md), [current plan and evidence](et-channelers/research/analysis-plan-2026-11-16/README.md), [coverage tables](et-channelers/plan/coverage.csv). |

The September panel report, October Atlas paper and November prediction samples answer different questions using different evidence. Discovery relationships, uploader accounts, human speakers and attributed entities remain distinct. The [source-reviewed relationship table](et-channelers/research/analysis-plan-2026-11-16/channeler-entity-table.md) records **115 relationships for 28 people from 30 first-party pages**; it is a dated discovery batch, not a worldwide count or verification of the claimed phenomena.

The updated [Atlas entity directory](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/#/entities) exposes that separately dated relationship extension alongside the historical groups. [Dreemtime and common-event comparison](et-channelers/research/cross-channel-events-2026-11-16.md) documents channel intake and the future comparison roadmap. The [conditional collection ETA](et-channelers/research/collection-eta-2026-11-16.md) models about 8–17 active days for all indexed audio; current media refusals prevent a guaranteed finish date. [HANDOFF](et-channelers/HANDOFF.md) records the latest Chromium investigation and source state.

## Public interfaces

[Open the dashboard directory](https://occult-kranti.github.io/bashar-index/dashboards/). These six maintained repository interfaces share navigation and show their dataset dates.

| Interface | Public URL and purpose |
|---|---|
| Bashar Index | [Original reference and analysis](https://occult-kranti.github.io/bashar-index/) |
| Channeling Atlas | [People, attributed entities, sources and the October research edition](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/) |
| Atlas research report | [Frozen 925-upload analysis, figures and limitations](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/analysis/report.html) |
| Channeler YouTube index | [Searchable historical channel/video/playlist records](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/) |
| Collection monitor | [Newest-20 → newest-50 → remaining-archive snapshot](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/collection/) |
| Prediction timelines | [480 published candidates, target windows and guarded source evidence](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/predictions.html) |

Predictions are **candidates, not verified outcomes**. The collection monitor reads a committed, dated aggregate snapshot; it is not connected to a live process API. Updating navigation or styling does not refresh scientific data.

The [separately hosted Atlas](https://channeling-atlas.whatswrong-inc.chatgpt.site) retains its existing access settings and separate source/deployment history. Its source root corresponds to this repository's `channeling-atlas/`, not the whole repository. Earlier [Bashar](https://claude.ai/artifact/MF1hY9MYG95BaSqm9KXTFM), [YouTube index](https://claude.ai/artifact/XFQHVyn2WSk7Xnn4yXpAa8), [collection](https://claude.ai/artifact/898o4zpkocZ8qXjvR1xDfb) and [experiment](https://claude.ai/artifact/EXrUcxSotuWRW8NCaBHieY) Claude artifacts are historical copies whose access depends on sharing. They are not evidence that those copies have been refreshed.

## Current collection and deferred compute

The supported local YouTube lane saves **native audio plus sanitized metadata**, verifies the exact Drive objects and writes durable receipts before deleting local copies. It also saves available **English published captions and original English automatic captions**, including regional English variants; other languages and machine translations are excluded. Caption bundles retain raw response, timed segments, readable text and provenance. No picture download, audio re-encoding or ASR is part of this lane.

The requested order is **newest 20 per channel → extend to newest 50 → all indexed remainder**. The first two cohorts use the Videos tab; the remaining archive includes Videos, Shorts, recorded streams and legacy unknown-tab items. There is no duration filter. Newest-50 counts include newest-20 items and must not be added to them.

The [committed snapshot](et-channelers/plan/ingestion_status.json), generated **2026-11-17 01:14:46 UTC**, reports:

| Measure | Snapshot value |
|---|---:|
| Tracked channels / indexed unique video IDs | 71 / 66,446 |
| Newest-20 / inclusive newest-50 / remainder | 1,360 / 3,320 / 63,126 |
| Audio/metadata pairs verified on Drive | 47 |
| Verified English caption bundles | 20 |
| Videos with complete verified caption inventories | 15 |
| New local ASR/analysis jobs enabled | 0 |

These are the new local YouTube lane's counts, not totals for older podcasts, archive.org sessions, publisher texts or the Atlas. Its snapshot records a source cooldown; a one-file recovery does not establish universal access or ongoing successful downloading. Audio, caption and Drive endpoint deadlines remain separate. Use the [Windows/rclone operating guide](et-channelers/pipeline/WINDOWS_DRIVE.md), [caption methods](et-channelers/pipeline/YOUTUBE_CAPTIONS_RESEARCH.md) and [archive catalog guide](et-channelers/pipeline/ARCHIVE_CATALOG.md) for controls and recovery. Their older dated examples retain their original queue counts.

The allowance is **20 decimal GB local total, with 2 GB left unused**. The current private-root ceiling is **17 GB**, leaving room for tools and checkouts; those external project bytes still count. Future environments, model caches, incomplete downloads, decoded scratch and outputs must be budgeted too. The inspected machine has an **8 GB RTX 4070 Laptop GPU**, not a 16 GB GPU. Downloads are network/I/O work. Future CUDA inference will use one GPU owner and a **soft 70% rolling utilization target**, not a promised instantaneous ceiling.

Parallel ASR is deferred until shared interprocess reservations, deletion-aware leases, bounded artifact reading, versioned spans and CUDA/quality tests exist. The old transcriber is retained code, not the current launch path. The [disabled implementation plan](et-channelers/research/analysis-plan-2026-11-16/implementation-plan.json) and [illustrative search lexicon](et-channelers/research/analysis-plan-2026-11-16/search-lexicon.json) make that boundary explicit. The consolidated sample register supersedes older proposals: 30 development works, an 80-work weighted extraction test with at most eight windows per work, and a separate 6-development/18-held-out ASR calibration study. No sample has been executed by that plan.

## Public repository, private working data and archives

| Location | What belongs there |
|---|---|
| **This public GitHub repository** | Code, public source metadata, dated aggregate tables, original summaries/diagrams, guarded excerpts, methods, frozen derivatives, figures and review receipts. |
| **Local private root** (`$env:USERPROFILE\et-channelers-private` in the Windows guide) | Media/metadata spool, caption bundles, complete transcripts, exact queues, journals, receipts, locks and supervisor state, outside Git. |
| **Local tools** (`$env:USERPROFILE\et-channelers-tools`) | Isolated Python tooling, rclone, source/JavaScript helpers and local QA artifacts. Tool bytes count toward the allowance. Credentials remain in private configuration. |
| **Owner's Google Drive archive** | Verified source objects, transcripts/caption bundles, immutable catalog checkpoints and derived archive artifacts. The 20 GB limit is local; it is not a 20 GB Drive cap. |
| **Historical private GitHub archive** | `occult-kranti/et-channelers-archive`, with earlier release bundles and text volumes, separate from the new direct-to-Drive lane. |

The historical private releases `archive-v1`, `archiveshelf-podcast-audio-v1` and `handoff-2026-11-14` preserve earlier audio/text bundles and state. At the **14 November** checkpoint they contained 64 assets/10.52 GB, 9 assets/0.6 GB and 7 assets/0.17 GB respectively. Those are historical release figures, not a fresh inventory. Drive's numbered areas are `01 Plans and reports`, `02 Tables`, `03 Transcripts`, `04 Audio`, `05 Analysis` and `06 Earlier work`; private receipts/catalogs map actual objects without publishing their identifiers.

Keep source-authored text, published captions, automatic captions and local ASR distinct. Verify exact objects before cleanup; retain authoritative Drive audio for later bounded retrieval. Never import a private repository's raw transcript history into this public repository. The [handoff](et-channelers/HANDOFF.md), [roadmap](et-channelers/ROADMAP.md) and [preserved work log](BRANCHES.md#preserved-historical-work-log) retain earlier archive history.

## Repository map and editing ownership

Ownership names the workstream responsible for a change, not independent human validation.

| Path | Source of truth / generated output | Responsible workstream |
|---|---|---|
| [`data/`](data/README.md), [`src/`](src/), [`index.html`](index.html) | Bashar research data and Python builder → original reference page. | Bashar reference/data |
| [`analysis/`](analysis/README.md), [`panel/`](panel/), [`FINAL_REPORT.md`](FINAL_REPORT.md) | Historical preregistered analysis, results and review history. | Bashar methods/review |
| [`channeling-atlas/dist/`](channeling-atlas/dist/), [`channeling-atlas/research/`](channeling-atlas/research/) | Maintained Atlas app; frozen October data, report/paper sources, figures and release receipts. | Atlas implementation/research |
| [`et-channelers/youtube-index/`](et-channelers/youtube-index/), [`et-channelers/dashboard/data/`](et-channelers/dashboard/data/) | Historical index and four committed dashboard CSVs. | Corpus/index |
| [`et-channelers/sources/`](et-channelers/sources/README.md), [`et-channelers/plan/`](et-channelers/plan/) | Source registry, public coverage/target tables and aggregate snapshots. | Collection/provenance |
| [`et-channelers/pipeline/`](et-channelers/pipeline/README.md) | Windows Drive lane, retained multi-lane/legacy tools and tests. | Collection/systems |
| [`et-channelers/dashboard/`](et-channelers/dashboard/), [`dashboards/`](dashboards/README.md), [`assets/`](assets/) | Public interfaces, templates/fragments and shared navigation. | UI/publication |
| [Research plan](et-channelers/research/analysis-plan-2026-11-16/README.md) | Two research rounds, third-round critiques, relationships and disabled configuration. | Research lead / identity / evaluation |
| [`.claude/agents/`](.claude/agents/) | Earlier role definitions for collection, discovery, reading and review. Their presence does not launch jobs. | Historical orchestration |
| [`BRANCHES.md`](BRANCHES.md), [workflow](.github/workflows/dashboard-checks.yml) | Branch/PR provenance and CI checks. | Integration/review |

Current collection entrypoints are `start_drive_ingest.ps1` (stages), `supervise_drive_ingest.ps1` (single-instance bounded retries), `drive_ingest.py` (budget/transfers/receipts), `youtube_captions.py` and `media_metadata.py` (caption/metadata handling), `archive_catalog.py` (immutable checkpoints), and `ingestion_status.py` (allowlisted export), all under `et-channelers/pipeline/`. `prepare_all_queue.py` and `prepare_collection_stages.py` prepare merged/staged queues. Building or testing is separate from launching a collector.

## Generation and verification entrypoints

Serve a local preview from the repository root:

```text
python -m http.server 8765
```

Open `http://localhost:8765/dashboards/`. Most dashboards need HTTP for data requests; the embedded historical channel index also works as a standalone file.

| Generated artifact | Entry point / constraint |
|---|---|
| Bashar root page | `src/build.py`; `src/topics.py` is the historical analysis generator. Both retain original machine-specific path assumptions. Port paths deliberately; do not blindly overwrite a reviewed snapshot. |
| Channeler index | `et-channelers/pipeline/dashboard_index.py` embeds four `dashboard/data/*.csv` files into `index.template.html` → `index.html`, preserving dates and hashes. |
| Collection page | `et-channelers/pipeline/dashboard_local.py` wraps `dashboard/collection/page.fragment.html` → `dashboard/collection/index.html`. |
| Collection snapshot | `et-channelers/pipeline/ingestion_status.py` exports allowlisted private-state aggregates to `et-channelers/plan/ingestion_status.json`; [exact command](dashboards/README.md). |
| Prediction page | `et-channelers/pipeline/prediction_page.py --refresh-public et-channelers/dashboard/predictions.html` changes presentation only. New evidence requires the private-corpus build and full guard. |
| Atlas app / report / paper | App maintained in `channeling-atlas/dist/`; report generator `channeling-atlas/research/analysis/build_report.py`; [paper build instructions](channeling-atlas/research/paper/README.md). Preserve October pins unless producing a new scientific edition. |

See [dashboard build/review instructions](dashboards/README.md) for complete commands. The older Atlas handoff mentions `research/validate.py` and `research/validate_discovery.py`; those files are absent from this GitHub checkout and are not currently runnable checks. GitHub and the separately hosted Site have different roots.

The [CI workflow](.github/workflows/dashboard-checks.yml) defines routine checks. From the repository root:

```text
python -m unittest discover -s et-channelers/pipeline/tests -v
python et-channelers/scripts/guard_no_raw_media.py
python et-channelers/scripts/check_counts.py
node --check assets/research-nav.js
node --check dashboards/hub.js
node --check channeling-atlas/dist/app.js
```

CI runs the full suite on Linux with its declared environment. Windows also has targeted supervisor/native-process fixtures; some Unix/platform fixtures are not portable. Inspect skips and run checks appropriate to the changed component. The public guard supports `--staged` and `--paths` for scoped review. Offline tests do not prove successful source access or upload.

Collection-only dependencies are in [`requirements-download.txt`](et-channelers/pipeline/requirements-download.txt); rclone is separate. The older broad [`requirements.txt`](et-channelers/pipeline/requirements.txt) includes ASR dependencies and is not an instruction to install them for this lane. Local helper setup, source/client behavior, quota handling and restart controls belong in [WINDOWS_DRIVE.md](et-channelers/pipeline/WINDOWS_DRIVE.md).

## Publication and interpretation safeguards

- Raw media, full caption/transcript dumps, private contacts, credentials, signed transport URLs and private working ledgers stay out of this repository. Run the media/credential guard before publication; an ignore rule is not permission to publish a secret.
- Bashar digests are AI-written summaries, not transcripts. Quotes are limited to 30 words and link to recordings. Diagrams are original redrawings with confidence grades; no handout artwork is reproduced.
- Prediction publication additionally enforces per-item quotation share and per-person caps, speaker/contact/path checks and comparison with private source texts. A presentation refresh preserves exact published records and inherits the earlier share audit; it cannot recompute the 5% denominator without the private catalogue.
- Re-upload dates are unreliable and flagged or excluded from date-based views. Recorded date, upload date, target date, missingness and coverage remain distinct.
- Agent agreement, self-description, a regex hit, a topic cluster or a quoted measurement claim is not human validation or proof of truth. Host/guest identity, entity attribution, physical frequency and metaphor require separate evidence. Skeptical coverage remains part of the project.
- Preserve immutable editions and original review receipts. An interface change does not certify changed scientific data or imply that an older review covers it.

## Not affiliated

This project is not affiliated with, endorsed by or connected to Bashar Communications, Inc. or Darryl Anka. Bashar® recordings, transcripts and handouts are © Darryl Anka / Bashar Communications, Inc.; full recordings/transcripts and handout artwork are not reproduced here. Original code and derived research material are released under the [MIT License](LICENSE), subject to third-party rights.
