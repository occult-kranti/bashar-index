# Publisher audio recovery, 17 November 2026

**18:49 UTC continuation:** 28 publisher editions are now verified: 17 Magenta, ten Athina and one Pavlina, totaling 1,131,582,863 audio bytes. The Magenta editions have English automatic captions; all ten Athina editions have verified English ASR, and Pavlina has a German original plus separate English translation. All newly owned ASR input copies have been retired after exact output proofs. The dated Magenta checkpoint below remains the original batch evidence.

Athina's ten source editions cover 15,068.10175 measured seconds (4h11m08s), with 2,889 generated segments / 39,022 words. The remaining-eight controller completed in 629.848 seconds including staging, inference, publication and retirement; this is not inference-only throughput. Maximum observed 30-second GPU utilization was 60.25%, peak VRAM 1.60 GB. Pavlina's 1,451.282-second source has 213 German and 205 English segments; its rolling GPU maximum was 58.87%, peak VRAM 2.77 GB. Source language evidence, original/translation roles and unreviewed accuracy are retained. The two earlier podcast editions and their ASR are separate.

At the 17:06 UTC checkpoint, **17 Magenta Pixie publisher editions and 17 English automatic-caption bundles are verified on Drive**. They contain 570,936,337 audio bytes. These are associated with current newest-20 entries; three entries remain unmatched in the inspected publisher listing. Native YouTube acquisition remains 47 of 1,420 and canonical native-source ASR remains 28.

## Working batch route

The official publisher account supplied normal public watch pages. One isolated Chromium session collected the matching site-generated player metadata for 16 additional episodes in 26.906 seconds; all watch pages and matching API responses returned HTTP 200. The browser did not download media or wait through playback. The accepted metadata exposed native audio-only AAC objects and English automatic VTT tracks.

The [bounded publisher worker](../pipeline/PUBLISHER_MIRROR.md) used two I/O workers, a 1.2 GB spool reservation and six-root storage accounting. It streamed complete CDN responses, calculated SHA-256/MD5 during transfer and preserved sanitized source metadata. Each completed edition uploaded as one audio/provenance/caption batch. Exact Drive object identity, size and MD5 receipts were durable before owned local files were released.

The initial 16-item run verified 13 editions and retained three complete files after a duration-check failure. The failure came from treating ffprobe's bitrate-based raw-AAC duration estimate as a measured duration. For one retained file, the estimate was 933.341536 seconds while 44,964 AAC-LC frames at 48 kHz represent 959.232 seconds, consistent with the publisher's rounded 959 seconds. The repaired publisher probe verifies raw ADTS frames through exact EOF, matching profile, sample rate, channels, one raw block per frame and packet count. It derives duration from the proven frame sample counts and retains the inaccurate estimate separately. Native YouTube format gates were unchanged.

The recovery run reused all three downloaded files, skipped the 13 matching completed receipts and verified the remaining three audio/caption editions. It made no replacement audio downloads. With the earlier pilot, all 17 editions now have usable timed text; automatic-caption accuracy and every-word coverage remain unreviewed.

## Identity and remaining entries

Publisher ownership, distinctive episode title, date evidence and rounded duration support qualified associations. Approximate queue dates and the observed `BeltaneSamhain` versus `Beltane/Samhain` punctuation difference remain explicit. Exact YouTube cross-references and edit equivalence are not established for these editions. The three unmatched entries are not declared unavailable: the inspected sample contains no sufficiently supported audio association.

Other official-feed research produced 18 Erin Lyons associations, ten Athina Krol associations and one Pavlina Klemm association. Fourteen Erin items and the Pavlina item contain exact YouTube references; the others retain qualified edition relationships. Sixteen Erin items expose publisher VTT pointers. Feed language is channel-scoped evidence, not independent proof of each episode's spoken language or each track's translation origin. Athina's ten items have no transcript pointer in the saved feed; this does not prove that captions exist nowhere else.

One ordinary Erin podcast GET followed its publisher redirect and returned HTTP 403. No audio was archived from that trial. The earlier HEAD refusal is retained separately. The recorded audio-endpoint retry deadline is 18 November 2026 at 17:07:54.109441 UTC. This evidence does not establish refusal of other publishers or the separate transcript endpoint. No cookies, credentials, forged headers, proxy rotation or challenge solver were used.

## Storage, checkpoint and continuation

After Magenta recovery, managed storage across private data, tools, three checkouts and Playwright's browser cache was **7,919,737,703 bytes**, with 40,837,058,560 bytes free on C:. The publisher spool held only 117,220 bytes of receipts/control files; the GPU lease was released. The 16 GB managed ceiling and owner's 20 GB total with 2 GB spare remain in force.

The 72-member sanitized [Magenta evidence checkpoint on Drive](https://drive.google.com/file/d/1zhGTbcJbcEWKc80dldbL-s5DuNiqv8F2/view) is 250,514 bytes, SHA-256 `516b16b57f3da3245b883b7005acdd92f4bc51f68790d6bf8c2322da69385adf`. Exact member hashes and Drive identity/size/MD5 were verified before deleting only the newly created ZIP. Signed-URL payloads, credentials, profiles, media and full caption text are excluded; original evidence remains private.

Continue official-source batches while the separate native YouTube panel audits current extractor and SABR code. Saved publisher captions take priority over duplicate ASR. The publisher-source ASR bridge reused the existing pinned CUDA models and source leases for all ten Athina editions and the Pavlina original/English pair reported above. These source-specific results remain unreviewed. Non-English recordings retain original-language text and a separate English translation. No scientific corpus-analysis jobs are enabled by this collection work.

One successful route for one publisher does not supply an all-channel completion ETA. The metadata and audio/CDN stages can overlap uploads; elapsed batch observations include validation, upload and recovery. They must not be reported as transfer-only bandwidth.

## Independent Dreemtime publisher timed text

Three Cosmic Conversations episodes now have publisher-provided timed text verified on Drive: episode60 (`2CAOL3sBy00`),58 (`Ec75gLdSEZ4`) and57 (`KjetxEOu7gA`). The official publisher blog explicitly links those YouTube IDs; the public RSS declares each VTT. Two content-addressed bundles total 248,386 bytes and 1,500 cues. Exact Drive identity, size and MD5 were checked before only the newly built ZIPs were retired; original VTT, normalized segments and provenance remain private. No podcast audio request was made.

The [official show](https://cosmicconversations.buzzsprout.com/) declares English at RSS-channel scope. Manual versus automatic caption origin and translation status are unspecified; recording-edit equivalence, accuracy and full speech coverage are unverified. These are independent publisher text artifacts, with no source-audio hash binding, and do not increase native audio, native YouTube captions, ASR or audio-with-text totals. The remaining candidate associations and the separate Buzzsprout audio refusal remain preserved.
