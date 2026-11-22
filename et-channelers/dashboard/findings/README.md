# Findings dashboard

`index.html` shows the finished transcription run of 20 November 2026, the time without speech, the languages,
the ten registered hypotheses with their registered tests (first round: from the public results file),
the 28 designed experiments and the first, provisional findings. It reads the
CSV files in `data/` in the browser; d3 7.9.0 is loaded from cdnjs, as on the prediction page.

Rules: counts, distributions and cohort-level estimates only. No file, chart or table has a row, mark or label
per creator or per recording; there are no creator codes, video ids, titles, transcript text or local paths.
No row, bin or cell describes fewer than five creators; cells with fewer than five creators are pooled. The
languages other than English, each spoken by fewer than five creators, are one pooled row; reasons for holding
a recording back that concern fewer than five creators are one row; every bin of the binned plot and of the
histograms over transcripts holds transcripts of five or more creators; adjacent bands of the histograms over
creators are merged until each holds five or more; a threshold of the longest quiet stretch is shown only while
every band between two thresholds, below the first and past the last holds five or more creators; and the kinds of
the read sample are two rows. When two counts of creators of nested groups would differ by one to four, one is
given as a number and the other against it ("all but fewer than 5 of 71", "61 and fewer than 5 more"), so that no
difference of two published counts is a group of fewer than five creators.
Counts of the whole run come from the run's ledger (creator, duration, language of each recording). Each count keeps
the unit this page published it in before 21 November 2026: the run in numbers, the transcription status, the
languages and the basis of the language decision count audio files, and the outcome chart counts the selected
recordings. Timing measures (time and share without speech, quiet stretches,
speech by position, speaking pace) are of the creators seen before the registry freeze only, counted in transcripts
(one per audio file); their bands of share without speech and of the longest quiet stretch are offset from the
full-run bands published before 21 November 2026, so that no such band of the other creators can be found by
subtraction. The length bands of the binned plot are the full-run ones; the other creators' transcripts in each
length band, which follow by subtraction, are of five or more creators. The hours-over-time series has a point only where the rise since the previous point holds
recordings of five or more creators; it is the run report's figure 1. The first-findings tab describes a
snapshot of 1,213 transcripts and says so; its artefact card counts the finished run's English transcripts of
the seen creators made by the English-only model, and no number on the page has the artefacts removed except the
H3 test and the comparison of the two models.
H3 was tested on 20 November 2026: it passed its registered rule, but the rule was not calibrated at creator
level, so H3 is not determined at creator level, and it was withdrawn (amendment A6). Its registered result stays
in the tests tab, and no other estimate by position on the hold-out creators is shown. H8 was dropped before it
ran (amendment A9); H7 and H10 are not run in the first round.
The six registered tests of the first round (H1, H2, H4, H5, H6 and H9) are shown from their public results file
`research/analysis-experiments-2026-11-20/results/first-round-2026-11-21.json`, published 2026-11-21T23:33:53Z: per hypothesis the verdict and its kind, the
eligible creators, the amended version's estimate with its 90% interval over creators where the file publishes one,
the Holm-adjusted p, the uninformative flag and the verification sentence. Every label behind them was made by
language models and no person checked it, so every verdict is model-coded. Each count of creators keeps the file's
printed form, except where it would lie one to four from a count of hold-out creators of H3 printed here; such a
count is stated against its minimum. Beyond the counts of the whole run, the hold-out creators enter only the
registered tests.
The same tab compares the two recognizer models on 36 recordings transcribed by both.
The budget card shows the spend committed for model calls, read from the spend ledger when the page was built
(2026-11-22T03:10:53Z), against the owner's hard stop, with the warning level.

The page and its data are built outside the repository from the run's private records, by the same script
that feeds the hosted copy of this dashboard. Built 2026-11-22T03:10:53Z.
