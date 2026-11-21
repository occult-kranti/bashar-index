import contextlib
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import public_disclosure_scan as scan  # noqa: E402


class SmallCellTests(unittest.TestCase):
    def test_counts_under_five_and_language_rows_are_found_and_zero_is_not(self):
        header = ['language', 'scope', 'audio_files', 'creators', 'hours']
        rows = [['English', 'language', '1616', '95', '716.5'], ['Finnish', 'language', '1', '1', ''],
                ['All other languages', 'pooled', '81', '6', '26.4'], ['Nothing', 'band', '0', '0', '']]
        found = scan.table_cells(header, rows)
        self.assertEqual(found['language_row'], 1)
        self.assertEqual(found['count_under_5'], 2)

    def test_markdown_tables_and_language_pairs(self):
        text = ('Intro\n\n| Measure | Recordings |\n|---|---|\n| A | 3 |\n| B | 300 |\n\n'
                '| Time | Languages |\n|---|---|\n| 06:09 | en 272, ja 4, es 3 |\n')
        found = scan.small_cells(Path('x.md'), text)
        self.assertEqual(found['count_under_5'], 1)
        self.assertEqual(found['language_pair'], 2)

    def test_json_is_walked_by_key(self):
        value = {'transcription': {'languages': [{'language': 'English', 'audio_files': 1616}, {'language': 'Czech', 'audio_files': 5}]},
                 'bins': [{'creators': 2}, {'creators': 7}], 'schema_version': 1}
        found = scan.small_cells(Path('state.json'), json.dumps(value))
        self.assertEqual(found['language_row'], 1)
        self.assertEqual(found['count_under_5'], 1)

    def test_pooled_tables_pass(self):
        text = ('language,scope,recordings,creators,hours\nEnglish,language,1618,95,716.5\n'
                'All other languages,pooled,81,6,26.4\n')
        self.assertEqual(scan.small_cells(Path('languages.csv'), text), {})


