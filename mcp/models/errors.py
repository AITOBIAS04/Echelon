"""Standardised error codes and response format for MCP tools."""

from __future__ import annotations

from typing import Any, Dict

from mcp.models.meta import build_meta


# Committed error codes — do not add new codes without spec review
ERROR_CODES = {
    "SCHEMA_INVALID": "Certificate does not conform to required schema",
    "HASH_MISMATCH": "Computed hash does not match declared hash",
    "INPUT_MALFORMED": "Input parameters are malformed or missing required fields",
    "INTERNAL_ERROR": "Unexpected internal error during processing",
}


def error_response(
    error_code: str,
    error_message: str,
) -> Dict[str, Any]:
    """Build a standardised error response.

    Format:
        {
            "overall_verdict": "ERROR",
            "error_code": "...",
            "error_message": "...",
            "_meta": { ... }
        }
    """
    if error_code not in ERROR_CODES:
        error_code = "INTERNAL_ERROR"

    return {
        "overall_verdict": "ERROR",
        "error_code": error_code,
        "error_message": error_message,
        "_meta": build_meta(),
    }
