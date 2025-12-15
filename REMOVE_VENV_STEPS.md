# Remove .venv - Step by Step

Since nothing is locking it, try these steps:

## Step 1: Make sure you're deactivated

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
deactivate 2>/dev/null || true
```

## Step 2: Try removing again

```bash
# Try standard remove
rm -rf .venv
```

## Step 3: If that fails, make files writable first

```bash
chmod -R u+w .venv
rm -rf .venv
```

## Step 4: If still fails, just rename it

```bash
# Rename instead of delete
mv .venv .venv.old

# Create new one
python3 -m venv .venv
```

## Step 5: Create fresh venv and install

```bash
# Create fresh venv
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install packages
python3 -m pip install --no-cache-dir --upgrade pip
python3 -m pip install --no-cache-dir "uvicorn[standard]" fastapi sqlalchemy pydantic
```

## Complete Command Sequence

```bash
cd /Users/tobyharber/Documents/prediction-market-monorepo/backend
deactivate 2>/dev/null || true
rm -rf .venv || mv .venv .venv.old
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --no-cache-dir --upgrade pip
python3 -m pip install --no-cache-dir "uvicorn[standard]" fastapi sqlalchemy pydantic
```

## If rm -rf still fails

Try this macOS-specific approach:

```bash
# Use find to delete files
find .venv -delete

# Then remove directory
rmdir .venv
```

Or just rename and move on:

```bash
mv .venv .venv.old
python3 -m venv .venv
```

The old .venv.old can be deleted later when macOS releases the lock.

