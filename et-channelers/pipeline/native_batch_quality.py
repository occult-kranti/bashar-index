"""Native batch extent checks; no source access and no changes to the strict sink."""
import json
import math
import re
import subprocess
from pathlib import Path


class QualityHold(RuntimeError):
    def __init__(self, code): self.code = code; super().__init__(code)


def require(value, code):
    if not value: raise QualityHold(code)


def known_opus_warning(stderr):
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    return len(lines) == 1 and bool(re.fullmatch(r'(?:\[opus @ (?:0x)?[0-9a-fA-F]+\]\s*)?Error parsing Opus packet header\.', lines[0]))


def probe_extent(value, selected):
    streams = value.get('streams', [])
    codec = {'mp4a.40.2': 'aac', 'aac': 'aac', 'opus': 'opus'}.get(selected.get('acodec'))
    require(codec and len(streams) == 1 and streams[0].get('codec_type') == 'audio' and
            streams[0].get('codec_name') == codec, 'audio_only_probe')
    try:
        duration = float(value.get('format', {}).get('duration') or streams[0].get('duration'))
        packets = int(streams[0].get('nb_read_packets', 0))
        expected = float(selected['duration'])
    except (ValueError, TypeError, KeyError): raise QualityHold('audio_extent') from None
    require(packets > 0 and math.isfinite(duration) and duration > 0 and
            math.isfinite(expected) and expected > 0 and abs(duration - expected) <= max(2, expected * .002), 'audio_extent')
    return {'codec': codec, 'packet_count': packets, 'container_duration_seconds': duration,
            'source_duration_seconds': expected, 'audio_streams': 1, 'video_streams': 0}


def inspect_quality(path, selected, ffprobe, ffmpeg, guard=lambda: None, *, run=subprocess.run):
    """One packet scan; the one known Opus warning needs a full decode too."""
    guard()
    scan = run([str(ffprobe), '-v', 'error', '-count_packets', '-show_entries',
        'stream=codec_type,codec_name,nb_read_packets,duration:format=duration', '-of', 'json', str(path)],
        capture_output=True, text=True, timeout=1800, check=False)
    guard()
    require(scan.returncode == 0, 'audio_probe_failed')
    try: proof = probe_extent(json.loads(scan.stdout), selected)
    except (ValueError, TypeError): raise QualityHold('audio_probe_invalid') from None
    base = {'accuracy': 'unreviewed', 'semantic_audio_reviewed': False, 'human_reviewed': False,
            'full_speech_coverage_claimed': False, **proof}
    if not scan.stderr.strip():
        return dict(base, quality_state='complete_native_audio', strict_probe_passed=True,
                    clean_decode=None, full_decode_performed=False)
    require(proof['codec'] == 'opus' and known_opus_warning(scan.stderr), 'codec_warning_unrecognized')
    require(type(selected.get('filesize')) is int and selected['filesize'] == Path(path).stat().st_size > 0,
            'warning_exact_source_size_required')
    require(abs(proof['container_duration_seconds'] - proof['source_duration_seconds']) <= 2, 'warning_source_extent')
    decode = run([str(ffmpeg), '-v', 'error', '-nostdin', '-err_detect', 'explode', '-threads', '1',
        '-i', str(path), '-map', '0:a:0', '-vn', '-sn', '-dn', '-progress', 'pipe:1', '-nostats',
        '-f', 'null', '-'], capture_output=True, text=True,
        timeout=max(120, proof['source_duration_seconds']), check=False)
    guard()
    require(decode.returncode == 0 and (not decode.stderr.strip() or known_opus_warning(decode.stderr)), 'warning_decode_failed')
    progress = dict(line.split('=', 1) for line in decode.stdout.splitlines() if '=' in line)
    try: end = int(progress['out_time_us']) / 1_000_000
    except (KeyError, ValueError): raise QualityHold('warning_decode_extent') from None
    require(progress.get('progress') == 'end' and abs(end - proof['source_duration_seconds']) <= 2 and
            abs(end - proof['container_duration_seconds']) <= 2, 'warning_decode_extent')
    return dict(base, quality_state='complete_with_codec_warning', strict_probe_passed=False, clean_decode=False,
                full_decode_performed=True, decode_exit_code=0, decode_end_seconds=end,
                warning='single_opus_packet_header_warning', warning_other_errors=False,
                exact_declared_source_bytes=selected['filesize'])
