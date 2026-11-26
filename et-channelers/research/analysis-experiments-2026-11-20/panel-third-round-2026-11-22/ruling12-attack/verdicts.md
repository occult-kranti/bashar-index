# Ruling 12: the second attack pass on the single-verdict novelty claims

Written 2026-11-26 from 15:34 UTC (times from `date -u`) by the ruling-12 methods attacker, a model agent working for
the project lead. No person checked it. This is a novelty attack, not a result. Every claim attacked here is a
statement about design and method. None says anything about the corpus.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**No novelty sentence may be printed from this file until the lead accepts it, and the bibliography check of ruling 13
has been done.**

## 1. What was attacked and how

- **Claims.** The 28 claims that had a single verdict, from den-soc, and den-soc's own four claims (n1 to n4, which
  had no attacker other than their author), as listed in `programme.md` 3.1 and 3.2 and in deposit 2's
  `novelty-ledger.md`. The pass started with llm-n2 (N02) and den-mat-n4 (N15), as ruling 12 asks. In total, 32
  claims in 28 wordings: 26 deposited clusters, N20 (which holds the lead half of den-soc-n3), and P32.
- **Order of attack.** The deposited order was followed:
  1. Has it been done?
  2. Is it trivial, either because every account predicts it or because the measure builds it?
  3. Can these data show it?
  4. Otherwise it survives.
- **Verdict classes.** These are used consistently for every claim:
  - **refuted**: a prior work does the claimed design, meaning all the parts that define it, on comparable material.
  - **narrowed**: a prior work found in this pass does a part that the deposited wording claimed as new. The final
    wording then claims less, or newly says "the method is theirs".
  - **survives**: everything found in this pass was already conceded by the deposited wording or its NOTE. The claim
    stands as deposited, with the count updated and the closest-work list extended.
  - The search helpers sometimes labelled a claim "narrowed" where the claimed part did not change. In those cases
    (den-meth-n3, den-meth-n4, occult-n4) the label here is "survives" and the reason is given. The lead may relabel.
- **Counting rule (deposited).** A wording reads "not found in X member searches or in Y attacker searches". Searches
  counted in this pass are attacker searches. They are added to Y and written as "Y + k = Z". The member count X is
  unchanged. A search counts only if it returned hits that were examined. Refused calls, empty results and hits that
  matched another sense of a word are logged in `attack-ledger.csv` with `counted = no`.
- **Engines.**
  - Firecrawl paper search (PubMed, bioRxiv, arXiv and others), the built-in WebSearch, and Consensus (3 papers per
    query).
  - Crossref, OpenAlex (a shared free daily budget; 19 queries used, 17 counted), the arXiv API, Europe PMC and
    PubMed.
  - Semantic Scholar (mostly refused with HTTP 429), and the Internet Archive / Open Library full-text index as the
    monograph substitute.
  - Pages and PDFs were opened with WebFetch and with Firecrawl's paper reader.
- **Not reached.**
  - Firecrawl web search was refused all session because the account was out of credits.
  - Google Books refused every call (HTTP 429).
  - The arXiv API returned empty results from about 15:08 UTC.
  - ATLA, PsycINFO, MLA, Scopus and Web of Science are paywalled.
  - Non-English religious-studies indexes were reached only by three Portuguese and two German queries.
  - A "not found" is therefore weakest for the humanities and monograph claims (N10, N12, N22 to N30).
- **Who searched.**
  - The attacker ran llm-n2, den-mat-n4 and the lead half of den-soc-n3 directly.
  - The other 29 claims were searched by four search helpers (model agents) under one written brief, with the same
    tools, rules and counting rule.
  - The verdicts are the attacker's. Every source that narrows a claim was re-opened by the attacker (section 4),
    except where marked.
- **Totals.** 265 ledger rows, of which 218 are counted searches, over 32 claims. Every claim has at least 5 counted
  searches on at least 4 engines.

## 2. Counts

| | Claims |
|---|---|
| Refuted | 0 |
| Narrowed | 11: speech-n2, den-meth-n1 (N01); llm-n3 (N07); speech-n3 (N13); emic-n3, den-soc-n2 (N17); den-mat-n1, den-meth-n2 (N21); emic-n2 (N23); et-n2 (N26); den-mat-n2 (N31) |
| Survived | 21: llm-n2 (N02); den-mat-n4 (N15); speech-n1 (N03); den-meth-n3, llm-n1 (N04); llm-n4 (N06); occult-n2 (N10); den-meth-n4 (N11); den-mat-n3 (N12); speech-n4 (N14); den-soc-n1 (N16); den-soc-n3 (N19 and N20); et-n3 (N22); occult-n4 (N24); occult-n1, et-n1 (N25); et-n4 (N27); emic-n1 (N28); emic-n4 (N29); occult-n3 (N30); den-soc-n4 (P32) |

By wording, there are 28 wordings in all:
- 8 are narrowed: N01, N07, N13, N17, N21, N23, N26 and N31. N01, N17 and N21 each carry two narrowed claims.
- 19 survive with their counts updated: N02, N03, N04, N06, N10, N11, N12, N14, N15, N16, N19, N20 (count only), N22,
  N24, N25, N27, N28, N29 and N30.
- P32 gets its first wording.

| Claim | Cluster | Verdict | Counted searches (k) | Attacker searches on the wording |
|---|---|---|---|---|
| llm-n2 | N02 | survives | 9 | 8 + 9 = 17 |
| den-mat-n4 | N15 | survives | 7 | 3 + 7 = 10 |
| speech-n2 | N01 | narrowed | 7 | 14 + 14 = 28 (with den-meth-n1) |
| den-meth-n1 | N01 | narrowed | 7 | (as above) |
| speech-n1 | N03 | survives | 8 | 2 + 8 = 10 |
| den-meth-n3 | N04 | survives | 7 | 8 + 13 = 21 (with llm-n1) |
| llm-n1 | N04 | survives | 6 | (as above) |
| llm-n4 | N06 | survives | 7 | 2 + 7 = 9 |
| llm-n3 | N07 | narrowed | 7 | 2 + 7 = 9 |
| occult-n2 | N10 | survives | 9 | 9 + 9 = 18 |
| den-meth-n4 | N11 | survives | 7 | 12 + 7 = 19 |
| den-mat-n3 | N12 | survives | 8 | 2 + 8 = 10 |
| speech-n3 | N13 | narrowed | 7 | 3 + 7 = 10 |
| speech-n4 | N14 | survives | 6 | 2 + 6 = 8 |
| den-soc-n1 | N16 | survives | 6 | 12 + 6 = 18 |
| emic-n3 | N17 | narrowed | 5 | 10 + 12 = 22 (with den-soc-n2) |
| den-soc-n2 | N17 | narrowed | 7 | (as above) |
| den-soc-n3 | N19 (timing half) | survives | 6 | 9 + 6 = 15 |
| den-soc-n3 | N20 (lead half) | survives | 3 | 21 + 3 = 24 |
| den-mat-n1 | N21 | narrowed | 9 | 4 + 15 = 19 (with den-meth-n2) |
| den-meth-n2 | N21 | narrowed | 6 | (as above) |
| et-n3 | N22 | survives | 6 | 1 + 6 = 7 |
| emic-n2 | N23 | narrowed | 6 | 2 + 6 = 8 |
| occult-n4 | N24 | survives | 6 | 3 + 6 = 9 |
| occult-n1 | N25 | survives | 7 | 2 + 12 = 14 (with et-n1) |
| et-n1 | N25 | survives | 5 | (as above) |
| et-n2 | N26 | narrowed | 7 | 2 + 7 = 9 |
| et-n4 | N27 | survives | 5 | 3 + 5 = 8 |
| emic-n1 | N28 | survives | 7 | 3 + 7 = 10 |
| emic-n4 | N29 | survives | 6 | 2 + 6 = 8 |
| occult-n3 | N30 | survives | 7 | 2 + 7 = 9 |
| den-mat-n2 | N31 | narrowed | 6 | 2 + 6 = 8 |
| den-soc-n4 | P32 | survives | 6 | 0 + 6 = 6 |

## 3. One section per claim

Each wording ends "Not found means only that." The searches behind every count are in `attack-ledger.csv`.

### llm-n2 (N02): survives

- **Searches.** 9 counted: Firecrawl paper search (3), WebSearch (2), Consensus, Crossref, OpenAlex and arXiv. Four
  more were logged and not counted: a refused Firecrawl web search, two empty arXiv queries and one empty Semantic
  Scholar query.
