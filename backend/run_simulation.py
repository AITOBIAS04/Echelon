"""
Echelon Simulation Runner
=========================

The "Game Loop" that brings the system to life.

1. Polls OSINT (Mocked or Real)
2. Wakes up Agents
3. Executes Trades
4. Prints beautiful logs for the Demo Video

Usage:
    python -m backend.run_simulation

Author: Echelon Protocol
Version: 1.0.0
"""

import asyncio
import logging
import random
import sys
from datetime import datetime
from decimal import Decimal
from typing import Optional

# Setup Logging for "Hacker Terminal" aesthetic
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("ECHELON_SIM")


# =============================================================================
# ASCII ART BANNER
# =============================================================================

BANNER = """
    ███████╗ ██████╗██╗  ██╗███████╗██╗      ██████╗ ███╗   ██╗
    ██╔════╝██╔════╝██║  ██║██╔════╝██║     ██╔═══██╗████╗  ██║
    █████╗  ██║     ███████║█████╗  ██║     ██║   ██║██╔██╗ ██║
    ██╔══╝  ██║     ██╔══██║██╔══╝  ██║     ██║   ██║██║╚██╗██║
    ███████╗╚██████╗██║  ██║███████╗███████╗╚██████╔╝██║ ╚████║
    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
    
    >>> SITUATION ROOM ONLINE
    >>> OSINT PIPELINE ACTIVE
    >>> AGENTS STANDING BY
"""


# =============================================================================
# MOCK COMPONENTS (for standalone testing)
# =============================================================================

class MockWalletFactory:
    """Mock wallet factory for testing without real blockchain."""
    
    def __init__(self, use_testnet: bool = True):
        self.use_testnet = use_testnet
        self.wallets = {}
    
    async def create_agent_wallet_set(self, agent_id: str):
        """Create mock wallet set for agent."""
        self.wallets[agent_id] = {
            "identity": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
            "polymarket": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
            "kalshi": f"{''.join(random.choices('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz', k=44))}"
        }
        return self.wallets[agent_id]
    
    async def get_wallet_set(self, agent_id: str):
        """Get wallet set for agent."""
        return self.wallets.get(agent_id)
    
    async def check_x402_allowance(self, agent_id: str, amount: Decimal) -> bool:
        """Check if agent can spend amount."""
        return True
    
    async def record_x402_payment(self, **kwargs):
        """Record payment."""
        pass


class MockExecutionResult:
    """Mock execution result."""
    
    def __init__(self, status: str, platform: str, size: int, message: str = ""):
        self.status = type('Status', (), {'value': status})()
        self.platform = type('Platform', (), {'value': platform})()
        self.executed_size = Decimal(size)
        self.message = message


class MockAgentBridge:
    """Mock agent bridge for testing."""
    
    def __init__(self, wallet_factory, dry_run: bool = True):
        self.wallet_factory = wallet_factory
        self.dry_run = dry_run
    
    async def process_agent_decision(
        self,
        agent_id: str,
        decision_type: str,
        market_data: dict
    ) -> MockExecutionResult:
        """Process mock decision."""
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        confidence = market_data.get("confidence", 0.5)
        
        # Skip low confidence
        if confidence < 0.3:
            return MockExecutionResult(
                status="skipped",
                platform=market_data.get("platform", "unknown"),
                size=0,
                message="Confidence below threshold"
            )
        
        # Simulate execution
        size = market_data.get("params", {}).get("size", 100)
        platform = market_data.get("platform", "echelon_internal")
        
        return MockExecutionResult(
            status="simulated" if self.dry_run else "submitted",
            platform=platform,
            size=size,
            message=f"Dry run execution for {agent_id}"
        )


# =============================================================================
# OSINT SIGNAL GENERATOR
# =============================================================================

class OSINTSignalGenerator:
    """Generates mock OSINT signals for simulation."""
    
    def __init__(self):
        self.signal_types = [
            {"type": "MARKET_SPIKE", "icon": "📈", "severity": "HIGH"},
            {"type": "SENTIMENT_SHIFT", "icon": "🔄", "severity": "MEDIUM"},
            {"type": "DARK_FLEET", "icon": "🚢", "severity": "HIGH"},
            {"type": "VIP_MOVEMENT", "icon": "✈️", "severity": "MEDIUM"},
            {"type": "WHALE_ALERT", "icon": "🐋", "severity": "HIGH"},
            {"type": "NEWS_BREAK", "icon": "📰", "severity": "LOW"},
            {"type": "SOCIAL_SPIKE", "icon": "🐦", "severity": "MEDIUM"},
        ]
    
    def generate_signal(self, market: dict) -> dict:
        """Generate a random OSINT signal."""
        signal_type = random.choice(self.signal_types)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "type": signal_type["type"],
            "icon": signal_type["icon"],
            "severity": signal_type["severity"],
            "market": market["ticker"],
            "price_impact": random.uniform(-0.05, 0.05),
            "confidence": random.uniform(0.4, 0.95),
        }


