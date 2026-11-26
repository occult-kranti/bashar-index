# Calibration battery for interval methods: method card (r3-P30)

Written 2026-11-26T01:56:43Z (UTC, from `date -u`) by the step-0 agent (a model agent working for the project lead; not a person), from
programme.md (revised 2026-11-26T00:56Z), section 2.1, r3-P30, and section 2.4 (r4-P10). Deposited with r3-P29, citing the
frozen ledger's SHA-256 `d2e8e3fd32291f3b0b0a40f5e8a54cf88819e391b6c89a536df49c80a799a80a`.

**Status.** Exploratory; not a test of H1-H10. Every label behind these entries is model-coded and not checked by a person; every step-0 field computed from text is rule-based and not checked by a person.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these recordings and how the creators present it.

| Field | As written in the programme |
|---|---|
| Entry | r3-P30, a shared calibration battery for interval methods; class a.1; its method card goes into the step-0 deposit |
| Why | CAL shows that under creator-level placebos the registered tests reject too often and only the t interval on creator means stays near nominal coverage; slope pooling moves off the method used for TL-7.1 |
| What it absorbs | The residual of the withdrawn r4-P10: a size-and-power table of the register's fixed procedures (with no novelty sentence) |
| Builds on | CAL, CAL-f, rv-R1, rv-R2, TL-7.1 |
| Output | A coverage grid: design class by interval method against creator count, coloured by coverage error, with a size panel; and the size-and-power table of r4-P10's residual |
| Use | It tells each proposal which interval to use at its creator count; r3-P33 runs after r3-P06 and r3-P30; r3-P36 runs after the ledger hash and r3-P30 |
| Interval level | The floor rule reads the near bound of a 90% creator interval (programme 2.0), so coverage is read at 90% |
| Schedule | a.1, one light job queued behind any audio job; no class-a run before the deposit commit is merged (lead's ruling 2) |
| Data and cost | Seen creators, stored fields and local computation; no model call |

**Not stated in the programme** (left open, not invented here): the list of design classes; the list of interval methods
beyond those named (the t interval on creator means, creator-level sign-flip tests and the registered tests, from CAL's
reading; the TL-7.1 slope pooling being replaced); the grid of creator counts; the placebo-generating scheme for each
design class; the number of draws; the size and power targets; and the rule that picks a method from the grid.

**Pointers (not registered).** CAL's headline reports power at 12 to 17 creators and coverage of the t interval on creator
means of 0.885 to 0.915; the round-3 P36 entry of `pooled.json` and stat's round-4 memo name a t interval on channel slopes
with HKSJ beside it, and no DerSimonian-Laird pooling, for TL-7.1's slope.
