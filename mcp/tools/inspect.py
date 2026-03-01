"""echelon_inspect MCP tool — certificate summary without verification.

Parses certificate and returns key fields. No verification performed.
"""

from __future__ import annotations

from typing import Any, Dict

from mcp.models.errors import error_response
from mcp.models.inputs import parse_input
from mcp.models.meta import build_meta


TOOL_DEFINITION = {
    "name": "echelon_inspect",
    "description": (
        "Parse an Echelon calibration certificate and return a summary "
        "of key fields. No verification is performed."
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

# Fields to extract for the summary
_SUMMARY_FIELDS = [
    "certificate_id",
    "theatre_id",
    "template_id",
    "construct_id",
    "construct_version",
    "verification_tier",
    "execution_path",
    "composite_score",
    "replay_count",
    "scorer_version",
    "methodology_version",
    "issued_at",
    "expires_at",
    "commitment_hash",
    "evidence_bundle_hash",
    "dataset_hash",
    "ground_truth_source",
]


def handle(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle echelon_inspect tool call."""
    raw_cert = arguments.get("certificate")
    if raw_cert is None:
        return error_response("INPUT_MALFORMED", "Missing required field: certificate")

    try:
        cert = parse_input(raw_cert, "certificate")
    except ValueError as e:
        return error_response("INPUT_MALFORMED", str(e))

    if not isinstance(cert, dict):
        return error_response("INPUT_MALFORMED", "certificate.value must be a JSON object")

    # Extract summary
    summary: Dict[str, Any] = {}
    for field in _SUMMARY_FIELDS:
        val = cert.get(field)
        if val is not None:
            summary[field] = val

    # Include scores breakdown
    scores = cert.get("scores")
    if isinstance(scores, dict):
        summary["scores"] = scores

    criteria = cert.get("criteria")
    if isinstance(criteria, dict):
        summary["criteria"] = criteria

    return {
        "summary": summary,
        "_meta": build_meta(),
    }
