"""T0 Context Compiler -- deterministic world-view compilation.

Compiles AgentGenome + MarketState + AgentPosition into a frozen T0Context
dataclass. Zero inference cost. Same inputs always produce same output.
SHA-256 hash enables reproducibility verification.

Cycle-013, Sprint 1 -- Task 2.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Tuple

from backend.agents.genome import AgentGenome
from backend.market.lmsr import LMSREngine
from backend.market.positions import AgentPosition
from backend.market.state import MarketState


@dataclass(frozen=True)
class T0Context:
    """Frozen agent world-view. Deterministic, hashable, zero inference cost.

    All mutable data (lists) converted to tuples for immutability.
    context_hash is set after construction via object.__setattr__.
    """

    # --- Archetype Parameters (from genome) ---
    archetype: str
    risk_appetite: float
    evidence_sensitivity: float
    time_preference: float
    exploration_rate: float
    position_limit: float
    sabotage_propensity: float
    shield_propensity: float
    patience: int
    novelty_threshold: float

    # --- Market Context ---
    prices: Tuple[float, ...]
    phase: str
    outcome_labels: Tuple[str, ...]
    n_outcomes: int
    evidence_coverage_pct: float  # 0.0-1.0

    # --- Position State ---
    current_shares: Tuple[float, ...]
    net_cashflow: float
    available_balance: float

    # --- Theatre Rules ---
    committed_sources: Tuple[str, ...]
    resolution_date: str
    liquidity_b: float

    # --- Constraints ---
    max_position_pct: float
    max_drawdown_pct: float
    stop_loss_threshold: float

    # --- Hash (set post-construction) ---
    context_hash: str = ""


class ContextCompiler:
    """Compiles AgentGenome + MarketState + position into T0Context.

    All methods are static -- no instance state. Pure data transformation.
    """

    @staticmethod
    def compile(
        genome: AgentGenome,
        market: MarketState,
        position: AgentPosition,
        available_balance: float,
        evidence_coverage_pct: float = 0.0,
    ) -> T0Context:
        """Pure function: genome + market + position -> T0Context.

        Deterministic. Same inputs always produce the same T0Context.

        Args:
            genome: Agent genome with archetype parameters.
            market: Current market state (x vector, phase, labels).
            position: Agent's current position (shares, cashflow).
            available_balance: Agent's available cash balance.
            evidence_coverage_pct: Fraction of committed sources with evidence.

        Returns:
            Frozen T0Context with SHA-256 hash set.
        """
        prices = tuple(LMSREngine.prices(market.x, market.b))
        shares = (
            tuple(position.shares)
            if position.shares
            else tuple(0.0 for _ in range(market.n_outcomes))
        )

        ctx = T0Context(
            archetype=genome.archetype.value,
            risk_appetite=genome.risk_appetite,
            evidence_sensitivity=genome.evidence_sensitivity,
            time_preference=genome.time_preference,
            exploration_rate=genome.exploration_rate,
            position_limit=genome.position_limit,
            sabotage_propensity=genome.sabotage_propensity,
            shield_propensity=genome.shield_propensity,
            patience=genome.patience,
            novelty_threshold=genome.novelty_threshold,
            prices=prices,
            phase=market.phase.value,
            outcome_labels=tuple(market.outcome_labels),
            n_outcomes=market.n_outcomes,
            evidence_coverage_pct=evidence_coverage_pct,
            current_shares=shares,
            net_cashflow=position.net_cashflow,
            available_balance=available_balance,
            committed_sources=tuple(genome.committed_sources),
            resolution_date=genome.resolution_date or "",
            liquidity_b=market.b,
            max_position_pct=genome.max_position_pct,
            max_drawdown_pct=genome.max_drawdown_pct,
            stop_loss_threshold=genome.stop_loss_threshold,
        )

        # Compute hash (replace empty sentinel via object.__setattr__ on frozen)
        ctx_hash = ContextCompiler.compute_hash(ctx)
        object.__setattr__(ctx, "context_hash", ctx_hash)

        return ctx

    @staticmethod
    def compute_hash(ctx: T0Context) -> str:
        """SHA-256 hash of T0Context for reproducibility verification.

        Uses Echelon Canonical JSON v0: sorted keys, no whitespace.
        Excludes context_hash itself to avoid circular dependency.
        Every other field contributes to the hash.
        """
        hashable = {
            "archetype": ctx.archetype,
            "risk_appetite": ctx.risk_appetite,
            "evidence_sensitivity": ctx.evidence_sensitivity,
            "time_preference": ctx.time_preference,
            "exploration_rate": ctx.exploration_rate,
            "position_limit": ctx.position_limit,
            "sabotage_propensity": ctx.sabotage_propensity,
            "shield_propensity": ctx.shield_propensity,
            "patience": ctx.patience,
            "novelty_threshold": ctx.novelty_threshold,
            "prices": list(ctx.prices),
            "phase": ctx.phase,
            "outcome_labels": list(ctx.outcome_labels),
            "n_outcomes": ctx.n_outcomes,
            "evidence_coverage_pct": ctx.evidence_coverage_pct,
            "current_shares": list(ctx.current_shares),
            "net_cashflow": ctx.net_cashflow,
            "available_balance": ctx.available_balance,
            "committed_sources": list(ctx.committed_sources),
            "resolution_date": ctx.resolution_date,
            "liquidity_b": ctx.liquidity_b,
            "max_position_pct": ctx.max_position_pct,
            "max_drawdown_pct": ctx.max_drawdown_pct,
            "stop_loss_threshold": ctx.stop_loss_threshold,
        }
        canonical = json.dumps(hashable, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
