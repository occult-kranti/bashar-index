"""Read typed, complete entries from a channel's public uploads playlist HTML."""
import json
import re
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from common import ID_RE


CHANNEL_ID = re.compile(r"UC[A-Za-z0-9_-]{22}")
INITIAL_DATA = re.compile(
    r"""(?:(?:window\[['"]ytInitialData['"]\]|\bytInitialData)\s*=\s*|"""
    r"""<script\b(?=[^>]{0,600}\bid=["']yt-initial-data["'])(?=[^>]{0,600}\btype=["']application/json["'])[^>]{0,600}>\s*)(?=\{)""",
    re.I,
)
DECODER = json.JSONDecoder()


def uploads_url(channel_id):
    if not CHANNEL_ID.fullmatch(channel_id):
        raise ValueError("Invalid primary channel ID")
    return "https://www.youtube.com/playlist?list=UU" + channel_id[2:]


def canonical_playlist_id(url):
    parts = urlsplit(url or "")
    if (parts.scheme not in ("http", "https") or parts.hostname not in ("youtube.com", "www.youtube.com")
            or parts.path != "/playlist"):
        return None
    values = parse_qs(parts.query).get("list", ())
    return values[0] if len(values) == 1 else None


class PageMetadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = None
        self.title = None
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
            self.urls.add(self.canonical)
        if tag == "meta" and attrs.get("property") == "og:url":
            self.urls.add(attrs.get("content"))
        if tag == "meta" and attrs.get("property") == "og:title":
            self.title = attrs.get("content")


def whitespace(text, offset):
    while offset < len(text) and text[offset].isspace():
        offset += 1
    return offset


def field_offset(text, offset, path):
    """Seek an exact JSON path. Decode preceding siblings to skip their contents."""
    for key in path:
        offset = whitespace(text, offset)
        if isinstance(key, int):
            if text[offset:offset + 1] != "[":
                raise ValueError("Missing playlist array")
            offset = whitespace(text, offset + 1)
            for _ in range(key):
                _, offset = DECODER.raw_decode(text, offset)
                offset = whitespace(text, offset)
                if text[offset:offset + 1] != ",":
                    raise ValueError("Missing primary playlist section")
                offset = whitespace(text, offset + 1)
        else:
            if text[offset:offset + 1] != "{":
                raise ValueError("Missing playlist object")
            offset = whitespace(text, offset + 1)
            while offset < len(text):
                name, offset = DECODER.raw_decode(text, offset)
                offset = whitespace(text, offset)
                if text[offset:offset + 1] != ":":
                    raise ValueError("Invalid playlist field")
                offset = whitespace(text, offset + 1)
                if name == key:
                    break
                _, offset = DECODER.raw_decode(text, offset)
                offset = whitespace(text, offset)
                if text[offset:offset + 1] != ",":
                    raise ValueError("Missing playlist field")
                offset = whitespace(text, offset + 1)
            else:
                raise ValueError("Playlist field is beyond the saved bytes")
    return offset


def nested(node, dotted_path):
    for key in dotted_path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def bylines(metadata):
    owner = nested(metadata, "image.decoratedAvatarViewModel.rendererContext.commandContext.onTap."
                             "innertubeCommand.browseEndpoint.browseId")
    if owner:
        return [owner]
    # Uploads with a guest can carry a list of credited channels. The first
    # channel in that displayed byline must match the requested uploads owner.
    roster = nested(metadata, "image.avatarStackViewModel.rendererContext.commandContext.onTap.innertubeCommand."
                              "showDialogCommand.panelLoadingStrategy.inlineContent.dialogViewModel.customContent."
                              "listViewModel.listItems")
    if roster:
        return [nested(row, "listItemViewModel.rendererContext.commandContext.onTap.innertubeCommand."
                            "browseEndpoint.browseId") for row in roster]
    rows = nested(metadata, "metadata.contentMetadataViewModel.metadataRows") or []
    if not rows:
        return []
    return [channel for part in rows[0].get("metadataParts", []) for run in part.get("text", {}).get("commandRuns", [])
            if (channel := nested(run, "onTap.innertubeCommand.browseEndpoint.browseId"))]


def text_field(field):
    field = field or {}
    return field.get("simpleText") or "".join(run.get("text", "") for run in field.get("runs", []))


