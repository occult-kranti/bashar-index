# Pre-analysis checkpoint

**The owner paused the remaining downloads on November 20, 2026 at 01:45 UTC** (November 19 at 8:45 p.m. in New York). The frozen latest-20+ selection contains 1,976 regular recordings from 101 channels. Drive receipts verify 1,946 audio and provenance pairs. The remaining 30 stay in the selection. [Private Drive checkpoint](https://drive.google.com/drive/folders/1tHjfDYrMA-WDUKG4ajLyvHRnKP56JBdJ) · [Copy-ready handoff](CONTINUE_IN_NEW_CHAT.md)

## What is in the archive

| At the pause | Count | Evidence |
| --- | ---: | --- |
| Selected recordings with a verified audio edition | 1,946 of 1,976 (98.5%) | 1,304 original-track YouTube editions, 464 other verified YouTube editions and 178 matched publisher editions. [Recording-level CSV](evidence/2026-11-20-close/recording-status.csv) |
| Channels with every available selection archived | 80 of 101 | Each channel contributes up to 20 regular Videos-tab uploads. Five channels had fewer than 20 available. [Creator-level CSV](evidence/2026-11-20-close/creator-status.csv) |
| Outstanding recordings | 30 across 21 channels | 29 selected-media requests returned HTTP 403. One recording stopped at metadata retrieval. [Failed links](evidence/2026-11-20-close/failed-links/failed-links.csv) · [Searchable table](evidence/2026-11-20-close/failed-links/index.html) |

The closed receipt register is timestamped 01:16:52 UTC. A second read at 01:41 UTC returned the same totals. The frozen selection file has SHA-256 `adb76d392fa9eded77e03fb41687a630fb82a17fb3de21af504092710b08fd01`. [Receipt checkpoint](evidence/2026-11-20-close/checkpoint.json)

At 01:56 UTC, a single Drive metadata listing confirmed the ID, path, byte count and MD5 of all 3,892 required audio and provenance objects. All 1,946 receipt-backed recordings passed. The audit used the SHA-256 recorded at acquisition and read zero media bytes. The per-object and per-recording results are in `archive/media-verification.zip` on the private Drive. [Verification totals and method](evidence/2026-11-20-close/drive-verification.json)

Two Dallisa Hocking listings share one creator-published audio file, each with its own association evidence. This accounts for the 1,945 distinct audio files across the 1,946 archived listings.

## Where to find the backup

| Location | Contents |
| --- | --- |
| [GitHub repository](https://github.com/occult-kranti/bashar-index) | Published source code, dashboards, public metadata tables, attempt history, research plans and operator documentation. [Dashboard directory](https://occult-kranti.github.io/bashar-index/dashboards/) |
| [Private Drive checkpoint](https://drive.google.com/drive/folders/1tHjfDYrMA-WDUKG4ajLyvHRnKP56JBdJ) | `repository/main.zip` contains the tracked files at the commit recorded in `MANIFEST.json`. The Git bundle preserves the published branches and their history. The folder also holds readable copies of the handoff and project documents. |
| `archive/` inside the Drive checkpoint | The private records ZIP carries the frozen selection, recording dispositions, catalog metadata, caption and transcript inventories, publisher evidence, receipt records and Windows pause state. Its `CONTENTS.json` records each member’s size and SHA-256. The portable catalog keeps its original preview date. |
| [Private media archive](https://drive.google.com/drive/folders/1pMBEavFcXc3BrDbg0BqW0mKkpyOHjD_B) | Audio, per-edition provenance, saved captions and earlier speech results retain their existing Drive objects. Individual receipt IDs identify the same files across checkpoints. |
| Drive checkpoint manifest and verification receipt | `MANIFEST.json` identifies the Git revision and expected sizes, MD5 and SHA-256 values. `VERIFIED.json` records the observed Drive IDs, sizes and MD5 values for the uploaded checkpoint. |

## Where the next chat starts

The Windows archive has the collector’s `sync/STOP_ROLLING_PUBLIC_INTAKE` marker and a dated record of the 15 download wake-up tasks disabled at the pause. All rolling wake-ups were disabled and no source worker was transferring audio. Keep the outstanding IDs and the stop in place until the owner asks to resume. A completion ETA is unavailable during the pause. [Operator guide](operations.md)

Full-batch transcription and analysis are pending. The current schedule releases local CUDA speech processing once all 1,976 recordings have verified audio and the collector has closed. Keep usable English captions and publisher transcripts, then fill speech gaps and translate non-English recordings locally. The study plan calls for a frozen text corpus, quantitative analysis and an independent review. Latest-50 collection follows translation and both reviews. [Roadmap](../ROADMAP.md) · [Study plan](../research/analysis-plan-2026-11-16/)
