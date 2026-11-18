"""Selected-media permission cannot escape its job, size, metadata or deadline."""
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline.native_bulk import selection_gate as gate
from pipeline.native_bulk import admission_budget as budget


class SelectionGateTests(unittest.TestCase):
    def setUp(self):
        self.binding = gate.Binding('abcdefghijk', 'owned_lease', *[c * 64 for c in 'abcde'])
        self.metadata = b'{"sanitized_metadata":true}'
        self.request = gate.make_request(self.binding, self.metadata, 50, 1000)
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))

    def permission(self, request=None, now=100):
        return gate.make_permission(request or self.request, self.binding, self.metadata, 1000,
                                    permit_sha256='f' * 64, now=now)

    def test_exact_size_or_full_unknown_cap_is_immutable(self):
        permission = self.permission()
        self.assertEqual(50, gate.validate_permission(permission, self.request, self.binding,
                                                     self.metadata, 1000, now=101))
        unknown = gate.make_request(self.binding, self.metadata, None, 1000)
        self.assertEqual(gate.MAX_AUDIO_BYTES, self.permission(unknown)['maximum_audio_bytes'])
        changed = dict(permission, maximum_audio_bytes=51)
        changed['permission_sha256'] = gate.sha({k:v for k,v in changed.items() if k != 'permission_sha256'})
        with self.assertRaisesRegex(gate.GateError, 'binding_changed'):
            gate.validate_permission(changed, self.request, self.binding, self.metadata, 1000, now=101)

    def test_other_attempt_worker_settings_lease_or_metadata_rejected(self):
        for field, value in [('nonce_sha256','f'*64),('attempt_sha256','f'*64),
                             ('worker_sha256','f'*64),('settings_sha256','f'*64),
                             ('lease_id','different_lease'),('video_id','lmnopqrstuv')]:
            with self.subTest(field=field), self.assertRaises(gate.GateError):
                gate.validate_request(self.request, replace(self.binding, **{field:value}),
                                      self.metadata, 1000, now=101)
        with self.assertRaises(gate.GateError):
            gate.validate_request(self.request, self.binding, b'changed', 1000, now=101)

    def test_real_budget_permit_must_match_request_bytes_and_job_before_permission(self):
        job = budget.JobKey(self.binding.video_id, 'root', self.binding.lease_id,
                            self.binding.plan_sha256, self.binding.attempt_sha256)
        selection = budget.Selection(gate.digest_bytes(self.metadata), 'f'*64, 50)
        permit = budget.MediaPermit(job, selection, 50, 50 + budget.JOB_HEADROOM)
        permission = gate.make_reserved_permission(self.request, self.binding, self.metadata, 1000,
                        permit=permit, expected_owner='root', now=100)
        self.assertEqual(permit.fingerprint(), permission['permit_sha256'])
        too_small = budget.MediaPermit(job, replace(selection, declared_bytes=40), 40, 40 + budget.JOB_HEADROOM)
        other_job = replace(permit, job=replace(job, owner='different_owner'))
        for wrong in [too_small, other_job]:
            with self.assertRaises(gate.GateError):
                gate.make_reserved_permission(self.request, self.binding, self.metadata, 1000,
                    permit=wrong, expected_owner='root', now=100)

    def test_unknown_fields_bad_numbers_and_expired_or_future_grants_rejected(self):
        for size in [True, 0, -1, 1.1, gate.MAX_AUDIO_BYTES + 1]:
            with self.subTest(size=size), self.assertRaises(gate.GateError):
                gate.make_request(self.binding, self.metadata, size, 1000)
        with self.assertRaises(gate.GateError):
            gate.validate_request(dict(self.request, signed_url='PRIVATE'), self.binding,
                                  self.metadata, 1000, now=101)
        for now in [1000, 1001]:
            with self.assertRaises(gate.GateError):
                gate.validate_permission(self.permission(), self.request, self.binding,
                                         self.metadata, 1000, now=now)
        with self.assertRaisesRegex(gate.GateError, 'issued_time'):
            gate.validate_permission(self.permission(now=200), self.request, self.binding,
                                     self.metadata, 1000, now=100)

    def test_control_is_invisible_until_flushed_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'MediaGO.json'
            link = os.link
            def inspect_before_publish(source, destination):
                self.assertFalse(target.exists())
                self.assertEqual(self.permission(), gate.read_control(source))
                return link(source, destination)
            with patch.object(gate.os, 'link', side_effect=inspect_before_publish):
                gate.write_once(target, self.permission())
            original = target.read_bytes()
            with self.assertRaises(FileExistsError): gate.write_once(target, self.permission(now=102))
            self.assertEqual(original, target.read_bytes())
            self.assertEqual(1, len(list(Path(temp).glob('MediaGO.json.pending-*'))))

    def test_partial_or_oversize_controls_cannot_be_consumed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'bad.json'
            for raw in [b'{', b'', b'x' * (gate.MAX_CONTROL_BYTES + 1)]:
                path.write_bytes(raw)
                with self.assertRaises(gate.GateError): gate.read_control(path)

    def test_post_publish_housekeeping_failure_still_acknowledges_durable_go(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'MediaGO.json'
            with patch.object(Path, 'unlink', side_effect=PermissionError(13, 'held')):
                outcome = gate.write_once(target, self.permission())
            self.assertEqual({'published': True, 'temporary_retained': True}, outcome)
            self.assertEqual(self.permission(), gate.read_control(target))

    def make_folder(self, folder):
        gate.write_once(folder / 'selected-request.json', self.request)
        (folder / 'selected-metadata.info.json').write_bytes(self.metadata)

    def test_capacity_wait_preserves_selection_beyond_initial_go_window(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); self.make_folder(folder)
            clock = [100.0]; checks = []
            def guard(): checks.append(clock[0])
            def sleep(seconds):
                clock[0] += seconds
                if clock[0] > 165 and not (folder / 'MediaGO.json').exists():
                    gate.write_once(folder / 'MediaGO.json', self.permission(now=clock[0]))
            result = gate.wait_permission(folder, self.request, self.binding, guard=guard,
                job_deadline_monotonic=1000, clock=lambda:clock[0], monotonic=lambda:clock[0], sleep=sleep)
            self.assertGreater(clock[0], 160)
            self.assertGreater(len(checks), 600)
            self.assertEqual(50, result['maximum_audio_bytes'])
            self.assertEqual(self.request, gate.read_control(folder / 'selected-request.json'))

    def test_guard_revocation_and_monotonic_deadline_prevent_permission(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); self.make_folder(folder)
            gate.write_once(folder / 'MediaGO.json', self.permission())
            calls = []
            def revoked():
                calls.append(1)
                if len(calls) == 2: raise gate.GateError('revoked')
            with self.assertRaisesRegex(gate.GateError, 'revoked'):
                gate.wait_permission(folder, self.request, self.binding, guard=revoked,
                    job_deadline_monotonic=200, clock=lambda:101, monotonic=lambda:101)
            with self.assertRaisesRegex(gate.GateError, 'media_deadline'):
                gate.wait_permission(folder, self.request, self.binding, guard=lambda:None,
                    job_deadline_monotonic=100, clock=lambda:101, monotonic=lambda:101)

    def test_changed_saved_request_or_selection_prevents_media_permission(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); self.make_folder(folder)
            gate.write_once(folder / 'MediaGO.json', self.permission())
            (folder / 'selected-metadata.info.json').write_bytes(b'changed')
            with self.assertRaises(gate.GateError):
                gate.wait_permission(folder, self.request, self.binding, guard=lambda:None,
                    job_deadline_monotonic=200, clock=lambda:101, monotonic=lambda:101)
            changed = dict(self.request, deadline_epoch=999)
            with self.assertRaisesRegex(gate.GateError, 'saved_request_changed'):
                gate.wait_permission(folder, changed, self.binding, guard=lambda:None,
                    job_deadline_monotonic=200, clock=lambda:101, monotonic=lambda:101)


if __name__ == '__main__': unittest.main()
