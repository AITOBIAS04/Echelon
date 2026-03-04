"""CI wrapper for validate_genome.py -- ensures all genomes pass validation.

Calls the standalone validator via subprocess so it runs in CI alongside
the rest of the test suite.

Cycle-014b, Sprint 1 -- Task 7.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

GENOME_DIR = Path(__file__).resolve().parents[3] / "grimoires" / "loa" / "genomes"
VALIDATOR = GENOME_DIR / "validate_genome.py"


def test_all_genomes_valid():
    """All genome YAML files pass the standalone validator."""
    result = subprocess.run(
        ["python3", str(VALIDATOR), "--summary"],
        capture_output=True,
        text=True,
        cwd=str(GENOME_DIR),
    )
    assert result.returncode == 0, (
        f"Genome validation failed:\n{result.stdout}\n{result.stderr}"
    )
