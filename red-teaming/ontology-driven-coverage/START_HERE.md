# 🚀 Start Here

Welcome to the Ontology-Driven Red-Team Planning Agent. This file guides you to what you need.

## I Want to... (Choose Your Path)

### 🎯 **Run the Agent in 30 Seconds**

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
.venv/bin/python examples/direct_agent.py
```

Done! The agent will query the real ontology and report coverage.

→ **Read**: [QUICKSTART.md](QUICKSTART.md)

---

### 📚 **Understand What This Project Does**

This is a **red-team planning agent** that uses the **AI Atlas Nexus** risk taxonomy to:
1. **Scope** which risks apply to your AI system
2. **Plan** tests (payload-free objectives, not exploits)
3. **Track** coverage against 99 known risks
4. **Report** gaps and owner breakdown

→ **Read**: [README.md](README.md) (2 min), then [DESIGN.md](DESIGN.md) (5 min)

---

### 🔧 **Understand the Real Ontology Integration**

We replaced the mock with the actual **AI Atlas Nexus** library:
- 99 real risks from IBM AI Risk Atlas, OWASP, NIST
- Full metadata: definitions, mitigations, controls
- Keyword-based scoping (can upgrade to ML-based)

→ **Read**: [INTEGRATION.md](INTEGRATION.md)

---

### 🏗️ **Understand the Architecture**

The agent has:
- **AIAtlasNexusOntology** wrapper (calls real library, queries by keyword)
- **MCP server** (optional, for Claude Desktop integration)
- **direct_agent.py** (main entry point, uses Claude's tool_use)
- **COVERAGE tracker** (in-memory, tracks test status per risk)

→ **Read**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) or [DESIGN.md](DESIGN.md)

---

### 🚢 **Deploy to Production**

Before shipping, you need:
- ✅ Real ontology (done)
- ❌ Database persistence (COVERAGE is in-memory)
- ❌ Authentication
- ❌ Ticketing integration (file Jira tasks for red-team)
- ❌ Multi-system tracking
- ❌ Governance reporting

→ **Read**: [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)

---

### 🔄 **Understand What Changed**

We updated the server from mock to real API. Here's what changed:
- MockOntology → AIAtlasNexusOntology (queries real library)
- Hardcoded 4 risks → 99 actual risks
- Taxonomy name: `"ibm-ai-risk-atlas"` → `"ibm-risk-atlas"`
- Mitigation structure changed (now objects with metadata)

→ **Read**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) or [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

### 📂 **Find What's in This Project**

Files and their purposes:

| File | Purpose |
|------|---------|
| **START_HERE.md** | This file |
| **QUICKSTART.md** | 30-second setup, troubleshooting |
| **README.md** | Project overview |
| **DESIGN.md** | Why this architecture, design constraints |
| **STATUS.md** | What's working, what's not, issues & workarounds |
| **INTEGRATION.md** | Real API details, how to use AIAtlasNexus |
| **MIGRATION_GUIDE.md** | What changed from mock to real |
| **PRODUCTION_CHECKLIST.md** | What's needed before production |
| **IMPLEMENTATION_SUMMARY.md** | This update summary |
| **PROJECT_OVERVIEW.md** | Detailed walkthrough, workflows, extensions |
| **FILES_AND_STRUCTURE.md** | Complete file listing, reading guide |
| **GETTING_STARTED.txt** | Quick reference card |
| **server/atlas_nexus_mcp_server.py** | MCP server + real ontology (production option) |
| **examples/direct_agent.py** | Main demo agent (works immediately) ⭐ |
| **examples/redteam_agent_cli.py** | Alternative agent (MCP-based, not working yet) |
| **examples/integration_example.py** | Multi-system planning demo |

→ **Read**: [FILES_AND_STRUCTURE.md](FILES_AND_STRUCTURE.md) for complete guide

---

### ⚠️ **Troubleshoot Issues**

Common problems:

**"ModuleNotFoundError: No module named 'anthropic'"**
→ Run: `.venv/bin/pip install -r requirements.txt`

**"No applicable risks found"**
→ Try a system description with more keywords. See [QUICKSTART.md](QUICKSTART.md#troubleshooting)

**"anthropic.AuthenticationError"**
→ Set: `export ANTHROPIC_API_KEY=sk-...`

→ **Read**: [QUICKSTART.md](QUICKSTART.md#troubleshooting) or [STATUS.md](STATUS.md)

---

## 📊 Project Status at a Glance

| Component | Status |
|-----------|--------|
| Real ontology (99 risks) | ✅ Working |
| Risk scoping | ✅ Working (keyword-based) |
| Tool execution | ✅ Working (direct_agent.py) |
| Coverage tracking | ✅ Working (in-memory) |
| MCP server | ✅ Running, ⚠️ Anthropic SDK issue |
| Persistence | ❌ In-memory only |
| Authentication | ❌ None |
| Ticketing | ❌ Not integrated |
| Multi-system | ❌ Single global state |
| ML-based scoping | ❌ Keyword-based only |

→ **Read**: [STATUS.md](STATUS.md) for full details

---

## 🎯 What to Do Next

### For Testing (Recommended)
1. Run `direct_agent.py` and explore
2. Try different system descriptions
3. Read DESIGN.md to understand why it's structured this way

### For Production
1. Read PRODUCTION_CHECKLIST.md
2. Add database backing (replace in-memory COVERAGE)
3. Add authentication
4. Add ticketing integration
5. Test with 3-5 real systems

### For Integration
1. Use the MCP server with Claude Desktop (configure in claude_desktop_config.json)
2. Or embed the ontology in your own workflows

---

## 🔗 Key Concepts

**Ontology**: Structured taxonomy of AI risks (99 risks from IBM, OWASP, NIST)

**Risk Scoping**: Filter the ontology to applicable risks for your system

**Test Objective**: High-level failure condition (what to test), not a payload or jailbreak

**Coverage**: Track which risks are tested, which are gaps, who tests each one

**Owner**: Who executes the test → `automated_eval`, `human_redteam`, or `guardrail_regression`

**Payload-Free Design**: The agent plans tests; humans craft the actual adversarial input

---

## ⏱️ Time Commitment

- **5 min**: Run the agent, see it work ([QUICKSTART.md](QUICKSTART.md))
- **15 min**: Understand the design ([README.md](README.md) + [DESIGN.md](DESIGN.md))
- **30 min**: Learn the real API ([INTEGRATION.md](INTEGRATION.md))
- **1 hour**: Full walkthrough ([PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md))
- **2 hours**: Plan production deployment ([PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md))

---

## 💡 Pro Tips

1. **Start with `direct_agent.py`** — it works immediately (don't worry about the MCP server yet)
2. **Customize the system description** — edit line ~200 in `direct_agent.py` to plan for your own systems
3. **Read DESIGN.md first** — understanding why this design matters will help everything else click
4. **The ontology is real** — 99 actual risks from authoritative sources (IBM, OWASP, NIST)
5. **This is production-ready for standalone use** — but needs DB + auth before sharing

---

**Ready?** Run this and see it work:

```bash
.venv/bin/python examples/direct_agent.py
```

Then read [QUICKSTART.md](QUICKSTART.md) for customization and troubleshooting.

Happy red-teaming! 🎯
