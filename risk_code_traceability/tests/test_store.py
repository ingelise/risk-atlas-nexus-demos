# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pyoxigraph as ox
import pytest

from risk_code_traceability.graphify_adapter import load_graphify_graph
from risk_code_traceability.store.loader import ATLAS, GRAPHIFY, build_store
from risk_code_traceability.store.queries import high_confidence_proposed, risks_by_file

DATA = Path(__file__).parent.parent / "data" / "sample_graph.json"

LINKS = [
    {"artifact_id": "src/inference.py::load_model", "risk_id": "risk-confirmed",
     "confidence": 0.95, "detection_method": "llm", "rationale": "clearly related",
     "status": "confirmed", "source_commit": "abc123"},
    {"artifact_id": "src/inference.py::load_model", "risk_id": "risk-proposed",
     "confidence": 0.8, "detection_method": "llm", "rationale": "possibly related",
     "status": "proposed", "source_commit": "abc123"},
    {"artifact_id": "src/inference.py::load_model", "risk_id": "risk-rejected",
     "confidence": 0.9, "detection_method": "llm", "rationale": "not actually related",
     "status": "rejected", "source_commit": "abc123"},
]


@pytest.fixture
def store():
    artifacts = load_graphify_graph(DATA)
    return build_store(artifacts, LINKS)


def test_confirmed_link_appears_in_risks_by_file(store):
    results = risks_by_file(store, "src/inference.py")
    statuses_by_risk = {r["riskId"].strip('"').rsplit("/", 1)[-1]: r["status"].strip('"') for r in results}
    assert statuses_by_risk.get("risk-confirmed") == "confirmed"


def test_rejected_link_absent_from_plain_and_quoted_triples(store):
    results = risks_by_file(store, "src/inference.py")
    risk_ids = {r["riskId"].strip('"').rsplit("/", 1)[-1] for r in results}
    assert "risk-rejected" not in risk_ids

    plain_triple = ox.Quad(
        ox.NamedNode(f"{GRAPHIFY}artifact/src_inference.py_load_model"),
        ox.NamedNode(f"{ATLAS}hasRelatedRisk"),
        ox.NamedNode(f"{ATLAS}risk/risk-rejected"),
    )
    assert plain_triple not in store


def test_proposed_link_plain_triple_present_but_only_status_distinguishes_it(store):
    results = risks_by_file(store, "src/inference.py")
    by_risk = {r["riskId"].strip('"').rsplit("/", 1)[-1]: r for r in results}

    assert "risk-proposed" in by_risk
    assert by_risk["risk-proposed"]["status"].strip('"') == "proposed"

    plain_triple = ox.Quad(
        ox.NamedNode(f"{GRAPHIFY}artifact/src_inference.py_load_model"),
        ox.NamedNode(f"{ATLAS}hasRelatedRisk"),
        ox.NamedNode(f"{ATLAS}risk/risk-proposed"),
    )
    assert plain_triple in store


def test_high_confidence_proposed_excludes_already_confirmed_links(store):
    results = high_confidence_proposed(store, threshold=0.5)
    risk_ids = {r["riskId"].strip('"').rsplit("/", 1)[-1] for r in results}
    assert "risk-proposed" in risk_ids
    assert "risk-confirmed" not in risk_ids


def test_rdf_star_provenance_triples_exist(store):
    results = risks_by_file(store, "src/inference.py")
    assert any(r["confidence"].strip('"').startswith("0.95") for r in results)
    assert all("status" in r for r in results)
