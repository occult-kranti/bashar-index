"""Validate timed captions archived separately from a selected recording's audio."""
import datetime as dt
from html import unescape
import math
import re
import unicodedata
from urllib.parse import urlsplit


RSS_ENGLISH_BATCH = 'declared_rss_english_caption_batch'
RSS_ENGLISH_BASIS = 'english_publisher_feed_plus_actual_common_words'
ENGLISH_COMMON_WORDS = frozenset('the and you is it of to what that this with for we have are our your'.split())


def cue_language_evidence(text):
    words = re.findall(r'[a-z]+', text.casefold())
    return {'basis': RSS_ENGLISH_BASIS, 'all_word_count': len(words),
            'english_common_words': sum(word in ENGLISH_COMMON_WORDS for word in words),
            'different_common_words': len(set(words) & ENGLISH_COMMON_WORDS)}


def confirmed_english_cues(evidence):
    if not isinstance(evidence, dict) or evidence.get('basis') != RSS_ENGLISH_BASIS:
        return False
    words, common, distinct = (evidence.get(key) for key in
                              ('all_word_count', 'english_common_words', 'different_common_words'))
    return (all(type(n) is int for n in (words, common, distinct)) and words > 25
            and 9 <= distinct <= len(ENGLISH_COMMON_WORDS) and distinct <= common <= words and common / words > .1)


def rss_edition(item):
    """Validate the publisher's declared episode, recording association and independently measured language."""
    if not isinstance(item, dict) or item.get('provider') != 'Buzzsprout':
        return False
    guid, show, video = item.get('episode_guid'), item.get('show_id'), item.get('video_id')
    if not (isinstance(guid, str) and re.fullmatch(r'Buzzsprout-[0-9]+', guid)
            and isinstance(show, str) and re.fullmatch(r'[0-9]+', show) and isinstance(video, str)
            and re.fullmatch(r'[A-Za-z0-9_-]{11}', video)):
        return False
    url = f"https://www.buzzsprout.com/{show}/{guid.split('-')[1]}/transcript.vtt"
    http = item.get('raw_http_proof') or {}
    file = http.get('proof') if isinstance(http, dict) else None
    if not (isinstance(http, dict) and isinstance(file, dict) and item.get('source_url') == http.get('origin_url') == url
            and http.get('status') == 200 and http.get('observed_eof') is True
            and file.get('bytes') == item.get('source_bytes') and file.get('sha256') == item.get('source_sha256')
            and re.fullmatch(r'[a-f0-9]{32}', str(file.get('md5'))) and sha256_string(item.get('publisher_feed_sha256'))
            and sha256_string(item.get('source_sha256')) and sha256_string(item.get('selection_sha256'))
            and isinstance(item.get('show_name'), str) and item['show_name'].strip()
            and re.fullmatch(r'en(?:-[a-z0-9]+)*', str(item.get('show_language','')), re.I)
            and item.get('language') == 'en' and confirmed_english_cues(item.get('language_evidence'))
            and item.get('declared_mime_type') == 'text/vtt' and item.get('source_format') == 'vtt'
            and item.get('caption_kind') == 'publisher_provided_unspecified' and item.get('translation_status') == 'not_declared'
            and item.get('source_timebase') == 'publisher_episode_seconds' and item.get('original_clock_retained') is True
            and 'source_audio_sha256' in item and item['source_audio_sha256'] is None
            and all(item.get(k) is False for k in ('native_youtube_caption','youtube_edit_equivalence_verified',
                                                    'youtube_time_alignment_verified','speech_coverage_verified'))):
        return False
    extent, listed, delta, start, end = (item.get(k) for k in
        ('publisher_duration_s', 'youtube_duration_s', 'difference_seconds', 'first_cue_start', 'last_cue_end'))
    if not (all(type(x) in (int, float) and math.isfinite(x) for x in (extent, listed, delta, start, end)) and min(extent,listed) > 0
            and delta == abs(extent-listed) and 0 <= start < end <= extent + 6
            and type(item.get('segment_count')) is int and item['segment_count'] > 5
            and type(item.get('source_bytes')) is int and 0 < item['source_bytes'] <= 750_000):
        return False
    refs = item.get('episode_youtube_references')
    if not isinstance(refs, list) or not all(isinstance(i,str) and re.fullmatch(r'[A-Za-z0-9_-]{11}', i) for i in refs):
        return False
    if item.get('association_method') == 'publisher_episode_exact_youtube_reference':
        return item.get('exact_youtube_crossreference') is True and video in refs
    try:
        published = dt.date.fromisoformat(item['publisher_date'])
        youtube = dt.date.fromisoformat(item['youtube_publication_date'])
    except (KeyError, ValueError, TypeError):
        return False
    return (item.get('association_method') == 'publisher_owner_title_date_duration'
            and item.get('exact_youtube_crossreference') is False and video not in refs
            and item.get('same_normalized_title') is True and bool(title_words(item.get('youtube_title')))
            and title_words(item.get('youtube_title')) == title_words(item.get('episode_title'))
            and abs((published-youtube).days) <= 2 and delta <= 8)


