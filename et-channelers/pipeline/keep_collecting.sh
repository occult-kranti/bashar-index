#!/usr/bin/env bash
# Keep collecting from this machine: one cloud cycle (run_cycle.py) every few hours, for every person.
#
#   setsid nohup bash et-channelers/pipeline/keep_collecting.sh >> ~/et-channelers-private/logs/collect.log 2>&1 < /dev/null &
#
# Each cycle lists channels whose listing is a week old, reads the feeds, queues what is new (the makers'
# own feeds, files on their sites, archive.org audio, and interviews with live channeling), downloads down
# to the free-disk floor, fetches the publishers' texts, types the interviews and rebuilds the tables.
# It never starts while another downloader is running (two downloaders could fetch the same item), and
# it never starts speech-to-text (that runs on its own, one process). When a private store is syncing
# (save_to_github.sh), stored audio leaves the disk and the next cycle can download more.
# Stop it with: kill <pid of this script>.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
py="${ET_PYTHON:-$HOME/et-venv/bin/python}"
root="${ET_PRIVATE_DIR:-$HOME/et-channelers-private}"
pause_hours="${ET_CYCLE_PAUSE_HOURS:-3}"
max_hours="${ET_CYCLE_MAX_HOURS:-80}"
while true; do
  while pgrep -f "download_enclosures.py" >/dev/null; do
    sleep 120                                    # another download is running: wait for it
  done
  echo "== cycle $(date -u +%FT%TZ)"
  "$py" -I "$here/run_cycle.py" --go --root "$root" --max-hours "$max_hours" || echo "== cycle ended with code $?"
  sleep $((pause_hours * 3600))
done
