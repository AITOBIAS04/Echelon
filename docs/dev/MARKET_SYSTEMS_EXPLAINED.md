# Market Systems Explained

## Two Market Endpoints

This project has **two separate market systems** for different purposes:

### 1. `/api/markets` - Mock Markets (Testing/Demo)

**Location:** `backend/api/markets.py`  
**Purpose:** Static mock data for testing and demos  
**Format:**
```json
[
  {
    "id": "trump_executive_order",
    "title": "Trump Signs Crypto Executive Order?",
    "yes_price": 0.78,
    "no_price": 0.22,
    "volume_24h": 22000.0
  }
]
```

**Characteristics:**
- 6 static markets
- Uses `yes_price`/`no_price` format
- No CPMM (Constant Product Market Maker)
- No real-time updates
- **Not used by frontend**

---

### 2. `/markets` - Real Markets (EventOrchestrator + CPMM)

**Location:** `backend/main.py` → `EventOrchestrator`  
**Purpose:** Real-time markets from OSINT signals with CPMM  
**Format:**
```json
{
  "markets": [
    {
      "id": "MKT_mission_taipei_1764355935_micro",
      "title": "⚠️ Air Superiority Mission Detected - Will It Succeed?",
      "outcome_odds": {"YES": 0.5, "NO": 0.5},
      "yes_shares": 1000.0,
      "no_shares": 1000.0,
      "total_volume": 0.0
    }
  ],
  "total": 9078,
  "filtered": 50
}
```

**Characteristics:**
- 50+ dynamic markets (generated from OSINT signals)
- Uses `outcome_odds` format
- **CPMM (Constant Product Market Maker)** for odds calculation
- Real-time updates when bets are placed
- Odds change based on liquidity (yes_shares/no_shares)
- **Used by frontend** ✅

---

## Frontend Configuration

The frontend correctly uses `/markets` (the real system):

```javascript
// frontend/utils/api.js
export const ENDPOINTS = {
  MARKETS: `${API_BASE}/markets`,  // ✅ Real EventOrchestrator
  // NOT: `${API_BASE}/api/markets`  // ❌ Mock (not used)
};
```

---

## Why Markets Show 50/50 Initially

**All new markets start at 50/50 odds** because:
1. Initial liquidity: `yes_shares = 1000.0`, `no_shares = 1000.0`
2. CPMM formula: `prob_yes = no_shares / (yes_shares + no_shares)`
3. With equal shares: `1000 / (1000 + 1000) = 0.5 = 50%`

**After a bet:**
- If you bet YES: `yes_shares` increases → YES odds decrease, NO odds increase
- If you bet NO: `no_shares` increases → NO odds decrease, YES odds increase

**Example:**
```
Before bet: YES 50% / NO 50% (1000/1000 shares)
After $50 YES bet: YES 47.6% / NO 52.4% (1048.5/953.7 shares)
```

---

## Bet Endpoint

**Endpoint:** `POST /markets/{market_id}/bet`  
**Authentication:** Wallet address via `X-Wallet-Address` header  
**Request:**
```json
{
  "outcome": "YES",
  "amount": 50
}
```

**Response:**
```json
{
  "success": true,
  "message": "Bet placed on YES. Price impact: 2.37%",
  "bet_id": "BET_MKT_...",
  "new_balance": 950.0,
  "potential_payout": 97.0
}
```

**What happens:**
1. User balance deducted
2. CPMM calculates shares received
3. Market `yes_shares`/`no_shares` updated
4. Market `outcome_odds` recalculated
5. Market `total_volume` increased
6. State saved to `data/markets.json`

---

## Debugging

### Check if odds are updating:
```bash
# Get a market
MARKET_ID=$(curl -s http://localhost:8000/markets | python3 -c "import sys,json; print(json.load(sys.stdin)['markets'][0]['id'])")

# Check odds before bet
curl -s "http://localhost:8000/markets/$MARKET_ID" | python3 -m json.tool | grep -A 5 "outcome_odds"

# Place a bet
curl -X POST "http://localhost:8000/markets/$MARKET_ID/bet" \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: 0x1234567890123456789012345678901234567890" \
  -d '{"outcome": "YES", "amount": 50}'

# Check odds after bet (should be different!)
curl -s "http://localhost:8000/markets/$MARKET_ID" | python3 -m json.tool | grep -A 5 "outcome_odds"
```

### Frontend console logs:
- `Markets API response:` - Shows full market data
- `Sample market odds:` - Shows CPMM state
- `⚠️ Market has default 50/50 odds:` - Warning if odds haven't updated

---

## Summary

✅ **Frontend uses `/markets`** (correct - EventOrchestrator with CPMM)  
✅ **Bet endpoint works** (`POST /markets/{id}/bet`)  
✅ **Odds update after bets** (CPMM recalculates)  
✅ **Markets persist** (saved to `data/markets.json`)  

❌ **`/api/markets` is mock data** (not used by frontend, for testing only)

