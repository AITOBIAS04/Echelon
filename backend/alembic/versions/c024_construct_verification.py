"""024 Construct Verification V1 — new table + column extensions

Revision ID: c024_construct_verification
Revises: c022_investigation_templates
Create Date: 2026-03-16

Sprint-0 migration:
- Create construct_registrations table with (slug, version) unique constraint
- Add content_text (TEXT, nullable) to investigation_evidence_items
- Add construct_meta_json (JSON, nullable) to investigation_evidence_items
- Add template_config_json (JSON, nullable) to investigation_templates
- Add run_number (INTEGER, nullable) to investigations
- Composite index on (construct_id, run_number) with partial uniqueness
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c024_construct_verification"
down_revision: Union[str, None] = "c022_investigation_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- NEW TABLE: construct_registrations --
    op.create_table(
        "construct_registrations",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("skill_manifest", sa.JSON, nullable=False),
        sa.Column("skill_count", sa.Integer, nullable=False),
        sa.Column("domain_claims", sa.JSON, nullable=False),
        sa.Column("test_prompts_hash", sa.String(128), nullable=False),
        sa.Column("rubric_hash", sa.String(128), nullable=False),
        sa.Column("commitment_hash", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="REGISTERED"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("slug", "version", name="uq_construct_slug_version"),
    )

    # -- EXTEND: investigation_evidence_items --
    op.add_column(
        "investigation_evidence_items",
        sa.Column("content_text", sa.Text, nullable=True),
    )
    op.add_column(
        "investigation_evidence_items",
        sa.Column("construct_meta_json", sa.JSON, nullable=True),
    )

    # -- EXTEND: investigation_templates --
    op.add_column(
        "investigation_templates",
        sa.Column("template_config_json", sa.JSON, nullable=True),
    )

    # -- EXTEND: investigations --
    op.add_column(
        "investigations",
        sa.Column("run_number", sa.Integer, nullable=True),
    )
    op.create_index(
        "ix_investigations_construct_run",
        "investigations",
        ["construct_id", "run_number"],
        unique=True,
        postgresql_where=sa.text("run_number IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_investigations_construct_run", table_name="investigations")
    op.drop_column("investigations", "run_number")
    op.drop_column("investigation_templates", "template_config_json")
    op.drop_column("investigation_evidence_items", "construct_meta_json")
    op.drop_column("investigation_evidence_items", "content_text")
    op.drop_table("construct_registrations")
