"""Pure receipt reader for unchanged HTTPS audio with unverified track identity.

Only validates metadata from an existing strict container probe and a paired
archive. No media inspection, source, filesystem, subprocess or Drive access.
"""
import re
if __package__:
    from .qualified_edition_receipts import (ENCODING, KIND, QualifiedEdition, ReceiptHold,
        digest, encoded, file_proof, finite, identity, need, positive, proof, sha)
else:
    from qualified_edition_receipts import (ENCODING, KIND, QualifiedEdition, ReceiptHold,
        digest, encoded, file_proof, finite, identity, need, positive, proof, sha)

QUALITY_SHA = '35f5936f3b407e8de2ed5d38aa8354d518259f192d320833cf664b419c09a4db'
CONTRACT = 'direct_exact_https_audio_file'
MAX_AUDIO = 2_000_000_000


def qualification(value, video, audio, variant):
    need(type(value) is dict and value.get('contract') == CONTRACT and
         value.get('payload_encoding') == ENCODING and digest(value.get('payload_sha256')),
         'direct_qualification_contract')
    payload = value.get('payload')
    need(type(payload) is dict and sha(encoded(payload)) == value['payload_sha256'],
         'direct_qualification_hash')
    identity(payload)
    module = value.get('quality_module')
    need(type(module) is dict and module.get('sha256') == QUALITY_SHA and
         type(module.get('bytes')) is int and module['bytes'] == 4251,
         'existing_strict_probe_pin_required')
    source = proof(payload.get('source_file'), MAX_AUDIO)
    archived = proof(payload.get('archived_audio_file'), MAX_AUDIO)
    need(source == archived == audio and source['sha256'] == variant and
         payload.get('source_and_archived_audio_same_bytes') is True and
         payload.get('file_before_after_quality_equal') is True and
         payload.get('audio_reencoded') is False and payload.get('remuxed_container') is False,
         'unchanged_direct_audio_file_required')
    selection = payload.get('selection')
    need(type(selection) is dict and selection.get('video_id') == video and
         selection.get('format_id') == '140' and selection.get('protocol') == 'https' and
         selection.get('ext') == 'm4a' and selection.get('acodec') in {'mp4a.40.2', 'aac'} and
         selection.get('vcodec') == 'none' and type(selection.get('filesize')) is int and
         selection['filesize'] == source['bytes'] and finite(selection.get('duration_seconds')) and
         selection.get('live_status') in {'not_live', 'was_live'} and
         selection.get('has_drm') is False and selection.get('is_drc') is False and
         selection.get('original_audio_track_identity_verified') is False and
         selection.get('spoken_language_verified') is False and digest(selection.get('metadata_sha256')),
         'exact_qualified_audio_selection')
    http = payload.get('source_http')
    need(type(http) is dict and http.get('selected_video_id') == video and
         http.get('selected_format_id') == '140' and digest(http.get('selected_url_sha256')) and
         http.get('selected_url_sha256') == http.get('request_url_sha256') == http.get('final_url_sha256'),
         'exact_direct_response_binding')
    size = source['bytes']
    need(all(type(http.get(k)) is int and http[k] == size for k in
         ('content_length', 'received_bytes', 'written_bytes', 'exact_on_write_limit')),
         'direct_body_length')
    need(type(http.get('status')) is int and 'content_range' in http and
         (http['status'] == 200 and http['content_range'] is None or
          http['status'] == 206 and type(http['content_range']) is list and
          all(type(v) is int for v in http['content_range']) and http['content_range'] == [0, size - 1, size]),
         'direct_whole_response_extent')
    need(http.get('body_sha256') == source['sha256'] and http.get('body_complete') is True and
         http.get('headers_checked_before_sink_write') is True and
         all(type(http.get(k)) is int and http[k] == v for k, v in
             {'finished_count': 1, 'media_requests': 1, 'redirect_count': 0, 'retry_count': 0}.items()),
         'direct_whole_response_no_replay')
    scan = payload.get('strict_probe')
    need(type(scan) is dict and scan.get('quality_state') == 'complete_native_audio' and
         scan.get('strict_probe_passed') is True and scan.get('codec') == 'aac' and
         type(scan.get('audio_streams')) is int and scan['audio_streams'] == 1 and
         type(scan.get('video_streams')) is int and scan['video_streams'] == 0 and
         positive(scan.get('packet_count'), size) and
         all(scan.get(k) is False for k in ('semantic_audio_reviewed', 'human_reviewed',
             'full_speech_coverage_claimed', 'full_decode_performed')) and
         finite(scan.get('container_duration_seconds')) and finite(scan.get('source_duration_seconds')) and
         scan['source_duration_seconds'] == selection['duration_seconds'] and
         abs(scan['container_duration_seconds'] - scan['source_duration_seconds']) <=
             max(2, scan['source_duration_seconds'] * .002), 'direct_strict_container_extent')
    return payload


