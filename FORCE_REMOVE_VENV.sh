#!/bin/bash
# Force remove virtual environment

set -e

echo "🔧 Force removing virtual environment..."

cd /Users/tobyharber/Documents/prediction-market-monorepo/backend

# Make sure we're deactivated
deactivate 2>/dev/null || true

# Kill any Python processes that might be using the venv
pkill -f "python.*backend" 2>/dev/null || true
sleep 1

# Force remove with sudo if needed (but try without first)
echo "Removing .venv directory..."
rm -rf .venv 2>/dev/null || {
    echo "Standard rm failed, trying with chmod..."
    chmod -R u+w .venv 2>/dev/null || true
    rm -rf .venv 2>/dev/null || {
        echo "Still failed, trying find -delete..."
        find .venv -delete 2>/dev/null || {
            echo "⚠️ Could not remove .venv completely"
            echo "Try manually: sudo rm -rf .venv"
            exit 1
        }
    }
}

echo "✅ .venv removed successfully"

# Create fresh venv
echo "Creating fresh virtual environment..."
python3 -m venv .venv

echo "✅ Fresh venv created!"
echo "Activate with: source .venv/bin/activate"

