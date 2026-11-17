# Native download panel: maintained-client integration, round 1

Reviewed 2026-11-17. No YouTube, media, browser navigation, Drive or GPU requests were made. This is an offline implementation/research checkpoint, not source acceptance.

The strongest concrete finding is a missing timing precondition in our custom direct-HTTPS transport. It is independent of the recorded SABR protection failures. The next falsifiable candidate is the supported upstream yt-dlp full-file downloader and unmodified WPC provider in the same owned browser lifetime, with those preconditions intact. It remains unproven and requires the coordinator's exact one-attempt source admission.

## Local evidence and repair

Installed versions were read locally: yt-dlp 2026.11.16.232655dev, yt-dlp-ejs 0.8.0, Deno 2.9.8, yt-dlp-getpot-wpc 1.1.2, bgutil-ytdlp-pot-provider 2.0.2. Deno is correctly detected by yt-dlp through Python's scripts directory even though it is absent from the shell PATH. A generic reinstall is not a supported diagnosis.

The installed YouTube extractor sets selected-format `available_at` from preroll availability. Upstream `FileDownloader.download` applies the maximum timestamp from `requested_formats` or the selected info dictionary before downloading. Our `extract_info(download=False)` and CLI metadata paths skip that downloader step, then `drive_ingest.stream_audio` previously issued its first GET immediately. The format field already survives extraction; the missing behavior was in the transport.

The narrow repair now honors that same selected-format scope, validates timestamps, waits at most 30 seconds with frequent STOP checks, and rechecks storage admission before GET. Longer waits create `deferred_availability` with `availability_retry_not_before_epoch`; this is an item-specific retry time, not the shared source-refusal cooldown. Restart before that deadline performs no extraction. Browser lifetime cleanup remains in the existing finally block. No skip-ad-context option was enabled.

Offline validation: 18 availability/browser-lifetime tests passed. The tests prove zero media GETs before the deadline, early STOP, invalid metadata rejection, deferred retry persistence, storage recheck, exact extraction propagation and browser cleanup. This does not establish why any previous HTTP403 or SABR plateau occurred.

Primary implementations: [extractor](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/youtube/_video.py), [downloader](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/downloader/common.py). Local reviewed locations: extractor lines 2696, 2948, 3595 and 3826; downloader lines 464–470.

## Maintained paths compared

| Path | Current evidence | Decision |
|---|---|---|
| yt-dlp SABR PR | PR13515 remains open; its maintainer release still points to 2026-10-27, already attempted here. It documents audio-only and resume support, but does not implement rate-limit or fragment concurrency. | Not a new fix or a ready replacement for the bounded collector. [PR13515](https://github.com/yt-dlp/yt-dlp/pull/13515) |
| YTSE plugin | Its maintainer removed the early SABR downloader; current plugin exposes UMP experiments. | Do not mistake an old plugin installation for new SABR capability. [Maintainer repository](https://github.com/coletdjnz/yt-dlp-ytse) |
| EJS | Runtime and scripts are already installed and locally detected. EJS solves player JavaScript tasks; that does not prove a media session is accepted. | Retain the pinned working pair; no speculative upgrade. [EJS guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS) |
| WPC provider | Official featured alternative uses the real WebPoClient in a browser. Installed default is headful, selects the configured executable, creates a distinct temporary profile and keeps it until provider close. Current project browser_audio overrides that default with headless=True. | A stock WPC + upstream downloader candidate is materially different from our patched headless/custom-transport path, but acceptance is unknown. [Guide](https://github.com/yt-dlp/yt-dlp/wiki/Po-Token-Guide), [provider code](https://github.com/coletdjnz/yt-dlp-getpot-wpc/blob/main/yt_dlp_plugins/extractor/getpot_wpc.py) |
| use_ad_playback_context | Present in the installed code; documented as effective only for mweb/web_music. It changes the requested ad context, not the SABR protection result. | Do not enable by default; honor supplied availability instead. [Extractor arguments](https://github.com/yt-dlp/yt-dlp#extractor-arguments) |
| Chrome downloads API | Supports ordinary URL downloads/resume and hostname cookies. It does not turn a SABR endpoint into a complete-file URL or supply protocol assembly. | Not a solution where the observed player exposes no direct URL. [Chrome documentation](https://developer.chrome.com/docs/extensions/reference/api/downloads) |

## Smallest next candidate and controls

Use the existing Python environment, explicitly pinned Deno executable and a private plugin directory containing only the byte-exact installed WPC provider. `--no-plugin-dirs --plugin-dirs <wpc-only>` was parsed offline and results in only that directory, preventing accidental bgutil fallback. Do not import browser_audio, which installs the custom headless override. Use the published WPC browser_path setting with the installed Chrome binary; the browser uses a new owned profile, never the user's profile. Do not copy cookies, alter browser fingerprints, use proxies, forge tokens, or change personal Chrome.

The full native API is `with YoutubeDL(options) as ydl: ydl.extract_info(exact_video_url, download=True)`. The ordinary downloader retains its own pre-download timing and complete-file handling. Options require one exact item, mweb, HTTPS audio-only, zero extractor/HTTP/fragment/file-access retries, 1 MiB chunks, 2 MiB/s, at most 64 MiB, private output, no automatic client fallback, no subtitle fetch, no raw trace logs and no source URI/token export. The return value stays private for later sanitized metadata/proof creation.

Important limit: retry=0 does not bound ordinary Chrome bootstrap traffic. WPC itself can poll client readiness ten times with one-second waits. A real trial therefore requires a reviewed harness that independently enforces one attempt, a finite bootstrap deadline, the media/spool cap and a total browser+metadata/media request budget. A tentative ceiling is 250 source requests, including at most about 64 successful 1 MiB media ranges for an admitted 64 MiB known-length file. These are proposed ceilings, not measurements or guarantees. Pipeline owner is independently reviewing that harness. Watch/player/media403,429 or explicit protection rejection must terminate without fallback or re-minting loops.

The current 24-hour source deadline is our operator policy attached to the actual 2026-11-17 07:31:07Z SPS3 event; the receipt contains no provider Retry-After. Preserve that record unchanged. Any materially changed one-item trial needs an explicit separate admission; this report grants none. Success still requires complete native bytes, verified audio-only format/full duration, exact hashes and durable Drive proof before cleanup.

## Cross-critique of SDK lane

The independent SDK audit found googlevideo5.0.1 matches the vendored source; audio-only restore guards and modern protobuf fields are already present. The V5 trace advanced its playhead and buffer to69.892 seconds while receiving51HTTP200/SPS2 responses. V6 observed SPS3 in ordinary playback before custom BEGIN. Therefore old PR54/restore/playhead patches are not new source-acceptance fixes. Our availability correction concerns direct HTTPS, not those SABR traces.

The adapter callback named onMintPoToken currently returns the once-captured token clone; its name alone does not establish a fresh accepted token. This is a conditional lifetime limitation worth preserving in the design record, not evidence explaining the old failure and not permission to change attestation. A future normal-browser SABR admission still needs fresh same-video SPS1 proof, not just HTTP200 or token presence.
