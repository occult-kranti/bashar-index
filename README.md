# The Bashar Index

An independent research site that indexes the public channeling sessions of **Bashar** (channeled by Darryl Anka): a 684-session catalogue (1984–2027), 75 structured digests of public recordings, a topic analysis with clustering, a glossary, a timeline, 56 redrawn concept diagrams, podcast appearances, and a skeptics section.

**Live site:** served from this repository via GitHub Pages (`index.html` at the root).

## Channeling Atlas handoff and roadmap

The expanded cross-channel research project is in [`channeling-atlas/`](channeling-atlas/README.md). Its [handoff](channeling-atlas/README.md#handoff-resume-here) records the reviewed baseline, exact data/PDF hashes, safe rebuild commands, source boundaries and the separate GitHub/Sites repository layouts.

The completed 23 October 2026 release contains a 925-upload analysis, per-account duration statistics, a caption/embedding pilot, a reviewed working paper and six build/review rounds. Read the [prioritized roadmap](channeling-atlas/README.md#roadmap-next-research-phase) before continuing: identity and sampling audit; dated activity/services refresh; caption and speaker validation; session deduplication; matched model comparisons; then a new dashboard/paper release.

| Branch | Purpose |
|---|---|
| `main` | Reviewed integration and documentation |
| [`release/channeling-atlas-2026-10-23`](https://github.com/occult-kranti/bashar-index/tree/release/channeling-atlas-2026-10-23) | Scientific baseline pinned to `bbe4801` |
| [`research/channeling-atlas-next`](https://github.com/occult-kranti/bashar-index/tree/research/channeling-atlas-next) | Next work, starting with the handoff |
| [`experiment-frequency-of-place`](https://github.com/occult-kranti/bashar-index/tree/experiment-frequency-of-place) | Existing experiment preserved for separate review |

See the [branch register](channeling-atlas/research/maintenance/branch-register.json); every branch of this repository, with its status, is in [Branches and work so far](#branches-and-work-so-far) below. The root Bashar Index and nested Channeling Atlas have separate build pipelines. Run Atlas commands from `channeling-atlas/`; preserve the original root application. Human validation, authorship, ethics determination and submission readiness remain TBD in the working paper.

## Branches and work so far

This repository first held the Bashar Index, a one-page site about Bashar's public sessions. A panel analysis of its data followed, then the Channeling Atlas, a separate study of channeling (a person speaking as, or passing on the words of, another being) across YouTube channels, and since 2026-11-11 the ET-channelers work, which indexes and collects the public recordings and texts of channelers who say the beings they speak for are extraterrestrial (ET). The early work was committed directly to `main`, the default branch. Since 2026-11-13 each piece of work has been done on its own branch and merged into `main` by a GitHub pull request (PR), numbered PR #1, PR #2 and so on in the tables below.

### Work so far

| Date | Work | Where |
|---|---|---|
| 2026-09-16 | The Bashar Index: a one-page site, served by GitHub Pages, that indexes Bashar's public sessions (a 684-session catalogue, 75 digests of recordings, a topic analysis, a glossary, a timeline, 56 redrawn diagrams), with its data package and the Python that builds it. | [`index.html`](index.html), [`data/`](data/), [`src/`](src/); on `main` |
| 2026-09-23 | A review panel tested the Index data: four pre-registered tests (their methods fixed before the data were analysed) on Bashar's dated predictions and audience questions, how the teachings shift over time, and a rubric for 2027 frozen in advance. The report measures the genre's habits, not whether any claim is true. | [`FINAL_REPORT.md`](FINAL_REPORT.md), [`analysis/`](analysis/), [`panel/`](panel/); on `main` |
| 2026-10-22 | An experiment page, "The frequency of a place": a design for a test of Bashar's copper-sphere idea. Not merged. | branch `experiment-frequency-of-place` only |
| 2026-10-23 | The Channeling Atlas: 925 YouTube uploads across channels, video lengths per account, a small trial on 30 English caption documents (video subtitles) and a 12-page working paper, with six review rounds. The release is pinned on its own branch. | [`channeling-atlas/`](channeling-atlas/README.md); on `main` |
| 2026-10-23 | The Atlas handoff, an eight-item roadmap for its next phase and a register of the branches. | [`channeling-atlas/README.md`](channeling-atlas/README.md#handoff-resume-here), [`channeling-atlas/research/maintenance/`](channeling-atlas/research/maintenance/); on `main` |
| 2026-10-23 | An Atlas expansion: an evidence explorer, a rewritten paper and a database of 949 audience questions and answers, as the Bashar Index's AI-written digests paraphrase them (not checked by a person), from 67 Bashar recordings. Its new YouTube collection was blocked. Not merged. | branch `research/atlas-expanded-qa` only |
| 2026-11-11 | The ET-channelers work of 2026-10-22 to 2026-10-30: research notes on who channels whom, a YouTube index of 92 people (16 of their channels crawled, 466 videos) and its dashboard tables, and Bashar transcripts used to answer a question on astrology and calendars. | [`et-channelers/`](et-channelers/README.md); PR #1 |
| 2026-11-11 | A batch pipeline for audio and speech-to-text, an inventory of channel sizes (at least 40,652 videos), a roadmap, and a guard that keeps media and transcripts out of this repository. A YouTube trial from a cloud server was refused. | [`et-channelers/pipeline/`](et-channelers/pipeline/README.md), [`et-channelers/ROADMAP.md`](et-channelers/ROADMAP.md); PR #1 |
| 2026-11-13 | Collection routes that work from a cloud server (podcast feeds, creators' own audio files, publishers' own text pages), a sync to a private store, and a per-person coverage table that keeps the texts published by the sources apart from speech-to-text. Four reviewers checked it before the merge; each finding was fixed with a test. | [`et-channelers/plan/coverage.csv`](et-channelers/plan/coverage.csv); PR #1 |
| 2026-11-13 | Each person's own website found from their YouTube channel page (45 of the 57 channels read declare one), each site asked what it publishes, and 4,461 session pages on four sites registered. | [`et-channelers/sources/`](et-channelers/sources/); PR #2 |
| 2026-11-13 | One list of everyone tracked (103 rows), whole YouTube channels counted (videos, live streams and shorts), and collection mistakes stopped by rules and tests. | [`et-channelers/plan/targets.csv`](et-channelers/plan/targets.csv); PR #3 |
| 2026-11-14 | Interviews sorted by kind and fetched only when the channeled being itself speaks in them (live channeling); Bashar's own sessions on archive.org (the Internet Archive) listed and queued (903 recordings); the Bashar Index data put to use in new tables. | [`et-channelers/plan/`](et-channelers/plan/); PR #4 |
| 2026-11-14 | One command for a whole collection cycle; four AI agents (Claude Code helpers, each with one job) to run it, find new sources, read interviews and review changes; and two roadmap phases: 7a, comparing short videos with long recordings after collection, and 7b, how the agents run the cycle. On their first run the reading agents read 39 interview transcripts and found 21 with live channeling. | [`.claude/agents/`](.claude/agents/), [`et-channelers/pipeline/run_cycle.py`](et-channelers/pipeline/run_cycle.py); PR #5 |
| 2026-11-14 | A table of every source with its link and method; a private GitHub store that can be read back into an empty folder; a browsable Google Drive copy by person, with long recordings cut into playable parts; collection paused, with a handoff, for the move to a GitHub Codespace (a cloud computer for development) with 16 GB of memory. | [`et-channelers/plan/sources.csv`](et-channelers/plan/sources.csv), [`et-channelers/HANDOFF.md`](et-channelers/HANDOFF.md); PR #6 |
| 2026-11-14 | After the pause: the Drive copy finished; the YouTube steps switched off, because youtube.com's robots.txt (the file where a site says what automated programs may fetch) disallows them; fixes for the 80 findings that two reviews confirmed; a plan for the analyses after collection. | [`et-channelers/ANALYSIS_PLAN.md`](et-channelers/ANALYSIS_PLAN.md), [`et-channelers/notes/`](et-channelers/notes/); PR #6 |
| 2026-11-15 | Redirect rules for the feeds, texts and site-pages lanes, as the audio lane already had them: no redirect is followed to a host that is being left alone, every host a redirect leads to gets its own turn and its own Retry-After (the wait a server asks for), and each refusal is charged to the host that gave it. The lane test retries its two-worker setup, and the methods table states the redirect rules. | [`et-channelers/pipeline/feeds.py`](et-channelers/pipeline/feeds.py), [`et-channelers/plan/methods.csv`](et-channelers/plan/methods.csv); PR #7 |
| 2026-11-15 | Every Bashar session on archive.org collected: all 903 recordings downloaded, with no failures, into the private store, and copied in full to the owner's Google Drive (`04 Audio`) in 18 rounds (1,422 files) of `drive_stage.py` (plan, batches, round, done), each round's ledger saved to the private store's release `handoff-2026-11-14`. The audio is in the private store and on Drive, not in this repository. | [`et-channelers/HANDOFF.md`](et-channelers/HANDOFF.md), [`et-channelers/ROADMAP.md`](et-channelers/ROADMAP.md); PR #8 |

### Branches

| Branch | Status | Last commit | What it holds |
|---|---|---|---|
| `main` | default branch | 2026-11-15 | Everything merged so far. GitHub Pages serves the site from here. |
| [`fix/redirect-rules-other-lanes`](https://github.com/occult-kranti/bashar-index/tree/fix/redirect-rules-other-lanes) | merged by PR #7 | 2026-11-15 | Redirect rules for the feeds, texts and site-pages lanes, the lane test's retried two-worker setup, and the redirect rules in the methods table. |
| [`docs/bashar-archive-complete`](https://github.com/occult-kranti/bashar-index/tree/docs/bashar-archive-complete) | PR #8 | 2026-11-15 | All 903 Bashar archive.org sessions downloaded and on Drive, the tables rebuilt to show them, and the final figures in the handoff, roadmap and READMEs. |
| [`dashboard/sources-and-private-store`](https://github.com/occult-kranti/bashar-index/tree/dashboard/sources-and-private-store) | merged by PR #6, with this section | 2026-11-14 | The sources table, the private store, the Drive copy, the pause and handoff, and the work after the pause. |
| [`automate/cycle-and-agents`](https://github.com/occult-kranti/bashar-index/tree/automate/cycle-and-agents) | merged by PR #5 | 2026-11-14 | The one-command cycle, the four AI agents and the reading agents' first run. |
| [`collect/bashar-host-shows`](https://github.com/occult-kranti/bashar-index/tree/collect/bashar-host-shows) | merged by PR #4 | 2026-11-14 | Interviews by kind, Bashar's sessions on archive.org, the Bashar Index data put to use. |
| [`research/targets-and-engines`](https://github.com/occult-kranti/bashar-index/tree/research/targets-and-engines) | merged by PR #3 | 2026-11-13 | One list of everyone tracked; whole channels counted. |
| [`research/source-recon`](https://github.com/occult-kranti/bashar-index/tree/research/source-recon) | merged by PR #2 | 2026-11-13 | Official sites found from channel pages, and what each site publishes. |
| [`integrate/multi-lane-archive`](https://github.com/occult-kranti/bashar-index/tree/integrate/multi-lane-archive) | merged by PR #1 | 2026-11-13 | Brought ET-channelers into `main`: routes that work from a cloud server, the private-store sync, the review fixes. |
| [`research/et-channelers-youtube-index`](https://github.com/occult-kranti/bashar-index/tree/research/et-channelers-youtube-index) | merged by PR #1, through `integrate/multi-lane-archive`, which builds on its two commits | 2026-11-11 | The start of ET-channelers: the YouTube index of 92 people (16 channels crawled), the batch pipeline. |
| [`research/atlas-expanded-qa`](https://github.com/occult-kranti/bashar-index/tree/research/atlas-expanded-qa) | not merged, no PR | 2026-10-23 | The Atlas expansion: evidence explorer, rewritten paper, Q&A database. |
| [`research/channeling-atlas-next`](https://github.com/occult-kranti/bashar-index/tree/research/channeling-atlas-next) | merged without a PR | 2026-10-23 | The Atlas handoff commit `1d6eb36`, which is also on `main`. |
| [`release/channeling-atlas-2026-10-23`](https://github.com/occult-kranti/bashar-index/tree/release/channeling-atlas-2026-10-23) | merged without a PR | 2026-10-23 | The Atlas release, pinned to `bbe4801` and kept fixed. |
| [`experiment-frequency-of-place`](https://github.com/occult-kranti/bashar-index/tree/experiment-frequency-of-place) | not merged, no PR | 2026-10-22 | The experiment page "The frequency of a place". |

Two branches are not merged, and neither has a pull request. `experiment-frequency-of-place` adds the experiment page to the site: a design for Bashar's copper-sphere test, with its physics model, research notes, diagrams, a Blender scene and an "Experiment" link in the navigation. The Atlas [branch register](channeling-atlas/research/maintenance/branch-register.json) keeps it apart until its code and its subject matter have had a review of their own. A trial merge into `main` conflicts only in this README: both sides add a row at the same place in the "What is here" table, and keeping both rows resolves it. `research/atlas-expanded-qa` adds the reviewed Atlas expansion under `channeling-atlas/research/expansion/` and `channeling-atlas/dist/expansion/`; its collector and query plan were written but collected nothing new, because outbound requests to YouTube were blocked. It merges into `main` without conflicts. Merging or deleting either branch is the owner's decision. Merged branches are kept on GitHub as a record.

### Outside this repository

The audio, the texts published by the sources and the speech-to-text transcripts are kept in a private store and a Google Drive copy; none of them goes into this repository. On 2026-11-14 the collection held 1,138 audio files (819.5 hours), 8,425 texts published by the sources and 61 speech-to-text transcripts. By 2026-11-15 all 903 recordings of Bashar's sessions on archive.org were downloaded into the private store, with no failures, and copied in full to the Drive copy's `04 Audio` folder; the collection then held 1,779 audio files (1,454.0 hours) and the Drive copy 3,420 files (17.9 GB); the store and Drive figures in the table below are those of 2026-11-14.

| What | Where |
|---|---|
| Private store | GitHub repository `occult-kranti/et-channelers-archive` (private), with the three releases below (a release is a set of files, called assets, attached to a GitHub repository). Its `main` branch holds the texts as plain files in `texts/`, by person, with the texts from the sources and the speech-to-text made here in separate folders. |
| Release `archive-v1` | 64 assets, 10.52 GB: checked bundles of the audio, the speech-to-text transcripts and the texts published by the sources, read back with `sync_archive.py pull`. |
| Release `archiveshelf-podcast-audio-v1` | 9 assets, 0.6 GB: the 16 podcast episodes held by ArchiveShelf, an earlier archive project of the owner's, byte for byte as ArchiveShelf holds them. |
| Release `handoff-2026-11-14` | 7 assets, 0.17 GB: the pipeline's state without media, the Drive ledger (which file sits where on Drive), an outside snapshot of YouTube channel data, notes, and the memory files Claude Code keeps between sessions. |
| Google Drive copy | The owner's Drive, folder "ET Channelers Archive", with a read-me: `01 Plans and reports`, `02 Tables`, `03 Transcripts` (by person; texts from the sources and speech-to-text made here in separate volumes), `04 Audio` (by person and source; 1,138 recordings as 1,958 playable files), `05 Analysis`, `06 Earlier work`. `03 Transcripts` and `04 Audio` hold 1,998 files (1,958 audio parts and 40 text volumes) in 77 folders. |
| Collection dashboard | <https://claude.ai/artifact/898o4zpkocZ8qXjvR1xDfb>, a dashboard page on claude.ai (Anthropic's Claude website) whose tables come from the CSV files in [`et-channelers/plan/`](et-channelers/plan/). Like every claude.ai page, it opens only for the people the owner shares it with. |
| Handoff | [`et-channelers/HANDOFF.md`](et-channelers/HANDOFF.md): the state, how to set up the next Codespace and read the store back, the decisions waiting for the owner, and a prompt for the next session. |

The current state and the next steps are in [`et-channelers/HANDOFF.md`](et-channelers/HANDOFF.md) and [`et-channelers/ROADMAP.md`](et-channelers/ROADMAP.md). The next task, set by the owner on 2026-11-15: the newest 10, then 20, then 50 videos of every tracked channel, then a timeline of the predictions made on each channel (HANDOFF section 5). It waits for the owner's decision on YouTube's robots.txt and runs from the owner's own connection.

## What is here

| Path | Contents |
|---|---|
| `index.html` | The whole site — one self-contained page, no external requests. |
| `data/` | The research data package: digests, catalogue, topic analysis, diagrams (JSON + SVG), glossary, timeline, manifests. See `data/README.md`. |
| `src/` | The Python that builds the page (`build.py`, `css.py`, `js.py`, `svglib.py`, `diagrams_a.py`, `diagrams_b.py`), the analysis pipeline (`topics.py`) and the digest schema (`DIGEST_SPEC.md`). |
| `et-channelers/` | The ET-channelers work from Claude sessions: research notes, a YouTube index of 92 people (16 of their channels crawled, 466 videos), the flat index and dashboard tables, and the transcript pipeline with its manifests and findings. Start with [`et-channelers/README.md`](et-channelers/README.md). Separate from `channeling-atlas/`. Since 2026-11-13 the pipeline also collects podcast episodes, creator-hosted audio and publisher texts (lanes that work where YouTube refuses cloud servers): see [`et-channelers/pipeline/README.md`](et-channelers/pipeline/README.md) and the per-person table in [`et-channelers/plan/coverage.csv`](et-channelers/plan/coverage.csv). |

## Rebuilding

```
pip install scikit-learn numpy
python3 src/topics.py      # regenerates the analysis from data/digests
python3 src/build.py       # regenerates index.html
```

(`build.py` expects the research files at the paths used during the original build; adjust the constants at the top of the file to point at `data/`.)

## Method and limits

- Digests are AI-generated from auto-transcripts of public YouTube recordings. They are summaries, not transcripts; quotes are limited to 30 words and link back to the original recording.
- Diagrams are original SVG redrawings of concepts described in sessions, each with a confidence grade. No handout artwork is reproduced.
- Upload dates on re-upload channels are unreliable; the site flags these (`~`) and excludes them from year-based views.
- All claims are reported as claims, not endorsed. The site includes critical and skeptical coverage.

## Not affiliated

This project is not affiliated with, endorsed by, or connected to Bashar Communications, Inc. or Darryl Anka. Bashar® session recordings, transcripts and handouts are © Darryl Anka / Bashar Communications, Inc.; none are reproduced here. The code and the derived data in this repository are released under the MIT License (see `LICENSE`).
