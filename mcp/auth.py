"""MCP Auth Layer — bearer token validation, scope enforcement, rate limiting.

Provides authentication and authorization for the MCP HTTP transport.
Stdio transport bypasses auth (local trust). Auth is disabled when
the MCP_AUTH_TOKENS environment variable is not set (development mode).

Configuration via environment variable:
    MCP_AUTH_TOKENS='{"tokens": [{"token": "abc", "name": "consumer-1",
        "scopes": ["verify", "status"]}], "rate_limit_rpm": 60}'
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Tuple


# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════

_DEFAULT_RATE_LIMIT_RPM = 60

# In-memory rate limit state: {token_name: deque of timestamps}
_rate_limit_windows: Dict[str, deque] = defaultdict(deque)

# Cached config (loaded once)
_auth_config: Optional[Dict[str, Any]] = None
_auth_config_loaded = False


def load_auth_config() -> Optional[Dict[str, Any]]:
    """Load auth config from MCP_AUTH_TOKENS env var.

    Returns parsed config dict or None if env var is not set (dev mode).
    Config shape:
        {
            "tokens": [
                {"token": "abc123", "name": "consumer-1", "scopes": ["verify", "status"]},
                ...
            ],
            "rate_limit_rpm": 60
        }
    """
    global _auth_config, _auth_config_loaded

    if _auth_config_loaded:
        return _auth_config

    raw = os.environ.get("MCP_AUTH_TOKENS")
    if raw is None:
        _auth_config = None
        _auth_config_loaded = True
        return None

    try:
        config = json.loads(raw)
    except json.JSONDecodeError:
        _auth_config = None
        _auth_config_loaded = True
        return None

    # Build lookup table: token_string -> {name, scopes}
    token_map: Dict[str, Dict[str, Any]] = {}
    for entry in config.get("tokens", []):
        token_str = entry.get("token", "")
        if token_str:
            token_map[token_str] = {
                "name": entry.get("name", "unknown"),
                "scopes": entry.get("scopes", []),
            }

    config["_token_map"] = token_map
    _auth_config = config
    _auth_config_loaded = True
    return _auth_config


def reset_auth_config() -> None:
    """Reset cached config. Used by tests."""
    global _auth_config, _auth_config_loaded
    _auth_config = None
    _auth_config_loaded = False
    _rate_limit_windows.clear()


# ════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ════════════════════════════════════════════════════════════════

def authenticate(auth_header: Optional[str]) -> Tuple[bool, Any]:
    """Validate bearer token from Authorization header.

    Returns:
        (True, token_info_dict) on success
        (False, error_dict) on failure

    When auth is disabled (no config), returns (True, None) — passthrough.
    """
    config = load_auth_config()

    # Dev mode: auth disabled
    if config is None:
        return True, None

    if auth_header is None or not auth_header.strip():
        return False, {
            "error": "authentication_required",
            "message": "Missing or invalid Authorization header. Expected: Bearer <token>",
        }

    # Parse "Bearer <token>"
    parts = auth_header.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False, {
            "error": "authentication_required",
            "message": "Invalid Authorization header format. Expected: Bearer <token>",
        }

    token_str = parts[1]
    token_map = config.get("_token_map", {})

    if token_str not in token_map:
        return False, {
            "error": "authentication_failed",
            "message": "Invalid bearer token",
        }

    return True, token_map[token_str]


# ════════════════════════════════════════════════════════════════
# AUTHORIZATION (SCOPE CHECK)
# ════════════════════════════════════════════════════════════════

def authorize(token_info: Optional[Dict[str, Any]], required_scopes: List[str]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Check that token's scopes include all required scopes.

    Args:
        token_info: Token info from authenticate(), or None in dev mode.
        required_scopes: Scopes required by the tool.

    Returns:
        (True, None) on success
        (False, error_dict) on failure
    """
    # Dev mode: no token info, allow everything
    if token_info is None:
        return True, None

    token_scopes = set(token_info.get("scopes", []))

    for scope in required_scopes:
        if scope not in token_scopes:
            return False, {
                "error": "insufficient_scope",
                "message": f"Token lacks required scope: {scope}",
                "required_scope": scope,
            }

    return True, None


# ════════════════════════════════════════════════════════════════
# RATE LIMITING
# ════════════════════════════════════════════════════════════════

def check_rate_limit(token_name: Optional[str], max_rpm: Optional[int] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Sliding window rate limit check (per-token, per-minute).

    Args:
        token_name: Token identifier. None in dev mode (no rate limit).
        max_rpm: Max requests per minute. None uses config or default.

    Returns:
        (True, None) if allowed
        (False, error_dict) if rate limit exceeded
    """
    # Dev mode: no rate limiting
    if token_name is None:
        return True, None

    config = load_auth_config()

    if max_rpm is None:
        max_rpm = (config or {}).get("rate_limit_rpm", _DEFAULT_RATE_LIMIT_RPM)

    now = time.time()
    window = _rate_limit_windows[token_name]

    # Purge timestamps older than 60 seconds
    cutoff = now - 60.0
    while window and window[0] < cutoff:
        window.popleft()

    if len(window) >= max_rpm:
        # Calculate retry-after from oldest entry in window
        retry_after = int(window[0] + 60.0 - now) + 1
        return False, {
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded. Max {max_rpm} requests/minute.",
            "retry_after_seconds": max(1, retry_after),
        }

    # Record this request
    window.append(now)
    return True, None
