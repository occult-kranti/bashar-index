# r3-P18: a transparent footing locator and a disagreement diagnostic (prespecification)

Written 2026-11-26 from 14:07:22Z (UTC, from `date -u`) by the step-5 agent (a model agent working for the project lead;
not a person), before any outcome of this entry was computed. Shared rules: `../common/prespec-common.md`. Class a.1. The
two-coder check of 300 windows is class c and is not run.

**Tier X**: the locator has one data-tuned part (its hold length L), and 10 to 19 non-development creators are eligible
(the 11 voice-eligible creators; eligibility from word counts only). Two-fold cross-fitting (shared file, 0.4).

**Exploratory; not a test of H1-H10.** Voice labels model-coded, not checked by a person. The codebook and the labeller
read the same transcript, so their agreement is by shared design and is never validation; the value lies in the
disagreement cells and in a free locator for a wave. Agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. The codebook (closed; written now from ling-4's categories, blind to the corpus)

Patterns are sequences of plain lower-case tokens (punctuation removed, apostrophes kept); within one category the
longest match wins; a token counts once per side. Design text only: no count per pattern is ever printed.

**Claimed-side categories**
- K1 collective first-person self-designation: "we are the", "we of the", "we who are", "we who have", "those of us who",
  "our collective", "our civilization", "our civilisation", "our people", "our council", "our federation", "our home
  world", "our homeworld", "our ships", "our craft", "we come in peace", "we come from", "we are here to", "we have been
  watching", "we are watching over".
- K2 address to humanity as a group: "humanity", "humankind", "mankind", "earthlings", "human beings", "the human race",
  "the human collective"; with a pronoun: "you humans", "you on earth", "you of earth", "you as a species", "you as a
  collective", "your species", "your race", "your humanity".
- K3 second-person possessive with a noun of world, time or body: "your planet", "your world", "your earth", "your time",
  "your timeline", "your timelines", "your dimension", "your reality", "your linear time", "your physical", "your
  society", "your civilization", "your governments", "your scientists", "your sun", "your solar system", "your galaxy",
  "your vessel", "upon your earth".
- K4 reference to the speaker's body, role or vessel: "this vessel", "the vessel", "this instrument", "the instrument",
  "the one known as", "the one you know as", "the one called", "the channeler", "this channeler", "the medium", "this
  medium", "the host body".
- K5 reportative and perception frames: "they are saying", "they're saying", "they are showing me", "they're showing me",
  "i am being shown", "i'm being shown", "i am being told", "i'm being told", "they are telling me", "they're telling
  me", "they want you to know", "they want me to tell you", "they want me to say", "i'm hearing", "i am hearing", "i'm
  getting that", "what i'm getting is", "i'm being guided", "i am being guided", "they show me", "they tell me".
- K6 vocatives of greeting and leave-taking: "greetings", "dear ones", "dearest ones", "beloved ones", "beloveds", "dear
  hearts", "we greet you", "we bid you", "we leave you now", "we take our leave", "we will leave you", "farewell", "in
  love and light".
- K7 place deixis: "here on earth", "upon the earth", "on this planet", "on the earth plane", "the earth plane", "this
  plane of existence", "on gaia", "this planet earth".

**Own-side categories**
- O1 first-person narrative of the speaker's own life: "when i was", "i remember when", "i remember", "my husband", "my
  wife", "my partner", "my boyfriend", "my girlfriend", "my son", "my daughter", "my kids", "my children", "my mom", "my
  mother", "my dad", "my father", "my sister", "my brother", "my family", "yesterday i", "last week i", "last night i",
  "this morning i", "i grew up", "in my experience", "my own experience".
- O2 platform talk: "subscribe", "this video", "the description", "description box", "link below", "links below", "the
  link", "comments below", "comment below", "the comments", "notification bell", "the bell", "patreon", "livestream",
  "live stream", "the chat", "youtube"; with a possessive: "my channel", "my website", "my book", "my course", "my
  program".

**Variants.** *Full*: all categories. *Pronoun-blind* (ling's change 10: place deixis, vocatives and reportative frames
only, the variant a wave could carry): K4, K5, K6, K7 and the pronoun-free O2 patterns; every pattern holding a personal
pronoun or possessive of the first or second person outside a reportative frame is dropped (K1, K2's pronoun forms, K3, O1,
O2's possessive forms).

## 2. The locator (two-state rule; one tuned part)

Per recording, units in order; the state starts at own. A unit with more claimed-side than own-side hits sets the state to
claimed and its counter to 0; a unit with more own-side hits sets it to own; a unit with equal non-zero hits leaves it
unchanged; a unit with no hit, in the claimed state, adds 1 to the counter, and when the counter exceeds L the state
returns to own. Units in the claimed state are "locator claimed". **L** is chosen per fold from {0, 1, 2, 3, 5, 8, 13, 21,
34, 55, no limit} as the value whose creator-balanced locator-claimed share of words is closest to the label's claimed
share of words on the fitting side's units (ties: the smaller L). Fitting side: the other half's creators and T with a
claimed and an own unit inside the definition.

Units: recordings inside the primary definition, outside H1's excluded formats; units with a label side (claimed or own)
enter the tables (units with no side keep their place in the state sequence).

## 3. Rows

| Row | Statistic | Interval | Words |
|---|---|---|---|
| Q1 four cells | creator-balanced word shares of agreed claimed, agreed own, label claimed with locator own, label own with locator claimed (both variants) | t on creator means (described) | described |
| Q2 kappa | word-weighted Cohen's kappa per creator, creator mean (both variants) | t on creator means; class E named as nearest, "interval class not calibrated by r3-P30" | "agreement by shared design" (no reading) |
| Q3 uncued share (primary for the label's reliance) | share of label-claimed words in units with no codebook hit (either side, full codebook) within 2 units either side | t on creator means, uncalibrated | described; binned over creators (width 0.1, step 2's rule) |
| Q4 disputed cells by label-invisible features (primary for the diagnostic; pronoun-blind locator) | index s = (m_D - m_O) / (m_C - m_O), creator-balanced means over creators with 5 or more units in each of the three cells; unmatched and position-stratified (features centred within creator and recording tenth) | creator bootstrap, 1,000 draws, percentile 90%; uncalibrated | below |
| Q5 RX cue-span reference | r3-P03's K-cue locator (first opening cue to the next leave-taking cue): Q1 and Q2 | as Q1, Q2 | described |

**Label-invisible features** (per unit; neither instrument reads them): f1 recognized syllable rate (syllables per second
from the first word's start to the last word's end; units of 3 or more words); f2 mean recognizer word probability; f3
contraction share as transcribed (T0, H4's closed list; units holding an item); f4 a long pause before the unit (a gap of
1 s or more before its first word, seam rule). Directions fixed now from the registry, not from the agreed cells: f1
lower in the claimed voice (H1), f3 lower (H4); f4 higher (E5's described direction, not registered); f2 none (described
only).

**Words for Q4** (meas's conditions 1 and 2 met, condition 3 not: no feature validated outside the table; r3-P08 is
audio, later): interval wholly above 0.5: "the disputed units sit nearer the label's side (consistency of correlates)";
wholly below 0.5: "nearer the locator's side (consistency of correlates)"; otherwise "undetermined"; "not read (the agreed
cells differ against the registered direction)" if m_C - m_O has the other sign; f2 and f4 described only; fewer than 5
creators: "not computed (too few terms or creators)". Never "evidence", never "accuracy".

**Agreement by source type** (et): not computed (source families come from titles; on 11 creators every type would hold
fewer than 5). Relayed spans (ling): not separated (relayed voice alone is below the reliability floor).

Predictions deposited: none (deposit 2's cells for r3-P18 are silent). Nothing is scored.

## 4. Plot

A four-cell concordance panel (the label-invisible features' creator-balanced means in each cell, pronoun-blind
locator), and the uncued share over creators (bins of 5 or more creators).
