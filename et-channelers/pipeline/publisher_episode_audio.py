"""Validate an MP3 podcast enclosure, including optional embedded cover artwork."""
from math import isfinite


def compare_feed_extent(*, advertised_bytes, delivered_bytes, advertised_seconds,
                        measured_seconds, bitrate, http_length):
    """Compare a complete HTTP enclosure with its feed's advertised edition.

    Some podcast hosts serve a longer MP3 at the exact enclosure URL. Its
    additional MPEG frames should account for the additional delivered bytes
    at the observed audio bitrate. This cannot identify their spoken content.
    """
    if any(type(n) is not int or n <= 0 for n in (advertised_bytes, delivered_bytes, bitrate)):
        raise ValueError('Missing positive enclosure lengths or bitrate')
    if (any(isinstance(n, bool) or not isinstance(n, (int, float)) or not isfinite(n) or n <= 0
            for n in (advertised_seconds, measured_seconds)) or http_length != delivered_bytes):
        raise ValueError('Missing complete HTTP extent or measured episode duration')
    extra_seconds = measured_seconds - advertised_seconds
    if abs(extra_seconds) <= 3:
        return {'basis': 'advertised_duration', 'extra_seconds': extra_seconds}
    extra_bytes = delivered_bytes - advertised_bytes
    byte_seconds = extra_bytes * 8 / bitrate
    if extra_bytes <= 0 or extra_seconds <= 0 or abs(byte_seconds - extra_seconds) > max(3, extra_seconds * .025):
        raise ValueError('Delivered MP3 size and duration differ from the feed without a matching extent')
    return {'basis': 'longer_publisher_enclosure', 'extra_seconds': extra_seconds,
            'extra_bytes': extra_bytes, 'seconds_from_extra_bytes': byte_seconds, 'bitrate': bitrate}


def inspect_mp3_episode(document, expected_seconds, tolerance_seconds=3):
    streams = document.get('streams', [])
    audio = [stream for stream in streams if stream.get('codec_type') == 'audio']
    if len(audio) != 1 or audio[0].get('codec_name') != 'mp3':
        raise ValueError('Expected exactly one MP3 audio program')
    artwork = []
    for stream in streams:
        if stream is audio[0]:
            continue
        if (stream.get('codec_type') != 'video' or stream.get('disposition', {}).get('attached_pic') != 1 or
                stream.get('codec_name') not in {'mjpeg','png','webp','bmp','gif','tiff','jpeg2000'} or
                str(stream.get('nb_read_packets', 1)) != '1'):
            raise ValueError('Additional stream is not a single declared cover picture')
        artwork.append(stream['codec_name'])
    track = audio[0]
    rate = int(track['sample_rate'])
    packets = int(track['nb_read_packets'])
    channels = int(track['channels'])
    if rate <= 0 or packets <= 0 or channels not in (1, 2) or expected_seconds <= 0:
        raise ValueError('Invalid MP3 program extent')
    seconds = packets * (1152 if rate >= 32000 else 576) / rate
    declared = track.get('duration')
    if abs(seconds - expected_seconds) >= tolerance_seconds:
        raise ValueError('MP3 packet duration differs from publisher episode')
    if declared not in (None, 'N/A') and (not isfinite(float(declared)) or abs(float(declared) - expected_seconds) >= tolerance_seconds):
        raise ValueError('Reported audio duration differs from publisher episode')
    return {'codec':'mp3','packets':packets,'sample_rate':rate,'channels':channels,'seconds':seconds,'attached_cover_art_codecs':artwork}


def compare_mp3_feed_extent(*, advertised_bytes, delivered_bytes, advertised_seconds,
                            measured_seconds, bitrate, http_length, delivered_id3_bytes):
    """Exclude the delivered MP3's parsed ID3 bytes from its audio extent.

    The HTTP length still binds the entire received object. A publisher may
    replace its ID3 artwork as well as insert audio after producing the RSS.
    The original comparator and its callers retain their existing semantics.
    RSS metadata size is unknown; its rounding/header difference must still
    fit the original comparator's finite tolerance.
    """
    if (type(delivered_bytes) is not int or delivered_bytes <= 0 or
            http_length != delivered_bytes or type(delivered_id3_bytes) is not int or
            not 0 <= delivered_id3_bytes < min(delivered_bytes, 5_000_001)):
        raise ValueError('Missing full HTTP extent or bounded parsed ID3 length')
    audio_extent = delivered_bytes - delivered_id3_bytes
    normalized = compare_feed_extent(advertised_bytes=advertised_bytes,
        delivered_bytes=audio_extent, advertised_seconds=advertised_seconds,
        measured_seconds=measured_seconds, bitrate=bitrate, http_length=audio_extent)
    return {**normalized, 'metadata_accounting': 'delivered_parsed_id3_excluded_from_audio_extent',
            'delivered_object_bytes': delivered_bytes, 'http_length': http_length,
            'delivered_id3_bytes': delivered_id3_bytes, 'delivered_audio_extent_bytes': audio_extent,
            'advertised_metadata_bytes': None}
