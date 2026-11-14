# Critique of the deep-research synthesis "Timelines, predictions and question banks", 2026-11-14
*The synthesis now lives in [ANALYSIS_PLAN.md, section 12](../../ANALYSIS_PLAN.md#12-timelines-predictions-and-question-banks-deep-research-2026-11-14), "Timelines, predictions and question banks (deep research, 2026-11-14)", revised after this critique.*

This is an adversarial review of the draft of that section, written by an agent on 2026-11-14. The figures it calls wrong are the draft's; section 12 carries the corrected ones. Private file locations are left out of this copy.

**How it was checked.** Against the private catalogue (73,921 rows), the audio manifest, the job queues, the pipeline code, ROADMAP.md and ANALYSIS_PLAN.md. All 41 links were fetched. The recount and simulation scripts (`works.py`, `works2.py`, `works3.py`, `twins.py`, `titledates.py`, `placebo_sim.py`) stayed in a private scratch folder.

## Verdict

The section does what the owner asked: every recording over 5 minutes, with no upper limit, and shorts kept apart. Its references are real. It is not workable yet, for five reasons:
- its route for YouTube dates breaks the robots.txt rule;
- "download and analyse everything" is not sized, and the code still limits long files;
- several figures count catalogue rows, not works, and the twin links are unreliable for 27% of Scranton's paired videos;
- the last-N test reads a steady drift as a recent change;
- the agent route cannot give structured output, exact model ids or blinding, and the human coding has no budget.

## A. The owner's request: everything over 5 minutes, no one-hour window

Confirmed:
- No queue limits length. All six queue meta files have minimum and maximum seconds at 0, and `too_short` and `too_long` at 0.
- 259 of the 1,138 held files run over 1 hour, and 6 over 3 hours. The longest is 6.7 hours.
- No download has ever timed out (0 of 1,646 manifest items).

What still limits length in practice:

1. `pipeline/download_audio.py`: the YouTube lane kills any yt-dlp or ffmpeg call after 3,600 s (the `--timeout` default). A timeout is filed as "network", retried from scratch twice, then recorded as an error. The listings include streams of up to 11.9 hours. Fix: a timeout of 600 s plus k times the expected duration, a separate "timeout" error class, and resumed downloads.
2. `pipeline/download_enclosures.py`: 1,800 s per item. That is too short for extracting audio from the 146 video-only sessions (529 GB). Fix: scale the timeout with file size.
3. `pipeline/select_episodes.py`: with `--max-hours` (80 hours per cycle), an item that would overflow the budget is skipped, and shorter ones keep filling it. So long episodes are put off cycle after cycle. Fix: stop at the first overflow, or reserve part of each cycle for the longest items waiting.
4. `pipeline/transcribe.py`:
   - `decode_audio` reads a whole file into memory (12 hours is about 2.8 GB of float32);
   - the Bashar pass hands out the longest files first, so on 8 GB two long sessions run at once;
   - `--order round-robin` is "shortest first", so long recordings are transcribed last and interim tables under-weight them.

   The draft's claim that long recordings are cut into chunks is not true of the code. Fix: decode and transcribe in 30-minute windows with overlap, and use the seeded order by person, year and length band that the draft proposes, with the seed in the manifest.
5. The plan documents still carry caps. The draft retires ROADMAP D4, but these remain:
   - ANALYSIS_PLAN D11 (50 long videos per channel);
   - section 5.5;
   - section 4.6, whose cost basis is "1,391 h capped at 50 per channel";
   - the `--per-channel 20` example in `select_jobs.py`.

   Retire them all, and recompute 4.6 for about 23,200 hours.
6. Archive.org files must be merged into sessions:
   - 27 part-files are 300 s or shorter and would fall into the short group one by one;
   - counted as sessions, 179 Bashar sessions run over 3 hours (769 h).

   Add a unit test for this.

## B. Rule breaches and compliance

7. **(High) robots.txt.** YouTube's robots.txt (fetched 2026-11-14) disallows `/youtubei/` and `/feeds/videos.xml` for every user agent. yt-dlp fetches channel-tab continuations and player data from `/youtubei/`. So the listings this plan rests on (`discover.py`), and its default for dates (read at home with yt-dlp), do not meet "robots.txt obeyed". Fix: the owner records one of two decisions in the roadmap:
   - a written, scoped exception for the YouTube lane; or
   - listings and dates through the YouTube Data API, the sanctioned route. `videos.list` takes 50 ids per 1-unit call, so the 58,699 listed ids cost about 1,200 units (the default quota is 10,000 a day). It works from the cloud, and it also gives `publishedAt`, `liveStreamingDetails`, `defaultAudioLanguage` and deletions.

   The policy's 30-day limit (III.E.4) reads "delete or refresh"; the draft leaves out "or refresh". A monthly refresh job complies.
8. **Quotes add up.** A checked quote of up to 30 words on every prediction card can copy a large share of short works: Scranton's posts have a median of about 600 words and often several predictions. Fix:
   - quote only one representative statement per family;
   - cap quotes per work (one quote, at most 5% of its words) and per channel;
   - the guard checks total overlap with the private texts.
9. **Paraphrases reach the public through family labels.** The draft keeps paraphrases private, but its public timelines name and colour families (for example "open contact begins"). Fix:
   - labels written by a person, neutral, at most 8 words;
   - no 5-word overlap with any transcript (an 8-word test can never fire on a label of 7 words or fewer);
   - the same floor as theme labels (10 items, 3 recordings).
10. **"Listen at 12:34" points at audio that only the private store holds** (media fragments). Fix:
    - public links go to the publisher's copy with its own time parameter (YouTube `t=`, the archive.org player), or show the time stamp only;
    - private links appear only on the owner's private page;
    - view links never encode private paths.
11. **Baroni 2012.** The page asks not to be quoted or reproduced without the author's consent. Its dated Bashar claims come from the 1990 book *Blueprint for Change*, not from a held recording. Fix: cite it as a pointer only, and apply the "must be found by the pipeline" check only to known predictions whose source recording is held.

## C. Numbers that are wrong or cannot be reproduced

12. The length figures count catalogue rows, not works:
    - "1-3 h hold 46%" is 45.6% of rows but 43.8% of works.
    - "128 items over 3 h, 562 h" counts rows. Under the draft's own rule (archive.org files merge into sessions) it is 299 works and about 1,300 hours.
    - "6,650 short videos and streams" counts YouTube rows only; 111 podcast episodes of 5 minutes or less are left out.
    - The draft's 43,092 main works could not be reproduced. Rows plus unpaired texts give 43,600 to 43,800; counted by work it is 45,515.

    Fix: one script and one unit (the work), with its output pinned in the plan.
13. **(High) Twin links.** 675 Scranton videos are each the "page-embed" twin of 2 to 4 posts, and in 674 of them the posts' dates differ: by a year or more in 610 cases, by up to 7 years. That is 1,379 rows. The "3,166 dated videos" are 3,166 page-video pairs covering 2,475 videos; only about 1,800 pairs are one-to-one. As a result:
    - a dated twin is not a safe date source;
    - collapsing twins merges different messages;
    - about 700 posts get the wrong duration;
    - the set used to score dates estimated from list order is contaminated.

    Fix: accept a twin only if it is one-to-one and passes a text-overlap check, and score date estimates on the one-to-one pairs. Scranton re-using a title for a new message is a repetition finding in its own right.
14. Dates:
    - "A fifth dated" depends on L/L's dates in the address. The catalogue's date field is empty for all 1,774 L/L texts; 1,669 of the 1,775 L/L pages carry `/channeling/YYYY/MMDD`. With catalogue dates alone, 16% of main works are dated (7,394 of 45,515). "First fill: L/L" needs a parser that the draft's step 1 does not list.
    - The draft's by-year tables from listings alone can only cover dated lanes. `discover.py` asks yt-dlp for approximate dates, but 0 of 58,699 rows came back with one.
15. **Dates in titles are ignored.** 2,771 YouTube main-corpus titles (7.7%) carry a full date: 67% of Mônica de Medeiros's titles, 76% of Elena Danaan's, 49% of Blossom Goodchild's, 37% of Jamie Butler's. Dated items in a tab's upload order also bracket the undated items between them. A bare year can be a target year ("2027"), so use full dates only, checked per channel, with EDTF precision.
16. Minor points:
    - The task's "903 Bashar sessions" are 903 files in 245 sessions (912 h).
    - Held audio is 1,138 files (819.5 h), not 1,055 (719 h).
    - Once the unit is fixed, the last-N qualifying counts come out close to the draft's: 62, 62, 56 and 42 people at N = 5, 10, 50 and 100, and 10, 8, 6 and 6 with text.

## D. Unworkable on this machine and budget as written

17. **(High) Size:**
    - The main corpus is about 23,200 hours of known length: about 21,000 h on YouTube and 3,100 h elsewhere. (Note added when filing: the two overlap, because some YouTube works have podcast or page twins, and the 3,100 h count the 146 video-only sessions, which are not in the catalogue.)
    - That is about 191 million words, and about 250 GB as 24 kbps Opus, against a 32 GB disk with 10 GB free.
    - base.en here runs at a median 5.9 times real time when idle and 1.3 times under load: about 164 days, or about 2 years.

    Fix: a resource table, with a calendar for each step:
    - the cloud CPU (or the 4-core machine) for the about 3,100 hours off YouTube, about 3 weeks idle;
    - the owner's computer, ideally with a GPU, for YouTube: large-v3 at the library's figure of about 46 times real time is about 500 GPU-hours (not measured);
    - private storage sized for about 250 GB.
18. **(High) Choose the engine and handle language before transcribing everything:**
    - base.en scored a word error rate of 0.729 on a 1981 tape (ANALYSIS_PLAN 10.1).
    - `keep_transcribing.sh` defaults to base.en with `--language en`.
    - Clearly non-English channels hold about 2,050 main items and 1,310 hours: Mônica de Medeiros (939 h, Portuguese), Elsa Farrús Rusiñol (267 h, Spanish), Pavlina Klemm (German, French, Czech), Channeler Junko (Japanese).

    Fix: settle D2 with a benchmark first, detect the language of each recording, use a multilingual model, analyse each language separately, and never pool rates across languages without calibration.
19. **(High) Agents as the bulk reader:**
    - Agents as run here return free text. Structured outputs is an API parameter (`output_config.format`) they cannot use.
    - The `haiku` alias records no exact model id (ANALYSIS_PLAN 4.5).
    - There is no batch discount; only two agents run at a time here, and they stop with the session.
    - At the measured rate (about 0.5 million words in 7 minutes, for a simpler task), one read of 190 million words takes at least 45 hours, and two reads at least 90.
    - Agents reading private files see the person and date in the file paths, so "the reader is not told the year" fails.

    The privacy reason given is not a real difference. Both routes send the text to Anthropic; 29 days is how long batch results stay downloadable. What differs is the account's data terms, which should be checked.

    Fix: the Message Batches API with `claude-haiku-5-5`, schema-constrained output, a control set in every batch and anonymised chunk ids; agents only for pilots and adjudication.

    Prices confirmed on the pricing page: Haiku 5.5 is $0.10 / $0.50 per million tokens up to 100k-token prompts ($0.50 / $2.50 above); batches are half price; Sonnet 5.5 is 20 times Haiku, and Opus 5.5 40 times.
20. **Sonnet "checks every candidate" in one place and "reads samples" in another** (the draft's sections 4 and 5). Channeled speech is full of the future tense, so expect about one candidate per 300 words. Over the full corpus that is about 600,000 candidates and roughly $900 to $1,800 of Sonnet (batch to standard), 10 to 20 times the Haiku pass. The source texts alone cost about $30 to $65. Haiku 5.5 also thinks by default (effort medium), which changes cost and output. Fix: Sonnet on every candidate in the source texts, and on a stratified sample plus low-confidence cases elsewhere; record the thinking setting.
21. **Human coding has no budget.** The draft implies:
    - three coders on 50 to 100 units for each of about six label families;
    - a 600-unit codebook gold set and 400 checked candidates;
    - 200 time expressions and 500 family pairs;
    - two-coder rulings on hits and misses.

    That is roughly 100 to 200 person-hours (ANALYSIS_PLAN 4.7 estimates about 205). The default coder is the owner alone (D5), which cannot run the alt-test (at least three annotators). Fix: name the coders and give their hours, pay and blinding, or report results only as "agreement with Opus".
22. **Tools:**
    - hierarchical GAMs need R and mgcv, and R is not installed;
    - HeidelTime needs Java and TreeTagger;
    - speaker roles from audio need diarization (pyannote, on a GPU).

    Fix: add them to the 4-core setup and the lockfile, or use tested Python substitutes.

## E. Statistically weak

23. **(High) The placebo windows read drift as change.** A simulation (`placebo_sim.py`, 22N recordings, no recent change) gives:
    - with a steady drift of 0.5 SD over the whole history, "last N against all earlier" gives p < .05 in 7.1% of runs at N = 10 and 13.1% at N = 50;
    - "against the N just before" stays at 4.5 to 4.8%;
    - autocorrelation (AR(1), rho 0.3) keeps both at or below 5%.

    Also, the first window has no history, so p < .05 needs 22N works, not 21N. Fix: make the headline contrast "against the N just before", or the residual from the GAM forecast, and keep "against all earlier" as description.
24. **The power figures** (1.25, 0.89, 0.40 and 0.28 SD) assume an infinite, independent reference group and a z-test:
    - the placebo test reaches about 75% power at those effects;
    - "against the N just before" needs 1.77, 1.25, 0.56 and 0.40;
    - autocorrelation raises both;
    - a block bootstrap inside 5 or 10 recordings means nothing.

    Fix: per-channel power by simulation on each channel's own series; at N = 5 and 10, report the value and its placebo percentile only.
25. **Calendar effects.** Two of Scranton's four newest main-corpus videos are about the 11/11 portal, so a last-5 window computed this week measures an annual date. Fix: a placebo from the same calendar window in earlier years, and a flag on windows that contain recurring dates (11/11, solstices, equinoxes, eclipses).
26. **Too many comparisons.** Four values of N, times the features, times about 63 people, times 2 text kinds, make thousands of contrasts, and "BH within groups" is not defined. Fix: name 3 to 5 primary features and apply BH across people within each feature and N, or pool across people for the latest-window effect.
27. **Merging sparse years.** Gries and Hilpert's method merges neighbouring periods by how similar their outcomes are, so merging and then testing is circular. Merge sparse years by a count rule fixed in advance. For the GAMs, the interval on the slope must be simultaneous, as in Simpson 2018, not pointwise.
28. **Weighting.** For means from partly transcribed years, use the Hájek ratio rather than Horvitz-Thompson. It needs recorded inclusion probabilities and an adjustment for non-response: failed downloads, failed transcripts, deleted videos.
29. **Receding deadlines:**
    - A fixed lead time makes deadlines recede by construction, so test the Theil-Sen slope against 1, not 0, and also analyse the lead time itself.
    - Restatements are not independent (the Index's own README says so of its P2 points). Use one point per family version, with a bootstrap clustered by family.
    - Open-ended targets ("by 2030") need interval or bounds methods.
30. **Correcting for model error:**
    - PPI corrects means. Trends and regressions on model labels need DSL, or PPI for coefficients.
    - Correcting by era or channel needs gold in each stratum, which 50 to 100 units per family cannot provide. State the transportability assumption and show bounds.
    - With 100 units, alpha is known only to about ±0.13, which cannot separate 0.667 from 0.80.
31. **Recall:**
    - Estimating recall needs gold drawn from text the rules did not flag.
    - Famous predictions are explicit and dated, so they are a smoke test, not a recall estimate.
    - The ledger was built from AI digests whose prompt examples (2027, 2033, 2050) became top "findings" (ANALYSIS_PLAN section 6).
32. **Preregistration:**
    - The source texts have already been profiled, and no split is named. Use the hash split and loader seal of ANALYSIS_PLAN 2.6.
    - "Hedging does not rise as deadlines near" is a null hypothesis: test it with TOST and a stated margin. It also contradicts the registered direction of B4.
    - "mid-2023" is not a date.
    - Only L/L and Kryon have dated text on both sides of 2012-12-21, so that test can only be within-channel.
33. **Denominators:**
    - Count rates per channeled word or minute, excluding intros, adverts, music and the medium's own talk.
    - Add a channeled share for each recording. Many tracked people mix channeling with teaching (Aaron Abke's ACIM lessons, meditations), and without it a change of format reads as a change of content.
    - Count each family once per recording.
    - Say whether the 5-minute rule applies to the whole recording or to the entity's turns: in interviews the channeled share has a median of 39% and a range of 8 to 70%.
34. **Survivorship:**
    - 6 of the Index's 75 recordings have left YouTube, and 1 is private.
    - `discover.py` overwrites each listing, so deleted videos leave no trace, and failed predictions may be the first to go.

    Fix:
    - keep first-seen and last-seen dates per id, with weekly diffs;
    - use earlier inventories: the 2026-10-23 crawl, channels-ET's 2,812 videos, Wayback captures;
    - show survival status on every timeline point.

## F. Missing, or inconsistent with the existing plan

35. **The order of work** contradicts the task's item 7 (the dashboard) and the freeze:
    - dashboard v1 is step 8, after everything is transcribed;
    - codebooks and preregistration (step 4) come after speech-to-text and after the listing-based tables.

    Suggested order:
    1. Owner decisions.
    2. Codebooks, preregistration and gold sampling frames.
    3. Dashboard v1 from the listings and dated texts: the coverage strip; last-N on duration, format and titles; per-year views for Scranton, L/L and Laarkmaa.
    4. Speech-to-text and reading in parallel, adding panels as the data arrive.
36. **Clashes with ANALYSIS_PLAN:**
    - 4,000-word chunks here, against 1,500-word windows (R1) and 200-word units (R2);
    - under 10 works here, against 20 in 5.15;
    - non-overlapping placebo windows here, against 10,000 consecutive windows in 5.15;
    - reading transcripts "as they arrive", against the single run, random batches and control sets of 4.5;
    - families per channel only, while the combined timeline needs event classes across channels (5.6).

    Say which sections this one replaces.
37. **Last-N ordering.** List order exists only within one YouTube tab. Videos and streams cannot be interleaved without dates, and dated lanes cannot be merged with undated tabs. Multi-part uploads (about 500 long items titled "part N", 135 titled "k of n") must be merged first.
38. **Small-model design:**
    - There is no development set: the gold "never tunes prompts", so nothing does.
    - Nothing bans example dates, names or years in prompts, and the priming and order-reversal checks of 4.4 are missing.
    - Refusals are not counted (Haiku 5.5 has no server-side fallback).
    - "Never quotes" conflicts with "drops strings it cannot find": spans should be sentence ids only, checked against the chunk.
    - Text versions should be pinned by hash (item ids were migrated once already).
    - Speaker roles in speech-to-text need diarization or validated boundaries (unitizing alpha).
39. **Prophecy literature and codes** (added from memory; verify before citing):
    - Festinger, Riecken and Schachter 1956; Melton 1985; Zygmunt 1970; Bader 1999; Dawson 1999.
    - Code how sources respond after a date passes: re-dating, spiritualizing, "the probable reality shifted" or free-will reframing, blame, denial, silence, deletion.
    - Treat 2012 as a natural experiment within L/L and Kryon.
40. **The survey of further analyses (the task's item 8) is thin,** and one item is mis-costed: titles against content needs YouTube transcripts, so it does not take seconds. Add:
    - voice and prosody of trance against the medium's own voice (unique to the audio, and possible on CPU for samples);
    - view counts (present in every listing row) against content;
    - commercial content: course and payment-plan promotions appear in Scranton's videos tab;
    - health and conspiracy content in warnings (Ward and Voas 2011);
    - event studies beyond the three fixed dates;
    - self-repetition within a channel;
    - general imposters (Koppel and Winter 2014) as the stylometric method for medium against being.
41. **Dashboard:**
    - carry the banner "claims are reported as claims", with uncertainty that lay readers can follow;
    - colour by family does not scale beyond about 8 families: label or facet instead;
    - a list view at 320 px;
    - Nielsen's article says 3 to 4 users per group when two groups are tested, so 6 to 8 per round for followers plus sceptics, not five.
42. **Owner decisions for step 0:** GPU, storage (about 250 GB), languages, the robots.txt and terms stance for YouTube metadata, coders and pay, the account's data terms, and deletion tracking.

## G. Link check (all 41 fetched on 2026-11-14)

All 41 resolve. The 26 DOIs were looked up in Crossref, and their titles, authors and years match. The other 15 pages answer HTTP 200. Pages were fetched with curl.

Not what is claimed, or needing a caveat:
- Nielsen 2000: recommends 3 to 4 users per group (item 41).
- Gries and Hilpert 2008: merges periods by similarity, not sparsity (item 27).
- YouTube developer policies: the rule is "delete or refresh" (item 7).
- Wahbeh and Glick 2026 (World Futures): "Semantic Structure and Correspondence in Prospective Trance-Channeled Communications Attributed to Extraterrestrial Intelligences". It studies correspondence of content, not style, so it is no stylometry precedent next to Burrows.
- The ledger link opens analysis/README.md, which describes a 164-row ledger built from digests (item 31).
- Baroni 2012: says what is claimed, but asks not to be quoted (item 11).
- Lopez Bernal 2017: an interrupted time series needs a fixed date (item 32).
- Liu et al. 2024: measured on 2023 models; a minor concern at chunks of about 7,000 tokens.

As claimed:
- Methods and statistics: Monroe 2008; Horvitz-Thompson 1952; Simpson 2018; Cliff 1993; Politis-Romano 1994; Sen 1968; Gneiting-Raftery 2007; Hayes-Krippendorff 2007; Webber 2013; Angelopoulos 2023; Lijffijt 2016; Pedersen 2019; Benjamini-Hochberg 1995; Nosek 2018; Steegen 2016; Spiegelhalter 2005; Burrows 2002; Barron 2018; Morris 2023.
- Language and time: FactBank; TimeML; HeidelTime; EDTF; Broder 1997.
- Prophecy and probability words: Kent 1964 (Sherman Kent's CIA paper); Tumminia 1998.
- Annotation: Calderon 2025 (at least three annotators, 50 to 100 items, confirmed).
- Claude documentation: structured outputs; pricing (Haiku 5.5 figures confirmed).
- Display and standards: the NSIDC chart (median with interquartile and interdecile bands); Media Fragments; WCAG 2.2.
- Catalogues: SIMBAD (Wenger 2000).

## Status when this note was filed

Added on 2026-11-14 when the note was filed; not part of the review.
- Section 12 of ANALYSIS_PLAN.md carries most of these fixes. Where it still overstated a point, it now says "Corrected after the critique".
- The plan's D11 and 5.15 and the caps in 4.6 and 5.5 are retired there, and 4.6 is recomputed for the whole main corpus.
- The main counts were rechecked against the catalogue at about 07:40 UTC with the review's rule, and they hold: 45,515 main works, about 23,200 h of known length, 7,647 works of unknown length, 22,858 short works, 7,394 works dated (16%), 42 people (6 with text) with at least 200 main works, and 3 people (1 with text) with at least 2,200.
- Links added to section 12 after this review were checked the same day. The DOIs of Dawson 1999, Lakens 2017, Koppel and Winter 2014 and Ward and Voas 2011 resolve to the cited titles. The DSL preprint and the YouTube quota page answer HTTP 200. googleapis.com, which serves the Data API, has no robots.txt.
- Still open in the code until step 1 of section 12.10: the limits in items 1 to 4, and the `--per-channel 20` example in `select_jobs.py` (item 5).
