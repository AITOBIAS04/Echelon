"""Tests for mcp.tools.status — echelon_status tool."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from mcp.tools import status


# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

def _write_cert(tmp_path: Path, construct_id: str, cert_dict: Dict[str, Any]) -> Path:
    """Write a certificate JSON file at the expected path."""
    cert_dir = tmp_path / "construct_calibration" / construct_id / "certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)
    template_id = cert_dict.get("template_id", "cert")
    fp = cert_dir / f"{template_id}.json"
    fp.write_text(json.dumps(cert_dict))
    return fp


def _sample_cert(**overrides: Any) -> Dict[str, Any]:
    """Build a sample certificate dict with optional overrides."""
    cert = {
        "certificate_id": "a64c7236-d229-5c6d-acb5-b4f6dfc2cd22",
        "template_id": "CONSTRUCT_CALIBRATION_V1",
        "composite_score": 0.6967,
        "verification_tier": "UNVERIFIED",
        "issued_at": "2026-03-01T00:00:00",
        "replay_count": 12,
        "evidence_bundle_hash": "cabd0288" + "a" * 56,
        "scores": {"precision": 0.8, "recall": 0.5417, "reply_accuracy": 0.8},
    }
    cert.update(overrides)
    return cert


# ════════════════════════════════════════════════════════════════
# TESTS
# ════════════════════════════════════════════════════════════════

class TestStatusTool:
    def test_status_existing_construct(self, tmp_path):
        cert = _sample_cert()
        _write_cert(tmp_path, "community_oracle_v1", cert)

        result = status.handle({
            "construct_id": "community_oracle_v1",
            "output_dir": str(tmp_path),
        })

        assert result["certificates_found"] == 1
        latest = result["latest_certificate"]
        assert latest["certificate_id"] == cert["certificate_id"]
        assert latest["template_id"] == cert["template_id"]
        assert latest["composite_score"] == cert["composite_score"]
        assert latest["verification_tier"] == "UNVERIFIED"
        assert latest["issued_at"] == cert["issued_at"]
        assert latest["replay_count"] == 12
        assert result["tier_summary"]["current_tier"] == "UNVERIFIED"
        assert "_meta" in result

    def test_status_no_certificates(self, tmp_path):
        # Create the directory but leave it empty
        cert_dir = tmp_path / "construct_calibration" / "empty_construct" / "certificates"
        cert_dir.mkdir(parents=True)

        result = status.handle({
            "construct_id": "empty_construct",
            "output_dir": str(tmp_path),
        })

        assert result["certificates_found"] == 0
        assert result["latest_certificate"] is None
        assert result["tier_summary"] is None

    def test_status_missing_output_dir(self, tmp_path):
        result = status.handle({
            "construct_id": "test_construct",
            "output_dir": str(tmp_path / "nonexistent"),
        })

        assert result["certificates_found"] == 0
        assert result["latest_certificate"] is None
        assert result["tier_summary"] is None
        assert "_meta" in result

    def test_status_corrupt_json_skipped(self, tmp_path):
        # Write one valid certificate
        cert = _sample_cert()
        _write_cert(tmp_path, "test_construct", cert)

        # Write a corrupt file
        cert_dir = tmp_path / "construct_calibration" / "test_construct" / "certificates"
        (cert_dir / "corrupt.json").write_text("not valid json {{{")

        result = status.handle({
            "construct_id": "test_construct",
            "output_dir": str(tmp_path),
        })

        assert result["certificates_found"] == 1
        assert result["latest_certificate"]["certificate_id"] == cert["certificate_id"]

    def test_status_missing_construct_id(self):
        result = status.handle({})
        assert result["overall_verdict"] == "ERROR"
        assert result["error_code"] == "INPUT_MALFORMED"

    def test_status_multiple_certificates_returns_latest(self, tmp_path):
        # Write two certificates with different timestamps
        cert_dir = tmp_path / "construct_calibration" / "test_construct" / "certificates"
        cert_dir.mkdir(parents=True)

        older = _sample_cert(
            certificate_id="cert-older",
            template_id="CERT_OLDER",
            issued_at="2026-03-01T00:00:00",
        )
        newer = _sample_cert(
            certificate_id="cert-newer",
            template_id="CERT_NEWER",
            issued_at="2026-03-02T00:00:00",
        )

        (cert_dir / "older.json").write_text(json.dumps(older))
        (cert_dir / "newer.json").write_text(json.dumps(newer))

        result = status.handle({
            "construct_id": "test_construct",
            "output_dir": str(tmp_path),
        })

        assert result["certificates_found"] == 2
        assert result["latest_certificate"]["issued_at"] == "2026-03-02T00:00:00"
        assert result["latest_certificate"]["certificate_id"] == "cert-newer"

    def test_status_replays_needed_calculation(self, tmp_path):
        # 12 replays -> need 38 more
        cert_12 = _sample_cert(replay_count=12)
        _write_cert(tmp_path, "construct_12", cert_12)

        result = status.handle({
            "construct_id": "construct_12",
            "output_dir": str(tmp_path),
        })
        assert result["tier_summary"]["replays_needed"] == 38

        # 60 replays -> need 0 more
        cert_60 = _sample_cert(replay_count=60, template_id="CERT_60")
        _write_cert(tmp_path, "construct_60", cert_60)

        result = status.handle({
            "construct_id": "construct_60",
            "output_dir": str(tmp_path),
        })
        assert result["tier_summary"]["replays_needed"] == 0

    def test_status_has_meta(self, tmp_path):
        cert = _sample_cert()
        _write_cert(tmp_path, "test_meta", cert)

        result = status.handle({
            "construct_id": "test_meta",
            "output_dir": str(tmp_path),
        })

        assert "_meta" in result
        assert "engine_version" in result["_meta"]
        assert "timestamp" in result["_meta"]
