# r4-P06 (carried by r3-P26), the acoustic column of the input-disjoint MTMM read (audio addendum)

Written 2026-11-26 (UTC, from `date -u`) by the audio-addendum agent, a model agent working for the project lead (not a
person), under the lead's decision 106.4. Prespecification: `../prespec.public.md` (published redacted), section 6 (hashed 2026-11-26T18:39:23Z).
Run 18:51:10Z; revised at 18:51Z (departure 1 below).

**Exploratory; not a test of H1-H10.** Outcome-free: no creator value, no correlation and no audio was read. The voice
labels that locate the stored acoustic features are model-coded and not checked by a person; agreement between methods is
agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What it asks

r3-P26 (step 1) placed every MTMM method on a map of the inputs it reads and counted convergence only over pairs that share
no input (Campbell and Fiske's independence condition); it printed the acoustic column as "not computable here (a.2)".
Once the audio pass exists, can an acoustic method of the voice construct be built from the stored features that shares no
input with a voice method of MTMM? "No input-disjoint pair" and "not computable" are permitted answers.

## How

Three codings of an acoustic method are classed against the twelve MTMM methods by r3-P26's class rule, unchanged
(`p26common.pair_class`, its file checked by SHA-256): (a) r3-P26's placeholder, a method reading voiced frames, recognizer
units and position only; (b) a voiced-frame method from the stored features (acoustic rates, F0 range); (c) a pause-tied
method from the stored features (meas's shared-channel cell). The stored features cover only label-admitted time and every
span is located by the small model's labels, so (b) and (c) also read the labels' inputs: the small model, the voice
codebook and through it the brand, and the vendor. (a) cannot be built from the stored features.

## Results

| Construct | Acoustic column's primary | Placeholder coding (not buildable) |
|---|---|---|
| voice | **no input-disjoint pair**: (b) and (c) are class C2 with the transcript-label methods, C4 with the rule method (the brand) and C3 with the page method (the vendor and the brand) | would be input-disjoint with the rule and page methods: not run (needs a further audio pass with a label-free admission rule and a label-free locator of the construct) |
| source family | not computable (the stored features hold no acoustic measure of this construct; class rows are formal) | - |
| asks | not computable (the stored features hold no acoustic measure of this construct; class rows are formal) | - |

**In words.** Every acoustic quantity the pass stored inherits the voice labels' inputs, so the acoustic column adds no
input-disjoint voice pair: on r3-P26's map, the acoustic instrument is independent of the transcript in measurement but not
in location (as r3-P08 says). An input-disjoint acoustic method would need a label-free admission rule that still processes
no third party's voice, and a label-free locator of the claimed voice (r3-P13's rule-located events are one candidate; they
read the brand through RX's J2 patterns, class C4 with the page method). No correlation is computed: none is needed for
these answers.

Predictions deposited: none (deposit 2's cells for r3-P26 and r4-P06 are silent); nothing is scored. Multiplicity: 56
primaries; if every true effect sat at half its margin, about 2.8 readings beyond the margin would be expected by chance.

**Split policy.** No creator is read here, so no tier applies. The addendum's departure from the split policy's wording,
accepted as the lead's decision 106.1 (data-tuned parts fitted on the tuning pool T only, because T sits on the
exploration side and is never read for a split reading), carries the limitation that half B is no longer sealed for the
acoustic measures described in the addendum.

## Departures (stated)

1. The prespecification (section 6) read the primary per construct from C5 pairs of any construct; the class rule makes a
   label-located acoustic method formally C5 with the asks rule method. An acoustic method measures delivery, a method of
   the voice construct only (meas's two audio columns), so source family and asks read "not computable" rather than
   "input-disjoint pair exists" (decided 2026-11-26 at 18:51Z, before any creator value; no data is involved).

## Files

| File | What |
|---|---|
| `public/data-r4-P06-acoustic-column.csv` | every coding against every MTMM method: class and shared inputs |
| `public/data-r4-P06-acoustic-reading.csv` | the acoustic column's primary per construct |
| `public/fig-r4-P06-acoustic-column.png`, `.pdf` | the class grid |
| `code/analyse_p06a.py`, `code/style.py` | the classing and the figure; style copied unchanged |
| `contacts.md`, `status.json` | contacts; every file's SHA-256 |

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Change by the lead's decision 113

2026-11-26T19:57:53Z (UTC, from the clock). No number changed. The prespecification is cited as its published, redacted
copy (`../prespec.public.md`), hashed at 18:39:23Z (UTC), before any outcome; the hash is kept privately (step-1 decision 49 item i); its citation of the audio
prespecification's hash is replaced. CSV headers are rewritten by rerunning the code for headers only, and every hash in
`status.json` is refreshed; the originals are listed there under `not_published`.

## Change by the lead's decision 114

2026-11-26T20:13:50Z (UTC, from the clock). No number changed. The CSV headers carry the half-B limitation of decision 106.1 (the code rerun for the headers only). The contact log carries the half-B limitation of decision 106.1.
