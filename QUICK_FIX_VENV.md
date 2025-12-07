# Quick Fix: Corrupted Virtual Environment

## Problem
Pip commands are hanging or very slow, indicating a corrupted virtual environment.

## Solution: Recreate Virtual Environment

### Option 1: Automated Script
```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
chmod +x FIX_CORRUPTED_VENV.sh
./FIX_CORRUPTED_VENV.sh
```

### Option 2: Manual Steps

```bash
# 1. Navigate to backend
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# 2. Deactivate current venv (if active)
deactivate 2>/dev/null || true

# 3. Remove corrupted venv
rm -rf .venv

# 4. Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# 5. Clean pip cache
rm -rf ~/.cache/pip

# 6. Create fresh venv
python3 -m venv .venv

# 7. Activate it
source .venv/bin/activate

# 8. Upgrade pip (use --no-cache-dir to avoid cache issues)
python3 -m pip install --upgrade pip setuptools wheel --no-cache-dir

# 9. Install dependencies (use --no-cache-dir)
pip install --no-cache-dir -r requirements.txt

# 10. Verify
python3 -c "import uvicorn; print('✅ Works!')"
```

## Why This Happens

1. **Corrupted pip cache** - Can cause pip to hang
2. **Broken virtual environment** - Files can become corrupted
3. **Network issues** - Slow downloads can make pip appear hung
4. **Disk space issues** - Full disk can cause hangs

## Prevention

- Use `--no-cache-dir` flag if pip is slow
- Regularly clean pip cache: `pip cache purge`
- Don't interrupt pip installations (Ctrl+C can corrupt venv)

## After Fixing

Start the server:
```bash
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

