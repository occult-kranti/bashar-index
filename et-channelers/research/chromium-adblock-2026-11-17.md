# Chromium adblock installation and source checks, 17 November 2026

**Batch continuation, 17:06 UTC:** the [publisher recovery report](publisher-mirrors-2026-11-17.md) records 17 complete publisher audio editions with English captions, including a two-worker batch and local recovery of three retained AAC files. The single-file observations below remain the original pilot evidence.

The maintainer's [uBlock Origin Lite 2026.1116.1650 release](https://github.com/uBlockOrigin/uBOL-home/releases/tag/2026.1116.1650) is installed unmodified in the project tools directory. The official 9,099,013-byte ZIP matches published SHA-256 `67e084b34470c51c08fa9314b118b8cb73df3a72e90c6a3b536d041c92e61bbc`. Its 1,030 entries expand to 32,948,819 bytes. The manifest hash is `f5c821556c853ef6dad8fdd1702a1432946cdb61300a7fc0bee7cdb9f98e1301`; it requires Chromium 122 or newer. The actual project executable is Chromium 151.0.7922.34.

The [installer and browser setup](../pipeline/BROWSER_ADBLOCK.md) preserve package/license bytes. Both unpacked extensions are included in both launch flags. Downloader worker selection uses its exact fixed ID and declared path; it does not assume that the first service worker belongs to the downloader. A valid leading slash in the official blocker's worker path is normalized without changing its manifest.

## Controlled local A/B result

One fresh baseline profile loaded only the downloader. One fresh filtered profile loaded downloader plus uBOL. The same loopback fixture served benign and ad scripts; the ad hostname came from actual default-enabled `pgl` rule 1. A loopback-only proxy/DNS configuration served fixture content and rejected upstream destinations. This did not contact an external ad service, YouTube or the production receiver.

| Observation | Baseline | Filtered |
|---|---|---|
| Benign script executed | Yes | Yes |
| Ad script executed / reached fixture server | Yes | No |
| Blocked ad request | No | `ERR_BLOCKED_BY_CLIENT` |
| Downloader manifest/options available | Yes | Yes |
| Native job started | No | No |
| JavaScript errors | 0 | 0 |

The untouched unpacked extension's `testMatchOutcome()` also identified `pgl` rule 1. Runtime inspection confirmed uBOL version 2026.1116.1650, Optimal/all-URLs mode, its six expected enabled rulesets and granted host access. No debug permission was added. This establishes local filtering and downloader coexistence, not YouTube ad-removal, buffering or full-file download recovery.

Profile peaks were 12,867,025 and 14,179,722 bytes, below the 150 MB per-profile ceiling. All captured owned Chrome PIDs had exited before both fresh profiles were removed. Original browser/source guards were unchanged. The local audit SHA-256 is `3f76a995c2327ab787e72625bf8f13694fc8ca811f111df91f10452eaabf8baa`.

## Public alternate publisher observations

A separate stock-Chromium metadata visit to the official Magenta Pixie Rumble listing returned HTTP 200. An optional login/challenge-class request triggered an overly broad local guard. The exact endpoint was not retained in that first diagnostic; the record does not establish a provider CAPTCHA or access denial. A later guard distinguishes blocked optional widgets from main-page authentication/access walls and preserves sanitized endpoint-path reasons.

One separately scoped episode page then returned HTTP 200. It identified Magenta Pixie, publication 2026-11-11 15:01:30 UTC, a 35:05 duration and actual declared embed ID `v7g0j2s`. That embed ID differs from the watch-page slug; it was observed independently in JSON-LD and player code. The queued YouTube item has the same distinctive title, approximate day and 35:06 duration. This remains a qualified candidate association without an exact YouTube cross-reference or verified edit equivalence.

The one standalone public metadata GET for that declared embed returned HTTP 403 and stopped. This does not erase the browser page's HTTP 200. A subsequent, separately scoped normal-site player visit used the public page and its own declared embed/site JavaScript, without copied cookies, custom headers, fingerprint changes, a proxy or a challenge solver. The site's own matching metadata request returned HTTP 200 and 13,890 bytes of JSON. This response exposed one audio-only AAC object and an English automatic VTT track. The successful browser request does not establish that the blocker caused access to work. The raw response, which can contain signed URLs, stays private.

## Complete publisher mirror and captions

The first selected audio object downloaded directly from the public publisher CDN with HTTP 200 in 3.891 seconds. Its 50,520,065-byte transport length equals the provider's declaration; SHA-256 is `8b63fed6c3a7db38df5fb1cf89ef72188f0b05c4706cc80a06975942c35a71f7`. One ffprobe pass identified audio-only AAC lasting 2,105.002708 seconds, matching the publisher's rounded 2,105-second duration. No picture track, re-encoding or real-time capture was used.

The 28,840-byte English automatic VTT response also returned HTTP 200. Parsing retained 255 timed cues, from 9.97 to 2,092.36 seconds. The union of cue intervals is 1,951.93 seconds; this is a timing statistic, not proof that every spoken word was captioned or that the words are accurate. The 27,816-byte caption ZIP retains original VTT, timed segments, readable text and provenance, with SHA-256 `f035fadaaa7e2e2a7408f3f0707075280f60fd0ec80b93b38bfca88ddaf80111`. Usable English text avoids unnecessary local ASR for this edition.

One three-object batch uploaded audio, sanitized provenance and captions to the associated video's content-addressed `PublisherVariants` namespace on Drive. Exact object IDs, sizes and MD5s were read back before the separate typed journal was fsynced and only the new 50,584,287-byte owned spool was removed. The original browser/source evidence and installed tools remain. This is one **qualified publisher mirror**: ownership, distinctive title, date and duration support the association, while an exact YouTube cross-reference and edit equivalence are unverified. Native YouTube audio, caption and ASR counters do not increase. Existing YouTube cooldowns remain unchanged.

## Storage and completion scope

The earlier five-folder snapshot omitted the task-owned Playwright browser cache outside those folders. At this audit, that cache added 735,101,726 bytes. New accounting includes private data, tools, three checkouts **and the Playwright cache**. Before the package/profile reservation the six-folder total was about 7.85 GB, below the 16 GB managed ceiling and owner's 20 GB total with 2 GB spare. Fresh profiles and source metadata are bounded separately.

The [9,291,081-byte BrowserTools checkpoint](https://drive.google.com/file/d/13X0bTj21VklgMbRaz8B7vrjuHWh8vrCl/view) is verified by exact Drive identity, size and MD5, with local SHA-256 `4ef24906bf40f5a302ffa6491674a5252315c2fd93f5ddcfa53dda7431b36bdf`. Its 41 allowlisted members include the unmodified official ZIP, installation receipt, frozen code, local A/B and publisher metadata evidence. Profiles, credentials, raw signed-URL payloads and media are excluded. Only the newly created checkpoint ZIP was removed after proof; installed files, archive and original evidence remain.

At the 16:35 UTC checkpoint, six-root managed storage was 7,907,187,531 bytes and C: had 40,863,281,152 bytes free. The first mirror spool was absent and the GPU lease was released.

At the original 16:35 UTC checkpoint, native acquisition was 47 of 1,420 latest-20 items and canonical ASR was 28, with saved text for 45 native audio items. Later [native recovery](native-transport-panel-2026-11-17/README.md) and [publisher batches](publisher-mirrors-2026-11-17.md) have separate completion evidence. The earlier SABR retry window remains 2026-11-18 07:31:07 UTC and captions retain their independent window. A passed browser component test is not itself a completed recording or permission to reset a spent source trial.
