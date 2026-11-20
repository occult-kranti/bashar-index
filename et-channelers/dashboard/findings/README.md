# Findings dashboard

`index.html` shows the finished transcription run of 20 November 2026, the time without speech, the languages,
the ten registered hypotheses, the 28 designed experiments and the first, provisional findings. It reads the
CSV files in `data/` in the browser; d3 7.9.0 is loaded from cdnjs, as on the prediction page.

Rules: counts and measures of time only; creators appear as codes (C001 to C101); no transcript text, video
ids, titles or local paths. The first-findings tab describes a snapshot of 1,213 transcripts and says so.
One registered hypothesis (H3) has been tested and then dropped by the owner; its numbers stay in the results tab.
The same tab compares the two recognizer models on 36 recordings transcribed by both.

The page and its data are built outside the repository from the run's private records, by the same script
that feeds the hosted copy of this dashboard. Built 2026-11-20T21:26:49Z.