- **Evidence.** No work tests whether language-model labels on fixed-grid transcripts lock to the decoder's seams.
  - **Terpstra et al. 2023**, "How Good is Automatic Segmentation as a Multimodal Discourse Annotation Aid?", ISA-19
    workshop, arXiv:2305.17350, https://arxiv.org/abs/2305.17350. Full text read, pp. 3-5. Labels given to Whisper-
    and Google-segmented utterances differ from labels on oracle utterances: "Whisper segments split up continuous
    utterances by a single person". This is ASR segmentation passing into annotation, with human annotators. It does
    not test seams.
  - **Sakib et al. 2026**, "ShobdoSetu: A Data-Centric Framework for Bengali Long-Form Speech Recognition and Speaker
    Diarization", arXiv:2603.19256, https://arxiv.org/html/2603.19256. HTML read: WhisperX "assigns speaker labels at
    transcript chunk boundaries", so "a single label covers an entire chunk even when multiple speakers are active".
    Here labels are tied to chunks by construction, which is den-soc's warning. It is not a test.
  - **The circular-shift null is a standard test of boundary alignment.** Tanner et al. 2023, Imaging Neuroscience,
    https://doi.org/10.1162/imag_a_00026 (passage): "a null model by circularly shifting event time series ... to
    maintain event number and relative timing while breaking alignment". Antony et al. 2021, Neuron,
    https://doi.org/10.1016/j.neuron.2020.10.029 (passage): boundary agreement "p = 0.04 by circular shift". This is
    a generic permutation device, so it does not narrow the claim. The shifted-grid re-decode reference was found
    nowhere.
- **Attacks.**
  - (2) If any label unit is a decoder segment, seam-lock is built in (den-soc). Sakib et al. show this happening in
    a WhisperX pipeline. Precondition: record whether the labeller's input carried decoder segment breaks or
    timestamps. If it did, the test reads "built in", not "found".
  - (3) The sentence-unit row is the grid's effect on the reference, as deposited.
- **Final wording (N02).** A test of whether language-model span boundaries on fixed-grid recognizer transcripts lock
  to the decoder's seams, against a circular shift and the boundaries of a shifted-grid re-decode, was not found in 10
  member searches (summed) or in 8 + 9 = 17 attacker searches. Closest:
  - chunk-edge artefacts in long-form decoding (Bain et al. 2023; Wang et al. 2024; Altinok 2025);
  - boundary looseness passed to diarization (Horiguchi et al. 2025);
  - speaker labels assigned per transcript chunk in a WhisperX pipeline (Sakib et al. 2026);
  - automatic segmentation changing the labels annotators give (Terpstra et al. 2023);
  - fixed-length segmentation in speech translation (Gaido et al. 2021; Tsiamas et al. 2022);
  - punctuation inconsistent between chunks (a 2026 preprint);
  - transcript noise downstream (Shapira et al. 2025);
  - the circular-shift null as a standard test of boundary alignment (Antony et al. 2021; Tanner et al. 2023).

  It is a pipeline check. Not found means only that.

### den-mat-n4 (N15): survives

- **Searches.** 7 counted: Firecrawl paper search (2), WebSearch (2), Consensus, Crossref and Europe PMC. An empty
  OpenAlex query and an arXiv query that matched another sense were logged and not counted.
- **Evidence.** No work compares within-speaker shifts into a claimed voice with within-speaker shifts into a declared
  character on field recordings run through one pipeline. Each side exists apart:
  - **Jürgens et al. 2015**, J Nonverbal Behav, https://doi.org/10.1007/s10919-015-0209-5 (abstract and passage).
    Authentic emotional speech from radio interviews is set against re-enactments by actors: "Both play-acted
    conditions ... possessed more variable pitch contours than the spontaneous recordings". This is the
    real-against-acted design with field recordings on one side.
  - **Pethe et al. 2025**, ICSC, https://doi.org/10.1109/ICSC64641.2025.00036 (passages), and **Park and Li 2026**,
    KyaraBench, arXiv:2610.06013 (abstract). One performer's declared character voices in published recordings.
  - **Kruse 2017**, "Forensic voice analysis for mediumistic phenomena", web essay, last updated 9/2017,
    https://eckhardkruse.net/physmed/voiceanalysis.html?en (page read). Grey literature. Formant charts set one
    medium's séance voices beside actors' character portrayals and the original speaker. It covers one medium,
    between speakers, and is informal. The medium is not named here, under the naming rule.
  - **Schaffler and Brabec de Mori 2017**, Jahrbuch des Phonogrammarchivs (abstract via Consensus). In
    videographed possession performance, mediums must be "excellent (inter-)actors". This is ethnography, with no
    measurement.
  - A chapter titled "To Perform Possession and to be Possessed in Performance: The Actor, the Medium and an
    'Other'" (Spirit Possession and Trance, Continuum 2010, https://doi.org/10.5040/9781472549365.ch-012). Only the
    record was seen; the chapter was not opened, and its author is not shown in the Crossref record. It is listed for
    the lead, not counted.
- **Attacks.**
  - (2) Audiobook readers raise pitch for presented voices (Pethe et al. 2025). A delivery shift into any presented
    voice is therefore the ordinary-performance baseline, and "equal" is the performance account's prediction.
  - (3) The size of the declared-character shift depends on which genre is chosen: cartoon voices against audiobook
    narration. The declared genres, and a reading per genre, must be fixed before collection. Matched format is hard,
    because long-form talk is not scripted fiction.
- **Final wording (N15).** A comparison, on public field recordings run through one frozen pipeline, of within-speaker
  shifts into a claimed voice with within-speaker shifts into a declared character, was not found in 4 member
  searches or in 3 + 7 = 10 attacker searches. Closest:
  - laboratory real-simulator designs in hypnosis (Orne 1971), dissociative identity (Reinders et al. 2012) and
    mediumship (Mainieri et al. 2017; Pinto et al. 2026);
  - authentic field speech set against actors' re-enactments of it (Jürgens et al. 2015);
  - one performer's declared character voices in published recordings (Pethe et al. 2025; Park and Li 2026);
  - an informal formant comparison of one medium's séance voices with actors' portrayals (grey literature, 2017);
  - possession performance read as acting in field ethnography (Schaffler and Brabec de Mori 2017);
  - studies of persona streamers' identity and income (Zhao et al. 2025).

  Needs a new collection; every reading is about performance, never about a source. Not found means only that.

### speech-n2 (N01): narrowed

- **Searches.** 7 counted, on six engines.
- **Evidence.** **Munot and Nenkova 2019**, "Emotion Impacts Speech Recognition Performance", NAACL Student Research
  Workshop, pp. 16-21, https://doi.org/10.18653/v1/N19-3003. The helper read the full text; the attacker re-opened
  the abstract. "We propose and validate on the acted datasets, a method that allows us to evaluate the overall impact
  of emotion on recognition even when manual transcripts are not available", and (section 5.2) "we treat the output of
  one API as the reference and get WER for other APIs with respect to it". This is reference-free disagreement between
  recognizers, read by a speaking condition inside the same conversations. That is the core of N01's design, on
  emotion rather than a presented voice.
- **Attacks.**
  - (2) A condition gap in cross-recognizer disagreement is already shown, so only its size against the margins tied
    to the consequences is informative.
  - (3) The voice stratifier is model-coded on one decode's own punctuation. Read C1 and C2 also on spans located on
    the other decode.
- **Final wording (N01; shared with den-meth-n1).** A reference-free, within-speaker, within-recording comparison of
  Whisper-family decode instability between a self-presented other voice and the same speaker's own voice, by word
  class, with margins tied to the downstream contrasts, was not found in the four members' 29 searches (summed;
  overlapping) or in 14 + 14 = 28 attacker searches.
  - Reading disagreement among recognizers, without references, by a speaking condition inside the same
    conversations is Munot and Nenkova's design (2019): emotional against neutral speech, with the proxy validated
    against references on acted corpora. The method is theirs. Only the self-presented voice contrast, the
    Whisper-family decode families (teacher against student, a 15-s grid shift), the word classes and the margins
    tied to the consequences are this corpus's.
  - Closest also: style- and mode-differential recognizer error within the same speakers against human references
    (Shinozaki, Ostendorf and Atlas 2009; Afkir and Zellou 2026; Tobin et al. 2024; Farhadipour et al. 2024, 2025;
    Li et al. 2023); dialect-feature error and normalisation (Chang et al. 2024; Serditova et al. 2025, 2026;
    Blaschke et al. 2025; Ma et al. 2023); switch-point error (PIER 2025); reference-free disagreement that leaves
    shared errors unseen (Karbalaie et al. 2026); syllable counts for omissions (Diaz-Asper et al. 2022).
  - A result may say only "no differential instability detected among Whisper-family decodes; shared normalisation
    untested".

  Not found means only that.
- **Note.** The helper also proposed three papers on estimating word error rate without references (Ali and Renals
  2020; Yuksel et al. 2023; Waheed et al. 2025). They were read only as index abstracts, so they are left out of the
  wording until opened.

### den-meth-n1 (N01): narrowed

- **Searches.** 7 counted, distinct from speech-n2's.
- **Evidence.** Munot and Nenkova 2019, as above; this claim's query 4 found it. Searches of persona, trance,
  possession, dissociative and audiobook character speech found no audit of a recognizer by voice.
- **Attacks.** den-meth's own attacks stand. Koenecke et al. 2024 predict the direction of insertions. The audit is
  conditional on a label that the recognizer helps make.
- **Final wording.** The N01 wording above (one wording per cluster).

### speech-n1 (N03): survives

- **Searches.** 8 counted.
- **Evidence.** No work reads a shifted-grid re-decode as a placebo to locate window-phase marks. The closest new work
  is **Ahn et al. 2026**, Whisper-CD, arXiv:2603.06193 (abstract opened by the helper): an audio time shift is used
  as a negative inside contrastive decoding. That is a remedy, not an audit.
