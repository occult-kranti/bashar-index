# Drive-only caption-gap review, 17 November 2026

This review uses one already verified native recording and both saved English caption alternatives. It makes no YouTube request, changes no publisher text, and creates no full-recording transcript or collection completion.

| Measure | Observed result |
|---|---:|
| Rounded metadata duration | 4,518 seconds |
| Uncued intervals | 33, totalling 186.163 seconds |
| Merged VAD context | 288.983 planned seconds |
| Retained PCM RAM | At most 18.49 MB; no PCM file |
| Decoded source end | 4,517.5253125 seconds |
| Unreviewed declared tail | 0.4746875 seconds; not padded |
| VAD-positive time inside actual gaps | 4.459 seconds |
| CUDA recognition input including context | 32.459 seconds |
| Selected word candidates | 5, all unreviewed |

The source audio/metadata, both caption ZIPs, cue geometry, environment/model, worker and plan hashes are bound to the proposal and leases. The worker streams decoded audio while retaining only merged gap/context arrays. Existing CPU Silero preprocessing identifies candidate speech; recognition uses the pinned English Distil model on CUDA with `int8_float16`, one GPU owner and no CPU recognition fallback. Missing/failed telemetry holds work.

Candidate timing is estimated. One candidate has zero duration and two cross core boundaries. Three candidates exactly match nearby caption words; both boundary-crossing words overlap matching cues, while the zero-duration word matches nearby published text. The remaining two have no exact adjacent match and include a low-probability estimate. Spelling and attributed identities remain unresolved. **No missing words are confirmed.** Absence of VAD speech is not validated silence or every-word coverage.

The brief inference produced only three telemetry samples: observed mean 33.3%, instantaneous peak 100%, peak VRAM 1,462,464,512 bytes and maximum temperature 58 C. The 70% governor is a soft pacing target. These samples do not establish a full 30-second utilization window or an instantaneous ceiling. GPU ownership was released after the run.

The [7,069-byte review bundle](https://drive.google.com/file/d/1vqRXYYLXWon_iRr275SrVonE5XqtpyNZ/view) and [86,496-byte runtime/provenance supplement](https://drive.google.com/file/d/1kPvjy-yDSakPCJoWFdpO7AVS6ur1PNKO/view) are verified by exact Drive IDs, sizes and MD5, with local SHA-256 receipts. Only the 72,248,693 bytes of newly owned input copies were removed after proof. Original published captions, result bundles and audit history remain. The separate review manifest is excluded from ordinary ASR and caption-completion counts.

The [byte-exact executed worker](../pipeline/caption_gap_review.py) and [execution contract](../pipeline/CAPTION_GAP_REVIEW.md) are published for reproducibility. Current text availability is 44 of the 47 archived audio items; 42 meet text-inventory checks, two have saved text with pending inventory review, and three remain on existing nonlexical/language/speech holds. This does not resolve the blocked acquisition of the remaining newest-20 videos.
