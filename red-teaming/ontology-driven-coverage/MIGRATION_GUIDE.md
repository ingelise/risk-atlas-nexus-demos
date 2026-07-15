# Migration Guide: Mock → Real AI Atlas Nexus API

## Summary of Changes

The MCP server has been updated to use the actual **AI Atlas Nexus** knowledge graph instead of a mock ontology. This brings real risk taxonomies, mitigations, and relationships into the red-team planning agent.

## What Changed

### File: `server/atlas_nexus_mcp_server.py`

**Before**:
- `MockOntology` class with hardcoded risk definitions (4 risks)
- Keyword-matching scoping logic
- No access to real taxonomy

**After**:
- `AIAtlasNexusOntology` class that wraps the real `ai_atlas_nexus.library.AIAtlasNexus` API
- Queries all ~40+ risks from the actual IBM AI Risk Atlas
- Fetches full metadata: definitions, source, mitigations, related actions
- Graceful fallback to mock if library not installed

### Key Classes

#### Before
```python
class MockOntology:
    RISKS = {
        "excessive-agency": {"name": "...", "definition": "..."},
        ...
    }
    def get_applicable_risks(self, intent): ...
    def get_risk_detail(self, risk_id): ...
```

#### After
```python
class AIAtlasNexusOntology:
    def __init__(self, base_dir=None, taxonomy="ibm-ai-risk-atlas"):
        from ai_atlas_nexus.library import AIAtlasNexus
        self.nexus = AIAtlasNexus(base_dir=base_dir)
        self.taxonomy = taxonomy
        self._all_risks_cache = None
    
    def get_applicable_risks(self, intent):
        # Query full ontology, score by relevance
        all_risks = self.get_all_risks()
        # ...
    
    def get_risk_detail(self, risk_id):
        # Fetch from AIAtlasNexus with all metadata
        risk = self.nexus.get_risk(id=risk_id, taxonomy=self.taxonomy)
        actions = self.nexus.get_related_actions(id=risk_id, ...)
        # ...
```

### File: `requirements.txt`

**Before**:
```
anthropic>=0.28.0
mcp>=0.5.0
```

**After**:
```
anthropic>=0.28.0
mcp>=0.5.0
ai-atlas-nexus>=1.1.0
```

## How to Upgrade

### 1. Update Dependencies

```bash
cd ontology-driven-coverage
pip install -r requirements.txt  # Now includes ai-atlas-nexus
```

### 2. Start the Server

```bash
python server/atlas_nexus_mcp_server.py --http
```

**First time** it will:
- Import `AIAtlasNexus` from the installed package
- Load the bundled ontology (~40 risks)
- Print setup confirmation

**If `ai_atlas_nexus` not installed**:
- Falls back to MockOntology (with deprecation warning)
- Still functional for testing

### 3. Run the Client

```bash
python examples/redteam_agent_cli.py
```

The agent will now:
- Query the real ontology (not mock)
- Use actual risk definitions
- Show real mitigations and controls

## What's New / Improved

### 1. Real Risk Taxonomy
Before: 4 hardcoded risks
After: 40+ risks from IBM AI Risk Atlas, OWASP, NIST

### 2. Richer Metadata
Before: `{name, source, definition, mitigations, linked_benchmarks}`
After: `{id, name, description, source, tag, type, concern, url, mitigations: [...]}`

Mitigations now include:
- `id`: Unique identifier
- `name`: Mitigation name
- `description`: How it reduces risk
- `type`: Category (control, process, technical, etc.)

### 3. Better Risk Scoping
Before: Simple keyword matching (`if "shell" in intent`)
After: 
- Query all risks from ontology
- Score each risk by keyword relevance
- Return top N by score
- Still keyword-based (production should upgrade to ML-based using `BenchmarkRiskDetector`)

### 4. Related Controls
Before: Mitigations were just strings
After: Fetch related actions from the graph, with full metadata

### 5. Caching
- `_all_risks_cache` stores fetched risks to avoid repeated queries
- All rules fetched once, then cached in memory

## API Surface (No Changes to Tools)

The four MCP tools have **identical signatures**:

