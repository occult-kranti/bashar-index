import hashlib
import http.client
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.request

from pipeline import youtube_captions as captions


VIDEO = "abcdefghijk"


def track(lang="en", ext="json3", query="", name="English"):
    return {"ext": ext, "name": name,
            "url": f"https://www.youtube.com/api/timedtext?v={VIDEO}&lang={lang}&fmt={ext}{query}"}


def info(subs=None, auto=None, **extra):
    return {"id": VIDEO, "subtitles": subs or {}, "automatic_captions": auto or {}, **extra}


class CaptionSelectionTests(unittest.TestCase):
    def test_english_published_and_original_asr_without_translations(self):
        result = captions.select_tracks(info(
            {"en": [track()], "en-GB": [track("en-GB")], "fr": [track("fr")]},
            {"en-orig": [track(query="&kind=asr")], "en": [track(query="&kind=asr")],
             "es": [track(query="&kind=asr&tlang=es")],
             "en-from-fr": [track("fr", query="&kind=asr&tlang=en")]}))
        self.assertEqual(len(result["tracks"]), 3)
        self.assertEqual(result["excluded_translated"], 2)
        self.assertEqual(result["excluded_languages"], 1)
        self.assertEqual({t["language"] for t in result["tracks"]}, {"en", "en-gb"})
        self.assertEqual(result["unresolved"], [])

    def test_source_language_controls_selection_and_blank_tlang_is_rejected(self):
        result = captions.select_tracks(info({"en": [track("de")], "en-GB": [track(query="&TLANG=")]}))
        self.assertEqual(result["tracks"], [])
        self.assertEqual(result["excluded_languages"], 1)
        self.assertEqual(result["excluded_translated"], 1)

    def test_prefer_json3_and_keep_distinct_named_published_tracks(self):
        result = captions.select_tracks(info({
            "en": [track(ext="vtt"), track(ext="json3"), track(ext="json3")],
            "en-commentary": [track(query="&name=commentary", name="English commentary")]}))
        self.assertEqual(len(result["tracks"]), 2)
        self.assertTrue(all(t["ext"] == "json3" for t in result["tracks"]))
        self.assertEqual(len({t["track_id"] for t in result["tracks"]}), 2)

    def test_stable_id_across_auto_alias_client_signature_and_format(self):
        first = captions.select_tracks(info(auto={"en-orig": [track(query="&kind=asr&expire=1&sig=aaa")]}))["tracks"][0]
        second = captions.select_tracks(info(auto={"en": [track(ext="vtt", query="&kind=asr&expire=2&sig=bbb")]}))["tracks"][0]
        self.assertEqual(first["track_id"], second["track_id"])

    def test_ambiguous_auto_missing_inventory_and_access_warning_are_not_absence(self):
        result = captions.select_tracks(info(auto={"en": [track()]},
                                             _caption_access_warning="subtitle_access_requirement"))
        self.assertEqual(result["tracks"], [])
        self.assertEqual(result["inventory_status"], "incomplete")
        self.assertEqual({r["reason"] for r in result["unresolved"]},
                         {"original_origin_unproven", "subtitle_access_requirement"})
        self.assertEqual(captions.select_tracks({"id": VIDEO})["inventory_status"], "incomplete")
        self.assertEqual(captions.select_tracks(info())["inventory_status"], "no_english_tracks_reported")

    def test_noncaption_unsafe_urls_and_safe_provenance(self):
        unsafe = track()
        unsafe["url"] = "https://evil.example/api/timedtext?secret=hidden"
        result = captions.select_tracks(info({"live_chat": [track()], "en": [track()], "en-GB": [unsafe]},
            http_headers={"Cookie": "secret-cookie", "Authorization": "secret-auth", "User-Agent": "test"}))
        self.assertEqual(result["excluded_noncaption"], 1)
        spec = result["tracks"][0]
        self.assertEqual(spec["http_headers"], {"User-Agent": "test"})
        persisted = json.dumps(captions.provenance(spec))
        for secret in ("https", "Cookie", "Authorization", "http_headers", "secret"):
            self.assertNotIn(secret, persisted)
        self.assertFalse(captions.provenance(spec)["machine_translated"])


