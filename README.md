# Bashar Index, Channeling Atlas and ET-channeler archive

## Start here

The project archives audio and metadata from channeling creators and publishes source-backed research. The latest-20 selection contains **1,976 public regular uploads across 101 channels**. At 22:51 UTC on November 19, Drive held **1,784 verified recordings**. Sixty-seven creators had complete coverage, and 192 recordings remained. The active Windows collector reached six source workers and eight outstanding recordings, with three Drive file transfers, a 23 GB working-file allowance and a 12 GB disk reserve. The larger catalog retains Shorts and streams. [Collection process and concurrency](et-channelers/pipeline/COLLECTION_PROCESS.md) · [Dashboard hub](dashboards/)

For data collection, start with the Windows handoff and the pipeline guide. For the study, start with the research plan, reviewed channeler–entity table and event register. Branch history records which work has reached the public site. [Handoff](et-channelers/HANDOFF.md) · [Pipeline](et-channelers/pipeline/README.md) · [Analysis plan](et-channelers/research/analysis-plan-2026-11-16/README.md) · [Source relationships](et-channelers/research/analysis-plan-2026-11-16/channeler-entity-table.md) · [Shared events](et-channelers/research/cross-channel-events-2026-11-16.md) · [Branches](BRANCHES.md)

**Latest-50 audio is scheduled after latest-20+ translation and both analysis rounds.** Allow about **22–28 hours from its eventual start** at the measured 100.6 verified recordings per hour. Channel growth, source availability and transfer rates can change that estimate. The Windows archive stores the dependency so a restart preserves the order. [Forecast and release conditions](et-channelers/pipeline/COLLECTION_PROCESS.md#latest-50-forecast)

<details>
<summary>Earlier receipt checkpoints for the 74-channel collection</summary>

**Receipt checkpoint, 19 November 2026, 04:15 UTC:** public `main` is `7c6a860`; [PR #75](https://github.com/occult-kranti/bashar-index/pull/75) merged the streaming PURE receipt reader and Pages passed. Audio remains **1,151 / 1,420 selected videos: 1,108 native + 37 publisher editions + six qualified YouTube editions**. Saved-text coverage is **136**, **269** selected videos still lack audio, and the creator-level selection gap remains **60**. ASR remains paused.

The new 20-item qualified batch closed after **five submitted attempts: four local holds and one missing final result, with zero new saved pairs**. Owned jobs are closed and its 5 GB reservation is released. At the saved November 19, 04:15 UTC checkpoint, the corrected 15-item continuation is terminal: 11 submissions produced five paired editions, two item-specific source holds, three unpublished native-route handoffs and one missing final result; four targets were not started. Its outer owned process is closed and the matching 5 GB future-growth allocation is released. Handoffs and partial work add no saved-audio count. Separately, **96 rich metadata items / 43 remote archive objects / 12,045,840 uploaded bytes** add zero audio or text coverage in the owner's **ET Channelers Archive** on Google Drive. Overall completion ETA is unknown, and the qualified route has no representative end-to-end ETA calibration. Use the dated [activity and ETA dashboard](et-channelers/dashboard/collection/) and [acquisition checkpoint](et-channelers/research/acquisition-checkpoint-2026-11-19.md) for subsequent updates.

**Earlier receipt snapshot, 19 November, 01:50 UTC:** the dated receipt snapshot is **1,146 / 1,420 selected videos**: **1,108 native, 37 publisher editions and one track-unverified YouTube edition**, with 136 carrying saved text and 274 still missing audio. The first HE-AAC edition preserves all **17,543 AAC packets** from an already downloaded MP4 without re-encoding; original-track and spoken-language identity remain unverified. Separately, **32 rich metadata records** are Drive-verified and add no audio or text coverage. ASR remains paused. Start with the [current acquisition checkpoint and dashboard links](et-channelers/research/acquisition-checkpoint-2026-11-19.md) and [branch register](BRANCHES.md).

**Collection update, 18 November 2026, 22:29 UTC:** the latest 14-item native-audio batch closed after **13 verified audio/metadata archives and one hold in 539.12 seconds**. Its two download workers overlapped a separate uploader; owned jobs are closed and its 4.8 GB reservation is released. The preceding 253-item Source6 batch added 208 paired archives and closed at 21:13 UTC. Use the timestamped [download/activity dashboard](et-channelers/dashboard/collection/), [saved-video CSV](et-channelers/plan/downloaded_videos.csv) and [conditional ETA](et-channelers/dashboard/collection/#collection-eta) for aggregate receipt counts and current jobs. ASR remains paused. Completing a batch does not complete the latest-20 goal; unresolved formats, actual access refusals and catalog gaps still require further work.

The goal is **20 audio items for each of 74 creators**, or 1,480 slots; the frozen 1,420-row Videos-tab selection does not satisfy it. Five creator selections are underfilled. Cached Shorts/stream candidates add 19 possible rows, awaiting metadata/completion review and separate admission, leaving 41 selection slots unresolved even if all qualify. Verified all-tabs listings and the Aluna backup/main-channel identity review are required; no duration cutoff excludes Shorts. See the [scope gap and next steps](et-channelers/ROADMAP.md#twenty-audio-items-for-each-creator).

The [portable implementation](et-channelers/pipeline/native_bulk/README.md) mirrors the corrected Source6 scheduler/adapter, including full static reservations, immediate shared fatal-stop signaling and actual callback ownership through closure. Metadata-first admission and selected-size MediaGO remain [isolated future components](et-channelers/research/native-admission-budget-prototype-2026-11-18.md). The first durable frame report separates copy, stat, finalization and partition timing; these overlapping intervals are not exclusive wall-time shares. The [round-4 panel](et-channelers/research/batch-download-panel-round4-2026-11-18.md) and [handoff](et-channelers/HANDOFF.md) preserve the preceding evidence.

The [upload-date timeline](et-channelers/dashboard/collection/timeline.html) accounts for all **1,420 selected videos / 74 creators: 581 exact metadata dates, 838 estimates and one unknown**. It preserves original estimates alongside exact overrides and offers row-level CSV/JSON exports. This is a capped selected sample, not each creator's complete production history. The channel table also exports a separate creator activity CSV; [state definitions](et-channelers/README.md#download-activity-and-date-exports) explain its mutually exclusive partitions.

This repository contains **three related research projects with separate datasets and build pipelines**: the original Bashar reference site, the cross-channel Channeling Atlas, and the ET-channeler discovery/collection project. They share public navigation; their people, uploads, recordings, documents and claims are different units and must not be added together.

Audio coverage also distinguishes [qualified YouTube editions](et-channelers/research/qualified-audio-editions-2026-11-18.md): a paired, verified audio extract can contribute to the selected-video total while its original track and spoken language remain unverified. It is labeled separately from native and publisher audio and adds no caption or transcription completion.

**Start here:** [all dashboards](https://occult-kranti.github.io/bashar-index/dashboards/) · [branch inventory and history](BRANCHES.md) · [collection handoff](et-channelers/HANDOFF.md) · [future transcription/analysis plan](et-channelers/research/analysis-plan-2026-11-16/README.md).

Historical repository guide checkpoint: **18 November 2026, 00:05:09 UTC**. [PR #38](https://github.com/occult-kranti/bashar-index/pull/38) merged as `f1e4f11`; its exact head passed 1,356 Python tests with 47 skips and all 86 Node tests. Pages deployed and seven public routes returned 200. Branch `feat/native-upload-overlap` is retained; continuation is `feat/decoded-native-audio-formats`. **128 native audio/metadata pairs and 77 native-source ASR bundles** are Drive-verified. Including qualified publisher editions, latest-20 coverage is **156 audio entries / 122 with an audio edition and saved text**. The admitted 40-target continuation and separate 42-input English consumer are running at this dated snapshot. A strict decoded-DRC policy recovered one complete native AAC file without re-encoding. Accuracy and publisher-edition equivalence remain unreviewed; scientific corpus analysis is deferred.

</details>

## The three research lanes

| Lane | Scope and dated denominator | Source and continuation |
|---|---|---|
| **Bashar Index** | September reference: **684 catalogued sessions/events (1984–2027), 75 AI-generated recording digests and 56 original diagram redrawings**. The catalogue and the 75-recording analysis are different samples. | [Root site](index.html), [data package](data/README.md), [digest schema](src/DIGEST_SPEC.md), [panel report](FINAL_REPORT.md), [analysis](analysis/README.md). |
| **Channeling Atlas** | Frozen **23 October 2026** release: **925 uploads**, 881 usable durations, 178 publishing groups with measured lengths and a **30-document English-caption pilot**. These are convenience-sample units, not 925 people or a census of channelers. | [Atlas handoff and roadmap](channeling-atlas/README.md), [analysis sources](channeling-atlas/research/analysis/README.md), [working paper](channeling-atlas/research/paper/README.md). Scientific baseline pinned at `bbe4801`. |
| **ET-channelers** | Historical October index: **92 people/group entries, 466 video rows (457 distinct IDs)**. Current acquisition has a separate **74-channel / 67,594-ID listing snapshot**, including Dreemtime Academy, Charlie Wilde, Infini Global and Odyssey of Ascension. An indexed ID is not a downloaded recording or a transcript. | [Historical index provenance](et-channelers/README.md), [pipeline](et-channelers/pipeline/README.md), [current plan and evidence](et-channelers/research/analysis-plan-2026-11-16/README.md), [coverage tables](et-channelers/plan/coverage.csv). |

The September panel report, October Atlas paper and November prediction samples answer different questions using different evidence. Discovery relationships, uploader accounts, human speakers and attributed entities remain distinct. The [source-reviewed relationship table](et-channelers/research/analysis-plan-2026-11-16/channeler-entity-table.md) now records **119 relationships for 31 people**, including four additions supported by official biographies. This is a dated discovery batch, not a worldwide count or verification of the claimed phenomena. Infini Global's publisher identity remains separate from the speaker named in its uploads; the requested historical Bashar video remains a candidate pending performer evidence.

The updated [Atlas entity directory](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/#/entities) exposes that separately dated relationship extension alongside the historical groups. [Dreemtime and common-event comparison](et-channelers/research/cross-channel-events-2026-11-16.md) documents channel intake and the future comparison roadmap. The [updated conditional ETA](et-channelers/research/collection-eta-2026-11-17.md) distinguishes native transfer capacity from real-time browser capture. Current source refusals prevent a guaranteed finish date. [HANDOFF](et-channelers/HANDOFF.md) records the latest Chromium investigation and source state.

## Public interfaces

[Open the dashboard directory](https://occult-kranti.github.io/bashar-index/dashboards/). These nine current public routes include the directory and entity view alongside the repository interfaces. Each retains its own dataset date.

| Interface | Public URL and purpose |
|---|---|
| Bashar Index | [Original reference and analysis](https://occult-kranti.github.io/bashar-index/) |
| Channeling Atlas | [People, attributed entities, sources and the October research edition](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/) |
| Atlas research report | [Frozen 925-upload analysis, figures and limitations](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/analysis/report.html) |
| Channeler YouTube index | [Searchable historical channel/video/playlist records](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/) |
| Collection monitor | [Newest-20 → newest-50 → remaining-archive snapshot](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/collection/) |
| Selected-video upload timeline | [All 1,420 selected videos, with exact, estimated and unknown dates](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/collection/timeline.html) |
| Prediction timelines | [480 published candidates, target windows and guarded source evidence](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/predictions.html) |
| Dashboard directory | [All current public routes](https://occult-kranti.github.io/bashar-index/dashboards/) |
| Atlas entity directory | [People/entity relationships and source links](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/#/entities) |

Predictions are **candidates, not verified outcomes**. The collection monitor reads a committed, dated aggregate snapshot; it is not connected to a live process API. Updating navigation or styling does not refresh scientific data.

The [separately hosted Atlas](https://channeling-atlas.whatswrong-inc.chatgpt.site) retains its existing access settings and separate source/deployment history. Its source root corresponds to this repository's `channeling-atlas/`, not the whole repository. Earlier [Bashar](https://claude.ai/artifact/MF1hY9MYG95BaSqm9KXTFM), [YouTube index](https://claude.ai/artifact/XFQHVyn2WSk7Xnn4yXpAa8), [collection](https://claude.ai/artifact/898o4zpkocZ8qXjvR1xDfb) and [Frequency of a Place experiment](https://claude.ai/artifact/EXrUcxSotuWRW8NCaBHieY) Claude artifacts are historical copies whose access depends on sharing. They are not evidence that those copies have been refreshed.

## Collection methods and historical 00:05 UTC checkpoint

The quantities and running-consumer observations in this section belong to the earlier November 18 checkpoint. Current receipts, activity and ETA are linked above. ASR is paused; the 500 MB future-growth reservation has been released, while retained inputs and failed artifacts remain charged to actual storage.

The supported local YouTube lane saves **native audio plus sanitized metadata**, verifies the exact Drive objects and writes durable receipts before deleting local copies. It also saves available **English published captions and original English automatic captions**, including regional English variants; other languages and machine translations are excluded. Caption bundles retain raw response, timed segments, readable text and provenance. No picture download, audio re-encoding or ASR is part of this lane.

The November 18 and current November 19 regular-video samples use each channel’s newest-first Videos tab. Each sweep accepts public uploads of every duration and date. The next sweep extends the target to fifty, reuses previously saved recordings and preserves both dated selections when new uploads change the order. Shorts and streams remain separately indexed in the cumulative catalog. [Selection and queue procedure](et-channelers/pipeline/COLLECTION_PROCESS.md)

The [dated collection snapshot](et-channelers/plan/ingestion_status.json) reports acquisition and derived text separately. At this continuation checkpoint:

| Measure | Snapshot value |
|---|---:|
| Tracked channels / indexed unique video IDs | 74 / 67,594 |
| Newest-20 / inclusive newest-50 / remainder | 1,420 / 3,449 / 64,145 |
| Audio/metadata pairs verified on Drive | 128 |
| Verified English caption bundles | 20 |
| Videos with complete verified caption inventories | 15 |
| Archived native audio items with verified text available | 94; 77 ASR plus 17 with English captions, no overlap |
| Text-inventory completion / saved-caption review / no saved text | 92 / 2 / 34 |
| Native-source ASR videos verified on Drive | 77; accuracy unreviewed |
| Additional latest-20 publisher-written companions | 16; author-written source material, not verified spoken transcripts |
| Additional exact-ID publisher transcripts | 1; untimed, spoken coverage unverified |
| Additional publisher podcast audio editions | 2; source/edition association retained separately from native audio |
| Additional publisher mirror audio / English captions | 28 / 17; source editions and YouTube edit equivalence retained separately |
| Mirror-edition ASR/translation sources verified on Drive | 11; ten English editions plus German original and separate English translation |
| Publisher-edition ASR verified on Drive | 2; about 2.6 audio hours, accuracy and YouTube edit equivalence unreviewed |
| Deduplicated latest-20 audio / audio with saved text | 156 / 122; canonical and publisher source overlaps counted once |
| Additional publisher timed-text sources | 3; recording edition and manual/automatic origin unverified |
| Scientific corpus-analysis jobs | 0 |

These are the new local lane's counts, not totals for older podcasts, archive.org sessions, publisher texts or the Atlas. The dated snapshot proves the current source and ASR processes through their matching leases and process identities; the older collector remains parked. The 40-target continuation has 22 new canonical pairs at this snapshot: its first frame finished with 15 verified and 5 held, and its second frame is running. The earlier stopped series archived five items before its consumer failed; its remaining 40 targets had never started and require the explicit continuation amendment. Held assets and prior attempts stay preserved. The [measured ETA](et-channelers/research/collection-eta-2026-11-17.md) retains an 8 to 12 active-hour first-pass planning range from completed batches, conditional on similar source availability and backpressure. It is not a finish date for all held audio or transcripts. Use the [series guide](et-channelers/pipeline/NATIVE_SERIES.md) and [current handoff](et-channelers/HANDOFF.md) for recovery.

The allowance is **20 decimal GB local total, with 2 GB left unused**. The active phase uses a tighter **16 GB managed ceiling**, including tools, checkouts, models, inputs and outputs. At this historical checkpoint, source growth reserved 5.5 GB and a separate 500 MB allowance covered at most three staged English pairs. Six-root storage was **8,328,191,629 bytes (8.33 GB)**; reserved future growth was checked separately. CUDA inference permits one owner, a 6.5 GB VRAM ceiling and a **soft 70% rolling utilization target** on the 8 GB RTX 4070 Laptop GPU. Brief instantaneous readings reached 100%; this is not a hard utilization cap. The earlier English consumer ran one input per process and published each valid result immediately. One separate recording remained held after word-alignment and segment-timing failures; its inputs and failed attempts are retained.

The [leased CUDA worker](et-channelers/pipeline/GPU_ASR_SETUP.md) uses exact audio/model/environment proofs, versioned bundles and proof-before-release input leases. English transcripts and original-language/English translation views remain distinct from publisher captions. Automated transcription accuracy is unreviewed; successful storage verification does not establish accuracy. The old transcriber is retained code, not the current launch path. The [disabled scientific analysis plan](et-channelers/research/analysis-plan-2026-11-16/implementation-plan.json) and [illustrative search lexicon](et-channelers/research/analysis-plan-2026-11-16/search-lexicon.json) remain planning artifacts. Their separate 6-development/18-held-out ASR calibration study has not been executed by the acquisition batches.

The [experimental Chrome SABR helper](et-channelers/browser_capture_extension/README.md) retains its earlier partials and protection response. **Real-time capture remains parked.** The working automated route uses owned Chromium with the stock WPC provider and the full upstream yt-dlp HTTPS downloader. It transfers independently of playback, retains raw original-track evidence, validates full native extent and verifies paired Drive objects before retiring owned local files. Earlier source controls remain preserved; the working v4 executor has its own exact scope and durable item/global error policy. See [the panel record](et-channelers/research/native-transport-panel-2026-11-17/README.md) and [batch guide](et-channelers/pipeline/NATIVE_BATCH.md).

The official [uBlock Origin Lite installer and isolated Chromium factory](et-channelers/pipeline/BROWSER_ADBLOCK.md) passed a controlled local filtering/coexistence test. [Publisher recovery](et-channelers/research/publisher-mirrors-2026-11-17.md) covers 17 Magenta Pixie, ten Athina and one Pavlina edition. Their captions and ASR remain source-specific. The [decoded-DRC repair](et-channelers/research/decoded-native-audio-formats-2026-11-18.md) distinguishes a proven processing tag from semantic track labels before selecting only normal audio. One 10,339,840-byte AAC source passed strict packet/extent checks and exact paired Drive verification; unknown source language remains unknown. Item-bound HTTP 403s quarantine that item; unknown/control failures, provider 429s and protection checks stop the executor. The same durable refusal ledger survives batches and restarts.

The [caption-gap review](et-channelers/research/caption-gap-review-2026-11-17.md) reuses verified Drive audio and existing English captions. It decoded once per reviewed run while retaining only gap windows, then used 32.459 seconds of CUDA ASR input for a 75-minute source. Three of five candidate words already match adjacent captions; two remain unresolved. No missing words, full coverage or new completed transcript are claimed. The [reproducible worker and execution contract](et-channelers/pipeline/CAPTION_GAP_REVIEW.md) preserve original caption alternatives and separate unreviewed evidence.

The [held-audio review](et-channelers/research/held-audio-language-review-2026-11-17.md) fills the earlier sampled-VAD gaps, checks original channels, and examines the recording previously held on metadata alone. A light-language label is a review signal, not proof about every interval. [Language-ID review](et-channelers/pipeline/LANGUAGE_ID_REVIEW.md) keeps bounded model scores separate from lexical meaning, whole-recording language and full-ASR completion.

## Public repository, private working data and archives

| Location | What belongs there |
|---|---|
| **This public GitHub repository** | Code, public source metadata, dated aggregate tables, original summaries/diagrams, guarded excerpts, methods, frozen derivatives, figures and review receipts. |
| **Local private root** (`$env:USERPROFILE\et-channelers-private` in the Windows guide) | Media/metadata spool, caption bundles, complete transcripts, exact queues, journals, receipts, locks and supervisor state, outside Git. |
| **Local tools** (`$env:USERPROFILE\et-channelers-tools`) | Isolated Python tooling, rclone, source/JavaScript helpers and local QA artifacts. Tool bytes count toward the allowance. Credentials remain in private configuration. |
| **Owner's Google Drive: ET Channelers Archive** | Verified source objects, transcripts/caption bundles, immutable catalog checkpoints and derived archive artifacts. The 20 GB limit is local; it is not a 20 GB Drive cap. |
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
| Selected-video date timeline | `et-channelers/pipeline/dataset_timeline.py` reads the saved selection CSV, optional exact-date overlay and receipt-coverage CSV; it exports JSON, video/month CSVs and standalone HTML using a local Plotly bundle. No source request is made. |
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
