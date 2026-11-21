#!/usr/bin/env python3
"""Publish the state of the latest-20 collection: the closed download goal and the finished transcription run.

The collection dashboard and the dashboard directory read et-channelers/plan/collection_state.json. This script
joins three things and refuses to write when they disagree:

* the owner's decision that closed the download goal (a private record; only its date, its aggregate counts and
  its SHA-256 are copied, never the recordings it lists or the owner's words);
* the committed public evidence of the close (knowledge-transfer/evidence/2026-11-20-close/): the receipt
  checkpoint, the Drive verification, the per-recording outcome table and the failed-links table that the decision
  is bound to by hash;
* the committed tables of the transcription run (research/transcription-run-2026-11-20/tables/) and the last row of
  its progress table (knowledge-transfer/partial-cohort-asr-progress.md).

    python -I et-channelers/pipeline/collection_state.py --decision PRIVATE_RUN_FOLDER/download-goal-closed.json \
        --out et-channelers/plan/collection_state.json
    python -I et-channelers/pipeline/collection_state.py --check et-channelers/plan/collection_state.json

`--check` re-reads the committed public evidence and confirms that a published state still agrees with it; it needs
no private file. Nothing here contacts YouTube, Drive or any other service.

Small cells (paper review, task D7, and its follow-up of 21 November 2026): no count by category describes fewer than
5 creators. The creators behind each category are counted from the ledger fields of the public evidence (the creator
and outcome of each recording), and categories are pooled by the rule of the exploratory reporting plan, section 3:
a category of fewer than 5 creators goes into "other", and while "other" holds fewer than 5 creators the smallest
remaining category joins it. When every category would end up in "other", only the total is published (the final
download failures are such a case). The run is counted in audio files, the unit the state published before
21 November 2026, never in recordings beside them (units decision of 21 November 2026).

Ledger fields only (close of the privacy findings, 21 November 2026): the state describes the whole run with counts
of audio files, hours of audio and languages, which come from the run's ledger. It carries no word count and no time
without speech of the whole run: those are transcript and timing measures of every creator, hold-out creators
included, and the run report now gives timing measures for the creators seen before the registry freeze only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSE = ROOT / 'knowledge-transfer' / 'evidence' / '2026-11-20-close'
RUN_TABLES = ROOT / 'research' / 'transcription-run-2026-11-20' / 'tables'
PROGRESS = ROOT / 'knowledge-transfer' / 'partial-cohort-asr-progress.md'

SCOPE = 'latest20_collection_state'
DECISION_KIND = 'owner_decision_download_goal_closed'
SOURCES = ('youtube_native', 'youtube_track_unverified', 'publisher_edition')
# The decision names its failure categories; the public failed-links table labels the same recordings.
REASONS = {'provider_refusal_http_403': 'Provider refusal', 'metadata_lookup_failure': 'Metadata lookup failure'}
PROGRESS_ROW = re.compile(r'^\| (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) \| ([\d,]+) of ([\d,]+) \| ([\d.]+) of ([\d.]+) \|'
                          r'.*\| finished \|\s*$')
MIN_CREATORS = 5
POOLED = 'other'


def pool_by_creators(groups, least=MIN_CREATORS):
    """groups: {category: (count, set of creators)}. Returns {category: count} with every category of fewer than `least`
    creators pooled into POOLED (exploratory reporting plan, section 3): while the pool holds fewer than `least`
    creators, the remaining category with the fewest creators (then the fewest items) joins it. Returns None when every
    category ends up pooled, since a breakdown that is all "other" is the total alone. Order is kept, POOLED last."""
    creators = lambda names: set().union(*(groups[name][1] for name in names)) if names else set()
    pooled = [name for name, (_, who) in groups.items() if len(who) < least]
    if not pooled:
        return {name: count for name, (count, _) in groups.items()}
    while len(creators(pooled)) < least:
        rest = [name for name in groups if name not in pooled]
        if not rest:
            return None
        pooled.append(min(rest, key=lambda name: (len(groups[name][1]), groups[name][0])))
    kept = {name: count for name, (count, _) in groups.items() if name not in pooled}
    if not kept:
        return None
    kept[POOLED] = sum(groups[name][0] for name in pooled)
    return kept


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def whole(value):
    return type(value) is int and value >= 0


def utc(value):
    """An ISO UTC instant, returned in the Z form; anything else is refused."""
    need(isinstance(value, str), 'utc_instant')
    instant = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(instant.tzinfo is not None and instant.utcoffset() == dt.timedelta(0), 'utc_instant')
    return instant.strftime('%Y-%m-%dT%H:%M:%SZ')


def sha(value):
    need(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value), 'sha256')
    return value


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def read_csv(raw):
    return list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))


def measures(path):
    rows = read_csv(Path(path).read_bytes())
    need(rows and set(rows[0]) == {'measure', 'value'}, 'summary_columns')
    return {row['measure']: row['value'] for row in rows}


def public_facts(close=CLOSE, tables=RUN_TABLES, progress=PROGRESS):
    """Read and cross-check the committed public evidence; return only aggregate values."""
    close, tables = Path(close), Path(tables)
    checkpoint = read_json(close / 'checkpoint.json')
    drive = read_json(close / 'drive-verification.json')
    selection = sha(checkpoint.get('selection_sha256'))
    selected, creators, verified = (checkpoint.get(key) for key in ('selected_recordings', 'selected_creators', 'verified_audio'))
    need(all(whole(value) and value > 0 for value in (selected, creators, verified)) and verified <= selected, 'checkpoint_counts')
    dispositions = checkpoint.get('selection_dispositions')
    need(isinstance(dispositions, dict) and all(whole(v) for v in dispositions.values())
         and sum(dispositions.values()) == selected and dispositions.get('verified_audio_receipt') == verified,
         'checkpoint_dispositions')
    outstanding = selected - verified
    need(drive.get('schema_version') == 1 and drive.get('selection_sha256') == selection
         and drive.get('selected_recordings') == selected and drive.get('selected_creators') == creators
         and drive.get('recordings_with_prior_verified_receipts') == verified
         and drive.get('recordings_with_all_required_drive_objects_matching') == verified
         and drive.get('recordings_with_discrepancies') == 0
         and drive.get('outstanding_without_a_verified_recording') == outstanding, 'drive_verification')
    rows = read_csv((close / 'recording-status.csv').read_bytes())
    need(len(rows) == selected and len({row['creator_key'] for row in rows}) == creators, 'recording_rows')
    need(Counter(row['checkpoint_disposition'] for row in rows) == Counter(dispositions), 'recording_dispositions')
    archived = [row for row in rows if row['checkpoint_disposition'] == 'verified_audio_receipt']
    need(all(row['verified_audio'] in SOURCES for row in archived)
         and all(row['verified_audio'] == '' for row in rows
                 if row['checkpoint_disposition'] != 'verified_audio_receipt'), 'recording_sources')
    # Creators per audio source, from the creator and the source of each archived recording (ledger fields).
    sources = {key: (0, set()) for key in SOURCES}
    for row in archived:
        count, who = sources[row['verified_audio']]
        sources[row['verified_audio']] = (count + 1, who | {row['creator_key']})
    by_source = pool_by_creators(sources)
    missing = Counter(row['creator_key'] for row in rows if row['checkpoint_disposition'] != 'verified_audio_receipt')
    need(len(missing) >= MIN_CREATORS, 'final_failure_creators')   # the final failures as one count: 5 or more creators
    complete = creators - len(missing)
    need(checkpoint.get('complete_creators') == complete, 'complete_creators')
    # The hash is of the file as git stores it (LF line ends), so a Windows checkout with CRLF ends gives the
    # same value as the Linux CI checkout; the private decision record may bind either line-end form.
    failed_raw = (close / 'failed-links' / 'failed-links.csv').read_bytes().replace(b'\r\n', b'\n')
    failed = read_csv(failed_raw)
    need(len(failed) == outstanding, 'failed_links_rows')
    reasons = Counter(row['Failure category'] for row in failed)
    # Creators per failure reason: the failed recording's creator is read from the outcome table (by video id), and
    # only the reason column of the failed-links table is used.
    creator_of = {row['video_id']: row['creator_key'] for row in rows if row['checkpoint_disposition'] != 'verified_audio_receipt'}
    label_key = {label: key for key, label in REASONS.items()}
    by_reason = {}
    for row in failed:
        video, label = row['Video ID'].lstrip("'"), row['Failure category']
        need(video in creator_of and label in label_key, 'failed_links_join')
        count, who = by_reason.get(label_key[label], (0, set()))
        by_reason[label_key[label]] = (count + 1, who | {creator_of[video]})
    need(sum(count for count, _ in by_reason.values()) == outstanding, 'failed_links_join')

    summary = measures(tables / 'summary.csv')
    need(int(summary['Recordings selected']) == selected, 'run_selection')
    # The run is counted in audio files, as the state published it before 21 November 2026 (units decision of that
    # day): no count of the run in recordings stands beside them, since the difference of the two would be solved.
    need(not {'Recordings in the run', 'Recordings transcribed'} & set(summary), 'run_units')
    files, transcribed = int(summary['Audio files in the run']), int(summary['Audio files transcribed'])
    not_transcribed = int(summary['Recordings not transcribed'])
    need(0 < transcribed <= files and transcribed + not_transcribed == files, 'run_files')
    hours_done = float(summary['Hours transcribed'])
    need(hours_done > 0, 'run_measures')
    # Since 2026-11-21 (task D7) the table has no row of fewer than 5 creators: English and one pooled row of the
    # other languages, whose rows sum to the audio files transcribed; the summary gives the number of languages found.
    languages = [row for row in read_csv((tables / 'languages.csv').read_bytes())
                 if (row.get('scope') or 'language') in ('language', 'pooled')]
    need(languages and 'recordings' not in languages[0] and sum(int(row['audio_files']) for row in languages) == transcribed
         and all(int(row['creators']) >= MIN_CREATORS for row in languages), 'run_languages')
    found = int(summary['Languages found']) if 'Languages found' in summary else len(languages)
    need(found >= len(languages), 'run_language_count')
    rows = [line for line in Path(progress).read_text(encoding='utf-8').splitlines() if PROGRESS_ROW.match(line)]
    need(len(rows) == 1, 'progress_finished_row')
    day, clock, done, total, hours, all_hours = PROGRESS_ROW.match(rows[0]).groups()
    need(int(done.replace(',', '')) == transcribed and int(total.replace(',', '')) == files
         and float(hours) == hours_done and float(all_hours) >= hours_done, 'progress_matches_tables')
    return {
        'selection': {'sha256': selection, 'recordings': selected, 'creators': creators},
        'archived': verified, 'outstanding': outstanding, 'complete_creators': complete,
        'by_source': by_source, 'failure_labels': dict(reasons), 'by_reason': pool_by_creators(by_reason),
        'failed_links_sha256': hashlib.sha256(failed_raw).hexdigest(),
        'failed_links_crlf_sha256': hashlib.sha256(failed_raw.replace(b'\n', b'\r\n')).hexdigest(),
        'receipt_checkpoint_utc': utc(checkpoint.get('as_of_utc')),
        'drive': {'finished_at_utc': utc(drive.get('drive_metadata_finished_utc')), 'recordings_matching': verified,
                  'discrepancies': 0},
        'transcription': {'state': 'finished', 'finished_at_utc': utc(f'{day}T{clock}:00Z'),
                          'audio_files': files, 'audio_files_transcribed': transcribed,
                          'not_transcribed': not_transcribed, 'hours': float(all_hours),
                          'hours_transcribed': hours_done, 'language_count': found,
                          'languages': [{'language': row['language'], 'audio_files': int(row['audio_files'])}
                                        for row in sorted(languages, key=lambda row: -int(row['audio_files']))]},
    }


def decision_facts(raw, public):
    """Copy the date and counts of the owner's decision after checking them against the public evidence."""
    value = json.loads(raw.decode('utf-8-sig'))
    need(isinstance(value, dict) and value.get('kind') == DECISION_KIND, 'decision_kind')
    need(value.get('selection_sha256') == public['selection']['sha256']
         and value.get('selected_recordings') == public['selection']['recordings']
         and value.get('archived_with_verified_audio') == public['archived']
         and value.get('final_download_failures') == public['outstanding'], 'decision_counts')
    categories = value.get('failure_categories')
    need(isinstance(categories, dict) and set(categories) <= set(REASONS)
         and all(whole(count) for count in categories.values())
         and sum(categories.values()) == public['outstanding']
         and {REASONS[key]: count for key, count in categories.items()} == public['failure_labels'], 'decision_reasons')
    bound = value.get('bound_to') or {}
    need(bound.get('published_failed_links_csv_sha256') in {public['failed_links_sha256'], public['failed_links_crlf_sha256']},
         'decision_binding')
    # The decision's categories are checked against the public table above; what is published of them is decided by
    # the creators behind each category (public['by_reason']), not copied from the decision.
    return {'closed_at_utc': utc(value.get('decided_at_utc')), 'decision_record_sha256': hashlib.sha256(raw).hexdigest()}


