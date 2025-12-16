"""
Echelon Agent Execution Module
==============================

The "Hands" of the AI. Routes decisions from the Brain (Skills System)
to the Body (Platform Clients) using Agent Wallets.

This module replaces mock executions with real market interactions:
- Polymarket via CLOB API (Polygon, Gnosis Safe)
- Kalshi via DFlow API (Solana keypair)
- Echelon internal via TimelineShard.sol (Base)

Author: Echelon Protocol
Version: 1.0.0
"""

import logging
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# EXECUTION MODELS
# =============================================================================

class ExecutionPlatform(str, Enum):
    """Supported execution platforms."""
    POLYMARKET = "polymarket"
    KALSHI = "kalshi"
    ECHELON_INTERNAL = "echelon_internal"


class ExecutionStatus(str, Enum):
    """Status of execution attempt."""
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    SKIPPED = "skipped"
    SIMULATED = "simulated"


class ExecutionResult(BaseModel):
    """Result of an execution attempt."""
    
    status: ExecutionStatus
    platform: Optional[ExecutionPlatform] = None
    
    # Identifiers
    order_id: Optional[str] = None
    tx_hash: Optional[str] = None
    
    # Details
    message: Optional[str] = None
    error: Optional[str] = None
    
    # Metrics
    executed_price: Optional[Decimal] = None
    executed_size: Optional[Decimal] = None
    gas_used: Optional[int] = None
    
    # Timing
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None


