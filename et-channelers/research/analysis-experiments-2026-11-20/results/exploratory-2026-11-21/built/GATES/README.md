# GATES: which instrument gates were met, and what did each revision change?

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Exploratory (registry A2); not a test of H1-H10. Public form made at the release review (plan P10) on 2026-11-22.
Place: M (summary in rv-D5); S (full table).

**Question.** Which instrument gates were met, and what did each revision change?

**Base.** The gate sample G (seen and check creators), as recorded in the paper's gate tables on main (generated
2026-11-22 01:51 UTC from the gate records, under the rule for agreement figures); and the hold-out reliability sample
R-hold (A10.5), as printed in the published first-round results file (2026-11-21 23:33:53 UTC). The release review copied both public forms and read no gate record of its own; release pass 2 then recounted gates A and B on G by creator from the stored answers and gate records (below). Every R-hold value was checked string by string against the
first-round file, so nothing here contradicts it.

**What is shown.** `public/GATES-gates.csv`: every gate the two sources print, failures included, with value, 90%
interval, floor and bound, verdict, and for G the revision and its decision time (voice revision 3, decision 02:55 UTC;
asks after one revision, 02:20 UTC; forecasts after the critic's one revision, 03:12 UTC, checkability with both
revisions spent and kept below its floor by the owner at 00:30 UTC; sentence codes after one revision; titles after both
revisions, kept below their floors by the owner at about 00:30 UTC). Gallery group B-D, `GATES`: fig-1, the agreement and
stability gates (C, D, VG-6) with a floor, against their floors (S).

**What it shows.** The claimed, own and other voice met its agreement gates on G and on R-hold (relayed voice failed on
G and was merged into claimed voice). The asks met their gates (the small model's check failed gate B, so the middle
model's check is the record). The forecast class of record passed on G, failed on the check creators alone and failed
gate D on R-hold (kappa 0.507, 90% 0.169 to 0.792, against 0.60), which is why H2 was not run; the forecast
checkability parts failed their two-model gate and are kept as the record by the owner's decision. The sentence group
passed on G but its stability fell below its floor on R-hold (0.816 against 0.85). Title presentation failed on both
samples and is kept as the record by the owner's decision.

**Withheld, and why.** Agreement figures whose positive code comes from fewer than 5 creators in a reading, or whose
disagreements come from 1 to 4 creators (rule of 2026-11-21 22:33 UTC), as in both sources; their verdicts are kept.
The figures of the owner's 00:30 decision (checkability "place"; the titles' presentation kappa and stability on the check creators; the titles' family figure) are not repeated here. Recounted by creator at release pass 2: the first three fail the rule and are no longer printed in the first-round file (dated correction); the family figure passes. The values of gates A and B on G (shares of valid calls and of exact quotations, near 100%) were recounted by creator at release pass 2 (lead's decision D48): a share whose misses come from 1 to 4 creators reads "not published (misses from fewer than 5 creators)" (D21); the small check's exact quotations on its ask items (misses that could not be attributed to creators without rebuilding the asks pipeline) stay not published; the other shares are printed as in the paper's gate tables; every verdict is kept. The R-hold rows of gates A and B (shares
near 100%) read "not published (misses not recounted by creator; a recount would be a hold-out contact)", with
their verdicts kept (D21, D53; release pass 2, fix step, 2026-11-26); the first-round file withholds them too since
its dated correction of 2026-11-26 (lead's decision D59).

**Not built in this release** (lead's decision D55). The full table of every gate of the annotation plan with revisions
spent and decision times for the gates run after freeze 1, and the verification gates VG-0 to VG-9 other than VG-6
(status L; no model call is needed; no package of the round assembled it; the gates run after freeze 1 are printed in
the published first-round results and entered in the registry).

**Interval level.** 90% (combined rule: the point at the floor and the lower 90% bound at the floor minus 0.10, where a
bound is given).

**Caveats.** Model-coded instruments; agreement between models or readers, never accuracy; not checked by a person.
Gates A and B (valid calls, exact quotations) are operational checks, not agreement figures; they are not drawn.

**Fix pass (2026-11-22, after the release verifier).** Gate A and B values on G withheld (above); the R-hold voice flag
copied; the table's header now names all four withheld figures of the 00:30 decision, as this README does; the figure
wraps its long labels instead of cutting them. No new value is printed.

**Release pass 2 (2026-11-25; lead's decision D48).** Gates A and B on G recounted by creator from the stored answers and gate records, with a reader that imports no API client and makes no call; seen and check creators only, so no hold-out contact. Shares whose misses come from 1 to 4 creators (voice B pooled; asks A find and B find on final asks; the forecast critic's chain run 1; the record's non-NO parts in run 3; sentence codes A in runs 1 and 3; title cue quotations of the middle, small and final readings) read "not published (misses from fewer than 5 creators)"; the other values are those of the paper's gate tables. The R-hold rows are unchanged.

**Writers.** Table: `build_tables_D.py` (SHA-256
`d38dc81e39a5d9606ca78aae9138138e1a429de11a2082f3e3de533467d1bb92`); figure: `plot_D.py` (SHA-256
`ab68d497db1726d7fd12edfbec30e72b71efe5b208be0886822e8c014fa44caf`). The table was written at 2026-11-25T21:48:11Z and then edited by checked text replacements, each logged with its backup; the table and this README were edited by p2_d42_d55_built.py (SHA-256 d1ec7400b2f8706c764137be76fbb676452ae960047ad0504d142539677e3f33; pass 2, 2026-11-25T21:51:12Z), p2_d41_flags.py (SHA-256 f51c2a6a880fcc827d9cc34d021458633921adda1eac6118668b3c88ea876797; pass 2, 2026-11-25T22:02:04Z), apply_pass2.py (SHA-256 e0ada1d2bc8eb1bdeae35da6bd0929b6cc849c2543ddb5dfd6c434f806005a3b; pass 2 (D48), 2026-11-25T22:04:54Z), followup_pass2.py (SHA-256 a47ad6c020d3c2cf52da3138e946a37d211ae6fdc3efe9df6375da457fe95258; pass 2 (D48), 2026-11-25T22:10:14Z), f01_edits.py (SHA-256 de3cdb4462a5fec5cdf3f49589e657901718c270b075bf45aaf2e3d7d3f45793; fix step, 2026-11-26T00:57:31Z), f33_edits.py (SHA-256 442d541d26f9e5167d980d3c61e23db5248293947ea568ce2b20d4a5a1ff37d4; second fix step, 2026-11-26T02:22:41Z), f52_edits.py (SHA-256 647ed82d76e723fa1c806a4d9c1215509c75f867f69b7963b3f2adaf35654556; third fix step, 2026-11-26T03:41:09Z; this note). The writer was patched afterwards (build_tables_D.py, SHA-256 b84a31fc38be3a70e633dee40e5e0699275dae11f86d0faa9f16cf88203781ab) and has not been rerun: a rerun would not reproduce these edits.

**Correction (2026-11-27T09:41:55Z, the lead's decision 134).** The base line's "seen and check creators" means the seen creators with every check creator included: the gate sample G holds a seeded draw from the seen creators and every check creator, so its agreement figures describe development and check creators alike, and its rows on the check creators alone report its check subset. No number or reading changes; the CSV is unchanged.
