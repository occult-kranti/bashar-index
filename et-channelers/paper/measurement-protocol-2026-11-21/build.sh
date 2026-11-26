#!/usr/bin/env bash
# Builds main.pdf in this folder from the files kept here. Usage:
#   bash build.sh             typeset only (findings/ and floats/ as they are)
#   bash build.sh --numbers   first regenerate findings/ and floats/ with the private builder, then typeset
# The private builder and the paper check read private files; they run only where the private folder exists, with the
# guarded analysis venv (one process, no worker pool, no API call). ET_PY names the guarded venv's Python and ET_WORK the
# private work folder (release pass 2, fix step, 2026-11-26: this public file names neither path).
set -u
cd "$(dirname "$0")"
HERE="$(pwd)"
PY="${ET_PY:-}"
WORK="${ET_WORK:-}"
if [ -z "$PY" ]; then
  echo "set ET_PY to the guarded analysis venv's Python (it also removes the PDF's document information)"; exit 1
fi
if [ "${1:-}" = "--numbers" ] && [ -z "$WORK" ]; then
  echo "set ET_WORK to the private work folder to regenerate findings/ and floats/"; exit 1
fi

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

# Release pass 2, fix step (2026-11-26; rule 6, D30): main.pdf carries no document information dictionary. main.tex
# omits the dates and the trailer id; the Producer and Creator keys are removed here (pages and text unchanged).
if [ -f "$PY" ]; then
  "$PY" -I - main.pdf <<'PYEOF'
import os
import sys
from pypdf import PdfReader, PdfWriter
path = sys.argv[1]
reader = PdfReader(path)
pages = len(reader.pages)
writer = PdfWriter(clone_from=reader)
writer.metadata = None
with open(path + ".tmp", "wb") as handle:
    writer.write(handle)
check = PdfReader(path + ".tmp")
assert check.metadata is None and len(check.pages) == pages, "stripped PDF differs"
os.replace(path + ".tmp", path)
print("main.pdf: document information removed (%d pages)" % pages)
PYEOF
else
  echo "main.pdf: document information NOT removed (the analysis venv's Python was not found)"
fi

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
