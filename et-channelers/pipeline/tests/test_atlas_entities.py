"""Public relationship projection: attribution, reproducibility and publication boundary."""
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atlas_entities as atlas


def row(**extra):
    result = dict(claim_instance_id="claim-example", person_id="pia-orleane", person_name="Pia Orleane",
                  collection_id="laarkmaa", role="channeler", entity_concept_id="quantamo-pia-orleane",
                  claimed_entity="Quantamo", entity_category="et_being", comparison_family="arcturian",
                  relationship_type="claims_channeling", source_url="https://example.com/source",
                  source_section="Source list", evidence_paraphrase="The practitioner attributes the communication to Quantamo.",
                  profile_verified="true", channel_ownership_verified="false", channel_url="", ownership_source_url="",
                  ownership_evidence="", existing_new="existing", source_review_state=atlas.REVIEW_STATE,
                  retrieved_at="2026-11-17T00:06:42Z", evidence_round="2", notes="Pia-only attribution.")
    result.update(extra)
    return result


def encoded(rows):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=sorted(set().union(*(r.keys() for r in rows))))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


class AtlasEntitiesTests(unittest.TestCase):
    def test_projection_is_identical_for_lf_crlf_and_utf8_bom_checkouts(self):
        crlf = encoded([row()])
        lf = crlf.replace(b'\r\n', b'\n')
        expected = atlas.build_projection(lf)
        self.assertEqual(expected, atlas.build_projection(crlf))
        self.assertEqual(expected, atlas.build_projection(b'\xef\xbb\xbf' + crlf))
        self.assertEqual(expected['meta']['sourceCanonicalization'], 'utf8-lf-v1')

    def test_projection_is_deterministic_and_only_explicit_public_fields_survive(self):
        source = encoded([row(private_path="PRIVATE", token="SECRET", transcript="FULL TRANSCRIPT")])
        result = atlas.build_projection(source)
        self.assertEqual(result, atlas.build_projection(source))
        text = json.dumps(result)
        for hidden in ("PRIVATE", "SECRET", "FULL TRANSCRIPT", "private_path", "transcript"):
            self.assertNotIn(hidden, text)
        self.assertEqual(result["relationships"][0]["evidence"]["url"], "https://example.com/source")
        self.assertEqual(result["meta"]["relationshipCount"], 1)

    def test_shared_collection_does_not_transfer_person_specific_relationship(self):
        result = atlas.build_projection(encoded([row(), row(claim_instance_id="claim-joint", person_id="cullen-baird-smith",
            person_name="Cullen Baird Smith", entity_concept_id="laarkmaa-pia-cullen", claimed_entity="Laarkmaa")]))
        self.assertEqual(len(result["people"]), 2)
        self.assertEqual([r["personId"] for r in result["relationships"] if r["entityLabel"] == "Quantamo"], ["pia-orleane"])
        self.assertTrue(all(p["collectionIds"] == ["laarkmaa"] for p in result["people"]))

    def test_contact_remains_contact_and_labels_are_not_merged_by_comparison_family(self):
        result = atlas.build_projection(encoded([row(), row(claim_instance_id="claim-contact", person_id="second-person",
            person_name="Second Person", entity_concept_id="council-second", claimed_entity="A Council",
            role="contactee", relationship_type="reports_contact_with")]))
        self.assertEqual(len(result["labels"]), 2)
        contact = next(r for r in result["relationships"] if r["id"] == "claim-contact")
        self.assertEqual(contact["predicate"], "Reports contact with")
        self.assertEqual(contact["role"], "contactee")

    def test_no_guessed_profile_or_unverified_channel_links(self):
        result = atlas.build_projection(encoded([row(channel_url="https://youtube.com/@guest-host")]),
                                        atlas_profiles=[{"id": "laarkmaa"}])
        self.assertNotIn("atlasProfileId", result["people"][0])
        self.assertEqual(result["people"][0]["channels"], [])
        known = atlas.build_projection(encoded([row(person_id="daniel-scranton", person_name="Daniel Scranton")]),
                                       atlas_profiles=[{"id": "lk-daniel"}])
        self.assertEqual(known["people"][0]["atlasProfileId"], "lk-daniel")

    def test_roxanne_reuses_separate_existing_profile_and_discovery_person(self):
        source = encoded([row(person_id="roxanne-swainhart", person_name="Roxanne Swainhart")])
        result = atlas.build_projection(source, atlas_profiles=[{"id": "em-roxanne"}],
                                        atlas_people=[{"id": "person-05fde1a08a4e"}])
        person = result["people"][0]
        self.assertEqual(person["atlasProfileId"], "em-roxanne")
        self.assertEqual(person["discoveryPersonId"], "person-05fde1a08a4e")
        absent = atlas.build_projection(source)["people"][0]
        self.assertNotIn("atlasProfileId", absent)
        self.assertNotIn("discoveryPersonId", absent)

    def test_unreviewed_duplicate_and_inconsistent_roles_fail_publication(self):
        for rows in ([row(source_review_state="agent_primary_source_reviewed_parent_pending")], [row(), row()],
                     [row(role="interview_host")], [row(relationship_type="same_external_entity")]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                atlas.build_projection(encoded(rows))

    def test_source_and_ownership_urls_reject_credentials_local_paths_and_schemes(self):
        for value in ("javascript:alert(1)", "file:///private", "https://user:secret@example.com/", "http://localhost/",
                      "http://127.0.0.1/", "https://example.com/?access_token=secret"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                atlas.build_projection(encoded([row(source_url=value)]))
            with self.subTest(ownership=value), self.assertRaises(ValueError):
                atlas.build_projection(encoded([row(channel_ownership_verified="true", channel_url=value,
                    ownership_source_url="https://example.com/about", ownership_evidence="An explicit own-channel link.")]))

    def test_repository_projection_matches_reviewed_snapshot_without_mutating_baseline(self):
        original = (atlas.REPO / "channeling-atlas/dist/data.json").read_bytes()
        baseline = json.loads(original)
        result = atlas.build_projection(atlas.DEFAULT_SOURCE.read_bytes(), atlas_profiles=baseline["profiles"],
                                        atlas_people=baseline.get("discovery", {}).get("people", []))
        self.assertEqual(result, json.loads(atlas.DEFAULT_OUTPUT.read_text(encoding="utf-8")))
        self.assertEqual(original, (atlas.REPO / "channeling-atlas/dist/data.json").read_bytes())
        self.assertEqual(len(result["relationships"]), len({r["id"] for r in result["relationships"]}))
        self.assertNotIn("multidimensional-soul", {r["personId"] for r in result["relationships"]})

    def test_intake_preserves_prior_rows_and_does_not_promote_pending_video_or_ownership(self):
        research = atlas.REPO / "et-channelers/research"
        audit = json.loads((research / "intake-three-channels-source-review.json").read_text(encoding="utf-8"))
        text = atlas.DEFAULT_SOURCE.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        # The accepted snapshot contains no multiline CSV fields; preserve its
        # header and all 115 existing records, rather than reserializing them.
        prior = "".join(text.splitlines(keepends=True)[:116]).encode("utf-8")
        self.assertEqual(hashlib.sha256(prior).hexdigest(), audit["prior_source_sha256_utf8_lf"])
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual({r["claim_instance_id"] for r in rows[115:119]},
                         {r["claim_instance_id"] for r in audit["accepted_records"]})
        self.assertFalse(any(r["person_id"] == "roxanne-swainhart" and r["claimed_entity"] == "Bashar" for r in rows))
        projection = atlas.build_projection(atlas.DEFAULT_SOURCE.read_bytes())
        ayako = next(p for p in projection["people"] if p["id"] == "ayako-sekino")
        self.assertEqual(ayako["channels"], [])
        claim = next(r for r in projection["relationships"] if r["personId"] == "ayako-sekino")
        self.assertIn("Historical self-report", claim["evidence"]["qualification"])
        proposed = list(csv.DictReader(io.StringIO(
            (research / "intake-three-channels-relationships-proposed.csv").read_text(encoding="utf-8"))))
        pending = [r for r in proposed if r["video_id"] == "Rcemlb-WPPY"]
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["source_review_state"], "pending_performer_evidence")

    def test_episode_credits_identify_host_guest_and_written_evidence(self):
        rows = list(csv.DictReader(io.StringIO(atlas.DEFAULT_SOURCE.read_text(encoding="utf-8"))))
        new = [r for r in rows if r["evidence_round"] == "publisher_episode_review"]
        self.assertEqual(len(new), 9)
        episode = [r for r in new if r["source_section"].endswith("episode 143")]
        self.assertEqual({(r["person_name"], r["claimed_entity"]) for r in episode},
                         {("Rachel Chamness", "AnaOmbre"), ("Caitlin de León", "Vera Light")})
        guests = [r for r in new if r["existing_new"] == "guest"]
        self.assertTrue(all(not r["channel_url"] and not r["collection_id"] for r in guests))
        self.assertEqual({r["claimed_entity"] for r in new if r["relationship_type"] == "attributes_written_message"},
                         {"St. Germain", "Ashanti", "The Creators"})


if __name__ == "__main__":
    unittest.main()
