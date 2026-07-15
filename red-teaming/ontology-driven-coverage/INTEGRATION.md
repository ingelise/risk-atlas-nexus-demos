# Integration Guide: Real AI Atlas Nexus API

This guide explains how the red-team planning agent now integrates with the actual AI Atlas Nexus knowledge graph.

## Architecture Change

### Before (Mock)
```python
class MockOntology:
    RISKS = {
        "excessive-agency": {...},
        "prompt-injection": {...},
        ...
    }
    
    def get_applicable_risks(self, intent: str):
        # Keyword matching only
        if "shell" in intent:
            return ["excessive-agency", "insecure-tool-use"]
        ...
```

### After (Real API)
```python
class AIAtlasNexusOntology:
    def __init__(self, base_dir=None, taxonomy="ibm-ai-risk-atlas"):
        from ai_atlas_nexus.library import AIAtlasNexus
        self.nexus = AIAtlasNexus(base_dir=base_dir)
        self.taxonomy = taxonomy
    
    def get_applicable_risks(self, intent: str):
        # Query full ontology
        all_risks = self.nexus.get_all_risks(taxonomy=self.taxonomy)
        # Score and filter risks (still keyword-based, but against real data)
        ...
```

## Key APIs Used

### 1. AIAtlasNexus Initialization

```python
from ai_atlas_nexus.library import AIAtlasNexus

# Initialize with default ontology (bundled)
nexus = AIAtlasNexus()

# Or with custom data directory
nexus = AIAtlasNexus(base_dir="/path/to/custom/ontology")
```

**Output**: AIAtlasNexus instance ready to query

### 2. Get All Risks

```python
all_risks = nexus.get_all_risks(taxonomy="ibm-ai-risk-atlas")
```

**Output**: List of `Risk` objects with:
- `id`: Risk identifier
- `name`: Human-readable name
- `description`: Full definition
- `tag`: Short tag
- `type`: Risk category
- `concern`: Impact description
- `url`: Reference link
- `isDefinedByTaxonomy`: Source taxonomy

### 3. Get Single Risk

```python
risk = nexus.get_risk(id="excessive-agency", taxonomy="ibm-ai-risk-atlas")
```

**Output**: Single `Risk` object or `None` if not found

**Also accepts**:
- `name`: Risk name (e.g., "Excessive Agency")
- `tag`: Risk tag (e.g., "EA")

### 4. Get Related Actions (Mitigations)

```python
actions = nexus.get_related_actions(id="excessive-agency", taxonomy="ibm-ai-risk-atlas")
```

**Output**: List of `Action` objects with:
- `id`: Action identifier
- `name`: Action name
- `description`: What the action does
- `type`: Action type (mitigation, control, etc.)

## Ontology Structure

The real ontology includes:

**Taxonomies** (available):
- `ibm-ai-risk-atlas` — IBM's comprehensive AI risk taxonomy
- Other taxonomies may be available depending on your deployment

**Risk Objects** have:
- **Definition**: What the risk is
- **Source**: Where it comes from (OWASP, NIST, etc.)
- **Type**: Category (security, fairness, robustness, etc.)
- **Concern**: Impact if it occurs
- **Related Actions**: Mitigations and controls that address it

**Action Objects** link to:
- **Risks**: Which risks they mitigate
- **Controls**: How they're implemented
- **Benchmarks**: Tests that verify effectiveness

## Improved Risk Scoping

The current implementation (in `atlas_nexus_mcp_server.py`) uses:

1. **Keyword matching** against the real ontology:
   - Parse system description for capability keywords
   - Score risks based on keyword relevance
   - Return top N applicable risks

**For production, consider upgrading to**:

2. **ML-based relevance scoring** (using BenchmarkRiskDetector):
   ```python
   from ai_atlas_nexus.blocks.risk_detector import BenchmarkRiskDetector
   
   detector = BenchmarkRiskDetector(
       risks=all_risks,
       inference_engine=engine,  # RITS or other LLM
       max_risk=10
   )
   
   applicable = detector.detect([system_description])
   ```

   This uses semantic matching instead of keyword matching, catching risks that aren't explicitly mentioned.

3. **Hybrid approach** (recommended):
   - Start with keyword matching for speed
   - Fall back to ML-based scoring for borderline cases
   - Cache results to avoid repeated inference

## Data Sources

The bundled ontology (`ai_atlas_nexus` package) includes:

- **IBM AI Risk Atlas**: Comprehensive taxonomy of AI risks
- **NIST AI RMF**: Governance and control mappings
- **OWASP Top 10s**: LLM and Agentic risk categories
- **Academic sources**: Research on AI safety and robustness

