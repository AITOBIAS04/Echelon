# CPMM Odds Debugging Guide

## Issue: Odds showing 50/50 even after bets

### Root Cause
The `_save_markets_state()` method was NOT saving `yes_shares` and `no_shares` to disk, causing markets to reset to 1000/1000 on every server restart.

### Fix Applied
1. ✅ Fixed `_save_markets_state()` to include `yes_shares` and `no_shares`
2. ✅ Added `orchestrator._save_markets_state()` call after each bet
3. ✅ Added debug logging to bet endpoint (before/after shares)
4. ✅ Added debug logging to `/markets` endpoint (sample market shares)

### Testing Steps

#### 1. Test Market Endpoint
```bash
# Get a market ID
curl http://localhost:8000/markets | jq '.markets[0].id'

# Check market state
curl http://localhost:8000/markets/MARKET_ID | jq '{yes_shares, no_shares, outcome_odds}'
```

#### 2. Place a Bet
```bash
# Place bet (requires wallet address header)
curl -X POST "http://localhost:8000/markets/MARKET_ID/bet" \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: 0x1234567890123456789012345678901234567890" \
  -d '{"outcome": "YES", "amount": 100}'
```

#### 3. Verify Odds Changed
```bash
# Check market again - odds should have changed
curl http://localhost:8000/markets/MARKET_ID | jq '{yes_shares, no_shares, outcome_odds}'
```

### Expected Behavior

**Before Bet:**
- `yes_shares: 1000.0`
- `no_shares: 1000.0`
- `outcome_odds: {"YES": 0.5, "NO": 0.5}`

**After Bet on YES ($100):**
- `yes_shares: ~1097.0` (increased)
- `no_shares: ~911.0` (decreased to maintain k = x * y)
- `outcome_odds: {"YES": ~0.45, "NO": ~0.55}` (YES price decreased)

### Debug Logs

Check backend console for:
- `🔍 [BET DEBUG] Market ... BEFORE bet:` - Shows shares before bet
- `🔍 [BET DEBUG] Market ... AFTER bet:` - Shows shares after bet
- `💾 Saved N markets to disk` - Confirms persistence
- `🔍 [MARKETS DEBUG] Sample market ...` - Shows sample market shares in /markets endpoint

### Two Market Systems

**Important:** There are TWO different market systems:

1. **`/api/markets`** - Mock markets from `backend/api/markets.py`
   - Uses `yes_price`/`no_price` format
   - Static mock data
   - NOT used by frontend

2. **`/markets`** - Real markets from EventOrchestrator (`backend/main.py`)
   - Uses `outcome_odds`, `yes_shares`/`no_shares` format
   - CPMM-based with persistence
   - **This is what the frontend uses**

### Frontend Endpoints

The frontend uses:
- `ENDPOINTS.MARKETS` = `${API_BASE}/markets` ✅ (Correct - EventOrchestrator)
- `ENDPOINTS.MARKET_BET(id)` = `${API_BASE}/markets/${id}/bet` ✅ (Correct)

### Persistence Files

Markets are saved to:
- `data/markets.json` - Contains all markets with `yes_shares`/`no_shares`
- `data/stats.json` - Orchestrator statistics

### If Odds Still Don't Update

1. **Check backend logs** for debug messages
2. **Verify persistence** - Check `data/markets.json` contains `yes_shares`/`no_shares`
3. **Check market ID** - Ensure you're using the same market ID from `/markets` (not `/api/markets`)
4. **Verify bet succeeded** - Check response for success message
5. **Check frontend refresh** - Frontend auto-refreshes every 5 seconds, but you can force refresh

