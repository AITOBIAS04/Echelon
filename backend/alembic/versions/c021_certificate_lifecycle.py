"""021 Certificate lifecycle columns + domain filter enforcement support

Revision ID: c021_certificate_lifecycle
Revises: c020_replay_source_run_id
Create Date: 2026-03-07

Adds 3 columns to investigations (stop_condition_status, stop_condition_reason,
stop_condition_evaluated_at) and 4 columns to investigation_certificates
(certificate_status, ready_at, anchored_at, batch_anchor_hash).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c021_certificate_lifecycle"
down_revision: Union[str, None] = "c020_replay_source_run_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # --- investigations: 3 new columns ---
    inv_cols = [c["name"] for c in inspector.get_columns("investigations")]

    if "stop_condition_status" not in inv_cols:
        op.add_column(
            "investigations",
            sa.Column(
                "stop_condition_status",
                sa.String(20),
                nullable=True,
                comment="NOT_READY | READY",
            ),
        )
    if "stop_condition_reason" not in inv_cols:
        op.add_column(
            "investigations",
            sa.Column(
                "stop_condition_reason",
                sa.String(500),
                nullable=True,
            ),
        )
    if "stop_condition_evaluated_at" not in inv_cols:
        op.add_column(
            "investigations",
            sa.Column(
                "stop_condition_evaluated_at",
                sa.DateTime,
                nullable=True,
            ),
        )

    # --- investigation_certificates: 4 new columns ---
    cert_cols = [c["name"] for c in inspector.get_columns("investigation_certificates")]

    if "certificate_status" not in cert_cols:
        op.add_column(
            "investigation_certificates",
            sa.Column(
                "certificate_status",
                sa.String(20),
                nullable=False,
                server_default="READY",
                comment="READY | ANCHORED | ISSUED",
            ),
        )
    if "ready_at" not in cert_cols:
        op.add_column(
            "investigation_certificates",
            sa.Column("ready_at", sa.DateTime, nullable=True),
        )
    if "anchored_at" not in cert_cols:
        op.add_column(
            "investigation_certificates",
            sa.Column("anchored_at", sa.DateTime, nullable=True),
        )
    if "batch_anchor_hash" not in cert_cols:
        op.add_column(
            "investigation_certificates",
            sa.Column("batch_anchor_hash", sa.String(64), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("investigation_certificates", "batch_anchor_hash")
    op.drop_column("investigation_certificates", "anchored_at")
    op.drop_column("investigation_certificates", "ready_at")
    op.drop_column("investigation_certificates", "certificate_status")
    op.drop_column("investigations", "stop_condition_evaluated_at")
    op.drop_column("investigations", "stop_condition_reason")
    op.drop_column("investigations", "stop_condition_status")
