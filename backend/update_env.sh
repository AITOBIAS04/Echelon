#!/bin/bash
# Update USE_MOCKS in .env file

cd "$(dirname "$0")"

if [ -f .env ]; then
    # Check if USE_MOCKS already exists
    if grep -q "^USE_MOCKS=" .env 2>/dev/null; then
        # Replace existing line
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' 's/^USE_MOCKS=.*/USE_MOCKS=false/' .env
        else
            # Linux
            sed -i 's/^USE_MOCKS=.*/USE_MOCKS=false/' .env
        fi
        echo "✅ Updated USE_MOCKS=false in .env"
    else
        # Append new line
        echo "USE_MOCKS=false" >> .env
        echo "✅ Added USE_MOCKS=false to .env"
    fi
    
    # Show the line
    echo ""
    echo "Current USE_MOCKS setting:"
    grep USE_MOCKS .env
else
    echo "⚠️  .env file not found. Creating it..."
    echo "USE_MOCKS=false" > .env
    echo "✅ Created .env with USE_MOCKS=false"
fi


