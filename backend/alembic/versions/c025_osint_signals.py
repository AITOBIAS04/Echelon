"""025 OSINT Signals table — Path 1 signal persistence

Revision ID: c025_osint_signals
Revises: c024_construct_verification
Create Date: 2026-03-17

Sprint-0 migration:
- Create osint_signals table for Path 1 registry-based OSINT persistence
- Composite indexes for source_group, investigation, and geo queries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c025_osint_signals"
down_revision: Union[str, None] = "c024_construct_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "osint_signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(128), nullable=False, index=True),
        sa.Column("source_group", sa.String(64), nullable=False),
        sa.Column("signal_type", sa.String(64), nullable=False),
        sa.Column("geo_region", sa.String(128), nullable=True),
        sa.Column("entity_ref", sa.String(256), nullable=True),
        sa.Column("content_hash", sa.String(128), nullable=False, index=True),
        sa.Column("normalised_data", sa.JSON, nullable=False),
        sa.Column("investigation_id", sa.String(36), sa.ForeignKey("investigations.id"), nullable=True),
        sa.Column("collected_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_index(
        "ix_osint_signals_source_group_collected",
        "osint_signals",
        ["source_group", "collected_at"],
    )
    op.create_index(
        "ix_osint_signals_investigation_collected",
        "osint_signals",
        ["investigation_id", "collected_at"],
    )
    op.create_index(
        "ix_osint_signals_geo_collected",
        "osint_signals",
        ["geo_region", "collected_at"],
    )


def downgrade() -> None:
    op.drop_table("osint_signals")
