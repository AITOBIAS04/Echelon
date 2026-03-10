"""DecisionTrace -- stable structured log for every agent decision.

Pydantic v2 model conforming to BEAUVOIR agent-first citizenship
requirements. Compatible with AgentTrace.decision_traces in
backend/services/rlmf_export.py. Every T1 (and T3) decision produces
a trace conforming to this schema.

Cycle-013, Sprint 1 -- Task 4.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class DecisionTrace(BaseModel):
    """Stable decision log schema. Every field is a stable key.

    Conforms to BEAUVOIR agent-first citizenship requirements.
    Compatible with RLMFExport.AgentTrace.decision_traces (list[dict]).
    Frozen after construction for auditability.
    """

    model_config = {"frozen": True}

    # --- Identity ---
    tick_id: str
    agent_id: str
    theatre_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.utcnow()
    )

    # --- Tier ---
    tier_used: Literal["T1-RULES", "T1-LOCAL-LLM", "T3"]

    # --- Market Snapshot ---
    market_state_snapshot: Dict  # prices, phase, evidence_coverage_pct

    # --- Evidence State ---
    evidence_state: Dict  # new_evidence_flag, source_ids_cited

    # --- Decision ---
    t0_context_hash: str
    action: str  # BUY(outcome, shares) / SELL / HOLD / SHIELD / SABOTAGE
    confidence: float = Field(ge=0.0, le=1.0)
    pattern_name: str  # Named pattern from archetype matrix
    options_considered: List[Dict]  # [{action, estimated_value, rejection_reason}]
    reasoning_summary: str

    # --- Escalation ---
    escalated_to_t3: bool = False

    # --- Evidence References ---
    evidence_refs: List[str] = Field(default_factory=list)

    def to_rlmf_dict(self) -> dict:
        """Serialise to dict compatible with AgentTrace.decision_traces.

        Uses Pydantic v2's model_dump with JSON mode for datetime
        serialisation and nested dict/list handling.
        """
        return self.model_dump(mode="json")
