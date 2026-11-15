# Batch pipeline: audio and transcripts for the tracked channels

Code to take a list of YouTube videos to private audio files and timestamped transcripts, in parallel, with every step resumable. It was built on 2026-11-11 for the plan in [`../ROADMAP.md`](../ROADMAP.md). Everything is standard-library Python except the two external tools it drives (yt-dlp and faster-whisper) and ffmpeg.

**Status in one paragraph.** The code is written and covered by automated tests that use stand-in downloader and encoder tools. The parts that can run offline were also run for real: ffmpeg encoded mono Opus, faster-whisper `tiny.en` transcribed a public speech clip, and yt-dlp accepted every flag the scripts use. A real YouTube pilot was tried once from a cloud server and was refused on all 3 videos (two bot checks and one HTTP 403), so the scripts stopped, as designed. No audio has been downloaded. The download has to be run from the owner's own computer. Nothing was run on Windows or on a GPU.

## Lanes (added 2026-11-13)

YouTube refuses audio and caption requests from cloud servers, so the pipeline now collects from every place a
recording or its text is published, and labels each item with the lane it came from. All lanes write the same
manifests, so `transcribe.py`, `verify.py`, `catalog.py` and `export_public.py` work on all of them.

**The YouTube lanes are off until the owner decides (2026-11-14).** youtube.com's robots.txt disallows, for every
user agent, `/youtubei/` (which yt-dlp's channel listing beyond the first page, its player and its caption requests
all go through) and `/feeds/videos.xml` (the channel RSS), among other paths. The project obeys robots.txt, so
`discover.py`, `fetch_captions.py` and `download_audio.py` send nothing unless `ET_YOUTUBE_ROBOTS_OVERRIDE=1` is
set. Without it each of them says so in one line and ends with exit code **9, skipped by rule**; `run_cycle.py`
reports that step as "skipped by rule" and goes on, and `run_all.py` leaves those lanes out of its plan. Without
the variable, no Python request goes to a YouTube path that robots.txt disallows, not even through a redirect
(`feeds.open_url` refuses it, error class `robots`); with it set, `feeds.open_url` and its redirects send those
requests too, in every step of the process that has it. The two steps that read allowed YouTube pages (a channel's
page in `discover_sites.py`, the oEmbed lookup in `host_channels.py`) read robots.txt first. Setting the variable
is the owner's decision, not a workaround: it says the owner accepts sending requests that robots.txt
disallows. The YouTube Data API is a different route, with its own terms and an API key of the owner's; it is
not used here.

| Lane | Source | Script | Works from a cloud server? |
|---|---|---|---|
| YouTube audio | the video itself, through yt-dlp | `download_audio.py` | **Off by rule** (above). Technically, **no** as well: tried twice from cloud machines (2026-11-11 and 2026-11-13), every request got "confirm you're not a bot". |
| YouTube captions | YouTube's own caption tracks | `fetch_captions.py` | **Off by rule**; technically no, same reason. Written and tested against a stand-in; not yet run against YouTube. |
| YouTube channel listing | what each channel lists on its Videos, Live and Shorts tabs: ids, titles, lengths. No media | `discover.py` | **Off by rule** since 2026-11-14. Technically yes: it answered from the cloud on 2026-11-13, and those listings set the size of the job. |
| Podcast episodes | the enclosure of each item in the maker's own feed | `find_feeds.py`, `fetch_feeds.py`, `select_episodes.py`, `download_enclosures.py` | Yes |
| Creator files | audio the maker hosts on their own site | `select_episodes.py`, `download_enclosures.py` | Yes |
| Publisher texts | transcripts the publisher wrote (site pages, feed transcript links) | `fetch_publisher_text.py` | Yes |

Items that do not come from YouTube get the id `pod-<16 hex>` (podcast episode) or `web-<16 hex>` (creator file
or page). Where the same recording is also an indexed YouTube video, the item records that id as `twin_of` and
how the link was made (`link`, `title`, `page-embed`, `creator-index`). A podcast edition can differ from the
video (intro, adverts), so it is never counted as a YouTube download.

Text is counted in three kinds that are never mixed: **publisher texts** and **captions** come from the source;
**machine transcripts** are made here by speech-to-text from downloaded audio. `catalog.py` writes the
per-person table with those columns to `../plan/coverage.csv`.

### The one list of everyone tracked

`targets.py` joins the three bodies of work that named people and channels (this index, the ArchiveShelf
channel intake in [`../sources/archiveshelf_intake.csv`](../sources/archiveshelf_intake.csv), and people added
since) and writes [`../plan/targets.csv`](../plan/targets.csv): one row per person with where the name came
from, the channel and what it lists, what is registered outside YouTube, what is in the archive, and a state.

| State | Meaning |
|---|---|
| `captured` | every listed piece of work is in the archive, and the person's channel has been listed, so "every" includes its videos |
| `partly captured` | some of it is |
| `planned: source found` | a feed, files or pages are registered and nothing is fetched yet |
| `planned: YouTube only` | a channel is known and nothing else: it waits for the owner's decision on YouTube's robots.txt (and then a home connection) |
| `planned: no source yet` | no channel or site is known |
| `unresolved` | a name nobody has tied to a channel (three truncated names from ArchiveShelf's screenshot) |
| `excluded` | left out at the owner's request |

A video and the podcast episode or page that carries the same content are **one piece of work**: the pair is
listed once and is captured as soon as either side is here. [`../plan/bashar_host_channels.csv`](../plan/bashar_host_channels.csv)
lists the channels behind the 75 Bashar recordings (the official channel, 16 interview shows, the re-upload and
clip channels) with what was read in October and what is in the archive now.

`list_site_pages.py --only <person>` names the families of addresses in a person's own sitemap (`/post/…`,
`/blog/…`), and with `--match` and `--merge` registers the chosen ones in `publisher_pages.csv`.

