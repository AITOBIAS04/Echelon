# How to Start the Backend

## Problem
If you see `ModuleNotFoundError: No module named 'uvicorn'`, you need to activate the virtual environment first.

## Solution

### Step 1: Navigate to backend directory
```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
```

### Step 2: Activate virtual environment
```bash
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### Step 3: Verify dependencies are installed
```bash
pip list | grep uvicorn
```

If uvicorn is not listed, install dependencies:
```bash
pip install -r requirements.txt
```

### Step 4: Start the backend server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**OR** if you want to run it as a module:
```bash
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Alternative: If virtual environment doesn't exist

### Create and setup virtual environment
```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# Create venv
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Quick Check Commands

### Check if venv is activated
```bash
which python3
# Should show: /Users/tobyharber/Documents/prediction-market-monorepo/backend/.venv/bin/python3
```

### Check if uvicorn is installed
```bash
pip show uvicorn
```

### Deactivate venv (when done)
```bash
deactivate
```

## Expected Output

When the server starts successfully, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
✅ Payments router included
✅ Situation Room router included
INFO:     Application startup complete.
```

## Troubleshooting

### If you still get "No module named 'uvicorn'":
1. Make sure you're in the backend directory
2. Make sure the venv is activated (you should see `(.venv)` in prompt)
3. Try: `pip install uvicorn[standard]`
4. Check: `python3 -c "import uvicorn; print('OK')"`

### If you get import errors:
- Make sure `backend/__init__.py` exists
- Make sure `backend/api/__init__.py` exists
- Check that all imports use `from backend.` prefix

