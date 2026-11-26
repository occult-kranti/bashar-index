# rv-D8: what was sent to external services, and how much of it was third-party speech

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Exploratory, paper review (registry A2/A7); not a test of H1-H10. Public form made at the release review (plan P10) on
2026-11-22 from the item's build of 2026-11-21 01:16 UTC (not re-run). Place: M (ethics table); S (by tag and date).

**Question.** What was sent to external services, and how much of it was third-party speech?

**Base.** The request ledger up to 2026-11-21 01:16:24 UTC (69,442 measured requests; the version of record as built,
before the first-round labels and the second round); the voice-map pilot (73 recordings of seen creators) for the
third-party share. The paper's ethics table on main reruns the same rule on the whole ledger (generated 2026-11-22
01:51 UTC); it is copied here as a revision beside the version of record. No model call was made in the exploratory
round (the ledger's last entry is 2026-11-21 18:40:42 UTC).

**What is shown.**

| File | Content |
|---|---|
| `public/rv-D8-external-processing.csv` | Services, data categories, creators, words sent (estimate), third-party share, retention and deletion, as built |
| `public/rv-D8-requests-by-category.csv` | Requests, tokens, USD and estimated words by data category, as built |
| `public/rv-D8-requests-by-date.csv` | Requests by UTC date and phase, as built |
| `public/rv-D8-requests-by-run-tag.csv` | Requests by run tag (tags name instruments and runs, never creators), as built |
| `public/rv-D8-third-party-share.csv` | Pilot share of words in other participants' turns or a third party's claimed voice |
| `public/rv-D8-pilot-formats.csv` | Recording formats in the pilot (model-coded) |
| `public/rv-D8-paper-full-ledger.csv` | The paper's whole-ledger table (revision) |
| `public/rv-D8-proposed-rule.csv` | The build's proposed rule for future external calls (one row per item; the plain-text copy is not part of a release, D56) |
| Gallery group B-D, `rv-D8` | fig-1 requests by category, as built (S); fig-2 requests by category, whole ledger (S) |

**What it shows.** By 01:16 UTC on 21 November the OpenAI API had received 69,442 requests (41.34 USD); about 26.45
million words of seen creators' transcript-derived text were sent, with repeats (an estimate: 0.75 words per uncached
input token). In the voice-map pilot, 14.1% of words (95% creator-bootstrap interval 4.5 to 24.1) were in other
participants' turns or in a guest's, client's or several people's claimed voice (6.7% in other participants' turns
alone): model-coded, not checked by a person, and extrapolated to the text sent, not measured. Over the whole ledger the
paper counts 396,608 requests and about 96.6 million words (estimate), with hold-out and other-group transcript windows
sent only after freeze 2 for the frozen instruments. Inputs may be kept up to 30 days in the vendor's abuse-monitoring
logs; zero data retention was not shown. Requests by the Anthropic agents of the panels and the review were not logged.

**Withheld, and why.**

- The pilot's creator count is printed against the seen total ("all but fewer than 5 of 71").
- Pilot formats with fewer than 5 creators are pooled into "other" (multi-presenter and unclear).

**Corrections.** The built caption gave 68,732 requests and 41.05 USD; the verifier found the summary's 69,442 requests
and 41.34 USD to match the ledger up to 01:16:24 UTC. The tables print the summary's figures.

**Interval levels.** 95% creator bootstrap (2,000 draws) for the pilot shares; none for counts. Words are estimates.

**Caveats.** This table does not replace an ethics determination. The pilot share applies to the pilot sample only.
The by-tag table is the version of record to 01:16 UTC; later tags appear only in the paper's whole-ledger totals.
The by-tag rerun on the whole ledger is not built in this release (lead's decision D55): the public form is made from the build of
01:16 UTC, not re-run.

**Fix pass (2026-11-22, after the release verifier).** The figures' data files and this README cite release file names
only. No value changed.

**Writers.** Tables: `build_tables_D.py` (SHA-256
`d38dc81e39a5d9606ca78aae9138138e1a429de11a2082f3e3de533467d1bb92`); figures: `plot_D.py` (SHA-256
`ab68d497db1726d7fd12edfbec30e72b71efe5b208be0886822e8c014fa44caf`). The tables were written at 2026-11-25T21:48:11Z and not edited since, except `rv-D8-proposed-rule.csv`, written by f01_edits.py (SHA-256 de3cdb4462a5fec5cdf3f49589e657901718c270b075bf45aaf2e3d7d3f45793) at 2026-11-26T00:57:31Z from the build's plain-text copy; this README was edited by p2_d42_d55_built.py (SHA-256 d1ec7400b2f8706c764137be76fbb676452ae960047ad0504d142539677e3f33; pass 2, 2026-11-25T21:51:12Z), p2_d41_flags.py (SHA-256 f51c2a6a880fcc827d9cc34d021458633921adda1eac6118668b3c88ea876797; pass 2, 2026-11-25T22:02:04Z), f01_edits.py (SHA-256 de3cdb4462a5fec5cdf3f49589e657901718c270b075bf45aaf2e3d7d3f45793; fix step, 2026-11-26T00:57:31Z), f33_edits.py (SHA-256 442d541d26f9e5167d980d3c61e23db5248293947ea568ce2b20d4a5a1ff37d4; second fix step, 2026-11-26T02:22:42Z; this note). The writer was patched afterwards (build_tables_D.py, SHA-256 b84a31fc38be3a70e633dee40e5e0699275dae11f86d0faa9f16cf88203781ab) and has not been rerun: a rerun writes the same tables (checked in the second fix step) and not the proposed rule's CSV.
