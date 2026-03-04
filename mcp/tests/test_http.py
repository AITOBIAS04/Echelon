"""Tests for mcp.http — HTTP transport (JSON-RPC + plain JSON)."""

from __future__ import annotations

import json
import os
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer
from typing import Any, Dict
from unittest import mock

import pytest

from mcp.http import MCPHttpHandler
from mcp.auth import reset_auth_config


# ════════════════════════════════════════════════════════════════
# FIXTURES
# ════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def http_server():
    """Start MCP HTTP server on a random port for testing."""
    server = HTTPServer(("127.0.0.1", 0), MCPHttpHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def _get(base_url: str, path: str) -> urllib.request.Request:
    """Build a GET request."""
    return urllib.request.Request(f"{base_url}{path}", method="GET")


def _post(base_url: str, path: str, data: Any) -> urllib.request.Request:
    """Build a POST request with JSON body."""
    if isinstance(data, (dict, list)):
        body = json.dumps(data).encode("utf-8")
    else:
        body = data.encode("utf-8") if isinstance(data, str) else data
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    return req


# ════════════════════════════════════════════════════════════════
# TESTS
# ════════════════════════════════════════════════════════════════

class TestHttpTransport:
    def test_health_endpoint(self, http_server):
        req = _get(http_server, "/health")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert body == {"status": "ok", "version": "1.0.0", "tools": 7}

    def test_sse_stub(self, http_server):
        req = _get(http_server, "/sse")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert body == {"status": "not_implemented", "available_from": "v1.3"}

    def test_mcp_endpoint_tools_list(self, http_server):
        req = _post(http_server, "/mcp", {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        })
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            tools = body["result"]["tools"]
            assert len(tools) == 7
            names = {t["name"] for t in tools}
            assert "echelon_status" in names
            assert "echelon_calibrate" in names

    def test_mcp_endpoint_tool_call(self, http_server):
        req = _post(http_server, "/mcp", {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "echelon_hash",
                "arguments": {
                    "content": {"mode": "inline", "value": {"test": 1}},
                },
            },
        })
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            content_text = body["result"]["content"][0]["text"]
            parsed = json.loads(content_text)
            assert parsed["hash"].startswith("sha256:")

    def test_mcp_endpoint_malformed(self, http_server):
        req = _post(http_server, "/mcp", "not json at all")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert body["error"]["code"] == -32700

    def test_mcp_endpoint_notification(self, http_server):
        req = _post(http_server, "/mcp", {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        })
        try:
            with urllib.request.urlopen(req) as resp:
                assert resp.status == 204
        except urllib.error.HTTPError as e:
            # Some urllib versions raise HTTPError for 204
            assert e.code == 204

    def test_unknown_get_path(self, http_server):
        req = _get(http_server, "/unknown")
        try:
            urllib.request.urlopen(req)
            pytest.fail("Expected 404")
        except urllib.error.HTTPError as e:
            assert e.code == 404

    def test_unknown_post_path(self, http_server):
        req = _post(http_server, "/unknown", {})
        try:
            urllib.request.urlopen(req)
            pytest.fail("Expected 404")
        except urllib.error.HTTPError as e:
            assert e.code == 404


# ════════════════════════════════════════════════════════════════
# PLAIN JSON TOOL ENDPOINT TESTS (C2)
# ════════════════════════════════════════════════════════════════

