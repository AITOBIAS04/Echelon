"""Tests for mcp.models — meta, errors, inputs."""

from __future__ import annotations

import pytest

from mcp.models.meta import ENGINE_VERSION, SCHEMA_VERSIONS, build_meta
from mcp.models.errors import ERROR_CODES, error_response
from mcp.models.inputs import SUPPORTED_MODES, parse_input


# ────────────────────────────────────────────────
# build_meta
# ────────────────────────────────────────────────

class TestBuildMeta:
    def test_meta_has_required_keys(self):
        meta = build_meta()
        assert "engine_version" in meta
        assert "schema_versions" in meta
        assert "timestamp" in meta

    def test_engine_version_matches(self):
        meta = build_meta()
        assert meta["engine_version"] == ENGINE_VERSION

    def test_schema_versions_is_dict(self):
        meta = build_meta()
        sv = meta["schema_versions"]
        assert isinstance(sv, dict)
        assert "certificate" in sv

    def test_resolved_inputs_included_when_provided(self):
        ri = [{"mode": "inline", "param": "certificate"}]
        meta = build_meta(resolved_inputs=ri)
        assert meta["resolved_inputs"] is ri

    def test_resolved_inputs_excluded_when_none(self):
        meta = build_meta()
        assert "resolved_inputs" not in meta


# ────────────────────────────────────────────────
# error_response
# ────────────────────────────────────────────────

class TestErrorResponse:
    def test_error_has_verdict_and_code(self):
        resp = error_response("INPUT_MALFORMED", "bad input")
        assert resp["overall_verdict"] == "ERROR"
        assert resp["error_code"] == "INPUT_MALFORMED"
        assert resp["error_message"] == "bad input"
        assert "_meta" in resp

    def test_unknown_code_falls_back_to_internal(self):
        resp = error_response("NONEXISTENT_CODE", "oops")
        assert resp["error_code"] == "INTERNAL_ERROR"

    def test_all_committed_codes_are_known(self):
        for code in ERROR_CODES:
            resp = error_response(code, "test")
            assert resp["error_code"] == code


# ────────────────────────────────────────────────
# parse_input
# ────────────────────────────────────────────────

class TestParseInput:
    def test_inline_mode_returns_value(self):
        result = parse_input({"mode": "inline", "value": {"key": 1}}, "test")
        assert result == {"key": 1}

    def test_missing_mode_raises(self):
        with pytest.raises(ValueError, match="missing 'mode'"):
            parse_input({"value": "x"}, "cert")

    def test_unsupported_mode_raises(self):
        with pytest.raises(ValueError, match="unsupported mode 'id'"):
            parse_input({"mode": "id", "value": "abc"}, "cert")

    def test_missing_value_raises(self):
        with pytest.raises(ValueError, match="missing 'value'"):
            parse_input({"mode": "inline"}, "cert")

    def test_non_dict_input_raises(self):
        with pytest.raises(ValueError, match="expected object"):
            parse_input("not a dict", "cert")

    def test_inline_string_value(self):
        result = parse_input({"mode": "inline", "value": "hello"}, "content")
        assert result == "hello"
