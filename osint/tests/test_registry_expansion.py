"""
Tests for the Intelligence Database Expansion (Cycle-005, Sprint 1).

Validates schema expansion (9 new fields), source group enum changes,
settlement guardrails, validator enhancements, and Pydantic model updates.

British spelling throughout.
"""

import json
import os
import sys
import tempfile

# Add osint/ directory to path so osint_pipeline package is found here.
_OSINT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _OSINT_DIR)

from osint_pipeline.models.registry import RegistryLoader, RegistrySource

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Monorepo root is two levels up from osint/tests/
_REPO_ROOT = os.path.normpath(os.path.join(_OSINT_DIR, ".."))
if not os.path.isdir(os.path.join(_REPO_ROOT, "theatre")):
    _REPO_ROOT = "/Users/tobiasharber/Developer/prediction-market-monorepo.nosync"

_DATASETS = os.path.join(
    _REPO_ROOT, "theatre", "fixtures", "two_rail_theatres_v0_1", "datasets"
)
_V060 = os.path.join(_DATASETS, "echelon_osint_source_registry_v0_6_0.json")
_V100 = os.path.join(_DATASETS, "echelon_osint_source_registry_v1_0_0.json")

_VALIDATOR = os.path.join(_REPO_ROOT, "tools", "validate_osint_registry.py")

