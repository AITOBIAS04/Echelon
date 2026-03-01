"""echelon_replay MCP tool — template/fixture structural consistency check.

Validates that template and fixture dataset are structurally consistent:
schema, dataset hash, record structure, criteria, weights.
"""

from __future__ import annotations

from typing import Any, Dict

from mcp.models.errors import error_response
from mcp.models.inputs import parse_input
from mcp.models.meta import build_meta

# Import verifier replay checks
import sys
import json
import tempfile
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.echelon_verify import (
    Verdict,
    check_deterministic_replay,
    canonical_json,
    sha256_bytes,
)


TOOL_DEFINITION = {
    "name": "echelon_replay",
    "description": (
        "Check structural consistency between a theatre template and its "
        "fixture dataset. Validates schema, dataset hash, record structure, "
        "criteria definitions, and weight sums."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "template": {
                "type": "object",
                "description": "Template JSON wrapped in mode object: {mode: 'inline', value: {...}}",
            },
            "fixtures": {
                "type": "object",
                "description": "Fixtures JSON wrapped in mode object: {mode: 'inline', value: {...}}",
            },
        },
        "required": ["template", "fixtures"],
    },
}


def handle(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle echelon_replay tool call."""
    raw_template = arguments.get("template")
    raw_fixtures = arguments.get("fixtures")

    if raw_template is None:
        return error_response("INPUT_MALFORMED", "Missing required field: template")
    if raw_fixtures is None:
        return error_response("INPUT_MALFORMED", "Missing required field: fixtures")

    try:
        template = parse_input(raw_template, "template")
        fixtures = parse_input(raw_fixtures, "fixtures")
    except ValueError as e:
        return error_response("INPUT_MALFORMED", str(e))

    if not isinstance(template, dict):
        return error_response("INPUT_MALFORMED", "template.value must be a JSON object")
    if not isinstance(fixtures, dict):
        return error_response("INPUT_MALFORMED", "fixtures.value must be a JSON object")

    # Write to temp files for the verifier's check_deterministic_replay
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tf:
            json.dump(template, tf)
            template_path = Path(tf.name)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as ff:
            json.dump(fixtures, ff)
            fixtures_path = Path(ff.name)

        results = check_deterministic_replay(template_path, fixtures_path)
    except Exception as e:
        return error_response("INTERNAL_ERROR", f"Replay check failed: {e}")
    finally:
        # Clean up temp files
        try:
            template_path.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            fixtures_path.unlink(missing_ok=True)
        except Exception:
            pass

    mismatches = []
    for r in results:
        if r.verdict == Verdict.FAIL:
            mismatches.append({
                "check_id": r.check_id,
                "title": r.title,
                "detail": r.detail,
            })

    consistent = len(mismatches) == 0

    return {
        "consistent": consistent,
        "mismatches": mismatches,
        "checks_run": len(results),
        "_meta": build_meta(),
    }
