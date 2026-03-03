"""T2 Personality Engine -- expression layer for archetype-specific voice.

Adds archetype-specific personality to T1 decisions.
CRITICAL: T2 never overrides T1's action. Expression only.
Falls back to generic template when Mistral provider is unavailable.

Cycle-013, Sprint 2 -- Task 1.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.agents.context_compiler import T0Context
from backend.agents.rules_engine import T1Decision


@dataclass(frozen=True)
class T2Output:
    """Personality-coloured expression of a T1 decision.

    Contains only strings -- never fed back into the decision pipeline.
    Immutable after construction.

    Attributes:
        coloured_rationale: Personality-flavoured explanation of the decision.
        market_commentary: Optional market commentary in archetype voice.
        diplomatic_message: Optional diplomatic message (Diplomat archetype).
    """

    coloured_rationale: str
    market_commentary: str
    diplomatic_message: Optional[str] = None


# ===================================================================
# Archetype Personality Prompts
# ===================================================================

PERSONALITY_PROMPTS: dict = {
    "SHARK": (
        "You are a ruthless momentum trader. Confident, terse. "
        "Express this trade decision in 1-2 sentences. No hedging."
    ),
    "SPY": (
        "You are a cryptic intelligence operative. Observational, indirect. "
        "Frame this decision as an intelligence assessment."
    ),
    "DIPLOMAT": (
        "You are a measured consensus-builder. Express this trade as "
        "a stabilisation action for the good of the market."
    ),
    "SABOTEUR": (
        "You revel in chaos. Express this trade provocatively. "
        "Hint at deeper motives without revealing them."
    ),
    "WHALE": (
        "You are deliberate and conviction-driven. Express this "
        "large position with gravitas. Few words, great weight."
    ),
    "DEGEN": (
        "YOLO. Express this trade with maximum energy. "
        "Use slang. Keep it under 2 sentences."
    ),
}


class PersonalityEngine:
    """T2 expression layer -- adds personality to decisions.

    CRITICAL: T2 never overrides T1's action. It only colours the output.
    The express() method takes a committed T1Decision and returns T2Output
    containing only strings.
    """

    def __init__(
        self, provider: Optional[object] = None  # MistralProvider
    ) -> None:
        """Initialise with optional Mistral provider.

        Args:
            provider: Optional MistralProvider for LLM-powered expression.
                      If None, falls back to generic templates.
        """
        self._provider = provider

    async def express(
        self,
        t0_context: T0Context,
        t1_decision: T1Decision,
    ) -> T2Output:
        """Generate personality-flavoured expression of a T1 decision.

        If Mistral provider is unavailable, returns generic template.
        T2Output contains only strings -- never overrides T1's action.

        Args:
            t0_context: Frozen T0Context with archetype info.
            t1_decision: Committed T1 decision to express.

        Returns:
            T2Output with personality-coloured rationale and commentary.
        """
        if self._provider is None or not await self._is_provider_available():
            return self._generic_fallback(t0_context, t1_decision)

        prompt = PERSONALITY_PROMPTS.get(
            t0_context.archetype,
            "Express this trading decision clearly.",
        )
        context_str = (
            f"Action: {t1_decision.action.value}, "
            f"Confidence: {t1_decision.confidence:.0%}, "
            f"Reasoning: {t1_decision.reasoning_trace}"
        )

        try:
            response = await self._provider.generate(
                system_prompt=prompt,
                user_prompt=context_str,
            )
            return T2Output(
                coloured_rationale=response.get("rationale", context_str),
                market_commentary=response.get("commentary", ""),
            )
        except Exception:
            return self._generic_fallback(t0_context, t1_decision)

    async def _is_provider_available(self) -> bool:
        """Check if the Mistral provider is healthy.

        Returns:
            True if provider is available, False otherwise.
        """
        if self._provider is None:
            return False
        try:
            return await self._provider.health_check()
        except Exception:
            return False

    def _generic_fallback(
        self, ctx: T0Context, decision: T1Decision
    ) -> T2Output:
        """Generic template fallback when Mistral is unavailable.

        Produces a structured but personality-free expression.

        Args:
            ctx: T0Context with archetype information.
            decision: T1Decision to express.

        Returns:
            T2Output with generic template strings.
        """
        return T2Output(
            coloured_rationale=(
                f"[{ctx.archetype}] {decision.action.value}: "
                f"{decision.reasoning_trace}"
            ),
            market_commentary="",
        )
