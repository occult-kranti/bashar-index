# channels-ET snapshot: integration plan for et-channelers

*Written on 2026-11-14 by an agent workflow: five readers of the snapshot's new parts and a writer who re-checked the key numbers. Nothing from the snapshot was run. Paths under `/workspaces/_incoming/` and `/workspaces/et-channelers-private/` are on the Codespace, not in this repository. Section 6 is now phase 4b of [`../../ROADMAP.md`](../../ROADMAP.md).*

Written 2026-11-14. It draws on five readers' reports, and I re-checked the key numbers against the files. I changed nothing and ran no code from the snapshot.

Path shorthand used below:
* `app/` is `/workspaces/_incoming/kimi-agent-youtube-et/app/` (the snapshot).
* `et-channelers/` is `/workspaces/bashar-index/et-channelers/`.
* `<root>` is the private folder `/workspaces/et-channelers-private/`.
* `notes/` is `/workspaces/_incoming/notes/`.

## 1. What the snapshot is

"Kimi_Agent_YouTube ET Channel Analysis.zip" is a copy of the channels-ET repository (the Channeling Atlas). It was last updated on 2026-11-14 at 02:31 UTC (`app/research/acquisition-2026-11/reference-summary.json`). It has 2,275 files. 517 of them are newer than the clone that the earlier notes read (`/tmp/et-drive/only_new.txt`):
* 380 are in `app/research/expansion-2026/` (24 October);
* 134 are in `app/research/acquisition-2026-11/` (10 to 14 November);
* 3 are in `app/scripts/expansion/`.

It holds no audio and no transcript bodies. A file search found no audio, `.srt`, `.vtt` or transcript files. Those stay in the other agent's private cloud folders.

What it adds:
* **An inventory.** 2,840 YouTube video records on 302 accounts. This is the 8 November inventory (2,812 records on 297 accounts) plus 28 videos and 5 playlists.
* **An October selection.** 942 indexed, 748 eligible and 733 chosen (100 Bashar, 633 other). It drops every recording under 300 s (`app/research/collection-policy/summary.json`).
* **Converter audio.** Audio of 42 YouTube videos, fetched on 2026-11-10 through the y2mate.gs converter (`app/research/acquisition-2026-11/download_y2mate.py` line 124). It comes with 34 `tiny.en` transcripts (146,605 words), 572 question units and 69 AI verdicts.
* **Paste-link subtitles.** Subtitles of 12 of those videos, from three paste-link services (`app/research/expansion-2026/youtube-transcripts/acquisition-ledger.json`).
* **Publisher-feed interviews.** 12 Bashar interviews downloaded again from the publishers' own feeds (15.09 h, 153,975 words), with 715 question units.
* **Paper and code.** A 57-page draft paper, AI review rounds, dashboard builders and analysis code. `app/research/acquisition-2026-11/analysis/verification.json` passes 121 of 121 checks; its README says 119.

Every label and every review was made by AI agents (`humanValidated=false`). None of the new work is merged or deployed. Round 15 asks for a new review (`app/research/acquisition-2026-11/reviews/round15/README.md`).

## 2. What we take

Rules for everything below:
* We take public metadata, methods and published results.
* We run none of their code.
* Every file we copy goes to `<root>/comparison/channels-et/`. Each one is listed in `<root>/comparison/channels-et/manifest.json` with its snapshot path, size, sha256 and the route that produced it.
* The folder goes into the private store's state bundle.

### (a) Metadata and inventories

| Source in the snapshot | Becomes on our side | Checked by |
|---|---|---|
| `app/research/acquisition-2026-11/channel-reference.csv` (302 accounts) | A private copy. From it: (1) channel ids for our people in `et-channelers/sources/extra_channels.csv`, one row each with evidence; (2) old routes and second channels in a new `et-channelers/sources/channel_aliases.csv` (person_id, route or id, kind, evidence, checked), read by `discover.py` and `targets.py`; (3) the new host rows of part 4 | 302 rows and the sha256. An id goes into `extra_channels.csv` only after `discover.py --only <person>` lists it or the channel page shows it. Matches by name only wait for the owner |
| `app/research/acquisition-2026-11/video-reference.csv` (2,840 ids, 955 titles, 871 lengths from their metadata) | A private copy, joined to our listings by `video_id`. Skip the 28 lengths they measured on converter files | 1,759 ids are already in our 63 listings and 1,081 are not (my join). Most of the 1,081 are on accounts we do not track, or are embeds on publishers' sites (631 have no account: `notes/05-cet-youtube-inventory.md` line 243). They are leads for `et-source-scout`, not queue items |
| `app/research/acquisition-2026-11/all-candidates.json` (the 43 converter candidates) | `<root>/comparison/channels-et/converter_ids.csv` with: id, account, our person_id, their status, whether it is in our listing, and the note "fetched by channels-ET through y2mate.gs; not reused" | 43 rows (my join). 23 are in our listings (14 Tyler Ellison, 2 Shaun Swanson, 7 others). 10 are on Lee Carroll's channel, which we have not listed. 3 are on Calenara, Christine Day and Barbara Marciniak. 7 are on re-upload accounts |
| `app/research/expansion-2026/publisher-cohort/plan.json` (20 Bashar interview episodes, with enclosure address and expected sha256) | 10 are already in `<root>/catalog/catalog.csv` (A01 to A04, A11 to A15, A18). The other 10 are on 7 shows that have no feed here (part 4). Those shows go into a new `et-channelers/sources/host_channels_more.csv` (the columns of `bashar_host_channels.csv` plus `found_in`), so that `host_channels.py` does not overwrite them. `find_host_feeds.py --hosts` reads that file | The feed is graded by `find_host_feeds.py` and episodes are typed by `interview_types.py`. Only live channeling is fetched. The expected sha256 marks a fetch as exact or changed |
| `app/research/expansion-2026/inventory/tables/selected_records_enriched.csv` and `practitioner_overlay.csv` (733) | A private copy. Their practitioner and entity labels become extra columns keyed by `video_id`, and never replace ours | Shown as "their label" |
| `app/research/expansion-2026/inventory/tables/title_reuse_fuzzy_families.csv` (170 families) | Candidate repost pairs for duplicate removal (Phase 6) and for Phase 7a question 1 | Decided by audio fingerprint and words, never by title |
| `app/research/expansion-2026/inventory/tables/bashar_route_census.csv` (68) and `bashar_cap_publisher_coverage.csv` (39) | New Bashar re-upload rows in `host_channels_more.csv`. The missing ids of Cosmic Bridge and ozy bourne in `et-channelers/sources/bashar_host_channels.csv` | Lookup with `host_channels.py` |
| `app/research/expansion-2026/acquisition/keyword-search-plan.jsonl` (109 context rules) | Screening words for `et-source-scout`: terms to include, terms to exclude, and false positives already seen | Its 806 YouTube search addresses are never run |
| `app/research/collection-policy/selection.csv` (942) | A private copy, kept as the record of their rule (part 5) | Unchanged since the older clone (note 05) |

