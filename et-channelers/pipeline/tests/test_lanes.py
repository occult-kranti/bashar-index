#!/usr/bin/env python3
"""Tests for the non-YouTube lanes: podcast feeds, creator-hosted files and publisher texts.

    python3 -I et-channelers/pipeline/tests/test_lanes.py -v

Standard library only. A small HTTP server on 127.0.0.1 plays the publisher and a stand-in ffmpeg
plays the encoder, so nothing here touches the network or a real podcast host.
"""
from __future__ import annotations

import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIPE = HERE.parent
ET = PIPE.parent
sys.path.insert(0, str(PIPE))
sys.path.insert(0, str(HERE))

import common  # noqa: E402
import feeds  # noqa: E402
import fetch_publisher_text  # noqa: E402
import find_feeds  # noqa: E402
import select_episodes  # noqa: E402
from test_pipeline import FAKE_FFMPEG, make_tool  # noqa: E402

AUDIO = b"ID3" + b"\x00" * 5000


def feed_xml(items, title="Test Show", author="Test Person", link="https://example.org/"):
    body = "".join(items)
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" '
            f'xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" '
            f'xmlns:podcast="https://podcastindex.org/namespace/1.0" '
            f'xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel><title>{title}</title>'
            f'<link>{link}</link><itunes:author>{author}</itunes:author><language>en</language>{body}'
            f'</channel></rss>').encode("utf-8")


def item(guid, title, url, duration="10:00", date="Fri, 06 Nov 2026 13:16:35 +0000", extra=""):
    enclosure = f'<enclosure url="{url}" length="5003" type="audio/mpeg"/>' if url else ""
    return (f"<item><title>{title}</title><guid>{guid}</guid><pubDate>{date}</pubDate>"
            f"<itunes:duration>{duration}</itunes:duration>{enclosure}{extra}</item>")


class Publisher(http.server.BaseHTTPRequestHandler):
    """Serves what the test put in the class attribute `routes`: path -> (status, content type, body)."""
    routes, hits, lock = {}, [], threading.Lock()

    def do_GET(self):  # noqa: N802
        with self.lock:
            self.hits.append(self.path)
        status, ctype, body = self.routes.get(self.path, (404, "text/plain", b"not here"))
        if callable(body):
            body = body()
        if status in (301, 302):                     # (302, "location", b"http://other-host/path")
            self.send_response(status)
            self.send_header("Location", body.decode())
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class LaneCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="etlane-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "private"
        self.ffmpeg = make_tool(self.tmp / "bin", "ffmpeg", FAKE_FFMPEG)
        Publisher.routes, Publisher.hits = {}, []
        self.server = http.server.ThreadingHTTPServer(("", 0), Publisher)   # every loopback address
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def cli(self, script, *args):
        return subprocess.run([sys.executable, "-I", str(PIPE / script), *map(str, args)], capture_output=True,
                              text=True, timeout=120, env=dict(os.environ))

    def write_queue(self, rows):
        fields = select_episodes.FIELDS
        common.write_csv(self.root / "jobs" / "queue_enclosures.csv",
                         [{**dict.fromkeys(fields, ""), **r} for r in rows], fields)

    def download(self, *extra):
        return self.cli("download_enclosures.py", "--root", self.root, "--ffmpeg", self.ffmpeg, "--ffprobe",
                        "ffprobe-not-installed", "--min-interval", "0", "--backoff", "0.01", "--min-bytes", "10", *extra)

    def manifest(self):
        return common.read_jsonl(self.root / "audio" / "audio_manifest.jsonl")


# --------------------------------------------------------------------------- ids and small helpers
class TestIds(unittest.TestCase):
    def test_lane_ids_are_stable_and_distinct_from_youtube_ids(self):
        a = common.item_id("pod", "https://x/feed", "guid-1")
        self.assertEqual(a, common.item_id("pod", "https://x/feed", "guid-1"))
        self.assertNotEqual(a, common.item_id("pod", "https://x/feed", "guid-2"))
        self.assertRegex(a, r"^pod-[0-9a-f]{16}$")
        self.assertTrue(common.ITEM_RE.match(a))
        self.assertFalse(common.ID_RE.match(a))            # never mistaken for a YouTube id
        self.assertTrue(common.ITEM_RE.match("kvU9mCJr-eo"))
        self.assertEqual(common.lane_of("kvU9mCJr-eo"), "youtube")
        self.assertEqual(common.lane_of(common.item_id("web", "u")), "web")
        with self.assertRaises(ValueError):
            common.item_id("yt", "x")

    def test_http_status_classes(self):
        self.assertEqual(common.http_error_class(429), "rate_limited")
        self.assertEqual(common.http_error_class(403), "forbidden")
        self.assertEqual(common.http_error_class(404), "unavailable")
        self.assertEqual(common.http_error_class(503), "network")

    def test_host_gates_stop_one_host_only(self):
        gates = common.HostGates(0, stop_after=2)
        gates.hard_block("a.example")
        self.assertFalse(gates.blocked("a.example"))
        gates.hard_block("a.example")
        self.assertTrue(gates.blocked("a.example"))
        self.assertFalse(gates.blocked("b.example"))
        self.assertEqual(gates.blocked_hosts(), ["a.example"])

    def test_a_success_resets_a_hosts_count(self):
        gates = common.HostGates(0, stop_after=2)
        gates.hard_block("a.example")
        gates.success("a.example")
        gates.hard_block("a.example")
        self.assertFalse(gates.blocked("a.example"))

    def test_urls_with_spaces_and_accents_are_encoded_once(self):
        self.assertEqual(feeds.safe_url("https://kryon.com/A B/DAY EIGHT- D.mp3"),
                         "https://kryon.com/A%20B/DAY%20EIGHT-%20D.mp3")
        self.assertEqual(feeds.safe_url("https://x.org/a%20b.mp3?x=1&y=a b"), "https://x.org/a%20b.mp3?x=1&y=a%20b")
        self.assertEqual(feeds.safe_url("https://x.org/Król.mp3"), "https://x.org/Kr%C3%B3l.mp3")
        with self.assertRaises(feeds.FetchError):
            feeds.safe_url("https://user:secret@x.org/a.mp3")


# --------------------------------------------------------------------------- feed parsing
class TestFeedParsing(unittest.TestCase):
    def test_episodes_and_summary(self):
        xml = feed_xml([
            item("g1", "First talk", "https://cdn.example/a.mp3", "1:02:03"),
            item("g2", "Second talk", "https://cdn.example/b.mp3", "894"),
            item("g3", "Text only post", ""),                                    # no enclosure: counted, not returned
            item("g1", "First talk again", "https://cdn.example/a2.mp3"),         # same guid twice
        ])
        parsed = feeds.parse_feed(xml, "https://example.org/feed")
        self.assertEqual(parsed["feed"]["items"], 4)
        self.assertEqual(parsed["feed"]["episodes"], 2)
        self.assertEqual([e["duration_s"] for e in parsed["episodes"]], [3723, 894])
        self.assertEqual(parsed["episodes"][0]["published"], "2026-11-06")
        self.assertEqual(parsed["feed"]["author"], "Test Person")
        self.assertEqual(parsed["feed"]["known_hours"], round((3723 + 894) / 3600, 1))
        self.assertNotIn("description", parsed["episodes"][0])                    # show notes are not kept

    def test_transcript_links_and_youtube_ids_in_show_notes(self):
        extra = ('<podcast:transcript url="https://t.example/1.vtt" type="text/vtt"/>'
                 '<description>Watch: https://www.youtube.com/watch?v=kvU9mCJr-eo and https://youtu.be/ufzO0sbNICQ'
                 '</description>')
        parsed = feeds.parse_feed(feed_xml([item("g", "T", "https://c.example/a.mp3", extra=extra)]), "https://f")
        episode = parsed["episodes"][0]
        self.assertEqual(episode["transcripts"][0], {"url": "https://t.example/1.vtt", "type": "text/vtt",
                                                     "language": "", "rel": ""})
        self.assertEqual(episode["youtube_ids"], ["kvU9mCJr-eo", "ufzO0sbNICQ"])
        self.assertEqual(parsed["feed"]["with_transcript"], 1)

    def test_video_ids_are_read_from_real_youtube_hosts_only(self):
        find = feeds.YOUTUBE_ID_IN_TEXT.findall
        self.assertEqual(find('<iframe src="https://www.youtube-nocookie.com/embed/AbCdEfGhIjK?rel=0">'), ["AbCdEfGhIjK"])
        self.assertEqual(find("https://m.youtube.com/watch?feature=x&amp;v=Zz_zZ-zZ0zZ and //youtube.com/shorts/SSSSSSSSSSS"),
                         ["Zz_zZ-zZ0zZ", "SSSSSSSSSSS"])
        self.assertEqual(find("https://youtu.be/ufzO0sbNICQ?t=4"), ["ufzO0sbNICQ"])
        for lookalike in ("notyoutube.com/embed/XXXXXXXXXXX", "my-youtube.com/embed/YYYYYYYYYYY",
                          "fakeyoutu.be/ZZZZZZZZZZZ", "youtube.com.evil.example/embed/QQQQQQQQQQQ"):
            self.assertEqual(find(lookalike), [], lookalike)
        self.assertEqual(find("https://www.youtube.com/watch?v=TooLongToBeAnId"), [])   # 15 characters is not an id

    def test_a_blog_feed_with_cover_images_is_not_a_podcast(self):
        post = ('<item><title>A written post</title><guid>p1</guid>'
                '<enclosure url="https://static.example/cover.jpg" length="1" type="image/jpeg"/></item>')
        untyped_picture = '<item><title>Another</title><guid>p2</guid><enclosure url="https://static.example/c.png"/></item>'
        document = '<item><title>A paper</title><guid>p3</guid><enclosure url="https://x.example/a.pdf" type="application/pdf"/></item>'
        parsed = feeds.parse_feed(feed_xml([post, untyped_picture, document]), "https://blog.example/blog-feed.xml", "elena-danaan")
        self.assertEqual((parsed["feed"]["items"], parsed["feed"]["episodes"]), (3, 0))
        real = feeds.parse_feed(feed_xml([item("g", "Talk", "https://cdn.example/a.mp3"),
                                          '<item><title>No type</title><guid>g2</guid><enclosure url="https://cdn.example/b.m4a"/></item>',
                                          '<item><title>Video</title><guid>g3</guid><enclosure url="https://cdn.example/play?id=9" type="video/mp4"/></item>']),
                                "https://f.example/rss", "athina-krol")
        self.assertEqual(real["feed"]["episodes"], 3)
        self.assertTrue(feeds.is_media("application/octet-stream", "https://c.example/a.mp3"))
        self.assertFalse(feeds.is_media("application/octet-stream", "https://c.example/a.bin"))

    def test_durations_and_dates(self):
        self.assertEqual(feeds.parse_duration_text("43:34"), 2614)
        self.assertEqual(feeds.parse_duration_text("894.6"), 894)
        self.assertIsNone(feeds.parse_duration_text("soon"))
        self.assertIsNone(feeds.parse_duration_text(""))
        self.assertEqual(feeds.parse_date("Wed, 17 May 2023 00:00:00 +0000"), "2023-05-17")
        self.assertEqual(feeds.parse_date("2024-04-30T19:13:53Z"), "2024-04-30")
        self.assertEqual(feeds.parse_date("whenever"), "")

    def test_an_episode_keeps_its_id_when_its_feed_moves(self):
        items = [item("guid-1", "First", "https://old-host.example/a/1.mp3"), item("guid-2", "Second", "https://old-host.example/a/2.mp3")]
        before = feeds.parse_feed(feed_xml(items), "http://old-host.example/feed.xml", "athina-krol")
        moved = [item("guid-1", "First", "https://new-cdn.example/shows/9/1.mp3"), item("guid-2", "Second", "https://new-cdn.example/shows/9/2.mp3")]
        after = feeds.parse_feed(feed_xml(moved), "https://new-host.example/rss", "athina-krol")
        self.assertEqual([e["video_id"] for e in before["episodes"]], [e["video_id"] for e in after["episodes"]])
        self.assertNotEqual(before["episodes"][0]["legacy_id"], after["episodes"][0]["legacy_id"])   # the old scheme moved
        other = feeds.parse_feed(feed_xml(items), "http://old-host.example/feed.xml", "aaron-abke")
        self.assertNotEqual(before["episodes"][0]["video_id"], other["episodes"][0]["video_id"])     # per person

    def test_an_episode_without_a_guid_is_keyed_by_its_file_not_its_host(self):
        def one(url):
            xml = feed_xml([f'<item><title>T</title><enclosure url="{url}" length="5" type="audio/mpeg"/></item>'])
            return feeds.parse_feed(xml, "https://f.example/rss", "athina-krol")["episodes"][0]["video_id"]
        self.assertEqual(one("https://tracker.example/redirect.mp3/cdn-a.example/shows/42/ep7.mp3?utm=1"),
                         one("http://cdn-b.example/shows/42/ep7.mp3"))
        self.assertNotEqual(one("https://cdn-a.example/shows/42/ep7.mp3"), one("https://cdn-a.example/shows/42/ep8.mp3"))

    def test_entity_declarations_are_refused(self):
        bomb = b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "aaaa">]><rss><channel></channel></rss>'
        with self.assertRaises(ValueError):
            feeds.parse_feed(bomb, "https://f")

    def test_title_matching(self):
        self.assertEqual(feeds.title_similarity("How to know your SOUL PURPOSE", "how to know your soul purpose!"), 1.0)
        self.assertLess(feeds.title_similarity("The Golden Line", "Mountain Consciousness"), 0.2)
        pattern = feeds.name_pattern(["Darryl Anka", "Bashar"])
        self.assertTrue(pattern.search("An evening with BASHAR (channeled)"))
        self.assertTrue(pattern.search("Darryl  Anka returns"))
        self.assertFalse(pattern.search("Basharat Ali on economics"))             # whole words only
        self.assertIsNone(feeds.name_pattern(["", "ab"]))


