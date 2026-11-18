import base64
import json
import unittest

from pipeline import xtags_decode as d


def tag(key, value):
    key, value = key.encode(), value.encode()
    nested = bytes([10, len(key)]) + key + bytes([18, len(value)]) + value
    return bytes([10, len(nested)]) + nested


def b64(data):
    return base64.urlsafe_b64encode(data).decode()


class DecodeTests(unittest.TestCase):
    def observation(self, value):
        return d.observe(value, encoding='top_level_protobuf')

    def test_known_proto_wire_fixture_and_independent_query_projection(self):
        value = 'CggKA2RyYxIBMQ=='
        self.assertEqual(b64(tag('drc', '1')), value)
        self.assertEqual(d.protobuf_pairs(value), [('drc', '1')])
        self.assertTrue(d.processing_only_consistent(value, 'drc=1', is_drc=True)['processing_only_consistent'])

    def test_one_percent_decoding_and_optional_padding(self):
        for value in ('CggKA2RyYxIBMQ%3D%3D', 'CggKA2RyYxIBMQ'):
            self.assertTrue(self.observation(value)['exact_drc_only'])
        self.assertFalse(self.observation('CggKA2RyYxIBMQ%253D%253D')['valid'])

    def test_semantic_and_unknown_tags_do_not_become_processing_only(self):
        for key in ('lang', 'acont', 'vb', 'unknown'):
            result = self.observation(b64(tag('drc', '1') + tag(key, 'private-value-never-export')))
            self.assertTrue(result['valid']); self.assertFalse(result['exact_drc_only'])
            self.assertNotIn('private-value-never-export', json.dumps(result))

    def test_url_projection_conflict_and_non_drc_flag_reject(self):
        value = b64(tag('drc', '1'))
        for url in ('drc=1&lang=en', 'drc=0', 'vb=1', 'drc=1&drc=1', 'drc=1;lang=en'):
            self.assertFalse(d.processing_only_consistent(value, url, is_drc=True)['processing_only_consistent'])
        for flag in (False, None, 1, 'true'):
            self.assertFalse(d.processing_only_consistent(value, 'drc=1', is_drc=flag)['processing_only_consistent'])

    def test_duplicate_proto_keys_and_nested_fields_reject(self):
        for raw in (tag('drc', '1') * 2, b'\x0a\x0d\x0a\x03drc\x0a\x03drc\x12\x011'):
            self.assertFalse(self.observation(b64(raw))['valid'])

    def test_unknown_fields_missing_value_and_trailing_wire_reject(self):
        for raw in (b'\x1a\x01x', b'\x0a\x05\x0a\x03drc', tag('drc', '1') + b'\x00',
                    tag('drc', '1') + b'\x0b', b'\x0a\x03\x12\x011'):
            self.assertFalse(self.observation(b64(raw))['valid'])

    def test_truncation_and_noncanonical_varints_reject(self):
        raw = tag('drc', '1')
        for bad in (raw[:-1], raw[:1] + b'\x88\x00' + raw[2:], b'\x8a\x00' + raw[1:]):
            self.assertFalse(self.observation(b64(bad))['valid'])

    def test_strict_base64_syntax_and_pad_bits_reject(self):
        for value in ('CggKA2RyYxIBMR==', 'CggKA2RyYxIBMQ=', 'CggKA2RyYxIBMQ===',
                      'CggKA2RyYxIBMQ==\n', '%GG', '!', 'A'):
            self.assertFalse(self.observation(value)['valid'], value)

    def test_invalid_utf8_and_resource_bounds_reject(self):
        for value in (b64(b'\x0a\x08\x0a\x03drc\x12\x01\xff'), b64(b'x' * 257),
                      b64(b''.join(tag(str(i), '1') for i in range(9))), 'A' * 513, '', None, {}):
            self.assertFalse(self.observation(value)['valid'])

    def test_private_bytes_and_unknown_encoding_never_export(self):
        value = b64(tag('secret', 'private-value-never-export'))
        result = d.observe(value, encoding='private-value-never-export')
        encoded = json.dumps(result)
        self.assertNotIn(value, encoded); self.assertNotIn('private-value-never-export', encoded)
        self.assertEqual(result['encoding'], 'unsupported')


if __name__ == '__main__':
    unittest.main()
