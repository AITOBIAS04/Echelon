"""Tests for the FastAPI verification API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from echelon_verify.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_status_unknown_job_returns_404(client):
    resp = client.get("/api/verification/status/nonexistent-id")
    assert resp.status_code == 404


def test_result_unknown_job_returns_404(client):
    resp = client.get("/api/verification/result/nonexistent-id")
    assert resp.status_code == 404


def test_list_certificates_empty(client):
    resp = client.get("/api/verification/certificates")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
