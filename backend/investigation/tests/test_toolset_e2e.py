"""E2E Tests for Investigation Toolset — 3 tests.

Full lifecycle tests verifying hash chaining across all tools.
"""

from backend.investigation.toolset import InvestigationToolset, InvestigationConfig
from backend.investigation.models import ProvenanceClass
from backend.investigation.claim_graph import ClaimType, ClaimStatus, CorroborationCheck
from backend.investigation.commitment_monitor import DriftType, DriftImpact
from backend.investigation.counter_signals import InvestigationCounterSignalClass
from backend.investigation.certificate import RoutingDecision
from backend.investigation.entity_resolver import EntityQuery


class TestE2EInvestigationLifecycle:
    def test_e2e_investigation_lifecycle(self):
        """Full lifecycle: submit evidence -> register claims -> corroborate
        -> counter-signals -> build certificate -> verify all hashes chain."""
        config = InvestigationConfig(
            domain_filters=["corporate_and_entity"],
            stop_condition="OUTCOME_RESOLUTION",
            stop_config={},
        )
        toolset = InvestigationToolset(
            config=config,
            theatre_id="theatre-e2e-001",
            construct_id="construct-e2e-001",
            inquiry_class="INVESTIGATIVE",
        )

        # Step 1: Submit evidence
        item1 = toolset.submit_evidence(
            content=b"Company X annual report 2025",
            provenance_class=ProvenanceClass.PUBLIC_PRIMARY,
            content_type="application/pdf",
            source_description="Companies House Filing",
        )
        item2 = toolset.submit_evidence(
            content=b"Financial analysis by Reuters",
            provenance_class=ProvenanceClass.PUBLIC_SECONDARY,
            content_type="text/html",
            source_description="Reuters Wire",
        )

        assert item1.evidence_id == "E001"
        assert item2.evidence_id == "E002"

        # Step 2: Register claims
        claim1 = toolset.register_claim(
            claim_text="Company X filed for insolvency",
            claim_type=ClaimType.FACT,
            evidence_refs=[item1.evidence_id],
        )
        claim2 = toolset.register_claim(
            claim_text="Insolvency was caused by regulatory action",
            claim_type=ClaimType.CAUSAL,
            evidence_refs=[item1.evidence_id, item2.evidence_id],
        )

        assert claim1.claim_id == "C001"
        assert claim2.claim_id == "C002"

        # Step 3: Corroborate claims
        checks = [
            CorroborationCheck(
                claim_id=claim1.claim_id,
                source_id="CH001",
                upstream_group="official_gov",
                status="confirmed",
                confidence=0.95,
            ),
            CorroborationCheck(
                claim_id=claim1.claim_id,
                source_id="LG001",
                upstream_group="gazette",
                status="confirmed",
                confidence=0.90,
            ),
        ]
        result = toolset.corroboration_checker.evaluate_claim(claim1, checks)
        assert result == ClaimStatus.SUPPORTED

        # Update claim status in the graph
        toolset.claim_graph.update_claim_status(
            claim1.claim_id, ClaimStatus.SUPPORTED, 0.92,
            ["official_gov", "gazette"],
        )

        # Step 4: Log counter-signals (non-material)
        toolset.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.REGULATORY_CLEARANCE,
            material=False,
            resolution_impact="low",
            detection_method="automated_osint",
        )

        # Step 5: Run OSINT scan
        brief = toolset.run_scan("Company X UK")
        assert brief.brief_id == "DB001"
        assert len(brief.content_hash) == 64

        # Step 6: Resolve entity
        profile = toolset.resolve_entity(
            EntityQuery(
                entity_name="Company X",
                jurisdiction="UK",
                registration_number="12345678",
            )
        )
        assert profile.entity_id.startswith("ENT-") and len(profile.entity_id) == 16
        assert len(profile.profile_hash) == 64

        # Step 7: Build certificate
        cert = toolset.build_certificate()

        # Verify certificate structure
        assert cert.theatre_id == "theatre-e2e-001"
        assert cert.construct_id == "construct-e2e-001"
        assert cert.evidence_item_count == 2
        assert cert.claim_count == 2
        assert len(cert.certificate_hash) == 64

        # Verify hash chaining
        assert cert.evidence_envelope_hash == toolset.evidence_envelope.compute_envelope_hash()
        assert cert.claim_graph_root_hash == toolset.claim_graph.compute_root_hash()

        # Verify routing
        assert cert.routing_decision == RoutingDecision.ALLOWED.value
        assert cert.routing_reason == "all_checks_passed"

    def test_e2e_with_drift_event(self):
        """Same lifecycle + material drift -> REVIEW_REQUIRED."""
        config = InvestigationConfig(
            domain_filters=["corporate_and_entity"],
            stop_condition="OUTCOME_RESOLUTION",
            stop_config={},
        )
        toolset = InvestigationToolset(
            config=config,
            theatre_id="theatre-drift-001",
            construct_id="construct-drift-001",
            inquiry_class="INVESTIGATIVE",
        )

        # Submit evidence
        toolset.submit_evidence(
            content=b"Original filing",
            provenance_class=ProvenanceClass.PUBLIC_PRIMARY,
            content_type="application/pdf",
            source_description="CH",
        )
        toolset.submit_evidence(
            content=b"Secondary source",
            provenance_class=ProvenanceClass.PUBLIC_SECONDARY,
            content_type="text/html",
            source_description="Reuters",
        )

        # Register claim
        toolset.register_claim(
            claim_text="Company X is active",
            claim_type=ClaimType.FACT,
            evidence_refs=["E001"],
        )

        # Log material drift
        toolset.log_drift(
            drift_type=DriftType.ENTITY_RESTRUCTURE,
            original_value="Company X Ltd",
            new_value="Company X Holdings Ltd",
            impact_assessment=DriftImpact.MATERIAL,
            evidence_ref="E001",
        )

        # Build certificate
        cert = toolset.build_certificate()

        assert cert.has_material_drift is True
        assert cert.drift_event_count == 1
        assert cert.routing_decision == RoutingDecision.REVIEW_REQUIRED.value
        assert cert.routing_reason == "drift_event_material"

    def test_e2e_evidence_threshold_resolution(self):
        """Early resolution via EVIDENCE_THRESHOLD stop condition."""
        from backend.investigation.stop_conditions import InvestigationStopConditionEvaluator

        config = InvestigationConfig(
            domain_filters=["corporate_and_entity"],
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 2, "min_corroboration_score": 0.5},
        )
        toolset = InvestigationToolset(
            config=config,
            theatre_id="theatre-thresh-001",
            construct_id="construct-thresh-001",
            inquiry_class="INVESTIGATIVE",
        )

        # Submit evidence
        toolset.submit_evidence(
            content=b"Primary source 1",
            provenance_class=ProvenanceClass.PUBLIC_PRIMARY,
            content_type="text/plain",
            source_description="Source A",
        )
        toolset.submit_evidence(
            content=b"Secondary source 1",
            provenance_class=ProvenanceClass.PUBLIC_SECONDARY,
            content_type="text/plain",
            source_description="Source B",
        )

        # Register and support 2 claims
        c1 = toolset.register_claim(
            "Claim 1: fact", ClaimType.FACT, ["E001"],
        )
        c2 = toolset.register_claim(
            "Claim 2: fact", ClaimType.FACT, ["E002"],
        )

        toolset.claim_graph.update_claim_status(
            c1.claim_id, ClaimStatus.SUPPORTED, 0.9, ["group_a", "group_b"],
        )
        toolset.claim_graph.update_claim_status(
            c2.claim_id, ClaimStatus.SUPPORTED, 0.85, ["group_a", "group_c"],
        )

        # Check stop condition
        evaluator = InvestigationStopConditionEvaluator()
        ready, reason = evaluator.evaluate(
            stop_condition=config.stop_condition,
            stop_config=config.stop_config,
            claim_graph=toolset.claim_graph,
            evidence_envelope=toolset.evidence_envelope,
            time_remaining=3600.0,  # time still remaining
        )

        assert ready is True
        assert reason == "evidence_threshold_met"

        # Build certificate
        cert = toolset.build_certificate()
        assert cert.stop_condition == "EVIDENCE_THRESHOLD"
        assert cert.claim_count == 2
        assert cert.routing_decision == RoutingDecision.ALLOWED.value
