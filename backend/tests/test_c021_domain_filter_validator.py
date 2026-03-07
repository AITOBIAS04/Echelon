"""Tests for DomainFilterValidator — cycle-021 sprint-0.

Pure function tests: no DB, no mocks. Tests cover all 9 DomainFilter enum values.
"""
import pytest

from backend.services.domain_filter_validator import (
    DomainFilterViolation,
    get_allowed_sources,
    validate_evidence_source,
    validate_signal_source,
)


def test_in_scope_evidence_passes():
    """Evidence from an in-scope source is accepted."""
    filters = ["corporate_and_entity", "finance_and_markets"]
    # corporate_filing is in CORPORATE_AND_ENTITY group
    validate_evidence_source(filters, source_id="corporate_filing")
    # market_data is in FINANCE_AND_MARKETS group
    validate_evidence_source(filters, source_id="market_data")


def test_out_of_scope_evidence_rejected():
    """Evidence from an out-of-scope source raises DomainFilterViolation."""
    filters = ["corporate_and_entity"]
    with pytest.raises(DomainFilterViolation) as exc_info:
        validate_evidence_source(filters, source_id="maritime_ais")
    assert exc_info.value.source == "maritime_ais"
    assert "corporate_filing" in exc_info.value.allowed_sources
    assert exc_info.value.domain_filters == filters


def test_empty_filters_passes_all():
    """Empty domain filters means no enforcement — all sources accepted."""
    validate_evidence_source([], source_id="maritime_ais")
    validate_evidence_source([], source_id="cyber_threat")
    validate_signal_source([], detection_method="cyber_threat", source_ref="cyber_threat")


def test_signal_out_of_scope_rejected():
    """Signal from an out-of-scope source raises DomainFilterViolation."""
    filters = ["maritime"]
    with pytest.raises(DomainFilterViolation) as exc_info:
        validate_signal_source(filters, detection_method="scan", source_ref="cyber_threat")
    assert exc_info.value.source == "cyber_threat"


def test_meta_methods_always_pass():
    """Meta detection methods (automated_osint, human_submitted, paradox_engine) always pass."""
    filters = ["maritime"]  # only maritime_ais and geospatial_verification allowed
    # These meta-methods should pass even though they're not in the allowed set
    validate_signal_source(filters, detection_method="automated_osint")
    validate_signal_source(filters, detection_method="human_submitted")
    validate_signal_source(filters, detection_method="paradox_engine")


def test_get_allowed_sources_expands_all_filters():
    """get_allowed_sources correctly expands all 9 DomainFilter enum values."""
    all_filters = [
        "corporate_and_entity",
        "finance_and_markets",
        "maritime",
        "airspace",
        "geopolitical_and_conflict",
        "cyber_threat",
        "property_and_land",
        "court_and_legal",
        "satellite_and_earth_observation",
    ]
    allowed = get_allowed_sources(all_filters)

    # Verify key sources from each group
    assert "corporate_filing" in allowed
    assert "market_data" in allowed
    assert "maritime_ais" in allowed
    assert "flight_tracking" in allowed
    assert "conflict_event" in allowed
    assert "cyber_threat" in allowed
    assert "property_registry" in allowed
    assert "court_filing" in allowed
    assert "satellite_imagery" in allowed

    # Should have all source groups (count from DOMAIN_FILTER_SOURCE_GROUPS)
    assert len(allowed) == 18
