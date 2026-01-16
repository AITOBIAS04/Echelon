# Quick Fix for slowapi Error

## The Problem
You're getting `ModuleNotFoundError: No module named 'slowapi'` because the Python environment you're using doesn't have `slowapi` installed.

## Solution

**Run this in your terminal (the one showing the error):**

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo
./fix_slowapi.sh
```

Or manually:

```bash
# Install slowapi in your active Python environment
python -m pip install slowapi starlette eth-utils

# Verify it works
PYTHONPATH=/Users/tobyharber/Documents/prediction-market-monorepo python -c "from backend.core.security import Limiter; print('✅ Success!')"

# Then run the backend
PYTHONPATH=/Users/tobyharber/Documents/prediction-market-monorepo python -m backend.main
```

## Why This Happens

The `((.venv) )` prompt suggests you have a virtual environment activated, but `slowapi` might not be installed in that specific environment. The fix script will install it in whatever Python you're currently using.
