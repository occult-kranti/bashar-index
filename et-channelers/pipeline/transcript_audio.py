#!/usr/bin/env python3
"""Where the recording behind every transcript is: downloaded, still on disk, in the private store, on
Drive; and when it is not downloaded, why. Counts only can go to the repository; the per-item table stays
in the private folder.

An item has a transcript when the catalogue says one of these is "ok":
  made      speech-to-text made here (asr_status)
  source    a text the publisher wrote (publisher_text_status)
  captions  a caption track (captions_status)
The kinds are kept apart: an item is counted once under each kind it has. The kind "any" counts every item
with a transcript once.

The recording of an item. A page (relation page, or lane page) has no recording of its own: its text
belongs to the video or episode named by twin_of. When that twin is in the catalogue and its audio was
downloaded or failed, the page takes the twin's audio state (and the twin's file, store lines and Drive
parts) and the row says so in "why" and in audio_item; otherwise the page is classed by what its twin is.
Every other item is its own recording (audio_item == item_id), twin or not.

The partition. For one kind, every item with that kind of text falls in exactly one of six classes, and
    items_with_text == audio_downloaded + no_audio_page + no_audio_youtube + no_audio_interview_held
                       + no_audio_not_yet + download_failed
  audio_downloaded   the recording's audio_status is "ok" (the item's own, or its twin's for a page); or,
                     whatever the status, the recording's audio is in the store or on Drive in every part
                     (a download run that stopped between writing the file and its finished manifest line
                     leaves the status empty, and the copies settle it)
  download_failed    the recording's audio_status is "error" (the audio manifest's error_class says what
                     went wrong)
  no_audio_youtube   neither of the above, and the recording is a YouTube video, which only the owner's
                     computer can fetch: the item's lane is youtube, or the item is a page whose twin_of is
                     a YouTube id
  no_audio_page      neither of the above, a page with no twin: there is no recording to fetch
  no_audio_interview_held
                     neither of the above, an episode of an interview show (relation host) whose
                     interview_type is not "live channeling": the pipeline fetches interviews only when
                     they hold live channeling (HANDOFF; interview_types.py), so the recording is held back
                     by policy (or, when the episode is not classified yet, waits for its classification),
                     not for a download. It is left out of the --gaps queue
  no_audio_not_yet   everything else: a recording of a lane that can be fetched here (a podcast
                     enclosure, a file on the maker's site, an archive.org file), or a page whose twin is
                     an item of one of those lanes
The counts are as of the run time: collection cycles and the sync keep running, so they move between runs.
Within audio_downloaded two more partitions hold:
    audio_downloaded == in_store + not_in_store
        in_store: the store ledger has a verified "audio" line for the recording not followed by a
        withdrawn one (sync_archive.ledger)
    audio_downloaded == on_drive + partly_on_drive + not_on_drive
        on_drive: the Drive ledger has an audio line for every part (distinct "part" numbers >= "parts",
        counted from the last upload: an upload with another number of parts starts the count again);
        partly_on_drive: some parts but not all; not_on_drive: none
  on_disk counts the downloaded items whose file is at <root>/<audio_path>; it is a fact beside the
  partition, not a class of it (a file can be on disk and in the store at once). The tool checks every one
  of these sums for every row it writes and stops if one does not hold.

Outputs, in <root>/analysis/coverage/:
  transcript_audio.jsonl        one line per item with a transcript: kinds, state, why, audio_item, error_class,
                                on_disk, held (a running process asked to keep the file), in_store, store,
                                Drive parts
  transcript_audio.md           the summary
  transcript_audio_counts.csv   the counts per person and kind, with a total row per kind (person_id "all")
  --publish-counts              copies the counts to plan/transcript_audio.csv in the repository: counts only.
                                Refused together with --only: the public counts cover every person
  --gaps                        transcript_audio_fetch.csv, a queue-shaped list of the items whose recording
                                can be fetched here (lanes pod, web file, ia; not downloaded, or failed; an
                                interview-show episode only when it is live channeling), with the columns
                                of jobs/queue_cycle.csv when that file exists (an item's row is copied from
                                a queue file that has it, else built from the catalogue), else
                                video_id,url,channel_dir,title;
                                transcript_audio_pull.csv, the recordings (audio_item, once each) that are
                                in the store but not on disk and not (fully) on Drive: to be pulled back so
                                the Drive copy can be made

    python3 pipeline/transcript_audio.py --root ~/et-channelers-private --publish-counts --gaps
"""
from __future__ import annotations