class AgentDecision(BaseModel):
    """Decision from the agent brain to be executed."""
    
    agent_id: str
    decision_id: str
    
    action: str  # "buy", "sell", "hold", "provide_liquidity"
    confidence: float = Field(ge=0, le=1)
    
    parameters: dict = Field(default_factory=dict)
    
    # Context
    reasoning: Optional[str] = None
    layer: int = Field(1, description="Decision layer (1=heuristic, 2=LLM)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MarketContext(BaseModel):
    """Context about the market being traded."""
    
    platform: ExecutionPlatform
    
    # Market identifiers
    market_id: str
    token_id: Optional[str] = None
    ticker: Optional[str] = None
    condition_id: Optional[str] = None
    
    # Current state
    current_price: Optional[Decimal] = None
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    
    # Timeline context (for internal markets)
    timeline_id: Optional[int] = None
    fork_id: Optional[str] = None


# =============================================================================
# EXECUTION ROUTER
# =============================================================================

class ExecutionRouter:
    """
    Routes agent decisions to the correct blockchain/platform.
    
    Connects:
    - Brain decisions → Platform clients
    - Agent wallets → Transaction signing
    - Builder codes → Volume attribution
    """
    
    def __init__(
        self,
        wallet_factory: Any,  # MultiChainWalletFactory
        polymarket_client: Optional[Any] = None,
        kalshi_client: Optional[Any] = None,
        shard_contract: Optional[Any] = None,
        dry_run: bool = False
    ):
        self.wallets = wallet_factory
        self.poly = polymarket_client
        self.kalshi = kalshi_client
        self.shard = shard_contract
        self.dry_run = dry_run
        
        # Execution history
        self._executions: list[ExecutionResult] = []
    
    async def execute_decision(
        self,
        decision: AgentDecision,
        market_context: MarketContext
    ) -> ExecutionResult:
        """
        Routes an AgentDecision to the correct blockchain/platform.
        
        Flow:
        1. Validate decision is executable
        2. Get agent's wallet for the platform
        3. Execute via appropriate client
        4. Record result
        """
        platform = market_context.platform
        action = decision.action
        
        # Skip non-executable actions
        if action not in ["buy", "sell", "provide_liquidity"]:
            return ExecutionResult(
                status=ExecutionStatus.SKIPPED,
                message=f"Action '{action}' not executable"
            )
        
        logger.info(
            f"⚡ EXECUTING: {decision.agent_id} {action.upper()} "
            f"on {platform.value} (confidence: {decision.confidence:.2f})"
        )
        
        # Dry run mode
        if self.dry_run:
            return ExecutionResult(
                status=ExecutionStatus.SIMULATED,
                platform=platform,
                message="Dry run - no actual execution"
            )
        
        try:
            if platform == ExecutionPlatform.POLYMARKET:
                result = await self._execute_polymarket(decision, market_context)
            elif platform == ExecutionPlatform.KALSHI:
                result = await self._execute_kalshi(decision, market_context)
            elif platform == ExecutionPlatform.ECHELON_INTERNAL:
                result = await self._execute_onchain_shard(decision, market_context)
            else:
                raise ValueError(f"Unknown platform: {platform}")
            
            self._executions.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            result = ExecutionResult(
                status=ExecutionStatus.FAILED,
                platform=platform,
                error=str(e)
            )
            self._executions.append(result)
            return result
    
    # =========================================================================
    # POLYMARKET EXECUTION
    # =========================================================================
    
    async def _execute_polymarket(
        self,
        decision: AgentDecision,
        context: MarketContext
    ) -> ExecutionResult:
        """
        Executes via Polymarket CLOB using the Agent's Gnosis Safe (Polygon).
        
        Features:
        - Gasless via Polygon Relayer
        - EIP-712 signing
        - Builder code attribution
        """
        if not self.poly:
            raise ValueError("Polymarket client not configured")
        
        # 1. Get Agent's Polygon Wallet
        wallet_set = await self.wallets.get_wallet_set(decision.agent_id)
        if not wallet_set or not wallet_set.polymarket_wallet:
            raise ValueError(f"Agent {decision.agent_id} missing Polymarket wallet")
        
        safe_address = wallet_set.polymarket_wallet.address
        
        # 2. Extract parameters
        params = decision.parameters
        token_id = params.get("token_id") or context.token_id
        market_id = params.get("market_id") or context.market_id
        
        price = Decimal(str(params.get("limit_price", "0.5")))
        size = Decimal(str(params.get("size", "10")))
        
        # Map action to side
        if decision.action == "buy":
            side = "buy"
        elif decision.action == "sell":
            side = "sell"
        else:
            side = "buy"  # Default for provide_liquidity
        
        # 3. Execute via CLOB Client
        # The client handles EIP-712 signing and builder code injection
        try:
            order = await self.poly.create_order(
                market_id=market_id,
                token_id=token_id,
                side=side,
                price=float(price),
                size=float(size),
                order_type="limit"
            )
            
            return ExecutionResult(
                status=ExecutionStatus.SUBMITTED,
                platform=ExecutionPlatform.POLYMARKET,
                order_id=order.get("order_id"),
                tx_hash=order.get("tx_hash"),
                executed_price=price,
                executed_size=size,
                message=f"Order submitted via Safe {safe_address[:10]}..."
            )
            
        except Exception as e:
            raise RuntimeError(f"Polymarket order failed: {e}")
    
    # =========================================================================
    # KALSHI EXECUTION
    # =========================================================================
    
    async def _execute_kalshi(
        self,
        decision: AgentDecision,
        context: MarketContext
    ) -> ExecutionResult:
        """
        Executes via Kalshi API using the Agent's Solana Keypair.
        
        Features:
        - SPL token settlement
        - Builder code via client_order_id
        """
        if not self.kalshi:
            raise ValueError("Kalshi client not configured")
        
        # 1. Get Agent's Solana Wallet
        wallet_set = await self.wallets.get_wallet_set(decision.agent_id)
        if not wallet_set or not wallet_set.kalshi_wallet:
            raise ValueError(f"Agent {decision.agent_id} missing Kalshi wallet")
        
        # 2. Extract parameters
        params = decision.parameters
        ticker = params.get("ticker") or context.ticker
        count = int(params.get("count", 1))
        outcome = params.get("outcome", "yes")
        
        # Map action
        action = "buy" if decision.action == "buy" else "sell"
        side = "yes" if outcome == "yes" else "no"
        
        # 3. Execute
        try:
            order = await self.kalshi.create_order(
                ticker=ticker,
                action=action,
                side=side,
                count=count,
                type="market"
            )
            
            return ExecutionResult(
                status=ExecutionStatus.SUBMITTED,
                platform=ExecutionPlatform.KALSHI,
                order_id=order.get("order_id"),
                executed_size=Decimal(count),
                message=f"Order submitted for {ticker}"
            )
            
        except Exception as e:
            raise RuntimeError(f"Kalshi order failed: {e}")
    
    # =========================================================================
    # ON-CHAIN SHARD EXECUTION
    # =========================================================================
    
    async def _execute_onchain_shard(
        self,
        decision: AgentDecision,
        context: MarketContext
    ) -> ExecutionResult:
        """
        Executes on Echelon's TimelineShard.sol contract (Base chain).
        
        Features:
        - Direct contract interaction
        - Uses agent's ERC-6551 identity wallet
        """
        if not self.shard:
            # Return simulated result if contract not configured
            return ExecutionResult(
                status=ExecutionStatus.SIMULATED,
                platform=ExecutionPlatform.ECHELON_INTERNAL,
                message="TimelineShard contract interaction pending Web3 setup"
            )
        
        # 1. Get Agent's Base Wallet
        wallet_set = await self.wallets.get_wallet_set(decision.agent_id)
        if not wallet_set or not wallet_set.identity_wallet:
            raise ValueError(f"Agent {decision.agent_id} missing identity wallet")
        
        identity_address = wallet_set.identity_wallet.address
        
        # 2. Extract parameters
        params = decision.parameters
        token_id = int(params.get("shard_token_id", 0))
        amount = int(params.get("amount", 1))
        
        # 3. Execute contract call
        try:
            if decision.action == "buy":
                # Call TimelineShard.mintShards()
                tx = await self.shard.mint_shards(
                    token_id=token_id,
                    amount=amount,
                    from_address=identity_address
                )
            elif decision.action == "sell":
                # Call TimelineShard.burnShards()
                tx = await self.shard.burn_shards(
                    token_id=token_id,
                    amount=amount,
                    from_address=identity_address
                )
            else:
                raise ValueError(f"Unsupported action for shards: {decision.action}")
            
            return ExecutionResult(
                status=ExecutionStatus.SUBMITTED,
                platform=ExecutionPlatform.ECHELON_INTERNAL,
                tx_hash=tx.get("tx_hash"),
                executed_size=Decimal(amount),
                message=f"Shard transaction submitted"
            )
            
        except Exception as e:
            raise RuntimeError(f"Shard transaction failed: {e}")
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    async def get_execution_history(
        self,
        agent_id: Optional[str] = None,
        platform: Optional[ExecutionPlatform] = None,
        limit: int = 100
    ) -> list[ExecutionResult]:
        """Get execution history with optional filters."""
        results = self._executions
        
        # Apply filters
        if platform:
            results = [r for r in results if r.platform == platform]
        
        return results[-limit:]
    
    async def get_execution_stats(self, agent_id: str) -> dict:
        """Get execution statistics for an agent."""
        executions = self._executions
        
        total = len(executions)
        successful = len([e for e in executions if e.status == ExecutionStatus.SUBMITTED])
        failed = len([e for e in executions if e.status == ExecutionStatus.FAILED])
        
        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0
        }


