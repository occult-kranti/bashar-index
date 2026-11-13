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
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Publisher)
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

    def test_durations_and_dates(self):
        self.assertEqual(feeds.parse_duration_text("43:34"), 2614)
        self.assertEqual(feeds.parse_duration_text("894.6"), 894)
        self.assertIsNone(feeds.parse_duration_text("soon"))
        self.assertIsNone(feeds.parse_duration_text(""))
        self.assertEqual(feeds.parse_date("Wed, 17 May 2023 00:00:00 +0000"), "2023-05-17")
        self.assertEqual(feeds.parse_date("2024-04-30T19:13:53Z"), "2024-04-30")
        self.assertEqual(feeds.parse_date("whenever"), "")

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

    def grade(self, author, title, target=None, strict=(), domains=None, site="", feed=""):
        return find_feeds.grade(target or self.T, {"artistName": author, "collectionName": title, "feedUrl": feed},
                                set(strict), domains or {}, site)[0]

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
        self.assertEqual(self.grade("Esther Hicks", "Esther Hicks Daily", target, strict={"esther-hicks"}), "candidate")
        self.assertEqual(self.grade("Esther Hicks", "Esther Hicks Daily", target, strict={"esther-hicks"},
                                    domains={"esther-hicks": {"abraham-hicks.com"}},
                                    site="www.abraham-hicks.com"), "verified")

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
    def write_feed(self, key, person, relation, episodes):
        lines = []
        for n, (title, seconds, yt) in enumerate(episodes):
            lines.append(json.dumps({"video_id": common.item_id("pod", key, str(n)), "guid": str(n), "title": title,
                                     "published": f"2026-01-{n + 1:02d}", "duration_s": seconds,
                                     "enclosure_url": f"https://cdn.example/{key}/{n}.mp3", "transcripts": [],
                                     "youtube_ids": yt, "feed_key": key, "person_id": person, "relation": relation}))
        common.atomic_write_text(self.root / "feeds" / f"{key}.jsonl", "\n".join(lines) + "\n")

    def select(self, *extra):
        done = self.cli("select_episodes.py", "--root", self.root, "--relation", "own,host", *extra)
        self.assertEqual(done.returncode, 0, done.stderr)
        return common.read_csv(self.root / "jobs" / "queue_enclosures.csv")

    def test_own_feed_keeps_everything_and_host_feed_keeps_only_tracked_people(self):
        self.write_feed("own1", "athina-krol", "own", [("Any title at all", 600, []), ("Another", 700, [])])
        self.write_feed("host1", "host:some-show", "host",
                        [("An evening with Bashar", 3600, []), ("Cooking with friends", 1800, []),
                         ("Darryl Anka on film", 2400, [])])
        rows = self.select()
        self.assertEqual(sum(r["channel_dir"] == "athina-krol" for r in rows), 2)
        self.assertEqual(sum(r["channel_dir"] == "darryl-anka" for r in rows), 2)
        self.assertEqual(len(rows), 4)
        meta = json.loads((self.root / "jobs" / "queue_enclosures.meta.json").read_text())
        self.assertEqual(meta["dropped"]["host_no_tracked_person"], 1)

    def test_a_show_note_link_to_an_indexed_video_makes_a_twin(self):
        index = json.loads((ET / "youtube-index" / "youtube_index.json").read_text(encoding="utf-8"))
        channel = next(c for c in index["channels"] if len(c.get("videos") or []) >= 2)
        vid = channel["videos"][0]["video_id"]
        self.write_feed("own2", channel["person"], "own", [("Unrelated wording", 600, [vid])])
        rows = self.select()
        self.assertEqual(rows[0]["twin_of"], vid)
        self.assertEqual(rows[0]["twin_method"], "link")

    def test_same_title_makes_a_twin_and_a_different_title_does_not(self):
        index = json.loads((ET / "youtube-index" / "youtube_index.json").read_text(encoding="utf-8"))
        channel = next(c for c in index["channels"]
                       if any(len(feeds.tokens(v.get("title") or "")) >= 4 for v in c.get("videos") or []))
        video = next(v for v in channel["videos"] if len(feeds.tokens(v.get("title") or "")) >= 4)
        self.write_feed("own3", channel["person"], "own", [(video["title"], None, []), ("Zebra quartz umbrella", None, [])])
        rows = {r["title"]: r for r in self.select()}
        self.assertEqual(rows[video["title"]]["twin_of"], video["video_id"])
        self.assertEqual(rows[video["title"]]["twin_method"], "title")
        self.assertEqual(rows["Zebra quartz umbrella"]["twin_of"], "")

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
        catalog = common.read_csv(self.root / "catalog" / "catalog.csv")
        self.assertEqual(catalog[0]["title"], "A private title")
        self.assertEqual(catalog[0]["has_text"], "1")
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
    folder.mkdir(parents=True, exist_ok=True)
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
work.mkdir(parents=True, exist_ok=True)
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
        twins = {r["twin_of"] for r in rows.values()}
        self.assertNotIn("SITEWIDE000", twins)
        self.assertEqual(len(twins - {""}), 12)
        self.assertEqual(rows[lonely]["twin_of"], "")
        self.assertEqual({r["twin_method"] for r in rows.values() if r["twin_of"]}, {"page-embed"})

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


if __name__ == "__main__":
    unittest.main()
