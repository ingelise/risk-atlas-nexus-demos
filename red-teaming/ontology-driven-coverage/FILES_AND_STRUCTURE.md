# Project Files and Structure

## Complete File Listing

```
ontology-driven-coverage/
│
├─ 📄 README.md                          Project overview & features
├─ 📄 QUICKSTART.md                      5-minute setup guide (start here!)
├─ 📄 DESIGN.md                          Architecture & why this design works
├─ 📄 PROJECT_OVERVIEW.md                Detailed walkthrough & workflows
├─ 📄 INTEGRATION.md                     ⭐ API details & AIAtlasNexus usage
├─ 📄 MIGRATION_GUIDE.md                 What changed from mock to real API
├─ 📄 PRODUCTION_CHECKLIST.md            Production readiness requirements
├─ 📄 IMPLEMENTATION_SUMMARY.md           What was done in this update
├─ 📄 GETTING_STARTED.txt                Quick reference card
├─ 📄 FILES_AND_STRUCTURE.md             This file
│
├─ 🔧 requirements.txt                   Python dependencies
├─ 📋 .env.example                       Environment variable template
│
├─ 📁 server/
│  └─ 🔧 atlas_nexus_mcp_server.py      ⭐ MCP server with real AIAtlasNexus
│                                         (replaced MockOntology)
│
└─ 📁 examples/
   ├─ 🔧 redteam_agent_cli.py           Single-system planner (main demo)
   ├─ 🔧 integration_example.py         Multi-system planning
   └─ 📋 claude_desktop_config_example.json  Claude Desktop config template
```

## Documentation Map

### Quick Start
- **QUICKSTART.md** — 5 minutes to running code
- **GETTING_STARTED.txt** — Reference card

### Understanding the System
- **README.md** — What this project does
- **DESIGN.md** — Why this architecture
- **PROJECT_OVERVIEW.md** — Detailed walkthrough with workflows

### The Change to Real API
- **MIGRATION_GUIDE.md** — Before/after comparison
- **INTEGRATION.md** — How to use the AIAtlasNexus API
- **IMPLEMENTATION_SUMMARY.md** — What was changed and how

### Production Deployment
- **PRODUCTION_CHECKLIST.md** — All requirements before shipping

## Key Files Explained

### Server: `server/atlas_nexus_mcp_server.py`

**Purpose**: MCP server exposing red-team planning tools

**What's Inside**:
1. **AIAtlasNexusOntology** class (NEW)
   - Wraps the real `ai_atlas_nexus.library.AIAtlasNexus` API
   - Loads 40+ risks from IBM AI Risk Atlas
   - Scores risks by relevance to system description
   - Fetches full metadata (definitions, mitigations, controls)
   - Caches risks for performance

2. **MCP Tools** (unchanged signatures)
   - `get_applicable_risks(intent)` — Scope which risks apply
   - `get_risk_detail(risk_id)` — Fetch full metadata
   - `log_test_objective(risk_id, objective, owner)` — Plan a test
   - `get_coverage_report()` — Summarize coverage & gaps

3. **Coverage State** (in-memory, needs DB for production)
   - Tracks test status per risk
   - Supports read/write via MCP tools

4. **Fallback to Mock**
   - If `ai_atlas_nexus` not installed, uses MockOntology
   - Allows testing without the full library
   - Production deployment requires real library

### Client: `examples/redteam_agent_cli.py`

**Purpose**: Example agent that uses the MCP server

**What It Does**:
1. Connects to MCP server on `http://127.0.0.1:8000/mcp`
2. Sends system description to Claude with MCP tools available
3. Claude calls tools to scope risks and plan tests
4. Prints all tool calls and reasoning
5. Returns final coverage report

**Usage**:
```bash
python examples/redteam_agent_cli.py
```

### Multi-System Example: `examples/integration_example.py`

**Purpose**: Show how to run planning across multiple systems

**What It Does**:
1. Defines 3 example systems:
   - Code Assistant with Shell Access
   - Document Retrieval Chatbot
   - Financial Analysis Agent
2. Runs planning for each one
3. Compares coverage across systems
4. Prints summary and next steps

**Usage**:
```bash
python examples/integration_example.py
```

### Configuration: `.env.example`

**Purpose**: Template for environment variables

