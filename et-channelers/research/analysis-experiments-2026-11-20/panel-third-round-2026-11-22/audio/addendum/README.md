# Audio addendum: the registered parts that waited for audio (the lead's decision 106.4)

Written 2026-11-26 (UTC, from `date -u`) by the audio-addendum agent, a model agent working for the project lead (not a
person). The parts of programme section 2.1 ("Also waiting for the Tier 0 ruling") that the audio pass's stored
per-recording summaries can serve, each run under its entry's registered text. No audio was read, copied or decoded; no
GPU lease was taken; no model or API call; nothing installed; no git commit; one worker.

**Exploratory; not a test of H1-H10.** Seen creators only. Voice labels are model-coded (the small model, the label of
record on seen recordings) and not checked by a person; comparisons between instruments are agreement, never accuracy.
Acoustic features describe the sound of these recordings (delivery and recording conditions), never a speaker's state or a
source; recovery was checked on constructed audio only (an upper bound); no person listened.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Order (times from `date -u`)

1. 18:20Z to 18:35Z: the registered text read (programme, decisions, deposits, steps 1 and 5, the seven audio entries'
   results); 18:35:43Z to 18:35:46Z: outcome-free counts from the label extract and the stored cue hits (no acoustic value).
2. **18:39:23Z: the prespecification hashed** (published as the redacted copy `prespec.public.md`, with
   `prespec-hash-record.public.md`; the hash is kept privately, step-1 decision 49 item i), before any outcome and
   before any acoustic value (the gate's included) was read for these parts.
3. 18:40:51Z to 18:44:16Z: r3-P01 E, r3-P17, r3-P15, r3-P13 computed (one worker each, in turn, under `run_locked.sh`);
   18:51:10Z: r4-P06 classed (no data).
4. 18:45Z to 18:57Z: publication, the lead's decision 109 applied (18:55Z), the nesting and band checks, the solvers.

## The parts

| Part | Status | Reading (only these words) |
|---|---|---|
| r3-P01 / r4-P01 part E (`r3-P01/`) | computed on all seen creators (unsplit); 40 to 49 creators | **undetermined**: recognized syllables per acoustic nucleus are lower in the claimed voice within recordings (beyond r3-P01's margin), but not at matched acoustic tempo; "no differential deletion" cannot be read (battery slope); shared normalisation stays untested |
| r3-P17 acoustic primary (`r3-P17/`) | not measurable acoustically in this corpus (A8) | every row not printed (A8) |
| r3-P15 / r4-P13 acoustic rungs (`r3-P15/`) | computed on all seen creators (unsplit); 30 or more per rung | **undetermined** (the composite cannot read a direction under the battery caps); described: delivery stays nearer the creator's own voice than other creators' claimed voices |
| r3-P13 exploration (`r3-P13/`) | tuning pool T only; not measurable acoustically in this corpus (A8) | every row not printed (A8); the registration condition is not met in this round |
| r4-P06 acoustic column (`r4-P06/`) | outcome-free, on r3-P26's map | **no input-disjoint pair** (voice); source family and asks not computable |
| r3-P14 acoustic part (`r3-P14/`) | not run | not run (needs a further audio pass; the read-like score is not computed per creator under the audio prespecification) |
| r3-P16 delivery rows (`r3-P16/`) | not computed | not computed (too few terms or creators) |
| GPU re-decode: r3-P02's grid rows, r3-P01's family C over the whole roster (`r3-P02/`) | not run | not run (decision 106.4) |

Predictions deposited for these parts: all silent, except r3-P16's "same as every other account" (no account is retired,
whatever the result: D23). Nothing is scored. Multiplicity: 56 primaries in the programme; if every true effect sat at half
its margin, about 2.8 readings beyond the margin would be expected by chance. A reading is never a finding.

## Shared rules (prespecification section 1)

- **Gate and A8:** a recording enters when its stored speech-to-background ratio is 25 dB or more. A part whose primary has
  fewer than 12 eligible creators after the gate prints "not measurable acoustically in this corpus" first and, under the
  lead's decision 109 item 1 (a rule that does not depend on the data), no estimate, interval or reading row and no figure.
- **Battery caps** (audio prespecification section 3; decision 106.3): rate rows never read "within the margin (B)"
  (criterion 1's slope); pitch-range rows read neither way (criterion 3); a composite profile reads a direction only if
  every feature in it may.
- **Split policy.** r3-P01, r3-P15 and r3-P17 are unsplit contrasts on all seen creators (deposit 2's split policy names
  them). Departure from the split policy's wording, accepted as the lead's decision 106.1: data-tuned parts (r3-P15's
  scalings, r3-P13's exploration) are fitted on the tuning pool T only, not built on exploration half A, and each reading
  is made once on all eligible creators. Reason: T sits on the exploration side and is never read for a split reading, so
  fitting on T alone keeps both halves out of every fit (decision 88's reading). **Limitation: half B is no longer sealed
  for the acoustic measures described here.**
- **Margins:** deposit 2's, except r3-P01's part E, which uses r3-P01's hashed tolerance-arm margin (0.0222).
- **Count forms:** gated sets print as bands; where an interval method is r3-P30's choice by count (r3-P01 E, r3-P15), the
  band lies inside one method's range (decisions 64 and 71).

## Privacy checks (all before the files were finalised)

| Check | Result |
|---|---|
| Nesting by membership against the steps 1 to 5 universe (the lead's `universe.py`), the audio entries' rebuilt sets, r3-P42's voice-eligible creators and each other (`common/code/nest_check_add.py`, `strict_check_add.py`; code, not published) | definitional and strict standards (decision 92.1), rechecked after the lead's decision 114: 0 bands of printed results left with 4 or fewer values (outcome-free bands of the prespecification narrow only to forms step 5 already prints for the same sets); decision 95.4: 0 addendum sets inside that set; decision 103: 0 pairs of the same measure nested 1 to 4 apart; 2 pairs 1 to 4 apart with a published set of a different measure, the addendum's side banded |
| Solvers and the identifier scan | summarised in `common/solver-results.md` (not published) |

## For the lead (2026-11-26)

1. The composite-profile cap (r3-P15): the addendum's prespecification applies the audio battery's caps to a distance over
   several features by requiring every feature to allow the direction; with F0 range in the profile the composite cannot
   read either way.
2. r3-P14's acoustic part is not run because the audio prespecification bars the read-like quantity per creator; a reduced
   row set without the score (acoustic pauses by clause slot, breaths at boundaries) would be a new registration.
3. r3-P01 part E reads undetermined because the two estimators disagree at the margin; with a calibrated nucleus detector
   (the revised instrument of decision 106.3) the tempo-matched row could decide it.

## Shared code (`common/code/`, not published)

| File | What |
|---|---|
| `addcommon.py`, `eligibility_add.py` | loaders and helpers; outcome-free counts (hashed with the prespecification) |
| `addpub.py`, `not_run.py`, `finalize_add.py` | publication helpers, the not-run tables, status files and staging |
| `nest_check_add.py`, `strict_check_add.py` | the nesting and band checks |
| `scans/` | copies of the release scan set pointed at the staged addendum (paths only changed) |

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Change by the lead's decision 113

2026-11-26T19:57:53Z (UTC, from the clock). No number changed. The prespecification is cited as its published, redacted
copy (`prespec.public.md`), hashed at 18:39:23Z (UTC), before any outcome; the hash is kept privately (step-1 decision 49 item i); its citation of the audio
prespecification's hash is replaced. CSV headers are rewritten by rerunning the code for headers only, and every hash in
`status.json` is refreshed; the originals are listed there under `not_published`.

## Change by the lead's decision 114

2026-11-26T20:13:50Z (UTC, from the clock). No number changed. The line on banded counts is corrected after the recheck; the solver summary and the code are named as not
published; the public prespecification replaces a phrase quoting an estimate the audio entries do not print and
words the standing rule generically; r3-P15's reference rungs print no interval (a fixed rule); r3-P16's
withheld row reads one label; every CSV header and contact log carries the half-B limitation of decision 106.1.
