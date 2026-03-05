"""Tests for investigation API routes — 8 tests covering all 11 endpoints."""

from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient

from backend.main import app

# Reset in-memory store between tests
from backend.api.investigation_routes import _investigations


@pytest.fixture(autouse=True)
def _clear_investigations():
    """Clear in-memory investigation store before each test."""
    _investigations.clear()
    yield
    _investigations.clear()


@pytest.fixture
def client():
    return TestClient(app)


def _create_investigation(client: TestClient, **overrides) -> dict:
    """Helper: create an investigation and return response data."""
    payload = {
        "theatre_id": "TH_TEST",
        "construct_id": "CON_TEST",
        "inquiry_class": "INVESTIGATIVE",
        "domain_filters": [],
        "stop_condition": "OUTCOME_RESOLUTION",
        "stop_config": {},
    }
    payload.update(overrides)
    resp = client.post("/api/v1/investigations/", json=payload)
    assert resp.status_code == 201
    return resp.json()


def _submit_evidence(client: TestClient, investigation_id: str, text: str = "test evidence") -> dict:
    """Helper: submit evidence to an investigation."""
    payload = {
        "content_base64": base64.b64encode(text.encode()).decode(),
        "provenance_class": "public_primary",
        "content_type": "text/plain",
        "source_description": "test source",
        "references": [],
    }
    resp = client.post(f"/api/v1/investigations/{investigation_id}/evidence", json=payload)
    assert resp.status_code == 201
    return resp.json()


def _register_claim(client: TestClient, investigation_id: str, evidence_refs: list[str] | None = None) -> dict:
    """Helper: register a claim in the investigation."""
    payload = {
        "claim_text": "Test claim statement",
        "claim_type": "fact",
        "evidence_refs": evidence_refs or [],
    }
    resp = client.post(f"/api/v1/investigations/{investigation_id}/claims", json=payload)
    assert resp.status_code == 201
    return resp.json()


