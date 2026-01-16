# Bet Endpoint 500 Error - Debugging Guide

## Current Status

✅ **Frontend Configuration:**
- Using `/markets` endpoint (correct - EventOrchestrator)
- NOT using `/api/markets` (mock)
- Wallet providers configured correctly (OnchainKitProvider)

❌ **Bet Endpoint:**
- Returns 500 Internal Server Error
- Need to check backend console logs for exception

## Test Results

```bash
# Market BEFORE bet:
YES shares: 1000.0
NO shares: 1000.0
YES odds: 0.5000
NO odds: 0.5000

# Bet request:
POST /markets/MKT_mission_taipei_1764355935_micro/bet
Response: 500 Internal Server Error

# Market AFTER bet (unchanged):
YES shares: 1000.0
NO shares: 1000.0
YES odds: 0.5000
NO odds: 0.5000
```

## Debugging Steps

### 1. Check Backend Console Logs

When you place a bet, the backend should log:

**If working:**
```
🔍 [BET] Starting bet placement for market MKT_...
🔍 [BET] User: wallet_12345678, Balance: 1000.0
🔍 [BET] Bet: YES $100
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

**If error:**
```
❌ [BET ERROR] Exception in place_bet:
   Error: [exception message]
   Type: [exception type]
   Traceback:
   [full stack trace]
```

### 2. Common Issues

#### A. Database Connection Error
**Symptom:** Error creating user or updating balance
**Fix:** Ensure database is running and migrations applied

#### B. User Creation Failure
**Symptom:** `get_user_or_wallet` fails to create user
**Fix:** Check database schema has `wallet_address` field

#### C. CPMM Import Error
**Symptom:** `from backend.core.cpmm import CPMM` fails
**Fix:** Ensure `backend/core/cpmm.py` exists and is importable

#### D. Market Not Found
**Symptom:** Market ID doesn't exist in orchestrator
**Fix:** Check market ID matches exactly (case-sensitive)

#### E. Balance Insufficient
**Symptom:** User balance < bet amount
**Fix:** Check user creation sets `play_money_balance=1000.0`

### 3. Manual Database Check

```bash
# Check if users table exists and has wallet_address column
# (if using SQLite, check the database file)
```

### 4. Test User Creation Directly

```python
# Test in Python REPL
from backend.core.database import SessionLocal, User as DBUser
db = SessionLocal()
user = db.query(DBUser).filter(DBUser.wallet_address == "0x1234567890123456789012345678901234567890").first()
if not user:
    user = DBUser(
        username="wallet_12345678",
        email="12345678@wallet.local",
        hashed_password="",
        wallet_address="0x1234567890123456789012345678901234567890",
        play_money_balance=1000.0
    )
    db.add(user)
    db.commit()
    print("User created:", user.id)
else:
    print("User exists:", user.id, "Balance:", user.play_money_balance)
```

### 5. Test CPMM Import

```python
# Test in Python REPL
from backend.core.cpmm import CPMM
cpmm = CPMM(initial_liquidity=1000.0)
print("CPMM works:", cpmm.get_current_odds())
```

## Expected Behavior After Fix

Once the 500 error is resolved:

1. **Bet succeeds** - Returns 200 with bet details
2. **Market shares update** - YES shares increase, NO shares decrease
3. **Odds recalculate** - YES odds decrease, NO odds increase
4. **Market persists** - Saved to `data/markets.json`
5. **Frontend updates** - Odds change in UI within 5 seconds

## Next Steps

1. **Check backend console** when placing bet
2. **Look for** `❌ [BET ERROR]` log message
3. **Share the error message** to fix the specific issue
4. **Once fixed**, retest the bet endpoint
5. **Verify odds update** in both API and frontend

