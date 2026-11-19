"""Select the latest available recording candidates from locally cached uploads pages.

The fetch command in collect_uploads_catalog produces one frames.json per
creator. This command joins source-tab labels and optional watch-page liveness
observations without fetching media.

    python pipeline/recording_selection.py --channels channels.csv --frames /private/uploads \
        --catalog /private/jobs/queue_youtube_all_merged.csv --out /private/latest20.json

Use --limit 50 on a sufficiently deep saved prefix to select the second round.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

from collect_uploads_catalog import manifest
from common import ID_RE, atomic_write_text, ensure_outside_git
from uploads_playlist import CHANNEL_ID, canonical_playlist_id, uploads_url


TABS = {"videos", "shorts", "streams"}
LIVE_BADGES = {"live", "live now", "upcoming", "premiere", "premiering now"}


def scheduled_or_live(item, watch=None):
    if watch and (watch.get("is_upcoming") is True or watch.get("is_live") is True
                  or watch.get("live_now") is True or watch.get("live_status") in {"is_upcoming", "is_live"}):
        return True
    badges = {str(value).strip().casefold() for value in item.get("duration_or_badges_as_shown", [])}
    labels = [value.casefold() for group in item.get("display_metadata", [])
              for value in group if isinstance(value, str)]
    return bool(badges & LIVE_BADGES) or any(
        value.startswith("scheduled for ") or value.endswith(" watching now") for value in labels
    )


def load_catalogs(files):
    evidence = defaultdict(set)
    for filename in files:
        with filename.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not {"channel_dir", "video_id", "tab"} <= set(reader.fieldnames or []):
                raise ValueError(f"Missing channel_dir, video_id or tab in {filename.name}")
            for row in reader:
                if row["tab"] in TABS and ID_RE.fullmatch(row["video_id"]):
                    evidence[(row["channel_dir"], row["video_id"])].add(row["tab"])
    return evidence


def current_tab_evidence(folder, creator, channel):
    found = defaultdict(set)
    if folder is None:
        return found
    for tab in sorted(TABS):
        file = folder / creator / (tab + ".json")
        if not file.is_file():
            continue
        result = json.loads(file.read_bytes())
        if (result.get("expected_channel_id") != channel or result.get("creator") != creator
                or result.get("tab") != tab):
            raise ValueError(f"Tab evidence belongs to a different channel or tab in {file}")
        if result.get("state") != "primary_grid_observed":
            continue
        for video, position in result["membership"].items():
            if not ID_RE.fullmatch(video) or type(position) is not int or position < 0:
                raise ValueError(f"Invalid video identity or position in {file}")
            found[video].add(tab)
    return found


def load_watch_status(files):
    status = {}
    for filename in files:
        saved = json.loads(filename.read_bytes())
        rows = saved if isinstance(saved, list) else [saved]
        for row in rows:
            channel, video = row.get("channel_id"), row.get("video_id")
            if (not isinstance(channel, str) or not CHANNEL_ID.fullmatch(channel)
                    or not isinstance(video, str) or not ID_RE.fullmatch(video)):
                raise ValueError(f"Watch status is missing a bound video and channel ID in {filename.name}")
            key = (channel, video)
            if key in status and scheduled_or_live({}, status[key]) != scheduled_or_live({}, row):
                raise ValueError(f"Conflicting watch observations for {video}. Select the current source snapshot.")
            status[key] = row
    return status


def select_channel(creator, channel, frames, limit, historical_tabs, current_tabs, watch_status):
    if limit < 1:
        raise ValueError("Requested count must be positive")
    requested_playlist = canonical_playlist_id(uploads_url(channel))
    if (frames.get("channel_id", channel) != channel
            or canonical_playlist_id(frames.get("canonical_url")) != requested_playlist):
        raise ValueError(f"Saved frame identity differs from the manifest for {creator}")
    available = {}
    for item in frames["items"]:
        pos = item.get("position_zero_based")
        if type(pos) is not int or pos < 0 or pos in available:
            raise ValueError(f"Invalid or duplicated playlist position for {creator}")
        available[pos] = item
    unresolved = set(frames["unresolved_positions"])
    entries, excluded = [], []
    seen = set()
    position = 0
    while position in available and position not in unresolved and len(entries) < limit:
        item = available[position]
        video = item["video_id"]
        if (item["byline_channel_id"] != channel or item["watch_playlist_id"] != requested_playlist
                or not ID_RE.fullmatch(video)):
            raise ValueError(f"Unbound source row in {creator} at position {position}")
        if video not in seen:
            seen.add(video)
            state = watch_status.get((channel, video))
            if scheduled_or_live(item, state):
                excluded.append({"video_id": video, "source_position": position, "reason": "upcoming_or_live"})
            else:
                typed = current_tabs.get(video) or historical_tabs.get((creator, video), set())
                entries.append({"video_id": video, "channel_dir": creator, "channel_id": channel,
                                "slot": len(entries) + 1, "source_position": position,
                                "title": item.get("title"), "tab": next(iter(typed)) if len(typed) == 1 else "unknown",
                                "observed_tabs": sorted(typed), "additional_byline_channel_ids": item.get("additional_byline_channel_ids", []),
                                "display_metadata": item.get("display_metadata", []),
                                "duration_or_badges_as_shown": item.get("duration_or_badges_as_shown", [])})
        position += 1
    if len(entries) == limit:
        scope = "all_requested_positions_observed"
    elif (frames.get("complete_http") and frames.get("primary_array_closed") and not frames.get("continuation_visible")
          and not unresolved and position == len(available)):
        scope = "short_complete_displayed_list"
    else:
        scope = "incomplete_visible_positions"
    return {"channel_dir": creator, "channel_id": channel, "scope": scope,
            "selected": len(entries), "excluded": excluded, "items": entries}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--channels", required=True, type=Path)
    parser.add_argument("--frames", required=True, type=Path)
    parser.add_argument("--catalog", type=Path, action="append", default=[])
    parser.add_argument("--tab-evidence", type=Path, help="private folder containing creator/{videos,shorts,streams}.json observations")
    parser.add_argument("--watch-status", type=Path, action="append", default=[])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.limit <= 0:
        parser.error("--limit must be positive")
    historical = load_catalogs(args.catalog)
    watch = load_watch_status(args.watch_status)
    results = []
    for creator, channel in manifest(args.channels):
        filename = args.frames / creator / "frames.json"
        if not filename.is_file():
            results.append({"channel_dir": creator, "channel_id": channel, "scope": "unobserved", "selected": 0,
                            "excluded": [], "items": []})
            continue
        frames = json.loads(filename.read_bytes())
        current = current_tab_evidence(args.tab_evidence, creator, channel)
        results.append(select_channel(creator, channel, frames, args.limit, historical, current, watch))
    summary = {"channels": len(results), "selected": sum(row["selected"] for row in results),
               "formats": dict(Counter(item["tab"] for row in results for item in row["items"])),
               "coverage": dict(Counter(row["scope"] for row in results))}
    dest = ensure_outside_git(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(dest, json.dumps({"schema_version": 1, "per_channel": args.limit,
                                        "summary": summary, "channels": results}, ensure_ascii=False) + "\n")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
