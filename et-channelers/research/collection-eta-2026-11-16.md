# Conditional collection estimate — 16 November 2026 planning session

Computed **2026-11-17T01:03:25.876533+00:00** from a stable private metadata snapshot after the 71-channel intake. This report reads queue rows, durable receipts and selected JSON progress fields only. **No media/transcript content, source requests, Drive requests, ASR, model downloads or collector changes were performed.**

**There is no finite guaranteed completion date while access is blocked and refusals can recur.** Under the assumptions below, completing the currently indexed native audio is approximately **7.7–16.5 active days as a service-time floor**, before unmeasured overhead and future downtime. This is a conditional capacity model, not a promised finish interval. At 50% future service availability, that becomes roughly **16.4–33.9 elapsed days including the current wait**, still not an upper bound.

## Inputs and denominators

| Measure | Observed metadata |
|---|---:|
| Tracked-channel snapshot | 71 |
| Full queue / verified audio-metadata pairs / remaining | 66,446 / 47 / 66,399 |
| Newest-20 cohort / inclusive newest-50 / final remainder | 1,360 / 3,320 / 63,126 |
| Remaining with known durations | 47,558 |
| Known remaining audio hours | 23,802.8 |
| Remaining without durations | 18,841 |
| Unknown durations by tab | 18,752 Shorts; 23 recorded streams; 1 Video; 65 legacy unknown-tab items |
| Verified calibration audio | 47 pairs; 18.43 hours; 0.950 GB |

The 47 completed pairs are from the recent priority cohort. They are not a representative probability sample of the full archive. Historical podcast, archive.org and earlier transcript-store totals are excluded. An unavailable or ongoing source can remain unresolved; indexing is not proof it can be retrieved.

## Native sizes and missing durations

Verified audio yields **14.32 kB per audio second** as a duration-weighted mean (about 114.6 kb/s). Across the 47 pairs, p10/median/p90 are **12224 / 13826 / 16673 bytes per audio second**. These empirical quantiles are scenario inputs, not a confidence interval or codec guarantee.

Missing durations use same-channel/tab observations when at least five exist, then same-tab observations when at least five exist. **All 18,752 Shorts lack durations**, so borrowing long-video lengths would be misleading. Their explicit illustrative assumptions are **15 / 60 / 180 seconds per item**; these are neither measured durations nor an exclusion threshold or asserted maximum. The 24 missing Video/stream durations use channel/tab evidence. The 65 unknown-tab items use pooled p25/median/p90 with that fallback disclosed.

These assumptions produce **23,911.2 / 24,162.5 / 24,853.9 remaining audio hours**, and native audio quantities of **1.05 / 1.20 / 1.49 TB** in the optimistic/central/cautious scenarios. Metadata, caption bundles, catalog objects and retry traffic add bytes; they are not included in those audio quantities. Unknown speech lengths and formats can lie outside these scenarios.

The current 17 GB private-root cap is a spool ceiling, not a cap on total Drive archive size. The model retains long recordings; 21 known remaining items exceed eight hours. No known-duration item exceeds 17 GB under this p90 bitrate assumption, but that does not prove it fits the **available** spool after other files/reservations. Exact admission remains the collector's responsibility; unusually large, inaccessible or ongoing items can prevent literal completion of every ID.

## What timing was actually measured

Eight selected existing progress logs supplied **7 distinct verified objects** with compatible byte totals and active download-prefix timings. Repeated/copied logs are deduplicated. They cover 237.0 MB over 120.1 summed worker-seconds; median observed prefix coverage is 69.0%.

Observed per-worker p10/median/p90 goodput is **1.56 / 2.00 / 2.00 MiB/s**. The near-2 MiB/s ceiling reflects the configured throttle. These are partial-stream observations from earlier configurations, not measured sustained four-worker aggregate throughput or proof the new browser service will perform identically.

Receipt attempt elapsed time has median **33 seconds**, p90 57.8; download-to-first-verification lag has median **241 seconds**, p90 1,618.4. The former includes metadata pacing/extraction, and the latter includes queues, upload, verification and possible quota waits. **Neither is treated as pure transfer time.** Exact upload-start/end timing is unavailable, so aggregate upload goodput is an explicit **10 / 4 / 1 MiB/s** optimistic/central/cautious assumption.

## Overlapped-stage capacity model

Assumed configuration: **four source workers, four upload transfers, eight pairs per upload batch and sixteen ready/in-flight items**. This is the requested modeling configuration, not a live-process inspection. Metadata starts are globally separated by **10 seconds**. English caption requests have their own serialized **15-second** starts.

For each phase:

```text
metadata floor = max(0, remaining_items - 1) × 10 seconds
download service = estimated_audio_bytes / (4 × per_worker_goodput)
upload service = estimated_audio_bytes / assumed_aggregate_upload_goodput
active floor = max(metadata floor, download service, upload service)
```

Download and upload overlap, so their service times are not simply added. Upload transfer count does not multiply the assumed aggregate connection speed. The three phase floors are summed using **newest20 + only the 21–50 extension + final remainder**, avoiding double-counting the inclusive newest-50 cohort. These floors omit metadata response time beyond the start schedule, finite-buffer effects, pipeline fill/drain, hashing, API verification, failures and retries.

