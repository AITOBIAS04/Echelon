"""Tests for mcp.tools.calibrate — echelon_calibrate tool."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from mcp.tools import calibrate, verify


# ════════════════════════════════════════════════════════════════
# TESTS
# ════════════════════════════════════════════════════════════════

class TestCalibrateTool:
    def test_calibrate_known_construct(self, tmp_path):
        result = calibrate.handle({
            "construct_id": "community_oracle_v1",
            "output_dir": str(tmp_path),
        })

        assert "certificate" in result
        assert isinstance(result["certificate"], dict)
        assert "pipeline_summary" in result
        assert isinstance(result["pipeline_summary"], dict)
        assert "_meta" in result

        summary = result["pipeline_summary"]
        assert summary["construct_id"] == "community_oracle_v1"
        assert isinstance(summary["composite_score"], float)
        assert result["certificate"]["certificate_id"]  # non-empty string

    def test_calibrate_unknown_construct(self):
        result = calibrate.handle({
            "construct_id": "nonexistent_v99",
        })

        assert result["overall_verdict"] == "ERROR"
        assert result["error_code"] == "INPUT_MALFORMED"
        assert "Available" in result["error_message"]

    def test_calibrate_certificate_passes_verify(self, tmp_path):
        cal_result = calibrate.handle({
            "construct_id": "community_oracle_v1",
            "output_dir": str(tmp_path),
        })

        # Certificate was produced
        cert = cal_result["certificate"]
        assert cert is not None

        # Verify it via echelon_verify (inline mode)
        verify_result = verify.handle({
            "certificate": {"mode": "inline", "value": cert},
        })
        assert verify_result["overall_verdict"] != "ERROR"

        # Pipeline summary includes verify verdict
        assert "mcp_verify_verdict" in cal_result["pipeline_summary"]
        assert isinstance(cal_result["pipeline_summary"]["mcp_verify_verdict"], str)

    def test_calibrate_missing_construct_id(self):
        result = calibrate.handle({})

        assert result["overall_verdict"] == "ERROR"
        assert result["error_code"] == "INPUT_MALFORMED"
        assert "construct_id" in result["error_message"]

    def test_calibrate_deterministic(self, tmp_path):
        # Run 1
        r1 = calibrate.handle({
            "construct_id": "community_oracle_v1",
            "output_dir": str(tmp_path / "run1"),
        })

        # Run 2
        r2 = calibrate.handle({
            "construct_id": "community_oracle_v1",
            "output_dir": str(tmp_path / "run2"),
        })

        assert r1["certificate"]["composite_score"] == r2["certificate"]["composite_score"]
        assert r1["certificate"]["certificate_id"] == r2["certificate"]["certificate_id"]

    def test_calibrate_has_meta(self, tmp_path):
        result = calibrate.handle({
            "construct_id": "community_oracle_v1",
            "output_dir": str(tmp_path),
        })

        assert "_meta" in result
        assert "engine_version" in result["_meta"]
        assert "timestamp" in result["_meta"]
