# Deployment Checklist

## ✅ Backend (Railway) - COMPLETE
- [x] Backend deployed to Railway
- [x] PostgreSQL database connected
- [x] Migrations completed
- [x] Database seeded
- [x] `USE_MOCKS=false` set
- [x] `DATABASE_URL` configured
- [x] Backend accessible at Railway URL

## 🔄 Frontend (Vercel) - TODO

### Step 1: Get Your Railway Backend URL
1. Go to Railway → Your backend service
2. Click "Settings" → "Networking"
3. If no domain exists, click "Generate Domain"
4. Copy the public URL (e.g., `https://your-backend-production.up.railway.app`)

### Step 2: Deploy to Vercel

**Via Dashboard:**
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import your GitHub repository
4. **IMPORTANT**: Set **Root Directory** to `frontend-vite`
5. Framework: `Vite` (should auto-detect)
6. Build Command: `npm run build`
7. Output Directory: `dist`

**Environment Variables:**
- `VITE_API_URL` = `https://your-railway-backend.railway.app` (from Step 1)
- `VITE_WS_BASE_URL` = `wss://your-railway-backend.railway.app` (same URL, but `wss://`)

### Step 3: Update Backend CORS
After you get your Vercel URL, update `backend/main.py` CORS origins to include:
```python
origins = [
    "http://localhost:5173",
    "https://your-project.vercel.app",  # Add your Vercel URL here
]
```

Or push the updated code I just created (allows all Vercel domains).

### Step 4: Verify
1. Visit your Vercel deployment URL
2. Open browser console (F12)
3. Check for:
   - ✅ No CORS errors
   - ✅ API calls succeeding
   - ✅ Data loading from Railway backend

## Quick Commands

**Get Railway Backend URL:**
```bash
# Check Railway dashboard → Backend service → Settings → Networking
```

**Deploy Frontend to Vercel:**
```bash
cd frontend-vite
vercel login
vercel
```

**Update CORS after getting Vercel URL:**
```bash
# Edit backend/main.py and add your Vercel URL to origins
# Then push to GitHub (Railway auto-deploys)
```


