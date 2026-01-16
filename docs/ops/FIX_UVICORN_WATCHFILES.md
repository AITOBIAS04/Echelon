# Fix Uvicorn WatchFiles Constant Reloading

## Problem
Uvicorn's file watcher is monitoring `.venv.old` and causing constant reloads.

## Solution 1: Configure uvicorn to ignore .venv.old

Instead of deleting (which is hanging), tell uvicorn to ignore it:

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate

# Run with --reload-exclude to ignore .venv.old
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --reload-exclude "*.venv.old/**"
```

## Solution 2: Disable reload (if you don't need auto-reload)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
# (no --reload flag)
```

## Solution 3: Create .watchignore file

Create `backend/.watchignore`:
```
.venv.old
.venv.old/**
```

## Solution 4: Force delete later (when nothing is using it)

If deletion is hanging, try later when no processes are using it:

```bash
# Kill any processes that might be using it
pkill -f python
sleep 2

# Then try deleting
rm -rf .venv.old
```

Or use `sudo` (be careful):
```bash
sudo rm -rf .venv.old
```

## Recommended: Use --reload-exclude

The easiest fix is to just exclude it from watching:

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --reload-exclude ".venv.old"
```

This will stop the constant reloading without needing to delete the directory.

