"""T3 Deep Reasoning Engine -- complex multi-step reasoning for escalated decisions.

Triggered only when T1 confidence < novelty_threshold, cross-theatre
correlation detected, or novel market conditions. Rate-limited and
cost-bounded. Falls back to None (caller uses T1) when unavailable.

Cycle-013, Sprint 2 -- Task 2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from backend.agents.context_compiler import T0Context
from backend.agents.rules_engine import T1Decision, TradeAction


@dataclass(frozen=True)
class T3Decision:
    """Deep reasoning output. Replaces T1Decision when used.

    Attributes:
        action: Decided trade action.
        outcome_index: Target outcome for BUY/SELL, None for HOLD.
        shares: Number of shares to trade.
        confidence: Confidence score (0.0-1.0).
        reasoning_summary: Human-readable multi-step reasoning.
        evidence_refs: Source IDs or bundle IDs cited in reasoning.
        pattern_name: Named pattern from deep analysis.
    """

    action: TradeAction
    outcome_index: Optional[int]
    shares: float
    confidence: float
    reasoning_summary: str
    evidence_refs: List[str]
    pattern_name: str


@dataclass
class T3RateLimiter:
    """Rate limiter for T3 calls. Configurable per agent per day.

    Auto-resets daily count on date change. Tracks per-tick limit
    to prevent multiple T3 calls within a single tick.

    Attributes:
        max_calls_per_day: Maximum T3 calls allowed per day per agent.
        max_calls_per_tick: Maximum T3 calls allowed per tick (default 1).
    """

    max_calls_per_day: int = 10
    max_calls_per_tick: int = 1
    _daily_count: int = field(default=0, repr=False)
    _last_reset_date: Optional[str] = field(default=None, repr=False)
    _tick_count: int = field(default=0, repr=False)
    _current_tick: int = field(default=-1, repr=False)

    def can_call(self, tick: int) -> bool:
        """Check if a T3 call is allowed under rate limits.

        Auto-resets daily count on date change. Resets per-tick
        count when tick changes.

        Args:
            tick: Current tick number.

        Returns:
            True if the call is within both daily and per-tick limits.
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if self._last_reset_date != today:
            self._daily_count = 0
            self._last_reset_date = today

        if tick != self._current_tick:
            self._tick_count = 0
            self._current_tick = tick

        return (
            self._daily_count < self.max_calls_per_day
            and self._tick_count < self.max_calls_per_tick
        )

    def record_call(self) -> None:
        """Record that a T3 call was made. Increments both counters."""
        self._daily_count += 1
        self._tick_count += 1

    @property
    def daily_count(self) -> int:
        """Current daily call count."""
        return self._daily_count


class DeepReasoningEngine:
    """T3 deep reasoning -- Sonnet/Opus via Anthropic API.

    Rate-limited and cost-bounded. Falls back to None (caller uses T1)
    if provider is unavailable or rate limit is exceeded.
    """

    def __init__(
        self,
        provider: Optional[object] = None,  # AnthropicProvider
        max_calls_per_day: int = 10,
    ) -> None:
        """Initialise with optional Anthropic provider.

        Args:
            provider: Optional AnthropicProvider for deep reasoning.
                      If None, always returns None (T1 fallback).
            max_calls_per_day: Maximum T3 calls per agent per day.
        """
        self._provider = provider
        self._rate_limiters: dict = {}
        self._max_calls_per_day = max_calls_per_day

    def _get_limiter(self, agent_id: str) -> T3RateLimiter:
        """Get or create a rate limiter for the given agent.

        Args:
            agent_id: Unique agent identifier.

        Returns:
            T3RateLimiter for the agent.
        """
        if agent_id not in self._rate_limiters:
            self._rate_limiters[agent_id] = T3RateLimiter(
                max_calls_per_day=self._max_calls_per_day
            )
        return self._rate_limiters[agent_id]

    async def reason(
        self,
        agent_id: str,
        t0_context: T0Context,
        t1_decision: T1Decision,
        market_history: List[dict],
        evidence_chain: List[dict],
        tick: int,
    ) -> Optional[T3Decision]:
        """Deep reasoning for escalated decisions.

        Returns T3Decision if provider is available and under rate limit.
        Returns None if unavailable or rate-limited -- caller falls back
        to T1Decision.

        Args:
            agent_id: Agent requesting deep reasoning.
            t0_context: Frozen T0Context with full agent world-view.
            t1_decision: T1 preliminary decision to reason about.
            market_history: List of past market state snapshots.
            evidence_chain: List of evidence items for citation.
            tick: Current tick number.

        Returns:
            T3Decision if reasoning succeeds, None otherwise.
        """
        limiter = self._get_limiter(agent_id)
        if not limiter.can_call(tick):
            return None

        if self._provider is None:
            return None

        try:
            available = await self._provider.health_check()
            if not available:
                return None
        except Exception:
            return None

        try:
            context_prompt = self._build_prompt(
                t0_context, t1_decision, market_history, evidence_chain
            )
            response = await self._provider.generate(
                system_prompt=(
                    "You are a deep reasoning engine for an autonomous "
                    "trading agent. Analyse the market context, evidence, "
                    "and T1 preliminary decision. Provide a final decision "
                    "with structured reasoning."
                ),
                user_prompt=context_prompt,
            )

            limiter.record_call()

            return T3Decision(
                action=TradeAction(response.get("action", "HOLD")),
                outcome_index=response.get("outcome_index"),
                shares=response.get("shares", 0.0),
                confidence=response.get("confidence", 0.5),
                reasoning_summary=response.get("reasoning_summary", ""),
                evidence_refs=response.get("evidence_refs", []),
                pattern_name=response.get(
                    "pattern_name", "deep_analysis"
                ),
            )
        except Exception:
            return None

    def _build_prompt(
        self,
        ctx: T0Context,
        t1: T1Decision,
        history: List[dict],
        evidence: List[dict],
    ) -> str:
        """Build structured prompt for T3 reasoning.

        Args:
            ctx: T0Context with agent world-view.
            t1: T1 preliminary decision.
            history: Market history snapshots.
            evidence: Evidence chain items.

        Returns:
            Formatted prompt string for the deep reasoning model.
        """
        return (
            f"Archetype: {ctx.archetype}\n"
            f"Market prices: {list(ctx.prices)}\n"
            f"Outcomes: {list(ctx.outcome_labels)}\n"
            f"Position: {list(ctx.current_shares)}\n"
            f"Balance: {ctx.available_balance}\n"
            f"T1 preliminary: {t1.action.value} "
            f"(confidence={t1.confidence:.2f})\n"
            f"T1 reasoning: {t1.reasoning_trace}\n"
            f"Evidence chain: {len(evidence)} items\n"
            f"Market history: {len(history)} ticks\n"
        )
