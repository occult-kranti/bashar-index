"""Read a creator's downloadable public Rumble audio and English caption descriptors.

The three inputs are saved HTML from a creator listing, its linked watch page,
and the embed declared by that watch page. The CLI writes a private descriptor
file for publisher_mirror plans. It does not make HTTP requests.

    python pipeline/rumble_public_source.py --listing creator.html --watch episode.html \
        --embed player.html --account https://rumble.com/c/Example \
        --watch-url https://rumble.com/v123abc-example.html --out /private/edition.json
"""
import argparse
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

try:
    from .common import ensure_outside_git
except ImportError:
    from common import ensure_outside_git


MAX_HTML = 8_000_000
RUMBLE = {'rumble.com', 'www.rumble.com'}
DECODER = json.JSONDecoder()
WHITESPACE = re.compile(r'\s*')
FIELD_SEPARATOR = re.compile(r'\s*:\s*')
COMMA = re.compile(r'\s*,\s*')


class SourceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise SourceError(message)


class Document(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        require(len(raw) <= MAX_HTML, 'source document exceeds byte limit')
        self.scripts = []
        self.script = None
        self.premium_lock_visible = False
        self.feed(raw.decode('utf-8-sig'))
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self.script = [attrs.get('type', '').lower(), []]
        classes = (attrs.get('class') or '').split()
        if 'js-premium-player-lock' in classes:
            hidden = ('hidden' in classes or 'hidden' in attrs or
                      'display:none' in (attrs.get('style') or '').replace(' ', '').lower())
            if not hidden:
                self.premium_lock_visible = True

    def handle_data(self, text):
        if self.script is not None:
            self.script[1].append(text)

    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            kind, chunks = self.script
            self.scripts.append((kind, ''.join(chunks)))
            self.script = None

    def objects(self, kind):
        for mime, body in self.scripts:
            if mime == kind:
                try:
                    root = json.loads(body)
                except ValueError:
                    continue
                for value in root if isinstance(root, list) else [root]:
                    if isinstance(value, dict):
                        yield value


def public_url(url, hosts):
    require(isinstance(url, str), 'source URL is missing')
    parts = urlsplit(url)
    require(parts.scheme == 'https' and parts.hostname in hosts and not parts.username and
            not parts.password and parts.port in (None, 443) and not parts.fragment,
            'source URL is outside its publisher host')
    return parts


def normalized_title(text):
    return ' '.join(unescape(text).split()) if isinstance(text, str) else ''


def listing_entry(document, account, watch_url):
    identity = public_url(account, RUMBLE)
    target = public_url(watch_url, RUMBLE)
    found = re.fullmatch(r'/(v[a-z0-9]+)-[^/]+\.html', target.path)
    require(found and not target.query and not identity.query and
            re.fullmatch(r'/(?:c/|user/)?[A-Za-z0-9_-]+/?', identity.path),
            'invalid public creator or watch page')
    matches = []
    for part in document.objects('application/json'):
        for row in part.get('items', []) if isinstance(part.get('items'), list) else []:
            if (isinstance(row, dict) and row.get('object_type') == 'video' and
                    row.get('permalink_id') == found[1] and row.get('url') == watch_url and
                    isinstance(row.get('by'), dict) and row['by'].get('url') == account):
                matches.append(row)
    require(matches, 'selected watch page is missing from the public creator listing')
    for row in matches:
        require(row.get('visibility') == 'public' and row.get('availability') is None and
                row.get('downloadable') is True and row.get('is_age_restricted') is False and
                row.get('is_processing') is False and row.get('live') is False,
                'listing does not offer the completed recording for public download')
    selected = {(normalized_title(row.get('title')), row.get('upload_date'), row.get('duration')) for row in matches}
    require(len(selected) == 1, 'conflicting publisher listing entries')
    title, published, duration = selected.pop()
    require(title and isinstance(published, str) and type(duration) is int and duration > 0,
            'incomplete publisher listing')
    return found[1], title, published, duration


def released_embed(document, title, published, duration):
    gate = re.compile(r'"show_premium_exclusive_gate"\s*:\s*(true|false)')
    states = {value for _, body in document.scripts for value in gate.findall(body)}
    require(states == {'false'} and not document.premium_lock_visible, 'watch page needs access review')
    videos = [value for value in document.objects('application/ld+json') if value.get('@type') == 'VideoObject']
    require(len(videos) == 1, 'watch page has no unique published video')
    video = videos[0]
    require(normalized_title(video.get('name')) == title and video.get('uploadDate') == published,
            'watch page differs from selected listing')
    period = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', video.get('duration') or '')
    require(period and sum(int(n or 0) * m for n, m in zip(period.groups(), (3600, 60, 1))) == duration,
            'watch and listing durations differ')
    embed = public_url(video.get('embedUrl'), RUMBLE)
    found = re.fullmatch(r'/embed/(v[a-z0-9]+)/?', embed.path)
    require(found and not embed.query, 'unsupported public embed')
    return video['embedUrl'], found[1]


def embedded_fields(document, embed_id):
    # The publisher appends a JavaScript bookkeeping property to this object.
    # Read its preceding literal JSON fields without executing page scripts.
    pattern = re.compile(r'\["' + re.escape(embed_id) + r'"\]\s*=\s*\{\s*"fps"\s*:')
    records = []
    for _, body in document.scripts:
        for match in pattern.finditer(body):
            cursor = body.index('{', match.start()) + 1
            fields = {}
            while cursor < len(body):
                cursor = WHITESPACE.match(body, cursor).end()
                if cursor >= len(body) or body[cursor] != '"':
                    break
                key, cursor = DECODER.raw_decode(body, cursor)
                sep = FIELD_SEPARATOR.match(body, cursor)
                require(sep, 'malformed published field')
                value, cursor = DECODER.raw_decode(body, sep.end())
                if key == 'ua' and isinstance(value, dict):
                    fields['audio'] = value.get('audio')
                elif key == 'sys' and isinstance(value, dict):
                    fields['message'] = value.get('msg')
                elif key in ('title', 'author', 'duration', 'pubDate', 'live', 'cc'):
                    fields[key] = value
                sep = COMMA.match(body, cursor)
                if not sep:
                    break
                cursor = sep.end()
            records.append(fields)
    require(len(records) == 1, 'embed has no unique selected public rendition set')
    return records[0]


def published_descriptors(listing, watch, embed, account, watch_url):
    """Return public source URLs, source pins, and a stable publisher identity."""
    watch_id, title, published, duration = listing_entry(Document(listing), account, watch_url)
    embed_url, embed_id = released_embed(Document(watch), title, published, duration)
    fields = embedded_fields(Document(embed), embed_id)
    require(normalized_title(fields.get('title')) == title and fields.get('duration') == duration and
            isinstance(fields.get('author'), dict) and fields['author'].get('url') == account and
            fields.get('pubDate') == published and fields.get('live') == 0, 'embed identity differs from listing')
    require(not re.search(r'log.?in|sign.?in|captcha|access denied|subscription|membership|premium',
                          str(fields.get('message') or ''), re.I), 'public embed requires access review')
    require(isinstance(fields.get('audio'), dict), 'publisher exposed no separate audio renditions')
    transport_hosts = {'hugh.cdn.rumble.cloud'}
    audio = {}
    for key, item in fields['audio'].items():
        if not isinstance(item, dict) or not isinstance(item.get('meta'), dict):
            continue
        url, info = item.get('url'), item['meta']
        location = public_url(url, transport_hosts)
        if (location.path.lower().endswith('.aac') and not info.get('w') and not info.get('h') and
                type(info.get('size')) is int and info['size'] > 0):
            audio[key] = {'url': url, 'bytes': info['size'], 'bitrate_kbps': info.get('bitrate'), 'extension': 'aac'}
    require(audio, 'publisher exposed no supported full audio-only rendition')
    captions = {}
    caption_fields = fields.get('cc') or {}
    require(isinstance(caption_fields, dict), 'invalid caption inventory')
    for key, item in caption_fields.items():
        if not isinstance(item, dict) or not re.fullmatch(r'en(?:[-_][A-Za-z]{2,4})?', key, re.I):
            continue
        label = item.get('language') or ''
        automatic = key.lower() == 'en-auto'
        if 'translat' in label.lower() or (automatic and 'auto' not in label.lower()):
            continue
        location = public_url(item.get('path'), transport_hosts)
        if location.path.lower().endswith('.vtt'):
            captions[key] = {'url': item['path'], 'label': label, 'format': 'vtt',
                             'kind': 'automatic_original' if automatic else 'publisher_provided_unspecified'}
    return {'schema_version': 1, 'provider': 'Rumble', 'publisher_account': account, 'watch_url': watch_url,
            'watch_page_id': watch_id, 'embed_url': embed_url, 'declared_embed_id': embed_id, 'title': title,
            'published_at': published, 'duration_seconds': duration, 'audio': audio, 'captions': captions,
            'source_sha256': {k: sha256(raw).hexdigest() for k, raw in
                              [('listing', listing), ('watch', watch), ('embed', embed)]}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('listing', 'watch', 'embed', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--account', required=True)
    parser.add_argument('--watch-url', required=True)
    args = parser.parse_args(argv)
    ensure_outside_git(args.out)
    inputs = []
    for source in (args.listing, args.watch, args.embed):
        require(source.stat().st_size <= MAX_HTML, 'source document exceeds byte limit')
        inputs.append(source.read_bytes())
    value = published_descriptors(*inputs, args.account, args.watch_url)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({'watch_page_id': value['watch_page_id'], 'audio_renditions': len(value['audio']),
                      'english_tracks': len(value['captions'])}))


if __name__ == '__main__':
    main()
