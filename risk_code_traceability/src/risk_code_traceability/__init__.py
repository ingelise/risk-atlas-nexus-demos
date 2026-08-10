# SPDX-License-Identifier: Apache-2.0
"""Risk-to-Code Traceability pipeline orchestrator."""
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from ai_atlas_nexus import AIAtlasNexus

from .graphify_adapter import load_graphify_graph
from .pipeline.pass_a_keywords import build_keyword_index, pass_a
from .pipeline.pass_b_embeddings import EmbeddingMatcher
from .pipeline.pass_c_llm import pass_c
from .store.loader import build_store

# Thresholds -- tune these for cost vs recall tradeoff
PASS_B_TOP_K = 5
PASS_C_MIN_SCORE = 0.45
CONFIRMED_THRESHOLD = 0.85
PROPOSED_THRESHOLD = 0.50


def run(
    graph_json_path: str | Path,
    output_ttl_path: str | Path | None = None,
    llm_model: str = "claude-sonnet-4-6",
    skip_pass_c: bool = False,
) -> dict:
    """
    Full pipeline: Graphify graph.json -> pyoxigraph RDF-star store.
    Returns {"store": ox.Store, "links": list[dict], "stats": dict}.
    """
    nexus = AIAtlasNexus()
    risks = {r.id: r for r in nexus.get_all_risks()}
    anthropic_client = anthropic.Anthropic() if not skip_pass_c else None

    print(f"[1/5] Loading Graphify graph from {graph_json_path}")
    artifacts = load_graphify_graph(graph_json_path)
    print(f"      {len(artifacts)} artifacts loaded")

    print("[2/5] Pass A -- keyword heuristics")
    kw_index = build_keyword_index(nexus)
    a_candidates = pass_a(artifacts, nexus, kw_index)
    print(f"      {len(a_candidates)} (artifact, risk) pairs shortlisted")

    print("[3/5] Pass B -- embedding similarity")
    matcher = EmbeddingMatcher(nexus)
    artifact_map = {a["id"]: a for a in artifacts}

    a_by_artifact: dict[str, list[str]] = {}
    for art_id, risk_id, _score in a_candidates:
        a_by_artifact.setdefault(art_id, []).append(risk_id)

    b_candidates: list[tuple[str, str, float]] = []
    for artifact in artifacts:
        prior_risk_ids = a_by_artifact.get(artifact["id"], [])
        scored = matcher.score_candidates(artifact, prior_risk_ids, top_k=PASS_B_TOP_K)
        for risk_id, score in scored:
            if score > 0.0:
                b_candidates.append((artifact["id"], risk_id, score))
    print(f"      {len(b_candidates)} pairs after embedding re-ranking")

    print("[4/5] Pass C -- LLM verification (top candidates only)")
    links: list[dict] = []
    llm_call_count = 0

    for art_id, risk_id, score in b_candidates:
        if score < PASS_C_MIN_SCORE or skip_pass_c:
            links.append({
                "artifact_id": art_id,
                "risk_id": risk_id,
                "confidence": score,
                "detection_method": "embedding",
                "rationale": "",
                "status": "proposed",
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "source_commit": artifact_map[art_id].get("source_commit", "unknown"),
            })
            continue

        risk = risks.get(risk_id)
        if not risk:
            continue

        result = pass_c(
            artifact=artifact_map[art_id],
            risk_name=risk.name,
            risk_description=risk.description or "",
            model=llm_model,
            client=anthropic_client,
        )
        llm_call_count += 1

        conf = result.get("confidence", 0.0)
        if conf < PROPOSED_THRESHOLD or not result.get("related", False):
            status = "rejected"
        elif conf >= CONFIRMED_THRESHOLD:
            status = "confirmed"
        else:
            status = "proposed"

        if status != "rejected":
            links.append({
                "artifact_id": art_id,
                "risk_id": risk_id,
                "confidence": conf,
                "detection_method": "llm",
                "rationale": result.get("rationale", ""),
                "status": status,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "source_commit": artifact_map[art_id].get("source_commit", "unknown"),
            })

    print(f"      {llm_call_count} LLM calls made; {len(links)} links retained")

    print("[5/5] Building pyoxigraph store")
    store = build_store(artifacts, links)

    if output_ttl_path:
        from .store.loader import serialize_store
        serialize_store(store, str(output_ttl_path))
        print(f"      Store serialized -> {output_ttl_path}")

    confirmed = sum(1 for l in links if l["status"] == "confirmed")
    proposed = sum(1 for l in links if l["status"] == "proposed")
    return {
        "store": store,
        "links": links,
        "stats": {
            "artifacts": len(artifacts),
            "pass_a_pairs": len(a_candidates),
            "pass_b_pairs": len(b_candidates),
            "llm_calls": llm_call_count,
            "links_confirmed": confirmed,
            "links_proposed": proposed,
        },
    }
