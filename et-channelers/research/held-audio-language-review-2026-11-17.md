# Held-audio review, 17 November 2026

The latest-20 collection remains 47 of 1,420 archived audio items. At the start of this review, 44 had saved text, 42 met text-inventory checks, two saved-caption inventories needed review and three audio items had no saved text. The evidence-driven full-source run below subsequently increased saved text to 45 and full ASR to 28. Intermediate VAD, language and partial-text reviews never create completion receipts. Metadata, voice activity and language-model scores are not semantic ground truth.

## Completing the two retained-input checks

Earlier beginning/middle/end VAD probes left 150 seconds unexamined across two recordings. One bounded full-file pass assessed all 291.073875 decoded seconds, retaining at most 9.73 MB of PCM. It detected no speech candidates in its windows. One earlier 30-second probe had detected 3.744 seconds in the second recording; that evidence remains preserved. Window/context sensitivity prevents a silence conclusion.

A separate original-channel check found both decoded stereo channels entirely zero in the first recording. The second has nonzero audio with channel correlation +0.761489 and a normal downmix. These findings rule out destructive mono cancellation in the examined archived streams; they do not establish the content of an independent source playback.

The [VAD evidence archive](https://drive.google.com/file/d/1Uho92Dl4QrmufLmB39Un-MR6kOK5Xya-/view) and [channel-integrity addendum](https://drive.google.com/file/d/1NsBn2QxIkyI_aTME-Sj8Cvzll_MW4-dG/view) have exact Drive identity, size and MD5 receipts, with local SHA-256 proofs. Original held inputs and earlier decisions remain unchanged.

## Examining the metadata-only hold

The third recording had never been fetched for the previous multilingual pilot. Its light-language/healing description does not determine the language or lexical meaning of every interval. English caption inventory keys do not establish saved caption text or original spoken language.

One exact 20,592,023-byte archived audio/metadata pair was retrieved from Drive and matched its existing identity, size, MD5 and SHA-256 proofs. One streamed decode assessed all 1,529.6029375 decoded seconds, with 120 VAD-positive intervals totalling 1,356.432 seconds. The rounded 1,530-second metadata leaves a 0.3970625-second unavailable, unreviewed tail; nothing was padded. Both native stereo channels are nonzero and strongly correlated (+0.99998494), with no decoded timestamp discontinuity. Conservative retained/scratch PCM accounting stayed below 13.24 MB; no PCM file was written.

These measurements justify a bounded language-identification review. They do not establish meaningful speech, English, a translation or a whole-recording language.

| Original-time window | Input seconds | VAD overlap seconds |
|---|---:|---:|
| 11.344–41.344 | 30 | 29.312 |
| 792.592–822.592 | 30 | 30 |
| 1,101.568–1,130.032 | 28.464 | 28.464 |

All windows are disjoint, aligned to original 16 kHz sample coordinates, and retained contiguously. The first window preserves its short pauses. The total model input bound is 88.464 seconds / 5,661,696 PCM bytes. The existing multilingual model, exclusive GPU lease and soft 70% pacing policy apply. Language scores describe selected intervals; they do not prove lexical meaning or authorize a full-recording label.

## Actual first trial

The first admitted language-review trial stopped with `seek_preroll_limit` during window decoding and saved no scores or review ZIP. Its diagnostic does not establish which window failed or how many earlier detection calls completed. The original worker, proposal, failure and lease history remain preserved; the GPU was released and verified inputs were retained.

The [execution contract](../pipeline/LANGUAGE_ID_REVIEW.md) keeps language review separate from text generation and ordinary ASR journals. Publisher captions, metadata flags, previous holds and full-recording completion counts remain authoritative in their original lanes.

## Revised language-review result

The second version replaced seeking with one bounded sequential decode. All 24,473,647 source samples and all three retained windows were validated before loading the model. It retained 5,661,696 PCM bytes and completed exactly three language-detection calls using the pinned multilingual model on CUDA `int8_float16`. No transcript or translation text was generated.

| Sampled window | Model language | Score | Top-two margin |
|---|---|---:|---:|
| Early | English | 0.999512 | 0.999436 |
| Middle | English | 0.999512 | 0.999287 |
| Later | English | 0.998535 | 0.998153 |

These uncalibrated scores support the sampled windows only. They do not establish lexical meaning, language throughout the recording, translation quality or a full transcript. They justify a separate, bounded text review on the same intervals while preserving the original metadata flag.

The local 3,339-byte review ZIP has SHA-256 `59d2f80a1572ad96b1e3c7ebf134437b8adee388056eed86cae9527da2695b91`. Its two GPU samples observed 35.5% mean utilization, 47% peak, 2,401,988,608 bytes peak VRAM and 53 C. This brief sample is not a complete 30-second utilization assessment. The GPU lease was released after completion; inputs remain retained for the separately admitted next step.

The [combined VAD and language-review evidence](https://drive.google.com/file/d/1OZ9xSQKn7mWEZOvKxhjymK7QYeDzQqau/view) is Drive-verified: 135,731 bytes, SHA-256 `9a8bd6885098d2e25ef1baa1e9319cb940220c57c6ec1e108dbe1ee6b418c06c`. It preserves the failed first trial and successful second trial without rewriting either history.

## Bounded text review

A separately admitted partial-ASR worker transcribed only the same three windows. It produced 13 segments and 186 unreviewed words, with original source timestamps and an explicit inventory of the unprocessed remainder. English original text and its English alias remain distinct from a full-recording transcript. No text is reproduced in this public report.

The root agent inspected the private output and found coherent English in all three excerpts. This is machine-assisted content assessment, not human review or a claim about every interval. Together with the language scores, it supports preparing a new full-source, unreviewed ASR admission while preserving the original metadata flag and evidence. The metadata label alone must not be treated as proof that the whole recording lacks lexical speech.

The partial trial took 32.86 seconds: 5.875 seconds sequential decoding, 10.5 seconds model loading, and 6.578 seconds across three inference calls. The decoder made 152,995 cheap heartbeat checks and 20 full lease checks, including forced phase boundaries. Expiry/deadline checks remained per frame; full file-backed checks ran once per second and at critical boundaries. This avoids the first implementation's repeated file/path reads on every audio frame.

Seven GPU samples observed 44.14% mean utilization, 61% peak, 2,737,532,928 bytes peak VRAM and 59 C, with no telemetry fallback or error. The inference observation is shorter than a complete 30-second utilization window. The GPU was released and inputs retained. The 10,426-byte partial bundle has SHA-256 `50ab6612e71802afbc4c7fa9adc0fd30565568b8f0bc87fef26be21c923c470f`; it remains excluded from ordinary full-ASR and collection-completion counters. See the [partial-review contract](../pipeline/PARTIAL_ASR_REVIEW.md).

The [partial result](https://drive.google.com/file/d/13tje2J0wiQfCtVXRZvhQnLAs4QZXQM8K/view) and [runtime supplement](https://drive.google.com/file/d/1LU7BuJPfHzFYNb68l5GPLDy5zSeciNk0/view) are exact-Drive verified in their separate review lane.

## Full-source ASR after explicit content assessment

A new, separately leased [reviewed-metadata adapter](../pipeline/REVIEWED_METADATA_ASR.md) used the existing multilingual runtime, full-source collector and established English-alias writer/verifier. The original metadata still declares an unknown language and retains its light-language review flag. A new root-agent assessment binds the VAD, language and coherent-text evidence; it permits unreviewed ASR without asserting human review or lexical content in every interval. Existing English-source and old multilingual-frame admission gates were not changed.

The completed run processed all 24,473,647 decoded samples (1,529.6029375 seconds) through 51 windows. It produced 196 segments and 2,711 unreviewed words. The rounded metadata's unavailable 0.3970625-second tail remains explicit. All original-English text and its English alias passed the established paired-artifact verifier.

The [76,657-byte canonical ASR bundle](https://drive.google.com/file/d/1RamNV3DmeVv6dgI-G_Ijv74a6osB8ZUP/view) has SHA-256 `6fe5c0285288da2ad7cfcb903b686bf5b1753a785bd5b257c321356c847729ec`. The [116,568-byte runtime/assessment supplement](https://drive.google.com/file/d/1EUvG7r0taP7cN2oTMbNmGPuCSW1h_gcJ/view) preserves the complete decision chain. Both were verified by exact Drive identity, size and MD5 before the ordinary full-ASR receipt was written and 20,592,023 newly owned input bytes were retired. Original holds and earlier evidence remain byte-exact, with retirement recorded separately. Older held inputs were untouched.

The full run took 140.641 seconds, including 22.919 seconds decoding and 97.065 seconds inference. Across 120 fresh telemetry samples, mean GPU utilization was 44.36%, maximum observed 30-second rolling mean 53.93%, instantaneous peak 100%, peak VRAM 2.738 GB and maximum temperature 71 C. No telemetry fallback/error occurred. The 70% setting is a soft pacing target; it is not an instantaneous kernel ceiling. The GPU was released after completion.

This result increases ordinary full-ASR coverage to 28 sources and saved transcript/caption availability to 45 of the 47 archived audio items. Forty-three meet text-inventory checks; two caption inventories need review and two audio items still have no saved text. Native latest-20 audio acquisition remains 47 of 1,420. Publisher-written companions and alternate audio editions are tracked [separately](publisher-companions-2026-11-17.md). Storage verification and complete source processing do not establish transcription accuracy or every-word coverage.