# Import validator
sys.path.insert(0, os.path.join(_REPO_ROOT, "tools"))
import validate_osint_registry as validator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_temp_registry(reg: dict) -> str:
    """Write registry to a temp file and return path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(reg, f, indent=2)
    return path


def _minimal_registry(**overrides) -> dict:
    """Build a minimal valid v1.0.0 registry for testing."""
    base = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://echelon.ai/schemas/osint_source_registry/v0.1",
        "title": "Test Registry",
        "description": "Test",
        "version": "1.0.0",
        "generated_at": "2026-03-01T00:00:00Z",
        "source_group_enum": {
            "description": "Test",
            "committed_values": [
                "official_gov", "sanctions_compliance", "health_biosecurity",
                "climate_weather", "election_governance", "demographic_economic",
                "entity_resolution", "geospatial_verification", "calendar_counter_signal",
                "alt_data_behavioural", "energy_commodities", "geophysical_hazard",
                "market_data",
            ],
            "proposed_extensions": [],
        },
        "resolution_role_enum": ["primary_evidence", "secondary_corroboration", "counter_signal", "triage_only"],
        "priority_bucket_enum": ["settlement_grade", "scoring_grade", "triage_only", "avoid"],
        "auth_methods_enum": ["none", "api_key", "basic", "oauth2", "user_agent_header", "registration", "membership"],
        "timestamp_precision_enum": ["second", "day", "month"],
        "counter_signal_class_enum": ["calendar", "calendar_holiday", "infrastructure_outage"],
        "access_surface_enum": ["public_api", "partner_api", "portal_scrape", "paid_gateway", "manual_attestation"],
        "revision_policy_enum": ["immutable", "as_of_timestamp", "latest_only", "forbid_settlement"],
        "receipt_mode_enum": ["none", "http_transcript", "cryptographic_transcript", "signed_receipt", "witness_quorum"],
        "consumption_surface_enum": [
            "theatre_settlement", "mission_factory", "bounded_inquiry",
            "delta_brief", "agent_context", "consumer_dashboard", "sponsored_theatre",
        ],
        "quality_tier_enum": [
            "settlement_grade", "investigation_grade", "anomaly_detection",
            "change_detection", "reasoning_grade", "display_grade",
        ],
        "access_tier_enum": ["tier_a", "tier_b", "tier_c"],
        "collector_status_enum": ["active", "planned", "enumerated", "deprecated"],
        "sources": [],
        "summary": {"total_sources": 0},
    }
    base.update(overrides)
    return base


def _make_source(source_id="test_src", settlement_eligible=False, **overrides) -> dict:
    """Build a minimal valid source entry."""
    s = {
        "source_id": source_id,
        "source_name": "Test Source",
        "source_group": "official_gov",
        "priority_bucket": "scoring_grade",
        "resolution_role": "primary_evidence",
        "replayability": "strong",
        "legal_risk": "low",
        "cost_model": "free",
        "rate_limit_notes": "No limit",
        "gap_policy_default": False,
        "world_monitor_domain": None,
        "evidence_capture": {
            "request_params": True,
            "response_headers": True,
            "payload_hash": True,
            "timestamp_precision": "second",
        },
        "settlement_eligible": settlement_eligible,
        "notes": "Test source",
        "theatre_families": ["OSINT_COMPOSED_ORACLE"],
        "auth_methods": ["none"],
        "jurisdiction": "GB",
        "independence_upstream_id": f"upstream_{source_id}",
        "access_surface": "public_api",
        "access_surface_confirmed": True,
        "revision_policy": "as_of_timestamp",
        "receipt_mode_minimum": "http_transcript",
        "counter_signal_class": None,
        "ui_url": "https://example.com/",
        "api_url": "https://api.example.com/",
        "access_proof": {
            "doc_url": "https://api.example.com/",
            "auth_method_expected": ["none"],
            "verified": True,
            "proof_type": "official_docs",
        },
        # v1.0.0 fields
        "consumption_surfaces": [
            {"surface": "mission_factory", "quality_tier": "investigation_grade", "update_interval_seconds": None, "notes": None},
            {"surface": "consumer_dashboard", "quality_tier": "display_grade", "update_interval_seconds": None, "notes": None},
        ],
        "access_tier": "tier_a",
        "api_endpoint": "https://api.example.com/",
        "collector_status": "planned",
        "rate_limit_policy": "No limit",
        "dashboard_permitted": True,
        "settlement_latest_only_override": False,
        "settlement_requires_corroboration": False,
        "independence_notes": None,
    }
    s.update(overrides)
    return s


# ---------------------------------------------------------------------------
# Test 1: Backwards compatibility — v0.6.0 loads into Pydantic model
# ---------------------------------------------------------------------------

def test_backwards_compat_v060_loads():
    """v0.6.0 registry must load into RegistryLoader without Pydantic errors.
    New fields get default values."""
    assert os.path.exists(_V060), f"v0.6.0 registry not found at {_V060}"
    loader = RegistryLoader.from_file(_V060)
    assert loader.total_sources >= 60
    assert loader.version == "0.6.0"

    # New fields should have defaults
    src = loader.get("companies_house_api")
    assert src is not None
    assert src.consumption_surfaces == []  # default: empty list
    assert src.access_tier == "tier_a"  # default
    assert src.collector_status == "planned"  # default
    assert src.dashboard_permitted is True  # default
    assert src.settlement_latest_only_override is False  # default
    assert src.settlement_requires_corroboration is False  # default
    assert src.independence_notes is None  # default


# ---------------------------------------------------------------------------
# Test 2: Settlement guardrail — receipt_mode_minimum required
# ---------------------------------------------------------------------------

def test_settlement_guardrail_receipt_mode():
    """settlement_eligible=true + receipt_mode_minimum='none' must produce an error."""
    src = _make_source(
        source_id="bad_receipt",
        settlement_eligible=True,
        priority_bucket="settlement_grade",
        receipt_mode_minimum="none",
        consumption_surfaces=[
            {"surface": "theatre_settlement", "quality_tier": "settlement_grade", "update_interval_seconds": None, "notes": None},
        ],
    )
    reg = _minimal_registry(
        sources=[src],
        summary={"total_sources": 1, "settlement_eligible_count": 1},
    )
    path = _write_temp_registry(reg)
    try:
        errors, warnings = validator.validate(path)
        receipt_errors = [e for e in errors if "receipt_mode_minimum" in e and "bad_receipt" in e]
        assert len(receipt_errors) >= 1, f"Expected receipt_mode error, got errors: {errors}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 3: Settlement guardrail — latest_only without override
# ---------------------------------------------------------------------------

def test_settlement_guardrail_latest_only_without_override():
    """latest_only + settlement_eligible + no override/compensating receipt = error."""
    src = _make_source(
        source_id="latest_bad",
        settlement_eligible=True,
        priority_bucket="settlement_grade",
        revision_policy="latest_only",
        receipt_mode_minimum="http_transcript",
        settlement_latest_only_override=False,
        consumption_surfaces=[
            {"surface": "theatre_settlement", "quality_tier": "settlement_grade", "update_interval_seconds": None, "notes": None},
        ],
    )
    reg = _minimal_registry(
        sources=[src],
        summary={"total_sources": 1, "settlement_eligible_count": 1},
    )
    path = _write_temp_registry(reg)
    try:
        errors, warnings = validator.validate(path)
        latest_errors = [e for e in errors if "latest_only" in e and "latest_bad" in e]
        assert len(latest_errors) >= 1, f"Expected latest_only error, got errors: {errors}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 4: Settlement guardrail — latest_only WITH override
# ---------------------------------------------------------------------------

def test_settlement_guardrail_latest_only_with_override():
    """latest_only + settlement_eligible + settlement_latest_only_override=True = OK."""
    src = _make_source(
        source_id="latest_ok",
        settlement_eligible=True,
        priority_bucket="settlement_grade",
        revision_policy="latest_only",
        receipt_mode_minimum="http_transcript",
        settlement_latest_only_override=True,
        consumption_surfaces=[
            {"surface": "theatre_settlement", "quality_tier": "settlement_grade", "update_interval_seconds": None, "notes": None},
        ],
    )
    reg = _minimal_registry(
        sources=[src],
        summary={"total_sources": 1, "settlement_eligible_count": 1},
    )
    path = _write_temp_registry(reg)
    try:
        errors, warnings = validator.validate(path)
        latest_errors = [e for e in errors if "latest_only" in e and "latest_ok" in e]
        assert len(latest_errors) == 0, f"Expected no latest_only error with override, got: {latest_errors}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 5: Settlement requires corroboration warning
# ---------------------------------------------------------------------------

def test_settlement_requires_corroboration_warning():
    """settlement_requires_corroboration=true must produce a warning (not error)."""
    src = _make_source(
        source_id="corrob_src",
        settlement_eligible=True,
        priority_bucket="settlement_grade",
        settlement_requires_corroboration=True,
        consumption_surfaces=[
            {"surface": "theatre_settlement", "quality_tier": "settlement_grade", "update_interval_seconds": None, "notes": None},
        ],
    )
    reg = _minimal_registry(
        sources=[src],
        summary={"total_sources": 1, "settlement_eligible_count": 1},
    )
    path = _write_temp_registry(reg)
    try:
        errors, warnings = validator.validate(path)
        corrob_warnings = [w for w in warnings if "corroboration" in w.lower() and "corrob_src" in w]
        assert len(corrob_warnings) >= 1, f"Expected corroboration warning, got warnings: {warnings}"
        # Must NOT be in errors
        corrob_errors = [e for e in errors if "corroboration" in e.lower() and "corrob_src" in e]
        assert len(corrob_errors) == 0, f"Expected no corroboration errors, got: {corrob_errors}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 6: Source group alias resolution
# ---------------------------------------------------------------------------

def test_source_group_alias_resolution():
    """court_record should produce a warning about alias to judicial_record."""
    src = _make_source(
        source_id="alias_src",
        source_group="court_record",
    )
    reg = _minimal_registry(
        sources=[src],
        summary={"total_sources": 1},
    )
    # Add court_record to committed_values for this test (alias resolution still warns)
    reg["source_group_enum"]["committed_values"].append("court_record")
    path = _write_temp_registry(reg)
    try:
        errors, warnings = validator.validate(path)
        alias_warnings = [w for w in warnings if "alias" in w.lower() and "court_record" in w]
        assert len(alias_warnings) >= 1, f"Expected alias warning for court_record, got warnings: {warnings}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 7: Consumption surfaces inference warning
# ---------------------------------------------------------------------------

def test_consumption_surfaces_inference_warning():
    """settlement_eligible=true + empty consumption_surfaces = warning (non-strict)."""
    src = _make_source(
        source_id="empty_cs",
        settlement_eligible=True,
        priority_bucket="settlement_grade",
        consumption_surfaces=[],
    )
    reg = _minimal_registry(
        sources=[src],
        summary={"total_sources": 1, "settlement_eligible_count": 1},
    )
    path = _write_temp_registry(reg)
    try:
        errors, warnings = validator.validate(path, strict=False)
        cs_warnings = [w for w in warnings if "consumption_surfaces" in w and "empty_cs" in w]
        assert len(cs_warnings) >= 1, f"Expected consumption_surfaces warning, got warnings: {warnings}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 8: Dashboard permitted default for paid access
# ---------------------------------------------------------------------------

def test_dashboard_permitted_default_paid():
    """tier_c access with dashboard_permitted=true should produce a warning."""
    src = _make_source(
        source_id="paid_src",
        access_tier="tier_c",
        dashboard_permitted=True,
    )
    reg = _minimal_registry(
        sources=[src],
        summary={"total_sources": 1},
    )
    path = _write_temp_registry(reg)
    try:
        errors, warnings = validator.validate(path)
        paid_warnings = [w for w in warnings if "tier_c" in w and "paid_src" in w]
        assert len(paid_warnings) >= 1, f"Expected tier_c dashboard warning, got warnings: {warnings}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 9: api_endpoint rejects query string
# ---------------------------------------------------------------------------

def test_api_endpoint_rejects_query_string():
    """api_endpoint with ? or # must produce an error."""
    src = _make_source(
        source_id="bad_ep",
        api_endpoint="https://api.example.com/data?key=abc",
    )
    reg = _minimal_registry(
        sources=[src],
        summary={"total_sources": 1},
    )
    path = _write_temp_registry(reg)
    try:
        errors, warnings = validator.validate(path)
        ep_errors = [e for e in errors if "api_endpoint" in e and "bad_ep" in e]
        assert len(ep_errors) >= 1, f"Expected api_endpoint error, got errors: {errors}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 10: rate_limit_policy required for active
