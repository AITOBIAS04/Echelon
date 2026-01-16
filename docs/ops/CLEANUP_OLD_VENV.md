# Cleanup Old Virtual Environment

## Problem
Uvicorn's file watcher is monitoring `.venv.old` and showing warnings.

## Solution: Delete the old venv

Since you have a working `.venv` now, you can safely delete `.venv.old`:

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
rm -rf .venv.old
```

## Or configure uvicorn to ignore it

If you want to keep it for now, you can tell uvicorn to ignore it by adding to your `.gitignore` or uvicorn config, but it's better to just delete it.

## After cleanup

Restart uvicorn and the warning should disappear:

```bash
# Stop uvicorn (Ctrl+C)
# Then restart
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

