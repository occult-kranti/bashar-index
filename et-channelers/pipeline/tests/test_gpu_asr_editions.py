from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pipeline import common, gpu_asr as base, gpu_asr_editions as editions, gpu_asr_multilingual as multi
from pipeline import ingestion_status, postrun_candidates, stage_archived_text
from pipeline.tests import test_corpus_asr_view, test_qualified_direct_audio_receipts, test_qualified_edition_receipts
from pipeline.tests import test_shared_publisher_audio


class EditionAsrTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.lock = self.root / "environment.lock"
        self.lock.write_bytes(b"fixture")
        self.settings = SimpleNamespace(root=self.root,output_root=self.root/"asr/results",
                                        environment_lock=self.lock,gpu_lease_id="fixture-lease")
        self.model = {"repository":"fixture","revision":"f"*40,"model_sha256":"a"*64}
        self.remote = "example:Audio"
        self.runtime = SimpleNamespace(model=SimpleNamespace(model=SimpleNamespace(device="cuda",compute_type="int8_float16")),
                                       dependencies={"fixture":"1"},close=Mock())

    def item(self, video="source00001", kind=editions.EXTRACT):
        row = {"video_id":video,"channel_dir":"testing","tab":"videos"}
        def obj(data, name):
            return {"bytes":len(data),"md5":hashlib.md5(data).hexdigest(),"sha256":hashlib.sha256(data).hexdigest(),
                    "remote":self.remote+"/testing/"+video+"/"+name,"drive_id":video+"-"+name}
        return editions.source(kind,row,"a"*64,obj(b"fixed audio","audio.m4a"),obj(b"metadata","provenance.json"),
                               7.0,"fixture-edition",{"video":video})

    def inference(self, origin, language):
        monitor = SimpleNamespace(begin=Mock(),finish=Mock(return_value={"sample_count":1}),guard=lambda:None)
        def segments(rt, path, duration, guard):
            value = rt.config["language"] if rt.config["task"] == "transcribe" else "en"
            doc, text = test_corpus_asr_view.AsrViewTests.document(["signal 528 Hz","control"],value,True)
            return doc,text,4
        with ExitStack() as stack:
            stack.enter_context(patch.object(base,"gpu_lease",return_value={"rolling_utilization_target":.7,"max_vram_bytes":1400}))
            stack.enter_context(patch.object(base,"inventory",return_value={}))
            stack.enter_context(patch.object(multi,"Monitor",return_value=monitor))
            stack.enter_context(patch.object(multi,"detect_language",return_value={"status":"accepted","language":language}))
            calls = stack.enter_context(patch.object(base,"collect_segments",side_effect=segments))
            local = editions.infer(self.settings,origin,self.root/"invented.m4a",self.runtime,self.model,
                                   self.proposal,self.selection,lambda:None)
        self.assertEqual(calls.call_count,1 if language == "en" else 2)
        return local

    proposal = "b"*64
    selection = "d"*64

    def mock_drive(self, local):
        drive=Mock()
        drive.stat.return_value={"ID":"result-object","Size":local["bundle"]["bytes"],
                                 "Hashes":{"md5":local["bundle"]["md5"]}}
        return drive

    def test_reads_both_qualified_receipt_contracts_and_preserves_container_and_audio_hashes(self):
        for fixture,kind,remote in ((test_qualified_edition_receipts.receipt_fixture(),editions.EXTRACT,"etdrive:04 Audio"),
                                   (test_qualified_direct_audio_receipts.fixture(),editions.DIRECT,"testdrive:Audio")):
            with self.subTest(kind=kind):
                row={k:fixture[k] for k in ("video_id","channel_dir","tab")}
                path=self.root/"sync/progressive_audio_extracts_manifest.jsonl"
                common.append_jsonl(path,fixture)
                item=next(iter(editions.source_catalogue(self.root,[row],remote)[row["video_id"]].values()))
                self.assertEqual((item["source_type"],item["source_variant_id"]),(kind,fixture["variant_id"]))
                self.assertEqual(item["audio"]["sha256"],fixture["audio"]["local_proof"]["sha256"])
                self.assertEqual(item["audio"]["drive_id"],fixture["audio"]["remote_proof"]["drive_id"])
                path.unlink()
                bad=deepcopy(fixture)
                bad["metadata"]["remote_proof"]["drive_id"]=bad["audio"]["remote_proof"]["drive_id"]
                common.append_jsonl(path,bad)
                self.assertFalse(editions.source_catalogue(self.root,[row],remote))
                path.unlink()

    def test_english_same_audio_two_associations_one_inference_one_upload_two_distinct_views(self):
        main, other = self.item(kind=editions.PUBLISHER),self.item("source00002",editions.PUBLISHER)
        now={"rows":[{"video_id":x["video_id"],"selected_source":x,"status":"edition_asr_eligible"} for x in (main,other)]}
        groups=editions.grouped_sources(now,now)
        self.assertEqual(len(groups),1)
        local=self.inference(main,"en")
        drive=self.mock_drive(local)
        records=editions.publish(self.settings,local,groups[0],drive)
        self.assertEqual(len(records),2)
        self.assertEqual(drive.copy.call_count,1)
        self.assertEqual(drive.stat.call_count,1)
        self.assertEqual({r["drive_id"] for r in records},{"result-object"})
        choices=[]
        for item,record in zip(groups[0],records):
            row={k:item[k] for k in ("channel_dir","video_id","tab")}
            job={"edition":item,"record":record,"proof":record,"row":row,"kind":editions.RESULT}
            outputs=stage_archived_text.text_views(self.root,job,Path(local["bundle"]["path"]),self.remote)
            view=next(v for name,v in outputs.items() if "/english-" in name)
            choices.append(view["text_version_id"])
            self.assertEqual(view["source_timebase"],"publisher_audio_seconds")
            self.assertEqual(view["source_audio"]["drive_id"],item["audio"]["drive_id"])
            self.assertEqual(view["source_kind"],"publisher_original_asr")
            self.assertFalse(view["translation_performed"])
            self.assertFalse(view["native_youtube_alignment_verified"])
            self.assertEqual(view["segments"][0]["time_end"],3.4)
            for name,v in outputs.items():
                path=self.root/"analysis"/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps(v))
        self.assertEqual(len(set(choices)),2)
        self.assertEqual(set(postrun_candidates.select_views(self.root,[main,other])),{main["video_id"],other["video_id"]})
        self.assertFalse((self.root/"sync/asr_manifest.jsonl").exists())
        editions.publish(self.settings,local,groups[0],drive,existing_remote=editions.proof(records[0]))
        self.assertEqual(drive.copy.call_count,1)
        self.assertEqual(len(common.read_jsonl(self.root/"sync"/editions.JOURNAL)),2)

    def test_non_english_original_and_machine_translation_and_wrong_source_rejection(self):
        origin=self.item()
        local=self.inference(origin,"ja")
        rec=editions.publish(self.settings,local,[origin],self.mock_drive(local))[0]
        views=editions.text_views(Path(local["bundle"]["path"]),{"record":rec,"edition":origin})
        self.assertEqual(views["original"]["language"],"ja")
        self.assertEqual(views["english"]["source_kind"],"qualified_youtube_english_audio_translation")
        self.assertTrue(views["english"]["translation_performed"])
        self.assertEqual(views["english"]["source_timebase"],"qualified_youtube_audio_seconds")
        wrong=deepcopy(origin)
        wrong["audio"]["sha256"]="e"*64
        self.assertFalse(editions.accepted_result(rec,wrong))
        self.assertEqual(editions.recover_local_result(self.settings,origin,self.selection,self.proposal)["run_id"],rec["run_id"])
        self.assertIsNone(editions.recover_local_result(self.settings,origin,self.selection,"a"*64))
        with self.assertRaises(ValueError):
            editions.publish(self.settings,local,[wrong],Mock())

    def test_missing_remote_id_or_modified_md5_preserves_local_without_receipt(self):
        origin=self.item()
        local=self.inference(origin,"en")
        drive=self.mock_drive(local)
        drive.stat.return_value["ID"]=origin["audio"]["drive_id"]
        with self.assertRaises(ValueError):
            editions.publish(self.settings,local,[origin],drive)
        self.assertTrue(Path(local["bundle"]["path"]).is_file())
        self.assertFalse((self.root/"sync"/editions.JOURNAL).exists())
        drive.stat.return_value={"ID":"different","Size":local["bundle"]["bytes"],"Hashes":{"md5":"0"*32}}
        with self.assertRaises(editions.drive_ingest.IngestError):
            editions.publish(self.settings,local,[origin],drive)
        self.assertFalse((self.root/"sync"/editions.JOURNAL).exists())

    def test_shared_publisher_alias_requires_its_real_strict_anchor_and_own_pointer(self):
        case=test_shared_publisher_audio.SharedPublisherAudio()
        case.setUp()
        self.addCleanup(case.doCleanups)
        anchor,alias=case.receipts()
        anchor.update(actual_probe_duration_s=7.0,recording_equivalence_verified=False)
        alias["canonical_receipt_sha256"]=ingestion_status.publisher_receipt_digest(anchor)
        p=self.root/"sync/publisher_mirror_manifest.jsonl"
        for a in (alias,anchor):
            common.append_jsonl(p,a)
        frame=[{"video_id":v,"channel_dir":case.channel,"tab":"videos"} for v in (case.original,case.video)]
        found=editions.source_catalogue(self.root,frame,case.remote)
        one=next(iter(found[case.original].values()))
        two=next(iter(found[case.video].values()))
        self.assertEqual(editions.audio_identity(one),editions.audio_identity(two))
        self.assertEqual(two["canonical_associated_youtube_id"],case.original)
        self.assertEqual(two["association_provenance"]["drive_id"],alias["provenance"]["drive_id"])
        self.assertNotEqual(two["source_receipt_sha256"],one["source_receipt_sha256"])
        p.unlink()
        common.append_jsonl(p,alias)
        self.assertFalse(editions.source_catalogue(self.root,frame,case.remote))

    def test_held_collection_fails_before_model_or_drive_and_changed_proposal_fails_closed(self):
        video="source00001"
        document={"profile":editions.PROFILE,"selection_sha256":self.selection,"remote":self.remote,
                  "rows":[{"video_id":video,"selected_source":self.item()}]}
        plan=self.root/"proposal.json"
        plan.write_bytes(base.encoded(document))
        proposal=base.hashes(plan)["sha256"]
        frame=[{"channel_dir":"testing","video_id":video}]
        coverage={"selection_sha256":self.selection,"summary":{"latest20_target":1,"audio_available":0,
                                                        "channels":1,"remaining_audio":1}}
        drive=Mock()
        engine=Mock(side_effect=AssertionError("GPU access during collection"))
        with patch.object(editions.collection_coverage,"mixed_selection",return_value=(frame,{"testing":"short_complete_displayed_list"},self.selection)), \
             patch.object(editions.collection_coverage,"coverage",return_value=(coverage,[])):
            for pin in (proposal,"a"*64):
                with self.assertRaises(ValueError):
                    editions.run(self.settings,plan,self.selection,plan,pin,drive,runtime_factory=engine)
        engine.assert_not_called()
        self.assertEqual(drive.mock_calls,[])

    def test_explicit_pause_stays_effective_after_all_selected_audio_is_verified(self):
        origin=self.item()
        frame=[{"channel_dir":"testing","video_id":origin["video_id"]}]
        report={"profile":editions.PROFILE,"selection_sha256":self.selection,"remote":self.remote,
                "rows":[{"video_id":origin["video_id"],"selected_source":origin}]}
        plan=self.root/"proposal.json"
        plan.write_bytes(base.encoded(report))
        digest=base.hashes(plan)["sha256"]
        self.settings.gpu_owner="fixture-owner"
        lease={"schema_version":1,"state":"active","lease_id":self.settings.gpu_lease_id,"owner":"fixture-owner",
               "exclusive_owner":True,"device_index":0,"cpu_fallback_allowed":False,"additional_models_allowed":False,
               "expires_at":"2099-01-01T00:00:00Z","max_vram_bytes":4096,"rolling_utilization_target":.7,
               "input_frame_sha256":digest,"model":self.model}
        base.atomic_json(self.root/"sync/gpu_lease.json",lease)
        (self.root/"sync/STOP_DRIVE_INGEST").touch()
        (self.root/"asr").mkdir()
        (self.root/"asr/STOP_ASR").touch()
        coverage={"selection_sha256":self.selection,"summary":{"latest20_target":1,"audio_available":1,"channels":1,"remaining_audio":0}}
        drive=Mock()
        factory=Mock(side_effect=AssertionError("ASR is paused"))
        with patch.object(editions.collection_coverage,"mixed_selection",return_value=(frame,{"testing":"short_complete_displayed_list"},self.selection)), \
             patch.object(editions.collection_coverage,"coverage",return_value=(coverage,frame)),self.assertRaises(base.AsrError) as caught:
            editions.run(self.settings,plan,self.selection,plan,digest,drive,runtime_factory=factory)
        self.assertEqual(caught.exception.kind,"stop_requested")
        self.assertEqual(drive.mock_calls,[])
        factory.assert_not_called()

    def test_uncertain_language_holds_without_transcription_or_canonical_journal(self):
        item=self.item()
        monitor=SimpleNamespace(begin=Mock(),finish=Mock(return_value={}),guard=lambda:None)
        with patch.object(base,"gpu_lease",return_value={"rolling_utilization_target":.7,"max_vram_bytes":4096}), \
             patch.object(multi,"Monitor",return_value=monitor), \
             patch.object(multi,"detect_language",return_value={"status":"held","reason":"mixed_or_conflicting_language"}), \
             patch.object(base,"collect_segments",side_effect=AssertionError("Language unknown")) as inference:
            result=editions.infer(self.settings,item,self.root/"fixture",self.runtime,self.model,self.proposal,self.selection,lambda:None)
        self.assertEqual(result["status"],"language_review")
        inference.assert_not_called()
        self.assertFalse((self.root/"sync"/editions.JOURNAL).exists())

    def test_complete_fixture_restarts_failed_publication_without_another_input_fetch_or_inference(self):
        origins=[self.item(),self.item("source00002")]
        frame=[{k:s[k] for k in ("video_id","channel_dir","tab")} for s in origins]
        live={"profile":editions.PROFILE,"selection_sha256":self.selection,"remote":self.remote,
              "rows":[{"video_id":s["video_id"],"selected_source":s,"status":"edition_asr_eligible"} for s in origins]}
        plan=self.root/"plan.json"
        plan.write_bytes(base.encoded(live))
        self.proposal=base.hashes(plan)["sha256"]
        sync=self.root/"sync"
        sync.mkdir()
        (sync/"STOP_DRIVE_INGEST").touch()
        coverage={"selection_sha256":self.selection,"summary":{"latest20_target":2,"audio_available":2,"channels":1,"remaining_audio":0}}
        live_lease={"input_frame_sha256":self.proposal,"rolling_utilization_target":.7,"max_vram_bytes":1400,"model":self.model}
        drive=Mock()
        stored={}
        def remote_copy(path,remote):
            stored[remote]=base.hashes(path)
        def remote_stat(remote):
            a=stored[remote]
            return {"ID":"new-output","Size":a["bytes"],"Hashes":{"md5":a["md5"]}}
        drive.copy.side_effect=remote_copy
        drive.stat.side_effect=RuntimeError("simulated interrupted Drive verification")
        def fetch(_drive,remote,cache,needed):
            for name,proof in needed.items():
                path=cache/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b"fixed audio" if name.endswith("audio.m4a") else b"metadata")
        infer_real=editions.infer
        def infer_test(*args,**kwargs):
            with patch.object(editions,"infer",infer_real):
                return self.inference(origins[0],"en")
        with ExitStack() as stack:
            stack.enter_context(patch.object(editions.collection_coverage,"mixed_selection",return_value=(frame,{"testing":"short_complete_displayed_list"},self.selection)))
            stack.enter_context(patch.object(editions.collection_coverage,"coverage",return_value=(coverage,frame)))
            stack.enter_context(patch.object(base,"inventory",return_value={}))
            stack.enter_context(patch.object(base,"gpu_lease",return_value=live_lease))
            stack.enter_context(patch.object(editions,"inventory",return_value=live))
            stack.enter_context(patch.object(editions,"source_catalogue",return_value={s["video_id"]:{s["source_key"]:s} for s in origins}))
            stack.enter_context(patch.object(multi,"model_proof",return_value=self.model))
            fetches=stack.enter_context(patch.object(stage_archived_text,"fetch_batch",side_effect=fetch))
            speech=stack.enter_context(patch.object(editions,"infer",side_effect=infer_test))
            model=Mock(return_value=self.runtime)
            arguments=(self.settings,plan,self.selection,plan,self.proposal,drive)
            with self.assertRaisesRegex(RuntimeError,"interrupted"):
                editions.run(*arguments,runtime_factory=model)
            self.assertEqual(len(list((self.root/"asr/input").rglob("audio.m4a"))),1)
            self.assertFalse((sync/editions.JOURNAL).exists())
            drive.stat.side_effect=remote_stat
            result=editions.run(*arguments,runtime_factory=model)
            self.assertEqual(result[0]["video_ids"],[s["video_id"] for s in origins])
            self.assertEqual((fetches.call_count,speech.call_count,model.call_count),(1,1,1))
            self.assertEqual(len(common.read_jsonl(sync/editions.JOURNAL)),2)
            self.assertFalse(list((self.root/"asr/input").rglob("audio.m4a")))
