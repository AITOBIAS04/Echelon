# Setup Fresh Virtual Environment

## Step 1: Create New Virtual Environment

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
python3 -m venv .venv
```

## Step 2: Activate It

```bash
source .venv/bin/activate
```

You should see `(.venv)` in your prompt.

## Step 3: Upgrade Pip

```bash
python3 -m pip install --no-cache-dir --upgrade pip
```

## Step 4: Install Essential Packages

```bash
# Core web framework
python3 -m pip install --no-cache-dir "uvicorn[standard]" fastapi

# Database
python3 -m pip install --no-cache-dir sqlalchemy pydantic

# Authentication
python3 -m pip install --no-cache-dir python-jose passlib python-multipart

# HTTP client
python3 -m pip install --no-cache-dir aiohttp httpx

# Or install everything at once
python3 -m pip install --no-cache-dir -r requirements.txt
```

## Step 5: Verify Installation

```bash
# Check pip works
python3 -m pip list

# Test imports
python3 -c "import uvicorn; import fastapi; print('✅ All good!')"
```

## Step 6: Start the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Payments router included
✅ Situation Room router included
INFO:     Application startup complete.
```

## Quick All-in-One Command

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend && \
python3 -m venv .venv && \
source .venv/bin/activate && \
python3 -m pip install --no-cache-dir --upgrade pip && \
python3 -m pip install --no-cache-dir "uvicorn[standard]" fastapi sqlalchemy pydantic python-jose passlib python-multipart aiohttp
```

