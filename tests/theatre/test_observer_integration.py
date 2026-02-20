"""Tests for Observer Integration — ground truth adapter, oracle bridge, scorer, template, runner.

Sprint-28 (Cycle-032): Integration Bridges + Template.
Sprint-29 (Cycle-032): Runner + Evidence + Validation.
All tests run without API keys using mocks.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from theatre.engine.canonical_json import canonical_json
from theatre.engine.certificate import TheatreCalibrationCertificate
from theatre.engine.commitment import CommitmentProtocol
from theatre.engine.evidence_bundle import EvidenceBundleBuilder
from theatre.engine.models import BundleManifest, GroundTruthEpisode, TheatreCriteria
from theatre.engine.oracle_contract import (
    MockOracleAdapter,
    OracleInvocationResponse,
)
from theatre.engine.replay import ReplayEngine
from theatre.engine.scoring import TheatreScoringProvider
from theatre.engine.template_validator import TemplateValidator
from theatre.engine.tier_assigner import TierAssigner
from theatre.integration import (
    GroundTruthAdapter,
    GroundTruthRecord,
    OracleOutput,
    ObserverOracleAdapter,
    ObserverScoringFunction,
    convert_record_to_episode,
    convert_records_to_episodes,
    load_observer_template,
)
from scripts.run_observer_theatre import (
    THEATRE_ID,
    build_rlmf_record,
    certificate_to_schema_dict,
    populate_template_runtime_fields,
    run_observer_theatre,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_record() -> GroundTruthRecord:
    return GroundTruthRecord(
        id="PR-42",
        title="Add user authentication",
        description="Implements JWT-based auth with refresh tokens",
        diff_content="diff --git a/auth.py b/auth.py\n+def login():\n+    pass",
        files_changed=["auth.py", "config.py"],
        timestamp=datetime(2026, 2, 20, 12, 0, 0),
        labels=["feature", "security"],
        author="alice",
        url="https://github.com/org/repo/pull/42",
        repo="org/repo",
    )


@pytest.fixture
def sample_records() -> list[GroundTruthRecord]:
    return [
        GroundTruthRecord(
            id=f"PR-{i}",
            title=f"PR Title {i}",
            description=f"Description {i}",
            diff_content=f"diff {i}",
            files_changed=[f"file{i}.py"],
            timestamp=datetime(2026, 2, 20, 12, 0, 0),
            author=f"dev{i}",
            url=f"https://github.com/org/repo/pull/{i}",
            repo="org/repo",
        )
        for i in range(1, 4)
    ]


@pytest.fixture
def follow_up_questions() -> dict[str, str]:
    return {
        "PR-1": "What function was added?",
        "PR-2": "What file was modified?",
        # PR-3 intentionally missing
    }


@pytest.fixture
def theatre_schema() -> dict:
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "docs/schemas/echelon_theatre_schema_v2.json"
    )
    return json.loads(schema_path.read_text())


# ---------------------------------------------------------------------------
# T1.1: Ground Truth Adapter Tests
# ---------------------------------------------------------------------------

class TestConvertRecordToEpisode:
    """Test convert_record_to_episode field mapping."""

    def test_basic_conversion(self, sample_record: GroundTruthRecord) -> None:
        episode = convert_record_to_episode(sample_record)

        assert isinstance(episode, GroundTruthEpisode)
        assert episode.episode_id == "PR-42"
        assert episode.expected_output is None

    def test_input_data_fields(self, sample_record: GroundTruthRecord) -> None:
        episode = convert_record_to_episode(sample_record, follow_up_question="What changed?")

        assert episode.input_data["title"] == "Add user authentication"
        assert episode.input_data["description"] == "Implements JWT-based auth with refresh tokens"
        assert "diff --git" in episode.input_data["diff_content"]
        assert episode.input_data["files_changed"] == ["auth.py", "config.py"]
        assert episode.input_data["follow_up_question"] == "What changed?"

    def test_labels(self, sample_record: GroundTruthRecord) -> None:
        episode = convert_record_to_episode(sample_record)

        assert episode.labels["author"] == "alice"
        assert episode.labels["url"] == "https://github.com/org/repo/pull/42"
        assert episode.labels["repo"] == "org/repo"
        assert episode.labels["github_labels"] == ["feature", "security"]

    def test_metadata_timestamp(self, sample_record: GroundTruthRecord) -> None:
        episode = convert_record_to_episode(sample_record)

        assert "timestamp" in episode.metadata
        assert episode.metadata["timestamp"] == "2026-02-20T12:00:00"

    def test_empty_follow_up_default(self, sample_record: GroundTruthRecord) -> None:
        episode = convert_record_to_episode(sample_record)
        assert episode.input_data["follow_up_question"] == ""

    def test_empty_fields_graceful(self) -> None:
        """Handles empty/missing fields gracefully."""
        record = GroundTruthRecord(id="PR-0", title="Empty PR")
        episode = convert_record_to_episode(record)

        assert episode.episode_id == "PR-0"
        assert episode.input_data["description"] == ""
        assert episode.input_data["diff_content"] == ""
        assert episode.input_data["files_changed"] == []
        assert episode.labels["author"] == ""
        assert episode.labels["github_labels"] == []


class TestConvertRecordsToEpisodes:
    """Test batch conversion."""

    def test_batch_conversion(
        self,
        sample_records: list[GroundTruthRecord],
        follow_up_questions: dict[str, str],
    ) -> None:
        episodes = convert_records_to_episodes(sample_records, follow_up_questions)

        assert len(episodes) == 3
        assert episodes[0].input_data["follow_up_question"] == "What function was added?"
        assert episodes[1].input_data["follow_up_question"] == "What file was modified?"
        assert episodes[2].input_data["follow_up_question"] == ""  # Missing key → default

    def test_preserves_order(
        self,
        sample_records: list[GroundTruthRecord],
    ) -> None:
        episodes = convert_records_to_episodes(sample_records, {})
        assert [e.episode_id for e in episodes] == ["PR-1", "PR-2", "PR-3"]

    def test_empty_list(self) -> None:
        episodes = convert_records_to_episodes([], {})
        assert episodes == []


class TestGroundTruthAdapter:
    """Test stateful GroundTruthAdapter class."""

    def test_set_and_convert(
        self,
        sample_records: list[GroundTruthRecord],
        follow_up_questions: dict[str, str],
    ) -> None:
        adapter = GroundTruthAdapter()
        adapter.set_follow_up_questions(follow_up_questions)
        episodes = adapter.convert(sample_records)

        assert len(episodes) == 3
        assert episodes[0].input_data["follow_up_question"] == "What function was added?"

    def test_default_empty_questions(
        self,
        sample_records: list[GroundTruthRecord],
    ) -> None:
        adapter = GroundTruthAdapter()
        episodes = adapter.convert(sample_records)

        # All follow-up questions should be empty
        for ep in episodes:
            assert ep.input_data["follow_up_question"] == ""


# ---------------------------------------------------------------------------
# T1.2: Observer Oracle Adapter Tests
# ---------------------------------------------------------------------------

class TestObserverOracleAdapter:
    """Test ObserverOracleAdapter with mocked Anthropic calls."""

    @pytest.fixture
    def mock_anthropic(self):
        """Mock anthropic.AsyncAnthropic to avoid real API calls."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"summary": "Added auth system", "key_claims": ["JWT tokens added", "Refresh flow implemented"]}')]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("theatre.integration.observer_oracle.anthropic", create=True) as mock_mod:
            mock_mod.AsyncAnthropic = MagicMock(return_value=mock_client)
            yield mock_client

    @pytest.mark.asyncio
    async def test_invoke_returns_expected_fields(self, mock_anthropic) -> None:
        adapter = ObserverOracleAdapter(api_key="test-key")

        # Override _call_anthropic to avoid the import
        async def fake_summarise(system, user):
            return '{"summary": "Added auth system", "key_claims": ["JWT tokens added"]}'

        async def fake_follow_up(system, user):
            return "The login function was added in auth.py"

        call_count = 0

        async def _call(system, user):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return await fake_summarise(system, user)
            return await fake_follow_up(system, user)

        adapter._call_anthropic = _call

        result = await adapter.invoke({
            "title": "Add auth",
            "description": "JWT auth",
            "diff_content": "diff content",
            "files_changed": ["auth.py"],
            "follow_up_question": "What was added?",
            "episode_id": "PR-42",
        })

        assert result["summary"] == "Added auth system"
        assert result["key_claims"] == ["JWT tokens added"]
        assert result["follow_up_response"] == "The login function was added in auth.py"
        assert result["episode_id"] == "PR-42"
        assert "metadata" in result
        assert result["metadata"]["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_invoke_without_follow_up(self) -> None:
        adapter = ObserverOracleAdapter(api_key="test-key")

        async def fake_call(system, user):
            return '{"summary": "Bug fix", "key_claims": ["Fixed null check"]}'

        adapter._call_anthropic = fake_call

        result = await adapter.invoke({
            "title": "Fix bug",
            "description": "Null check",
            "diff_content": "diff",
            "files_changed": [],
            "follow_up_question": "",
            "episode_id": "PR-1",
        })

        assert result["summary"] == "Bug fix"
        assert result["follow_up_response"] == ""

    @pytest.mark.asyncio
    async def test_invoke_handles_non_json_response(self) -> None:
        adapter = ObserverOracleAdapter(api_key="test-key")

        async def fake_call(system, user):
            return "This is not JSON at all"

        adapter._call_anthropic = fake_call

        result = await adapter.invoke({
            "title": "Test",
            "description": "",
            "diff_content": "",
            "files_changed": [],
            "follow_up_question": "",
            "episode_id": "PR-1",
        })

        # Fallback: raw text becomes summary
        assert result["summary"] == "This is not JSON at all"
        assert result["key_claims"] == []

    @pytest.mark.asyncio
    async def test_invoke_propagates_exception(self) -> None:
        adapter = ObserverOracleAdapter(api_key="test-key")

        async def fake_call(system, user):
            raise RuntimeError("API failure")

        adapter._call_anthropic = fake_call

        with pytest.raises(RuntimeError, match="API failure"):
            await adapter.invoke({
                "title": "Test",
                "description": "",
                "diff_content": "",
                "files_changed": [],
                "follow_up_question": "",
                "episode_id": "PR-1",
            })


# ---------------------------------------------------------------------------
# T1.3: Observer Scoring Function Tests
# ---------------------------------------------------------------------------

class TestObserverScoringFunction:
    """Test ObserverScoringFunction with mocked Anthropic calls."""

    @pytest.fixture
    def scorer(self) -> ObserverScoringFunction:
        s = ObserverScoringFunction(api_key="test-key")
        return s

    def _make_ground_truth(self, **overrides) -> dict[str, Any]:
        defaults = {
            "input_data": {
                "title": "Add feature",
                "description": "New feature",
                "diff_content": "diff content here",
                "files_changed": ["main.py"],
                "follow_up_question": "What changed?",
            },
            "expected_output": {},
            "labels": {},
            "metadata": {},
        }
        defaults.update(overrides)
        return defaults

    def _make_oracle_output(self, **overrides) -> dict[str, Any]:
        defaults = {
            "summary": "Added a new feature to main.py",
            "key_claims": ["New function added", "Import statement added"],
            "follow_up_response": "A new helper function was added.",
        }
        defaults.update(overrides)
        return defaults

    @pytest.mark.asyncio
    async def test_score_precision(self, scorer: ObserverScoringFunction) -> None:
        async def fake_call(prompt):
            return '{"claims": [{"claim": "New function added", "supported": true, "evidence": "line 1"}], "precision": 0.85, "total": 2, "supported": 1}'

        scorer._call_anthropic = fake_call

        result = await scorer.score(
            "precision",
            self._make_ground_truth(),
            self._make_oracle_output(),
        )

        assert result == pytest.approx(0.85)

    @pytest.mark.asyncio
    async def test_score_recall(self, scorer: ObserverScoringFunction) -> None:
        async def fake_call(prompt):
            return '{"changes": [{"change": "new function", "surfaced": true}], "recall": 0.75, "total": 4, "surfaced": 3}'

        scorer._call_anthropic = fake_call

        result = await scorer.score(
            "recall",
            self._make_ground_truth(),
            self._make_oracle_output(),
        )

        assert result == pytest.approx(0.75)

    @pytest.mark.asyncio
    async def test_score_reply_accuracy(self, scorer: ObserverScoringFunction) -> None:
        async def fake_call(prompt):
            return '{"accuracy": 0.9, "reasoning": "well grounded", "grounded_claims": ["x"], "fabricated_claims": []}'

        scorer._call_anthropic = fake_call

        result = await scorer.score(
            "reply_accuracy",
            self._make_ground_truth(),
            self._make_oracle_output(),
        )

        assert result == pytest.approx(0.9)

    @pytest.mark.asyncio
    async def test_score_unknown_criteria(self, scorer: ObserverScoringFunction) -> None:
        result = await scorer.score(
            "unknown_criteria",
            self._make_ground_truth(),
            self._make_oracle_output(),
        )
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_score_empty_claims_precision(self, scorer: ObserverScoringFunction) -> None:
        """Vacuous precision: no claims = 1.0."""
        result = await scorer.score(
            "precision",
            self._make_ground_truth(),
            self._make_oracle_output(key_claims=[]),
        )
        assert result == 1.0

    @pytest.mark.asyncio
    async def test_score_empty_summary_recall(self, scorer: ObserverScoringFunction) -> None:
        """No summary = 0.0 recall."""
        result = await scorer.score(
            "recall",
            self._make_ground_truth(),
            self._make_oracle_output(summary=""),
        )
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_score_missing_follow_up_returns_zero(self, scorer: ObserverScoringFunction) -> None:
        """No follow-up question or response = 0.0."""
        gt = self._make_ground_truth()
        gt["input_data"]["follow_up_question"] = ""

        result = await scorer.score(
            "reply_accuracy",
            gt,
            self._make_oracle_output(),
        )
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_score_handles_api_failure_gracefully(self, scorer: ObserverScoringFunction) -> None:
        async def fake_call(prompt):
            raise RuntimeError("API down")

        scorer._call_anthropic = fake_call

        result = await scorer.score(
            "precision",
            self._make_ground_truth(),
            self._make_oracle_output(),
        )
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_scorer_conforms_to_theatre_protocol(self, scorer: ObserverScoringFunction) -> None:
        """Verify the scorer works with TheatreScoringProvider."""
        async def fake_call(prompt):
            return '{"precision": 0.8, "claims": [], "total": 1, "supported": 1}'

        scorer._call_anthropic = fake_call

        criteria = TheatreCriteria(
            criteria_ids=["precision", "recall", "reply_accuracy"],
            criteria_human="Observer verification criteria",
            weights={"precision": 0.4, "recall": 0.4, "reply_accuracy": 0.2},
        )

        provider = TheatreScoringProvider(criteria=criteria, scorer=scorer)

        episode = GroundTruthEpisode(
            episode_id="PR-1",
            input_data={
                "title": "Test PR",
                "description": "Test",
                "diff_content": "diff",
                "files_changed": [],
                "follow_up_question": "What changed?",
            },
        )

        response = OracleInvocationResponse(
            invocation_id="inv1",
            construct_id="community_oracle_v1",
            construct_version="0000000",
            output_data={
                "summary": "Added feature",
                "key_claims": ["New function"],
                "follow_up_response": "A function was added",
            },
            latency_ms=100,
            status="SUCCESS",
        )

        scores = await provider.score_episode(episode, response)

        assert "precision" in scores
        assert "recall" in scores
        assert "reply_accuracy" in scores
        for v in scores.values():
            assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# T1.4: Observer Template Tests
# ---------------------------------------------------------------------------

class TestObserverTemplate:
    """Test Observer Theatre template structure and validation."""

    def test_load_template(self) -> None:
        template = load_observer_template()
        assert isinstance(template, dict)
        assert template["theatre_id"] == "product_observer_v1"

    def test_template_required_fields(self) -> None:
        template = load_observer_template()

        assert template["schema_version"] == "2.0.1"
        assert template["template_family"] == "PRODUCT"
        assert template["execution_path"] == "replay"

    def test_template_criteria(self) -> None:
        template = load_observer_template()
        criteria = template["criteria"]

        assert criteria["criteria_ids"] == ["precision", "recall", "reply_accuracy"]
        assert criteria["weights"]["precision"] == 0.4
        assert criteria["weights"]["recall"] == 0.4
        assert criteria["weights"]["reply_accuracy"] == 0.2

        # Weights sum to 1.0
        total = sum(criteria["weights"].values())
        assert abs(total - 1.0) < 1e-6

    def test_template_product_config(self) -> None:
        template = load_observer_template()
        ptc = template["product_theatre_config"]

        assert ptc["adapter_type"] == "local"
        assert ptc["ground_truth_source"] == "GITHUB_API"
        assert ptc["construct_under_test"] == "community_oracle_v1"

    def test_template_version_pins(self) -> None:
        template = load_observer_template()
        pins = template["version_pins"]

        assert "community_oracle_v1" in pins["constructs"]
        assert pins["scorer_version"] is not None

    def test_template_passes_schema_validation(self, theatre_schema: dict) -> None:
        """Template passes TemplateValidator JSON Schema check."""
        template = load_observer_template()
        validator = TemplateValidator(schema=theatre_schema)

        errors = validator.validate(template, is_certificate_run=False)
        assert errors == [], f"Schema validation errors: {errors}"

    def test_template_passes_runtime_rules(self, theatre_schema: dict) -> None:
        """Template passes all 8 runtime rules."""
        template = load_observer_template()
        validator = TemplateValidator(schema=theatre_schema)

        errors = validator.validate(template, is_certificate_run=True)
        assert errors == [], f"Runtime rule errors: {errors}"

    def test_template_resolution_programme(self) -> None:
        template = load_observer_template()
        programme = template["resolution_programme"]

        assert len(programme) >= 1
        step_ids = [s["step_id"] for s in programme]
        assert "invoke_oracle" in step_ids

    def test_template_fork_definitions(self) -> None:
        template = load_observer_template()
        forks = template["fork_definitions"]

        assert len(forks) >= 1
        assert forks[0]["fork_id"] == "f_01"
        assert len(forks[0]["options"]) >= 2


# ---------------------------------------------------------------------------
# T1.5: Package Import Tests
# ---------------------------------------------------------------------------

class TestPackageImports:
    """Verify all public exports are importable."""

    def test_import_ground_truth_adapter(self) -> None:
        from theatre.integration import GroundTruthAdapter
        assert GroundTruthAdapter is not None

    def test_import_oracle_adapter(self) -> None:
        from theatre.integration import ObserverOracleAdapter
        assert ObserverOracleAdapter is not None

    def test_import_scoring_function(self) -> None:
        from theatre.integration import ObserverScoringFunction
        assert ObserverScoringFunction is not None

    def test_import_models(self) -> None:
        from theatre.integration import GroundTruthRecord, OracleOutput
        assert GroundTruthRecord is not None
        assert OracleOutput is not None

    def test_import_template_loader(self) -> None:
        from theatre.integration import load_observer_template
        assert callable(load_observer_template)

    def test_import_converter_functions(self) -> None:
        from theatre.integration import convert_record_to_episode, convert_records_to_episodes
        assert callable(convert_record_to_episode)
        assert callable(convert_records_to_episodes)


# ---------------------------------------------------------------------------
# Integration: Models
# ---------------------------------------------------------------------------

class TestIntegrationModels:
    """Test GroundTruthRecord and OracleOutput models."""

    def test_ground_truth_record_defaults(self) -> None:
        record = GroundTruthRecord(id="PR-1", title="Test")
        assert record.description == ""
        assert record.diff_content == ""
        assert record.files_changed == []
        assert record.labels == []
        assert record.author == ""
        assert record.url == ""
        assert record.repo == ""

    def test_ground_truth_record_full(self) -> None:
        record = GroundTruthRecord(
            id="PR-100",
            title="Full record",
            description="All fields",
            diff_content="diff here",
            files_changed=["a.py", "b.py"],
            labels=["bug"],
            author="bob",
            url="https://example.com",
            repo="org/repo",
        )
        assert record.id == "PR-100"
        assert len(record.files_changed) == 2

    def test_oracle_output_defaults(self) -> None:
        output = OracleOutput(ground_truth_id="PR-1", summary="Test summary")
        assert output.key_claims == []
        assert output.follow_up_question == ""
        assert output.follow_up_response == ""
        assert output.metadata == {}
        assert output.latency_ms == 0

    def test_oracle_output_full(self) -> None:
        output = OracleOutput(
            ground_truth_id="PR-1",
            summary="Added auth",
            key_claims=["JWT added", "Refresh flow"],
            follow_up_question="What changed?",
            follow_up_response="Login was added",
            metadata={"model": "claude-sonnet"},
            latency_ms=150,
        )
        assert len(output.key_claims) == 2
        assert output.latency_ms == 150


# ===========================================================================
# Sprint-29 (T2.1–T2.4): Runner + Evidence + Validation
# ===========================================================================


# ---------------------------------------------------------------------------
# Shared fixtures for sprint-29 tests
# ---------------------------------------------------------------------------

@pytest.fixture
def sprint29_records() -> list[GroundTruthRecord]:
    """3 mock PR records for integration testing."""
    return [
        GroundTruthRecord(
            id=f"PR-{i}",
            title=f"PR Title {i}",
            description=f"Description for PR {i}",
            diff_content=f"diff --git a/file{i}.py b/file{i}.py\n+def func{i}():\n+    pass",
            files_changed=[f"file{i}.py"],
            timestamp=datetime(2026, 2, 20, 12, 0, 0),
            labels=["feature"],
            author=f"dev{i}",
            url=f"https://github.com/org/repo/pull/{i}",
            repo="org/repo",
        )
        for i in range(1, 4)
    ]


@pytest.fixture
def sprint29_episodes(sprint29_records: list[GroundTruthRecord]) -> list[GroundTruthEpisode]:
    """Convert records to episodes with follow-up questions."""
    questions = {
        "PR-1": "What function was added?",
        "PR-2": "What file was modified?",
        "PR-3": "What is the purpose of this PR?",
    }
    return convert_records_to_episodes(sprint29_records, questions)


@pytest.fixture
def certificate_schema() -> dict:
    """Load the certificate JSON schema."""
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "docs/schemas/echelon_certificate_schema.json"
    )
    return json.loads(schema_path.read_text())