# --------------------------------------------------------------------------- grading feed candidates
class TestGrading(unittest.TestCase):
    T = {"person_id": "athina-krol", "person_name": "Athina Król", "names": ["Athina Król", "AthinaKrol"]}

    def grade(self, author, title, target=None, strict=(), domains=None, site="", feed="", linked=False):
        return find_feeds.grade(target or self.T, {"artistName": author, "collectionName": title, "feedUrl": feed},
                                set(strict), domains or {}, site, linked)[0]

    def test_author_and_title_match_is_a_name_match(self):
        self.assertEqual(self.grade("Athina Krol", "Spirit Channel with Athina Król"), "name-match")

    def test_accents_and_case_do_not_matter(self):
        self.assertEqual(find_feeds.fold("Athina Król"), "athina krol")
        self.assertEqual(self.grade("ATHINA KRÓL", "athina krol live"), "name-match")

    def test_a_guest_appearance_is_unrelated(self):
        self.assertEqual(self.grade("Alex Ferrari", "Next Level Soul Podcast"), "unrelated")

    def test_a_fan_feed_is_only_a_candidate(self):
        self.assertEqual(self.grade("Some Fan", "Athina Król Messages"), "candidate")

    def test_a_namesake_with_another_show_is_only_a_candidate(self):
        self.assertEqual(self.grade("Athina Krol", "Gardening Weekly"), "candidate")

    def test_widely_reuploaded_people_need_official_evidence(self):
        target = {"person_id": "esther-hicks", "person_name": "Esther Hicks", "names": ["Esther Hicks"]}
        domains = {"esther-hicks": {"abraham-hicks.com"}}
        self.assertEqual(self.grade("Esther Hicks", "Esther Hicks Daily", target, strict={"esther-hicks"}), "candidate")
        self.assertEqual(self.grade("Esther Hicks", "Esther Hicks Daily", target, strict={"esther-hicks"},
                                    domains=domains, linked=True), "verified")        # the official site links the show

    def test_a_feed_cannot_vouch_for_itself_by_naming_the_makers_site(self):
        target = {"person_id": "lee-carroll", "person_name": "Lee Carroll", "names": ["Lee Carroll", "Kryon"]}
        domains = {"lee-carroll": {"kryon.com"}}
        for strict in ((), ("lee-carroll",)):
            verdict, reason = find_feeds.grade(target, {"artistName": "Some Fan", "collectionName": "Kryon Channelings (fan uploads)",
                                                        "feedUrl": "https://anywhere.example/feed"}, set(strict), domains,
                                               "www.kryon.com")
            self.assertEqual(verdict, "candidate", strict)
            self.assertIn("confirm by hand", reason)
        self.assertEqual(self.grade("Someone Else", "Unrelated Show", target, domains=domains, site="www.kryon.com"), "candidate")

    def test_the_official_site_is_asked_whether_it_links_the_show(self):
        pages = {"maker.example": '<a href="https://podcasts.apple.com/us/podcast/the-show/id1289437231">listen</a>',
                 "other.example": "<p>no podcast here</p>", "byfeed.example": 'subscribe: https://Media.RSS.com/stevenobel/feed.xml'}
        yes = find_feeds.site_links_show("maker.example", "https://media.rss.com/stevenobel/feed.xml", 1289437231, pages)
        no = find_feeds.site_links_show("other.example", "https://media.rss.com/stevenobel/feed.xml", 1289437231, pages)
        by_feed = find_feeds.site_links_show("byfeed.example", "https://media.rss.com/stevenobel/feed.xml", None,
                                             {k: v.lower() for k, v in pages.items()})
        self.assertEqual((yes, no, by_feed), (True, False, True))
        self.assertEqual(find_feeds.show_needles("https://host.example/", None), [])   # a bare host proves nothing

    def test_merge_does_not_list_one_show_at_two_addresses(self):
        import io
        import contextlib
        tmp = Path(tempfile.mkdtemp(prefix="etmerge-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        registry = tmp / "podcast_feeds.csv"
        common.write_csv(registry, [{"person_id": "athina-krol", "relation": "own", "feed_url": "http://old.example/feed.xml",
                                     "apple_id": "1561735554", "verification": "name-match"}], find_feeds.REGISTRY_FIELDS)
        root = tmp / "private"
        raw = root / "sources" / "apple_candidates.jsonl"
        for url in ("https://new.example/feed.xml", "https://other-show.example/feed.xml"):
            common.append_jsonl(raw, {"kind": "result", "person_id": "athina-krol", "query": "Athina Król", "feed_url": url,
                                      "podcast_title": "Spirit Channel with Athina Król", "author": "Athina Krol", "episodes": 5,
                                      "apple_id": 1561735554 if "new" in url else 999, "genre": ""})
        saved, argv = find_feeds.REGISTRY, sys.argv
        find_feeds.REGISTRY, sys.argv = registry, ["find_feeds.py", "--root", str(root), "--merge"]
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                find_feeds.main()
        finally:
            find_feeds.REGISTRY, sys.argv = saved, argv
        urls = sorted(r["feed_url"] for r in common.read_csv(registry))
        self.assertEqual(urls, ["http://old.example/feed.xml", "https://other-show.example/feed.xml"])   # the moved show is not doubled
        self.assertIn("already listed at http://old.example/feed.xml", err.getvalue())

    def test_text_from_a_strangers_listing_is_made_safe_for_a_spreadsheet(self):
        self.assertEqual(find_feeds.clean_cell('=HYPERLINK("https://x/"&B2,"A")\nsecond line'),
                         '\'=HYPERLINK("https://x/"&B2,"A") second line')
        self.assertEqual(find_feeds.clean_cell("+1 show"), "'+1 show")
        self.assertEqual(find_feeds.clean_cell("x" * 500), "x" * 200)
        self.assertEqual(find_feeds.clean_cell("Tab\there\x00null"), "Tab here null")
        self.assertEqual(find_feeds.clean_author("athina.krol@private.example"), "")
        self.assertEqual(find_feeds.clean_author("Athina Krol"), "Athina Krol")
        self.assertEqual(find_feeds.clean_address('=HYPERLINK("https://x/")'), "")
        self.assertEqual(find_feeds.clean_address("javascript:alert(1)"), "")
        self.assertEqual(find_feeds.clean_address("https://thesoulmatrix.com/"), "https://thesoulmatrix.com/")

    def test_a_feed_served_from_the_official_domain_is_verified(self):
        target = {"person_id": "l-l-research", "person_name": "L/L Research", "names": ["L/L Research"]}
        self.assertEqual(self.grade("Anyone", "Anything", target, domains={"l-l-research": {"llresearch.org"}},
                                    feed="https://www.llresearch.org/podcast/rss.xml"), "verified")

    def test_a_lookalike_domain_is_not_official(self):
        self.assertEqual(self.grade("Some Fan", "Athina Król Messages", domains={"athina-krol": {"athinakrol.com"}},
                                    site="notathinakrol.com"), "candidate")


# --------------------------------------------------------------------------- downloading enclosures
class TestDownloadEnclosures(LaneCase):
    def rows(self, n, person="chanA", prefix="/media/"):
        out = []
        for i in range(n):
            path = f"{prefix}{i}.mp3"
            Publisher.routes.setdefault(path, (200, "audio/mpeg", AUDIO + bytes([i])))
            out.append({"video_id": common.item_id("pod", "feed", str(i)), "url": self.base + path,
                        "channel_dir": person, "title": f"Episode {i}", "duration_s": 600, "lane": "pod",
                        "relation": "own", "twin_of": "kvU9mCJr-eo" if i == 0 else ""})
        return out

    def test_dry_run_changes_nothing(self):
        self.write_queue(self.rows(3))
        done = self.download()
        self.assertIn("dry run", done.stderr)
        self.assertEqual(Publisher.hits, [])
        self.assertFalse((self.root / "audio").exists())

    def test_downloads_encodes_and_records_provenance(self):
        rows = self.rows(3)
        self.write_queue(rows)
        done = self.download("--all", "--workers", "2")
        self.assertEqual(done.returncode, 0, done.stderr)
        recs = {r["video_id"]: r for r in self.manifest()}
        self.assertEqual(len(recs), 3)
        first = recs[rows[0]["video_id"]]
        self.assertEqual(first["status"], "ok")
        self.assertEqual(first["lane"], "pod")
        self.assertEqual(first["twin_of"], "kvU9mCJr-eo")
        self.assertEqual(first["source_host"], "127.0.0.1")
        self.assertEqual(first["source_bytes"], len(AUDIO) + 1)
        self.assertEqual(len(first["source_sha256"]), 64)
        self.assertIn("complexity 5", first["target"])
        out = self.root / "audio" / first["path"]
        self.assertTrue(out.read_bytes().startswith(b"FAKEOPUS"))
        self.assertEqual(out.name, rows[0]["video_id"] + ".opus")
        self.assertFalse((self.root / "audio" / ".work").exists() and any((self.root / "audio" / ".work").iterdir()))

    def test_rerun_skips_finished_items(self):
        self.write_queue(self.rows(3))
        self.download("--all")
        first_hits = len(Publisher.hits)
        self.download("--all")
        self.assertEqual(len(Publisher.hits), first_hits)

    def test_missing_file_is_recorded_once_and_the_batch_goes_on(self):
        rows = self.rows(3)
        Publisher.routes["/media/1.mp3"] = (404, "text/plain", b"gone")
        self.write_queue(rows)
        done = self.download("--all")
        self.assertEqual(done.returncode, 0, done.stderr)
        recs = {r["video_id"]: r for r in self.manifest()}
        self.assertEqual(recs[rows[1]["video_id"]]["error_class"], "unavailable")
        self.assertEqual(sum(r["status"] == "ok" for r in recs.values()), 2)
        hits = len(Publisher.hits)
        self.download("--all")                                    # a 404 is not asked for again
        self.assertEqual(len(Publisher.hits), hits)
        self.download("--all", "--retry-failed")
        self.assertEqual(len(Publisher.hits), hits + 1)

    def test_an_html_page_is_not_saved_as_audio(self):
        rows = self.rows(1)
        Publisher.routes["/media/0.mp3"] = (200, "text/html", b"<html>please log in</html>" * 20)
        self.write_queue(rows)
        self.download("--all")
        self.assertEqual(self.manifest()[0]["error_class"], "not_audio")

    def test_three_refusals_stop_that_host_without_retrying(self):
        rows = self.rows(6)
        for i in range(6):
            Publisher.routes[f"/media/{i}.mp3"] = (403, "text/plain", b"no")
        self.write_queue(rows)
        done = self.download("--all", "--workers", "1")
        self.assertEqual(done.returncode, 3)
        self.assertIn("STOPPED", done.stderr)
        self.assertEqual(len(Publisher.hits), 3)                  # one request each, then the host is left alone
        self.assertEqual({r["error_class"] for r in self.manifest()}, {"forbidden"})
        self.assertEqual(len(self.manifest()), 3)                 # the untouched items are picked up next run

    def test_a_rate_limit_counts_as_a_refusal(self):
        rows = self.rows(4)
        for i in range(4):
            Publisher.routes[f"/media/{i}.mp3"] = (429, "text/plain", b"slow down")
        self.write_queue(rows)
        done = self.download("--all", "--workers", "1")
        self.assertEqual(done.returncode, 3)
        self.assertEqual(len(Publisher.hits), 3)

    def test_a_server_error_is_retried(self):
        rows = self.rows(1)
        calls = []

        def flaky():
            calls.append(1)
            return AUDIO
        Publisher.routes["/media/0.mp3"] = (200, "audio/mpeg", flaky)
        self.write_queue(rows)
        self.download("--all")
        self.assertEqual(self.manifest()[0]["status"], "ok")
        Publisher.routes["/media/0.mp3"] = (503, "text/plain", b"busy")
        (self.root / "audio" / "audio_manifest.jsonl").unlink()
        shutil.rmtree(self.root / "audio" / "chanA")
        Publisher.hits.clear()
        self.download("--all", "--attempts", "3")
        self.assertEqual(len(Publisher.hits), 3)                  # network-class errors are tried again
        self.assertEqual(self.manifest()[-1]["error_class"], "network")

    def test_files_over_the_size_cap_are_refused(self):
        self.write_queue(self.rows(1))
        self.download("--all", "--max-bytes", "100")
        self.assertEqual(self.manifest()[0]["error_class"], "too_large")

    def test_a_transcode_failure_is_recorded(self):
        rows = self.rows(1)
        Publisher.routes["/media/0.mp3"] = (200, "audio/mpeg", b"BADAUDIO" + b"\x00" * 100)
        self.write_queue(rows)
        self.download("--all")
        self.assertEqual(self.manifest()[0]["error_class"], "transcode")

    def test_a_url_with_spaces_works(self):
        Publisher.routes["/NEW%20AUDIO/Day%20One.mp3"] = (200, "audio/mpeg", AUDIO)
        self.write_queue([{"video_id": common.item_id("web", "x"), "url": self.base + "/NEW AUDIO/Day One.mp3",
                           "channel_dir": "chanA", "lane": "web", "relation": "file"}])
        self.download("--all")
        self.assertEqual(self.manifest()[0]["status"], "ok")
        self.assertEqual(self.manifest()[0]["lane"], "web")

    def two_shows_behind_one_first_hop(self, n=5):
        """Show A's media host (127.0.0.2) refuses everything; show B's (127.0.0.3) is healthy. Both are
        reached through the same redirecting first hop (127.0.0.1), as podcast enclosures usually are."""
        port = self.server.server_address[1]
        rows = []
        for i in range(n):
            for show, addr, status in (("A", "127.0.0.2", 403), ("B", "127.0.0.3", 200)):
                Publisher.routes[f"/r/{show}/{i}.mp3"] = (302, "location", f"http://{addr}:{port}/m/{show}/{i}.mp3".encode())
                Publisher.routes[f"/m/{show}/{i}.mp3"] = (status, "audio/mpeg", AUDIO + bytes([i]))
                rows.append({"video_id": common.item_id("pod", "show" + show, str(i)), "url": f"{self.base}/r/{show}/{i}.mp3",
                             "channel_dir": "show" + show, "lane": "pod", "relation": "own", "feed_key": "feed" + show})
        self.write_queue(rows)                                         # order A0, B0, A1, B1, ... like round-robin
        return rows

    def test_a_refusal_is_charged_to_the_host_that_refused(self):
        self.two_shows_behind_one_first_hop()
        done = self.download("--all", "--workers", "1")
        self.assertEqual(done.returncode, 3, done.stderr)
        self.assertIn("127.0.0.2", done.stderr.split("STOPPED")[-1])   # the refusing media host is named
        recs = self.manifest()
        self.assertEqual(sum(r["status"] == "ok" and r["channel_dir"] == "showB" for r in recs), 5)   # show B is complete
        refused = [h for h in Publisher.hits if h.startswith("/m/A/")]
        self.assertEqual(len(refused), 3)                              # three refusals, then show A is left alone
        self.assertEqual({r.get("final_host") for r in recs if r["status"] == "error"}, {"127.0.0.2"})

    def test_items_refused_last_time_do_not_hold_up_the_queue(self):
        self.two_shows_behind_one_first_hop(n=3)
        self.download("--all", "--workers", "1", "--limit", "2")       # A0 refused, B0 fine
        Publisher.hits.clear()
        self.download("--all", "--workers", "1", "--limit", "2")
        asked = [h for h in Publisher.hits if h.startswith("/r/")]
        self.assertNotIn("/r/A/0.mp3", asked)                          # new items first, the refused one waits

    def test_a_host_that_only_answers_errors_is_left_alone_after_a_while(self):
        rows = self.rows(10)
        for i in range(10):
            Publisher.routes[f"/media/{i}.mp3"] = (503, "text/plain", b"down")
        self.write_queue(rows)
        done = self.download("--all", "--workers", "1", "--attempts", "3", "--stop-after-failures", "2")
        self.assertEqual(done.returncode, 3, done.stderr)
        self.assertLessEqual(len(Publisher.hits), 6)                   # it used to send 30 requests
        self.assertIn("not answering", done.stderr)

    def test_only_and_shards(self):
        rows = self.rows(4, "chanA") + self.rows(4, "chanB", "/b/")
        for n, r in enumerate(rows[4:]):
            r["video_id"] = common.item_id("pod", "feedB", str(n))
        self.write_queue(rows)
        self.download("--all", "--only", "chanB")
        self.assertEqual({r["channel_dir"] for r in self.manifest()}, {"chanB"})
        self.download("--all", "--shard", "0/2")
        self.download("--all", "--shard", "1/2")
        ids = [r["video_id"] for r in self.manifest() if r["status"] == "ok"]
        self.assertEqual(len(ids), 8)
        self.assertEqual(len(set(ids)), 8)

    def test_refuses_to_write_inside_a_git_checkout(self):
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        done = self.cli("download_enclosures.py", "--root", repo / "data", "--all")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("inside a Git checkout", done.stderr)

    def test_no_cookies_proxies_or_logins_anywhere_in_the_lane(self):
        for name in ("download_enclosures.py", "feeds.py", "fetch_feeds.py", "fetch_publisher_text.py", "find_feeds.py"):
            code = "\n".join(line for line in (PIPE / name).read_text(encoding="utf-8").splitlines()
                             if not line.strip().startswith("#"))
            code = code.split('"""', 2)[2] if code.count('"""') >= 2 else code   # skip the module docstring
            code = code.replace("urllib.request.ProxyHandler({})", "")       # the one allowed use: an empty proxy table
            for word in ("cookiejar", "HTTPCookieProcessor", "ProxyHandler", "set_proxy", "Authorization",
                         "add_password", "impersonate", "urlopen("):
                self.assertNotIn(word, code, f"{name} mentions {word}")
        self.assertNotIn("Mozilla", feeds.USER_AGENT)             # says what it is, not a browser
        handlers = [type(h).__name__ for h in feeds._DIRECT.handlers]
        proxies = [h for h in feeds._DIRECT.handlers if type(h).__name__ == "ProxyHandler"]
        self.assertTrue(all(not getattr(h, "proxies", {}) for h in proxies), handlers)

    def test_proxy_settings_in_the_environment_are_ignored(self):
        Publisher.routes["/media/0.mp3"] = (200, "audio/mpeg", AUDIO)
        self.write_queue([{"video_id": common.item_id("pod", "f", "0"), "url": self.base + "/media/0.mp3",
                           "channel_dir": "chanA", "lane": "pod", "relation": "own"}])
        done = subprocess.run([sys.executable, "-I", str(PIPE / "download_enclosures.py"), "--root", str(self.root),
                               "--ffmpeg", self.ffmpeg, "--ffprobe", "ffprobe-not-installed", "--min-interval", "0",
                               "--min-bytes", "10", "--all"], capture_output=True, text=True, timeout=120,
                              env={**os.environ, "HTTP_PROXY": "http://127.0.0.1:9", "http_proxy": "http://127.0.0.1:9"})
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.manifest()[0]["status"], "ok")      # a dead proxy in the environment changes nothing


# --------------------------------------------------------------------------- choosing episodes
class TestSelectEpisodes(LaneCase):
    def write_feed(self, key, person, relation, episodes, verification="verified"):
        url = f"https://feeds.example/{key}.xml"
        real_key = feeds.feed_key(person, url)
        lines = []
        for n, (title, seconds, yt) in enumerate(episodes):
            lines.append(json.dumps({"video_id": common.item_id("pod", key, str(n)), "guid": str(n), "title": title,
                                     "published": f"2026-01-{n + 1:02d}", "duration_s": seconds,
                                     "enclosure_url": f"https://cdn.example/{key}/{n}.mp3", "transcripts": [],
                                     "youtube_ids": yt, "feed_key": real_key, "person_id": person, "relation": relation}))
        common.atomic_write_text(self.root / "feeds" / f"{real_key}.jsonl", "\n".join(lines) + "\n")
        registry = self.tmp / "registry.csv"
        rows = common.read_csv(registry) if registry.exists() else []
        rows.append({"person_id": person, "relation": relation, "feed_url": url, "verification": verification})
        common.write_csv(registry, rows, find_feeds.REGISTRY_FIELDS)

    def select(self, *extra):
        done = self.cli("select_episodes.py", "--root", self.root, "--relation", "own,host", "--registry",
                        self.tmp / "registry.csv", *extra)
        self.assertEqual(done.returncode, 0, done.stderr)
        return common.read_csv(self.root / "jobs" / "queue_enclosures.csv")

    def test_a_feed_the_registry_no_longer_accepts_is_not_queued(self):
        self.write_feed("good", "athina-krol", "own", [("Kept", 600, [])])
        self.write_feed("fan", "esther-hicks", "own", [("Re-upload", 600, [])], verification="candidate")
        common.atomic_write_text(self.root / "feeds" / "orphan--deadbeef.jsonl", json.dumps(
            {"video_id": common.item_id("pod", "x", "1"), "guid": "1", "title": "From a feed that left the registry",
             "duration_s": 600, "enclosure_url": "https://cdn.example/o/1.mp3", "feed_key": "orphan--deadbeef",
             "person_id": "athina-krol", "relation": "own"}) + "\n")
        rows = self.select()
        self.assertEqual([r["title"] for r in rows], ["Kept"])
        meta = json.loads((self.root / "jobs" / "queue_enclosures.meta.json").read_text())
        self.assertEqual(meta["dropped"]["feed_not_in_registry"], 2)

    def test_a_show_at_an_old_and_a_new_address_is_taken_from_the_live_one(self):
        ident = common.item_id("pod", "athina-krol", "guid-1")
        for name, started, status in (("aaa-old", "2026-11-01T00:00:00Z", "error"), ("zzz-new", "2026-11-13T00:00:00Z", "ok")):
            url = f"https://feeds.example/{name}.xml"
            key = feeds.feed_key("athina-krol", url)
            common.atomic_write_text(self.root / "feeds" / f"{key}.jsonl", json.dumps(
                {"video_id": ident, "guid": "guid-1", "title": "Same episode", "duration_s": 600,
                 "enclosure_url": f"https://{name}.example/1.mp3", "feed_key": key, "person_id": "athina-krol",
                 "relation": "own"}) + "\n")
            common.append_jsonl(self.root / "feeds" / "feeds_manifest.jsonl",
                                {"feed_key": key, "status": status, "started": started})
            registry = self.tmp / "registry.csv"
            rows = common.read_csv(registry) if registry.exists() else []
            rows.append({"person_id": "athina-krol", "relation": "own", "feed_url": url, "verification": "verified"})
            common.write_csv(registry, rows, find_feeds.REGISTRY_FIELDS)
        rows = self.select()
        self.assertEqual(len(rows), 1)                                        # one episode, queued once
        self.assertEqual(rows[0]["url"], "https://zzz-new.example/1.mp3")     # from the feed that still answers

    def test_the_queue_cannot_be_written_into_a_git_checkout(self):
        self.write_feed("good", "athina-krol", "own", [("Kept", 600, [])])
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        done = self.cli("select_episodes.py", "--root", self.root, "--registry", self.tmp / "registry.csv",
                        "--out", repo / "queue.csv")
        self.assertNotEqual(done.returncode, 0)
        self.assertFalse((repo / "queue.csv").exists())

    def test_own_feed_keeps_everything_and_host_feed_keeps_only_tracked_people(self):
        self.write_feed("own1", "athina-krol", "own", [("Any title at all", 600, []), ("Another", 700, [])])
        self.write_feed("host1", "host:some-show", "host",
                        [("An evening with Bashar", 3600, []), ("Cooking with friends", 1800, []),
                         ("Darryl Anka on film", 2400, []), ("Syria after Bashar al-Assad", 1500, []),
                         ("Steve Nobel and Aaron Abke together", 1600, [])])
        rows = self.select()
        self.assertEqual(sum(r["channel_dir"] == "athina-krol" for r in rows), 2)
        self.assertEqual(sum(r["channel_dir"] == "darryl-anka" for r in rows), 2)
        self.assertEqual(len(rows), 4)
        meta = json.loads((self.root / "jobs" / "queue_enclosures.meta.json").read_text())
        self.assertEqual(meta["dropped"]["host_no_tracked_person"], 2)
        self.assertEqual(meta["dropped"]["host_ambiguous"], 1)

    def test_a_show_note_link_to_an_indexed_video_makes_a_twin(self):
        index = json.loads((ET / "youtube-index" / "youtube_index.json").read_text(encoding="utf-8"))
        channel = next(c for c in index["channels"] if len(c.get("videos") or []) >= 2)
        vid = channel["videos"][0]["video_id"]
        self.write_feed("own2", channel["person"], "own", [("Unrelated wording", 600, [vid])])
        rows = self.select()
        self.assertEqual(rows[0]["twin_of"], vid)
        self.assertEqual(rows[0]["twin_method"], "link")

    def indexed_video_with_length(self):
        index = json.loads((ET / "youtube-index" / "youtube_index.json").read_text(encoding="utf-8"))
        for channel in index["channels"]:
            for video in channel.get("videos") or []:
                seconds = common.parse_duration(video.get("length_text"))
                if seconds and len(feeds.tokens(video.get("title") or "")) >= 4 and not select_episodes.numbers_in(video["title"]):
                    return channel["person"], video, seconds
        self.fail("the index has no video with a length and a four-word title")

    def test_same_title_and_length_make_a_twin_and_a_different_title_does_not(self):
        person, video, seconds = self.indexed_video_with_length()
        self.write_feed("own3", person, "own", [(video["title"], seconds + 20, []), ("Zebra quartz umbrella", seconds, [])])
        rows = {r["title"]: r for r in self.select()}
        self.assertEqual(rows[video["title"]]["twin_of"], video["video_id"])
        self.assertEqual(rows[video["title"]]["twin_method"], "title")
        self.assertEqual(rows["Zebra quartz umbrella"]["twin_of"], "")

    def test_a_title_match_without_comparable_lengths_is_only_a_candidate(self):
        person, video, seconds = self.indexed_video_with_length()
        self.write_feed("own4", person, "own", [(video["title"], None, [])])
        row = self.select()[0]
        self.assertEqual(row["twin_of"], "")                       # not counted
        self.assertEqual(row["twin_candidate"], video["video_id"])   # but kept for a person to look at

    def test_lengths_that_disagree_are_not_a_twin(self):
        person, video, seconds = self.indexed_video_with_length()
        self.write_feed("own5", person, "own", [(video["title"], seconds * 2, [])])
        row = self.select()[0]
        self.assertEqual((row["twin_of"], row["twin_candidate"]), ("", ""))

    def test_day_10_is_not_day_11(self):
        videos = [{"video_id": "RdDRrCJrj34", "title": "Enjoy our Day 10 class from Walk With Jesus!", "duration_s": 2045}]
        for title, seconds in (("Enjoy our Day 11 class from Walk With Jesus!", 2100), ("Enjoy our Day 12 class from Walk With Jesus!", 1900),
                               ("Building a Contact Field - Part 3", 2045)):
            twin, method, score, candidate = select_episodes.find_twin({"title": title, "duration_s": seconds}, videos, 0.72, 0.12)
            self.assertEqual((twin, candidate), ("", ""), title)
        twin, method, _, _ = select_episodes.find_twin({"title": "Enjoy our Day 10 class from Walk With Jesus! (2026)", "duration_s": 2050},
                                                       videos, 0.72, 0.12)
        self.assertEqual((twin, method), ("RdDRrCJrj34", "title"))     # a year in one title does not matter
        self.assertEqual(select_episodes.numbers_in("Day 010, part 2 (2026)"), ["10", "2"])

    def test_titles_in_other_scripts_are_compared_by_their_words(self):
        self.assertEqual(feeds.title_similarity("銀河連合からのメッセージ 2026", "プレアデスの光 2026"), 0.5)   # only the year is shared
        self.assertLess(feeds.title_similarity("銀河連合 メッセージ 光の扉", "プレアデス 瞑想 朝の祈り"), 0.01)
        self.assertEqual(feeds.title_similarity("Послание Плеяд сегодня", "послание плеяд сегодня"), 1.0)

    def test_a_link_in_every_episode_is_a_promotion_not_a_twin(self):
        person, video, seconds = self.indexed_video_with_length()
        promo = video["video_id"]
        self.write_feed("own6", person, "own", [(f"Unrelated talk number {i}", 600 + i, [promo]) for i in range(8)])
        rows = self.select()
        self.assertEqual(len(rows), 8)
        self.assertEqual({r["twin_of"] for r in rows}, {""})

    def test_one_video_is_the_twin_of_one_item(self):
        person, video, seconds = self.indexed_video_with_length()
        self.write_feed("own7", person, "own", [(video["title"], seconds, []), (video["title"] + " (replay)", seconds + 5, []),
                                                ("Other", 500, []), ("Other two", 501, []), ("Other three", 502, []),
                                                ("Other four", 503, []), ("Other five", 504, []), ("Something else", 505, []),
                                                ("And another", 506, []), ("Linked one", 507, [video["video_id"]])])
        rows = self.select()
        holders = [r for r in rows if r["twin_of"] == video["video_id"]]
        self.assertEqual(len(holders), 1)
        self.assertEqual(holders[0]["twin_method"], "link")                           # a link beats a title match
        self.assertEqual(sum(r["twin_candidate"] == video["video_id"] for r in rows), 2)

    def test_interview_titles_are_assigned_carefully(self):
        rules = select_episodes.matchers(find_feeds.load_targets())
        who = lambda title: select_episodes.assign_person(title, rules)   # noqa: E731
        self.assertEqual(who("An evening with Bashar (channeled by Darryl Anka)")[0], "darryl-anka")
        self.assertEqual(who("Syria after Bashar al-Assad: what comes next"), ("", "nobody_named"))
        self.assertEqual(who("ATHINA KROL on spirit guides")[0], "athina-krol")       # no accent, other case
        self.assertEqual(who("Athina Król returns")[0], "athina-krol")
        self.assertEqual(who("The Law of One explained | Brian Scott"), ("", "weak_alias_only"))
        self.assertEqual(who("Steve Nobel on the Law of One and the ascension timeline")[0], "steve-nobel")
        self.assertEqual(who("Cooking with friends"), ("", "nobody_named"))
        self.assertEqual(who("Steve Nobel and Aaron Abke in conversation"), ("", "ambiguous"))
        self.assertEqual(who("Basharat Ali on economics"), ("", "nobody_named"))

    def test_names_with_a_qualifier_are_matched_by_each_part(self):
        self.assertEqual(select_episodes.name_parts("JZ Knight / Ramtha"), ["jz knight", "ramtha"])
        self.assertEqual(select_episodes.name_parts("Jordan Younger (The Balanced Blonde)"), ["jordan younger", "the balanced blonde"])
        rules = select_episodes.matchers([{"person_id": "j-z-knight", "names": ["JZ Knight / Ramtha"]}])
        self.assertEqual(select_episodes.assign_person("Ramtha on the nature of reality", rules)[0], "j-z-knight")
        self.assertEqual(select_episodes.assign_person("JZ Knight interview", rules)[0], "j-z-knight")

    def test_one_episode_in_two_feeds_is_queued_once(self):
        self.write_feed("a", "athina-krol", "own", [("Same talk", 900, [])])
        self.write_feed("b", "athina-krol", "own", [("Same talk", 900, []), ("Same talk", 1200, [])])
        self.assertEqual(len(self.select()), 2)                   # equal title and length is one recording

    def test_sampling_is_reproducible_and_round_robin_starts_everyone_early(self):
        self.write_feed("p1", "athina-krol", "own", [(f"A{i}", 600, []) for i in range(8)])
        self.write_feed("p2", "aaron-abke", "own", [(f"B{i}", 600, []) for i in range(8)])
        first = [r["video_id"] for r in self.select("--per-channel", "3", "--seed", "7")]
        again = [r["video_id"] for r in self.select("--per-channel", "3", "--seed", "7")]
        other = [r["video_id"] for r in self.select("--per-channel", "3", "--seed", "8")]
        self.assertEqual(first, again)
        self.assertEqual(len(first), 6)
        self.assertNotEqual(sorted(first), sorted(other))
        people = [r["channel_dir"] for r in self.select()][:2]
        self.assertEqual(sorted(people), ["aaron-abke", "athina-krol"])

    def test_filters(self):
        self.write_feed("p1", "athina-krol", "own", [("Short", 120, []), ("Long", 7200, []), ("Unknown", None, [])])
        self.assertEqual({r["title"] for r in self.select("--min-seconds", "300")}, {"Long", "Unknown"})
        self.assertEqual({r["title"] for r in self.select("--max-seconds", "3600")}, {"Short", "Unknown"})
        self.assertEqual(len(self.select("--max-hours", "1", "--assume-minutes", "30")), 2)


# --------------------------------------------------------------------------- reading feeds
class TestFetchFeeds(LaneCase):
    def registry(self, rows):
        path = self.tmp / "registry.csv"
        common.write_csv(path, rows, find_feeds.REGISTRY_FIELDS)
        return path

    def run_fetch(self, registry, *extra):
        return self.cli("fetch_feeds.py", "--root", self.root, "--registry", registry, "--min-interval", "0", *extra)

    def test_only_accepted_feeds_are_read(self):
        Publisher.routes["/ok.xml"] = (200, "text/xml", feed_xml([item("g1", "One", "https://c.example/1.mp3")]))
        Publisher.routes["/cand.xml"] = (200, "text/xml", feed_xml([item("g1", "One", "https://c.example/1.mp3")]))
        registry = self.registry([
            {"person_id": "athina-krol", "relation": "own", "feed_url": self.base + "/ok.xml", "verification": "name-match"},
            {"person_id": "esther-hicks", "relation": "own", "feed_url": self.base + "/cand.xml", "verification": "candidate"}])
        done = self.run_fetch(registry)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(Publisher.hits, ["/ok.xml"])
        key = feeds.feed_key("athina-krol", self.base + "/ok.xml")
        episodes = common.read_jsonl(self.root / "feeds" / f"{key}.jsonl")
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["person_id"], "athina-krol")
        self.assertEqual(episodes[0]["relation"], "own")

    def test_a_fresh_feed_is_not_read_again_and_a_broken_one_is_recorded(self):
        Publisher.routes["/ok.xml"] = (200, "text/xml", feed_xml([item("g1", "One", "https://c.example/1.mp3")]))
        Publisher.routes["/bad.xml"] = (200, "text/xml", b"<rss><channel><item>")
        registry = self.registry([
            {"person_id": "a", "relation": "own", "feed_url": self.base + "/ok.xml", "verification": "verified"},
            {"person_id": "b", "relation": "own", "feed_url": self.base + "/bad.xml", "verification": "verified"}])
        self.run_fetch(registry)
        manifest = {r["person_id"]: r for r in common.read_jsonl(self.root / "feeds" / "feeds_manifest.jsonl")}
        self.assertEqual(manifest["a"]["status"], "ok")
        self.assertEqual(manifest["b"]["error_class"], "parse")
        Publisher.hits.clear()
        self.run_fetch(registry)
        self.assertEqual(Publisher.hits, ["/bad.xml"])           # only the one that failed is tried again


