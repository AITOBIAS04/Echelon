"""echelon_verify MCP tool — full certificate + evidence bundle verification.

Delegates to tools/echelon_verify.py verification logic.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.models.errors import error_response
from mcp.models.inputs import parse_input
from mcp.models.meta import build_meta

# Import verifier functions
import sys
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.echelon_verify import (
    CheckResult,
    Verdict,
    VerificationReport,
    check_composite_score,
    check_dataset_hash,
    check_evidence_bundle_hash,
    check_evidence_bundle_structure,
    check_expiry,
    check_schema_compliance,
    check_template_hash_consistency,
    check_temporal_ordering,
    check_weight_sum,
)


TOOL_DEFINITION = {
    "name": "echelon_verify",
    "description": (
        "Full verification of an Echelon calibration certificate against its "
        "evidence bundle. Checks schema compliance, arithmetic consistency, "
        "hash integrity, and structural validity."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "certificate": {
                "type": "object",
                "description": "Certificate JSON wrapped in mode object: {mode: 'inline', value: {...}}",
            },
            "evidence_bundle_path": {
                "type": "string",
                "description": "Absolute path to the evidence bundle directory",
            },
        },
        "required": ["certificate"],
    },
}


def _check_result_to_dict(cr: CheckResult) -> Dict[str, Any]:
    return {
        "check_id": cr.check_id,
        "title": cr.title,
        "verdict": cr.verdict.value,
        "detail": cr.detail,
    }


def handle(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle echelon_verify tool call."""
    # Parse certificate input
    raw_cert = arguments.get("certificate")
    if raw_cert is None:
        return error_response("INPUT_MALFORMED", "Missing required field: certificate")

    try:
        cert = parse_input(raw_cert, "certificate")
    except ValueError as e:
        return error_response("INPUT_MALFORMED", str(e))

    if not isinstance(cert, dict):
        return error_response("INPUT_MALFORMED", "certificate.value must be a JSON object")

    # Parse evidence bundle path (optional)
    evidence_dir: Optional[Path] = None
    ebp = arguments.get("evidence_bundle_path")
    if ebp:
        evidence_dir = Path(ebp)
        if not evidence_dir.exists():
            return error_response(
                "INPUT_MALFORMED",
                f"Evidence bundle directory not found: {ebp}",
            )

    # Run verification checks
    report = VerificationReport()
    report.certificate_id = cert.get("certificate_id", "unknown")
    report.template_id = cert.get("template_id", "unknown")

    # Schema checks
    for r in check_schema_compliance(cert):
        report.add(r)

    # Arithmetic checks
    report.add(check_composite_score(cert))
    report.add(check_weight_sum(cert))

    # Temporal checks
    report.add(check_expiry(cert))
    report.add(check_temporal_ordering(cert))

    # Hash checks (require evidence_dir)
    report.add(check_dataset_hash(cert, evidence_dir))
    report.add(check_evidence_bundle_hash(cert, evidence_dir))

    # Structure checks
    report.add(check_evidence_bundle_structure(evidence_dir))
    report.add(check_template_hash_consistency(cert, evidence_dir))

    return {
        "overall_verdict": report.overall_verdict.value,
        "certificate_id": report.certificate_id,
        "template_id": report.template_id,
        "checks": [_check_result_to_dict(c) for c in report.checks],
        "summary": {
            "total": len(report.checks),
            "passed": report.pass_count,
            "failed": report.fail_count,
            "warnings": report.warn_count,
        },
        "_meta": build_meta(),
    }