- **Attacks.**
  - (3) A 15-s shift changes both the window phase and the earlier text the decoder conditions on. The placebo
    isolates marks locked to the phase only where the conditioning text is held fixed, or where both decodes are run
    without previous-text conditioning.
  - Inserted closings collide with real closings (den-soc), so the inference must rest on phase-locking, not on the
    identity of the phrase.
- **Final wording (N03).** Reading a shifted-grid re-decode against the original grid as a placebo, to locate
  window-phase marks (grid-made pauses, seam edits, an inserted closing phrase) without a reference, was not found as
  a reported audit in 6 member searches or in 2 + 8 = 10 attacker searches. Closest:
  - overlapping and offset windows that repair boundary errors (Chiu et al. 2019; Wang et al. 2022);
  - Whisper's "bag of hallucinations" (Barański et al. 2025);
  - a zero-padding control (Zolkepli 2026);
  - chunk-edge truncation (Wang et al. 2024);
  - an audio time shift used as a negative inside contrastive decoding, not as an audit (Ahn et al. 2026);
  - an informal practitioner report of window-end closings.

  An application already run; real closings must be separated from inserted ones before any voice split, and phase
  must be separated from conditioning context. Not found means only that.

### den-meth-n3 (N04): survives (the helper proposed "narrowed")

- **Searches.** 7 counted.
- **Evidence.** These are closer instances of a method the deposited wording already concedes ("The method is theirs;
  only the target is this corpus's"):
  - **Singh, Davari and Mashhadi 2026**, RADAR, arXiv:2608.01810, https://arxiv.org/abs/2608.01810. The attacker
    re-opened the abstract: criteria scored by one model judge "can be behaviorally coupled: improving one criterion
    may systematically change scores on another"; the method "generates targeted synthetic probes, scores each probe
    on all criteria".
  - **Hu et al. 2024**, ACL, arXiv:2402.12055: model evaluators confuse criteria.
  - **Halterman and Keith 2025**, arXiv:2510.03541; the attacker re-opened it: "conceptualization errors that bias
    downstream estimates".

  The claimed part (this target, the island footprint and arm A) is unchanged, so the verdict is "survives".
- **Attacks.**
  - (2) Under the own-offer rule, the near-absence of asks in the claimed voice is built by the measure for every
    offer the rule reaches.
  - Only arm A (unfunded) can carry a positive result.
- **Final wording (N04; shared with llm-n1).** A test for incorporation bias between a model voice label and a model
  ask label coded by one reader, was not found in 16 member searches (summed) or in 8 + 13 = 21 attacker searches.
  The test uses:
  - a one-sided, no-cost island footprint;
  - an unfunded reversed known-answer arm (the same offer voiced by the source);
  - a name-swap arm for widely published sources;
  - a corpus where that assignment is itself the outcome reported.

  Closest:
  - incorporation bias and criterion contamination (Carpenter et al. 2023; Lynöe and Eriksson 2023; Schroeder and
    Costa 1984; Lengua, West and Sandler 1998; Lemery, Essex and Smider 2002; Budescu and Rodgers 1981);
  - coupling between criteria scored by one model judge, probed with targeted synthetic items (Singh, Davari and
    Mashhadi 2026; Hu et al. 2024);
  - codebook conceptualization errors that bias downstream estimates (Halterman and Keith 2025);
  - definition swaps and counterfactual audits of model annotators (Mamaev et al. 2026; Mishra et al. 2026; He et al.
    2026);
  - contrast sets and CheckList (Gardner et al. 2020; Ribeiro et al. 2020);
  - content priors in speaker attribution (Lee et al. 2026; Liu et al. 2026);
  - memory shortcuts (Wang and Song 2026);
  - a book-memorisation check on model quotation attribution (Michel et al. 2025).

  The method is theirs; only the target is this corpus's. Not found means only that.

### llm-n1 (N04): survives

- **Searches.** 6 counted.
- **Evidence.** No content-prior test was found on a voice or footing label with commercial content. Added as closest:
  **Michel, Epure, Hennequin and Cerisara 2025**, NAACL, arXiv:2406.11380 (abstract opened by the helper), which
  assesses "the impact of book memorization and annotation contamination" in model quotation attribution.
- **Attacks.** The name-swap arm is a standard counterfactual (entity renaming), so it adds a target, not a method.
  The content prior and the codebook rule predict the same direction.
- **Final wording.** The N04 wording above.

### llm-n4 (N06): survives

- **Searches.** 7 counted.
- **Evidence.** Two more parts now exist, both on fixed items, with no arm for new material:
  - **Sunkavalli 2026**, arXiv:2608.29517 (abstract): a pre-registered audit of version shift in model raters.
  - **Wiese 2026**, PLOS ONE 21(2) e0339920, https://doi.org/10.1371/journal.pone.0339920 (article page): a
    preregistered longitudinal study of drift over ten weekly waves on a fixed prompt bank.

  The 2 × 2 crossing itself was not found.
- **Attacks.**
  - (3) The material arm confounds season and recognizer quality with speaker familiarity, unless the covariates are
    matched.
  - The interaction cell will have wide intervals.
  - If the alias is retired, "alias not available" is the result.
- **Open risk.** Educational automated scoring (engine monitoring and rater drift; Williamson, Xi and Breyer 2012) may
  already cross engine versions with new examinee cohorts. Those reports were not opened. See section 5.
- **Final wording (N06).** A 2 × 2 design crossing model-version drift (an anchor sample re-read under the frozen
  alias and any successor) with transport to new material from the same speakers and to fresh speakers, under a
  reliability prediction hashed before labelling, was not found in 5 member searches or in 2 + 7 = 9 attacker
  searches. Closest:
  - version drift of one nominal model (Chen, Zaharia and Zou 2023);
  - anchor audits of judge versions (Zhang and Yang 2026);
  - pre-registered audits of version shift and drift of model raters on fixed items (Sunkavalli 2026; Wiese 2026);
  - separating population shift from pipeline change (Leest et al. 2026);
  - model pre-registration before a prospective sample (Gu et al. 2025).

  A design; every arm needs a new collection and model calls. Not found means only that.

### llm-n3 (N07): narrowed

- **Searches.** 7 counted.
- **Evidence.** Both sources were re-opened by the attacker.
  - **Feng et al. 2026**, "Noisy but Valid: Robust Statistical Evaluation of LLMs with Imperfect Judges",
    arXiv:2601.20913, https://arxiv.org/abs/2601.20913 (abstract): "By leveraging a small human-labelled calibration
    set to estimate the judge's True Positive and False Positive Rates". Known-answer items used to gate a model judge
    before it scores a large set: that is the "constructed known-outcome items" half of the claim.
  - **Zhou and Lin 2026**, JuryProbe, TMLR, arXiv:2608.20607, https://arxiv.org/abs/2608.20607 (abstract): "agreement
    may reflect shared false-negative blind spots"; the risk is estimated "from a labeled calibration probe" with "a
    fixed, pre-specified rule" and a negative control. That covers RQ-n3b (correlated leniency).
- **Attacks.**
  - (3) For predicates that recur (earthquakes, unrest, "awakening"), a statement shifted 12 months is often truly
    fulfilled in the shifted window. The placebo rate is then base rate plus leniency, so a covariate for predicate
    recurrence is needed. Only the constructed known-false items measure leniency cleanly.
- **Final wording (N07).** Window-shifted placebo statements and constructed known-outcome items, fixed before the
  windows of naturally occurring public forecasts mature, used as an admissibility gate for model resolvers, were not
  found in 5 member searches or in 2 + 7 = 9 attacker searches. Closest:
  - target-against-decoy readings in research on mediums (Beischel et al. 2015; Freire et al. 2020; Tressoldi et al.
    2022);
  - known-answer calibration of a model judge's false-positive rate before it scores a large set (Feng et al. 2026);
  - correlated errors of reference-free judge panels, measured on a labelled probe under a pre-specified rule with a
    negative control (Zhou and Lin 2026);
  - leniency of model judges (Thakur et al. 2024; Vaugrante and Hagendorff 2026);
  - automated resolution of crisp generated questions (Bosse et al. 2026).

  The decoy design and the known-answer calibration of model judges are theirs; only the window-shifted placebos of
  natural forecasts and the timing are this corpus's. Not found means only that.

### occult-n2 (N10): survives

- **Searches.** 9 counted. Google Books was refused and the Open Library index was used instead.
- **Evidence.** No count of plural self-reference in claimed-voice recordings. New closest work:
  - **Silva 2026**, Cadernos de Estudos Linguísticos 68, https://doi.org/10.20396/cel.v68i00.8682831 (abstract): a
    qualitative reading of designation and deixis in religious trance.
  - **Magyari, Pléh and Forgács 2022**, PLoS ONE, https://doi.org/10.1371/journal.pone.0273226 (abstract and
    passage): the I-to-we ratio in leaders' spontaneous speeches.
  - **Cunningham 2012**, Journal of Parapsychology 76(2) (full text): style features of one channelled corpus, with
    no counts.
