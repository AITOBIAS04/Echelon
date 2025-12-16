#!/bin/bash
# Efficient git secrets checker

echo "🔍 Checking git history for exposed secrets..."
echo ""

# Check for SECRET_KEY
echo "=== SECRET_KEY ==="
git log --all -S "SECRET_KEY" --pretty=format:"%h - %s (%ar)" --no-patch | head -5
echo ""

# Check for api_key
echo "=== api_key ==="
git log --all -S "api_key" --pretty=format:"%h - %s (%ar)" --no-patch | head -5
echo ""

# Check for password
echo "=== password ==="
git log --all -S "password" --pretty=format:"%h - %s (%ar)" --no-patch | head -5
echo ""

# Check for private_key
echo "=== private_key ==="
git log --all -S "private_key" --pretty=format:"%h - %s (%ar)" --no-patch | head -5
echo ""

echo "✅ Check complete. If commits found, review with: git show <commit-hash>"
