# Fix Python Version Issue

## Problem
You're using Python 3.14, but many packages require Python <3.13.

## Solution: Use Python 3.12

### Step 1: Check Available Python Versions

```bash
# See what Python versions you have
ls -la /usr/local/bin/python* 2>/dev/null
which python3.12
which python3.11
which python3.10

# Or check with pyenv if installed
pyenv versions
```

### Step 2: Create Venv with Python 3.12

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# Remove current venv
rm -rf .venv

# Create with Python 3.12 (or 3.11 if 3.12 not available)
python3.12 -m venv .venv

# OR if python3.12 doesn't exist, try:
python3.11 -m venv .venv

# OR use system Python 3.12 if available:
/usr/local/bin/python3.12 -m venv .venv
```

### Step 3: Activate and Install

```bash
source .venv/bin/activate

# Verify Python version
python3 --version  # Should show 3.12.x or 3.11.x

# Install packages
python3 -m pip install --no-cache-dir --upgrade pip
python3 -m pip install --no-cache-dir -r requirements.txt
```

## Alternative: Install Python 3.12 via Homebrew

If you don't have Python 3.12:

```bash
# Install Python 3.12
brew install python@3.12

# Create venv with it
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
rm -rf .venv
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install --no-cache-dir --upgrade pip
python3 -m pip install --no-cache-dir -r requirements.txt
```

## Quick Fix: Remove virtuals-acp

I've already commented out `virtuals-acp` in requirements.txt since it's not on PyPI. If you need it, install it separately:

```bash
# If virtuals-acp is a local package
pip install -e /path/to/virtuals-acp

# Or if it's in a git repo
pip install git+https://github.com/your-repo/virtuals-acp.git
```

## Verify After Fix

```bash
python3 --version  # Should be 3.12.x or 3.11.x
python3 -c "import pydantic; print('✅ Works!')"
```