These are versioned with the library, so upgrading the library gives you the latest taxonomy.

## Error Handling

The server handles several failure modes:

1. **ai_atlas_nexus not installed**:
   - Falls back to MockOntology
   - Warning printed to stderr
   - Allows testing without the full library

2. **Risk not found**:
   - Returns `{"error": "Risk not found: <risk_id>"}`
   - Tool continues (MCP doesn't throw)

3. **Ontology initialization fails**:
   - Raises `RuntimeError` with details
   - Server doesn't start (fail-fast for production)

## Custom Ontology

To use a custom ontology (e.g., company-specific risks):

1. Prepare YAML files in LinkML format (matching the schema)
2. Place them in a directory
3. Pass to the server:
   ```bash
   python server/atlas_nexus_mcp_server.py --http --ontology-dir /path/to/custom
   ```

   Currently the CLI doesn't accept this flag, but you can modify `atlas_nexus_mcp_server.py`:
   ```python
   parser.add_argument("--ontology-dir", default=None)
   args = parser.parse_args()
   ontology = AIAtlasNexusOntology(base_dir=args.ontology_dir)
   ```

## Performance Notes

1. **Caching**: `_all_risks_cache` stores the full risk set to avoid repeated queries
2. **Scoping**: Keyword matching is fast; ML-based scoring is slower (needs LLM inference)
3. **Network**: No network calls — everything is local file-based

## Limitations & Future Work

### Current Limitations

1. **Risk scoping still uses keyword matching** — a production system should use ML-based semantic matching
2. **No benchmark execution** — `linked_benchmarks` are noted but not run
3. **No incident linking** — Can't yet map real incidents back to risk nodes
4. **No control linkage** — Actions are fetched but not scored for effectiveness

### Roadmap

- [ ] Add ML-based risk scoping (use BenchmarkRiskDetector)
- [ ] Integrate benchmark execution (run tests and mark as passed/failed)
- [ ] Link to ticketing system (file Jira issues for gaps)
- [ ] Track coverage over time (database persistence)
- [ ] Add incident-to-risk mapping (when a bug surfaces, which risk did it reveal?)
- [ ] Multi-taxonomy support (query across OWASP, NIST, etc.)

## Testing the Integration

### With Real Ontology (Recommended)

```bash
# Install the library
pip install ai-atlas-nexus

# Start server
python server/atlas_nexus_mcp_server.py --http

# Run client
python examples/redteam_agent_cli.py
```

The agent will query the real ontology and show actual risks from the IBM AI Risk Atlas.

### With Mock (Testing Only)

If `ai_atlas_nexus` is not installed, the server falls back to MockOntology. This is useful for:
- Testing the MCP server structure without the heavy dependency
- Rapid iteration on the tool design
- CI/CD pipelines where the full library isn't needed

To force the mock:

```python
# In server/atlas_nexus_mcp_server.py, comment out the real initialization
# ontology = AIAtlasNexusOntology()
# And uncomment:
# ontology = MockOntology()
```

## Example: Full Flow with Real API

```python
from ai_atlas_nexus.library import AIAtlasNexus

# 1. Initialize
nexus = AIAtlasNexus()

# 2. Get all risks
all_risks = nexus.get_all_risks(taxonomy="ibm-ai-risk-atlas")
print(f"Loaded {len(all_risks)} risks from the ontology")

# 3. Query a specific risk
risk = nexus.get_risk(name="Excessive Agency", taxonomy="ibm-ai-risk-atlas")
print(f"Risk: {risk.name}")
print(f"Description: {risk.description}")

# 4. Get mitigations
actions = nexus.get_related_actions(id=risk.id, taxonomy="ibm-ai-risk-atlas")
print(f"Mitigations: {[a.name for a in actions]}")

# 5. Get related risks
related = nexus.get_related_risks(id=risk.id, taxonomy="ibm-ai-risk-atlas")
print(f"Related risks: {[r.name for r in related]}")
```

**Output** (example):
```
Loaded 47 risks from the ontology
Risk: Excessive Agency
Description: Agent takes actions beyond its intended scope...
Mitigations: ['Human approval gate', 'Action allowlist', 'Limited delegation']
Related risks: ['Insecure Tool Use', 'Prompt Injection', ...]
```

## References

- **AIAtlasNexus API Docs**: See the library's docstrings and `library.py`
- **IBM AI Risk Atlas**: The bundled taxonomy
- **LinkML Schema**: The ontology is defined in LinkML format
- **OWASP & NIST**: Referenced categories within the ontology