# --------------------------------------------------------------------------- publisher texts
class TestPublisherText(unittest.TestCase):
    def test_page_text_keeps_the_article_and_drops_the_chrome(self):
        page = ("<html><body><nav>Menu Home Shop</nav><main><h1>Session 1</h1><p>First   paragraph.</p>"
                "<script>var x = 'not text';</script><p>Second paragraph.</p><form>Subscribe</form></main>"
                "<footer>Copyright notice</footer></body></html>")
        text = fetch_publisher_text.html_to_text(page)
        self.assertEqual(text, "Session 1\nFirst paragraph.\nSecond paragraph.")

    def test_webvtt_and_srt_lose_their_timings(self):
        vtt = "WEBVTT\n\n1\n00:00:00.000 --> 00:00:02.000\n<v Host>Hello there\n\n2\n00:00:02.000 --> 00:00:04.000\nHello there\nand welcome\n"
        self.assertEqual(fetch_publisher_text.cues_to_text(vtt), "Hello there\nand welcome")
        kind, text = fetch_publisher_text.to_text(vtt.encode(), "text/vtt", "text/vtt", "https://x/1.vtt")
        self.assertEqual((kind, text), ("vtt", "Hello there\nand welcome"))
        srt = "1\n00:00:00,000 --> 00:00:02,000\nOne line\n\n2\n00:00:02,000 --> 00:00:03,000\nTwo line\n"
        self.assertEqual(fetch_publisher_text.to_text(srt.encode(), "application/x-subrip", "", "https://x/1.srt"),
                         ("srt", "One line\nTwo line"))

    def test_podcast_json_transcript(self):
        body = json.dumps({"segments": [{"speaker": "A", "body": "Hi."}, {"speaker": "A", "body": "Again."},
                                        {"speaker": "B", "body": "Reply."}]})
        kind, text = fetch_publisher_text.to_text(body.encode(), "application/json", "", "https://x/1.json")
        self.assertEqual(kind, "json")
        self.assertEqual(text, "A: Hi. Again. \nB: Reply.")

    def test_media_links_on_a_page(self):
        page = '<a href="https://s3.example/audio/session-1.m4a">audio</a><img src="/x.png"><a href="/y.MP3?dl=1">'
        self.assertEqual(fetch_publisher_text.MEDIA_LINK.findall(page),
                         ["https://s3.example/audio/session-1.m4a", "/y.MP3?dl=1"])