### Interviews: the host lane

The 75 Bashar recordings sit on 38 channels. `host_channels.py` finds each channel's address through
YouTube's public embed lookup and reads the websites the channel declares
([`../sources/bashar_host_channels.csv`](../sources/bashar_host_channels.csv)); with `--recordings` it asks, once
per recording, whether YouTube still has it
([`../sources/bashar_recordings_status.csv`](../sources/bashar_recordings_status.csv): 68 do, 6 are gone and 1 is
private).

Sixteen of the 38 are interview shows, and most interview shows also publish their episodes as a podcast:
a file on the show's own host, which a cloud server can fetch. `find_host_feeds.py` looks each show up in
Apple's podcast search and registers its feed as a **host feed** when the name fits and either the feed
lives on a website the show's channel declares or the feed carries an interview of the list. Nine were found.
"The name fits" means the distinctive words are shared as a phrase or nearly all of them match: a long
subtitle that happens to contain "next", "level" and "soul" somewhere is another show.

A host feed is never taken whole. `select_episodes.py --relation host` keeps only the episodes whose title
names a tracked person: 186 of the nine feeds' episodes do, for 27 people (246 hours), 42 of them Darryl Anka
or Bashar. For 17 of the 27, Darryl Anka among them, these interviews are the first source outside YouTube.
An episode from a show's own feed and a
video on that show's own channel with mostly the same title words and the same numbers are the same
interview (`twin_method: title-same-show`), so the Bashar table counts it for the recording in the list.

### What kind of interview: live channeling, or talk about it

An interview's audio is queued only when the entity speaks in it (since 14 November; audio fetched before
that is kept whatever its kind), while the feed's own transcript is fetched for every listed episode.
`interview_types.py` gives every listed interview episode a kind, and says what the kind rests on:

