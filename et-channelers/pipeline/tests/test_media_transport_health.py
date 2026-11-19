import math
import unittest

from pipeline.media_transport_health import Health, HealthHold, advance, backoff_seconds, may_dispatch, source_limit


def failure(video='denied00001', **changes):
    return dict(video_id=video, status=403, action='item_quarantine', binding_verified=True,
                retry_after_state='absent', retry_after_requires_review=False,
                retry_not_before_epoch=None, **changes)


def complete(video='success0001'):
    return dict(video_id=video, evidence_sha256='a'*64,
                evidence_kind='validated_complete_qualified_transfer')


class MediaHealthTests(unittest.TestCase):
    def test_interleaved_complete200_resets_only_transport_backoff_not_item_holds(self):
        state = advance(Health(), observed_at_epoch=1000, refusals=[failure()])
        self.assertEqual(source_limit(state, configured_sources=4, now_epoch=1059), 0)
        self.assertEqual(source_limit(state, configured_sources=4, now_epoch=1060), 1)
        state = advance(state, observed_at_epoch=1065, complete_proofs=[complete()])
        self.assertEqual(source_limit(state, configured_sources=4, now_epoch=1065), 4)
        self.assertFalse(may_dispatch(state, 'denied00001', active_sources=0,
                                     configured_sources=4, now_epoch=9999))
        self.assertFalse(state.Native_success_or_reset_inferred)
        state = advance(state, observed_at_epoch=1100, refusals=[failure('denied00002')])
        self.assertEqual(state.not_before_epoch, 1160)
        self.assertEqual(state.failure_waves, 1)

    def test_concurrent_success_does_not_hide_refusal_and_backoff_is_finite(self):
        state = advance(Health(), observed_at_epoch=1000,
                        complete_proofs=[complete()], refusals=[failure()])
        self.assertFalse(state.normal_pool_allowed)
        self.assertEqual(state.complete_transfer_count, 0)
        self.assertEqual([backoff_seconds(n) for n in range(1,9)],
                         [60,120,240,480,960,1800,1800,1800])
        self.assertEqual(advance(state, observed_at_epoch=1100), state)

    def test_global429_or_challenge_cannot_be_cleared_by_another_full200(self):
        event = failure();event.update(status=429, action='global_stop',
                                     retry_after_state='valid', retry_not_before_epoch=5000)
        state = advance(Health(), observed_at_epoch=1000, refusals=[event])
        state = advance(state, observed_at_epoch=6000, complete_proofs=[complete()])
        self.assertEqual(source_limit(state, configured_sources=4, now_epoch=6000), 0)
        self.assertEqual(state.global_hold, 'server_rate_or_wait')
        event = failure();event.update(binding_verified=False)
        self.assertEqual(advance(Health(), observed_at_epoch=1000, refusals=[event]).global_hold,
                         'global_or_unbound_response')

    def test_metadata_only_and_malformed_proofs_never_unlock_parallel_pool(self):
        self.assertEqual(source_limit(Health(), configured_sources=4, now_epoch=1000), 1)
        for clock in (math.nan, math.inf, True):
            with self.assertRaises(HealthHold):advance(Health(), observed_at_epoch=clock)
        proof = complete();proof['evidence_kind'] = 'native_route_pending'
        with self.assertRaises(HealthHold):advance(Health(), observed_at_epoch=1000, complete_proofs=[proof])


if __name__ == '__main__':unittest.main()