class TestPublisherTextRun(LaneCase):
    def test_robots_rules_are_obeyed_and_texts_are_saved_outside_git(self):
        Publisher.routes["/robots.txt"] = (200, "text/plain", b"User-agent: *\nDisallow: /private/\n")
        words = " ".join(f"word{i}" for i in range(80))
        Publisher.routes["/open/1.vtt"] = (200, "text/vtt", f"WEBVTT\n\n00:00.000 --> 00:05.000\n{words}\n".encode())
        Publisher.routes["/private/2.vtt"] = (200, "text/vtt", f"WEBVTT\n\n00:00.000 --> 00:05.000\n{words}\n".encode())
        a, b = common.item_id("pod", "f", "1"), common.item_id("pod", "f", "2")
        self.write_queue([
            {"video_id": a, "url": "https://c.example/1.mp3", "channel_dir": "chanA", "transcript_url": self.base + "/open/1.vtt",
             "transcript_type": "text/vtt"},
            {"video_id": b, "url": "https://c.example/2.mp3", "channel_dir": "chanA", "transcript_url": self.base + "/private/2.vtt",
             "transcript_type": "text/vtt"}])
        done = self.cli("fetch_publisher_text.py", "--root", self.root, "--kinds", "episodes", "--all", "--min-interval", "0")
        self.assertEqual(done.returncode, 0, done.stderr)
        recs = {r["video_id"]: r for r in common.read_jsonl(self.root / "transcripts_publisher" / "publisher_text_manifest.jsonl")}
        self.assertEqual(recs[a]["status"], "ok")
        self.assertEqual(recs[a]["n_words"], 80)
        self.assertEqual(recs[b]["error_class"], "robots")
        self.assertNotIn("/private/2.vtt", Publisher.hits)
        self.assertTrue((self.root / "transcripts_publisher" / "chanA" / f"{a}.txt").exists())

    def text_queue(self, n):
        words = " ".join(f"word{i}" for i in range(80))
        rows = []
        for i in range(n):
            Publisher.routes[f"/t/{i}.vtt"] = (200, "text/vtt", f"WEBVTT\n\n00:00.000 --> 00:05.000\n{words}\n".encode())
            rows.append({"video_id": common.item_id("pod", "t", str(i)), "url": f"https://c.example/{i}.mp3",
                         "channel_dir": "chanA", "transcript_url": f"{self.base}/t/{i}.vtt", "transcript_type": "text/vtt"})
        self.write_queue(rows)
        return rows

    def fetch_text(self, *extra):
        return self.cli("fetch_publisher_text.py", "--root", self.root, "--kinds", "episodes", "--all",
                        "--min-interval", "0", *extra)

    def test_a_robots_file_that_could_not_be_read_is_not_a_refusal_for_good(self):
        rows = self.text_queue(4)
        Publisher.routes["/robots.txt"] = (503, "text/plain", b"try later")
        first = self.fetch_text()
        manifest = self.root / "transcripts_publisher" / "publisher_text_manifest.jsonl"
        classes = {r["error_class"] for r in common.read_jsonl(manifest)}
        self.assertEqual(classes, {"network"}, first.stderr)           # it used to say "robots" and never try again
        self.assertEqual([h for h in Publisher.hits if h.startswith("/t/")], [])   # and nothing was fetched meanwhile
        Publisher.routes["/robots.txt"] = (200, "text/plain", b"User-agent: *\nAllow: /\n")
        self.fetch_text()                                               # the site is back: an ordinary rerun gets them
        latest = common.latest_by_key(common.read_jsonl(manifest))
        self.assertEqual({r["status"] for r in latest.values()}, {"ok"})
        self.assertEqual(len(latest), len(rows))

    def test_a_site_with_no_robots_file_is_open(self):
        self.text_queue(2)                                              # /robots.txt answers 404
        self.fetch_text()
        latest = common.latest_by_key(common.read_jsonl(self.root / "transcripts_publisher" / "publisher_text_manifest.jsonl"))
        self.assertEqual({r["status"] for r in latest.values()}, {"ok"})

    def test_a_malformed_address_is_recorded_and_the_batch_goes_on(self):
        rows = self.text_queue(2)
        rows.append({"video_id": common.item_id("pod", "t", "bad"), "url": "https://c.example/b.mp3", "channel_dir": "chanA",
                     "transcript_url": "http://127.0.0.1:99999999/x.vtt", "transcript_type": "text/vtt"})
        self.write_queue(rows)
        done = self.fetch_text()
        self.assertEqual(done.returncode, 0, done.stderr)
        latest = common.latest_by_key(common.read_jsonl(self.root / "transcripts_publisher" / "publisher_text_manifest.jsonl"))
        self.assertEqual(sum(r["status"] == "ok" for r in latest.values()), 2)
        self.assertEqual(latest[rows[-1]["video_id"]]["status"], "error")

    def test_dry_run_fetches_nothing(self):
        self.write_queue([{"video_id": common.item_id("pod", "f", "1"), "url": "https://c.example/1.mp3",
                           "channel_dir": "chanA", "transcript_url": self.base + "/1.vtt"}])
        done = self.cli("fetch_publisher_text.py", "--root", self.root, "--kinds", "episodes")
        self.assertIn("dry run", done.stderr)
        self.assertEqual(Publisher.hits, [])