# =============================================================================
# AGENT PERSONAS
# =============================================================================

AGENT_PERSONAS = [
    {
        "id": "SHARK_ALPHA",
        "archetype": "SHARK",
        "emoji": "🦈",
        "style": "AGGRESSIVE",
        "risk_tolerance": 0.8,
        "preferred_platforms": ["polymarket", "kalshi"],
    },
    {
        "id": "SPY_CARDINAL",
        "archetype": "SPY",
        "emoji": "🕵️",
        "style": "CAUTIOUS",
        "risk_tolerance": 0.4,
        "preferred_platforms": ["polymarket"],
    },
    {
        "id": "WHALE_NEPTUNE",
        "archetype": "WHALE",
        "emoji": "🐋",
        "style": "INSTITUTIONAL",
        "risk_tolerance": 0.6,
        "preferred_platforms": ["kalshi"],
    },
    {
        "id": "DIPLOMAT_ENVOY",
        "archetype": "DIPLOMAT",
        "emoji": "🤝",
        "style": "BALANCED",
        "risk_tolerance": 0.5,
        "preferred_platforms": ["echelon_internal"],
    },
    {
        "id": "SABOTEUR_GHOST",
        "archetype": "SABOTEUR",
        "emoji": "💣",
        "style": "CHAOTIC",
        "risk_tolerance": 0.9,
        "preferred_platforms": ["echelon_internal"],
    },
]


# =============================================================================
# MARKET DEFINITIONS
# =============================================================================

MARKETS = [
    {
        "id": "0xPoly_FED_DEC",
        "ticker": "FED-DEC-RATE",
        "platform": "polymarket",
        "description": "Fed December Rate Decision",
        "base_price": 0.45,
    },
    {
        "id": "Kalshi_GDP_Q4",
        "ticker": "US-GDP-Q4",
        "platform": "kalshi",
        "description": "US Q4 GDP Growth",
        "base_price": 0.60,
    },
    {
        "id": "Timeline_ALPHA",
        "ticker": "UKRAINE-CEASEFIRE",
        "platform": "echelon_internal",
        "description": "Ukraine Ceasefire Timeline",
        "base_price": 0.25,
    },
    {
        "id": "0xPoly_BTC_100K",
        "ticker": "BTC-100K-DEC",
        "platform": "polymarket",
        "description": "Bitcoin $100K by December",
        "base_price": 0.72,
    },
    {
        "id": "Timeline_BETA",
        "ticker": "GHOST-TANKER",
        "platform": "echelon_internal",
        "description": "Ghost Tanker Mission",
        "base_price": 0.35,
    },
]


# =============================================================================
# SIMULATION RUNNER
# =============================================================================

