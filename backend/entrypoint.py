#!/usr/bin/env python3
"""
Railway-compatible entrypoint that reads PORT from environment.
"""
import os
import sys
import subprocess
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    # Add current directory to Python path for imports
    import pathlib
    current_dir = pathlib.Path.cwd()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    # Also add parent directory (for running from backend/)
    parent_dir = current_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # Run database migrations before starting the server
    if os.path.exists("alembic.ini"):
        print("🔄 Running database migrations...")
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print("✅ Database migrations completed")
            else:
                print(f"⚠️  Migration warning: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Could not run migrations: {e}")
            print("   Continuing startup anyway...")
    
    print(f"🚀 Starting Echelon backend on port {port}")
    
    # Determine the app path based on where we're running from
    # If we're in the backend directory, use "main:app"
    # If we're in the project root, use "backend.main:app"
    if current_dir.name == "backend":
        app_path = "main:app"
    else:
        app_path = "backend.main:app"
    
    uvicorn.run(
        app_path,
        host="0.0.0.0",
        port=port,
        log_level="info",
        ws="wsproto"  # Use wsproto instead of websockets to avoid version conflicts
    )
