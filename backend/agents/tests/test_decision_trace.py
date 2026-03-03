"""Tests for DecisionTrace schema.

Covers schema validation, JSON round-trip, RLMF compatibility,
tier_used literal enforcement, and per-archetype trace production.

Cycle-013, Sprint 1 -- Task 7.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.agents.decision_trace import DecisionTrace


# ===================================================================
# Fixtures
# ===================================================================


def _make_trace(**overrides) -> DecisionTrace:
    """Create a valid DecisionTrace with sensible defaults."""
    defaults = {
        "tick_id": "tick_0001",
        "agent_id": "theatre_test_shark",
        "theatre_id": "theatre_test",
        "tier_used": "T1-RULES",
        "market_state_snapshot": {
            "prices": [0.5, 0.3, 0.2],
            "phase": "TRADING",
            "evidence_coverage_pct": 0.0,
        },
        "evidence_state": {
            "new_evidence_flag": False,
            "source_ids_cited": [],
        },
        "t0_context_hash": "abc123def456",
        "action": "BUY(outcome=0, shares=10.0)",
        "confidence": 0.75,
        "pattern_name": "momentum_exploitation",
        "options_considered": [
            {
                "action": "HOLD",
                "estimated_value": 0.0,
                "rejection_reason": "Momentum signal present",
            }
        ],
        "reasoning_summary": "Momentum buy on leading outcome",
        "escalated_to_t3": False,
        "evidence_refs": [],
    }
    defaults.update(overrides)
    return DecisionTrace(**defaults)


# ===================================================================
# Tests
# ===================================================================


class TestDecisionTrace:
    """Tests for DecisionTrace Pydantic v2 model."""

    def test_full_schema_validation(self) -> None:
        """All required fields validate successfully."""
        trace = _make_trace()
        assert trace.tick_id == "tick_0001"
        assert trace.agent_id == "theatre_test_shark"
        assert trace.theatre_id == "theatre_test"
        assert trace.tier_used == "T1-RULES"
        assert trace.confidence == 0.75
        assert trace.pattern_name == "momentum_exploitation"
        assert len(trace.options_considered) == 1
        assert trace.reasoning_summary == "Momentum buy on leading outcome"
        assert trace.escalated_to_t3 is False
        assert trace.evidence_refs == []

    def test_json_round_trip(self) -> None:
        """JSON serialisation round-trip produces identical trace."""
        trace = _make_trace()
        data = trace.model_dump(mode="json")
        restored = DecisionTrace(**data)

        assert restored.tick_id == trace.tick_id
        assert restored.agent_id == trace.agent_id
        assert restored.tier_used == trace.tier_used
        assert restored.confidence == trace.confidence
        assert restored.pattern_name == trace.pattern_name
        assert restored.action == trace.action

    def test_rlmf_dict_compatibility(self) -> None:
        """to_rlmf_dict() produces dict compatible with AgentTrace.decision_traces."""
        trace = _make_trace()
        d = trace.to_rlmf_dict()

        # Must be a plain dict
        assert isinstance(d, dict)
        # Must have all required keys
        required_keys = {
            "tick_id", "agent_id", "theatre_id", "timestamp",
            "tier_used", "market_state_snapshot", "evidence_state",
            "t0_context_hash", "action", "confidence", "pattern_name",
            "options_considered", "reasoning_summary", "escalated_to_t3",
            "evidence_refs",
        }
        assert required_keys.issubset(d.keys())
        # Timestamp should be serialised as string
        assert isinstance(d["timestamp"], str)
        # Nested structures preserved
        assert isinstance(d["market_state_snapshot"], dict)
        assert isinstance(d["options_considered"], list)

    def test_tier_used_literal_enforcement(self) -> None:
        """tier_used restricted to Literal['T1-RULES', 'T1-LOCAL-LLM', 'T3']."""
        # Valid tiers
        _make_trace(tier_used="T1-RULES")
        _make_trace(tier_used="T1-LOCAL-LLM")
        _make_trace(tier_used="T3")

        # Invalid tier
        with pytest.raises(ValidationError):
            _make_trace(tier_used="T2")

    def test_timestamp_defaults_to_utc(self) -> None:
        """timestamp defaults to current UTC time."""
        trace = _make_trace()
        assert trace.timestamp.tzinfo is not None
        # Should be close to now
        delta = (datetime.now(timezone.utc) - trace.timestamp).total_seconds()
        assert abs(delta) < 5.0  # Within 5 seconds

    def test_confidence_range_validation(self) -> None:
        """confidence must be in [0.0, 1.0]."""
        _make_trace(confidence=0.0)
        _make_trace(confidence=1.0)

        with pytest.raises(ValidationError):
            _make_trace(confidence=-0.1)
        with pytest.raises(ValidationError):
            _make_trace(confidence=1.1)

    def test_frozen_enforcement(self) -> None:
        """DecisionTrace is frozen -- cannot mutate after construction."""
        trace = _make_trace()
        with pytest.raises(ValidationError):
            trace.confidence = 0.99  # type: ignore[misc]

    @pytest.mark.parametrize("pattern", [
        "momentum_exploitation",
        "intel_arbitrage",
        "stability_maintenance",
        "chaos_creation",
        "conviction_accumulation",
        "random_exploration",
    ])
    def test_all_pattern_names_valid(self, pattern: str) -> None:
        """All archetype pattern names produce valid traces."""
        trace = _make_trace(pattern_name=pattern)
        assert trace.pattern_name == pattern
        # Round-trip through RLMF dict
        d = trace.to_rlmf_dict()
        assert d["pattern_name"] == pattern

    def test_evidence_refs_populated(self) -> None:
        """Evidence refs populated when evidence is present."""
        trace = _make_trace(
            evidence_refs=["src_001", "bundle_abc"],
            evidence_state={
                "new_evidence_flag": True,
                "source_ids_cited": ["src_001"],
            },
        )
        assert len(trace.evidence_refs) == 2
        assert "src_001" in trace.evidence_refs
