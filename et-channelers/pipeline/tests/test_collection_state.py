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
FAILED_ROW = 'https://www.youtube.com/watch?v=PRIVATEVID1,Private Creator,Private title,4,PRIVATEVID1,Provider refusal,403\n'


def fixture(root):
    """A two-creator selection: three recordings archived, one final failure, a finished run."""
    close, tables = root / 'close', root / 'tables'
    (close / 'failed-links').mkdir(parents=True)
    tables.mkdir()
    (close / 'checkpoint.json').write_text(json.dumps({
        'as_of_utc': '2026-11-20T01:16:52Z', 'selection_sha256': SELECTION, 'selected_recordings': 4,
        'selected_creators': 2, 'verified_audio': 3, 'complete_creators': 1,
        'selection_dispositions': {'verified_audio_receipt': 3, 'current_source_refusal': 1}}), encoding='utf-8')
    (close / 'drive-verification.json').write_text(json.dumps({
        'schema_version': 1, 'selection_sha256': SELECTION, 'selected_recordings': 4, 'selected_creators': 2,
        'recordings_with_prior_verified_receipts': 3, 'recordings_with_all_required_drive_objects_matching': 3,
        'recordings_with_discrepancies': 0, 'outstanding_without_a_verified_recording': 1,
        'drive_metadata_finished_utc': '2026-11-20T01:56:31Z'}), encoding='utf-8')
    (close / 'recording-status.csv').write_text(
        '﻿creator,creator_key,video_id,url,checkpoint_disposition,verified_audio,distinct_attempt_evidence\n'
        'Creator A,creator-a,AAAAAAAAAA1,u,verified_audio_receipt,youtube_native,1\n'
        'Creator A,creator-a,AAAAAAAAAA2,u,verified_audio_receipt,publisher_edition,1\n'
        'Private Creator,creator-b,BBBBBBBBBB1,u,verified_audio_receipt,youtube_track_unverified,2\n'
        'Private Creator,creator-b,PRIVATEVID1,u,current_source_refusal,,1\n', encoding='utf-8')
    failed = (FAILED_HEADER + FAILED_ROW).encode('utf-8')
    (close / 'failed-links' / 'failed-links.csv').write_bytes(failed)
    (tables / 'summary.csv').write_text(
        'measure,value\nRecordings selected,4\nAudio files in the run,3\nAudio files transcribed,2\n'
        'Hours transcribed,1.5\nRecordings not transcribed,1\nHours without speech,0.2\n'
        'Share of hours without speech,0.133\nWords transcribed,900\n', encoding='utf-8')
    (tables / 'languages.csv').write_text('language,audio_files,hours\nJapanese,1,0.5\nEnglish,1,1.0\n', encoding='utf-8')
    progress = root / 'progress.md'
    progress.write_text('| Time (UTC) | Audio files done | Audio hours done | Held |\n|---|---|---|---|\n'
                        '| 2026-11-20 16:18 | 1 of 3 | 1.0 of 1.7 | 1 | 0.1 | en 1 | 60.6x | 2026-11-20 21:25 |\n'
                        '| 2026-11-20 19:56 | 2 of 3 | 1.5 of 1.7 | 1 | 0.2 | en 1, ja 1 | 58.8x | finished |\n',
                        encoding='utf-8')
    decision = {'kind': 'owner_decision_download_goal_closed', 'decided_at_utc': '2026-11-20T04:57:21Z',
                'decision': 'PRIVATE DECISION TEXT', 'owner_words': 'PRIVATE OWNER WORDS',
                'selection_sha256': SELECTION, 'selected_recordings': 4, 'archived_with_verified_audio': 3,
                'final_download_failures': 1, 'failure_categories': {'provider_refusal_http_403': 1},
                'failed_recordings': [{'video_id': 'PRIVATEVID1', 'creator': 'Private Creator'}],
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
        self.assertEqual((state['downloads']['archived_with_verified_audio'], state['downloads']['final_failures']), (3, 1))
        self.assertEqual(state['downloads']['final_failures_by_reason'], {'provider_refusal_http_403': 1})
        self.assertEqual(state['downloads']['archived_by_source'],
                         {'youtube_native': 1, 'youtube_track_unverified': 1, 'publisher_edition': 1})
        self.assertEqual(state['downloads']['creators_complete'], 1)
        self.assertFalse(state['downloads']['retried'])
        self.assertEqual(state['transcription']['finished_at_utc'], '2026-11-20T19:56:00Z')
        self.assertEqual((state['transcription']['audio_files_transcribed'], state['transcription']['hours']), (2, 1.7))
        self.assertEqual([row['audio_files'] for row in state['transcription']['languages']], [1, 1])
        self.assertEqual(state['as_of_utc'], '2026-11-20T19:56:00Z')
        serialized = json.dumps(state)
        for private in ('PRIVATEVID1', 'Private Creator', 'PRIVATE', 'Creator A', 'AAAAAAAAAA1', 'b' * 64):
            self.assertNotIn(private, serialized)
        self.assertTrue(collection_state.check(state, self.public()))

    def test_decision_must_match_the_selection_counts_reasons_and_failed_links_hash(self):
        changes = {'decision_kind': {'kind': 'other'}, 'decision_counts': {'selection_sha256': 'c' * 64},
                   'decision_reasons': {'failure_categories': {'metadata_lookup_failure': 1}},
                   'decision_binding': {'bound_to': {'published_failed_links_csv_sha256': 'd' * 64}}}
        for reason, change in changes.items():
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                self.build({**self.decision, **change})
        with self.assertRaisesRegex(ValueError, 'decision_counts'):
            self.build({**self.decision, 'archived_with_verified_audio': 4, 'final_download_failures': 0})

    def test_public_evidence_must_agree_before_anything_is_written(self):
        drive = json.loads((self.close / 'drive-verification.json').read_text(encoding='utf-8'))
        (self.close / 'drive-verification.json').write_text(json.dumps({**drive, 'recordings_with_discrepancies': 1}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'drive_verification'):
            self.public()
        (self.close / 'drive-verification.json').write_text(json.dumps(drive), encoding='utf-8')
        text = self.progress.read_text(encoding='utf-8')
        self.progress.write_text(text.replace('2 of 3', '3 of 3'), encoding='utf-8')
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
        self.assertIn('29 refused by the media provider with HTTP 403 and 1 failed its metadata lookup',
                      closed['values']['cc-current-explanation'])
        self.assertEqual((closed['values']['cc-verified'], closed['values']['cc-awaiting'], closed['values']['cc-channels'],
                          closed['values']['cc-indexed']), ('1,946', '30', '101', '1,697'))
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
