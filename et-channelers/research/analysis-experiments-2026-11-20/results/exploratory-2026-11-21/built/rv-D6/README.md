# rv-D6: how the design was registered and then amended

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Exploratory, paper review (registry A2/A7); not a test of H1-H10. Public form made at the release review (plan P10) on
2026-11-22 from the item's build of 2026-11-21 01:10 UTC (not re-run). Place: M (figure); S (table).

**Question.** How was the design registered and then amended?

**Base.** Repository commit times (UTC), the run's progress records, the registry and the contact log, 19 to 21
November 2026. The registry was frozen at 19:47 UTC on 20 November (hypotheses.md SHA-256 `831ed6fa...`, unchanged at
the freeze commit and at the build); the H3 procedure was frozen at 20:38 and its result committed at 20:39.

**What is shown.**

| File | Content |
|---|---|
| `public/rv-D6-deviation-table.csv` | 19 deviations from the registered text: as registered, as done, time, decided by, results known, direction, effect on any verdict |
| `public/rv-D6-timeline-events.csv` | 34 dated events in five lanes (run progress, design events, results, hold-out contacts, public outputs) |
| Gallery group B-D, `rv-D6` | fig-1 timeline (M) |

**What it shows.** Within three hours of the registry freeze came the H3 test (20:39), a stricter verdict rule (A5)
written after its result, the owner's withdrawal of H3 from the claims (A6, 20:49) and three hold-out contacts; a first
contact (panel tables that included 32 hold-out files) predates the freeze. Of the 19 deviations, 9 are looser than the
registered text, 4 stricter in whole or in part (one of them only if entered), and the rest neutral or pending.

**Withheld, and why.**

- Two gate figures of the owner's 00:30 decision in the freeze-1 row (checkability "place" and the titles' figure): they
  rest on fewer than 5 creators under the rule for agreement figures (registry 2026-11-21 22:33, applied to the paper on
  2026-11-22 00:13). The row keeps the verdicts.
- File names of private records in the events' sources: a source reads "repository commit <hash>", "site repository
  commit <hash>" or "time stated in the project's record".
- The run's total of transcribed audio files in event 15: beside the seen and hold-out transcript counts of rv-D1 it
  gives the other group's withheld transcript count by subtraction. Event 15 is worded in recordings, as the paper's
  timeline key words it ("run closes: 1,699 of 1,731 recordings transcribed").

**Fix pass (2026-11-22, after the release verifier).** Event 15 is reworded as above, and the figure stacks events of
one lane that lie closer than a marker's width (each at its own time, earliest on top, numbered to its right), so no
marker hides another. No new value is printed.

**Not built in this release** (lead's decision D55). Rows for the deviations after 2026-11-21 01:10 UTC, including this
round's: the round's own deviation table holds them. The paper's deviation tables and timeline on main carry later rows.

**Interval level.** None (dates and a census of decisions).

**Caveats.** Times are UTC from commits, or the time stated in the record where no commit exists; three events are
plotted at a stated time earlier than their commit (verifier). The registry's time stamps come from a repository the
authors control; no external time stamp exists.

**Writers.** Tables: `build_tables_D.py` (SHA-256
`d38dc81e39a5d9606ca78aae9138138e1a429de11a2082f3e3de533467d1bb92`); figure: `plot_D.py` (SHA-256
`ab68d497db1726d7fd12edfbec30e72b71efe5b208be0886822e8c014fa44caf`).
