#!/usr/bin/env python3
"""Build the public, dated Atlas relationship extension without changing its baseline.

Run: python et-channelers/pipeline/atlas_entities.py
Only explicitly parent-reviewed research rows are publishable. No media, private
catalog, credentials, or generated transcript content is read by this module.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import ipaddress
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

REPO = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPO / "et-channelers/research/analysis-plan-2026-11-16/discovery-relationships.csv"
DEFAULT_OUTPUT = REPO / "channeling-atlas/dist/entity-relationships.json"
EDITION_DATE = "2026-11-17"
REVIEW_STATE = "parent_primary_source_reviewed"
PREDICATES = {
    "claims_channeling": "Claims channeling",
    "claims_series_channeling": "Claims channeling in an event series",
    "claims_channeling_codes": "Attributes channeled codes to",
    "claims_channeling_light_language": "Attributes light language to",
    "reports_contact_with": "Reports contact with",
    "reports_guidance_from": "Reports guidance from",
    "reports_guide_association": "Names as a guide",
}
# Reviewed human matches only. A collection/channel/guest name is not a profile ID.
PROFILE_LINKS = {"daniel-scranton": "lk-daniel", "rob-gauthier": "lk-rob", "lyssa-royal-holt": "lk-lyssa"}


def clean(value, *, limit=4000):
    if not isinstance(value, str) or len(value) > limit or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value):
        raise ValueError("Invalid public text field")
    return value.strip()


def identifier(value):
    value = clean(value, limit=160)
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", value):
        raise ValueError("Invalid public record identifier")
    return value


def public_url(value):
    value = clean(value, limit=2000)
    parts = urlsplit(value)
    if parts.scheme not in {"https", "http"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("Source must be a public HTTP(S) URL without credentials")
    host = parts.hostname.lower()
    if host == "localhost" or host.endswith((".localhost", ".local")):
        raise ValueError("Local source URL is not publishable")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Private source URL is not publishable")
    if any(re.search(r"token|secret|password|signature|authorization|api.?key|credential", key, re.I)
           for key, _ in parse_qsl(parts.query)):
        raise ValueError("Credential-bearing source URL is not publishable")
    return value


def build_projection(source_bytes, *, edition_date=EDITION_DATE, atlas_profiles=()):
    date.fromisoformat(edition_date)
    # Git checkouts can use LF or CRLF. Hash the documented canonical UTF-8/LF
    # source so the same reviewed table rebuilds identically on Windows/Linux.
    source_bytes = source_bytes.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    rows = list(csv.DictReader(io.StringIO(source_bytes.decode("utf-8"))))
    people, labels, relationships = {}, {}, []
    profile_ids = {profile["id"] for profile in atlas_profiles}
    seen = set()
    for row in rows:
        if row.get("source_review_state") != REVIEW_STATE:
            raise ValueError("Every public relationship requires parent primary-source review")
        record_id = identifier(row["claim_instance_id"])
        if record_id in seen:
            raise ValueError("Duplicate relationship record ID")
        seen.add(record_id)
        person_id, entity_id = identifier(row["person_id"]), identifier(row["entity_concept_id"])
        relation_type = row["relationship_type"]
        if relation_type not in PREDICATES:
            raise ValueError("Unknown relationship predicate")
        expected_role = "contactee" if relation_type.startswith("reports_") else "channeler"
        if row["role"] != expected_role:
            raise ValueError("Relationship predicate and human role disagree")
        person_name, entity_name = clean(row["person_name"]), clean(row["claimed_entity"])
        if not person_name or not entity_name:
            raise ValueError("Public relationships require human and source labels")
        person = people.setdefault(person_id, {"id": person_id, "name": person_name, "collectionIds": [], "channels": []})
        if person["name"] != person_name:
            raise ValueError("Conflicting human names require an explicit identity review")
        collection = row.get("collection_id", "")
        if collection and identifier(collection) not in person["collectionIds"]:
            person["collectionIds"].append(collection)
        mapped = PROFILE_LINKS.get(person_id)
        if mapped and mapped in profile_ids:
            person["atlasProfileId"] = mapped
        if row.get("channel_ownership_verified") == "true":
            channel = {"url": public_url(row["channel_url"]), "evidenceUrl": public_url(row["ownership_source_url"]),
                       "basis": clean(row["ownership_evidence"])}
            if channel not in person["channels"]:
                person["channels"].append(channel)
        label = labels.setdefault(entity_id, {"id": entity_id, "aliases": [], "categories": [], "comparisonFamilies": []})
        for key, value in (("aliases", entity_name), ("categories", clean(row["entity_category"])),
                           ("comparisonFamilies", clean(row["comparison_family"]))):
            if value and value not in label[key]:
                label[key].append(value)
        relationships.append({
            "id": record_id, "personId": person_id, "entityId": entity_id, "entityLabel": entity_name,
            "relationshipType": relation_type, "predicate": PREDICATES[relation_type], "role": expected_role,
            "evidence": {"url": public_url(row["source_url"]), "section": clean(row["source_section"]),
                         "summary": clean(row["evidence_paraphrase"]), "qualification": clean(row.get("notes", ""))},
            "capturedAt": clean(row["retrieved_at"], limit=40), "reviewState": REVIEW_STATE,
        })
    for person in people.values():
        person["collectionIds"].sort()
        person["channels"].sort(key=lambda item: (item["url"], item["evidenceUrl"]))
    for label in labels.values():
        for key in ("aliases", "categories", "comparisonFamilies"):
            label[key].sort(key=str.casefold)
        label["name"] = label["aliases"][0]
    relationships.sort(key=lambda item: item["id"])
    return {
        "schemaVersion": 1,
        "meta": {"editionDate": edition_date, "sourceSha256": hashlib.sha256(source_bytes).hexdigest(),
                 "sourceCanonicalization": "utf8-lf-v1",
                 "source": "discovery-relationships.csv", "relationshipCount": len(relationships),
                 "peopleCount": len(people), "labelCount": len(labels),
                 "scope": "Dated primary-source relationship extension; historical Atlas and analysis denominators are unchanged.",
                 "unit": "One human–claimed source–predicate–supporting page relationship. Labels compare claims, not verified external identities."},
        "predicates": PREDICATES,
        "people": sorted(people.values(), key=lambda item: (item["name"].casefold(), item["id"])),
        "labels": sorted(labels.values(), key=lambda item: (item["name"].casefold(), item["id"])),
        "relationships": relationships,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--atlas", type=Path, default=REPO / "channeling-atlas/dist/data.json")
    parser.add_argument("--edition-date", default=EDITION_DATE)
    args = parser.parse_args(argv)
    atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
    result = build_projection(args.source.read_bytes(), edition_date=args.edition_date, atlas_profiles=atlas["profiles"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["meta"], ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
