"""Conservative inference from complete returned-client raw audio inventories.

Pure observation only: never mutates player responses, makes requests, or
generates tokens. Absence of track labels is not explicit-original evidence.
"""
import hashlib
import json
import re
from urllib.parse import parse_qs, urlsplit

LABEL_FIELDS = {'language', 'languageCode', 'audioLanguage', 'audioTrackId', 'displayName',
    'isOriginal', 'isDubbed', 'isAutoDubbed', 'isDescriptive', 'isSecondary', 'audioIsDefault',
    'isDefault', 'isVoiceBoost', 'isVb', 'xtags'}
AUDIO_CODEC = re.compile(r'^(?:mp4a\.[0-9.]+|opus|vorbis|mp3|aac)$')
MAX_RAW_FORMATS = 8192


def nonempty(value):
    return value is not None and value is not False and value != '' and value != {} and value != []


def transport_track_tags(fmt, explicit_drc=False):
    """Inspect URL/cipher query keys in memory; values never enter a proof."""
    urls = []
    if fmt.get('url') is not None:
        if not isinstance(fmt['url'], str): return True
        urls.append(fmt['url'])
    for key in ('signatureCipher', 'cipher'):
        if fmt.get(key) is not None:
            if not isinstance(fmt[key], str): return True
            values = parse_qs(fmt[key], keep_blank_values=True)
            if any(k in values for k in ('xtags', 'lang', 'language', 'acont')): return True
            urls.extend(values.get('url', []))
    try:
        for url in urls:
            values = parse_qs(urlsplit(url).query, keep_blank_values=True)
            for key, value in values.items():
                if key.lower() == 'drc' and explicit_drc and value == ['1']: continue
                if key.lower() in {'xtags', 'lang', 'language', 'acont', 'drc', 'vb'} and any(value): return True
    except ValueError: return True
    return False


DIAGNOSTIC_TRANSPORT_KEYS = frozenset({'xtags', 'lang', 'language', 'acont', 'drc', 'vb'})
DIAGNOSTIC_TRACK_KEYS = frozenset({'id', 'displayName', 'audioIsDefault', 'languageCode', 'isOriginal', 'isDubbed', 'isAutoDubbed', 'isDescriptive', 'isSecondary'})


def label_diagnostics(fmt):
    """Bounded observation only; projections never change semantic admission."""
    origins = ('top_level', 'url', 'cipher', 'cipher_url')
    projections = {origin: [] for origin in origins}
    result = {'label_fields_present': sorted(k for k in LABEL_FIELDS if nonempty(fmt.get(k))),
        'audio_track_present': fmt.get('audioTrack') not in (None, {}),
        'audio_track_known_keys': [], 'audio_track_unknown_key_present': False,
        'transport_known_keys': [], 'transport_diagnostic_complete': True,
        'xtags_state': 'absent', 'xtags_projection_count': 0,
        'xtags_projection_limit_reached': False, 'xtags_projections_equal': None,
        'all_exact_drc_only': False, 'semantic_admission_unchanged': True}
    track = fmt.get('audioTrack')
    if isinstance(track, dict):
        result['audio_track_known_keys'] = sorted(k for k in DIAGNOSTIC_TRACK_KEYS if k in track)
        result['audio_track_unknown_key_present'] = any(k not in DIAGNOSTIC_TRACK_KEYS for k in track)
    elif track not in (None, {}):
        result['audio_track_unknown_key_present'] = True
    keys = set(); urls = []
    def parsed(value):
        if not isinstance(value, str) or len(value) > 32768: raise ValueError('bounded')
        return parse_qs(value, keep_blank_values=True, max_num_fields=128)
    def add(origin, values):
        for value in values:
            if result['xtags_projection_count'] >= 8:
                result['xtags_projection_limit_reached'] = True
                raise ValueError('bounded')
            projections[origin].append(value); result['xtags_projection_count'] += 1
    def inspect(values, origin):
        keys.update(k.lower() for k in values if k.lower() in DIAGNOSTIC_TRANSPORT_KEYS)
        for key, values0 in values.items():
            if key.lower() == 'xtags': add(origin, values0)
    def exact_drc(value):
        return (isinstance(value, str) and len(value) <= 64 and '&' not in value and ';' not in value
                and parsed(value) == {'drc': ['1']})
    try:
        if nonempty(fmt.get('xtags')): add('top_level', [fmt['xtags']])
        if fmt.get('url') is not None: urls.append(('url', fmt['url']))
        for field in ('signatureCipher', 'cipher'):
            if fmt.get(field) is not None:
                values = parsed(fmt[field]); inspect(values, 'cipher')
                urls.extend(('cipher_url', value) for value in values.get('url', []))
        if len(urls) > 3: raise ValueError('bounded')
        for origin, value in urls:
            if not isinstance(value, str) or len(value) > 32768: raise ValueError('bounded')
            inspect(parsed(urlsplit(value).query), origin)
    except (ValueError, TypeError):
        result['transport_diagnostic_complete'] = False
    # Compare bounded copies in memory only; no values or hashes of values leave.
    all_values = [value for origin in origins for value in projections[origin]]
    result['xtags_projection_counts'] = {origin: len(projections[origin]) for origin in origins}
    result['xtags_by_origin'] = {origin: ('absent' if not projections[origin] else
        'exact_drc_only' if all(exact_drc(value) for value in projections[origin]) else 'other_or_unreadable') for origin in origins}
    complete = result['transport_diagnostic_complete']
    if complete and len(all_values) >= 2 and all(isinstance(value, str) and len(value) <= 64 for value in all_values):
        result['xtags_projections_equal'] = all(value == all_values[0] for value in all_values[1:])
    result['all_exact_drc_only'] = bool(complete and all_values and all(exact_drc(value) for value in all_values))
    if all_values or not complete:
        result['xtags_state'] = 'exact_drc_only' if result['all_exact_drc_only'] else 'other_or_unreadable'
    result['transport_known_keys'] = sorted(keys)
    return result


