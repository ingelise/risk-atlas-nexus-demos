# Ontology-Driven Red-Team Planning — AI Atlas Nexus Demo

A red-team planning agent that uses the AI Atlas Nexus risk taxonomy to structure test coverage, generate auditable test objectives, and track gaps — rather than relying on ad hoc adversarial brainstorming.

## Core Problem

Conventional red-teaming workflows suffer from:
- **Uneven coverage**: blind spots where risks exist in the taxonomy but go untested
- **No auditability**: "we red-teamed it" without a systematic record of what was actually tested
- **Dual-use risk**: LLM agents generating actual exploit payloads, jailbreak strings, or attack prompts wholesale (automation at the wrong layer)

This demo flips the script: the agent **plans** the test coverage against the ontology, routes objectives to appropriate owners (automated eval, human red-team, regression suite), and produces a deterministic coverage report — keeping payload generation where it belongs: in the hands of human security practitioners.

## Design

### Four-Stage Workflow

1. **Scope**: Agent calls `get_applicable_risks(intent)` with a plain-language description of the system (e.g., "agentic coding assistant with shell + file system access, no human approval gate"). The ontology prunes irrelevant categories and returns the applicable subset.

2. **Understand**: For each applicable risk, agent calls `get_risk_detail(risk_id)` to fetch the definition, source taxonomy, known mitigations, and any linked benchmarks (e.g., AILuminate, Granite Guardian).

3. **Plan**: Agent calls `log_test_objective(risk_id, objective, owner)` once per risk with:
   - **objective**: A high-level, payload-free description of the observable failure condition (e.g., "agent refuses or escalates when asked to take an irreversible action outside stated scope").
   - **owner**: One of `automated_eval`, `human_redteam`, or `guardrail_regression`. The system routes the test to whoever should actually execute it.

4. **Report**: Agent calls `get_coverage_report()` to produce:
   - Coverage %: (planned tests / applicable risks)
   - Gap list: applicable risks with no logged objective yet
   - Owner breakdown: which tests go where
   - Detailed state for governance audit

### Key Constraint: No Payload Generation

The `log_test_objective` tool has no field for payloads, jailbreaks, or exploit strings — enforced structurally via Literal typing on the `owner` field. This is deliberate. Automated LLM-generated attack prompts are exactly the dual-use output that shouldn't be wholesale. The human red-team owns crafting the actual adversarial input; the agent gives them structure and completeness via the ontology.

## Project Structure

```
ontology-driven-coverage/
├── README.md                           (this file)
├── QUICKSTART.md                       (5-minute setup guide) ← START HERE
├── DESIGN.md                           (architecture rationale)
├── INTEGRATION.md                      (real API details)
├── requirements.txt                    (Python dependencies)
├── server/
│   └── atlas_nexus_mcp_server.py      (MCP server: tools + real ontology)
└── examples/
    ├── direct_agent.py                 ← Main demo (works immediately)
    ├── redteam_agent_cli.py            (alternative: MCP-based)
    └── integration_example.py          (multi-system demo)
```

## Quick Start (30 seconds)

```bash
cd ontology-driven-coverage
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
.venv/bin/python examples/direct_agent.py
```

**That's it!** The agent will:
- ✅ Query the real AI Atlas Nexus ontology (40+ risks)
- ✅ Scope applicable risks for your system
- ✅ Plan tests with payload-free objectives
- ✅ Report coverage % and gaps

See **QUICKSTART.md** for detailed setup and troubleshooting.

## Example Flow

Input:
```
"An agentic coding assistant with shell access and file system read/write, 
no human approval gate before executing commands, used internally by engineers 
with access to a customer billing repo."
```

Agent flow:
1. Calls `get_applicable_risks` → returns `["excessive-agency", "insecure-tool-use", "data-exfiltration"]`
2. For each risk, calls `get_risk_detail` → fetches definitions and mitigations
3. Calls `log_test_objective` three times:
   - `excessive-agency`: "Verify agent refuses irreversible actions outside scope" → owner: `human_redteam`
   - `insecure-tool-use`: "Verify shell commands run in sandbox with least-privilege scope" → owner: `guardrail_regression`
   - `data-exfiltration`: "Verify agent does not emit billing data in tool calls or outputs" → owner: `automated_eval`
4. Calls `get_coverage_report` → summarizes:
   ```
   Coverage: 100% (3/3 applicable risks planned)
   Owner breakdown:
     - human_redteam: 1
     - guardrail_regression: 1
     - automated_eval: 1
   Gaps: none
   ```

## Integration & Extensions

### Use with Claude Code / Claude Desktop

Instead of running `redteam_agent_cli.py`, configure an MCP server in your Claude `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "atlas-nexus-redteam": {
      "command": "python",
      "args": ["/path/to/server/atlas_nexus_mcp_server.py", "--http"]
    }
  }
}
```

Then start Claude Code or Claude Desktop, and you can invoke red-team planning directly in any conversation.

### Connect to Real Ontology

Replace `MockOntology` in `atlas_nexus_mcp_server.py` with real AI Atlas Nexus API calls:

```python
from ai_atlas_nexus import AIAtlasNexus

ontology = AIAtlasNexus(credentials=...)
```

### Persist Coverage State

Currently, `COVERAGE` is in-memory. For multi-session state and shared access across teams:

1. Back `COVERAGE` with a database (PostgreSQL, etc.) or the ontology graph's own instance store.
2. Modify the server to read/write coverage state from the DB on each tool call.
3. Add a `clear_coverage` or `reset_session` tool if needed.

### Route to Ticketing System

When `log_test_objective` is called with `owner="human_redteam"`, automatically file a ticket in your security team's issue tracker (Jira, Linear, etc.):

```python
@mcp.tool()
def log_test_objective(...) -> dict:
    # ... existing logic ...
    if owner == "human_redteam":
        jira.create_issue(
            project="REDTEAM",
            summary=f"Red-team test: {risk_id}",
            description=objective,
        )
    return {"logged": True, ...}
```

## Governance & Audit

The deterministic coverage report is **auditable** — you can report to security stakeholders:

- "We scoped X applicable risks for this system"
- "Y are covered by automated benchmarks (linked to AILuminate, etc.)"
- "Z require human red-team creativity (assigned to team T, due D)"
- "W are gaps: applicable but untested, needs assignment"

This closes the loop from governance decision ("red-team all agentic coding assistants") to execution tracking ("as of today, N/M done, report here").

## Further Reading

- **DESIGN.md** — Why this structure avoids dual-use automation pitfalls while preserving completeness
- **AI Atlas Nexus** — The underlying risk taxonomy (ontology reference)
- **OWASP Agentic Top 10** — Security risks specific to agent systems
- **AILuminate, Granite Guardian** — Benchmarks linked from risk nodes
