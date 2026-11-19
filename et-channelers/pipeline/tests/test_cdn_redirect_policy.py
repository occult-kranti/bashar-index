import hashlib
from pathlib import Path
import sys
import unittest
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cdn_redirect_policy as policy
import qualified_edition_receipts as receipts


def url(host, **changes):
    fields = {"id": "example", "itag": "18", "lmt": "1234", "mime": "video/mp4",
              "dur": "71.005", "expire": "2000000000"}
    fields.update(changes)
    return "https://" + host + "/videoplayback?" + urlencode(fields)


class RedirectTests(unittest.TestCase):
    def setUp(self):
        self.source = url("r1.example.googlevideo.com")
        self.next = url("r2.example.googlevideo.com")

    def approve(self, target, status=302, retry=None):
        return policy.approve(self.source, self.source, target, status=status,
                              retry_after_values=[] if retry is None else retry, now_epoch=100)

    def test_response_only_extent_is_recorded_honestly(self):
        target, proof = self.approve(self.next)
        self.assertEqual(target, self.next)
        self.assertIsNone(proof["declared_source_bytes"])
        self.assertEqual(proof["schema_version"], 2)
        self.assertEqual(proof["extent_basis"], "final_http_content_length")
        proof.update(observation_durable_before_follow=True, follow_only_after_approval=True,
                     explicit_redirect_body_reads=0, redirect_body_writes=0)
        hashes = {"original_sha256": hashlib.sha256(self.source.encode()).hexdigest(),
                  "final_sha256": hashlib.sha256(self.next.encode()).hexdigest()}
        self.assertTrue(policy.validate_safe_proof(proof, content_length=1092, **hashes))
        for value in (0, -1, True):
            with self.subTest(length=value), self.assertRaises(policy.Hold):
                policy.validate_safe_proof(proof, content_length=value, **hashes)

    def test_refusal_changed_asset_length_or_redirect_host_stops(self):
        for target in (url("r2.example.googlevideo.com", clen="1092"), url("r2.example.googlevideo.com", id="other"),
                       url("r2.example.googlevideo.com", dur="70"), url("other.example"), self.source,
                       self.next + "&id=example"):
            with self.subTest(target=target), self.assertRaises(policy.Hold):
                self.approve(target)
        for code in (200, 401, 403, 429):
            with self.subTest(status=code), self.assertRaises(policy.Hold):
                self.approve(self.next, status=code)
        with self.assertRaises(policy.Hold):
            self.approve(self.next, retry=["60"])

    def test_declared_source_extent_still_requires_exact_header(self):
        self.source = url("r1.example.googlevideo.com", clen="108")
        self.next = url("r2.example.googlevideo.com", clen="108")
        _, proof = self.approve(self.next)
        self.assertEqual(proof["schema_version"], 1)
        proof.update(observation_durable_before_follow=True, follow_only_after_approval=True,
                     explicit_redirect_body_reads=0, redirect_body_writes=0)
        hashes = {"original_sha256": proof["request_url_sha256"], "final_sha256": proof["final_url_sha256"]}
        self.assertTrue(policy.validate_safe_proof(proof, content_length=108, **hashes))
        with self.assertRaises(policy.Hold):
            policy.validate_safe_proof(proof, content_length=109, **hashes)
        self.assertEqual(policy.artifact(), {"sha256": receipts.CDN_FINAL_LENGTH_POLICY_SHA, "bytes": 7338})


if __name__ == "__main__":
    unittest.main()
