"""Offline setup protocol only: no package install, conversion or model calls."""
from contextlib import redirect_stdout
import hashlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import types
import unittest
from unittest.mock import patch

from pipeline import minilm_analysis_setup as setup


class MiniLMSetupTests(unittest.TestCase):
    def test_three_locked_binary_wheels_never_include_torch(self):
        self.assertEqual({r['distribution'] for r in setup.WHEELS}, {'ctranslate2','cupy-cuda12x','fastrlock'})
        self.assertEqual(sum(r['bytes'] for r in setup.WHEELS),110311087)
        for proof in setup.WHEELS:
            self.assertEqual(len(proof['sha256']),64)
            self.assertTrue(proof['filename'].endswith('cp310-cp310-win_amd64.whl'))
            self.assertTrue(proof['url'].startswith('https://files.pythonhosted.org/'))

    def test_exact_wheel_reuse_and_hash_mismatch_never_install(self):
        raw=b'invented binary wheel bytes, no executable payload'
        proof={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'url':'https://files.pythonhosted.org/fixture.whl'}
        with TemporaryDirectory() as temp:
            path=Path(temp)/'fixture.whl'
            calls=[]
            def opener(*args,**kwargs):
                calls.append(args);return io.BytesIO(raw)
            self.assertEqual(setup.fetch_wheel(path,proof,opener=opener),path)
            setup.fetch_wheel(path,proof,opener=lambda *a,**k: self.fail('unchanged wheel must not download'))
            self.assertEqual(len(calls),1)
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'existing_reviewed_wheel_changed'):
                setup.fetch_wheel(path,proof,opener=opener)

    def test_corrupt_or_oversized_download_never_becomes_installable_wheel(self):
        proof={'bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest(),'url':'https://files.pythonhosted.org/fixture.whl'}
        for value in (b'xyz',b'abcdef',b'ab'):
            with TemporaryDirectory() as temp:
                path=Path(temp)/'fixture.whl'
                with self.assertRaises(ValueError):
                    setup.fetch_wheel(path,proof,opener=lambda *a,**k:io.BytesIO(value))
                self.assertFalse(path.exists())

    def test_conversion_forward_guard_restores_original_even_on_failure(self):
        original=lambda *a,**k:'fixture original'
        module=types.SimpleNamespace(_call_impl=original)
        torch=types.SimpleNamespace(nn=types.SimpleNamespace(Module=module))
        with setup.no_torch_forward(torch):
            with self.assertRaisesRegex(ValueError,'CPU_neural_forward_forbidden'):
                module._call_impl()
        self.assertIs(module._call_impl,original)
        with self.assertRaises(RuntimeError):
            with setup.no_torch_forward(torch):
                raise RuntimeError('fixture conversion interrupted')
        self.assertIs(module._call_impl,original)

    def test_smoke_evidence_needs_tail_pooling_repeatability_and_finite_vectors(self):
        values=dict(finite=True,tail=True,pooling_error=1e-7,repeat_error=1e-6,
                    window_lengths=[256,98,8],runtime={'fixture_only':True},pacing={'target':.70})
        proof=setup.smoke_report(**values)
        self.assertEqual(proof['device'],'cuda')
        self.assertFalse(proof['sentence_transformers_reference_parity_verified'])
        for key,value in (('finite',False),('tail',False),('pooling_error',2e-6),
                          ('repeat_error',2e-4),('window_lengths',[128]),('window_lengths',[256,256]),('repeat_error',float('nan'))):
            with self.subTest(key=key), self.assertRaises(ValueError):
                setup.smoke_report(**{**values,key:value})

    def test_source_active_or_missing_ready_stops_before_install_and_conversion(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);ready=root/'ready.json'
            with patch.object(setup.numerical,'load_ready',side_effect=setup.numerical.NumericalHold('not_ready')):
                with patch.object(setup.subprocess,'run',side_effect=AssertionError('no process allowed')):
                    with self.assertRaises(setup.numerical.NumericalHold):
                        setup.run(root,ready)
            path=root/'sync/analysis_resource_plan.json';path.parent.mkdir()
            path.write_text('{"reservations":[{"state":"active","lease_id":"native_fixture"}]}')
            with patch.object(setup.numerical,'load_ready'):
                with self.assertRaisesRegex(setup.numerical.NumericalHold,'source_still_active'):
                    setup.require_closed(root,ready)

    def test_describe_never_opens_inputs_or_spawns_a_process(self):
        with patch.object(setup,'run',side_effect=AssertionError('setup must remain dormant')):
            value=setup.main(['--root','unused-fixture-root','--describe'])
        self.assertEqual(value['state'],'dormant')
        self.assertFalse(value['GPU_initialized'])

    def test_actual_shared_reservation_releases_on_failed_setup_without_GPU(self):
        from pipeline import drive_ingest
        from unittest.mock import Mock
        import json
        with TemporaryDirectory() as temp:
            root=Path(temp);path=root/'sync/analysis_resource_plan.json';path.parent.mkdir()
            path.write_text('{"accounting_cap_bytes":23000000000,"reservations":[]}')
            with patch.object(drive_ingest,'storage_usage',return_value=(0,1000)), patch.object(setup.shutil,'disk_usage',return_value=types.SimpleNamespace(free=30_000_000_000)):
                with self.assertRaisesRegex(RuntimeError,'fixture failure'):
                    with setup.reserve(root):
                        value=json.loads(path.read_bytes());self.assertEqual(value['reservations'][0]['state'],'active')
                        self.assertEqual(drive_ingest.reserved_project_growth(root),setup.SETUP_GROWTH_BYTES)
                        raise RuntimeError('fixture failure')
            self.assertEqual(json.loads(path.read_bytes())['reservations'][0]['state'],'released')


if __name__=='__main__':
    unittest.main()