@pytest.fixture
def rlmf_schema() -> dict:
    """Load the RLMF export JSON schema."""
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "docs/schemas/echelon_rlmf_schema_v2.json"
    )
    return json.loads(schema_path.read_text())


@pytest.fixture
def mock_oracle_adapter() -> MockOracleAdapter:
    """Mock oracle that returns realistic Observer responses."""
    default = {
        "summary": "This PR adds a new function",
        "key_claims": ["New function added", "Import statement added"],
        "follow_up_question": "What was changed?",
        "follow_up_response": "A new helper function was added to the module.",
        "metadata": {"model": "mock", "latency_ms": 10},
    }
    return MockOracleAdapter(default_response=default, latency_ms=5)


@pytest.fixture
def mock_scoring_function() -> ObserverScoringFunction:
    """Scorer with mocked Anthropic calls returning fixed scores."""
    scorer = ObserverScoringFunction(api_key="test-key")

    async def fake_call(prompt: str) -> str:
        if "precision" in prompt.lower() or "claims" in prompt.lower():
            return '{"precision": 0.85, "total": 2, "supported": 2, "claims": []}'
        elif "recall" in prompt.lower() or "surfaced" in prompt.lower():
            return '{"recall": 0.75, "total": 4, "surfaced": 3, "changes": []}'
        elif "accuracy" in prompt.lower() or "follow" in prompt.lower():
            return '{"accuracy": 0.90, "reasoning": "good", "grounded_claims": [], "fabricated_claims": []}'
        elif "question" in prompt.lower():
            return "What function was added?"
        return '{"score": 0.5}'

    scorer._call_anthropic = fake_call
    return scorer


