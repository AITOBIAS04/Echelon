"""Input mode objects for MCP tool parameters.

v1.0: Only inline mode supported.
v1.1: id mode (store lookup) planned.
"""

from __future__ import annotations

from typing import Any, Dict


SUPPORTED_MODES = {"inline"}


def parse_input(raw: Any, param_name: str = "input") -> Any:
    """Parse a mode-wrapped input object and return the value.

    Expected format: {"mode": "inline", "value": <content>}

    Raises ValueError if mode is unsupported or format is invalid.
    """
    if not isinstance(raw, dict):
        raise ValueError(
            f"{param_name}: expected object with 'mode' and 'value', "
            f"got {type(raw).__name__}"
        )

    mode = raw.get("mode")
    if mode is None:
        raise ValueError(f"{param_name}: missing 'mode' field")

    if mode not in SUPPORTED_MODES:
        raise ValueError(
            f"{param_name}: unsupported mode '{mode}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_MODES))} (id mode deferred to v1.1)"
        )

    if "value" not in raw:
        raise ValueError(f"{param_name}: missing 'value' field")

    return raw["value"]
