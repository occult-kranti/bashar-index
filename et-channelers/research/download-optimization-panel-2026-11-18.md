# Batch download optimization panel, November 18

The immediate job is the frozen latest-20 audio queue, with metadata and available English text. Speech-to-text remains paused. At the receipt checkpoint after the first completed recovery frame and its partial successor, **270 selected recordings** have paired Drive proofs: 240 YouTube originals and 30 additional publisher editions; 136 have saved text. A final worker result describes acquisition, not upload status: canonical Drive receipts determine the saved count.

## Ownership and evidence

The download lead owns the finite queue, resource accounting and runtime supervision. The transport engineer owns isolated code and its portable repository package. The fallback lead owns publisher feeds, progressive audio extraction and caption research. The integration lead owns dashboard data, ETA, source comparison and release. Changes to an active downloader's files are excluded from experiments.

The measured 20-decision download-only run took 435.24 seconds, including startup, metadata, source transfer, upload and closure: 15 verified recordings and five local holds. Its first-pass planning range is approximately 7–14 active hours for a similarly sized remaining queue, including possible held decisions. It does not establish a calendar finish or successful audio for every item.

A separate metadata-only measurement found a private capacity scan took 1.169 seconds over 2,605 directories and 11,489 files. This is a filesystem measurement, not a network speed test. The implemented optimization caches partition accounting for at most 12 seconds and reconciles it when slots or publication state change. Stop controls, code/lease checks and physical spare remain immediate. Per-write audio accounting was already constant-time; it was not the measured bottleneck.

## Options and next experiments

| Option | Evidence and use | Decision |
|---|---|---|
| Existing yt-dlp + isolated Chromium/WPC | Full native audio and paired metadata have been verified in Drive. Current work focuses on scheduling and error isolation. | Primary route; retain working versions during a run. |
| More video workers | Fixed worst-case audio and browser reservations constrain concurrency. | Prototype metadata-first admission: start with a bounded bootstrap reservation, then enforce and reserve the selected size before media transfer. Measure before raising the worker ceiling. |
| Fragment concurrency | yt-dlp documents `-N` for DASH/HLS fragments. | It does not increase concurrency for the current plain-HTTPS files. [yt-dlp options](https://github.com/yt-dlp/yt-dlp#download-options) |
| Progressive MP4 → AAC stream copy | A held item's saved inventory offered progressive format 18 with AAC even though audio-only HTTPS was absent. FFmpeg supports copying streams without decoding/re-encoding. | Isolated prototype; require source completeness and matching audio packet hashes/counts. Track identity stays qualified where unproven. [FFmpeg streamcopy](https://ffmpeg.org/ffmpeg.html#Streamcopy) |
| Reuse an owned browser process | Repeated browser startup is a candidate cost. PO tokens are content-bound. | Reuse a process only with fresh correctly bound requests; never assume one token works for the whole queue. [PO-token guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide) |
| English captions through WPC | Current 1.1.2 code explicitly supports Subs as well as GVS/Player, although its README omits Subs. | Separate caption lane with its own observations, English selection and endpoint holds; no new ASR. [Provider code](https://github.com/coletdjnz/yt-dlp-getpot-wpc/blob/main/yt_dlp_plugins/extractor/getpot_wpc.py) |
| YouTube.js / googlevideo SABR | Primary projects provide InnerTube and SABR/UMP tooling. The checked googlevideo release is 5.0.1, already present locally. Earlier project trials produced an incomplete prefix. | Compatibility research, not a claimed full-file fix. [YouTube.js](https://github.com/LuanRT/YouTube.js), [googlevideo](https://github.com/LuanRT/googlevideo/releases) |
| pytubefix | Its source documents progressive/DASH streams and caption support. | Candidate isolated extractor comparison; published capability is not live acceptance proof. [Project documentation](https://github.com/JuanBindez/pytubefix/blob/main/docs/index.rst) |
| aria2 HTTP ranges | Parallel connections are supported subject to split and server settings. | Benchmark only larger eligible files, with bound headers and complete nonoverlapping range coverage. Small-file startup may dominate. [aria2 manual](https://aria2.github.io/manual/en/html/aria2c.html) |
| Publisher RSS / official sites | Two more official-feed editions were fully archived. Other feeds delegated through normal CDN redirects. | Preserve publisher-edition labels; archive uncertain associations separately. Normal redirects are not HTTP quota refusals. |
| Extensions / tab recording | The project has isolated inspection/filtering evidence. Recording requires playback and changes the artifact. | Inspection aid; it is not the batch acquisition path. No claim that an ad blocker repairs a streaming protocol. |
| Persistent or larger upload batches | Rclone documents connection/buffer tradeoffs and avoiding unnecessary destination traversal. | Measure upload wait, startup and listing time first; preserve exact Drive size/MD5/ID proof before deletion. [Rclone performance](https://rclone.org/docs/#performance) |

## Failure handling and crawling

A valid final worker result can exist without a progress file. The controller must use final diagnostics and preserve any HTTP evidence before releasing a slot. Known, measured parent-enforced deadlines are being isolated through separate parent-censored records: no invented success, zero-request claim, streak reset or automatic retry. Unknown crashes, control-write failures, ownership failures and actual global source holds remain review conditions.

The crawler should retain distinct listing, attempted, available-audio and saved-text inventories. Incremental channel listings can discover new IDs after the frozen queue completes; metadata presence must never be mistaken for a downloaded-audio receipt. Preserve video/Shorts/live categories, source dates and stable IDs. Dashboard checkpoints can validate their generated JSON/CSV consistency without repeating the full Python suite when no code changes.

The experiment log should record input scope, exact versions, requests, bytes, elapsed phases, temporary-space peaks, validated completions and failure class. A new library or extension is promoted only after a complete file and its archive proof, not after a successful metadata request or short prefix.
