# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from risk_code_traceability.pipeline.pass_b_embeddings import EmbeddingMatcher


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
    FakeRisk(id="risk-pickle", name="Insecure Deserialization", description="Unpickling untrusted data can execute arbitrary code."),
    FakeRisk(id="risk-privacy", name="Data Privacy Leakage", description="Logging personal data exposes it to unauthorized readers."),
    FakeRisk(id="risk-bias", name="Algorithmic Bias", description="Model outputs systematically disadvantage a protected group."),
])


def test_score_candidates_respects_top_k():
    matcher = EmbeddingMatcher(NEXUS)
    artifact = {"id": "a1", "name": "log_user_input", "content_summary": "logs email and query text to a file"}
    results = matcher.score_candidates(artifact, candidate_risk_ids=[], top_k=1)
    assert len(results) <= 1


def test_scores_are_floats():
    matcher = EmbeddingMatcher(NEXUS)
    artifact = {"id": "a1", "name": "log_user_input", "content_summary": "logs email and query text to a file"}
    results = matcher.score_candidates(artifact, candidate_risk_ids=["risk-privacy"], top_k=2)
    assert results
    for _risk_id, score in results:
        assert isinstance(score, float)
