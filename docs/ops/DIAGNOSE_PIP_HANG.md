# Diagnose Pip Hang Issue

## Step 1: Check Basic Connectivity

```bash
# Test if you can reach PyPI
curl -I https://pypi.org/simple/

# Test DNS resolution
nslookup pypi.org

# Check if pip can resolve packages (without installing)
pip index versions requests --no-cache-dir
```

## Step 2: Try Installing One Package at a Time

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate

# Try installing just uvicorn first
pip install --no-cache-dir uvicorn[standard]

# If that works, try fastapi
pip install --no-cache-dir fastapi

# If that works, continue with others
```

## Step 3: Use Alternative Package Index

```bash
# Try using a different mirror
pip install --no-cache-dir --index-url https://pypi.org/simple/ uvicorn

# Or use a faster mirror (if in certain regions)
pip install --no-cache-dir --index-url https://pypi.python.org/simple/ uvicorn
```

## Step 4: Check System Issues

```bash
# Check disk space
df -h

# Check Python version
python3 --version
which python3

# Check if pip is actually working
python3 -m pip --version

# Try using python3 -m pip instead of just pip
python3 -m pip install --no-cache-dir uvicorn
```

## Step 5: Minimal Installation

```bash
# Install only essential packages first
python3 -m pip install --no-cache-dir --upgrade pip
python3 -m pip install --no-cache-dir uvicorn[standard] fastapi

# Then test if server starts
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Step 6: Check for Proxy/Firewall Issues

```bash
# Check if you're behind a proxy
echo $HTTP_PROXY
echo $HTTPS_PROXY

# If you have proxy settings, pip might need them
# Unset if not needed:
unset HTTP_PROXY
unset HTTPS_PROXY
```

## Step 7: Use Timeout to See Where It Hangs

```bash
# Install with timeout to see where it hangs
timeout 30 python3 -m pip install --no-cache-dir uvicorn || echo "Timed out after 30 seconds"
```

## Step 8: Check Pip Logs

```bash
# Enable verbose logging to see where it hangs
python3 -m pip install --no-cache-dir -v uvicorn 2>&1 | tee pip_log.txt
```

## Alternative: Use System Python (Temporary)

If venv keeps hanging, you could temporarily use system Python (not recommended for production):

```bash
# Install to user directory instead
pip3 install --user uvicorn fastapi

# Then run with system Python (not recommended)
python3 main.py
```

## Most Likely Causes

1. **Network timeout** - PyPI is slow or unreachable
2. **DNS issues** - Can't resolve pypi.org
3. **Proxy settings** - Corporate proxy blocking
4. **Disk I/O** - Slow disk or full disk
5. **Python installation** - Corrupted Python/pip

## Quick Test

Run this to see where it hangs:

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate

# Test 1: Can pip even run?
python3 -m pip --version

# Test 2: Can it list packages?
python3 -m pip list

# Test 3: Try installing smallest package
python3 -m pip install --no-cache-dir --timeout 10 setuptools
```

If even `pip --version` hangs, the issue is with Python/pip itself, not the network.

