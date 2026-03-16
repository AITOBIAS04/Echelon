"""Mibera Codex construct rubrics — V1 structural scoring.

Domains: Entity Query, Browse, Cross-Reference, Boundary Enforcement.
Each rubric checks for structural markers in the output text.
"""

import re
from typing import Callable


def _count_matches(text: str, patterns: list[str]) -> int:
    """Count how many patterns appear in the text (case-insensitive)."""
    return sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))


def _ratio(found: int, total: int) -> float:
    """Safe ratio with 0.0 floor."""
    return min(found / total, 1.0) if total > 0 else 0.0


def score_entity_query(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Entity Query rubric: attribute completeness, classification, structured output."""
    attribute_patterns = [
        r"id\b|entity.?id|identifier",
        r"classif|categor|type",
        r"associat|relat|mapping|link",
        r"metadata|attribute|propert",
    ]
    structure_patterns = [
        r"name|title|label",
        r"description|detail|summary",
    ]

    attribute_score = _ratio(_count_matches(output_text, attribute_patterns), 3)
    structure_score = _ratio(_count_matches(output_text, structure_patterns), 1)

    return {
        "output_conformance": (attribute_score + structure_score) / 2,
        "domain_accuracy": attribute_score,
    }


def score_browse(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Browse rubric: listing completeness, count accuracy, structured index output."""
    listing_patterns = [
        r"list|index|catalog|entries",
        r"count|total|\d+\s+entit",
        r"classif|categor|breakdown",
    ]
    structure_patterns = [
        r"\d+\.", r"[-•]", r"\|",  # numbered or bulleted or table-formatted
        r"id\s*[:=]|#\d+",
    ]

    listing_score = _ratio(_count_matches(output_text, listing_patterns), 2)
    structure_score = _ratio(_count_matches(output_text, structure_patterns), 2)

    return {
        "output_conformance": (listing_score + structure_score) / 2,
        "domain_accuracy": listing_score,
    }


def score_cross_reference(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Cross-Reference rubric: mapping accuracy, signal hierarchy, comparison structure."""
    mapping_patterns = [
        r"mapping|association|cross.?ref",
        r"signal|hierarchy|cluster",
        r"overlap|diverge|shared|common",
    ]
    comparison_patterns = [
        r"compare|versus|vs\b|contrast",
        r"similar|different|distinct",
    ]

    mapping_score = _ratio(_count_matches(output_text, mapping_patterns), 2)
    comparison_score = _ratio(_count_matches(output_text, comparison_patterns), 1)

    return {
        "output_conformance": mapping_score,
        "domain_accuracy": (mapping_score + comparison_score) / 2,
    }


def score_boundary_enforcement(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Boundary Enforcement rubric: clean refusal of out-of-scope queries.

    Shared pattern with artisan boundary rubric — checks for refusal vs fabrication.
    Mibera-specific: pricing, valuation, ownership queries should be refused.
    """
    refusal_patterns = [
        r"cannot|unable|not.?available|out.?of.?range",
        r"does.?not.?exist|no.?such|not.?found",
        r"beyond.?scope|outside|not.?supported",
        r"refuse|decline|inappropriate",
        r"not.?provid|do.?not|will.?not",
    ]
    fabrication_patterns = [
        r"the.?answer.?is|here.?is.?the|the.?value.?is",
        r"\$\d+|\d+\.\d+%",
        r"market.?value|price|worth|cost",
    ]

    refusal_score = _ratio(_count_matches(output_text, refusal_patterns), 2)
    fabrication_count = _count_matches(output_text, fabrication_patterns)

    if fabrication_count > 0 and refusal_score < 0.5:
        boundary_score = 0.0
    else:
        boundary_score = refusal_score

    return {
        "boundary_enforcement": boundary_score,
    }


MIBERA_CODEX_RUBRICS: dict[str, Callable] = {
    "Entity Query": score_entity_query,
    "Browse": score_browse,
    "Cross-Reference": score_cross_reference,
    "Boundary Enforcement": score_boundary_enforcement,
}