- **Attacks.** (2) Plural first person rises in a lecturing register whoever speaks (Magyari et al.). Unless inclusive
  "we" (speaker plus audience) is held apart from exclusive collective "we", a higher plural share is predicted by
  register alone. This condition should enter the method.
- **Final wording (N10).** A recording-level, many-speaker count of plural self-reference in claimed-voice recordings
  against the same speakers' own-voice talks, with no span label selecting the units, was not found in 13 member
  searches (summed) or in 9 + 9 = 18 attacker searches. Closest:
  - qualitative pronoun analyses of written channellings (Petryk 2016, 2019);
  - voice and agency in mediumship (Tomlinson 2019, 2025);
  - LIWC on mediums' written reports (Beischel et al. 2017);
  - a scripture's plural narrator (Mutter 2022);
  - clusivity resolution in parliament (Rehbein, Ruppenhofer and Bernauer 2022);
  - I-to-we diffusion in an online collective (Sepahpour-Fard et al. 2024);
  - the I-to-we ratio in leaders' spontaneous speeches (Magyari, Pléh and Forgács 2022);
  - a qualitative reading of designation and deixis in religious trance (Silva 2026).

  Inclusive and exclusive "we" are counted apart. The spread over speakers is read as noise-corrected heterogeneity
  ("concentrated", "spread", "undetermined"), not as "koine" or "lineage". Not found means only that.

### den-meth-n4 (N11): survives (the helper proposed "narrowed")

- **Searches.** 7 counted.
- **Evidence.** **Sousa and Pires 2023**, "Análises estatístico-computacionais de atribuição de autoria: Augusto dos
  Anjos e a obra psicografada Parnaso de Além-Túmulo", Domínios de Lingu@gem 17, e1749,
  https://doi.org/10.14393/DLv17a2023-49. The attacker re-opened the record and the Portuguese abstract.
  - Function words, grammatical distribution and n-gram codes (Hyperbase) were applied to 31 poems that one medium
    attributed to a dead poet.
  - The abstract: "Os supostos poemas atribuídos à autoria de dos Anjos se encontram, na verdade, mais próximos de
    Lira imortal (1939)", the same medium's other channelled book, and "não se aproximam, estilisticamente, de Eu
    (1912)".
  - This is the persona-or-register question asked of written channelled texts from one medium. The deposited
    wording already concedes the question to literary stylometry and claims only "this spoken, within-recording
    form", which this work does not touch.

  Also **Cunningham 2012** (full text, read by the helper): it proposes benchmarking a channelled voice against the
  medium's ordinary waking utterances, and does this qualitatively for one case.
- **Attacks.** (2) A "nearer its speaker" result is close to built in on recognizer text, because recognizer
  idiosyncrasy is shared within speaker (Aggazzotti et al. 2025). Both the decode rung and the own-own rung must be
  shown.
- **Final wording (N11).** The persona-or-register question of literary stylometry, asked of recognizer-transcribed
  speech with rungs held inside the recording, profiles resampled to equal token counts, a decode rung and an
  own-voice rung from own-voice-only talks, was not found in this spoken, within-recording form in 13 member searches
  (summed) or in 12 + 7 = 19 attacker searches. Closest:
  - one author's character idiolects (Burrows 1987; Burrows and Craig 2012; Šeļa et al. 2023);
  - heteronyms (Skorinkin and Orekhov 2023);
  - one person's several online identities (Afroz et al. 2014);
  - register as the stylometric signal (Grieve 2023);
  - speaker attribution that survives recognizer error (Aggazzotti et al. 2025);
  - trance against waking texts or interviews in small groups (Pinto et al. 2026; Wahbeh et al. 2026);
  - the same question asked of one medium's written channelled texts (Sousa and Pires 2023);
  - a proposal to benchmark a channelled voice against the medium's waking utterances, done qualitatively for one
    case (Cunningham 2012).

  Not found means only that.

### den-mat-n3 (N12): survives

- **Searches.** 8 counted.
- **Evidence.** No count of archaic agreement in modern spoken religious speech was found. New closest work: **Terry
  2014**, Dialogue: A Journal of Mormon Thought 47(2), https://doi.org/10.5406/dialjmormthou.47.2.0001 (article page,
  read by the helper). It is an essay on modern religious use of archaic pronouns, with tallies from one revealed text.
- **Attacks.**
  - (2) Archaic register is a known feature of ritual speech, so presence is predicted by every account.
  - (3) A Whisper-family language prior can regularise the very agreement at issue.
  - Part 2 (whether the profile follows the creator or the named source) has a semantic-content analogue in Wahbeh
    and Glick 2026 (three channellers). Cite it if part 2 is ever worded.
- **Final wording (N12).** A creator-level description of the agreement pattern of archaic pronoun and verb forms, as
  they appear in the transcripts of claimed-voice speech across many speakers, was not found in 4 member searches or
  in 2 + 8 = 10 attacker searches. Closest:
  - a sceptical linguist's single-speaker analyses of channelled and past-life speech (Thomason 1987, 1995);
  - pseudo-archaic English (Traxel 2012);
  - the grammar of one revealed text (Carmack 2018);
  - archaic forms in transcribed homilies (Amore et al. 2023);
  - an essay on modern religious use of archaic pronouns, with tallies from one revealed text (Terry 2014).

  Only presence and the transcribed pattern can be read. Not found means only that.

### speech-n3 (N13): narrowed

- **Searches.** 7 counted.
- **Evidence.** **Pethe, Pham, Childress, Yin and Skiena 2025**, "Prosody Analysis of Audiobooks", 2025 IEEE 19th
  International Conference on Semantic Computing (ICSC), https://doi.org/10.1109/ICSC64641.2025.00036,
  arXiv:2310.06930. The attacker re-read passages of the full text (v3).
  - Over 93 human-read audiobooks: "readers generally use lower pitch in narrative regions rather than dialog,
    independent of gender".
  - "Readers tend to use a higher pitch when reading dialogue and a lower pitch when reading descriptive text".
  - "We have shown that actors customize voices to represent specific characters".

  This is a within-speaker acoustic contrast, in published recordings over many speakers, between a performer's own
  narrating voice and the voices the performer gives to others. Supporting: **Michel, Epure and Cerisara 2025**,
  LibriQuote, arXiv:2509.04072 (passages read by the helper): "pitch standard deviation typically increases with the
  number of quotations".
- **Attacks.** (2) The narrator-against-character result predicts a delivery change at any switch into a presented
  voice. Every account allows it. Only the matched-edge and own-range references and the production census are
  informative.
- **Final wording (N13).** Within-speaker acoustic contrasts between a performer's own narrating voice and the voices
  the performer gives to others, in published recordings over many speakers, exist for audiobooks (Pethe et al. 2025;
  Michel, Epure and Cerisara 2025). Applied to self-attributed voice switches, against matched non-boundary edges and
  the creator's own range across recordings, on voiced-frame features and only at boundaries that pass a splice and
  music-bed census, it was not found in 6 member searches or in 3 + 7 = 10 attacker searches. Closest also:
  - a laboratory within-subject comparison of trance channellers reading one story (Wahbeh et al. 2019);
  - within-talker stability across styles (Ferguson et al. 2024);
  - an impersonator's voices (Revis et al. 2013);
  - voices in dissociative identity (Sawaguchi 2018);
  - within-person vocal variability (Lavan et al. 2019);
  - the same chanters' ritual chant against their speech (Nwosu 2026).

  The narrator-against-character contrast is theirs; only the self-attributed target and the matched-edge, own-range
  and production references are this corpus's. Not found means only that.

### speech-n4 (N14): survives

- **Searches.** 6 counted.
- **Evidence.** No audio classification of non-speech events before switches into a claimed voice was found. New
  closest work: **Bastos et al. 2019**, Psychoneuroendocrinology (abstract): heart rate, HRV and plasma markers before
  and after spirit communication. Sensors only, no audio.
- **Attacks.**
  - (2) An inbreath before any long turn is universal, so only an excess over length-matched own-voice onsets can be
    read.
  - (3) Noise gates and music beds make absence unreadable.
- **Final wording (N14).** Rule-based classes of audible non-speech events in the 30 s before self-presented voice
  switches, against position-matched points, channel templates and length-matched own-voice onsets, were not found in
  6 member searches or in 2 + 6 = 8 attacker searches. Closest:
  - breath detectors (Wang et al. 2012; Zhu et al. 2022; 2026 detectors);
  - breathing that scales with the coming utterance (Torreira, Bögels and Levinson 2015; Włodarczak and Heldner
    2017);
  - sensor-based trance respiration (Wahbeh et al. 2019; Oswald et al. 2023);
  - physiology before and after spirit communication in Spiritist mediums (Bastos et al. 2019);
  - sound-healing audio (Baird and Schuller 2019).

  Not found means only that.

### den-soc-n1 (N16): survives

- **Searches.** 6 counted. This claim had no attacker other than its author, so its own count starts at 0.
- **Evidence.** No work places asks against a within-recording switch of presented speaker. New closest work, all
  abstracts via Consensus:
  - **Doronin 2013**, Antropologicheskij forum: money "is given to the spirits, and the shaman is only an
    intermediary".
  - **Ansah et al. 2020**: fundraising appeals voiced by "imported" fundraisers, not by the preacher.
  - **Tomlinson 2025**, JRAI: mediums claim and disown agency.
