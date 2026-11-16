#!/usr/bin/env python3
"""Build the public, standalone historical YouTube index from its four public CSVs.

This does not read private manifests, contacts, recordings, or transcripts. The
source observation dates remain visible; building the page does not refresh them.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parents[1] / "dashboard"
SOURCES = ("channels", "videos", "entities", "playlists")


def build(directory=DIRECTORY):
    directory = Path(directory)
    payload = {"sources": {}, "tables": {}}
    for name in SOURCES:
        raw = (directory / "data" / f"{name}.csv").read_bytes()
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        payload["tables"][name] = rows
        payload["sources"][name] = {"file": f"data/{name}.csv", "rows": len(rows),
                                    "sha256": hashlib.sha256(raw).hexdigest()}
    channels, videos = payload["tables"]["channels"], payload["tables"]["videos"]
    payload["observed_dates"] = sorted({row["observed"] for row in channels if row.get("observed")})
    payload["summary"] = {
        "entries": len(channels), "video_rows": len(videos),
        "unique_videos": len({row["video_id"] for row in videos if row.get("video_id")}),
        "missing_video_ids": sum(not row.get("video_id") for row in videos),
        "listed_channels": sum(row["index_status"] == "ok" for row in channels),
        "channeling_rows": sum(row["channeling"] == "yes" for row in videos),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    template = (directory / "index.template.html").read_text(encoding="utf-8")
    html = template.replace("__INDEX_DATA__", encoded)
    for key, value in payload["summary"].items():
        html = html.replace("__" + key.upper() + "__", f"{value:,}")
    (directory / "index.html").write_text(html, encoding="utf-8", newline="\n")
    return payload["summary"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DIRECTORY)
    print(json.dumps(build(parser.parse_args().directory), indent=2))