class TestInvestigationRoutes:
    """Tests for investigation REST endpoints."""

    def test_create_investigation(self, client: TestClient) -> None:
        """POST / creates investigation and returns summary."""
        data = _create_investigation(client, theatre_id="TH_CREATE", construct_id="CON_CREATE")

        assert data["id"].startswith("INV-")
        assert data["theatre_id"] == "TH_CREATE"
        assert data["construct_id"] == "CON_CREATE"
        assert data["inquiry_class"] == "INVESTIGATIVE"
        assert data["status"] == "active"
        assert data["evidence_count"] == 0
        assert data["claim_count"] == 0
        assert data["counter_signal_count"] == 0
        assert data["drift_event_count"] == 0

    def test_list_investigations(self, client: TestClient) -> None:
        """GET / returns list of all active investigations."""
        # Empty list initially
        resp = client.get("/api/v1/investigations/")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["investigations"] == []

        # Create two investigations
        _create_investigation(client, theatre_id="TH_A")
        _create_investigation(client, theatre_id="TH_B")

        resp = client.get("/api/v1/investigations/")
        data = resp.json()
        assert data["total"] == 2
        assert len(data["investigations"]) == 2
        theatre_ids = {inv["theatre_id"] for inv in data["investigations"]}
        assert theatre_ids == {"TH_A", "TH_B"}

    def test_get_investigation_detail(self, client: TestClient) -> None:
        """GET /{id} returns full investigation detail with sub-components."""
        summary = _create_investigation(client)
        inv_id = summary["id"]

        resp = client.get(f"/api/v1/investigations/{inv_id}")
        assert resp.status_code == 200
        data = resp.json()

        assert data["id"] == inv_id
        assert data["theatre_id"] == "TH_TEST"
        assert data["status"] == "active"
        assert data["stop_condition"] == "OUTCOME_RESOLUTION"
        # Sub-components present
        assert "evidence" in data
        assert "claims" in data
        assert "counter_signals" in data
        assert "drift" in data
        assert data["evidence"]["items"] == []
        assert data["claims"]["claims"] == []

    def test_get_evidence(self, client: TestClient) -> None:
        """GET /{id}/evidence returns envelope manifest; POST adds items."""
        summary = _create_investigation(client)
        inv_id = summary["id"]

        # Empty envelope
        resp = client.get(f"/api/v1/investigations/{inv_id}/evidence")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

        # Submit evidence
        ev = _submit_evidence(client, inv_id, "first piece of evidence")
        assert ev["evidence_id"].startswith("EV")
        assert ev["provenance_class"] == "public_primary"
        assert ev["content_type"] == "text/plain"
        assert len(ev["content_hash"]) > 0

        # Envelope now has 1 item
        resp = client.get(f"/api/v1/investigations/{inv_id}/evidence")
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["evidence_id"] == ev["evidence_id"]

    def test_get_claims(self, client: TestClient) -> None:
        """GET /{id}/claims returns claim graph with status summary."""
        summary = _create_investigation(client)
        inv_id = summary["id"]

        # Submit evidence first, then claim
        ev = _submit_evidence(client, inv_id)
        claim = _register_claim(client, inv_id, evidence_refs=[ev["evidence_id"]])

        assert claim["claim_id"].startswith("CLM")
        assert claim["claim_type"] == "fact"
        assert ev["evidence_id"] in claim["evidence_refs"]

        # Get claim graph
        resp = client.get(f"/api/v1/investigations/{inv_id}/claims")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["claims"]) == 1
        assert "root_hash" in data
        assert "status_summary" in data

    def test_get_counter_signals(self, client: TestClient) -> None:
        """GET /{id}/counter-signals returns feed; POST logs signals."""
        summary = _create_investigation(client)
        inv_id = summary["id"]

        # Empty feed
        resp = client.get(f"/api/v1/investigations/{inv_id}/counter-signals")
        assert resp.status_code == 200
        assert resp.json()["signals"] == []

        # Log a counter-signal
        cs_payload = {
            "signal_class": "filing_contradiction",
            "material": True,
            "resolution_impact": "weakens primary claim",
            "detection_method": "human_submitted",
            "evidence_ref": None,
        }
        resp = client.post(f"/api/v1/investigations/{inv_id}/counter-signals", json=cs_payload)
        assert resp.status_code == 201
        cs = resp.json()
        assert cs["signal_class"] == "filing_contradiction"
        assert cs["material"] is True

        # Feed now has 1 signal
        resp = client.get(f"/api/v1/investigations/{inv_id}/counter-signals")
        data = resp.json()
        assert len(data["signals"]) == 1
        assert "summary" in data

    def test_get_drift(self, client: TestClient) -> None:
        """GET /{id}/drift returns drift events (empty by default)."""
        summary = _create_investigation(client)
        inv_id = summary["id"]

        resp = client.get(f"/api/v1/investigations/{inv_id}/drift")
        assert resp.status_code == 200
        data = resp.json()
        assert data["events"] == []
        assert data["has_material_drift"] is False

    def test_get_certificate(self, client: TestClient) -> None:
        """GET /{id}/certificate builds and returns investigation certificate."""
        summary = _create_investigation(client)
        inv_id = summary["id"]

        # Add some data first
        ev = _submit_evidence(client, inv_id, "certificate evidence")
        _register_claim(client, inv_id, evidence_refs=[ev["evidence_id"]])

        resp = client.get(f"/api/v1/investigations/{inv_id}/certificate")
        assert resp.status_code == 200
        cert = resp.json()

        assert cert["certificate_id"].startswith("CERT-")
        assert cert["theatre_id"] == "TH_TEST"
        assert cert["construct_id"] == "CON_TEST"
        assert cert["evidence_item_count"] == 1
        assert cert["claim_count"] == 1
        assert len(cert["certificate_hash"]) > 0
        assert cert["routing_decision"] in ("ALLOWED", "REVIEW_REQUIRED")
        assert "methodology_version" in cert
        assert "toolset_version" in cert

        # Investigation status should now be completed
        resp = client.get(f"/api/v1/investigations/{inv_id}")
        assert resp.json()["status"] == "completed"


class TestInvestigationRoutes404:
    """Tests for 404 handling on invalid investigation IDs."""

    def test_get_nonexistent_investigation(self, client: TestClient) -> None:
        resp = client.get("/api/v1/investigations/INV-nonexistent")
        assert resp.status_code == 404

    def test_submit_evidence_nonexistent(self, client: TestClient) -> None:
        payload = {
            "content_base64": base64.b64encode(b"test").decode(),
            "provenance_class": "public_primary",
        }
        resp = client.post("/api/v1/investigations/INV-nonexistent/evidence", json=payload)
        assert resp.status_code == 404
