# Windows operator handoff

## Read the current state

The November 20 ordinary queue and its two supported recovery cases have finished. The [last recording and creator totals](evidence/2026-11-20-close/) give the precise starting point for a follow-up. The dated work area described below remains available for reconciling newly verified receipts.

Run the following from the repository’s `et-channelers` directory. On the configured Windows host, the private workspace and installed tools live alongside the checkout under the operator’s profile. Progress queries read saved receipts and selection membership. They can run while a download is active. [Coverage reader](../pipeline/collection_coverage.py) · [Failure definitions](../pipeline/COLLECTION_PROCESS.md#unresolved-downloads)

```powershell
$toolsRoot = Join-Path $env:USERPROFILE 'et-channelers-tools'
$archiveRoot = Join-Path $env:USERPROFILE 'et-channelers-private'
$python = Join-Path $toolsRoot 'venv/Scripts/python.exe'
$selection = Join-Path $archiveRoot 'provisioning/expanded-regular-20261119-v9/selection/selection.json'
$coverage = Join-Path $toolsRoot 'latest20-handoff-coverage.json'
$creators = Join-Path $toolsRoot 'latest20-handoff-creators.csv'
& $python -B -m pipeline.collection_coverage --root $archiveRoot --selection $selection --out $coverage --activity-csv $creators
Get-ScheduledTask -TaskName 'ETChannelers-Latest20-*' | Select-Object TaskName, State
& $python -B -m pipeline.research_agent_schedule --root $archiveRoot status
```

The selection SHA-256 is `adb76d392fa9eded77e03fb41687a630fb82a17fb3de21af504092710b08fd01`. Always read the creator and video together. A retry, a second edition, a metadata-only bundle, a declared caption, and a closed source job each have their own meaning. See the [evidence dictionary](evidence/README.md) before comparing snapshots.

## What runs where

| Owner | Input and responsibility | Handoff evidence |
| --- | --- | --- |
| Roster and listing | A reviewed channel ID, its public Videos tab and observed listing order. Carry earlier Shorts, streams and selections forward. | Frozen primary creator/video membership, listing exhaustion and additive catalog. [Selection code](../pipeline/collect_regular_videos.py) |
| Audio collection | One rolling coordinator owns a source batch at a time. During this run it admits six source workers, two staggered browser starts and eight outstanding recordings under one capacity reservation. | Complete local bytes, creator identity, edition-specific quality checks and closed acquisition records. [Production history](production-history.md) |
| Independent publisher matching | Exact recording links or reconciled episode, publisher, guest, date and duration evidence. Preserve ambiguous and negative matches. | A separate publisher edition, a text companion or an unresolved lead. [Publisher research](../research/publisher-mirrors-2026-11-17.md) |
| Drive publisher | Three concurrent transfers. Group eligible audio/sidecar pairs, check remote IDs, bytes and MD5 together, and write each pair’s own receipt. | Each verified pair permits retirement of its owned local copy. Complete files from interrupted batches can enter quality review and publication locally. [Grouped publisher](../pipeline/native_grouped_publication.py) |
| Local speech and translation | After all audio receipts and collector closure, recover existing usable English text; the isolated CUDA worker handles missing text. Non-English speech produces the original transcript and an English translation. | Per-edition text receipts, source timestamps, checkpointed long recordings and individually reviewed exceptions. [CUDA runbook](../pipeline/GPU_ASR_SETUP.md) |
| Analysis and research panels | Method and source review after complete audio; subsequent statistical and replication reviewers use the frozen English corpus, numerical results and source evidence. | Generation manifest, individual panel results and shared budget ledger. [Research scheduler](../pipeline/PROJECT_RESEARCH_AGENTS.md) |

The working-file limit is **23 decimal GB** across managed directories. The allocator also keeps **12 GB physically free** after reservations. Source reads and Drive transfers use network and disk. GPU inference uses a 70% rolling utilization target; instantaneous peaks can be higher. The four-transfer experiment measured 2.23 MB/s against a size-matched three-transfer group at 2.27 MB/s. Three remains the production setting. [Measurements and workload differences](production-history.md)

## Drive and recovery

The configured remote is `etdrive:`, rooted at the owner’s ET Channelers Archive. The owner selected a Desktop OAuth client in their own Google project, enabled the Drive API, added the archive account as a tester and kept the app in Testing. If authentication expires, reconnect this remote interactively. The client JSON and rclone configuration stay on the operator’s machine. Use a remote probe at setup or after a connection fault. Rechecking the whole remote after every file would duplicate the batch receipt work. [Windows Drive configuration](../pipeline/WINDOWS_DRIVE.md)

```powershell
$rclone = Join-Path $toolsRoot 'rclone.exe'
& $rclone listremotes
& $rclone lsf 'etdrive:' --dirs-only --max-depth 1
```

| Observation | Operator action |
| --- | --- |
| A job appears slow | Compare the last completed source and publication stages and the age of the oldest ready file. Check physical disk and committed memory before changing concurrency. |
| A provider rejects one item or sends a retry time | Record the exact item and outcome. Continue eligible recordings and check documented creator-owned sources. A publisher title or preview still needs a full-edition match. |
| A worker ended with a partial file or missing final report | Preserve the item and its observed bytes until reconciliation. Consult the saved disposition before placing reuse or further work in the queue. |
| Complete audio exists locally without a remote pair | Reuse the complete file after quality and identity validation; batch upload it with provenance. Verify the remote pair before retirement. |
| The queue reports no eligible work while some recordings lack receipts | Report the outstanding IDs and reasons. The ASR, paid research and latest-50 dependencies still require the applicable completion receipts. |
| Windows restarted | Inspect registered tasks, existing owner, reservations and latest closed journals before resuming the established coordinator. The text and research tasks recover their own states. |

## Completing the study

1. Reconcile all 1,976 primary IDs and each creator’s selected extent. Save the final manifests, failed-link table and creator counts. Publish the coordinated dashboard update after the run.
2. Stage archived English published captions, original English automatic captions and eligible publisher transcripts. Run local transcription only where usable English text is missing. Preserve the original and translation for a non-English recording. A reviewed non-speech recording has its own audio-bound evidence.
3. Freeze a versioned text collection with the creator, recording ID, edition, spoken language, text provenance and source spans. Compare creator-balanced TF–IDF, clustering stability, cross-creator passages and shared-event candidates. Publish sample sizes, sensitivity checks and denominators with the tables and figures.
4. Report predictions with separately attributable statement and event dates. Treat discussions of healing, frequencies, hypotheses or experimental designs as attributed claims; keep proposed measurements, observed results and independent evidence distinct. Have a second panel challenge the first panel’s results.
5. Release the latest-50 queue after translation and both analysis rounds. Refresh the Videos listings first and reuse verified recordings. The provisional estimate is **22–28 download hours after release** for 2,231–2,775 additional recordings, with a measured-rate sensitivity range of 20–31 hours. Prior transcription, review, unavailable recordings and later channel uploads affect the calendar date. [Queues, assumptions and commands](../pipeline/COLLECTION_PROCESS.md#preparing-the-next-50)

The project API key finances text research. All six planned calls share a $100 ceiling. The running Codex session and its built-in agents use the session’s billing. The project research dispatcher reads the key from its private file when a paid task becomes eligible. [Budget and recovery](../pipeline/PROJECT_RESEARCH_AGENTS.md)
