"""Check the actual project research entry points using a fake transport and temporary billing database."""
import hashlib
import json
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from pipeline import research_agents as agents, research_agent_budget as budget, research_agent_schedule as schedule


class PaidResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.parent = self.root / schedule.HOME
        self.parent.mkdir(parents=True)
        self.evidence = {"SELECTION": {"count": 3}}
        self.key = self.root / "unused-private-file"
        self.usage = {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120,
            "input_tokens_details": {"cached_tokens": 10}, "output_tokens_details": {"reasoning_tokens": 8}}
        self.answer = {"title": "Evidence review", "findings": [{"observation": "Three selected items.",
                       "evidence_ids": ["SELECTION"], "limitations": "A small test selection."}], "next_steps": []}

    def fake_response(self, payload, key, dispatch_id):
        data = json.loads(payload)
        self.assertRegex(dispatch_id, r"^[0-9a-f]{32}$")
        self.assertTrue(data["model"] == budget.MODEL and not data["store"] and data["tools"] == [])
        self.assertEqual(data["service_tier"], "default")
        return {"id": "resp_test_101", "model": data["model"], "service_tier": "default", "status": "completed",
            "usage": self.usage, "output": [{"type": "message", "role": "assistant",
            "content": [{"type": "output_text", "text": json.dumps(self.answer)}]}]}

    def call(self, sender):
        return agents.run_agent(self.parent, self.key, "methods", "source-audit", self.evidence, submit=sender)

    def test_restarting_a_completed_response_never_resends_or_recharges(self):
        send = Mock(side_effect=self.fake_response)
        with patch.object(agents, "read_key", return_value="test") as credential:
            original = self.call(send)
            again = self.call(send)
            self.assertEqual(original, again)
            self.assertEqual((credential.call_count, send.call_count), (1, 1))
        state = budget.BudgetLedger(self.parent / "budget.sqlite3").status()
        self.assertEqual((state["charged_micro_usd"], state["reserved_micro_usd"]),
                         (budget.usage_cost_micro_usd(self.usage), 0))

    def test_uncertain_reply_is_held_and_cannot_be_replayed(self):
        send = Mock(side_effect=agents.ResearchHold("api_http_503"))
        with patch.object(agents, "read_key", return_value="test"):
            with self.assertRaisesRegex(agents.ResearchHold, "api_http_503"):
                self.call(send)
            with self.assertRaisesRegex(agents.ResearchHold, "reconciliation"):
                self.call(send)
        self.assertEqual(send.call_count, 1)
        status = budget.BudgetLedger(self.parent / "budget.sqlite3").status()
        self.assertEqual(status["pending"][0]["state"], "uncertain")
        self.assertGreater(status["reserved_micro_usd"], 0)

    def test_bad_citation_still_settles_cost_once(self):
        self.answer["findings"][0]["evidence_ids"] = ["INVENTED"]
        send = Mock(side_effect=self.fake_response)
        with patch.object(agents, "read_key", return_value="test"):
            for _ in range(2):
                with self.assertRaisesRegex(agents.ResearchHold, "unbound_panel_finding"):
                    self.call(send)
        self.assertEqual(send.call_count, 1)
        self.assertGreater(budget.BudgetLedger(self.parent / "budget.sqlite3").status()["charged_micro_usd"], 0)

    def test_collection_wait_never_reads_credentials_or_calls_network(self):
        (self.root / "state").mkdir()
        schedule.save(self.parent / schedule.SETUP, {"cap_usd": "100.00", "model": budget.MODEL, "asr_state": "state",
                      "selection": {"sha256": "a"*64, "path": "selected.json"}})
        with patch.object(agents, "read_key", side_effect=AssertionError("early credential read")), \
             patch.object(schedule, "finish_round", side_effect=AssertionError("early funded call")):
            self.assertEqual(schedule.watch(self.root, once=True), {"state": "waiting_for_all_audio_receipts"})
        self.assertFalse((self.parent/"budget.sqlite3").exists())

    def test_incomplete_or_forged_scope_cannot_start_a_funded_agent(self):
        data = b'{"selection":"test"}'
        selection = self.root / "selection.json"
        selection.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        cfg = {"selection": {"sha256": sha, "path": "selection.json"}}
        marker = {"selection": {"path": str(selection), "sha256": sha}, "backend": "local_cuda",
            "kind": "verified_collection_ready_for_local_speech_recognition", "selected_count": 20, "creator_count": 1}
        frame = [{"video_id": "v", "channel_dir": "creator"}]
        snapshot = {"summary": {"latest20_target": 1, "audio_available": 0, "channels": 1, "remaining_audio": 1}, "selection_sha256": sha}
        with patch.object(schedule.collection_coverage, "coverage", return_value=(snapshot, [])), \
             patch.object(schedule.collection_coverage, "mixed_selection", return_value=(frame, {"creator": "short_complete_displayed_list"}, sha)), \
             self.assertRaisesRegex(ValueError, "verified audio"):
            schedule.collection_handoff(self.root, cfg, marker)
        self.assertFalse(schedule.terminal_ready({"status": "all_selected_audio_assessed", "backend": "local_cuda",
                         "selection": {"sha256":sha}, "verified_audio":1, "unprocessed": ["v"]}, cfg["selection"], 1))

    def test_rejects_unknown_evidence_keys_and_oversized_packet_before_reserving(self):
        for evidence in ({"bad id": 1}, {"E": "x"*agents.MAX_PACKET_BYTES}):
            with self.assertRaises(ValueError):
                agents.request_for("source-audit", evidence)
        self.assertFalse((self.parent/"budget.sqlite3").exists())

    def test_numerical_summary_is_bound_to_real_artifacts_and_source_generation(self):
        selection = {"sha256": "c"*64}
        artifact = self.root/"result.csv"
        artifact.write_text("n,mean\n1,0.5\n")
        proof = schedule.study_schedule.pin(self.root, artifact)
        entry = {"state":"complete","schema_version":1,"generation_manifest_sha256":"d"*64,
                 "selection_sha256":selection["sha256"],
                 "analyses":[{"method":k,"status":"measured","artifact":proof,"summary":{"n":1}}
                            for k in ("tfidf","cluster_sensitivity","passage_retrieval")]}
        self.assertEqual(len(schedule.numerical_evidence(self.root, entry, selection, {"sha256":"d"*64})), 3)
        with self.assertRaisesRegex(ValueError, "generation"):
            schedule.numerical_evidence(self.root, entry, selection, {"sha256":"a"*64})
        artifact.write_text("n,mean\n1,1.0\n")
        with self.assertRaisesRegex(ValueError, "changed"):
            schedule.numerical_evidence(self.root, entry, selection, {"sha256":"d"*64})

    def test_six_role_handoff_reuses_responses_and_shares_one_budget(self):
        state = self.root / "state"
        state.mkdir()
        selection = self.root / "selection.json"
        selection.write_bytes(b"test selection")
        proof = schedule.study_schedule.pin(self.root, selection)
        cfg = {"cap_usd": "100.00", "model": budget.MODEL, "asr_state": "state",
               "selection": proof, "credential_file": str(self.key), "rclone": "disabled-in-test"}
        schedule.save(self.parent / schedule.SETUP, cfg)
        schedule.save(state / "backend-ready.json", {"generation": "test"})
        summary = {"latest20_target": 1, "channels": 1, "audio_available": 1, "youtube_native_audio": 1,
                   "publisher_only_audio": 0, "qualified_youtube_only_audio": 0}
        snapshot = {"selection_sha256": proof["sha256"], "summary": summary}
        frame = [{"video_id": "v", "channel_dir": "test"}]
        generation = self.root / "generation"
        generation.mkdir()
        schedule.save(generation / "manifest.json", {"revision": "fixture"})
        schedule.save(generation / "view-inventory.json", [{"video_id": "v"}])
        sent = {}

        def sender(payload, key, dispatch):
            result = self.fake_response(payload, key, dispatch)
            result["id"] = "resp_" + dispatch
            sent[dispatch] = json.loads(payload)
            return result

        with ExitStack() as mocks:
            mocks.enter_context(patch.object(agents, "read_key", return_value="test"))
            mocks.enter_context(patch.object(agents, "api_submit", side_effect=sender))
            mocks.enter_context(patch.object(schedule, "collection_handoff", return_value=(snapshot, frame)))
            mocks.enter_context(patch.object(schedule.stage_archived_text, "stage"))
            mocks.enter_context(patch.object(schedule.postrun_candidates, "select_views", return_value={"v": [1]}))
            mocks.enter_context(patch.object(schedule.postrun_candidates, "run", return_value=generation))
            mocks.enter_context(patch.object(schedule.study_schedule, "validate_generation"))
            mocks.enter_context(patch.object(schedule.packets, "corpus_evidence", return_value={"SELECTION": 1, "CORPUS": 1}))
            for _ in range(2):
                self.assertEqual(schedule.tick(self.root)["state"], "methods_complete_waiting_for_local_transcription")
            self.assertEqual(len(sent), 2)
            schedule.save(state / "terminal.json", {"status": "all_selected_audio_assessed", "backend": "local_cuda",
                          "selection": proof, "verified_audio": 1, "unprocessed": []})
            for _ in range(2):
                self.assertEqual(schedule.tick(self.root)["state"], "waiting_for_local_numerical_analysis")
            self.assertEqual(len(sent), 2)
            manifest = schedule.study_schedule.pin(self.root, generation / "manifest.json")
            schedule.save(self.parent / "numerical-evidence.json", {"schema_version": 1, "state": "complete",
                          "selection_sha256": proof["sha256"], "generation_manifest_sha256": manifest["sha256"],
                          "analyses": [{"method": method, "status": "measured", "artifact": manifest, "summary": {"n": 1}}
                            for method in ("tfidf", "cluster_sensitivity", "passage_retrieval")]})
            for _ in range(2):
                self.assertEqual(schedule.tick(self.root)["state"], "corpus_panels_complete")
        self.assertEqual(len(sent), 6)
        self.assertEqual(sum("FIRST-claims-and-events" in json.loads(v["input"]) for v in sent.values()), 2)
        self.assertEqual(sum("NUMERICAL-tfidf" in json.loads(v["input"]) for v in sent.values()), 4)
        ledger = budget.BudgetLedger(self.parent / "budget.sqlite3").status()
        self.assertEqual(ledger["charged_micro_usd"], 6 * budget.usage_cost_micro_usd(self.usage))
        self.assertEqual(ledger["reserved_micro_usd"], 0)


if __name__ == "__main__":
    unittest.main()
