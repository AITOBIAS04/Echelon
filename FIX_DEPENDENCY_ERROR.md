# Fix Dependency Error: propcache/yarl/aiohttp

## Problem
The error `from . import backend.api` is syntactically invalid, indicating a corrupted Python package installation (likely `propcache`, `yarl`, or `aiohttp`).

## Solution: Clean Reinstall

### Step 1: Remove corrupted packages and cache
```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# Deactivate virtual environment if active
deactivate 2>/dev/null || true

# Remove virtual environment
rm -rf .venv

# Remove Python cache files
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Remove problematic package cache
rm -rf ~/.cache/pip 2>/dev/null || true
```

### Step 2: Recreate virtual environment
```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Upgrade pip and install dependencies
```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install dependencies one by one to catch any errors
pip install fastapi==0.121.3
pip install uvicorn[standard]==0.38.0
pip install aiohttp==3.13.2

# If aiohttp fails, try installing its dependencies first
pip install yarl
pip install multidict
pip install async-timeout
pip install aiohttp==3.13.2

# Then install the rest
pip install -r requirements.txt
```

### Step 4: Verify installation
```bash
python3 -c "import aiohttp; print('✅ aiohttp works!')"
python3 -c "import yarl; print('✅ yarl works!')"
python3 -c "from backend.core.osint_registry import get_osint_registry; print('✅ Imports work!')"
```

## Alternative: Pin Specific Versions

If the issue persists, try pinning specific versions of the problematic packages:

```bash
pip install yarl==1.9.4
pip install multidict==6.0.5
pip install aiohttp==3.13.2
```

## Why This Happens

1. **Corrupted cache**: Python bytecode cache (`.pyc` files) can become corrupted
2. **Broken package**: `propcache` is a C extension that can fail to compile/install correctly
3. **Version conflicts**: Different packages requiring different versions of dependencies
4. **Virtual environment issues**: Corrupted venv can cause import errors

## Prevention

- Always use virtual environments
- Pin dependency versions in `requirements.txt`
- Clear cache when switching Python versions
- Use `pip install --no-cache-dir` if cache corruption is suspected