def playlist_entry(item, position, expected_owner, expected_playlist):
    model = item.get("lockupViewModel")
    legacy = item.get("playlistVideoRenderer")
    if isinstance(model, dict):
        if model.get("contentType") != "LOCKUP_CONTENT_TYPE_VIDEO":
            return None
        video = model.get("contentId")
        watch = nested(model, "rendererContext.commandContext.onTap.innertubeCommand.watchEndpoint") or {}
        if type(watch.get("index")) is not int or watch["index"] != position:
            return None
        metadata = nested(model, "metadata.lockupMetadataViewModel") or {}
        owners = bylines(metadata)
        title = nested(metadata, "title.content")
        rows = nested(metadata, "metadata.contentMetadataViewModel.metadataRows") or []
        labels = [[part.get("text", {}).get("content") for part in row.get("metadataParts", [])] for row in rows]
        overlays = nested(model, "contentImage.thumbnailViewModel.overlays") or []
        badges = [nested(badge, "thumbnailBadgeViewModel.text") for overlay in overlays
                  for badge in (nested(overlay, "thumbnailBottomOverlayViewModel.badges") or [])]
    elif isinstance(legacy, dict):
        video = legacy.get("videoId")
        watch = nested(legacy, "navigationEndpoint.watchEndpoint") or {}
        if text_field(legacy.get("index")) != str(position + 1):
            return None
        owners = [nested(run, "navigationEndpoint.browseEndpoint.browseId")
                  for run in legacy.get("shortBylineText", {}).get("runs", [])]
        title = text_field(legacy.get("title"))
        labels = []
        badges = [text_field(legacy.get("lengthText"))]
    else:
        return None
    if (not ID_RE.fullmatch(video or "") or watch.get("videoId") != video or watch.get("playlistId") != expected_playlist
            or not owners or owners[0] != expected_owner or not all(CHANNEL_ID.fullmatch(ch or "") for ch in owners)):
        return None
    return {"video_id": video, "position_zero_based": position, "title": title,
            "byline_channel_id": owners[0], "additional_byline_channel_ids": owners[1:],
            "watch_playlist_id": expected_playlist, "display_metadata": labels,
            "duration_or_badges_as_shown": [s for s in badges if s]}


def first_playlist_array(text, data_start):
    tab = ("contents", "twoColumnBrowseResultsRenderer", "tabs", 0, "tabRenderer")
    selected = field_offset(text, data_start, tab + ("selected",))
    if DECODER.raw_decode(text, selected)[0] is not True:
        raise ValueError("Missing selected uploads tab")
    sections = tab + ("content", "sectionListRenderer", "contents")
    for section_index in range(4):
        path = sections + (section_index, "itemSectionRenderer", "contents")
        offset = field_offset(text, data_start, path)
        if text[offset:offset + 1] != "[":
            raise ValueError("Missing primary uploads array")
        first = whitespace(text, offset + 1)
        if text[first:first + 1] != "{":
            continue
        key, _ = DECODER.raw_decode(text, whitespace(text, first + 1))
        if key == "lockupViewModel":
            return first, "lockup"
        if key == "playlistVideoListRenderer":
            wrapped = field_offset(text, first, ("playlistVideoListRenderer", "contents"))
            return whitespace(text, wrapped + 1), "playlist_video"
    raise ValueError("Unsupported primary uploads list")


def parse_uploads_page(raw, channel_id, *, complete_http):
    """Read only closed item objects. An unfinished final object contributes no row."""
    playlist = canonical_playlist_id(uploads_url(channel_id))
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        if complete_http or exc.end != len(raw) or exc.reason != "unexpected end of data":
            raise
        text = raw[:exc.start].decode("utf-8")
    match = INITIAL_DATA.search(text)
    if not match:
        raise ValueError("No structured playlist data")
    page = PageMetadata()
    page.feed(text[:match.start()])
    if canonical_playlist_id(page.canonical) != playlist or any(canonical_playlist_id(url) != playlist for url in page.urls):
        raise ValueError("Returned canonical URL differs from the requested uploads playlist")
    offset, layout = first_playlist_array(text, match.end())
    rows, unresolved, seen = [], [], set()
    position = 0
    closed = more = False
    while offset < len(text):
        if text[offset:offset + 1] == "]":
            closed = True
            break
        try:
            item, end = DECODER.raw_decode(text, offset)
        except json.JSONDecodeError:
            if complete_http:
                raise ValueError("Invalid complete playlist entry") from None
            break
        if not isinstance(item, dict):
            raise ValueError("Unexpected primary playlist item")
        if "continuationItemRenderer" in item or "continuationItemViewModel" in item:
            more = True
        else:
            row = playlist_entry(item, position, channel_id, playlist)
            if row is None or row["video_id"] in seen:
                unresolved.append(position)
            else:
                rows.append(row)
                seen.add(row["video_id"])
            position += 1
        offset = whitespace(text, end)
        if text[offset:offset + 1] == ",":
            offset = whitespace(text, offset + 1)
        elif text[offset:offset + 1] != "]":
            break
    if not rows:
        raise ValueError("No complete primary item could be bound to this channel")
    return {"channel_id": channel_id, "canonical_url": page.canonical, "page_title": page.title,
            "items": rows, "unresolved_positions": unresolved, "complete_primary_frames": position,
            "primary_array_closed": closed, "continuation_visible": more, "complete_http": complete_http, "layout": layout}
