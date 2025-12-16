#!/bin/bash
# Fix iCloud Drive Syncing Issues
# This script excludes problematic files from iCloud Drive syncing

REPO_DIR="/Users/tobyharber/Library/Mobile Documents/com~apple~CloudDocs/Documents/prediction-market-monorepo"
cd "$REPO_DIR" || exit 1

echo "🔧 Fixing iCloud Drive sync issues..."
echo ""

# Database files - these cause thumbnail generation errors
echo "📦 Excluding database files from iCloud sync..."
find . -type f \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" \) -exec brctl evict {} \; 2>/dev/null
find . -type f \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" \) -exec touch {}.nosync \; 2>/dev/null

# Binary files that cause thumbnail errors - exclude from entire repo
echo "📦 Excluding binary files (.node, .dylib, .so) from iCloud sync..."
find . -type f \( -name "*.node" -o -name "*.dylib" -o -name "*.so" \) -exec brctl evict {} \; 2>/dev/null
find . -type f \( -name "*.node" -o -name "*.dylib" -o -name "*.so" \) -exec touch {}.nosync \; 2>/dev/null

# Large compressed files
echo "📦 Excluding compressed files (.pack.gz) from iCloud sync..."
find . -type f -name "*.pack.gz" -exec brctl evict {} \; 2>/dev/null
find . -type f -name "*.pack.gz" -exec touch {}.nosync \; 2>/dev/null

# Check if node_modules exists and exclude entire directories
if [ -d "node_modules" ] || [ -d "frontend/node_modules" ] || [ -d "smart-contracts/node_modules" ]; then
    echo "📦 Excluding node_modules directories (entire directories)..."
    find . -name "node_modules" -type d | while read dir; do
        brctl evict "$dir" 2>/dev/null
        touch "$dir/.nosync" 2>/dev/null
    done
fi

# Check if venv exists and exclude them
if [ -d "backend/venv" ] || [ -d "backend/.venv" ]; then
    echo "📦 Excluding Python virtual environments..."
    find . \( -name "venv" -o -name ".venv" \) -type d | while read dir; do
        touch "$dir/.nosync" 2>/dev/null
    done
fi

# Exclude __pycache__ directories
echo "📦 Excluding Python cache directories..."
find . -name "__pycache__" -type d -exec touch {}/.nosync \; 2>/dev/null

# Exclude .next build cache
if [ -d "frontend/.next" ]; then
    echo "📦 Excluding Next.js build cache..."
    touch frontend/.next/.nosync 2>/dev/null
fi

echo ""
echo "✅ Done! The problematic files have been excluded from iCloud Drive syncing."
echo ""
echo "📝 Excluded file types:"
echo "   - Database files (*.db, *.sqlite*)"
echo "   - Binary files (*.node, *.dylib, *.so)"
echo "   - Compressed cache files (*.pack.gz)"
echo "   - node_modules directories"
echo "   - Python virtual environments"
echo "   - Python cache directories"
echo ""
echo "💡 To verify, run: brctl log -t | grep -i error"
echo "💡 To check excluded files: brctl status <file>"


