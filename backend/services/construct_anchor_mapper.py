"""Construct Anchor Mapper — dimension-to-anchor resolution.

Maps evaluation dimensions to external evidence anchors using
keyword-based matching rules. Dimensions with no recognized anchor
are flagged as weakly anchored.

Used by the construct evidence anchoring pipeline (Cycle-026a).
"""

from __future__ import annotations

from backend.schemas.construct_anchor_schema import (
    AnchorClass,
    AnchorReference,
    EvaluationDimensionAnchor,
)


# ── Mapping Rules ────────────────────────────────────────────────────
#
# Each rule is a tuple of (keywords, anchor_class, anchor_id, rationale).
# A dimension matches a rule if ANY keyword appears in the lowercased
# dimension name.  A dimension may match multiple rules.

_MAPPING_RULES: list[tuple[list[str], AnchorClass, str, str]] = [
    # Code compilation / lint / test → deterministic_check
    (
        ["code", "compile", "lint", "test", "syntax", "type_check", "static_analysis"],
        AnchorClass.DETERMINISTIC_CHECK,
        "code_verification",
        "Deterministic code compilation, linting, or test-suite execution",
    ),
    # Benchmark prompt family → benchmark_dataset
    (
        ["benchmark", "eval_score", "humaneval", "mbpp", "mmlu", "hellaswag", "swe_bench"],
        AnchorClass.BENCHMARK_DATASET,
        "benchmark_suite",
        "Evaluation against a versioned benchmark dataset",
    ),
    # Accessibility / UI compliance → public_standard
    (
        ["accessibility", "accessible", "wcag", "aria", "a11y", "ui_compliance", "standard", "compliance"],
        AnchorClass.PUBLIC_STANDARD,
        "public_standard_check",
        "Verification against a published public standard (e.g. WCAG, ARIA APG)",
    ),
    # Real-world factual / expertise → live_external_evidence
    (
        ["factual", "real_world", "live", "external", "osint", "market_data", "regulatory"],
        AnchorClass.LIVE_EXTERNAL_EVIDENCE,
        "live_evidence_feed",
        "Grounded in live or regularly-updated external evidence sources",
    ),
    # ── Cycle-026b: Domain anchor expansion ──────────────────────────
    # Frontend / component quality → public_standard (React + Tailwind docs)
    (
        ["frontend", "react", "component", "tailwind", "css", "layout", "responsive", "ui_quality"],
        AnchorClass.PUBLIC_STANDARD,
        "frontend_standards",
        "Verification against React and Tailwind CSS official documentation",
    ),
    # Security / vulnerability → public_standard (OWASP Top 10 + CWE)
    (
        ["security", "vulnerability", "owasp", "cwe", "injection", "xss", "csrf", "auth_bypass"],
        AnchorClass.PUBLIC_STANDARD,
        "security_standards",
        "Verification against OWASP Top 10 and CWE weakness taxonomy",
    ),
    # Research / academic citation → benchmark_dataset (arXiv metadata)
    (
        ["research", "paper", "citation", "arxiv", "academic", "scholarly", "ml_method"],
        AnchorClass.BENCHMARK_DATASET,
        "research_metadata",
        "Evaluation against versioned arXiv ML metadata snapshots",
    ),
    # Research / live citation evidence → live_external_evidence (Semantic Scholar)
    (
        ["research", "paper", "citation", "scholarly", "semantic_scholar"],
        AnchorClass.LIVE_EXTERNAL_EVIDENCE,
        "research_evidence",
        "Grounded in live Semantic Scholar citation and paper metadata",
    ),
    # ── Cycle-026c: User Research + Journey Anchors ───────────────────
    # User research methodology → public_standard (GOV.UK Service Manual)
    (
        ["user_research", "hypothesis", "interview", "survey", "usability", "evidence_discipline", "confidence_label"],
        AnchorClass.PUBLIC_STANDARD,
        "user_research_methods",
        "Verification against GOV.UK Service Manual user research methodology",
    ),
    # Journey / flow patterns → public_standard (GOV.UK Design System patterns)
    (
        ["journey", "flow", "step_by_step", "task_list", "check_answers", "onboarding", "flow_extraction"],
        AnchorClass.PUBLIC_STANDARD,
        "journey_patterns",
        "Verification against GOV.UK Design System journey and flow patterns",
    ),
    # Recovery / validation / error → public_standard (GOV.UK validation guidance)
    (
        ["recovery", "validation", "error_handling", "error_message", "gap_analysis", "recovery_reasoning"],
        AnchorClass.PUBLIC_STANDARD,
        "recovery_guidance",
        "Verification against GOV.UK Design System validation and recovery guidance",
    ),
    # ── Cycle-037c: Security Domain Pack Anchors ────────────────────────
    # ATT&CK technique framework → public_standard (MITRE ATT&CK)
    (
        ["attack", "att_ck", "mitre", "technique", "tactic", "t1059", "t1566"],
        AnchorClass.PUBLIC_STANDARD,
        "attack_framework",
        "Verification against MITRE ATT&CK technique and tactic taxonomy",
    ),
    # Security skill corpus → public_standard (structured cybersecurity skills)
    (
        ["security_skill", "skill_corpus", "cybersecurity_skill", "workflow_verification"],
        AnchorClass.PUBLIC_STANDARD,
        "security_skill_corpus",
        "Verification against structured cybersecurity skill corpus with workflow verification",
    ),
    # ── Cycle-037d: Theatre Construct Anchors ─────────────────────────────
    # Settlement / oracle ground truth → live_external_evidence
    (
        ["settlement", "oracle", "ground_truth"],
        AnchorClass.LIVE_EXTERNAL_EVIDENCE,
        "theatre_oracle_settlement",
        "Settlement accuracy verified against oracle ground truth data",
    ),
    # Brier / calibration / ECE → deterministic_check
    (
        ["brier", "calibration", "ece"],
        AnchorClass.DETERMINISTIC_CHECK,
        "theatre_calibration",
        "Calibration metrics (Brier score, ECE) are arithmetically verifiable",
    ),
    # Position history / temporal analysis → deterministic_check
    (
        ["position_history", "temporal_analysis"],
        AnchorClass.DETERMINISTIC_CHECK,
        "theatre_state_machine",
        "Theatre state transitions and position history are deterministically verifiable",
    ),
    # Named oracles (USGS, EMSC, SWPC, DONKI, NOAA, IRIS, GFZ) → live_external_evidence
    (
        ["usgs", "emsc", "swpc", "donki", "noaa", "iris_dmc", "gfz"],
        AnchorClass.LIVE_EXTERNAL_EVIDENCE,
        "theatre_named_oracle",
        "Grounded in named public oracle data sources (USGS, EMSC, NOAA SWPC, NASA DONKI, GFZ)",
    ),
]


