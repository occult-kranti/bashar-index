"""Post-collection-only local MiniLM conversion and genuine CUDA fixture setup.

Default execution requires the coordinator's validated text-ready generation.
Authoring and --describe never install, convert, initialize CUDA or infer text.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.request import urlopen
import uuid

from . import common, corpus_semantic_retrieval as semantic, postrun_numerical_evidence as numerical

SETUP_GROWTH_BYTES = 1_500_000_000
BASE_PYTHON = Path.home()/'.conda/envs/vlm-vision-inference/python.exe'
CUDA_HOME = Path('C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.8')
SNAPSHOT = Path.home()/'.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots'/semantic.REVISION
WHEELS = (
    {'distribution': 'ctranslate2', 'version': '4.9.0', 'bytes': 20_406_022,
     'filename': 'ctranslate2-4.9.0-cp310-cp310-win_amd64.whl',
     'sha256': 'b7b5a4626508258991e0c5bec4d172cf72f194ad10193cddaf4f0c43d8fd26a3',
     'url': 'https://files.pythonhosted.org/packages/a9/b8/89ff13e6f29db9b4fec2f5d0b6081283dde87189b0ded0c7b5d18435d73b/ctranslate2-4.9.0-cp310-cp310-win_amd64.whl'},
    {'distribution': 'cupy-cuda12x', 'version': '13.6.0', 'bytes': 89_874_119,
     'filename': 'cupy_cuda12x-13.6.0-cp310-cp310-win_amd64.whl',
     'sha256': 'f33c9c975782ef7a42c79b6b4fb3d5b043498f9b947126d792592372b432d393',
     'url': 'https://files.pythonhosted.org/packages/de/7b/bac3ca73e164d2b51c6298620261637c7286e06d373f597b036fc45f5563/cupy_cuda12x-13.6.0-cp310-cp310-win_amd64.whl'},
    {'distribution': 'fastrlock', 'version': '0.8.3', 'bytes': 30_946,
     'filename': 'fastrlock-0.8.3-cp310-cp310-win_amd64.whl',
     'sha256': '001fd86bcac78c79658bac496e8a17472d64d558cd2227fdc768aa77f877fe40',
     'url': 'https://files.pythonhosted.org/packages/76/a7/8b91068f00400931da950f143fa0f9018bd447f8ed4e34bed3fe65ed55d2/fastrlock-0.8.3-cp310-cp310-win_amd64.whl'},
)


def digest_file(path):
    sha = hashlib.sha256(); size = 0
    with Path(path).open('rb') as source:
        while block := source.read(1024*1024):
            sha.update(block); size += len(block)
    return {'bytes': size, 'sha256': sha.hexdigest()}


def require_closed(root, ready):
    numerical.load_ready(root, ready)
    plan = root/'sync/analysis_resource_plan.json'
    if not plan.is_file():
        raise numerical.NumericalHold('collection_resource_ledger_unavailable')
    for row in json.loads(plan.read_bytes())['reservations']:
        if row.get('state') == 'active' and str(row.get('lease_id', '')).startswith(('qualified_', 'native_')):
            raise numerical.NumericalHold('collection_source_still_active')


@contextmanager
def reserve(root):
    """One bounded future envelope, visible to all existing ledger readers."""
    from . import drive_ingest, gpu_asr, host_capacity
    plan_path = root/'sync/analysis_resource_plan.json'
    key = uuid.uuid4().hex
    lock = root/'sync/native_series_resource.lock'
    with gpu_asr.kernel_lock(lock):
        plan = json.loads(plan_path.read_bytes())
        _, occupied = drive_ingest.storage_usage(root, drive_ingest.managed_roots(root))
        future = drive_ingest.reserved_project_growth(root)
        limit = min(host_capacity.MAX_MANAGED_BYTES, plan['accounting_cap_bytes'])
        if (occupied+future+SETUP_GROWTH_BYTES > limit
                or shutil.disk_usage(root).free-future-SETUP_GROWTH_BYTES < host_capacity.MIN_DISK_SPARE):
            raise numerical.NumericalHold('analysis_runtime_setup_storage_deferred')
        plan['reservations'].append({'lease_id': 'offline_minilm_setup_v1', 'owner': 'postrun_minilm_setup',
            'state': 'active', 'max_bytes': SETUP_GROWTH_BYTES, 'reservation_key': key,
            'source_scope_authorized': False, 'created_at_epoch': time.time(),
            'scope': ['reviewed wheels, inherited-base venv, float32 local model and synthetic CUDA proof']})
        gpu_asr.atomic_json(plan_path, plan)
    try:
        yield
    finally:
        for retry in range(81):
            try:
                with gpu_asr.kernel_lock(lock):
                    plan = json.loads(plan_path.read_bytes())
                    matches = [r for r in plan['reservations'] if r.get('reservation_key') == key and r.get('state') == 'active']
                    if len(matches) != 1:
                        raise ValueError('analysis_runtime_setup_reservation_changed')
                    matches[0].update(state='released', released_at_epoch=time.time())
                    gpu_asr.atomic_json(plan_path, plan)
                break
            except Exception as error:
                if getattr(error, 'kind', None) != 'gpu_owner_busy' or retry == 80:
                    raise
                time.sleep(.1)


def fetch_wheel(path, proof, *, opener=urlopen):
    """Only reviewed binary wheels; an interrupted download is never installed."""
    if path.exists():
        if digest_file(path) != {k: proof[k] for k in ('bytes', 'sha256')}:
            raise ValueError('existing_reviewed_wheel_changed')
        return path
    pending = path.with_suffix('.pending-'+uuid.uuid4().hex)
    with opener(proof['url'], timeout=60) as response, pending.open('xb') as out:
        count = 0
        while block := response.read(1024*1024):
            count += len(block)
            if count > proof['bytes']:
                raise ValueError('reviewed_wheel_extent_exceeded')
            out.write(block)
        out.flush(); os.fsync(out.fileno())
    if digest_file(pending) != {k: proof[k] for k in ('bytes', 'sha256')}:
        raise ValueError('reviewed_wheel_hash_mismatch')
    os.rename(pending, path)
    return path


@contextmanager
def no_torch_forward(torch):
    original = torch.nn.Module._call_impl
    def forbidden(*args, **kwargs):
        raise ValueError('CPU_neural_forward_forbidden_during_conversion')
    torch.nn.Module._call_impl = forbidden
    try:
        yield
    finally:
        torch.nn.Module._call_impl = original


def smoke_report(*, finite, tail, pooling_error, repeat_error, window_lengths, runtime, pacing):
    if (finite is not True or tail is not True or not window_lengths
            or max(window_lengths) != 256 or min(window_lengths) < 2
            or len(set(window_lengths)) < 2
            or any(type(x) not in (float, int) or not math.isfinite(x) or x < 0 for x in (pooling_error, repeat_error))
            or pooling_error > 1e-6 or repeat_error > 1e-4):
        raise ValueError('actual_CUDA_fixture_protocol_failed')
    return {'schema_version': 1, 'model_revision': semantic.REVISION, 'device': 'cuda',
        'compute_type': 'float32', 'pooling': semantic.POOLING, 'dimension': 384,
        'maximum_sequence_length': 256, 'finite_unit_vectors': True, 'full_window_tail_covered': True,
        'mask_mean_pooling_max_abs_error': pooling_error, 'repeatability_max_cosine_error': repeat_error,
        'window_lengths': window_lengths, 'runtime': runtime, 'utilization_pacing': pacing,
        'corpus_inference': False, 'CPU_neural_forward': False,
        'sentence_transformers_reference_parity_verified': False}


def worker(root, ready, snapshot, home):
    """Called only by the reviewed inherited-base Python 3.10 runtime."""
    root, ready, snapshot, home = map(Path, (root, ready, snapshot, home))
    require_closed(root, ready)
    if sys.version_info[:2] != (3,10) or snapshot.name != semantic.REVISION:
        raise ValueError('reviewed_Python310_and_pinned_local_snapshot_required')
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_PATH=str(CUDA_HOME),
                      CUPY_CACHE_DIR=str(home/'cupy-cache'), CUDA_CACHE_PATH=str(home/'cuda-cache'))
    dll = os.add_dll_directory(str(CUDA_HOME/'bin')) if os.name == 'nt' else None
    import torch
    import transformers
    import ctranslate2
    import cupy as cp
    import numpy
    import tokenizers
    import safetensors
    from . import gpu_asr, gpu_workload_pacing
    from ctranslate2.converters import TransformersConverter
    runtime = {'python': sys.version.split()[0], 'torch': torch.__version__,
        'torch_cuda': torch.version.cuda, 'transformers': transformers.__version__,
        'ctranslate2': ctranslate2.__version__, 'cupy': cp.__version__,
        'numpy': numpy.__version__, 'tokenizers': tokenizers.__version__, 'safetensors': safetensors.__version__,
        'backend': 'ctranslate2_cuda_float32_mean_pool_cupy_blocked_v1',
        'existing_CUDA_toolkit': str(CUDA_HOME), 'base_prefix': sys.base_prefix}
    if (ctranslate2.__version__ != '4.9.0' or cp.__version__ != '13.6.0'
            or torch.__version__.split('+')[0] != '2.6.0' or torch.version.cuda is not None
            or transformers.__version__ != '4.51.3' or numpy.__version__ != '1.26.4'
            or tokenizers.__version__ != '0.21.1' or safetensors.__version__ != '0.5.3'):
        raise ValueError('reviewed_analysis_dependency_versions_required')
    target = home/'model'
    manifest = target/'manifest.json'
    if manifest.exists():
        semantic.load_model_manifest(root, manifest, digest_file(manifest)['sha256'])
        return {'model_manifest': numerical.artifact(root, manifest), 'runtime': runtime, 'reused_verified_model': True}
    if target.exists():
        raise ValueError('existing_incomplete_final_model_requires_preservation')
    source_config = json.loads((snapshot/'config.json').read_bytes())
    if (source_config.get('model_type') != 'bert' or source_config.get('hidden_size') != 384
            or source_config.get('num_hidden_layers') != 6):
        raise ValueError('cached_MiniLM_BERT_configuration_required')
    weights = digest_file(snapshot/'model.safetensors')
    if weights['bytes'] != 90_868_376:
        raise ValueError('pinned_cached_source_weight_extent_changed')
    attempt = home/'attempts'/uuid.uuid4().hex
    attempt.mkdir(parents=True)
    converted = attempt/'model'
    # This converter may load CPU weights; a neural forward is forbidden.
    with no_torch_forward(torch):
        TransformersConverter(str(snapshot), copy_files=['tokenizer.json','vocab.txt']).convert(
            str(converted), quantization='float32', force=False)
    tokenizer = semantic.LocalTokenizer(converted/'tokenizer.json')
    text = ('café naïve Ελληνικά 東京 stars and oceans. '*350)+'Final Unicode tail café.'
    view = {'text': text, 'segments': [{'source_segment_id': 'synthetic:0', 'char_start': 0,
             'char_end': len(text), 'time_start': None, 'time_end': None}]}
    windows = semantic.chunk_spans(view, tokenizer)
    total = len(tokenizer.encode(text).ids)
    covered = {i for row in windows for i in range(row['token_start'], row['token_end'])}
    tail = (covered == set(range(total)) and windows[-1]['token_end'] == total
            and windows[-1]['char_end'] == len(text))
    batch = [windows[0]['token_ids'], windows[-1]['token_ids'], [101]+list(tokenizer.encode('café tail.').ids)+[102]]
    with gpu_asr.kernel_lock(root/'sync/asr_gpu_owner.lock'):
        if cp.cuda.runtime.memGetInfo()[0] < 512*1024**2:
            raise numerical.NumericalHold('model_fixture_CUDA_memory_deferred')
        with gpu_workload_pacing.pace_cuda(pci_bus_id=cp.cuda.Device().pci_bus_id,
                synchronize=lambda: cp.cuda.runtime.deviceSynchronize(), target=.70) as pacer:
            with pacer.block():
                encoder = semantic.CudaMeanEncoder({'model_root': str(converted)}, cp)
            try:
                with pacer.block():
                    first = encoder.encode(batch)
                    second = encoder.encode(batch)
                    finite = bool(cp.all(cp.isfinite(first))) and bool(cp.all(cp.abs(cp.linalg.norm(first,axis=1)-1)<1e-5))
                    repeat = float(cp.max(cp.abs(1-cp.sum(first*second,axis=1))).get())
                    hidden = encoder.encoder.forward_batch(batch).last_hidden_state
                    if str(hidden.device) != 'cuda':
                        raise ValueError('actual_CUDA_hidden_states_required')
                    cp.cuda.runtime.deviceSynchronize()
                    host = cp.asarray(hidden).get().tolist()
                    reference = semantic.cpu_fixture_pool(host, [len(x) for x in batch], fixture_only=True)
                    pooling = float(cp.max(cp.abs(first-cp.asarray(reference,dtype=cp.float32))).get())
            finally:
                with pacer.block():
                    encoder.close()
    proof = smoke_report(finite=finite, tail=tail, pooling_error=pooling, repeat_error=repeat,
        window_lengths=[len(row) for row in batch], runtime=runtime, pacing=pacer.summary())
    proof['full_text_window_count'] = len(windows)
    proof['full_text_token_count'] = total
    proof['padding_exercised'] = len({len(row) for row in batch}) > 1
    proof['synthetic_unicode_text_sha256'] = hashlib.sha256(text.encode()).hexdigest()
    proof['semantic_adapter_sha256'] = digest_file(Path(semantic.__file__))['sha256']
    proof['created_at'] = datetime.now(timezone.utc).isoformat()
    common.atomic_write_text(converted/'cuda-smoke.json', numerical.encoded(proof).decode()+'\n')
    value = {'schema_version': 1, 'repository': semantic.REPOSITORY, 'revision': semantic.REVISION,
        'conversion': 'ctranslate2_transformers_float32_no_integer_quantization',
        'source_weights_sha256': weights['sha256'],
        'configuration': {'architecture': 'BertModel', 'hidden_size': 384, 'max_sequence_length': 256, 'pooling': semantic.POOLING},
        'files': [{'path': p.name, **digest_file(p)} for p in sorted(converted.iterdir()) if p.is_file()],
        'validation': {'cuda_fixture_verified': True, 'fixture': {'path': 'cuda-smoke.json', **digest_file(converted/'cuda-smoke.json')},
                       'sentence_transformers_reference_parity_verified': False}, 'runtime': runtime}
    common.atomic_write_text(converted/'manifest.json', numerical.encoded(value).decode()+'\n')
    semantic.load_model_manifest(root, converted/'manifest.json', digest_file(converted/'manifest.json')['sha256'])
    os.rename(converted, target)
    if dll is not None:
        dll.close()
    return {'model_manifest': numerical.artifact(root, target/'manifest.json'), 'runtime': runtime,
            'reused_verified_model': False}


def run(root, ready, *, base_python=BASE_PYTHON, snapshot=SNAPSHOT):
    root = common.ensure_outside_git(root)
    ready = numerical.within(root, ready)
    require_closed(root, ready)
    home = root/'analysis/model_runtime/minilm-py310'
    home.mkdir(parents=True, exist_ok=True)
    from . import gpu_asr
    with gpu_asr.kernel_lock(root/'sync/minilm_setup_owner.lock'), reserve(root):
        venv = home/'venv'
        python = venv/'Scripts/python.exe'
        if not python.is_file():
            subprocess.run([str(base_python), '-m', 'venv', '--system-site-packages', str(venv)], check=True)
        wheel_home = home/'wheels'; wheel_home.mkdir(exist_ok=True)
        wheels = [fetch_wheel(wheel_home/proof['filename'], proof) for proof in WHEELS]
        subprocess.run([str(python), '-m', 'pip', 'install', '--no-index', '--no-deps',
                        '--only-binary=:all:', *map(str,wheels)], check=True)
        # -I keeps arbitrary current-directory imports out; insert this exact source root.
        bootstrap = ('import hashlib,json,pathlib,sys; '
            'p=pathlib.Path(sys.argv[1]); '
            'assert hashlib.sha256(p.read_bytes()).hexdigest()==sys.argv[2]; '
            'sys.path.insert(0,str(p.parent.parent)); '
            'from pipeline.minilm_analysis_setup import worker; '
            'print(json.dumps(worker(*sys.argv[3:7])))')
        completed = subprocess.run([str(python), '-I', '-B', '-c', bootstrap, str(Path(__file__).resolve()),
            digest_file(Path(__file__))['sha256'], str(root), str(ready), str(snapshot), str(home)],
            check=True, text=True, capture_output=True, timeout=1800)
        result = json.loads(completed.stdout.splitlines()[-1])
        descriptor = {'schema_version': 1, 'state': 'ready', 'python_executable': str(python),
            **result, 'source_text_ready': numerical.artifact(root, ready), 'wheels': WHEELS,
            'no_new_Torch_stack': True, 'post_collection_synthetic_CUDA_fixture': True,
            'Source_requests': 0, 'corpus_inference': False}
        path = root/'research/project-text-agents/analysis-runtime.READY.json'
        common.atomic_write_text(path, numerical.encoded(descriptor).decode()+'\n')
        return numerical.artifact(root, path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--ready', type=Path)
    parser.add_argument('--base-python', type=Path, default=BASE_PYTHON)
    parser.add_argument('--snapshot', type=Path, default=SNAPSHOT)
    parser.add_argument('--describe', '--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if args.describe:
        return {'state': 'dormant', 'model_revision': semantic.REVISION, 'planned_wheels': WHEELS,
                'CPU_forward_forbidden': True, 'GPU_initialized': False,
                'requires': 'validated text-ready generation, no active Source, 1.5GB bounded shared allowance'}
    return run(args.root, args.ready or args.root/'research/project-text-agents/text-generation-ready.json',
               base_python=args.base_python, snapshot=args.snapshot)


if __name__ == '__main__':
    try:
        print(json.dumps(main()))
    except numerical.NumericalHold as error:
        print(json.dumps({'state': 'held', 'reason': str(error), 'setup_not_performed': True}))
        raise SystemExit(75)
