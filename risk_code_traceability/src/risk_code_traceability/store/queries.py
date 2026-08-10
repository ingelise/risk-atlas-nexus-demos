# SPDX-License-Identifier: Apache-2.0
"""
SPARQL-star query helpers for risk traceability exploration.

Quoted-triple patterns use this pyoxigraph version's `<<( s p o )>>` syntax
(parens required) rather than the plain `<< s p o >>` form.
"""
import pyoxigraph as ox

PREFIXES = """
PREFIX graphify: <https://example.org/graphify-bridge/>
PREFIX atlas:    <https://ibm.github.io/ai-atlas-nexus/ontology/>
"""


def risks_by_file(store: ox.Store, source_file: str) -> list[dict]:
    """All risks linked to a given source file path."""
    q = PREFIXES + f"""
    SELECT ?artifact ?riskId ?confidence ?method ?status WHERE {{
        ?artifact graphify:sourceFile "{source_file}" .
        ?link graphify:asserts <<( ?artifact atlas:hasRelatedRisk ?risk )>> ;
              graphify:confidence      ?confidence ;
              graphify:detectionMethod ?method ;
              graphify:status          ?status .
        BIND(STR(?risk) AS ?riskId)
    }}
    ORDER BY DESC(?confidence)
    """
    return _to_dicts(store.query(q))


def artifacts_by_risk(store: ox.Store, risk_id: str) -> list[dict]:
    """All code artifacts linked to a given risk id."""
    risk_uri = f"<https://ibm.github.io/ai-atlas-nexus/ontology/risk/{risk_id}>"
    q = PREFIXES + f"""
    SELECT ?artifact ?sourceFile ?confidence ?status WHERE {{
        ?link graphify:asserts <<( ?artifact atlas:hasRelatedRisk {risk_uri} )>> ;
              graphify:confidence ?confidence ;
              graphify:status     ?status .
        ?artifact graphify:sourceFile ?sourceFile .
    }}
    ORDER BY DESC(?confidence)
    """
    return _to_dicts(store.query(q))


def high_confidence_proposed(store: ox.Store, threshold: float = 0.7) -> list[dict]:
    """Links above threshold that are still proposed (need human review)."""
    q = PREFIXES + f"""
    SELECT ?artifact ?riskId ?confidence ?rationale WHERE {{
        ?link graphify:asserts <<( ?artifact atlas:hasRelatedRisk ?risk )>> ;
              graphify:confidence ?confidence ;
              graphify:status     "proposed" ;
              graphify:rationale  ?rationale .
        FILTER(?confidence >= {threshold})
        BIND(STR(?risk) AS ?riskId)
    }}
    ORDER BY DESC(?confidence)
    """
    return _to_dicts(store.query(q))


def community_risk_heatmap(store: ox.Store) -> list[dict]:
    """Count confirmed risk links per Graphify community."""
    q = PREFIXES + """
    SELECT ?communityId (COUNT(?risk) AS ?linkCount) WHERE {
        ?artifact graphify:communityId ?communityId .
        ?link graphify:asserts <<( ?artifact atlas:hasRelatedRisk ?risk )>> ;
              graphify:status "confirmed" .
    }
    GROUP BY ?communityId
    ORDER BY DESC(?linkCount)
    """
    return _to_dicts(store.query(q))


def _to_dicts(result) -> list[dict]:
    return [
        {var.value: str(row[var]) for var in result.variables}
        for row in result
    ]
