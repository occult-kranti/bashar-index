<!-- Public copy of the private `stored-facts.md`, made 2026-11-27 under the lead's decisions 140.7 and 141: every private path is replaced by a neutral description, and byte sizes, file counts not printed on main and an unpublished decision reference are removed; after the independent check, one constant of a private code is dropped and one cross-reference names the programme. Nothing else differs. The original's SHA-256 is in `hash-record.md`. -->
# Deposit 5, part 1: the four outcome-free stored-fact checks (decision 131.7)

Written 2026-11-27 from 10:32Z to 10:49Z (UTC, from `date -u`) by the deposit-5 list agent, a model agent working for the
project lead (not a person). Brief: the lead's brief to the list agent, part A. No person checked this file.

Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**How the answers were found.** From code, file listings (names and sizes only) and published metadata. No transcript,
label, ledger row, feature value, audio file or outcome table was opened. No value of any outcome field was read for these
checks (two incidental views of values already printed on main are disclosed at the end). Hashes are SHA-256 of the bytes
read: "main:" means the file at origin/main 3e141f8; "archive:" means a file in the project's private run folder (its path is not published).

---

## 1. Are TIME's year roles rule-based or model-coded?

**Answer: model-coded.** The year tokens are found by rule; the role of each token is model-coded.

- **Hits, by rule.** TIME's hits are matches of RX's frozen time sub-patterns (year, month, season or festival, bounded
  span, astronomical, digit date, vague future, deep time). A year token is a match of the year sub-pattern.
- **Roles, by model.** Each hit gets one role (forecast, logistics, calendar or sky, biography, deep time, other) from the
  small model. The middle model re-read 600 hits, and the small model ran once more as a repeat. The
  codebook's development rounds used development creators only. Not checked by a person.

**Sources.**

| File | SHA-256 | What it shows |
|---|---|---|
| archive: TIME's run code, `time_run.py` (docstring, constants) | `d1ced0b55d5922be26863e7c872967abb6f6d87f24efd6efb56624ea466ddb7e` | hits from RX's frozen sub-patterns; one role per hit by the small model; middle model on 600 hits; one repeat run; development rounds on development creators only |
| archive: TIME's frozen codebook record (hashed, not opened) | `9b101ab7f2973252c3ba9d72ceba7676b889ca61db94f2e0854158d4685a0b7d` | the frozen codebook record |
| main: `et-channelers/research/analysis-experiments-2026-11-20/exploratory-reporting-plan.md` (row TIME) | `061bab3303a03951a57e2f05f58ca3ee86bbdba29db637117831715b6acf3c7c` | "role shares under both readers"; middle-model re-read; hold-out pass TIME-H |
| main: `.../results/exploratory-2026-11-21/README.md` (status row TIME-H) | `7489b5becabbdcd4bdc5f35548f0f1f77b56fba4cbc1c0499c5edff17ee740c2` | "the time-role reading needs model calls" |
| main: `.../panel-third-round-2026-11-22/step3/r3-P40/prespec.public.md` | `d610f4be826c42ce89874052e844c6b8b50364db7612df1f7ab14e4ccdf355ab` | "TIME's roles are model-coded and not checked by a person"; "TIME small-model role" |

**Not on main.** TIME has no published README or code on main. The plan row, the status row and r3-P40's public
prespecification are its published description. The code above is private and is cited by hash.

**Bearing on f4-Q04.**
- A row that uses only the rule-found year tokens and deposit 4's rule-defined classes is a label-free count. These are
  class 1, family A, family B and the corrected class 3.
- Any row that reads TIME's role is model-coded. It carries the tuning-exposure note and the private guard (the card's
  rule). r3-P40's biographical reference row is one such row.
- Which f4-Q04 rows read the role is for deposit 5's f4-Q04 entry to state.

---

## 2. Did the per-recording edge classes (r3-P11 / r4-P03) survive the deletion of the audio caches?

**Answer: yes, for what is stored per recording. The edge classes are not a stored per-event label.**
- **The features survive.** All 895 per-recording feature summaries are on disk. Their stored arrays include each 1-s
  block's frame counts by class outside recognized speech, and four values per unit edge.
- **r4-P03's flags survive.** They are per-boundary environment-change flags.
- **Not stored.** No file holds a per-event class such as "session join" or "music-bed onset".
- **The deletion.** A later step deleted the audio caches; its deletion record names no files.
  Nothing that the entries' code reads is missing from the listing below.

