"""Shared pytest fixtures for OSINT pipeline tests.

Provides fixture loaders, mock WorldMonitor configs, and test
collector factories. All fixtures use mock data — no real HTTP calls.
Live tests gated behind --live-wm / --live-ch flags.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from backend.osint.collectors.worldmonitor import WorldMonitorCollector, WorldMonitorConfig
from backend.osint.models.evidence import WMDomain


def pytest_addoption(parser):
    """Add live test opt-in flags."""
    parser.addoption("--live-wm", action="store_true", default=False,
                     help="Run live WorldMonitor tests")
    parser.addoption("--live-ch", action="store_true", default=False,
                     help="Run live Companies House tests")


def pytest_configure(config):
    """Register custom markers for live tests."""
    config.addinivalue_line("markers", "live_wm: requires live WorldMonitor instance")
    config.addinivalue_line("markers", "live_ch: requires live Companies House API key")


def pytest_collection_modifyitems(config, items):
    """Skip live tests unless opt-in flag or env var is set."""
    skip_wm = not (config.getoption("--live-wm", default=False)
                   or os.environ.get("ECHELON_LIVE_WM"))
    skip_ch = not (config.getoption("--live-ch", default=False)
                   or os.environ.get("ECHELON_LIVE_CH"))
    for item in items:
        if "live_wm" in item.keywords and skip_wm:
            item.add_marker(pytest.mark.skip(
                reason="Need --live-wm flag or ECHELON_LIVE_WM=1"))
        if "live_ch" in item.keywords and skip_ch:
            item.add_marker(pytest.mark.skip(
                reason="Need --live-ch flag or ECHELON_LIVE_CH=1"))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    """Load a JSON fixture file from the fixtures directory."""
    path = FIXTURES_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _fixture_bytes(name: str) -> bytes:
    """Load a fixture file as raw bytes."""
    path = FIXTURES_DIR / name
    with open(path, "rb") as f:
        return f.read()


@pytest.fixture
def cii_response() -> dict:
    """Mock CII endpoint response."""
    return _load_fixture("wm_cii_response.json")


@pytest.fixture
def market_response() -> dict:
    """Mock market snapshot response."""
    return _load_fixture("wm_market_response.json")


@pytest.fixture
def maritime_response() -> dict:
    """Mock maritime anomaly response."""
    return _load_fixture("wm_maritime_response.json")


@pytest.fixture
def error_responses() -> dict:
    """Mock error responses (5xx, timeout, malformed)."""
    return _load_fixture("wm_error_responses.json")


@pytest.fixture
def cii_response_bytes() -> bytes:
    """Mock CII response as raw bytes."""
    return _fixture_bytes("wm_cii_response.json")


@pytest.fixture
def market_response_bytes() -> bytes:
    """Mock market response as raw bytes."""
    return _fixture_bytes("wm_market_response.json")


@pytest.fixture
def maritime_response_bytes() -> bytes:
    """Mock maritime response as raw bytes."""
    return _fixture_bytes("wm_maritime_response.json")


@pytest.fixture
def wm_config() -> WorldMonitorConfig:
    """Test WorldMonitor config with short timeouts for fast tests."""
    return WorldMonitorConfig(
        base_url="http://localhost:8080",
        timeout_s=5.0,
        version="v0.1.0",
        retry_count=1,
        retry_delay_s=0.01,  # Very short for tests
    )


@pytest.fixture
def cii_collector(wm_config: WorldMonitorConfig) -> WorldMonitorCollector:
    """CII domain collector with test config."""
    return WorldMonitorCollector(domain=WMDomain.INTELLIGENCE, config=wm_config)


@pytest.fixture
def market_collector(wm_config: WorldMonitorConfig) -> WorldMonitorCollector:
    """Market domain collector with test config."""
    return WorldMonitorCollector(domain=WMDomain.MARKET, config=wm_config)


@pytest.fixture
def maritime_collector(wm_config: WorldMonitorConfig) -> WorldMonitorCollector:
    """Maritime domain collector with test config."""
    return WorldMonitorCollector(domain=WMDomain.MARITIME, config=wm_config)


@pytest.fixture
def sources_json_path() -> str:
    """Path to the WM sources registry JSON."""
    return str(Path(__file__).parent.parent / "sources.json")
