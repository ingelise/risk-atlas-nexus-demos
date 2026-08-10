# Risk-to-Code Traceability

Automatically links code artifacts extracted by Graphify to AI risks from the AI Atlas Nexus
risk ontology, through a three-pass detection pipeline (keywords → embeddings → LLM verification),
and stores the result as an RDF-star graph in an embedded pyoxigraph store.

```
 ┌───────────┐      ┌────────────────────┐      ┌──────────────┐
 │ Graphify  │ ───► │ graphify_bridge.yaml│ ───► │  pyoxigraph  │
 │ graph.json│      │ (LinkML schema,     │      │ RDF-star     │
 │           │      │  imports Atlas Nexus)│      │ triple store │
 └───────────┘      └────────────────────┘      └──────────────┘
```

## Prerequisites

- Python 3.11
- `ANTHROPIC_API_KEY` env var (only needed for Pass C / LLM verification — the pipeline runs fully
  without it via `skip_pass_c=True`)

The demonstration can be installed locally using the instructions below. 

The toolkit uses [uv](https://docs.astral.sh/uv/) as the package manager (Python 3.12). Make sure that `uv` is installed via either:

```curl -Ls https://astral.sh/uv/install.sh | sh```

or using [Homebrew](https://brew.sh):

```brew install astral-sh/uv/uv```

or using pip (use this if in Windows):

```pip install uv```

## Installation

Once `uv` is installed,

Navigate to the `python` directory and run:

```bash
uv venv --python 3.12 .venv-risk-code-traceability
source .venv-risk-code-traceability/bin/activate
uv pip install -e .
```


## What is being demonstrated

- **Pass A (keywords)** — a reverse index over each risk's `name`/`id` tokens gives an O(1) dict
  lookup per artifact token, so shortlisting candidates doesn't require scanning every risk.
- **Pass B (embeddings)** — `txtai` cosine similarity re-ranks Pass A's shortlist and also surfaces
  risks the keyword pass missed entirely.
- **Pass C (LLM verification)** — Claude judges the highest-scoring candidates directly (no
  orchestration framework) and assigns a status: `confirmed` (auto-merged), `proposed` (needs human
  review), or `rejected`.

Every surviving link is stored with full provenance as RDF-star: a link node asserts a quoted
`artifact hasRelatedRisk risk` triple, carrying `confidence`, `detectionMethod`, `rationale`, and
`status`. **The plain `hasRelatedRisk` triple is asserted for both `confirmed` and `proposed` links**
— only the `status` on the link node distinguishes an unreviewed proposal from a confirmed one, so
any consumer reading just the plain triple will treat a `proposed` link as if it were accepted.

## Going to production

pyoxigraph is embedded and zero-ops, good for this demo's scale. For a production graph, export the
store to Turtle (`serialize_store`) and load it into Neo4j via Atlas Nexus's existing Cypher export
tooling and the [`cymple`](https://github.com/koffiedev/cymple) query builder — the bridge schema and
query semantics are unchanged, only the storage backend

## Extending the schema

`src/risk_code_traceability/schema/graphify_bridge.yaml` composes with the upstream
`ai-atlas-nexus` schema via LinkML's `imports` mechanism — it never edits it. The upstream schema's
installed filesystem location varies by environment, so the import path is a placeholder
(`AI_ATLAS_NEXUS_SCHEMA_PATH`) resolved at build time:

```bash
python scripts/resolve_bridge_schema.py schema.resolved.yaml
gen-json-schema schema.resolved.yaml
```

New classes should follow `CodeArtifact`/`RiskTraceabilityLink`'s example: `is_a: Entity` (or another
upstream Atlas Nexus base class), so they participate in the existing graph model instead of forking it.

## License

Apache-2.0 — see the SPDX header in each source file.
