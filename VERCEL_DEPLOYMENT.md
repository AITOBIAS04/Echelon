# Vercel Deployment Guide

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional): `npm i -g vercel`
3. **GitHub Repository**: Your code should be pushed to GitHub

## Deployment Steps

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "Add New Project"

2. **Import Your Repository**
   - Select your GitHub repository
   - Choose the repository: `prediction-market-monorepo`

3. **Configure Project**
   - **Root Directory**: Set to `frontend-vite`
   - **Framework Preset**: Select `Vite` (or it should auto-detect)
   - **Build Command**: `npm run build` (should auto-fill)
   - **Output Directory**: `dist` (should auto-fill)
   - **Install Command**: `npm install` (should auto-fill)

4. **Set Environment Variables**
   Click "Environment Variables" and add:
   - `VITE_API_URL` = `https://your-railway-backend.railway.app`
     - Get this from Railway → Your backend service → Settings → Domains
   - `VITE_WS_BASE_URL` = `wss://your-railway-backend.railway.app`
     - Same as above, but with `wss://` instead of `https://`

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be live at `https://your-project.vercel.app`

### Option 2: Deploy via Vercel CLI

```bash
cd frontend-vite
npm install -g vercel
vercel login
vercel
```

Follow the prompts:
- Set root directory to `frontend-vite`
- Framework: Vite
- Add environment variables when prompted

## Environment Variables

**Required:**
- `VITE_API_URL` - Your Railway backend URL (e.g., `https://your-backend.railway.app`)
- `VITE_WS_BASE_URL` - WebSocket URL (e.g., `wss://your-backend.railway.app`)

**To get your Railway backend URL:**
1. Go to Railway → Your backend service
2. Click "Settings" → "Networking"
3. Generate a domain (if not already done)
4. Copy the public URL (e.g., `https://your-backend-production.up.railway.app`)

## Troubleshooting

### Build Fails
- Check that all dependencies are in `package.json`
- Ensure TypeScript compiles: `npm run build` locally first
- Check Vercel build logs for errors

### API Calls Fail (CORS)
- Make sure your Railway backend has CORS configured
- Check `backend/main.py` has your Vercel domain in `origins`
- Verify `VITE_API_URL` is set correctly in Vercel

### Blank Page
- Check browser console for errors
- Verify `VITE_API_URL` is set correctly
- Check that Railway backend is running and accessible

### 404 Errors
- Ensure `vercel.json` has the rewrite rule for SPA routing
- Check that `outputDirectory` is set to `dist`

## Verify Deployment

After deployment, check:
1. ✅ Frontend loads at Vercel URL
2. ✅ API calls work (check Network tab in browser)
3. ✅ Data loads from Railway backend
4. ✅ No CORS errors in console

## Updating Deployment

After pushing to GitHub:
- Vercel automatically redeploys (if connected to GitHub)
- Or run `vercel --prod` from CLI

