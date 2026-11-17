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
    'isDefault', 'isDrc', 'isVoiceBoost', 'isVb', 'xtags'}
AUDIO_CODEC = re.compile(r'^(?:mp4a\.[0-9.]+|opus|vorbis|mp3|aac)$')


def nonempty(value):
    return value is not None and value is not False and value != '' and value != {} and value != []


def transport_track_tags(fmt):
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
            if any(k.lower() in {'xtags', 'lang', 'language', 'acont', 'drc', 'vb'} and any(v) for k, v in values.items()): return True
    except ValueError: return True
    return False


def legacy_track_inventory(video_id, player_responses, chosen_client='mweb'):
    result = {'schema_version': 1, 'video_id': video_id, 'chosen_client': chosen_client,
        'eligible': False, 'reason': 'missing_raw_inventory', 'audio_representations': [],
        'context_only_responses': 0, 'inventory_responses': 0,
        'completeness_basis': 'entire_parsed_returned_client_arrays', 'provider_global_inventory_claimed': False}
    def hold(reason):
        result['reason'] = reason
        return result
    if not isinstance(player_responses, list) or not 1 <= len(player_responses) <= 16: return hold('missing_raw_inventory')
    seen = set()
    for response in player_responses:
        if not isinstance(response, dict) or not isinstance(response.get('videoDetails'), dict) or response['videoDetails'].get('videoId') != video_id:
            return hold('response_identity')
        if not isinstance(response.get('playabilityStatus'), dict) or response['playabilityStatus'].get('status') != 'OK': return hold('response_not_playable')
        if response.get('truncated') or response.get('__truncated'): return hold('response_incomplete')
        if 'streamingData' not in response: return hold('response_incomplete')
        streaming = response['streamingData']
        if streaming is None:  # pinned extractor's stripped initial caption context
            result['context_only_responses'] += 1
            continue
        if not isinstance(streaming, dict) or streaming.get('__yt_dlp_client') != chosen_client:
            return hold('conflicting_client_inventory')
        if not any(key in streaming for key in ('formats', 'adaptiveFormats')): return hold('response_incomplete')
        result['inventory_responses'] += 1
        for key in ('formats', 'adaptiveFormats'):
            formats = streaming.get(key, [])
            if not isinstance(formats, list) or len(formats) > 4096: return hold('response_incomplete')
            for fmt in formats:
                if not isinstance(fmt, dict): return hold('malformed_format')
                if fmt.get('__yt_dlp_client', chosen_client) != chosen_client: return hold('conflicting_client_inventory')
                mime = fmt.get('mimeType')
                if not isinstance(mime, str) or len(mime) > 256: return hold('malformed_format')
                parts = re.fullmatch(r'(audio|video)/[A-Za-z0-9.+-]+;\s*codecs="([A-Za-z0-9., _+-]+)"', mime)
                if not parts: return hold('malformed_format')
                codecs = [s.strip() for s in parts[2].split(',')]
                audio_codecs = [s for s in codecs if AUDIO_CODEC.fullmatch(s)]
                audio = parts[1] == 'audio' or bool(audio_codecs) or any(nonempty(fmt.get(k)) for k in ('audioQuality', 'audioChannels', 'audioSampleRate', 'audioTrack'))
                if not audio: continue
                itag = fmt.get('itag')
                if type(itag) is not int or not 1 <= itag <= 99999: return hold('malformed_audio_itag')
                if itag in seen: return hold('ambiguous_duplicate_itag')
                seen.add(itag)
                if fmt.get('audioTrack') not in (None, {}): return hold('track_labels_present')
                if any(nonempty(fmt.get(k)) for k in LABEL_FIELDS) or transport_track_tags(fmt): return hold('track_labels_present')
                if nonempty(fmt.get('drmFamilies')) or nonempty(fmt.get('drmTrackType')) or fmt.get('has_drm') is True:
                    return hold('drm_audio_alternative')
                length = fmt.get('contentLength')
                if isinstance(length, str) and re.fullmatch(r'[0-9]{1,16}', length): length = int(length)
                if type(length) is not int or not 0 < length <= 2**53: length = None
                result['audio_representations'].append({'itag': itag, 'audio_only': parts[1] == 'audio',
                    'codec': audio_codecs[0] if len(audio_codecs) == 1 else None, 'source_bytes': length})
    if not result['inventory_responses'] or not result['audio_representations']: return hold('no_audio_inventory')
    result.update(eligible=True, reason='provider_single_legacy_track_inference', source_language=None, source_language_status='unknown',
                  origin_inferred=True, original_explicitly_verified=False)
    safe = (json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n').encode()
    result['inventory_sha256'] = hashlib.sha256(safe).hexdigest()
    return result


def legacy_selection_proof(info, inventory):
    """Bind the selected normalized representation to the raw unlabeled source."""
    if not isinstance(inventory, dict) or inventory.get('eligible') is not True or info.get('id') != inventory.get('video_id'):
        return None
    if info.get('language_preference') != -1 or info.get('language') not in (None, ''):
        return None
    matches = [f for f in inventory['audio_representations'] if str(f['itag']) == info.get('format_id') and f['audio_only']]
    if len(matches) != 1 or matches[0]['codec'] != info.get('acodec'): return None
    if matches[0]['source_bytes'] is not None and info.get('filesize') != matches[0]['source_bytes']: return None
    return {'basis': 'provider_single_legacy_track_inference', 'origin_basis': 'provider_single_legacy_track_inference',
        'origin_inferred': True, 'original_explicitly_verified': False, 'source_language': None,
        'source_language_status': 'unknown',
        'language': None, 'language_preference': -1, 'original_label_present': False,
        'raw_inventory_sha256': inventory['inventory_sha256'], 'selected_itag': matches[0]['itag'],
        'completeness_basis': inventory['completeness_basis'], 'provider_global_inventory_claimed': False}
