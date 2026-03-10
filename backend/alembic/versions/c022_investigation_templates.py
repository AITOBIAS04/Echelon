"""022 Investigation Template Infrastructure — new table + Investigation extension

Revision ID: c022_investigation_templates
Revises: c021_certificate_lifecycle
Create Date: 2026-03-08

Sprint-0 migration:
- Create investigation_templates table
- Add template_id column to investigations table with FK
- Add committed_sources_json column to investigations table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c022_investigation_templates"
down_revision: Union[str, None] = "c021_certificate_lifecycle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # --- Create investigation_templates table ---
    if "investigation_templates" not in existing_tables:
        op.create_table(
            "investigation_templates",
            sa.Column("id", sa.String(100), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column(
                "inquiry_class",
                sa.String(30),
                nullable=False,
                server_default="INVESTIGATIVE",
                comment="COUNTERFACTUAL | INVESTIGATIVE | INSPECTION | SURVEY | SCRUTINY",
            ),
            sa.Column("domain_filters_json", sa.JSON, nullable=True, server_default="[]"),
            sa.Column("default_sources_json", sa.JSON, nullable=True, server_default="[]"),
            sa.Column(
                "default_stop_condition",
                sa.String(30),
                nullable=False,
                server_default="OUTCOME_RESOLUTION",
                comment="OUTCOME_RESOLUTION | EVIDENCE_THRESHOLD | SPONSOR_DEFINED",
            ),
            sa.Column("default_time_window_days", sa.Integer, nullable=True),
            sa.Column(
                "requires_legal_review",
                sa.Boolean,
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "min_corroboration_groups",
                sa.Integer,
                nullable=False,
                server_default=sa.text("2"),
            ),
            sa.Column(
                "template_status",
                sa.String(20),
                nullable=False,
                server_default="ACTIVE",
                comment="ACTIVE | DRAFT",
            ),
            sa.Column(
                "is_seeded",
                sa.Boolean,
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column("created_at", sa.DateTime, nullable=True),
        )

    # --- Add columns to investigations ---
    inv_cols = [c["name"] for c in inspector.get_columns("investigations")]

    if "template_id" not in inv_cols:
        op.add_column(
            "investigations",
            sa.Column(
                "template_id",
                sa.String(100),
                sa.ForeignKey("investigation_templates.id"),
                nullable=True,
            ),
        )
        op.create_index(
            "ix_investigations_template_id",
            "investigations",
            ["template_id"],
        )

    if "committed_sources_json" not in inv_cols:
        op.add_column(
            "investigations",
            sa.Column("committed_sources_json", sa.JSON, nullable=True),
        )


def downgrade() -> None:
    op.drop_index("ix_investigations_template_id", table_name="investigations")
    op.drop_column("investigations", "committed_sources_json")
    op.drop_column("investigations", "template_id")
    op.drop_table("investigation_templates")
