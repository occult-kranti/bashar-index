"""Build a private discovery list for newest-N collection across YouTube tabs.

Read a merged catalog and the frozen selection. Each channel's Videos, Shorts
and Streams tab has its own ordering. Keep every ID tied at a tab's cutoff.
The output schedules metadata lookups. It does not certify cross-tab chronology.
"""

import argparse
import collections
import csv
from datetime import date
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ID_RE, ensure_outside_git, read_jsonl, write_csv
from dataset_timeline import exact_dates


TABS = ("videos", "shorts", "streams")
OUTPUT_FIELDS = (
    "channel_dir", "video_id", "tab", "listing_rank", "title", "duration_s",
    "upload_date_approx", "youtube_upload_date", "upload_date_metadata_sha256",
    "recorded_publication_date", "date_evidence",
    "in_frozen_selection", "at_tab_cutoff_tie", "needs_stream_completion_check",
)


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def select_candidates(catalog, selected, per_tab):
    """Use distinct IDs within each tab and include ties without a date guess."""
    if per_tab < 1:
        raise ValueError("per_tab must be positive")
    frozen = {(row["channel_dir"], row["video_id"]) for row in selected}
    channels = {channel for channel, _ in frozen}
    groups = collections.defaultdict(dict)
    for item in catalog:
        channel, tab, video = item["channel_dir"], item["tab"], item["video_id"]
        if channel not in channels or tab not in TABS:
            continue
        value = item.get("listing_rank")
        if value is None or value == "":
            continue
        rank = str(value).strip()
        if not ID_RE.fullmatch(video) or not rank.isascii() or not rank.isdecimal():
            raise ValueError(f"Invalid listing ID or rank for {channel}/{tab}: {video}")
        rank = int(rank)
        entries = groups[channel, tab]
        previous = entries.get(video)
        if previous is None or rank < previous[0]:
            entries[video] = (rank, item)

    result = []
    for (channel, tab), entries in sorted(groups.items()):
        ordered = sorted(entries.values(), key=lambda pair: (pair[0], pair[1]["video_id"]))
        # Merged snapshots can contain two distinct IDs at one rank. One such
        # collision must not displace an item recorded in the original top N.
        cutoff = max(per_tab - 1, ordered[min(per_tab, len(ordered)) - 1][0])
        cutoff_tie = len(ordered) > per_tab and sum(rank == cutoff for rank, _ in ordered) > 1
        for rank, item in ordered:
            if rank > cutoff:
                break
            video = item["video_id"]
            result.append({
                "channel_dir": channel, "tab": tab, "video_id": video, "listing_rank": rank,
                "title": item.get("title", ""), "duration_s": item.get("duration_s", ""),
                "upload_date_approx": item.get("upload_date_approx", ""),
                "in_frozen_selection": (channel, video) in frozen,
                "at_tab_cutoff_tie": cutoff_tie and rank == cutoff,
                "needs_stream_completion_check": tab == "streams",
            })
    return result


def add_recorded_dates(candidates, receipts):
    """Use source-derived dates only for the same channel and video."""
    keys = {(r["channel_dir"], r["video_id"]) for r in candidates}
    dates = collections.defaultdict(set)
    for receipt in receipts:
        key = (receipt.get("channel_dir"), receipt.get("video_id"))
        published = receipt.get("published")
        if key not in keys or not isinstance(published, str):
            continue
        try:
            day = date.fromisoformat(published)
        except ValueError:
            continue
        if day.isoformat() == published:
            dates[key].add(published)
    for item in candidates:
        values = dates[item["channel_dir"], item["video_id"]]
        item["recorded_publication_date"] = ""
        if len(values) == 1:
            item["recorded_publication_date"] = next(iter(values))
            item["date_evidence"] = "extractor release_date or upload_date recorded by Drive ingest"
        elif values:
            item["date_evidence"] = "conflicting recorded dates"
        else:
            item["date_evidence"] = "unresolved"


def add_upload_dates(candidates, overlay):
    """Match globally unique YouTube IDs to validated, saved metadata."""
    # A shared overlay may cover creators or older uploads outside this run.
    known = exact_dates(overlay)
    for item in candidates:
        evidence = known.get(item["video_id"])
        item["youtube_upload_date"] = evidence["upload_date"] if evidence else ""
        item["upload_date_metadata_sha256"] = evidence["provenance"]["source_sha256"] if evidence else ""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True, help="merged listing CSV")
    parser.add_argument("--selected", type=Path, required=True, help="frozen queue selecting the channels")
    parser.add_argument("--ingest-receipts", type=Path, help="existing drive_ingest_manifest.jsonl")
    parser.add_argument("--exact-dates", type=Path, help="existing saved-YouTube-metadata date overlay")
    parser.add_argument("--per-tab", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True, help="private output CSV")
    args = parser.parse_args(argv)
    if args.per_tab < 1:
        parser.error("--per-tab must be positive")
    ensure_outside_git(args.out.parent)
    inputs = (args.catalog, args.selected, args.ingest_receipts, args.exact_dates)
    if args.out.resolve() in {p.resolve() for p in inputs if p}:
        parser.error("The output path overlaps an input")
    selected = list(rows(args.selected))
    candidates = select_candidates(rows(args.catalog), selected, args.per_tab)
    if args.ingest_receipts and not args.ingest_receipts.is_file():
        parser.error("The requested ingest receipts file is missing")
    add_recorded_dates(candidates, read_jsonl(args.ingest_receipts) if args.ingest_receipts else ())
    add_upload_dates(candidates, json.loads(args.exact_dates.read_bytes()) if args.exact_dates else None)
    write_csv(args.out, candidates, OUTPUT_FIELDS)
    ids = {row["video_id"] for row in candidates}
    print(json.dumps({
        "tracked_channels": len({row["channel_dir"] for row in selected}),
        "candidate_rows": len(candidates), "distinct_ids": len(ids),
        "per_tab": dict(collections.Counter(row["tab"] for row in candidates)),
        "ids_outside_frozen_queue": len(ids - {row["video_id"] for row in selected}),
        "ids_with_recorded_dates": len({r["video_id"] for r in candidates if r["recorded_publication_date"]}),
        "ids_with_exact_upload_dates": len({r["video_id"] for r in candidates if r["youtube_upload_date"]}),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
