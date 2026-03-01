"""Tests for mcp.tools — verify, inspect, hash, schema_check, replay."""

from __future__ import annotations

import copy
import json
from typing import Any, Dict

import pytest

from mcp.tools import verify, inspect, hash, schema_check


# ════════════════════════════════════════════════════════════════
# SHARED FIXTURES
# ════════════════════════════════════════════════════════════════

def _minimal_cert() -> Dict[str, Any]:
    """Build a minimal valid certificate for testing."""
    return {
        "certificate_id": "test-0001-0001-0001-000000000001",
        "theatre_id": "test_theatre_v1",
        "template_id": "test_template_v1",
        "construct_id": "test_construct",
        "criteria": {
            "criteria_ids": ["accuracy", "coverage"],
            "criteria_human": ["Accuracy", "Coverage"],
            "weights": {"accuracy": 0.6, "coverage": 0.4},
        },
        "scores": {
            "accuracy": 0.9,
            "coverage": 0.8,
        },
        "composite_score": 0.86,  # 0.6*0.9 + 0.4*0.8 = 0.54 + 0.32
        "replay_count": 10,
        "evidence_bundle_hash": "a" * 64,
        "commitment_hash": "b" * 64,
        "issued_at": "2026-03-01T12:00:00Z",
        "verification_tier": "UNVERIFIED",
        "execution_path": "replay",
    }


def _wrap_inline(value: Any) -> Dict[str, Any]:
    """Wrap a value in inline mode object."""
    return {"mode": "inline", "value": value}


# ════════════════════════════════════════════════════════════════
# echelon_verify
# ════════════════════════════════════════════════════════════════

class TestVerifyTool:
    def test_valid_cert_returns_checks(self):
        result = verify.handle({"certificate": _wrap_inline(_minimal_cert())})
        assert "overall_verdict" in result
        assert "checks" in result
        assert isinstance(result["checks"], list)
        assert len(result["checks"]) > 0
        assert "_meta" in result

    def test_missing_cert_returns_error(self):
        result = verify.handle({})
        assert result["overall_verdict"] == "ERROR"
        assert result["error_code"] == "INPUT_MALFORMED"

    def test_invalid_mode_returns_error(self):
        result = verify.handle({"certificate": {"mode": "id", "value": "x"}})
        assert result["overall_verdict"] == "ERROR"

    def test_check_structure(self):
        result = verify.handle({"certificate": _wrap_inline(_minimal_cert())})
        for check in result["checks"]:
            assert "check_id" in check
            assert "title" in check
            assert "verdict" in check
            assert check["verdict"] in ("PASS", "FAIL", "WARN", "SKIP")

    def test_summary_counts(self):
        result = verify.handle({"certificate": _wrap_inline(_minimal_cert())})
        summary = result["summary"]
        assert summary["total"] == len(result["checks"])
        # SKIP verdicts exist but aren't counted in pass/fail/warnings
        skipped = sum(1 for c in result["checks"] if c["verdict"] == "SKIP")
        assert summary["total"] == summary["passed"] + summary["failed"] + summary["warnings"] + skipped

    def test_nonexistent_evidence_path_returns_error(self):
        result = verify.handle({
            "certificate": _wrap_inline(_minimal_cert()),
            "evidence_bundle_path": "/nonexistent/path/12345",
        })
        assert result["overall_verdict"] == "ERROR"
        assert "not found" in result["error_message"]


# ════════════════════════════════════════════════════════════════
# echelon_inspect
# ════════════════════════════════════════════════════════════════

class TestInspectTool:
    def test_inspect_returns_summary(self):
        result = inspect.handle({"certificate": _wrap_inline(_minimal_cert())})
        assert "summary" in result
        assert "_meta" in result
        summary = result["summary"]
        assert summary["certificate_id"] == "test-0001-0001-0001-000000000001"
        assert summary["theatre_id"] == "test_theatre_v1"
        assert summary["composite_score"] == 0.86

    def test_inspect_includes_scores(self):
        result = inspect.handle({"certificate": _wrap_inline(_minimal_cert())})
        assert "scores" in result["summary"]
        assert result["summary"]["scores"]["accuracy"] == 0.9

    def test_inspect_includes_criteria(self):
        result = inspect.handle({"certificate": _wrap_inline(_minimal_cert())})
        assert "criteria" in result["summary"]

    def test_inspect_missing_cert_returns_error(self):
        result = inspect.handle({})
        assert result["overall_verdict"] == "ERROR"


# ════════════════════════════════════════════════════════════════
# echelon_hash
# ════════════════════════════════════════════════════════════════

class TestHashTool:
    def test_hash_json_object(self):
        obj = {"key": "value", "num": 42}
        result = hash.handle({"content": _wrap_inline(obj)})
        assert "hash" in result
        assert result["hash"].startswith("sha256:")
        assert len(result["hash"]) == 7 + 64  # "sha256:" + 64 hex chars

    def test_hash_string(self):
        result = hash.handle({"content": _wrap_inline("hello world")})
        assert result["hash"].startswith("sha256:")

    def test_hash_deterministic(self):
        obj = {"b": 2, "a": 1}
        r1 = hash.handle({"content": _wrap_inline(obj)})
        r2 = hash.handle({"content": _wrap_inline(obj)})
        assert r1["hash"] == r2["hash"]

    def test_hash_canonical_key_order(self):
        """Keys sorted canonically — {b,a} should hash same as {a,b}."""
        r1 = hash.handle({"content": _wrap_inline({"b": 2, "a": 1})})
        r2 = hash.handle({"content": _wrap_inline({"a": 1, "b": 2})})
        assert r1["hash"] == r2["hash"]

    def test_hash_missing_content_returns_error(self):
        result = hash.handle({})
        assert result["overall_verdict"] == "ERROR"

    def test_hash_has_meta(self):
        result = hash.handle({"content": _wrap_inline({"x": 1})})
        assert "_meta" in result


# ════════════════════════════════════════════════════════════════
# echelon_schema_check
# ════════════════════════════════════════════════════════════════

class TestSchemaCheckTool:
    def test_valid_cert_passes(self):
        result = schema_check.handle({"certificate": _wrap_inline(_minimal_cert())})
        assert "valid" in result
        assert "checks_run" in result
        assert result["checks_run"] > 0

    def test_missing_fields_detected(self):
        bad_cert = {"certificate_id": "test", "theatre_id": "test"}
        result = schema_check.handle({"certificate": _wrap_inline(bad_cert)})
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        # Should flag missing required fields
        error_ids = [e["check_id"] for e in result["errors"]]
        assert "SCHEMA-001" in error_ids

    def test_invalid_tier_detected(self):
        cert = _minimal_cert()
        cert["verification_tier"] = "BOGUS"
        result = schema_check.handle({"certificate": _wrap_inline(cert)})
        assert result["valid"] is False
        error_ids = [e["check_id"] for e in result["errors"]]
        assert "SCHEMA-002" in error_ids

    def test_missing_cert_returns_error(self):
        result = schema_check.handle({})
        assert result["overall_verdict"] == "ERROR"
