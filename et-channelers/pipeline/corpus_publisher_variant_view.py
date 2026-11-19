"""Read verified publisher-edition transcripts and independent timed-text batches offline."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
import math
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from . import (common, corpus_asr_view as asr, corpus_caption_view as captions, gpu_asr,
               ingestion_status as status, publisher_caption_batch, publisher_mirror, youtube_captions)

PROOF = ('bytes','md5','sha256','drive_id','remote')
FOLDERS = {'videos':'Videos','shorts':'Shorts','streams':'Streams'}
SCHEMA = 1
ASR = 'publisher_variant_asr'
CAPTION = 'standalone_publisher_caption'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _fingerprint(record):
    return _hash(publisher_mirror.encoded(record))


def _proof(left, right):
    return status.publisher_object_proof(left) and status.publisher_object_proof(right) and all(left[k] == right[k] for k in PROOF)


def _source_method(edition, row, remote):
    video, creator, tab = row['video_id'], row['channel_dir'], row['tab']
    audio, meta = edition.get('audio'), edition.get('provenance')
    need(tab in FOLDERS and status.record_row(row) and edition.get('schema_version') == 1
         and edition.get('status') == 'verified' and edition.get('channel_dir') == creator
         and edition.get('native_youtube_bytes') is False and edition.get('changes_native_audio_count') is False
         and status.publisher_object_proof(audio) and status.publisher_object_proof(meta)
         and audio['drive_id'] != meta['drive_id'], 'unverified publisher source objects')
    parent = f"{remote}/{creator}/{FOLDERS[tab]}/{video}/PublisherVariants/{audio['sha256']}"
    need(re.fullmatch(re.escape(parent) + r'/publisher-audio\.(?:mp3|m4a|aac|opus|ogg|flac|webm)', audio['remote'])
         and meta['remote'] == parent+'/provenance.json', 'publisher source is stored under a different edition')
    kind = edition.get('artifact_kind')
    if kind in ('publisher_podcast_audio_variant','qualified_publisher_podcast_audio_variant'):
        need(edition.get('video_id') == video and tab == 'videos' and edition.get('changes_full_asr_count') is False
             and audio.get('kind') == kind and audio['remote'].endswith('.mp3'), 'legacy publisher recording identity')
        if kind == 'qualified_publisher_podcast_audio_variant':
            need(edition.get('identity_basis') == 'publisher_rss_source_id_references' and edition.get('direct_watch_link_present') is False
                 and edition.get('association_human_verified') is False and meta.get('kind') == 'qualified_publisher_variant_provenance',
                 'unproven legacy qualification')
            return 'publisher_rss_source_id_references'
        need(meta.get('kind') == 'publisher_podcast_variant_provenance','unverified publisher episode provenance')
        return 'official_video_page_embeds_youtube_id_and_feed_links_page'
    method = edition.get('association_method')
    need(edition.get('associated_youtube_id') == video and edition.get('variant_id') == audio['sha256']
         and edition.get('source_tab',edition.get('tab',tab)) == tab and edition.get('kind') == publisher_mirror.kind_for(edition)
         and all(edition.get(k) is False for k in publisher_mirror.NATIVE_FLAGS), 'publisher mirror association is unproven')
    if method == 'publisher_rss_exact_youtube_id' and edition.get('exact_youtube_crossreference') is True:
        publisher_mirror.exact_youtube_link(edition.get('original_youtube_link'), video)
    else:
        need(method == 'publisher_owner_title_date_duration' and edition.get('exact_youtube_crossreference') is False,
             'unsupported publisher selection identity')
    return method


def _asr_source(record, edition, row, remote):
    method = _source_method(edition,row,remote)
    run, variant = record.get('run_id',''), record.get('variant_id')
    audio, meta = edition['audio'], edition['provenance']
    need(re.fullmatch(r'asr-[a-f0-9]{24}',run) and record.get('schema_version') == 1 and record.get('status') == 'verified'
         and record.get('artifact_kind') == ASR and record.get('quality_state') == 'unreviewed_asr'
         and record.get('associated_youtube_id') == row['video_id'] and record.get('channel_dir') == row['channel_dir']
         and variant == audio['sha256'] and _proof(record.get('source_audio'),audio) and _proof(record.get('source_provenance'),meta)
         and status.publisher_object_proof(record) and len({record['drive_id'],audio['drive_id'],meta['drive_id']}) == 3
         and record['remote'] == audio['remote'].rpartition('/')[0] + f'/ASR/{run}/{run}.zip'
         and all(record.get(k) is False for k in ('native_youtube_bytes','changes_native_audio_count','changes_native_asr_count')),
         'publisher ASR receipt is not bound to this recording and source pair')
    source = record.get('source_variant',{})
    need(source.get('variant_id') == variant and source.get('associated_youtube_id') == row['video_id']
         and source.get('channel_dir') == row['channel_dir'] and source.get('native_youtube_bytes') is False
         and source.get('source_kind') == 'publisher_audio_variant', 'publisher ASR source identity mismatch')
    association = source.get('association', {})
    if method == 'official_video_page_embeds_youtube_id_and_feed_links_page':
        need(association.get('exact_youtube_id_linked_on_page') is True, 'legacy page does not establish episode identity')
    elif method == 'publisher_rss_source_id_references':
        need(association.get('identity_basis') == method and association.get('direct_watch_link_present') is False,
             'legacy episode is only qualified by publisher references')
    else:
        need(association.get('association_method') == method and association.get('recording_equivalence_verified') is False
             and association.get('exact_youtube_crossreference') is edition.get('exact_youtube_crossreference'),
             'ASR source association contradicts publisher acquisition')
    return method


def _caption_item(record, item, row, remote):
    video, creator = row['video_id'], row['channel_dir']
    bundle = record.get('proof',{})
    need(status.record_row(row) and row['tab'] in FOLDERS and record.get('schema_version') == 1 and record.get('status') == 'verified'
         and status.publisher_object_proof(bundle) and bundle['remote'] == f"{remote}/{creator}/PublisherCaptions/Batches/{bundle['sha256']}/publisher-captions.zip"
         and item.get('video_id') == video and item.get('channel_dir') == creator and item.get('tab') == row['tab']
         and item.get('audio_binding') is None and all(item.get(k) is False for k in ('native_youtube_caption','recording_equivalence_verified','speech_coverage_verified'))
         and all(record.get(k) is False for k in ('changes_native_audio_count','changes_full_asr_count'))
         and re.fullmatch(r'[a-f0-9]{64}',str(item.get('source_sha256'))) and type(item.get('source_bytes')) is int and item['source_bytes'] > 0
         and type(item.get('segment_count')) is int and item['segment_count'] > 0, 'unverified standalone publisher caption')
    if record.get('artifact_kind') == 'publisher_edition_caption_batch':
        need(publisher_caption_batch.verified_videos({**record,'items':[item]}, {video},remote,{video:(creator,row['tab'])}) == {video}
             and all(not row.get(key) or row[key] == item['selected_channel_id']
                     for key in ('expected_channel_id', 'channel_id')), 'unverified Rumble public caption association')
        return item['publisher_watch_url'], item['track_key']
    need(record.get('artifact_kind') == 'publisher_provided_timed_text_batch' and item.get('language_basis') == 'publisher_rss_channel'
         and re.fullmatch(r'en(?:-[A-Za-z]{2,8})?',str(item.get('language'))) and item.get('track_language_verified') is False
         and item.get('caption_kind') == 'publisher_provided_unspecified' and item.get('translation_status') == 'not_declared'
         and item.get('association_basis') in ('official_blog_exact_video_reference_plus_same_publisher_guest_topic_date_and_duration',
                                              'official_blog_exact_youtube_reference_plus_publisher_episode_identity'), 'unrecognized RSS-declared caption')
    publisher_mirror.exact_youtube_link(item.get('official_blog_youtube_reference'),video)
    site = urlsplit(item.get('official_blog_url',''))
    source = urlsplit(item.get('source_url',''))
    episode = re.fullmatch(r'/\d+/(\d+)/transcript\.vtt',source.path)
    need(site.scheme == 'https' and site.hostname and not site.username and not site.password and source.netloc == 'www.buzzsprout.com'
         and source.scheme == 'https' and not source.query and not source.fragment and episode
         and item.get('publisher_episode_guid') == 'Buzzsprout-'+episode[1], 'RSS host and publisher transcript GUID disagree')
    return item['source_url'], item['language']


def input_rows(root, frame, remote=status.DEFAULT_REMOTE):
    """Yield distinct eligible archive inputs; support duplicate acquisition/retirement journal lines."""
    root = Path(root)
    rows = {r['video_id']:r for r in frame}
    sources, seen = {}, set()
    for name in ('publisher_variant_manifest.jsonl','publisher_mirror_manifest.jsonl'):
        for rec in common.read_jsonl(root/'sync'/name):
            video = rec.get('associated_youtube_id') or rec.get('video_id')
            if video in rows and isinstance(rec.get('audio'),dict):
                sources.setdefault((video,rec['audio'].get('sha256')),[]).append(rec)
    for rec in common.read_jsonl(root/'sync/publisher_variant_asr_manifest.jsonl'):
        video = rec.get('associated_youtube_id')
        for source in sources.get((video,rec.get('variant_id')),[]):
            try:
                _asr_source(rec,source,rows[video],remote)
            except (ValueError,TypeError,KeyError):
                continue
            key = (ASR,video,rec['sha256'])
            if key not in seen:
                seen.add(key)
                yield {'kind':ASR,'row':rows[video],'record':rec,'edition':source,'proof':rec,'track_id':rec['run_id']}
            break
    for rec in common.read_jsonl(root/'sync/publisher_caption_manifest.jsonl'):
        for item in rec.get('items',[]) if isinstance(rec.get('items'),list) else ():
            video = item.get('video_id') if isinstance(item,dict) else None
            if video not in rows:
                continue
            try:
                url, track = _caption_item(rec,item,rows[video],remote)
            except (ValueError,TypeError,KeyError):
                continue
            key = (CAPTION,video,url,track,item['source_sha256'])
            if key not in seen:
                seen.add(key)
                yield {'kind':CAPTION,'row':rows[video],'record':rec,'proof':rec['proof'],'item':item,'track_id':track}


def local_bundle(root, job):
    if job['kind'] != ASR:
        return None
    base = Path(root).resolve()
    record = job['record']
    run, variant = record['run_id'], record['variant_id']
    need(re.fullmatch(r'asr-[a-f0-9]{24}',run) and re.fullmatch(r'[a-f0-9]{64}',variant),'invalid publisher ASR local key')
    for path in (base/'asr/results').glob(f'publisher*/publisher-{variant}/{run}/{run}.zip'):
        if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(base):
            return path
    return None


def _asr_views(path, job, remote):
    record, edition, row = job['record'], job['edition'], job['row']
    method = _asr_source(record,edition,row,remote)
    paired, proof, parts = asr._parts(path, {'bundle':record,'output_contract':record.get('output_contract')})
    p = proof['provenance']
    source = record['source_audio']
    model, language = p.get('model',{}), record.get('language_evidence',{})
    need(p.get('source_kind') == 'publisher_audio_variant' and p.get('source_video_id') == 'publisher-'+source['sha256']
         and p.get('channel_dir') == row['channel_dir'] and p.get('associated_youtube_id') == row['video_id']
         and all(record.get(k) is not None and p.get(k) == record[k] for k in ('run_id','source_lease_id','source_variant','variant_id','model','metrics','language_evidence'))
         and _proof(p.get('source_audio'),source) and _proof(p.get('source_metadata'),record['source_provenance'])
         and p['run_id'] == 'asr-'+gpu_asr.fingerprint(p.get('identity',{}))[:24]
         and p['identity'].get('source_audio') == p['source_audio'] and p['identity'].get('source_metadata') == p['source_metadata']
         and p['identity'].get('source_variant') == p['source_variant'] and p['identity'].get('model') == model
         and re.fullmatch('[a-f0-9]{64}',str(model.get('model_sha256'))) and re.fullmatch('[a-f0-9]{40}',str(model.get('revision')))
         and all(p.get(k) is False for k in ('changes_native_audio_count','changes_native_asr_count','native_youtube_bytes'))
         and all(p.get('quality',{}).get(k) is False for k in ('accuracy_claimed','human_reviewed','speech_coverage_validated','native_youtube_alignment_validated'))
         and language.get('scope') == 'publisher_rss_channel_declaration' and language.get('native_youtube_language_asserted') is False,
         'archived publisher ASR provenance or recording binding changed')
    duration = p['metrics'].get('audio_seconds')
    need(type(duration) in (int,float) and math.isfinite(duration) and duration>0, 'invalid publisher ASR duration')
    if paired:
        variants = p.get('text_variants')
        need(p.get('quality_state') == 'unreviewed_asr' and p.get('profile') == record.get('profile')
             and p.get('output_contract') == record.get('output_contract') and variants == record.get('text_variants')
             and isinstance(variants,dict) and set(variants) == {'original','english'}
             and proof['artifact_manifest_sha256'] == record.get('artifact_manifest_sha256'), 'invalid paired publisher ASR receipt')
    else:
        need(p.get('status') == 'local_transcription_complete_unreviewed' and p.get('config',{}).get('task') == 'transcribe'
             and p['config'].get('language') == 'en' and p['identity'].get('config') == p['config']
             and str(language.get('code','')).lower().split('-')[0] == 'en', 'unverified original English publisher transcription')
        variants = {'english':{'text_kind':'original_asr','language':'en'}}
    views = {}
    for key, variant in variants.items():
        alias = paired and key == 'english' and variant.get('same_as') == 'original'
        member_key = 'original' if alias else key
        prefix = member_key+'/' if paired else ''
        name = prefix+'segments.json'
        document, raw_text = json.loads(parts[name]), parts[prefix+'transcript.txt']
        text = raw_text.decode('utf-8')
        segments = asr._segments(document,text,variant['language'],duration)
        translated = variant['text_kind'] == 'english_audio_translation'
        if alias:
            need(variants['original']['language'] == variant['language'] == 'en'
                 and variant['text_kind'] == 'original_english_alias' and variant.get('translation_performed') is False
                 and variant['text_sha256'] == _hash(raw_text) and variant['segments_sha256'] == _hash(parts[name]),
                 'invalid English publisher transcript alias')
        elif paired:
            need(variant['text_sha256'] == _hash(raw_text) and variant['segments_sha256'] == _hash(parts[name])
                 and variant.get('config',{}).get('task') == ('translate' if translated else 'transcribe')
                 and variant['config'].get('language') == variants['original']['language'] and (key=='english') == translated,
                 'publisher ASR task/language or text member changed')
        spans = [{'cue_index':i,'char_start':s['char_start'],'char_end':s['char_end'],
                  'source_segment_id':f"{name}:{s['id']}",'raw_segment_id':s['id'],'source_member':name,
                  'time_start':s['start'],'time_end':s['end'],'words':deepcopy(s.get('words',[]))} for i,s in enumerate(segments)]
        views[key] = {'schema_version':SCHEMA,'video_id':row['video_id'],'channel_dir':row['channel_dir'],
            'run_id':p['run_id'],'track_id':'publisher-asr:'+p['run_id']+':'+key,'variant':key,
            'source_kind':'publisher_english_audio_translation' if translated else 'publisher_original_asr',
            'text_kind':variant['text_kind'],'language':variant['language'],'original_language':variants.get('original',variant)['language'],
            'same_text_as_variant':'original' if alias else None,
            'language_evidence':language,'translation_performed':translated,'translation_semantics_verified':False,
            'text_version_id':_hash(f"publisher-asr-v{SCHEMA}|{record['sha256']}|{name}".encode()),
            'bundle_sha256':record['sha256'],'raw_sha256':_hash(parts[name]),'text_sha256':_hash(raw_text),
            'text':text,'segments':spans,'offset_unit':'unicode_codepoint','source_timebase':'publisher_audio_seconds',
            'duration_seconds':duration,'source_edition_id':'sha256:'+source['sha256'],'source_audio_sha256':source['sha256'],
            'source_audio_drive_id':source['drive_id'],'source_metadata_sha256':record['source_provenance']['sha256'],
            'edition_receipt_sha256':_fingerprint(edition),'asr_receipt_sha256':_fingerprint(record),
            'artifact_manifest_sha256':proof['artifact_manifest_sha256'],'quality_state':'unreviewed_asr',
            'known_cue_union_seconds':captions.timed_union(segments),'cues_without_end':0,
            'recording_association_method':method,'recording_equivalence_verified':False,'native_youtube_alignment_verified':False,
            'speech_coverage_verified':False,'speaker_attribution':None,'human_reviewed':False}
    return views


def _caption_parts(path, bundle):
    size = bundle['bytes']
    need(type(size) is int and 0<size<=captions.MAX_ARCHIVE, 'invalid publisher caption archive size')
    with Path(path).open('rb') as f:
        raw = f.read(size+1)
    need(len(raw)==size and _hash(raw)==bundle['sha256'] and hashlib.md5(raw).hexdigest()==bundle['md5'],
         'publisher caption ZIP does not match its archived receipt')
    with ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        need(0<len(infos)<=2048 and len(set(archive.namelist())) == len(infos)
             and sum(i.file_size for i in infos)<=captions.MAX_EXPANDED, 'duplicate or oversized caption ZIP members')
        parts = {}
        for i in infos:
            need(not i.flag_bits&1 and stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG)
                 and i.compress_type in (ZIP_STORED,ZIP_DEFLATED) and re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', i.filename)
                 and all(x not in ('.','..') for x in i.filename.split('/')), 'unsafe publisher caption ZIP member')
            parts[i.filename] = archive.read(i)
    if 'manifest.json' in parts:
        manifest=json.loads(parts.pop('manifest.json'))
        need(isinstance(manifest,dict) and set(manifest)==set(parts) and all(isinstance(m,dict) and m.get('bytes')==len(parts[n])
             and m.get('sha256')==_hash(parts[n]) and m.get('md5')==hashlib.md5(parts[n]).hexdigest() for n,m in manifest.items()),
             'publisher caption archive manifest mismatch')
    else:
        checksums=parts.pop('SHA256SUMS.txt',b'')
        expected=''.join(_hash(data)+'  '+name+'\n' for name,data in sorted(parts.items())).encode()
        need(checksums==expected,'publisher caption SHA256SUMS mismatch')
    return parts


def _caption_view(path, job, remote):
    record,item,row=job['record'],job['item'],job['row']
    need(item in record.get('items',[]),'publisher caption item is absent from its batch')
    url,track = _caption_item(record,item,row,remote)
    parts=_caption_parts(path,record['proof'])
    rumble=record['artifact_kind']=='publisher_edition_caption_batch'
    if rumble:
        prefix = f"{row['video_id']}/{item['publisher_watch_id']}/{track}/"
    else:
        prefix = row['video_id']+'/' if row['video_id']+'/publisher.vtt' in parts else ''
        need(bool(prefix) or len(record['items']) == 1, 'shared publisher archive has no item-specific member')
    raw=parts[prefix+'publisher.vtt']
    segments=json.loads(parts[prefix+'segments.json'])
    provenance=json.loads(parts[prefix+'provenance.json'])
    need(_hash(raw)==item['source_sha256'] and len(raw)==item['source_bytes'],'original publisher VTT length or SHA mismatch')
    normalized=youtube_captions.normalize_caption(raw,'vtt')
    need(len(normalized['segments'])==item['segment_count'] and normalized['text'].strip(),'publisher VTT cue count mismatch')
    if rumble:
        need(provenance==item and segments==normalized['segments'] and parts[prefix+'transcript.en.txt']==normalized['text'].encode()
             and len(normalized['text'].split())==item['word_count']
             and normalized['segments'][0]['start']==item['first_cue_start'] and normalized['segments'][-1]['end']==item['last_cue_end'],
             'publisher caption text or source-edition proof changed')
    elif prefix:
        need(provenance.get('item')==item and segments==normalized,'publisher episode-catalog item or normalized cues changed')
    else:
        need(provenance.get('associated_youtube_id')==row['video_id'] and provenance.get('publisher_episode_guid')==item['publisher_episode_guid']
             and provenance.get('source_sha256')==item['source_sha256'] and provenance.get('source_url')==url
             and provenance.get('source_audio_binding') is None and segments==normalized,'publisher stand-alone transcript provenance changed')
    raw_proof={'bytes':len(raw),'md5':hashlib.md5(raw).hexdigest(),'sha256':_hash(raw)}
    content=captions.text_content({'raw.vtt':raw,'segments.json':json.dumps(normalized).encode(),'transcript.txt':normalized['text'].encode()},
                                  'vtt',raw_proof,normalized['normalization_version'])
    return {'schema_version':SCHEMA,'video_id':row['video_id'],'channel_dir':row['channel_dir'],'source_kind':'standalone_publisher_caption',
            'track_id':track,'caption_kind':item['caption_kind'],'language':item['language'],
            'language_evidence':({'basis':'publisher_labels_original_English_track','label':item['caption_label'],'track_key':track} if rumble else
                {'basis':'publisher_rss_channel','track_language_verified':False,'translation_status':'not_declared','authorship':'not_declared'}),
            'source_edition_id':'publisher:'+_hash(url.encode()),'source_audio_sha256':None,'source_timebase':'publisher_caption_seconds',
            'text_version_id':_hash(f"standalone-publisher-caption-v{SCHEMA}|{url}|{item['source_sha256']}".encode()),
            'bundle_sha256':record['proof']['sha256'],'edition_receipt_sha256':_fingerprint(item),
            'recording_association_method':item.get('association_method') or item['association_basis'],
            'recording_equivalence_verified':False,'native_youtube_alignment_verified':False,**content}


def text_views(path, job, remote=status.DEFAULT_REMOTE):
    """Validate an explicitly supplied ZIP and derive versioned, publisher-timebase text views."""
    if job['kind'] == ASR:
        return _asr_views(path,job,remote)
    need(job['kind']==CAPTION,'unsupported publisher text source')
    return {'caption':_caption_view(path,job,remote)}
