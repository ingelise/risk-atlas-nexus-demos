# SPDX-License-Identifier: Apache-2.0
"""
Pass C: LLM verification of candidate (artifact, risk) pairs.
Called only on candidates above the combined A+B score threshold, to contain cost.

Confidence routing (applied by the orchestrator):
  >= 0.85  -> confirmed (auto-merge)
  0.5-0.85 -> proposed  (human review)
  < 0.5    -> rejected
"""
import json

import anthropic

SYSTEM_PROMPT = """You are an AI governance analyst. You will be given a code artifact
(its name, file path, and a summary of what it does) and an AI risk from the AI Atlas
Nexus taxonomy (its name and description).

Assess whether the code artifact is meaningfully related to the risk - for example,
it implements, mitigates, triggers, or exposes the risk in some way.

Respond ONLY with a JSON object. No preamble, no markdown fences.
Schema:
{
  "related": true | false,
  "confidence": <float 0.0-1.0>,
  "rationale": "<one or two sentences explaining why>"
}"""


def pass_c(
    artifact: dict,
    risk_name: str,
    risk_description: str,
    model: str = "claude-sonnet-4-6",
    client: anthropic.Anthropic | None = None,
) -> dict:
    """Returns dict with keys: related, confidence, rationale."""
    client = client or anthropic.Anthropic()

    user_message = json.dumps({
        "artifact": {
            "name": artifact["name"],
            "source_file": artifact["source_file"],
            "summary": artifact.get("content_summary", "")[:800],
        },
        "risk": {
            "name": risk_name,
            "description": risk_description,
        },
    }, indent=2)

    response = client.messages.create(
        model=model,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    block = response.content[0]
    assert isinstance(block, anthropic.types.TextBlock)  # only content type possible for a text-only prompt
    raw = block.text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"related": False, "confidence": 0.0, "rationale": f"Parse error: {raw[:100]}"}
