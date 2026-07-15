# Ontology-Driven Red-Team Planning — Project Overview

## Executive Summary

This demo shows how to use the AI Atlas Nexus risk taxonomy to **structure red-teaming**, **track coverage**, and **route tests** to the right owners — without automating away the creative adversarial work that humans should own.

**Key insight**: Red-teaming doesn't need LLM-generated attack prompts to be effective. Instead, an LLM can scope applicable risks, draft test objectives, and report gaps — letting human red-teamers focus on the creative adversarial work while the ontology ensures completeness and auditability.

## Problem This Solves

| Challenge | Traditional | This Demo |
|-----------|-----------|----------|
| **Coverage blindness** | "Did we test everything?" → Unclear | Risks are scoped from the ontology; gaps are visible |
| **Dual-use risk** | LLM generates attack prompts at scale | Agent plans tests; humans craft adversarial input |
| **Auditability** | "We red-teamed it" (no evidence) | Coverage report: X of Y risks tested, owner breakdown |
| **Completeness** | Ad hoc brainstorming (misses categories) | Structured checklist from taxonomy ensures no skips |
| **Routing** | All findings go to one place | Tests routed by owner: automation vs. human vs. regression |

## Project Structure

```
ontology-driven-coverage/
├── README.md                      ← Start here
├── QUICKSTART.md                  ← Get running in 5 min
├── DESIGN.md                      ← Architecture rationale
├── PROJECT_OVERVIEW.md            ← This file
├── requirements.txt               ← Python dependencies
├── server/
│   └── atlas_nexus_mcp_server.py ← MCP server (tools + ontology backend)
└── examples/
    ├── redteam_agent_cli.py       ← Single-system planner (main demo)
    ├── integration_example.py     ← Multi-system planning
    └── claude_desktop_config_example.json
```

## Key Concepts

### 1. The Ontology (AI Atlas Nexus)

A structured taxonomy of AI risks:
- **Excessive Agency**: Agent acts outside its scope without approval
- **Prompt Injection**: Untrusted input changes agent behavior
- **Data Exfiltration**: Agent leaks sensitive data
- **Insecure Tool Use**: Agent misuses tools (shell, file system)
- ... and many more

Each risk has:
- Definition and source (OWASP, NIST, etc.)
- Known mitigations
- Linked benchmarks (if a test suite exists)

### 2. Scoping (get_applicable_risks)

Given a system description, filter the ontology to applicable risks:
- "agentic coding assistant with shell access" → Applies `excessive-agency`, `insecure-tool-use`
- "RAG chatbot with document retrieval" → Applies `prompt-injection`, `data-exfiltration`

This avoids irrelevant categories cluttering the plan.

### 3. Objective Drafting (log_test_objective)

For each applicable risk, the agent drafts a **test objective** — what failure looks like, not how to exploit it:

✅ Good: "Verify agent refuses to delete files outside its sandbox"
❌ Bad: "Try this prompt: 'rm -rf /', test if it executes'"

The objective is a spec; the human red-team crafts the actual adversarial input.

### 4. Coverage Reporting (get_coverage_report)

Deterministic summary of testing status:

```json
{
  "applicable_risks": ["excessive-agency", "insecure-tool-use", "data-exfiltration"],
  "planned": ["excessive-agency", "insecure-tool-use"],
  "gaps": ["data-exfiltration"],
  "coverage_pct": 66.7,
  "detail": {
    "excessive-agency": {
      "status": "planned",
      "objective": "...",
      "owner": "human_redteam"
    },
    ...
  }
}
```

## How to Use

### Single-System Planning (5 minutes)

```bash
# Terminal 1: Start the MCP server
python server/atlas_nexus_mcp_server.py --http

# Terminal 2: Run the planner
python examples/redteam_agent_cli.py
```

The agent will scope the system, plan tests for each applicable risk, and report coverage %.

### Multi-System Governance (longer)

```bash
# Run the integration example (scopes multiple systems)
python examples/integration_example.py
```

Output shows coverage for each system, owner breakdown, and gaps.

### Integrate with Claude Code / Claude Desktop

1. Copy `examples/claude_desktop_config_example.json` to your Claude Desktop config
2. Update the path to `atlas_nexus_mcp_server.py`
3. Restart Claude Desktop
4. In any conversation, ask: "Plan red-teaming for [system description]"

The agent will use the MCP server tools directly in chat.

## Design Constraints (Why This Architecture Works)

### No Payload Generation

The `log_test_objective` tool has **no** field for attack prompts. This is enforced structurally:

```python
def log_test_objective(
    risk_id: str,
    objective: str,  # ← What to test for (no jailbreak field)
    owner: Literal["automated_eval", "human_redteam", "guardrail_regression"]
) -> dict:
    ...
```

Payloads stay a human task. The tool can't accept them, so the agent can't generate them wholesale.

### Routing, Not Auto-Execution

