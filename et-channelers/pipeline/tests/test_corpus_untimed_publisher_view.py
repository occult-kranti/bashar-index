"""Synthetic publisher text and a real OOXML container; no remote source or speech inference."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile

from pipeline import corpus_untimed_publisher_view as reader, corpus_concordance, postrun_candidates, stage_archived_text
from pipeline.tests import test_publisher_episode_page as episode_fixture


REMOTE = "archive:Audio"
VIDEO = "GEhE9JPrK78"
UUID = "1fc8d52c-59c7-4837-926d-2ee83a64dd8c"


def hashes(raw):
    return {"bytes":len(raw), "md5":hashlib.md5(raw).hexdigest(), "sha256":hashlib.sha256(raw).hexdigest()}


class UntimedPublisherTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root/"sync").mkdir()

    def publish_fixture(self, office=True):
        creator = "julie-ryan" if office else "sounds-true"
        parent = f"{REMOTE}/{creator}/Videos/{VIDEO}/PublisherVariants/" + "a"*64
        source = episode_fixture.EpisodePageTests.record(SimpleNamespace(video=VIDEO, uuid=UUID, parent=parent))
        row = {"video_id":VIDEO, "channel_dir":creator, "tab":"videos"}
        if office:
            paragraphs = ["Julie \U0001f319 [00:03:17] " + " ".join(["the control group"]*200), "A second thought."]
            doc = ElementTree.Element(reader.WORD + "document")
            body = ElementTree.SubElement(doc, reader.WORD + "body")
            for value in (paragraphs[0], "", paragraphs[1]):
                p = ElementTree.SubElement(body, reader.WORD + "p")
                t = ElementTree.SubElement(ElementTree.SubElement(p, reader.WORD + "r"), reader.WORD + "t")
                t.text = value
            archive = io.BytesIO()
            with ZipFile(archive, "w", ZIP_DEFLATED) as z:
                z.writestr("word/document.xml", ElementTree.tostring(doc, encoding="utf-8"))
                z.writestr("word/header1.xml", "<header>do not use</header>")
            raw = archive.getvalue()
            text = ("\n\n".join(paragraphs) + "\n").encode()
            words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text.decode().lower())
            source["publisher_transcript"].update(**hashes(text), paragraphs=2, words=len(words),
                english_common_words=sum(w in reader.ENGLISH_WORDS for w in words), language_verification="english_document_lexical_check",
                completeness="complete_publisher_declared_document", audio_alignment_verified=False)
            source["publisher_transcript_document"].update(hashes(raw))
            evidence = source["publisher_transcript_provenance"]
            evidence.update(source_document_sha256=hashes(raw)["sha256"], observation={"accepted":True,"http_status":200,
                "eof_observed":True,"declared_http_bytes":len(raw),"obtained_bytes":len(raw),"source_url":evidence["source_url"],
                "fingerprint":hashes(raw)})
            path = self.root/"jobs/julie-ryan-publisher-latest20-synthetic/batch-01"/VIDEO/"publisher-transcript.retained.source.docx"
        else:
            text = raw = "A source \U0001f319 control\r\n\r\ngroup shows 528 Hz.\r\n".encode()
            for k in ("publisher_episode_binding","publisher_transcript_document","publisher_transcript_provenance","original_youtube_link"):
                source.pop(k)
            source.update(associated_youtube_id=VIDEO, channel_dir=creator, provider="Sounds True / ART19",
                          exact_youtube_crossreference=False, kind="qualified_publisher_mirror_audio_variant",
                          association_method="publisher_owner_title_date_duration")
            source["publisher_transcript"].update(**hashes(raw), paragraphs=2, source="https://www.soundstrue.com/a/resources/transcript/fixture/")
            path = self.root/"jobs/sounds-true-fixture/publisher-transcript.en.txt"
        source["caption_state"] = "english_publisher_transcript_untimed"
        path.parent.mkdir(parents=True)
        path.write_bytes(raw)
        return row, source, text, path

    def journal(self, record):
        (self.root/"sync/publisher_mirror_manifest.jsonl").write_text(json.dumps(record)+"\n", encoding="utf-8")

    def test_feed_declared_plaintext_stays_bound_to_the_episode_and_audio_hash(self):
        row, source, _, path = self.publish_fixture(office=False)
        show = "3a7c5d4f-efce-4ba6-bc3e-af4ada4aae47"
        url = f"https://hosting-media.riverside.com/media/podcasts/{show}/episodes/{UUID}/transcripts.txt"
        raw = ("We have the data. " * 180).encode()
        path.write_bytes(raw)
        source.update(provider="Riverside", watch_page_id=UUID, accepted_api_sha256="e"*64)
        text = source["publisher_transcript"]
        text.update(**hashes(raw), source=url, timed=False, paragraphs=1, words=720, english_common_words=540,
                    language_verification="english_show_and_document_lexical_check", usable_timed_text=False,
                    completeness="complete_publisher_declared_document", audio_alignment_verified=False)
        source["publisher_rss_transcript_provenance"] = {
            "feed_url":"https://api.riverside.fm/hosting/example.rss", "feed_sha256":"e"*64,
            "episode_guid":UUID, "publisher_show_id":show, "mime_type":"text/plain", "source_url":url,
            "source_audio_sha256":source["variant_id"], "show_language":"en-US",
            "observation":{"accepted":True, "eof_observed":True, "http_status":200, "source_url":url,
                           "declared_http_bytes":len(raw), "fingerprint":hashes(raw)}}
        for key, value in [("episode_guid", show), ("source_audio_sha256", "f"*64),
                           ("feed_sha256", "b"*64), ("source_url", url.replace(show, UUID))]:
            invalid = deepcopy(source)
            invalid["publisher_rss_transcript_provenance"][key] = value
            self.journal(invalid)
            self.assertEqual(list(reader.input_rows(self.root, [row], REMOTE)), [])
            audio, _, _, text_ids = reader.status.publisher_mirror_evidence(self.root, {VIDEO}, REMOTE, [row])
            self.assertEqual(audio, {VIDEO})
            self.assertEqual(text_ids, set())
        self.journal(source)
        (job,) = reader.input_rows(self.root, [row], REMOTE)
        view = reader.text_views(path, job, REMOTE)["english"]
        self.assertEqual(view["source_url"], url)
        self.assertEqual(view["text"].encode(), raw)
        self.assertEqual(view["association_evidence"], "publisher_declared_episode_text")
        self.assertFalse(view["usable_timed_text"])
        self.assertIsNone(view["segments"][0]["time_start"])
        self.assertEqual(reader.status.publisher_mirror_evidence(self.root, {VIDEO}, REMOTE, [row])[3], {VIDEO})

    def test_docx_reproduces_distinct_verified_plaintext_and_xml_paragraph_positions(self):
        row, source, text, path = self.publish_fixture()
        self.journal(source)
        (job,) = reader.input_rows(self.root, [row], REMOTE, additional_verified_records=[source,source])
        self.assertEqual(reader.local_bundle(self.root, job), path)
        result = reader.text_views(path, job, REMOTE)["english"]
        self.assertEqual(result["text"].encode(),text)
        self.assertEqual([span["source_paragraph_index"] for span in result["segments"]],[0,2])
        self.assertEqual(result["source_document_sha256"],job["proof"]["sha256"])
        self.assertNotEqual(result["source_document_sha256"],result["text_sha256"])
        self.assertTrue(result["source_timecodes_present"])
        self.assertFalse(result["usable_timed_text"])
        self.assertIsNone(result["source_timebase"])
        for span in result["segments"]:
            self.assertIsNone(span["time_start"])
            self.assertIsNone(span["time_end"])
        self.assertEqual(result["text"][result["segments"][1]["char_start"]:result["segments"][1]["char_end"]],"A second thought.")

    def test_source_snapshot_wont_gain_a_foreign_document_or_transcript_by_same_title(self):
        row, source, _, path = self.publish_fixture()
        for keys, new in [(("publisher_transcript_provenance","associated_youtube_id"),"another0123"),
                          (("publisher_transcript_provenance","source_document_sha256"),"f"*64),
                          (("publisher_transcript_document","drive_id"),source["audio"]["drive_id"]),
                          (("publisher_transcript","timed"),True)]:
            bad=deepcopy(source);bad[keys[0]][keys[1]]=new
            self.assertEqual(list(reader.input_rows(self.root,[row],REMOTE,additional_verified_records=[bad])),[])
        self.assertEqual(list(reader.input_rows(self.root,[{**row,"tab":"shorts"}],REMOTE,additional_verified_records=[source])),[])
        self.assertEqual(list(reader.input_rows(self.root,[{**row,"channel_id":"UC"+"0"*22}],REMOTE,additional_verified_records=[source])),[])
        wrong=deepcopy(source);wrong["publisher_transcript"]["sha256"]="9"*64
        (job,)=reader.input_rows(self.root,[row],REMOTE,additional_verified_records=[wrong])
        with self.assertRaisesRegex(ValueError,"reproduce"):
            reader.text_views(path,job,REMOTE)

    def test_html_derived_plaintext_retains_exact_line_endings_and_qualification(self):
        row, source, text, path = self.publish_fixture(office=False)
        self.journal(source)
        (job,) = reader.input_rows(self.root,[row],REMOTE)
        view = reader.text_views(reader.local_bundle(self.root,job),job,REMOTE)["english"]
        self.assertEqual(view["text"].encode(),text)
        self.assertEqual(view["source_document_sha256"],view["text_sha256"])
        self.assertEqual(view["association_evidence"],"qualified_title_date_duration")
        self.assertFalse(view["recording_equivalence_verified"])
        self.assertFalse(view["native_youtube_alignment_verified"])
        self.assertFalse(view["source_timecodes_present"])
        self.assertIsNone(view["speaker_attribution"])
        self.assertTrue(all(p["source_member"]=="publisher-transcript.en.txt" for p in view["segments"]))
        path.write_bytes(text+b"!")
        with self.assertRaisesRegex(ValueError,"checksum mismatch"):
            reader.text_views(path,job,REMOTE)

    def test_docx_does_not_parse_external_entities_or_headers(self):
        archive=io.BytesIO()
        with ZipFile(archive,"w") as z:
            z.writestr("word/document.xml", '<!DOCTYPE doc [<!ENTITY e SYSTEM "file:///absent">]><doc>&e;</doc>')
        with self.assertRaisesRegex(ValueError,"type definitions"):
            reader._document(archive.getvalue())

    def test_equal_length_local_editions_are_resolved_by_the_receipt_hash(self):
        row, source, raw, original = self.publish_fixture(office=False)
        self.journal(source)
        (job,) = reader.input_rows(self.root, [row], REMOTE)
        other = self.root / "jobs/sounds-true-another-edition/publisher-transcript.en.txt"
        other.parent.mkdir()
        other.write_bytes(b"x" * len(raw))
        self.assertEqual(reader.local_bundle(self.root, job), original)

    def test_ordinary_staging_and_postrun_emit_cross_paragraph_evidence_and_keep_native_priority(self):
        row, source, _, local = self.publish_fixture(office=False)
        # The post-run CLI reads the normal configured remote. All fixture inputs remain local.
        remote = stage_archived_text.ingestion_status.DEFAULT_REMOTE
        for name in ("audio", "provenance", "publisher_transcript"):
            source[name]["remote"] = source[name]["remote"].replace(REMOTE, remote)
        self.journal(source)
        selected = {**row, "slot":1, "source_position":0, "title":"Synthetic episode", "channel_id":"UC" + "x"*22}
        selection = self.root/"selection.json"
        selection.write_text(json.dumps({"per_channel":20, "channels":[{"channel_dir":row["channel_dir"],
            "channel_id":selected["channel_id"], "items":[selected], "selected":1, "scope":"short_complete_displayed_list"}]}))
        pin = hashes(selection.read_bytes())["sha256"]
        drive = Mock()
        info = stage_archived_text.stage(self.root, selection, pin, drive, inventory_only=True)
        self.assertEqual(info["archive_inputs"],{reader.KIND:1})
        self.assertEqual(info["untimed_publisher_inputs_by_creator"],{"sounds-true":1})
        self.assertFalse((self.root/"analysis").exists())
        with patch.object(stage_archived_text,"headroom",return_value=20_000_000):
            staged = stage_archived_text.stage(self.root, selection, pin, drive)
            self.assertEqual(staged["held"],[])
            self.assertEqual(staged["views_staged"],1)
            with patch.object(reader,"text_views",side_effect=AssertionError("redundant local verification")):
                self.assertEqual(stage_archived_text.stage(self.root, selection, pin, drive)["views_staged"],1)
        self.assertTrue(local.is_file())
        self.assertEqual(drive.mock_calls,[])
        run = postrun_candidates.run(self.root, selection, pin)
        evidence = [json.loads(line) for line in (run/"concordance.jsonl").read_bytes().splitlines()]
        control, = [r for r in evidence if r.get("rule_id") == "science_control_cue"]
        self.assertEqual(control["evidence_granularity"],"paragraph")
        self.assertEqual(control["matched_text"],"control\r\n\r\ngroup")
        self.assertEqual([m["source_paragraph_index"] for m in control["raw_offset_mapping"]],[0,1])
        self.assertEqual(control["raw_offset_mapping"][1]["normalized_paragraph_end"],5)
        self.assertFalse(any("normalized_cue_end" in m for m in control["raw_offset_mapping"]))
        self.assertIsNone(control["source_time_start_or_null"])
        self.assertIsNone(control["source_time_end_or_null"])
        anchor, = [r for r in evidence if r["record_type"] == "anchor"]
        self.assertEqual(anchor["raw_segment_ids"],control["raw_segment_ids"])
        roster, = json.loads((run/"view-inventory.json").read_bytes())
        self.assertEqual(roster["selected_primary"]["paragraph_count"],2)
        self.assertEqual(roster["selected_primary"]["source_kind"],reader.KIND)
        self.assertEqual(roster["selected_primary"]["source_timebase"],None)
        view_path = next((self.root/"analysis/publisher_transcript_views").rglob("*.json"))
        view = json.loads(view_path.read_bytes())
        native = self.root/"analysis/caption_views"/VIDEO/"fixture.json"
        native.parent.mkdir(parents=True)
        native.write_text(json.dumps({**view,"source_kind":"published","source_timebase":"source_audio_seconds"}))
        ranks = postrun_candidates.select_views(self.root,[selected])[VIDEO]
        self.assertEqual([r["source_kind"] for r in ranks],["published",reader.KIND])
        view["segments"][0]["time_start"] = 224
        with self.assertRaisesRegex(ValueError,"media timestamp"):
            list(corpus_concordance.Concordance().records(view))
        view_path.write_text(json.dumps(view))
        with self.assertRaisesRegex(ValueError,"media timestamp"):
            postrun_candidates.select_views(self.root,[selected])
