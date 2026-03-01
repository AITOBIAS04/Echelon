"""echelon_schema_check MCP tool — certificate schema validation.

Runs schema compliance checks only (no hash or evidence verification).
"""

from __future__ import annotations

from typing import Any, Dict

from mcp.models.errors import error_response
from mcp.models.inputs import parse_input
from mcp.models.meta import build_meta

# Import verifier schema checks
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.echelon_verify import Verdict, check_schema_compliance


TOOL_DEFINITION = {
    "name": "echelon_schema_check",
    "description": (
        "Validate an Echelon calibration certificate against the required schema. "
        "Checks required fields, verification tier, execution path, timestamps, "
        "hash formats, and score completeness."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "certificate": {
                "type": "object",
                "description": "Certificate JSON wrapped in mode object: {mode: 'inline', value: {...}}",
            },
        },
        "required": ["certificate"],
    },
}


def handle(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle echelon_schema_check tool call."""
    raw_cert = arguments.get("certificate")
    if raw_cert is None:
        return error_response("INPUT_MALFORMED", "Missing required field: certificate")

    try:
        cert = parse_input(raw_cert, "certificate")
    except ValueError as e:
        return error_response("INPUT_MALFORMED", str(e))

    if not isinstance(cert, dict):
        return error_response("INPUT_MALFORMED", "certificate.value must be a JSON object")

    # Run schema checks
    results = check_schema_compliance(cert)

    errors = []
    for r in results:
        if r.verdict == Verdict.FAIL:
            errors.append({
                "check_id": r.check_id,
                "title": r.title,
                "detail": r.detail,
            })

    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
        "checks_run": len(results),
        "_meta": build_meta(),
    }
