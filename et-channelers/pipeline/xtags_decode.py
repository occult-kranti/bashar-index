"""Bounded offline FormatXTags inspection; no I/O or source-access authority.

Schema: https://github.com/LuanRT/YouTube.js/blob/main/protos/misc/common.proto
Interop: Format.ts URL-decodes top-level xtags before Base64 protobuf decoding.
Unknown fields, duplicate keys, noncanonical varints and malformed data reject.
The exported observation contains categories only, never tag values or input.
"""
import base64
import binascii
import re
from urllib.parse import unquote, parse_qs


class Invalid(ValueError):
    pass


def varint(data, offset):
    start, value = offset, 0
    for shift in range(0, 35, 7):
        if offset >= len(data): raise Invalid()
        byte = data[offset]; offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            if offset - start > 1 and byte == 0: raise Invalid()
            return value, offset
    raise Invalid()


def field(data, offset):
    tag, offset = varint(data, offset)
    if tag not in (10, 18): raise Invalid()
    length, offset = varint(data, offset)
    if not 0 < length <= 256 or offset + length > len(data): raise Invalid()
    return tag >> 3, data[offset:offset + length], offset + length


def protobuf_pairs(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 512: raise Invalid()
    # decodeURIComponent is one operation; do not repeatedly peel encodings.
    if re.search(r'%(?![0-9a-fA-F]{2})', value): raise Invalid()
    encoded = unquote(value, encoding='ascii', errors='strict')
    if not re.fullmatch(r'[A-Za-z0-9_+/-]+={0,2}', encoded): raise Invalid()
    if len(encoded.rstrip('=')) % 4 == 1: raise Invalid()
    padding = '=' * (-len(encoded.rstrip('=')) % 4)
    if '=' in encoded and encoded != encoded.rstrip('=') + padding: raise Invalid()
    try:
        data = base64.b64decode(encoded.rstrip('=') + padding, altchars=b'-_', validate=True)
    except (ValueError, binascii.Error): raise Invalid()
    if not 1 <= len(data) <= 256: raise Invalid()
    # Canonical re-encoding rejects alternate pad bits and stray syntax.
    if base64.urlsafe_b64encode(data).decode().rstrip('=') != encoded.replace('+', '-').replace('/', '_').rstrip('='):
        raise Invalid()
    pairs, offset, keys = [], 0, set()
    while offset < len(data):
        kind, payload, offset = field(data, offset)
        if kind != 1 or len(pairs) >= 8: raise Invalid()
        fields, cursor = {}, 0
        while cursor < len(payload):
            key, text, cursor = field(payload, cursor)
            if key in fields: raise Invalid()
            fields[key] = text.decode('utf-8', errors='strict')
        if set(fields) != {1, 2}: raise Invalid()
        key, text = fields[1], fields[2]
        if not 1 <= len(key) <= 32 or not 1 <= len(text) <= 128 or key in keys: raise Invalid()
        keys.add(key); pairs.append((key, text))
    if not pairs: raise Invalid()
    return pairs


def observe(value, *, encoding):
    """An enum/boolean observation is not permission to ignore any source tag."""
    result = {'encoding': encoding if encoding in {'top_level_protobuf', 'url_query'} else 'unsupported',
              'valid': False, 'exact_drc_only': False,
              'pair_count': 0, 'semantic_tag_present': False, 'unknown_tag_present': False}
    try:
        if encoding == 'top_level_protobuf':
            pairs = protobuf_pairs(value)
        elif encoding == 'url_query':
            if not isinstance(value, str) or not 1 <= len(value) <= 512: raise Invalid()
            parsed = parse_qs(value, keep_blank_values=True, strict_parsing=True, max_num_fields=8)
            if any(len(v) != 1 for v in parsed.values()): raise Invalid()
            pairs = [(k, v[0]) for k, v in parsed.items()]
            if not pairs: raise Invalid()
        else:
            raise Invalid()
        result.update(valid=True, exact_drc_only=pairs == [('drc', '1')], pair_count=len(pairs),
            semantic_tag_present=any(k in {'lang', 'language', 'vlang', 'acont', 'vb', 'isVb'} for k, _ in pairs),
            unknown_tag_present=any(k not in {'drc', 'lang', 'language', 'vlang', 'acont', 'vb', 'isVb'} for k, _ in pairs))
    except (Invalid, ValueError, TypeError, UnicodeError):
        pass
    return result


def processing_only_consistent(top_level, url_tag, *, is_drc):
    """Pure recognition only; callers must retain all original selection gates."""
    top = observe(top_level, encoding='top_level_protobuf')
    url = observe(url_tag, encoding='url_query')
    return {'top_level': top, 'url': url,
            'processing_only_consistent': is_drc is True and top['exact_drc_only'] and url['exact_drc_only']}
