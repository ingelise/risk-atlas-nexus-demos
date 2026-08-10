# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from risk_code_traceability.pipeline.pass_a_keywords import build_keyword_index, pass_a


@dataclass
class FakeRisk:
    id: str
    name: str
    description: str = ""


class FakeNexus:
    def __init__(self, risks):
        self._risks = risks

    def get_all_risks(self):
        return self._risks


NEXUS = FakeNexus([
    FakeRisk(id="risk-pickle", name="Insecure Deserialization"),
    FakeRisk(id="risk-privacy", name="Data Privacy Leakage"),
])


def test_keyword_match_returns_matching_risk():
    artifacts = [{
        "id": "a1", "name": "load_model", "source_file": "src/inference.py",
        "content_summary": "deserialization of a pickle file",
    }]
    candidates = pass_a(artifacts, NEXUS)
    risk_ids = {risk_id for _artifact_id, risk_id, _score in candidates}
    assert "risk-pickle" in risk_ids


def test_no_match_returns_empty():
    artifacts = [{
        "id": "a2", "name": "add_numbers", "source_file": "src/math_utils.py",
        "content_summary": "returns the sum of two integers",
    }]
    assert pass_a(artifacts, NEXUS) == []


def test_score_bounded_between_zero_and_one():
    index = build_keyword_index(NEXUS)
    artifacts = [{
        "id": "a1", "name": "load_model", "source_file": "src/inference.py",
        "content_summary": "insecure deserialization of a pickle file",
    }]
    for _artifact_id, _risk_id, score in pass_a(artifacts, NEXUS, index):
        assert 0.0 < score <= 1.0
