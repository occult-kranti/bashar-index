"""Source-free resource, ownership, write-bound and publication fixtures."""
from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
from threading import Barrier, Thread
import unittest
from unittest.mock import patch

from pipeline.native_bulk import admission_budget as budget
from pipeline.native_bulk import selection_gate as gate


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


JOBS = tuple(budget.JobKey(letter * 11, 'root', 'fixture-lease', sha('plan'), sha('attempt ' + letter))
             for letter in 'abcdefgh')


def selected(size=50_000_000, tag='one'):
    return budget.Selection(sha('metadata ' + tag), sha('format ' + tag), size)


class Fixture:
    def __init__(self, limits=None):
        self.managed = 8 * budget.GB
        self.spool = 0; self.others = 1 * budget.GB; self.owner_other = 0
        self.free = 35 * budget.GB
        self.files = {}; self.omit = set(); self.revoked = False; self.guards = 0
        self.writes = []
        self.ledger = budget.AdmissionBudget(JOBS, limits=limits or budget.Limits(),
            snapshot=self.snapshot, fresh_guard=self.guard)

    def guard(self):
        self.guards += 1
        if self.revoked: raise budget.BudgetError('fixture_lease_revoked')

    def snapshot(self, excluded):
        included = tuple((key, size) for key, size in self.files.items() if key not in excluded and key not in self.omit)
        actual = sum(size for _, size in included)
        return budget.Inventory(self.managed + actual, self.spool + actual, self.others,
            self.owner_other, self.free, included)

    def bootstrap(self, job):
        value = self.ledger.admit_bootstrap(job)
        self.files[job.job_id] = 0
        return value

    def media(self, job, size=50_000_000):
        self.bootstrap(job)
        self.ledger.bind_selection(job, selected(size))
        permit = self.ledger.reserve_media(job)
        self.ledger.commit_media_go(job, permit, self.writes.append)
        return permit

    def close(self, job, audio=50_000_000, total=51_000_000, ready=True):
        self.files[job.job_id] = total
        proof = budget.ClosedJob(job, sha('closure ' + job.job_id), True, True, audio, total,
                                 sha('strict native quality') if ready else None)
        return self.ledger.settle_owned(proof)


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))

    def test_two_full_unknown_media_and_two_bootstraps_fit_without_extra_media(self):
        f = Fixture()
        for job in JOBS[:2]: f.media(job, None)
        for job in JOBS[2:4]: projection = f.bootstrap(job)
        self.assertEqual(4_960_000_000, sum(j['reserved_bytes'] for j in f.ledger.view()['jobs'].values()))
        self.assertEqual(5_200_000_000, projection.spool_bytes)
        f.ledger.bind_selection(JOBS[2], selected(None))
        with self.assertRaisesRegex(budget.Deferred, 'media_slots'): f.ledger.reserve_media(JOBS[2])
        self.assertEqual('waiting_media', f.ledger.view()['jobs'][JOBS[2].job_id]['stage'])
        self.assertEqual(2, len(f.writes))
        with self.assertRaisesRegex(budget.Deferred, 'child_slots'): f.bootstrap(JOBS[4])

    def test_four_exact_media_fit_but_four_static_full_slots_do_not(self):
        f = Fixture(budget.Limits(max_media=4))
        for job in JOBS[:4]: f.media(job, 145_141_353)
        charged = sum(j['reserved_bytes'] for j in f.ledger.view()['jobs'].values())
        self.assertEqual(1_540_565_412, charged)
        self.assertGreater(4 * (budget.AUDIO_CAP + budget.JOB_HEADROOM), budget.SPOOL_CAP)
        self.assertEqual(4, len(f.writes))

    def test_unknown_third_media_cannot_borrow_an_approximate_size(self):
        f = Fixture(budget.Limits(max_media=4))
        for job in JOBS[:2]: f.media(job, None)
        f.bootstrap(JOBS[2]); f.ledger.bind_selection(JOBS[2], selected(None))
        before = f.ledger.view()
        with self.assertRaisesRegex(budget.Deferred, 'spool_capacity'): f.ledger.reserve_media(JOBS[2])
        self.assertEqual(before, f.ledger.view())
        self.assertEqual(2, len(f.writes))

    def test_simultaneous_upgrades_cannot_double_spend_capacity(self):
        f = Fixture(budget.Limits(max_media=4))
        for job in JOBS[:2]: f.media(job, budget.GB)
        for job in JOBS[2:4]:
            f.bootstrap(job); f.ledger.bind_selection(job, selected(1_500_000_000))
        start = Barrier(3); results = []
        def upgrade(job):
            start.wait()
            try: results.append(('reserved', f.ledger.reserve_media(job)))
            except budget.Deferred as error: results.append(('deferred', str(error)))
        threads = [Thread(target=upgrade, args=(job,)) for job in JOBS[2:4]]
        for thread in threads: thread.start()
        start.wait()
        for thread in threads: thread.join(2); self.assertFalse(thread.is_alive())
        self.assertEqual(['deferred', 'reserved'], sorted(kind for kind, _ in results))
        self.assertEqual(4_460_000_000, sum(j['reserved_bytes'] for j in f.ledger.view()['jobs'].values()))

    def test_each_storage_ceiling_and_exact_managed_boundary(self):
        cases = [('spool', budget.SPOOL_CAP - budget.JOB_HEADROOM + 1, 'spool_capacity'),
                 ('managed', budget.MANAGED_CAP - budget.JOURNAL_RESERVE - budget.JOB_HEADROOM - budget.PUBLISH_HEADROOM + 1, 'managed_capacity'),
                 ('owner_other', 11 * budget.GB, 'owner_capacity'),
                 ('free', budget.SPARE + budget.JOB_HEADROOM + budget.JOURNAL_RESERVE - 1, 'physical_spare')]
        for attribute, value, reason in cases:
            f = Fixture(); f.others = 0; setattr(f, attribute, value)
            with self.subTest(reason=reason), self.assertRaisesRegex(budget.Deferred, reason): f.bootstrap(JOBS[0])
            self.assertFalse(f.ledger.view()['jobs'])
        f = Fixture(); f.others = 0
        f.managed = budget.MANAGED_CAP - budget.JOURNAL_RESERVE - budget.JOB_HEADROOM - budget.PUBLISH_HEADROOM
        self.assertEqual(budget.MANAGED_CAP, f.bootstrap(JOBS[0]).managed_bytes)

    def test_active_folder_growth_is_not_double_counted_as_inactive(self):
        f = Fixture(); permit = f.media(JOBS[0], None)
        f.files[JOBS[0].job_id] = 1_500_000_000
        f.bootstrap(JOBS[1])
        self.assertEqual(2_480_000_000, sum(j['reserved_bytes'] for j in f.ledger.view()['jobs'].values()))
        self.assertEqual(budget.AUDIO_CAP, permit.audio_write_limit)

    def test_job_owner_lease_attempt_and_selection_are_immutable(self):
        f = Fixture(); f.bootstrap(JOBS[0])
        for wrong in [replace(JOBS[0], owner='other'), replace(JOBS[0], lease_id='other'),
                      replace(JOBS[0], attempt_sha256=sha('other'))]:
            with self.assertRaisesRegex(budget.BudgetError, 'job_binding'): f.ledger.bind_selection(wrong, selected())
        f.ledger.bind_selection(JOBS[0], selected())
        f.ledger.bind_selection(JOBS[0], selected())  # Re-observing the SAME selection is not a source retry.
        with self.assertRaisesRegex(budget.BudgetError, 'selection_changed'):
            f.ledger.bind_selection(JOBS[0], selected(tag='changed'))
        permit = f.ledger.reserve_media(JOBS[0])
        with self.assertRaisesRegex(budget.BudgetError, 'media_go_binding'):
            f.ledger.commit_media_go(JOBS[0], replace(permit, job=JOBS[1]), f.writes.append)
        self.assertFalse(f.writes)

    def test_fresh_revocation_prevents_go_after_successful_reservation(self):
        f = Fixture(); f.bootstrap(JOBS[0]); f.ledger.bind_selection(JOBS[0], selected())
        permit = f.ledger.reserve_media(JOBS[0]); f.revoked = True
        with self.assertRaisesRegex(budget.BudgetError, 'lease_revoked'):
            f.ledger.commit_media_go(JOBS[0], permit, f.writes.append)
        self.assertFalse(f.writes)
        self.assertEqual('media_reserved', f.ledger.view()['jobs'][JOBS[0].job_id]['stage'])

    def test_failed_or_partial_durable_go_is_one_shot_and_keeps_reservation(self):
        f = Fixture(); f.bootstrap(JOBS[0]); f.ledger.bind_selection(JOBS[0], selected())
        permit = f.ledger.reserve_media(JOBS[0])
        def ambiguous(value):
            f.writes.append(value)
            raise OSError('private path, URL and token must not be copied')
        with self.assertRaisesRegex(budget.BudgetError, '^media_go_commit_failed$'):
            f.ledger.commit_media_go(JOBS[0], permit, ambiguous)
        view = f.ledger.view()
        self.assertEqual('go_uncertain', view['jobs'][JOBS[0].job_id]['stage'])
        self.assertEqual(permit.reserved_job_bytes, view['jobs'][JOBS[0].job_id]['reserved_bytes'])
        for operation in [lambda:f.ledger.commit_media_go(JOBS[0], permit, ambiguous), lambda:f.bootstrap(JOBS[1])]:
            with self.assertRaisesRegex(budget.BudgetError, 'administrative_hold'): operation()
        self.assertEqual(1, len(f.writes))

    def test_write_cap_stops_underestimate_before_extra_byte_and_retains_partial(self):
        f = Fixture(); permit = f.media(JOBS[0], 1000)
        self.assertEqual(1000, budget.check_audio_write(permit, JOBS[0], permit.selection.metadata_sha256, 994, 6))
        with self.assertRaisesRegex(budget.BudgetError, 'selected_write_cap'):
            budget.check_audio_write(permit, JOBS[0], permit.selection.metadata_sha256, 994, 7)
        f.close(JOBS[0], audio=994, total=1_000_000, ready=False)
        self.assertEqual('retained', f.ledger.view()['jobs'][JOBS[0].job_id]['stage'])
        with self.assertRaisesRegex(budget.BudgetError, 'job_already_spent'): f.bootstrap(JOBS[0])

    def test_unknown_write_still_has_full_hard_cap_and_exact_binding(self):
        f = Fixture(); permit = f.media(JOBS[0], None)
        self.assertEqual(budget.AUDIO_CAP, budget.check_audio_write(permit, JOBS[0], permit.selection.metadata_sha256, budget.AUDIO_CAP-1, 1))
        with self.assertRaisesRegex(budget.BudgetError, 'audio_hard_cap'):
            budget.check_audio_write(permit, JOBS[0], permit.selection.metadata_sha256, budget.AUDIO_CAP, 1)
        for job, pin in [(JOBS[1], permit.selection.metadata_sha256), (JOBS[0], sha('wrong metadata'))]:
            with self.assertRaisesRegex(budget.BudgetError, 'write_binding'):
                budget.check_audio_write(permit, job, pin, 0, 1)

    def test_closed_files_must_be_reconciled_before_envelope_release(self):
        f = Fixture(); permit = f.media(JOBS[0])
        f.omit.add(JOBS[0].job_id)
        with self.assertRaisesRegex(budget.BudgetError, 'closed_job_not_reconciled'): f.close(JOBS[0])
        self.assertEqual(permit.reserved_job_bytes, f.ledger.view()['jobs'][JOBS[0].job_id]['reserved_bytes'])
        f.omit.clear(); projection = f.close(JOBS[0])
        self.assertEqual(0, projection.active_reserved_bytes)
        self.assertEqual(51_000_000 + budget.PUBLISH_HEADROOM, projection.spool_bytes)

    def test_unclosed_uningested_or_oversized_job_never_releases_its_envelope(self):
        for gone, history, size in [(False, True, 51_000_000), (True, False, 51_000_000), (True, True, 300_000_000)]:
            f = Fixture(); permit = f.media(JOBS[0])
            proof = budget.ClosedJob(JOBS[0], sha('audit'), gone, history, 50_000_000, size)
            with self.subTest(gone=gone, history=history, size=size), self.assertRaisesRegex(budget.BudgetError, 'closure_or_write'):
                f.ledger.settle_owned(proof)
            self.assertEqual(max(permit.reserved_job_bytes, size), f.ledger.view()['jobs'][JOBS[0].job_id]['reserved_bytes'])
            self.assertIsNotNone(f.ledger.view()['administrative_hold'])

    def test_positive_audio_before_media_go_is_not_normalized_as_local_retained(self):
        f = Fixture(); f.bootstrap(JOBS[0]); f.ledger.bind_selection(JOBS[0], selected())
        f.ledger.reserve_media(JOBS[0])
        proof = budget.ClosedJob(JOBS[0], sha('audit'), True, True, 1, 1000)
        with self.assertRaisesRegex(budget.BudgetError, 'closure_or_write'): f.ledger.settle_owned(proof)

    def test_single_publisher_backpressure_and_proof_before_reuse(self):
        f = Fixture()
        for job in JOBS[:2]: f.media(job); f.close(job)
        with self.assertRaisesRegex(budget.Deferred, 'publication_backpressure'): f.bootstrap(JOBS[2])
        f.ledger.begin_publication(JOBS[0])
        with self.assertRaisesRegex(budget.Deferred, 'single_publisher'): f.ledger.begin_publication(JOBS[1])
        f.files[JOBS[0].job_id] = 1000
        f.ledger.finish_publication(budget.ArchiveProof(JOBS[0], sha('paired Drive proof'), sha('owned cleanup'), 1000))
        f.bootstrap(JOBS[2])
        self.assertEqual('archived', f.ledger.view()['jobs'][JOBS[0].job_id]['stage'])
        with self.assertRaisesRegex(budget.BudgetError, 'job_already_spent'): f.bootstrap(JOBS[0])

    def test_retained_payload_still_blocks_spool_after_full_slot_released(self):
        f = Fixture(budget.Limits(max_media=4, max_pending_bytes=budget.SPOOL_CAP))
        f.media(JOBS[0], None); f.media(JOBS[1], None)
        f.close(JOBS[0], audio=budget.AUDIO_CAP, total=budget.AUDIO_CAP+1_000_000)
        f.bootstrap(JOBS[2]); f.ledger.bind_selection(JOBS[2], selected(None))
        with self.assertRaisesRegex(budget.Deferred, 'spool_capacity'): f.ledger.reserve_media(JOBS[2])

    def test_held_output_has_no_publication_permission_without_strict_quality_pin(self):
        f = Fixture(); f.media(JOBS[0]); f.close(JOBS[0], ready=False)
        with self.assertRaisesRegex(budget.BudgetError, 'publication_stage'): f.ledger.begin_publication(JOBS[0])

    def test_numeric_inputs_and_scope_bounds_do_not_accept_bool_or_approximation(self):
        for size in [0, -1, True, 12.5, '12', budget.AUDIO_CAP+1]:
            with self.subTest(size=size), self.assertRaises(budget.BudgetError): selected(size)
        for limits in [dict(max_children=5), dict(max_bootstraps=3), dict(max_media=5), dict(max_pending_pairs=0)]:
            with self.subTest(limits=limits), self.assertRaises(budget.BudgetError): budget.Limits(**limits)
        with self.assertRaises(budget.BudgetError):
            budget.AdmissionBudget((JOBS[0], JOBS[0]), limits=budget.Limits(), snapshot=lambda _:None, fresh_guard=lambda:None)

    def test_permit_fingerprint_changes_with_immutable_job_or_selection(self):
        permit = budget.MediaPermit(JOBS[0], selected(), 50_000_000, 290_000_000)
        self.assertEqual(64, len(permit.fingerprint()))
        self.assertEqual(permit.fingerprint(), replace(permit).fingerprint())
        self.assertNotEqual(permit.fingerprint(), replace(permit, job=JOBS[1]).fingerprint())
        self.assertNotEqual(permit.fingerprint(), replace(permit, selection=selected(tag='new')).fingerprint())

    def test_real_selection_gate_ack_matches_reserved_limit_and_budget_fingerprint(self):
        metadata = b'{"sanitized_selection":true}'
        for size in [50_000_000, None]:
            with self.subTest(size=size), tempfile.TemporaryDirectory() as temp:
                f = Fixture(); job = JOBS[0]; folder = Path(temp)
                binding = gate.Binding(job.job_id, job.lease_id, job.plan_sha256, job.attempt_sha256,
                                       sha('settings'), sha('worker'), sha('nonce'))
                request = gate.make_request(binding, metadata, size, 1000)
                gate.validate_request(request, binding, metadata, 1000, now=100)
                f.bootstrap(job)
                f.ledger.bind_selection(job, budget.Selection(request['selected_metadata_sha256'], sha('format'), request['expected_audio_bytes']))
                permit = f.ledger.reserve_media(job)
                def durable_writer(value):
                    permission = gate.make_permission(request, binding, metadata, 1000,
                        permit_sha256=value.fingerprint(), now=100)
                    if permission['maximum_audio_bytes'] != value.audio_write_limit:
                        raise budget.BudgetError('gate_budget_allowance_mismatch')
                    gate.write_once(folder / 'MediaGO.json', permission)
                f.ledger.commit_media_go(job, permit, durable_writer)
                acknowledged = gate.read_control(folder / 'MediaGO.json')
                self.assertEqual(permit.audio_write_limit, gate.validate_permission(acknowledged, request, binding, metadata, 1000, now=101))
                self.assertEqual(permit.fingerprint(), acknowledged['permit_sha256'])

    def test_mismatched_gate_allowance_fails_before_permission_is_published(self):
        f = Fixture(); job = JOBS[0]; f.bootstrap(job)
        metadata = b'{"sanitized_selection":true}'
        f.ledger.bind_selection(job, budget.Selection(hashlib.sha256(metadata).hexdigest(), sha('format'), 50))
        permit = f.ledger.reserve_media(job)
        binding = gate.Binding(job.job_id, job.lease_id, job.plan_sha256, job.attempt_sha256,
                               sha('settings'), sha('worker'), sha('nonce'))
        wrong = gate.make_request(binding, metadata, 80, 1000)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'MediaGO.json'
            def durable_writer(value):
                permission = gate.make_permission(wrong, binding, metadata, 1000,
                    permit_sha256=value.fingerprint(), now=100)
                if permission['maximum_audio_bytes'] != value.audio_write_limit:
                    raise budget.BudgetError('gate_budget_allowance_mismatch')
                gate.write_once(path, permission)
            with self.assertRaisesRegex(budget.BudgetError, 'media_go_commit_failed'):
                f.ledger.commit_media_go(job, permit, durable_writer)
            self.assertFalse(path.exists())
            self.assertEqual(50 + budget.JOB_HEADROOM, f.ledger.view()['jobs'][job.job_id]['reserved_bytes'])


if __name__ == '__main__':
    unittest.main()
