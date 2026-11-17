# Research audio capture for the browser that already plays

This Chrome Manifest V3 extension records audio from explicitly activated YouTube tabs and streams it to the local archive service. It uses supported `chrome.tabCapture`; it does not retrieve signed media URLs or read/export cookies, credentials, or profiles. Output is **browser_recorded_audio**, re-encoded WebM/Opus at96kbps, with no native-source or accuracy claim.

## Load and use

1. Start the project's local capture service on `127.0.0.1:8768`. Its health endpoint is `http://127.0.0.1:8768/capture/v1/health`.
2. In the Chrome window where ordinary playback works, open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**, and select this `et-channelers/browser_capture_extension` directory. Pin **Channel Research Audio Capture** if convenient.
3. Open an eligible YouTube video, let ordinary playback work, and leave the video and tab unmuted. Click the extension button. Chrome requires this explicit user activation before a tab can be captured. The extension seeks to the beginning, records at1×, and preserves audio through the speakers.

Click again to stop that tab. Activate up to four tabs independently. Right-click the extension and open **Options** for status and **Stop all captures**. Keep Chrome and the activated tabs open. After a completed item passes local validation, the same activated tab can move to the next eligible `www.youtube.com/watch` job. No additional tabs are opened automatically. Changing origin revokes access and stops the worker.

Badges: **REC** recording; **BUF** source buffering/paused; **CHECK** local validation; **DONE** no eligible job; **ERR** held/error (hover for the constant reason). An ad, source change, unexpected seek/rate change, protected media, missing monitor signal, or uncertain chunk acknowledgement holds the recording. Resolve the cause before a new explicit activation; the extension does not silently retry a partial source. Starting a capture pauses/seeks the chosen video; stopping capture releases the tab stream and restores normal audio routing.

The package is implemented and fixture-tested. A real user-activated recording in the accepted browser context is still an acceptance gate; no complete archive item is claimed by the extension's offline tests.

## Identity and local service contract v1

Stable extension ID: `egndajoiodmfaakhopchlaikhpdjdcnb`.

Exact allowed Origin: `chrome-extension://egndajoiodmfaakhopchlaikhpdjdcnb`.

The manifest contains a public RSA key. Its private half was generated only in memory and discarded. This public key fixes the unpacked extension ID; it is not an authentication secret. The service also requires a paired bearer token. Tokens stay in extension session storage/offscreen memory, never in page messages, URLs, UI, or logs. Requests use `credentials:omit`, reject redirects, and target only the fixed loopback service.

| Endpoint | Request / response |
|---|---|
| GET `/capture/v1/health` | No bearer; health read only. |
| POST `/pair` | Exact extension Origin, empty JSON; returns `{token}`. |
| POST `/next` | Bearer; `{worker_id, video_id?}`; returns `{job}` or `{job:null}`. Current activated ID is prioritized initially. |
| POST `/start` | `{capture_id,video_id,duration_seconds,source_time,playback_rate:1,ads_detected:false,is_live:false,source_metadata}`; requires `{accepted:true}`. |
| POST `/chunk` | Binary body≤1MiB; bearer, `X-Capture-Id`, zero-based `X-Sequence`; requires matching `{accepted:true,sequence}`. |
| POST `/finish` | `{capture_id,video_id,source_duration,source_time,source_ended:true,coverage_intervals:[[start,end],...],ads_detected:false,playback_rate:1,media_mime_type}`; returns `{accepted:true,state}`. |
| POST `/status` | `{capture_id}`; local-only polling every2s while `state=validating`. `ready_for_upload` permits next job; `held` stops the worker. |
| POST `/abort` | `{capture_id,video_id,reason}`; constant reason; partial capture remains held. |

All endpoints except health/pair require the bearer. Control errors are constant codes. There are no ambiguous POST retries: a lost acknowledgement holds the capture. Local validation can take up to source-duration/3+120s; its worker waits and does not acquire another item meanwhile. Drive verification, disk admission, durable source receipts, and deletion are owned by the Python service, not this extension.

## Coverage and resource bounds

Each source begins at observed time≤0.15s, uses the live player ID plus current URL ID, and must reach the source's own `ended` state at its expected duration. A250ms monitor plus media events detects ads, seeks, rate changes, errors, another active media element, and loss of source identity. Recording pauses during ordinary buffering; the guarded intervals must join within0.20s timing tolerance. This timing tolerance and recorder scheduling latency are not sample-accurate alignment guarantees. Server decode/duration/signal checks and later quality review remain necessary.

Each worker allows at most eight pending chunks /4MiB, with chunks≤1MiB; four workers bound pending media buffers to16MiB. One stream per activated tab persists between same-origin jobs. The source is not accelerated. A stale monitor pauses recording after2s and holds it after5s. Wall time is bounded by1.5×source duration+300s; long videos are not excluded by an arbitrary duration threshold. The local service admits actual disk usage and can hold a job when its storage budget cannot accommodate it.

Published metadata is allowlisted from the current matching player response: title, description, channel/author, dates, declared language when available, keywords/category, static thumbnail URLs and view count. Rendered chapter markers are included only when their links identify the same video and valid source times. Missing fields remain empty; UI language is not treated as source language. Streaming formats, transport URLs, caption URLs, tokens, request headers and cookies are never traversed or exported. Private research text stays in the local service; the extension does not publish it.

## Verification

Run `node --test tests/*.test.mjs` in this directory; no package installation is required. Tests cover identity/permissions, canonical navigation, guards, buffering/coverage, local-only requests, final-chunk ordering and uncertain-acknowledgement retention. They do not access YouTube, a personal profile, Drive, or a GPU.

Official references: [Chrome tabCapture](https://developer.chrome.com/docs/extensions/reference/api/tabCapture), [background audio recording](https://developer.chrome.com/docs/extensions/how-to/web-platform/screen-capture), [activeTab lifetime](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab), [offscreen documents](https://developer.chrome.com/docs/extensions/reference/api/offscreen). Chrome documents that tab capture survives navigation and activeTab survives same-origin navigation; both are still bounded to the user's explicitly activated tab.
