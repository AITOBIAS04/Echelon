"""Cycle 024 Sprint 1 — ConstructRegistry + ConstructAdapter tests.

Tests:
1. Register Artisan v1.4.0 with correct hash, status=REGISTERED, skill_manifest has 14 entries
2. Registration rejects invalid inputs (bad hash format, empty manifest, missing keys)
3. Status transitions enforce valid paths
4. Create run creates Investigation with correct template_id, construct_id, run_number
5. Capture episode persists evidence with correct content_hash, content_text, construct_meta_json
6. Cannot capture episode for COMPLETED investigation
7. Complete run validates all committed prompts have evidence items
"""

import hashlib
import sys
from dataclasses import dataclass
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Stub backend.database to avoid asyncpg import chain ──

# Create stub modules for the database import chain so we can import
# the services without triggering the real connection module (which
# eagerly creates an asyncpg engine at import time).

_db_stub = ModuleType("backend.database")
_db_stub.__path__ = []

_models_stub = ModuleType("backend.database.models")

# Create lightweight model classes that behave like SQLAlchemy models
# but don't require the real ORM machinery for unit tests.

class _StubColumn:
    """Minimal stand-in for a SQLAlchemy mapped column used in queries."""
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False

class _StubConstructRegistration:
    """Stub for ConstructRegistration model."""
    # Class-level attributes for SQLAlchemy-style column references
    slug = _StubColumn()
    version = _StubColumn()
    created_at = _StubColumn()
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class _StubInvestigation:
    """Stub for Investigation model."""
    run_number = _StubColumn()
    construct_id = _StubColumn()
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class _StubInvestigationEvidenceItem:
    """Stub for InvestigationEvidenceItem model."""
    investigation_id = _StubColumn()
    submitted_at = _StubColumn()
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

_models_stub.ConstructRegistration = _StubConstructRegistration
_models_stub.Investigation = _StubInvestigation
_models_stub.InvestigationEvidenceItem = _StubInvestigationEvidenceItem

# Patch sys.modules BEFORE importing services
if "backend.database" not in sys.modules:
    sys.modules["backend.database"] = _db_stub
    sys.modules["backend.database.models"] = _models_stub

    # Also stub connection and config
    _conn_stub = ModuleType("backend.database.connection")
    _conn_stub.Base = type("Base", (), {})
    sys.modules["backend.database.connection"] = _conn_stub
    _config_stub = ModuleType("backend.database.config")
    sys.modules["backend.database.config"] = _config_stub

# Stub sqlalchemy imports needed by services
_sa_stub = MagicMock()
if "sqlalchemy" not in sys.modules:
    sys.modules["sqlalchemy"] = _sa_stub
    sys.modules["sqlalchemy.ext"] = MagicMock()
    sys.modules["sqlalchemy.ext.asyncio"] = MagicMock()

# Now safe to import services
from backend.services.construct_registry import ConstructRegistry
from backend.services.construct_adapter import ConstructAdapter
from backend.services.test_prompt_registry import TestPromptRegistry


# ── Test Data ──

ARTISAN_SKILL_MANIFEST = [
    {"command": "/distill", "domain": "Design Systems"},
    {"command": "/distill", "domain": "Frontend Best Practices"},
    {"command": "/distill", "domain": "Motion Design"},
    {"command": "/iterate", "domain": "Design Systems"},
    {"command": "/iterate", "domain": "Visual Refinement"},
    {"command": "/iterate", "domain": "Motion Design"},
    {"command": "/survey", "domain": "Design Systems"},
    {"command": "/survey", "domain": "Frontend Best Practices"},
    {"command": "/survey", "domain": "Visual Refinement"},
    {"command": "/motion", "domain": "Motion Design"},
    {"command": "/motion", "domain": "Visual Refinement"},
    {"command": "/synthesize", "domain": "Taste Compounding"},
    {"command": "/synthesize", "domain": "Design Systems"},
    {"command": "/synthesize", "domain": "Visual Refinement"},
]

ARTISAN_DOMAIN_CLAIMS = [
    "Design Systems",
    "Frontend Best Practices",
    "Motion Design",
    "Taste Compounding",
    "Visual Refinement",
]


