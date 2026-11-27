# Research dashboards

The public [directory](https://occult-kranti.github.io/bashar-index/dashboards/) links all eight maintained repository dashboards, including the [selected-video upload timeline](../et-channelers/dashboard/collection/timeline.html) and the [transcript findings](../et-channelers/dashboard/findings/). Shared navigation lives in `assets/research-nav.{css,js}`. Links resolve from the asset URL so they work locally and beneath the GitHub Pages project prefix. A separately hosted copy can set the script's `data-root` to the public project URL.

## Where the work stands, 20 November 2026

The frozen selection is the newest 20 public uploads on the Videos tab of each of 101 channeling mediums: 1,976 recordings (selection SHA-256 `adb76d392fa9eded77e03fb41687a630fb82a17fb3de21af504092710b08fd01`). The owner closed the download goal on 20 November: 1,946 recordings are archived with verified audio on Drive, and the other 30 are final failures that are not retried. The local speech-to-text run finished at 19:56 UTC the same day: 1,697 of 1,729 audio files, 742.9 hours and 5.83 million words in seven languages; 12.6% of the audio holds no speech. Analysis is under way. The [analysis handoff](../et-channelers/knowledge-transfer/analysis-handoff-2026-11-20.md) has the details and the [findings dashboard](../et-channelers/dashboard/findings/) the published counts.

The directory's collection strip and the state and banner of the [collection dashboard](../et-channelers/dashboard/collection/) read `et-channelers/plan/collection_state.json`. The collection dashboard keeps the last receipt checkpoint of the open collection (19 November, the earlier 74-channel queue) below it as an earlier checkpoint, with its date.

## Daily edition and operating data

The current [daily publication timeline](../et-channelers/dashboard/collection/timeline.html?date=2026-11-16) covers all 1,976 selected regular recordings. Of these, 1,579 carry an exact day from date-stamped metadata; the other 397 carry estimated windows, eight of which fall on a single day. Its 6,724 calendar rows therefore distinguish 1,587 recordings assignable to a day from the 389 with wider windows. Use the [daily CSV](../et-channelers/dashboard/collection/dates-by-day.csv), the [recording-level CSV](../et-channelers/dashboard/collection/recording-dates.csv) or the [generator and date-evidence guide](../et-channelers/research/recording-dates-2026-11-19.md) for this edition. In the recording-level CSV, the 36 video IDs that begin with a hyphen are written with a leading apostrophe so that spreadsheets do not read them as formulas; strip it on read, and every ID then matches the selection. The [knowledge-transfer folder](../et-channelers/knowledge-transfer/) links the latest dated creator and recording counts, the failed-link dashboard and historical site versions.

## Rebuilding from the repository root

```powershell
python et-channelers/pipeline/prediction_page.py --refresh-public et-channelers/dashboard/predictions.html
python et-channelers/pipeline/dashboard_index.py
python -I et-channelers/pipeline/collection_state.py --decision PRIVATE_RUN_FOLDER/download-goal-closed.json --out et-channelers/plan/collection_state.json
python et-channelers/pipeline/dashboard_local.py --fragment et-channelers/dashboard/collection/page.fragment.html --out et-channelers/dashboard/collection/index.html
```

The prediction refresh preserves the exact published JSON, quotation blocks and original build date. It does not recompute the 5% item-share limit without the original private catalogue; that limit is inherited from the unchanged, previously guarded records. Use the normal private-corpus build for new evidence. The channel index embeds the five committed CSV datasets with their SHA-256 hashes and original observation dates; `index.claude-fragment.html` preserves the earlier artifact.

The collection state joins the owner's decision record that closed the download goal (`download-goal-closed.json` in the private run folder named in the [analysis handoff](../et-channelers/knowledge-transfer/analysis-handoff-2026-11-20.md)) with the committed [evidence of the close](../et-channelers/knowledge-transfer/evidence/2026-11-20-close/) and the committed [tables of the transcription run](../et-channelers/research/transcription-run-2026-11-20/tables/). It copies only the decision's date, its counts and its SHA-256, never the recordings it lists, and refuses to write when the decision, the receipt checkpoint, the Drive verification, the failed-links table (bound to the decision by hash) and the run tables disagree. `python -I et-channelers/pipeline/collection_state.py --check et-channelers/plan/collection_state.json` confirms a published state against the public evidence without the private file.

The receipt checkpoint below the collection state is a **published snapshot**, not a live process API. It describes the open collection and was last exported on 19 November. To export fresh aggregate counts:

```powershell
python et-channelers/pipeline/ingestion_status.py --root "$env:USERPROFILE/et-channelers-private" --out et-channelers/plan/ingestion_status.json
```

The status exporter uses an explicit allowlist. It emits no titles, video IDs, contacts, local paths, media or raw errors. An expired cooldown is labeled ready to resume; it is not evidence that a worker is running. Newest-50 counts include the newest-20 cohort. The remaining index is metadata coverage, not completed audio collection. The current phase uses a stricter 16 GB managed ceiling across private data, tools, browser assets and checkouts, beneath the owner's 20 GB allowance with a 2 GB buffer. Supply each additional accounted root with `--managed-root PATH`; the private root is included automatically. Source and Drive cooldowns are labeled separately.

The separate `collection_coverage.py` exporter publishes per-creator receipt counts, a public saved-video inventory and a six-state activity partition. Its table offers a creator activity CSV. These public titles and IDs are intentionally distinct from the status export's aggregate-only schema. See [activity definitions](../et-channelers/README.md#download-activity-and-date-exports). The final outcome of each of the 101 creators at the close is in the evidence folder's `creator-status.csv`.

The current upload timeline is rendered offline by `pipeline/collection_metadata_timeline.py` from the date report described in the [date-evidence guide](../et-channelers/research/recording-dates-2026-11-19.md). The older timeline builder reads local saved metadata for the earlier 1,420-video, 74-creator selection and makes no source or Drive request:

```powershell
python -I et-channelers/pipeline/dataset_timeline.py --queue PATH_TO_SAVED_SELECTION.csv --exact-dates PATH_TO_SAVED_DATE_OVERLAY.json --coverage-csv et-channelers/plan/downloaded_videos.csv --out-dir et-channelers/dashboard/collection --template et-channelers/dashboard/collection/timeline.template.html --plotly-js PATH_TO_LOCAL_PLOTLY_CARTESIAN_4_1_1.js --expected-videos 1420 --expected-creators 74
```

That earlier date sample (`dataset_timeline.json`) contains 581 exact metadata dates, 838 estimates and one unknown. Original estimates and safe provenance remain in the exports; capped creator windows do not measure total production.

The original Bashar builder and report builder also include the shared navigation. The Bashar builder retains historical machine-specific input paths; this interface refresh updates its template and the published artifact without rerunning its research analysis. The Atlas application is maintained directly in `channeling-atlas/dist/`. Scientific release files, hashes and old review receipts remain tied to their October release.

## Interface review

The 16 November update uses ivory surfaces, forest accents, editorial headings and compact data controls. The prediction chart and filters are placed before the detailed methodology; source evidence remains adjacent to the chart on wide screens and accessible in the mobile reader. Every dashboard has a direct route to the directory. Historical Claude artifacts remain linked and explicitly labeled as earlier copies.

The 20 November update states the closed collection and the finished transcription run in the directory's plan, strip and rows, describes the transcript findings row by what that dashboard now holds, and gives the collection dashboard a banner and state read from the collection record, with links to the findings dashboard and the analysis handoff.

Browser review covers desktop and 320/390 px layouts, keyboard navigation, search, filtering, sorting, empty states, source links, mobile menus and prediction detail/fullscreen flows. Screenshots and local QA receipts are kept outside the public repository. Targeted automated tests cover the public-record identity guard, snapshot privacy, the collection state's joins, accessible color tokens and generator behavior.

Serve the repository with `python -m http.server 8765` and open `http://localhost:8765/dashboards/` for local review. The historical channel index and standalone timeline also work directly from a file; the other dashboards should be served over HTTP for their data requests.
