"""Read evidence for upload dates from the private metadata catalog of a completed selection."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
from zipfile import ZipFile

if __package__:
    from . import episode_comparison, episode_periods
else:
    import episode_comparison
    import episode_periods


def _records(archive, name):
    with archive.open("catalog/" + name + ".jsonl") as stream:
        for line in stream:
            yield json.loads(line)


def _day(value):
    if value is None:
        return None
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("Expected an exact ISO calendar day in the metadata catalog")
    return value


def read_catalog(path, catalog_sha256, rows, selection_sha256):
    """Require an exact roster and bind each reported upload day to that video's observations."""
    if not episode_comparison.digest(catalog_sha256):
        raise ValueError("Supply the SHA-256 from the final metadata catalog receipt")
    frame = {row["video_id"]: row for row in rows}
    creators = {row["channel_dir"] for row in frame.values()}
    days, counts = {}, Counter()
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
        if digest.hexdigest() != catalog_sha256:
            raise ValueError("The metadata catalog differs from its receipt")
        stream.seek(0)
        with ZipFile(stream) as archive:
            if len(archive.namelist()) != len(set(archive.namelist())):
                raise ValueError("Duplicate metadata catalog member")
            summary = json.loads(archive.read("summary.json"))
            portable = "current_selection_sha256" in summary
            if portable:
                selections = summary.get("selections") or [{}]
                final = selections[-1]
                matches = (summary.get("state") == "verified_current_cohort"
                           and summary["current_selection_sha256"] == final.get("selection_sha256") == selection_sha256
                           and final.get("listing_complete") is True and final.get("creators") == len(creators)
                           and summary.get("current_recordings") == len(frame))
            else:
                matches = (summary.get("scope") == "closed_full_cohort" and summary.get("selection_sha256") == selection_sha256
                           and summary.get("recordings") == len(frame) and summary.get("creators") == len(creators))
            if not matches:
                raise ValueError("Upload dates require a final catalog for the same completed selection")
            listings, historical = {}, set()
            for listing in _records(archive, "listings"):
                video = listing["video_id"]
                if video in listings or video in historical:
                    raise ValueError("Duplicate catalog listing")
                if portable and listing.get("in_current_selection") is False and video not in frame:
                    historical.add(video)
                    continue
                row = frame.get(video)
                if (not row or portable and listing.get("in_current_selection") is not True
                        or listing["channel_dir"] != row["channel_dir"] or listing["channel_id"] != row["expected_channel_id"]
                        or listing["media_type"] != row["tab"]):
                    raise ValueError("A catalog listing differs from the selected channel and recording")
                listings[video] = listing
            if listings.keys() != frame.keys():
                raise ValueError("The final metadata catalog omits selected recordings")
            projected = {}
            for item in _records(archive, "public-metadata-snapshots"):
                key = item["projection_sha256"]
                if key in projected or not episode_comparison.digest(key):
                    raise ValueError("Invalid or duplicate metadata projection")
                projected[key] = _day(item["metadata"].get("upload_date"))
            observed = defaultdict(dict)
            for item in _records(archive, "source-observations"):
                video, source = item["video_id"], item["input_sha256"]
                if video in historical:
                    continue
                projection = item["projection_sha256"]
                if (video not in frame or source in observed[video] or not episode_comparison.digest(source)
                        or projection not in projected):
                    raise ValueError("An upload observation lost its recording or source identity")
                observed[video][source] = projected[projection]
            for video, listing in listings.items():
                row = frame[video]
                evidence = defaultdict(list)
                for source, day in observed[video].items():
                    if day is not None:
                        evidence[day].append(source)
                if {day: sorted(keys) for day, keys in evidence.items()} != listing["observed_upload_day_evidence"]:
                    raise ValueError("The reported dates differ from the underlying metadata observations")
                day = next(iter(evidence)) if len(evidence) == 1 else None
                if listing["single_observed_upload_day"] != day:
                    raise ValueError("Inconsistent single upload day")
                days[video] = day
                if day is None:
                    counts["conflicting_observed_upload_days" if evidence else "missing_upload_day"] += 1
                elif episode_periods.publication_quarter(row) is None:
                    counts["upload_day_only"] += 1
                elif day == row["selected_publication_date"]:
                    counts["same_upload_and_publication_day"] += 1
                elif episode_periods.quarter_for_day(day) == episode_periods.publication_quarter(row):
                    counts["different_days_within_same_quarter"] += 1
                else:
                    counts["different_upload_and_publication_quarters"] += 1
    return days, dict(sorted(counts.items()))
