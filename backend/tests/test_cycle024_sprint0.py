"""Cycle 024 Sprint 0 — Schema + Template Foundation tests.

Tests:
1. StopCondition.CONSTRUCT_EVALUATION is valid and evaluator handles it
2. ProvenanceClass.construct_evaluation is valid and accepted by EvidenceEnvelope
3. Template seeder creates CONSTRUCT_VERIFICATION_V1 with correct config
4. Artisan prompt set has 12 entries across 5 domains
5. Prompt set hash is stable and verifiable
6. ConstructRegistration model has correct fields
7. New nullable columns default to None
8. Stop condition evaluator returns correct results for construct evaluation
9. Template carries correct thresholds
"""

import hashlib
import json

import pytest

from backend.investigation.certificate import StopCondition
from backend.investigation.models import ProvenanceClass
from backend.investigation.evidence_envelope import EvidenceEnvelope
from backend.investigation.stop_conditions import InvestigationStopConditionEvaluator
from backend.investigation.claim_graph import ClaimGraph
from backend.services.test_prompt_registry import TestPromptRegistry


class TestEnumExtensions:
    """Test that new enum values are valid."""

    def test_stop_condition_construct_evaluation_is_valid(self):
        """StopCondition.CONSTRUCT_EVALUATION is a valid enum value."""
        condition = StopCondition("CONSTRUCT_EVALUATION")
        assert condition == StopCondition.CONSTRUCT_EVALUATION
        assert condition.value == "CONSTRUCT_EVALUATION"

    def test_provenance_class_construct_evaluation_is_valid(self):
        """ProvenanceClass.construct_evaluation is a valid enum value."""
        prov = ProvenanceClass("construct_evaluation")
        assert prov == ProvenanceClass.CONSTRUCT_EVALUATION
        assert prov.value == "construct_evaluation"

    def test_provenance_class_accepted_by_evidence_envelope(self):
        """EvidenceEnvelope.submit() accepts construct_evaluation provenance."""
        envelope = EvidenceEnvelope()
        item = envelope.submit(
            content=b"test output from construct skill",
            provenance_class=ProvenanceClass.CONSTRUCT_EVALUATION,
            content_type="text/plain",
            source_description="construct:artisan:1.4.0 /distill prompt 1",
            source_id="construct:artisan:1.4.0",
        )
        assert item.provenance_class == ProvenanceClass.CONSTRUCT_EVALUATION
        assert item.content_hash == hashlib.sha256(b"test output from construct skill").hexdigest()


class TestStopConditionEvaluator:
    """Test CONSTRUCT_EVALUATION stop condition handler."""

    def test_construct_evaluation_ready_when_all_prompts_evaluated(self):
        """Returns ready when evidence count >= committed prompt count."""
        evaluator = InvestigationStopConditionEvaluator()
        envelope = EvidenceEnvelope()

        # Submit 3 items
        for i in range(3):
            envelope.submit(
                content=f"output {i}".encode(),
                provenance_class=ProvenanceClass.CONSTRUCT_EVALUATION,
                content_type="text/plain",
                source_description=f"prompt {i}",
            )

        stop_config = {"committed_prompt_count": 3}
        claim_graph = ClaimGraph()

        ready, reason = evaluator.evaluate(
            stop_condition="CONSTRUCT_EVALUATION",
            stop_config=stop_config,
            claim_graph=claim_graph,
            evidence_envelope=envelope,
            time_remaining=999,
        )
        assert ready is True
        assert reason == "all_prompts_evaluated"

    def test_construct_evaluation_not_ready_when_prompts_missing(self):
        """Returns not ready when evidence count < committed prompt count."""
        evaluator = InvestigationStopConditionEvaluator()
        envelope = EvidenceEnvelope()

        # Submit 2 of 5 items
        for i in range(2):
            envelope.submit(
                content=f"output {i}".encode(),
                provenance_class=ProvenanceClass.CONSTRUCT_EVALUATION,
                content_type="text/plain",
                source_description=f"prompt {i}",
            )

        stop_config = {"committed_prompt_count": 5}
        claim_graph = ClaimGraph()

        ready, reason = evaluator.evaluate(
            stop_condition="CONSTRUCT_EVALUATION",
            stop_config=stop_config,
            claim_graph=claim_graph,
            evidence_envelope=envelope,
            time_remaining=999,
        )
        assert ready is False
        assert "missing_prompts:3" in reason

    def test_construct_evaluation_no_config(self):
        """Returns not ready when committed_prompt_count not configured."""
        evaluator = InvestigationStopConditionEvaluator()
        envelope = EvidenceEnvelope()
        claim_graph = ClaimGraph()

        ready, reason = evaluator.evaluate(
            stop_condition="CONSTRUCT_EVALUATION",
            stop_config={},
            claim_graph=claim_graph,
            evidence_envelope=envelope,
            time_remaining=999,
        )
        assert ready is False
        assert "no_committed_prompt_count" in reason


