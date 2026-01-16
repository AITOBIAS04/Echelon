# Run Uvicorn Correctly

## Problem
When running `uvicorn main:app` from `backend/` directory, Python can't find the `backend` module.

## Solution: Run from Project Root

### Option 1: Run as module from project root (Recommended)

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo
source backend/.venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Set PYTHONPATH and run from backend

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate
export PYTHONPATH=/Users/tobyharber/Documents/prediction-market-monorepo:$PYTHONPATH
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Use python -m uvicorn from project root

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo
source backend/.venv/bin/activate
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Why This Happens

When you run `uvicorn main:app` from `backend/`, Python looks for `main.py` in the current directory, but the imports in `main.py` use `from backend.core.xxx`, which requires the project root to be in Python's path.

## Recommended Command

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo
source backend/.venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

This runs from the project root, so `backend` is a proper module.

