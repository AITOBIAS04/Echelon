#!/usr/bin/env python3
"""
Echelon Verifier MCP Server — stdio and HTTP transport.

Implements MCP protocol (JSON-RPC 2.0) over stdin/stdout or HTTP.
Seven verification and calibration tools, no external SDK dependency, Python 3.9+.

Usage:
    python3 -m mcp.server                    # Start stdio server
    python3 -m mcp.server --http             # Start HTTP server on port 3100
    python3 -m mcp.server --http --port 8080 # Start HTTP server on custom port
    python3 -m mcp.server --list-tools       # Print tool definitions
    python3 -m mcp.server --call <tool> '{"arg": "val"}'  # One-shot call
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

from mcp.tools import verify, inspect, hash, schema_check, replay, status, calibrate


# ════════════════════════════════════════════════════════════════
# TOOL REGISTRY
# ════════════════════════════════════════════════════════════════

TOOLS = {
    "echelon_verify": {
        "definition": verify.TOOL_DEFINITION,
        "handler": verify.handle,
    },
    "echelon_inspect": {
        "definition": inspect.TOOL_DEFINITION,
        "handler": inspect.handle,
    },
    "echelon_hash": {
        "definition": hash.TOOL_DEFINITION,
        "handler": hash.handle,
    },
    "echelon_schema_check": {
        "definition": schema_check.TOOL_DEFINITION,
        "handler": schema_check.handle,
    },
    "echelon_replay": {
        "definition": replay.TOOL_DEFINITION,
        "handler": replay.handle,
    },
    "echelon_status": {
        "definition": status.TOOL_DEFINITION,
        "handler": status.handle,
    },
    "echelon_calibrate": {
        "definition": calibrate.TOOL_DEFINITION,
        "handler": calibrate.handle,
    },
}


# ════════════════════════════════════════════════════════════════
# JSON-RPC HELPERS
# ════════════════════════════════════════════════════════════════

def jsonrpc_response(id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id, "result": result}


def jsonrpc_error(id: Any, code: int, message: str) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": id,
        "error": {"code": code, "message": message},
    }


# ════════════════════════════════════════════════════════════════
# MCP PROTOCOL HANDLERS
# ════════════════════════════════════════════════════════════════

def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialize request."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {"listChanged": False},
        },
        "serverInfo": {
            "name": "echelon-verifier",
            "version": "1.0.0",
        },
    }


def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/list request — return all tool definitions."""
    return {
        "tools": [t["definition"] for t in TOOLS.values()],
    }


def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request — dispatch to tool handler."""
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    if tool_name not in TOOLS:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "overall_verdict": "ERROR",
                        "error_code": "INPUT_MALFORMED",
                        "error_message": f"Unknown tool: {tool_name}. "
                        f"Available: {', '.join(TOOLS.keys())}",
                    }),
                }
            ],
            "isError": True,
        }

    try:
        result = TOOLS[tool_name]["handler"](arguments)
        return {
            "content": [
                {"type": "text", "text": json.dumps(result)},
            ],
            "isError": False,
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "overall_verdict": "ERROR",
                        "error_code": "INTERNAL_ERROR",
                        "error_message": str(e),
                    }),
                }
            ],
            "isError": True,
        }


# Method dispatch table
METHOD_HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
}

# Notifications (no response expected)
NOTIFICATIONS = {"notifications/initialized", "notifications/cancelled"}


def dispatch(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Dispatch a JSON-RPC message and return a response (or None for notifications)."""
    method = message.get("method", "")
    msg_id = message.get("id")
    params = message.get("params", {})

    # Notifications don't get responses
    if method in NOTIFICATIONS:
        return None

    handler = METHOD_HANDLERS.get(method)
    if handler is None:
        if msg_id is not None:
            return jsonrpc_error(msg_id, -32601, f"Method not found: {method}")
        return None

    try:
        result = handler(params)
        return jsonrpc_response(msg_id, result)
    except Exception as e:
        return jsonrpc_error(msg_id, -32603, f"Internal error: {e}")


# ════════════════════════════════════════════════════════════════
# STDIO TRANSPORT
# ════════════════════════════════════════════════════════════════

def run_stdio():
    """Run the MCP server over stdio (stdin/stdout)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            resp = jsonrpc_error(None, -32700, f"Parse error: {e}")
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
            continue

        response = dispatch(message)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


# ════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ════════════════════════════════════════════════════════════════

def call_tool(tool_name: str, arguments_json: str) -> int:
    """One-shot tool call from command line."""
    if tool_name not in TOOLS:
        print(f"Unknown tool: {tool_name}", file=sys.stderr)
        print(f"Available: {', '.join(TOOLS.keys())}", file=sys.stderr)
        return 2

    try:
        arguments = json.loads(arguments_json)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON arguments: {e}", file=sys.stderr)
        return 2

    result = TOOLS[tool_name]["handler"](arguments)
    print(json.dumps(result, indent=2))

    verdict = result.get("overall_verdict", "")
    if verdict == "ERROR":
        return 2
    if verdict == "FAIL":
        return 1
    return 0


def main() -> int:
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list-tools":
            tools = [t["definition"] for t in TOOLS.values()]
            print(json.dumps(tools, indent=2))
            return 0
        elif sys.argv[1] == "--call" and len(sys.argv) >= 4:
            return call_tool(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == "--call" and len(sys.argv) == 3:
            return call_tool(sys.argv[2], "{}")
        elif sys.argv[1] == "--http":
            port = 3100
            if "--port" in sys.argv:
                port_idx = sys.argv.index("--port")
                if port_idx + 1 < len(sys.argv):
                    try:
                        port = int(sys.argv[port_idx + 1])
                    except ValueError:
                        print(f"Invalid port: {sys.argv[port_idx + 1]}", file=sys.stderr)
                        return 2
                else:
                    print("--port requires a value", file=sys.stderr)
                    return 2
            from mcp.http import run_http
            run_http(port)
            return 0
        elif sys.argv[1] == "--help":
            print(__doc__)
            return 0
        else:
            print(f"Unknown argument: {sys.argv[1]}", file=sys.stderr)
            print("Usage: python3 -m mcp.server [--list-tools | --call <tool> '<json>' | --http [--port N]]", file=sys.stderr)
            return 2

    # Default: run stdio server
    run_stdio()
    return 0


if __name__ == "__main__":
    sys.exit(main())
