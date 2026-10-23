# Channeling Atlas research release

Exploratory public-video metadata and text-analysis snapshot, checked 23 October 2026.

Open `dist/index.html` through a local static server for the atlas, or `dist/analysis/report.html` for the report. The analysis includes 925 unique upload IDs, source-linked metadata, sample averages, transparent keyword indicators and executed learned embeddings. It is not a count of human mediums.

Rebuild: install `research/analysis/requirements.txt`, then run `python research/analysis/build_analysis.py` and `python research/analysis/build_report.py`. See the analysis README for local caption recomputation, licenses and exact model pins. Full captions and model weights are excluded.

Frozen inputs and three build/review rounds are in `research/analysis/`. Original repository content is retained outside this directory.