Not needed: `app/research/expansion-2026/source-reading/youtube-watch-pilot.json` (13 watch pages read for metadata). `discover.py` gives the same fields.

### (b) Methods and code to re-implement (their code is never run)

| Method (where in the snapshot) | Becomes on our side | Checked by |
|---|---|---|
| Wrong-language and broken-output check. It flags text where German or English function words are over 0.08 of the words, text with Arabic letters, output under 45 words a minute, and output where one word triple is 15% or more of all triples (`app/research/acquisition-2026-11/transcribe_youtube.py` lines 98-117 and 272-284) | A check after speech-to-text in `et-channelers/pipeline/transcribe.py`, beside the feed-language rule. A flagged item is marked `wrong_language` or `degenerate` in `transcripts_manifest.jsonl` and redone with the right model | A test in `et-channelers/pipeline/tests/` with made-up German text (the Pavlina Klemm case) |
| Receipts: a hash of the settings, a hash of the code, a lock per item, and finished records that are never downgraded (same file; `app/research/acquisition-2026-11/reuse_verified_audio.py`) | `settings_sha256` and `code_sha256` in `transcripts_manifest.jsonl`. A transcript is reused only when the audio, settings and code hashes all match | Test |
| Question units (`qmark_merge_v1`). Sentences with a "?" are merged when 1.5 to 2 s apart. The answer window is 4 segments or 90 s and stops at the next question. Windows have six states. The discourse class stays "unclear" unless the text shows more (`app/research/expansion-2026/asr-qa/build.py` lines 287-358; `asr-qa/protocol.json`) | A new `et-channelers/pipeline/qa_units.py`, written from the protocol. It works on sentences with word time stamps from `transcribe.py`, because our `base.en` segments average about 27 s and theirs 3.7 s. Output: `<root>/analysis/qa_units.jsonl`, with offsets and hashes only | A reader ran their rule on our segments of `pod-3c5a1234149ddedb`: it found 50 units. On their own segments of the same episode (another edition) it found 97, although the counts of "?" are close (132 and 146). The sentence version must close that gap |
| Family key: the sha256 of the sorted content words (`asr-qa/build.py` lines 361-373) | Part of `qa_units.py`, with three fixes: (1) a family needs at least two content words; (2) "what, who, which, mean, sure, true, else, right" are stop words; (3) only families with content get a repost flag | A test that fails when a recurring family rests on one function word. Their largest "common question", `749ab2c0d06c42ae` (21 members, 11 sources), is the single word "what" (hash checked) |
| AI review of a sample. The sample is seeded and stratified; each verdict has five flags; the verdict is tied to the row's hash; the reviewed class is written back to the row (`asr-qa/build.py` lines 603-648; `asr-qa/apply_review.py`; `app/research/expansion-2026/non-bashar-analysis/apply_review.py`) | The Phase 7c audit, in which a larger model checks Haiku's rows | Add Cohen's kappa, which they never report |
| Topic and cluster checks. NMF stability over 10 random starts. KMeans silhouette, with ARI measured against the other seeds (`app/research/acquisition-2026-11/analysis/build.py` lines 1029-1106). An advert filter, `COMMERCIAL_RE` (`asr-qa/build.py` lines 87-90) | Rules for 7a and 7c in `ANALYSIS_PLAN.md`: mask names, entity names and adverts first; match topics one to one; compare silhouettes with shuffled data; fix split tokens such as "ve", "don" and "ll" | No topic or cluster is claimed unless it beats the shuffled baseline |
| Edition states: exact, changed or failed, against a known sha256 (`app/research/expansion-2026/publisher-cohort/scripts/download_audio.py`) | An `edition` field in our enclosure manifest when an item is fetched again. In feeds that insert adverts, duplicates are found by GUID and by transcript overlap, not by bytes | ACID FOR SQUARES #68 already exists in three byte editions: two of theirs and one of ours |
| Membership count for videos on several channels: unique videos = account memberships + unattributed videos − extra memberships (`app/research/acquisition-2026-11/reference-summary.json`) | A check in `et-channelers/pipeline/catalog.py` and in the dashboard builder | Their 2,286 + 631 − 77 = 2,840 |
| States kept apart: listed, eligible, selected, attempted, reached, downloaded and transcribed. A failed probe counts as one observation, not as N failed videos (`app/research/expansion-2026/acquisition/README.md` lines 30-40) | Columns per lane in `et-channelers/plan/coverage.csv`, including `refused` | The dashboard shows "not recorded" for an empty cell, never 0 |
| Public tables rebuilt in a temporary file, counts checked, then replaced in one step; `safe_cell` for CSV cells (`app/scripts/expansion/rebuild_public_sqlite.py` lines 34-49; `app/research/expansion-2026/qa/build.py` line 104) | `et-channelers/pipeline/export_public.py` | Test |
| Leak test. Theirs compares only 500 segments of one source (`asr-qa/verify.py` lines 87-105) | A stronger `et-channelers/scripts/guard_no_raw_media.py` that compares word runs in every public file with all private transcripts | Fail on a run over 30 words; warn at 10 |
| Reviews of hashed snapshots (`app/research/expansion-2026/reviews/round13/snapshot.json`) | `et-reviewer` records the sha256 of every file it reviewed | A changed hash needs a new review |
| Coding rules for predictions. Timing is coded as conditional or deferred. A reference to an earlier message is not a forecast. Denials of the premise are kept (`app/research/expansion-2026/source-reading/manual-transcript-notes.md` lines 24-30; `paper/sections/08-answer-resemblance.tex` lines 84-98) | Labels in the Phase 7c prediction protocol | The scoring rules are written before any outcome is checked |
| Paper standards: a table of acquisition states; a table of cohorts with what each one is not; exact denominators; falsifiers; a statement on AI use; and a script that ties each quoted number to its file (`app/research/expansion-2026/paper/sections/03-sources-acquisition.tex`, `04-cohorts-units.tex`, `appendices.tex`, `14-future-analyses.tex`, `15-disclosure.tex`; `paper/verify.py`). Related work is in `paper/references.bib` | Our methods note and the Phase 8 release check | Before citing a source, check how deeply they read it in `app/research/expansion-2026/literature/methods-register.md` |

