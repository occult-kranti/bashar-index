# ET channelers — current draft (2026-10-23)

Status: **draft, unreviewed.** This folder packages what the research passes produced before work was stopped. Nothing here was independently verified, and the website, timeline page, dashboard update and repository branch were not built.

## Files

| File | What it is |
|---|---|
| `ET channelers directory and timeline.md` | Draft synthesis report (about 7,000 words). Stops after the occult-forums and Reddit section; see the last section for what is missing. |
| `csv/youtube_channels.csv` | 92 people and organisations with their YouTube channel (handle, id, URL, subscribers, video count, entities seen). `index_status` says how deep each row goes. |
| `csv/youtube_videos.csv` | 466 video rows: title, URL, views and relative publish date as displayed on 2026-10-23, length, whether it is a channeling session, entity named in the title. |
| `csv/youtube_links_harvest.csv` | 136 YouTube links pulled from the research notes (68 channel, 10 playlist, 2 short, 56 video), each with the person or section it was cited under and the line it came from. |
| `csv/youtube_playlists.csv` | 12 playlists that turned up incidentally. Not a systematic playlist census. |
| `csv/youtube_entity_rollup.csv` | Beings named in video titles, with video counts and which channelers voice them. |
| `csv/bashar_videos_in_repo_by_channel.csv` | The 75 Bashar videos already digested in the Bashar index repo, grouped by the 38 channels that post them. |
| `csv/people_directory.csv` | 127 people parsed from the research notes (entity, start, first public, location, platforms, method, confidence), joined to the YouTube index. |
| `csv/entities_catalogue_raw.csv` | 73 entity blocks from the notes. Duplicates across notes are not merged. |
| `csv/timeline_draft.csv` | 530 dated entries from 1848 to 2027, with source URL, confidence and focus tags (ra, bashar, ashtar, ryok). Raw union of the notes, lightly de-duplicated. A few entries are scheduled items or claimed predictions (for example the 2027 row), flagged in the confidence column. |
| `plots/` | Audience of channels with a known subscriber count; beings named in video titles. |
| `notes/` | The eight research notes (about 67,000 words) and the canonical id list. |
| `data/` | Merged YouTube index JSON, its three source group files, the partly compiled people dataset (23 of about 129) and the planned dataset schemas. |

## How to read the YouTube files

- `index_status` is `ok` when the channel page and up to 30 recent uploads were read on 2026-10-23, `metadata-only` when the channel details come from the research notes and the video list was not read, `no_youtube` when no channel was found or applies, and `not_found` when a search found nothing.
- Subscriber and view counts are as displayed on that date. Publish dates are relative ("3 weeks ago") because the source only gave relative times.
- The structured YouTube data provider ran out of credits partway through, so most `metadata-only` rows still need one provider call each to fill their video lists.

## Known gaps

- Reddit: nothing retrieved. Wizard Forums: two site searches only. BALG: eleven threads read.
- Reported but unmerged conflicts between notes are left visible: duplicate timeline events with different wording, duplicate entity blocks, and dates marked low confidence.
- `people_directory.csv` was parsed from free-text notes by label matching, so a cell can be blank where a note used an unusual label: 18 of 127 rows have no parsed entity, start date or first-public value at all, and others have single blanks (Tyler Ellison's first-public and confidence cells, for example). The full text is always in `notes/`. All 73 blocks in `entities_catalogue_raw.csv` parsed without fallback.