def build(public, decision):
    transcription = dict(public['transcription'])
    instants = [decision['closed_at_utc'], public['drive']['finished_at_utc'], transcription['finished_at_utc']]
    downloads = {
        'state': 'closed', 'closed_by': 'owner', 'closed_at_utc': decision['closed_at_utc'], 'retried': False,
        'archived_with_verified_audio': public['archived'], 'final_failures': public['outstanding'],
    }
    # a breakdown is published only where every category holds 5 or more creators after pooling (None: the total only)
    if public['by_reason'] is not None:
        downloads['final_failures_by_reason'] = public['by_reason']
    if public['by_source'] is not None:
        downloads['archived_by_source'] = public['by_source']
    downloads.update({
        'creators_complete': public['complete_creators'],
        'receipt_checkpoint_utc': public['receipt_checkpoint_utc'], 'drive_verification': public['drive'],
        'decision_record_sha256': decision['decision_record_sha256'],
        'failed_links_csv_sha256': public['failed_links_sha256'],
    })
    return {
        'schema_version': 1, 'scope': SCOPE, 'as_of_utc': max(instants),
        'selection': {**public['selection'], 'label': "Newest 20 public uploads on each creator's Videos tab"},
        'downloads': downloads,
        'transcription': transcription,
        'evidence': {'close': 'knowledge-transfer/evidence/2026-11-20-close/',
                     'transcription_tables': 'research/transcription-run-2026-11-20/tables/',
                     'analysis_handoff': 'knowledge-transfer/analysis-handoff-2026-11-20.md'},
    }


