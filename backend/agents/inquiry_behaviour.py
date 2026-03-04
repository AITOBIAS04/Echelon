"""Inquiry-class-specific behaviour adaptation for agent archetypes.

Each archetype adapts its decision profile per inquiry class as defined in
System Bible v13 section X.4 (domain adaptation matrix).

Cycle-014, Sprint 2 — Task 3.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class InquiryProfile:
    """Inquiry-class-specific behaviour modifiers for an archetype.

    Applied by the RulesEngine before archetype dispatch:
    - evidence_sensitivity is scaled by evidence_weight_modifier
    - risk_appetite is scaled by momentum_weight_modifier
    - pattern_name is overridden in T1Decision
    - reasoning_trace includes action_description
    """

    pattern_name_override: str
    evidence_weight_modifier: float
    momentum_weight_modifier: float
    action_description: str


# Default profile for unknown archetype/inquiry_class combinations
DEFAULT_PROFILE = InquiryProfile(
    pattern_name_override="",
    evidence_weight_modifier=1.0,
    momentum_weight_modifier=1.0,
    action_description="Default behaviour — no inquiry-specific adaptation",
)


# 30 profiles: 6 archetypes x 5 inquiry classes
# Keys: (archetype, inquiry_class) -> InquiryProfile
INQUIRY_PROFILES: Dict[Tuple[str, str], InquiryProfile] = {
    # =========================================================================
    # SHARK — momentum exploitation
    # =========================================================================
    ("SHARK", "COUNTERFACTUAL"): InquiryProfile(
        pattern_name_override="momentum_exploitation",
        evidence_weight_modifier=1.0,
        momentum_weight_modifier=1.0,
        action_description="Momentum play: ride simulation divergence signals",
    ),
    ("SHARK", "INVESTIGATIVE"): InquiryProfile(
        pattern_name_override="evidence_front_running",
        evidence_weight_modifier=1.5,
        momentum_weight_modifier=0.7,
        action_description="Evidence front-running: trading ahead of evidence arrival",
    ),
    ("SHARK", "INSPECTION"): InquiryProfile(
        pattern_name_override="rapid_certification",
        evidence_weight_modifier=1.2,
        momentum_weight_modifier=0.9,
        action_description="Rapid certification: fast position on inspection outcome",
    ),
    ("SHARK", "SURVEY"): InquiryProfile(
        pattern_name_override="sentiment_tracking",
        evidence_weight_modifier=0.6,
        momentum_weight_modifier=1.4,
        action_description="Sentiment tracking: ride opinion momentum",
    ),
    ("SHARK", "SCRUTINY"): InquiryProfile(
        pattern_name_override="short_unverified",
        evidence_weight_modifier=1.3,
        momentum_weight_modifier=1.1,
        action_description="Short-selling unverified: bet against unsubstantiated claims",
    ),

    # =========================================================================
    # SPY — intel arbitrage
    # =========================================================================
    ("SPY", "COUNTERFACTUAL"): InquiryProfile(
        pattern_name_override="intel_arbitrage",
        evidence_weight_modifier=1.0,
        momentum_weight_modifier=1.0,
        action_description="OSINT intel: trade on real-world intelligence signals",
    ),
    ("SPY", "INVESTIGATIVE"): InquiryProfile(
        pattern_name_override="primary_discovery",
        evidence_weight_modifier=1.8,
        momentum_weight_modifier=0.5,
        action_description="Primary discovery: first-mover on new evidence",
    ),
    ("SPY", "INSPECTION"): InquiryProfile(
        pattern_name_override="audit_trail",
        evidence_weight_modifier=1.5,
        momentum_weight_modifier=0.6,
        action_description="Audit trail: trade on inspection evidence completeness",
    ),
    ("SPY", "SURVEY"): InquiryProfile(
        pattern_name_override="opinion_mining",
        evidence_weight_modifier=0.7,
        momentum_weight_modifier=1.0,
        action_description="Opinion mining: detect sentiment shifts before consensus",
    ),
    ("SPY", "SCRUTINY"): InquiryProfile(
        pattern_name_override="deep_verification",
        evidence_weight_modifier=1.7,
        momentum_weight_modifier=0.5,
        action_description="Deep verification: trade on verified/falsified evidence depth",
    ),

    # =========================================================================
    # DIPLOMAT — stability maintenance
    # =========================================================================
    ("DIPLOMAT", "COUNTERFACTUAL"): InquiryProfile(
        pattern_name_override="stability_maintenance",
        evidence_weight_modifier=1.0,
        momentum_weight_modifier=1.0,
        action_description="Treaty enforcement: maintain equilibrium across scenarios",
    ),
    ("DIPLOMAT", "INVESTIGATIVE"): InquiryProfile(
        pattern_name_override="source_corroboration",
        evidence_weight_modifier=1.3,
        momentum_weight_modifier=0.7,
        action_description="Source corroboration: stabilise around corroborated evidence",
    ),
    ("DIPLOMAT", "INSPECTION"): InquiryProfile(
        pattern_name_override="compliance_mediation",
        evidence_weight_modifier=1.1,
        momentum_weight_modifier=0.8,
        action_description="Compliance mediation: smooth inspection outcome volatility",
    ),
    ("DIPLOMAT", "SURVEY"): InquiryProfile(
        pattern_name_override="consensus_building",
        evidence_weight_modifier=0.8,
        momentum_weight_modifier=1.1,
        action_description="Consensus building: push market toward opinion median",
    ),
    ("DIPLOMAT", "SCRUTINY"): InquiryProfile(
        pattern_name_override="dispute_resolution",
        evidence_weight_modifier=1.2,
        momentum_weight_modifier=0.8,
        action_description="Dispute resolution: balance claim vs counter-evidence",
    ),

    # =========================================================================
    # SABOTEUR — chaos creation
    # =========================================================================
    ("SABOTEUR", "COUNTERFACTUAL"): InquiryProfile(
        pattern_name_override="chaos_creation",
        evidence_weight_modifier=1.0,
        momentum_weight_modifier=1.0,
        action_description="Chaos creation: disrupt counterfactual convergence",
    ),
    ("SABOTEUR", "INVESTIGATIVE"): InquiryProfile(
        pattern_name_override="evidence_spoofing",
        evidence_weight_modifier=0.4,
        momentum_weight_modifier=1.3,
        action_description="Evidence spoofing: trade against evidence consensus",
    ),
    ("SABOTEUR", "INSPECTION"): InquiryProfile(
        pattern_name_override="compliance_disruption",
        evidence_weight_modifier=0.5,
        momentum_weight_modifier=1.1,
        action_description="Compliance disruption: challenge inspection certainty",
    ),
    ("SABOTEUR", "SURVEY"): InquiryProfile(
        pattern_name_override="opinion_manipulation",
        evidence_weight_modifier=0.3,
        momentum_weight_modifier=1.4,
        action_description="Opinion manipulation: distort survey consensus",
    ),
    ("SABOTEUR", "SCRUTINY"): InquiryProfile(
        pattern_name_override="claim_challenge",
        evidence_weight_modifier=0.6,
        momentum_weight_modifier=1.2,
        action_description="Claim challenge: amplify counter-evidence signals",
    ),

    # =========================================================================
    # WHALE — conviction accumulation
    # =========================================================================
    ("WHALE", "COUNTERFACTUAL"): InquiryProfile(
        pattern_name_override="conviction_accumulation",
        evidence_weight_modifier=1.0,
        momentum_weight_modifier=1.0,
        action_description="Conviction accumulation: large positions on scenario evidence",
    ),
    ("WHALE", "INVESTIGATIVE"): InquiryProfile(
        pattern_name_override="evidence_conviction",
        evidence_weight_modifier=1.6,
        momentum_weight_modifier=0.6,
        action_description="Evidence conviction: accumulate on corroborated intelligence",
    ),
    ("WHALE", "INSPECTION"): InquiryProfile(
        pattern_name_override="certification_conviction",
        evidence_weight_modifier=1.4,
        momentum_weight_modifier=0.7,
        action_description="Certification conviction: accumulate on complete inspections",
    ),
    ("WHALE", "SURVEY"): InquiryProfile(
        pattern_name_override="consensus_conviction",
        evidence_weight_modifier=0.8,
        momentum_weight_modifier=1.2,
        action_description="Consensus conviction: accumulate on clear opinion trends",
    ),
    ("WHALE", "SCRUTINY"): InquiryProfile(
        pattern_name_override="audit_conviction",
        evidence_weight_modifier=1.5,
        momentum_weight_modifier=0.7,
        action_description="Audit conviction: accumulate on verified claims",
    ),

    # =========================================================================
    # DEGEN — random exploration
    # =========================================================================
    ("DEGEN", "COUNTERFACTUAL"): InquiryProfile(
        pattern_name_override="random_exploration",
        evidence_weight_modifier=1.0,
        momentum_weight_modifier=1.0,
        action_description="Random exploration: explore counterfactual price space",
    ),
    ("DEGEN", "INVESTIGATIVE"): InquiryProfile(
        pattern_name_override="evidence_gambling",
        evidence_weight_modifier=0.9,
        momentum_weight_modifier=1.0,
        action_description="Evidence gambling: speculate on investigation outcomes",
    ),
    ("DEGEN", "INSPECTION"): InquiryProfile(
        pattern_name_override="inspection_lottery",
        evidence_weight_modifier=0.8,
        momentum_weight_modifier=1.0,
        action_description="Inspection lottery: random bets on inspection results",
    ),
    ("DEGEN", "SURVEY"): InquiryProfile(
        pattern_name_override="opinion_roulette",
        evidence_weight_modifier=0.5,
        momentum_weight_modifier=1.3,
        action_description="Opinion roulette: random trades in opinion markets",
    ),
    ("DEGEN", "SCRUTINY"): InquiryProfile(
        pattern_name_override="audit_gambling",
        evidence_weight_modifier=0.8,
        momentum_weight_modifier=1.1,
        action_description="Audit gambling: speculate on claim outcomes",
    ),
}


class InquiryBehaviourAdapter:
    """Adapts archetype decision profiles per inquiry class.

    Does NOT replace the rules engine. Provides modifiers that the
    rules engine applies before archetype-specific dispatch.
    """

    @staticmethod
    def get_profile(archetype: str, inquiry_class: str) -> InquiryProfile:
        """Get the inquiry-specific behaviour profile for an archetype.

        Args:
            archetype: Agent archetype (SHARK, SPY, etc.).
            inquiry_class: Inquiry class (COUNTERFACTUAL, INVESTIGATIVE, etc.).

        Returns:
            InquiryProfile with modifiers. DEFAULT_PROFILE for unknown combos.
        """
        key = (archetype.upper().strip(), inquiry_class.upper().strip())
        return INQUIRY_PROFILES.get(key, DEFAULT_PROFILE)
