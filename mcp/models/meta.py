"""_meta envelope for all MCP tool responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


ENGINE_VERSION = "1.0.0"

SCHEMA_VERSIONS = {
    "certificate": "1.0.0",
    "theatre": "2.0.0",
    "verifier": "0.1.0",
}


def build_meta(
    *,
    resolved_inputs: Optional[List[Dict[str, Any]]] = None,
    resolved_inputs_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a _meta envelope dict for inclusion in tool responses."""
    meta: Dict[str, Any] = {
        "engine_version": ENGINE_VERSION,
        "schema_versions": SCHEMA_VERSIONS,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if resolved_inputs is not None:
        meta["resolved_inputs"] = resolved_inputs
    if resolved_inputs_hash is not None:
        meta["resolved_inputs_hash"] = resolved_inputs_hash
    return meta
