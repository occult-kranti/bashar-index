import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import collect_uploads_catalog as catalog
from feeds import FetchError
from uploads_playlist import parse_uploads_page, uploads_url


OWNER = "UC" + "A" * 22
GUEST = "UC" + "B" * 22
PLAYLIST = "UU" + OWNER[2:]


def endpoint(**command):
    return {"rendererContext": {"commandContext": {"onTap": {"innertubeCommand": command}}}}


def modern_item(index, guest=False):
    video = f"{index:011}"
    avatar = endpoint(browseEndpoint={"browseId": OWNER})
    image = {"decoratedAvatarViewModel": avatar}
    if guest:
        roster = [{"listItemViewModel": endpoint(browseEndpoint={"browseId": person})} for person in (OWNER, GUEST)]
        panel = {"dialogViewModel": {"customContent": {"listViewModel": {"listItems": roster}}}}
        image = {"avatarStackViewModel": endpoint(showDialogCommand={"panelLoadingStrategy": {"inlineContent": panel}})}
    return {"lockupViewModel": {
        "contentId": video, "contentType": "LOCKUP_CONTENT_TYPE_VIDEO",
        "metadata": {"lockupMetadataViewModel": {"title": {"content": "Episode"}, "image": image}},
        **endpoint(watchEndpoint={"videoId": video, "index": index, "playlistId": PLAYLIST}),
    }}


def markup(entries, *, application_json=False):
    section = {"itemSectionRenderer": {"contents": entries}}
    tab = {"tabRenderer": {"selected": True, "content": {"sectionListRenderer": {"contents": [section]}}}}
    # A sidebar with a valid-looking row must never count toward the inventory.
    document = {"contents": {"twoColumnBrowseResultsRenderer": {"tabs": [tab]}}, "sidebar": modern_item(999)}
    content = json.dumps(document, separators=(",", ":"))
    script = '<script type="application/json" id="yt-initial-data">' if application_json else '<script>window["ytInitialData"]='
    return (f'<html><link rel="canonical" href="{uploads_url(OWNER)}">{script}{content}</script></html>').encode()


class Response(io.BytesIO):
    status = 200
    headers = {"Content-Type": "text/html; charset=UTF-8"}

    def geturl(self):
        return uploads_url(OWNER)


class UploadsTest(unittest.TestCase):
    def test_current_script_shapes_and_collaborator_with_continuation(self):
        rows = [modern_item(0), modern_item(1, guest=True), {"continuationItemViewModel": {}}]
        for other_script in (False, True):
            result = parse_uploads_page(markup(rows, application_json=other_script), OWNER, complete_http=True)
            self.assertEqual([r["position_zero_based"] for r in result["items"]], [0, 1])
            self.assertEqual(result["items"][1]["additional_byline_channel_ids"], [GUEST])
            self.assertTrue(result["primary_array_closed"])
            self.assertTrue(result["continuation_visible"])
            self.assertEqual(result["unresolved_positions"], [])
            with self.assertRaisesRegex(ValueError, "canonical"):
                parse_uploads_page(markup(rows, application_json=other_script), GUEST, complete_http=True)

    def test_prefix_does_not_invent_last_entry_or_exhaustion(self):
        source = markup([modern_item(i) for i in range(3)])
        cut = source.index(b'"contentId":"00000000002"') + 17
        result = parse_uploads_page(source[:cut], OWNER, complete_http=False)
        self.assertEqual([r["video_id"] for r in result["items"]], ["00000000000", "00000000001"])
        self.assertFalse(result["primary_array_closed"])
        self.assertFalse(result["complete_http"])
        self.assertFalse(result["continuation_visible"])

    def test_legacy_unverified_identity_and_index_are_preserved_as_gaps(self):
        records = []
        for index in range(3):
            video = f"{index:011}"
            channel = GUEST if index == 1 else OWNER
            records.append({"playlistVideoRenderer": {
                "videoId": video, "index": {"simpleText": str(index + 1)}, "title": {"simpleText": "Video"},
                "shortBylineText": {"runs": [{"navigationEndpoint": {"browseEndpoint": {"browseId": channel}}}]},
                "navigationEndpoint": {"watchEndpoint": {"videoId": video, "playlistId": PLAYLIST}},
            }})
        result = parse_uploads_page(markup([{"playlistVideoListRenderer": {"contents": records}}]), OWNER, complete_http=True)
        self.assertEqual([r["position_zero_based"] for r in result["items"]], [0, 2])
        self.assertEqual(result["unresolved_positions"], [1])

    def test_normal_entrypoint_fetch_resume_reparse_and_provider_stop(self):
        with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()):
            root = Path(td)
            manifest = root / "creators.csv"
            manifest.write_text(f"channel_dir,channel_id\nfirst,{OWNER}\nnext,{GUEST}\n", encoding="utf-8")
            args = ["--channels", str(manifest), "--out", str(root / "out"), "--min-interval", "0"]
            robots = ("https://www.youtube.com/robots.txt", "text/plain", b"User-agent: *\nAllow: /\n")
            answered = Response(markup([modern_item(i) for i in range(3)]))
            with (patch.object(catalog, "youtube_override", return_value=True),
                  patch.object(catalog, "get_bytes", return_value=robots) as rules,
                  patch.object(catalog, "open_url", side_effect=[answered, FetchError(429, "limit", retry_after=60)]) as opened):
                self.assertEqual(catalog.main(["plan", *args]), 0)
                self.assertEqual(opened.call_count, 0)
                self.assertEqual(catalog.main(["fetch", *args]), 3)
                self.assertEqual(opened.call_count, 2)
                self.assertEqual(rules.call_count, 1)
                self.assertEqual(catalog.main(["fetch", *args]), 3)
                self.assertEqual(opened.call_count, 2)
                (root / "out/first/frames.json").unlink()
                self.assertEqual(catalog.main(["reparse", *args]), 0)
                self.assertEqual(len(json.loads((root / "out/first/frames.json").read_bytes())["items"]), 3)
                self.assertEqual(opened.call_count, 2)
            self.assertTrue(json.loads((root / "out/next/receipt.json").read_bytes())["provider_stop"])


if __name__ == "__main__":
    unittest.main()
