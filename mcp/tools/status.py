"""echelon_status MCP tool — construct verification state query.

Scans the output directory for existing calibration certificates
and reports the current verification state of a construct.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.models.errors import error_response
from mcp.models.meta import build_meta


TOOL_DEFINITION = {
    "name": "echelon_status",
    "description": (
        "Query the current verification state of a construct. Returns the "
        "latest certificate, tier, composite score, expiry, and certificate count."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "construct_id": {
                "type": "string",
                "description": "Construct identifier (e.g. 'community_oracle_v1')",
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory containing calibration results (default: 'output')",
            },
        },
        "required": ["construct_id"],
    },
}

# Threshold from TierAssigner — number of replays required for BACKTESTED tier
_BACKTESTED_MIN_REPLAYS = 50


def handle(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle echelon_status tool call."""
    # 1. Extract and validate construct_id
    construct_id = arguments.get("construct_id", "")
    if not construct_id:
        return error_response("INPUT_MALFORMED", "Missing required field: construct_id")

    # 2. Extract output_dir, default to "output"
    output_dir = Path(arguments.get("output_dir", "output"))

    # 3. Build certificate directory path
    cert_dir = output_dir / "construct_calibration" / construct_id / "certificates"

    # 4. If directory does not exist, return zero-certificate response
    if not cert_dir.is_dir():
        return {
            "construct_id": construct_id,
            "certificates_found": 0,
            "latest_certificate": None,
            "tier_summary": None,
            "_meta": build_meta(),
        }

    # 5. Scan for *.json files
    json_files = list(cert_dir.glob("*.json"))

    # 6. Parse each file, skip corrupt ones
    certificates: List[Dict[str, Any]] = []
    for fp in json_files:
        try:
            cert = json.loads(fp.read_text())
            if isinstance(cert, dict):
                certificates.append(cert)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: skipping {fp}: {e}", file=sys.stderr)
            continue

    # 7. If no valid certificates, return zero response
    if not certificates:
        return {
            "construct_id": construct_id,
            "certificates_found": 0,
            "latest_certificate": None,
            "tier_summary": None,
            "_meta": build_meta(),
        }

    # 8. Sort by issued_at (ISO 8601 string comparison)
    certificates.sort(key=lambda c: c.get("issued_at", ""))

    # 9. Select latest (most recent)
    latest = certificates[-1]

    # 10. Build tier_summary
    replay_count = latest.get("replay_count", 0)
    replays_needed = max(0, _BACKTESTED_MIN_REPLAYS - replay_count)

    # 11. Return structured response
    return {
        "construct_id": construct_id,
        "certificates_found": len(certificates),
        "latest_certificate": {
            "certificate_id": latest.get("certificate_id"),
            "template_id": latest.get("template_id"),
            "composite_score": latest.get("composite_score"),
            "verification_tier": latest.get("verification_tier"),
            "issued_at": latest.get("issued_at"),
            "replay_count": latest.get("replay_count", 0),
        },
        "tier_summary": {
            "current_tier": latest.get("verification_tier"),
            "backtested_threshold": _BACKTESTED_MIN_REPLAYS,
            "current_replays": replay_count,
            "replays_needed": replays_needed,
        },
        "_meta": build_meta(),
    }