# --------------------------------------------------------------------------- catalogue
class TestCatalog(LaneCase):
    def test_coverage_holds_numbers_only_and_text_counts_once(self):
        ident = common.item_id("pod", "f", "1")
        self.write_queue([{"video_id": ident, "url": "https://c.example/1.mp3", "channel_dir": "athina-krol",
                           "title": "A private title", "duration_s": 600, "lane": "pod", "relation": "own",
                           "twin_of": "kvU9mCJr-eo", "twin_method": "title"}])
        common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                            {"video_id": ident, "channel_dir": "athina-krol", "lane": "pod", "status": "ok",
                             "path": f"athina-krol/{ident}.opus", "bytes": 10, "duration_s": 600.0,
                             "source_host": "c.example"})
        common.append_jsonl(self.root / "transcripts" / "transcripts_manifest.jsonl",
                            {"video_id": ident, "channel_dir": "athina-krol", "status": "ok", "model": "base.en", "n_words": 1500})
        done = self.cli("catalog.py", "--root", self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        catalog = {r["item_id"]: r for r in common.read_csv(self.root / "catalog" / "catalog.csv")}
        self.assertEqual(catalog[ident]["title"], "A private title")
        self.assertEqual(catalog[ident]["has_text"], "1")
        coverage_text = (self.root / "public_export" / "coverage.csv").read_text(encoding="utf-8")
        self.assertNotIn("A private title", coverage_text)
        self.assertNotIn("c.example", coverage_text)
        row = next(r for r in common.read_csv(self.root / "public_export" / "coverage.csv") if r["person_id"] == "athina-krol")
        self.assertEqual((row["audio_ok"], row["asr_transcripts"], row["items_with_text"], row["youtube_twins"]),
                         ("1", "1", "1", "1"))
        self.assertEqual(row["audio_hours"], "0.2")
        summary = json.loads((self.root / "public_export" / "coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["people_with_audio"], 1)
        self.assertEqual(summary["totals"]["audio_ok"], 1)


# --------------------------------------------------------------------------- sync to a private store
FAKE_GH = r"""
import json, os, shutil, sys, hashlib
from pathlib import Path
args = sys.argv[1:]
store = Path(os.environ["FAKE_GH_DIR"])
with open(os.environ["FAKE_GH_LOG"], "a") as fh:
    fh.write(" ".join(args[:4]) + "\n")
if args[0] == "api":
    print(os.environ.get("FAKE_GH_VISIBILITY", "private"))
    sys.exit(0)
tag = args[2]
folder = store / tag
if args[:2] == ["release", "view"]:
    if os.environ.get("FAKE_GH_VIEW_FAILS"):
        sys.stderr.write("error connecting to api.github.com\n"); sys.exit(1)
    if not folder.exists():
        sys.stderr.write("release not found\n"); sys.exit(1)
    assets = []
    for f in sorted(folder.iterdir()):
        size = f.stat().st_size + (1 if os.environ.get("FAKE_GH_WRONG_SIZE") else 0)
        assets.append({"name": f.name, "size": size, "digest": "sha256:" + hashlib.sha256(f.read_bytes()).hexdigest()})
    print(json.dumps({"assets": assets})); sys.exit(0)
if args[:2] == ["release", "create"]:
    folder.mkdir(parents=True, exist_ok=True); sys.exit(0)
if args[:2] == ["release", "upload"]:
    if not folder.exists():
        sys.stderr.write("release not found\n"); sys.exit(1)       # as the real gh answers
    shutil.copyfile(args[3], folder / Path(args[3]).name); sys.exit(0)
if args[:2] == ["release", "download"]:
    name, dest = args[args.index("-p") + 1], Path(args[args.index("-D") + 1])
    shutil.copyfile(folder / name, dest / name); sys.exit(0)
sys.exit(2)
"""


class TestSync(LaneCase):
    def setUp(self):
        super().setUp()
        self.gh = make_tool(self.tmp / "bin", "gh", FAKE_GH)
        self.gh_dir, self.gh_log = self.tmp / "ghstore", self.tmp / "gh.log"
        self.gh_dir.mkdir()
        self.ids = [common.item_id("pod", "f", str(i)) for i in range(3)]
        for n, ident in enumerate(self.ids):
            f = self.root / "audio" / "chanA" / f"{ident}.opus"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"FAKEOPUS" + bytes([n]) * (1000 + n))
            common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                                {"video_id": ident, "channel_dir": "chanA", "lane": "pod", "status": "ok",
                                 "path": f"chanA/{ident}.opus", "bytes": f.stat().st_size, "duration_s": 60.0})
        t = self.root / "transcripts" / "chanA"
        t.mkdir(parents=True)
        (t / f"{self.ids[0]}.txt").write_text("machine words\n")
        (t / f"{self.ids[0]}.json").write_text("{}\n")
        common.append_jsonl(self.root / "transcripts" / "transcripts_manifest.jsonl",
                            {"video_id": self.ids[0], "channel_dir": "chanA", "status": "ok", "n_words": 2})

    def sync(self, command, store, *extra, env=None):
        full = {**os.environ, "FAKE_GH_DIR": str(self.gh_dir), "FAKE_GH_LOG": str(self.gh_log), **(env or {})}
        return subprocess.run([sys.executable, "-I", str(PIPE / "sync_archive.py"), command, "--root", str(self.root),
                               "--store", store, "--gh", self.gh, *map(str, extra)], capture_output=True, text=True,
                              timeout=120, env=full)

    def local_audio(self):
        return sorted(p.name for p in (self.root / "audio" / "chanA").glob("*.opus"))

    def test_folder_store_copies_checks_and_keeps_locals_by_default(self):
        store = self.tmp / "disk"
        done = self.sync("push", f"dir:{store}")
        self.assertEqual(done.returncode, 0, done.stderr)
        for ident in self.ids:
            self.assertEqual((store / "audio" / "chanA" / f"{ident}.opus").read_bytes(),
                             (self.root / "audio" / "chanA" / f"{ident}.opus").read_bytes())
        self.assertTrue((store / "transcripts" / "chanA" / f"{self.ids[0]}.txt").exists())
        self.assertTrue((store / "audio" / "audio_manifest.jsonl").exists())      # manifests travel too
        self.assertEqual(len(self.local_audio()), 3)                              # nothing deleted unless asked
        ledger = common.read_jsonl(self.root / "sync" / "sync_manifest.jsonl")
        self.assertEqual(len(ledger), 4)                                          # 3 audio + 1 transcript
        self.assertTrue(all(r["verified"] for r in ledger))

    def test_delete_audio_frees_the_disk_but_keeps_texts_and_manifests(self):
        store = self.tmp / "disk"
        done = self.sync("push", f"dir:{store}", "--delete", "audio")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.local_audio(), [])
        self.assertTrue((self.root / "transcripts" / "chanA" / f"{self.ids[0]}.txt").exists())
        self.assertTrue((self.root / "audio" / "audio_manifest.jsonl").exists())
        again = self.sync("push", f"dir:{store}", "--delete", "audio")            # nothing left to do
        self.assertIn("to upload 0", again.stderr)

    def test_a_later_run_deletes_what_an_earlier_run_stored(self):
        store = self.tmp / "disk"
        self.sync("push", f"dir:{store}")
        self.assertEqual(len(self.local_audio()), 3)
        self.sync("push", f"dir:{store}", "--delete", "audio")
        self.assertEqual(self.local_audio(), [])

    def test_a_store_inside_a_git_checkout_is_refused(self):
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        done = self.sync("push", f"dir:{repo / 'archive'}", "--delete", "audio")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("inside a Git checkout", done.stderr)
        self.assertEqual(len(self.local_audio()), 3)

    def test_a_public_repository_is_refused_and_nothing_is_uploaded_or_deleted(self):
        for visibility in ("public", "internal", ""):
            done = self.sync("push", "gh:someone/archive@audio-v1", "--delete", "all", env={"FAKE_GH_VISIBILITY": visibility})
            self.assertEqual(done.returncode, 5, visibility)
            self.assertIn("refusing to upload", done.stderr)
        self.assertEqual(len(self.local_audio()), 3)
        self.assertFalse(any(self.gh_dir.iterdir()))
        self.assertNotIn("release upload", self.gh_log.read_text())
        self.assertFalse((self.root / "sync" / "sync_manifest.jsonl").exists())

    def test_private_repository_gets_bundles_and_pull_brings_them_back(self):
        originals = {ident: (self.root / "audio" / "chanA" / f"{ident}.opus").read_bytes() for ident in self.ids}
        done = self.sync("push", "gh:someone/archive@audio-v1", "--delete", "audio")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.local_audio(), [])
        names = sorted(f.name for f in (self.gh_dir / "audio-v1").iterdir())
        self.assertEqual(sum(n.startswith("audio-") for n in names), 1)
        self.assertEqual(sum(n.startswith("asr-") for n in names), 1)
        self.assertIn("manifests.tar", names)
        back = self.sync("pull", "gh:someone/archive@audio-v1", "--kinds", "audio")
        self.assertEqual(back.returncode, 0, back.stderr)
        for ident, data in originals.items():
            self.assertEqual((self.root / "audio" / "chanA" / f"{ident}.opus").read_bytes(), data)

    def test_bundles_respect_the_item_cap(self):
        done = self.sync("push", "gh:someone/archive@audio-v1", "--kinds", "audio", "--bundle-items", "2")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(sum(f.name.startswith("audio-") for f in (self.gh_dir / "audio-v1").iterdir()), 2)

    def test_a_failed_check_deletes_nothing(self):
        done = self.sync("push", "gh:someone/archive@audio-v1", "--delete", "audio", env={"FAKE_GH_WRONG_SIZE": "1"})
        self.assertEqual(done.returncode, 5)
        self.assertIn("different size", done.stderr)
        self.assertEqual(len(self.local_audio()), 3)
        self.assertFalse((self.root / "sync" / "sync_manifest.jsonl").exists())

    def test_unfinished_audio_is_never_moved(self):
        bad = common.item_id("pod", "f", "bad")
        common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                            {"video_id": bad, "channel_dir": "chanA", "status": "error", "error_class": "network"})
        (self.root / "audio" / "chanA" / f"{self.ids[1]}.opus").write_bytes(b"short")   # size no longer matches
        store = self.tmp / "disk"
        self.sync("push", f"dir:{store}", "--kinds", "audio", "--delete", "audio")
        stored = sorted(p.stem for p in (store / "audio" / "chanA").glob("*.opus"))
        self.assertEqual(stored, sorted([self.ids[0], self.ids[2]]))
        self.assertEqual(self.local_audio(), [f"{self.ids[1]}.opus"])                # the doubtful file stays put

    # ---- findings of the 2026-11-13 review, each reproduced before it was fixed
    def test_a_store_that_is_the_private_folder_is_refused_and_nothing_is_lost(self):
        for attempt in (1, 2):                                    # the loss used to happen on the second run
            done = self.sync("push", f"dir:{self.root}", "--delete", "all")
            self.assertEqual(done.returncode, 5, f"run {attempt}: {done.stderr}")
            self.assertIn("same folder", done.stderr)
            self.assertEqual(len(self.local_audio()), 3)
        self.assertFalse((self.root / "sync" / "sync_manifest.jsonl").exists())

    def test_a_store_reached_through_a_link_onto_the_same_files_loses_nothing(self):
        disk = self.tmp / "disk"
        (disk / "audio").mkdir(parents=True)
        shutil.move(str(self.root / "audio" / "chanA"), str(disk / "audio" / "chanA"))
        (self.root / "audio" / "chanA").symlink_to(disk / "audio" / "chanA", target_is_directory=True)
        for attempt in (1, 2):
            done = self.sync("push", f"dir:{disk}", "--kinds", "audio", "--delete", "audio")
            self.assertEqual(done.returncode, 5, f"run {attempt}: {done.stderr}")
        self.assertEqual(len(list((disk / "audio" / "chanA").glob("*.opus"))), 3)

    def test_a_file_that_changed_after_its_upload_is_uploaded_again_not_deleted(self):
        store = self.tmp / "disk"
        self.sync("push", f"dir:{store}", "--kinds", "audio")
        target = self.root / "audio" / "chanA" / f"{self.ids[0]}.opus"
        target.write_bytes(b"FAKEOPUS" + b"new encode at another bitrate" * 50)
        common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                            {"video_id": self.ids[0], "channel_dir": "chanA", "lane": "pod", "status": "ok",
                             "path": f"chanA/{self.ids[0]}.opus", "bytes": target.stat().st_size, "duration_s": 60.0})
        fresh = target.read_bytes()
        done = self.sync("push", f"dir:{store}", "--kinds", "audio", "--delete", "audio")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual((store / "audio" / "chanA" / f"{self.ids[0]}.opus").read_bytes(), fresh)   # the new version is stored
        self.assertEqual(self.local_audio(), [])

    def test_same_size_different_bytes_is_still_a_different_file(self):
        store = self.tmp / "disk"
        self.sync("push", f"dir:{store}", "--kinds", "audio")
        target = self.root / "audio" / "chanA" / f"{self.ids[0]}.opus"
        swapped = bytes(reversed(target.read_bytes()))
        target.write_bytes(swapped)                                # same length, other content
        done = self.sync("push", f"dir:{store}", "--kinds", "audio", "--delete", "audio")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual((store / "audio" / "chanA" / f"{self.ids[0]}.opus").read_bytes(), swapped)

    def test_an_emptied_store_is_noticed_and_local_files_are_kept_and_sent_again(self):
        store = self.tmp / "disk"
        self.sync("push", f"dir:{store}", "--kinds", "audio")      # stored, locals kept
        shutil.rmtree(store)                                       # another disk at that path, or it was wiped
        done = self.sync("push", f"dir:{store}", "--kinds", "audio", "--delete", "audio")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("no longer in the store", done.stderr)
        self.assertEqual(len(list((store / "audio" / "chanA").glob("*.opus"))), 3)   # sent again
        self.assertEqual(self.local_audio(), [])                   # and only then deleted

    def test_a_deleted_release_is_noticed_before_local_files_are_removed(self):
        self.sync("push", "gh:someone/archive@audio-v1", "--kinds", "audio")
        shutil.rmtree(self.gh_dir / "audio-v1")                    # the release was deleted on GitHub
        done = self.sync("push", "gh:someone/archive@audio-v1", "--kinds", "audio", "--delete", "audio")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("no longer in the store", done.stderr)
        self.assertEqual(sum(f.name.startswith("audio-") for f in (self.gh_dir / "audio-v1").iterdir()), 1)
        self.assertEqual(self.local_audio(), [])

    def test_the_first_push_to_a_new_release_works(self):
        self.assertFalse((self.gh_dir / "audio-v1").exists())
        done = self.sync("push", "gh:someone/archive@audio-v1", "--kinds", "audio", "--delete", "audio")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.local_audio(), [])

    def test_a_github_outage_is_reported_as_such_and_no_release_is_created(self):
        done = self.sync("push", "gh:someone/archive@audio-v1", "--kinds", "audio", "--delete", "audio",
                         env={"FAKE_GH_VIEW_FAILS": "1"})
        self.assertEqual(done.returncode, 5)
        self.assertIn("error connecting", done.stderr)
        self.assertNotIn("release create", self.gh_log.read_text())
        self.assertEqual(len(self.local_audio()), 3)

    def test_pull_does_not_overwrite_a_newer_local_file(self):
        store = self.tmp / "disk"
        self.sync("push", f"dir:{store}", "--kinds", "asr")
        local = self.root / "transcripts" / "chanA" / f"{self.ids[0]}.txt"
        local.write_text("made again with a better model\n")
        self.sync("pull", f"dir:{store}", "--kinds", "asr")
        self.assertEqual(local.read_text(), "made again with a better model\n")
        self.sync("pull", f"dir:{store}", "--kinds", "asr", "--overwrite")
        self.assertEqual(local.read_text(), "machine words\n")

    def test_archived_audio_is_not_downloaded_again(self):
        rows = []
        for i in range(3):
            Publisher.routes[f"/m/{i}.mp3"] = (200, "audio/mpeg", AUDIO + bytes([i]))
            rows.append({"video_id": common.item_id("pod", "g", str(i)), "url": f"{self.base}/m/{i}.mp3",
                         "channel_dir": "chanB", "lane": "pod", "relation": "own"})
        self.write_queue(rows)
        self.download("--all")
        self.assertEqual(len(Publisher.hits), 3)
        store = self.tmp / "disk"
        self.sync("push", f"dir:{store}", "--kinds", "audio", "--only", "chanB", "--delete", "audio")
        self.assertEqual(list((self.root / "audio" / "chanB").glob("*.opus")), [])
        again = self.download("--all")                              # the owner runs the same command again
        self.assertEqual(len(Publisher.hits), 3, again.stderr)      # nothing is asked for twice
        self.assertIn("to do 0", again.stderr)

    def test_captions_travel_to_the_store_too(self):
        caps = self.root / "captions" / "chanA"
        caps.mkdir(parents=True)
        vid = "kvU9mCJr-eo"
        (caps / f"{vid}.en.vtt").write_text("WEBVTT\n")
        (caps / f"{vid}.txt").write_text("words\n")
        common.append_jsonl(self.root / "captions" / "captions_manifest.jsonl",
                            {"video_id": vid, "channel_dir": "chanA", "status": "ok", "tracks": ["en"], "preferred": "en"})
        store = self.tmp / "disk"
        done = self.sync("push", f"dir:{store}", "--kinds", "captions")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue((store / "captions" / "chanA" / f"{vid}.en.vtt").exists())
        self.assertTrue((store / "captions" / "captions_manifest.jsonl").exists())

    def test_status_reports_both_sides(self):
        store = self.tmp / "disk"
        self.sync("push", f"dir:{store}", "--kinds", "audio", "--limit", "2")
        done = self.sync("status", f"dir:{store}")
        report = json.loads(done.stdout)
        self.assertEqual(report["kinds"]["audio"]["on_disk"], 3)
        self.assertEqual(report["kinds"]["audio"]["in_store"], 2)
        self.assertEqual(report["kinds"]["audio"]["on_disk_not_stored"], 1)


