#!/bin/bash
# Push all updates to GitHub

set -e  # Exit on error

echo "🚀 Pushing all updates to GitHub..."
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"
echo ""

# Show status
echo "📊 Current git status:"
git status --short
echo ""

# Stage all changes
echo "📦 Staging all changes..."
git add -A
echo "✅ All changes staged"
echo ""

# Show what will be committed
echo "📝 Changes to be committed:"
git status --short
echo ""

# Commit with a descriptive message
COMMIT_MSG="Update: Install virtuals-acp, fix imports, update requirements

- Installed virtuals-acp==0.3.14 from PyPI
- Reverted all optional imports to required imports
- Updated backend/requirements.txt
- Fixed import paths and module resolution
- All components (main, scheduler, frontend) running successfully"

echo "💾 Committing changes..."
git commit -m "$COMMIT_MSG"
echo "✅ Changes committed"
echo ""

# Push to remote
echo "⬆️  Pushing to GitHub (origin/$CURRENT_BRANCH)..."
git push origin "$CURRENT_BRANCH"
echo ""
echo "✅ Successfully pushed to GitHub!"
echo "🔗 Repository: https://github.com/AITOBIAS04/prediction-market-monorepo"

