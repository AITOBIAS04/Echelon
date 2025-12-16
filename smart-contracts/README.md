# Echelon Protocol - Timeline Shards Smart Contracts

## Phase 2: Timeline Shards Contracts

This package contains the smart contracts implementing Echelon's deflationary Timeline Shard mechanics, including bonding curves, VRF integration, faction warfare, and Hot Potato events.

---

## Contract Overview

### 1. TimelineShard.sol (ERC-1155)

The core token contract representing positions in counterfactual timeline markets.

**Key Features:**
- **Bonding Curve Pricing:** `price = basePrice × (1 + supply/scaleFactor)²`
- **Timeline Management:** Fork canonical reality into parallel universes
- **Market Creation:** Multiple outcomes per timeline with distinct tokens
- **Deflationary Mechanics:**
  - Reality Reaper: OSINT-triggered instant destruction
  - Quantum Decay: VRF-based daily percentage burn (2-5%)
  - Agent Shield: Shark-backed shards gain temporary immunity

**Token ID Encoding:**
```
tokenId = (timelineId << 128) | (marketId << 64) | outcomeIndex
```

**Roles:**
- `TIMELINE_MANAGER_ROLE` - Create timelines and markets
- `REAPER_ROLE` - Trigger Reality Reaper events
- `DECAY_ROLE` - Execute Quantum Decay
- `AGENT_ROLE` - Apply Agent Shields

---

### 2. SabotagePool.sol

Manages faction warfare, War Tax collection, and FUD (Fear, Uncertainty, Doubt) mechanics.

**War Tax Mechanics:**
- Every trade contributes 0.5% to faction war chests
- Factions use war chests to attack rival timelines
- Successful attacks trigger accelerated decay

**Attack Types:**
| Type | Base Success | Effect |
|------|-------------|--------|
| Raid | 40% | Direct timeline damage |
| Infiltrate | 50% | Plant sleeper agents |
| Propaganda | 60% | Spread FUD |
| Economic | 35% | Drain liquidity |

**FUD Fund Mechanics:**
- Saboteur agents contribute to FUD funds
- When threshold reached (default: 1000 USDC), triggers Mass Panic
- Mass Panic causes 2× decay on all shards in affected market

---

### 3. EchelonVRFConsumer.sol

Chainlink VRF integration for provably fair randomness.

**VRF Use Cases:**
1. **Timeline Fork Seeds** - Determine how timelines diverge
2. **Quantum Decay** - Random daily shard burning
3. **Attack Resolution** - Determine faction attack outcomes
4. **Hot Potato** - Random bomb transfers

**Configuration (Polygon):**
```solidity
VRF Coordinator: 0xAE975071Be8F8eE67addBC1A82488F1C24858067
Key Hash: 0xcc294a196eeeb44da2888d17c0625cc88d70d9760a69d58d853ba6581a9ab0cd
```

---

### 4. HotPotatoEvents.sol

High-drama "Musical Chairs" mechanic creating viral moments.

**Mechanics:**
- **The Bomb:** 60-minute countdown on one timeline bubble
- **The Pop:** Timer expires = bubble eliminated, shards destroyed
- **The Pass:** Pay Bribe Fee to pass bomb to neighbour
- **The Catch:** Each pass shortens timer (60m → 50m → 40m...)

**Prize Distribution:**
| Recipient | Percentage |
|-----------|------------|
| Survivors | 70% |
| Last Passer | 20% |
| Protocol | 10% |

---

## Deployment

### Prerequisites

```bash
npm install
cp .env.example .env
# Fill in your private key and RPC URLs
```

### Local Testing

```bash
npx hardhat test
npx hardhat coverage
```

### Deploy to Testnet (Base Sepolia)

```bash
npx hardhat run scripts/deploy.js --network baseSepolia
```

### Deploy to Mainnet

```bash
# Polygon (for Polymarket integration)
npx hardhat run scripts/deploy.js --network polygon

# Base (for Virtuals Protocol integration)
npx hardhat run scripts/deploy.js --network base
```

---

## Integration Points

### Polymarket Integration
- Settlement: USDC on Polygon
- Agent Wallets: Gnosis Safe via Relayer (gasless)
- VRF: Chainlink VRF v2
- API: CLOB + Gamma Markets

### Kalshi Integration
- Settlement: SPL tokens on Solana
- Agent Wallets: Programmatic Solana keypairs
- VRF: Switchboard VRF
- API: DFlow API

### Virtuals Protocol Integration
- Chain: Base
- Agent Identity: ERC-6551 Token Bound Accounts
- Payments: x402 micropayment protocol

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ECHELON PROTOCOL                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Timeline   │    │  Sabotage   │    │  Hot Potato │     │
│  │   Shard     │◄──►│    Pool     │◄──►│   Events    │     │
│  │  (ERC-1155) │    │  (Factions) │    │  (Drama)    │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         └────────────┬─────┴────────┬─────────┘             │
│                      │              │                       │
│               ┌──────▼──────┐       │                       │
│               │   Echelon   │       │                       │
│               │     VRF     │◄──────┘                       │
│               │  Consumer   │                               │
│               └──────┬──────┘                               │
│                      │                                      │
│               ┌──────▼──────┐                               │
│               │  Chainlink  │                               │
│               │   VRF v2    │                               │
│               └─────────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Gas Estimates

| Operation | Estimated Gas | Cost (@ 30 gwei) |
|-----------|---------------|------------------|
| Create Timeline | ~150,000 | ~0.0045 ETH |
| Create Market | ~200,000 | ~0.006 ETH |
| Buy Shards | ~120,000 | ~0.0036 ETH |
| Sell Shards | ~100,000 | ~0.003 ETH |
| Apply Shield | ~80,000 | ~0.0024 ETH |
| Pass Bomb | ~90,000 | ~0.0027 ETH |
| Launch Attack | ~150,000 | ~0.0045 ETH |

---

## Security Considerations

1. **Architectural Isolation:** Strict separation between Market Engine (deterministic) and Agent Logic (probabilistic)
2. **VRF for Fairness:** All random outcomes use Chainlink VRF
3. **Access Control:** Role-based permissions for sensitive operations
4. **Reentrancy Protection:** All external calls use ReentrancyGuard
5. **Pausability:** Emergency pause functionality on all contracts

---

## Audit Status

- [ ] Internal review
- [ ] External audit (planned for Month 2)
- [ ] Bug bounty programme (planned for Month 3)

---

## Contact

- **Email:** playechelon@gmail.com
- **X:** @playechelon
- **Telegram:** @playechelon
- **GitHub:** github.com/AITOBIAS04/prediction-market-monorepo

---

## Licence

MIT License - see LICENSE file for details.