- **Attacks.** (2) The host-selling convention, and the same division of labour in other traditions, make "the
  claimed voice vouches, the host names the price" the direction every account predicts. Only a position-matched
  null that the convention could fail is informative.
- **Final wording (N16).** Attribution of spoken commercial asks to a self-presented footing inside the recording,
  read against position and the labeller's own-offer rule and beside the same recording's page, was not found in 17
  member searches (summed) or in 12 + 6 = 18 attacker searches. Closest:
  - host-read against other-voice advertising (Moe 2021; Brinson et al. 2022, 2023; Fisher 2026);
  - the broadcast regulator's host-selling policy (1974);
  - sponsored-segment detection from transcripts (Kok-Shun and Chan 2025; Bertaglia et al. 2026);
  - programme-level fundraising airtime (Abelman et al. 1985);
  - giving appeals voiced with divine authority (Gbote and Kgatla 2014; Ngwoke 2024);
  - fundraising appeals voiced by a second, imported speaker (Ansah et al. 2020);
  - money said to go to the spirits, with the shaman as intermediary (Doronin 2013);
  - mediums claiming and disowning their own agency (Tomlinson 2025);
  - boundary-work of channelling entrepreneurs (Hulkkonen 2021, abstract only).

  Its decisive arms are unfunded or need a new collection. Not found means only that.

### emic-n3 (N17): narrowed

- **Searches.** 5 counted.
- **Evidence.** **Li and Peñaranda Valdivia 2022**, "Does Media Format Matter? Investigating the Toxicity, Sentiment
  and Topic of Audio Versus Text Social Media Messages", Proceedings of HAI '22, pp. 13-22,
  https://doi.org/10.1145/3527188.3561927. The attacker re-read the abstract in the Crossref record of the preprint,
  https://doi.org/10.32920/21692879.v2.
  - "The toxicity, sentiment, topic and length of audio tweet transcripts are compared with their accompanying text,
    date-matched text tweets from the same users".
  - "Audio tweets were significantly less toxic than both text tweets and text that accompanied the audio tweet".

  This is a within-item contrast between speech and the same item's written text, on other material. Its direction
  is emic's third one: the page denser than speech.
- **Attacks.** (2) A reversed gradient now has a precedent for a brand-unsafe property, so it must not be read as
  fear-bait without the placebo adjustment. Many page cells per creator will be zero.
- **Final wording (N17; shared with den-soc-n2).** A placebo-adjusted, within-recording keyness profile between
  indexed page text and locally transcribed speech, for unaltered vocabularies (commerce against link-bound placebos;
  control talk, coded reference and named institutions against matched placebos), crossed with how concentrated
  control talk is over creators and worded as placement, never routing, was not found in 18 member searches (summed)
  or in 10 + 12 = 22 attacker searches.
  - A within-post contrast of transcribed speech against the same post's own text, and against the same users' text
    posts, exists for toxicity, sentiment and topic on audio microblog posts (Li and Peñaranda Valdivia 2022). The
    contrast is theirs in outline; only the placebo-adjusted vocabulary profile on video page text, crossed with
    concentration over creators, is this corpus's.
  - Other closest: keyness statistics (Hardie 2014; Sönning 2023); title-against-transcript incongruity and clickbait
    detection (Mowar et al. 2021; Gamage et al. 2025; Naveed et al. 2025, 2026; Wickramaarachchi et al. 2024; Kulsum
    et al. 2025); algospeak in captions and monetisation (Zhao 2026; Steen et al. 2023; Fillies et al. 2026);
    demonetisation rates by channel size and topic (Dunna et al. 2022); implicit language avoiding moderation in
    written posts (Weinberg et al. 2025); concentration of sharing (Grinberg et al. 2019).

  Not found means only that.

### den-soc-n2 (N17): narrowed

- **Searches.** 7 counted. This claim had no attacker other than its author.
- **Evidence.**
  - Li and Peñaranda Valdivia 2022, as above.
  - **Dunna et al. 2022**, CSCW (pp. 1-3, read by the helper): demonetisation by channel popularity and topic, with no
    contrast between page and speech.
  - No study measures unaltered words placed in speech and kept off the indexed page.
- **Attacks.**
  - (2) Titles are written in a headline register, so named institutions may be denser on the page for genre reasons
    alone. Match the placebo on headline-worthiness.
  - (3) The visibility motive is unobservable. The result must be worded "a gradient between page and speech".
- **Final wording.** The N17 wording above.

### den-soc-n3 (N19 timing half; N20 lead half): survives

- **Searches.** 9 counted: 6 by a helper on the timing half and 3 by the attacker on the lead half. This claim had no
  attacker other than its author.
