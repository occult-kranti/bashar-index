# One split policy for the seen creators (r3-P31)

Written 2026-11-26T01:55:20Z (UTC, from `date -u`) by the step-0 agent (a model agent working for the project lead; not a
person). The draw was made at 2026-11-26T01:49:43Z (UTC, from `date -u`). Deposited with r3-P29, citing the frozen forecast
ledger's SHA-256 `d2e8e3fd32291f3b0b0a40f5e8a54cf88819e391b6c89a536df49c80a799a80a`. The policy is public; the membership
of each half stays private (`split.private.json`, whose SHA-256 is in `deposit.json`).

**Status.** Exploratory; not a test of H1-H10. Seen creators only; no hold-out or other-group field was kept. Labels behind
any later rule are model-coded and not checked by a person.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## The policy (programme 2.1, r3-P31; stat's final tier table)

| Tier | Which rules | Rule |
|---|---|---|
| L | Lists written blind from the literature and hashed before any count | Run once on all non-development seen creators, with no split |
| S | Data-tuned rules or revisions with 20 or more outcome-blind eligible creators | Built on the exploration half, run once on the sealed half |
| X | The same with 10 to 19 eligible creators | Two-fold cross-fitting with roles swapped, folds balanced by the deposited seed |
| D | Fewer than 10 eligible creators | Description only, labelled "no overfitting check possible" |

- **The tuning pool T** is the registry's development creators, who are already exposed to prompt tuning. T joins the
  exploration side and is never in the sealed half.
- **The halves.** The seen non-development creators are drawn once into an exploration half A and a sealed check half B.
- **Tiers are assigned before any outcome is read**, from each proposal's count of eligible creators computed from
  outcome-free fields and printed as a count band.
- Contrasts already computed on all seen creators (r3-P01 to r3-P06, r3-P15, r3-P17, r3-P32 and r3-P33's rows) are not
  split; their guard is r3-P29's register and r3-P30's card. r3-P27 uses the paper's existing development and check
  partition as it is.

## The draw

- **Seed:** 2026112602, fixed before the draw.
- **Code:** `code/draw_split.py` (SHA-256 `72281e90a8d21bff3ae2cefe6634b8c4ce8ef3cdd84b19584f2b4f95b1d7a300`). No model or
  network call.
- **Strata, as the programme names them:** roster vintage (on the 74-channel roster table of 19 November, 04:31 UTC, or
  added later that day); audience band (median subscriber count over the creator's recordings at the latest capture, in
  CSS-10's bands); language mix (language of each seen recording's transcript); middle-model subset (whether the middle
  model labelled the creator's recordings); development membership.
- **Method:** each non-development creator gets a stratum key; creators are ordered by key and, within a key, by a seeded
  random number; consecutive creators form pairs and a seeded coin sends one of each pair to A and the other to B (an odd
  last creator goes by a coin). Every stratum and every combination of strata is balanced to within one creator per pair
  boundary.
- **Strata that do not vary.** Inside the non-development creators three of the five strata take one value for every
  creator: language mix (every transcript in English), the middle-model subset (every one is in it) and development
  membership (constant by construction). The draw is therefore balanced in effect on roster vintage and audience band.

## Counts (only counts of 5 or more; no two nested counts 1 to 4 apart)

| Set | Creators |
|---|---|
| Seen creators | 71 |
| Tuning pool T (development creators) | 48 |
| Non-development creators drawn | 23 |
| Exploration half A | 11 |
| Sealed check half B | 12 |
| A, on the 19 November roster table / added later | 6 / 5 |
| B, on the 19 November roster table / added later | 7 / 5 |

Audience band by half is withheld: one band holds fewer than 5 of the 23 creators, and the cells by half fall under 5
creators or could be solved by difference.

## The known leak (printed, as the programme asks)

- The development creators (T) were used to develop and tune the prompts of the frozen instruments.
- Every member of the panel, the lead and this agent have seen the exploratory round's aggregates over all seen creators,
  so rules and lists written now are not blind to seen aggregates; the sealed half guards only against tuning done after
  this deposit, not against what those aggregates showed.
- The halves are drawn after the exploratory round's outputs on all seen creators were built; outputs already computed on
  all seen creators cannot be re-run as if sealed.
- With T holding every development creator, the non-development pool is 23 creators, so a tier-S rule needs 20 or more of
  them to be eligible; most data-tuned rules will fall in tier X or D.
