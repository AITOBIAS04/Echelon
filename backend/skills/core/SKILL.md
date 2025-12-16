# 🎯 Core Agent Skills

**Archetype:** CORE
**Role:** Universal Foundation
**Tier:** Base Capabilities

---

## Identity

Core skills are the foundational capabilities shared by ALL Echelon agents. Every Shark, Spy, Diplomat, and Saboteur inherits these base abilities. They provide the fundamental decision-making framework upon which specialised skills are built.

---

## Capabilities

### 1. Market Analysis
Read and interpret market conditions.

**Key Metrics:**
| Metric | Description | Usage |
|--------|-------------|-------|
| `yes_price` | Current YES share price (0-1) | Direction signal |
| `liquidity` | Available capital in pool | Size limits |
| `spread` | Bid-ask gap | Opportunity indicator |
| `volume_24h` | Recent trading activity | Interest level |
| `hours_to_expiry` | Time remaining | Urgency factor |

### 2. Risk Assessment
Evaluate and size positions appropriately.

**Position Sizing Rules:**
```
max_position = min(
    wallet_balance * 0.1,           # Never >10% of wallet
    market_liquidity * 0.1,         # Never >10% of liquidity
    confidence * base_size          # Scale with confidence
)
```

### 3. Signal Processing
Interpret OSINT signals and market data.

**Signal Categories:**
- **Price:** Direct market movements
- **Volume:** Trading activity changes
- **Sentiment:** News and social signals
- **Whale:** Large position movements
- **Anomaly:** Unusual patterns

### 4. Wallet Management
Track capital allocation across positions.

---

## Decision Framework

```
┌─────────────────────────────────────────┐
│        UNIVERSAL DECISION FLOW          │
└─────────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │ 1. ASSESS STATE  │
         │ (position, wallet)│
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ 2. READ MARKET   │
         │ (price, liquidity)│
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ 3. PROCESS SIGNALS│
         │ (OSINT, news)    │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ 4. APPLY ARCHETYPE│
         │ (specialised logic)│
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ 5. EXECUTE & LOG │
         └──────────────────┘
```

---

## Universal Parameters

All agents share these base parameters:

| Parameter | Range | Description |
|-----------|-------|-------------|
| `bankroll` | 0-∞ | Available capital (USDC) |
| `influence` | 0-1 | Impact on global state |
| `resilience` | 0-1 | Resistance to chaos events |
| `aggression` | 0-1 | Risk-taking tendency |
| `loyalty` | 0-1 | Commitment to alliances |
| `adaptability` | 0-1 | Response to change |

---

## Best Practices

- **Always know your position** - Track exposure at all times
- **Size based on confidence** - Higher confidence = larger position
- **Respect liquidity limits** - Never exceed 10% of market
- **Log all decisions** - Enable learning and debugging
- **Adapt to conditions** - Markets change, strategies must too

---

## Anti-Patterns

- ❌ **Ignoring position size** - Leads to over-exposure
- ❌ **Trading without edge** - Random = losing
- ❌ **Emotional decisions** - Stick to framework
- ❌ **Ignoring signals** - OSINT exists for a reason

---

*"Every master was once a student. Core skills are the foundation upon which legends are built."*
