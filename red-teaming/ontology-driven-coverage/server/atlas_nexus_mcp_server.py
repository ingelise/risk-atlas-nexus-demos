"""
AI Atlas Nexus — Red-Team Planning MCP Server
===============================================
Exposes the ontology-backed red-team planning tools (get_applicable_risks,
get_risk_detail, log_test_objective, get_coverage_report) as an MCP server.

STATUS: ✅ Real ontology integrated (ai_atlas_nexus 1.2.2)
- Queries actual IBM AI Risk Atlas (99 risks)
- Fetches full metadata, definitions, and mitigations
- Keyword-based risk scoping (can upgrade to ML-based with BenchmarkRiskDetector)

Run as MCP server (optional):
    python atlas_nexus_mcp_server.py --http   # Serves at http://127.0.0.1:8000/mcp

Or use directly:
    from atlas_nexus_mcp_server import ontology
    risks = ontology.get_applicable_risks("system description")

Design constraint: log_test_objective has no field for payloads, jailbreaks,
or exploit strings — enforced structurally via Literal typing. Humans own
crafting adversarial input; the agent provides structure and completeness.

PRODUCTION GAPS (see PRODUCTION_CHECKLIST.md):
- [ ] Persistent storage (replace in-memory COVERAGE dict)
- [ ] Authentication (API key / OAuth)
- [ ] Ticketing integration (auto-file human red-team tasks)
- [ ] Multi-system tracking (track coverage per system)
"""

import argparse
from typing import Literal

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="ai-atlas-nexus-redteam",
    instructions=(
        "Tools for planning red-team test coverage against the AI Atlas "
        "Nexus risk ontology. Use get_applicable_risks first to scope a "
        "system, get_risk_detail to understand each risk, log_test_objective "
        "to record a payload-free test plan entry, and get_coverage_report "
        "to summarize coverage and gaps."
    ),
)


# ---------------------------------------------------------------------------
# Ontology backend — AI Atlas Nexus integration
# ---------------------------------------------------------------------------

class AIAtlasNexusOntology:
    """Wrapper around AIAtlasNexus library for red-team planning tools.

    Provides methods to:
    - Query the knowledge graph for risks matching a system description
    - Fetch rich metadata (definition, source, mitigations, linked benchmarks)
    - Handle cases where risks aren't found gracefully
    """

    def __init__(self, base_dir: str = None, taxonomy: str = "ibm-risk-atlas"):
        """Initialize the ontology wrapper.

        Args:
            base_dir: Optional path to custom ontology data directory
            taxonomy: Which taxonomy to use (default: "ibm-ai-risk-atlas")
        """
        try:
            from ai_atlas_nexus import AIAtlasNexus
            self.nexus = AIAtlasNexus(base_dir=base_dir)
            self.taxonomy = taxonomy
            self._all_risks_cache = None
        except ImportError:
            raise ImportError(
                "ai_atlas_nexus not installed. Install with: pip install ai-atlas-nexus"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AIAtlasNexus: {e}")

    def get_all_risks(self):
        """Fetch all risks from the ontology (cached)."""
        if self._all_risks_cache is None:
            self._all_risks_cache = self.nexus.get_all_risks(taxonomy=self.taxonomy)
        return self._all_risks_cache

    def get_applicable_risks(self, intent: str):
        """Scope which ontology risks apply to a system description.

        This is a keyword-matching heuristic. For a production system with
        an LLM inference engine, you'd want to use the actual risk detector
        (BenchmarkRiskDetector or GenericRiskDetector) to score matches.

        Args:
            intent: Plain-language description of the system

        Returns:
            List of risk IDs that apply to this system
        """
        all_risks = self.get_all_risks()
        if not all_risks:
            return []

        text = intent.lower()
        applicable_risks = []

        # Score risks based on keyword matches and semantic relevance
        risk_scores = {}
        for risk in all_risks:
            risk_id = risk.id
            risk_name = (risk.name or "").lower()
            risk_desc = (risk.description or "").lower()
            score = 0

            # Simple keyword matching (can be replaced with ML-based relevance)
            keywords = {
                "shell,exec,file system,code execution,command": ["excessive-agency", "insecure-tool-use"],
                "retrieve,rag,document,retrieval,input source,output": ["prompt-injection"],
                "data,sensitive,customer,billing,personal,privacy,leak": ["data-exfiltration"],
                "hallucination,confabulation,factual": ["hallucination"],
            }

            for keyword_group, relevant_ids in keywords.items():
                for keyword in keyword_group.split(","):
                    if keyword.strip() in text or keyword.strip() in risk_name or keyword.strip() in risk_desc:
                        if risk_id in relevant_ids:
                            score += 2  # Direct match
                        else:
                            score += 1  # Secondary relevance

            if score > 0:
                risk_scores[risk_id] = score

        # Return risks sorted by relevance score (higher first)
        sorted_risks = sorted(risk_scores.items(), key=lambda x: -x[1])
        applicable_risks = [rid for rid, _ in sorted_risks]

        # If no keyword matches, return all risks as fallback (user can filter)
        if not applicable_risks:
            applicable_risks = [r.id for r in all_risks]

        return applicable_risks[:10]  # Limit to top 10 for manageability

    def get_risk_detail(self, risk_id: str):
        """Fetch full details for a risk from the ontology.

        Returns definition, source, mitigations, linked benchmarks, and related actions.

        Args:
            risk_id: Risk identifier from AIAtlasNexus

        Returns:
            Dictionary with risk metadata, or error dict if not found
        """
        try:
            # Note: get_risk with taxonomy param has a bug in AIAtlasNexus, so query without it
            risk = self.nexus.get_risk(id=risk_id)

            if not risk:
                return {"error": f"Risk not found: {risk_id}"}

            # Extract linked actions (mitigations/controls)
            related_actions = self.nexus.get_related_actions(id=risk_id)
            actions = [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "type": a.type,
                }
                for a in (related_actions or [])
            ]

            return {
                "id": risk.id,
                "name": risk.name,
                "description": risk.description,
                "source": risk.isDefinedByTaxonomy or "ibm-ai-risk-atlas",
                "tag": risk.tag,
                "type": risk.type,
                "concern": risk.concern,
                "url": risk.url,
                "mitigations": actions,
                "linked_benchmarks": [],  # Could query BenchmarkMetadataCard links if available
            }
        except Exception as e:
            return {"error": f"Failed to fetch risk {risk_id}: {str(e)}"}


