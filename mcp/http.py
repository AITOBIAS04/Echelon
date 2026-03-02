"""HTTP transport for the Echelon Verifier MCP Server.

Wraps the existing dispatch() function behind an HTTP POST endpoint at /mcp.
Also exposes /health and /sse (stub) endpoints.

Usage:
    python3 -m mcp.server --http             # Start on port 3100
    python3 -m mcp.server --http --port 8080 # Custom port
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict

from mcp.server import dispatch, jsonrpc_error


class MCPHttpHandler(BaseHTTPRequestHandler):
    """HTTP handler that routes JSON-RPC requests to the MCP dispatch layer."""

    def do_POST(self) -> None:
        if self.path != "/mcp":
            self._send_json(404, {"error": "Not found"})
            return

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