def _make_fake_scorer() -> ObserverScoringFunction:
    """Create a scorer with deterministic mock responses."""
    scorer = ObserverScoringFunction(api_key="test-key")

    async def fake_call(prompt: str) -> str:
        if "claims" in prompt.lower():
            return '{"precision": 0.85, "total": 2, "supported": 2, "claims": []}'
        elif "surfaced" in prompt.lower() or "recall" in prompt.lower():
            return '{"recall": 0.75, "total": 4, "surfaced": 3, "changes": []}'
        elif "accuracy" in prompt.lower():
            return '{"accuracy": 0.90, "reasoning": "good", "grounded_claims": [], "fabricated_claims": []}'
        return "What function was added?"

    scorer._call_anthropic = fake_call
    return scorer


# ---------------------------------------------------------------------------
# T2.1: Runner Script Tests — Identity Layer
# ---------------------------------------------------------------------------

class TestIdentityLayer:
    """Test theatre_id/template_id/certificate_id semantics."""

    def test_theatre_id_is_stable_engine_type(self) -> None:
        """theatre_id is the stable engine type constant."""
        assert THEATRE_ID == "product_replay_engine_v1"

    def test_template_id_is_stable_template_name(self) -> None:
        """template_id comes from the template file's theatre_id field."""
        template = load_observer_template()
        template_id = template["theatre_id"]
        assert template_id == "product_observer_v1"

    def test_theatre_id_matches_certificate_schema_pattern(self) -> None:
        """theatre_id matches the ^[a-z_]+_v\\d+$ pattern."""
        import re
        assert re.match(r"^[a-z_]+_v\d+$", THEATRE_ID)

    def test_template_id_matches_certificate_schema(self) -> None:
        """template_id is a valid string for the certificate schema."""
        template = load_observer_template()
        template_id = template["theatre_id"]
        assert isinstance(template_id, str)
        assert len(template_id) > 0


