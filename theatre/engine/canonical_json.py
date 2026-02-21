"""Canonical JSON utility — RFC 8785 compliant deterministic serialisation.

All commitment hash computations MUST use canonical_json(). Never raw json.dumps().
"""

from __future__ import annotations

import json
import math
from typing import Any


def canonical_json(obj: Any) -> str:
    """Produce RFC 8785-compliant canonical JSON.

    Rules:
    - Keys sorted lexicographically (Unicode code point order) at every level
    - No whitespace between tokens
    - Integers as-is, floats normalised (no trailing zeroes, no positive sign)
    - null included (not omitted)
    - Arrays preserve insertion order
    - NaN and Infinity prohibited
    """
    normalised = _normalise_value(obj)
    return json.dumps(
        normalised,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _normalise_value(v: Any) -> Any:
    """Recursively normalise values for canonical representation."""
    if v is None:
        return None
    if isinstance(v, bool):
        # Must check bool before int — bool is a subclass of int in Python
        return v
    if isinstance(v, dict):
        return {k: _normalise_value(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_normalise_value(item) for item in v]
    if isinstance(v, float):
        return _normalise_float(v)
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        return v
    # Fallback: attempt to convert via standard JSON serialisation
    raise TypeError(f"canonical_json: unsupported type {type(v).__name__}: {v!r}")


def _normalise_float(f: float) -> float | int:
    """Normalise floats: 1.0 → 1, 0.10 → 0.1. Disallow NaN/Inf."""
    if math.isnan(f) or math.isinf(f):
        raise ValueError(f"canonical_json: NaN/Infinity not permitted: {f}")
    # Convert whole-number floats to int: 1.0 → 1, -3.0 → -3
    if f == int(f) and abs(f) < 2**53:
        return int(f)
    return f