def check(state, public):
    """Confirm that a published state agrees with the committed public evidence (the decision itself stays private)."""
    need(state.get('schema_version') == 1 and state.get('scope') == SCOPE, 'state_schema')
    downloads = state['downloads']
    sha(downloads['decision_record_sha256'])
    closed = utc(downloads['closed_at_utc'])
    expected = build(public, {'closed_at_utc': closed, 'decision_record_sha256': downloads['decision_record_sha256']})
    need(state == expected, 'state_drift')
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--decision', type=Path, help="The owner's private decision record that closed the download goal")
    mode.add_argument('--check', type=Path, help='A published state file to validate against the public evidence')
    parser.add_argument('--out', type=Path, help='Where to write the state (with --decision)')
    parser.add_argument('--close', type=Path, default=CLOSE)
    parser.add_argument('--tables', type=Path, default=RUN_TABLES)
    parser.add_argument('--progress', type=Path, default=PROGRESS)
    args = parser.parse_args(argv)
    try:
        public = public_facts(args.close, args.tables, args.progress)
        if args.check:
            check(read_json(args.check), public)
            print(json.dumps({'state': 'consistent', 'file': args.check.name}))
            return 0
        if args.out is None:
            parser.error('--out is required with --decision')
        state = build(public, decision_facts(args.decision.read_bytes(), public))
    except (OSError, ValueError, KeyError, TypeError) as error:
        # The message names the failed check only; no input contents are printed.
        raise SystemExit('Collection state refused: ' + (error.args[0] if isinstance(error, ValueError) and error.args
                                                         and isinstance(error.args[0], str) and re.fullmatch(r'[a-z0-9_]+', error.args[0])
                                                         else type(error).__name__))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + '.tmp')
    temporary.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    temporary.replace(args.out)
    print(json.dumps({'wrote': args.out.name, 'as_of_utc': state['as_of_utc']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