import argparse
import collections
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, ID_RE, add_root_arg, ensure_outside_git, held_items, latest_by_key, layout,  # noqa: E402
                    read_csv, read_jsonl, write_csv)
from sync_archive import ledger  # noqa: E402

KINDS = ("made", "source", "captions", "any")
KIND_COLUMN = {"made": "asr_status", "source": "publisher_text_status", "captions": "captions_status"}
STATES = ("downloaded", "failed", "no_audio_youtube", "no_audio_page", "no_audio_interview_held", "no_audio_not_yet")
STATE_COLUMN = {"downloaded": "audio_downloaded", "failed": "download_failed", "no_audio_youtube": "no_audio_youtube",
                "no_audio_page": "no_audio_page", "no_audio_interview_held": "no_audio_interview_held",
                "no_audio_not_yet": "no_audio_not_yet"}
COUNT_FIELDS = ("person_id", "kind", "items_with_text", "audio_downloaded", "on_disk", "in_store", "on_drive",
                "partly_on_drive", "not_in_store", "not_on_drive", "no_audio_page", "no_audio_youtube",
                "no_audio_interview_held", "no_audio_not_yet", "download_failed")
LIVE = "live channeling"
ITEM_FIELDS = ("item_id", "person_id", "lane", "relation", "twin_of", "kinds", "state", "why", "audio_item", "error_class",
               "fetchable_here", "audio_path", "on_disk", "disk_size_differs", "held", "in_store", "stores",
               "drive_parts_seen", "drive_parts", "drive_state", "pull_back")
NOT_CLASSIFIED = ("", "not classified")
QUEUE_FIELDS = ("video_id", "url", "channel_dir", "title")
RECORDING_LANES = ("pod", "web", "ia")
OUT_DIR = "analysis/coverage"
TOTAL = "all"


# ---------------------------------------------------------------- one item
def kinds_of(row):
    return [kind for kind in KINDS if kind != "any" and row.get(KIND_COLUMN[kind], "") == "ok"]


def is_page(row):
    return row.get("relation", "") == "page" or row.get("lane", "") == "page"


def has_own_recording(row):
    """A podcast enclosure, a file on the maker's site, or an archive.org file: something this machine can fetch."""
    return row.get("lane", "") in RECORDING_LANES and not is_page(row)


def classify(row):
    """(state, why) for a catalogue row. The order of the tests is the partition of the docstring."""
    status, lane, twin = row.get("audio_status", ""), row.get("lane", ""), row.get("twin_of", "")
    if status == "ok":
        return "downloaded", "audio ok"
    if status == "error":
        return "failed", "an earlier download failed"
    if lane == "youtube":
        return "no_audio_youtube", "a YouTube video: only the owner's computer can fetch it"
    if is_page(row):
        if not twin:
            return "no_audio_page", "a web page with no recording"
        if ID_RE.match(twin):
            return "no_audio_youtube", "a page whose recording is a YouTube video: only the owner's computer can fetch it"
        return "no_audio_not_yet", f"a page whose recording is the {twin.split('-', 1)[0]} item {twin}, not downloaded yet"
    if held_by_policy(row):
        if row.get("interview_type", "") in NOT_CLASSIFIED:
            return "no_audio_interview_held", ("an interview-show episode not classified yet: interviews are fetched only "
                                               "when they hold live channeling, so it waits for its classification")
        return "no_audio_interview_held", (f"an interview-show episode of kind '{row.get('interview_type', '')}': "
                                           "interviews are fetched only when they hold live channeling, so it is held by policy")
    return "no_audio_not_yet", f"a {lane} recording not downloaded yet"