# ---------------------------------------------------------------------------

def test_rate_limit_policy_required_for_active():
    """collector_status=active + empty rate_limit_policy = warning."""
    src = _make_source(
        source_id="active_no_rl",
        collector_status="active",
        rate_limit_policy=None,
    )
    reg = _minimal_registry(
        sources=[src],
        summary={"total_sources": 1},
    )
    path = _write_temp_registry(reg)
    try:
        errors, warnings = validator.validate(path)
        rl_warnings = [w for w in warnings if "rate_limit_policy" in w and "active_no_rl" in w]
        assert len(rl_warnings) >= 1, f"Expected rate_limit_policy warning, got warnings: {warnings}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 11: Summary header mismatch fails
# ---------------------------------------------------------------------------

def test_summary_header_mismatch_fails():
    """summary.total_sources != actual count must produce an error."""
    src = _make_source(source_id="src_1")
    reg = _minimal_registry(
        sources=[src],
        summary={"total_sources": 99},  # wrong count
    )
    path = _write_temp_registry(reg)
    try:
        errors, warnings = validator.validate(path)
        count_errors = [e for e in errors if "total_sources" in e]
        assert len(count_errors) >= 1, f"Expected total_sources error, got errors: {errors}"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Test 12: RegistrySource model has new fields
# ---------------------------------------------------------------------------

