# Delete Stubborn .venv.old Directory

## Why It Hangs
macOS can lock directories when:
- Finder has the folder open
- Time Machine is backing it up
- Spotlight is indexing it
- File system is slow/large

## Solution 1: Use Finder (Easiest)

1. Open Finder
2. Navigate to `backend/` folder
3. Find `.venv.old` folder
4. Right-click → Move to Trash
5. Empty Trash

## Solution 2: Force Delete with sudo

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
sudo rm -rf .venv.old
```

## Solution 3: Disable Spotlight Indexing Temporarily

```bash
# Disable Spotlight for the directory
sudo mdutil -i off /Users/tobyharber/Documents/prediction-market-monorepo/backend/.venv.old

# Then delete
rm -rf .venv.old

# Re-enable Spotlight
sudo mdutil -i on /
```

## Solution 4: Use find -delete (More Reliable)

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
find .venv.old -delete
rmdir .venv.old 2>/dev/null || true
```

## Solution 5: Just Leave It (Recommended)

Since `--reload-exclude` works, you can just leave `.venv.old` there. It's not hurting anything now that uvicorn ignores it.

## Solution 6: Rename and Delete Later

```bash
# Rename it to something uvicorn definitely won't watch
mv .venv.old .OLD_VENV_DELETE_ME

# Delete later when you have time
# Or just leave it - it's not causing issues anymore
```

## Recommended: Just Use --reload-exclude

Since the exclude flag works perfectly, you don't actually need to delete it. Just use:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --reload-exclude ".venv.old"
```

And leave `.venv.old` there. You can delete it later when you have time, or just ignore it.

