# Measured collection ETA: 18 November 2026

## Latest checkpoint, 07:04 UTC

Receipts confirm **321/1,420 audio entries**: 287 native YouTube pairs and 34 additional publisher editions. Of these, 136 have saved text; native ASR remains 91 and is paused by owner instruction. The actual bound process for a **1,046-item / 53-frame** cohort was confirmed running, with two source workers and one publisher. Two frames / 40 decisions have closed, leaving 1,006 first-pass decisions. The [channel table](../dashboard/collection/#channel-downloads) and [saved-video CSV](../plan/downloaded_videos.csv) preserve deduplicated coverage and edition labels.

The calibration download-only 20-decision run took **435.239216 seconds**, including startup, metadata, source transfer, upload and closure. It archived 15 pairs totaling 347,194,262 audio bytes; five decisions were local format holds. This supersedes the older source-plus-ASR-backpressure calibration below for the current download-only workload. The remaining first-pass calculation is `1006 * 435.239216 / 20 / 3600 = 6.0813` active hours. A stated 1–2x planning allowance gives **6.1–12.2 active hours**, including decisions that may be held. It is not a statistical interval or a finish date for all missing audio and text. Downtime, different source lengths, refusals and unavailable formats can extend calendar time.

This cohort excludes all actual or uncertain attempts from its predecessors. Their HTTP history and quarantines are preserved; a bound selected-asset 403 in the last cohort was followed by strict successful full transfers, leaving no global circuit at admission. A measured parent deadline can now quarantine one item through a separate parent-censored record without inventing worker success or resetting HTTP history. Unknown failures and global controls still stop work. See the [optimization panel](download-optimization-panel-2026-11-18.md) for implementation and alternatives.

Managed actual usage was **8.40 GB** in this snapshot. At atomic admission, actual bytes, other active reservations, the new 5.5 GB growth reservation and journal headroom totaled **15.729 GB**, below the 16 GB accounting cap; physical spare was also checked. ASR is not included in the active batch. Public status and ETA are saved checkpoints, not live worker polling.

For current ETA refreshes, pass `--service-live TERMINAL_DIRECT_RUN --service-direct` instead of the historical series baseline. The exporter derives the admitted finite scope from process-bound bulk status. Refreshing generated coverage/status/ETA JSON and CSV files requires consistency checks; full Python tests remain required for code changes.

## Historical checkpoint, 02:41 UTC

Coverage checkpoint: **2026-11-18T02:41:58Z**. Estimate generated **2026-11-18T02:44:22Z**. The [collection dashboard](../dashboard/collection/#collection-eta) reads [aggregate status](../plan/ingestion_status.json) and [the machine-readable estimate](../plan/collection_eta.json). Both files are saved checkpoints. Loading the page fetches those files; it does not contact or continuously poll a source worker.

## Historical scope and coverage

| Measure | Saved proof count |
|---|---:|
| Channels / newest-20 target entries | 74 / 1,420 |
| Native audio + metadata pairs | 164 |
| Native ASR bundles | 85 |
| Deduplicated entries with audio from any verified source | 192 |
| Audio edition with saved text | 130 |
| Native recordings with saved text / complete inventory / partial captions | 102 / 100 / 2 |
| Native recordings without saved text | 62 |
| English caption tracks / videos / complete inventories | 20 / 17 / 15 |

Publisher mirrors (28), old podcast variants (2) and independent publisher timed-text sources (3) keep their own source/edition labels. Overlapping editions do not increase the deduplicated audio count. Saved captions and ASR do not establish every-word accuracy or exact YouTube-edit equivalence. The newest-50 tier is 3,449 inclusive entries and the full index is 67,594; their full acquisition is outside this first-pass ETA.

The recovery plan is **terminal: 27 verified / 30 decisions, three held, zero pending**. The separately admitted **600-item / 30-frame** first-pass cohort was confirmed running at the checkpoint; **553 later candidates remain prepared and disabled**. No drained campaign frame had been recorded yet, although individual canonical pairs can already be verified during a frame. This is a finite 12-hour admission, not a guarantee that every item finishes within it. GPU transcription is separate; this source campaign has no ASR handoff.

## Measured service and conditional scenarios

| Completed scope | Elapsed service | Verified pairs | Native audio bytes |
|---|---:|---:|---:|
| 40-decision source continuation | 1581.878479 s (26.36 min) | 30 | 743,607,049 |
| Recovery frames, 10 + 20 decisions | 710.773301 s in the two source processes | 27 | 631,810,685 |
| Recovery first invocation through final exit | 887.931620 s including interframe admission | same 27 | same bytes |

The 40-decision run includes startup, source/metadata work, upload, frame gates and initial ASR-stage backpressure. Its immediate success fraction is **75%**, and its end-to-end decision rate is **91.03/hour**. This is service timing, not isolated download/upload bandwidth. It supersedes the earlier 8-12 active-hour range that included a faster failing workload. The recovery run's 90% immediate success is a different, selected workload and does not replace the untouched-queue baseline.

| Scope | Conditional estimate |
|---|---|
| Selected 30-item recovery | Terminal; no remaining automatic work. Three held items need separate review. |
| Frozen 1,153-item untouched first pass | **12.7-25.3 active hours**, including successful decisions and holds/failures. |
| Same first pass at assumed 50% availability | **25.3-50.7 calendar hours**, plus additional admission delays. |
| All 1,420 entries with audio and usable text | **No reliable finish date or finite guaranteed duration.** |

The first-pass central calculation is `1153 * 1581.878479 / 40 / 3600 = 12.6660` active hours. The upper planning value is an explicit **2x service-time allowance**. This is a planning scenario, not a confidence interval, measured variability bound, or promised deadline. It assumes similar successful-file lengths, source availability, Drive service and local backpressure. New refusals, unavailable sources, quarantines, uncertain attempts, language review, ASR timing holds, admission windows and downtime can extend the work. The 553-item later cohort is not authorized by this estimate.

Managed storage was **8,293,258,117 bytes (8.29 GB)** at the saved checkpoint, under the 16 GB managed ceiling. Runtime admission separately checks actual usage plus future growth reservations and physical spare within the owner's 20 GB allowance. The current v4 HTTP circuit is clear; six exact-item quarantines and one historical global event remain preserved. The older collector's STOP and 07:31 UTC retry record remain separate from the admitted native campaign.

## Refresh and interpretation

The dashboard shows checkpoint age, distinguishes confirmed running from released terminal readiness, and leaves the all-text finish date unknown. Older assumptions remain under `historical_assumptions` in the schema-2 ETA JSON, with their original 17 November 03:57 timestamp. The [17 November report](collection-eta-2026-11-17.md) is retained as history.

For a local status refresh, use the private root and all configured managed roots. This reads receipts and file sizes; it makes no source, Drive, media-probe or GPU request:

```powershell
python et-channelers/pipeline/ingestion_status.py --root PRIVATE_ROOT --out et-channelers/plan/ingestion_status.json --managed-root TOOLS_ROOT --managed-root OTHER_MANAGED_ROOT
```

For an ETA refresh, supply the completed 40-decision series directory, both completed recovery-frame directories, selection snapshots and the saved aggregate status. Repeat `--recovery-live` once per independent completed frame:

```powershell
python et-channelers/pipeline/collection_eta.py --root PRIVATE_ROOT --refresh-operational --service-live TERMINAL_SERIES --recovery-live RECOVERY_FRAME_1 --recovery-live RECOVERY_FRAME_2 --next-selection RECOVERY_SELECTION_JSON --campaign-selection FIRST_PASS_SELECTION_JSON --status-snapshot et-channelers/plan/ingestion_status.json --out et-channelers/plan/collection_eta.json
```

These commands do not admit or resume work. Source code and runtime configuration were frozen during this dashboard change. Private paths, process identities, source IDs, credentials and transcript content are excluded from the public export. Browser QA checked the ETA at 1440, 720, 390 and 320 pixels, keyboard expansion, unavailable data and its 200% zoom reflow; focused aggregate/proof tests passed.
