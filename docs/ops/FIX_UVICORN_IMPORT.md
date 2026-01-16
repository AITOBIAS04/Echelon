# Fix Uvicorn "Could not import module 'main'" Error

## Problem
Uvicorn can't find the `main` module, causing constant reload errors.

## Solution: Run from the correct directory

### Option 1: Run from backend directory (Recommended)

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Run as module from project root

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo
source backend/.venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Also: Delete .venv.old to stop constant reloads

The `.venv.old` directory is causing uvicorn to constantly reload. Delete it:

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
rm -rf .venv.old
```

## Complete Fix Steps

```bash
# 1. Stop uvicorn (Ctrl+C)

# 2. Delete old venv
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
rm -rf .venv.old

# 3. Start uvicorn from backend directory
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Verify it's working

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Payments router included
✅ Situation Room router included
INFO:     Application startup complete.
```

No more "Could not import module 'main'" errors!