def held_by_policy(row):
    """An interview-show episode (relation host) that is not live channeling: never fetched here, whatever happened before."""
    return row.get("relation", "") == "host" and row.get("interview_type", "") != LIVE


def resolve(row, catalog):
    """(state, why, the catalogue row whose audio counts) for an item.

    A page looks through to its twin when the twin is in the catalogue and its audio was downloaded or failed;
    otherwise, and for every item that is not a page, the item's own row is the recording."""
    state, why = classify(row)
    if state in ("downloaded", "failed") or not is_page(row):
        return state, why, row
    twin = catalog.get(row.get("twin_of", ""))
    if twin is not None:
        twin_state, twin_why = classify(twin)
        if twin_state in ("downloaded", "failed"):
            return twin_state, f"the recording is the twin {twin['item_id']}: {twin_why}", twin
    return state, why, row


def settle_by_copies(state, why, audio, row, catalog, stored, on_drive):
    """A recording whose audio is in the store, or on Drive in every part, was downloaded, whatever the audio
    manifest says: a download run that stops after writing the file and before its finished line (a full
    disk, a kill) leaves the catalogue's audio_status empty, and the next run skips the item because the
    store has it. The copies settle it; so they do for a YouTube video the owner's computer fetched and this
    machine only pulled. A page looks at its twin's copies when the twin is in the catalogue."""
    if state not in ("no_audio_not_yet", "no_audio_youtube", "failed"):
        return state, why, audio
    twin = catalog.get(row.get("twin_of", "")) if is_page(row) else None
    candidate = twin if twin is not None else (None if is_page(row) else audio)
    if candidate is None:
        return state, why, audio
    item = candidate["item_id"]
    copies = ("in the store" if item in stored else "") or ("on Drive" if drive_state(*on_drive.get(item, (0, 0))) == "all" else "")
    if not copies:
        return state, why, audio
    note = f"the audio is {copies} (the audio manifest has no finished line for it)"
    if twin is not None:
        return "downloaded", f"the recording is the twin {item}: {note}", twin
    return "downloaded", note, audio


def drive_index(records):
    """{item_id: (distinct audio parts seen, parts the item has)} from the Drive ledger's audio lines.

    An upload with another number of parts than the one before it starts the count of parts seen again, so
    the parts of an old split never stand in for the parts of the new one."""
    seen, parts = collections.defaultdict(set), {}
    for rec in records:
        if not str(rec.get("mime") or "").startswith("audio") or not rec.get("item_id"):
            continue
        item, total = rec["item_id"], int(rec.get("parts") or 1)
        if parts.get(item, total) != total:
            seen[item] = set()
        seen[item].add(rec.get("part") or 1)
        parts[item] = total
    return {item: (len(seen[item]), parts[item]) for item in seen}


def disk_state(file, expected):
    """(on disk, size differs from the catalogue's audio_bytes). A file the sync removes between the two looks is not on disk."""
    if file is None:
        return False, False
    try:
        size = file.stat().st_size if file.is_file() else None
    except OSError:
        return False, False
    if size is None:
        return False, False
    return True, bool(str(expected).isdigit() and size != int(expected))


def drive_state(seen, parts):
    if not seen:
        return "none"
    return "all" if seen >= parts else "partly"


