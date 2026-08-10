# SPDX-License-Identifier: Apache-2.0
"""Parse Graphify's node-link graph.json into CodeArtifact dicts, offline."""
import hashlib
import json
from pathlib import Path
from typing import Any


def load_graphify_graph(path: str | Path) -> list[dict[str, Any]]:
    with open(path) as f:
        data = json.load(f)

    artifacts = []
    for node in data.get("nodes", []):
        content = node.get("content", node.get("summary", ""))
        artifacts.append({
            "id": node["id"],
            "name": node.get("label", node["id"].split("::")[-1]),
            "source_file": node.get("source_file", ""),
            "node_type": _infer_node_type(node),
            "community_id": node.get("community", -1),
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            "content_summary": node.get("summary", content[:500]),
            "source_commit": node.get("git_commit", "unknown"),
        })
    return artifacts


def _infer_node_type(node: dict) -> str:
    node_id = node.get("id", "")
    if "::" in node_id:
        return "function"
    if node.get("file_type", "") in ("python", "javascript", "typescript", "java"):
        return "file"
    return "concept"
