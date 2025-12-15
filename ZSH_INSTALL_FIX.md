# Fix: zsh "no matches found" Error

## Problem
zsh interprets square brackets `[]` as glob patterns, so `uvicorn[standard]` fails.

## Solution: Quote the Package Name

### Option 1: Use Quotes
```bash
python3 -m pip install --no-cache-dir "uvicorn[standard]" fastapi sqlalchemy pydantic
```

### Option 2: Escape the Brackets
```bash
python3 -m pip install --no-cache-dir uvicorn\[standard\] fastapi sqlalchemy pydantic
```

### Option 3: Use Single Quotes
```bash
python3 -m pip install --no-cache-dir 'uvicorn[standard]' fastapi sqlalchemy pydantic
```

## Complete Installation Command

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate

# Upgrade pip first
python3 -m pip install --no-cache-dir --upgrade pip

# Install packages (with quotes!)
python3 -m pip install --no-cache-dir "uvicorn[standard]" fastapi sqlalchemy pydantic

# Install more packages as needed
python3 -m pip install --no-cache-dir python-jose passlib python-multipart aiohttp
```

## Why This Happens

zsh treats `[standard]` as a glob pattern (character class) and tries to match files. Since no files match, it errors.

## Alternative: Disable Glob for One Command

```bash
# Disable glob expansion temporarily
setopt noglob
python3 -m pip install --no-cache-dir uvicorn[standard] fastapi
setopt glob
```

But quoting is simpler and safer.

## Recommended Command

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
source .venv/bin/activate
python3 -m pip install --no-cache-dir "uvicorn[standard]" fastapi sqlalchemy pydantic python-jose passlib python-multipart aiohttp
```

