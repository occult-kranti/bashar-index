# Acquisition checkpoint — 19 November 2026, 00:52 UTC

The saved-audio checkpoint contains **1,145 of 1,420 selected videos** across 74 creators: 1,108 native YouTube recordings and 37 publisher editions. There are 136 videos with an audio edition and saved text. Qualified YouTube audio editions currently contribute zero. The per-creator goal remains open: 74 × 20 requires 1,480 slots, so 275 selected recordings and 60 selection slots remain unresolved.

## Verified work

- The last native batch archived 13 recordings from 14 attempts in 539.12 seconds. Its processes and 4.8 GB reservation are closed. The preceding batch archived 208 recordings from 253 attempts.
- An owned Chromium trial confirmed a local connection bug: the permission guard rejected nodriver's lowercase `get` method. The corrected guard accepts that spelling and passes the original method unchanged. The subsequent YouTube trial completed browser startup and token generation once each.
- That trial saved zero audio. YouTube declared audio-only formats in its raw response, while the processed format list exposed an MP4 recording and storyboards. A raw audio-format declaration therefore establishes no usable direct download URL. The fresh response, actual metadata traffic, closed jobs and released 650 MB reservation are retained separately.
- A metadata batch archived **16 rich metadata records, 33 files and 10,764,239 bytes**. One copy operation and one stat operation established matching remote MD5, size and distinct Drive IDs for every file. Its separate receipt is durable; the uploader exited cleanly and released its 64 MB reservation. These records add zero audio or transcript coverage. Originals and sanitized staging files remain available.
- [PR #70](https://github.com/occult-kranti/bashar-index/pull/70) published the terminal audio checkpoint. [PR #71](https://github.com/occult-kranti/bashar-index/pull/71) refreshed the upload timeline and made its saved flags recognize paired qualified YouTube editions. Both exact-head checks and Pages deployments passed. Their branches are retained.

## Next acquisition work

Prepare a bounded MP4 download followed by audio stream-copy extraction with the existing preservation verifier. A response-sized file must retain the distinction between an unknown metadata filesize and the actual response Content-Length. Full transfer, audio preservation, paired Drive receipts and owned-process closure remain required. Original-track and spoken-language uncertainty remain explicit.

Four other cached audio-only declarations remain metadata leads. Their current processed URL availability needs evidence before scheduling transfers. A proposed compressed metadata bundle will preserve per-video paths, member hashes and provenance while reducing Drive object operations; it has not been uploaded.

Transcription remains paused. Managed local storage stays below 16 GB with at least 2 GB physical spare. Download, upload and preparation work have dedicated owners, and held attempts remain recorded.

## ETA and links

The completed native batch achieved about 87 saved recordings per hour. At that rate, 275 eligible recordings would require approximately 3 hours 10 minutes. Format recovery, provider holds and the 60 missing selection slots prevent assigning that duration as an overall completion date.

- [Dashboard hub](https://occult-kranti.github.io/bashar-index/dashboards/)
- [Downloads, creator counts and ETA](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/collection/)
- [Selected-video timeline](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/collection/timeline.html)
- [Predictions](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/predictions.html)
- [Channel index](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/)
- [Channeling Atlas](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/)
- [Entity directory](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/#/entities)
- [Analysis report](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/analysis/report.html)
- [Bashar Index](https://occult-kranti.github.io/bashar-index/)

The [creator coverage CSV](../plan/channel_download_coverage.csv) and [saved-video CSV](../plan/downloaded_videos.csv) contain dated receipt snapshots. The timeline now reconciles its 1,145 saved flags against the same audio snapshot; its exact, estimated and unknown upload-date labels remain visible.
