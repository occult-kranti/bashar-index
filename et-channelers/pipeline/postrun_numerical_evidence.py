"""Restartable local numerical handoff from one validated text generation.

No media, paid APIs or CPU model fallback. CUDA dependencies load only after the
ready document and all completed-generation checks have succeeded.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import time

from . import common, corpus_group_lexical as lexical

METHODS = ('tfidf', 'cluster_sensitivity', 'passage_retrieval')
THRESHOLDS = (.25, .35, .45, .55, .65, .75, .85, .95)
MAX_REPORT_BYTES = 45_000


class NumericalHold(ValueError):
    """An incomplete setup or input must remain pending, never non-estimable."""


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def within(root, value):
    path = Path(value)
    path = (path if path.is_absolute() else root/path).resolve()
    if not path.is_relative_to(root):
        raise ValueError('numerical_artifact_must_stay_under_private_root')
    return path


def artifact(root, path):
    path = within(root, path)
    raw = path.read_bytes()
    return {'path': path.relative_to(root).as_posix(), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def verified(root, proof):
    path = within(root, proof['path'])
    actual = artifact(root, path)
    if actual['sha256'] != proof['sha256'] or ('bytes' in proof and actual['bytes'] != proof['bytes']):
        raise ValueError('numerical_evidence_hash_changed')
    return path


def load_ready(root, path):
    """Recheck both producer pins and the existing full view/edition contracts."""
    root = Path(root).resolve()
    path = within(root, path)
    if not path.is_file():
        raise NumericalHold('awaiting_validated_text_generation')
    ready = json.loads(path.read_bytes())
    generation = within(root, ready['generation'])
    manifest = verified(root, ready['manifest'])
    inventory = verified(root, ready['view_inventory'])
    if manifest != generation/'manifest.json' or inventory != generation/'view-inventory.json':
        raise ValueError('ready_generation_paths_do_not_match')
    data = lexical.load_inventory(root, generation, ready['manifest']['sha256'])
    if (ready['selection_sha256'] != data['manifest']['selection_sha256']
            or data['inventory_sha256'] != ready['view_inventory']['sha256']):
        raise ValueError('ready_generation_selection_or_inventory_changed')
    return ready, data, artifact(root, path)


def _storage(root, growth):
    from . import drive_ingest, host_capacity
    import shutil
    _, occupied = drive_ingest.storage_usage(root, drive_ingest.managed_roots(root))
    future = drive_ingest.reserved_project_growth(root)
    if (occupied+future+growth > host_capacity.MAX_MANAGED_BYTES
            or shutil.disk_usage(root).free-future-growth < host_capacity.MIN_DISK_SPARE):
        raise NumericalHold('numerical_output_storage_deferred')


def _write(root, path, value):
    raw = encoded(value)+b'\n'
    _storage(root, len(raw)+65_536)
    common.atomic_write_text(path, raw.decode('utf-8'))
    return artifact(root, path)


def _preflight(root, model_manifest, model_sha256):
    plan = root/'sync/analysis_resource_plan.json'
    if not plan.is_file():
        raise NumericalHold('collection_resource_ledger_unavailable')
    for row in json.loads(plan.read_bytes())['reservations']:
        if row.get('state') == 'active' and str(row.get('lease_id', '')).startswith(('qualified_', 'native_')):
            raise NumericalHold('collection_source_still_active')
    # find_spec does not initialize CUDA, load a neural model or download code.
    if importlib.util.find_spec('cupy') is None:
        raise NumericalHold('analysis_runtime_missing_cupy')
    if importlib.util.find_spec('ctranslate2') is None:
        raise NumericalHold('analysis_runtime_missing_ctranslate2')
    if model_manifest is None or model_sha256 is None:
        raise NumericalHold('converted_MiniLM_and_actual_CUDA_fixture_pending')
    from . import corpus_semantic_retrieval as semantic
    try:
        semantic.load_model_manifest(root, within(root, model_manifest), model_sha256)
    except FileNotFoundError as error:
        raise NumericalHold('converted_MiniLM_and_actual_CUDA_fixture_pending') from error


def _cached(root, checkpoint, stage):
    saved = checkpoint.get(stage)
    if saved is None:
        return None
    for proof in saved['proofs']:
        verified(root, proof)
    return saved


def _lexical_result(root, directory, manifest_sha256):
    directory = within(root, directory)
    manifest = json.loads((directory/'manifest.json').read_bytes())
    raw = (directory/'analysis.json').read_bytes()
    result = json.loads(raw)
    sha = hashlib.sha256(raw).hexdigest()
    if (manifest['postrun_manifest_sha256'] != manifest_sha256
            or manifest['revision'] != directory.name or manifest['analysis_sha256'] != sha
            or manifest['analysis_bytes'] != len(raw) or result['postrun_manifest_sha256'] != manifest_sha256
            or result.get('method') != lexical.METHOD or manifest.get('method') != lexical.METHOD
            or result.get('backend', {}).get('name') != 'cupy_cuda12x_csr_v1'):
        raise ValueError('verified_CUDA_lexical_generation_required')
    return result


def _score_summary(result):
    groups = {row['id']: row['kind'] for row in result['groups']}
    pairs = defaultdict(list)
    for row in result['cosine_overlap']:
        kind = '_vs_'.join(sorted((groups[row['left']], groups[row['right']])))
        pairs[kind].append(row)
    output = {}
    for kind, rows in sorted(pairs.items()):
        scores = [r['cosine'] for r in rows if r['cosine'] is not None and not r['overlap_is_not_independent']]
        output[kind] = {'possible_pairs': len(rows), 'independent_measured_pairs': len(scores),
            'shared_input_pairs': sum(r['overlap_is_not_independent'] for r in rows),
            'missing_cosine_pairs': sum(r['cosine'] is None for r in rows),
            'independent_cosine_min': min(scores) if scores else None,
            'independent_cosine_median': statistics.median(scores) if scores else None,
            'independent_cosine_max': max(scores) if scores else None}
    return output


def _tfidf_summary(result):
    return {'backend': result['backend'], 'selected_recordings': result['selected_recordings'],
        'observed_primary_texts': result['observed_primary_texts'], 'missing_primary_texts': len(result['missing_primary_texts']),
        'unique_audio_text_units': result['unique_audio_text_units'],
        'collapsed_exact_audio_text_aliases': result['collapsed_exact_audio_text_aliases'],
        'vocabulary_terms': len(result['vocabulary']), 'source_kind_units': result['source_kind_units'],
        'group_counts': dict(Counter(r['kind'] for r in result['groups'])),
        'unassigned_claimed_source_recordings': len(result['unassigned_claimed_source_video_ids']),
        'comparisons': _score_summary(result),
        'limitations': ['English primary views only; missing text remains unknown.',
            'Creator labels are selection owners, not diarized speakers.',
            'Claimed-source labels require episode-specific review; repertoire does not assign an episode.',
            'Lexical overlap and transitive graph components are descriptive, not independent confirmation.']}


def _semantic_result(root, directory, manifest_sha256, model_sha256):
    from . import corpus_semantic_retrieval as semantic
    directory = within(root, directory)
    result = json.loads((directory/'manifest.json').read_bytes())
    with (directory/'chunks.jsonl').open('rb') as source:
        ids = [json.loads(line)['chunk_id'] for line in source]
    semantic.verified_existing(directory, result['revision'], manifest_sha256, model_sha256, expected_chunk_ids=ids)
    if result.get('backend') != 'ctranslate2_cuda_float32_mean_pool_cupy_blocked_v1':
        raise ValueError('verified_CUDA_semantic_generation_required')
    return result


def run(root, ready_path, *, model_manifest=None, model_sha256=None, assignments=None,
        assignments_sha256=None, gpu_memory_budget=1_000_000_000):
    """Normal execution is phase-gated; repeat calls verify saved numerical outputs."""
    root = common.ensure_outside_git(root)
    from . import gpu_asr
    with gpu_asr.kernel_lock(root/'sync/numerical_evidence.lock'):
        ready, data, ready_proof = load_ready(root, ready_path)
        if assignments is not None:
            data = lexical.load_inventory(root, root/ready['generation'], ready['manifest']['sha256'],
                assignments=within(root, assignments), assignments_sha256=assignments_sha256)
        method_files = ('postrun_numerical_evidence.py', 'corpus_group_lexical.py',
                        'corpus_semantic_retrieval.py', 'lexical_cluster_figures.py', 'gpu_workload_pacing.py')
        code = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in method_files}
        key = hashlib.sha256(encoded([ready_proof, code, model_sha256, data.get('review_pin'), gpu_memory_budget])).hexdigest()
        home = root/'research/project-text-agents/numerical-runs'/key
        home.mkdir(parents=True, exist_ok=True)
        state_path = home/'checkpoint.json'
        checkpoint = json.loads(state_path.read_bytes()) if state_path.exists() else {}
        manifest_sha = ready['manifest']['sha256']
        try:
            _preflight(root, model_manifest, model_sha256)
            saved = _cached(root, checkpoint, 'tfidf')
            if saved is None:
                directory = lexical.run(root, root/ready['generation'], manifest_sha,
                    assignments=within(root, assignments) if assignments else None,
                    assignments_sha256=assignments_sha256, gpu_memory_budget=gpu_memory_budget)
                checkpoint['tfidf'] = saved = {'directory': directory.relative_to(root).as_posix(),
                    'proofs': [artifact(root, directory/'analysis.json'), artifact(root, directory/'manifest.json')]}
                _write(root, state_path, checkpoint)
            result = _lexical_result(root, saved['directory'], manifest_sha)
            if (result['selection_sha256'] != ready['selection_sha256']
                    or result['view_inventory_sha256'] != ready['view_inventory']['sha256']):
                raise ValueError('lexical_source_identity_changed')
            lexical_proof = artifact(root, within(root, saved['directory'])/'analysis.json')
            analyses = [{'method': 'tfidf', 'status': 'measured' if result['vocabulary'] else 'not_estimable',
                'artifact': lexical_proof, 'summary': _tfidf_summary(result)}]
            if not result['vocabulary']:
                analyses[0]['summary']['reason'] = 'zero_non_stopword_primary_English_terms'

            saved = _cached(root, checkpoint, 'cluster_sensitivity')
            if saved is None:
                from .lexical_cluster_figures import summarize
                comparisons, curves = summarize(result, THRESHOLDS)
                value = {'schema_version': 1, 'selection_sha256': ready['selection_sha256'],
                    'generation_manifest_sha256': manifest_sha, 'source_lexical_analysis': lexical_proof,
                    'thresholds': THRESHOLDS, 'curves': curves,
                    'independent_measured_pairs': sum(r['comparison'] == 'compared' for r in comparisons),
                    'limitations': ['Saved GPU cosine scores reused; CPU performs only graph bookkeeping.',
                        'Shared text/family pairs excluded. Components may be transitive.',
                        'No significance, topic truth or speaker attribution is inferred.']}
                proof = _write(root, home/'cluster-sensitivity.json', value)
                checkpoint['cluster_sensitivity'] = saved = {'proofs': [proof]}
                _write(root, state_path, checkpoint)
            cluster = json.loads(verified(root, saved['proofs'][0]).read_bytes())
            if (cluster['selection_sha256'] != ready['selection_sha256']
                    or cluster['generation_manifest_sha256'] != manifest_sha
                    or cluster['source_lexical_analysis'] != lexical_proof):
                raise ValueError('cluster_source_identity_changed')
            analyses.append({'method': 'cluster_sensitivity',
                'status': 'measured' if cluster['independent_measured_pairs'] else 'not_estimable',
                'artifact': saved['proofs'][0], 'summary': {k: cluster[k] for k in
                    ('thresholds', 'curves', 'independent_measured_pairs', 'limitations')}})
            if not cluster['independent_measured_pairs']:
                analyses[-1]['summary']['reason'] = 'no_independent_assessed_within_kind_group_pairs'

            saved = _cached(root, checkpoint, 'passage_retrieval')
            if saved is None:
                from . import corpus_semantic_retrieval as semantic
                try:
                    directory = semantic.run(root, root/ready['generation'], manifest_sha,
                        within(root, model_manifest), model_sha256, gpu_memory_budget=gpu_memory_budget)
                except ValueError as error:
                    if str(error) != 'no_nonempty_primary_text_chunks':
                        raise
                    value = {'schema_version': 1, 'reason': 'no_nonempty_primary_English_text_chunks',
                        'selected_recordings': len(data['roster']), 'observed_primary_texts': len(data['documents']),
                        'generation_manifest_sha256': manifest_sha}
                    proof = _write(root, home/'passage-not-estimable.json', value)
                    saved = {'proofs': [proof], 'not_estimable': True}
                else:
                    output = json.loads((directory/'manifest.json').read_bytes())
                    saved = {'directory': directory.relative_to(root).as_posix(), 'proofs':
                        [artifact(root, directory/'manifest.json')]+[artifact(root, directory/name) for name in output['files']]}
                checkpoint['passage_retrieval'] = saved
                _write(root, state_path, checkpoint)
            if saved.get('not_estimable'):
                summary = json.loads(verified(root, saved['proofs'][0]).read_bytes())
                if summary['generation_manifest_sha256'] != manifest_sha:
                    raise ValueError('passage_source_identity_changed')
                status = 'not_estimable'
            else:
                measured = _semantic_result(root, saved['directory'], manifest_sha, model_sha256)
                summary = {k: measured[k] for k in ('backend', 'selected_recordings', 'observed_primary_texts',
                    'missing_primary_texts', 'unique_inference_chunks', 'ranked_candidates', 'top_k',
                    'max_sequence_length', 'overlap_tokens', 'model_revision', 'utilization_pacing')}
                summary['missing_primary_texts'] = len(measured['missing_primary_texts'])
                summary['limitations'] = ['Cross-creator cosine rankings are unreviewed retrieval candidates, not probabilities or event identities.',
                    'Repeated audio/text/family and overlapping creator sets excluded before ranking.',
                    'Offsets address original Unicode views; cue timing is not verified word alignment.']
                status = 'measured' if measured['ranked_candidates'] else 'not_estimable'
                if status == 'not_estimable':
                    summary['reason'] = 'zero_eligible_cross_creator_passage_pairs_after_identity_masks'
            analyses.append({'method': 'passage_retrieval', 'status': status, 'artifact': saved['proofs'][0], 'summary': summary})
            report = {'schema_version': 1, 'state': 'complete', 'selection_sha256': ready['selection_sha256'],
                'generation_manifest_sha256': manifest_sha, 'analyses': analyses,
                'source_ready': ready_proof, 'method_code_sha256': code,
                'GPU_target': {'rolling_utilization_target': .70, 'instantaneous_guarantee': False},
                'Source_requests': 0, 'paid_API_requests': 0}
            if tuple(r['method'] for r in analyses) != METHODS or len(encoded(report)) >= MAX_REPORT_BYTES:
                raise ValueError('compact_three_method_numerical_report_required')
            _write(root, home/'numerical-evidence.json', report)
            output = root/'research/project-text-agents/numerical-evidence.json'
            _write(root, output, report)
            return artifact(root, output)
        except (NumericalHold, ModuleNotFoundError) as error:
            _write(root, home/'hold.json', {'state': 'held', 'reason': str(error),
                'selection_sha256': ready['selection_sha256'], 'generation_manifest_sha256': manifest_sha,
                'setup_failure_is_not_non_estimability': True,
                'completed_stage_checkpoints': sorted(checkpoint),
                'partial_results_are_not_complete': True})
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--ready', type=Path)
    parser.add_argument('--model-manifest', type=Path)
    parser.add_argument('--model-sha256')
    parser.add_argument('--entity-assignments', type=Path)
    parser.add_argument('--assignments-sha256')
    parser.add_argument('--gpu-working-mb', type=int, default=1000)
    parser.add_argument('--describe', '--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if args.describe:
        return {'state': 'dormant', 'methods': METHODS, 'GPU_initialized': False, 'model_inference': False,
                'requires': 'validated text generation, reviewed runtime and actual CUDA model fixture'}
    if not 256 <= args.gpu_working_mb <= 16000:
        raise ValueError('bounded_GPU_working_budget_required')
    if args.model_manifest is None and args.model_sha256 is None:
        runtime_path = args.root/'research/project-text-agents/analysis-runtime.READY.json'
        if runtime_path.is_file():
            runtime = json.loads(runtime_path.read_bytes())
            if runtime.get('state') != 'ready' or runtime.get('post_collection_synthetic_CUDA_fixture') is not True:
                raise NumericalHold('reviewed_analysis_runtime_not_ready')
            model = runtime['model_manifest']
            args.model_manifest, args.model_sha256 = within(args.root.resolve(), model['path']), model['sha256']
    return run(args.root, args.ready or args.root/'research/project-text-agents/text-generation-ready.json',
        model_manifest=args.model_manifest, model_sha256=args.model_sha256,
        assignments=args.entity_assignments, assignments_sha256=args.assignments_sha256,
        gpu_memory_budget=args.gpu_working_mb*1_000_000)


if __name__ == '__main__':
    try:
        print(json.dumps(main()))
    except NumericalHold as error:
        print(json.dumps({'state': 'held', 'reason': str(error), 'retry_after_setup': True}))
        raise SystemExit(75)
