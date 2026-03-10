"""012 Create theatre, investigation, and deployment tables

Revision ID: c012_theatre_inv_deploy
Revises: a1b2c3d4e5f6
Create Date: 2026-03-10

These 13 tables were previously created by SQLAlchemy create_all() in the
old dual-database (SQLite + PostgreSQL) setup but never captured in an
Alembic migration.  With the Cycle-023 unification on PostgreSQL-only,
they must be created explicitly.

Tables created (in FK-safe order):
  1. theatre_templates
  2. theatre_certificates
  3. theatres
  4. theatre_episode_scores
  5. theatre_audit_events
  6. investigations
  7. investigation_evidence_items
  8. investigation_claim_nodes
  9. investigation_counter_signals
 10. investigation_drift_events
 11. investigation_certificates
 12. agent_deployments
 13. deployment_audit_events

NOTE: Columns added by later migrations (c014 inquiry_class, c014c stop
conditions, c018 spawned_from_checkpoint_id, c021 certificate lifecycle,
c022 investigation templates) are intentionally EXCLUDED — those
migrations add them via add_column.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c012_theatre_inv_deploy"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # ── 1. theatre_templates ──
    if "theatre_templates" not in existing_tables:
        op.create_table(
            "theatre_templates",
            sa.Column("id", sa.String(100), primary_key=True),
            sa.Column("template_family", sa.String(50), nullable=False),
            sa.Column("execution_path", sa.String(10), nullable=False),
            sa.Column("display_name", sa.String(100), nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("schema_version", sa.String(20), nullable=False),
            sa.Column("template_json", sa.JSON, nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=False),
        )
        op.create_index(
            "ix_theatre_templates_family", "theatre_templates", ["template_family"]
        )
        op.create_index(
            "ix_theatre_templates_execution_path",
            "theatre_templates",
            ["execution_path"],
        )

    # ── 2. theatre_certificates (no FK to theatres — theatre_id is plain string) ──
    if "theatre_certificates" not in existing_tables:
        op.create_table(
            "theatre_certificates",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("theatre_id", sa.String(50), nullable=False),
            sa.Column("template_id", sa.String(100), nullable=False),
            sa.Column("construct_id", sa.String(255), nullable=False),
            # Criteria & scores
            sa.Column("criteria_json", sa.JSON, nullable=False),
            sa.Column("scores_json", sa.JSON, nullable=False),
            sa.Column("composite_score", sa.Float, nullable=False),
            # Calibration (optional)
            sa.Column("precision", sa.Float, nullable=True),
            sa.Column("recall", sa.Float, nullable=True),
            sa.Column("reply_accuracy", sa.Float, nullable=True),
            sa.Column("brier_score", sa.Float, nullable=True),
            sa.Column("ece", sa.Float, nullable=True),
            # Evidence
            sa.Column("replay_count", sa.Integer, nullable=False),
            sa.Column("evidence_bundle_hash", sa.String(64), nullable=False),
            sa.Column("ground_truth_hash", sa.String(64), nullable=False),
            # Reproducibility
            sa.Column("construct_version", sa.String(64), nullable=False),
            sa.Column("construct_chain_versions", sa.JSON, nullable=True),
            sa.Column("scorer_version", sa.String(100), nullable=False),
            sa.Column("methodology_version", sa.String(20), nullable=False),
            sa.Column("dataset_hash", sa.String(64), nullable=False),
            # Trust
            sa.Column("verification_tier", sa.String(20), nullable=False),
            sa.Column("commitment_hash", sa.String(64), nullable=False),
            # Timestamps
            sa.Column("issued_at", sa.DateTime, nullable=False),
            sa.Column("expires_at", sa.DateTime, nullable=True),
            sa.Column("theatre_committed_at", sa.DateTime, nullable=False),
            sa.Column("theatre_resolved_at", sa.DateTime, nullable=False),
            # Integration
            sa.Column("ground_truth_source", sa.String(100), nullable=False),
            sa.Column("execution_path", sa.String(10), nullable=False),
        )
        op.create_index(
            "ix_theatre_certs_construct_created",
            "theatre_certificates",
            ["construct_id", "issued_at"],
        )
        op.create_index(
            "ix_theatre_certs_tier",
            "theatre_certificates",
            ["verification_tier"],
        )
        op.create_index(
            "ix_theatre_certs_template",
            "theatre_certificates",
            ["template_id"],
        )

    # ── 3. theatres ──
    # NOTE: inquiry_class added by c014, stop_condition/stop_config by c014c,
    #       spawned_from_checkpoint_id by c018.  Excluded here.
    if "theatres" not in existing_tables:
        op.create_table(
            "theatres",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(50),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column(
                "template_id",
                sa.String(100),
                sa.ForeignKey("theatre_templates.id"),
                nullable=False,
            ),
            sa.Column(
                "state", sa.String(20), nullable=False, server_default="DRAFT"
            ),
            sa.Column("construct_id", sa.String(255), nullable=False),
            # Commitment
            sa.Column("commitment_hash", sa.String(64), nullable=True),
            sa.Column("committed_at", sa.DateTime, nullable=True),
            sa.Column("version_pins", sa.JSON, nullable=True),
            sa.Column("dataset_hashes", sa.JSON, nullable=True),
            # Paradox risk surface (cycle-019, no separate migration)
            sa.Column("paradox_risk_level", sa.String(10), nullable=True),
            sa.Column("paradox_risk_factors_json", sa.JSON, nullable=True),
            sa.Column("paradox_risk_updated_at", sa.DateTime, nullable=True),
            # Execution tracking
            sa.Column(
                "progress", sa.Integer, nullable=False, server_default="0"
            ),
            sa.Column(
                "total_episodes", sa.Integer, nullable=False, server_default="0"
            ),
            sa.Column(
                "failure_count", sa.Integer, nullable=False, server_default="0"
            ),
            sa.Column("error", sa.Text, nullable=True),
            # Resolution
            sa.Column("resolved_at", sa.DateTime, nullable=True),
            sa.Column(
                "certificate_id",
                sa.String(50),
                sa.ForeignKey("theatre_certificates.id"),
                nullable=True,
            ),
            # Timestamps
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=False),
        )
        op.create_index("ix_theatres_state", "theatres", ["state"])
        op.create_index("ix_theatres_construct", "theatres", ["construct_id"])
        op.create_index(
            "ix_theatres_user_created", "theatres", ["user_id", "created_at"]
        )
        op.create_index("ix_theatres_user_id", "theatres", ["user_id"])
        op.create_index("ix_theatres_template_id", "theatres", ["template_id"])

    # ── 4. theatre_episode_scores ──
    if "theatre_episode_scores" not in existing_tables:
        op.create_table(
            "theatre_episode_scores",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column(
                "theatre_id",
                sa.String(50),
                sa.ForeignKey("theatres.id"),
                nullable=False,
            ),
            sa.Column(
                "certificate_id",
                sa.String(50),
                sa.ForeignKey("theatre_certificates.id"),
                nullable=True,
            ),
            sa.Column("episode_id", sa.String(255), nullable=False),
            sa.Column("invocation_status", sa.String(20), nullable=False),
            sa.Column("latency_ms", sa.Integer, nullable=False),
            sa.Column("scores_json", sa.JSON, nullable=False),
            sa.Column("composite_score", sa.Float, nullable=False),
            sa.Column("scored_at", sa.DateTime, nullable=False),
        )
        op.create_index(
            "ix_theatre_episode_scores_theatre",
            "theatre_episode_scores",
            ["theatre_id"],
        )
        op.create_index(
            "ix_theatre_episode_scores_cert",
            "theatre_episode_scores",
            ["certificate_id"],
        )

    # ── 5. theatre_audit_events ──
    if "theatre_audit_events" not in existing_tables:
        op.create_table(
            "theatre_audit_events",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column(
                "theatre_id",
                sa.String(50),
                sa.ForeignKey("theatres.id"),
                nullable=False,
            ),
            sa.Column("event_type", sa.String(50), nullable=False),
            sa.Column("from_state", sa.String(20), nullable=True),
            sa.Column("to_state", sa.String(20), nullable=True),
            sa.Column("detail_json", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
        op.create_index(
            "ix_theatre_audit_theatre_created",
            "theatre_audit_events",
            ["theatre_id", "created_at"],
        )

    # ── 6. investigations ──
    # NOTE: stop_condition lifecycle columns added by c021,
    #       template_id/committed_sources_json added by c022.  Excluded here.
    if "investigations" not in existing_tables:
        op.create_table(
            "investigations",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("theatre_id", sa.String(50), nullable=False),
            sa.Column("construct_id", sa.String(100), nullable=False),
            sa.Column(
                "inquiry_class",
                sa.String(30),
                nullable=False,
                server_default="INVESTIGATIVE",
            ),
            sa.Column(
                "status",
                sa.String(20),
                nullable=False,
                server_default="ACTIVE",
            ),
            sa.Column(
                "domain_filters_json", sa.JSON, nullable=True, server_default="[]"
            ),
            sa.Column(
                "stop_condition",
                sa.String(30),
                nullable=False,
                server_default="OUTCOME_RESOLUTION",
            ),
            sa.Column(
                "stop_config_json", sa.JSON, nullable=True, server_default="{}"
            ),
            sa.Column("created_by", sa.String(50), nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=False),
            sa.Column("completed_at", sa.DateTime, nullable=True),
        )
        op.create_index(
            "ix_investigations_theatre_id", "investigations", ["theatre_id"]
        )
        op.create_index(
            "ix_investigations_status", "investigations", ["status"]
        )

    # ── 7. investigation_evidence_items ──
    if "investigation_evidence_items" not in existing_tables:
        op.create_table(
            "investigation_evidence_items",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column(
                "investigation_id",
                sa.String(50),
                sa.ForeignKey("investigations.id"),
                nullable=False,
            ),
            sa.Column("content_hash", sa.String(64), nullable=False),
            sa.Column("provenance_class", sa.String(30), nullable=False),
            sa.Column(
                "content_type",
                sa.String(50),
                nullable=False,
                server_default="text/plain",
            ),
            sa.Column(
                "source_description", sa.Text, nullable=False, server_default=""
            ),
            sa.Column(
                "source_id",
                sa.String(100),
                nullable=False,
                server_default="",
            ),
            sa.Column(
                "query_determinism",
                sa.String(30),
                nullable=False,
                server_default="",
            ),
            sa.Column(
                "references_json", sa.JSON, nullable=True, server_default="[]"
            ),
            sa.Column("submitted_at", sa.DateTime, nullable=False),
        )
        op.create_index(
            "ix_investigation_evidence_inv",
            "investigation_evidence_items",
            ["investigation_id"],
        )

    # ── 8. investigation_claim_nodes ──
    if "investigation_claim_nodes" not in existing_tables:
        op.create_table(
            "investigation_claim_nodes",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column(
                "investigation_id",
                sa.String(50),
                sa.ForeignKey("investigations.id"),
                nullable=False,
            ),
            sa.Column("claim_text", sa.Text, nullable=False),
            sa.Column("claim_type", sa.String(20), nullable=False),
            sa.Column(
                "evidence_refs_json", sa.JSON, nullable=True, server_default="[]"
            ),
            sa.Column(
                "counter_signals_json",
                sa.JSON,
                nullable=True,
                server_default="[]",
            ),
            sa.Column(
                "status",
                sa.String(30),
                nullable=False,
                server_default="UNCONFIRMED",
            ),
            sa.Column(
                "confidence",
                sa.Float,
                nullable=False,
                server_default="0.0",
            ),
            sa.Column(
                "independence_groups_json",
                sa.JSON,
                nullable=True,
                server_default="[]",
            ),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=False),
        )
        op.create_index(
            "ix_investigation_claims_inv",
            "investigation_claim_nodes",
            ["investigation_id"],
        )

    # ── 9. investigation_counter_signals ──
    if "investigation_counter_signals" not in existing_tables:
        op.create_table(
            "investigation_counter_signals",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column(
                "investigation_id",
                sa.String(50),
                sa.ForeignKey("investigations.id"),
                nullable=False,
            ),
            sa.Column("signal_class", sa.String(50), nullable=False),
            sa.Column("detected_at", sa.DateTime, nullable=False),
            sa.Column("evidence_ref", sa.String(50), nullable=True),
            sa.Column(
                "material",
                sa.Boolean,
                nullable=False,
                server_default="false",
            ),
            sa.Column(
                "resolution_impact", sa.Text, nullable=False, server_default=""
            ),
            sa.Column(
                "detection_method",
                sa.String(30),
                nullable=False,
                server_default="human_submitted",
            ),
        )
        op.create_index(
            "ix_investigation_counter_signals_inv",
            "investigation_counter_signals",
            ["investigation_id"],
        )

    # ── 10. investigation_drift_events ──
    if "investigation_drift_events" not in existing_tables:
        op.create_table(
            "investigation_drift_events",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column(
                "investigation_id",
                sa.String(50),
                sa.ForeignKey("investigations.id"),
                nullable=False,
            ),
            sa.Column("drift_type", sa.String(30), nullable=False),
            sa.Column("detected_at", sa.DateTime, nullable=False),
            sa.Column(
                "original_value", sa.Text, nullable=False, server_default=""
            ),
            sa.Column("new_value", sa.Text, nullable=False, server_default=""),
            sa.Column("evidence_ref", sa.String(50), nullable=True),
            sa.Column(
                "impact_assessment",
                sa.String(20),
                nullable=False,
                server_default="non_material",
            ),
        )
        op.create_index(
            "ix_investigation_drift_inv",
            "investigation_drift_events",
            ["investigation_id"],
        )

    # ── 11. investigation_certificates ──
    # NOTE: certificate_status, ready_at, anchored_at, batch_anchor_hash
    #       added by c021_certificate_lifecycle.  Excluded here.
    if "investigation_certificates" not in existing_tables:
        op.create_table(
            "investigation_certificates",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column(
                "investigation_id",
                sa.String(50),
                sa.ForeignKey("investigations.id"),
                nullable=False,
                unique=True,
            ),
            sa.Column("certificate_hash", sa.String(64), nullable=False),
            sa.Column("certificate_json", sa.JSON, nullable=False),
            sa.Column("routing_decision", sa.String(20), nullable=False),
            sa.Column(
                "routing_reason",
                sa.String(50),
                nullable=False,
                server_default="",
            ),
            sa.Column("issued_at", sa.DateTime, nullable=True),
        )
        op.create_index(
            "ix_investigation_certs_inv",
            "investigation_certificates",
            ["investigation_id"],
        )

    # ── 12. agent_deployments ──
    if "agent_deployments" not in existing_tables:
        op.create_table(
            "agent_deployments",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column(
                "agent_id",
                sa.String(50),
                sa.ForeignKey("agents.id"),
                nullable=False,
            ),
            sa.Column(
                "theatre_id",
                sa.String(50),
                sa.ForeignKey("theatres.id"),
                nullable=False,
            ),
            sa.Column(
                "status",
                sa.String(20),
                nullable=False,
                server_default="ACTIVE",
            ),
            sa.Column(
                "strategy_profile",
                sa.String(20),
                nullable=False,
                server_default="BALANCED",
            ),
            sa.Column("deployed_by", sa.String(50), nullable=False),
            sa.Column("deployed_at", sa.DateTime, nullable=False),
            sa.Column("paused_at", sa.DateTime, nullable=True),
            sa.Column("withdrawn_at", sa.DateTime, nullable=True),
            sa.Column("routing_hint_snapshot", sa.String(30), nullable=True),
            sa.Column(
                "coherence_gate_status_snapshot", sa.String(20), nullable=True
            ),
            sa.Column("config_json", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=False),
        )
        op.create_index(
            "ix_agent_deployments_agent", "agent_deployments", ["agent_id"]
        )
        op.create_index(
            "ix_agent_deployments_theatre", "agent_deployments", ["theatre_id"]
        )
        op.create_index(
            "ix_agent_deployments_status", "agent_deployments", ["status"]
        )
        op.create_index(
            "ix_agent_deployments_active",
            "agent_deployments",
            ["agent_id", "theatre_id", "status"],
        )
        op.create_index(
            "ix_agent_deployments_deployed_by",
            "agent_deployments",
            ["deployed_by"],
        )

    # ── 13. deployment_audit_events ──
    if "deployment_audit_events" not in existing_tables:
        op.create_table(
            "deployment_audit_events",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column(
                "deployment_id",
                sa.String(50),
                sa.ForeignKey("agent_deployments.id"),
                nullable=False,
            ),
            sa.Column("event_type", sa.String(50), nullable=False),
            sa.Column("detail_json", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
        op.create_index(
            "ix_deployment_audit_deployment",
            "deployment_audit_events",
            ["deployment_id"],
        )
        op.create_index(
            "ix_deployment_audit_event_type",
            "deployment_audit_events",
            ["event_type"],
        )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("deployment_audit_events")
    op.drop_table("agent_deployments")
    op.drop_table("investigation_certificates")
    op.drop_table("investigation_drift_events")
    op.drop_table("investigation_counter_signals")
    op.drop_table("investigation_claim_nodes")
    op.drop_table("investigation_evidence_items")
    op.drop_table("investigations")
    op.drop_table("theatre_audit_events")
    op.drop_table("theatre_episode_scores")
    op.drop_table("theatres")
    op.drop_table("theatre_certificates")
    op.drop_table("theatre_templates")