| Kind | Rests on |
|---|---|
| `live channeling` | the entity's own signature in the episode's transcript (Bashar's greeting "this day of your time", or the entity naming itself or being greeted by name), or show notes that say the session is channeled live in this episode |
| `unclear` | a transcript with many marks of an entity addressing humans ("your planet", "as you call it") and no signature: a conversation with channeled passages, or one about channeling |
| `conversation` | a transcript with neither |
| `commentary or clip` | a short episode whose title carries only what the person channels, not their name |
| `not classified` | no transcript is held and the show notes do not say |

A fifth basis outranks all of these: **a reading**. A reader given the whole transcript (the
`et-interview-reader` agent, a small model; or a person) says what the episode is and where in it the
entity starts and stops speaking. Verdicts are kept in `<root>/sources/interview_readings.jsonl`, and the
label then says "read in full by ...". The phrase rules only look for marks; a reader notices that Kryon
is brought in halfway through, or that "Bashar says" is Darryl Anka talking.

**A title never makes an episode live channeling.** Eleven Bashar interviews came with the publisher's own
transcript, several titled "Bashar's Channeled Message ...": all are conversations with Darryl Anka in which
nothing is channeled. A sentence such as "I am going to channel" is not used either: in the transcripts read
it was always part of a story. Show notes count only when they speak of the episode itself ("the episode
concludes with a live channeling of ..."), not when they advertise an event or describe the guest.

`select_episodes.py` queues only `live channeling` by default (`--interview-types all` to change that); the
others stay listed with their kind in the catalogue, the coverage table and the dashboard. A transcript that
a podcast feed itself links (`<podcast:transcript>`) is fetched like the episode's audio, because the feed
hands it to podcast apps: a file store that has no robots.txt and answers 403 for it no longer hides it, a
robots.txt that says no is still obeyed, and a site that cannot be reached is left alone for the run.

### Channeled sessions on archive.org

The Bashar Index data package at the top of this repository (`data/session_catalog.csv`) catalogues 684
Bashar sessions since 1984, and 393 of its entries (392 distinct items) point at a recording somebody
deposited on archive.org; 274 more are only on the official streaming site, which is paid and is not
collected. Those are the channeled sessions themselves, not interviews, so the interview rule (fetch only
when the entity speaks live) does not apply to them. `list_archive_org.py` asks archive.org's public metadata service what
each item holds and writes [`../sources/archive_org_sessions.csv`](../sources/archive_org_sessions.csv): audio
files (tape transfers, small) are queued like any other recording, with ids `ia-<16 hex>`; video files run
to gigabytes each and are only listed. `targets.py` also writes three tables from that data package:
`plan/bashar_recordings.csv` (the 75 digested recordings, each with its kind and where it stands),
`plan/bashar_sessions.csv` (the catalogue by decade) and `plan/bashar_podcasts.csv` (the 48 podcast
appearances it listed, with the type it gave and the kind found here).

### A long run has to survive its accidents

A two-process speech-to-text run lost a worker six times on 2026-11-13, each time stopped from outside
(signal 15) while tests and downloads ran beside it and memory was short. Without care that halves a
two-day run. On this 8 GB machine the bulk run therefore uses one process with two threads (11% slower,
half the memory), restarted by a loop if it is stopped. `transcribe.py` now restarts a worker that ends early. A worker that ended by itself
(a fault inside a native library leaves no Python error) skips the file it was on, which is recorded as
`worker_died`; a worker stopped from outside tries its file again. `--restarts` caps it at 20 per worker.

### Three mistakes found on 2026-11-13 (evening), and what stops them now

| What happened | Now |
|---|---|
| The podcast lookup accepted two shows by **other people called Michelle Robinson** (a yoga teacher and a media host): author and title matched the name | When a show gives a website of its own that is not one of the person's known sites, the name counts only if that website links to the person's YouTube channel (`--check-links` asks). A show set aside this way still counts as a claimant, and once a namesake is known the name alone settles nothing for the others. Both rows were removed before anything was downloaded |
| A **German** podcast (Pavlina Klemm) had one episode transcribed with the English-only model, which wrote confident English nonsense that was counted as a transcript | `transcribe.py` reads each feed's stated language. A recording in another language than the run's is left out and named with the command that fits it (`--model base --language de --only pavlina-klemm`). The bad transcript was marked as an error and redone |
| "Captured" was said of people whose **YouTube channel had not even been counted** | The channel listing is part of the catalogue: every listed video, live stream and short is an item, and a twin that is here covers its video |

Also fixed: with several worker processes `--order round-robin` was undone by a longest-first split (each
process now gets every person in turn), and the catalogue could not see the transcripts of a multi-process run
until it ended.

### Speech-to-text on this machine: what was measured

The Codespace's two CPUs are two threads of one core. Measured on 300 seconds of podcast speech and on a
1981 tape (Ra Contact session 45, 22 minutes) against the publisher's own transcript:

| Engine (CPU, int8) | Podcast speech, times real time | Old tape, times real time | Tape word error rate | Words that differ from `base.en` on the podcast |
|---|---|---|---|---|
| faster-whisper `base.en`, one process, 2 threads | 9.2 | 40.1 | 0.729 | – |
| faster-whisper `base.en`, **two processes, 1 thread each** | 10.3 together | 44.4 together | 0.729 | none |
| faster-whisper `tiny.en` | 16.5 | 76.0 | 0.749 | 5.1% |
| faster-whisper `distil-small.en` | 4.0 | 15.9 | 0.726 | 7.0% |
| Parakeet TDT 0.6b v3 (onnx-asr, with silero VAD) | 3.2 | 7.7 | 0.831 | 4.9% |

So the bulk run uses `base.en` with `--workers 2 --cpu-threads 1` (12% more than one process). `tiny.en` is 1.8
times faster and a little less accurate; the larger models are too slow here. The tape's error rate is mostly
quiet passages the voice detector drops (553 of 866 words recovered): for the Ra sessions the published
transcript is the text to use. At this speed the 476 hours held take about two days of machine time; a
machine with eight real cores or a GPU would take hours.

### One command on your own computer

`run_all.py` starts the lanes side by side with a watcher that uploads finished items to your private store,
checks each copy, and deletes the local file. Without `--go` it only prints the plan. Its YouTube lanes run only
if the owner has decided to send requests that youtube.com's robots.txt disallows and set the variable
(`$env:ET_YOUTUBE_ROBOTS_OVERRIDE = "1"` in PowerShell, `export ET_YOUTUBE_ROBOTS_OVERRIDE=1` in a Unix shell);
without it they are left out of the plan, and a run of YouTube lanes alone ends with exit code 9.

```powershell
python et-channelers\pipeline\run_all.py --store gh:YOU/PRIVATE-REPO@audio-v1            # show the plan
python et-channelers\pipeline\run_all.py --store gh:YOU/PRIVATE-REPO@audio-v1 --go      # run it
python et-channelers\pipeline\run_all.py --store dir:D:\et-archive --lanes youtube,captions --set bashar75 --go   # only with the variable
```

`--store gh:OWNER/REPO@TAG` puts tar bundles on a release of a **private** GitHub repository through the `gh`
command you are logged in with. The repository's visibility is read before anything is downloaded and the run
stops (exit code 5) unless it is private; there is no flag to override that. `--store dir:/folder` copies into
any folder outside a Git checkout (an external disk, or a folder your Drive client syncs). Exit codes: 3 a
source refused requests, 4 the disk floor was reached, 5 the store was refused, 6 a run of setup faults, 8 another
cycle was running (`run_cycle.py`), 9 skipped by rule (a YouTube step without `ET_YOUTUBE_ROBOTS_OVERRIDE=1`).
`sync_archive.py` can also be run by itself (`push`, `status`, `pull`).

### A browsable copy on Google Drive

`drive_stage.py` lays out what the store holds as files for the owner's Google Drive, under one top folder:
`04 Audio/<person>/<group>/<date> <title> [<item id>].opus` (groups: "Podcast - <show>", "archive.org
sessions", "Audio from own website", "Interviews on other shows") and `03 Transcripts/<person>/`, where
texts from the source and speech-to-text made here are separate volumes, never one file. Audio is never
re-encoded: a file over 7.3 MB is cut between Ogg pages into parts that each play on their own. The ledger
`<root>/sync/drive_manifest.jsonl` holds the Drive id of every folder and file, so a later run plans only
what is new or changed.

```bash
S=~/et-drive/stage                       # outside any Git checkout
python3 -I et-channelers/pipeline/sync_archive.py pull --root ~/et-channelers-private --store gh:OWNER/REPO@TAG --kinds audio --only darryl-anka
python3 -I et-channelers/pipeline/drive_stage.py plan    --out $S --only darryl-anka --kinds audio
python3 -I et-channelers/pipeline/drive_stage.py batches --out $S --n 1 --link-dir <folder the uploader may read>
python3 -I et-channelers/pipeline/drive_stage.py round   --out $S --size 200     # numbered: title, parent id, file, type; and its id
# ... upload each file of the round, then hand back one "i <Drive id>" line per upload:
python3 -I et-channelers/pipeline/drive_stage.py done    --out $S --round <id> < ids.txt
python3 -I et-channelers/pipeline/drive_stage.py status  --out $S
```

The uploads are done by whoever holds the Drive login. With the Claude Google Drive connector, one call
sends one file, by reference, only from the main session's scratchpad folder and only a file with a single
hard link: `--link-dir` copies each file there under a plain name. About two seconds per 7 MB file; two
messages of 100 calls make a round of 200. `round` prints the round's id, and `done` takes back only numbers
of that round (`--round <id>`): once part of a round is recorded, `round` numbers the rest afresh under a new
id, and the old numbers are refused (the refusal lists those uploads' Drive ids, to trash on Drive). `done`
also refuses a number outside the round, one given twice, one whose file changed or left the plan after the
round was printed, and a Drive id that the ledger already holds for another file, and records the rest; it records only the lines it is
given (every round's lines are also kept in `<out>/results.jsonl`). rclone with a one-time Google login would do the same unattended (not set up).

While new audio arrives, the sync would delete each file once it is stored, before its Drive round. A Drive
hold keeps it: `ET_DRIVE_HOLD=1 bash et-channelers/pipeline/resume_jobs.sh` starts a holder (a long `sleep`)
and its note, and `drive_hold.py --root <root>`, run after each round, lists in the note every file on disk
that is not yet on Drive with all its parts. Once a round is recorded, its staged copies (`<out>/files/` and
the copies in the link folder) can be deleted.

### What changed in the YouTube lane on 2026-11-13

An independent read of the code found three faults, now fixed and covered by tests:

* YouTube's session rate limit arrives as "Video unavailable. This content isn't available, try again later".
  It was filed as a removed video and skipped for good. It is now a hard block that stops the run.
* "Requested format is not available" (yt-dlp found no formats at all, usually a setup fault) was also filed as
  a removed video. It is now its own class, tried again on later runs, and eight in a row stop the run.
* The default pace was a start every 1.5 seconds with 4 workers. It is now 2 workers and a start every 10
  seconds, with yt-dlp's `--sleep-requests 0.75`, which is yt-dlp's own advice for staying under the limit.

Proxy settings in the environment are now removed before any tool is started, so "no proxies" is enforced, not
only stated. Python 3.10 or newer is needed (the code uses 3.10 syntax; the earlier "3.9" was wrong).

### Review of 2026-11-13: what was wrong and what changed

Before this work was merged, four reviewers each took one risk (lost files, conduct toward the hosts,
private material leaking, wrong numbers) and had to show a concrete failure, not a suspicion. Every finding
below was first reproduced as a failing test, then fixed.

| Found | Now |
|---|---|
| Running the same command again downloaded everything that had already been uploaded and deleted, then deleted it without uploading | every step reads the sync ledger: an item with a checked copy in a store is finished |
| A ledger line was trusted without looking: a file that changed after its upload, or a store that had been emptied, still led to the local copy being deleted | before a delete the file's SHA-256 is taken again and compared with the ledger, and the store is asked whether it still holds the item; if not, the item is sent again first |
| With the store folder the same as the private folder, the second run deleted every recording | refused at start; a store path that is the same file as the local one (a link) is refused too |
| The first push to a new GitHub release always failed | the release is made before anything is uploaded; a GitHub outage is reported as one, and creates nothing |
| The repository's visibility was read once per run | read at the start of every pass |
| Captions: a refusal after the first track counted as success; "Your IP is likely being blocked" was not a block; `en.*` asked YouTube for a machine translation per language | all three fixed; named English tracks only |
| A robots.txt that could not be read marked every page of that site as refused, for good | a third answer, "could not be read": nothing is fetched this run and the pages are tried again next run |
| A refusal was charged to the first address of a redirect chain, so one refusing media host stopped every show behind the same redirector, or none | charged to the host that refused, remembered per feed; items that failed before go to the back of the queue |
| A host answering only errors was asked again for every item | left alone for the run after six in a row |
| A podcast item's id depended on the feed's address, so a feed that moved would be downloaded and counted twice | ids are made from the person and the episode's own guid (`migrate_ids.py` renamed the 503 files already held) |
| A feed that names the maker's site as its website was graded `verified` | only the official site linking the show, or the feed being served from the official domain, verifies |
| Title matching joined "Day 10" with "Day 11", and one video could be the twin of many episodes | numbers must agree, both lengths must be known and close, one video has one twin; the rest are `twin_candidate` and are not counted |
| The coverage table was built from whatever queue file existed | built from the source lists; the queue is only a work order |
| The guard did not recognise what these lanes write | item files, saved pages, the private catalogue, queues, manifests and bundles are flagged |
| The runner's defaults undid the slower YouTube pace | 2 workers, one start per 10 seconds, captions never faster than audio |

Not fixed, by choice: the GitHub release is an ordinary one, not a draft (a draft would stay hidden if the
repository were made public, but `gh` behaviour with drafts was not tested here). Use a repository made for
this purpose, with no public past.

### Review of 2026-11-14: what was wrong and what changed

The same four risks again, on the store, the cycle loop and the sources table. Each finding was reproduced
before it was fixed, and each fix has a test.

| Found | Now |
|---|---|
| The deleting sync removed audio that `transcribe.py` had open or queued; the finished transcript was then recorded as an error, never stored, and never made again | each `transcribe.py` run names the files it has queued in `<root>/sync/holds/`, and the sync keeps them until they are transcribed; the audio is hashed before the work, and a file that is gone is skipped, not failed, so a later pass makes it (earlier `FileNotFoundError` errors are tried again). `ET_HOLD_UNTRANSCRIBED=1` keeps everyone's audio until it has a transcript |
| After one failed manifests upload, the next pass deleted local audio while the store's ledger did not list it, so a fresh folder could not read it back | every pass that deletes anything sends the current ledger first, and deletes nothing if that send fails |
| "Never two downloaders" was one look at the process list: two downloaders ran at once on overlapping queues | every downloader takes a lock in `<root>/jobs/` (a second waits, then reads what is left; shards of one queue may run together); a second `keep_collecting.sh` leaves at once; a cycle started while another runs does nothing (exit code 8) |
| A host that refused was asked again in every cycle; nothing read Retry-After; one or two refusals ended a run with code 0 | a refusing host rests a day at least, longer if its Retry-After says so, doubling with each further spell (`common.resting_hosts`, from each step's own manifest; `--ask-resting` overrides); any 403 / 429 ends the run with code 3; a Retry-After over ten minutes ends that host's turn for the run |
| `interview_types.py --notes` downloaded every interview feed again in every cycle, with no refusal handling | `fetch_feeds.py` keeps the names of the marks in each interview episode's show notes (never the notes) from the read it makes anyway; `interview_types.py` fetches nothing (`--notes` is accepted and ignored) |
| Requests waiting for their turn still went out after a host's third refusal | the breaker is checked again after the wait, in every fetcher |
| `mirror_texts.py --remote` was never compared with `--repo`; the origin check read one fetch address while the push went to the push addresses; a link inside the checkout could lead writes into the public repository; one failed push beside a second writer left the mirror stuck in a rebase | `--remote` must be an address of `--repo`; the checkout must have one fetch and one push address, both of that repository; nothing is written through a link that leads out of the checkout; each run starts from the remote's branch and pushes to it by name; a failed run is logged as one |
| The sources table: 257 texts counted under no source; a channel row counting 63 videos of other channels; "here" counting a page's text as the file held; a never-listed channel shown as "listed" with 0; notes counting list rows (937 files, 1,775 pages) against the catalogue's numbers; a fixed claim that only live channeling is downloaded; ArchiveShelf linked | every catalogue item lands on one row (a row is made for what no list names); a channel row counts its own listing; `items_here` is what the source yields, with `audio_here`, `texts_from_source` and `texts_made_here` beside it; an unlisted channel has no count and says "not listed yet"; notes say what they count; the interview note is built from the counts; ArchiveShelf rows link this repository's intake list. archive.org audio is counted once per recording everywhere (903, not 937) |
| Three "official sites" were a platform's home page (Crowdcast, the Libsyn directory, LINE) | those services are platforms in `discover_sites.py`, and the three rows are gone |
| (pre-merge review, 2026-11-14) archive.org sends every file from one of about a hundred storage nodes, so its own host was never credited with a success: one 403 from it would have held back every queued Bashar session for a day or more. The node of the last answer also stood for the whole site (and for a Podbean feed, whose episodes come from dozens of nodes), across runs and within a run | a success counts for the first hop too; an item is held back by the host that last answered for it, and a feed or site only when its last three items all came from one host that is being left alone (`MediaHosts`); no redirect is followed to a host that is being left alone (`Hops`), and a connection that fails after a redirect is charged to the host it led to |
| A short Retry-After from the host a redirect led to was stored but never waited for; a Retry-After sent with a 503 was ignored (audio, feeds, texts) | every host a redirect leads to waits for its own turn and its own Retry-After (first in the audio lane; now in the feeds, texts and site-pages lanes too, see the last row); a 503's Retry-After delays the host's next request, and a wait over ten minutes ends the host's turn for the run |
| A 429 for a site's robots.txt was recorded as a network error, so every cycle asked again | it is recorded as a refusal (rate limited, with its Retry-After), so the site rests on later runs |
| `drive_stage.py done` gave the ledger every earlier round's lines again, which could record a new version of a text volume at an old Drive id and never upload it; after a partial `done`, `round` numbered the rest afresh and old numbers went to other files | `done` records only its own lines; `round` prints a round id that `done --round` must be given; a Drive id already recorded for another file is refused |
| `keep_collecting.sh`'s lock was inherited by its cycle and its sleep, so after `kill <pid>` a new loop reported one running and left | the children do not inherit the lock |
| `mirror_texts.py` read the remote's branch as "HEAD" when the checkout had no `origin/HEAD` | read with `git symbolic-ref`, which says nothing then, so the fallback applies |
| Hours in the summaries added values already rounded per row (911.2 instead of 911.3) | the totals add unrounded hours and round once |
| (second pass, checking the fixes) A host in the middle of a redirect chain was never credited with a success, so one refusal from it held back every episode behind it; three files of one archive.org item, which sit on one node, made that node stand for the whole site | every host along the way is credited (`via_hosts` in the record); files without a feed are never grouped |
| A request already waiting for its turn went out despite a Retry-After the host sent meanwhile; a download that started before a 429 and ended after it erased the refusal; a lone 403 with a Retry-After of days was asked again on the next run; a huge Retry-After crashed every later run | the limiter holds waiting requests too; a success clears only refusals that came before it started (`started` is the moment the request goes out); a refusal's Retry-After holds the host on later runs; a Retry-After is capped at 32 days |
| `list_site_pages.py` read robots.txt twice, the second time outside the site's turn; one 429 for robots.txt was counted 3 to 10 times | read once, through the gates; counted and recorded once |
| `done` recorded an upload whose file had changed or left the plan since the round was printed, so the new version was never offered; an old round's ids were refused with no word on what to do with them | `done` refuses such a number and says to trash that upload; the round id covers the files' checksums; a refused old round lists its uploads' Drive ids, to trash |
| (after the merge of 2026-11-14) The feeds, texts and site-pages lanes followed a redirect without the audio lane's rules: every refusal and Retry-After was charged to the first host of the address, so a host that had refused three times on a run was still reached through another host's redirect, a host resting from an earlier run was reached that way too (robots.txt included), and a 429 from the host a redirect led to held back the first host, which never refused, while the refusing host's own next request went out at once | `Hops` is in `feeds.py` and `get_bytes` takes it (`before_redirect`); the audio, feeds, texts and site-pages lanes use it: no redirect is followed to a host left alone on this run, or (audio, feeds, texts) resting from an earlier one (the item is not asked for and not recorded), each host along the way waits for its own turn and Retry-After, an answer is charged to the host that gave it (`final_host`, `via_hosts`), and a success counts for every host along the way, on this run and on later ones (`common.resting_hosts_along`, one helper for the three lanes that remember refusals) |

## Rules for the data

| Data | Where it lives | May it go into Git? |
|---|---|---|
| Audio, captions, transcripts, QA sheets | the private folder (default `~/et-channelers-private`, set with `--root` or `$ET_PRIVATE_DIR`) | **No, never.** Every script refuses a folder inside a Git checkout. |
| Manifests (`audio_manifest.jsonl`, `transcripts_manifest.jsonl`), queue, discovery lists | the private folder | Only after review. They contain titles and error text. |
| `public_export/media_manifest_public.csv` | the private folder | Yes, after review. Numbers and hashes only: no text, no paths. |
| Inventory and estimates | [`../plan/`](../plan/) | Yes. Public metadata only. |

The recordings belong to their rights holders (the Bashar sessions: Darryl Anka / Bashar Communications, Inc.), and downloading media from YouTube is outside YouTube's terms unless a feature offers it. That is why the output is private and nothing derived from it is published before the paper. [`../scripts/guard_no_raw_media.py`](../scripts/guard_no_raw_media.py) fails if the repository holds audio, caption files, speech-to-text JSON, files over 5 MB, or credentials; run it before every push.

**What the scripts will not do.** They use no cookies, logins, proxies, alternative player clients or mirror sites. If YouTube answers with a bot check, HTTP 403 or 429, the run stops after three such answers in a row (exit code 3) and nothing is retried into the block. Removed, private and age-gated videos are recorded once and skipped on later runs. The tests assert that the command lines contain none of those options.

## Setup

You need Python 3.10 or newer, ffmpeg (with the libopus encoder), and for transcription an NVIDIA GPU is strongly recommended.

```powershell
# Windows PowerShell (macOS/Linux: use python3, source .../bin/activate, brew/apt for ffmpeg)
winget install Gyan.FFmpeg                         # once; open a new terminal afterwards
git clone <this repository>; cd <repository folder>
python -m venv $HOME\et-venv
& $HOME\et-venv\Scripts\Activate.ps1
pip install -r et-channelers\pipeline\requirements.txt
python et-channelers\pipeline\doctor.py --root $HOME\et-channelers-private
```

`doctor.py` lists what is installed, what is missing and how to fix it. It checks ffmpeg and libopus, yt-dlp, a JavaScript runtime (yt-dlp needs one for YouTube; `pip install deno` is in the requirements), faster-whisper, whether CTranslate2 sees a GPU, and the free space on the data drive. For GPU use, faster-whisper needs the NVIDIA cuBLAS and cuDNN 9 libraries for CUDA 12; see the GPU section of the [faster-whisper README](https://github.com/SYSTRAN/faster-whisper#gpu).

## Run order

These steps request YouTube paths that its robots.txt disallows: they run only after the owner's decision, with
`$env:ET_YOUTUBE_ROBOTS_OVERRIDE = "1"` (HANDOFF section 6). Without it steps 2 to 4 end at once with exit code 9.

```powershell
$P = "et-channelers\pipeline"
python $P\select_jobs.py --set bashar75                 # 1. queue of the 75 Bashar recordings
python $P\download_audio.py                             # 2. dry run: how many, how long, how much disk
python $P\download_audio.py --limit 3 --workers 1 --min-interval 3     # 3. pilot, 3 videos
python $P\download_audio.py --all --workers 3 --min-interval 3         # 4. everything in the queue
python $P\verify.py --hash                              # 5. sizes, hashes, durations
python $P\transcribe.py --limit 3 --model large-v3 --devices 0         # 6. transcription pilot on the GPU
python $P\transcribe.py --model large-v3 --devices 0 --model-revision <commit>   # 7. everything, model pinned
python $P\verify.py --hash --qa-sample 20               # 8. checks + sheet for a human word-error-rate check
python $P\export_public.py                              # 9. publishable numbers and hashes
```

If step 3 prints `STOPPED` (exit code 3), do not push on: wait, lower `--workers`, raise `--min-interval`, or stop. Finished items are skipped when you rerun. To work from audio you already hold, put files named `<11-character-video-id>.opus` (or `.m4a`, `.mp3`, `.wav`, ...) in `<root>/audio/<channel>/` and start at step 6.

For the other channels: `discover.py` lists every video on each tracked channel (public metadata; off by the same rule), `select_jobs.py --set all --per-channel 20 --seed 7 --min-seconds 300` draws a reproducible sample, or `--newest N` takes the first N of each channel's Videos tab in listing order (newest first; `run_all.py --newest N` lists only that much of each channel), and the same download and transcription steps follow. Two machines can split a queue with `--shard 0/2` and `--shard 1/2`.

## The scripts

| Script | Job | Notable options |
|---|---|---|
| [`inventory.py`](inventory.py) | channel and video totals and hour/disk estimates from the committed index; rewrites the table in the README | `--update-readme`, `--refresh-bashar75` |
| [`select_jobs.py`](select_jobs.py) | builds the queue from the Bashar-75 list, the index, and discovery output | `--set bashar75\|indexed\|channeling\|all`, `--per-channel K --seed N`, `--newest N`, `--min-seconds`, `--max-seconds`, `--order`, `--shards N`, `--export-ids` |
| [`prediction_timeline.py`](prediction_timeline.py) | the rules pass of ANALYSIS_PLAN 12.4: statements about the future in each person's texts, each with a target window counted from the date said, laid out as a timeline per person; texts from the source and speech-to-text kept apart. Output stays in the private folder (it quotes, at most 30 words); counts only can go to `plan/` | `--only`, `--kinds made,source`, `--listing <videos_all.jsonl>` (approximate dates for YouTube rows), `--publish-counts` |
| [`prediction_pilot.py`](prediction_pilot.py) | a pilot of the model pass: a seeded, blinded sample of the candidates with a target window (no person, title or date shown) for two independent coders, and the score of their labels (agreement, Cohen's kappa, and the share each calls prediction-like, by kind and time rule); private, the score holds counts and ids only | `sample --per-person --seed`, `score` |
| [`discover.py`](discover.py) | every video, live stream and short on a channel via yt-dlp flat listing (off unless `ET_YOUTUBE_ROBOTS_OVERRIDE=1`), one atomic file per channel, coverage against the expected count | `--only id,id`, `--tabs`, `--workers`, `--min-interval`, `--page-pause`, `--retry-failed` |
| [`targets.py`](targets.py) | the one list of everyone tracked, with origin, channel, sources, capture counts and state; and the channels behind the 75 Bashar recordings | `--no-private`, `--out` |
| [`list_site_pages.py`](list_site_pages.py) | names the address families in a person's own sitemap and registers the chosen pages | `--only`, `--match`, `--exclude`, `--merge` |
| [`host_channels.py`](host_channels.py) | the address, id and declared websites of each channel behind the Bashar list; whether each recording is still on YouTube | `--all`, `--recordings`, `--refresh` |
| [`find_host_feeds.py`](find_host_feeds.py) | the podcast feed of each interview show in the Bashar list, graded, registered as a host feed | `--all`, `--merge`, `--kinds` |
| [`interview_types.py`](interview_types.py) | the kind of each listed interview episode (live channeling, unclear, conversation, commentary or clip), from its transcript or the marks of its show notes that `fetch_feeds.py` keeps; fetches nothing | `--only` |
| [`list_archive_org.py`](list_archive_org.py) | the audio and video files behind the session catalogue's archive.org entries | `--all`, `--refresh` |
| [`run_cycle.py`](run_cycle.py) | one collection cycle from a cloud server: list (skipped by rule without `ET_YOUTUBE_ROBOTS_OVERRIDE=1`), feeds, queue, fetch, texts, interview kinds, tables. What the agents run (see Phase 7b of the roadmap) | `--go`, `--skip`, `--max-hours`, `--transcribe`, `--interview-types` |
| [`download_audio.py`](download_audio.py) | (off unless `ET_YOUTUBE_ROBOTS_OVERRIDE=1`) yt-dlp downloads a small audio stream to a scratch folder, ffmpeg re-encodes it to mono 16 kHz Opus, scratch is deleted | `--limit N` (pilot), `--all`, `--workers`, `--per-channel`, `--min-interval`, `--shard i/n`, `--bitrate`, `--limit-rate`, `--retry-failed` |
| [`transcribe.py`](transcribe.py) | faster-whisper with batching and VAD; one process per GPU; longest files first so processes finish together, or every person in turn with `--order round-robin`; leaves out speech in a language the run was not asked for | `--model`, `--model-revision`, `--devices 0,1`, `--workers`, `--cpu-threads`, `--batch-size`, `--language`, `--order`, `--only`, `--compute-type`, `--shard i/n` |
| [`verify.py`](verify.py) | file sizes, optional re-hash, audio-versus-listing length, transcript sanity, audio without transcript; builds the QA sheet | `--hash`, `--qa-sample N` |
| [`export_public.py`](export_public.py) | the publishable table: durations, sizes, hashes, language, word counts, model and revision, speed | `--out` |
| [`sync_archive.py`](sync_archive.py) | puts audio, transcripts and texts in the private store as checked tar bundles, reads them back into a fresh folder, and frees the disk once a copy is checked | `push`, `pull`, `status`, `--store`, `--kinds`, `--only`, `--delete`, `--hold-untranscribed-for` |
| [`drive_stage.py`](drive_stage.py) | the Google Drive copy by person and source: names, folders, playable parts of at most 7.3 MB, text volumes, and the ledger of Drive ids | `plan`, `batches`, `round`, `done`, `record`, `status`, `--only`, `--kinds`, `--link-dir`, `--size` |
| [`drive_hold.py`](drive_hold.py) | writes into each live Drive hold note (`sync/holds/drive-<pid>.json`) the downloaded audio on disk that is not yet on Drive with all its parts, so the sync keeps it until its round is recorded; run it after each round | `--root` |
| [`resume_jobs.sh`](resume_jobs.sh) | after a restart, starts each standing job that is not running: the sync (new files held until transcribed), the collection cycles, speech-to-text in a loop, a Drive hold (`ET_DRIVE_HOLD=1`) and a backlog download (`ET_BACKLOG_QUEUE`) | environment: `ET_PRIVATE_DIR`, `ET_ASR_WORKERS`, `ET_ASR_THREADS`, `ET_HOLD_UNTRANSCRIBED` |
| [`doctor.py`](doctor.py) | checks the machine | `--root`, `--need-gb` |
| [`common.py`](common.py) | shared helpers: manifests, shards, rate limiter, circuit breaker, Git guard | – |
| [`tests/test_pipeline.py`](tests/test_pipeline.py), [`tests/test_lanes.py`](tests/test_lanes.py), [`tests/test_drive_stage.py`](tests/test_drive_stage.py) | the automated tests | – |

## How it works

* **Resumable.** Each step appends one JSON line per item to a manifest (latest line wins). A rerun skips finished work, repairs missing files, and ignores a torn last line left by a crash. Files are written to a temporary name and renamed.
* **Parallel without overlap.** Videos are split across workers and machines by a stable hash of the id (`--shard i/n`), so shards never overlap and do not depend on Python's randomised `hash()`.
* **Polite.** A global limit on how often downloads start (`--min-interval`, with a little jitter), a per-channel cap on simultaneous downloads, and a scheduler that never leaves a worker idle behind a busy channel.
* **Stops instead of pushing through.** Three hard blocks in a row (bot check, 403, 429) trip a circuit breaker; a success resets the count. Only network errors are retried (exponential backoff). A re-encode failure is not retried.
* **Remembers a refusal.** A Retry-After is obeyed, with a 403, 429 or 503. In the audio, feeds, texts (robots.txt included) and site-pages lanes a redirect follows the same rules (`feeds.Hops`): the host it leads to waits for its own turn and its own Retry-After, an answer is charged to the host that gave it (`final_host` in the record, `via_hosts` for the hosts in between), a success counts for every host along the way, and no redirect is followed to a host that is being left alone on this run, or (audio, feeds, texts) resting from an earlier one: that item is not asked for and not recorded, so a later run picks it up. A host that keeps refusing (a 429, three refusals in a row, or a refusal from a host that served nothing in the day before) is not asked again on later runs until its wait is over: a day at least, the Retry-After if longer, doubling with each further spell of refusals; any other refusal holds the host for the Retry-After it carried (`--ask-resting` asks anyway).
* **One at a time.** Each downloader holds a lock in `<root>/jobs/`, so a second one waits and then reads what is left; shards of one queue may run together. One collection loop and one cycle at a time.
* **Safe by default.** `download_audio.py` only prints its plan unless `--limit` or `--all` is given. Every script refuses a data folder inside a Git checkout.
* **Why ffmpeg encodes, not yt-dlp.** yt-dlp copies the stream unchanged when the source is already Opus, which would ignore the bitrate and channel settings. The pipeline downloads a stream and encodes it itself, so every file is mono 16 kHz Opus at the stated bitrate (24 kbps is about 10.8 MB per hour).
* **Why ffmpeg decodes, not PyAV.** faster-whisper 1.2.1 calls `av.open(..., metadata_errors=...)`, which PyAV 19 rejects, and its requirement is only `av>=11`, so a fresh install fails with `TypeError`. `transcribe.py` decodes with ffmpeg and hands the samples to the model. The test suite checks this.
* **Provenance.** Each audio record keeps the yt-dlp and ffmpeg versions and the target format. Each transcript record keeps the model repository, revision and weight hash, the library version, device, compute type, speed (times real time) and hashes of the audio, the JSON and the normalised text.

## Layout of the private folder

```
<root>/
  jobs/queue.csv, queue.meta.json            what was selected, with seed and input hashes
  discover/channels/<person>.jsonl           every video on a channel
  discover/videos_all.jsonl, discover_manifest.jsonl
  audio/<channel>/<video_id>.opus            re-encoded audio
  audio/audio_manifest.jsonl                 one line per attempt: status, bytes, sha256, duration, error class
  transcripts/<channel>/<video_id>.json|.txt
  transcripts/transcripts_manifest.jsonl
  qa/qa_sample.csv                           60-second windows for a human to correct
  public_export/media_manifest_public.csv    the only file meant to leave this folder
```

## What was tested

| Check | Result |
|---|---|
| Automated tests (stand-in yt-dlp and ffmpeg written to a temp folder; no network) | pass: scheduling, worker and channel caps, start-rate spacing, resume and repair, retries, unavailable and age-gated skipping, circuit breaker (stops after three blocks without retrying, not tripped by blocks separated by successes), shard partition, Git-folder refusal, no cookie or proxy options in the command lines, transcript worker processes and per-GPU device pinning, verify and QA sheet, public export has no text or paths, repository guard, doctor |
| Safety rails broken on purpose (breaker never counts, channel cap ignored, Git guard disabled, resume ignores the manifest) | the tests failed each time, so they do test those rails |
| Real ffmpeg | mono Ogg Opus produced from a 44.1 kHz stereo file; duration read back by ffprobe |
| Real yt-dlp (2026.10.26) | every flag the scripts use is accepted; no network used |
| Real faster-whisper 1.2.1, model `Systran/faster-whisper-tiny.en`, CPU int8, 2 vCPU | transcribed a 10-second public speech clip correctly (14.5 times real time, a figure that includes start-up and means nothing for a GPU); model repository, revision and weight hash recorded; this is how the PyAV problem was found |
| Real YouTube, from a cloud server (2026-11-11) | 3 of 3 pilot videos refused: two "confirm you're not a bot" responses and one HTTP 403. The breaker stopped the run. No workaround was tried. |
| Windows, a GPU, large models, long batches | **not tested** |

Run the tests with `python3 -I et-channelers/pipeline/tests/test_pipeline.py` (116 tests, about 80 seconds alone), `tests/test_lanes.py` (251, about 7 minutes alone) and `tests/test_drive_stage.py` (14) (standard library only; the encoder and decoder tests are skipped if ffmpeg or numpy is missing).

## Known limits

* Audio at 24 kbps is a planning choice. Compare word error rate against a higher bitrate on the QA sample before committing to the full set.
* `--language en` is right for the Bashar sessions. A podcast feed states its language, and recordings in another language are left out of an English run and named; audio from YouTube carries no such statement, so for channels that are not in English pass `--language` yourself or use `--language auto` with a multilingual model.
* The channel listing has no upload dates and no lengths for shorts; YouTube's own "N videos" can differ by a few from what the three tabs list (members-only and scheduled items).
* The yt-dlp listing returns what is public today, which can differ from the counts in the index (observed 2026-10-23); `discover_manifest.jsonl` records the coverage per channel.
* The stand-in tools cannot reproduce YouTube's behaviour. Treat the first real runs on your machine as the real test, and read the first lines of `audio_manifest.jsonl` after the pilot.
