# Vercel Root Directory Fix

## Problem
Vercel is trying to build from `/opt/buildhome/repo/frontend-vite` but that directory no longer exists. We've unified the frontend and moved everything to `frontend`.

## Solution

**Update the Root Directory in Vercel Dashboard:**

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project: `prediction-market-monorepo`
3. Go to **Settings** → **General**
4. Scroll down to **Root Directory**
5. Change from `frontend-vite` to `frontend`
6. Click **Save**
7. Go to **Deployments** tab
8. Click **Redeploy** on the latest deployment (or push a new commit)

## Alternative: Create New Project

If you can't find the setting or prefer a fresh start:

1. Create a new project in Vercel
2. Import the same GitHub repository
3. Set **Root Directory** to `frontend` during setup
4. Copy environment variables from the old project
5. Delete the old project (optional)

## Verify

After updating, the build should succeed and you should see:
- ✅ Build completes successfully
- ✅ No "Cannot find cwd" errors
- ✅ Frontend deploys correctly