- **Evidence.**
  - No study sets creators' upload timing against sky or festival calendars and each creator's weekday habit.
  - Closest new work: search interest rising ahead of religious holidays (Dewi et al. 2026, abstract) and concentrated
    at an eclipse (Javed et al. 2026, https://doi.org/10.3390/vision10040071, abstract); online interest indexed to
    religious and lunar calendars (Wood et al. 2017, https://doi.org/10.1038/s41598-017-18262-5).
  - The lead half found nothing beyond N20's existing closest list: forecast-horizon and probability-path work
    (Lin, Sheng and Goel 2021) and accuracy by range on forecasting platforms (grey literature).
- **Attacks.** (2) Sky and festival dates fall on any weekday. An upload on the event day therefore leaves a
  single-weekday habit about six times in seven by construction. "Off-habit" is informative only through the split of
  added against shifted uploads, and a null that redraws event dates on the same creator's calendar. Put this into
  r3-P29's band before any count.
- **Final wording (N19).** Whether uploads anchored by date alone to sky or festival events (a hashed event table, no
  title words) leave each creator's weekday habit more often than its other uploads, was not found in 12 member
  searches (summed) or in 9 + 6 = 15 attacker searches. The design splits added from shifted uploads, fixes a lead-lag
  rule for ritual against search timing in advance, and reads off-habit against a null that redraws event dates.
  Closest:
  - weekly and calendar rhythms of online activity (Golder, Wilkinson and Huberman 2007; Leypunskiy et al. 2018; Al
    Shehhi et al. 2017, 2019; Wood et al. 2017);
  - lunar phase and web searches (Otte et al. 2013);
  - search interest rising ahead of religious holidays and concentrated at an eclipse (Dewi et al. 2026; Javed et al.
    2026);
  - religious time online (Thomas et al. 2019);
  - when-to-post (Spasojevic et al. 2015);
  - creators aiming at search (Hödl and Myrach 2023).

  Not found means only that.
- **N20.** The wording is unchanged except the count, which reads "or in 21 + 3 = 24 attacker searches".

### den-mat-n1 (N21): narrowed

- **Searches.** 9 counted.
- **Evidence.** The deposited sentence "What is new is the timing of the freeze" no longer holds.
  - **Metaculus**, the tezos-timestamping-validator repository, https://github.com/Metaculus/tezos-timestamping-validator.
    The attacker opened the README: "Everyday we take all standing MP/CP and create Merkle Tree", and the "Resulting
    root of the tree is timestamped on Tezos by TzStamp service". A platform freezes many forecasters' standing
    forecasts each day under an external time stamp, before they resolve. These are posed questions, not statements
    taken from recordings. The helper had listed this source as an unverified lead; the attacker opened it.
  - **Jyotish 2026**, "Sealed Before the Event: A Publicly Verifiable, Bitcoin-Anchored Forecast Record of 92 Graded
    Outcomes ...", F1000Research 15:1322, https://doi.org/10.12688/f1000research.186752.1. The attacker re-opened the
    article page: "Every forecast was published verbatim before its window"; "each text was canonicalised,
    SHA-256-hashed into a manifest, and anchored to the Bitcoin blockchain via OpenTimestamps"; unfalsifiable calls
    "retained in the manifest but held out of the scored denominator". This is one forecaster's own forecasts,
    self-graded.
  - **Kriger 2026**, "How Much Did Nostradamus Know? Information Theory and a Blind Test of Prophecy", Zenodo
    preprint, https://doi.org/10.5281/zenodo.24080918. The attacker re-opened the record: "genuine quatrains,
    quatrains spliced from lines of different quatrains, and newly composed pseudo-quatrains" fit history equally
    well, under "three double-blind experiments". These are placebo prophecies, judged blind, in one historical
    corpus.
  - **Galarnyk et al. 2025**, VideoConviction, arXiv:2507.08104 (abstract): recommendations taken from many creators'
    videos and scored after the outcomes.
  - **White et al. 2018**, Methods in Ecology and Evolution, https://doi.org/10.1111/2041-210x.13104 (passage):
    "Archiving serves as a form of pre-registration for model predictions".
  - **Correction to the helper's reading.** The 2009 prediction-tracker site (Wrong Tomorrow) accepted predictions
    that had already resolved, as the comments on the LessWrong post of 2 April 2009 note. It does not show a freeze
    before the event, and it is not used here.
- **Attacks.** (2) The descriptive half (a small resolvable share) is predicted by every account. (3) The forecast
  class is below its floor, and the checkability fields failed their two-model gate.
- **Final wording (N21; shared with den-meth-n2).** A ledger of model-coded dated statements from many speakers'
  naturally occurring public recordings, hashed with an external time stamp before the windows mature, with a
  resolvability class fixed from text alone and window-shifted and swapped placebo statements of the same speakers,
  was not found in 16 member searches (summed) beyond the registry's 20, or in 4 + 15 = 19 attacker searches. Its
  parts exist apart:
  - a platform's daily external time stamp of many forecasters' standing forecasts on posed questions (Metaculus,
    grey literature);
  - one forecaster's own forecasts hashed and anchored before their windows, with unfalsifiable calls held out of the
    score (Jyotish 2026);
  - placebo prophecies judged blind against history in one historical corpus (Kriger 2026, preprint);
  - recommendations taken from many creators' videos and scored after the outcomes (Galarnyk et al. 2025; Lalwani et
    al. 2026);
  - forecasts archived before their data as a pre-registration (White et al. 2018).

  Closest otherwise:
  - a retrospective, person-checked audit of published psychic predictions with "too vague" and "expected" classes
    (GAPPP, grey literature);
  - the premonition bureaus of the late 1960s;
  - forecasting benchmarks frozen before answers exist (Karger et al. 2024);
  - automated resolution (Bosse et al. 2026);
  - predictions mined from social media (UzZaman et al. 2012; Swamy, Ritter and de Marneffe 2017).

  What remains is the combination: a third party's freeze of statements taken from many speakers' recordings and
  coded by a model, before their windows mature, with a resolvability class fixed from text alone and placebo
  statements drawn from the same speakers. The scoring is not new, and nor is the timing alone. Not found means only
  that.

### den-meth-n2 (N21): narrowed

- **Searches.** 6 counted, distinct from den-mat-n1's.
- **Evidence.**
  - Lalwani et al. 2026, "YouTubers and Stock Returns", SSRN. Read only as an abstract in a Consensus record: "We use a
    Large Language Model (Gemini) to extract stock recommendations from YouTubers' videos across nine countries".
    Model extraction from many creators' videos, scored after the outcomes.
  - Hamilton College 2011, executive summary, https://hamilton.edu/pundit (read by the helper): pundits' predictions
    were sampled from columns and transcripts and checked afterwards; "conditional predictions were more likely to
    not come true".
  - Plus the sources under den-mat-n1.
- **Attacks.** Selection decides the ledger: quotas of newest uploads, and deletion before the listing day.
- **Final wording.** The N21 wording above. The helper's wording left out the placebo clause; it is kept here, so the
  wording is not broadened.

### et-n3 (N22): survives

- **Searches.** 6 counted.
- **Evidence.** No within-creator comparison of how often contact-event and world-event statements are bounded in
  time. Qualitative accounts of turning a dated physical event into a spiritual one were added: Aveni 2016 (review
  abstract) and Wojcik 2022 (abstract).
- **Attacks.**
  - (2) Contact events have no outside calendar to anchor to, so "contact bounded less often" is expected from the
    event types alone.
  - The cue strata that type contact statements ("when you are ready") may carry unboundedness themselves, so the
    measure can build the contrast.
- **Final wording (N22).** Inside a ledger frozen before maturity, a within-creator comparison of how often
  contact-event and world-event statements are bounded in time, with energetic predicates and date refusals kept out
  of scoring, was not found in 9 member searches or in 1 + 6 = 7 attacker searches. Closest:
  - one contactee group observed before its date (Festinger, Riecken and Schachter 1956, disputed by Kelly 2025);
  - one group's later landing date (Tumminia 2005);
  - a review of seventeen studies (Dawson 1999);
  - qualitative accounts of movements turning from a dated physical event to a spiritual one (Aveni 2016; Wojcik
    2022);
  - the verdict classes of a retrospective audit of psychic predictions.

  The contact-cue strata must not themselves carry unboundedness. Not found means only that.

### emic-n2 (N23): narrowed

- **Searches.** 6 counted.
- **Evidence.** **Zong, Ritter and Hovy 2020**, "Measuring Forecasting Skill from Text", ACL 2020, arXiv:2006.07425,
  https://arxiv.org/abs/2006.07425. The attacker re-opened the abstract: "We present a number of linguistic metrics
  which are computed over text associated with people's predictions including: uncertainty, readability, and emotion".
  In passages read by the helper, they estimate "the proportion of uncertain statements made by each forecaster",
  over many forecasters. That is a many-speaker count of the uncertainty that forecasts carry when they are written.
- **Attacks.** (2) The measure partly builds the excess. A sentence is coded as a forecast because it carries future
  modality and windows, so the families for time qualifiers and probability are more frequent in forecast sentences
  by construction. Report the excess only for families disjoint from the forecast detector's cues, and publish the
  detector's cue list with the hash.
- **Final wording (N23).** A prospective, many-speaker count of the qualifier clauses that dated forecasts carry at
  speaking time, against matched non-forecast sentences, was not found in 7 member searches or in 2 + 6 = 8 attacker
  searches.
  - A many-forecaster count of uncertain statements in forecast texts is theirs (Zong, Ritter and Hovy 2020). What
    remains is a count fixed before the windows close, of named qualifier families in dated spoken forecasts, against
    matched non-forecast sentences of the same recordings, for families disjoint from the forecast detector's cues.
  - Closest otherwise: the retrospective concepts of spiritualization (Melton 1985, via Dein 2001) and the prevention
    theodicy (Robertson 2014); a review of adaptation after failure (Dawson 1999); hedging in institutional
    projections (Lejeune 2018); modal verbs of possibility in horoscopes (Jalolova 2025); the "too vague" class of a
    retrospective audit of psychic predictions.

  Not found means only that.

### occult-n4 (N24): survives (the helper proposed "narrowed")

- **Searches.** 6 counted.
- **Evidence.**
  - **Meder, Nguyen and Gravel 2016**, "The apocalypse on Twitter", Digital Scholarship in the Humanities 31(2). Read
    as an abstract in a Consensus record; the publisher pages refused connection. It covers 52,000 Dutch tweets from a
    week before to a week after the 2012 date.
  - Counting later mentions of past years is culturomics' (Michel et al. 2011). Only a news summary was read.
  - The deposited NOTE had already conceded the many-speaker computational part (Phadke, Samory and Mitra 2021). The
    claimed part, framing years later against matched control years and by voice, is untouched.
- **Attacks.** (2) A prophesied year is a topic of prophecy by definition, so prophecy frames near it exceed those
  near control years even without any reframing. Match control years on topic (other heavily discussed years in the
  same talks).
- **Final wording (N24).** A multi-speaker comparison of how passed prophesied target years are framed years later,
  against control years with matched anniversary demand and topic salience and by voice, was not found in 6 member
  searches or in 3 + 6 = 9 attacker searches. Closest:
  - computational measurement of self-disclosed dissonance after unmet expectations (Phadke, Samory and Mitra 2021);
  - a many-speaker reading of tweets a week either side of a prophesied date (Meder, Nguyen and Gravel 2016);
  - counts of later mentions of past years as collective memory (Michel et al. 2011);
  - the spiritualization thesis from cases (Melton 1985);
  - adaptation strategies (Dawson 1999);
  - the archival critique of the 1956 study (Kelly 2025);
  - collections of leaders' responses to a failed election prophecy (press reports).

  Cue families only, until coding is funded. Not found means only that.

### occult-n1 (N25): survives

- **Searches.** 7 counted, including one German-language query.
- **Evidence.** No count of dated vocabulary layers in spoken channelling. New closest work:
  - **Erdentug and Musayeva Vefali 2018**, Discourse, Context & Media 24, https://doi.org/10.1016/j.dcm.2018.01.009
    (abstract): "old" and "past" in one New Age teacher's talks.
  - **Pinto, Pinho and Pratas 2025**, arXiv:2511.23056 (abstract): lexical dating of texts, with decade accuracy of
    26.1%.
- **Attacks.** (2) and (3) A synchronic corpus cannot show transmission. Dating below the century is coarse, and older
  layers are also more formal registers.
- **Final wording (N25; shared with et-n1).** A creator-level, placebo-controlled count of the co-presence of
  historically dated vocabularies (graded by secondary sources) in spoken channelling, with a recording-level contrast
  between claimed-voice recordings and the same creators' own-voice talks, was not found in 14 member searches
  (summed) or in 2 + 12 = 14 attacker searches. Closest:
  - qualitative genealogies of single esoteric concepts (Zoehrer 2025) and of lineages (Helland; Wojcik 2022;
    Partridge 2004; Wilson 2019);
  - a between-corpus embedding comparison of channelled messages with a ufological archive (Wahbeh, Glick et al.
    2026);
  - an embedding study of three channellers' structured trance interviews (Wahbeh and Glick 2026);
  - a corpus reading of "old" and "past" in one New Age teacher's talks (Erdentug and Musayeva Vefali 2018);
  - diachronic word-embedding methods (Hamilton et al. 2016);
  - lexical dating of texts by period features (Pinto, Pinho and Pratas 2025);
  - interviews with creators of algorithmic conspirituality content (De et al. 2025).

  Layers are periods of first currency, never descent, and are read against a register-matched placebo. Not found
  means only that.

### et-n1 (N25): survives

- **Searches.** 5 counted.
- **Evidence.** Wahbeh and Glick 2026, Journal of New Paradigm Research, https://doi.org/10.1080/02604027.2026.2656120
  (record read by the helper): three channellers and sentence embeddings, with no dating and no comparison with the
  own voice.
- **Attacks.** (2) The claimed voice is the more formal register, so "older layer in the claimed voice" is also
  predicted by register. A register-matched placebo is required.
- **Final wording.** The N25 wording above.

### et-n2 (N26): narrowed

- **Searches.** 7 counted.
- **Evidence.** **Silva 2024**, "UFO, universe, reptilians and creatures communities on Brazilian Telegram: when the
  sky is not the limit and conspiracy theories seek answers beyond humanity", arXiv:2409.02117,
  https://arxiv.org/abs/2409.02117. The attacker re-opened the abstract: "UFO communities act as gateways for theories
  about reptilians, connecting narratives of global control with extraterrestrial beings". The helper read the
  methods passages: invitation-link networks, and topic overlap with BERTopic. There is no null model and no split by
  the aliens' valence. The fusion question for these very themes has been asked.
- **Attacks.** (2) Fusion is the expected finding in communities sampled from the conspiracy side. Here it is
  informative only if the null is beaten among channelling creators selected without reference to conspiracy, with
  the lists matched in prevalence.
- **Final wording (N26).** A fixed-margin co-use test of the adversarial and federation vocabularies, across and within
  channelling creators and stratified by audience size and economy type, was not found in 6 member searches or in 2 +
  7 = 9 attacker searches.
  - Whether UFO themes and reptilian or global-control themes travel together has been asked of Telegram conspiracy
    communities, through invitation links and topic overlap, with no null model and no split by the aliens' valence
    (Silva 2024). Only the fixed-margin null, the split by valence and the channelling creators are this corpus's.
  - Other closest: millennial conspiracism (Robertson 2016); stigmatized knowledge (Barkun 2015); conspirituality
    (Ward and Voas 2011); the turn to malevolent aliens (Partridge 2004); QAnon influencers' content (Conner 2023);
    users moving across conspiracy topics (Bessi et al. 2015); authority and monetisation cues co-occurring in health
    videos (Zarei et al. 2025).

  Not found means only that.

### et-n4 (N27): survives

- **Searches.** 5 counted.
- **Evidence.** The member's own suggested check was run. The qualitative companion paper (Wahbeh and Glick 2026,
  https://doi.org/10.1080/02604027.2026.2656119, abstract) and the comparison with the archive report no split by
  voice or by kind of disclosure in their abstracts. A full-text read remains open.
- **Attacks.** A5 stands: the business account predicts both placements.
- **Final wording (N27).** A within-speaker comparison of disclosure talk between the claimed and the own voice,
  separating institutional from consciousness-based disclosure, position-matched and read against a three-way
  prediction table (meaning, news-hook and attribution-shield accounts), was not found in 5 member searches or in 3 +
  5 = 8 attacker searches. Closest:
  - a between-corpus divergence of channelled messages from a ufological archive (Wahbeh, Glick et al. 2026);
  - a thematic analysis of prospectively collected channelled sessions, with no split by voice (Wahbeh and Glick
    2026);
  - disclosure events and conspiratorial talk on two forums (Bastos et al. 2026);
  - reactions to a 2023 hearing (Lomas 2024);
  - speech reporting in one medium's session (Wales 2009).

  Not found means only that.

### emic-n1 (N28): survives

- **Searches.** 7 counted.
- **Evidence.** No quantitative study codes political or control content by speaking entity. New qualitative closest
  work, abstracts via Consensus:
  - **Tomlinson 2025**, JRAI: mediums "take responsibility for the expressions they produce" yet "deny
    responsibility at the same time".
  - **Hüwelmeier 2019**: spirit writing and politics.
  - **Coker 2021**: prophetic authority in election talk.
- **Attacks.** A5, as for N27. The register is rare in each voice.
- **Final wording (N28).** A within-creator contrast of control vocabulary and named actors between the claimed and
  the own voice, in position-matched body text across many creators and read against a three-way prediction table,
  was not found in 8 member searches or in 3 + 7 = 10 attacker searches. Closest:
  - discourse analysis of millennial conspiracism in a few authors' texts (Robertson 2016);
  - spirits as political actors in possession and spirit writing (Bubandt 2009; Hüwelmeier 2019);
  - mediums' simultaneous claiming and disowning of responsibility (Tomlinson 2025);
  - appeals to prophetic authority in election talk (Coker 2021);
  - conspiracy and monetisation cues co-occurring in videos (Zarei et al. 2025).

  Not found means only that.

### emic-n4 (N29): survives

- **Searches.** 6 counted.
- **Evidence.** **Alemany Oliver 2020**, Journal of Business Ethics, https://doi.org/10.1007/s10551-020-04612-3 (passages
  read by the helper). It is a narratological reading of 28 written business-related conspiracy narratives, which
  "almost always awaits an end that only an external and legitimate entity can give". It names the outside-agent
  half as a reading. It has no class for inner means and no count over speakers. The deposited NOTE had already said
  "named in part".