def sha256_string(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def title_words(value):
    if not isinstance(value, str):
        return []
    title = unescape(unicodedata.normalize('NFKC', value)).casefold().split('#', 1)[0]
    return re.findall(r'\w+', title)


def rumble_edition(item):
    if (item.get('provider') != 'Rumble' or item.get('declared_downloadable') is not True
            or item.get('association_method') != 'same_publisher_normalized_title_date_and_duration'):
        return False
    watch_id, embed_id = item.get('publisher_watch_id'), item.get('publisher_embed_id')
    if not all(isinstance(x, str) and re.fullmatch('v[a-z0-9]+', x) for x in (watch_id, embed_id)):
        return False
    account, watch = item.get('publisher_account'), item.get('publisher_watch_url')
    if not all(isinstance(x, str) for x in (account, watch)):
        return False
    try:
        channel, page = urlsplit(account), urlsplit(watch)
        published = dt.datetime.fromisoformat(item['publisher_date'].replace('Z', '+00:00'))
        if not published.tzinfo:
            return False
        if item.get('listed_upload_date'):
            listed = dt.date.fromisoformat(item['listed_upload_date'])
            if abs((listed - published.date()).days) > 3:
                return False
    except (AttributeError, KeyError, TypeError, ValueError):
        return False
    if (any(p.scheme != 'https' or p.netloc not in {'rumble.com', 'www.rumble.com'} or p.query or p.fragment
            for p in (channel, page))
            or not re.fullmatch(r'/(?:user/|c/)?[A-Za-z0-9_-]+/?', channel.path)
            or not re.fullmatch('/' + watch_id + r'-[^/]+\.html', page.path)):
        return False
    title = title_words(item.get('selected_title'))
    seconds, publisher_seconds = item.get('selected_duration_s'), item.get('publisher_duration_s')
    documents = item.get('source_documents')
    return (bool(title) and title == title_words(item.get('publisher_title'))
            and all(type(n) is int and n > 0 for n in (seconds, publisher_seconds))
            and abs(seconds - publisher_seconds) <= 1 and isinstance(documents, dict)
            and all(sha256_string(documents.get(k)) for k in ('listing', 'watch', 'embed')))


def english_track(item):
    language, key = item.get('language'), item.get('track_key')
    label = item.get('caption_label')
    if (language != 'en' or not isinstance(key, str) or not isinstance(label, str)
            or 'translat' in label.casefold() or 'english' not in label.casefold()):
        return False
    if key == 'en-auto':
        return item.get('caption_kind') == 'automatic_original' and 'auto' in label.casefold()
    return (re.fullmatch('en(?:[-_][A-Za-z]{2,4})?', key) is not None
            and 'auto' not in label.casefold() and item.get('caption_kind') == 'publisher_provided_unspecified')


def verified_videos(record, targets, remote, owners):
    """Return associated target IDs with a verified independent publisher caption bundle."""
    if (record.get('schema_version') != 1 or record.get('artifact_kind') not in ('publisher_edition_caption_batch', RSS_ENGLISH_BATCH)
            or record.get('status') != 'verified' or not isinstance(record.get('items'), list)
            or any(record.get(k) is not False for k in
                   ('changes_native_audio_count', 'changes_native_caption_count', 'changes_full_asr_count'))):
        return set()
    bundle, creator = record.get('proof'), record.get('channel_dir')
    if (not isinstance(creator, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,119}', creator)
            or not isinstance(bundle, dict) or not sha256_string(bundle.get('sha256'))
            or type(bundle.get('bytes')) is not int or bundle['bytes'] <= 0
            or not isinstance(bundle.get('drive_id'), str) or not bundle['drive_id']
            or not isinstance(bundle.get('md5'), str) or not re.fullmatch('[0-9a-f]{32}', bundle['md5'])
            or bundle.get('remote') != f"{remote}/{creator}/PublisherCaptions/Batches/{bundle['sha256']}/publisher-captions.zip"):
        return set()
    found = set()
    for item in record['items']:
        if not isinstance(item, dict):
            continue
        video, tab = item.get('video_id'), item.get('tab')
        if record['artifact_kind'] == RSS_ENGLISH_BATCH:
            if (isinstance(video, str) and video in targets and item.get('channel_dir') == creator
                    and tab in ('videos','streams','shorts') and owners.get(video) == (creator, tab)
                    and re.fullmatch(r'UC[A-Za-z0-9_-]{22}', str(item.get('selected_channel_id',''))) and rss_edition(item)):
                found.add(video)
            continue
        if (not isinstance(video, str) or video not in targets or tab not in ('videos', 'shorts', 'streams')
                or item.get('channel_dir') != creator or owners.get(video) != (creator, tab)
                or not isinstance(item.get('selected_channel_id'), str)
                or not re.fullmatch('UC[A-Za-z0-9_-]{22}', item['selected_channel_id'])
                or item.get('source_format') != 'vtt' or item.get('audio_binding') is not None
                or any(item.get(k) is not False for k in
                       ('native_youtube_caption', 'recording_equivalence_verified', 'speech_coverage_verified'))
                or not all(sha256_string(item.get(k)) for k in ('selection_sha256', 'source_sha256', 'track_url_sha256'))
                or not all(type(item.get(k)) is int and item[k] > 0 for k in ('segment_count', 'source_bytes', 'word_count'))
                or not rumble_edition(item) or not english_track(item)):
            continue
        start, end = item.get('first_cue_start'), item.get('last_cue_end')
        if all(type(n) in (int, float) for n in (start, end)) and 0 <= start < end <= item['publisher_duration_s'] + 3:
            found.add(video)
    return found
