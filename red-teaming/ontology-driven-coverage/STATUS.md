# Project Status

## ✅ What's Working

### Real Ontology Integration
- ✅ AIAtlasNexus library loads and queries successfully
- ✅ Correct taxonomy name: `"ibm-risk-atlas"` (not `"ibm-ai-risk-atlas"`)
- ✅ 99 actual risks from IBM AI Risk Atlas loaded
- ✅ Full metadata: definitions, descriptions, concerns, sources
- ✅ Related actions (mitigations) fetched successfully
- ✅ Keyword-based scoping working (risks matched to system description)

### Agent Execution
- ✅ `examples/direct_agent.py` — **Main working entry point**
  - Uses Claude's native `tools` parameter (not MCP)
  - Actually invokes tools and gets real responses
  - Returns deterministic coverage report
  - No narration — actual execution with results

### MCP Server
- ✅ `server/atlas_nexus_mcp_server.py` runs without errors
- ✅ Can be started with `python server/atlas_nexus_mcp_server.py --http`
- ⚠️ Anthropic SDK's MCP client (beta) has issues — tools not being invoked by agent
- ⚠️ Use `direct_agent.py` instead (simpler, works immediately)

## 📋 What's Documented

- ✅ README.md — Updated with real API status
- ✅ QUICKSTART.md — 30-second setup guide with `direct_agent.py`
- ✅ INTEGRATION.md — Details on AIAtlasNexus API
- ✅ DESIGN.md — Architecture and constraints
- ✅ PROJECT_OVERVIEW.md — Detailed walkthrough
- ✅ MIGRATION_GUIDE.md — What changed from mock to real
- ✅ PRODUCTION_CHECKLIST.md — What's needed for production
- ✅ FILES_AND_STRUCTURE.md — File guide and reading paths

## ⚠️ Known Issues & Workarounds

### Issue: Taxonomy name mismatch
- **Problem**: Initial implementation used `"ibm-ai-risk-atlas"` but ontology uses `"ibm-risk-atlas"`
- **Status**: ✅ Fixed
- **Workaround**: Use correct name `"ibm-risk-atlas"`

### Issue: get_risk_detail fails with taxonomy filter
- **Problem**: AIAtlasNexus library has a bug when querying risks by ID with a taxonomy parameter
- **Status**: ✅ Worked around
- **Workaround**: Query without taxonomy parameter: `nexus.get_risk(id=risk_id)` (not `id=risk_id, taxonomy=...`)

### Issue: Anthropic SDK MCP client not invoking tools
- **Problem**: Beta MCP client feature in Anthropic SDK not actually calling tools
- **Status**: ⚠️ Unresolved (not a blocker)
- **Workaround**: ✅ Use `direct_agent.py` which uses Claude's native `tools` parameter instead

## 🚀 How to Use Right Now

### Quickest: Run the working agent

```bash
cd ontology-driven-coverage
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
.venv/bin/python examples/direct_agent.py
```

Expected output:
```
======================================================================
Red-Team Planning Agent (Direct Tool Calling)
======================================================================

[calling] get_applicable_risks
[result] {"applicable_risk_ids": ["atlas-...", ...]}
...
[agent] Based on the coverage analysis...

======================================================================
Final Coverage Report
======================================================================
{
  "applicable_risks": [...],
  "planned": [...],
  "gaps": [],
  "coverage_pct": 85.7,
  ...
}
```

### Alternative: MCP Server (for future integrations)

```bash
# Terminal 1: Start server
.venv/bin/python server/atlas_nexus_mcp_server.py --http

# Terminal 2: Use the direct agent (it ignores the server and calls ontology directly)
# Or: Configure Claude Desktop with the MCP server in claude_desktop_config.json
```

## 📊 Test Results

### Ontology Loading
```
✓ Loaded 99 risks from ibm-risk-atlas taxonomy
✓ Risks accessible by ID, name, and tag
✓ Related actions/mitigations fetchable
```

### Risk Scoping
```
Input: "agentic coding assistant with shell access and file system read/write"
✓ Found 10 applicable risks:
  - atlas-exposing-personal-information
  - atlas-data-privacy-rights
  - atlas-revealing-confidential-information
  - ... (7 more)
```

### Tool Execution
```
✓ get_applicable_risks: Returns real risk IDs
✓ get_risk_detail: Returns full metadata (id, name, description, concerns, mitigations)
✓ log_test_objective: Logs objective and owner, updates coverage state
✓ get_coverage_report: Returns applicable/planned/gaps with coverage %
```

## ❌ What's NOT Working (Known Gaps)

### Persistence
- ❌ COVERAGE state is in-memory (lost on restart)
- ❌ No database backing yet
- **Impact**: Single-session only. For multi-session shared state, need DB.

### Authentication
- ❌ No API key or OAuth on MCP server
- ❌ Unauthenticated access only
- **Impact**: Can't restrict access. For production, add auth.

### Ticketing
- ❌ No integration with Jira, Linear, Asana, etc.
- ❌ Human red-team tasks logged in memory only
- **Impact**: Can't route tasks to teams. For production, add ticketing.

### Multi-System Tracking
- ❌ Coverage is global (not per-system)
- ❌ No way to compare coverage across systems
- **Impact**: Can't track "which system has the most gaps?" For production, add system_id parameter.

### ML-Based Risk Scoping
- ❌ Currently keyword-matching only
- ❌ No BenchmarkRiskDetector integration
- **Impact**: May miss risks not explicitly mentioned. For production, upgrade to LLM-based semantic matching.

### Benchmark Integration
- ❌ linked_benchmarks noted but not executed
- ❌ No auto-run of AILuminate, Granite Guardian, etc.
- **Impact**: Can't verify coverage with actual tests. For production, integrate benchmarks.

## 🎯 Next Steps (Priority Order)

### This Week (To Unlock Production Use)
1. [ ] Add PostgreSQL backing for COVERAGE state (persistence)
2. [ ] Add API key authentication to server
3. [ ] Add multi-system scoping (system_id parameter)
4. [ ] Test with 3-5 real systems

### Next Week (Production-Grade)
5. [ ] Integrate with Jira (auto-file human red-team tasks)
6. [ ] Add benchmark execution (run tests, mark pass/fail)
7. [ ] Governance reporting (pre-built compliance reports)
8. [ ] Coverage trend tracking (coverage % over time)

### Later (Nice-to-Have)
9. [ ] ML-based risk scoping (BenchmarkRiskDetector)
10. [ ] Incident-to-risk mapping
11. [ ] Multi-taxonomy support
12. [ ] Advanced analytics and heatmaps

See **PRODUCTION_CHECKLIST.md** for full requirements.

## 📝 Summary

**Status**: ✅ **Working and ready for testing**

The real AI Atlas Nexus ontology is integrated and functional. The `direct_agent.py` entry point works immediately and produces real, auditable red-team coverage plans. The MCP server is available for future integrations.

**To use right now**: Run `direct_agent.py` (see Quick Start above)

**To ship to production**: Complete items in PRODUCTION_CHECKLIST.md

**For questions**: See QUICKSTART.md, DESIGN.md, and INTEGRATION.md
