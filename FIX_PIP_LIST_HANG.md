# Fix: pip list Hangs

## Problem
- `pip --version` works ✅
- `pip list` hangs ❌

This indicates corrupted package metadata in site-packages.

## Quick Fix

### Option 1: Clean Package Metadata

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate

# Find site-packages location
python3 -c "import site; print(site.getsitepackages()[0])"

# Remove corrupted metadata (replace with actual path from above)
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")

# Clean .pth files
find "$SITE_PACKAGES" -name "*.pth" -type f -delete 2>/dev/null || true

# Clean .dist-info directories
find "$SITE_PACKAGES" -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Clean .egg-info directories  
find "$SITE_PACKAGES" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Test again
python3 -m pip list
```

### Option 2: Recreate Venv (Recommended)

Since pip works but list hangs, the venv has corrupted packages. Recreate it:

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# Deactivate and remove
deactivate 2>/dev/null || true
rm -rf .venv

# Create fresh
python3 -m venv .venv
source .venv/bin/activate

# Now pip should work
python3 -m pip --version
python3 -m pip list  # Should work now

# Install packages
python3 -m pip install --no-cache-dir --upgrade pip
python3 -m pip install --no-cache-dir uvicorn[standard] fastapi
```

### Option 3: Use pip with --no-deps (if installing specific packages)

If you know what you need, install directly:

```bash
source .venv/bin/activate

# Install without checking existing packages
python3 -m pip install --no-cache-dir --force-reinstall --no-deps uvicorn
python3 -m pip install --no-cache-dir --force-reinstall --no-deps fastapi
```

## Why This Happens

1. **Corrupted .dist-info** - Package metadata files are corrupted
2. **Corrupted .pth files** - Path configuration files are broken
3. **Disk I/O issues** - Can't read package directories
4. **Permission issues** - Can't access package files

## Test After Fix

```bash
# Should work now
python3 -m pip list

# Should show version
python3 -m pip show uvicorn
```

## If Still Hanging

If `pip list` still hangs after cleaning, the issue is deeper:

```bash
# Check disk space
df -h

# Check permissions
ls -la .venv/lib/python*/site-packages/

# Try with verbose output to see where it hangs
python3 -m pip list -v 2>&1 | head -20
```

## Recommended: Fresh Start

Since pip works but list hangs, the safest approach is a fresh venv:

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
deactivate 2>/dev/null || true
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --no-cache-dir --upgrade pip
python3 -m pip install --no-cache-dir uvicorn[standard] fastapi sqlalchemy pydantic
```

Then test:
```bash
python3 -m pip list  # Should work now
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