def build_rows(paths, only=()):
    """One record per catalogue item with a transcript of any kind."""
    catalog = read_csv(paths.root / "catalog" / "catalog.csv")
    manifest = latest_by_key(read_jsonl(paths.audio / "audio_manifest.jsonl"))
    stored = collections.defaultdict(set)
    for (video_id, kind, store) in ledger(paths):
        if kind == "audio":
            stored[video_id].add(store)
    on_drive = drive_index(read_jsonl(paths.root / "sync" / "drive_manifest.jsonl"))
    held = held_items(paths.root)
    by_id = {r["item_id"]: r for r in catalog}
    rows = []
    for row in catalog:
        kinds = kinds_of(row)
        if not kinds or (only and row.get("person_id", "") not in only):
            continue
        state, why, audio = resolve(row, by_id)
        state, why, audio = settle_by_copies(state, why, audio, row, by_id, stored, on_drive)
        audio_id = audio["item_id"]
        rec = manifest.get(audio_id, {})
        audio_path = audio.get("audio_path", "")
        on_disk, size_differs = disk_state(paths.root / audio_path if audio_path else None, audio.get("audio_bytes", ""))
        seen, parts = on_drive.get(audio_id, (0, 0))
        in_store = audio_id in stored
        drive = drive_state(seen, parts)
        rows.append({
            "item_id": row["item_id"], "person_id": row.get("person_id", ""), "lane": row.get("lane", ""),
            "relation": row.get("relation", ""), "twin_of": row.get("twin_of", ""), "kinds": kinds,
            "state": state, "why": why, "audio_item": audio_id,
            "error_class": (rec.get("error_class") or "") if state == "failed" else "",
            "fetchable_here": (state in ("no_audio_not_yet", "failed") and has_own_recording(row)
                               and not held_by_policy(row)),
            "audio_path": audio_path, "on_disk": on_disk, "disk_size_differs": size_differs,
            "held": audio_id in held, "in_store": in_store, "stores": sorted(stored.get(audio_id, ())),
            "drive_parts_seen": seen, "drive_parts": parts, "drive_state": drive,
            "pull_back": state == "downloaded" and in_store and not on_disk and drive != "all",
        })
    return rows


# ---------------------------------------------------------------- counts
def blank_counts(person, kind):
    return {**{f: 0 for f in COUNT_FIELDS}, "person_id": person, "kind": kind}


def add_to(counts, item):
    counts["items_with_text"] += 1
    counts[STATE_COLUMN[item["state"]]] += 1
    if item["state"] != "downloaded":
        return
    counts["on_disk"] += item["on_disk"]
    counts["in_store" if item["in_store"] else "not_in_store"] += 1
    counts[{"all": "on_drive", "partly": "partly_on_drive", "none": "not_on_drive"}[item["drive_state"]]] += 1


def check_partition(counts):
    """Raise if one of the three sums of the docstring does not hold for this row."""
    c = counts
    classes = (c["audio_downloaded"] + c["no_audio_page"] + c["no_audio_youtube"] + c["no_audio_interview_held"]
               + c["no_audio_not_yet"] + c["download_failed"])
    if classes != c["items_with_text"]:
        raise AssertionError(f"{c['person_id']}/{c['kind']}: the six classes add to {classes}, not {c['items_with_text']}")
    if c["in_store"] + c["not_in_store"] != c["audio_downloaded"]:
        raise AssertionError(f"{c['person_id']}/{c['kind']}: in_store + not_in_store != audio_downloaded")
    if c["on_drive"] + c["partly_on_drive"] + c["not_on_drive"] != c["audio_downloaded"]:
        raise AssertionError(f"{c['person_id']}/{c['kind']}: on_drive + partly_on_drive + not_on_drive != audio_downloaded")
    if c["on_disk"] > c["audio_downloaded"]:
        raise AssertionError(f"{c['person_id']}/{c['kind']}: on_disk exceeds audio_downloaded")


def count(rows):
    """Count rows per person and kind, then a total row per kind (person_id "all"). Every row is checked."""
    table = {(TOTAL, kind): blank_counts(TOTAL, kind) for kind in KINDS}   # a total row per kind, also at zero
    for item in rows:
        for kind in item["kinds"] + ["any"]:
            for person in (item["person_id"], TOTAL):
                add_to(table.setdefault((person, kind), blank_counts(person, kind)), item)
    out = [table[k] for k in sorted(table, key=lambda k: (k[0] == TOTAL, k[0], KINDS.index(k[1])))]
    for counts in out:
        check_partition(counts)
    return out


# ---------------------------------------------------------------- gaps
def queue_fields(paths):
    sample = paths.jobs / "queue_cycle.csv"
    if sample.is_file():
        with open(sample, newline="", encoding="utf-8-sig") as handle:
            header = handle.readline().strip()
        if header:
            return tuple(h.strip() for h in header.split(","))
    return QUEUE_FIELDS


