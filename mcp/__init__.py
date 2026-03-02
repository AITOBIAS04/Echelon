"""
Echelon Verifier MCP Server — v1.0.0

Exposes 7 verification and calibration tools over MCP (stdio and HTTP transport).
Implements JSON-RPC 2.0 / MCP protocol directly — no external SDK dependency.
Compatible with Python 3.9+.

Tools:
    echelon_verify       — Full certificate + evidence bundle verification
    echelon_inspect      — Certificate summary (no verification)
    echelon_hash         — Canonical JSON hash (Echelon Canonical JSON v0)
    echelon_schema_check — Certificate schema validation
    echelon_replay       — Template/fixture structural consistency check
    echelon_status       — Construct verification state query
    echelon_calibrate    — Full calibration pipeline execution
"""

__version__ = "1.0.0"
