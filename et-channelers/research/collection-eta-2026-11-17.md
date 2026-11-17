# Conditional collection estimate — 17 November 2026 update

This supplement uses the **74-channel snapshot computed at 03:57:11 UTC on 17 November 2026**, published in [collection_eta.json](../plan/collection_eta.json). It supersedes the numerical scope of the [71-channel estimate](collection-eta-2026-11-16.md), while preserving that earlier report as a dated record.

**There is no reliable completion date.** Earlier native Chromium trials reached 69.892 seconds before failing. The repaired observer then detected SPS3 and stopped before downloading, without a new native attempt or output. There is no full-file success or sustained batch-rate measurement for this route, so these trials do not calibrate the model. Source work is parked; the new pre-BEGIN refusal's recorded window ends **18 November 2026 at 07:31:07 UTC**, superseding the earlier 01:40:49 window. Expiry permits a later attempt; it does not establish availability or resume collection automatically. Real-time browser recording remains parked. The estimates below are conditional capacity scenarios, not deadlines or confidence intervals.

## Current inventory and native collection scenarios

| Scope | Indexed items | Remaining audio/metadata pairs | Conditional active service time |
|---|---:|---:|---:|
| Newest 20 Videos per channel, where available | 1,420 | 1,373 | **3.81–9.27 hours** |
| Newest 50 Videos, inclusive of newest 20 | 3,449 | 3,402 | **9.45–23.07 hours** |
| All indexed uploads and legacy items | 67,594 | 67,547 | **7.82–16.84 days** |

The 47 already verified native audio/metadata pairs are excluded from each remaining-work total. The newest-50 estimate includes newest 20; do not add those two rows. The all-indexed row includes both priority stages and the 64,145-item final remainder. Counts describe the captured inventory, not a guarantee that every listed source can be retrieved.

This computation received **zero matched download-progress observations**. Its per-worker download rates of **1.56 / 2.00 / 2.00 MiB/s are explicit assumptions**, not a fresh measurement of this machine or service. The upload scenarios likewise assume aggregate goodput of **1 / 4 / 10 MiB/s**; upload throughput has not been isolated and measured. Earlier receipt timing includes pacing, queueing and cooldown waits and is not substituted for transfer bandwidth.

The model assumes four download workers and ten seconds between metadata request starts. For each scenario it takes the largest of the metadata-start floor, download service time and upload service time, because those stages can overlap. This omits some real overhead. At the snapshot time the recorded audio wait was approximately 21.73 hours; future availability, refusals, retry limits, local backpressure and activation delays can add further elapsed time. Applying a hypothetical availability fraction does not turn the scenario into an upper bound.

Audio size scenarios use the 47 verified pairs' observed encoding densities. That recent cohort is not a representative sample of the full archive. **18,904 remaining items have no recorded duration**. Missing durations are imputed by the documented channel/tab hierarchy; where Shorts have insufficient observations, 15/60/180 seconds are explicit illustrative assumptions. No duration cutoff is applied. The estimated audio bytes exclude metadata, caption bundles, catalogs and retry traffic.

## Browser recording: a playback floor, not a completion forecast

The remaining newest-20 queue has **2,094,214 known audio seconds: 581.73 playback hours**, plus one item with unknown duration. At normal **1× playback**, four continuously productive, perfectly balanced workers would require at least:

**581.73 ÷ 4 = 145.43 hours = 6.06 days.**

This is an idealized lower bound for the known playback duration. It excludes the unknown item, browser activation, ads, interrupted or rejected playback, validation, upload and scheduling overhead. Four successful concurrent full recordings have not been demonstrated for this queue. Native transfer rates cannot be applied to real-time browser recording. Browser recordings also remain separately labeled re-encoded artifacts, not native waveform copies.

## Captions and ASR are separate work

English caption acquisition retains its own endpoint pacing and cooldown. The model assumes at least 15 seconds between caption request starts. Illustrative zero/one/two-track scenarios do not establish actual availability or an upper bound; some items have more tracks, while unavailable or unresolved inventory must not be counted as no captions. Audio and caption work may overlap, so their complete-archive estimates are not simply added.

**27 ASR sources, covering approximately 9.97 source hours, are verified on Drive:** 25 English recordings plus Spanish and Japanese originals with separate English translations. They remain **unreviewed ASR**: successful upload and model completion do not establish transcription accuracy or speech coverage. The multilingual frame is complete with three explicit holds for metadata nonlexical content, no VAD speech in sampled windows, and insufficient language confidence. Those observations do not establish whole-file silence or meaning. The GPU is released. These results are not an ASR forecast for all 1,420 newest-20 items; the native collection model excludes ASR entirely.

## Storage and interpretation

The current native spool reservation is **8 GB**, within a **16 GB managed-project cap**. Real-time capture and its earlier 5 GB reservation are parked. The owner's total local allowance remains **20 GB with a 2 GB buffer**; models, environments, repositories, inputs, temporary files and retained outputs count toward their applicable budgets. Verified upload permits rolling retirement of owned local copies. The 17 GB private ceiling recorded in the native estimate's assumed configuration is not permission to override the current 16 GB managed cap or the native reservation.

The [machine-readable estimate](../plan/collection_eta.json) records its input hashes and assumptions. This supplement uses aggregate counts only; it contains no source media, transcript text, credentials or private object identifiers. A credible observed finish estimate requires successful end-to-end runs under the chosen acquisition method and representative measurements of throughput, failures and duty cycle.
