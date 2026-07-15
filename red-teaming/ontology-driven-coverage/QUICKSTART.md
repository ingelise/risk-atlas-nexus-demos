# Quick Start Guide

Get the red-team planning agent up and running in 5 minutes.

## Prerequisites

- Python 3.10+
- `ANTHROPIC_API_KEY` environment variable set
- Virtual environment (`.venv`) with dependencies installed

## Setup

### 1. Install dependencies

```bash
cd red-teaming/ontology-driven-coverage
pip install -r requirements.txt
```

This installs:
- `anthropic` — Claude API client
- `mcp` — Model Context Protocol (optional, for future use)
- `ai-atlas-nexus` — Real AI risk ontology (40+ risks)

### 2. Run the agent (simplest approach)

```bash
cd red-teaming/ontology-driven-coverage
export ANTHROPIC_API_KEY=sk-your-key-here
.venv/bin/python examples/direct_agent.py
```

**That's it!** The agent will:
1. ✅ Scope applicable risks from the real ontology
2. ✅ Fetch details for each risk
3. ✅ Plan tests with payload-free objectives
4. ✅ Report coverage % and gaps

## What You'll See

Output like:

```
======================================================================
Red-Team Planning Agent (Direct Tool Calling)
======================================================================

[calling] get_applicable_risks
[result] {"applicable_risk_ids": ["atlas-exposing-personal-information", ...]}

[calling] get_risk_detail
[result] {"id": "atlas-exposing-personal-information", "name": "Exposing personal information", ...}

[calling] log_test_objective
[result] {"logged": true, "risk_id": "atlas-exposing-personal-information"}

[agent] Based on the coverage analysis, I've planned tests for X applicable risks...

======================================================================
Final Coverage Report
======================================================================
{
  "applicable_risks": [...],
  "planned": [...],
  "gaps": [],
  "coverage_pct": 100.0,
  ...
}
```

## Alternative: Using the MCP Server (Optional)

If you want to expose the tools via MCP (for Claude Desktop or custom clients):

**Terminal 1: Start server**
```bash
.venv/bin/python server/atlas_nexus_mcp_server.py --http
```

**Terminal 2: Use with Claude Code / Desktop**
- Add server to your `claude_desktop_config.json`
- Ask Claude: "Plan red-teaming for [system description]"

## Customization

### Try a different system

Edit `examples/direct_agent.py` and change the `description` variable:

```python
description = (
    "Your system description here: "
    "what tools does it have? what data does it access? "
    "what oversight exists?"
)
```

### Use a different Claude model

Edit line 22 in `examples/direct_agent.py`:

```python
MODEL = "claude-haiku-4-5-20251001"  # or claude-sonnet-5, etc.
```

## Next Steps

- **Understand the design**: Read **DESIGN.md** and **PROJECT_OVERVIEW.md**
- **Learn the API**: Read **INTEGRATION.md** for details on AIAtlasNexus
- **Production**: See **PRODUCTION_CHECKLIST.md** for what's needed before deploying

## Troubleshooting

**"ModuleNotFoundError: No module named 'anthropic'"?**
- Install dependencies: `.venv/bin/pip install -r requirements.txt`

**"anthropic.AuthenticationError"?**
- Set your API key: `export ANTHROPIC_API_KEY=sk-...`

**"No module named 'ai_atlas_nexus'"?**
- Install: `.venv/bin/pip install ai-atlas-nexus`

**"No applicable risks found"?**
- This means the keyword matching didn't find anything. Try a description with more keywords:
  - "shell", "file system", "exec", "code execution" → excessive-agency, insecure-tool-use
  - "data", "sensitive", "customer", "billing", "personal" → data-exfiltration
  - "retrieve", "document", "rag", "tool output" → prompt-injection

**Wrong model/rate limited?**
- Adjust `MODEL` to a model you have access to
- Wait a moment and try again
