import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import collection_state  # noqa: E402
import dashboard_local  # noqa: E402

SELECTION = 'a' * 64
FAILED_HEADER = 'Video URL,Creator,Video title,Newest rank,Video ID,Failure category,HTTP status\n'
CREATORS = [f'creator-{index:02d}' for index in range(1, 13)]          # twelve creators
# Creators 7 to 12 each have one final failure: five refused by the provider, one failed metadata lookup (one creator)
FAILURES = {key: ('Metadata lookup failure' if key == 'creator-12' else 'Provider refusal') for key in CREATORS[6:]}


def failed_id(key):
    return 'PRIVATEV' + key[-2:] + 'F'


def failed_links():
    rows = ''.join(f'https://www.youtube.com/watch?v={failed_id(key)},Private Creator {key[-2:]},Private title,4,{failed_id(key)},{label},403\n'
                   for key, label in FAILURES.items())
    return (FAILED_HEADER + rows).encode('utf-8')


def fixture(root):
    """Twelve creators, 36 selected recordings: 30 archived (every creator has a native and a track recording, creators
    1 to 6 a publisher edition too), six final failures of six creators (one reason held by one creator), a finished run
    of 10 recordings, nine transcribed."""
    close, tables = root / 'close', root / 'tables'
    (close / 'failed-links').mkdir(parents=True)
    tables.mkdir()
    (close / 'checkpoint.json').write_text(json.dumps({
        'as_of_utc': '2026-11-20T01:16:52Z', 'selection_sha256': SELECTION, 'selected_recordings': 36,
        'selected_creators': 12, 'verified_audio': 30, 'complete_creators': 6,
        'selection_dispositions': {'verified_audio_receipt': 30, 'current_source_refusal': 5, 'metadata_lookup_failure': 1}}),
        encoding='utf-8')
    (close / 'drive-verification.json').write_text(json.dumps({
        'schema_version': 1, 'selection_sha256': SELECTION, 'selected_recordings': 36, 'selected_creators': 12,
        'recordings_with_prior_verified_receipts': 30, 'recordings_with_all_required_drive_objects_matching': 30,
        'recordings_with_discrepancies': 0, 'outstanding_without_a_verified_recording': 6,
        'drive_metadata_finished_utc': '2026-11-20T01:56:31Z'}), encoding='utf-8')
    lines = ['﻿creator,creator_key,video_id,url,checkpoint_disposition,verified_audio,distinct_attempt_evidence\n']
    for number, key in enumerate(CREATORS, 1):
        sources = ['youtube_native', 'youtube_track_unverified'] + (['publisher_edition'] if number <= 6 else [])
        lines += [f'Creator {number},{key},VID{number:02d}{index}XXXXX,u,verified_audio_receipt,{source},1\n'
                  for index, source in enumerate(sources)]
        if key in FAILURES:
            disposition = 'metadata_lookup_failure' if FAILURES[key] == 'Metadata lookup failure' else 'current_source_refusal'
            lines.append(f'Private Creator {key[-2:]},{key},{failed_id(key)},u,{disposition},,1\n')
    (close / 'recording-status.csv').write_text(''.join(lines), encoding='utf-8')
    failed = failed_links()
    (close / 'failed-links' / 'failed-links.csv').write_bytes(failed)
    (tables / 'summary.csv').write_text(
        'measure,value\nRecordings selected,36\nAudio files in the run,10\nAudio files transcribed,9\n'
        'Hours transcribed,1.5\nRecordings not transcribed,1\nHours without speech,0.2\n'
        'Share of hours without speech,0.133\nWords transcribed,900\nLanguages found,3\n', encoding='utf-8')
    # since 2026-11-21 no language row describes fewer than 5 creators: English and one pooled row (D7), in audio files
    (tables / 'languages.csv').write_text('language,scope,audio_files,creators\nEnglish,language,6,5\n'
                                          'All other languages,pooled,3,5\n', encoding='utf-8')
    progress = root / 'progress.md'
    progress.write_text('| Time (UTC) | Audio files done | Audio hours done | Without speech (hours) |\n|---|---|---|---|\n'
                        '| 2026-11-20 16:18 | 5 of 10 | 1.0 of 1.7 | 0.1 | 2 languages | 60.6x | 2026-11-20 21:25 |\n'
                        '| 2026-11-20 19:56 | 9 of 10 | 1.5 of 1.7 | 0.2 | 3 languages | 58.8x | finished |\n',
                        encoding='utf-8')
    decision = {'kind': 'owner_decision_download_goal_closed', 'decided_at_utc': '2026-11-20T04:57:21Z',
                'decision': 'PRIVATE DECISION TEXT', 'owner_words': 'PRIVATE OWNER WORDS',
                'selection_sha256': SELECTION, 'selected_recordings': 36, 'archived_with_verified_audio': 30,
                'final_download_failures': 6, 'failure_categories': {'provider_refusal_http_403': 5, 'metadata_lookup_failure': 1},
                'failed_recordings': [{'video_id': failed_id(key), 'creator': 'Private Creator'} for key in FAILURES],
                'bound_to': {'published_failed_links_csv_sha256': hashlib.sha256(failed).hexdigest(),
                             'download_pause_record_sha256': 'b' * 64},
                'unchanged': ['PRIVATE PATH']}
    return close, tables, progress, decision


class CollectionStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.close, self.tables, self.progress, self.decision = fixture(self.root)

    def tearDown(self):
        self.directory.cleanup()

    def public(self):
        return collection_state.public_facts(self.close, self.tables, self.progress)

    def build(self, decision=None):
        raw = json.dumps(decision or self.decision).encode('utf-8')
        public = self.public()
        return collection_state.build(public, collection_state.decision_facts(raw, public))

    def test_closed_state_joins_the_decision_with_public_evidence_and_copies_no_private_value(self):
        state = self.build()
        self.assertEqual(state['downloads']['state'], 'closed')
        self.assertEqual((state['downloads']['archived_with_verified_audio'], state['downloads']['final_failures']), (30, 6))
        # one reason is held by one creator: pooled, "other" would still hold fewer than 5 creators, so the total only
        self.assertNotIn('final_failures_by_reason', state['downloads'])
        self.assertEqual(state['downloads']['archived_by_source'],
                         {'youtube_native': 12, 'youtube_track_unverified': 12, 'publisher_edition': 6})
        self.assertEqual(state['downloads']['creators_complete'], 6)
        self.assertFalse(state['downloads']['retried'])
        self.assertEqual(state['transcription']['finished_at_utc'], '2026-11-20T19:56:00Z')
        self.assertEqual((state['transcription']['audio_files'], state['transcription']['audio_files_transcribed'],
                          state['transcription']['hours']), (10, 9, 1.7))
        self.assertEqual([row['audio_files'] for row in state['transcription']['languages']], [6, 3])
        self.assertEqual(state['transcription']['language_count'], 3)
        self.assertEqual({row['language'] for row in state['transcription']['languages']}, {'English', 'All other languages'})
        # ledger fields only: no word count and no time without speech of the whole run (transcript and timing measures)
        self.assertFalse({'words', 'hours_without_speech', 'share_without_speech'} & set(state['transcription']))
        self.assertEqual(state['as_of_utc'], '2026-11-20T19:56:00Z')
        serialized = json.dumps(state)
        for private in ('PRIVATEV', 'Private Creator', 'PRIVATE', 'Creator 1', 'VID010XXXXX', 'creator-', 'b' * 64, 'recordings_transcribed'):
            self.assertNotIn(private, serialized)
        self.assertTrue(collection_state.check(state, self.public()))

    def test_categories_of_fewer_than_five_creators_are_pooled_or_only_the_total_is_given(self):
        pool = collection_state.pool_by_creators
        who = lambda *names: set(names)
        self.assertIsNone(pool({'refusal': (29, set(range(20))), 'metadata': (1, who('x'))}))
        self.assertEqual(pool({'a': (100, set(range(12))), 'b': (50, set(range(20, 30))), 'c': (5, who('p', 'q')), 'd': (4, who('p', 'r'))}),
                         {'a': 100, 'other': 59})          # c and d hold 3 creators, so the smaller remaining b joins them
        self.assertEqual(pool({'a': (9, set(range(6))), 'b': (8, set(range(6, 12))), 'c': (3, who(1, 2)), 'd': (2, who(3, 4, 5))}),
                         {'a': 9, 'b': 8, 'other': 5})     # c and d together hold 5 creators
        self.assertEqual(pool({'a': (9, set(range(6))), 'b': (7, set(range(5)))}), {'a': 9, 'b': 7})
        self.assertIsNone(pool({'a': (3, who(1, 2)), 'b': (2, who(3))}))
        # a source held by fewer than 5 creators is pooled in the published state
        rows = (self.close / 'recording-status.csv').read_text(encoding='utf-8')
        kept = [line for line in rows.splitlines(True) if 'publisher_edition' not in line or line.startswith(('Creator 1,', 'Creator 2,'))]
        dropped = len(rows.splitlines()) - len(kept)
        (self.close / 'recording-status.csv').write_text(''.join(kept), encoding='utf-8')
        for name in ('checkpoint.json', 'drive-verification.json'):
            value = json.loads((self.close / name).read_text(encoding='utf-8'))
            for key in ('selected_recordings', 'verified_audio', 'recordings_with_prior_verified_receipts',
                        'recordings_with_all_required_drive_objects_matching'):
                if key in value:
                    value[key] -= dropped
            if 'selection_dispositions' in value:
                value['selection_dispositions']['verified_audio_receipt'] -= dropped
            (self.close / name).write_text(json.dumps(value), encoding='utf-8')
        summary = (self.tables / 'summary.csv').read_text(encoding='utf-8').replace('Recordings selected,36', f'Recordings selected,{36 - dropped}')
        (self.tables / 'summary.csv').write_text(summary, encoding='utf-8')
        public = self.public()
        # the publisher source (2 creators) is pooled; "other" still holds fewer than 5 creators, so the remaining source
        # with the fewest creators joins it (here a tie of 12, broken by order: the native source)
        self.assertEqual(public['by_source'], {'youtube_track_unverified': 12, 'other': 14})

    def test_the_run_is_counted_in_audio_files_and_never_beside_a_count_of_recordings(self):
        path = self.tables / 'summary.csv'
        path.write_text(path.read_text(encoding='utf-8') + 'Recordings in the run,10\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'run_units'):
            self.public()

    def test_final_failures_of_fewer_than_five_creators_are_refused(self):
        path = self.close / 'recording-status.csv'
        lines = path.read_text(encoding='utf-8').splitlines(True)
        # move two failures onto creators that already have one: six failures of four creators
        moved = [line.replace('creator-07', 'creator-08').replace('creator-09', 'creator-10') if line.startswith('Private Creator')
                 else line for line in lines]
        path.write_text(''.join(moved), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'final_failure_creators'):
            self.public()

    def test_decision_must_match_the_selection_counts_reasons_and_failed_links_hash(self):
        changes = {'decision_kind': {'kind': 'other'}, 'decision_counts': {'selection_sha256': 'c' * 64},
                   'decision_reasons': {'failure_categories': {'metadata_lookup_failure': 6}},
                   'decision_binding': {'bound_to': {'published_failed_links_csv_sha256': 'd' * 64}}}
        for reason, change in changes.items():
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                self.build({**self.decision, **change})
        with self.assertRaisesRegex(ValueError, 'decision_counts'):
            self.build({**self.decision, 'archived_with_verified_audio': 31, 'final_download_failures': 5})

    def test_failed_links_hash_does_not_depend_on_line_ends(self):
        lf = self.public()['failed_links_sha256']
        path = self.close / 'failed-links' / 'failed-links.csv'
        path.write_bytes(path.read_bytes().replace(b'\n', b'\r\n'))
        crlf_public = self.public()
        self.assertEqual(crlf_public['failed_links_sha256'], lf)
        crlf = hashlib.sha256(failed_links().replace(b'\n', b'\r\n')).hexdigest()
        for bound in (lf, crlf):
            with self.subTest(bound=bound[:8]):
                self.build({**self.decision, 'bound_to': {**self.decision['bound_to'],
                                                          'published_failed_links_csv_sha256': bound}})

    def test_public_evidence_must_agree_before_anything_is_written(self):
        drive = json.loads((self.close / 'drive-verification.json').read_text(encoding='utf-8'))
        (self.close / 'drive-verification.json').write_text(json.dumps({**drive, 'recordings_with_discrepancies': 1}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'drive_verification'):
            self.public()
        (self.close / 'drive-verification.json').write_text(json.dumps(drive), encoding='utf-8')
        text = self.progress.read_text(encoding='utf-8')
        self.progress.write_text(text.replace('9 of 10', '10 of 10'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'progress_matches_tables'):
            self.public()
        self.progress.write_text(text.replace('| finished |', '| 2026-11-20 21:00 |'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'progress_finished_row'):
            self.public()

    def test_check_reports_drift_in_a_published_state(self):
        state = self.build()
        state['downloads']['final_failures'] = 0
        with self.assertRaisesRegex(ValueError, 'state_drift'):
            collection_state.check(state, self.public())

    def test_cli_writes_the_state_and_refuses_without_printing_inputs(self):
        decision, out = self.root / 'decision.json', self.root / 'plan' / 'collection_state.json'
        decision.write_text(json.dumps(self.decision), encoding='utf-8')
        script = str(Path(collection_state.__file__))
        common = ['--close', str(self.close), '--tables', str(self.tables), '--progress', str(self.progress)]
        done = subprocess.run([sys.executable, '-I', script, '--decision', str(decision), '--out', str(out), *common],
                              capture_output=True, text=True, timeout=30, cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(out.read_text(encoding='utf-8')), self.build())
        checked = subprocess.run([sys.executable, '-I', script, '--check', str(out), *common],
                                 capture_output=True, text=True, timeout=30, cwd=self.root)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        decision.write_text(json.dumps({**self.decision, 'selected_recordings': 5}), encoding='utf-8')
        refused = subprocess.run([sys.executable, '-I', script, '--decision', str(decision), '--out', str(out), *common],
                                 capture_output=True, text=True, timeout=30, cwd=self.root)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('decision_counts', refused.stderr)
        self.assertNotIn('PRIVATE', refused.stdout + refused.stderr)


RENDER_HARNESS = """
const values = {}; const elements = {};
const element = (id) => elements[id] || (elements[id] = {id, dataset: {}, hidden: true, open: true, children: [],
  setAttribute() {}, append(...items) { this.children.push(...items); }, replaceChildren() { this.children = []; }});
const document = {getElementById: element, createElement: () => element('child-' + Object.keys(elements).length)};
const put = (id, value) => { values[id] = value; };
const number = (value) => Number.isFinite(+value) ? (+value).toLocaleString('en-US') : '—';
const date = String; const BASE = '';
const fetch = async () => ({ok: true, json: async () => STATE});
"""


class CollectionStateRendererTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is needed for the dashboard renderer fixture')
    def test_dashboard_states_the_close_and_the_finished_run_from_the_record(self):
        prefix = '  async function collectionClosure(statusSnapshot, coverage) {'
        renderer = prefix + dashboard_local.HEAD.split(prefix, 1)[1].split('  const loadCollection = ', 1)[0]
        state = json.loads((collection_state.ROOT / 'plan' / 'collection_state.json').read_text(encoding='utf-8'))
        broken = json.loads(json.dumps(state))
        broken['downloads']['final_failures'] += 1
        results = {}
        for name, value in (('closed', state), ('broken', broken)):
            script = ('const STATE = ' + json.dumps(value) + ';\n' + RENDER_HARNESS + renderer
                      + "\ncollectionClosure({generated_at: '2026-11-19T04:15:44Z', counts: {channels: 74}},"
                      + " {generated_at: '2026-11-19T04:15:44Z', channels: 74, target: 1420})"
                      + ".then(() => console.log(JSON.stringify({values, stages: element('cc-closure-stages').children.length,"
                      + " earlierOpen: element('cc-earlier').open, banner: element('cc-closure').hidden,"
                      + " pill: element('cc-current-state').dataset.state})));")
            done = subprocess.run([shutil.which('node'), '-e', script], capture_output=True, text=True, timeout=20)
            self.assertEqual(done.returncode, 0, done.stderr)
            results[name] = json.loads(done.stdout)
        closed = results['closed']
        self.assertEqual(closed['values']['cc-current-state'], 'Downloads closed')
        self.assertEqual(closed['pill'], 'closed')
        self.assertIn('1,946 of the 1,976 selected recordings from 101 channels', closed['values']['cc-closure-summary'])
        self.assertIn('final failures and are not retried', closed['values']['cc-closure-summary'])
        self.assertIn('finished the same day at 19:56 UTC: 1,697 of 1,729 audio files, 742.9 hours, in seven languages',
                      closed['values']['cc-closure-summary'])
        # one reason of the final failures is held by one creator: the record gives the total only, and so does the page
        self.assertNotIn('final failures,', closed['values']['cc-current-explanation'])
        self.assertNotIn('metadata', closed['values']['cc-current-explanation'])
        self.assertNotIn('recordings transcribed', (closed['values']['cc-closure-summary'] + closed['values']['cc-indexed-label']).lower())
        self.assertEqual((closed['values']['cc-verified'], closed['values']['cc-awaiting'], closed['values']['cc-channels'],
                          closed['values']['cc-indexed']), ('1,946', '30', '101', '1,697'))
        pooled = json.loads(json.dumps(state))
        pooled['downloads']['final_failures_by_reason'] = {'provider_refusal_http_403': 25, 'other': 5}
        script = ('const STATE = ' + json.dumps(pooled) + ';\n' + RENDER_HARNESS + renderer
                  + "\ncollectionClosure(null, null).then(() => console.log(JSON.stringify(values)));")
        done = subprocess.run([shutil.which('node'), '-e', script], capture_output=True, text=True, timeout=20)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('Of the 30 final failures, 25 refused by the media provider with HTTP 403 and 5 failed for other reasons',
                      json.loads(done.stdout)['cc-current-explanation'])
        self.assertEqual(closed['stages'], 3)
        self.assertFalse(closed['earlierOpen'])
        self.assertFalse(closed['banner'])
        self.assertIn('19 November 2026, 04:15 UTC', closed['values']['cc-earlier-summary'])
        broken = results['broken']
        self.assertEqual(broken['values']['cc-closure-heading'], 'Collection record unavailable')
        self.assertNotIn('cc-current-state', broken['values'])
        self.assertTrue(broken['earlierOpen'])


class PublishedCollectionStateTests(unittest.TestCase):
    def test_committed_state_agrees_with_the_committed_close_and_run_evidence(self):
        path = collection_state.ROOT / 'plan' / 'collection_state.json'
        state = json.loads(path.read_text(encoding='utf-8'))
        self.assertTrue(collection_state.check(state, collection_state.public_facts()))
        self.assertEqual(state['downloads']['archived_with_verified_audio'] + state['downloads']['final_failures'],
                         state['selection']['recordings'])


if __name__ == '__main__':
    unittest.main()