# ── Core API ─────────────────────────────────────────────────────────

def map_dimension_anchors(
    dimension: str,
    *,
    available_anchors: list[str] | None = None,
) -> EvaluationDimensionAnchor:
    """Map a single evaluation dimension to its anchor references.

    Uses keyword matching on the dimension name (case-insensitive) to
    resolve which anchor classes apply.  If ``available_anchors`` is
    provided, only anchors whose ``anchor_id`` appears in the list are
    included.

    Args:
        dimension: Evaluation dimension name (e.g. ``"code_quality"``).
        available_anchors: Optional allowlist of anchor IDs.  When set,
            matched anchors not in this list are excluded.

    Returns:
        An ``EvaluationDimensionAnchor`` with resolved anchors.
        If no rules match, ``weakly_anchored`` is ``True`` and
        ``anchors`` is empty.
    """
    dim_lower = dimension.lower()
    matched: list[AnchorReference] = []

    for keywords, anchor_class, anchor_id, rationale in _MAPPING_RULES:
        if any(kw in dim_lower for kw in keywords):
            # If caller constrained the available anchors, respect that
            if available_anchors is not None and anchor_id not in available_anchors:
                continue
            matched.append(
                AnchorReference(
                    anchor_class=anchor_class,
                    anchor_id=anchor_id,
                    rationale=rationale,
                )
            )

    weakly_anchored = len(matched) == 0

    return EvaluationDimensionAnchor(
        dimension=dimension,
        anchors=matched,
        weakly_anchored=weakly_anchored,
    )


def map_contract_anchors(
    dimensions: list[str],
) -> list[EvaluationDimensionAnchor]:
    """Map a full evaluation contract to anchor references.

    Iterates over a list of dimension names and resolves anchors for
    each.  Dimensions with no matching rules are returned with
    ``weakly_anchored=True`` and an empty ``anchors`` list.

    Args:
        dimensions: List of evaluation dimension names.

    Returns:
        List of ``EvaluationDimensionAnchor`` objects, one per
        input dimension, in the same order.
    """
    return [map_dimension_anchors(dim) for dim in dimensions]
