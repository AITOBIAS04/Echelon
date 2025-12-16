#!/bin/bash
# =============================================================================
# ECHELON PROJECT SETUP (Bun Edition)
# =============================================================================
# Run this after cloning/extracting the project to install all dependencies
# 
# Prerequisites:
#   - Bun installed: curl -fsSL https://bun.sh/install | bash
#   - Python 3.11+ installed
#   - Node.js 18+ (for Hardhat compatibility)
#
# Usage:
#   chmod +x setup_bun.sh
#   ./setup_bun.sh
# =============================================================================

set -e  # Exit on error

echo "=============================================="
echo "🚀 ECHELON PROJECT SETUP (Bun Edition)"
echo "=============================================="
echo ""

# Check for Bun
if ! command -v bun &> /dev/null; then
    echo "❌ Bun not found. Installing..."
    curl -fsSL https://bun.sh/install | bash
    source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true
fi

echo "✅ Bun version: $(bun --version)"

# Check for Python (prefer 3.12 for virtuals-acp compatibility)
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD=python3.12
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    echo "❌ Python 3 not found. Please install Python 3.11 or 3.12"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python version: $PYTHON_VERSION (using $PYTHON_CMD)"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "📦 Installing Frontend Dependencies (Bun)..."
echo "----------------------------------------------"
cd frontend

# Remove any stale lock files
rm -f package-lock.json yarn.lock bun.lockb 2>/dev/null || true

# Install with Bun
bun install

echo "✅ Frontend dependencies installed"

echo ""
echo "📦 Installing Smart Contract Dependencies (Bun)..."
echo "----------------------------------------------"
cd ../smart-contracts

# Remove any stale lock files
rm -f package-lock.json yarn.lock bun.lockb 2>/dev/null || true

# Install with Bun
bun install

echo "✅ Smart contract dependencies installed"

echo ""
echo "🐍 Setting up Python Backend..."
echo "----------------------------------------------"
cd ../backend

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Backend dependencies installed"

echo ""
echo "🔐 Setting up Environment Variables..."
echo "----------------------------------------------"
cd ..

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Please edit .env and add your API keys"
    else
        # Create a minimal .env
        cat > .env << 'EOF'
# =============================================================================
# ECHELON ENVIRONMENT CONFIGURATION
# =============================================================================

# JWT Secret (REQUIRED - generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')
JWT_SECRET_KEY=CHANGE_ME_IN_PRODUCTION

# Environment
ENVIRONMENT=development

# =============================================================================
# AI PROVIDERS (at least one required)
# =============================================================================

# Anthropic (Premium tier - highest quality)
ANTHROPIC_API_KEY=

# Groq (Free tier - fast inference)
GROQ_API_KEY=

# Mistral (Budget tier - Devstral models)
MISTRAL_API_KEY=

# OpenAI (Standard tier - reliable fallback)
OPENAI_API_KEY=

# =============================================================================
# BLOCKCHAIN
# =============================================================================

# Wallet seed for HD derivation (12-24 words)
MASTER_WALLET_SEED=

# Virtuals Protocol Entity ID (from registration)
ENTITY_ID=0

# RPC URLs
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
POLYGON_RPC_URL=https://polygon-rpc.com

# Deployer private key (for contract deployment only)
DEPLOYER_PRIVATE_KEY=

# =============================================================================
# OPTIONAL SERVICES
# =============================================================================

# Coinbase Commerce (for fiat onramp)
COINBASE_COMMERCE_API_KEY=

# Market Data
POLYGON_API_KEY=

# OSINT Sources
TWITTER_BEARER_TOKEN=
NEWS_API_KEY=

EOF
        echo "⚠️  Created .env - please add your API keys"
    fi
else
    echo "✅ .env already exists"
fi

# Also create frontend .env.local if needed
if [ ! -f "frontend/.env.local" ]; then
    cat > frontend/.env.local << 'EOF'
# Frontend Environment
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ONCHAINKIT_API_KEY=
NEXT_PUBLIC_WALLET_CONNECT_PROJECT_ID=
EOF
    echo "✅ Created frontend/.env.local"
fi

echo ""
echo "=============================================="
echo "✅ SETUP COMPLETE!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your API keys:"
echo "   - At minimum: JWT_SECRET_KEY"
echo "   - For AI: GROQ_API_KEY (free) or ANTHROPIC_API_KEY"
echo "   - For blockchain: MASTER_WALLET_SEED"
echo ""
echo "2. Start the backend:"
echo "   cd backend"
echo "   source .venv/bin/activate"
echo "   uvicorn main:app --reload --port 8000"
echo ""
echo "3. Start the frontend (new terminal):"
echo "   cd frontend"
echo "   bun dev"
echo ""
echo "4. (Optional) Deploy contracts:"
echo "   cd smart-contracts"
echo "   bunx hardhat compile"
echo "   bunx hardhat run scripts/deploy.js --network baseSepolia"
echo ""
echo "=============================================="
