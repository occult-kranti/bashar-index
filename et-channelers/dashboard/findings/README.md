# Findings dashboard

`index.html` shows the finished transcription run of 20 November 2026, the time without speech, the languages,
the ten registered hypotheses, the 28 designed experiments and the first, provisional findings. It reads the
CSV files in `data/` in the browser; d3 7.9.0 is loaded from cdnjs, as on the prediction page.

Rules: counts, distributions and cohort-level estimates only. No file, chart or table has a row, mark or label
per creator or per recording; there are no creator codes, video ids, titles, transcript text or local paths.
Every number the run measured rests on five or more creators: a language row gives hours and time without
speech only if five or more creators speak the language (the others are pooled), every bin of the binned plot
and of the histograms over recordings holds files of five or more creators, and the outer bands of the
histograms over creators are merged until each holds five or more. Speech by position in the recording is shown
for the creators seen before the registry freeze only. The first-findings tab describes a snapshot of 1,213
transcripts and says so.
One registered hypothesis (H3) has been tested and then dropped by the owner; its registered result stays in the
results tab, and no other estimate by position on the hold-out creators is shown until freeze 2.
The same tab compares the two recognizer models on 36 recordings transcribed by both.

The page and its data are built outside the repository from the run's private records, by the same script
that feeds the hosted copy of this dashboard. Built 2026-11-21T00:30:26Z.
