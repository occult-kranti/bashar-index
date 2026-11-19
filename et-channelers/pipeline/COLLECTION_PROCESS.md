# Collecting the latest 20+ recordings

## Current run

The November 19, 2026 selection contains **1,976 public regular uploads from 101 channels**. At 21:45 UTC, 67 channels had all their selected recordings on Drive. The saved audio comprised 1,211 native YouTube recordings, 295 YouTube editions with unverified source-track identity and 165 independently matched publisher editions. That gives **1,671 saved and 305 outstanding**. [Collection dashboard](../dashboard/collection/) · [Guest-channel evidence](../research/interview-discovery-2026-11-19/verified-guest-channels.csv)

Use each creator's newest-first **Videos** tab. Keep videos of every duration and publication date. Continue past membership-only entries to fill 20 public positions, or reach the end of the creator's displayed list. Ninety-six channels supplied twenty recordings. The other five supplied 56 combined. The cumulative index preserves 2,697 entries, comprising 2,067 regular videos, 482 Shorts and 148 streams. Store each upload under its original tab classification and stable channel and video IDs.

## Download and upload together

The portable Windows launcher defaults to six source workers, three concurrent Drive transfers, twelve recordings per upload batch, and 24 ready or in-flight slots. Its supported range extends to eight source workers and four upload transfers. A short flush timer also publishes small batches. Accepted bodies can upload while another worker retrieves the next recording. Browser startup gets a separate memory check because launching a browser uses more RAM than continuing an established transfer. [Windows setup](WINDOWS_DRIVE.md) · [Host capacity checks](host_capacity.py)

The operator authorized **23 decimal GB across managed project files** and **12 GB physically free after outstanding reservations**. Existing media, partial files, tools, models and browser storage count. The Drive archive has no project-imposed size limit. Workers reserve space before accepting a body and release it after the corresponding files leave local storage. The extra 5 GB became available at 20:31 UTC after the preceding batch released its 4.8 GB reservation. The 96-item successor started at 20:36 UTC with a 9 GB reservation. Its admission accounted for 21.13 GB of files, future writes and journal space. It runs up to six source workers, two staggered browser starts, eight outstanding items and three Drive transfers. [Grouped uploads](grouped_publication.py) · [Publisher staging and upload](publisher_mirror.py)

Each Drive batch verifies remote object IDs, byte counts and MD5 for both audio and provenance. The local journals preserve SHA-256 and identify the recording edition. A verified pair unlocks deletion of its local working copies. Incomplete jobs retain their bytes and resume from their last accepted stage. One source problem can defer a recording while unrelated creators continue. English publisher captions, original English automatic captions and separately identified publisher transcripts keep their own receipts. [Receipt coverage](collection_coverage.py) · [Drive batch lookup](drive_batch_stat.py)

## Issues resolved during the run

| Observation | Change |
| --- | --- |
| An earlier dashboard showed 1,108 native YouTube recordings from a different selection. | Join receipts by creator, video ID and edition against one saved selection. Show the observation time and count each recording once. |
| A creator description or browser format list can exist without a complete media body. | Keep metadata and media receipts separate. Count an audio file after the whole file and its sidecar are verified on Drive. |
| A publisher can use a different episode title or issue a longer MP3. | Match the creator and edition using the public episode page, player identifiers, title, publication evidence and duration. Compare the complete HTTP body with packet duration and tag bytes. Keep the publisher's timeline for its transcript. |
| A local validation failure left complete MP3s in the spool. | Reuse the accepted bodies. Include all retained files in subsequent staging decisions and use one grouped checksum lookup after upload. |
| A host and a guest may share a YouTube byline. | Keep personal attribution, channel ownership and interview appearance in separate fields. The Natalie Namaste review links 57 podcast episodes to YouTube and identifies 31 distinct guest-owned channels. [Episode matches](../research/interview-discovery-2026-11-19/episode-crosswalk.csv) · [Appearance evidence](../research/interview-discovery-2026-11-19/guest-appearances.csv) |

## Checking progress

A November 19 batch started 54 jobs, saved 35 audio and metadata pairs, and passed 16 recordings to the native-audio worker. Three jobs ended with source or transport errors. Closing admissions at 16 ready native recordings let the already-running transfers finish. The native worker then archived all 16. A progress file briefly disappearing during replacement is a local observation error. The controller waits for a stable snapshot while independent transfers proceed. [Native handoff queue](native_handoff_queue.py)

The collector checks saved Drive receipts before starting each source request. If an independent publisher worker has just archived that recording, the collector skips that single request and proceeds with its other jobs. For native transfers, the recorded time of a completed response determines when transfer resumed. A later audio inspection or delayed upload has its own timestamp. This keeps the scheduler's decision tied to the actual network activity. [Transfer completion clock](native_completion_clock.py) · [Progress and producer monitor](PRODUCER_MONITOR.md)

