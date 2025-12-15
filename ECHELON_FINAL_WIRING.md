# Echelon Final Wiring

## Overview

This completes the Echelon architecture by connecting all four pillars:

| Pillar | Components | Status |
|--------|------------|--------|
| **Brain** | Agent Skills, Brain Router | ✅ Complete |
| **Body** | Multi-Chain Wallets, x402 | ✅ Complete |
| **World** | Timeline Forks, Hot Potato | ✅ Complete |
| **Laws** | Smart Contracts | ✅ Complete |
| **Hands** | Execution Router | ✅ **NEW** |

---

## New Files

### 1. Agent Execution (`backend/agents/agent_execution.py`)

Connects agent decisions to real market execution:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Agent Brain   │ ──> │ Execution Router│ ──> │  Platform API   │
│   (Decision)    │     │  (Routing)      │     │  (Execution)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               v
                        ┌─────────────────┐
                        │  Agent Wallet   │
                        │  (Signing)      │
                        └─────────────────┘
```

**Features:**
- Routes to Polymarket (Polygon), Kalshi (Solana), or Echelon (Base)
- Uses agent's chain-specific wallet for signing
- Respects x402 daily spending limits
- Dry-run mode for testing

**Usage:**
```python
from backend.agents.agent_execution import ExecutionRouter, AgentBridge
from backend.wallets.wallet_factory import MultiChainWalletFactory

# Initialize
wallets = MultiChainWalletFactory(use_testnet=True)
router = ExecutionRouter(wallet_factory=wallets, dry_run=True)
bridge = AgentBridge(execution_router=router)

# Execute decision
result = await bridge.process_agent_decision(
    agent_id="SHARK_001",
    decision_type="buy",
    market_data={
        "platform": "polymarket",
        "market_id": "0x123",
        "price": 0.65,
        "confidence": 0.8,
        "params": {"size": 100}
    }
)
```

---

### 2. Deployment Script (`smart-contracts/scripts/deploy.js`)

Deploys and wires all contracts:

```bash
# Deploy to Base Sepolia
npx hardhat run scripts/deploy.js --network baseSepolia

# Deploy to Polygon Mumbai
npx hardhat run scripts/deploy.js --network polygonMumbai
```

**Deployment Order:**
1. TimelineShard.sol (ERC-1155 shards)
2. SabotagePool.sol (FUD mechanics)
3. HotPotatoEvents.sol (Hot Potato game)
4. EchelonVRFConsumer.sol (Randomness)

**Permission Wiring:**
- VRF Consumer → DECAY_ROLE on Shard
- VRF Consumer → REAPER_ROLE on Shard
- Hot Potato → TIMELINE_MANAGER_ROLE on Shard
- Sabotage Pool → AGENT_ROLE on Shard

---

## Testnet Launch Checklist

### Prerequisites

- [ ] Node.js 18+ installed
- [ ] Python 3.10+ installed
- [ ] Hardhat configured
- [ ] Test ETH on Base Sepolia ([faucet](https://www.coinbase.com/faucets/base-ethereum-goerli-faucet))
- [ ] Test MATIC on Polygon Mumbai ([faucet](https://faucet.polygon.technology/))

### Step 1: Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit with your values
nano .env
```

Required values:
- `PRIVATE_KEY` - Your deployer wallet
- `TREASURY_ADDRESS` - Where fees go
- `VRF_SUB_ID` - From vrf.chain.link

### Step 2: Compile Contracts

```bash
cd smart-contracts
npm install
npx hardhat compile
```

### Step 3: Deploy Contracts

```bash
# Base Sepolia (for Echelon internal)
npx hardhat run scripts/deploy.js --network baseSepolia

# Polygon Mumbai (for Polymarket testing)
npx hardhat run scripts/deploy.js --network polygonMumbai
```

