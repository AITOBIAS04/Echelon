# Echelon Phase 4: Advanced Mechanics

## Overview

Phase 4 implements the advanced game mechanics and infrastructure for Echelon:

1. **Timeline Fork Manager** - User-specific fork support
2. **Hot Potato Frontend** - High-drama UI component
3. **Agent Genealogy System** - Breeding and trait inheritance
4. **Multi-Chain Wallet Factory** - Cross-chain agent wallets

---

## 1. Timeline Fork Manager (`backend/timeline/fork_manager.py`)

### User-Specific Forks Analysis

**Current Contract Architecture (TimelineShard.sol):**
- Timelines are global - shared by all users
- No creator/owner tracking
- No visibility settings
- No capital segregation per user

**Enhanced Architecture (This Module):**

| Fork Type | Storage | Capital | Use Case |
|-----------|---------|---------|----------|
| Global | On-chain | Real USDC | Shared markets |
| User Private | Off-chain | Simulated | Personal exploration |
| User Public | Off-chain | Simulated | Shareable scenarios |
| Agent Sandbox | Off-chain | Simulated | Training environments |

### Features

```python
from backend.timeline.fork_manager import TimelineForkManager, ForkVisibility

manager = TimelineForkManager()

# Create global fork (on-chain)
global_fork = await manager.create_global_fork(
    source_market_id="0x123",
    source_platform="polymarket",
    premise="What if Fed cut rates?",
    duration_hours=48
)

# Create user-specific fork (off-chain)
user_fork = await manager.create_user_fork(
    user_address="0xUser123",
    source_market_id="0x456",
    source_platform="kalshi",
    premise="What if Bitcoin hit $200k?",
    config=UserForkConfig(
        visibility=ForkVisibility.PRIVATE,
        simulated_capital=Decimal("50000")
    )
)

# Check access
can_trade = await manager.can_user_trade_fork("0xUser123", fork_id)

# Get leaderboard
leaderboard = await manager.get_fork_leaderboard(fork_id)
```

### Recommendation

**Hybrid approach:**
- Keep global forks on-chain for real capital and verification
- Use off-chain for user exploration (cheaper, scalable)
- "Graduate" popular user forks to global when warranted

---

## 2. Hot Potato Game (`frontend/components/HotPotatoGame.tsx`)

### Features

- **Real-time countdown timer** with visual urgency
- **Animated bomb icon** with shake effect
- **Timeline bubble visualisation** with elimination states
- **Prize pool tracker** with distribution breakdown
- **Pass history feed** showing all bomb transfers
- **Responsive bribe fee display** (10% increase per pass)

### Component Structure

```tsx
<HotPotatoGame
  eventId="event_123"
  userAddress="0xUser..."
  onPassBomb={(targetIndex) => contract.passBomb(eventId, targetIndex)}
  onClaimReward={() => contract.claimSurvivorReward(eventId)}
/>
```

### Sub-components

| Component | Purpose |
|-----------|---------|
| `CountdownTimer` | Displays MM:SS with urgency colours |
| `BombIcon` | Animated SVG bomb with spark |
| `TimelineBubbleCard` | Individual timeline bubble |
| `PrizePoolDisplay` | Shows pool and distribution |
| `PassHistoryFeed` | Scrollable pass log |

### Visual Design

