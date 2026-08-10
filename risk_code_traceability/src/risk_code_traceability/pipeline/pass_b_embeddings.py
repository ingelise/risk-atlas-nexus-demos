# SPDX-License-Identifier: Apache-2.0
"""
Pass B: embedding similarity re-ranking.

Takes Pass A candidates and scores them with txtai cosine similarity;
also surfaces top-K risks Pass A missed entirely.
"""
from txtai.embeddings import Embeddings

from ai_atlas_nexus import AIAtlasNexus


class EmbeddingMatcher:
    def __init__(self, nexus: AIAtlasNexus, model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embeddings = Embeddings({"path": model, "content": False})
        risks = nexus.get_all_risks()
        self.risk_ids = [r.id for r in risks]
        documents = [
            (i, f"{r.name}. {r.description or ''} {getattr(r, 'concern', '') or ''}", None)
            for i, r in enumerate(risks)
        ]
        self.embeddings.index(documents)

    def score_candidates(
        self,
        artifact: dict,
        candidate_risk_ids: list[str],
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """Returns (risk_id, similarity_score) for the union of prior candidates and top_k discovered."""
        query = f"{artifact['name']}. {artifact.get('content_summary', '')}"
        results = self.embeddings.search(query, limit=top_k + len(candidate_risk_ids))

        scored = {self.risk_ids[idx]: score for idx, score in results}
        all_risk_ids = set(candidate_risk_ids) | set(scored.keys())
        return [(risk_id, scored.get(risk_id, 0.0)) for risk_id in all_risk_ids]
