#!/usr/bin/env python3
"""Scan the public files of the repository for small cells and for identifying strings. Prints counts only.

Written for task D7 of the paper review (21 November 2026): no public row, bin or cell may describe fewer than 5
creators, and the outputs of the transcription run and its analysis name no creator, video id or title.

Two checks:

* Small cells (needs no private file). In CSV files and Markdown tables, a value of 1 to 4 in a column that counts
  creators, recordings, audio files, transcripts, held or failed recordings is a cell of fewer than 5 creators (fewer
  than 5 recordings come from fewer than 5 creators); so is a row or a "xx 12" pair naming a language other than
  English, since every such language is spoken by fewer than 5 creators of this corpus. Strengthened on 2026-11-21
  (follow-up of D7, after the verifier's findings) with:
  - columns named in words, as in the progress table ("Recordings done", "Held"), whose cells may read "N of M";
    and two-column measure/value tables, whose value counts when the measure names a count ("Recordings ...");
  - JSON: every numeric leaf under a count-by-category dictionary (a key containing "by_" or ending in "_counts",
    such as final_failures_by_reason) is a count, as is a leaf whose own key names a count;
  - prose: "<number> <noun>" with a number under 5 (digits, or two to four) and a count noun (creators, recordings,
    files, transcripts, videos, channels), next to a word of a creator-level group (a language, hold-out, seen,
    other, held, failed, refused, reason, metadata, publisher, source, shared, kind, damaged), as in "2 hold-out
    transcripts" or "two files are each shared by two recordings"; and a language other than English followed by a
    number in prose ("Japanese 30"), counted with the "xx 12" pairs;
  - units (revised after the units decision of 21 November 2026: every count keeps the unit it was published in
    before, audio files for the run, its languages and its progress, recordings for the outcome of the selection): a
    count given in both units, whose difference would be solved (unit_pair). That is a table with a column of audio
    files and one of recordings; a measure/value table with "Audio files X" and "Recordings X"; a JSON object with
    the keys audio_files... and recordings... of the same ending; or a sentence with a count of audio files and one
    of recordings that differ by 1 to 4.
  JSON files are walked by key.
* Identifying strings (needs the private creator sets and the selection catalogue, passed by path). Creator names
  (the channel keys of the creator sets and the display names of the catalogue, two words or more), video ids, and
  the titles of the seen creators' recordings. Titles of hold-out and other creators are not read (hold-out rule);
  a file that lists those titles lists their ids as well, which are matched. Nothing found is printed: the report
  gives a count per file and per kind.

    python -I et-channelers/pipeline/public_disclosure_scan.py                      small cells, whole repository
    python -I et-channelers/pipeline/public_disclosure_scan.py --creator-sets PRIVATE/llm/creator-sets.json \
        --proposal PRIVATE/proposal.json                                             both checks
    ... --strict-run-outputs     exit 1 if a file made from the transcription run has a small cell

The run outputs (RUN_OUTPUTS) must have no small cell; tests/test_public_disclosure_scan.py asserts it, so a build
that would publish one fails the repository's checks.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIN_CREATORS = 5
TEXT_SUFFIXES = {'.csv', '.json', '.md', '.html', '.js', '.mjs', '.tex', '.txt', '.bib', '.svg', '.yml', '.py', '.css', '.tsv'}
COUNT_COLUMN = re.compile(r'^(creators?|recordings|audio_files|files|transcripts|n)$|^(creators|recordings|audio_files)_', re.I)
# A header or key named in words counts things when it names a count noun and no measure (hours, shares, ...).
COUNT_WORDS = re.compile(r'\b(creators?|recordings?|audio files?|files|transcripts?|transcribed|held|failures?|failed|videos?|channels?)\b')
MEASURE_WORDS = re.compile(r'\b(hours?|share|percent|minutes?|seconds?|usd|mean|median|rate|ratio|speed|wpm|estimate|kappa|'
                           r'p10|p90|q1|q3|ci95|low|high|left|right|words|per|bin|band|label|status|state|id|code|sha256|utc)\b')
AUDIO_FILE_COUNT = re.compile(r'\baudio files?\b')
RECORDING_COUNT = re.compile(r'\brecordings?\b')
# A count of audio files or recordings in prose: "1,697 audio files", "1,697 of 1,729 audio files", "1,976 selected recordings".
UNIT_COUNT = re.compile(r'(?<![\w.,$%-])(\d[\d,]*)(?:\s+of\s+(?:the\s+)?(\d[\d,]*))?\s+(?:distinct\s+|selected\s+|archived\s+)?'
                        r'(audio files?|recordings?)\b', re.I)
SENTENCE_END = re.compile(r'(?<=[.!?;])\s+|\n')
OTHER_LANGUAGES = {'japanese', 'spanish', 'portuguese', 'german', 'czech', 'finnish'}
LANGUAGE_PAIR = re.compile(r'(?<![A-Za-z])(ja|es|pt|de|cs|fi) \d+(?![\d.])')
# the same in words: "Japanese 30", "Finnish: 1", "German (8)" (every such language is one or two creators)
LANGUAGE_PROSE = re.compile(r'\b(japanese|spanish|portuguese|german|czech|finnish)\s*[:(]?\s*\d', re.I)
VIDEO_ID = re.compile(r'(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{11}(?![A-Za-z0-9_-])')
OF_TOTAL = re.compile(r'^\s*([\d,]+)\s+of\s+[\d,]+\s*$')
# Prose: a small number, up to two words of a group, a count noun; a group word next to it marks a creator-level cell.
GROUP_WORDS = ('english|japanese|spanish|portuguese|german|czech|finnish|language|languages|hold-out|holdout|seen|other|'
               'held|failed|failure|failures|refused|refusal|reason|reasons|metadata|publisher|source|sources|native|shared|'
               'kind|kinds|damaged|channelled|interview|interviews|meditation|meditations')
# "one" is left out: "one creator" and "one recording" are the generic singular of the rules ("a contrast inside one
# recording"), never a count; digits 1 to 4 and the words two to four are counts.
PROSE_COUNT = re.compile(r'(?<![\w.,$%-])([1-4]|two|three|four)\s+((?:(?:' + GROUP_WORDS + r'|audio|more|English-only)\s+){0,2})'
                         r'(creators?|recordings?|files?|transcripts?|videos?|channels?)\b', re.I)
GROUP = re.compile(r'\b(' + GROUP_WORDS + r')\b', re.I)
PROSE_SUFFIXES = ('.md', '.html', '.txt', '.tex', '.csv', '.json')
# Files made from the transcription run and its analysis, which must hold no cell of fewer than 5 creators.
RUN_OUTPUTS = ('et-channelers/research/transcription-run-2026-11-20/tables/',
               'et-channelers/dashboard/findings/data/',
               'et-channelers/research/transcription-run-2026-11-20/README.md',
               'et-channelers/dashboard/findings/README.md',
               'et-channelers/dashboard/findings/index.html',
               'et-channelers/knowledge-transfer/partial-cohort-asr-progress.md',
               'et-channelers/plan/collection_state.json')
SMALL_KINDS = ('count_under_5', 'language_row', 'language_pair', 'prose_count_under_5', 'unit_pair')


def words(name):
    return ' '.join(re.sub(r'[_`*()\-]+', ' ', str(name)).lower().split())


def counts_things(name):
    """A header or key that counts creators or recordings: the old exact names, or a count noun and no measure word."""
    text = words(name)
    return bool(COUNT_COLUMN.search(str(name).strip().strip('`'))) or bool(COUNT_WORDS.search(text) and not MEASURE_WORDS.search(text))


def small_count(value):
    """A count of 1 to 4 (a zero describes nobody); a cell "N of M" counts N."""
    text = str(value).replace(',', '').strip()
    match = OF_TOTAL.match(text)
    if match:
        text = match.group(1)
    try:
        number = float(text)
    except ValueError:
        return False
    return number.is_integer() and 1 <= number < MIN_CREATORS


def table_cells(header, rows):
    """Small cells of one table: (kind, count) pairs, never the values."""
    found = Counter()
    names = [words(name) for name in header]
    columns = [index for index, name in enumerate(header) if counts_things(name)]
    measure_value = names[:2] == ['measure', 'value']
    # a column of audio files beside a column of recordings: one count in both units
    found['unit_pair'] += bool(any(AUDIO_FILE_COUNT.search(names[index]) for index in columns)
                               and any(RECORDING_COUNT.search(names[index]) for index in columns))
    by_unit = {'audio': set(), 'recordings': set()}
    for row in rows:
        if any(cell.strip().lower() in OTHER_LANGUAGES for cell in row):
            found['language_row'] += 1
        for index in columns:
            if index < len(row) and small_count(row[index]):
                found['count_under_5'] += 1
        if measure_value and len(row) >= 2 and COUNTED_MEASURE.match(words(row[0])):
            found['count_under_5'] += small_count(row[1])
            measure = words(row[0])
            for unit, pattern in (('audio', r'audio files? '), ('recordings', r'recordings? ')):
                if re.match(pattern, measure):
                    by_unit[unit].add(re.sub(pattern, '', measure, count=1))
    found['unit_pair'] += len(by_unit['audio'] & by_unit['recordings'])     # "Audio files X" and "Recordings X"
    return found


def unit_pairs(text):
    """Sentences that give a count of audio files and a count of recordings differing by 1 to 4."""
    found = 0
    for sentence in SENTENCE_END.split(text):
        counts = {'audio': set(), 'recordings': set()}
        for match in UNIT_COUNT.finditer(sentence):
            unit = 'audio' if match.group(3).lower().startswith('audio') else 'recordings'
            counts[unit].update(int(value.replace(',', '')) for value in match.group(1, 2) if value)
        found += any(1 <= abs(a - r) < MIN_CREATORS for a in counts['audio'] for r in counts['recordings'])
    return found


COUNTED_MEASURE = re.compile(r'(creators?|recordings?|audio files?|files|transcripts?|videos?|channels?)\b')   # "Recordings ..."


def prose_counts(text):
    """'<number> <noun>' with a number under 5 next to a word of a creator-level group (within four words)."""
    found = 0
    for match in PROSE_COUNT.finditer(text):
        before = ' '.join(text[max(0, match.start() - 80):match.start()].split()[-4:])
        after = ' '.join(text[match.end():match.end() + 80].split()[:6])
        if GROUP.search(match.group(2)) or GROUP.search(before) or GROUP.search(after):
            found += 1
    return found


def markdown_tables(text):
    """Header and rows of each Markdown table (lines that start with '|')."""
    block = []
    for line in text.splitlines() + ['']:
        if line.lstrip().startswith('|'):
            block.append([cell.strip() for cell in line.strip().strip('|').split('|')])
            continue
        if len(block) >= 3 and set(''.join(block[1])) <= set('-: '):
            yield block[0], block[2:]
        block = []


def category_key(key):
    """A count-by-category dictionary: its numeric leaves are counts whatever their own keys are."""
    key = str(key).lower()
    return 'by_' in key or key.endswith('_counts')


def json_cells(value, found, key='', category=False):
    if isinstance(value, dict):
        if any(str(v).strip().lower() in OTHER_LANGUAGES for v in value.values() if isinstance(v, str)):
            found['language_row'] += 1
        numeric = {str(name).lower() for name, item in value.items() if isinstance(item, (int, float)) and not isinstance(item, bool)}
        endings = lambda prefix: {name[len(prefix):] for name in numeric if name.startswith(prefix)}
        found['unit_pair'] += len(endings('audio_files') & endings('recordings'))   # audio_files... beside recordings...
        for name, item in value.items():
            json_cells(item, found, name, category or category_key(name))
    elif isinstance(value, list):
        for item in value:
            json_cells(item, found, key, category)
    elif isinstance(value, (int, float)) and not isinstance(value, bool) and (category or counts_things(key)) and small_count(value):
        found['count_under_5'] += 1


def small_cells(path, text):
    found = Counter()
    suffix = path.suffix.lower()
    if suffix in ('.csv', '.tsv'):
        rows = list(csv.reader(io.StringIO(text.lstrip('﻿')), delimiter='\t' if suffix == '.tsv' else ','))
        if rows:
            found += table_cells(rows[0], rows[1:])
    elif suffix == '.json':
        try:
            json_cells(json.loads(text.lstrip('﻿')), found)
        except ValueError:
            pass
    if suffix in ('.md', '.tex', '.txt', '.html'):
        for header, rows in markdown_tables(text):
            found += table_cells(header, rows)
    found['language_pair'] += len(LANGUAGE_PAIR.findall(text)) if suffix in ('.md', '.csv', '.json', '.txt') else 0
    found['language_pair'] += len(LANGUAGE_PROSE.findall(text)) if suffix in PROSE_SUFFIXES else 0
    found['prose_count_under_5'] += prose_counts(text) if suffix in PROSE_SUFFIXES else 0
    found['unit_pair'] += unit_pairs(text) if suffix in PROSE_SUFFIXES else 0
    return +found


def normalise(text):
    return ' ' + re.sub(r'[^0-9a-z]+', ' ', text.lower()).strip() + ' '


class Forbidden:
    """Creator names, video ids and seen titles, held only in memory; matches are counted, never shown."""

    def __init__(self, creator_sets, proposal, catalogue):
        sets = json.loads(Path(creator_sets).read_text(encoding='utf-8'))
        keys = {key for group in ('seen_creators', 'holdout_creators', 'other_creators') for key in sets.get(group, [])}
        seen = set(sets.get('seen_creators', []))
        self.ids = set()
        if proposal:
            self.ids |= {row['video_id'] for row in json.loads(Path(proposal).read_text(encoding='utf-8'))['rows']}
        names, titles = {key.replace('-', ' ').replace('_', ' ') for key in keys}, set()
        if catalogue and Path(catalogue).is_file():
            with open(catalogue, encoding='utf-8-sig', newline='') as handle:
                for row in csv.DictReader(handle):
                    self.ids.add(row['video_id'].lstrip("'"))
                    if row.get('creator'):
                        names.add(row['creator'])
                    if row.get('channel_dir') in seen and row.get('title'):    # seen creators only
                        titles.add(row['title'])
        self.names = {name for name in map(normalise, names) if len(name.split()) >= 2}
        self.titles = {title for title in map(normalise, titles) if len(title.split()) >= 3 and len(title) >= 16}
        self.keys = {key.lower() for key in keys if '-' in key or '_' in key}

    def count(self, text):
        found = Counter()
        found['video_id'] = sum(1 for token in VIDEO_ID.findall(text) if token in self.ids)
        plain = normalise(text)
        lowered = text.lower()
        found['creator_name'] = sum(1 for name in self.names if name in plain) + sum(1 for key in self.keys if key in lowered)
        found['title'] = sum(1 for title in self.titles if title in plain)
        return +found


def public_files(root):
    listed = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], capture_output=True, check=True).stdout.decode('utf-8')
    return [root / name for name in listed.split('\0') if name]


def read_text(path):
    if path.suffix.lower() == '.pdf':
        try:
            from pypdf import PdfReader
            return '\n'.join(page.extract_text() or '' for page in PdfReader(str(path)).pages)
        except Exception:                                   # no reader available, or an unreadable file
            return None
    if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 20_000_000:
        return None
    return path.read_bytes().decode('utf-8', errors='replace')


def area(relative):
    parts = relative.split('/')
    return '/'.join(parts[:3]) if parts[0] == 'et-channelers' else '/'.join(parts[:2])


def scan(root, forbidden=None, only=None):
    report = {}
    for path in public_files(root):
        relative = path.relative_to(root).as_posix()
        if only and not any(relative.startswith(prefix) for prefix in only):
            continue
        text = read_text(path)
        if text is None:
            continue
        found = Counter() if path.suffix.lower() == '.pdf' else small_cells(path, text)
        if forbidden is not None:
            found += forbidden.count(text)
        if found:
            report[relative] = dict(found)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--creator-sets', type=Path)
    parser.add_argument('--proposal', type=Path)
    parser.add_argument('--catalogue', type=Path, help='the selection catalogue with titles (default: the public recording-dates.csv)')
    parser.add_argument('--strict-run-outputs', action='store_true')
    parser.add_argument('--files', action='store_true', help='list counts per file, not only per area')
    args = parser.parse_args(argv)
    forbidden = None
    if args.creator_sets:
        catalogue = args.catalogue or args.root / 'et-channelers' / 'dashboard' / 'collection' / 'recording-dates.csv'
        forbidden = Forbidden(args.creator_sets, args.proposal, catalogue)
        print(json.dumps({'forbidden_strings': {'creator_names': len(forbidden.names) + len(forbidden.keys),
                                                'video_ids': len(forbidden.ids), 'seen_titles': len(forbidden.titles)}}))
    report = scan(args.root, forbidden)
    by_area = defaultdict(Counter)
    for relative, found in report.items():
        by_area[area(relative)].update({kind: 1 for kind in found})     # files per kind
    total = Counter()
    for found in report.values():
        total.update(found)
    run = {relative: found for relative, found in report.items() if relative.startswith(RUN_OUTPUTS)}
    run_small = {relative: found for relative, found in run.items() if any(kind in found for kind in SMALL_KINDS)}
    print(json.dumps({'files_scanned_with_findings': len(report), 'findings_by_kind': dict(total),
                      'run_outputs_with_small_cells': len(run_small),
                      'run_outputs_with_identifiers': sum(1 for found in run.values()
                                                          if any(kind in found for kind in ('video_id', 'creator_name', 'title')))}))
    for name in sorted(by_area):
        print(json.dumps({'area': name, 'files_by_kind': dict(by_area[name])}))
    if args.files:
        for relative in sorted(report):
            print(json.dumps({'file': relative, 'counts': report[relative]}))
    return 1 if args.strict_run_outputs and run_small else 0


if __name__ == '__main__':
    raise SystemExit(main())
