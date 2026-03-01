"""
Echelon Verifier MCP Server — v0.8.0

Exposes 5 stateless verification tools over MCP (stdio transport).
Implements JSON-RPC 2.0 / MCP protocol directly — no external SDK dependency.
Compatible with Python 3.9+.

Tools:
    echelon_verify      — Full certificate + evidence bundle verification
    echelon_inspect     — Certificate summary (no verification)
    echelon_hash        — Canonical JSON hash (Echelon Canonical JSON v0)
    echelon_schema_check — Certificate schema validation
    echelon_replay      — Template/fixture structural consistency check
"""

__version__ = "0.8.0"
