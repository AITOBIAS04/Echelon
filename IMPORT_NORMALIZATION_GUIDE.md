# Import Normalization Guide

## Problem
The try/except blocks were masking import errors. When `from backend.core.xxx` failed (because `backend/__init__.py` was missing), it silently fell back to `from core.xxx`, which doesn't work when running from the project root.

## Solution
1. ✅ Created `backend/__init__.py` - Makes `backend` a proper Python package
2. ✅ Created `backend/api/__init__.py` - Makes `backend.api` a proper package
3. ✅ Fixed critical files manually:
   - `backend/main.py` - Removed try/except, using absolute imports
   - `backend/simulation/scheduler.py` - Removed try/except, using absolute imports
4. ⚠️ Created `backend/normalize_imports.py` - Script to fix remaining files

## Manual Steps

### Step 1: Run the normalization script
```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo
python3 backend/normalize_imports.py
```

This will:
- Convert all `from core.` → `from backend.core.`
- Convert all `from agents.` → `from backend.agents.`
- Convert all `from simulation.` → `from backend.simulation.`
- Convert all `from payments.` → `from backend.payments.`
- Convert all `from api.` → `from backend.api.`
- Create any missing `__init__.py` files

### Step 2: Verify the fixes
```bash
# Check that __init__.py files exist
ls -la backend/__init__.py
ls -la backend/api/__init__.py

# Test imports
cd /Users/tobyharber/Documents/prediction-market-monorepo
python3 -c "from backend.core.osint_registry import get_osint_registry; print('✅ Import works!')"
```

### Step 3: Test the application
```bash
cd backend
source .venv/bin/activate
python3 -m backend.main  # Should work now
```

## Files Already Fixed
- ✅ `backend/main.py` - Removed try/except blocks, using absolute imports
- ✅ `backend/simulation/scheduler.py` - Removed try/except blocks, using absolute imports

## Files That Need Fixing (Run the script)
The following files still have relative imports that need to be normalized:
- `backend/core/osint_registry.py`
- `backend/core/situation_room_engine.py`
- `backend/agents/autonomous_agent.py`
- `backend/simulation/evolution_engine.py`
- `backend/simulation/sim_football_engine.py`
- `backend/simulation/sim_market_engine.py`
- And others...

## Why This Matters
- **Before**: `from core.xxx` only works when running from `backend/` directory
- **After**: `from backend.core.xxx` works from anywhere (project root, backend/, etc.)
- **Result**: No more `ModuleNotFoundError: No module named 'core'` errors

## Notes
- The script uses regex to find and replace import statements
- It won't double-prefix (won't create `backend.backend.core`)
- It preserves all other code exactly as-is
- It creates missing `__init__.py` files automatically

