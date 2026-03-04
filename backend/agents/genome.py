"""AgentGenome -- Pydantic v2 model for Echelon agent archetypes.

Defines the complete T0 context specification: 8 behavioural parameters,
variant modifiers, Theatre context, position constraints, and decision
routing config. Frozen after construction for auditability.

Cycle-013, Sprint 1 -- Task 1.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EchelonArchetype(str, Enum):
    """Six core agent archetypes from System Bible v13 Section VIII."""

    SHARK = "SHARK"
    SPY = "SPY"
    DIPLOMAT = "DIPLOMAT"
    SABOTEUR = "SABOTEUR"
    WHALE = "WHALE"
    DEGEN = "DEGEN"


class TierProfile(BaseModel):
    """Tier routing configuration for multi-tier inference."""

    model_config = {"frozen": True}

    active_tiers: List[str] = Field(default_factory=list)
    default_tier: str = "T1"
    escalation_rules: List[Dict] = Field(default_factory=list)
    cost_profile: str = ""
    max_inference_budget_per_market: float = Field(default=0.10, ge=0.0)


class DecisionPolicy(BaseModel):
    """Decision routing policy: method, temperature, bias, strategy."""

    model_config = {"frozen": True}

    method: str = "SOFTMAX_Q_VALUE"
    temperature: float = Field(default=0.5, ge=0.0)
    bias_vector: Dict[str, float] = Field(default_factory=dict)
    strategy_rules: List[str] = Field(default_factory=list)


class ParadoxBehaviour(BaseModel):
    """Paradox Engine response configuration."""

    model_config = {"frozen": True}

    logic_gap_threshold: float = Field(default=0.20, ge=0.0, le=1.0)
    response_action: str = "EXTRACT"
    extraction_cost_ceiling: float = Field(default=0.25, ge=0.0)
    coalition_willingness: float = Field(default=0.15, ge=0.0, le=1.0)
    circuit_breaker_behaviour: str = "REDUCE"


class InquiryClassAffinity(BaseModel):
    """Affinity scores for each inquiry class (0-1)."""

    model_config = {"frozen": True}

    counterfactual: float = Field(default=0.5, ge=0.0, le=1.0)
    investigative: float = Field(default=0.5, ge=0.0, le=1.0)
    inspection: float = Field(default=0.5, ge=0.0, le=1.0)
    survey: float = Field(default=0.5, ge=0.0, le=1.0)
    scrutiny: float = Field(default=0.5, ge=0.0, le=1.0)


class SuccessMetrics(BaseModel):
    """Target performance metrics for this genome."""

    model_config = {"frozen": True}

    brier_score_target: float = Field(default=0.20, ge=0.0)
    ece_bound: float = Field(default=0.10, ge=0.0)
    pnl_expectation: str = "PROFITABLE"
    consistency_threshold: float = Field(default=0.80, ge=0.0, le=1.0)
    position_size_variance_max: float = Field(default=0.20, ge=0.0)
    fork_choice_consistency_min: float = Field(default=0.80, ge=0.0, le=1.0)


class AgentGenome(BaseModel):
    """Complete T0 context specification for an Echelon agent.

    Pydantic v2 model. Frozen after construction for auditability.
    8 archetype parameters, variant overrides, Theatre context,
    position constraints, and decision routing config.
    """

    model_config = {"frozen": True}

    # --- Identity ---
    archetype: EchelonArchetype
    variant: Optional[str] = None  # e.g., "MEGALODON"
    genome_version: str = "1.0.0"
    name: Optional[str] = None
    agent_id: Optional[str] = None
    lineage: str = "GENESIS"
    description: Optional[str] = None

    # --- 8 Archetype Parameters ---
    risk_appetite: float = Field(ge=0.0, le=1.0, description="rho")
    evidence_sensitivity: float = Field(ge=0.0, le=1.0, description="epsilon")
    time_preference: float = Field(ge=0.0, le=1.0, description="gamma")
    exploration_rate: float = Field(ge=0.0, le=1.0, description="xi")
    position_limit: float = Field(gt=0, description="L -- max position in shares")
    sabotage_propensity: float = Field(ge=0.0, le=1.0, description="sigma")
    shield_propensity: float = Field(ge=0.0, le=1.0, description="phi")
    patience: int = Field(ge=1, description="pi -- ticks between evaluations")

    # --- Variant Overrides ---
    variant_overrides: Dict[str, float] = Field(default_factory=dict)

    # --- Theatre Context (injected at spawn) ---
    committed_sources: List[str] = Field(default_factory=list)
    outcome_labels: List[str] = Field(default_factory=list)
    resolution_date: Optional[str] = None
    liquidity_b: Optional[float] = None

    # --- Position Constraints ---
    max_position_pct: float = Field(default=0.10, ge=0.0, le=1.0)
    max_drawdown_pct: float = Field(default=0.20, ge=0.0, le=1.0)
    stop_loss_threshold: float = Field(default=0.15, ge=0.0, le=1.0)

    # --- Extended Genome Sections (YAML-driven) ---
    tier_profile: Optional[TierProfile] = None
    decision_policy: Optional[DecisionPolicy] = None
    paradox_behaviour: Optional[ParadoxBehaviour] = None
    inquiry_class_affinity: Optional[InquiryClassAffinity] = None
    success_metrics: Optional[SuccessMetrics] = None

    # --- Decision Routing ---
    novelty_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Confidence below this triggers T3 escalation",
    )


# ===================================================================
# Archetype Behaviour Matrix (PRD Section 4.1)
# ===================================================================

ARCHETYPE_DEFAULTS: Dict[EchelonArchetype, dict] = {
    EchelonArchetype.SHARK: {
        "risk_appetite": 0.85,
        "evidence_sensitivity": 0.70,
        "time_preference": 0.95,
        "exploration_rate": 0.15,
        "position_limit": 10_000,
        "sabotage_propensity": 0.30,
        "shield_propensity": 0.10,
        "patience": 30,
    },
    EchelonArchetype.SPY: {
        "risk_appetite": 0.40,
        "evidence_sensitivity": 0.90,
        "time_preference": 0.98,
        "exploration_rate": 0.40,
        "position_limit": 2_500,
        "sabotage_propensity": 0.05,
        "shield_propensity": 0.15,
        "patience": 120,
    },
    EchelonArchetype.DIPLOMAT: {
        "risk_appetite": 0.30,
        "evidence_sensitivity": 0.50,
        "time_preference": 0.99,
        "exploration_rate": 0.20,
        "position_limit": 5_000,
        "sabotage_propensity": 0.02,
        "shield_propensity": 0.85,
        "patience": 60,
    },
    EchelonArchetype.SABOTEUR: {
        "risk_appetite": 0.95,
        "evidence_sensitivity": 0.30,
        "time_preference": 0.90,
        "exploration_rate": 0.60,
        "position_limit": 7_500,
        "sabotage_propensity": 0.95,
        "shield_propensity": 0.05,
        "patience": 45,
    },
    EchelonArchetype.WHALE: {
        "risk_appetite": 0.70,
        "evidence_sensitivity": 0.55,
        "time_preference": 0.92,
        "exploration_rate": 0.10,
        "position_limit": 25_000,
        "sabotage_propensity": 0.15,
        "shield_propensity": 0.30,
        "patience": 90,
    },
    EchelonArchetype.DEGEN: {
        "risk_appetite": 1.00,
        "evidence_sensitivity": 0.15,
        "time_preference": 0.85,
        "exploration_rate": 0.95,
        "position_limit": 1_000,
        "sabotage_propensity": 0.50,
        "shield_propensity": 0.02,
        "patience": 10,
    },
}


VARIANT_OVERRIDES: Dict[str, dict] = {
    "MEGALODON": {
        "risk_appetite": 0.90,
        "evidence_sensitivity": 0.80,
        "position_limit": 15_000,
        "novelty_threshold": 0.6,
    },
}


# ===================================================================
# Factory Functions
# ===================================================================


def create_genome(
    archetype: EchelonArchetype,
    variant: Optional[str] = None,
    **overrides: float,
) -> AgentGenome:
    """Factory: create a genome from the Behaviour Matrix with optional overrides.

    Applies defaults for the archetype, then variant overrides, then caller
    overrides. Returns a frozen AgentGenome.
    """
    defaults = ARCHETYPE_DEFAULTS[archetype]
    params: dict = {**defaults}
    if variant and variant in VARIANT_OVERRIDES:
        params.update(VARIANT_OVERRIDES[variant])
    params.update(overrides)
    return AgentGenome(
        archetype=archetype,
        variant=variant,
        **params,
    )


def create_shark_genome(**overrides: float) -> AgentGenome:
    """Create a Shark archetype genome with default parameters."""
    return create_genome(EchelonArchetype.SHARK, **overrides)


def create_spy_genome(**overrides: float) -> AgentGenome:
    """Create a Spy archetype genome with default parameters."""
    return create_genome(EchelonArchetype.SPY, **overrides)


def create_diplomat_genome(**overrides: float) -> AgentGenome:
    """Create a Diplomat archetype genome with default parameters."""
    return create_genome(EchelonArchetype.DIPLOMAT, **overrides)


def create_saboteur_genome(**overrides: float) -> AgentGenome:
    """Create a Saboteur archetype genome with default parameters."""
    return create_genome(EchelonArchetype.SABOTEUR, **overrides)


def create_whale_genome(**overrides: float) -> AgentGenome:
    """Create a Whale archetype genome with default parameters."""
    return create_genome(EchelonArchetype.WHALE, **overrides)


def create_degen_genome(**overrides: float) -> AgentGenome:
    """Create a Degen archetype genome with default parameters."""
    return create_genome(EchelonArchetype.DEGEN, **overrides)


def create_megalodon_genome(**overrides: float) -> AgentGenome:
    """Create a MEGALODON variant Shark genome."""
    return create_genome(EchelonArchetype.SHARK, variant="MEGALODON", **overrides)
