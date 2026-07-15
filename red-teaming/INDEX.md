# Red-Teaming Demos — AI Atlas Nexus

Demonstrations of how to use the AI Atlas Nexus risk taxonomy for structured red-team planning, coverage tracking, and governance.

## Projects

### 1. Ontology-Driven Coverage Planning

**Path**: `ontology-driven-coverage/`

A red-team planning agent that uses the risk taxonomy to:
- **Scope** applicable risks for a system (filter out irrelevant categories)
- **Plan** tests by drafting payload-free objectives and routing to owners
- **Track** coverage with a deterministic report (X of Y risks tested, gaps identified)

**Key Insight**: Keep LLM automation in the planning/tracking layer (safe, auditable), and keep payload generation (jailbreak strings, exploit prompts) a human task.

**Get Started**:

set up api keys 
```bash
cd ontology-driven-coverage
pip install -r requirements.txt
python server/atlas_nexus_mcp_server.py --http    # Terminal 1
python examples/redteam_agent_cli.py               # Terminal 2 (after server starts)
```

**Documentation**:
- `README.md` — Project overview
- `QUICKSTART.md` — Get running in 5 minutes
- `DESIGN.md` — Architecture rationale
- `PROJECT_OVERVIEW.md` — Detailed walkthrough

**Key Files**:
- `server/atlas_nexus_mcp_server.py` — MCP server exposing four tools
- `examples/redteam_agent_cli.py` — Single-system planner (main demo)
- `examples/integration_example.py` — Multi-system planning
- `requirements.txt` — Dependencies (anthropic, mcp)

**What It Does**:

1. **get_applicable_risks(intent)** → Filter ontology to applicable risks
   ```
   Input: "Agentic coding assistant with shell access"
   Output: ["excessive-agency", "insecure-tool-use", "data-exfiltration"]
   ```

2. **get_risk_detail(risk_id)** → Fetch definition, mitigations, benchmarks
   ```
   Input: "excessive-agency"
   Output: {
     "name": "Excessive Agency",
     "definition": "...",
     "mitigations": ["human-approval-gate", "action-allowlist"],
     "linked_benchmarks": [...]
   }
   ```

3. **log_test_objective(risk_id, objective, owner)** → Plan a test (no payloads)
   ```
   Input: risk_id="excessive-agency", 
          objective="Verify agent refuses irreversible actions",
          owner="human_redteam"
   Output: {"logged": true, "risk_id": "excessive-agency"}
   ```

4. **get_coverage_report()** → Summarize coverage and gaps
   ```
   Output: {
     "applicable_risks": ["excessive-agency", "insecure-tool-use", "data-exfiltration"],
     "planned": ["excessive-agency", "insecure-tool-use"],
     "gaps": ["data-exfiltration"],
     "coverage_pct": 66.7,
     ...
   }
   ```

**Design Constraints** (Why This Works):

- **No payload field**: `log_test_objective` only accepts `objective` (what to test) and `owner` (who tests). No field for jailbreak strings. Enforced structurally.
- **Routing, not execution**: Tests are routed to `automated_eval`, `human_redteam`, or `guardrail_regression`. Not auto-executed.
- **Deterministic state**: Coverage lives outside the LLM, in a persistent store. Auditable, reproducible.

**Extensions**:

- Swap `MockOntology` for real `AIAtlasNexus` API calls
- Replace in-memory `COVERAGE` dict with a database for multi-session state
- Auto-file Jira tickets when `owner="human_redteam"`
- Track coverage % over time across multiple systems

## Why Ontology-Driven Planning?

| Challenge | Without Ontology | With Ontology-Driven Planning |
|-----------|------------------|-------------------------------|
| Coverage gaps | Hidden; you don't know what you missed | Visible; gaps are in the coverage report |
| Auditability | "We red-teamed it" (no evidence) | "We tested N of M applicable risks; here's the audit" |
| Scaling | Each system needs a fresh brainstorm | One ontology; scope per system, reuse taxonomy |
| Dual-use risk | LLM generates attack prompts wholesale | Agent plans; human red-teamers craft payloads |
| Owner assignment | All findings mixed together | Tests routed: automated, human, or regression |

## Integration Options

### 1. Standalone CLI (Fastest)

```bash
cd ontology-driven-coverage
python examples/redteam_agent_cli.py
```

Good for: Single-shot planning, CI pipelines, one-off analysis.

### 2. Claude Desktop / Code (Easiest)

Copy `examples/claude_desktop_config_example.json` to your Claude Desktop config, then ask Claude directly: "Plan red-teaming for [system description]"

Good for: Interactive planning, exploring multiple systems in conversation.

### 3. Custom Integration

Use the four MCP tools in your own orchestration logic (your agent framework, workflow engine, etc.). The tools are language-agnostic over MCP.

## Project Structure

```
red-teaming/
├── INDEX.md (this file)
└── ontology-driven-coverage/
    ├── README.md                          ← Start here
    ├── QUICKSTART.md                      ← 5-min setup
    ├── DESIGN.md                          ← Why this design
    ├── PROJECT_OVERVIEW.md                ← Detailed walkthrough
    ├── requirements.txt                   ← Dependencies
    ├── .env.example                       ← Config template
    ├── server/
    │   └── atlas_nexus_mcp_server.py     ← MCP server (main)
    └── examples/
        ├── redteam_agent_cli.py           ← Single-system planner
        ├── integration_example.py         ← Multi-system demo
        └── claude_desktop_config_example.json
```

## Governance & Compliance

Use the coverage report to demonstrate:

- **Compliance**: "We scoped X risks and tested Y%; gaps are [list]"
- **Traceability**: Link each test to its risk node in the ontology
- **Ownership**: "Human red-team owns N tests, automated suite owns M, regression tests own P"
- **Trends**: Track coverage % over time for each system

## Further Reading

- **OWASP Agentic Top 10**: https://owasp.org/www-project-agentic-top-10
- **NIST AI Risk Management Framework**: https://airc.nist.gov
- **AILuminate, Granite Guardian**: Benchmarks for testing AI robustness (linked in the ontology)

---

**Questions?** See the README or DESIGN files in `ontology-driven-coverage/` for detailed rationale.
