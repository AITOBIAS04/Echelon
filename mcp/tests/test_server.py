"""Tests for mcp.server — JSON-RPC dispatch and protocol handling."""

from __future__ import annotations

import json
from typing import Any, Dict

import pytest

from mcp.server import TOOLS, dispatch, jsonrpc_response, jsonrpc_error


# ────────────────────────────────────────────────
# JSON-RPC helpers
# ────────────────────────────────────────────────

class TestJsonRpcHelpers:
    def test_response_format(self):
        resp = jsonrpc_response(1, {"key": "val"})
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 1
        assert resp["result"] == {"key": "val"}

    def test_error_format(self):
        resp = jsonrpc_error(2, -32600, "Invalid request")
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 2
        assert resp["error"]["code"] == -32600
        assert resp["error"]["message"] == "Invalid request"


# ────────────────────────────────────────────────
# MCP protocol dispatch
# ────────────────────────────────────────────────

class TestDispatch:
    def test_initialize(self):
        resp = dispatch({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"clientInfo": {"name": "test"}},
        })
        assert resp is not None
        assert resp["id"] == 1
        result = resp["result"]
        assert "protocolVersion" in result
        assert result["serverInfo"]["name"] == "echelon-verifier"

    def test_tools_list(self):
        resp = dispatch({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        })
        assert resp is not None
        tools = resp["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 7
        names = {t["name"] for t in tools}
        assert names == {
            "echelon_verify",
            "echelon_inspect",
            "echelon_hash",
            "echelon_schema_check",
            "echelon_replay",
            "echelon_status",
            "echelon_calibrate",
        }

    def test_tools_call_hash(self):
        resp = dispatch({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "echelon_hash",
                "arguments": {
                    "content": {"mode": "inline", "value": {"test": 1}},
                },
            },
        })
        assert resp is not None
        assert resp["id"] == 3
        call_result = resp["result"]
        assert call_result["isError"] is False
        content_text = call_result["content"][0]["text"]
        parsed = json.loads(content_text)
        assert parsed["hash"].startswith("sha256:")

    def test_tools_call_unknown_tool(self):
        resp = dispatch({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
        })
        assert resp is not None
        call_result = resp["result"]
        assert call_result["isError"] is True

    def test_notification_returns_none(self):
        resp = dispatch({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        })
        assert resp is None

    def test_unknown_method(self):
        resp = dispatch({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "unknown/method",
        })
        assert resp is not None
        assert "error" in resp
        assert resp["error"]["code"] == -32601


# ────────────────────────────────────────────────
# Tool registry
# ────────────────────────────────────────────────

class TestToolRegistry:
    def test_all_tools_have_definition_and_handler(self):
        for name, entry in TOOLS.items():
            assert "definition" in entry, f"{name} missing definition"
            assert "handler" in entry, f"{name} missing handler"
            assert callable(entry["handler"]), f"{name} handler not callable"

    def test_definition_has_name_and_schema(self):
        for name, entry in TOOLS.items():
            defn = entry["definition"]
            assert "name" in defn, f"{name} definition missing name"
            assert "inputSchema" in defn, f"{name} definition missing inputSchema"
            assert defn["name"] == name, f"{name} definition name mismatch"