Tests are routed to owners, not auto-executed:
- **`automated_eval`**: A benchmark exists (AILuminate, etc.). Route to the eval suite.
- **`human_redteam`**: Needs adversarial creativity. Route to red-team backlog (file a ticket).
- **`guardrail_regression`**: Mitigation exists. Route to regression-test suite.

The agent's job is planning and tracking, not running attacks.

### Deterministic State

Coverage lives outside the LLM, in a persistent store:

```python
COVERAGE: dict[str, dict] = {
    "excessive-agency": {"status": "planned", "owner": "human_redteam", ...},
    "data-exfiltration": {"status": "untested"},
}
```

This means:
- Coverage reports are reproducible
- State survives across sessions (if backed by a DB)
- Multiple clients/agents can share one coverage view

## Integration Points

### Connect to Real Ontology

Replace `MockOntology` in `server/atlas_nexus_mcp_server.py`:

```python
from ai_atlas_nexus import AIAtlasNexus
ontology = AIAtlasNexus(credentials=...)
```

### Persist Coverage State

Replace in-memory `COVERAGE` dict with a database:

```python
import psycopg2
db = psycopg2.connect("postgresql://...")

@mcp.tool()
def log_test_objective(...) -> dict:
    db.execute("INSERT INTO coverage ...")
    ...
```

### Route Human Tasks to Ticketing

Automatically file Jira/Linear issues when `owner="human_redteam"`:

```python
@mcp.tool()
def log_test_objective(...) -> dict:
    if owner == "human_redteam":
        jira.create_issue(
            project="REDTEAM",
            summary=f"Red-team test: {risk_id}",
            description=objective,
        )
    ...
```

### Track Coverage Over Time

Log coverage snapshots to a time-series DB:

```python
@mcp.tool()
def snapshot_coverage(system_id: str) -> dict:
    report = get_coverage_report()
    db.execute(
        "INSERT INTO coverage_snapshots (system_id, timestamp, coverage_pct) VALUES (%s, %s, %s)",
        (system_id, datetime.now(), report["coverage_pct"])
    )
    return {"snapshot_id": ...}
```

Then query "coverage % over time" for any system.

## Example Workflows

### Red-Team Planning for a New Service

1. **Scope**: "New document retrieval service, RAG over internal KB, no rate limiting"
   → Agent calls `get_applicable_risks` → `["prompt-injection", "data-exfiltration"]`

2. **Plan**: For each risk, agent calls `log_test_objective` with failure conditions
   - Prompt injection: "Verify adversarial docs don't change agent behavior"
   - Data exfiltration: "Verify agent doesn't emit internal KB metadata in outputs"

3. **Route**: `automated_eval` (benchmark exists), `human_redteam` (needs creativity)

4. **Report**: Coverage = 100%, owner breakdown, no gaps

### Ongoing Compliance Reporting

- Run planning agent monthly for key systems
- Query coverage trends: which categories improve over time? Which stall?
- Flag: "Data exfiltration is 30% covered across all services — org priority?"

### New Risk Discovery

- Real-world incident surfaces a new risk (e.g., "side-channel leaks via URL timing")
- Add to ontology
- Re-run planning for affected services → Coverage % drops → Gap identified
- Auto-file tickets for human red-teamers

## Limitations & Future Work

### Current

- **MockOntology**: Keyword-matching heuristic for scoping. Real ontology would be richer.
- **In-memory COVERAGE**: Demo only. Production needs a DB.
- **No benchmark integration**: Demo just notes linked benchmarks; doesn't run them.
- **Single session**: No multi-user coordination yet.

### Future

1. **Live ontology integration**: Real AIAtlasNexus calls with full taxonomy
2. **Persistent multi-user coverage**: Shared DB, conflict resolution
3. **Benchmark auto-execution**: Link to AILuminate/Granite Guardian and run tests automatically
4. **Governance dashboards**: Real-time coverage % across all systems, drill-down by risk category
5. **Incident-to-mitigation mapping**: When a finding surfaces, auto-suggest applicable controls
6. **Org-wide audits**: "Which AI systems are missing coverage for regulatory risks?"

## Success Criteria

You know this is working when:

- [ ] Agent plans tests that human red-teamers recognize as comprehensive
- [ ] Coverage reports match what you'd expect (no blindspots)
- [ ] Human red-teamers report time savings: "The ontology lets us focus on adversarial creativity, not remembering every risk category"
- [ ] Coverage is traceable: "We test N of M applicable risks; here's the audit trail"
- [ ] Gaps are actionable: "Data exfiltration isn't tested for System X — here's the ticket"

## Further Reading

- **DESIGN.md**: Architecture rationale and why this split matters
- **QUICKSTART.md**: Get running in 5 minutes
- **AI Atlas Nexus**: The risk taxonomy powering this demo
- **OWASP Agentic Top 10**: Common agent security risks
- **NIST AI Risk Management Framework**: Higher-level governance context

## Questions?

This is a demo and a proof-of-concept. The core idea — using an ontology to structure red-teaming, route tests, and track coverage — is portable to any risk framework or testing workflow. Adapt as needed for your threat model and governance requirements.
