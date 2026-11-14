# Analysis plan for the Bashar Index and the et-channelers corpus

*Written on 2026-11-14 from three independent drafts and a synthesis, made by an agent workflow that read the repository, the Bashar Index panel and the private store's tables (no transcript text is reproduced here). Counts are as of about 02:15 UTC that day; [README.md](README.md) and [HANDOFF.md](HANDOFF.md) have the current ones. The references in Appendix B are to be checked before they are cited. Section 12, added later that day from a deep-research survey, replaces decision D11, section 5.15 and the caps per channel in 4.6 and 5.5.*

## How this plan was chosen

| Draft | Grounding in the data and its sizes | Completeness | Feasibility on the machines available | Clarity | Total (of 40) |
|---|---|---|---|---|---|
| A. Language and small models | 9 | 8 | 8 | 8 | **33** |
| B. Networks and comparisons | 9 | 6 | 8 | 9 | 32 |
| C. Design, statistics and standards | 9 | 8 | 7 | 8 | 32 |

Draft A is the base because it is strongest where most of this plan's work lies: processing with a small model, and the language analyses the owner asked for once collection ends. It is the only draft that prices the model work per hour of audio, at about $0.006 with Claude Haiku 5.5 through the Batches API. Its price figures, and its warning that this model rejects a temperature setting, match the API reference. It shows that a 3B model on this CPU is unworkable, at about 72 minutes per audio hour. It covers summaries, question banks, embeddings with real overlap measures, topic models, keyness, repetition and the shorts study. Its one counting error was 67 transcripts where there are 61 unique ones. Draft C supplies what A lacks: confirmatory families that re-test the panel's questions on independent archive.org sessions, and a hash split that can be computed today. It adds a prospective test that must be filed before 2027 and a blind error audit (it found that `verify.py` shows the machine text to the person correcting it). It also gives the paper outline, the standards and the rights analysis. It loses a point on feasibility because it depends on a GPU by January, the owner's laptop lane and an exception to the interview rule. Draft B supplies the network designs, the rules for comparing groups and networks, and the clearest display guidance. Its metadata checks also changed the design: the guest projection is saturated, and the claim register is mostly one-to-one. But it has no summaries, no costs and no paper, and it asks for "temperature 0", which the model rejects. All three drafts were well grounded, so completeness and feasibility decided the order.

## 0. The plan on one page

- **What is studied.** The study measures language and genre discipline in channeled material, not whether any claim is true. It has two arms:
  - Bashar across four decades, on verbatim transcripts of the archive.org sessions the Index catalogues.
  - The cross-channel corpus: texts from the source now, speech-to-text as it arrives, and the owner's Phase 7a (shorts against long videos) and Phase 7c (years, last N recordings, predictions, timelines, question banks).
- **Scope, as the owner decided.** Every recording over 5 minutes is analysed, with no upper length limit and no cap per channel. Shorts and recordings of 5 minutes or less are analysed apart (Phase 7a). Section 12 is the method for Phase 7c.
- **Text kinds never mix.** Texts from the source and speech-to-text made here are separate strata in every table, model, figure and test. They meet only in a calibration study on the same works.
- **Few confirmatory tests, registered outside the repository.** There are five small families, each Holm-corrected and each behind measurement gates:
  - B: Bashar sessions.
  - S: voice and register.
  - Q: the same question put to different voices.
  - Y: shorts and the 75 digested recordings; needs the laptop lane.
  - PR: what is said after 2027; must be filed before 2027-01-01.

  Everything else is exploratory and carries a badge.
- **Small model.** Claude Haiku 5.5, through the Message Batches API, reads every unit in three passes: structure, codes and summaries. Every label carries an evidence span that must match the text.
  - Cost: about $0.006 per audio hour in batches when the prompt cache hits, $0.009 when it never does. For the source texts and every main-corpus recording of known length (about 24,800 hour-equivalents) that is about $150 to $225, or about $300 at standard rates; a 10% Sonnet audit adds about $270 (12.5).
  - The real cost is about 205 hours of human coding, and that coding decides which codes may be used.
- **Machines.**
  - The present two-core machine runs metadata, counting, networks, keyness and small embeddings.
  - A GPU is needed for large-v3 transcription, speaker separation, an open-weight coder and larger encoders.
  - Only the owner's own computer can reach YouTube text. That route, like the listings, reads paths YouTube's robots.txt disallows, so it waits for the owner's decision D12 (12.1).
  - The whole main corpus (about 23,200 h) needs about 250 GB of private storage, about 3 weeks of CPU for the audio off YouTube and about 500 GPU-hours for YouTube's (12.10, step 0).
- **Order of work.**
  - Preparation and measurement happen now, because they decide how collection transcribes and what gets registered.
  - Content results come only after the freeze.
  - Confirmation data stay sealed until registration.

## 1. What exists today, in numbers

**Snapshot.** The figures are as of 2026-11-14 at about 03:30 UTC, when all jobs were paused for the move to a 16 GB Codespace. They were recounted for this plan from the private manifests, taking the last record per item and counting only (Appendix A). The handoff has later figures: the Drive copy was finished after this snapshot (1,998 files in 77 folders), and the hours were recounted unrounded (911.3 h listed on archive.org). Collection will resume, so every later number cites its snapshot.

### 1.1 Held material

| What | Count | Hours | Words | Persons | Detail |
|---|---|---|---|---|---|
| Audio (mono 24 kbps Opus, 10.11 GB) | 1,138 files | 819.5 | | 23 | Podcast feeds 781 files (502.7 h); archive.org 262 (275.2 h, all Bashar); creators' own sites 95 (41.6 h); YouTube 0 |
| of which Bashar / Darryl Anka | 282 files | 298.1 | | 1 | 262 archive.org session files from 146 items (275.2 h); 20 podcast interviews (22.9 h; 5 published in 2025, 15 in 2026) |
| Texts from the source | 8,425 | | 13,309,693 | 19 | L/L Research 6.41 M, Daniel Scranton 3.07 M, Cosmic Agency 2.29 M (88.5% together). 8,111 web pages, 257 imported Sam the Illusionist texts, 57 podcast-host transcripts. 5,233 carry a published date. Darryl Anka: 11 texts (138,022 words) |
| Speech-to-text made here | 61 | 30.6 | 259,518 | 14 | faster-whisper base.en 49, multilingual base 12 (German, one person). Median 5.9x real time (1.3 to 16.1). Darryl Anka: 9 (7 podcasts, 2 archive.org sessions) |
| Works with both text kinds | 6 | | | | 24 more items (33.8 h) have audio and a source text but no transcript yet |
| YouTube captions | 0 | | | | Refused from cloud servers |

Stores:
- **Private GitHub store.** Every item is verified: audio 1,138, made-here transcripts 61, source texts 8,425. The text mirror keeps `texts/<person>/from-source` and `made-here` apart.
- **The owner's Google Drive** (folder "ET Channelers Archive", unshared).
  - Already up: the tables, transcript zips by person, and the earlier work (Bashar Index, ArchiveShelf, Channeling Atlas).
  - The browsable copy was part-way through at this snapshot: its ledger listed 286 of 1,948 planned files (1.41 of 9.93 GB) in 77 folders. It was finished at 07:25 UTC with 1,998 files in 77 folders. These are 246 audio parts covering 106 recordings, and 40 text volumes.

### 1.2 Still to collect or transcribe

- **Bashar archive.org queue:** 262 of 903 files downloaded, 636.7 h left.
- **Podcast backlog:** 733 of 2,647 episodes, 1,442.6 h left; creators' own files 95 of 1,410 (1,315 left, length unknown).
- **Interviews on other shows:** 28 of the 29 queued live-channeling interviews downloaded.
- **Held audio with no transcript:** about 789 h. Speech-to-text is the bottleneck: under collection load the machine made about 1.3 hours of text per hour.
- **Not reachable from a cloud server:**
  - YouTube audio and captions for 58,762 YouTube rows (58,699 of them listed);
  - 274 sessions that exist only on tv.bashar.org (paid, behind a login).
- **Reachable with extra work:** the 146 video-only archive.org sessions (300.2 h; about 529 GB as video). Their audio track can be extracted as a stream without storing the video.

### 1.3 Bashar sessions on archive.org: the sampling frame

The rows come from the public list `et-channelers/sources/archive_org_sessions.csv`, with archive.org session dates, joined to held audio and transcripts.

| Era | Items | Items with audio files (h) | Video-only items (h) | Held: items, files (h) | Transcribed items |
|---|---|---|---|---|---|
| E1 1984-89 | 183 | 151 (586.4) | 32 (69.6) | 96, 190 (205.2) | 2 |
| E2 1990-99 | 131 | 89 (305.4) | 42 (58.8) | 45, 63 (50.5) | 0 |
| E3 2000-09 | 49 | 4 (15.1) | 45 (105.4) | 4, 4 (14.9) | 0 |
| E4 2010-26 | 26 | 0 | 26 (64.4) | 0 | 0 |
| undated | 2 | 1 (4.3) | 1 (2.0) | 1, 5 (4.6) | 0 |
| **Total** | **391** | **245 items, 903 recordings (911.3 h listed; 6 with no listed length)** | **146 items, 153 files (300.2 h)** | **146, 262 (275.2 h)** | **2** |

What this means:
- **Cloud arm.** The 1980s and 1990s can be studied from the cloud: 240 items with audio, about 892 h.
- **Video-only decades.** The 2000s to 2020s are almost all video-only (45 of 49 items and all 26), so they need the stream extraction above.
- **Split.** The Index catalogue cites 392 items. Draft C's hash split puts 102 in discovery and 290 in confirmation. Of the confirmation items, 76 from E1 and 31 from E2 are already held.

### 1.4 The Bashar Index and its panel

- **Site.** A single static page (about 2.1 MB), built from a data package dated 2026-09-11; it last changed in commit cff3988 on 2026-09-16.
  - It shows 684 sessions, 75 digests, "1.19M transcript words" (a model guess), 949 questions, 56 diagrams and 104 terms.
  - None of the panel's later work appears on it.
- **Session catalogue.** 684 sessions, 1984 to 2027. By decade: 184, 131, 50, 159 and 151, plus 9 undated.
  - 393 rows link to archive.org (392 items) and 274 to tv.bashar.org.
  - 387 descriptions are boilerplate. It holds metadata only.
- **The 75 digests.**
  - Recording types: 27 full-session re-uploads, 21 Darryl Anka interviews, 15 clips, 12 official clips.
  - 40 have a reliable year, 35 of them in 2024 to 2026.
  - 949 questions, capped at 20 per recording (34 lists at the cap, 8 empty).
  - 2,066 key-term entries, 493 quotes of 30 words or fewer, 164 ledger rows.
  - Known defects:
    - the digests came in three batch conventions (25, 27 and 23), and the batches line up with recording type;
    - 7 of the 10 commonest key terms are the prompt's own examples;
    - word counts are model guesses (only 28 distinct values).
- **Where the 75 are.**
  - 68 are still on YouTube, 6 are gone and 1 is private.
  - 5 are held here: 4 as podcast audio of the same interview, 1 as podcast text only.
  - 2 have real text: one has both kinds, one a publisher text only.
- **Panel** (commit 457dc2f; two AI roles over five rounds, digests only):
  - P3 confirmed: V 0.212, cluster-bootstrap interval 0.211 to 0.300. But it cannot be separated from the batch: V by batch is 0.205, and V by batch within clips is 0.595.
  - P1 null: n = 88, and 72 of the 88 claims contain no listed phrase.
  - P2 not certified: n = 25, slope 0.0 (interval -1.2 to 1.0).
  - P4 null, on capped question counts.
  - 73 window flips from 35 rows; one 2021 interview takes part in 32 of them.
  - Kendall's W 0.009. Rubric calibration 0 of 2, with 55 windows still open and a deadline of 2030-01-01.
  - Never run: digest re-verification, the cluster sweep, stylometry, the word-error audit.
  - Design, code and results went into one commit, and nothing was registered outside.
- **Tools worth keeping:**
  - the frozen 50-phrase list;
  - the frozen 2027 rubric with its no-tuning clause;
  - the 164-row ledger format;
  - `report.py` (Holm correction; refuses an unbadged p-value);
  - seed 42;
  - `common.py` and the modules `predictions.py`, `demand.py`, `doctrine_graph.py`, `doctrine_dynamics.py` and `rubric_calibration.py`.

  All of them need REPO and GIT_HEAD pointed at the new commit.

### 1.5 Interviews

- **Typed:** 189 interviews.
  - 30 live channeling, from 11 persons: Paul Selig 6, Riz Mirza 6, Wendy Kennedy 4, Lee Carroll 3, the rest 1 or 2 each.
  - 19 conversation, 13 of them Darryl Anka.
  - 2 commentary or clip.
  - 138 not classified, because no transcript exists yet.
- **Read in full by the reader agent:** 39 (a small model under the `haiku` alias, so these are model labels). It found 21 live channeling, 17 conversation and 1 commentary. The median channeled share is 39% (range 8 to 70%).
- **Live channeling material:** 21 source transcripts (270,153 words) and 29 audio files (44.4 h).
- **Shows:** 9 shows and 28 guests make 75 show-guest pairs.
  - 21 of the 30 live-channeling interviews and 16 of the 19 conversations come from one show.
  - Only 2 guests have interviews of both kinds.

### 1.6 Listings and catalogue (metadata only)

- **Catalogue.** 73,921 rows; 69,186 distinct works once 4,735 twin rows are merged; 70 persons; about 23,760 h listed. 61,578 rows are undated.
- **YouTube.** 58,699 listed rows on 63 channels: 32,570 long-form videos, 10,014 live streams and 16,115 shorts. The catalogue's 58,762 YouTube rows also hold 63 Bashar recordings on 37 other channels, which no listing holds.
  - Length is known for 21,269 h.
  - There are no upload dates and no text or audio.
  - 3,076 long-form videos have a linked page text, 2,470 of them Daniel Scranton.
- **Phase 7a sizes** (Draft A, from the listings).
  - 51 channels have both shorts and long videos.
  - 39 have at least 20 shorts and 20 videos over 5 minutes. The count rises to 47 if videos of 5 minutes or less count as short.
  - In those 47 channels:
    - the short group is 22,623 items: 16,078 shorts, 5,718 videos of 5 minutes or less (300 h) and 827 short streams;
    - the main corpus is 33,307 items and 19,718 h;
    - the median channel has 354 long videos (191.5 h) and 161 short items.
- **Other metadata.** 865 items on 34 channels name Q&A in their title.
- **Language.** English holds 13.30 of the 13.31 M source words. The only sizeable non-English text is the 12 German made-here files (39,145 words).

### 1.7 Reference layers

- **channels-ET.** Only its metadata is on this machine. Its 36,413 objects (17.8 GB) and its 683-document text frame stayed elsewhere, so its analyses cannot be recomputed here. What it offers:
  - **Claim registers:** 41 mediums, 52 beings, 69 claims, 19 comparison groups and 150 sources. The claims are mostly one-to-one: 30 of the 38 mediums with a claim have one being, and 43 of the 52 beings have one medium.
  - **Codebooks:** 10 reading codes, 8 Q&A themes, 5 modality classes, 10 keyword dictionaries and 5 content-label themes. In its pilot, models of 0.8B parameters or less gave nearly every item the same label.
  - **YouTube inventory:** 297 accounts and 2,812 videos, of which 642 carry entity labels and 878 a verified uploader. 1,809 of those video ids are in our listings.
- **ArchiveShelf.**
  - 257 Sam the Illusionist texts; the same pages are already held as source texts.
  - 16 Sounds True episodes (10.31 h, audio plus Whisper large-v3-turbo transcripts), in a private release. They are context material, not channeling, and are useful for comparing speech-to-text engines.
- **Kimi snapshot** (channels-ET as of 2026-11-14). It holds no audio or transcript text, only tables, code and the paper. Its tables describe audio of 42 YouTube videos fetched through a converter site, with 34 `tiny.en` transcripts (146,605 words; 572 literal question units), and paste-link subtitles. These stay in the other agent's folders, and this project does not take them (handoff decision 6.2).

### 1.8 Machines and software

- **Present machine.** A Codespace with 2 vCPUs on one physical core and 8 GB of memory.
  - All jobs are paused; 11 GB of 32 GB is free now (5.5 GB while downloads ran).
  - The load average is about 15 when collection runs.
- **Next machine.** A 4-core, 16 GB Codespace, as the handoff says.
- **Not available yet.** There is no GPU. Only the owner's own computer can run the YouTube lane (`run_all.py`).
- **Software.**
  - The system `python3` lacks scipy, pandas, scikit-learn, statsmodels and networkx.
  - `et-venv` has numpy, faster-whisper, ctranslate2, onnxruntime and tokenizers.
  - R is not installed.

## 2. Research questions and hypotheses

### 2.1 Labels used below

- **Pre-registered (confirmatory).** The test sits in a family with Holm correction. It is registered outside the repository before any confirmation data are opened.
- **Pre-registered (conditional).** The same, but the test runs only if a stated run condition is met by a stated date. Otherwise it is reported as "not run", with the reason, and is never dropped silently.
- **Registered exploratory.** The method is fixed in the registration, but readers profiled the data before registration. The result therefore carries an EXPLORATORY badge and stays outside every family.
- **Exploratory.** Benjamini-Hochberg correction applies within each named set, and a badge goes on every result. A finding becomes confirmatory only on a held-out half or through a registered amendment.
- **Gate (estimand).** A measurement with no test. It decides what the later tests may use, and it is decided before any outcome is computed.

Every result carries the panel's banner: these analyses measure genre discipline, not truth. Claims are reported as claims.

### 2.2 Research questions

| RQ | Question | Answered by |
|---|---|---|
| RQ1 Change within a voice | Do Bashar's teaching vocabulary, emphasis on contact, and dating of milestones change between 1984 and the 2020s? How do L/L Research and Daniel Scranton change by decade and year? | B1-B4; X5; X6 |
| RQ2 Audience | What do audiences ask, how often (with no cap), and does demand shift? | B5; X3 |
| RQ3 Voice and register | Is the channeled register separable from the person's own voice? Are entities channeled by one person separable from each other? How does that compare with other mediums? | S1-S3; X8 |
| RQ4 Same question, different voices | Do different voices answer the same question alike, beyond topic? | Q1; X7 |
| RQ5 Repetition and spread | How much does a channel repeat its own formulas and passages, how much wording moves between channels, and along which ties? | Q2; X1; X10 |
| RQ6 Names | Which beings, star systems, places, calendar terms and astrology terms are named, by whom, in which role, and next to what? Is naming nested? | X4; E-H1 |
| RQ7 Circulation | How do people and material move through interview shows and clip and re-upload channels? | E-H2; X9 |
| RQ8 Dated statements | Which statements point to the future, how sure are they, are they conditional, and which date do they name? What is said once the date passes? | B3; B4; PR1-PR3; X2 |
| RQ9 Shorts | Is a short an excerpt, a rewording or new material? What do shorts carry, and what do they leave out? | Y1-Y3; Y-E |
| RQ10 Measurement | How much do text kind, speech-to-text model and coding model move each measure, and which Index figures survive? | M1-M6 |

### 2.3 Pre-registered families

**Family B: Bashar sessions on archive.org, on verbatim made-here text.**
- *Population.* Bashar sessions deposited on archive.org and catalogued by the Index. This is not "all of Bashar".
- *Unit.* The session. Dates come from the archive.org item, never from what the session says.
- *Holm.* Correction runs over the tests that pass their gates; with 5 tests the first threshold is .01.
- *Scope.* E3 and E4 enter only if the video-only items are extracted and pass the M1 gate. Otherwise B2, B3 and B5 cover 1984 to 1999.