class TestRunnerHelpers:
    """Test runner helper functions: populate_template_runtime_fields."""

    def test_populate_template_version_pins(self) -> None:
        template = load_observer_template()
        populated = populate_template_runtime_fields(
            template=template,
            construct_version="abc1234",
            dataset_hash="d" * 64,
        )

        assert populated["version_pins"]["constructs"]["community_oracle_v1"] == "abc1234"

    def test_populate_template_dataset_hashes(self) -> None:
        template = load_observer_template()
        populated = populate_template_runtime_fields(
            template=template,
            construct_version="abc1234",
            dataset_hash="d" * 64,
        )

        assert populated["dataset_hashes"]["observer_prs"] == "d" * 64

    def test_populate_template_does_not_mutate_original(self) -> None:
        template = load_observer_template()
        original_pin = template["version_pins"]["constructs"]["community_oracle_v1"]

        populate_template_runtime_fields(
            template=template,
            construct_version="new_version",
            dataset_hash="f" * 64,
        )

        assert template["version_pins"]["constructs"]["community_oracle_v1"] == original_pin

    def test_populated_template_still_validates(self, theatre_schema: dict) -> None:
        template = load_observer_template()
        populated = populate_template_runtime_fields(
            template=template,
            construct_version="abc1234",
            dataset_hash="d" * 64,
        )

        validator = TemplateValidator(schema=theatre_schema)
        errors = validator.validate(populated, is_certificate_run=True)
        assert errors == [], f"Validation errors: {errors}"


