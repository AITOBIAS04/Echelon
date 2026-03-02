"""Tests for mcp.http — HTTP transport."""

from __future__ import annotations

import json
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer
from typing import Any, Dict

import pytest

from mcp.http import MCPHttpHandler


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
