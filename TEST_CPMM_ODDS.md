# CPMM Odds Test Results

## Current Status

### Market State (from curl test)
All markets are showing:
- `yes_shares: 1000.0`
- `no_shares: 1000.0`
- `outcome_odds: {"YES": 0.5, "NO": 0.5}`

This confirms markets are at default CPMM state (50/50 odds).

### Bet Endpoint Test
**Result:** ❌ 500 Internal Server Error

```bash
curl -X POST "http://localhost:8000/markets/MKT_mission_taipei_1764355935_micro/bet" \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: 0x1234567890123456789012345678901234567890" \
  -d '{"outcome": "YES", "amount": 100}'
```

**Response:** `Internal Server Error`

## Diagnosis Steps

### 1. Check Backend Logs
The 500 error suggests an exception in the bet endpoint. Check backend console for:
- Database connection errors
- User creation failures
- CPMM calculation errors
- Market not found errors

### 2. Verify Database Connection
The `get_user_or_wallet` function creates users in the database. Check:
- Is the database running?
- Are migrations applied?
- Can users be created?

### 3. Test with JWT Token Instead
Try authenticating with a JWT token instead of wallet address:

```bash
# First, get a token (if you have login endpoint)
TOKEN=$(curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test" | jq -r '.access_token')

# Then place bet with token
curl -X POST "http://localhost:8000/markets/MARKET_ID/bet" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"outcome": "YES", "amount": 100}'
```

### 4. Check Market Persistence
Verify markets are being saved to disk:

```bash
# Check if markets.json exists
ls -lh data/markets.json

# View saved markets
cat data/markets.json | jq '.["data"] | keys | length'
```

### 5. Manual CPMM Test
Test CPMM calculation directly:

```python
from backend.core.cpmm import CPMM

cpmm = CPMM(initial_liquidity=1000.0)
print("Initial odds:", cpmm.get_current_odds())

shares, impact, new_odds = cpmm.execute_trade("YES", 100.0)
print("After $100 YES bet:")
print("  Shares received:", shares)
print("  Price impact:", impact)
print("  New odds:", new_odds)
print("  YES shares:", cpmm.state.yes_shares)
print("  NO shares:", cpmm.state.no_shares)
```

## Expected Behavior After Fix

**Before Bet:**
- YES shares: 1000.0
- NO shares: 1000.0
- YES odds: 0.5000
- NO odds: 0.5000

**After $100 YES Bet:**
- YES shares: ~1097.0 (increased)
- NO shares: ~911.0 (decreased to maintain k = x * y)
- YES odds: ~0.4545 (decreased - more YES shares means lower YES price)
- NO odds: ~0.5455 (increased)
- Total volume: 100.0

## Next Steps

1. **Fix the 500 error** - Check backend logs to identify the exception
2. **Verify database** - Ensure user creation works
3. **Test bet placement** - Once 500 error is fixed, verify odds update
4. **Check persistence** - Verify markets are saved after bets
5. **Frontend test** - Once backend works, test from UI

## Debug Logs to Check

When the bet endpoint works, you should see in backend console:
```
🔍 [BET DEBUG] Market MKT_... BEFORE bet:
   yes_shares: 1000.0
   no_shares: 1000.0
   bet: YES $100

🔍 [BET DEBUG] Market MKT_... AFTER bet:
   yes_shares: 1097.0
   no_shares: 911.0
   new_odds: {'YES': 0.4545, 'NO': 0.5455}

💾 Saved N markets to disk
```