def test_registry_source_model_new_fields():
    """RegistrySource Pydantic model must have all 9 new fields with defaults."""
    src = RegistrySource(
        source_id="model_test",
        source_group="official_gov",
        resolution_role="primary_evidence",
        priority_bucket="scoring_grade",
        settlement_eligible=False,
        jurisdiction="GB",
    )
    # Check all 9 new fields exist and have correct defaults
    assert src.consumption_surfaces == []
    assert src.access_tier == "tier_a"
    assert src.api_endpoint is None
    assert src.collector_status == "planned"
    assert src.rate_limit_policy is None
    assert src.dashboard_permitted is True
    assert src.settlement_latest_only_override is False
    assert src.settlement_requires_corroboration is False
    assert src.independence_notes is None


# ---------------------------------------------------------------------------
# Test 13: RegistryLoader.by_consumption_surface
# ---------------------------------------------------------------------------

def test_registry_loader_by_consumption_surface():
    """by_consumption_surface returns only sources containing the specified surface."""
    src_a = RegistrySource(
        source_id="src_a",
        source_group="official_gov",
        resolution_role="primary_evidence",
        priority_bucket="settlement_grade",
        settlement_eligible=True,
        jurisdiction="GB",
        consumption_surfaces=[
            {"surface": "theatre_settlement", "quality_tier": "settlement_grade"},
            {"surface": "mission_factory", "quality_tier": "investigation_grade"},
        ],
    )
    src_b = RegistrySource(
        source_id="src_b",
        source_group="official_gov",
        resolution_role="secondary_corroboration",
        priority_bucket="scoring_grade",
        settlement_eligible=False,
        jurisdiction="GB",
        consumption_surfaces=[
            {"surface": "mission_factory", "quality_tier": "investigation_grade"},
        ],
    )
    loader = RegistryLoader(sources=[src_a, src_b], metadata={"version": "1.0.0"})

    # theatre_settlement — only src_a
    settlement_sources = loader.by_consumption_surface("theatre_settlement")
    assert len(settlement_sources) == 1
    assert settlement_sources[0].source_id == "src_a"

    # mission_factory — both
    factory_sources = loader.by_consumption_surface("mission_factory")
    assert len(factory_sources) == 2

    # nonexistent surface — empty
    empty = loader.by_consumption_surface("nonexistent")
    assert len(empty) == 0

    # active_sources
    assert len(loader.active_sources()) == 0  # both default to planned

    # settlement_sources_requiring_corroboration
    assert len(loader.settlement_sources_requiring_corroboration()) == 0

    # by_access_tier
    assert len(loader.by_access_tier("tier_a")) == 2

    # by_collector_status
    assert len(loader.by_collector_status("planned")) == 2


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__} -- {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__} -- {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {passed + failed} total")
    sys.exit(1 if failed > 0 else 0)
