# Force Remove Virtual Environment

## Problem
`rm -rf .venv` fails with "Directory not empty" - files are locked or in use.

## Solution

### Step 1: Make sure venv is deactivated and no Python processes are running

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# Deactivate
deactivate 2>/dev/null || true

# Kill any Python processes using the venv
pkill -f "python.*backend" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

# Wait a moment
sleep 2
```

### Step 2: Force remove with chmod first

```bash
# Make files writable
chmod -R u+w .venv 2>/dev/null || true

# Now try removing
rm -rf .venv
```

### Step 3: If still fails, use find -delete

```bash
# Remove files one by one
find .venv -delete 2>/dev/null || true

# Then remove directory
rmdir .venv 2>/dev/null || true
```

### Step 4: Nuclear option (if nothing else works)

```bash
# Use sudo (be careful!)
sudo rm -rf .venv

# Or use find with sudo
sudo find .venv -delete
```

### Step 5: Alternative - Rename and create new

If you can't delete it, just rename it and create a new one:

```bash
# Rename old venv
mv .venv .venv.old

# Create new one
python3 -m venv .venv

# You can delete .venv.old later when nothing is using it
```

## Complete Solution (Recommended)

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# 1. Deactivate
deactivate 2>/dev/null || true

# 2. Kill Python processes
pkill -f python 2>/dev/null || true
sleep 2

# 3. Make writable and remove
chmod -R u+w .venv 2>/dev/null || true
rm -rf .venv

# 4. If still fails, rename it
mv .venv .venv.old 2>/dev/null || true

# 5. Create fresh
python3 -m venv .venv
source .venv/bin/activate

# 6. Install packages
python3 -m pip install --no-cache-dir --upgrade pip
python3 -m pip install --no-cache-dir uvicorn[standard] fastapi
```

## Why This Happens

1. **Files locked by running processes** - Python/uvicorn still using venv
2. **Permission issues** - Files not writable
3. **File system issues** - macOS sometimes locks directories

## Quick Fix (Easiest)

Just rename it and create a new one:

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
deactivate 2>/dev/null || true
mv .venv .venv.old
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --no-cache-dir --upgrade pip
python3 -m pip install --no-cache-dir uvicorn[standard] fastapi
```

This way you don't have to fight with file locks - just create a new venv and delete the old one later.

