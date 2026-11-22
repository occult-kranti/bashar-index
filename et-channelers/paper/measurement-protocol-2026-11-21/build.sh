#!/usr/bin/env bash
# Builds main.pdf in this folder from the files kept here. Usage:
#   bash build.sh             typeset only (findings/ and floats/ as they are)
#   bash build.sh --numbers   first regenerate findings/ and floats/ with the private builder, then typeset
# The private builder and the paper check read private files; they run only where the private folder exists, with the
# guarded analysis venv (one process, no worker pool, no API call). Override the defaults with ET_PY and ET_WORK.
set -u
cd "$(dirname "$0")"
HERE="$(pwd)"
PY="${ET_PY:-$HERE/../../../../analysis-venv/Scripts/python.exe}"
WORK="${ET_WORK:-$HERE/../../../../../et-channelers-private/provisioning/claude-cohort-asr-20261120-v1/paper-measurement-2026-11-21/work}"

# MiKTeX on this machine (pdflatex, bibtex) when it is not on the PATH already.
if ! command -v pdflatex > /dev/null 2>&1 && [ -n "${LOCALAPPDATA:-}" ]; then
  export PATH="$(cygpath -u "$LOCALAPPDATA")/Programs/MiKTeX/miktex/bin/x64:$PATH"
fi

if [ "${1:-}" = "--numbers" ]; then
  [ -f "$WORK/build_numbers.py" ] || { echo "private builder not found: $WORK"; exit 1; }
  (cd "$WORK" && "$PY" -I build_numbers.py) || exit 1
fi

# Anonymous submission (privacy review P30): the PDF's creation and modification dates are written in UTC from the
# build time, so the metadata carry no time-zone offset of the authors' machine.
export SOURCE_DATE_EPOCH="$(date -u +%s)"
export FORCE_SOURCE_DATE=1

rm -f main.aux main.bbl main.blg main.out
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
bibtex main > bibtex.log 2>&1
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex > build.log 2>&1

echo "--- errors, undefined references, citations and macros, float and box problems (last pass) ---"
grep -n -E '^!|Undefined control sequence|undefined|Float too large|Overfull' build.log
echo "--- bibtex ---"
grep -n -i -E 'warning|error' bibtex.log | grep -v -i 'unsupported version of windows'
grep -n 'Output written' build.log

# Paper check: literal numerals, wording, privacy (names, codes, ids), pending placeholders. Prints counts, no names.
if [ -f "$WORK/check_paper.py" ]; then
  "$PY" -I "$WORK/check_paper.py" "$HERE"
else
  echo "paper check skipped (private folder not present)"
fi
