from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import zipfile
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

    def item(self, video="source00001", kind=editions.EXTRACT, audio=b"fixed audio"):
        row = {"video_id":video,"channel_dir":"testing","tab":"videos"}
        def obj(data, name):
            return {"bytes":len(data),"md5":hashlib.md5(data).hexdigest(),"sha256":hashlib.sha256(data).hexdigest(),
                    "remote":self.remote+"/testing/"+video+"/"+name,"drive_id":video+"-"+name}
        return editions.source(kind,row,"a"*64,obj(audio,"audio.m4a"),obj(b"metadata","provenance.json"),
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

    def authorization(self, videos, **changes):
        document={"schema_version":1,"kind":editions.OUTSTANDING_KIND,"selection_sha256":self.selection,
                  "authorized_by":"owner","instruction_utc":"2026-11-20T02:30:00Z","outstanding_video_ids":list(videos),**changes}
        path=self.root/"outstanding.json"
        path.write_bytes(base.encoded(document))
        return path,base.hashes(path)["sha256"]

    def test_outstanding_authorization_is_hash_bound_and_names_only_selected_recordings(self):
        frame=[{"video_id":"source00001"},{"video_id":"absent00001"}]
        path,pin=self.authorization(["absent00001"])
        self.assertEqual(editions.authorized_outstanding(self.root,path,pin,self.selection,frame),frozenset({"absent00001"}))
        with self.assertRaisesRegex(ValueError,"changed"):
            editions.authorized_outstanding(self.root,path,"0"*64,self.selection,frame)
        for videos,changes in ((["elsewhere01"],{}),(["absent00001","absent00001"],{}),([],{}),
                               (["absent00001"],{"selection_sha256":"e"*64}),(["absent00001"],{"authorized_by":"worker"}),
                               (["absent00001"],{"instruction_utc":""})):
            with self.subTest(videos=videos,changes=changes):
                path,pin=self.authorization(videos,**changes)
                with self.assertRaises(ValueError):
                    editions.authorized_outstanding(self.root,path,pin,self.selection,frame)

    def test_unified_grouping_skips_exactly_the_authorized_outstanding_recordings(self):
        origin=self.item()
        rows=[{"video_id":origin["video_id"],"selected_source":origin,"status":"edition_asr_eligible"},
              {"video_id":"absent00001","selected_source":None,"status":"audio_missing"}]
        plan={"source_scope":editions.ALL_SOURCES,"rows":rows}
        with self.assertRaisesRegex(ValueError,"lacks a typed ASR source"):
            editions.grouped_sources(plan,plan)
        groups=editions.grouped_sources(plan,plan,outstanding=frozenset({"absent00001"}))
        self.assertEqual([[x["video_id"] for x in group] for group in groups],[[origin["video_id"]]])
        with self.assertRaisesRegex(ValueError,"now has audio"):
            editions.grouped_sources(plan,plan,outstanding=frozenset({"absent00001",origin["video_id"]}))

    def test_authorized_outstanding_list_processes_archived_audio_and_any_other_gap_fails_closed(self):
        origin=self.item()
        absent={"video_id":"absent00001","channel_dir":"testing","tab":"videos"}
        frame=[{k:origin[k] for k in ("video_id","channel_dir","tab")},absent]
        live={"profile":editions.PROFILE,"selection_sha256":self.selection,"remote":self.remote,
              "rows":[{"video_id":origin["video_id"],"selected_source":origin,"status":"edition_asr_eligible"},
                      {"video_id":absent["video_id"],"selected_source":None,"status":"audio_missing"}]}
        plan=self.root/"plan.json"
        plan.write_bytes(base.encoded(live))
        self.proposal=base.hashes(plan)["sha256"]
        sync=self.root/"sync"
        sync.mkdir()
        (sync/"STOP_DRIVE_INGEST").touch()
        coverage={"selection_sha256":self.selection,"summary":{"latest20_target":2,"audio_available":1,"channels":1,"remaining_audio":1}}
        live_lease={"input_frame_sha256":self.proposal,"rolling_utilization_target":.7,"max_vram_bytes":1400,"model":self.model}
        drive=Mock()
        stored={}
        def remote_copy(path,remote):
            stored[remote]=base.hashes(path)
        def remote_stat(remote):
            a=stored[remote]
            return {"ID":"new-output","Size":a["bytes"],"Hashes":{"md5":a["md5"]}}
        drive.copy.side_effect=remote_copy
        drive.stat.side_effect=remote_stat
        def fetch(_drive,remote,cache,needed):
            for name in needed:
                path=cache/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b"fixed audio" if name.endswith("audio.m4a") else b"metadata")
        infer_real=editions.infer
        def infer_test(*args,**kwargs):
            with patch.object(editions,"infer",infer_real):
                return self.inference(origin,"en")
        scopes={"testing":"short_complete_displayed_list"}
        with ExitStack() as stack:
            stack.enter_context(patch.object(editions.collection_coverage,"mixed_selection",return_value=(frame,scopes,self.selection)))
            stack.enter_context(patch.object(editions.collection_coverage,"coverage",return_value=(coverage,frame[:1])))
            stack.enter_context(patch.object(base,"inventory",return_value={}))
            stack.enter_context(patch.object(base,"gpu_lease",return_value=live_lease))
            stack.enter_context(patch.object(editions,"inventory",return_value=live))
            stack.enter_context(patch.object(editions,"source_catalogue",return_value={origin["video_id"]:{origin["source_key"]:origin}}))
            stack.enter_context(patch.object(multi,"model_proof",return_value=self.model))
            fetches=stack.enter_context(patch.object(stage_archived_text,"fetch_batch",side_effect=fetch))
            speech=stack.enter_context(patch.object(editions,"infer",side_effect=infer_test))
            model=Mock(return_value=self.runtime)
            arguments=(self.settings,plan,self.selection,plan,self.proposal,drive)
            for unlisted in (None,frozenset({"another0001"}),frozenset({absent["video_id"],"another0001"})):
                with self.subTest(outstanding=unlisted),self.assertRaises(ValueError):
                    editions.run(*arguments,runtime_factory=model,outstanding=unlisted)
            self.assertEqual((fetches.call_count,speech.call_count,model.call_count,drive.mock_calls),(0,0,0,[]))
            result=editions.run(*arguments,runtime_factory=model,limit=None,outstanding=frozenset({absent["video_id"]}))
        self.assertEqual([row["video_ids"] for row in result],[[origin["video_id"]]])
        self.assertEqual((fetches.call_count,speech.call_count,model.call_count),(1,1,1))
        journal=common.read_jsonl(sync/editions.JOURNAL)
        self.assertEqual([record["video_id"] for record in journal],[origin["video_id"]])
        self.assertFalse(list((self.root/"asr/input").rglob("audio.m4a")))

    def test_lease_admits_one_fully_named_english_model_and_nothing_looser(self):
        self.settings.gpu_owner="fixture-owner"
        pinned={"repository":"fixture-english","revision":"e"*40,"model_sha256":"c"*64,
                "model_dir":str(self.root/"models/english"),"model_receipt":str(self.root/"english-receipt.json")}
        lease={"schema_version":1,"state":"active","lease_id":self.settings.gpu_lease_id,"owner":"fixture-owner",
               "exclusive_owner":True,"device_index":0,"cpu_fallback_allowed":False,"additional_models_allowed":True,
               "expires_at":"2099-01-01T00:00:00Z","max_vram_bytes":4096,"rolling_utilization_target":.7,"english_model":pinned}
        path=self.root/"sync/gpu_lease.json"
        def saved(value):
            path.unlink(missing_ok=True)
            base.atomic_json(path,value)
        saved(lease)
        self.assertEqual(base.gpu_lease(self.settings)["english_model"],pinned)
        refused=[{k:v for k,v in lease.items() if k != "english_model"},{**lease,"additional_models_allowed":False},
                 {**lease,"english_model":{**pinned,"revision":"main"}},{**lease,"english_model":{**pinned,"model_sha256":""}},
                 {**lease,"english_model":{k:v for k,v in pinned.items() if k != "model_receipt"}},
                 {**lease,"parallel_windows":9},{**lease,"parallel_windows":"2"}]
        saved({**lease,"rolling_utilization_target":.8,"parallel_windows":2})
        self.assertEqual(base.gpu_lease(self.settings)["rolling_utilization_target"],.8)
        saved({**lease,"rolling_utilization_target":.81})
        with self.assertRaises(base.AsrError) as caught:
            base.gpu_lease(self.settings)
        self.assertEqual(caught.exception.kind,"gpu_target")
        for number,value in enumerate(refused):
            with self.subTest(case=number):
                saved(value)
                with self.assertRaises(base.AsrError) as caught:
                    base.gpu_lease(self.settings)
                self.assertEqual(caught.exception.kind,"gpu_lease_policy")
        saved(lease)
        with patch.object(base,"model_proof",return_value={**{k:pinned[k] for k in ("repository","revision")},"model_sha256":"d"*64}), \
             self.assertRaisesRegex(ValueError,"different English model"):
            editions.english_model(self.settings,lease)
        self.assertIsNone(editions.english_model(self.settings,{**lease,"additional_models_allowed":False}))

    def test_english_speech_is_recognized_by_the_english_model_and_the_result_names_both(self):
        origin=self.item()
        pinned={"repository":"fixture-english","revision":"e"*40,"model_sha256":"c"*64}
        engine=object()
        used=[]
        monitor=SimpleNamespace(begin=Mock(),finish=Mock(return_value={"sample_count":1}),guard=lambda:None)
        def segments(task,path,duration,guard):
            used.append(task.runtime.model)
            value=task.config["language"] if task.config["task"] == "transcribe" else "en"
            doc,text=test_corpus_asr_view.AsrViewTests.document(["signal 528 Hz","control"],value,True)
            return doc,text,4
        self.runtime.windows=Mock()
        for language,models in (("en",[engine]),("es",[self.runtime.model,self.runtime.model])):
            with self.subTest(language=language),ExitStack() as stack:
                used.clear()
                stack.enter_context(patch.object(base,"gpu_lease",return_value={"rolling_utilization_target":.7,"max_vram_bytes":1400}))
                stack.enter_context(patch.object(base,"inventory",return_value={}))
                stack.enter_context(patch.object(multi,"Monitor",return_value=monitor))
                stack.enter_context(patch.object(multi,"detect_language",return_value={"status":"accepted","language":language}))
                stack.enter_context(patch.object(base,"collect_segments",side_effect=segments))
                local=editions.infer(self.settings,origin,self.root/"invented.m4a",self.runtime,self.model,
                                     self.proposal,self.selection,lambda:None,english=(pinned,engine))
                self.assertEqual(used,models)
                record=multi.verify_pair(Path(local["bundle"]["path"]))["provenance"]
                self.assertEqual(record["compute"]["models_loaded"],2)
                if language == "en":
                    self.assertEqual((record["model"],record["identity"]["language_decision_model"]),(pinned,self.model))
                    self.assertEqual(record["compute"]["text_model_role"],"english_only")
                else:
                    self.assertEqual(record["model"],self.model)
                    self.assertNotIn("language_decision_model",record["identity"])
                    self.assertEqual(record["compute"]["text_model_role"],"multilingual")
        with ExitStack() as stack:
            used.clear()
            stack.enter_context(patch.object(base,"gpu_lease",return_value={"rolling_utilization_target":.7,"max_vram_bytes":1400}))
            stack.enter_context(patch.object(base,"inventory",return_value={}))
            stack.enter_context(patch.object(multi,"Monitor",return_value=monitor))
            stack.enter_context(patch.object(multi,"detect_language",return_value={"status":"accepted","language":"ja"}))
            stack.enter_context(patch.object(base,"collect_segments",side_effect=segments))
            local=editions.infer(self.settings,self.item("source00009",audio=b"other audio"),self.root/"invented.m4a",self.runtime,
                                 self.model,self.proposal,self.selection,lambda:None,parallel_windows=2)
            record=multi.verify_pair(Path(local["bundle"]["path"]))["provenance"]
            self.assertEqual((used,record["compute"]["model_workers"],record["compute"]["models_loaded"]),
                             ([self.runtime.model]*2,2,1))

    def test_parallel_windows_return_in_source_order_skip_saved_ones_and_surface_errors(self):
        import threading, time
        active,peak,gate=[0],[0],threading.Lock()
        class Engine:
            def transcribe(self,audio,**config):
                with gate:
                    active[0]+=1
                    peak[0]=max(peak[0],active[0])
                time.sleep(.02 if audio % 2 else .005)      # later windows may finish first
                with gate:
                    active[0]-=1
                if audio == 13:
                    raise RuntimeError("recognizer fault")
                return iter([f"window {audio}"]),SimpleNamespace(duration_after_vad=audio)
        def source(path,duration):
            for number in range(8):
                yield number*30.0,number
        ahead=editions.Lookahead(source,Engine(),{"task":"transcribe"},3,skip=lambda index:index in (2,5))
        seen=[]
        for start,audio in ahead.windows("invented",240):
            if audio in (2,5):
                self.assertIsNone(ahead.current)
                with self.assertRaisesRegex(ValueError,"not submitted"):
                    ahead.transcribe(audio)
                continue
            segments,info=ahead.transcribe(audio)
            seen.append((start,list(segments),info.duration_after_vad))
        ahead.close()
        self.assertEqual(seen,[(n*30.0,[f"window {n}"],n) for n in (0,1,3,4,6,7)])
        self.assertGreater(peak[0],1)
        self.assertLessEqual(peak[0],3)
        failing=editions.Lookahead(lambda path,duration:iter([(0.0,12),(30.0,13),(60.0,14)]),Engine(),{},2)
        steps=failing.windows("invented",90)
        next(steps)
        self.assertEqual(list(failing.transcribe(12)[0]),["window 12"])
        next(steps)
        with self.assertRaisesRegex(RuntimeError,"recognizer fault"):
            failing.transcribe(13)
        failing.close()
        binding={"repository":"fixture-english","revision":"e"*40,"model_sha256":"c"*64,"model_dir":"m","model_receipt":"r"}
        self.assertIsNotNone(base.english_binding({"english_model":{**binding,"parallel_windows":4}}))
        for value in (0,5,2.0,"2",True):
            self.assertIsNone(base.english_binding({"english_model":{**binding,"parallel_windows":value}}))

    def test_fetching_ahead_and_background_publication_keep_every_result_and_fetch_each_input_once(self):
        sounds={f"source0000{n}":f"audio number {n}".encode() for n in (1,2,3,4)}
        origins=[self.item(video,audio=data) for video,data in sounds.items()]
        frame=[{k:s[k] for k in ("video_id","channel_dir","tab")} for s in origins]
        live={"profile":editions.PROFILE,"selection_sha256":self.selection,"remote":self.remote,
              "rows":[{"video_id":s["video_id"],"selected_source":s,"status":"edition_asr_eligible"} for s in origins]}
        plan=self.root/"plan.json"
        plan.write_bytes(base.encoded(live))
        self.proposal=base.hashes(plan)["sha256"]
        sync=self.root/"sync"
        sync.mkdir()
        (sync/"STOP_DRIVE_INGEST").touch()
        coverage={"selection_sha256":self.selection,"summary":{"latest20_target":4,"audio_available":4,"channels":1,"remaining_audio":0}}
        live_lease={"input_frame_sha256":self.proposal,"rolling_utilization_target":.7,"max_vram_bytes":1400,"model":self.model}
        drive=Mock()
        stored={}
        def remote_copy(path,remote):
            stored[remote]=base.hashes(path)
        def remote_stat(remote):
            a=stored[remote]
            return {"ID":"output-"+a["md5"],"Size":a["bytes"],"Hashes":{"md5":a["md5"]}}
        drive.copy.side_effect=remote_copy
        drive.stat.side_effect=remote_stat
        by_hash={hashlib.sha256(data).hexdigest():data for data in sounds.values()}
        fetched=[]
        def fetch(_drive,remote,cache,needed):
            for name,proof in needed.items():
                fetched.append(name)
                path=cache/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(by_hash.get(proof["sha256"],b"metadata"))
        infer_real=editions.infer
        def infer_test(settings,origin,*args,**kwargs):
            with patch.object(editions,"infer",infer_real):
                return self.inference(origin,"en")
        with ExitStack() as stack:
            stack.enter_context(patch.object(editions.collection_coverage,"mixed_selection",return_value=(frame,{"testing":"short_complete_displayed_list"},self.selection)))
            stack.enter_context(patch.object(editions.collection_coverage,"coverage",return_value=(coverage,frame)))
            stack.enter_context(patch.object(base,"inventory",return_value={}))
            stack.enter_context(patch.object(base,"gpu_lease",return_value=live_lease))
            stack.enter_context(patch.object(editions,"inventory",return_value=live))
            stack.enter_context(patch.object(editions,"source_catalogue",return_value={s["video_id"]:{s["source_key"]:s} for s in origins}))
            stack.enter_context(patch.object(multi,"model_proof",return_value=self.model))
            stack.enter_context(patch.object(stage_archived_text,"fetch_batch",side_effect=fetch))
            speech=stack.enter_context(patch.object(editions,"infer",side_effect=infer_test))
            model=Mock(return_value=self.runtime)
            result=editions.run(self.settings,plan,self.selection,plan,self.proposal,drive,runtime_factory=model,
                                limit=None,prefetch=2,background_publish=True,drive_slots=5)
        self.assertEqual(editions.drive_ingest._DRIVE_CALLS._initial_value,2)
        self.assertEqual([row["video_ids"] for row in result],[[s["video_id"]] for s in origins])
        self.assertEqual({row["state"] for row in result},{"verified"})
        self.assertEqual((speech.call_count,model.call_count,drive.copy.call_count),(4,1,4))
        self.assertEqual(sorted(fetched),sorted(name for s in origins for name in
                         (f"testing/{s['video_id']}/audio.m4a",f"testing/{s['video_id']}/provenance.json")))
        self.assertEqual([r["video_id"] for r in common.read_jsonl(sync/editions.JOURNAL)],[s["video_id"] for s in origins])
        self.assertFalse(list((self.root/"asr/input").rglob("audio.m4a")))

    def test_unclear_probes_follow_one_strong_probe_then_the_creator_and_two_languages_still_wait(self):
        def held(reason, *probes):
            return {"status":"held","reason":reason,
                    "probes":[{"language":language,"probability":chance} for language,chance in probes]}
        creator=("pt","creator_established_language")
        cases=[(held("mixed_or_conflicting_language",("en",.99)),creator,None),
               (held("metadata_nonlexical_review"),creator,None),
               (held("language_confidence_insufficient",("en",.97),(None,0),(None,0)),creator,("en","single_strong_probe")),
               (held("language_confidence_insufficient",("nl",.87),("en",.98)),creator,None),
               (held("no_reliable_speech",(None,0),(None,0)),creator,creator),
               (held("language_confidence_insufficient",("en",.62)),None,None),
               (held("insufficient_independent_sensitive_speech_evidence"),("en","owner_default_english"),("en","owner_default_english"))]
        for number,(decision,choice,expected) in enumerate(cases):
            with self.subTest(case=number):
                self.assertEqual(editions.fallback_language(decision,choice),expected)
        spoken={"segments":[{"start":0.0,"end":5.0},{"start":40.0,"end":50.0},{"start":60.0,"end":61.0}]}
        self.assertEqual(editions.quiet_spans(spoken,120.0),[[5.0,40.0],[61.0,120.0]])
        self.assertEqual(editions.quiet_spans({"segments":[]},45.0),[[0.0,45.0]])

    def test_policy_transcribes_a_recording_with_unclear_probes_and_keeps_the_detector_answer(self):
        origin=self.item()
        detector={"status":"held","reason":"no_reliable_speech","probes":[{"language":None,"probability":0}]}
        monitor=SimpleNamespace(begin=Mock(),finish=Mock(return_value={"sample_count":1}),guard=lambda:None)
        def segments(task,path,duration,guard):
            value=task.config["language"] if task.config["task"] == "transcribe" else "en"
            doc,text=test_corpus_asr_view.AsrViewTests.document(["signal 528 Hz","control"],value,True)
            return doc,text,4
        def attempt(**options):
            with ExitStack() as stack:
                stack.enter_context(patch.object(base,"gpu_lease",return_value={"rolling_utilization_target":.7,"max_vram_bytes":1400}))
                stack.enter_context(patch.object(base,"inventory",return_value={}))
                stack.enter_context(patch.object(multi,"Monitor",return_value=monitor))
                stack.enter_context(patch.object(multi,"detect_language",return_value=detector))
                stack.enter_context(patch.object(base,"collect_segments",side_effect=segments))
                return editions.infer(self.settings,origin,self.root/"invented.m4a",self.runtime,self.model,
                                      self.proposal,self.selection,lambda:None,**options)
        self.assertEqual(attempt()["status"],"language_review")
        self.assertEqual(attempt(language_fallback={"channel":None})["status"],"language_review")
        local=attempt(language_fallback={"channel":("pt","creator_established_language")})
        record=multi.verify_pair(Path(local["bundle"]["path"]))["provenance"]
        decision=record["language_decision"]
        self.assertEqual((decision["language"],decision["basis"],decision["detector_decision"]),
                         ("pt","creator_established_language",detector))
        self.assertEqual(local["language_decision"],decision)
        self.assertEqual(set(record["text_variants"]),{"original","english"})
        task=record["metrics"]["tasks"]["original"]
        self.assertEqual((task["non_speech_seconds"],task["quiet_stretches_of_30s_or_more"]),(3.0,0))

    def test_a_held_recording_is_taken_up_in_the_last_sweep_with_english_and_only_under_the_policy(self):
        origin=self.item()
        frame=[{k:origin[k] for k in ("video_id","channel_dir","tab")}]
        live={"profile":editions.PROFILE,"selection_sha256":self.selection,"remote":self.remote,
              "rows":[{"video_id":origin["video_id"],"selected_source":origin,"status":"edition_asr_eligible"}]}
        plan=self.root/"plan.json"
        plan.write_bytes(base.encoded(live))
        self.proposal=base.hashes(plan)["sha256"]
        sync=self.root/"sync"
        sync.mkdir()
        (sync/"STOP_DRIVE_INGEST").touch()
        detector={"status":"held","reason":"no_reliable_speech","probes":[]}
        hold=self.root/"asr/jobs"/("edition-"+origin["audio"]["sha256"])/"language-review.json"
        hold.parent.mkdir(parents=True)
        hold.write_bytes(base.encoded({"status":"language_review","decision":detector,"source":origin,"proposal_sha256":self.proposal}))
        coverage={"selection_sha256":self.selection,"summary":{"latest20_target":1,"audio_available":1,"channels":1,"remaining_audio":0}}
        live_lease={"input_frame_sha256":self.proposal,"rolling_utilization_target":.7,"max_vram_bytes":1400,"model":self.model}
        drive=Mock()
        stored={}
        drive.copy.side_effect=lambda path,remote:stored.__setitem__(remote,base.hashes(path))
        drive.stat.side_effect=lambda remote:{"ID":"new-output","Size":stored[remote]["bytes"],"Hashes":{"md5":stored[remote]["md5"]}}
        def fetch(_drive,remote,cache,needed):
            for name in needed:
                path=cache/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b"fixed audio" if name.endswith("audio.m4a") else b"metadata")
        received=[]
        infer_real=editions.infer
        def infer_test(settings,source,*args,**options):
            received.append((options.get("language_fallback"),options.get("prior_decision")))
            with patch.object(editions,"infer",infer_real):
                return self.inference(source,"en")
        with ExitStack() as stack:
            stack.enter_context(patch.object(editions.collection_coverage,"mixed_selection",return_value=(frame,{"testing":"short_complete_displayed_list"},self.selection)))
            stack.enter_context(patch.object(editions.collection_coverage,"coverage",return_value=(coverage,frame)))
            stack.enter_context(patch.object(base,"inventory",return_value={}))
            stack.enter_context(patch.object(base,"gpu_lease",return_value=live_lease))
            stack.enter_context(patch.object(editions,"inventory",return_value=live))
            stack.enter_context(patch.object(editions,"source_catalogue",return_value={origin["video_id"]:{origin["source_key"]:origin}}))
            stack.enter_context(patch.object(multi,"model_proof",return_value=self.model))
            stack.enter_context(patch.object(stage_archived_text,"fetch_batch",side_effect=fetch))
            speech=stack.enter_context(patch.object(editions,"infer",side_effect=infer_test))
            model=Mock(return_value=self.runtime)
            arguments=(self.settings,plan,self.selection,plan,self.proposal,drive)
            self.assertEqual(editions.run(*arguments,runtime_factory=model,limit=None),[])
            self.assertEqual((speech.call_count,drive.mock_calls),(0,[]))
            result=editions.run(*arguments,runtime_factory=model,limit=None,language_fallback=True)
        self.assertEqual([(row["state"],row["video_ids"]) for row in result],[("verified",[origin["video_id"]])])
        self.assertEqual(received,[({"channel":("en","owner_default_english")},detector)])
        self.assertFalse(hold.exists())
        self.assertTrue(hold.with_name("language-review.resolved-by-policy.json").is_file())
        self.assertEqual(len(common.read_jsonl(sync/editions.JOURNAL)),1)

    def test_an_english_creator_needs_no_probes_and_metadata_or_a_poor_transcript_brings_the_detector_back(self):
        monitor=SimpleNamespace(begin=Mock(),finish=Mock(return_value={"sample_count":1}),guard=lambda:None)
        quality={"en":-.1}
        def segments(task,path,duration,guard):
            value=task.config["language"] if task.config["task"] == "transcribe" else "en"
            doc,text=test_corpus_asr_view.AsrViewTests.document(["signal 528 Hz","control"],value,True)
            for row in doc["segments"]:
                row["avg_logprob"]=quality.get(task.config["language"],-.1)
            return doc,text,4
        number=iter(range(1,99))
        def attempt(detector,kind=editions.EXTRACT,**options):
            origin=self.item(f"source{next(number):05d}",kind,audio=f"sound {options} {detector}".encode())
            with ExitStack() as stack:
                stack.enter_context(patch.object(base,"gpu_lease",return_value={"rolling_utilization_target":.7,"max_vram_bytes":1400}))
                stack.enter_context(patch.object(base,"inventory",return_value={}))
                stack.enter_context(patch.object(multi,"Monitor",return_value=monitor))
                probe=stack.enter_context(patch.object(multi,"detect_language",return_value=detector))
                passes=stack.enter_context(patch.object(base,"collect_segments",side_effect=segments))
                if "metadata_path" in options:
                    options["metadata_path"].write_bytes(base.encoded({"source":{"video_id":origin["video_id"]},"languages":{"audio":"es"}}))
                local=editions.infer(self.settings,origin,self.root/"invented.m4a",self.runtime,self.model,
                                     self.proposal,self.selection,lambda:None,**options)
            record=multi.verify_pair(Path(local["bundle"]["path"]))["provenance"]
            self.assertEqual(record["language_decision"],local["language_decision"])
            return local["language_decision"],probe.call_count,passes.call_count
        spanish={"status":"accepted","language":"es","basis":"model_agreement_across_speech_probes","probes":[]}
        unclear={"status":"held","reason":"no_reliable_speech","probes":[]}
        creator={"language":"en","votes":3}
        decision,probes,passes=attempt(spanish,channel_language=creator)
        self.assertEqual((probes,passes,decision),(0,1,{"status":"accepted","language":"en",
                         "basis":"creator_established_language","policy":editions.CHANNEL_POLICY,
                         "creator_detector_votes":3,"detector_decision":None}))
        decision,probes,passes=attempt(spanish)
        self.assertEqual((probes,passes,decision),(1,2,spanish))
        decision,probes,passes=attempt(spanish,editions.NATIVE,channel_language=creator,metadata_path=self.root/"declared.json")
        self.assertEqual((probes,passes,decision),(1,2,spanish))
        quality["en"]=editions.DOUBT_LOG_PROBABILITY-.4
        decision,probes,passes=attempt(spanish,channel_language=creator)
        self.assertEqual((probes,passes,decision),(1,3,{**spanish,"replaced_creator_language":"en",
                         "transcript_log_probability":-.9,"doubt_below":editions.DOUBT_LOG_PROBABILITY}))
        decision,probes,passes=attempt(unclear,channel_language=creator)
        self.assertEqual((probes,passes,decision["language"],decision["basis"],decision["detector_decision"],
                          decision["transcript_log_probability"]),(1,1,"en","creator_established_language",unclear,-.9))
        self.assertEqual(editions.transcript_confidence({"segments":[{"start":0,"end":3,"avg_logprob":-.2},
                         {"start":3,"end":4,"avg_logprob":-1.0},{"start":4,"end":9}]}),-.4)
        self.assertIsNone(editions.transcript_confidence({"segments":[{"start":0,"end":3}]}))

    def test_english_creators_come_first_without_probes_then_unknown_creators_then_other_languages(self):
        def made(video,channel):
            data=("sound of "+video).encode()
            def obj(body,name):
                return {"bytes":len(body),"md5":hashlib.md5(body).hexdigest(),"sha256":hashlib.sha256(body).hexdigest(),
                        "remote":self.remote+"/"+channel+"/"+video+"/"+name,"drive_id":video+"-"+name}
            return data,editions.source(editions.EXTRACT,{"video_id":video,"channel_dir":channel,"tab":"videos"},"a"*64,
                                        obj(data,"audio.m4a"),obj(b"metadata","provenance.json"),7.0,"fixture-edition",{"video":video})
        listed=[("japanese001","ja-person"),("english0001","en-person"),("japanese002","ja-person"),("english0002","en-person"),
                ("newperson01","new-person"),("japanese003","ja-person"),("english0003","en-person"),("english0004","en-person")]
        pairs=[made(video,channel) for video,channel in listed]
        origins=[origin for _,origin in pairs]
        by_hash={hashlib.sha256(data).hexdigest():data for data,_ in pairs}
        frame=[{k:s[k] for k in ("video_id","channel_dir","tab")} for s in origins]
        live={"profile":editions.PROFILE,"selection_sha256":self.selection,"remote":self.remote,
              "rows":[{"video_id":s["video_id"],"selected_source":s,"status":"edition_asr_eligible"} for s in origins]}
        plan=self.root/"plan.json"
        plan.write_bytes(base.encoded(live))
        self.proposal=base.hashes(plan)["sha256"]
        sync=self.root/"sync"
        sync.mkdir()
        (sync/"STOP_DRIVE_INGEST").touch()
        coverage={"selection_sha256":self.selection,"summary":{"latest20_target":8,"audio_available":8,"channels":3,"remaining_audio":0}}
        live_lease={"input_frame_sha256":self.proposal,"rolling_utilization_target":.7,"max_vram_bytes":1400,"model":self.model}
        drive=Mock()
        stored={}
        drive.copy.side_effect=lambda path,remote:stored.__setitem__(remote,base.hashes(path))
        drive.stat.side_effect=lambda remote:{"ID":"output-"+stored[remote]["md5"],"Size":stored[remote]["bytes"],
                                              "Hashes":{"md5":stored[remote]["md5"]}}
        def fetch(_drive,remote,cache,needed):
            for name,proof in needed.items():
                path=cache/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(by_hash.get(proof["sha256"],b"metadata"))
        monitor=SimpleNamespace(begin=Mock(),finish=Mock(return_value={"sample_count":1}),guard=lambda:None)
        def segments(task,path,duration,guard):
            value=task.config["language"] if task.config["task"] == "transcribe" else "en"
            doc,text=test_corpus_asr_view.AsrViewTests.document(["signal 528 Hz","control"],value,True)
            return doc,text,4
        received=[]
        infer_real=editions.infer
        def infer_test(settings,source,audio,runtime,model,proposal,selection,guard,**options):
            received.append((source["video_id"],options.get("channel_language")))
            spoken="ja" if source["channel_dir"] == "ja-person" else "en"
            detector={"status":"accepted","language":spoken,"basis":"model_agreement_across_speech_probes","probes":[]}
            with ExitStack() as inner:
                inner.enter_context(patch.object(editions,"infer",infer_real))
                inner.enter_context(patch.object(multi,"Monitor",return_value=monitor))
                inner.enter_context(patch.object(multi,"detect_language",return_value=detector))
                inner.enter_context(patch.object(base,"collect_segments",side_effect=segments))
                return infer_real(settings,source,audio,runtime,model,proposal,selection,guard,
                                  **({"channel_language":options["channel_language"]} if "channel_language" in options else {}))
        with ExitStack() as stack:
            stack.enter_context(patch.object(editions.collection_coverage,"mixed_selection",return_value=(
                frame,{name:"short_complete_displayed_list" for name in ("ja-person","en-person","new-person")},self.selection)))
            stack.enter_context(patch.object(editions.collection_coverage,"coverage",return_value=(coverage,frame)))
            stack.enter_context(patch.object(base,"inventory",return_value={}))
            stack.enter_context(patch.object(base,"gpu_lease",return_value=live_lease))
            stack.enter_context(patch.object(editions,"inventory",return_value=live))
            stack.enter_context(patch.object(editions,"source_catalogue",return_value={s["video_id"]:{s["source_key"]:s} for s in origins}))
            stack.enter_context(patch.object(multi,"model_proof",return_value=self.model))
            stack.enter_context(patch.object(stage_archived_text,"fetch_batch",side_effect=fetch))
            stack.enter_context(patch.object(editions,"infer",side_effect=infer_test))
            model=Mock(return_value=self.runtime)
            arguments=(self.settings,plan,self.selection,plan,self.proposal,drive)
            first=editions.run(*arguments,runtime_factory=model,limit=4)
            self.assertEqual([row["video_ids"][0] for row in first],[video for video,_ in listed[:4]])
            self.assertEqual(received,[(video,None) for video,_ in listed[:4]])
            del received[:]
            editions.run(*arguments,runtime_factory=model,limit=None,english_first=True,channel_language=True)
        english={"language":"en","votes":2}
        self.assertEqual(received,[("english0003",english),("english0004",english),("newperson01",None),("japanese003",None)])
        journal=common.read_jsonl(sync/editions.JOURNAL)
        self.assertEqual([r["video_id"] for r in journal],["japanese001","english0001","japanese002","english0002",
                                                           "english0003","english0004","newperson01","japanese003"])
        self.assertEqual([(r["language_decision"]["language"],r["language_decision"]["basis"]) for r in journal[4:]],
                         [("en","creator_established_language")]*2+[("en","model_agreement_across_speech_probes"),
                                                                     ("ja","model_agreement_across_speech_probes")])

    def test_an_unclear_second_look_follows_the_policy_and_a_recovered_result_keeps_its_language_decision(self):
        monitor=SimpleNamespace(begin=Mock(),finish=Mock(return_value={"sample_count":1}),guard=lambda:None)
        def segments(task,path,duration,guard):
            value=task.config["language"] if task.config["task"] == "transcribe" else "en"
            doc,text=test_corpus_asr_view.AsrViewTests.document(["signal 528 Hz","control"],value,True)
            doc["duration_seconds"]=duration
            for row in doc["segments"]:
                row["avg_logprob"]=-.9 if task.config["language"] == "en" else -.2
            return doc,text,4
        def probe(seconds,language=None,chance=0):
            return {"start":0,"duration_seconds":30,"speech_seconds":seconds,"language":language,"probability":chance,
                    "margin":max(0,chance-.03)}
        def detector(*probes):
            job={"duration_seconds":600.0,"declared_audio_language":"und","metadata_content_flags":{}}
            return {**multi.decide_language(job,list(probes)),"probes":list(probes)}
        def attempt(video,answer,**options):
            origin={**self.item(video,audio=("sound "+video).encode()),"duration_seconds":600.0}
            with ExitStack() as stack:
                stack.enter_context(patch.object(base,"gpu_lease",return_value={"rolling_utilization_target":.7,"max_vram_bytes":1400}))
                stack.enter_context(patch.object(base,"inventory",return_value={}))
                stack.enter_context(patch.object(multi,"Monitor",return_value=monitor))
                stack.enter_context(patch.object(multi,"detect_language",return_value=answer))
                stack.enter_context(patch.object(base,"collect_segments",side_effect=segments))
                return origin,editions.infer(self.settings,origin,self.root/"invented.m4a",self.runtime,self.model,
                                             self.proposal,self.selection,lambda:None,**options)
        creator={"language":"en","votes":3}
        one_strong=detector(probe(1.0),probe(25.0,"es",.97),probe(1.5))
        mixed=detector(probe(25.0,"en",.96),probe(25.0,"es",.97),probe(25.0,"es",.95))
        self.assertEqual((one_strong["reason"],mixed["reason"]),("language_confidence_insufficient","mixed_or_conflicting_language"))
        origin,local=attempt("secondlook1",one_strong,channel_language=creator)
        decision=local["language_decision"]
        self.assertEqual((decision["language"],decision["basis"],decision["replaced_creator_language"],decision["detector_decision"]),
                         ("es","single_strong_probe","en",one_strong))
        recovered=editions.recover_local_result(self.settings,origin,self.selection,self.proposal)
        self.assertEqual((recovered["run_id"],recovered["language_decision"]),(local["run_id"],decision))
        _,local=attempt("secondlook2",mixed,channel_language=creator)
        self.assertEqual((local["status"],local["decision"]["reason"],local["decision"]["replaced_creator_language"]),
                         ("language_review","mixed_or_conflicting_language","en"))

    def test_without_an_english_model_a_second_recognition_never_reads_the_first_ones_saved_windows(self):
        origin=self.item("collision01",audio=b"sound collision")
        calls=[]
        def transcribe(audio,**config):
            calls.append((config["language"],config["task"]))
            text={("en","transcribe"):"wrong words",("es","transcribe"):"texto original",("es","translate"):"translated text"}[calls[-1]]
            part=SimpleNamespace(start=0.0,end=3.0,text=text,words=[],avg_logprob=-.9 if config["language"] == "en" else -.2,
                                 no_speech_prob=.1,compression_ratio=1.2)
            return iter([part]),SimpleNamespace(duration_after_vad=3.0)
        runtime=SimpleNamespace(model=SimpleNamespace(model=SimpleNamespace(device="cuda",compute_type="int8_float16"),transcribe=transcribe),
                                windows=lambda path,duration:iter([(0.0,[0]*int(duration*base.SAMPLE_RATE))]),
                                dependencies={"fixture":"1"},close=Mock())
        spanish={"status":"accepted","language":"es","basis":"model_agreement_across_speech_probes","probes":[]}
        monitor=SimpleNamespace(begin=Mock(),finish=Mock(return_value={"sample_count":1}),guard=lambda:None)
        with ExitStack() as stack:
            stack.enter_context(patch.object(base,"gpu_lease",return_value={"rolling_utilization_target":.7,"max_vram_bytes":1400}))
            stack.enter_context(patch.object(base,"inventory",return_value={}))
            stack.enter_context(patch.object(multi,"Monitor",return_value=monitor))
            stack.enter_context(patch.object(multi,"detect_language",return_value=spanish))
            local=editions.infer(self.settings,origin,self.root/"invented.m4a",runtime,self.model,self.proposal,self.selection,
                                 lambda:None,checkpoint_path=self.root/"asr/jobs/collision/windows.sqlite",worker_sha="c"*64,
                                 channel_language={"language":"en","votes":3})
        self.assertEqual(calls,[("en","transcribe"),("es","transcribe"),("es","translate")])
        with zipfile.ZipFile(local["bundle"]["path"]) as archive:
            self.assertEqual(archive.read("original/transcript.txt").decode().strip(),"texto original")
        self.assertEqual(local["language_decision"]["language"],"es")

    def test_recordings_taken_on_the_creators_language_stay_in_the_ratio_that_resolves_an_unclear_one(self):
        def made(video):
            data=("sound of "+video).encode()
            def obj(body,name):
                return {"bytes":len(body),"md5":hashlib.md5(body).hexdigest(),"sha256":hashlib.sha256(body).hexdigest(),
                        "remote":self.remote+"/testing/"+video+"/"+name,"drive_id":video+"-"+name}
            return data,editions.source(editions.EXTRACT,{"video_id":video,"channel_dir":"testing","tab":"videos"},"a"*64,
                                        obj(data,"audio.m4a"),obj(b"metadata","provenance.json"),7.0,"fixture-edition",{"video":video})
        pairs=[made(f"recording{n:02d}") for n in range(1,8)]
        origins=[origin for _,origin in pairs]
        by_hash={hashlib.sha256(data).hexdigest():data for data,_ in pairs}
        frame=[{k:s[k] for k in ("video_id","channel_dir","tab")} for s in origins]
        live={"profile":editions.PROFILE,"selection_sha256":self.selection,"remote":self.remote,
              "rows":[{"video_id":s["video_id"],"selected_source":s,"status":"edition_asr_eligible"} for s in origins]}
        plan=self.root/"plan.json"
        plan.write_bytes(base.encoded(live))
        self.proposal=base.hashes(plan)["sha256"]
        sync=self.root/"sync"
        sync.mkdir()
        (sync/"STOP_DRIVE_INGEST").touch()
        coverage={"selection_sha256":self.selection,"summary":{"latest20_target":7,"audio_available":7,"channels":1,"remaining_audio":0}}
        live_lease={"input_frame_sha256":self.proposal,"rolling_utilization_target":.7,"max_vram_bytes":1400,"model":self.model}
        drive=Mock()
        stored={}
        drive.copy.side_effect=lambda path,remote:stored.__setitem__(remote,base.hashes(path))
        drive.stat.side_effect=lambda remote:{"ID":"output-"+stored[remote]["md5"],"Size":stored[remote]["bytes"],
                                              "Hashes":{"md5":stored[remote]["md5"]}}
        def fetch(_drive,remote,cache,needed):
            for name,proof in needed.items():
                path=cache/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(by_hash.get(proof["sha256"],b"metadata"))
        monitor=SimpleNamespace(begin=Mock(),finish=Mock(return_value={"sample_count":1}),guard=lambda:None)
        accepted=lambda language:{"status":"accepted","language":language,"basis":"model_agreement_across_speech_probes","probes":[]}
        answers={"recording06":accepted("es"),"recording07":{"status":"held","reason":"no_reliable_speech","probes":[]}}
        infer_real=editions.infer
        def infer_test(settings,source,audio,runtime,model,proposal,selection,guard,**options):
            def segments(task,path,duration,guard):
                value=task.config["language"] if task.config["task"] == "transcribe" else "en"
                doc,text=test_corpus_asr_view.AsrViewTests.document(["signal 528 Hz","control"],value,True)
                for row in doc["segments"]:
                    row["avg_logprob"]=-.9 if (source["video_id"],value) == ("recording06","en") else -.1
                return doc,text,4
            with ExitStack() as inner:
                inner.enter_context(patch.object(editions,"infer",infer_real))
                inner.enter_context(patch.object(multi,"Monitor",return_value=monitor))
                inner.enter_context(patch.object(multi,"detect_language",return_value=answers.get(source["video_id"],accepted("en"))))
                inner.enter_context(patch.object(base,"collect_segments",side_effect=segments))
                return infer_real(settings,source,audio,runtime,model,proposal,selection,guard,
                                  **{k:options[k] for k in ("channel_language","language_fallback","prior_decision") if k in options})
        with ExitStack() as stack:
            stack.enter_context(patch.object(editions.collection_coverage,"mixed_selection",return_value=(
                frame,{"testing":"short_complete_displayed_list"},self.selection)))
            stack.enter_context(patch.object(editions.collection_coverage,"coverage",return_value=(coverage,frame)))
            stack.enter_context(patch.object(base,"inventory",return_value={}))
            stack.enter_context(patch.object(base,"gpu_lease",return_value=live_lease))
            stack.enter_context(patch.object(editions,"inventory",return_value=live))
            stack.enter_context(patch.object(editions,"source_catalogue",return_value={s["video_id"]:{s["source_key"]:s} for s in origins}))
            stack.enter_context(patch.object(multi,"model_proof",return_value=self.model))
            stack.enter_context(patch.object(stage_archived_text,"fetch_batch",side_effect=fetch))
            stack.enter_context(patch.object(editions,"infer",side_effect=infer_test))
            result=editions.run(self.settings,plan,self.selection,plan,self.proposal,drive,runtime_factory=Mock(return_value=self.runtime),
                                limit=None,channel_language=True,language_fallback=True)
        self.assertEqual({row["state"] for row in result},{"verified"})
        decided=[(r["language_decision"]["language"],r["language_decision"]["basis"],r["language_decision"].get("policy"))
                 for r in common.read_jsonl(sync/editions.JOURNAL)]
        detected,fallback=("model_agreement_across_speech_probes",None),"owner_2026-11-20_language_fallback"
        self.assertEqual(decided,[("en",*detected)]*2+[("en","creator_established_language",editions.CHANNEL_POLICY)]*3+
                                 [("es",*detected),("en","creator_established_language",fallback)])