# --------------------------------------------------------------------------- YouTube captions and the runner
FAKE_YTDLP_SUBS = r"""
import os, re, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as fh:
    fh.write(" ".join(args) + "\n")
if "--version" in args:
    print("2099.01.01-fake"); sys.exit(0)
vid = re.search(r"v=([A-Za-z0-9_-]{11})", args[-1]).group(1)
work = Path(args[args.index("-o") + 1]).parent
if vid.startswith("BOTC"):
    sys.stderr.write("ERROR: [youtube] %s: Sign in to confirm you're not a bot\n" % vid); sys.exit(1)
if vid.startswith("NOCA"):
    sys.exit(0)
if vid.startswith("IPBL"):
    sys.stderr.write("ERROR: [youtube] %s: All player responses are invalid. Your IP is likely being blocked by Youtube\n" % vid)
    sys.exit(1)
work.mkdir(parents=True, exist_ok=True)
if vid.startswith("PART"):          # one track arrives, the next is refused: yt-dlp exits 1 and leaves the first
    (work / (vid + ".en-orig.vtt")).write_text("WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nonly the first track\n")
    sys.stderr.write("ERROR: Unable to download video subtitles for 'en': HTTP Error 429: Too Many Requests\n")
    sys.exit(1)
if "--skip-download" in args:
    cue = "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nhello from %s\n\n00:00:02.000 --> 00:00:04.000\nsecond line\n" % vid
    (work / (vid + ".en.vtt")).write_text(cue)
    (work / (vid + ".en-orig.vtt")).write_text(cue.replace("hello", "auto hello"))
else:
    (work / (vid + ".webm")).write_bytes(b"RAW:" + vid.encode() * 40)
"""


def yt(prefix, n):
    tail = str(n)
    return (prefix + "0" * 11)[:11 - len(tail)] + tail


class TestCaptionsAndRunner(LaneCase):
    def setUp(self):
        super().setUp()
        self.log = self.tmp / "yt.log"
        self.log.write_text("")
        self.ytdlp = make_tool(self.tmp / "bin", "yt-dlp", FAKE_YTDLP_SUBS)

    def queue(self, ids):
        import select_jobs
        common.write_csv(self.root / "jobs" / "queue.csv",
                         [{"video_id": v, "url": f"https://www.youtube.com/watch?v={v}", "channel_dir": "chanY",
                           "sources": "test", "shard": 0} for v in ids], select_jobs.FIELDS)

    def captions(self, *extra):
        return subprocess.run([sys.executable, "-I", str(PIPE / "fetch_captions.py"), "--root", str(self.root),
                               "--ytdlp", self.ytdlp, "--min-interval", "0", *map(str, extra)], capture_output=True,
                              text=True, timeout=120, env={**os.environ, "FAKE_LOG": str(self.log)})

    def test_captions_are_saved_as_tracks_and_plain_text(self):
        ids = [yt("GOOD", 1), yt("NOCA", 2)]
        self.queue(ids)
        done = self.captions("--all", "--workers", "1")
        self.assertEqual(done.returncode, 0, done.stderr)
        recs = {r["video_id"]: r for r in common.read_jsonl(self.root / "captions" / "captions_manifest.jsonl")}
        self.assertEqual(recs[ids[0]]["status"], "ok")
        self.assertEqual(recs[ids[0]]["preferred"], "en")                         # the uploader's track wins
        self.assertEqual(sorted(recs[ids[0]]["tracks"]), ["en", "en-orig"])
        self.assertEqual((self.root / "captions" / "chanY" / f"{ids[0]}.txt").read_text(),
                         f"hello from {ids[0]}\nsecond line\n")
        self.assertEqual(recs[ids[1]]["error_class"], "no_captions")
        calls = len(self.log.read_text().splitlines())
        self.captions("--all")                                                    # nothing is asked for twice
        self.assertEqual(len(self.log.read_text().splitlines()), calls)

    def test_captions_stop_after_three_bot_checks_and_use_no_evasion(self):
        self.queue([yt("BOTC", i) for i in range(6)])
        done = self.captions("--all", "--workers", "1")
        self.assertEqual(done.returncode, 3)
        self.assertIn("STOPPED", done.stderr)
        lines = self.log.read_text().splitlines()
        self.assertEqual(len(lines), 3)
        for line in lines:
            for word in ("cookies", "proxy", "player_client", "extractor-args", "username", "impersonate", "po_token"):
                self.assertNotIn(word, line)
            self.assertIn("--skip-download", line)

    def test_a_refusal_after_the_first_track_is_a_refusal_not_a_success(self):
        ids = [yt("PART", i) for i in range(8)]
        self.queue(ids)
        done = self.captions("--all", "--workers", "1")
        self.assertEqual(done.returncode, 3, done.stderr)             # it used to run through all 8 and exit 0
        recs = common.read_jsonl(self.root / "captions" / "captions_manifest.jsonl")
        self.assertEqual(len(recs), 3)
        self.assertEqual({(r["status"], r["error_class"]) for r in recs}, {("error", "rate_limited")})
        self.assertTrue((self.root / "captions" / "chanY" / f"{ids[0]}.en-orig.vtt").exists())   # what arrived is kept
        calls = len(self.log.read_text().splitlines())
        self.captions("--all", "--workers", "1")                       # and the videos are asked for again later
        self.assertGreater(len(self.log.read_text().splitlines()), calls)

    def test_an_ip_block_message_stops_the_captions_run(self):
        self.queue([yt("IPBL", i) for i in range(8)])
        done = self.captions("--all", "--workers", "1")
        self.assertEqual(done.returncode, 3, done.stderr)
        self.assertEqual(len(self.log.read_text().splitlines()), 3)
        self.assertEqual(common.classify_error("Your IP is likely being blocked by Youtube"), "bot_check")

    def test_captions_ask_for_named_english_tracks_not_machine_translations(self):
        self.queue([yt("GOOD", 1)])
        self.captions("--all")
        line = self.log.read_text().splitlines()[0]
        langs = line.split("--sub-langs ")[1].split(" ")[0]
        self.assertNotIn("*", langs)                                   # 'en.*' asks for a translation per language
        self.assertIn("en-orig", langs.split(","))

    def test_captions_dry_run(self):
        self.queue([yt("GOOD", 1)])
        self.assertIn("dry run", self.captions().stderr)
        self.assertEqual(self.log.read_text(), "")

    def runner(self, *extra, env=None):
        gh = make_tool(self.tmp / "bin", "gh", FAKE_GH)
        (self.tmp / "ghstore").mkdir(exist_ok=True)
        full = {**os.environ, "FAKE_LOG": str(self.log), "FAKE_GH_DIR": str(self.tmp / "ghstore"),
                "FAKE_GH_LOG": str(self.tmp / "gh.log"), "PATH": f"{self.tmp / 'bin'}{os.pathsep}{os.environ['PATH']}",
                **(env or {})}
        return subprocess.run([sys.executable, "-I", str(PIPE / "run_all.py"), "--root", str(self.root), "--gh", gh,
                               *map(str, extra)], capture_output=True, text=True, timeout=240, env=full)

    def test_runner_prints_the_plan_and_does_nothing_without_go(self):
        done = self.runner("--store", f"dir:{self.tmp / 'disk'}", "--lanes", "youtube,captions", "--set", "bashar75")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("PLAN", done.stdout)
        self.assertIn("download_audio.py", done.stdout)
        self.assertIn("sync_archive.py push", done.stdout)
        self.assertIn("dry run", done.stdout)
        self.assertFalse(self.root.exists())
        self.assertEqual(self.log.read_text(), "")

    def test_runner_checks_the_store_before_downloading_anything(self):
        done = self.runner("--store", "gh:someone/archive@audio-v1", "--lanes", "youtube", "--set", "bashar75", "--go",
                           env={"FAKE_GH_VISIBILITY": "public"})
        self.assertEqual(done.returncode, 5)
        self.assertIn("refusing to upload", done.stderr)
        self.assertEqual(self.log.read_text(), "")                                # yt-dlp was never started

    def test_runner_downloads_uploads_checks_and_deletes(self):
        store = self.tmp / "disk"
        done = self.runner("--store", f"dir:{store}", "--lanes", "youtube,captions", "--set", "bashar75",
                           "--per-channel", "1", "--workers", "2", "--min-interval", "0", "--watch", "1", "--go")
        self.assertEqual(done.returncode, 0, done.stdout[-1500:] + done.stderr[-1500:])
        manifest = common.read_jsonl(self.root / "audio" / "audio_manifest.jsonl")
        ok = [r for r in manifest if r["status"] == "ok"]
        self.assertGreater(len(ok), 5)
        stored = list((store / "audio").rglob("*.opus"))
        self.assertEqual(len(stored), len(ok))                                     # every finished file reached the store
        self.assertEqual(list((self.root / "audio").rglob("*.opus")), [])          # and the local copies are gone
        self.assertTrue((self.root / "catalog" / "catalog.csv").exists())
        self.assertTrue((self.root / "captions" / "captions_manifest.jsonl").exists())
        self.assertIn("done", done.stdout.splitlines()[-1])


