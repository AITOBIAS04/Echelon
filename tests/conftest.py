"""Root conftest — ensures the project root is on sys.path for theatre imports."""

import sys
from pathlib import Path

# Add project root so `theatre` package is importable
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
