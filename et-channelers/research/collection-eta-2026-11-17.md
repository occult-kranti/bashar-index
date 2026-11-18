# Conditional collection estimate — 17 November 2026 update

## Current continuation, November 18 00:05:09 UTC

The frozen snapshot has **128 native pairs / 77 native ASR / 156 unique audio
entries / 122 audio entries with saved text**. The amended 40-target source run
has 22 new canonical pairs: its first frame ended with 15 verified and 5 held,
and its second frame is still running. The separate 42-input English consumer
uses one input per process and publishes valid results immediately. A retained
word-alignment/segment-timing case is excluded; its cause remains unresolved.
Do not extrapolate a final rate from this unfinished run.

The completed initial 60-item baseline remains **1,642.680453 seconds** for 30
archives and 18 overlapping English ASR bundles, with 8.06 GB measured after its
closure. The earlier **8 to 12 active-hour first-pass planning range** was conditional
on that workload mix; it is neither a completion date nor a guarantee for all
held audio, languages and transcripts. Decoded DRC metadata has now enabled one
strict full-native recovery, but one successful repair does not quantify the
remaining held population. A separate 30-item recovery and finite campaign are
prepared only and remain disabled.

Current six-root storage is **8,328,191,629 bytes (8.33 GB)** under the 16 GB
managed ceiling. Native growth remains 5.5 GB and staging 500 MB/three pairs;
other active allocations and 2 GB physical spare must still pass admission.
The historical measurements and remaining-work denominators below retain their
original dates. Global source holds, Drive service and ASR backpressure can add
wall time; no reliable all-audio-plus-text finish date is established.

## Completed 60-item series, 22:27 UTC

The latest source series made 60 decisions in **27m22.68s**, archiving **30 new
native audio/metadata pairs**: 651,969,521 audio bytes / 11.19 source hours.
The parallel consumer verified **18 English ASR bundles / 7.85 source hours**,
then retired its inputs and released the GPU/staging reservation. Twelve new
recordings await language review. Three uncertain source attempts remain held;
no retry is implied by a completed series.

Together, the preceding two 20-item v4 frames and this series made **100
first-pass decisions in 2,503.102453 seconds (41m43s)**: about 2.40 items/minute.
The next-cohort selection snapshot identifies **1,213 untouched candidates**.
At the aggregate observed mix, their first pass implies **8.4 active hours**;
use **8–12 active hours** for planning while source availability, upload service
and backpressure remain similar. This is not a statistical interval or a date
for complete acquisition/transcription. It excludes recovery of held formats,
source denials, uncertain attempts and additional language/ASR work. The new
upload-overlap scheduler has only offline validation so far; no speedup is
assumed in this estimate.

The 22:27 aggregate has **100 native pairs / 63 native ASR / 128 deduplicated
audio entries / 108 audio entries with saved text**. A single six-root inventory
after closure measured **8.06 GB**, plus 300 MB of other active growth, below
16 GB; physical free space was 36.36 GB. Source, English staging and GPU leases
from the series are released. Later admissions retain their own exact budgets.
The earlier measurements and hypothetical scenarios below remain dated records.

## Measured native batches, 21:59 UTC

The current snapshot has 77 native audio/metadata pairs and 46 native-source ASR
bundles. Including qualified publisher editions, 105 of 1,420 latest-20 entries
have audio and 91 have an audio edition with saved text. A 60-item/three-frame
series is running with two source workers, Drive archival and a parallel local
English-ASR handoff. These are observed checkpoints, not a claim of completion.

| Completed native frame | First-pass items | Wall time | Immediate Drive pairs | Audio bytes / source duration |
|---|---:|---:|---:|---:|
| v4 frame 1 | 20 | 359.016s (5m59s) | 12 | 216,163,605 / 13,356s |
| v4 frame 2 | 20 | 501.406s (8m21s) | 7 | 252,899,891 / 15,626s |

One additional complete file from frame 1 was recovered and archived offline
after its local progress write failed. It is outside the immediate completion
count above. The Windows write repair and a strict normal/DRC catalog repair
were made before the 60-item series; its full measured result is not yet known.

The two frames made 40 decisions in 860.422 seconds: about 2.79 items/minute.
At that exact workload mix, another 1,300 first-pass decisions would take about
**7.8 active hours**. Allow roughly **6–10 active hours for the remaining first
pass** as an operational planning range, conditional on similar item mix,
source availability, upload service and storage/GPU backpressure. This is not a
statistical confidence interval, a bound, or an ETA for all audio and captions.
Held formats, source denials, unknown-language review and further ASR still
require work. A reliable all 1,420-audio-plus-text finish date is not established.

ASR overlaps downloads. The eight-item English frame processed 9,325.877 source
seconds in 745.016 wall seconds including staging/upload/retirement, with maximum
rolling GPU use 60.71%. The first two local-handoff English inputs processed
5,757.434 source seconds in 248.059 seconds, without Drive input pulls. The
four-source multilingual review produced three verified original/English or
inferred-English bundles and one no-reliable-speech hold. These are different
workloads; none measures every-word accuracy or all-language throughput.

The active reservations are 5.5 GB native plus 500 MB/three-pair English staging,
with one GPU owner, a 6.5 GB VRAM maximum and soft 70% rolling target. Actual
six-root storage was 8.09 GB at 21:59 UTC. Actual plus reserved future growth must
fit 16 GB, within the owner's 20 GB allowance and 2 GB spare. Individual capacity
waits are local backpressure and are not counted as source rate-limit periods.

The sections and machine-readable estimate below retain their explicitly dated
03:57/19:45 inputs and assumptions. They are historical scenarios rather than
the current execution profile. Real-time capture remains parked.

**19:45 UTC operational update:** 78 of 1,420 unique latest-20 entries have verified audio from canonical or publisher sources; 76 have an audio edition with saved text. Native acquisition is 50 and native ASR is 31. Three complete browser-assisted native files are verified, including two recovered locally after a capacity stop. Corrected reservation accounting and automatic metadata preservation then ran on a fresh 20-item frame; one selected-media HTTP 403 stopped it after 15.734 seconds, leaving seventeen pending and no new verified pairs. The denied asset and source hold remain preserved for scope review. No sustained all-channel throughput or finish date is established. Publisher editions, native duplicates, caption availability and ASR work remain separate inputs.

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
