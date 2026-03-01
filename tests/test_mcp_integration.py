"""MCP integration tests — end-to-end certificate generation and verification."""

from __future__ import annotations

import asyncio
import copy
import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _run_async(coro):
    """Run async function synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestEndToEndVerification:
    """Generate certificate via pipeline, verify via MCP."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from scripts.run_construct_calibration import run_construct_calibration
        self._run = run_construct_calibration

    def test_generated_certificate_passes_verification(self):
        from mcp.tools import verify as mcp_verify

        _, cert_dict = _run_async(self._run("community_oracle_v1", Path("output")))

        result = mcp_verify.handle({
            "certificate": {"mode": "inline", "value": cert_dict},
        })

        assert result["overall_verdict"] == "PASS"

    def test_tampered_certificate_fails_verification(self):
        from mcp.tools import verify as mcp_verify

        _, cert_dict = _run_async(self._run("community_oracle_v1", Path("output")))

        tampered = copy.deepcopy(cert_dict)
        tampered["composite_score"] = 0.99  # tamper

        result = mcp_verify.handle({
            "certificate": {"mode": "inline", "value": tampered},
        })

        assert result["overall_verdict"] == "FAIL"
        fail_ids = [c["check_id"] for c in result["checks"] if c["verdict"] == "FAIL"]
        assert len(fail_ids) > 0  # tampered composite detected

    def test_deterministic_evidence_bundle_hash(self):
        _, c1 = _run_async(self._run("community_oracle_v1", Path("output")))
        _, c2 = _run_async(self._run("community_oracle_v1", Path("output")))

        assert c1["evidence_bundle_hash"] == c2["evidence_bundle_hash"]
        assert c1["composite_score"] == c2["composite_score"]
        assert c1["scores"] == c2["scores"]

    def test_certificate_has_required_fields(self):
        _, cert_dict = _run_async(self._run("community_oracle_v1", Path("output")))

        required = {
            "certificate_id", "theatre_id", "template_id", "construct_id",
            "criteria", "scores", "composite_score", "replay_count",
            "evidence_bundle_hash", "commitment_hash", "issued_at",
            "verification_tier", "execution_path",
        }
        assert required.issubset(set(cert_dict.keys()))
