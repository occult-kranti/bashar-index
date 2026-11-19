"""Validate timed captions archived separately from a selected recording's audio."""
import datetime as dt
from html import unescape
import re
import unicodedata
from urllib.parse import urlsplit


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
    if (record.get('schema_version') != 1 or record.get('artifact_kind') != 'publisher_edition_caption_batch'
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