- Dark theme (`#1a1a2e` background)
- Red (#FF4136) for danger/bomb
- Green (#2ECC40) for safe states
- Yellow (#FFDC00) for prizes
- Pulse animation when timer < 60s
- Shake animation on bomb holder

---

## 3. Agent Genealogy System (`backend/agents/genealogy_manager.py`)

### Breeding Mechanics

**Requirements to breed:**
1. Both parents must be ACTIVE status
2. Both must have sufficient breeding points (default: 1000)
3. Breeding cooldown must have passed (default: 7 days)
4. Cannot breed with self, direct parent, or offspring

**Inheritance:**
- 40% chance each parent's archetype
- 20% chance mutation to different archetype
- Traits blend with ±10 variation
- Inheritance chance per trait (default: 70%)
- Mutation chance per trait (default: 10%)

### Sleeper Genes

Saboteur agents have a special mechanic:
- `sleeper_gene` can skip 2-3 generations
- Creates "hidden_saboteur" dormant trait
- Activates in grandchildren/great-grandchildren
- Creates paranoia metagame

### Agent Traits by Archetype

| Archetype | Base Traits | Possible Mutations |
|-----------|-------------|-------------------|
| Shark | aggression, speed, market_sense | frenzy_mode, blood_scent |
| Spy | accuracy, discretion, source_network | deep_cover, double_agent |
| Diplomat | charisma, negotiation, loyalty | silver_tongue, alliance_builder |
| Saboteur | deception, patience, dormancy | sleeper, mole, chaos_agent |

### Usage

```python
from backend.agents.genealogy_manager import GenealogyManager, AgentArchetype

manager = GenealogyManager()

# Create genesis agents
shark = await manager.create_genesis_agent(
    archetype=AgentArchetype.SHARK,
    name="MEGALODON",
    owner_address="0xOwner1"
)

# Earn breeding points through performance
shark.breeding_points = 1000

# Request breeding
request = await manager.request_breeding(
    parent1_id=shark.agent_id,
    parent2_id=spy.agent_id,
    requester_address="0xBreeder"
)

# Execute with VRF seed
result = await manager.execute_breeding(request_id, vrf_seed)

print(f"Offspring: {result.offspring.name}")
print(f"Generation: {result.offspring.genome.generation}")
print(f"Mutations: {result.mutations}")
```

---

## 4. Multi-Chain Wallet Factory (`backend/wallets/wallet_factory.py`)

### Sandwich Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT WALLET SET                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Identity       │  │  Polymarket     │  │   Kalshi    │ │
│  │  (Base)         │  │  (Polygon)      │  │   (Solana)  │ │
│  │  ERC-6551       │  │  Gnosis Safe    │  │   Keypair   │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                  │         │
│           └────────────────────┼──────────────────┘         │
│                                │                            │
│                    ┌───────────▼───────────┐                │
│                    │   x402 Protocol       │                │
│                    │   (Micropayments)     │                │
│                    └───────────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Wallet Types

| Chain | Wallet Type | Purpose |
|-------|-------------|---------|
| Base | ERC-6551 (Token Bound) | Agent identity, Virtuals Protocol |
| Polygon | Gnosis Safe | Polymarket trading (gasless via relayer) |
| Solana | Programmatic Keypair | Kalshi SPL settlement |

### Features

- **HD Derivation** - Coordinated wallets from single seed
- **x402 Protocol** - Daily spending limits for autonomous payments
- **Cross-chain bridging** - CCIP/Wormhole integration
- **Balance tracking** - Aggregated across all chains

### Usage

```python
from backend.wallets.wallet_factory import MultiChainWalletFactory

factory = MultiChainWalletFactory(use_testnet=True)

# Create wallet set
wallet_set = await factory.create_agent_wallet_set(
    agent_id="SHARK_001",
    agent_token_contract="0xVirtuals...",
    agent_token_id="12345"
)

# Activate wallets (deploy contracts)
await factory.activate_wallet_set("SHARK_001")

# x402 micropayment
await factory.record_x402_payment(
    agent_id="SHARK_001",
    amount=Decimal("10"),
    recipient="0xSpyAgent",
    purpose="intel_purchase"
)

# Bridge funds
await factory.initiate_bridge(
    agent_id="SHARK_001",
    from_chain=Chain.BASE,
    to_chain=Chain.POLYGON,
    token="USDC",
    amount=Decimal("100")
)
```

---

## File Structure

```
echelon_phase4/
├── backend/
│   ├── timeline/
│   │   └── fork_manager.py      # User-specific forks
│   ├── agents/
│   │   └── genealogy_manager.py # Breeding & traits
│   └── wallets/
│       └── wallet_factory.py    # Multi-chain wallets
├── frontend/
│   └── components/
│       └── HotPotatoGame.tsx    # Hot Potato UI
└── README.md                    # This file
```

---

## Integration Notes

### With Phase 2 (Contracts)

- `fork_manager.py` coordinates with `TimelineShard.sol` for global forks
- `genealogy_manager.py` VRF requests go through `EchelonVRFConsumer.sol`
- `wallet_factory.py` deploys wallets that interact with `HotPotatoEvents.sol`

### With Phase 3 (Platform Integration)

- User forks can source prices from `polymarket_client.py` / `kalshi_client.py`
- Wallet factory wallets are used by platform clients for trading
- Builder attribution tracks trades across all wallet types

---

## Next Steps

- [ ] Integrate fork_manager with TimelineShard contract calls
- [ ] Add WebSocket support to HotPotatoGame for real-time updates
- [ ] Implement actual HD derivation (BIP-32/BIP-44) in wallet factory
- [ ] Add genealogy visualization component
- [ ] Deploy to testnet for integration testing

---

## Contact

- **Email:** playechelon@gmail.com
- **X:** @playechelon
- **GitHub:** github.com/AITOBIAS04/prediction-market-monorepo
