"""T1 Rules Engine -- parameterised decision engine driven by T0 context.

Per-archetype decision logic produces T1Decision with action, confidence,
reasoning trace, pattern name, and options considered. All logic is
parameterised by genome values -- no hard-coded archetype if-chains.

Cycle-013, Sprint 1 -- Task 3.
Cycle-014, Sprint 2 -- Task 3: Inquiry-class-aware behaviour adaptation.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from backend.agents.context_compiler import T0Context
from backend.agents.inquiry_behaviour import InquiryBehaviourAdapter


class TradeAction(str, Enum):
    """Possible agent actions."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"


@dataclass(frozen=True)
class ActionOption:
    """A considered alternative for options_considered in DecisionTrace."""

    action: str
    estimated_value: float
    rejection_reason: str


@dataclass(frozen=True)
class T1Decision:
    """Output of the T1 rules engine. Immutable after creation."""

    action: TradeAction
    outcome_index: Optional[int]  # which outcome to buy/sell, None for HOLD
    shares: float
    confidence: float  # 0.0-1.0
    reasoning_trace: str
    pattern_name: str
    options_considered: Tuple[ActionOption, ...] = ()
    escalate_to_t3: bool = False


# ===================================================================
# Thresholds (tunable, but fixed for v1.0)
# ===================================================================

MOMENTUM_THRESHOLD = 0.05  # price delta above uniform for Shark BUY
PROFIT_TARGET = 0.10  # unrealised profit fraction for take-profit
SPREAD_MAX = 0.40  # max spread before Diplomat intervenes
CONVICTION_PCT = 0.5  # fraction of position_limit for Whale buy
MIN_TRADE_SHARES = 1.0  # minimum shares per trade


