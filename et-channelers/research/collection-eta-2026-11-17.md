# Conditional collection estimate — 17 November 2026 update

**19:13 UTC operational update:** 76 of 1,420 unique latest-20 entries have verified audio from canonical or publisher sources; 74 have an audio edition with saved text. One complete native recording and metadata are newly verified, bringing native acquisition to 48. Its 1,570.961-second audio completed within a 21.984-second child trial, but this includes setup and is one item. The broader pilot retained no media before local cleanup stopped it; its successor cleaned correctly but stopped on unbound browser-bootstrap media failures, leaving fourteen untouched. A scope correction is reviewed. No sustained batch throughput or all-channel completion date is established. Publisher mirrors, native duplicates, caption availability, and ASR work must remain separate inputs.

All ten Athina publisher editions now have ASR; the remaining-eight controller completed in 629.848 seconds including staging/upload/cleanup. Native English ASR of the 26-minute recording took 50.766 seconds, with maximum rolling GPU use 29.37%. These are observed workload-specific results, not forecasts for all languages or recordings. The capacity scenarios below retain their original 03:57 snapshot/47-native-pair inputs; they are historical assumptions, not live remaining-work totals or a benchmark of the new route.

This supplement uses the **74-channel snapshot computed at 03:57:11 UTC on 17 November 2026**, published in [collection_eta.json](../plan/collection_eta.json). It supersedes the numerical scope of the [71-channel estimate](collection-eta-2026-11-16.md), while preserving that earlier report as a dated record.

**There is no reliable completion date.** In the earlier experimental SABR checkpoint, trials reached 69.892 seconds before failing and a repaired observer later stopped on SPS3 before downloading. That route has no full-file success; its recorded window remains **18 November 2026 at 07:31:07 UTC**. The separately admitted supported HTTPS recovery above does not calibrate a sustained all-channel rate or resume the old SABR collector. Real-time recording remains parked. The historical capacity scenarios below are not deadlines or confidence intervals.

## Measured publisher-mirror route, 16:35 UTC

One official publisher mirror now has a complete, Drive-verified audio edition and English automatic captions. Its 50,520,065-byte audio transfer took 3.891 seconds (about 12.98 MB/s), followed by a verified three-object upload. Browser metadata took 12.687 seconds for this episode. These are single-item measurements, not a sustained batch benchmark or a forecast for all channels. Candidate discovery, source matching, upload time and source availability remain unmeasured at scale. No all-channel finish ETA is supported yet. Publisher mirrors retain their own source/edition labels and do not reduce the native YouTube remaining-work totals below.

The next batch starts with at most two audio/CDN I/O workers and serialized publisher metadata visits, using byte reservations and upload backpressure. It does not wait through playback. Usable English captions avoid redundant GPU transcription; absent captions can later use the contained leased CUDA lane.

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

**29 native-source ASR bundles, covering approximately 10.8 source hours, are verified on Drive:** 27 English recordings plus Spanish and Japanese originals with separate English translations. They remain **unreviewed ASR**: successful upload and model completion do not establish transcription accuracy or speech coverage. Two held audio inputs remain unresolved; the later [held-audio review](held-audio-language-review-2026-11-17.md) supersedes the earlier three-hold snapshot. The GPU is released. Publisher-edition ASR is counted separately. These results are not an ASR forecast for all 1,420 newest-20 items; the native collection model excludes ASR entirely.

## Storage and interpretation

The current native spool reservation is **8 GB**, within a **16 GB managed-project cap**. Real-time capture and its earlier 5 GB reservation are parked. The owner's total local allowance remains **20 GB with a 2 GB buffer**; models, environments, repositories, inputs, temporary files and retained outputs count toward their applicable budgets. Verified upload permits rolling retirement of owned local copies. The 17 GB private ceiling recorded in the native estimate's assumed configuration is not permission to override the current 16 GB managed cap or the native reservation.

The [machine-readable estimate](../plan/collection_eta.json) records its input hashes and assumptions. This supplement uses aggregate counts only; it contains no source media, transcript text, credentials or private object identifiers. A credible observed finish estimate requires successful end-to-end runs under the chosen acquisition method and representative measurements of throughput, failures and duty cycle.
