"""All-templates verification — run pipeline for each of the 4 templates.

Validates echelon_verify passes for all and composite scores are within
expected ranges.
"""

import asyncio
import sys
from pathlib import Path

import pytest

project_root = str(Path(__file__).resolve().parents[2])
osint_root = str(Path(__file__).resolve().parents[2] / "osint")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if osint_root not in sys.path:
    sys.path.insert(0, osint_root)

from theatre.scoring.arrears_scorer import ArrearsScorer  # noqa: E402
from theatre.scoring.escrow_scorer import EscrowScorer  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

TEMPLATES = [
    "escrow_milestone_release_v1",
    "distribution_waterfall_v1",
    "ledger_reconciliation_v1",
    "arrears_resolution_v1",
]

# Expected composite score ranges (min, max) — tolerance of 0.05.
EXPECTED_COMPOSITES = {
    "escrow_milestone_release_v1": (0.80, 0.92),
    "distribution_waterfall_v1": (0.88, 0.98),
    "ledger_reconciliation_v1": (0.84, 0.95),
    "arrears_resolution_v1": (0.88, 0.98),
}


@pytest.fixture(scope="module")
def all_results(tmp_path_factory):
    """Run pipeline for all 4 templates, return {key: (passed, composite)}."""
    from run_two_rail_certificates import run_template

    output_dir = tmp_path_factory.mktemp("all_templates")
    results = {}
    for key in TEMPLATES:
        passed, composite = asyncio.run(run_template(key, output_dir, verbose=False))
        results[key] = (passed, composite)
    return results


@pytest.mark.parametrize("template_key", TEMPLATES)
def test_all_four_templates_pass_verifier(all_results, template_key):
    """Each template produces Verifier CLI PASS."""
    passed, _ = all_results[template_key]
    assert passed is True, f"{template_key} did not pass verifier"


@pytest.mark.parametrize("template_key", TEMPLATES)
def test_composite_scores_in_expected_range(all_results, template_key):
    """Composite scores within expected range."""
    _, composite = all_results[template_key]
    lo, hi = EXPECTED_COMPOSITES[template_key]
    assert lo <= composite <= hi, (
        f"{template_key}: composite {composite:.4f} outside [{lo}, {hi}]"
    )