**Listing** (2026-11-27 about 10:40Z; the third panel's private audio folder in the archive). Which stored files are present:

| Stored file | Present? | What the code says it holds |
|---|---|---|
| the per-recording feature files (one per recording) | present, one per processed seen recording (895) | One per processed seen recording, written by `pass_audio.py` through `features.save`. Arrays per `features.py`: `cls` (counts of frames outside recognized speech in 9 classes, "music-like or sustained sound" among them, per 1-s block); `edge_jump`, `edge_med`, `edge_hf`, `edge_ds` (per unit edge: largest level jump in the gap window, its local median, high-band spike, digital-silence share); also `adm`, `act`, `voi`, `ds`, `clip`, `osr`, `lv10`, `lv50`, `lv90`, `flat`, `hf`, `roll`, `mod`, `st_hist`, `int_s1`, `int_s2`, `tilt_s1`, `bg`, `bgn`, `nuclei`, `pauses`, `meta` |
| r4-P03's flag file | present | r4-P03's exclusion flags, which r3-P09 and r4-P15 use: one record (status, detected) per decidable voice boundary, keyed by recording and unit; with the threshold (kept private) and the null-class count. SHA-256 `2b316977c908062cdd2d1be781dc213bd2b6f2b5409a814d19d8764deb1098ab` (hashed, not opened) |
| r3-P11's summary file | present | r3-P11's summary (rows, carriers); not per recording |
| r4-P03's summary file | present | r4-P03's summary (threshold, counts); not per recording |
| the battery records | present | battery records (constructed-audio checks) |
| the decode scratch folder | present and empty | the decode scratch: audio is deleted after use, by design (`acommon.py`) |
| the label extract (one file per creator) | present, one file per creator (not opened) | the outcome-free label extract that the audio entries read (`acommon.py`); listed by name only |

**Code read.**

| File | SHA-256 |
|---|---|
| archive: the audio code, `features.py` | `7a06903b156930ec2042d3ccf6d89c639321af420dde67bcd49d2bdefc46f864` |
| archive: the audio code, `acommon.py` | `0ea79a48e7ba54d3aa2079051e388dd9e860035915dec524ab10eae52ba1fdc3` |
| archive: r4-P03's code, `analyse_p03.py` | `1a90151daada7e0d8b6a060fe0ba1bb193fc99c26101b83d2159a915199b4f72` |
| archive: r3-P11's code, `analyse_p11.py` | `4e2894fa0dfa0c59f7796bf2a7a3ac2b3bcd81148e43985817512111113355dc` |
| archive: the third panel's lead decisions, step 3 (the record of the cache deletion) | `368f9e6164cb41b6e1d67fa208947e78ce04f26ae770467cb257a3b5718ae474` |

**Bearing on f4-Q12(b).**
- **Music-like share.** The music-like share of frames outside recognized speech in the first and last minutes can be
  computed from the stored `cls` arrays. It needs no new audio pass, so the music row is class a, not a.2.
- **r4-P03's flags.** They detect an environment change at a voice boundary, with one threshold. They are not
  "session-join" or "music-bed" flags. The six splice classes appear only in the instrument battery (criterion 6). They
  are not stored as per-event labels.
- **The matched-edge baseline** can be recomputed from the stored features with r4-P03's hashed code.
- **Wording.** The programme's words "r4-P03's session-join and music-bed flags" therefore need the lead's wording: "r4-P03's
  environment-change flags".

---

## 3. Do the stored audio feature blocks hold an F0 level, or only F0 range?

**Answer: a relative F0 level and range, never an absolute F0 level.**
- **The pitch array.** The only pitch array is `st_hist`. Per 1-s block, it counts voiced frames in 48 one-semitone bins,
  from -24 to +24 semitones. The bins are relative to the recording's own median F0. The median itself is never stored
  (`instrument.semitones`: "the median itself is never kept"; `features.py`: "no absolute pitch").
- **What can be computed.** From these histograms, at a resolution of one semitone:
  - a block's or a window's F0 position against the recording's median (a within-recording relative F0 level);
  - its F0 spread (range).
- **What cannot be computed.** An F0 level in Hz, and any comparison of F0 level between recordings or creators.

| File | SHA-256 | What it shows |
|---|---|---|
| archive: the audio code, `features.py` | `7a06903b156930ec2042d3ccf6d89c639321af420dde67bcd49d2bdefc46f864` | the stored field list; `st_hist` "relative to the recording median (Tier 1)"; "no absolute pitch" |
| archive: the audio code, `instrument.py` | `a81a6161d4c73607242775bc7c7df3900ef01d673dade19dccfa3c552ed64de2` | `ST_BINS` (48 bins, -24 to +24); `semitones()`: F0 in semitones relative to the recording median, the median never kept |
| main: `.../panel-third-round-2026-11-22/audio/common/README.md` | `4bca2d7516281328a9bff150f9ae763b7e5afecd5f4d6f6a7b4ba0a455eb0f81` | "Tier 1: F0 in semitones relative to the recording's own median" |

**Bearing on RQ-A3 and f4-Q05b.**
- **What the stored blocks give.** A3's "relative F0 level" is a within-recording shift, so the stored blocks can give it at
  one-semitone resolution with no audio pass.
- **What needs a pass.** A row that needs finer resolution, or an absolute level, needs f4-Q05a's pass (the programme's section 4.2's
  "heavy only if the F0-level row needs f4-Q05a's pass").