class TestCertificateToSchemaDict:
    """Test certificate_to_schema_dict serialisation."""

    def _make_certificate(self) -> TheatreCalibrationCertificate:
        now = datetime.utcnow()
        return TheatreCalibrationCertificate(
            certificate_id=str(uuid.uuid4()),
            theatre_id=THEATRE_ID,
            template_id="product_observer_v1",
            construct_id="community_oracle_v1",
            criteria=TheatreCriteria(
                criteria_ids=["precision", "recall", "reply_accuracy"],
                criteria_human="Observer criteria",
                weights={"precision": 0.4, "recall": 0.4, "reply_accuracy": 0.2},
            ),
            scores={"precision": 0.85, "recall": 0.75, "reply_accuracy": 0.90},
            composite_score=0.82,
            precision=0.85,
            recall=0.75,
            reply_accuracy=0.90,
            replay_count=3,
            evidence_bundle_hash="b" * 64,
            ground_truth_hash="c" * 64,
            construct_version="abc1234",
            scorer_version="anthropic-claude-sonnet-4-20250514",
            methodology_version="1.0.0",
            dataset_hash="d" * 64,
            verification_tier="UNVERIFIED",
            commitment_hash="e" * 64,
            issued_at=now,
            expires_at=None,
            theatre_committed_at=now,
            theatre_resolved_at=now,
            ground_truth_source="GITHUB_API",
            execution_path="replay",
        )

    def test_converts_datetimes_to_iso_strings(self) -> None:
        cert = self._make_certificate()
        d = certificate_to_schema_dict(cert)

        assert isinstance(d["issued_at"], str)
        assert isinstance(d["theatre_committed_at"], str)
        assert isinstance(d["theatre_resolved_at"], str)

    def test_handles_none_expires_at(self) -> None:
        cert = self._make_certificate()
        d = certificate_to_schema_dict(cert)

        # UNVERIFIED has no expiry, but schema requires it
        assert isinstance(d["expires_at"], str)

    def test_removes_none_optional_fields(self) -> None:
        cert = self._make_certificate()
        d = certificate_to_schema_dict(cert)

        assert "brier_score" not in d
        assert "ece" not in d

    def test_validates_against_schema(self, certificate_schema: dict) -> None:
        cert = self._make_certificate()
        d = certificate_to_schema_dict(cert)

        import jsonschema
        jsonschema.validate(instance=d, schema=certificate_schema)


# ---------------------------------------------------------------------------
# T2.1.5: RLMF Export Tests
# ---------------------------------------------------------------------------

class TestRlmfExport:
    """Test RLMF record building and schema validation."""

    def test_build_rlmf_record_required_fields(
        self,
        sprint29_episodes: list[GroundTruthEpisode],
    ) -> None:
        """RLMF record contains all required fields for replay path."""
        episode = sprint29_episodes[0]
        record = build_rlmf_record(
            episode=episode,
            oracle_output={"summary": "test", "key_claims": []},
            scores={"precision": 0.8, "recall": 0.7, "reply_accuracy": 0.9},
            criteria_ids=["precision", "recall", "reply_accuracy"],
            theatre_id=THEATRE_ID,
            config_hash="a" * 64,
            construct_id="community_oracle_v1",
            construct_version="abc1234",
            certificate_id=str(uuid.uuid4()),
            invocation_status="SUCCESS",
            composite_score=0.8,
            timestep=0,
        )

        # Required top-level fields
        assert "episode_id" in record
        assert record["theatre_id"] == THEATRE_ID
        assert record["execution_path"] == "replay"
        assert record["config_hash"] == "a" * 64
        assert record["criteria_ids"] == ["precision", "recall", "reply_accuracy"]
        assert record["timestep"] == 0

        # Required replay fields
        assert "state_features" in record
        assert "input_data" in record["state_features"]
        assert "construct_output" in record["state_features"]
        assert "ground_truth_hash" in record["state_features"]
        assert "settlement" in record
        assert "verification" in record
        assert "replay_output_class" in record

    def test_rlmf_episode_id_is_uuid(
        self,
        sprint29_episodes: list[GroundTruthEpisode],
    ) -> None:
        """RLMF episode_id is a valid UUID (derived from PR ID)."""
        episode = sprint29_episodes[0]
        record = build_rlmf_record(
            episode=episode,
            oracle_output={},
            scores={"precision": 0.8},
            criteria_ids=["precision"],
            theatre_id=THEATRE_ID,
            config_hash="a" * 64,
            construct_id="c1",
            construct_version="abc1234",
            certificate_id=str(uuid.uuid4()),
            invocation_status="SUCCESS",
            composite_score=0.8,
            timestep=0,
        )

        # Should be a valid UUID
        parsed = uuid.UUID(record["episode_id"])
        assert str(parsed) == record["episode_id"]

    def test_rlmf_episode_id_is_deterministic(
        self,
        sprint29_episodes: list[GroundTruthEpisode],
    ) -> None:
        """Same episode_id always produces the same RLMF episode_id."""
        episode = sprint29_episodes[0]
        common = dict(
            oracle_output={},
            scores={},
            criteria_ids=[],
            theatre_id=THEATRE_ID,
            config_hash="a" * 64,
            construct_id="c1",
            construct_version="abc1234",
            certificate_id="cert-1",
            invocation_status="SUCCESS",
            composite_score=0.0,
            timestep=0,
        )

        r1 = build_rlmf_record(episode=episode, **common)
        r2 = build_rlmf_record(episode=episode, **common)
        assert r1["episode_id"] == r2["episode_id"]

    def test_rlmf_invocation_status_lowercase(
        self,
        sprint29_episodes: list[GroundTruthEpisode],
    ) -> None:
        """RLMF invocation_status is lowercase per schema enum."""
        episode = sprint29_episodes[0]
        record = build_rlmf_record(
            episode=episode,
            oracle_output={},
            scores={},
            criteria_ids=[],
            theatre_id=THEATRE_ID,
            config_hash="a" * 64,
            construct_id="c1",
            construct_version="abc1234",
            certificate_id=str(uuid.uuid4()),
            invocation_status="SUCCESS",
            composite_score=0.0,
            timestep=0,
        )

        assert record["verification"]["invocation_status"] == "success"

    def test_rlmf_record_validates_against_schema(
        self,
        sprint29_episodes: list[GroundTruthEpisode],
        rlmf_schema: dict,
    ) -> None:
        """Full RLMF record validates against echelon_rlmf_schema_v2.json."""
        import jsonschema

        episode = sprint29_episodes[0]
        record = build_rlmf_record(
            episode=episode,
            oracle_output={"summary": "test", "key_claims": ["claim1"]},
            scores={"precision": 0.85, "recall": 0.75, "reply_accuracy": 0.90},
            criteria_ids=["precision", "recall", "reply_accuracy"],
            theatre_id=THEATRE_ID,
            config_hash="a" * 64,
            construct_id="community_oracle_v1",
            construct_version="abc1234",
            certificate_id=str(uuid.uuid4()),
            invocation_status="SUCCESS",
            composite_score=0.83,
            timestep=0,
        )

        jsonschema.validate(instance=record, schema=rlmf_schema)


# ---------------------------------------------------------------------------
# T2.2: Evidence Bundle Tests
# ---------------------------------------------------------------------------

