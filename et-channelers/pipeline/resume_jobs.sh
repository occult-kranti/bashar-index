#!/usr/bin/env bash
# Start again every standing job a Codespace restart stops, each only if it is not running already:
#   the sync to the private store (and the text mirror), the collection cycles, speech-to-text in a loop
#   that restarts it, if asked a Drive hold (ET_DRIVE_HOLD=1), and, if a queue is named, a backlog download.
#
#   bash et-channelers/pipeline/resume_jobs.sh                         # the three standing jobs
#   ET_BACKLOG_QUEUE=~/et-channelers-private/jobs/queue_backlog.csv bash et-channelers/pipeline/resume_jobs.sh
#
# Settings (environment): ET_PRIVATE_DIR (default ~/et-channelers-private), ET_GH_TOKEN_FILE (default
# ~/.config/et-channelers/github_token), ET_HOLD_UNTRANSCRIBED (default 1: every new file stays on disk until
# it is transcribed), ET_ASR_WORKERS / ET_ASR_THREADS (default 1 / 2, for 2 cores), ET_BACKLOG_QUEUE.
# The YouTube override is never set here: the cycles skip their listing step by rule (HANDOFF 6.6).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
py="${ET_PYTHON:-$HOME/et-venv/bin/python}"
root="${ET_PRIVATE_DIR:-$HOME/et-channelers-private}"
logs="$root/logs"
mkdir -p "$logs"
cd "$repo" || exit 1

running() { pgrep -f -- "$1" >/dev/null; }

if running "sync_archive.py push --root"; then
  echo "sync: already running"
else
  ET_GH_TOKEN_FILE="${ET_GH_TOKEN_FILE:-$HOME/.config/et-channelers/github_token}" \
  ET_HOLD_UNTRANSCRIBED="${ET_HOLD_UNTRANSCRIBED:-1}" \
    bash "$here/save_to_github.sh" >> "$logs/save_to_github.log" 2>&1 < /dev/null
  echo "sync: started (log $logs/sync.log)"
fi

if running "keep_collecting.sh"; then
  echo "collection cycles: already running"
else
  setsid nohup bash "$here/keep_collecting.sh" >> "$logs/collect.log" 2>&1 < /dev/null &
  echo "collection cycles: started (log $logs/collect.log)"
fi

if running "keep_transcribing.sh"; then
  echo "speech-to-text: already running"
else
  # keep_transcribing.sh ends when nothing is left; the loop starts it again every 30 minutes
  ET_ASR_WORKERS="${ET_ASR_WORKERS:-1}" ET_ASR_THREADS="${ET_ASR_THREADS:-2}" \
    setsid nohup bash -c "while true; do bash '$here/keep_transcribing.sh'; sleep 1800; done" \
    >> "$logs/asr.log" 2>&1 < /dev/null &
  echo "speech-to-text: started (log $logs/asr.log)"
fi

if [ "${ET_DRIVE_HOLD:-0}" = "1" ]; then
  # a Drive hold: a long sleep whose note lists the files to keep on disk until their Drive round is recorded.
  # The holder is found by its command line ($! is setsid's own id when setsid forks).
  holder=$(pgrep -n -f "^sleep 2592000$" || true)
  if [ -z "$holder" ]; then
    setsid nohup sleep 2592000 >/dev/null 2>&1 < /dev/null &
    sleep 1
    holder=$(pgrep -n -f "^sleep 2592000$")
  fi
  mkdir -p "$root/sync/holds"
  if [ ! -f "$root/sync/holds/drive-$holder.json" ]; then
    printf '{"who": "drive", "pid": %s, "since": "%s", "video_ids": [], "why": "new audio not yet on Google Drive"}' \
      "$holder" "$(date -u +%FT%TZ)" > "$root/sync/holds/drive-$holder.json"
  fi
  "$py" -I "$here/drive_hold.py" --root "$root"      # list in it every file on disk not yet fully on Drive
  echo "Drive hold: holder $holder (run drive_hold.py again after each Drive round)"
fi

if [ -n "${ET_BACKLOG_QUEUE:-}" ]; then
  if running "download_enclosures.py --root $root --queue ${ET_BACKLOG_QUEUE}"; then
    echo "backlog download: already running"
  else
    setsid nohup "$py" -I "$here/download_enclosures.py" --root "$root" --queue "$ET_BACKLOG_QUEUE" --all \
      --workers 3 --per-host 2 --min-interval 1.5 --min-free-gb 3 >> "$logs/backlog_download.log" 2>&1 < /dev/null &
    echo "backlog download: started from $ET_BACKLOG_QUEUE (log $logs/backlog_download.log)"
  fi
fi
