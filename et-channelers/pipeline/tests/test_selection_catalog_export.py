"""Source-free contract tests for dated archive catalogs."""
import gzip
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from pipeline import selection_catalog_export as catalog
from pipeline.tests.test_prepare_regular_fifty import CHANNEL, row
from pipeline.tests.test_archive_catalog import receipt


REMOTE = "archive:audio"


class SelectionCatalogTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.first, self.second = row(0)["video_id"], row(1)["video_id"]

    def write(self, name, obj):
        path = self.root / name
        path.write_bytes(catalog.encoded(obj))
        return path

    def fresh(self, name="later selection.json", new_slug="example", count=2):
        rows = [dict(row(i), channel_dir=new_slug) for i in range(count)]
        return self.write(name, {"schema_version":1, "index_revision":2, "per_channel":50, "channels":[{
            "channel_dir":new_slug, "channel_id":CHANNEL, "channel_name":"Updated display name",
            "page_sha256":"d"*64, "observed_at":"2026-11-20T10:30:00Z", "public_items":rows,
            "public_listing_complete":True, "exhausted":True}]})

    def mixed(self):
        return self.write("original selection.json", {"schema_version":1,"per_channel":20,"channels":[{
            "channel_dir":"old-name","channel_id":CHANNEL,"scope":"short_complete_displayed_list","selected":1,
            "items":[{"slot":1,"source_position":0,"channel_dir":"old-name","channel_id":CHANNEL,
                      "video_id":self.second,"tab":"videos","title":"Earlier title"}]}]})

    def unpack(self, data, name):
        with ZipFile(io.BytesIO(data)) as bundle:
            self.assertIsNone(bundle.testzip())
            return [json.loads(s) for s in bundle.read(name).splitlines()]

    def test_two_dated_cohorts_keep_original_rank_and_owner_on_handle_change(self):
        older, fresh = self.mixed(), self.fresh(new_slug="new-handle")
        bundle, summary = catalog.build(self.root, [older, fresh], remote=REMOTE)
        rows = self.unpack(bundle, "catalog/selection-memberships.jsonl")
        memberships = [r for r in rows if r["video_id"] == self.second]
        self.assertEqual([(r["channel_dir"], r["channel_id"], r["listing_position_one_based"]) for r in memberships],
                         [("old-name",CHANNEL,1),("new-handle",CHANNEL,2)])
        self.assertEqual((summary["current_recordings"],summary["memberships"]), (2,3))
        self.assertEqual(summary["verified_archive_references"],0)
        with self.assertRaisesRegex(ValueError,"needs verified audio"):
            catalog.build(self.root,[older,fresh],remote=REMOTE,final=True)

    def test_sidecars_keep_disagreeing_upload_days_separate_from_release_date_and_redact_secrets(self):
        fresh = self.fresh()
        inputs=[]
        for i, date in enumerate(("20261101","20261102")):
            inputs.append(self.write(f"sidecar-{i}.json", {"source":{"platform":"youtube","video_id":self.first},"metadata":{
                "id":self.first, "channel_id":CHANNEL,"upload_date":date,"release_date":"20261015",
                "release_timestamp":1792023000, "title":"Saved title","description":"source C:\\Users\\secret\\item access_token=private-value",
                "chapters":[], "formats":[{"format_id":"140","acodec":"aac","url":"https://rr.googlevideo.com/videoplayback?sig=private-value"}],
                "subtitles":{"en":[{"name":"English (publisher)"}]},"automatic_captions":{"en-orig":[{"name":"English original"}],
                        "en":[{"name":"English"},{"url":"https://example.com/cap?tlang=en"}]},
                "http_headers":{"Authorization":"Bearer secretvalue"}}}))
        bundle, summary = catalog.build(self.root, [fresh], remote=REMOTE, sidecars=inputs)
        listing = self.unpack(bundle, "catalog/listings.jsonl")[0]
        self.assertEqual(listing["upload_day_evidence_state"], "multiple_observed_days")
        self.assertIsNone(listing["single_observed_upload_day"])
        self.assertEqual(listing["observed_upload_day_evidence"],{f"2026-11-0{i+1}":[catalog.digest(p.read_bytes())] for i,p in enumerate(inputs)})
        self.assertEqual((listing["declared_published_english"],listing["declared_original_automatic_english"],listing["automatic_english_alias_without_original_evidence"]),
                         (["en"],["en-orig"],["en"]))
        dates=self.unpack(bundle,"catalog/date-evidence.jsonl")
        self.assertTrue(any(d["field"]=="release_date" and d["value"]=="2026-10-15" and d["precision"]=="date" for d in dates))
        self.assertEqual(summary["rich_field_coverage"]["chapters"],{"present":0,"absent":1,"declared_empty":1})
        with ZipFile(io.BytesIO(bundle)) as z:
            entire=b"\n".join(z.read(n) for n in z.namelist())
            for raw in (b"private-value",b"googlevideo",b"Users",str(self.root).encode()):
                self.assertNotIn(raw,entire)
        previous=self.root/"previous catalog.zip";previous.write_bytes(bundle)
        replay, now=catalog.build(self.root,[fresh],remote=REMOTE,prior_catalogs=[previous])
        self.assertEqual(now["source_observations"],2)
        self.assertEqual(self.unpack(replay,"catalog/listings.jsonl")[0]["observed_upload_day_evidence"],listing["observed_upload_day_evidence"])

    def test_older_rich_pack_reuses_locator_observations_without_original_paths(self):
        fresh = self.fresh()
        source={"channel_id":CHANNEL,"title":"Older observation","upload_date":"2026-10-30"}
        fp=catalog.digest(catalog.encoded(source)); raw_key="1"*64
        rich=self.root/"rich.jsonl.gz"
        rich.write_bytes(gzip.compress(catalog.encoded({"video_id":self.second,"expected_channel_id":CHANNEL,"projection_sha256":fp,"metadata":source})+b"\n",mtime=0))
        locator=self.write("index.json",{"public_projection_archive":{"sha256":catalog.digest(rich.read_bytes()),"bytes":rich.stat().st_size},
            "per_video":{self.second:{"documents":[{"public_projection_sha256":fp,"input_sha256":raw_key,"input_bytes":90,
                                                  "path_relative_to_private_root":"foreign/missing/file.json"}],
                                   "declared_published_english":["en"],"declared_original_automatic_english":[]}}})
        delta=self.write("delta.json",{"baseline_sha256":catalog.digest(locator.read_bytes()),"observations":{}})
        bundle,summary=catalog.build(self.root,[fresh],remote=REMOTE,locator=locator,projections=rich,delta=delta)
        self.assertEqual((summary["source_observations"],summary["distinct_public_snapshots"]),(1,1))
        self.assertEqual(self.unpack(bundle,"catalog/source-observations.jsonl")[0]["input_sha256"],raw_key)
        self.assertEqual(self.unpack(bundle,"catalog/listings.jsonl")[1]["observed_upload_day_evidence"],{"2026-10-30":[raw_key]})
        changed=self.write("wrong-base.json",{"baseline_sha256":"9"*64,"observations":{}})
        with self.assertRaisesRegex(ValueError,"another metadata locator"):
            catalog.build(self.root,[fresh],remote=REMOTE,locator=locator,projections=rich,delta=changed)

    def test_prepared_fifty_cannot_use_stale_saved_flags_or_another_index(self):
        fresh=self.fresh()
        _,members,_=catalog.memberships(fresh)
        rows=[{"video_id":v,"channel_id":row["expected_channel_id"],"channel_dir":row["channel_dir"],"tab":row["tab"],
               "listing_rank":row["listing_rank"],"verified_audio":True} for v,row in members.items()]
        prepared=self.write("prepared.json",{"cohort":"Latest 50 public regular uploads","target":2,"rows":rows,"fresh_index_sha256":catalog.digest(fresh.read_bytes())})
        with self.assertRaisesRegex(ValueError,"original"):
            catalog.memberships(prepared)
        with self.assertRaisesRegex(ValueError,"needs verified audio"):
            catalog.build(self.root,[prepared],remote=REMOTE,fresh_index=fresh,final=True)
        out=self.root/"catalog.zip"
        with patch.object(catalog,"MIN_DISK_SPARE",0):
            catalog.main(["--root",str(self.root),"--selection",str(prepared),"--fresh-index",str(fresh),"--out",str(out)])
        self.assertTrue(out.exists())

    def test_bad_date_owner_cannot_contribute_publication_evidence(self):
        fresh=self.fresh();fp="a"*64
        overlay=self.write("dates.jsonl",{"video_id":self.first,"channel_id":"UC"+"1"*22,"publication_or_upload":{"precision":"date","value":"20261117"},"public_watch_evidence":{"sha256":fp}})
        with self.assertRaisesRegex(ValueError,"different channel"):
            catalog.build(self.root,[fresh],remote=REMOTE,overlays=[overlay])

    def test_closed_cohort_writes_one_verified_catalog_and_reuses_drive_receipt(self):
        fresh=self.fresh(count=1)
        journal=self.root/"sync/drive_ingest_manifest.jsonl"
        journal.parent.mkdir()
        obj=receipt(dict(row(0), listing_rank=0), remote=REMOTE)
        journal.write_bytes(catalog.encoded(obj)+b"\n")
        archive,summary=catalog.build(self.root,[fresh],remote=REMOTE,final=True)
        self.assertEqual(summary["state"],"verified_current_cohort")
        out=self.root/"closed.zip";out.write_bytes(archive)
        calls=[]
        class Drive:
            def copy(self,local,dest):
                self.data=local.read_bytes();calls.append(("copy",dest))
            def stat_batch(self,remote,paths,manifest):
                self.assertion=paths==set(manifest.read_text(encoding="utf8").splitlines())
                calls.append(("stat",self.assertion))
                return {k:{"ID":"catalog-object","Size":len(self.data),"Hashes":{"MD5":catalog.archive_catalog.digest(self.data)["md5"]}} for k in paths}
        drive=Drive()
        with patch.object(catalog.drive_ingest,"Rclone",return_value=drive):
            first=catalog.publish_catalog(out,archive,summary,root=self.root,remote=REMOTE,executable="unused")
            second=catalog.publish_catalog(out,archive,summary,root=self.root,remote=REMOTE,executable="unused")
        self.assertEqual(first,second)
        self.assertEqual([k for k,_ in calls],["copy","stat"])
        self.assertTrue(calls[-1][1])
        self.assertEqual(first["sha256"],catalog.digest(archive))

    def test_private_catalog_date_references_conflicting_native_hashes_and_foreign_channels(self):
        fresh=self.fresh(count=1)
        package,_=catalog.build(self.root,[fresh],remote=REMOTE)
        changed=self.root/"foreign.zip"
        with ZipFile(io.BytesIO(package)) as before,ZipFile(changed,"w") as after:
            for name in before.namelist():
                body=before.read(name)
                if name=="catalog/listings.jsonl":
                    record=json.loads(body)
                    record["channel_id"]="UC"+"9"*22
                    body=catalog.encoded(record)+b"\n"
                after.writestr(name,body)
        with self.assertRaisesRegex(ValueError,"another owner"):
            catalog.build(self.root,[fresh],remote=REMOTE,prior_catalogs=[changed])

    def test_offset_midnight_and_original_upload_day_keep_different_meanings(self):
        selection=self.fresh(count=1)
        overlay=self.write("dates.jsonl",{"video_id":self.first,"channel_id":CHANNEL,"date_quality":"instant",
            "publication_or_upload":{"value":"2026-10-01T01:15:00Z","precision":"instant"},
            "public_watch_evidence":{"sha256":"f"*64,"first_party_fields":[{"field":"uploadDate","precision":"instant",
                "value":"2026-10-01T01:15:00Z","source_value":"2026-09-30T18:15:00-07:00"}]}})
        data,_=catalog.build(self.root,[selection],remote=REMOTE,overlays=[overlay])
        listing=self.unpack(data,"catalog/listings.jsonl")[0]
        self.assertEqual(listing["observed_upload_day_evidence"],{})
        self.assertEqual(listing["watch_page_upload_calendar_days"],{"2026-09-30":["f"*64]})
        dates=self.unpack(data,"catalog/date-evidence.jsonl")
        self.assertIn(("instant","2026-10-01T01:15:00Z"),[(d["precision"],d["value"]) for d in dates])

    def test_earlier_checksum_verified_zip_members_keep_distinct_retrieval_handles(self):
        selection=self.fresh(count=1)
        data,_=catalog.build(self.root,[selection],remote=REMOTE)
        prior=self.root/"legacy-members.zip"
        references=[]
        for i in (1,2):
            name=f"example/Videos/{self.first}/data{i}.json"
            references.append({"kind":"archived_metadata_in_bundle","video_id":self.first,"bytes":400,"md5":"c"*32,"drive_id":"one-zip",
                "member_sha256":str(i)*64,"member_bytes":80,"private_archive_member":name,
                "zip_member_identifier_sha256":catalog.digest(name.encode())})
        with ZipFile(io.BytesIO(data)) as before,ZipFile(prior,"w") as after:
            for name in before.namelist():
                body=before.read(name)
                if name=="private/verified-drive-edition-references.jsonl":
                    body=b"".join(catalog.encoded(ref)+b"\n" for ref in references)
                after.writestr(name,body)
        final,summary=catalog.build(self.root,[selection],remote=REMOTE,prior_catalogs=[prior])
        old=self.unpack(final,"private/verified-drive-edition-references.jsonl")
        self.assertEqual(summary["verified_archive_references"],2)
        self.assertEqual({x["private_archive_member"] for x in old},{x["private_archive_member"] for x in references})
        self.assertTrue(all(x["sha256"] is None for x in old))
