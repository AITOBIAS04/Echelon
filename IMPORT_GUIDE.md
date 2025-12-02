# How to Import Updated Files

After the migration from "war-room" to "situation-room", here's how to ensure your Python imports work correctly.

## Quick Fix: Restart Your Python Process

**The simplest solution:** If you have a running Python process (like `python3 -m backend.main` or a scheduler), **restart it** to pick up the new imports.

```bash
# Stop your current process (Ctrl+C)
# Then restart:
python3 -m backend.main
```

## Import Structure

The updated imports follow this pattern:

### ✅ Correct Imports

```python
# In backend/core/osint_registry.py
from backend.core.osint_sources_situation_room import get_situation_room_sources

# In backend/simulation/situation-room/scheduler.py
from backend.simulation.situation_room_engine import SituationRoomEngine
from backend.core.mission_generator import OSINTSignal
from backend.core.osint_registry import get_osint_registry
```

### ❌ Old Imports (Don't Use)

```python
# OLD - These won't work anymore:
from backend.core.osint_sources_warroom import get_war_room_sources  # ❌
```

## If You Need to Clear Python's Import Cache

If you're in a Python REPL or have modules already imported, you may need to clear the cache:

```python
# In Python REPL or interactive session:
import sys
import importlib

# Clear specific modules
if 'backend.core.osint_sources_warroom' in sys.modules:
    del sys.modules['backend.core.osint_sources_warroom']

if 'backend.core.osint_sources_situation_room' in sys.modules:
    importlib.reload(sys.modules['backend.core.osint_sources_situation_room'])

# Or reload the registry
if 'backend.core.osint_registry' in sys.modules:
    importlib.reload(sys.modules['backend.core.osint_registry'])
```

## Testing Imports

Test that everything imports correctly:

```bash
# From project root:
cd /Users/tobyharber/Documents/prediction-market-monorepo

# Test OSINT sources
python3 -c "from backend.core.osint_sources_situation_room import get_situation_room_sources; print('✅ Import successful')"

# Test OSINT registry
python3 -c "from backend.core.osint_registry import get_osint_registry; registry = get_osint_registry(); print('✅ Registry loaded')"

# Test Situation Room engine
python3 -c "from backend.simulation.situation_room_engine import SituationRoomEngine; print('✅ Engine imported')"
```

## Common Issues & Solutions

### Issue 1: `ModuleNotFoundError: No module named 'backend.core.osint_sources_warroom'`

**Solution:** The old file was deleted. Make sure you're using:
```python
from backend.core.osint_sources_situation_room import get_situation_room_sources
```

### Issue 2: Import works but old code is still running

**Solution:** Restart your Python process. Python caches imported modules in memory.

### Issue 3: Circular import errors

**Solution:** The imports are structured to handle this with try/except fallbacks. If you see issues, check that all files are in the correct locations:
- `backend/core/osint_sources_situation_room.py` ✅
- `backend/simulation/situation_room_engine.py` ✅
- `backend/simulation/situation-room/scheduler.py` ✅

## File Locations

All updated files are in these locations:

```
backend/
├── core/
│   ├── osint_sources_situation_room.py  ← NEW (replaces warroom)
│   └── osint_registry.py                 ← UPDATED (imports changed)
└── simulation/
    ├── situation_room_engine.py          ← NEW
    └── situation-room/
        └── scheduler.py                   ← NEW
```

## Backward Compatibility

The new `osint_sources_situation_room.py` includes a backward-compatible alias:

```python
# Both work:
from backend.core.osint_sources_situation_room import get_situation_room_sources  # ✅ New
from backend.core.osint_sources_situation_room import get_war_room_sources      # ✅ Alias (for compatibility)
```

However, **prefer using `get_situation_room_sources()`** going forward.

