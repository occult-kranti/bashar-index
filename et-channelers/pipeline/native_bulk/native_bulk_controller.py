"""One explicitly granted finite cohort, serial frames, no automatic restart."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


batch_module = load('owned_bulk_cohort_batch', 'native_batch.py')
contract = batch_module.bulk_contract
worker = batch_module.worker
need = contract.need


def frame_closed(batch):
    """Only saved metadata. Never infer zero source attempts from missing files."""
    need(getattr(batch, 'parallel_callback_closure_proven', False) is True, 'bulk_parallel_callbacks_unclosed')
    proofs = []
    for marker in sorted(batch.jobs.glob('*/attempt.json')):
        ident = marker.parent.name
        need(ident in {x['video_id'] for x in batch.items}, 'bulk_foreign_attempt')
        audit_path = marker.parent / 'parent-audit.json'
        need(audit_path.exists(), 'bulk_child_audit_missing')
        audit = worker.read(audit_path)
        need(audit.get('owned_processes_gone') is True, 'bulk_child_closure_unproven')
        result_path=marker.parent/'result.json'
        complete=result_path.exists() and contract.terminal_result_complete(worker.read(result_path),ident)
        censored=False if complete else contract.parent_censored_valid(marker.parent,ident,
            getattr(batch,'settings_path',None),getattr(batch,'plan_sha',None))
        need(complete or censored,'bulk_child_diagnostics_missing')
        proof={'video_id':ident,'attempt_sha256':worker.digest(marker),'parent_audit_sha256':worker.digest(audit_path),
               'owned_child_identity':audit.get('owned_child_identity'),'owned_processes_gone':True,
               'progress_observed':(marker.parent/'progress.json').exists()}
        if complete:proof.update(outcome_kind='worker_terminal_result',terminal_result_sha256=worker.digest(result_path))
        else:proof.update(outcome_kind='parent_censored_timeout',parent_censored_sha256=worker.digest(marker.parent/'parent-censored.json'),
                          source_access='unknown',item_quarantined=True,counts_as_success=False,resets_streak=False)
        proofs.append(proof)
    need(not batch.live_reservations, 'bulk_live_reservations_remain')
    return proofs


class BulkController:
    def __init__(self, settings_path, *, batch_factory=None):
        self.settings_path = Path(settings_path).resolve()
        self.s, self.manifest, self.ids, self.frames = contract.metadata(self.settings_path)
        self.root = Path(self.s['root']).resolve()
        self.runtime = self.settings_path.parent / 'runtime'
        self.state_path = self.runtime / 'cohort-state.json'
        self.invocation_path = self.runtime / 'source-invocation.json'
        self.factory = batch_factory or batch_module.NativeBatch
        need(self.s.get('owner') == 'root' and isinstance(self.s.get('lease_id'), str), 'bulk_controller_owner')

    def plan(self):
        for row in self.frames:
            need(worker.digest(row['plan_path']) == row['plan_sha256'], 'bulk_frame_plan_changed')
            plan = worker.read(row['plan_path'])
            need([x['video_id'] for x in plan['items']] == row['video_ids'], 'bulk_plan_membership')
        return {'status': 'disabled_finite_cohort_preparation', 'cohort_items': len(self.ids),
                'frames': len(self.frames), 'source_workers': 2, 'publishers': 1,
                'source_requests': 0, 'Drive_requests': 0, 'runtime_created': False}

    def admit(self, row):
        frame_settings = worker.read(row['settings_path'])
        need(frame_settings['cohort_controller_settings']['sha256'] == worker.digest(self.settings_path) and
             Path(frame_settings['cohort_controller_settings']['path']).resolve() == self.settings_path,
             'bulk_controller_settings_pin')
        lease = worker.read(worker.control_paths(self.root)['lease_path'])
        _, grant = contract.frame_admission(row['settings_path'], lease)
        return grant

    def run(self):
        # No runtime or source marker is created before exact Root admission.
        self.plan()
        grant = self.admit(self.frames[0])
        grant_sha = worker.digest(self.s['root_admission_path'])
        identity = contract.windows_identity()
        with batch_module.storage.exclusive_lock(self.runtime):
            need(not self.invocation_path.exists() and not self.state_path.exists(),
                 'bulk_existing_invocation_requires_root_reconciliation')
            self.runtime.mkdir(parents=True, exist_ok=True)
            invocation = {'schema_version': 1, 'controller_identity': identity,
                          'root_grant_sha256': grant_sha, 'controller_settings_sha256': worker.digest(self.settings_path),
                          'cohort_manifest_sha256': self.s['cohort_manifest']['sha256'],
                          'frame_map_sha256': self.s['frame_map']['sha256'],
                          'started_at_epoch': time.time(), 'source_invocations': 1,
                          'automatic_restart_allowed': False}
            with self.invocation_path.open('xb') as out:
                out.write(worker.encoded(invocation)); out.flush(); os.fsync(out.fileno())
            state = dict(invocation, status='active', current_frame=None, frames=[], last_ledger_sha256=None)
            worker.write(self.state_path, state)
            ledger_path = worker.control_paths(self.root)['http_state_path']
            for row in self.frames:
                state['current_frame'] = {'frame_index': row['frame_index'], 'plan_sha256': row['plan_sha256'],
                                          'frame_launcher_identity': identity, 'base_identities': [],
                                          'status': 'preparing', 'phase': 'admission',
                                          'batch_run_may_have_started': False, 'at_epoch': time.time()}
                try:
                    worker.write(self.state_path, state)
                    self.admit(row)  # Fresh grant, exact map/settings and live lease.
                    need(worker.digest(self.s['root_admission_path']) == grant_sha, 'bulk_grant_changed')
                    state['current_frame']['phase'] = 'ledger_boundary'
                    if state['last_ledger_sha256'] is not None:
                        need(worker.digest(ledger_path) == state['last_ledger_sha256'], 'bulk_boundary_ledger_changed')
                    state['current_frame']['phase'] = 'construction'
                    batch = self.factory(row['settings_path'])
                    need(batch.http_state_path.resolve() == ledger_path.resolve(), 'bulk_shared_ledger_path')
                    state['current_frame']['phase'] = 'pre_source_guard'
                    # Fresh capacity/control/receipt gate before any fork.
                    batch.guard(source=True, force=True, force_inventory=True, video_id=row['video_ids'][0])
                    state['current_frame'].update(status='started', phase='batch_run', batch_run_may_have_started=True)
                    worker.write(self.state_path, state)  # Durable marker BEFORE Batch.run can fork.
                    result = batch.run()
                    state['current_frame']['phase'] = 'owned_closure'
                    closed = frame_closed(batch)
                    need(not batch.source_stop.is_set() and not batch.dispatch_paused.is_set() and
                         not batch.stop_path.exists() and result.get('pending') == 0 and result.get('inflight') == 0 and
                         result.get('parallel_state') == 'complete' and result.get('parallel_callbacks_closed') is True,
                         'bulk_frame_held_requires_review')
                    envelope = batch.policy_envelope()
                    policy = batch_module.http_policy.status(envelope['state'], time.time(),
                        historical_review=batch.http_review, candidate_video_id=row['video_ids'][-1])
                    need(not policy['global_stop'], 'bulk_sticky_policy_stop')
                    state['last_ledger_sha256'] = worker.digest(ledger_path)
                    state['frames'].append({'frame_index': row['frame_index'], 'plan_sha256': row['plan_sha256'],
                                            'status': 'terminal_closed', 'summary': result, 'owned_children': closed,
                                            'ledger_sha256': state['last_ledger_sha256'],
                                            'next_sequence': envelope['state']['next_sequence']})
                    state['current_frame'] = None
                    worker.write(self.state_path, state)
                except BaseException as error:
                    state['status'] = 'held_reconciliation_required'
                    state['current_frame']['status'] = 'held_reconciliation_required'
                    code = (str(error) if isinstance(error, contract.ContractError) else
                            getattr(error, 'code', getattr(error, 'kind', 'bulk_frame_failed')))
                    state['failed_frame'] = {'frame_index': row['frame_index'],
                                             'phase': state['current_frame']['phase'],
                                             'batch_run_may_have_started': state['current_frame']['batch_run_may_have_started'],
                                             'error_class': code, 'at_epoch': time.time()}
                    worker.write(self.state_path, state)
                    raise
            state['status'] = 'complete'
            state['finished_at_epoch'] = time.time()
            worker.write(self.state_path, state)
            return {'status': 'complete', 'frames': len(state['frames']), 'cohort_items': len(self.ids),
                    'controller_identity': identity, 'ledger_sha256': state['last_ledger_sha256'],
                    'lease_or_reservation_released': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('plan', 'run'))
    parser.add_argument('--settings', type=Path, required=True)
    args = parser.parse_args(argv)
    controller = BulkController(args.settings)
    return controller.plan() if args.mode == 'plan' else controller.run()


if __name__ == '__main__':
    try:
        print(json.dumps(main()))
    except Exception as error:
        print(json.dumps({'status': 'held', 'error_class': getattr(error, 'code',
                         str(error) if isinstance(error, contract.ContractError) else 'bulk_controller_failed')}))
        raise SystemExit(3)
