# r3-P57 / r4-P32: sample-to-offer congruence

Third-round panel programme, step 4 (class a.1), a description on seen creators; r4-P32 is carried here. Run on 2026-11-26
(UTC, from `date -u`) by the step-4 agent, a model agent working for the project lead (not a person). Prespecification
`prespec.md` with `../common/prespec-shared.md`, hashed 14:07:09Z before any outcome (`prespec-hash-record.md`).

**Exploratory; not a test of H1-H10.** Worded as the programme fixes it: "a funnel, whatever its age" (the free message and
the paid sitting predate the platform), "offers, not income", "in this platform-surviving roster". Voice, kind and asks
labels are model-coded and not checked by a person; comparisons are agreement, never accuracy. Offers and asks are described
neutrally, as the creators make them. Confirmation on fresh creators is class b (card b6).

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Tier and units

- **Tier X.** Eligible non-development creators (outcome-free: one or more claimed-voice recordings and one or more
  own-voice talks, both with asks labels): 10 to 19, printed as "11 and fewer than 5 more". Two-fold cross-fitting over the
  deposited halves; no parameter is fitted, so the estimate is the pooled estimate of the fixed rules over the eligible
  creators of both folds. Fold values are not printed; the tuning pool is not used.
- Claimed-voice recordings: the voice map's main kind "claimed voice"; own-voice talks: main kind "own-voice talk" (small
  model, the production map). Asks: the frozen asks instrument's final asks, any voice, at recording level. Client service:
  a pay-or-enrol ask whose object is a session or reading (CSS-10's client offer).

## Results in words

- **Ask half (P1, b6): undetermined.** The Mantel-Haenszel odds ratio of a pay-or-enrol ask in a claimed-voice recording
  against an own-voice talk of the same creator is 0.42 (90% creator-cluster bootstrap 0.10 to 1.34) with creator and
  length-tertile strata, and 0.64 (0.20 to 1.52) with creator strata only. Both intervals cross 0.8, so neither b6's
  non-inferiority (lower bound above 0.8) nor den-soc's retirement condition (upper bound below 0.8) holds. The share-based
  classes (25% or more claimed-voice words against none) give the same words (0.62, 0.20 to 1.85; 0.62, 0.23 to 1.30).
- **Congruence half (P2, b6): not computed (too few terms or creators).** Fewer than 5 eligible creators have a
  pay-or-enrol ask in both kinds of recording, so the client-service share cannot be compared within creator. The two
  brackets ('several' objects; either evidence, a session object or a written booking cue) rest on the same fewer than 5
  creators; the share-based sensitivity row has 5 to 9 creators but its shares are carried by fewer than 5 (not printed).
- **Ask shares by kind (described).** Creator-balanced shares of recordings carrying an ask, claimed-voice recordings
  against own-voice talks: pay-or-enrol 0.29 against 0.42 (difference -0.13, 90% bootstrap -0.33 to 0.06); platform 0.24
  against 0.40 (-0.17, -0.33 to -0.03); off-platform 0.20 against 0.25 (-0.06, -0.25 to 0.13); any ask 0.42 against 0.70
  (-0.28, -0.49 to -0.05). Every difference reads **undetermined** against the 0.05 margin (each interval reaches inside
  it). Money gifts with third-party adverts: not printed (fewer than 5 creators carry the estimate). Claimed-voice
  recordings carry asks somewhat less often in every class; many still carry one.
- Covariate (described): claimed-voice recordings hold about 5% more speech than the same creators' own-voice talks
  (mean log10 difference 0.022).

**The deposited prediction** (deposit 2's account cell, business account: "as b6, read on seen creators as a
description"): ask half **undetermined**; congruence half **not computed (too few terms or creators)**. Neither half is
supported, and neither of den-soc's retirement rules is met.

Consistency with published counts: LAB-A's "about four in ten of a creator's recordings" with a spoken pay-or-enrol ask
lies between this entry's two kinds (0.29 and 0.42). r3-P05 (step 1) found pay-or-enrol asks falling in the claimed voice
0.29 times as often as position predicts, a span-level result; at recording level, a claimed-voice recording can carry an
own-voice ask (r3-P05's occult row: most own-voice pay asks come after the last claimed offset), so the recording-level
odds ratio is closer to 1 and undetermined. r3-P56 (step 2): pay-or-enrol asks per hour lower in the claimed voice; same
direction. The units differ (span, hour, recording) and are not reconciled after the fact.

Multiplicity (deposit 2): no family-wise adjustment; 56 primaries; about 2.8 readings beyond a margin expected by chance at
half-margin effects. A reading is never called a finding.

## Rows not computed

P2 and its three brackets (fewer than 5 creators with asks in both kinds); the share-based P2 row (carried by fewer than 5
creators); the money-gift and advert share row (carried by fewer than 5 creators); the creator-level t interval on
per-creator log odds ratios (r3-P30 class G, chosen by the count; the eligible count is banded: decision 62).

## Files

| File | What |
|---|---|
| `public/data-r3-P57-shares.csv` | ask shares by class and kind, differences, readings |
| `public/data-r3-P57-primaries.csv` | P1, P2, sensitivities, covariate, tier, the b6 scorecard |
| `public/fig-r3-P57-asks.png`, `.pdf` | paired bars of ask shares by kind with the differences; b6's words |
| `prespec.md`, `prespec-hash-record.md` | prespecification and its hash |
| `code/p57.py`, `code/publish_p57.py` | analysis and publication (shared code: `../common/s4common.py`, `../common/eligibility.py`) |
| `contacts.md`, `status.json` | reads (no contact); status with every file's SHA-256 |

## Privacy

Creator counts are printed in the forms the step's register gives (banded where near a published count). Intervals are
fixed methods (creator-cluster bootstrap), never chosen by the count; the one count-chosen interval is not printed. No
value carried by fewer than 5 creators is printed. Checks: see `../common/privacy-checks.md`.

## Departures

1. Length tertiles use speech duration (the voice file's speech seconds), the duration every labelled recording carries.
2. Round 3's creator-level t interval is not the primary's interval: with this entry's banded count it would be withheld
   (decision 62), so the prespecification made the bootstrap of the Mantel-Haenszel ratio primary before any outcome.

## For the lead (settled)

- **Settled** (the lead's decision 77): the congruence half goes on the fourth panel's agenda with the
  larger-tier registration.
- The congruence half cannot be computed on the 23 non-development creators: fewer than 5 have pay-or-enrol asks in both
  kinds of recording. A run on all seen creators (with the tuning pool) would be a new registration (decision 65 item 1).

## Change by the lead's decision 103 (2026-11-26T17:16:20Z, UTC from `date -u`)

- The note to the lead is marked as settled. No number changed.