| Phase from this checkpoint | Remaining items | Audio GB, optimistic–cautious | Active-hour floor, optimistic / central / cautious |
|---|---:|---:|---|
| Finish newest 20 | 1,313 | 24.7–33.7 | 3.6 / 3.6 / 8.9 |
| Add ranks 21–50 | 1,960 | 36.8–50.2 | 5.4 / 5.4 / 13.3 |
| Indexed remainder | 63,126 | 990.8–1,407.9 | 175.3 / 175.3 / 373.0 |

Finishing the inclusive newest-50 cohort therefore has an active floor of about **9.1–22.2 hours** from this checkpoint. The full staged archive has active floors of **7.7 / 7.7 / 16.5 days**. At the central assumptions, global metadata pacing is the limiting service. More download workers alone cannot beat that floor; in the cautious case, the assumed upload connection dominates.

## Cooldowns and calendar scenarios

At computation, the audio receipt deadline was **2026-11-18T00:57:17.380Z**, about 23.9 hours away; the independent caption deadline was **2026-11-17T23:20:02.791Z**, about 22.3 hours away. These are dated receipt observations. Later runtime decisions or renewed refusals can change them.

Future availability is unmeasured. The examples below add the current wait **once**, then divide active service time by an assumed future available fraction. They are not forecasts of source behavior.

| Assumed future service availability | Audio archive elapsed-day floor, optimistic–cautious |
|---|---:|
| 100% | 8.7–17.5 |
| 50% | 16.4–33.9 |
| 25% | 31.7–66.9 |

If availability approaches zero or repeated refusals exhaust the bounded retry policy, no finite finish time follows. Terminal source unavailability, live broadcasts, premiere states, missing-format items and storage deferrals must be reported separately, never counted as successful archive completion.

## Captions are a separate endpoint and completion condition

There are **66,430 queued videos with pending or unknown completed English-caption inventories**. Assuming zero, one or two remaining English tracks per such video gives caption request-start floors of **0.0 / 11.5 / 23.1 active days**. Zero is a scenario, not evidence of absence; two is not an upper bound because published/regional originals can be more numerous.

Caption transfer, normalization/ZIP, upload and metadata-only backfill add time. Some caption work overlaps audio acquisition. A combined audio-plus-caption floor is at least the slower endpoint's floor; it is not the sum of two independent full-archive ETAs. With one track per pending video, caption pacing alone can exceed the central audio floor; with two it reaches about 23.1 active days. Caption cooldowns do not pause audio, but completing all captions can extend beyond audio completion. ASR and future corpus analysis are excluded entirely.

## Recompute and validation

The new [collection_eta.py](../pipeline/collection_eta.py) is an offline aggregate estimator. With no progress logs it explicitly falls back to assumed download rates; it never silently derives bandwidth from receipt waits. Read queues only after their writer completes a checkpoint. It verifies stable file reads, checks tier/partition consistency, uses canonical completed-audio/caption proof predicates, and emits no titles, video/channel IDs, Drive IDs, private paths, transcript text or raw error strings.

```powershell
$EtPython = Join-Path $env:USERPROFILE 'et-channelers-tools/venv/Scripts/python.exe'
$EtPrivate = Join-Path $env:USERPROFILE 'et-channelers-private'
& $EtPython -I et-channelers/pipeline/collection_eta.py --root $EtPrivate --workers 4 --metadata-interval 10 --caption-interval 15
```

For measured-prefix scenarios, repeat `--progress-log` for the selected private pilot/supervisor logs. The report used eight logs: repaired audio, optimization audio, original/resumed English archive, caption-scoped archive, original/resumed supervised archive, and paced supervisor resume. Only numeric progress events matched to verified objects entered the estimate.

Focused offline tests cover mixed receipt timings, bad/mismatched progress, missing durations, absent Shorts observations, overlap arithmetic, malformed proof, separate source/caption cooldowns, inconsistent stages, and isolated `python -I` CLI privacy/read-only behavior. The test command is:

```text
python -I -m unittest discover -s et-channelers/pipeline/tests -p test_collection_eta.py -v
```

Input SHA-256 pins (only hashes, no private paths):

| Snapshot | SHA-256 |
|---|---|
| full_queue | `4239d9723aa45cc353fa61e1f4d5091acaf656967c41e64cec386182d8eb8497` |
| newest20 | `702c7bb0d47ef3c3addd128d88e925357dc13eeb249782ad9b12a3a4900c9f9e` |
| newest50_inclusive | `55ab7a5004fe01c41d6537f664db0516d9ba6c5c17824343b8351727f7bdcf8c` |
| remaining_archive | `5ad14f0dc1b07de61595dd6b7b0ef5e0bf04f54c80fb4751a5ecab44546b921e` |
| audio_journal | `800b700b475a12fc28810f2ee99ae93e3a3b732798869eceee063ea08ec7bc91` |
| caption_journal | `7c86a73abc922e612d301d499d03dc40ebdf19ca572a88cd79a0cc7802308d77` |

The JSON output also pins the selected log bytes and reports malformed receipt counts. Unknowns and scenario assumptions remain explicit when counts change; rerun after a new stable checkpoint instead of treating this dated report as live progress.
