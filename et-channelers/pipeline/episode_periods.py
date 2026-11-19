"""Compare topic presence by publication quarter using a frozen, dated selection."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import fmean

try:
    from . import episode_comparison
except ImportError:
    import episode_comparison


def publication_quarter(row):
    """Keep unproved, approximate and missing dates together for coverage reporting."""
    value = row.get("selected_publication_date")
    if (row.get("selected_date_quality") != "exact" or not isinstance(value, str)
            or not episode_comparison.digest(row.get("selected_date_source_sha256"))):
        return None
    try:
        day = date.fromisoformat(value)
    except ValueError:
        return None
    if day.isoformat() != value:
        return None
    return day.year * 4 + (day.month - 1) // 3


def period_name(quarter):
    return "undated" if quarter is None else f"{quarter // 4:04d}-Q{quarter % 4 + 1}"


def summarize(rows, evidence, topics):
    """Give creators equal weight and compare adjacent quarters using shared creators."""
    rows = list(rows)
    topics = sorted(topics)
    frame = episode_comparison.primary_frame(rows)
    selected = defaultdict(lambda: defaultdict(list))
    for row in rows:
        selected[publication_quarter(row)][row["channel_dir"]].append(row["video_id"])
    observations = {}
    for proof in evidence:
        video = proof["video_id"]
        if video in observations or video not in frame or frame[video]["creator"] != proof["channel_dir"]:
            raise ValueError("Publication-period evidence must identify one selected episode and creator")
        observations[video] = (set(proof["assessed_topics"]), {match["topic"] for match in proof["matches"]}, proof)

    dated = sorted(q for q in selected if q is not None)
    quarters = dated + ([None] if None in selected else [])
    series, comparisons, by_creator = [], [], {}
    for quarter in quarters:
        for topic in topics:
            cells = {}
            for creator, videos in sorted(selected[quarter].items()):
                cells[creator] = episode_comparison.measure(frame, videos, observations, {topic})
            by_creator[quarter, topic] = cells
            assessed = {c: cell for c, cell in cells.items() if cell["assessed_episodes"]}
            eligible_episodes = sum(x["eligible_episodes"] for x in cells.values())
            assessed_episodes = sum(x["assessed_episodes"] for x in assessed.values())
            positives = sum(x["positive_episodes"] for x in assessed.values())
            series.append({
                "publication_quarter": period_name(quarter), "topic": topic,
                "eligible_episodes": eligible_episodes, "assessed_episodes": assessed_episodes,
                "positive_episodes": positives, "eligible_creators": len(cells), "assessed_creators": len(assessed),
                "episode_share": positives / assessed_episodes if assessed_episodes else None,
                "creator_balanced_share": (fmean(x["family_balanced_observed_share"] for x in assessed.values())
                                           if assessed else None),
                "creator_balanced_frame_lower": fmean(x["family_balanced_frame_bounds"][0] for x in cells.values()),
                "creator_balanced_frame_upper": fmean(x["family_balanced_frame_bounds"][1] for x in cells.values())
            })
            previous = by_creator.get((quarter - 1, topic)) if quarter is not None else None
            if previous is None:
                continue
            shared = sorted(c for c in assessed if c in previous and previous[c]["assessed_episodes"])
            changes = [assessed[c]["family_balanced_observed_share"] - previous[c]["family_balanced_observed_share"]
                       for c in shared]
            comparisons.append({
                "previous_quarter": period_name(quarter - 1), "publication_quarter": period_name(quarter),
                "topic": topic, "matched_creators": len(shared),
                "previous_assessed_episodes": sum(previous[c]["assessed_episodes"] for c in shared),
                "current_assessed_episodes": sum(assessed[c]["assessed_episodes"] for c in shared),
                "mean_within_creator_change_percentage_points": 100 * fmean(changes) if changes else None,
                "matched_channel_dirs": shared
            })
    return {"schema_version": 1, "date_basis": "pinned_publication_day",
            "eligible_episodes": len(frame),
            "episodes_with_exact_publication_dates": sum(len(ids) for q in dated for ids in selected[q].values()),
            "undated_episodes": sum(len(ids) for ids in selected.get(None, {}).values()),
            "quarters": [period_name(q) for q in dated], "series": series, "matched_quarter_changes": comparisons}
