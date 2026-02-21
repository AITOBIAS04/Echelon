"""Deterministic Oracle Adapter — passthrough for fixture-based scoring.

Returns input_data as-is. The scorer independently recomputes each check
from inputs and verifies against expected_outputs in ground_truth.
"""

from __future__ import annotations

from typing import Any


class DeterministicOracleAdapter:
    """Passes fixture inputs through — the scorer does the real work."""

    async def invoke(self, input_data: dict[str, Any]) -> dict[str, Any]:
        return input_data