class TestMigrateIds(LaneCase):
    def setUp(self):
        super().setUp()
        self.old, self.new = common.item_id("pod", "https://f/feed", "g1"), common.item_id("pod", "athina-krol", "g1")
        common.atomic_write_text(self.root / "feeds" / "athina-krol--11111111.jsonl", json.dumps(
            {"video_id": self.new, "legacy_id": self.old, "guid": "g1", "title": "T", "enclosure_url": "https://c/1.mp3",
             "feed_key": "athina-krol--11111111", "person_id": "athina-krol", "relation": "own"}) + "\n")
        folder = self.root / "audio" / "athina-krol"
        folder.mkdir(parents=True)
        (folder / f"{self.old}.opus").write_bytes(b"FAKEOPUS" + b"x" * 500)
        common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                            {"video_id": self.old, "channel_dir": "athina-krol", "lane": "pod", "status": "ok",
                             "path": f"athina-krol/{self.old}.opus", "bytes": 508, "duration_s": 600.0})
        t = self.root / "transcripts" / "athina-krol"
        t.mkdir(parents=True)
        (t / f"{self.old}.txt").write_text("words\n")
        (t / f"{self.old}.json").write_text(json.dumps({"video_id": self.old, "segments": []}))
        common.append_jsonl(self.root / "transcripts" / "transcripts_manifest.jsonl",
                            {"video_id": self.old, "channel_dir": "athina-krol", "status": "ok", "n_words": 1, "model": "base.en"})

    def migrate(self, *extra):
        return self.cli("migrate_ids.py", "--root", self.root, *extra)

    def test_report_only_changes_nothing(self):
        done = self.migrate()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("would rename", done.stdout)
        self.assertTrue((self.root / "audio" / "athina-krol" / f"{self.old}.opus").exists())
        self.assertEqual(len(common.read_jsonl(self.root / "audio" / "audio_manifest.jsonl")), 1)

    def test_files_and_records_move_to_the_new_id_and_the_old_one_is_retired(self):
        self.assertEqual(self.migrate("--go").returncode, 0)
        folder = self.root / "audio" / "athina-krol"
        self.assertFalse((folder / f"{self.old}.opus").exists())
        self.assertEqual((folder / f"{self.new}.opus").stat().st_size, 508)
        latest = common.latest_by_key(common.read_jsonl(self.root / "audio" / "audio_manifest.jsonl"))
        self.assertEqual(latest[self.new]["status"], "ok")
        self.assertEqual(latest[self.new]["path"], f"athina-krol/{self.new}.opus")
        self.assertEqual(latest[self.new]["migrated_from"], self.old)
        self.assertEqual(latest[self.old]["status"], "superseded")
        doc = json.loads((self.root / "transcripts" / "athina-krol" / f"{self.new}.json").read_text())
        self.assertEqual(doc["video_id"], self.new)
        self.assertEqual(self.migrate("--go").returncode, 0)                 # a second run is a no-op
        self.assertEqual(len(common.read_jsonl(self.root / "audio" / "audio_manifest.jsonl")), 3)

    def test_the_catalogue_counts_a_migrated_item_once(self):
        self.migrate("--go")
        self.assertEqual(self.cli("catalog.py", "--root", self.root).returncode, 0)
        rows = [r for r in common.read_csv(self.root / "catalog" / "catalog.csv") if r["person_id"] == "athina-krol"]
        self.assertEqual([r["item_id"] for r in rows], [self.new])
        self.assertEqual((rows[0]["audio_status"], rows[0]["asr_status"]), ("ok", "ok"))

    def test_the_sync_and_the_transcriber_follow_the_new_id(self):
        self.migrate("--go")
        store = self.tmp / "disk"
        done = subprocess.run([sys.executable, "-I", str(PIPE / "sync_archive.py"), "push", "--root", str(self.root),
                               "--store", f"dir:{store}"], capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue((store / "audio" / "athina-krol" / f"{self.new}.opus").exists())
        self.assertFalse((store / "audio" / "athina-krol" / f"{self.old}.opus").exists())


class TestCatalogFromLists(LaneCase):
    """The review's case: the queue is a work order, not the list of what exists."""

    def ra_recording(self, n):
        rows = [r for r in common.read_csv(ET / "sources" / "creator_files.csv") if r["person_id"] == "l-l-research"]
        row = rows[n]
        return common.item_id("web", row["media_url"]), common.item_id("web", row["official_page"])

    def coverage(self, person):
        self.assertEqual(self.cli("catalog.py", "--root", self.root).returncode, 0)
        return next(r for r in common.read_csv(self.root / "public_export" / "coverage.csv") if r["person_id"] == person)

    def test_counts_do_not_change_when_the_queue_is_rebuilt_for_someone_else(self):
        for n in range(3):
            audio, page = self.ra_recording(n)
            common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                                {"video_id": audio, "channel_dir": "l-l-research", "lane": "web", "status": "ok",
                                 "path": f"l-l-research/{audio}.opus", "bytes": 10, "duration_s": 3000.0})
            common.append_jsonl(self.root / "transcripts_publisher" / "publisher_text_manifest.jsonl",
                                {"video_id": page, "channel_dir": "l-l-research", "status": "ok", "kind": "page", "n_words": 2000})
        before = self.coverage("l-l-research")
        self.assertEqual((before["audio_ok"], before["publisher_texts"], before["audio_awaiting_transcript"]), ("3", "3", "0"))
        listed = before["items_listed"]
        # the owner now builds a queue for another person only
        self.write_queue([{"video_id": common.item_id("web", "https://kryon.com/x.mp3"), "url": "https://kryon.com/x.mp3",
                           "channel_dir": "lee-carroll", "lane": "web", "relation": "file"}])
        after = self.coverage("l-l-research")
        self.assertEqual(after["items_listed"], listed)                       # it used to shrink to what was queued
        self.assertEqual((after["audio_ok"], after["publisher_texts"], after["audio_awaiting_transcript"]), ("3", "3", "0"))
        self.assertIn("download the remaining", after["next_step"])           # 101 recordings are still to fetch

    def test_complete_is_only_said_when_nothing_listed_is_left(self):
        audio, page = self.ra_recording(0)
        common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                            {"video_id": audio, "channel_dir": "l-l-research", "lane": "web", "status": "ok",
                             "path": f"l-l-research/{audio}.opus", "bytes": 10, "duration_s": 3000.0})
        row = self.coverage("l-l-research")
        self.assertNotIn("complete", row["next_step"])
        self.assertEqual(row["audio_ok"], "1")
        self.assertGreater(int(row["items_listed"]), 100)                     # the lists, not the queue

    def test_a_listed_page_that_is_not_fetched_yet_is_counted_as_listed(self):
        row = self.coverage("daniel-scranton")
        self.assertGreater(int(row["items_listed"]), 4000)
        self.assertEqual(row["publisher_texts"], "0")
        self.assertIn("publisher pages", row["next_step"])