### (c) Results to compare ours against

| Their result (where) | Compared with | Label |
|---|---|---|
| Title topics. NMF chose K=5 by seed stability (0.853), and the topics follow channel and entity names. KMeans finds no structure. Merging near-duplicate titles removes 12% to 38% of the network's links (`app/research/expansion-2026/inventory/analysis.json`) | Our 7a and 7c topics on transcripts | "channels-ET, titles only" |
| 715 question units on 12 Bashar interviews, 32.5 to 79.3 per hour with `tiny.en` (`app/research/expansion-2026/asr-qa/analysis.json`, `asr-qa-public.csv`) | Our units on the same episodes. Their A04 is byte-identical to our `pod-505525fbd6216f31` (checked), with 38 units. That allows a direct check of `tiny.en` against `base.en`, and of their unit finder against ours | "channels-ET, publisher feed, tiny.en" |
| AI review of 60 units: 43 accepted, 14 rhetorical, 3 rejected, and 8 with boundary problems (`app/research/expansion-2026/asr-qa/manual-review.json`) | Starting estimates and sample size for our 7c audit | Same |
| Answer resemblance. The difference disappears once publishers are resampled (interval −0.006 to 0.031) (`app/research/expansion-2026/qa/analysis.json`; critique in `app/research/expansion-2026/reviews/round13/methods.md` lines 104-114) | Our comparisons across channels | An expectation, not evidence |
| Converter cohort. 572 units. Review of 69: 7 confirmed, 49 reclassified, 13 boundary errors; often these were Kryon's own questions in solo talks. Silhouette at most 0.0070 (`app/research/acquisition-2026-11/analysis/analysis.json`, `manual-review.json`) | Cited only | "channels-ET, converter-derived" |
| Subtitle cohort. 23 of 57 units have boundary errors caused by caption line breaks (`app/research/expansion-2026/non-bashar-analysis/analysis.json`) | Cited only | "channels-ET, paste-link-derived" |
| Only 3 of their 100 Bashar picks are on the official channel (`app/research/expansion-2026/inventory/tables/bashar_cap_publisher_coverage.csv`, a reader's join) | Decision D1 | – |

### (d) Transcript text (private store only, with provenance)

* The zip holds no transcript bodies. It holds only short excerpts and AI paraphrases.
* Some of that text comes from allowed lanes (publishers' feeds and pages):
  * `app/research/expansion-2026/qa/qa-records.csv` has 37 AI paraphrases: 21 from podcast speech-to-text, and 16 prompts written from Daniel Scranton and Paul Selig texts. Answers run up to 41 words.
  * `app/research/expansion-2026/asr-qa/manual-review.json` has review notes of 25 words or fewer. Some quote a question.
* What we do with that text:
  * Take only ids, time offsets and hashes, into `<root>/comparison/channels-et/qa_reading_2026.csv`.
  * Copy paraphrase text only if a calibration needs it. It goes into the same private folder with a `provenance` column: "channels-ET AI paraphrase, 2026-10-24, of tiny.en speech-to-text of the publisher's own feed".
  * It never goes into the repository. It never sits in one table with our source texts or our speech-to-text.
* Nothing is taken from the converter and paste-link lanes (part 3).
* The `digest_legacy` cohort is our own data. It is 949 rows in `app/research/expansion-2026/qa/qa-database.sqlite`: the question lists of 67 of our digests. `app/data/digests` is byte-identical to `/workspaces/bashar-index/data/digests` (75 of 75 files, checked). We do not import it again.

## 3. What we do not take, and why

| Item | Where | Why not |
|---|---|---|
| Audio of 42 YouTube videos (35 counted, 7 under 300 s kept in quarantine), 34 transcripts, the segment index, 572 question units with their excerpts, and every statistic built on them | `app/research/acquisition-2026-11/download_y2mate.py`: headless Chromium opens y2mate.gs, pastes the watch address and saves the MP3. Run log: `acquisition-ledger.json`, 23:14 to 23:56 UTC on 2026-11-10 | A converter site fetched YouTube for them. Their paths (`cloud-raw://`, `/mnt/agents`) suggest a cloud sandbox. That gets around YouTube's refusal, and our rules forbid it. The script reads no robots.txt. One file (`1UufR6Wn9z8`) was already there when the run began; how it was obtained is not recorded |
| Subtitles of 12 videos | `app/research/expansion-2026/youtube-transcripts/` (youtube-transcript.ai 9, CollabPals 2, NoteGPT 1; 13 more attempts failed) | Paste-link transcript services, which our rules forbid. Their transcriber also reads this text to guess the language (`transcribe_youtube.py` lines 184-189) |
| The non-Bashar analysis built on those subtitles: 57 units, figures and review excerpts | `app/research/expansion-2026/non-bashar-analysis/` | Same route |
| Fallback routes: Invidious, Piped, r.jina.ai, youtube-transcript-api, paid transcript services, and a caption request through an agent's web reader | `app/research/expansion-2026/acquisition/access-matrix.json`, `network-probes.json`, `tools-register.json`, and the `route_order` lists in `plan.jsonl` | Front-ends and services that get around the refusal |
| Their fetchers and mirrors | `app/research/expansion-2026/publisher-cohort/scripts/fetch_texts.py` (no robots.txt check); `download_audio.py` (replaces a host it cannot reach with a CDN address, then tries curl); model weights from hf-mirror.com | Our `et-channelers/pipeline/fetch_publisher_text.py` reads robots.txt first (class `Robots`, line 151). We fetch again with our own tools |
| Release and site code | `app/research/acquisition-2026-11/materialize_public_artifacts.py` downloads and runs gofile-dl and installs curl_cffi. `push_git_data.py` pushes with a token. `prepare_source_bootstrap.py` fails at line 42 (`manifest` is never defined). `app/scripts/pages/stage_site.py` runs sudo apt-get and still contains the Cobalt probe | It runs third-party code nobody has reviewed. Never run it, and do not open the gofile.io link |
| Personal data | `app/research/expansion-2026/storage/drive-state.json`; `app/research/expansion-2026/reviews/round13/acquisition.md`; a Drive folder id in `app/research/expansion-2026/HANDOFF.md`; 14 excluded accounts that are the owner's own subscriptions | Private. Keep it out of every table and every outbound request |
| Their selection rule | `app/research/collection-policy/policy.json` | A 300 s floor and a cap of 100 Bashar videos. Our rule keeps every length (`et-channelers/README.md` line 208) |
| Headline counts without their receipt | 119/119 in their README against 121/121 in `analysis/verification.json`; 34 against 36 artifacts; 507 against 509 staged files | Copy a number only together with the file that backs it |

**May what they already obtained be used privately, marked with how it was obtained?** Our rules forbid the method. They do not say whether material that someone else obtained that way may be kept. HANDOFF section 6.2 proposed to keep it. I recommend **not using it**, for four reasons:
1. None of it is in the zip. Using it would mean moving converter and paste-link media from the other agent's private folders into our store.
2. Getting it the clean way is a small job. The 43 videos come to about 21 measured hours, plus one compilation whose title says 8 hours. 23 of them are already in our listings, and 10 more come with Lee Carroll's channel. The YouTube lane on the owner's computer (the laptop lane) can fetch them all.
3. Our corpus and methods note can then say that nothing in them was obtained by getting around a refusal.
4. Their transcripts are another edition (`tiny.en`, 300 s windows with no overlap). We would redo them anyway.

What may be used is their published numbers. We cite them as their results, labelled "converter-derived" or "paste-link-derived", in a column of their own. If the owner decides otherwise, these conditions apply:
* the files go in a separate private folder;
* every file is tagged with how it was obtained;
* none of it counts as captured, or enters the main corpus or anything public;
* each file is replaced as soon as our own copy arrives.

Questions for the owner:
1. Was the y2mate.gs route known and approved for channels-ET? Its branch `research/acquisition-2026-11-expanded` would publish converter-derived figures and excerpts (`app/research/acquisition-2026-11/push_git_data.py`). Should it stay unmerged?
2. Are channelers and mediums outside our 103 who channel non-ET sources in scope? Examples: Crimson Circle, Suzanne Giesemann, Lee Harris, April Crawford.

## 4. New people or channels

"Records" are their counts in `app/research/acquisition-2026-11/channel-reference.csv`, given as observed / eligible / selected. They are not channel sizes: `uploaded_total` is empty for every account.

Across all 302 accounts:
* 59 match 59 of our people by channel id, handle or route;
* 27 match 21 of our people by name only;
* 216 match nobody.

The readers' crosswalk is in `accounts_vs_targets.csv` and `untracked_accounts_grouped.csv`, kept private: they are in `<root>/comparison/channels-et/` and in the asset `scratch-notes-2026-11-14.tar.gz` of the private release `handoff-2026-11-14` (unpack it into `<root>`).

Every target goes through `et-source-scout` first. The owner confirms any identity that was matched by name. The 28 untracked accounts that are already in `et-channelers/sources/bashar_host_channels.csv` need nothing.

### Accounts that are not among our 103

| Name | Handle or id | Records | Recommendation | Why |
|---|---|---|---|---|
| Calenara (Caroline and Leo) | @calenara, UClECKVt1ep1gjAzbZfbyAZg | 51/51/51 | Add as target | Their largest channel: 25.8 of 455.5 selected hours. ET entities in the labels (Ashtar, Sassani, Ra). None of its videos is in our listings |
| Tracy Kumbera | @TracyKumbera | 7/0/0 | Add as target | They screened her in as a direct channeler, and her site links the handle. Her own podcast feed has 204 episodes and 71 transcript files (`notes/05-cet-youtube-inventory.md` line 130). A feed can be fetched from the cloud |
| Multidimensional Soul (Akanksshaa) | @akanksshaa, UC1jF0BbiGpAB6ekXgByEPYg | 4/4/4 | Add as target | Screened in as a channeler and interviewer. Own feed on podbean (note 05 line 130). Type each episode |
| OmNa Sanctuary (Natalie Glasson) | @omnasanctuary, UCki3n6iD5mejV8C6DtEOUvw | 1/1/1, plus 221 embeds with no account | Add as target | omna.org pairs each message with its text and an MP3: 192 pages, 44.55 h (note 05 lines 138-139). These fit our creator-file and publisher-text lanes. 60 pages ask for an attribution line on any copy (note 05 line 410) |
| Christine Day | @christinedayonline, UCpEGC0keVGgMKRLLNOKq8Fg; twin /c/ChristineDayOnline | 2/2/2 | Add as target | A Pleiadian channeler in their pilot. Two routes, one channel |
| YahYel & Freunde (Simon Gerve) | @yahyeldeutsch, UCcRbh0NjCHy88-SNUtqd8NA | 8/8/8 | Add as target | Yahyel channeling in German. Needs language detection and a multilingual model |
| Jonathan Trinity Martin | @JonathanTrinityMartin, UC4m2GWzVejzwVj_Xn4aBM6A | 5/5/5 | Add as target | Yahyel labels. Also a guest on two shows |
| Ivet & Shayla YahYel channeling | @ivkahAndShayla, UCAF2kODnoBDKm5KuSpb7UeQ | 4/4/4 | Add as target | Yahyel network, own channel |
| Hucolo (Human Colonies) | @Hucolo, UCj5wGWloHE8hKHPd5kqWsJQ; @hucololibrarychanneling933; Hucolo 2 Live, UCgrfR7gORGqK0CETQhU8Btw; /c/HumancolonyOrg; /user/HumanColonies | 4/4/4 and 2/2/2; 0 on the other three | Add as target: one person with five routes | Long sessions (7.6 h in 4 records). Count the routes once |
| Odyssey of Ascension (Roxanne Swainhart) | @OdysseyofAscension, UCoxINFqPqOU6W8OOTi1nqeQ | 3/3/3 | Scout first | Yahyel labels; small |
| Crimson Circle (Geoffrey Hoppe) | @TheCrimsonCircle | 3/0/0, plus 295 embeds with no account | Add as target if the owner keeps non-ET sources in scope | The publisher's own transcript PDFs (144 in English: `notes/09-critic.md` section 2, row 10) are a text lane that works from the cloud. Its sources are not ETs, like Seth or Abraham in our list |
| Suzanne Giesemann | @SuzanneGiesemann, UCGU9Lw6sITU4kvjqJ2gzaQw | 2/2/2 | Owner decides | A medium (Sanaya), not an ET source |
| Lee Harris | /user/LeeHarrisEnergy | 0/0/0 | Owner decides, then scout | A known channeler. No records here |
| April Crawford (The Inner Whispers Interviews) | @TheInnerWhispersInterviews | 2/2/2 | Owner decides | Channels "Veronica" (their label). Not ET |
| Ananda Frequencies (Amara Alquimia) | @AnandaFrequencies | 4/4/4 | Scout, low priority | Light-language transmissions. They may hold little speech |
| Alexander Quinn; Viviane Chauvet | @AlexanderQuinn1; @VivianeChauvetGalacticHealer | 2/2/2; 0/0/0 | Scout, low priority | Mostly seen as guests on other shows (3 and 5 records) |
| we-see-you-2; Matt & Enrico Channeling | @we-see-you-2547; @mattenricochanneling1952 | 3/3/3; 2/2/2 | Scout, low priority | Small Yahyel channels |
| SynchronicityJapan | @SynchronicityJapan | 2/2/2 | Scout first | Labels "Sasha (Pleiadian)" and "Ishthara". Check for a link to Lyssa Royal Holt before deciding |
| I Am New Earth Eden | @iamneweartheden | 5/5/5 | Add as host show | Appearances by Pia Orleane and Cullen Baird Smith, who are our `laarkmaa` (aliases in `et-channelers/sources/extra_targets.csv`) |
| KSMediaGroup | @KorneliaStephanie | 3/3/3 | Add as host show | Same (Laarkmaa) |
| Living Astrology | @LivingAstrology | 2/2/2 | Add as host show | Same (Laarkmaa) |
| The Moore Show | @themooreshowofficial | 2/2/2 | Add as host show | Ishuwa label: our `shaun-swanson` |
| Danica Patrick (Pretty Intense podcast) | @danicapatrick, UCjzc6KWjzKosSGw0VkIHaaw | 1/0/0, plus 2 episodes in their feed list | Add as host show | Bashar interviews with a public feed |
| Healing + Human Potential; SoulTalk with Kute Blackson; Virtual Campfire; Gateways to Awakening; Oh No, Ross and Carrie | feeds in `app/research/expansion-2026/publisher-cohort/plan.json` | 7 episodes | Add as host shows | Bashar interviews whose feeds are not registered here. Ross and Carrie is a sceptics' show, so expect "commentary" |
| Gaia Consciousness (podcast) | buzzsprout feed in the same file | 1 episode | Feed candidate for our existing row `host:gaia` | Our Gaia row has no feed yet |
| Bashar Channeling Podcast | @basharchannelingpodcast, UCLH8WD_3p2pkBzoimxU0SYw | 21/20/16 | Add as host show (re-upload), listed only | The largest new Bashar re-uploader. Needed for duplicate checks (Phase 6, Phase 7a question 1) |
| Conscious Living Today | @consciouslivingtoday | 6/6/6 | Add as host show (re-upload), listed only | Same |
| 17 more accounts with one Bashar-labelled record each (Bashar Channeling Daily, Bashar Higher Mind, Darryl Channels Bashar, Universe Awakening: Bashar Channeling, Hakawati Podcasts, Mente Autêntica and others) | in `untracked_accounts_grouped.csv`, group `new_bashar_repost_or_host` | 1 each | Add as host shows (re-upload), listed only | Same. Hakawati Podcasts may be an interview show: type it |
| Cosmic Bridge; ozy bourne | @cosmicbridge888, UCA2wguwtXnLln3Fhg_nihnQ; /user/arap35 | 2/0/0; 1/0/0 | Fill the id in our existing row | Already in `et-channelers/sources/bashar_host_channels.csv` by name, marked "no channel found" |
| KRYON Archives; KRYON CHANNELLING; Kryon Lee Carroll Español | UCnqGBcYUGgzV_6jbEgQ8lfA; UCbzZmC-cvS57cWbeBe7XPoA; UCpCvZr6ixNz628JUouxbBXQ | 0 each | Add as host shows (re-upload) for `lee-carroll`, listed only | To mark twins of the 1,306 kryon.com files we list |
| November playlists (Kryon, The Heyoka, The Importance of your last lifetime, The Stargate Experience, YAJAYRA) and The New Earth Frequency | `supplement-*` ids; @thenewearthfrequency | 1 each | Ignore as accounts, but mark their videos as re-uploads | They carry Kryon and Ryokah recordings that the people publish themselves |
| JeffMara Podcast; Interview with E.D.; Brian Scott; NEW PARADIGM FILMS | @JeffMaraPodcast; @interviewwithed; @BrianScott1111; @newparadigmfilms3326 | 4/4/4; 3/3/3; 2/2/2; 2/2/2 | Ignore for now | Interview channels that mostly feature people we do not track. Look again if a guest becomes a target |
| GFL Station Snippets; GFL Station; GFL Council Messages; Light Codes Awakening; Universal Lighthouse Higher Gnosis | @gflstationsnippets; @gflstation; @gfl_council_messages; @LightCodesAwakening; @universallighthouse | 2/2/2; 0; 1/1/1; 2/2/2; 3/3/3 | Ignore for now | They seem to collect or read out messages from several sources, with no single speaker. Check before any use |
| Channeling Erik site embeds | UC0ecgEdVOnQfijQ1JKtcrSA; /user/MsOinaes; UCN7upjryanS62vfB-xgPoBA; @psychiclizcross | 17/0/0; 8/0/0; 3/0/0; 2/0/0 | Ignore | No titles. These are mediums for a deceased person. The owner may add the site as a publisher later |
| All other new accounts (one record or none) | listed in `untracked_accounts_grouped.csv` | 0 or 1 | Ignore; keep as discovery leads | Too little to go on |
| 14 accounts that they excluded | not named here | 0 | Ignore; keep out of every table | The owner's own subscriptions |

### Accounts that belong to people we already track

| Our person | Their account | Records | Action |
|---|---|---|---|
| `lee-carroll` | Kryon Lee Carroll, UCMiuw8FLujKn06dnlxpbWGQ (tied to kryon.com in their notes) | 12/10/1 | Our row has the address but no id, and we have no listing for this channel. Put the id in `sources/extra_channels.csv`, then run `discover.py --only lee-carroll` |
| `barbara-marciniak` | UCSffF5wKtHDCezvV5tUm68w (@barbaramarciniak1593) | 1/1/1 | A candidate only: their note says current uploads were not counted. Scout first, then the owner confirms |
| `paul-selig` | UCBVD69mrsA_Vfx4dhu1aX6Q (@paulselig); /user/paulseligvideos | 2/2/2; 3/1/1 | Check with a listing, then add the id |
| `l-l-research` | UCY6atkykMJAljLkIP7L8ZVA (@llresearch); /c/LLResearch | 3/3/3 each | Same |
| `esther-hicks` | UCnBfVA-8WFwOXACivW1rPyA (Abraham-Hicks Publications); /user/AbrahamHicks | 2/2/2; 0 | Same |
| `channeling-arcturians` | UCO-NLR7buQ40JlsJshf130Q | 1/1/1 | Same |
| `judy-satori` | UC-Epj_gzOBrtm79CoOZSShA (Judy Satori's Ascension Library) | 1/1/1 | Same |
| `sarah-evans` | Into the Blue Channeling, UChH80310cC6HgkCxbHb5wng | 3/3/3 | Ours is @sarahevansandco. Is this a second channel? The scout checks |
| `darryl-anka` | /BasharChanneledbyDarrylAnka; Awaken with Darryl Anka, UC2XEhQiPV-MuIkxo9klEhRg; a look-alike, UCPvbIxYNi98uEpSDuJs9G6A; @BasharCommunications | 4/1/1; 1/1/1; 0; 0 | The first is his channel (all 4 ids are in our listing): record it as an alias. Check the other three before treating any of them as his |
| `daniel-scranton` | /user/danscranton; /danscranton | 116/25/25; 0 | Alias only: all 116 ids are already in our listing (checked) |
| `laarkmaa` | /user/laarkmaa | 17/1/1 | 16 of its 17 ids are not in our listing. List this route to see whether it is an older channel |
| `lyssa-royal-holt` | UCNAfojYPimQtLegcVl5-oGA | 16/3/3 | 6 of its ids are in our listing and 10 are not. Is it a second channel, or are these removed videos? |
| `shaun-swanson` | /user/IshuwaDotCom; /user/TheYahyel | 0 | Old routes: record them as aliases |
| `paul-hamden` | @retcheto; @The-Zeta-Connection; /user/Paulham33 | 0 | Channel candidates for a person who has no source yet: scout |
| `suzanne-ward` | THE MATTHEW BOOKS, UC8bAT0Ys7PC2AybDvR_Q78Q | 0 | Scout |
| `toni-ghazi` | @theantareanheart | 0 | Scout |
| Nine more: `nora-herold`, `rachel-chamness`, `rob-gauthier`, `wieteke-koolhof`, `suzanne-lie-ph-d`, `debbie-solaris`, `krista-raisa`, `kristin-davies`, `brad-johnson` | old /user/ or /c/ routes and related accounts | 0 to 3 | Record as aliases once a listing shows the same channel |
| `jamie-butler` | excluded there on an earlier owner instruction | – | Our decision stands: the owner asked for her on 2026-11-13 |
| Vivek Samtani (our row 104, which has no id) | @VivekSamtani | 0 | Excluded in both projects. Give our row an id, or move it to an exclusion list |

## 5. Effects on our plans

### Phase 7a: shorts and recordings of 5 minutes or less

* **The roadmap is wrong about their selection.** It does not set short recordings apart; it drops them. It excludes 123 recordings under 300 s. It holds back 61 recordings with no length and 10 with conflicting lengths. It finds only one Short, by its address (`app/research/collection-policy/summary.json`; their README line 61 says "excluded/held"). Nothing of theirs can serve as a group of short recordings.
* **The 300 s boundary differs.** For them a recording of exactly 300 s is eligible. Our main corpus is "over 5 minutes", so for us 300 s goes into the short group. Every table should say which side 300 s is on.
* **Their converter run set aside 7 Ryokah recordings under 300 s.** We want them. Six are in our `tyler-ellison` listing; the seventh is a re-upload.
* **Question 1 (repetition).** Their near-duplicate title families are a cheap first list of candidate pairs. Words and audio decide.
* **Question 2 (topics).** Their models found no structure. Silhouettes were 0.0070 on 34 transcripts (converter-derived), about 0.05 on 12, and 0.026 on 12 subtitle files (paste-link-derived). Topics fitted on titles only found channel names. So:
  * mask names, entity names and adverts before fitting;
  * fit on long videos only, as planned;
  * report seed stability, ARI against other seeds, and a shuffled baseline;
  * claim nothing that fails these checks.
* **Distinctive words.** Their log-odds with a Dirichlet prior (alpha 0.01) is the method we planned. Fix split tokens such as "ve", "don" and "ll" first.
* **Pace and question share.** A count of questions depends on where the speech-to-text model puts "?". Compare shorts and long videos only within one model. Their 32.5 to 79.3 questions per hour come from `tiny.en`.

### Phase 7c

* **By year.**
  * Their per-year table counts upload dates of titles. 438 of their 732 dated records are from 2026 (`app/research/expansion-2026/inventory/tables/temporal_yearly.csv`). That reflects when they collected, not growth.
  * Keep upload year and session year apart.
  * Use whole-channel listings as denominators, and resolve reposts first.
  * Adopt their test: if topics follow upload habits rather than the calendar, make no claim by year (`app/research/expansion-2026/paper/sections/14-future-analyses.tex` lines 80-84).
* **The last N recordings.**
  * Freeze each channel's list by hash, so that a window can be rebuilt.
  * Print "fewer than N" rather than padding.
  * Give intervals by resampling recordings or sessions within a channel (their cluster bootstrap: `app/research/expansion-2026/qa/build.py` lines 724-752).
* **Predictions and warnings.**
  * Add the labels "conditional or deferred", "refers to an earlier message" and "denies the premise".
  * Keywords cannot classify. Their keyword codebooks found 0 predictions in 57 units and called 51 of them "descriptive" (`app/research/expansion-2026/non-bashar-analysis/analysis.json`).
  * Use their timing pattern (`non-bashar-analysis/build.py` lines 174-176) only to count what the model missed.
  * Write the scoring rules first.
* **Timelines.**
  * Each point opens to: the recording id and link, the time stamp, a quote of at most 30 words, the model, the audit state, and the note "not checked against events".
  * Audited items are the main layer. Unaudited Haiku rows are a separate, marked layer.
  * A prediction repeated across recordings is one family, shown with a short label rather than a hash.
* **Q&A datasets.**
  * Columns: kind of text (source text, our speech-to-text, captions, model-made), `is_constructed`, `human_validated`, speaker (default "unknown"), discourse class (default "unclear"), answer-window state (six codes), support hash and offsets.
  * Run `qa_units.py` beside the Haiku pass and report how far the two agree.
  * Keep audience questions apart from a speaker's own questions. Their review moved 21 of 69 "direct" questions to "rhetorical": in Kryon's talks the speaker asks and answers his own questions.
  * Starting estimates for the audit: about 2 in 5 "?" units are not audience questions, and 13% to 40% have boundary errors.
* **Question banks across channels.**
  * Pairs from one channel, or from one reposted recording, are not independent.
  * TF-IDF on short questions is too sparse (1 of 554 pairs matched). Group the questions with the model or with embeddings, and audit a sample.

### Dashboard

* **Two tables at the top.** One row per lane: YouTube laptop lane, podcasts and creator files, publisher texts, speech-to-text, Haiku extraction, audit sample, human check. The first table says what each layer is and what it supports. The second gives its state: done, running, not done or refused. Model: `app/research/continuation/dashboard/round12-overview-scope.png`.
* **Counts only from receipts.** A missing receipt shows "pending". An empty cell shows "not recorded", never 0.
* **Per channel:** listed, over 5 minutes, selected, attempted, refused, downloaded, transcribed (source text and speech-to-text apart), analysed.
* **Text origin.** Every row says where its text came from. Tiles read "a + b", never a pooled total.
* **channels-ET figures, if shown at all.** They get their own column, labelled by route: "publisher feed", "converter-derived" or "paste-link-derived". First map their `person-<hash>` ids to our slugs.
* **A dataset manifest behind the page.** For each dataset: sha256, rows, date, and one line on what it is and is not. Model: `app/research/transcript-dashboard/inputs.json`. The builder stops on a mismatch. After each publish, read the page back and compare the hashes.
* **Rewrite `et-channelers/dashboard/qa/run.py`.** Today it only prints and checks nothing, and its path points at an old session's scratchpad. It should check:
  * widths 320, 390 and 1440, and 720 at device-pixel ratio 2;
  * no "NaN", "undefined" or "[object Object]" on the page;
  * exports equal the filtered rows;
  * empty states reached through the real controls;
  * the hashes of the files the page loaded.
* **Phone width.** Tables turn into cards, and the first screen shows data.

### Other parts of the roadmap

* **Phase 4b.** Replace the present text with part 6. It says their selection "already sets shorts and recordings under five minutes apart, as Phase 7a does", but in fact it drops them. It also says "119 checks"; the receipt says 121.
* **D4 and Phase 5** still say "5 min to 3 h", but Phase 7a says no upper limit. Align D4 with 7a.
* **`ANALYSIS_PLAN.md`** is linked from `et-channelers/ROADMAP.md` lines 19 and 333, `et-channelers/README.md` line 214, and `et-channelers/HANDOFF.md` lines 101 and 137. It is not in the repository or its history. Write it with the methods above, or fix the links.
* **Phase 2.** Calibrate on `pod-505525fbd6216f31`. Their `tiny.en` ran at 30 to 47 times real time on one thread (`app/research/acquisition-2026-11/asr-summary.json`).
* **Phase 3.** Our 949 digest rows came through youtubetotranscript.com, a paste-link page (`/workspaces/bashar-index/src/DIGEST_SPEC.md` line 4). Keep them as history only; our own transcripts replace them.
* **Phase 4.** List Lee Carroll's channel. Add the ids that pass the check.
* **Phase 6.** Their near-duplicate title families give candidate duplicates. The edition field, and matching by GUID plus transcript, handle podcast editions.
* **D1.** Only 3 of their 100 Bashar picks are on the official channel, so reposts dominate any count of "Bashar videos". Count each session once, by fingerprint.
* **Phase 7.** The crosswalk starts the identity audit (N1). Quote joint counts only for the 59 accounts matched by id, handle or route.
* **Enclosure queue.** Athina Król's "Ashtar Live Channelling" episode failed for them (their A18). Here it is `pod-87d6a64c14ef215a`, listed and queued (`<root>/jobs/queue_enclosures.csv`) but not yet fetched.

## 6. Roadmap section

The text below replaces the present Phase 4b of `et-channelers/ROADMAP.md` (438 words by `wc -w`).

```markdown
### Phase 4b: the Kimi agent's channels-ET snapshot (received 2026-11-14)

The owner shared "Kimi_Agent_YouTube ET Channel Analysis.zip": the channels-ET (Channeling Atlas) repository
as of 2026-11-14. It holds 2,275 files; 517 are newer than the clone read before. No audio or transcript text
is in it. Five agents read the new parts.

What it holds:
* an inventory of 2,840 YouTube videos on 302 accounts, and a selection of 733 that **drops** recordings
  under 300 s and caps Bashar at 100. Unlike Phase 7a, it does not study short recordings as a group;
* audio of 42 videos fetched through the y2mate.gs converter (2026-11-10), with 34 `tiny.en` transcripts and
  572 question units;
* subtitles of 12 of those videos from paste-link services;
* 12 Bashar interviews from the publishers' own feeds, with 715 question units;
* a 57-page draft paper, AI reviews and analysis code (121 checks).

**Provenance.** The converter audio and the subtitles were obtained by going around YouTube's refusal. We do
not use them, not even privately: none is in the zip, and the YouTube lane on the owner's computer can fetch
the same 43 videos. Their figures may be cited, labelled by route, apart from ours. The owner decides
(HANDOFF section 6.2).

Steps:
1. Copy their metadata tables and the readers' tables to `<root>/comparison/channels-et/`, with a sha256 per
   file.
2. Channels: put Lee Carroll's channel id in `sources/extra_channels.csv` and list the channel. Check and add
   six more ids for people we list without a channel. Record old routes as aliases.
3. New accounts: Calenara, Tracy Kumbera, Multidimensional Soul, OmNa and Christine Day go to
   `et-source-scout` first. 19 Bashar and 3 Kryon re-upload accounts and 10 interview shows join the host
   lists; an interview is fetched only when the entity speaks live.
4. Queue: with Lee Carroll listed, the laptop lane covers 33 of the 43 videos; the other 10 wait for steps 2
   and 3 and a twin check.
5. Methods: a language and broken-output check in `transcribe.py`; `pipeline/qa_units.py` (question units,
   six answer-window states, families of two or more content words); an edition field (exact, changed,
   failed) for enclosures; `tiny.en` against `base.en` on `pod-505525fbd6216f31`, held by both projects byte
   for byte.
6. Analysis: write the missing `ANALYSIS_PLAN.md` with their limits: no topic or cluster claim without seed
   stability and a shuffled baseline; names and adverts masked first; upload year apart from session year;
   their AI-review rates as priors for the 7c audit.

**Done when** the account decisions are in `plan/targets.csv` or the source tables, the comparison folder has
its hashes, `qa_units.py` and the language check pass their tests, and phases 7a and 7c cite what was taken
and what was refused.
```