| ID | Hypothesis | Data | Test and effect | Smallest effect or verdict rule | Gate or run condition | Label |
|---|---|---|---|---|---|---|
| B1 | Core-teaching vocabulary is stable between E1 and E2 | Per-session rate of a frozen core-teaching dictionary per 10,000 Bashar-voice words; confirmation sessions (frame: 136 in E1, 98 in E2) | TOST on the log rate ratio E2/E1; BCa session bootstrap (10,000 resamples, seed 42) | Equivalent if the 90% interval lies inside [0.80, 1.25]. This is reachable if the between-session SD of log rates is at most 0.58 (whole frame), 0.49 (audio items only) or 0.36 (today's held items) | M1 in E1 and E2 | Pre-registered |
| B2 | The share of Bashar-voice words matching a frozen ET-contact dictionary rises with session year | Same sessions | Fractional logit on year plus session type; years permuted within type (m = 9,999); one-sided; effect in percentage points per decade with a BCa interval | Set on the discovery half before registration; default 1 point per decade | M1 | Pre-registered |
| B3 | Stated deadlines for open contact recede across independent sessions | Each session's median stated lower bound for the open-contact window, from verbatim statements typed with a frozen milestone codebook | Theil-Sen slope with a session bootstrap; one-sided permutation against a fixed deadline | The panel's rule: an interval lower bound of at least 1 year per year certifies super-unity drift; an upper bound below 1 rejects it | At least 10 sessions with such statements, otherwise descriptive; dated-statement labels pass M3 | Pre-registered (conditional) |
| B4 | Hedging rises as a deadline approaches (the panel's P1, now on verbatim text) | Conditionality c_i from the frozen 50 phrases in the claim sentence, in the panel's bins of years to the deadline (Δ) | One-sided Jonckheere-Terpstra (m = 9,999); Somers' D with a session-cluster bootstrap | Declared in the registration; default D of at least 0.10 | M5: phrase precision of at least 0.50 in claim sentences. Otherwise "instrument invalid", and B4 leaves the family | Pre-registered (gated) |
| B5 | The share of audience questions about contact and disclosure rises with session year (the panel's P4, now on uncapped verbatim questions) | Question units from the sessions, uncapped, with their tag from the coding run | Mixed logistic model with a session intercept, on year plus type; DSL correction; odds ratio per decade | Default OR of at least 1.2 per decade | M2 (DER at most 20%, question-turn recall at least 0.70) and M3 (alpha at least .667 for the tag) | Pre-registered (gated) |

**Family S: voice and register.**
- *Holm.* With 3 tests the first threshold is .0167.
- *Interpretation, fixed now.* Separation says nothing in favour of a non-human origin, and equivalence says nothing against one. Both are statements about register only.

| ID | Hypothesis | Data | Test and effect | Verdict rule | Gate or run condition | Label |
|---|---|---|---|---|---|---|
| S1 | The channeled register is separable from Darryl Anka's own voice (the panel's registered stylometry) | Single-voice segments of at least 1,500 tokens of made-here text, all from one engine. Bashar-voice sessions against Anka's own-voice podcasts, era-matched where possible: 7 archive.org items from 2024-25 (video-only); the laptop lane would add official sessions | ΔCE, the held-out cross-entropy difference between per-register language models, in nats per token; recording-cluster bootstrap | Three verdicts fixed in advance: **separable** if the 95% interval's lower bound is above +0.15; **equivalent** if the 90% interval lies within ±0.15 (TOST); otherwise **not determined** | M1 in both strata; a 6+6 pilot measures variance before the power statement is written | Pre-registered |
| S2 | Bashar's separation from Darryl Anka is typical of mediums' own-voice versus channeled separation | 30 live-channeling interviews from 11 persons (44.4 h), within and between recordings; channeled spans from GS11 | Cross-validated AUC on 150 function words, with folds grouped by recording; Bashar's AUC placed in the baseline distribution with a bootstrap over persons | Inside or outside the middle 80% of the baseline | M2; span gold with unitizing alpha of at least .667 | Pre-registered |
| S3 | Within Daniel Scranton, texts whose titles name different entities differ in function-word style beyond chance | 1,000-word samples with year and Layer A topic matched. In 2024-26 about 330 titles name the Arcturians and 285 the Creators | Balanced accuracy of Delta attribution, leave-one-year-out; one-sided permutation with labels shuffled within year | A positive claim needs at least 0.60; a TOST against 0.60 supports the null | Title labels pass a 100-title check; at least 200 texts per entity in shared years | Pre-registered (conditional) |

Power for S1 (computed by Draft C, normal approximation):
- 7 recordings against 14 detect only d of about 1.30 at 80% power.
- Equivalence would need a margin of about 1.35 SD.
- So from the cloud alone, S1 can find a large separation but cannot show equivalence. Only the laptop lane and an own-voice exception (decision D3) make "equivalent" reachable.

**Family Q: the same question put to different voices.** Holm correction runs over the tests that meet their run conditions.

| ID | Hypothesis | Data | Test and effect | Smallest effect | Gate or run condition | Label |
|---|---|---|---|---|---|---|
| Q1 | Different voices answer the same question alike, beyond topic | Q&A pairs from L/L Research, Cosmic Agency and the live-channeling interviews; confirmation half only; voices from different persons | Δ = (mean cosine of answers in the same question family from different persons) minus (mean cosine for the same two persons in different families matched on theme); cluster bootstrap by person pair and session; one-sided | Δ of at least 0.05 and d_z of at least 0.2 | Q&A unit span F1 of at least .85 (GS3); embedding validity rho of at least .60 and better than TF-IDF/BM25 (GS6); at least 4 persons and 30 cross-person question families | Pre-registered (conditional) |
| Q2 | Distinctive wording travels along the interview circuit | Person pairs with text of the same kind | MRQAP with double semi-partialling (m = 9,999). Outcome: shared distinctive passages beyond the genre baseline. Predictor: co-appearance weight on shows. Controls: same family, same role, same text kind | Standardised beta of at least 0.2 | At least 15 persons with 50,000 or more words in one text kind, and at least 30 tied pairs, by the registered date; otherwise "not run" | Pre-registered (conditional) |

**Family Y: needs the owner's laptop lane.**
- *Registration.* Registered as an amendment before those data are opened.
- *Holm.* Correction runs over Y1 to Y3.

| ID | Hypothesis | Data | Test and effect | Smallest effect | Run condition | Label |
|---|---|---|---|---|---|---|
| Y1 | Shorts carry more contact and prediction language than long videos of the same channel | The short group against random windows of matched length from the same channel's long videos | Per-channel log ratio, combined by random effects. Primary measure: a frozen contact-and-predictions dictionary rate. Secondary: the PPI-corrected code share. Robustness: Wilcoxon signed-rank test over channels. One-sided | Ratio of at least 1.25 | At least 20 channels with transcripts on both sides | Pre-registered (conditional) |
| Y2 | Excerpted windows carry fewer hedges than unclipped windows of the same parent video | Located excerpts (Y-E) | Conditional Poisson model with parent fixed effects and log words as the offset; cluster bootstrap over channels; one-sided | Rate ratio of 0.80 or lower | At least 300 located excerpts in at least 10 channels; M5 | Pre-registered (conditional) |
| Y3 | The kind of recording predicts the topic mix (the panel's P3, re-tested without the batch confound) | The 75 recordings, transcribed and coded in one pinned run | Bias-corrected Cramér's V; video-cluster bootstrap; within-year permutation | V above 0.2 (the panel's rule) | The 75 fetched by the laptop lane and passing M1 | Pre-registered (conditional) |
| Y-E | (estimand) Per channel, the shares of shorts that are excerpts, rewordings and new material | | Wilson intervals | | | Estimand |

**Family PR: prospective.** Filed before 2027-01-01, under embargo, and evaluated once after 2028-01-31.
- *Dating.* A statement's date is when the collection log first saw it (a cycle runs every 3 hours), not what the text mentions. Texts written after registration are blind by construction.
- *Dependency.* Collection cycles must keep running through 2028.
- **PR1 (estimand).** Among statements first seen after 2027-12-31 that refer back to a 2027 milestone: the shares that re-date it, reframe it, say it did not happen, or do something else. Wilson intervals, with persons weighted equally. Two people code every statement.
- **PR2 (test).** Take a person who gave a target year of 2027 or earlier for a milestone in texts first seen in 2026 to 2027, and who restates that milestone after 2027-12-31: is the new target later? One-sided sign test over person-milestone pairs. With fewer than 10 pairs it becomes an estimate.
- **PR3.** The frozen 2027 rubric, unchanged, scored once on 2030-01-01 by a coder who has not seen the drift results.

### 2.4 Measurement gates (registered; estimation, no tests)

| ID | Estimand | Gate |
|---|---|---|
| M1 | Speech-to-text error per stratum (E1, E2, E3-E4, podcasts, live interviews). Measured: WER, CER, function-word WER, entity-name error, rate of invented text, and run-to-run WER | WER of at most 15% and function-word WER of at most 10% per stratum (the panel's registered gates). A failing stratum's text measures become descriptive |
| M2 | Speaker separation: DER with a 0.25 s collar; recall of audience question turns | DER of at most 20% and question-turn recall of at least 0.70, for any measure attributed to a speaker |
| M3 | Label reliability: human-to-human Krippendorff's alpha first, then model-to-human alpha; per-class precision, recall and F1 | Alpha of at least .667 to use a label, at least .800 for firm claims. For codes in tests, the lower 95% bound of per-code F1 must be at least 0.60 |
| M4 | Digest validity (needs the 75; laptop lane): atomic-fact precision; recall of questions and predictions; share of the 493 quotes found by string match; topic L1. Each by batch | The panel's registered yardsticks: L1 at most 0.15, kappa at least 0.60, Jaccard at least 0.40, prediction match at least 75% |
| M5 | Precision of each frozen hedge phrase inside claim sentences | At least 0.50 pooled, for B4 and Y2. Never used to edit the list |
| M6 | Text-kind and model calibration on works that have both kinds (6 now; 30 once the 24 queued items are transcribed). Measured: how far kind and speech-to-text model shift code shares, topic shares, keyness, embedding centroids, self-reuse, hedge density and question counts | A difference smaller than its calibration shift is not reported as a finding |

### 2.5 Registered exploratory analyses and exploratory sets

**Registered exploratory.** These two run on metadata that readers already profiled, so they stay outside the families.
- **E-H1: naming is nested.**
  - Data: the person-by-family title matrix. Persons with at least 50 listed items; families that pass the title check (precision of at least .90 on 50 titles each). The broad "angels" and "Christ" patterns are dropped unless they pass. A cell counts at 3 or more items and at least 1% of the person's items.
  - Test: NODF against a curveball null (m = 9,999).
  - Threshold of interest: z of at least 2, and NODF at least 5 points above the null mean.
- **E-H2: the interview circuit groups guests by entity family.**
  - Measure: the share of co-appearing guest pairs, weighted by Newman's method, that fall in the same family. It is compared with a curveball null over 9 shows and 28 guests.
  - Unassigned and context guests are left out; including them is a sensitivity check.
  - Threshold of interest: 0.10 above the null mean. The registration states how wide an interval a null result would leave.

**Exploratory sets.** Benjamini-Hochberg correction applies within each set, and every result carries a badge.

| Set | Content | Section |
|---|---|---|
| X1 | Wording spread and reuse between channels; adoption curves (NET5) | 5.13 |
| X2 | Dated statements and timelines across channels | 5.6 |
| X3 | Question bank, Q&A structure, live channeling against conversation | 5.8, 5.4 |
| X4 | Names, mention roles, entity networks (NET1, NET2, NET4) | 5.9, 5.14 |
| X5 | Change within one source: L/L Research by decade, Scranton by year, Bashar tapes by year beyond family B | 5.9-5.13 |
| X6 | Per-year tables and last-N windows | 12.2, 12.3 (was 5.15) |
| X7 | Embedding overlap across filter groups | 5.12 |
| X8 | Topic models and keyness contrasts; the six voices; the Federation and Ashtar family | 5.10, 5.11 |
| X9 | Circulation and the interview circuit (NET3); metadata comparisons of format, length, platform and title language | 5.14, 3.3 |
| X10 | Repetition, formulas and boilerplate within channels | 5.13 |

### 2.6 How registration works

- **What is registered:**
  - codebooks, dictionaries and the gazetteer;
  - JSON schemas and prompts, verbatim;
  - model ids or weight hashes;
  - seeds, thresholds and smallest effects;
  - split files;
  - the analysis code at a tagged commit;
  - the families with their run conditions;
  - the policy for deviations.
- **Where.**
  - OSF's template for secondary data (van den Akker et al. 2021), embargoed so that nothing is public before the paper. Check the current embargo terms.
  - The registration's SHA-256 is timestamped (for example with OpenTimestamps, so only the hash leaves the machine) and committed with a signed tag.
  - Neither the registration nor the tag contains any text from the corpus.
- **When.**
  - Before any confirmation transcript is opened.
  - Family PR before 2027-01-01.
  - Family Y as an amendment, before the laptop lane's data are opened.
- **Splits.** Both are computed from identifiers only, so they can be made today and published with the registration.
  - Bashar items: within each era, sort archive.org identifiers by SHA-256 of `bashar-split-v1:` plus the identifier. The first ceil(0.25 n) go to discovery (102 items) and the rest to confirmation (290). The 2 items already transcribed are moved to discovery.
  - Cross-channel source texts: split 50/50 by recording within each person, by hashed item id with a registered salt.
- **Seal.**
  - Transcription may produce confirmation transcripts, but the analysis loader refuses confirmation ids until `prereg_id` is set.
  - Agents get discovery-only paths, and an access log records every read.
  - `report.py` refuses confirmatory output if any confirmation id was read before the registration timestamp.
- **Disclosure.** The registration lists what had already been seen:
  - the panel's digest results;
  - the 39 interview readings;
  - the 61 made-here transcripts;
  - the readers' profiles of the corpus: counts, speaker-label tallies, title families and network sizes.
- **Deviations.** A dated table records each change, its reason and its effect.

## 3. Filter groups and comparisons

### 3.1 Dimensions

| Dimension | Values | Size today | How it is used |
|---|---|---|---|
| Text kind (always a stratum) | Publisher-written; publisher transcript; platform caption; publisher caption; `stt:<model>@<revision>` | 8,425 source texts; 61 made-here transcripts; 0 captions | Never pooled. Crossed only in M6 |
| Person (source) | 70 persons; 19 with source text, 14 with made-here text | The top three hold 88.5% of source words | Capped or weighted per person |
| Named voice within one person | Scranton's titled entities: about 2,750 titles name the Arcturians, 384 the Creators, 359 an archangel, 237 the Pleiadians, 168 St. Germain, 977 none of these. L/L's labelled speakers (Ra, Q'uo, Hatonn, Latwii). Bashar against Darryl Anka | Large now for Scranton; Bashar after speech-to-text | Within-person designs (S1, S3) |
| Entity family (person level; a researcher's grouping) | Law of One; Arcturian; Taygetan; Federation and Ashtar; Pleiadian; Bashar and Essassani; angels and masters; guides, spirits and mediums; Kryon; other named ET; context; unassigned (24 persons) | Only Federation and Ashtar passes the text rule: 490 texts, 0.86 M words, 3 persons, 53% of them Sam the Illusionist | Metadata comparisons with persons as units; text comparisons mostly descriptive |
| Role (`targets.csv`) | Channeler 59; organisation 2; contactee 2; context 6; publisher 1 | One or two persons with text per role, except channelers | Metadata only |
| Format | Long-form, short, stream, page, own podcast episode, host-show interview; Q&A against monologue | Dialogue share of sampled texts: L/L 69%, Cosmic Agency 31%, Blossom Goodchild 35% | Within persons |
| Length class | Short group (shorts and anything of 5 minutes or less) against the main corpus (over 5 minutes); also 5-20, 20-60 and over 60 minutes | 0-3 min 3,622; 3-20 min 19,368; 20-60 min 15,373; over 60 min 8,027 | Phase 7a |
| Era | Bashar E1-E4; L/L decades (140 to 503 texts and 0.43 to 1.75 M words each); Scranton years (307 to 366 texts a year, 2013-2026) | YouTube rows are undated | Within one source only |
| Platform (lane) | YouTube; own website; podcast feed; archive.org | Tangled with person and text kind | Metadata only; twins for paired contrasts |
| Language | English; German (12 made-here files, 39,145 words); Spanish, Portuguese and Japanese titles | No text comparison is possible | Sanity checks only |
| Channel type | Official against clip and re-upload channels. Bashar has 1 official, 11 clip, 10 re-upload and 16 interview-show channels | | NET3; Phase 7a across channels |
| Interview kind | Live channeling, conversation, commentary, not classified | 30 / 19 / 2 / 138 | S2 baseline; X3 |

### 3.2 Rules for any comparison

1. **Text kinds are never pooled.** Cross-kind numbers appear only in M6, and only on the same works.
2. **Unit of inference.**
   - Across persons: the person.
   - Within a source: the recording or session.
   - Phase 7a: the channel.
   - Platform contrasts: the work pair.
   - Never segments or tokens.
3. **Size rule** (the corpus reader's).
   - A text comparison needs, on each side, at least 50 texts, 100,000 words and 3 persons, with no person over 60% of the words.
   - A metadata comparison needs at least 300 items and 5 persons on each side.
   - Added here: a claim that generalises across persons needs at least 10 persons on each side. With 19 persons, r = 0.5 has a 95% interval of 0.06 to 0.78; with 11 persons, -0.14 to 0.85.
   - Below these sizes: a within-source design or description, with the claim limited to the named persons.
4. **Caps and weights.**
   - Each person is capped, at 300,000 words or 1,500 units per model fit, drawn with a seed.
   - Persons are weighted equally when the claim is about persons.
   - These caps limit what one pooled model fit draws per person. They do not limit what is collected, transcribed or coded, which is every recording over 5 minutes (12.1).
5. **Matched sizes.**
   - Networks, coverage and vocabulary measures grow with sample size.
   - So the larger side is rarefied to the smaller (200 subsamples), and rarefaction curves are shown.
6. **Model-coded shares per group.**
   - A group needs about 150 to 250 gold units of its own for ±5 points when model and humans disagree on 10 to 15% of units (231 at 15%).
   - Without that, the share is corrected with pooled error rates and labelled "group-specific error not measured".
7. **No double counting.** Twins and duplicates are counted once (twin marks, MinHash, audio fingerprints) before any count.
8. **What every comparison table states:** the text kind; the n of items, recordings and persons; and the basis of each date.

### 3.3 What can be compared, and when

Key to the "When" column:
- *now*: on data already held, after the freeze;
- *STT*: after speech-to-text of held or queued audio;
- *lane*: after the owner's laptop lane delivers.

| Comparison | Sides today | Unit | When | Analyses | Family or set |
|---|---|---|---|---|---|
| Bashar E1 against E2 (against E3-E4) | Frame 183 / 131 / 49 / 26 items; with audio 151 / 89 / 4 / 0; held 96 / 45 / 4 / 0 | Session | STT; E3-E4 after extraction | 5.2, 5.8-5.11 | B1-B5; X5 |
| Bashar channeled against Darryl Anka's own voice | 7 era-matched video-only sessions against 20 podcasts (2025-26) | Recording | STT and extraction; lane improves it | 5.3 | S1 |
| Own voice against channeled inside live interviews | 30 interviews, 11 persons, 44.4 h | Segment in recording; person | STT, GS11 | 5.3 | S2 |
| Scranton entity against entity | About 330 against about 285 titled texts in 2024-26 | Text, year-matched | now | 5.3, 5.11 | S3 |
| L/L Research by decade and by labelled entity | 1970s 234 texts (0.43 M words) to 2020s 146 texts (0.79 M); Ra 106 texts, undated | Session, clustered by year | now | 5.8-5.13, 12 | X5 |
| Scranton by year; last N against history | 307 to 366 texts a year; 2010s 2,455 against 2020s 2,505 texts | Text | now | 5.9-5.13, 12 | X5, X6 |
| Six named voices, each over 100k words: Ra and Q'uo, the 9D Arcturian Council, the Taygetans, Sam the Illusionist's source, the Federation of Light, Laarkmaa | Each voice is one source | Text; voice (n = 6) | now | 5.11, 5.12, NET2 | X7, X8 (descriptive; no group p-values) |
| Q&A against monologue within L/L, Cosmic Agency and Blossom Goodchild | Samples of 300 / 300 / 227 | Text within person | now | 5.8, 5.11, NET2 | X3, X8 |
| Federation and Ashtar family against other sources | 490 texts, 0.86 M words, 3 persons, capped | Person | now | 5.11, 5.12 | X8 |
| Live channeling against conversation interviews | 21 against 16 source texts, about 250k words a side; mostly one show; 13 of the 19 conversations are Darryl Anka | Interview, show held fixed | now (keywords only) | 5.4, 5.11 | X3 |
| Source text against made-here text of the same work | 6 works; 30 after the 24 queued items | Work | now / STT | 5.1 | M6 |
| Short group against main corpus within a channel | 39 to 47 channels qualify by listing; 0 transcripts | Channel (paired) | lane | 5.5 | Y1-Y3, Y-E |
| The 75 by kind of recording | 75 | Recording | lane | 5.5 | Y3, M4 |
| Texts first seen after registration | Scranton about 360 a year; others | Person-milestone pair | 2027-2028 | 5.6 | PR |
| Metadata: format mix by family or role | Families with 5 or more persons: unassigned 24, angels and masters 7, Pleiadian 7, Federation and Ashtar 6, context 6, guides and spirits 5, Bashar and Essassani 5 | Person | now | 3.6 | X9 |
| Metadata: durations of shorts against long-form | 51 channels with both | Channel (paired) | now | 3.6 | X9 |
| Metadata: Q&A in the title; platform on twins; title language within bilingual channels | Q&A in title: 865 items, 34 channels. Twins: 3,764 pages and 966 podcast episodes matched to videos. Spanish titles: 652, 76% from one person | Item within person; work pair; item within channel | now | 3.6 | X9 |

### 3.4 Crossings worth making, and some that are not

**Worth making:**
- era by format inside L/L Research, which separates a change of genre from a change of era;
- interview kind inside one show, which compares channeled answers with human answers with the host held fixed;
- text kind on the same work (M6);
- entity family by format, with persons as units;
- role by how often a person names others (NET4);
- family by circulation (E-H2);
- platform on the same work (twins);
- language within bilingual channels;
- era by naming: the Bashar tapes against later recordings, and the Ra sessions against later L/L Research;
- shorts within a channel (Y).

**Not worth making now:** family by era, platform by family, and language by family. Each collapses to one or two persons, so it would measure individuals, not groups.

**A control, not a finding:** era by audio quality.

### 3.5 How two groups or two networks are compared

- **Same footing.** Both sides use the same node set (the same lexicon version), the same window rule and the same text kind.
- **Same size.** The larger side is rarefied to the smaller side's window count under the same per-person caps, repeated 200 times, and rarefaction curves are shown.
- **Measures:**
  - correlation of NPMI over the node pairs present in both networks;
  - Jaccard similarity of the two backbone edge sets, with a bootstrap interval;
  - differences in density, transitivity, modularity and family assortativity, with permutation at the right level:
    - documents are permuted within each person for within-person contrasts;
    - persons are permuted for between-person contrasts;
    - exact enumeration is used when there are few relabellings. Three persons against three allow only 20, so no p-value is given;
  - edge-level differences in the log odds ratio, with Benjamini-Hochberg correction;
  - change in centrality ranks (Spearman, with a bootstrap);
  - agreement between the two partitions on shared nodes (AMI).
- **Hypotheses about pairs of nodes** use QAP or MRQAP (m = 9,999), and a Mantel test for two matrices.
- **Pairwise comparisons multiply:** 19 persons with source text give 171 pairs, and 14 with made-here text give 91. So the plan shows full matrices with intervals instead of testing every pair, and applies Benjamini-Hochberg wherever pairs are tested.

### 3.6 Statistics by kind of measure

| Measure | Method | Interval and unit |
|---|---|---|
| Category by group | Chi-squared with a Monte-Carlo p-value for sparse tables; bias-corrected Cramér's V (V of at least 0.2 to call an association, the earlier rule) | Cluster bootstrap by person or session (`demand.py`, with persons in place of videos) |
| Share per item | Binomial mixed model with a person intercept, or GEE | Odds ratio with a cluster bootstrap |
| Model-coded share | PPI for means, DSL for regressions | Interval combining the gold sample and the model labels |
| Continuous (length, pace, cosine) | Mixed model (segment within session within person), or per-person medians with Cliff's delta | Bootstrap over persons |
| Vocabulary | Weighted log-odds with an informative Dirichlet prior; Log Ratio; Gries' DP; Benjamini-Hochberg over the vocabulary; G² only as a cross-check | Documents or persons resampled, never tokens |
| Topic prevalence | Regression of topic proportions on covariates (STM's estimateEffect where R exists) | Bootstrap over documents |
| Style | Delta on 150 function words; ΔCE; unmasking | Held-out documents; recording-cluster bootstrap |
| Trend within a source | Theil-Sen and Spearman; change points exploratory only | Bootstrap within year; block bootstrap by month for daily sources |
| Equivalence | TOST with registered margins | 90% interval |
| Permutation | p = (b+1)/(m+1); m = 9,999 for confirmatory tests, 999 for exploratory ones; exact enumeration when relabellings are few | |
| Robustness | Specification curve over window size, backbone threshold, resolution, K, lexicon version, caps, name masking and quality filters | Share of specifications that support each claim |

## 4. Processing steps with a small model

### 4.1 What each size of model does here

| Tier | Size | Used for | Not used for |
|---|---|---|---|
| Rules and string matching | | Final counts of entities, terms and hedges (the frozen 50 phrases); n-grams; TF-IDF; keyness; Q&A parsing where speaker labels exist | Anything that needs judgment |
| Encoders | 8M to 600M parameters | Sentence embeddings; NLI checks that a summary point or answer pair is supported | Labels |
| Tiny generative models | 1B or less | Nothing in content coding. In channels-ET's pilot, Qwen2.5-0.5B gave all 9 parsed items the same theme, and reversing the option order changed 6 of 8 labels. Qwen3.5-0.8B gave 11 of 12 items one theme | |
| Small generative model (the bulk coder) | `claude-haiku-5-5`, or a 7-9B open-weight instruct model on a GPU | The three reading passes (4.3) | Final counts of names or terms |
| Auditor | `claude-sonnet-5-5`, or an open model of 30B or more | Re-codes a random 10%; disagreements go to a person | Accuracy claims: its agreement is reported as agreement, never accuracy |

### 4.2 The steps: what each reads, writes and costs, and how it is checked against people

| Step | Model | Reads | Writes (private unless marked) | Cost per audio hour | Checked against people by |
|---|---|---|---|---|---|
| 0. Speech-to-text | faster-whisper base.en now (int8, CPU); large-v3 on a GPU for confirmatory strata if the M1 benchmark picks it; Parakeet TDT 0.6B if the owner allows it | Audio (Opus) | Timed segments (JSON) and text. The manifest has model revision and weight hash; to add: beam size, temperature fallback, `condition_on_previous_text`, VAD parameters, per-segment compression ratio | base.en: about 10 minutes of this machine when idle (5.9x real time), about 46 minutes under collection load (1.3x). large-v3 on a GPU: about 1 to 2 minutes (estimate, to measure) | GS12: blind one-minute windows per stratum (M1) |
| 1. Quality flags | Rules | Segments | Flags per unit: compression ratio over 2.4; mean log-probability under -1.0; no-speech probability over 0.6; repeated segments; under 100 words a minute; language mismatch | Seconds | GS12 windows over silence and music |
| 2. Speaker turns | pyannote speaker-diarization 3.1 on a GPU | Audio | Speaker turns (which speaker the most speech belongs to is checked) | GPU minutes | GS13: 2 hand-labelled hours per stratum (M2) |
| 3. Units | Rules | Text | Units of about 200 words (about 85 seconds of speech), cut only at segment or paragraph boundaries, never across a speaker label. Also: offsets or times, boilerplate marks, a copy with names masked, and the split half | Seconds | Spot checks |
| R1. Structure | Bulk coder | 1,500-word windows overlapping by 200, in order | Turn type, speaker role, question spans, future statements with any date, names not in the gazetteer, ads and housekeeping; all with offsets | Part of the $0.006 below | GS3 (questions and dated statements) |
| R2. Codes | Bulk coder | Each 200-word unit alone, blind to person and title | Layer A codes (multi-label), an evidence span of at most 12 verbatim words per code, the modality class, and whether the entity is the one speaking | Part of the $0.006 | GS1 (1,200 units), GS4 (question themes) |
| R3. Summaries | Bulk coder | R1 windows of items of 1,500 words or 10 minutes and more | 5 to 10 atomic points with offsets and code tags; an abstract of 60 to 120 words written only from those points | Part of the $0.006 | GS5 (320 points) |
| Names | Gazetteer string match; GLiNER-small or spaCy on a 2% sample to find new names | Units | Counts per item; candidate names for review | Seconds | GS8 |
| Embeddings | Model2Vec (exploration); all-MiniLM-L6-v2 or bge-small through ONNX on CPU; an E5/BGE-class model on a GPU for final vectors | Windows of 150 or 300 words | Vectors (private, because they can be inverted back to text) | About 42 windows per audio hour; seconds | GS6 |
| NLI checks | DeBERTa-v3 MNLI cross-encoder | Summary points with their evidence; answer pairs | Entails, neutral or contradicts | CPU for samples | GS5; 200 answer pairs |
| Audit | `claude-sonnet-5-5` through Batches, on a random 10% | Same inputs as R2 | Second labels | About twice the Haiku bill, spread over the whole corpus | Agreement only |

### 4.3 The three reading passes

- **R1, structure.** It reads windows in order, so turn-taking and the speaker's role can be seen. Its output is used for:
  - question units (5.8);
  - dated statements (5.6);
  - new names (5.9);
  - masking ads and housekeeping.
- **R2, codes.** It reads units one at a time, blind to person, title and year, so that labels cannot follow who is speaking. Code shares are counted by words and corrected with PPI.
- **R3, summaries.** These are for reading, for navigation and for the "last N recordings" view only. They are never a source of measurements. Scranton's daily texts (median 609 words) get codes but no summaries.

### 4.4 Codebook and prompts

**Layer A** is the set of codes used across channels. It is built from channels-ET's 10 reading codes and 8 Q&A themes and from the Index's 20 tags, with every example term removed:
1. contact and disclosure;
2. predictions and timelines;
3. beings and identity;
4. cosmology and ontology;
5. practice and technique;
6. beliefs, agency and manifestation;
7. emotion, fear and self-worth;
8. health, body, healing and death;
9. relationships, family and sexuality;
10. society, politics, economy and technology;
11. money and career;
12. ancient history and origins;
13. calendars, astrology and numerology;
14. channeling mechanics and the channel's account of itself;
15. validation, qualification and criticism;
16. framing and promotion;
17. other or unclear.

R2 also records the modality of the main claim, using channels-ET's five classes: conditional, possibility, probability, absolute and imperative.

**Layer B** codes are specific to one voice and used only within it.
- For Bashar, they are the Index's 20 tags, renamed neutrally and given no examples. For instance, the tag named `et_contact_disclosure_2027` becomes "contact and disclosure".
- Other voices get Layer B codes only after a person has reviewed their TF-IDF terms.

**Prompt rules:**
- no example terms, names or years anywhere in a prompt;
- the codebook order is fixed and recorded;
- "unclear" is always allowed;
- every output must validate against a JSON schema;
- every evidence span is string-matched against the normalised unit, and a label whose span does not match is void.

Two checks on the development set measure prompt effects:
- *Order reversal:* the share of labels that change when the codebook order is reversed.
- *Priming:* adding the old prompt's example terms back in; any term whose frequency more than doubles is flagged.

channels-ET's 10 keyword dictionaries are the baseline that every model must beat on each code.

### 4.5 How the runs are made

**Model and route.**
- The bulk coder is `claude-haiku-5-5`, called by its exact id. It costs $0.10 per million input tokens and $0.50 per million output tokens for prompts of up to 100K tokens; every request here is far below that.
- Calls go through the Message Batches API:
  - 50% off every token, cache reads included;
  - up to 100,000 requests or 256 MB per batch;
  - most batches finish within an hour, and none takes more than 24 hours;
  - results are kept for 29 days.
- These prices and limits come from the API reference, cached on 2026-11-03; check them before the run.

**Agents and bulk rows.**
- The roadmap (Phase 7c) names Claude Haiku in batches through the Message Batches API for the bulk rows; agents run the pilots, check them and adjudicate disagreements.
- Bulk rows still go through Batches with the exact id, because the agent alias `haiku` does not record which model produced each row. Every row stores the returned model id and its token usage.
- If the owner prefers agents for coding as well, each row must record the model id the agent reports. Section 12.5 finds this unworkable at the corpus's size, so agents run pilots and adjudication only.

**Settings.**
- *Output format:* structured outputs through `output_config.format` with a JSON schema.
- *Thinking:* this model thinks by default (adaptive, effort medium). Coding runs send `thinking: {type: "disabled"}`, which is accepted at effort high or below, or effort low, whichever the development set favours. The choice is recorded.
- *No temperature:* this model rejects non-default sampling parameters with a 400, so the "temperature 0" in drafts B and C is impossible. Stability is measured instead by running 5% of units a second time and reporting agreement per code.
- *Prompt caching:* the codebook sits in a fixed system block with a cache breakpoint; the minimum cacheable prefix is 512 tokens. Costs are planned as if the cache never hits.
- *Refusals:* the model can stop with `stop_reason: "refusal"`, and it has no server-side fallback. Refused units are counted per pass and coded by the auditor model or by a person.

**Batches.**
- `custom_id` is `item:unit:pass:run`, and results are matched by id, never by position.
- Units go to batches at random, never by person, kind or year.
- A 100-unit control set goes into every batch and must come back with the same labels.
- One model version codes the whole corpus. If the model changes or is retired mid-study, everything is run again; versions are never mixed.
- Phase 7a material is coded in its own run, linked to the main run through the control set.

**Run record.** Each pass gets a public record that contains no corpus text:
- run id and model;
- hashes of the prompt, schema and codebook;
- dates and counts;
- parse rate, and the share of labels whose evidence span matched;
- refusals;
- agreement on the repeated 5%;
- cost.

**Open-weight route.**
- One 7-9B instruct model with a permissive licence, pinned by repository revision and weight SHA-256.
- It runs under vLLM or llama.cpp with greedy decoding, JSON output guided by the schema, and prefix caching. The engine version, quantisation and GPU are recorded.
- It is used in two cases:
  - if the owner wants no text to leave their own machines;
  - to replicate, on a 20% sample, the two labels that enter tests: the question tag and dated statements.

**Privacy.**
- Sending third-party transcripts to a provider is the owner's decision (D4), and the account's data terms decide what it means (D14); the reader agents already did so for 39 interviews.
- Units flagged for personal disclosure go to the local route or are masked.

### 4.6 Cost

*Recomputed on 2026-11-14 for the whole main corpus (12.1). It replaces the earlier set, whose long videos were capped at 50 per channel.*

**Token budget per audio hour.** One hour of audio is about 8,221 words: the measured median, with a 10th to 90th percentile range of 5,965 to 9,800. That is 42 units and 7 windows.
- R1 to R3 together use about 54,500 input tokens that cannot be cached, 81,200 that can, and 10,440 output tokens.
- This assumes 1.7 tokens per word: this model's newer tokenizer counts about 30% more tokens than Haiku 4.5's. Measure it with `count_tokens` on the first batch.
- It also assumes thinking is off. If adaptive thinking at low effort wins the bake-off, output tokens rise; even five times as many would add only about $0.01 per audio hour.
- The local throughputs below are assumptions, to be replaced by a measured benchmark.

| Route | Per audio hour | Source texts (about 1,620 hour-equivalents) | Main corpus (about 23,200 h of known length) |
|---|---|---|---|
| Haiku 5.5, Batches, cache hits | about $0.006 | about $10 | about $140 |
| Haiku 5.5, Batches, cache never hits | about $0.009 | about $15 | about $210 |
| Haiku 5.5, standard API | about $0.012 | about $20 | about $280 |
| 10% audit with Sonnet 5.5 through Batches | about $0.011 | about $18 | about $255 |
| 7-9B open weights on one 24 GB GPU (assumed 4,000 tokens/s reading, 1,000 tokens/s writing) | about 21 GPU-seconds | about 9 GPU-hours | about 135 GPU-hours |
| 3B quantised on this CPU (assumed 20 / 5 tokens/s) | about 72 minutes | about 81 days: not workable | about 3 years: not workable |
| 1B on this CPU | about 24 minutes | Not workable, and tiny models failed the pilot | Not workable |
| Embeddings | about 42 windows | About 93,000 windows of 150 words (5.12). MiniLM: about 5 h on this CPU (assumed 5 windows/s) | About 975,000 windows. Model2Vec: minutes on CPU. MiniLM: about 2 days on this CPU, about 5 minutes on a GPU. bge-m3 class: about 2 h on a GPU. Storage: about 1.5 GB at 384 dimensions |

The totals are the per-hour figures times the hours, rounded. What they cover:
- **Source texts:** 13.3 M words at 8,221 words an hour.
- **Main corpus:** every recording over 5 minutes, with no upper length limit and no cap per channel: 45,515 works, about 23,200 h of known length, about 21,000 h of it in works on YouTube (12.1). It includes the held audio, the rest of the Bashar archive.org queue and the podcast backlog. The 7,647 works of unknown length are not priced.
- **Not in the table: the short group** (Phase 7a), coded in its own run (4.5): 6,743 works of 5 minutes or less (311 h) and 16,115 shorts, which have no length in the listings (about 268 h at an assumed minute each). Its long side is now the main corpus itself, no longer 1,391 h of long videos capped at 50 per channel.

**Speech-to-text costs more than the model passes, and it comes first.**
- The backlog is about 789 h held without transcripts, 636.7 h left in the archive.org queue and 1,442.6 h of podcasts: about 2,870 h in all.
- On this machine that is about 490 hours of wall time when idle (5.9x) and about 2,200 hours under load (1.3x).
- With large-v3 on a GPU it is about 62 GPU-hours, at about 46x real time (the library's figure for large-v2 on an 8 GB card).
- The whole main corpus (about 23,200 h) would take this machine about 164 days when idle and about 2 years under load. So it is split (12.10, step 0): about 3 weeks of cloud CPU for the about 3,100 h off YouTube, and about 500 GPU-hours with large-v3 for YouTube's audio (not measured).

**Priority order for transcription:**
1. the 24 paired items (33.8 h), for M6;
2. the M1 strata samples;
3. the 102 Bashar discovery items;
4. the live interviews;
5. the confirmation items, under the seal;
6. the rest, in the seeded order by person, year and length band of 12.10 (step 4), long files included.

**Human coding, about 205 hours (section 4.7), is the real cost.**

### 4.7 Validation against human coding

**Order and decision rules** (pre-registered):
1. **Human reliability comes first.**
   - Two people code the double-coded units without seeing any model output, and human-to-human Krippendorff's alpha, with a bootstrap interval, is reported before anything else.
   - If only the owner codes, the reliability sample is coded twice, at least two weeks apart, and reported as intra-coder reliability. That is a weaker standard, and the plan says so.
2. **The codebook is revised on the development half only.** Version 2 is then frozen.
3. **Bake-off on the development half.**
   - Candidates: `claude-haiku-5-5`, one 7-9B open model, and optionally one 3-4B open model, with the auditor as a reference and channels-ET's 10 dictionaries as the baseline.
   - Measured for each candidate:
     - per-code F1, and alpha with the model counted as one more coder;
     - confusion matrices;
     - parse rate and the share of evidence spans that match;
     - agreement on repeated runs;
     - the order-reversal and priming effects;
     - refusals and cost.
4. **Choosing the model.** The cheapest model wins if, in each text kind, it reaches alpha of at least .667 with the human consensus and a per-code F1 whose lower 95% bound is at least 0.60, on every code used in a test.
   - A code the model fails is reported from the gold sample only, or dropped.
   - A code with human-to-human alpha below .667 is dropped; between .667 and .800 it is exploratory only.
   - If two prompt wordings move label shares by more than the gold interval, the labels are reported as prompt-sensitive.
5. **One run, one scoring.**
   - One run codes everything, and the test half is scored once.
   - Corpus shares use PPI (Angelopoulos et al. 2023) for means and DSL (Egami et al. 2023) for regressions, by group wherever the group has gold.
   - Raw model counts appear only next to the corrected ones.
6. **The 39 interview readings are model labels.** People check them in GS11.

**Gold sets.** Coding sheets are opened from the private store, coded blind to model output, and never uploaded. Every sample is a probability sample with known weights, as PPI and DSL require.

| Set | What people code | Size | Sampling | Feeds | Hours |
|---|---|---|---|---|---|
| GS1 Codes | Layer A codes, modality, whether the entity speaks | 1,200 units: 600 development (discovery half) and 600 test (confirmation half); 300 test units coded twice | Two-thirds source texts, one-third made-here; spread over L/L, Scranton, Cosmic Agency, other sources, Bashar tapes, interviews and podcasts; rare codes oversampled through a dictionary pre-screen | M3 for every code; Y1 secondary measure; X sets | About 50 |
| GS2 Phase 7a | Short-group units, length-matched long windows, short-to-parent pairs | 230 + 230 + 200 | Stratified by channel | Y1 secondary; Y-E thresholds | About 19 |
| GS3 Questions and dated statements | Question spans and the asking turn; future statements with their dates, marked in the same pass. Attributes coded on 200 statements | 12 session-hours: 3 from E1, 3 from E2, 3 interviews and podcasts, 3 labelled L/L or Cosmic Agency sessions (to check the rule parser). A second coder does 25% | By hash within stratum | B3, B4, B5, Q1 (span F1 of at least .85), PR | About 30 |
| GS4 Question themes | The tag of each question | 600 questions, at least 15 per tag; a second coder does 150 | Stratified by era and predicted tag | B5 | About 12 |
| GS5 Summaries | Each point: supported, partly supported or not supported | 40 recordings x 8 points = 320 | Stratified by source | 5.7 (target: at least 0.90 supported) | About 6 |
| GS6 Meaning pairs | Window pairs (same idea, related, unrelated) and question pairs (same question or not) | 300 + 300 | Spread over cosine deciles | Q1 (rho of at least .60); thresholds in 5.4 and 5.12 | About 6 |
| GS7 Topics | Word intrusion and topic intrusion | About 100 items per chosen model; two raters | | 5.10 | About 2 |
| GS8 Names | Lexicon precision and recall on windows; the role of each mention; precision of each title pattern | 300 windows by two coders; 300 mentions; 50 titles per family | | NET1, NET2, 5.9 (precision at least .90, recall at least .80; alpha between coders at least .80 first) | About 6 |
| GS9 Repetition | Near-duplicate and containment candidate pairs | 200 | Stratified by score | 5.13 (precision at least .95) | About 2 |
| GS10 Hedges | Whether each phrase hit is a hedge in its claim sentence | 400 hits, at most 8 per phrase | Stratified by phrase | M5, which gates B4 and Y2 | About 4 |
| GS11 Interviews | The kind of each typed live or conversation interview (heard around the cited evidence, blind to the model's label); channeled and own-voice spans | All 49 interviews; spans in 12 interviews, at least 1 per medium | | S2 (alpha of at least .80 for kind; unitizing alpha of at least .667 for spans, median boundary error of at most 15 s) | About 20 |
| GS12 Speech-to-text | 60-second windows transcribed from the audio without seeing the machine text. A second person redoes 25%; 10% of windows lie over silence or music | At least 12 files x 3 windows per stratum, 5 strata (about 180 audio minutes) | Inside speech, by hash | M1, which gates every measure on made-here text | About 30 to 43 |
| GS13 Speaker turns | Speaker turns | 2 h per stratum (E1, E2, interviews) | By hash | M2, which gates B5 and S1 | About 15 |

**Totals.** About 205 hours in all; about 150 of them feed the gates of the confirmatory families. The rest can shrink.

**Why these sizes** (computed by drafts A and C):
- A code present in 10% of units needs about 500 random units to yield 50 positives (1,000 at 5%), hence the oversampling.
- A recall of 0.8 is known to ±0.11 with 50 positives and to ±0.078 with 100.
- A PPI share known to ±5 points needs about 231 gold units per group at 15% disagreement, 154 at 10% and 385 at 25%.
- A binomial ±5 points needs 385 units at p = .5, 246 at .8 and 139 at .9.
- A mean WER is known to ±0.045 with 12 files if the SD between files is 0.08, and to ±0.035 with 20.

## 5. The analyses

### 5.0 Conventions for every result and figure

**Every result:**
- states n first (items, recordings, persons) and names the unit that was resampled;
- carries its text kind and a `coding_level`: rule, string match, `model:<id>@<prompt hash>`, human, or human consensus;
- carries a grade:
  - Established: confirmatory, gates passed, and Holm-significant or equivalence shown;
  - Frontier: confirmatory, but with a tentative gate or a "not determined" verdict;
  - Speculative: exploratory.

**Statistics:**
- an effect size and a 95% interval for every estimate, 90% for TOST;
- permutation p = (b+1)/(m+1);
- BCa bootstrap with at least 2,000 resamples (10,000 for confirmatory tests, seed 42) over the independent unit;
- mixed models for segments within recordings within persons;
- Holm correction within families, Benjamini-Hochberg within exploratory sets, Benjamini-Yekutieli for sets that span the whole vocabulary;
- "significant" is used only for confirmatory tests after Holm.

**Every figure:**
- shows n in its title;
- is split by text kind;
- carries an EXPLORATORY or CONFIRMATORY badge and the banner.

The numbers behind each figure (counts, edge lists, effect tables) are published as CSV, so the dashboard draws them; no text goes out.

**Display rules** (from Draft B):
- one share across groups with few persons: a dot plot of every person, with the group median and interval on top;
- a group by many categories: a heatmap of standardised residuals with n per row, not stacked bars;
- two groups by vocabulary: a Fightin' Words scatter, never word clouds;
- many effects at once: a forest plot sorted by effect, with nulls in the same panel;
- change within a source: a line with a 95% ribbon, or small multiples, never dual axes;
- paired units: a slope plot or a Bland-Altman plot;
- distances among a few voices: a heatmap with a dendrogram and bootstrap support. t-SNE and UMAP maps are allowed only as EXPLORATORY;
- dense networks: an adjacency matrix ordered by community, never a hairball;
- sparse backbones: node-link drawings with a fixed-seed layout and only the top nodes labelled;
- two-mode networks: a biadjacency heatmap, or a two-column layout when sparse;
- flows: alluvial or layered diagrams;
- networks over time: small multiples on a fixed layout;
- null-model tests: the null distribution as a histogram, with the observed value and z;
- robustness: a specification curve.

### 5.1 Measurement (M1-M6)

**M1, speech-to-text error.**
- *Audit design.* The registered audit is made blind. A person transcribes each 60-second window from the audio without seeing the machine text. That fixes `verify.py`'s QA sheet, which puts `machine_text` beside an empty `human_text` column and so invites the person to anchor on the machine.
- *Scoring.* Whisper's English normaliser and jiwer, with a bootstrap over files. Function-word WER uses the 150 Delta words. An entity-name variant map (Bashar, Essassani, Yahyel and others) is built on discovery and then frozen.
- *Stability.* 2% of files are transcribed twice, to measure WER between runs.
- *Engine benchmark,* on discovery windows: base.en, distil-large-v3, large-v3 (GPU), and Parakeet if the owner allows it.
- *Publisher texts.* Against the Ra tapes this is reported as "agreement with the publisher text", because publisher texts are edited. On a 1981 tape base.en scored 0.729, mostly from dropped quiet passages: only 553 of 866 words were recovered. On the 16 Sounds True episodes, base.en against large-v3-turbo measures disagreement, not accuracy.
- *Pinning the configuration.* `transcribe.py` runs the batched pipeline by default, and only its unbatched path sets `condition_on_previous_text=False`. So one configuration is fixed for the whole confirmation set, with beam 5 and VAD settings tuned on discovery only.
- *Figures:*
  - Fig M1-a: WER and function-word WER by stratum, dot and whisker, with the 15% and 10% gate lines;
  - Fig M1-b: WER against mean log-probability, one point per file;
  - Fig M1-c: engine benchmark by era, grouped dots;
  - Fig M1-d: rate of invented text in silent windows, bars.

**M2, speaker separation.**
- *Method.* pyannote on a GPU. The cluster with the most speech is taken to be Bashar, and that is checked; in interviews, host and guest are separated.
- *Fallback.* If the gate fails, B1 and B2 use whole-session text with a sensitivity check, and B5 becomes descriptive.
- *Figure:* Fig M2: DER and question-turn recall by stratum, dots with intervals.

**M3, label reliability.**
- Fig M3-a: reliability forest plot, human-to-human against model-to-human alpha for each label.
- Fig M3-b: confusion matrix for each code.

**M4, digest audit** (laptop lane).
- *Method.* A transcript-based audit of the digests, by batch. The panel's registered second-model re-verification runs only as agreement and is logged as a deviation.
- *Figure:* Fig M4: digest audit metrics by batch (A, B, C), with intervals.

**M5, hedge phrases.** Fig M5: precision of each hedge phrase, bars with Wilson intervals.

**M6, calibration.**
- Fig M6-a: Bland-Altman plots for each measure, source text against made-here text of the same work.
- Table M6: "safe comparisons", meaning the measures that move less than their own sampling error when the text kind or model changes.

### 5.2 Bashar sessions over four decades (family B)

**Inputs.**
- Confirmation sessions, with Bashar-voice text taken from speaker-separated made-here transcripts.
- Dictionaries frozen before registration, drawn from three sources:
  - glossary terms whose sources lie outside the digests;
  - channels-ET's dictionaries (ontology, agency and free will, time and probability, contact and others);
  - the speech-to-text variant map.

**Methods and figures.**
- **B1.**
  - *Method:* the log rate ratio E2/E1, with a BCa interval, tested by TOST.
  - *Sensitivity:* whole-session text; inverse-probability weights (frame count over analysed count, by era and type); the better half of sessions by audio quality; counts corrected for speech-to-text term recall. The weights assume that losses within a stratum are unrelated to content; that is stated, not tested.
  - *Figures:* Fig B1-a, an equivalence plot of the 90% and 95% intervals against the [0.80, 1.25] margins; Fig B1-b, a beeswarm of session rates by era.
- **B2.**
  - *Method:* the fractional logit with permutation, as in 2.3.
  - *Figures:* Fig B2-a, the contact share against session year with a smoother and interval band; Fig B2-b, the contribution of the top 10 dictionary terms in each era.
- **B3.**
  - *Method:* statements from R1 with human-checked attributes (only human-checked statements if there are 300 or fewer); a Theil-Sen slope with a session bootstrap; permutation p.
  - *Figures:* Fig B3-a, stated target year against session date, with slope-0 and slope-1 reference lines; Fig B3-b, a verbatim ledger Gantt chart in the layout of the panel's F1, coloured by milestone type, with n in the caption.
- **B4.**
  - *Method:* c_i on claim sentences in the bins over 10 years, 5-10, 1-5, under 1, and after the deadline; Jonckheere-Terpstra permutation; Somers' D. The partial Spearman controlling for session date stays exploratory, as the panel's E3 was.
  - *Figure:* Fig B4, pooled conditionality by bin with intervals, placed beside Fig M5.
- **B5.**
  - *Method:* the mixed logistic model with DSL correction.
  - *Figures:* Fig B5-a, tag shares by era with DSL-corrected intervals; Fig B5-b, a residual mosaic of tag by era (descriptive).

**Alongside the tests (exploratory):**
- An STM with era, type and audio quality as covariates: K in {10, 15, 20, 30} with 5 seeds, plus coherence, exclusivity, held-out likelihood and human intrusion checks.
- Per-era co-mention backbones with Leiden communities, as the descriptive replacement for Kendall's W.
- The frozen rubric applied to resolved open-contact claims from 1984 to 2009, descriptive only, with Clopper-Pearson intervals.
- Figures: Fig BX-a, STM topic prevalence by era; NET-B, per-era co-mention backbones on a fixed layout.

### 5.3 Voice and register (family S)

**Documents.** Single-voice segments of at least 1,500 tokens of made-here text, all from one engine.
- Speaker turns come from publisher transcripts where those exist, otherwise from speaker separation.
- Only Darryl Anka's own turns are used, and on the tapes only the entity's turns.
- If session tapes include spoken introductions by Darryl Anka (checked on a sample), they give a contrast inside the same tape.

**Features:**
- F1: Burrows' Delta on 150 function words, with a bootstrap.
- F2: ΔCE from per-register language models. The primary model is a KenLM 5-gram on CPU; a GPT-2-small fine-tune on a GPU is the sensitivity check.
- F3: unmasking.

**Matching.**
- By Layer A code proportions taken from transcripts, never from digests.
- By register, answers against answers.
- Declared deviations from the 2026 registration: matching by transcript codes, and podcast interviews in place of the 21 YouTube interviews.

**Placebo.**
- Six podcast hours are degraded to sound like cassette tape (narrow band, noise, compression) and transcribed again with the pinned engine.
- The distance between the clean and degraded versions of the same speech is the floor that audio and transcription differences alone can produce.

**Pilot,** on discovery data only.
- 6 + 6 recordings: E4 sessions once extracted, and 6 podcasts chosen by hash, which then leave the confirmation set.
- It measures variance and the correlation inside a recording.
- The power statement is written before registration.

**Figures:**
- Fig S1-a: ΔCE per document by class, with the ±0.15 band and the zero line (the panel's F7, drawn to read equally well around a null).
- Fig S1-b: unmasking curves.
- Fig S1-c: placebo distance beside the observed distance.
- Fig S2: forest plot of the 11 mediums' own-voice against channeled AUC, with Bashar marked.
- Fig S3: confusion matrix of entity attribution by year, with balanced accuracy.
- Fig SX: Delta MDS map of the voices (EXPLORATORY).

### 5.4 The same question put to different voices (family Q; NET7)

**Q&A pairs.**
- Labelled texts are parsed by rule and recorded as observed pairs. L/L puts labels on their own lines, Cosmic Agency uses inline labels, and Blossom Goodchild's split is approximate.
- In made-here text, R1 finds the pairs after speaker separation, and they are recorded as detected pairs.
- Prompts written by a model are never counted.

**Vectors.**
- Main models: bge-small-en-v1.5 (33M parameters, 512 tokens) or all-MiniLM-L6-v2 (22M, 256 word pieces), run through onnxruntime.
- Long answers are cut into chunks whose vectors are averaged; using only the first chunk is the sensitivity check.
- Baselines: TF-IDF/BM25, and Model2Vec for speed.
- multilingual-e5-small is used only for the German files.

**Measures.**
- *Responsiveness:* R = cos(q_i, a_i) minus the mean cosine of q_i with the other answers in the same session. Subtracting the session mean cancels the session's topic.
- *Question families:*
  - a nearest-neighbour graph over all questions (k = 10), cut at a threshold set on GS6's "same question?" pairs from the discovery half;
  - Leiden communities;
  - each family gets a label written by a researcher, so no question text appears in any output.
- *NET7:* a two-mode network of question families by voice, which carries the convergence measure of Q1.
- *NLI:* labels on at most 5,000 sampled answer pairs, checked against 200 pairs labelled by people.

**Statistics.**
- Mixed models (answer pair within session within voice), or a cluster bootstrap.
- Families by voice: chi-squared with a Monte-Carlo p-value, bias-corrected V and a session-cluster bootstrap.

**Comparisons that matter:**
- channeled against human answers inside one show, with the 2 guests who have both kinds as a within-person check;
- the Ra era against later L/L Research;
- Bashar audiences of the 1980s against the 1990s.

**Q2.** MRQAP, as in 2.3.

**Figures:**
- Fig Q1-a: ridgelines of matched against mismatched answer cosine, one per voice.
- Fig Q1-b: calibration of cosine against human rating.
- Fig Q1-c: heatmap of question families by voice, normalised by row, with n per row.
- NET7: biadjacency heatmap of families by voice.
- Fig Q1-d: forest plot of responsiveness R by voice, era and interview kind.
- Fig Q2: MRQAP coefficient plot with permutation intervals.

### 5.5 Shorts against long videos (Phase 7a; family Y)

**Groups,** as the roadmap defines them and 12.1 counts them. The main corpus is every recording over 5 minutes, with no upper length limit and no cap per channel. Shorts and anything of 5 minutes or less form the short group. Archive.org files and multi-part uploads merge into whole recordings before the 5-minute rule.

**What must be transcribed,** by the laptop lane once the owner settles the YouTube question (D12):
- every short-group item in qualifying channels: at most about 1,200 h, even if every short ran 3 minutes (about 800 h of shorts, 300 h of videos of 5 minutes or less and under 70 h of short streams; 1.6);
- every long video over 5 minutes, with no cap. In the 47 qualifying channels that is 33,307 items and 19,718 h by Draft A's listing count (1.6), all of it part of the main corpus that section 12 transcribes anyway. The earlier caps of 20, 50 or 100 long videos per channel (default 50, D11) are retired.
- Both sides use one engine. Captions serve as a cross-check only (roadmap decision D6).

**Question 1: excerpt, rewording or new?**
- *Stage 1, candidate parents:* the video the short links to, where the lane records it; then title similarity; then audio fingerprints against the channel's long audio, where that audio is held.
- *Stage 2, class:*
  - **excerpt** if most of the short's five-word runs fall together in one candidate's transcript (containment);
  - otherwise **rewording** if its semantic coverage reaches the threshold;
  - otherwise **new**.
- *Recall check:* a pilot on 5 smaller channels searches every long video, to measure how many true parents stage 1 finds.
- *Clip channels* are searched across channels as well (the Bashar list has 11).
- *Reported per channel:* the share of each class, the parent videos, and the lag from long video to short (dates from the lane).

**Question 2: topics.**
- One vocabulary and one topic model are fitted on long videos only, and the shorts are scored with them.
- Shorts are compared with random windows of the same length from the same channel's long videos.
- Shares are counted by words. Weighted log-odds with a prior compare terms, alongside length, pace and the share of questions.

**Question 3: what the shorts leave out.**
- Per channel: the share of long-video words in topics that never reach a short, and the topics that are over-represented in shorts.
- Inside parents with excerpts: which windows were clipped. This is a conditional logistic model with parent fixed effects. Its predictors are position, codes, questions, future statements, names, and hedge density from the frozen list on verbatim text (the measurement the panel's P1 could not make on paraphrases).
- For Bashar, `topic_share.csv` is shown beside this as description only, because those shares are model estimates confounded with batch.

**Statistics.**
- Per-channel differences, combined by random effects.
- Permutation within channel; Benjamini-Hochberg across topics; cluster bootstrap over channels.
- Y1 to Y3 are the confirmatory tests.

**Figures:**
- Fig Y-a: stacked bars per channel of excerpt, rewording and new.
- Fig Y-b: histogram of the lag from long video to short.
- Fig Y-c: slope chart of topic shares from long videos to shorts.
- Fig Y-d: heatmap of channel by topic log ratios.
- Fig Y-e: histogram of where in the parent the excerpted windows sit.
- Fig Y1: forest plot of per-channel log ratios, with the random-effects estimate.
- Fig Y3: the new residual mosaic beside the panel's.
- NET-Y: directed excerpt network from short to parent, per channel.

**Done when** (the roadmap's test): every channel with at least 20 shorts and 20 long videos has its three answers, and a second reader has re-run the numbers from the saved transcripts.

### 5.6 Dated statements, predictions and warnings (Phase 7c; family PR; NET8)

**Marking.**
- R1 marks every statement about the future: what it says, whether it is conditional, its modality, and any date or period.
- Each date is resolved against the recording's own date, so only dated sources can be used: archive.org items, podcasts and dated pages. YouTube rows have no upload dates until the laptop lane supplies them.

**Linking.**
- Statements with the same target period and semantic coverage above the threshold form one claim cluster.
- Repeats across recordings or channels are linked, not counted twice.

**Ledger and rubric.**
- Ledger rows use the panel's columns, now filled from verbatim spans, with hedge counts from the frozen list.
- The 2027 rubric stays unchanged.

**Checks.** On GS3: span F1, and the accuracy of date resolution on 200 statements.

**Statistics.** Counts per channel-year with a recording-cluster bootstrap; the share that is conditional; the mix of certainty. Family PR's statistics are given in 2.3.

**Figures:**
- Fig D-a: one timeline per channel. It lives in the private dashboard, where each point links to its item and time stamp; the public copy shows counts only.
- Fig D-b: combined timeline of claim clusters.
- NET8: two-mode network of claim clusters by channel, shown as a biadjacency heatmap.
- Fig PR-a: target year by first-seen date, per person.
- Fig PR-b: stacked bars of the categories after the deadline.

*Section 12.4 refines the marking, linking and timelines above (statement types, target windows, families, receding deadlines), and 12.7 the dashboard. What the public copy may show beyond counts is decision D16.*

### 5.7 Per-recording summaries

**Data.** Items of 1,500 words or 10 minutes and more:
- most L/L texts (median 3,542 words);
- Cosmic Agency (median 2,118);
- Sam the Illusionist and Blossom Goodchild (about 1,750);
- every made-here recording.

**Method.** R3, as in 4.3.

**Checks:**
- every offset is valid;
- an NLI model checks that each point follows from its evidence, and points scoring under 0.5 are flagged;
- every name in a summary must appear in the text;
- GS5 gives the share of points that are supported, with a recording-level bootstrap; the target is 0.90 or more;
- coverage: the share of the item's three most frequent codes that appear among the points.

**The old digests.** Where a transcript twin exists (4 to 5 now, all 75 through the laptop lane), each digest is compared with what the transcript shows; this is M4.

**Figure:** Fig A1, the share of supported points by source, with intervals.

The summaries themselves stay private.

### 5.8 Question bank

**Data now:**
- L/L Research: 69% of 300 sampled texts are dialogue, and the asking side is 8.4% of words.
- Cosmic Agency: 31% are dialogue, and the human side is 42% of words.
- Blossom Goodchild: her lines are about 1.6% of words.
- 21 live-channeling and 16 conversation interview texts.

**Data later:** the Bashar tapes, where 30% of segments in the two transcribed tapes end in a question mark (a weak proxy), and the podcasts.

**One row per question,** with no cap per recording. Each row holds:
- ids and offsets;
- the asker's role: audience, host, the channel's own team, or the speaker answering their own question;
- Layer A themes on both the question and the answer;
- a flag for personal disclosure;
- the answer's length and modality;
- the frozen-list hedge count in the answer;
- any future statements and names in the answer.

**Clusters.** Each question gets a private normalised paraphrase of at most 25 words, with names removed. The paraphrases are embedded and clustered at a threshold validated on GS6, and a person labels the clusters.

**Checks:**
- unitizing alpha and span F1 on question boundaries (GS3);
- theme alpha on 600 questions (GS4);
- the rule parser's precision on 100 sampled turns.

**Statistics:**
- theme shares by person, decade or tape year, and format, PPI-corrected where a model detected the questions;
- questions per session hour;
- answer length by theme;
- within-voice stability, measured against a recording-level permutation null;
- between-voice differences on clusters that several voices share.

**Figures:**
- Fig A2-a: theme shares by L/L decade and by Bashar tape year, stacked bars with intervals.
- Fig A2-b: questions per session hour, violins.
- Fig A2-c: matrix of question-cluster counts by voice.
- Fig A2-d: answer length by theme, dots with intervals.

**Privacy.** No question text is published, and questions flagged for disclosure are kept out of every example.

### 5.9 Codes, names and dictionaries

**Codes.**
- Share of words per code, by item, person, year and format, corrected with PPI.
- Statistics: differences in shares with a cluster bootstrap; Theil-Sen trends; the modality mix by code.

**Gazetteer v1** draws on:
- the channels-ET registers (52 beings with their aliases, 42 mediums);
- `CANONICAL_IDS` (129 persons, 60 entities);
- the YouTube-index labels (15 canonical, 40 raw);
- the 104-term glossary;
- star systems and places, calendar terms and astrology terms;
- the ways speech-to-text spells entity names.

**Counting names.**
- Ambiguous names (Ra, Abraham, Christ, angels, Federation, Council, Creator) are flagged and need context rules.
- Final counts come from string matching.
- New names found by R1, or by GLiNER on a 2% sample, are adjudicated by a person into version 2, and counting is run again.

**Mention roles.**
- R2 records whether a being is speaking, cited, addressed or described; GS8 checks this.
- Same-name beings are grouped for comparison but never assumed to be the same being.

**Figures:**
- Fig A3-a: heatmap of person by code, per text kind.
- Fig A3-b: code shares by year for L/L, Scranton and the Bashar tapes.
- Fig A3-c: modality mix by code, bars.
- Fig A3-d: mentions per 10,000 words, heatmap of person by entity.
- Fig A3-e: entity timelines for Scranton and L/L.

### 5.10 Topic models

**Documents.** 200-word units, or Q&A turns where they are labelled; never whole sessions.

**Fits:**
- pooled, per text kind, with each person capped at 1,500 units;
- within one source, with year as a covariate: L/L (32,925 units) and Scranton (17,798), using tomotopy's DMR or dynamic topic model on this machine;
- STM with person, year and format covariates, where R is installed;
- BERTopic on unit embeddings: UMAP (n_neighbors 15, 5 components, min_dist 0, cosine) and HDBSCAN (min_cluster_size 10), with a fixed random state and the outlier share reported;
- for Phase 7a, a fit on long videos only.

**Choices.**
- K in {10, 15, 20, 30, 40, 60}, with 5 seeds each.
- Two preprocessing variants: two stop lists, and names masked or not.
- The rule for K is fixed in advance: the smallest K within one standard error of the best held-out likelihood whose median NPMI is at least the grid median.

**Checks:**
- NPMI and C_V coherence, exclusivity and diversity;
- stability: topics matched across seeds by the Hungarian method, reporting the share with cosine of at least 0.8;
- GS7 intrusion tests; topics with intrusion precision below 0.5 are marked incoherent;
- topic labels written by a person from the top words and top units;
- agreement with Layer A codes, measured by normalised mutual information.

**Figures:**
- Fig A4-a: top FREX words per topic.
- Fig A4-b: topic prevalence by year, with intervals.
- Fig A4-c: heatmap of person by topic.
- Fig A4-d: coherence against K.
- Fig A4-e: stability across seeds.
- Fig A4-f: intrusion results.

### 5.11 TF-IDF, keyness and style

**TF-IDF** describes the top terms per person, voice, topic and year. It is counted on the text, never taken from model-written lists, and it is not a test.

**Keyness:**
- *Measure:* weighted log-odds with an informative Dirichlet prior, using the capped pooled corpus of the same text kind as the prior, with the prior's scale fixed in the registration.
- *Effects:* a log-odds difference and a Log Ratio, with intervals from resampling documents, or persons and then documents.
- *Dispersion:* Gries' DP; terms above 0.8 are flagged.
- *Multiple testing:* Benjamini-Hochberg at q = .05 across the vocabulary. The Bonferroni-equivalent absolute z (4.06 for 1,000 terms, 4.56 for 10,000) is drawn as a stricter line. G² appears only as the conventional cross-check.
- *Vocabulary:* unigrams and bigrams found in at least 5 documents, and in at least 3 persons for cross-person contrasts.

**Contrasts:**
- L/L adjacent decades, and the 1980s against the 2010s and 2020s, by labelled entity;
- Scranton 2013-16 against 2023-26;
- each of the six voices against the rest;
- Q&A against monologue within persons;
- live channeling against conversation interviews;
- Bashar sessions against Darryl Anka interviews;
- Bashar E1 against E2;
- the short group against the main corpus (family Y).

**Style:** Delta, ΔCE and unmasking (5.3).

**Figures:**
- Fig A5-a: Fightin' Words scatter (z against log frequency) for each contrast.
- Fig A5-b: the top 20 terms on each side, with intervals.
- Fig A5-c: dispersion against keyness.
- Fig A5-d: rising and falling terms by year (Theil-Sen slopes).
- Fig A5-e: Delta dendrogram of the voices, with bootstrap support.

### 5.12 Embeddings and their overlap across filter groups

**Windows.**
- 150 words for 256-token models (about 93,000 windows in today's source texts) and 300 words for 512-token models.
- The share of windows cut short is logged and kept under 5%.

**Models.**
- Model2Vec for exploration.
- An E5 or BGE-class model for final vectors, chosen on MTEB/MMTEB and on GS6 (the Spearman correlation between cosine and human ratings, against a TF-IDF/BM25 baseline).
- Vectors stay private.

**Measures.** Every comparison stays within one text kind, with names masked, boilerplate removed, and a fixed maximum number of windows per person.
1. **Coverage:** the share of A's windows whose nearest window in B reaches a cosine threshold.
   - The threshold is set on GS6 so that 80% of pairs above it are rated "same idea", and a curve over the threshold is shown as well.
   - Reference sets are subsampled to equal size, 200 times.
2. **Normalised overlap:** the coverage of A by B, divided by the coverage of A by an equal-size half of A held out by recording.
3. **Classifier two-sample test:**
   - a logistic regression on the vectors;
   - folds grouped by recording within one source, or leave-one-person-out across persons;
   - AUC with an interval, against a permutation null at the same level.
4. **Maximum mean discrepancy,** with an RBF kernel and a recording-level permutation test.
5. **Novelty:** the share of windows in year t, or in the last N recordings, that earlier windows of the same source do not cover. The earlier text is held to a fixed size.

**Figures:**
- Fig A6-a: heatmap of normalised overlap between voices, with a dendrogram.
- Fig A6-b: coverage curves against the threshold.
- Fig A6-c: forest plot of two-sample AUC per contrast.
- Fig A6-d: novelty by year for Scranton and L/L.
- NET-A6: network of persons whose edges are the normalised overlaps above the permutation null.
- Fig A6-e: UMAP map (EXPLORATORY, never used for inference).

### 5.13 Repetition within and across channels (NET5)

**Units.** Overlapping five-word runs on normalised text, after speech-to-text loops have been removed.

**Within a channel.**
- *Self-reuse rate:* the share of an item's runs found in the same person's earlier text.
  - Boilerplate and runs common to 10 or more persons are excluded.
  - The earlier text is held to a fixed size (the previous 365 days, or a fixed word count), so that reuse does not rise just because the history grows.
- *Formula inventories:* lexical bundles (four-word runs at 20 or more per million in at least 5 texts). Each person's inventory is compared with those of random persons of similar size.

**Near-duplicates.**
- Exact duplicates by normalised hash.
- MinHash on five-word shingles, 256 permutations in 32 bands of 8 rows (a candidate threshold of about 0.65). Candidates are confirmed by exact Jaccard similarity, or by containment for clips and excerpts.
- Local alignment, in the style of passim, to locate reused passages.
- Chromaprint fingerprints to catch re-uploads before transcription (Atlas item N5).
- Positive controls: the Sam texts that are held twice, and the two editions of the Ra sessions (lawofone.info with 278,601 words, llresearch.org with 289,222).

**NET5: shared wording between persons.**
- *Candidate links:* rare runs that occur in at most 5 texts in the whole corpus but in 2 or more persons.
- *Edges:* weighted by association strength beyond each person's own self-reuse.
- *Backbone:* kept against a document-level permutation null within text kind and era (m = 999), with FDR control.
- *Direction:* given only when both sides are dated, earliest first. This is called precedence, never influence.
- *Phrase adoption:* each person's first dated use of predeclared multiword terms and of distinctive n-grams from the discovery half.

**Statistics.** Distributions of self-reuse; Theil-Sen by year with a block bootstrap by month; detection precision on GS9.

**Figures:**
- Fig A7-a: self-reuse by person, violins per text kind.
- Fig A7-b: self-reuse by year.
- Fig A7-c: boilerplate share per person.
- NET5: backbone of shared rare passages between persons, coloured by family.
- Fig A7-d: timeline arc diagram of reused passages, with dates on the x-axis and one row per person.
- Fig A7-e: matrix of reuse counts between persons.
- Fig A7-f: phrase adoption curves.

Reuse between persons will stay thin until more channelers have text.

### 5.14 Networks

| Network | Nodes | What an edge means | Built from | Size today | Can start |
|---|---|---|---|---|---|
| NET1 Channeler and entity (two-mode) | Persons; names, with families as a coarser layer | Claimed in a register; named in titles; named in text (three layers kept apart) | channels-ET register; titles; texts | Register: 41 mediums by 52 beings, 69 claims. Titles: 64 persons by 21 families, 455 non-zero cells (163 with 10 or more items) | Now (register, titles); text after GS8 |
| NET2 Entity co-mention | Names | Named in the same window (paragraph, turn or 60 s) | Source texts; made-here text later | 19 persons with text | Now, per person |
| NET3 Interview circuit and circulation | Shows and guests; channels and accounts | An interview, typed by kind; a channel carrying someone else's material | Interview types; plan tables; channels-ET inventory; Atlas | 9 shows, 28 guests, 75 pairs, 189 interviews; 38 Bashar host channels; 3,242 account-video links | Now |
| NET4 Cross-references (directed) | Persons; clip and re-upload channels as a separate class | A names B, or B's being | Titles now; texts later | Single-owner beings named on other people's channels: Bashar 752 items on 12 other channels (473 on his own), Law of One 128 on 8, Kryon 17 on 7, Taygetan 4 on 3, Ryokah 2 on 1 | Now (titles) |
| NET5 Reuse of wording | Texts rolled up to persons | A shared passage beyond self-reuse | Source texts | 8,425 texts, 5,233 dated | Now (5.13) |
| NET6 Topic co-occurrence | Topics or dictionary themes | Present together, or correlated, in a chunk | Dictionaries; LDA | 10 dictionaries, 8 Q&A themes, 20 tags without examples | Now (dictionaries) |
| NET7 Questions by voice | Question families; voices | Asked of; answers agree | Q&A pairs | L/L, Cosmic Agency, Blossom Goodchild, 37 interview texts | After GS3 and GS6 (5.4) |
| NET8 Dated claims by channel | Claim clusters; channels | The same claim recurs | Verbatim spans | | After R1 (5.6) |

**What the sizes already say** (Draft B's checks):
- **The register is mostly one-to-one.** 30 of the 38 mediums with a claim have one being, and 43 of the 52 beings have one medium, so projections built from the register alone are nearly empty.
- **The interview circuit is saturated.** Every pair of the 9 shows shares a guest, and the guest projection has 253 of 378 possible edges. Unweighted projections therefore carry no information; only weighted projections tested against a null model are used.
- **One show dominates.** 21 of the 30 live-channeling interviews come from one show, so contrasts by interview kind hold the show fixed.
- **Re-upload speakers need another source.** channels-ET's per-video speaker field holds a single value for all 2,812 videos. Who speaks in a re-upload must come from the Atlas (which names 897 of 925 uploads) or from the identity crosswalk.

**Identity crosswalk** (a gate for NET1, NET3 and NET4):
- It joins the et-channelers person slug, the channels-ET medium id, the Atlas person id, the channel id and `host:<show>`, using the keys reader note 09 recommends.
- Never merge on a fuzzy name; mark clip and re-upload channels; count twins once.
- The owner confirms the 14 name-only matches and the 97 unchecked Kryon twins before they enter a test.
- The crosswalk is frozen and hashed.

**NET1.**
- *Edge weight:* the share of a person's items or windows that name the being. Nodes are names, not beings.
- *Null models:* SDSM, and a curveball null with fixed degrees.
- *Projections:* Newman's 1/(n-1) weights, keeping only edges significant under SDSM at Benjamini-Hochberg q < .05.
- *Statistics:*
  - NODF nestedness (E-H1) and bipartite modularity, against the curveball null (m = 9,999);
  - family assortativity of the person projection, with labels permuted over persons;
  - name centrality (strength, PageRank), with a bootstrap over items within persons.
- *Figures:*
  - NET1-a: biadjacency heatmap of persons by families in NODF order, with each cell the share of items, n on each row label and register claims shown as dots;
  - NET1-b: two-column bipartite drawing of the register;
  - Fig NET1-c: null distribution of NODF with the observed value;
  - NET1-d: backbone of the person projection, coloured by family.

**NET2.**
- *Counting:* each name counts once per window; Q&A sources are split by side.
- *Weights:* association strength and NPMI.
- *Per-person networks come first.* A pooled network is built only from equal samples of windows per person, and an edge is kept only if it is in the backbone in at least 90% of 200 subsamples.
- *Backbone:* a hypergeometric test for each pair at Benjamini-Hochberg q < .05, with Benjamini-Yekutieli as a sensitivity check and at least 5 shared windows; SDSM as a cross-check.
- *Communities:* Leiden at resolutions from 0.5 to 2.0, with 100 seeds and a consensus partition. Modularity is compared with degree-preserving rewiring (z).
- *Resolution limit:* communities with fewer than about √(2L) internal edges can merge (100 at L = 5,000).
- *Centrality:* strength, betweenness, eigenvector and PageRank, with a document bootstrap (2,000 resamples) and robustness to dropout.
- *What it replaces:* the panel's doctrine graph (126 nodes, 635 edges from model-written key terms, with no null model).
- *Figures:*
  - NET2-a: per-person backbone with a fixed-seed layout. Nodes are coloured by family and sized by documents; edge width shows NPMI; only the top 20 nodes are labelled;
  - NET2-b: adjacency matrix ordered by consensus community, for dense backbones;
  - NET2-c: small multiples of one shared name's ego network as each person uses it, on a common layout;
  - NET2-d: difference network between two groups, showing only edges that survive Benjamini-Hochberg, stronger edges in one colour and weaker in another;
  - NET2-e: small multiples by L/L decade.

**NET3.**
- *Build:*
  - a two-mode network of shows by guests, typed by interview kind and weighted by count;
  - Bashar's appearances, joined on `host:<slug>`;
  - a layered circulation graph for Bashar: official channel, then clip and re-upload channels, then interview shows;
  - account-to-practitioner links from the Atlas;
  - possible re-uploads: titles that recur across channels, found by MinHash on title shingles over the 58,699 listing rows and confirmed later by audio fingerprints.
- *Null model:* a bipartite configuration model drawn by curveball. FDSM or SDSM backbones go on the Newman-weighted projections.
- *Statistics:*
  - E-H2;
  - show specialisation against the null;
  - which shows bridge families (betweenness), descriptive only, with leave-one-interview-out stability;
  - the share of a channeler's items carried by accounts that are not theirs, with person-level intervals.
- *Small-sample rule:* with 9 shows and 28 guests, only exact or permutation tests are used, and no single centrality gets a p-value.
- *Interview kinds* from the reader agent must pass GS11 before they enter a test.
- *Figures:*
  - NET3-a: two-column bipartite drawing, edges coloured by interview kind (unclassified in grey), n on each node;
  - NET3-b: alluvial chart from show to guest family to interview kind;
  - NET3-c: biadjacency heatmap;
  - NET3-d: Bashar's layered circulation diagram, with counts on the edges.

**NET4.**
- *Build:* a directed, weighted graph from A to B, where the weight is the share of A's items or windows that name B or B's own being.
  - Self-loops are dropped, and clip and re-upload channels form their own class.
  - A title alone cannot tell a clip channel from a commentator, so the crosswalk sorts channel kinds first.
- *Three edge types,* kept apart: names the channeler; names the channeler's being; reuses the channeler's wording (NET5).
- *Null model:* a directed configuration model that keeps out-strength and in-strength fixed.
- *Statistics:*
  - reciprocity against the null;
  - in-strength centralisation;
  - context persons against channelers in how often they name others, per 1,000 windows, with a person-level permutation;
  - exploratory: in-strength against first public year, with a bootstrap over persons.
- *Mention types:* a small model types a sample of person mentions (quotes, recommends, criticises, channels the same being, mentions), checked under M3. The counts stay string-based.
- *Figures:*
  - NET4-a: directed node-link drawing with curved arrows; nodes coloured by role and sized by in-strength;
  - NET4-b: heatmap of namer by named;
  - Fig NET4-c: in-strength against first year.

**NET6.**
- *Two rulers:*
  - predeclared dictionaries applied by string match;
  - LDA topics fitted per text kind on equal words per person (5.10).
- *Edges:* co-presence above a set share, tested against a hypergeometric null with Benjamini-Hochberg; or positive Spearman correlations of topic proportions that survive Benjamini-Hochberg, with partial correlations as the sensitivity check.
- *What it replaces:* the panel's 19 tag pairs, which were model estimates on digests.
- *Figures:*
  - NET6-a: topic correlation heatmap in hierarchical-clustering order;
  - NET6-b: network of significant positive edges between topics;
  - NET6-c: difference heatmap between groups, with Benjamini-Hochberg marks;
  - NET6-d: small multiples by L/L decade.

### 5.15 Per-year tables and the last N recordings (Phase 7c)

*Superseded on 2026-11-14 by section 12: 12.2 (each channel by year), 12.3 (the last 5, 10, 50 and 100) and 12.7 (the dashboard). They keep this section's measures and figures but change its tests: sparse years merge by a rule fixed in advance; the last N is set against the N just before, with placebo windows in place of 10,000 resampled ones; and a channel needs 2N works, not N. The roadmap's Phase 7c test still decides when the work is done.*

## 6. What extends the Bashar Index panel

| Panel work (commit 457dc2f and earlier) | What the readers found | This plan |
|---|---|---|
| 75 AI digests of auto-captions, one pass each, no transcript kept | Three batch conventions that line up with recording type; the prompt's examples became the top key terms; a later full reading found passages the digests had missed | Records from kept transcripts, with offsets. One pinned model, one recorded run, random batches, control sets, no examples, a priming check (4.4, 4.5) |
| 20-tag topic percentages estimated by the model (summing to as much as 169 before rescaling) | Model guesses | Code shares counted from coded units and corrected with PPI; topic models with human checks; the 20 tags kept as Bashar-only Layer B codes, without examples |
| Key terms from model-written lists; doctrine graph (126 nodes, 635 edges); Kendall's W 0.009; 4 contradiction flags | They inherit the priming: 7 of the top 10 terms and 6 of the 7 example names are among the top 10 | Counts by string match; TF-IDF and weighted log-odds on the text; NET2 and NET6 with null models. W and the flags are not repeated on digests |
| At most 20 questions per recording, tags not stored | 34 of 75 lists at the cap and 8 empty, so 949 is a capped count | An uncapped question bank: one row per question, tags stored, boundaries validated (5.8; B5) |
| P1: hedging on 11-token paraphrases (n 88, p .948) | 72 of 88 claims had no listed phrase; the panel's own first-round rules called this unsafe | The frozen 50-phrase list applied to verbatim claim sentences, with its precision measured (M5; B4; Y2) |
| P2 drift (n 25, slope 0.0) and the 73 flips | One 2021 interview takes part in 32 flips; the word "contact" lumps different milestones together | B3 on independent sessions, with typed milestones. The slip chain is not re-derived |
| P3: topic mix by kind (V 0.212, the one confirmed result) | Cannot be separated from batch (V by batch 0.205) | Not re-run on digests. Y3 re-tests it on transcripts coded in one run, Y1 re-tests the clip pattern, and M4 measures the batch effect |
| P4: disclosure share (34 videos, null) | Built on capped counts | B5 on uncapped verbatim question units, with DSL |
| k-means with k = 5 (silhouette 0.346; k = 6 and 7 scored higher) | The robustness sweep never ran | Clustering is exploratory only, with seed and K grids and specification curves. The sweep on digests is skipped |
| Registered stylometry and speech-to-text audit | Blocked; never ran | Run as registered on real transcripts (S1, M1), with the audit made blind; plus the 11-medium baseline (S2) and the within-channel test (S3) |
| Re-verification of 8 digests | Never ran; "n/a" in every results file; not mentioned in the final report | The transcript-based audit M4. The second-model check runs only as agreement and is logged as a deviation |
| Frozen 2027 rubric, ledger, phrase list, `report.py`, seed 42, n first, badges, banner | Sound | Kept unchanged. `report.py` is generalised: it requires n, unit, text kind, level, snapshot id, prereg id, gate status and the flow row, and it refuses confirmatory output if a confirmation id was read before registration. The rubric is scored once on 2030-01-01 (PR3) |
| The 684-session catalogue | Metadata only; 387 boilerplate descriptions | The sampling frame of family B, with dates from archive.org items, and the source of the split file |
| Design, code and results in one commit; two AI roles | The pre-registration cannot be checked from outside; the review was not independent | External registration with a hash timestamp before data access; separate commits; AI roles disclosed. Agent reviewers are not peer review |

**Kept unchanged:**
- the phrase list, and the rubric with its no-tuning clause;
- the ledger format;
- `report.py`'s refusals;
- the seed registry;
- the working rules: n first, grades and badges, corrections left visible, nulls given the same prominence as hits, and the banner.

**Not repeated:**
- P1 to P4, Kendall's W and the contradiction flags on the digests;
- the slip chain;
- new digests made by a single model pass with no transcript kept;
- the cluster sweep on digests.

**Corrections to post on the Index before any paper cites it:**
1. the batch confound behind P3 and behind the site's "four packagings" chart;
2. the prompt priming: 7 of the top 10 key terms, 6 of the 7 example names, the example years 2027, 2033 and 2050 among the most mentioned, and a fixed tag named `et_contact_disclosure_2027`;
3. the 20-question cap behind "949 questions";
4. the model-guessed word counts behind "1.19M words" and behind the 141-hour estimate;
5. clip 9Ij2AEoRwoM's impossible "reliable" year of 2027;
6. the re-verification that never ran;
7. links to the panel's report, ledger and rubric.

Also fix the year table's raw JSON strings, and the README's claim that the page makes no external requests (it loads Google Fonts).

**On the site.** A new "Verbatim studies" section shows each family's results with n first, badges, nulls shown as prominently as hits, and the banner. It contains numbers only and links to the registration.

## 7. Compute

| Task | Present 2-core machine (one physical core, 8 GB; paused) | 4-core, 16 GB Codespace (next) | GPU | API (Batches) | Owner's computer |
|---|---|---|---|---|---|
| Frames, split files, flow diagrams, power simulations, gold sampling sheets | Yes, in minutes | Yes | | | |
| Metadata networks and null models (NET1 register and titles, NET3, NET4 titles; curveball with m = 9,999 on a 64 x 21 matrix) | Yes, seconds to minutes | Yes | | | |
| Units, flags, boilerplate; gazetteer and hedge counts; five-word runs; MinHash over 13.3 M source words | After the freeze, minutes to tens of minutes at nice 19 | Yes | | | |
| TF-IDF, keyness, Delta, KenLM | Yes, after the freeze | Yes | | | |
| LDA, DMR and dynamic topic models (tomotopy) on capped samples | Overnight at nice 19 | Yes, faster grids | | | |
| STM (needs R) | No | Yes, with R installed | | | |
| Embeddings | Model2Vec in minutes; MiniLM on the source texts about 5 h, on the whole main corpus about 2 days (4.6) | MiniLM in hours; UMAP and HDBSCAN up to about 100k windows | E5/BGE class in minutes | | |
| Reading passes R1-R3 | At most a 20-unit smoke test | | 7-9B open weights: about 145 GPU-hours for the source texts and the main corpus; the 20% replication | Haiku 5.5: about $150 to $300 (4.6, 12.5); the 10% Sonnet 5.5 audit, about $270 | |
| NLI checks | Samples up to about 5,000 pairs | Yes | Beyond that | | |
| Speech-to-text | base.en at 1.3x (under load) to 5.9x (idle) real time | About twice that (to measure); Parakeet TDT 0.6b v3 int8: measured slower than base.en on 2 threads (3.2x against 9.2x real time; pipeline/README); to measure again | large-v3 for the confirmatory strata (about 1,000 h; 1 to 2 GPU-days, estimate); the 2,870 h backlog in about 62 GPU-hours; YouTube's audio in about 500 (12.10, step 0) | | YouTube lane, transcribed with the same engine, once D12 is settled |
| Speaker separation (pyannote) | No | Slow (to measure) | Yes | | |
| GPT-2-small fine-tune for ΔCE | No | Slow | Yes | | |
| Chromaprint fingerprints of all audio | Slowly | Yes | | | For YouTube audio |
| Audio stream-extraction from the 146 video-only sessions (300 h; about 529 GB transferred; only Opus stored) | No | Yes, one file at a time, E4 first, within archive.org's rate rules | | | |
| YouTube audio, captions and upload dates (Phase 7a; the 75; official sessions 2021-2026) | Refused from the cloud. Listings and upload dates could come from the YouTube Data API, which works from the cloud with the owner's own key (D12) | Refused, as before | | | Yes (`run_all.py`), once D12 is settled |

**Software.**
- *Analysis environment:* a separate environment built from a lockfile, containing numpy, scipy, pandas, statsmodels, scikit-learn, matplotlib, networkx, python-igraph, leidenalg, krippendorff, datasketch, tomotopy, model2vec or fastembed, umap-learn, hdbscan, jiwer, kenlm and the `anthropic` SDK. Use Python 3.12 if wheels for 3.14 are missing.
- *R,* with stm and backbone, on the 4-core machine.
- *vLLM or llama.cpp* on the GPU machine.
- *Untested so far:* GPU runs, Windows, large models and long batches.

**Rules.**
- Nothing heavy runs while collection needs the CPU. Jobs run at nice 19 with checkpoints.
- Every script calls `ensure_outside_git`.
- Private intermediates (units, offsets, embeddings, model outputs) live under the private root's own `analysis/` folder, outside Git, and sync to the private store.
- `guard_no_raw_media.py` runs before every commit, and the et-reviewer's four risks are checked before each merge.
- Public outputs are numbers only.

## 8. Phases

**Two freezes.**
- **S1** freezes the inputs of families B, S and Q: the Bashar frame audio and the interviews.
- **S2** freezes the cross-channel corpus once collection is done.

**Order relative to collection.** Phases 0 to 2 prepare and measure. They decide how collection transcribes and what is registered, and they produce no content findings. Content results wait for the freezes, as the owner asked (decision D10). Section 12.10 orders the Phase 7c work inside these phases; its first dashboard shows metadata and counts until freeze S2.

| Phase | When | Work | Deliverables | How it is checked |
|---|---|---|---|---|
| 0. Preparation | Now to 2026-11-28; light CPU; no transcript opened for analysis | See the list below the table | Code and tests; codebook, gazetteer and dictionary files; draft registrations | Tests pass on synthetic text; the et-reviewer's "wrong numbers" pass; the owner's decisions recorded |
| 1. Measurement and discovery | To about 2026-12-20; 4-core machine, GPU if available | See the list below the table | Measurement memo (variances, within-recording correlation, final N, margins, power by simulation with the cluster structure); frozen codebook v2, dictionaries, prompts and model choice | A second reader re-runs the memo's numbers; human-to-human alpha is known for every code |
| 2. Registration | By 2026-12-31 (PR before 2027-01-01) | Embargoed OSF registration; hash timestamp; signed tag; split files and dictionaries attached; prior exposure listed | Registration id | The timestamp can be checked from outside; `report.py` refuses confirmatory runs without it |
| 3. Freeze S1 and confirmation transcription | January 2027, or when a GPU is available | S1 manifest with hashes of every input; pinned engine on confirmation items, own voice and baseline interviews; flags; speaker separation; blind audit of the confirmation strata | S1 manifest; QA report; gate log | Gates decided and logged before any outcome is computed |
| 4. Coding and gold | January to February 2027 | One run of R1-R3 through Batches; 10% audit; 20% open-weight replication of the test labels; gold test half scored once | Coded data (private); validation report; model and LLM setup cards; run records | Every code has a verdict (keep, exploratory only, drop); repeat-run agreement reported |
| 5. Confirmatory run | One day, February 2027 | Families B, S and Q through `report.py`; a second runner | Results tables and figures, nulls included; deviations table | Byte-identical JSON from the second runner, or a documented difference |
| 6. Exploratory work and Phase 7c datasets | From S2; CPU and API | X1-X10; per-year tables, last N, timelines and question banks by section 12; summaries | Badged exploratory report; dashboard sections (numbers only); methods note | The roadmap's 7c test; a second reader re-runs the numbers |
| 7. Laptop lane | Whenever the owner can run it | See the list below the table | M4; Y1-Y3; Y-E; extension of S1 | The roadmap's 7a test; a second reader re-runs the numbers |
| 8. Write-up and release gate | March to April 2027 | Paper, data paper, documentation; corrections on the Index; rights check | Drafts; public numbers and code; the Index's new section | `guard_no_raw_media.py` clean; Atlas checklist N8; owner sign-off |
| 9. Prospective | 2027-01-01 to 2030-01-01 | Collection cycles continue; PR evaluated once after 2028-01-31; rubric scored on 2030-01-01 | Prospective addendum (2028) and rubric score (2030) | No interim looks; the access log shows none |

**Phase 0 work:**
- the analysis environment's lockfile;
- snapshot manifest S0 and the split files;
- codebook, gazetteer and dictionaries v1;
- schemas and prompts, with no examples;
- the unit segmenter and quality flags;
- the generalised `report.py`, the loader seal and the access log;
- the blind QA sheet;
- new manifest fields for the decoding settings;
- the identity crosswalk;
- sampling frames for the gold sets;
- a check of 100 of Scranton's title labels;
- draft registrations for B, S, Q and PR, with Y as conditional;
- the priority list for transcription.

**Phase 1 work:**
- transcribe the 24 paired items and the 102 discovery items;
- an M1 pilot of 6 files x 3 windows per stratum, and the engine benchmark;
- pilots of speaker separation and of phrase precision;
- the 6+6 stylometry pilot;
- the GS1 development half, with its reliability check;
- the bake-off;
- the registered exploratory metadata networks may also run in this phase.

**Phase 7 work:**
- the 75 recordings;
- shorts and long videos of channels with at least 20 of each: every long video over 5 minutes, with no cap per channel (12.1);
- YouTube audio and captions only once the owner has settled D12;
- official sessions from 2021 to 2026;
- family Y registered as an amendment before any of these data are opened.

## 9. The paper

### 9.1 Main paper

**Working title:** *A channeled persona across four decades: pre-registered tests on verbatim transcripts of the Bashar sessions, 1984-2025.*

**Abstract:** n first; every confirmatory result, nulls included; the banner.

**Sections:**
1. **Introduction.** Channeling as a performed genre (Hanegraaff 1996; Brown 1997; Klimo 1998; Hastings 1991); the claims tested, and why verbatim and pre-registered; contributions.
2. **Prior work.** The Bashar Index and its panel, with the limits found here; persona and authorship studies (Burrows 2002; Evert et al. 2017; unmasking); coding with language models and how it is validated (Gilardi et al. 2023; Törnberg 2024; Egami et al. 2023; Angelopoulos et al. 2023; Baumann et al. 2025); speech-to-text in research (Radford et al. 2023; Koenecke et al. 2024).
3. **Data.** The frame, collection lanes and text kinds; the flow diagram; short versions of the data statement and of the rights and ethics sections.
4. **Measurement.** M1 to M6, which decide what can be tested.
5. **Design.** The hypotheses, the split and the seal, the statistics, the deviations.
6. **Confirmatory results.** One table (family, test, n, unit, estimate, interval, p, Holm p, verdict), then a subsection per test with the equivalence plots.
7. **Stylometry,** with the 11-medium baseline.
8. **Exploratory results,** badged.
9. **The digest layer revisited,** if M4 ran: which Index figures survive.
10. **Discussion:** genre discipline, not truth.
11. **Limitations.**
12. **Ethics, rights and AI use:** what is released and what is not, and why.

**Figures:**
1. the flow diagram;
2. WER by stratum (Fig M1-a);
3. the reliability forest plot (Fig M3-a);
4. B1 equivalence (Fig B1-a);
5. B2 contact share against year (Fig B2-a);
6. B3 target year against session date (Fig B3-a);
7. B4 conditionality by bin (Fig B4);
8. B5 shares by era (Fig B5-a);
9. S1 ΔCE (Fig S1-a);
10. the S2 baseline (Fig S2).

**Appendices:**
- the registration and the deviations;
- codebooks and prompts, verbatim;
- the model and LLM setup cards;
- the datasheet, data statement, ARR checklist and HEDS sheet;
- the power memo;
- the S1 manifest and the environment.

### 9.2 Other outputs

- **Companion data paper:** *A provenance-separated catalogue of channeled material from 70 people.* It covers:
  - the catalogue's design: lanes, ids, twins and text kinds;
  - coverage and gaps: the YouTube refusal, undated rows, concentration in three sources;
  - the quality checks;
  - what is released: metadata, hashes, counts and derived features;
  - a datasheet and Croissant metadata.

  Check the current author instructions of the target data journal or resource track (Atlas item N8).
- **Prospective addendum,** in 2028 and 2030: family PR's results and the rubric score.
- **Methods notes for the dashboard:** Phase 7a and Phase 7c, numbers only.

### 9.3 Standards and checklists

- **Reporting checklist.** The ACL Rolling Review Responsible NLP Research checklist, with the required Limitations section. It covers:
  - artifacts, licences and intended use;
  - personal data;
  - compute budget;
  - annotators' instructions, pay and consent, and ethics review;
  - use of AI assistants.
- **Pre-registration.** The OSF template for secondary data (van den Akker et al. 2021), with a split-sample design (Egami et al. 2022) and qualitative pre-registration where it fits.
- **For every study:** a CONSORT-style flow (frame, eligible, acquired, transcribed with the engine named, passed the error gate, has at least 2,000 Bashar-voice words, analysed), counted by era or person with a reason for every loss, plus a deviations table. `report.py` rejects a results table without a flow row.
- **Statistics.** Effect sizes and intervals for everything (Wasserstein and Lazar 2016; Cumming 2014; Lakens 2013); Holm 1979; Benjamini-Hochberg 1995; Benjamini-Yekutieli 2001; Phipson and Smyth 2010 for permutation p-values; specification curves (Steegen et al. 2016; Simonsohn et al. 2020).
- **Human evaluation:** HEDS (Shimorina and Belz 2022), covering coders, training, blinding, pay and agreement.
- **Metadata:** FAIR principles for every release.

### 9.4 Data documentation

- **Data statement** (Bender and Friedman 2018, version 2 guide 2021). It covers:
  - the curation rationale;
  - language variety: English, plus one German person;
  - speakers: channelers are public figures, and audience members are unknown;
  - speech situations: live sessions, workshops, interviews and written messages;
  - recording quality: cassette transfers from 1984-99 against podcasts from 2025-26;
  - provenance: lane and dates.
- **Other documents:**
  - a datasheet (Gebru et al. 2021);
  - a Data Card or Croissant metadata for released metadata;
  - model cards for any trained classifier;
  - an LLM setup card: model id, prompts, dates, thinking and effort settings, and the run records.
- **Storage layout,** documented in the data paper and in each read-me:
  - the private GitHub store, release `archive-v1`, with the text mirror under `texts/<person>/from-source` and `made-here`;
  - the analysis snapshots as private releases (`analysis-s1`, `analysis-s2`), mirrored to the unshared Drive folder "ET Channelers Archive";
  - in that folder, audio is organised by person and source, and texts are volumes per person, with source texts and made-here texts never in one file.
- **Public outputs:**
  - `media_manifest_public.csv`-style tables of durations, sizes, hashes, counts, model and revision;
  - split files of public ids;
  - run records, codebooks, prompts and code.

## 10. Risks, ethics and copyright

### 10.1 Risks

| Risk | Effect | What the plan does |
|---|---|---|
| Three sources hold 88.5% of source words | Pooled numbers describe L/L, Scranton and Cosmic Agency | Per-person caps and weights; within-source designs; at least 3 persons per side, and 10 for generalising |
| One to three persons per group | No valid group p-value | Persons as units; descriptive or within-person designs; the number of possible relabellings stated |
| Publisher text against speech-to-text | Differences caused by text kind read as findings | Never pooled; M6 calibration; differences below the calibration shift not reported |
| Old tapes fail the error gates (base.en scored 0.729 on a 1981 tape) | B and S lose the 1980s; missing words bias counts | Engine benchmark; VAD tuned on discovery; gates per stratum; descriptive fallback; high-confidence spans used only as a sensitivity check, with their bias shown; large-v3 on a GPU |
| Era moves with audio quality | Spurious change over time | Audio-quality covariates; the degradation placebo; equivalence tested on the better half of sessions |
| Speech-to-text loops, invented text in silence, misheard names | Inflated repetition; missing or false network nodes | Whisper's flags; loop removal; silent-window checks; the variant map; the publisher text for Ra |
| Audience microphones defeat speaker separation | B5 cannot run | DER gate; whole-session fallback |
| Small-model failure modes: one label for everything, option-order effects, priming, refusals | Systematic mislabelling | A Haiku-class or 7-9B coder; order-reversal and priming checks; evidence spans; refusals counted; a human test half |
| Batch or version drift (the digests' three batches) | Groups confounded with the run that coded them | Random batch assignment; control sets; one model version; a full re-run on any change |
| No temperature control | Labels vary between runs | 5% re-run, agreement reported per code |
| Gold sample too small for rare codes or small groups | Wide intervals | Oversampling with known weights; PPI per group; rare codes exploratory only |
| Only one human coder | No human-to-human reliability | Recruit a second coder; otherwise intra-coder reliability and no firm claims |
| Data seen before registration | Weaker confirmatory claims | Hash split today; the seal; the access log; disclosure; the registered-exploratory label for metadata tests |
| Forking paths; many contrasts; a large vocabulary | False discoveries | Small Holm families; Benjamini-Hochberg and Benjamini-Yekutieli; effect sizes; split-sample confirmation; specification curves |
| Unstable topics and communities; dense projections; the resolution limit | Artefacts read as structure | Seed and K grids; intrusion checks; backbones; consensus partitions; null models; resolution stated |
| Network size follows sample size | False group differences | Rarefaction to matched samples |
| Over-reading edges (co-mention read as doctrine, precedence as influence, shared vocabulary as contact when common sources such as the Law of One explain it) | Over-claiming | The banner; the meaning of an edge in every caption; MRQAP controls; the word "precedence" |
| Identity errors (clips, re-uploads, name-only matches, the 97 unchecked Kryon twins, over-counted accounts) | Wrong nodes; double counts | The crosswalk; twins counted once; fingerprints; the owner confirms name-only matches |
| Too few era-matched sessions and own-voice recordings | S1 "not determined" | Extract the 2024-25 sessions; the laptop lane; the own-voice exception (D3); intervals reported, never zeros |
| Video-only sessions are not extracted | Family B limited to 1984-1999 | Stream-extract one file at a time, E4 first |
| The laptop lane never runs | M4, family Y and Phase 7a are missing | Said plainly; Y stays registered as conditional |
| Shorts have no dates or lengths; the parent search misses parents | Phase 7a late; excerpts counted as new | Metadata parts first; stage-1 recall measured on the 5-channel pilot |
| The API model changes or is retired | Labels cannot be reproduced | Raw outputs kept privately; open-weight replication; human gold |
| Counts keep moving; the machine move changes the environment | Inconsistent numbers | Snapshots S0, S1 and S2 cited by every number; the lockfile; a second runner |
| The hold on untranscribed Bashar audio fills the disk (handoff section 7) | Collection stops | Keep only a window of sessions ahead of the transcriber, and pull the rest back later |
| CPU contention with collection | Slower collection | Nothing heavy before the freeze; nice 19 |

### 10.2 Ethics

- **Callers' personal data.** Callers disclose health, family and beliefs. These are special categories under GDPR Article 9, which calls for Article 89 safeguards.
  - Question units are pseudonymised: no names, places or ages.
  - Identifying details are never quoted, and data at the level of single questions are published only as counts.
  - Rows flagged for disclosure stay out of examples, and go to the local route if the owner chooses it.
- **"Public" is not consent.** AoIR Internet Research Ethics 3.0 (franzke et al. 2020) and Zimmer 2010 apply.
- **Ethics review.** An ethics determination is needed if an institution or paid annotators are involved; instructions, pay and consent are documented (HEDS, ARR checklist).
- **Stance.**
  - The writing keeps methodological agnosticism (Smart 1973; Porpora 2006).
  - No sentence asserts or denies where the material comes from.
  - Evaluative labels such as the panel's "self-sealing prophecy" appear only as the names of tested hypotheses, and claims are reported as claims.
- **AI use is disclosed:** coding, agents and drafting. The 2026 panel was two AI roles, and agent reviewers are not peer review.
- **Takedown.** Every release README carries a takedown route.

### 10.3 Copyright and provenance

- **Who holds the rights.** The recordings and texts belong to their makers; the Bashar sessions belong to Darryl Anka and Bashar Communications, Inc. Channeled material is protected as human authorship, whatever source it claims (Urantia Foundation v. Maaherra, 9th Cir. 1997; Copyright Office Compendium § 313.2; Thaler v. Perlmutter, D.C. Cir. 2025).
- **Copies made for analysis** rely on non-consumptive research use.
  - *United States:* fair use (Authors Guild v. HathiTrust 2014; Authors Guild v. Google 2015), narrowed by Warhol v. Goldsmith (2023). The 2025 rulings in Bartz v. Anthropic and Kadrey v. Meta, and the Copyright Office's 2025 report, turn on how copies were obtained and on market harm. So acquisition stays clean: public archive.org items and the makers' own feeds and sites, and nothing that gets around a block.
  - *EU:* the DSM Directive, Article 3 (research organisations with lawful access) and Article 4 (a general exception that rights holders can opt out of).
  - *UK:* CDPA s29A (computational analysis) and s30(1ZA) (quotation).
- **What may be published:**
  - metadata, hashes, counts and derived non-consumptive features, following HathiTrust's extracted-features model;
  - quotes of 30 words or fewer, with attribution, item id and time stamp.

  Never published: audio, full text, embeddings (which can be inverted; Morris et al. 2023), or indexes of third-party text.
- **Storage.**
  - The private GitHub store, plus the Drive copy, which stays unshared; its permissions are checked after each upload batch.
  - bashar-index is public (GitHub Pages) and never holds media or text.
- **Provenance and open items:**
  - **Kimi snapshot.** Its YouTube audio and subtitles came through converter and paste-link sites. That material is not taken, not even privately (ROADMAP phase 4b, HANDOFF 6.2); its figures may be cited only labelled by route (D8). The method is never repeated.
  - **ArchiveShelf** is public and carries third-party audio and transcripts. It should be made private again (handoff decision 4).
  - **A full-access token file** sits in the working tree. It is ignored by Git and was never committed, but it should be revoked and replaced by a fine-grained token (handoff decision 3).
- **References.** They come from the methods reader's memory, because no web search ran. Verify the 2024-2026 items and the current ARR checklist before citing. Nothing here is legal advice.

## 11. Decisions for the owner

| # | Decision | Default if nobody decides |
|---|---|---|
| D1 | A GPU, and where: the owner's laptop or a cloud GPU | If none is available by the registered date, confirmation uses the best CPU engine from the benchmark, and the gates decide what can be tested |
| D2 | The speech-to-text engine: Parakeet TDT 0.6B on CPU (measured slower than base.en on the 2-thread machine, 3.2x against 9.2x real time: to measure again on 4 cores), or large-v3 on a GPU; and a multilingual model for the about 2,050 main works (1,310 h) not in English (12.10, step 0) | Decided by the M1 benchmark on discovery windows, before everything is transcribed; language detected per recording, and each language analysed on its own |
| D3 | An exception to the interview rule for Darryl Anka's own-voice conversations, for stylometry only | No exception; S1 stays underpowered and is reported as such |
| D4 | The bulk coder: Haiku 5.5 through Batches (about $150 to $300 for the source texts and the main corpus, 4.6; texts go to the provider, as they already did with the reader agents) or a pinned 7-9B open model on a GPU (about 145 GPU-hours; nothing leaves the owner's machines) | The bake-off decides on quality, then cost; units with personal disclosures go local |
| D5 | A second human coder, pay, and an ethics determination; for section 12, three coders (100 to 200 person-hours), their pay and blinding | The owner alone, with intra-coder reliability stated as a limitation; section 12's model labels are then reported as agreement with Opus |
| D6 | Registration route and embargo; family PR filed before 2027-01-01 | Embargoed OSF, plus a hash timestamp and a signed tag |
| D7 | Sealing: transcribe confirmation items before registration under the loader seal, or hold them back | Transcribe under the seal |
| D8 | The Kimi snapshot's YouTube material | Not taken, not even privately; figures cited only labelled by route |
| D9 | Stream-extract the audio of the 146 video-only sessions | Yes, one file at a time, E4 first |
| D10 | Light discovery work during collection (codebook development, pilots) | Allowed only when it does not compete with collection for the CPU; no content results before the freeze |
| D11 | Phase 7a: whether to fingerprint all long audio. The cap on long videos per channel was retired on 2026-11-14: every recording over 5 minutes is analysed, with no upper length limit and no cap per channel (12.1) | Fingerprints where the audio is held |
| D12 | YouTube: a written, scoped exception to "robots.txt obeyed" for the YouTube lane, or listings and dates through the YouTube Data API (about 2,400 of 10,000 daily units, refreshed monthly; 12.1, 12.10) | Lanes off; the listings already made are kept, labelled by route and not refreshed (roadmap D8, HANDOFF 6.6). The Data API needs the owner's own key and is not built |
| D13 | Machines and storage for the whole main corpus: about 3 weeks of cloud CPU for the about 3,100 h off YouTube, about 500 GPU-hours for YouTube's audio (not measured), and about 250 GB of private storage, against 10 GB free | None given for storage. Until it is sized, audio is kept only in a window ahead of the transcriber (10.1) |
| D14 | The account's data terms, which decide what sending text to the API means for privacy (12.5) | No batch is sent until they are checked |
| D15 | Deletion tracking: first-seen and last-seen dates per id, seeded from earlier inventories, because 6 of the Index's 75 recordings have left YouTube | On, from step 1 of 12.10 |
| D16 | What the public dashboard shows: counts only (5.6), or also time stamps, links to the publisher's copy and checked quotes within the limits of 12.9, with a quote cap per channel still to set; and whether prediction hit rates appear per channel | Counts only until decided; hit rates only in aggregate |

## 12. Timelines, predictions and question banks (deep research, 2026-11-14)

*Written on 2026-11-14 from five agent surveys and that day's private catalogue, then revised after an adversarial review that recounted the catalogue. The review, cleaned up, is in [notes/2026-11-14/research_critique.md](notes/2026-11-14/research_critique.md). AI-written; not yet reviewed by a person. Counts are works, not catalogue rows, by the rule under "Units" in 12.1. The main ones (works, hours, the dated share, who qualifies for the last-N tests) were rechecked against the catalogue (73,921 rows) at about 07:40 UTC that day. Corrected after the critique, which asked for one pinned works script: that script is not in the repository yet, and step 1 of 12.10 adds it.*

*This section replaces roadmap decision D4, decision D11 and section 5.15 of this plan, and the caps per channel in 4.6 and 5.5. Section 4.5 governs every model pass.*

### 12.1 Corpus groups

- **Main corpus: every recording over 5 minutes, with no upper limit,** all downloaded and analysed at the owner's request: 45,515 works, 23,200 hours of known length, and 7,647 works of unknown length. A one-hour cap would lose 49% of the hours; 299 works run over 3 hours (1,300 hours), 179 of them Bashar sessions. Long recordings are to be cut into windows, never dropped. Corrected after the critique: the code does not do this yet. Downloads time out after 3,600 seconds on YouTube and 1,800 on files, the cycle budget skips items that would overflow it, and transcription decodes each file whole; step 1 of 12.10 lifts these limits.
- **YouTube holds about 21,000 of these hours.** yt-dlp reads `/youtubei/`, which YouTube's [robots.txt](https://www.youtube.com/robots.txt) disallows. So its audio, captions, listings and dates, the listings used here included, break the rule "robots.txt obeyed". Step 0 of 12.10 settles this (D12).
- **Short group:** 16,115 shorts and 6,743 other works of 5 minutes or less. It meets the main corpus only through the Phase 7a method (5.5), whose distinctive-word measure follows [Monroe et al. 2008](https://doi.org/10.1093/pan/mpn018).
- **Units:** a video, its podcast episode and its page are one work only through a verified twin (12.2), which also lends a text its length. Archive.org files (903 files, 245 Bashar sessions) and multi-part uploads merge before the 5-minute rule, which applies to the whole recording. Source texts and speech-to-text made here are never pooled. Interviews count only with live channeling, and only the entity's turns.

### 12.2 Each channel by year

Each work gets two dates, said and published, each with its source and precision in [EDTF](https://www.loc.gov/standards/datetime/), a format for uncertain dates. Sources, best first:
1. the publisher or archive.org item;
2. a date in the address (L/L's `/channeling/YYYY/MMDD`);
3. a full date in the title, checked per channel, never a bare year, which may be a target;
4. a verified twin;
5. YouTube's upload date from the Data API;
6. failing these, the interval between the nearest dated items of the same tab.

No year is guessed from content.

A twin counts only if it is one-to-one and its title and date agree; 675 Scranton videos each link to 2 to 4 posts, often years apart. Corrected after the critique: the listings give no upload dates (0 of 58,699 rows). So for a video with no full date in its title, a text-overlap check after transcription stands in for the date check until the Data API supplies one. 16% of main works are dated now (7,394 of 45,515), about a quarter once addresses and titles are parsed. Works with only a list position enter last-N views, not yearly ones.

One row per person, year, corpus group and text kind: works, hours, words, median length, uploads per month, format mix, and per-recording means of text features. The features are those the old 5.15 listed: Layer A code shares, type-token ratio on fixed-size samples, the share of audience questions, and named beings, star systems and places. Because sampling is uneven:
- years with under 20 works are flagged, not tested, and merge into periods of 20 or more by a rule fixed in advance;
- each year is also shown at the person's lifetime format mix;
- partly transcribed years use Hájek means: inverse-probability weights ([Horvitz and Thompson 1952](https://doi.org/10.1080/01621459.1952.10483446)) normalised to sum to one. The inclusion probabilities come from the seeded transcription order (12.10, step 4), adjusted for failed downloads, failed transcripts and deleted videos;
- trends are smooth curves (GAMs). A change is named only where the slope's simultaneous interval excludes zero ([Simpson 2018](https://doi.org/10.3389/fevo.2018.00149)). 2026 is partial.

### 12.3 The last 5, 10, 50 and 100 against the whole history

Order each person's main works by date; undated works only within one YouTube tab. The measures are those the old 5.15 listed: topics; novelty of wording (as in 5.12, plus five-word runs never seen before); length and pace; the rate of predictions and warnings.

The headline compares the last N with the N just before, or with the GAM's forecast. "Against all earlier works" is description only, as steady drift alone inflates its false alarms (up to 13% in simulation). Report both values, their difference, an effect size with its interval, and the window's dates and format mix. Corrected after the critique: at N = 5 and 10 an interval says little, so there the value and its placebo percentile stand alone.

- **Too few:** under 2N works gives "not enough recordings". At N = 100, 42 people qualify from listings, 6 with text.
- **Effect sizes:** Hedges' g, or Cliff's delta when skewed ([Cliff 1993](https://doi.org/10.1037/0033-2909.114.3.494)); block-bootstrap intervals ([Politis and Romano 1994](https://doi.org/10.1080/01621459.1994.10476870)) only at N = 50 and 100.
- **Placebo windows:** the same contrast for every earlier non-overlapping run of N; the latest window's percentile is the headline. A p-value below 0.05 needs 20 placebo runs, so 22N works: at N = 100, three people from listings, and only Scranton with text.
- **Calendar:** windows holding recurring dates (11/11, solstices, equinoxes, eclipses) are flagged and compared with the same weeks in earlier years.
- **Power:** simulated per channel. Against the N just before, 80% power needs about 1.77, 1.25, 0.56 and 0.40 standard deviations at N = 5, 10, 50 and 100, more when neighbours resemble each other.
- **Multiplicity:** the primary tests (Holm) pool the latest-window effect across people, for 3 to 5 preregistered features. Per-person results use Benjamini-Hochberg ([1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)) across people within each feature and N.

### 12.4 Predictions and warnings

**Definitions.** One unit is one statement about the future, by one speaker, about one event.
- Types: prediction; conditional prediction; warning (a harm, with advice); prophecy (harvest, ascension, the shift); "timeline" as a schedule, not a parallel reality; self-validation; refusal to give a date. Future-tense teaching is not a prediction.
- Each unit gets a speaker role, certainty ([FactBank](https://doi.org/10.1007/s10579-009-9089-9) levels), domain, specificity (0 to 5) and checkability.
- The sources' frames ("probable realities") are coded, not judged; a questioner's guess is not the entity's claim.

**Extraction.** Rules flag future words, dates and warnings, to audit the model. Haiku's structure pass (R1, 4.2) marks future statements; a second, shifted read of the source texts and a sample measures what one read misses. Sonnet checks every candidate in the source texts ($30 to $65) and, elsewhere, a stratified sample plus low-confidence cases. All of the about 600,000 candidates expected (about one per 300 words) would cost $900 to $1,800.

**Dates.** Code turns each time expression into a target window counted from the date said ([TimeML](https://timeml.github.io/site/index.html)). Rules ([HeidelTime](https://doi.org/10.1007/s10579-012-9179-y), which needs Java and TreeTagger) and a model propose; Sonnet settles. "Soon" gets no invented bounds; "by 2030" keeps one bound.

**Repeats.** Copies collapse first, by shared five-word runs ([Broder 1997](https://doi.org/10.1109/SEQUEN.1997.666900)). Statements form families, one event per channel (Bashar's "open contact begins"), each distinct target window a version, with Sonnet on borderline pairs. For the combined timeline, families join cross-channel event classes (5.6). Rates count statements, each family once per recording; accuracy counts families.

**Timelines.**
- Per channel: date said across, target window as a bar, families labelled or faceted, undated statements apart. Each point links to its recording and time stamp, and shows if it is still public.
- A Theil-Sen slope ([Sen 1968](https://doi.org/10.1080/01621459.1968.10480934)), with one point per family version and a bootstrap by family, is tested against 1, as in family B3, since a fixed lead time recedes by construction. The lead time itself is analysed too.
- Channels weigh equally in the combined timeline.
- Known dated predictions with a held source recording must be found, as a smoke test only, since the [earlier ledger](../analysis/README.md) came from AI digests primed by their prompts. [Baroni 2012](https://www.cesnur.org/2012/el-baroni.htm) is a pointer only, at its author's request.

**Checking, later.** Only checkable families whose window has passed.
- Criteria are frozen first, and two coders rule hit, partial, miss or not resolvable.
- Probability words get numbers ([Kent 1964](https://www.cia.gov/resources/csi/static/Words-of-Estimative-Probability.pdf)) and proper scores ([Gneiting and Raftery 2007](https://doi.org/10.1198/016214506000001437)), beside a base rate and the share not scorable.
- Open windows, such as Bashar's 2027, enter family PR's registry before 2027-01-01.
- Responses after a date passes are coded: re-dating, spiritualising, "the probable reality shifted", blame, denial, silence, deletion ([Tumminia 1998](https://doi.org/10.2307/3712078); [Dawson 1999](https://doi.org/10.1525/nr.1999.3.1.60)).
- Personal readings are never scored.

### 12.5 The small-model reading

**Outputs.** Six private tables: `turns`, `qa_pairs`, `question_bank`, `summaries`, `dated_statements` and `predictions`. Each row carries item and sentence ids, time stamps or character positions, the text's hash, and model, prompt and codebook versions. Speaker roles in speech-to-text need diarization on a GPU, or boundaries checked by people.

**Route.** Bulk reading uses the Message Batches API with `claude-haiku-5-5` under 4.5, with [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) and the thinking setting recorded. Agents only run pilots and adjudication: they cannot fix output formats or record exact model ids, and would need at least 45 hours per read. Both routes send text to Anthropic, and batch results stay downloadable for 29 days, so privacy turns on the account's data terms (D14).

**Chunks and provenance.** Sentences are numbered first; windows follow 4.2. The reader sees anonymised chunk ids, never a path, person, title or year. It returns sentence ids and labels; code voids ids not in the chunk. Raw answers are kept. Prompts hold no example dates, names or years; priming and order checks (4.4) use a development set, not the gold sample. Refusals are counted and recoded, as Haiku 5.5 has no server-side fallback.

**Cost.** Haiku 5.5 costs $0.10 per million input tokens and $0.50 per million output tokens, half in batches ([pricing](https://platform.claude.com/docs/en/about-claude/pricing)). Three passes cost about $0.006 per audio hour in batches when the cache hits, $0.009 when it never does (the basis 4.5 plans on), and $0.012 at standard rates (4.6, recomputed). That is $10 to $20 for the source texts and $140 to $280 for the 23,200 hours, or about $210 in batches with no cache hits. The 7,647 works of unknown length are not priced. Sonnet costs 20 times as much and Opus 40; a 10% Sonnet audit adds about $270.

**Validation.**
- A random gold sample, stratified by person, decade, text kind and format, is fixed first and never tunes prompts.
- Haiku re-runs 5%, Sonnet re-labels 10% blind, Opus settles disagreements, and three people label 50 to 100 units per label family ([Calderon et al. 2025](https://arxiv.org/abs/2501.10970)). All human coding takes 100 to 200 person-hours (4.7 estimates about 205 for its gold sets). With only the owner coding, the default (D5), results are "agreement with Opus".
- Krippendorff's alpha is used from 0.80, tentatively from 0.667 ([Hayes and Krippendorff 2007](https://doi.org/10.1080/19312450709336664)). 100 units give ±0.13, so fields used in tests get 400.
- Recall needs 100 real predictions in the gold sample, some from text the rules missed, for ±0.08 ([Webber 2013](https://doi.org/10.1145/2414782.2414784)).
- Rates use prediction-powered inference ([Angelopoulos et al. 2023](https://doi.org/10.1126/science.adi6000)), regressions its coefficient form or [DSL](https://arxiv.org/abs/2306.04746). Correcting by era or channel needs gold in each, or stated assumptions and bounds.

### 12.6 Statistics to research-paper standard

- **Unit and intervals:** the recording, not the word, is resampled ([Lijffijt et al. 2016](https://doi.org/10.1093/llc/fqu064)). Every effect size gets a 95% interval from at least 2,000 resamples (10,000 for confirmatory tests, 5.0), except the last-N contrasts at N = 5 and 10 (12.3). No p-value stands alone.
- **Denominators:** per channeled word or minute, without intros, adverts, music or the medium's own talk. Each recording gets a channeled share, so a format change does not read as a content change.
- **Models:** negative binomial models with channel and recording effects; hierarchical GAMs that pull small channels toward the group ([Pedersen et al. 2019](https://doi.org/10.7717/peerj.6876)), with R and mgcv added to the 4-core setup.
- **Preregistration:** N values, features, codebook, thresholds, tests and seeds are hashed before analysis ([Nosek et al. 2018](https://doi.org/10.1073/pnas.1708274114)). Confirmation uses the hash split and loader seal of 2.6, as the source texts are already profiled.
  - Candidate primary questions: dated predictions rise before a focal year and fall after; after a lapse, a new date within a year is commoner than silence; specificity falls over a career; hedging rises as deadlines near (family B4).
  - "No change" needs an equivalence test ([Lakens 2017](https://doi.org/10.1177/1948550617697177)).
  - Before-and-after tests only at fixed dates ([Lopez Bernal et al. 2017](https://doi.org/10.1093/ije/dyw098)): 2012-12-21 (within L/L and Kryon only), 2020-03-11 (pandemic) and 2023-07-26 (US House UAP hearing). Other dates are exploratory.
- **Checks:** a multiverse of alternative choices ([Steegen et al. 2016](https://doi.org/10.1177/1745691616658637)); uniform p-values under shuffled order; planted shifts found, planted drift not flagged; a second script recomputing every table.

### 12.7 The dashboard

**Build first,** static and computed in advance from listings and dated texts, while transcription runs. Until freeze S2 (section 8) it shows metadata and counts; text features and predictions join after the freeze, as D10 asks, unless the owner changes D10.
1. A coverage strip: channels by year, plus "undated" and "order only", shaded by hours, one panel per text kind.
2. Per-year small multiples for channels with 20 or more dated main works (the old Fig 7c-a).
3. Last-N bands: the latest window as a dot over earlier windows' spread, as on the [NSIDC sea-ice chart](https://nsidc.org/sea-ice-today/sea-ice-tools/charctic-interactive-sea-ice-graph) (the old Fig 7c-b and 7c-c).
4. Prediction rows per channel and the combined timeline; channels on a funnel plot, not a league table ([Spiegelhalter 2005](https://doi.org/10.1002/sim.1970)).
5. Two required switches, with no "both": corpus group and text kind.
6. A details card: time stamp and checked quotes. Public links open the publisher's copy at that time (YouTube's `t=`; `#t=` on podcast and archive.org files, per [media fragments](https://www.w3.org/TR/media-frags/)). Held audio is linked only on the owner's private page, and no link encodes a private path.
7. A banner: claims are reported as claims, with uncertainty in plain words. A table under each chart, a list view at 320 pixels wide, and layout checks at 320, 400 and 1,100 pixels.

First fill: Scranton, L/L and Laarkmaa, plus last-N on duration, format and titles for every listed channel.

**Improve after** a few weeks of use: families, filters, compare mode, a page per prediction, downloads. Each round is tested with 3 or 4 followers and 3 or 4 sceptics ([Nielsen 2000](https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/): 3 or 4 per group), and against [WCAG 2.2](https://www.w3.org/TR/WCAG22/).

### 12.8 Further analyses, ranked by value against cost

1. **Named beings, stars and places,** stars linked to [SIMBAD](https://doi.org/10.1051/aas:2000332). Under an hour.
2. **Keywords and coined words.** Minutes.
3. **View counts** against content. Minutes.
4. **Self-repetition,** including titles re-used for new messages. CPU hours.
5. **Who voices whom:** Q'uo came through four L/L channelers; Scranton voices about 25 beings ([Burrows 2002](https://doi.org/10.1093/llc/17.3.267); the impostors method, [Koppel and Winter 2014](https://doi.org/10.1002/asi.22954)). CPU hours.
6. **Audience questions:** needs by year; answers that reframe or refuse. Dollars, plus gold.
7. **Titles against content.** Needs YouTube text.
8. **Commercial content:** course and payment-plan promotion. Dollars.
9. **Health and conspiracy content in warnings** ([Ward and Voas 2011](https://doi.org/10.1080/13537903.2011.539846)). Dollars, plus gold.
10. **Wording spreading between channels** ([Barron et al. 2018](https://doi.org/10.1073/pnas.1717729115)); [Wahbeh and Glick 2026](https://doi.org/10.1080/02604027.2026.2656120) compare content, not style. Needs dates.
11. **Trance voice and prosody** against the medium's own. Samples on CPU.

### 12.9 Private and public

**Private:** audio, transcript text, paraphrases, question texts, summaries, raw model answers, embeddings (which can largely rebuild text; [Morris et al. 2023](https://aclanthology.org/2023.emnlp-main.765/)), the gold sample, anything naming a questioner.

**Public:** ids, labels, counts, dates, intervals, time stamps, model and prompt versions, codebooks, agreement figures, and the tables of 12.2 to 12.4.
- Theme and family labels: person-written, neutral, 8 words at most, covering 10 or more items from 3 or more recordings, with no 5-word run from any transcript.
- Quotes: checked, at most 30 words, with recording and time stamp; one per family, one per work, at most 5% of its words, capped per channel.
- A guard checks every publish, including total overlap with the private texts.

This is looser than 5.6, whose public timeline shows counts only. Until the owner decides (D16), the rule of 5.6 holds.

### 12.10 Order of work

0. **Owner decisions,** with defaults, in the decisions tables (roadmap section 4; section 11 here: D1, D2, D5 and D12 to D16). *Done when* each is settled.
   - **YouTube (D12):** a written, scoped robots.txt exception, or listings and dates through the [YouTube Data API](https://developers.google.com/youtube/v3/determine_quota_cost), which no robots.txt bars: about 2,400 of 10,000 daily units, refreshed monthly as its [policies](https://developers.google.com/youtube/terms/developer-policies) require. Default: the YouTube lanes stay off; the listings are kept, labelled by route and not refreshed (roadmap D8, HANDOFF 6.6). The Data API needs the owner's own key and is not built.
   - **Speech-to-text (D2):** the engine chosen by benchmark first (base.en: word error rate 0.729 on a 1981 tape). Language is detected per recording; about 2,050 main works (1,310 hours) need a multilingual model and analysis per language.
   - **Machines (D1, D13):** off-YouTube audio (about 3,100 hours, counting the 146 video-only archive.org sessions) needs about 3 weeks of cloud CPU; YouTube audio, about 500 GPU-hours with large-v3 on the owner's computer (not measured). Storage: about 250 GB, against 10 GB free.
   - **Also:** the account's data terms, before any batch (D14); coders, hours, pay and blinding (D5); deletion tracking, as 6 of the Index's 75 recordings have left YouTube (D15); hit rates only in aggregate (D16).
1. **Works, dates and lengths:** the works script, date parsers, twin checks, merging of sessions and parts, and first-seen and last-seen dates per id, seeded from earlier inventories. Download timeouts (now 3,600 seconds on YouTube, 1,800 on files) scale with length, resume and get their own error class. The cycle budget stops at the first overflow instead of skipping long items. Transcription runs in 30-minute windows, one long file at a time. *Done when* counts match `coverage.csv`, a 300-second item lands in the short group, a session of short parts does not, and list-order dates are scored on Scranton's 1,800 one-to-one pairs.
2. **Codebooks, output formats, preregistration, development and gold samples.** *Done when* all are hashed, a 50-chunk pilot passes, and alpha per field has intervals.
3. **Dashboard v1** (12.7). *Done when* it passes the width checks and the guard (12.9).
4. **Speech-to-text and reading, in parallel,** adding panels as data arrive (content panels after freeze S2, 12.7). After the priority items of 4.6, transcription follows a seeded order by person, year and length band, Ra recordings first, checked against L/L's texts. Haiku reads the source texts, then transcript batches with one pinned model, prompt and control set, as one run; Sonnet checks. *Done when* word error rate per decade, precision and recall have intervals for both text kinds.
5. **Dates, families, timelines.** *Done when* 200 time expressions and 500 family pairs are checked, and each channel with predictions has a timeline.
6. **Features by year and last N,** corrected for model error. *Done when* the Phase 7c test holds.
7. **Dashboard v2.** *Done when* it has had two reader rounds.
8. **Checking, then 12.8 in order.** *Done when* every scored family has frozen criteria and two coders' verdicts.

## Appendix A. Checks made for this plan

**Fresh counts.**
- `judge_snapshot.py` takes the last record per item, counts only, and writes `judge_snapshot.json`. Both are
  kept privately, in the folder `analysis_plan/` of the asset `scratch-notes-2026-11-14.tar.gz` of the
  release `handoff-2026-11-14` (HANDOFF section 3 unpacks it into the private folder).
- It matches the handoff: 1,138 audio files, 819.5 h, 10.11 GB; 61 transcripts; 8,425 source texts; 262 Bashar archive.org files from 146 items. It also matches the store's verified counts.

**Discrepancies between drafts or readers, resolved:**
- **Transcripts.** Draft A's 67 transcripts (284,737 words, 33.4 h) counted every "ok" row in the manifest, including rows left behind by re-runs after the id migration. There are 61 unique transcripts (259,518 words, 30.6 h), which matches the store and the 61 text files on disk.
- **Held twins.** `plan/bashar_recordings.csv` shows 5 of the 75 digested recordings held here: 4 as podcast audio of the same interview, 1 as podcast text only. The readers' "4" and "5" were each partly right.
- **Era table.** Draft C's archive.org era table was recounted and matches.

**API facts.** Checked against the bundled Claude API reference, cached 2026-11-03:
- the model id `claude-haiku-5-5`;
- prices of $0.10 / $0.50 per million tokens up to 100K-token prompts, and $0.50 / $2.50 beyond;
- cache reads at 0.1x, and a minimum cacheable prefix of 512 tokens;
- Batches: 50% off, 100,000 requests or 256 MB per batch, at most 24 hours, results kept 29 days;
- non-default sampling parameters rejected with a 400;
- adaptive thinking by default, which can be disabled at effort high or below;
- a tokenizer that counts about 30% more tokens;
- refusals with no server-side fallback;
- `output_config.format` for structured outputs.

**Code.**
- `transcribe.py` uses `BatchedInferencePipeline` by default and sets `condition_on_previous_text=False` only on the unbatched path.
- The manifest records batch size and whether VAD was on, but not beam size, temperature fallback or VAD parameters.
- `verify.py` writes `machine_text` beside an empty `human_text` column.

**Draft numbers re-read** from the scratch folder:
- `lang_plan_costs.json`: costs, embedding volumes, gold-set arithmetic;
- `lang_plan_sizes.json`: Phase 7a sizes, the 24 paired items (33.8 h), the 6 pairs already done;
- `design_numbers.json`: split and power;
- `network_sizes.json`: network sizes.

**Other checks.**
- The credential file in the working tree is ignored by Git and has no history.
- No web search ran, no model was loaded, and no file was changed outside the scratch folder.

## Appendix B. References (verify before citing)

- **Speech-to-text:** Radford et al. 2023; Koenecke et al. 2024; Bain et al. 2023; Bredin et al. 2020.
- **Coding with language models, and reliability:** Krippendorff 1995 and 2018; Hayes and Krippendorff 2007; Artstein and Poesio 2008; Rajpurkar et al. 2016; Gilardi, Alizadeh and Kubli 2023; Törnberg 2024; Pangakis et al. 2023; Egami et al. 2023 (DSL); Angelopoulos et al. 2023 (PPI); Baumann et al. 2025; Maynez et al. 2020; Min et al. 2023; Palmer, Smith and Spirling 2024.
- **Embeddings:** Reimers and Gurevych 2019; Muennighoff et al. 2023; Enevoldsen et al. 2025; Rodriguez and Spirling 2022; Morris et al. 2023.
- **Topic models:** Blei, Ng and Jordan 2003; Griffiths and Steyvers 2004; Roberts et al. 2014 and 2019; Grootendorst 2022; Denny and Spirling 2018; Schofield et al. 2017; Lau, Newman and Baldwin 2014; Röder et al. 2015; Chang et al. 2009; Ying, Montgomery and Stewart 2022; Hoyle et al. 2021; Maier et al. 2018.
- **Keyness and style:** Monroe, Colaresi and Quinn 2008; Hardie 2014; Lijffijt et al. 2016; Gries 2008; Egbert and Biber 2019; Dunning 1993; Kilgarriff 2005; Burrows 2002; Evert et al. 2017; Koppel, Schler and Bonchek-Dokow 2007.
- **Repetition:** Broder 1997; Leskovec, Rajaraman and Ullman (MMDS, chapter 3); Lee et al. 2022; Charikar 2002; Manku et al. 2007; Zhu et al. 2016; Smith, Cordell and Mullen 2015; Wang 2003; Biber, Conrad and Cortes 2004.
- **Networks:**
  - Newman 2001; Latapy et al. 2008; Tumminello et al. 2011; Neal 2014 and 2022; Serrano et al. 2009; Traag, Waltman and van Eck 2019; Lancichinetti and Fortunato 2012; Peixoto 2023; Fortunato and Barthélemy 2007; Good et al. 2010; Opsahl et al. 2010; Borgatti, Carley and Krackhardt 2006; Krackhardt 1988; Dekker, Krackhardt and Snijders 2007; van Eck and Waltman 2009.
  - Added by Draft B and also to check: Almeida-Neto et al. 2008; Strona et al. 2014; Barber 2007.
- **Inference:** Holm 1979; Benjamini and Hochberg 1995; Benjamini and Yekutieli 2001; Phipson and Smyth 2010; Efron and Tibshirani 1993; Field and Welsh 2007; Barr et al. 2013; Lakens 2013; Steegen et al. 2016; Simonsohn et al. 2020; Egami et al. 2022.
- **Reporting and ethics:** the ARR Responsible NLP checklist; Bender and Friedman 2018; Gebru et al. 2021; Pushkarna et al. 2022; Akhtar et al. 2024; Mitchell et al. 2019; Shimorina and Belz 2022; van den Akker et al. 2021; Wilkinson et al. 2016; franzke et al. 2020; Zimmer 2010; Smart 1973; Porpora 2006.