```python
@mcp.tool()
def get_applicable_risks(intent: str) -> dict: ...

@mcp.tool()
def get_risk_detail(risk_id: str) -> dict: ...

@mcp.tool()
def log_test_objective(risk_id: str, objective: str, owner: ...) -> dict: ...

@mcp.tool()
def get_coverage_report() -> dict: ...
```

Clients **don't change** — the server handles the migration transparently.

## Example: Before vs After

### Input
```
System: "Agentic coding assistant with shell access and file system read/write, 
         no human approval gate before executing commands, used internally by 
         engineers with access to customer billing repos."
```

### Before (Mock)
```
Applicable risks:
  - excessive-agency (OWASP)
  - insecure-tool-use (OWASP)
  - data-exfiltration (NIST)

get_risk_detail("excessive-agency"):
  {
    "name": "Excessive Agency",
    "definition": "Agent takes actions beyond its intended scope...",
    "mitigations": ["human-approval-gate", "action-allowlist"],
    "linked_benchmarks": []
  }
```

### After (Real API)
```
Applicable risks: [scored by relevance]
  - excessive-agency (score: 3)
  - insecure-tool-use (score: 2)
  - data-exfiltration (score: 1)
  - prompt-injection (score: 0.5) [found via ontology query]
  ... (40+ total risks available)

get_risk_detail("excessive-agency"):
  {
    "id": "excessive-agency",
    "name": "Excessive Agency",
    "description": "An AI system acts on...",
    "source": "ibm-ai-risk-atlas",
    "tag": "EA",
    "type": "Agency & Capability Risks",
    "concern": "The system may take actions...",
    "url": "https://...",
    "mitigations": [
      {
        "id": "control-1",
        "name": "Human Approval Gate",
        "description": "Require explicit human approval...",
        "type": "Process Control"
      },
      {
        "id": "control-2",
        "name": "Action Allowlist",
        "description": "Restrict actions to a known set...",
        "type": "Technical Control"
      }
    ],
    "linked_benchmarks": [...]
  }
```

## Migration Path

### Phase 1: Install & Test (Today)
- [ ] Install `ai-atlas-nexus>=1.1.0`
- [ ] Run server and client with real ontology
- [ ] Verify risks and objectives look reasonable

### Phase 2: Validate (Next Week)
- [ ] Red-teamers test the new coverage report
- [ ] Check that all expected risks are captured
- [ ] Verify mitigations are accurate and useful

### Phase 3: Deploy (When Ready)
- [ ] Update production server
- [ ] Verify coverage state persists (with new DB backing)
- [ ] Monitor error rates and performance

### Phase 4: Deprecate Mock (Later)
- [ ] Remove MockOntology class (still there for now, for fallback)
- [ ] Require `ai-atlas-nexus` as a hard dependency
- [ ] Update documentation

## Troubleshooting

### "ai_atlas_nexus not installed"
**Solution**: Install with `pip install ai-atlas-nexus`
**Fallback**: Server will still work with MockOntology

### "Risk not found: excessive-agency"
**Solution**: The risk ID is correct, but your custom ontology might not include it
**Check**: `python -c "from ai_atlas_nexus.library import AIAtlasNexus; nexus = AIAtlasNexus(); risks = nexus.get_all_risks(); print([r.id for r in risks[:5]])"`

### "ModuleNotFoundError: No module named 'linkml_runtime'"
**Solution**: `pip install --upgrade ai-atlas-nexus` (will install dependencies)

### Scoping returns too many risks
**Current**: All risks from ontology are returned if no keyword matches
**Fix**: Tweak the keyword-matching thresholds in `get_applicable_risks()`
**Future**: Use ML-based scoring for better precision

## Backward Compatibility

- ✅ All tool signatures unchanged
- ✅ Coverage state format unchanged
- ✅ Clients work without modification
- ⚠️ Risk ID format might change if you use custom taxonomy (use the real IDs)
- ⚠️ Mitigation structure changed (now objects with id/name/description, not strings)

## New Documentation

- **INTEGRATION.md** — Deep dive on the API and how to use it
- **PRODUCTION_CHECKLIST.md** — What needs to be done before production deployment
- **MIGRATION_GUIDE.md** — This file

## Questions?

- See **INTEGRATION.md** for API details
- See **DESIGN.md** for architecture
- See **PROJECT_OVERVIEW.md** for the big picture
- Run `examples/redteam_agent_cli.py` to see it in action
