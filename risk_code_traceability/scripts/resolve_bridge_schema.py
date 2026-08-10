# SPDX-License-Identifier: Apache-2.0
"""
Materializes graphify_bridge.yaml with the AI_ATLAS_NEXUS_SCHEMA_PATH
placeholder replaced by the absolute path of the installed
ai-atlas-nexus schema, so LinkML tooling (gen-json-schema, gen-pydantic)
can resolve the `imports` without a hardcoded, environment-specific path.
"""
import sys
from importlib.resources import files
from pathlib import Path

BRIDGE_SCHEMA = Path(__file__).parent.parent / "src/risk_code_traceability/schema/graphify_bridge.yaml"
PLACEHOLDER = "AI_ATLAS_NEXUS_SCHEMA_PATH"
UPSTREAM_SCHEMA_RELPATH = "ai_risk_ontology/schema/ai-risk-ontology.yaml"


def resolve(output_path: Path) -> Path:
    upstream_path = files("ai_atlas_nexus") / UPSTREAM_SCHEMA_RELPATH
    if not upstream_path.is_file():
        raise FileNotFoundError(f"ai-atlas-nexus schema not found at {upstream_path}")

    # LinkML's import resolver appends ".yaml" itself, so the imports: entry
    # must omit the extension or resolution fails with a ".yaml.yaml" path.
    import_path = str(upstream_path).removesuffix(".yaml")

    text = BRIDGE_SCHEMA.read_text()
    text = text.replace(PLACEHOLDER, import_path)
    output_path.write_text(text)
    return output_path


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else BRIDGE_SCHEMA.parent / "graphify_bridge.resolved.yaml"
    resolve(out)
    print(f"Resolved schema written to {out}")
