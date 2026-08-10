# SPDX-License-Identifier: Apache-2.0
"""
Pass A: fast keyword heuristic shortlist.

The AI Atlas Nexus `Risk` class has no `hasKeywords` slot; `name` and `id`
are the only fields populated on every risk, so the index is built from
tokens of those two fields instead. Single-word tokens get an O(1) dict
lookup per artifact token; multi-word risk names fall back to a substring
check against a small phrase index.
"""
import re
from collections import defaultdict

from ai_atlas_nexus import AIAtlasNexus

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def build_keyword_index(
    nexus: AIAtlasNexus,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Returns (single_word_index, phrase_index) keyed by risk.name/id tokens."""
    single_word_index: dict[str, list[str]] = defaultdict(list)
    phrase_index: dict[str, list[str]] = defaultdict(list)
    for risk in nexus.get_all_risks():
        name_lower = (risk.name or "").lower()
        tokens = _tokenize(risk.name or "") | _tokenize(risk.id or "")
        for token in tokens:
            single_word_index[token].append(risk.id)
        if " " in name_lower.strip():
            phrase_index[name_lower].append(risk.id)
    return dict(single_word_index), dict(phrase_index)


def pass_a(
    artifacts: list[dict],
    nexus: AIAtlasNexus,
    index: tuple[dict[str, list[str]], dict[str, list[str]]] | None = None,
) -> list[tuple[str, str, float]]:
    """Returns (artifact_id, risk_id, score) for pairs with >=1 keyword match."""
    if index is None:
        index = build_keyword_index(nexus)
    single_word_index, phrase_index = index

    risk_token_counts = {
        risk.id: max(len(_tokenize(risk.name or "") | _tokenize(risk.id or "")), 1)
        for risk in nexus.get_all_risks()
    }

    candidates = []
    for artifact in artifacts:
        haystack = " ".join([
            artifact["name"].lower(),
            artifact["source_file"].lower(),
            artifact.get("content_summary", "").lower(),
        ])
        tokens = _tokenize(haystack)

        matched_risks: dict[str, int] = defaultdict(int)
        for token in tokens:
            for risk_id in single_word_index.get(token, ()):
                matched_risks[risk_id] += 1
        for phrase, risk_ids in phrase_index.items():
            if phrase in haystack:
                for risk_id in risk_ids:
                    matched_risks[risk_id] += 1

        for risk_id, count in matched_risks.items():
            score = min(count / risk_token_counts[risk_id], 1.0)
            candidates.append((artifact["id"], risk_id, score))

    return candidates
