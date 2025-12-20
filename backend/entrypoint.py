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
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        ws="wsproto"  # Use wsproto instead of websockets to avoid version conflicts
    )