def validate(record, *, remote_base):
    need(type(record) is dict and type(record.get('schema_version')) is int and
         record['schema_version'] == 1 and record.get('kind') == KIND and
         record.get('status') in {'verified', 'deleted'}, 'qualified_direct_receipt_required')
    video, channel, variant = (record.get(k) for k in ('video_id', 'channel_dir', 'variant_id'))
    need(type(video) is str and re.fullmatch(r'[A-Za-z0-9_-]{11}', video) and
         type(channel) is str and re.fullmatch(r'[a-z0-9][a-z0-9-]{0,119}', channel) and
         record.get('tab') in {'videos', 'shorts', 'streams'} and digest(variant) and
         record.get('source_format_id') == '140' and digest(record.get('root_grant_sha256')),
         'qualified_direct_identity')
    identity(record)
    need(type(record.get('native_count_increment')) is int and record['native_count_increment'] == 0,
         'no_direct_native_promotion')
    audio, metadata = record.get('audio'), record.get('metadata')
    need(type(audio) is dict and type(metadata) is dict, 'paired_direct_receipts_required')
    local_audio = proof(audio.get('local_proof'), MAX_AUDIO)
    local_meta = proof(metadata.get('local_proof'), 2_000_000)
    qualification(record.get('qualification'), video, local_audio, variant)
    provenance = record.get('provenance')
    need(type(provenance) is dict and type(provenance.get('schema_version')) is int and
         provenance['schema_version'] == 1 and provenance.get('kind') == KIND and
         all(provenance.get(k) == record[k] for k in ('video_id', 'channel_dir', 'tab', 'variant_id', 'source_format_id')) and
         provenance.get('audio') == local_audio and provenance.get('qualification') == record['qualification'],
         'direct_archived_provenance_binding')
    identity(provenance)
    need(file_proof(encoded(provenance)) == local_meta, 'direct_actual_provenance_hash')
    need(type(remote_base) is str and ':' in remote_base and not remote_base.endswith('/'), 'remote_base')
    parent = f'{channel}/AudioEditions/{video}/{variant}'
    ids = []
    for part, local, leaf in ((audio, local_audio, 'audio.m4a'), (metadata, local_meta, 'provenance.json')):
        remote = part.get('remote_proof')
        need(type(remote) is dict and type(remote.get('bytes')) is int and remote['bytes'] == local['bytes'] and
             remote.get('md5') == local['md5'] and type(remote.get('drive_id')) is str and bool(remote['drive_id']) and
             remote.get('relative_path') == parent + '/' + leaf and
             remote.get('remote') == remote_base + '/' + parent + '/' + leaf and 'sha256' not in remote,
             'actual_direct_paired_remote_proof')
        ids.append(remote['drive_id'])
    need(len(set(ids)) == 2, 'distinct_direct_remote_IDs')
    return QualifiedEdition(video, channel, variant)
