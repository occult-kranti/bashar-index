"""Synthetic CPU lexical math and orchestration; no neural inference or CUDA."""
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from pipeline import corpus_group_lexical as lexical, corpus_semantic_retrieval as semantic
from pipeline import postrun_numerical_evidence as numerical
from pipeline.tests import test_corpus_group_lexical as lexical_fixtures


class NumericalEvidenceTests(unittest.TestCase):
    def setUp(self):
        fixture = lexical_fixtures.GroupLexicalTests('runTest'); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.row('aaaaaaaaaaa', 'creator-a', 'Galaxies and oceans.')
        fixture.row('bbbbbbbbbbb', 'creator-b', 'Oceans and stars.')
        fixture.row('ccccccccccc', 'creator-c', None)
        fixture.freeze()
        self.fixture, self.root = fixture, fixture.root
        self.ready = self.root/'research/project-text-agents/text-generation-ready.json'
        self.ready.parent.mkdir(parents=True)
        self.ready.write_bytes(numerical.encoded({'selection_sha256': fixture.selection,
            'generation': fixture.folder.relative_to(self.root).as_posix(),
            'manifest': numerical.artifact(self.root, fixture.folder/'manifest.json'),
            'view_inventory': numerical.artifact(self.root, fixture.folder/'view-inventory.json')}))
        self.lexical_calls = self.semantic_calls = 0

    def fake_lexical(self, *args, **kwargs):
        self.lexical_calls += 1
        data = lexical.load_inventory(self.root, self.fixture.folder, self.fixture.manifest_sha)
        result = lexical.assemble(data, backend='cpu_fixture', fixture_only=True)
        # Protocol fixture only: no production or GPU result is produced by this test.
        result['backend'] = {'name': 'cupy_cuda12x_csr_v1', 'fixture_backend_stub': True}
        raw = numerical.encoded(result)+b'\n'; sha = hashlib.sha256(raw).hexdigest()
        directory = self.root/'analysis/group_lexical'/sha; directory.mkdir(parents=True, exist_ok=True)
        (directory/'analysis.json').write_bytes(raw)
        (directory/'manifest.json').write_bytes(numerical.encoded({'revision': sha,
            'method': lexical.METHOD, 'postrun_manifest_sha256': self.fixture.manifest_sha,
            'analysis_sha256': sha, 'analysis_bytes': len(raw)}))
        return directory

    def fake_semantic(self, *args, **kwargs):
        self.semantic_calls += 1
        directory = self.root/'analysis/semantic_retrieval'/('f'*64)
        directory.mkdir(parents=True, exist_ok=True)
        contents = {'chunks.jsonl': b'{"chunk_id":"fixture-a"}\n{"chunk_id":"fixture-b"}\n',
            'ranked-passages.jsonl': b'{"fixture_numeric_candidate":true}\n', 'embeddings.f32': b'\0'*(2*384*4)}
        files = {}
        for name, raw in contents.items():
            (directory/name).write_bytes(raw)
            files[name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
        files['embeddings.f32']['shape'] = [2,384]
        (directory/'manifest.json').write_bytes(numerical.encoded({'revision': 'f'*64,
            'method': semantic.METHOD, 'postrun_manifest_sha256': self.fixture.manifest_sha,
            'model_manifest_sha256': 'e'*64, 'files': files,
            'backend': 'ctranslate2_cuda_float32_mean_pool_cupy_blocked_v1',
            'selected_recordings': 3, 'observed_primary_texts': 2, 'missing_primary_texts': ['ccccccccccc'],
            'unique_inference_chunks': 2, 'ranked_candidates': 1, 'top_k': 5,
            'max_sequence_length': 256, 'overlap_tokens': 64, 'model_revision': semantic.REVISION,
            'utilization_pacing': {'target': .70, 'fixture_backend_stub': True}}))
        return directory

    def services(self):
        stack = ExitStack()
        stack.enter_context(patch.object(numerical, '_storage'))
        stack.enter_context(patch.object(numerical, '_preflight'))
        stack.enter_context(patch.object(lexical, 'run', side_effect=self.fake_lexical))
        stack.enter_context(patch.object(semantic, 'run', side_effect=self.fake_semantic))
        return stack

    def run_numerical(self):
        return numerical.run(self.root, self.ready, model_manifest=self.root/'fixture-model.json', model_sha256='e'*64)

    def test_three_method_report_source_binding_missingness_and_idempotent_restart(self):
        with self.services():
            proof = self.run_numerical()
            report = json.loads(numerical.verified(self.root, proof).read_bytes())
            self.assertEqual(tuple(x['method'] for x in report['analyses']), numerical.METHODS)
            self.assertEqual(report['generation_manifest_sha256'], self.fixture.manifest_sha)
            self.assertEqual(report['selection_sha256'], self.fixture.selection)
            self.assertEqual([x['status'] for x in report['analyses']], ['measured']*3)
            summary = report['analyses'][0]['summary']
            self.assertEqual(summary['observed_primary_texts'], 2)
            self.assertEqual(summary['missing_primary_texts'], 1)
            self.assertEqual(summary['unassigned_claimed_source_recordings'], 3)
            for analysis in report['analyses']:
                numerical.verified(self.root, analysis['artifact'])
            self.assertLess(len(numerical.encoded(report)), 45000)
            self.assertNotIn(b'Galaxies', numerical.encoded(report))
            again = self.run_numerical()
            self.assertEqual(proof, again)
        self.assertEqual((self.lexical_calls, self.semantic_calls), (1,1))

    def test_transient_setup_hold_is_never_non_estimable_or_complete(self):
        with patch.object(numerical, '_storage'), patch.object(numerical, '_preflight', side_effect=numerical.NumericalHold('setup_pending')):
            with self.assertRaises(numerical.NumericalHold):
                self.run_numerical()
        self.assertFalse((self.ready.parent/'numerical-evidence.json').exists())
        holds = list((self.ready.parent/'numerical-runs').glob('*/hold.json'))
        self.assertEqual(len(holds), 1)
        self.assertTrue(json.loads(holds[0].read_bytes())['setup_failure_is_not_non_estimability'])

    def test_resume_after_later_stage_hold_reuses_completed_lexical_work(self):
        with self.services(), patch.object(semantic, 'run', side_effect=ModuleNotFoundError('fixture dependency missing')):
            with self.assertRaises(ModuleNotFoundError):
                self.run_numerical()
        with self.services():
            self.run_numerical()
        self.assertEqual((self.lexical_calls, self.semantic_calls), (1,1))

    def test_mutated_saved_result_fails_instead_of_recomputing_or_laundering(self):
        with self.services():
            proof = self.run_numerical()
            report = json.loads(numerical.verified(self.root, proof).read_bytes())
            path = numerical.within(self.root, report['analyses'][0]['artifact']['path'])
            path.write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'hash_changed'):
                self.run_numerical()
        self.assertEqual(self.lexical_calls, 1)

    def test_ready_generation_and_selection_tamper_rejected_before_compute(self):
        value = json.loads(self.ready.read_bytes())
        value['selection_sha256'] = '0'*64
        self.ready.write_bytes(numerical.encoded(value))
        with self.services(), self.assertRaisesRegex(ValueError, 'selection_or_inventory'):
            self.run_numerical()
        self.assertEqual((self.lexical_calls, self.semantic_calls), (0,0))

    def test_source_active_blocks_preflight_even_before_dependency_checks(self):
        path = self.root/'sync/analysis_resource_plan.json';path.parent.mkdir(exist_ok=True)
        path.write_bytes(numerical.encoded({'reservations': [{'state': 'active', 'lease_id': 'qualified_fixture'}]}))
        with self.assertRaisesRegex(numerical.NumericalHold, 'source_still_active'):
            numerical._preflight(self.root, None, None)

    def test_empty_semantic_text_has_specific_data_reason_not_setup_excuse(self):
        with self.services(), patch.object(semantic, 'run', side_effect=ValueError('no_nonempty_primary_text_chunks')):
            proof = self.run_numerical()
        report = json.loads(numerical.verified(self.root, proof).read_bytes())
        item = report['analyses'][-1]
        self.assertEqual(item['status'], 'not_estimable')
        self.assertEqual(item['summary']['reason'], 'no_nonempty_primary_English_text_chunks')

    def test_describe_opens_no_generation_or_model(self):
        with patch.object(numerical, 'run', side_effect=AssertionError('execution forbidden')):
            value = numerical.main(['--root', str(self.root), '--describe'])
        self.assertEqual(value['state'], 'dormant')
        self.assertFalse(value['GPU_initialized'])


if __name__ == '__main__':
    unittest.main()
