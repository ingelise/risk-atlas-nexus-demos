"""
Integration Example: Multi-System Red-Team Planning
=====================================================

Demonstrates how to use the red-team planning agent across multiple systems,
track coverage by system, and generate a governance report.

Run this after the MCP server is up (python ../server/atlas_nexus_mcp_server.py --http)
"""

from anthropic import Anthropic
import json

client = Anthropic()
MODEL = "claude-opus-4-8"

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"

SYSTEM_PROMPT = """You are a red-team planning agent. Your job is to build \
a test-coverage plan for an AI system using the AI Atlas Nexus risk \
ontology, not to invent attacks yourself.

Process:
1. Call get_applicable_risks with the system description to scope relevant risks.
2. For each applicable risk_id, call get_risk_detail to understand it.
3. For each, call log_test_objective with a clear, payload-free failure \
   condition and an appropriate owner.
4. Call get_coverage_report and present a final summary."""

# Example systems to plan red-teaming for
SYSTEMS = [
    {
        "name": "Code Assistant with Shell Access",
        "description": "An agentic coding assistant with shell access and file system read/write, "
                      "no human approval gate before executing commands, used internally by "
                      "engineers with access to customer billing repos."
    },
    {
        "name": "Document Retrieval Chatbot",
        "description": "A retrieval-augmented generation (RAG) chatbot that searches company "
                      "knowledge base documents and retrieves customer data, no rate limiting on "
                      "document access."
    },
    {
        "name": "Financial Analysis Agent",
        "description": "An agent that analyzes financial data, makes predictions, and generates reports "
                      "for traders, with access to market data APIs and trading system connections."
    },
]


def plan_for_system(system_name: str, system_description: str) -> dict:
    """Run red-team planning for one system."""
    print(f"\n{'='*70}")
    print(f"Planning red-team coverage for: {system_name}")
    print(f"{'='*70}\n")

    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": system_description}],
        mcp_servers=[
            {
                "type": "url",
                "url": MCP_SERVER_URL,
                "name": "atlas-nexus-redteam",
            }
        ],
        extra_headers={"anthropic-beta": "mcp-client-2025-04-04"},
    )

    # Extract and display the agent's reasoning
    for block in response.content:
        if block.type == "text":
            print(f"[agent] {block.text}")
        elif block.type == "mcp_tool_use":
            print(f"[tool_call] {block.name}(...)")
        elif block.type == "mcp_tool_result":
            result = json.loads(block.content)
            if block.name == "get_coverage_report":
                print(f"\n[COVERAGE REPORT]")
                print(f"  Applicable risks: {result['applicable_risks']}")
                print(f"  Planned: {result['planned']} ({result['coverage_pct']}%)")
                print(f"  Gaps: {result['gaps']}")
                print()

    return response


def main():
    """Run red-team planning across all example systems."""
    print("\nOntology-Driven Red-Team Planning — Multi-System Integration Example\n")

    for system in SYSTEMS:
        plan_for_system(system["name"], system["description"])

    print("\n" + "="*70)
    print("Governance Summary")
    print("="*70)
    print("\nIf you connected this to a database or ticketing system, you could now:")
    print("  - Report coverage % across all systems")
    print("  - Identify which risk categories are universally untested")
    print("  - Assign human red-team tasks to teams with deadlines")
    print("  - Verify that all gaps have a mitigation path")


if __name__ == "__main__":
    main()