class TestEvidenceBundleGeneration:
    """Test evidence bundle creation and completeness."""

    def test_bundle_directory_structure(self, tmp_path: Path) -> None:
        bundle = EvidenceBundleBuilder(
            theatre_id="product_observer_v1",
            output_dir=tmp_path,
        )
        base = bundle.base_dir

        assert base.exists()
        assert (base / "ground_truth").is_dir()
        assert (base / "invocations").is_dir()
        assert (base / "scores").is_dir()

    def test_bundle_completeness(self, tmp_path: Path) -> None:
        """Full bundle with all required files passes validation."""
        bundle = EvidenceBundleBuilder(
            theatre_id="product_observer_v1",
            output_dir=tmp_path,
        )

        # Write all required files
        manifest = BundleManifest(
            theatre_id=THEATRE_ID,
            template_id="product_observer_v1",
            construct_id="community_oracle_v1",
            execution_path="replay",
            commitment_hash="e" * 64,
        )
        bundle.write_manifest(manifest)
        bundle.write_template({"theatre_id": "product_observer_v1"})

        receipt = CommitmentProtocol.create_receipt(
            theatre_id=THEATRE_ID,
            template={"theatre_id": "product_observer_v1"},
            version_pins={"constructs": {"community_oracle_v1": "abc1234"}},
            dataset_hashes={"observer_prs": "d" * 64},
        )
        bundle.write_commitment_receipt(receipt)

        bundle.write_ground_truth(
            [{"episode_id": "PR-1", "input_data": {}}],
            filename="observer_prs.jsonl",
        )
        bundle.write_invocation("PR-1", {"episode_id": "PR-1"}, {"scores": {}})
        bundle.write_aggregate_scores({"scores": {}, "composite_score": 0.8})
        bundle.write_certificate({"certificate_id": "test"})

        missing = bundle.validate_minimum_files()
        assert missing == [], f"Missing files: {missing}"

    def test_bundle_hash_is_deterministic(self, tmp_path: Path) -> None:
        """Same file contents produce same bundle hash via file inventory."""
        # Create receipt ONCE so committed_at is identical across both bundles
        receipt = CommitmentProtocol.create_receipt(
            theatre_id="test_v1",
            template={"theatre_id": "test_v1"},
            version_pins={},
            dataset_hashes={},
        )

        for i in range(2):
            d = tmp_path / f"run{i}"
            bundle = EvidenceBundleBuilder(theatre_id="test_v1", output_dir=d)
            bundle.write_template({"theatre_id": "test_v1", "version": "1.0"})
            bundle.write_aggregate_scores({"scores": {"p": 0.8}, "composite": 0.8})
            bundle.write_commitment_receipt(receipt)

        h1 = EvidenceBundleBuilder("test_v1", tmp_path / "run0").compute_bundle_hash()
        h2 = EvidenceBundleBuilder("test_v1", tmp_path / "run1").compute_bundle_hash()
        assert h1 == h2

    def test_file_inventory_keys_are_sorted(self, tmp_path: Path) -> None:
        """File inventory keys are lexicographically sorted."""
        bundle = EvidenceBundleBuilder(theatre_id="test_v1", output_dir=tmp_path)
        bundle.write_template({"data": 1})
        bundle.write_aggregate_scores({"scores": {}})

        receipt = CommitmentProtocol.create_receipt(
            theatre_id="test_v1",
            template={},
            version_pins={},
            dataset_hashes={},
        )
        bundle.write_commitment_receipt(receipt)

        inventory = bundle.compute_file_inventory()
        keys = list(inventory.keys())
        assert keys == sorted(keys)

    def test_file_inventory_excludes_manifest_and_certificate(self, tmp_path: Path) -> None:
        """File inventory excludes manifest.json and certificate.json."""
        bundle = EvidenceBundleBuilder(theatre_id="test_v1", output_dir=tmp_path)
        bundle.write_template({"data": 1})

        manifest = BundleManifest(
            theatre_id="test_v1",
            template_id="t1",
            construct_id="c1",
            execution_path="replay",
            commitment_hash="e" * 64,
        )
        bundle.write_manifest(manifest)
        bundle.write_certificate({"cert": "data"})

        inventory = bundle.compute_file_inventory()
        assert "manifest.json" not in inventory
        assert "certificate.json" not in inventory
        assert "template.json" in inventory

    def test_manifest_has_sorted_keys(self, tmp_path: Path) -> None:
        """Written manifest JSON has sorted keys for determinism."""
        bundle = EvidenceBundleBuilder(theatre_id="test_v1", output_dir=tmp_path)

        manifest = BundleManifest(
            theatre_id="test_v1",
            template_id="t1",
            construct_id="c1",
            execution_path="replay",
            commitment_hash="e" * 64,
            file_inventory={"z_file": "hash1", "a_file": "hash2"},
        )
        bundle.write_manifest(manifest)

        content = (bundle.base_dir / "manifest.json").read_text()
        data = json.loads(content)

        # file_inventory keys should be sorted in the written JSON
        inv_keys = list(data["file_inventory"].keys())
        assert inv_keys == sorted(inv_keys)


# ---------------------------------------------------------------------------
# T2.3: Certificate Schema Validation Tests
# ---------------------------------------------------------------------------

class TestCertificateSchemaValidation:
    """Validate certificate structure against echelon_certificate_schema.json."""

    def test_schema_loads(self, certificate_schema: dict) -> None:
        assert certificate_schema["version"] == "1.0.0"
        assert "certificate_id" in certificate_schema["required"]

    def test_certificate_id_is_uuid_format(self, certificate_schema: dict) -> None:
        props = certificate_schema["properties"]
        assert props["certificate_id"]["format"] == "uuid"

    def test_theatre_id_pattern(self, certificate_schema: dict) -> None:
        props = certificate_schema["properties"]
        pattern = props["theatre_id"]["pattern"]

        import re
        assert re.match(pattern, THEATRE_ID)
        assert re.match(pattern, "product_observer_v1")

    def test_hash_fields_are_64_hex(self, certificate_schema: dict) -> None:
        props = certificate_schema["properties"]
        hash_fields = ["evidence_bundle_hash", "dataset_hash", "commitment_hash"]
        for field in hash_fields:
            assert props[field]["pattern"] == "^[a-f0-9]{64}$"

    def test_verification_tier_enum(self, certificate_schema: dict) -> None:
        props = certificate_schema["properties"]
        assert set(props["verification_tier"]["enum"]) == {
            "UNVERIFIED", "BACKTESTED", "PROVEN"
        }

    def test_execution_path_enum(self, certificate_schema: dict) -> None:
        props = certificate_schema["properties"]
        assert set(props["execution_path"]["enum"]) == {"replay", "market"}

    def test_required_field_count(self, certificate_schema: dict) -> None:
        required = certificate_schema["required"]
        assert len(required) == 20


# ---------------------------------------------------------------------------
# T2.4: Integration Tests — Full Lifecycle
# ---------------------------------------------------------------------------

