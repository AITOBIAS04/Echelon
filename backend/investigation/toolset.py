"""Investigation Toolset — orchestrator wiring all 8 investigation tools.

Instantiates and delegates to:
1. EvidenceEnvelope
2. ClaimGraph
3. InvestigationCounterSignalFeed
4. CommitmentMonitor
5. SignalScanner
6. EntityResolver
7. InvestigationCorroborationChecker
8. InvestigationCertificateBuilder
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from backend.investigation.certificate import (
    InvestigationCertificate,
    InvestigationCertificateBuilder,
)
from backend.investigation.claim_graph import ClaimGraph, ClaimType, ClaimStatus
from backend.investigation.commitment_monitor import (
    CommitmentMonitor,
    DriftType,
    DriftImpact,
)
from backend.investigation.corroboration_checker import (
    InvestigationCorroborationChecker,
)
from backend.investigation.counter_signals import (
    InvestigationCounterSignalFeed,
    InvestigationCounterSignalClass,
)
from backend.investigation.evidence_envelope import EvidenceEnvelope
from backend.investigation.entity_resolver import EntityResolver, EntityQuery
from backend.investigation.models import ProvenanceClass
from backend.investigation.signal_scanner import DomainFilter, SignalScanner


class InvestigationConfig(BaseModel):
    """Configuration for an investigation toolset instance."""

    domain_filters: list[str] = Field(default_factory=list)
    stop_condition: str = "OUTCOME_RESOLUTION"
    stop_config: dict = Field(default_factory=dict)


class InvestigationToolset:
    """Orchestrator wiring all 8 investigation tools.

    Provides delegation methods that pass through to underlying tools,
    plus build_certificate() for assembling the terminal artefact.
    """

    def __init__(
        self,
        config: InvestigationConfig,
        theatre_id: str = "",
        construct_id: str = "",
        inquiry_class: str = "INVESTIGATIVE",
    ) -> None:
        self._config = config
        self._theatre_id = theatre_id
        self._construct_id = construct_id
        self._inquiry_class = inquiry_class
        self._started_at = datetime.utcnow()

        # Parse domain filters
        domain_filters = [DomainFilter(f) for f in config.domain_filters] if config.domain_filters else []

        # Instantiate all 8 tools
        self._evidence_envelope = EvidenceEnvelope()
        self._claim_graph = ClaimGraph()
        self._counter_signal_feed = InvestigationCounterSignalFeed()
        self._commitment_monitor = CommitmentMonitor()
        self._signal_scanner = SignalScanner(domain_filters)
        self._entity_resolver = EntityResolver()
        self._corroboration_checker = InvestigationCorroborationChecker()
        self._certificate_builder = InvestigationCertificateBuilder()

    # ---- Delegation: Evidence Envelope ----

    def submit_evidence(
        self,
        content: bytes,
        provenance_class: ProvenanceClass,
        content_type: str,
        source_description: str,
        references: list[str] | None = None,
        source_id: str = "",
        query_determinism: str = "",
    ):
        """Submit evidence to the envelope."""
        return self._evidence_envelope.submit(
            content=content,
            provenance_class=provenance_class,
            content_type=content_type,
            source_description=source_description,
            references=references,
            source_id=source_id,
            query_determinism=query_determinism,
        )

    # ---- Delegation: Claim Graph ----

    def register_claim(
        self,
        claim_text: str,
        claim_type: ClaimType,
        evidence_refs: list[str],
    ):
        """Register a claim in the claim graph."""
        return self._claim_graph.add_claim(
            claim_text=claim_text,
            claim_type=claim_type,
            evidence_refs=evidence_refs,
        )

    # ---- Delegation: Counter-Signal Feed ----

    def log_counter_signal(
        self,
        signal_class: InvestigationCounterSignalClass,
        material: bool,
        resolution_impact: str,
        detection_method: str,
        evidence_ref: str | None = None,
    ):
        """Log a counter-signal to the feed."""
        return self._counter_signal_feed.log_counter_signal(
            signal_class=signal_class,
            material=material,
            resolution_impact=resolution_impact,
            detection_method=detection_method,
            evidence_ref=evidence_ref,
        )

    # ---- Delegation: Commitment Monitor ----

    def log_drift(
        self,
        drift_type: DriftType,
        original_value: str,
        new_value: str,
        impact_assessment: DriftImpact,
        evidence_ref: str | None = None,
    ):
        """Log a drift event to the commitment monitor."""
        return self._commitment_monitor.log_drift(
            drift_type=drift_type,
            original_value=original_value,
            new_value=new_value,
            impact_assessment=impact_assessment,
            evidence_ref=evidence_ref,
        )

    # ---- Delegation: Signal Scanner ----

    def run_scan(self, subject: str):
        """Run an OSINT signal scan."""
        return self._signal_scanner.scan(subject)

    # ---- Delegation: Entity Resolver ----

    def resolve_entity(self, query: EntityQuery):
        """Resolve an entity profile."""
        return self._entity_resolver.resolve(query)

    # ---- Tool Access (for advanced use) ----

    @property
    def evidence_envelope(self) -> EvidenceEnvelope:
        return self._evidence_envelope

    @property
    def claim_graph(self) -> ClaimGraph:
        return self._claim_graph

    @property
    def counter_signal_feed(self) -> InvestigationCounterSignalFeed:
        return self._counter_signal_feed

    @property
    def commitment_monitor(self) -> CommitmentMonitor:
        return self._commitment_monitor

    @property
    def corroboration_checker(self) -> InvestigationCorroborationChecker:
        return self._corroboration_checker

    # ---- Certificate ----

    def build_certificate(
        self,
        template_id: str | None = None,
        template_name: str | None = None,
        committed_sources: list | None = None,
    ) -> InvestigationCertificate:
        """Build the terminal InvestigationCertificate from all tool state."""
        return self._certificate_builder.build(
            theatre_id=self._theatre_id,
            construct_id=self._construct_id,
            inquiry_class=self._inquiry_class,
            stop_condition=self._config.stop_condition,
            stop_config=self._config.stop_config,
            evidence_envelope=self._evidence_envelope,
            claim_graph=self._claim_graph,
            counter_signal_feed=self._counter_signal_feed,
            commitment_monitor=self._commitment_monitor,
            investigation_started_at=self._started_at,
            template_id=template_id,
            template_name=template_name,
            committed_sources=committed_sources,
        )
