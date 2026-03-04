"""HTTP transport for the Echelon Verifier MCP Server.

Wraps the existing dispatch() function behind an HTTP POST endpoint at /mcp.
Also exposes /health, /sse (stub), and plain JSON tool endpoints at
/api/v1/tools/{tool_name}.

Usage:
    python3 -m mcp.server --http             # Start on port 3100
    python3 -m mcp.server --http --port 8080 # Custom port
"""

from __future__ import annotations

import json
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional

from mcp.server import TOOLS, dispatch, jsonrpc_error
from mcp.auth import authenticate, authorize, check_rate_limit

# Regex to match /api/v1/tools/{tool_name}
_TOOLS_PATH_RE = re.compile(r"^/api/v1/tools/([a-zA-Z0-9_]+)$")


class MCPHttpHandler(BaseHTTPRequestHandler):
    """HTTP handler that routes JSON-RPC and plain JSON requests."""

    def do_POST(self) -> None:
        # ── Plain JSON tool endpoint ──
        match = _TOOLS_PATH_RE.match(self.path)
        if match:
            self._handle_plain_json_tool(match.group(1))
            return

        # ── JSON-RPC MCP endpoint ──
        if self.path == "/mcp":
            self._handle_jsonrpc()
            return

        self._send_json(404, {"error": "Not found"})

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {
                "status": "ok",
                "version": "1.0.0",
                "tools": 7,
            })
        elif self.path == "/sse":
            self._send_json(200, {
                "status": "not_implemented",
                "available_from": "v1.3",
            })
        else:
            self._send_json(404, {"error": "Not found"})

    # ═══════════════════════════════════════════════════════════
    # PLAIN JSON TOOL ENDPOINT
    # ═══════════════════════════════════════════════════════════

    def _handle_plain_json_tool(self, tool_name: str) -> None:
        """Handle POST /api/v1/tools/{tool_name} with plain JSON body."""
        # 1. Check tool exists
        if tool_name not in TOOLS:
            self._send_json(404, {
                "error": "tool_not_found",
                "message": f"Unknown tool: {tool_name}. Available: {', '.join(TOOLS.keys())}",
            })
            return

        # 2. Authenticate
        auth_header = self.headers.get("Authorization")
        ok, auth_result = authenticate(auth_header)
        if not ok:
            self._send_json(401, auth_result)
            return

        # 3. Authorize (check scopes)
        tool_scopes = TOOLS[tool_name].get("scopes", [])
        ok, scope_err = authorize(auth_result, tool_scopes)
        if not ok:
            self._send_json(403, scope_err)
            return

        # 4. Rate limit
        token_name = auth_result["name"] if isinstance(auth_result, dict) and "name" in auth_result else None
        ok, rate_err = check_rate_limit(token_name)
        if not ok:
            self._send_json(429, rate_err)
            return

        # 5. Read and parse body
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            # Empty body = empty arguments
            arguments: Dict[str, Any] = {}
        else:
            try:
                content_length = int(raw_length)
            except ValueError:
                self._send_json(400, {"error": "Invalid Content-Length"})
                return
            body = self.rfile.read(content_length)
            try:
                arguments = json.loads(body) if body else {}
            except json.JSONDecodeError as e:
                self._send_json(400, {
                    "error": "invalid_json",
                    "message": f"Failed to parse request body: {e}",
                })
                return

        # 6. Call tool handler directly
        try:
            result = TOOLS[tool_name]["handler"](arguments)
            self._send_json(200, result)
        except Exception as e:
            self._send_json(500, {
                "error": "internal_error",
                "message": str(e),
            })

    # ═══════════════════════════════════════════════════════════
    # JSON-RPC MCP ENDPOINT (preserved for backward compat)
    # ═══════════════════════════════════════════════════════════

    def _handle_jsonrpc(self) -> None:
        """Handle POST /mcp — original JSON-RPC endpoint."""
        # Read Content-Length
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self._send_json(400, {"error": "Missing or invalid Content-Length"})
            return
        try:
            content_length = int(raw_length)
        except ValueError:
            self._send_json(400, {"error": "Missing or invalid Content-Length"})
            return

        body = self.rfile.read(content_length)

        # Parse JSON
        try:
            message = json.loads(body)
        except json.JSONDecodeError as e:
            resp = jsonrpc_error(None, -32700, f"Parse error: {e}")
            self._send_json(200, resp)
            return

        # Dispatch to MCP server
        response = dispatch(message)
        if response is None:
            # Notification — no response body
            self.send_response(204)
            self.end_headers()
            return

        self._send_json(200, response)

    # ═══════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════

    def _send_json(self, status_code: int, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_http(port: int = 3100) -> None:
    """Start the MCP HTTP server on the given port."""
    server = HTTPServer(("", port), MCPHttpHandler)
    print(f"Echelon MCP HTTP server listening on port {port}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