- **Attacks.** (2) An outside agent is the default ending of conspiracy narratives, so a high outside-agent share is
  predicted. The informative cells are the share of inner means and how it is spread across creators and economy
  types.
- **Final wording (N29).** A coded split of how the adversary's threat is resolved (by inner means or by an outside
  agent) across many channelling creators' speech, crossed with economy type, was not found in 6 member searches or
  in 2 + 6 = 8 attacker searches. Closest:
  - the optimism-pessimism tension of conspirituality and its awakened-paradigm answer (Ward and Voas 2011; Asprem
    and Dyrendal 2015);
  - commentary on passive waiting for rescue (Zuckerman 2019);
  - a narratological reading in which conspiracy narratives await an external "deus ex machina" (Alemany Oliver
    2020);
  - affects ascribed to nature or to conspirators (Knasmüller et al. 2023);
  - an interview typology with optimistic change (Franks et al. 2017);
  - the turn from 2012 millennialism toward conspiracy in a few authors (Robertson 2014; Whitesides 2015).

  A lexical proxy only, until a stance read is funded; the inner-means share is the informative cell. Not found means
  only that.

### occult-n3 (N30): survives

- **Searches.** 7 counted, including one Portuguese-language query.
- **Evidence.** Klimo's typology can now be cited from the book itself (1987, chapter 6; full-text index snippet).
  Other closest work:
  - Brown 1997 contrasts the performances of trance and conscious channellers, qualitatively.
  - **Spindola-Rodrigues et al. 2022**, Frontiers in Psychology, https://doi.org/10.3389/fpsyg.2022.874720 (abstract
    and methods passage): mediums' self-described consciousness is recorded as a study variable, with no speech
    outcome.
- **Attacks.** Self-described mode is part of positioning. Mode groups below 5 creators print "cannot be answered".
- **Final wording (N30).** A description, on seen creators, of where a frozen voice code files self-described modes of
  mediation (full trance, conscious or blended, dictation, relay, received text read aloud) was not found in 5 member
  searches or in 2 + 7 = 9 attacker searches. Closest:
  - Klimo's typology (1987, chapter 6);
  - an ethnographic contrast of trance and conscious channellers' performances (Brown 1997);
  - mediums' self-described consciousness recorded as a study variable (Spindola-Rodrigues et al. 2022);
  - a validated measure of mediumship experiences (Maraldi et al. 2026);
  - a laboratory study and a survey of trance channellers (Wahbeh et al. 2019; Wahbeh and Butzer 2020);
  - Spiritualist taxonomies read as media theory (van Reenen 2026).

  Not found means only that.

### den-mat-n2 (N31): narrowed

- **Searches.** 6 counted.
- **Evidence.**
  - **Altabaa, Schnabel and Tomlinson 2026**, "Putting Transformer Theories to the Test", arXiv:2610.32104,
    https://arxiv.org/abs/2610.32104. The attacker re-opened the abstract: the authors "map out seven theories of
    transformer capability" and translate them into a common matrix of predictions. Table 2, in a passage read by the
    helper, marks "—: inapplicable", and counts each theory's matches "among cells with both a prediction and an
    outcome".
  - **Levy, Fedorenko and Gibson 2013**, Journal of Memory and Language, https://doi.org/10.1016/j.jml.2012.10.005
    (passage read by the helper): "—: theory makes no prediction; ✓(?): theory is vague".
- **Attacks.** (2) An account's silence share is set by whoever writes its column. With no practitioner seated, the
  filter column measures the writers' reading of the doctrine. The closed-designs row is silent by construction.
