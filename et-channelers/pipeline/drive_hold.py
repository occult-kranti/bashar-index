#!/usr/bin/env python3
"""Fill the Drive hold: every downloaded audio file on disk that is not yet fully on Google Drive.

The sync (sync_archive.py push) deletes a stored file's local copy only when no live hold lists it. A Drive
hold is a note <root>/sync/holds/drive-<pid>.json whose process (a long `sleep`, see resume_jobs.sh) is alive;
this writes into every such note the item ids that are downloaded, on disk, and not yet in the Drive ledger
with all their parts. Run it after each Drive round and before the sync's next pass.

    python3 -I pipeline/drive_hold.py --root ~/et-channelers-private
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import add_root_arg, atomic_write_text, latest_by_key, layout, read_jsonl  # noqa: E402
import drive_stage  # noqa: E402


def fully_on_drive(paths):
    """Item ids whose every part is in the Drive ledger."""
    parts = {}
    for key, rec in drive_stage.ledger(paths).items():
        if key.startswith("audio:") and rec.get("item_id"):
            got = parts.setdefault(rec["item_id"], {"have": set(), "of": 1})
            got["have"].add(int(rec.get("part") or 1))
            got["of"] = max(got["of"], int(rec.get("parts") or 1))
    return {item for item, got in parts.items() if got["have"] >= set(range(1, got["of"] + 1))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    args = ap.parse_args()
    paths = layout(args.root)
    full = fully_on_drive(paths)
    last = latest_by_key(read_jsonl(paths.audio / "audio_manifest.jsonl"))
    here = sorted(vid for vid, rec in last.items()
                  if rec.get("status") == "ok" and rec.get("path") and (paths.audio / rec["path"]).exists())
    hold = [vid for vid in here if vid not in full]
    notes = sorted((paths.root / "sync" / "holds").glob("drive-*.json"))
    for note in notes:
        data = json.loads(note.read_text(encoding="utf-8"))
        data["video_ids"] = hold
        atomic_write_text(note, json.dumps(data))
    print(f"audio on disk {len(here)} | fully on Drive {len(here) - len(hold)} | held for Drive {len(hold)} "
          f"in {len(notes)} note(s)")
    if not notes:
        print("no Drive hold note: start one with ET_DRIVE_HOLD=1 bash pipeline/resume_jobs.sh", file=sys.stderr)


if __name__ == "__main__":
    main()