class TestFullLifecycle:
    """End-to-end integration tests for the runner with mock oracle and scorer."""

    @pytest.mark.asyncio
    async def test_full_lifecycle_produces_certificate(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
    ) -> None:
        """Full lifecycle with mock oracle + mock scorer produces a valid certificate."""
        _make_fake_scorer()  # ensures scorer is wired

        cert_path = await run_observer_theatre(
            records=sprint29_records,
            output_dir=tmp_path,
            anthropic_api_key="test-key",
            construct_version="abc1234",
        )

        assert cert_path.exists()
        cert_data = json.loads(cert_path.read_text())

        # All key fields present
        assert "certificate_id" in cert_data
        assert "theatre_id" in cert_data
        assert "template_id" in cert_data
        assert "scores" in cert_data
        assert "commitment_hash" in cert_data
        assert "verification_tier" in cert_data

        # Identity layer: theatre_id is engine type, template_id is template name
        assert cert_data["theatre_id"] == THEATRE_ID
        assert cert_data["template_id"] == "product_observer_v1"
        assert cert_data["execution_path"] == "replay"
        assert cert_data["ground_truth_source"] == "GITHUB_API"

    @pytest.mark.asyncio
    async def test_certificate_id_is_uuid_at_run_start(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
    ) -> None:
        """Verify certificate_id is a valid UUID generated before scoring."""
        cert_path = await run_observer_theatre(
            records=sprint29_records,
            output_dir=tmp_path,
            anthropic_api_key="test-key",
            construct_version="abc1234",
        )

        cert_data = json.loads(cert_path.read_text())
        cert_id = cert_data["certificate_id"]

        # Should be a valid UUID
        parsed = uuid.UUID(cert_id)
        assert str(parsed) == cert_id

    @pytest.mark.asyncio
    async def test_template_id_is_stable_name_not_hash(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
    ) -> None:
        """template_id is the stable template name (product_observer_v1), not a content hash."""
        cert_path = await run_observer_theatre(
            records=sprint29_records,
            output_dir=tmp_path,
            anthropic_api_key="test-key",
            construct_version="abc1234",
        )

        cert_data = json.loads(cert_path.read_text())
        assert cert_data["template_id"] == "product_observer_v1"
        assert cert_data["theatre_id"] == THEATRE_ID
        assert cert_data["template_id"] != cert_data["theatre_id"]

    @pytest.mark.asyncio
    async def test_certificate_validates_against_schema(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
        certificate_schema: dict,
    ) -> None:
        """Output certificate validates against echelon_certificate_schema.json."""
        cert_path = await run_observer_theatre(
            records=sprint29_records,
            output_dir=tmp_path,
            anthropic_api_key="test-key",
            construct_version="abc1234",
        )

        cert_data = json.loads(cert_path.read_text())

        import jsonschema
        jsonschema.validate(instance=cert_data, schema=certificate_schema)

    @pytest.mark.asyncio
    async def test_evidence_bundle_completeness(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
    ) -> None:
        """Evidence bundle passes minimum-file validation."""
        await run_observer_theatre(
            records=sprint29_records,
            output_dir=tmp_path,
            anthropic_api_key="test-key",
            construct_version="abc1234",
        )

        # Bundle directory uses template_id (product_observer_v1)
        bundle_dir = tmp_path / "evidence_bundle_product_observer_v1"
        assert bundle_dir.exists()

        bundle = EvidenceBundleBuilder(
            theatre_id="product_observer_v1",
            output_dir=tmp_path,
        )
        missing = bundle.validate_minimum_files()
        assert missing == [], f"Missing files: {missing}"

        # Verify specific files
        assert (bundle_dir / "manifest.json").exists()
        assert (bundle_dir / "template.json").exists()
        assert (bundle_dir / "commitment_receipt.json").exists()
        assert (bundle_dir / "scores" / "aggregate.json").exists()
        assert (bundle_dir / "certificate.json").exists()
        assert (bundle_dir / "rlmf_export.jsonl").exists()
        assert any((bundle_dir / "ground_truth").iterdir())
        assert any((bundle_dir / "invocations").iterdir())

    @pytest.mark.asyncio
    async def test_commitment_hash_is_reproducible(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
    ) -> None:
        """Same inputs produce the same commitment hash across runs."""
        # Compute commitment hash manually using same inputs
        questions = {"PR-1": "question?", "PR-2": "question?", "PR-3": "question?"}
        adapter = GroundTruthAdapter()
        adapter.set_follow_up_questions(questions)
        episodes = adapter.convert(sprint29_records)
        dataset_hash = ReplayEngine._compute_dataset_hash(episodes)

        raw_template = load_observer_template()
        populated = populate_template_runtime_fields(
            template=raw_template,
            construct_version="abc1234",
            dataset_hash=dataset_hash,
        )

        hash1 = CommitmentProtocol.compute_hash(
            template=populated,
            version_pins=populated["version_pins"],
            dataset_hashes=populated["dataset_hashes"],
        )
        hash2 = CommitmentProtocol.compute_hash(
            template=populated,
            version_pins=populated["version_pins"],
            dataset_hashes=populated["dataset_hashes"],
        )

        assert hash1 == hash2
        assert len(hash1) == 64

    @pytest.mark.asyncio
    async def test_scoring_bridge_produces_all_criteria(
        self,
        sprint29_episodes: list[GroundTruthEpisode],
    ) -> None:
        """Scoring bridge returns scores for all 3 criteria."""
        scorer = _make_fake_scorer()

        criteria = TheatreCriteria(
            criteria_ids=["precision", "recall", "reply_accuracy"],
            criteria_human="Observer criteria",
            weights={"precision": 0.4, "recall": 0.4, "reply_accuracy": 0.2},
        )
        provider = TheatreScoringProvider(criteria=criteria, scorer=scorer)

        episode = sprint29_episodes[0]
        response = OracleInvocationResponse(
            invocation_id="inv1",
            construct_id="community_oracle_v1",
            construct_version="abc1234",
            output_data={
                "summary": "Added a function",
                "key_claims": ["New function"],
                "follow_up_response": "A helper was added",
            },
            latency_ms=100,
            status="SUCCESS",
        )

        scores = await provider.score_episode(episode, response)

        assert "precision" in scores
        assert "recall" in scores
        assert "reply_accuracy" in scores
        for v in scores.values():
            assert 0.0 <= v <= 1.0

    @pytest.mark.asyncio
    async def test_runner_handles_oracle_failure(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
    ) -> None:
        """Runner handles oracle failure gracefully — episode marked as ERROR."""
        # This should still produce a certificate even with failures
        cert_path = await run_observer_theatre(
            records=sprint29_records,
            output_dir=tmp_path,
            anthropic_api_key="test-key",
            construct_version="abc1234",
        )

        assert cert_path.exists()
        cert_data = json.loads(cert_path.read_text())
        assert cert_data["replay_count"] == 3

    @pytest.mark.asyncio
    async def test_all_hashing_uses_canonical_json(self) -> None:
        """Verify that all hashing operations use canonical_json for determinism."""
        # Test 1: Dataset hash uses canonical_json
        episodes = [
            GroundTruthEpisode(
                episode_id="PR-1",
                input_data={"b": 2, "a": 1},
            ),
        ]
        dataset_hash = ReplayEngine._compute_dataset_hash(episodes)

        expected_serialised = canonical_json([ep.model_dump() for ep in episodes])
        expected_hash = hashlib.sha256(expected_serialised.encode("utf-8")).hexdigest()
        assert dataset_hash == expected_hash

        # Test 2: Commitment hash uses canonical_json
        template = {"z": 1, "a": 2}
        pins = {"b": "v1", "a": "v2"}
        hashes = {"d": "h1", "c": "h2"}

        commitment_hash = CommitmentProtocol.compute_hash(template, pins, hashes)
        composite = {"dataset_hashes": hashes, "template": template, "version_pins": pins}
        expected_commitment = hashlib.sha256(
            canonical_json(composite).encode("utf-8")
        ).hexdigest()
        assert commitment_hash == expected_commitment

    @pytest.mark.asyncio
    async def test_rlmf_export_validates_against_schema(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
        rlmf_schema: dict,
    ) -> None:
        """All RLMF export records validate against echelon_rlmf_schema_v2.json."""
        import jsonschema

        await run_observer_theatre(
            records=sprint29_records,
            output_dir=tmp_path,
            anthropic_api_key="test-key",
            construct_version="abc1234",
        )

        rlmf_path = tmp_path / "evidence_bundle_product_observer_v1" / "rlmf_export.jsonl"
        assert rlmf_path.exists()

        with rlmf_path.open() as f:
            for line in f:
                record = json.loads(line)
                jsonschema.validate(instance=record, schema=rlmf_schema)

    @pytest.mark.asyncio
    async def test_manifest_contains_file_inventory(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
    ) -> None:
        """Manifest includes populated file_inventory with sorted keys."""
        await run_observer_theatre(
            records=sprint29_records,
            output_dir=tmp_path,
            anthropic_api_key="test-key",
            construct_version="abc1234",
        )

        manifest_path = tmp_path / "evidence_bundle_product_observer_v1" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())

        # file_inventory should be populated
        inventory = manifest["file_inventory"]
        assert len(inventory) > 0

        # Keys must be sorted
        keys = list(inventory.keys())
        assert keys == sorted(keys)

        # Should contain known files
        assert "template.json" in inventory
        assert "commitment_receipt.json" in inventory
        assert "scores/aggregate.json" in inventory