class TestCatalogTextKinds(LaneCase):
    def page(self, n, ids, words=300):
        ident = common.item_id("web", f"https://site.example/post-{n}/")
        common.append_jsonl(self.root / "transcripts_publisher" / "publisher_text_manifest.jsonl",
                            {"video_id": ident, "channel_dir": "daniel-scranton", "status": "ok", "kind": "page",
                             "n_words": words, "youtube_ids": ids, "source_host": "site.example",
                             "source_url": f"https://site.example/post-{n}/", "published": "2015-01-01"})
        return ident

    def test_a_video_embedded_on_every_page_is_not_a_twin(self):
        for n in range(12):
            self.page(n, [f"OWN{n:08d}", "SITEWIDE000"])
        lonely = self.page(99, ["SITEWIDE000"])
        self.assertEqual(self.cli("catalog.py", "--root", self.root).returncode, 0)
        rows = {r["item_id"]: r for r in common.read_csv(self.root / "catalog" / "catalog.csv")}
        mine = {k: r for k, r in rows.items() if r["source_host"] == "site.example"}
        twins = {r["twin_of"] for r in mine.values()}
        self.assertNotIn("SITEWIDE000", twins)
        self.assertEqual(len(twins - {""}), 12)
        self.assertEqual(rows[lonely]["twin_of"], "")
        self.assertEqual({r["twin_method"] for r in mine.values() if r["twin_of"]}, {"page-embed"})

    def test_source_text_and_text_made_here_are_counted_apart(self):
        self.page(1, [], words=500)                                                   # publisher text, no audio
        made = common.item_id("pod", "f", "1")
        both = common.item_id("pod", "f", "2")
        for ident in (made, both):
            common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                                {"video_id": ident, "channel_dir": "daniel-scranton", "lane": "pod", "status": "ok",
                                 "path": f"daniel-scranton/{ident}.opus", "bytes": 10, "duration_s": 1800.0})
        waiting = common.item_id("pod", "f", "3")
        common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                            {"video_id": waiting, "channel_dir": "daniel-scranton", "lane": "pod", "status": "ok",
                             "path": f"daniel-scranton/{waiting}.opus", "bytes": 10, "duration_s": 600.0})
        for ident in (made, both):
            common.append_jsonl(self.root / "transcripts" / "transcripts_manifest.jsonl",
                                {"video_id": ident, "channel_dir": "daniel-scranton", "status": "ok", "model": "base.en",
                                 "n_words": 4000})
        common.append_jsonl(self.root / "transcripts_publisher" / "publisher_text_manifest.jsonl",
                            {"video_id": both, "channel_dir": "daniel-scranton", "status": "ok", "kind": "vtt", "n_words": 3900})
        self.assertEqual(self.cli("catalog.py", "--root", self.root).returncode, 0)
        row = next(r for r in common.read_csv(self.root / "public_export" / "coverage.csv") if r["person_id"] == "daniel-scranton")
        self.assertEqual(row["publisher_texts"], "2")             # the page and the feed transcript
        self.assertEqual(row["asr_transcripts"], "2")
        self.assertEqual(row["items_text_from_source"], "2")
        self.assertEqual(row["items_text_made_here"], "2")
        self.assertEqual(row["items_with_text"], "3")             # one item has both kinds and counts once
        self.assertEqual(row["audio_awaiting_transcript"], "1")
        self.assertEqual(row["asr_hours"], "1.0")
        summary = json.loads((self.root / "public_export" / "coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["people_with_text_from_source"], 1)
        self.assertEqual(summary["people_with_text_made_here"], 1)


# --------------------------------------------------------------------------- official sites from channel pages
def channel_page(channel_id, name, same_as, subscribers=35100):
    data = {"@context": "https://schema.org", "@type": "ProfilePage", "url": f"https://www.youtube.com/channel/{channel_id}",
            "mainEntity": {"@type": "Person", "name": name, "alternateName": "@handle",
                           "url": f"https://www.youtube.com/channel/{channel_id}", "sameAs": same_as,
                           "interactionStatistic": [{"@type": "InteractionCounter", "interactionType": "https://schema.org/SubscribeAction",
                                                     "userInteractionCount": subscribers}]}}
    return f'<html><head><script type="application/ld+json" nonce="x">{json.dumps(data)}</script></head><body>videos</body></html>'


class TestDiscoverSites(LaneCase):
    def setUp(self):
        super().setUp()
        import discover_sites
        self.mod = discover_sites
        self.pages, self.asked = {}, []
        self.index = self.tmp / "index.json"
        self.sites = self.tmp / "official_sites.csv"

    def run_tool(self, people, *extra):
        self.index.write_text(json.dumps({"channels": [
            {"person": p, "channel": {"url": f"https://www.youtube.com/@{p}"}} for p in people]}))
        mod, case = self.mod, self

        def fake_get(url, timeout=60, max_bytes=0):
            case.asked.append(url)
            final, body = case.pages.get(url, (url, ""))
            if body is None:
                raise feeds.FetchError(429, "HTTP Error 429: Too Many Requests", url)
            return final, "text/html", body.encode("utf-8")
        saved = (mod.get_bytes, mod.Robots.allowed, sys.argv)
        mod.get_bytes = fake_get
        mod.Robots.allowed = lambda self_, url: True
        sys.argv = ["discover_sites.py", "--root", str(self.root), "--index", str(self.index), "--extra-channels",
                    str(self.tmp / "none.csv"), "--official-sites", str(self.sites), "--min-interval", "0", *extra]
        import io
        import contextlib
        out, err, code = io.StringIO(), io.StringIO(), 0
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    mod.main()
                except SystemExit as stop:
                    code = stop.code or 0
        finally:
            mod.get_bytes, mod.Robots.allowed, sys.argv = saved
        return code, out.getvalue(), err.getvalue()

    def test_declared_links_are_read_and_only_the_makers_own_site_is_kept(self):
        page = channel_page("UC0ycS7cUA44tvG9T8VErW_w", "The Angels of Atlantis",
                            ["https://www.facebook.com/TheAngels", "https://www.instagram.com/angels/", "www.theangelsofatlantis.com"])
        facts = self.mod.read_channel_page(page)
        self.assertEqual(facts["channel_id"], "UC0ycS7cUA44tvG9T8VErW_w")
        self.assertEqual(facts["subscribers"], 35100)
        self.assertEqual(self.mod.website_domains(facts["same_as"]), ["theangelsofatlantis.com"])
        self.assertEqual(self.mod.website_domains(["https://linktr.ee/x", "https://m.facebook.com/y", "https://open.spotify.com/show/z",
                                                   "https://maker.example/about", "maker.example"]), ["maker.example"])
        self.assertEqual(self.mod.read_channel_page("<html><body>Before you continue</body></html>"), {})
        self.assertEqual(self.mod.read_channel_page('<script type="application/ld+json">{not json</script>'), {})

    def test_dry_run_asks_for_nothing(self):
        code, out, err = self.run_tool(["alice"])
        self.assertIn("dry run", err)
        self.assertEqual(self.asked, [])

    def test_sites_are_recorded_with_the_channel_as_evidence_and_never_twice(self):
        self.pages["https://www.youtube.com/@alice"] = ("https://www.youtube.com/@alice",
                                                        channel_page("UC" + "a" * 22, "Alice", ["https://alice.example", "https://x.com/alice"]))
        self.pages["https://www.youtube.com/@bob"] = ("https://www.youtube.com/@bob",
                                                      channel_page("UC" + "b" * 22, "Bob", ["https://www.instagram.com/bob"]))
        code, out, err = self.run_tool(["alice", "bob"], "--all", "--merge")
        self.assertEqual(code, 0, err)
        rows = common.read_csv(self.sites)
        self.assertEqual([(r["person_id"], r["domain"]) for r in rows], [("alice", "alice.example")])
        self.assertIn("UC" + "a" * 22, rows[0]["evidence"])
        records = common.latest_by_key(common.read_jsonl(self.root / "sources" / "channel_pages.jsonl"), "person_id")
        self.assertEqual(records["bob"]["websites"], [])                      # a profile on a platform is not a site
        self.asked.clear()
        code, out, err = self.run_tool(["alice", "bob"], "--all", "--merge")
        self.assertEqual(self.asked, [])                                      # already read: not asked again
        self.assertEqual(len(common.read_csv(self.sites)), 1)                 # and not listed twice

    def test_a_consent_page_is_a_refusal_and_three_stop_the_run(self):
        people = [f"p{i}" for i in range(6)]
        for p in people:
            self.pages[f"https://www.youtube.com/@{p}"] = ("https://consent.youtube.com/m?continue=x", "<html>Before you continue</html>")
        code, out, err = self.run_tool(people, "--all")
        self.assertEqual(code, 3)
        self.assertEqual(len(self.asked), 3)
        self.assertIn("STOPPED", err)
        records = common.read_jsonl(self.root / "sources" / "channel_pages.jsonl")
        self.assertEqual({r["error_class"] for r in records}, {"bot_check"})

    def test_a_rate_limit_stops_the_run_too(self):
        people = [f"q{i}" for i in range(5)]
        for p in people:
            self.pages[f"https://www.youtube.com/@{p}"] = (f"https://www.youtube.com/@{p}", None)
        code, out, err = self.run_tool(people, "--all")
        self.assertEqual(code, 3)
        self.assertEqual(len(self.asked), 3)

    def test_only_youtube_addresses_are_ever_read(self):
        self.index.write_text(json.dumps({"channels": [{"person": "x", "channel": {"url": "https://evil.example/@x"}},
                                                       {"person": "y", "channel": {"url": "https://www.youtube.com/@y/videos"}}]}))
        entries = self.mod.targets(self.index, self.tmp / "none.csv")
        self.assertEqual(entries, [{"person_id": "y", "channel_url": "https://www.youtube.com/@y"}])


# --------------------------------------------------------------------------- what an official site publishes
class TestReconSites(LaneCase):
    def setUp(self):
        super().setUp()
        import recon_sites
        self.mod = recon_sites
        self.pages, self.asked = {}, []
        self.sites = self.tmp / "official_sites.csv"
        self.registry = self.tmp / "registry.csv"

    def serve(self, url, body, status=200):
        self.pages[url] = (status, body if isinstance(body, bytes) else body.encode("utf-8"))

    def run_tool(self, rows, *extra):
        common.write_csv(self.sites, rows, ["person_id", "domain", "evidence"])
        mod, case = self.mod, self

        def fake_get(url, timeout=60, max_bytes=0):
            case.asked.append(url)
            status, body = case.pages.get(url, (404, b""))
            if status != 200:
                raise feeds.FetchError(status, f"HTTP Error {status}", url)
            return url, "text/html", body
        saved = (mod.get_bytes, sys.argv)
        import fetch_publisher_text as fpt
        saved_fpt = fpt.get_bytes
        mod.get_bytes = fpt.get_bytes = fake_get
        sys.argv = ["recon_sites.py", "--root", str(self.root), "--official-sites", str(self.sites), "--registry",
                    str(self.registry), "--workers", "1", *extra]
        import io
        import contextlib
        out, err, code = io.StringIO(), io.StringIO(), 0
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    mod.main()
                except SystemExit as stop:
                    code = stop.code or 0
        finally:
            mod.get_bytes, sys.argv = saved
            fpt.get_bytes = saved_fpt
        return code, out.getvalue(), err.getvalue()

    def a_site(self, domain="maker.example"):
        base = f"https://{domain}"
        self.serve(base + "/robots.txt", f"User-agent: *\nDisallow: /members/\nSitemap: {base}/sitemap_index.xml\n")
        self.serve(base + "/", f'''<html><head>
            <link rel="alternate" type="application/rss+xml" title="Posts" href="/feed/">
            <link rel="alternate" type="application/rss+xml" title="Comments" href="/comments/feed/">
            </head><body><a href="https://anchor.fm/s/abc123/podcast/rss">Podcast</a>
            <a href="https://podcasts.apple.com/us/podcast/the-show/id1234567890">Apple</a></body></html>''')
        self.serve(base + "/feed/", feed_xml(["<item><title>Post one</title><guid>p1</guid></item>",
                                              "<item><title>Post two</title><guid>p2</guid></item>"], title="Maker blog"))
        self.serve("https://anchor.fm/s/abc123/podcast/rss",
                   feed_xml([item("g1", "Episode one", "https://cdn.example/1.mp3")], title="The Show", author="Maker"))
        self.serve("https://anchor.fm/robots.txt", "User-agent: *\nAllow: /\n")
        self.serve("https://itunes.apple.com/robots.txt", "")
        self.serve("https://itunes.apple.com/lookup?id=1234567890&entity=podcast",
                   json.dumps({"results": [{"feedUrl": "https://anchor.fm/s/abc123/podcast/rss", "collectionName": "The Show",
                                            "artistName": "Maker", "trackCount": 1}]}))
        self.serve(base + "/sitemap_index.xml", f"<sitemapindex><sitemap><loc>{base}/post-sitemap.xml</loc></sitemap></sitemapindex>")
        self.serve(base + "/post-sitemap.xml", "<urlset>" + "".join(
            f"<url><loc>{base}/2026/01/message-{i}/</loc></url>" for i in range(30)) + f"<url><loc>{base}/about/</loc></url></urlset>")
        return base

    def test_page_links_are_read(self):
        declared, hosted, apple = self.mod.links_on(
            '<link rel="alternate" type="application/rss+xml" href="/feed/">'
            '<a href="https://feed.podbean.com/show/feed.xml">x</a> https://podcasts.apple.com/gb/podcast/a-show/id987654321',
            "https://maker.example/")
        self.assertEqual(declared, ["https://maker.example/feed/"])
        self.assertEqual(hosted, ["https://feed.podbean.com/show/feed.xml"])
        self.assertEqual(apple, ["987654321"])
        pages, children = self.mod.sitemap_locs(b"<urlset><url><loc> https://a/1 </loc></url></urlset>")
        self.assertEqual((pages, children), (["https://a/1"], []))
        pages, children = self.mod.sitemap_locs(b"<sitemapindex><sitemap><loc>https://a/s1.xml</loc></sitemap></sitemapindex>")
        self.assertEqual((pages, children), ([], ["https://a/s1.xml"]))

    def test_dry_run_asks_for_nothing(self):
        code, out, err = self.run_tool([{"person_id": "maker", "domain": "maker.example"}])
        self.assertIn("dry run", err)
        self.assertEqual(self.asked, [])

    def test_a_site_is_described_by_what_it_publishes(self):
        self.a_site()
        code, out, err = self.run_tool([{"person_id": "maker", "domain": "maker.example"}], "--all")
        self.assertEqual(code, 0, err)
        row = common.read_csv(self.root / "sources" / "site_recon.csv")[0]
        self.assertEqual((row["status"], row["podcast_feeds"], row["post_feeds"], row["post_feed_items"]), ("ok", "1", "1", "2"))
        self.assertEqual((row["sitemap_urls"], row["sitemap_post_like"]), ("31", "30"))
        self.assertNotIn("https://maker.example/comments/feed/", self.asked)          # a comments feed is not a source
        rec = common.read_jsonl(self.root / "sources" / "site_recon.jsonl")[0]
        self.assertNotIn("Post one", json.dumps(rec))                                 # addresses and counts, no content

    def linked_shows(self, domain, shows):
        """An official site whose home page links the given (feed address, title, author) shows."""
        base = f"https://{domain}"
        self.serve(base + "/robots.txt", "User-agent: *\nAllow: /\n")
        self.serve(base + "/", "<html><body>" + "".join(f'<a href="{url}">listen</a>' for url, _, _ in shows) + "</body></html>")
        for url, title, author in shows:
            self.serve(url, feed_xml([item("g1", "Episode one", "https://cdn.example/1.mp3")], title=title, author=author))
            self.serve("https://" + url.split("/")[2] + "/robots.txt", "")

    def test_the_makers_own_show_linked_from_their_site_is_recorded_once(self):
        self.linked_shows("athinakrol.example", [("https://anchor.fm/s/abc123/podcast/rss", "Spirit Channel with Athina Król", "Athina Krol")])
        rows = [{"person_id": "athina-krol", "domain": "athinakrol.example"}]
        code, out, err = self.run_tool(rows, "--all", "--merge")
        self.assertEqual(code, 0, err)
        registry = common.read_csv(self.registry)
        self.assertEqual(len(registry), 1)
        self.assertEqual((registry[0]["verification"], registry[0]["relation"]), ("verified", "own"))
        self.assertIn("linked from the official site athinakrol.example", registry[0]["evidence"])
        self.run_tool(rows, "--all", "--merge", "--refresh")
        self.assertEqual(len(common.read_csv(self.registry)), 1)

    def test_a_show_the_person_was_a_guest_on_is_not_taken_as_their_own(self):
        # the real case: a maker's site links an interviewer's show with hundreds of episodes
        self.linked_shows("athinakrol.example", [("https://www.spreaker.com/show/4221459/episodes/feed",
                                                  "Inner Journey with Greg Friedman", "Greg Friedman")])
        code, out, err = self.run_tool([{"person_id": "athina-krol", "domain": "athinakrol.example"}], "--all", "--merge")
        self.assertEqual(code, 0, err)
        self.assertEqual(common.read_csv(self.registry), [])
        self.assertIn("1 linked show(s) left out", out)
        row = common.read_csv(self.root / "sources" / "site_recon.csv")[0]
        self.assertEqual(row["podcast_feeds"], "1")                                   # still listed for a person to look at

    def test_a_feed_served_from_the_official_domain_is_the_makers_own_whatever_it_is_called(self):
        base = "https://athinakrol.example"
        self.serve(base + "/robots.txt", "")
        self.serve(base + "/", f'<html><head><link rel="alternate" type="application/rss+xml" href="{base}/feed/podcast/"></head></html>')
        self.serve(base + "/feed/podcast/", feed_xml([item("g1", "Episode", "https://cdn.example/1.mp3")], title="Sessions", author="Studio"))
        self.run_tool([{"person_id": "athina-krol", "domain": "athinakrol.example"}], "--all", "--merge")
        registry = common.read_csv(self.registry)
        self.assertEqual([r["feed_url"] for r in registry], [base + "/feed/podcast/"])

    def test_a_blog_feed_on_the_official_site_is_a_feed_of_posts_not_a_podcast(self):
        base = "https://elenadanaan.example"
        self.serve(base + "/robots.txt", "")
        self.serve(base + "/", f'<html><head><link rel="alternate" type="application/rss+xml" href="{base}/blog-feed.xml"></head></html>')
        posts = "".join(f'<item><title>Post {i}</title><guid>p{i}</guid><enclosure url="https://static.example/{i}.jpg" type="image/jpeg"/></item>'
                        for i in range(7))
        self.serve(base + "/blog-feed.xml", feed_xml([posts], title="Elena Danaan", author="Elena Danaan"))
        self.run_tool([{"person_id": "elena-danaan", "domain": "elenadanaan.example"}], "--all", "--merge")
        self.assertEqual(common.read_csv(self.registry), [])
        row = common.read_csv(self.root / "sources" / "site_recon.csv")[0]
        self.assertEqual((row["podcast_feeds"], row["post_feeds"], row["post_feed_items"]), ("0", "1", "7"))

    def test_robots_rules_and_refusals_are_respected(self):
        base = "https://closed.example"
        self.serve(base + "/robots.txt", "User-agent: *\nDisallow: /\n")
        self.serve(base + "/", "<html>should never be read</html>")
        code, out, err = self.run_tool([{"person_id": "closed", "domain": "closed.example"}], "--all")
        self.assertEqual(code, 0, err)
        self.assertNotIn(base + "/", self.asked)
        row = common.read_csv(self.root / "sources" / "site_recon.csv")[0]
        self.assertEqual(row["status"], "error")
        self.assertIn("robots.txt does not allow", row["note"])

    def test_a_site_that_is_down_is_noted_and_the_rest_go_on(self):
        self.a_site("up.example")
        code, out, err = self.run_tool([{"person_id": "down", "domain": "down.example"}, {"person_id": "up", "domain": "up.example"}], "--all")
        self.assertEqual(code, 0, err)
        rows = {r["person_id"]: r for r in common.read_csv(self.root / "sources" / "site_recon.csv")}
        self.assertEqual((rows["down"]["status"], rows["up"]["status"]), ("error", "ok"))


if __name__ == "__main__":
    unittest.main()