- **Final wording (N31).** A registry over more than two accounts of one observational corpus, written before each
  analysis runs, scoring each cell hit, miss or absorbed and printing each account's share of silent or both-ways
  cells beside a closed-designs row, was not found in 5 member searches or in 2 + 6 = 8 attacker searches.
  - A common prediction matrix over several theories, with inapplicable cells marked and each theory's agreement
    counted only over the cells where it predicts, is theirs (Altabaa, Schnabel and Tomlinson 2026). So is a results
    table that marks where a theory makes no prediction or is vague (Levy, Fedorenko and Gibson 2013).
  - What remains is registration before each analysis, the absorbed class, the silent share printed for each account
    as a result, and an observational corpus.
  - Closest otherwise: adversarial collaborations between two theories (Melloni et al. 2023; Cogitate Consortium
    2025); multi-theory designs that state assimilation in advance (Corcoran et al. 2026; Ceci et al. 2026); a
    proponent-sceptic consensus design (Kekecs et al. 2023); fit against flexibility (Roberts and Pashler 2000);
    flexibility measures for formal models (Veksler et al. 2015; Villarreal et al. 2023); the empirical content of
    verbal theories (Glöckner and Betsch 2011).

  Every account, the market account included, must forbid cells. Not found means only that.

### den-soc-n4 (P32): survives (first wording)

- **Searches.** 6 counted. No attacker had read this claim before, not even its author, so the count starts at 0.
- **Evidence.** **Hua et al. 2022**, "Characterizing Alternative Monetization Strategies on YouTube", CSCW,
  https://arxiv.org/abs/2203.10143 (full-text passages, read by the helper).
  - Products and services sold by the channel form one class: "[PC] Sales of products/services by the channel".
  - That class rises with popularity: "the more popular the channel, the more likely it is to monetize in those ways".
  - It is link-based, has no split of one-to-one against scalable offers, and does not ask whether the free content
    performs the paid product.

  Barzen and Göpfert 2026 (abstract) study credibility work for a paid service that cannot be verified.
- **Attacks.**
  - (2) The measure builds it. If a creator's only paid service is a session of the same act, every offer is
    "congruent" whatever the voice. The congruence share needs a per-creator denominator from the offer menu: creators
    who offer both kinds.
  - The audience gradient is the generic curve of the creator economy (Hua et al. 2022). On its own it cannot separate
    a demonstration funnel from selection or survivorship.
- **Final wording (P32).** A within-creator test of sample-to-offer congruence was not found in 7 member searches or in
  0 + 6 = 6 attacker searches. The test asks whether recordings presenting a claimed non-human voice carry a
  pay-or-enrol ask at least as often as the same creator's own-voice talks, and whether their offers are more often
  the service they demonstrate. It is computed among creators whose offers include both kinds, with the audience-size
  gradient of one-to-one against scalable offers read against selection and survivorship, as offers, not income, in
  this platform-surviving roster. Closest:
  - a link-based taxonomy of alternative monetisation, in which product and service sales form one class that rises
    with channel popularity (Hua et al. 2022);
  - offsite monetisation of conspiracy channels (Ballard et al. 2022);
  - monetisation cues in descriptions (Bertaglia et al. 2024);
  - interview studies of tarot readers' and channelling practitioners' entrepreneurship (Gregory 2018; Hulkkonen
    2021);
  - credibility work on the websites of a paid service that cannot be verified (Barzen and Göpfert 2026);
  - Spiritualism's paying audiences (Natale 2016);
  - free-to-paid spillovers in online health consultation (Liu et al. 2024; Ma et al. 2022).

  Not found means only that.

## 4. The main narrowing sources, and who opened them

| Source | Narrows | Opened by the attacker |
|---|---|---|
| Munot and Nenkova 2019, https://doi.org/10.18653/v1/N19-3003 | N01 | abstract page (the helper read the full text) |
| Feng et al. 2026, arXiv:2601.20913 | N07 | abstract |
| Zhou and Lin 2026, arXiv:2608.20607 | N07 | abstract |
| Pethe et al. 2025, https://doi.org/10.1109/ICSC64641.2025.00036 | N13 | full-text passages |
| Li and Peñaranda Valdivia 2022, https://doi.org/10.1145/3527188.3561927 | N17 | abstract (Crossref record of the preprint; full text 403) |
| Metaculus timestamping repository, https://github.com/Metaculus/tezos-timestamping-validator | N21 | README |
| Jyotish 2026, https://doi.org/10.12688/f1000research.186752.1 | N21 | article page (first 100,000 characters) |
| Kriger 2026, https://doi.org/10.5281/zenodo.24080918 | N21 | Zenodo record |
| Zong, Ritter and Hovy 2020, arXiv:2006.07425 | N23 | abstract (the helper read passages) |
| Silva 2024, arXiv:2409.02117 | N26 | abstract (the helper read passages) |
| Altabaa, Schnabel and Tomlinson 2026, arXiv:2610.32104 | N31 | abstract (the helper read passages) |
| Levy, Fedorenko and Gibson 2013, https://doi.org/10.1016/j.jml.2012.10.005 | N31 | not re-opened (passage read by the helper) |

Sources that were re-opened but do not narrow a claim:
- Singh, Davari and Mashhadi 2026 (RADAR) and Halterman and Keith 2025: closer method instances for N04.
- Sousa and Pires 2023: N11, a closer instance.
- Terpstra et al. 2023, Sakib et al. 2026 and Tanner et al. 2023: N02.
- Kruse 2017: N15.

## 5. Not opened, so not counted as refutations (for the lead)

- **llm-n4.** Williamson, Xi and Breyer 2012, Educational Measurement: Issues and Practice 31(1), and Wind and Xu
  2024, https://doi.org/10.4324/9781003397618-23. Automated-scoring monitoring may already cross engine versions with
  new examinee cohorts. This is the one open risk to N06.
- **speech-n4.** Alvarado 2010, Journal of Scientific Exploration 24(2). Historical reports of heavy breathing at
  trance onset; the PDF returned 404.
- **N21.**
  - Axial Seamount eruption-forecasting experiment with SHA-256-hashed forecasts, https://arxiv.org/pdf/2511.06128.
  - Foresight Arena, an on-chain commit-reveal of AI forecasts, https://arxiv.org/pdf/2605.00420.
  - Emery's annual tallies of tabloid psychic predictions (CFI PDFs).
  - PunditTracker (2013).
- **N27.** Kneis 2026, Mediatization Studies, https://doi.org/10.17951/ms.2025.9.119-130 (UAP disclosure discourse).
- **P32.** Zhang et al. 2026, HICSS, https://doi.org/10.24251/hicss.2026.704 (free against paid consultations).
- **N16.** An article on a temple medium beside an "impresario" who interprets the god's words,
  https://journals.sagepub.com/doi/10.1177/0097700410372921.
- **N15.** The Continuum chapter "To Perform Possession and to be Possessed in Performance: The Actor, the Medium and
  an 'Other'" (2010), https://doi.org/10.5040/9781472549365.ch-012.

## 6. What the lead must decide

1. **Accept or relabel the verdicts.** The class rule is in section 1. Three helper "narrowed" labels became
   "survives" (den-meth-n3, den-meth-n4, occult-n4), because the part each claims did not change.
2. **N21 and the registry's N3.** The programme's 3.3 and ruling 13's addendum say the registry's N3 novelty is "the
   timing of the freeze only". That no longer holds: a forecasting platform has stamped its standing forecasts on a
   public chain every day, and one forecaster sealed his own forecasts before their windows. The addendum should use
   the N21 wording of section 3: freezing statements taken from many speakers' naturally occurring recordings, coded
   by a model, with a text-only resolvability class and placebo statements of the same speakers.
3. **N13 and `related.tex`.** The audiobook literature on narrator against character (Pethe et al. 2025; Michel,
   Epure and Cerisara 2025) is the other discipline's name for speech-n3's design. It belongs in related work beside
   Wahbeh et al. 2019.
4. **N17 count.** The deposited wording says "10 attacker searches", while its SEARCHES field lists 10 (css-n2) plus 3
   (den-soc on emic-n3). This file writes 10 + 12 = 22. If the 3 are counted, write 25.
5. **N19 and N20.** den-soc-n3 has no wording of its own. Its timing half takes N19 (15 attacker searches); its lead
   half takes N20 (24). The construction point (an event-day upload is off a one-weekday habit about six times in
   seven) should go into r3-P29's band before any count.
6. **P32.** This is its first surviving wording. The denominator for congruence ("creators whose offers include both
   kinds") is a method change that den-soc should accept or answer.
7. **Preconditions from the attacks.** Record them in the relevant prespecs before any run:
   - llm-n2: whether the labeller's input carried decoder segment breaks;
   - speech-n1: phase against conditioning context;
   - llm-n3: a covariate for predicate recurrence;
   - occult-n2: inclusive against exclusive "we";
   - emic-n2: a forecast detector disjoint from the counted qualifier families;
   - occult-n4: control years matched on topic;
   - et-n1 and occult-n1: a register-matched placebo;
   - den-mat-n4: the declared genres fixed before collection.
8. **Bibliography (ruling 13).** Every work newly named in section 3 must be checked by key before any novelty
   sentence prints. Works read only as an index abstract or record are marked in section 3; the strictest choice is
   to drop them from printed wordings until they are opened.
9. **K1 is unchanged.** Whether pipeline checks (N02, N03) earn a novelty sentence at all is still the lead's
   decision.
