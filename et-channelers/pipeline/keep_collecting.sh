#!/usr/bin/env bash
# Keep collecting from this machine: one cloud cycle (run_cycle.py) every few hours, for every person.
#
#   setsid nohup bash et-channelers/pipeline/keep_collecting.sh >> ~/et-channelers-private/logs/collect.log 2>&1 < /dev/null &
#
# Each cycle lists channels whose listing is a week old (only if the owner set ET_YOUTUBE_ROBOTS_OVERRIDE=1:
# youtube.com's robots.txt disallows what the listing requests; otherwise the step is "skipped by rule"),
# reads the feeds, queues what is new (the makers' own feeds, files on their sites, archive.org audio, and
# interviews with live channeling), downloads down to the free-disk floor, fetches the publishers' texts,
# types the interviews and rebuilds the tables.
# Never two downloaders: every download_enclosures.py takes one lock (<root>/jobs/download_enclosures.lock),
# so the cycle's download waits for one started elsewhere (an archive.org run, another cycle) and reads
# what is left to do only when it has finished. Never two of these loops: a second copy finds this one's
# lock (<root>/jobs/collect.lock) and leaves at once. It never starts speech-to-text (that runs on its own).
# When a private store is syncing (save_to_github.sh), stored audio leaves the disk and the next cycle can
# download more. Stop it with: kill <pid of this script>. A cycle that is running then finishes on its own;
# to stop that too, kill the whole group the setsid above made: kill -- -<pid of this script>. The lock is
# this script's alone (its children do not inherit it), so a new loop can start at once either way.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
py="${ET_PYTHON:-$HOME/et-venv/bin/python}"
root="${ET_PRIVATE_DIR:-$HOME/et-channelers-private}"
pause_hours="${ET_CYCLE_PAUSE_HOURS:-3}"
max_hours="${ET_CYCLE_MAX_HOURS:-80}"
mkdir -p "$root/jobs"
exec 9>>"$root/jobs/collect.lock"
if ! flock -n 9; then
  echo "$(date -u +%FT%TZ) another keep_collecting.sh is running (it holds $root/jobs/collect.lock): not starting a second one"
  exit 0
fi
while true; do
  echo "== cycle $(date -u +%FT%TZ)"
  "$py" -I "$here/run_cycle.py" --go --root "$root" --max-hours "$max_hours" 9>&- || echo "== cycle ended with code $?"
  sleep $((pause_hours * 3600)) 9>&-
done
