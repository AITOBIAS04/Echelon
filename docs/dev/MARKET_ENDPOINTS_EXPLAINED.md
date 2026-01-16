# Market Endpoints Explained

## ⚠️ CRITICAL: Two Different Market Systems

There are **TWO completely separate market systems** in this codebase:

### 1. `/api/markets` - Mock Markets (NOT USED BY FRONTEND)

**Location:** `backend/api/markets.py`

**Format:**
```json
{
  "id": "btc_100k_dec",
  "yes_price": 0.65,
  "no_price": 0.35,
  "volume_24h": 12000.0,
  "total_volume": 450000.0
}
```

**Characteristics:**
- Static mock data
- Simple price updates (not CPMM)
- In-memory only (no persistence)
- **NOT used by the frontend**

**Endpoints:**
- `GET /api/markets` - List mock markets
- `POST /api/markets/{id}/bet` - Place bet (updates prices slightly)

---

### 2. `/markets` - EventOrchestrator Markets (REAL - USED BY FRONTEND)

**Location:** `backend/main.py` (uses `EventOrchestrator`)

**Format:**
```json
{
  "id": "MKT_mission_taipei_1764355935_micro",
  "outcome_odds": {
    "YES": 0.5,
    "NO": 0.5
  },
  "yes_shares": 1000.0,
  "no_shares": 1000.0,
  "total_volume": 0.0
}
```

**Characteristics:**
- CPMM-based (Constant Product Market Maker)
- Persisted to disk (`data/markets.json`)
- Real-time odds calculation from liquidity
- **THIS is what the frontend uses**

**Endpoints:**
- `GET /markets` - List EventOrchestrator markets
- `GET /markets/{id}` - Get specific market
- `POST /markets/{id}/bet` - Place bet (updates CPMM state)
- `GET /markets/trending` - Get trending markets
- `GET /markets/stats` - Get market statistics

---

## Frontend Configuration

The frontend uses the **EventOrchestrator markets** (`/markets`):

```javascript
// frontend/utils/api.js
export const ENDPOINTS = {
  MARKETS: `${API_BASE}/markets`,  // ✅ EventOrchestrator
  MARKET_BET: (id) => `${API_BASE}/markets/${id}/bet`,  // ✅ EventOrchestrator
};
```

**NOT:**
```javascript
// ❌ This is NOT used
MARKETS: `${API_BASE}/api/markets`
```

---

## Testing the Correct Endpoint

### ✅ Correct (EventOrchestrator):
```bash
# List markets
curl http://localhost:8000/markets

# Get specific market
curl http://localhost:8000/markets/MKT_mission_taipei_1764355935_micro

# Place bet
curl -X POST "http://localhost:8000/markets/MKT_mission_taipei_1764355935_micro/bet" \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: 0x1234567890123456789012345678901234567890" \
  -d '{"outcome": "YES", "amount": 100}'
```

### ❌ Wrong (Mock Markets):
```bash
# This is the mock endpoint - NOT used by frontend
curl http://localhost:8000/api/markets
```

---

## Why Two Systems?

The `/api/markets` endpoint appears to be legacy/example code that was never removed. The real system uses EventOrchestrator with CPMM.

**Recommendation:** Consider removing `/api/markets` to avoid confusion, or clearly document it as a mock/example endpoint.

---

## Current Issue

The bet endpoint (`POST /markets/{id}/bet`) is returning **500 Internal Server Error**. This needs to be fixed to test CPMM odds updates.

**Check backend logs** when placing a bet to see the actual exception causing the 500 error.

