"""Cycle-017 Sprint 3 — Registry Schema Expansion tests.

4 tests:
1. Source registry entries correctly store and return policy fields
2. Evidence submission without receipt when required → 422
3. Evidence submission with receipt when required → 200
4. Investigation with legal-review source returns has_legal_review_requirement=true
"""

import base64
import json
import os
import tempfile

import pytest

from backend.osint.models.registry import RegistryLoader


# ── Test 1: Registry fields ──────────────────────────────────────────

def test_registry_policy_fields():
    """Source registry entries correctly store and return policy fields."""
    sources_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "osint", "sources.json",
    )
    loader = RegistryLoader(sources_path)

    # Polymarket — pure_id_lookup, no receipt, no legal
    poly = loader.get_source("polymarket_api")
    assert poly is not None
    assert poly.query_determinism == "pure_id_lookup"
    assert poly.receipt_body_required is False
    assert poly.requires_legal_review is False

    # Companies House — search_endpoint, receipt required, no legal
    ch = loader.get_source("companies_house_api")
    assert ch is not None
    assert ch.query_determinism == "search_endpoint"
    assert ch.receipt_body_required is True
    assert ch.requires_legal_review is False

    # Private leak — bulk_export, receipt required, legal review required
    leak = loader.get_source("private_leak_source")
    assert leak is not None
    assert leak.query_determinism == "bulk_export"
    assert leak.receipt_body_required is True
    assert leak.requires_legal_review is True

    # Validation should pass
    errors = loader.validate()
    assert errors == [], f"Validation errors: {errors}"


# ── Tests 2-4: API-level (using FastAPI TestClient) ──────────────────

@pytest.fixture
def client():
    """Create a FastAPI test client with investigation routes."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.api.investigation_routes import router, _investigations, _get_registry

    app = FastAPI()
    app.include_router(router)

    # Clear investigation store between tests
    _investigations.clear()

    yield TestClient(app)

    _investigations.clear()


@pytest.fixture
def investigation_id(client):
    """Create a test investigation and return its ID."""
    resp = client.post("/api/v1/investigations/", json={
        "theatre_id": "TEST_THEATRE",
        "construct_id": "TEST_CONSTRUCT",
        "inquiry_class": "INVESTIGATIVE",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


def test_evidence_submit_without_receipt_returns_422(client, investigation_id):
    """Submit evidence without receipt when source requires it → 422."""
    content_b64 = base64.b64encode(b"test evidence content").decode()

    resp = client.post(
        f"/api/v1/investigations/{investigation_id}/evidence",
        json={
            "content_base64": content_b64,
            "provenance_class": "public_primary",
            "source_id": "companies_house_api",
            "receipt_body": "",
        },
    )
    assert resp.status_code == 422
    assert "receipt_body" in resp.json()["detail"]


def test_evidence_submit_with_receipt_succeeds(client, investigation_id):
    """Submit evidence with receipt when source requires it → 201."""
    content_b64 = base64.b64encode(b"test evidence content").decode()

    resp = client.post(
        f"/api/v1/investigations/{investigation_id}/evidence",
        json={
            "content_base64": content_b64,
            "provenance_class": "public_primary",
            "source_id": "companies_house_api",
            "receipt_body": "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n...",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["evidence_id"] == "E001"


def test_investigation_detail_legal_review_flag(client, investigation_id):
    """Investigation with legal-review source returns has_legal_review_requirement=true."""
    # First, check default is false
    resp = client.get(f"/api/v1/investigations/{investigation_id}")
    assert resp.status_code == 200
    assert resp.json()["has_legal_review_requirement"] is False

    # Submit evidence from a source that requires legal review
    content_b64 = base64.b64encode(b"leaked document content").decode()
    resp = client.post(
        f"/api/v1/investigations/{investigation_id}/evidence",
        json={
            "content_base64": content_b64,
            "provenance_class": "private_leak",
            "source_id": "private_leak_source",
            "receipt_body": "witness attestation hash: abc123",
        },
    )
    assert resp.status_code == 201

    # Now detail should show has_legal_review_requirement=true
    resp = client.get(f"/api/v1/investigations/{investigation_id}")
    assert resp.status_code == 200
    assert resp.json()["has_legal_review_requirement"] is True
