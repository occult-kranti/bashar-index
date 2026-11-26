# Contacts of r4-P03

Times from `date -u`. Every read is of seen creators only; no hold-out, other-group or reliability file was opened, and no
recursive text search ran over the run folder.

| Time (UTC) | Contact | What |
|---|---|---|
| 2026-11-26T15:08:29Z to 15:10:21Z | `llm/creator-sets.json`, `prep.recordings()` (the run ledger), `prep.load_units` (seen transcripts, seen guard), `adapter.load_seen_bundle` (labels/seen, voice), the CROSS transcript pass (RX cue hits), `sync/edition_asr_manifest.jsonl` and `sync/drive_ingest_manifest.jsonl` (remote paths, sizes, SHA-256) | the outcome-free label extract (`common/code/extract_labels.py`); numbers only |
| 2026-11-26T15:11:42Z | `step0/split.private.json` (deposit 2's split) | outcome-free eligibility (`common/code/eligibility_audio.py`) |
| 2026-11-26T15:18:12Z to 15:24:47Z | Google Drive (rclone): four development creators' seen recordings, copied, checked by SHA-256, decoded and deleted | development test of the instrument (tuning pool T only; deleted before the pass) |
| 2026-11-26T15:28:00Z to 2026-11-26T17:58:03Z | Google Drive (rclone): every seen recording in the pass, one at a time (at most 2 local files), each checked by SHA-256 against the run ledger, decoded in memory and deleted | the acoustic pass (`common/code/pass_audio.py`) under `run_locked.sh` |
| 2026-11-26T17:59:31Z to 18:05:13Z (run and rerun) | `audio/private/features/` (the pass's private summaries), the label extract, `step0/split.private.json`; for r3-P08 also rv-R3's bridge pairs and BR-GS's grid-shift re-decode (seen, through step 1's `p01common` loaders) | this entry's analysis |
| 2026-11-26T19:12:55Z to 19:13:10Z | `audio/private/features/` (the pass's private summaries), the label extract, `step0/split.private.json` | rerun of this entry's code under the lead's decision 109 (the fix pass after the independent privacy check; no number changed) |
| 2026-11-26T19:49:25Z to 19:49:39Z | `audio/private/features/` (the pass's private summaries), the label extract, `step0/split.private.json` | rerun of this entry's code under the lead's decision 112 (CSV header lines only; no number changed) |

No model or API call; no GPU lease was taken (no GPU work); nothing was installed; no git commit.

Exploratory; not a test of H1-H10. No measure in this study can tell whether a non-human source speaks; every measure
describes the speech in these recordings and how the creators present it.
