# Railway Deployment Setup

## Required Environment Variables

In your **backend service** in Railway, set these variables:

### 1. `USE_MOCKS=false`
**CRITICAL**: This must be set to `false` (lowercase) to use the real database instead of mocks.

**How to set:**
1. Go to your backend service in Railway
2. Click "Variables" tab
3. Add or update: `USE_MOCKS=false`
4. Railway will automatically redeploy

### 2. `DATABASE_URL` (Auto-set by Railway)
Railway automatically shares `DATABASE_URL` from your PostgreSQL service to your backend service. 

**Verify it's set:**
- In your backend service Variables tab
- Look for `DATABASE_URL`
- It should be: `postgresql://postgres:...@postgres.railway.internal:5432/railway`

**If `DATABASE_URL` is missing:**
1. Make sure your PostgreSQL service is linked to your backend service
2. In Railway, go to your backend service → "Settings" → "Service Connections"
3. Ensure PostgreSQL is connected

## Verification

After setting `USE_MOCKS=false` and redeploying, check the logs for:

✅ **Success indicators:**
- `🔍 [Alembic] Found DATABASE_URL: postgresql://***@postgres.railway.internal:5432/railway`
- `✅ [Alembic] Database URL configured for migrations`
- `✅ Database migrations completed` (no errors)
- `🔍 [Main] USE_MOCKS=False (from env: false)`
- `✅ Butterfly Engine initialized` (NOT "mock mode")
- `✅ Paradox Engine initialized` (NOT "mock mode")

❌ **If you see errors:**
- `connection to server at "localhost"` → `DATABASE_URL` not being read correctly
- `USE_MOCKS=True` → Variable not set or set incorrectly
- `✅ Butterfly Engine initialized (mock mode)` → `USE_MOCKS` is still `true`

## Troubleshooting

### Migrations failing with "localhost" error
- Check that `DATABASE_URL` is set in backend service variables
- Verify PostgreSQL service is connected to backend service
- Check logs for `🔍 [Alembic]` debug messages

### Still in mock mode
- Verify `USE_MOCKS=false` (lowercase, not `False` or `FALSE`)
- Check logs for `🔍 [Main] USE_MOCKS=` to see what value is being read
- Redeploy after setting the variable


