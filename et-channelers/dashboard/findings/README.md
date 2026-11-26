# Findings dashboard

`index.html` shows the finished transcription run of 20 November 2026, the time without speech, the languages,
the ten registered hypotheses with their registered tests (first round: from the public results file),
the 28 designed experiments, the exploratory release with its headline figures, the third-round panel's programme
(its deposits and step 1's published entries), and the first, provisional findings.
It reads the CSV files in `data/` in the browser; d3 7.9.0 is loaded from cdnjs, as on the prediction page.

Rules: counts, distributions and cohort-level estimates only. No file, chart or table has a row, mark or label
per creator or per recording; there are no creator codes, video ids, video titles, quotations, transcript text or local paths.
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
The same tab compares the two recognizer models on 36 recordings transcribed by both, and links to the corrected
first-round results file (corrections of 25 and 26 November 2026; no verdict changes).
The tab "Exploratory round" shows the exploratory release of 26 November 2026 (exploratory; not a test of H1-H10)
from its public files only, read from the repository's main branch (a5e20e0): the
outputs by status and by plan section (the status table's rows, counted; counts of outputs, never of creators), links to
the release, its status table and its gallery, the third-round panel's programme, rulings and step-0 deposits, and a
small set of headline figures picked by a printed rule: every released gallery figure whose place includes both M (the paper's main text) and W (this dashboard), read from the gallery's manifest.json, in the gallery's order. The figures in `figures/` are
byte copies of the gallery's PNGs, with their titles and captions as the release prints them; a figure whose intervals
rest on a method that the calibration entry (CAL) did not test for its estimate and creator count says so. The rule
was chosen after the results were seen (the lead's step-1 decision 27a); r3-P33 prints a selection rule (S1 to S12)
for the release's headline descriptions and audits them.
The tab "Third-round panel" shows the panel programme from its public files on main
(a5e20e0): step 0's deposits 1 and 2; step 1, published,
as a table of its 17 entries with each entry's question and its reading
in the entry's own words, copied from the step-1 index (no entry is picked as a headline, and nothing the index withholds
is added; square brackets mark the page's own words where the index uses a word the page does not); r3-P20's registered
prediction with its SHA-256; deposits 3 and 4, step 2's instruments, written before any count; and "steps 2 to 5 run;
outputs published after independent privacy checks". No number of steps 2 to 5 is printed. Every item links to its
folder on GitHub.
Every view carries the sentence: "No measure in this study can tell whether a non-human source speaks; every measure
describes the speech in these recordings and how the creators present it."
The budget card shows the spend committed for model calls, read from the spend ledger when the page was built
(2026-11-26T15:54:04Z), against the owner's hard stop, with the warning level.

The page and its data are built outside the repository from the run's private records, by the same script
that feeds the hosted copy of this dashboard. Built 2026-11-26T15:54:04Z.
