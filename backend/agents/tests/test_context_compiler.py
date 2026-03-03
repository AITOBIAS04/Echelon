"""Tests for AgentGenome and T0 Context Compiler.

Covers genome construction, all 6 archetypes, variant overrides,
frozen enforcement, JSON round-trip, T0 compilation, determinism,
and hash stability.

Cycle-013, Sprint 1 -- Task 7.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.agents.genome import (
    ARCHETYPE_DEFAULTS,
    VARIANT_OVERRIDES,
    AgentGenome,
    EchelonArchetype,
    create_degen_genome,
    create_diplomat_genome,
    create_genome,
    create_megalodon_genome,
    create_saboteur_genome,
    create_shark_genome,
    create_spy_genome,
    create_whale_genome,
)
from backend.agents.context_compiler import ContextCompiler, T0Context
from backend.market.positions import AgentPosition
from backend.market.state import MarketPhase, MarketState


# ===================================================================
# Fixtures
# ===================================================================


def _make_market(
    n_outcomes: int = 3,
    b: float = 100.0,
    phase: MarketPhase = MarketPhase.TRADING,
) -> MarketState:
    """Create a test market with uniform initial state."""
    return MarketState(
        market_id="mkt_test",
        theatre_id="theatre_test",
        b=b,
        n_outcomes=n_outcomes,
        outcome_labels=[f"outcome_{i}" for i in range(n_outcomes)],
        x=[0.0] * n_outcomes,
        phase=phase,
    )


def _make_position(
    agent_id: str = "agent_test",
    market_id: str = "mkt_test",
    n_outcomes: int = 3,
) -> AgentPosition:
    """Create a zero-filled test position."""
    return AgentPosition(
        agent_id=agent_id,
        market_id=market_id,
        shares=[0.0] * n_outcomes,
    )


# ===================================================================
# Genome Tests
# ===================================================================


class TestAgentGenome:
    """Tests for AgentGenome Pydantic v2 model."""

    @pytest.mark.parametrize("archetype", list(EchelonArchetype))
    def test_all_archetype_defaults_validate(self, archetype: EchelonArchetype) -> None:
        """All 6 default genomes validate successfully."""
        genome = create_genome(archetype)
        assert genome.archetype == archetype
        assert genome.genome_version == "1.0.0"
        # Verify all 8 parameters are set
        defaults = ARCHETYPE_DEFAULTS[archetype]
        assert genome.risk_appetite == defaults["risk_appetite"]
        assert genome.evidence_sensitivity == defaults["evidence_sensitivity"]
        assert genome.time_preference == defaults["time_preference"]
        assert genome.exploration_rate == defaults["exploration_rate"]
        assert genome.position_limit == defaults["position_limit"]
        assert genome.sabotage_propensity == defaults["sabotage_propensity"]
        assert genome.shield_propensity == defaults["shield_propensity"]
        assert genome.patience == defaults["patience"]

    def test_megalodon_variant_overrides(self) -> None:
        """MEGALODON variant applies overrides on top of Shark defaults."""
        genome = create_megalodon_genome()
        assert genome.archetype == EchelonArchetype.SHARK
        assert genome.variant == "MEGALODON"
        # Overridden values
        assert genome.risk_appetite == 0.90
        assert genome.evidence_sensitivity == 0.80
        assert genome.position_limit == 15_000
        assert genome.novelty_threshold == 0.6
        # Non-overridden values come from Shark defaults
        assert genome.time_preference == ARCHETYPE_DEFAULTS[EchelonArchetype.SHARK]["time_preference"]
        assert genome.patience == ARCHETYPE_DEFAULTS[EchelonArchetype.SHARK]["patience"]

    def test_frozen_enforcement(self) -> None:
        """Frozen genome cannot be mutated after construction."""
        genome = create_shark_genome()
        with pytest.raises(ValidationError):
            genome.risk_appetite = 0.99  # type: ignore[misc]

    def test_invalid_parameter_range_rejected(self) -> None:
        """Pydantic v2 rejects risk_appetite > 1.0."""
        with pytest.raises(ValidationError):
            AgentGenome(
                archetype=EchelonArchetype.SHARK,
                risk_appetite=1.5,
                evidence_sensitivity=0.5,
                time_preference=0.9,
                exploration_rate=0.1,
                position_limit=1000,
                sabotage_propensity=0.1,
                shield_propensity=0.1,
                patience=10,
            )

    def test_json_round_trip(self) -> None:
        """JSON serialisation round-trip produces identical genome."""
        genome = create_megalodon_genome()
        data = genome.model_dump(mode="json")
        restored = AgentGenome(**data)
        assert restored == genome
        assert restored.archetype == genome.archetype
        assert restored.variant == genome.variant

    def test_factory_override_chain(self) -> None:
        """Caller overrides take precedence over variant and archetype defaults."""
        genome = create_genome(
            EchelonArchetype.SHARK,
            variant="MEGALODON",
            risk_appetite=0.50,  # Override MEGALODON's 0.90
        )
        assert genome.risk_appetite == 0.50  # Caller override wins
        assert genome.evidence_sensitivity == 0.80  # MEGALODON override
        assert genome.time_preference == 0.95  # Shark default

    def test_convenience_factory_functions(self) -> None:
        """All convenience factory functions create correct archetypes."""
        assert create_shark_genome().archetype == EchelonArchetype.SHARK
        assert create_spy_genome().archetype == EchelonArchetype.SPY
        assert create_diplomat_genome().archetype == EchelonArchetype.DIPLOMAT
        assert create_saboteur_genome().archetype == EchelonArchetype.SABOTEUR
        assert create_whale_genome().archetype == EchelonArchetype.WHALE
        assert create_degen_genome().archetype == EchelonArchetype.DEGEN


# ===================================================================
# Context Compiler Tests
# ===================================================================


class TestContextCompiler:
    """Tests for T0 Context Compiler."""

    def test_deterministic_output(self) -> None:
        """Same inputs always produce same T0Context (including hash)."""
        genome = create_shark_genome()
        market = _make_market()
        position = _make_position()
        balance = 1000.0

        ctx1 = ContextCompiler.compile(genome, market, position, balance)
        ctx2 = ContextCompiler.compile(genome, market, position, balance)

        assert ctx1 == ctx2
        assert ctx1.context_hash == ctx2.context_hash
        assert len(ctx1.context_hash) == 64  # SHA-256 hex

    def test_hash_stability_across_calls(self) -> None:
        """Hash is stable across multiple compile calls."""
        genome = create_diplomat_genome()
        market = _make_market()
        position = _make_position()

        hashes = set()
        for _ in range(10):
            ctx = ContextCompiler.compile(genome, market, position, 500.0)
            hashes.add(ctx.context_hash)

        assert len(hashes) == 1  # All hashes identical

    @pytest.mark.parametrize("archetype", list(EchelonArchetype))
    def test_all_archetypes_compile(self, archetype: EchelonArchetype) -> None:
        """All 6 archetype genomes compile correctly into T0Context."""
        genome = create_genome(archetype)
        market = _make_market()
        position = _make_position()

        ctx = ContextCompiler.compile(genome, market, position, 1000.0)

        assert ctx.archetype == archetype.value
        assert ctx.risk_appetite == genome.risk_appetite
        assert ctx.n_outcomes == 3
        assert len(ctx.prices) == 3
        assert ctx.context_hash != ""

    def test_position_state_propagation(self) -> None:
        """Position state (shares, cashflow, balance) propagates correctly."""
        genome = create_whale_genome()
        market = _make_market()
        position = AgentPosition(
            agent_id="agent_whale",
            market_id="mkt_test",
            shares=[10.0, 5.0, 0.0],
            net_cashflow=150.0,
        )

        ctx = ContextCompiler.compile(genome, market, position, 850.0)

        assert ctx.current_shares == (10.0, 5.0, 0.0)
        assert ctx.net_cashflow == 150.0
        assert ctx.available_balance == 850.0

    def test_evidence_coverage_propagation(self) -> None:
        """Evidence coverage percentage propagates into T0Context."""
        genome = create_spy_genome()
        market = _make_market()
        position = _make_position()

        ctx = ContextCompiler.compile(
            genome, market, position, 1000.0, evidence_coverage_pct=0.75
        )
        assert ctx.evidence_coverage_pct == 0.75

    def test_hash_changes_when_input_changes(self) -> None:
        """Hash changes when any input changes."""
        genome = create_shark_genome()
        market = _make_market()
        position = _make_position()

        ctx_base = ContextCompiler.compile(genome, market, position, 1000.0)

        # Change balance
        ctx_diff_balance = ContextCompiler.compile(genome, market, position, 999.0)
        assert ctx_base.context_hash != ctx_diff_balance.context_hash

        # Change evidence coverage
        ctx_diff_evidence = ContextCompiler.compile(
            genome, market, position, 1000.0, evidence_coverage_pct=0.5
        )
        assert ctx_base.context_hash != ctx_diff_evidence.context_hash

    def test_empty_position_handling(self) -> None:
        """Empty position (no shares) handled correctly."""
        genome = create_degen_genome()
        market = _make_market()
        position = AgentPosition(
            agent_id="agent_degen",
            market_id="mkt_test",
            shares=[],  # Empty shares
        )

        ctx = ContextCompiler.compile(genome, market, position, 500.0)

        # Should create zero-filled shares matching n_outcomes
        assert len(ctx.current_shares) == 3
        assert all(s == 0.0 for s in ctx.current_shares)

    def test_market_context_propagation(self) -> None:
        """Market context (prices, phase, labels) propagates correctly."""
        genome = create_shark_genome()
        market = _make_market(n_outcomes=2, b=50.0)
        market.x = [10.0, 0.0]  # Non-uniform prices
        position = _make_position(n_outcomes=2)

        ctx = ContextCompiler.compile(genome, market, position, 1000.0)

        assert ctx.phase == "TRADING"
        assert ctx.n_outcomes == 2
        assert len(ctx.prices) == 2
        assert ctx.outcome_labels == ("outcome_0", "outcome_1")
        assert ctx.liquidity_b == 50.0
        # Prices should not be uniform since x[0] > x[1]
        assert ctx.prices[0] > ctx.prices[1]
