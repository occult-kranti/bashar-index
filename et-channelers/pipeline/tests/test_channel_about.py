#!/usr/bin/env python3
"""Tests for channel_about.py: parsing an About page's ytInitialData (description, links, redirect unwrapping
including nested and scheme-less targets, addresses), resume, the merge into the contacts table (new columns,
every old cell kept, the dated copy, the abort), the gate, the pacing, the robots.txt branches, redirects away
from youtube.com, and the three-refusals stop. Invented markup, invented people, no network: the fetch is
replaced in the module.

    python3 -I et-channelers/pipeline/tests/test_channel_about.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
PIPE = HERE.parent
sys.path.insert(0, str(PIPE))

import channel_about as ca  # noqa: E402
import common  # noqa: E402
from feeds import FetchError  # noqa: E402


def wrap(target):
    return ("https://www.youtube.com/redirect?event=channel_description&redir_token=QUFFLUhqbTAx&q="
            + urllib.parse.quote(target, safe=""))


REDIRECT = wrap("https://example-maker.test/sessions?ref=yt")
DESCRIPTION = ("Weekly transmissions from an invented source.\nBookings: Hello.Desk@example-maker.test or "
               "hello.desk@example-maker.test (same inbox); press: press@news.example.org.\nNot an address: me@localhost"
               "\nBanner: header@2x.png")
RECORD_KEYS = {"person_id", "channel_url", "fetched_at", "final_url", "status", "description", "links", "emails",
               "country", "subscribers_text", "videos_text", "error"}


def link(title, shown, url=None):
    model = {"title": {"content": title}, "link": {"content": shown}}
    if url:
        model["link"]["commandRuns"] = [{"startIndex": 0, "length": len(shown), "onTap": {"innertubeCommand": {
            "commandMetadata": {"webCommandMetadata": {"url": url, "webPageType": "WEB_PAGE_TYPE_UNKNOWN"}},
            "urlEndpoint": {"url": url, "target": "TARGET_NEW_WINDOW", "nofollow": True}}}}]
    return {"channelExternalLinkViewModel": model}


def about_block(description=DESCRIPTION, links=None, **extra):
    block = {"description": description, "descriptionLabel": {"content": "Description"}, "country": "Atlantis",
             "subscriberCountText": "12.3K subscribers", "viewCountText": "1,234 views", "videoCountText": "456 videos",
             "canonicalChannelUrl": "http://www.youtube.com/@invented", "channelId": "UCinventedinventedinvent",
             "links": links if links is not None else [
                 link("Sessions", "example-maker.test/sessions", REDIRECT),
                 link("Blog", "blog.example-maker.test"),
             ]}
    block.update(extra)
    return block


def page(block=None, with_data=True):
    """An invented YouTube About page: the about block sits deep in ytInitialData, as on the real page."""
    data = {"responseContext": {"serviceTrackingParams": []}, "onResponseReceivedEndpoints": [{"showEngagementPanelEndpoint": {
        "engagementPanel": {"engagementPanelSectionListRenderer": {"content": {"sectionListRenderer": {"contents": [
            {"itemSectionRenderer": {"contents": [{"aboutChannelRenderer": {"metadata": {
                "aboutChannelViewModel": block if block is not None else about_block()}}}]}}]}}}}}}]}
    script = f"var ytInitialData = {json.dumps(data)};</script>" if with_data else "var other = 1;</script>"
    return ("<!DOCTYPE html><html><head><title>t</title></head><body><script nonce=\"x\">" + script +
            "<script>var ytcfg = {};</script></body></html>").encode("utf-8")


class TestParsing(unittest.TestCase):
    def test_description_links_redirects_and_addresses(self):
        facts = ca.parse_about(page().decode("utf-8"))
        self.assertEqual(facts["description"], DESCRIPTION)
        self.assertEqual(facts["links"], [{"title": "Sessions", "url": "https://example-maker.test/sessions?ref=yt"},
                                          {"title": "Blog", "url": "https://blog.example-maker.test"}])
        self.assertEqual(facts["emails"], ["hello.desk@example-maker.test", "press@news.example.org"])
        self.assertEqual((facts["country"], facts["subscribers_text"], facts["videos_text"]),
                         ("Atlantis", "12.3K subscribers", "456 videos"))

    def test_unwrap_redirect(self):
        self.assertEqual(ca.unwrap_redirect(REDIRECT), "https://example-maker.test/sessions?ref=yt")
        self.assertEqual(ca.unwrap_redirect("https://example-maker.test/redirect?q=x"), "https://example-maker.test/redirect?q=x")
        self.assertEqual(ca.unwrap_redirect("https://other.test/page"), "https://other.test/page")
        self.assertEqual(ca.unwrap_redirect(wrap(wrap("https://deep.example.test/a?b=c"))), "https://deep.example.test/a?b=c")

    def test_links_are_normalised_to_http_addresses(self):
        self.assertEqual(ca.normalise_link(wrap("www.example-maker.test/book")), "https://www.example-maker.test/book")
        self.assertEqual(ca.normalise_link(wrap(wrap("example-maker.test"))), "https://example-maker.test")
        self.assertEqual(ca.normalise_link("//cdn.example.test/x"), "https://cdn.example.test/x")
        self.assertEqual(ca.normalise_link("HTTP://Example.test/"), "HTTP://Example.test/")
        for bad in ("javascript:alert(1)", "mailto:someone@example.test", wrap("javascript:void(0)"), wrap(""), "", "   "):
            self.assertEqual(ca.normalise_link(bad), "", bad)
        block = about_block(links=[link("Book", "www.example-maker.test/book", wrap("www.example-maker.test/book")),
                                   link("Nested", "deep.example.test", wrap(wrap("https://deep.example.test/a"))),
                                   link("Script", "x", "javascript:alert(1)"),
                                   link("Shown only", "shown.example.test/p")])
        facts = ca.parse_about(page(block).decode())
        self.assertEqual([l["url"] for l in facts["links"]],
                         ["https://www.example-maker.test/book", "https://deep.example.test/a", "https://shown.example.test/p"])

    def test_pages_without_an_about_block(self):
        self.assertEqual(ca.parse_about(page(with_data=False).decode("utf-8")), {})
        self.assertEqual(ca.parse_about("<html>consent</html>"), {})
        self.assertEqual(ca.parse_about("var ytInitialData = {\"a\": [1, 2]};"), {})

    def test_emails_regex_only(self):
        self.assertEqual(ca.emails_in("write to Someone@Example.test. or not"), ["someone@example.test"])
        self.assertEqual(ca.emails_in("no address here @ all"), [])
        self.assertEqual(ca.emails_in("see image@2x.png and logo@3x.JPG, mail hi@example.test"), ["hi@example.test"])
        self.assertEqual(ca.parse_about(page(about_block(description="plain text", links=[])).decode())["emails"], [])

    def test_about_url(self):
        self.assertEqual(ca.about_url("https://www.youtube.com/@invented/"), "https://www.youtube.com/@invented/about")
        self.assertEqual(ca.about_url("https://www.youtube.com/channel/UCx/videos"), "https://www.youtube.com/channel/UCx/about")

    def test_redirect_hook_stays_on_youtube(self):
        ca.stay_on_youtube("https://www.youtube.com/@invented/about")
        ca.stay_on_youtube("https://m.youtube.com/@invented/about")
        with self.assertRaises(FetchError) as caught:
            ca.stay_on_youtube("https://consent.youtube.com/m?continue=x")
        self.assertEqual(caught.exception.klass, "bot_check")
        with self.assertRaises(FetchError) as caught:
            ca.stay_on_youtube("https://www.google.com/sorry/index?continue=x")
        self.assertEqual(caught.exception.klass, "bot_check")
        with self.assertRaises(FetchError) as caught:
            ca.stay_on_youtube("https://elsewhere.test/page")
        self.assertEqual(caught.exception.klass, "offsite")

    def test_verify_kept(self):
        before = [{"person_id": "a", "name": "A", "contact_emails": "", "about_links": "old"}]
        ok = [{"person_id": "a", "name": "A", "contact_emails": "x@example.test", "about_links": "new", "about_country": "Atlantis"}]
        ca.verify_kept(before, ok, ["person_id", "name", "contact_emails", "about_links"])
        with self.assertRaises(ca.MergeAborted):
            ca.verify_kept(before, [{**ok[0], "name": "B"}], ["person_id", "name", "contact_emails", "about_links"])
        with self.assertRaises(ca.MergeAborted):
            ca.verify_kept(before, [], ["person_id", "name"])
        with self.assertRaises(ca.MergeAborted):
            ca.verify_kept(before, [{**ok[0], "person_id": "b"}], ["person_id", "name"])


class Redirect:
    """A FakeNet answer: the server redirects to `target`; the hook is asked first, as feeds does, and may stop it."""

    def __init__(self, target, then=None):
        self.target, self.then = target, then


class FakeNet:
    """Stands in for feeds.get_bytes inside channel_about: robots.txt answers as `robots` says (permissive by
    default), each About page answers as `answers` says (bytes, a (final_url, type, body) tuple, a Redirect, or a
    FetchError to raise), and every request is logged with the time it started."""

    def __init__(self, answers, robots=b"User-agent: *\nDisallow: /youtubei/\n"):
        self.answers, self.robots, self.requests, self.started = answers, robots, [], []

    def __call__(self, url, timeout=60, max_bytes=0, before_redirect=None):
        self.requests.append(url)
        self.started.append(time.monotonic())
        if url.endswith("/robots.txt"):
            if isinstance(self.robots, Exception):
                raise self.robots
            return url, "text/plain", self.robots
        answer = self.answers.get(url, self.answers.get("*"))
        if isinstance(answer, Exception):
            raise answer
        if isinstance(answer, Redirect):
            if before_redirect is not None:
                before_redirect(answer.target)
            self.requests.append(answer.target)
            return answer.target, "text/html", answer.then if answer.then is not None else page()
        if isinstance(answer, tuple):
            return answer
        return url, "text/html; charset=utf-8", answer

    def about_requests(self):
        return [u for u in self.requests if u.endswith("/about")]


class RunCase(unittest.TestCase):
    PEOPLE = ["alpha", "beta", "gamma", "delta", "epsilon"]

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="etabout-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "private"
        (self.root / "analysis" / "coverage").mkdir(parents=True)
        self.targets = self.tmp / "targets.csv"
        rows = [{"person_id": p, "person_name": p.title(), "youtube_channel_url": f"https://www.youtube.com/@{p}",
                 "state": "planned: YouTube only"} for p in self.PEOPLE]
        rows.append({"person_id": "nochannel", "person_name": "No Channel", "youtube_channel_url": "", "state": "planned: no source yet"})
        rows.append({"person_id": "left-out", "person_name": "Left Out", "youtube_channel_url": "https://www.youtube.com/@leftout",
                     "state": "excluded"})
        rows.append({"person_id": "left-out-2", "person_name": "Left Out Too", "youtube_channel_url": "https://www.youtube.com/@leftout2",
                     "state": "Excluded: not a channeler"})
        with open(self.targets, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["person_id", "person_name", "youtube_channel_url", "state"])
            writer.writeheader()
            writer.writerows(rows)
        self.out = self.root / ca.OUT_REL
        self.contacts = self.root / ca.CONTACTS_REL
        self.env = mock.patch.dict(os.environ, {common.YOUTUBE_OVERRIDE: "1", "ET_PRIVATE_DIR": str(self.root)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def run_tool(self, *args, net=None, interval="0"):
        net = net or FakeNet({"*": page()})
        code = 0
        with mock.patch.object(ca, "get_bytes", net):
            try:
                ca.main(["--root", str(self.root), "--targets", str(self.targets), "--min-interval", interval, *map(str, args)])
            except SystemExit as stop:
                code = stop.code or 0
        return code, net

    def records(self):
        return common.read_jsonl(self.out)

    def test_every_tracked_channel_is_read_once_and_recorded(self):
        code, net = self.run_tool()
        self.assertEqual(code, 0)
        self.assertEqual(net.requests[0], "https://www.youtube.com/robots.txt")
        self.assertEqual(net.about_requests(), [f"https://www.youtube.com/@{p}/about" for p in self.PEOPLE])
        self.assertNotIn("https://www.youtube.com/@leftout/about", net.requests)
        self.assertNotIn("https://www.youtube.com/@leftout2/about", net.requests)
        recs = self.records()
        self.assertEqual([r["person_id"] for r in recs], self.PEOPLE)
        self.assertTrue(all(r["status"] == "ok" for r in recs))
        self.assertEqual(set(recs[0]), RECORD_KEYS)
        self.assertEqual(recs[0]["final_url"], "https://www.youtube.com/@alpha/about")
        self.assertEqual(recs[0]["links"][0]["url"], "https://example-maker.test/sessions?ref=yt")
        self.assertEqual(recs[0]["emails"], ["hello.desk@example-maker.test", "press@news.example.org"])

    def test_limit_and_only(self):
        code, net = self.run_tool("--limit", "2")
        self.assertEqual(len(net.about_requests()), 2)
        code, net = self.run_tool("--only", "delta,epsilon")
        self.assertEqual(net.about_requests(), ["https://www.youtube.com/@delta/about", "https://www.youtube.com/@epsilon/about"])

    def test_resume_skips_a_fresh_read_and_repeats_an_old_failed_or_moved_one(self):
        now = dt.datetime.now(dt.timezone.utc)
        old = (now - dt.timedelta(days=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
        fresh = (now - dt.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        common.append_jsonl(self.out, {"person_id": "alpha", "status": "ok", "fetched_at": fresh, "channel_url": "https://www.youtube.com/@alpha"})
        common.append_jsonl(self.out, {"person_id": "beta", "status": "ok", "fetched_at": old, "channel_url": "https://www.youtube.com/@beta"})
        common.append_jsonl(self.out, {"person_id": "gamma", "status": "error", "fetched_at": fresh, "channel_url": "https://www.youtube.com/@gamma"})
        common.append_jsonl(self.out, {"person_id": "delta", "status": "ok", "fetched_at": fresh, "channel_url": "https://www.youtube.com/@delta-old"})
        code, net = self.run_tool()
        asked = [u.split("@")[1].split("/")[0] for u in net.about_requests()]
        self.assertEqual(asked, ["beta", "gamma", "delta", "epsilon"])
        code, net = self.run_tool()
        self.assertEqual(net.about_requests(), [])                         # everything is fresh now
        code, net = self.run_tool("--max-age-days", "0")
        self.assertEqual(len(net.about_requests()), 5)

    def test_fetched_at_is_the_time_of_the_answer_and_requests_are_paced(self):
        slow = FakeNet({"*": page()})
        code, net = self.run_tool("--limit", "3", net=slow, interval="0.3")
        self.assertEqual(code, 0)
        self.assertEqual(len(net.requests), 4)                              # robots.txt and three About pages
        gaps = [b - a for a, b in zip(net.started, net.started[1:])]
        self.assertTrue(all(g >= 0.29 for g in gaps), gaps)                 # robots.txt is paced like the rest
        for rec in self.records():
            self.assertRegex(rec["fetched_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_a_page_without_an_about_block_is_recorded_and_not_a_refusal(self):
        net = FakeNet({"*": page(), "https://www.youtube.com/@beta/about": page(with_data=False)})
        code, net = self.run_tool(net=net)
        self.assertEqual(code, 0)
        beta = common.latest_by_key(self.records(), "person_id")["beta"]
        self.assertEqual(beta["status"], "no_about")
        self.assertEqual(len(net.about_requests()), 5)

    def test_bot_check_words_inside_a_description_are_not_a_refusal(self):
        wordy = page(about_block(description="Please confirm you're not a bot before booking; unusual traffic from your computer network"))
        code, net = self.run_tool(net=FakeNet({"*": wordy}))
        self.assertEqual(code, 0)
        self.assertEqual([r["status"] for r in self.records()], ["ok"] * 5)

    def test_the_gate_sends_nothing_without_the_override(self):
        with mock.patch.dict(os.environ, {k: v for k, v in os.environ.items() if k != common.YOUTUBE_OVERRIDE}, clear=True):
            code, net = self.run_tool()
        self.assertEqual(code, common.SKIPPED_BY_RULE)
        self.assertEqual(net.requests, [])
        self.assertFalse(self.out.exists())
        with mock.patch.dict(os.environ, {common.YOUTUBE_OVERRIDE: "0"}):
            code, net = self.run_tool()
        self.assertEqual((code, net.requests), (common.SKIPPED_BY_RULE, []))

    def test_robots_txt_unreadable_or_disallowing_sends_nothing_more(self):
        code, net = self.run_tool(net=FakeNet({"*": page()}, robots=FetchError(403, "HTTP Error 403: Forbidden")))
        self.assertEqual(code, 0)
        self.assertEqual(net.requests, ["https://www.youtube.com/robots.txt"])
        self.assertEqual([(r["status"], r["error"]) for r in self.records()], [("error", "robots.txt could not be read this run")] * 5)
        self.out.unlink()
        code, net = self.run_tool(net=FakeNet({"*": page()}, robots=b"User-agent: *\nDisallow: /\n"))
        self.assertEqual(net.requests, ["https://www.youtube.com/robots.txt"])
        self.assertEqual([r["error"] for r in self.records()], ["robots.txt disallows the About page"] * 5)
        self.out.unlink()
        code, net = self.run_tool(net=FakeNet({"*": page()}, robots=b"User-agent: *\nDisallow: /@alpha/\n"))
        self.assertEqual(len(net.about_requests()), 4)
        self.assertEqual(common.latest_by_key(self.records(), "person_id")["alpha"]["status"], "error")

    def test_redirects_away_from_youtube_are_not_followed(self):
        net = FakeNet({"*": page(), "https://www.youtube.com/@beta/about": Redirect("https://elsewhere.test/page"),
                       "https://www.youtube.com/@gamma/about": Redirect("https://consent.youtube.com/m?continue=x")})
        code, net = self.run_tool(net=net)
        self.assertEqual(code, 0)
        self.assertNotIn("https://elsewhere.test/page", net.requests)
        self.assertNotIn("https://consent.youtube.com/m?continue=x", net.requests)
        latest = common.latest_by_key(self.records(), "person_id")
        self.assertEqual((latest["beta"]["status"], latest["gamma"]["status"]), ("error", "refused"))
        self.assertEqual(latest["gamma"]["final_url"], "https://consent.youtube.com/m?continue=x")
        # a redirect that stays on youtube.com is followed and recorded
        net = FakeNet({"*": Redirect("https://www.youtube.com/channel/UCx/about")})
        self.out.unlink()
        code, net = self.run_tool(net=net, *("--only", "alpha"))
        self.assertEqual(self.records()[0]["final_url"], "https://www.youtube.com/channel/UCx/about")
        self.assertEqual(self.records()[0]["status"], "ok")

    def test_three_refusals_in_a_row_stop_the_run(self):
        code, net = self.run_tool(net=FakeNet({"*": FetchError(403, "HTTP Error 403: Forbidden")}))
        self.assertEqual(code, 3)
        self.assertEqual(len(net.about_requests()), 3)
        recs = self.records()
        self.assertEqual([r["status"] for r in recs], ["refused"] * 3)
        # a bot-check page, a consent redirect and a 429 count as refusals too; a success in between resets the count
        bot = ("https://www.youtube.com/@alpha/about", "text/html", b"<html>Our systems have detected unusual traffic from your computer network</html>")
        consent = Redirect("https://consent.youtube.com/m?continue=x")
        net = FakeNet({"*": page(), "https://www.youtube.com/@alpha/about": bot, "https://www.youtube.com/@beta/about": consent,
                       "https://www.youtube.com/@delta/about": FetchError(429, "HTTP Error 429: Too Many Requests"),
                       "https://www.youtube.com/@epsilon/about": FetchError(429, "HTTP Error 429: Too Many Requests")})
        (self.out).unlink()
        code, net = self.run_tool(net=net)
        self.assertEqual(code, 0, "gamma answered in between: never three in a row")
        self.assertEqual([r["status"] for r in self.records()], ["refused", "refused", "ok", "refused", "refused"])
        self.assertEqual(len(net.about_requests()), 5)
        # three consent redirects in a row stop the run without the consent host being asked
        (self.out).unlink()
        code, net = self.run_tool(net=FakeNet({"*": consent}))
        self.assertEqual((code, len(net.about_requests())), (3, 3))
        self.assertNotIn("https://consent.youtube.com/m?continue=x", net.requests)

    def test_other_errors_do_not_trip_the_breaker(self):
        code, net = self.run_tool(net=FakeNet({"*": FetchError(0, "URLError: timed out")}))
        self.assertEqual(code, 0)
        self.assertEqual(len(net.about_requests()), 5)
        self.assertTrue(all(r["status"] == "error" for r in self.records()))

    def write_contacts(self):
        fields = ["person_id", "name", "role", "named_by", "state", "youtube_channel", "websites", "podcasts", "podcast_feeds",
                  "podcast_sites", "contact_emails", "email_source", "audio_pages", "text_pages", "archive_org",
                  "earlier_research", "interview_shows", "sources_registered", "as_of", "channel_last_upload",
                  "channel_activity", "podcast_last_episode", "podcast_activity"]
        rows = [dict.fromkeys(fields, "") for _ in range(4)]
        for row, pid in zip(rows, ["alpha", "beta", "nochannel", "zeta"]):
            row.update(person_id=pid, name=pid.title(), role="channeler", state="partly captured", as_of="2026-11-16",
                       sources_registered="2", websites="https://site.example.test/")
        rows[0].update(contact_emails="press@news.example.org", email_source="the podcast feed's own contact field")
        rows[1].update(contact_emails="old@feed.example.test", email_source="the podcast feed's own contact field")
        with open(self.contacts, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        return fields

    def copies(self):
        return sorted(self.contacts.parent.glob("contacts.before-about.*.csv"))

    def test_merge_adds_columns_keeps_every_existing_value_and_keeps_the_old_table(self):
        fields = self.write_contacts()
        before = common.read_csv(self.contacts)
        old_bytes = self.contacts.read_bytes()
        net = FakeNet({"*": page(), "https://www.youtube.com/@beta/about": page(about_block(description="no address", links=[]))})
        self.run_tool(net=net)
        code, net = self.run_tool("--merge")
        self.assertEqual(code, 0)
        self.assertEqual(net.requests, [], "--merge fetches nothing")
        after = common.read_csv(self.contacts)
        self.assertEqual(list(after[0].keys()), fields + ca.ABOUT_COLUMNS)
        for old, new in zip(before, after):
            for column in fields:
                if column not in ("contact_emails", "email_source"):
                    self.assertEqual(new[column], old[column], column)
        alpha, beta, nochannel, zeta = after
        self.assertEqual(alpha["about_links"], "https://example-maker.test/sessions?ref=yt https://blog.example-maker.test")
        self.assertEqual(alpha["about_emails"], "hello.desk@example-maker.test press@news.example.org")
        self.assertEqual((alpha["about_country"], alpha["about_fetched"][:4]), ("Atlantis", dt.date.today().strftime("%Y")))
        self.assertEqual(alpha["contact_emails"], "press@news.example.org hello.desk@example-maker.test")
        self.assertEqual(alpha["email_source"], "the podcast feed's own contact field; " + ca.ABOUT_SOURCE)
        self.assertEqual((beta["about_links"], beta["about_emails"], beta["about_country"]), ("", "", "Atlantis"))
        self.assertEqual((beta["contact_emails"], beta["email_source"]), ("old@feed.example.test", "the podcast feed's own contact field"))
        self.assertEqual([nochannel[c] for c in ca.ABOUT_COLUMNS], ["", "", "", ""])
        self.assertEqual([zeta[c] for c in ca.ABOUT_COLUMNS], ["", "", "", ""])
        # the old table is kept beside the new one, byte for byte
        self.assertEqual(len(self.copies()), 1)
        self.assertEqual(self.copies()[0].read_bytes(), old_bytes)
        # a second merge changes nothing: the source is named once, the address kept once, no new copy, no rewrite
        stamp = self.contacts.stat().st_mtime_ns
        self.run_tool("--merge")
        self.assertEqual(common.read_csv(self.contacts), after)
        self.assertEqual(len(self.copies()), 1)
        self.assertEqual(self.contacts.stat().st_mtime_ns, stamp)
        # a re-read with other links is merged over the About columns (they may change; the rest may not)
        self.out.unlink()
        self.run_tool(net=FakeNet({"*": page(about_block(links=[link("Shop", "shop.example-maker.test")]))}))
        code, _ = self.run_tool("--merge")
        self.assertEqual(code, 0)
        again = common.read_csv(self.contacts)
        self.assertEqual(again[0]["about_links"], "https://shop.example-maker.test")
        self.assertEqual([r["websites"] for r in again], [r["websites"] for r in after])
        self.assertEqual(len(self.copies()), 2)

    def test_merge_aborts_and_writes_nothing_when_a_kept_cell_would_change(self):
        self.write_contacts()
        old_bytes = self.contacts.read_bytes()
        self.run_tool()
        with mock.patch.object(ca, "verify_kept", side_effect=ca.MergeAborted("row 1 column name would change")):
            code, _ = self.run_tool("--merge")
        self.assertEqual(code, 4)
        self.assertEqual(self.contacts.read_bytes(), old_bytes)
        self.assertEqual(self.copies(), [])

    def test_merge_names_the_about_page_alone_when_it_is_the_only_source(self):
        self.write_contacts()
        self.run_tool("--only", "nochannel,zeta,gamma")                      # nothing read for alpha or beta
        self.run_tool(net=FakeNet({"*": page()}), *("--only", "beta"))
        self.run_tool("--merge")
        rows = common.latest_by_key(common.read_csv(self.contacts), "person_id")
        self.assertEqual(rows["beta"]["contact_emails"], "old@feed.example.test hello.desk@example-maker.test press@news.example.org")
        self.assertEqual(rows["alpha"]["about_fetched"], "")
        with open(self.contacts, newline="", encoding="utf-8") as handle:
            table = list(csv.DictReader(handle))
        table[0]["contact_emails"], table[0]["email_source"] = "", ""
        with open(self.contacts, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(table[0].keys()), lineterminator="\n")
            writer.writeheader()
            writer.writerows(table)
        self.run_tool(net=FakeNet({"*": page()}), *("--only", "alpha"))
        self.run_tool("--merge")
        alpha = common.latest_by_key(common.read_csv(self.contacts), "person_id")["alpha"]
        self.assertEqual(alpha["email_source"], ca.ABOUT_SOURCE)
        self.assertEqual(alpha["contact_emails"], "hello.desk@example-maker.test press@news.example.org")

    def test_a_private_root_inside_a_git_checkout_is_refused(self):
        inside = self.tmp / "repo"
        (inside / ".git").mkdir(parents=True)
        (inside / "analysis" / "coverage").mkdir(parents=True)
        with mock.patch.object(ca, "get_bytes", FakeNet({"*": page()})) as net:
            with self.assertRaises(SystemExit):
                ca.main(["--root", str(inside), "--targets", str(self.targets), "--min-interval", "0"])
        self.assertEqual(net.requests, [])


if __name__ == "__main__":
    unittest.main()
