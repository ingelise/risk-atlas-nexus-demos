"""
Direct red-team planning agent — Main Demo
===========================================

This is the WORKING entry point for the red-team planning agent.

Uses Claude's native tool_use to call the ontology directly:
- ✅ Queries real AI Atlas Nexus ontology (99 risks)
- ✅ Gets actual tool responses (not MCP, just direct calls)
- ✅ Plans tests with payload-free objectives
- ✅ Reports coverage % and gaps

STATUS: Production-ready for standalone use. For persistence/auth/ticketing,
see PRODUCTION_CHECKLIST.md

Run it:
    python examples/direct_agent.py

Or with a custom system description:
    Edit line ~200 to change the system description, then run.
"""
import sys
import os
import json

# Import from server module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))
from atlas_nexus_mcp_server import ontology, COVERAGE
from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-opus-4-8"

# Define tools for Claude
TOOLS = [
    {
        "name": "get_applicable_risks",
        "description": "Scope which ontology risks apply to a system",
        "input_schema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "Plain-language description of the system under test"
                }
            },
            "required": ["intent"]
        }
    },
    {
        "name": "get_risk_detail",
        "description": "Fetch full details for a risk from the ontology",
        "input_schema": {
            "type": "object",
            "properties": {
                "risk_id": {
                    "type": "string",
                    "description": "Risk identifier"
                }
            },
            "required": ["risk_id"]
        }
    },
    {
        "name": "log_test_objective",
        "description": "Log a test objective (no payloads)",
        "input_schema": {
            "type": "object",
            "properties": {
                "risk_id": {
                    "type": "string",
                    "description": "Risk ID"
                },
                "objective": {
                    "type": "string",
                    "description": "Payload-free test objective"
                },
                "owner": {
                    "type": "string",
                    "enum": ["automated_eval", "human_redteam", "guardrail_regression"],
                    "description": "Who executes this test"
                }
            },
            "required": ["risk_id", "objective", "owner"]
        }
    },
    {
        "name": "get_coverage_report",
        "description": "Get current coverage report",
        "input_schema": {"type": "object", "properties": {}}
    }
]

SYSTEM_PROMPT = """You are a red-team planning agent. Your job is to build
a test-coverage plan for an AI system using the AI Atlas Nexus risk ontology.

Process:
1. Call get_applicable_risks with the system description to scope relevant risks
2. For each applicable risk_id, call get_risk_detail to understand it
3. For each, call log_test_objective with a clear, payload-free failure condition and owner
4. Call get_coverage_report and present a final summary

Never produce jailbreak prompts or exploit payloads — objectives describe what a
tester should check for, and humans own crafting the actual adversarial input."""


def call_tool(name: str, **kwargs) -> dict:
    """Call a tool directly and return the result"""
    if name == "get_applicable_risks":
        result = ontology.get_applicable_risks(kwargs["intent"])
        return {"applicable_risk_ids": result}

    elif name == "get_risk_detail":
        return ontology.get_risk_detail(kwargs["risk_id"])

    elif name == "log_test_objective":
        COVERAGE[kwargs["risk_id"]] = {
            "status": "planned",
            "objective": kwargs["objective"],
            "owner": kwargs["owner"]
        }
        return {"logged": True, "risk_id": kwargs["risk_id"]}

    elif name == "get_coverage_report":
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


def run_agent(system_description: str):
    """Run agent with tool calling loop"""
    messages = [{"role": "user", "content": system_description}]

    print("\n" + "="*70)
    print("Red-Team Planning Agent (Direct Tool Calling)")
    print("="*70 + "\n")

    turn = 0
    max_turns = 20  # Safety limit

    while turn < max_turns:
        turn += 1

        # Call Claude with tools
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            tools=TOOLS,
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        # Print any text from Claude
        for block in response.content:
            if hasattr(block, 'text') and block.text:
                print(f"[agent] {block.text}\n")

        # If Claude stops (end_turn), we're done
        if response.stop_reason == "end_turn":
            print("\n[done]\n")
            break

        # If Claude wants to use tools (tool_use stop reason)
        if response.stop_reason == "tool_use":
            # Add Claude's response to messages
            messages.append({"role": "assistant", "content": response.content})

            # Process each tool call
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n[calling] {block.name}")

                    # Call the tool
                    result = call_tool(block.name, **block.input)

                    # Show result (first 200 chars for brevity)
                    result_str = json.dumps(result)
                    print(f"[result] {result_str[:200]}{'...' if len(result_str) > 200 else ''}\n")

                    # Add to results
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str
                    })

            # Add all tool results in one user message
            messages.append({"role": "user", "content": tool_results})
        else:
            # Some other stop reason — we're done
            print(f"\n[stopped with: {response.stop_reason}]\n")
            break

    print("="*70)
    print("Final Coverage Report")
    print("="*70)
    report = call_tool("get_coverage_report")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    description = (
        "An agentic coding assistant with shell access and file system "
        "read/write, no human approval gate before executing commands, "
        "used internally by engineers."
    )
    run_agent(description)
