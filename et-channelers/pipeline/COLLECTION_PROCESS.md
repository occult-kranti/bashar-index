# Collecting the latest 20+ recordings

## Current run

The November 19, 2026 selection contains **1,976 public regular uploads from 101 channels**. At 22:51 UTC, 67 channels had all their selected recordings on Drive. The saved audio comprised 1,240 native YouTube recordings, 368 YouTube editions with unverified source-track identity and 176 independently matched publisher editions. That gives **1,784 saved and 192 outstanding**. [Collection dashboard](../dashboard/collection/) · [Guest-channel evidence](../research/interview-discovery-2026-11-19/verified-guest-channels.csv)

Use each creator's newest-first **Videos** tab. Keep videos of every duration and publication date. Continue past membership-only entries to fill 20 public positions, or reach the end of the creator's displayed list. Ninety-six channels supplied twenty recordings. The other five supplied 56 combined. The cumulative index preserves 2,697 entries, comprising 2,067 regular videos, 482 Shorts and 148 streams. Store each upload under its original tab classification and stable channel and video IDs.

## Download and upload together

The portable Windows launcher defaults to six source workers, three concurrent Drive transfers, twelve recordings per upload batch, and 24 ready or in-flight slots. Its supported range extends to eight source workers and four upload transfers. A short flush timer also publishes small batches. Accepted bodies can upload while another worker retrieves the next recording. Browser startup gets a separate memory check because launching a browser uses more RAM than continuing an established transfer. [Windows setup](WINDOWS_DRIVE.md) · [Host capacity checks](host_capacity.py)

The operator authorized **23 decimal GB across managed project files** and **12 GB physically free after outstanding reservations**. Existing media, partial files, tools, models and browser storage count. The Drive archive has no project-imposed size limit. Workers reserve space before accepting a body and release it after the corresponding files leave local storage. The extra 5 GB became available at 20:31 UTC after the preceding batch released its 4.8 GB reservation. The 96-item successor started at 20:36 UTC with a 9 GB reservation. Its admission accounted for 21.13 GB of files, future writes and journal space. It runs up to six source workers, two staggered browser starts, eight outstanding items and three Drive transfers. [Grouped uploads](grouped_publication.py) · [Publisher staging and upload](publisher_mirror.py)

Each Drive batch verifies remote object IDs, byte counts and MD5 for both audio and provenance. The local journals preserve SHA-256 and identify the recording edition. A verified pair unlocks deletion of its local working copies. Incomplete jobs retain their bytes and resume from their last accepted stage. One source problem can defer a recording while unrelated creators continue. English publisher captions, original English automatic captions and separately identified publisher transcripts keep their own receipts. [Receipt coverage](collection_coverage.py) · [Drive batch lookup](drive_batch_stat.py)

A measured native-audio batch saved 16 recordings totalling 456.2 MB in 399.9 seconds. Drive publication occupied 356.2 seconds, including 301.4 seconds spent copying. In the grouped uploader, one publication worker accepts up to six already validated pairs, uses three concurrent file transfers and looks up the whole group's checksums together. A partial upload retains every unverified pair and its metadata on disk. The first verified file in a group can be retired as soon as its individual receipt is written. The same Drive quota journal and code checks apply to each group. [Native uploader entry point](native_audio_sink.py) · [Group publication](native_grouped_publication.py)

## Issues resolved during the run

The first production batch with six source workers and eight outstanding recordings verified 354.45 MB across 13 recordings in 241.8 seconds. A copy or lookup in the table refers to a batch command. Each command can cover multiple files.

| Observed measure | Earlier single-pair publication | Grouped publication |
| --- | ---: | ---: |
| Verified recordings | 16 | 13 |
| Mean audio size | 28.51 MB | 27.27 MB |
| Drive copies / checksum lookups | 16 / 16 | 5 / 5 |
| Median wait between ready and publication | 79.4 s | 12.2 s |
| Verified audio per second from start to close | 1.14 MB | 1.47 MB |

The grouped batch finished retrieving audio in 77.6 seconds. About 153 seconds of its runtime had Drive work alone, close to the prior batch's 152 seconds. Three requested source files returned HTTP 403. These batches contain different recordings. Use the complete campaign's receipt rate for the completion estimate.

A subsequent trial archived 15 audio and metadata pairs totaling 447.1 MB in 309.6 seconds. Its four-transfer group copied 194.6 MB at 2.23 MB/s. The closest three-transfer group had copied 187.9 MB at 2.27 MB/s. The host had sufficient memory for either configuration. The collector returned to three simultaneous Drive transfers after the trial.

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