class CaptionNormalizationTests(unittest.TestCase):
    def test_json3_preserves_cue_timing_and_missing_duration(self):
        raw = json.dumps({"events": [{"id": 1}, {"tStartMs": 1200, "dDurationMs": 2300,
            "segs": [{"utf8": "Hello "}, {"utf8": "world\n"}]},
            {"tStartMs": 3500, "segs": [{"utf8": "Again"}]}]}).encode()
        result = captions.normalize_caption(raw, "json3")
        self.assertEqual(result["segments"], [{"start": 1.2, "end": 3.5, "text": "Hello world"},
                                               {"start": 3.5, "end": None, "text": "Again"}])
        self.assertEqual(result["text"], "Hello world\nAgain")

    def test_vtt_preserves_timing_and_removes_display_markup(self):
        raw = ("WEBVTT\nKind: captions\nLanguage: en\n\nNOTE comment\nignored\n\n"
               "cue-1\n00:01.200 --> 00:03.500 align:start\n<v Person>Hello &amp; <b>world</b>\n\n"
               "01:00:02.000 --> 01:00:03.000\nAgain\n").encode()
        result = captions.normalize_caption(raw, "vtt")
        self.assertEqual(result["segments"][0], {"start": 1.2, "end": 3.5, "text": "Hello & world"})
        self.assertEqual(result["segments"][1]["start"], 3602.0)

    def test_invalid_documents_and_timings_fail_without_body_leak(self):
        invalid = [(b"<html>private token</html>", "json3"), (b"{}", "json3"),
                   (b'{"events":[{"tStartMs":-1,"segs":[{"utf8":"x"}]}]}', "json3"),
                   (b'{"events":[{"tStartMs":NaN,"segs":[{"utf8":"x"}]}]}', "json3"),
                   (b"WEBVTT\n\n00:05.000 --> 00:01.000\nx", "vtt"),
                   (b"00:01.000 --> 00:02.000\nx", "vtt"), (b"\xff", "vtt")]
        for raw, ext in invalid:
            with self.subTest(raw=raw):
                with self.assertRaises(captions.CaptionError) as caught:
                    captions.normalize_caption(raw, ext)
                self.assertEqual(caught.exception.kind, "caption_response")
                self.assertNotIn("private", str(caught.exception))

    def test_empty_valid_caption_document_is_not_invented_text(self):
        for raw, ext in [(b'{"events":[]}', "json3"), (b"WEBVTT\n\n", "vtt")]:
            self.assertEqual(captions.normalize_caption(raw, ext)["segments"], [])


class Response(io.BytesIO):
    def __init__(self, body, headers=None, status=200):
        super().__init__(body)
        self.headers = headers if headers is not None else {"Content-Length": str(len(body)), "Content-Type": "application/json"}
        self.status = status

    def geturl(self):
        return track()["url"]


class Budget:
    def __init__(self, cap=1024 * 1024):
        self.cap, self.used, self.admitted = cap, 0, []

    def admit_size(self, path, total):
        self.admitted.append((path, total))
        if total > self.cap:
            raise RuntimeError("storage budget exhausted")

    def write(self, output, data):
        if self.used + len(data) > self.cap:
            raise RuntimeError("storage budget exhausted")
        output.write(data)
        output.flush()
        self.used += len(data)


class CaptionTransportTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "raw.json3.part"
        self.spec = captions.select_tracks(info({"en": [track()]}))["tracks"][0]
        self.stop, self.limiter, self.budget = threading.Event(), Mock(), Budget()

    def fetch(self, response=None, error=None, **kwargs):
        opener = Mock()
        opener.open.side_effect = error
        opener.open.return_value = response
        with patch.object(captions.urllib.request, "build_opener", return_value=opener):
            with self.path.open("wb") as output:
                result = captions.fetch_track(self.spec, output, budget=self.budget,
                    limiter=self.limiter, stop=self.stop, **kwargs)
        return result, opener

    def test_real_spool_writes_and_hashes_with_reservation_expansion(self):
        raw = b'{"events":[]}'
        result, opener = self.fetch(Response(raw))
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertEqual(self.budget.used, len(raw))
        self.assertEqual(self.budget.admitted, [(self.path, len(raw))])
        self.assertEqual(result["md5"], hashlib.md5(raw).hexdigest())
        self.assertEqual(result["sha256"], hashlib.sha256(raw).hexdigest())
        self.limiter.wait.assert_called_once()
        opener.open.assert_called_once()

    def test_declared_oversize_is_deferred_before_writing(self):
        with self.assertRaises(captions.CaptionError) as caught:
            self.fetch(Response(b"123456", {"Content-Length": "6"}), max_bytes=5)
        self.assertEqual(caught.exception.kind, "deferred_caption_size")
        self.assertEqual(self.path.stat().st_size, 0)
        self.assertEqual(self.budget.admitted, [])

    def test_unknown_length_is_bounded_and_budget_errors_are_not_hidden(self):
        with self.assertRaises(captions.CaptionError) as caught:
            self.fetch(Response(b"123456", {}), max_bytes=5)
        self.assertEqual(caught.exception.kind, "deferred_caption_size")
        self.assertLessEqual(self.path.stat().st_size, 5)
        self.budget = Budget(cap=3)
        with self.assertRaisesRegex(RuntimeError, "storage budget"):
            self.fetch(Response(b"1234", {}))

    def test_short_content_length_html_and_partial_ranges_fail(self):
        cases = [{"Content-Length": "6"}, {"Content-Length": "-2"}, {"Content-Length": "0"},
                 {"Content-Type": "text/html"}, {"Content-Range": "bytes 0-2/9"},
                 {"Content-Encoding": "gzip"}]
        for headers in cases:
            with self.subTest(headers=headers):
                with self.assertRaises(captions.CaptionError) as caught:
                    self.fetch(Response(b"123", headers))
                self.assertEqual(caught.exception.kind, "caption_response")

    def test_interrupted_chunked_response_is_not_a_completed_track(self):
        response = Response(b"123", {})
        response.read = Mock(side_effect=http.client.IncompleteRead(b"partial", 20))
        with self.assertRaises(captions.CaptionError) as caught:
            self.fetch(response)
        self.assertEqual(caught.exception.kind, "caption_response")
        self.assertEqual(self.path.stat().st_size, 0)

    def test_http_errors_do_not_retry_or_leak_url(self):
        for status, kind in [(403, "forbidden"), (429, "rate_limited"), (401, "login_required"),
                             (404, "caption_unavailable"), (410, "caption_unavailable")]:
            with self.subTest(status=status):
                error = urllib.error.HTTPError("https://secret.example/token", status, "secret-body", {}, None)
                with self.assertRaises(captions.CaptionError) as caught:
                    self.fetch(error=error)
                self.assertEqual(caught.exception.kind, kind)
                self.assertNotIn("secret", str(caught.exception))

    def test_stop_before_request_and_after_wait(self):
        self.stop.set()
        with self.assertRaises(captions.CaptionError) as caught:
            self.fetch(Response(b"123"))
        self.assertEqual(caught.exception.kind, "stopped")
        self.limiter.wait.assert_not_called()
        self.stop.clear()
        self.limiter.wait.side_effect = self.stop.set
        with self.assertRaises(captions.CaptionError) as caught:
            self.fetch(Response(b"123"))
        self.assertEqual(caught.exception.kind, "stopped")
        self.assertEqual(self.path.stat().st_size, 0)

    def test_redirect_rejects_translation_and_untrusted_host_before_pacing(self):
        handler = captions._CaptionRedirect(VIDEO, self.limiter, self.stop)
        request = urllib.request.Request(self.spec["url"])
        for target in [self.spec["url"] + "&tlang=en", "https://evil.example/api/timedtext"]:
            with self.assertRaises(captions.CaptionError):
                handler.redirect_request(request, None, 302, "Found", {}, target)
        self.limiter.wait.assert_not_called()


if __name__ == "__main__":
    unittest.main()