**Includes**:
- ANTHROPIC_API_KEY (required)
- MCP_SERVER_URL (default: http://127.0.0.1:8000/mcp)
- Optional database credentials
- Optional ticketing system config

**To Use**:
```bash
cp .env.example .env
# Edit .env with your values
# Source it before running:
source .env
```

### Dependencies: `requirements.txt`

**What's Installed**:
- `anthropic` — Claude API client
- `mcp` — Model Context Protocol
- `ai-atlas-nexus` — Real risk ontology ⭐ NEW

**To Install**:
```bash
pip install -r requirements.txt
```

## Reading Guide by Role

### I'm a Red-Teamer
Start here:
1. QUICKSTART.md (get running in 5 min)
2. PROJECT_OVERVIEW.md (understand the workflow)
3. Try: `python examples/redteam_agent_cli.py`
4. Then: Use the real agent to plan for your system

### I'm an Engineer
Start here:
1. DESIGN.md (understand the architecture)
2. INTEGRATION.md (learn the API)
3. Read: `server/atlas_nexus_mcp_server.py`
4. Then: Modify for your use case (custom ontology, DB, etc.)

### I'm Setting Up Production
Start here:
1. MIGRATION_GUIDE.md (what changed)
2. PRODUCTION_CHECKLIST.md (what must be done)
3. INTEGRATION.md (API surface)
4. Then: Work through checklist items

### I'm Evaluating This Project
Start here:
1. README.md (what is this?)
2. PROJECT_OVERVIEW.md (why does it matter?)
3. Try: QUICKSTART.md
4. Check: PRODUCTION_CHECKLIST.md (is it ready for you?)

## What Changed (Real API Integration)

### Files Modified
- **server/atlas_nexus_mcp_server.py**
  - Replaced MockOntology with AIAtlasNexusOntology
  - Now queries real ontology (40+ risks)
  - Fetches full metadata and mitigations

- **requirements.txt**
  - Added: ai-atlas-nexus>=1.1.0

### Files Added
- **INTEGRATION.md** — API details
- **MIGRATION_GUIDE.md** — What changed
- **PRODUCTION_CHECKLIST.md** — Production requirements
- **IMPLEMENTATION_SUMMARY.md** — This update

### Files Unchanged
- **examples/redteam_agent_cli.py** — Same interface
- **examples/integration_example.py** — Still works
- **DESIGN.md** — Architecture unchanged
- **README.md** — Goals unchanged

## Testing the Integration

### Quick Test: Ontology Loaded?
```bash
python -c "
from ai_atlas_nexus.library import AIAtlasNexus
nexus = AIAtlasNexus()
risks = nexus.get_all_risks()
print(f'Loaded {len(risks)} risks')
"
```

### End-to-End Test: Full Planning
```bash
# Terminal 1: Start server
python server/atlas_nexus_mcp_server.py --http

# Terminal 2: Run agent
python examples/redteam_agent_cli.py
```

## Project Dependencies (Dependency Tree)

```
requirements.txt
├── anthropic>=0.28.0              (Claude API)
│   └── httpx (HTTP client)
│
├── mcp>=0.5.0                     (Model Context Protocol)
│   └── starlette (HTTP server)
│
└── ai-atlas-nexus>=1.1.0          (Risk ontology) ⭐ NEW
    ├── linkml (ontology format)
    ├── sssom (mapping format)
    ├── pyyaml (YAML parsing)
    └── jinja2 (template rendering)
```

## File Sizes

```
Documentation (~18 KB)
├─ README.md                    ~4 KB
├─ DESIGN.md                    ~5 KB
├─ PROJECT_OVERVIEW.md          ~7 KB
├─ INTEGRATION.md               ~8 KB
├─ MIGRATION_GUIDE.md           ~6 KB
├─ PRODUCTION_CHECKLIST.md      ~5 KB
└─ (other docs)                 ~2 KB

Code (~15 KB)
├─ server/atlas_nexus_mcp_server.py   ~12 KB
├─ examples/redteam_agent_cli.py      ~1 KB
├─ examples/integration_example.py    ~2 KB
└─ config files                       ~1 KB
```

## How to Extend

### Add a Custom Ontology
```python
# In server/atlas_nexus_mcp_server.py, modify:
ontology = AIAtlasNexusOntology(
    base_dir="/path/to/custom/ontology",
    taxonomy="my-custom-taxonomy"
)
```

### Add Database Persistence
Replace the in-memory `COVERAGE` dict:
```python
# Instead of:
COVERAGE: dict[str, dict] = {}

# Use:
import psycopg2
db = psycopg2.connect("postgresql://...")

# Modify tools to read/write from DB
@mcp.tool()
def log_test_objective(...):
    db.execute("INSERT INTO coverage ...")
    ...
```

### Add Ticketing Integration
```python
@mcp.tool()
def log_test_objective(risk_id, objective, owner):
    # ... existing logic ...
    
    if owner == "human_redteam":
        jira.create_issue(
            project="SECURITY",
            summary=f"Red-team test: {risk_id}",
            description=objective
        )
```

### Add ML-Based Risk Scoping
```python
# Replace keyword matching with:
from ai_atlas_nexus.blocks.risk_detector import BenchmarkRiskDetector

detector = BenchmarkRiskDetector(
    risks=all_risks,
    inference_engine=engine,
    max_risk=10
)
applicable = detector.detect([intent])
```

## Next Steps

1. **Try It**: Run `python examples/redteam_agent_cli.py`
2. **Understand**: Read INTEGRATION.md and PROJECT_OVERVIEW.md
3. **Customize**: Adapt examples for your systems and risks
4. **Deploy**: Work through PRODUCTION_CHECKLIST.md
5. **Integrate**: Connect to your ticketing system and governance workflows

---

**Status**: Complete and functional with real API integration. Ready for testing and development. Production deployment requires completing PRODUCTION_CHECKLIST.md items.
