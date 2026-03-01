"""echelon_hash MCP tool — canonical hash computation.

Computes SHA-256 hash using Echelon Canonical JSON v0 for JSON objects,
or raw SHA-256 for binary data.

Reuses the existing canonical hash utility from the pipeline.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from mcp.models.errors import error_response
from mcp.models.inputs import parse_input
from mcp.models.meta import build_meta

# Import canonical hash from existing pipeline
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.echelon_verify import canonical_json, sha256_bytes


TOOL_DEFINITION = {
    "name": "echelon_hash",
    "description": (
        "Compute SHA-256 hash of content using Echelon Canonical JSON v0 "
        "for JSON objects, or raw SHA-256 for binary data."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "content": {
                "type": "object",
                "description": "Content wrapped in mode object: {mode: 'inline', value: <JSON object or string>}",
            },
        },
        "required": ["content"],
    },
}


def handle(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle echelon_hash tool call."""
    raw_content = arguments.get("content")
    if raw_content is None:
        return error_response("INPUT_MALFORMED", "Missing required field: content")

    try:
        content = parse_input(raw_content, "content")
    except ValueError as e:
        return error_response("INPUT_MALFORMED", str(e))

    try:
        if isinstance(content, (dict, list)):
            # Echelon Canonical JSON v0: sorted keys, no whitespace, UTF-8
            canonical = canonical_json(content)
            hash_hex = sha256_bytes(canonical.encode("utf-8"))
        elif isinstance(content, str):
            # Treat string content as raw bytes
            hash_hex = sha256_bytes(content.encode("utf-8"))
        else:
            return error_response(
                "INPUT_MALFORMED",
                f"content.value must be a JSON object, array, or string, got {type(content).__name__}",
            )
    except Exception as e:
        return error_response("INTERNAL_ERROR", f"Hash computation failed: {e}")

    return {
        "hash": f"sha256:{hash_hex}",
        "_meta": build_meta(),
    }
