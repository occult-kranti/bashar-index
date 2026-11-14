#!/usr/bin/env bash
# Save the collected audio and transcripts to a PRIVATE GitHub repository, and keep saving.
#
# Run it yourself in this Codespace's terminal; it asks for your GitHub login once:
#     bash et-channelers/pipeline/save_to_github.sh                  # <your login>/et-channelers-archive
#     bash et-channelers/pipeline/save_to_github.sh OWNER/REPO       # another private repository
#
# Why your login is needed: the Codespace's own token can write only to bashar-index, which is public
# and must never hold these recordings and texts (they belong to their makers). With your login this
#   1. creates the repository as PRIVATE if it does not exist, and stops if it exists and is not private;
#   2. starts sync_archive.py in the background: audio, transcripts and texts go to the repository's
#      release as checked tar bundles, and a local audio file is deleted only after its stored copy
#      has been verified, which frees the disk for the next downloads;
#   3. every 30 minutes, copies the texts into the repository as plain files (mirror_texts.py), so they
#      can be read and searched on GitHub.
# Run it again after the Codespace restarts: everything resumes where it stopped.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
py="${ET_PYTHON:-$HOME/et-venv/bin/python}"
root="${ET_PRIVATE_DIR:-$HOME/et-channelers-private}"
tag="${ET_ARCHIVE_TAG:-archive-v1}"
checkout="${ET_ARCHIVE_CHECKOUT:-$HOME/et-archive-checkout}"

# gh prefers the Codespace's own GITHUB_TOKEN over your login; set it aside here and in everything started here
unset GITHUB_TOKEN GH_TOKEN

if [ "${1:-}" = "--mirror-loop" ]; then          # the background half: copy the texts every 30 minutes
  repo="$2"
  interval="${ET_MIRROR_INTERVAL:-1800}"          # 0: once, then stop
  while true; do
    "$py" -I "$here/mirror_texts.py" --root "$root" --repo "$repo" --checkout "$checkout" --push || true
    [ "$interval" = "0" ] && exit 0
    sleep "$interval"
  done
fi

if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  echo "Log in to GitHub: choose GitHub.com, HTTPS, and 'Login with a web browser'."
  gh auth login --hostname github.com --git-protocol https --web
fi
login="$(gh api user --jq .login)"
repo="${1:-$login/et-channelers-archive}"
if ! gh repo view "$repo" >/dev/null 2>&1; then
  gh repo create "$repo" --private \
    --description "Private archive of the et-channelers pipeline (bashar-index). Not for publication."
  echo "created $repo (private)"
fi
if [ "$(gh repo view "$repo" --json isPrivate --jq .isPrivate)" != "true" ]; then
  echo "STOPPED: $repo is not private. Make it private first: these recordings and texts belong to their makers." >&2
  exit 5
fi
mkdir -p "$root/logs"
store="gh:$repo@$tag"
"$py" -I "$here/sync_archive.py" status --root "$root" --store "$store" || true

if pgrep -f "sync_archive.py push" >/dev/null; then
  echo "a sync is already running: not starting a second one"
else
  setsid nohup "$py" -I "$here/sync_archive.py" push --root "$root" --store "$store" --delete audio --watch 300 \
    >> "$root/logs/sync.log" 2>&1 < /dev/null &
  echo "audio and transcripts: uploading to the release '$tag' of $repo in the background (log: $root/logs/sync.log)"
fi
if pgrep -f "save_to_github.sh --mirror-loop" >/dev/null; then
  echo "the text mirror is already running"
else
  setsid nohup bash "$here/save_to_github.sh" --mirror-loop "$repo" >> "$root/logs/mirror.log" 2>&1 < /dev/null &
  echo "texts: copied into $repo as files every 30 minutes (log: $root/logs/mirror.log)"
fi
echo "done. Stored items are never downloaded again, and local audio is removed only after its copy is verified."
