"""Scope, privacy, durable deduplication and restart fixtures; no network/I/O."""
from copy import deepcopy
import hashlib
import json
import unittest

from pipeline import native_http_policy as policy

ID, OTHER, THIRD, FOURTH = 'aaaaaaaaaaa', 'bbbbbbbbbbb', 'ccccccccccc', 'ddddddddddd'
MEDIA = 'https://r1---fixture.googlevideo.com/videoplayback?private=never-export-this-token'
CONTROL = 'https://www.youtube.com/watch?v=aaaaaaaaaaa'


def key(value):
    return hashlib.sha256(value.encode()).hexdigest()


def failure(ident=ID, **changes):
    args = {'status': 403, 'request_url': MEDIA, 'final_url': MEDIA, 'selected_url': MEDIA,
            'phase': 'native_transfer', 'video_id': ident, 'format_identity': {'format_id': '140', 'filesize': 123},
            'selection_validated': True, 'now_epoch': 1000}
    args.update(changes)
    return policy.classify_http_failure(**args)


def historical():
    # Original request endpoint and selection are known; exact request/final URL
    # binding is absent from the historical evidence and must remain unproven.
    return failure(request_url=MEDIA, final_url=None, selected_url=None)


def reviewed(state, candidate=OTHER, now=1000, covered=None, allowed=None):
    return policy.status(state, now, candidate_video_id=candidate, historical_review={
        'review_sha256': key('root immutable review'), 'covered_event_ids': covered or [key('historical')],
        'allowed_video_ids': allowed or [OTHER, THIRD, FOURTH]})


class HttpScopeTests(unittest.TestCase):
    def test_exact_selected_request_and_final_response_are_required(self):
        self.assertEqual(failure()['action'], 'item_quarantine')
        for change in ({'selection_validated': False}, {'selected_url': None}, {'final_url': None},
                       {'final_url': MEDIA.replace('r1---', 'r2---')}, {'request_url': MEDIA + '&range=1'},
                       {'method': 'HEAD'}, {'phase': 'bootstrap'}, {'final_url': CONTROL}):
            with self.subTest(change=list(change)):
                event = failure(**change)
                self.assertEqual(event['action'], 'global_stop')
                self.assertFalse(event['binding_verified'])

    def test_same_looking_untrusted_host_and_nonhttps_never_bind(self):
        for url in (MEDIA.replace('.googlevideo.com', '.googlevideo.com.evil.invalid'),
                    MEDIA.replace('https:', 'http:'), MEDIA.replace('https://', 'https://name:secret@'),
                    MEDIA.replace('.com/', '.com:444/')):
            self.assertEqual(failure(request_url=url, selected_url=url, final_url=url)['action'], 'global_stop')

    def test_browser_media403_is_diagnostic_but_control403_and_every429_global(self):
        self.assertEqual(failure(transport='wpc_browser')['action'], 'diagnostic')
        self.assertEqual(failure(transport='wpc_browser', final_url=CONTROL)['action'], 'global_stop')
        for transport in ('wpc_browser', 'yt_dlp_python'):
            self.assertEqual(failure(status=429, transport=transport)['action'], 'global_stop')

    def test_explicit_protection_is_global_without_http_status(self):
        for code in ('bot_check', 'protection_failure', 'access_challenge'):
            event = policy.global_failure_event(code, ID)
            self.assertEqual(event['action'], 'global_stop')
            state = policy.apply_event(policy.empty_state(), event, key(code), 1000)
            self.assertTrue(policy.status(state, 1000, candidate_video_id=OTHER)['global_stop'])

    def test_retry_after_parsing_never_exports_raw_header_or_clamps_early(self):
        delta = failure(status=429, retry_after='120')
        self.assertEqual(delta['retry_not_before_epoch'], 1120)
        date = failure(status=429, retry_after='Thu, 01 Jan 1970 00:20:00 GMT')
        self.assertEqual(date['retry_not_before_epoch'], 1200)
        for raw in ('-1', 'token=secret', '0\r\nAuthorization:secret', '999999999999', 'x' * 200):
            event = failure(status=429, retry_after=raw)
            self.assertTrue(event['retry_after_requires_review'])
            self.assertIsNone(event['retry_not_before_epoch'])
            self.assertNotIn(raw, json.dumps(event))

    def test_format_whitelist_and_event_validation_prevent_secret_serialization(self):
        event = failure(format_identity={'format_id': MEDIA, 'url': MEDIA, 'headers': {'Authorization': 'secret'}, 'filesize': True})
        self.assertEqual(event['format_identity'], {})
        self.assertNotIn('never-export', json.dumps(event))
        event['url'] = MEDIA
        with self.assertRaises(policy.PolicyError):
            policy.apply_event(policy.empty_state(), event, key('secret'), 1000)


