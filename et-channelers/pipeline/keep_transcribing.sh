#!/usr/bin/env bash
# Speech-to-text for everything held here, channeled material first, and keep going as audio arrives.
#
#     bash et-channelers/pipeline/keep_transcribing.sh            # in the background: setsid nohup ... &
#
# Order: Bashar's archive.org sessions (darryl-anka, lane ia) while their download runs, then the
# interview types are re-read, then everyone else one file per person in turn, then one retry of
# what failed. A pass that is stopped is simply started again: finished files are skipped.
#
# Size it to the machine (each process with base.en int8 needs about 1.6 GB of memory):
#   2 cores,  8 GB:  ET_ASR_WORKERS=1 ET_ASR_THREADS=2   (about 1.3x real time in all)
#   4 cores, 16 GB:  ET_ASR_WORKERS=2 ET_ASR_THREADS=2
#   8 cores, 32 GB:  ET_ASR_WORKERS=4 ET_ASR_THREADS=2
# A GPU is far faster: ET_ASR_MODEL=large-v3 ET_ASR_DEVICE=cuda ET_ASR_COMPUTE=float16 (see README).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
py="${ET_PYTHON:-$HOME/et-venv/bin/python}"
root="${ET_PRIVATE_DIR:-$HOME/et-channelers-private}"
first="${ET_ASR_FIRST:-darryl-anka}"                 # whose archive.org sessions go first
common=(--root "$root" --model "${ET_ASR_MODEL:-base.en}" --language "${ET_ASR_LANGUAGE:-en}"
        --device "${ET_ASR_DEVICE:-cpu}" --compute-type "${ET_ASR_COMPUTE:-int8}"
        --workers "${ET_ASR_WORKERS:-1}" --cpu-threads "${ET_ASR_THREADS:-2}" --batch-size "${ET_ASR_BATCH:-8}")

for round in $(seq 1 400); do
  echo "== $first archive.org sessions, round $round $(date -u +%FT%TZ)"
  # the pass prints "N to transcribe" first; that number is read from its own output
  left=$("$py" -I "$here/transcribe.py" "${common[@]}" --only "$first" --lanes ia --order as-is 2>&1 \
         | tee /dev/stderr | grep -o "^[0-9]* to transcribe" | head -1 | cut -d" " -f1)
  # sessions keep arriving while their download runs: stop only when none was left and none is coming
  if [ "${left:-1}" = "0" ] && ! pgrep -f "queue_archive_org" >/dev/null; then break; fi
  sleep 120
done
"$py" -I "$here/interview_types.py" --root "$root"
for round in $(seq 1 60); do
  echo "== everyone else, round $round $(date -u +%FT%TZ)"
  if "$py" -I "$here/transcribe.py" "${common[@]}" --order round-robin; then break; fi
  sleep 60
done
"$py" -I "$here/transcribe.py" "${common[@]}" --order round-robin --retry-failed
"$py" -I "$here/interview_types.py" --root "$root"
echo "== finished $(date -u +%FT%TZ)"