def queued_rows(paths, wanted):
    """{video_id: row} for the wanted ids from the queue files in jobs/, the newest file first; files whose
    header has no video_id are skipped, and the reading stops once every wanted id has a row."""
    out, wanted = {}, set(wanted)
    files = sorted(paths.jobs.glob("queue*.csv"), key=lambda p: p.stat().st_mtime, reverse=True) if paths.jobs.is_dir() else []
    for path in files:
        if not wanted - set(out):
            break
        with open(path, newline="", encoding="utf-8-sig") as handle:
            header = handle.readline()
        if "video_id" not in [h.strip() for h in header.split(",")]:
            continue
        for row in read_csv(path):
            if row.get("video_id") in wanted and row["video_id"] not in out:
                out[row["video_id"]] = row
    return out


def fetch_queue(rows, paths):
    """The items whose recording can be fetched here, shaped like a queue."""
    fields = queue_fields(paths)
    gaps = [r for r in rows if r["fetchable_here"]]
    catalog = {r["item_id"]: r for r in read_csv(paths.root / "catalog" / "catalog.csv")}
    known = queued_rows(paths, {r["item_id"] for r in gaps})
    out = []
    for gap in gaps:
        cat = catalog.get(gap["item_id"], {})
        built = {"video_id": gap["item_id"], "url": cat.get("source_url", ""), "channel_dir": gap["person_id"],
                 "title": cat.get("title", ""), "duration_s": cat.get("duration_s", ""), "published": cat.get("published", ""),
                 "lane": gap["lane"], "relation": gap["relation"], "feed_key": cat.get("feed_key", ""),
                 "twin_of": gap["twin_of"], "twin_method": cat.get("twin_method", ""),
                 "interview_type": cat.get("interview_type", ""), "shard": 0}
        row = {**built, **{k: v for k, v in known.get(gap["item_id"], {}).items() if v != ""}}
        out.append({f: row.get(f, "") for f in fields})
    return fields, out


def pull_back(rows):
    """The recordings to pull back, once each (a page and its twin share one recording)."""
    out = {}
    for r in rows:
        if r["pull_back"] and r["audio_item"] not in out:
            out[r["audio_item"]] = {"item_id": r["audio_item"], "person_id": r["person_id"], "drive_state": r["drive_state"],
                                    "stores": ";".join(r["stores"])}
    return list(out.values())