class DurablePolicyTests(unittest.TestCase):
    def add(self, state, ident, event_name, at=1000, **kwargs):
        return policy.apply_event(state, failure(ident, **kwargs), key(event_name), at)

    def test_item_hold_never_retries_that_item_but_other_can_continue(self):
        state = self.add(policy.empty_state(), ID, 'first')
        self.assertFalse(policy.status(state, 1000, candidate_video_id=ID)['dispatch_allowed'])
        self.assertTrue(policy.status(state, 1000, candidate_video_id=OTHER)['dispatch_allowed'])
        self.assertIn(ID, policy.status(state, 100000)['quarantined_video_ids'])
        self.assertEqual(policy.status(state, 100000)['distinct_403_count'], 0)

    def test_event_dedup_survives_json_restart_and_does_not_refresh_time(self):
        state = self.add(policy.empty_state(), ID, 'first', 1000)
        restarted = json.loads(json.dumps(state))
        repeated = self.add(restarted, ID, 'first', 1200)
        self.assertEqual(repeated, state)
        with self.assertRaises(policy.PolicyError):
            self.add(state, OTHER, 'first', 1000)

    def test_same_video_multiple_events_counts_once_but_three_distinct_stop_stickily(self):
        state = self.add(policy.empty_state(), ID, 'first', 1000)
        state = self.add(state, ID, 'same-video', 1010)
        state = self.add(state, OTHER, 'second', 1020)
        self.assertFalse(policy.status(state, 1020)['global_stop'])
        state = self.add(state, THIRD, 'third', 1030)
        self.assertEqual(policy.status(state, 1030)['distinct_403_count'], 3)
        self.assertTrue(policy.status(state, 1030)['global_stop'])
        self.assertTrue(policy.status(json.loads(json.dumps(state)), 100000)['global_stop'])

    def test_window_boundary_and_out_of_order_delivery(self):
        state = self.add(policy.empty_state(), ID, 'first', 1000)
        state = self.add(state, OTHER, 'second', 1300)
        state = self.add(state, THIRD, 'third', 1600)
        self.assertFalse(policy.status(state, 1600)['global_stop'])
        # A delayed event demonstrates that three different refusals did occur
        # inside one historical window; delivery order cannot hide that fact.
        state = self.add(state, FOURTH, 'delayed', 1299)
        self.assertTrue(policy.status(state, 1600)['global_stop'])

    def test_historical_unknown_scope_stays_global_without_explicit_target_review(self):
        state = policy.seed_historical_event(policy.empty_state(), historical(), key('historical'), 900)
        self.assertTrue(policy.status(state, 1000, candidate_video_id=OTHER)['global_stop'])
        view = reviewed(state)
        self.assertFalse(view['global_stop'])
        self.assertEqual(view['historical_403_count'], 1)
        self.assertEqual(view['bound_asset_403_count'], 0)
        self.assertFalse(state['events'][key('historical')]['event']['binding_verified'])
        self.assertEqual(state['events'][key('historical')]['event']['action'], 'global_stop')

    def test_historical_unrecorded_header_is_unknown_and_review_cannot_retry_denied_item(self):
        event = dict(historical(), **policy.retry_after_not_recorded())
        state = policy.seed_historical_event(policy.empty_state(), event, key('historical'), 900)
        restored = json.loads(json.dumps(state))
        retained = restored['events'][key('historical')]['event']
        self.assertEqual(retained['retry_after_state'], 'not_recorded')
        self.assertTrue(retained['retry_after_requires_review'])
        self.assertIsNone(retained['retry_not_before_epoch'])
        self.assertFalse(retained['binding_verified'])
        self.assertTrue(policy.status(restored, 1000, candidate_video_id=OTHER)['global_stop'])
        self.assertTrue(reviewed(restored, candidate=OTHER)['dispatch_allowed'])
        self.assertFalse(reviewed(restored, candidate=ID)['dispatch_allowed'])
        with self.assertRaises(policy.PolicyError):
            reviewed(restored, candidate=ID, allowed=[ID])
        bad = dict(event, retry_after_requires_review=False)
        with self.assertRaises(policy.PolicyError):
            policy.seed_historical_event(policy.empty_state(), bad, key('bad'), 900)

    def test_review_never_authorizes_historical_item_or_new_global_failure(self):
        state = policy.seed_historical_event(policy.empty_state(), historical(), key('historical'), 900)
        with self.assertRaises(policy.PolicyError):
            reviewed(state, candidate=ID, allowed=[ID])
        self.assertFalse(reviewed(state, candidate=ID)['dispatch_allowed'])
        state = self.add(state, OTHER, 'new-global', 1000, final_url=None)
        self.assertTrue(reviewed(state, candidate=THIRD)['global_stop'])
        with self.assertRaises(policy.PolicyError):
            reviewed(state, covered=[key('historical'), key('new-global')])

    def test_new_item_quarantine_does_not_invalidate_other_review_targets(self):
        state = policy.seed_historical_event(policy.empty_state(), historical(), key('historical'), 900)
        state = self.add(state, OTHER, 'new-local', 1000)
        self.assertFalse(reviewed(state, candidate=OTHER)['dispatch_allowed'])
        self.assertTrue(reviewed(state, candidate=THIRD)['dispatch_allowed'])
        state = self.add(state, THIRD, 'third-distinct', 1001)
        self.assertTrue(reviewed(state, candidate=FOURTH, now=1001)['global_stop'])

    def test_true_historical_control_refusal_cannot_use_uncertain_asset_seed(self):
        with self.assertRaises(policy.PolicyError):
            policy.seed_historical_event(policy.empty_state(), failure(final_url=CONTROL), key('control'), 900)
        state = policy.seed_historical_event(policy.empty_state(), historical(), key('historical'), 900)
        state['events'][key('historical')]['event'] = failure(final_url=CONTROL)
        with self.assertRaises(policy.PolicyError):
            reviewed(json.loads(json.dumps(state)))

    def test_clock_regression_and_unreviewed_candidates_hold(self):
        state = self.add(policy.empty_state(), ID, 'future', 1200)
        self.assertTrue(policy.status(state, 1100, candidate_video_id=OTHER)['clock_regressed'])
        historical_state = policy.seed_historical_event(policy.empty_state(), historical(), key('historical'), 900)
        self.assertTrue(reviewed(historical_state, candidate='eeeeeeeeeee')['global_stop'])


if __name__ == '__main__':
    unittest.main()
