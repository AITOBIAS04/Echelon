import os
import re

# Configuration
TARGET_DIRS = ["backend"]

# Modules that should always be prefixed with 'backend.'
MODULES = ["core", "agents", "simulation", "payments", "api"]

def normalize_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Remove try/except ImportError blocks that mask issues
    # This matches the pattern: try:\n ... from backend.x ... except ImportError:\n ... from x ...
    # and replaces it with just the secure import.
    # (Simplified approach: We just fix the import strings globally first)
    for mod in MODULES:
        # Pattern: from core.xyz import... -> from backend.core.xyz import...
        # Negative lookbehind ensures we don't double-prefix (backend.backend.core)
        pattern = r'(from\s+)(?!backend\.)(' + mod + r')(\.| )'
        replacement = r'\1backend.\2\3'
        content = re.sub(pattern, replacement, content)
        
        # Pattern: import core.xyz -> import backend.core.xyz
        pattern_import = r'(import\s+)(?!backend\.)(' + mod + r')(\.| )'
        content = re.sub(pattern_import, replacement, content)
    
    if content != original_content:
        print(f"🔧 Fixing imports in: {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

def main():
    root_dir = os.getcwd()
    print(f"🔍 Scanning for python files in {root_dir}...")
    
    for target in TARGET_DIRS:
        target_path = os.path.join(root_dir, target)
        if not os.path.exists(target_path):
            print(f"⚠️ Directory not found: {target_path}")
            continue
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith(".py") and file != "normalize_imports.py":
                    normalize_file(os.path.join(root, file))
    
    # Also ensure __init__.py files exist (but skip data directories)
    skip_dirs = {"data", "backups", "snapshots", "__pycache__", "node_modules", ".git"}
    for root, dirs, _ in os.walk(os.path.join(root_dir, "backend")):
        # Filter out directories we don't want to create __init__.py in
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for d in dirs:
            # Only create __init__.py in actual Python package directories
            # (ones that contain .py files or are known package dirs)
            init_path = os.path.join(root, d, "__init__.py")
            package_dirs = {"core", "agents", "simulation", "payments", "api", "scripts"}
            if d in package_dirs and not os.path.exists(init_path):
                print(f"➕ Creating missing {init_path}")
                open(init_path, 'a').close()
    print("✅ Import normalization complete.")

if __name__ == "__main__":
    main()