---

## 4. Do CSS-10's economy types rest on model-coded title labels? (decision 129.9)

**Answer: not on the title labels.** CSS-10's types do not use LAB-T, the model-coded title instrument. They do rest on
other model-coded labels, and one of these reads titles among other page fields.
- **Offer classes, from two kinds of evidence:**
  - *Spoken asks.* Model-coded by the asks instrument (K1 objects, K2 and K5).
  - *Page text.* PT's cue families and link classes, which are rule-based cue counts, and PT's written asks, which are
    model-coded. PT reads seen descriptions, chapters, tags and titles.
- **Economy types** are built from these offer classes. A creator offers a class when it is found in 2 or more recordings.
  The types are client offers, audience offers and pooled residuals.
- **The plan's input line for CSS-10** is "Ask labels, META subscriber bands".

| File | SHA-256 | What it shows |
|---|---|---|
| main: `.../results/exploratory-2026-11-21/packages/CSS/README.md` (section "CSS-10") | `4c00a9b8c9311fa598ba4f89544452502c5c9340223330446b449d6c127c2530` | the two kinds of evidence, the 2-recording rule and the types |
| main: `.../exploratory-reporting-plan.md` (rows CSS-10, PT, LAB-T, LAB-A) | `061bab3303a03951a57e2f05f58ca3ee86bbdba29db637117831715b6acf3c7c` | CSS-10 from ask labels; PT's inputs include titles; LAB-T is the title-label instrument |

**Bearing on decision 129.9 (the lead decides).**
- **Literal reading.** Under the rule's wording ("no creator groups from model-coded title labels"), CSS-10's types are
  not barred.
- **Broader reading.** If the rule covers any model-coded label whose input includes titles, PT's written-ask part is
  covered.
- **Either way.** The stratum is built from model-coded ask labels whose prompts were developed on the development
  creators. Any stratum by economy type (f4-Q06's control; f4-Q12(e)'s economy crossing) therefore carries the
  tuning-exposure note.

---

## Rulings applied (decision 137, 2026-11-27 11:23Z; this section added at stage 3)

- **Fact 1 (TIME).** Every f4-Q04 row that reads TIME's role is a TIME-role row. It carries the tuning-exposure note and
  the private guard (decision 137.6). Rows built only from rule-found year tokens and deposit 4's rule-defined classes do
  not read the role.
- **Fact 2 (r4-P03).** Deposit 5 rewords the programme's "r4-P03's session-join and music-bed flags" (f4-Q12(b) and RQ-E2)
  as **"r4-P03's environment-change flags (one per decidable voice boundary)"** (decision 137.6).
  - The music row reads the stored frame-class counts ("music-like or sustained sound") in the first and last minutes. It
    is class a.
  - No row names a session join or a music bed as a detected class.
- **Fact 4 (CSS-10).** CSS-10's written-ask part rests on model-coded labels of page text, titles included. Under decision
  129.9 it may not define creator groups (decision 137.6).
  - An economy stratum (f4-Q06's control; f4-Q12(e)'s economy crossing) may be built from the spoken-ask part only, and it
    carries the tuning note.
  - The page cue families and link classes are rule-based cue counts, not labels. They may enter only as described rows,
    never as a grouping, unless the lead rules otherwise.

## Disclosures

- **Two incidental views of printed values.** While finding the TIME and CSS-10 descriptions, two lines on main that print
  published values were shown on screen: TIME's status row (its share of forecast-role hits) and one CSS deviation line
  (interval values). Both are printed on main. Neither is an outcome of any fourth-panel entry. Nothing was computed from
  them.
- **Third-panel lead decisions.** Part of the third panel's private lead decisions was read for the record of the cache
  deletion.
- **Label extract.** The label extract's file names were listed by name and size. No label file was opened.
- **Hashes without reading.** The env-flag file and TIME's frozen codebook were hashed, not opened.
- **No model or API call** was made. Nothing was committed.