For publisher feeds, match the creator and episode before transferring audio. A title ending in a season and episode number can match a shorter podcast title when both numbers and the duration agree. Some publishers distribute an alternative edit with a different running time. Preserve the evidence and the difference in the recording metadata. For Lisa Williams, eight separately verified podcast editions supplied eight English transcripts. Another five published transcripts accompanied recordings already saved on Drive, so those five audio files needed no further transfer. Paragraph offsets support quotations and searches in these documents. [Episode matching](interview_guest_discovery.py) · [Publisher transcript reader](publisher_feed_text.py)

Twenty more recordings with saved YouTube audio received timed English captions from the creators' other releases. Eight tracks on Rumble were labeled original automatic English. Twelve tracks on Buzzsprout had English cues and an English publisher feed, with the transcription method unspecified. Preserve each track's source clock when citing a passage. [Publisher caption reader](corpus_publisher_variant_view.py)

Run from `et-channelers` with the private archive root and the selected recording index. The first command reads the journals and writes two private CSVs alongside the JSON report. The second inventories existing transcript inputs without starting inference. The SHA-256 value must be the digest of the same selection file.

```powershell
python -m pipeline.collection_coverage --root $archiveRoot --selection $selectionFile --out $coverageFile --activity-csv $creatorsCsv
python -m pipeline.stage_archived_text --root $archiveRoot --selection $selectionFile --selection-sha256 $selectionHash --inventory-only
```

Use the change in verified recordings between checkpoints of the **same selection** to estimate remaining audio time. Include pauses, uploads and checks in elapsed time. Keep transcripts, source media and private worker journals in the owner's archive. The public dashboard, charts and exports receive a coordinated refresh after collection and analytical review. [Dashboard hub](../../dashboards/)

## After the last audio receipt

1. Reconcile the complete selection, archive the final recording index and creator table on Drive, then close the run in the README and handoff. Prepare the newest-50 workload by extending each public Videos listing, reusing saved IDs, and scheduling only the additional recordings. Index the rest of the catalog separately. Keep the 20-record cohort available as its own research sample.
2. Use the saved English captions and publisher documents first. Run GPU speech recognition only for missing usable text in an isolated environment. For a non-English recording, preserve the original transcript and an English translation. Target 70% rolling GPU utilization and record observed utilization. Keep an edition-specific timeline for each text.
3. Have the first panel study coverage, word and expression matches, TF–IDF, topic and embedding clusters, publication-time changes, and cross-creator descriptions of the same event or claimed source. Export creator-normalized tables, plots, networks and heatmaps with denominators and underlying evidence.
4. Give the second panel the first panel's findings, source excerpts and uncertainty estimates. Challenge candidate clusters, shared-event matches and prediction dates. Evaluate rival explanations. Turn documented proposed measurements and experimental setups into testable questions, keeping speakers' claims distinct from independent evidence. Publish reviewed aggregates with a reproducible snapshot and update all dashboards together. [Analysis plan](../research/analysis-plan-2026-11-16/README.md) · [Cross-creator event register](../research/cross-channel-events-2026-11-16.md)

## Preparing the next 50

After the 20-recording cohort is complete, use a new dated private folder for the 50-recording sweep. From `et-channelers`, set `$archiveRoot` to the private root, `$channelRoster` to the same creator manifest, `$previousSelection` to the completed 20-recording selection JSON and `$sweep` to the new folder.

```powershell
python -m pipeline.collect_regular_videos fetch --root $archiveRoot --channels $channelRoster --out $sweep
python -m pipeline.collect_regular_videos index --root $archiveRoot --channels $channelRoster --out $sweep --per-channel 50
python -m pipeline.extend_regular_video_grid --root $archiveRoot --base (Join-Path $sweep 'fresh-videos-50.json') --out (Join-Path $sweep 'public-50.json')
python -m pipeline.prepare_regular_fifty --root $archiveRoot --previous $previousSelection --fresh (Join-Path $sweep 'public-50.json') --out (Join-Path $sweep 'work')
```

The planner reads the local Drive receipts once. It checks that the preceding cohort is complete and that every creator supplied 50 public regular uploads or reached the end of their Videos tab. It writes the new membership to `work/selection.json` and the outstanding downloads to `work/pending.csv`. The queue interleaves creators by publication rank. Previously saved recordings are reused even when their rank has changed. The old selection and its historical Shorts and streams remain available for later comparison. [Queue planner](prepare_regular_fifty.py)
