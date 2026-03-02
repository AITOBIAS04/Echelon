"""echelon_calibrate MCP tool — full calibration pipeline execution.

Runs the construct calibration pipeline via the existing async runner
and returns the certificate with a pipeline summary.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

from mcp.models.errors import error_response
from mcp.models.meta import build_meta

# Path setup for runner import — same pattern as verify.py, hash.py, etc.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.run_construct_calibration import CONSTRUCTS, run_construct_calibration


TOOL_DEFINITION = {
    "name": "echelon_calibrate",
    "description": (
        "Run the full construct calibration pipeline. Produces a calibration "
        "certificate with deterministic replay, scoring, tier assignment, "
        "and evidence bundle generation."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "construct_id": {
                "type": "string",
                "description": "Construct key from the registry (e.g. 'community_oracle_v1')",
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory for certificates and evidence bundles (default: 'output')",
            },
        },
        "required": ["construct_id"],
    },
}


def handle(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle echelon_calibrate tool call."""
    # 1. Extract and validate construct_id
    construct_id = arguments.get("construct_id", "")
    if not construct_id:
        return error_response("INPUT_MALFORMED", "Missing required field: construct_id")

    # 2. Validate against CONSTRUCTS registry
    if construct_id not in CONSTRUCTS:
        return error_response(
            "INPUT_MALFORMED",
            f"Unknown construct: '{construct_id}'. "
            f"Available: {', '.join(CONSTRUCTS.keys())}",
        )

    # 3. Extract output_dir
    output_dir = Path(arguments.get("output_dir", "output"))

    try:
        # 4. Bridge async to sync — run the calibration pipeline
        cert_path, cert_dict = asyncio.run(
            run_construct_calibration(construct_id, output_dir)
        )

        # 5. Run echelon_verify against the certificate
        from mcp.tools import verify as mcp_verify

        verify_result = mcp_verify.handle({
            "certificate": {"mode": "inline", "value": cert_dict},
        })
        mcp_verify_verdict = verify_result.get("overall_verdict", "ERROR")

        # 6. Build pipeline summary
        pipeline_summary = {
            "construct_id": construct_id,
            "template_id": cert_dict.get("template_id"),
            "composite_score": cert_dict.get("composite_score"),
            "scores": cert_dict.get("scores", {}),
            "verification_tier": cert_dict.get("verification_tier"),
            "evidence_bundle_hash": cert_dict.get("evidence_bundle_hash"),
            "mcp_verify_verdict": mcp_verify_verdict,
        }

        # 7. Return combined response
        return {
            "certificate": cert_dict,
            "pipeline_summary": pipeline_summary,
            "_meta": build_meta(),
        }

    except Exception as e:
        return error_response("INTERNAL_ERROR", str(e))
