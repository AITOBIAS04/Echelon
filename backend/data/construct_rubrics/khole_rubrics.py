"""K-Hole construct rubrics — V1 structural scoring.

Domains: Intentional Descent, Resonance Navigation, Pipeline Orchestration, Source Discipline.
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


def score_intentional_descent(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Intentional Descent rubric: depth of research, source quality, technical accuracy."""
    depth_patterns = [
        r"deep.?dive|in.?depth|thorough|comprehensive",
        r"architecture|mechanism|protocol|specification",
        r"comparison|contrast|trade.?off|versus",
    ]
    source_patterns = [
        r"according.?to|source|reference|paper|spec",
        r"w3c|ieee|rfc|eip|standard",
    ]
    technical_patterns = [
        r"function|algorithm|formula|equation",
        r"parameter|variable|coefficient|threshold",
    ]

    depth_score = _ratio(_count_matches(output_text, depth_patterns), 2)
    source_score = _ratio(_count_matches(output_text, source_patterns), 1)
    technical_score = _ratio(_count_matches(output_text, technical_patterns), 1)

    return {
        "output_conformance": (depth_score + technical_score) / 2,
        "domain_accuracy": (depth_score + source_score) / 2,
    }


def score_resonance_navigation(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Resonance Navigation rubric: pattern recognition, theme synthesis, continuity."""
    pattern_patterns = [
        r"pattern|theme|recurring|thread",
        r"connection|relationship|link|overlap",
        r"synthesis|consolidat|aggregat",
    ]
    continuity_patterns = [
        r"previous|earlier|session|history",
        r"unresolved|open.?question|gap|remain",
    ]

    pattern_score = _ratio(_count_matches(output_text, pattern_patterns), 2)
    continuity_score = _ratio(_count_matches(output_text, continuity_patterns), 1)

    return {
        "consistency": (pattern_score + continuity_score) / 2,
        "domain_accuracy": pattern_score,
    }


def score_pipeline_orchestration(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Pipeline Orchestration rubric: stage definition, quality gates, artifact specification."""
    stage_patterns = [
        r"stage|phase|step|pipeline",
        r"input|output|artifact|deliverable",
        r"gate|checkpoint|validation|criteria",
    ]
    config_patterns = [
        r"config|parameter|setting|specification",
        r"depth|breadth|scope|requirement",
    ]

    stage_score = _ratio(_count_matches(output_text, stage_patterns), 2)
    config_score = _ratio(_count_matches(output_text, config_patterns), 1)

    return {
        "output_conformance": stage_score,
        "domain_accuracy": (stage_score + config_score) / 2,
    }


def score_source_discipline(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Source Discipline rubric: citation verification, fabrication detection, quality assessment."""
    audit_patterns = [
        r"verif|validat|confirm|check",
        r"citation|reference|source|origin",
        r"quality|reliab|credib|authoritat",
    ]
    fabrication_patterns = [
        r"fabricat|hallucin|invent|fake",
        r"unverifi|unconfirm|suspect|flag",
    ]

    audit_score = _ratio(_count_matches(output_text, audit_patterns), 2)
    fabrication_score = _ratio(_count_matches(output_text, fabrication_patterns), 1)

    return {
        "boundary_enforcement": (audit_score + fabrication_score) / 2,
        "domain_accuracy": audit_score,
    }


KHOLE_RUBRICS: dict[str, Callable] = {
    "Intentional Descent": score_intentional_descent,
    "Resonance Navigation": score_resonance_navigation,
    "Pipeline Orchestration": score_pipeline_orchestration,
    "Source Discipline": score_source_discipline,
}
