#!/usr/bin/env python3
"""Channel inventory and size estimates from the committed index. No network.

Reads   youtube-index/youtube_index.json                      (observed 2026-10-23)
Writes  plan/channel_inventory.csv   one row per tracked person or group
        plan/estimates.json          totals, assumptions and the arithmetic behind them
With --update-readme it also rewrites the block between
<!-- inventory:start --> and <!-- inventory:end --> in README.md, so the README table is
always generated from the data, never typed by hand.

    python3 et-channelers/pipeline/inventory.py --update-readme
    python3 et-channelers/pipeline/inventory.py --refresh-bashar75   # needs ../data/videos.json
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ET_ROOT, atomic_write_text, parse_duration, write_csv  # noqa: E402

INDEX = ET_ROOT / "youtube-index" / "youtube_index.json"
PLAN = ET_ROOT / "plan"
README = ET_ROOT / "README.md"
BASHAR75 = PLAN / "bashar75_estimate.json"
START, END = "<!-- inventory:start -->", "<!-- inventory:end -->"
WORDS_PER_MINUTE = 140  # assumption for spoken English, used only for the Bashar-75 estimate
STATUS_ORDER = {"ok": 0, "metadata-only": 1, "not_found": 2, "no_youtube": 3}
FIELDS = ["rank", "person_id", "person_name", "role", "status", "channel_title", "handle",
          "channel_url", "subscribers", "total_videos", "videos_in_index", "crawled",
          "sample_mean_min", "est_basis", "est_hours", "next_action"]
NEXT_ACTION = {
    "metadata-only": "read the channel video list",
    "not_found": "search again or confirm there is no channel",
    "no_youtube": "search for a channel (the search never ran)",
}


def sample_minutes(entry):
    if entry["status"] != "ok":
        return []
    secs = (parse_duration(v.get("length_text")) for v in entry.get("videos") or [])
    return [s / 60 for s in secs if s]


def build():
    channels = json.loads(INDEX.read_text(encoding="utf-8"))["channels"]
    samples = {c["person"]: sample_minutes(c) for c in channels}
    pooled = [m for mins in samples.values() for m in mins]
    chan_means = [st.mean(m) for m in samples.values() if len(m) >= 10]
    q1, med, q3 = st.quantiles(chan_means, n=4)[0], st.median(chan_means), st.quantiles(chan_means, n=4)[2]
    pooled_mean = st.mean(pooled)

    rows = []
    for c in channels:
        ch = c.get("channel") or {}
        total = c.get("video_count") if isinstance(c.get("video_count"), int) else None
        mins = samples[c["person"]]
        if total is not None and len(mins) >= 10:
            mean_min, basis = st.mean(mins), "channel sample"
        elif total is not None:
            mean_min, basis = pooled_mean, "pooled mean"
        else:
            mean_min, basis = None, ""
        action = NEXT_ACTION.get(c["status"], "")
        if c["status"] == "ok":
            action = "list the remaining videos" if (total or 0) > len(c.get("videos") or []) else "none"
        rows.append({
            "rank": "", "person_id": c["person"], "person_name": c["person_name"],
            "role": c.get("role", ""), "status": c["status"],
            "channel_title": ch.get("title", ""), "handle": ch.get("handle", ""),
            "channel_url": ch.get("url", ""), "subscribers": c.get("subscribers") or "",
            "total_videos": total if total is not None else "",
            "videos_in_index": len(c.get("videos") or []),
            "crawled": "yes" if c["status"] == "ok" else "no",
            "sample_mean_min": round(st.mean(mins), 1) if len(mins) >= 10 else "",
            "est_basis": basis,
            "est_hours": round(total * mean_min / 60) if total is not None else "",
            "next_action": action,
        })
    known = sorted((r for r in rows if r["total_videos"] != ""), key=lambda r: (-r["total_videos"], r["person_name"]))
    unknown = sorted((r for r in rows if r["total_videos"] == ""),
                     key=lambda r: (STATUS_ORDER[r["status"]], r["person_name"].lower()))
    for n, row in enumerate(known, 1):
        row["rank"] = n
    rows = known + unknown

    total_known = sum(r["total_videos"] for r in known)
    hours = sum(r["est_hours"] for r in known)
    by_status = {}
    for r in known:
        by_status[r["status"]] = by_status.get(r["status"], 0) + r["total_videos"]
    est = {
        "source": "youtube-index/youtube_index.json, observed 2026-10-23",
        "entries": len(rows),
        "entries_with_total": len(known),
        "entries_without_total": len(unknown),
        "total_videos_known": total_known,
        "videos_by_status": dict(sorted(by_status.items())),
        "channels_over_1000_videos": sum(r["total_videos"] > 1000 for r in known),
        "median_videos_per_channel": st.median(r["total_videos"] for r in known),
        "sample": {
            "crawled_channels_with_10plus_durations": len(chan_means),
            "videos_with_duration": len(pooled),
            "pooled_mean_min": round(pooled_mean, 1),
            "pooled_median_min": round(st.median(pooled), 1),
            "share_under_5_min": round(sum(m < 5 for m in pooled) / len(pooled), 3),
            "share_over_60_min": round(sum(m > 60 for m in pooled) / len(pooled), 3),
            "channel_mean_min_q1": round(q1, 1),
            "channel_mean_min_median": round(med, 1),
            "channel_mean_min_q3": round(q3, 1),
        },
        "hours": {
            "central": round(hours),
            "low": round(total_known * q1 / 60),
            "high": round(total_known * q3 / 60),
            "method": "central = sum over channels of total videos x that channel's mean length "
                      "(its own sample if 10+ videos were read, else the pooled mean); "
                      "low/high = total videos x the first/third quartile of channel mean lengths",
        },
        "caveats": [
            f"Lengths were read only for the most recent uploads of the {sum(c['status'] == 'ok' for c in channels)} crawled channels ({len(pooled)} videos), so means lean towards recent uploads.",
            f"{len(unknown)} entries have no video count and are not in any total.",
            "Shorts and clips pull the mean down; full sessions pull it up.",
        ],
    }
    gb = lambda kbps: round(est["hours"]["central"] * 3600 * kbps * 1000 / 8 / 1e9)  # noqa: E731
    est["storage_gb_central"] = {"opus_mono_24kbps": gb(24), "opus_mono_32kbps": gb(32)}
    est["asr_gpu_hours_central_if_speedup"] = {
        f"{x}x": round(est["hours"]["central"] / x) for x in (15, 30, 60, 120)}
    return rows, est


def bashar75():
    if BASHAR75.exists():
        return json.loads(BASHAR75.read_text(encoding="utf-8"))
    return None


def refresh_bashar75():
    src = ET_ROOT.parent / "data" / "videos.json"
    vids = json.loads(src.read_text(encoding="utf-8"))
    words = sum(int(v.get("approx_word_count") or 0) for v in vids)
    out = {"videos": len(vids), "approx_words": words, "words_per_minute_assumed": WORDS_PER_MINUTE,
           "est_hours": round(words / WORDS_PER_MINUTE / 60, 1),
           "method": "sum of approx_word_count in data/videos.json divided by an assumed 140 words per minute"}
    atomic_write_text(BASHAR75, json.dumps(out, indent=2) + "\n")
    return out


def esc(text):
    return str(text).replace("|", "\\|")


def table_row(r):
    handle = f"[{esc(r['handle'])}]({r['channel_url']})" if r["handle"] and r["channel_url"] else "none on record"
    subs = f"{int(r['subscribers']):,}" if r["subscribers"] != "" else "?"
    total = f"{r['total_videos']:,}" if r["total_videos"] != "" else "?"
    hrs = f"{r['est_hours']:,}" if r["est_hours"] != "" else "?"
    return (f"| {r['rank'] or ''} | {esc(r['person_name'])} | {handle} | {r['status']} | {subs} | {total} "
            f"| {r['videos_in_index']} | {hrs} |")


HEAD = ("| # | Person or group | Channel | Index status | Subscribers | Videos on channel | In index | Est. hours |\n"
        "|--:|---|---|---|--:|--:|--:|--:|")


def render_block(rows, est):
    s, h, b = est["sample"], est["hours"], bashar75()
    s_ = s
    lines = [
        START,
        f"**Totals.** {est['entries_with_total']} of {est['entries']} entries have a channel video count on record; "
        f"together they hold **{est['total_videos_known']:,} videos** ({est['channels_over_1000_videos']} channels have more "
        f"than 1,000; the median channel has {est['median_videos_per_channel']:,}). The other {est['entries_without_total']} "
        "entries have no count yet, so every total below is a floor.",
        "",
        f"**Rough size.** The {s['videos_with_duration']} videos actually measured average {s['pooled_mean_min']} minutes "
        f"(median {s['pooled_median_min']}; {s['share_under_5_min']:.0%} are under 5 minutes, {s['share_over_60_min']:.0%} over an hour). "
        f"That puts the known total at about **{h['central']:,} hours of audio** (plausible range {h['low']:,} to {h['high']:,}). "
        f"Stored as mono 24 kbps Opus that is roughly {est['storage_gb_central']['opus_mono_24kbps']} GB "
        f"({est['storage_gb_central']['opus_mono_32kbps']} GB at 32 kbps). Transcription time depends on the speed-up measured in the "
        "pilot: " + ", ".join(f"{k} real time = {v:,} GPU-hours" for k, v in est["asr_gpu_hours_central_if_speedup"].items()) + ". "
        "These are planning figures, not measurements; "
        "[`plan/estimates.json`](plan/estimates.json) shows the arithmetic and caveats.",
    ]
    if b:
        lines += ["", f"**Bashar pilot set.** The {b['videos']} recordings already digested in this repository hold about "
                      f"{b['approx_words']:,} words, roughly {b['est_hours']} hours at {b['words_per_minute_assumed']} words per minute."]
    lines += ["", "Largest channels (full list below):", "", HEAD]
    lines += [table_row(r) for r in rows[:15]]
    lines += ["", f"<details><summary>All {len(rows)} entries, largest first, then the ones with no count</summary>", "", HEAD]
    lines += [table_row(r) for r in rows]
    lines += ["", "</details>", "",
              "The same table as CSV: [`plan/channel_inventory.csv`](plan/channel_inventory.csv). "
              "`Index status` is the rule from Stage 4. `In index` counts the video rows in `youtube_index.json` "
              "(30 recent uploads for crawled channels; only the ones the notes named for the rest). "
              f"`Est. hours` is the video count times the channel's own mean length where 10 or more lengths were read, "
              f"otherwise times the pooled mean ({s_['pooled_mean_min']} minutes).", END]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update-readme", action="store_true")
    ap.add_argument("--refresh-bashar75", action="store_true")
    args = ap.parse_args()
    if args.refresh_bashar75:
        print(json.dumps(refresh_bashar75()))
    rows, est = build()
    write_csv(PLAN / "channel_inventory.csv", rows, FIELDS)
    atomic_write_text(PLAN / "estimates.json", json.dumps(est, indent=2) + "\n")
    print(f"{est['entries']} entries, {est['entries_with_total']} with a total, "
          f"{est['total_videos_known']:,} videos, ~{est['hours']['central']:,} h")
    if args.update_readme:
        text = README.read_text(encoding="utf-8")
        if START not in text or END not in text:
            sys.exit("README.md has no inventory markers")
        head, rest = text.split(START, 1)
        tail = rest.split(END, 1)[1]
        atomic_write_text(README, head + render_block(rows, est) + tail)
        print("README inventory block updated")


if __name__ == "__main__":
    main()
