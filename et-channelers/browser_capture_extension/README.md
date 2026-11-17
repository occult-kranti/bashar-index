# Research native audio pilot

## Current mode: one admitted native SABR pilot

Version 0.3.0 is restricted to `EliqxbbQoRw`, one resource-owner-admitted attempt, 64,000,000 output bytes and 1,000 authorized source requests. It does not enable batch collection yet. **At the owner's request installation and activation are automated in dedicated headful Chromium; another manual reload/click is not required.** The same extension ID is retained. The manifest permits the two exact loopback ports and `https://www.youtube.com/*` so automation can inject the helper without a toolbar gesture. No Googlevideo host permission, cookies access, browser profile access, debugger permission or recording activation is added. Source fetches remain inside the normal page context.

The actual automated trial reached **1,133,713 bytes / eight segments / 69.892 seconds** while playback was paused, then held before EOS with `sabr_stream_failed`. It did not pass full validation or upload a new artifact. The spent attempt and partial remain retained; the receiver is stopped while safe diagnostics are improved. HTTP 200 did not establish full protocol acceptance. See [the investigation record](../research/native-audio-investigation-2026-11-17.md). The preserved recording instructions below remain historical.

The diagnostic follow-up exposed `sdk_stalled` with protection status 2 (pending), correct 69,892 ms request playhead/buffer and full selected-format match. Both incomplete attempts remain retained. The owned status page now provides **Reload helper**, read-only **Check target tab**, and **Start admitted native trial** for scoped automation in the normal Chrome session. Check verifies the actual granted permission and exact eligible video; Start repeats those checks and pairs before injection. It requires a matching separate backend admission. The safe protocol report rejects unexpected diagnostic fields. These controls do not resume collection automatically or require another owner toolbar click.

The MAIN-world observer passively wraps ordinary player fetch/XHR while preserving their original calls. It waits at most45s, examines at most16 candidate request bodies (one at a time, each at most64KiB), and requires live URL/player/response video agreement, no ads/DRM, matching streaming-config bytes and selected full format identity `(itag,lastModified,xtags)`. It accepts session material only from a normal HTTP200 UMP request. Source403/429 stops it; unrelated timedtext/telemetry responses do not. Wrappers are restored and token memory is cleared on cleanup. If ordinary playback was paused, the explicit activation briefly resumes it for this bootstrap and pauses it again; it never records playback.

The actual download format is selected independently from the same video's published catalog: `acont=original` must be explicit, with no DRC/voice-boost tags. A default track, SDK inference or `.4` track suffix is not original-language proof. Original AAC140 is preferred for this first integration pilot. The ordinary player's bootstrap track may differ. Its video-bound token, already-deciphered media URL, config, client information and credentials mode stay within the accepted MAIN realm. No attestation is generated or solved.

The reviewed googlevideo5.0.1 adapter downloads audio only with zero source retries and per-request durable authorization. Native encoded audio is reassembled, **not re-encoded**. Only public metadata, format/hash proofs and bounded audio chunks cross MAIN→isolated content bridge→extension. Chrome JSON messages carry at most768KiB raw/base64 media per call; the extension converts them to binary loopback POSTs. The bearer stays in extension memory. A lost/incorrect chunk ACK holds the attempt rather than resending. No source URL, PO token, cookie, request-header value or raw player response is sent to Python.

Options reports observation, native download, validation/upload and final Drive verification separately. Protocol EOS, complete contiguous segments, exact declared/emitted byte lengths, local decode/duration checks and Drive ID/size/MD5 proof all remain required. No prefix is a completed recording. A second toolbar click stops this active native pilot. No automatic retry or second video is dispatched; four-worker batch operation remains gated on the first full verified result.

`native-main.iife.js` is reproducibly built from `native-main.js` and `native-observer.js`. Use esbuild0.25.12 with `node build-native-main.mjs` (or `--esbuild-module <installed-esbuild/lib/main.js>`). `native-main.build.json` records input/output hashes. Vendored SDK hashes/licenses are under `vendor/`. Importing either bundle makes no source request. Run `node --test tests/*.test.mjs` for offline fixtures; the live accepted-context result is a separate gate.

## Earlier v0.2.0 inspection mode

Version 0.2.0 changes the default toolbar action to **inspection only**. Reload the unpacked extension once if an earlier version is already loaded. On a normal `www.youtube.com/watch` tab that already plays, the toolbar reads the live player/URL/response identity and opens Options with safe audio format descriptors. It does not seek, record, acquire a tab stream, download media, contact the local archive service, or export transport URLs, tokens, cookies or player responses. No new permissions are required; the extension ID is unchanged.

Options shows up to four recent inspections: audio MIME/codec, declared size and duration, direct-URL versus cipher-only availability, and presence flags for SABR, streaming configuration and client information. The **Copy safe inspection** button copies only these descriptors. A published-token presence flag is not a token-acquisition mechanism; absent fields stay absent. Ads, protected media, a stale response or mismatched live video fail closed. This inspection is evidence for selecting a supported native batch transport, **not proof of a successful full download**.

`native-inspector.js` also contains an unexposed 64KiB direct-format probe for a later, explicit integration. It accepts only an existing HTTPS Googlevideo audio URL in page memory, performs no deciphering/client changes, requires exact HTTP206 range/length/known total and an audio container header, and returns only a prefix hash/proof. It refuses a second attempt for that video/format in the same page lifetime. HTTP403/429 or CORS errors stop it. The toolbar does not call this mode. No full native artifact has been proved by these fixtures.

The preserved recording code is not exposed by the current UI. Its last16 bounded outcomes remain in Chrome session storage after cleanup; explicit user stop/tab closure is distinguished from an actual failure. Source URL/token/error-body material is excluded. A later authorized recording activation refreshes local pairing first, without retrying uncertain chunk/finish requests.

Official browser constraints: [MAIN-world scripting](https://developer.chrome.com/docs/extensions/reference/api/scripting) runs within the accepted page context; [ordinary cross-origin restrictions](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests) still apply. The YouTube host permission enables automated injection; it does not grant cross-origin media access or establish acceptance by the source.

## Preserved experimental recording fallback

**Parked, November 17:** the owner requests scalable native batch downloading rather than real-time recording. The local capture service and its dispatch reservation are stopped. Do not follow the activation steps below as the current acquisition plan; they document the preserved experimental fallback. Short accepted-browser recordings were held, and no complete browser artifact was archived.

This Chrome Manifest V3 extension records audio from explicitly activated YouTube tabs and streams it to the local archive service. It uses supported `chrome.tabCapture`; it does not retrieve signed media URLs or read/export cookies, credentials, or profiles. Output is **browser_recorded_audio**, re-encoded WebM/Opus at96kbps, with no native-source or accuracy claim.

## Historical recording setup (parked)

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