def legacy_track_inventory(video_id, player_responses, chosen_client='mweb'):
    result = {'schema_version': 1, 'video_id': video_id, 'chosen_client': chosen_client,
        'eligible': False, 'reason': 'missing_raw_inventory', 'audio_representations': [],
        'context_only_responses': 0, 'inventory_responses': 0,
        'completeness_basis': 'entire_parsed_returned_client_arrays', 'provider_global_inventory_claimed': False,
        'inspection_complete': False, 'inspected_formats': 0, 'rejection_reasons': []}
    def hold(reason):
        if reason not in result['rejection_reasons']: result['rejection_reasons'].append(reason)
        result['reason'] = result['rejection_reasons'][0]
        return result
    if not isinstance(player_responses, list) or not 1 <= len(player_responses) <= 16: return hold('missing_raw_inventory')
    seen = {}; structurally_complete = True
    for response in player_responses:
        if not isinstance(response, dict) or not isinstance(response.get('videoDetails'), dict) or response['videoDetails'].get('videoId') != video_id:
            hold('response_identity'); structurally_complete = False; continue
        if not isinstance(response.get('playabilityStatus'), dict) or response['playabilityStatus'].get('status') != 'OK': hold('response_not_playable')
        if response.get('truncated') or response.get('__truncated'): hold('response_incomplete'); structurally_complete = False
        if 'streamingData' not in response:
            hold('response_incomplete'); structurally_complete = False; continue
        streaming = response['streamingData']
        if streaming is None:  # pinned extractor's stripped initial caption context
            result['context_only_responses'] += 1
            continue
        if not isinstance(streaming, dict) or streaming.get('__yt_dlp_client') != chosen_client:
            hold('conflicting_client_inventory'); structurally_complete = False; continue
        if not any(key in streaming for key in ('formats', 'adaptiveFormats')): hold('response_incomplete'); structurally_complete = False
        result['inventory_responses'] += 1
        for key in ('formats', 'adaptiveFormats'):
            formats = streaming.get(key, [])
            if not isinstance(formats, list) or len(formats) > 4096:
                hold('response_incomplete'); structurally_complete = False; continue
            for fmt in formats:
                if result['inspected_formats'] >= MAX_RAW_FORMATS: return hold('inventory_limit')
                result['inspected_formats'] += 1
                if not isinstance(fmt, dict): hold('malformed_format'); structurally_complete = False; continue
                if fmt.get('__yt_dlp_client', chosen_client) != chosen_client: hold('conflicting_client_inventory')
                mime = fmt.get('mimeType')
                if not isinstance(mime, str) or len(mime) > 256: hold('malformed_format'); structurally_complete = False; continue
                parts = re.fullmatch(r'(audio|video)/[A-Za-z0-9.+-]+;\s*codecs="([A-Za-z0-9., _+-]+)"', mime)
                if not parts: hold('malformed_format'); structurally_complete = False; continue
                codecs = [s.strip() for s in parts[2].split(',')]
                audio_codecs = [s for s in codecs if AUDIO_CODEC.fullmatch(s)]
                audio = parts[1] == 'audio' or bool(audio_codecs) or any(nonempty(fmt.get(k)) for k in ('audioQuality', 'audioChannels', 'audioSampleRate', 'audioTrack'))
                if not audio: continue
                itag = fmt.get('itag')
                if type(itag) is not int or not 1 <= itag <= 99999: hold('malformed_audio_itag'); continue
                drc = fmt.get('isDrc')
                if drc is not None and type(drc) is not bool: hold('malformed_drc_flag')
                is_drc = drc is True
                variant = (itag, is_drc)
                if variant in seen: hold('ambiguous_duplicate_itag')
                labels = fmt.get('audioTrack') not in (None, {}) or any(nonempty(fmt.get(k)) for k in LABEL_FIELDS) or transport_track_tags(fmt, is_drc)
                if labels: hold('track_labels_present')
                drm = nonempty(fmt.get('drmFamilies')) or nonempty(fmt.get('drmTrackType')) or fmt.get('has_drm') is True
                if drm: hold('drm_audio_alternative')
                length = fmt.get('contentLength')
                if isinstance(length, str) and re.fullmatch(r'[0-9]{1,16}', length): length = int(length)
                if type(length) is not int or not 0 < length <= 2**53: length = None
                row = {'itag': itag, 'audio_only': parts[1] == 'audio', 'is_drc': is_drc,
                    'codec': audio_codecs[0] if len(audio_codecs) == 1 else None, 'source_bytes': length,
                    'semantic_labels_present': bool(labels), 'has_drm': bool(drm),
                    'label_diagnostics': label_diagnostics(fmt)}
                result['audio_representations'].append(row)
                seen[variant] = row
    result['inspection_complete'] = structurally_complete
    if not result['inventory_responses'] or not result['audio_representations']: return hold('no_audio_inventory')
    normal = [row for row in result['audio_representations'] if not row['is_drc'] and row['audio_only']]
    if not normal: hold('no_non_drc_audio')
    for row in result['audio_representations']:
        if not row['is_drc']: continue
        base = seen.get((row['itag'], False))
        if base is None or base['audio_only'] != row['audio_only'] or base['codec'] != row['codec']:
            hold('unmatched_drc_variant')
    if result['rejection_reasons']: return result
    result.update(eligible=True, reason='provider_single_legacy_track_inference', source_language=None, source_language_status='unknown',
                  origin_inferred=True, original_explicitly_verified=False)
    safe = (json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n').encode()
    result['inventory_sha256'] = hashlib.sha256(safe).hexdigest()
    return result


def legacy_selection_proof(info, inventory):
    """Bind the selected normalized representation to the raw unlabeled source."""
    if not isinstance(inventory, dict) or inventory.get('eligible') is not True or info.get('id') != inventory.get('video_id'):
        return None
    if info.get('language_preference') != -1:
        return None
    if info.get('isDrc') is True or info.get('is_drc') is True: return None
    matches = [f for f in inventory['audio_representations'] if str(f['itag']) == info.get('format_id') and f['audio_only'] and not f.get('is_drc')]
    if len(matches) != 1 or matches[0]['codec'] != info.get('acodec'): return None
    if type(matches[0]['source_bytes']) is not int or matches[0]['source_bytes'] <= 0: return None
    if type(info.get('filesize')) is not int or info['filesize'] != matches[0]['source_bytes']: return None
    return {'basis': 'provider_single_legacy_track_inference', 'origin_basis': 'provider_single_legacy_track_inference',
        'origin_inferred': True, 'original_explicitly_verified': False, 'source_language': None,
        'source_language_status': 'unknown',
        # The pinned extractor can fill normalized audio language from captions.
        # Only the complete raw inventory establishes absence of audio labels.
        'normalized_language_used_as_audio_evidence': False,
        'language': None, 'language_preference': -1, 'original_label_present': False,
        'raw_inventory_sha256': inventory['inventory_sha256'], 'selected_itag': matches[0]['itag'],
        'selected_is_drc': False,
        'completeness_basis': inventory['completeness_basis'], 'provider_global_inventory_claimed': False}
