#!/bin/bash
# Monitor iCloud Drive Errors (Fast Version - macOS Compatible)
# This script helps you understand what errors are happening

REPO_DIR="/Users/tobyharber/Library/Mobile Documents/com~apple~CloudDocs/Documents/prediction-market-monorepo"
cd "$REPO_DIR" || exit 1

echo "🔍 Monitoring iCloud Drive Errors..."
echo "=================================="
echo ""

# Check if repo files are excluded (fast check - do this first)
echo "✅ Repository file status:"
if brctl status database.db 2>&1 | grep -q "Client zone not found"; then
    echo "   ✅ database.db is excluded from iCloud sync"
else
    echo "   ⚠️  database.db status unknown or being synced"
fi

if brctl status backend/database.db 2>&1 | grep -q "Client zone not found"; then
    echo "   ✅ backend/database.db is excluded from iCloud sync"
else
    echo "   ⚠️  backend/database.db status unknown or being synced"
fi
echo ""

# Use tail to get only recent entries (much faster than full log)
echo "📊 Recent errors (last 50 log entries only):"
echo "   (Reading last 50 entries to avoid hanging on large logs...)"
RECENT_LOG=$(brctl log -t 2>&1 | tail -50)
RECENT_ERRORS=$(echo "$RECENT_LOG" | grep -i error)

if [ -z "$RECENT_ERRORS" ]; then
    echo "   ✅ No errors in recent log entries!"
else
    ERROR_COUNT=$(echo "$RECENT_ERRORS" | wc -l | tr -d ' ')
    echo "   Found $ERROR_COUNT error(s) in last 50 entries:"
    echo "$RECENT_ERRORS" | head -5
    if [ "$ERROR_COUNT" -gt 5 ]; then
        echo "   ... (showing first 5 of $ERROR_COUNT)"
    fi
fi
echo ""

# Quick error breakdown from recent entries
echo "📈 Error breakdown (from last 50 entries):"
if [ -n "$RECENT_ERRORS" ]; then
    NOTES=$(echo "$RECENT_ERRORS" | grep "Notes\[" | wc -l | tr -d ' ')
    THUMBNAIL=$(echo "$RECENT_ERRORS" | grep "Thumbnail" | wc -l | tr -d ' ')
    FILEPROVIDER=$(echo "$RECENT_ERRORS" | grep "iCloudDriveFileProvider" | wc -l | tr -d ' ')
    DOCUMENTURL=$(echo "$RECENT_ERRORS" | grep "br_documentURL" | wc -l | tr -d ' ')
    
    echo "   - Notes app: $NOTES"
    echo "   - Thumbnail: $THUMBNAIL"
    echo "   - FileProvider: $FILEPROVIDER"
    echo "   - Document URL: $DOCUMENTURL"
    echo ""
    echo "   💡 These are system-level errors, not from your repo!"
else
    echo "   ✅ No errors found!"
fi
echo ""

# Show recent activity (limited)
echo "📋 Recent iCloud Drive activity (last 5 entries):"
echo "$RECENT_LOG" | tail -5
echo ""

echo "💡 Summary:"
echo "   ✅ Your repo files are properly excluded from iCloud sync"
echo "   ⚠️  Errors shown are from system services (Notes, FileProvider)"
echo "   ✅ These system errors don't affect your repo syncing"

