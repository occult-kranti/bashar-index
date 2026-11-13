# Source lists

Public metadata only: addresses, names and how each one was verified. No audio, no transcript text.
Everything fetched from these addresses is stored in the private folder (default `~/et-channelers-private`),
never in this repository. The scripts that read these files are in [`../pipeline/`](../pipeline/).

| File | One row is | Read by | How rows get in |
|---|---|---|---|
| `podcast_feeds.csv` | a podcast feed accepted for a tracked person | `fetch_feeds.py` | `find_feeds.py --merge` (Apple's public podcast search), or by hand |
| `official_sites.csv` | a domain known to be a person's own site, with the evidence | `find_feeds.py` | by hand, from the research notes or the ArchiveShelf channel intake |
| `creator_files.csv` | an audio file the maker hosts on their own site | `select_episodes.py` | from the maker's free-audio or session pages |
| `publisher_pages.csv` | a page that holds the published text of one session or message | `fetch_publisher_text.py` | from the publisher's sitemap or index page |
| `extra_targets.csv` | extra names and aliases, and people the 2026-10-23 index does not have. `weak_aliases` holds phrases (such as "Law of One") that must not assign an interview episode to a person by themselves | `find_feeds.py`, `select_episodes.py` | by hand |

## How a feed is graded

`find_feeds.py` never downloads audio. It grades each feed Apple returns for a person's name:

| Grade | Rule | Queued for download? |
|---|---|---|
| `verified` | the feed is served from a domain in `official_sites.csv`, or a page on that official site links to the show (its Apple id or its feed address) | yes |
| `name-match` | the feed's author is the person and its title carries the person's or channel's name, and at most two feeds make that claim | yes |
| `candidate` | something matches but not enough to tell the maker's own feed from a re-upload, a namesake or a guest appearance | no, until someone confirms it |

A feed naming the maker's site as its own website proves nothing: fan re-upload feeds usually do. That
claim alone leaves a feed a `candidate` (an earlier version of the rule accepted it; the 2026-11-13 review
caught that, and the one feed promoted that way, Steve Nobel's, was re-checked and is linked from his site).
Titles and author names from Apple are cleaned before they are written here: one line, no control
characters, never starting like a spreadsheet formula, and an author that is an e-mail address is blanked.

People whose recordings are widely re-uploaded (the `STRICT` list in `find_feeds.py`: Bashar, Abraham-Hicks,
Seth, Kryon, Ramtha, L/L Research and others) are never promoted on a name match. They need the
official-domain evidence. On 2026-11-13 the sweep graded 74 feeds for 25 people: 2 verified by the sweep (a third,
Sounds True, was verified by hand from its official site), 9 name-match and 63 candidates. Seven of the candidates were feeds titled "Abraham Hicks" from seven different accounts, which
is the case the rule exists for.

## Known limits

* `creator_files.csv` holds 97 Kryon rows whose YouTube twin came from ArchiveShelf's resolver. An independent
  read of that resolver found wrong matches among its 112 (one file given to several videos, and part numbers
  not checked). Rows where one file was claimed by several videos already have no twin; the remaining 97 are
  resolver output, not checked by a person.
* 42 Kryon files on Spanish-language hosts were left out of this pass.
* `publisher_pages.csv` lists 4,958 Daniel Scranton posts from his sitemap. Posts from 2015 on embed their
  video through YouTube's privacy-mode host; the id is read from the saved page, and an id that appears on
  more than a fifth of a site's pages is treated as page furniture, not as that post's video.
* Four person ids here (`sounds-true`, `kristin-davies`, `saraharyana`, `arkayla`) come from the ArchiveShelf
  inventory and are not in `research/notes/CANONICAL_IDS.md` yet.
