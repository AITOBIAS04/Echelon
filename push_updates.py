#!/usr/bin/env python3
"""Push all updates to GitHub."""
import subprocess
import sys

def run_cmd(cmd, description):
    """Run a command and return the result."""
    print(f"📋 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"⚠️  {result.stderr}", file=sys.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False

def main():
    print("🚀 Pushing all updates to GitHub...\n")
    
    # Check git status
    if not run_cmd("git status --short", "Checking git status"):
        print("❌ Not a git repository or git not available")
        return 1
    
    # Get current branch
    branch_result = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True)
    current_branch = branch_result.stdout.strip() or "main"
    print(f"📍 Current branch: {current_branch}\n")
    
    # Stage all changes
    if not run_cmd("git add -A", "Staging all changes"):
        return 1
    
    # Check if there are changes to commit
    status_result = subprocess.run("git status --short", shell=True, capture_output=True, text=True)
    if not status_result.stdout.strip():
        print("✅ No changes to commit")
        return 0
    
    # Commit
    commit_msg = """Add Polymarket integration and frontend SIGINT panel

- Added PolymarketClient for CLOB and Gamma API integration
- Replaced Kalshi sync with Polymarket market sync task
- Updated market_sync.py to sync real Polymarket data to timelines
- Fixed API routes to support database mode (USE_MOCKS=false)
- Made engine dependencies Optional in butterfly_routes and paradox_routes
- Fixed missing Optional import in paradox_routes.py
- Created React frontend with SIGINT panel, timeline cards, wing flap feed
- Added TypeScript types matching backend API responses
- Created API clients for Butterfly and Paradox endpoints
- Added React Query hooks for real-time data fetching
- Configured Tailwind CSS with Echelon dark terminal theme
- Updated worker tasks to use MarketSyncTask instead of KalshiSyncTask"""
    
    commit_cmd = f'git commit -m "{commit_msg}"'
    if not run_cmd(commit_cmd, "Committing changes"):
        return 1
    
    # Push
    if not run_cmd(f"git push origin {current_branch}", f"Pushing to GitHub (origin/{current_branch})"):
        return 1
    
    print("\n✅ Successfully pushed to GitHub!")
    print("🔗 Repository: https://github.com/AITOBIAS04/prediction-market-monorepo")
    return 0

if __name__ == "__main__":
    sys.exit(main())


