# Reading and reproducing the attempt evidence

The [01:16 UTC close of eligible work](2026-11-20-close/) is the most recent snapshot. It includes 1,946 verified recordings, 2,913 attempt observations, a 30-recording failure register and publisher follow-up. The 00:51 UTC snapshot below preserves the preceding state.

The November 20 directory is a dated export. Its two units are a **selected recording** and a **retained evidence record**. A recording can have several attempt markers and one accepted audio edition. A single marker can describe a stage that made zero network requests. The number of rows in the attempt register therefore cannot be used as the number of HTTP requests or downloads.

| File | Unit and interpretation |
| --- | --- |
| [checkpoint.json](2026-11-20/checkpoint.json) | UTC cutoff, selection and disposition digests, creator and recording coverage, marker inventory, work areas and date evidence. |
| [creator-status.csv](2026-11-20/creator-status.csv) | One row per selected channel. Verified, outstanding and source-edition counts reconcile to that channel’s selected extent. An eligible row can already belong to a running batch. |
| [recording-status.csv](2026-11-20/recording-status.csv) | One stable creator/video identity, ordinary watch URL, status from the closed snapshot, verified edition and number of retained attempt records. |
| [attempt-history.csv](2026-11-20/attempt-history.csv) | Deduplicated evidence from closed batches and retained attempt markers. The evidence ID is the SHA-256 of the marker or, where no individual marker survived, a digest of the closed observation and its position. |
| [attempt-summary.csv](2026-11-20/attempt-summary.csv) | Counts from the attempt register grouped by work area and recorded outcome. |
| [Earlier failed-link report](../../research/download-failures-2026-11-19/failed-links.md) | Item-specific evidence for the earlier 23:25 UTC snapshot, with its own linked CSV and filterable dashboard. |

**Time.** `recorded_event_time` comes from a dated field in the evidence. `file_modified_time` is a local filesystem observation; it can move when files are copied. `unavailable` means the closed evidence supplied neither clock. The upload date of the video is a separate measure, shown in the [daily timeline](../../dashboard/collection/timeline.html).

**Importing IDs.** CSV cells use the project’s spreadsheet escaping. An ID beginning with a hyphen has a leading apostrophe in the raw CSV so a spreadsheet preserves it as text. For a programmatic join, read the `v` parameter of the accompanying watch URL or remove that single leading apostrophe before validating the eleven-character ID.

**Outcome.** HTTP status and body completion appear only where the private verifier or matching result supplied them. `terminal_outcome_unavailable` means the retained marker has no known terminal state. `other_recorded_outcome` means a state was retained without a finer public category. A failure can sit beside a later successful receipt for the same video. Use `audio_receipt_at_checkpoint` or `verified_audio` to answer whether audio was archived.

**Scope.** `current_regular` belongs to the 1,976-recording corpus. `retained_index` belongs to the larger union. `outside_or_unbound` preserves an observation whose identifier cannot be joined to that union. Only joined recordings receive public creator and watch links. Paths, authentication material, raw requests and unreviewed diagnostics remain in the private archive. Identical copies are collapsed by recording and evidence digest. Test fixtures are excluded. A historical aggregate can outlive its per-recording logs. The [research index](../research-index.md) and [production history](../production-history.md) cover those trials at their surviving level of detail.

## Reproduce

Supply the frozen selection, its private archive root and a matching closed disposition snapshot to the exporter. A new snapshot receives its own dated output directory. The command reads local evidence, validates the creator/video joins and receipt totals, and writes the five files above.

```powershell
& $python -B -m pipeline.collection_history --root $archiveRoot --selection $selection --snapshot $closedDispositions --out $reportFolder
```

The [exporter](../../pipeline/collection_history.py) and [regression tests](../../pipeline/tests/test_collection_history.py) document the matching, time and privacy rules. The [operator handoff](../operations.md) supplies the rest of the environment settings.
