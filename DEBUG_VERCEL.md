# Debugging Vercel Deployment - No Data Showing

## Issue
Frontend loads but shows "0 events 0 timelines active" - API calls are failing.

## Quick Debug Steps

### 1. Check Browser Console
Open your Vercel site → Press F12 → Console tab
Look for:
- ❌ API Error messages
- 🔍 API URL logged
- 🌐 Network errors

### 2. Verify Environment Variables in Vercel
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Check:
   - `VITE_API_URL` is set to your Railway backend URL
   - Should be: `https://your-backend-production.up.railway.app`
   - NOT: `http://localhost:8000`

### 3. Test Railway Backend Directly
Open in browser:
```
https://your-railway-backend.railway.app/api/v1/butterfly/timelines/health?limit=8
```

Should return JSON with timelines. If you get:
- **404**: Backend routes not registered
- **503**: Backend not running or USE_MOCKS issue
- **CORS error**: CORS not configured
- **Connection refused**: Backend URL wrong

### 4. Check Railway Backend Logs
1. Go to Railway → Backend service → Deployments → Latest
2. Check logs for:
   - ✅ "Database migrations completed"
   - ✅ "Butterfly Engine initialized" (NOT "mock mode")
   - ✅ "Uvicorn running on http://0.0.0.0:8080"
   - ❌ Any error messages

### 5. Verify CORS
Check `backend/main.py` - should allow Vercel domains:
```python
origins = [
    "http://localhost:5173",
    # Should allow *.vercel.app or your specific Vercel URL
]
```

### 6. Test API Endpoints
Run these in your browser (replace with your Railway URL):
```
https://your-backend.railway.app/api/v1/butterfly/timelines/health?limit=8
https://your-backend.railway.app/api/v1/butterfly/wing-flaps?limit=20
https://your-backend.railway.app/api/v1/paradox/active
```

## Common Issues

### Issue: "Network Error" or "Failed to fetch"
**Cause**: CORS not configured or backend URL wrong
**Fix**: 
1. Check `VITE_API_URL` in Vercel
2. Update CORS in `backend/main.py`
3. Redeploy backend

### Issue: "404 Not Found"
**Cause**: API routes not registered
**Fix**: Check Railway logs - should see "✅ Butterfly Engine router included"

### Issue: "503 Service Unavailable"
**Cause**: `USE_MOCKS=false` but engines not initialized
**Fix**: Check Railway logs - should NOT see "mock mode"

### Issue: Empty data but no errors
**Cause**: Backend returning empty arrays
**Fix**: Run seed script: `./seed_railway.sh`

## Quick Fix Commands

**Check what API URL frontend is using:**
```javascript
// In browser console on Vercel site:
console.log('API URL:', import.meta.env.VITE_API_URL);
```

**Test backend directly:**
```bash
curl https://your-backend.railway.app/api/v1/butterfly/timelines/health?limit=8
```

**Check Railway backend health:**
```bash
curl https://your-backend.railway.app/health
```