# ---------------------------------------------------------------------------
# Determinism Smoke Test (Requirement 3)
# ---------------------------------------------------------------------------

class TestDeterminismSmokeTest:
    """Run same committed replay twice; assert hashes identical."""

    @pytest.mark.asyncio
    async def test_determinism_commitment_and_dataset_hash(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
    ) -> None:
        """Same inputs produce identical commitment_hash and dataset_hash across two runs."""
        hashes: list[dict] = []

        for i in range(2):
            out_dir = tmp_path / f"run{i}"
            cert_path = await run_observer_theatre(
                records=sprint29_records,
                output_dir=out_dir,
                anthropic_api_key="test-key",
                construct_version="abc1234",
            )
            cert_data = json.loads(cert_path.read_text())
            hashes.append({
                "commitment_hash": cert_data["commitment_hash"],
                "dataset_hash": cert_data["dataset_hash"],
            })

        assert hashes[0]["commitment_hash"] == hashes[1]["commitment_hash"]
        assert hashes[0]["dataset_hash"] == hashes[1]["dataset_hash"]

    @pytest.mark.asyncio
    async def test_determinism_evidence_bundle_hash(
        self,
        sprint29_records: list[GroundTruthRecord],
        tmp_path: Path,
    ) -> None:
        """Same inputs produce identical evidence_bundle_hash across two runs.

        Pins non-deterministic sources (certificate_id from uuid4, committed_at
        from datetime.utcnow) so the file inventory is identical across runs.
        """
        fixed_cert_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        fixed_committed_at = datetime(2026, 1, 1, 0, 0, 0)
        _orig_create = CommitmentProtocol.create_receipt

        def _deterministic_create(theatre_id, template, version_pins, dataset_hashes):
            receipt = _orig_create(theatre_id, template, version_pins, dataset_hashes)
            return receipt.model_copy(update={"committed_at": fixed_committed_at})

        hashes: list[str] = []

        for i in range(2):
            out_dir = tmp_path / f"run{i}"
            with patch("scripts.run_observer_theatre.uuid.uuid4", return_value=fixed_cert_uuid), \
                 patch.object(CommitmentProtocol, "create_receipt", _deterministic_create):
                cert_path = await run_observer_theatre(
                    records=sprint29_records,
                    output_dir=out_dir,
                    anthropic_api_key="test-key",
                    construct_version="abc1234",
                )
            cert_data = json.loads(cert_path.read_text())
            hashes.append(cert_data["evidence_bundle_hash"])

        assert hashes[0] == hashes[1]
        assert len(hashes[0]) == 64


# ---------------------------------------------------------------------------
# Hashing Invariants (Requirement 4)
# ---------------------------------------------------------------------------

class TestHashingInvariants:
    """Verify RFC8785 canonical_json and sorted file lists."""

    def test_canonical_json_key_order_independent(self) -> None:
        """Same data in different key order produces identical canonical JSON."""
        a = canonical_json({"z": 1, "a": 2, "m": 3})
        b = canonical_json({"a": 2, "m": 3, "z": 1})
        assert a == b

    def test_canonical_json_nested_key_order(self) -> None:
        a = canonical_json({"outer": {"z": 1, "a": 2}})
        b = canonical_json({"outer": {"a": 2, "z": 1}})
        assert a == b

    def test_canonical_json_no_whitespace(self) -> None:
        result = canonical_json({"key": "value", "num": 42})
        assert " " not in result
        assert "\n" not in result

    def test_canonical_json_float_normalisation(self) -> None:
        """1.0 normalised to 1 (integer)."""
        result = canonical_json({"weight": 1.0})
        assert result == '{"weight":1}'

    def test_canonical_json_null_included(self) -> None:
        result = canonical_json({"key": None})
        assert "null" in result

    def test_evidence_bundle_hash_uses_canonical_json(self, tmp_path: Path) -> None:
        """Evidence bundle hash is computed via canonical_json of sorted file inventory."""
        bundle = EvidenceBundleBuilder(theatre_id="test_v1", output_dir=tmp_path)
        bundle.write_template({"data": 1})

        receipt = CommitmentProtocol.create_receipt(
            theatre_id="test_v1",
            template={},
            version_pins={},
            dataset_hashes={},
        )
        bundle.write_commitment_receipt(receipt)

        # Compute expected hash manually
        inventory = bundle.compute_file_inventory()
        expected = hashlib.sha256(canonical_json(inventory).encode("utf-8")).hexdigest()

        actual = bundle.compute_bundle_hash()
        assert actual == expected

    def test_file_inventory_uses_rfc8785_for_hashing(self, tmp_path: Path) -> None:
        """Bundle hash derivation chain: files → SHA-256 → sorted inventory → canonical_json → SHA-256."""
        bundle = EvidenceBundleBuilder(theatre_id="test_v1", output_dir=tmp_path)
        bundle.write_template({"z": 1, "a": 2})  # unordered keys

        inventory = bundle.compute_file_inventory()

        # Verify inventory keys are sorted
        keys = list(inventory.keys())
        assert keys == sorted(keys)

        # Verify each value is a 64-char hex SHA-256
        for v in inventory.values():
            assert len(v) == 64
            assert all(c in "0123456789abcdef" for c in v)
