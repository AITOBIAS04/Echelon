"""017 Policy Surface — routing, coherence, TAO flow columns

Revision ID: c017_policy_surface
Revises: c016_engine_coherence
Create Date: 2026-03-06

Sprint-0 migration:
- Add 6 policy columns to theatre_certificates (routing_hint, review_reason_code,
  coherence_review_required, coherence_gate_status, coherence_reviewed_at,
  coherence_reviewer_id)
- Add 3 TAO flow columns to timelines (net_inflow_24h, net_inflow_7d, flow_updated_at)
- Create index on theatre_certificates.routing_hint
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c017_policy_surface"
down_revision: Union[str, None] = "c016_engine_coherence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # ── 1. TheatreCertificate: routing + coherence columns ──
    cert_cols = [c["name"] for c in inspector.get_columns("theatre_certificates")]

    if "routing_hint" not in cert_cols:
        op.add_column(
            "theatre_certificates",
            sa.Column("routing_hint", sa.String(20), nullable=True),
        )
    if "review_reason_code" not in cert_cols:
        op.add_column(
            "theatre_certificates",
            sa.Column("review_reason_code", sa.String(100), nullable=True),
        )
    if "coherence_review_required" not in cert_cols:
        op.add_column(
            "theatre_certificates",
            sa.Column(
                "coherence_review_required",
                sa.Boolean(),
                server_default="false",
                nullable=False,
            ),
        )
    if "coherence_gate_status" not in cert_cols:
        op.add_column(
            "theatre_certificates",
            sa.Column("coherence_gate_status", sa.String(20), nullable=True),
        )
    if "coherence_reviewed_at" not in cert_cols:
        op.add_column(
            "theatre_certificates",
            sa.Column("coherence_reviewed_at", sa.DateTime(), nullable=True),
        )
    if "coherence_reviewer_id" not in cert_cols:
        op.add_column(
            "theatre_certificates",
            sa.Column("coherence_reviewer_id", sa.String(50), nullable=True),
        )

    # Index on routing_hint
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("theatre_certificates")]
    if "ix_theatre_certs_routing_hint" not in existing_indexes:
        op.create_index(
            "ix_theatre_certs_routing_hint",
            "theatre_certificates",
            ["routing_hint"],
        )

    # ── 2. Timeline: TAO flow columns ──
    tl_cols = [c["name"] for c in inspector.get_columns("timelines")]

    if "net_inflow_24h" not in tl_cols:
        op.add_column(
            "timelines",
            sa.Column("net_inflow_24h", sa.Float(), server_default="0.0", nullable=False),
        )
    if "net_inflow_7d" not in tl_cols:
        op.add_column(
            "timelines",
            sa.Column("net_inflow_7d", sa.Float(), server_default="0.0", nullable=False),
        )
    if "flow_updated_at" not in tl_cols:
        op.add_column(
            "timelines",
            sa.Column("flow_updated_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # ── Drop timeline TAO flow columns ──
    tl_cols = [c["name"] for c in inspector.get_columns("timelines")]
    for col in ("flow_updated_at", "net_inflow_7d", "net_inflow_24h"):
        if col in tl_cols:
            op.drop_column("timelines", col)

    # ── Drop certificate routing/coherence columns ──
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("theatre_certificates")]
    if "ix_theatre_certs_routing_hint" in existing_indexes:
        op.drop_index("ix_theatre_certs_routing_hint", table_name="theatre_certificates")

    cert_cols = [c["name"] for c in inspector.get_columns("theatre_certificates")]
    for col in (
        "coherence_reviewer_id",
        "coherence_reviewed_at",
        "coherence_gate_status",
        "coherence_review_required",
        "review_reason_code",
        "routing_hint",
    ):
        if col in cert_cols:
            op.drop_column("theatre_certificates", col)