# ---------------------------------------------------------------- the summary
def markdown(counts, rows, gaps=None, pulls=None):
    def table(lines):
        head = ("person", "kind", "with text", "downloaded", "on disk", "in store", "on Drive", "partly", "not in store",
                "not on Drive", "no audio: page", "no audio: YouTube", "no audio: interview held", "no audio: not yet",
                "failed")
        out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
        for c in lines:
            out.append("| " + " | ".join(str(c[f]) for f in COUNT_FIELDS) + " |")
        return out
    totals = [c for c in counts if c["person_id"] == TOTAL]
    persons = [c for c in counts if c["person_id"] != TOTAL and c["kind"] == "any"]
    lines = [f"# Where the audio of every transcript is (as of {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())})", "",
             "The counts are as of the run time: the collection cycles and the sync keep running (items counted as "
             "\"not yet\" may be downloading now, and a downloaded file leaves the disk once a store holds it), so the "
             "numbers move between runs.", "",
             "An item with a transcript is counted once under each kind it has (made = speech-to-text made here, "
             "source = the publisher's text, captions = a caption track; any = once per item). Per kind, every item "
             "is in exactly one class: downloaded, no audio because it is a page, no audio because the recording is a "
             "YouTube video (only the owner's computer can fetch it), no audio because it is an interview-show episode "
             "that is not live channeling (held by policy), no audio because the recording of a fetchable lane is not "
             "downloaded yet, or a failed download. Within downloaded: in store or not; on Drive with all parts, "
             "partly, or not. On disk is a fact beside the partition.", "",
             "## Totals per kind", ""] + table(totals) + ["", "## Per person (kind: any)", ""] + table(persons)
    failed = collections.Counter(r["error_class"] or "unknown" for r in rows if r["state"] == "failed")
    if failed:
        lines += ["", "## Failed downloads by error class", ""] + [f"- {k}: {v}" for k, v in failed.most_common()]
    if gaps is not None:
        fetchable = collections.Counter(r["lane"] for r in rows if r["fetchable_here"])
        lines += ["", "## Gaps", "",
                  f"- {len(gaps)} item(s) with a transcript whose recording can be fetched here "
                  f"({', '.join(f'{k}: {v}' for k, v in sorted(fetchable.items())) or 'none'}): transcript_audio_fetch.csv",
                  f"- {len(pulls or [])} item(s) in the store but not on disk and not fully on Drive, to be pulled back "
                  "for the Drive copy: transcript_audio_pull.csv",
                  f"- {sum(1 for r in rows if r['state'] == 'downloaded' and not r['in_store'])} downloaded item(s) not "
                  "in the store",
                  f"- {sum(1 for r in rows if r['state'] == 'no_audio_interview_held')} interview episode(s) that are not "
                  f"live channeling, left out of the queue (held by policy; "
                  f"{sum(1 for r in rows if r['state'] == 'no_audio_interview_held' and 'not classified' in r['why'])} "
                  "of them not classified yet)",
                  f"- {sum(1 for r in rows if r['audio_item'] != r['item_id'])} page(s) whose audio state is their "
                  "twin's"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--publish-counts", action="store_true", help="also copy the counts to plan/transcript_audio.csv")
    ap.add_argument("--gaps", action="store_true", help="also write the fetch queue and the pull-back list")
    ap.add_argument("--plan-dir", type=Path, default=ET_ROOT / "plan", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    if only and args.publish_counts:
        ap.error("--publish-counts cannot go with --only: the public counts cover every person")
    paths = layout(ensure_outside_git(args.root))
    out = paths.root / OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    rows = build_rows(paths, only)
    counts = count(rows)
    with open(out / "transcript_audio.jsonl", "w", encoding="utf-8") as handle:
        for r in rows:
            handle.write(json.dumps(r, ensure_ascii=False) + "\n")
    write_csv(out / "transcript_audio_counts.csv", counts, COUNT_FIELDS)
    gaps = pulls = None
    if args.gaps:
        fields, gaps = fetch_queue(rows, paths)
        write_csv(out / "transcript_audio_fetch.csv", gaps, fields)
        pulls = pull_back(rows)
        write_csv(out / "transcript_audio_pull.csv", pulls, ("item_id", "person_id", "drive_state", "stores"))
    (out / "transcript_audio.md").write_text(markdown(counts, rows, gaps, pulls), encoding="utf-8")
    if args.publish_counts:
        args.plan_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out / "transcript_audio_counts.csv", args.plan_dir / "transcript_audio.csv")

    for c in counts:
        if c["person_id"] == TOTAL:
            print(f"{c['kind']:8s} with text {c['items_with_text']:6d} | downloaded {c['audio_downloaded']:5d} "
                  f"(on disk {c['on_disk']}, in store {c['in_store']}, on Drive {c['on_drive']}, partly {c['partly_on_drive']}) "
                  f"| no audio: page {c['no_audio_page']}, YouTube {c['no_audio_youtube']}, interview held "
                  f"{c['no_audio_interview_held']}, not yet {c['no_audio_not_yet']} | failed {c['download_failed']}")
    if args.gaps:
        print(f"gaps: {len(gaps)} fetchable here -> {out / 'transcript_audio_fetch.csv'}; "
              f"{len(pulls)} to pull back for Drive -> {out / 'transcript_audio_pull.csv'}")
    print(f"per item -> {out / 'transcript_audio.jsonl'}; summary -> {out / 'transcript_audio.md'}"
          + (f"; counts -> {args.plan_dir / 'transcript_audio.csv'}" if args.publish_counts else ""))


if __name__ == "__main__":
    main()
