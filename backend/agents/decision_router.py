"""Novelty Threshold Router -- routes decisions through the tier stack.

Always T0 -> T1. Conditionally T2 (expression) and/or T3 (escalation)
based on confidence and novelty threshold. Records tier_used for
DecisionTrace.

Cycle-013, Sprint 2 -- Task 3.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from backend.agents.context_compiler import T0Context
from backend.agents.deep_reasoning import DeepReasoningEngine, T3Decision
from backend.agents.personality_engine import PersonalityEngine, T2Output
from backend.agents.rules_engine import T1Decision, TradeAction


@dataclass
class RoutedDecision:
    """Final routed decision with tier metadata.

    Contains the decided action plus metadata about which tier produced
    the decision, T2 expression output, and escalation/rate-limit flags.

    Attributes:
        action: Decided trade action.
        outcome_index: Target outcome for BUY/SELL, None for HOLD.
        shares: Number of shares to trade.
        confidence: Confidence score (0.0-1.0).
        reasoning_summary: Human-readable reasoning.
        pattern_name: Named pattern from the deciding tier.
        tier_used: Which tier produced the final decision.
        t2_output: Optional personality expression.
        escalated_to_t3: Whether the decision was escalated to T3.
        t3_rate_limited: Whether T3 was rate-limited (fell back to T1).
        evidence_refs: Evidence references from T3 reasoning.
    """

    action: TradeAction
    outcome_index: Optional[int]
    shares: float
    confidence: float
    reasoning_summary: str
    pattern_name: str
    tier_used: str  # "T1-RULES", "T1-LOCAL-LLM", "T3"
    t2_output: Optional[T2Output] = None
    escalated_to_t3: bool = False
    t3_rate_limited: bool = False
    evidence_refs: List[str] = field(default_factory=list)


class DecisionRouter:
    """Routes decisions through the T0/T1/T2/T3 pipeline.

    Always: T0 -> T1
    Conditional: T2 (expression, non-blocking)
    Conditional: T3 (escalation, replaces T1 if available)

    Routing logic:
    1. Start with T1 decision as baseline.
    2. If confidence >= novelty_threshold: use T1, optionally T2.
    3. If confidence < novelty_threshold: escalate to T3.
    4. If T3 rate-limited or unavailable: fall back to T1.
    """

    def __init__(
        self,
        personality_engine: Optional[PersonalityEngine] = None,
        deep_reasoning: Optional[DeepReasoningEngine] = None,
        enable_t2: bool = True,
    ) -> None:
        """Initialise the decision router.

        Args:
            personality_engine: Optional T2 engine for expression.
            deep_reasoning: Optional T3 engine for deep reasoning.
            enable_t2: Whether to run T2 expression (default True).
        """
        self._personality = personality_engine
        self._deep_reasoning = deep_reasoning
        self._enable_t2 = enable_t2

    async def route(
        self,
        t0_context: T0Context,
        t1_decision: T1Decision,
        agent_id: str,
        tick: int,
        market_history: Optional[List[dict]] = None,
        evidence_chain: Optional[List[dict]] = None,
    ) -> RoutedDecision:
        """Route a T1 decision through the tier stack.

        1. Always use T1 as baseline.
        2. If confidence >= novelty_threshold: use T1, optionally T2.
        3. If confidence < novelty_threshold: escalate to T3.
        4. If T3 rate-limited or unavailable: fall back to T1.

        Args:
            t0_context: Frozen T0Context for routing decision.
            t1_decision: T1 baseline decision.
            agent_id: Agent requesting the routed decision.
            tick: Current tick number.
            market_history: Optional market history for T3.
            evidence_chain: Optional evidence chain for T3.

        Returns:
            RoutedDecision with action, tier_used, and optional T2/T3 output.
        """
        tier_used = "T1-RULES"
        action = t1_decision.action
        outcome_index = t1_decision.outcome_index
        shares = t1_decision.shares
        confidence = t1_decision.confidence
        reasoning = t1_decision.reasoning_trace
        pattern = t1_decision.pattern_name
        escalated = False
        rate_limited = False
        evidence_refs: List[str] = []
        t2_output: Optional[T2Output] = None

        # Check escalation: T1 flagged OR confidence below threshold
        needs_escalation = (
            t1_decision.escalate_to_t3
            or confidence < t0_context.novelty_threshold
        )

        if needs_escalation and self._deep_reasoning is not None:
            t3_result = await self._deep_reasoning.reason(
                agent_id=agent_id,
                t0_context=t0_context,
                t1_decision=t1_decision,
                market_history=market_history or [],
                evidence_chain=evidence_chain or [],
                tick=tick,
            )

            if t3_result is not None:
                # T3 succeeded -- use its decision
                tier_used = "T3"
                action = t3_result.action
                outcome_index = t3_result.outcome_index
                shares = t3_result.shares
                confidence = t3_result.confidence
                reasoning = t3_result.reasoning_summary
                pattern = t3_result.pattern_name
                evidence_refs = list(t3_result.evidence_refs)
                escalated = True
            else:
                # T3 unavailable or rate-limited -- fall back to T1
                rate_limited = True
                # T1 decision used as-is, but flagged

        # T2 expression (non-blocking, optional)
        if self._enable_t2 and self._personality is not None:
            try:
                t2_output = await self._personality.express(
                    t0_context=t0_context,
                    t1_decision=t1_decision,
                )
            except Exception:
                pass  # T2 failure is never fatal

        return RoutedDecision(
            action=action,
            outcome_index=outcome_index,
            shares=shares,
            confidence=confidence,
            reasoning_summary=reasoning,
            pattern_name=pattern,
            tier_used=tier_used,
            t2_output=t2_output,
            escalated_to_t3=escalated,
            t3_rate_limited=rate_limited,
            evidence_refs=evidence_refs,
        )