Melissa Minnich's show publishes complete MP3s through an RSS feed that reports zero for their size. The publisher worker reserved a bounded number of bytes before downloading, read each MP3 to its end and inspected its audio packets. Matching the host, named guest, episode topic and publication period established the association. It archived ten podcast editions and ten provenance files by 22:23 UTC, then retired 413,069,340 bytes of local audio. The podcast and YouTube editions have different running times. [Publisher's show page](https://mindbodyspirit.fm/shows/high-on-life-with-melissa-minnich/) · [Feed reader](interview_guest_discovery.py)

Run from `et-channelers` with the private archive root and the selected recording index. The first command reads the journals and writes two private CSVs alongside the JSON report. The second inventories existing transcript inputs without starting inference. The SHA-256 value must be the digest of the same selection file.

```powershell
python -m pipeline.collection_coverage --root $archiveRoot --selection $selectionFile --out $coverageFile --activity-csv $creatorsCsv
python -m pipeline.stage_archived_text --root $archiveRoot --selection $selectionFile --selection-sha256 $selectionHash --inventory-only
```

Use the change in verified recordings between checkpoints of the **same selection** to estimate remaining audio time. Include pauses, uploads and checks in elapsed time. Keep transcripts, source media and private worker journals in the owner's archive. The public dashboard, charts and exports receive a coordinated refresh after collection and analytical review. [Dashboard hub](../../dashboards/)

## Unresolved downloads

The November 19, 23:25 UTC register identified 27 recordings with a closed unsuccessful attempt and no verified audio. The media provider returned HTTP 403 for 23. Three accepted transfers ended early and one local browser failed to start. The remaining 140 outstanding recordings had no documented failure in the closed work through 23:22 UTC. A verified publisher recovery retires the recording from this list and preserves its publishing source in the collection inventory.

The dated snapshot is available in three formats. [Interactive dashboard](../research/download-failures-2026-11-19/index.html) · [CSV](../research/download-failures-2026-11-19/failed-links.csv) · [Readable report](../research/download-failures-2026-11-19/failed-links.md)

Use the coordinator’s latest closed disposition export for the same selected recording IDs, creator channels and formats. The failure report reads that export and local Drive receipt journals. A dated output folder keeps the HTML dashboard, Markdown report and CSV together. All three use ordinary public watch links. The CSV records the last attempt start and last provider refusal separately. The dashboard opens offline and filters by creator or reason. [Register generator](collection_failure_report.py) · [Dashboard renderer](collection_failure_dashboard.py)

```powershell
python -m pipeline.collection_failure_report --root $archiveRoot --selection $selectionFile --dispositions $closedDispositions --out $reportFolder
python -m pipeline.collection_coverage --root $archiveRoot --selection $selectionFile --dispositions $closedDispositions --out $coverageFile --activity-csv $creatorsCsv
```

## After the last audio receipt

1. Reconcile the complete selection, archive the final recording index and creator table on Drive, then close the audio run in the README and handoff. Keep the 20-record cohort available as its own research sample. The portable catalog export retains earlier memberships, original upload days and the private recording references. [Metadata exporter](selection_catalog_export.py)
2. Use the saved English captions and publisher documents first. Run GPU speech recognition only for missing usable text in an isolated environment. For a non-English recording, preserve the original transcript and an English translation. Target 70% rolling GPU utilization and record observed utilization. Keep an edition-specific timeline for each text.
3. Have the first panel study coverage, word and expression matches, TF–IDF, topic and embedding clusters, publication-time changes, and cross-creator descriptions of the same event or claimed source. Export creator-normalized tables, plots, networks and heatmaps with denominators and underlying evidence.
4. Give the second panel the first panel's findings, source excerpts and uncertainty estimates. Challenge candidate clusters, shared-event matches and prediction dates. Evaluate rival explanations. Turn documented proposed measurements and experimental setups into testable questions, keeping speakers' claims distinct from independent evidence. Publish reviewed aggregates with a reproducible snapshot and update all dashboards together. [Analysis plan](../research/analysis-plan-2026-11-16/README.md) · [Cross-creator event register](../research/cross-channel-events-2026-11-16.md)
5. Release latest-50 acquisition after the latest-20+ translations and both analysis rounds are complete. Refresh the listings at that point and recalculate the expected work. Older catalog history remains a separate indexing phase.

The dated selection has 1,272 exact publication days and 704 approximate or unknown days. For an independent upload-quarter comparison, give `pipeline.postrun_candidates` the final metadata ZIP and its receipt hash using `--upload-catalog` and `--upload-catalog-sha256`. With `--figures`, both timelines get their own heatmaps and CSVs. Conflicting upload observations stay undated. The result counts recordings where upload and publication fall in different quarters. [Calendar reader](episode_upload_calendar.py) · [Lexical analysis](CORPUS_GROUP_LEXICAL.md) · [Cross-creator passage retrieval](CORPUS_SEMANTIC_RETRIEVAL.md)

## Latest-50 forecast

Plan for **22–28 hours of audio acquisition from the eventual start**. The November 19 snapshot contained 101 creators. Eight displayed lists ended within the observed pages. For the other channels, the upper scenario fills every available position up to 50. The forecast credits the 1,976 latest-20+ recordings once that cohort finishes and 34 already verified beyond those ranks.

| Evidence for a future roster | Total regular recordings | Additional downloads | Hours at 100.6 verified recordings per hour |
| --- | ---: | ---: | ---: |
| Public positions already visible on saved pages | 2,934 | 924 | 9.2 for this observed subset |
| Saved pages plus older ranks behind matching video IDs | 4,241 | 2,231 | 22.2 |
| All continuing channels reach 50 | 4,785 | 2,775 | 27.6 |

The rate uses the change from 1,436 verified recordings at 19:23 UTC to 1,784 at 22:51 UTC on the same selection. Three non-overlapping intervals of roughly one hour produced 89.5, 97.9 and 110.2 recordings per hour. Applying the slowest and fastest of those to the two planning workloads gives about 20–31 hours. Later uploads, removed recordings, changes in running time and unavailable sources can shift the result. The prior study's translation and review time precedes that clock. The forecasting command uses only saved indexes and receipt journals and creates a private per-creator report. [Forecast code](regular_fifty_forecast.py)

At 23:18 UTC, the entire latest-20+ selection represented 874.4 hours. The 214 recordings with confirmed English text accounted for 116.9 hours. Of the remaining 757.5 hours, an English-only worker previously processed 25.8 hours at 29.8 times real time, while a multilingual worker processed 4.65 hours at 8.35 times real time. If three quarters of the outstanding hours follow the faster English path, the resulting scenario is about 42 worker-hours. A half-and-half mix gives 58 hours. These are speech-processing scenarios. Input transfers, subsequently discovered captions, language mix, review and both analysis rounds also affect the start of the latest 50.

For the coordinated dashboard release, pass the per-creator forecast to `pipeline.collection_eta` using `--latest50-forecast` alongside the usual `--coverage-checkpoint` arguments. The public output contains aggregate download hours and the study prerequisite.

The archive's scheduling record binds this dependency to its exact latest-20 selection. Single-queue and multi-stage Windows launches check it before starting the latest-50 media phase. Planning remains available. At study completion, the research lead records the final corpus generation and two distinct panel reports using `python -m pipeline.study_schedule --root $archiveRoot finish --generation $generation --first-panel $firstReport --second-panel $secondReport`. Each spoken recording needs a primary English text, and a selected ASR translation needs its original-language transcript. A reviewed non-speech recording can be documented with `--non-speech`. The resulting receipt identifies the study artifacts that released the queue. [Schedule and release code](study_schedule.py)

## Preparing the next 50

After the 20-recording cohort is complete, use a new dated private folder for the 50-recording sweep. From `et-channelers`, set `$archiveRoot` to the private root, `$channelRoster` to the same creator manifest, `$previousSelection` to the completed 20-recording selection JSON and `$sweep` to the new folder.

```powershell
python -m pipeline.collect_regular_videos fetch --root $archiveRoot --channels $channelRoster --out $sweep
python -m pipeline.collect_regular_videos index --root $archiveRoot --channels $channelRoster --out $sweep --per-channel 50
python -m pipeline.extend_regular_video_grid --root $archiveRoot --base (Join-Path $sweep 'fresh-videos-50.json') --out (Join-Path $sweep 'public-50.json')
python -m pipeline.prepare_regular_fifty --root $archiveRoot --previous $previousSelection --fresh (Join-Path $sweep 'public-50.json') --out (Join-Path $sweep 'work')
```

The planner reads the local Drive receipts once. It checks that the preceding cohort is complete and that every creator supplied 50 public regular uploads or reached the end of their Videos tab. It writes the new membership to `work/selection.json` and the outstanding downloads to `work/pending.csv`. The queue interleaves creators by publication rank. Previously saved recordings are reused even when their rank has changed. The old selection and its historical Shorts and streams remain available for later comparison. [Queue planner](prepare_regular_fifty.py)

From `et-channelers`, preview and run that exact queue with the fifty-recording rank limit. Each phase reads the same CSV. The default rank limit for other single-queue runs remains twenty.

```powershell
$pendingCsv = Join-Path $sweep 'work/pending.csv'
& .\pipeline\start_drive_ingest.ps1 -Mode Plan -Newest 50 -Queue $pendingCsv -PrivateRoot $archiveRoot
& .\pipeline\start_drive_ingest.ps1 -Mode Run -Newest 50 -Queue $pendingCsv -PrivateRoot $archiveRoot
```