# =============================================================================
# AGENT BRIDGE INTEGRATION
# =============================================================================

class AgentBridge:
    """
    Bridges the Agent Skills System to real execution.
    
    Replaces mock _execute_buy/_execute_sell with real market operations.
    """
    
    def __init__(
        self,
        execution_router: ExecutionRouter,
        x402_enabled: bool = True
    ):
        self.router = execution_router
        self.x402_enabled = x402_enabled
    
    async def process_agent_decision(
        self,
        agent_id: str,
        decision_type: str,
        market_data: dict,
        osint_context: Optional[dict] = None
    ) -> ExecutionResult:
        """
        Process a decision from the agent brain and execute if appropriate.
        
        Flow:
        1. Receive decision from Brain Router
        2. Validate via risk checks
        3. Execute via Execution Router
        4. Update agent performance metrics
        """
        # Build decision object
        decision = AgentDecision(
            agent_id=agent_id,
            decision_id=f"{agent_id}_{int(datetime.utcnow().timestamp())}",
            action=decision_type,
            confidence=market_data.get("confidence", 0.5),
            parameters=market_data.get("params", {}),
            reasoning=market_data.get("reasoning")
        )
        
        # Build market context
        context = MarketContext(
            platform=ExecutionPlatform(market_data.get("platform", "echelon_internal")),
            market_id=market_data.get("market_id", ""),
            token_id=market_data.get("token_id"),
            ticker=market_data.get("ticker"),
            current_price=Decimal(str(market_data.get("price", 0.5)))
        )
        
        # Risk checks
        if decision.confidence < 0.3:
            logger.info(f"Skipping low-confidence decision ({decision.confidence})")
            return ExecutionResult(
                status=ExecutionStatus.SKIPPED,
                message="Confidence below threshold"
            )
        
        # Check x402 spending limit
        if self.x402_enabled:
            size = Decimal(str(decision.parameters.get("size", 10)))
            can_spend = await self.router.wallets.check_x402_allowance(agent_id, size)
            if not can_spend:
                return ExecutionResult(
                    status=ExecutionStatus.SKIPPED,
                    message="x402 daily limit reached"
                )
        
        # Execute
        result = await self.router.execute_decision(decision, context)
        
        # Record x402 spend if successful
        if result.status == ExecutionStatus.SUBMITTED and self.x402_enabled:
            await self.router.wallets.record_x402_payment(
                agent_id=agent_id,
                amount=result.executed_size or Decimal("0"),
                recipient=context.market_id,
                purpose=f"trade_{decision.action}"
            )
        
        return result


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

async def example_usage():
    """Example of wiring everything together."""
    from backend.wallets.wallet_factory import MultiChainWalletFactory
    
    # Initialize components
    wallet_factory = MultiChainWalletFactory(use_testnet=True)
    
    # Create execution router (dry run for testing)
    router = ExecutionRouter(
        wallet_factory=wallet_factory,
        polymarket_client=None,  # Add real client when available
        kalshi_client=None,      # Add real client when available
        dry_run=True
    )
    
    # Create agent bridge
    bridge = AgentBridge(execution_router=router)
    
    # Create agent wallet
    await wallet_factory.create_agent_wallet_set(agent_id="SHARK_001")
    
    # Process a decision
    result = await bridge.process_agent_decision(
        agent_id="SHARK_001",
        decision_type="buy",
        market_data={
            "platform": "polymarket",
            "market_id": "0x123abc",
            "token_id": "token_yes",
            "price": 0.65,
            "confidence": 0.8,
            "params": {
                "limit_price": 0.65,
                "size": 100
            }
        }
    )
    
    print(f"Execution result: {result.status.value}")
    print(f"Message: {result.message}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
