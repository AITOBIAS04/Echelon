"""Tests for mcp.auth — bearer token validation, scope enforcement, rate limiting."""

from __future__ import annotations

import json
import os
import time
from unittest import mock

import pytest

from mcp.auth import (
    authenticate,
    authorize,
    check_rate_limit,
    load_auth_config,
    reset_auth_config,
    _rate_limit_windows,
)


# ════════════════════════════════════════════════════════════════
# FIXTURES
# ════════════════════════════════════════════════════════════════

_TEST_CONFIG = {
    "tokens": [
        {
            "token": "valid-token-abc",
            "name": "test-consumer",
            "scopes": ["verify", "inspect", "hash", "schema_check", "replay", "status"],
        },
        {
            "token": "admin-token-xyz",
            "name": "test-admin",
            "scopes": ["verify", "inspect", "hash", "schema_check", "replay", "status", "calibrate"],
        },
    ],
    "rate_limit_rpm": 60,
}


@pytest.fixture(autouse=True)
def _reset_auth():
    """Reset auth config before and after each test."""
    reset_auth_config()
    yield
    reset_auth_config()


@pytest.fixture
def auth_env():
    """Set MCP_AUTH_TOKENS env var with test config."""
    with mock.patch.dict(os.environ, {"MCP_AUTH_TOKENS": json.dumps(_TEST_CONFIG)}):
        reset_auth_config()
        yield


# ════════════════════════════════════════════════════════════════
# AUTHENTICATION TESTS
# ════════════════════════════════════════════════════════════════

class TestAuthenticate:
    def test_valid_token_passes(self, auth_env):
        ok, info = authenticate("Bearer valid-token-abc")
        assert ok is True
        assert info["name"] == "test-consumer"
        assert "verify" in info["scopes"]

    def test_valid_admin_token(self, auth_env):
        ok, info = authenticate("Bearer admin-token-xyz")
        assert ok is True
        assert info["name"] == "test-admin"
        assert "calibrate" in info["scopes"]

    def test_missing_header_rejected(self, auth_env):
        ok, err = authenticate(None)
        assert ok is False
        assert err["error"] == "authentication_required"

    def test_empty_header_rejected(self, auth_env):
        ok, err = authenticate("")
        assert ok is False
        assert err["error"] == "authentication_required"

    def test_invalid_token_rejected(self, auth_env):
        ok, err = authenticate("Bearer wrong-token-999")
        assert ok is False
        assert err["error"] == "authentication_failed"

    def test_malformed_header_rejected(self, auth_env):
        ok, err = authenticate("Basic abc123")
        assert ok is False
        assert err["error"] == "authentication_required"

    def test_no_bearer_prefix_rejected(self, auth_env):
        ok, err = authenticate("valid-token-abc")
        assert ok is False
        assert err["error"] == "authentication_required"

    def test_dev_mode_passthrough(self):
        """Without MCP_AUTH_TOKENS, auth is disabled (dev mode)."""
        ok, info = authenticate(None)
        assert ok is True
        assert info is None

    def test_dev_mode_any_header(self):
        """In dev mode, any header passes."""
        ok, info = authenticate("Bearer anything")
        assert ok is True
        assert info is None


# ════════════════════════════════════════════════════════════════
# AUTHORIZATION (SCOPE) TESTS
# ════════════════════════════════════════════════════════════════

class TestAuthorize:
    def test_correct_scope_passes(self, auth_env):
        ok, _ = authenticate("Bearer valid-token-abc")
        assert ok
        token_info = _
        ok, err = authorize(token_info, ["verify"])
        assert ok is True
        assert err is None

    def test_multiple_scopes_pass(self, auth_env):
        ok, token_info = authenticate("Bearer valid-token-abc")
        ok, err = authorize(token_info, ["verify", "status"])
        assert ok is True

    def test_missing_scope_rejected(self, auth_env):
        ok, token_info = authenticate("Bearer valid-token-abc")
        ok, err = authorize(token_info, ["calibrate"])
        assert ok is False
        assert err["error"] == "insufficient_scope"
        assert err["required_scope"] == "calibrate"

    def test_admin_has_calibrate_scope(self, auth_env):
        ok, token_info = authenticate("Bearer admin-token-xyz")
        ok, err = authorize(token_info, ["calibrate"])
        assert ok is True

    def test_dev_mode_allows_all_scopes(self):
        """In dev mode (token_info=None), all scopes allowed."""
        ok, err = authorize(None, ["calibrate", "verify", "anything"])
        assert ok is True
        assert err is None


# ════════════════════════════════════════════════════════════════
# RATE LIMITING TESTS
# ════════════════════════════════════════════════════════════════

class TestRateLimit:
    def test_under_limit_allowed(self):
        ok, err = check_rate_limit("test-user", max_rpm=10)
        assert ok is True
        assert err is None

    def test_over_limit_rejected(self):
        for _ in range(5):
            check_rate_limit("rate-test-user", max_rpm=5)

        ok, err = check_rate_limit("rate-test-user", max_rpm=5)
        assert ok is False
        assert err["error"] == "rate_limit_exceeded"
        assert "retry_after_seconds" in err
        assert err["retry_after_seconds"] >= 1

    def test_different_tokens_independent(self):
        for _ in range(5):
            check_rate_limit("user-a", max_rpm=5)

        # user-a is at limit
        ok, _ = check_rate_limit("user-a", max_rpm=5)
        assert ok is False

        # user-b should still be fine
        ok, _ = check_rate_limit("user-b", max_rpm=5)
        assert ok is True

    def test_dev_mode_no_rate_limit(self):
        """In dev mode (token_name=None), no rate limiting."""
        for _ in range(100):
            ok, err = check_rate_limit(None, max_rpm=1)
            assert ok is True

    def test_window_expires(self):
        """Old timestamps are purged from the sliding window."""
        # Fill the window
        for _ in range(5):
            check_rate_limit("expiry-test", max_rpm=5)

        # Manually age all timestamps to > 60s ago
        window = _rate_limit_windows["expiry-test"]
        old_time = time.time() - 61.0
        window.clear()
        for _ in range(5):
            window.append(old_time)

        # Now a new request should succeed (old ones purged)
        ok, err = check_rate_limit("expiry-test", max_rpm=5)
        assert ok is True


# ════════════════════════════════════════════════════════════════
# CONFIG LOADING TESTS
# ════════════════════════════════════════════════════════════════

class TestLoadConfig:
    def test_no_env_returns_none(self):
        config = load_auth_config()
        assert config is None

    def test_valid_env_parsed(self, auth_env):
        config = load_auth_config()
        assert config is not None
        assert "_token_map" in config
        assert "valid-token-abc" in config["_token_map"]

    def test_invalid_json_returns_none(self):
        with mock.patch.dict(os.environ, {"MCP_AUTH_TOKENS": "not json"}):
            reset_auth_config()
            config = load_auth_config()
            assert config is None

    def test_config_cached(self, auth_env):
        c1 = load_auth_config()
        c2 = load_auth_config()
        assert c1 is c2
