"""Integration layer — wires engines to 010a market system.

EngineOrchestrator wraps TradingEngine to produce Wing Flaps on every trade.
Registers heartbeat handlers for Entropy and Paradox ticks.
Does NOT modify backend/market/.
"""
from __future__ import annotations

from backend.engines.butterfly import ButterflyEngine, WingFlap, WingFlapType, _clamp
from backend.engines.config import EngineConfig
from backend.engines.entropy import EntropyEngine
from backend.engines.heartbeat import HeartbeatScheduler
from backend.engines.paradox import ParadoxAction, ParadoxEngine
from backend.engines.vrf import VRFProvider
from backend.market.exceptions import TradingHalted
from backend.market.positions import PositionManager
from backend.market.state import MarketPhase, MarketState
from backend.market.trading import Trade, TradingEngine


class EngineOrchestrator:
    """Wires engines to 010a market system. One instance per Theatre session."""

    def __init__(
        self,
        market: MarketState,
        trading_engine: TradingEngine,
        position_manager: PositionManager,
        butterfly: ButterflyEngine,
        entropy: EntropyEngine,
        engine_config: EngineConfig,
        heartbeat: HeartbeatScheduler,
        paradox: ParadoxEngine | None = None,
        vrf: VRFProvider | None = None,
    ) -> None:
        self._market = market
        self._trading_engine = trading_engine
        self._position_manager = position_manager
        self._butterfly = butterfly
        self._entropy = entropy
        self._engine_config = engine_config
        self._heartbeat = heartbeat
        self._paradox = paradox
        self._vrf = vrf
        self._halted: bool = False
        self._last_logic_gap_status: str = "healthy"

    def execute_trade_with_flap(
        self,
        agent_id: str,
        outcome_index: int,
        shares: float,
    ) -> Trade:
        """Execute trade via 010a TradingEngine, then record TRADE Wing Flap.

        Raises TradingHalted if circuit breaker halt is active.
        """
        if self._halted:
            raise TradingHalted(MarketPhase.TRADING)

        # Delegate to 010a's TradingEngine
        trade = self._trading_engine.execute_trade(
            self._market, agent_id, outcome_index, shares
        )

        # Compute stability impact
        k = self._engine_config.butterfly.trade_impact_k
        b = self._market.b
        raw_impact = k * abs(trade.cost) / b

        # Sign convention: buy (shares > 0) = negative (destabilising),
        # sell (shares < 0) = positive (stabilising)
        if shares > 0:
            impact = -raw_impact
        else:
            impact = raw_impact

        impact = _clamp(impact, -0.05, 0.05)

        # Record TRADE Wing Flap
        self._butterfly.record_flap(
            flap_type=WingFlapType.TRADE,
            theatre_id=self._market.market_id,
            agent_id=agent_id,
            impact=impact,
            trigger_detail={
                "trade_id": trade.trade_id,
                "outcome_index": outcome_index,
                "shares": shares,
                "cost": trade.cost,
            },
        )

        return trade

    def halt_trading(self, theatre_id: str) -> None:
        """Set circuit breaker halt. Called by Paradox TRADING_PAUSE."""
        self._halted = True

    def resume_trading(self, theatre_id: str) -> None:
        """Clear circuit breaker halt."""
        self._halted = False

    async def start(self) -> None:
        """Register heartbeat handlers and start heartbeat."""
        self._heartbeat.register_handler("entropy", self._entropy_tick_handler)
        if self._paradox is not None:
            self._heartbeat.register_handler("paradox", self._paradox_tick_handler)
        await self._heartbeat.start(self._market.market_id)

    async def stop(self) -> None:
        """Stop heartbeat. Clean shutdown."""
        await self._heartbeat.stop(self._market.market_id)

    async def _entropy_tick_handler(self, theatre_id: str) -> None:
        """Heartbeat handler for ENTROPY cadence. Uses real Logic Gap status."""
        self._entropy.tick(theatre_id, self._last_logic_gap_status)

    async def _paradox_tick_handler(self, theatre_id: str) -> None:
        """Heartbeat handler for PARADOX cadence. Scans, evaluates, acts."""
        if self._paradox is None:
            return

        reading = self._paradox.scan(theatre_id)
        if reading is None:
            return

        # Update Logic Gap status for Entropy wiring
        self._last_logic_gap_status = reading.status.value

        action = self._paradox.evaluate_thresholds(reading)
        if action is None:
            return

        self._paradox.execute_action(action, theatre_id)

        # Circuit breaker actions
        if action == ParadoxAction.TRADING_PAUSE:
            self.halt_trading(theatre_id)
        elif action == ParadoxAction.FORCED_RESOLUTION:
            self.halt_trading(theatre_id)