class RulesEngine:
    """Parameterised T1 decision engine.

    All decision logic is driven by T0Context parameters.
    No hard-coded archetype if-chains -- thresholds are genome-derived.
    """

    def decide(self, ctx: T0Context, tick: int, rng_seed: int) -> T1Decision:
        """Produce a T1 decision from T0 context.

        Reads ctx.inquiry_class, gets InquiryProfile, applies modifiers
        before dispatching to archetype-specific logic.

        Args:
            ctx: Frozen T0Context with all genome + market + position state.
            tick: Current tick number.
            rng_seed: Deterministic RNG seed for this decision.

        Returns:
            T1Decision with action, confidence, and reasoning trace.
        """
        rng = random.Random(rng_seed)

        # Get inquiry-class-specific behaviour profile
        profile = InquiryBehaviourAdapter.get_profile(
            ctx.archetype, ctx.inquiry_class
        )

        # Apply inquiry modifiers to context by creating a modified copy
        # (T0Context is frozen, so we use object.__setattr__ workaround)
        modified_ctx = T0Context(
            archetype=ctx.archetype,
            risk_appetite=ctx.risk_appetite * profile.momentum_weight_modifier,
            evidence_sensitivity=ctx.evidence_sensitivity * profile.evidence_weight_modifier,
            time_preference=ctx.time_preference,
            exploration_rate=ctx.exploration_rate,
            position_limit=ctx.position_limit,
            sabotage_propensity=ctx.sabotage_propensity,
            shield_propensity=ctx.shield_propensity,
            patience=ctx.patience,
            novelty_threshold=ctx.novelty_threshold,
            prices=ctx.prices,
            phase=ctx.phase,
            outcome_labels=ctx.outcome_labels,
            n_outcomes=ctx.n_outcomes,
            evidence_coverage_pct=ctx.evidence_coverage_pct,
            current_shares=ctx.current_shares,
            net_cashflow=ctx.net_cashflow,
            available_balance=ctx.available_balance,
            committed_sources=ctx.committed_sources,
            resolution_date=ctx.resolution_date,
            liquidity_b=ctx.liquidity_b,
            max_position_pct=ctx.max_position_pct,
            max_drawdown_pct=ctx.max_drawdown_pct,
            stop_loss_threshold=ctx.stop_loss_threshold,
            inquiry_class=ctx.inquiry_class,
        )

        # Dispatch to archetype-specific logic
        dispatch = {
            "SHARK": self._shark_decide,
            "SPY": self._spy_decide,
            "DIPLOMAT": self._diplomat_decide,
            "SABOTEUR": self._saboteur_decide,
            "WHALE": self._whale_decide,
            "DEGEN": self._degen_decide,
        }
        decide_fn = dispatch.get(ctx.archetype, self._hold_default)
        decision = decide_fn(modified_ctx, tick, rng)

        # Apply pattern_name override from inquiry profile
        pattern_name = (
            profile.pattern_name_override
            if profile.pattern_name_override
            else decision.pattern_name
        )

        # Append inquiry adaptation to reasoning trace
        reasoning = decision.reasoning_trace
        if profile.action_description and "Default behaviour" not in profile.action_description:
            reasoning = f"[{profile.action_description}] {reasoning}"

        decision = T1Decision(
            action=decision.action,
            outcome_index=decision.outcome_index,
            shares=decision.shares,
            confidence=decision.confidence,
            reasoning_trace=reasoning,
            pattern_name=pattern_name,
            options_considered=decision.options_considered,
            escalate_to_t3=decision.escalate_to_t3,
        )

        # Flag for T3 escalation if confidence is below novelty threshold
        if decision.confidence < ctx.novelty_threshold:
            decision = T1Decision(
                action=decision.action,
                outcome_index=decision.outcome_index,
                shares=decision.shares,
                confidence=decision.confidence,
                reasoning_trace=decision.reasoning_trace,
                pattern_name=decision.pattern_name,
                options_considered=decision.options_considered,
                escalate_to_t3=True,
            )

        return decision

    def _shark_decide(
        self, ctx: T0Context, tick: int, rng: random.Random
    ) -> T1Decision:
        """Momentum exploitation: buy leading, take profit, stop-loss.

        Logic (parameterised by risk_appetite, time_preference, stop_loss_threshold):
        1. Find leading outcome by price.
        2. BUY if price delta > risk_appetite * MOMENTUM_THRESHOLD.
        3. SELL (take profit) if holding and unrealised gain exceeds target.
        4. SELL (stop loss) if loss exceeds stop_loss_threshold.
        5. Default HOLD.
        """
        options = []
        prices = ctx.prices
        n = ctx.n_outcomes

        # Uniform price baseline
        uniform = 1.0 / n if n > 0 else 0.5
        leading_idx = max(range(n), key=lambda i: prices[i])
        price_delta = prices[leading_idx] - uniform

        # Check current position for take-profit / stop-loss
        held_shares = ctx.current_shares[leading_idx] if leading_idx < len(ctx.current_shares) else 0.0
        has_position = held_shares > 0

        # --- Take profit check ---
        if has_position:
            # Estimate unrealised P&L as position * (price - avg_cost)
            # Simplified: use price deviation as proxy
            profit_signal = price_delta * held_shares
            profit_threshold = ctx.time_preference * PROFIT_TARGET * ctx.position_limit
            if profit_signal > profit_threshold and profit_threshold > 0:
                sell_shares = min(held_shares, held_shares * 0.5)
                sell_shares = max(sell_shares, MIN_TRADE_SHARES)
                confidence = 0.6 + price_delta * 0.3
                confidence = min(1.0, max(0.0, confidence))
                options.append(ActionOption(
                    action="BUY",
                    estimated_value=price_delta,
                    rejection_reason="Position profit exceeds take-profit target",
                ))
                return T1Decision(
                    action=TradeAction.SELL,
                    outcome_index=leading_idx,
                    shares=sell_shares,
                    confidence=confidence,
                    reasoning_trace=(
                        f"Take profit: leading outcome {leading_idx} "
                        f"price_delta={price_delta:.4f}, held={held_shares:.1f}, "
                        f"profit_signal={profit_signal:.4f} > threshold={profit_threshold:.4f}"
                    ),
                    pattern_name="momentum_exploitation",
                    options_considered=tuple(options),
                )

        # --- Stop loss check ---
        if has_position and ctx.net_cashflow > 0:
            loss_ratio = -price_delta * held_shares / ctx.net_cashflow if ctx.net_cashflow > 0 else 0.0
            if loss_ratio > ctx.stop_loss_threshold:
                confidence = 0.7
                options.append(ActionOption(
                    action="HOLD",
                    estimated_value=-loss_ratio,
                    rejection_reason="Loss exceeds stop-loss threshold",
                ))
                return T1Decision(
                    action=TradeAction.SELL,
                    outcome_index=leading_idx,
                    shares=held_shares,
                    confidence=confidence,
                    reasoning_trace=(
                        f"Stop loss: loss_ratio={loss_ratio:.4f} > "
                        f"stop_loss_threshold={ctx.stop_loss_threshold}"
                    ),
                    pattern_name="momentum_exploitation",
                    options_considered=tuple(options),
                )

        # --- BUY check: momentum ---
        buy_threshold = ctx.risk_appetite * MOMENTUM_THRESHOLD
        if price_delta > buy_threshold:
            max_shares = min(
                ctx.position_limit * 0.1,
                ctx.available_balance * ctx.risk_appetite,
            )
            shares = max(MIN_TRADE_SHARES, min(max_shares, ctx.position_limit * 0.05))
            confidence = 0.5 + price_delta * 0.5
            confidence = min(1.0, max(0.0, confidence))
            options.append(ActionOption(
                action="HOLD",
                estimated_value=0.0,
                rejection_reason=(
                    f"Momentum signal present: delta={price_delta:.4f} > "
                    f"threshold={buy_threshold:.4f}"
                ),
            ))
            return T1Decision(
                action=TradeAction.BUY,
                outcome_index=leading_idx,
                shares=shares,
                confidence=confidence,
                reasoning_trace=(
                    f"Momentum buy: outcome {leading_idx} "
                    f"price={prices[leading_idx]:.4f}, "
                    f"delta={price_delta:.4f} > {buy_threshold:.4f}, "
                    f"shares={shares:.1f}"
                ),
                pattern_name="momentum_exploitation",
                options_considered=tuple(options),
            )

        # --- Default HOLD ---
        options.append(ActionOption(
            action="BUY",
            estimated_value=price_delta,
            rejection_reason=(
                f"Momentum insufficient: delta={price_delta:.4f} <= "
                f"threshold={buy_threshold:.4f}"
            ),
        ))
        return T1Decision(
            action=TradeAction.HOLD,
            outcome_index=None,
            shares=0.0,
            confidence=0.4 + price_delta * 0.2,
            reasoning_trace=(
                f"No momentum signal: delta={price_delta:.4f} <= "
                f"threshold={buy_threshold:.4f}"
            ),
            pattern_name="momentum_exploitation",
            options_considered=tuple(options),
        )

    def _spy_decide(
        self, ctx: T0Context, tick: int, rng: random.Random
    ) -> T1Decision:
        """Intel arbitrage: trade on evidence arrival.

        Logic (parameterised by evidence_sensitivity):
        1. If evidence coverage > 0 (new evidence present), evaluate signal.
        2. Trade outcome with highest price if sensitivity threshold met.
        3. Otherwise HOLD.
        """
        options = []
        n = ctx.n_outcomes
        prices = ctx.prices

        # Evidence check: coverage > 0 implies evidence present
        has_evidence = ctx.evidence_coverage_pct > 0
        sensitivity_met = ctx.evidence_sensitivity > 0.5

        if has_evidence and sensitivity_met:
            # Trade the most likely outcome based on evidence
            target_idx = max(range(n), key=lambda i: prices[i])
            max_shares = min(
                ctx.position_limit * 0.05,
                ctx.available_balance * 0.3,
            )
            shares = max(MIN_TRADE_SHARES, max_shares)
            confidence = 0.5 + ctx.evidence_coverage_pct * ctx.evidence_sensitivity * 0.5
            confidence = min(1.0, max(0.0, confidence))

            options.append(ActionOption(
                action="HOLD",
                estimated_value=0.0,
                rejection_reason="Evidence signal detected with sufficient sensitivity",
            ))
            return T1Decision(
                action=TradeAction.BUY,
                outcome_index=target_idx,
                shares=shares,
                confidence=confidence,
                reasoning_trace=(
                    f"Intel arbitrage: evidence_coverage={ctx.evidence_coverage_pct:.2f}, "
                    f"sensitivity={ctx.evidence_sensitivity:.2f}, "
                    f"target_outcome={target_idx}, shares={shares:.1f}"
                ),
                pattern_name="intel_arbitrage",
                options_considered=tuple(options),
            )

        # No evidence or sensitivity too low
        reason = "No evidence available" if not has_evidence else (
            f"Sensitivity too low: {ctx.evidence_sensitivity:.2f} <= 0.5"
        )
        options.append(ActionOption(
            action="BUY",
            estimated_value=0.0,
            rejection_reason=reason,
        ))
        return T1Decision(
            action=TradeAction.HOLD,
            outcome_index=None,
            shares=0.0,
            confidence=0.3,
            reasoning_trace=f"No intel signal: {reason}",
            pattern_name="intel_arbitrage",
            options_considered=tuple(options),
        )

    def _diplomat_decide(
        self, ctx: T0Context, tick: int, rng: random.Random
    ) -> T1Decision:
        """Stability maintenance: buy trailing outcome to reduce spread.

        Logic (parameterised by shield_propensity):
        1. Compute spread (max price - min price).
        2. If spread > (1 - shield_propensity) * SPREAD_MAX, buy trailing outcome.
        3. Otherwise HOLD.
        """
        options = []
        n = ctx.n_outcomes
        prices = ctx.prices

        if n < 2:
            return self._hold_default(ctx, tick, rng)

        max_price = max(prices)
        min_price = min(prices)
        spread = max_price - min_price

        spread_threshold = (1.0 - ctx.shield_propensity) * SPREAD_MAX

        if spread > spread_threshold:
            trailing_idx = min(range(n), key=lambda i: prices[i])
            max_shares = min(
                ctx.position_limit * 0.05,
                ctx.available_balance * 0.3,
            )
            shares = max(MIN_TRADE_SHARES, max_shares)
            confidence = 0.5 + (spread - spread_threshold) * 0.5
            confidence = min(1.0, max(0.0, confidence))

            options.append(ActionOption(
                action="HOLD",
                estimated_value=0.0,
                rejection_reason=(
                    f"Spread {spread:.4f} exceeds threshold {spread_threshold:.4f}"
                ),
            ))
            return T1Decision(
                action=TradeAction.BUY,
                outcome_index=trailing_idx,
                shares=shares,
                confidence=confidence,
                reasoning_trace=(
                    f"Stability maintenance: spread={spread:.4f} > "
                    f"threshold={spread_threshold:.4f}, "
                    f"buying trailing outcome {trailing_idx} at {prices[trailing_idx]:.4f}"
                ),
                pattern_name="stability_maintenance",
                options_considered=tuple(options),
            )

        # Spread within tolerance -- SHIELD (express stability preference)
        if ctx.shield_propensity > 0.7:
            options.append(ActionOption(
                action="BUY",
                estimated_value=spread,
                rejection_reason="Spread within tolerance, shielding preferred",
            ))
            return T1Decision(
                action=TradeAction.SHIELD,
                outcome_index=None,
                shares=0.0,
                confidence=0.6,
                reasoning_trace=(
                    f"Market stable: spread={spread:.4f} <= "
                    f"threshold={spread_threshold:.4f}, shielding"
                ),
                pattern_name="stability_maintenance",
                options_considered=tuple(options),
            )

        options.append(ActionOption(
            action="BUY",
            estimated_value=spread,
            rejection_reason=(
                f"Spread {spread:.4f} within tolerance {spread_threshold:.4f}"
            ),
        ))
        return T1Decision(
            action=TradeAction.HOLD,
            outcome_index=None,
            shares=0.0,
            confidence=0.5,
            reasoning_trace=(
                f"Market stable: spread={spread:.4f} <= "
                f"threshold={spread_threshold:.4f}"
            ),
            pattern_name="stability_maintenance",
            options_considered=tuple(options),
        )

    def _saboteur_decide(
        self, ctx: T0Context, tick: int, rng: random.Random
    ) -> T1Decision:
        """Chaos creation: random contrary trades.

        Logic (parameterised by sabotage_propensity):
        1. Roll against sabotage_propensity to decide whether to act.
        2. If acting, buy a non-leading outcome (contrary trade).
        3. Otherwise HOLD.
        """
        options = []
        n = ctx.n_outcomes
        prices = ctx.prices

        # Roll for sabotage
        roll = rng.random()
        if roll < ctx.sabotage_propensity:
            leading_idx = max(range(n), key=lambda i: prices[i])
            other_indices = [i for i in range(n) if i != leading_idx]
            if not other_indices:
                other_indices = list(range(n))

            contrary_idx = rng.choice(other_indices)
            shares = float(rng.randint(1, max(1, int(ctx.position_limit * 0.01))))
            shares = min(shares, ctx.available_balance * 0.2)
            shares = max(MIN_TRADE_SHARES, shares)
            confidence = 0.3 + ctx.sabotage_propensity * 0.2
            confidence = min(1.0, max(0.0, confidence))

            options.append(ActionOption(
                action="BUY leading",
                estimated_value=prices[leading_idx],
                rejection_reason="Chaos strategy: contrary trade preferred",
            ))

            # Decide between BUY contrary or SABOTAGE action
            if ctx.sabotage_propensity > 0.8 and rng.random() < 0.3:
                return T1Decision(
                    action=TradeAction.SABOTAGE,
                    outcome_index=contrary_idx,
                    shares=shares,
                    confidence=confidence,
                    reasoning_trace=(
                        f"Chaos creation (SABOTAGE): roll={roll:.3f} < "
                        f"propensity={ctx.sabotage_propensity:.2f}, "
                        f"targeting outcome {contrary_idx}"
                    ),
                    pattern_name="chaos_creation",
                    options_considered=tuple(options),
                )

            return T1Decision(
                action=TradeAction.BUY,
                outcome_index=contrary_idx,
                shares=shares,
                confidence=confidence,
                reasoning_trace=(
                    f"Chaos creation: roll={roll:.3f} < "
                    f"propensity={ctx.sabotage_propensity:.2f}, "
                    f"contrary buy on outcome {contrary_idx} ({shares:.1f} shares)"
                ),
                pattern_name="chaos_creation",
                options_considered=tuple(options),
            )

        # Sabotage roll failed -- HOLD
        options.append(ActionOption(
            action="SABOTAGE",
            estimated_value=0.0,
            rejection_reason=f"Roll {roll:.3f} >= propensity {ctx.sabotage_propensity:.2f}",
        ))
        return T1Decision(
            action=TradeAction.HOLD,
            outcome_index=None,
            shares=0.0,
            confidence=0.4,
            reasoning_trace=(
                f"Chaos suppressed: roll={roll:.3f} >= "
                f"propensity={ctx.sabotage_propensity:.2f}"
            ),
            pattern_name="chaos_creation",
            options_considered=tuple(options),
        )

    def _whale_decide(
        self, ctx: T0Context, tick: int, rng: random.Random
    ) -> T1Decision:
        """Conviction accumulation: large positions on strong evidence.

        Logic (parameterised by position_limit, evidence_sensitivity):
        1. Check evidence coverage and leading outcome.
        2. If evidence supports conviction AND position < L * conviction_pct, large BUY.
        3. Otherwise HOLD with patience.
        """
        options = []
        n = ctx.n_outcomes
        prices = ctx.prices

        leading_idx = max(range(n), key=lambda i: prices[i])
        leading_price = prices[leading_idx]
        current_held = ctx.current_shares[leading_idx] if leading_idx < len(ctx.current_shares) else 0.0

        # Conviction signal: leading price well above uniform AND evidence present
        uniform = 1.0 / n if n > 0 else 0.5
        conviction_signal = (leading_price - uniform) * ctx.evidence_sensitivity

        # Check position room
        max_position = ctx.position_limit * CONVICTION_PCT
        position_room = max_position - current_held

        if conviction_signal > 0.1 and position_room > MIN_TRADE_SHARES:
            shares = min(
                position_room * 0.3,
                ctx.available_balance * 0.5,
                ctx.position_limit * 0.1,
            )
            shares = max(MIN_TRADE_SHARES, shares)
            confidence = 0.5 + conviction_signal * 0.5
            confidence = min(1.0, max(0.0, confidence))

            options.append(ActionOption(
                action="HOLD",
                estimated_value=0.0,
                rejection_reason=(
                    f"Conviction signal {conviction_signal:.4f} > 0.1, "
                    f"position_room={position_room:.1f}"
                ),
            ))
            return T1Decision(
                action=TradeAction.BUY,
                outcome_index=leading_idx,
                shares=shares,
                confidence=confidence,
                reasoning_trace=(
                    f"Conviction accumulation: outcome {leading_idx} "
                    f"price={leading_price:.4f}, "
                    f"conviction_signal={conviction_signal:.4f}, "
                    f"shares={shares:.1f} (room={position_room:.1f})"
                ),
                pattern_name="conviction_accumulation",
                options_considered=tuple(options),
            )

        # No conviction -- HOLD with patience
        reason = (
            f"Conviction insufficient: signal={conviction_signal:.4f}, "
            f"room={position_room:.1f}"
        )
        options.append(ActionOption(
            action="BUY",
            estimated_value=conviction_signal,
            rejection_reason=reason,
        ))
        return T1Decision(
            action=TradeAction.HOLD,
            outcome_index=None,
            shares=0.0,
            confidence=0.4,
            reasoning_trace=f"Patient hold: {reason}",
            pattern_name="conviction_accumulation",
            options_considered=tuple(options),
        )

    def _degen_decide(
        self, ctx: T0Context, tick: int, rng: random.Random
    ) -> T1Decision:
        """Random exploration: random outcome, random volume.

        Logic (parameterised by exploration_rate):
        1. Roll against exploration_rate.
        2. If exploring: random outcome, random shares (1 to position_limit * 0.02).
        3. Random action: mostly BUY, sometimes SELL if holding.
        """
        options = []
        n = ctx.n_outcomes
        roll = rng.random()

        if roll < ctx.exploration_rate:
            outcome_idx = rng.randint(0, n - 1)
            max_vol = max(1, int(ctx.position_limit * 0.02))
            shares = float(rng.randint(1, max_vol))
            shares = min(shares, ctx.available_balance * 0.5)
            shares = max(MIN_TRADE_SHARES, shares)

            # Randomly sell if holding
            held = ctx.current_shares[outcome_idx] if outcome_idx < len(ctx.current_shares) else 0.0
            if held > MIN_TRADE_SHARES and rng.random() < 0.3:
                sell_shares = min(held, shares)
                confidence = 0.2 + rng.random() * 0.3
                options.append(ActionOption(
                    action="BUY",
                    estimated_value=rng.random(),
                    rejection_reason="Random sell chosen",
                ))
                return T1Decision(
                    action=TradeAction.SELL,
                    outcome_index=outcome_idx,
                    shares=sell_shares,
                    confidence=confidence,
                    reasoning_trace=(
                        f"Random exploration (SELL): outcome={outcome_idx}, "
                        f"shares={sell_shares:.1f}, roll={roll:.3f}"
                    ),
                    pattern_name="random_exploration",
                    options_considered=tuple(options),
                )

            confidence = 0.2 + rng.random() * 0.3
            options.append(ActionOption(
                action="HOLD",
                estimated_value=0.0,
                rejection_reason=f"Exploring: roll={roll:.3f} < rate={ctx.exploration_rate:.2f}",
            ))
            return T1Decision(
                action=TradeAction.BUY,
                outcome_index=outcome_idx,
                shares=shares,
                confidence=confidence,
                reasoning_trace=(
                    f"Random exploration (BUY): outcome={outcome_idx}, "
                    f"shares={shares:.1f}, roll={roll:.3f}"
                ),
                pattern_name="random_exploration",
                options_considered=tuple(options),
            )

        # Exploration roll failed -- HOLD
        options.append(ActionOption(
            action="BUY random",
            estimated_value=0.0,
            rejection_reason=f"Roll {roll:.3f} >= rate {ctx.exploration_rate:.2f}",
        ))
        return T1Decision(
            action=TradeAction.HOLD,
            outcome_index=None,
            shares=0.0,
            confidence=0.2,
            reasoning_trace=(
                f"No exploration: roll={roll:.3f} >= "
                f"rate={ctx.exploration_rate:.2f}"
            ),
            pattern_name="random_exploration",
            options_considered=tuple(options),
        )

    def _hold_default(
        self, ctx: T0Context, tick: int, rng: random.Random
    ) -> T1Decision:
        """Default fallback: HOLD with low confidence and T3 escalation."""
        return T1Decision(
            action=TradeAction.HOLD,
            outcome_index=None,
            shares=0.0,
            confidence=0.3,
            reasoning_trace="Unknown archetype, defaulting to HOLD",
            pattern_name="default_hold",
            escalate_to_t3=True,
            options_considered=(
                ActionOption(
                    action="BUY",
                    estimated_value=0.0,
                    rejection_reason="Unknown archetype -- no decision logic available",
                ),
            ),
        )