Save the output addresses to your `.env`:
```
TIMELINE_SHARD_ADDRESS=0x...
SABOTAGE_POOL_ADDRESS=0x...
HOT_POTATO_ADDRESS=0x...
VRF_CONSUMER_ADDRESS=0x...
```

### Step 4: Fund VRF Subscription

1. Go to [vrf.chain.link](https://vrf.chain.link)
2. Create subscription (or use existing)
3. Fund with LINK tokens
4. Add VRF Consumer address as consumer

### Step 5: Verify Contracts

```bash
npx hardhat verify --network baseSepolia <address> <constructor_args>
```

### Step 6: Test Backend Integration

```bash
cd backend
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Test execution (dry run)
python -m backend.agents.agent_execution
```

### Step 7: Create Demo Accounts

**Kalshi:**
1. Go to [demo.kalshi.co](https://demo.kalshi.co)
2. Create account
3. Add credentials to `.env`

**Polymarket:**
1. Apply to builder programme
2. Wait for approval
3. Add API keys when received

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ECHELON PROTOCOL                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │
│  │   OSINT     │   │   Mission   │   │  Timeline   │               │
│  │   Pipeline  │──>│   Factory   │──>│   Manager   │               │
│  └─────────────┘   └─────────────┘   └─────────────┘               │
│         │                                   │                       │
│         v                                   v                       │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │
│  │   Agent     │   │   Brain     │   │  Execution  │               │
│  │   Skills    │──>│   Router    │──>│   Router    │               │
│  └─────────────┘   └─────────────┘   └─────────────┘               │
│         │               │                   │                       │
│         │        ┌──────┴──────┐            │                       │
│         │        │             │            │                       │
│         v        v             v            v                       │
│  ┌─────────────────────────────────────────────────┐               │
│  │              MULTI-CHAIN WALLETS                │               │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐         │               │
│  │  │  Base   │  │ Polygon │  │ Solana  │         │               │
│  │  │ERC-6551 │  │  Safe   │  │ Keypair │         │               │
│  │  └────┬────┘  └────┬────┘  └────┬────┘         │               │
│  └───────┼────────────┼────────────┼──────────────┘               │
│          │            │            │                               │
│          v            v            v                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                  │
│  │ TimelineShard│ │ Polymarket │ │   Kalshi   │                  │
│  │   (Base)    │ │  (Polygon) │ │  (Solana)  │                  │
│  └─────────────┘ └─────────────┘ └─────────────┘                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
echelon/
├── backend/
│   ├── agents/
│   │   ├── agent_execution.py    # NEW - Execution router
│   │   ├── brain_router.py       # Layer 1/2 routing
│   │   ├── genealogy_manager.py  # Breeding system
│   │   └── archetypes/           # Shark, Spy, etc.
│   ├── integrations/
│   │   ├── polymarket_client.py  # Polymarket API
│   │   ├── kalshi_client.py      # Kalshi API
│   │   └── builder_attribution.py
│   ├── timeline/
│   │   └── fork_manager.py       # User forks
│   └── wallets/
│       └── wallet_factory.py     # Multi-chain wallets
│
├── smart-contracts/
│   ├── contracts/
│   │   ├── TimelineShard.sol
│   │   ├── SabotagePool.sol
│   │   ├── HotPotatoEvents.sol
│   │   └── EchelonVRFConsumer.sol
│   └── scripts/
│       └── deploy.js             # NEW - Deployment script
│
├── frontend/
│   └── components/
│       └── HotPotatoGame.tsx
│
└── .env.example                  # NEW - Environment template
```

---

## Next Steps

1. **Deploy to testnet** - Run deployment script
2. **Test agent execution** - Dry run first, then with test funds
3. **Apply to builder programmes** - Polymarket and Kalshi
4. **Build demo video** - Record the Situation Room in action
5. **Submit grant applications** - With working testnet demo

---

## Contact

- **Email:** playechelon@gmail.com
- **X:** @playechelon
- **GitHub:** github.com/AITOBIAS04/prediction-market-monorepo