class StrengthenedSmallCellTests(unittest.TestCase):
    """The rules added after the verifier's findings of 2026-11-21 (follow-up of D7)."""

    def test_numeric_leaves_of_count_by_category_dictionaries_are_counts_whatever_their_keys(self):
        value = {'downloads': {'final_failures': 30,
                               'final_failures_by_reason': {'provider_refusal_http_403': 29, 'metadata_lookup_failure': 1},
                               'archived_by_source': {'youtube_native': 1304, 'publisher_edition': 178},
                               'outcome_counts': {'kept': {'deep': 3}}, 'schema_version': 1, 'language_count': 2}}
        found = scan.small_cells(Path('collection_state.json'), json.dumps(value))
        self.assertEqual(found['count_under_5'], 2)          # the 1 under by_reason and the 3 nested under _counts
        self.assertEqual(scan.small_cells(Path('state.json'), json.dumps({'final_failures': 30, 'archived_by_source': {'a': 1304}})), {})

    def test_progress_table_columns_named_in_words_with_n_of_m_cells(self):
        text = ('| Time (UTC) | Audio files done | Audio hours done | Held | Without speech (hours) | Languages found |\n'
                '|---|---|---|---|---|---|\n'
                '| 2026-11-20 06:09 | 3 of 1,729 | 1.2 of 746.3 | 4 | 2.0 | 2 languages |\n'
                '| 2026-11-20 19:56 | 1,697 of 1,729 | 742.9 of 746.3 | 32 | 3.0 | 7 languages |\n')
        found = scan.small_cells(Path('progress.md'), text)
        self.assertEqual(found['count_under_5'], 2)          # 3 audio files done and 4 held; hours and languages are not counts
        self.assertNotIn('unit_pair', found)                 # one unit: audio files, as the table counted during the run
        both = text.replace('| Held |', '| Recordings done |')
        self.assertEqual(scan.small_cells(Path('progress.md'), both)['unit_pair'], 1)

    def test_measure_value_tables_count_measures_that_name_recordings(self):
        text = ('measure,value\nRecordings selected,1976\nRecordings with a damaged packet passed over,2\n'
                'Hours transcribed,3.0\nMedian recording length minutes,4\nAudio files transcribed,1697\n'
                'Audio files in the run,1729\nRecordings not transcribed,32\n')
        found = scan.small_cells(Path('summary.csv'), text)
        self.assertEqual(found['count_under_5'], 1)
        self.assertNotIn('unit_pair', found)                 # each measure in one unit
        both = text + 'Recordings in the run,1731\nRecordings transcribed,1699\n'
        self.assertEqual(scan.small_cells(Path('summary.csv'), both)['unit_pair'], 2)

    def test_a_count_in_both_units_is_found_in_json_and_prose(self):
        state = {'transcription': {'audio_files': 1729, 'audio_files_transcribed': 1697, 'not_transcribed': 32,
                                   'languages': [{'language': 'English', 'audio_files': 1616}]}, 'selection': {'recordings': 1976}}
        self.assertNotIn('unit_pair', scan.small_cells(Path('collection_state.json'), json.dumps(state)))
        state['transcription'].update({'recordings': 1731, 'recordings_transcribed': 1699})
        self.assertEqual(scan.small_cells(Path('collection_state.json'), json.dumps(state))['unit_pair'], 2)
        flagged = ['The distributions count each audio file once, so 1,697 audio files stand for 1,699 recordings.',
                   'Done: 1,697 of 1,729 audio files (1,731 recordings in the run).']
        for text in flagged:
            with self.subTest(text=text[:30]):
                self.assertEqual(scan.small_cells(Path('notes.md'), text)['unit_pair'], 1)
        passed = ['The run finished: 1,697 of 1,729 audio files, 742.9 hours. 1,946 of the 1,976 selected recordings are archived.',
                  'Speech-to-text of the archived recordings: 1,729 audio files, 746.3 hours; the 30 recordings whose audio could not be downloaded are not part of it.']
        for text in passed:
            with self.subTest(text=text[:30]):
                self.assertNotIn('unit_pair', scan.small_cells(Path('notes.md'), text))

    def test_small_counts_in_prose_next_to_a_group_word(self):
        flagged = ['The distributions count each audio file once: two files are each shared by two recordings.',
                   'One row per vendor, including 2 hold-out transcripts until freeze 2.',
                   'The pooled row holds 4 Japanese recordings.', 'Of these, 3 recordings failed their metadata lookup.']
        for text in flagged:
            with self.subTest(text=text[:30]):
                self.assertGreaterEqual(scan.small_cells(Path('notes.md'), text)['prose_count_under_5'], 1)
        passed = ['Each is a contrast inside one recording or one creator; the other eight have not run.',
                  'Every language spoken by fewer than 5 creators is pooled; 17 hold-out creators were tested.',
                  'The two recognizer models agree on 36 English recordings, one per creator.',
                  'A percentile over the recordings of fewer than 5 creators would be their lengths.',
                  'Speech is thinnest in the first 3 minutes; 2 rows of the table are pooled.']
        for text in passed:
            with self.subTest(text=text[:30]):
                self.assertNotIn('prose_count_under_5', scan.small_cells(Path('notes.md'), text))

    def test_languages_other_than_english_with_a_number_in_prose(self):
        text = 'The run found seven languages: English 1,616 audio files, Japanese 30, Spanish 19, Finnish: 1.'
        self.assertEqual(scan.small_cells(Path('ROADMAP.md'), text)['language_pair'], 3)
        self.assertNotIn('language_pair', scan.small_cells(Path('ROADMAP.md'), 'English and six other languages, pooled: 81.'))

    def test_the_scan_prints_counts_only(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:   # git's read-only objects on Windows
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            secret = 'Spanish channel of Private Person, 2 hold-out recordings, video AAAAAAAAAA1'
            (root / 'notes.md').write_text(secret + '\n\n| Language | Recordings |\n|---|---|\n| Spanish | 3 |\n', encoding='utf-8')
            subprocess.run(['git', '-C', str(root), 'add', 'notes.md'], check=True)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = scan.main(['--root', str(root), '--files'])
            self.assertEqual(code, 0)
            printed = output.getvalue()
            self.assertIn('prose_count_under_5', printed)
            for value in ('Spanish', 'Private Person', 'AAAAAAAAAA1', 'hold-out recordings'):
                self.assertNotIn(value, printed)


class ForbiddenStringTests(unittest.TestCase):
    def test_names_ids_and_seen_titles_are_counted_and_hold_out_titles_are_not_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'sets.json').write_text(json.dumps({'seen_creators': ['alpha-creator'], 'holdout_creators': ['beta-person'],
                                                        'other_creators': []}), encoding='utf-8')
            (root / 'proposal.json').write_text(json.dumps({'rows': [{'video_id': 'AAAAAAAAAA1'}, {'video_id': 'BBBBBBBBBB2'}]}), encoding='utf-8')
            with open(root / 'catalogue.csv', 'w', encoding='utf-8', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(['video_id', 'channel_dir', 'creator', 'title'])
                writer.writerow(["'AAAAAAAAAA1", 'alpha-creator', 'Alpha Creator', 'A long seen title about the stars'])
                writer.writerow(['BBBBBBBBBB2', 'beta-person', 'Beta Person', 'A long hold-out title never read'])
            forbidden = scan.Forbidden(root / 'sets.json', root / 'proposal.json', root / 'catalogue.csv')
            self.assertEqual(len(forbidden.titles), 1)
            text = 'Alpha Creator said: "A long seen title about the stars" (AAAAAAAAAA1); see beta-person and BBBBBBBBBB2.'
            found = forbidden.count(text)
            self.assertEqual(found['video_id'], 2)
            self.assertEqual(found['title'], 1)
            self.assertGreaterEqual(found['creator_name'], 2)
            self.assertEqual(forbidden.count('A long hold-out title never read'), {})


class RunOutputTests(unittest.TestCase):
    def test_the_published_run_outputs_hold_no_cell_of_fewer_than_five_creators(self):
        report = scan.scan(scan.ROOT, only=scan.RUN_OUTPUTS)
        small = {name: found for name, found in report.items() if any(kind in found for kind in scan.SMALL_KINDS)}
        self.assertEqual(small, {})


if __name__ == '__main__':
    unittest.main()
