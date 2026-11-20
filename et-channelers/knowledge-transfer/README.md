# Collection knowledge transfer

Start here to operate the latest-20+ audio archive or reproduce a result from it. The archive selects up to twenty public, completed recordings from each channel’s **Videos** tab, newest first. A short recording on that tab qualifies. YouTube Shorts and streams keep their own classifications in the cumulative index. Publication date and running time have no cutoff.

## Where the collection stands

The **00:51 UTC, November 20, 2026** receipt checkpoint contains **1,918 of 1,976 recordings (97.1%)**, with all available selections archived for **70 of 101 channels**. The source listing ended with fewer than twenty eligible recordings for five channels. Ninety-six channels supplied twenty each. The cumulative catalog contains 2,697 entries. These counts describe one frozen selection, so a later channel upload can change the membership of a future sweep. [Creator table](evidence/2026-11-20/creator-status.csv) · [Every recording](evidence/2026-11-20/recording-status.csv) · [Checkpoint](evidence/2026-11-20/checkpoint.json)

| Evidence at the checkpoint | Recordings | Interpretation |
| --- | ---: | --- |
| Native YouTube audio | 1,298 | The selected audio track had provider-labelled original-track evidence. |
| Other verified YouTube audio | 443 | The full selected file yielded verified audio. The source track’s original-language identity remains unconfirmed. |
| Creator-published edition | 177 | A creator or publisher independently distributes the matched recording. Its edit and timecodes can differ from YouTube’s. |
| Current source refusal | 28 | The closed record contains an item-specific refusal. |
| Local or administrative hold | 4 | The previous worker recorded an operating or admission problem. |
| Ordinary work awaiting a closed outcome | 26 | These rows were eligible for the next batch. Closed evidence cannot identify a currently downloading file. |

A recording counts once when the private archive has the matching creator/video identity, verified audio and provenance. The 1,108 figure on an older dashboard counted native audio on a 1,420-recording selection. The [November 19 failure report](../research/download-failures-2026-11-19/) preserves a separate, earlier observation.

## Find a question, decision or artifact

| Question | Start with |
| --- | --- |
| How do I check the Windows service, storage, Drive and remaining work? | [Operator handoff](operations.md) |
| Which fixes improved throughput? What happened in each production batch? | [Measured production history](production-history.md) |
| What did the research panels and browser, caption, feed and GPU trials establish? | [Research and experiment index](research-index.md) |
| What happened to one recording or creator? | [Recording status](evidence/2026-11-20/recording-status.csv), [creator status](evidence/2026-11-20/creator-status.csv) and [attempt register](evidence/2026-11-20/attempt-history.csv) |
| Which observations survive, and how can I reproduce the export? | [Evidence dictionary](evidence/README.md), [aggregated attempts](evidence/2026-11-20/attempt-summary.csv) and [exporter](../pipeline/collection_history.py) |
| Where did a change enter Git? | [Pull requests, branches and merge commits](release-history.csv), [branch heads](branch-heads.csv) and [branch guide](../../BRANCHES.md) |
| Which channels, people and attributed sources are documented? | [Channeler and source table](../research/analysis-plan-2026-11-16/channeler-entity-table.md), [primary-source relationships](../research/analysis-plan-2026-11-16/discovery-relationships.csv) and [interview guest review](../research/interview-discovery-2026-11-19/verified-guest-channels.csv) |
| How do I study dates, shared events, predictions, healing or proposed experiments? | [Research plan](../research/analysis-plan-2026-11-16/README.md), [date evidence](../research/recording-dates-2026-11-19.md) and [shared-event register](../research/cross-channel-events-2026-11-16.md) |
| Where do the next fifty and deeper index fit? | [Phases and dependencies](../ROADMAP.md) and [queue preparation and timing](../pipeline/COLLECTION_PROCESS.md#latest-50-forecast) |

## Dashboards and archive

The release CSV covers pull requests 1–87 and the branch CSV captures 88 remote heads after the daily calendar release. The research index traces 86 earlier pull requests and 170 historical documents to pinned revisions. The subsequent numerical-analysis release adds repeatable term-score, cluster-sensitivity and passage-retrieval outputs. Its model and GPU checks are scheduled against the completed text corpus. [Numerical-analysis change](https://github.com/occult-kranti/bashar-index/pull/88)

The [dashboard directory](https://occult-kranti.github.io/bashar-index/dashboards/) links the public interfaces. The [collection dashboard](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/collection/) shows its saved reporting time. The [daily timeline](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/collection/timeline.html?date=2026-11-16) supports individual dates and ranges. The [failed-links dashboard](https://occult-kranti.github.io/bashar-index/et-channelers/research/download-failures-2026-11-19/) filters the failure report by creator and reason. The [Atlas entities view](https://occult-kranti.github.io/bashar-index/channeling-atlas/dist/#/entities) ties an attributed source to the person, episode or publication that supports it.

The project’s private Drive holds media, full recording provenance, transcripts, translation bundles and private verification material. The repository carries code, reviewed research, public recording IDs, receipt-derived counts and release history. [Archive on Google Drive](https://drive.google.com/drive/folders/1pMBEavFcXc3BrDbg0BqW0mKkpyOHjD_B) · [Daily timeline edition on Drive](https://drive.google.com/drive/folders/1gl1O5vRqitZKJ-48-ZJdEEcNIsQO3WRA)