def _make_mock_session():
    """Create a properly configured AsyncMock session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


class TestConstructRegistry:
    """Test ConstructRegistry service."""

    @pytest.mark.asyncio
    async def test_register_artisan_v1_4_0(self):
        """Register Artisan v1.4.0 with correct hash, status=REGISTERED, skill_manifest has 14 entries."""
        session = _make_mock_session()
        registry = ConstructRegistry(session)

        content_hash = "sha256:abc123def456"
        test_prompts_hash = "sha256:prompts789"
        rubric_hash = "sha256:rubric012"

        reg = await registry.register(
            slug="artisan",
            version="1.4.0",
            content_hash=content_hash,
            skill_manifest=ARTISAN_SKILL_MANIFEST,
            domain_claims=ARTISAN_DOMAIN_CLAIMS,
            test_prompts_hash=test_prompts_hash,
            rubric_hash=rubric_hash,
        )

        assert reg.slug == "artisan"
        assert reg.version == "1.4.0"
        assert reg.status == "REGISTERED"
        assert reg.content_hash == content_hash
        assert len(reg.skill_manifest) == 14
        assert reg.skill_count == 14

        # Verify commitment_hash = sha256(content_hash + test_prompts_hash + rubric_hash)
        expected_input = content_hash + test_prompts_hash + rubric_hash
        expected_hash = f"sha256:{hashlib.sha256(expected_input.encode()).hexdigest()}"
        assert reg.commitment_hash == expected_hash

        # Session interactions
        session.add.assert_called_once_with(reg)
        session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_registration_rejects_invalid_inputs(self):
        """Registration validates content_hash format and skill_manifest structure."""
        session = _make_mock_session()
        registry = ConstructRegistry(session)

        # Invalid content_hash (missing sha256: prefix)
        with pytest.raises(ValueError, match="content_hash must start with 'sha256:'"):
            await registry.register(
                slug="artisan",
                version="1.4.0",
                content_hash="badprefix:abc123",
                skill_manifest=ARTISAN_SKILL_MANIFEST,
                domain_claims=ARTISAN_DOMAIN_CLAIMS,
                test_prompts_hash="sha256:prompts789",
                rubric_hash="sha256:rubric012",
            )

        # Empty skill_manifest
        with pytest.raises(ValueError, match="skill_manifest must be non-empty"):
            await registry.register(
                slug="artisan",
                version="1.4.0",
                content_hash="sha256:abc123",
                skill_manifest=[],
                domain_claims=ARTISAN_DOMAIN_CLAIMS,
                test_prompts_hash="sha256:prompts789",
                rubric_hash="sha256:rubric012",
            )

        # Missing command key
        with pytest.raises(ValueError, match="missing 'command' key"):
            await registry.register(
                slug="artisan",
                version="1.4.0",
                content_hash="sha256:abc123",
                skill_manifest=[{"domain": "Design Systems"}],
                domain_claims=ARTISAN_DOMAIN_CLAIMS,
                test_prompts_hash="sha256:prompts789",
                rubric_hash="sha256:rubric012",
            )

    @pytest.mark.asyncio
    async def test_status_transitions_enforce_valid_paths(self):
        """Status transitions enforce valid paths (cannot go from CERTIFIED back to REGISTERED)."""
        session = _make_mock_session()
        registry = ConstructRegistry(session)

        # Mock a CERTIFIED registration
        reg = MagicMock()
        reg.status = "CERTIFIED"
        reg.slug = "artisan"
        reg.version = "1.4.0"
        session.get = AsyncMock(return_value=reg)

        # CERTIFIED → REGISTERED should be rejected (terminal state)
        with pytest.raises(ValueError, match="Invalid status transition"):
            await registry.update_status("test-id", "REGISTERED")

        # CERTIFIED → IN_PROGRESS should also be rejected
        with pytest.raises(ValueError, match="Invalid status transition"):
            await registry.update_status("test-id", "IN_PROGRESS")

        # Verify valid transitions work
        reg2 = MagicMock()
        reg2.status = "REGISTERED"
        reg2.slug = "artisan"
        reg2.version = "1.4.0"
        session.get = AsyncMock(return_value=reg2)

        await registry.update_status("test-id", "IN_PROGRESS")
        assert reg2.status == "IN_PROGRESS"
        session.flush.assert_awaited()


class TestConstructAdapter:
    """Test ConstructAdapter service."""

    @pytest.mark.asyncio
    async def test_create_run_correct_investigation(self):
        """Create run creates Investigation with correct template_id, construct_id, run_number."""
        session = _make_mock_session()
        prompt_registry = TestPromptRegistry()

        adapter = ConstructAdapter(session, prompt_registry)

        # Mock the run_number query (no previous runs)
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        # Create a mock registration
        reg = MagicMock()
        reg.id = "reg-001"
        reg.slug = "artisan"
        reg.version = "1.4.0"
        reg.domain_claims = ARTISAN_DOMAIN_CLAIMS
        reg.commitment_hash = "sha256:commitment123"

        investigation = await adapter.create_run(reg)

        assert investigation.template_id == "CONSTRUCT_VERIFICATION_V1"
        assert investigation.construct_id == "artisan:1.4.0"
        assert investigation.stop_condition == "CONSTRUCT_EVALUATION"
        assert investigation.status == "ACTIVE"
        assert investigation.run_number == 1
        assert investigation.inquiry_class == "INSPECTION"

        # stop_config_json should contain construct run metadata
        config = investigation.stop_config_json
        assert config["construct_registration_id"] == "reg-001"
        assert config["construct_slug"] == "artisan"
        assert config["construct_version"] == "1.4.0"
        assert config["run_number"] == 1
        assert config["commitment_hash"] == "sha256:commitment123"

        # Registration status updated
        assert reg.status == "IN_PROGRESS"
        session.add.assert_called_once()
        session.flush.assert_awaited_once()

        # Test run_number increment: second run for same construct
        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = 1  # Previous max run_number is 1
        session.execute = AsyncMock(return_value=mock_result2)
        session.add.reset_mock()
        session.flush.reset_mock()

        investigation2 = await adapter.create_run(reg)
        assert investigation2.run_number == 2

    @pytest.mark.asyncio
    async def test_capture_episode_persists_evidence(self):
        """Capture episode persists InvestigationEvidenceItem with correct fields."""
        session = _make_mock_session()
        prompt_registry = TestPromptRegistry()

        adapter = ConstructAdapter(session, prompt_registry)

        # Mock investigation lookup
        inv = MagicMock()
        inv.status = "ACTIVE"
        inv.stop_config_json = {
            "construct_slug": "artisan",
            "construct_version": "1.4.0",
            "construct_registration_id": "reg-001",
        }
        session.get = AsyncMock(return_value=inv)

        output_text = "Here is a design system analysis with OKLCH tokens..."
        evidence = await adapter.capture_episode(
            investigation_id="inv-001",
            skill_command="/distill",
            domain="Design Systems",
            prompt_index=1,
            output_text=output_text,
            timing_ms=1500,
        )

        # Verify content_hash
        expected_hash = hashlib.sha256(output_text.encode()).hexdigest()
        assert evidence.content_hash == expected_hash

        # Verify content_text stored
        assert evidence.content_text == output_text

        # Verify construct_meta_json
        meta = evidence.construct_meta_json
        assert meta["skill_command"] == "/distill"
        assert meta["domain"] == "Design Systems"
        assert meta["prompt_index"] == 1
        assert meta["timing_ms"] == 1500
        assert meta["output_hash"] == f"sha256:{expected_hash}"

        # Verify provenance
        assert evidence.provenance_class == "construct_evaluation"
        assert evidence.investigation_id == "inv-001"

        session.add.assert_called_once()
        session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cannot_capture_episode_for_completed_investigation(self):
        """Cannot capture episode for a COMPLETED investigation."""
        session = _make_mock_session()
        prompt_registry = TestPromptRegistry()

        adapter = ConstructAdapter(session, prompt_registry)

        # Mock a COMPLETED investigation
        inv = MagicMock()
        inv.status = "COMPLETED"
        session.get = AsyncMock(return_value=inv)

        with pytest.raises(ValueError, match="Cannot capture episode.*Expected 'ACTIVE'"):
            await adapter.capture_episode(
                investigation_id="inv-001",
                skill_command="/distill",
                domain="Design Systems",
                prompt_index=1,
                output_text="output",
                timing_ms=100,
            )

    @pytest.mark.asyncio
    async def test_complete_run_rejects_partial(self):
        """Complete run validates all committed prompts have evidence items (rejects partial runs)."""
        session = _make_mock_session()
        prompt_registry = TestPromptRegistry()

        adapter = ConstructAdapter(session, prompt_registry)

        # Mock investigation with artisan config
        inv = MagicMock()
        inv.stop_config_json = {
            "committed_prompt_count": 12,
            "construct_slug": "artisan",
            "construct_version": "1.4.0",
            "construct_registration_id": "reg-001",
        }
        session.get = AsyncMock(return_value=inv)

        # Only 2 evidence items (missing 10)
        item1 = MagicMock()
        item1.construct_meta_json = {
            "domain": "Design Systems",
            "skill_command": "/distill",
            "prompt_index": 1,
        }
        item2 = MagicMock()
        item2.construct_meta_json = {
            "domain": "Design Systems",
            "skill_command": "/distill",
            "prompt_index": 2,
        }

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [item1, item2]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="Incomplete run.*missing evidence items"):
            await adapter.complete_run("inv-001")