class TestPlainJsonEndpoints:
    """Tests for POST /api/v1/tools/{tool_name} — plain JSON in/out."""

    def test_hash_tool_plain_json(self, http_server):
        """Plain JSON endpoint returns tool result directly (no JSON-RPC wrapper)."""
        req = _post(http_server, "/api/v1/tools/echelon_hash", {
            "content": {"mode": "inline", "value": {"test": 1}},
        })
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            # Plain JSON — result is the tool output directly, not wrapped
            assert "hash" in body
            assert body["hash"].startswith("sha256:")

    def test_status_tool_plain_json(self, http_server):
        """echelon_status via plain JSON returns correct structure."""
        req = _post(http_server, "/api/v1/tools/echelon_status", {
            "construct_id": "nonexistent_construct",
        })
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert body["construct_id"] == "nonexistent_construct"
            assert body["certificates_found"] == 0
            assert "_meta" in body

    def test_unknown_tool_returns_404(self, http_server):
        """Unknown tool name returns 404."""
        req = _post(http_server, "/api/v1/tools/nonexistent_tool", {})
        try:
            urllib.request.urlopen(req)
            pytest.fail("Expected 404")
        except urllib.error.HTTPError as e:
            assert e.code == 404
            body = json.loads(e.read())
            assert body["error"] == "tool_not_found"

    def test_schema_check_plain_json(self, http_server):
        """echelon_schema_check via plain JSON endpoint."""
        req = _post(http_server, "/api/v1/tools/echelon_schema_check", {
            "certificate": {
                "mode": "inline",
                "value": {"certificate_id": "test", "theatre_id": "test"},
            },
        })
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert "valid" in body

    def test_empty_body_accepted(self, http_server):
        """Empty body (no Content-Length) is treated as empty arguments."""
        req = urllib.request.Request(
            f"{http_server}/api/v1/tools/echelon_status",
            data=json.dumps({"construct_id": "test"}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200

    def test_jsonrpc_still_works_alongside(self, http_server):
        """JSON-RPC endpoint still works after adding plain JSON endpoints."""
        req = _post(http_server, "/mcp", {
            "jsonrpc": "2.0",
            "id": 99,
            "method": "tools/list",
            "params": {},
        })
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert body["jsonrpc"] == "2.0"
            assert body["id"] == 99
            assert len(body["result"]["tools"]) == 7


# ════════════════════════════════════════════════════════════════
# AUTH ENFORCEMENT TESTS (over HTTP)
# ════════════════════════════════════════════════════════════════

_AUTH_CONFIG = {
    "tokens": [
        {
            "token": "test-http-token",
            "name": "http-tester",
            "scopes": ["hash", "status"],
        },
    ],
    "rate_limit_rpm": 1000,
}


@pytest.fixture(scope="module")
def auth_http_server():
    """Start MCP HTTP server with auth enabled."""
    env = {"MCP_AUTH_TOKENS": json.dumps(_AUTH_CONFIG)}
    with mock.patch.dict(os.environ, env):
        reset_auth_config()
        server = HTTPServer(("127.0.0.1", 0), MCPHttpHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{port}"
        server.shutdown()
        reset_auth_config()


class TestAuthEnforcement:
    """Auth enforcement on plain JSON endpoints."""

    def test_valid_token_passes(self, auth_http_server):
        req = _post(auth_http_server, "/api/v1/tools/echelon_hash", {
            "content": {"mode": "inline", "value": {"x": 1}},
        })
        req.add_header("Authorization", "Bearer test-http-token")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert "hash" in body

    def test_missing_token_rejected(self, auth_http_server):
        req = _post(auth_http_server, "/api/v1/tools/echelon_hash", {
            "content": {"mode": "inline", "value": {"x": 1}},
        })
        # No Authorization header
        try:
            urllib.request.urlopen(req)
            pytest.fail("Expected 401")
        except urllib.error.HTTPError as e:
            assert e.code == 401
            body = json.loads(e.read())
            assert body["error"] == "authentication_required"

    def test_wrong_scope_rejected(self, auth_http_server):
        """Token has hash+status but not calibrate scope."""
        req = _post(auth_http_server, "/api/v1/tools/echelon_calibrate", {
            "construct_id": "test",
        })
        req.add_header("Authorization", "Bearer test-http-token")
        try:
            urllib.request.urlopen(req)
            pytest.fail("Expected 403")
        except urllib.error.HTTPError as e:
            assert e.code == 403
            body = json.loads(e.read())
            assert body["error"] == "insufficient_scope"
            assert body["required_scope"] == "calibrate"

    def test_invalid_token_rejected(self, auth_http_server):
        req = _post(auth_http_server, "/api/v1/tools/echelon_hash", {
            "content": {"mode": "inline", "value": {"x": 1}},
        })
        req.add_header("Authorization", "Bearer wrong-token")
        try:
            urllib.request.urlopen(req)
            pytest.fail("Expected 401")
        except urllib.error.HTTPError as e:
            assert e.code == 401
