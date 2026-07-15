# Design Rationale: Ontology-Driven Red-Team Planning

## Problem Statement

Red-teaming is often approached as a creative brainstorming exercise: practitioners rely on domain knowledge, past experience, and ad hoc intuition to generate test cases and attack scenarios. This approach suffers from several gaps:

1. **Incomplete Coverage**: Risks in the taxonomy that exist but aren't top-of-mind go untested. The result is an asymmetric coverage profile — some categories heavily tested, others ignored.

2. **Blind Spots Aren't Visible**: There's no structured record of what was tested against what. A report saying "we red-teamed the system" doesn't tell you which risk categories were scoped, which were skipped, or why.

3. **Dual-Use Risk at the Wrong Layer**: When an LLM agent is asked to generate "test cases for prompt injection," it's tempting to let it produce actual jailbreak strings or attack payloads. But wholesale LLM-generated exploits are exactly the kind of dual-use output that should stay bounded. Attack-prompt generation is where human judgment and accountability matter most.

4. **Coverage Doesn't Feed Back**: When a red-team test uncovers a mitigation gap, the finding sits in a security report somewhere. It doesn't automatically flag which control is missing or suggest which team should own it.

## Design Solution

**Separate planning from payload generation.**

- **Agent's job**: Scope the applicable risks for a system, understand each one, draft high-level test objectives (what a failure looks like), and route objectives to the right owners. Produce a deterministic coverage report.
- **Human red-team's job**: Given a test objective, craft the actual adversarial input — jailbreak prompt, shell-escape attempt, whatever is needed.
- **Automation's job**: Run regression tests against known mitigations.

This isn't about avoiding attack-prompt generation; it's about keeping LLM automation out of the creative adversarial work and instead using it for what it's good at: systematic exploration of a structured taxonomy and deterministic tracking.

## Core Components

### 1. The Ontology (MockOntology → Real AIAtlasNexus)

A taxonomy of AI risks, each with:
- **Definition**: What the risk is and why it matters
- **Source**: Where the risk comes from (OWASP Agentic Top 10, NIST GenAI Profile, etc.)
- **Mitigations**: Known controls that reduce the risk
- **Linked Benchmarks**: Existing test suites (AILuminate, Granite Guardian) that might automate testing for this risk

Example:
```json
{
  "risk_id": "excessive-agency",
  "name": "Excessive Agency",
  "definition": "Agent takes actions beyond its intended scope or without appropriate approval, especially irreversible ones.",
  "mitigations": ["human-approval-gate", "action-allowlist"],
  "linked_benchmarks": []
}
```

### 2. Scoping (get_applicable_risks)

Given a plain-language description of a system's capabilities, data access, and constraints, the agent calls `get_applicable_risks(intent)` to get the subset of risks that plausibly apply.

**Why this matters**: Not every risk in the taxonomy is relevant to every system. A medical-advice risk category shouldn't clutter the plan for a code-generation tool. Scoping filters the work.

**Mock logic** (to be replaced with real ontology): keyword matching on capabilities mentioned in the intent (e.g., "shell access" → escalate `excessive-agency` and `insecure-tool-use`, "customer data" → escalate `data-exfiltration`).

### 3. Planning (log_test_objective)

For each applicable risk, the agent calls `log_test_objective(risk_id, objective, owner)` with:

- **risk_id**: The risk this test addresses
- **objective**: A high-level description of what a failing test looks like. Examples:
  - "Agent refuses or escalates when asked to delete files it shouldn't have access to"
  - "Agent does not emit API keys, passwords, or billing data in tool call arguments or output"
  - "Agent rejects shell commands that write to directories outside its sandbox"
  
  These are **not** exploit payloads — they're test specifications.

- **owner**: One of:
  - `automated_eval`: A linked benchmark exists, or this can be checked by a deterministic rule (e.g., "does the agent's tool schema exclude destructive operations?"). Route to the eval suite.
  - `human_redteam`: Requires adversarial creativity. A human tester will craft the actual input. Route to the red-team backlog.
  - `guardrail_regression`: A known mitigation exists, and this is a regression check. Route to the regression-test suite.

**Design constraint**: `log_test_objective` has NO field for payloads, jailbreak strings, or attack prompts. This is enforced structurally by Literal typing on the `owner` enum — you physically cannot pass a prompt string to this tool. The objective describes what to test; the human red-team crafts how to test it.

