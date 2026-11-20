#!/usr/bin/env bash
# Builds main.pdf in this folder from the files kept here. Usage: bash build.sh
set -u
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
bibtex main > /dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex > build.log 2>&1
grep -n -E '^!|LaTeX Warning|Overfull|Citation' build.log
grep -n 'Output written' build.log