class SimulationRunner:
    """
    The heartbeat of Echelon.
    
    Runs the game loop:
    1. Generate OSINT signals
    2. Wake agents
    3. Execute decisions
    4. Log beautifully
    """
    
    def __init__(
        self,
        wallet_factory=None,
        bridge=None,
        tick_interval: float = 2.0,
        dry_run: bool = True
    ):
        self.wallet_factory = wallet_factory or MockWalletFactory(use_testnet=True)
        self.bridge = bridge or MockAgentBridge(self.wallet_factory, dry_run=dry_run)
        self.tick_interval = tick_interval
        self.dry_run = dry_run
        
        self.osint = OSINTSignalGenerator()
        self.agents = []
        self.markets = {m["id"]: {**m, "price": m["base_price"]} for m in MARKETS}
        
        # Stats
        self.tick_count = 0
        self.total_executions = 0
        self.total_volume = Decimal("0")
    
    async def initialize(self):
        """Initialize the simulation."""
        print(BANNER)
        
        logger.info("🔌 Connecting to Multi-Chain Wallets...")
        await asyncio.sleep(0.5)
        
        logger.info("🧬 Spawning Genesis Agents...")
        for persona in AGENT_PERSONAS:
            await self.wallet_factory.create_agent_wallet_set(persona["id"])
            self.agents.append(persona)
            logger.info(f"   {persona['emoji']} [ONLINE] Agent {persona['id']} ({persona['archetype']})")
            await asyncio.sleep(0.2)
        
        logger.info("📡 OSINT Pipeline Active")
        logger.info("🎮 Markets Loaded: " + ", ".join(m["ticker"] for m in MARKETS))
        
        print("-" * 70)
        logger.info("🚀 STARTING SIMULATION LOOP (Press Ctrl+C to stop)")
        print("-" * 70)
    
    async def tick(self):
        """Execute one simulation tick."""
        self.tick_count += 1
        
        # 1. Select random market and update price
        market_id = random.choice(list(self.markets.keys()))
        market = self.markets[market_id]
        
        # Price movement
        price_shift = Decimal(str(random.uniform(-0.03, 0.03)))
        new_price = max(0.01, min(0.99, float(Decimal(str(market["price"])) + price_shift)))
        market["price"] = new_price
        
        # 2. Generate OSINT signal
        signal = self.osint.generate_signal(market)
        
        print(f"\n{'='*70}")
        print(f"[TICK {self.tick_count:04d}] {signal['icon']} {signal['type']} | {market['ticker']} @ {market['price']:.3f}")
        print(f"           Severity: {signal['severity']} | Confidence: {signal['confidence']:.2f}")
        print(f"{'='*70}")
        
        # 3. Wake random agent
        agent = random.choice(self.agents)
        
        # 4. Agent decision
        logger.info(f"{agent['emoji']} {agent['id']} analyzing signal...")
        await asyncio.sleep(0.3)  # Thinking time
        
        # Decision based on agent style and signal
        base_confidence = signal["confidence"]
        risk_modifier = agent["risk_tolerance"]
        final_confidence = base_confidence * risk_modifier
        
        decision = "buy" if random.random() > 0.5 else "sell"
        size = int(random.uniform(50, 500) * risk_modifier)
        
        logger.info(f"   └─ Decision: {decision.upper()} | Confidence: {final_confidence:.2f}")
        
        # 5. Execute if confident enough
        if final_confidence > 0.5:
            result = await self.bridge.process_agent_decision(
                agent_id=agent["id"],
                decision_type=decision,
                market_data={
                    "platform": market["platform"],
                    "market_id": market["id"],
                    "ticker": market["ticker"],
                    "price": market["price"],
                    "confidence": final_confidence,
                    "params": {"size": size}
                }
            )
            
            if result.status.value in ["submitted", "simulated"]:
                self.total_executions += 1
                self.total_volume += result.executed_size
                
                status_icon = "✅" if result.status.value == "submitted" else "🔵"
                logger.info(
                    f"{status_icon} EXECUTED: {agent['id']} {decision.upper()} "
                    f"${result.executed_size} on {result.platform.value}"
                )
            else:
                logger.warning(f"❌ SKIPPED: {result.message}")
        else:
            logger.info(f"⏸️  HOLD: Confidence too low ({final_confidence:.2f})")
        
        # 6. Periodic stats
        if self.tick_count % 10 == 0:
            print(f"\n📊 STATS | Ticks: {self.tick_count} | Executions: {self.total_executions} | Volume: ${self.total_volume}")
    
    async def run(self, max_ticks: Optional[int] = None):
        """Run the simulation loop."""
        await self.initialize()
        
        try:
            while max_ticks is None or self.tick_count < max_ticks:
                await self.tick()
                await asyncio.sleep(self.tick_interval)
        
        except KeyboardInterrupt:
            print("\n")
            print("=" * 70)
            print("🛑 SIMULATION STOPPED")
            print("=" * 70)
            print(f"\n📊 FINAL STATS:")
            print(f"   Total Ticks: {self.tick_count}")
            print(f"   Total Executions: {self.total_executions}")
            print(f"   Total Volume: ${self.total_volume}")
            print(f"   Execution Rate: {self.total_executions/max(1,self.tick_count)*100:.1f}%")
            print()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Main entry point."""
    # Check for command line args
    dry_run = "--live" not in sys.argv
    tick_interval = 2.0
    
    for arg in sys.argv:
        if arg.startswith("--interval="):
            tick_interval = float(arg.split("=")[1])
    
    if dry_run:
        logger.info("🔒 Running in DRY RUN mode (use --live for real execution)")
    else:
        logger.warning("⚠️  Running in LIVE mode - real transactions will occur!")
    
    # Try to import real components, fall back to mocks
    try:
        from backend.agents.agent_execution import ExecutionRouter, AgentBridge
        from backend.wallets.wallet_factory import MultiChainWalletFactory
        
        wallet_factory = MultiChainWalletFactory(use_testnet=True)
        exec_router = ExecutionRouter(wallet_factory=wallet_factory, dry_run=dry_run)
        bridge = AgentBridge(execution_router=exec_router)
        
        logger.info("✅ Using REAL components")
    except ImportError as e:
        logger.warning(f"⚠️  Using MOCK components: {e}")
        wallet_factory = None
        bridge = None
    
    # Run simulation
    sim = SimulationRunner(
        wallet_factory=wallet_factory,
        bridge=bridge,
        tick_interval=tick_interval,
        dry_run=dry_run
    )
    
    await sim.run()


if __name__ == "__main__":
    asyncio.run(main())