### 4. Reporting (get_coverage_report)

Once planning is done, `get_coverage_report()` returns:

```json
{
  "applicable_risks": ["excessive-agency", "insecure-tool-use", "data-exfiltration"],
  "planned": ["excessive-agency", "insecure-tool-use"],
  "gaps": ["data-exfiltration"],
  "coverage_pct": 66.7,
  "detail": {
    "excessive-agency": {
      "status": "planned",
      "objective": "verify agent refuses irreversible actions outside scope",
      "owner": "human_redteam"
    },
    "insecure-tool-use": {
      "status": "planned",
      "objective": "verify shell commands run in sandbox",
      "owner": "guardrail_regression"
    },
    "data-exfiltration": {
      "status": "untested"
    }
  }
}
```

This is deterministic (lives outside the model, computed from state), auditable (you can show this to a compliance officer), and actionable (gaps and owner breakdowns drive next steps).

## Why This Architecture Matters

### 1. Avoids Dual-Use Automation

Generating adversarial prompts at scale without human oversight is risky — you could inadvertently help bad actors or create attack vectors you didn't intend. By keeping the agent in the planning layer and routing actual testing to humans, we bound the automation to what's safe and useful.

### 2. Ensures Completeness

A human red-teamer, no matter how skilled, can miss things. The ontology acts as a structured checklist — you can report "X of Y risks in the taxonomy were scoped" and have confidence you didn't accidentally skip a category.

### 3. Auditable & Reproducible

Because coverage state lives in a deterministic store (not in the LLM's reasoning), you can:
- Reproduce the exact coverage report from any earlier date
- Show stakeholders which risks are covered, which are gaps
- Attribute findings to their risk node for impact analysis

### 4. Composable with Multiple Clients

The MCP server approach decouples "how you access the ontology" from "how you run red-team planning." Claude Code, Claude Desktop, a custom script, or a CI pipeline can all connect to the same server and contribute to shared coverage state.

## Implementation Notes

### MockOntology → Real AIAtlasNexus

Replace:
```python
ontology = MockOntology()
```

with:
```python
from ai_atlas_nexus import AIAtlasNexus
ontology = AIAtlasNexus(credentials=...)
```

The tool signatures stay the same; only the backend changes.

### In-Memory COVERAGE → Persistent Store

For a single-session demo, the in-memory `COVERAGE` dict works. For production (multi-client, multi-session, governed workflows):

1. Replace with a database:
   ```python
   import psycopg2
   COVERAGE_DB = psycopg2.connect(...)
   ```

2. On each tool call, read/write from the DB instead of memory.

3. Add a `query_coverage_by_system(system_id)` tool if you want to track separate sessions per system.

### Log Test Objectives to Ticketing

Extend `log_test_objective` to automatically file tickets:

```python
@mcp.tool()
def log_test_objective(risk_id: str, objective: str, owner: ...) -> dict:
    COVERAGE[risk_id] = {"status": "planned", "objective": objective, "owner": owner}
    
    if owner == "human_redteam":
        ticket = jira.create_issue(
            project="SECURITY",
            summary=f"Red-team test: {risk_id}",
            description=objective,
            labels=["red-team", risk_id],
        )
        return {"logged": True, "risk_id": risk_id, "ticket_url": ticket.url}
    
    return {"logged": True, "risk_id": risk_id}
```

## Related Work

- **OWASP Agentic Top 10**: Taxonomy of risks specific to agent systems
- **NIST AI Risk Management Framework**: Higher-level governance framework
- **AILuminate, Granite Guardian**: Benchmarks for testing AI system robustness
- **AI Atlas Nexus**: Unified risk ontology that this design uses

## Further Extensions

1. **Coverage Over Time**: Track coverage % as it evolves (system matures, new risks discovered).
2. **Multi-System Governance**: Query coverage across all systems owned by an org; highlight which categories are universally untested.
3. **Mitigation Traceability**: When a red-team finding surfaces, link it back to the risk node and automatically suggest the known mitigations for that risk.
4. **Benchmark Integration**: If a risk has a linked benchmark, automatically run it and mark the test as "passed" or "needs manual review."
