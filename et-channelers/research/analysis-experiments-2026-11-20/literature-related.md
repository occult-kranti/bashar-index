# Methods digest from related venues, for the analysis panel

Date: 2026-11-20. Scope: CSCW, The Web Conference, ACL / EMNLP / TACL, Interspeech / ICASSP, Journal of Quantitative Description: Digital Media (JQD:DM), EPJ Data Science, PNAS, Science Advances, political-methodology and communication-methods journals, sociology of religion and new religious movements, and the statistics papers these fields lean on. ICWSM itself is left to the companion review.

## 0. How to read this file

- Section 1 gives corpus facts measured today that decide which methods fit.
- Section 2 holds the method cards. Each card states the question, the statistic or model, the standard figure or table, the pitfalls, what it means for this corpus, and the sources.
- Section 3 turns the cards into 20 concrete experiments with their plots and tables.
- Section 4 lists what the search did not find. Section 5 is the reference list.

**Checking of sources.** 98 references are listed. Each carries one of four marks:

| Mark | Meaning | Count |
|---|---|---|
| opened | The page or paper was fetched and read in this session | 11 |
| search | Title, authors, year, venue and abstract-level content were confirmed by a search result in this session; full text not read | 79 |
| partial | Found in search, but one bibliographic field or the title was not confirmed | 5 |
| unverified | Recalled, not found or not opened | 3 |

Numbers quoted from a paper come only from "opened" pages or from the search result's abstract text. Where I add something from memory it says "(recalled)". All searches used general research terms; no transcript text, creator name or project name left this machine.

## 1. Corpus facts that decide which methods fit

Read-only measurements made today. Scripts and output: `lit_related_sample_pass.py` and `lit_related_sample_pass.json` in this folder.

**Size and clustering.**
- The run proposal lists 1,976 rows from 101 creators. Recordings per creator: minimum 2, median 20, maximum 20.
- The manifest held 1,218 finished transcripts when read: 1,206 English from 90 creators (510.2 hours), 4 Japanese from 2 creators, 3 Spanish from 1 creator, 3 Portuguese from 1 creator, 2 Czech from 1 creator. Non-English so far: 12 recordings, 5 creators, 3.3 hours.

**How the text was made** (settings read from 204 of the ZIP files, every sixth one).
- All 204 used beam size 5, temperature 0 with no fallback, `condition_on_previous_text` off, voice-activity filtering on with a 500 ms minimum silence, and word time stamps on.
- Model by language, over all 1,239 ZIP files present at the time: 1,216 English recordings on the distilled large-v3 model, 10 English recordings on the full large-v3 model, and all 13 non-English recordings (4 Japanese, 3 Czech, 3 Portuguese, 3 Spanish) on the full large-v3 model. So every non-English transcript and 99% of English transcripts come from two different models. The 10 English recordings on the full model are the only bridge between them.
- The English view of a non-English recording comes from the recognizer's own `translate` task (speech straight to English text). It is not a text translation of the original transcript.
- `speaker_identity` is "unassigned" in all 204. There is no speaker separation.

**Sample pass.** 118 English recordings, 4 from each of 30 creators drawn at random from the 71 English creators with at least 4 finished transcripts; 400,136 words; 1.7 seconds of compute.

| Per-recording measure | 10th pct | Median | 90th pct | Max |
|---|---|---|---|---|
| Length, minutes | 3.9 | 16.8 | 57.9 | 149.0 |
| Words | 498 | 2,393 | 8,063 | 25,743 |
| Share of audio without speech | 0.9% | 4.4% | 22.2% | 55.1% |
| Words per minute of detected speech | 120 | 154 | 177 | 215 |
| Words per minute of whole audio | 98 | 144 | 172 | 194 |
| Median segment log-probability | -0.167 | -0.123 | -0.098 | -0.075 |
| Share of segments with log-probability below -1.0 | 0 | 0 | 0.2% | 1.7% |
| Share of segments with compression ratio above 2.4 | 0 | 0 | 0 | 65% |
| Share of words with word probability below 0.5 | 0.7% | 1.2% | 2.7% | 17.3% |
| Gaps of 0.2 s or more per 100 words | 7.2 | 9.9 | 13.7 | 23.2 |
| Median length of those gaps, seconds | 0.42 | 0.52 | 0.85 | 3.23 |
| Gaps of 2 s or more per 1,000 words | 0 | 1.9 | 24.0 | 156.3 |
| Question marks per 1,000 words | 0 | 3.5 | 10.3 | 51.3 |

Other counts from the same sample: 29 of 118 recordings have at least one segment whose text repeats the segment before it; 8 of 118 contain a stock sign-off phrase of the kind the recognizer is known to invent on silence (it can also be real speech; position decides).

**How much of each measure belongs to the creator.** One-way intraclass correlation (ICC), 30 creators with 4 recordings each. These are rough: the intervals on an ICC from 30 groups of 4 are wide.

| Measure | ICC | Design effect at 20 recordings per creator | Effective number of recordings out of 1,946 |
|---|---|---|---|
| Words per minute of detected speech | 0.42 | 9.0 | about 215 |
| Words per minute of whole audio | 0.32 | 7.1 | about 275 |
| Question marks per 1,000 words | 0.22 | 5.1 | about 380 |
| Share of audio without speech | 0.18 | 4.4 | about 445 |
| Gaps per 100 words | 0.16 | 3.9 | about 495 |
| Median segment log-probability | 0.05 | 1.9 | about 1,050 |

Design effect = 1 + (m - 1) x ICC, with m = 20.

**What follows from these facts.**
1. The unit of inference is the creator, about 100 of them. For style and timing measures 1,946 recordings carry the information of roughly 200 to 500 independent ones.
2. A "language" comparison has 1 or 2 creators per language. It cannot separate language from creator, and it is also confounded with the recognizer model (distilled against full) and with translation. Section 2 D4 and K1.
3. The stock threshold of -1.0 on segment log-probability flags almost nothing here (90th percentile of the flagged share is 0.2%). Quality gates must be set from this corpus's own distribution.
4. About half of the recordings have fewer than 2,400 words and about three quarters fewer than 4,200. Per-recording stylometry is below the sample sizes the stylometry literature treats as safe (G2).
5. With no speaker separation, question-and-answer structure has to be recovered from text and timing, or a separation pass has to be added later.

## 2. Method cards

### A. Spoken content and automatic transcripts

**A1. Do recognition errors move the numbers we report?**
- *Question.* Would a word count, topic share or scaling result change if the transcript were perfect?
- *Statistic or model.* (a) A gold subsample: human-corrected transcripts for a stratified set of recordings, with word error rate (WER) and with each downstream measure computed on both versions; report the paired difference and the correlation. (b) Error simulation: inject substitutions, deletions and insertions at set rates into clean text and re-estimate. Proksch, Wratil and Wäckerle call this WERSIM and ship it in R. Fetic et al. did the same for LDA topics on podcast transcripts and tracked the cosine similarity between topic vectors and the creators' own descriptions as noise rose.
- *Standard figure or table.* A line plot: injected error rate on the x axis, agreement with the clean-text result on the y axis (rank correlation of topic shares, share of top-50 key terms retained), one line per measure. A table of WER by stratum.
- *Pitfalls.* Uniform random noise is not how a recognizer fails: Fetic et al. found topics much more robust to realistic recognizer-style noise than to uniform noise. Errors concentrate in rare words, which are the proper nouns and coined terms this corpus is about. Su et al. found that different noise types affect different topic models differently, so the test has to be run on the model actually used. Automated WER against professional transcripts overstates error because professional transcripts drop disfluencies: SPoRC measured 8 to 9% automated WER per show but 3.0% on manual review of 18 episodes.
- *Here.* Draw substitution candidates from the words the recognizer itself was unsure about (word probability below 0.5: 1.2% of words at the median, 17% at worst), not from the whole vocabulary. Run every registered claim at 0, 5, 10 and 20% injected error.
- *Sources.* [R1] [R6] [R7] [R8].

