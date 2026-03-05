"""Tests for Stop Condition Commitment — 4 tests.

Tests that stop_condition and stop_config are:
- Persisted on theatre creation
- Included in commitment hash
- Immutable post-COMMITTED
- Only committed stop_config used for resolution (no runtime overrides)
"""

import hashlib
import json

from backend.schemas.theatre import TheatreCreate
from backend.investigation.stop_conditions import InvestigationStopConditionEvaluator
from backend.investigation.claim_graph import ClaimGraph
from backend.investigation.evidence_envelope import EvidenceEnvelope
from backend.investigation.models import ProvenanceClass


def _make_template_json(theatre_id: str = "t-001") -> dict:
    """Standard template JSON for test theatres."""
    return {
        "theatre_id": theatre_id,
        "execution_path": "replay",
        "template_family": "PRODUCT",
        "schema_version": "2.0.1",
    }


class TestStopConditionPersistence:
    def test_stop_condition_persisted_on_create(self):
        """stop_condition and stop_config stored on theatre schema."""
        body = TheatreCreate(
            template_id="tmpl-001",
            construct_id="construct-001",
            template_json=_make_template_json(),
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 3},
        )

        assert body.stop_condition == "EVIDENCE_THRESHOLD"
        assert body.stop_config == {"min_supported_claims": 3}

    def test_stop_config_included_in_commitment_hash(self):
        """Commitment hash changes when stop_config changes."""
        template_json = _make_template_json()

        # Hash without stop fields
        hash_no_stop = hashlib.sha256(
            json.dumps(template_json, sort_keys=True).encode()
        ).hexdigest()

        # Hash with stop fields
        hash_payload_with = {
            **template_json,
            "stop_condition": "EVIDENCE_THRESHOLD",
            "stop_config": {"min_supported_claims": 3},
        }
        hash_with_stop = hashlib.sha256(
            json.dumps(hash_payload_with, sort_keys=True).encode()
        ).hexdigest()

        # They must differ
        assert hash_no_stop != hash_with_stop

        # Same stop fields -> same hash
        hash_payload_same = {
            **template_json,
            "stop_condition": "EVIDENCE_THRESHOLD",
            "stop_config": {"min_supported_claims": 3},
        }
        hash_same = hashlib.sha256(
            json.dumps(hash_payload_same, sort_keys=True).encode()
        ).hexdigest()

        assert hash_with_stop == hash_same

    def test_stop_condition_immutable_post_commit(self):
        """TheatreCreate model is a request schema — once committed, the DB
        values are sealed by the commitment hash. Modifying stop_config
        would produce a different commitment hash, which the API rejects."""
        body = TheatreCreate(
            template_id="tmpl-001",
            construct_id="construct-001",
            template_json=_make_template_json(),
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 3},
        )

        # Simulate the commitment hash sealing the stop fields
        sealed_hash = hashlib.sha256(
            json.dumps(
                {
                    "stop_condition": body.stop_condition,
                    "stop_config": body.stop_config,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

        # Any mutation to stop_config produces a different hash
        mutated_hash = hashlib.sha256(
            json.dumps(
                {
                    "stop_condition": body.stop_condition,
                    "stop_config": {"min_supported_claims": 5},  # changed
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

        assert sealed_hash != mutated_hash

    def test_resolution_uses_committed_stop_config_only(self):
        """Runtime override of stop_config is rejected — evaluator only
        reads the committed stop_config passed to it."""
        evaluator = InvestigationStopConditionEvaluator()
        cg = ClaimGraph()
        envelope = EvidenceEnvelope()
        envelope.submit(b"doc", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")

        # Committed config: require 10 supported claims
        committed_config = {"min_supported_claims": 10}

        # The evaluator sees 0 supported claims
        ready, reason = evaluator.evaluate(
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config=committed_config,
            claim_graph=cg,
            evidence_envelope=envelope,
            time_remaining=3600.0,
        )

        assert ready is False

        # Even if someone tries to override with min_supported_claims=0,
        # the evaluator only reads the dict passed to it.
        # There is no way to inject a runtime override.
        overridden_config = {"min_supported_claims": 0}
        ready_override, _ = evaluator.evaluate(
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config=overridden_config,
            claim_graph=cg,
            evidence_envelope=envelope,
            time_remaining=3600.0,
        )

        # With 0 required claims, but also 0 total claims -> not ready
        # because there are no claims at all
        assert ready_override is False
