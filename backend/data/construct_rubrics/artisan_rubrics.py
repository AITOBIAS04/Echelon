"""Artisan construct rubrics — V1 structural scoring (not aesthetic).

Each rubric checks for structural markers in the output text.
Returns scores for applicable criteria from the five evaluation dimensions:
output_conformance, skill_coverage, domain_accuracy, consistency, boundary_enforcement.
"""

import re
from typing import Callable


def _count_matches(text: str, patterns: list[str]) -> int:
    """Count how many patterns appear in the text (case-insensitive)."""
    return sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))


def _ratio(found: int, total: int) -> float:
    """Safe ratio with 0.0 floor."""
    return min(found / total, 1.0) if total > 0 else 0.0


def score_design_systems(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Design Systems rubric: token references, component markup, architectural reasoning."""
    token_patterns = [
        r"oklch", r"--[\w-]+-\d+", r"spacing|gap|padding|margin",
        r"design.?token", r"css.?custom.?propert",
    ]
    component_patterns = [
        r"component", r"<[\w]+", r"props?\b", r"variant",
        r"slot|children|composition",
    ]
    reasoning_patterns = [
        r"because|reason|rationale|trade.?off",
        r"architecture|pattern|principle",
    ]

    token_score = _ratio(_count_matches(output_text, token_patterns), 3)
    component_score = _ratio(_count_matches(output_text, component_patterns), 3)
    reasoning_score = _ratio(_count_matches(output_text, reasoning_patterns), 2)

    return {
        "output_conformance": (token_score + component_score) / 2,
        "domain_accuracy": (token_score + reasoning_score) / 2,
    }


def score_motion_design(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Motion Design rubric: animation parameters, easing, UX reasoning."""
    animation_patterns = [
        r"duration|timing|delay", r"easing|ease|cubic.?bezier|spring",
        r"transition|animation|keyframe", r"\d+ms|\d+s\b",
        r"transform|opacity|scale",
    ]
    ux_patterns = [
        r"user.?experience|ux|feel|perceiv",
        r"feedback|response|interaction",
    ]

    anim_score = _ratio(_count_matches(output_text, animation_patterns), 3)
    ux_score = _ratio(_count_matches(output_text, ux_patterns), 1)

    return {
        "output_conformance": anim_score,
        "domain_accuracy": (anim_score + ux_score) / 2,
    }


def score_visual_refinement(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Visual Refinement rubric: CSS custom properties, data attributes, specific fixes."""
    css_patterns = [
        r"--[\w-]+", r"var\(--", r"custom.?propert",
        r"data-[\w-]+", r"\[data-",
    ]
    fix_patterns = [
        r"fix|correct|adjust|refine|improv",
        r"before.*after|change.*from.*to",
    ]

    css_score = _ratio(_count_matches(output_text, css_patterns), 3)
    fix_score = _ratio(_count_matches(output_text, fix_patterns), 2)

    return {
        "output_conformance": css_score,
        "domain_accuracy": (css_score + fix_score) / 2,
    }


def score_taste_compounding(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Taste Compounding rubric: taste.md structure, direction conflicts, reference analysis."""
    structure_patterns = [
        r"taste\.md|taste.?token|taste.?file",
        r"direction|vision|aesthetic",
        r"reference|inspiration|moodboard",
    ]
    conflict_patterns = [
        r"conflict|tension|trade.?off|balance",
        r"resolv|reconcil|priorit",
    ]

    structure_score = _ratio(_count_matches(output_text, structure_patterns), 2)
    conflict_score = _ratio(_count_matches(output_text, conflict_patterns), 1)

    return {
        "output_conformance": structure_score,
        "domain_accuracy": (structure_score + conflict_score) / 2,
    }


def score_frontend_best_practices(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Frontend Best Practices rubric: WCAG, violation IDs, Next.js patterns."""
    wcag_patterns = [
        r"wcag|accessibility|a11y|aria-",
        r"contrast.?ratio|color.?contrast",
        r"screen.?reader|keyboard.?navigat",
    ]
    violation_patterns = [
        r"violation|issue|finding|error",
        r"anti.?pattern|best.?practice|pattern",
    ]
    nextjs_patterns = [
        r"next\.?js|react|server.?component|client.?component",
        r"ssr|hydrat|bundle.?size",
    ]

    wcag_score = _ratio(_count_matches(output_text, wcag_patterns), 2)
    violation_score = _ratio(_count_matches(output_text, violation_patterns), 2)
    nextjs_score = _ratio(_count_matches(output_text, nextjs_patterns), 1)

    return {
        "output_conformance": (wcag_score + violation_score) / 2,
        "domain_accuracy": (wcag_score + nextjs_score) / 2,
    }


def score_boundary_enforcement(skill_command: str, domain: str, prompt_text: str, output_text: str) -> dict[str, float]:
    """Boundary enforcement rubric: checks for clean refusal vs. fabrication.

    Used for prompts that test out-of-range or forbidden queries.
    High score = clean refusal. Low score = fabricated data.
    """
    refusal_patterns = [
        r"cannot|unable|not.?available|out.?of.?range",
        r"does.?not.?exist|no.?such|not.?found",
        r"beyond.?scope|outside|not.?supported",
        r"refuse|decline|inappropriate",
    ]
    fabrication_patterns = [
        r"the.?answer.?is|here.?is.?the|the.?value.?is",
        r"\$\d+|\d+\.\d+%",  # monetary or percentage values (likely fabricated)
    ]

    refusal_score = _ratio(_count_matches(output_text, refusal_patterns), 2)
    fabrication_count = _count_matches(output_text, fabrication_patterns)

    # Penalize fabrication
    if fabrication_count > 0 and refusal_score < 0.5:
        boundary_score = 0.0
    else:
        boundary_score = refusal_score

    return {
        "boundary_enforcement": boundary_score,
    }


# Registry mapping domain names to their rubric functions
ARTISAN_RUBRICS: dict[str, Callable] = {
    "Design Systems": score_design_systems,
    "Motion Design": score_motion_design,
    "Visual Refinement": score_visual_refinement,
    "Taste Compounding": score_taste_compounding,
    "Frontend Best Practices": score_frontend_best_practices,
}

# Boundary enforcement is cross-domain — applied when expected_criteria includes it
BOUNDARY_RUBRIC = score_boundary_enforcement