**A2. Invented text on music, silence and meditation.**
- *Question.* How much transcript text was never spoken?
- *Statistic or model.* Rate of invented segments per hour of non-speech audio. Barański et al. ran the full large-v3 model on 301,317 clips with no speech: 40.3% produced text; 9.1% of those looped; two phrases made up about 35% of all inventions and the top ten more than half (thanks, sign-offs, caption credits). Koenecke et al. found invented phrases in about 1.4% of 13,140 speech segments, more often where the share of non-vocal audio was higher (logistic coefficient 0.951, SE 0.438).
- *Standard figure or table.* A table of the most frequent invented strings with counts; a bar chart of error rate under each mitigation. In Barański et al. WER on speech mixed with noise went from 104.8% with no mitigation to 8.0% with Silero voice-activity filtering and 6.5% when a phrase blacklist and de-looping were added.
- *Pitfalls.* Koenecke et al. found inventions by running the same audio twice and comparing; identical inventions in both runs go uncounted. WER alone hides them. Creators really do say sign-off phrases, so a blacklist removes true speech unless position is checked. A compression-ratio flag also fires on real chanting, mantras and repeated affirmations.
- *Here.* Voice-activity filtering was on for every sampled file (the library's filter is Silero-based; recalled), which is the strongest mitigation in Barański et al. The distilled model is reported by its authors to hallucinate less on long audio. Remaining risk sits in the 10% of recordings with more than 22% non-speech audio. Flag a segment when it (i) matches a stock phrase, (ii) starts within a few seconds after a quiet stretch of 30 s or more (the provenance file lists these stretches), or (iii) repeats the previous segment. Hand-check a sample of flags and report precision. One sampled recording has 65% of its segments above the compression-ratio threshold; decide by listening whether that is a loop or a chant.
- *Sources.* [R2] [R3] [R11] [R12].

**A3. Names of beings, places and people.**
- *Question.* Can entity counts and name networks be trusted on transcripts?
- *Statistic or model.* Entity-level precision and recall against hand annotation, by entity type, reported separately for names in and out of the recognizer's vocabulary.
- *Standard figure or table.* An error taxonomy table (wrong span, split entity, wrong spelling, missed) with the share of each.
- *Pitfalls.* Szymański et al. report that entity recognizers fail badly on spontaneous speech even when the recognizer made no word errors, because spoken text lacks the structure the models were trained on, and that F1 is a poor summary there. Coined names get many spellings.
- *Here.* Do not run a general entity recognizer and count. Build a closed list of being and place names with spelling variants per creator (the plan's lexicon), match by sound-alike variants, and validate against 200 hand-checked mentions. Report name counts with and without low-probability words.
- *Sources.* [R4].

**A4. Word-list measures on speech.**
- *Question.* Does an emotion or certainty word list measure the same thing in speech as in writing?
- *Pitfalls.* Sun et al. recorded 185 people in daily life and found that word-list emotion scores computed on their speech were not significantly related to the emotions they reported. Chan et al. ran 37 off-the-shelf sentiment scores over one news corpus and reached different conclusions depending on which was used.
- *Here.* Treat any word-list score as a description of vocabulary, not of state or intent. One list per construct, fixed before looking, validated on this corpus (card M).
- *Sources.* [R20] [R86].

**A5. Reference pipelines for spoken corpora.**
- SPoRC [R8]: 1.1 million podcast transcripts; base English recognizer with word time stamps; speaker turns on 370,000 episodes (word-level speaker error 2.1% for two-person shows); pitch and spectral features averaged per word; host and guest names by entity recognition plus a classifier (0.88 test accuracy); LDA with 200 topics on the first 1,000 words; guest network of 10,480 shows and 26,589 links. A repetition filter removed about 11% of episodes.
- RadioTalk [R10]: 2.8 billion words from 284,000 hours of talk radio with speaker turn boundaries; published with an explicit statement that transcription error is present.
- Pew sermons [R15]: 49,719 sermons from 6,431 churches over 8 weeks; a classifier removed files that were not sermons; the report states the sample is not representative and that the tools cannot always separate the sermon from the rest of the service. Median length differed by tradition (54 against 14 minutes).
- Boussalis, Coan and Holman [R17]: over 110,000 sermons; politics in more than a third; shares reported both per sermon and per pastor (over 70% of pastors).
- Pew health influencers 2026 [R16]: 535,512 posts from 6,334 influencers; speech detected then transcribed with a diarizing model; a small language model coded 13 topics; two coders on 250 posts (at least 88% agreement, kappa at least 0.6), validation set of 600 posts, model F1 at least 0.6 on every label; only the first five minutes of each long video were transcribed.
- Brookings podcasts [R18]: 36,603 episodes from 79 shows; transcripts matched against a database of fact-checked claims, then hand review; the authors say the design undercounts.
- Tarr, Hwang and Imai [R14]: machine coding of campaign videos checked against an existing human-coded archive. It matched people well on issue and opponent mentions, slightly less well on negativity, and worst on the mood of background music, a variable on which human coders also disagree. The lesson: machine-against-human agreement is bounded by human-against-human agreement, so measure both.
- *Use.* These fix the reporting standard: state the recognizer, the validation sample, per-label agreement, both per-item and per-creator shares, and what part of each recording was read.

### B. Timing: speech rate, pauses and what time stamps support

**B1. Speech rate.**
- *Question.* How fast does a creator speak, and does it change between own voice and channelled voice, or between monologue and question time?
- *Statistic.* Words (better: syllables) per minute of detected speech, per recording and per segment; a mixed model with segment within recording within creator.
- *Standard figure.* Ridge or violin plot by creator, ordered by median; a slope chart for within-creator contrasts.
- *Evidence.* Reddy et al. found that podcast advice to speak slowly was contradicted by engagement data. Wahbeh et al. had 13 trance channels read the same story in both states: reading took 56.0 s against 38.2 s for one story and 67.3 s against 36.8 s for the other (F(1,51) = 15.44, p = 0.0006), Slower delivery was the clearest behavioural difference in that study; voice spectral power also differed in some bands, while EEG, heart and breathing measures showed no difference after correction.
- *Pitfalls.* Words per minute depends on word length, so it is not comparable across languages; use syllables or characters and state which. Rate over whole audio mixes speaking speed with silence (median 144 against 154 here). The recognizer drops fillers and false starts, which lowers measured rate for disfluent speakers. Rate is 42% creator in this corpus, so recordings are not independent.
- *Sources.* [R9] [R44].

**B2. Pause profile.**
- *Question.* Where are the silences, how long are they, and do they mark meditation, entry into trance or turn changes?
- *Statistic.* Gaps between consecutive word time stamps: count per 100 words above a threshold, median length, share of time, and the count of long gaps (2 s or more). Model gap lengths on the log scale.
- *Standard figure.* A histogram of log gap length per creator; a timeline strip per recording showing speech and silence; a heatmap of creators by pause measures.
- *Pitfalls.* The threshold is a convention. Search results showed 0.2 s in a 2026 dialogue-system paper and 0.15 s in a clinical study, where a stop consonant's closure can be miscounted as a pause; neither paper was opened (section 4). Imprecise word boundaries create spurious and missed pauses. Voice-activity filtering with a 500 ms floor shapes which silences survive.
- *Here.* Report at two thresholds (0.2 s and 0.5 s). Long-gap rate ranges from 0 to 156 per 1,000 words, which by itself separates meditations from talk.
- *Sources.* [R5] [R2].

**B3. What word time stamps can carry.**
- *Evidence.* Rousso et al. compared a classical forced aligner with two recognizer-based aligners on hand-aligned speech. Share of word boundaries within 50 ms: 89.4% classical, 82.4% and 75.7% recognizer-based on read speech; on conversational speech 84.9% against 67.4% and 75.0%. Median boundary error 12 to 14 ms classical, 23 to 30 ms recognizer-based. Only correctly recognized words were scored.
- *Rule.* Use time stamps for measures at 100 ms resolution and coarser (rate, pauses of 0.2 s and up, position in recording). Do not use them for segment durations of single sounds or for rhythm measures that need 20 ms accuracy. Time stamps in this corpus come from the recognizer's own attention weights, not from a separate forced aligner (recalled from the library's design), so expect the weaker end of these figures or worse.
- *Sources.* [R5].

**B4. Pitch and voice quality.**
- Not available from transcripts. SPoRC extracted pitch, first formant and four spectral coefficients per word with an open toolkit. Knox and Lucas model tone of voice in court hearings and show it carries information that text models miss. Wahbeh et al. found spectral power differences between states in fixed bands. This needs a pass over the audio and is out of scope while the transcription worker runs.
- *Sources.* [R8] [R13] [R44].

### C. Long monologue and question-and-answer structure

**C1. Parts of a recording.**
- *Question.* What share of a recording is opening, teaching, questions, meditation and close, and does content differ by part?
- *Statistic.* A segment-type label per time window from timing and text features, validated by hand; then every content measure reported by part.
- *Standard figure.* A stacked bar per creator (share of time by part); a recording-by-position heatmap.
- *Pitfalls.* Pew states its tools could not always isolate the sermon from the rest of the service. Without speaker separation, a questioner who is off-microphone may be missing from the transcript entirely.
- *Sources.* [R15] [R8].

**C2. Questions.**
- *Question.* What kinds of questions do audiences ask, and do different voices get different kinds?
- *Statistic or model.* Zhang, Spirling and Danescu-Niculescu-Mizil find recurring surface patterns in questions without supervision and group them by the kind of answer they draw; they applied it to parliamentary question sessions and related question types to the asker's role.
- *Standard figure or table.* A table of question types with example patterns and shares; a heatmap of question type by creator or by asker role.
- *Pitfalls.* Question marks in a transcript are placed by the recognizer (median 3.5 per 1,000 words here, up to 51). Rhetorical questions by the speaker and audience questions read back by the host look alike.
- *Here.* Validate question detection on 200 hand-labelled sentences before any typology. Separate audience questions from the speaker's own.
- *Sources.* [R22].

**C3. Conversation-level models.**
- Althoff, Clark and Leskovec analysed about 80,000 text counselling conversations with sequence models of conversation stages, language-model comparisons, message clustering and word-frequency contrasts, and related strategies to outcomes. The reusable parts are the stage model (how a session progresses) and the practice of comparing the same counsellor across conversations. Their outcome analysis does not transfer: this corpus has no outcome.
- *Sources.* [R21].

**C4. Position profiles.**
- *Statistic.* Cut each recording into equal shares of its length and compute a measure per share. Reagan et al. slid a window through 1,327 stories and decomposed the sentiment curves into six basic shapes by matrix decomposition and clustering. Boyd, Blackburn and Pennebaker profiled function-word categories across about 40,000 narratives and found three processes (staging, plot progression, cognitive tension), with a different profile for factual texts.
- *Standard figure.* Mean curve with a band across recordings; a heatmap of recordings by position bin, rows clustered.
- *Pitfalls.* Smoothing windows manufacture smooth arcs. Recordings of 4 minutes and of 150 minutes do not have comparable positions; stratify by length class.
- *Sources.* [R64] [R65].

### D. Comparing languages through machine translation

**D1. Is translated text good enough for counting and topic models?**
- *Evidence.* De Vries, Schoonvelde and Schumacher compared human and machine translation of parliamentary speeches: term-document matrices were highly similar and LDA gave similar topic prevalence and content, with small differences by language. Lucas et al. set out the workflow of translating into one language and fitting a structural topic model. Maier et al. compared machine translation with a multilingual dictionary on English, Hebrew and Arabic: both recovered a large share of equivalent topics in news, with systematic differences on informal text.
- *Pitfalls.* All three used written, formal or edited text and a text translation system. Here the English view is speech translation by the recognizer, so recognition and translation errors are fused and cannot be told apart, and the source is spontaneous speech with coined terms. None of the three was confirmed to cover Japanese; the language sets were only confirmed for Maier et al.
- *Standard table.* For a bilingual check sample: correlation of term frequencies and of topic shares between two routes to English.
- *Here.* For a sample of non-English recordings make a second English version by translating the original-language transcript with a text system, and compare the two English versions on every measure reported. Report measures only where the two routes agree.
- *Sources.* [R23] [R24] [R25].

**D2. Translation artifacts.**
- *Evidence.* Vanmassenhove, Shterionov and Gwilliam measured a loss of lexical and morphological richness in the output of every translation system they tested, for two language pairs. Volansky, Ordan and Wintner show that classifiers separate translated from original text from features of simplification, explicitation and interference.
- *Consequence.* Lexical diversity, vocabulary size, rare-word rates, sentence length and function-word profiles of a translated English view are not comparable with native English transcripts. A translated creator will look simpler and more standard than they are.
- *Here.* Compare lexical measures only within the original language. McCarthy and Jarvis found MTLD to be the one diversity index that does not vary with text length; use it, not type-token ratio.
- *Sources.* [R27] [R28] [R66].

**D3. Multilingual sentence vectors instead of translation.**
- Licht found classifiers on multilingual sentence embeddings at least as reliable as translate-then-count when labelled data are scarce (20,000 sentences or fewer). For topic or theme assignment across languages, embed the original-language segments and the English segments in one multilingual space and compare there, with the translated view as a cross-check.
- *Sources.* [R26].

**D4. Design limits.**
- Language is carried by 1 or 2 creators each, uses a different recognizer model, and passes through translation. Three confounds, none removable by statistics. State any language result as a description of named creators. Language-free measures (share of audio without speech, pause profile, recording length, position profiles, and rate in syllables) are the only ones that compare cleanly.

### E. Prophecy, prediction and failed prediction

**E1. What counts as a prediction and whether it can be scored.**
- *Model.* A ledger with one row per dated or datable statement: source recording, time stamp, date said, claim, target date or window, specificity, stated certainty, and a verifiability class.
- *Evidence on classes.* The Great Australian Psychic Prediction Project scored more than 3,800 published predictions by 207 people into five classes: correct about 11%, wrong about 53%, too vague about 18%, expected (would happen anyway) about 15%, unknown about 2%. Reports differ by a point on some shares. It is a skeptics' society project, not peer-reviewed; how scorers were assigned and whether they were blind to the source was not retrieved.
- *Standard figure.* A stacked bar of classes per source; a table of the scoring rules with examples.
- *Pitfalls.* Most statements fall outside "correct or wrong". The "expected" class needs a base rate, which is a judgement. Scorers who know the source drift. One coder's ruling is not a measurement: use two coders blind to creator and report agreement per class.
- *Sources.* [R39].

**E2. Scoring rules.**
- *Statistic.* Where a statement carries a probability or a graded certainty, use a strictly proper score. Brier's score is the mean squared difference between stated probability and outcome; Murphy split it into reliability, resolution and uncertainty. Gneiting and Raftery give the general theory and the logarithmic, quadratic and spherical scores, plus an interval score for stated ranges.
- *Standard figure.* A calibration plot (stated probability against observed frequency) and a discrimination curve. Mandel and Barnes did this for 1,514 intelligence forecasts with Brier decomposition, ROC analysis and logistic calibration curves.
- *Pitfalls.* Channelled predictions rarely state probabilities. Mapping words to numbers is itself a model: Friedman et al., on 888,328 forecasts, show that coarsening numbers into verbal categories loses accuracy, so the reverse mapping adds noise that must be reported. With no probabilities, report hit rates against a stated base rate and stop there.
- *Sources.* [R33] [R34] [R35] [R36].

**E3. Certainty language.**
- *Evidence.* Zong, Ritter and Hovy predicted forecasters' skill from the language of their justifications alone. Pei and Jurgens annotated 2,167 statements for certainty and found hedge words explain only part of perceived certainty; they model it at sentence level and per aspect of the statement.
- *Here.* Code certainty per prediction with a rubric, not a hedge-word count. Then test whether stated certainty relates to specificity and to outcome class.
- *Sources.* [R37] [R38].

**E4. What happens after a date passes.**
- *Evidence.* Dawson reviewed the case studies after the classic 1956 study and tabulated how groups respond: spiritualizing the event, calling it a test of faith, blaming human error, blaming others, with social support and decisive leadership as conditions. Melton argued earlier that failure rarely destroys a group and that spiritualization and reaffirmation are the normal course. Kelly's 2025 archival paper argues the 1956 study reported its group selectively and that its leader had recanted in 1955. A 2021 report on an online conspiracy movement found content and engagement at pre-failure levels after missed dates and date-shifting as the most common response; it is a qualitative reading.
- *Statistic.* For each prediction whose date falls inside the collected window, code later mentions with Dawson's categories; count restatements with a moved date.
- *Standard table.* Prediction by response type, with counts per creator.
- *Pitfalls.* The corpus holds only the newest 20 or so recordings per creator, so most predictions and their follow-ups fall outside it. Deleted recordings are missing by design: survivorship.
- *Sources.* [R30] [R31] [R32] [R40].

### F. Channelling, new-age, conspirituality and wellness research

**F1. Prior quantitative work on channelled content.**
- Wahbeh and Glick (2026): three experienced channelers, standard interviews over 28 topic areas, sentence embeddings. Reported correspondence 0.65 to 0.79 across channelers for the same named being and 0.75 to 0.88 within a channeler across different beings after residualization. The page read does not name the similarity measure, a control condition or a permutation test. My reading: on these figures the channeler accounts for at least as much similarity as the named being, which is the comparison experiment 9 below should make with proper controls.
- Wahbeh et al. (2019): 13 trance channels, within-person design; slower reading and voice spectral differences in the channelled state; no EEG, heart or breathing differences after correction.
- Anastasia et al. (2020): hand-coded content from the same 13: seven themes in three groups (research method, how channelling works, personal and philosophical messages). An earlier study from the same group is cited as reporting five themes, among them the nature of reality, multi-dimensional beings and the need to awaken humanity [R54].
- *Use.* These give a theme list to test for recurrence, a design (same questions to different voices), and a warning: published work in this area comes mostly from one institute with small samples and no outside controls.
- *Sources.* [R43] [R44] [R45] [R54].

**F2. Conspirituality as a measurable construct.**
- Ward and Voas define it by two convictions: a secret group controls the political and social order, and humanity is undergoing a shift in consciousness. Asprem and Dyrendal argue the mix is old and expected in this milieu.
- Samory and Mitra extract agent, action and target triples from statements, cluster them into narrative motifs, and count motifs over 6 million comments from more than 200,000 users.
- Miani, Hills and Bangerter compare conspiracy and non-conspiracy texts about the same events: conspiracy texts are more interconnected and cover more topics, with lower cohesion inside a text and higher cohesion across texts.
- *Statistic.* Motif counts per creator; number of distinct themes linked within one recording; cohesion within a recording against similarity across recordings.
- *Standard figure.* A bipartite heatmap of creators by motifs; a scatter of within-recording cohesion against cross-recording similarity.
- *Pitfalls.* The triple extractor was built for written forum posts. Miani et al. rely on matched non-conspiracy texts about the same events; this corpus has no such matched control, so only between-creator contrasts are available.
- *Sources.* [R41] [R42] [R47] [R48].

**F3. Influencer ecosystems.**
- O'Brien, Ganjigunta and Dhillon: 161 wellness influencers against controls; 20% of on-topic posts pro-vaccination (614 of 3,045) against 42%; account-level classification beside post-level shares; topic models for themes.
- McGrady et al. drew a random sample of 10,000 videos from the whole platform to estimate what the platform holds; it shows how unrepresentative any creator-first sample is and gives platform baselines (for example the share of videos in English).
- Baker (2022) is the qualitative account of wellness influencers and conspiracy content during the pandemic; it supplies concepts, not measures.
- *Use.* Report at both item and creator level. State plainly that the corpus is a purposive set of creators and the newest recordings of each, not a sample of a population.
- *Sources.* [R46] [R51] [R52].

**F4. Comparing religious discourses.**
- Stine, Deitrick and Agarwal compare 14 online communities on religion and spirituality three ways: word frequencies, topic-model usage patterns, and topic models refit after removing each community's most distinguishing words. The third step separates deep resemblance from shared jargon.
- A 2020 study in the sociology of religion fitted a structural topic model to 255 religion-and-spirituality questionnaires published from 1929 to 2017 and tracked which topics rose and fell. It is the closest example found of a topic model over time in that field, and it is on survey instruments, not on speech.
- *Here.* Refit creator comparisons after masking being names and each creator's signature terms. The plan already lists name masking; this is its published precedent.
- *Sources.* [R49] [R50].

### G. Stylometry and consistency of voice

**G1. Same voice or different voice.**
- *Question.* Is a channelled voice stylistically distinct from the channeler's own voice, and is one named being consistent across recordings?
- *Statistic or model.* Treat it as verification: given two samples, same speaker or not. Report the area under the curve and equal-error rate with a bootstrap over recordings. Aggazzotti, Andrews and Smith built such a benchmark on speech transcripts and found that text models do reasonably well until topic is controlled, when performance drops; transcription style also changes results.
- *Standard figure.* Score distributions for same and different pairs; a table by difficulty level (topic controlled or not).
- *Pitfalls.* Topic leaks into style. A being who always talks about one subject will look stylistically distinct for that reason alone. Recognizer normalization (no fillers, model-chosen punctuation) removes the cues that mark spoken style.
- *Sources.* [R19].

**G2. How much text is needed.**
- Eder found a minimum sample of about 5,000 running words for stable attribution, later lowered to under 2,000 for some settings, and the threshold varies by language and genre.
- *Here.* Median recording 2,393 words. Pool by creator and voice, or use rolling windows of fixed size over concatenated text. Cafiero and Camps used a rolling analysis over a prophetic online text against profiles of 13 candidate writers and reported a change of author over time.
- *Standard figure.* A rolling plot: position in the text on the x axis, classifier score on the y axis, one line per candidate.
- *Sources.* [R55] [R57].

**G3. A closed candidate set always names someone.**
- The dispute over a 19th-century scripture is the lesson. Jockers, Witten and Criddle attributed chapters among a fixed set of candidates. Schaalje et al. replied that the method must pick one of the candidates even when the true author is absent, and proposed an open-set version. The first paper also needed a correction for a preprocessing error involving dashes.
- *Rule.* Any "voice A resembles voice B" result needs a none-of-the-above option and distractor speakers. Preprocessing choices go into the specification curve.
- *Sources.* [R56].

**G4. Translation and style.**
- Rybicki reports that a standard distance measure usually groups literary translations by original author, not by translator. That was human literary translation. Combined with D2 it does not license stylometry on the recognizer's English view.
- *Sources.* [R29].

### H. Text reuse and near-duplicates across sources

**H1. Phrase clusters.**
- Leskovec, Backstrom and Kleinberg tracked short quoted phrases and their variants across 90 million articles, clustering variants by graph partitioning, and measured the lag between outlets (about 2.5 hours between news and blogs).
- *Statistic.* Clusters of near-identical phrases of 8 or more words; first use by date; number of creators using each.
- *Standard figure.* Stacked timeline of the top phrase clusters; a creator-by-creator matrix of shared clusters.
- *Sources.* [R58].

**H2. Local alignment.**
- Wilkerson, Smith and Stramp trace policy ideas by finding aligned passages between bills, then filter boilerplate (method details recalled; the search confirmed only that it is a text-reuse design). Local alignment tolerates inserted and changed words, which shingling does not, and that tolerance is what recognizer noise needs.
- *Pitfalls.* The largest reuse is a creator's own opening and closing formula. Remove within-creator reuse first. Shared scripture or shared source-text quotations are common ancestors, not borrowing between creators.
- *Sources.* [R59].

**H3. Novelty, transience, resonance.**
- Barron et al. score each speech by how much its topic mixture departs from the speeches before it (novelty) and after it (transience), using information divergence over LDA mixtures; speeches that are new and then persist mark innovators. The term "resonance" for novelty minus transience is recalled, not confirmed in the search text.
- *Standard figure.* Scatter of novelty against transience with one point per speaker.
- *Pitfalls.* Needs a time-ordered stream. With 20 recent recordings per creator the windows are short and the dates span different periods per creator.
- *Sources.* [R60].

**H4. Vocabulary life cycles.**
- Danescu-Niculescu-Mizil et al. show members of online communities adopt new community language early and stop adapting later. Applied here: date of first use of each coined term per creator, to see who adopts whose vocabulary.
- *Sources.* [R61].

### I. Showing how two bodies of text differ

**I1. Word shift graphs.** Gallagher et al.: any difference in a weighted average (a word-list score, entropy, a divergence) is broken down into per-word contributions and drawn as a ranked horizontal bar chart. Use one for every headline contrast so readers see which words drive it. [R62]

**I2. Rank comparison.** Dodds et al.: rank-turbulence divergence compares two ranked lists with a tunable weight on rare against common items, drawn as a rank-rank histogram with the most divergent words listed. It does not need equal sample sizes. [R63]

**I3. Lexical diversity.** MTLD, as in D2. [R66]

*Pitfall for all three.* They describe; they carry no uncertainty by themselves. Put a creator-level bootstrap around any number taken from them.

### J. Topic shares are compositions

**J1. Log-ratio transforms.**
- *Problem.* Topic shares per recording sum to 1. A rise in one share forces falls in others. Aitchison's 1982 paper sets out the remedy: analyse logs of ratios. Gloor et al. make the case for data with an arbitrary total. Greenacre and co-authors' 2023 reappraisal reviews 40 years of the approach.
- *Statistic.* Centred log-ratio: log of each share minus the mean log share of the recording. Then ordinary multivariate methods.
- *Standard figure.* A compositional biplot (Aitchison and Greenacre): creators as points, topics as rays; the link between two rays shows the log-ratio of those two topics.
- *Pitfalls.* Zeros have no logarithm. Topic-model shares are never exactly zero but lexicon-based shares often are; a replacement rule is then an analysis choice and belongs in the specification curve. A 2023 preprint argues for modelling on the original scale with logit-type quasi-likelihood because it is stable with zeros.
- *Sources.* [R67] [R68] [R69] [R70] [R76].

**J2. Do not correlate shares.**
- Lovell et al. show that correlation between relative abundances can give the opposite sign from correlation between absolute amounts, and propose a proportionality statistic. A topic-by-topic correlation heatmap of raw shares is therefore unsafe; compute it on centred log-ratios or use proportionality.
- *Sources.* [R71].

**J3. Models for shares with creators as groups.**
- Dirichlet regression for several shares and Beta regression for one share, with dispersion, zero-and-one inflation and random effects (Douma and Weedon's guide).
- Dirichlet-multinomial regression inside the topic model: the prior over a document's topics is a function of document features (Mimno and McCallum).
- Logistic-normal topic models allow topics to correlate (Blei and Lafferty); the structural topic model makes prevalence a function of covariates (Roberts, Stewart and Airoldi).
- Schulze et al. point out that regressing estimated shares on covariates ignores that shares are estimates; they draw shares from the posterior repeatedly and use Beta regression in a fully Bayesian fit.
- *Standard table.* Coefficients as ratios of shares with intervals; a plot of fitted share by group with intervals.
- *Pitfall.* None of these has a creator random effect by default. Add one, or aggregate to creator first.
- *Sources.* [R72] [R73] [R74] [R75] [R77].

**J4. Variance partition.**
- Nakagawa, Johnson and Schielzeth give R-squared and the intraclass correlation for generalized mixed models, including non-Gaussian outcomes. Report for every measure the share of variance between creators, between recordings within a creator, and within recordings. Section 1 shows why: for speech rate 42% is creator.
- *Sources.* [R78].

### K. Inference when groups have few creators

**K1. Few clusters.**
- Cameron, Gelbach and Miller: ordinary cluster-robust tests reject too often with 5 to 30 clusters; a wild cluster bootstrap of the t statistic restores the nominal rate in their simulations. MacKinnon, Nielsen and Webb give a full practice guide. Pustejovsky and Tipton give a small-sample correction with Satterthwaite degrees of freedom.
- *Here.* About 100 creators overall is enough for creator-level bootstraps. Subgroups are the issue: an entity family or a format with 5 to 10 creators needs the wild bootstrap or the corrected estimator and should report the effective degrees of freedom. A language with 1 creator allows no test: place that creator as a percentile among the 90 English creators, where the smallest attainable permutation p-value is 1/91 = 0.011. With 2 creators there are 4,186 ways to pick 2 of 92, so the floor is 0.00024, but the two are then treated as a group they may not form.
- *Sources.* [R79] [R80] [R81].

**K2. Multilevel models with few groups.**
- Elff et al.: with few upper-level units, estimate variances by restricted maximum likelihood and use a t distribution with suitable degrees of freedom; then likelihood methods are unbiased and tests are accurate. Gelman: for a Bayesian fit use a half-t prior on the group standard deviation when groups are few; a flat prior needs at least 3 groups to give a proper posterior (threshold as given in secondary summaries).
- *Sources.* [R82] [R83].

**K3. What the result generalizes to.**
- Yarkoni: a model generalizes only over factors entered as random. Creators, recordings, topics and question prompts are all sampled; if only creators are random, a claim about "channelled speech" is really a claim about these recordings on these topics.
- *Sources.* [R84].

**K4. Power and tests in language research.**
- Card et al. show typical comparisons in language processing are underpowered and give simulation notebooks. Dror et al. survey which test fits which measure and find testing often missing or misapplied.
- *Here.* For each registered contrast run a simulation with the section 1 ICCs to state the smallest detectable difference before looking at the result.
- *Sources.* [R88] [R89].

### L. Robustness and registration

**L1. Multiverse with judgement.** Del Giudice and Gangestad: a multiverse can bury a real effect under poorly justified alternatives. Classify each choice as principled equivalence (include all), principled non-equivalence (pick the right one and say why), or uncertainty (include and treat as exploratory). The plan's specification curve should carry this label per choice. [R87]

**L2. Many analysts.** Breznau et al.: 73 teams, same data, same hypothesis; results ranged widely and more than 95% of the variance stayed unexplained after coding every identifiable decision. A specification curve covers listed choices only; say so. [R85]

**L3. Word lists as a garden of forking paths.** Chan et al.: 37 sentiment scores, one corpus, different conclusions. One list per construct, chosen before the analysis. [R86]

**L4. Registration and description.** Van Miltenburg, van der Lee and Krahmer propose registration questions for language studies of different kinds. Munger, Guess and Hargittai argue that careful description is a publishable aim in itself. Most of what this corpus supports is description; register the few tests and label the rest as description. [R90] [R53]

### M. Validity of machine-coded measures

**M1. Construct before code.** Jacobs and Wallach: a construct is not observable; a measurement model links it to observables; most harms come from the mismatch. Write down for each coded construct (prediction, own voice, question, meditation) what would count as a failure of the measure. [R92]

**M2. Validate in this corpus.** Grimmer and Stewart: automated methods are wrong models of language and must be validated in each application. Song et al. simulate what happens when the human "gold" labels are themselves poor: the risk of misjudging the automated method rises sharply. A unified validation framework for text measures is proposed in the ValiTex preprint. [R91] [R94] [R95]

**M3. Correct for misclassification.** TeBlunthuis, Hase and Chan reviewed 48 studies using supervised classifiers and found misclassification bias mostly ignored; errors bias regression in either direction; a validation sample plus a correction model fixes it. This complements the prediction-powered and design-based estimators already in the plan. [R93]

**M4. Reporting template.** The Pew 2026 methodology [R16] is the current public standard: codebook, two coders on 250 items, per-label agreement and kappa, validation set of 600, per-label F1, stated limits. Match or exceed it per label and per creator group.

## 3. Experiments, plots and tables this literature supports

Unit of inference is the creator unless stated. "Cost" is compute: low = seconds to minutes on text already held; model = needs a language model or embedding pass; audio = needs the audio again.

| # | Question | Plot or table | Statistic | Sources | Cost |
|---|---|---|---|---|---|
| 1 | Do headline results survive recognition error? | Line plot: injected error 0/5/10/20% against agreement with the unperturbed result, one line per claim | Rank correlation of topic shares; share of top key terms kept | R1 R6 R7 | low |
| 2 | Do term rates depend on recognizer confidence? | Scatter: rate of each key term in high- against low-confidence segments, creator-relative terciles | Log rate ratio with creator bootstrap | R4 | low |
| 3 | How much text was invented on silence or music? | Table of flagged strings; heatmap of creators by flag type (stock phrase after quiet stretch, repeated segment, high compression) | Flags per hour of non-speech audio; precision from a hand check | R2 R3 | low |
| 4 | Timing atlas | Clustered heatmap of creators by speech rate, pause rate, median pause, long-pause rate, non-speech share; ridge plot of rate | z-scores; ICC table as in section 1 | R8 R9 R44 | low |
| 5 | Shape of a recording | Heatmap of recordings by 20 position bins for rate, pauses, question density and topic share; cluster rows | Mean curves with bands; matrix decomposition | R64 R65 | low |
| 6 | Parts of a recording | Stacked bars: share of time in talk, questions, meditation, close | Timing-and-text classifier; confusion matrix on 200 hand-labelled windows | R15 R8 | low |
| 7 | Kinds of questions | Table of question types; heatmap of type by creator | Pattern clustering; validated detection first | R22 | model |
| 8 | Is a voice consistent and distinct? | Score distributions for same and different pairs; rolling plot along pooled text | AUC by level of topic control; rolling distance on function words | R19 R55 R57 R56 | low |
| 9 | Named being or channeler: which carries the similarity? | Paired dot plot: within-creator-across-voice against across-creator-same-voice similarity | Permutation over recordings; names masked | R43 R49 | model |
| 10 | Who shares phrases with whom? | Creator-by-creator matrix of shared phrase clusters; timeline of top clusters | Aligned passages of 8+ words after removing within-creator formulas | R58 R59 | low |
| 11 | Who introduces and who repeats? | Scatter of novelty against transience per creator | Divergence of topic mixture from earlier and later recordings | R60 R61 | low |
| 12 | Which words drive each contrast? | Word shift graph per headline contrast; rank-rank plot for creator pairs | Per-word contributions; rank-turbulence divergence | R62 R63 | low |
| 13 | Topic structure without closure artifacts | Compositional biplot of creators and topics; proportionality heatmap in place of a correlation heatmap | Centred log-ratio PCA; proportionality | R67 R70 R71 | low |
| 14 | Topic shares by group with creators as random | Fitted shares with intervals by format or family | Dirichlet or Beta mixed regression; shares drawn from the posterior | R72 R75 R77 | low |
| 15 | Where the variance sits | Table per measure: between creators, between recordings, within; design effect; effective n | Mixed-model ICC | R78 | low |
| 16 | Prediction ledger | Stacked bar of verifiability classes per creator; calibration plot only where certainty is graded | Two blind coders; agreement per class; hit rate against stated base rate; proper score where possible | R33 to R39 | model plus people |
| 17 | After the date passes | Table of prediction by response type | Dawson's categories; count of moved dates | R30 R31 | people |
| 18 | Language panel, descriptive | Each non-English creator as a marked point on the English creators' distribution, language-free measures only | Percentile among 90; no test | R79 R23 R27 | low |
| 19 | Translation check | Scatter of term rates and topic shares, recognizer English against text-translated English | Correlation; list of measures that fail | R23 R25 R27 | model |
| 20 | Robustness and validity tables | Specification curve with each choice labelled equivalent, non-equivalent or uncertain; per-label validation table | Share of specifications supporting each claim; agreement, kappa, F1, corrected estimate | R85 R87 R16 R93 | low |

Experiments 1 to 6, 8, 10 to 15 and 18 need only the transcripts and time stamps already on disk.

A note for experiment 18. Recognizer confidence values and word rates cannot be compared between the distilled and the full model without a bridge. The 10 English recordings already transcribed with the full model give a first look at the size of the model difference. A designed bridge (the same 30 English recordings through both models) would settle it; it needs the GPU and so waits until the transcription run is over.

## 4. What the search did not find

- No computational study that scores predictions from a prophetic or channelling source and follows engagement after failure. The nearest are a qualitative think-tank report and survey work.
- No published stylometric comparison of a channeler's trance speech with the same person's ordinary speech. Experiment 8 would be new.
- No study validating the recognizer's direct speech-to-English output for word counts or topic models. The translation evidence (D1) is all for text systems on written text.
- No per-language error table for the recognizer covering Japanese, Czech, Portuguese and Spanish was retrieved. Search results note that Japanese is reported as character error rate, so it is not comparable with the others in any case.
- The numeric results of Proksch et al. and of de Vries et al. were not retrieved (pages closed or unreadable); only their abstracts are relied on.
- The stock decoding thresholds (-1.0, 2.4, 0.6) were seen on a third-party model page, not confirmed in the recognizer paper.
- Pause-threshold conventions (0.15 s, 0.2 s) come from search snippets of papers not opened; treat as conventions, not findings.
- Quantitative text work in the sociology of new religious movements is thin: forum comparisons and a topic model of survey instruments were found, no corpus study of spoken new-age content.

## 5. References

Mark after each entry: opened, search, partial or unverified (section 0).

**Spoken content and automatic transcripts**
- [R1] Proksch, Wratil, Wäckerle. Testing the Validity of Automatic Speech Recognition for Political Text Analysis. 2019. Political Analysis 27(3):339-360. https://www.cambridge.org/core/product/E375085D96331A47E810C01AA6DB0A46 (search; abstract page opened)
- [R2] Koenecke, Choi, Mei, Schellmann, Sloane. Careless Whisper: Speech-to-Text Hallucination Harms. 2024. ACM FAccT. https://arxiv.org/abs/2402.08021 (opened)
- [R3] Barański et al. Investigation of Whisper ASR Hallucinations Induced by Non-Speech Audio. 2025. ICASSP. https://arxiv.org/abs/2501.11378 (opened)
- [R4] Szymański et al. Why Aren't We NER Yet? Artifacts of ASR Errors in Named Entity Recognition in Spontaneous Speech Transcripts. 2023. ACL. https://aclanthology.org/2023.acl-long.98 (opened, abstract page)
- [R5] Rousso, Cohen, Keshet, Chodroff. Tradition or Innovation: A Comparison of Modern ASR Methods for Forced Alignment. 2024. Interspeech. https://arxiv.org/abs/2406.19363 (opened)
- [R6] Fetic, Jordahn, Lima, Egebæk, Nielsen, Biering, Hansen. Topic Model Robustness to Automatic Speech Recognition Errors in Podcast Transcripts. 2021. arXiv 2109.12306. https://arxiv.org/abs/2109.12306 (opened, abstract; uniform-versus-realistic noise finding from search text)
- [R7] Su, Boydell, Greene, Lynch. Topic Stability over Noisy Sources. 2015. arXiv 1508.01067; a copy appears in the ACL Anthology as W16-3913, venue not confirmed. https://arxiv.org/abs/1508.01067 (opened, abstract)
- [R8] Litterer, Jurgens, Card. Mapping the Podcast Ecosystem with the Structured Podcast Research Corpus. 2025. ACL. https://aclanthology.org/2025.acl-long.1222 (opened, arXiv HTML)
- [R9] Reddy, Lazarova, Yu, Jones. Modeling Language Usage and Listener Engagement in Podcasts. 2021. ACL. https://aclanthology.org/2021.acl-long.52 (search)
- [R10] Beeferman, Brannon, Roy. RadioTalk: A Large-Scale Corpus of Talk Radio Transcripts. 2019. Interspeech. https://arxiv.org/abs/1907.07073 (search)
- [R11] Radford et al. Robust Speech Recognition via Large-Scale Weak Supervision. 2023. ICML (PMLR 202). https://proceedings.mlr.press/v202/radford23a.html (search; thresholds not confirmed in the paper)
- [R12] Gandhi, von Platen, Rush. Distil-Whisper: Robust Knowledge Distillation via Large-Scale Pseudo Labelling. 2023. arXiv 2311.00430. https://arxiv.org/abs/2311.00430 (search)
- [R13] Knox, Lucas. A Dynamic Model of Speech for the Social Sciences. 2021. American Political Science Review 115(2):649-666. https://dcknox.github.io/files/KnoxLucas_DynamicModelSpeech.pdf (search)
- [R14] Tarr, Hwang, Imai. Automated Coding of Political Campaign Advertisement Videos: An Empirical Validation Study. 2023. Political Analysis 31(4):554-574. https://imai.fas.harvard.edu/research/campvideo.html (search)
- [R15] Pew Research Center. The Digital Pulpit: A Nationwide Analysis of Online Sermons. 2019. Report. https://www.pewresearch.org/religion/2019/12/16/the-digital-pulpit-a-nationwide-analysis-of-online-sermons/ (search)
- [R16] Pew Research Center. What Do Health and Wellness Influencers Post About? Methodology. 7 October 2026. Report. https://www.pewresearch.org/data-labs/2026/10/07/health-influencers-methodology/ (opened)
- [R17] Boussalis, Coan, Holman. Political Speech in Religious Sermons. 2021. Politics and Religion 14(2):241-268. https://ore.exeter.ac.uk/repository/handle/10871/40061 (search)
- [R18] Wirtschafter. Audible Reckoning: How Top Political Podcasters Spread Unsubstantiated and False Claims. 2023. Brookings Institution report. https://www.brookings.edu/essay/audible-reckoning-how-top-political-podcasters-spread-unsubstantiated-and-false-claims/ (search)
- [R19] Aggazzotti, Andrews, Smith. Can Authorship Attribution Models Distinguish Speakers in Speech Transcripts? 2024. TACL 12:875-891. https://aclanthology.org/2024.tacl-1.49 (search)
- [R20] Sun, Schwartz, Son, Kern, Vazire. The Language of Well-Being: Tracking Fluctuations in Emotion Experience Through Everyday Speech. 2020. Journal of Personality and Social Psychology 118(2):364-387. https://doi.org/10.1037/pspp0000244 (search)
- [R21] Althoff, Clark, Leskovec. Large-scale Analysis of Counseling Conversations. 2016. TACL 4:463-476. https://aclanthology.org/Q16-1033/ (search)
- [R22] Zhang, Spirling, Danescu-Niculescu-Mizil. Asking Too Much? The Rhetorical Role of Questions in Political Discourse. 2017. EMNLP. https://aclanthology.org/D17-1164/ (search)

**Languages and translation**
- [R23] de Vries, Schoonvelde, Schumacher. No Longer Lost in Translation: Evidence that Google Translate Works for Comparative Bag-of-Words Text Applications. 2018. Political Analysis 26:417-430. https://www.cambridge.org/core/product/43CB03805973BB8AD567F7AE50E72CA6 (search)
- [R24] Lucas, Nielsen, Roberts, Stewart, Storer, Tingley. Computer-Assisted Text Analysis for Comparative Politics. 2015. Political Analysis 23(2):254-277. https://www.mit.edu/~rnielsen/pa2015_corrected.pdf (search)
- [R25] Maier, Baden, Stoltenberg, De Vries-Kedem, Waldherr. Machine Translation vs. Multilingual Dictionaries: Assessing Two Strategies for the Topic Modeling of Multilingual Text Collections. 2022. Communication Methods and Measures 16(1):19-38. https://refubium.fu-berlin.de/handle/fub188/32510 (search)
- [R26] Licht. Cross-Lingual Classification of Political Texts Using Multilingual Sentence Embeddings. 2023. Political Analysis 31(3):366-379. https://www.cambridge.org/core/journals/political-analysis/article/crosslingual-classification-of-political-texts-using-multilingual-sentence-embeddings/30689C8798F097EEBA514ABE4891A71B (search)
- [R27] Vanmassenhove, Shterionov, Gwilliam. Machine Translationese: Effects of Algorithmic Bias on Linguistic Complexity in Machine Translation. 2021. EACL. https://aclanthology.org/2021.eacl-main.188 (search)
- [R28] Volansky, Ordan, Wintner. On the Features of Translationese. 2015. Digital Scholarship in the Humanities 30(1):98-118. https://cris.haifa.ac.il/en/publications/on-the-features-of-translationese/ (search)
- [R29] Rybicki. The Great Mystery of the (Almost) Invisible Translator: Stylometry in Translation. 2012. In Oakes and Ji (eds), Quantitative Methods in Corpus-Based Translation Studies, Benjamins, 231-248. https://ruj.uj.edu.pl/xmlui/handle/item/19905 (search)

**Prophecy, prediction, forecasting**
- [R30] Dawson. When Prophecy Fails and Faith Persists: A Theoretical Overview. 1999. Nova Religio (starts p. 60; full page range not confirmed). https://gwern.net/doc/sociology/1999-dawson.pdf (search)
- [R31] Melton. Spiritualization and Reaffirmation: What Really Happens When Prophecy Fails. 1985. American Studies 26(2):17-29. https://journals.ku.edu/amsj/issue/view/200 (search)
- [R32] Kelly. Debunking "When Prophecy Fails". Online 2025, issue 2026. Journal of the History of the Behavioral Sciences 62(1):e70043. https://doi.org/10.1002/jhbs.70043 (search)
- [R33] Gneiting, Raftery. Strictly Proper Scoring Rules, Prediction, and Estimation. 2007. Journal of the American Statistical Association 102(477):359-378. https://doi.org/10.1198/016214506000001437 (search)
- [R34] Brier. Verification of Forecasts Expressed in Terms of Probability. 1950. Monthly Weather Review 78:1-3. Murphy. A New Vector Partition of the Probability Score. 1973. Journal of Applied Meteorology 12:595-600. https://www.wpc.ncep.noaa.gov/research/amsver/tsld018.htm (search, via secondary reference lists)
- [R35] Mandel, Barnes. Accuracy of Forecasts in Strategic Intelligence. 2014. PNAS. https://doi.org/10.1073/pnas.1406138111 (search)
- [R36] Friedman, Baker, Mellers, Tetlock, Zeckhauser. The Value of Precision in Probability Assessment: Evidence from a Large-Scale Geopolitical Forecasting Tournament. 2018. International Studies Quarterly 62:410-422. https://doi.org/10.1093/isq/sqx078 (search)
- [R37] Zong, Ritter, Hovy. Measuring Forecasting Skill from Text. 2020. ACL. https://aclanthology.org/2020.acl-main.473 (search)
- [R38] Pei, Jurgens. Measuring Sentence-Level and Aspect-Level (Un)certainty in Science Communications. 2021. EMNLP. https://aclanthology.org/2021.emnlp-main.784 (search)
- [R39] Australian Skeptics. The Great Australian Psychic Prediction Project. 2021. Society report, not peer-reviewed. https://www.skeptics.com.au/psychic-project-full-results-released/ (search; primary page refused the fetch)
- [R40] Global Network on Extremism and Technology. How QAnon Reacts to Failed Predictions. 2021. Think-tank report. https://gnet-research.org/2021/03/31/how-qanon-reacts-to-failed-predictions/ (search)
- Festinger, Riecken, Schachter. When Prophecy Fails. 1956. Book. (unverified; discussed by R30 to R32)

**Channelling, new age, conspirituality, wellness, religion**
- [R41] Ward, Voas. The Emergence of Conspirituality. 2011. Journal of Contemporary Religion 26(1):103-121. https://repository.essex.ac.uk/7980/ (search)
- [R42] Asprem, Dyrendal. Conspirituality Reconsidered: How Surprising and How New Is the Confluence of Spirituality and Conspiracy Theory? Journal of Contemporary Religion. Year recalled as 2015. https://intersections.ssrc.org/citations/conspirituality-reconsidered-how-surprising-and-how-new-is-the-confluence-of-spirituality-and-conspiracy-theory/ (partial)
- [R43] Wahbeh, Glick. Semantic Structure and Correspondence in Prospective Trance-Channeled Communications Attributed to Extraterrestrial Intelligences. 2026. The Journal of New Paradigm Research. https://doi.org/10.1080/02604027.2026.2656120 (opened, institute summary page; full paper not read)
- [R44] Wahbeh, Cannard, Okonsky, Delorme. A Physiological Examination of Perceived Incorporation During Trance. 2019. F1000Research 8:67. https://f1000research.com/articles/8-67/v2 (opened)
- [R45] Anastasia, Wahbeh, Delorme, Okonsky. A Qualitative Exploratory Analysis of Channeled Content. 2020. EXPLORE 16(4):231-236. https://noetic.org/publication/a-mixed-methods-phenomenological-and-exploratory-study-of-channeling/ (search; the URL is the institute's related-publication page)
- [R46] O'Brien, Ganjigunta, Dhillon. Wellness Influencer Responses to COVID-19 Vaccines on Social Media: A Longitudinal Observational Study. 2024. Journal of Medical Internet Research 26:e56651. https://www.jmir.org/2024/1/e56651 (search)
- [R47] Miani, Hills, Bangerter. Interconnectedness and (In)coherence as a Signature of Conspiracy Worldviews. 2022. Science Advances 8(43):eabq3668. https://pmc.ncbi.nlm.nih.gov/articles/PMC9604529 (search)
- [R48] Samory, Mitra. "The Government Spies Using Our Webcams": The Language of Conspiracy Theories in Online Discussions. 2018. Proceedings of the ACM on Human-Computer Interaction 2 (CSCW), article 152. https://par.nsf.gov/servlets/purl/10082961 (search)
- [R49] Stine, Deitrick, Agarwal. Using Information Divergence to Differentiate Deep from Superficial Resemblances among Discourses. 2021. Culture and Computing, HCI International 2021. https://zacharykstine.github.io/files/stine_deitrick_agarwal_c&c_2021.pdf (search; PDF not readable)
- [R50] Dimensions of Religion and Spirituality: A Longitudinal Topic Modeling Approach. 2020. Journal for the Scientific Study of Religion. Authors not retrieved. https://doi.org/10.1111/jssr.12639 (partial)
- [R51] McGrady, Zheng, Curran, Baumgartner, Zuckerman. Dialing for Videos: A Random Sample of YouTube. 2023. Journal of Quantitative Description: Digital Media 3. https://journalqd.org/article/view/4066 (search)
- [R52] Baker. Article on alternative-health influencers and conspiracy content during the pandemic. 2022. European Journal of Cultural Studies. Exact title not confirmed. https://openaccess.city.ac.uk/27089/ (partial)
- [R53] Munger, Guess, Hargittai. Quantitative Description of Digital Media: A Modest Proposal to Disrupt Academic Publishing. 2021. Journal of Quantitative Description: Digital Media 1. https://journalqd.org/issue/view/vol2021 (search)
- [R54] Wahbeh, Carpenter, Radin. Earlier mixed-methods study of channelling reporting five themes. 2018. Title not confirmed. (partial; mentioned in a search result only)

**Stylometry, reuse, change**
- [R55] Eder. Does Size Matter? Authorship Attribution, Small Samples, Big Problem. 2015. Digital Scholarship in the Humanities (formerly Literary and Linguistic Computing). https://doi.org/10.1093/llc/fqt066 (search)
- [R56] Jockers, Witten, Criddle. Reassessing Authorship of the Book of Mormon Using Delta and Nearest Shrunken Centroid Classification. 2008. Literary and Linguistic Computing. https://doi.org/10.1093/llc/fqn040. Reply: Schaalje, Fields, Roper, Snow. Extended Nearest Shrunken Centroid Classification: A New Method for Open-Set Authorship Attribution of Texts of Varying Sizes. 2011. Literary and Linguistic Computing 26(1):71-88. https://purl.stanford.edu/rs276tc2764 (search; the secondary sources describing the dispute are partisan)
- [R57] Cafiero, Camps. Who Could Be Behind QAnon? Authorship Attribution with Supervised Machine-Learning. 2023. Digital Scholarship in the Humanities 38(4):1418-1430. https://arxiv.org/abs/2303.02078 (search)
- [R58] Leskovec, Backstrom, Kleinberg. Meme-Tracking and the Dynamics of the News Cycle. 2009. KDD, 497-506. https://doi.org/10.1145/1557019.1557077 (search)
- [R59] Wilkerson, Smith, Stramp. Tracing the Flow of Policy Ideas in Legislatures: A Text Reuse Approach. 2015. American Journal of Political Science 59(4):943-956. https://ccs.neu.edu/home/dasmith/wilkerson-smith-stramp-AJPS.pdf (search; "local alignment" is recalled)
- [R60] Barron, Huang, Spang, DeDeo. Individuals, Institutions, and Innovation in the Debates of the French Revolution. 2018. PNAS 115(18):4607-4612. https://pmc.ncbi.nlm.nih.gov/articles/PMC5939074 (search)
- [R61] Danescu-Niculescu-Mizil, West, Jurafsky, Leskovec, Potts. No Country for Old Members: User Lifecycle and Linguistic Change in Online Communities. 2013. WWW, 307-318. https://doi.org/10.1145/2488388.2488416 (search)
- [R62] Gallagher, Frank, Mitchell, Schwartz, Reagan, Danforth, Dodds. Generalized Word Shift Graphs: A Method for Visualizing and Explaining Pairwise Comparisons Between Texts. 2021. EPJ Data Science 10:4. https://epjdatascience.springeropen.com/articles/10.1140/epjds/s13688-021-00260-3 (search)
- [R63] Dodds et al. Allotaxonometry and Rank-Turbulence Divergence: A Universal Instrument for Comparing Complex Systems. 2023. EPJ Data Science 12:37. https://doi.org/10.1140/epjds/s13688-023-00400-x (search)
- [R64] Reagan, Mitchell, Kiley, Danforth, Dodds. The Emotional Arcs of Stories Are Dominated by Six Basic Shapes. 2016. EPJ Data Science 5. https://doi.org/10.1140/epjds/s13688-016-0093-1 (search)
- [R65] Boyd, Blackburn, Pennebaker. The Narrative Arc: Revealing Core Narrative Structures Through Text Analysis. 2020. Science Advances 6(32):eaba2196. https://pmc.ncbi.nlm.nih.gov/articles/PMC7413736 (search)
- [R66] McCarthy, Jarvis. MTLD, vocd-D, and HD-D: A Validation Study of Sophisticated Approaches to Lexical Diversity Assessment. 2010. Behavior Research Methods 42(2):381-392. https://doi.org/10.3758/BRM.42.2.381 (search)

**Compositions and hierarchical models**
- [R67] Aitchison. The Statistical Analysis of Compositional Data. 1982. Journal of the Royal Statistical Society B 44(2):139-160 (some sources give 139-177). https://doi.org/10.1111/j.2517-6161.1982.tb01195.x (search)
- [R68] Gloor, Macklaim, Pawlowsky-Glahn, Egozcue. Microbiome Datasets Are Compositional: And This Is Not Optional. 2017. Frontiers in Microbiology 8:2224. https://pmc.ncbi.nlm.nih.gov/articles/PMC5695134 (search)
- [R69] Greenacre et al. Aitchison's Compositional Data Analysis 40 Years On: A Reappraisal. 2023. Statistical Science. https://www.projecteuclid.org/journals/statistical-science/advance-publication/Aitchisons-Compositional-Data-Analysis-40-Years-on-A-Reappraisal/10.1214/22-STS880.full (search). Also Greenacre, review in Annual Review of Statistics and Its Application, 2021, title not confirmed (partial)
- [R70] Aitchison, Greenacre. Biplots of Compositional Data. 2002. Journal of the Royal Statistical Society C 51(4):375-392. https://doi.org/10.1111/1467-9876.00275 (search)
- [R71] Lovell, Pawlowsky-Glahn, Egozcue, Marguerat, Bähler. Proportionality: A Valid Alternative to Correlation for Relative Data. 2015. PLoS Computational Biology 11(3):e1004075. https://pmc.ncbi.nlm.nih.gov/articles/PMC4361748 (search)
- [R72] Douma, Weedon. Analysing Continuous Proportions in Ecology and Evolution: A Practical Introduction to Beta and Dirichlet Regression. 2019. Methods in Ecology and Evolution 10(9):1412-1430. https://doi.org/10.1111/2041-210x.13234 (search)
- [R73] Mimno, McCallum. Topic Models Conditioned on Arbitrary Features with Dirichlet-Multinomial Regression. 2008. UAI, 411-418. https://proceedings.mlr.press/r6/mimno08a.html (search)
- [R74] Blei, Lafferty. A Correlated Topic Model of Science. 2007. Annals of Applied Statistics 1(1):17-35. https://doi.org/10.1214/07-AOAS114 (search)
- [R75] Roberts, Stewart, Airoldi. A Model of Text for Experimentation in the Social Sciences. 2016. Journal of the American Statistical Association 111(515):988-1003. https://doi.org/10.1080/01621459.2016.1141684 (search)
- [R76] Analysis of Composition on the Original Scale of Measurement. 2023. arXiv 2312.10548. Authors not retrieved. https://arxiv.org/abs/2312.10548 (partial)
- [R77] Schulze, Wiegrebe, Thurner, Heumann, Aßenmacher. A Bayesian Approach to Modeling Topic-Metadata Relationships. 2021, revised 2025. arXiv 2104.02496. https://arxiv.org/abs/2104.02496 (opened, abstract)
- [R78] Nakagawa, Johnson, Schielzeth. The Coefficient of Determination R2 and Intra-Class Correlation Coefficient from Generalized Linear Mixed-Effects Models Revisited and Expanded. 2017. Journal of the Royal Society Interface 14(134):20170213. https://pmc.ncbi.nlm.nih.gov/articles/PMC5636267 (search)

**Inference, robustness, registration**
- [R79] Cameron, Gelbach, Miller. Bootstrap-Based Improvements for Inference with Clustered Errors. 2008. Review of Economics and Statistics 90(3):414-427. https://www.nber.org/papers/t0344 (search)
- [R80] MacKinnon, Nielsen, Webb. Cluster-Robust Inference: A Guide to Empirical Practice. 2023. Journal of Econometrics 232(2):272-299. https://arxiv.org/abs/2205.03285 (search)
- [R81] Pustejovsky, Tipton. Small-Sample Methods for Cluster-Robust Variance Estimation and Hypothesis Testing in Fixed Effects Models. 2018. Journal of Business and Economic Statistics 36(4):672-683. https://arxiv.org/abs/1601.01981 (search)
- [R82] Elff, Heisig, Schaeffer, Shikano. Multilevel Analysis with Few Clusters: Improving Likelihood-Based Methods to Provide Unbiased Estimates and Accurate Inference. 2021. British Journal of Political Science 51(1):412-426. https://www.ssoar.info/ssoar/handle/document/67788 (search)
- [R83] Gelman. Prior Distributions for Variance Parameters in Hierarchical Models. 2006. Bayesian Analysis 1(3):515-534. https://doi.org/10.1214/06-BA117A (search; the group-count thresholds are from secondary summaries)
- [R84] Yarkoni. The Generalizability Crisis. 2022. Behavioral and Brain Sciences 45:e1. https://pubmed.ncbi.nlm.nih.gov/33342451/ (search)
- [R85] Breznau et al. Observing Many Researchers Using the Same Data and Hypothesis Reveals a Hidden Universe of Uncertainty. 2022. PNAS 119(44):e2203150119. https://doi.org/10.1073/pnas.2203150119 (search)
- [R86] Chan, Bajjalieh, Auvil, Wessler, Althaus, Welbers, van Atteveldt, Jungblut. Four Best Practices for Measuring News Sentiment Using 'Off-the-Shelf' Dictionaries: A Large-Scale P-Hacking Experiment. 2021. Computational Communication Research 3(1):1-27. https://www.aup-online.com/content/journals/10.5117/CCR2021.1.001.CHAN (search)
- [R87] Del Giudice, Gangestad. A Traveler's Guide to the Multiverse: Promises, Pitfalls, and a Framework for the Evaluation of Analytic Decisions. 2021. Advances in Methods and Practices in Psychological Science 4(1). https://doi.org/10.1177/2515245920954925 (search)
- [R88] Card, Henderson, Khandelwal, Jia, Mahowald, Jurafsky. With Little Power Comes Great Responsibility. 2020. EMNLP, 9263-9274. https://aclanthology.org/2020.emnlp-main.745 (search)
- [R89] Dror, Baumer, Shlomov, Reichart. The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing. 2018. ACL, 1383-1392. https://aclanthology.org/P18-1128/ (search)
- [R90] van Miltenburg, van der Lee, Krahmer. Preregistering NLP Research. 2021. NAACL, 613-623. https://aclanthology.org/2021.naacl-main.51 (search)

**Measurement validity**
- [R91] Grimmer, Stewart. Text as Data: The Promise and Pitfalls of Automatic Content Analysis Methods for Political Texts. 2013. Political Analysis 21(3):267-297. https://www.doi.org/10.1093/PAN/MPS028 (search)
- [R92] Jacobs, Wallach. Measurement and Fairness. 2021. ACM FAccT. https://arxiv.org/abs/1912.05511 (search)
- [R93] TeBlunthuis, Hase, Chan. Misclassification in Automated Content Analysis Causes Bias in Regression. Can We Fix It? Yes We Can! 2024. Communication Methods and Measures. https://arxiv.org/abs/2307.06483 (search)
- [R94] Song, Tolochko, Eberl et al. In Validations We Trust? The Impact of Imperfect Human Annotations as a Gold Standard on the Quality of Validation of Automated Content Analysis. 2020. Political Communication 37(4):550-572. https://doi.org/10.1080/10584609.2020.1723752 (search)
- [R95] Birkenmaier, Lechner, Wagner. ValiTex: a validation framework for computational text-based measures of social science constructs. 2023. arXiv 2307.02863. https://arxiv.org/abs/2307.02863 (search; exact preprint title not confirmed)
- Birkenmaier, Lechner, Wagner. The Search for Solid Ground in Text as Data: A Systematic Review of Validation Practices and Practical Recommendations for Validation. Communication Methods and Measures. (unverified: the search did not return it)
- Tetlock. Expert Political Judgment. 2005. Book. (unverified; background to R35 to R37)
