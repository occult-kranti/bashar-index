# Research dashboards

The public [directory](https://occult-kranti.github.io/bashar-index/dashboards/) links all six maintained repository dashboards. Shared navigation lives in `assets/research-nav.{css,js}`. Links resolve from the asset URL so they work locally and beneath the GitHub Pages project prefix. A separately hosted copy can set the script's `data-root` to the public project URL.

## Rebuilding from the repository root

```powershell
python et-channelers/pipeline/prediction_page.py --refresh-public et-channelers/dashboard/predictions.html
python et-channelers/pipeline/dashboard_index.py
python et-channelers/pipeline/dashboard_local.py --fragment et-channelers/dashboard/collection/page.fragment.html --out et-channelers/dashboard/collection/index.html
```

The prediction refresh preserves the exact published JSON, quotation blocks and original build date. It does not recompute the 5% item-share limit without the original private catalogue; that limit is inherited from the unchanged, previously guarded records. Use the normal private-corpus build for new evidence. The channel index embeds the four committed CSV datasets with their SHA-256 hashes and original observation dates; `index.claude-fragment.html` preserves the earlier artifact.

The collection monitor and directory read a **published snapshot**, not a live process API. To export fresh aggregate counts:

```powershell
python et-channelers/pipeline/ingestion_status.py --root "$env:USERPROFILE/et-channelers-private" --out et-channelers/plan/ingestion_status.json
```

The exporter uses an explicit allowlist. It emits no titles, video IDs, contacts, local paths, media or raw errors. An expired cooldown is labeled ready to resume; it is not evidence that a worker is running. Newest-50 counts include the newest-20 cohort. The remaining index is metadata coverage, not completed audio collection. The 17 GB private-root ceiling reserves up to 1 GB for tools and repositories plus the owner's requested 2 GB buffer beneath the 20 GB total limit. Source and Drive cooldowns are labeled separately.

The original Bashar builder and report builder also include the shared navigation. The Bashar builder retains historical machine-specific input paths; this interface refresh updates its template and the published artifact without rerunning its research analysis. The Atlas application is maintained directly in `channeling-atlas/dist/`. Scientific release files, hashes and old review receipts remain tied to their October release.

## Interface review

The 16 November update uses ivory surfaces, forest accents, editorial headings and compact data controls. The prediction chart and filters are placed before the detailed methodology; source evidence remains adjacent to the chart on wide screens and accessible in the mobile reader. Every dashboard has a direct route to the directory. Historical Claude artifacts remain linked and explicitly labeled as earlier copies.

Browser review covers desktop and 320/390 px layouts, keyboard navigation, search, filtering, sorting, empty states, source links, mobile menus and prediction detail/fullscreen flows. Screenshots and local QA receipts are kept outside the public repository. Targeted automated tests cover the public-record identity guard, snapshot privacy, accessible color tokens and generator behavior.

Serve the repository with `python -m http.server 8765` and open `http://localhost:8765/dashboards/` for local review. The historical channel index also works directly from a file; the other dashboards should be served over HTTP for their data requests.
