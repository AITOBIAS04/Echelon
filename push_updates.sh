#!/bin/bash
# Push all updates to GitHub

echo "🚀 Pushing all updates to GitHub..."
echo ""

# Check git status
echo "📊 Current status:"
git status --short
echo ""

# Stage all changes
echo "📦 Staging all changes..."
git add -A

# Show what will be committed
echo ""
echo "📝 Changes to be committed:"
git status --short
echo ""

# Commit with descriptive message
echo "💾 Committing changes..."
git commit -m "Add frontend panels, fix database config, update entrypoint

- Added ParadoxPanel and FieldKitPanel components
- Updated App.tsx with sidebar navigation
- Fixed entrypoint.py to handle directory detection
- Updated database config to handle Railway DATABASE_URL format
- Fixed seed script datetime deprecation warnings
- Commented out virtuals-acp (requires Python <3.13)
- Added database seed documentation
- Created helper scripts (run_seed.sh, update_env.sh)"

# Push to GitHub
echo ""
echo "⬆️  Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Successfully pushed to GitHub!"

