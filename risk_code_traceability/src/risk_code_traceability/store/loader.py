# SPDX-License-Identifier: Apache-2.0
"""
Load CodeArtifacts and RiskTraceabilityLinks into a pyoxigraph in-memory store.

RDF-star provenance model: this pyoxigraph version only allows a quoted
triple in *object* position (there is no subject-position `TripleSubject`),
so each link gets its own node rather than attaching predicates directly to
the base triple:

    graphify:link/<id>  graphify:asserts  <<( :artifact atlas:hasRelatedRisk :risk )>> ;
                        graphify:confidence  X ;
                        graphify:status      Y .

The plain `artifact hasRelatedRisk risk` triple is asserted separately for
every non-rejected link (confirmed and proposed alike), so it stays queryable
with plain SPARQL 1.1. That means status alone -- not the presence of the
plain triple -- distinguishes a reviewed "confirmed" link from an
unreviewed "proposed" one; a consumer reading only the plain triple cannot
tell them apart.
"""
from datetime import datetime, timezone

import pyoxigraph as ox

GRAPHIFY = "https://example.org/graphify-bridge/"
ATLAS = "https://ibm.github.io/ai-atlas-nexus/ontology/"
XSD = "http://www.w3.org/2001/XMLSchema#"

HAS_TYPE = ox.NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
HAS_RELATED_RISK = ox.NamedNode(f"{ATLAS}hasRelatedRisk")
CODE_ARTIFACT_CLASS = ox.NamedNode(f"{GRAPHIFY}CodeArtifact")
LINK_CLASS = ox.NamedNode(f"{GRAPHIFY}RiskTraceabilityLink")
ASSERTS = ox.NamedNode(f"{GRAPHIFY}asserts")


def _uri(ns: str, local: str) -> ox.NamedNode:
    return ox.NamedNode(f"{ns}{local}")


def _lit(val: str, datatype: str = f"{XSD}string") -> ox.Literal:
    return ox.Literal(val, datatype=ox.NamedNode(datatype))


def _artifact_node(artifact_id: str) -> ox.NamedNode:
    return _uri(GRAPHIFY, f"artifact/{artifact_id.replace('/', '_').replace('::', '_')}")


def _risk_node(risk_id: str) -> ox.NamedNode:
    return _uri(ATLAS, f"risk/{risk_id}")


def build_store(artifacts: list[dict], links: list[dict]) -> ox.Store:
    """
    artifacts: CodeArtifact dicts (from graphify_adapter).
    links: RiskTraceabilityLink dicts with artifact_id, risk_id, confidence,
           detection_method, rationale, status, extracted_at, source_commit.
    """
    store = ox.Store()

    for a in artifacts:
        subj = _artifact_node(a["id"])
        store.add(ox.Quad(subj, HAS_TYPE, CODE_ARTIFACT_CLASS))
        for slot, pred_local in [
            ("name", "name"),
            ("source_file", "sourceFile"),
            ("node_type", "nodeType"),
            ("content_hash", "contentHash"),
            ("content_summary", "contentSummary"),
            ("source_commit", "sourceCommit"),
        ]:
            if a.get(slot):
                store.add(ox.Quad(subj, _uri(GRAPHIFY, pred_local), _lit(str(a[slot]))))
        if a.get("community_id") is not None:
            store.add(ox.Quad(
                subj, _uri(GRAPHIFY, "communityId"),
                _lit(str(a["community_id"]), f"{XSD}integer"),
            ))

    for i, link in enumerate(links):
        if link.get("status") == "rejected":
            continue

        artifact_node = _artifact_node(link["artifact_id"])
        risk_node = _risk_node(link["risk_id"])
        base_triple = ox.Triple(artifact_node, HAS_RELATED_RISK, risk_node)
        store.add(ox.Quad(artifact_node, HAS_RELATED_RISK, risk_node))

        link_node = _uri(GRAPHIFY, f"link/{i}")
        store.add(ox.Quad(link_node, HAS_TYPE, LINK_CLASS))
        store.add(ox.Quad(link_node, ASSERTS, base_triple))

        for pred_local, val in [
            ("confidence", link["confidence"]),
            ("detectionMethod", link.get("detection_method", "")),
            ("rationale", link.get("rationale", "")),
            ("status", link.get("status", "proposed")),
            ("sourceCommit", link.get("source_commit", "")),
            ("extractedAt", link.get("extracted_at", datetime.now(timezone.utc).isoformat())),
        ]:
            if val == "" or val is None:
                continue
            datatype = f"{XSD}double" if pred_local == "confidence" else f"{XSD}string"
            store.add(ox.Quad(link_node, _uri(GRAPHIFY, pred_local), _lit(str(val), datatype)))

    return store


def serialize_store(store: ox.Store, path: str) -> None:
    """Persist the store to disk as Turtle for offline inspection."""
    with open(path, "wb") as f:
        store.dump(f, ox.RdfFormat.TURTLE, from_graph=ox.DefaultGraph())