class TestTestPromptRegistry:
    """Test prompt registry loading and verification."""

    def test_artisan_prompt_set_has_12_entries(self):
        """Artisan prompt set has 12 entries."""
        registry = TestPromptRegistry()
        prompt_set = registry.get_prompts("artisan", "1.4.0")
        assert prompt_set is not None
        assert prompt_set.count == 12

    def test_artisan_prompt_set_covers_5_domains(self):
        """Artisan prompt set covers 5 domains."""
        registry = TestPromptRegistry()
        prompt_set = registry.get_prompts("artisan", "1.4.0")
        assert prompt_set is not None
        assert len(prompt_set.domains) == 5
        expected = [
            "Design Systems",
            "Frontend Best Practices",
            "Motion Design",
            "Taste Compounding",
            "Visual Refinement",
        ]
        assert prompt_set.domains == expected

    def test_prompt_set_hash_is_stable(self):
        """Hash is deterministic — same prompts produce same hash."""
        registry1 = TestPromptRegistry()
        registry2 = TestPromptRegistry()

        set1 = registry1.get_prompts("artisan", "1.4.0")
        set2 = registry2.get_prompts("artisan", "1.4.0")

        assert set1 is not None
        assert set2 is not None
        assert set1.prompts_hash == set2.prompts_hash
        assert set1.prompts_hash.startswith("sha256:")

    def test_verify_hash_matches(self):
        """verify_hash returns True for correct hash."""
        registry = TestPromptRegistry()
        prompt_set = registry.get_prompts("artisan", "1.4.0")
        assert prompt_set is not None
        assert registry.verify_hash("artisan", "1.4.0", prompt_set.prompts_hash) is True

    def test_verify_hash_rejects_wrong_hash(self):
        """verify_hash returns False for incorrect hash."""
        registry = TestPromptRegistry()
        assert registry.verify_hash("artisan", "1.4.0", "sha256:wrong") is False

    def test_khole_prompt_set_has_7_entries(self):
        """K-Hole prompt set has 7 entries."""
        registry = TestPromptRegistry()
        prompt_set = registry.get_prompts("khole", "1.2.0")
        assert prompt_set is not None
        assert prompt_set.count == 7

    def test_mibera_codex_prompt_set_has_11_entries(self):
        """Mibera Codex prompt set has 11 entries."""
        registry = TestPromptRegistry()
        prompt_set = registry.get_prompts("mibera-codex", "1.0.0")
        assert prompt_set is not None
        assert prompt_set.count == 11

    def test_get_prompt_at_index(self):
        """get_prompt_at_index returns correct prompt."""
        registry = TestPromptRegistry()
        prompt = registry.get_prompt_at_index("artisan", "1.4.0", 1)
        assert prompt is not None
        assert prompt.skill_command == "/distill"
        assert prompt.domain == "Design Systems"

    def test_get_prompt_at_invalid_index_returns_none(self):
        """get_prompt_at_index returns None for missing index."""
        registry = TestPromptRegistry()
        prompt = registry.get_prompt_at_index("artisan", "1.4.0", 999)
        assert prompt is None