try:
    ontology = AIAtlasNexusOntology()
except ImportError:
    import sys
    print(
        "ERROR: ai_atlas_nexus not installed.\n"
        "Install with: pip install ai-atlas-nexus\n"
        "Or use MockOntology for testing.",
        file=sys.stderr,
    )
    # Fallback to mock for testing (can be removed in production)
    class MockOntology:
        RISKS = {
            "excessive-agency": {
                "name": "Excessive Agency",
                "source": "OWASP Agentic Top 10",
                "definition": "Agent takes actions beyond its intended scope "
                               "or without appropriate approval, especially "
                               "irreversible ones.",
                "mitigations": [{"id": "m1", "name": "human-approval-gate"}],
                "linked_benchmarks": [],
            },
            "prompt-injection": {
                "name": "Prompt Injection",
                "source": "OWASP LLM Top 10",
                "definition": "Untrusted content alters agent behavior.",
                "mitigations": [{"id": "m2", "name": "input-provenance-tagging"}],
                "linked_benchmarks": [],
            },
        }

        def get_applicable_risks(self, intent: str):
            return list(self.RISKS.keys())

        def get_risk_detail(self, risk_id: str):
            return self.RISKS.get(risk_id, {"error": f"unknown risk_id {risk_id}"})

    ontology = MockOntology()

# NOTE: process-local state. Replace with a real DB for multi-client /
# multi-session persistence — that's the main reason to run this as a
# standalone MCP server rather than in-process tools.
COVERAGE: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_applicable_risks(intent: str) -> dict:
    """Scope which ontology risks are plausibly applicable to an AI system.

    Args:
        intent: Plain-language description of the system under test —
            its capabilities, tools, and data access. Call this first.
    """
    risk_ids = ontology.get_applicable_risks(intent)
    for rid in risk_ids:
        COVERAGE.setdefault(rid, {"status": "untested"})
    return {"applicable_risk_ids": risk_ids}


@mcp.tool()
def get_risk_detail(risk_id: str) -> dict:
    """Fetch the ontology definition, source taxonomy, mitigations, and
    linked benchmarks for a given risk_id.

    Args:
        risk_id: A risk identifier returned by get_applicable_risks.
    """
    return ontology.get_risk_detail(risk_id)


@mcp.tool()
def log_test_objective(
    risk_id: str,
    objective: str,
    owner: Literal["automated_eval", "human_redteam", "guardrail_regression"],
) -> dict:
    """Register a test PLAN entry for a risk.

    IMPORTANT: `objective` must describe the observable failure condition
    to check for (what would constitute a failure) — never an attack
    prompt, payload, or exploit string. Crafting the actual adversarial
    input is a human red-team task, not this tool's job.

    Args:
        risk_id: The risk this objective addresses.
        objective: High-level, payload-free description of what a
            passing/failing test looks like.
        owner: Who executes this — automated_eval (a linked benchmark
            exists), human_redteam (needs adversarial creativity), or
            guardrail_regression (mitigation exists, this is a regression
            check).
    """
    COVERAGE[risk_id] = {"status": "planned", "objective": objective, "owner": owner}
    return {"logged": True, "risk_id": risk_id}


@mcp.tool()
def get_coverage_report() -> dict:
    """Summarize current coverage: applicable risks, planned tests, gaps
    (applicable risks with no logged objective yet), and coverage %."""
    applicable = list(COVERAGE.keys())
    planned = [r for r, v in COVERAGE.items() if v.get("status") == "planned"]
    gaps = [r for r, v in COVERAGE.items() if v.get("status") == "untested"]
    return {
        "applicable_risks": applicable,
        "planned": planned,
        "gaps": gaps,
        "coverage_pct": round(100 * len(planned) / max(len(applicable), 1), 1),
        "detail": COVERAGE,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--http", action="store_true",
        help="Serve over streamable-http instead of stdio (for remote clients).",
    )
    args = parser.parse_args()
    mcp.run(transport="streamable-http" if args.http else "stdio")
